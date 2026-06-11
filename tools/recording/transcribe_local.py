#!/usr/bin/env python3
"""Transcreve os segmentos de uma sessão LOCALMENTE (CPU, faster-whisper).

Mesmo papel da célula 1 do notebook 0, sem Colab — útil pra dataset pequeno
(~48min ≈ 20min de CPU no M2 com 'medium' int8).

  python tools/recording/transcribe_local.py --session elevenlabs2024 --model medium
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--model", default="medium")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    asr = WhisperModel(args.model, device="cpu", compute_type="int8")

    seg_meta = Path(args.raw_root) / args.session / "segments" / "to_transcribe.jsonl"
    rows = [json.loads(l) for l in seg_meta.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = seg_meta.with_name("transcribed.jsonl")
    done = set()
    if out.exists():  # retomável
        done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(todo)} segmentos a transcrever ({len(done)} já feitos)")

    with out.open("a", encoding="utf-8") as f:
        for k, r in enumerate(todo):
            segs, _ = asr.transcribe(r["audio"], language="pt", vad_filter=False)
            r["text"] = " ".join(s.text.strip() for s in segs).strip()
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if k % 20 == 0:
                print(f"  {k}/{len(todo)} · {r['id']}: {r['text'][:70]}")
    print(f"✅ → {out}")


if __name__ == "__main__":
    main()
