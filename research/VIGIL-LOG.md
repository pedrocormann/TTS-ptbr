# Research Vigil Log

Weekly scan (per CHRONOGRAM standing ritual): review watched orgs/people/arXiv →
log findings here → decide incorporate into the spine / test in parallel / ignore.

---

## 2026-05-17 — Deep scan #1 (autonomous, 5-front + code reads)

Dossier written: `research/dossier/{00-SYNTHESIS,10..50}.md`. Highlights:

**Incorporate into the bet:**
- **J-Moshi (arXiv 2506.02979)** — non-EN/FR Moshi recipe = CPT + tokenizer/embed
  swap + stereo FT, Mimi frozen. ⇒ pt-BR plan is CPT, not LoRA-only. Use
  `nu-dialogue/moshi-finetune` + `nu-dialogue/j-moshi` as references. **Adopted.**
- **Moshi weights = CC-BY-4.0** (verified in cloned repo README) — commercial OK
  w/ attribution. Bet legal. **Confirmed.**
- **Codec = freeze/clone Mimi recipe** (12.5 Hz split-RVQ WavLM-distilled causal).
  Foundational, upstream of spine. **Adopted into Phase-0 (test #1 = Mimi freeze).**
- **Emotion = implicit + NL prompt + light paralinguistic-RL** (Step-Audio 2,
  arXiv 2507.16632, ~2× GPT-4o-Audio). **Adopted for Phase-3 method.**

**Test in parallel / watch:**
- Qwen3-Omni (2509.17765, Apache-2.0) — co-bet hedge; verify pt speech-output.
- Step-Audio 2 (2507.16632) — emotion/paralinguistic-RL method study.
- Full-Duplex-Bench v1.5/v2 (2507.23159 / 2510.07838), URO-Bench (2502.17810) —
  eval harness blueprint (pt-BR version = strategic asset, none exists).
- Codecs: U-Codec/FlexiCodec/TS3 5-Hz frontier (watch, don't adopt yet).
- Watermarking: AudioSeal (2401.17264), VoiceMark (2505.21568) — day-one.

**New facts logged:**
- ElevenLabs $11B (Feb-26), entering Brazil, pure usage pricing → wedge durable.
- Sesame $250M Series B, pivot to wearables, not selling pt-BR API.
- FINEP R$300M Digital-Tech edital, deadline 2026-09-30 (priority funding).
- SDumont +575% capacity ("first step of PBIA"); free training-only confirmed.
- ANPD voice-biometrics rules expected 2026; voice = sensitive data (LGPD).

**Watchlist (scan weekly):**
- Orgs/repos: kyutai-labs (moshi/finetune/DSM/hibiki releases), QwenLM (Qwen-Omni),
  stepfun-ai (Step-Audio), SesameAILabs (csm), canopyai (Orpheus), nu-dialogue
  (J-Moshi lineage), Edresson (pt-BR TTS).
- People: Edresson Casanova (NVIDIA), Kyutai team (Défossez/Zeghidour), Maritaca CEO.
- Sources: arXiv eess.AS/cs.SD/cs.CL (pt-BR / full-duplex / speech-LM / codec),
  HF papers daily (audio), finep.gov.br, sdumont.lncc.br/call.php, gov.br/anpd,
  elevenlabs.io + kyutai.org blogs.
- Recheck at ship: per-repo license text, Moshi watermarker presence, annotate.py
  model versions, Qwen3-Omni pt speech-out.

### 2026-05-17 — scan #1 continued (2 verification frentes)

**Qwen3-Omni pt verified (2 primary sources):** `pt` IS in the speech-OUTPUT
set (HF card + arXiv 2509.17765 Table 3). Genuine co-bet. Caveats: generic "pt"
(likely EU-leaning, pt-BR needs FT); emotion control **weak** (3 fixed speakers
Ethan/Chelsie/Aiden + system prompt only, no tags/clone); no official LoRA;
heavy (~79GB bf16 → 2×A100, community AWQ-4bit only). Apache-2.0 ✅.
- **New emotion model to study: Step-Audio-EditX** (3B, Apache, emotion/style/
  paralinguistic edit + RL) + Step-Audio-2-mini — best-in-class controllable
  emotion, lighter than Qwen. **GLM-4-Voice-9B** (26 langs, low-lat FD, small)
  = 3rd candidate. MiMo-Audio (MIT). No Moshi v2; CSM-3B/8B still closed.

**2-party pt-BR sourcing (dossier 21):** corrects dossier 20. **Câmara CC-BY-4.0**
+ **court/CNJ Art. 8º public-domain** = real commercial 2-party lane (formal
register). **Senado = NC, do not use.** Synthetic via **Kokoro (Apache)/
Chatterbox (MIT)** only — XTTS/F5 NC poisons output. pyannote **community-1** >
3.1. Phase-0 needs ~1–3 h (synth = fastest, no-spend, this week). J-Moshi mix
≈ 602 synth : 344 real on mono-dialogue CPT.

**Action deltas:** to_stereo.py → community-1; tools/data + eval harness built;
spike_c requirements fixed (torch 2.6 conflict — separate venvs B vs C).

### 2026-05-17 — scan #2 (compute budget + voice/watermark) → dossier 60, 70

**CPT probably SKIPPABLE for pt-BR (big).** Finetune ≈ 6–20 GH200-h / <US$60 /
<1 day. Heavy CPT (~920–1,540 GH200-h) only forced by tokenizer-swap/embedding-
re-init — pt-BR (Latin, Helium EN/EU-heavy) likely keeps Helium tokenizer ⇒
**LoRA-only is the first bet; CPT is the fallback gated by native-speaker eval,
not metrics.** Do scenario M (SDumont LoRA, ~free) regardless. SDumont: 1 UA =
1 CPU-core-h, Standard ≥750k covers all; confirm GPU→UA w/ helpdesk-sdumont.

**Voice path CORRECTED.** For a Moshi spine: NOT per-voice LoRA, NOT CSM-front
(CSM doesn't compose with FD Moshi — either/or). Use **Kyutai-TTS/DSM voice-
EMBEDDING conditioning** (re-anchored, no drift); ~5–15 min/voice; LoRA staged
fallback. ⇒ corrects dossier 50's "CSM = the voice component" for the Moshi case.

**Watermark CORRECTED.** Sony RAW-Bench: post-waveform marks (AudioSeal etc.)
ERASED by neural-codec re-encode; our output IS Mimi-decoded. Ship AudioSeal
(MIT) day-one as **provenance signal only**; codec-embedded/Latent-Mark = the
durable Phase-3+ upgrade. VoiceMark license unstated → don't ship.

**Action deltas:** synth 2-party pipeline built + CPU-tested (gen_dialogues +
compose_stereo ✓); eval harness CPU-validated; dossier 50/00 get correction
pointers; PARKING-LOT += helpdesk-sdumont email, privacy counsel, VoiceMark lic.

Next scan: 2026-05-24 (weekly). Big review folds this: 2026-06-17 (`/sdd` ATUALIZAR).

---

## 2026-06-10 — Deep scan #3 (8-front web sweep; the big review, 1 week early)

Dossier: `research/dossier-2026-06/10..60-*.md`. Plan: `specs/REPLAN-2026-06-10.md`.

**Incorporated into the bet:**
- **Qwen3-TTS (jan/2026, Apache, pt native, 97ms TTFA, official finetune)** —
  Track-A candidate #1; also replaces Kokoro as synthetic-data generator.
- **Kyutai interactivity-RL (2026-06-10!, `moshika-rl-seamless` CC-BY-4.0, arXiv
  2606.11167)** — adopted as F5 post-training blueprint (supersedes Step-Audio-2
  as primary reference).
- **PersonaPlex-7B (NVIDIA, jan/2026)** — Moshi-architecture validation + public
  persona/voice-prompt recipe (paper 2602.06053). Weights NVIDIA OML = outside
  whitelist; replicate recipe, don't touch weights.
- **Colab Pro+ A100-80/G4-96GB** — moshi-finetune fits in Colab now.
- **Unsloth CSM-1B T4 notebook** — no public pt-BR CSM finetune exists; open lane.
- **Eval v2**: TTSDS2 + Audiobox-Aesthetics + DNSMOS + Parakeet-v3 second-ASR +
  emotion2vec+ SER head; UTMOS demoted. BIPA (CC-BY, Rio IPA) for accent eval.

**Watch / vetoes:**
- Pocket-TTS-pt (CC-BY, CPU 200ms) — listening test pending (pt-BR vs pt-PT).
- NILC `NURC-SP_ENTOA_TTS` MIT tag — email NILC before training shippable weights.
- New vetoes: Voxtral TTS (NC), Higgs v2/v3, Spark-TTS (relicensed NC!), Fish
  S2-Pro (research), TAGARELA (NC, eval-only), CETUC (research-only).
- Reg: PL 2338 pending vote; **PL 1460/2026** (voice replicas: consent+watermark
  mandatory) — our design is already compliant.

Next scan: 2026-06-17 (weekly). Next hard review: **2026-07-17**.
