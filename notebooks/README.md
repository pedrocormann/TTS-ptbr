# Notebooks — ordem de EXECUÇÃO (renumerados 2026-06-11)

> A numeração é a sequência que rodamos, não a ordem em que foram escritos.
> Fase 0 = o que já foi feito localmente no M2 (testes 0 e 0.x).

| # | Notebook | O quê | GPU | Status |
|---|---|---|---|---|
| **0** | `0_dataset_prep` | transcrever/exportar gravações (roda sempre que houver áudio novo) | T4 | ✅ feito local p/ os 48min (import ElevenLabs) |
| 0.x | *(local, M2)* | zero-shot CSM/Pocket + smoke finetune → voz nos pesos ✓, língua ✗ | — | ✅ eval/results/2026-06-1*.md |
| **1** | `1_csm_lingua_pt` ⭐ **PRÓXIMO** | **Estágio A: ensinar PORTUGUÊS ao CSM** (A1-cml smoke → A3-tagarela; matriz em specs/EXPERIMENTS.md) | **A100** | ⬜ |
| **2** | `2_csm_voz_pedro` | Estágio B: a voz do Pedro sobre a BASE-PT do passo 1 (B1: WER≤15% + spk-sim≥0.95 sem âncora) | T4 | ⬜ |
| **3** | `3_eval_comparativo` | bench do nosso modelo vs Chatterbox-pt-br/Pocket zero-shot (gate F0.5/F1 com números) | T4 | ⬜ |
| **4** | `4_alt_qwen3tts` | braço alternativo da Trilha A (Qwen3-TTS LoRA) — só se o caminho CSM decepcionar | **L4/A100** | ⬜ opcional |
| **5** | `5_moshi_spine` | Trilha B: Moshi LoRA pt-BR (precisa dos dados estéreo — flywheel de reuniões) | **A100-80/G4** | ⬜ depois do flywheel |

**Regra de bolso:** 1 → ouvir → 2 → 3 (medir) → decidir se 4; o 5 espera as reuniões.
**Sempre:** SMOKE=True antes de run cheio · checkpoints no Drive · resultado em specs/EXPERIMENTS.md.
