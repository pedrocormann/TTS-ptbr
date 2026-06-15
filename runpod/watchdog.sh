#!/usr/bin/env bash
# Watchdog autônomo — roda DESTACADO no pod, vigia o treino e escreve /workspace/status.json
# a cada 30s pro Claude ler de fora. Faz limpeza de disco proativa. Detecta done/crash/stall.
# NÃO auto-reinicia treino (crash precisa de diagnóstico do Claude); só vigia e reporta.
#
# Lançar:  nohup bash runpod/watchdog.sh >/workspace/watchdog.log 2>&1 &
# Parar:   pkill -f watchdog.sh
set -uo pipefail
STATUS=/workspace/status.json
LOG=/workspace/bateria.log
JOB='train_bateria.py'

while true; do
  # --- disco: limpeza proativa se > 92% ---
  pct=$(df /workspace 2>/dev/null | awk 'NR==2{gsub("%","",$5);print $5}')
  cleanup=""
  if [ -n "${pct:-}" ] && [ "${pct:-0}" -gt 92 ] 2>/dev/null; then
    # SÓ checkpoints intermediários (mantém final/) e downloads temporários — NUNCA o
    # cache de dataset ativo (o treino está lendo o arrow; apagar quebraria a run).
    find /workspace/TTS-ptbr-data/runs -type d -name 'checkpoint-*' -exec rm -rf {} + 2>/dev/null
    rm -rf /workspace/hf_cache/downloads 2>/dev/null
    cleanup="limpou-checkpoints@${pct}pct"
  fi

  # --- métricas do log (tolerantes a vazio) ---
  last_loss=$(grep -oE "'loss': [0-9.]+" "$LOG" 2>/dev/null | tail -1 | grep -oE '[0-9.]+$')
  last_step=$(grep -oE '[0-9]+/[0-9]+ \[' "$LOG" 2>/dev/null | tail -1 | grep -oE '^[0-9]+/[0-9]+')
  cur_exp=$(grep -oE 'A[0-9]_[a-z]+  \(' "$LOG" 2>/dev/null | tail -1 | grep -oE 'A[0-9]_[a-z]+')
  gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')

  # --- estado do job ---
  if pgrep -f "$JOB" >/dev/null; then
    age=0
    if [ -f "$LOG" ]; then age=$(( $(date +%s) - $(stat -c %Y "$LOG" 2>/dev/null || echo "$(date +%s)") )); fi
    if [ "$age" -gt 360 ]; then state="stalled"; else state="running"; fi
    note="$cleanup"
  else
    age=0
    if grep -q 'BATERIA_results.md' "$LOG" 2>/dev/null; then
      state="done"; note="concluido $cleanup"
    else
      state="crashed"
      note=$(tail -4 "$LOG" 2>/dev/null | tr '\n\r' '  ' | tr -cd '[:alnum:] :./_=-' | tail -c 240)
    fi
  fi

  # --- escreve status.json atômico ---
  printf '{"ts":"%s","state":"%s","exp":"%s","loss":"%s","step":"%s","disk_pct":"%s","gpu":"%s","log_age_s":"%s","note":"%s"}\n' \
    "$(date -u +%FT%TZ)" "$state" "${cur_exp:-}" "${last_loss:-}" "${last_step:-}" "${pct:-}" "${gpu:-}" "$age" "${note:-}" \
    > "$STATUS.tmp" 2>/dev/null && mv "$STATUS.tmp" "$STATUS" 2>/dev/null

  sleep 30
done
