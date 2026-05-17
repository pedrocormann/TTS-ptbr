# TTS-ptbr — Tech Stack

> **Status: DRAFT v0.2.** Architecture is bet-not-locked: Phase 0 decides with data. `[TBD]` = open.

## System architecture
Full-duplex conversational voice. **The spine is the conversational speech model (audio-native, emotional, full-duplex). Text is backstage/parallel, never the spine** (see `phase0/RETHINK.md`, primary-source verified 2026-05-17). Bet = **Moshi** (true full-duplex, text = ablatable parallel Inner Monologue, official LoRA finetune); co-bet = **Qwen3-Omni** (Apache-2.0, native pt speech I/O). CSM-1B = expressive single-utterance + in-context voice-clone **component**, not the spine. Cascade = latency/expressivity floor only. Layers:

~~~
Audio I/O:   mic capture / playback, 24 kHz, streaming, barge-in
VAD:         silero-vad — endpointing + turn-taking
ASR:         faster-whisper (CTranslate2) — streaming pt-BR + transcription context
Text (back): backstage/parallel only — Moshi Inner-Monologue (internal) OR a swappable content LLM (Sabiá/Gemini Flash). NOT the spine.
Spine:       Moshi (bet, FD) | Qwen3-Omni (co-bet, pt-native) — both + Mimi-class codec (12.5 Hz, 80 ms/frame). CSM-1B = voice/clone component. Cascade = floor.
Serving:     hybrid — Python orchestration + Rust/Moshi server for codec/inference
Eval:        latency harness, WER round-trip (faster-whisper), MOS panel tooling
Data tools:  in-house pt-BR audio manual labeling tool (lightweight, from Phase 1)
Storage:     open code; PRIVATE weights registry + proprietary dataset (the "gold")
~~~

## Stack
| Layer | Technology | Why |
|---|---|---|
| Language | Python | team proficiency; ML/audio ecosystem; maintenance = decision factor #1 |
| Spine — bet | **Moshi** (kyutai, CC-BY-4.0) | true full-duplex; text=parallel Inner Monologue (ablatable); official `moshi-finetune` LoRA; ~200ms |
| Spine — co-bet | **Qwen3-Omni-30B-A3B** (Apache-2.0) | native pt speech I/O; emotion via prompt; streaming near-FD; fine-tunable |
| Voice component | Sesame CSM-1B (Apache-2.0) | best expressive single-utterance + in-context clone; NOT a spine (no FD, no text) |
| Codec | Mimi-class (CC-BY-4.0) | low-latency streaming RVQ; shared by Moshi and CSM |
| Text (backstage) | Moshi Inner-Monologue (internal) or pluggable LLM (Sabiá/Gemini Flash) | content only; parallel/backstage, not the spine |
| ASR | faster-whisper | fast (CTranslate2), pt-BR ok, ubiquitous; Sesame forks it |
| VAD / turn-taking | silero-vad | endpointing, barge-in; Sesame forks it |
| Serving | Hybrid: Python orchestration + Rust/Moshi inference server | latency without making the team a Rust shop (factor #1) |
| Emotion control | spine-native (Moshi: latent via audio-context; Qwen3-Omni: prompt) + reference audio | conversational emotion lives in the spine, not bolted-on tags |
| Training | PyTorch; QLoRA proof (Colab) → continued-pretrain + full (SDumont GH200) | cost-staged |
| Experiment tracking | `[TBD]` W&B / local | reproducibility |

## Phase-0 hypotheses (decide the SPINE with data — see phase0/README.md)
| Spike | Model | Decisive metric (go/no-go) |
|---|---|---|
| **C — Moshi** ★bet | `kyutai/moshiko-pytorch-bf16` | real full-duplex latency (ceiling) + after small pt LoRA: pt-BR WER drops while FD/Inner-Monologue holds |
| **D — Qwen3-Omni** co-bet | `Qwen/Qwen3-Omni-30B-A3B-Instruct` | pt-BR emotional expressivity preference + turn latency (heavy GPU: SDumont/A100-80G, not free Colab) |
| **B — CSM** voice probe | `sesame/csm-1b` | in-context clone fidelity (Pedro/carioca) + pt-BR WER no-FT — feeds the voice layer whichever spine wins |
| **A — Cascade** floor | faster-whisper → LLM → TTS | e2e p50 latency floor every spine must beat (yardstick, not destination) |

**Research vigil (standing ritual):** each sprint, review new papers/refs/repo advances (Moshi/Kyutai, Qwen-Omni, Step-Audio, CSM, …) → decide to incorporate into the spine or test in parallel.

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
