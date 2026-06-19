#!/bin/bash
# ============================================================================
# GRID OVERNIGHT — Treino-2 na voz CURADA do Pedro, satura a H100 e roda
# BACK-TO-BACK até 14:00 UTC (11h BRT, ~12h) SEM nunca idlar.
# Revisado adversarialmente (workflow review-overnight-grid, 22 achados aplicados).
#
# Robustez:
#  - RESUMÍVEL: pula arm com stage_b_result.json (inclui sentinel de crash) → watchdog
#    pode reiniciar a qualquer hora sem refazer nem re-rodar arm que já falhou.
#  - PRE-FLIGHT: aborta LOUD (overnight.blocked) se faltar dado/base — em vez de idlar.
#  - DEADLINE-AWARE: piso MIN_TRAIN; arm longo só roda se couber ≥70%; capa o último.
#  - Crash de arm NÃO derruba a fila (run() sempre return 0; só o deadline retorna 99).
#  - FILL com fallback de dado + backoff anti busy-spin.
# Cada arm: CSM + funde BASE-PT (cml_long, exceto c_nobase) + LoRA novo; batch 8 + 8 workers.
# ============================================================================
set -u
cd /workspace/TTS-ptbr || { echo "FATAL: /workspace/TTS-ptbr ausente $(date -u)"; exit 1; }
set -a; source /workspace/.env 2>/dev/null || true; set +a
export HF_HUB_ENABLE_HF_TRANSFER=1

BASE=/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final
RUNS=/workspace/TTS-ptbr-data/runs
LOGD=/workspace/grid
CLEAN=/workspace/pedro_clean
FULL=/workspace/pedro_data
mkdir -p "$LOGD"
DEADLINE=$(date -u -d "2026-06-19 14:00:00" +%s)   # 11h BRT (~12h de janela; Pedro pediu 12h)
GUARD_MIN=8            # margem p/ o eval fechar antes do deadline
MIN_TRAIN=18          # não começa arm com menos que isso de treino (evita stub que paga eval cheio)
FAILS=0               # contador GLOBAL de crashes consecutivos (NÃO local — persiste entre run())
export OVERNIGHT_HEARTBEAT="$LOGD/overnight.heartbeat"

# guarda de instância única
if [ -f "$LOGD/overnight.pid" ] && kill -0 "$(cat "$LOGD/overnight.pid" 2>/dev/null)" 2>/dev/null; then
  echo "já há overnight vivo (PID $(cat "$LOGD/overnight.pid")) — saio"; exit 0
fi
echo $$ > "$LOGD/overnight.pid"

remain_min () { echo $(( (DEADLINE - $(date -u +%s)) / 60 )); }

# ---- PRE-FLIGHT: aborta loud se faltar o essencial (em vez de SKIP-cascata + idle) ----
preflight_fatal () { echo "ABORT preflight: $1 $(date -u)" | tee -a "$LOGD/overnight.log"; echo "$1" > "$LOGD/overnight.blocked"; rm -f "$LOGD/overnight.pid"; exit 2; }
[ -d "$BASE" ] || preflight_fatal "BASE-PT ausente: $BASE"
[ -f "$CLEAN/transcribed_clean.jsonl" ] || preflight_fatal "falta $CLEAN/transcribed_clean.jsonl (suba o curado)"
[ -f "$CLEAN/transcribed_clean_130.jsonl" ] || preflight_fatal "falta $CLEAN/transcribed_clean_130.jsonl (subset)"
[ -f "$CLEAN/transcribed.jsonl" ] || preflight_fatal "falta $CLEAN/transcribed.jsonl (auto 262)"
# a0_auto só é A/B válido se o auto NÃO foi sobrescrito pelo curado:
if cmp -s "$CLEAN/transcribed.jsonl" "$CLEAN/transcribed_clean.jsonl"; then
  preflight_fatal "transcribed.jsonl == transcribed_clean.jsonl (auto foi sobrescrito — a0_auto inválido)"
fi
rm -f "$LOGD/overnight.blocked"
echo "######## OVERNIGHT START $(date -u) · deadline $(date -u -d @$DEADLINE) · rem $(remain_min)m ########" | tee -a "$LOGD/overnight.log"
echo "dados: $(wc -l "$CLEAN/transcribed_clean.jsonl" "$CLEAN/transcribed_clean_130.jsonl" "$CLEAN/transcribed.jsonl" "$FULL/transcribed.jsonl" 2>/dev/null | tr '\n' '|')" | tee -a "$LOGD/overnight.log"

# ---- run() genérico (funde $BASE) ----
run () {
  local name="$1" lr="$2" mode="$3" reqmin="$4" ddir="$5" dfile="$6" rank="$7" seed="${8:-3407}"
  local out="$RUNS/ov_$name" log="$LOGD/ov_$name.log"
  date -u +%s > "$OVERNIGHT_HEARTBEAT"
  [ -f "$out/stage_b_result.json" ] && { echo "SKIP $name (já feito)" | tee -a "$LOGD/overnight.log"; return 0; }
  [ -f "$ddir/$dfile" ] || { echo "SKIP $name (sem $ddir/$dfile)" | tee -a "$LOGD/overnight.log"; return 0; }
  local rem; rem=$(remain_min)
  if [ "$rem" -lt $((GUARD_MIN + MIN_TRAIN)) ]; then echo "DEADLINE ($rem min) — encerro a fila" | tee -a "$LOGD/overnight.log"; return 99; fi
  local mins="$reqmin" cap=$((rem - GUARD_MIN))
  # arm longo (≥60min): só roda se couber ≥70% do pedido (senão vira convergência truncada → SKIP)
  if [ "$reqmin" -ge 60 ] && [ "$cap" -lt $((reqmin * 7 / 10)) ]; then
    echo "SKIP $name (arm longo: cap ${cap}m < 0.7x${reqmin}m)" | tee -a "$LOGD/overnight.log"; return 0; fi
  [ "$mins" -gt "$cap" ] && mins="$cap"
  echo "===== $(date -u) START $name lr=$lr mode=$mode rank=$rank data=$dfile mins=$mins rem=${rem}m =====" | tee -a "$LOGD/overnight.log"
  python3 runpod/train_voice.py --base-adapter "$BASE" --data-dir "$ddir" --data-file "$dfile" \
    --out "$out" --lr "$lr" --lora-r "$rank" --batch 8 --accum 4 --workers 8 --minutes "$mins" \
    --text-mode "$mode" --seed "$seed" > "$log" 2>&1
  local rc=$?
  # sentinel de crash: se morreu sem resultado, marca como feito (watchdog não re-roda doomed)
  if [ "$rc" -ne 0 ] && [ ! -f "$out/stage_b_result.json" ]; then
    echo "{\"failed\":true,\"rc\":$rc,\"name\":\"$name\"}" > "$out/stage_b_result.json"
    FAILS=$((FAILS + 1))
  else
    FAILS=0
  fi
  local wer; wer=$(python3 -c "import json;print(json.load(open('$out/stage_b_result.json')).get('wer'))" 2>/dev/null || echo NA)
  echo "===== $(date -u) END $name rc=$rc WER=$wer FAILS=$FAILS =====" | tee -a "$LOGD/overnight.log"
  date -u +%s > "$OVERNIGHT_HEARTBEAT"
  return 0
}

# ---- c_nobase: ablação da BASE (CSM cru, --base-adapter '') — testa se o CML formal abafa o carioca ----
c_nobase () {
  local out="$RUNS/ov_c_nobase" log="$LOGD/ov_c_nobase.log"
  date -u +%s > "$OVERNIGHT_HEARTBEAT"
  [ -f "$out/stage_b_result.json" ] && { echo "SKIP c_nobase (já feito)" | tee -a "$LOGD/overnight.log"; return 0; }
  [ -f "$CLEAN/transcribed_clean.jsonl" ] || { echo "SKIP c_nobase (sem dado)" | tee -a "$LOGD/overnight.log"; return 0; }
  local rem; rem=$(remain_min); [ "$rem" -lt $((GUARD_MIN + MIN_TRAIN)) ] && { echo "DEADLINE — pulo c_nobase" | tee -a "$LOGD/overnight.log"; return 0; }
  local mins=35 cap=$((rem - GUARD_MIN)); [ "$mins" -gt "$cap" ] && mins="$cap"
  echo "===== $(date -u) START c_nobase (ablação BASE: CSM cru) mins=$mins =====" | tee -a "$LOGD/overnight.log"
  python3 runpod/train_voice.py --base-adapter '' --data-dir "$CLEAN" --data-file transcribed_clean.jsonl \
    --out "$out" --lr 5e-5 --lora-r 64 --batch 8 --accum 4 --workers 8 --minutes "$mins" --text-mode raw --seed 3407 > "$log" 2>&1
  local rc=$?
  [ "$rc" -ne 0 ] && [ ! -f "$out/stage_b_result.json" ] && echo "{\"failed\":true,\"rc\":$rc,\"name\":\"c_nobase\"}" > "$out/stage_b_result.json"
  local wer; wer=$(python3 -c "import json;print(json.load(open('$out/stage_b_result.json')).get('wer'))" 2>/dev/null || echo NA)
  echo "===== $(date -u) END c_nobase rc=$rc WER=$wer =====" | tee -a "$LOGD/overnight.log"
  date -u +%s > "$OVERNIGHT_HEARTBEAT"
}

# ============================================================================
# FILA — ordem = prioridade. Objetivo nº1 = SOTAQUE (G2P) → vem cedo, antes dos
# sweeps de hparam, pq o deadline corta a CAUDA. (reorder do review science-lens)
# ============================================================================
# nome          lr     modo       min  data-dir  data-file                     rank
run c0_curated   5e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # GOLD control (260 curado à mão)
run c_g2p        5e-5  g2p        35   "$CLEAN"  transcribed_clean.jsonl       64    # SOTAQUE (fonético) — top valor
run a0_auto      5e-5  raw        35   "$CLEAN"  transcribed.jsonl             64    # auto 262 → curado-vs-auto
c_nobase                                                                              # ablação da BASE (suspeita nº1)
run c_g2p_r128   5e-5  g2p        45   "$CLEAN"  transcribed_clean.jsonl       128   # sotaque + capacidade
run c_g2p_long   5e-5  g2p        70   "$CLEAN"  transcribed_clean.jsonl       64    # sotaque convergência
run c_g2p_auto   5e-5  g2p        35   "$CLEAN"  transcribed.jsonl             64    # G2P depende da curadoria? (auto)
run c_g2p_full   5e-5  g2p        35   "$FULL"   transcribed.jsonl             64    # sotaque com MAIS dado (362)
run c_full362    5e-5  raw        35   "$FULL"   transcribed.jsonl             64    # a curadoria ajudou? (362 brutos)
run c_long       5e-5  raw        90   "$CLEAN"  transcribed_clean.jsonl       64    # convergência (mais treino)
# --- cauda: sweeps de hparam (1-variável) — primeiros a serem cortados pelo deadline ---
run c_half130    5e-5  raw        35   "$CLEAN"  transcribed_clean_130.jsonl   64    # curva de escala de dado
run c_r128       5e-5  raw        45   "$CLEAN"  transcribed_clean.jsonl       128   # capacidade↑
run c_r32        5e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       32    # capacidade↓
run c_lr2e5      2e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # lr↓
run c_lr1e4      1e-4  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # lr↑ (gotcha #6: pode falhar — por último)
run c_deep       5e-5  raw        140  "$CLEAN"  transcribed_clean.jsonl       64    # teto de convergência (gold)

# ---- FILL até o deadline: replica os arms de DECISÃO ciclando modo+seed (error bars; nunca idle) ----
FILL_DDIR="$CLEAN"; FILL_DFILE=transcribed_clean.jsonl
[ -f "$FILL_DDIR/$FILL_DFILE" ] || { FILL_DDIR="$FULL"; FILL_DFILE=transcribed.jsonl; }   # fallback garantido
FILL_MODES=(raw g2p normalize)
i=0
while [ "$(remain_min)" -gt $((GUARD_MIN + MIN_TRAIN)) ]; do
  m=${FILL_MODES[$((i % 3))]}
  before=$(date -u +%s)
  run fill_${i}_$m 5e-5 "$m" 30 "$FILL_DDIR" "$FILL_DFILE" 64 $((2000 + i))
  # se o "arm" voltou em <60s foi SKIP/no-op → dorme p/ não busy-spin; 2 falhas seguidas → para
  [ $(( $(date -u +%s) - before )) -lt 60 ] && sleep 30
  [ "$FAILS" -ge 2 ] && { echo "2 falhas seguidas no fill — paro" | tee -a "$LOGD/overnight.log"; break; }
  i=$((i + 1))
  [ "$i" -ge 40 ] && break
done

echo "######## OVERNIGHT DONE $(date -u) ########" | tee -a "$LOGD/overnight.log"
rm -f "$LOGD/overnight.pid"
