#!/usr/bin/env bash
# ============================================================================
# WATCHDOG OVERNIGHT (roda NO POD, nohup) — a prova-de-idle real, imune ao Mac.
# Revisado adversarialmente. A cada 120s:
#  1. HANG-DETECTION: se train_voice está VIVO mas o log do arm não escreve há >600s
#     (TimeCap só capa on_step_end; step/eval travado nunca para) → pkill (grid resume re-roda).
#  2. ANTI-IDLE: se NADA treina E nenhum orquestrador vivo E não está 'blocked' → (re)lança o grid.
#  3. Limpa disco (>90%) e respeita overnight.blocked (preflight abortou → não relança cego).
# Checagens por EXIT-CODE (não `pgrep -fc || echo 0`, que vira "0\n0" e quebra a guarda).
# Lança o grid pelo PATH REAL do repo (/workspace/TTS-ptbr/runpod/), não cópia fantasma.
#
# Lançar:  setsid nohup bash /workspace/TTS-ptbr/runpod/watchdog_overnight.sh >/workspace/grid/watchdog.out 2>&1 < /dev/null &
# ============================================================================
set -u
LOGD=/workspace/grid
REPO=/workspace/TTS-ptbr
GRID="$REPO/runpod/grid_overnight.sh"
mkdir -p "$LOGD"
# instância única
exec 8>"$LOGD/watchdog.lock"
flock -n 8 || { echo "watchdog já vivo — saio"; exit 0; }
echo $$ > "$LOGD/watchdog.pid"
DEADLINE=$(date -u -d "2026-06-19 14:00:00" +%s)   # 11h BRT (~12h)
HANG_S=600
log () { echo "$(date -u) [wd] $*" >> "$LOGD/watchdog.log"; }
log "START deadline=$(date -u -d @$DEADLINE) grid=$GRID"

while true; do
  now=$(date -u +%s)
  [ "$now" -ge "$DEADLINE" ] && { log "deadline — watchdog encerra"; break; }

  # --- disco: limpa checkpoints se >90% (df -P = 1 linha, robusto) ---
  pct=$(df -P /workspace 2>/dev/null | awk 'END{gsub("%","",$5); print $5+0}')
  if [[ "$pct" =~ ^[0-9]+$ ]] && [ "$pct" -gt 90 ]; then
    find /workspace/TTS-ptbr-data/runs -type d -name 'checkpoint-*' -exec rm -rf {} + 2>/dev/null
    log "disco ${pct}% → limpei checkpoints intermediários"
  fi

  # --- 1) HANG: train_voice vivo mas log do arm parado há muito tempo ---
  if pgrep -f "train_voice.py" >/dev/null 2>&1; then
    newest=$(ls -t "$LOGD"/ov_*.log 2>/dev/null | head -1)
    if [ -n "$newest" ]; then
      age=$(( now - $(stat -c %Y "$newest" 2>/dev/null || echo "$now") ))
      if [ "$age" -gt "$HANG_S" ]; then
        log "HANG: train_voice vivo, $newest parado ${age}s (>${HANG_S}) → pkill (grid resume re-roda)"
        pkill -9 -f train_voice.py; sleep 8
      fi
    fi
  fi

  # --- 2) ANTI-IDLE: nada treinando E nenhum orquestrador vivo ---
  if ! pgrep -f "train_voice.py" >/dev/null 2>&1 && ! pgrep -f "grid_overnight.sh" >/dev/null 2>&1; then
    if [ -f "$LOGD/overnight.blocked" ]; then
      log "BLOCKED (preflight: $(cat "$LOGD/overnight.blocked" 2>/dev/null)) — não relanço"
      sleep 120; continue
    fi
    log "GPU ociosa + sem orquestrador → (re)lanço $GRID"
    cd "$REPO" && nohup bash "$GRID" >> "$LOGD/orchestrator.log" 2>&1 &
    sleep 40   # deixa subir antes de re-checar (evita double-launch)
  fi
  sleep 120
done
rm -f "$LOGD/watchdog.pid"
