#!/bin/bash
# ============================================================================
# GRID RODADA 3 — multi-voz (pedro/gui/joao) sobre o flywheel exportado.
#
# 11 arms (teto 12 — dimensionado pela ESCUTA: ~top-4 por noite de escuta humana,
# 11 arms = 2-3 noites; NÃO adicione arms sem adicionar noites):
#   por voz {pedro,gui,joao}:  r3_<voz>_solo  · r3_<voz>_mix15 (base 0.15) · r3_<voz>_mix30 (0.30)
#   + 2 seeds extras do vencedor esperado:  r3_pedro_mix15_s2 · r3_pedro_mix15_s3
#
# Molde do grid_overnight.sh (provado na noite de 19/jun):
#   - RESUMÍVEL: pula arm com stage_b_result.json (inclui sentinel de crash)
#   - PRE-FLIGHT loud (r3.blocked) se faltar dado/base/HF_TOKEN — em vez de idlar
#   - DEADLINE-AWARE: capa minutos; crash de arm NÃO derruba a fila
#   - Receita fixa do grid de 26 arms: lr 5e-5 · r=64 · raw · base-PT fundida · batch 8×4
#   - SEM fill loop: arms são dimensionados pela capacidade de escuta, não pelo relógio
#
# COLETA: tar ÚNICO no fim com verificação de tamanho/contagem e falha LOUD.
# (O review_overnight.sh antigo fazia scp por-arm com 2>/dev/null → engoliu erros
#  e produziu 26 diretórios vazios. Aqui NADA falha em silêncio.)
# ============================================================================
set -u
cd /workspace/TTS-ptbr || { echo "FATAL: /workspace/TTS-ptbr ausente $(date -u)"; exit 1; }
set -a; source /workspace/.env 2>/dev/null || true; set +a
export HF_HUB_ENABLE_HF_TRANSFER=1

BASE=${BASE:-/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final}
RUNS=${RUNS:-/workspace/TTS-ptbr-data/runs}
LOGD=${LOGD:-/workspace/grid}
FLY=${FLY:-/workspace/TTS-ptbr/data/flywheel}           # export_flywheel.py → <FLY>/<voz>/{train.jsonl,segments/}
BASE_DATA=${BASE_DATA:-/workspace/TTS-ptbr/data/base_pt} # dataset público local (train.jsonl|transcribed.jsonl + segments/)
PUSH_HUB=${PUSH_HUB:-pedrocormann/tts-ptbr-rodada3}
VOZES=${VOZES:-pedro gui joao}
PER_ARM_MIN=${PER_ARM_MIN:-45}       # ≈3 épocas p/ ~12h de áudio a 50 h-áudio/H100-h; ver RUNBOOK p/ dimensionar
BUDGET_MIN=${BUDGET_MIN:-720}        # janela total (12h) a partir do START
MIN_AUDIO_MIN=${MIN_AUDIO_MIN:-300}  # go/no-go: ≥5h por voz (piloto: export MIN_AUDIO_MIN=60)
GUARD_MIN=12                         # margem p/ eval+métricas+push fecharem
MIN_TRAIN=20                         # não começa arm com menos treino que isso
FAILS=0                              # crashes consecutivos (global, persiste entre run())
MAIN_LOG="$LOGD/r3.log"
HEARTBEAT="$LOGD/r3.heartbeat"
mkdir -p "$LOGD" "$RUNS"
DEADLINE=$(( $(date -u +%s) + BUDGET_MIN * 60 ))

# guarda de instância única
if [ -f "$LOGD/r3.pid" ] && kill -0 "$(cat "$LOGD/r3.pid" 2>/dev/null)" 2>/dev/null; then
  echo "já há rodada3 viva (PID $(cat "$LOGD/r3.pid")) — saio"; exit 0
fi
echo $$ > "$LOGD/r3.pid"

remain_min () { echo $(( (DEADLINE - $(date -u +%s)) / 60 )); }
preflight_fatal () { echo "ABORT preflight: $1 $(date -u)" | tee -a "$MAIN_LOG"; echo "$1" > "$LOGD/r3.blocked"; rm -f "$LOGD/r3.pid"; exit 2; }

# ---- PRE-FLIGHT: aborta LOUD se faltar o essencial ----
[ -n "${HF_TOKEN:-}" ] || preflight_fatal "HF_TOKEN ausente (confere /workspace/.env)"
[ -d "$BASE" ] || preflight_fatal "BASE-PT ausente: $BASE"
[ -f eval/benchmark_ptbr.jsonl ] || preflight_fatal "eval/benchmark_ptbr.jsonl ausente (repo incompleto)"
if [ ! -f "$BASE_DATA/train.jsonl" ] && [ ! -f "$BASE_DATA/transcribed.jsonl" ]; then
  preflight_fatal "dataset base do mix ausente: $BASE_DATA/{train,transcribed}.jsonl (8 dos 11 arms são mix)"
fi
for voz in $VOZES; do
  [ -f "$FLY/$voz/train.jsonl" ] || preflight_fatal "falta $FLY/$voz/train.jsonl (rode tools/data/export_flywheel.py e suba data/flywheel/)"
  mins=$(python3 - "$FLY/$voz" <<'PY'
import json, os, sys
import soundfile as sf
d = sys.argv[1]; tot = 0.0
for l in open(os.path.join(d, 'train.jsonl'), encoding='utf-8'):
    if not l.strip():
        continue
    r = json.loads(l)
    p = os.path.join(d, 'segments', os.path.basename(r['audio']))
    try:
        i = sf.info(p); tot += i.frames / i.samplerate
    except Exception:
        pass
print(int(tot / 60))
PY
) || preflight_fatal "não consegui medir a duração de $voz (soundfile instalado?)"
  [ "$mins" -ge "$MIN_AUDIO_MIN" ] || preflight_fatal "$voz tem só ${mins}min de áudio (< ${MIN_AUDIO_MIN}min) — colete mais ou baixe MIN_AUDIO_MIN"
  echo "  preflight: $voz = ${mins}min de áudio ✓" | tee -a "$MAIN_LOG"
done
rm -f "$LOGD/r3.blocked"
echo "######## RODADA3 START $(date -u) · deadline $(date -u -d @$DEADLINE 2>/dev/null || date -u -r $DEADLINE) · vozes: $VOZES · push: $PUSH_HUB ########" | tee -a "$MAIN_LOG"

# ---- run(): 1 arm. mixw vazio = solo; senão mistura voz=1.0,base=<mixw>.
#      6º arg opcional = data-file (default train.jsonl; ex.: train_pros.jsonl no A/B prosódico) ----
run () {
  local name="$1" voz="$2" mixw="$3" reqmin="$4" seed="${5:-3407}" datafile="${6:-train.jsonl}"
  local out="$RUNS/$name" log="$LOGD/$name.log"
  date -u +%s > "$HEARTBEAT"
  [ -f "$out/stage_b_result.json" ] && { echo "SKIP $name (já feito)" | tee -a "$MAIN_LOG"; return 0; }
  local rem; rem=$(remain_min)
  if [ "$rem" -lt $((GUARD_MIN + MIN_TRAIN)) ]; then echo "DEADLINE ($rem min) — encerro a fila" | tee -a "$MAIN_LOG"; return 99; fi
  local mins="$reqmin" cap=$((rem - GUARD_MIN))
  [ "$mins" -gt "$cap" ] && mins="$cap"
  local dargs
  if [ -n "$mixw" ]; then
    dargs=(--mix "voz=1.0,base=$mixw" --mix-dirs "voz=$FLY/$voz,base=$BASE_DATA")
  else
    dargs=(--data-dir "$FLY/$voz" --data-file "$datafile")
  fi
  echo "===== $(date -u) START $name voz=$voz mix=${mixw:-solo} seed=$seed mins=$mins rem=${rem}m =====" | tee -a "$MAIN_LOG"
  python3 runpod/train_voice.py --base-adapter "$BASE" --out "$out" \
    --lr 5e-5 --lora-r 64 --batch 8 --accum 4 --workers 8 --minutes "$mins" \
    --text-mode raw --seed "$seed" --speaker "$voz" --holdout 0.05 \
    --push-hub "$PUSH_HUB" "${dargs[@]}" > "$log" 2>&1
  local rc=$?
  # sentinel de crash: morreu sem resultado → marca como feito (fila resumível não re-roda doomed)
  if [ "$rc" -ne 0 ] && [ ! -f "$out/stage_b_result.json" ]; then
    echo "{\"failed\":true,\"rc\":$rc,\"name\":\"$name\"}" > "$out/stage_b_result.json"
    FAILS=$((FAILS + 1))
  else
    FAILS=0
  fi
  local wer; wer=$(python3 -c "import json;print(json.load(open('$out/stage_b_result.json')).get('wer'))" 2>/dev/null || echo NA)
  echo "===== $(date -u) END $name rc=$rc WER=$wer FAILS=$FAILS =====" | tee -a "$MAIN_LOG"
  date -u +%s > "$HEARTBEAT"
  [ "$FAILS" -ge 3 ] && { echo "3 crashes seguidos — algo estrutural quebrou, paro a fila" | tee -a "$MAIN_LOG"; return 99; }
  return 0
}

# ============================================================================
# FILA — solo primeiro (baseline por voz), depois as misturas; seeds por último
# (se o deadline cortar, corta réplica, não ciência). run devolve 99 no deadline
# e os demais arms viram no-op rápido (mesmo padrão do grid_overnight).
# ============================================================================
for voz in $VOZES; do
  run "r3_${voz}_solo"  "$voz" ""     "$PER_ARM_MIN"
  run "r3_${voz}_mix15" "$voz" 0.15   "$PER_ARM_MIN"
  run "r3_${voz}_mix30" "$voz" 0.30   "$PER_ARM_MIN"
done
run r3_pedro_mix15_s2 pedro 0.15 "$PER_ARM_MIN" 1234
run r3_pedro_mix15_s3 pedro 0.15 "$PER_ARM_MIN" 4242

# A/B pontuação prosódica (docs/TRANSCRICAO-PROSODICA.md; BRACIS 2025 mediu WER .43 vs .50):
# mesmo dado/receita do r3_pedro_solo, só muda o texto (train_pros.jsonl via repunct_prosodic --emit-dataset)
if [ -f "$FLY/pedro/train_pros.jsonl" ]; then
  run r3_pedro_pros pedro "" "$PER_ARM_MIN" 3407 train_pros.jsonl
else
  echo "AVISO: $FLY/pedro/train_pros.jsonl não existe — arm r3_pedro_pros pulado (rode tools/curate/repunct_prosodic.py --report-only --emit-dataset)" | tee -a "$MAIN_LOG"
fi

# ---- placar (WER + spk_sim + eval_loss por arm) ----
echo "── PLACAR RODADA 3 ──" | tee -a "$MAIN_LOG"
python3 - "$RUNS" <<'PY' | tee -a "$MAIN_LOG"
import json, glob, os, sys
print(f"{'arm':<22}{'WER':>6}{'spk_sim':>9}{'evloss':>8}  mix")
for d in sorted(glob.glob(os.path.join(sys.argv[1], 'r3_*'))):
    rj = os.path.join(d, 'stage_b_result.json')
    if not os.path.exists(rj):
        continue
    try:
        r = json.load(open(rj))
    except Exception:
        print(f"{os.path.basename(d):<22} (json ilegível)"); continue
    w = r.get('wer'); ws = f"{w*100:.0f}%" if isinstance(w, (int, float)) else str(w)
    ss = (r.get('spk_sim') or {}).get('mean')
    hl = (r.get('holdout') or {}).get('eval_loss')
    mx = ','.join(f"{k}={v['weight']}" for k, v in (r.get('mix') or {}).items()) or 'solo'
    print(f"{os.path.basename(d):<22}{ws:>6}{str(ss):>9}{str(hl):>8}  {mx}")
PY

# ============================================================================
# COLETA — tar ÚNICO, verificação explícita, falha LOUD (nunca 2>/dev/null).
# ============================================================================
collect_artifacts () {
  echo "── COLETA: tar único ──" | tee -a "$MAIN_LOG"
  local list="$LOGD/r3_tar_list.txt" tarball="$LOGD/r3_artifacts.tar.gz"
  : > "$list"
  local complete=0 warn=0
  for out in "$RUNS"/r3_*; do
    [ -d "$out" ] || continue
    local name; name=$(basename "$out")
    if [ ! -f "$out/stage_b_result.json" ]; then
      echo "  ⚠️ $name sem stage_b_result.json — fora do tar" | tee -a "$MAIN_LOG"; warn=$((warn+1)); continue
    fi
    echo "$name/stage_b_result.json" >> "$list"
    local nwav=0
    if [ -d "$out/gen" ]; then
      nwav=$(find "$out/gen" -name '*.wav' | wc -l | tr -d ' ')
      echo "$name/gen" >> "$list"
    fi
    if [ "$nwav" -lt 14 ]; then
      echo "  ⚠️ $name: $nwav/14 wavs (arm falhou ou foi cortado)" | tee -a "$MAIN_LOG"; warn=$((warn+1))
    else
      complete=$((complete+1))
    fi
  done
  if [ ! -s "$list" ]; then
    echo "❌ COLETA: NENHUM arm com resultado — nada a tarar" | tee -a "$MAIN_LOG"
    touch "$LOGD/r3_collect.FAILED"; return 1
  fi
  if ! tar -czf "$tarball" -C "$RUNS" -T "$list"; then
    echo "❌ COLETA: tar falhou (rc=$?)" | tee -a "$MAIN_LOG"
    touch "$LOGD/r3_collect.FAILED"; return 1
  fi
  local size; size=$(stat -c%s "$tarball" 2>/dev/null || stat -f%z "$tarball")
  local nfiles; nfiles=$(tar -tzf "$tarball" | wc -l | tr -d ' ')
  # piso de sanidade: cada arm completo carrega 14 wavs de ~24kHz (≥1MB por arm)
  if [ "$complete" -gt 0 ] && [ "${size:-0}" -lt $((complete * 1000000)) ]; then
    echo "❌ COLETA: tar suspeito (${size}B para $complete arms completos) — NÃO confie, inspecione $RUNS" | tee -a "$MAIN_LOG"
    touch "$LOGD/r3_collect.FAILED"; return 1
  fi
  rm -f "$LOGD/r3_collect.FAILED"
  echo "✅ COLETA: $tarball · $((size/1024/1024))MB · $nfiles entradas · $complete arms completos · $warn avisos" | tee -a "$MAIN_LOG"
  echo "   No Mac (1 scp, depois VERIFICA o tamanho):" | tee -a "$MAIN_LOG"
  echo "     scp -P <PORT> -i ~/.ssh/id_ed25519 root@<IP>:$tarball runpod_samples/rodada3/" | tee -a "$MAIN_LOG"
  echo "     tar -tzf runpod_samples/rodada3/r3_artifacts.tar.gz | wc -l   # deve dar $nfiles" | tee -a "$MAIN_LOG"
  echo "     tar -xzf runpod_samples/rodada3/r3_artifacts.tar.gz -C runpod_samples/rodada3/" | tee -a "$MAIN_LOG"
}
collect_artifacts

echo "######## RODADA3 DONE $(date -u) ########" | tee -a "$MAIN_LOG"
rm -f "$LOGD/r3.pid"
