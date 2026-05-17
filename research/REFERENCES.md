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
| Llasa | Spike contender, pt via MLS, Llama-3.2 speech-LM. GitHub path 404'd on clone — study via HF model `HKUSTAudio/Llasa-1B-Multilingual`; training repo to confirm | verify ⚠️ |
| `SYSTRAN/faster-whisper` | ASR (locked) | MIT ✅ |
| `snakers4/silero-vad` | VAD / turn-taking (locked) | MIT ✅ |
| `unslothai/unsloth` | QLoRA/LoRA on Colab (the proof rig) | Apache ✅ |
| `Edresson/TTS-Portuguese-Corpus` | pt-BR seed corpus + author is a key person (below) | CC-BY ✅ |

**Cloned for STUDY (commercial-license gate deferred to launch — Pedro's call):**
`coqui-ai/TTS` (XTTS, CPML non-commercial), `SWivid/F5-TTS` (CC-BY-NC). Learn the
technique freely now; the license decision happens at productization, not before.
Do not ship their code into the product without resolving the license then.

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

## Spine candidates (post-RETHINK 2026-05-17 — audio is the spine, text parallel)

| Model | Role | Spine type | License | pt-BR |
|---|---|---|---|---|
| **Moshi** (kyutai) | ★bet | true full-duplex, text=parallel Inner Monologue (ablatable) | CC-BY-4.0 | needs LoRA (EN/FR base) |
| **Qwen3-Omni-30B-A3B** (Qwen) | co-bet | s2s Thinker-Talker, near-FD turn-taking | Apache-2.0 ✅ | native ✅ |
| **CSM-1B** (sesame) | voice component | single-utterance + in-context clone (NOT a spine) | Apache-2.0 | from scratch |
| Step-Audio 2 (StepFun) | emotion probe | end-to-end s2s, RL paralinguistics | unverified ⚠️ | unverified |
| Kyutai DSM / Unmute | cascade ref | STT→LLM→TTS modular | CC-BY-4.0 | — |

Watch additionally: `Qwen/Qwen3-Omni-*` (HF), arXiv 2509.17765; Step-Audio 2 arXiv
2507.16632; kyutai-labs/delayed-streams-modeling. Rationale: `phase0/RETHINK.md`.

## Similar work / prior art to keep mapped

- ElevenLabs (the incumbent / quality+price bar to beat in BR)
- GPT-4o Realtime, Gemini Live native audio (closed; architectural + latency reference)
- Open expressive TTS: StyleTTS2, Fish-Speech, Kokoro, Piper (fallback/technique refs)
