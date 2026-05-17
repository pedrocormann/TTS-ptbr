# TTS-ptbr — Mission

> **Status: DRAFT v0.2** — constitution from a deep Spec-Driven interview (28 Q). Architecture is bet-not-locked (Phase 0 decides with data). `[TBD]` = still open. Despite the repo name, scope is a full-duplex conversational voice platform, not a classic TTS engine.

## Overview
A low-latency Brazilian Portuguese conversational voice system targeting the *perceived* quality of Sesame's "Maya" (naturalness, expressivity, sub-second turn latency). It will:
1. **Synthesize** expressive pt-BR speech with emotion control (categorical + intensity, tuned for service/warmth).
2. **Clone** a voice in-context from a short conversational sample (Sesame-style). MVP = 2 voices: male = Pedro / carioca; female = hired professional / accent decided with her.
3. **Converse** full-duplex (turn-taking, barge-in), end-to-end latency p50 < 800 ms.
4. **Audio is the spine**: emotion, prosody, voice and turn-taking live in the conversational speech model itself. Text (STT/LLM/Inner-Monologue) is backstage/parallel, never the core (see `phase0/RETHINK.md`).

Central idea: language is not only the written word. Phonemes, prosody, melody, regional traits and emotion are first-class features, enriched over time with language and verbal-communication specialists.

## Motivation
- No strong open expressive pt-BR conversational voice exists. Closed leaders (ElevenLabs, GPT-4o Realtime, Gemini Live) are proprietary; Maya is the best isolated experience tested (rated above ElevenLabs) but its voice/fine-tune is not open and is English-centric.
- No open model is at once full-duplex + native pt-BR + emotion-controllable + commercial. The bet is **Moshi** (right architecture, pt-BR is the adaptation risk); co-bet **Qwen3-Omni** (native pt, Apache-2.0). pt-BR + emotion is the work, not a download.
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

## Commercial wedge (from /office-hours 2026-05-17 — see specs/business/2026-05-17-office-hours-wedge.md)
- **Wedge ICP:** cultural/experiential client with recurring real budget, annual procurement, who rejects variable cost (the "Mariclea/Sesc" archetype). Anchor: Sesc, 3-yr repeat client, R$350k+, a deferred PO gated on this product (declined an AI-voice activation feature purely on ElevenLabs cost).
- **Motion:** A → B. A = AI-voice as a fixed-price, capped, fail-closed line bundled into Unflat activation contracts now (runs on the R$50k box). B = standardized "signature voice" offer for the experiential segment, funded by A. Gov / maquininha / API = expansion, not wedge.
- **Moat:** owning a small (1B) pt-BR model → serving ≈ R$0.02-0.12/min, ~10-40× under ElevenLabs, subsidy-independent (SDumont funds training only; serving self-funded).
- **New product requirement:** fixed annual price + quota metering + **fail-closed** mode (hard-stop at quota, zero variable bill). Customer-dictated; only viable because of the moat. Must enter the roadmap via `/sdd` ATUALIZAR or a feature-spec (not silently rewritten here).

## Scope
### MVP delivers
- In-context cloning of 2 voices / 2 genders / 2 accents (M = Pedro/carioca; F = hired pro).
- Emotion control: categorical + intensity (neutral, warm/welcoming, enthusiastic, empathetic, sad, surprise; intensity 0..1), expandable.
- Low-latency streaming, end-to-end p50 < 800 ms, full-duplex (turn-taking, barge-in).
- Architecture chosen by data via Phase 0 (bet = Moshi full-duplex; co-bet Qwen3-Omni; CSM = voice component; cascade = floor).
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
4. Phase C business model — **resolved** by /office-hours 2026-05-17: wedge = experiential bundle (Mariclea/Sesc archetype), fixed-annual + fail-closed pricing, A→B motion. See `specs/business/2026-05-17-office-hours-wedge.md`. Remaining sub-question: the fixed-annual price point (clear discount vs ElevenLabs, fat-margin at owned serving cost).
5. Which portfolio product (beyond the website demo) is productized first after MVP.

## Inspiration / prior art
Sesame Maya/CSM (the recipe and the bar), Kyutai Moshi (full-duplex speech-native ceiling), ElevenLabs (market quality bar to beat, and the incumbent in Unflat's own installations). This project does not clone Maya; it builds a pt-BR voice of our own at Maya-class quality.
