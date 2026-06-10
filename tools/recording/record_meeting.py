#!/usr/bin/env python3
"""Gravador de reunião multi-canal — 1 mic por pessoa, 1 wav por canal.

O flywheel UNFLAT (REPLAN §3): reuniões diárias com N canais sincronizados
(UMA interface multi-entrada = um clock; nunca 3 mics USB separados).
Escreve em chunks (flush a cada ~10s) — queda de energia perde no máx. 10s.

  python tools/recording/record_meeting.py --device 2 --channels 3 \
      --speakers pedro joao guilherme --session reuniao_2026-06-11

Saída:
  data/meetings/<session>/<speaker>.wav      (48kHz/24-bit, mono por canal)
  data/meetings/<session>/meta.json          (falantes, início, duração, níveis)

Pós-processamento: meeting_to_moshi.py (pares estéreo p/ o spine) e
segment_long.py por canal (utterances p/ TTS/voz).
Pare com Ctrl-C ou ENTER. Consentimento de TODOS antes (docs/consentimento-voz.md).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("pip install sounddevice soundfile numpy", file=sys.stderr)
    raise

SR = 48_000
FLUSH_S = 10


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", type=int, default=None,
                    help="índice da interface (veja --list-devices)")
    ap.add_argument("--channels", type=int, default=3)
    ap.add_argument("--speakers", nargs="+", required=False,
                    help="nomes na ordem dos canais da interface (ex.: pedro joao guilherme)")
    ap.add_argument("--session", default=time.strftime("reuniao_%Y-%m-%d_%H%M"))
    ap.add_argument("--out-root", default="data/meetings")
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        return
    speakers = args.speakers or [f"ch{i}" for i in range(args.channels)]
    if len(speakers) != args.channels:
        raise SystemExit("--speakers deve ter 1 nome por canal")

    out_dir = Path(args.out_root) / args.session
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [sf.SoundFile(out_dir / f"{s}.wav", mode="w", samplerate=SR,
                          channels=1, subtype="PCM_24") for s in speakers]

    peaks = np.zeros(args.channels)
    written = [0]
    lock = threading.Lock()

    def cb(indata, frames, t, status):
        if status:
            print(f"[áudio] {status}", file=sys.stderr)
        with lock:
            for c in range(args.channels):
                files[c].write(indata[:, c])
            written[0] += frames
            np.maximum(peaks, np.abs(indata[:, :args.channels]).max(axis=0), out=peaks)

    print(f"🎙️  Reunião '{args.session}' — {args.channels} canais "
          f"({', '.join(speakers)}) · 48kHz/24-bit\n"
          f"    ENTER ou Ctrl-C para encerrar. Flush a cada {FLUSH_S}s.\n")
    t0 = time.time()
    stop = threading.Event()

    def monitor():
        while not stop.is_set():
            time.sleep(FLUSH_S)
            with lock:
                for f in files:
                    f.flush()
                dur = written[0] / SR
                lv = " ".join(f"{s}:{20*np.log10(max(p,1e-9)):.0f}dB"
                              for s, p in zip(speakers, peaks))
                peaks[:] = 0
            print(f"  ⏺ {dur/60:5.1f} min · picos último bloco: {lv}")

    th = threading.Thread(target=monitor, daemon=True)
    try:
        with sd.InputStream(samplerate=SR, channels=args.channels, dtype="float32",
                            device=args.device, callback=cb):
            th.start()
            input()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        with lock:
            for f in files:
                f.close()
        dur = written[0] / SR
        meta = {"session": args.session, "speakers": speakers, "sr": SR,
                "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0)),
                "dur_s": round(dur, 1),
                "files": [str(out_dir / f"{s}.wav") for s in speakers]}
        (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
        print(f"\n🏁 {dur/60:.1f} min gravados → {out_dir}\n"
              f"   próximo: python tools/recording/meeting_to_moshi.py --session {args.session}")


if __name__ == "__main__":
    main()
