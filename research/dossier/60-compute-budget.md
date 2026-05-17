# Dossier 60 — pt-BR Moshi compute & cost budget (web research, 2026-05-17)

> Autonomous pass. All arithmetic from primary sources. Bottom line: **finetune
> is trivially cheap (~6–20 GH200-h, <US$60, <1 day); heavy CPT (~920–1,540
> GH200-h) is the ONLY expensive item and is PROBABLY SKIPPABLE for pt-BR.**

## J-Moshi reference (arXiv 2506.02979, verbatim)
- CPT: ~60k h JA, **128×V100-32GB, 36 h**, batch 512, 8,880 steps, LR 3e-5.
- FT: 344 h real + 602 h synth stereo, **16×V100, 2 h**, batch 16, ~1.4–2.4k steps.
  Mimi frozen; JA tokenizer swap + text-embedding re-init.
- Raw: CPT = 4,608 V100-h; FT = 32 V100-h.

## V100 → modern (GH200/H100 ≈ same Hopper die, 989 vs ~125 TFLOPS ≈ 7.9× raw;
use 3–5× effective derate for a 7B + tiny Depth Transformer)
- **CPT: ~920–1,540 GH200-h** (~1,150 center). 1 node (4×GH200) ≈ 240–400 h;
  8 nodes (32×) ≈ 30–48 h.
- **FT: ~6–11 GH200-h** → <3 h on one node. A100-80G ≈ 1.6× slower.

## The CPT-vs-LoRA boundary (the key strategic finding)
pt-BR is materially easier than JA: Latin script, Helium-7B already EN/EU-text-
heavy ⇒ **no tokenizer swap / embedding re-init strictly required** — that is the
single thing that FORCED J-Moshi's heavy CPT. So:
- **SKIP heavy CPT (optimistic) plausible if:** keep Helium tokenizer, synthetic
  pt-BR for acoustic adaptation, frozen Mimi, accept LoRA r128 re-aligns text↔
  semantic for a close Latin language.
- **CPT unavoidable if:** tokenizer swapped, OR post-FT eval shows English-leaning
  phonotactics / broken pt-BR turn-taking. Then **light CPT (~2–4k h, 600–1,200
  steps ≈ 150–350 GH200-h)**, not 60k.
- The proposed 300–600 h is **finetune-scale, not CPT-scale** ⇒ LoRA-only is the
  right first bet; CPT is the fallback.

## 3 scenarios
| | S Shoestring | M SDumont LoRA | L Full CPT+FT |
|---|---|---|---|
| HW | Colab Pro+ A100-40G | 1 GH200 node (4×) | 4–8 GH200 nodes |
| Recipe | QLoRA r64–128, ~500 steps | LoRA r128, 2k steps (defaults) | CPT 600–8,880 + FT |
| GPU-h | ~15–30 A100-h | **~6–20 GH200-h** | CPT 920–1,540 + FT ~10 |
| Wall | 1–2 Colab sessions | **<1 day** | 240–400 h/1node or 30–48 h/8 |
| SDumont free? | n/a | yes (trivial UA) | yes if allocated |
| Inception US$ | self-funded | **~US$60** | **~US$3.5–5k** |
**Do M regardless** (≈free / US$60). M→L gated by **native-speaker human eval**, not metrics.

## SDumont specifics
GH200 node = 4×GH200 (96 GB HBM3) + 4×Grace ARM (72c) + 480 GB RAM, 36 nodes.
**1 UA = 1 CPU-core-hour**; Standard 750k–7.49M UA, Premium ≥7.5M, Edu ≤150k.
**No published GPU→UA conversion — confirm with helpdesk-sdumont@lncc.br before
sizing the proposal.** A Standard grant covers S+M+L. Air-gapped ⇒ `WANDB_MODE=
offline`, pre-stage weights/data/wheels to `$SCRATCH`, checkpoint every 200–500
steps, resume-on-requeue (`--requeue`), design for SLURM preemption.

## Memory math
LoRA r128 = **39.6 GB / 1×H100** (moshi-finetune README, ≈12k tok/s). Full
CPT (7B bf16 Adam grad-ckpt) ≈ params 14 + Adam 56 + grads 14 ≈ **~84 GB** →
fits 1×GH200 tight; **FSDP/ZeRO-2 across 4 GH200 ⇒ ~25–30 GB/GPU** (recommended).

## Staged plan + gates
- **P0 Colab:** moshi-finetune e2e on EN + ~10 h synth pt-BR, QLoRA r64 ~300 steps. Gate: loss↓ + intelligible.
- **P1 SDumont M (or US$60):** ~300 h pt-BR, LoRA r128, 2k steps, Helium tokenizer kept, <1 day. **Gate (decisive): native-speaker naturalness + turn-taking eval. PASS ⇒ ship LoRA, CPT abandoned.**
- **P2 Light CPT (only if P1 fails):** ~2–4k h, 600–1,200 steps (~150–350 GH200-h), re-run P1 FT.
- **P3 Full CPT (last resort, ≈tokenizer swap needed):** J-Moshi-scale, multi-node FSDP, Standard allocation.
Escalation: S→M automatic (free). **M→L gated by human eval, not convergence.**

## Park (spend/allocation/accounts)
SDumont Standard proposal (≥750k UA covers all; **critical-path blocker**);
confirm GPU→UA w/ helpdesk-sdumont@lncc.br; Inception fallback (~US$60 M / ~US$3.5–5k L);
Colab Pro+ (P0); pt-BR multi-stream TTS for synth (the real bottleneck, not GPUs);
W&B offline (free).

Sources: J-Moshi arXiv 2506.02979 + nu-dialogue/j-moshi; moshi-finetune README;
NVIDIA Hopper / GH200 spec; A100-vs-H100 TFLOPS; SDumont machine.php + call.php.
