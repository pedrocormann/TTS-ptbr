"""
Per-turn wavs (synth_tts.py) -> ONE Moshi-format STEREO wav per dialogue:
  LEFT  channel = agent A  (Moshi role)
  RIGHT channel = human B  (user role)
Turns are laid sequentially with a small inter-turn gap; the non-speaking
channel is silent during a turn (exactly Moshi's 2-stream training format).
Also emits a ground-truth `<id>.json` transcript in moshi-finetune's schema
(synthetic data has perfect text + known turn timing -> we can skip the
whisper annotate step for synth; real data still uses annotate_ptbr.sh).

MODEL-FREE — pure numpy/soundfile. CPU. This is the half that is unit-testable
without any GPU/TTS, and it is tested (see research/VIGIL-LOG.md).

  python tools/data/synth/compose_stereo.py --turns-dir synth_turns \
      --out-dir data/data_stereo --gap 0.4
"""
import argparse, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns-dir", required=True, help="from synth_tts.py (has _turns_manifest.json)")
    ap.add_argument("--out-dir", default="data/data_stereo")
    ap.add_argument("--gap", type=float, default=0.4, help="seconds of silence between turns")
    ap.add_argument("--sr", type=int, default=24000)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    import numpy as np
    import soundfile as sf

    man = json.load(open(os.path.join(a.turns_dir, "_turns_manifest.json"),
                         encoding="utf-8"))
    made = 0
    for did, d in man.items():
        # Build on two continuous timelines (samples), not concatenation, so a
        # backchannel ("bc": true) can OVERLAP the previous turn — real
        # full-duplex behaviour (dossier 30: backchannels/overlap matter; pure
        # sequential data underfits it).
        turns = []
        for turn in d["turns"]:
            wav, sr = sf.read(os.path.join(a.turns_dir, turn["file"]),
                              dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(1)
            if sr != a.sr:
                import librosa
                wav = librosa.resample(wav, orig_sr=sr, target_sr=a.sr)
            turns.append((turn, wav))

        total = sum(len(w) for _, w in turns) + int(a.gap * a.sr) * len(turns)
        left = np.zeros(total, "float32")
        right = np.zeros(total, "float32")
        aligns = []
        cursor = 0           # samples; next sequential turn starts here
        prev_start = prev_dur = 0
        end_used = 0
        for i, (turn, wav) in enumerate(turns):
            ch = left if turn["spk"] == "A" else right
            role = "SPEAKER_MAIN" if turn["spk"] == "A" else "SPEAKER_OTHER"
            is_bc = bool(turn.get("bc")) and i > 0  # 1st turn can't backchannel
            if is_bc:
                # start ~60% into the previous (opposite-speaker) turn; do NOT
                # advance the sequential cursor past the previous turn's end.
                start = prev_start + int(0.6 * prev_dur)
            else:
                start = cursor
            start = min(start, total - len(wav)) if len(wav) <= total else 0
            ch[start:start + len(wav)] += wav[:max(0, total - start)]
            dur = len(wav)
            aligns.append([turn["text"],
                           [round(start / a.sr, 3),
                            round((start + dur) / a.sr, 3)], role])
            end_used = max(end_used, start + dur)
            if not is_bc:
                prev_start, prev_dur = start, dur
                cursor = start + dur + int(a.gap * a.sr)
        n = max(end_used, 1)
        stereo = np.stack([left[:n], right[:n]], axis=1)  # (T,2) L=Moshi R=user

        wav_path = os.path.join(a.out_dir, f"{did}.wav")
        sf.write(wav_path, stereo, a.sr)
        # ground-truth transcript (moshi-finetune annotate.py schema)
        json.dump({"alignments": aligns},
                  open(os.path.join(a.out_dir, f"{did}.json"), "w",
                       encoding="utf-8"), ensure_ascii=False)
        made += 1

    print(f"{made} Moshi-format stereo dialogues -> {a.out_dir}")
    print("next: tools/data/make_jsonl.py --wav-dir %s --out data/ds.jsonl" % a.out_dir)
    print("(synth has ground-truth .json already; annotate_ptbr.sh only needed for REAL audio)")


if __name__ == "__main__":
    main()
