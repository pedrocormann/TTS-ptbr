# 88 — Inworld AI + Voice.ai (FRENTE 2: concorrentes de voz de baixa latência)

**Projeto:** TTS-ptbr — fala conversacional pt-BR nível Maya/Sesame, baixa latência, emoções, sotaque carioca.
**Data da pesquisa:** 2026-06-10
**Disciplina:** extrair MÉTODO/ARQUITETURA/ENGENHARIA reaproveitável. Aprender com concorrentes fechados, **sem copiar código**. Termos técnicos em inglês, explicação em português.
**Aviso de honestidade:** quando algo não é verificável por fonte primária, está marcado como **[NÃO-VERIFICÁVEL]**. Nada foi inventado.

---

## TL;DR (resumo de bolso)

- **Inworld AI** é o achado técnico forte desta frente. Pivotou de "NPCs de jogos" (parceria Xbox 2023) para **realtime voice AI lab**. O **Inworld TTS-1** é um **LLM-based autoregressive TTS** (backbone LLaMA) com **codec X-codec2 + super-resolution a 48 kHz**, treino em 3 estágios (**pre-training → SFT → GRPO RL alignment**), e — crucial para nós — **código aberto sob licença MIT** (`github.com/inworld-ai/tts`). A engenharia de serving (parceria com **Modular/MAX + Mojo**) atinge **~200 ms time-to-first-audio**. Isso é diretamente estudável e a arquitetura é exatamente a família "LLaSA-style" que o nosso projeto pode reproduzir.
- **Voice.ai** é tecnicamente **outra categoria**: é primariamente um **real-time voice changer baseado em RVC** (Retrieval-based Voice Conversion) — ou seja, **voice-to-voice conversion**, não TTS-from-text como produto-core. O aprendizado aqui é o **pipeline RVC** (HuBERT/ContentVec → FAISS top1 retrieval → VITS/NSF-HiFiGAN) com **latência end-to-end de 90–170 ms** real-time. Útil como referência de **conversão de timbre de baixa latência**, não de síntese conversacional.

---

# PARTE 1 — INWORLD AI

## 1.1 [PRODUTO] O que é / foco

- Fundada em **2021** por **Kylan Gibbs (CEO)** + co-fundadores; time fundador "liderou produto de LLMs na DeepMind e construiu o **Dialogflow**" (plataforma de IA conversacional adquirida pelo Google). **Chief Science Officer: Igor Poletaev**. Fonte: [What is Inworld AI](https://inworld.ai/resources/what-is-inworld-ai).
- **Funding:** mais de **US$125M** de Lightspeed, Section 32, Kleiner Perkins, Founders Fund, CRV, Stanford, Intel Capital, **Microsoft M12**, **Meta**, **Samsung NEXT**, LG, Bitkraft. Fonte: search agregado / [LinkedIn Inworld](https://www.linkedin.com/company/inworld-ai). *(Valor agregado é auto-reportado; tratar como ordem de grandeza.)*
- **Pivô estratégico:** começou como engine de **NPCs dinâmicos para jogos** (memória, conhecimento, controle narrativo — ver [Voices of VR #1264](https://voicesofvr.com/1264-inworld-ai-for-dynamic-npc-characters-with-knowledge-memory-robust-narrative-controls/)). Em 2023 fez **parceria multi-ano com Xbox/Microsoft** para um "AI design copilot" + "AI character runtime engine" ([anúncio Microsoft](https://developer.microsoft.com/en-us/games/articles/2023/11/xbox-and-inworld-ai-partnership-announcement/)). Em **2025** reposicionou-se como **"Realtime Voice AI Research Lab"**, oferecendo TTS, STT e speech-to-speech via Realtime API ([what-is-inworld-ai](https://inworld.ai/resources/what-is-inworld-ai)).
- **Para nós:** o pivô confirma a tese do projeto — a camada de **voz realtime conversacional** é onde está o valor defensável, não o "personagem"/wrapper.

## 1.2 [TÉCNICO] Inworld TTS-1 / TTS-1-Max — arquitetura

Fonte primária: **TTS-1 Technical Report**, [arXiv:2507.21138](https://arxiv.org/html/2507.21138v1), e o repo MIT [github.com/inworld-ai/tts](https://github.com/inworld-ai/tts).

**Família de modelos (Transformer-based autoregressive TTS):**
- **TTS-1** — backbone **LLaMA-3.2-1B**, **1.6B** parâmetros totais. Foco em **real-time** e **on-device**.
- **TTS-1-Max** — backbone **LLaMA-3.1-8B**, **8.8B** parâmetros totais. Foco em qualidade/expressividade máxima.

**Speech codec / tokenização:**
- **Audio codec construído sobre a arquitetura X-codec2** com um **super-resolution module**, gerando áudio a **48 kHz**.
- **Vocabulário de 65.536 tokens** de áudio, **50 tokens por segundo** de áudio (taxa de frame baixa = sequências curtas = latência menor).
- Arquitetura do codec **"inspired by LLaSA"** (LLaSA = LLaMA + single-codebook speech tokens). Esse é exatamente o paradigma **"LLM-as-TTS"**: o SpeechLM gera **audio codes** autoregressivamente, condicionado na transcrição de texto, e um **audio decoder** converte os codes de volta em waveform 48 kHz.

**Pipeline de treino — 3 estágios:**
1. **Pre-training:** large-scale, **>1M horas de raw audio** misturado com dados de texto.
2. **SFT (Supervised Fine-tuning):** **200k horas** de pares **audio-text** filtrados de alta qualidade.
3. **RL Alignment:** **GRPO (Group Relative Policy Optimization)** com **composite reward function** combinando:
   - **WER** (word error rate — inteligibilidade, via ASR);
   - **speaker similarity** (fidelidade ao timbre);
   - **DNSMOS** (qualidade perceptual sem referência).
   - *Para nós: este é o achado de método mais transferível — usar RL (GRPO) com reward composto WER+SIM+DNSMOS é uma receita concreta e barata de alinhar um TTS para "soar natural + inteligível + fiel" sem dados humanos extras.*

**Controle expressivo:**
- **Fine-grained emotional control** e **non-verbal vocalizations** via **audio markups**: **8 speaking styles** + **7 non-verbal tags**.
- *Diretamente relevante ao requisito de emoção/sotaque do TTS-ptbr — tags inline são mais simples de treinar que condicionamento por reference audio.*

**Idiomas:** **11–12 idiomas** documentados. O README do repo lista: `en, es, fr, de, it, pt, ru, zh, ko, ja, nl, pl` — **inclui `pt` (português)**. (Não há garantia de cobertura de sotaque carioca; é pt genérico/europeu/brasileiro misturado — **[NÃO-VERIFICÁVEL]** qual variante predomina.)

**Streaming / técnicas de baixa latência (no nível do modelo):**
- **Context-aware decoding.**
- **Concatenation at non-voicing regions** — emendar chunks de áudio nas **regiões não-vozeadas** (silêncio/pausas) para eliminar artefatos de junção entre chunks streamados. *(Truque limpo e barato — vale copiar a ideia, não o código.)*
- **Volume stabilization** via **context extension**.
- **Decoding the prompt audio** para melhorar **speaker fidelity**.

## 1.3 [TÉCNICO] Serving / infra de baixa latência — o ouro de engenharia

Fonte primária: blog Inworld ["TTS at Scale: Why vLLM Wasn't Enough"](https://inworld.ai/blog/how-we-made-state-of-the-art-speech-synthesis-scalable-with-modular).

**Problema central:** arquitetura de **2 componentes** (**SpeechLM + audio decoder**) tem **performance characteristics descasadas** — o **audio decoder fica ocioso esperando o SpeechLM produzir tokens**, desperdiçando GPU. O `vLLM` vanilla não resolve isso (ele otimiza o LLM, não o par LLM+decoder).

**Solução (parceria com Modular):**
- **MAX framework** — serving framework de alta performance com **advanced batching, graph-level optimizations, memory planning, fine-grained kernel scheduling**.
- **Mojo** — linguagem de sistemas para escrever **custom kernels**. Implementaram um **silence-detection kernel rodando direto na GPU** (on-device output processing), maximizando utilização da GPU.
- **Streaming-aware scheduler** que dá **~1.6× speedup** no SpeechLM.
- Overlapping de execução de kernels, **faster data types no decoder**, eliminação de transferências de memória redundantes entre componentes.

**Números de latência/custo (auto-reportados pela Inworld):**
- **Time-to-first-audio:** mediana **~200 ms** para o primeiro chunk de ~2 s.
- **~70% mais rápido** na entrega do primeiro chunk vs baseline vLLM.
- **~1.6× speedup** no SpeechLM (scheduler streaming-aware).
- **60% de pricing menor** que alternativas baseadas em vLLM.
- Processa áudio em chunks → **playback do início enquanto o resto sintetiza**.

**Lição reaproveitável (mesmo sem Modular):** o gargalo de um TTS LLM-based **não é só o LLM** — é o **descasamento de throughput entre SpeechLM e codec decoder**. Qualquer serving que **paralelize/overlap** os dois e faça **silence/voicing detection na GPU** ganha latência grátis. Vale desenhar o nosso runtime com essa separação em mente desde o dia 1.

## 1.4 [TÉCNICO] Geração 2026: Realtime TTS-2 / TTS 1.5 Max

Fontes: [TestingCatalog](https://www.testingcatalog.com/inworld-ai-launches-realtime-tts-2-model-for-live-conversations/), [Business Wire / press release](https://www.businesswire.com/news/home/20260505096579/en/Inworld-Launches-New-Frontier-Voice-Model-That-Gives-AI-Agents-Contextual-Empathy) (maio/2026).

- **Sub-200 ms median time-to-first-audio** (e **sub-250 ms P90** no "Realtime TTS 1.5 Max" — número de blog/arena, **tratar como auto-reportado**).
- **#1 realtime TTS** na **Artificial Analysis Realtime TTS Arena** (maio/2026, auto-reportado). A geração anterior já tinha **3 das top-5 posições** na Speech Arena, "acima de Google e ElevenLabs" (claim de marketing — **verificar na Artificial Analysis antes de citar como fato**).
- **Conversational awareness:** rastreia **tonal e emotional cues ao longo da troca** e ajusta delivery — a mesma frase soa diferente conforme o contexto da conversa (isto aproxima o produto da experiência "Maya/Sesame").
- **Natural-language voice direction:** em vez de tags fixas, prompts descritivos tipo *"tired but warm after a long day"* dirigem a síntese.
- **Inline controls:** whispers, sighs, laughter em **timestamps precisos**.
- **>100 idiomas** com **on-the-fly switching** preservando a **voice identity** entre idiomas.
- **Integrações de orquestração:** **Layercode, LiveKit, NLX, Pipecat, Vapi, Voximplant** (relevante p/ a frente de orquestradores — ver dossier 83).
- **[NÃO-VERIFICÁVEL]** se TTS-2 tem **open weights** — o press release e o repo MIT cobrem **TTS-1** (código de treino/modelagem MIT, **sem pesos publicados**); TTS-2 aparenta ser **API-only/closed**.

## 1.5 [PRODUTO] GitHub / HF — o que está aberto de fato

- **`github.com/inworld-ai/tts`** — **licença MIT**. Contém: **training infra (SFT + RLHF/GRPO), inference, data pipeline/vectorization, modeling code do SpeechLM e do audio codec**. Suporte a **DDP, DeepSpeed, FSDP**.
- **IMPORTANTE / limite de licença:** o repo libera **código, não pesos**. Usa **checkpoints públicos do xcodec2 (HF)** e exige **LLaMA da Meta** (`meta-llama/Llama-3.2-1B-Instruct`) — que tem **licença LLaMA Community (não Apache/MIT/CC)**. Logo: a **arquitetura e o método são estudáveis e o código é MIT**, mas **treinar em cima do LLaMA carrega a licença restritiva da Meta** → **incompatível com o requisito de licença dura (Apache/MIT/CC) no PRODUTO final**. Para o TTS-ptbr: **reaproveitar o método** (codec X-codec2 single-codebook + SpeechLM + GRPO), mas trocar o backbone por um **base model permissivo** (ex.: Qwen-Apache, OLMo, ou treinar do zero) para manter a licença limpa.
- Demo: [inworld-ai.github.io/tts](https://inworld-ai.github.io/tts/).

---

# PARTE 2 — VOICE.AI

> **Cuidado com homônimos:** existem várias "voice.ai". Esta é a empresa de **Heath Ahrens**, do **real-time voice changer** (voice.ai), **não** "Voicing AI", "Voiceflow", nem outras. Confirmado via [About Voice.ai](https://voice.ai/about) e [TechCrunch 2023](https://techcrunch.com/2023/06/30/voice-ai-raises-6m-as-its-real-time-voice-changer-approaches-500k-users/).

## 2.1 [PRODUTO] O que é exatamente

- **Core histórico:** **real-time voice changer** para **gaming, streaming, chat online** — "troque entre milhares de vozes instantaneamente". App desktop (Windows).
- **Fundador/CEO:** **Heath Ahrens**, que antes fundou a **iSpeech (2007)**, descrita como uma das primeiras plataformas cloud-based de TTS. Fonte: [About Voice.ai](https://voice.ai/about).
- **Funding:** **US$6M** em 2023 liderado por **Mucker Capital + M13**, após **US$3M self-funded**; ~500k usuários na época. Fonte: [TechCrunch](https://techcrunch.com/2023/06/30/voice-ai-raises-6m-as-its-real-time-voice-changer-approaches-500k-users/). Rodadas mais recentes/valuation: **[NÃO-VERIFICÁVEL]** nas fontes primárias acessadas.
- **Expansão de produto (mais recente):** além do voice changer, listam **Voice Cloning** (clone com ~10 s de áudio), **TTS** ("15+ idiomas"), e **Voice AI Agent** (chamadas inbound/outbound). APIs: **Voice Agent API, Text-to-Speech API, Voice Changer API**. Fonte: [voice.ai](https://voice.ai/).
- **Natureza híbrida:** hoje cobrem **voice-to-voice (conversion)** *e* **text-to-speech**, mas o **DNA e o diferencial real é a conversão de voz em tempo real**, não a síntese conversacional from-text.

## 2.2 [TÉCNICO] Tecnologia = RVC (voice conversion), não TTS-core

Fonte primária da Voice.ai: [RVC Voice Changer](https://voice.ai/hub/tools/rvc-voice-changer/) (confirmam usar **"retrieval-based voice conversion methods"**, suportam **upload de modelos RVC v1 e v2**). Detalhe técnico de arquitetura **não é divulgado** por eles (página é marketing). Portanto o método abaixo vem da **fonte aberta do RVC**, que é o que eles usam por baixo.

**Pipeline RVC** (de [RVC-Project README](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/README.en.md) e [Wikipedia: RVC](https://en.wikipedia.org/wiki/Retrieval-based_Voice_Conversion)):

1. **Content feature extractor:** **HuBERT / ContentVec** (self-supervised). RVC **v2** subiu de **256-dim (9-layer HuBERT + final_proj)** para **768-dim (12-layer HuBERT)** — features de conteúdo linguístico independentes do timbre.
2. **Vector retrieval / FAISS (top1):** o passo-assinatura. **"replacing the source feature to training-set feature using top1 retrieval"** via **FAISS** + **k-NN**. Isto resolve o **timbre leakage** (vazamento da voz original) e mitiga o **oversmoothing effect** dos modelos seq2seq puros. Em vez de mapear estatisticamente, ele **recupera a unidade de fala mais parecida do banco da voz-alvo**.
3. **Pitch extraction (f0):** opções **pm, harvest, crepe, dio** e o destaque **RMVPE** (InterSpeech 2023) — extração de pitch robusta para voz aguda/cantada.
4. **Synthesizer / vocoder:** **VITS** + **NSF-HiFiGAN** (GAN-based vocoder) para reconstruir a waveform.
5. **Dados:** treina com **≥10 min de fala low-noise** — pouquíssimo dado.

**Latência real-time (o número que importa):**
- **End-to-end ~170 ms**; **~90 ms com hardware ASIO**. Áudio processado em **chunks de 0.2–0.5 s**.
- *Este é o aprendizado de baixa latência da Voice.ai: a stack RVC já é nativamente real-time por ser leve (não-autoregressiva no decoder, retrieval barato), rodando local/on-device.*

## 2.3 [PRODUTO] GitHub / HF da Voice.ai

- A Voice.ai **não publica os próprios pesos/código de pesquisa** como open source nas fontes acessadas — o produto é **app + API fechada**, construído **sobre o ecossistema open RVC** (que é GPL/MIT-misto e da comunidade, não deles). **[NÃO-VERIFICÁVEL]** se há repo oficial de pesquisa da empresa. O "aberto" aqui é o **RVC upstream**, não a Voice.ai.

---

# PARTE 3 — COMPARAÇÃO: o que cada um faz MELHOR (mesmo sendo "inferiores" no geral)

| Eixo | Inworld AI | Voice.ai | Relevância p/ TTS-ptbr |
|---|---|---|---|
| **Paradigma** | LLM-based autoregressive **TTS** (text→speech) | **RVC voice conversion** (speech→speech) + TTS secundário | Inworld é o **molde direto** do nosso alvo |
| **Latência (TTFA)** | ~200 ms median time-to-first-audio | ~90–170 ms end-to-end (conversion) | Ambos < 250 ms; metas de referência |
| **Abertura** | **Código MIT** (sem pesos; backbone LLaMA) | Produto fechado sobre RVC open | Inworld = método estudável |
| **Emoção/expressão** | audio markups, NL voice direction, conversational awareness | herda timbre da voz-alvo (sem controle semântico) | Inworld vence p/ emoção pt-BR |
| **Engenharia de serving** | MAX/Mojo, GPU silence kernel, scheduler streaming-aware | leve por design (RVC roda em CPU/GPU modesta) | Dois aprendizados distintos |

**O que vale estudar de cada um (sem copiar código):**

1. **De Inworld — [TÉCNICO]:**
   - **Receita de alinhamento GRPO** com reward composto **WER + speaker-similarity + DNSMOS**. Barato, sem anotação humana, melhora naturalidade+inteligibilidade. **Adotar no nosso treino.**
   - **Codec single-codebook estilo X-codec2/LLaSA a baixa frame-rate (50 tps)** → sequências curtas → latência baixa. **Escolha de design para o nosso codec.**
   - **Concatenation at non-voicing regions** para streaming sem artefatos — emendar chunks no silêncio. **Truque de DSP barato.**
   - **Separação SpeechLM ↔ audio decoder** com **overlap/scheduling** e **silence-detection kernel na GPU** — desenhar o runtime já antecipando o descasamento de throughput.

2. **De Voice.ai / RVC — [TÉCNICO]:**
   - **FAISS top1 retrieval para matar timbre leakage** e oversmoothing — técnica de **voice conversion** que pode complementar TTS (ex.: pós-converter a saída do TTS para reforçar identidade da voz do Pedro/carioca, com pouquíssimo dado de speaker).
   - **Pipeline leve não-autoregressivo no decoder (VITS+NSF-HiFiGAN)** atingindo **90–170 ms** — referência de **on-device real-time**. Se o nosso TTS LLM-based for pesado demais para edge, um **estágio RVC final** dá voz-alvo barata em tempo real.
   - **Treino com ≥10 min de dados** — relevante para **few-shot da voz do Pedro**.

3. **[PRODUTO] / business (não poluir o foco, só ciência da estratégia):**
   - Inworld **pivotou de "personagem/NPC" para "camada de voz realtime"** — confirma que o valor está na **infra de voz**, não no wrapper de personagem.
   - Voice.ai cresceu **bottom-up via gaming/streaming** (~500k users em self-funding) — mostra que **voice changer real-time tem demanda de consumo**, distinta do nosso nicho conversacional pt-BR.

---

# FONTES (URLs primárias)

**Inworld:**
- TTS-1 Technical Report — https://arxiv.org/html/2507.21138v1
- Repo MIT (código de treino/modelagem) — https://github.com/inworld-ai/tts
- Demo TTS-1 — https://inworld-ai.github.io/tts/
- "TTS at Scale: Why vLLM Wasn't Enough" (serving/Modular) — https://inworld.ai/blog/how-we-made-state-of-the-art-speech-synthesis-scalable-with-modular
- Realtime TTS-2 (TestingCatalog) — https://www.testingcatalog.com/inworld-ai-launches-realtime-tts-2-model-for-live-conversations/
- Press release TTS-2 (Business Wire) — https://www.businesswire.com/news/home/20260505096579/en/Inworld-Launches-New-Frontier-Voice-Model-That-Gives-AI-Agents-Contextual-Empathy
- What is Inworld AI (lab/funding/founders) — https://inworld.ai/resources/what-is-inworld-ai
- Parceria Xbox/Microsoft (2023) — https://developer.microsoft.com/en-us/games/articles/2023/11/xbox-and-inworld-ai-partnership-announcement/

**Voice.ai / RVC:**
- Voice.ai homepage (produtos/APIs) — https://voice.ai/
- About Voice.ai (fundador Heath Ahrens) — https://voice.ai/about
- RVC Voice Changer (confirma RVC) — https://voice.ai/hub/tools/rvc-voice-changer/
- TechCrunch funding US$6M — https://techcrunch.com/2023/06/30/voice-ai-raises-6m-as-its-real-time-voice-changer-approaches-500k-users/
- RVC-Project README (pipeline técnico) — https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/README.en.md
- Wikipedia: Retrieval-based Voice Conversion — https://en.wikipedia.org/wiki/Retrieval-based_Voice_Conversion

**Contexto:**
- PredGen (input-time speculation; NÃO é Inworld) — https://arxiv.org/pdf/2506.15556

---

## Notas de verificação (honestidade)

- Números de latência da Inworld (200 ms TTFA, sub-250 ms P90, 70%/1.6×/60%) e o ranking #1 na Artificial Analysis Arena são **auto-reportados** (blog/press release). **Verificar independentemente na Artificial Analysis** antes de usar como fato em qualquer comparação pública.
- **TTS-2 open weights:** não confirmado — provável **API-only**. O que está aberto (MIT) é **TTS-1, código sem pesos**, com **dependência de LLaMA (licença Meta, não permissiva)**.
- **Voice.ai:** detalhes internos de arquitetura **não divulgados**; o pipeline RVC descrito vem da **fonte aberta RVC**, que é o que o produto usa por baixo. Founders/valuation pós-2023 **não verificáveis** nas fontes acessadas.
- **PredGen** apareceu na busca por "Inworld real-time" mas **não é paper da Inworld** (autores: Shufan Li, Aditya Grover). Incluído só como técnica de contexto (**input-time speculation** para reduzir TTFT em diálogo falado).
