#!/usr/bin/env python3
"""Relatório de QC de uma sessão gravada (ou de todas).

Lê data/raw/<sessao>/metadata.jsonl + WAVs, recalcula métricas no arquivo final
(pico, clipping, SNR, duração; LUFS se pyloudnorm instalado) e imprime um
relatório markdown com totais por estilo/sotaque/kind e itens problemáticos.

Uso:
  python tools/recording/qc_report.py --session ses01
  python tools/recording/qc_report.py --all --out qc_report.md
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import pyloudnorm  # opcional
    _METER_CACHE: dict[int, "pyloudnorm.Meter"] = {}

    def lufs(audio: np.ndarray, sr: int) -> float | None:
        if sr not in _METER_CACHE:
            _METER_CACHE[sr] = pyloudnorm.Meter(sr)
        try:
            return round(float(_METER_CACHE[sr].integrated_loudness(audio)), 1)
        except Exception:
            return None
except ImportError:
    def lufs(audio, sr):  # type: ignore
        return None

from record import qc_take, SR  # reusa limites/funções


def analyze(meta_path: Path) -> list[dict]:
    rows = []
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        wav = Path(rec["audio"])
        if not wav.exists():
            rec["qc_final"] = {"error": "wav ausente"}
            rows.append(rec)
            continue
        audio, sr = sf.read(wav, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio[:, 0]
        qc = qc_take(audio if sr == SR else audio)  # SNR/pico independem de SR exato
        qc["lufs"] = lufs(audio, sr)
        qc["sr"] = sr
        rec["qc_final"] = qc
        rows.append(rec)
    return rows


def fmt_report(rows: list[dict], session: str) -> str:
    by_style: dict[str, float] = defaultdict(float)
    by_accent: dict[str, float] = defaultdict(float)
    by_kind: dict[str, float] = defaultdict(float)
    problems = []
    total_s = 0.0
    for r in rows:
        qc = r.get("qc_final", {})
        d = qc.get("dur_s", 0) or 0
        total_s += d
        by_style[r.get("style") or "-"] += d
        by_accent[r.get("accent") or "-"] += d
        by_kind[r.get("kind") or "-"] += d
        if qc.get("issues") or qc.get("error"):
            problems.append((r["id"], qc.get("error") or "; ".join(qc["issues"])))

    lines = [f"# QC — sessão {session}", "",
             f"- Takes aceitos: **{len(rows)}**",
             f"- Áudio total: **{total_s/60:.1f} min**",
             f"- Problemas: **{len(problems)}**", "",
             "## Minutos por estilo"]
    lines += [f"- {k}: {v/60:.1f} min" for k, v in sorted(by_style.items(), key=lambda x: -x[1])]
    lines += ["", "## Minutos por sotaque"]
    lines += [f"- {k}: {v/60:.1f} min" for k, v in sorted(by_accent.items(), key=lambda x: -x[1])]
    lines += ["", "## Minutos por tipo"]
    lines += [f"- {k}: {v/60:.1f} min" for k, v in sorted(by_kind.items(), key=lambda x: -x[1])]
    if problems:
        lines += ["", "## ⚠️ Itens para regravar/revisar"]
        lines += [f"- `{pid}` — {msg}" for pid, msg in problems]
    snrs = [r["qc_final"]["snr_db"] for r in rows if r.get("qc_final", {}).get("snr_db")]
    if snrs:
        lines += ["", f"SNR mediano: {np.median(snrs):.0f} dB · mín: {min(snrs):.0f} dB"]
    lufs_vals = [r["qc_final"]["lufs"] for r in rows if r.get("qc_final", {}).get("lufs") is not None]
    if lufs_vals:
        lines += [f"LUFS mediano: {np.median(lufs_vals):.1f} (alvo gravação crua: −23 a −18)"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out", default=None, help="salva o relatório em arquivo")
    args = ap.parse_args()

    root = Path(args.raw_root)
    sessions = ([p.name for p in root.iterdir() if (p / "metadata.jsonl").exists()]
                if args.all else [args.session])
    if not sessions or sessions == [None]:
        raise SystemExit("informe --session NOME ou --all")

    report = ""
    for s in sessions:
        rows = analyze(root / s / "metadata.jsonl")
        report += fmt_report(rows, s) + "\n"
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"→ {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
