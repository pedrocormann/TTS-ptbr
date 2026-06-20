#!/bin/bash
# ============================================================================
# Maya-BR v0 — cascata conversacional COMPLETA no Mac (sem pod/GPU).
#   mic → VAD/turn (silero+SmartTurn) → ASR (faster-whisper) → LLM (Gemini Flash)
#   → TTS (Pocket-TTS clonando a voz do Pedro) → speaker. Mede latência por turno.
#
# Uso:
#   1) Edite src/duplex/.env e ponha sua GEMINI_API_KEY (nunca cole no chat).
#   2) bash src/duplex/run_maya.sh            # mic padrão
#      bash src/duplex/run_maya.sh --barge-in # interromper falando (SÓ com fones)
#      bash src/duplex/run_maya.sh --device 2 # escolher mic (lista os devices)
# ============================================================================
set -u
cd "$(dirname "$0")/../.." || exit 1   # raiz do repo
set -a; [ -f src/duplex/.env ] && . src/duplex/.env; set +a

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "❌ GEMINI_API_KEY vazia. Edite src/duplex/.env e cole sua chave do Gemini (ai.google.dev)."
  echo "   (NUNCA cole a chave no chat nem commite — o .env já está no .gitignore.)"
  exit 1
fi

PY=.venv-duplex/bin/python
BASE="https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL="${GEMINI_MODEL:-gemini-2.0-flash}"
REF="${MAYA_VOICE:-runpod_samples/maya_pocket_smoke/_referencia_pedro.wav}"
[ -f "$REF" ] || { echo "❌ voz de referência não achada: $REF"; exit 1; }

# 1) smoke do Gemini (confirma chave + endpoint ANTES de abrir o mic)
echo "🧪 testando Gemini ($MODEL)…"
GEMINI_API_KEY="$GEMINI_API_KEY" "$PY" - "$BASE" "$MODEL" <<'PY' || { echo "❌ Gemini falhou — confira a chave/modelo em src/duplex/.env"; exit 1; }
import os, sys
from openai import OpenAI
c = OpenAI(base_url=sys.argv[1], api_key=os.environ["GEMINI_API_KEY"])
r = c.chat.completions.create(model=sys.argv[2],
        messages=[{"role": "user", "content": "Responda em 4 palavras: tá funcionando?"}],
        max_tokens=20, temperature=0)
print("✅ Gemini respondeu:", r.choices[0].message.content.strip())
PY

# 2) cascata completa
echo "🎙️  Maya-BR v0 · voz=Pocket(clone do Pedro) · cérebro=$MODEL · Ctrl-C sai"
exec "$PY" -m src.duplex.chat_loop --tts pocket --voice "$REF" \
  --llm-base-url "$BASE" --llm-model "$MODEL" --llm-key "$GEMINI_API_KEY" "$@"
