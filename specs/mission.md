# TTS-ptbr — Mission

> **Status: DRAFT v0.2** — constitution from a deep Spec-Driven interview (28 Q). Architecture is bet-not-locked (Phase 0 decides with data). `[TBD]` = still open. Despite the repo name, scope is a full-duplex conversational voice platform, not a classic TTS engine.

## Overview
A low-latency Brazilian Portuguese conversational voice system targeting the *perceived* quality of Sesame's "Maya" (naturalness, expressivity, sub-second turn latency). It will:
1. **Synthesize** expressive pt-BR speech with emotion control (categorical + intensity, tuned for service/warmth).
2. **Clone** a voice in-context from a short conversational sample (Sesame-style). MVP = 2 voices: male = Pedro / carioca; female = hired professional / accent decided with her.
3. **Converse** full-duplex (turn-taking, barge-in), end-to-end latency p50 < 800 ms.
4. **Stay controllable**: words come from a pluggable text LLM; prosody, emotion and voice route through audio context, not the text bottleneck (the Maya recipe).

Central idea: language is not only the written word. Phonemes, prosody, melody, regional traits and emotion are first-class features, enriched over time with language and verbal-communication specialists.

## Motivation
- No strong open expressive pt-BR conversational voice exists. Closed leaders (ElevenLabs, GPT-4o Realtime, Gemini Live) are proprietary; Maya is the best isolated experience tested (rated above ElevenLabs) but its voice/fine-tune is not open and is English-centric.
- The open base (Sesame CSM-1B, Apache-2.0) is a base model only; pt-BR is a from-scratch language adaptation.
- Unflat already pays for ElevenLabs in real work (e.g. the "Arquitetos do Samba" AI vitrola at the SambaCore expo). A controllable in-house pt-BR voice removes per-token lock-in and becomes a product line.

## Target audience (phased)
- **Phase A — internal Unflat capability**: voice for Unflat products; Unflat controls quality and consent.
- **Phase B — partial open-source**: open code/pipeline/recipe; **closed weights and proprietary dataset** (the "gold"); NDA and Brazilian academic partnerships.
- **Phase C — B2B API + D2C products**.

## Product vision (where the voice is consumed)
First consumer = **demo on the Unflat website**: low-latency pt-BR conversation, 2 min without signup / 10 min with signup, used as marketing and to land first sales. Then a portfolio:
- Smart-glasses experiences (the Museum Lens in development).
- "Fala Cidadão": a government attendance booth, public-sector SAC and access facilitator to services/info.
- Agentic AI SAC for companies (the ElevenLabs-style use case).
- Live-marketing activations and artistic installations (replacing ElevenLabs, e.g. the samba vitrola).
- B2B API, and a packaged physical device ("maquininha") for retail, self-service and events.

## Scope
### MVP delivers
- In-context cloning of 2 voices / 2 genders / 2 accents (M = Pedro/carioca; F = hired pro).
- Emotion control: categorical + intensity (neutral, warm/welcoming, enthusiastic, empathetic, sad, surprise; intensity 0..1), expandable.
- Low-latency streaming, end-to-end p50 < 800 ms, full-duplex (turn-taking, barge-in).
- Architecture chosen by data via Phase 0 (bet = path B / CSM-style hybrid).
- Unflat-website demo with freemium gating (2 min anon / 10 min signed).
### Deferred (mapped, out of MVP)
- **5 regional accents** — start with 2; each accent ~10-30 h recorded.
- **Production API / scale** (multi-tenant, SLA).
- **Formal language-specialist enrichment program** — starts as a contact in Phase 3.
- **Manual pt-BR audio labeling tool as a standalone product** — built internally first (lightweight track from Phase 1).

## Success metrics (gating)
| What we measure | Target | How |
|---|---|---|
| End-to-end latency p50 | < 800 ms (turn-end → speech start) | instrumented harness across VAD+ASR+LLM+TTS |
| Naturalness/expressivity MOS | ≥ 4.0 (adjustable), blind | internal blind 1-5 panel vs baseline + ElevenLabs + Maya |
| pt-BR intelligibility | WER round-trip ≤ `[TBD]%` | ASR (faster-whisper) on generated audio vs source text |
| Voice-clone similarity | tracked, not gating in MVP | speaker-verification cosine, sample ≤ 30 s |

Beyond automatic metrics: a "linguistic richness" track (phonemes, prosody, melody, regional traits) with language/verbal-communication specialists (first contact Phase 3; rubric `[TBD]`).

## Team & owners
- **Pedro** — solo on core ML / architecture / pipeline / the demo.
- **João** — joins only in the data phase (corpus curation/QA, labeling tool usage).
- **David** — not involved in this project.
- **Hired** — professional female voice talent (Phase 2); language specialists later.

## Risk register
1. **CSM has no published latency** — may miss < 800 ms. Mitigation: Spike C (Moshi ceiling) + measure in Phase 0.
2. **pt-BR from scratch** — CSM "won't do well", phonetics may break. Mitigation: Spike B measures this early.
3. **Expressive labeled pt-BR data barely exists openly** — the real bottleneck. Mitigation: in-house directed recording + labeling tool from Phase 1.
4. **CSM repo stale ~12 mo, no official fine-tune tooling; SDumont auth may slip** — compute + community-recipe dependency. Mitigation: staged compute, community recipes, Inception overflow.

## Constraints & assumptions
- License hygiene: only Apache-2.0 / CC-BY / CC0 inputs. Veto CPML (XTTS), CC-BY-NC (F5-TTS, TEDx-pt).
- Mimi codec is CC-BY-4.0 → attribution required in product.
- Sesame CSM acceptable-use clauses → mirror in product T&Cs; consent-gate any voice clone.
- LGPD: consent forms for recorded voices + LGPD doc from MVP; weights kept in a private registry separate from the public code.
- Compute: Colab ≤ R$500/mo (spikes/QLoRA) → SDumont GH200 (full, pending authorization) → NVIDIA Inception overflow.
- No external deadline.

## Open questions
1. F voice accent (decided with the hired talent; complementary to carioca).
2. WER round-trip threshold (set after Phase-0 baseline).
3. Language-specialist rubric + partners.
4. Phase C business model (B2B pricing, D2C product shape, the physical device) — routed to `/office-hours`.
5. Which portfolio product (beyond the website demo) is productized first after MVP.

## Inspiration / prior art
Sesame Maya/CSM (the recipe and the bar), Kyutai Moshi (full-duplex speech-native ceiling), ElevenLabs (market quality bar to beat, and the incumbent in Unflat's own installations). This project does not clone Maya; it builds a pt-BR voice of our own at Maya-class quality.
