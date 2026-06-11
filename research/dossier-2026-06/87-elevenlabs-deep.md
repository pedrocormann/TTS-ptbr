# 87 — ElevenLabs DEEP (FRENTE 1: OSINT competitivo)

**Data da coleta:** 2026-06-10 · **Método:** web search + fetch de fontes primárias
(elevenlabs.io/blog, elevenlabs.io/docs, github.com/elevenlabs, huggingface.co/elevenlabs,
podcast Sequoia "Training Data", Wikipedia, imprensa). Idioma: PT com **termos técnicos em EN**.
**Regra de confiança:** [P] = fonte primária (ElevenLabs ou autor direto) · [S] = secundária
confiável · [F] = fonte fraca (agregador/imprensa não-técnica — usar com cautela) ·
**[NV] = NÃO VERIFICÁVEL** (declarado mas sem prova independente, ou não encontrado).

**Disciplina do projeto:** estamos APRENDENDO com um concorrente FECHADO, não copiando código.
ElevenLabs é o 2o melhor do mercado em fala, em produção, com voice cloning fácil. O alvo de
referência MAIOR do projeto continua sendo Maya/Sesame (conversacional). Aqui extraímos
**método/arquitetura/engenharia reaproveitável** e separamos o que é só ruído de produto/business.

---

## 0. TL;DR técnico (o que importa pra nós)

1. **Arquitetura declarada (pela boca do CEO):** "**transformer diffusion** trazida para o
   espaço de áudio" + modelo de **dois inputs** (texto-como-contexto + voz-como-referência)
   com representação de voz por **encode/decode** (NÃO hard-coded por gênero/idade — o modelo
   decide as características). Isso é diferente da abordagem RVQ-codes-autoregressiva da
   Sesame/Kyutai. [P, Sequoia podcast]
2. **O moat REAL não é a arquitetura — é o data pipeline:** speech-to-text próprio que rotula
   "não só o que foi dito mas COMO foi dito" (emoção, não-verbais, quem falou), revisado por
   **voice coaches** humanos. O próprio CEO diz: *"data quality and labeling methodology would
   be more defensible than model architecture alone"*. **Esta é a lição número 1 pra nós.** [P]
3. **Latência:** Flash v2.5 = **~75ms model time**, **~135ms end-to-end TTFB** (time-to-first-byte
   de áudio). Conversational pipeline alvo **sub-500ms first-turn**, **sub-1s** no total. [P]
4. **Pipeline conversacional = cascading** (STT→LLM→TTS), não duplex. CEO admite que estão
   pesquisando um **"truly duplex model"** (como Moshi/Sesame) mas com trade-off
   **expressivity vs reliability** ainda não resolvido. **Confirma nossa tese:** duplex é o
   futuro, mas é difícil estabilizar. [P]
5. **Modelos menores que foundation models** → menos compute → conseguem competir. [P]
6. **Zero papers públicos, zero pesos abertos.** GitHub = só SDKs/clients. HF = só uma demo
   Space + uma "model card" de métricas de 2023. **Não há nada reaproveitável de código deles.**

---

## 1. PESSOAS / corpo técnico

### 1.1 Fundadores [P/S]

| Nome | Papel | Histórico pré-ElevenLabs | Formação |
|---|---|---|---|
| **Mati Staniszewski** | Co-founder / CEO | **Palantir** (Deployment Strategist, ~4 anos, desde 2018); antes BlackRock (Product Dev) e Opera Software (Business Intelligence) | Mathematics, First-Class, **Imperial College London** |
| **Piotr Dąbkowski** | Co-founder / CTO | **ex-Google** (ML engineer) | Engineering BA (Distinction) **Oxford**; MPhil Advanced CS **Cambridge** — pesquisa em **real-time image saliency**, publicada no **NeurIPS 2017** |

- Os dois se conhecem desde adolescentes na Copernicus High School, Varsóvia. Fundaram em
  2022. Motivação narrada: dublagem ruim de filmes destruindo a atuação original. [S: Wikipedia,
  Yahoo/Finance, CryptoRank]
- **Leitura técnica:** o CTO (Dąbkowski) tem background de **deep learning de verdade**
  (NeurIPS, saliency = mapas de atenção/interpretabilidade visual). O CEO é produto/deployment
  (Palantir = forward-deployed culture, daí o foco em "Forward Deployed Engineers" deles). A
  combinação importa: cultura de **research-perto-de-deploy** (ver 1.3).

### 1.2 Corpo de research / engenharia [NV em grande parte]

**Achado importante e honesto:** ElevenLabs mantém um **perfil de pesquisa público quase
invisível**. Buscas no arXiv por afiliação "ElevenLabs" **não retornam papers técnicos** deles
(verificado 2026-06-10). Não há VPs de research nomeados publicamente, nem "rockstar
researchers" com papers atribuídos à empresa. Isto **contrasta fortemente com a Sesame** (que
tem post de research com 8 autores nomeados e gente vinda de Google/MSR/Edinburgh CSTR).

- A empresa se autodescreve no GitHub como *"Research Lab. Exploring new frontiers of voice
  generation"* [P], mas **não publica**. O conhecimento fica fechado por design.
- Estrutura declarada pelo CEO: separam **researchers** de **research engineers** (estes
  "improving, changing, deploying at scale"), e mantêm um time de **voice coaches + data
  labelers treinados por voice coaches**. [P, Sequoia]
- **R&D center em Varsóvia** (Polônia) e escritório na Índia abertos recentemente. [F: catalaize
  substack]
- **Forward Deployed Engineers (FDE):** têm post de blog dedicado — cultura herdada do Palantir
  do CEO. [P: elevenlabs.io/blog/forward-deployed-engineers]

### 1.3 Saídas recentes de funcionários (2025-2026) [NV]

**NÃO ENCONTRADO.** Buscas específicas por departures de research/eng 2025-2026 não retornaram
nada verificável. Diferente da Sesame (onde Johan Schalkwyk saiu pra Meta em jun/2025, com
Bloomberg), **não achei rastro público de saídas técnicas relevantes da ElevenLabs**. Possíveis
razões: (a) empresa muito fechada, baixo perfil de imprensa de pessoas; (b) retenção alta por
equity (valuation $6.6B); (c) simplesmente não vazou. **NÃO INVENTAR — marcar como lacuna e
revigiar.** Único sinal de cultura: um VP de Sales avisou candidatos sobre "20x quota / muitas
horas" (TheNextWeb) — isso é **business/cultura, não técnico**.

> **Lacuna a vigiar:** se algum ex-ElevenLabs publicar paper em 2025-26 expondo o método de
> labeling emocional ou a "transformer diffusion" de áudio deles, é ouro pra nós.

---

## 2. ARQUITETURA (público / inferível)

### 2.1 O que o CEO REVELOU no podcast Sequoia "Training Data" [P — fonte mais rica]

Fonte: https://sequoiacap.com/podcast/training-data-mati-staniszewski/ (transcrição via fetch).
Estas são as declarações técnicas mais concretas que existem publicamente:

- **"Transformer diffusion into the audio space"** — atribuem a "human quality" a terem trazido
  diffusion + transformer pro áudio, com o modelo entendendo **contexto do texto** para ajustar
  tonalidade/emoção. *(Não detalham se é diffusion no espaço latente de áudio, num codec, ou em
  mel-spectrogram — [NV] no detalhe.)*
- **Modelo de dois inputs (dual-input):**
  > *"the text-to-speech model will take the context of the text as one input and the second
  > will take the voice as a second input. And based on the voice delivery, if it's more calm or
  > dynamic, both of those will merge together."*
  Ou seja: **um caminho de conteúdo (texto) + um caminho de identidade/estilo (voz de
  referência)**, fundidos. Conceitualmente similar a speaker-conditioning, mas eles enfatizam
  que a **entrega/prosódia da voz de referência** influencia o output.
- **Representação de voz por encode/decode, sem features hard-coded:**
  > *"rather than hard coding or predicting any specific features [like gender/age], we let the
  > model decide what the characteristic should be... using a decoding and coding way."*
  → Sugere um **voice encoder/embedding aprendido** (estilo speaker-embedding latente), não
  rótulos categóricos. **Relevante pra nós:** condiciona-se a voz por embedding contínuo, deixa
  o modelo aprender o espaço — bom pra sotaque/emoção sem taxonomia rígida.
- **Cascading vs Duplex (CONFIRMAÇÃO IMPORTANTE):**
  > Produção hoje = *"cascading model: speech-to-text, LLM, text-to-speech"* (3 peças).
  > Em pesquisa = *"truly duplex model"* onde *"the delivery is much better"* mas há
  > *"reliability versus expressivity trade-off"*. *"The true duplex model will always be
  > quicker, more expressive but less reliable."*
  → **Eles ainda NÃO entregam duplex em produção.** O alvo Maya/Sesame (duplex de verdade) está
  à frente nesse eixo específico. Mas eles compensam com qualidade de voz + data.
- **Modelos menores:** *"the models are smaller, so you don't need as much compute... you can
  still outcompete foundational models rather than [having] the compute disadvantage."*
- **Data como moat:** áudio de alta qualidade é escasso e raramente vem com transcrição precisa;
  por isso construíram pipeline próprio de labeling (transcript + emoção + não-verbais + speaker).

### 2.2 Família de modelos (de elevenlabs.io/docs/overview/models) [P]

| Modelo | Latência | Idiomas | Max chars | Uso / nota |
|---|---|---|---|---|
| **Eleven v3 (alpha)** | não declarada / alta (não streama) | **70+** | 5.000 | Mais expressivo; **audio tags** + Text-to-Dialogue multi-speaker. **NÃO suporta WebSocket streaming** → ruim pra real-time |
| **Multilingual v2** | não declarada | 29 | 10.000 | "Emotionally-aware"; consistência de voz entre idiomas |
| **Flash v2.5** | **~75ms model time** | **32** | 40.000 | **Real-time agents**; 50% mais barato/char; streaming |
| **Flash v2** | ~75ms | só inglês | 30.000 | Rápido/barato |
| **Turbo v2.5** | (deprecando) | — | — | Equivalente ao Flash; Flash tem latência menor em média |
| **Scribe v2** (STT) | — | **90+** | — | Word-level timestamps, **diarization até 32 speakers**, entity detection |
| **Scribe v2 Realtime** (STT) | **~150ms** | 90+ | — | Streaming + VAD + manual commit |
| **Eleven Music (music_v1)** | — | EN/ES/DE/JA+ | — | Geração de música, edição por seção |

### 2.3 Eleven v3 — controle de emoção por **Audio Tags** [P]

- Lançado **05/jun/2025** como alpha/research preview. https://elevenlabs.io/v3
- **Audio Tags** = diretivas inline entre colchetes que o modelo interpreta: `[excited]`,
  `[whispers]`, `[sighs]`, `[sarcastic]`, `[laughs]`, e até efeitos `[gunshot]`, `[clapping]`.
- **Text-to-Dialogue:** tece múltiplas vozes numa interação só, casando prosódia e pegando
  cues dos tags entre falantes.
- **Stability slider** (Creative / Natural / Robust) controla quão fiel à referência vs quão
  expressivo. Creative = mais emocional mas menos estável.
- **Trade-off crítico pra nós:** v3 é o mais expressivo MAS **não streama** (sem WebSocket) →
  latência alta em respostas longas → **inadequado pra voice agent real-time**. Eles usam Flash
  v2.5 pra real-time e v3 pra conteúdo. **Há uma tensão expressividade↔latência que eles ainda
  não unificaram num único modelo** — exatamente o problema que nosso projeto quer resolver.

### 2.4 Conversational AI / Agents Platform [P]

Fonte: https://elevenlabs.io/blog/how-do-you-optimize-latency-for-conversational-ai (fetch).
Breakdown de latência **aditiva** do pipeline cascading (ASR + VAD/turn-taking + LLM + TTS):

| Componente | Latência declarada |
|---|---|
| **ASR** (Whisper open) | ~300ms+ |
| **ASR** (custom ElevenLabs) | **<100ms** |
| **LLM** (Gemini Flash 1.5) | <350ms (first token) |
| **LLM** (GPT-4 / Claude) | 700–1000ms |
| **TTS Turbo** | ~300ms |
| **TTS Flash** | **75ms model / 135ms end-to-end TTFB** |
| **Telephony (mesma região)** | ~200ms |
| **Telephony (global)** | ~500ms |

**Princípios de engenharia que eles declaram (REAPROVEITÁVEL):**
- *"What matters most is the **first token latency**"* (TTFB do LLM) → streamar token-a-token
  pro TTS imediatamente. **Não esperar a frase inteira.**
- **Co-location:** ASR, VAD/TTI, LLM e TTS devem ficar **no mesmo lugar** (mesma região/host)
  pra cortar latência de rede entre componentes.
- **Async function calling:** fazer o LLM **responder ao usuário ANTES** de a function call
  terminar (via webhook) pra não deixar silêncio.
- Alvo: **sub-1s** total; **Conversational AI 2.0** declara **first-turn <500ms** + interrupt
  handling + call routing.
- **Turn-taking (TTI)** = processo intermediário que decide quando o usuário terminou de falar;
  modelo subjacente = **VAD (Voice Activity Detector)**. Configurável (timeouts, interrupções).

### 2.5 Streaming / WebSocket [P]

- TTS WebSocket endpoint = **bidirecional**, ideal pra input em tempo real (saída de LLM).
- **`chunk_length_schedule`**: array de inteiros = quantos caracteres mandar ao modelo antes de
  gerar áudio. **Trade-off:** chunks menores = TTFB menor mas pior continuidade prosódica;
  chunks maiores = melhor prosódia mas TTFB maior. **Isto é diretamente aplicável ao nosso
  buffering de streaming.**
- **v3 NÃO tem WebSocket** (nem multi-context) → mais uma confirmação de que expressividade
  máxima e streaming de baixa latência ainda são, na engenharia deles, **dois regimes
  separados**.

---

## 3. CLONAGEM DE VOZ (Instant vs Professional) [P]

Fontes: help.elevenlabs.io (IVC vs PVC) + elevenlabs.io/docs/.../voice-cloning.

| | **Instant Voice Cloning (IVC)** | **Professional Voice Cloning (PVC)** |
|---|---|---|
| Técnica | **Zero/few-shot adaptation**: usa o áudio como **conditioning signal no inference**. **NÃO atualiza pesos.** | **Fine-tuning**: **modifica os parâmetros** do modelo pra representar a voz-alvo |
| Áudio necessário | < 2 min (bom resultado já com 1–5 min) | **30 min mínimo, ~3h ótimo** (fine-tune leva 3–6h de processamento) |
| Consistência | Menos consistente longe do material de referência (voz calma clonada soa diferente se pedir emoção forte) | Mais consistente entre estilos; lida melhor com **range emocional** |
| Modelo criado? | Não cria modelo custom; "educated guess" a partir do prior | Sim, captura características mais profundas e tendências estilísticas |

**Leitura técnica (REAPROVEITÁVEL):**
- O **IVC = nosso "zero-shot via speaker embedding"** (condicionamento no inference). Confirma
  que ~1–5 min de áudio limpo dá clone usável SEM treino — caminho rápido pra protótipo pt-BR.
- O **PVC = fine-tune** com ~3h de áudio pra qualidade/consistência emocional máxima. Isto
  espelha exatamente a nossa estratégia de duas fases (zero-shot rápido → fine-tune da voz do
  Pedro com dataset robusto). **A faixa "~3h ótimo" valida nosso alvo de volume de gravação.**
- A admissão de que IVC "soa diferente quando se pede emoção forte" é a **fraqueza do zero-shot
  puro** — justifica investir no dataset com cobertura emocional (nosso protocolo de gravação).

---

## 4. GITHUB / HUGGINGFACE (open vs closed) [P]

### GitHub (github.com/elevenlabs) — ~25 repos, **TUDO client-side**:
- **elevenlabs-python** (~3k★), **elevenlabs-js** (~431★), **elevenlabs-swift-sdk**,
  **elevenlabs-flutter** — SDKs oficiais da API.
- **packages** (Agents SDK TypeScript), **elevenlabs-mcp** (~1.4k★, MCP server oficial),
  **cli** (CLI pra agents).
- **ui** (~2.3k★) — component library sobre shadcn/ui pra montar agentes multimodais.
- **examples**, **skills**.
- **VEREDITO:** **zero model code, zero training scripts, zero weights.** Útil só como
  referência de **API/SDK design e de como montam um agente** (orquestração), não de modelo.

### HuggingFace (huggingface.co/elevenlabs):
- **1 Space:** "ElevenLabs TTS" (demo hospedada, ~624 likes) — é interface, **não pesos**.
- **1 "model":** `elevenlabs/xi-metrics` (atualizado **mar/2023**) — métricas, não um TTS.
- **Datasets:** **nenhum** oficial. (Datasets "elevenlabs_*" no HF são de TERCEIROS que geraram
  áudio com a API — `skypro1111/elevenlabs_dataset`, `Sh1man/elevenlabs` — **não são da
  empresa**; cuidado com licença/origem se alguém pensar em usar.)
- **CONFIRMADO:** **nada open-weight.** Como esperado, a ElevenLabs é **100% fechada** no modelo.
  **Nada de código reaproveitável diretamente.** Só lições de método.

---

## 5. LATÊNCIA / STREAMING — números consolidados [P]

- **Flash v2.5:** 75ms model time · **135ms end-to-end TTFB** · 75–150ms p50 pra inputs <100 chars
  (streaming ligado, carga normal). 32 idiomas.
- **Custom ASR:** <100ms (vs Whisper ~300ms+). **Scribe v2 Realtime:** ~150ms.
- **Conversational 2.0:** first-turn <500ms; alvo total sub-1s.
- **Como conseguem:** modelo pequeno + streaming WebSocket + chunking (`chunk_length_schedule`)
  + co-location dos componentes + streamar no first-token do LLM + async function calls.
- **pt-BR (qualidade reportada):** [S/F — fontes secundárias, não benchmark independente forte]
  - ElevenLabs é repetidamente citada como **líder de mercado em pt-BR** por agregadores
    (Speechify, fluxnote, json2video).
  - Sotaque default = **"neutro (São Paulo)"**; afirmam adaptar a sotaques regionais. [P, página
    de produto — **alegação de marketing, não medida**]
  - Pontos de qualidade citados: ritmo melódico do PT-BR (≠ PT-PT) e pronúncia correta de
    **loanwords do inglês** (erro típico que denuncia TTS ruim). [F]
  - **NÃO ENCONTREI** benchmark independente com número (MOS/CMOS/WER) específico pra voz
    **carioca** ou pt-BR da ElevenLabs. **[NV]** — vale gerar amostras nossas e comparar no nosso
    eval harness (TTSDS2) em vez de confiar em marketing. **Nosso diferencial declarado (sotaque
    carioca) não é coberto pelo default "São Paulo" deles** — possível brecha.

---

## 6. ENTREVISTAS / TALKS do corpo técnico

| Fonte | Link | O que revela (técnico) |
|---|---|---|
| **Sequoia "Training Data" — Mati Staniszewski** | https://sequoiacap.com/podcast/training-data-mati-staniszewski/ | **A MELHOR fonte.** transformer diffusion no áudio; dual-input (texto+voz); encode/decode de voz sem features hard-coded; cascading vs duplex + trade-off reliability/expressivity; voice coaches + labeling como moat; modelos menores. |
| Apple Podcasts (mesmo ep.) | https://podcasts.apple.com/us/podcast/elevenlabs-mati-staniszewski-why-voice-will-be-the/id1750736528 | Áudio do acima. |
| Pigment "Perspectives" — Mati | https://www.pigment.com/perspectives-podcast/elevenlabs-mati-staniszewski-why-your-voice-will-be-the-new-ai-interface | Mais visão/produto; pouco técnico novo. [business] |
| Blog: optimizing latency for Conv AI | https://elevenlabs.io/blog/how-do-you-optimize-latency-for-conversational-ai | Breakdown de latência por componente (seção 2.4). **Muito técnico/útil.** |
| Blog: Conv AI latency w/ efficient TTS pipelines (07/abr/2026) | https://elevenlabs.io/blog/enhancing-conversational-ai-latency-with-efficient-tts-pipelines | Model selection, streaming, preloading, edge compute. |
| Blog: Meet Flash | https://elevenlabs.io/blog/meet-flash | Posicionamento do Flash, 75ms. |
| Blog: v3 Audio Tags (vários) | https://elevenlabs.io/blog/v3-audiotags · /eleven-v3-situational-awareness | Como funcionam os audio tags / situational awareness. |
| Blog: Forward Deployed Engineers | https://elevenlabs.io/blog/forward-deployed-engineers | Cultura FDE (herança Palantir). [business/cultura] |

---

## 7. SEPARAÇÃO FINAL

### [TÉCNICO reaproveitável] — o que levar pro projeto

1. **DATA PIPELINE É O MOAT, NÃO A ARQUITETURA.** Rotular áudio com **transcript + emoção +
   não-verbais + speaker**, com **humanos (voice coaches) revisando o labeling**. Investir aqui
   tem ROI maior que caçar arquitetura exótica. → reflete no nosso protocolo de gravação/labeling.
2. **Dual-input / condicionamento por embedding de voz aprendido** (sem rótulos hard-coded de
   gênero/idade). Deixar o modelo aprender o espaço de voz/estilo. Bom pra **sotaque carioca +
   emoção** sem taxonomia rígida.
3. **IVC = zero-shot (~1–5 min, conditioning no inference) ; PVC = fine-tune (~3h, melhor range
   emocional).** Valida nossa estratégia de 2 fases e o **alvo ~3h de gravação** da voz do Pedro.
   Fraqueza conhecida do zero-shot: emoção forte fora do material de referência → justifica
   cobertura emocional no dataset.
4. **Engenharia de latência:** streamar no **first-token** do LLM; **co-location** de
   STT/VAD/LLM/TTS; **chunking** com schedule (trade-off TTFB↔prosódia); async function calls;
   alvo **sub-500ms first-turn / sub-1s total**. Números-âncora: Flash **75ms model / 135ms TTFB**.
5. **Cascading vs Duplex:** mesmo o 2o-melhor do mercado **ainda não entrega duplex em produção**
   (trade-off reliability↔expressivity não resolvido). **Maya/Sesame está à frente nesse eixo.**
   → nosso aposta em duplex/full-duplex é a direção certa e é onde está a fronteira aberta.
6. **Tensão expressividade↔latência não unificada:** v3 (expressivo) NÃO streama; Flash (rápido)
   é menos expressivo. **Unificar os dois num modelo é exatamente o gap de mercado** — alvo nosso.
7. **Modelos menores batem foundation models** em áudio (menos compute). Reforça que dá pra
   competir sem cluster gigante — alinhado ao nosso "startup mode" / Colab.
8. **Brecha de sotaque:** default pt-BR deles é "neutro São Paulo". **Carioca não é foco deles**
   → nosso diferencial é defensável. Validar com nosso eval (TTSDS2), não com marketing.

### [PRODUTO / BUSINESS — só anotar, não poluir o foco]

- Valuation ~$6.6B, receita >$200M; CEO entrevista todo hire. [F]
- R&D em Varsóvia + escritório na Índia. Cultura FDE (Palantir). VP Sales "20x quota". [F]
- Investidor anjo: Mustafa Suleyman (DeepMind). [S]
- Posicionamento "voz será a interface fundamental da tecnologia". [P, marketing]
- Líder de mercado percebido em pt-BR (agregadores). [F]
- Eleven Music, Scribe (STT 90+ idiomas, diarization 32 speakers) — expansão de portfólio.

---

## 8. LACUNAS / NÃO-VERIFICÁVEL (vigiar)

- **[NV] Saídas de funcionários técnicos 2025-26** — não encontrado. Empresa muito fechada.
- **[NV] Nomes de researchers/VPs de research** — não publicam; sem arXiv com afiliação deles.
- **[NV] Detalhe da "transformer diffusion"** — não dizem se é diffusion em latente de codec,
  mel, ou waveform; nem se o backbone TTS é AR ou não-AR. Só a frase do CEO.
- **[NV] Benchmark independente de pt-BR carioca** (MOS/WER) — não achei número sólido; gerar
  o nosso.
- **[NV] Patentes** — não localizei patente técnica deles nesta rodada (não confirmado nem
  negado). Revigiar se relevante.

---

### Fontes primárias citadas
- https://sequoiacap.com/podcast/training-data-mati-staniszewski/ (entrevista CEO — mais rica)
- https://elevenlabs.io/blog/how-do-you-optimize-latency-for-conversational-ai
- https://elevenlabs.io/docs/overview/models
- https://elevenlabs.io/v3 · https://elevenlabs.io/blog/v3-audiotags · /blog/meet-flash
- https://help.elevenlabs.io/hc/en-us/articles/13313681788305- (IVC vs PVC)
- https://elevenlabs.io/docs/eleven-api/concepts/voice-cloning
- https://github.com/elevenlabs · https://huggingface.co/elevenlabs
- https://en.wikipedia.org/wiki/ElevenLabs (fundadores)
