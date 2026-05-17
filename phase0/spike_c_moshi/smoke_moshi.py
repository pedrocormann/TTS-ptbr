"""
Spike C smoke — Moshi (the spine bet). Measures the FULL-DUPLEX LATENCY CEILING
on our GPU by running Kyutai's OWN benchmark (research/repos/moshi/scripts/
moshi_benchmark.py), which uses the real loaders.CheckpointInfo + LMGen path.

We deliberately do NOT reimplement Moshi inference — Kyutai ships a proven
benchmark; reimplementing it would just add bugs. This wraps it, echoes its
numbers, and frames the go/no-go + the official pt-BR LoRA handoff.

Run (Colab/CUDA box):
  python smoke_moshi.py --moshi-repo /content/moshi \
      --hf-repo kyutai/moshiko-pytorch-bf16 --steps 125
( 125 steps @ 12.5 Hz ≈ 10 s of audio )
"""
import argparse, os, subprocess, sys, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moshi-repo", required=True, help="path to research/repos/moshi (or a clone)")
    ap.add_argument("--hf-repo", default="kyutai/moshiko-pytorch-bf16",
                    help="kyutai/moshiko-pytorch-bf16 (M) or kyutai/moshika-pytorch-bf16 (F)")
    ap.add_argument("--steps", type=int, default=125)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    bench = os.path.join(args.moshi_repo, "scripts", "moshi_benchmark.py")
    if not os.path.isfile(bench):
        sys.exit(f"[FATAL] not found: {bench}\n>> clone github.com/kyutai-labs/moshi first.")

    cmd = [sys.executable, bench, "--hf-repo", args.hf_repo,
           "--steps", str(args.steps), "--device", args.device]
    print(f"[run] {' '.join(cmd)}\n      (downloads ~7B Moshiko on first run; needs CUDA)\n")

    t0 = time.perf_counter()
    # Stream Kyutai's benchmark output verbatim — it prints per-step + summary timing.
    proc = subprocess.run(cmd, cwd=args.moshi_repo)
    wall = time.perf_counter() - t0

    print("\n================ SPIKE C — GO/NO-GO ================")
    if proc.returncode != 0:
        print("benchmark FAILED (returncode "
              f"{proc.returncode}). Common causes: no CUDA, OOM (need ~16GB for "
              "7B bf16), or HF download blocked. Fix and re-run.")
        print("====================================================")
        sys.exit(proc.returncode)
    print(f"model              : {args.hf_repo}")
    print(f"steps              : {args.steps}  (@12.5 Hz ≈ {args.steps/12.5:.1f}s audio)")
    print(f"wall (incl. load)  : {wall:.1f}s  (per-step latency = see Kyutai output above)")
    print("READ the per-step ms above: that is the full-duplex LATENCY CEILING on")
    print("this GPU. Paper claims ~200ms practical on an L4. Record it in")
    print("../../specs/tech-stack.md + Dev KB.")
    print("--- next: pt-BR is the real work ---")
    print("Stock Moshi is EN/FR. pt-BR via the OFFICIAL recipe:")
    print("  research/repos/moshi-finetune (LoRA) — tutorials/moshi_finetune.ipynb")
    print("  + example/moshi_7B.yaml. Metric: pt-BR WER drop while FD/Inner-")
    print("  Monologue is preserved. Do NOT hand-roll a trainer; Kyutai ships one.")
    print("====================================================")


if __name__ == "__main__":
    main()
