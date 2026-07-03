# VERIFICAÇÃO (verificador adversarial — 02/jul/2026)

Método: 8 claims load-bearing checados contra a fonte citada (WebFetch) + 1 fonte independente quando disponível. Vereditos:

1. **Chatterbox Multilingual v3 + Language Pack pt-BR dedicado, MIT, 10/jun/2026** — **CONFIRMADO.** Blog oficial da Resemble confirma release 10/jun/2026, expansão 25.6k→36.7k horas, MIT, e checkpoints dedicados pt-BR (0.35% CER) e pt-PT (0.38%); página HF `ResembleAI/chatterbox` (fonte independente do blog) confirma V3 + Single Language Pack com pt-br sob MIT. *Ressalvas:* (a) o CER 0.35% é benchmark do próprio vendor — o mesmo blog situa o modelo multilíngue geral na faixa 1–5% CER pra pt-BR, ou seja, 0.35% é do checkpoint dedicado e auto-reportado; (b) título oficial diz "21 línguas e 4 dialetos" (25 total), não "23+".

2. **Higgs Audio v3 TTS (Boson AI), 04/jun/2026, licença NC, pt em tier de produção (WER/CER<5)** — **CONFIRMADO.** Blog oficial da Boson confirma publicação 04/jun/2026; página HF confirma 102 línguas, 85 em produção com Português (pt/pt-BR) explicitamente listado, e "Boson Higgs TTS 3 Research and Non-Commercial License"; LMSYS publicou post independente no mesmo dia (lmsys.org/blog/2026-06-04-higgs-audio-v3-tts). *Ressalvas:* nome oficial oscila entre "Higgs TTS 3" e "Higgs Audio v3 TTS"; o sub-claim "também saiu Higgs Audio 3.0 STT" NÃO foi confirmado nas fontes checadas; "21 tipos de emoção" não quantificado na fonte.

3. **Gradium (spinoff Kyutai) lançou stt-translate/s2s-translate em 24/jun/2026, API-only, PT entre 5 línguas** — **CONFIRMADO.** Artigo MarkTechPost de 24/jun/2026 confirma os dois modelos, PT entre EN/FR/DE/ES/PT, 20 pares, e nenhuma menção a pesos abertos (consistente com API-only); TechCrunch (02/dez/2025) confirma independentemente spinoff da Kyutai e seed de $70M. *Ressalva:* TechCrunch nomeia só Zeghidour como fundador (não os 4) e não confirma "Kyutai é acionista" — esses dois detalhes são PLAUSÍVEIS, não confirmados.

4. **Qwen3-TTS: 22/jan/2026, Apache-2.0, 0.6B/1.7B + Tokenizer-12Hz, português entre 10 línguas** — **CONFIRMADO.** Repo oficial QwenLM/Qwen3-TTS confirma todos os itens literalmente (release 22/jan/2026, seis variantes, Apache-2.0, "…Russian, Portuguese, Spanish…"). Fonte primária oficial; sem fonte independente separada checada, mas claim de baixo risco.

5. **Kyutai Pocket TTS: 100M/CPU (jan/2026), ganhou pt-BR em abril/2026 com voz "Rafael"** — **CONFIRMADO.** kyutai.org/tts confirma Pocket TTS 100M em CPU real-time, lista "Rafael (Brazilian Portuguese, m)" e diz "In April, we made it speak five other languages". *Ressalva:* licença CC-BY 4.0 dos pesos não aparece na página checada — detalhe de licença fica PLAUSÍVEL; confirmar no HF antes de decisão que dependa disso.

6. **TAGARELA: 8.972h de podcasts, release 16/mar/2026, arXiv 2603.15326, sem TTS treinado publicado** — **CONFIRMADO.** arXiv 2603.15326 existe (submetido 16/mar/2026, autores incl. Frederico S. de Oliveira), 8.972h+; HF `freds0/TAGARELA` confirma independentemente: ICASSP 2026, 91% pt-BR / 9% pt-PT, CC-BY-NC-SA 4.0, subset limpo ~2.800h (bate com a memória do projeto). A negativa "sem checkpoint TTS treinado nele" é consistente com as fontes (não exaustivamente verificável).

7. **Voxtral TTS (Mistral): 23/mar/2026, 4B streaming, CC-BY-NC 4.0, pt entre 9 línguas SOTA, cloning 3s** — **CONFIRMADO.** Blog oficial da Mistral confirma todos os pontos (data, 4B, CC BY-NC 4.0 no HF, PT entre as 9, referência de 3s). Fonte primária oficial.

8. **Sesame CSM: nada novo aberto; upgrades Maya/Miles fechados; sem pt-BR** — **CONFIRMADO** (na parte verificável). HF `sesame/csm-1b` sem release novo (último update mai/2025, Apache 2.0) e diz explicitamente que capacidade não-inglês é fraca ("data contamination... likely won't do well") — sustenta a premissa "nicho pt-BR aberto". *Ressalva:* detalhes do app iOS/beta/smart glasses vêm de fonte secundária (Contrary) não re-checada — PLAUSÍVEL.

**Balanço:** os 8 claims load-bearing sobrevivem; nenhum REFUTADO ou SEM-FONTE. As 3 linhas de "LEITURA PRO PROJETO" seguem válidas. Pontos a tratar com cautela: o CER 0.35% do Chatterbox pt-BR é self-reported (medir no rate_app antes de re-justificar a espinha CSM), o suposto Higgs STT 3.0 não foi confirmado, e a licença exata do Pocket TTS merece checagem no HF.

---

# Cenário de modelos abertos de fala relevantes pra pt-BR — o que mudou desde 2026-06-20

**Resumo executivo:** na janela estrita (20/jun → 02/jul/2026) quase nada saiu — a única novidade dentro da janela é o lançamento comercial da Gradium (spinoff da Kyutai) em 24/jun. **Mas** duas coisas grandes saíram nos ~15 dias imediatamente antes da janela e provavelmente ainda não estão no radar do projeto: **Chatterbox Multilingual v3 com finetune dedicado pt-BR sob MIT (10/jun)** e **Higgs Audio v3 TTS com português em tier de produção (04/jun)**. São os dois achados acionáveis.

---

## DENTRO DA JANELA (20/jun–02/jul)

### Gradium (spinoff comercial da Kyutai) — stt-translate e s2s-translate
- **O que saiu:** modelos de tradução de fala em tempo real (STT→texto traduzido e speech-to-speech end-to-end), com clonagem de voz sobre WebSocket duplex. **Data: 24/jun/2026.**
- **Licença:** API-only até agora — sem pesos abertos.
- **pt-BR:** Português é uma das 5 línguas (EN/FR/DE/ES/PT), 20 pares bidirecionais.
- **Relevância:** não substitui CSM (fechado), mas é o sinal mais forte de pra onde a linha Moshi/delayed-streams vai: Gradium é fundada pelos co-fundadores da Kyutai (Zeghidour, Mazaré, Défossez, Teboul), seed de $70M dez/2025, Kyutai é acionista. A pesquisa aberta continua na Kyutai, o produto vai pra Gradium. Vale monitorar se pesos vazam pro lado aberto.
- **URLs:** https://www.marktechpost.com/2026/06/24/gradium-launches-stt-translate-and-s2s-translate-real-time-speech-translation-models-beating-gpt-realtime-translate-on-accuracy-and-latency/ · https://techcrunch.com/2025/12/02/paris-based-ai-voice-startup-gradium-nabs-70m-seed/

**Todo o resto: nada novo dentro da janela estrita.** Abaixo, o que saiu logo antes (provável ponto cego do replan de 20-21/jun) e o status modelo a modelo.

---

## LOGO ANTES DA JANELA (junho/2026) — provável ponto cego do projeto

### Chatterbox Multilingual v3 + Language Pack pt-BR (Resemble) — ACHADO Nº 1
- **O que saiu:** v3 do Chatterbox Multilingual (mesmo backbone Llama 0.5B), 23+ línguas, dados de treino de 25.6k→36.7k horas, melhora em speaker similarity, alucinação e naturalidade conversacional. E o principal: **Single Language Pack com 6 finetunes dedicados, incluindo um checkpoint só de Português Brasileiro (0.35% CER — o melhor dos 6) e outro de pt-PT (0.38%)**. **Data: 10/jun/2026.**
- **Licença:** **MIT** (pesos no Hugging Face, watermark PerTh embutido).
- **pt-BR:** sim, explícito e dedicado — checkpoint mono-língua pt-BR baixável.
- **Relevância:** **candidato imediato a baseline forte E possível concorrente da espinha CSM.** É o único checkpoint aberto MIT com finetune pt-BR dedicado de um lab de primeira linha. Mínimo: baseline obrigatória no rate_app contra o Treino-2; também serve como professor/judge de pronúncia. Testar antes de qualquer próximo treino grande no CSM.
- **URLs:** https://www.resemble.ai/resources/chatterbox-multilingual-v3-tts-with-embedded-watermarking-for-25-languages · https://huggingface.co/ResembleAI/chatterbox · https://github.com/resemble-ai/chatterbox

### Higgs Audio v3 TTS (Boson AI) — ACHADO Nº 2
- **O que saiu:** Higgs Audio v3 TTS 4B (~5B total), 102 línguas (85 em qualidade de produção, WER/CER<5), zero-shot cloning, tokens inline de emoção (21 tipos)/estilo/prosódia. Também saiu Higgs Audio 3.0 STT. **Data: 04/jun/2026.**
- **Licença:** Boson Research and Non-Commercial — pesos abertos NC; comercial requer licença. (Em modo pesquisa do projeto: usável.)
- **pt-BR:** **Português (pt e pt-BR) listado no tier de produção** (WER/CER<5).
- **Relevância:** baseline de alta qualidade + judge de expressividade. Não substitui CSM pro produto (NC), mas em modo pesquisa é dos TTS abertos mais fortes com pt explícito hoje.
- **URLs:** https://huggingface.co/bosonai/higgs-audio-v3-tts-4b · https://www.boson.ai/blog/higgs-audio-v3-tts · https://github.com/boson-ai/higgs-audio

### MisoTTS (Miso Labs)
- **O que saiu:** TTS 8B emotivo, open weights, one-shot cloning com ~10s. **Data: 04/jun/2026.** Licença: MIT modificada.
- **pt-BR:** não especificado (aparenta EN-first). Checar model card antes de investir tempo.
- **Relevância:** watch-list; só vira baseline se confirmar pt.
- **URL:** https://www.marktechpost.com/2026/06/04/miso-labs-releases-misotts-an-8b-emotive-text-to-speech-model-with-open-weights/ · https://huggingface.co/MisoLabs/MisoTTS

---

## STATUS MODELO A MODELO (pedidos explicitamente)

### Qwen3-Omni
- **Nada novo desde 20/jun.** Último release: set/2025 (30B-A3B Instruct/Thinking/Captioner, Apache-2.0, fala em 10 línguas incl. português). https://github.com/QwenLM/Qwen3-Omni

### Qwen3-TTS
- **Nada novo desde 20/jun.** Série lançada em **22/jan/2026**: 0.6B/1.7B (Base/CustomVoice/VoiceDesign) + Tokenizer-12Hz, **Apache-2.0, português entre as 10 línguas**. Se o projeto ainda não avaliou, é o candidato aberto mais treinável com pt (Apache, tamanho CSM-like, código de treino do ecossistema Qwen). https://github.com/QwenLM/Qwen3-TTS · https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base

### Kyutai (Moshi / delayed-streams / TTS)
- **Nada novo desde 20/jun** no lado aberto. Estado atual: **Kyutai Pocket TTS** (100M params, roda em CPU, jan/2026; **ganhou português em abril/2026 — voz "Rafael", pt-BR masculino**); Kyutai TTS 1.6B (jul/2025, streaming). Pesos CC-BY 4.0 / código Apache+MIT. A novidade estrutural é a Gradium (acima) absorver o lado produto. Pocket TTS pt-BR = baseline levíssima e possível voz de fallback. https://kyutai.org/tts/ · https://github.com/kyutai-labs/delayed-streams-modeling

### Resemble Chatterbox
- **Ver ACHADO Nº 1 acima** (v3 + language pack pt-BR, 10/jun, MIT).

### Higgs Audio (Boson AI)
- **Ver ACHADO Nº 2 acima** (v3 TTS 04/jun, NC, pt tier produção). Contexto: v2.5 (09/jan/2026, 1B) não tinha pt; v2 (ago/2025, Apache) pt só zero-shot.

### CosyVoice 3 (Alibaba/FunAudioLLM)
- **Nada novo desde 20/jun.** Fun-CosyVoice3-0.5B-2512 (dez/2025), Apache-2.0, latência 150ms — mas **9 línguas SEM português** (ZH/EN/JA/KO/DE/ES/FR/IT/RU + dialetos chineses). Irrelevante pra pt-BR por ora. https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512

### IndexTTS-2 / IndexTTS 2.5 (Bilibili)
- **Nada novo desde 20/jun.** IndexTTS 2.5 (technical report jan/2026, arXiv 2601.03888): 2.28x mais rápido, multilíngue estendido pra **ZH/EN/JA/ES — sem português**. Relevante só como referência de arquitetura (controle de duração + emoção desacoplada). https://arxiv.org/abs/2601.03888 · https://huggingface.co/IndexTeam/IndexTTS-2

### VibeVoice (Microsoft)
- **Nada novo desde 20/jun.** Timeline 2026: **VibeVoice-ASR** (jan/2026, MIT, 50+ línguas, diarização+timestamps nativos, 60min numa passada; no transformers desde mar/2026). TTS-1.5B (podcasts 90min, 4 falantes) e Realtime-0.5B seguem sem pt explícito. **ASR é candidato forte pro pipe de transcrição/curadoria do TAGARELA e da coleta diária** (diarização embutida). https://github.com/microsoft/VibeVoice · https://simonwillison.net/2026/Apr/27/vibevoice/

### Step-Audio 2 (StepFun)
- **Nada novo desde 20/jun.** StepAudio 2.5 Realtime saiu **24/mai/2026** (S2S end-to-end, RLHF pra roleplay, paralinguagem) — foco ZH/EN, sem pt-BR. Step-Audio 2 mini (8B, Apache-2.0, ago/2025) segue como está. Não muda nada pro projeto. https://www.marktechpost.com/2026/05/24/stepfun-releases-stepaudio-2-5-realtime-an-end-to-end-voice-model-with-roleplay-specific-rlhf-and-paralinguistic-comprehension/

### GLM-4-Voice (Zhipu)
- **Nada novo** — projeto parado desde 2024, ZH/EN apenas. Irrelevante pra pt-BR. https://github.com/zai-org/GLM-4-Voice

### Maya-1 (Maya Research) — sim, o modelo existe
- **Existe e não tem relação com a Maya da Sesame** (colisão de nome). `maya-research/maya1`: 3B Llama-style + codec SNAC, **Apache 2.0**, lançado **nov/2025**. Voice design por prompt em linguagem natural + 20+ emoções inline. **Inglês apenas** (multi-accent). **Nada novo desde 20/jun.** Relevância: referência de receita (Llama+SNAC, mesma família do Orpheus) e de UX de voice design; não serve pra pt-BR hoje. https://huggingface.co/maya-research/maya1

### NeuTTS (Neuphonic)
- **Nada novo desde 20/jun.** NeuTTS Nano lista **português** entre as línguas suportadas (linha on-device, super leve). Últimas atualizações fev e jun/2026 (melhorias, sem língua nova). Possível baseline on-device pt. https://github.com/neuphonic/neutts · https://huggingface.co/neuphonic/neutts-nano

### Orpheus (Canopy Labs)
- **Nada novo desde 20/jun.** Última novidade: dez/2025 (Groq hospeda variantes EN + árabe saudita, com melhorias gerais). Preview multilíngue (abr/2025) nunca incluiu português e nunca amadureceu. Apache 2.0. Segue como referência de receita Llama-3B-TTS, não como opção pt-BR. https://github.com/canopyai/Orpheus-TTS · https://canopylabs.ai/releases/orpheus_can_speak_any_language

### Dia / Dia2 (Nari Labs)
- **Nada novo desde 20/jun.** Dia2 (nov/2025): streaming conversacional em tempo real, 1B e 2B, tags [S1]/[S2], condicionamento em áudio — **inglês apenas**. Arquitetura interessante pro objetivo "agente que conversa", mas sem pt. https://github.com/nari-labs/dia2

### Sesame CSM / forks treináveis
- **Nada novo desde 20/jun.** `sesame/csm-1b` sem release novo; os upgrades de Maya/Miles (multilingue melhor, contexto maior) ficaram **fechados** no app iOS (que em mai/2026 seguia em beta, sem Android/assinatura; rumor de smart glasses fim de 2026). `CsmForConditionalGeneration` no transformers estável, sem mudança relevante; `csm-mlx` sem atividade nova. Comunidade segue provando finetune de língua nova no CSM-1B (ex.: georgiano, 2026 — mesmo playbook do projeto). https://huggingface.co/sesame/csm-1b · https://github.com/senstella/csm-mlx · https://research.contrary.com/company/sesame-ai

---

## PROJETOS BRASILEIROS / pt-BR

### TAGARELA
- **Nada novo desde 20/jun.** Estado: dataset de **8.972h** de podcasts (pt-BR + pt-PT), release público **16/mar/2026**, paper ICASSP 2026 (arXiv 2603.15326), HF `freds0/TAGARELA`. Sem checkpoint TTS treinado nele publicado até agora — a janela de "primeiro TTS bom treinado no TAGARELA" continua aberta. https://arxiv.org/abs/2603.15326 · https://huggingface.co/datasets/freds0/TAGARELA

### CORAA / NURC-SP (NILC/C4AI-USP)
- **Nada novo desde 20/jun.** CORAA NURC-SP Audio Corpus segue na v2 (dez/2023, ~240h). Nenhum release novo de CORAA/ENTOA encontrado na janela. https://huggingface.co/datasets/nilc-nlp/CORAA-NURC-SP-Audio-Corpus

### AKCIT/UFG
- **Nada novo encontrado** — nenhum release público de modelo de fala do hub na janela (só atividade institucional/cursos; evento Conecta AKCIT 2026 no site). Parceria continua sendo via contato direto, não via release. https://akcit.ufg.br/

### Outros com pt explícito (contexto 2026, pré-janela — checar se já estão no radar)
- **Voxtral TTS (Mistral)** — 23/mar/2026, 4B streaming, **CC-BY-NC 4.0**, **português entre 9 línguas SOTA**, cloning com 3s. Baseline NC forte em modo pesquisa. https://mistral.ai/news/voxtral-tts/
- **Fish Audio S2 / S2 Pro** — open-sourced 09/mar/2026, 80+ línguas, **português tier 2**, Fish Research License (NC). Controle de emoção por linguagem natural. https://huggingface.co/fishaudio/s2-pro
- **F5-TTS-pt-br** (comunidade, `firstpixel/F5-TTS-pt-br`) — pesos pt-BR pro F5-TTS; sem data nova na janela. https://huggingface.co/firstpixel/F5-TTS-pt-br

---

## LEITURA PRO PROJETO (3 linhas)
1. **Ação imediata:** puxar o **Chatterbox v3 pt-BR language pack (MIT)** pro rate_app como baseline contra o CSM Treino-2 — é o primeiro checkpoint aberto comercial-friendly com finetune pt-BR dedicado; se ele ganhar de lavada, a espinha CSM precisa re-justificação.
2. **Judges/baselines NC (modo pesquisa):** Higgs v3 TTS (pt produção) e Voxtral TTS — bons pra scorecard de prosódia e como teto de referência.
3. **Ninguém fechou o nicho:** nenhum player abriu um S2S conversacional com pt-BR nativo na janela; Sesame segue sem pt-BR e com os melhores pesos fechados; o fosso continua sendo dado pt-BR conversacional — a fase de coleta continua sendo a aposta certa.

Sources: [Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS) · [Qwen3-Omni GitHub](https://github.com/QwenLM/Qwen3-Omni) · [Kyutai TTS](https://kyutai.org/tts/) · [delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling) · [Chatterbox v3 blog](https://www.resemble.ai/resources/chatterbox-multilingual-v3-tts-with-embedded-watermarking-for-25-languages) · [ResembleAI/chatterbox HF](https://huggingface.co/ResembleAI/chatterbox) · [Higgs v3 TTS HF](https://huggingface.co/bosonai/higgs-audio-v3-tts-4b) · [Boson blog v3](https://www.boson.ai/blog/higgs-audio-v3-tts) · [CosyVoice3 HF](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512) · [IndexTTS 2.5 arXiv](https://arxiv.org/abs/2601.03888) · [VibeVoice GitHub](https://github.com/microsoft/VibeVoice) · [Simon Willison VibeVoice](https://simonwillison.net/2026/Apr/27/vibevoice/) · [StepAudio 2.5 Realtime](https://www.marktechpost.com/2026/05/24/stepfun-releases-stepaudio-2-5-realtime-an-end-to-end-voice-model-with-roleplay-specific-rlhf-and-paralinguistic-comprehension/) · [GLM-4-Voice](https://github.com/zai-org/GLM-4-Voice) · [maya1 HF](https://huggingface.co/maya-research/maya1) · [NeuTTS GitHub](https://github.com/neuphonic/neutts) · [Orpheus GitHub](https://github.com/canopyai/Orpheus-TTS) · [Dia2 GitHub](https://github.com/nari-labs/dia2) · [sesame/csm-1b HF](https://huggingface.co/sesame/csm-1b) · [csm-mlx](https://github.com/senstella/csm-mlx) · [Contrary: Sesame](https://research.contrary.com/company/sesame-ai) · [TAGARELA arXiv](https://arxiv.org/abs/2603.15326) · [TAGARELA HF](https://huggingface.co/datasets/freds0/TAGARELA) · [CORAA NURC-SP HF](https://huggingface.co/datasets/nilc-nlp/CORAA-NURC-SP-Audio-Corpus) · [AKCIT](https://akcit.ufg.br/) · [Voxtral TTS](https://mistral.ai/news/voxtral-tts/) · [Fish S2 Pro HF](https://huggingface.co/fishaudio/s2-pro) · [MisoTTS](https://www.marktechpost.com/2026/06/04/miso-labs-releases-misotts-an-8b-emotive-text-to-speech-model-with-open-weights/) · [Gradium launch](https://www.marktechpost.com/2026/06/24/gradium-launches-stt-translate-and-s2s-translate-real-time-speech-translation-models-beating-gpt-realtime-translate-on-accuracy-and-latency/) · [Gradium seed TechCrunch](https://techcrunch.com/2025/12/02/paris-based-ai-voice-startup-gradium-nabs-70m-seed/) · [Coval: Gradium/Kyutai](https://www.coval.ai/blog/the-future-of-speech-to-speech-ai-inside-gradium-and-kyutai-s-approach-to-full-duplex-conversation/)

Fontes adicionais usadas na verificação: [LMSYS: Higgs Audio v3 TTS on SGLang-Omni (04/jun/2026)](https://www.lmsys.org/blog/2026-06-04-higgs-audio-v3-tts/) · [HF Space Chatterbox-Multilingual-TTS-V3](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-V3) · [bosonai/higgs-tts-3-4b HF](https://huggingface.co/bosonai/higgs-tts-3-4b)