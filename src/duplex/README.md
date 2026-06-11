# src/duplex — Maya-BR v0 (esqueleto da Trilha M)

> **STATUS: SCAFFOLD HONESTO (2026-06-10) — arquitetura ligada, NÃO testado
> end-to-end** (sem mic/GPU no ambiente autônomo). Primeiro alvo executável:
> Mac do Pedro com engine `pocket` (CPU). Eval: `eval/maya_parity.md`.

Hipótese arquitetural (REPLAN Trilha M): a Maya ≈ cascata engenheirada —
turn-engine esperto + ASR streaming + LLM persona (backstage) + TTS condicionado
no ÁUDIO do histórico da conversa. Este pacote implementa exatamente isso:

```
mic → turn_engine (silero-vad: endpointing + BARGE-IN)
    → asr (faster-whisper)
    → llm (qualquer endpoint OpenAI-compatible: Gemini/Maritaca/sglang/ollama)
    → tts_adapter (pocket | chatterbox-ptbr | csm | qwen3)
    → playback (interrompível)
histórico de ÁUDIO da conversa alimenta o CSM (o "segredo Maya") e o texto alimenta o LLM.
```

## Rodar (Mac, CPU, hoje — voz default pt ou clone após aceitar o gate)

```bash
pip install sounddevice soundfile numpy faster-whisper pocket-tts openai
python -m src.duplex.chat_loop --tts pocket --voice /caminho/minha_voz.wav \
    --llm-base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
    --llm-model gemini-2.0-flash --llm-key $GEMINI_KEY
```

GPU (Colab/box): `--tts csm` usa o checkpoint do notebook 2 com contexto de
conversa; `--tts qwen3` usa CustomVoice + instruct.

## Decisões embutidas

- **Persona em `persona_ptbr.txt`** (system prompt) — respostas CURTAS, orais,
  com backchannels escritos; o LLM é trocável sem tocar na voz (REPLAN §D).
- **Barge-in**: o playback roda em thread com flag; VAD detecta fala do usuário
  durante o playback → corta em <1 frame (80ms de buffer).
- **Contexto de áudio**: cada turno (usuário e agente) entra numa janela
  deslizante (default 4 turnos) que o adaptador CSM consome via
  `apply_chat_template` multi-turno (roles "0"=agente, "1"=usuário).
- Latência: medida e logada por estágio (vad_end→asr, asr→llm_first,
  llm→tts_first, total) — alimenta a tabela A do maya_parity.md.
```
