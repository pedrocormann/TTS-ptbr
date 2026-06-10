"""Turn engine: captura de mic + endpointing (silero-vad) + barge-in.

Mantém um InputStream sempre aberto. Estados:
  LISTENING  — acumula fala do usuário; fim de turno = silêncio >= endpoint_ms
  SPEAKING   — agente tocando áudio; se o usuário falar (VAD), corta o playback
               (barge-in) e volta a LISTENING já capturando.
Sem GUI; tudo por callback. Latências logadas por estágio.
"""
from __future__ import annotations

import queue
import threading
import time

import numpy as np

SR = 16000          # VAD/ASR trabalham em 16k; TTS sai em 24k (playback separado)
FRAME_MS = 32       # silero janela 512 amostras @16k
FRAME = 512


class VAD:
    """silero-vad streaming. prob > threshold = fala.
    Prefere o pacote pip oficial (sem API do GitHub); fallback torch.hub."""

    def __init__(self, threshold: float = 0.5):
        import torch
        try:
            from silero_vad import load_silero_vad
            self.model = load_silero_vad()
        except ImportError:
            self.model, _ = torch.hub.load("snakers4/silero-vad", "silero_vad",
                                           trust_repo=True)
        self.threshold = threshold
        self._torch = torch

    def is_speech(self, frame_f32: np.ndarray) -> bool:
        t = self._torch.from_numpy(frame_f32)
        prob = self.model(t, SR).item()
        return prob >= self.threshold

    def reset(self):
        self.model.reset_states()


class Player:
    """Playback interrompível (barge-in corta em ~1 buffer)."""

    def __init__(self, sr_out: int = 24000):
        self.sr_out = sr_out
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.playing = threading.Event()

    def play(self, audio_f32: np.ndarray):
        import sounddevice as sd
        self.stop()
        self._stop.clear()

        def _run():
            self.playing.set()
            try:
                blocksize = int(self.sr_out * 0.08)  # 80ms — granularidade do corte
                with sd.OutputStream(samplerate=self.sr_out, channels=1,
                                     dtype="float32", blocksize=blocksize) as out:
                    for i in range(0, len(audio_f32), blocksize):
                        if self._stop.is_set():
                            break
                        out.write(audio_f32[i:i + blocksize].reshape(-1, 1))
            finally:
                self.playing.clear()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)


class TurnEngine:
    def __init__(self, endpoint_ms: int = 600, min_turn_ms: int = 300,
                 barge_in_frames: int = 4, device: int | None = None):
        self.vad = VAD()
        self.player = Player()
        self.endpoint_frames = max(1, endpoint_ms // FRAME_MS)
        self.min_turn_frames = max(1, min_turn_ms // FRAME_MS)
        self.barge_in_frames = barge_in_frames  # frames seguidos de fala p/ cortar
        self.device = device
        self._q: queue.Queue[np.ndarray] = queue.Queue()

    def _callback(self, indata, frames, t, status):
        self._q.put(indata[:, 0].copy())

    def listen_turn(self) -> tuple[np.ndarray, dict]:
        """Bloqueia até capturar um turno completo do usuário.
        Se o agente estiver falando e o usuário entrar, faz barge-in e captura."""
        import sounddevice as sd
        buf: list[np.ndarray] = []
        speech_frames = 0
        silence_run = 0
        consec_speech = 0
        started = False
        t0 = None
        self.vad.reset()
        with sd.InputStream(samplerate=SR, channels=1, dtype="float32",
                            blocksize=FRAME, device=self.device,
                            callback=self._callback):
            while True:
                frame = self._q.get()
                if frame.shape[0] != FRAME:   # garante janela exata p/ o VAD
                    continue
                speaking = self.vad.is_speech(frame)
                if self.player.playing.is_set():
                    # agente falando: monitora barge-in
                    consec_speech = consec_speech + 1 if speaking else 0
                    if consec_speech >= self.barge_in_frames:
                        self.player.stop()          # BARGE-IN
                        started, buf = True, [frame]
                        speech_frames, silence_run = 1, 0
                        t0 = time.perf_counter()
                    continue
                if speaking:
                    if not started:
                        started = True
                        t0 = time.perf_counter()
                    buf.append(frame)
                    speech_frames += 1
                    silence_run = 0
                elif started:
                    buf.append(frame)
                    silence_run += 1
                    if (silence_run >= self.endpoint_frames
                            and speech_frames >= self.min_turn_frames):
                        audio = np.concatenate(buf)
                        meta = {"t_start": t0, "t_end": time.perf_counter(),
                                "dur_s": len(audio) / SR}
                        return audio, meta

    def speak(self, audio_24k: np.ndarray):
        self.player.play(audio_24k)

    def wait_speech_end(self):
        while self.player.playing.is_set():
            time.sleep(0.05)
