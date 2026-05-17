# TTS-ptbr — Mission

> **Status: DRAFT v0.1** — constitution in progress, deepening interview ongoing. `[TBD]` marks open items resolved in upcoming rounds. Despite the repo name, scope is a full-duplex conversational voice agent, not a classic TTS engine.

## Overview
A low-latency Brazilian Portuguese conversational voice system targeting the *perceived* quality of Sesame's "Maya" (naturalness, expressivity, sub-second turn latency). It will:
1. **Synthesize** expressive pt-BR speech with emotion control.
2. **Clone** a voice in-context from a short conversational sample (Sesame-style). MVP = 2 voices: male = Pedro / carioca accent; female = `[TBD speaker/accent]`.
3. **Converse** full-duplex (turn-taking, barge-in), end-to-end latency p50 < 800 ms.
4. **Stay controllable**: words come from a pluggable text LLM; prosody, emotion and voice route through audio context, not the text bottleneck (the Maya recipe).

Central idea: language is not only the written word. Phonemes, prosody, melody, regional traits and emotion are first-class features, enriched over time with language and verbal-communication specialists.

## Motivation
- No strong open expressive pt-BR conversational voice exists. Closed leaders (ElevenLabs, GPT-4o Realtime, Gemini Live) are proprietary; Maya is the best isolated experience tested (rated above ElevenLabs) but its voice/fine-tune is not open and is English-centric.
- The open base (Sesame CSM-1B, Apache-2.0) is a base model only; pt-BR is a from-scratch language adaptation.
- Unflat needs a controllable in-house pt-BR voice for its products (kiosk, AR Mirror, PalmPay assistant) without per-token lock-in to an external player.

## Target audience (phased)
- **Phase A — internal Unflat capability**: voice for Unflat products; Unflat controls quality and consent.
- **Phase B — partial open-source**: open code/pipeline/recipe; **closed weights and proprietary dataset** (the "gold"); NDA and Brazilian academic partnerships.
- **Phase C — B2B API + D2C products**.

## Scope
### MVP delivers
- In-context cloning of 2 voices / 2 genders / 2 accents (M = Pedro/carioca, F = `[TBD]`).
- Emotion control (set `[TBD]`; at least neutral/happy/sad).
- Low-latency streaming, end-to-end p50 < 800 ms.
- Full-duplex conversation (turn-taking, barge-in) as the target experience.
- Architecture chosen by data via Phase 0 (bet = path B / CSM-style hybrid).
### Deferred (mapped, out of MVP)
- **5 regional accents** — start with 2 (carioca + `[TBD]`); each accent needs ~10-30 h recorded.
- **Production API / scale** (multi-tenant, SLA) — validate viability first.
- **Formal language-specialist enrichment program** — starts informally, formalizes later.
- **Manual pt-BR audio labeling tool as a product** — built internally first as dev support.

## Success metrics (gating)
| What we measure | Target | How |
|---|---|---|
| End-to-end latency p50 | < 800 ms (turn-end → speech start) | instrumented harness across VAD+ASR+LLM+TTS |
| Naturalness/expressivity MOS | `[TBD threshold, e.g. ≥ 4.0]` blind vs baseline | human listening panel |
| pt-BR intelligibility | WER round-trip ≤ `[TBD]%` | ASR on generated audio vs source text |
| Voice-clone similarity | `[TBD]` (tracked, not gating in MVP) | speaker-verification cosine, sample ≤ 30 s |

Beyond automatic metrics: a qualitative "linguistic richness" track (phonemes, prosody, melody, regional traits) assessed with language/verbal-communication specialists. `[TBD: rubric + who]`.

## Constraints & assumptions
- License hygiene: only Apache-2.0 / CC-BY / CC0 inputs. Veto CPML (XTTS), CC-BY-NC (F5-TTS, TEDx-pt).
- Mimi codec is CC-BY-4.0 → attribution required in product.
- Sesame CSM acceptable-use clauses → mirror in product T&Cs; consent-gate any voice clone.
- Compute budget: Colab ≤ R$500/mo (spikes/QLoRA) → SDumont GH200 (full, pending authorization) → NVIDIA Inception overflow.
- No external deadline.

## Open questions
1. Female voice: which speaker, which accent? Hire vs. team member?
2. Emotion set and labeling scheme (categorical vs. dimensional valence/arousal)?
3. MOS protocol and thresholds; who runs the listening panel?
4. Phase C business model (B2B pricing? D2C product shape?) — candidate for `/office-hours`.
5. How is "closed weights" enforced technically in an otherwise open repo?
6. LGPD posture for voice cloning and stored voice data; consent artifacts.
7. Which Unflat products consume v1 first, and their concrete latency/voice requirements?
8. Language-specialist program: scope, partners, when it starts.

## Inspiration / prior art
Sesame Maya/CSM (the recipe and the bar), Kyutai Moshi (full-duplex speech-native ceiling), ElevenLabs (market quality bar to beat in pt-BR). This project does not clone Maya; it builds a pt-BR voice of our own at Maya-class quality.
