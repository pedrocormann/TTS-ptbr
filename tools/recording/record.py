#!/usr/bin/env python3
"""Gravador guiado de sessão — apresenta cada item do plano, grava, faz QC na hora.

Fluxo por item:
  mostra texto + direção → ENTER inicia → fala → ENTER para →
  QC automático (clipping, SNR, duração) →
  [a]ceitar  [r]efazer  [p]ouvir  [s]pular  [q]sair

Saída:
  data/raw/<sessao>/<id>_t<take>.wav        (48 kHz, mono, 24-bit)
  data/raw/<sessao>/metadata.jsonl          (1 linha por take aceito)

Retomável: itens já aceitos são pulados ao reabrir.

Uso:
  python tools/recording/record.py --plan tools/recording/sessions/mix.jsonl --session ses01
  python tools/recording/record.py --list-devices
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("Instale as dependências:  pip install sounddevice soundfile numpy", file=sys.stderr)
    raise

SR = 48_000
CHANNELS = 1

# limites de QC
PEAK_CLIP = 0.985          # amostras acima disso contam como clipping
CLIP_RATIO_MAX = 1e-4      # fração de amostras clipadas tolerada
SNR_MIN_DB = 30.0          # abaixo disso, alerta
PEAK_LOW_DBFS = -24.0      # sinal fraco demais
PEAK_HIGH_DBFS = -3.0      # quente demais (sem headroom)


def db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-9))


def qc_take(audio: np.ndarray) -> dict:
    """QC rápido de um take: pico, clipping, SNR estimado, duração."""
    peak = float(np.abs(audio).max()) if audio.size else 0.0
    clip_ratio = float((np.abs(audio) >= PEAK_CLIP).mean()) if audio.size else 0.0

    # SNR: piso de ruído = percentil 5 do RMS por janela de 50ms; fala = percentil 90
    win = int(0.05 * SR)
    if audio.size >= win * 4:
        frames = audio[: (audio.size // win) * win].reshape(-1, win)
        rms = np.sqrt((frames ** 2).mean(axis=1))
        noise = float(np.percentile(rms, 5))
        speech = float(np.percentile(rms, 90))
        snr = db(speech) - db(noise)
    else:
        snr = 0.0

    issues = []
    if clip_ratio > CLIP_RATIO_MAX:
        issues.append(f"CLIPPING ({clip_ratio:.2%} das amostras) — abaixe o ganho")
    if db(peak) < PEAK_LOW_DBFS:
        issues.append(f"sinal fraco (pico {db(peak):.1f} dBFS) — aproxime do mic ou suba o ganho")
    if db(peak) > PEAK_HIGH_DBFS:
        issues.append(f"muito quente (pico {db(peak):.1f} dBFS) — deixe headroom de ~6 dB")
    if snr < SNR_MIN_DB and snr > 0:
        issues.append(f"SNR baixo ({snr:.0f} dB) — reduza ruído de fundo / AC / ventilador")
    if audio.size / SR < 0.6:
        issues.append("take muito curto (<0,6s)")

    return {"peak_dbfs": round(db(peak), 1), "clip_ratio": clip_ratio,
            "snr_db": round(snr, 1), "dur_s": round(audio.size / SR, 2),
            "issues": issues}


def record_until_enter(device: int | None) -> np.ndarray:
    """Grava até o usuário apertar ENTER."""
    chunks: list[np.ndarray] = []

    def cb(indata, frames, t, status):
        if status:
            print(f"  [áudio] {status}", file=sys.stderr)
        chunks.append(indata.copy())

    with sd.InputStream(samplerate=SR, channels=CHANNELS, dtype="float32",
                        device=device, callback=cb):
        input()  # bloqueia até ENTER; o callback acumula em paralelo
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks)[:, 0]


def load_done(meta_path: Path) -> set[str]:
    done = set()
    if meta_path.exists():
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", help="plano de sessão (.jsonl do build_session.py)")
    ap.add_argument("--session", default="ses01", help="nome da sessão (vira pasta)")
    ap.add_argument("--speaker", default="pedro")
    ap.add_argument("--out-root", default="data/raw")
    ap.add_argument("--device", type=int, default=None, help="índice do dispositivo de entrada")
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        return
    if not args.plan:
        ap.error("--plan é obrigatório (gere com build_session.py)")

    plan = [json.loads(l) for l in Path(args.plan).read_text(encoding="utf-8").splitlines() if l.strip()]
    out_dir = Path(args.out_root) / args.session
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "metadata.jsonl"
    done = load_done(meta_path)
    todo = [it for it in plan if it["id"] not in done]

    print(f"\n🎙️  Sessão {args.session} — {len(todo)} itens a gravar ({len(done)} já feitos)")
    print("    48 kHz · mono · 24-bit | alvo: pico entre −12 e −6 dBFS, sala silenciosa")
    print("    Dica: deixe ~0,5 s de silêncio antes e depois da fala em cada take.\n")

    for idx, item in enumerate(todo, 1):
        take = 1
        while True:
            print("─" * 72)
            print(f"[{idx}/{len(todo)}] {item['id']}  ·  {item['kind']}  ·  "
                  f"estilo={item.get('style','-')}/{item.get('intensity','-')}  ·  "
                  f"sotaque={item.get('accent','-')}")
            if item.get("direction"):
                print(f"  🎬 {item['direction']}")
            print(f"\n  📜 {item['text']}\n")
            cmd = input("  ENTER grava · s pula · q sai > ").strip().lower()
            if cmd == "q":
                print("Até a próxima. Sessão retomável.")
                return
            if cmd == "s":
                break

            print("  🔴 GRAVANDO… (ENTER para parar)")
            audio = record_until_enter(args.device)
            qc = qc_take(audio)
            flag = "⚠️ " if qc["issues"] else "✅"
            print(f"  {flag} {qc['dur_s']}s · pico {qc['peak_dbfs']} dBFS · SNR {qc['snr_db']} dB")
            for issue in qc["issues"]:
                print(f"     ⚠️  {issue}")

            while True:
                act = input("  [a]ceitar  [r]efazer  [p]ouvir  [s]pular > ").strip().lower()
                if act == "p":
                    sd.play(audio, SR); sd.wait(); continue
                break
            if act == "r":
                take += 1
                continue
            if act == "s":
                break
            # aceitar (default)
            wav_path = out_dir / f"{item['id']}_t{take}.wav"
            sf.write(wav_path, audio, SR, subtype="PCM_24")
            rec = {
                "id": item["id"], "audio": str(wav_path), "text": item["text"],
                "kind": item["kind"], "style": item.get("style"),
                "intensity": item.get("intensity"), "accent": item.get("accent"),
                "speaker": args.speaker, "session": args.session, "take": take,
                "sr": SR, "qc": {k: qc[k] for k in ("peak_dbfs", "clip_ratio", "snr_db", "dur_s")},
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            with meta_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            break

    print("\n🏁 Plano concluído. Rode o qc_report.py e depois export_dataset.py.")


if __name__ == "__main__":
    main()
