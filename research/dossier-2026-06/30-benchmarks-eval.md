# FRENTE 5 — Benchmarks e Avaliação (estado em 2026-06-10)

> Pesquisa web realizada em 2026-06-10. Todas as afirmações decisivas têm URL primária.
> Contexto: projeto TTS-ptbr (fala conversacional pt-BR, spine Moshi/Kyutai, licença dura Apache/MIT/CC-BY/CC0).

---

## TL;DR — o que muda nas decisões do projeto

1. **Não existe arena nem benchmark público de TTS em pt-BR.** As duas arenas vivas (Artificial Analysis Speech Arena e TTS Arena V2) são inglês-cêntricas. A avaliação pt-BR terá de ser construída em casa — e isso é uma **oportunidade de publicação** (um "ptBR-TTS-eval" não existe; os ingredientes todos existem, ver §6).
2. **Qwen3-TTS (Apache-2.0, jan/2026) muda a aposta de TTS license-clean**: 0.6B/1.7B, português na saída, ~97 ms de latência streaming, clone com 3 s, **código oficial de finetune** — supera Kokoro/Chatterbox como gerador de dado sintético e candidato a componente de voz.
3. **Voxtral TTS (Mistral, mar/2026) suporta pt mas é CC-BY-NC-4.0 → VETADO** no produto (só API comercial).
4. **A aposta na arquitetura Moshi foi validada pela indústria**: NVIDIA PersonaPlex-7B-v1 (jan/2026) é full-duplex sobre Mimi+Helium com controle de persona/voz — código MIT, **pesos sob NVIDIA Open Model License (fora da whitelist; analisar antes de tocar)**.
5. **Métricas para pt-BR em 2026**: UTMOS/UTMOSv2 não são calibrados fora do inglês. Stack recomendado: **TTSDS2 (MIT, multilíngue validado) + Audiobox-Aesthetics (CC-BY-4.0) + DNSMOS (higiene) + WER round-trip + SIM WavLM-SV + LALM-as-judge em pt-BR**, com CMOS humano como ground truth.
6. **WER round-trip pt-BR**: whisper-large-v3 continua o padrão da literatura; Parakeet-TDT-0.6B-v3 / Canary-1B-v2 (CC-BY-4.0, pt WER ~6%) entram como **segundo ASR** — com a ressalva explícita do model card de que foram treinados com **pt europeu**.
7. **PROPOR 2026 entregou os tijolos pt-BR que faltavam**: BIPA (350k transcrições IPA com variante **Rio de Janeiro**, CC-BY-4.0), Certas Palavras (70h de rádio espontânea + baselines YourTTS/F5-TTS) e, fora do PROPOR, **Tagarela (8.972 h de podcasts pt, CC-BY-4.0, para ASR e TTS)**.

---

## 1. Arenas de preferência humana (a)

### 1.1 Artificial Analysis Speech Arena — a arena de referência em 2026

- Leaderboard: https://artificialanalysis.ai/text-to-speech/arena e https://artificialanalysis.ai/text-to-speech/leaderboard (espelho HF: https://huggingface.co/spaces/ArtificialAnalysis/Speech-Arena-Leaderboard). ~**76 modelos** avaliados por Elo de votos cegos.
- **Topo em 03/jun/2026**: **Fun-Realtime-TTS (Alibaba) #1, Elo 1.219** (962 aparições), à frente de Gemini 3.1 Flash TTS (1.214), Inworld Realtime TTS-2 Research Preview (1.209) e Cartesia Sonic 3.5 (1.203). Fonte: https://artificialanalysis.ai/articles/fun-realtime-tts-new-text-to-speech-model-topping-artificial-analysis-leaderboard
- **Snapshot mai/2026 (análise OfflineTTS sobre a mesma arena)**: todo o top-10 é fechado/API. Melhores **open-weights**:
  | # geral | Modelo aberto | Elo |
  |---|---|---|
  | 11 | Fish Audio S2 Pro | 1128,7 |
  | 16 | StepFun Step Audio EditX | 1104,9 |
  | 32 | Kokoro 82M v1.0 | 1056,2 |
  | 33 | Mistral Voxtral TTS (CC-BY-NC!) | 1055,9 |
  | 35 | Maya Research Maya1 (Apache-2.0, EN-only) | 1050,6 |
  Fonte: https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/
- Tendência: o gap open vs. comercial caiu de ~223 Elo (2023) para **~81 Elo (início de 2026)** — abertos melhorando mais rápido.
- **Limitação para nós**: a arena roda com textos/votantes em inglês. **Não há arena pt-BR** (nem sub-leaderboard por língua público até 10/jun/2026).

### 1.2 TTS Arena V2 (TTS-AGI / Hugging Face)

- Vive em https://tts-agi-tts-arena-v2.hf.space/leaderboard e https://ttsarena.org. Comunidade, menos volume que a Artificial Analysis.
- **Kokoro 82M chegou a #1 nessa arena em jan/2026** (Elo ~1056 na AA; na TTS Arena da comunidade ficou no topo), batendo modelos 10–100x maiores — referência: https://texttolab.com/blog/kokoro-tts-review e https://github.com/huggingface/blog/blob/main/arena-tts.md
- Útil como sanity check de modelos abertos; menos útil como métrica de produto.

**Implicação**: nossas decisões de qualidade não podem terceirizar para arenas. Eval humana própria (CMOS A/B com ouvintes cariocas) é obrigatória; arenas servem só para escolher baselines de comparação.

---

## 2. Benchmarks de TTS expressivo (b)

### 2.1 EmergentTTS-Eval (NeurIPS 2025 D&B) — o padrão de expressividade

- Paper: https://arxiv.org/abs/2505.23009 · Código/dados: https://github.com/boson-ai/EmergentTTS-Eval-public (**Apache-2.0**).
- 1.645 casos em 6 categorias: **Emoções, Paralinguística, Palavras estrangeiras, Sintaxe complexa, Pronúncia complexa (URLs/fórmulas), Perguntas**. Geração de casos por LLM a partir de seeds; avaliação **model-as-judge com LALM** (leaderboard oficial usa **gemini-2.5-pro**; suporta judges OpenAI) medindo win-rate contra uma baseline.
- Resultado de referência: GPT-4o-audio (voz Ballad) lidera em expressividade.
- **Inglês-cêntrico**, mas o *pipeline* (seeds → expansão por LLM → judge LALM) é diretamente replicável em pt-BR — é exatamente a receita para o nosso harness de emoções (já alinhado com a crença "base implícita + prompt de estilo").

### 2.2 Seed-TTS-eval — o padrão objetivo zero-shot

- https://github.com/BytedanceSpeech/seed-tts-eval — test sets **EN (Common Voice ~1k) e ZH (DiDiSpeech-2 ~2k)**; métricas: **WER** (whisper-large-v3 para EN, Paraformer para ZH) e **SIM** (cosseno de embeddings de um **WavLM-large fine-tuned em speaker verification**).
- Sem português, sem atualização relevante 2025–2026 (repo com ~10 commits). Continua sendo a régua que todo paper de zero-shot TTS cita (MiniMax-Speech, MaskGCT, Qwen3-TTS...).
- **Implicação**: criar um **seed-tts-eval-ptBR** é trivial em estrutura (textos CV-pt/CORAA + whisper-large-v3 + mesmo WavLM-SV) e nos dá comparabilidade metodológica com a literatura.

### 2.3 InstructTTSEval (2025) e MINT-Bench (2026) — instrução de estilo

- **InstructTTSEval**: https://arxiv.org/abs/2506.16381 — 6k casos EN+ZH em 3 níveis (Acoustic-Parameter Specification, Descriptive-Style Directive, Role-Play), judge Gemini. Conclusão: controle acústico fino continua aberto mesmo nos melhores sistemas.
- **MINT-Bench (NOVO, 2026)**: https://arxiv.org/abs/2604.17958 · página: https://longwaytog0.github.io/MINT-Bench/ — **primeiro benchmark de instruction-following TTS multilíngue com PORTUGUÊS** (10 línguas: zh, en, ja, ko, fr, de, es, **pt**, it, ru; ~12k casos; 16 sistemas). Protocolo híbrido: consistência de conteúdo + obediência à instrução + qualidade perceptual. Resultado: Gemini 2.5-Flash/Pro lideram; abertos (Qwen3-TTS, MiniMax, MOSS etc.) ficam competitivos em línguas localizadas; **controles composicionais e paralinguísticos são o gargalo**.
- **Implicação**: MINT-Bench-pt vira nosso teste externo de "emoções controláveis" — dá para rodar o subset pt contra o nosso modelo sem construir nada.

### 2.4 TTSDS2 — métrica distributiva + benchmark multilíngue contínuo

- Paper: https://arxiv.org/abs/2506.19441 · Código: https://github.com/ttsds/ttsds (**MIT**) · Leaderboard: ttsdsbenchmark.com (instável no fetch em 10/jun; o GitHub confirma "multilingual, atualizado trimestralmente").
- Única métrica (de 16 comparadas) com Spearman > 0,50 contra MOS humano **em todos os domínios**; benchmark em **14 línguas**, 20 sistemas. A lista exata de línguas não está no abstract — **verificar se pt está entre as 14 antes de adotar como métrica principal** (a seleção é "toda língua sintetizada por ≥2 sistemas", e pt é sintetizado por Qwen3-TTS, Voxtral, Fish etc., então é provável).

### 2.5 Outros 2025–2026

- **MULTI-Bench** (https://arxiv.org/pdf/2511.00850): inteligência emocional multi-turn em spoken dialogue models — ponte entre expressividade e conversação.
- WildSpoof/ICASSP 2026 (TTS in-the-wild) usa **DNSMOS OVRL como métrica primária** citando inconsistência do UTMOSv2 entre runs: https://arxiv.org/html/2605.23859 — ver §4.

---

## 3. Benchmarks full-duplex / conversacionais (c)

### 3.1 Full-Duplex-Bench — família dominante (MIT)

Repo único: https://github.com/DanielLin94144/Full-Duplex-Bench (**MIT**). Quatro gerações:

| Versão | Data | O que mede |
|---|---|---|
| v1.0 (https://arxiv.org/abs/2503.04721) | mar/2025 | Turn-taking: pause handling, backchannel, smooth turn-taking, interrupção do usuário |
| v1.5 (https://arxiv.org/abs/2507.23159) | ago/2025 | **Overlap**: interrupção vs. backchannel vs. conversa paralela vs. fala ambiente; métricas de stop/response latency e adaptação prosódica. Achado: modelos divergem entre estratégia "responsiva" e "floor-holding" |
| v2.0 (https://arxiv.org/abs/2510.07838) | out/2025–fev/2026 | **Tempo real multi-turn com examinador automático via WebRTC** (orquestrador Node.js, PCM 48 kHz/frames de 10 ms); famílias: daily, correction, entity tracking, safety; LLM-as-judge |
| v3.0 (código/dados **20/mai/2026**) | mai/2026 | **Tool use sob disfluência humana real** + chamadas de API multi-step |

**Implicação direta**: o FDB-v2 é o harness pronto para medir o nosso spine (Moshi adaptado) — latência de resposta, barge-in, backchannel — basta trocar os prompts/áudios do examinador para pt-BR. Os dados são inglês; **a infraestrutura é reaproveitável**.

### 3.2 Talking Turns (ICLR 2025)

- https://arxiv.org/abs/2503.01174 — judge supervisionado **treinado em Switchboard (inglês)** prevê eventos de turn-taking; achados: sistemas atuais não sabem quando falar, interrompem agressivamente e quase não backchannelam.
- Para pt-BR o judge precisaria ser re-treinado em conversa espontânea brasileira (candidatos de dados: CORAA/C-ORAL-BRASIL, Certas Palavras, NURC).

### 3.3 URO-Bench

- https://arxiv.org/abs/2502.17810 · https://github.com/Ruiqi-Yan/URO-Bench — primeiro benchmark S2S cobrindo **multilinguismo, multi-turn e paralinguística**; tracks basic/pro com 20 test sets cada (40 no HF; miniset de 1k). Achados: SDMs abertos vão bem em QA cotidiano mas sofrem **catastrophic forgetting** do LLM-base e são fracos em paralinguística — exatamente o risco do nosso CPT/LoRA no Moshi (reforça a decisão LoRA-first).

### 3.4 Novidades 2026

- **ICASSP 2026 HumDial Challenge — track Full-Duplex** (https://arxiv.org/abs/2604.21406): corpus **dual-channel de conversas humanas reais** (interrupções, overlap, feedback), benchmark **HumDial-FDBench** e leaderboard público. Vale minerar o corpus para padrões de backchannel (mesmo em inglês/chinês, os tempos servem de prior).
- **FD-Bench** (https://arxiv.org/abs/2507.19040): pipeline alternativo de benchmarking full-duplex.
- **PersonaPlex-7B-v1 (NVIDIA, jan/2026)** — não é benchmark, mas é o fato mais relevante da frente conversacional: full-duplex S2S **sobre a arquitetura Moshi** (dual-stream, Mimi 24 kHz, backbone Helium) com **controle de persona via prompt de texto + condicionamento de voz por áudio**. Código **MIT**, pesos **NVIDIA Open Model License**: https://huggingface.co/nvidia/personaplex-7b-v1 · https://github.com/NVIDIA/personaplex · https://research.nvidia.com/labs/adlr/personaplex/. **A NOML não está na whitelist do projeto (Apache/MIT/CC-BY/CC0)** — é commercial-friendly mas com condições próprias; antes de usar pesos, análise jurídica. Mesmo sem tocar nos pesos, o paper (https://arxiv.org/pdf/2602.06053) é a receita pública de "persona control" sobre Moshi — diretamente aplicável às 5 sub-variações cariocas.

**Gap**: nenhum benchmark full-duplex cobre pt-BR. Adaptar FDB (MIT) com áudio pt-BR é o caminho de menor atrito e é publicável.

---

## 4. Métricas automáticas em 2026 — o que usar para pt-BR (d)

### 4.1 Qualidade/naturalidade (MOS proxies)

| Métrica | Licença | Treino | Funciona em pt-BR? | Veredito 2026 |
|---|---|---|---|---|
| **UTMOS (UTMOS22)** | MIT (https://github.com/sarulab-speech/UTMOS22) | VoiceMOS 2022 (EN/ZH) | Proxy aproximado; **não calibrado**; comparações cross-língua não confiáveis | Só sanity check |
| **UTMOSv2** | MIT (https://github.com/sarulab-speech/UTMOSv2) | VoiceMOS 2024 T1 (vencedor: 1º em 7/16 métricas) | Mesma limitação EN; **relatos 2026 de inconsistência entre runs** (desvio alto p/ mesmo áudio — https://arxiv.org/html/2605.23859) | Evitar como métrica de decisão |
| **Audiobox-Aesthetics (Meta)** | Código/pesos **CC-BY-4.0** (+ partes MIT) — https://github.com/facebookresearch/audiobox-aesthetics · https://arxiv.org/abs/2502.05139 | Áudio diverso (incl. Common Voice multilíngue); 4 eixos: CE, CU, PC, **PQ** | Menos dependente de língua; bom p/ qualidade de produção | **Adotar** (PQ/CE) p/ dataset do Pedro e outputs |
| **DNSMOS (Microsoft)** | repo DNS-Challenge | P.808/P.835, foco ruído | Língua-agnóstico (qualidade, não naturalidade) | **Adotar** p/ higiene de dataset; usado como métrica primária no WildSpoof 2026 por ser estável |
| **SQuId (Google)** | paper https://arxiv.org/abs/2210.06324 | **42 línguas de treino, 65 locales de teste** (mSLAM 600M) | Único MOS-predictor genuinamente multilíngue; disponibilidade de checkpoint limitada | Citar; usar se checkpoint acessível |
| **TTSDS2** | **MIT** — https://github.com/ttsds/ttsds | Distributivo (não precisa de MOS de treino); validado em 14 línguas | **Melhor opção multilíngue 2026** (Spearman>0,5 em todos os domínios) | **Adotar como métrica principal** (confirmar pt nas 14 línguas) |

**Stack recomendado (eval automática de qualidade, pt-BR):**
1. **TTSDS2** (principal, distributiva, compara contra fala real do Pedro/CORAA);
2. **Audiobox-Aesthetics PQ/CE** (qualidade de produção);
3. **DNSMOS** (limpeza/ruído, gate de dataset);
4. UTMOS apenas como número de continuidade histórica — nunca para decidir entre checkpoints;
5. **CMOS humano A/B (ouvintes BR)** como ground truth a cada milestone — nenhuma métrica automática substitui isso em pt-BR hoje.

### 4.2 Speaker similarity (clone da voz do Pedro)

- **Padrão da área**: cosseno de embeddings do **WavLM-large fine-tuned em speaker verification** (UniSpeech-SAT/microsoft) — é o SIM do seed-tts-eval e dos reports de Qwen3-TTS/MiniMax. https://github.com/BytedanceSpeech/seed-tts-eval
- **ECAPA-TDNN** (SpeechBrain, Apache-2.0): segunda opinião sólida; nota: modelos com melhor EER (ECAPA/TitaNet) têm maior disparidade intra/inter-classe que WavLM — discussão em https://arxiv.org/html/2507.02176v1 (limitações: SIM mede timbre, não estilo/prosódia).
- **Resemblyzer**: legado (GE2E 2019); ainda aparece em papers (Fish-Speech reporta 0,914) mas **não usar como métrica primária**.
- **Recomendação**: WavLM-SV primário + ECAPA-TDNN secundário; reportar ambos. Embeddings são razoavelmente língua-agnósticos — funcionam em pt-BR.

### 4.3 WER round-trip (inteligibilidade) — qual ASR pt-BR em 2026

- **whisper-large-v3 (OpenAI, Apache-2.0)** segue sendo o ASR de referência da literatura para WER de TTS (seed-tts-eval EN; reports multilíngues). Para pt-BR continua o **default de comparabilidade**.
- **distil-whisper oficial é inglês-only** (https://github.com/huggingface/distil-whisper); para multilíngue rápido a recomendação oficial é whisper-turbo.
- **Fine-tune pt-BR**: freds0/distil-whisper-large-v3-ptbr (**MIT**, WER 8,22% no Common Voice 16-pt): https://huggingface.co/freds0/distil-whisper-large-v3-ptbr
- **NOVO (out/2025→2026): Open ASR Leaderboard ganhou track multilíngue com português** (https://huggingface.co/blog/open-asr-leaderboard · paper https://arxiv.org/abs/2510.06961 · space https://huggingface.co/spaces/hf-audio/open_asr_leaderboard):
  - **NVIDIA Parakeet-TDT-0.6B-v3** — **CC-BY-4.0**, 25 línguas, pt WER **6,16%** (média do track; 4,76% Fleurs / 7,50% MLS), RTFx ≈ **3.333**: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
  - **NVIDIA Canary-1B-v2** — **CC-BY-4.0**, 25 línguas, pt WER 6,33%: https://huggingface.co/nvidia/canary-1b-v2
  - ⚠️ **Caveat decisivo, do próprio model card**: "training data uses **European Portuguese** while most benchmarks use Brazilian Portuguese" — podem penalizar fonética carioca.
- **CAMÕES** (https://arxiv.org/abs/2508.19721) é benchmark de **pt europeu** — não usar como régua pt-BR.
- **Recomendação para o harness**: WER com **whisper-large-v3** como métrica canônica (comparável com a literatura) + **Parakeet-TDT-0.6B-v3** como segundo ASR ("ensemble WER") para detectar overfitting do TTS às manhas do Whisper. Em produção (cascata piso-de-latência), Parakeet v3 é ordens de magnitude mais rápido (RTFx 3,3k). Normalização de texto pt-BR (números, siglas) precisa ser fixada no harness — é onde WER pt mais varia.

### 4.4 SER (emoção) para pt-BR

- **emotion2vec** (código/modelos **MIT**: https://github.com/ddlBoJack/emotion2vec): a literatura cross-lingual (paper ACL Findings 2024 + estudos posteriores, ex. https://arxiv.org/pdf/2406.07162 EmoBox) mostra que **funciona bem em línguas indo-europeias, incluindo português** (avaliado em 9 corpora incl. pt; degrada forte só fora da família, ex. quéchua). Os modelos **emotion2vec+ (seed/base/large)** dão 9 classes (angry, disgusted, fearful, happy, neutral, other, sad, surprised, unknown) — línguas de treino não documentadas.
- **Datasets pt-BR**: **VERBO** (atuado, https://github.com/jrtorresneto/VERBO-emotional-speech-dataset), **CORAA SER v1.0** (~50 min, espontâneo, neutro/não-neutro: https://github.com/rmarcacini/ser-coraa-pt-br), modelo pronto wav2vec2-XLS-R pt-BR spontaneous SER: https://huggingface.co/alefiury/wav2vec2-xls-r-300m-pt-br-spontaneous-speech-emotion-recognition
- **Realidade em jun/2026: não existe SER pt-BR robusto off-the-shelf.** Caminho: **emotion2vec+ large como extrator congelado + cabeça linear fine-tuned em VERBO + CORAA SER + subset emotado da gravação do Pedro** (as takes dirigidas com rótulo de emoção viram, de graça, o conjunto de treino/teste do nosso próprio SER). Usar EmoBox como toolkit. Para o harness de "emoções controláveis": acurácia do SER no áudio gerado + judge LALM (estilo EmergentTTS/MINT) com rubrica em pt-BR.

---

## 5. Benchmarks/recursos TTS pt-BR publicados 2025–2026 (e)

### PROPOR 2026 (Salvador, abr/2026) — colheita relevante

| Recurso | O que é | Por que importa |
|---|---|---|
| **Certas Palavras** (https://aclanthology.org/2026.propor-1.81/) | 70 h de diálogos espontâneos multi-speaker de rádio BR (anos 80–90); baselines **YourTTS e F5-TTS** treinados em subset de 9 h; WER/CER moderados, MOS claramente abaixo do ground truth | Primeiro test bed pt-BR de TTS em fala **espontânea/ruidosa/dialógica** — o regime exato do nosso produto. Reusar como conjunto de comparação e para minerar padrões conversacionais |
| **BIPA** (https://aclanthology.org/2026.propor-1.47/) | **53.353 palavras, 350.021 transcrições IPA**, 6 variedades dialetais incluindo **Rio de Janeiro**; **CC-BY-4.0** | Ouro para o front-end: G2P carioca, test set de pronúncia regional (chiamento /s/→[ʃ], vocalização etc.), e métrica de "sotaque correto" via comparação fonética |
| **GARAGEM** (https://aclanthology.org/2026.propor-1.83/) | ASR adaptado com fala sintética em pt-BR (domínio automotivo) | Valida a alça "TTS sintético → melhora ASR" em pt-BR (relevante p/ bootstrap de dados) |
| **ProsSegue-ML** (https://aclanthology.org/2026.propor-2.24/) | Ferramenta livre de segmentação prosódica pt-BR | Útil p/ anotar prosódia do dataset do Pedro |

### Fora do PROPOR

- **Tagarela** (https://arxiv.org/abs/2603.15326): **8.972 h de podcasts em português**, pipeline de pré-processamento + transcrição mista (ASR próprios + APIs), **CC-BY-4.0**, feito para treinar **ASR e TTS** (escala GigaSpeech). Autores incluem Frederico Oliveira e **Edresson Casanova** (autor do TTS-Portuguese Corpus/YourTTS). Candidato imediato a: (i) corpus de pré-treino/CPT de fala pt-BR, (ii) fonte de textos+áudios para um seed-tts-eval-ptBR.
- **MuPe Life Stories** (COLING 2025): fala espontânea pt-BR com estudo de viés de ASR — útil para test sets de robustez.
- **CORAA v1** (290 h validadas, https://arxiv.org/pdf/2110.15731) e **TTS-Portuguese Corpus** (10,5 h, single-speaker) seguem sendo as bases históricas.

### Conclusão (e): existe benchmark de TTS pt-BR?

**Não existe leaderboard/benchmark padronizado de TTS pt-BR** estilo Seed-TTS-eval/TTSDS2 em jun/2026. O mais próximo é Certas Palavras (test bed de corpus + 2 baselines). **Oportunidade clara**: publicar o "**ptBR-TTS-eval**" do projeto — textos de CV-pt/CORAA/Tagarela + WER (whisper-large-v3 + Parakeet-v3) + SIM (WavLM-SV) + TTSDS2-pt + judge LALM com rubrica pt-BR + teste de pronúncia dialetal via BIPA. Publicável em PROPOR 2027 / Interspeech 2027 e vira fosso reputacional.

---

## 6. Desenho do eval harness do projeto (síntese acionável)

**Camada 0 — dataset (gate de gravação):** DNSMOS OVRL + Audiobox-Aesthetics PQ por take; rejeitar abaixo de limiar.

**Camada 1 — regressão automática (toda run de treino):**
- WER round-trip: whisper-large-v3 (canônico) + Parakeet-TDT-0.6B-v3 (controle), textos fixos pt-BR (CV-pt + frases BIPA-dialetais);
- SIM: WavLM-large-SV (primário) + ECAPA-TDNN (secundário) vs. enrollment do Pedro;
- TTSDS2 contra fala real do Pedro;
- SER: emotion2vec+ fine-tuned (VERBO+CORAA SER+takes do Pedro) — acurácia de emoção pedida vs. detectada.

**Camada 2 — expressividade/instrução (semanal):** subset pt do **MINT-Bench** + port pt-BR do pipeline EmergentTTS-Eval (judge gemini-2.5-pro ou LALM aberto), win-rate vs. checkpoint anterior.

**Camada 3 — conversacional/full-duplex (por milestone):** Full-Duplex-Bench v1.5 (overlap/backchannel/latência de stop) e FDB-v2 (examiner WebRTC) com áudios de examinador em pt-BR; metas: stop latency e response latency p50 < 800 ms (ideal 200–300 ms), taxa de backchannel não-nula, sem floor-holding patológico.

**Camada 4 — humano (gate de release):** CMOS A/B com ouvintes BR (cego, ≥30 ouvintes), MUSHRA leve para sotaque ("soa carioca de onde?"), e conversa livre de 5 min estilo arena interna.

---

## Fontes principais

- Artificial Analysis Speech Arena: https://artificialanalysis.ai/text-to-speech/arena · artigo Fun-Realtime-TTS: https://artificialanalysis.ai/articles/fun-realtime-tts-new-text-to-speech-model-topping-artificial-analysis-leaderboard · snapshot aberto: https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/
- TTS Arena V2: https://tts-agi-tts-arena-v2.hf.space/leaderboard · https://github.com/huggingface/blog/blob/main/arena-tts.md
- EmergentTTS-Eval: https://arxiv.org/abs/2505.23009 · https://github.com/boson-ai/EmergentTTS-Eval-public
- Seed-TTS-eval: https://github.com/BytedanceSpeech/seed-tts-eval
- InstructTTSEval: https://arxiv.org/abs/2506.16381 · MINT-Bench: https://arxiv.org/abs/2604.17958 · https://longwaytog0.github.io/MINT-Bench/
- TTSDS2: https://arxiv.org/abs/2506.19441 · https://github.com/ttsds/ttsds
- Full-Duplex-Bench: https://github.com/DanielLin94144/Full-Duplex-Bench · v1: https://arxiv.org/abs/2503.04721 · v1.5: https://arxiv.org/abs/2507.23159 · v2: https://arxiv.org/abs/2510.07838 · HumDial ICASSP 2026: https://arxiv.org/abs/2604.21406 · FD-Bench: https://arxiv.org/abs/2507.19040
- Talking Turns: https://arxiv.org/abs/2503.01174 · URO-Bench: https://arxiv.org/abs/2502.17810
- PersonaPlex: https://huggingface.co/nvidia/personaplex-7b-v1 · https://github.com/NVIDIA/personaplex · https://arxiv.org/pdf/2602.06053
- Métricas: UTMOS https://github.com/sarulab-speech/UTMOS22 · UTMOSv2 https://github.com/sarulab-speech/UTMOSv2 · Audiobox-Aesthetics https://github.com/facebookresearch/audiobox-aesthetics · SQuId https://arxiv.org/abs/2210.06324 · inconsistência UTMOSv2/uso DNSMOS: https://arxiv.org/html/2605.23859 · speaker-sim: https://arxiv.org/html/2507.02176v1
- ASR: Open ASR Leaderboard https://huggingface.co/blog/open-asr-leaderboard · https://arxiv.org/abs/2510.06961 · Parakeet v3 https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 · Canary 1B v2 https://huggingface.co/nvidia/canary-1b-v2 · distil-whisper https://github.com/huggingface/distil-whisper · pt-BR fine-tune https://huggingface.co/freds0/distil-whisper-large-v3-ptbr · CAMÕES (pt-PT) https://arxiv.org/abs/2508.19721
- SER: emotion2vec https://github.com/ddlBoJack/emotion2vec · EmoBox https://arxiv.org/pdf/2406.07162 · CORAA SER https://github.com/rmarcacini/ser-coraa-pt-br · VERBO https://github.com/jrtorresneto/VERBO-emotional-speech-dataset · modelo pt-BR https://huggingface.co/alefiury/wav2vec2-xls-r-300m-pt-br-spontaneous-speech-emotion-recognition
- pt-BR 2025–2026: Certas Palavras https://aclanthology.org/2026.propor-1.81/ · BIPA https://aclanthology.org/2026.propor-1.47/ · GARAGEM https://aclanthology.org/2026.propor-1.83/ · ProsSegue-ML https://aclanthology.org/2026.propor-2.24/ · Tagarela https://arxiv.org/abs/2603.15326 · CORAA https://arxiv.org/pdf/2110.15731
- Modelos citados: Qwen3-TTS https://github.com/QwenLM/Qwen3-TTS · https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base · Voxtral TTS https://mistral.ai/news/voxtral-tts/ · https://huggingface.co/mistralai/Voxtral-4B-TTS-2603 · Maya1 https://huggingface.co/maya-research/maya1 · Fun-Audio-Chat https://github.com/FunAudioLLM/Fun-Audio-Chat
