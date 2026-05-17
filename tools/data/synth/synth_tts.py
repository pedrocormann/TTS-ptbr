"""
Dialogues jsonl -> per-turn wavs, using a COMMERCIAL-SAFE TTS only.
Primary: Kokoro (Apache-2.0) — has lang_code 'p' = Brazilian Portuguese, voices
  pf_* (female) / pm_* (male), 24 kHz. Alt: Chatterbox (MIT, multilingual).
NEVER XTTS/F5/Fish here — they are CC-BY-NC/CPML and poison commercial output
(dossier 21). Agent A = LEFT/Moshi voice, Agent B = RIGHT/user voice.

  pip install kokoro soundfile        # (Pedro, on a box with audio)
  python tools/data/synth/synth_tts.py --dialogues synth_dialogues.jsonl \
      --out-dir synth_turns --engine kokoro --voice-a pm_alex --voice-b pf_dora

⚠️ Parked verify (PARKING-LOT): confirm Kokoro/Chatterbox pt-BR voice QUALITY
before bulk runs — accent may be generic; this pipeline is correct, the voice
quality is the open check.
"""
import argparse, json, os


def synth_kokoro(turns, out_dir, did, voice_a, voice_b, sr=24000):
    from kokoro import KPipeline  # lang 'p' = Brazilian Portuguese
    import soundfile as sf
    import numpy as np
    pipe = KPipeline(lang_code="p")
    man = []
    for i, t in enumerate(turns):
        voice = voice_a if t["spk"] == "A" else voice_b
        # Kokoro yields (graphemes, phonemes, audio) chunks; concat them.
        chunks = [a for _, _, a in pipe(t["text"], voice=voice)]
        audio = np.concatenate(chunks) if chunks else np.zeros(1, "float32")
        fn = f"{did}_t{i:02d}_{t['spk']}.wav"
        sf.write(os.path.join(out_dir, fn), audio, sr)
        man.append({"file": fn, "spk": t["spk"], "text": t["text"],
                    "emotion": t["emotion"], "intensity": t["intensity"]})
    return man


def synth_chatterbox(turns, out_dir, did, voice_a, voice_b, sr=24000):
    # MIT. Multilingual Chatterbox; voice_a/voice_b = reference wav paths here.
    from chatterbox.tts import ChatterboxTTS  # API per the MIT repo
    import soundfile as sf
    model = ChatterboxTTS.from_pretrained(device="cuda")
    man = []
    for i, t in enumerate(turns):
        ref = voice_a if t["spk"] == "A" else voice_b
        wav = model.generate(t["text"], audio_prompt_path=ref, language_id="pt")
        fn = f"{did}_t{i:02d}_{t['spk']}.wav"
        sf.write(os.path.join(out_dir, fn),
                 wav.squeeze(0).cpu().numpy(), model.sr)
        man.append({"file": fn, "spk": t["spk"], "text": t["text"],
                    "emotion": t["emotion"], "intensity": t["intensity"]})
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dialogues", required=True)
    ap.add_argument("--out-dir", default="synth_turns")
    ap.add_argument("--engine", choices=["kokoro", "chatterbox"], default="kokoro")
    ap.add_argument("--voice-a", default="pm_alex",
                    help="kokoro: pm_* voice id | chatterbox: ref wav path")
    ap.add_argument("--voice-b", default="pf_dora",
                    help="kokoro: pf_* voice id | chatterbox: ref wav path")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    fn = synth_kokoro if a.engine == "kokoro" else synth_chatterbox
    rows = [json.loads(l) for l in open(a.dialogues, encoding="utf-8") if l.strip()]
    idx = {}
    for d in rows:
        man = fn(d["turns"], a.out_dir, d["id"], a.voice_a, a.voice_b)
        idx[d["id"]] = {"scenario": d["scenario"], "accent": d["accent"],
                        "turns": man}
    with open(os.path.join(a.out_dir, "_turns_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print(f"{len(rows)} dialogues -> per-turn wavs in {a.out_dir} "
          f"(engine={a.engine}). next: compose_stereo.py")


if __name__ == "__main__":
    main()
