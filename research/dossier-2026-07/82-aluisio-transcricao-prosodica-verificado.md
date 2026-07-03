# VERIFICAÇÃO (verificador adversarial — 02/jul/2026)

**Método**: 8 claims load-bearing checados na fonte primária citada (WebFetch; PDFs do PROPOR 2024 e IberSPEECH 2022 lidos na íntegra; API datasets-server do HF pro schema exato) + 1 checagem independente por claim.

| # | Claim | Veredito | Justificativa |
|---|---|---|---|
| 1 | **Números do BRACIS 2025** (arXiv:2511.14779): WER 0,43 vs 0,50 (p<0,01), CER 0,31 vs 0,35, F0-RMSE ≈39,07 vs 44,05 Hz, sem MOS; CML-TTS 59h/30 falantes, 720k steps, RTX 4070; filtros CER>0,6 e overlap >2s/>50% | **CONFIRMADO** | Todos os números batem no HTML do arXiv (2511.14779v1), inclusive "WER (t=2.589, p<0.01)"; nuance: CER deu p=0,07 (não significativo) — o relatório corretamente só alega p<0,01 pro WER. |
| 2 | **Conflito de licença**: HF card = MIT, paper BRACIS = CC BY-NC-ND 4.0, Minimal Corpus (Portulan) = CC BY-NC-ND 4.0 | **CONFIRMADO** | As três pontas verificadas independentemente: card HF declara MIT; o arXiv diz "CC BY-NC-ND 4.0"; o PDF do IberSPEECH 2022 diz Portulan "under the CC BY-NC-ND 4.0 license". O conflito existe mesmo — rastrear proveniência é a atitude certa. |
| 3 | **Configs e campos do ENTOA_TTS** (prosodic 7.527+473, automatic 9.870+500, prossegue ~12k, test 29; 14,33 vs 12,79 tokens; campos incl. `normalized_text`) | **CONFIRMADO** | Contagens do HF viewer batem (prosodic 8k, automatic 10,4k, prossegue 12,1k, audioCorpus 8,44k, test 29); tokens 14,33(±13)/12,79(±9,69) confirmados no arXiv; schema do config `prosodic` confirmado via datasets-server API (path, name, speaker, start_time, end_time, **normalized_text**, text, duration, type, year, gender, age_range, total_duration, quality, theme, audio). Atenção: o config default do viewer mostra outro schema (estilo CORAA, sem normalized_text) — o par text/normalized_text existe no `prosodic`. |
| 4 | **PROPOR 2024 (ProsSegue heurístico)**: 300 ms silêncio, janela 300 ms, delta1 88%, delta2 70%, interval 3 palavras, h2 10 s, tolerância 0,25 s; **silêncio sozinho ≈ todas as heurísticas (Δ 0–3%)**; NTB F1 33–50% > TB 16–29%; macro-F1 31%; UFPAlign; lista de pausas preenchidas | **CONFIRMADO** | Lido direto do PDF (aclanthology.org/2024.propor-1.4.pdf): todos os 6 parâmetros idênticos; "the silences' heuristics alone nearly achieved the same numbers in all cases (with a difference ranging from 0 to 3%)"; macro-F1 = 0,31125; lista de fillers idêntica (hum, uhum, éh, ah, ha, ahn, han, uhn, eh, ehn, hein, oh, hun). A regra dominante do Passo 1 da receita está bem fundamentada. |
| 5 | **Roll et al. 2023 (Psst)**: Whisper fine-tuned p/ IUs, F1 87%/96% (SBC), citado como melhor resultado; grupo declara intenção de estudar pontuação do Whisper vs fronteiras prosódicas | **CONFIRMADO** | Tabela 3 do PROPOR 2024 lista Roll et al. (2023) com "87%/96% (SBC), 73%/93% (IViE)" e a conclusão declara: "We intend to study the correlation between punctuations provided by Whisper and the prosodic boundaries". Paper real e independente: CoNLL 2023 / arXiv:2302.01984, acc 95,8%, F1 0,87. |
| 6 | **Speech Prosody 2026** = "análise acústica de YourTTS e SYNTACC; IUs/sílabas mais curtas e menos variáveis; 70% dos contornos nucleares divergem" | **PARCIALMENTE REFUTADO** (atribuição errada; substância confirmada) | O paper do Speech Prosody 2026 (galdino26) usa **FastSpeech2 sob 3 condições de segmentação** (manual, WhisperX, ML) — não YourTTS/SYNTACC — e confirma o "70% of synthesized nuclear contours differed" e "automatic segmentation does not capture systematically pauses and F0 variations". A análise YourTTS/SYNTACC com IUs/sílabas "significantly shorter and less variable" é de **outro paper do grupo (ENIAC 2024)**, confirmada por busca independente. Nuance extra: o abstract do SP2026 reporta variabilidade MAIOR em eventos tonais/foco prosódico no sintético — a claim de "menos variável" refere-se a durações (ENIAC 2024), não a eventos tonais. Impacto na receita: nenhum (Passo 7 continua válido), mas corrigir a citação do scorecard. |
| 7 | **IberSPEECH 2022 (convenções + kappa)**: símbolos (::/:::/CAPS/`/`/`...`=só silêncio), fáticos sempre escritos, risos como unidade separada `((risos))`, kappa 0,67–0,83 (overall) / 0,80–0,88 (partial), pistas acústicas (pausa+F0+duração), "pausa sempre indica quebra; nem toda quebra tem pausa" | **CONFIRMADO** | Lido direto do PDF (isca-archive): todas as convenções batem, incluindo as adaptações (só 2 níveis de alongamento; ellipsis só p/ silêncio; risos separados ao contrário do C-ORAL-BRASIL; filled pauses/false starts NÃO viram unidades); Tabela 1: κ overall 0,67/0,82/0,83, partial 0,80/0,85/0,88; footnote 6 = a "regra de ouro" verbatim. |
| 8 | **Review JBCS**: 100 estudos 2020–2024, F0-RMSE = métrica objetiva de prosódia mais usada; **STIL 2025**: Random Forest, F1 0,55 binário / 0,77 macro | **CONFIRMADO** (JBCS integral; STIL nos números) | JBCS 5468: "100 studies published between 2020 and 2024", F0-RMSE a mais frequente — verbatim. STIL 37818 (abstract): "F1 score of 0.55 and 0.77, with binary and macro averages", RF com F0/taxa/pausa/energia. Detalhes "9 features no nível da sílaba" e "janela 300 ms" não verificáveis no abstract → **PLAUSÍVEL** (coerente com o pipeline do grupo). |

**Balanço**: 7/8 claims confirmados na fonte citada, incluindo todos os que sustentam a receita (thresholds do Passo 1, evidência quantitativa do Passo 3, convenções do Passo 4, filtros do Passo 6, métricas do Passo 7). Único erro real: a atribuição YourTTS/SYNTACC ao Speech Prosody 2026 (é do ENIAC 2024) — corrigir a citação, manter a conclusão. O aviso de calibração do próprio relatório ("ganho modesto, FastSpeech2, sem evidência em modelos CSM/LLM-áudio") está correto e deve ser mantido.

---

# Sandra Aluísio (NILC/ICMC-USP) — fala espontânea pt-BR, prosódia e transcrição para TTS (2023–2026)

## 1. Contexto: quem é e onde o trabalho acontece

- **Sandra Maria Aluísio** — ICMC-USP São Carlos, NILC (sandra@icmc.usp.br). Lidera a frente de fala do projeto **TaRSila** (C4AI-USP): trazer o acervo NURC-SP (~334h, gravações 1970s) para vida digital e construir datasets de ASR/TTS de fala espontânea.
  - TaRSila: https://sites.google.com/view/tarsila-c4ai
  - Portal NURC-SP: https://nurc.fflch.usp.br/
  - Página ACL Anthology (lista completa de papers): https://aclanthology.org/people/sandra-aluisio/
  - Org no HuggingFace: https://huggingface.co/nilc-nlp | GitHub: https://github.com/nilc-nlp
- A tese do grupo, em uma frase: **fala espontânea deve ser segmentada e transcrita por UNIDADES ENTOACIONAIS (IUs), não por pontuação gramatical/janela de ASR** — e treinar TTS nesses segmentos produz fala mais inteligível e com prosódia mais próxima da natural.

## 2. O dataset NURC-SP_ENTOA_TTS (o artefato central)

- **HuggingFace**: https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS — card diz **licença MIT** (atenção: o paper BRACIS diz que os recursos foram liberados **CC BY-NC-ND 4.0**, e o Minimal Corpus no Portulan Clarin é CC BY-NC-ND 4.0 — conflito de licença a rastrear no `dataset_registry.yaml`; para MODO PESQUISA tanto faz, mas registrar proveniência).
- **Página do projeto**: https://nilc-nlp.github.io/entoa-tts/ | **Código**: https://github.com/nilc-nlp/entoa-tts
- Origem: 20 áudios do **CORAA NURC-SP Minimal Corpus** (gravações 1971–1977; EF=aulas formais, DID=entrevistas, D2=diálogos), ~15,5h de fala.
- **Configs (subsets)**:
  - `prosodic` — 7.527 train + 473 val (7.816 segmentos, 12h32m). Segmentado **só em fronteiras terminais (TB)** da anotação manual. Média 14,33 tokens/segmento (±13) — segmentos maiores e mais variáveis.
  - `automatic` — 9.870 train + 500 val (10.182 segmentos, 16h33m). Segmentação **WhisperX** (máx 30s). Média 12,79 tokens (±9,69) — segmentos mais regulares.
  - `audioCorpus` (7.941+500), `prossegue` (12.065, segmentação automática do ProsSegue), `test` (29).
- **Campos**: `path, name, speaker (ex.: SP_D2_255_TB-L2), start_time, end_time, duration, text, normalized_text, type (EF/DID/D2), year, gender, age_range, quality, theme, audio`.
- **Como é o texto anotado (exemplos REAIS extraídos do dataset viewer)**:
  - `"há dez anos atrás eu trabalhava com jornal e:: não era professor então minha atividade era... mais diversificada... então viajei bastante de avião."`
  - `"tivesse eu o dia TOdo ao meu dispor... talvez aquela ligação que não saia naquele momento pudesse sair em OUtros momentos."`
  - `"quer dizer... ele não chega nem a lé/ a a ao nível DA opção."`
  - `"senão o que nós temos é realmente um cemitério de homens né? um caos."`
  - Correspondente `normalized_text`: minúsculas, sem `::`/`...`/`/`/CAPS, mantém só `.` ou `?` final.
- Filtros aplicados na construção: remoção de segmentos com **CER > 0,6** vs ASR, **sobreposição de vozes > 2s** (ou >50% do tempo), risos e trechos ininteligíveis.

## 3. As convenções de anotação (fonte primária: paper do Minimal Corpus, IberSPEECH 2022)

- Paper: **"CORAA NURC-SP Minimal Corpus: a manually annotated corpus of Brazilian Portuguese spontaneous speech"** (Santos, Alves, ..., Svartman, Leite, Aluísio) — https://www.isca-archive.org/iberspeech_2022/santos22_iberspeech.pdf (DOI 10.21437/IberSPEECH.2022-33). Dados: https://hdl.handle.net/21.11129/0000-000F-73CA-C (Portulan Clarin, CC BY-NC-ND 4.0).
- **Símbolos (norma NURC adaptada)**:
  - `/` — palavra truncada (`lé/`); hífen — pronúncia silabada
  - `::` — alongamento vocálico/consonantal; `:::` — alongamento extra (adaptação: SÓ esses dois níveis)
  - MAIÚSCULA na sílaba — ênfase (`TOdo`, `criAR`)
  - `?` — pergunta; `...` — **apenas trecho SEM fala (silêncio)** (adaptação: no NURC original marcava "qualquer pausa")
  - `[` — sobreposição de vozes; aspas — digressão; hífen duplo — discurso direto
  - `( )` vazio — incompreensível; `(hipótese)` — hipótese do ouvido; `(( ))` — comentário descritivo (em tier separada, não no texto)
  - Risos = **unidade separada** com tag `((risos))`; siglas expandidas p/ pronúncia + `((sigla))`; nomes abreviados expandidos (`M.` → `Maria`) + `((name))`; estrangeirismos + `((palavra estrangeira))`
  - Pontuação restrita; maiúsculas só em nomes próprios; **números por extenso**; **expressões fáticas/fillers sempre escritos**
- **Segmentação em IUs (base teórica: C-ORAL-BRASIL / Language into Act Theory)**:
  - **TB (terminal break)** = enunciado completo, menor unidade pragmaticamente autônoma → vira o **fim do segmento** e recebe `.` `?` `!` `...`
  - **NTB (non-terminal break)** = quebra prosódica interna, não autônoma → fica DENTRO do segmento
  - Pistas acústicas de fronteira em pt-BR: **inserção de pausa, mudanças de F0 (reset/tom de fronteira) e duração (alongamento final)**; também taxa de elocução e intensidade
  - Regra de ouro deles: *pausa sempre indica quebra prosódica; mas nem toda quebra tem pausa*
  - Pausas preenchidas (éh, ah...) e falsos começos **não viram unidades separadas** (diferente do C-ORAL-BRASIL)
  - Confiabilidade inter-anotador: kappa 0,67–0,83 (overall), 0,80–0,88 (partial)
- TextGrid multinível no Praat: tiers TB-/NTB- por falante (L1, L2, DOC1, DOC2), LA, COM, e cópia normalizada (N-). No PROPOR 2024 aparece ainda a tier `-point` com a pontuação que fecha cada TB: `. ? ! ...`

## 4. A tese central e a evidência quantitativa

**Paper-chave: "The Impact of Prosodic Segmentation on Speech Synthesis of Spontaneous Speech"** — Galdino, Leal, de Souza, Lima, Moreira, Candido Jr., Oliveira Jr., Casanova, Aluísio. BRACIS 2025.
- arXiv: https://arxiv.org/abs/2511.14779 (HTML: https://arxiv.org/html/2511.14779v1) | Springer: https://link.springer.com/chapter/10.1007/978-3-032-15984-7_37
- Setup: FastSpeech 2 (não-autoregressivo), treino ENTOA-prosodic vs ENTOA-automatic, ambos + CML-TTS pt (59h, 30 falantes), MFA para fonemas, 720k steps, RTX 4070 (~4 dias).
- **Números**:
  - Inteligibilidade: **WER 0,43 (prosódico) vs 0,50 (automático), p<0,01**; CER 0,31 vs 0,35
  - Prosódia: **F0-RMSE ≈ 39,07 Hz (prosódico) vs 44,05 Hz (automático)** vs contornos naturais
  - Sem MOS nesse paper (avaliação objetiva apenas)
- **Por que funciona (leitura deles)**: a segmentação manual por IU produz segmentos com **maior variabilidade de duração** e fronteiras que coincidem com eventos prosódicos reais (pausa+reset de F0+alongamento). O WhisperX corta em fronteiras "convenientes" (~30s, pausas quaisquer), quebrando unidades pragmáticas — o modelo aprende prosódia "média" e regular = robótica. Segmentar onde a prosódia realmente fecha ensina o modelo a fechar contornos.

**Complemento (o "scorecard do robótico"): "Investigating the effect of automatic prosodic segmentation on speech synthesis for Brazilian Portuguese"** — Galdino, Fernandes, Craveiro, Alves, Leal, Candido Jr., Svartman, Aluísio. **Speech Prosody 2026** (DOI 10.21437/SpeechProsody.2026-27) — https://www.isca-archive.org/speechprosody_2026/galdino26_speechprosody.html
- Análise acústica de YourTTS e SYNTACC vs fala natural: fala sintética tem **IUs e sílabas significativamente mais curtas e menos variáveis**; **70% dos contornos nucleares sintetizados diferem dos naturais**; segmentação automática **não captura sistematicamente as pausas e variações de F0 que delimitam IUs**. É a quantificação objetiva do "robótico" (bate com a tua memória `reference-aluisio-prosodia-eval.md`).

**Review de métricas: "The evaluation of prosody in speech synthesis: a systematic review"** — Galdino, Matos, Svartman, Aluísio, JBCS 2025 (DOI 10.5753/jbcs.2025.5468) — https://journals-sol.sbc.org.br/index.php/jbcs/article/view/5468 (PDF: https://journals-sol.sbc.org.br/index.php/jbcs/article/view/5468/3317). 100 estudos 2020–2024; **F0-RMSE é a métrica objetiva de prosódia mais usada**; parâmetros: F0, duração, intensidade.

**EyetrackingMOS** — Araújo, Galdino, Lima, Ishida, Lopes, Oliveira Jr., Candido Jr., Aluísio, Ponti. STIL 2024 (DOI 10.5753/stil.2024.245424) — https://sol.sbc.org.br/index.php/stil/article/view/31120 (PDF: https://sol.sbc.org.br/index.php/stil/article/view/31120/30923). Avaliação online de TTS com eye tracking; 76 anotadores; correlação razoável com MOS e avaliação mais rápida.

## 5. A ferramenta: ProsSegue (segmentação prosódica automática)

- **Código**: https://github.com/nilc-nlp/ProsSegue
- **Paper baseline (heurístico): "Simple and Fast Automatic Prosodic Segmentation of Brazilian Portuguese Spontaneous Speech"** — Craveiro, Santos, Dalalana, Svartman, Aluísio, PROPOR 2024 — https://aclanthology.org/2024.propor-1.4/ (PDF: https://aclanthology.org/2024.propor-1.4.pdf). Adaptação do método de Biron et al. 2021 (PLoS ONE, https://doi.org/10.1371/journal.pone.0250969) para pt-BR.
  - **Parâmetros exatos** (mantidos de Biron): `window_size` = **300 ms** (janela p/ medir taxa de elocução, média dos fonemas não-silenciosos por palavra); `silence_threshold` = **300 ms** de pausa ⇒ fronteira; `delta1` = **88%** da maior diferença de taxa de elocução do turno (heurística 1, DSR); `delta2` = **70%** (heurística 2, aplicada a trechos >3s com >10 palavras); `interval_size` = 3 palavras mínimas entre DSRs; `min_words_h2` = 10 s; tolerância de acerto na avaliação = **0,25 s**.
  - Alinhador forçado: **UFPAlign** (Kaldi, específico pt-BR; Batista et al. 2022, https://doi.org/10.1186/s13634-022-00844-9); áudios longos divididos em blocos de 10 min.
  - **Resultado crucial pra ti**: a **heurística de silêncio sozinha empata com todas juntas (diferença 0–3%)**. O método é melhor para **NTB (F1 33–50%)** do que TB (F1 16–29%); macro-F1 31% (vs 66% de Biron em inglês — diferenças: mantiveram pausas preenchidas, sem tuning de parâmetros pro pt-BR, áudio anos 70).
  - Lista de pausas preenchidas usada: `hum, uhum, éh, ah, ha, ahn, han, uhn, eh, ehn, hein, oh, hun`.
  - Subcorpus CATNA anotado disponível: http://tarsila.icmc.usp.br:8080/nurc/catna. Padrões CATNA (simplificação do MC): sem pontuação/caractere especial, caixa baixa, números por extenso, fáticos sempre escritos, `( )` p/ incompreensível, risos = tag `((risos))` em NTB separada.
- **Versão ML: "Machine Learning Classifiers with Acoustic Features for Prosodic Segmentation in Brazilian Portuguese"** — Craveiro et al., STIL 2025 — PDF: https://sol.sbc.org.br/index.php/stil/article/download/37818/37596/ — Random Forest com **9 features acústicas no nível da sílaba** (F0, taxa de elocução, pausa, energia, duração da vogal do núcleo...); F1 0,55 binário / 0,77 macro; janela de 300 ms.
- **Robustez: "Robustness and Diversity Evaluation on ProsSegue-ML"** — Craveiro & Aluísio, PROPOR 2026 — https://aclanthology.org/2026.propor-2.24/ (PDF: https://aclanthology.org/2026.propor-2.24.pdf). Alerta: expandir treino com dados maiores porém menos diversos piora desigualdades entre grupos de falantes.
- Nota importante do PROPOR 2024: eles citam **Roll et al. 2023 (Psst!)** — *fine-tuning do Whisper para segmentar IUs* obteve os melhores resultados da literatura (F1 87%/96% SBC) — e declaram intenção de estudar a correlação entre a pontuação do Whisper e fronteiras prosódicas. Ou seja: o teu pipeline (Whisper + pós-processador) está exatamente na direção que eles apontam como estado da arte.

## 6. Outros recursos 2024–2026 do grupo (contexto)

- **MuPe Life Stories** — Leal, Candido Jr., Marcacini, Casanova, ..., Aluísio, COLING 2025: ~365h de fala espontânea (histórias de vida, Museu da Pessoa), estudo de viés de ASR — https://aclanthology.org/people/sandra-aluisio/ (entrada COLING 2025).
- **Certas Palavras** — Araújo, Ponti, ..., Aluísio, PROPOR 2026: corpus de rádio 1980s-90s, **70h de diálogo espontâneo multi-falante com ruído, CC BY 4.0**, para estressar TTS — https://aclanthology.org/2026.propor-1.81.pdf
- **Portal NURC-SP** (PROPOR 2024) e **CORAA-NURC-SP-Audio-Corpus** (239,68h transcritas por ASR): https://huggingface.co/datasets/nilc-nlp/CORAA-NURC-SP-Audio-Corpus | https://github.com/nilc-nlp/nurc-sp | https://github.com/nilc-nlp/nurc-sp-audio-corpus
- **EF/TTS p/ ASR**: "TTS applied to the generation of datasets for ASR" (Casanova, Ponti, Aluísio, PROPOR 2024).

## 7. Orientandos/coautores ativos (2024–2026) — quem faz o quê

| Nome | Papel |
|---|---|
| **Julio Cesar Galdino** (ICMC) | Doutorando; 1º autor do BRACIS 2025, Speech Prosody 2026 e da review JBCS — impacto da segmentação prosódica no TTS + métricas de prosódia. O contato técnico natural pro teu caso de uso. |
| **Giovana Meloni Craveiro** (ICMC) | Autora do ProsSegue (PROPOR 2024, STIL 2025, PROPOR 2026) — segmentação prosódica automática. |
| **Vinícius G. Santos** (FFLCH) | Liderou anotação do Minimal Corpus (IberSPEECH 2022); convenções de transcrição. |
| **Flaviane R. F. Svartman** (FFLCH) | Professora, prosodista — fundamentação linguística das IUs. |
| **Miguel Oliveira Jr.** (UFAL) | Autor do protocolo NURC Digital; coautor recorrente. |
| **Sidney Evaldo Leal** | MuPe, ENTOA, engenharia de datasets. |
| **Arnaldo Candido Junior** | Modelos ASR/TTS (CORAA). |
| **Edresson Casanova** | Ex-grupo (YourTTS/XTTS, hoje NVIDIA), coautor nos papers de TTS. |
| **Moacir Ponti** (ICMC) | EyetrackingMOS, avaliação. |
| **Gustavo E. Araújo, Rodrigo F. Lima, Leticia G. de Souza, Caroline A. Alves, Rian P. Fernandes, Gabriel Dalalana** | EyetrackingMOS / Certas Palavras / anotação / ProsSegue. |

---

# RECEITA IMPLEMENTÁVEL — pós-processador prosódico pro pipeline (faster-whisper large-v3 + word timestamps + F0)

Objetivo: transformar a saída do Whisper em segmentos-IU com "pontuação prosódica" no estilo ENTOA-prosodic, gerando `text` (com marcas) e `normalized_text` por segmento.

### Passo 0 — insumos por palavra
- Word timestamps do faster-whisper (`word_timestamps=True`).
- Pausa entre palavras: `gap = start[i+1] - end[i]`.
- F0 por frame (parselmouth/pyworld, 10 ms): média/mediana de F0 na última sílaba/palavra antes do gap e na primeira depois (reset = `F0_next_mean - F0_prev_final`).
- Duração média de fonema por palavra ≈ `dur_palavra / n_chars_foneticos` numa janela de **300 ms** (proxy da taxa de elocução deles).

### Passo 1 — detectar fronteiras prosódicas (candidatas)
1. **Regra dominante (implementa primeiro, resto é refinamento)**: `gap ≥ 0,300 s` ⇒ fronteira prosódica. *Evidência: no PROPOR 2024, silêncio sozinho ≈ todas as heurísticas combinadas (Δ 0–3% F1).*
2. Refinamento DSR (opcional, heurísticas de Biron adaptadas): calcular taxa de elocução por palavra (janela 300 ms); marcar fronteira quando a diferença entre medidas consecutivas exceder **88%** da maior diferença do turno (H1); segunda passada com limiar **70%** apenas em trechos > 3 s e > 10 palavras (H2).
3. Nunca contar pausa preenchida como silêncio: antes de medir `gap`, funde `{ah, éh, eh, ehn, ahn, han, uhn, hum, uhum, hein, oh, hun, ha, né}` à fala adjacente.

### Passo 2 — classificar TB (terminal) vs NTB (não-terminal)
O método deles é fraco nisso (TB F1 16–29%); usa um ensemble de pistas — é onde teu pipeline pode superar o deles:
- **TB se**: (pontuação do Whisper ∈ {`.`, `?`, `!`} na palavra) E (`gap ≥ 0,300 s` OU fim de turno) — Roll et al. 2023 mostram que o Whisper já carrega sinal prosódico na pontuação; o grupo da Aluísio aponta essa combinação como caminho.
- Reforços acústicos de TB: F0 final descendente + **reset de F0 para cima** no início da unidade seguinte (ex.: `reset > +2 semitons`); alongamento da sílaba final (duração da última vogal > μ+2σ do falante); pausa mais longa (sugestão prática: `gap ≥ 0,6 s` promove a TB mesmo sem pontuação).
- **NTB se**: `gap ≥ 0,300 s` sem as pistas terminais.
- `?` quando F0 terminal ascendente (ou o Whisper já pontuou `?`).

### Passo 3 — segmentar para TTS **somente em TB**
- Cada amostra de treino = 1 unidade terminal completa (do TB anterior ao TB atual). NÃO cortar em NTB.
- Alvo de distribuição: média ~14 tokens/segmento com desvio alto (±13), duração 0,2–29,5 s como no ENTOA. **Não uniformizar**: a variabilidade é o que melhorou a naturalidade (WER 0,43 vs 0,50; F0-RMSE 39 vs 44 Hz). Se precisares do teu range 3–12 s, corta apenas em TBs e aceita concatenar IUs curtas adjacentes do mesmo falante — nunca dividir uma IU no meio.
- Fim do segmento recebe `.` `?` `!` ou `...` (interrompido/suspenso).

### Passo 4 — marcas dentro do texto (campo `text` prosódico)
| Fenômeno | Marca | Como detectar automaticamente |
|---|---|---|
| Pausa silenciosa interna (NTB) | `...` no lugar do gap | `gap ≥ 0,300 s` intra-segmento |
| Alongamento | `::` após o segmento alongado (`e::`, `telefone::`); `:::` se extremo | duração da vogal > μ+2σ (ou 3σ p/ `:::`) do próprio falante; ou razão duração-palavra/duração-esperada |
| Palavra truncada | `/` colado (`lé/`) | palavra com baixa confiança + duração curta + repetição parcial da seguinte |
| Ênfase | sílaba em MAIÚSCULA (`TOdo`) | pico local de F0+energia (opcional, v2) |
| Pergunta | `?` (inclusive interno: `né?`) | pontuação Whisper + F0 ascendente |
| Fillers | **manter escritos**, forma padronizada da lista acima | nunca deletar — têm função discursiva (decisão explícita do grupo) |
| Risos | segmento separado / tag `((risos))` → **excluir do treino TTS** | detector de riso ou tag do Whisper |
| Números | por extenso | num2words pt-BR |
| Siglas | expandidas p/ pronúncia | dicionário |

### Passo 5 — campo `normalized_text`
Cópia em caixa baixa, sem `::` `/` `...` internos, sem CAPS, mantendo apenas pontuação final (`.`/`?`). (É exatamente o par que o ENTOA fornece — útil pra treinar com/sem marcas e comparar.)

### Passo 6 — filtros de qualidade (do BRACIS 2025)
- Descartar segmento se **CER(transcrição vs re-ASR) > 0,6**; sobreposição de falantes > 2 s ou > 50% do segmento; risos/ininteligível.

### Passo 7 — avaliação (fecha o loop com teu prosody_scorecard)
- **F0-RMSE** vs áudio natural (métrica nº 1 da literatura, review JBCS).
- Distribuições de **duração de IU e de sílaba** (sintético vs natural): o "robótico" = IUs curtas demais e pouco variáveis (Speech Prosody 2026); % de contornos nucleares divergentes (eles mediram 70% nos modelos atuais).
- Tolerância de 0,25 s ao comparar fronteiras previstas vs referência.

### Avisos de calibração (realismo, não otimismo)
- Ganho comprovado é **modesto**: ~7 pontos de WER e ~5 Hz de F0-RMSE, em FastSpeech2 (não-autoregressivo) num corpus dos anos 70 — não há evidência publicada ainda em modelos tipo CSM/LLM-áudio; trata como aposta barata de alta plausibilidade, não como bala de prata.
- O classificador TB/NTB deles é fraco (macro-F1 31%); a heurística confiável é **pausa ≥ 300 ms**. O caminho apontado por eles mesmos (Whisper fine-tuned p/ IUs, Roll et al. 2023, F1 até 96%) é a melhoria natural v2.
- Licenças: ENTOA_TTS no HF diz MIT, mas o paper diz CC BY-NC-ND 4.0 e o Minimal Corpus (Portulan) é CC BY-NC-ND 4.0 — registrar como proveniência ambígua; a RECEITA (regras/thresholds) é livre para implementar no teu dado.

### URLs consolidadas
- Dataset: https://huggingface.co/datasets/nilc-nlp/NURC-SP_ENTOA_TTS · https://nilc-nlp.github.io/entoa-tts/ · https://github.com/nilc-nlp/entoa-tts
- Código de segmentação: https://github.com/nilc-nlp/ProsSegue · CATNA: http://tarsila.icmc.usp.br:8080/nurc/catna
- Papers: PROPOR 2024 https://aclanthology.org/2024.propor-1.4.pdf · BRACIS 2025 https://arxiv.org/abs/2511.14779 (Springer https://link.springer.com/chapter/10.1007/978-3-032-15984-7_37) · Speech Prosody 2026 https://www.isca-archive.org/speechprosody_2026/galdino26_speechprosody.html · STIL 2025 (ML) https://sol.sbc.org.br/index.php/stil/article/download/37818/37596/ · PROPOR 2026 (ProsSegue-ML) https://aclanthology.org/2026.propor-2.24.pdf · IberSPEECH 2022 (convenções) https://www.isca-archive.org/iberspeech_2022/santos22_iberspeech.pdf · EyetrackingMOS https://sol.sbc.org.br/index.php/stil/article/view/31120 · Review JBCS https://journals-sol.sbc.org.br/index.php/jbcs/article/view/5468 · Certas Palavras https://aclanthology.org/2026.propor-1.81.pdf
- Corpora relacionados: https://hdl.handle.net/21.11129/0000-000F-73CA-C (Minimal Corpus) · https://huggingface.co/datasets/nilc-nlp/CORAA-NURC-SP-Audio-Corpus · https://github.com/nilc-nlp/nurc-sp · https://github.com/nilc-nlp/nurc-sp-audio-corpus
- Base externa: Biron et al. 2021 https://doi.org/10.1371/journal.pone.0250969 · UFPAlign https://doi.org/10.1186/s13634-022-00844-9 · Roll et al. 2023 ("Psst! prosodic speech segmentation with transformers", citado no PROPOR 2024 como melhor resultado)