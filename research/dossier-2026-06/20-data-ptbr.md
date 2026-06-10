# Frente 4 — Dados pt-BR: estado em jun/2026 (web research, 2026-06-10)

> Atualização do dossiê `research/dossier/20-data-map.md` (2026-05-17). Foco: o que
> MUDOU. Veredito de licença explícito em tudo. Restrição dura do projeto:
> **só Apache-2.0 / MIT / CC-BY / CC0 entra no produto; NC/ND/pesquisa-only = veto.**

## TL;DR — o que mudou desde 2026-05-17

1. **TAGARELA (mar/2026)**: nasceu o maior corpus de fala pt já publicado — 8.972 h de
   podcasts (8.130 h pt-BR) + subset limpo de 2.800 h para TTS — **mas é
   CC-BY-NC-SA-4.0 → vetado para o produto** (o abstract do arXiv diz "CC BY 4.0";
   o card do HF e o site oficial dizem NC-SA — prevalece o card). Vale ouro como
   *eval/pesquisa* e como **receita de pipeline** publicada.
2. **NILC/TaRSila está soltando datasets NURC para TTS com tag MIT**:
   `nilc-nlp/NURC-SP_ENTOA_TTS` (MIT, espontâneo, com anotação prosódica) e
   `nilc-nlp/nurc_tts_24khz` (320 k amostras, **SP + Recife**, 24 kHz, ainda sem tag
   de licença). Se a tag MIT for intencional, é a **primeira via legal para fala
   espontânea pt-BR no produto** — mas conflita com o CC-BY-NC-ND histórico do
   CORAA/NURC ⇒ **confirmar com o NILC antes de treinar peso shippável**.
3. **Common Voice pt 25.0 (mar/2026)**: 228,79 h (187,33 h validadas), 3.817 falantes,
   **CC0 mantido** — agora distribuído via Mozilla Data Collective com termos extras
   (proibido re-hospedar; proibido tentar reidentificar falante). O modo
   *Spontaneous Speech* existe (21 línguas) mas **não tem português**.
4. **Emocional pt-BR continua ≈ 0 h commercial-safe.** Nada novo em 2025-26 além de
   SER em cima de CORAA (NC). O moat emoção×sotaque segue de pé.
5. **Expressivo aberto (design model)**: Expresso e EARS **continuam CC-BY-NC** (e as
   vozes `expresso/`/`ears/` dentro de `kyutai/tts-voices` são NC — não usar essas
   embeddings no produto). A novidade é **LibriQuote (CC-BY-4.0, 5,3 k h de falas
   expressivas de personagens + 12,7 k h de narração, EN)** — o melhor modelo de
   design aberto e commercial-safe de 2025. **Emilia-YODAS é CC-BY-4.0 mas não tem pt.**
6. **Câmara dos Deputados**: termos oficiais confirmados e mais finos do que o dossiê
   anterior: **só as transmissões AO VIVO de atividade legislativa são CC-BY-4.0**;
   programas produzidos (jornalismo, documentário) são CC-BY-NC-ND e Rádio Câmara é
   CC-BY-ND. **Ninguém publicou dataset de fala da Câmara até jun/2026** (HF só tem
   texto/tabular) — a lane continua aberta para nós.
7. **Regulação**: PL 2338 **não foi votado na Câmara** (adiado para 2026; comissão
   especial, relator Aguinaldo Ribeiro); texto em discussão restringe TDM livre a
   pesquisa sem fim comercial e cria **direito de remuneração + opt-out** para treino
   comercial. **PL 1460/2026 (réplicas digitais)** exige consentimento prévio para
   réplica de voz/imagem + watermark/metadata obrigatórios. ANPD (NT 12/2025 e
   sinalização de abr/2026) caminha para aceitar **legítimo interesse** como base
   legal de treino, com scraping na agenda regulatória 2025-26.

---

## (a) Datasets de fala pt-BR — estado e licenças (jun/2026)

### Tabela mestra (mudanças marcadas com ✦)

| Dataset | pt h | Tipo | Licença (verificada jun/2026) | Produto? | Nota |
|---|---|---|---|---|---|
| **CML-TTS (pt)** | ~1.100–1.200 | lido (audiobook) | CC-BY-4.0 ([OpenSLR 146](https://www.openslr.org/146/), [arXiv 2306.10097](https://arxiv.org/abs/2306.10097)) | ✅ | inalterado; seed de inteligibilidade |
| **MLS pt** | 160,96 (train) | lido | CC-BY-4.0 ([OpenSLR 94](https://www.openslr.org/94/)) | ✅ | inalterado |
| ✦ **Common Voice pt 25.0** | 228,79 (187,33 val.) | lido crowd | **CC0** + termos MDC: sem re-host, sem re-id ([Mozilla Data Collective](https://mozilladatacollective.com/datasets/cmn29f4cb017bmm07pd9yd8mw)) | ✅ | release 2026-03-22; 3.817 falantes; melhor diversidade de sotaque legal |
| ✦ CV Spontaneous Speech | **0 (sem pt)** | espontâneo crowd | CC0 | — | 21 línguas minoritárias, pt fora ([shared task](https://datacollective.mozillafoundation.org/datasets/cmfzu8u8wa555eq8onrk334h4)) |
| **TTS-Portuguese (Edresson)** | 10,5 | lido 1 spk | CC-BY-4.0 ([GitHub](https://github.com/Edresson/TTS-Portuguese-Corpus)) | ✅ | inalterado |
| ✦ **TAGARELA** | **8.972 (8.130 pt-BR); 2.800 clean p/ TTS** | podcast espontâneo | **CC-BY-NC-SA-4.0** ([HF freds0/TAGARELA](https://huggingface.co/datasets/freds0/TAGARELA), [site](https://freds0.github.io/TAGARELA/), [arXiv 2603.15326](https://arxiv.org/abs/2603.15326)) | ❌ | abstract arXiv diz CC-BY (errado vs card); fonte = Spotify *Cem Mil Podcasts* (acadêmica) ⇒ cadeia de licença suja de qualquer jeito. Usar só p/ eval/pesquisa |
| CORAA-ASR v1.1 | ~290 | espont.+preparado | CC-BY-NC-ND ([GitHub nilc-nlp/CORAA](https://github.com/nilc-nlp/CORAA)) | ❌ | inalterado |
| CORAA NURC-SP Audio Corpus | 239,68 | 100% espontâneo | NC-ND (projeto TaRSila) ([HF](https://huggingface.co/datasets/nilc-nlp/CORAA-NURC-SP-Audio-Corpus)) | ❌ | inalterado |
| ✦ **NURC-SP_ENTOA_TTS** | ~20–40 (8,4 k+ clips; configs prosodic/automatic) | **espontâneo p/ TTS, anotação prosódica** | **tag MIT no HF** ([HF nilc-nlp/NURC-SP_ENTOA_TTS](https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS)) | ⚠️ **confirmar** | criado 2025-01, atualizado 2026-05-29. Conflita com NC-ND upstream do NURC-SP ⇒ e-mail ao NILC antes de usar em peso shippável |
| ✦ **nurc_tts_24khz / nurc_tts** | 320 k clips (SP 120 k + **Recife 200 k**), 83–150 GB | espontâneo p/ TTS 24 kHz | **sem tag de licença ainda** ([HF nurc_tts_24khz](https://huggingface.co/datasets/nilc-nlp/nurc_tts_24khz)) | ⚠️ vigiar | criado mar/2026, ativo até 2026-05-28. **Recife = primeiro corpus TTS nordestino em escala**; quando a licença sair, pode mudar o jogo |
| ✦ nurc-sp-prosodic-segmentation, catna-* | n/d | segmentação prosódica | sem tag | ⚠️ | atividade NILC contínua (última 2026-06-02) — pipeline TTS espontâneo em construção |
| **CORAA-MUPE-ASR** (Museu da Pessoa) | 365 (289 entrevistas) | entrevista espontânea | CC-BY-NC-ND ([HF](https://huggingface.co/datasets/nilc-nlp/CORAA-MUPE-ASR), [COLING 2025](https://aclanthology.org/2025.coling-main.407/)) | ❌ | inalterado; + MuPe-Diversidades (amostras por estado, prosódia) |
| NURC-RJ (acervo digital) | dezenas h | espontâneo | **não declarada** no portal ([nurcrj.letras.ufrj.br](https://nurcrj.letras.ufrj.br/)) | ❌ tratar como fechado | sem release ML-ready; só transcrições/áudio de acervo |
| C-ORAL-BRASIL | 21,1 | diálogo espontâneo | CC-BY-NC-SA (corpus; o CC-BY que aparece é do *paper*) ([site](http://www.c-oral-brasil.org/)) | ❌ | inalterado |
| ✦ CETUC | ~145 | lido, 100 spk | **"exclusivamente para pesquisa"** (concessão CETUC→LaPS) ([falabrasil/speech-datasets](https://github.com/falabrasil/speech-datasets)) | ❌ | corrigido: download livre ≠ licença livre |
| ✦ SPIRA (refinement) | ~1 + 18 controle | fala/médico | **CC-BY-4.0** ([Zenodo 6672451](https://zenodo.org/records/6672451)) | ✅ (irrelevante p/ TTS) | pequeno, domínio respiratório |
| ✦ BRSpeech-TTS (freds0) | n/d | TTS | **sem tag de licença** ([HF API author=freds0](https://huggingface.co/freds0)) | ❌ até declarar | não confundir com BRSpeech-DF |
| ✦ BRSpeech-DF | 458 k utts (real+sintético) | anti-deepfake | verificar ([EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1780/)) | n/a | útil p/ EVAL de anti-spoof/watermark, não p/ treino de voz |
| VERBO | ~1,4 | emocional atuado | mediante pedido, licença unclear ([GitHub](https://github.com/jrtorresneto/VERBO-emotional-speech-dataset)) | ❌ | inalterado |
| CORAA-SER v1.0 | ~0,8 (625 áudios) | emocional espontâneo | NC ([GitHub ser-coraa-pt-br](https://github.com/rmarcacini/ser-coraa-pt-br)) | ❌ | inalterado |
| ✦ BrAccent / FakeBrAccent | 1.648 áudios / 746–1.545 | sotaques (7 classes, incl. **carioca/fluminense**) | não clara (acadêmica) ([ERI-ES 2025](https://sol.sbc.org.br/index.php/eries/article/view/38243)) | ❌ | pequeno; útil como ref. de taxonomia de sotaque |
| ✦ **SOTAQUE (sotaque.ia.br)** | embrionário (lançado ~2026) | crowdsourcing espontâneo c/ sotaque | **CDLA-Permissive-2.0** ([sotaque.ia.br](https://sotaque.ia.br/), [GitHub](https://github.com/fabriciocarraro/projeto-sotaque)) | ✅ (quando tiver volume) | caipira/baiano/nortista/gaúcho/mineiro/paulistano/carioca; consentimento LGPD embutido. **Monitorar/contribuir/parceria** |
| ✦ **Granary (NVIDIA, pt)** | pt incluído (subsets `pt_ytc` 497 k rows + `pt_voxpopuli` 4,31 M rows; total 643 k h ASR/25 línguas) | YouTube CC + VoxPopuli pseudo-label | **CC-BY-3.0** ([HF nvidia/Granary](https://huggingface.co/datasets/nvidia/Granary), [arXiv 2505.13404](https://arxiv.org/abs/2505.13404)) | ✅ | maior fonte commercial-safe de fala pt "in-the-wild"; qualidade ASR-grade (não TTS-grade) |
| ✦ YODAS / YODAS-Granary | pt presente (centenas de h CC) | YouTube CC | CC-BY-3.0 ([espnet/yodas](https://huggingface.co/datasets/espnet/yodas), [espnet/yodas-granary](https://huggingface.co/datasets/espnet/yodas-granary)) | ✅ | áudio cru pt com licença CC dos uploaders |

### PROPOR 2026 (Salvador, abr/2026) — o que saiu de relevante

Proceedings: [aclanthology.org/volumes/2026.propor-1/](https://aclanthology.org/volumes/2026.propor-1/) (117 + 42 papers).

- **Certas Palavras** — 70 h de diálogos espontâneos multi-falante de programa de rádio
  anos 80-90, anotação manual de marcadores de oralidade; pensado como *benchmark de
  robustez para TTS conversacional* ([2026.propor-1.81](https://aclanthology.org/2026.propor-1.81/)).
  ⚠️ Áudio de rádio comercial = copyright de terceiros; CC-BY do ACL cobre o *paper*,
  não o áudio. Não achei release público do corpus ⇒ tratar como pesquisa-only.
  **Mesmo padrão do nosso problema: o registro casal/diálogo segue sem lane comercial.**
- **BIPA** — 350 k transcrições IPA de 53 k palavras em **6 dialetos (incl. Rio de
  Janeiro)**, G2P ByT5 com 2,66% PER ([2026.propor-1.47](https://aclanthology.org/2026.propor-1.47/)).
  Diretamente útil pro nosso front-end de sotaque carioca (G2P regional). Fonte =
  Wiktionary (CC-BY-SA — atenção share-alike se redistribuirmos o léxico).
- **GARAGEM** — ASR de domínio automotivo ([2026.propor-1.83](https://aclanthology.org/2026.propor-1.83/)); irrelevante p/ nós.
- **CoDEl-BR** — corpus de debates eleitorais municipais ([2026.propor-1.64](https://aclanthology.org/2026.propor-1.64/));
  registro adversarial 2-party; checar licença se quisermos eval de overlap.

### Leitura estratégica (a)

- O **pool CC-BY/CC0 de pt-BR lido cresceu pouco** (CV +~60 h desde 2025) — continua
  ~1,5 k h, suficiente para LoRA/CPT de inteligibilidade. Nada disso resolve
  conversacional.
- A fronteira moveu em **espontâneo**: TAGARELA (NC) e os releases NURC-TTS do NILC
  (MIT?/sem tag). A ação de maior alavancagem da frente de dados é **um e-mail ao
  NILC** confirmando a intenção da tag MIT do `NURC-SP_ENTOA_TTS` e a licença
  planejada do `nurc_tts_24khz`. Se confirmarem MIT/CC-BY ⇒ primeiro corpus
  espontâneo pt-BR utilizável no produto (e com Recife = nordestino).
- **Emoção pt-BR commercial-safe ≈ 0 h** se mantém ⇒ gravação dirigida do Pedro
  continua sendo o moat, sem mudança de plano.

---

## (b) Corpora expressivos/emocionais abertos (modelo de design)

| Corpus | Lang | Escala | Licença | Uso p/ nós |
|---|---|---|---|---|
| **Expresso** (Meta) | EN | 40 h (11 lidas + 30 diálogo improvisado, 26 estilos) | **CC-BY-NC-4.0** ([speechbot.github.io/expresso](https://speechbot.github.io/expresso/), [arXiv 2308.05725](https://arxiv.org/abs/2308.05725)) | método/eval apenas. ⚠️ As vozes `expresso/` em [kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices) são NC — **não usar essas embeddings no produto Moshi**; usar `voice-donations/` (CC0), `vctk/` e `cml-tts/fr` (CC-BY) ou vozes próprias |
| **EARS** | EN | 100 h, 107 spk, 22 emoções | **CC-BY-NC-4.0** ([github.com/facebookresearch/ears_dataset](https://github.com/facebookresearch/ears_dataset)) | método/eval apenas (idem NC em kyutai/tts-voices) |
| **Emilia / Emilia-Large** | EN ZH DE FR JA KO | 101 k h (NC) + **Emilia-YODAS 114 k h CC-BY-4.0** | mista por subset ([HF amphion/Emilia-Dataset](https://huggingface.co/datasets/amphion/Emilia-Dataset), [arXiv 2501.15907](https://arxiv.org/abs/2501.15907)) | **sem pt em nenhuma versão**. Valor = o *pipeline* (ver (d)) e o padrão "CC-BY quando a fonte é YouTube-CC" |
| ✦ **LibriQuote** (set/2025) | EN | **5,3 k h falas expressivas de personagens + 12,7 k h narração**, 3.300 spk | **CC-BY-4.0** ([HF gasmichel/LibriQuote](https://huggingface.co/datasets/gasmichel/LibriQuote), [arXiv 2509.04072](https://arxiv.org/abs/2509.04072)) | **melhor modelo de design aberto p/ expressividade**: pseudo-labels de estilo extraídos do contexto narrativo ("sussurrou", "gritou suavemente"). Padrão replicável em pt com audiobooks PD/LibriVox-pt e o nosso roteiro dirigido |
| ✦ LAION's Got Talent / EmoNet-Voice | EN DE ES FR | ~5 k h sintético (GPT-4o audio); 110 h+ públicas | licença não declarada no card ([HF laion/laions_got_talent](https://huggingface.co/datasets/laion/laions_got_talent)) | ref. de taxonomia (40 emoções + vocal bursts) e de *recording script* sintético; ⚠️ proveniência OpenAI-output — não treinar voz do produto com isso |
| LibriTTS-R | EN | 585 h | CC-BY-4.0 | inalterado; prosódia limpa |
| EmoV-DB / CREMA-D / JL-Corpus | EN | 5–9 h | CC0-ish / ODbL / CC-BY | inalterado, pequenos |
| MSP-Podcast / MSP-Conversation | EN | 409 h / 74 h | acadêmica (UTD), via assinatura | inalterado — segue no Park |

**Padrões de design a copiar (sem copiar dados):**
1. **Expresso**: pares de diálogo improvisado por estilo (nosso roteiro de gravação
   2-party já segue isso).
2. **LibriQuote**: rotular expressividade por *contexto* (verbo de fala + advérbio) em
   vez de categoria fechada — encaixa direto no plano "base implícita + prompt de
   estilo" do Step-Audio-2/GRPO.
3. **EARS**: 22 emoções + leitura livre + não-verbais (risada, suspiro) por falante —
   usar como checklist do kit de gravação do Pedro.

---

## (c) Câmara dos Deputados e Judiciário

### Câmara — termos confirmados (mais finos que o dossiê de mai/2026)

Fonte oficial: [Termos de Uso TV Câmara](https://www.camara.leg.br/tv/termos-de-uso/).

| Conteúdo | Licença | Treino comercial? |
|---|---|---|
| **Transmissões ao vivo de atividade legislativa** (Plenário, comissões, audiências públicas) | **CC-BY-4.0** | ✅ sim, com atribuição |
| Conteúdo produzido (telejornais, reportagens, documentários TV Câmara) | CC-BY-NC-ND | ❌ |
| Rádio Câmara | CC-BY-**ND** | ❌ (treino = derivação; ND mata) |

- Acervo de áudio bruto: [Arquivo Sonoro](https://imagem.camara.leg.br/internet/audio/);
  metadados/discursos pela [API de Dados Abertos](https://dadosabertos.camara.leg.br/).
- **Ninguém montou dataset de fala com isso até jun/2026**: busca no HF por "camara"
  só retorna texto/tabular (ulysses-ner-br, ementas etc.). O análogo europeu
  [ParlaSpeech](https://clarinsi.github.io/parlaspeech/) (v3.0, [arXiv 2511.01619](https://arxiv.org/abs/2511.01619))
  cobre HR/CZ/PL/SR — **sem pt** — mas o método deles (alinhar áudio oficial com
  transcrição taquigráfica) é exatamente a receita para a Câmara: áudio CC-BY +
  notas taquigráficas abertas = pares áudio-texto de graça, sem ASR pseudo-label.
- Ferramentas prontas só para o lado texto: [speechbr](https://github.com/dcardosos/speechbr),
  [raspador-discursos-camara](https://github.com/dados-congresso/raspador-discursos-camara).
  O lado áudio teríamos que montar (diarização pyannote + alinhamento; cf. pipeline (d)).
- ⚠️ Senado/TV Senado continua proprietário (não confundir). Registro = formal/
  adversarial; serve p/ robustez ASR/full-duplex (apartes, sobreposição), não para o
  registro casual da Maya.

### Judiciário

- **STF**: áudio integral dos julgamentos publicado desde 2020 (Informativo/YouTube)
  ([notícia oficial](https://noticias.stf.jus.br/postsnoticias/informativo-stf-passa-a-oferecer-audio-integral-dos-julgamentos-e-trechos-em-video-no-youtube/)).
  Atos oficiais não têm proteção autoral (**Lei 9.610, art. 8º, IV** — "atos oficiais")
  ⇒ lane juridicamente forte para áudio de julgamento.
- **TJSP** grava audiências e usa IA interna para atas, mas os autos/áudios **não são
  públicos em massa** (sigilo processual + LGPD) ([TJSP](https://www.tjsp.jus.br/Noticias/Noticia?codigoNoticia=61878)).
- **Nenhum dataset público de fala do judiciário brasileiro existe até jun/2026**
  (buscas HF/OpenSLR/arXiv vazias). Mesma conclusão da Câmara: lane aberta, registro
  formal, útil só como dado de robustez/full-duplex — baixa prioridade vs gravação
  própria.

---

## (d) Pipelines dataset-from-internet (2026) e risco legal no Brasil

### Pipelines

| Pipeline | Estado jun/2026 | Notas |
|---|---|---|
| **Emilia-Pipe** ([Amphion](https://github.com/open-mmlab/Amphion/blob/main/preprocessors/Emilia/README.md)) | referência; última grande att fev/2025 (Emilia-Large) | 6 etapas (padronização → source separation → diarização → VAD → ASR → filtro). Suporte oficial a 6 línguas, **pt não incluso mas adaptável** (Whisper cobre pt). Código no repo Amphion |
| **NeMo Speech Data Processor** ([docs](https://nvidia.github.io/NeMo-speech-data-processor/)) | ativo; usado no Granary | processors declarativos; a receita Granary (segmentação → ASR 2-pass → LID → filtro de texto → PnC) está publicada ([arXiv 2505.13404](https://arxiv.org/abs/2505.13404)) |
| ✦ **Receita TAGARELA** ([arXiv 2603.15326](https://arxiv.org/html/2603.15326v1)) | mar/2026 — receita pt mais recente publicada | FLAC 16 k → clipes 5-20 s em silêncios → **pyannote** diarização → detector de overlap (XLS-R) → **bootstrap de transcrição: ElevenLabs Scribe em seed → fine-tune Whisper-large-v3 pt → transcreve o resto** → **Vocos como denoiser** → clustering de falante HDBSCAN → classificador BR/PT. Tudo replicável com componentes MIT/Apache; é o blueprint para qualquer coleta nossa (Câmara, YouTube-CC, acervo próprio) |
| YODAS/YTC harvesting | ativo | filtrar YouTube por licença CC-BY do uploader = única coleta web em escala com lane comercial limpa (padrão Emilia-YODAS/Granary/YouTube-Commons) |

**Podcasts pt-BR**: a fonte (Spotify *Cem Mil Podcasts*, [arXiv 2209.11871](https://arxiv.org/abs/2209.11871),
76 k h) é acadêmica e o portal oficial ([podcastsdataset.byspotify.com](https://podcastsdataset.byspotify.com/))
está fora do ar/sem manutenção. TAGARELA herda essa cadeia ⇒ mesmo o subset "clean"
não tem caminho comercial. Para podcast comercial-safe: só com acordo direto com
podcasters (ou nosso próprio podcast — Pedro gravando com convidados, consentimento
LGPD assinado = dado conversacional 2-party autêntico e 100% nosso).

### Risco legal Brasil (jun/2026) — scrappar filmes/novelas/podcasts para sotaques

**Status do PL 2338/2023 (Marco Legal da IA):** aprovado no Senado em 10/12/2024;
na Câmara desde mar/2025 em comissão especial (presid. Luísa Canziani, relator
Aguinaldo Ribeiro); **votação adiada para 2026 e ainda não realizada até jun/2026**
([tramitação](https://www25.senado.leg.br/web/atividade/materias/-/materia/157233),
[comissão especial](https://www2.camara.leg.br/atividade-legislativa/comissoes/comissoes-temporarias/especiais/57a-legislatura/comissao-especial-sobre-inteligencia-artificial-pl-2338-23),
[adiamento](https://desinformante.com.br/votacao-do-marco-da-ia-fica-para-2026-em-meio-a-impasses-politicos-e-criticas-ao-texto)).
No texto em discussão (mineração de dados / direitos autorais):

- **TDM livre só para pesquisa** (instituições de pesquisa, jornalismo, museus,
  arquivos, bibliotecas, educação), sem finalidade comercial e com acesso legítimo.
- **Uso comercial de obra protegida em treino ⇒ direito de remuneração ao titular** +
  possibilidade de **opt-out**; transparência via sumário de datasets
  ([Câmara](https://www.camara.leg.br/noticias/1159193-projeto-que-regulamenta-uso-da-inteligencia-artificial-no-brasil), [Demarest, mar/2026](https://www.demarest.com.br/en/inteligencia-artificial-reacende-debates-na-camara-dos-deputados/)).
- Implicação direta: **scrappar novela/filme/podcast para treinar sotaque é a pior
  combinação possível** — obra audiovisual protegida (sem exceção TDM vigente na Lei
  9.610), voz de ator = direito de personalidade (CF art. 5º, X), dublagem é pauta
  sindical quente ([Câmara, dublagem](https://www.camara.leg.br/noticias/1092791-segmento-de-dublagem-pede-protecao-legal-contra-uso-de-voz-gerada-por-inteligencia-artificial/)),
  e o PL 2338 só *aumenta* a exposição (remuneração retroativa-ish + transparência
  obrigatória de dataset tornaria o uso detectável). **Veto total mantido.**

**LGPD/ANPD:**
- Agenda Regulatória ANPD 2025-26 prioriza **IA** e **data scraping** ([ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/documentos-tecnicos-orientativos)).
- **Nota Técnica 12/2025** consolida a tomada de subsídios sobre IA/decisões
  automatizadas (art. 20 LGPD) — sem obrigação nova, mas indica direção: transparência,
  dados pessoais em treino, mitigação de risco ([análise](https://privacidade.org.br/analise-critica-da-nota-tecnica-no-12-2025-con1-cgn-anpd/)).
- Abr/2026: ANPD sinaliza que **legítimo interesse pode fundamentar treino de IA**
  ([Mobile Time, 29/04/2026](https://www.mobiletime.com.br/noticias/29/04/2026/anpd-treinamento-ia/)) —
  bom para dados *não sensíveis*; mas **voz é dado pessoal e, como biometria,
  sensível** ⇒ para vozes identificáveis, consentimento continua sendo a base segura.
  Estudo preliminar ANPD sobre IA generativa já tratava scraping de dado público como
  tratamento sob a LGPD ([FPF](https://fpf.org/blog/brazils-anpd-preliminary-study-on-generative-ai-highlights-the-dual-nature-of-data-protection-law-balancing-rights-with-technological-innovation/)).
- ✦ **PL 1460/2026 (Tabata Amaral + 5): marco das "réplicas digitais"** — exige
  **autorização prévia do titular** para criar/difundir réplica de voz/imagem por IA;
  **identificadores visíveis + metadados + watermark imperceptível obrigatórios**;
  responsabilidade solidária e objetiva de usuário e agente de IA; direitos
  post-mortem por 70 anos; exceção para paródia/sátira/crítica
  ([PDT na Câmara, mar/2026](https://www.pdtnacamara.com.br/dorinaldo-assina-projeto-que-estabelece-normas-para-o-uso-de-imagem-por-ia/noticias/mario/35471/23/56/13/30/03/2026/),
  [Congresso em Foco](https://www.congressoemfoco.com.br/noticia/117708/projeto-cria-regras-para-uso-de-imagem-e-voz-em-videos-feitos-por-ia)).
  **Nos afeta diretamente como produto de voz**: nosso desenho (consentimento por
  escrito de cada voz + watermark — dossiê 70) já fica *compliance-by-design* com o
  texto proposto. Acompanhar tramitação.
- Eleições 2026 = pressão regulatória extra sobre clonagem de voz no 2º semestre
  ([Público, jun/2026](https://www.publico.pt/2026/06/02/publico-brasil/noticia/ressuscitar-mortos-clonar-vozes-ia-ja-influencia-eleicoes-testara-brasil-2026-2176966)).

**Matriz de risco por fonte (treino comercial, jun/2026):**

| Fonte | Autoral | LGPD/voz | Veredito |
|---|---|---|---|
| Gravação própria com consentimento | ✅ | ✅ | **fazer (moat)** |
| CC0/CC-BY (CV, CML, MLS, Granary/YODAS-CC, Câmara-ao-vivo) | ✅ atribuição | ⚠️ baixo (dado público, finalidade compatível; sem re-id) | **ok** |
| Podcasts scraped / TAGARELA | ❌ (copyright + NC) | ⚠️ | pesquisa/eval só |
| Filmes/novelas/dublagem | ❌❌ | ❌ (voz de ator) | **veto total** |
| YouTube não-CC (sotaques) | ❌ ToS + autoral | ⚠️ | veto p/ produto; cinza até p/ pesquisa |
| Judiciário (STF julgamentos) | ✅ (art. 8º Lei 9.610) | ⚠️ vozes de agentes públicos em ato público | ok c/ parcimônia |

---

## Decisões recomendadas (delta vs plano atual)

1. **Mantém**: gravação dirigida do Pedro como única fonte de emoção×sotaque carioca —
   nada em 2025-26 ameaçou esse moat (emocional pt-BR aberto continua ≈ 0 h).
2. **Ação nova nº 1 (custo ~0)**: e-mail ao NILC/TaRSila confirmando a tag **MIT** do
   `NURC-SP_ENTOA_TTS` e a licença futura do `nurc_tts_24khz` (SP+Recife). Se
   confirmada ⇒ adicionar ao mix de CPT/LoRA como primeira fala espontânea legal.
3. **Ação nova nº 2**: registrar TAGARELA como **eval set** (WER conversacional,
   robustez de sotaque) — nunca em peso shippável. Adotar a receita de pipeline dele
   (pyannote + bootstrap Whisper-FT + Vocos) para qualquer coleta nossa.
4. **Câmara**: continua a única fonte 2-party CC-BY em escala; restringir coleta às
   **transmissões ao vivo** (CC-BY-4.0), nunca programas produzidos (NC-ND) nem Rádio
   Câmara (ND). ParlaSpeech dá o método de alinhamento com notas taquigráficas.
5. **Kyutai stack**: auditar quais vozes/embeddings usamos — `expresso/` e `ears/` do
   `kyutai/tts-voices` são **NC**; usar CC0/CC-BY ou vozes próprias.
6. **Design de expressividade**: adicionar **LibriQuote (CC-BY)** como referência
   primária de rotulagem de estilo por contexto; manter Expresso/EARS como leitura.
7. **Compliance**: desenhar o produto já compatível com PL 1460/2026 (consentimento
   explícito por voz + watermark imperceptível + metadata de proveniência) e manter
   sumário de datasets de treino (PL 2338, transparência).
8. **Monitorar**: (i) votação do PL 2338 na Câmara (2026); (ii) licença do
   `nurc_tts_24khz`; (iii) crescimento do SOTAQUE (CDLA-Permissive — possível canal de
   sotaques com consentimento nativo); (iv) se a Emilia adiciona pt via YODAS.

## Park (não agir sem decisão)
- Contato NILC (item 2 acima) — único contato recomendado JÁ.
- MSP-Podcast (UTD, assinatura) — inalterado.
- Autores de Certas Palavras / CoDEl-BR se quisermos eval de diálogo ruidoso.
- SOTAQUE: avaliar contribuição/parceria quando houver volume.

---
*Fontes primárias citadas inline. Verificação cruzada de licenças feita em
2026-06-10 contra HF cards/API (tags `license:`), sites oficiais e papers; onde card
e paper divergem (TAGARELA), o card/site oficial prevalece e a divergência está
registrada.*
