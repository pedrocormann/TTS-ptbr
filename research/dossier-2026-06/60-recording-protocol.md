# FRENTE 8 — Protocolo de gravação e design de dataset próprio (melhores práticas, jun/2026)

> Pesquisa web realizada em 2026-06-10. Todas as afirmações decisivas têm URL primária.
> Contexto: dataset inicial = voz do Pedro, gravação dirigida de alta qualidade, sotaque carioca
> (+ ~5 sub-variações), alvo = fala conversacional expressiva nível "Maya da Sesame".
> Restrição dura de licença no produto: Apache-2.0 / MIT / CC-BY / CC0. Veto a NC / SA / research-only.

---

## TL;DR — decisões recomendadas

1. **Copiar o protocolo do EARS para emoções** (barato e replicável: 3 frases fixas + descrição
   de imagem por emoção) e **o do Expresso para conversacional** (diálogo improvisado sobre cenário
   imaginário, 2 canais separados) — mas **NÃO usar os áudios deles**: ambos são **CC BY-NC** (veto).
2. **Gravar a 48 kHz / 24-bit, mono, cardioide, ~1 palmo do mic, ganho fixo, picos entre −12 e −6 dB**
   (protocolo NVIDIA Riva + specs do Expresso/EARS). Normalizar depois para **−23 LUFS (EBU R128)**
   com `ffmpeg loudnorm`; nunca peak-normalize.
3. **Metas de volume por categoria** (números reportados na literatura):
   - ≥ **30 min por emoção/estilo** = qualidade "Good" em MUSHRA (15 min = só "Fair");
   - **~1 h de voz neutra limpa** é suficiente para adaptação de voz (LoRA/partial finetune);
   - **Orpheus: 50 exemplos já mostram resultado; 300 exemplos/falante recomendado**;
   - **moshi-finetune: exemplo oficial usa só ~20 h de diálogo (DailyTalk)** → meta full-duplex: 10–20 h.
4. **Balanceamento fonético pt-BR**: existem listas prontas — **Alcaim et al. 1992 (20 listas × 10
   frases, calibradas no português DO RIO)**, as ~1.000 frases do CETUC (CETEN-Folha) e as frases do
   TTS-Portuguese Corpus (**CC BY 4.0** — única base pt-BR license-clean). Para cobertura máxima,
   gerar lista própria por algoritmo guloso de trifones (paper de 2024 mostra +55,8% de trifones
   distintos vs. CETUC/TTS-Portuguese). Adicionar frases desenhadas para os traços cariocas
   (/S/ pós-vocálico, africadas, /R/ de coda).
5. **Ferramenta de sessão**: `piper-recording-studio` (MIT, web local, exporta LJSpeech, multi-idioma
   via arquivos de prompt .txt) é o melhor ponto de partida; `mimic-recording-studio` está morto
   (Mycroft encerrou). Complementar com QC automático próprio: SNR ≥ 32 dB, sem clipping,
   DNSMOS ≥ ~3.2 / NISQA ≥ ~4.0, verificação de transcrição por ASR (como a Kyutai fez no
   Voice Donation).
6. **Bônus license-clean descoberto**: a Kyutai encerrou (fev/2026) o **Unmute Voice Donation
   Project** — **228 vozes verificadas, publicadas como CC0** em `kyutai/tts-voices`. Vozes extras
   gratuitas para conditioning/diversidade, zero risco de licença.

---

## (a) Como foram desenhados os datasets expressivos de referência

### Expresso (Meta AI / usado pelo ecossistema Kyutai)

- **40 h total: 11 h lidas + ~30 h de diálogo improvisado**; **4 falantes** (2M/2F), atores
  profissionais; estúdio profissional, **48 kHz / 24-bit**; leitura em mono, diálogo em
  **estéreo com um canal por ator, preservando o fluxo natural de turn-taking** (exatamente o
  formato que o Moshi consome).
- **Leitura: 8 estilos** — default, confused, enunciated, happy, laughing, sad, whisper (+ narração
  longa e canto). **Diálogo improvisado: 26 estilos**, incluindo angry, awe, bored, child-directed,
  fearful, sarcastic, desire, non-verbal (risos, suspiros etc.).
- **Protocolo do diálogo**: os atores recebiam um **cenário imaginário** ("dois motoristas
  discutindo depois de uma batida") e improvisavam — sem script. Transcrição fornecida só para a
  parte lida.
- **Licença: CC BY-NC 4.0 → VETADO como dado de treino do produto.** Vale apenas como referência
  de protocolo e como benchmark acadêmico.
- Fontes: https://speechbot.github.io/expresso/ ; paper: https://ai.meta.com/research/publications/expresso-a-benchmark-and-analysis-of-discrete-expressive-speech-resynthesis/ ;
  versão HF: https://huggingface.co/datasets/ylacombe/expresso

**Lição de design**: separar (i) leitura por estilo (controle e cobertura fonética) de
(ii) diálogo improvisado por cenário (naturalidade, turn-taking, overlap). O estéreo 1-canal-por-
falante é requisito para treino full-duplex tipo Moshi.

### EARS (Meta + Univ. Hamburgo, Interspeech 2024)

- **100 h, 107 falantes, ~1 h por falante**, câmara anecoica, **48 kHz / 32-bit**, dois mics GRAS
  simultâneos a **~1 m** do falante, equalização entre mics.
- Por falante: **7 estilos de leitura** (regular, loud, whisper, fast, slow, low pitch, high pitch),
  **22 emoções** e **18 min de fala livre** (entrevista: operador faz perguntas abertas — férias,
  hobbies, profissão).
- **Protocolo de emoção (o achado mais reaproveitável da frente)**: para cada uma das 22 emoções o
  falante (1) **lê 3 frases fixas** na emoção-alvo e (2) **descreve uma imagem** com o tom emocional
  pedido — ou seja, *acted* sobre texto neutro + *semi-espontâneo* sobre estímulo visual. Cobre
  do sussurro ao grito (full dynamic range).
- **Licença: CC BY-NC 4.0 → VETADO** como dado de treino. Referência de protocolo apenas.
- Fontes: https://arxiv.org/abs/2406.06185 ; https://github.com/facebookresearch/ears_dataset ;
  https://sp-uhh.github.io/ears_dataset/

### Hi-Fi TTS e HiFiTTS-2 (NVIDIA)

- Hi-Fi TTS: **292 h, 10 falantes, ≥17 h/falante, 44,1 kHz**, de audiolivros LibriVox (domínio
  público). O design não é de gravação, e sim de **filtragem por qualidade**: só entra áudio com
  **largura de banda ≥ 13 kHz e SNR ≥ 32 dB** — dois números que servem direto de gate de QC para
  as nossas gravações. https://arxiv.org/abs/2104.01497 ; https://www.openslr.org/109/
- HiFiTTS-2 (jun/2025): escala a mesma ideia para ~milhares de horas de LibriVox com estimativa
  de largura de banda e filtragem automática. https://arxiv.org/abs/2506.04152

### LJSpeech (baseline histórico)

- **13.100 clipes, 23h55min, 1 falante, 22,05 kHz / 16-bit, domínio público**; passagens de 7
  livros de não-ficção (1884–1964) gravadas pela falante do LibriVox em 2016-17.
  É o "formato padrão" (metadata.csv + wavs/) que quase toda ferramenta de gravação exporta.
  https://keithito.com/LJ-Speech-Dataset/
- Lição: ~24 h de um único falante consistente foi suficiente para definir uma era de TTS lido;
  para conversacional expressivo o gargalo não é volume, é **cobertura de estilos e diálogo real**.

### DailyTalk (conversacional lido, ICASSP 2023)

- **2.541 diálogos** amostrados/adaptados do DailyDialog e **gravados em estúdio por 2 falantes
  simultâneos** (1M/1F), com inserção deliberada de marcadores de hesitação ("filling-gap words").
  ~20 h. É o dataset do exemplo oficial do moshi-finetune (versão "contiguous").
  Licença **CC BY-SA 4.0** (SA = fora da allow-list do projeto; usar só como referência/benchmark).
  https://arxiv.org/abs/2207.01063 ; https://github.com/keonlee9420/DailyTalk
- Lição: **diálogo lido a 2 com hesitações escritas no script** é o meio-termo entre leitura e
  improviso — barato de dirigir e já serve para treino conversacional.

### O que Orpheus / Dia / CSM dizem sobre dados (modelos da nossa órbita)

- **Orpheus (canopyai)**: pré-treino em **100k+ h de fala em inglês**; tags emotivas no transcript
  (`<laugh> <chuckle> <sigh> <cough> <sniffle> <groan> <yawn> <gasp>`); para finetune de voz o
  README oficial reporta: "**resultados de alta qualidade a partir de ~50 exemplos, mas recomendamos
  300 exemplos/falante**". https://github.com/canopyai/Orpheus-TTS
- **Dataset Elise** (usado nos tutoriais Unsloth/Orpheus/CSM): **~3 h single-speaker** com **tags de
  emoção embutidas na transcrição** — prova de que 3 h bem anotadas bastam para dar expressividade
  controlável a um modelo LLM-TTS. https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning
- **CSM/Sesame**: ~**1 milhão de horas de áudio público predominantemente em inglês**, transcrito e
  segmentado (sem detalhes de protocolo de emoção — a expressividade é implícita, aprendida da
  distribuição). https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice
- **Dia (nari-labs)**: não divulga composição do treino; aprende não-verbais `(laughs)`, `(coughs)`
  por tags no texto. https://github.com/nari-labs/dia
- **Lição transversal**: nos modelos 2025-26 a emoção vem (i) implícita da escala, (ii) controlável
  por **tags no transcript** ou prompt de estilo. Logo, **o nosso transcript deve nascer com tags
  de evento não-verbal e de estilo desde o dia 1** — é barato anotar na hora da gravação e caro
  depois.

### Datasets de estilo/caption 2025 (estado da arte de anotação)

- **ParaSpeechCaps**: 282 h anotadas por humanos + 2.450 h auto-anotadas, **59 tags de estilo**
  (intrínsecas do falante + situacionais do enunciado). Modelo de anotação a copiar para o nosso
  metadado. https://arxiv.org/abs/2503.04713 ; https://paraspeechcaps.github.io/
- **EmoVoice-DB**: **40 h / 7 emoções balanceadas / 20k+ amostras**, cada uma com **descrição da
  emoção em linguagem natural** (não só rótulo categórico). https://arxiv.org/abs/2504.12867
- **CapSpeech** (jun/2025): benchmark de TTS com caption de estilo. https://arxiv.org/abs/2506.02863
- **Lição**: anotar cada take com (1) rótulo categórico, (2) intensidade 1–3, (3) uma frase livre
  descrevendo o estilo ("irritado mas contido, falando baixo") — isso habilita controle por prompt
  de estilo depois.

### Kyutai Voice Donation (achado novo, encerrou fev/2026)

- A Kyutai rodou jun/2025→fev/2026 um projeto de doação de voz para o ecossistema Kyutai TTS:
  **374 vozes submetidas, 228 passaram verificação, publicadas como CC0** em
  `kyutai/tts-voices` (pasta `voice-donations/`). Pipeline de verificação: **ASR confere se o texto
  lido bate com a gravação** antes de aceitar — modelo de QC a copiar.
  https://unmute.sh/voice-donation ; https://huggingface.co/kyutai/tts-voices
- Implicação: temos um banco de vozes CC0 prontas para conditioning/diversidade de speaker no spine
  Moshi/Kyutai (checar quantas são pt — maioria provável en/fr).

---

## (b) Balanceamento fonético para pt-BR (e para o carioca)

### Listas prontas existentes

| Recurso | O que é | Licença/acesso | Uso recomendado |
|---|---|---|---|
| **Alcaim, Solewicz & Moraes (1992)** | Levantamento de frequência de fones do **português falado no Rio de Janeiro** + **20 listas de 10 frases foneticamente balanceadas** (balanceamento por χ² contra a distribuição carioca) | Paper aberto na Rev. SBrT: https://jcis.sbrt.org.br/jcis/article/view/166 | **Script-base ideal: é a única lista calibrada na distribuição DO RIO.** 200 frases = ~15-20 min de leitura; repetir nas várias emoções/estilos |
| **CETUC (PUC-Rio)** | 100 falantes × ~1.000 frases balanceadas extraídas do CETEN-Folha; 145 h, 16 kHz | Áudio cedido "exclusivamente para pesquisa", **sem licença explícita → VETO no produto**; acesso via https://github.com/falabrasil/speech-datasets | **Não usar o áudio.** As 1.000 frases (texto) servem de inspiração de cobertura; checar licença do texto CETEN-Folha antes de copiar frases literalmente |
| **TTS-Portuguese Corpus (Casanova et al.)** | 10,5 h, 1 falante, pt-BR; frases balanceadas (conjunto Seara/UFSC, calibrado em Florianópolis) + Wikipédia + frases de chatbot | **CC BY 4.0** — única base de fala pt-BR claramente license-clean. https://github.com/Edresson/TTS-Portuguese-Corpus ; paper: https://arxiv.org/abs/2005.05144 | **Usável no produto** (dado de treino suplementar) e fonte pronta de frases para o nosso script. Atenção: balanceamento é catarinense, não carioca; áudio tem qualidade de estúdio caseiro |
| **Corpus foneticamente rico 2024 (Mendonça & Aluísio)** | Algoritmo de seleção de sentenças por **distribuição de trifones** + classificação acústico-articulatória; resultado com **+55,8% de trifones distintos** vs. bases não-ricas (CETUC +12,6%, TTS-Portuguese +12,3%) | https://arxiv.org/abs/2402.05794 | **Metodologia a replicar**: rodar seleção gulosa de trifones sobre um pool de texto license-clean (Wikipédia pt CC BY-SA → cuidado; preferir textos próprios/CC0) |
| **NURC-RJ (UFRJ)** | Fala culta carioca espontânea (entrevistas/diálogos, décadas de material; uso acadêmico) | https://nurcrj.letras.ufrj.br/ — acadêmico | **Não treinar com o áudio**; usar como **referência auditiva** dos sub-sotaques e fonte de padrões lexicais/prosódicos cariocas para escrever scripts |

### Cobertura específica do carioca — o que as listas genéricas não cobrem

Traços que o script próprio precisa estressar (as listas balanceadas "neutras" sub-amostram esses
contextos ou foram calibradas em outros dialetos):

1. **/S/ pós-vocálico (coda) → [ʃ]/[ʒ]** — a marca registrada carioca ("chiado"). Cobrir
   sistematicamente: coda antes de consoante surda ("**pasta, biscoito, festa**" → [ʃ]), antes de
   sonora ("**mesmo, rasgo, Israel**" → [ʒ]), em final absoluto ("**dez, vamos**"), e o **sândi**
   entre palavras ("a**s a**migas" — /s/ + vogal → [z]; "a**s ch**aves" — encontro [ʃʃ]).
   Referências: https://pt.wikipedia.org/wiki/Dialeto_carioca ;
   estudo sociolinguístico do /S/ em Copacabana: https://pantheon.ufrj.br/handle/11422/22317 ;
   análise clássica: https://periodicos.sbu.unicamp.br/ojs/index.php/cel/article/view/8646158
2. **Africadas [tʃ]/[dʒ]** diante de [i] (inclusive epentético): "**tia, dia, parte, pode**
   (→ [ˈpɔdʒi]), **advogado** ([adʒi-])".
3. **/R/ de coda como fricativa velar/glotal [χ]/[h]** e variação no infinitivo ("falá(r)") —
   cobrir coda interna ("**porta, carta**") e final com e sem apagamento.
4. **Vogais pós-tônicas reduzidas** e ditongação diante de /S/ final ("ma**is**" vs "ma**s**" —
   "mash"/"maish"), "**arroz**" → [aˈχoʃ]~[aˈχojʃ].
5. **Léxico/prosódia por sub-variação** (zona sul, cria, surfista, interior): isso é mais
   **prosódia, ritmo, gíria e grau do chiado** do que fonemas novos → tratar como **estilos**
   (seção e) e não como dialetos separados; escrever scripts com o léxico típico de cada persona.

### Receita prática de lista (pipeline próprio)

1. Pool de texto: frases do TTS-Portuguese (CC-BY) + frases autorais/CC0 escritas com léxico
   carioca + transcrições próprias.
2. G2P pt-BR (ex.: módulos do FalaBrasil — https://github.com/falabrasil — ou phonemizer/espeak-ng
   com pt-br) → trifones por frase. **Adaptar o G2P para refletir o carioca** (regra /S/ coda → ʃ),
   senão a "cobertura" calculada é a do dialeto errado.
3. Seleção gulosa maximizando trifones distintos ponderados por frequência (método do
   arXiv 2402.05794), com cotas mínimas para os contextos cariocas da lista acima.
4. Alvo: **~1.000–1.500 frases núcleo** (≈2–3 h lidas) cobrindo o máximo de trifones; as 200 de
   Alcaim como subconjunto de calibração/eval (re-gravadas a cada marco para regressão de voz).

---

## (c) Protocolo prático de gravação caseira de alta qualidade

Base: tutorial oficial NVIDIA Riva "Guidelines to Record a TTS Dataset at Home"
(https://docs.nvidia.com/deeplearning/riva/user-guide/docs/tutorials/tts-dataset-recording-at-home.html),
specs do Expresso/EARS e prática de produção (11c.media, Sewade Ogun:
https://ogunlao.github.io/blog/2021/01/26/how-to-create-speech-dataset.html).

### Equipamento

- **Mic**: condensador cardioide. USB resolve (AT2020USB+, Blue Yeti em modo cardioide); upgrade
  natural = condensador XLR + interface (ex. AT2020/AT2035 + Scarlett Solo). **Pop filter
  obrigatório**; pedestal/braço articulado (nunca segurar na mão).
- **Software**: Audacity (grátis, medidor de dB numérico) ou Reaper. Evitar apps sem medidor.
- **Fones fechados** para monitorar sem vazamento.

### Sala

- Cômodo mais silencioso; janelas/portas fechadas; **desligar ar-condicionado, ventilador,
  geladeira próxima e silenciar o fan do computador** (mic USB + notebook longe, ou gravar com
  o computador fora da sala).
- Tratamento caseiro eficaz: gravar dentro de **closet com roupas penduradas** ou montar "fortaleza"
  de cobertores/edredons atrás e ao redor do mic. O objetivo é matar reflexões precoces — o modelo
  aprende a sala junto com a voz.
- **Consistência > perfeição**: mesma sala, mesma posição do mic, mesma cadeira em TODAS as sessões.
  Tirar foto do setup e marcar posições com fita.

### Configuração e níveis

| Parâmetro | Valor | Fonte |
|---|---|---|
| Sample rate | **48 kHz** (Riva sugere até 96 kHz; Expresso/EARS usam 48 kHz — suficiente e 2× menor em disco; Mimi opera a 24 kHz de qualquer forma) | Riva / Expresso / EARS |
| Bit depth | **24-bit** (32-float se a interface suportar) | Riva / EARS |
| Padrão polar | **Cardioide**, falar no lado do logo | Riva |
| Distância | **1 punho (~10–15 cm)** do mic, levemente off-axis para plosivas | Riva |
| Ganho | Fixar (~posição 9h no Yeti) e **NUNCA mexer depois de calibrado** | Riva |
| Picos | **entre −24 e −6 dB** (24-bit); alvo prático −12 a −6 dB; jamais encostar em 0 | Riva |
| Noise floor | medir 10 s de "silêncio da sala" no início de toda sessão; alvo < −60 dBFS | prática padrão |
| Formato | WAV PCM mono (estéreo 1-canal-por-falante nos diálogos a 2) | Expresso |

### Sessões e fadiga vocal

- **Blocos de 45–60 min de gravação com 10 min de descanso vocal por hora**; máx. **2–4 h/dia**.
  Regra de produção de audiolivro: **~4 h de tempo real por 1 h de áudio útil** (gravar + editar).
  Fontes: práticas ACTRA (https://actratoronto.com/vocal-health/),
  https://karencommins.com/2009/11/time_required_to_narrate_and_p.html
- Aquecimento de 5–10 min (humming, lip trills), água em temperatura ambiente sempre à mão; evitar
  laticínios/café logo antes; **não gravar gritado/sussurrado por períodos longos** — estilos
  extremos em blocos curtos (≤15 min) intercalados com neutro.
- **Slate em áudio no início de cada take-batch**: ID da sessão, estilo, data — facilita QC depois.
- Gravar **sempre no mesmo horário do dia** se possível (voz muda manhã→noite).

### Pós-processamento e QC automático (pipeline)

1. **Sem denoise agressivo por padrão** — denoisers (RNNoise/DeepFilterNet) introduzem artefatos
   que o TTS aprende; se a captação foi boa, pular. (Evidência: pipelines in-the-wild testam
   condição "no-denoising" e ela compete bem — https://arxiv.org/abs/2510.03111)
2. **Loudness**: normalizar por programa para **−23 LUFS integrado (EBU R128 / ITU-R BS.1770),
   true peak ≤ −2 dBTP**, via `ffmpeg loudnorm` dual-pass. **RMS/LUFS, nunca peak-normalize**
   (peak norm gera amplitudes inconsistentes p/ treino). Ferramenta dedicada:
   https://github.com/ScottishFold007/TTSAudioNormalizer
3. **Gates automáticos por clipe** (rejeita ou re-grava):
   - **SNR ≥ 32 dB** e largura de banda ≥ 13 kHz (critérios Hi-Fi TTS, https://arxiv.org/abs/2104.01497);
   - **zero clipping** (amostras ≥ 0,99 FS);
   - **DNSMOS ≥ ~3.2** e/ou **NISQA ≥ ~4.0** (thresholds reportados: NISQA 4.0–4.6 = zona ótima
     de curadoria; DNSMOS é mais sensível a pequenos ajustes de threshold —
     https://arxiv.org/abs/2510.03111);
   - silêncio inicial/final aparado para ~50–100 ms; duração 1–15 s (lido) / até 30 s (diálogo).
4. **Verificação de transcrição**: rodar faster-whisper pt no clipe e comparar com o script
   (WER por clipe; gate ~< 10% p/ leitura — é o mesmo esquema de verificação do Kyutai Voice
   Donation: https://unmute.sh/voice-donation). Forced alignment com **Montreal Forced Aligner**
   ou WhisperX para timestamps e para detectar palavras engolidas.
5. **Relatório por sessão**: % aprovado, SNR médio, LUFS, histograma de duração — perseguir
   tendência, não clipe individual. (O repo já tem `tools/` — encaixar aqui.)
6. Referência de pipeline industrial in-the-wild (para a fase de dados de terceiros):
   **Emilia-Pipe** (open-source: separação→VAD→diarização→ASR→filtro DNSMOS) —
   https://github.com/open-mmlab/Amphion/tree/main/preprocessors/Emilia

---

## (d) Quanto gravar por estilo/emoção/sub-sotaque (números reportados)

| Evidência | Número | Fonte |
|---|---|---|
| Rasa (TTS expressivo low-resource, Indian langs): emoção avaliada "Fair" com ≥15 min, **"Good" com ≥30 min** de fala expressiva por emoção (sobre base neutra de 1–10 h) | **30 min/emoção** | https://arxiv.org/abs/2407.14056 |
| Partial finetune de LLM-TTS (emoção+speaker): ~15% dos parâmetros, **~1 h de áudio single-speaker** atinge similaridade ≈ full finetune | **1 h/voz** | https://arxiv.org/abs/2501.14273 |
| Orpheus README (finetune de voz): resultados visíveis com **~50 exemplos**; **300 exemplos/falante recomendado** (~20–30 min) | **50–300 frases/voz** | https://github.com/canopyai/Orpheus-TTS |
| Dataset Elise (tutoriais Unsloth p/ Orpheus/CSM/Sesame): **~3 h** com tags de emoção bastam p/ expressividade controlável | **3 h** | https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning |
| moshi-finetune (oficial Kyutai): exemplo com **apenas ~20 h** (DailyTalkContiguous), LoRA | **20 h diálogo** | https://github.com/kyutai-labs/moshi-finetune |
| J-Moshi (adaptação de língua completa do Moshi): 69k h (J-CHAT) — teto, não piso; é o caminho CPT, não LoRA | 69k h | https://arxiv.org/abs/2506.02979 |
| LJSpeech: ~24 h, 1 falante = TTS lido de alta qualidade (era pré-LLM) | 24 h | https://keithito.com/LJ-Speech-Dataset/ |
| Expresso: 4 falantes, 11 h lidas (8 estilos) + 30 h diálogo (26 estilos) = SOTA expressivo acadêmico | 40 h/4 vozes | https://speechbot.github.io/expresso/ |

### Plano de gravação recomendado (voz do Pedro, fases incrementais)

| Fase | Conteúdo | Volume alvo | Para quê |
|---|---|---|---|
| **0 — Piloto (1 fim de semana)** | 200 frases Alcaim + 100 frases conversacionais, estilo default | **~1 h útil** | Validar pipeline (gravação→QC→finetune CSM/Orpheus/Kokoro); baseline de regressão |
| **1 — Núcleo lido** | 1.000–1.500 frases balanceadas (trifone-greedy) + 1–2 h de narração longa | **4–6 h** | Adaptação de voz sólida; base neutra sobre a qual emoções se ancoram |
| **2 — Estilos/emoções** | 8–10 estilos à la Expresso (feliz, irritado, triste, sussurro, riso, confuso, enfático, cansado, "contando segredo", narração) × **30–45 min cada** (protocolo EARS: frases fixas + descrição de imagem + monólogo livre no estilo) | **5–7 h** | Controle de emoção via tag/estilo (meta ≥30 min = "Good") |
| **3 — Sub-sotaques como estilos** | 5 personas cariocas (médio, zona sul, cria, surfista, interior) × **30–60 min** (script com léxico típico + improviso) | **3–5 h** | Sub-variação controlável; validar com ouvintes cariocas se não caricaturou |
| **4 — Conversacional/full-duplex** | Diálogos: re-speaking de podcast, conversas reais consentidas, diálogos improvisados por cenário (estéreo, 1 canal/falante), rico em backchannels/overlap | **10–20 h** | LoRA no Moshi (paridade com o exemplo oficial de 20 h) |
| **Total** | | **~25–40 h úteis** (~100–160 h de trabalho na regra 4:1) | |

Notas:
- Os números acima são de papers de **TTS lido/estilo**; para o spine full-duplex a fase 4 é a que
  manda, e 10–20 h é a única âncora pública (moshi-finetune). Planejar eval humana no marco de 10 h
  antes de gravar até 20 h.
- **Sub-sotaque atuado por um único falante é risco de caricatura** — não há literatura de suporte
  para "sub-accent acting" em TTS; mitigar com (i) eval cega com ouvintes nativos de cada persona,
  (ii) plano B: dado de terceiros license-clean (Common Voice pt / YouTube CC-BY) filtrado por
  região, ou doadores de voz convidados (protocolo de termo de cessão tipo Kyutai/CC0).

---

## (e) Estrutura de prompts de gravação (emoção dirigida e conversacional)

### Acted vs. elicited vs. natural — o que a literatura diz

- **Acted** (ator simula sobre texto pré-definido): áudio limpo e controle total das categorias,
  mas tende a **estereotipado/exagerado**; é o método do EARS, Expresso (parte lida) e da maioria
  dos corpora SER clássicos.
- **Elicited** (emoção induzida por estímulo — vídeo, música, recall autobiográfico, imagem,
  situação): mais genuíno, menos controlável; técnicas eficazes: estímulo visual, música, **recall
  autobiográfico** e imaginação dirigida (mood induction procedures).
- **Natural/espontâneo**: o mais real e o mais fraco em intensidade média; difícil de rotular.
- Revisão comparativa (2025): https://doi.org/10.3390/data10100164 ;
  DEMoS (elicitação combinada): https://www.researchgate.net/publication/331286044 ;
  EMOVOME (espontâneo real): https://arxiv.org/abs/2403.02167
- **Consenso prático para TTS** (não SER): *acted-com-direção* é aceitável e é o que os datasets
  TTS expressivos de referência usam — TTS precisa de **expressividade percebida**, não de verdade
  emocional. O risco a gerenciar é a caricatura, via direção ("menos 30%") e takes em 2–3
  intensidades.

### Template por emoção/estilo (síntese EARS + Expresso + EmoVoice-DB)

Para cada estilo/emoção E, gravar 4 blocos:

1. **Frases-âncora (acted, texto fixo)**: as MESMAS 10–15 frases semanticamente neutras gravadas em
   TODOS os estilos ("A reunião foi remarcada para quinta-feira.") → dá pares minimal-pair de
   estilo, ouro para treino e eval de controle.
2. **Frases congruentes (acted, texto específico)**: 20–30 frases cujo conteúdo combina com E
   (raiva: reclamação de trânsito carioca) → naturalidade máxima.
3. **Estímulo (elicited)**: descrever uma imagem/lembrança no tom E (protocolo EARS: "descreva
   esta foto como se estivesse com muita raiva"); recall autobiográfico quando seguro.
4. **Monólogo improvisado** de 2–3 min no estilo E (protocolo Expresso/EARS freeform).

Anotação por take (modelo ParaSpeechCaps/EmoVoice-DB): `emoção categórica` + `intensidade 1–3` +
`caption livre em uma frase` + tags inline de evento (`<laugh>`, `<sigh>`, `<breath>`...) no
transcript.

### Conversacional espontâneo — 4 formatos, todos com lugar

| Formato | Protocolo | Prós/contras | Referência |
|---|---|---|---|
| **Diálogo lido a 2** | Scripts de diálogo (escrever do zero em pt-carioca; DailyDialog traduzido tem cheiro de tradução) **com hesitações escritas** ("é... tipo assim..."), 2 mics, 1 canal/falante | Controle total, transcrição grátis; menos natural | DailyTalk https://arxiv.org/abs/2207.01063 |
| **Diálogo improvisado por cenário** | Cartão com situação ("dois motoristas discutindo batida"; "amigo contando fofoca"), improvisar 3–5 min, estéreo | Naturalidade alta, turn-taking/overlap reais; precisa de 2ª pessoa e ASR depois | Expresso https://speechbot.github.io/expresso/ |
| **Entrevista freeform** | Operador (ou o próprio Claude por voz) faz perguntas abertas; 18 min/sessão | Monólogo espontâneo com backchannel do entrevistador | EARS https://arxiv.org/abs/2406.06185 |
| **Re-speaking de podcast** | Ouvir trecho de podcast próprio/CC, re-falar com as próprias palavras e prosódia natural | Espontaneidade dirigida sem precisar de 2ª pessoa; conteúdo license-clean se a fonte for própria/CC-BY | prática da indústria (sem paper canônico; análogo ao "respeaking" de legendagem) |

Para o **spine Moshi**: priorizar os formatos com 2 canais e overlap real (improvisado + entrevista),
porque o Inner Monologue/full-duplex treina com os dois streams separados — é exatamente o formato
estéreo do Expresso e do DailyTalkContiguous do exemplo oficial kyutai.
**Backchannels têm que existir no dataset** ("uhum", "é", "caraca", "sério?") — gravar sessões onde
o Pedro é o ouvinte ativo, não só o falante.

---

## (f) Ferramentas open-source de gestão de sessão de gravação (status jun/2026)

| Ferramenta | Status | Licença | Notas |
|---|---|---|---|
| **piper-recording-studio** (rhasspy) | Vivo (Nabu Casa patrocina); 215+ stars | **MIT** | Web local (localhost:8000), prompts por idioma em `.txt` (`id\ttexto` — basta criar pasta `pt-BR`), multi-usuário com código de login, **exporta LJSpeech**, corte de silêncio via ffmpeg, Docker. **Recomendado como base.** https://github.com/rhasspy/piper-recording-studio |
| **mimic-recording-studio** (MycroftAI) | **Abandonado** (Mycroft encerrou operação em 2023) | Apache-2.0 | Docker, métricas de fonema por sessão; só como referência de UX. https://github.com/MycroftAI/mimic-recording-studio |
| **TextyMcSpeechy** (dataset recorder) | Vivo | GPL-3.0 (tool, não contamina o dado) | Grava datasets a partir de qualquer `metadata.csv`, preview do modelo durante o treino (Piper). https://github.com/domesticatedviking/TextyMcSpeechy |
| **Speech Data Builder** | Vivo (web app estático) | open-source | Browser, exporta LJSpeech/CSV/JSON. https://fs-17.github.io/SpeechDataBuilder/ |
| **Common Voice** (Mozilla) | Vivo | plataforma (dados CC0) | Só faz sentido para crowdsourcing público, não para sessão dirigida |
| **Kyutai Voice Donation** | Encerrado fev/2026 | vozes CC0 | Não é ferramenta instalável, mas o fluxo (gravar → ASR verifica texto → aceita) é o blueprint de QC. https://unmute.sh/voice-donation |

**Veredito**: não apareceu nada em 2025-26 melhor que `piper-recording-studio` para sessão dirigida
local. Plano: fork leve com (1) prompts pt-BR próprios organizados por estilo/sessão, (2) gate de QC
em tempo real no upload (SNR/clipping/duração — recusar take ruim na hora é 10× mais barato que
re-gravar depois), (3) campo de tags de emoção/evento, (4) export LJSpeech + manifest JSONL com os
metadados de estilo. Para os diálogos a 2 canais, gravar direto no Reaper/Audacity multitrack
(piper-rs é single-track) e segmentar com VAD/diarização (pipeline Emilia-Pipe como referência).

---

## Tabela de licenças (gate duro do projeto)

| Recurso | Licença | Pode treinar produto? |
|---|---|---|
| Expresso | CC BY-NC 4.0 | **NÃO** (referência de protocolo apenas) |
| EARS | CC BY-NC 4.0 | **NÃO** (idem) |
| LJSpeech | Domínio público | Sim (inglês) |
| Hi-Fi TTS / HiFiTTS-2 | LibriVox domínio público (verificar termos NVIDIA do pacote) | Provável sim (inglês) |
| DailyTalk | CC BY-SA 4.0 | **Não** pela allow-list (SA); ok como benchmark |
| TTS-Portuguese Corpus | **CC BY 4.0** | **SIM** — único corpus de fala pt-BR claramente clean |
| CETUC | research-only, sem licença explícita | **NÃO** (áudio); frases = verificar CETEN-Folha |
| CORAA / NURC | acadêmico | **NÃO**; referência auditiva |
| Kyutai tts-voices (voice-donations) | **CC0** | **SIM** (conditioning de voz) |
| EmoVoice-DB / ParaSpeechCaps | verificar nos cards HF antes de qualquer uso | a confirmar |
| Dado próprio (voz do Pedro) | nosso | **SIM — é por isso que esta frente existe** |

---

## Fontes principais

- Expresso: https://speechbot.github.io/expresso/ · https://ai.meta.com/research/publications/expresso-a-benchmark-and-analysis-of-discrete-expressive-speech-resynthesis/
- EARS: https://arxiv.org/abs/2406.06185 · https://github.com/facebookresearch/ears_dataset · https://sp-uhh.github.io/ears_dataset/
- Hi-Fi TTS: https://arxiv.org/abs/2104.01497 · https://www.openslr.org/109/ · HiFiTTS-2: https://arxiv.org/abs/2506.04152
- LJSpeech: https://keithito.com/LJ-Speech-Dataset/
- DailyTalk: https://arxiv.org/abs/2207.01063 · https://github.com/keonlee9420/DailyTalk
- Orpheus: https://github.com/canopyai/Orpheus-TTS · Unsloth TTS guide: https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning
- CSM/Sesame: https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice · finetune CSM: https://blog.speechmatics.com/sesame-finetune
- moshi-finetune: https://github.com/kyutai-labs/moshi-finetune · Kyutai voices: https://huggingface.co/kyutai/tts-voices · https://unmute.sh/voice-donation
- pt-BR fonética: Alcaim 1992: https://jcis.sbrt.org.br/jcis/article/view/166 · TTS-Portuguese: https://github.com/Edresson/TTS-Portuguese-Corpus · arXiv:2402.05794 · FalaBrasil: https://github.com/falabrasil/speech-datasets · dialeto carioca: https://pt.wikipedia.org/wiki/Dialeto_carioca · https://pantheon.ufrj.br/handle/11422/22317
- Protocolo caseiro: https://docs.nvidia.com/deeplearning/riva/user-guide/docs/tutorials/tts-dataset-recording-at-home.html · https://ogunlao.github.io/blog/2021/01/26/how-to-create-speech-dataset.html
- QC: DNSMOS: https://arxiv.org/abs/2110.01763 · pipelines in-the-wild: https://arxiv.org/abs/2510.03111 · Emilia-Pipe: https://github.com/open-mmlab/Amphion/tree/main/preprocessors/Emilia · loudness: https://github.com/ScottishFold007/TTSAudioNormalizer
- Volumes p/ emoção: Rasa: https://arxiv.org/abs/2407.14056 · partial finetune: https://arxiv.org/abs/2501.14273 · EELE (LoRA emocional): https://arxiv.org/abs/2408.10852
- Estilo/caption: ParaSpeechCaps: https://arxiv.org/abs/2503.04713 · EmoVoice: https://arxiv.org/abs/2504.12867 · CapSpeech: https://arxiv.org/abs/2506.02863
- Acted/elicited/natural: https://doi.org/10.3390/data10100164 · EMOVOME: https://arxiv.org/abs/2403.02167
- Ferramentas: https://github.com/rhasspy/piper-recording-studio · https://github.com/MycroftAI/mimic-recording-studio · https://github.com/domesticatedviking/TextyMcSpeechy · https://fs-17.github.io/SpeechDataBuilder/
- Fadiga vocal: https://actratoronto.com/vocal-health/ · https://karencommins.com/2009/11/time_required_to_narrate_and_p.html
