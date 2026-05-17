"""
UTMOS naturalness proxy. Adapted from research/repos/F5-TTS/src/f5_tts/eval/
eval_utmos.py (proven). Automatic MOS gate per run; weak on *emotional* quality
(known limitation — pair with human CMOS for expressivity, see eval/README.md).

  python -m eval.utmos --audio-dir gen/ [--ext wav]
"""
import argparse, json
from pathlib import Path


def load_predictor(device):
    import torch
    p = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
    return p.to(device)


def score_dir(audio_dir: str, ext: str = "wav"):
    import torch, librosa
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    pred = load_predictor(dev)
    paths = sorted(Path(audio_dir).rglob(f"*.{ext}"))
    out = Path(audio_dir) / "_utmos_results.jsonl"
    tot = 0.0
    with open(out, "w", encoding="utf-8") as f:
        for ap_ in paths:
            wav, sr = librosa.load(ap_, sr=None, mono=True)
            t = torch.from_numpy(wav).to(dev).unsqueeze(0)
            s = pred(t, sr).item()
            tot += s
            f.write(json.dumps({"wav": ap_.stem, "utmos": s}) + "\n")
        avg = tot / len(paths) if paths else 0.0
        f.write(f"\nUTMOS: {avg:.4f}\n")
    return avg, len(paths), str(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--ext", default="wav")
    a = ap.parse_args()
    avg, n, out = score_dir(a.audio_dir, a.ext)
    print(f"UTMOS={avg:.4f} n={n} -> {out}")


if __name__ == "__main__":
    main()
