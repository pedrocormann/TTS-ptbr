# Finetune smoke local (M2) — resultado, 2026-06-11 00:05

Setup: csm-mlx LoRA r=16/α=32, lr 5e-4, 2 épocas (328 steps), batch-eff 8,
dataset = 48 min ElevenLabs-import (351 train/11 val), M2 24GB, ~50 min/época.
Loss: 6.02 → 5.10 (caindo, longe de convergir). Protocolo de eval idêntico ao
de 2026-06-10 (spk-sim WavLM vs 10 refs reais; WER whisper-small).

| Amostra | spk-sim | WER | Leitura |
|---|---|---|---|
| ft1 com âncora | 0.971 | 100% | timbre teto, fala embolada |
| ft2 com âncora | 0.907 | 100% | idem |
| **ft1 SEM âncora** | **0.969** | 268% | **voz NOS PESOS ✓** (zero-shot sem âncora era ~aleatório) |
| **ft2 SEM âncora** | **0.980** | 147% | idem — acima do teto real (0.965) |
| (baseline zero-shot) | 0.93-0.97 | 47-100% | — |

## Veredito (2 conclusões, 1 de cada sinal)

✅ **A IDENTIDADE DE VOZ ENTROU NOS PESOS.** O teste-chave do smoke passou:
sem NENHUMA âncora de contexto, o modelo gera com o timbre do Pedro em nível
de teto (0.969-0.980). 48 min + LoRA r16 + 2 épocas bastam pra voz.

❌ **PORTUGUÊS NÃO (como previsto).** WER 100%+ — "português-aparente" sem
conteúdo. Coerente com a evidência georgiana (35h LIMPAS + r64 + ~14 épocas →
CER 2,8%): língua exige ~40× mais exposição do que demos. Loss em 5.10 ainda
caindo confirma undertraining, não bug.

## Implicação no plano (reforça o REPLAN, não muda)

1. **Voz = resolvida barato; língua = o investimento.** A receita em 2 estágios
   (dossiê 10) volta ao centro: **Estágio A** = adaptar o CSM ao pt com corpus
   CC aberto (CML 68h + MLS-pt 161h + CV 187h ≈ 416h; full-FT ou LoRA r64
   agressivo, Colab A100/L4) → **Estágio B** = LoRA da voz do Pedro por cima
   (provado hoje que funciona).
2. Notebook 04 (T4, voz-only) serve pro Estágio B; criar **notebook 06
   (Estágio A — língua)** com o mix CC. Alternativa testável antes: r64 +
   train-embeddings + ~10-14 épocas sobre as horas novas do G0/G1 (a aposta
   "dezenas de horas bastam se LIMPAS").
3. Infra 100% validada: transcrição→dataset→treino→adapter→inferência rodou
   de ponta a ponta NUM MACBOOK. O ciclo de iteração local existe.
4. Bug corrigido: `load_adapters` espera o DIRETÓRIO do run (adapter_config.json
   + adapters.safetensors), não o arquivo .safetensors.
