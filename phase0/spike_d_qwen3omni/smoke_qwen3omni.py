"""
Spike D smoke — Qwen3-Omni (pt-BR co-bet). HONEST SCAFFOLD.

Follows the documented HF model-card API for Qwen3-Omni-30B-A3B-Instruct
(Qwen3OmniMoeForConditionalGeneration + processor + qwen_omni_utils, speech
output via the Talker). The model-card API CAN drift — verify on first run
against huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct.

⚠️ NEEDS ~60-70 GB VRAM (MoE 30B/3B-active, all experts bf16). NOT free Colab.
Run on SDumont GH200 or Inception A100-80G/H100. See README.

Run:
  pip install -U "transformers>=4.57" accelerate qwen-omni-utils soundfile
  python smoke_qwen3omni.py
"""
import argparse, time


PT_PROMPTS = [
    ("neutro", "Bom dia. Bem-vindo. Como posso ajudar você hoje?"),
    ("caloroso/acolhedor", "Que alegria te ver por aqui! Fica à vontade, tá?"),
    ("entusiasmado", "Isso é incrível! Você vai adorar o que preparamos!"),
    ("empático", "Eu entendo, isso é chato mesmo. Vamos resolver juntos, com calma."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-Omni-30B-A3B-Instruct")
    ap.add_argument("--speaker", default="Ethan", help="talker voice id per model card")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()

    import os, torch, soundfile as sf
    os.makedirs(args.out_dir, exist_ok=True)
    try:
        from transformers import (Qwen3OmniMoeForConditionalGeneration,
                                  Qwen3OmniMoeProcessor)
        from qwen_omni_utils import process_mm_info  # noqa
    except Exception as e:
        raise SystemExit(
            f"[FATAL] Qwen3-Omni classes not importable: {e}\n"
            ">> pip install -U 'transformers>=4.57' accelerate qwen-omni-utils\n"
            ">> and verify the class names on the live model card (API may have drifted)."
        )

    print(f"[load] {args.model}  (~60-70GB — must be SDumont/A100-80G, not Colab)")
    model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
        args.model, torch_dtype="auto", device_map="auto")
    proc = Qwen3OmniMoeProcessor.from_pretrained(args.model)

    results = []
    for tag, line in PT_PROMPTS:
        # emotion steered via system prompt (Qwen-Omni has no emotion tags; prompt is the knob)
        conv = [
            {"role": "system", "content": [{"type": "text",
             "text": f"Você é uma voz brasileira. Fale em pt-BR com tom {tag}."}]},
            {"role": "user", "content": [{"type": "text", "text": line}]},
        ]
        text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conv, use_audio_in_video=False)
        inputs = proc(text=text, audio=audios, images=images, videos=videos,
                      return_tensors="pt", padding=True).to(model.device)

        torch.cuda.synchronize()
        t0 = time.perf_counter()
        out = model.generate(**inputs, speaker=args.speaker,
                              thinker_max_new_tokens=256, return_audio=True)
        torch.cuda.synchronize()
        dt = time.perf_counter() - t0

        # out audio extraction follows the model card; verify the attribute name.
        wav = getattr(out, "audio", None)
        path = f"{args.out_dir}/qwen_{tag.split('/')[0]}.wav"
        if wav is not None:
            sf.write(path, wav.reshape(-1).detach().cpu().numpy(), 24000)
        results.append((tag, dt, path if wav is not None else "NO AUDIO (check API)"))
        print(f"  [{tag}] {dt:.2f}s -> {results[-1][2]}")

    print("\n================ SPIKE D — GO/NO-GO ================")
    print(f"model   : {args.model} (Apache-2.0)")
    for tag, dt, path in results:
        print(f"  {tag:<20} latency={dt:5.2f}s  {path}")
    print("LISTEN: does prompt-steered emotion in pt-BR beat adapting Moshi?")
    print("Compare vs Spike C (Moshi ceiling) + Spike A (cascade floor).")
    print("Record in ../../specs/tech-stack.md + Dev KB.")
    print("====================================================")


if __name__ == "__main__":
    main()
