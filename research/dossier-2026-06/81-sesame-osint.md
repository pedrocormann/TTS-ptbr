# 81 — OSINT Sesame, rodada 1 (Trilha M: engenharia reversa da Maya)

**Data da coleta:** 2026-06-10 · **Método:** web search + fetch de fontes primárias
(sesame.com, github.com/SesameAILabs, api Ashby de vagas, HF, imprensa).
**Regra de confiança:** [P] = fonte primária · [S] = secundária confiável ·
[F] = fonte fraca (agregador de perfis/imprensa não-técnica — usar com cautela).

---

## 1. Pessoas

### 1.1 Autores do post "Crossing the Uncanny Valley of Voice" (27/fev/2025) [P]

Créditos exatos no post (https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice):
**Johan Schalkwyk, Ankit Kumar, Dan Lyth, Sefik Emre Eskimez, Zack Hodari,
Cinjon Resnick, Ramon Sanabria, Raven Jiang.** Sem seção formal de
acknowledgments. O índice em sesame.com/research credita "Brendan Iribe,
Ankit Kumar, and the Sesame team". O README do repo `csm` credita "Johan
Schalkwyk, Ankit Kumar, Dan Lyth, and the Sesame team" [P].
**Não existe paper formal (arXiv) do CSM** — só o blog post. Buscas no arXiv
por afiliação "Sesame" não retornaram nada (verificado 2026-06-10).

### 1.2 Quem é quem — histórico pré-Sesame (de onde veio a técnica)

| Nome | Papel na Sesame | Antes da Sesame | Linha de pesquisa que trouxe |
|---|---|---|---|
| **Brendan Iribe** | Co-founder/CEO | Co-founder/CEO Oculus (vendida à Meta por $2B) | Produto/hardware; não é autor técnico |
| **Ankit Kumar** (`apkumar` no GitHub) | Co-founder/CTO | MetaMind (researcher, era Socher — Dynamic Memory Networks), Pilot AI (chief scientist), co-founder Ubiquity6 (2017-21, adquirida pela Discord), liderou eng do Clyde AI na Discord (2021-23). Stanford math '15 | NLP/agents/LLM; commitou no fork sglang (tokenizer_manager.py) |
| **Ryan Brown** | Founding engineer | Oculus (2013-19), Meta Reality Labs Research Engineering (2019-23) | Hardware/sistemas |
| **Johan Schalkwyk** | ML lead — **SAIU jun/2025 → Meta Superintelligence Labs** | Google Fellow/VP, liderou Google voice search ~duas décadas | ASR/speech em escala Google |
| **Dan Lyth** | Research (speech generation) | Stability AI; autor do **Parler-TTS** ("Natural language guidance of high-fidelity TTS with synthetic annotations", com Simon King/Edinburgh) | Controle de estilo por descrição textual + anotação sintética de dados |
| **Sefik Emre Eskimez** | Research | Microsoft Research; autor de **E2-TTS** (flow-matching não-autoregressivo) e **EmoCtrl-TTS** (emoção zero-shot c/ vocalizações não-verbais) | Naturalidade/emoção, linha MSR |
| **Zack Hodari** | Research | PhD Edinburgh/CSTR em **prosódia contextual** (tese "Prosody generation for TTS"); Papercup (dublagem) | Prosódia dependente de contexto — o coração do pitch da Maya |
| **Cinjon Resnick** (`cinjon`) | Research scientist | PhD NYU (Cho/Bruna); Google Brain (**NSynth**, audio synthesis — patenteado pelo Google), FAIR, NVIDIA, Quora | Síntese de áudio neural + serving (o fork sglang da org vem do fork pessoal dele) |
| **Ramon Sanabria** | Research engineer | PhD Edinburgh, MSc CMU; estágios **Google DeepMind**, Facebook AI, Google | ASR multi-sotaque, acoustic word embeddings — *diretamente relevante à nossa tese de sotaque* |
| **Raven Jiang** | Research engineer | Tesla, Facebook, co-founder Arc, Ubiquity6; Stanford BS+MBA | Engenharia/produto |

Outros nomes confirmados via forks/perfis [S/F]:
- **Wael Abid** — engineer (NY); Stanford MS CS; ex-Predibase, Apple, InstaDeep.
  Fez o sync do fork `moshi` (ago/2025).
- **Neal Manaktola** (`nealmanaktola`) — lidera eng de ML; ex-Discord senior
  SWE, ex-Ubiquity6 (rede do Ankit). Commits no fork sglang (mai/2025).
- **Nate Mitchell** — co-founder da Oculus, CPO desde jun/2025 (roadtovr.com).
- **Angela Gayles** — exec, ex-Facebook/Meta. **Hans Hartmann** — COO,
  ex-Oculus COO/Fitbit (TechCrunch).
- Time: ~61 funcionários (Contrary Research); SF + Bellevue + NY (sesame.com/team).

**Leitura:** a técnica da Sesame é uma fusão de quatro escolas — Google speech
(Schalkwyk, saiu), Microsoft Research TTS (Eskimez), Stability/HF TTS-com-
descrição (Lyth) e Edinburgh CSTR prosódia/sotaque (Hodari, Sanabria; Simon
King é co-autor do Parler-TTS). A base de tokenização (Mimi/RVQ) veio da
Kyutai (Moshi). A rede Ubiquity6→Discord (Kumar, Manaktola, Jiang) é o núcleo
de engenharia.

### 1.3 Saídas e publicações de ex-funcionários (2025-2026)

- **Johan Schalkwyk → Meta Superintelligence Labs (jun/2025)** — Bloomberg
  (2025-06-11) e réplicas (Business Standard, Japan Times). Zuckerberg o
  contratou para voz/personalização do Llama. **Não encontrei paper público
  dele na Meta (2025-26) que exponha a linha Sesame** — vigiar (qualquer
  paper Meta de voz full-duplex/expressiva com o nome dele é sinal direto).
- Nenhum outro ex-Sesame com publicação reveladora localizado nesta rodada.
  O ecossistema full-duplex 2025-26 no arXiv (PersonaPlex 2602.06053,
  F-Actor 2601.11329, DuplexSLA 2605.20755, Full-Duplex-Bench 2507.23159)
  **não tem afiliação Sesame** — eles continuam sem publicar.

---

## 2. GitHub org SesameAILabs — todos os repos (13, verificado 2026-06-10) [P]

| Repo | Fork de | Últ. atividade | O que tocaram / papel inferido no stack |
|---|---|---|---|
| **csm** | original | 27/mai/2025 · ~15k★ | Release público CSM-1B (Apache-2.0). Inclui `watermarking.py` → usa silentcipher. Llama backbone + decoder Mimi |
| **torchtune** | meta-pytorch/torchtune | push dez/2025 (main sem commits set-dez/25 — provável sync/branch privado) | **Post-training/finetune** (LoRA, RLHF/DPO). Fork mais recentemente tocado da org |
| **moshi** | kyutai-labs/moshi | ago/2025 (sync por wael-abid) | **Estudo de full-duplex** (Kyutai). Sem commits próprios visíveis — espelho de acompanhamento. Sinal de interesse em duplex real |
| **ClearerVoice-Studio** | modelscope/ClearerVoice-Studio | ago/2025 | Enhancement/separação/super-resolução de fala → **pipeline de limpeza do 1M h de áudio** |
| **sglang** | **cinjon/sglang** (fork pessoal do Resnick) → sgl-project | mai/2025 | **ÚNICO fork com commits próprios confirmados:** "Add logit bias into main" (cinjon, 29/jan/25), "Clamp the logit outputs so we dont run into json errors" (cinjon, 18/fev/25), patch `tokenizer_manager.py` (apkumar, 5/fev/25), pyproject (nealmanaktola, mai/25). → **Serving do LLM em produção com controle fino de decodificação** (logit bias = tokens de controle/JSON p/ tools) |
| **ultralytics** | ultralytics/ultralytics (AGPL!) | mai/2025 | YOLO11 — **visão para os óculos** (eyewear 2027). Sem mods visíveis |
| **torchtitan** | pytorch/torchtitan | mai/2025 | **Pretraining em escala** (clusters grandes citados em sesame.com/team) |
| **silentcipher** | sony/silentcipher | mar/2025 | **Watermarking de áudio** (40-bit, psychoacoustic) — usado no csm |
| **faster-whisper-plus** | SYSTRAN/faster-whisper | mar/2025 · 50★ | **ASR streaming/batched**. Commits visíveis são todos de mantenedores upstream (MahmoudAshraf97, Purfview) até v1.1.1 — o "plus" não tem diff público claro nesta rodada (checar compare na rodada 2) |
| **wavtools** | keithwhor/wavtools (ex-OpenAI Realtime Console, MIT) | jan/2025 | **Captura/streaming PCM16 no browser** — o front do research preview web |
| **whisperX** | m-bain/whisperX | out/2024 | **Alinhamento word-level + diarização** → rotulagem do dataset de 1M h |
| **silero-vad** | snakers4/silero-vad | jun/2024 | **VAD** — fork mais antigo da org: turn-taking foi a 1ª peça do stack |
| **gpt-fast** | meta-pytorch/gpt-fast | abr/2024 | Inferência LLM rápida — experimentos da era pré-sglang (early 2024) |

**Leitura do stack pela cronologia dos forks:** 2024 = VAD + ASR + inferência
(cascata primeiro); jan-mai/2025 = serving sglang + watermark + release CSM;
mai-ago/2025 = visão (óculos), treino em escala, limpeza de dados, moshi
(duplex); dez/2025 = post-training (torchtune). Nenhum branch público além de
`main` em nenhum fork.

---

## 3. Vagas e patentes

### 3.1 Vagas (jobs.ashbyhq.com/sesame via API pública, 2026-06-10) [P]

10 vagas, todas SF (NY/Bellevue secundárias): iOS Engineer, Embedded Engineer,
Research Scientist, Backend Engineer, Electrical Engineer, Product Designer,
Embedded OS Architect, **ML Model Serving Engineer**, PM Hardware, Dev Infra.

Stack revelado pelas descrições:
- **ML Model Serving: PyTorch, vLLM, SGLang, Kubernetes, GCP** ← confirma o
  fork sglang como produção, não experimento.
- Backend: Python, WebSockets/gRPC/REST, K8s, **GCP** (não AWS).
- iOS: **WebRTC**, codecs de áudio/vídeo, **BLE** (óculos), Metal, bateria.
- Research Scientist: NLP, speech recognition **e Computer Vision** ← multimodal/óculos.
- 4 de 10 vagas são de hardware (Embedded, EE, Embedded OS, PM HW) ← o centro
  de gravidade de contratação é o eyewear.

### 3.2 Patentes

**Nada encontrado** sob "Sesame AI Inc" no Google Patents/USPTO até 2026-06-10
(buscas diretas não retornaram nenhum pedido; possível nome legal distinto ou
pedidos ainda não publicados — pedidos levam 18 meses para publicar). Iribe tem
patentes da era Oculus (atribuídas a Oculus/Meta); Resnick tem patente do NSynth
(Google). **Conclusão: a vantagem deles não está protegida por patente visível —
está em dados (1M h), engenharia e velocidade.**

---

## 4. Comportamento do produto (app iOS, lançado 28/mai/2026)

Fontes: TechCrunch 2026-05-28 [S], PCWorld [S], testingcatalog.com [S],
sesame.com/blog "Voice your curiosity" 27/mai/2026 [P].

- **4 agentes** (Maya, Miles, Simone, Charlie), voz/persona/memória próprias;
  39 países, grátis (preview), waitlist; Android depois; eyewear em 2027.
- **Memória entre sessões** + **modo incógnito** (sem gravar memória) +
  **Notes** (resumo de takeaways) + **text mode** + localização (recomendações
  locais).
- **Busca ao vivo DURANTE a fala**: "multiple parallel searches while
  speaking", com cards visuais, e o agente "muda de rumo no meio da frase"
  quando resultados chegam → **tool-use assíncrono entrelaçado com geração
  incremental de fala** (não é pipeline linear por turno).
- **PCWorld**: disfluências deliberadas ("ums/ahs"), fala "composta on-the-fly,
  que meandra, pivota e até se contradiz" (≠ ler texto pronto); afirma que o
  sistema combina **"Gemma 4 LLM + CSM-1B"** ← claim de jornalista, tratar com
  cautela, mas coerente com o research preview que usava **Gemma-27B**
  (the-decoder.com, mar/2025).
- Latência: sem números publicados pós-launch; era ~200-300 ms no preview
  (Contrary Research). Sesame fala em "low-latency e fluxo conversacional".
- Funding: Seed $10,1M (set/2023) → Series A $47,5M a16z (fev/2025) →
  **Series B $250M Sequoia+Spark (anunciada TechCrunch 21/out/2025**, junto com
  beta dos óculos); total ~$307M; valuation >$1B (Contrary, TIMEWELL).

---

## 5. Síntese — refinando a "hipótese arquitetural Maya v0" do REPLAN

Hipótese do REPLAN: *cascata rápida e engenheirada — VAD/turn-engine → ASR
streaming → LLM persona (backstage) → CSM condicionado no áudio da conversa →
playback duplex-aparente.*

### Confirmado pelas evidências desta rodada
1. **É cascata engenheirada, sim.** A própria cronologia dos forks é a cascata:
   silero-vad (VAD) → faster-whisper/whisperX (ASR) → sglang/gpt-fast (LLM
   serving) → CSM (fala). As vagas confirmam serving vLLM/SGLang + WebSockets/
   WebRTC + GCP em produção.
2. **LLM backstage = família Gemma** (27B no preview [the-decoder]; "Gemma 4"
   no app segundo PCWorld). Os commits de **logit bias + clamp anti-erro-JSON
   no sglang** são a digital de um LLM controlado por tokens de
   formatação/ferramentas alimentando o TTS.
3. **CSM condicionado no áudio-contexto** confirmado na fonte primária: janela
   de 2048 tokens ≈ **2 minutos de áudio** interleaved texto+áudio, Mimi
   12.5 Hz, backbone+decoder em dois estágios, decoder treinado em 1/16 dos
   frames (amortização). Tamanhos: Tiny 1B+100M, Small 3B+250M, Medium 8B+300M.
4. **Watermark em produção** (silentcipher) — detalhe que o REPLAN não tinha.

### Refinamentos (novo nesta rodada)
5. **O turn-engine é mais que barge-in:** a busca paralela durante a fala exige
   um orquestrador que injete resultados no contexto **enquanto o CSM já está
   falando** e re-planeje a frase. As "disfluências e meandros" que o PCWorld
   descreve são o som desse re-planejamento incremental — e são engenharia de
   UX tanto quanto modelo. Para o Maya-BR v0: nossa ponte precisa de um laço
   de re-síntese incremental (chunk a chunk), não TTS por turno completo.
6. **Interesse deles em full-duplex real existe** (fork moshi sincronizado
   ago/2025), mas não há evidência de que o app de 2026 seja duplex nativo —
   o comportamento descrito continua compatível com duplex-aparente.
7. **A equipe de fala revela a receita de dados:** Lyth (Parler-TTS) = anotação
   sintética de estilo em escala; Eskimez (EmoCtrl) = emoção controlável;
   Hodari = prosódia contextual; Sanabria = multi-sotaque. Provável: 1M h
   filtradas + rótulos sintéticos de estilo/emoção → é exatamente a direção do
   nosso pipeline pt-BR (tags de emoção, sotaque carioca como eixo).

### O que as evidências NÃO confirmam (refutações/incertezas)
- **"CSM-Medium em produção" segue sem prova.** A única afirmação pública
  (PCWorld) diz **CSM-1B** no app — pode ser imprecisão do jornalista, mas a
  hipótese do REPLAN ("CSM-Medium") deve ser rebaixada para "CSM-?B,
  possivelmente 1B-8B; o diferencial está mais no orquestrador+dados do que no
  tamanho".
- Sem paper, sem patente, sem pesos novos na HF (só csm-1b, atualizado
  dez/2025) — não há "modelo mágico" escondido documentável.

### Lacunas para a rodada 2 (entram no VIGIL-LOG)
1. `compare` real dos forks (faster-whisper-plus vs upstream; o push dez/2025
   no torchtune) — exige API/clone fora do sandbox.
2. Qual ASR roda em produção (whisper? próprio?) e onde roda o VAD
   (cliente iOS vs servidor) — sniffing de tráfego do app (WebRTC?) é o caminho.
3. O "curiosity engine" (prompting? RL? — vaga de Research Scientist não cita RL).
4. Vigiar: papers Meta com Schalkwyk; novas saídas de funcionários; vagas novas;
   release Android; HF sesame; qualquer CSM-2.

---

## Fontes primárias e secundárias

- https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice [P]
- https://www.sesame.com/research · https://www.sesame.com/blog · https://www.sesame.com/team [P]
- https://github.com/orgs/SesameAILabs/repositories (+ páginas e /commits de cada fork) [P]
- https://github.com/SesameAILabs/csm · https://huggingface.co/sesame/csm-1b · https://huggingface.co/sesame [P]
- https://api.ashbyhq.com/posting-api/job-board/sesame (vagas) [P]
- https://www.bloomberg.com/news/articles/2025-06-11/meta-hires-top-researchers-from-google-sesame-for-new-ai-lab [S]
  (réplicas: business-standard.com, japantimes.co.jp)
- https://techcrunch.com/2026/05/28/sesame-the-conversational-ai-startup-from-oculus-founders-launches-its-ios-app/ [S]
- https://techcrunch.com/2025/10/21/sesame-the-conversational-ai-startup-from-oculus-founders-raises-250m-and-launches-beta/ [S]
- https://www.pcworld.com/article/3151873/sesame-ai-voice-app-is-the-best-ive-tested-thats-what-worries-me.html [S]
- https://www.testingcatalog.com/sesame-debutes-ios-app-in-preview-with-personal-voice-agents/ [S]
- https://research.contrary.com/company/sesame-ai [S]
- https://the-decoder.com/sesame-releases-csm-1b-ai-voice-generator-as-open-source/ [S]
- https://www.roadtovr.com/ex-oculus-execs-sesame-smart-glasses-nate-mitchell/ [S]
- https://timewell.jp/en/columns/sesame-ai [F]
- arXiv 2406.18009 (E2-TTS, Eskimez); Parler-TTS (Lyth & King, huggingface/parler-tts);
  era.ed.ac.uk/handle/1842/36396 (tese Hodari); scholar (Sanabria, Resnick) [P/S]
- Perfis LinkedIn/RocketReach/ZoomInfo de Kumar, Lyth, Hodari, Sanabria,
  Resnick, Jiang, Abid, Manaktola [F]
