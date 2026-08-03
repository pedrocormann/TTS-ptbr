# 87 · Triagem — alerta Scholar (tracking Sandra Aluísio), 03/ago/2026

> Lote de 9 papers baixados do Google Scholar Alerts (tracking da Sandra Aluísio).
> Critério: mérito de **arquitetura/add-on** transferível pro nosso treino/deploy/eval — não idioma
> ([[feedback-arquitetura-nao-idioma]]). Triagem multi-agente + verificação adversarial nos vereditos fortes.
> Saldo: **3 WATCH · 6 SKIP** (excluídos). O Qwen 3.0 entrou como TEST e foi **rebaixado a WATCH na
> verificação** ([[feedback-realismo-nao-otimismo]]) — detalhe abaixo.

## WATCH

### Qwen-Audio-3.0-TTS (arXiv 2607.23938) — a linhagem do nosso challenger evoluiu
- **O quê**: tech report do sucessor do Qwen3-TTS (Alibaba). Tokenizer supervisionado **12.5Hz (FSQ)** —
  converge com o frame rate do Mimi/CSM — **LM+FM acoplados por hidden-states contínuos** (estilo JoyVoice),
  receita de 5 estágios com **data annealing** (amplo → subset curado expressivo) e **GRPO com reward
  composto incluindo termo de prosódia/pausas** em rollouts token-only. #1 no leaderboard Artificial Analysis.
- **Por que WATCH e não TEST** (verificação adversarial): (1) a ação-âncora ("annealing com nosso dado
  curado") assume dado que não existe — o curado real é ~24min, e o fine-tune já treina só no subset limpo,
  não há gradiente amplo→curado na camada de voz; (2) nada executável em <1 semana com treino pausado;
  (3) DPO-antes-de-GRPO já é guardrail (`SWEEP_GUARDRAILS`), o reward com prosódia **confirma**, não muda;
  (4) modelo fechado, sem pesos — não muda o artefato fine-tunável do bake-off (`spine_qwen3_base`).
- **Resíduo que fica**: anotação de linhagem — o challenger evoluiu na direção que apostávamos (12.5Hz +
  FM decoder). **Gatilhos de re-triagem**: pesos abertos da linha 3.0; ou treino retomado com Estágio A
  sobrevivendo ao bake-off (aí annealing no CPT faz sentido, onde o gradiente amplo→curado existe).
- **PDF**: `research/papers/2607.23938-qwen-audio3-tts-recipe.pdf`

### Best-of-N TTS Evaluation is Confounded by ASR Family Alignment (arXiv 2607.08256)
- **O quê**: rerank Best-of-N com verificador ASR e medir WER com ASR da **mesma família** infla o
  resultado (self-bias de linhagem). Análogo ao self-bias de LLM-judge.
- **Regra que levamos** (vale hoje, mesmo sem BoN no pipeline): **qualquer filtro/reranking baseado em
  ASR** (anti-erosão de dado sintético, pares DPO por WER, curadoria) **deve usar ASR de família
  diferente da usada na eval**. Registrado como regra de protocolo de eval.
- **PDF**: `research/papers/2607.08256-bon-asr-confound.pdf`

### Zero-Shot Phonetic Classification via Articulatory Features (arXiv 2607.23606)
- **O quê**: classificadores frame-level de **traços articulatórios** língua-agnósticos capturam
  distinções fonéticas **não-fonêmicas** que G2P/Speech-to-IPA erram.
- **Por que watch**: é o tipo de instrumento pra detectar **alofones cariocas** (chiado do /s/ pós-vocálico,
  vocalização do /l/) objetivamente na saída do modelo → candidato futuro a módulo do **accent scorecard**
  (gap #1). Não é acionável em <1 semana; anotado na célula de eval.
- **PDF**: `research/papers/2607.23606-af-zeroshot-alofones-eval.pdf`

## SKIP (excluídos do disco)

| Paper | Por quê |
|---|---|
| OT-align p/ LLM-AVSR (2607.09001) | ASR audio-visual (leitura labial) — tarefa oposta; nada toca síntese/prosódia |
| MEUSLI projetor multilíngue ASR (2607.22100) | ASR não é nosso gargalo; Whisper já resolve pt-BR na cascata |
| ASR c/ discrete-diffusion LM (2607.13013) | ASR de novo; pior que Whisper e exige backbone 26B |
| Indic DiarBench (2607.23808) | recurso de diarização+ASR p/ línguas indianas; sem add-on transferível |
| DA-ICL correção ASR árabe (IEEE) | engenharia de prompt sobre ASR; WER já saturou como métrica pra nós |
| MSE-TTS emoção por imagem facial (IJCNN) | modalidade errada (imagem não existe no nosso loop) + spine VITS defasado |

## Padrão do lote

7 dos 9 eram **ASR/understanding** — o tracking da Sandra puxa muito o lado reconhecimento. O filtro
de arquitetura ([[feedback-arquitetura-nao-idioma]]) continua rendendo: o que sobra é exatamente o que
toca spine (Qwen 3.0), protocolo de eval (BoN-confound) e o gap #1 (traços articulatórios).
