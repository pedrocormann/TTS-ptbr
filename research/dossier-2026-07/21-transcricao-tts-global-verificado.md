# Transcrição/pontuação otimizada pra TTS conversacional — panorama global 2023–2026

## VERIFICAÇÃO (verificador adversarial, 02/jul/2026)

Metodologia: 8 claims mais load-bearing checados na fonte primária citada (WebFetch/leitura do PDF integral) + 1 busca independente cada.

| # | Claim | Veredito | Justificativa |
|---|---|---|---|
| 1 | **Receita Emilia-Pipe**: WhisperX com Whisper *medium*, filtro DNSMOS < 3.0, filtro de outlier de duração, sem restaurador de pontuação extra | **CONFIRMADO** (com 2 nuances) | Paper confirma verbatim: "Whisper-Medium" via WhisperX, "retaining only speech data with a score higher than 3.0", nenhum restaurador de P&C mencionado. Nuance 1: o outlier é por **duração média de fone** (1.5×IQR), não exatamente "por caractere". Nuance 2: F5-TTS e MaskGCT treinaram em Emilia (100k h cada — confirmado nos papers deles), mas **CosyVoice NÃO**: treinou em corpus interno de 170k h (130k zh); a parte "base de CosyVoice" é imprecisa/refutada. |
| 2 | **DisfluencySpeech**: verbatim MCD 3.68/CER 15% vs transcrição limpa MCD 5.26/CER 60% (não converge) | **CONFIRMADO** | Tabela II do paper bate exato (A: 3.68/15.01; B: 5.26/60.07; C: 4.87/55.66) e o texto diz verbatim "the training of the Transformer models for transcript B and transcript C both failed to converge"; busca independente (HF/GitHub AMAAI-Lab) confirma. É a evidência mais forte do relatório e está correta. |
| 3 | **Granary**: Whisper-large-v3 em 2 passadas + P&C com Qwen-2.5-7B + guardrail de 5% CER | **CONFIRMADO** | Quote exato encontrado no paper: "If Qwen's output deviated from Whisper's transcriptions by more than a 5% character error rate, the original pseudo-labels were retained"; 2-pass (LID→transcrição), 25 línguas, filtros de alucinação e LID confirmados. Nuance de escala: ~1,06M h brutas → **643k h filtradas**. |
| 4 | **Vietnamita**: re-pontuar o texto onde o áudio pausa → MOS ~4.1 | **CONFIRMADO com ressalva relevante** | O relatório funde DOIS papers distintos: o arxiv 2004.09607 (Oriental COCOSDA) reporta MOS 4.1 vs 4.3 natural com "prosodic punctuation insertion"; o da ACL Anthology (VLSP 2020, mesmo grupo VAIS) detalha o método — **vírgula inserida onde o word-timestamp do ASR mostra silêncio > 0.3s** — mas alcançou MOS **3.31** vs 4.22 humano. A direção (pausa→pontuação melhora prosódia) está confirmada nos dois; o número 4.1 pertence só ao primeiro. |
| 5 | **Balalaika**: pontuação restaurada + stress lexical complementares, ganhos de MOS, MOS-filtering estrito ajuda | **CONFIRMADO** | Abstract confirma verbatim: "ablations confirm complementary benefits of stress and punctuation and improved synthesis with stricter MOS filtering"; 5.1k h russo, semantic VAD + ensemble ROVER confirmados; página arxiv diz "Accepted to Interspeech 2026". Título real: "A Data-Centric Framework for Addressing Phonetic and Prosodic Challenges in Russian Speech Generative Models". |
| 6 | **Székely fillers**: anotar só a LOCALIZAÇÃO do filler foi preferido vs especificar o tipo | **CONFIRMADO** (com escopo) | PDF primário lido integral: "synthesiser-predicted FP types from location-only annotation often were preferred over specifying the ground-truth type". Nuance: a preferência pelo GenFP só é estatisticamente significativa em FPs no **meio** do enunciado (p=0.02/0.04); no início, empate (p>0.30). A recomendação nº 6 do relatório continua válida. |
| 7 | **CrisperWhisper**: verbatim + timestamps precisos via retokenização + DTW na cross-attention, SOTA em fillers, checkpoint CC-BY-NC | **CONFIRMADO** | Abstract confirma retokenização + DTW nos cross-attention scores, SOTA em "verbatim speech transcription, word segmentation, and the timed detection of filler events" e mitigação de alucinação; model card HF confirma licença **cc-by-nc-4.0** e transcrição verbatim de um/uh — a trava de proveniência do relatório está certa. |
| 8 | **PSST**: Whisper fine-tunado emite fronteiras de unidade entoacional (IU) junto da transcrição | **CONFIRMADO** | PDF primário (CoNLL 2023) confirma: fine-tune do Whisper (versão English-only, 764M) no corpus SBCSAE com token dedicado de fronteira de IU, robusto em dados out-of-distribution (IViE, inglês britânico) — só inglês, como o relatório assume ao propor a versão pt-BR como pesquisa nova. |

**Balanço**: 8/8 claims centrais confirmados na fonte primária; nenhuma recomendação da seção "O QUE ADOTAR" cai. Três correções pontuais a registrar: (a) CosyVoice não foi treinado em Emilia (remover da lista de "base de"); (b) o esquema vietnamita explícito (gap > 0.3s → vírgula) vem do paper VLSP com MOS 3.31 — o MOS 4.1 é do paper irmão COCOSDA; (c) filtro Emilia é por duração de fone, não por caractere (implementação equivalente na prática). A "lacuna honesta" declarada no fim da seção 5 (falta head-to-head em LLM-TTS moderno) se sustenta: nenhuma das buscas achou estudo que a feche.

---

## 1. Como labs de ponta transcrevem dado conversacional pra TTS

**Emilia / Emilia-Pipe (o padrão de-facto em escala)** — pipeline aberto que virou base de CosyVoice, F5-TTS, MaskGCT: padronização → separação de fontes → diarização → segmentação fina por VAD → ASR (WhisperX batched, modelo *medium*) → filtragem. A pontuação usada é **a do próprio Whisper** (nenhum restaurador extra); qualidade vem da FILTRAGEM: remove segmentos com DNSMOS < 3.0, baixa confiança de language-ID e **outliers de duração média por caractere** (proxy barato de desalinhamento texto-áudio).
- https://arxiv.org/html/2407.05361v3 (Emilia) e https://arxiv.org/pdf/2501.15907 (Emilia-Large)
- https://www.emergentmind.com/topics/emilia-data-processing-pipeline

**CasualConversations (Meta) — guideline verbatim público mais explícito**: manter hesitações e disfluências ("uh", "um"), palavras repetidas como faladas, coloquialismos ("gonna", "sorta"); sons não-fala (música, risada) viram **tags**; pausas longas viram tag `<no-speech>`.
- https://arxiv.org/pdf/2111.09983

**Granary (NVIDIA/NeMo, ~1M h, 25 línguas) — receita moderna de pseudo-label**: Whisper-large-v3 em duas passadas + verificação de LID + filtro de alucinação + **restauração de P&C com LLM (Qwen-2.5-7B)** com guardrail: se a saída do LLM desviar >5% CER do Whisper, mantém o pseudo-label original. Parakeet/Canary saem com P&C nativo porque o dado de treino preserva P&C.
- https://arxiv.org/pdf/2505.13404 · https://github.com/NVIDIA/NeMo-speech-data-processor/tree/main/dataset_configs/multilingual/granary
- https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3

**WhisperD** — Whisper fine-tunado pra INCLUIR fillers (uh/um) em fala com disfluência; mostra que o Whisper vanilla sistematicamente apaga fillers ("intended transcription style") e que fine-tune pequeno corrige. https://arxiv.org/abs/2505.21551

**CrisperWhisper** — Whisper ajustado (retokenização + DTW na cross-attention) pra transcrição **verbatim** com timestamps precisos; SOTA em detecção temporal de fillers e segmentação de palavra; reduz alucinação. Código: https://github.com/nyrahealth/CrisperWhisper · paper: https://arxiv.org/abs/2408.16589 (checkpoint no HF é CC-BY-NC — ok pro modo pesquisa de vocês, rastrear proveniência).

**DisfluencySpeech** — dataset single-speaker com 3 camadas de transcrição (A: verbatim + paralanguage; B: sem eventos não-fala; C: sem false starts). https://arxiv.org/pdf/2406.08820

**Eventos como tags no texto — prática dos modelos atuais**: CosyVoice usa `[laughter]`, `[breath]` inline no treino/inferência (https://arxiv.org/pdf/2412.10117, https://huggingface.co/FunAudioLLM/CosyVoice-300M-Instruct); Dia (Nari Labs) usa `(laughs)`, `(sighs)`, `(clears throat)` etc. (https://github.com/nari-labs/dia); NonverbalTTS publicou pipeline de tagging automático + validação humana (17h, risadas/tosse/etc.) e fine-tune com essas tags empata com CosyVoice2 (https://arxiv.org/abs/2507.13155). Expresso (Meta) é a referência de estilos expressivos lidos+improvisados (https://speechbot.github.io/expresso/).

**EARS**: 100h anecoicas 48kHz, mas só a parte LIDA tem transcrição — a parte conversacional/emocional não; não é fonte de guideline de transcrição conversacional. https://arxiv.org/html/2406.06185v2

## 2. Punctuation restoration multilíngue com pt

| Modelo | pt? | Base/treino | Licença | Notas |
|---|---|---|---|---|
| [kredor/punctuate-all](https://huggingface.co/kredor/punctuate-all) | **sim** | xlm-roberta-base, Europarl 12 línguas | MIT | F1: `.` 0.95, `,` 0.86, `?` 0.86, `:` 0.58, `-` 0.39 |
| [oliverguhr/fullstop-punctuation-multilang-large](https://huggingface.co/oliverguhr/fullstop-punctuation-multilang-large) (+ pacote [deepmultilingualpunctuation](https://github.com/oliverguhr/deepmultilingualpunctuation)) | não (EN/DE/FR/IT) | xlm-roberta | MIT | o pacote aceita o kredor como backbone → vira pt |
| [dominguesm/bert-restore-punctuation-ptbr](https://huggingface.co/dominguesm/bert-restore-punctuation-ptbr) | **sim (pt-BR nativo)** | BERTimbau + WikiLingua | (checar card) | restaura `! ? . , - : ; '` + caixa |
| NeMo P&C | treinável | BERT token-classification | Apache-2.0 | sem checkpoint pt pronto |
| Silero repunctuation | **não** (EN/DE/RU/ES) | — | — | https://habr.com/en/articles/581960/ |

Caveat estrutural: TODOS treinados em texto escrito/formal (Europarl, wiki) → devolvem pontuação **gramatical**, não prosódica. Pesquisa pt-BR (T5/BERT, F1 até 0.883 em TEDTalk/NILC): https://www.sciencedirect.com/science/article/abs/pii/S095741742401964X · https://link.springer.com/chapter/10.1007/978-3-031-21689-3_43

## 3. Pontuação prosódica / pausa em TTS (pesquisa)

- **Duration-aware pause insertion** (ICASSP'23): distingue pausas respiratórias (sem pontuação) de pausas de pontuação, categorizadas por DURAÇÃO; BERT + speaker embedding melhora precisão/recall de pausa e ritmo do sintetizado. https://arxiv.org/pdf/2302.13652
- **PauseSpeech**: modelagem de prosódia baseada em frases separadas por pausas. https://arxiv.org/pdf/2306.07489
- **Phrase break prediction speaker-conditioned** (2025): BERT fonemizado, MOS 4.39, preferência de ouvintes 58,5% vs baseline. https://arxiv.org/pdf/2509.00675
- **Vietnamita — pontuação inserida por detecção de pausa no áudio** (o mais próximo do que vocês querem): re-pontuar o texto de treino onde o áudio pausa → MOS ~4.1 no sistema E2E. https://arxiv.org/pdf/2004.09607 · https://aclanthology.org/2020.vlsp-1.4.pdf
- **Balalaika (Interspeech 2026, russo)**: pipeline data-céntrico (VAD semântico, ensemble ASR+ROVER, restauração de pontuação + marca de STRESS lexical); ablação mostra pontuação+stress **complementares**, ganhos consistentes de MOS/IntMOS e CER em budget igual. Melhor evidência recente de que anotação prosódica no TEXTO paga no TTS. https://arxiv.org/pdf/2507.13563
- **Székely et al., "How to train your fillers"** (SSW'19): anotar só a LOCALIZAÇÃO do filler e deixar o modelo escolher o tipo foi **preferido** vs especificar o tipo ground-truth. https://www.speech.kth.se/tts-demos/ssw19/szekely2019how.pdf
- **PSST — Prosodic Speech Segmentation with Transformers** (CoNLL'23): Whisper fine-tunado pra emitir fronteiras de **unidade entoacional** junto com a transcrição — exatamente a linha Aluísio/IU, já provada em inglês. https://aclanthology.org/2023.conll-1.31.pdf
- **Detecção de fronteira prosódica com wav2vec 2.0** (do áudio, não do texto): https://arxiv.org/pdf/2209.15032
- SSML/break control: https://arxiv.org/pdf/2508.17494 · anotação automática de prosódia com modelo texto-fala (fronteiras prosódicas melhoram naturalidade): https://arxiv.org/pdf/2206.07956

## 4. Word-timestamps pra detectar fronteiras (pausas)

- **WhisperX**: forced alignment com wav2vec2 → ~±50ms por palavra (vs ~centenas de ms do Whisper puro). Pra pt, requer wav2vec2 de alinhamento pt (VoxPopuli). https://arxiv.org/pdf/2303.00747 · https://github.com/m-bain/whisperX — mas há relatos de imprecisão vs MFA: https://github.com/m-bain/whisperX/issues/1247
- **CrisperWhisper**: SOTA em segmentação de palavra e timing de fillers (DTW cross-attention); pausas ficam FORA das palavras (Whisper vanilla "engole" pausa dentro do timestamp da palavra). https://arxiv.org/abs/2408.16589
- **stable-ts**: heurísticas + `nonspeech_sections`/gap adjustment; útil e barato, menos preciso que FA. https://github.com/jianfch/stable-ts · alternativa: https://github.com/linto-ai/whisper-timestamped
- Comparação FA tradicional (MFA) vs métodos ASR modernos: https://arxiv.org/pdf/2406.19363
- Regra prática da literatura: pausa = gap entre palavras **do alinhador forçado**, não do timestamp bruto do Whisper; avaliações usam collar de 200ms.

## 5. Evidência quantitativa (transcrição prosódica/verbatim vs limpa)

- **DisfluencySpeech**: treinar com transcrição LIMPA sobre áudio espontâneo é catastrófico — verbatim: MCD 3.68/CER 15%; sem eventos: MCD 5.26/CER 60% (não converge); sem false starts: MCD 4.87/CER 56%. A evidência mais direta de que o texto tem que cobrir o que soa no áudio. https://arxiv.org/html/2406.08820
- **Balalaika**: ganhos consistentes de MOS/IntMOS com pontuação restaurada + stress, ablações confirmam complementaridade. https://arxiv.org/pdf/2507.13563
- **Phrase-break BERT**: MOS 4.39, 58,5% preferência. https://arxiv.org/pdf/2509.00675
- **Vietnamita**: pontuação dirigida por pausa do áudio → MOS ~4.1. https://arxiv.org/pdf/2004.09607
- **Székely fillers**: preferência subjetiva por anotação location-only. https://www.speech.kth.se/tts-demos/ssw19/szekely2019how.pdf
- Lacuna honesta: NÃO existe estudo grande "pontuação prosódica vs gramatical" head-to-head em LLM-TTS moderno; a evidência é convergente mas indireta (línguas/arquiteturas menores). O sinal mais forte é o negativo: texto que não cobre o áudio destrói o treino.

---

## O QUE ADOTAR (custo/benefício, pro pipeline faster-whisper → TTS pt-BR)

1. **Filtro de desalinhamento texto-áudio (receita Emilia)** — custo mínimo, evita o pior erro: descartar segmentos com duração-por-caractere outlier + DNSMOS < 3 + baixa confiança. Não conserta transcrição ruim; joga fora. (arxiv 2407.05361)
2. **Verbatim-first: preservar fillers/repetições no texto** ("é…", "né", "hum", "tipo", false starts) — Whisper large-v3 os apaga sistematicamente; evidência DisfluencySpeech mostra que texto "limpo demais" quebra o treino. Caminho barato: 2ª passada com CrisperWhisper (NC, ok pesquisa) ou fine-tune leve estilo WhisperD; mínimo absoluto: nunca "limpar" o que o Whisper já pegou. (arxiv 2406.08820, 2505.21551, 2408.16589)
3. **Pontuação por pausa do áudio, não por gramática**: extrair gaps entre palavras via forced alignment (wav2vec2-pt/MFA, não timestamp bruto do Whisper) e re-pontuar: gap ~150–400ms → vírgula; >400–700ms → "…" ou ponto; manter a pontuação do Whisper onde concorda. É exatamente o esquema vietnamita + duration-aware pause insertion, e é quase grátis com o pipeline que vocês já têm. (arxiv 2004.09607, 2302.13652, 2303.00747)
4. **Reparo de P&C com LLM + guardrail de CER (receita Granary)**: LLM corrige pontuação/caixa, reverte se desviar >5% CER do original — pega o melhor do restaurador sem alucinar texto. Em pt, LLM > kredor/dominguesm (que são gramaticais, treinados em Europarl/wiki; usar só como fallback offline). (arxiv 2505.13404)
5. **Tags de evento padronizadas inline** (`[risada]`, `[respira]`, `[riso-falando]`) no formato CosyVoice/Dia; detectar com classificador + validação rápida no rate_app (pipeline NonverbalTTS). Só vale se houver eventos frequentes no dado de vocês. (arxiv 2507.13155, 2412.10117)
6. **Fillers: anotar localização, não micro-gerenciar o tipo** — Székely mostra que deixar o modelo escolher o filler soa melhor; ou seja, basta o filler estar no texto, sem taxonomia fina. (szekely2019how)
7. **MOS-filtering estratificado antes do treino** (Balalaika): filtrar por MOS objetivo (DNSMOS/UTMOS) mais estrito melhora síntese com o mesmo budget — barato, já quase implementado no fluxo de vocês. (arxiv 2507.13563)
8. **(Ceiling alto, custo alto) Whisper fine-tunado pra fronteiras de IU estilo PSST** — emitir a fronteira entoacional como token junto da transcrição, unificando ASR+segmentação prosódica; é a versão "de ponta" da linha Aluísio e o candidato natural de colaboração USP. (aclanthology 2023.conll-1.31, arxiv 2209.15032)

Sources: [Emilia](https://arxiv.org/html/2407.05361v3) · [Emilia-Large](https://arxiv.org/pdf/2501.15907) · [CasualConversations transcriptions](https://arxiv.org/pdf/2111.09983) · [Granary](https://arxiv.org/pdf/2505.13404) · [WhisperD](https://arxiv.org/abs/2505.21551) · [CrisperWhisper](https://arxiv.org/abs/2408.16589) · [DisfluencySpeech](https://arxiv.org/html/2406.08820) · [NonverbalTTS](https://arxiv.org/abs/2507.13155) · [CosyVoice2](https://arxiv.org/pdf/2412.10117) · [Dia](https://github.com/nari-labs/dia) · [Expresso](https://speechbot.github.io/expresso/) · [EARS](https://arxiv.org/html/2406.06185v2) · [punctuate-all](https://huggingface.co/kredor/punctuate-all) · [fullstop](https://huggingface.co/oliverguhr/fullstop-punctuation-multilang-large) · [bert-restore-punctuation-ptbr](https://huggingface.co/dominguesm/bert-restore-punctuation-ptbr) · [Silero repunct](https://habr.com/en/articles/581960/) · [pt punct restoration survey](https://www.sciencedirect.com/science/article/abs/pii/S095741742401964X) · [pause insertion ICASSP23](https://arxiv.org/pdf/2302.13652) · [PauseSpeech](https://arxiv.org/pdf/2306.07489) · [phrase break 2025](https://arxiv.org/pdf/2509.00675) · [Vietnamese data processing](https://arxiv.org/pdf/2004.09607) · [Balalaika](https://arxiv.org/pdf/2507.13563) · [Székely fillers](https://www.speech.kth.se/tts-demos/ssw19/szekely2019how.pdf) · [PSST](https://aclanthology.org/2023.conll-1.31.pdf) · [wav2vec2 boundaries](https://arxiv.org/pdf/2209.15032) · [WhisperX](https://arxiv.org/pdf/2303.00747) · [whisperX vs MFA issue](https://github.com/m-bain/whisperX/issues/1247) · [stable-ts](https://github.com/jianfch/stable-ts) · [FA comparison](https://arxiv.org/pdf/2406.19363) · [SSML French](https://arxiv.org/pdf/2508.17494) · [auto prosody annotation](https://arxiv.org/pdf/2206.07956)