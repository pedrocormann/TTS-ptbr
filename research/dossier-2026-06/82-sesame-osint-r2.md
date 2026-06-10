# 82 — OSINT Sesame, rodada 2 (fechando as lacunas da rodada 1)

**Data da coleta:** 2026-06-10 · **Método:** GitHub (páginas HTML, feeds `.atom`, endpoints
`.patch`/`.diff`, páginas `/compare`), arXiv (abs + HTML), web search + fetch de fontes primárias.
**Nota de método:** a API REST `api.github.com` estava inacessível no ambiente (timeout); todos os
diffs abaixo foram extraídos dos endpoints públicos `github.com/.../commit/<sha>.patch|.diff` e das
páginas `/compare`, que são equivalentes e verificáveis.
**Regra de confiança:** [P] = fonte primária · [S] = secundária confiável · [F] = fraca.

**Contexto herdado da rodada 1 (81-sesame-osint.md):** Maya = cascata silero-vad → whisper →
sglang(Gemma) → CSM com ~2 min de áudio-contexto, tool-use assíncrono com re-síntese incremental,
watermark silentcipher; produção possivelmente CSM-1B.

---

## 1. Diff real dos forks da org SesameAILabs [P]

### 1.1 `SesameAILabs/sglang` — o único fork com engenharia própria visível (7 commits ahead)

Fork de `cinjon/sglang` (fork pessoal do Cinjon Resnick) → upstream `sgl-project/sglang`.
Base do fork = upstream em 28/jan/2025 (último commit upstream incorporado: `9f635ea`, mickqian).
Lista COMPLETA dos commits próprios (verificada via `commits/main.atom` + páginas filtradas por
autor — não há mais nenhum commit próprio além destes 7):

| # | SHA | Autor | Data | Mensagem |
|---|---|---|---|---|
| 1 | `a4abcb1116d0` | cinjon (Cinjon Resnick, cinjon.resnick@gmail.com) | 2025-01-29 | "Add logit bias into main. (#1)" |
| 2 | `57ad4363daae` | apkumar (Ankit Kumar, ankit@apkumar.com) | 2025-02-05 | "Update tokenizer_manager.py" |
| 3 | `cf4b8cff2c7a` | apkumar | 2025-02-05 | Merge PR #1 (apkumar-patch-1) |
| 4 | `45e28bd524be` | Cinjon (**Cinjon@sesame.com**) | 2025-02-18 | "Clamp the logit outputs so we dont run into json errors." |
| 5 | `5a9693b1c7bd` | cinjon | 2025-02-18 | Merge PR #2 (cj/clamp) |
| 6 | `022a3902713c` | nealmanaktola (neal@sesameai.com) | 2025-05-07 | "Update pyproject.toml (#3)" |
| 7 | `e677d377d2bc` | nealmanaktola | 2025-05-07 | "Update pyproject.toml (#4)" |

**Diff de cada commit (extraído dos `.patch`/`.diff`):**

**(1) `a4abcb1` — logit bias na API OpenAI do SGLang** (4 arquivos, +52/−8):
- `python/sglang/srt/openai_api/adapter.py`: adiciona `"logit_bias": request.logit_bias` aos
  dicts de sampling em `v1_generate_request` e `v1_chat_generate_request` (expõe o parâmetro
  na API compatível-OpenAI).
- `python/sglang/srt/sampling/sampling_params.py`: novo parâmetro
  `logit_bias: Optional[Dict[int, float]] = None` no `__init__`.
- `python/sglang/srt/sampling/sampling_batch_info.py`: monta tensor de logit_bias com shape
  `(len(reqs), vocab_size)` quando qualquer request do batch traz logit_bias; corrige dtype
  (troca context manager `torch.dtype` por dtype explícito na criação do tensor).
- `test/srt/test_srt_endpoint.py`: `test_logit_bias()` — bias de 100.0 força amostragem
  consistente do mesmo token em 4 tokens gerados.
- **Leitura:** controle determinístico de tokens específicos no LLM em produção — a ferramenta
  clássica para forçar/banir tokens de controle (tags de estilo, marcadores de tool-call,
  formatação JSON) na saída do Gemma que alimenta o CSM.

**(2) `57ad4363` — abort 50x mais rápido** (1 arquivo, 1 linha):
- `python/sglang/srt/managers/tokenizer_manager.py`, método `create_abort_task`:
  `await asyncio.sleep(1)` → `await asyncio.sleep(0.02)`.
- **Leitura (o commit mais revelador do fork):** o loop que processa aborts de geração em voo
  passa a reagir em **20 ms em vez de 1 s**. É a digital de um sistema que **cancela a geração
  do LLM no meio** o tempo todo — exatamente o que barge-in do usuário e o "pivota no meio da
  frase quando chega resultado de busca" exigem. Para um serving batch normal, 1 s de latência
  de abort é irrelevante; para conversa em tempo real, é inaceitável. Commitado pelo **CTO**.

**(4) `45e28bd` — clamp anti `-inf`** (2 arquivos):
- `python/sglang/srt/layers/sampler.py`: em dois pontos, adiciona
  `.clamp(min=torch.finfo(probs.dtype).min)` com comentário `# clamp to avoid -inf.`
- `test/srt/sampling/penaltylib/test_srt_endpoint_with_penalizers.py`: troca prints de debug
  por `assert response.status_code == 200`.
- **Leitura:** a mensagem do commit é literal — "so we dont run into **json errors**". Logprobs
  `-inf` (consequência direta de logit_bias/penalizers agressivos) quebravam a serialização
  JSON das respostas. Confirma que eles usam bias/penalidades fortes em produção e que a saída
  do LLM trafega como JSON estruturado.

**(6) `022a390` — despina vllm** (`python/pyproject.toml`): `"vllm==0.6.4.post1"` → `"vllm"`.
**(7) `e677d377` — despina outlines** (`python/pyproject.toml`):
`"outlines>=0.0.44,<0.1.0"` → `"outlines>=0.0.44"`.
- **Leitura:** manutenção de deps (mai/2025) para conviver com versões novas de vllm e
  **outlines** — e outlines é a biblioteca de **geração estruturada/JSON constrainada** do
  SGLang. O conjunto logit_bias + clamp-JSON + outlines fecha o quadro: o LLM da Maya emite
  **saída estruturada (JSON) com tokens controlados**, presumivelmente separando "o que falar"
  de "chamadas de ferramenta".

### 1.2 `SesameAILabs/faster-whisper-plus` — **zero diff público** [P]

- Compare `SYSTRAN/faster-whisper:master...SesameAILabs:faster-whisper-plus:master` retorna
  literalmente: *"There isn't anything to compare. SYSTRAN:master is up to date with all
  commits from SesameAILabs:master."* → **0 commits ahead**.
- Os 20 commits mais recentes do fork são todos de mantenedores upstream (MahmoudAshraf97 ×13,
  Purfview ×3, heimoshuiyu, jordimas, zh-plus, trungkienbkhn). 245 commits, nenhum branch extra.
- A descrição do repo diz **"Faster Whisper with additional features"** — mas as "additional
  features" **não existem no código público**. Conclusão: ou o "plus" vive em repo privado
  (fork espelho renomeado para casar com pacote interno), ou a intenção nunca virou código
  público. A lacuna da rodada 1 está fechada: **não há diff a estudar**.

### 1.3 `SesameAILabs/silero-vad` — espelho puro [P]

- Compare `snakers4/silero-vad:master...SesameAILabs:silero-vad:master`:
  *"snakers4:master is up to date with all commits from SesameAILabs:master."* → **0 ahead**.
- Top 20 commits todos de upstream (snakers4, adamnsandle, gau-nernst, yairl, abinthomasonline).
- O uso do silero é como dependência, não como código modificado publicamente.

### 1.4 Bônus (lacuna r1): `SesameAILabs/torchtune` — também 0 ahead [P]

- Compare `meta-pytorch/torchtune:main...SesameAILabs:torchtune:main`: *"meta-pytorch:main is
  up to date with all commits from SesameAILabs:main."* O "push dez/2025" da rodada 1 era
  sync/espelho, não trabalho próprio público.

### 1.5 `SesameAILabs/silentcipher` — **4 commits próprios** (achado novo da rodada) [P]

A rodada 1 não tinha o diff; o compare contra `sony/silentcipher:master` mostra **4 commits
ahead**, e o autor principal é **Zack Hodari** (o pesquisador de prosódia da Sesame):

| SHA | Autor | Data | Mensagem |
|---|---|---|---|
| `898f27ab` | ZackHodari (zackhodari@gmail.com) | 2025-03-13 | "Update requirements, support torch.Tensor (#1)" |
| `ec6bd900` | dw61 (Leo Wang, contribuidor externo) | 2025-03-17 | "[server] directly initialize msg_enc to torch.float32 to support mps (#3)" |
| `e080df7e` | ZackHodari | 2025-03-17 | "relax requirements (#4)" |
| `d46d7d08` | ZackHodari | 2025-03-17 | "relax requirements (#5)" |

Diff do commit principal (`898f27ab`, +87/−67 em `src/silentcipher/server.py` + requirements):
- **Reescreve o caminho de encode/decode de numpy para torch**: aceita `torch.Tensor` direto
  (`if not isinstance(y, torch.Tensor): y = torch.tensor(y, dtype=torch.float32)`),
  `librosa.resample` → `torchaudio.functional.resample`, `np.mean/np.concatenate` →
  `torch.mean/torch.cat`, constantes movidas para o device
  (`torch.tensor(self.average_energy_VCTK, device=self.device)`).
- `ec6bd900` adiciona compat **MPS (Mac)** — dtype float32 explícito no `msg_enc` (PR externo
  aceito e mergeado por eles).
- Os dois "relax requirements" trocam pins `==` por `>=` (torch>=2.4.0 etc.).
- **Leitura:** eles tornaram o watermarking **tensor-nativo e residente em GPU**, eliminando a
  ida-e-volta CPU/numpy — o necessário para marcar áudio **inline no pipeline de síntese em
  tempo real**, não como pós-processo offline. (E o suporte MPS sugere devs rodando em Mac.)

### 1.6 Como o repo `csm` USA o silentcipher [P]

`requirements.txt` do csm aponta **direto para o fork**:
`silentcipher @ git+https://github.com/SesameAILabs/silentcipher@master`.

**`watermarking.py`** (arquivo dedicado):
- Constante pública: `CSM_1B_GH_WATERMARK = [212, 211, 146, 56, 201]` — com comentário de que
  é "public key for demonstration only" (chave de 5 bytes ≈ os 40 bits do silentcipher;
  produção usa chave privada distinta).
- `load_watermarker(device="cuda")` → `silentcipher.server.Model` configurado para **44.1 kHz**.
- `watermark(watermarker, audio, sample_rate, key)` → resampleia para 44.1k, codifica com
  **`message_sdr=36`** (36 dB de relação sinal-distorção da marca — quase inaudível), e
  resampleia de volta (cap em 44.1k).
- `verify(...)` → decodifica e compara a mensagem extraída com a chave; retorna booleano.
- `check_audio_from_file` / `cli_check_audio` → CLI de verificação (`--audio_path`).

**`generator.py`** (integração):
- Import: `from watermarking import CSM_1B_GH_WATERMARK, load_watermarker, watermark`.
- No `__init__` do `Generator`: `self._watermarker = load_watermarker(device=device)` —
  o watermarker é carregado junto com o modelo, sempre.
- No fim de **todo** `generate()` (assinatura:
  `generate(text, speaker, context: List[Segment], max_audio_length_ms=90_000, temperature=0.9, topk=50)`):
  ```python
  audio, wm_sample_rate = watermark(self._watermarker, audio, self.sample_rate, CSM_1B_GH_WATERMARK)
  audio = torchaudio.functional.resample(audio, orig_freq=wm_sample_rate, new_freq=self.sample_rate)
  ```
  Ou seja: **não existe caminho de geração sem watermark** no código de referência; a marca é
  aplicada a 44.1 kHz e o áudio volta para os 24 kHz do Mimi.
- O README do csm **não menciona** o watermark (só a seção "Misuse and abuse") — a salvaguarda
  está 100% no código.

---

## 2. A linhagem do controle de emoção (papers de Lyth e Eskimez)

### 2.1 Parler-TTS — "Natural language guidance of high-fidelity text-to-speech with synthetic annotations" (arXiv 2402.01912, Dan Lyth & Simon King, fev/2024) [P]

O pipeline de **anotação sintética em escala** (o coração do paper, e o playbook que o Lyth
levou para a Sesame):

| Atributo | Ferramenta/Método |
|---|---|
| Gênero | labels do próprio dataset (modelo preditivo do MLS) |
| **Sotaque** | classificador próprio: embeddings de um modelo de language-ID + **classificador linear simples**, treinado em **EdAcc + VCTK + VoxPopuli**, **53 sotaques**, 86% de acurácia |
| Pitch (média por falante + desvio por enunciado) | contornos de pitch via biblioteca **PENN** |
| Velocidade de fala | fonemas/segundo — G2P via biblioteca **g2p** ÷ duração |
| SNR (ruído) | biblioteca **Brouhaha** |
| C50 (reverberação) | **Brouhaha** |

- Variáveis contínuas discretizadas em **7 bins** com frases descritivas ("very fast",
  "quite fast", "fairly slowly"...).
- Keywords → descrições em linguagem natural via LLM **Stable Beluga 2.5** com prompts
  ("female, Hungarian, ..." → "a woman with a deep voice speaking slowly...").
- Dados: **MLS inglês (45k h) + LibriTTS-R (585 h)** — só "found data".
- Arquitetura: AudioCraft adaptado; codec **DAC 44.1 kHz, 9 codebooks, 86 Hz**; transcript
  pre-pendido + descrição via cross-attention.

**O que isso sugere sobre o dataset da Sesame:** o post do CSM diz, verbatim: *"We use a large
dataset of publicly available audio, which we transcribe, diarize, and segment. After
filtering, the dataset consists of approximately one million hours of predominantly English
audio."* É o pipeline do Parler-TTS escalado ~20x (45k h → 1M h) — found data + rotulagem
automática + filtragem — com a diferença de que no CSM o controle não é por descrição textual,
e sim **implícito, pelo contexto conversacional de áudio** (a janela de ~2 min). A presença do
Lyth no time torna quase certo que rótulos sintéticos de estilo/qualidade (SNR/C50/pitch/rate)
foram usados ao menos na **filtragem** do 1M h.

### 2.2 E2-TTS — "Embarrassingly Easy Fully Non-Autoregressive Zero-Shot TTS" (arXiv 2406.18009, **Eskimez como 1º autor**, MSR, jun/2024) [P]

- Flow-matching **não-autoregressivo** sobre mel; entrada = sequência de **caracteres com
  filler tokens** até o comprimento do mel; treino por **audio infilling**.
- **Sem** duration model, sem G2P, sem monotonic alignment search.
- Iguala/supera Voicebox e NaturalSpeech 3 em naturalidade/similaridade.
- **Contraste com o CSM:** o CSM é autoregressivo (backbone Llama + decoder Mimi RVQ) — a
  arquitetura do E2 **não** foi a adotada. O que o Eskimez plausivelmente levou não foi a
  arquitetura, e sim a cultura MSR de simplificação + curadoria massiva (ver 2.3).

### 2.3 EmoCtrl-TTS — "Laugh Now Cry Later: Controlling Time-Varying Emotional States of Flow-Matching-Based Zero-Shot TTS" (arXiv 2407.12229, Eskimez co-autor, jul/2024) [P]

Técnicas de controle de emoção/risada (verificadas no HTML v2):
- **Condicionamento frame-level variável no tempo**: embeddings de **arousal/valence** de um
  extrator A-V-D (wav2vec 2.0 **fine-tunado em MSP-PODCAST**), janela deslizante de 0.5 s com
  hop de 0.25 s; + **embedding de risada de 32 dims** de um detector off-the-shelf — que na
  prática captura NVs além de risada (choro, gemidos). Interpolação linear para alinhar ao
  comprimento da sequência de fonemas.
- **Curadoria por pseudo-rotulagem**: de **200k h de áudio interno não-rotulado** → **27k h**
  filtrando com **emotion2vec** (mantém {angry, disgusted, fearful, sad, surprised} ou
  {neutral, happy} com confiança 1.0), **DNSMOS** OVRL > 3.0 (qualidade) e um detector interno
  de troca de falante (descarta amostras com mudança de speaker).
- Base: Voicebox (flow-matching), Transformer 24L/16 heads/1024d/FF 4096.

### 2.4 O que do post do CSM ecoa esses papers [P]

- **Eco direto (dados):** "transcribe, diarize, segment... after filtering" = o funil de
  pseudo-rotulagem do EmoCtrl (200k→27k) e a anotação automática do Parler aplicados a 1M h.
- **Eco direto (avaliação expressiva):** o estudo CMOS do CSM usa o **dataset Expresso**
  (fala expressiva com NVs) com condições com/sem contexto — a mesma obsessão por emoção
  dependente de contexto do EmoCtrl, transposta de "controle explícito por embedding" para
  "controle implícito por contexto de conversa".
- **Eco conceitual:** os "key components" do post — *"Emotional intelligence: reading and
  responding to emotional contexts"*, *"Conversational dynamics: natural timing, pauses,
  interruptions and emphasis"*, *"Contextual awareness: adjusting tone and style"* — são a
  fusão das três linhas: emoção (Eskimez), estilo rotulado em escala (Lyth) e prosódia
  contextual (tese do Hodari).
- **Não-eco (refutação útil):** o post do CSM **não menciona** controle por descrição em
  linguagem natural (estilo Parler) nem vocalizações não-verbais explícitas — não há tags
  públicas de risada/suspiro no CSM-1B. O controle público é só: id do speaker + contexto de
  áudio. (As issues #164/#169 do repo pedindo condicionamento de emoção seguem sem resposta.)

**Para o TTS-ptbr:** o stack de rotulagem inteiro é open e replicável em pt-BR — Brouhaha
(SNR/C50), PENN (pitch), g2p/fonemas-por-segundo (rate), emotion2vec (emoção), DNSMOS
(qualidade), detector de risada, A-V via wav2vec2+MSP-PODCAST, 7 bins + LLM para descrições.

---

## 3. Schalkwyk na Meta (desde jun/2025) e ex-Sesame em 2026

- **Cargo confirmado:** "Voice Lead — Meta Superintelligence Lab" (LinkedIn, theorg.com) [S/F].
- **PlayAI (jul/2025):** Meta adquiriu a startup de voice cloning; o time inteiro passou a
  **reportar diretamente ao Schalkwyk** (The Information; réplicas mlq.ai, HPCwire/AIwire) [S].
- **WaveForms (ago/2025, ~US$ 40M):** aquisição do time de "emotional voice AI" de **Alexis
  Conneau** (ex-líder de áudio do GPT-4o na OpenAI) + Coralie Lemaitre, integrados ao MSL
  (the-decoder, Digital Music News, Outlook Business) [S]. A Meta está montando sob Schalkwyk
  exatamente o tipo de time que a Sesame tem.
- **Publicações dele na Meta: NENHUMA encontrada** até 2026-06-10 — nem paper, nem blog post
  técnico assinado, nem anúncio de voice mode do Llama com o nome dele. Verificado por
  múltiplas buscas; **não existe** material público que exponha a linha Sesame. (Vigiar.)
- **Outros ex-Sesame, papers 2026: nada novo.** Checados Hodari (Semantic Scholar), Sanabria
  (Scholar/CMU), Lyth, Eskimez, Resnick — nenhuma publicação 2026 com novas afiliações ou
  conteúdo revelador. O ecossistema full-duplex 2026 no arXiv (τ-Voice 2603.13686, HumDial/
  ICASSP-2026 2604.21406, PersonaPlex 2602.06053, Unit-Based semi-cascaded 2601.20230) segue
  **sem nenhuma afiliação Sesame ou Meta-voice/Schalkwyk**.

---

## 4. "Curiosity engine" e a stack de busca-durante-fala

### 4.1 Fonte primária — blog "Voice your curiosity" (Raven Jiang, Head of Product Engineering, 27/mai/2026) [P]

Verbatim (as frases mais importantes que existem publicamente sobre o orquestrador):
> "Sesame agents can run **multiple parallel searches while speaking** and seamlessly **weave
> relevant results into their response as they stream in, pivoting mid-sentence if
> necessary**."
> — isso "allows our agents to carefully **balance latency and accuracy**" e "tap into
> **slower and smarter agentic loops without awkward interruptions**".

Mais: "curiosity engine" = nome **interno** ("what we internally refer to as the curiosity
engine — agents that help you learn, discover, and reflect"); memória por agente ("what you
discuss with Miles stays with Miles"), consistente entre voz e texto; Incognito Mode (lê
contexto, não grava); próximo passo declarado: agentes que **fazem** coisas "for you", não só
pensam "with you"; Android "em breve"; óculos 2027.

### 4.2 Vagas (Ashby API, 2026-06-10) [P]

- **SWE - Backend Engineer**: "Own the architecture of systems where ML models are a critical
  component but not the whole story... **agentic orchestration, stateful conversation
  systems**", "**scalable agentic workflows**" → o orquestrador é um sistema backend dedicado
  (não está dentro do modelo de fala).
- Nenhuma vaga menciona RL/reinforcement → **sem evidência de RL** no curiosity engine;
  tudo aponta para orquestração + prompting + serving.

### 4.3 Podcast a16z com o fundador [S→P]

- **"Building the Next Generation of Conversational AI"**, AI + a16z, **14/mar/2025**, 1h42 —
  **Ankit Kumar (CTO)** com Anjney Midha (a16z.com/podcast/building-the-next-generation-of-conversational-ai/;
  YouTube watch?v=bTcpNQH8ViQ). Temas confirmados na página: full-duplex conversation modeling,
  otimizações de latência, scaling laws de síntese, in-context learning para vozes expressivas,
  trade-off personalidade×eficiência, open-sourcing de componentes, "produto antes de API".
  Resumo de terceiros (podwise) acrescenta: direção "transcription-free audio processing",
  debate AR vs diffusion, roadmap "multimodal transformer", "full-duplex conversational AI
  para óculos AR". **Anterior ao app (mai/2026); não detalha tool-use durante fala.** É a
  única entrevista técnica longa de fundador localizada; vale a escuta integral (1h42) para
  a rodada 3.
- **TestingCatalog** (28/mai/2026) [S]: agentes "can search the web, **manage reminders**, and
  have memory" → além de busca, há pelo menos uma segunda ferramenta (reminders).

### 4.4 A ponte entre as fontes e o código (síntese da frente 4)

O comportamento descrito no blog (buscas paralelas + pivô no meio da frase) casa um-a-um com
os commits do fork sglang: **logit_bias** (forçar/banir tokens de controle), **outlines/JSON**
(saída estruturada para separar fala de tool-calls), **clamp anti-`-inf`** (robustez do JSON
sob bias agressivo) e **abort em 20 ms** (matar a geração em voo quando chega resultado novo
ou o usuário interrompe, e re-gerar com o contexto atualizado). Não existe NENHUMA fonte
pública descrevendo o mecanismo interno além disso — o que está acima é o teto do verificável
em 2026-06-10.

---

## 5. Síntese — o que muda para o TTS-ptbr

1. **A hipótese da cascata sai re-confirmada e mais nítida.** Os únicos pontos onde a Sesame
   tocou código de infra pública são (a) controle de decodificação + abort rápido no serving
   do LLM e (b) watermark tensor-nativo. Todo o resto (VAD, ASR, torchtune, moshi) é espelho.
   A mágica é orquestração + dados, não forks secretos.
2. **Receita concreta para o nosso laço de re-síntese incremental:** abort de geração precisa
   ser ~20 ms, não ~1 s; saída do LLM em JSON estruturado (outlines/logit_bias) separando
   "fala" de "tool-call"; buscas paralelas assíncronas que injetam contexto e disparam
   re-geração do trecho ainda não falado.
3. **Watermark é barato e pronto:** silentcipher do fork deles aceita torch.Tensor e MPS (roda
   no M2!); integração = 3 linhas no fim do generate(), chave de 5 bytes, message_sdr=36,
   44.1 kHz. Adotar no Maya-BR v0 desde o dia 1.
4. **Pipeline de rotulagem pt-BR tem blueprint completo** (Parler + EmoCtrl, seção 2): tudo
   open-source, tudo roda em Colab. Sotaque via embeddings de language-ID + classificador
   linear (86% com 53 sotaques!) é exatamente o atalho para o eixo carioca.
5. **Vigiar (VIGIL-LOG):** 1º paper/anúncio de voz do MSL com Schalkwyk/Conneau; escuta
   integral do podcast a16z (1h42); release Android; qualquer commit novo nos forks (sglang e
   silentcipher são os canários); CSM-2/HF.

---

## Fontes

**GitHub [P]:**
- https://github.com/SesameAILabs/sglang (+ /commits/main.atom, /commits/main/?author=cinjon|apkumar|nealmanaktola)
- Patches: github.com/SesameAILabs/sglang/commit/{a4abcb1,57ad436,45e28bd→5a9693b.diff,022a390,e677d377d2bcd3e6c34d61866190f2d133663041}.patch
- https://github.com/SYSTRAN/faster-whisper/compare/master...SesameAILabs:faster-whisper-plus:master
- https://github.com/snakers4/silero-vad/compare/master...SesameAILabs:silero-vad:master
- https://github.com/meta-pytorch/torchtune/compare/main...SesameAILabs:torchtune:main
- https://github.com/sony/silentcipher/compare/master...SesameAILabs:silentcipher:master (+ commits/master.atom)
- Patches silentcipher: commit/{898f27aba3ac…,ec6bd9003607…,e080df7ee87d…,d46d7d0893a5…}.patch
- https://raw.githubusercontent.com/SesameAILabs/csm/main/{watermarking.py,generator.py,requirements.txt,README.md}

**Papers [P]:**
- https://arxiv.org/abs/2402.01912 (+ /html/2402.01912v1) — Parler-TTS, Lyth & King
- https://arxiv.org/abs/2406.18009 — E2-TTS, Eskimez et al. (MSR)
- https://arxiv.org/abs/2407.12229 (+ /html/2407.12229v2) — EmoCtrl-TTS

**Sesame [P]:**
- https://www.sesame.com/blog/voice-your-curiosity (Raven Jiang, 2026-05-27)
- https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice
- https://api.ashbyhq.com/posting-api/job-board/sesame

**Schalkwyk/Meta [S]:**
- https://theorg.com/org/meta/org-chart/johan-schalkwyk · linkedin.com/in/johan-schalkwyk
- https://www.theinformation.com/briefings/meta-acquires-voice-ai-startup (PlayAI→reporta a Schalkwyk; réplicas: mlq.ai, hpcwire.com/aiwire 2025-07-16)
- https://the-decoder.com/meta-acquires-audio-ai-startup-waveforms-as-it-ramps-up-efforts-to-build-llama-4-5/ · digitalmusicnews.com 2025-08-11 · outlookbusiness.com (WaveForms ~$40M, Conneau)

**Podcast/produto [S]:**
- https://a16z.com/podcast/building-the-next-generation-of-conversational-ai/ (2025-03-14) · youtube.com/watch?v=bTcpNQH8ViQ · podwise.ai/dashboard/episodes/3320382 [F]
- https://x.com/testingcatalog/status/2059743513047093533 · techcrunch.com 2026-05-28
