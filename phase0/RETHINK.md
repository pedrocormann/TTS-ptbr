# RETHINK 2026-05-17 — text is parallel, not the spine

Pedro's correction (verbatim intent): the AI over-anchored on "Maya = hybrid with
text at the core." Maya/Sesame theoretically use text only in **parallel**; it is
not the core. The core they do extremely well is **conversation**. Our core is NOT
text/transcription (obviously needed in the back); it is **the best pt-BR emotional
audio conversation**. Rethink, revise, advance code.

## What primary sources actually say (verified)

- **Moshi (arXiv 2410.00037), verbatim:** *"operating purely in the audio domain
  already yields convincing results"*; the text "Inner Monologue" is a **time-aligned
  parallel scaffold** that *"increases the linguistic quality"* and is **ablatable**
  (you can set audio to *lead* text). True full-duplex: two parallel audio streams,
  no turn-taking assumption. ⇒ **audio is the spine; text is a parallel aid.**
  Nuance (kept honest): Inner Monologue is *"one of the most critical impacts on
  quality"* — parallel ≠ negligible.
- **CSM/Maya:** CSM *"cannot generate text"*; it is a single-utterance audio
  generator conditioned on prior conversational **audio**. Maya's lifelike feel =
  audio-context conditioning; a separate LLM only supplies content **words**
  (backstage), and Sesame did not open-source that stack. ⇒ CSM is a **voice
  component**, not a conversational spine.

## Decision delta

| Before (wrong) | After (corrected) |
|---|---|
| Bet = "CSM-hybrid", text-core framing | Bet = **Moshi** (true FD, text = parallel Inner Monologue) |
| CSM = the spine | CSM = **expressive voice component / clone block**, not a spine |
| Moshi = "ceiling probe only, not a candidate" | Moshi = **the architecturally-correct bet** |
| (none) | **Qwen3-Omni** added = pragmatic co-bet (Apache-2.0, native pt speech) |
| Cascade = fallback family | Cascade = **latency/expressivity yardstick** (the floor), not a destination |

## Why a co-bet, not a single bet
No open model is simultaneously parallel-stream full-duplex **and** native pt-BR
**and** emotion-controllable **and** commercially licensed. So Phase 0 races:
- **Moshi** (right architecture; pt-BR is the risk — adapt via official `moshi-finetune`)
- **Qwen3-Omni** (right language + license; near-FD turn-taking, not parallel-stream)
CSM probes the voice/clone quality; cascade sets the latency floor.

This file is the rationale of record. The `/sdd` ATUALIZAR at the 2026-06-17 review
folds it into mission/tech-stack/roadmap formally.
