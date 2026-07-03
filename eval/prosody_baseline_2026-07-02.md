# Baseline de prosódia — 2026-07-02 (1º número objetivo do projeto; F3 estava em n=0)

Instrumento: `tools/prosody/prosody_scorecard.py` (receita Aluísio/USP · Galdino et al. 2024, núcleos silábicos via picos de intensidade vozeados, CPU/parselmouth). Âncora humana: clipes reais do Pedro (`data/raw/elevenlabs2024/segments`, 349/364 analisáveis).

| Run | n | dur média (s) | taxa fala (síl/s) | sílaba média (ms) | nuclear (ms) | SD sílaba (ms) | pausas/clipe | pausas/10s |
|---|---|---|---|---|---|---|---|---|
| **humano (Pedro, real)** | 349 | 7.9 | 1.7 | 605 | 1910 | **576** | 1.0 | **1.23** |
| treino2 a0_auto | 14 | 4.8 | 1.7 | 440 | 1108 | 392 | 0.3 | 0.60 |
| treino2 c0_curated | 12 | 4.8 | 2.1 | 373 | 987 | 305 | 0.2 | 0.35 |
| treino2 c_long | 14 | 4.6 | 1.6 | 717 | 1335 | 312 | 0.5 | 1.08 |
| treino2 c_lr2e5 | 13 | 4.8 | 1.5 | 562 | 1486 | 499 | 0.4 | 0.80 |
| cml_long (base, Treino 1) | 10* | 12.8 | 0.3 | 786 | 1708 | 517 | 4.9 | 3.83 |
| stage_b_final (Treino 1) | 14 | 4.6 | 2.4 | 426 | 1053 | 326 | 0.5 | 1.08 |

\* cml_long: 4 de 14 clipes não-analisáveis (<2 núcleos detectados) — degeneração de long-form, não amostra limpa.

Coluna `pausas/10s` derivada (pausas totais ÷ duração total ×10) — normaliza o viés de clipes de tamanhos diferentes. JSONs por clipe no scratchpad da sessão (`prosody_*.json`).

## Leitura honesta

1. **O valor ABSOLUTO de taxa de fala está errado no instrumento, não na voz.** O detector (limiar = pico máximo −4dB) acha ~1.7 síl/s até no Pedro real — 4x abaixo do alvo do paper (6.67). Ou seja: NÃO dá pra comparar com os alvos naturais do Galdino et al.; só vale comparação RELATIVA entre runs medidos com o mesmo instrumento. Consertar o limiar (mediana+2dB, de Jong & Wempe completo) antes de citar número absoluto.
2. **O sinal relativo que presta: pausas e variabilidade rítmica.** Humano = 1.23 pausas/10s e SD 576ms. Todos os treinos ficam ABAIXO nos dois — menos pausa (0.35–1.08) e ritmo mais achatado (SD 305–499). É a assinatura objetiva do "robótico" que a gente ouvia: o modelo fala em fluxo contínuo e uniforme, sem o respiro e a elasticidade silábica do Pedro.
3. **c0_curated é o braço MAIS robótico por esta régua** (0.35 pausas/10s, SD 305) — curadoria melhorou WER mas achatou prosódia. c_lr2e5 é o mais próximo do humano em SD (499 vs 576) e c_long em pausas (1.08 vs 1.23) — nenhum braço ganha nos dois eixos ao mesmo tempo.
4. **cml_long é outlier degenerado, não "natural":** 3.83 pausas/10s (3x o humano), 0.3 síl/s e 4 clipes imprestáveis = silêncio longo/colapso em geração longa, problema já conhecido — o "dentro da faixa natural 👍" do veredito automático aqui é falso positivo.
5. **Limites:** o script mede SD de DURAÇÃO silábica, não desvio de F0 (monotonia de pitch segue sem número — próximo passo do F3); n=12–14 por braço é amostra pequena; e o veredito automático foi calibrado pros alvos do paper que o item 1 invalida — ignorar o emoji, olhar as colunas.
