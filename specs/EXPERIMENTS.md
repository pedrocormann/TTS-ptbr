# EXPERIMENTS — matriz de treinos no Colab (criada 2026-06-11)

> Encodifica os aprendizados de 10-11/jun (dossiês 84/85, smoke local, podcast
> CTO): **voz é barata (provada no M2), língua é o investimento**; dado LIMPO >
> horas; fillers transcritos; receita georgiana = referência (r=64/α=64,
> LR 5e-5 cosine, ~14 épocas, batch-eff ~128 → CER 2,8% com 35h limpas).
> Resultados → preencher aqui + eval/results/ + VIGIL-LOG.

> **POLÍTICA (Pedro, 2026-06-11): fase é RESEARCH — qualquer dataset pode entrar
> nos experimentos** (NC incluído). O que fica é a RASTREABILIDADE: a coluna
> "linhagem" diz com que dado o peso nasceu; artefato com dado NC leva o dado no
> nome do run. Quando algo for virar produto: retreino com linhagem limpa
> (CC/próprios) — caminho sempre documentado. Hipóteses explícitas em tudo.

## Estágio A — ensinar PORTUGUÊS ao CSM-1B (notebook 06)

| Exp | Dados | Horas | Linhagem | Hipótese | GPU/CUs | Status |
|---|---|---|---|---|---|---|
| **A1-cml** ⭐smoke/baseline | CML-TTS pt (Frederico, CC-BY) | 68h | limpa | "georgian-scale limpo basta pra inteligibilidade" (68h ≈ 2× as 35h dele); âncora de linhagem limpa | A100-40, ~15-25h, ~80-135 CU | ⬜ |
| **A3-tagarela** 🔥 aposta | TAGARELA (slice 100-300h, espontâneo) | 100-300h | NC (tag no run) | "fala ESPONTÂNEA de podcast ensina pt conversacional (prosódia, ritmo, disfluência) melhor que leitura" — se vencer A1 com folga, o flywheel de reuniões vira ainda mais valioso (é a versão LIMPA do mesmo tipo de dado) | A100, 40-120h | ⬜ |
| A2-mix | CML + MLS-pt + CV-pt (leitura) | ~416h | limpa | mais horas lidas = melhor cauda/robustez (1-2 épocas) | A100, 40-85h, 216-460 CU | ⬜ |
| A4-fullft | = A1, mas full-FT (knottwill) vs LoRA r64 | 68h | limpa | "full-FT > LoRA pra domain-shift de língua" (ablação em subset 20h) | A100-40 | ⬜ |
| A5-best-mix | vencedor(es) acima combinados (ex.: TAGARELA + 10% CML) | — | mista | combinação supera os puros | A100 | ⬜ |

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
6. Linhagem no nome do run (ex.: `csm_A3_tagarela300h`) + nesta tabela; peso
   com dado NC não vira produto sem retreino limpo (mas experimenta à vontade).
