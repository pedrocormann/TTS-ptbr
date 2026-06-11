#!/usr/bin/env python3
"""Fábrica de dados do spine: reunião N-canal → pares estéreo formato Moshi.

Formato moshi-finetune: wav ESTÉREO, canal ESQUERDO = agente/modelo, DIREITO =
usuário. De uma reunião com N falantes geramos N arquivos de treino — cada
falante vira o "agente" uma vez (L = canal dele; R = MIX dos outros).
Os .json de transcrição vêm depois, do annotate.py oficial (--lang pt) no Colab
(notebook 5) — aqui só preparamos os wavs + manifest.

  python tools/recording/meeting_to_moshi.py --session reuniao_2026-06-11
  python tools/recording/meeting_to_moshi.py --all

Saída: data/moshi_pairs/<session>__<speaker>.wav (24kHz estéreo, formato Mimi)
       data/moshi_pairs/ds_meetings.jsonl        (egs p/ moshi-finetune)
Opções: --chunk-sec 300 corta reuniões longas em blocos (duration_sec do treino
é 100s; blocos de 5 min dão variedade de amostragem sem arquivos gigantes).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

TARGET_SR = 24_000  # Mimi


def resample(audio: np.ndarray, sr: int, target: int) -> np.ndarray:
    if sr == target:
        return audio
    try:
        import soxr
        return soxr.resample(audio, sr, target)
    except ImportError:
        x_old = np.linspace(0, 1, audio.size)
        x_new = np.linspace(0, 1, int(audio.size * target / sr))
        return np.interp(x_new, x_old, audio).astype(np.float32)


def load_channel(path: Path) -> tuple[np.ndarray, int]:
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio[:, 0]
    return audio, sr


def process_session(ses_dir: Path, out_dir: Path, chunk_sec: float) -> list[dict]:
    meta = json.loads((ses_dir / "meta.json").read_text(encoding="utf-8"))
    speakers = meta["speakers"]
    chans = {}
    n_min = None
    for s in speakers:
        a, sr = load_channel(ses_dir / f"{s}.wav")
        a = resample(a, sr, TARGET_SR)
        chans[s] = a
        n_min = len(a) if n_min is None else min(n_min, len(a))
    for s in chans:           # canais do mesmo clock: apara diferenças de borda
        chans[s] = chans[s][:n_min]

    rows = []
    chunk = int(chunk_sec * TARGET_SR) if chunk_sec else n_min
    for agent in speakers:
        others = [chans[s] for s in speakers if s != agent]
        right = np.sum(others, axis=0) / max(1, len(others))
        peak = np.abs(right).max()
        if peak > 0.99:       # evita clip no mix
            right = right * (0.99 / peak)
        left = chans[agent]
        for k in range(0, n_min, chunk):
            seg_l, seg_r = left[k:k + chunk], right[k:k + chunk]
            if seg_l.size < TARGET_SR * 20:        # blocos <20s não valem
                continue
            # pula blocos onde o "agente" quase não fala (RMS muito baixo)
            if np.sqrt((seg_l ** 2).mean()) < 1e-3:
                continue
            name = f"{meta['session']}__{agent}_b{k // chunk:03d}.wav"
            sf.write(out_dir / name, np.stack([seg_l, seg_r], axis=1),
                     TARGET_SR, subtype="PCM_16")
            rows.append({"path": str(out_dir / name),
                         "duration": round(seg_l.size / TARGET_SR, 3)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--meetings-root", default="data/meetings")
    ap.add_argument("--out-dir", default="data/moshi_pairs")
    ap.add_argument("--chunk-sec", type=float, default=300)
    args = ap.parse_args()

    root = Path(args.meetings_root)
    sessions = ([p for p in sorted(root.iterdir()) if (p / "meta.json").exists()]
                if args.all else [root / args.session])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    egs = out_dir / "ds_meetings.jsonl"
    seen = set()
    if egs.exists():
        seen = {json.loads(l)["path"] for l in egs.read_text(encoding="utf-8").splitlines() if l.strip()}
    n_new, total_s = 0, 0.0
    with egs.open("a", encoding="utf-8") as f:
        for ses in sessions:
            rows = process_session(ses, out_dir, args.chunk_sec)
            for r in rows:
                if r["path"] in seen:
                    continue
                f.write(json.dumps(r) + "\n")
                n_new += 1
                total_s += r["duration"]
    print(f"🧩 {n_new} pares estéreo novos (+{total_s/3600:.2f} h de treino) → {egs}\n"
          f"   transcrição: annotate.py --lang pt no Colab (notebook 5, célula 2)")


if __name__ == "__main__":
    main()
