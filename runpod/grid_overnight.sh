#!/bin/bash
# ============================================================================
# GRID OVERNIGHT — Treino-2 na voz do Pedro (dado CURADO à mão), satura a H100
# e roda BACK-TO-BACK até as 9h BRT (12:00 UTC) SEM nunca idlar.
#
# Robustez (o ponto do Pedro: "da última vez perdemos horas de GPU ociosa"):
#  - RESUMÍVEL: pula arm cujo stage_b_result.json já existe → o cron pode
#    reiniciar este script a qualquer momento sem refazer trabalho.
#  - DEADLINE-AWARE: nunca começa arm que não cabe antes de 12:00 UTC; capa
#    os minutos do último arm pra terminar (com eval) antes do deadline.
#  - PID/heartbeat: escreve overnight.pid + toca heartbeat a cada arm → o cron
#    detecta "morto/idle" e reinicia.
#  - Um arm que CRASHAR não derruba o grid (sem set -e no run()).
#  - FILL: se a fila acabar antes do deadline, roda arms extras (seeds variados)
#    → a GPU trabalha até o fim.
# Cada arm: CSM + funde BASE-PT (cml_long) + LoRA novo; batch 8 + workers (~1.4s/it).
# ============================================================================
set -u
cd /workspace/TTS-ptbr || exit 1
set -a; source /workspace/.env 2>/dev/null || true; set +a
export HF_HUB_ENABLE_HF_TRANSFER=1

BASE=/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final
RUNS=/workspace/TTS-ptbr-data/runs
LOGD=/workspace/grid
CLEAN=/workspace/pedro_clean
FULL=/workspace/pedro_data
mkdir -p "$LOGD"

# instância única: se já há um overnight vivo, sai (o watchdog/cron pode chamar em paralelo)
if [ -f "$LOGD/overnight.pid" ] && kill -0 "$(cat "$LOGD/overnight.pid" 2>/dev/null)" 2>/dev/null; then
  echo "já há overnight vivo (PID $(cat "$LOGD/overnight.pid")) — saio" ; exit 0
fi
echo $$ > "$LOGD/overnight.pid"

DEADLINE=$(date -u -d "2026-06-19 14:00:00" +%s)   # 11h BRT (~12h de janela; Pedro pediu 12h)
GUARD_MIN=8                                          # margem p/ o eval fechar antes do deadline

remain_min () { echo $(( (DEADLINE - $(date -u +%s)) / 60 )); }

run () {
  local name="$1" lr="$2" mode="$3" reqmin="$4" ddir="$5" dfile="$6" rank="$7"
  local out="$RUNS/ov_$name" log="$LOGD/ov_$name.log"
  date -u +%s > "$LOGD/overnight.heartbeat"
  # resumível
  if [ -f "$out/stage_b_result.json" ]; then echo "SKIP $name (já feito)" | tee -a "$LOGD/overnight.log"; return 0; fi
  # guarda de dado: não tenta arm cujo data-file não existe
  if [ ! -f "$ddir/$dfile" ]; then echo "SKIP $name (sem $ddir/$dfile)" | tee -a "$LOGD/overnight.log"; return 0; fi
  local rem; rem=$(remain_min)
  if [ "$rem" -lt $((GUARD_MIN + 6)) ]; then echo "DEADLINE ($rem min) — encerro a fila" | tee -a "$LOGD/overnight.log"; return 99; fi
  local mins="$reqmin" cap=$((rem - GUARD_MIN))
  [ "$mins" -gt "$cap" ] && mins="$cap"
  echo "===== $(date -u) START $name lr=$lr mode=$mode rank=$rank data=$dfile mins=$mins rem=${rem}m =====" | tee -a "$LOGD/overnight.log"
  python3 runpod/train_voice.py --base-adapter "$BASE" --data-dir "$ddir" --data-file "$dfile" \
    --out "$out" --lr "$lr" --lora-r "$rank" --batch 8 --accum 4 --workers 8 --minutes "$mins" \
    --text-mode "$mode" --seed "${8:-3407}" > "$log" 2>&1
  local rc=$?
  local wer; wer=$(python3 -c "import json;print(json.load(open('$out/stage_b_result.json')).get('wer'))" 2>/dev/null || echo NA)
  echo "===== $(date -u) END $name rc=$rc WER=$wer =====" | tee -a "$LOGD/overnight.log"
  date -u +%s > "$LOGD/overnight.heartbeat"
  return 0
}

echo "######## OVERNIGHT START $(date -u) · deadline $(date -u -d @$DEADLINE) · rem $(remain_min)m ########" | tee -a "$LOGD/overnight.log"

# ---- FILA (ordem = prioridade; se o deadline cortar a cauda, a ciência-chave já rodou) ----
# nome          lr     modo       min  data-dir  data-file                     rank
run c0_curated   5e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # GOLD control (260 curado à mão)
run c_g2p        5e-5  g2p        35   "$CLEAN"  transcribed_clean.jsonl       64    # SOTAQUE (fonético) — top valor
run a0_auto      5e-5  raw        35   "$CLEAN"  transcribed.jsonl             64    # auto 262 → curado-vs-auto
run c_norm       5e-5  normalize  35   "$CLEAN"  transcribed_clean.jsonl       64    # número→palavra no treino
run c_full362    5e-5  raw        35   "$FULL"   transcribed.jsonl             64    # data↑ (362) → curadoria ajudou?
run c_lr1e4      1e-4  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # lr↑
run c_r128       5e-5  raw        45   "$CLEAN"  transcribed_clean.jsonl       128   # capacidade↑
run c_long       5e-5  raw        90   "$CLEAN"  transcribed_clean.jsonl       64    # convergência (mais treino)
run c_half130    5e-5  raw        35   "$CLEAN"  transcribed_clean_130.jsonl   64    # data↓ (curva de escala)
run c_lr2e5      2e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       64    # lr↓
run c_r32        5e-5  raw        35   "$CLEAN"  transcribed_clean.jsonl       32    # capacidade↓
run c_g2p_r128   5e-5  g2p        45   "$CLEAN"  transcribed_clean.jsonl       128   # sotaque + capacidade
run c_g2p_long   5e-5  g2p        70   "$CLEAN"  transcribed_clean.jsonl       64    # sotaque convergência
# --- 2ª onda (Pedro estendeu p/ 12h): interações modo×dado + convergência profunda ---
run c_g2p_auto   5e-5  g2p        35   "$CLEAN"  transcribed.jsonl             64    # G2P depende da curadoria? (auto 262)
run c_g2p_full   5e-5  g2p        35   "$FULL"   transcribed.jsonl             64    # sotaque com MAIS dado (362)
run c_norm_full  5e-5  normalize  35   "$FULL"   transcribed.jsonl             64    # número × mais dado
run c_deep       5e-5  raw        140  "$CLEAN"  transcribed_clean.jsonl       64    # teto de convergência (gold, recipe vencedora estendida)

# ---- FILL até o deadline: re-roda o melhor-palpite ciclando MODO (informativo, nunca idle) ----
FILL_MODES=(raw normalize g2p)
i=0
while [ "$(remain_min)" -gt $((GUARD_MIN + 12)) ] && [ "$i" -lt 16 ]; do
  m=${FILL_MODES[$((i % 3))]}
  run fill_${i}_$m 5e-5 "$m" 30 "$CLEAN" transcribed_clean.jsonl 64 $((1000 + i)) || break
  i=$((i + 1))
done

echo "######## OVERNIGHT DONE $(date -u) ########" | tee -a "$LOGD/overnight.log"
rm -f "$LOGD/overnight.pid"
