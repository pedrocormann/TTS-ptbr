"""
Mono 2-party pt-BR  ->  Moshi-format STEREO (L = Moshi-role, R = user-role).
This is the real data-engineering job for the Moshi bet (dossier 50 §7): Moshi
needs per-role channels; most pt-BR audio is mono. We diarize then split.

⚠️ SCAFFOLD: pyannote/speaker-diarization-3.1 is GATED (needs HF token + accept
conditions — see research/PARKING-LOT.md). Logic is written; the gated model
load is the only blocker. Runs as soon as the token exists.

  python tools/data/to_stereo.py --in conv.wav --out data_stereo/conv.wav \
      --moshi-speaker SPEAKER_00
(If you don't know which speaker is the "Moshi" role, run once, inspect, re-run
 with the right --moshi-speaker; or pass --auto to put the longer-talking one left.)
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="mono 2-party pt-BR wav")
    ap.add_argument("--out", required=True)
    ap.add_argument("--moshi-speaker", default=None,
                    help="diarization label to map to LEFT (Moshi role)")
    ap.add_argument("--auto", action="store_true",
                    help="map the longer-speaking speaker to LEFT/Moshi")
    ap.add_argument("--sr", type=int, default=24000)
    a = ap.parse_args()

    import torch, torchaudio
    try:
        from pyannote.audio import Pipeline
    except Exception as e:
        raise SystemExit(f"[FATAL] pyannote not installed: {e}\n"
                         ">> pip install pyannote.audio (and accept HF conditions for"
                         " pyannote/speaker-diarization-3.1 — PARKING-LOT.md)")

    import os
    tok = os.environ.get("HF_TOKEN")
    try:
        # community-1 (2025+) > 3.1: lower speaker-confusion, better 2-party
        # baseline (dossier 21 / arXiv 2509.26177). Fallback to 3.1 if unavailable.
        try:
            pipe = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1", use_auth_token=tok)
        except Exception:
            pipe = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", use_auth_token=tok)
    except Exception as e:
        raise SystemExit(f"[FATAL] gated model load failed: {e}\n"
                         ">> set HF_TOKEN and accept pyannote/speaker-diarization-3.1"
                         " conditions on HF. Parked auth — see PARKING-LOT.md.")

    wav, sr = torchaudio.load(a.inp)
    wav = wav.mean(0, keepdim=True)  # mono
    dia = pipe(a.inp)

    spk_time = {}
    for turn, _, spk in dia.itertracks(yield_label=True):
        spk_time[spk] = spk_time.get(spk, 0.0) + (turn.end - turn.start)
    if not spk_time:
        raise SystemExit("[FATAL] no speakers found by diarization")
    moshi_spk = (a.moshi_speaker or
                 (max(spk_time, key=spk_time.get) if a.auto else
                  sorted(spk_time)[0]))
    print(f"[diar] speakers={spk_time} -> LEFT/Moshi = {moshi_spk}")

    left = torch.zeros_like(wav)   # Moshi role
    right = torch.zeros_like(wav)  # user role
    for turn, _, spk in dia.itertracks(yield_label=True):
        s = int(turn.start * sr); e = int(turn.end * sr)
        (left if spk == moshi_spk else right)[:, s:e] = wav[:, s:e]

    stereo = torch.cat([left, right], dim=0)               # (2, T)
    stereo = torchaudio.functional.resample(stereo, sr, a.sr)
    import os as _os
    _os.makedirs(_os.path.dirname(a.out) or ".", exist_ok=True)
    torchaudio.save(a.out, stereo, a.sr)
    print(f"[ok] {a.out}  (L=Moshi {moshi_spk}, R=user). Next: make_jsonl.py + annotate_ptbr.sh")
    print("NOTE: diarized-split ≈ J-Moshi's approach; true per-mic stereo is cleaner"
          " when you record in-house (Phase 2).")


if __name__ == "__main__":
    main()
