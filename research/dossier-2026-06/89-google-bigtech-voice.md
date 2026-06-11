# Dossiê 89 — Google + Big Tech: voz de baixa latência com SOTAQUES (FRENTE 3)

> Data da pesquisa: **2026-06-10**. Investigação OSINT sobre como Google e demais
> big techs fazem **voz conversacional, baixa latência, full-duplex e sotaque**.
> Disciplina: extrair **MÉTODO / ARQUITETURA / ENGENHARIA reaproveitável** — não
> fofoca de mercado. Nada aqui é cópia de código (tudo fechado); estamos
> **aprendendo o método**. Restrição dura do produto TTS-ptbr continua: só
> Apache-2.0 / MIT / CC-BY / CC0. Referência MAIOR do projeto: **Sesame Maya**.
>
> Marcação honesta: `[VERIFICADO]` = fonte primária; `[INFERÊNCIA]` = dedução
> minha; `[NÃO-VERIFICÁVEL]` = não achei fonte primária. **Separo `[TÉCNICO]` de
> `[PRODUTO]`** explicitamente, como pedido.

---

## 0. TL;DR — o que isto ensina para o TTS-ptbr

1. **A arquitetura vencedora é "native audio" (speech-to-speech num único modelo)**,
   não cascade STT→LLM→TTS. Google (Gemini Live) e OpenAI (Realtime) convergiram
   nisto. É exatamente o paradigma do nosso spine (Moshi/CSM: tokens de áudio
   interleaved). Confirma a trilha.
2. **O método de baixa latência de longa data do Google é SoundStorm**: decoding
   **paralelo não-autoregressivo, estilo MaskGIT, confidence-based** sobre tokens
   RVQ — **100× mais rápido** que AR para sequências longas. Esse é o truque de
   engenharia central, e é replicável conceitualmente.
3. **Sotaque na big tech hoje = duas escolas**: (a) **prompt / audio tags em
   linguagem natural** (Gemini 3.1 Flash TTS, Chirp 3 HD, gpt-realtime — "fale
   com sotaque X"); (b) na **literatura aberta**, **accent embedding com controle
   de intensidade** (multiplicar o embedding por um coeficiente). A escola (b) é a
   que nos ensina o método técnico reaproveitável para o **carioca**.
4. **Ninguém da big tech entrega sotaque REGIONAL pt-BR de verdade** (carioca,
   paulista, nordestino) como recurso primário e documentado. Quem oferece isso
   são **agregadores de produto** (Notevibes, SpeechGen) — sem método publicado.
   Isso é uma **lacuna de mercado** e tecnicamente um diferencial possível pra nós.
5. **Números de latência-alvo concretos** para calibrar nossa meta: OpenAI mira
   **~800 ms voice-to-voice** com **~300 ms** de orçamento de endpointing; áudio
   24 kHz, barge-in por cancelamento de resposta. Use como baseline de SLA.

---

# PARTE A — GOOGLE

## A.1 [PRODUTO] O anúncio recente de "voz com sotaques" — o que é, exatamente

Há **três produtos distintos** do Google que tocam "voz + sotaque + baixa latência",
e é importante não confundi-los:

### (i) Gemini 3.1 Flash TTS — o anúncio de SOTAQUES (15/abr/2026)
[VERIFICADO] É o modelo de **text-to-speech** (não conversacional) lançado em
**15 de abril de 2026**. É o "anúncio de sotaques" a que a tarefa se refere.
Promessas oficiais/divulgadas:
- **70+ línguas** + **variações regionais de sotaque**, incluindo **múltiplos
  sotaques de inglês** (American, RP britânico, etc.).
- **30 vozes distintas**, **diálogo multi-speaker nativo**.
- **"Director-Level Voice Control"** via **inline audio tags**.
- Disponível em Gemini API, Google AI Studio, Vertex AI, Google Vids.
- Specs oficiais (doc): `gemini-3.1-flash-tts-preview`, input 8.192 tokens,
  output 16.384 tokens, suporta Batch API; **não** suporta function calling /
  caching / thinking. Knowledge cutoff jan/2025, update abr/2026.

[NÃO-VERIFICÁVEL — importante] A **doc oficial não lista as línguas** nem confirma
explicitamente **pt-BR** nesta página específica; remete a um "Text-to-Speech
guide". As fontes secundárias dizem "70+ línguas" mas **não vi fonte primária
nomeando português/pt-BR como sotaque regional suportado**. Tratar pt-BR como
**provável mas não confirmado em fonte primária** até teste de escuta.
Fontes: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview ·
https://blog.google/products/gemini/gemini-audio-model-updates/ ·
https://www.eweek.com/news/gemini-3-1-flash-tts-ai-voice-languages-accents/

### (ii) Cloud TTS — Chirp 3: HD voices — o TTS de produção do Google Cloud
[VERIFICADO] É a linha de produção (API Cloud TTS). Relevante porque **confirma
pt-BR**:
- **`pt-BR` (Português do Brasil) ESTÁ na lista**; pt-PT NÃO está. 60+ locales.
- 8 vozes "personalidade" (Puck, Charon, Fenrir, Orus / Aoede, Kore, Leda, Zephyr).
- **Controle**: `speaking_rate` (0.25x–2.0x), **markup de pausa**
  (`[pause short]`, `[pause long]`, `[pause]`), **custom pronunciations** (IPA /
  X-SAMPA), e SSML em preview (`<prosody>`, `<phoneme>`, `<break>`, etc.).
- **Streaming** suportado (`streaming_synthesize()`, formatos ALAW/MULAW/OGG_OPUS/PCM).
- Sotaque/emoção: NÃO há parâmetro dedicado — controla-se por **scripting/prompting
  e pontuação** + re-síntese iterativa.
- Há ainda **Chirp 3: Instant Custom Voice** (clonagem de voz instantânea) —
  detalhes técnicos não documentados na página principal.
- **Latência não documentada** na doc.
Fonte: https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd ·
https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types

### (iii) Gemini Live / Gemini 2.5 Native Audio — o conversacional em tempo real
Coberto na PARTE B. É o "voz ao vivo com baixa latência e interrupção".

> **Resumo do PRODUTO Google**: o "anúncio de sotaques" = **Gemini 3.1 Flash TTS
> (abr/2026)**, controle por **audio tags inline em linguagem natural**. pt-BR
> está garantido só no **Chirp 3 HD (Cloud TTS)**, não confirmado no 3.1 Flash TTS.

---

## A.2 [TÉCNICO] A tecnologia por trás — a linhagem que ENSINA método

O Google não publica a arquitetura exata do Gemini 3.1 / Live, mas a **linhagem de
papers** revela os métodos centrais. Esta é a parte de ouro do dossiê.

### A.2.1 SoundStorm (2305.09636) — o método de BAIXA LATÊNCIA [VERIFICADO]
**O truque central de engenharia de velocidade do Google.**
- Gera tokens de áudio com **decoding paralelo, não-autoregressivo, confidence-based,
  inspirado em MaskGIT** — sobre sequências de tokens **RVQ** (residual vector
  quantization) do SoundStream.
- Arquitetura: **Conformer bidirecional** treinado para prever tokens mascarados,
  condicionado em tokens semânticos (do AudioLM).
- Inferência estilo MaskGIT: começa de tokens mascarados; a cada rodada prevê uma
  fração dos tokens com **maior confiança**; o schedule aumenta a fração por
  iteração. Poucas iterações → áudio completo.
- **Resultado: ~100× mais rápido que o decoding AR** do AudioLM em sequências
  longas, com qualidade igual e **maior consistência** de voz/condições acústicas.
- **REUSO PRA NÓS**: este é o porquê de modelos modernos atingirem TTFA baixo.
  Nosso spine (Moshi/Mimi/CSM) é AR no backbone + decoder pequeno; o ensinamento
  do SoundStorm é que **a etapa acústica pode ser não-AR e paralela** para cortar
  latência. Mesmo sem implementar SoundStorm, a lição vale: **minimize passos AR
  na cadeia acústica; paralelize os codebooks residuais.**
Fontes: https://arxiv.org/abs/2305.09636 ·
https://research.google/blog/soundstorm-efficient-parallel-audio-generation/

### A.2.2 AudioLM (2209.03143) — o paradigma de tokens hierárquicos [VERIFICADO]
A base conceitual de "áudio = modelagem de linguagem sobre tokens".
- **Dois tipos de token**: **semantic tokens** (de w2v-BERT, self-supervised —
  capturam fonética + estrutura de longo prazo) e **acoustic tokens** (do codec
  SoundStream — capturam identidade do falante, condições de gravação, detalhe fino).
- **Estrutura hierárquica** dos acoustic tokens (RVQ): quantizadores grossos =
  identidade/condições; finos = detalhe acústico.
- **Modelagem em 3 estágios encadeados** (um Transformer por estágio):
  (i) semantic → coerência de longo prazo; (ii) coarse acoustic condicionado no
  semantic; (iii) fine acoustic.
- **REUSO PRA NÓS**: é exatamente a decomposição semantic/acoustic que o **Mimi**
  (split-RVQ do Sesame/Kyutai: 1 codebook semântico + N-1 acústicos) usa. Confirma
  que nosso tokenizer está na linhagem certa. **Sotaque vive predominantemente no
  estágio semântico/fonético + nos coarse acoustic tokens** — então conditioning
  de sotaque deve entrar cedo na cadeia.
Fonte: https://arxiv.org/abs/2209.03143 ·
https://research.google/blog/audiolm-a-language-modeling-approach-to-audio-generation/

### A.2.3 Translatotron 3 / linhagem S2ST (2305.17547) — preservar paralinguística [VERIFICADO]
Relevante por **método de speech-to-speech direto** (sem texto intermediário):
- Encoder-decoder **direto** sobre spectrograma, **bypass de texto** → reduz
  latência e propagação de erro do cascade.
- Translatotron 3: treino **totalmente não-supervisionado** (masked autoencoder +
  SpecAugment + mapeamento de embeddings MUSE + reconstruction loss por
  back-translation). **<0.5s de latência** reportada.
- **Insight reusável**: S2ST direto **preserva e transfere** características
  para-/não-linguísticas — **estilo de fala, emoção, ênfase, fonação, vocal
  bursts** — que o cascade perde. É a justificativa técnica de por que "native
  audio" soa mais humano e **carrega sotaque/emoção naturalmente**.
Fonte: https://arxiv.org/pdf/2305.17547 ·
https://research.google/blog/introducing-translatotron-an-end-to-end-speech-to-speech-translation-model/

> **Cadeia mental do Google**: AudioLM (tokens hierárquicos) → SoundStorm
> (geração paralela rápida) → produtos (Chirp 3 HD, Gemini native audio).
> Translatotron mostra o ganho de "direto vs cascade". É o blueprint de **baixa
> latência + preservação de paralinguística** que queremos.

---

# PARTE B — GEMINI LIVE / NATIVE AUDIO (conversa ao vivo)

## B.1 [TÉCNICO] Arquitetura: native audio, não cascade [VERIFICADO]
- O Google afirma que o Gemini 2.5 **"raciocina e gera fala nativamente em áudio"** —
  colapsa o stack `transcribe→reason→synthesize` num **único processo
  audio-to-audio**, reduzindo latência e permitindo reconhecer pitch/pace naturais.
- **Full-duplex / barge-in**: a Live API usa **WebSockets (WSS)** para comunicação
  **full-duplex**, permitindo **interrupção do usuário (barge-in)** e transmissão
  simultânea de áudio, frames de vídeo e transcripts. Quando o usuário fala durante
  a fala do modelo, a resposta em curso é cancelada.
- **Proactive audio**: "context awareness" — o modelo **discerne e ignora** fala de
  fundo / conversas ambientes, respondendo só quando apropriado. (É VAD/turn-taking
  semântico, não só energético.)
- **Affective dialog**: responde ao **tom de voz** do usuário (as mesmas palavras
  ditas diferente → conversa diferente).
- **Controlabilidade de estilo**: dá pra **dirigir sotaque, tom, expressões, e até
  sussurro** dentro da conversa; controle de speech rate e pronúncia; multi-speaker.
- **Línguas**: 24+ línguas, pode **misturar línguas na mesma frase**.
- **Watermark**: toda saída leva **SynthID**.
- [NÃO-VERIFICÁVEL] As fontes oficiais **não dão número de ms** de latência ("very
  low latency"), nem confirmam SoundStorm/AudioLM por baixo do Live (é [INFERÊNCIA]
  que a linhagem SoundStorm está envolvida).
Fontes: https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-2-5-native-audio/ ·
https://cloud.google.com/blog/topics/developers-practitioners/how-to-use-gemini-live-api-native-audio-in-vertex-ai ·
https://ai.google.dev/gemini-api/docs/live-api/capabilities

## B.2 [PRODUTO] Evolução de produto do Live (linha do tempo)
- **Gemini 2.5 Flash Native Audio**: **30 vozes HD em 24 línguas**, qualidade
  "como falar com uma pessoa".
- **Gemini 3.1 Flash Live** (~mar/2026): modelo multimodal real-time para voz +
  vídeo + tool-use de baixa latência para agentes.
- **Novas vozes Gemini Live** (27/mai/2026): "Flare" e "Glow" substituem Nova/Lyra;
  voice picker virou lista. [PRODUTO puro — não ensina método.]
- **Gemini 3.5 Live Translate** (09/jun/2026): tradução de fala **contínua**, 70+
  línguas / 2000 pares, **alguns segundos atrás** do falante, **preservando
  intonação, ritmo e pitch**. ComplexFuncBench Audio 71.5%; adesão a instruções 90%.
  [TÉCNICO relevante: "ficar segundos atrás preservando prosódia" = streaming S2ST
  com style transfer, linhagem Translatotron.]
Fontes: https://blog.google/products-and-platforms/products/gemini/gemini-live-audio-updates/ ·
https://www.marktechpost.com/2026/03/26/google-releases-gemini-3-1-flash-live-... ·
https://9to5google.com/2026/05/27/new-gemini-live-voices/

---

# PARTE C — OUTROS BIG TECH (só o que ensina MÉTODO)

## C.1 OpenAI Realtime API / gpt-realtime [TÉCNICO — alta densidade de números]
A fonte mais útil para **calibrar metas de latência e protocolo**.
- **Arquitetura**: speech-to-speech **num único modelo** — `[audio in] → GPT-4o →
  [audio out]` — sem cascade. `gpt-realtime` é o modelo S2S "production-ready".
- **Números (via Latent Space, análise técnica) [VERIFICADO secundário]**:
  - **TTFB ~500 ms** de clientes nos EUA.
  - **Alvo voice-to-voice ~800 ms** para conversa natural.
  - **Orçamento de endpointing ~300 ms** restante após inferência.
  - **VAD silence default 500 ms** (`silence_duration_ms`).
  - Áudio **24 kHz, 16-bit**; suporte G.711 (telefonia); **~800 tokens/min** de áudio.
  - **Turn detection**: server-side VAD configurável; modo manual via
    `input_audio_buffer.commit` + `response.create`.
  - **Interrupção (barge-in)**: ao detectar fala do usuário, **cancela a resposta
    em curso e dá flush** no áudio; `conversation.item.truncate` para alinhar o
    contexto ao que o usuário realmente ouviu.
  - **Protocolo**: WebSocket stateful, 9 eventos cliente / 28 eventos servidor;
    cliente mínimo ~75 linhas Python; sessão limitada a 15 min, contexto 128k.
- **Sotaque/voz/persona**: definidos por **system/developer instructions em
  linguagem natural** ("leia disclaimers ao pé da letra", troca de língua mid-sentence).
- **REUSO PRA NÓS**: adote **~800 ms voice-to-voice** como SLA-alvo e **~300 ms**
  de orçamento de turn-taking; implemente **barge-in por cancelamento+truncate**;
  24 kHz é o sample rate de referência.
Fontes: https://openai.com/index/introducing-the-realtime-api/ ·
https://openai.com/index/introducing-gpt-realtime/ ·
https://www.latent.space/p/realtime-api (números de ms; **secundário, não-oficial**)

## C.2 Microsoft — VALL-E 2 (2406.05370) [TÉCNICO]
Não é produto conversacional, mas ensina **dois truques de eficiência/robustez**:
- **Repetition Aware Sampling**: refina o nucleus sampling considerando repetição
  de tokens no histórico de decode → **menos travas/loops**, mais robustez.
- **Grouped Code Modeling**: agrupa os códigos do codec em grupos para **encurtar a
  sequência** → **acelera inferência** e ajuda em sequência longa.
- Primeira reivindicação de **human parity** em zero-shot TTS (LibriSpeech/VCTK).
- **REUSO PRA NÓS**: "repetition aware sampling" é barato de portar e ataca um
  problema real de codec-LM (repetição/alucinação acústica). "Grouped code
  modeling" é uma alavanca de latência além do SoundStorm.
Fonte: https://arxiv.org/abs/2406.05370 ·
[PRODUTO/Microsoft Azure TTS: vozes neurais multilíngues com pt-BR, controle por
SSML/estilo — não achei método novo publicado além do SSML; sem ganho técnico novo.]

## C.3 Amazon [PRODUTO, baixo sinal]
[NÃO-VERIFICÁVEL/baixo sinal] Amazon Polly tem pt-BR (Camila/Vitória/Thiago) com
estilo neural e SSML, mas **nada de método de baixa-latência/sotaque regional
publicado** que ensine algo novo. Sem achados técnicos reaproveitáveis nesta rodada.

---

# PARTE D — SOTAQUE: como modelam tecnicamente (o coração da FRENTE 3)

## D.1 [TÉCNICO] Duas escolas de controle de sotaque

### Escola 1 — Prompt / audio tags em linguagem natural (o que a big tech EXPÕE)
- **Gemini 3.1 Flash TTS**: **inline audio tags em colchetes**, posicionados antes
  do trecho a afetar. Exemplos verificados de sintaxe:
  `[whispers]`, `[screams]`, `[laughs]`, `[cackles]`, `[slow]`, `[fast]`,
  `[short pause]`, `[long pause]`, `[determination]`, `[enthusiasm]`, `[uhm]`.
  **200+ tags** cobrindo emoção, interjeição, pacing, performance. Regra: tag
  imediatamente antes da frase-alvo; não colar duas tags adjacentes.
  Sotaque é pedido por **instrução em linguagem natural / tag**, não por embedding
  exposto. (Ex.: "cowboy accent", "Cockney British" no Gemini app.)
- **gpt-realtime / Gemini Live**: sotaque por **instrução em linguagem natural**.
- **Chirp 3 HD**: sotaque por **scripting/pontuação**, sem parâmetro dedicado.
- **Limitação**: nenhum desses expõe **accent embedding** ou **intensidade**
  controlável; é "black box" guiada por prompt. Bom pra produto, pobre pra
  controle fino e para sotaque **regional** específico.
Fontes: https://www.mindstudio.ai/blog/gemini-3-1-flash-tts-controllable-text-to-speech ·
https://devradar.dev/radar/gemini-3-1-tts-audio-tags-guide

### Escola 2 — Accent embedding + intensidade (a literatura ABERTA — REUSÁVEL) [TÉCNICO]
Esta é a escola que **nos ensina como construir o carioca de verdade**. Métodos da
pesquisa recente (2024–2026):
- **AccentBox / accent embedding como conditioning**: extrai e **promedia
  embeddings** de enunciados com label de sotaque (ex.: do CommonVoice) e usa como
  sinal de condicionamento. Sotaque vira um vetor.
- **"Scalable Controllable Accented TTS" (2508.07426)** [VERIFICADO]:
  - **Accent encoder** extrai embeddings de sotaque de áudio de referência usando
    **modelos self-supervised (WavLM / XLS-R)** — não usa labels categóricos rígidos.
  - **Accent conditioner** injeta o embedding no modelo acústico; vocoder HiFiGAN-style.
  - **Controle de intensidade**: **multiplicar o accent embedding por um coeficiente
    [0, 2+]** → amplifica/atenua o quão forte o sotaque aparece, **sem re-treinar**.
  - **Escalável** porque usa features self-supervised (menos dado rotulado) e
    conditioning **modular** (reusável entre modelos acústicos).
  - Datasets: Common Voice, L2-Arctic, VCTK.
- **MLVAE + adversarial training**: usa **Multi-Level VAE** com treino adversarial
  para **desemaranhar (disentangle) sotaque de identidade do falante** — crucial
  para "voz do Pedro com sotaque carioca controlável" sem misturar timbre e sotaque.
- **Controle de intensidade fino/grosso** (utterance + phoneme level) existe na
  literatura.
- **REUSO PRA NÓS (carioca)**: o caminho técnico é
  **(1)** coletar áudio carioca rotulado/identificável; **(2)** extrair um
  **accent embedding** via WavLM/XLS-R (self-supervised, casa com nossa stack);
  **(3)** condicionar o modelo acústico nesse vetor, **disentangling** sotaque de
  timbre (estilo MLVAE); **(4)** expor um **coeficiente de intensidade** para
  dosar "quão carioca". Isso é **superior ao prompt** porque dá controle contínuo,
  regional e reprodutível — exatamente o diferencial que a big tech NÃO entrega.
Fontes: https://www.arxiv.org/pdf/2508.07426 ·
https://arxiv.org/html/2601.14417v2 (speaker-embedding × regras fonológicas) ·
https://arxiv.org/pdf/2409.09352 (MacST, transliteração p/ accent conversion) ·
https://arxiv.org/pdf/2506.16310 (multilingual TTS com accent code switching)

## D.2 [PRODUTO] Quem faz sotaque REGIONAL pt-BR de verdade?
[VERIFICADO — mas fontes de produto, sem método]
- **Big tech: ninguém** documenta sotaque regional pt-BR (carioca/paulista/
  nordestino) como recurso primário. Google/OpenAI/MS dão "pt-BR genérico" +
  prompt de sotaque genérico ("cowboy"), não regional brasileiro.
- **Agregadores de produto SIM**:
  - **Notevibes**: declara **4 sotaques** — Paulista, Carioca, Mineiro, Nordestino.
  - **SpeechGen**: marcadores regionais carioca/paulistano/nordestino, 118 vozes;
    cita features fonéticas (R gutural carioca vs Lisboa, nasais, nh/lh).
  - Sem **nenhum método publicado** (caixa-preta de produto).
- **LACUNA / OPORTUNIDADE**: sotaque carioca **controlável, com intensidade,
  open-weights (Apache/MIT/CC)** e conversacional **não existe** na big tech nem
  como recurso aberto. É um wedge técnico real para o TTS-ptbr.
Fontes: https://notevibes.com/brazilian-portuguese-text-to-speech/ ·
https://speechgen.io/en/tts-portuguese-brazil/

---

# PARTE E — Sesame (referência MAIOR) vs Google: o que difere no MÉTODO [TÉCNICO]
Para contexto do projeto (Sesame Maya é a referência maior):
- **CSM/Maya**: backbone **Llama** + audio decoder menor, tokens **text+audio
  interleaved**, tokenizer **Mimi** (split-RVQ: 1 semântico + N-1 acústicos, 12.5 Hz).
  Backbone prevê codebook 0; decoder amostra 1..N-1; áudio realimentado AR.
  Decoder pequeno → **baixa latência mantendo end-to-end**. Maya **"match accents"**,
  ajusta tom emocional, mantém pronúncia entre turnos. Meta declarada: **full-duplex**
  aprendendo turn-taking/pausas **implicitamente dos dados**.
- **Convergência com Google**: mesma decomposição **semantic/acoustic** do AudioLM;
  mesma filosofia **native audio**; mesma meta full-duplex do Gemini Live.
- **Divergência de método**: Google usa **SoundStorm (não-AR paralelo)** para a
  etapa acústica; CSM usa **decoder AR pequeno**. Para latência, o ensinamento
  combinado é: **backbone semântico AR enxuto + etapa acústica paralela/leve**.
Fontes: https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice ·
https://github.com/SesameAILabs/csm · https://huggingface.co/sesame/csm-1b

---

# PARTE F — Implicações diretas para o roadmap TTS-ptbr

[TÉCNICO]
1. **Latência**: fixar SLA conversacional em **~800 ms voice-to-voice** (OpenAI) com
   **~300 ms** de turn-taking; áudio **24 kHz**; barge-in por **cancelar+truncate**.
2. **Sotaque carioca = accent embedding + intensidade** (escola 2), não prompt.
   Extrair embedding via **WavLM/XLS-R**, condicionar o acústico, **disentangle**
   timbre (Pedro) × sotaque (carioca) estilo **MLVAE**, expor **coeficiente de
   intensidade**. Diferencial que a big tech não tem.
3. **Etapa acústica**: avaliar geração **não-AR/paralela** (lição SoundStorm) e
   **grouped code modeling** + **repetition-aware sampling** (VALL-E 2) como
   alavancas de latência/robustez sobre o spine Moshi/CSM.
4. **Tags expressivas inline** (estilo Gemini `[whispers]`/`[laughs]`) são um bom
   **UX de controle de emoção** — barato de adotar como interface, ortogonal ao
   accent embedding.
5. **SynthID/watermark**: big tech marca tudo; considerar watermark próprio é
   higiene de produto (não bloqueia licença aberta).

[PRODUTO]
6. Posicionamento: **"carioca controlável, open-weights, conversacional"** é
   território vazio. Big tech só dá pt-BR genérico; agregadores dão sotaque sem
   controle/abertura. Wedge claro.

---

## Apêndice — Mapa de verificabilidade
- **VERIFICADO (primária)**: SoundStorm (arXiv+blog Google), AudioLM (arXiv+blog),
  Translatotron 3 (arXiv+blog), VALL-E 2 (arXiv/MS), Chirp 3 HD pt-BR (doc Cloud),
  specs do `gemini-3.1-flash-tts-preview` (doc), tags Gemini 3.1 (doc/AI Studio),
  Gemini 2.5 native audio capabilities (blog Google), CSM/Mimi (repo+HF),
  "Scalable Controllable Accented TTS" (arXiv 2508.07426).
- **VERIFICADO secundário (não-oficial)**: números de ms do OpenAI Realtime
  (Latent Space). Confiança média — usar como ordem de grandeza.
- **NÃO-VERIFICÁVEL**: pt-BR explícito no Gemini 3.1 Flash TTS; latência em ms do
  Gemini Live; uso confirmado de SoundStorm dentro do Gemini Live (inferência);
  método dos agregadores (Notevibes/SpeechGen) de sotaque regional.
- **NÃO INVENTAR**: nenhum número de latência foi atribuído ao Google em ms (não há
  fonte). Sotaque regional pt-BR na big tech: **não encontrado em fonte primária**.

_Fim do Dossiê 89._
