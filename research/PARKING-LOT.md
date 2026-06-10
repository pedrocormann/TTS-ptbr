# PARKING LOT — needs Pedro's authorization (NOT done autonomously)

Aggregated from the 2026-05-17 deep research pass. Pedro said: don't do anything
that requires authorization, save it for later. These are saved here. Ordered by
when it bites.

> **STATUS 2026-05-17 (pre-sleep):**
> - `meta-llama/Llama-3.2-1B` → **submitted, AWAITING META MANUAL REVIEW**
>   (not instant; minutes–days). Blocks **only Spike B (CSM)**, which is
>   secondary. Spike-only fallback: Llama-3.2-1B tokenizer via an ungated
>   mirror (e.g. `unsloth/Llama-3.2-1B`) — research/spike use only, NOT product.
> - `sesame/csm-1b` → **clicked by Pedro 2026-05-17** (auto-accept, granted).
> - `pyannote/speaker-diarization-community-1` (+3.1) → **clicked, granted**.
> - HF read token → **created by Pedro**, kept by him (→ Colab `HF_TOKEN`).
>   ⤷ Next session: verify Llama-3.2 status (Meta review) before Spike B.
> - `kyutai/moshiko-pytorch-bf16` + `kyutai/mimi` → **NO gate (CC-BY-4.0)**;
>   token is enough. **Critical path (Moshi spine, Mimi-freeze test, data
>   pipeline) does NOT depend on the Meta review.**
> - Colab Pro+ / W&B / NVIDIA Inception = PENDING (not tonight). Rest = PENDING.

## Blocks Phase-0 / Phase-1 (decide soon)
- [x] **HF gated-model accepts + read token** — Pedro committing 2026-05-17
      (pre-sleep): `meta-llama/Llama-3.2-1B`, `sesame/csm-1b`,
      `pyannote/speaker-diarization-community-1` (+3.1 fallback) + a READ token
      at hf.co/settings/tokens (kept by Pedro → Colab `HF_TOKEN`).
      `kyutai/moshiko-pytorch-bf16` + `kyutai/mimi` = CC-BY-4.0 (no gate;
      attribution obligation — legal note). Qwen3-Omni Apache (no gate).
      ⤷ Verify on next session that all 3 accepts went through before Spike C.
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
- [ ] **Câmara dos Deputados CC-BY-4.0 audio** — confirm attribution mechanics at
      scale (how to credit in a trained model / product) before bulk ingest.
- [ ] **Court/CNJ/STF audio (Art. 8º public-domain)** — per-portal terms review +
      an **LGPD redaction policy for private parties' voices** (legal) before use.
- [ ] EBC / TV Brasil — licensing contact (mostly ©, case-by-case) only if needed.
- [ ] Re-verify **Kokoro (Apache) / Chatterbox (MIT) pt-BR quality** before bulk
      synthetic generation (no spend; a quality check, parked as a task).
- [ ] Product **data flywheel**: consent UX + LGPD doc so consented SAC calls
      become training data (Phase B; legal + product decision).

## Legal / compliance
- [ ] **Counsel on voice-clone consent + data provenance vs LGPD + ANPD 2026
      voice-biometrics rules** — engage BEFORE any voice-donation/cloning data
      collection. Voice = sensitive personal data; clone-fraud R$4.5B/2025.
      Blocks Phase-2 (the 2 signature voices: Pedro + hired F). Concrete consent-
      artifact + provenance-log checklist now in dossier 70 §B — counsel reviews it.
- [ ] **Clear VoiceMark license** before any use (unstated). AudioSeal MIT /
      Moshi-Mimi CC-BY-4.0 / CSM Apache are clear. Hired-talent voice IP/license
      contract = counsel item too.
- [ ] **Email helpdesk-sdumont@lncc.br** to confirm the GPU→UA conversion before
      sizing the SDumont Standard proposal (no published rate; needed to budget).
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
- [ ] **Outreach: Frederico Santos de Oliveira** (fredso.com.br, HF freds0; prof
      UFMT, PhD UFG, pesquisador AKCIT/MCTI-EMBRAPII; 1º autor do TAGARELA,
      co-autor recorrente do Edresson — um contato puxa o outro). Pauta
      (refinada pelo dossiê 80): (i) thresholds do subset clean-2.800h do
      TAGARELA (não publicados); (ii) roadmap dos checkpoints "Coming Soon"
      (Orpheus/Chatterbox-pt); (iii) licença do código SER (repo sem LICENSE) e
      do BRSpeech-TTS; (iv) parceria AKCIT (FINEP/SDumont). [Pedro, 2026-06-10]

Nothing here is urgent enough to have justified acting without you. The Phase-0
technical work (dossier 00 §Revised Phase-0) needs none of it to start.
