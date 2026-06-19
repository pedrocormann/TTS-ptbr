#!/bin/bash
# Coleta os resultados do grid Treino-2 do pod: tabela comparativa (WER por arm) + puxa
# os 14 wavs de cada arm + per_sentence pra runpod_samples/grid_t2/ (pra ouvir/avaliar).
# Uso: bash runpod/collect_grid_t2.sh
set -u
POD="root@31.24.80.44 -p 17313 -i $HOME/.ssh/id_ed25519"
RUNS=/workspace/TTS-ptbr-data/runs
DEST="$(cd "$(dirname "$0")/.." && pwd)/runpod_samples/grid_t2"
mkdir -p "$DEST"

echo "=== STATUS DO GRID ==="
ssh $POD "cat /workspace/grid/grid.log 2>/dev/null"

echo; echo "=== TABELA COMPARATIVA (WER mediana por arm) ==="
ssh $POD 'python3 - <<PY
import json, glob, os
rows=[]
for d in sorted(glob.glob("/workspace/TTS-ptbr-data/runs/t2_*")):
    rj=os.path.join(d,"stage_b_result.json")
    if not os.path.exists(rj): continue
    r=json.load(open(rj))
    rows.append((os.path.basename(d), r.get("wer"), r.get("text_mode"), r.get("lr"), r.get("rank"), r.get("clips"), r.get("steps"), r.get("data_file")))
print(f"{\"arm\":<14}{\"WER\":>7}  {\"modo\":<10}{\"lr\":<7}{\"r\":>4}{\"clips\":>7}{\"steps\":>7}")
for a,w,m,lr,rk,cl,st,df in rows:
    ws=f"{w*100:.0f}%" if isinstance(w,(int,float)) else str(w)
    print(f"{a:<14}{ws:>7}  {str(m):<10}{str(lr):<7}{str(rk):>4}{str(cl):>7}{str(st):>7}")
PY'

echo; echo "=== PUXANDO WAVS + per_sentence ==="
for arm in a0_clean a1_lr1e4 a2_norm a3_g2p a4_full362; do
  od="$DEST/$arm"; mkdir -p "$od"
  scp -q $POD:"$RUNS/t2_$arm/gen/*.wav" "$od/" 2>/dev/null && echo "  $arm: wavs ok" || echo "  $arm: (sem wavs ainda)"
  scp -q $POD:"$RUNS/t2_$arm/gen/per_sentence.jsonl" "$od/" 2>/dev/null
  scp -q $POD:"$RUNS/t2_$arm/stage_b_result.json" "$od/" 2>/dev/null
done
echo; echo "Resultados em: $DEST"
