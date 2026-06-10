"""Adaptadores de TTS — interface única: synth(text) -> (audio_f32, sr).

Engines (REPLAN Trilha A/M; APIs verificadas em dossier-2026-06/70-api-recipes.md):
  pocket           Kyutai Pocket-TTS pt (CC-BY) — CPU, ~200ms; roda no Mac HOJE.
  chatterbox-ptbr  pack pt-BR dedicado (MIT) — GPU; clone por referência.
  csm              CSM-1B/finetune (Apache) — GPU; condiciona no ÁUDIO do
                   histórico da conversa (o "segredo Maya"): use add_context().
  qwen3            Qwen3-TTS CustomVoice (Apache) — GPU; instruct de emoção.
"""
from __future__ import annotations

import numpy as np

TTS_SR = 24000  # todos os engines saem em 24 kHz


class BaseTTS:
    sr = TTS_SR

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        raise NotImplementedError

    def add_context(self, role: str, text: str, audio_24k: np.ndarray) -> None:
        """Histórico de conversa (só o CSM usa; no resto é no-op)."""


class PocketTTSAdapter(BaseTTS):
    def __init__(self, voice: str, language: str = "portuguese"):
        from pocket_tts import TTSModel
        self.model = TTSModel.load_model()  # config de língua via packaging do pocket-tts
        self.language = language
        self.state = self.model.get_state_for_audio_prompt(voice)  # wav | .safetensors | nome
        self.sr = getattr(self.model, "sample_rate", TTS_SR)

    def synth(self, text):
        audio = self.model.generate_audio(self.state, text)
        if hasattr(audio, "numpy"):
            audio = audio.numpy()
        return audio.astype(np.float32).reshape(-1), self.sr


class ChatterboxPTBRAdapter(BaseTTS):
    def __init__(self, voice: str, device: str = "cuda"):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                             / "tools" / "data" / "synth"))
        from synth_tts import _load_chatterbox_ptbr  # reusa a montagem do pack
        self.model = _load_chatterbox_ptbr()
        self.voice = voice  # wav de referência ~7-10s
        self.sr = self.model.sr

    def synth(self, text):
        wav = self.model.generate(text, language_id="pt",
                                  audio_prompt_path=self.voice)
        return wav.squeeze(0).cpu().numpy().astype(np.float32), self.sr


class CSMAdapter(BaseTTS):
    """Condicionamento de áudio-contexto: a prosódia/emoção do próximo turno vem
    do histórico da conversa (usuário E agente), como na Maya. roles: "0"=agente,
    "1"=usuário."""

    def __init__(self, model_dir: str = "unsloth/csm-1b", voice: str | None = None,
                 voice_text: str | None = None, max_context_turns: int = 4):
        import torch
        from transformers import AutoProcessor, CsmForConditionalGeneration
        self.torch = torch
        self.proc = AutoProcessor.from_pretrained(model_dir)
        self.model = CsmForConditionalGeneration.from_pretrained(
            model_dir, torch_dtype=torch.bfloat16, device_map="cuda")
        self.context: list[dict] = []
        self.max_turns = max_context_turns
        if voice and voice_text:  # âncora de voz: 1 utterance de referência fixa
            import librosa
            arr, _ = librosa.load(voice, sr=TTS_SR, mono=True)
            self.anchor = {"role": "0", "content": [
                {"type": "text", "text": voice_text},
                {"type": "audio", "path": arr}]}
        else:
            self.anchor = None

    def add_context(self, role, text, audio_24k):
        self.context.append({"role": role, "content": [
            {"type": "text", "text": text},
            {"type": "audio", "path": audio_24k}]})
        self.context = self.context[-self.max_turns:]

    def synth(self, text):
        conv = ([self.anchor] if self.anchor else []) + self.context + [
            {"role": "0", "content": [{"type": "text", "text": text}]}]
        inputs = self.proc.apply_chat_template(conv, tokenize=True, return_dict=True)
        with self.torch.no_grad():
            audio = self.model.generate(**inputs.to("cuda"), max_new_tokens=375,
                                        output_audio=True)
        wav = audio[0].to(self.torch.float32).cpu().numpy().reshape(-1)
        self.add_context("0", text, wav)  # a própria fala vira contexto
        return wav, TTS_SR


class Qwen3Adapter(BaseTTS):
    def __init__(self, voice: str = "Ethan",
                 model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
                 instruct: str | None = None):
        import torch
        from qwen_tts import Qwen3TTSModel
        self.model = Qwen3TTSModel.from_pretrained(
            model_id, device_map="cuda:0", dtype=torch.bfloat16,
            attn_implementation="sdpa")
        self.voice, self.instruct = voice, instruct

    def synth(self, text):
        kwargs = dict(text=text, language="Portuguese", speaker=self.voice)
        if self.instruct:
            kwargs["instruct"] = self.instruct
        wavs, sr = self.model.generate_custom_voice(**kwargs)
        wav = wavs[0] if isinstance(wavs, (list, tuple)) else wavs
        if hasattr(wav, "cpu"):
            wav = wav.cpu().numpy()
        return np.asarray(wav, dtype=np.float32).reshape(-1), sr


def make_tts(engine: str, voice: str | None, **kw) -> BaseTTS:
    if engine == "pocket":
        return PocketTTSAdapter(voice or "rafael")
    if engine == "chatterbox-ptbr":
        return ChatterboxPTBRAdapter(voice)
    if engine == "csm":
        return CSMAdapter(model_dir=kw.get("model_dir") or "unsloth/csm-1b",
                          voice=voice, voice_text=kw.get("voice_text"))
    if engine == "qwen3":
        return Qwen3Adapter(voice or "Ethan")
    raise SystemExit(f"engine desconhecido: {engine}")
