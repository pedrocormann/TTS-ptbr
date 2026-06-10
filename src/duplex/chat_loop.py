"""Maya-BR v0 — loop de conversa por voz (CLI). SCAFFOLD: não testado end-to-end.

  python -m src.duplex.chat_loop --tts pocket --voice minha_voz.wav \
      --llm-base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
      --llm-model gemini-2.0-flash --llm-key $GEMINI_KEY

Fluxo por turno (latências logadas p/ eval/maya_parity.md tabela A):
  listen_turn (VAD + barge-in) → ASR → LLM (stream por sentença) → TTS → play
O áudio do USUÁRIO e do AGENTE entram no contexto do CSM (áudio-contexto à la Maya).
TODO v0.1: playback por sentença em streaming (hoje concatena e toca 1x).
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from .asr import ASR
from .llm import LLM
from .turn_engine import SR as MIC_SR, TurnEngine
from .tts_adapter import make_tts


def resample_16k(audio: np.ndarray, sr_in: int) -> np.ndarray:
    if sr_in == 16000:
        return audio
    x_old = np.linspace(0, 1, audio.size)
    x_new = np.linspace(0, 1, int(audio.size * 16000 / sr_in))
    return np.interp(x_new, x_old, audio).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tts", default="pocket",
                    choices=["pocket", "chatterbox-ptbr", "csm", "qwen3"])
    ap.add_argument("--voice", default=None,
                    help="pocket: wav/.safetensors/nome | chatterbox: ref wav | "
                         "csm: ref wav (com --voice-text) | qwen3: speaker preset")
    ap.add_argument("--voice-text", default=None,
                    help="csm: transcrição exata do wav de referência")
    ap.add_argument("--model-dir", default=None, help="csm: dir do finetune (notebook 04)")
    ap.add_argument("--asr-model", default="small")
    ap.add_argument("--llm-base-url", required=True)
    ap.add_argument("--llm-model", required=True)
    ap.add_argument("--llm-key", default="x")
    ap.add_argument("--endpoint-ms", type=int, default=600)
    ap.add_argument("--device", type=int, default=None,
                    help="índice do mic (liste com: python -c \"import sounddevice; print(sounddevice.query_devices())\")")
    ap.add_argument("--barge-in", action="store_true",
                    help="permite interromper falando por cima — SÓ COM FONES (eco)")
    args = ap.parse_args()

    print("⏳ carregando modelos…")
    engine = TurnEngine(endpoint_ms=args.endpoint_ms, device=args.device,
                        barge_in=args.barge_in)
    asr = ASR(model=args.asr_model)
    llm = LLM(base_url=args.llm_base_url, model=args.llm_model, api_key=args.llm_key)
    tts = make_tts(args.tts, args.voice, model_dir=args.model_dir,
                   voice_text=args.voice_text)
    engine.player.sr_out = tts.sr
    print(f"🎙️  Maya-BR v0 · tts={args.tts} · fale alguma coisa (Ctrl-C sai)\n")

    while True:
        result = engine.listen_turn()
        if result is None:
            break
        user_audio, meta = result
        t_vad_end = time.perf_counter()

        text = asr.transcribe(user_audio)
        t_asr = time.perf_counter()
        if not text:
            continue
        print(f"🧑 {text}")
        # turno do usuário entra no áudio-contexto (CSM); 16k→24k aproximado
        up = np.interp(np.linspace(0, 1, int(user_audio.size * tts.sr / MIC_SR)),
                       np.linspace(0, 1, user_audio.size), user_audio).astype(np.float32)
        tts.add_context("1", text, up)

        parts, t_llm_first, t_tts_first = [], None, None
        reply_text = []
        for sent in llm.reply_stream(text):
            if t_llm_first is None:
                t_llm_first = time.perf_counter()
            reply_text.append(sent)
            wav, _ = tts.synth(sent)
            if t_tts_first is None:
                t_tts_first = time.perf_counter()
            parts.append(wav)
        if not parts:
            continue
        full = np.concatenate(parts)
        print(f"🤖 {' '.join(reply_text)}")
        print(f"   ⏱ asr={t_asr - t_vad_end:.2f}s · llm₁={t_llm_first - t_asr:.2f}s "
              f"· tts₁={t_tts_first - t_llm_first:.2f}s "
              f"· total→1ºaudio={t_tts_first - t_vad_end:.2f}s")
        engine.speak(full)
        # próximo listen_turn monitora barge-in enquanto o agente fala


if __name__ == "__main__":
    main()
