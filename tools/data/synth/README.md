# tools/data/synth/ — synthetic 2-party pt-BR (the no-license, this-week path)

Why: the Moshi bet's binding constraint is 2-party stereo pt-BR; all open
spontaneous/emotional pt-BR is NC-vetoed (dossier 20/21). Synthetic data has
**zero license risk**, infinite scale, and is exactly how J-Moshi got 602 h of
its 946 h fine-tune set (**~1.75 synth : 1 real**). This is the Phase-0 data path.

## Flow
```
seed_dialogues.jsonl   14 hand-authored pt-BR 2-party dialogues, emotion-tagged,
                        wedge domains (museu/SAC/vitrola/gov/maquininha/evento)
   └─ gen_dialogues.py  deterministic expansion (NO api/model) -> N variants    [TESTED ✓]
        └─ synth_tts.py  Kokoro(Apache, lang 'p'=pt-BR) | Chatterbox(MIT)        [needs GPU/audio]
             └─ compose_stereo.py  -> Moshi-format stereo (L=agent, R=user)
                                     + ground-truth .json transcript            [TESTED ✓]
                  └─ ../make_jsonl.py -> ds.jsonl -> moshi-finetune
```
A = agent → LEFT/Moshi channel. B = human → RIGHT/user channel. Synthetic data
ships a perfect `<id>.json` (known text + turn timing) so `annotate_ptbr.sh`
(whisper) is only needed for REAL audio.

## Tested (2026-05-17, CPU, no GPU here)
- `gen_dialogues.py`: 14 seeds × 3 → 42 dialogues, zero deps. ✓
- `compose_stereo.py`: emits valid **2-channel** 24 kHz stereo + moshi-finetune
  `{"alignments":[[word,[s,e],"SPEAKER_MAIN|OTHER"]]}` JSON. ✓
- `synth_tts.py`: written against Kokoro's real API (`KPipeline(lang_code='p')`);
  **NOT executed here** (needs the kokoro pkg + a GPU/audio box — Pedro runs it).
  ⚠️ Parked: verify Kokoro/Chatterbox pt-BR voice *quality/accent* before bulk.

## Scale guidance (dossier 21 / 60)
- Phase-0 proof: ~1–3 h synth (run gen with --variants ~30 → hundreds of dialogues
  → synth_tts → compose). No spend, this week.
- Toward usable: mix ~600 h synth + ~300 h real (Câmara CC-BY diarized + in-house).
- License: Kokoro Apache-2.0 / Chatterbox MIT only. NEVER XTTS/F5/Fish (NC poisons
  the trained weights).
