# Eval local M2 — zero-shot, 2026-06-10 (gate F0.5, primeira rodada de números)

Setup: M2 24GB; refs = 10 segmentos reais do Pedro (import ElevenLabs, mp3 192k);
spk-sim = WavLM-base-plus-sv cosseno vs centroide; WER = faster-whisper small pt.
Amostras em `data/testes_maya/` (não versionadas).

| Sistema | spk-sim | WER | RTF | Veredito |
|---|---|---|---|---|
| real vs real (teto) | 0.965 | — | — | — |
| Pocket-6L "rafael" | 0.906* | — | 5,3× | fala pt ok, voz genérica, qualidade fraca (Pedro: "mt ruim") |
| Pocket-24L "rafael" | 0.877* | **7,4%** | 1,8× | fala pt ok; voz não é do Pedro |
| CSM-1B cheio, 1 ref | 0.930 | 84% | 0,33× | timbre certo, português EMBOLADO |
| CSM 8-bit, 1 ref | **0.973** | 47% | 0,70× | timbre nível teto; pt ruim |
| CSM 4-bit, 1 ref | 0.618 | 100% | 0,97× | 4-bit + contexto fino = perde identidade |
| **CSM 4-bit, 3 refs** | **0.973** | 94% | 0,97× | **contexto múltiplo recupera o timbre no 4-bit** |

\* spk-sim do WavLM-base-plus-sv COMPRIME a escala: ~0.88-0.91 = "voz masculina
pt parecida" (rafael ≠ Pedro); só ≥0.97 ≈ mesma voz aqui. Reportar sempre com o
teto real-vs-real da mesma rodada.

## Conclusões (alimentam o REPLAN)

1. **Confirmada a previsão do dossiê**: CSM-1B base não fala pt (treino EN) —
   timbre clona perfeito, fonética desmorona (WER 47-100%). O problema do app
   "não consegue falar direito" é ESTE, não engenharia.
2. **O finetune é o desbloqueio** (georgiano: mesmo padrão; pós-35h → CER 2,8%).
   Smoke local de 48 min em andamento; run sério = notebook 04 (Colab).
3. **Regra de operação 4-bit: SEMPRE ≥3 âncoras de contexto** (0.618→0.973).
   Embutido no `CSMMLXAdapter` (auto-âncoras dos segmentos transcritos).
4. Pocket = útil só como fallback de latência/inteligibilidade; não compete em voz.
5. Próxima medição: mesmas métricas nos ft*.wav (pós-LoRA local) — a expectativa
   é WER despencar mantendo spk-sim ≥0.95. Depois, notebook 04 com r=64.
