#!/usr/bin/env bash
# Orquestrador OVERNIGHT — roda o grid de experimentos CSM pt-BR sozinho (~8-10h) e,
# se estiver pronto, o Estágio B (voz do Pedro). Resiliente: cada run com timeout, e se
# um falhar os outros seguem. Progresso em /workspace/overnight.status (pro Claude ler).
#
# Lançar:  nohup bash runpod/overnight.sh >/workspace/overnight.log 2>&1 &
# Parar:   pkill -f overnight.sh ; pkill -f train_bateria.py
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
source /workspace/.env
export HF_HUB_ENABLE_HF_TRANSFER=1
LOG=/workspace/overnight.log
PROG=/workspace/overnight.status
LIVE=/workspace/bateria.log               # o watchdog lê isto = run atual
HUB="pedrocormann/tts-ptbr-bateria"
GRID_DEADLINE=$(( $(date +%s) + 600*60 ))  # 10h de teto pro grid (deixa folga p/ Stage B)

# grid: "tag|exp|lr|rank|minutos"  — varia UM eixo por vez a partir do baseline
GRID=(
  "cml_base|A1_cml|2e-4|64|60"        # baseline (data source)
  "tag_base|A3_tagarela|2e-4|64|60"
  "mix_base|A2_mix|2e-4|64|60"
  "cml_lr1e4|A1_cml|1e-4|64|60"       # eixo LR
  "cml_lr3e4|A1_cml|3e-4|64|60"
  "cml_r128|A1_cml|2e-4|128|60"       # eixo rank
  "cml_long|A1_cml|2e-4|64|150"       # BASE-PT candidato (longo) — vira base do Stage B
  "tag_long|A3_tagarela|2e-4|64|150"
)

n=${#GRID[@]}; i=0
for row in "${GRID[@]}"; do
  i=$((i+1)); IFS='|' read -r tag exp lr rank mins <<< "$row"
  if [ "$(date +%s)" -gt "$GRID_DEADLINE" ]; then
    echo "[$(date +%H:%M)] deadline do grid — parando após $((i-1))/$n" | tee -a "$LOG"; break
  fi
  echo "{\"phase\":\"grid\",\"run\":\"$tag\",\"idx\":$i,\"of\":$n,\"exp\":\"$exp\",\"lr\":\"$lr\",\"rank\":$rank,\"min\":$mins,\"started\":\"$(date -u +%FT%TZ)\"}" > "$PROG"
  echo "===== [$(date +%H:%M)] GRID $i/$n: $tag (exp=$exp lr=$lr rank=$rank ${mins}min) =====" | tee -a "$LOG"
  timeout $((mins+25))m python -u runpod/train_bateria.py \
      --skip-preflight --experiments "$exp" --lr "$lr" --lora-r "$rank" --lora-alpha "$rank" \
      --per-exp-min "$mins" --time-budget-min $((mins+15)) --run-tag "$tag" \
      > "$LIVE" 2>&1 \
    && echo "[$(date +%H:%M)] ✓ $tag" | tee -a "$LOG" \
    || echo "[$(date +%H:%M)] ✗ $tag falhou/timeout (continua)" | tee -a "$LOG"
  cp "$LIVE" "$LOG.$tag" 2>/dev/null || true
done

# ===== relatório mestre + push pro Hub =====
echo "{\"phase\":\"aggregate\",\"started\":\"$(date -u +%FT%TZ)\"}" > "$PROG"
python -u runpod/aggregate.py >> "$LOG" 2>&1 || true
python - <<'PY' >> "$LOG" 2>&1 || true
import os
from huggingface_hub import HfApi
api = HfApi(token=os.environ['HF_TOKEN'])
api.create_repo('pedrocormann/tts-ptbr-bateria', repo_type='model', exist_ok=True, private=True)
api.upload_folder(folder_path='/workspace/TTS-ptbr-data/runs', path_in_repo='runs',
                  repo_id='pedrocormann/tts-ptbr-bateria', repo_type='model')
print('push final pro Hub ok')
PY

# ===== Estágio B (voz do Pedro) — só se script + dados + base estiverem prontos =====
BASE=/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final
if [ -f runpod/train_voice.py ] && [ -d /workspace/pedro_data ] && [ -d "$BASE" ]; then
  echo "{\"phase\":\"stage_b\",\"started\":\"$(date -u +%FT%TZ)\"}" > "$PROG"
  echo "===== [$(date +%H:%M)] STAGE B: voz do Pedro sobre BASE-PT =====" | tee -a "$LOG"
  timeout 130m python -u runpod/train_voice.py --base-adapter "$BASE" \
      --data-dir /workspace/pedro_data --out /workspace/TTS-ptbr-data/runs/stage_b_pedro \
      > "$LIVE" 2>&1 \
    && echo "[$(date +%H:%M)] ✓ Stage B" | tee -a "$LOG" \
    || echo "[$(date +%H:%M)] ✗ Stage B falhou" | tee -a "$LOG"
  cp "$LIVE" "$LOG.stageb" 2>/dev/null || true
  python - <<'PY' >> "$LOG" 2>&1 || true
import os
from huggingface_hub import HfApi
HfApi(token=os.environ['HF_TOKEN']).upload_folder(
    folder_path='/workspace/TTS-ptbr-data/runs', path_in_repo='runs',
    repo_id='pedrocormann/tts-ptbr-bateria', repo_type='model')
print('push Stage B ok')
PY
else
  echo "[$(date +%H:%M)] Stage B pulado (faltou script/dados/base)" | tee -a "$LOG"
fi

echo "{\"phase\":\"all_done\",\"finished\":\"$(date -u +%FT%TZ)\"}" > "$PROG"
echo "[$(date +%H:%M)] ===== NOITE COMPLETA =====" | tee -a "$LOG"
