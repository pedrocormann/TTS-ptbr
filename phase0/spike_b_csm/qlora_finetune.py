"""
QLoRA pt-BR fine-tune — HONEST SCAFFOLD, NOT TURNKEY.

Why this file is a scaffold and not a finished trainer:
  Sesame shipped CSM as INFERENCE ONLY. research/repos/csm has generator.py /
  models.py (Model.generate_frame, the autoregressive *sampling* primitive) but
  NO training forward, NO loss, NO train.py. Fine-tuning CSM is unsolved by
  Sesame. So this is Phase-0 research work, not a "run it" step.

The real path (pick one, validate in Phase 0):
  A) Adapt the OFFICIAL Kyutai recipe: research/repos/moshi-finetune/train.py
     — same Mimi codec, LoRA trainer, closest supported thing. Best bet.
  B) Community CSM LoRA (Speechmatics "finetuning Sesame on new languages/
     voices" blog; Unsloth-style 4-bit). Less official, documented.
  C) Reconstruct a training forward over CSM's 33-wide frame sequence
     (32 Mimi codebooks + 1 text slot) and a per-codebook CE loss. Most work.

This file gives the data→token scaffold (reusing CSM's exact tokenization from
generator.py) + the PEFT LoRA wrap, then STOPS at the training step with a
pointer. Do not pretend the TODO is done.

Run (after prep_ptbr_data.py):
  python qlora_finetune.py --csm-repo ../../research/repos/csm \
      --manifest data_ptbr/manifest.jsonl --dry-run
"""
import argparse, json, os, sys

os.environ.setdefault("NO_TORCH_COMPILE", "1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csm-repo", required=True)
    ap.add_argument("--manifest", required=True, help="from prep_ptbr_data.py")
    ap.add_argument("--moshi-finetune", default="../../research/repos/moshi-finetune",
                    help="OFFICIAL recipe to adapt (path A)")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--dry-run", action="store_true",
                    help="build model+data scaffold and stop before the unsolved trainer")
    args = ap.parse_args()

    sys.path.insert(0, args.csm_repo)
    import torch
    from generator import load_csm_1b, Segment  # reuse the REAL tokenization path

    gen = load_csm_1b(device="cuda")  # gives us model + Mimi + llama tokenizer
    model = gen._model               # the CSM backbone+decoder (inference-built)
    print(f"[ok] CSM loaded. sample_rate={gen.sample_rate}")

    # ---- data: reuse CSM's exact (T,33) frame scheme via the Generator internals ----
    # generator._tokenize_segment(Segment) -> (tokens[T,33], mask[T,33]) :
    #   text frame: tokenizer.encode(f"[{speaker}]{text}") in col -1
    #   audio frame: Mimi 32 codebooks in cols :-1  (+ EOS frame)
    def example_to_frames(text, wav_path):
        import torchaudio
        wav, sr = torchaudio.load(wav_path)
        wav = torchaudio.functional.resample(wav.mean(0), sr, gen.sample_rate)
        seg = Segment(text=text, speaker=0, audio=wav)
        toks, mask = gen._tokenize_segment(seg)   # <-- real CSM scheme, not reinvented
        return toks, mask

    rows = [json.loads(l) for l in open(args.manifest, encoding="utf-8")]
    print(f"[data] {len(rows)} pairs. Building 1 sample to validate the token path...")
    t, m = example_to_frames(rows[0]["text"], rows[0]["audio"])
    print(f"[data] sample frames shape={tuple(t.shape)} mask={tuple(m.shape)}  (expect (T,33))")

    # ---- LoRA wrap (PEFT) on the Llama backbone linears ----
    try:
        from peft import LoraConfig, get_peft_model
        cfg = LoraConfig(
            r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"],
            bias="none", task_type="FEATURE_EXTRACTION",
        )
        # NOTE: model is CSM's custom Model (Llama backbone + audio decoder), not a
        # HF CausalLM. get_peft_model may need a target submodule (model.backbone).
        # This line is the integration point to validate in Phase 0:
        peft_model = get_peft_model(model, cfg)  # TODO[A]: may require model.backbone
        peft_model.print_trainable_parameters()
    except Exception as e:
        print(f"[scaffold] PEFT wrap is an integration TODO: {e}")

    if args.dry_run:
        print(
            "\n[STOP — scaffold boundary]\n"
            "The training forward + per-codebook loss over the (T,33) frames is the\n"
            "unsolved part (CSM ships no trainer). Do NOT fake it. Next action:\n"
            f"  1. Read {args.moshi_finetune}/train.py (official LoRA recipe, same Mimi).\n"
            "  2. Map CSM's 33-wide frame to that loop's targets (32 codebooks + text).\n"
            "  3. Start at lora_r=16, the TTS-Portuguese single voice, QLoRA 4-bit on Colab.\n"
            "  4. Metric: does pt-BR WER (smoke_csm.py) drop materially vs no-FT baseline?\n"
            "Record the answer in ../../specs/tech-stack.md + Dev KB."
        )
        return

    raise NotImplementedError(
        "Training loop intentionally not stubbed as 'done'. Adapt moshi-finetune/"
        "train.py (path A) — see the dry-run notes."
    )


if __name__ == "__main__":
    main()
