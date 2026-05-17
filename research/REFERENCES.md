# TTS-ptbr — Research Map (vigil source of truth)

Curated. Keep tight, high-signal. Weekly vigil scans the "Watch" section and logs
to `VIGIL-LOG.md`. `research/repos/` is gitignored (we don't vendor others' code).

## Repos — clone for study (`./clone.sh`)

| Repo | Why | Product-use license |
|---|---|---|
| `SesameAILabs/csm` | The bet (B). CSM-1B speech model | Apache-2.0 ✅ |
| `kyutai-labs/moshi` | Full-duplex speech-native + **Mimi codec** (Spike C, ceiling) | code MIT/Apache ✅ / weights CC-BY |
| `kyutai-labs/moshi-finetune` | Official finetune recipe (no equivalent for CSM) | Apache ✅ |
| `canopyai/Orpheus-TTS` | Spike A/Orpheus. Emotion tags, ~100-200ms published | Apache-2.0 ✅ |
| `HKUSTAudio/Llasa` | Spike contender, pt via MLS, Llama-3.2 speech-LM | verify ⚠️ |
| `SYSTRAN/faster-whisper` | ASR (locked) | MIT ✅ |
| `snakers4/silero-vad` | VAD / turn-taking (locked) | MIT ✅ |
| `unslothai/unsloth` | QLoRA/LoRA on Colab (the proof rig) | Apache ✅ |
| `Edresson/TTS-Portuguese-Corpus` | pt-BR seed corpus + author is a key person (below) | CC-BY ✅ |

**Reference-only (read, do NOT vendor/use in product — license vetoed):**
`coqui-ai/TTS` (XTTS, CPML non-commercial), `SWivid/F5-TTS` (CC-BY-NC). Study the
technique, never ship it.

## Watch — orgs & people (weekly: new repos / papers / releases)

- **Sesame AI Labs** — github.com/orgs/SesameAILabs/repositories (the bet's origin; repo is stale ~12mo, watch for any revival)
- **Kyutai** — github.com/kyutai-labs · kyutai.org (Moshi/Mimi; most active in full-duplex). People: Neil Zeghidour, Alexandre Défossez (also EnCodec/AudioCraft)
- **Canopy Labs** — github.com/canopyai (Orpheus; active)
- **Edresson Casanova** — github.com/Edresson · the pt-BR TTS authority (TTS-Portuguese Corpus, CML-TTS, YourTTS, XTTS co-author). **Highest-priority person to follow for pt-BR.**
- **HKUST Audio** — Llasa / speech-LM recipe family
- **Hugging Face audio** — hf.co/models?pipeline_tag=text-to-speech&language=pt ; "reach-vb" (Vaibhav Srivastav) for ecosystem signal
- **Coqui alumni / community forks** — XTTS lineage (technique reference, not product)

## Papers — core reading (cutting edge)

- Sesame — "Crossing the uncanny valley of conversational voice" (research post; the recipe + the bar)
- Moshi — arXiv 2410.00037 (full-duplex speech-text, Inner Monologue, Mimi)
- Mimi / EnCodec lineage — neural audio codecs (RVQ, streaming)
- CML-TTS — arXiv 2306.10097 (the pt-BR multilingual TTS corpus; Edresson et al.)
- YourTTS / XTTS — zero-shot multilingual voice cloning (technique; license-vetoed for product)
- Llasa — Llama-based speech-LM, multilingual incl. pt
- Emotional/expressive TTS surveys — track 1-2 recent MDPI/arXiv surveys for the linguistic-richness track

## Standing scan sources (weekly)

- arXiv: `eess.AS`, `cs.SD`, `cs.CL` (filter: TTS / speech LM / voice clone / full-duplex / pt-BR)
- Hugging Face: Papers daily (audio), trending TTS models, pt models
- GitHub: releases/activity of the Watch repos above
- HF + GitHub: search "portuguese" / "brazilian" TTS monthly for new pt-BR work

## Similar work / prior art to keep mapped

- ElevenLabs (the incumbent / quality+price bar to beat in BR)
- GPT-4o Realtime, Gemini Live native audio (closed; architectural + latency reference)
- Open expressive TTS: StyleTTS2, Fish-Speech, Kokoro, Piper (fallback/technique refs)
