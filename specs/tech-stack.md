# TTS-ptbr — Tech Stack

> **Status: DRAFT v0.1.** Architecture is bet-not-locked: Phase 0 decides with data. `[TBD]` = open.

## System architecture
Full-duplex conversational voice. Bet = **path B (CSM-style hybrid, the Maya recipe)**: a pluggable text LLM produces the words; the speech model conditions on conversational *audio* context for prosody/emotion and in-context voice cloning; prosody does not pass through the text bottleneck. Layers:

~~~
Audio I/O:   mic capture / playback, 24 kHz, streaming, barge-in
VAD:         endpointing + turn-taking          (candidate: silero-vad)
ASR:         streaming pt-BR                     (candidate: faster-whisper / Parakeet) [TBD]
LLM (brain): content only, pluggable behind iface (candidates: Sabiá, Gemini Flash) [post-Phase 0]
Speech:      CSM-1B (bet) + Mimi codec (RVQ, 12.5 Hz, 80 ms/frame); alts: A=cascade TTS, C=Moshi
Eval:        latency harness, WER round-trip, MOS tooling
Data tools:  in-house pt-BR audio manual labeling tool
Storage:     datasets + checkpoints (closed weights, separate from open code)
~~~

## Stack
| Layer | Technology | Why |
|---|---|---|
| Language | Python | team proficiency; ML/audio ecosystem |
| Speech model (bet) | Sesame CSM-1B (Apache-2.0) | built for conversational context + in-context cloning = the goal |
| Codec | Kyutai Mimi (CC-BY-4.0) | low-latency streaming RVQ; shared by CSM and Moshi |
| LLM (content) | Pluggable; Sabiá / Gemini Flash candidates | swap behind interface; decide with Phase-0 data |
| ASR | `[TBD]` faster-whisper / Parakeet | streaming pt-BR for cascade + transcription context |
| VAD / turn-taking | `[TBD]` silero-vad | endpointing, barge-in |
| Serving | `[TBD]` streaming (websockets; Rust à la Moshi vs Python) | < 800 ms budget |
| Training | PyTorch; LoRA/QLoRA (Colab) → full (SDumont GH200) | cost-staged |
| Experiment tracking | `[TBD]` W&B / local | reproducibility |

## Phase-0 hypotheses (decide architecture with data)
| Spike | Stack | Decisive metric (go/no-go) |
|---|---|---|
| A — Cascade | streaming Whisper → pt-BR LLM → Orpheus/XTTS clone | e2e p50 < 800 ms + intelligible clone from 10-30 s |
| B — CSM hybrid (bet) | pt-BR LLM → CSM-1B on audio context | prosody/emotion MOS vs A + CSM pt-BR phonetics w/o fine-tune |
| C — Moshi (ceiling probe) | stock Moshi | measured full-duplex latency + pt-BR out-of-box go/no-go |
| (opt) Orpheus | dedicated TTS latency spike | published ~100-200 ms streaming validated on our HW |

**Research vigil (standing ritual):** each sprint, review new papers/refs/repo advances (CSM, Moshi, Orpheus, …) → decide to incorporate into B or test in parallel.

## Hardware
- Dev recording: team mics (good quality) for in-house directed recording.
- Compute: Colab Pro+ (≤ R$500/mo), SDumont GH200 (Grace Hopper, pending auth), NVIDIA Inception cloud credits (overflow + multi-GPU latency benchmarking).

## Data & storage
- Open pt-BR corpora (commercial-safe): CML-TTS, MLS-pt, Common Voice pt, TTS-Portuguese Corpus (CC-BY/CC0).
- In-house directed recordings (emotion-prompted, multi-accent); team voices for MVP.
- Manual labeling tool to enrich/curate pt-BR audio.
- Closed: proprietary expressive dataset + voice/emotion checkpoints (the "gold"), stored separately from open code (mechanism `[TBD]`).

## Configuration
| Var | Default | Description |
|---|---|---|
| LATENCY_TARGET_MS | 800 | e2e p50 design budget |
| `[TBD]` | | |

## Dependencies
Lean runtime: torch, transformers, the CSM/Mimi stack, an ASR lib, a VAD lib, audio I/O. Exact pins `[TBD]` after Phase 0.

## Folder structure
~~~
TTS-ptbr/
  specs/        mission, tech-stack, roadmap (this constitution)
  phase0/       throwaway spikes A/B/C/orpheus
  src/          pipeline (open)
  data/         corpora manifests (open); raw audio gitignored
  eval/         latency harness, WER round-trip, MOS tooling
  tools/labeler/ manual pt-BR audio labeling tool
  weights/      PRIVATE — gitignored / separate registry (the "gold")
~~~

## Technical constraints
- e2e p50 < 800 ms.
- License: Apache / CC-BY / CC0 only.
- Open code, closed weights (enforcement `[TBD]`).
- Consent-gated voice cloning; Mimi attribution; Sesame acceptable-use mirrored.

## Open questions
1. Serving stack: Rust (Moshi-style) vs Python for the < 800 ms budget?
2. ASR + VAD concrete choices and their latency contribution.
3. Closed-weights mechanism inside a public repo.
4. Emotion conditioning method (tokens? reference audio? both?).
5. pt-BR fine-tune recipe for CSM (continued pretrain vs LoRA; data volume).
6. Eval: MOS tooling and panel; WER round-trip ASR choice.
