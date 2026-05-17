# Spike B — CSM-1B (voice component probe, NOT the spine)

> Reframed 2026-05-17 (see ../RETHINK.md). CSM is no longer "the bet" — text is
> parallel, not core, so the spine bet moved to Moshi (Spike C). CSM stays as the
> **expressive single-utterance + in-context voice-clone component** probe: its
> output feeds the voice layer whichever spine wins. Still worth running.

Throwaway. One job: measure CSM's expressive voice + pt-BR phonetics + clone of
Pedro/carioca — the voice-quality data point, independent of the spine choice.

## Decisive metrics (go/no-go)
1. **Latency/RTF** on the Colab GPU (real-time factor = gen_time / audio_seconds; <1 is the floor for streaming).
2. **pt-BR phonetics without fine-tune** — generate pt-BR, ASR round-trip WER (faster-whisper). The CSM README itself says non-English "likely won't do well" — we measure *how* bad. High WER ⇒ pt-BR is a from-scratch fine-tune (expected), informs effort.
3. **In-context voice clone** — feed a short pt-BR reference, does the voice carry (qualitative).

## What runs (verified against research/repos/csm real API)
- `smoke_csm.py` — load CSM-1B, EN baseline, pt-BR test, latency/RTF, ASR round-trip WER, optional in-context clone. **Fully runnable.**
- `prep_ptbr_data.py` — TTS-Portuguese-Corpus → (text, 24kHz wav) manifest. Runnable.
- `qlora_finetune.py` — **honest scaffold, NOT turnkey.** The CSM repo ships *inference only* (generator.py/models.py, no train.py). Fine-tuning CSM is unsolved-by-Sesame; this scaffolds the data→token path and points at `research/repos/moshi-finetune` (official Kyutai recipe, same Mimi codec) + the Speechmatics/Unsloth community approach as the real path. This file is the Phase-0 research task, not a solved step.
- `colab.ipynb` — orchestrates the above on Colab (clone, install pinned deps, HF login, run smoke, print the go/no-go table).

## Hard prerequisites (real, from the CSM README)
- CUDA GPU (Colab T4/L4/A100). `NO_TORCH_COMPILE=1`.
- HF account with **accepted licenses**: `meta-llama/Llama-3.2-1B` (gated) AND `sesame/csm-1b`. Without both, load fails.
- Pinned deps (CSM repo): torch 2.4, transformers 4.49, moshi 0.2.2, torchao 0.9, torchtune 0.4, silentcipher.

## Run order
1. `colab.ipynb` cell 1-3: clone csm + install + `huggingface-cli login`.
2. `smoke_csm.py`: get the latency/RTF + pt-BR WER numbers. **This alone decides most of B.**
3. `prep_ptbr_data.py` then read `qlora_finetune.py` — scope the fine-tune effort; don't expect it to "just run".
4. Record numbers in `../../specs/tech-stack.md` + Dev KB. Then `/sdd` ATUALIZAR + `/feature-spec` Phase 1.

Watermark note: `generator.generate()` auto-applies Sesame's GH watermark. Fine for the spike; production needs our own key (tracked in tech-stack open questions).
