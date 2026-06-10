#!/usr/bin/env python3
"""Exporta as sessões gravadas para o dataset-mestre de treino.

Pipeline: trim de silêncio (energia) com padding → resample → normalização de
loudness (opcional) → split train/val → JSONL canônico + formatos por modelo.

Formato canônico (1 linha por clipe):
  {"audio": "clips/ses01/core_001.wav", "text": "...", "speaker": "pedro",
   "style": "animado", "intensity": "forte", "accent": "carioca-medio",
   "kind": "emocao", "dur_s": 4.2}

Conversores por modelo (--format):
  canonical  apenas o dataset-mestre (default)
  csm        conversation JSON p/ finetune CSM-1B (speaker turns)
  orpheus    text com tags de estilo inline p/ Orpheus-style ("<animado> texto")
  ljspeech   metadata.csv estilo LJSpeech (wav|text) p/ receitas clássicas

Uso:
  python tools/recording/export_dataset.py --sessions ses01 ses02 --sr 24000 --format canonical csm
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf

TRIM_DB = -42.0     # limiar de energia p/ trim
PAD_S = 0.25        # padding mantido em volta da fala


def trim_silence(audio: np.ndarray, sr: int) -> np.ndarray:
    win = max(1, int(0.02 * sr))
    n = (audio.size // win) * win
    if n == 0:
        return audio
    frames = audio[:n].reshape(-1, win)
    rms_db = 20 * np.log10(np.maximum(np.sqrt((frames ** 2).mean(axis=1)), 1e-9))
    voiced = np.where(rms_db > TRIM_DB)[0]
    if voiced.size == 0:
        return audio
    start = max(0, voiced[0] * win - int(PAD_S * sr))
    end = min(audio.size, (voiced[-1] + 1) * win + int(PAD_S * sr))
    return audio[start:end]


def resample(audio: np.ndarray, sr: int, target: int) -> np.ndarray:
    if sr == target:
        return audio
    try:
        import soxr
        return soxr.resample(audio, sr, target)
    except ImportError:
        # fallback linear (instale soxr para qualidade: pip install soxr)
        x_old = np.linspace(0, 1, audio.size)
        x_new = np.linspace(0, 1, int(audio.size * target / sr))
        return np.interp(x_new, x_old, audio).astype(np.float32)


def normalize_peak(audio: np.ndarray, peak_dbfs: float = -3.0) -> np.ndarray:
    peak = np.abs(audio).max()
    if peak < 1e-9:
        return audio
    return audio * (10 ** (peak_dbfs / 20) / peak)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", nargs="+", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out-root", default="data/dataset_v1")
    ap.add_argument("--sr", type=int, default=24000, help="sample rate alvo (Mimi/CSM=24k; 16k p/ alguns)")
    ap.add_argument("--val-frac", type=float, default=0.03)
    ap.add_argument("--peak-norm", type=float, default=-3.0, help="dBFS; use 0 p/ desligar")
    ap.add_argument("--format", nargs="+", default=["canonical"],
                    choices=["canonical", "csm", "orpheus", "ljspeech"])
    ap.add_argument("--exclude-kinds", nargs="*", default=[],
                    help="ex.: --exclude-kinds paralinguistico dialogo")
    args = ap.parse_args()

    out_root = Path(args.out_root)
    clips_dir = out_root / "clips"
    rows: list[dict] = []

    for ses in args.sessions:
        meta = Path(args.raw_root) / ses / "metadata.jsonl"
        if not meta.exists():
            raise SystemExit(f"metadata não encontrado: {meta}")
        # take mais recente por id
        best: dict[str, dict] = {}
        for line in meta.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                best[r["id"]] = r
        for r in best.values():
            if r.get("kind") in args.exclude_kinds:
                continue
            wav_in = Path(r["audio"])
            if not wav_in.exists():
                print(f"  ⚠️ pulando {r['id']}: wav ausente")
                continue
            audio, sr = sf.read(wav_in, dtype="float32", always_2d=False)
            if audio.ndim > 1:
                audio = audio[:, 0]
            audio = trim_silence(audio, sr)
            audio = resample(audio, sr, args.sr)
            if args.peak_norm < 0:
                audio = normalize_peak(audio, args.peak_norm)
            rel = Path("clips") / ses / f"{r['id']}.wav"
            (clips_dir / ses).mkdir(parents=True, exist_ok=True)
            sf.write(out_root / rel, audio, args.sr, subtype="PCM_16")
            rows.append({
                "audio": str(rel), "text": r["text"], "speaker": r.get("speaker", "pedro"),
                "style": r.get("style"), "intensity": r.get("intensity"),
                "accent": r.get("accent"), "kind": r.get("kind"),
                "dur_s": round(audio.size / args.sr, 2),
            })

    random.Random(42).shuffle(rows)
    n_val = max(1, int(len(rows) * args.val_frac))
    splits = {"val": rows[:n_val], "train": rows[n_val:]}

    total_min = sum(r["dur_s"] for r in rows) / 60
    print(f"📦 {len(rows)} clipes · {total_min:.1f} min · sr={args.sr}")

    for split, data in splits.items():
        if "canonical" in args.format:
            p = out_root / f"{split}.jsonl"
            with p.open("w", encoding="utf-8") as f:
                for r in data:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  canonical → {p} ({len(data)})")
        if "csm" in args.format:
            # CSM finetune: lista de conversas de 1 turno (context vem do sampler de treino)
            p = out_root / f"csm_{split}.json"
            conv = [{"speaker": 0, "text": _style_prefix(r) + r["text"], "audio": r["audio"]}
                    for r in data if r["kind"] not in ("paralinguistico",)]
            p.write_text(json.dumps(conv, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  csm → {p}")
        if "orpheus" in args.format:
            p = out_root / f"orpheus_{split}.jsonl"
            with p.open("w", encoding="utf-8") as f:
                for r in data:
                    f.write(json.dumps({"audio": r["audio"],
                                        "text": _style_prefix(r) + r["text"]},
                                       ensure_ascii=False) + "\n")
            print(f"  orpheus → {p}")
        if "ljspeech" in args.format:
            p = out_root / f"metadata_{split}.csv"
            with p.open("w", encoding="utf-8") as f:
                for r in data:
                    f.write(f"{Path(r['audio']).stem}|{r['text']}\n")
            print(f"  ljspeech → {p}")


def _style_prefix(r: dict) -> str:
    """Prefixo de controle no texto (formato tag) — ajuste fino pós-decisão de modelo."""
    parts = []
    if r.get("style") and r["style"] not in ("neutro", "conversa"):
        parts.append(r["style"])
    if r.get("accent") and r["accent"] != "carioca-medio":
        parts.append(r["accent"])
    return f"<{'|'.join(parts)}> " if parts else ""


if __name__ == "__main__":
    main()
