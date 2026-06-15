#!/usr/bin/env bash
# Lança a bateria em BACKGROUND (nohup) com log em /workspace/bateria.log.
# Assim a sessão SSH pode cair / o Claude pode só dar `tail` no log e voltar,
# sem segurar o terminal pelas ~3h de treino.
#
# Uso:
#   bash runpod/run_bg.sh                          # bateria completa
#   bash runpod/run_bg.sh --experiments A1_cml --lr 2e-5 --per-exp-min 30
#   tail -f /workspace/bateria.log                 # acompanhar
#   tail -n 40 /workspace/bateria.log              # espiar (Claude via ssh "...")
#   pkill -f train_bateria.py                       # abortar
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"   # raiz do repo (robusto a qualquer cwd/invocação)
LOG=/workspace/bateria.log
echo "▶ lançando bateria em background → $LOG"
nohup python -u runpod/train_bateria.py "$@" > "$LOG" 2>&1 &
echo "   PID $! · acompanhe com: tail -f $LOG"
