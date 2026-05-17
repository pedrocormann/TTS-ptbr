# PARKING LOT — needs Pedro's authorization (NOT done autonomously)

Aggregated from the 2026-05-17 deep research pass. Pedro said: don't do anything
that requires authorization, save it for later. These are saved here. Nothing
below was acted on. Ordered by when it bites.

## Blocks Phase-0 / Phase-1 (decide soon)
- [ ] **HF gated-model license accepts** (free, but a human must click "agree"):
      `meta-llama/Llama-3.2-1B` (CSM dependency), `sesame/csm-1b`,
      `pyannote/speaker-diarization-3.1` (needed for stereo role-split).
      `kyutai/moshiko-pytorch-bf16` + `kyutai/mimi` are CC-BY-4.0 (no gate, but
      attribution obligation — note for legal). Qwen3-Omni Apache (no gate).
- [ ] **SDumont GH200 allocation** — still "pending auth" in specs. Blocks the
      Phase-1 continued-pretrain scale run. Needs PI/academic affiliation +
      proposal (continuous-flow call open). Contact CEIA-UFG / a USP lab.
- [ ] **Colab Pro+** subscription (≤ R$500/mo cap) for the smoke/QLoRA-proof rig.
- [ ] **W&B account** (free tier ok; `offline:true` mode for air-gapped SDumont)
      — moshi-finetune has native W&B. Resolves tech-stack open Q#5.
- [ ] **Private weights registry** decision (private HF repo vs object bucket)
      for the "gold" — tech-stack open Q#3.

## Spend / compute
- [ ] **NVIDIA Inception application** (free; account/contact decision) — overflow
      GPU + the live-serving box (SDumont is training-only, cannot serve).
- [ ] Continued-pretrain compute budget sign-off (J-Moshi ref: 128×V100·36h;
      scale to GH200, pt-BR likely cheaper — quantify before committing).
- [ ] Download `kyutai/DailyTalkContiguous` (14 GB) — bandwidth/storage decision.

## Datasets — license accept / sign / pay / contact
- [ ] **MSP-Podcast / MSP-Conversation** — sign UTD/Carlos-Busso academic license;
      verify the commercial clause for source clips. The one high-value emotion-
      *method* lever with a plausible commercial path. Worth the signature.
- [ ] **LDC** (Fisher / Switchboard) — paid membership; only if Moshi-recipe
      full-duplex method data proves insufficient.
- [ ] **CANDOR** — confirm commercial vs research-only terms before any product use.
- [ ] CORAA / NURC-SP / NURC-Recife authors (NILC / C4AI-USP / UFPE) — only if a
      commercial carve-out / academic partnership is wanted (Phase B). Currently
      NC-ND ⇒ research probe only, never trained into shippable weights.
- [ ] C-ORAL-BRASIL (UFMG) — NC; contact only if mineiro spontaneous needed.
- [ ] Re-verify exact license tags of EARS / Expresso before any non-research use.

## Legal / compliance
- [ ] **Counsel on voice-clone consent + data provenance vs LGPD + ANPD 2026
      voice-biometrics rules** — engage BEFORE any voice-donation/cloning data
      collection. Voice = sensitive personal data; clone-fraud R$4.5B/2025.
      Blocks Phase-2 (the 2 signature voices: Pedro + hired F).
- [ ] Mirror Sesame acceptable-use + Moshi/Mimi CC-BY attribution + Llama-3.2
      community license into product T&Cs (legal review before commercial ship).
- [ ] LGPD consent artifacts per recorded/cloned voice (Phase-2 blocker).

## Business / funding (decisions + spend + contact)
- [ ] **Apply to FINEP R$300M Digital-Technologies edital** (deadline 2026-09-30,
      PBIA/sovereignty) — priority target. Needs budget plan, legal/CNPJ, likely
      academic co-proponent (CEIA-UFG). Pedro/Unflat decision.
- [ ] FINEP+BNDES AI Fund (Apr-2026) — equity/fund-of-funds, manager-selection
      deadline 2026-05-28; likely NOT directly applicable — confirm & drop or pursue.
- [ ] ElevenLabs Startup Grant (12mo free/680h) — weigh incumbent lock-in vs runway.
- [ ] Outreach: Edresson Casanova (NVIDIA, pt-BR TTS SOTA) / CEIA-UFG — partnership
      anchor (strengthens SDumont + FINEP). Maritaca — text-LLM partner candidate.
      All = relationship/NDA decisions, Pedro's call.

Nothing here is urgent enough to have justified acting without you. The Phase-0
technical work (dossier 00 §Revised Phase-0) needs none of it to start.
