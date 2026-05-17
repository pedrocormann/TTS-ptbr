# Spike C — Moshi (★ the spine bet)

The architecturally-correct bet: true full-duplex, text = **parallel** Inner
Monologue (ablatable), not the spine. Verified in `../RETHINK.md`.

## Decisive metrics (go/no-go)
1. **Real full-duplex latency on our GPU** — the ceiling every other path chases.
   Moshi's paper claims ~200ms on an L4; measure it on the GPU we actually have.
2. **pt-BR adaptation viability** — stock Moshi is EN/FR (known). The real test:
   after a small LoRA via the OFFICIAL `moshi-finetune`, does pt-BR speech become
   intelligible (WER) while keeping full-duplex + Inner-Monologue behaviour?

## What runs (verified vs research/repos/moshi real API)
- `smoke_moshi.py` — wraps the repo's own `scripts/moshi_benchmark.py`
  (`loaders.CheckpointInfo.from_hf_repo` + `LMGen`, `--steps`, `--hf-repo`,
  `--device`). Prints the per-step + total latency ceiling. **Runnable on Colab**
  (Moshiko 7B bf16 fits L4 24GB / A100).
- `colab.ipynb` — clone moshi, install, run the benchmark, then hand off to the
  official pt-BR LoRA path.
- pt-BR fine-tune = **official** `research/repos/moshi-finetune` (LoRA, has its own
  Colab `tutorials/moshi_finetune.ipynb` + `example/moshi_7B.yaml`). We do NOT
  reinvent a trainer here — Kyutai ships one. That is the strength vs CSM.

## Prereqs (real)
- CUDA GPU. HF model `kyutai/moshiko-pytorch-bf16` (male) or
  `kyutai/moshika-pytorch-bf16` (female). CC-BY-4.0 (attribution required).
- `pip install moshi` (PyPI) OR run from the cloned repo.
- The interactive duplex demo (`python -m moshi.server`) needs a mic/browser —
  NOT used for the smoke; the smoke is the non-interactive benchmark.

## Run order
1. `colab.ipynb`: clone moshi + `pip install moshi sphn` + run benchmark.
2. `smoke_moshi.py --hf-repo kyutai/moshiko-pytorch-bf16 --steps 125` →
   latency ceiling number (125 steps ≈ 10 s of audio at 12.5 Hz).
3. Record the ceiling in `../../specs/tech-stack.md` + Dev KB.
4. pt-BR LoRA: follow `research/repos/moshi-finetune` (official Colab) on a small
   pt-BR conversational set. Metric: pt-BR WER drop + FD preserved.
5. Compare ceiling vs Spike A (cascade floor) vs Spike D (Qwen3-Omni).

License note: Moshi weights CC-BY-4.0 → attribute Kyutai in any product that ships them.
