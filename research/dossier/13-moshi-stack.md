# Dossier 13 — Moshi stack deep technical (web research, 2026-05-17)

> Autonomous research pass (Pedro away). Primary-source, [V]=verified [C]=community
> [I]=inferred. The single most important new finding: **J-Moshi** (the only
> rigorous non-EN/FR Moshi adaptation) → the pt-BR recipe is **continued-pretrain
> + tokenizer/embedding swap + stereo finetune**, NOT LoRA-only; **Mimi freezes**.

---

## 1. Moshi architecture (arXiv 2410.00037v2)

RQ-Transformer = Temporal Transformer (Helium 7B: 32L, d=4096, 32 heads, RoPE,
4096 ctx, runs @12.5 Hz) + small Depth Transformer (6L, d=1024, per-codebook
linear weights, predicts 8 Mimi codebooks within a frame). Big-slow + tiny-fast
factorization = real-time per-frame gen. Helium pretrained on 2.1T text tokens
(text competence is the spine even pre-audio).

**Inner Monologue**: time-aligned text token stream as a *prefix* to Moshi's own
audio tokens, aligned to 12.5 Hz via Whisper word timestamps; ~65% PAD (EN) +
EPAD boundary markers. **Delay is configurable & directional**: audio-ahead-of-
text ⇒ streaming ASR mode; text-ahead-of-audio ⇒ streaming TTS (text plans
speech). In dialogue, Moshi's text leads its own audio slightly ⇒ that is the
content-controllability lever. Ablation: Inner Monologue has "one of the most
critical impacts on quality" — short/removed ⇒ linguistic collapse. (So "text is
parallel" yes, but it is the highest-leverage quality knob — keep it.)

**Dual-stream full-duplex**: jointly models its own + the user's audio as parallel
token streams, no turn boundaries — always listening, can backchannel/interrupt.
Structural reason it beats TTS+VAD for emotional dialogue.

**Mimi**: 24 kHz mono, 12.5 Hz frame (80 ms), 1.1 kbps, **8 codebooks**. Split-RVQ:
cb0 = semantic (WavLM-distilled), cb1–7 = acoustic RVQ. SeaNet + causal conv +
8L/512d transformer bottleneck, fully streaming. (CSM uses a larger 32-codebook
setup — Moshi/Mimi is the lean design ⇒ cheaper Depth Transformer + VRAM.)

**Training stages**: Helium text 2.1T → audio pretrain **7M h** unsupervised ~1M
steps → multistream post-train (PyAnnote diarization, ~100k steps) → Fisher 2000h
(~10k) → instruct on 20k+ h synthetic TTS (~30k). Voice/persona/safety set in 4–5.

**Latency**: theoretical 160 ms, practical ~200 ms (80 ms Mimi frame + acoustic
delay + compute). Inference single GPU (L4-class ok); finetune H100-class.

## 2. moshi-finetune (official LoRA) — matches our code read (dossier 10)

Stereo wav (L=Moshi, R=user) + timestamped json + jsonl. `annotate.py` =
PyAnnote diarization → main/residual split → timestamped transcription, SLURM-
shardable. LoRA rank 128 / scaling 2.0 / `ft_embed` (full-train embeddings —
**essential for a new language**) / duration_sec 100 / bs 16 / 2k steps / lr 2e-6.
1×H100 ≈12k tok/s @ 39.6 GB. No official non-EN path documented.

## 3. Siblings / ecosystem

- **Hibiki**: streaming speech translation, FR→EN only, CC-BY-4.0.
- **delayed-streams-modeling (DSM)**: Kyutai **STT** (`stt-1b-en_fr` 0.5s, `stt-2.6b-en` 2.5s) + **TTS** (`tts-1.6b-en_fr`, ~220 ms, 2.5M h). EN/FR only. Code MIT/Apache, weights CC-BY-4.0.
- **Unmute**: cascaded STT→LLM→TTS on DSM (not the e2e model) — a fallback arch.
- **Kyutai TTS / Pocket-TTS**: voice cloning from ~10–20 s + voice blending — relevant for pt-BR voice identity (Moshi itself ships ONE fixed voice).
- Backends: PyTorch (research), Rust server (~400 streams/H100 [C]), MLX (Apple), rustymimi/Candle quantized.
- Licenses: Moshi & Mimi weights **CC-BY-4.0**, code Apache/MIT — re-verify per repo at ship.

## 4. pt-BR reality — J-Moshi is the template (arXiv 2506.02979) ★

Moshi is English-centric (Helium mostly EN; 7M h + Fisher = US EN; instruct EN).
**No public pt-BR Moshi exists** (absence-verified) → greenfield.

**J-Moshi (Japanese), the proof:** method = **continued pretraining, not LoRA**.
Pretrain ~60k h Japanese (J-CHAT/~69k h corpus) → finetune **344 h real stereo +
602 h synthetic = 946 h**. Reuse decisions (gold for us):
- **Mimi FROZEN** — resynthesizes Japanese acceptably with no retrain ⇒ strong
  signal **Mimi handles pt-BR phonetics frozen** (a ~1-day test to confirm).
- Helium/RQ-Transformer weights kept, but **SentencePiece tokenizer swapped** +
  **text embeddings re-init** in both Temporal & Depth Transformers.
- Compute: pretrain 128×V100-32G / 36 h; finetune 16×V100 / 2 h.
- Failure modes: naturalness/perplexity ~1 pt below resynthesis ceiling; **PAD
  ratio 88% JA vs 65% EN** (phoneme density) ⇒ PAD-loss reweighting needed.
- **pt-BR should be EASIER than Japanese** (Latin script, structurally closer to
  EN) ⇒ J-Moshi is a conservative upper bound on effort.
- Fork to use: `nu-dialogue/moshi-finetune` + `nu-dialogue/j-moshi`.

## 5. Limitations / open problems (commercial emotional pt-BR)

- Content control only via Inner-Monologue steering; instruct layer weak.
- **No explicit emotion conditioning** — emotion entangled in the one learned
  voice ⇒ must be induced via curated finetune data (+ possibly RL, dossier 30).
- Ships **one fixed voice** "to avoid impersonation" — no native cloning; pt-BR
  brand voices must be fine-tuned in OR fronted with Kyutai-TTS-style cloning.
- Helium 7B-class hallucination; "research only" card; mid-range toxicity, no
  pt-BR safety tuning. Watermarking described in paper — verify it ships.

## 6. Implications + revised Phase-0 (supersedes dossier-10's "LoRA path")

Moshi remains the right bet (audio spine, ablatable monologue, true FD, CC-BY,
J-Moshi proves transfer). **Realistic path = continued-pretrain + tokenizer/
embedding swap + stereo finetune, NOT LoRA-only.** Mimi almost certainly transfers
frozen (verify first).

Phase-0 (no spend; 1×H100/A100-80G or SDumont GH200):
1. **Mimi pt-BR round-trip test** — 30 min pt-BR → Mimi encode→decode → WER/UTMOS
   vs original. If ok ⇒ freeze Mimi (mirrors J-Moshi). *1-day, decisive.*
2. **Stock moshiko pt-BR probe** — characterize failure (accent, code-switch, PAD).
3. **LoRA smoke** — 5–20 h pt-BR stereo via `annotate.py` (pt Whisper), rank 128,
   `ft_embed:true`, 2k steps. Goal = pipeline validation + LoRA-vs-CPT go/no-go.
4. **Plan data scale** — target ≥300 h real stereo pt-BR + synthetic for finetune;
   continued-pretrain budget per J-Moshi (scaled down, pt easier). North-star
   metric = pt-BR dialogue-continuation perplexity + human naturalness vs Mimi
   resynthesis ceiling (J-Moshi protocol ⇒ comparable numbers).

Sources: arXiv 2410.00037v2; kyutai-labs/moshi, /moshi-finetune, /hibiki,
/delayed-streams-modeling; J-Moshi arXiv 2506.02979 + nu-dialogue/j-moshi;
HF kyutai/moshiko-pytorch-bf16, tts-1.6b-en_fr. Re-verify at ship: per-repo
license, watermarker presence, annotate.py model versions.
