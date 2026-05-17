# TTS-ptbr — Roadmap

> **DRAFT v0.2.** Phases intentionally small (each implementable in a focused session, independently testable). No external deadline. Bet = path B; A/C/Orpheus validated in Phase 0. Standing ritual: research vigil each sprint. Owners: Pedro (core ML solo), João (data phase only).

---

## Phase 0: Hypothesis validation

**Goal:** decide the architecture with data, not on paper. Throwaway parallel spikes, one decisive metric each.

- [ ] Spike A — cascade: faster-whisper → pt-BR LLM → Orpheus/XTTS clone. Metric: e2e p50 < 800 ms + intelligible clone from 10-30 s sample
- [ ] Spike B — CSM hybrid (bet): pt-BR LLM → CSM-1B on audio context. Metric: prosody/emotion MOS vs A + CSM pt-BR phonetics w/o fine-tune
- [ ] Spike C — Moshi ceiling probe: stock Moshi. Metric: measured full-duplex latency + pt-BR out-of-box go/no-go
- [ ] (optional) Spike Orpheus — dedicated TTS latency spike
- [ ] Decision: lock architecture from metrics; record in tech-stack + Dev KB
- [ ] Compute ready: Colab set up + SDumont GH200 requested/confirmed + NVIDIA Inception activated

---

## Phase 1: Lock B + pt-BR base + labeler

**Goal:** chosen architecture runs; intelligible pt-BR speech (no expressivity yet); eval harness; data-labeling unblocked.

- [ ] Eval harness: latency instrumentation + WER round-trip pipeline (faster-whisper)
- [ ] pt-BR base via open corpora (TTS-Portuguese seed + CML-TTS); QLoRA proof on Colab
- [ ] Baseline numbers recorded (latency, WER) vs Phase-0 ceiling
- [ ] LLM interface defined (content layer pluggable)
- [ ] Lightweight in-house labeling tool: tag emotion/accent/quality on pt-BR audio

---

## Phase 2: Two-voice in-context cloning

**Goal:** clone M (Pedro/carioca) and F (hired professional) from short conversational samples.

- [ ] Directed recording protocol + team mics; record Pedro (carioca) seed audio
- [ ] Hire female voice talent; decide her accent; record F seed audio + consent form
- [ ] In-context cloning working for both voices
- [ ] Voice-clone similarity measured (speaker-verification cosine)
- [ ] LGPD doc + consent artifacts stored; weights moved to private registry

---

## Phase 3: Emotion control

**Goal:** controllable emotion on both voices (categorical + intensity).

- [ ] Emotion scheme: neutral, warm/welcoming, enthusiastic, empathetic, sad, surprise; intensity 0..1
- [ ] Emotion-prompted directed recordings; labeled via the tool
- [ ] Conditioning implemented (tags + reference audio); emotion accuracy measured
- [ ] First contact with a language/verbal-communication specialist (rubric input)

---

## Phase 4: Full-duplex < 800 ms

**Goal:** turn-taking + barge-in within the latency budget; gating metrics pass.

- [ ] silero-vad + turn-taking + barge-in integrated (hybrid Python + Rust/Moshi server)
- [ ] End-to-end latency optimized to p50 < 800 ms
- [ ] MOS internal blind panel (1-5) vs baseline + ElevenLabs + Maya; MOS ≥ 4.0
- [ ] Gating metrics pass (latency, MOS, WER)

---

## Phase 5: Unflat-website demo + hardening

**Goal:** public demo as the GTM wedge; stabilize for internal/sales use.

- [ ] Web demo: low-latency pt-BR conversation, freemium gating (2 min anon / 10 min signed)
- [ ] Robustness pass (noise, interruptions, long sessions)
- [ ] Open/closed split enforced (open code, private weights registry)
- [ ] Demo instrumented for sales (usage, feedback capture)

---

Future phases (parking lot, not yet planned): 5 regional accents; production API + scale (multi-tenant, SLA); productized portfolio (Museum Lens / smart glasses, "Fala Cidadão" gov booth, agentic enterprise SAC, live-marketing activations, art installations, physical "maquininha" device); formal language-specialist enrichment program; labeling tool as a standalone product; B2B/D2C business model (routed to `/office-hours`).
