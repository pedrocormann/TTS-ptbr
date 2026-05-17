# Spike A — Cascade (the latency FLOOR / yardstick)

Not a destination. The reference number every spine (Moshi/Qwen3-Omni) must beat:
how slow is the naive STT → LLM → TTS pipeline? If a spine can't beat the floor,
it has no reason to exist.

## Decisive metric
End-to-end p50 latency: user-stop → speech-start, summing ASR + LLM + TTS.
Target the spines chase: < 800 ms (constitution).

## What's here
- `cascade_latency.py` — runnable skeleton. ASR = faster-whisper (real, measured).
  LLM + TTS = clearly-marked stubs with the swap points (Sabiá/Gemini Flash;
  Orpheus/OpenAudio-S1). It measures the real ASR hop now and a configurable
  budget for the stubbed hops so you get a floor estimate this week, then tighten
  as the LLM/TTS get wired.

## Run
  python cascade_latency.py --wav sample_ptbr.wav --runs 5
(no GPU strictly required for tiny faster-whisper, but use one for realistic numbers)

This spike is intentionally light — it is a ruler, not a product.
