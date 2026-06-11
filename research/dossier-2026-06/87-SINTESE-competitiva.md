# 87 — SÍNTESE COMPETITIVA (cruzamento das frentes 87–90)

> **Data:** 2026-06-10 · **Autor:** sintetizador-chefe TTS-ptbr
> **Insumos:** `87-elevenlabs-deep.md`, `88-inworld-voiceai.md`,
> `89-google-bigtech-voice.md`, `90-live-agents-arch.md` (+ cruzamento com
> `00-SYNTHESIS.md`, `10-sesame-csm.md`, `83-voice-orchestrators.md`).
> **Projeto:** melhor fala conversacional **pt-BR** nível **Maya/Sesame**
> (referência MAIOR), baixa latência, emoções, **sotaque carioca**.
> **Disciplina:** extrair **method/architecture/engineering** reaproveitável de
> concorrentes FECHADOS — **aprender, não copiar código**. Gate de licença DURO no
> PRODUTO: **Apache-2.0 / MIT / CC-BY / CC0**.
> **Marcação:** `[P]` fonte primária · `[S]` secundária · `[NV]` NÃO-VERIFICÁVEL
> (não inventar). Termos técnicos em **inglês**, explicação em português.

---

## 1. MAPA COMPETITIVO

Eixos: **architecture** (como o modelo gera fala) · **latency** (time-to-first-audio
ou voice-to-voice, sempre dizendo se é *model time* ou *end-to-end*) · **emotion**
(controle expressivo) · **cloning** (clonagem de voz) · **full-duplex** (fala e
escuta simultâneas, barge-in real) · **accent** (controle de sotaque) ·
**open/closed** (pesos/código).

| Player | Architecture | Latency | Emotion | Cloning | Full-duplex | Accent | Open/Closed |
|---|---|---|---|---|---|---|---|
| **Sesame / Maya** (ref MAIOR) | `native audio`: backbone Llama + audio decoder pequeno, tokens **text+audio interleaved**, tokenizer **Mimi** (split-RVQ 12.5Hz) [P] | baixa, decoder pequeno mantém end-to-end (sem ms oficial) [NV] | tom emocional ajustado entre turnos; aprendido dos dados [P] | in-context pelo **áudio de referência** | **meta declarada** (turn-taking implícito dos dados) [P] | **"match accents"** declarado [P] | **CSM-1B open (Apache)**; Maya completa fechada |
| **ElevenLabs** | `transformer diffusion` no áudio + **dual-input** (texto + voz-ref por encode/decode), backbone **[NV]** AR ou não-AR [P] | **Flash v2.5: 75ms model / 135ms TTFB**; Conv 2.0 first-turn <500ms; **cascading** (STT→LLM→TTS), duplex só em research [P] | **v3 audio tags** `[excited]`/`[whispers]`; stability slider; v3 **não streama** [P] | **IVC** zero-shot (~1–5min, conditioning) e **PVC** fine-tune (~3h, melhor range) [P] | **NÃO** em produção (trade-off reliability↔expressivity admitido) [P] | pt-BR default "neutro SP"; sotaque por prompt/marketing [P/NV] | **100% fechado** (SDKs/MCP no GitHub; zero pesos/paper) |
| **Inworld** | **LLM-based AR TTS** (`LLaSA-style`): backbone **LLaMA** (1B/8B) + codec **X-codec2** single-codebook 50tps + super-res 48kHz [P] | **~200ms TTFA** median (auto-reportado); TTS-2 sub-250ms P90 [S/NV] | **audio markups** (8 styles + 7 non-verbals); TTS-2: **NL voice direction** + conversational awareness [P/S] | herda voz por reference; few-shot | **[NV]** (TTS, não duplex; integra orquestradores) | pt na lista (`pt`); variante **[NV]** (carioca não documentado) | **código MIT** (sem pesos; **backbone LLaMA = licença Meta**, fora do gate) |
| **Voice.ai** | **RVC** (Retrieval-based Voice Conversion): HuBERT/ContentVec → FAISS top1 → VITS+NSF-HiFiGAN [S — fonte aberta RVC] | **~90–170ms** end-to-end (conversion, on-device) [S] | herda timbre da voz-alvo; **sem controle semântico** | **voice-to-voice** + clone ~10s; TTS secundário | **N/A** (voice changer, não conversa) | **N/A** (transfere timbre, não sotaque) | produto fechado **sobre RVC open** (não publicam pesos próprios) |
| **Google** | `native audio` (Gemini Live, speech-to-speech) — linhagem **AudioLM** (tokens semantic+acoustic) + **SoundStorm** (parallel non-AR MaskGIT, ~100× vs AR) [P] | **"very low latency"**, **sem ms oficial** [NV]; Live Translate "segundos atrás" preservando prosódia | **affective dialog** + audio tags inline (Gemini 3.1 Flash TTS, 200+ tags) [P] | **Chirp 3 Instant Custom Voice** (detalhe técnico não doc.) [P/NV] | **full-duplex** via WSS, barge-in por cancelamento (Gemini Live) [P] | pt-BR confirmado só no **Chirp 3 HD**; sotaque por prompt; **regional pt-BR não documentado** [P/NV] | **fechado** (papers SoundStorm/AudioLM abertos = método, sem pesos do produto) |
| **OpenAI** | `speech-to-speech` num único modelo (`gpt-realtime`), `[audio in]→GPT-4o→[audio out]` [P] | **TTFB ~500ms** (EUA); **alvo v2v ~800ms**; **~300ms** budget endpointing; 24kHz [S — Latent Space] | persona/emoção por **system instructions** (NL); barge-in afetivo | voz por preset (não clona arbitrário no Realtime) | **full-duplex** real: server VAD + barge-in por **cancel+truncate** [P] | sotaque por **instrução NL** (sem embedding exposto) [P] | **fechado** (protocolo Realtime documentado = método) |
| **→ TTS-ptbr (NÓS)** | `native audio` spine **Moshi/CSM** (Mimi split-RVQ) — mesma linhagem da ref; trilha A/B com Qwen3-TTS/Chatterbox-ptbr/Pocket | alvo **p50 v2v <800ms** Mac / **<600ms** GPU (a calibrar); hoje STT pós-turno = gap | base implícita + **GRPO paralinguístico** (moshika-rl-seamless) + tags inline | **zero-shot → fine-tune** voz do Pedro (~3h, valida o IVC/PVC) | **src/duplex** já tem silero-VAD + barge-in; **smart-turn v3 = próximo passo** | **accent embedding + intensidade** (carioca) — o diferencial | **100% aberto** (Apache/MIT/CC) por design |

**Onde nos posicionamos:** mesma **família arquitetural da referência** (native
audio / tokens interleaved, tokenizer split-RVQ), o que nos coloca no eixo certo.
Somos os **únicos 100% open** mirando **full-duplex + emoção + sotaque regional
pt-BR**. ElevenLabs nos ganha em qualidade de voz e data pipeline; Google em método
de latência (SoundStorm); Inworld em serving e em ter código aberto estudável.
**Ninguém ocupa nosso quadrante** (open + carioca controlável + conversacional).

---

## 2. APRENDIZADOS TÉCNICOS ACIONÁVEIS

> Só o que melhora NOSSO projeto. Cada item com fonte.

### 2.A — Adotar no `src/duplex` (Maya-BR) AGORA (barato, dentro do gate)

1. **`smart-turn v3.2` como 2º estágio de turn-taking** — hoje `turn_engine.py` é
   **silêncio puro** (`endpoint_ms`). Produção séria usa **VAD rápido (Silero) +
   classificador semântico de fim-de-turno**. smart-turn v3.2: **BSD-2** (cabe no
   gate), **ONNX 8MB, 12ms CPU, 23 línguas incl. português (95.42% acc)**, roda
   offline. Maior ROI da rodada. _Fonte: `90` §4.1 ·
   huggingface.co/pipecat-ai/smart-turn-v3 · daily.co/blog smart-turn-v3._
   ⚠️ acc é dataset deles, **não pt-BR carioca espontâneo** → gate de escuta nosso.
2. **Barge-in com `truncate` do contexto pelo ouvido** — ao interromper, **truncar
   o histórico do agente no ponto que o usuário DE FATO ouviu** (OpenAI
   `conversation.item.truncate`/`audio_end_ms`; ElevenLabs `AgentResponseCorrection`).
   Sem isso o agente "acha que falou" frases cortadas → contexto corrompido. Nosso
   barge-in hoje só corta o playback. _Fonte: `90` §1.3, §2.2._
3. **`prefix_padding_ms` parametrizado** no buffer de captura (não cortar o *attack*
   da 1ª palavra). Barato, melhora ASR. _Fonte: `90` §2.1 (server_vad)._
4. **`previous_text`/`next_text` (ou áudio-contexto no CSM) na síntese por sentença**
   — condiciona a prosódia do chunk atual no texto vizinho, evita "costura"
   audível entre sentenças. CSM já tem de graça (áudio-contexto); Pocket/Qwen3 é
   parâmetro a expor. _Fonte: `90` §1.4 (Flash v2.5)._
5. **`Concatenation at non-voicing regions`** — emendar chunks de áudio streamado nas
   **regiões não-vozeadas** (silêncio/pausas) elimina artefatos de junção. Truque de
   DSP barato, independe de modelo. _Fonte: `88` §1.2 (Inworld)._
6. **Métrica por percentil + `endpointing delay` como estágio explícito** — logar
   **p50/p95/p99** de voice-to-voice (nunca média) e escrever a meta
   **p50 v2v <800ms (Mac) / <600ms (GPU)** no `maya_parity.md`. Já logamos por
   estágio; falta agregar percentil e tornar o endpointing um estágio medido.
   _Fonte: `90` §5; `89` C.1._

### 2.B — Estudar para Trilha A/B (método de treino e modelo)

7. **`GRPO` com reward composto `WER + speaker-similarity + DNSMOS`** (RL alignment
   sem anotação humana extra) — receita concreta e barata pra alinhar "natural +
   inteligível + fiel". Casa com o `moshika-rl-seamless` (GRPO paralinguístico) já no
   `00-SYNTHESIS`. **Adotar no nosso pós-treino.** _Fonte: `88` §1.2 (Inworld TTS-1)._
8. **`accent embedding` + controle de intensidade (carioca)** — escola técnica da
   literatura aberta (ñ prompt): **(1)** áudio carioca rotulado; **(2)** extrair
   embedding via **WavLM/XLS-R** (self-supervised, casa com nossa stack);
   **(3)** condicionar o acoustic model; **(4)** **disentangle** timbre (Pedro) ×
   sotaque (carioca) estilo **MLVAE+adversarial**; **(5)** expor **coeficiente de
   intensidade [0, 2+]** sem re-treinar. _Fonte: `89` D.1/D.2 · arXiv 2508.07426
   "Scalable Controllable Accented TTS"._
9. **Codec single-codebook a baixa frame-rate (LLaSA/X-codec2, ~50tps)** → sequências
   curtas → latência baixa. Valida a escolha do Mimi (12.5Hz) na linhagem certa.
   _Fonte: `88` §1.2; `89` E (convergência Mimi/AudioLM)._
10. **`dual-input` por embedding de voz aprendido (sem features hard-coded de
    gênero/idade)** — deixar o modelo aprender o espaço de voz/estilo. Bom pra
    sotaque+emoção sem taxonomia rígida. _Fonte: `87` §2.1 (CEO ElevenLabs)._
11. **DATA PIPELINE é o moat, não a arquitetura** — rotular áudio com
    **transcript + emoção + non-verbals + speaker**, com **humanos (voice coaches)
    revisando o labeling**. CEO da ElevenLabs: *"data quality and labeling would be
    more defensible than model architecture alone"*. **Lição nº1.** Reflete no nosso
    protocolo de gravação/labeling. _Fonte: `87` §0, §2.1._

### 2.C — Técnicas de latência (engenharia de serving + inferência)

12. **Separação `SpeechLM ↔ audio decoder` com overlap/scheduling** — o gargalo de um
    TTS LLM-based **não é só o LLM**: o decoder fica ocioso esperando tokens. Desenhar
    o runtime antecipando esse descasamento de throughput; **silence-detection na GPU**
    e scheduler streaming-aware dão latência grátis (Inworld: ~1.6× speedup, ~200ms
    TTFA). Aprender o **padrão**, não depender do Modular/Mojo. _Fonte: `88` §1.3._
13. **`SoundStorm` (non-AR parallel, MaskGIT confidence-based)** — etapa **acústica**
    pode ser não-AR e paralela (~100× vs AR em sequências longas). Lição mesmo sem
    implementar: **minimizar passos AR na cadeia acústica; paralelizar os codebooks
    residuais.** _Fonte: `89` A.2.1 · arXiv 2305.09636._
14. **`Grouped Code Modeling` + `Repetition Aware Sampling` (VALL-E 2)** — agrupar
    códigos do codec encurta a sequência (acelera) e o sampling anti-repetição mata
    loops/alucinação acústica. Barato de portar sobre o spine. _Fonte: `89` C.2 ·
    arXiv 2406.05370._
15. **Princípios de pipeline (cascading enxuto):** streamar no **first-token** do LLM
    (não esperar a frase); **co-location** de STT/VAD/LLM/TTS na mesma região/GPU
    (fator dominante, confirma Modal do `83`); **`chunk_length_schedule`**
    (trade-off TTFB↔prosódia); **async function calling**. Âncoras: Flash 75ms model;
    Vapi enxuto ~465ms web; Retell ~580–620ms. _Fonte: `87` §2.4; `90` §1.1, §3._

### 2.D — Sotaque (resumo de método)

16. **Big tech faz sotaque por prompt/audio tags (black box, sem intensidade)** →
    pobre pra **regional**. A literatura aberta (item 8) dá **controle contínuo e
    reprodutível** via embedding+intensidade — **superior ao prompt** e é nosso
    diferencial. Sotaque vive cedo na cadeia (semantic + coarse acoustic), então o
    conditioning de sotaque deve entrar **cedo**. _Fonte: `89` D, A.2.2._

### 2.E — Clonagem (resumo de método)

17. **IVC (zero-shot, ~1–5min, conditioning no inference) → PVC (fine-tune, ~3h,
    melhor range emocional)** valida nossa **estratégia de 2 fases** e o **alvo ~3h**
    da voz do Pedro. Fraqueza conhecida do zero-shot: emoção forte fora do material
    de referência → justifica cobertura emocional no dataset. _Fonte: `87` §3._
18. **`FAISS top1 retrieval` (RVC) contra timbre leakage/oversmoothing** — estágio
    **opcional de voice-conversion** pós-TTS pra reforçar identidade da voz do
    Pedro/carioca com **≥10min** de áudio. Backup on-device leve se o TTS LLM-based
    for pesado pro edge. _Fonte: `88` §2.2._

---

## 3. O QUE NINGUÉM FAZ BEM (nossos gaps de oportunidade)

> **Tese a confirmar:** full-duplex + emoção + sotaque REGIONAL pt-BR + barato/open.

- **Full-duplex de verdade em produção é raro.** ElevenLabs **admite** que não
  entrega (cascading; duplex só em research, trade-off reliability↔expressivity).
  Google e OpenAI entregam full-duplex, mas **fechados**. A **referência Maya/Sesame**
  é a única open na linhagem certa, e ainda não-completa. → **CONFIRMA.** [P, `87` §0/§2.1]
- **Expressividade ↔ latência não estão unificadas** nem no 2º-melhor do mercado: o
  v3 (expressivo) **não streama**; o Flash (rápido) é menos expressivo. **Unificar é o
  gap.** → **CONFIRMA** (é exatamente nosso alvo). [P, `87` §2.3]
- **Sotaque REGIONAL pt-BR controlável NÃO existe aberto.** Big tech dá "pt-BR
  genérico" + prompt; agregadores (Notevibes/SpeechGen) citam carioca/paulista/
  nordestino **sem método publicado e sem abertura**. Sotaque carioca **controlável,
  com intensidade, open-weights, conversacional** = **território vazio**. → **CONFIRMA
  e AJUSTA**: o wedge não é "ter carioca", é **carioca controlável + intensidade +
  open**. [P, `89` D.2]
- **Re-síntese-com-pivô (speculative/incremental) não é commodity.** Produção faz só
  **streaming interleaved** (TTS no 1º token); regenerar do pivô no meio da frase é
  **fronteira de research** (RelayS2S, LTS-VoiceAgent), sem nada open pronto. →
  **CONFIRMA**: continua **nosso diferencial a construir** (os primitivos — word
  timestamps + cancelamento — existem; o loop é código nosso). [P/S, `90` §4.4]
- **Barato/open com qualidade:** "modelos menores batem foundation models" (ElevenLabs)
  e o spine open cabe em Colab → dá pra competir **sem cluster gigante**. → **CONFIRMA**
  o startup-mode. [P, `87` §0]

**Ajuste fino da tese:** mantida e reforçada. O quadrante defensável é
**open + carioca-controlável-com-intensidade + full-duplex conversacional + emoção**,
e a *peça mais difícil/única* é a combinação **full-duplex + re-síntese-com-pivô**,
não o sotaque isolado.

---

## 4. RISCOS / AMEAÇAS

- **Google com sotaques — ameaça MÉDIA, não imediata.** O "anúncio de sotaques"
  (Gemini 3.1 Flash TTS, abr/2026) é **prompt-based, sem intensidade**, e a doc
  primária **não confirma pt-BR** nem sotaque **regional brasileiro** (só Chirp 3 HD
  confirma pt-BR genérico). Eles têm o método (SoundStorm/AudioLM) e poderiam virar a
  chave, mas hoje **não entregam carioca controlável**. Risco real = **se** lançarem
  controle regional fino; mitigação = nosso embedding+intensidade open. [P/NV, `89` A.1/D.2]
- **ElevenLabs no Brasil — ameaça de PRODUTO, não técnica no nosso eixo.** Percebido
  como líder pt-BR por agregadores, mas default "neutro SP", **carioca não é foco**, e
  é **fechado/pago**. Não compete no quadrante open+regional. Sem benchmark
  independente pt-BR carioca (MOS/WER) → **gerar o nosso** (TTSDS2), não confiar em
  marketing. [P/S/NV, `87` §5]
- **Inworld — ameaça TÉCNICA de método (a mais relevante de aprendizado).** Código MIT
  estudável, serving SOTA (~200ms), GRPO publicado, **#1 Realtime TTS Arena**
  (auto-reportado). Mas: **TTS-2 aparenta API-only**, e o open (TTS-1) **depende de
  LLaMA (licença Meta)** → fora do nosso gate. Ameaça = elevam a régua de latência e
  expressividade; oportunidade = **reusar o método** trocando o backbone por um base
  **permissivo** (Qwen-Apache/OLMo). [P/S/NV, `88` §1.4/§1.5]
- **Plataformas de voice-agent (Vapi/Retell/Bland) — NÃO são concorrentes diretos.**
  Orquestram componentes de terceiros (cloud, BYO, fechado). Servem como **baseline de
  latência** a bater (~465–620ms), não como ameaça ao produto open pt-BR. [P, `90` §3/§8]
- **Risco interno (nosso):** STT **pós-turno** (faster-whisper segmentado) é o maior
  gap de latência vs o padrão "transcrever incrementalmente durante a fala". Reescrita
  não-trivial — atacar só quando virar gargalo medido. [P, `90` §1.1/§7]

---

## 5. [PRODUTO/BUSINESS — não poluir startup mode]

> Só listado, sem análise. Revisitar no `/office-hours`.

- ElevenLabs: valuation ~$6.6B, receita >$200M; R&D Varsóvia + escritório Índia;
  cultura FDE (herança Palantir); anjo Mustafa Suleyman; "voz será a interface
  fundamental"; líder pt-BR percebido (agregadores). [`87` §7]
- Inworld: funding >$125M (Lightspeed, Microsoft M12, Meta, Samsung NEXT…); pivô
  NPC→voz realtime; integrações Layercode/LiveKit/Pipecat/Vapi/Voximplant. [`88` §1.1/§1.4]
- Voice.ai: funding $6M (2023, Mucker/M13), ~500k users via gaming/streaming; founder
  ex-iSpeech; mercado voice-changer de consumo distinto do nosso. [`88` §2.1]
- Google: Gemini 3.1 Flash TTS abr/2026; novas vozes Live (Flare/Glow, mai/2026);
  Gemini 3.5 Live Translate (jun/2026); SynthID watermark em toda saída. [`89` A.1/B.2]
- Mercado voice-agent muito quente em 2026; sub-600ms é o estado-da-arte de produção;
  Hamming (4M chamadas) diz que a **mediana real de mercado é ~1.5–1.7s** (vendor
  benchmark ≠ produção sob carga). [`90` §5.3, §8]
- Pricing/serving: Inworld alega 60% mais barato que vLLM; ElevenLabs Flash 50% mais
  barato/char. [`88` §1.3; `87` §2.2]

---

## RESUMO EXECUTIVO (≤22 linhas)

1. Estamos na **família arquitetural certa** (native audio / tokens interleaved /
   split-RVQ Mimi) — a mesma da referência Maya/Sesame; ninguém open ocupa nosso
   quadrante (open + carioca controlável + full-duplex + emoção).
2. **Maior fato:** mesmo o 2º-melhor do mercado (ElevenLabs) **NÃO entrega full-duplex
   em produção** e **não unificou expressividade↔latência** (v3 expressivo não streama;
   Flash rápido é menos expressivo). Nosso alvo é exatamente esse gap. [`87`]
3. **Ação nº1 AGORA:** plugar **smart-turn v3.2** (BSD-2, ONNX 8MB, 12ms CPU, pt
   95.4%) como 2º estágio do `turn_engine` — hoje é silêncio puro. Maior ROI. [`90`]
4. **Ação nº2 AGORA:** barge-in com **truncate do contexto pelo ponto ouvido**
   (`item.truncate`/`AgentResponseCorrection`) — senão o histórico corrompe. [`90`]
5. **Ações rápidas:** `prefix_padding_ms`, `previous_text/next_text` na síntese por
   sentença, concatenação em regiões não-vozeadas, percentis p50/p95 + meta
   **p50 v2v <800ms Mac / <600ms GPU**. [`87`,`88`,`90`]
6. **Treino (Trilha A/B):** adotar **GRPO com reward WER+speaker-sim+DNSMOS**
   (Inworld) — casa com o moshika-rl-seamless; e o moat real é o **data/labeling
   pipeline** (voice coaches), não a arquitetura (CEO ElevenLabs). [`87`,`88`]
7. **Sotaque carioca = accent embedding (WavLM/XLS-R) + intensidade + disentangle
   timbre×sotaque (MLVAE)**, NÃO prompt. É o método aberto que a big tech não entrega;
   diferencial defensável e reproduzível. [`89`]
8. **Latência (método):** separar SpeechLM↔decoder com overlap (Inworld); etapa
   acústica non-AR/paralela (SoundStorm); grouped-code + repetition-aware sampling
   (VALL-E 2); streamar no first-token + co-location. [`88`,`89`]
9. **Tese CONFIRMADA e ajustada:** o wedge não é "ter carioca", é **carioca
   controlável-com-intensidade + open + full-duplex + emoção**; a peça mais
   única/difícil é **full-duplex + re-síntese-com-pivô** (fronteira, nada open pronto). [`90`]
10. **Ameaças:** Google poderia ligar sotaque regional (hoje só prompt, sem pt-BR
    regional confirmado) — média; ElevenLabs no BR é ameaça de produto/pago, não do
    nosso eixo open+carioca; Inworld eleva a régua técnica mas o open deles depende de
    LLaMA (fora do gate) → reusar método com backbone permissivo. [`87`,`88`,`89`]
11. **Gate de escuta obrigatório:** nenhum claim de pt-BR/carioca (smart-turn,
    Inworld, Chirp 3, ElevenLabs) está verificado em **carioca espontâneo** — validar
    no nosso eval (TTSDS2) antes de confiar; marketing ≠ medida.
12. **Achados de produto/preço/GTM** ficam isolados na §5 para o `/office-hours` — não
    poluem o foco de engenharia.
