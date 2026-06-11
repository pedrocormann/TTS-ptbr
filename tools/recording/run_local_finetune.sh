#!/usr/bin/env bash
# Esteira do finetune LOCAL (M2, csm-mlx): espera transcrição → dataset → LoRA → amostras.
# Uso:  nohup bash tools/recording/run_local_finetune.sh > /tmp/maya_test/finetune.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv-duplex/bin/activate

SES=elevenlabs2024
SEG="data/raw/$SES/segments"
RUN="data/csmmlx_runs/v1"

echo "[1/4] esperando transcrição completar…"
TOTAL=$(wc -l < "$SEG/to_transcribe.jsonl")
while :; do
  DONE=$(wc -l < "$SEG/transcribed.jsonl" 2>/dev/null || echo 0)
  echo "  transcritos: $DONE/$TOTAL ($(date +%H:%M))"
  [ "$DONE" -ge "$TOTAL" ] && break
  pgrep -f transcribe_local >/dev/null || { echo "  ⚠️ transcritor morreu — retomando"; \
    nohup python tools/recording/transcribe_local.py --session $SES --model medium \
      >> /tmp/maya_test/transcribe.log 2>&1 & }
  sleep 120
done

echo "[2/4] montando dataset csm-mlx…"
python tools/recording/make_csmmlx_dataset.py --session $SES --out data/csmmlx_ds

echo "[3/4] LoRA finetune (r=16, batch 2, grad-acc 4, 2 épocas, grad-ckpt)…"
mkdir -p "$RUN"
csm-mlx finetune lora sft \
  --data-path data/csmmlx_ds/train.json \
  --val-data-path data/csmmlx_ds/val.json --val-freq 50 \
  --output-dir "$RUN" \
  --lora-rank 16 --lora-alpha 32 \
  --batch-size 2 --gradient-accumulation-steps 4 \
  --epochs 2 --learning-rate 5e-4 \
  --max-audio-length-ms 20000 \
  --gradient-ckpt --ckpt-freq 50

echo "[4/4] gerando amostras de comparação…"
ADAPTER=$(ls -t "$RUN"/*.safetensors 2>/dev/null | head -1)
echo "  adapter: $ADAPTER"
python tools/recording/gen_csmmlx_samples.py --adapter "$ADAPTER" --out data/testes_maya
python tools/recording/gen_csmmlx_samples.py --adapter "$ADAPTER" --out data/testes_maya --no-context

echo "🏁 PIPELINE COMPLETO — amostras ft*.wav em data/testes_maya/"
