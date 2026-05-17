# Dossier 70 — Voice-identity & watermarking decisions (web research, 2026-05-17)

> Autonomous pass. Two decisive findings that **correct earlier dossiers**:
> (1) for a Moshi spine the voice path is **Kyutai-TTS/DSM voice EMBEDDINGS**,
> NOT per-voice LoRA and NOT CSM-front. (2) Post-waveform watermarks (AudioSeal
> etc.) are **erased by neural-codec re-encode** (Sony RAW-Bench) — and our
> output IS Mimi-decoded.

## PART A — Voice-identity / cloning

**DECISION: 2-voice MVP = Kyutai-TTS/DSM voice-embedding conditioning** (cross-
attention on a precomputed speaker embedding; same multistream lineage as the
Moshi spine; re-anchored every frame ⇒ does NOT drift like prefix-cloning).
Per-voice LoRA staged ONLY as Phase-2 fallback if speaker-sim cosine < target.

- **Per-voice LoRA on Moshi:** stereo data, rank 128, ~2k steps; **multi-voice
  hot-swap is UNDOCUMENTED** (process-per-voice, one `--lora-weight` each);
  conflates *voice* with *dialogue behavior*; heaviest path. Fallback only.
- **CSM-1B front:** single-utterance, no full-duplex, no internal text — running
  it on Moshi's text output **destroys Moshi's audio-native full-duplex** + adds
  a serial TTS hop. **It does NOT compose with a Moshi spine — either/or.**
  ⇒ corrects dossier 50's "CSM = the voice component" for the Moshi-spine case.
- **Hybrid (Moshi-as-text-manager + cloned TTS):** collapses to "TTS on Moshi
  text" — negates the reason to bet Moshi; risks <800 ms + kills full-duplex.
- **Long-dialogue drift** = the documented open problem. Measure: SV cosine
  (ECAPA/Resemblyzer) on rolling 30 s windows over ~10 min; report mean +
  worst-window + drift slope. Mitigations in order: (a) fixed precomputed
  embedding (DSM — inherently re-anchored), (b) periodic prefix re-anchor,
  (c) per-voice LoRA last.
- **Effort:** per voice = **~5–15 min clean directed pt-BR** (multi-emotion,
  single mic, 24 kHz) → compute embedding → condition. Days, no GPU training for
  MVP. Kyutai voices are EN/FR — **pt-BR embedding fidelity is the Phase-0
  Spike B/C test (unproven).**

## PART B — Watermarking / consent (day-one)

**CRITICAL (Sony RAW-Bench, Interspeech 2025):** under neural-codec re-encode
(EnCodec/DAC), AudioSeal/SilentCipher/WavMark/Timbre full-message accuracy ≈ 0;
adversarial retraining doesn't fix it; DAC defeats all. "Watermarking and neural
codecs compete for the same space." **Our output is Mimi-decoded ⇒ any downstream
Mimi/neural re-encode erases a post-waveform mark.**

| Method | License | Survives neural re-encode? | Note |
|---|---|---|---|
| **AudioSeal** | MIT | ❌ (RAW-Bench) | fast/streaming, 16-bit, robust to resample/MP3, 0.997 clean |
| VoiceMark | **unstated ⚠️** | partial (EnCodec 98.5%, but self-VC→chance 2026) | don't ship until license cleared |
| **Codec-embedded / Latent-Mark / GenMark** | research | ✅ (born watermarked) | only family that survives the codec bottleneck; heavy integrate |
| Perth/etc | — | ❌ weak | not competitive |

**DECISION:** ship **AudioSeal (MIT) post-Mimi-decode, day one** as a
**provenance signal, NOT tamper-proof** — document it does not survive 3rd-party
neural re-encode. **Roadmap codec-embedded / Latent-Mark as the durable Phase-3+
upgrade** (the only thing that truly survives Mimi; needs Mimi-side retraining,
SDumont). Place strictly last (post-decode, pre-serialize); negligible latency.
Do NOT adopt VoiceMark until license cleared.

**LGPD/ANPD posture (ship day one).** Voice = biometric ⇒ sensitive data (LGPD
Art. 11); ANPD 2025-26 agenda prioritizes biometrics + AI-training scrutiny.
Consent artifact (per voice, signed, versioned, in the private registry): states
voice = sensitive biometric; **specific commercial purpose**; that a synthetic
clone is created; retention; controller (Unflat) + DPO contact; **revocation
right + effect (delete clone/embedding)**; **separate opt-in checkbox for model-
training use** (do not bundle); no secondary use w/o new consent; enumerated
rights. Hired talent: + commercial-use/IP license clause. **Provenance log**
(append-only per artifact): voice ID, consent-version hash, model+ckpt hash, ts,
watermark ID, requestor. **Disclose** AI-generated output. **Fail-closed:** no
consent record ⇒ generation refused (matches the business fail-closed/quota req).

## Park (spend/license/legal)
- Brazilian privacy counsel: review consent artifact + hired-talent voice IP/
  license contract before any non-internal use (LGPD Art. 11 sensitive data).
- VoiceMark license unstated — clear before any use. AudioSeal MIT / Moshi-Mimi
  CC-BY-4.0 / CSM Apache clear.
- Phase-0 Spike B/C must verify pt-BR speaker-embedding fidelity (Kyutai EN/FR).
- Codec-embedded watermark = future R&D (Mimi retraining, SDumont GPU).
- ANPD biometric rule still on agenda (not final law) — monitor in the vigil.

Sources: Sony RAW-Bench (Özer et al., Interspeech 2025); AudioSeal (facebook
research, MIT); VoiceMark arXiv 2505.21568 + 2601.20432; Latent Watermarking
arXiv 2409.02915 / Latent-Mark 2603.05310; Kyutai TTS / delayed-streams-modeling;
moshi-finetune README; ANPD 2025-26 agenda; FPF/Meta-case; LGPD Art. 11.
