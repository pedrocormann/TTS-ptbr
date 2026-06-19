#!/bin/bash
# Grid Treino-2 — satura a H100 (batch 8 + dataloader workers → util 60-100%, 1.45s/it).
# 5 arms SEQUENCIAIS. Cada arm: CSM + funde BASE-PT (cml_long) + LoRA novo. Back-to-back
# (nunca idle). Um arm que crashar NÃO derruba o grid (sem set -e no run).
set -u
cd /workspace/TTS-ptbr
set -a; source /workspace/.env 2>/dev/null || true; set +a
export HF_HUB_ENABLE_HF_TRANSFER=1

BASE=/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final
RUNS=/workspace/TTS-ptbr-data/runs
LOGD=/workspace/grid
mkdir -p "$LOGD"

run () {
  name="$1"; lr="$2"; mode="$3"; mins="$4"; ddir="$5"; dfile="$6"; rank="$7"
  out="$RUNS/t2_$name"; log="$LOGD/$name.log"
  echo "===== $(date -u) START $name lr=$lr mode=$mode rank=$rank data=$ddir/$dfile mins=$mins =====" | tee -a "$LOGD/grid.log"
  python3 runpod/train_voice.py --base-adapter "$BASE" --data-dir "$ddir" --data-file "$dfile" \
    --out "$out" --lr "$lr" --lora-r "$rank" --batch 8 --accum 4 --workers 8 --minutes "$mins" \
    --text-mode "$mode" > "$log" 2>&1
  rc=$?
  wer=$(python3 -c "import json;print(json.load(open('$out/stage_b_result.json')).get('wer'))" 2>/dev/null || echo NA)
  echo "===== $(date -u) END $name rc=$rc WER=$wer =====" | tee -a "$LOGD/grid.log"
}

# nome        lr     modo       min  data-dir                  data-file          rank
run a0_clean    5e-5  raw        35  /workspace/pedro_clean    transcribed.jsonl  64   # CONTROL: Stage B na 262-clean
run a1_lr1e4    1e-4  raw        35  /workspace/pedro_clean    transcribed.jsonl  64   # lever de LR
run a2_norm     5e-5  normalize  35  /workspace/pedro_clean    transcribed.jsonl  64   # número→palavra no treino
run a3_g2p      5e-5  g2p        35  /workspace/pedro_clean    transcribed.jsonl  64   # sotaque fonético (experimental)
run a4_full362  5e-5  raw        35  /workspace/pedro_data     transcribed.jsonl  64   # 362 brutos: a curadoria ajudou?

echo "GRID DONE $(date -u)" | tee -a "$LOGD/grid.log"
