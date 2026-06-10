"""ASR do turno do usuário — faster-whisper (MIT), pt."""
from __future__ import annotations

import numpy as np


class ASR:
    def __init__(self, model: str = "small", device: str = "auto",
                 compute_type: str = "auto"):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio_16k: np.ndarray) -> str:
        segs, _ = self.model.transcribe(audio_16k, language="pt", vad_filter=False,
                                        beam_size=1)  # beam 1 = latência mínima
        return " ".join(s.text.strip() for s in segs).strip()
