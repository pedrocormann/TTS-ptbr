# FRENTE 2 — Ecossistema Kyutai (estado em 2026-06-10)

> Dossiê de pesquisa para o projeto TTS-ptbr. Baseline de crenças: 2026-05-17.
> Tudo abaixo foi verificado na web em 2026-06-10 com URLs primárias (HF model cards, GitHub, arXiv, blog oficial). Onde a fonte é secundária ou inferida, está marcado.

---

## TL;DR — o que mudou desde 2026-05-17

1. **HOJE (2026-06-10) a Kyutai lançou o RL de interatividade que o projeto planejava fazer**: `kyutai/moshika-rl-seamless` (CC-BY-4.0) e `kyutai/personaplex-rl-seamless` — Moshi e PersonaPlex pós-treinados com **GRPO + recompensas por eixo (pausa, turn-taking, backchannel, interrupção) + LLM-judge**, sobre o corpus Seamless Interaction (~4.000h, Meta). Paper: arXiv 2606.11167. A receita do "RL paralinguístico leve" agora existe pronta, da própria Kyutai, sobre o nosso spine.
2. **NVIDIA entrou no jogo Moshi**: PersonaPlex-7B-v1 (jan/2026) é um full-duplex construído **sobre os pesos do Moshika**, com **controle de persona por prompt de texto + condicionamento de voz por prompt de áudio**, turn-taking de 170ms. Código MIT, pesos NVIDIA Open Model License (comercial OK, mas **fora da whitelist de licenças do projeto**). Inglês apenas, sem código de treino.
3. **Kyutai TTS agora fala português**: o **Pocket TTS** (jan/2026, 100M, CPU em tempo real, clonagem de voz local a partir de qualquer wav) ganhou modelos **portugueses dedicados em abr–mai/2026** (6 camadas distilled + 24 camadas undistilled). Pesos CC-BY-4.0, código MIT. Falta confirmar por escuta se o sotaque é pt-BR ou pt-PT.
4. **Hibiki-Zero (fev/2026)**: tradução simultânea fala→fala {fr,es,**pt**,de}→en, 3B, treinada com **GRPO sem dados alinhados**; adaptável a nova língua de entrada com **<1000h**. Mas pesos **CC-BY-NC-SA 4.0 → vetado no produto**. Valor: a receita, não os pesos.
5. **Não existe "Moshi 2" nem Helium novo**. O roadmap implícito da Kyutai em 2026 é: pós-treino de interatividade (RL), RAG full-duplex (MoshiRAG), TTS minúsculo multilíngue (Pocket), visão (CASA) e física (lab KE:SAI). Moshi continua inglês-only no spine oficial.
6. **Cascata subiu de patamar, mas continua piso**: Unmute em produção roda com TTS ~450ms (componente) e resposta total <1s; a própria Kyutai agora ataca o que falta na cascata (interatividade) com RL **no modelo full-duplex**, ou seja: a fronteira de naturalidade continua no speech-native.

---

## Linha do tempo Kyutai (2024 → jun/2026)

| Data | Release | Relevância |
|---|---|---|
| 2024-07-03 | Moshi (demo) | spine full-duplex |
| 2024-09-18 | Moshi open-source (Moshiko/Moshika, Mimi) | pesos CC-BY-4.0 |
| 2025-01-13 | Helium-1 preview (2B) | LLM multilíngue de bolso |
| 2025-03-21 | MoshiVis | Moshi + imagens, CC-BY-4.0 |
| 2025-04-30 | Helium 1 final (2B, CC-BY-SA-4.0) | sem sucessor até hoje |
| 2025-05-22 | Unmute (cascata STT→LLM→TTS) | MIT |
| 2025-06-19 | Kyutai STT open-source (1B en/fr, 2.6B en) | CC-BY-4.0 |
| 2025-07-03 | Kyutai TTS 1.6B (en/fr) + Unmute open-source | CC-BY-4.0 |
| 2025-09 | Paper DSM (arXiv 2509.08753) | framework seq2seq streaming |
| 2026-01-13 | **Pocket TTS** (100M, CPU, clonagem) | MIT código / CC-BY-4.0 pesos |
| 2026-01-15 | **NVIDIA PersonaPlex-7B-v1** (sobre Moshika) | persona + voz por prompt |
| 2026-02-12 | **Hibiki-Zero** (3B, GRPO, {fr,es,pt,de}→en) | CC-BY-NC-SA (vetado) |
| 2026-02 | Voice Donation encerra: 228 vozes CC0 | banco de vozes limpo |
| 2026-04-21→05-04 | **Pocket TTS multilíngue** (en,fr,de,es,**pt**,it) | pt 6L + pt 24L |
| 2026-04-30 | **MoshiRAG** (retrieval assíncrono em full-duplex) | CC-BY-4.0 |
| 2026-05-26 | Kairos (temporalidade de dados em LLM) | pesquisa, não produto |
| 2026-06-10 | **RL de interatividade**: moshika-rl-seamless + personaplex-rl-seamless (arXiv 2606.11167) | **muda nosso plano de pós-treino** |

Fontes: [kyutai.org/blog](https://kyutai.org/blog), [HF kyutai](https://huggingface.co/kyutai).

---

## (a) Inventário por projeto

### 1. Moshi (spine) + moshi-finetune + MoshiRAG + **moshika-rl-seamless**

| Item | Estado (jun/2026) |
|---|---|
| Pesos | `kyutai/moshiko-/moshika-pytorch-bf16` — **CC-BY-4.0**, não gated ([HF](https://huggingface.co/kyutai/moshika-pytorch-bf16)) |
| Código | [kyutai-labs/moshi](https://github.com/kyutai-labs/moshi) — Python MIT / Rust Apache-2.0 |
| Línguas | **Inglês apenas** (oficial). Adaptações de comunidade: japonês (J-Moshi NC, LLM-jp-Moshi Apache-2.0) |
| Latência | ~200ms teórica (frame 80ms, Mimi 12.5Hz); prática 160–200ms em GPU local |
| Treino/finetune | [kyutai-labs/moshi-finetune](https://github.com/kyutai-labs/moshi-finetune) — **Apache-2.0, LoRA e full-FT**, dados = wav estéreo + JSON com timestamps (script `annotate.py` incluído). LoRA 1×H100 ≈ 39,6GB → **não cabe em A100-40GB do Colab sem cortar `duration_sec`/batch (apertado, mas é o caso de teste para GH200-96GB)** |
| Clonagem/vozes | Moshi tem voz fixa (Moshika/Moshiko). Condicionamento de voz via arquitetura existe na variante PersonaPlex (abaixo) |
| Novidades 2026 | **`kyutai/moshika-rag-pytorch-bf16`** (abr/2026, CC-BY-4.0): retrieval assíncrono durante a conversa ([blog MoshiRAG](https://kyutai.org/blog/2026-04-30-moshi-rag)). **`kyutai/moshika-rl-seamless`** (hoje, CC-BY-4.0, gated auto-aprovação): ver §(d) |

### 2. Kyutai TTS 1.6B (delayed-streams-modeling)

| Item | Estado |
|---|---|
| Pesos | `kyutai/tts-1.6b-en_fr` — **CC-BY-4.0**, não gated ([HF](https://huggingface.co/kyutai/tts-1.6b-en_fr)) |
| Código | [kyutai-labs/delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling) — Python MIT / Rust Apache-2.0; PyTorch, Rust (produção), MLX |
| Línguas | **EN + FR somente** (nada de pt no 1.6B) |
| Latência | **220ms** do 1º token de texto ao 1º chunk de áudio; serve 32 usuários a 350ms num único L40S ([X Kyutai](https://x.com/kyutai_labs/status/1940767331921416302)); delay interno texto→áudio do DSM = 1,28s (16 frames) |
| Treino/finetune | **NÃO liberado.** Pedido aberto desde 2025 ([issue #64](https://github.com/kyutai-labs/delayed-streams-modeling/issues/64), "discutindo internamente", sem entrega até hoje) |
| Clonagem | **Ainda fechada para o 1.6B**: vozes só via embeddings pré-computados no repo [kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices) (**não gated**). O script `tts_make_voice.py` existe no repo moshi, mas o encoder `mimi_voice.safetensors` do 1.6B **não é público** ([issue #404](https://github.com/kyutai-labs/moshi/issues/404)) |
| Licenças das vozes | Mistas, por pasta: voice-donations e voice-zero = **CC0**; VCTK, CML-TTS, Alba MacKenna = **CC-BY-4.0**; **Expresso e EARS = CC-NC (vetadas no produto)** ([README tts-voices](https://huggingface.co/kyutai/tts-voices/blob/main/README.md)) |

### 3. **Pocket TTS** (novo, o achado da frente)

| Item | Estado |
|---|---|
| O que é | TTS 100M parâmetros que roda **em CPU em tempo real** (~200ms para 1º chunk; ~6× tempo real em 2 cores de um MacBook Air M4) ([GitHub](https://github.com/kyutai-labs/pocket-tts), [docs](https://kyutai-labs.github.io/pocket-tts/)) |
| Datas | v1.0 em 2026-01-13; **v2.0 (2026-04-21) adicionou fr, de, es, pt, it**; v2.1 (2026-05-04) vozes default por língua + quantização (~+30% perf) ([releases](https://github.com/kyutai-labs/pocket-tts/releases)) |
| Pesos | `kyutai/pocket-tts` — **CC-BY-4.0**, **gated com auto-aprovação** (termos de consentimento p/ clonagem); existe `kyutai/pocket-tts-without-voice-cloning` **sem gate** ([HF](https://huggingface.co/kyutai/pocket-tts)) |
| Código | **MIT** (`pip install pocket-tts`; CLI `generate`/`serve`/`export-voice`; servidor HTTP local) |
| Português | **Modelos pt dedicados**: `languages/portuguese/model.safetensors` (6 camadas, distilled) e `languages/portuguese_24l/model.safetensors` (24 camadas, maior qualidade, mais lento) — verificado no tree do HF. Voz default pt = "rafael" (= `voice-donations/Rafaelpazv.wav`, **CC0**) |
| Clonagem | **Local e aberta**: `--voice qualquer.wav` (wav/mp3) gera o embedding na hora. Proibição contratual: clonar sem consentimento |
| Treino/finetune | **Não liberado**; paper promete código de treino, cobrança em aberto ([issue #30](https://github.com/kyutai-labs/pocket-tts/issues/30)). Paper: [arXiv 2509.06926](https://arxiv.org/abs/2509.06926) |
| ⚠️ Pendência | **pt-BR vs pt-PT não documentado** — precisa de teste de escuta (5 min). Indício pró-BR: vozes do ecossistema vêm de CML-TTS (corpus pt majoritariamente brasileiro) e doações; indício neutro: blog não declara variante |

### 4. Kyutai STT

| Item | Estado |
|---|---|
| Pesos | `kyutai/stt-1b-en_fr` e `kyutai/stt-2.6b-en` — **CC-BY-4.0** ([HF](https://huggingface.co/kyutai/stt-1b-en_fr)) |
| Línguas | **EN+FR (1B) e EN (2.6B) — sem português até hoje** |
| Latência | delay de 0,5s (1B, com VAD semântico p/ detecção de fim de fala) e 2,5s (2.6B); servidor Rust: 64 streams a 3× tempo real num L40S ([DSM repo](https://github.com/kyutai-labs/delayed-streams-modeling)) |
| Treino/finetune | Não liberado |
| Implicação | Cascata "all-Kyutai" para pt-BR é **impossível na entrada** → manter faster-whisper p/ STT pt-BR |

### 5. Unmute (cascata otimizada)

| Item | Estado |
|---|---|
| Código | [kyutai-labs/unmute](https://github.com/kyutai-labs/unmute) — **MIT**; backend FastAPI + protocolo estilo OpenAI Realtime; Docker Compose/Swarm |
| LLM | Qualquer servidor OpenAI-compatible (vLLM, Ollama, OpenRouter...) |
| Latência real | TTS (componente): **~750ms tudo num único L40S → ~450ms na infra de produção do unmute.sh**; TTS isolado 220ms/350ms@32 usuários; resposta voz-a-voz total **<1s** reportado pela Kyutai |
| Línguas | EN/FR (presas ao STT/TTS da Kyutai) |
| Vozes | `voices.yaml` + repo tts-voices (inclui as 228 vozes CC0 doadas) |
| HW | ≥16GB VRAM, Linux/WSL |

### 6. Hibiki e **Hibiki-Zero**

| Item | Hibiki (fev/2025) | Hibiki-Zero (fev/2026) |
|---|---|---|
| Tarefa | fr→en simultâneo c/ transferência de voz | {fr, es, **pt**, de}→en simultâneo c/ transferência de voz |
| Pesos | 1B/2B, **CC-BY-4.0** ([HF](https://huggingface.co/kyutai/hibiki-2b-pytorch-bf16)) | 3B, **CC-BY-NC-SA 4.0 → VETADO** ([HF](https://huggingface.co/kyutai/hibiki-zero-3b-pytorch-bf16)) |
| Treino | dados alinhados sintéticos | **GRPO sem nenhum dado alinhado por palavra** (~40kh de fala real por língua-fonte + alinhamento sintético sentence-level + 200h FT); [arXiv 2602.11072](https://arxiv.org/abs/2602.11072) |
| Latência/HW | tempo real | tempo real; batch 3× RT em 1 H100; 8–12GB VRAM ([GitHub](https://github.com/kyutai-labs/hibiki-zero)) |
| Código de treino | não | não (código de inferência MIT) |
| Nota decisiva | — | model card afirma: **"pode ser ajustado para nova língua de entrada com <1000h de fala"** — confirma a tese de adaptação de língua barata na família Moshi/DSM |

### 7. MoshiVis / CASA

- **MoshiVis** (mar/2025): Moshi + cross-attention visual; pesos **CC-BY-4.0** exceto o vision encoder (PaliGemma2, licença Gemma) ([GitHub](https://github.com/kyutai-labs/moshivis), [HF](https://huggingface.co/kyutai/moshika-vis-pytorch-bf16)). Sem mudanças relevantes em 2026.
- **CASA** (dez/2025): nova linha de visão-linguagem da Kyutai (cross-attention via self-attention), não é fala ([kyutai.org/casa](https://kyutai.org/casa)).

### 8. Helium

- **Helium 1 (2B)** continua sendo o único LLM da casa; pesos **CC-BY-SA-4.0** ([HF](https://huggingface.co/kyutai/helium-1-2b)). Sem Helium 2.
- `kyutai/Sequential_Helium_6B` (fev/2026, CC-BY-SA-4.0) é artefato do estudo Kairos sobre temporalidade de dados ([arXiv 2605.22769](https://arxiv.org/abs/2605.22769)), não um modelo de produto.

### 9. **NVIDIA PersonaPlex-7B-v1** (não é Kyutai, mas é o maior evento do ecossistema Moshi)

| Item | Estado |
|---|---|
| O que é | Full-duplex speech-to-speech **construído sobre arquitetura e pesos do Moshi (Moshika)**: Mimi + Temporal/Depth Transformer + backbone Helium ([HF](https://huggingface.co/nvidia/personaplex-7b-v1)) |
| Diferencial | **Controle de persona por prompt de texto** (papel, contexto, cenário) + **condicionamento de voz por prompt de áudio** (16 vozes empacotadas; aceita áudio custom). Resolve no spine o que o projeto planejava fazer com CSM-1B à parte |
| Latência | **turn-taking 170ms, interrupção 240ms** (testado em A100-80GB) |
| Línguas | **Inglês apenas** (treinado em Fisher English) |
| Licenças | Código **MIT** ([GitHub](https://github.com/NVIDIA/personaplex)); pesos **NVIDIA Open Model License** — comercial permitido, mas **NÃO está na whitelist do projeto (Apache/MIT/CC-BY/CC0)** → exige decisão explícita de política |
| Treino/finetune | **Não liberado** (repo só tem inferência/serving/eval). Porém é arquitetura Moshi → o moshi-finetune (Apache) é adaptável em princípio |
| Tração | 315k downloads no HF em ~5 meses |

---

## (b) Kyutai TTS serve para pt-BR? Alguém já adaptou? Qual a receita?

**Resposta curta: o 1.6B não; o Pocket TTS sim (com asterisco de sotaque); ninguém de fora adaptou nenhum dos dois porque não há código de treino.**

1. **Kyutai TTS 1.6B = EN/FR e fechado para adaptação.** Sem código de treino/finetune ([issue #64 aberta desde 2025](https://github.com/kyutai-labs/delayed-streams-modeling/issues/64)), sem encoder de voz público ([issue #404](https://github.com/kyutai-labs/moshi/issues/404)). Não existe nenhum caso público de adaptação de língua do TTS 1.6B (busca em jun/2026). Quem adaptou língua no ecossistema adaptou o **Moshi** (via moshi-finetune), não o TTS.
2. **Pocket TTS é a via Kyutai para pt hoje**: a própria Kyutai treinou modelos pt (6L e 24L) e liberou com CC-BY-4.0 + clonagem local. Para o TTS-ptbr isso significa:
   - **dado sintético license-clean em pt** com a voz do Pedro clonada (CC-BY-4.0 + consentimento próprio = ok);
   - **piso de latência absurdo** (200ms em CPU) para o componente TTS da cascata;
   - limite: 100M params → prosódia/emoção menos rica que TTS grandes; sem código de treino → **não dá para fazer finetune de sotaque carioca** nele hoje (issue #30 cobra o código prometido no paper).
3. **A "receita" de adaptação de língua que existe e funciona é no nível do Moshi/DSM**, não do TTS: vocabulário + CPT em áudio massivo da língua + FT em diálogo estéreo (J-Moshi), ou GRPO sem dados alinhados (Hibiki-Zero, <1000h por língua nova). Para TTS puro, a alternativa continua sendo treinar fora da Kyutai (Kokoro/Chatterbox/etc.) ou esperar o código de treino do Pocket TTS.
4. **Ação recomendada**: teste de escuta do Pocket TTS pt (`uvx pocket-tts generate --language portuguese_24l --voice <wav do Pedro>`) para (i) confirmar variante pt-BR vs pt-PT e (ii) medir qualidade da clonagem da voz do Pedro. Custo: minutos, em CPU.

---

## (c) J-Moshi e sucessores — o que os papers 2025–2026 ensinaram

1. **J-Moshi** (Nagoya, [arXiv 2506.02979](https://arxiv.org/html/2506.02979v1)) continua sendo a receita canônica: adaptação de vocabulário → CPT com 69kh de pseudo-estéreo japonês → FT com 344h de diálogo estéreo real → dado sintético multi-stream TTS. **Atenção: os pesos do J-Moshi são CC-BY-NC-4.0** ([HF nu-dialogue/j-moshi](https://huggingface.co/nu-dialogue/j-moshi)) — a receita é livre, os pesos não.
2. **LLM-jp-Moshi-v1** (fev/2026) é o sucessor em escala: Moshi 7B + **J-CHAT ~69.000h (podcasts) + ~1.000h de diálogo Zoom**, treinado no ABCI 3.0, **pesos Apache-2.0** ([HF](https://huggingface.co/llm-jp/llm-jp-moshi-v1), [GitHub](https://github.com/llm-jp/llm-jp-moshi)). Prova que (i) a adaptação de língua do Moshi se repete fora do grupo original e (ii) dá para soltar o resultado com licença permissiva. Autores avisam: ainda protótipo, respostas podem soar não-naturais; requer ≥24GB VRAM.
3. **Lições novas (Abe et al., IWSDS fev/2026, ["Effects of dialogue corpora properties on fine-tuning a Moshi-based spoken dialogue model"](https://aclanthology.org/2026.iwsds-1.10/))** — diretamente aplicável ao desenho do dataset do Pedro:
   - as **propriedades interacionais** do corpus (e não só quantidade/qualidade) moldam o comportamento: corpus estilo *chat* → ritmo natural, overlaps e gaps moderados; corpus estilo *consulta* → timing mais estável e deliberado;
   - **qualidade de áudio do corpus transfere direto** para a qualidade de fala do modelo;
   - **mismatch de domínio degrada coerência linguística** → gravar diálogo no estilo-alvo (conversa casual carioca), não leitura.
   - Ferramenta associada: [nu-dialogue/moshi-finetune](https://github.com/nu-dialogue/moshi-finetune) (fork para FT em dados próprios de diálogo).
4. **Infra de dados**: o paper **Sommelier** ([arXiv 2603.25750](https://arxiv.org/pdf/2603.25750)) propõe pipeline escalável de pré-processamento de áudio multi-turno para SLMs full-duplex (o "como fabricar pseudo-estéreo em escala") — candidato a base do nosso pipeline pt-BR.
5. **Benchmark**: o desafio **HumDial @ ICASSP 2026** ([arXiv 2604.21406](https://arxiv.org/abs/2604.21406)) e o Full-Duplex-Bench consolidaram avaliação de turn-taking/interrupção — usar como referência do eval harness.

---

## (d) Moshi 2? Helium novo? Roadmap público

- **Não existe Moshi 2** e não há roadmap público formal. O que existe (sinais fortes, todos verificáveis no blog/HF):
  - **Pós-treino de interatividade com RL é a aposta atual** ([blog 2026-06-10](https://kyutai.org/blog/2026-06-10-interactivity); paper ["Multi-Faceted Interactivity Alignment in Full-Duplex Speech Models", arXiv 2606.11167](https://arxiv.org/abs/2606.11167), autores incluem Ohashi — o autor do J-Moshi — agora com Zeghidour/Défossez/Kharitonov): GRPO com recompensas específicas por eixo (pausa, turn-taking, backchannel, interrupção) derivadas de conversa humana (Seamless Interaction, ~4.000h) + recompensa LLM-judge para não degradar conteúdo. Resultado: menos interrupções indevidas, **latência de resposta de turno substancialmente menor**, backchannels bem posicionados — em eval offline e em diálogo multi-turno em tempo real.
  - Artefatos: `kyutai/moshika-rl-seamless` (**CC-BY-4.0**, 8B bf16, gated auto, `python -m moshi.server --hf-repo kyutai/moshika-rl-seamless`) e `kyutai/personaplex-rl-seamless` (delta CC-BY-4.0 **+ NVIDIA OML herdada** → fora da whitelist).
  - **Colaboração de fato Kyutai↔NVIDIA** em torno da arquitetura Moshi (PersonaPlex) — o ecossistema do spine está crescendo, não morrendo.
  - **MoshiRAG** (abr/2026): conhecimento externo em conversa full-duplex sem quebrar o fluxo.
  - **Multilíngue no Moshi**: nenhum anúncio oficial; afirmações de terceiros de que "variantes multilíngues estão em desenvolvimento" ([nextomoro](https://nextomoro.com/kyutai/)) — confiança baixa.
- **Helium**: parado no Helium 1 2B (abr/2025, CC-BY-SA-4.0). Pesquisas derivadas (ARC-Encoder, Kairos) não são modelos de produto.
- **Leitura estratégica para o projeto**: a Kyutai está investindo exatamente na camada que diferencia "Maya": interatividade conversacional pós-treino. O caminho Moshi → (adaptação pt-BR à la J-Moshi/LLM-jp) → (RL de interatividade à la 2606.11167 com dados pt-BR) está agora inteiramente pavimentado com artefatos e papers públicos.

---

## (e) Unmute muda a aposta "cascata é só piso"?

**Move o piso para cima; não muda o teto.**

Números reais reportados (fontes primárias):
- TTS isolado: **220ms** até o 1º áudio; **350ms servindo 32 usuários num único L40S** ([X Kyutai](https://x.com/kyutai_labs/status/1940767331921416302)).
- Pipeline completo: TTS (componente) cai de **~750ms (tudo num L40S) para ~450ms na infra de produção do unmute.sh**; STT com delay de **0,5s** (stt-1b, com VAD semântico embutido — detecta fim de turno pela semântica, não só silêncio); resposta total voz-a-voz **<1s** ([GitHub unmute](https://github.com/kyutai-labs/unmute)).
- Ou seja: uma cascata bem-engenheirada (streaming nas 3 pontas + VAD semântico) entrega p50 perto de 700ms–1s — **dentro do alvo "<800ms" do projeto, mas longe dos 200–300ms ideais** e estruturalmente incapaz de overlap/backchannel verdadeiro.
- E é a própria Kyutai que confirma o teto: o blog de hoje justifica o RL de interatividade porque modelos full-duplex (não cascatas) são o único lugar onde pausa/interrupção/backchannel podem ser otimizados como comportamento do modelo. A cascata responde rápido; ela não **conversa**.
- Para pt-BR há um furo adicional: **Kyutai STT não tem português** → o "Unmute brasileiro" teria que ser faster-whisper + LLM + Pocket TTS-pt. Viável como **piso imediato** (e com componentes MIT/CC-BY/Apache, license-clean), e o repo Unmute (MIT) serve de esqueleto de orquestração/WebSocket pronto.

**Veredicto: manter a tese.** Cascata = piso (agora mais alto e mais barato de montar, com Unmute como referência de engenharia). Spine full-duplex = destino, reforçado pelo fato de a Kyutai ter publicado a receita de RL que faltava.

---

## Implicações diretas para o TTS-ptbr (recomendações)

1. **Adotar arXiv 2606.11167 como blueprint do pós-treino** (substitui/complementa Step-Audio 2 GRPO como referência): recompensas por eixo de interatividade + LLM-judge, sobre moshi-finetune. Estudar se os rewards são reproduzíveis com dados pt-BR (Seamless Interaction é inglês; precisaremos de proxy pt-BR).
2. **Testar Pocket TTS pt imediatamente** (escuta pt-BR vs pt-PT + clonagem da voz do Pedro). Se pt-BR: vira (i) gerador de dado sintético license-clean ao lado de Kokoro/Chatterbox, (ii) TTS do piso de cascata, (iii) candidato a TTS on-device.
3. **Política de licença — decisão pendente**: PersonaPlex (NVIDIA OML) está fora da whitelist atual, mas resolve "voz por prompt + persona" dentro do spine. Ou amplia-se a whitelist (OML permite uso comercial), ou replica-se a ideia: condicionamento de voz no Moshi via finetune próprio (receita descrita no paper do PersonaPlex, dados Fisher → análogo pt-BR).
4. **Desenho do dataset do Pedro**: incorporar as lições do IWSDS 2026 — gravar **diálogo espontâneo no estilo-alvo** (não só leitura dirigida), com qualidade de áudio alta e estatísticas de pausa/overlap/backchannel naturais do carioca; o estilo interacional do corpus vira o estilo do modelo.
5. **Não esperar código de treino dos TTS da Kyutai** (1.6B e Pocket): pedidos abertos sem resposta; planejar sem essa dependência.
6. **Eval harness**: alinhar com Full-Duplex-Bench/HumDial (pausa, turn-taking, backchannel, interrupção) — são as métricas que a própria Kyutai usa no paper de RL.

---

## Fontes primárias

- Kyutai blog index: https://kyutai.org/blog
- RL interatividade (hoje): https://kyutai.org/blog/2026-06-10-interactivity · paper: https://arxiv.org/abs/2606.11167 · modelo: https://huggingface.co/kyutai/moshika-rl-seamless · https://huggingface.co/kyutai/personaplex-rl-seamless
- Moshi: https://github.com/kyutai-labs/moshi · https://huggingface.co/kyutai/moshika-pytorch-bf16
- moshi-finetune: https://github.com/kyutai-labs/moshi-finetune
- MoshiRAG: https://kyutai.org/blog/2026-04-30-moshi-rag · https://huggingface.co/kyutai/moshika-rag-pytorch-bf16
- DSM (TTS/STT): https://github.com/kyutai-labs/delayed-streams-modeling · paper https://arxiv.org/abs/2509.08753 · https://huggingface.co/kyutai/tts-1.6b-en_fr · https://huggingface.co/kyutai/stt-1b-en_fr
- Vozes: https://huggingface.co/kyutai/tts-voices · clonagem 1.6B fechada: https://github.com/kyutai-labs/moshi/issues/404 · finetune TTS: https://github.com/kyutai-labs/delayed-streams-modeling/issues/64
- Pocket TTS: https://github.com/kyutai-labs/pocket-tts · releases: https://github.com/kyutai-labs/pocket-tts/releases · https://huggingface.co/kyutai/pocket-tts · paper: https://arxiv.org/abs/2509.06926 · docs: https://kyutai-labs.github.io/pocket-tts/ · código de treino pendente: https://github.com/kyutai-labs/pocket-tts/issues/30
- Unmute: https://github.com/kyutai-labs/unmute · https://kyutai.org/unmute · latência TTS: https://x.com/kyutai_labs/status/1940767331921416302
- Hibiki-Zero: https://github.com/kyutai-labs/hibiki-zero · https://huggingface.co/kyutai/hibiki-zero-3b-pytorch-bf16 · paper: https://arxiv.org/abs/2602.11072 · Hibiki original: https://huggingface.co/kyutai/hibiki-2b-pytorch-bf16
- MoshiVis: https://github.com/kyutai-labs/moshivis · https://huggingface.co/kyutai/moshika-vis-pytorch-bf16 · CASA: https://kyutai.org/casa
- Helium 1: https://huggingface.co/kyutai/helium-1-2b
- PersonaPlex: https://huggingface.co/nvidia/personaplex-7b-v1 · https://github.com/NVIDIA/personaplex
- J-Moshi: https://arxiv.org/html/2506.02979v1 · https://huggingface.co/nu-dialogue/j-moshi · LLM-jp-Moshi: https://huggingface.co/llm-jp/llm-jp-moshi-v1 · https://github.com/llm-jp/llm-jp-moshi · lições IWSDS 2026: https://aclanthology.org/2026.iwsds-1.10/ · fork finetune: https://github.com/nu-dialogue/moshi-finetune
- Sommelier (pré-processamento full-duplex): https://arxiv.org/pdf/2603.25750 · HumDial/ICASSP 2026: https://arxiv.org/abs/2604.21406

*Verificações feitas via API do Hugging Face (licença/gating/datas) em 2026-06-10.*
