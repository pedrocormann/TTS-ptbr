# Phase 0 — Hypothesis validation (throwaway spikes)

Goal: decide the architecture with **data**, not on paper. Each spike is disposable
code with **one decisive metric**. Do not productionize anything here.

| Spike | Build | Decisive metric (go/no-go) |
|---|---|---|
| `spike_a_cascade/` | faster-whisper → pt-BR LLM → Orpheus/XTTS clone | e2e p50 < 800ms + intelligible clone from 10-30s sample |
| `spike_b_csm/` (bet) | pt-BR LLM → CSM-1B conditioned on conversational audio | prosody/emotion MOS vs A + does CSM handle pt-BR phonetics w/o fine-tune |
| `spike_c_moshi/` | stock Moshi (ceiling probe only) | measured full-duplex latency + pt-BR out-of-box go/no-go |
| `spike_orpheus/` (opt) | dedicated Orpheus TTS latency test | published ~100-200ms validated on our HW |

## Order of attack
1. **Compute ready:** Colab set up (cap R$500/mo), SDumont GH200 access requested, NVIDIA Inception activated.
2. **Smoke first:** get CSM-1B + Mimi running at all (Spike B smoke) and Moshi running (Spike C) — just generate audio, measure latency on the GPU you have.
3. **Spike A** in parallel (cascade is the de-risk fallback).
4. **QLoRA proof (Colab):** single pt-BR voice on the chosen base from `TTS-Portuguese-Corpus` (10.5h) — proves the fine-tune path cheaply before any SDumont full run.
5. **Decide:** record the numbers in `tech-stack.md` + Dev KB; lock the architecture; then `/sdd` ATUALIZAR + `/feature-spec` Phase 1.

## Rules
- Reference code to read: `../research/repos/` (run `../research/clone.sh`).
- Measure, don't polish. The only output that matters is the metric per spike.
- Latency budget is end-to-end (turn-end → speech start), p50, target < 800ms.
- License: only Apache/CC-BY/CC0 paths reach the bet (XTTS/F5 = study only).
- Each spike gets its own throwaway venv; nothing here is committed weights.
