#!/usr/bin/env bash
# Clone reference repos for study into research/repos/ (gitignored).
# Idempotent: skips repos already cloned. Shallow (--depth 1) — we read, not contribute.
# Model weights are NOT here (they live on HuggingFace); this pulls code only.
set -u
cd "$(dirname "$0")" || exit 1
mkdir -p repos
cd repos || exit 1

# name|git url  (clean licenses — safe to study and learn the technique)
REPOS=(
  "csm|https://github.com/SesameAILabs/csm.git"
  "moshi|https://github.com/kyutai-labs/moshi.git"
  "moshi-finetune|https://github.com/kyutai-labs/moshi-finetune.git"
  "Orpheus-TTS|https://github.com/canopyai/Orpheus-TTS.git"
  "Llasa|https://github.com/HKUSTAudio/Llasa.git"
  "faster-whisper|https://github.com/SYSTRAN/faster-whisper.git"
  "silero-vad|https://github.com/snakers4/silero-vad.git"
  "unsloth|https://github.com/unslothai/unsloth.git"
  "TTS-Portuguese-Corpus|https://github.com/Edresson/TTS-Portuguese-Corpus.git"
)

for entry in "${REPOS[@]}"; do
  name="${entry%%|*}"; url="${entry##*|}"
  if [ -d "$name/.git" ]; then
    echo "SKIP  $name (already cloned)"
  else
    echo "CLONE $name"
    git clone --depth 1 -q "$url" "$name" && echo "  ok" || echo "  FAILED: $name"
  fi
done

echo
echo "Reference-only (NOT cloned by default — license-vetoed for product, study via web):"
echo "  coqui-ai/TTS (XTTS, CPML)  ·  SWivid/F5-TTS (CC-BY-NC)"
echo "Done. Repos in: $(pwd)"
