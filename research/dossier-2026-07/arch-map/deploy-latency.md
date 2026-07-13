# Deploy & Latência — mapa da fronteira → nosso stack (jul/2026)

> Sub-tópico do sweep de arquiteturas/add-ons. Foco: **como servir** a cascata Maya-BR v0
> (VAD → faster-whisper → LLM → CSM/Mimi) em **<800ms p50 de resposta** e **<300ms de barge-in**.
> Lente: avaliar por **mérito de engenharia de sistema**, não por idioma. No deploy o idioma nem entra —
> latência é física de kernel, transporte e escalonamento. Esta é literalmente a lição do CTO da Sesame:
> **"o fosso é systems engineering, não o modelo"**. Marco de honestidade: **[V]** = verificado na web (jul/2026),
> **[~]** = número de blog/estimativa, **[I]** = inferido do meu conhecimento.

---

## 0) O orçamento de latência da cascata (a conta que manda)

A "resposta" que o usuário sente = soma de estágios **em série**, menos o que você consegue **sobrepor** (pipeline).
Alvo de conversa natural: gap entre falas ≈ **200ms** (Gradium) [V]. Nosso alvo realista de produto: **<800ms p50**.

| Estágio | O que custa | Número de referência | Alavanca principal |
|---|---|---|---|
| **VAD / endpoint** | esperar o silêncio pra saber que o turno acabou | Silero ~1ms/chunk [I]; **mas o wait de silêncio 200–400ms é o custo real** [V] | **detector semântico de fim-de-turno** (corta o wait) |
| **STT (faster-whisper)** | transcrever o áudio final | streaming 90–300ms; WhisperPipe **89ms mediana / 142ms p90** [V] | partial decode + VAD hybrid |
| **LLM TTFT** | primeiro token da resposta | 150–300ms típico [~] | **streamar token→TTS** (não esperar frase inteira) |
| **TTS TTFA (CSM+Mimi)** | primeiro chunk de áudio | CSM-1B síntese ~150ms [~]; Fish S2 **100ms** [V]; Kyutai **220ms** [V] | CUDA-graph do decode + chunk pequeno no 1º |

**A conta só fecha com sobreposição.** Serial ingênuo = 400+300+300+150 ≈ 1.15s. Com **stream LLM→TTS**
(TTS começa na 1ª frase enquanto o LLM ainda gera) + endpoint semântico, dá pra puxar o p50 pra **~600–800ms**.
O gargalo que a maioria esquece **não é o modelo — é o endpoint** (esperar 300ms de silêncio custa mais que a síntese inteira).

---

## 1) SGLang-Omni como backbone de serving  — **TEST**
**O que é:** fork de serving do SGLang especializado em modelos de áudio (Higgs Audio v3, MOSS-TTS). Traz de fábrica:
continuous batching, **paged KV cache**, **RadixAttention** (prefix cache — reusa o prefixo de referência de voz),
**CUDA graph replay** no loop de decode, `OmniScheduler` compartilhado, encoder/vocoder batched. [V]
**Números [V]:** Higgs v3 num H100 → RTF **0.147** (c=1) a **0.262** (c=16); latência média 617ms→1079ms.
RadixAttention particionado por **áudio de referência** (`extra_key`) reusa cache de voz clonada.
**Por que pra nós:** é o candidato #1 de arma de serving. Dá exatamente os botões do brief:
**`abort_request` in-flight** (barge-in) e **`logit_bias`** (esteirar/proibir tokens — útil pra grão prosódico/pausas).
Ambos têm bugs abertos reportados no repo [V] — testar antes de confiar. **CSM/Mimi ainda não é first-class** no
sglang-omni (Higgs/MOSS sim) → é porte, não plug-and-play. **Licença:** SGLang core = **Apache-2.0** [I]; sglang-omni
inferido Apache (verificar LICENSE). Veredito **TEST**: montar 1 arm que serve o CSM sob sglang-omni e medir RTF/TTFA vs. baseline.

## 2) CUDA-graph do decode per-frame do Mimi/codec — **ADOPT**
**O que é:** o vocoder/codec decodifica **1 frame por passo** (12.5Hz → milhares de kernel-launches/request). Capturar
esse passo em **CUDA graph** elimina o overhead de launch. É o truque mais citado pra TTS AR sobre codec. [V]
**Números [V]:** PR do MOSS-TTS no sglang-omni — **2.20x** (30.1ms vs 66.3ms) pra 4 frames/passo, 1.93x pra 8, e
**bit-identical / default-on**. Precisa de **pools de estado GPU em endereço estável** (feedback embeddings, sampling,
histórico) pra o graph replay não sincronizar com a CPU. **Por que pra nós:** o CSM decodifica Mimi RVQ exatamente
nesse padrão per-frame — é o item de maior alavanca/menor risco do deploy. **Licença:** método (CUDA graph), livre.
Veredito **ADOPT** no decode loop do CSM/Mimi.

## 3) Streaming decode + chunking adaptativo (1º chunk pequeno → cresce) — **ADOPT**
**O que é:** emitir áudio por frame com **janela adaptativa** — chunk minúsculo no começo (derruba TTFA), janela
grande depois (recupera throughput). Alinhar chunk a **80ms (1280 samples @16kHz = 4 frames WebRTC)**. [V/~]
**Números:** MOSS reporta ~8.8 chunks/completion e inter-chunk ~0.109s @c16 [V]; forks community de CSM-streaming
relatam **primeiros chunks em ms** e total 40–60% melhor [~]. **Por que pra nós:** é o que transforma "geração de 3s"
em "voz que começa em 150ms". Os forks `davidbrowne17/csm-streaming` e `interactivetech/csm-streaming-tts` já
implementam isso sobre o CSM-1B (código community, checar LICENSE — método é livre de qualquer forma). Veredito **ADOPT**.

## 4) Arquitetura de cascata streaming (stream LLM→TTS, WS multiplex, sessão isolada) — **ADOPT**
**O que é:** o "systems engineering" que faz a cascata competir com modelo full-duplex. Peças:
(a) **streamar saída do LLM direto pro TTS** por sentença/cláusula — TTS não espera o LLM terminar; [V]
(b) **WebSocket persistente multiplexado** (economiza ~50ms/conexão; Gradium cai de 258→**214ms** p50 com multiplex) [V];
(c) **colocalizar** os componentes (sem hop de datacenter); [V]
(d) **sessão isolada por conexão** — `model.streaming()` com KV cache + **ring buffer do Mimi** próprios; sem isso,
clientes concorrentes corrompem o áudio uns dos outros; setar `max_session_tokens≈2000` (~160s) pra não fragmentar. [~]
**Por que pra nós:** é a espinha da Maya-BR v0. **Transporte:** WebSocket via FastAPI basta pra <200ms; WebRTC só
agrega complexidade sem ganho a distâncias cloud-local. **Licença:** engenharia própria, livre. Veredito **ADOPT** —
é onde ganhamos a corrida sem trocar de modelo.

## 5) Barge-in por abort-in-flight + flush de buffer — **ADOPT**
**O que é:** detectou fala do usuário durante a resposta → **cancelar** jobs de TTS pendentes/rodando + limpar fila de
geração + drenar o buffer de playback. **Orçamento de flush ≈ 60ms** [V]: 10ms VAD→dispatch + 20ms drenar buffer +
20ms fechar WS + 10ms release do device (mudança de estado do device custa 10–20ms). Moshi reseta o estado de geração
em **~50ms** [~]; manter os **últimos 3–4 chunks** pra recuperar contexto da interrupção. **Por que pra nós:** é o
caminho direto pro **<300ms de barge-in** — que é engenharia de cancelamento, não modelo. `sglang.abort_request`
existe mas tem bug de coroutine que trava (issue aberta) [V] → validar ou implementar cancelamento próprio na camada
de sessão. **Licença:** método, livre. Veredito **ADOPT** (obrigatório pro full-duplex percebido).

## 6) Detector semântico de fim-de-turno sobre o Silero VAD — **TEST**
**O que é:** o maior custo escondido da cascata é **quanto silêncio você espera** pra decidir que o turno acabou
(200–400ms). Um **endpoint semântico** (acústico + CTC rápido → decisão) corta esse wait sem trocar de modelo.
Linha 2026: **FastTurn**, **Next-Turn** (prediz onset da próxima fala), **Phoenix-VAD** streaming. [V]
**Por que pra nós:** derruba latência **percebida** mais que qualquer otimização de kernel — cada 100ms de silêncio
cortado é 100ms a menos de resposta, de graça. **Baseline Silero VAD = ADOPT** (MIT [I], ~1ms/chunk, já no repo).
O detector semântico é o upgrade. **Licença:** Silero MIT; os papers são método (reimplementar). Veredito **TEST**.

## 7) Speculative / multi-token decoding no LM AR do codec — **WATCH**
**O que é:** o backbone AR do CSM faz 1 forward por frame temporal — candidato clássico a **speculative decoding**
(draft pequeno propõe, target verifica). Novidade-chave 2026: **aceitação "coarse-grained"** — tokens de fala são
foneticamente **intercambiáveis**, então exigir match exato joga fora o ganho; relaxar o critério de aceitação
aproveita o mapa many-to-one ("Principled Coarse-Grained Acceptance for SD in Speech", 2511.13732). [V]
Também: multi-token prediction, SSD, compressão de tokens de áudio (TLDR). **Por que pra nós:** ganho real no loop AR,
mas o CSM já paraleliza os codebooks RVQ num depth-transformer (parte do ganho já colhido) e a área é **fresca**
(papers de nov/2025–jun/2026, sem release maduro). **Licença:** método, livre. Veredito **WATCH** — reavaliar quando
tiver implementação de referência; não é o gargalo enquanto endpoint + decode-graph não estiverem colhidos.

## 8) Kyutai DSM (KyutaiTTS 2B + Kyutai STT) — **TEST** como componentes streaming / **WATCH** como voz
**O que é:** **Delayed Streams Modeling** — gera fala **antes** do texto completo chegar (streaming de verdade LLM→TTS).
KyutaiTTS 2B: **220ms de latência**, treinado em **2.5M h**, **32 usuários simultâneos <350ms num L40S**, **CC-BY-4.0**. [V]
O STT do mesmo framework é streaming e também CC-BY. **Por que pra nós:** dois usos. (a) **STT streaming CC-BY** é
alternativa séria ao faster-whisper com timings nativos → **TEST** num arm de ASR. (b) DSM é a **referência viva** de
como fazer "streamar LLM→TTS" bem (item #4). (c) A **voz** KyutaiTTS passa no gate (CC-BY) mas é caminho concorrente
ao CSM+voz-do-Pedro, não o nosso — **WATCH**. **Licença:** CC-BY-4.0 [V] → passa no gate de produto. Veredito **TEST**
(componentes) / **WATCH** (como TTS principal).

---

## Ranking de decisão (o que fazer segunda-feira)
1. **ADOPT já (baixo risco, alta alavanca):** CUDA-graph do decode Mimi (#2), streaming+chunk adaptativo (#3),
   cascata com stream LLM→TTS + WS multiplex + sessão isolada (#4), barge-in por abort+flush (#5), Silero VAD (#6 baseline).
2. **TEST (arm barato de experimento):** sglang-omni servindo CSM (#1), endpoint semântico (#6 upgrade),
   Kyutai STT streaming como alternativa de ASR (#8a).
3. **WATCH:** speculative/coarse-grained SD no LM AR (#7), KyutaiTTS como voz (#8c).
4. **SKIP por ora:** WebRTC (WS basta a distância cloud-local); modelos full-duplex nativos (Moshi/Hertz) como spine —
   parkeados; nossa aposta é cascata + barge-in de engenharia.

## Nota de licença (deploy é o andar mais limpo)
Quase tudo aqui é **método** (CUDA graph, KV cache, chunking, cancelamento, pipeline) → **livre**, sem gate.
Artefatos concretos que tocaríamos: **SGLang/sglang-omni = Apache-2.0** [I, verificar sglang-omni], **Silero VAD = MIT** [I],
**faster-whisper/CTranslate2 = MIT** [I], **Kyutai DSM (TTS+STT) = CC-BY-4.0** [V], **CSM = Apache-2.0** (nossa base).
**Todos passam** no gate (Apache/MIT/CC-BY/CC0). O gargalo do deploy é **engenharia**, não licença — exatamente a tese Sesame.

## Verificado vs. inferido (honestidade)
- **[V]** Kyutai 220ms/2.5Mh/CC-BY/32-users-<350ms-L40S; MOSS CUDA-graph 2.20x (30.1 vs 66.3ms); Higgs v3 RTF 0.147→0.262 + RadixAttention-by-reference; Fish S2 TTFA 100ms/RTF 0.195; Gradium TTFA 258/274 e 214/228 c/ multiplex; WhisperPipe 89ms/142ms; coarse-grained SD em speech; sglang abort/logit_bias bugs; WhisperPipe/Silero hybrid VAD.
- **[~]** Moshi TTFA ~200/250ms e reset ~50ms, CSM-1B síntese ~150ms, chunk 80ms, flush 60ms breakdown, forks CSM-streaming 40–60% — vêm de blogs (Spheron/FutureAGI), tratar como ordem de grandeza.
- **[I]** Licenças Apache/MIT dos serving tools (não reconfirmei o LICENSE de sglang-omni nesta rodada); Silero ~1ms/chunk.

### Fontes
- LMSYS — Higgs Audio v3 on SGLang-Omni (2026-06-04); MOSS-TTS Local v1.5 on SGLang-Omni (2026-06-17)
- sgl-project/sglang-omni PR #798 (CUDA-graph streaming codec decode); sglang issues #14338 (abort), #6171 (logit_bias)
- Kyutai — Delayed Streams Modeling (KyutaiTTS 2B, 220ms, CC-BY-4.0); MarkTechPost/ScaleByTech releases
- Gradium — "Time to First Audio" (TTFA benchmark + multiplex)
- Spheron — "Sub-300ms Voice Agents: Moshi, Sesame CSM, Hertz-dev" (orçamento de latência/GPU/barge-in)
- Fish Audio S2 Technical Report (TTFA 100ms / RTF 0.195)
- FireRedChat (2509.06502) — full-duplex cascata/semi-cascata
- WhisperPipe (2604.25611), FastTurn (2604.01897), Next-Turn (2606.18094) — endpoint/turn detection
- "Principled Coarse-Grained Acceptance for Speculative Decoding in Speech" (2511.13732); TLDR audio-token compression (2606.09019)
- Futureagi — Voice AI Barge-In & Turn-Taking 2026 (flush 60ms breakdown)
