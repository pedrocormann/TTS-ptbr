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
- `benchmark_sotaque_carioca.jsonl` — 18 sondas dos traços cariocas (ʃ/ʒ/tʃ/dʒ/χ/w)
  com o campo `traits` (o que escutar). Para eval de sotaque.
- `benchmark_pronuncia_ptbr.jsonl` — **sonda de pronúncia** (a métrica que NÃO
  satura — Sesame usa, dossiê 86): homógrafos (sede/colher/jogo/olho…), números,
  siglas, estrangeirismos, topônimos cariocas, casos difíceis. Cada item tem
  `probe` (o que testar) + `expect` (resposta certa). Avaliação: escuta humana
  (acertou a pronúncia contextual? sim/não) — objetivo e não-saturável.
- `accent_scorecard.py` — **sotaque OBJETIVO por-segmento com DIREÇÃO do erro** (o gap #1 vira
  número, não reclamação). Classificador (LR/RF) treinado na fala carioca REAL do Pedro pra um
  contraste fonológico (médias abertas/fechadas /ɛ/-/e/, /ɔ/-/o/), aplicado cross-domain na saída
  do CSM → mede se o TTS cai do lado errado e **pra que lado** ("fecha as abertas?"). Método
  reimplementado de arXiv 2607.01965 (livre; código deles sem licença → não copiado). Lógica
  validada em self-test (`python eval/accent_scorecard.py --selftest`); falta plugar extração real
  de formante (parselmouth) + alinhamento de vogal (MFA) + rótulo do léxico (tools/text/g2p_lexicon,
  BIPA dialeto-Rio). Alimenta o gate de sotaque + é peça publicável com a USP.

## Protocol (what a run reports)
1. Synthesize `benchmark_ptbr.jsonl` with the spine under test → `gen/`.
2. `python -m eval.wer_roundtrip --in-dir gen --transcripts benchmark_ptbr.jsonl`
   (note: jsonl uses `text`; pass the same file, the loader reads `text`).
3. `python -m eval.utmos --audio-dir gen`
4. Latency captured in-spike via `eval.latency.Timer/summarize`.
5. `python -m eval.speaker_sim --ref-dir ref_pedro/ --gen-dir gen/` (clone runs).
6. (later) emotion accuracy via a pt-BR SER head (must be trained — no good
   off-the-shelf for pt-BR prosody; dossier 50).

## Guardrails de métrica (verificado externamente — não repetir erro)
- **NÃO rankear checkpoints por MOS automático (UTMOS/UTMOSv2/NISQA/DNSMOS/SHEET) em PROSÓDIA/timbre.**
  Eles são **cegos a erro de prosódia** (humano cai 1,84 MOS; os modelos <0,1) e têm **viés de F0**
  (premiam voz mais grave: DNSMOS r=−0,79; UTMOSv2 r=−0,72) — arXiv 2606.19951 (dossiê 84). Então:
  (a) medir prosódia pelo scorecard próprio (F0-RMSE segmentado / IU), não por MOS escalar;
  (b) **controlar por F0 médio** ao comparar vozes (é confundidor); (c) usar **variância de F0** como
  feature do "vivo" (humanos correlacionam +0,48; MOS ignora). Confirma externamente o rebaixamento do UTMOS.
- Sanity-check de régua: perturbar a prosódia de propósito e checar se a métrica MOVE (senão é cega ao que importa).

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
