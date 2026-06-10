# Phase-0 RUNBOOK — what needs Colab/GPU vs what doesn't

> **UPDATE 2026-06-10 (see specs/REPLAN-2026-06-10.md):** (1) Colab Pro+ now has
> A100-80GB/H100/G4-96GB → moshi-finetune LoRA (~40GB peak) fits in Colab; Kyutai
> has an official Colab notebook (tutorials/moshi_finetune.ipynb). (2) For the
> synthetic-data TTS step, prefer **Qwen3-TTS (Apache, pt) or
> Chatterbox-Multilingual-pt-br (MIT)** over Kokoro (kept as fallback).
> (3) Track-A baselines/finetunes (Qwen3-TTS, CSM-Unsloth) live in `notebooks/`.

Single source for executing Phase 0. Top table answers "are the next steps all
Colab-dependent?" — **no.** Prep is done on CPU (committed); Colab is only for
the GPU model runs.

## Dependency map

| Step | Needs | Status |
|---|---|---|
| Synthetic dialogue **scripts** (`gen_dialogues.py`) | **CPU only, no deps** | ✅ done + tested; corpus generatable now |
| `compose_stereo.py` / eval harness / data pipeline **logic** | **CPU only** | ✅ built + CPU-tested (incl. full-duplex backchannel) |
| Research / dossier / decisions | none | ✅ done (`research/dossier/00-SYNTHESIS.md`) |
| **synth_tts.py** (Kokoro renders the audio) | **Colab GPU** (Kokoro, ungated Apache) | ⏳ Pedro runs |
| **Spike C — Moshi smoke** (latency ceiling) | **Colab GPU** (Moshi CC-BY, no gate) | ⏳ Pedro runs |
| **Mimi pt-BR freeze test** (decisive #1) | **Colab GPU** (Mimi CC-BY, no gate) | ⏳ Pedro runs |
| moshi-finetune LoRA pt-BR proof | **Colab A100 / SDumont** | ⏳ after data |
| Spike B — CSM smoke | Colab GPU + **Llama-3.2 (Meta review pending)** | ⏳ blocked on Meta (secondary) |
| Spike D — Qwen3-Omni | **SDumont/A100-80G** (too big for free Colab) | ⏳ later |
| Full CPT (only if LoRA eval fails) | **SDumont GH200** (allocation pending) | ⏳ fallback only |

**So:** the *thinking/prep* is NOT Colab-dependent and is finished. The *model
runs that produce go/no-go numbers* ARE GPU — Colab for Moshi/Mimi/Kokoro
(everything ungated, unblocked now), SDumont only for the heavy/fallback. Colab
is execution, not figuring-things-out.

## Colab session — copy-paste order

> ⚠️ Spike B (CSM, torch 2.4) and Spike C (Moshi, torch 2.6) CONFLICT — use
> SEPARATE Colab runtimes. Set `HF_TOKEN` (Runtime secret) for downloads.

**0. Get the repo (private):**
```
!git clone https://<TOKEN>@github.com/pedrocormann/TTS-ptbr.git && cd TTS-ptbr
```

**1. Synthetic Phase-0 data (engines atualizados 2026-06-10 — ver REPLAN):**
```
!python tools/data/synth/gen_dialogues.py --seeds tools/data/synth/seed_dialogues.jsonl --out synth_dialogues.jsonl --variants 20
# PREFERIDO — qwen3 (Apache, pt nativo, emoção do diálogo via instruct):
!pip -q install qwen-tts soundfile
!python tools/data/synth/synth_tts.py --dialogues synth_dialogues.jsonl --out-dir synth_turns --engine qwen3 --voice-a Ethan --voice-b Chelsie
# ALTERNATIVA — chatterbox-ptbr (MIT, pack pt-BR; voice-a/b = wavs de ref ~7-10s):
#   !pip -q install chatterbox-tts && python tools/data/synth/synth_tts.py ... --engine chatterbox-ptbr --voice-a refA.wav --voice-b refB.wav
# FALLBACK leve — kokoro (sem emoção): --engine kokoro --voice-a pm_alex --voice-b pf_dora
!python tools/data/synth/compose_stereo.py --turns-dir synth_turns --out-dir data/data_stereo
!python tools/data/make_jsonl.py --wav-dir data/data_stereo --out data/ds.jsonl   # needs sphn (moshi env)
```
(26 seeds × 20 ≈ 520 dialogues; raise --variants for more. Escutar o 1º lote de
cada engine: o sotaque é pt-BR? — gate F0.5 do REPLAN.)

**2. Spike C — Moshi latency ceiling (separate runtime; ungated):**
```
!git clone --depth 1 https://github.com/kyutai-labs/moshi.git /content/moshi
!pip -q install "moshi @ git+https://github.com/kyutai-labs/moshi.git#subdirectory=moshi" sphn==0.1.12 faster-whisper==1.1.0 jiwer==3.0.4
!python phase0/spike_c_moshi/smoke_moshi.py --moshi-repo /content/moshi --steps 125
```

**3. Decisive test #1 — Mimi pt-BR freeze (record ~10 short pt-BR clips + a
`trans.jsonl` of {audio,text}; or reuse synth turns):**
```
!python phase0/spike_c_moshi/mimi_ptbr_roundtrip.py --in-dir ptbr_clips --transcripts ptbr_clips/trans.jsonl
```
→ if Δ(resynth−original WER) < 10 pts ⇒ **freeze Mimi** (mirrors J-Moshi); pt-BR
work collapses to the LM. Record in `specs/tech-stack.md` + `research/VIGIL-LOG.md`.

**4. pt-BR LoRA proof (the bet, dossier 60 "M" scenario):**
```
!pip -q install -e research/repos/moshi-finetune
!bash tools/data/annotate_ptbr.sh data/ds.jsonl            # synth has GT json; real audio only
# edit research/repos/moshi-finetune/example/moshi_7B.yaml: data.train_data=data/ds.jsonl, run_dir=...
!torchrun --nproc-per-node 1 -m train research/repos/moshi-finetune/example/moshi_7B.yaml
```
Gate (decisive, dossier 60): native-speaker naturalness + turn-taking. PASS ⇒
ship LoRA, CPT abandoned. FAIL ⇒ escalate to SDumont light-CPT.

**5. Eval every run against the frozen set:**
```
!python -m eval.wer_roundtrip --in-dir gen --transcripts eval/benchmark_ptbr.jsonl --model medium --lang pt
!python -m eval.utmos --audio-dir gen
```

## Order of decisions
test#1 (Mimi freeze) → Spike C latency ceiling → LoRA proof + eval gate →
(pass: lock Moshi+LoRA, /sdd ATUALIZAR) | (fail: SDumont light-CPT) → Phase 1.
Spike B/D run in parallel when Meta/SDumont clear (both secondary).
