#!/usr/bin/env bash
# ============================================================================
# SUPERVISE (roda NO POD, setsid nohup) — respawna o WATCHDOG, que é a raiz única
# de recuperação pod-side. Sem isto, se o watchdog morrer E o Mac dormir, a árvore
# inteira (arms←grid←watchdog) morre e a GPU idla a noite toda. 4 linhas, sem
# dependência de cron (RunPod frequentemente não tem crond). Encerra no deadline.
#
# Lançar:  setsid nohup bash /workspace/TTS-ptbr/runpod/supervise.sh >/workspace/grid/supervise.out 2>&1 < /dev/null &
# ============================================================================
set -u
LOGD=/workspace/grid
WD=/workspace/TTS-ptbr/runpod/watchdog_overnight.sh
mkdir -p "$LOGD"
exec 7>"$LOGD/supervise.lock"
flock -n 7 || { echo "supervise já vivo — saio"; exit 0; }
DEADLINE=$(date -u -d "2026-06-19 14:00:00" +%s)
while [ "$(date -u +%s)" -lt "$DEADLINE" ]; do
  if ! pgrep -f "watchdog_overnight.sh" >/dev/null 2>&1; then
    echo "$(date -u) [sup] watchdog morto → relanço" >> "$LOGD/supervise.log"
    cd /workspace/TTS-ptbr && setsid nohup bash "$WD" >> "$LOGD/watchdog.out" 2>&1 < /dev/null &
    sleep 10
  fi
  sleep 60
done
echo "$(date -u) [sup] deadline — encerro" >> "$LOGD/supervise.log"
