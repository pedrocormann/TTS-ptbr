#!/bin/bash
# Revisão de 20-em-20min (roda no Mac via cron) — coleta resultados do grid overnight,
# imprime a tabela de WER, e garante que o pod está trabalhando (re-lança o watchdog se
# ele caiu). NÃO derruba nada que esteja rodando. Idempotente.
set -u
POD="root@31.24.80.44 -p 17313 -i $HOME/.ssh/id_ed25519"
SSHC="ssh -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new $POD"
RUNS=/workspace/TTS-ptbr-data/runs
DEST="$(cd "$(dirname "$0")/.." && pwd)/runpod_samples/grid_overnight"
mkdir -p "$DEST"
NOW_UTC=$(date -u +%s)   # BSD date suporta +%s e -u (mas NÃO -d)
DEADLINE=$(python3 -c "import calendar,time;print(calendar.timegm(time.strptime('2026-06-19 14:00:00','%Y-%m-%d %H:%M:%S')))")

echo "===== REVIEW $(date) ====="

# 1) estado do pod (1 só SSH): processos, GPU, tail dos logs, watchdog vivo?
STATE=$($SSHC 'bash -lc "
echo TRAIN=\$(pgrep -fc \"[t]rain_voice.py\" 2>/dev/null)
echo ORCH=\$(pgrep -fc \"[g]rid_overnight.sh\" 2>/dev/null)
echo WD=\$(pgrep -fc \"[w]atchdog_overnight.sh\" 2>/dev/null)
echo SUP=\$(pgrep -fc \"[s]upervise.sh\" 2>/dev/null)
echo BLOCKED=\$(cat /workspace/grid/overnight.blocked 2>/dev/null)
echo GPU=\$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d \" \")
echo ---OVERNIGHT---
tail -n 8 /workspace/grid/overnight.log 2>/dev/null
echo ---WATCHDOG---
tail -n 4 /workspace/grid/watchdog.log 2>/dev/null
"' 2>/dev/null)
echo "$STATE"

# 2) tabela comparativa de WER (todos os ov_*)
echo "--- TABELA WER ---"
$SSHC 'python3 - <<PY 2>/dev/null
import json, glob, os
rows=[]
for d in sorted(glob.glob("/workspace/TTS-ptbr-data/runs/ov_*")):
    rj=os.path.join(d,"stage_b_result.json")
    if not os.path.exists(rj): continue
    try: r=json.load(open(rj))
    except: continue
    rows.append((os.path.basename(d)[3:], r.get("wer"), r.get("text_mode"), r.get("lr"), r.get("rank"), r.get("clips"), r.get("data_file","")))
if not rows: print("(nenhum arm concluído ainda)")
for a,w,m,lr,rk,cl,df in rows:
    ws=f"{w*100:.0f}%" if isinstance(w,(int,float)) else str(w)
    print(f"  {a:<13}{ws:>6}  {str(m):<9} lr={lr} r={rk} clips={cl} {os.path.basename(str(df))}")
PY' 2>/dev/null

# 3) puxa wavs+json dos arms concluídos que ainda não baixei
echo "--- COLETA ---"
for arm in $($SSHC "ls -d $RUNS/ov_* 2>/dev/null | xargs -n1 basename" 2>/dev/null); do
  if $SSHC "test -f $RUNS/$arm/stage_b_result.json" 2>/dev/null; then
    od="$DEST/$arm"
    if [ ! -f "$od/stage_b_result.json" ]; then
      mkdir -p "$od"
      scp -q -o ConnectTimeout=20 $POD:"$RUNS/$arm/gen/*.wav" "$od/" 2>/dev/null
      scp -q -o ConnectTimeout=20 $POD:"$RUNS/$arm/gen/per_sentence.jsonl" "$od/" 2>/dev/null
      scp -q -o ConnectTimeout=20 $POD:"$RUNS/$arm/stage_b_result.json" "$od/" 2>/dev/null
      echo "  baixei $arm"
    fi
  fi
done

# 4) anti-idle do lado do Mac (3ª camada; o supervise.sh no pod é a 1ª). Se o SUPERVISE
#    caiu E não está 'blocked' E antes do deadline → re-lança o supervise (que respawna o watchdog).
SUP=$(echo "$STATE" | grep -oE "^SUP=[0-9]+" | cut -d= -f2)
BLOCKED=$(echo "$STATE" | grep -oE "^BLOCKED=.+" | cut -d= -f2-)
if [ -n "$BLOCKED" ]; then
  echo "  ⚠️ POD BLOCKED (preflight abortou): $BLOCKED — precisa de intervenção (dado/base faltando)"
elif [ "$NOW_UTC" -lt "$DEADLINE" ] && [ "${SUP:-0}" = "0" ]; then
  echo "  supervise caiu → re-lançando no pod (respawna o watchdog)"
  $SSHC 'cd /workspace/TTS-ptbr && setsid nohup bash /workspace/TTS-ptbr/runpod/supervise.sh >/workspace/grid/supervise.out 2>&1 < /dev/null &' 2>/dev/null
fi
echo "===== fim review ====="
