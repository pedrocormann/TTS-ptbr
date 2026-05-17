# Dossier 00 — SYNTHESIS (autonomous research pass, 2026-05-17)

Keystone doc. 5 web frentes + deep code reads of the cloned repos. Read this
first; 10–50 are the depth. Honest about contradictions and residual unknowns.

## The one contradiction we found — RESOLVED

The academic agent (dossier 30) reported **Moshi weights = CC-BY-NC-SA (non-
commercial)**. Dossiers 13 & 50 said CC-BY-4.0. This decides whether the entire
Moshi bet is even legal for a commercial product, so it could not be left fuzzy.
**Resolved from the source of truth on disk** — `research/repos/moshi/README.md`
line 86 & 277, verbatim: *"All models are released under the CC-BY 4.0 license."*
/ *"The weights for the models are released under the CC-BY 4.0 license."* Code =
MIT (Python) / Apache (Rust).

> **VERDICT: Moshi weights = CC-BY-4.0. Commercial use OK with attribution.**
> Mimi = CC-BY-4.0 too. The bet is commercially viable. Dossier 30's NC claim is
> wrong (agent confusion, likely with dGSLM/older claim). Re-confirm on the live
> `hf.co/kyutai/moshiko-pytorch-bf16` card at ship time, but the repo is explicit.

## What changed vs what we believed before

1. **Recipe correction (important).** Dossier 10 (from cloned code) implied "pt-BR
   via LoRA is a real path." J-Moshi (arXiv 2506.02979 — the ONLY rigorous non-
   EN/FR Moshi adaptation, Japanese) shows the working recipe is **continued-
   pretrain + tokenizer swap + text-embedding re-init + stereo finetune**, NOT
   LoRA-only. **Mimi freezes** (transfers to new languages unchanged — a 1-day
   test confirms for pt-BR). pt-BR should be *easier* than Japanese (Latin script,
   structurally closer to Helium's EN). LoRA is still the right *smoke/proof*
   step; it is likely *insufficient for fluent pt-BR* alone. Plan CPT.
2. **Codec is THE foundational decision** (all three technical dossiers converge):
   adopt/freeze the **Mimi recipe** (12.5 Hz, split-RVQ, WavLM-distilled *causal*
   semantic RVQ-0, ~8 codebooks). Never DAC/EnCodec-class (75–86 Hz) — sequence
   length, not fidelity, governs real-time. This is upstream of the spine choice.
3. **Emotion has a 2026 "right answer":** implicit audio-context base + natural-
   language style prompt + a **light paralinguistic-RL pass** (Step-Audio 2:
   ~2× GPT-4o-Audio on paralinguistic accuracy via GRPO). Pure emotion-tags alone
   is dated. RL/DPO stays Phase-3+; SFT-with-tags first.
4. **Data reality is sharper:** open pt-BR is ~1,500 h+ but **read-speech only**
   (CC-BY/CC0, intelligibility). **Every** sizeable spontaneous/emotional pt-BR
   corpus (CORAA, NURC-SP, MUPE, C-ORAL-BRASIL) is **CC-BY-NC-ND — product-
   vetoed** (research probe only). emotion×accent for Brazil ≈ **0 h open**. The
   binding constraints for Moshi specifically: (a) **stereo 2-party** pt-BR
   (Moshi-role/user-role split — must be engineered via pyannote 3.1), (b)
   in-house emotion/voice recording (~12–16 h raw). Both = the moat.
5. **Eval is a strategic asset:** no pt-BR conversational-S2S benchmark exists.
   Building one (URO-Bench-style + Full-Duplex-Bench v1.5 + UTMOS/DNSMOS + WER
   round-trip + pt-BR SER) is both necessary and defensible IP. F5-TTS (cloned)
   ships `eval_utmos.py` + `ecapa_tdnn.py` — reuse.
6. **Watermark from day one:** fake-voice detectors are losing the arms race
   (2510.06544). Proactive watermarking (AudioSeal/VoiceMark) baked into the
   codec/vocoder is the only credible consent posture — and aligns with **ANPD
   voice-biometrics rules landing 2026** (voice = sensitive data under LGPD).

## Decision-relevant conclusions

- **Bet holds, sharper: Moshi architecture + CC-BY-4.0 weights, adapted to pt-BR
  via CPT (not LoRA-only), Mimi frozen.** J-Moshi is the de-risking template;
  `nu-dialogue/moshi-finetune` fork + `nu-dialogue/j-moshi` are the references.
- **Qwen3-Omni (Apache-2.0, native pt) is a genuine co-bet/hedge**, not a
  formality: if CPT proves too costly or pt-BR transfer weak, it's the license-
  clean fallback (accept turn-based + fast barge-in for v1).
- **CSM stays the voice-clone component** (native in-context cloning, excellent;
  per-voice LoRA stabilizes long-dialogue drift). Not the spine.
- **Business wedge confirmed durable.** ElevenLabs ($11B, entering Brazil) is
  pure usage-priced and structurally can't follow fixed-price/fail-closed without
  cannibalizing $330M ARR. Sesame pivoting to wearables (not selling pt-BR API)
  ⇒ low direct competition on the wedge.
- **FINEP R$300M Digital-Technologies edital (deadline 2026-09-30, PBIA/
  sovereignty-aligned) = priority funding target.** SDumont upgraded +575%
  ("first step of PBIA") — the free-training plan is valid. Edresson Casanova /
  CEIA-UFG = the pt-BR speech academic backbone + partnership anchor (strengthens
  SDumont allocation AND FINEP positioning). Maritaca = text-LLM **partner**
  candidate (no voice), not a competitor.

## Revised Phase-0 (consolidated — supersedes earlier spike framing details)

Order, all no-spend, fits 1×A100-80G / GH200 / Colab-A100 except where noted:
1. **Mimi pt-BR round-trip freeze test** — 30 min pt-BR → Mimi encode→decode →
   WER/UTMOS vs original. If acceptable ⇒ freeze Mimi (mirrors J-Moshi). *1 day, decisive, do first.*
2. **Stock moshiko pt-BR probe + latency ceiling** — `phase0/spike_c_moshi/
   smoke_moshi.py` (Kyutai's own benchmark) → FD latency ceiling on our GPU +
   characterize pt-BR failure (accent/code-switch/PAD blowup).
3. **moshi-finetune pipeline proof** — run the official quick preset *unchanged*
   on ~1 h pt-BR stereo (build stereo via pyannote 3.1; `annotate.py --lang pt
   --whisper_model medium`). Goal = pipeline + loss-drop, LoRA-vs-CPT go/no-go.
4. **Qwen3-Omni hedge spike** — `phase0/spike_d_qwen3omni/` (heavy GPU: SDumont/
   A100-80G, NOT free Colab). pt-BR speech + emotion-via-prompt + latency.
5. **CSM voice probe** — `phase0/spike_b_csm/smoke_csm.py` (in-context clone of
   Pedro/carioca + pt-BR WER). Voice-layer data point.
6. **Cascade floor** — `phase0/spike_a_cascade/` yardstick.
7. **Decide spine** with the numbers → record in tech-stack + Dev KB → `/sdd`
   ATUALIZAR (also fold: codec=Mimi-frozen, CPT recipe, watermark-day-one,
   eval-harness-as-asset, fail-closed/quota) → `/feature-spec` Phase 1.

## Open questions now on the table (for the 2026-06-17 review)
- CPT compute budget for pt-BR Moshi (J-Moshi: 128×V100·36h pretrain — scale to
  SDumont GH200; pt-BR likely cheaper than JA). Quantify before committing.
- Where does stereo 2-party pt-BR conversational data come from at scale? (open
  is read-only/NC; in-house is ~12–16 h MVP, not "scale"). The real long pole.
- Voice-identity strategy: per-voice LoRA on Moshi-channel vs CSM-front cloning —
  decide after Spike B/C.
- pt-BR SER classifier: train our own (no good off-the-shelf for pt-BR prosody).
- Mimi-frozen vs light Mimi pt-BR fine-tune — decided by test #1.
- Watermarking method + where in the stack (codec vs post) — pick before any
  voice data is shipped/stored.

## Cross-doc honesty notes
- Dossier 30 Moshi-license = **wrong** (corrected here + in 30 header). Trust 00/13.
- Dossier 10 "LoRA path is real" = **too optimistic** for fluent pt-BR; corrected
  by 13/50 (CPT needed). 10 patched with a pointer.
- Qwen3-Omni pt *speech-output* coverage: "plausible, verify" across agents — not
  yet primary-source confirmed. Verify on the live Qwen3-Omni model card.
- All prices (dossier 40) are 2026 third-party-aggregated — verify official pages
  before quoting a client.
