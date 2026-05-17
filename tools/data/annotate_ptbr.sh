#!/usr/bin/env bash
# Thin wrapper over the OFFICIAL moshi-finetune annotator, pinned to pt-BR.
# Verified against research/repos/moshi-finetune/annotate.py: it takes the egs
# jsonl, --lang (default "en"), --whisper_model (code WARNS use 'medium' for
# stereo, NOT large-v3), --shards/--partition for SLURM (SDumont), -l/--local.
#
# Usage:
#   tools/data/annotate_ptbr.sh data/ds.jsonl                 # local, 1 box
#   tools/data/annotate_ptbr.sh data/ds.jsonl 64 cpu_long     # SLURM 64 shards
set -euo pipefail
EGS="${1:?usage: annotate_ptbr.sh <egs.jsonl> [shards] [slurm_partition]}"
SHARDS="${2:-1}"
PART="${3:-}"
MF="research/repos/moshi-finetune"
[ -f "$MF/annotate.py" ] || { echo "clone moshi-finetune first ($MF)"; exit 1; }

if [ -z "$PART" ]; then
  # local single box (Colab / dev): note the -l/--local flag + medium model
  python "$MF/annotate.py" "$EGS" --lang pt --whisper_model medium --local
else
  # SLURM (SDumont): shard across the partition
  python "$MF/annotate.py" "$EGS" --lang pt --whisper_model medium \
      --shards "$SHARDS" --partition "$PART"
fi
echo "done -> sibling .json transcripts written next to each wav. Set"
echo "data.train_data in example/moshi_7B.yaml to the egs jsonl and train."
