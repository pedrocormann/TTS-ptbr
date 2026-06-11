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

    def prob(self, frame_f32: np.ndarray) -> float:
        t = self._torch.from_numpy(frame_f32)
        return self.model(t, SR).item()

    def is_speech(self, frame_f32: np.ndarray) -> bool:
        return self.prob(frame_f32) >= self.threshold

    def reset(self):
        self.model.reset_states()


class SmartTurn:
    """smart-turn v3 (Pipecat/Daily, BSD-2): endpointing SEMÂNTICO por áudio.
    2º estágio após o silero: 'esse silêncio é fim de turno ou só pausa?'
    ONNX 8MB, ~12-95ms em CPU, 23 línguas (pt acc 95.4%). Receita verificada
    no repo oficial (inference.py): últimos 8s @16kHz → WhisperFeatureExtractor
    → input_features → sigmoid; >0.5 = turno completo."""

    MAX_S = 8

    def __init__(self):
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download, list_repo_files
        from transformers import WhisperFeatureExtractor
        repo = "pipecat-ai/smart-turn-v3"
        onnxs = sorted(f for f in list_repo_files(repo) if f.endswith(".onnx"))
        path = hf_hub_download(repo, onnxs[-1])  # mais novo (v3.2 > v3.1)
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.sess = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
        self.fe = WhisperFeatureExtractor(feature_size=80)

    def is_complete(self, audio_16k: np.ndarray) -> float:
        n = self.MAX_S * SR
        tail = audio_16k[-n:] if audio_16k.size > n else np.concatenate(
            [np.zeros(n - audio_16k.size, dtype=np.float32), audio_16k])
        feats = self.fe(tail, sampling_rate=SR, padding="max_length",
                        max_length=n, return_tensors="np",
                        do_normalize=True)["input_features"].astype(np.float32)
        prob = self.sess.run(None, {"input_features": feats})[0][0].item()
        return float(prob)


class Player:
    """Playback interrompível (barge-in corta em ~1 buffer)."""

    def __init__(self, sr_out: int = 24000):
        self.sr_out = sr_out
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.playing = threading.Event()
        self.ended_at = 0.0  # p/ cooldown anti-eco pós-playback
        self.total_samples = 0
        self.played_samples = 0
        self._interrupted = False

    def consume_interruption(self) -> tuple[bool, float]:
        """(houve barge-in?, fração OUVIDA do último playback). Reseta o flag."""
        was = self._interrupted
        frac = (self.played_samples / self.total_samples) if self.total_samples else 1.0
        self._interrupted = False
        return was, min(1.0, frac)

    def play(self, audio_f32: np.ndarray):
        import sounddevice as sd
        self.stop()
        self._stop.clear()

        self.total_samples = len(audio_f32)
        self.played_samples = 0
        self._interrupted = False

        def _run():
            self.playing.set()
            try:
                blocksize = int(self.sr_out * 0.08)  # 80ms — granularidade do corte
                with sd.OutputStream(samplerate=self.sr_out, channels=1,
                                     dtype="float32", blocksize=blocksize) as out:
                    for i in range(0, len(audio_f32), blocksize):
                        if self._stop.is_set():
                            self._interrupted = True  # barge-in: parou no meio
                            break
                        out.write(audio_f32[i:i + blocksize].reshape(-1, 1))
                        self.played_samples = min(i + blocksize, len(audio_f32))
            finally:
                self.playing.clear()
                self.ended_at = time.time()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)


class TurnEngine:
    def __init__(self, endpoint_ms: int = 600, min_turn_ms: int = 300,
                 barge_in_frames: int = 8, device: int | None = None,
                 barge_in: bool = False, echo_cooldown_s: float = 0.35,
                 barge_in_threshold: float = 0.85):
        """barge_in=False (default) = half-duplex: mic IGNORADO enquanto o agente
        fala — único modo seguro em caixa de som (eco). Com FONES, ligue
        barge_in=True (gate alto: prob>=0.85 por 8 frames ≈ 256ms).
        Endpointing 2 estágios: silêncio CURTO (~280ms) → smart-turn semântico
        decide se acabou; fallback DURO em endpoint_ms se ele disser 'pausa'."""
        self.vad = VAD()
        try:
            self.smart_turn = SmartTurn()
        except Exception:
            self.smart_turn = None  # sem onnx/transformers: cai no silêncio puro
        self.short_silence_frames = max(1, 280 // FRAME_MS)
        self.player = Player()
        self.endpoint_frames = max(1, endpoint_ms // FRAME_MS)
        self.min_turn_frames = max(1, min_turn_ms // FRAME_MS)
        self.barge_in_frames = barge_in_frames  # frames seguidos de fala p/ cortar
        self.barge_in = barge_in
        self.barge_in_threshold = barge_in_threshold
        self.echo_cooldown_s = echo_cooldown_s
        self.device = device
        self._q: queue.Queue[np.ndarray] = queue.Queue()

    def _callback(self, indata, frames, t, status):
        self._q.put(indata[:, 0].copy())

    def listen_turn(self, stop_event=None) -> tuple[np.ndarray, dict] | None:
        """Bloqueia até capturar um turno completo do usuário (None se stop_event).
        Se o agente estiver falando e o usuário entrar, faz barge-in e captura."""
        import queue as _q
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
                if stop_event is not None and stop_event.is_set():
                    self.player.stop()
                    return None
                try:
                    frame = self._q.get(timeout=0.5)
                except _q.Empty:
                    continue
                if frame.shape[0] != FRAME:   # garante janela exata p/ o VAD
                    continue
                if self.player.playing.is_set():
                    if not self.barge_in:
                        continue                    # half-duplex: ignora eco
                    # com fones: barge-in com gate ALTO (anti-eco residual)
                    strong = self.vad.prob(frame) >= self.barge_in_threshold
                    consec_speech = consec_speech + 1 if strong else 0
                    if consec_speech >= self.barge_in_frames:
                        self.player.stop()          # BARGE-IN
                        started, buf = True, [frame]
                        speech_frames, silence_run = 1, 0
                        t0 = time.perf_counter()
                    continue
                # cooldown anti-eco: ignora a cauda logo após o playback acabar
                if (not started and self.player.ended_at
                        and time.time() - self.player.ended_at < self.echo_cooldown_s):
                    continue
                speaking = self.vad.is_speech(frame)
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
                    if speech_frames < self.min_turn_frames:
                        continue
                    done = False
                    if silence_run >= self.endpoint_frames:
                        done = True          # fallback duro: silêncio longo
                    elif (self.smart_turn is not None
                          and silence_run == self.short_silence_frames):
                        # estágio 2: o silêncio curto é FIM DE TURNO ou pausa?
                        prob = self.smart_turn.is_complete(np.concatenate(buf))
                        done = prob > 0.5
                    if done:
                        audio = np.concatenate(buf)
                        meta = {"t_start": t0, "t_end": time.perf_counter(),
                                "dur_s": len(audio) / SR}
                        return audio, meta

    def speak(self, audio_24k: np.ndarray):
        self.player.play(audio_24k)

    def wait_speech_end(self):
        while self.player.playing.is_set():
            time.sleep(0.05)
