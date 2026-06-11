# FRENTE 4 — Arquitetura de AGENTES DE VOZ ao vivo em produção (2026-06-10)

> **Foco: ENGENHARIA de produção real-time.** Como ElevenLabs, OpenAI Realtime,
> Vapi/Retell/Bland e os frameworks (Pipecat/LiveKit) montam o pipeline voz-a-voz
> de verdade — turn-taking, barge-in, endpointing, streaming, protocolo de
> websocket, breakdown de latência por componente — para **refinar o `src/duplex`
> (Maya-BR)**. Esta frente **não decide** se adotamos Pipecat (isso já está em
> `83-voice-orchestrators.md`: "não migrar agora, convergir p/ Pipecat no v0.3");
> ela **confirma e refina** essa decisão com detalhes de produção e me dá uma
> lista do que copiar de método AGORA vs DEPOIS.
>
> Disciplina: extrair **método/arquitetura reaproveitável**, não fofoca. Tudo com
> URL primária; o que não for verificável está marcado **[NÃO VERIFICÁVEL]**.
> Estamos só APRENDENDO com concorrentes fechados — nenhum código é copiado; o
> produto continua sob gate de licença dura (Apache/MIT/CC-BY/CC0).

---

## TL;DR — o que adotar no `src/duplex` (resumo de engenharia)

1. **Turn-taking de produção é cascata em 2 estágios, não silêncio puro.** Todos os
   sérios (ElevenLabs, OpenAI semantic_vad, LiveKit, Pipecat, Retell) usam
   **VAD rápido (Silero) + um classificador semântico de fim-de-turno** por cima.
   Nosso `turn_engine.py` hoje é silêncio puro (`endpoint_ms=600`). **Ação #1:
   plugar smart-turn v3 como 2º estágio** — pesos+dados BSD-2, ONNX 8MB,
   **12ms CPU**, **23 línguas incluindo português (95.42% acc)**. É o único
   componente SOTA de endpointing que cabe no nosso gate de licença E roda offline.
2. **Barge-in = cancelamento de pipeline + truncamento do contexto pelo ponto
   ouvido.** O detalhe que faltava no nosso loop: ao interromper, **truncar o
   histórico do agente no `audio_end_ms` que o usuário de fato ouviu** (OpenAI
   `conversation.item.truncate`; ElevenLabs `AgentResponseCorrection`). Sem isso,
   o agente "acha que falou" frases que foram cortadas → contexto corrompido.
   Já tínhamos issue análoga citada no Pipecat (#2791). **Ação #2.**
3. **Latência boa em 2026, voz-a-voz**: ~**800ms mediana** é o alvo de mercado
   (regra Daily); **sub-600ms** é o estado-da-arte de produção (Retell ~580-620ms;
   Vapi enxuto ~465ms web). **>800ms = "Zoom moment"** (o usuário acha que caiu a
   linha). Mede-se por **percentil (p50/p95/p99)**, nunca média, e por **estágio**.
4. **Speculative/incremental TTS em produção é raro e ainda imaturo**; o que TODO
   mundo faz é **streaming interleaved** (TTS começa no 1º token do LLM). A
   re-síntese-com-pivô que queremos é fronteira (papers RelayS2S/LTS-2026), não
   commodity — continua sendo **nosso diferencial a construir** (alinha com `83`).
5. **Protocolo de websocket**: o padrão de evento de produção (ElevenLabs/OpenAI)
   é nosso melhor blueprint para quando o `src/duplex` ganhar cliente remoto.
   **Espelhar os nomes de evento** desde já (custo ~zero) deixa a migração barata.

---

## 1. ElevenLabs Agents / Conversational AI — engenharia espelhável

**Fontes primárias:**
- Blog latência: https://elevenlabs.io/blog/how-do-you-optimize-latency-for-conversational-ai
- Protocolo WS: https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket
- Flash v2.5: https://elevenlabs.io/blog/meet-flash · https://elevenlabs.io/docs/overview/models
- Latency optimization: https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization

### 1.1 Breakdown de latência por componente (números do vendor)
O blog deles é, de longe, o documento mais útil porque **publica o orçamento de
latência por estágio** — exatamente a tabela A do nosso `maya_parity.md`:

| Estágio | Como medem | Número publicado |
|---|---|---|
| **ASR** (fim-da-fala→texto) | custom STT | **<100ms** (custom); Whisper OSS "300ms+" |
| **Turn-taking/VAD** | threshold de silêncio + delay humano deliberado | não divulgam o ms |
| **LLM** (time-to-first-token) | depende do modelo | Gemini Flash **<350ms**; GPT-4/Claude **700-1000ms** |
| **TTS** (TTFB) | Flash v2.5 | **75ms model time / 135ms end-to-end**; Turbo (geração anterior) ~300ms |
| **Telefonia** | rede | **200ms** mesma região; **~500ms** global |

**Método reaproveitável:**
- **O ASR roda em background DURANTE a fala do usuário** (streaming), então a
  latência "fim-da-fala→texto" é só a cauda. Nosso `chat_loop` hoje transcreve
  **depois** do turno fechar (faster-whisper segmentado) — é o nosso maior gap de
  latência. **Não dá p/ copiar trivialmente** (faster-whisper não é token-a-token),
  mas o padrão "transcrever incrementalmente enquanto fala" é o alvo.
- **Co-localizar todos os componentes** (mesma região/GPU) — confirma o achado do
  Modal no `83` (proximidade GPU↔cliente foi o fator dominante p/ ~1s voz-a-voz).
- **Escolha de LLM domina o p50.** Trocar o modelo é a alavanca de latência mais
  barata. Nosso `llm_bench.py` já existe pra isso — manter a disciplina.

### 1.2 Turn-taking model (proprietário, mas a ideia é clara)
"Real-time detection of pauses, overlaps, and speech intent" + **turn eagerness
configurável** (quão rápido interpreta uma pausa como vez de responder). Não é só
silêncio: é **intenção de fala**. É a mesma família do smart-turn / semantic_vad.
**[NÃO VERIFICÁVEL]** a arquitetura interna do modelo deles (fechado).

### 1.3 Protocolo WebSocket — blueprint de eventos (espelhar)
Endpoint `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=...`. Eventos que
importam pro nosso desenho de protocolo futuro:

**Servidor→cliente:** `ConversationInitiationMetadata` (formatos de áudio),
`UserTranscript`, `InternalTentativeAgentResponse` (texto preliminar do agente —
**útil p/ especulação**), `AgentResponse`, `AudioResponse` (áudio base64 **+
alignment char-level**: chars/durations/start_times — isso é lip-sync/karaokê e
serve p/ saber **exatamente onde a fala parou** num barge-in), **`Interruption`**
(referencia o `event_id` do áudio cortado), **`AgentResponseCorrection`**
(`original` vs `corrected` — o **truncamento do contexto** após interrupção),
`VadScore` (0-1), `Ping`/`Pong` com `ping_ms`.

**Cliente→servidor:** `UserAudioChunk` (base64), `Pong`, `ContextualUpdate`
(injeta contexto **sem interromper** — padrão elegante p/ RAG/estado),
`ClientToolResult`, `UserActivity`.

**Lições de engenharia:**
- **`AgentResponseCorrection` é a prova viva da Ação #2**: produção SÉRIA corrige
  o histórico textual do agente pelo que foi *de fato* reproduzido. Replicar.
- **`alignment` char-level** dá o ponto de corte exato no barge-in — é o primitivo
  que a nossa **re-síntese-com-pivô** precisa (saber em que palavra/char parou).
  Nosso TTS local (Pocket/CSM) precisa expor timestamps por palavra p/ isso.
- **`ContextualUpdate` (não-interruptivo)** é um padrão que vale ter no `src/duplex`:
  empurrar fatos novos pro contexto sem cortar a fala.

### 1.4 Flash v2.5 — engenharia de streaming TTS
75ms é **só model time**; o "135ms end-to-end" inclui aplicação+rede. Para prosódia
contínua entre chunks, a API aceita **`previous_text`/`next_text`** (ou
`previous_request_id`/`next_request_id`) — o modelo condiciona a entonação do chunk
atual no texto vizinho. **Lição direta p/ nosso TTS por sentença**: quando tocamos
sentença-a-sentença (TODO do `chat_loop` v0.1), passar a sentença anterior/seguinte
como contexto evita a "costura" prosódica audível. CSM já tem isso de graça (áudio-
contexto); para Pocket/Qwen3 é um parâmetro a expor.

---

## 2. OpenAI Realtime API — o protocolo de referência

**Fontes primárias:**
- VAD/turn detection: https://developers.openai.com/api/docs/guides/realtime-vad
- Conversas/interrupção: https://developers.openai.com/api/docs/guides/realtime-conversations
- Server events: https://developers.openai.com/api/reference/resources/realtime/server-events

### 2.1 Turn detection: server_vad vs semantic_vad
Configurado em `session.audio.input.turn_detection`. Emite
`input_audio_buffer.speech_started` e `...speech_stopped`.

- **`server_vad`** (default): chunking por silêncio, 3 params —
  - `threshold` (0-1): mais alto = exige fala mais alta (ambiente ruidoso);
  - `prefix_padding_ms`: quanto áudio incluir ANTES do início detectado (não
    cortar o ataque da palavra) — **temos isso implícito no nosso buffer, mas não
    parametrizado**;
  - `silence_duration_ms`: silêncio p/ marcar fim — equivalente ao nosso
    `endpoint_ms=600`. Menor = turnos mais rápidos, mais risco de cortar pausa.
- **`semantic_vad`**: um **classificador semântico** dá a probabilidade de o
  usuário ter terminado **pelo conteúdo da fala**, e aplica um timeout proporcional.
  "Áudio que termina em 'ummm…' → prob baixa → espera mais." **Eagerness**:
  `low` (espera mais), `medium`/`auto`, `high` (corta rápido). **Este é o conceito
  central a importar**: fim-de-turno é semântico, não acústico. (No nosso caso, o
  smart-turn v3 é a versão open desse classificador — §4.)

### 2.2 Barge-in / truncamento (a parte que mais nos ensina)
- Com **WebSocket**, o **cliente** gerencia playback e DEVE detectar
  `input_audio_buffer.speech_started` p/ saber que houve interrupção (é o nosso
  caso: somos o cliente do playback). Com **WebRTC/SIP**, o servidor faz o
  truncamento automático.
- O passo crítico: cliente envia **`conversation.item.truncate`** com o
  `item_id` da última resposta e **`audio_end_ms`** = quanto o usuário **de fato
  ouviu** → "remove a porção não reproduzida da resposta do conversation". **Sem
  esse passo, o modelo guarda no histórico texto que nunca foi ouvido.** É
  literalmente a Ação #2 do nosso TL;DR, no protocolo de referência da indústria.
- `interrupt_response`/`create_response` (booleans): controlam se um `speech_started`
  do VAD **cancela automaticamente** a resposta em curso e se dispara nova resposta.
  Mapeia 1:1 no nosso `player.stop()` + reentrada em LISTENING.

### 2.3 Function calling durante a fala
`response.function_call_arguments.delta` (streaming dos argumentos) →
`response.done` traz `call_id`+JSON → cliente executa →
`conversation.item.create` com `function_call_output`. **Lição**: tool-calls são
**streamados** e resolvidos sem travar o turno; o resultado volta como item de
conversa. Para o Maya-BR isso só importa quando adicionarmos ferramentas; por ora,
registrar o padrão.

### 2.4 WebRTC vs WebSocket (decisão de transporte)
- **WebRTC**: browser cuida do media stream; **servidor gerencia o buffer de áudio
  e o truncamento** (menos código no cliente); melhor p/ rede instável. Saída via
  media stream remoto.
- **WebSocket**: controle total, melhor server-to-server, **buffer manual**; áudio
  via `response.output_audio.delta` (base64). Formatos: `pcm16` 24kHz
  (recomendado), `g711`/`pcmu` (telefonia µ-law).
- **Para nós**: localhost = nem precisa (somos in-process). Cliente web futuro:
  **FastRTC/WebRTC** poupa o trabalho de truncamento manual — bate com a sugestão
  "FastRTC na frente do `src/duplex`" do `83`.

---

## 3. Plataformas de voice-agent (Vapi / Retell / Bland) — números e padrões

> Estas são **plataformas** (orquestram STT/LLM/TTS de terceiros), não frameworks
> que rodaríamos local. O valor aqui é **número de latência de produção** e
> **como resolvem turn-taking/barge-in**. Tudo fechado → método, não código.

### 3.1 Retell AI — o melhor turn-taking publicado
- **Turn Taking Engine proprietário** que, segundo reviews independentes, lida com
  barge-in "melhor que quase todo mundo": reconhece **tom, pausas e padrões de
  frase** (não só fronteiras de fala do VAD). No barge-in, "parou, reconheceu a
  interjeição e **retomou sem repetir a frase anterior**" — isso é exatamente o
  comportamento que a Ação #2 (truncar pelo ouvido) habilita.
- **Latência ~580-620ms voz-a-voz** medida em 180-200+ chamadas (review Coval/Retell).
  É o **estado-da-arte de produção** que vi com número. Transporte WebRTC.
- Fontes: https://www.retellai.com/blog/why-low-latency-matters-how-retell-ai-outpaces-traditional-players
  · https://www.coval.ai/blog/retell-ai-review-2026-features-pricing-and-when-to-use-it
  **[NÃO VERIFICÁVEL]** a arquitetura interna do Turn Taking Engine (fechado).

### 3.2 Vapi — latência é função do stack que você monta
- Vapi é "BYO componentes". Stack enxuto **Deepgram + GPT-4o-mini + Cartesia →
  500-700ms**; config ultra-otimizada (AssemblyAI Universal-Streaming + Groq Llama4
  + ElevenLabs Flash) → **~465ms web**. Breakdown publicado (AssemblyAI):

  | Componente | Tech | ms |
  |---|---|---|
  | STT | AssemblyAI Universal-Streaming | **90** |
  | LLM | Groq Llama 4 Maverick 17B | **200** (TTFT) |
  | TTS | ElevenLabs Flash v2.5 | **75** (TTFB) |
  | Pipeline | soma | **365** |
  | Rede (WebRTC web) | | **100** |
  | **Total** | | **~465** |

- **Pegadinha de produção (importante p/ nós):** os **defaults de turn detection
  do Vapi adicionam 1.5s+** (`On No Punctuation Seconds: 1.5s`,
  `Wait Seconds: 0.4s`, `On Punctuation: 0.1s`). Ou seja: **o endpointing mal
  configurado é o maior vilão de latência percebida**, não os modelos. Nosso
  `endpoint_ms=600` é um meio-termo; com smart-turn semântico dá p/ baixar o
  silêncio fixo e deixar o classificador decidir.
- Fontes: https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi
  · https://vapi.ai/blog/speech-latency

### 3.3 Bland AI — sem número primário confiável
Não achei breakdown técnico de latência em fonte primária da Bland nesta rodada
(material disponível é majoritariamente marketing/comparativo de terceiros).
**[NÃO VERIFICÁVEL]** — não inventar números. Padrão arquitetural é o mesmo
(STT→LLM→TTS orquestrado com turn-taking proprietário + telefonia).

### 3.4 O denominador comum (o que TODOS fazem)
1. **Staged streaming**: STT streama durante a fala → no fim-de-fala manda o texto
   acumulado pro LLM, que **já começa a gerar** → TTS começa **no 1º token**.
2. **Barge-in = detectar fala + cortar TTS em ~200ms** + truncar contexto.
3. **VAD com 300-500ms de silence threshold** como 1º estágio; turn-taking
   semântico por cima nos melhores.
4. **<800ms** é o limiar de naturalidade; **>800ms = "Zoom moment"**.

---

## 4. Turn detection / endpointing SOTA 2026 (o coração desta frente)

> Esta é a seção mais acionável. Há **dois modelos abertos** de fim-de-turno que
> importam, com **abordagens opostas** — e um deles cabe no nosso gate de licença.

### 4.1 smart-turn v3 / v3.2 (Pipecat/Daily) — **AUDIO-based, BSD-2, cabe no gate**
- **Arquitetura**: base **Whisper Tiny** (encoder, 39M) + **camada linear de
  classificação** → **~8M params efetivos**, int8 via QAT, **ONNX 8MB** (~50x menor
  que v2). Analisa **a waveform crua, NÃO o transcript** → independe do STT e pega
  prosódia (entonação ascendente = "ainda falando").
- **Latência CPU**: **12ms** (c7a.2xlarge), 60ms (instância barata), ~95ms (t3.medium).
  Inclui ~3ms de pré-processamento. **Não precisa de GPU.**
- **23 línguas incluindo PORTUGUÊS**: acc **95.42%** em pt (FP 2.79% / FN 1.79%,
  1.398 amostras). Range geral 81% (vietnamita) a 97% (turco).
- **v3.2 (07/jan/2026)**: drop-in do v3.1; **−40% de erro em respostas curtas**
  ("sim", "ok") e robustez a ruído de café/escritório (datasets novos). Variante
  CPU 8MB / GPU 32MB.
- **Como se usa**: **2º estágio depois do Silero VAD** — VAD diz "tem fala/parou de
  falar", smart-turn diz "esse silêncio é fim-de-turno OU só uma pausa?".
- **Licença**: **pesos + dados + script de treino abertos (BSD-2)** → compatível
  com nosso gate. **É o único endpointing semântico SOTA que podemos embarcar.**
- Fontes: https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/
  · https://www.daily.co/blog/smart-turn-v3-2-handling-noisy-environments-and-short-responses/
  · https://huggingface.co/pipecat-ai/smart-turn-v3 · https://github.com/pipecat-ai/smart-turn

### 4.2 LiveKit turn detector — **TEXT-based, mais preciso, licença restritiva**
- **Arquitetura**: LLM **Qwen2.5-0.5B-Instruct** (student) destilado de um teacher
  **Qwen2.5-7B-Instruct**. **Processa o TEXTO do STT, não o áudio** → usa
  conteúdo+contexto da conversa; **não capta prosódia/pausas** (limitação assumida).
- **Multilíngue incl. português**: 14 línguas; em **pt o erro caiu 45.97%**
  (23.3%→12.6%). v0.4.1-intl: **−39.23% de falsos-positivos de interrupção**, sem
  latência extra. (Outras fontes citam ~25ms e ~400MB RAM — **[NÃO VERIFICÁVEL]** no
  blog primário, que não dá o ms/RAM.)
- **Licença**: **"LiveKit Model License"** (pesos), **fora do nosso gate** e atrelada
  ao uso com LiveKit Agents (já registrado no `83`). **Não embarcar; só aprender.**
- Fontes: https://livekit.com/blog/improved-end-of-turn-model-cuts-voice-ai-interruptions-39
  · https://huggingface.co/livekit/turn-detector

### 4.3 A escolha de engenharia para o `src/duplex`
**audio-based (smart-turn) > text-based (LiveKit) PARA NÓS**, por 3 razões:
1. **Licença**: smart-turn é BSD-2; LiveKit é proibido no produto.
2. **Não depende do STT**: roda em paralelo ao faster-whisper, não DEPOIS dele —
   economiza a latência do transcript no caminho crítico do endpointing.
3. **Pega prosódia** (entonação de pergunta, hesitação) que o text-based perde — e
   prosódia é central no pt-BR carioca (curva melódica forte).
   **Trade-off honesto**: text-based entende "frases incompletas semanticamente"
   melhor (ex.: "eu acho que..."). O ideal teórico é **fundir os dois sinais**, mas
   p/ v0.2 o smart-turn sozinho já é um salto enorme sobre silêncio puro.

### 4.4 Re-síntese incremental / speculative TTS em produção — **ainda não é commodity**
- O que **todo mundo em produção faz** é **streaming interleaved** (TTS no 1º token
  do LLM) — isso reduz **time-to-first-audio**, mas **não regenera** a fala já
  emitida. Ninguém em produção aberta documenta "re-sintetizar do pivô no meio da
  frase".
- **Speculative/predictive** existe como **técnica avançada e ainda rara**: gerar
  resposta a partir de transcrição parcial (antes do fim do turno) e descartar se a
  intenção final não bater; pré-gerar áudio provável e tocar de cache se acertar.
  Em produção isso aparece mais como otimização pontual que como padrão estável.
- **Fronteira (research, não produção)**:
  - **RelayS2S** (arXiv 2603.23346): **dual-path** — modelo TTS leve gera "draft"
    especulativo em paralelo; modelo pesado verifica e troca p/ o áudio final
    quando pronto. Reduz latência percebida. **É pesquisa com código, não deploy.**
  - **LTS-VoiceAgent** (arXiv 2601.19952): framework "Listen-Think-Speak" com
    gatilho semântico + raciocínio incremental p/ streaming.
- **Conclusão (bate com o `83`)**: a **re-síntese-com-pivô continua sendo NOSSO
  diferencial a construir** — não há nada pronto open p/ copiar. Os **primitivos**
  de que precisamos (timestamps por palavra p/ saber o ponto de corte; cancelamento
  de pipeline) existem; o **loop "regenera do pivô"** é código nosso.
- Fontes: https://arxiv.org/pdf/2603.23346 · https://arxiv.org/html/2601.19952v1
  · https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture

---

## 5. Métricas de latência de produção 2026 — o que é "bom" e como medir

**Fontes:** https://www.coval.ai/blog/how-to-measure-voice-ai-latency-the-complete-guide
· https://hamming.ai/resources/voice-agent-evaluation-metrics-guide
· https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/ (regra 800ms, já no `83`)

### 5.1 Definição canônica
**Voice-to-voice latency** = atraso entre **o usuário PARAR de falar** e **o agente
COMEÇAR a falar**. Sempre medida por **percentil** (p50/p95/p99), nunca média
("média esconde os outliers"). Quatro estágios instrumentados separadamente:
**STT → LLM (TTFT) → TTS (TTFB) → rede**.

### 5.2 Números-alvo por componente (consolidado, 2026)
| Componente | Alvo "bom" 2026 | Observação |
|---|---|---|
| STT (fim-fala→texto) | <200ms streaming | batch = 500-1500ms (evitar) |
| LLM TTFT | <400ms (rápido) | modelos grandes 1.5-3s |
| TTS TTFB/TTFA | <150ms | Flash v2.5 = 75ms model |
| **Voz-a-voz p50** | **<800ms** (alvo mercado) | <600ms = SOTA produção |

### 5.3 O que é "bom" voz-a-voz (consolidado, com a tensão entre fontes honesta)
- **Regra de mercado / Daily**: **800ms mediana** é o alvo; **>800ms = "Zoom
  moment"** (usuário acha que a linha caiu).
- **SOTA de produção medido**: Retell **~580-620ms**; Vapi enxuto **~465ms** (web).
- **TENSÃO HONESTA**: a Hamming, analisando **4M+ chamadas reais**, diz que a
  **mediana de mercado REAL é 1.5-1.7s** (5x pior que os 300ms humanos) e recomenda
  alvo **p50 <1.5s / p95 <5s** p/ cascata. Ou seja: **os ~500ms são o que os
  melhores stacks atingem em condições ótimas; a realidade média operacional é
  ~1.5s.** Não confundir benchmark de vendor com produção sob carga.
- Cascata (STT→LLM→TTS) total típico **1.4-2.6s**; speech-to-speech **0.9-2.0s**.
- Fonte: https://hamming.ai/resources/how-to-evaluate-voice-agents-2026

### 5.4 Onde o `src/duplex` está nesse mapa
Já logamos por estágio (`asr`, `llm₁`, `tts₁`, `total→1ºaudio`) no `chat_loop.py` —
**arquitetura de medição correta**. Faltam: (a) **endpointing delay** como estágio
explícito (hoje embutido no `listen_turn`); (b) **percentis** (logamos por turno,
não agregamos p50/p95); (c) o número-alvo escrito: **mirar p50 voz-a-voz <800ms no
Mac, <600ms no servidor GPU** como meta Maya-BR v0.2.

---

## 6. Mapeamento direto: cada concorrente → uma linha do `src/duplex`

| O que eles fazem | Onde bate no nosso código | Status |
|---|---|---|
| Endpointing semântico (semantic_vad/smart-turn) | `turn_engine.py` (hoje silêncio puro) | **adotar smart-turn v3 (Ação #1)** |
| Truncar contexto pelo ouvido (`item.truncate`/`AgentResponseCorrection`) | `chat_loop.py` no barge-in | **adotar (Ação #2)** |
| `prefix_padding_ms` (não cortar ataque) | `turn_engine` buffer | parametrizar |
| Word-level alignment p/ ponto de corte | `tts_adapter` (expor timestamps) | pré-requisito da re-síntese |
| `previous_text`/`next_text` p/ prosódia entre chunks | `tts_adapter` síntese por sentença | adotar no streaming v0.1 |
| STT streaming durante a fala | `asr.py` (hoje pós-turno) | **gap; difícil c/ faster-whisper** |
| Métrica por percentil p50/p95 | logging do `chat_loop` | agregar (fácil) |
| `ContextualUpdate` não-interruptivo | futuro (RAG/estado) | registrar padrão |
| Speculative/re-síntese-com-pivô | nosso diferencial | **construir (fronteira)** |

---

## 7. O QUE ADOTAR — agora vs depois (a entrega desta frente)

### AGORA (v0.2, Mac local — barato, dentro do gate, alto impacto)
1. **smart-turn v3.2 como 2º estágio do `turn_engine`** (BSD-2, ONNX 8MB, 12ms CPU,
   pt 95.4%). Silero VAD detecta fala/silêncio → smart-turn decide fim-de-turno.
   Baixa o `endpoint_ms` fixo e mata cortes de pausa. **Maior ROI da frente.**
2. **Truncamento de contexto no barge-in**: ao cortar o playback, registrar quantos
   ms/quais sentenças foram REALMENTE ouvidas e truncar o histórico do agente nesse
   ponto (espelha `conversation.item.truncate` / `AgentResponseCorrection`).
3. **`prefix_padding_ms` parametrizado** no buffer de captura (não cortar o ataque
   da 1ª palavra) — barato, melhora ASR.
4. **Agregar percentis** (p50/p95) no log de latência + escrever a meta
   **p50 voz-a-voz <800ms** no `maya_parity.md`. Adicionar **"endpointing delay"**
   como estágio explícito.
5. **`previous_text`/`next_text`** (ou áudio-contexto, no CSM) na síntese por
   sentença p/ continuidade prosódica quando ligarmos o streaming por sentença.

### DEPOIS (v0.3+, servidor GPU / cliente remoto — alinhado ao `83`)
6. **Adotar Pipecat** como transporte/orquestração (já é a recomendação do `83`):
   ele **já traz smart-turn v3 nativo** + observers de latência + cancelamento de
   pipeline + `MinWordsUserTurnStartStrategy` (distingue backchannel de barge-in).
   Portar nosso CSM-adapter como `TTSService` e a re-síntese como FrameProcessor.
7. **Transporte WebRTC/FastRTC** p/ cliente web — ganha truncamento server-side de
   graça (lição OpenAI Realtime). Espelhar nomes de evento (ElevenLabs/OpenAI)
   desde já no protocolo interno.
8. **Re-síntese-com-pivô** (nosso diferencial): construir sobre os primitivos
   (word-timestamps + cancelamento). Estudar RelayS2S (dual-path draft/verify) como
   inspiração de método, **não como dependência**.
9. **STT streaming token-a-token** (substituir faster-whisper pós-turno) — só quando
   virar gargalo medido; é reescrita não-trivial.

### NÃO adotar
- **LiveKit turn detector** (pesos com licença restritiva — fora do gate; usar
  smart-turn no lugar).
- **Plataformas Vapi/Retell/Bland** como dependência (fechadas, cloud, BYO — são
  fonte de método/números, não de código). Servem como **baseline de latência**
  (~500-600ms) a bater.
- **Speculative TTS pré-emptiva agressiva** agora — imatura e cara; o ganho real
  hoje vem do streaming interleaved simples, que já temos no caminho.

---

## 8. Achados de PRODUTO/BUSINESS (separados — NÃO poluir o foco de engenharia)
> Mantidos aqui só p/ não se perderem; **não são tarefa desta frente.**
- ElevenLabs, Retell, Vapi, Bland são **plataformas comerciais fechadas** (cloud,
  preço por minuto). Mercado de voice-agent muito quente em 2026, mas **não é
  concorrente direto do nosso produto** (TTS pt-BR open, voz própria). Ignorar p/ o
  foco de startup-mode.
- "Sub-200ms"/"75ms" de vendors são **model time**, não end-to-end — sempre ler a
  letra miúda (já tratado em rodadas anteriores p/ Chatterbox).

---

## 9. Honestidade / o que NÃO foi verificado
- **Arquitetura interna** dos turn-taking proprietários (ElevenLabs, Retell Turn
  Taking Engine) — **fechada, [NÃO VERIFICÁVEL]**. Extraí só o comportamento
  observável e os números publicados.
- **Bland AI**: sem breakdown de latência em fonte primária nesta rodada — não
  inventei número.
- **LiveKit turn detector**: ms/RAM (~25ms/~400MB) vieram de fonte secundária; o
  blog primário não confirma esses números (confirma só base model, línguas, −39%).
- **smart-turn pt 95.42%** é acc em dataset deles, não em pt-BR carioca espontâneo —
  **gate de escuta/teste nosso** antes de confiar (mesma disciplina do resto do
  dossiê). A bandeira no card é 🇵🇹, mas o modelo é treinado multilíngue; **testar
  com áudio pt-BR real** é obrigatório.
- Números de latência de Vapi/Retell são de **reviews/benchmarks de terceiros ou do
  próprio vendor** em condições ótimas — a contraprova Hamming (4M chamadas, p50
  real ~1.5s) está registrada em §5.3.

---

## 10. Fontes primárias (consolidado)
- ElevenLabs latência: https://elevenlabs.io/blog/how-do-you-optimize-latency-for-conversational-ai
- ElevenLabs WS: https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket
- ElevenLabs Flash: https://elevenlabs.io/blog/meet-flash · https://elevenlabs.io/docs/overview/models
- OpenAI Realtime VAD: https://developers.openai.com/api/docs/guides/realtime-vad
- OpenAI Realtime conversas: https://developers.openai.com/api/docs/guides/realtime-conversations
- OpenAI Realtime server events: https://developers.openai.com/api/reference/resources/realtime/server-events
- smart-turn v3: https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/
- smart-turn v3.2: https://www.daily.co/blog/smart-turn-v3-2-handling-noisy-environments-and-short-responses/
- smart-turn HF/GitHub: https://huggingface.co/pipecat-ai/smart-turn-v3 · https://github.com/pipecat-ai/smart-turn
- LiveKit turn detector: https://livekit.com/blog/improved-end-of-turn-model-cuts-voice-ai-interruptions-39 · https://huggingface.co/livekit/turn-detector
- Vapi latência (AssemblyAI 465ms): https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi · https://vapi.ai/blog/speech-latency
- Retell latência/turn-taking: https://www.retellai.com/blog/why-low-latency-matters-how-retell-ai-outpaces-traditional-players · https://www.coval.ai/blog/retell-ai-review-2026-features-pricing-and-when-to-use-it
- Medição de latência: https://www.coval.ai/blog/how-to-measure-voice-ai-latency-the-complete-guide · https://hamming.ai/resources/how-to-evaluate-voice-agents-2026
- Speculative/dual-path (research): https://arxiv.org/pdf/2603.23346 (RelayS2S) · https://arxiv.org/html/2601.19952v1 (LTS-VoiceAgent)
- Cascata vs S2S: https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture
- (Cruzar com `83-voice-orchestrators.md`: Pipecat/LiveKit framework decision; regra 800ms Daily; Modal ~1s v2v stack aberta.)
