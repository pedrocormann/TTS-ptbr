# FRENTE D — Bases pt-BR: contradições resolvidas e ativação do eval

**Data:** 2026-06-10 · **Projeto:** TTS-ptbr (conversacional pt-BR nível Maya/Sesame; licença dura Apache/MIT/CC-BY/CC0 no produto)
**Método:** verificação na fonte primária (paper PDF, OpenSLR, cards HF, READMEs, Linguateca, sites institucionais). Tudo abaixo tem URL primária. Onde não há evidência, está dito explicitamente.

---

## 1. CML-TTS português: horas REAIS — **RESOLVIDO: ~68 h de treino (~69,4 h total), não ~1.100 h**

Fui à Tabela 1 do paper (PDF baixado de https://arxiv.org/pdf/2306.10097, "CML-TTS: A Multilingual Dataset for Speech Synthesis in Low-Resource Languages", Oliveira et al., TSD 2023). Valores exatos:

| Língua | Train (M / F) | Test (M / F) | Dev (M / F) | Falantes Train (M/F) |
|---|---|---|---|---|
| Dutch | 482,82 / 162,17 | 2,46 / 1,29 | 2,24 / 1,67 | 8 / 27 |
| French | 260,08 / 24,04 | 2,48 / 3,55 | 3,31 / 2,72 | 25 / 20 |
| German | **1.128,96** / 436,64 | 3,75 / 5,27 | 4,31 / 5,03 | 78 / 90 |
| Italian | 73,78 / 57,51 | 1,47 / 0,85 | 0,40 / 1,52 | 23 / 38 |
| Polish | 30,61 / 8,32 | 0,70 / 0,90 | 0,56 / 0,80 | 4 / 4 |
| **Portuguese** | **23,14 / 44,81** | **0,28 / 0,24** | **0,68 / 0,20** | **20 / 10** |
| Spanish | 279,15 / 164,08 | 2,77 / 2,06 | 3,40 / 2,34 | 35 / 42 |
| **Total** | **3.176,13** | 28,11 | 29,19 | 424 (+94 test, +95 dev) |

**Português (pt, gravações LibriVox — maioria pt-BR):**
- **Train: 67,95 h** (23,14 h masc + 44,81 h fem), **30 falantes** (20M/10F)
- **Test: 0,52 h** (9 falantes: 5M/4F) · **Dev: 0,88 h** (9 falantes: 6M/3F)
- **Total: ≈ 69,35 h**
- Amostras (card HF ylacombe/cml-tts, https://huggingface.co/datasets/ylacombe/cml-tts): **34.265 train / 1.134 dev / 1.297 test**
- 24 kHz, derivado do MLS com repontuação + re-segmentação + validação Wav2Vec (similaridade ≥ 0,9)

**Origem da divergência 16x (~1.100 h vs ~68 h):** a linha do **alemão** na mesma tabela é 1.128,96 h de treino — quase certamente leitura trocada de linha da Tabela 1 (não existe NENHUMA fonte primária com ~1.100 h de pt; o total do dataset inteiro é 3.233,43 h / 613 falantes). Corroboração independente: o arquivo pt no OpenSLR 146 (https://www.openslr.org/146/) tem **9,7 GB** (`cml_tts_dataset_portuguese_v0.1.tar.bz`) — compatível com ~69 h a 24 kHz, e incompatível com 1.100 h (o alemão, com 1.565 h, ocupa ~187 GB).

**Licença:** CC-BY 4.0 (OpenSLR 146 e card HF; áudio LibriVox/Gutenberg em domínio público). **Usável no produto.**

**Implicação:** CML-TTS pt é base legítima de pré-treino/aquecimento (~68 h limpas, multi-falante, CC-BY), mas NÃO é o "corpus gigante" que parte da literatura sugere. Para volume, as alternativas continuam sendo MLS-pt bruto, CORAA (licenças restritivas) ou dados próprios/SOTAQUE.

---

## 2. BRSpeechMOS (arXiv 2306.09979) — **dataset PÚBLICO via Drive/OneDrive; código público; SEM checkpoint pré-treinado; SEM licença declarada**

Paper: "Evaluation of Speech Representations for MOS prediction" (Oliveira et al., TSD 2023) — https://arxiv.org/abs/2306.09979 (versão HTML: https://arxiv.org/html/2306.09979).

**O que é:** **2.428 amostras de áudio a 16 kHz** em pt-BR, cada uma avaliada por **em média 2 avaliadores** (escala MOS). O paper não identifica quais sistemas TTS geraram as amostras. Melhores extratores no BRSpeechMOS: **Whisper-Small (LCC 0,6980)** e **SpeakerNet (0,6963)**.

**Disponibilidade verificada (2026-06-10):**
- **Código:** https://github.com/freds0/BSpeech-MOS-Prediction — treino (`python train.py -c configs/config_model.json`), teste (`test.py`), extração de embeddings (`extract_emb/`), Python 3.9.
- **Dataset:** link público no README — Google Drive `BRSPEECH_MOS_DATASET_v2.tar.bz` (https://drive.google.com/file/d/1_nSqIzFzvDdmIaJB6uxjhJ20pnZJA7ru/view) — **verifiquei via HTTP: responde 200 e é acessível sem login**. Espelho OneDrive/UFMT no README.
- **Checkpoint pré-treinado: NÃO existe** (nem no repo, nem em HF — busquei; não há "BRSpeechMOS" no Hugging Face).
- **Licença: NÃO declarada** nem no repo nem no dataset. Risco para redistribuição; uso interno de eval é de baixo risco, mas não dá para embutir no produto.

**Como rodar (pipeline do repo):** (1) baixar dataset; (2) extrair embeddings com os scripts de `extract_emb` (Whisper/SpeakerNet/etc.); (3) treinar o regressor MOS com `train.py` + config JSON; (4) `test.py` produz a predição MOS por áudio. Input: wav 16 kHz; output: MOS escalar.

**Caminho recomendado para o eval:**
1. **Treinar nós mesmos** o predictor (dataset público + código público; custo baixo: 2.428 amostras, embeddings congelados, cabe no M2/Colab em minutos-horas).
2. Em paralelo, **e-mail ao autor** (Frederico Santos de Oliveira, UFMT/AKCIT — o OneDrive é `frederico_oliveira_ufmt_br`) pedindo checkpoint e clarificação de licença.
3. Não depender só dele: manter TTSDS2/UTMOS como métricas-âncora e usar o BRSpeechMOS-predictor como métrica pt-BR complementar.

---

## 3. Licenças pendentes — estado real em 2026-06-10

### 3.1 freds0/BRSpeech-TTS — **continua SEM licença; pedido público sem resposta; migração embrionária para AKCIT-Speech**
- Card: https://huggingface.co/datasets/freds0/BRSpeech-TTS — público, não-gated, **76,3 mil amostras** (73.848 train / 1.158 val / 1.316 test), ~27,6 GB, 2.960+ falantes (áudio literário/audiobook), `lastModified` 2025-04-19. **Campo license: ausente** (confirmado via API do HF).
- Discussão aberta **"Can you add any license for BRSpeech-TTS?"** (#2, aberta ~mar/2026 por thotnd): **sem resposta do autor** até hoje — https://huggingface.co/datasets/freds0/BRSpeech-TTS/discussions
- **Movimento novo:** existe **https://huggingface.co/datasets/AKCIT-Speech/BRSpeech-TTS** (org AKCIT-Speech, atualizado em fev/2026) — porém **VAZIO** (2,46 kB, sem card, sem licença). Sinaliza migração institucional do dataset para o AKCIT, ainda não concretizada. Vale monitorar.
- **Veredito:** sem licença = **inutilizável no produto**. Não houve liberação.

### 3.2 freds0/BRSpeech-YT — **existe no HF, mas está VAZIO**
- https://huggingface.co/datasets/freds0/BRSpeech-YT — placeholder de 2,5 kB, sem card, sem dados, sem licença. **Nenhum movimento verificável.** (Buscas por "BRSpeech-YT" não retornam nenhum release em outro lugar.)

### 3.3 nilc-nlp/NURC-SP_ENTOA_TTS — **tag MIT permanece, SEM clarificação publicada; contradição com upstream CC BY-NC-ND continua em aberto**
- README (https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS/raw/main/README.md): `license: mit` no YAML, **nenhum texto adicional de clarificação**. ~31 mil segmentos (~50–60 h estimadas), fala espontânea, 16 kHz, prosódia anotada, público/não-gated.
- Citações novas no README: **BRACIS 2025** ("The Impact of Prosodic Segmentation on Speech Synthesis of Spontaneous Speech", LNCS 16180, Springer 2026) e **Speech Prosody 2026** ("Investigating the effect of automatic prosodic segmentation...", pp. 134-138). Nenhum dos dois resolve a licença do DADO (são papers de método).
- **Contradição não resolvida:** o corpus-mãe NURC-SP Audio Corpus é distribuído sob **CC BY-NC-ND 4.0** — declaração explícita no paper arXiv 2409.15350 ("The corpus and trained models are publicly available in our Github repository under the CC BY-NC-ND 4.0 license", repo github.com/nilc-nlp/nurc-sp-audio-corpus). Um derivado MIT de um corpus BY-NC-ND é juridicamente frágil. **Não encontrei nenhum issue, errata ou nota PROPOR/BRACIS clarificando.** Tratar o MIT como tag não confiável até resposta do NILC.
- **nurc_tts_24khz** (https://huggingface.co/datasets/nilc-nlp/nurc_tts_24khz): **320.916 segmentos, ~81,7 GB, 24 kHz** (SP 121k + Recife 200k) — mas **README vazio e SEM licença nenhuma**. Nenhuma clarificação publicada. Mesmo problema de upstream.
- **Veredito:** nada mudou; para produto Apache/MIT, NURC-* segue **fora** (ou só para eval interno não-redistribuído, com risco aceito e e-mail enviado ao NILC).

### 3.4 CETUC / CETEN-Folha — **reuso do texto NÃO está autorizado de forma verificável**
- CETUC: ~143–145 h, 100–101 falantes, 1.000 frases foneticamente balanceadas extraídas do **CETEN-Folha**. No catálogo FalaBrasil (https://github.com/falabrasil/speech-datasets): CETUC listado **sem licença explícita**, com a nota de que o material foi "provided for research purposes exclusively" (pesquisa apenas).
- CETEN-Folha (Linguateca, https://www.linguateca.pt/cetenfolha/index_info.html): ~24 M palavras de textos da **Folha de S. Paulo**; a página **não publica licença** — apenas agradece "à Folha de São Paulo pela autorização gentilmente concedida" e exige registro/senha para download. Ou seja: o texto-fonte é jornalístico, com copyright da Folha, cedido à Linguateca para fins de pesquisa; **não há concessão verificável de redistribuição ou uso comercial das 1.000 frases**.
- **Veredito:** as 1.000 frases do CETUC **não podem** ser embutidas num produto Apache/MIT (nem como prompts redistribuídos). Para eval interno (síntese das frases para medir WER/MOS sem redistribuir o texto) o risco é baixo, mas a recomendação é gerar/usar conjunto de frases próprio ou CC-0 (ex.: frases novas, Wikipédia CC-BY-SA com cuidado, ou nosso próprio script de seeds).

---

## 4. AKCIT (akcit.ufg.br) — quem são e o que têm de FALA

**O que é:** Centro de Competência **Embrapii** em Tecnologias Imersivas Aplicadas a Mundos Virtuais, coordenado pelo **CEIA-UFG** (Centro de Excelência em IA da UFG). Financiamento: **R$ 60 M do MCTI** (42 meses) + **R$ 20 M** de consórcio Fapeg/Sebrae-GO/empresas (fonte: https://embrapii.org.br/embrapii-instala-centro-de-competencia-em-tecnologias-imersivas-aplicadas-a-mundos-virtuais-em-goiania-go/ e https://inf.ufg.br/p/akcit). Laboratório inaugurado em mai/2025 (https://ufg.br/n/190903-ufg-inaugura-laboratorio-avancado-de-tecnologias-imersivas). ~700 pesquisadores; parcerias citadas: Bancorbrás, Globo, **Vivo** (fev/2025, https://teletime.com.br/17/02/2025/vivo-se-une-com-ufg-para-inovacao-em-inteligencia-artificial/), negociações com VW, Positivo, Flex etc.

**Projetos de FALA verificados:**
- **AKCIT-Speech** (HF org: https://huggingface.co/AKCIT-Speech) — "Advanced Knowledge Center for Immersive Technologies"; membro listado: **Frederico Santos de Oliveira** (autor do CML-TTS, BRSpeechMOS, BRSpeech-TTS). Único dataset: BRSpeech-TTS (vazio, fev/2026). **Nenhum modelo público ainda.**
- **AKCIT-Deepfake** (HF org: https://huggingface.co/AKCIT-Deepfake) — **BRSpeech-DF** (https://huggingface.co/datasets/AKCIT-Deepfake/BRSpeech-DF): primeiro dataset público de detecção de deepfake de fala em português — **459.137 amostras** (76.644 bonafide + 382.493 spoof gerados por 5 TTS zero-shot open-source), 243 GB, **CC-BY 4.0**, citação "AKCIT Speech Group, 2025". Também há o modelo **xtts-BRSpeech-collection** (XTTS treinado na coleção BRSpeech, fev/2026).
- Histórico UFG em voz: **Mr. Falante** (UFG + CyberLabs, pioneiro em síntese de voz no Brasil) e o projeto **TaRSila/CORAA** (acordo ICMC-USP + UFG + Museu da Pessoa, ASR/transcrição, ~300 h MuPe).

**Compete ou complementa?** O grupo de fala do AKCIT (= Frederico Oliveira e colegas) está claramente construindo a pilha pt-BR de síntese (XTTS fine-tunes, BRSpeech-*) — **parcialmente competidor** em TTS pt-BR, mas **complementar** em três pontos: (a) BRSpeech-DF CC-BY 4.0 serve para nosso anti-spoofing/eval de naturalidade; (b) eles são o caminho mais provável para destravar a licença do BRSpeech-TTS; (c) não há evidência pública de TTS **conversacional full-duplex** (nicho Maya/Sesame continua aberto no Brasil).

**Como se candidatar a parceria:** modelo Embrapii de inovação aberta — a empresa propõe projeto com apelo de mercado e co-financia (parte empresa, parte Embrapii/MCTI/Sebrae; bolsistas e professores da UFG entram como equipe). Startups têm porta específica via Sebrae-GO (https://go.agenciasebrae.com.br/inovacao-e-tecnologia/centro-de-competencia-embrapii-em-tecnologias-imersivas-instalado-na-ufg-comeca-a-mobilizacao-de-startups/). Contato direto: akcit.ufg.br (e, taticamente, e-mail ao Frederico Oliveira — UFMT/AKCIT — que já é nosso alvo de contato pelos itens 2 e 3.1).

---

## 5. SOTAQUE (sotaque.ia.br) — **CDLA-Permissive-2.0 confirmada; AINDA SEM release baixável; volume atual ~zero/embrionário**

Verificado direto no site (2026-06-10; o site bloqueia fetchers, baixei com UA de navegador) e no repo:

- **O que é:** "SOTAQUE: Speech-Oriented Training Audio for Quality Understanding and Expression" — dataset aberto crowdsourced de vozes pt-BR com diversidade regional (caipira, baiano, nortista, gaúcho, mineiro, paulistano, carioca). Controlador: **Fabrício Carraro**. Código: https://github.com/fabriciocarraro/projeto-sotaque (74 commits).
- **Licença:** **CDLA-Permissive-2.0** declarada no rodapé do site e no termo de consentimento (item 4 do aceite: "publicação aberta e reutilização da minha gravação sob a licença CDLA-Permissive-2.0") — **permite uso comercial**; compatível com nosso produto.
- **Volume atual:** o site tem mapa "Representação por estado" exibindo **"Vazio"** — i.e., projeto em fase inicial, sem volume divulgado. O README não publica números. Metas declaradas: **1.000 h** (meta inicial p/ treino básico) e **10.000 h** (meta final). **Não há nenhum release baixável ainda**; publicação futura planejada no Hugging Face.
- **Como contribuir:** https://sotaque.ia.br/contribuir/ — gravação direto no navegador ou upload de até 5 arquivos de 100 MB cada (vale áudio de WhatsApp); cadastro de pseudônimo, e-mail, região/estado/sotaque, faixa etária, gênero, escolaridade, nº de falantes; maiores de 18, no Brasil; consentimento explícito para treino/avaliação de TTS. Bot de WhatsApp planejado.
- **Implicação para nós:** é a única fonte pt-BR futura com licença permissiva nativa e fala espontânea diversa — **monitorar e contribuir** (e considerar parceria/divulgação: nosso projeto pode doar gravações do kit e amplificar a coleta; contato no site: oi@[domínio] — verificar no rodapé, o e-mail é ofuscado por JS).

---

## Decisões recomendadas (Frente D)

1. **Corrigir toda doc interna**: CML-TTS pt = **67,95 h train / 69,35 h total / 30 falantes train**, CC-BY 4.0. A cifra ~1.100 h é o alemão. Fechado.
2. **Eval MOS pt-BR**: baixar BRSPEECH_MOS_DATASET_v2 (Drive público) + repo BSpeech-MOS-Prediction e treinar nosso predictor (Whisper-Small como extrator, LCC esperado ≈ 0,70). Sem checkpoint público — treinar é o caminho. Em paralelo, e-mail ao Frederico Oliveira (licença do dataset + checkpoint + licença BRSpeech-TTS + parceria AKCIT num e-mail só).
3. **BRSpeech-TTS/YT**: seguem inutilizáveis (sem licença / vazio). Monitorar a org **AKCIT-Speech** no HF — é onde o destravamento aconteceria.
4. **NURC-***: tag MIT sem lastro (upstream CC BY-NC-ND 4.0); nurc_tts_24khz sem licença alguma. Fora do produto; eval interno apenas com risco documentado.
5. **CETUC**: áudio "research only" e texto (CETEN-Folha/Folha de S.Paulo) sem direito de reuso verificável → **não usar as 1.000 frases no produto**; criar set de frases próprio para eval.
6. **SOTAQUE**: contribuir + monitorar; única promessa de base pt-BR espontânea CDLA-Permissive, mas hoje sem dados.

## Fontes primárias
- https://arxiv.org/abs/2306.10097 + PDF (Tabela 1) · https://www.openslr.org/146/ · https://huggingface.co/datasets/ylacombe/cml-tts · https://freds0.github.io/CML-TTS-Dataset/
- https://arxiv.org/abs/2306.09979 · https://arxiv.org/html/2306.09979 · https://github.com/freds0/BSpeech-MOS-Prediction
- https://huggingface.co/datasets/freds0/BRSpeech-TTS (+/discussions) · https://huggingface.co/datasets/freds0/BRSpeech-YT · https://huggingface.co/datasets/AKCIT-Speech/BRSpeech-TTS
- https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS · https://huggingface.co/datasets/nilc-nlp/nurc_tts_24khz · https://arxiv.org/abs/2409.15350 (CC BY-NC-ND do NURC-SP Audio Corpus)
- https://github.com/falabrasil/speech-datasets · https://www.linguateca.pt/cetenfolha/index_info.html
- https://akcit.ufg.br/ · https://inf.ufg.br/p/akcit · https://embrapii.org.br/embrapii-instala-centro-de-competencia-em-tecnologias-imersivas-aplicadas-a-mundos-virtuais-em-goiania-go/ · https://huggingface.co/AKCIT-Speech · https://huggingface.co/AKCIT-Deepfake · https://huggingface.co/datasets/AKCIT-Deepfake/BRSpeech-DF · https://teletime.com.br/17/02/2025/vivo-se-une-com-ufg-para-inovacao-em-inteligencia-artificial/ · https://go.agenciasebrae.com.br/inovacao-e-tecnologia/centro-de-competencia-embrapii-em-tecnologias-imersivas-instalado-na-ufg-comeca-a-mobilizacao-de-startups/
- https://sotaque.ia.br/ · https://sotaque.ia.br/contribuir/ · https://github.com/fabriciocarraro/projeto-sotaque
