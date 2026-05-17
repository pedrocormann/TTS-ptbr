# TTS-ptbr — Tech Stack

> **Status: DRAFT v0.2.** Architecture is bet-not-locked: Phase 0 decides with data. `[TBD]` = open.

## System architecture
Full-duplex conversational voice. Bet = **path B (CSM-style hybrid, the Maya recipe)**: a pluggable text LLM produces the words; the speech model conditions on conversational *audio* context for prosody/emotion and in-context voice cloning; prosody does not pass through the text bottleneck. Layers:

~~~
Audio I/O:   mic capture / playback, 24 kHz, streaming, barge-in
VAD:         silero-vad — endpointing + turn-taking
ASR:         faster-whisper (CTranslate2) — streaming pt-BR + transcription context
LLM (brain): content only, pluggable behind interface (candidates: Sabiá, Gemini Flash) [decide post-Phase 0]
Speech:      CSM-1B (bet) + Mimi codec (RVQ, 12.5 Hz, 80 ms/frame); alts: A=cascade TTS, C=Moshi
Serving:     hybrid — Python orchestration + Rust/Moshi server for codec/inference
Eval:        latency harness, WER round-trip (faster-whisper), MOS panel tooling
Data tools:  in-house pt-BR audio manual labeling tool (lightweight, from Phase 1)
Storage:     open code; PRIVATE weights registry + proprietary dataset (the "gold")
~~~

## Stack
| Layer | Technology | Why |
|---|---|---|
| Language | Python | team proficiency; ML/audio ecosystem; maintenance = decision factor #1 |
| Speech model (bet) | Sesame CSM-1B (Apache-2.0) | built for conversational context + in-context cloning = the goal |
| Codec | Kyutai Mimi (CC-BY-4.0) | low-latency streaming RVQ; shared by CSM and Moshi |
| LLM (content) | Pluggable; Sabiá / Gemini Flash candidates | swap behind interface; decide with Phase-0 data |
| ASR | faster-whisper | fast (CTranslate2), pt-BR ok, ubiquitous; Sesame forks it |
| VAD / turn-taking | silero-vad | endpointing, barge-in; Sesame forks it |
| Serving | Hybrid: Python orchestration + Rust/Moshi inference server | latency without making the team a Rust shop (factor #1) |
| Emotion control | Tags + reference audio | explicit control surface + in-context nuance (fits CSM paradigm) |
| Training | PyTorch; QLoRA proof (Colab) → continued-pretrain + full (SDumont GH200) | cost-staged |
| Experiment tracking | `[TBD]` W&B / local | reproducibility |

## Phase-0 hypotheses (decide architecture with data)
| Spike | Stack | Decisive metric (go/no-go) |
|---|---|---|
| A — Cascade | faster-whisper → pt-BR LLM → Orpheus/XTTS clone | e2e p50 < 800 ms + intelligible clone from 10-30 s |
| B — CSM hybrid (bet) | pt-BR LLM → CSM-1B on audio context | prosody/emotion MOS vs A + CSM pt-BR phonetics w/o fine-tune |
| C — Moshi (ceiling probe) | stock Moshi | measured full-duplex latency + pt-BR out-of-box go/no-go |
| (opt) Orpheus | dedicated TTS latency spike | published ~100-200 ms streaming validated on our HW |

**Research vigil (standing ritual):** each sprint, review new papers/refs/repo advances (CSM, Moshi, Orpheus, …) → decide to incorporate into B or test in parallel.

## Hardware
- Dev recording: team mics (good quality) for in-house directed recording.
- Compute: Colab Pro+ (≤ R$500/mo), SDumont GH200 (Grace Hopper, pending auth), NVIDIA Inception cloud credits (overflow + multi-GPU latency benchmarking).

## Data & storage
- Open pt-BR corpora (commercial-safe): CML-TTS, MLS-pt, Common Voice pt, TTS-Portuguese Corpus (CC-BY/CC0).
- In-house directed recordings (emotion-prompted, 2 voices); curated/labeled via the in-house tool.
- **Closed (the "gold"):** proprietary expressive dataset + voice/emotion checkpoints, kept in a **private registry separate from the public repo** (private HuggingFace repo or object bucket); `weights/` and raw audio are gitignored. Consent artifacts stored per voice.

## Configuration
| Var | Default | Description |
|---|---|---|
| LATENCY_TARGET_MS | 800 | e2e p50 design budget |
| WEIGHTS_REGISTRY | `[TBD]` | private HF repo / bucket URI for the gold |
| LLM_BACKEND | `[TBD post-P0]` | pluggable content LLM |

## Dependencies
Lean runtime: torch, transformers, the CSM/Mimi stack, faster-whisper, silero-vad, audio I/O, the Moshi server for inference. Exact pins `[TBD]` after Phase 0.

## Folder structure
~~~
TTS-ptbr/
  specs/        mission, tech-stack, roadmap (this constitution)
  phase0/       throwaway spikes A/B/C/orpheus
  src/          pipeline (open)
  data/         corpora manifests (open); raw audio gitignored
  eval/         latency harness, WER round-trip, MOS tooling
  tools/labeler/ manual pt-BR audio labeling tool
  weights/      PRIVATE — gitignored; mirrored to private registry (the "gold")
~~~

## Technical constraints
- e2e p50 < 800 ms.
- License: Apache / CC-BY / CC0 only.
- Open code, closed weights (private registry; gitignore enforced).
- Consent-gated voice cloning; Mimi attribution; Sesame acceptable-use mirrored.

## Open questions
1. Exact split of Python vs the Rust/Moshi server boundary.
2. pt-BR fine-tune recipe details (continued-pretrain data volume; LoRA rank).
3. Private weights registry choice (HF private vs bucket) + access control.
4. Emotion data scheme to feed tags + reference-audio conditioning.
5. Experiment tracking choice; reproducibility policy.
6. WER round-trip ASR config; MOS panel tooling.
