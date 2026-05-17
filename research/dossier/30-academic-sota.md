# Dossier 30 — Academic SOTA: emotional/full-duplex conversational speech (2024-2026)

> Autonomous web research (Pedro away). ⚠️ **License claim in this agent's output
> is WRONG and has been corrected.** It reported Moshi weights = CC-BY-NC-SA. The
> source of truth (cloned `research/repos/moshi/README.md` L86/L277, verbatim
> *"The weights for the models are released under the CC-BY 4.0 license"*) ⇒
> **Moshi weights = CC-BY-4.0, commercial OK with attribution.** Wherever this
> doc says "CC-BY-NC-SA??" for Moshi, read **CC-BY-4.0**. See 00-SYNTHESIS.
> Everything else in this dossier stands.

## 1. Speech-to-speech / dialogue LMs

Field split: **time-multiplexed/turn-based** (majority, GPT-4o-like) vs **true
parallel-stream full-duplex** (Moshi = only production-grade open one). Survey:
*From Turn-Taking to Synchronous Dialogue* (arXiv 2509.14515).

| Model | Arch | Duplex | Emotion | Latency | License | pt |
|---|---|---|---|---|---|---|
| **Moshi** (2410.00037) | RQ-Transf (Helium 7B)+Mimi, dual stream + Inner Monologue | **true FD parallel** | implicit, 70+ styles | 160/200ms | **CC-BY-NC-SA?? (CONFLICT)** | EN only |
| GLM-4-Voice (2412.02612) | interleaved speech-text | turn | weak | ~sub-s | Apache-ish | Zh/En |
| LLaMA-Omni2 (2505.02625) | Qwen2.5+AR streaming decoder | turn | limited | low | non-comm weights | En/Zh |
| Freeze-Omni (2411.00774) | frozen LLM+adapters | soft duplex | limited | sentence | open | En/Zh |
| Mini-Omni2 (2410.11190) | parallel text+audio | pseudo | weak | low | MIT | En |
| Kimi-Audio (2504.18425) | 12.5Hz tok, flow-match detok, 13M h | turn | good | streaming | open | Zh/En |
| **Qwen3-Omni** (2509.17765) | Thinker-Talker MoE 30B-A3B, Code2Wav | turn, streaming | multi-cb paraling | **234ms** first-packet | **Apache-2.0** ✅ | 119 text/10 spoken (verify pt) |
| **Step-Audio 2** (2507.16632) | frozen enc + CosyVoice2 tok, CoT+RL | turn | **best explicit+RL paraling** | n/r | "mini" open | En/Zh/Ja/Ar |
| Voila/SALMONN-omni/NTPP (2025) | synchronous SLM / codec-free | FD (research) | varies | low | research | En |

**Read:** Moshi = correct *architecture* reference (only verified true-FD open). EN-only + license-uncertain ⇒ replicate the architecture, not necessarily the weights. **Qwen3-Omni (Apache-2.0, multilingual)** = strongest commercially-clean base if we accept turn-based+fast-barge-in. **Step-Audio 2** = study for emotion/paralinguistics.

## 2. Neural codecs (THE foundational choice)

Decisive axis = frame-rate × semantic content × streaming-causality, NOT raw fidelity.

| Codec | Frame | Semantic? | Streaming | Note |
|---|---|---|---|---|
| **Mimi** (2410.00037) | **12.5 Hz** | **yes (WavLM-distilled RVQ-0)** split-RVQ | **yes 80ms** | the reference choice |
| EnCodec/DAC/SoundStream | 75–86 Hz | no | yes/semi | too high frame-rate for AR LM (DAC = recon trap) |
| SNAC (2410.14411) | multi-scale | no | yes | variable-rate, good q/bitrate |
| WavTokenizer (2408.16532) | 40–75 Hz single-VQ | partial | yes | single-codebook simplicity |
| X-Codec2 (2502.04128) | 50 Hz single-VQ | **yes unified** | yes | strong for single-stream LMs (Llasa) |
| DualCodec (2505.13000) | low | **yes semantic-enh** | yes | targets low-frame-rate gen |
| U-Codec/FlexiCodec/TS3 (2025) | **5 Hz**/dyn | yes | yes | frontier: 5Hz≈50Hz intelligibility |

**Decision: clone the Mimi recipe** (split-RVQ, WavLM-distilled *causal* semantic RVQ-0, 12.5 Hz, ~8 codebooks) or fine-tune Mimi on pt-BR. Sequence length, not fidelity, governs real-time. (J-Moshi evidence in dossier 13: Mimi likely **freezes** for pt-BR.)

## 3. Emotion / expressivity control
3 families: implicit (audio-context/latent — Moshi: most natural, least controllable), explicit (tags/embeddings/ref/NL-style-prompt — Step-Audio 2: controllable, can sound pasted), **RL for paralinguistics (2025 step-change)**. **Step-Audio 2: 83.09% paralinguistic accuracy vs GPT-4o Audio 43.45% (~2×)** via CoT-conciseness reward → reward model → GRPO. Corroborated: ParaS2S (2511.08723, waveform-level RL), EMO-RL, "Frozen LLMs perceive paralinguistics" (Interspeech 2025). **Best-method-2026: implicit base + NL style prompt + light paralinguistic-RL pass.** Pure tag-conditioning is dated.

## 4. Full-duplex & turn-taking
parallel-stream (Moshi/dGSLM: turn-taking emergent, no VAD) vs VAD-turn (legacy, high latency) vs predictive (SyncLLM, *Chronological Thinking* 2510.05150). Survey gap: behavioral arbitration 54–86% vs 94% human; **inverse latency↔coherence correlation** (pushing latency down degrades coherence). Metrics to build: **Full-Duplex-Bench** (2503.04721) + v1.5 (2507.23159: interruption/backchannel/overlap, stop & response latency) + v2 (2510.07838: SLM examiner). Headline numbers = stop-latency + response-latency.

## 5. Evaluation methodology
Stack: UTMOS (2204.02152)+DNSMOS (2010.15258) automatic naturalness gates (weak on *emotional* quality); WER/CER round-trip (content); **URO-Bench** (2502.17810: first S2S bench w/ multiling+multi-turn+paralinguistics — adopt as primary); Full-Duplex-Bench v1.5; pt-BR SER classifier for emotion; periodic human CMOS. Security: RVCBench (2602.00443), Fake-Voice-Detection (2510.06544). **No pt-BR conv-S2S benchmark exists — owning one is a strategic asset.**

## 6. Voice cloning / consistency
weakest→strongest: speaker-embedding < per-speaker FT < **in-context (reference-audio prefix)** (dominant 2025, few-shot from short clip; Moshi/Qwen3-Omni multi-codebook do implicitly). Open problem: **speaker drift over long dialogue** (under-measured — instrument ourselves). Voice Cloning Survey 2505.00579. **Watermark from day one**: AudioSeal (2401.17264), VoiceMark (2505.21568), SafeSpeech (2504.09839). Sobering: fake-voice detectors are LOSING the arms race (2510.06544) ⇒ proactive watermarking is the only credible consent/anti-spoof posture.

## 8 decision-relevant takeaways
1. **Clone Moshi's parallel-stream + Inner-Monologue architecture** (only verified true-FD open). Don't rely on Moshi *weights* (EN-only, license-uncertain).
2. **Codec = the foundational decision: adopt the Mimi recipe** (12.5Hz, split-RVQ, WavLM-distilled causal semantic). Avoid DAC/EnCodec high-frame-rate.
3. **Emotion: implicit base + NL style prompt + light paralinguistic-RL** (Step-Audio 2 verified ~2× GPT-4o — RL is the 2026 right answer for *controllable* emotion).
4. **Qwen3-Omni (Apache-2.0)** = license-clean broadly-multilingual fallback base if true parallel-stream proves too costly (accept fast-barge-in turn-based v1 → evolve).
5. **Build the pt-BR eval harness now**: URO-Bench-style + Full-Duplex-Bench v1.5 + UTMOS/DNSMOS + WER round-trip + pt-BR SER. Owning the pt-BR benchmark = strategic asset.
6. **Watermark from day one** (AudioSeal/VoiceMark baked into codec/vocoder) — detection is being lost; aligns with ANPD/LGPD 2026 (dossier 40).
7. Open problems we'll hit: synchronized dual-channel spontaneous pt-BR data (binding constraint); latency↔coherence inverse tradeoff (~200ms target has a coherence tax); speaker drift over long dialogue (instrument it).
8. **Build sequence:** pt-BR Mimi-style codec (or freeze Mimi) → text/speech-interleaved pretrain for semantic grounding → dual-stream FD finetune on (scarce) 2-channel pt-BR dialogue → paralinguistic RL → watermark+eval harness in parallel.

Sources: Moshi 2410.00037, Step-Audio2 2507.16632, Qwen3-Omni 2509.17765, Kimi-Audio 2504.18425, LLaMA-Omni2 2505.02625, FD survey 2509.14515, SNAC 2410.14411, DualCodec 2505.13000, U-Codec 2510.16718, Full-Duplex-Bench 2503.04721/2507.23159/2510.07838, URO-Bench 2502.17810, Voice-Clone survey 2505.00579, AudioSeal 2401.17264, VoiceMark 2505.21568, fake-voice arms race 2510.06544, ParaS2S 2511.08723.
