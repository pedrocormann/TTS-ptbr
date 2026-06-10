# Dossiê: Frederico Santos de Oliveira (freds0)

> FRENTE A — Deep-read da obra. Pesquisado em 2026-06-10 com fontes primárias (arXiv, HF, GitHub, fredso.com.br, Google Scholar).
> Contexto do projeto: TTS-ptbr conversacional nível Maya/Sesame, sotaque carioca, **licença dura Apache/MIT/CC-BY/CC0 no produto**.

---

## 0. Quem é (TL;DR)

- **Frederico Santos de Oliveira** — Professor na **UFMT** (Faculdade de Engenharia / Dep. Ciência da Computação, Cuiabá-MT), doutorado pela **UFG** (síntese e reconhecimento de fala com deep learning).
- Membro do cluster de pesquisa de fala pt-BR ligado a **Edresson Casanova** (XTTS/YourTTS/Coqui→NVIDIA), **Arnaldo Candido Jr**, **Lucas Rafael Stefanel Gris**, **Alef Iury Siqueira Ferreira**, **Anderson da Silva Soares** e **Arlindo Galvão Filho** (UFG/CEIA).
- Hoje o trabalho dele roda dentro do **AKCIT** (Advanced Knowledge Center for Immersive Technologies, https://akcit.ufg.br/), financiado por MCTI/EMBRAPII (grant 057/2023) — projeto "Digital Human Technological Components".
- **Por que importa pra nós**: ele é o autor principal do **TAGARELA** (8.972h de podcasts pt, ICASSP 2026), o maior corpus de fala conversacional em português já publicado — e o pipeline dele é exatamente o tipo de pipeline de coleta que precisamos replicar.
- Scholar: 358 citações, h-index 8 (https://scholar.google.com/citations?user=ei62cecAAAAJ).

---

## 1. PRIORIDADE MÁXIMA — arXiv 2506.02088 (SER, Interspeech 2025)

**"Enhancing Speech Emotion Recognition with Graph-Based Multimodal Fusion and Prosodic Features for the Speech Emotion Recognition in Naturalistic Conditions Challenge at Interspeech 2025"**
- arXiv: https://arxiv.org/abs/2506.02088 (HTML: https://arxiv.org/html/2506.02088) — submetido 2025-06-02.
- Autores: Alef Iury Siqueira Ferreira, Lucas Rafael Gris, Alexandre Ferro Filho, Lucas Ólives, Daniel Ribeiro, Luiz Fernando, Fernanda Lustosa, Rodrigo Tanaka, **Frederico Santos de Oliveira**, Arlindo Galvão Filho. (Frederico é 9º autor — o lead é o Alef Iury, do mesmo grupo UFG/AKCIT.)
- Contexto: submissão ao **Interspeech 2025 SER in Naturalistic Conditions Challenge** (dataset **MSP-Podcast**, fala espontânea de podcast em inglês, 8 classes de emoção categóricas). Ficaram em **8º lugar**.

### 1.1 Arquitetura exata

**Encoders testados (audio, congelados/fine-tuned como extratores):**
- Wav2Vec2 Large, HuBERT Large, WavLM Large, **Whisper Large V3 (melhor unimodal: Macro-F1 0.366)**, XEUS (ESPnet — entrou no ensemble final).

**Encoder de texto:**
- **RoBERTa Large** (escolha primária; E5-Large-v2 testado e descartado).
- Transcrições geradas pelo ASR **Canary** (NVIDIA) — ou seja, o ramo de texto funciona 100% sobre transcrição automática, sem texto gold. Importante: isso é o cenário real de um eval de TTS (a gente transcreve o áudio sintetizado e alimenta o ramo textual).

**Fusão multimodal — o "grafo":**
- O mecanismo central é o **MDAT (Multimodal Dual Attention Transformer)**, que combina **Graph Attention Networks (GAT)** + co-attention. O GAT atribui pesos de atenção dinâmicos a nós para "adaptive feature importance estimation"; depois há **dois encoders Transformer** de refinamento, mantendo representações específicas por modalidade (texto Z_F,T(j) e fala Z_F,S(t)).
- 8 cabeças de multihead attention (escolhido por experimentos preliminares).
- **Limitação do paper**: a definição exata de nós/arestas do grafo e a profundidade do GAT NÃO são especificadas no texto — para reproduzir é preciso ler o código (abaixo). Comparado com baselines de fusão: MDAT 0.401 vs concat simples 0.388 vs HCAM 0.383 (Macro-F1, validação) — ou seja, **o grafo dá ~+1.3 ponto sobre concatenação**. Ganho real, mas não transformador.

**Features prosódicas (a parte mais interessante pra nós):**
- **F0 quantizado**: pitch extraído com **RMVPE**, convertido pra escala mel e **quantizado em 256 bins** (+ índice de padding), mapeado para embeddings aprendíveis de 256-d, projetados a 512-d, mean-pooled no tempo. Comparado contra baseline CNN-1D (kernel 3, stride 1, 256 canais) — a versão quantizada ganha.
- **Features espectrais**: mel filterbanks (torchaudio estilo Kaldi) processados pelo **CED-Small (22M params, Consistent Ensemble Distillation — modelo de audio tagging)**, fine-tuned e concatenado antes do MLP classificador.
- Incremental: Whisper+RoBERTa+MDAT = 0.401 → **+F0 quantizado = 0.407** → +SeqAug+SwiGLU = **0.411**.

### 1.2 Treino
- Loss: **Cross-Entropy ponderada** por frequência inversa de classe (MSP-Podcast é muito desbalanceado).
- AdamW (β=[0.9,0.98], ε=1e-8, wd=1e-6), LR 5e-5→1e-5 cosine, warmup 500 steps, batch 8, 20 épocas, grad clip 10.
- Augmentation: **SeqAug** (permutação por dimensão de feature, p=0.5, beta α=0.5).

### 1.3 Ensemble e resultados
- **Majority voting** sobre 13 variações (fusões/augment/prosódia), mínimo 3 modelos, desempate pelo melhor modelo; seleção por Macro-F1 médio em 100 subconjuntos balanceados amostrados da validação.
- Final: **Macro-F1 0.422 (validação) / 0.3979 (teste oficial)** — 8º lugar no challenge. Sem breakdown por classe no paper.

### 1.4 Código
- **Público**: https://github.com/alefiury/InterSpeech-SER-2025 — ~45 commits, 98% Python, scripts de extração de embeddings (todas as camadas e última camada), download de RIR/background e checkpoint de F0, configs. README lista 16 modelos de áudio e 7 de texto suportados. **Sem arquivo LICENSE visível** (ponto de atenção: tecnicamente "all rights reserved"; se formos copiar código, pedir licença via issue ou reimplementar).

### 1.5 Avaliação: dá pra adaptar como nosso SER pt-BR (camada 2 do eval)?

**Sim, e é uma boa receita — mas com adaptações e expectativas calibradas.**

O que joga A FAVOR:
1. A receita é **encoder-agnóstica**: trocar os ramos é trivial. Para pt-BR: áudio = **Whisper Large V3** (multilíngue, já foi o melhor deles) e/ou **emotion2vec+** como ramo adicional; texto = **BERTimbau/XLM-R** sobre transcrição do nosso ASR.
2. Foi desenhada exatamente para **fala espontânea de podcast** — o mesmo domínio do nosso alvo conversacional (Maya/Sesame).
3. O achado mais transferível é barato: **F0 quantizado em bins mel com embedding aprendível** dá ganho consistente (+0.6 pt) e é ~50 linhas de código (RMVPE já temos no ecossistema RVC). Prosódia é justamente o que queremos medir num TTS conversacional.
4. O protocolo de ensemble + validação em subsets balanceados é diretamente copiável para qualquer classificador do nosso eval.

O que joga CONTRA / cuidados:
1. **Números absolutos baixos** (Macro-F1 ~0.40-0.42 em 8 classes): SER naturalista é difícil; como camada de eval, usar para **comparações relativas A/B** (modelo X vs Y na mesma frase-alvo) e não como métrica absoluta.
2. **Não existe MSP-Podcast pt-BR**: dados de emoção em pt-BR são escassos (CORAA-SER é pequeno e NC; VERBO idem). Caminho realista: (a) emotion2vec+ zero-shot como backbone congelado, (b) cabeça MDAT-lite treinada com poucos dados pt-BR + dados sintéticos de emoção (ver `freds0/expressive_synthetic_speech`, 600 amostras, 41.9GB — sem card, provavelmente saída de TTS expressivo; investigar antes de usar), (c) cross-lingual transfer do MSP-Podcast.
3. O grafo (MDAT) é a parte de menor ROI: +1.3 pt sobre concat. **Recomendação: copiar o ramo prosódico (F0 quantizado) + CED espectral + WCE + ensemble protocol; adiar o GAT** — começar com concat simples sobre emotion2vec+ ⊕ F0-quant ⊕ BERTimbau e só adicionar MDAT se o ganho justificar.

**O que copiar (lista objetiva):**
- [ ] F0 via RMVPE → mel-scale → 256 bins → embedding 256d→512d (módulo do eval).
- [ ] Weighted CE com pesos por frequência inversa.
- [ ] Validação em 100 subsets balanceados (seleção de checkpoints/ensemble).
- [ ] Transcrição automática como entrada do ramo textual (casa com nosso pipeline Whisper).
- [ ] (Opcional, fase 2) MDAT/GAT do repo do alefiury — após resolver licença.

---

## 2. TAGARELA (arXiv 2603.15326, ICASSP 2026)

**"Tagarela — A Portuguese speech dataset from podcasts"**
- arXiv: https://arxiv.org/abs/2603.15326 (submetido 2026-03-16; HTML: https://arxiv.org/html/2603.15326)
- Publicado: **ICASSP 2026**, pp. 15517-15521, DOI 10.1109/ICASSP55912.2026.11462137.
- Autores: **Frederico Santos de Oliveira (1º autor)**, Lucas R. S. Gris, Alef Iury S. Ferreira, Augusto Seben da Rosa, Alexandre Ferro Filho, **Edresson Casanova**, Christopher D. Shulby, Rafael T. Sousa, D.F.C. Silva, Anderson da S. Soares, Arlindo Galvão Filho.
- Projeto: https://fredso.com.br/TAGARELA (também https://freds0.github.io/TAGARELA/) | HF: https://huggingface.co/datasets/freds0/TAGARELA
- Financiamento: AKCIT / MCTI PPI IoT / EMBRAPII grant 057/2023.

### 2.1 Números
| Métrica | Valor |
|---|---|
| Duração total | **8.972 h** (rival do GigaSpeech inglês, 10kh) |
| Fonte | repositório **"Cem Mil Podcasts"** (podcasts em português) |
| Episódios / shows | 16.806 / 2.094 |
| Falantes distintos (rotulados) | ~13.368 |
| pt-BR / pt-PT | 8.130 h (~91%) / 842 h (~9%) |
| Gênero | ~70% M (6.368h) / ~30% F (2.604h) |
| Segmento médio | 9,30 ± 5,49 s; 27,7 ± 17 palavras |
| Subsets | **Full 8.972h (ASR, com disfluências)** + **Clean ~2.800h (TTS)** |

### 2.2 Pipeline completo, etapa por etapa

1. **Padronização**: conversão para FLAC, 16 kHz, 16-bit, mono.
2. **Segmentação**: clipes de **5–20 s**, priorizando cortes em silêncios naturais.
3. **Diarização**: **pyannote** — rótulo de falante por segmento, garantindo amostras mono-falante.
4. **Detecção de sobreposição de fala**: classificador **Wav2Vec2-XLS-R** treinado para overlap; segmentos com overlap **descartados**.
5. **Transcrição bootstrap em 2 estágios**:
   - Estágio A: ~**1.000 h** transcritas com **ElevenLabs Scribe v1** (API comercial, jun/2025) = corpus-semente.
   - Estágio B: **Whisper large-v3 fine-tuned** no corpus-semente; as **7.972 h restantes pseudo-rotuladas** pelo Whisper FT.
   - Filtro de qualidade: **concordância WER/CER entre Whisper FT e um Wav2Vec2-XLS-R** — só ficam amostras com alta concordância. **Thresholds exatos NÃO publicados** no paper.
6. **Denoising**: **Vocos** adaptado como denoiser (remove ruído de fundo, hiss, reverberação leve). Versão pública do denoiser treinada só com dados públicos; a usada internamente foi treinada com dataset privado.
7. **Rotulagem de falante/dialeto**: embeddings **ReDimNet B6** + clustering **HDBSCAN por podcast** (evita merge de IDs entre shows) → 13.368 falantes; classificador de dialeto (BR vs PT) = wav2vec2-base fine-tuned em **CORAA + CommonVoice + CML-TTS**.

### 2.3 Subset "clean" de 2.800 h para TTS — como foi filtrado
- O paper **NÃO documenta os critérios quantitativos** (sem threshold de SNR, sem NISQA/UTMOS declarado). O que está explícito: mono-falante (diarização), sem overlap (etapa 4), áudio denoised via Vocos. A metodologia de seleção exata é a maior lacuna do paper — se for crítico, vale abrir issue/e-mail pro Frederico.
- Validação do clean subset: fine-tuning de **Orpheus-TTS** (WER 0.095, MOS 4.155±1.001) e **Chatterbox** (MOS 4.176±0.983) vs ground truth MOS 4.231 — 50 avaliadores, 40 amostras, outlier removal em 2 estágios. **Sinal fortíssimo pra nós: Orpheus e Chatterbox fine-tunam bem em 2.800h de podcast pt e chegam perto do MOS do áudio real.**
- Métricas objetivas reference-free via **TorchAudio-SQUIM** (STOI, PESQ-wb, SI-SDR) — só violin plots, sem tabela numérica.

### 2.4 Validação ASR (full 8.972h)
| Modelo | WER % | CER % |
|---|---|---|
| **Parakeet v2 FT** | **15,18** | **7,09** |
| Distil-Whisper FT | 20,02 | 11,18 |
| Wav2Vec Large FT | 21,85 | 8,55 |
| Whisper Large V3 (zero-shot) | 20,91 | 12,42 |
| Parakeet v3 baseline | 23,30 | 14,86 |

(Teste = test set TAGARELA transcrito manualmente. Nota: Parakeet v2 FT vira candidato a melhor ASR aberto pt-BR para o nosso eval de inteligibilidade — checar se publicam o checkpoint; em 2026-06-10 a página diz **"Models: Coming Soon"**.)

### 2.5 Estrutura real no HF (verificado via datasets-server API, 2026-06-10)
- **Config**: apenas `default`. **Split**: apenas `train` = **7.111.196 linhas**. Tamanho: **1,21 TB**.
- **Campos (4)**: `audio` (Audio, 16 kHz) | `path` (string) | `sentence` (string, transcrição) | `accent` (string, presumivelmente pt-BR/pt-PT).
- **O que NÃO está no HF**: não há config separada do subset clean-2.800h, não há campos de speaker_id, gênero, show/episódio, scores de qualidade ou flags de disfluência — ou seja, **os metadados ricos do paper (13k falantes, dialeto por falante, etc.) não estão expostos no dataset viewer** na versão atual. Última atualização: ~2026-06-09 (1 dia atrás), 7,67k downloads.

### 2.6 LICENÇA — ponto crítico (discrepância real)
- **HF dataset card** e **página do projeto fredso.com.br/TAGARELA**: **CC BY-NC-SA 4.0** (citação literal da página: "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International").
- O HTML do paper no arXiv exibe "License: CC BY 4.0" — mas isso é a **licença do artigo no arXiv**, não do dataset (o abstract menciona disponibilidade via CC, o que gerou confusão em resumos de terceiros).
- **Veredicto para o nosso produto: TAGARELA é NC-SA → INCOMPATÍVEL com a nossa exigência dura (Apache/MIT/CC-BY/CC0).** Além disso, o material-fonte são podcasts com copyright dos criadores — mesmo um relicenciamento CC-BY pelo autor não sanaria a cadeia de direitos para uso comercial. **Uso permitido pra nós: pesquisa interna, ablações, eval, pré-estudos — nunca pesos do produto final treinados nele** (assumindo postura conservadora de que pesos herdam restrição NC).

### 2.7 O que reaproveitar no nosso pipeline de coleta própria (a parte valiosa)
A receita inteira é replicável com componentes abertos sobre **fontes que NÓS licenciamos** (gravações próprias do Pedro, áudio CC-BY/CC0, parcerias):
1. FLAC 16kHz mono → segmentação 5–20s em silêncios (nós: manter 24/44.1kHz para TTS — eles usam 16kHz por foco em ASR; **não copiar o sample rate**).
2. pyannote para diarização + classificador de overlap (podemos usar o próprio pyannote `overlapped-speech-detection` em vez de treinar um XLS-R).
3. **Bootstrap de transcrição 2-estágios**: API comercial premium num seed pequeno (~10% do corpus) → fine-tune de Whisper → pseudo-label do resto → filtro por concordância entre 2 ASRs distintos. Barateia transcrição em ~10x.
4. ReDimNet B6 + HDBSCAN **por fonte** para speaker labeling.
5. Denoising: eles usam Vocos; em 2026 considerar também MossFormer2/resemble-enhance — mas a ideia "denoise antes do TTS subset" está validada.
6. Classificador de dialeto wav2vec2 fine-tuned (nós: adaptar para **classificador de sotaque carioca vs outros** usando o campo `accent` de datasets abertos + CORAA como referência de treino — atenção à licença NC do CORAA para esse uso).
7. Validar o corpus do jeito deles: treinar Orpheus/Chatterbox e medir WER-Whisper + MOS + SQUIM — é exatamente o nosso eval harness.

---

## 3. Restante da obra (1 parágrafo cada + o que aproveitar)

**FreeSVC (arXiv 2501.05586, ICASSP 2025)** — https://arxiv.org/abs/2501.05586. Conversão de voz cantada multilíngue zero-shot: VITS aprimorado com **SPIN** (Speaker-invariant Clustering) como extrator de conteúdo e **ECAPA2** como speaker encoder, mais embeddings de língua treináveis; mostram que extrator de conteúdo multilíngue é crucial para conversão cross-lingual. Código/modelos públicos (repo `freds0/free-svc` está nos pinned do GitHub dele). *Aproveitar*: ECAPA2 como speaker encoder de referência para nosso eval de similaridade de locutor; SPIN como alternativa a ContentVec se um dia fizermos VC/data augmentation de timbre.

**CORAA (arXiv 2110.15731, LREV)** — https://arxiv.org/abs/2110.15731. Corpus de 290,77h pt-BR (+4,69h pt-PT) com pares áudio-transcrição **validados manualmente**, ênfase em fala espontânea; baseline Wav2Vec2 XLSR-53 com WER 24,18%. **Licença CC BY-NC-ND 4.0 → incompatível com o produto.** *Aproveitar*: test set como benchmark de inteligibilidade espontânea no eval (uso de avaliação, não de treino); taxonomia de disfluências deles é boa referência para anotar nosso corpus próprio.

**Wav2vec2-pt ASR (arXiv 2107.11414)** — https://arxiv.org/abs/2107.11414. Fine-tune do XLSR-53 só com dados públicos pt-BR; WER médio 12,4% em 7 datasets (10,5% com LM) — era o melhor ASR aberto pt-BR de 2021. *Aproveitar*: historicamente importante, mas superado; para o eval 2026 usar Whisper large-v3 / Parakeet FT (do TAGARELA, quando saírem os checkpoints).

**SC-GlowTTS (arXiv 2104.05557, Interspeech 2021)** — https://arxiv.org/abs/2104.05557. TTS zero-shot multi-speaker eficiente (decoder flow-based condicionado a speaker, 3 variantes de text encoder, vocoder GAN fine-tuned nos espectrogramas do TTS); SOTA de similaridade com falantes não vistos convergindo com só 11 falantes. Paper mais citado dele (141). *Aproveitar*: arquitetura obsoleta em 2026; fica a lição do fine-tune do vocoder nos outputs do acoustic model (ainda válida quando se usa vocoder separado).

**TTS-Portuguese Corpus (arXiv 2005.05144)** — https://arxiv.org/abs/2005.05144. Primeiro corpus público de TTS pt-BR: 10,5h, single-speaker, + Tacotron 2/RTISI-LA, MOS 4,03. *Aproveitar*: é o "LJSpeech brasileiro" — útil como sanity check/baseline de pipeline e como referência de escala mínima single-speaker (10h), que é justamente a ordem de grandeza do dataset de voz própria do Pedro; checar licença da versão atual antes de qualquer uso em produto (historicamente CC BY 4.0 nos releases do grupo, confirmar no repo).

**Speech2Phone (arXiv 2002.11213, BRACIS)** — https://arxiv.org/abs/2002.11213. Método eficiente de treino de speaker recognition via reconstrução de fonemas na voz do falante; resultados competitivos com 500x menos dados (corpus próprio de ~3h, 40 falantes). *Aproveitar*: pouco — speaker embedding em 2026 se resolve com ECAPA2/ReDimNet; valor apenas conceitual (supervisão barata p/ low-resource).

**Papers 2023–2026 adicionais encontrados (busca arXiv por autor):**
- **CML-TTS (arXiv 2306.10097, 1º autor)** — https://arxiv.org/abs/2306.10097. Dataset multilíngue de TTS (3.176h em 7 línguas incl. português, derivado de MLS/LibriVox, + LibriTTS), **CC BY 4.0**, treinaram YourTTS. *Aproveitar*: **a porção portuguesa é dos poucos corpora pt grandes com licença compatível com nosso produto** — estilo audiobook (não conversacional), serve para pré-treino/robustez fonética; HF tem `freds0/cml_tts_dataset_*`.
- **Evaluation of Speech Representations for MOS prediction (arXiv 2306.09979, TSD 2023, 1º autor)** — https://arxiv.org/abs/2306.09979. Compara Whisper, SpeakerNet, TitaNet como features para predição de MOS; cria o **BRSpeechMOS** (pt-BR!); Whisper-Small dá a melhor correlação (0,698) no BRSpeechMOS. Código público (repo pinned `BSpeech-MOS-Prediction`). *Aproveitar*: **diretamente relevante pro nosso eval harness** — um preditor de MOS calibrado em pt-BR; comparar com UTMOSv2/TTSDS2 e considerar re-treinar a cabeça deles nos nossos dados de preferência.
- **No Saved Kaleidosope (arXiv 2409.11600)** — linguagem de programação JIT para redes neurais com sintaxe pythônica (CUDA/C++); fora do nosso escopo.
- **Yin Yang Convolutional Nets (arXiv 2310.16148)** — visão computacional (extração de manifold por análise de opostos); fora do escopo.
- (Visão/infra: PTL-AI Furnas Dataset, 2022 — detecção de falhas em linhas de transmissão; fora do escopo.)

---

## 4. Perfil e rede (estado em 2026-06-10)

**Afiliação atual**: Professor na **UFMT** (Cuiabá-MT); PhD pela **UFG**; pesquisador do **AKCIT** (akcit.ufg.br — centro de IA imersiva da UFG, financiado MCTI/EMBRAPII; a UFG também tem o CEIA, e os co-autores Anderson Soares/Arlindo Galvão são desse ecossistema). A linhagem NILC/USP entra via Sandra Aluísio/Moacir Ponti nos papers antigos com Edresson. ResearchGate: https://www.researchgate.net/profile/Frederico-Santos-De-Oliveira-2.

**Co-autores recorrentes** (núcleo duro): Edresson Casanova (6+ papers; hoje NVIDIA), Arnaldo Candido Jr (UTFPR/UNESP), Lucas R. S. Gris, Alef Iury Siqueira Ferreira (lead do SER e do FreeSVC), Anderson da Silva Soares e Arlindo Galvão Filho (UFG, orientadores/líderes do grupo), Augusto Seben da Rosa, Christopher Shulby, Rafael T. Sousa.

**O que ele está fazendo AGORA (HF `freds0`, atividade verificada)**:
- **TAGARELA atualizado há 1 dia** (2026-06-09) — dataset vivo, em manutenção ativa.
- Série **`baseline_codebase_*`** com updates quase diários (último: `baseline_codebase_results_500k`, **há 20 horas**; antes: `results_b_agenet_finetuned`, `baseline_codebase_v1.1.1_28052026`, `baseline-codebase-v0.1.1_ft`, `GMFlow`, `flowlet`...). **Todos sem model card** — parecem checkpoints de experimentos internos do AKCIT. Os nomes `GMFlow`/`flowlet` e os datasets `FOMO300K_brain_age`/`OpenBHB` indicam que parte dessa atividade recente é **neuroimagem (brain age)**, não fala — ele aparenta tocar duas frentes no AKCIT.
- Lado fala: orgs **AKCIT-Speech** (1 membro = ele; dataset BRSpeech-TTS, fev/2026) e **AKCIT-Deepfake** (dataset BRSpeech-DF: 459k amostras reais+sintéticas de TTS abertos — útil como referência anti-deepfake/detecção). Também é membro de "StyleTTS 2 Community" e "Ermis AI".
- **`freds0/BRSpeech-TTS`** (HF, abr/2025): 76,3k linhas pt-BR, campos `wav_filename, text, transcript, duration, speaker (2.960+), gender, accent, levenshtein, num_words` — **tem campo `accent`** (interessante p/ filtro carioca) mas sem documentação de licença → tratar como não-utilizável no produto até esclarecimento.
- **`freds0/expressive_synthetic_speech`** (abr/2026): 600 amostras, 41,9GB, sem card — provável material de fala expressiva sintética (candidato a apoio do eval de emoção; investigar conteúdo).
- **`freds0/BrSpeech-YT`** (abr/2026): **stub vazio** (2,5kB, sem dados) — sinaliza que um corpus de YouTube pt-BR pode estar a caminho. Monitorar.
- GitHub https://github.com/freds0: 111 repos; pinned: TAGARELA, BSpeech-MOS-Prediction, CML-TTS-Dataset/Toolkit, free-svc.
- Página da TAGARELA: **"Models: Coming Soon"** → os checkpoints ASR/TTS (Parakeet FT, Orpheus FT pt) devem ser publicados em breve. **Vale acompanhar o HF dele semanalmente — um Orpheus-pt do AKCIT mudaria nosso ponto de partida.**

---

## 5. Síntese acionável para o TTS-ptbr

1. **Não dá pra usar TAGARELA nos pesos do produto** (CC BY-NC-SA + cadeia de direitos de podcasts). Usar só para eval/pesquisa interna.
2. **Copiar a receita, não o dado**: o pipeline TAGARELA (pyannote → overlap filter → bootstrap ElevenLabs→Whisper-FT → filtro por concordância dual-ASR → Vocos denoise → ReDimNet+HDBSCAN) é o blueprint do nosso pipeline de coleta licenciada.
3. **Evidência de ouro**: Orpheus-TTS e Chatterbox fine-tunados em 2.800h de podcast pt chegam a MOS ~4,16 (GT 4,23) — valida nossa aposta em fine-tune de modelos LLM-TTS abertos com dados conversacionais pt.
4. **SER (camada 2 do eval)**: adotar F0-quantizado (RMVPE→mel→256 bins→embedding) + weighted CE + ensemble com validação balanceada sobre emotion2vec+ ⊕ BERTimbau; MDAT/GAT só na fase 2 (ganho de ~1,3 pt; repo sem LICENSE).
5. **Eval de MOS pt-BR**: BSpeech-MOS-Prediction + BRSpeechMOS são o único preditor de MOS calibrado em pt-BR — integrar como métrica complementar ao TTSDS2/UTMOS.
6. **CML-TTS (CC BY 4.0)** é o corpus pt grande license-clean do grupo — candidato a pré-treino fonético.
7. **Monitorar**: HF freds0 (TAGARELA "Models: Coming Soon", BrSpeech-YT stub) e AKCIT-Speech. Considerar contato direto (oi@unflat.studio → fredso) para: thresholds do clean subset, licença do BRSpeech-TTS e roadmap dos checkpoints.

---

## Fontes primárias
- https://arxiv.org/abs/2506.02088 | https://arxiv.org/html/2506.02088 | https://github.com/alefiury/InterSpeech-SER-2025
- https://arxiv.org/abs/2603.15326 | https://arxiv.org/html/2603.15326 | https://fredso.com.br/TAGARELA | https://huggingface.co/datasets/freds0/TAGARELA | datasets-server.huggingface.co/info?dataset=freds0/TAGARELA
- https://arxiv.org/abs/2501.05586 | https://arxiv.org/abs/2110.15731 | https://arxiv.org/abs/2107.11414 | https://arxiv.org/abs/2104.05557 | https://arxiv.org/abs/2005.05144 | https://arxiv.org/abs/2002.11213 | https://arxiv.org/abs/2306.10097 | https://arxiv.org/abs/2306.09979 | https://arxiv.org/abs/2409.11600 | https://arxiv.org/abs/2310.16148
- https://huggingface.co/freds0 | https://huggingface.co/AKCIT-Speech | https://huggingface.co/datasets/freds0/BRSpeech-TTS | https://huggingface.co/datasets/freds0/expressive_synthetic_speech | https://huggingface.co/datasets/freds0/BrSpeech-YT | https://huggingface.co/datasets/AKCIT-Deepfake/BRSpeech-DF
- https://github.com/freds0 | https://www.fredso.com.br | https://scholar.google.com/citations?user=ei62cecAAAAJ | https://www.researchgate.net/profile/Frederico-Santos-De-Oliveira-2 | https://akcit.ufg.br/
- Export arXiv API (author query, 12 papers, 2026-06-10).
