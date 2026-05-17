# Spike D — Qwen3-Omni (pragmatic pt-BR co-bet)

The commercially-clean, **native-pt** spine candidate. Apache-2.0, Thinker-Talker
speech-to-speech, multilingual incl. Portuguese speech I/O, emotion via prompt,
fine-tunable. Near-full-duplex (streaming turn-taking, not Moshi's parallel-stream).

## Decisive metric (go/no-go)
pt-BR **emotional expressivity preference** in dialogue (blind vs Moshi/CSM) +
**turn latency**. Does native pt + prompt-steered emotion beat adapting Moshi?

## ⚠️ Compute reality (honest — read before running)
`Qwen/Qwen3-Omni-30B-A3B-Instruct` is **MoE 30B total / 3B active**. All experts
load in bf16 ⇒ **~60-70 GB VRAM**. This does **NOT** fit free/Pro Colab. Run on:
- **SDumont GH200** (Grace Hopper, unified memory — ideal) or
- **NVIDIA Inception** A100-80G / H100.
Check for an FP8 / smaller Qwen-Omni variant to halve it; otherwise this spike is
the SDumont/Inception job, not the weekly Colab one. Don't pretend otherwise.

## What's here
- `smoke_qwen3omni.py` — honest scaffold following the HF model-card API
  (`Qwen3OmniMoeForConditionalGeneration` + processor + `process_mm_info`,
  speech output via the Talker). pt-BR prompt + emotion via system prompt +
  latency. **API may drift — verify against the live model card on first run.**

## Run order
1. On SDumont/Inception (≥70 GB GPU), `pip install` transformers + qwen-omni-utils.
2. `python smoke_qwen3omni.py` → pt-BR speech out + emotion-styled variants + latency.
3. Record vs Moshi ceiling (Spike C) and cascade floor (Spike A) in tech-stack + Dev KB.

License: Apache-2.0 (clean for product) — its main edge over Moshi (CC-BY attribution)
and the reason it's the pragmatic co-bet.
