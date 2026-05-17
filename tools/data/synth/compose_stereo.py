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
    gap = np.zeros(int(a.gap * a.sr), dtype="float32")
    made = 0
    for did, d in man.items():
        L_parts, R_parts, aligns, cursor = [], [], [], 0.0
        for turn in d["turns"]:
            wav, sr = sf.read(os.path.join(a.turns_dir, turn["file"]),
                              dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(1)
            if sr != a.sr:  # guard; synth_tts writes at sr already
                import librosa
                wav = librosa.resample(wav, orig_sr=sr, target_sr=a.sr)
            sil = np.zeros(len(wav), dtype="float32")
            if turn["spk"] == "A":          # agent -> LEFT/Moshi
                L_parts += [wav, gap]
                R_parts += [sil, gap]
                role = "SPEAKER_MAIN"
            else:                            # human -> RIGHT/user
                L_parts += [sil, gap]
                R_parts += [wav, gap]
                role = "SPEAKER_OTHER"
            dur = len(wav) / a.sr
            aligns.append([turn["text"], [round(cursor, 3),
                           round(cursor + dur, 3)], role])
            cursor += dur + a.gap

        left = np.concatenate(L_parts) if L_parts else np.zeros(1, "float32")
        right = np.concatenate(R_parts) if R_parts else np.zeros(1, "float32")
        n = max(len(left), len(right))
        left = np.pad(left, (0, n - len(left)))
        right = np.pad(right, (0, n - len(right)))
        stereo = np.stack([left, right], axis=1)   # (T, 2)  L=Moshi R=user

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
