# Dossier 50 — Speech-LM fine-tune recipes for pt-BR (web research, 2026-05-17)

> Autonomous web research (Pedro away). Most actionable doc. Pairs with dossier 10
> (recipe from cloned code) + 13 (J-Moshi: CPT not LoRA-only).

## 1. Language adaptation — the core fact
**Mimi is acoustic, language-agnostic** (24kHz→12.5Hz, 8 cb, cb0 semantic/WavLM-distilled). ⇒ **don't retrain the codec for pt-BR**; the gap is in the LM over tokens + the text/Inner-Monologue BPE (EN/FR-trained → pt-BR over-segmented but functional; `text_padding_weight` already down-weights it).
Ladder cheapest→strongest: **LoRA/QLoRA** (rank 64–128, `ft_embed:true`) = accent/voice/style + modest phonetic; low forgetting risk (base frozen). **Continued pretrain** (full FT, low LR) = needed if pt-BR truly OOD (Moshi en/fr-centric; CSM EN, "won't do well" non-EN) — forgetting bites ⇒ **replay 10–30% original-lang**, lr~2e-6, short schedule. **From-scratch on target only = never** (destroys the FD/conversational prior).
Hours: LoRA accent/style **5–50 h**; solid pt-BR intelligibility via CPT **low-hundreds–~1k h**; from scratch 10k h+ (don't). Curriculum: (a) transcribed read → fix phonetics → (b) TTS-style aligned single-spk → (c) conversational stereo for FD/turn-taking. Precedent: Spirit-LM (2402.05755), VoxtLM/SpeechGPT CPT, F5-TTS multilingual community finetunes incl. pt-BR with a few hundred h (2410.06885).

## 2. moshi-finetune in depth (matches dossier 10)
Data = **stereo WAV (L=Moshi, R=user)** + `.jsonl {path,duration}` + sibling `.json` word-timestamps. `annotate.py`: NOT full diarization — per-channel, 16kHz, **`whisper_timestamped` default `medium`** (code WARNS use medium not large-v3 for stereo; best_of=5,beam=5,temp-fallback), `keep_silence_in_segments`, writes `{"alignments":[[word,[s,e],"SPEAKER_MAIN"]]}`. SLURM-shardable (submitit, 6 CPU/task) ⇒ **SDumont-mappable**; **pass `--lang pt`**. Since channels pre-separated, "diarization" = per-channel ASR ⇒ **your pt-BR data must already be stereo Moshi-role/user-role split — producing that split is the real data-eng job (§7).**
Config: hf_repo moshiko-pytorch-bf16; lora rank128/scaling2.0/ft_embed false; first_codebook_weight_multiplier 100 (keep — up-weights semantic cb); text_padding_weight .5; duration_sec100/bs16/steps2000; lr2e-6/wd0.1/pct_start0.05; grad-ckpt; save_adapters. Tokens = steps×gpus×bs×dur×9×12.5. Compute: 1×H100 ≈12k tok/s @ **39.6GB** ⇒ fits one 80GB GPU; **NOT free-Colab T4/L4 at defaults**. OOM: bs↓ then dur↓ (shorter ⇒ model goes silent faster). Inference: `python -m moshi.server --lora-weight=…/lora.safetensors --config-path=…/config.json`.

## 3. Voice cloning by model
- **Moshi:** voice baked in base (moshiko M / moshika F), no clean in-context API ⇒ per-voice LoRA on that speaker's Moshi-channel, or full-FT. Long-dialogue consistency strong (voice in weights).
- **CSM-1B:** **native in-context cloning, excellent** — `context=[Segment(text,speaker,audio),…]`, tens of sec ref. Our **voice-clone component** (matches tech-stack). Long-dialogue drift = known failure ⇒ carry growing context / periodic re-anchor / per-voice LoRA stabilizes.
- **Qwen3-Omni:** fixed speaker set + system-prompt/reference; not arbitrary few-shot OOTB; pt in-distribution.
Few-shot reality: CSM ~30s–few min clean ref → recognizable; per-voice LoRA from ~10–60 min → stable. Always gate on consent (LGPD).

## 4. Emotion control FT
weakest→strongest: **reference-audio style** (zero labels, warm/enthusiastic nudge, weak intensity) < **discrete tags in text/Inner-Monologue stream** (`[emotion=empathetic;intensity=0.7]`, a few h/emotion works because acoustic codebooks already hold paralinguistic priors) < **latent embedding** (most plumbing, usually unnecessary now) < **RL/DPO** (Step-Audio 2 / 2507.16632; ParaS2S 2511.08723 — defer to Phase 3+, SFT-with-tags first). Phase-3 scheme (neutral/warm/enthusiastic/empathetic/sad/surprise+intensity): emotion-prompted directed recordings → tag in text stream + optional ref audio → LoRA, ~2–5 h/emotion across 2 voices.

## 5. Compute planning
| | Moshi-7B LoRA r128 | Moshi-7B full-FT | Qwen3-Omni-30B-A3B |
|---|---|---|---|
| GH200 96GB ✅ | easy (peak 39.6GB) | fits (bf16+ckpt, small bs) | LoRA fits; full tight |
| A100-80G ✅ | fits (default) | tight (bs/dur↓) | LoRA only |
| Free Colab T4/L4 ❌ | QLoRA smoke only | no | no |
| Colab Pro+ A100-40G ⚠️ | fits (bs/dur↓) | no | no |
QLoRA 4-bit: 7B≈5–6GB wts, loads on T4 but moshi-finetune is bf16/LoRA-native (not bitsandbytes-wired) ⇒ **pipeline-proof only**, real runs 80GB+. Qwen3-Omni 30B 4-bit ≈18–20GB ⇒ ≥A100-40G even QLoRA. Budget: quick LoRA proof (2000 steps) 1×80GB ≈ few hours; serious pt-BR CPT-LoRA ≈ 10s–100s GH200-h (within free SDumont). **Stage:** Colab QLoRA smoke → SDumont GH200 LoRA on open seed → SDumont CPT + per-voice/emotion LoRA → serve via Moshi Rust server on Inception/Colab/local (SDumont can't serve).

## 6. Eval harness (all OSS; resolves tech-stack open Q#5)
- WER round-trip: **faster-whisper large-v3** for *eval* (keep labeler=whisper-medium and judge distinct).
- Naturalness: **UTMOS** (sarulab UTMOS22) + **DNSMOS P.835**. **F5-TTS cloned repo ships `eval_utmos.py` + `ecapa_tdnn.py` — reuse.**
- Speaker-sim: ECAPA-TDNN cosine (SpeechBrain spkrec-ecapa-voxceleb) / WavLM-TDNN.
- Emotion: pt-BR wav2vec2/Whisper-encoder SER head fine-tuned on our labels (off-the-shelf EN SER won't transfer); report confusion matrix + per-class.
- Latency/RTF: time-to-first-audio-token, RTF, p50/p95 e2e vs 800ms; reuse `phase0/spike_a_cascade/cascade_latency.py`.
- FD metrics: turn latency, barge-in, overlap, %silence from silero-vad on both channels.
- Frozen bench: ~50–100 pt-BR utterances (carioca+neutral, read+spont, 6 emotions), versioned in `eval/`.
- Logging: moshi-finetune **native W&B** (`wandb:` YAML, `offline:true` for air-gapped SDumont → `wandb sync` later).

## 7. Data pipeline engineering
raw→trainable: acquire (open + in-house 24kHz) → **diarize+role-split** (the hard part: Moshi needs 2-ch Moshi-role vs user-role; **pyannote.audio 3.1** to get turns → synthesize stereo, A→left/Moshi, B→right/user; single-spk corpora → speech on Moshi ch, user ch silent) → transcribe+align (`annotate.py --lang pt --whisper_model medium`, OR **WhisperX** for faster batched word align, same `{"alignments":…}` schema) → segment ≤100s preserving turns → codec tokens (internal at train; offline via moshi `scripts/test_mimi.py`) → **emotion tagging at scale = the in-house labeler** (clip→emotion+intensity+accent+quality; weak SER pre-labels + human-correct active-learning loop).

## Staged recipe Phase0→3
- **P0** (days, Colab+1GPU): smoke_moshi/csm; download DailyTalkContiguous; run moshi-finetune quick preset unchanged on 1h pt-BR slice (pipeline+loss-drop proof); benchmark Moshi FD latency vs cascade floor; decide spine.
- **P1** (SDumont GH200): build stereo from open pt-BR; `annotate.py --lang pt` SLURM-sharded; LoRA r128 lr2e-6→4e-6 ft_embed:true, replay 10–20% en/fr; stand up WER-round-trip+UTMOS+latency harness w/ frozen pt-BR bench; W&B offline; baseline vs P0 ceiling.
- **P2** (2 voices): directed recordings (Pedro/carioca + hired F + consent); CSM in-context clone fast + per-voice LoRA stable; ECAPA cosine; weights→private registry.
- **P3** (emotion): emotion-prompted recordings labeled via in-house tool; LoRA emotion tags in text stream + ref audio; SER accuracy+confusion; DPO/Step-Audio-2 parked for later.

## Park (spend/accounts/license — DO NOT ACT)
HF gated accepts: meta-llama/Llama-3.2-1B (CSM dep), sesame/csm-1b, kyutai/moshiko + kyutai/mimi (CC-BY attribution), pyannote/speaker-diarization-3.1 (accept conditions+token). Qwen3-Omni Apache (no gate). Compliance: Sesame acceptable-use mirror, Moshi/Mimi attribution, Llama-3.2 license, **LGPD consent per cloned voice (blocks P2)**. Accounts/quota: **SDumont GH200 allocation (still pending — blocks P1 scale)**, Colab Pro+, NVIDIA Inception (+ live-serving box since SDumont can't serve), W&B (free/offline), private HF/bucket for "gold" weights (tech-stack open Q#3).

Reusable in tree: `research/repos/moshi-finetune/{README,annotate.py,example/moshi_7B.yaml,finetune/args.py}`; `research/repos/csm/{README,generator.py}`; **`research/repos/F5-TTS/src/f5_tts/eval/{eval_utmos.py,ecapa_tdnn.py}`** (reuse for eval); `phase0/`.
Sources: Moshi 2410.00037, J-Moshi 2506.02979, Spirit-LM 2402.05755, F5-TTS 2410.06885, Step-Audio2 2507.16632, ParaS2S 2511.08723; kyutai-labs/moshi-finetune; SesameAILabs/csm; QwenLM/Qwen3-Omni; pyannote 3.1; SYSTRAN/faster-whisper; m-bain/whisperX.
