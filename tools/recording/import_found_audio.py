#!/usr/bin/env python3
"""Importa áudio "achado" (ex.: gravações do voice-clone da ElevenLabs) pro pipeline.

Faz: mp3/m4a/wav → wav mono PCM → QC (SNR/pico/duração) → segmentação por
energia em utterances de 1-20s → data/raw/<sessao>/segments/to_transcribe.jsonl
(exatamente o que o notebook 0 consome: transcreve no Colab → export → treino).

  python tools/recording/import_found_audio.py \
      --src "data/voice clone eleven labs" --session elevenlabs2024 \
      --speaker pedro --accent carioca-medio

Requer ffmpeg no PATH (conversão) e o venv do kit (numpy/soundfile).
Nota: fonte lossy (mp3) serve pra finetune v0/baselines; o dataset "ouro"
definitivo vem das gravações novas em WAV (REPLAN G0-G4).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from record import qc_take  # noqa: E402  (limiares compartilhados)
from segment_long import energy_segments  # noqa: E402

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac"}


def convert(src: Path, dst: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
                    "-ac", "1", "-c:a", "pcm_s24le", str(dst)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="pasta com os áudios originais")
    ap.add_argument("--session", required=True)
    ap.add_argument("--speaker", default="pedro")
    ap.add_argument("--accent", default="carioca-medio")
    ap.add_argument("--style", default="conversa",
                    help="rótulo default (ASR não sabe o estilo; revisar depois)")
    ap.add_argument("--raw-root", default="data/raw")
    args = ap.parse_args()

    src_dir = Path(args.src)
    files = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS)
    if not files:
        raise SystemExit(f"nenhum áudio em {src_dir}")

    ses_dir = Path(args.raw_root) / args.session
    seg_dir = ses_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    meta_path = ses_dir / "metadata.jsonl"
    out_meta = seg_dir / "to_transcribe.jsonl"

    total_s, n_segs, qc_rows = 0.0, 0, []
    with meta_path.open("w", encoding="utf-8") as fm, \
         out_meta.open("w", encoding="utf-8") as fo:
        for k, src in enumerate(files):
            pid = f"found_{k:02d}"
            wav_path = ses_dir / f"{pid}.wav"
            if not wav_path.exists():
                convert(src, wav_path)
            audio, sr = sf.read(wav_path, dtype="float32", always_2d=False)
            if audio.ndim > 1:
                audio = audio[:, 0]
            qc = qc_take(audio)            # SNR/pico (janelas independem do SR exato)
            qc["dur_s"] = round(audio.size / sr, 2)
            qc_rows.append((pid, qc))
            total_s += qc["dur_s"]
            fm.write(json.dumps({
                "id": pid, "audio": str(wav_path), "text": f"[IMPORTADO: {src.name}]",
                "kind": "found", "style": args.style, "intensity": "media",
                "accent": args.accent, "speaker": args.speaker,
                "session": args.session, "take": 1, "sr": sr,
                "qc": {x: qc[x] for x in ("peak_dbfs", "clip_ratio", "snr_db", "dur_s")},
                "source": str(src),
            }, ensure_ascii=False) + "\n")
            for j, (s, e) in enumerate(energy_segments(audio, sr)):
                seg_path = seg_dir / f"{pid}_seg{j:03d}.wav"
                sf.write(seg_path, audio[s:e], sr, subtype="PCM_24")
                fo.write(json.dumps({
                    "id": f"{pid}_seg{j:03d}", "audio": str(seg_path),
                    "source_id": pid, "kind": "found", "style": args.style,
                    "intensity": "media", "accent": args.accent,
                    "speaker": args.speaker, "session": args.session,
                    "dur_s": round((e - s) / sr, 2), "text": None,
                }, ensure_ascii=False) + "\n")
                n_segs += 1

    print(f"📦 {len(files)} arquivos · {total_s/60:.1f} min → {n_segs} segmentos em {seg_dir}")
    snrs = [q["snr_db"] for _, q in qc_rows if q["snr_db"]]
    if snrs:
        print(f"   SNR mediano {np.median(snrs):.0f} dB · mín {min(snrs):.0f} dB "
              f"(gate Hi-Fi TTS: ≥32)")
    bad = [(p, q["issues"]) for p, q in qc_rows if q["issues"]]
    for pid, issues in bad:
        print(f"   ⚠️ {pid}: {'; '.join(issues)}")
    print(f"   próximo: notebook 0 no Colab (transcreve segments) → export → notebook 2")


if __name__ == "__main__":
    main()
