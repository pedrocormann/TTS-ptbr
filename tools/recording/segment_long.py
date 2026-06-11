#!/usr/bin/env python3
"""Segmenta takes longos (monólogos/diálogos) em utterances para treino.

Local (CPU): segmentação por energia (default) ou silero-vad (--vad silero, requer torch).
A TRANSCRIÇÃO dos segmentos roda no Colab (faster-whisper) — este script gera o
to_transcribe.jsonl que o notebook consome.

Uso:
  python tools/recording/segment_long.py --session ses01 --kinds monologo dialogo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

MIN_SEG_S = 1.0
MAX_SEG_S = 20.0
SIL_DB = -42.0
MIN_SIL_S = 0.35
PAD_S = 0.15


def energy_segments(audio: np.ndarray, sr: int) -> list[tuple[int, int]]:
    win = max(1, int(0.02 * sr))
    n = (audio.size // win) * win
    frames = audio[:n].reshape(-1, win)
    rms_db = 20 * np.log10(np.maximum(np.sqrt((frames ** 2).mean(axis=1)), 1e-9))
    voiced = rms_db > SIL_DB
    segs, start = [], None
    sil_run = 0
    min_sil_frames = int(MIN_SIL_S / 0.02)
    for k, v in enumerate(voiced):
        if v:
            if start is None:
                start = k
            sil_run = 0
        elif start is not None:
            sil_run += 1
            if sil_run >= min_sil_frames:
                segs.append((start, k - sil_run + 1))
                start, sil_run = None, 0
    if start is not None:
        segs.append((start, len(voiced)))

    out = []
    for a, b in segs:
        s = max(0, a * win - int(PAD_S * sr))
        e = min(audio.size, b * win + int(PAD_S * sr))
        dur = (e - s) / sr
        if dur < MIN_SEG_S:
            continue
        # quebra segmentos longos demais em pedaços de ~MAX_SEG_S no vale de energia
        while dur > MAX_SEG_S:
            cut = s + int(MAX_SEG_S * sr)
            out.append((s, cut))
            s = cut
            dur = (e - s) / sr
        out.append((s, e))
    return out


def silero_segments(audio: np.ndarray, sr: int) -> list[tuple[int, int]]:
    import torch
    model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
    get_speech_timestamps = utils[0]
    wav16 = audio if sr == 16000 else None
    if wav16 is None:
        x_old = np.linspace(0, 1, audio.size)
        x_new = np.linspace(0, 1, int(audio.size * 16000 / sr))
        wav16 = np.interp(x_new, x_old, audio).astype(np.float32)
    ts = get_speech_timestamps(torch.from_numpy(wav16), model,
                               min_speech_duration_ms=int(MIN_SEG_S * 1000),
                               max_speech_duration_s=MAX_SEG_S)
    scale = sr / 16000
    return [(int(t["start"] * scale), int(t["end"] * scale)) for t in ts]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--kinds", nargs="+", default=["monologo", "dialogo"])
    ap.add_argument("--vad", choices=["energy", "silero"], default="energy")
    args = ap.parse_args()

    ses_dir = Path(args.raw_root) / args.session
    meta = ses_dir / "metadata.jsonl"
    seg_dir = ses_dir / "segments"
    seg_dir.mkdir(exist_ok=True)
    out_meta = seg_dir / "to_transcribe.jsonl"
    seg_fn = silero_segments if args.vad == "silero" else energy_segments

    n_out = 0
    with out_meta.open("w", encoding="utf-8") as fo:
        for line in meta.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") not in args.kinds:
                continue
            audio, sr = sf.read(r["audio"], dtype="float32", always_2d=False)
            if audio.ndim > 1:
                audio = audio[:, 0]
            for k, (s, e) in enumerate(seg_fn(audio, sr)):
                seg_path = seg_dir / f"{r['id']}_seg{k:03d}.wav"
                sf.write(seg_path, audio[s:e], sr, subtype="PCM_24")
                fo.write(json.dumps({
                    "id": f"{r['id']}_seg{k:03d}", "audio": str(seg_path),
                    "source_id": r["id"], "kind": r["kind"], "style": r.get("style"),
                    "intensity": r.get("intensity"), "accent": r.get("accent"),
                    "speaker": r.get("speaker"), "session": r.get("session"),
                    "dur_s": round((e - s) / sr, 2), "text": None,
                }, ensure_ascii=False) + "\n")
                n_out += 1
    print(f"✂️  {n_out} segmentos → {seg_dir}\n   transcreva no Colab (notebook 0) e mescle no export.")


if __name__ == "__main__":
    main()
