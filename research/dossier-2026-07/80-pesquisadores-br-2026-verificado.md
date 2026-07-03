# VERIFICAÇÃO (checagem adversarial, 02/jul/2026)

**Método:** 8 claims load-bearing selecionados (mudam roadmap de dados, G2P, parcerias e baselines). Cada um checado na fonte citada via WebFetch + ≥1 busca/fonte independente.

| # | Claim | Veredito | Justificativa (1 linha) |
|---|-------|----------|-------------------------|
| 1 | TAGARELA: 8.972h totais (ASR), ~2.800h clean p/ TTS, rótulo de dialeto 8.130h pt-BR / 842h pt-PT, aceito no ICASSP 2026 | **CONFIRMADO** | arXiv 2603.15326 ("over 8,972 hours") + site fredso.com.br/TAGARELA (2.800h clean, 8.130/842, "Models Coming Soon") + listagem independente no programa do ICASSP 2026 (cmsworkshops, sessão AASP-P20.4). |
| 2 | Licença do **dado** TAGARELA = CC BY-NC-SA 4.0 (a CC-BY do arXiv é só do paper) | **CONFIRMADO** | Site oficial e página HF freds0/TAGARELA listam ambos CC BY-NC-SA 4.0; a página do arXiv exibe CC-BY apenas para o artigo — a distinção do relatório está correta. |
| 3 | BIPA (PROPOR 2026): 53.353 palavras / 350.021 transcrições IPA, 6 dialetos incl. Rio, ByT5-small PER 2,66% | **CONFIRMADO** | aclanthology.org/2026.propor-1.47 bate número a número (53.353 / 350.021 / Rio entre os 6 dialetos / PER 2,66%), autores Sousa, Gris, N. Silva conferem. |
| 4 | Certas Palavras: ~70h rádio 1980s-90s, testa YourTTS e F5-TTS, autores incl. Casanova/Ponti/Candido Jr./Aluísio; **licença CC BY-NC** | **CONFIRMADO com ressalva (licença = SEM-FONTE)** | Paper (2026.propor-1.81) confirma 70h, baselines YourTTS+F5-TTS em subset de 9h e todos os autores; MAS o HF nilc-nlp/certas_palavras está com README vazio e sem licença declarada — o "CC BY-NC" do dataset não é verificável nas fontes citadas (a CC-BY da ACL é do paper). Tratar licença como pendente antes de ingerir. |
| 5 | NURC-SP_ENTOA_TTS em licença MIT no HF nilc-nlp | **CONFIRMADO** | Página HF confirma licença MIT, ~8.440 amostras de fala espontânea NURC-SP com metadados de locutor — é de fato o dataset prosódico "usável sem trava". |
| 6 | Candido Junior agora é professor no IBILCE/UNESP e publicou no PROPOR 2026 o paper de TTS emocional (Brito/Leal) + speaker disentanglement (Matos/Ponti) | **CONFIRMADO** | Portal docente UNESP 446359 + página oficial IBILCE listam-no no Depto. de Ciências de Computação e Estatística; proceedings PROPOR 2026 contêm os dois papers com exatamente esses autores (título real tem "Uma Análise Comparativa" — diferença trivial). |
| 7 | Koel-TTS: LLM-TTS com preference alignment + CFG, coautoria Casanova (2025) | **CONFIRMADO** | arXiv 2502.05236 / EMNLP 2025 main (aclanthology 2025.emnlp-main.1076) confirmam receita (reward via ASR+speaker-verification + CFG) e Casanova entre autores — nota: o relatório citou só ResearchGate; a fonte primária é o arXiv/EMNLP. |
| 8 | Qwen3-TTS (jan/2026): baseline aberto multilíngue com pt, streaming e controle por instrução | **CONFIRMADO** | GitHub QwenLM/Qwen3-TTS + Simon Willison (22/jan/2026) confirmam release aberto (Apache 2.0), 10 línguas incl. português, streaming (~97ms TTFA) e controle por instrução natural — bônus: Apache 2.0 significa sem trava de licença, ao contrário do que a bateria NC do resto sugere. |

**Checagens auxiliares (de passagem):** `freds0/parler-tts-mini-v1.1-ptbr` existe no HF (Apache 2.0, ~600M params, BRSpeech-TTS ~200h) — sustenta o "Tem TTS treinado? Sim". GARAGEM (2026.propor-1.83) existe com Anderson Soares entre os 9 autores; título real é "Combining Real and Synthetic Speech for ASR Adaptation in Brazilian Portuguese" (GARAGEM é o nome do corpus, domínio automotivo/oficina — mais nichado do que o relatório sugere).

**Síntese:** 7/8 claims plenamente confirmados nas fontes primárias; a única lacuna real é a **licença do dataset Certas Palavras** (README vazio no HF — não assumir CC BY-NC; confirmar com o NILC antes de ingerir). Correções menores: citar Koel-TTS pelo arXiv/EMNLP em vez de ResearchGate; GARAGEM é corpus de domínio automotivo, não receita genérica. O ranking e os ganchos de colaboração ficam de pé.

---

# Cenário de pesquisadores/labs brasileiros de fala/TTS (estado 2025–2026)

---

## 1. Frederico Santos de Oliveira — UFMT (professor) + AKCIT/CEIA-UFG

- **Afiliação atual:** Professor no Depto. de Ciência da Computação da [UFMT](https://www.researchgate.net/profile/Frederico-Santos-De-Oliveira-2); pesquisador no [AKCIT (Centro de Competência EMBRAPII em Tecnologias Imersivas, UFG)](https://www.linkedin.com/in/fred-santos-oliveira/), doutorado pelo CEIA/UFG.
- **Últimos trabalhos (2024–2026):**
  - **[TAGARELA](https://arxiv.org/abs/2603.15326)** (aceito no **ICASSP 2026**) — dataset de podcasts com **8.972h** (versão ASR completa) + subset **clean-speech de ~2.800h para TTS**. Inclui **rotulagem automática de dialeto** (8.130h pt-BR / 842h pt-PT) feita com um classificador de sotaque (wav2vec fine-tunado em CORAA+CommonVoice+CML-TTS). **Licença do dataset: CC BY-NC-SA 4.0** (a CC-BY na página do arXiv é do *paper*, não do dado). Download: [HF freds0/TAGARELA](https://huggingface.co/datasets/freds0/TAGARELA); página: [fredso.com.br/TAGARELA](http://fredso.com.br/TAGARELA/). A página anuncia **"Models (Coming Soon)"** — ASR e TTS treinados exclusivamente no TAGARELA.
  - [CML-TTS](https://arxiv.org/html/2306.10097) (3.176h, 7 línguas, base MLS/audiobooks) + [checkpoint YourTTS multilíngue](https://github.com/freds0/CML-TTS-Dataset).
- **Tem TTS treinado? Sim:** no [HF freds0](https://huggingface.co/freds0) há **`parler-tts-mini-v1.1-ptbr`** ([link](https://huggingface.co/freds0/parler-tts-mini-v1.1-ptbr)), datasets **BRSpeech-TTS**, **BRSpeech-YT**, **expressive_synthetic_speech**, além dos YourTTS do CML-TTS. E os modelos TAGARELA vêm aí.
- **Abordagem distintiva:** engenharia de dados em escala (pipeline podcast → filtro de qualidade → rótulo de dialeto). É o "dono do dado" do ecossistema.
- **Uso/colaboração pro projeto carioca:** (a) pedir/replicar o **classificador de sotaque** para minerar um subset *carioca* do TAGARELA clean; (b) usar as 2.800h clean como base de pesquisa (NC — ok pro modo pesquisa do projeto); (c) monitorar os modelos "coming soon" como baseline pt-BR de verdade; (d) oferecer o rate_app (eval WER+perceptual localizada) como instrumento de avaliação dos modelos deles.

---

## 2. Edresson Casanova — NVIDIA

- **Afiliação atual:** Research Scientist na [NVIDIA](https://www.linkedin.com/in/edresson/) (ex-Coqui, doutorado USP).
- **Últimos trabalhos (2024–2026):**
  - [XTTS: a Massively Multilingual Zero-Shot TTS Model](https://arxiv.org/abs/2406.04904) (Interspeech 2024, 16 línguas incl. pt).
  - [Low Frame-rate Speech Codec](https://edresson.github.io/Low-Frame-rate-Speech-Codec/) (21,5 fps, 1,89 kbps — codec pra treinar speech-LLM rápido).
  - **Koel-TTS** (2025) — LLM-TTS com **preference alignment + classifier-free guidance** ([ref](https://www.researchgate.net/scientific-contributions/Edresson-Casanova-2292817725)).
  - [NanoCodec](https://www.researchgate.net/publication/396810305_NanoCodec_Towards_High-Quality_Ultra_Fast_Speech_LLM_Inference) (12,5 fps, 1,78 kbps) e [Magpie-TTS multilingual](https://build.nvidia.com/nvidia/magpie-tts-multilingual/modelcard) (multilíngue; presença de pt-BR a confirmar no modelcard).
  - Continua co-autor dos papers BR: **TAGARELA (ICASSP 2026)** e **Certas Palavras (PROPOR 2026)** — a ponte Brasil↔NVIDIA.
- **Abordagem distintiva:** zero-shot multilingual TTS + codecs neurais de baixo frame-rate pra speech-LLM (exatamente a família técnica do CSM/Moshi).
- **Artefatos abertos:** [TTS-Portuguese Corpus](https://github.com/Edresson/TTS-Portuguese-Corpus) (10,5h, single-speaker), YourTTS (código/pesos abertos), XTTS-v2 (pesos com licença Coqui CPML, não-comercial), codecs NeMo (pesos abertos).
- **Uso/colaboração:** Koel-TTS é a **receita publicada mais próxima do que o projeto faz** (LLM-TTS + alinhamento por preferência — casa com o flywheel de rating do rate_app); NanoCodec/LFSC são alternativas documentadas ao Mimi. Colaboração direta é difícil (empregado NVIDIA), mas ele responde a issues/GitHub e segue ativo nos papers BR.

---

## 3. Arnaldo Candido Junior — UNESP (São José do Rio Preto)

- **Afiliação atual:** Professor no IBILCE/**UNESP** ([portal docente](http://portaldocentes.unesp.br/portaldocentes/docentes/446359)) — saiu da UTFPR-Medianeira.
- **Últimos trabalhos (2024–2026):**
  - **PROPOR 2026:** *"Síntese de Voz Emocional Multi-Idioma para Português Brasileiro: Análise Comparativa de Abordagens de Ajuste Fino"* (Brito, Leal, Candido Junior) — fine-tuning de YourTTS pra emoção em pt-BR ([proceedings](https://aclanthology.org/volumes/2026.propor-1/)).
  - **PROPOR 2026:** *"Contrastive and Adversarial Disentanglement for Speaker Representations in Brazilian Portuguese"* (Matos, Candido Junior, **Ponti**).
  - Co-autor do corpus [Certas Palavras](https://aclanthology.org/2026.propor-1.81/) e de [corpus foneticamente rico para língua de baixo recurso](https://arxiv.org/pdf/2402.05794).
  - Clássico: [TTS-Portuguese Corpus](https://link.springer.com/article/10.1007/s10579-021-09570-4) (co-autor com Casanova/Ponti/Aluísio). [Scholar](https://scholar.google.com/citations?user=tT_zTwgAAAAJ).
- **Abordagem distintiva:** TTS de baixo recurso com fine-tuning barato (YourTTS-lineage), agora focado em **expressividade/emoção** e **desentrelaçamento de locutor** — os dois gaps exatos do projeto.
- **Uso/colaboração:** replicar a receita de fine-tuning emocional na voz carioca; embeddings desentrelaçados pra manter identidade de voz ao augmentar com dado público. É historicamente o acadêmico mais acessível do grupo (orienta alunos em projetos pequenos e práticos).

---

## 4. Anderson Soares + AKCIT/CEIA (UFG)

- **Afiliação:** Professor no [INF-UFG](https://ww2.inf.ufg.br/node/96), coordena o **CEIA** (maior centro de IA da América Latina, unidade EMBRAPII) e o **AKCIT** (centro EMBRAPII de tecnologias imersivas; [lab inaugurado mai/2025](https://www.andifes.org.br/2025/05/09/ufg-inaugura-laboratorio-avancado-de-tecnologias-imersivas/)).
- **Releases de voz (2024–2026):** o hub é a *fábrica* por trás de TAGARELA e CML-TTS, e em 2026 soltou mais dois artefatos:
  - **[BIPA](https://aclanthology.org/2026.propor-1.47/)** (PROPOR 2026; Sousa, Gris, N. Silva) — **53.353 palavras / 350.021 transcrições IPA em 6 dialetos, incluindo Rio de Janeiro**; G2P ByT5-small com PER 2,66%.
  - **GARAGEM** (PROPOR 2026, [paper](https://aclanthology.org/2026.propor-1.83/), grupo do Anderson Soares) — ASR de domínio com **fala sintética + real** combinadas.
  - Interspeech 2025: [SER multimodal com features prosódicas](https://arxiv.org/html/2506.02088v1) (Alef Iury, Gris et al.) e [FreeSVC (voice conversion zero-shot)](https://arxiv.org/pdf/2501.05586).
- **Abordagem distintiva:** escala + engenharia + funding EMBRAPII (projetos com empresas). Time de fala: Frederico, Lucas Gris, Alef Iury.
- **Uso/colaboração:** **BIPA é um asset direto pro G2P carioca** (transcrições IPA dialeto-Rio → léxico/feature de sotaque no pipeline); a porta EMBRAPII permite colaboração formal empresa-pequena↔centro; a receita GARAGEM (sintético+real pra adaptação) é aplicável ao flywheel de coleta.

---

## 5. Moacir Ponti — USP/ICMC + Mercado Livre

- **Afiliação:** Professor Associado [ICMC-USP](https://sites.google.com/site/moacirponti/) + lidera pesquisa de foundation models/agentes no [Mercado Livre](https://www.linkedin.com/in/moacir-antonelli-ponti/).
- **Últimos trabalhos (2024–2026):** co-autor de [Certas Palavras](https://aclanthology.org/2026.propor-1.81/) e do paper de **speaker disentanglement** (PROPOR 2026, com Candido Junior); historicamente co-autor de TTS-Portuguese Corpus e CORAA. Foco atual é ML geral/LLMs (fraude, agentes), não fala.
- **Abordagem distintiva:** fundamentos de representation learning + ponte indústria-academia.
- **Uso/colaboração:** consultivo — metodologia de avaliação e embeddings de locutor. Não é a aposta principal (bandwidth dele hoje está em LLM/indústria).

---

## 6. Grupo FalaBrasil — UFPA

- **Afiliação:** grupo de processamento de fala da UFPA ([GitHub](https://github.com/falabrasil) / [GitLab](https://gitlab.com/falabrasil)).
- **Estado 2025–2026:** ativo porém devagar: **ufpalign** (alinhamento fonético forçado pt-BR) atualizado jul/2025; **[speech-datasets](https://github.com/falabrasil/speech-datasets)** atualizado jun/2026 com migração dos datasets pro Hugging Face Hub. Resto do stack (kaldi-br, espnet-br, dicts-br, nlp-generator com G2P/silabificação) é 2020–2022.
- **Abordagem distintiva:** infraestrutura clássica (Kaldi-era): G2P, dicionários fonéticos, alinhamento forçado.
- **Uso/colaboração:** **ufpalign pra alinhamento em nível de fone do dataset-semente do Pedro** (útil pra métricas de prosódia F0/duração por segmento) e dicts-br como base de léxico. Usar como ferramenta, não como parceria ativa.

---

## 7. CPQD — Campinas (corporativo, fechado)

- **Estado 2025:** produto [CPQD Texto Fala](https://www.cpqd.com.br/solucoes/interacao-inteligente/texto-fala/) (docs [v4.9](https://speechweb.cpqd.com.br/tts/docs/4.9/Overview/Architecture.html)), [síntese neural](https://www.cpqd.com.br/noticias/nova-solucao-de-sintese-de-voz-neural-do-cpqd-proporciona-interacoes-digitais-mais-naturais-e-humanizadas/) com vozes Rosana/Carlos; [70+ clientes (ago/2025)](https://www.mobiletime.com.br/noticias/27/08/2025/tecnologias-de-voz-cpqd/); cria voz nova em **15 dias**, meta de clonagem com **4 minutos** de áudio e voz 100% sintética paramétrica.
- **Uso pro projeto:** zero artefato aberto. Serve como **benchmark comercial pt-BR** (o que o mercado corporativo aceita como "bom") e referência de pricing/posicionamento. Não é alvo de colaboração indie.

---

## 8. Novos grupos/artefatos 2025–2026

- **NILC/USP + C4AI — projeto [TaRSila](https://sites.google.com/view/tarsila-c4ai)** (Sandra Aluísio et al.): a resposta à pergunta "CORAA-v2" — o CORAA virou **família com 6 versões**: v1 CORAA-ASR (290h, CC BY-NC-ND), v2 **NURC-SP** (239h paulistano, [portal](http://tarsila.icmc.usp.br:8080/nurc/home)), v3 **[Certas Palavras](https://huggingface.co/datasets/nilc-nlp/certas_palavras/)** (~63–70h de rádio 1980s-90s, CC BY-NC, diálogo espontâneo multi-locutor com anotação de oralidade — [paper PROPOR 2026](https://aclanthology.org/2026.propor-1.81/) testando YourTTS e F5-TTS), v4 MuPe Life-Stories (365h), v5 SOFIA-FALA, v6 SER. Plus: **[NURC-SP_ENTOA_TTS](https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS)** (MIT) e os papers de **segmentação prosódica** (Galdino 2026 [Springer](https://link.springer.com/chapter/10.1007/978-3-032-15984-7_37); Craveiro 2025 classificadores acústicos).
- **PROPOR 2026 (Salvador, abr/2026)** concentrou a produção nova de fala pt-BR ([proceedings vol. 1](https://aclanthology.org/volumes/2026.propor-1/)): BIPA, GARAGEM, Certas Palavras, TTS emocional (UNESP), speaker disentanglement, [Whisper p/ história oral](https://aclanthology.org/2026.propor-1.30.pdf), detecção de gagueira.
- **Indie/comunidade:** fine-tunes de F5-TTS pt-BR no HF — [firstpixel/F5-TTS-pt-br](https://huggingface.co/firstpixel/F5-TTS-pt-br) (~330h, fev/2025) e [pedrohlopes/F5-TTS-pt-br](https://github.com/pedrohlopes/F5-TTS-pt-br) — precedentes de que um indie consegue fine-tunar flow-matching TTS pt-BR com centenas de horas.
- **Qwen3-TTS** (jan/2026, [nota](https://assuntonerd.com.br/2026/01/26/qwen3-tts-tts-open-source-com-streaming-de-baixa-latencia-e-controle-de-voz/)): não é BR, mas é o novo baseline aberto multilíngue com pt + streaming + controle por instrução — vale entrar na bateria de baselines do rate_app.

---

# Ranking: os 3 mais úteis pro projeto (com gancho concreto)

**1. Cluster AKCIT/CEIA-UFG (Frederico Oliveira + Lucas Gris + Alef Iury + Anderson Soares).** Donos do dado (TAGARELA 8.9k h com rótulo de dialeto), do G2P dialetal (BIPA com dialeto-Rio) e de modelos pt-BR "coming soon". **Gancho:** e-mail direto ao Frederico (perfil ativo em HF/LinkedIn) propondo troca: o projeto oferece a **eval perceptual carioca do rate_app + a voz-semente curada como test set de sotaque**, e pede (a) o checkpoint do classificador de sotaque do TAGARELA pra minerar um subset carioca, (b) early access aos modelos TAGARELA como baseline. Caminho formal existe via EMBRAPII se virar projeto pago.

**2. NILC/USP — Sandra Aluísio / TaRSila.** Únicos com **instrumento de avaliação de prosódia pt-BR** + datasets de fala espontânea (ENTOA_TTS em MIT, Certas Palavras como stress-test de diálogo ruidoso — exatamente o cenário "Maya conversacional"). **Gancho:** a tarefa #7 do projeto (transcrição prosódica à la Aluísio) já é o gancho — implementar a segmentação prosódica deles no pipeline, rodar na voz carioca e mandar os resultados como estudo de caso externo; propor co-avaliação usando o scorecard objetivo de "robótico".

**3. Arnaldo Candido Junior (UNESP).** Publicou em 2026 **exatamente o playbook que falta ao projeto**: fine-tuning emocional de TTS pt-BR + desentrelaçamento de locutor com poucos dados. **Gancho:** replicar o paper de síntese emocional na voz do Pedro (a receita usa YourTTS, barata de rodar na esteira RunPod), reportar divergências e propor um experimento conjunto "expressividade com sotaque carioca" — perfil de professor que abraça colaboração pequena e prática, sem burocracia de centro grande.

*(Menção honrosa: Edresson Casanova — não como parceiro formal, mas Koel-TTS/NanoCodec são as receitas NVIDIA mais próximas do stack CSM/Mimi do projeto, e ele historicamente responde a perguntas técnicas da comunidade BR.)*

**Nota de correção pro registro do projeto:** TAGARELA cresceu — o paper ICASSP 2026 descreve **8.972h totais (ASR)**; as "2.800h" da memória são o **subset clean pra TTS**. Licença confirmada CC BY-NC-SA 4.0 na [página oficial](http://fredso.com.br/TAGARELA/).

Sources: [TAGARELA arXiv](https://arxiv.org/abs/2603.15326) · [TAGARELA site](http://fredso.com.br/TAGARELA/) · [HF freds0](https://huggingface.co/freds0) · [XTTS](https://arxiv.org/abs/2406.04904) · [Edresson LFSC](https://edresson.github.io/Low-Frame-rate-Speech-Codec/) · [PROPOR 2026 proceedings](https://aclanthology.org/volumes/2026.propor-1/) · [Certas Palavras](https://aclanthology.org/2026.propor-1.81/) · [BIPA](https://aclanthology.org/2026.propor-1.47/) · [GARAGEM](https://aclanthology.org/2026.propor-1.83/) · [TaRSila](https://sites.google.com/view/tarsila-c4ai) · [NURC-SP_ENTOA_TTS](https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS) · [FalaBrasil GitHub](https://github.com/falabrasil) · [CPQD Texto Fala](https://www.cpqd.com.br/solucoes/interacao-inteligente/texto-fala/) · [CPQD Mobile Time ago/2025](https://www.mobiletime.com.br/noticias/27/08/2025/tecnologias-de-voz-cpqd/) · [UNESP portal docente](http://portaldocentes.unesp.br/portaldocentes/docentes/446359) · [Anderson Soares INF-UFG](https://ww2.inf.ufg.br/node/96) · [AKCIT lab](https://www.andifes.org.br/2025/05/09/ufg-inaugura-laboratorio-avancado-de-tecnologias-imersivas/) · [SER Interspeech 2025](https://arxiv.org/html/2506.02088v1) · [FreeSVC](https://arxiv.org/pdf/2501.05586) · [firstpixel/F5-TTS-pt-br](https://huggingface.co/firstpixel/F5-TTS-pt-br) · [Qwen3-TTS nota](https://assuntonerd.com.br/2026/01/26/qwen3-tts-tts-open-source-com-streaming-de-baixa-latencia-e-controle-de-voz/)

Fontes adicionais usadas na verificação: [ICASSP 2026 programa (TAGARELA AASP-P20.4)](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=13079) · [Koel-TTS arXiv 2502.05236](https://arxiv.org/abs/2502.05236) · [Koel-TTS EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1076/) · [HF freds0/TAGARELA](https://huggingface.co/datasets/freds0/TAGARELA) · [HF nilc-nlp/certas_palavras (sem licença declarada)](https://huggingface.co/datasets/nilc-nlp/certas_palavras) · [HF freds0/parler-tts-mini-v1.1-ptbr](https://huggingface.co/freds0/parler-tts-mini-v1.1-ptbr) · [IBILCE/UNESP docente](https://www.ibilce.unesp.br/#!/departamentos/cienc-comp-estatistica/docentes/arnaldo-candido-junior/) · [QwenLM/Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS) · [Simon Willison sobre Qwen3-TTS](https://simonwillison.net/2026/Jan/22/qwen3-tts/)