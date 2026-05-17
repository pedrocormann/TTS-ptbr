"""
Spike A — cascade latency FLOOR. Measures the real ASR hop (faster-whisper) and
adds configurable budgets for the still-stubbed LLM + TTS hops, to get a floor
estimate this week. Tighten by replacing the stubs with real Sabiá/Gemini-Flash
and Orpheus/OpenAudio-S1 calls (marked TODO).

This is the YARDSTICK every spine (Moshi/Qwen3-Omni) must beat. Light on purpose.

Run:
  python cascade_latency.py --wav sample_ptbr.wav --runs 5
"""
import argparse, statistics, time


def asr_hop(wav_path: str) -> tuple[str, float]:
    from faster_whisper import WhisperModel
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = WhisperModel("small", device=dev,
                         compute_type="float16" if dev == "cuda" else "int8")
    t0 = time.perf_counter()
    segs, _ = model.transcribe(wav_path, language="pt", beam_size=1)  # beam=1 = fastest
    text = " ".join(s.text for s in segs).strip()
    return text, time.perf_counter() - t0


def llm_hop(_text: str, budget_ms: float) -> tuple[str, float]:
    # TODO: replace with real streaming Sabiá / Gemini-Flash call (first-token latency).
    # Stub: just account a budget so the floor is honest until wired.
    time.sleep(budget_ms / 1000.0)
    return "resposta da IA (stub)", budget_ms / 1000.0


def tts_hop(_text: str, budget_ms: float) -> float:
    # TODO: replace with real Orpheus / OpenAudio-S1 streaming first-audio latency.
    time.sleep(budget_ms / 1000.0)
    return budget_ms / 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", required=True, help="a pt-BR utterance wav (the 'user turn')")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--llm-budget-ms", type=float, default=300,
                    help="placeholder until a real LLM is wired (first-token)")
    ap.add_argument("--tts-budget-ms", type=float, default=200,
                    help="placeholder until a real TTS is wired (first-audio)")
    args = ap.parse_args()

    e2e = []
    for i in range(args.runs):
        txt, t_asr = asr_hop(args.wav)
        _, t_llm = llm_hop(txt, args.llm_budget_ms)
        t_tts = tts_hop(txt, args.tts_budget_ms)
        total = t_asr + t_llm + t_tts
        e2e.append(total)
        print(f"  run {i+1}: ASR={t_asr*1000:.0f}ms (real) + LLM={t_llm*1000:.0f}ms"
              f"(stub) + TTS={t_tts*1000:.0f}ms(stub) = {total*1000:.0f}ms")

    print("\n================ SPIKE A — FLOOR ================")
    print(f"e2e p50 : {statistics.median(e2e)*1000:.0f} ms  "
          f"(ASR real; LLM/TTS = budgets — tighten when wired)")
    print(f"target  : < 800 ms. This is the number Moshi/Qwen3-Omni must BEAT")
    print("to justify a spine over a dumb cascade. Record in ../../specs/tech-stack.md.")
    print("================================================")


if __name__ == "__main__":
    main()
