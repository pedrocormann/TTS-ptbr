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
