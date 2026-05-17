"""
Build the moshi-finetune dataset index. EXACT format from
research/repos/moshi-finetune/README.md (verified): one line per stereo wav,
{"path": "<rel>.wav", "duration": <sec>}. Uses sphn.durations (their snippet).

  python tools/data/make_jsonl.py --wav-dir data/data_stereo --out data/ds.jsonl
"""
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav-dir", required=True, help="dir of STEREO wavs (L=Moshi, R=user)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import sphn  # from the moshi env
    paths = [str(f) for f in Path(a.wav_dir).glob("*.wav")]
    durs = sphn.durations(paths)
    n = 0
    with open(a.out, "w") as f:
        for p, d in zip(paths, durs):
            if d is None:
                continue
            f.write(json.dumps({"path": p, "duration": d}) + "\n")
            n += 1
    print(f"{n} wavs -> {a.out}  (next: annotate_ptbr.sh to make the .json transcripts)")


if __name__ == "__main__":
    main()
