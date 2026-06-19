#!/usr/bin/env bash
# ============================================================================
# WATCHDOG OVERNIGHT (roda NO POD, nohup) — a prova-de-idle real, imune ao Mac.
# A cada 120s: se a GPU NÃO está treinando (sem train_voice) E nenhum orquestrador
# vivo E ainda não passou do deadline → (re)lança grid_overnight.sh (RESUMÍVEL,
# pula arms já feitos). A GPU NUNCA fica ociosa até 9h BRT, mesmo se o Mac/SSH cair
# ou o orquestrador morrer. Sem double-launch (só lança quando NADA treina + sem orquestrador).
# Também faz limpeza de disco proativa (>90%) p/ os adapters não entupirem o volume.
#
# Lançar:  nohup bash runpod/watchdog_overnight.sh >/workspace/grid/watchdog.out 2>&1 &
# Parar:   pkill -f watchdog_overnight.sh
# ============================================================================
set -u
LOGD=/workspace/grid
mkdir -p "$LOGD"
echo $$ > "$LOGD/watchdog.pid"
DEADLINE=$(date -u -d "2026-06-19 14:00:00" +%s)   # 11h BRT (~12h de janela)
log () { echo "$(date -u) [wd] $*" >> "$LOGD/watchdog.log"; }
log "START deadline=$(date -u -d @$DEADLINE)"

while true; do
  now=$(date -u +%s)
  if [ "$now" -ge "$DEADLINE" ]; then log "deadline — watchdog encerra"; break; fi

  # --- disco: limpa checkpoints intermediários se > 90% (mantém final/ e o arrow ativo) ---
  pct=$(df /workspace 2>/dev/null | awk 'NR==2{gsub("%","",$5);print $5}')
  if [ -n "${pct:-}" ] && [ "${pct:-0}" -gt 90 ] 2>/dev/null; then
    find /workspace/TTS-ptbr-data/runs -type d -name 'checkpoint-*' -exec rm -rf {} + 2>/dev/null
    log "disco ${pct}% → limpei checkpoints intermediários"
  fi

  # --- anti-idle ---
  training=$(pgrep -fc "train_voice.py" 2>/dev/null || echo 0)
  orch=$(pgrep -fc "grid_overnight.sh" 2>/dev/null || echo 0)
  if [ "${training:-0}" -eq 0 ] && [ "${orch:-0}" -eq 0 ]; then
    log "GPU ociosa + sem orquestrador → (re)lanço grid_overnight.sh"
    cd /workspace && nohup bash /workspace/grid_overnight.sh >> "$LOGD/orchestrator.log" 2>&1 &
    sleep 40   # deixa o orquestrador subir antes de re-checar (evita double-launch)
  fi
  sleep 120
done
rm -f "$LOGD/watchdog.pid"
