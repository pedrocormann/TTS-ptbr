# eval/ — pt-BR conversational-voice eval harness

Why this exists: **no pt-BR conversational-S2S benchmark exists** (dossier 30/00).
Owning one is both necessary and a strategic asset. This is that harness, built
to be reused by every Phase-0 spike and every later phase.

## Components
- `wer_roundtrip.py` — intelligibility: gen/encode → ASR → WER vs source. The
  core gate. Library + CLI. Judge = faster-whisper (kept distinct from the
  annotate.py labeler on purpose).
- `ttsds2.py` — **primary quality metric since 2026-06-10** (REPLAN eval v2):
  distributional score vs REAL reference speech (MIT, multilingual-validated;
  arXiv 2506.19441). Run on Colab (downloads probe models).
- `utmos.py` — DEMOTED to historical-continuity number only (not calibrated for
  pt-BR; unstable across runs — dossier-2026-06/30 §4). Never decide between
  checkpoints with it; pair expressivity with human CMOS.
- `latency.py` — RTF + e2e p50/p95 vs the 800 ms budget. Reused by all spikes.
- `speaker_sim.py` — clone fidelity: cosine vs reference-voice centroid
  (WavLM-base-plus-sv default — Seed-TTS-eval convention; resemblyzer fallback).
- `benchmark_ptbr.jsonl` — **frozen** pt-BR text set: neutral + warm/enthusiastic/
  empathetic/sad/surprise × {neutral, carioca} + 2 "hard" lines (numbers/named).
  Versioned. Every run synthesizes THIS set so numbers are comparable over time.

## Protocol (what a run reports)
1. Synthesize `benchmark_ptbr.jsonl` with the spine under test → `gen/`.
2. `python -m eval.wer_roundtrip --in-dir gen --transcripts benchmark_ptbr.jsonl`
   (note: jsonl uses `text`; pass the same file, the loader reads `text`).
3. `python -m eval.utmos --audio-dir gen`
4. Latency captured in-spike via `eval.latency.Timer/summarize`.
5. `python -m eval.speaker_sim --ref-dir ref_pedro/ --gen-dir gen/` (clone runs).
6. (later) emotion accuracy via a pt-BR SER head (must be trained — no good
   off-the-shelf for pt-BR prosody; dossier 50).

## Still to build (tracked, not done — needs GPU/data or auth)
- pt-BR SER classifier (train our own on the in-house labeled set).
- Full-Duplex-Bench v1.5-style stop/response-latency + overlap (from silero-vad
  on both channels) once a duplex spine runs.
- URO-Bench-style multi-turn/paralinguistic pt-BR set (extend benchmark_ptbr).
- Human CMOS panel tooling (internal blind vs ElevenLabs+Maya — mission.md).

## Tested
`wer_roundtrip.py` logic CPU-smoke-validated 2026-05-17 (faster-whisper tiny,
synthetic clip) — see research/VIGIL-LOG.md. GPU model runs are Pedro's (no GPU
in the autonomous env).
