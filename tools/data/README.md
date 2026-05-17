# tools/data/ — pt-BR → Moshi-format data pipeline

The Moshi bet's hardest input job: produce **stereo** (L=Moshi-role, R=user-role)
pt-BR conversational audio + timestamped transcripts, in the exact format
`moshi-finetune` expects. Verified against the cloned official code (dossier
10/50; sourcing = dossier 21).

## Pipeline
```
raw 2-party pt-BR (mono)
   └─ to_stereo.py        diarize (pyannote community-1) → L/R split  [pyannote = gated, PARKING-LOT]
        └─ make_jsonl.py  → ds.jsonl  {"path","duration"}             [sphn, runnable]
             └─ annotate_ptbr.sh  → sibling .json transcripts (--lang pt, whisper medium)
                  └─ moshi-finetune example/moshi_7B.yaml (data.train_data = ds.jsonl)
```

## Commercial-safe sources (dossier 21)
1. **Synthetic** (Kokoro Apache / Chatterbox MIT + LLM pt-BR scripts) — zero
   license risk, infinite, **the Phase-0 path this week**. NEVER XTTS/F5 (NC
   poisons output).
2. **Câmara dos Deputados** audio = **CC-BY-4.0** → diarize → split. Real-data
   workhorse (formal register). NOT Senado (proprietary/NC).
3. **Court/CNJ/STF** hearings = public-domain (Lei 9.610 Art. 8º) — LGPD-redact
   private parties.
4. In-house directed 2-party (Phase 2, the moat) + product flywheel (Phase B,
   consented SAC calls = ideal stereo).

J-Moshi ratio ≈ **602 h synth : 344 h real** (1.75:1) on top of mono-dialogue
continued-pretrain. Phase-0 proof needs only **~1–3 h** (synth fastest).

## Status
- `make_jsonl.py` — runnable (needs the moshi env's `sphn`).
- `annotate_ptbr.sh` — runnable wrapper (needs moshi-finetune cloned ✓ + whisper).
- `to_stereo.py` — logic complete; **blocked only on pyannote HF gate** (token +
  accept conditions — see ../../research/PARKING-LOT.md). Runs once the token exists.
