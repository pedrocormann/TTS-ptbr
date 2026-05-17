# Phase 0 — Hypothesis validation (the architecture bake-off)

> **Reframed 2026-05-17** after primary-source research (Pedro's correction).
> Earlier framing ("CSM-hybrid, text-core") was wrong. See `RETHINK.md`.

## The mental model (do not lose this)

**The spine is the conversational SPEECH model — audio-native, emotional, full-duplex.
Text is backstage/parallel, NEVER the spine.** (Verified: Moshi's paper says audio
generation works alone; the text "Inner Monologue" is a *time-aligned parallel aid*
that boosts quality and is ablatable. CSM cannot generate text; Maya's conversational
feel comes from conditioning on prior conversational *audio*, not a text pipeline.)

North star: the best pt-BR **emotional full-duplex conversation** model. Text/STT/LLM
exist in the back end; they are not the core.

```
   THE SPINE = audio conversation model
   (emotion + full-duplex live here)
        ▲                 ▲
        │ parallel        │ backstage
   text Inner-Monologue   content LLM (swappable)
   (Moshi: aid, ablatable)  (words only, not the spine)
```

## Candidates (ranked by fit to the north star)

| # | Spine type | Model | Why | License | pt-BR |
|---|---|---|---|---|---|
| 1 ★bet | true full-duplex, text=parallel Inner Monologue | **Moshi** (kyutai) | exactly the thesis; official `moshi-finetune` (LoRA); ~200ms; 2 parallel audio streams, no turn assumption | CC-BY-4.0 ✅ | needs adaptation (EN/FR base) |
| 2 co-bet | streaming s2s omni, near-FD turn-taking | **Qwen3-Omni-30B-A3B** | Apache-2.0, **native pt speech I/O**, emotion via prompt, fine-tunable | Apache-2.0 ✅ | native ✅ |
| 3 component | expressive single-utterance + in-context clone | **CSM-1B** (sesame) | best expressive voice + voice-clone block; NOT a spine (no FD, no text) | Apache-2.0 ✅ | from scratch |
| floor | cascade STT→LLM→TTS | faster-whisper→LLM→Orpheus/S1 | the latency/expressivity **yardstick**, not a destination | mixed | ok |

## Spikes (each: one decisive metric, throwaway)

| Spike | Model | Build | Decisive metric (go/no-go) |
|---|---|---|---|
| **C** ★ | Moshi (`kyutai/moshiko-pytorch-bf16`) | latency benchmark on our GPU + confirm pt-BR gap + set up moshi-finetune pt path | real full-duplex latency (the ceiling) + after small pt LoRA: pt-BR WER drops while FD/Inner-Monologue holds |
| **D** | Qwen3-Omni | pt-BR speech gen + emotion-via-prompt + latency (heavy GPU) | pt-BR emotional expressivity preference + turn latency |
| **B** | CSM-1B | single-utterance expressivity + pt-BR phonetics + in-context clone of Pedro/carioca | clone fidelity + pt-BR WER (no FT) — feeds the *voice layer* whichever spine wins |
| **A** | cascade | faster-whisper→LLM→TTS skeleton | e2e p50 latency floor every spine must beat |

## Order of attack
1. Compute: Colab (≤R$500/mo) for Moshi-7B + CSM smokes; **SDumont GH200 / A100-80G for Qwen3-Omni-30B** (it does NOT fit free Colab — honest).
2. **Spike C (Moshi)** + **Spike B (CSM)** smokes on Colab — the two that fit. Get latency ceiling + expressivity/clone reads.
3. **Spike D (Qwen3-Omni)** on SDumont/Inception when access lands.
4. **Spike A** cascade as the latency floor reference.
5. Decide the spine with data → record in `tech-stack.md` + Dev KB → `/sdd` ATUALIZAR → `/feature-spec` Phase 1.

## ⚠️ Environment conflict (found by static test 2026-05-17)
Spike B (CSM) needs **torch==2.4 + moshi==0.2.2**; Spike C (Moshi/moshi-finetune)
needs **torch==2.6 + sphn==0.1.12 + moshi@git**. **Incompatible — use SEPARATE
venvs / separate Colab runtimes per spike.** Don't `pip install` both in one env.

Each spike dir has its own README + runnable code + Colab notebook. Reference code: `../research/repos/`.
