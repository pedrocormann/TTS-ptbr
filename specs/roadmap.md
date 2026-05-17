# TTS-ptbr — Roadmap

> **DRAFT v0.1.** Phases intentionally small (each implementable in a focused session, independently testable). No external deadline. Bet = path B; A/C/Orpheus validated in Phase 0. Standing ritual: research vigil each sprint.

---

## Phase 0: Hypothesis validation

**Goal:** decide the architecture with data, not on paper. Throwaway parallel spikes, one decisive metric each.

- [ ] Spike A — cascade: streaming Whisper → pt-BR LLM → Orpheus/XTTS clone. Metric: e2e p50 < 800 ms + intelligible clone from 10-30 s sample
- [ ] Spike B — CSM hybrid (bet): pt-BR LLM → CSM-1B on audio context. Metric: prosody/emotion MOS vs A + CSM pt-BR phonetics w/o fine-tune
- [ ] Spike C — Moshi ceiling probe: stock Moshi. Metric: measured full-duplex latency + pt-BR out-of-box go/no-go
- [ ] (optional) Spike Orpheus — dedicated TTS latency spike
- [ ] Decision: lock architecture from metrics; record in tech-stack + Dev KB
- [ ] Compute ready: Colab set up + SDumont GH200 requested/confirmed + NVIDIA Inception activated

---

## Phase 1: Lock B + pt-BR base

**Goal:** chosen architecture runs; intelligible pt-BR speech (no expressivity yet) + eval harness.

- [ ] Eval harness: latency instrumentation + WER round-trip pipeline
- [ ] pt-BR base via open corpora (TTS-Portuguese seed + CML-TTS) on chosen model
- [ ] Baseline numbers recorded (latency, WER) vs Phase-0 ceiling
- [ ] LLM interface defined (content layer pluggable)

---

## Phase 2: Two-voice in-context cloning

**Goal:** clone M (Pedro/carioca) and F (`[TBD]`) from short conversational samples.

- [ ] In-house directed recording protocol + team mics; record M and F seed audio
- [ ] In-context cloning working for both voices
- [ ] Voice-clone similarity measured (speaker-verification cosine)
- [ ] Consent artifacts for recorded voices (LGPD)

---

## Phase 3: Emotion control

**Goal:** controllable emotion on both voices.

- [ ] Emotion set + labeling scheme defined
- [ ] Emotion-prompted directed recordings
- [ ] Emotion conditioning implemented; emotion accuracy measured
- [ ] First contact with a language/verbal-communication specialist (rubric input)

---

## Phase 4: Full-duplex < 800 ms

**Goal:** turn-taking + barge-in within the latency budget.

- [ ] VAD + turn-taking + barge-in integrated
- [ ] End-to-end latency optimized to p50 < 800 ms
- [ ] MOS listening panel run vs baseline/Maya
- [ ] Gating metrics pass

---

## Phase 5: Second accent + hardening

**Goal:** add the 2nd accent; stabilize for internal Unflat use.

- [ ] 2nd accent data + integration
- [ ] Robustness pass; integrate into one Unflat product (pilot)
- [ ] Open/closed split enforced (open code, private weights mechanism)

---

Future phases (parking lot, not yet planned): 5 regional accents; production API + scale (multi-tenant, SLA); formal language-specialist enrichment program; manual labeling tool as a product; partial open-source release (code) with closed weights; B2B/D2C business model (candidate for `/office-hours`).
