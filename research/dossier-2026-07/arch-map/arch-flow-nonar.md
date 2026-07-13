# arch-flow-nonar — família NÃO-autoregressiva (flow-matching / diffusion) vs. nosso spine AR codec-LM

**Sub-tópico:** ARQUITETURA — F5-TTS, E2-TTS, CosyVoice 2/3, MegaTTS3, Matcha-TTS, MaskGIT/SoundStorm.
**Data:** 2026-07-13. **Lente:** avaliar por mérito de arquitetura/add-on, não por idioma. Gate de licença só morde PESO/DADO embarcado.
**Nosso stack de referência:** CSM = LM autoregressivo sobre codec Mimi/RVQ (12.5 Hz), audio-conditioned; produto = conversa full-duplex baixa latência, barge-in, voz carioca do Pedro. Gaps: sotaque gringo (#1), prosódia robótica (#2), número (#3). Gargalo = DADO limpo pt-BR.

---

## TL;DR — a única decisão que importa aqui

**"NAR flow-matching" NÃO é uma coisa só. São dois papéis, e confundi-los é o erro.**

- **(A) FM como o SINTETIZADOR INTEIRO** (texto→mel de uma vez): F5-TTS, E2-TTS, Matcha-TTS, MegaTTS3.
  Precisa do **texto inteiro na entrada** (ou modelo de duração + alinhamento completo). Gera a elocução toda num passo (ODE de poucos steps). RTF ótimo (~0.15), mas isso é *throughput*, não *time-to-first-audio* pra conversa. **Não consome token-a-token** de um LLM e **não tem barge-in limpo no meio da fala** → mau spine pra full-duplex. Ganha do AR em *offline*: naturalidade, robustez (sem loop/repetição/exposure-bias que assola codec-LM AR), controle de duração e **edição/infilling**.
- **(B) FM como DECODER acústico em STREAMING, a jusante de um LM AR de tokens semânticos**: CosyVoice 2/3, Kimi-Audio, StreamFlow, FireRedTTS-1S.
  O LM AR emite tokens semânticos incrementalmente → um **decoder flow-matching chunk-wise** (DiT com máscara de atenção por bloco + look-ahead) vira cada chunk em áudio. **Isso streama bidirecional, com baixa latência, E herda a naturalidade do FM.** É o padrão pra onde o campo TODO convergiu em 2025-26.

**Mapa pro nosso caso:**
1. **NÃO troque o spine AR do CSM por um NAR-FM puro** (F5/E2/MegaTTS3) pro produto conversacional. Você perde streaming-nativo, condicionamento em turnos/contexto e emoção-do-contexto — que é justamente o que o CSM te dá.
2. **ROUBE o padrão (B): decoder FM chunk-wise** como alternativa/aumento do decode do Mimi. É o lever barato pra atacar prosódia robótica (#2) e sotaque (#1) **sem retreinar o LM do CSM** — treina só o detokenizer em áudio carioca. Este é o item ADOPT-worthy de verdade da célula.
3. **Rode um bake-off com CosyVoice** — é a referência Apache-2.0 que já faz exatamente a arquitetura que queremos, e streama. Serve de sanity-check honesto contra o CSM.

**Quando NAR bate AR:** offline throughput (RTF), robustez (sem alucinação/loop), controle de duração, edição/infilling. **Quando AR (CSM) ganha:** geração incremental streaming-nativa, contexto longo/turnos, emoção-do-contexto, barge-in. **Híbrido (AR LM + FM decoder) ganha no geral pra conversa** — por isso CosyVoice/Kimi existem.

---

## Item a item (veredito + licença + maturidade)

### 1. CosyVoice 2/3 — LM AR + decoder flow-matching chunk-aware (bi-streaming) — **TEST (forte) / ADOPT-padrão**
- **O que é:** LLM emite tokens semânticos supervisionados; **flow-matching chunk-aware** faz o detokenize acústico. Streaming bidirecional, latência baixa, qualidade "human-parity". CosyVoice 3 (arXiv 2505.17589, papers escalam a 1M h / 9 idiomas / 18 dialetos chineses, RL post-training).
- **Licença:** **Apache-2.0 — código E pesos** (verificado: repo FunAudioLLM, HF `CosyVoice2-0.5B`, `Fun-CosyVoice3-0.5B-2512`). **PASSA no gate.**
- **Maturidade:** released+usável. CosyVoice3 aberto **só na 0.5B** (dez/2025, base+RL+scripts); a versão maior citada no paper **não** tem pesos abertos (verificado no HF). CosyVoice2-0.5B released e maduro.
- **Fit / pegadinha:** é *a* arquitetura-alvo (AR semântico + FM streaming) já pronta e Apache-2.0. **MAS não suporta português** (9 idiomas, sem pt) → precisa do MESMO trabalho de dado pt-BR que o CSM. Por isso não é "plugar já": é **arm de bake-off** (CosyVoice2/3-0.5B fine-tuned na voz do Pedro vs. CSM), e **fonte do padrão de decoder FM streaming** que a gente adota.

### 2. Decoder/detokenizer flow-matching CHUNK-WISE em streaming (Kimi-Audio, StreamFlow, FireRedTTS-1S) — **TEST** *(o método ADOPT-worthy)*
- **O que é:** desacoplar o lado de saída do LM. Kimi-Audio troca o decoder RVQ por um **detokenizer flow-matching chunk-wise** (arXiv 2504.18425); StreamFlow (2506.23986) = FM streaming com máscara de atenção por bloco pra decodar tokens de fala; TTFP (time-to-first-packet) controlado pelo tamanho do chunk + look-ahead.
- **Licença:** **método livre** (papers). Implementações variam — validar peso caso a caso, mas a técnica não embarca dado de terceiros.
- **Maturidade:** released+usável como técnica (múltiplos relatórios de sistema 2025-26, integrado em vLLM-Omni). Não é um "modelo" único a baixar; é um bloco a treinar.
- **Fit:** **é o lever central pra nós.** Mantém o LM AR do CSM (que já streama e condiciona em turnos) e melhora o acústico. Treinar um FM detokenizer sobre os tokens semânticos do Mimi, em áudio carioca limpo, ataca #2 (robótico) e #1 (sotaque) **sem tocar no LM**. Amplia o espaço de design (naturalidade sem re-treinar o AR). Experimento barato e alto valor.

### 3. F5-TTS — DiT flow-matching NAR (infilling), zero-shot — **WATCH** *(método/baseline; peso reprovado no gate)*
- **O que é:** flow-matching sobre mel via ConvNeXt/DiT, tarefa de audio-infilling, sem G2P/duração explícitos. RTF ~0.15; variante "streaming" ~300-500 ms TTFA numa 4090 (mas precisa do texto todo à frente).
- **Licença:** **código MIT, mas PESOS CC-BY-NC-4.0** (treinado no dataset **Emilia**, in-the-wild, NC). **Pesos REPROVAM no gate** (verificado: GitHub discussion #997 — "even after finetuning" continua NC). Pra embarcar teria que **retreinar do zero em dado comercialmente-limpo.**
- **Maturidade:** released+usável (pesos oficiais + forks multilíngues, ex. F5-TTS-vi vietnamês → retrain pt-BR é factível).
- **Fit:** NAR não serve de spine conversacional (sem streaming-nativo/barge-in). Serve como **(a)** referência de arquitetura FM, **(b)** possível gerador offline/data-gen SE retreinado limpo em pt-BR, **(c)** baseline de naturalidade. Não é caminho de produto por causa do gate + NAR.

### 4. E2-TTS — FM NAR "embarrassingly easy" (infilling puro, sem duração/G2P) — **WATCH** *(método ancestral)*
- **O que é:** Microsoft (arXiv 2406.18009). Gerador de mel por flow-matching treinado só com audio-infilling; naturalidade nível-humano (CMOS -0.05), SIM/intelig. SOTA. É o **ancestral do F5**.
- **Licença:** **sem pesos oficiais abertos** (paper); reproduções usam o framework do F5 sobre Emilia (NC). Método livre.
- **Maturidade:** paper-só / reprodução community. Não é um artefato a plugar.
- **Fit:** valor **conceitual** — mostra que dá pra jogar fora G2P/duração/alinhamento e ainda ter naturalidade. Relevante pro nosso debate "G2P morto". Não é caminho de produto.

### 5. Matcha-TTS — conditional flow matching leve (ODE), footprint mínimo — **WATCH** *(baseline limpo, não conversacional)*
- **O que é:** ICASSP 2024 (arXiv 2309.03199). CFM sobre encoder tipo-Transformer; menor footprint de memória, rápido, MOS alto entre baselines pequenos.
- **Licença:** **MIT (código)** e treinável do zero → se você treina em dado limpo, **peso é seu e passa no gate**.
- **Maturidade:** released+usável, mas single-speaker-ish; **não é zero-shot cloning nem grado-conversa**.
- **Fit:** útil como **baseline limpo pt-BR barato** (treinar do zero em áudio limpo pra medir teto de naturalidade FM sem risco de licença) e pra **aprender CFM/ODE-decoding** antes de montar o decoder FM do item 2. Não é produto.

### 6. MegaTTS3 — Latent Diffusion Transformer com sparse alignment — **SKIP** *(peso capado pro nosso uso)*
- **O que é:** ByteDance (arXiv 2502.18924). DiT de difusão latente ~0.45B, "sparse alignment", controle de sotaque/similaridade. Zero-shot cloning.
- **Licença:** **Apache-2.0 (código + pesos do DiT)**, MAS o **encoder WaveVAE NÃO foi liberado** ("security") → você **não clona voz nova arbitrária** (a voz do Pedro) sem passar pelo processo de extração de latente deles. Chinês/Inglês só.
- **Maturidade:** released mas **funcionalmente capado** pro nosso caso (cloning gatekept; forks community reconstroem o WaveVAE, mas aí some a garantia de licença/qualidade).
- **Fit:** **SKIP** — sem pt, sem streaming pra duplex, e o gargalo (clonar Pedro) depende de peso não-liberado. Método (sparse-alignment DiT) fica no radar como referência, não como plug.

### 7. SoundStorm / MaskGIT — decode paralelo iterativo (mask-predict) sobre RVQ — **WATCH** *(método pro head acústico do Mimi)*
- **O que é:** SoundStorm (Google, arXiv 2305.09636) usa o esquema **confidence-based parallel decoding do MaskGIT** adaptado a tokens **RVQ** hierárquicos: decodifica nível-a-nível, amostrando muitos tokens em paralelo nos níveis finos. É o ramo NÃO-flow (mask-predict) da família NAR.
- **Licença:** **sem pesos oficiais** (Google não liberou; só reproduções community). Método livre.
- **Maturidade:** paper + reproduções; nada shippable direto.
- **Fit:** relevante **estruturalmente** — o CSM já usa um depth-transformer sobre codebooks RVQ do Mimi; decode paralelo estilo MaskGIT nos codebooks finos poderia **cortar latência do decode acústico** vs. AR-por-codebook. Braço de pesquisa (WATCH), não produto.

---

## Fechamento pro roadmap
- **Não** existe substituto NAR-puro plug-and-play pro spine conversacional que ganhe do CSM — todos os NAR-FM "inteiros" (F5/E2/MegaTTS3) tropeçam em streaming/barge-in e/ou licença.
- **O ativo real desta célula é o padrão híbrido:** AR semântico (que o CSM já é) + **decoder flow-matching chunk-wise em streaming** (item 2). Método livre, ataca #1/#2, não exige retreinar o LM. **Arm barato, prioridade alta.**
- **Bake-off obrigatório:** CosyVoice2/3-0.5B (Apache-2.0, streaming, human-parity) fine-tuned na voz do Pedro vs. CSM — mede honestamente quanto do nosso gap é arquitetura vs. dado. (Lembrando: CosyVoice também **não** tem pt, então nivela o campo no ponto que sabemos ser o gargalo: DADO carioca.)
- **Gate:** CosyVoice2/3 e Matcha passam (Apache/MIT). **F5/E2 pesos NÃO** (Emilia NC). MegaTTS3 passa no papel mas é capado (WaveVAE). SoundStorm sem peso.
