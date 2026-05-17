"""
Prepare TTS-Portuguese-Corpus (Edresson, CC-BY-4.0, ~10h28m, 1 speaker, 48kHz)
into a manifest CSM/Mimi can consume: JSONL of {"audio": <24k mono wav>, "text": <str>}.

Source: https://huggingface.co/datasets/Edresson/TTS-Portuguese-Corpus/resolve/main/TTS-Portuguese-Corpus.zip

Usage:
  # download+extract yourself (≈large), then point --src at the extracted folder:
  python prep_ptbr_data.py --src /content/TTS-Portuguese-Corpus --out-dir data_ptbr
  # or let it fetch (Colab):
  python prep_ptbr_data.py --download --out-dir data_ptbr

Robust by design: the corpus zip layout isn't pinned here (verify on first run),
so we AUTO-DETECT the transcript file (csv/txt with "<id>==<text>" or "<id>|<text>")
and the wav directory, instead of hard-coding a path that might drift.
"""
import argparse, csv, glob, json, os, re, subprocess, sys, zipfile

ZIP_URL = "https://huggingface.co/datasets/Edresson/TTS-Portuguese-Corpus/resolve/main/TTS-Portuguese-Corpus.zip"


def _download(dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "TTS-Portuguese-Corpus.zip")
    if not os.path.exists(zip_path):
        print(f"[dl] {ZIP_URL}")
        subprocess.check_call(["wget", "-q", "-O", zip_path, ZIP_URL])
    print("[dl] extracting...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest_dir)
    return dest_dir


def _find_transcripts(root: str):
    """Return list of (wav_basename, text). Auto-detect the metadata file."""
    cands = []
    for ext in ("*.csv", "*.txt"):
        cands += glob.glob(os.path.join(root, "**", ext), recursive=True)
    for path in sorted(cands, key=lambda p: len(p)):
        rows = []
        with open(path, encoding="utf-8", errors="ignore") as f:
            sample = f.read(4000)
            f.seek(0)
            sep = "==" if "==" in sample else ("|" if "|" in sample else None)
            if sep is None:
                continue
            for line in f:
                line = line.strip()
                if not line or sep not in line:
                    continue
                wid, text = line.split(sep, 1)
                wid = os.path.splitext(os.path.basename(wid.strip()))[0]
                text = text.strip().strip('"')
                if wid and text:
                    rows.append((wid, text))
        if len(rows) > 50:  # looks like the real transcript file
            print(f"[meta] using {path} ({len(rows)} rows, sep={sep!r})")
            return rows
    sys.exit("[FATAL] could not auto-detect a transcript file under " + root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="extracted corpus dir")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--out-dir", default="data_ptbr")
    ap.add_argument("--target-sr", type=int, default=24000)  # Mimi/CSM rate
    args = ap.parse_args()

    src = args.src
    if args.download:
        src = _download(args.out_dir)
    if not src or not os.path.isdir(src):
        sys.exit("need --src <extracted dir> or --download")

    import torchaudio  # imported late so --help works without torch
    wav_out = os.path.join(args.out_dir, "wav24k")
    os.makedirs(wav_out, exist_ok=True)
    rows = _find_transcripts(src)
    wav_index = {os.path.splitext(os.path.basename(p))[0]: p
                 for p in glob.glob(os.path.join(src, "**", "*.wav"), recursive=True)}
    print(f"[wav] found {len(wav_index)} wavs")

    manifest = os.path.join(args.out_dir, "manifest.jsonl")
    n = 0
    with open(manifest, "w", encoding="utf-8") as mf:
        for wid, text in rows:
            src_wav = wav_index.get(wid)
            if not src_wav:
                continue
            wav, sr = torchaudio.load(src_wav)
            wav = wav.mean(0)  # mono
            if sr != args.target_sr:
                wav = torchaudio.functional.resample(wav, sr, args.target_sr)
            dst = os.path.join(wav_out, wid + ".wav")
            torchaudio.save(dst, wav.unsqueeze(0), args.target_sr)
            mf.write(json.dumps({"audio": dst, "text": text}, ensure_ascii=False) + "\n")
            n += 1
    print(f"[done] {n} pairs -> {manifest}  (24k mono). Feed this to qlora_finetune.py")


if __name__ == "__main__":
    main()
