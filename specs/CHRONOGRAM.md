# TTS-ptbr — Macro Chronogram

> Macro view only. All month bands are **projections, not commitments** (SDD = phases,
> not deadlines). The only hard gate is the monthly spec/plan review.

Start: 2026-05-17.

## ★ Hard checkpoint — 2026-06-17 (review in 1 month)
Re-read and revise `specs/{mission,tech-stack,roadmap}.md` + `specs/business/`.
Run `/sdd` in ATUALIZAR mode. Decide: did Phase 0 data change the architecture bet?
Fold the fail-closed/quota requirement into the roadmap. Re-baseline this chronogram.
**Nothing below this line is fixed until this review passes.**

## Month bands (projection)

| Band | ~Window | Roadmap phase | Macro goal |
|---|---|---|---|
| M0 | May (now) | Phase 0 kickoff | Clone repos, research base, spikes A/B/C/Orpheus, compute setup, first Colab QLoRA smoke |
| ★ | **2026-06-17** | — | **Spec/plan review (hard gate)** |
| M1 | Jun–Jul | Phase 1 | Architecture locked; pt-BR base; eval harness; labeler-lite |
| M2 | Jul–Aug | Phase 2 | 2-voice in-context cloning (Pedro/carioca + hired F) + consent/LGPD |
| M3 | Aug–Sep | Phase 3 | Emotion (tags + reference audio) + fail-closed/quota + specialist contact |
| M4 | Sep–Oct | Phase 4 | Full-duplex <800ms, MOS panel, gating metrics pass |
| M5 | Oct–Nov | Phase 5 | Website demo (freemium 2/10min) + target Sesc next-cycle bundled deal |

## Standing ritual — research vigil (weekly, Mondays)
Scan watched orgs/people/arXiv (`research/REFERENCES.md`) → append findings to
`research/VIGIL-LOG.md` → decide per finding: incorporate into bet B, test in
parallel, or ignore. 30 min, every week. This is not optional; it is how the bet
stays current against a fast-moving field.

## Review cadence
- Weekly: research vigil (above).
- Monthly: spec/plan review (the ★ gate; first one 2026-06-17, then rolling).
- Per phase: `/feature-spec` before implementing; `/review` before merge; `/qa` before ship.

## Session log

> Honest accounting: elapsed = verifiable git span (first→last commit); real
> session is a bit longer (pre-first-commit interview not git-captured).
> Plus concrete output + an honest *human-equivalent* estimate. One block/session.

### Day 1 — 2026-05-17 (project kickoff)
- **Arc:** memory note → SDD constitution (mission/tech-stack/roadmap v0.2, 28-Q
  interview) → office-hours business wedge (Sesc/Mariclea) → architecture RETHINK
  (audio-spine, bet = Moshi) → deep research dossier → Phase-0 spikes vs real
  cloned APIs → eval harness + synthetic 2-party pipeline (built + CPU-tested) →
  data pipeline + RUNBOOK + PARKING-LOT.
- **Concrete output:** 14 commits · 55 versioned files · ~3,600 lines specs/code/
  dossier · 13 research docs · 10 research agents · 2 skills (created
  `feature-spec`, updated `/sdd`+dev-kb) · 3 real bugs caught+fixed by testing.
- **Elapsed (verifiable):** git span 1st→last commit = **22:58→02:07 ≈ 3h09m**,
  continuous (commit every ~5–30 min, no idle/sleep gap). Real session ≈ 3h30–4h
  (the pre-first-commit `/sdd` interview isn't git-captured). Single late-night session.
- **Human-equivalent (estimate):** ~2–4 person-weeks of a small team
  (researcher: the dossier; ML eng: spikes/pipeline/eval; + spec/business) →
  delivered in ~3–4h. That ratio is the actual compression story.
- **State at close:** critical path unblocked (Moshi/Mimi ungated; HF token +
  csm-1b/pyannote granted; Llama pending Meta — secondary). Next: token + Colab
  + `phase0/RUNBOOK.md` (copy-paste). No open decisions blocking execution.
