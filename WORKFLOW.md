# Working method (Spec-Driven Development + gstack)

This project is governed by its constitution in `specs/` (mission, tech-stack, roadmap).
Spec-first: specs before code. Skills are composable, not merged (small tools > one
mega-skill) — easier to maintain.

## Pipeline (ideal greenfield order)

| # | Command | Purpose | Output |
|---|---|---|---|
| 0 | `/office-hours` | Pressure-test demand/wedge BEFORE writing specs | design doc in `specs/business/` |
| 1 | `/sdd` | Constitution (ingests the office-hours doc) | `specs/{mission,tech-stack,roadmap}.md` |
| 2 | `/feature-spec` | Per roadmap phase: requirements + plan + validation, then implement | `specs/AAAA-MM-DD-<feature>/` |
| 3 | `/plan-ceo-review` | On any ambitious feature idea, before building | reviewed plan |
| 4 | implement | Execute the plan groups | code |
| 5 | `/review` | Any branch with changes, pre-merge | review report |
| 6 | `/qa` | Staging URL before shipping | QA report |

Note: we ran 1 before 0 this time (sdd then office-hours). Future projects: 0 first, so
the mission is grounded in demand evidence, not assumptions. Use office-hours for the
forcing questions + design doc; ignore its YC-recruitment closing (noise for internal use).

## Per-change checklist

- Run `/office-hours` — describe what you're building
- Run `/plan-ceo-review` on any feature idea
- Run `/review` on any branch with changes
- Run `/qa` on your staging URL

## Where artifacts live

```
specs/                      constitution (mission, tech-stack, roadmap)
specs/business/             office-hours design docs (demand/wedge diagnostics)
specs/AAAA-MM-DD-<feature>/ per-phase feature specs (from /feature-spec)
weights/                    PRIVATE — gitignored (the "gold")
```

All TTS-ptbr artifacts live in this repo (github.com/pedrocormann/TTS-ptbr).
This project is independent from any other Unflat repo.
