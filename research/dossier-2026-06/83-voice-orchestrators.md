# 83 — Frameworks de orquestração de agente de voz (FRENTE B)

> **Data da pesquisa: 2026-06-10.** Decisão em pauta: adotar Pipecat / LiveKit Agents /
> outro framework, ou continuar evoluindo o orquestrador artesanal `src/duplex`
> (~503 linhas: silero-VAD turn engine + faster-whisper + LLM OpenAI-compatible +
> adaptadores TTS próprios, incl. CSM com **audio-contexto entre turnos**).
> Critérios Maya-BR v0.2: barge-in <300ms · TTS custom **com estado** ·
> re-síntese incremental (pivô no meio da frase) · LLM OpenAI-compatible ·
> ASR pt-BR · licença permissiva · 100% offline (Mac M2 24GB → servidor GPU).

---

## 1. Pipecat (pipecat-ai/pipecat)

**Fonte primária:** https://github.com/pipecat-ai/pipecat · docs: https://docs.pipecat.ai

| Critério | Verificado (jun/2026) |
|---|---|
| Licença | **BSD-2-Clause** (permissiva, compatível com nosso gate Apache/MIT) |
| Atividade | 12.8k stars, 2.2k forks; **release v1.3.0 em 29/mai/2026** — muito ativo |
| Mantenedor | Daily.co (empresa de WebRTC; o framework é o core do Pipecat Cloud) |

### Arquitetura: pipelines de frames (sim)
Tudo que flui no pipeline é um **frame tipado** — áudio, transcrição, tokens de LLM,
áudio sintetizado. Três classes de frames ([docs/pipeline](https://docs.pipecat.ai/guides/learn/pipeline)):
- **SystemFrames** (alta prioridade, sobrevivem a interrupções): `InputAudioRawFrame`,
  `UserStartedSpeakingFrame`, `InterruptionFrame`;
- **DataFrames** (ordenados): `OutputAudioRawFrame`, `TranscriptionFrame`, `LLMTextFrame`;
- **ControlFrames**: `EndFrame`, `TTSStartedFrame` etc.
Processadores não "consomem" frames — processam e repassam downstream; dá para inserir
um processor custom em qualquer ponto (é exatamente o gancho de que a re-síntese
incremental precisa).

### Barge-in / interrupção
- Silero VAD roda local junto ao pipeline; ao detectar voz do usuário, um
  `InterruptionFrame` (alta prioridade) propaga e o `PipelineTask` **cancela tarefas
  pendentes automaticamente** (LLM em streaming, TTS, playback).
- Estratégias de interrupção plugáveis: ex.
  [`MinWordsUserTurnStartStrategy`](https://reference-server.pipecat.ai/en/latest/api/pipecat.audio.interruptions.min_words_interruption_strategy.html)
  (só interrompe após N palavras — útil para distinguir backchannel de barge-in real,
  exatamente o problema Maya).
- Turn detection semântico próprio e **aberto de verdade**: **smart-turn v3**
  (modelo + datasets sob **BSD-2-Clause** no HF:
  https://huggingface.co/pipecat-ai/smart-turn-v3, repo https://github.com/pipecat-ai/smart-turn).
- Latência de barge-in: não há número oficial publicado; com VAD local a detecção é
  ~1 frame de VAD (dezenas de ms) + cancelamento do pipeline. Issues abertas mostram
  arestas reais: [#3986](https://github.com/pipecat-ai/pipecat/issues/3986)
  (guard `_bot_speaking` falha se o áudio TTS ainda não chegou ao transport) e
  [#2791](https://github.com/pipecat-ai/pipecat/issues/2791) (contexto não atualizado
  na interrupção). Ou seja: barge-in <300ms é plausível e é o caminho do projeto,
  mas não é garantido sem tuning.

### TTS custom (plugar CSM/Pocket)
- Subclasse de [`TTSService`](https://reference-server.pipecat.ai/en/stable/api/pipecat.services.tts_service.html):
  sobrescrever `run_tts(text, context_id) -> AsyncGenerator` de frames de áudio.
  A base já cuida de agregação de sentenças, filtros e frame management.
- **Estado entre turnos é viável sem hack**: o service é uma instância persistente do
  pipeline — a janela de audio-contexto do CSM pode viver como atributo da classe,
  alimentada ouvindo `TranscriptionFrame`/`OutputAudioRawFrame` que passam por ela.
  Existe `InterruptibleTTSService` para engines via websocket.
- Serviços locais já inclusos: **Piper, Kokoro, XTTS** ([supported-services](https://docs.pipecat.ai/server/services/supported-services)).

### ASR plugável / pt-BR
- **`WhisperSTTService` usa faster-whisper por baixo** (mesmo engine do nosso scaffold)
  e há **`WhisperSTTServiceMLX`** otimizado para Apple Silicon
  ([referência](https://reference-server.pipecat.ai/en/stable/api/pipecat.services.whisper.stt.html)).
  Modelos até large-v3-turbo (incl. quantizado Q4 no MLX). Whisper cobre pt-BR.
  Ressalva: é STT **segmentado pós-VAD**, não streaming token-a-token — igual ao nosso.

### 100% local/offline
Sim: `LocalAudioTransport` (mic/speaker locais, sem servidor —
[issue #197](https://github.com/pipecat-ai/pipecat/issues/197) documenta o combo
LocalAudioTransport+Whisper+LLM+TTS), mais `SmallWebRTCTransport`/FastAPI-WebSocket
sem dependência de Daily/LiveKit. LLM via **Ollama** ou qualquer endpoint
OpenAI-compatible.

### Latência reportada (stack 100% aberta, self-hosted)
- Modal (04/nov/2025): **~1s mediana voice-to-voice** com Pipecat + Parakeet-tdt-0.6b
  (STT) + Qwen3-4B/vLLM + Kokoro-82M, tudo self-hosted —
  https://modal.com/blog/low-latency-voice-bot. Proximidade geográfica GPU↔cliente foi
  o fator dominante.
- Regra da casa Daily/kwindla: alvo **800ms mediana voice-to-voice** —
  https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/ e
  https://gist.github.com/kwindla/f755284ef2b14730e1075c2ac803edcf.
- Observabilidade embutida: `MetricsLogObserver` (TTFB por serviço) e
  `UserBotLatencyLogObserver` (fim-da-fala→início-da-resposta) — substitui nosso
  logging artesanal de latência por estágio.

### Exemplos parecidos com nosso caso
O combo "local transport + Whisper local + Ollama + TTS local" é caso de uso
reconhecido (issue #197, exemplos `07x-local` no repo de exemplos). Não achei exemplo
público de **TTS condicionado em áudio do histórico** (estilo CSM) — isso seria
contribuição nossa de qualquer forma.

---

## 2. LiveKit Agents (livekit/agents)

**Fonte primária:** https://github.com/livekit/agents · docs: https://docs.livekit.io/agents/

| Critério | Verificado (jun/2026) |
|---|---|
| Licença (framework) | **Apache-2.0** |
| Atividade | 10.9k stars, 3.2k forks; **release v1.5.17 em 03/jun/2026** — muito ativo |
| Mantenedor | LiveKit (empresa; usado no modo voz do ChatGPT, segundo o repo) |

### Dependência do servidor LiveKit
- **Modo console** (`python agent.py console`): roda 100% local com mic/speaker, **sem
  servidor** — mas é posicionado como modo de *teste*
  ([docs](https://docs.livekit.io/agents/)).
- Produção pressupõe um **LiveKit server** (WebRTC SFU). O servidor é open source
  Apache-2.0 e self-hostable ([docs self-hosting](https://docs.livekit.io/transport/self-hosting/local/)),
  então dá para ficar offline — ao custo de operar um SFU em Go + redis etc.
  Arquitetura: `AgentServer` agenda jobs, `AgentSession` gerencia a sessão.

### Barge-in / turn detection
- Interrupção automática na `AgentSession` + **turn detector semântico** (transformer
  ~135M baseado em SmolLM v2,
  [blog](https://blog.livekit.io/using-a-transformer-to-improve-end-of-turn-detection)).
- **PEGADINHA DE LICENÇA**: o plugin é Apache-2.0, mas **os pesos do modelo de
  end-of-turn estão sob a "LiveKit Model License"**, não permissiva e atrelada ao uso
  com LiveKit Agents — https://huggingface.co/livekit/turn-detector
  ([LICENSE](https://huggingface.co/livekit/turn-detector/blob/main/LICENSE)). Para o
  nosso gate de licença, teríamos que usar Silero VAD puro ou o smart-turn (BSD) da
  concorrente — possível, porém perde-se parte do valor.

### TTS custom / ASR / LLM
- Interface padrão `tts.TTS` com modo stream (`push_text` → stream de
  `SynthesizedAudio`); plugins são extensíveis e há demanda comunitária por TTS
  self-hosted ([issue #1724](https://github.com/livekit/agents/issues/1724),
  [docs TTS](https://docs.livekit.io/agents/models/tts/)). Viável plugar CSM, mas a
  documentação de "como escrever um plugin TTS do zero" é mais rasa que a do Pipecat
  (remete às contribution guidelines —
  [docs plugins](https://docs.livekit.io/agents/integrations/plugins/)).
- STT/LLM: dezenas de plugins; LLM OpenAI-compatible ok; Whisper local existe via
  plugin da comunidade, mas o ecossistema empurra para cloud (Deepgram/Cartesia via
  "Inference API" da LiveKit Cloud).

### Veredito parcial
Excelente para produto multiusuário com telefonia/WebRTC em escala; **overhead
estrutural alto para um agente local single-user**, e o componente de turn-taking que
mais nos interessa tem pesos com licença restritiva.

---

## 3. Alternativas

### 3.1 Vocode (vocodedev/vocode-core) — **descartado**
Desenvolvimento praticamente parado: commits mínimos há bem mais de um ano, issues sem
resposta; arquitetura anterior à era speech-to-speech/sub-500ms. Avaliações de 2026
recomendam não iniciar nada novo nele
(https://github.com/vocodedev/vocode-core; análise de abr/2026:
https://blog.dograh.com/ai-voice-agents-github-proven-guide-dograh-vs-livekit-vs-pipecat/).

### 3.2 KoljaB/RealtimeVoiceChat — **referência, não base**
O próprio autor declara que **não mantém mais ativamente** (só revisa PRs)
(https://github.com/KoljaB/RealtimeVoiceChat). Continua sendo a melhor *referência de
código* para turn-taking dinâmico e barge-in low-latency com RealtimeSTT/RealtimeTTS
(faster-whisper + Coqui), mas não é um framework para construir em cima.

### 3.3 huggingface/speech-to-speech — **vivo e ALINHADO, mas é pipeline, não framework**
- Apache-2.0, 4.9k stars, release em 06/fev/2026, 551 commits, ativo em 2026
  (https://github.com/huggingface/speech-to-speech).
- Stack: Silero VAD v5 + Whisper/Parakeet/MLX-Whisper + transformers/mlx-lm/llama.cpp/
  OpenAI API + **TTS incluindo Pocket TTS, Kokoro, Qwen3-TTS** (os nomes de voz
  alba/marius/javert são os presets do Pocket — mesma engine do nosso default!).
- Flag `--local_mac_optimal_settings` (MPS + MLX) — receita pronta de tuning p/ M2.
- Suporta cancelamento por `turn_detected` (barge-in básico).
- **Línguas declaradas: en/fr/es/zh/ja/ko — pt NÃO listado** (Whisper transcreve pt,
  mas o pipeline não foi ajustado para isso).
- Leitura: é um *reference pipeline* mono-sessão, sem ecossistema de
  transports/observabilidade. Vale **roubar padrões** (MLX no Mac, handlers modulares),
  não migrar.

### 3.4 TEN Framework (TEN-framework/ten-framework) — **forte, mas runtime pesado e licença com asterisco**
- 10.7k stars, muito ativo em 2026; ecossistema com **TEN VAD** e **TEN Turn Detection**
  (full-duplex) (https://github.com/TEN-framework/ten-framework, https://theten.ai/).
- Runtime poliglota (C++/Go/Python/TS), origem Agora.io, foco enterprise/telefonia.
- **Licença: "Apache 2.0 com restrições adicionais"** (texto do próprio README;
  pastas específicas excluídas). Não verifiquei o teor exato das restrições no LICENSE
  — **bloqueador até auditoria**, dado nosso gate de licença dura.
- Exemplos default dependem de Deepgram/OpenAI/ElevenLabs (cloud); operação 100%
  offline não é o caminho feliz documentado. Complexidade >> nossa necessidade.

### 3.5 Novos 2025–2026
- **FastRTC (gradio-app/fastrtc)**, fev/2025: biblioteca Python que transforma uma
  função em stream de áudio em tempo real (WebRTC/WebSocket), com VAD e turn-taking
  embutidos (https://github.com/gradio-app/fastrtc, https://fastrtc.org/). É camada de
  **transporte**, não orquestrador — candidata natural quando o `src/duplex` precisar
  de um cliente web, sem adotar framework inteiro.
- **Dograh (dograh-hq/dograh)**: "Vapi open source", BSD-2-Clause, workflow builder
  visual + telefonia, ~1.2k stars (https://github.com/dograh-hq/dograh). Jovem, foco
  call-center; não agrega aos nossos critérios.
- Não encontrei (buscas jun/2026) nenhum framework novo que suporte nativamente TTS
  com estado de áudio entre turnos ou re-síntese incremental.

---

## 4. O ponto que decide: TTS com ESTADO + re-síntese incremental

**Nenhum framework avaliado oferece, nativo:**
1. **TTS condicionado no áudio do histórico da conversa** (o "segredo Maya"/CSM). Todas
   as interfaces TTS (Pipecat `run_tts(text)`, LiveKit `tts.TTS.synthesize/stream`)
   são *texto→áudio sem memória*. Em ambos dá para manter estado na instância do
   service — no Pipecat é mais natural porque o service vê os frames de áudio de
   entrada/saída passando pelo pipeline.
2. **Re-síntese incremental com pivô no meio da frase** (cancelar e regerar a fala já
   em reprodução a partir do ponto falado). O mais próximo que existe: Pipecat rastreia
   word timestamps e sincroniza contexto com o que foi *de fato* falado, e o
   `InterruptionFrame` cancela geração pendente — ou seja, os **primitivos** existem
   (sabe-se onde a fala parou; sabe-se cancelar), mas o loop "regerar do pivô"
   teríamos que escrever como FrameProcessor custom. No LiveKit/TEN/HF-s2s os ganchos
   são piores ou inexistentes.

Conclusão técnica: a parte *difícil e diferenciada* do Maya-BR é nossa em qualquer
cenário. Framework só compra transporte, VAD/turn-taking, cancelamento e métricas.

---

## 5. Tabela-resumo contra os critérios v0.2

| Critério | src/duplex (nosso) | Pipecat | LiveKit Agents | HF s2s | TEN | vocode/RVC |
|---|---|---|---|---|---|---|
| Licença | n/a | **BSD-2** | Apache-2.0 (modelo EOU restrito) | Apache-2.0 | Apache-2.0 + restrições | MIT (mortos) |
| Barge-in <300ms | sim (corte <1 frame, 80ms buffer) | plausível (VAD local + cancel; sem nº oficial) | plausível (idem) | básico | sim (foco full-duplex) | — |
| TTS estado/audio-ctx | **nativo (CSM adapter)** | viável (service com estado) | viável (mais atrito) | não | não | não |
| Re-síntese c/ pivô | a construir (controle total) | a construir (primitivos bons: word-ts + interruption) | a construir (ganchos piores) | não | não | não |
| LLM OpenAI-compat | sim | sim (+Ollama) | sim | sim | sim | — |
| ASR pt-BR local | faster-whisper | **faster-whisper nativo + MLX** | plugin comunidade | Whisper (pt não tunado) | depende | — |
| 100% offline | sim | **sim (LocalAudioTransport)** | console=sim; prod=self-host SFU | sim | não é o caminho feliz | — |
| Custo de adoção | 0 | médio | alto | baixo (cópia de padrões) | alto | — |

---

## 6. Recomendação fundamentada

**Não migrar agora; convergir para o Pipecat em duas fases.**

1. **v0.2 (Mac local, agora): manter o `src/duplex`.** Ele já entrega os dois itens
   que nenhum framework dá (audio-contexto do CSM; caminho livre para a re-síntese com
   pivô), tem 503 linhas auditáveis e barge-in projetado para <100ms. Migrar agora =
   reescrever a parte única em cima de abstrações alheias antes de validar a hipótese
   Maya. Importar do mundo externo, sem adotar framework:
   - **smart-turn v3 (BSD-2)** como segundo estágio do turn_engine (semântico, anti
     corte de pausa) — substitui heurística de silêncio;
   - padrões MLX/MPS do huggingface/speech-to-speech para o M2;
   - os dois observers de latência do Pipecat como inspiração do nosso log.
2. **Espelhar interfaces do Pipecat desde já** (custo ~zero): manter `tts_adapter` com
   assinatura compatível com `TTSService.run_tts` e o turn_engine emitindo eventos
   equivalentes a `UserStartedSpeaking/Interruption`. Isso deixa a migração barata.
3. **v0.3+ (servidor GPU, clientes remotos, multiusuário): adotar Pipecat** como
   camada de transporte/orquestração (BSD-2, ativo, faster-whisper nativo, offline,
   ~1s voice-to-voice comprovado com stack 100% aberta), portando o CSM adapter como
   `TTSService` custom e a re-síntese como FrameProcessor. Alternativa mínima se só
   precisarmos de um cliente web: FastRTC na frente do `src/duplex`.
4. **Descartar**: LiveKit Agents (SFU obrigatório em produção + pesos do turn detector
   com licença restritiva), vocode e RealtimeVoiceChat (sem manutenção), TEN
   (complexidade e licença com asterisco), HF speech-to-speech (pipeline de
   referência, não framework).

**Risco a monitorar**: Pipecat é dirigido pela Daily (Pipecat Cloud); se o open core
fechar features (como LiveKit fez com o modelo EOU), o plano B é continuar no
orquestrador próprio — mais um motivo para a fase 2 (interfaces espelhadas, não
dependência).

---

## 7. Fontes primárias
- https://github.com/pipecat-ai/pipecat (BSD-2; v1.3.0 29/mai/2026; 12.8k★)
- https://docs.pipecat.ai/guides/learn/pipeline · https://docs.pipecat.ai/server/services/supported-services
- https://reference-server.pipecat.ai/en/stable/api/pipecat.services.tts_service.html
- https://reference-server.pipecat.ai/en/stable/api/pipecat.services.whisper.stt.html
- https://github.com/pipecat-ai/smart-turn · https://huggingface.co/pipecat-ai/smart-turn-v3
- https://github.com/pipecat-ai/pipecat/issues/197 · /issues/3986 · /issues/2791
- https://modal.com/blog/low-latency-voice-bot (1s v2v, stack aberta, nov/2025)
- https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/
- https://github.com/livekit/agents (Apache-2.0; v1.5.17 03/jun/2026; 10.9k★)
- https://docs.livekit.io/agents/models/tts/ · https://docs.livekit.io/agents/integrations/plugins/
- https://huggingface.co/livekit/turn-detector (LiveKit Model License)
- https://docs.livekit.io/transport/self-hosting/local/
- https://github.com/livekit/agents/issues/1724
- https://github.com/vocodedev/vocode-core (estagnado)
- https://github.com/KoljaB/RealtimeVoiceChat (autor: sem manutenção ativa)
- https://github.com/huggingface/speech-to-speech (Apache-2.0; release fev/2026)
- https://github.com/TEN-framework/ten-framework (Apache-2.0 + restrições) · https://theten.ai/
- https://github.com/gradio-app/fastrtc · https://fastrtc.org/
- https://github.com/dograh-hq/dograh (BSD-2)
- https://blog.dograh.com/ai-voice-agents-github-proven-guide-dograh-vs-livekit-vs-pipecat/ (análise abr/2026; fonte interessada — Dograh)

**Não verificado / honestidade**: (a) teor exato das "restrições adicionais" da licença
TEN (exige ler o LICENSE no repo); (b) latência de barge-in medida em ms para Pipecat e
LiveKit — não há benchmark oficial publicado, só arquitetura compatível com <300ms;
(c) se Dograh usa Pipecat internamente (alegado em posts de terceiros, não confirmado
em fonte primária).
