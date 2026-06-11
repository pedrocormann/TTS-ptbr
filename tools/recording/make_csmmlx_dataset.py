#!/usr/bin/env python3
"""transcribed.jsonl → dataset JSON do csm-mlx (list[list[Segment]]).

  python tools/recording/make_csmmlx_dataset.py --session elevenlabs2024 \
      --out data/csmmlx_ds
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out", default="data/csmmlx_ds")
    ap.add_argument("--val-frac", type=float, default=0.03)
    ap.add_argument("--min-words", type=int, default=3)
    args = ap.parse_args()

    src = Path(args.raw_root) / args.session / "segments" / "transcribed.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    keep, skipped = [], 0
    for r in rows:
        text = (r.get("text") or "").strip()
        if len(text.split()) < args.min_words or r.get("dur_s", 0) < 1.5:
            skipped += 1
            continue
        keep.append([{"text": text, "audio_path": str(Path(r["audio"]).resolve()),
                      "speaker": 0}])

    random.Random(42).shuffle(keep)
    n_val = max(1, int(len(keep) * args.val_frac))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "train.json").write_text(json.dumps(keep[n_val:], ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    (out / "val.json").write_text(json.dumps(keep[:n_val], ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    total_s = sum(r.get("dur_s", 0) for r in rows)
    print(f"✅ {len(keep) - n_val} train / {n_val} val ({skipped} descartados) · "
          f"~{total_s/60:.0f} min → {out}")


if __name__ == "__main__":
    main()
