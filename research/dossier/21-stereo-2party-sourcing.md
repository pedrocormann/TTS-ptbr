# Dossier 21 — 2-party stereo pt-BR sourcing (the binding constraint)

> Deep-dive on Moshi's hardest input requirement, complementing dossier 20
> (which mapped general/read corpora). Moshi-finetune needs **stereo: one
> speaker per channel**. Question: every realistic path to COMMERCIALLY-USABLE
> 2-party conversational pt-BR. Web pass 2026-05-17. License verdicts explicit.

## Reframe: "stereo" ≠ a data type, it's a *pipeline output*

Almost no corpus ships true dual-mic per-speaker stereo. J-Moshi proves the
real recipe: **fine-tune on 344 h real stereo + 602 h synthetic** (multi-stream
TTS), pretrain on 69k h *mono* dialogue (J-CHAT). So three supply lines, not one:
real-separable, diarize→split, synthetic. Mono 2-party is still useful (CPT).

## 1. Permissively-licensed 2-party pt-BR — verdicts

| Source | Scale (pt-BR) | Separability | License | Commercial | Verdict |
|---|---|---|---|---|---|
| **Câmara dos Deputados — TV/áudio legislativo** (plenário, comissões, audiências públicas) | **very large, growing daily** (years of sessions) | mono floor-mic, multi-speaker → **needs diarization** | **CC-BY-4.0** (live legislative events; watermark = attribution, must not be hidden) | ✅ **YES** | **#1 commercial-safe 2-party source.** Adversarial/turn-taking dialogue. Park: scraper + watermark-attribution handling |
| Câmara *produced* content (telejornais, docs) | n/a | n/a | CC-BY-**NC-ND** | ❌ | vetoed (derivatives + commercial forbidden) |
| **Court/CNJ/STF/STJ hearings & sessions** (TV Justiça, court YouTube, e-proc audiência recordings) | large (STF/STJ sessions, public hearings on YouTube; 1st-instance audiências in PJe) | mono → diarization; some 2-party Q&A (judge↔party) | **Lei 9.610 Art. 8º IV: leis, decisões judiciais e "demais atos oficiais" NÃO são objeto de proteção** → effectively public-domain *as official acts* | ✅ (Art. 8º) — but moral/privacy/LGPD on private parties | ✅ for the **act itself**; verify per-tribunal portal terms + redact identifiable private parties. Strong dyadic register (Q&A) |
| **TV/Rádio Senado** | large | mono | **proprietary non-commercial**, derivatives forbidden ("sem montagem/alteração", "vedado uso comercial") | ❌ | **VETOED** (contrast w/ Câmara — do not confuse the two) |
| EBC / TV Brasil / Rádio Nacional / Agência Brasil | medium-large (interview/debate shows) | mono | not CC by default; EBC content generally ©EBC, case-by-case; *some* tagged "domínio público" | ⚠️ mostly ❌ | default NO; only specific public-domain-tagged items or with EBC license. Park: EBC licensing contact |
| gov.br / Planalto / ministry audio | small, mostly speeches (1-party) | mono | Art. 8º (atos oficiais) for official pronouncements | ✅ but low value | low yield — monologue, not 2-party |
| YouTube CC-BY pt-BR dialogue channels | small/scattered; no curated set found | mono | per-video CC-BY (must verify each) | ✅ if truly CC-BY | manual curation only; not a scalable lane |
| Common Voice pt | ~170 h | single-spk, **read** | CC0 | ✅ | NOT conversational; CV has no released 2-party/spontaneous pt-BR slice (sentence-collector ≠ dialogue). Use for CPT/intelligibility only |
| LibriVox-pt | small | single-spk read; multi-reader dramatic works rare | public domain | ✅ | not dialogue; ignore for 2-party |

**Bottom line:** the commercial-safe 2-party pt-BR universe is essentially
**Câmara (CC-BY-4.0) + court/legislative audio (Art. 8º atos oficiais)** — both
mono-floor-mic ⇒ require a diarization→split pipeline. Register = formal/
adversarial, not casual SAC/empathy. That register gap is real and stays a moat.

## 2. Diarization → synthetic-stereo (pyannote)

- **pyannote speaker-diarization-3.1**: DER ~7% AMI-headset, ~11–22% CALLHOME
  telephone (2-party), worse on noisy/overlap. **pyannote `community-1`** (2025+)
  is now the better open baseline (lower speaker-confusion, same segmentation) —
  use it, not 3.1, as the default. Both pip-installable, gated HF model.
- Pipeline: VAD → diarization (2 speakers) → assign each speaker to L/R →
  zero/duck the other channel per turn → Moshi stereo. Overlaps (~12% of
  conversational speech) are the main failure: both-talking segments get
  mis-split. J-Moshi/Moshi tolerate this because the *model* learns turn-taking;
  perfect separation isn't required — **diarized-then-split is "good enough"** to
  fine-tune (it's literally how J-Moshi's non-studio data was handled), but it is
  *not* as clean as true dual-mic. Mitigation: filter clips by diarization
  confidence + ASR round-trip (J-Moshi's exact filter), discard high-overlap.
- Practical: feed Câmara/court mono → community-1 → keep only confident 2-spk
  segments → `annotate.py --lang pt`. This is the realistic main lane.

## 3. Synthetic 2-party generation (the scalable lane)

- Recipe (Moshi's own instruct data ≈ 20k h synthetic; J-Moshi's 602 h):
  LLM writes pt-BR dialogues (spoken-style rewrite) → 2 TTS voices → pan to
  L/R → ASR-filter. Fully in-house, infinite scale, no corpus license.
- **Commercial-safe pt-BR TTS for the synthesis step:**
  - **Kokoro (Apache-2.0)** — pt support, multi-voice, commercial OK ✅
  - **Chatterbox (MIT)** — commercial OK ✅; **XTTS-v2 = Coqui CPML (NC)** ❌,
    **F5-TTS = CC-BY-NC** ❌, **Fish weights CC-BY-NC** ❌ (correct dossier 50
    if it implies XTTS/F5 are usable to generate *shippable* training data —
    NC contaminates the output's commercial use; use Kokoro/Chatterbox).
  - Or our own CSM/Moshi voices once Phase 1 lands (self-bootstrapping).
- Quality ceiling: synthetic teaches turn-taking, timing, pt-BR phonetics — but
  inherits TTS prosody flatness and lacks authentic disfluency/emotion (the
  moat). J-Moshi ratio = **602 synth : 344 real ≈ 1.75 : 1**. Replicable: it
  needs only commercial-safe TTS (have it) + scripts (LLM). The 344 h *real*
  half is the hard half — that's Câmara/court (diarized) + in-house.

## 4. Telephony / call-center pt-BR

- **No open commercial BR call-center corpus exists** (BR equivalents of
  Fisher/Switchboard/CALLHOME pt are LDC-paid or absent). Confirmed gap.
- Realistic path = **record our own with consent**. The experiential/SAC wedge
  (Mariclea/Sesc archetype) *generates real 2-party pt-BR with LGPD consent as a
  byproduct of the product* — true dual-channel telephony stereo (each leg = a
  channel), the *ideal* Moshi format, in the exact target register. This is the
  data flywheel: product bootstraps its own gold training data. Phase B (needs
  consent UX + LGPD doc); not a this-week lever but the strategic answer to "where
  does scale come from."

## 5. Minimum viable

- **Phase-0 pipeline proof: ~1–3 h** stereo pt-BR (synthesis confirms loss-drop,
  LoRA-vs-CPT go/no-go). Cheapest legal path *this week*: (a) synth ~2 h via
  Kokoro/Chatterbox + LLM scripts (zero license risk, fastest), and/or (b)
  diarize ~2–3 h of Câmara CC-BY aud> via community-1. Both no-spend.
- **Usable pt-BR Moshi (per J-Moshi): ~300–900 h** fine-tune-stage equiv
  (J-Moshi: 344 real + 602 synth ≈ 946 h) on top of CPT. pt-BR likely cheaper
  than JA (Latin script, closer to Helium-EN). Realistic mix: synth ~600 h
  (cheap, have tools) + real ~300 h from **Câmara+court diarized** + in-house.
- Mono CPT base (J-CHAT analogue): Câmara/court mono at scale is the pt-BR
  J-CHAT substitute — no separability needed for the pretrain stage.

## Sourcing plan — ranked by effort/legality

1. **Synthetic (Kokoro/Chatterbox + LLM scripts)** — lowest effort, zero license
   risk, infinite scale, this week. Covers Phase-0 + the 600 h synth half.
2. **Câmara CC-BY legislative audio → community-1 diarize → split** — medium
   effort, clean license (CC-BY, attribution), large scale, the real-data
   workhorse. Park: scraper + watermark-attribution.
3. **Court/CNJ/STF/STJ audio (Art. 8º atos oficiais)** — medium effort, strong
   legal basis (not copyrightable), large; verify per-portal terms + LGPD-redact
   private parties. Adds dyadic Q&A register.
4. **In-house directed 2-party recording** — higher effort, perfect license/
   quality/register, the emotion+voice moat (~12–16 h, dossier 20).
5. **Product flywheel (consented SAC/experiential calls)** — Phase B; the
   strategic scale + ideal telephony stereo + target register.

## Park (needs licensing / contact / spend — DO NOT ACT)

- EBC/TV Brasil/Rádio Nacional licensing contact (only if interview-show audio
  wanted; default ©EBC, NOT CC).
- Per-tribunal portal terms-of-use review before bulk court-audio harvest;
  LGPD redaction policy for identifiable private parties in hearings.
- Câmara watermark/attribution mechanics for CC-BY compliance at scale.
- LDC pt telephony (none confirmed; revisit only if Câmara+synth insufficient).
- Consent UX + LGPD legal doc for the product data flywheel (Phase B).
- Re-verify Kokoro/Chatterbox pt-BR quality is good enough to not poison data.

Sources: J-Moshi arXiv 2506.02979 (344 real + 602 synth + 69k J-CHAT pretrain);
nu-dialogue/{j-moshi,moshi-finetune}; Câmara TV termos-de-uso (CC-BY-4.0 live /
CC-BY-NC-ND produced); Senado política-de-uso (proprietary NC); Lei 9.610/98
Art. 8º IV (Planalto L9610); pyannote speaker-diarization-3.1 + community-1
(HF) + arXiv 2509.26177 benchmark; STF/STJ/CNJ TV Justiça portals + YouTube;
TTS licenses: Kokoro Apache-2.0, Chatterbox MIT, XTTS Coqui-CPML, F5-TTS
CC-BY-NC, Fish CC-BY-NC (resemble.ai / bentoml TTS surveys 2025-26).
