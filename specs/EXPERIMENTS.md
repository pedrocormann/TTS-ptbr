# EXPERIMENTS — matriz de treinos no Colab (criada 2026-06-11)

> Encodifica os aprendizados de 10-11/jun (dossiês 84/85, smoke local, podcast
> CTO): **voz é barata (provada no M2), língua é o investimento**; dado LIMPO >
> horas; fillers transcritos; receita georgiana = referência (r=64/α=64,
> LR 5e-5 cosine, ~14 épocas, batch-eff ~128 → CER 2,8% com 35h limpas).
> Resultados → preencher aqui + eval/results/ + VIGIL-LOG.

## Estágio A — ensinar PORTUGUÊS ao CSM-1B (notebook 06)

| Exp | Dados | Horas | Licença | Hipótese | GPU/CUs | Status |
|---|---|---|---|---|---|---|
| **A1-cml** ⭐começar | CML-TTS pt (Frederico, CC-BY) | 68h | ✅ produto | "georgian-scale limpo basta pra inteligibilidade" (68h ≈ 2× as 35h dele) | A100-40, ~15-25h, ~80-135 CU | ⬜ |
| A2-mix | CML + MLS-pt + CV-pt | ~416h | ✅ produto | mais horas = melhor cauda/robustez (1-2 épocas) | A100, 40-85h, 216-460 CU | ⬜ |
| A3-tagarela 🔬 | TAGARELA clean slice (stream 50-100h) | 50-100h | ❌ **NC — RESEARCH-ONLY** | "espontâneo ensina prosódia conversacional melhor que leitura" — comparação científica; **pesos jamais shipam** (tag _RESEARCH no nome) | A100, ~20-40h | ⬜ |
| A4-fullft | = A1, mas full-FT (knottwill: melhor p/ língua) vs LoRA r64 | 68h | ✅ | "full-FT > LoRA pra domain-shift de língua" (ablação em subset 20h) | A100-40 | ⬜ |

Métricas de decisão (gate): WER round-trip (whisper-large-v3) ≤15% no
benchmark_ptbr + sondas de pronúncia ≥70% + escuta. Vencedor vira a BASE-PT.

## Estágio B — a VOZ por cima da BASE-PT (notebook 04 adaptado)

| Exp | Dados | Hipótese | Status |
|---|---|---|---|
| B1 | 48min ElevenLabs sobre BASE-PT | voz+língua juntas finalmente (espera-se WER≤15% E spk-sim≥0.95 sem âncora) | ⬜ |
| B2 | B1 + G0/G1 gravados (quando existirem) | mais dado limpo de voz = prosódia mais estável | ⬜ |
| B3 | multi-turno mascarado (csm-mlx --mask-speaker-ids / mask -100) | contexto no treino reduz drift (EXPERIMENTO INÉDITO, publicável) | ⬜ |

## Regras herdadas dos aprendizados

1. Smoke SEMPRE antes do run cheio (subset 5-10h, 1 época, ouvir).
2. Checkpoint no Drive a cada ~200 steps (sessão Colab morre em 24h; retomar).
3. Misturar ~10% de dado conversacional/expressivo no Estágio A (lição Dia-pt:
   leitura pura apaga expressividade).
4. Fillers/disfluências SEMPRE transcritos (lição finlandesa).
5. Eval automática ao fim de cada run: WER + spk-sim + 5 sondas de pronúncia +
   2 amostras pra escuta. Registrar AQUI antes do próximo run.
6. A3: sufixo `_RESEARCH` em todo artefato; nunca mesclar no caminho do produto.
