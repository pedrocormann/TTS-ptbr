# deploy-duplex-turn — full-duplex serving + turn-taking

**Sub-tópico:** o "add-on de deploy" que faz a cascata *parecer* full-duplex — VAD, end-of-turn semântico, barge-in (cancelar + truncar contexto ouvido), abort-in-flight, orquestradores (Pipecat, Unmute, LiveKit).
**Data:** 2026-07-13 · **Lente:** mérito de arquitetura, não idioma. Idioma só entra em (a) licença/PT do peso e (b) eval carioca.
**Honestidade:** `[✓web]` = verificado na web hoje · `[~inf]` = inferido do conhecimento, não re-verificado.

---

## TL;DR — a boa notícia é que já plugamos o certo

`src/duplex/turn_engine.py` **já implementa a receita moderna de 2026**, e bem:

- **Silero VAD** (1º estágio, presença de fala) `[✓web MIT]`
- **Smart Turn v3** (2º estágio, end-of-turn *semântico* por áudio) `[✓web BSD-2]`
- **Endpointing 2 estágios**: silêncio curto (~280ms) → smart-turn decide "fim de turno ou pausa?" → fallback duro em `endpoint_ms`
- **Barge-in interrompível**: player em thread, corte em ~80ms; `half-duplex` seguro por default (anti-eco em caixa de som), barge-in com gate alto (prob≥0.85 por 8 frames) só com fones
- **`Player.consume_interruption()`** já devolve a **fração ouvida** do último playback — a primitiva exata pra "truncar o contexto ouvido"

Isso é literalmente o que Pipecat/LiveKit/Unmute vendem como "turn-taking stack". **Não há gap arquitetural aqui.** O gargalo do projeto continua sendo DADO/voz pt-BR, não o serving duplex.

Então este dossiê é sobre **3 coisas concretas**:
1. **Afinar o que já temos** (2 melhorias baratas: *flush trick* e *backchannel-aware barge-in*).
2. **Uma decisão de graduação**: manter o loop artesanal vs. migrar pro Pipecat.
3. **Não cair em armadilha de licença** (LiveKit Turn Detector é PT-capaz mas *proibido* fora do ecossistema LiveKit).

**Padrão de produção 2026** `[✓web]`: TTS *flush* < 60ms, gap de turn-taking ponta-a-ponta 200–400ms. Barge-in de verdade exige STT e TTS em streams independentes simultâneos — a linha que separa "full-duplex real" de "cascata que finge". Nossa cascata *finge* (meia-duplex com barge-in por cima); pra o produto Maya-BR v0 isso basta, e a régua é "parece full-duplex", não "é Moshi".

---

## O que ADOTAR / TESTAR / VIGIAR / PULAR

### ✅ ADOPT — já plugado, manter e afinar

**1. Silero VAD** `[✓web]` — MIT, v6.2.1 (fev/2026; usamos via `silero_vad` pip), 512 amostras/32ms @16k. É o 1º estágio (presença de fala + gatilho de interrupção). **Zero motivo pra trocar.** Passa o gate folgado (MIT).

**2. Smart Turn v3.2** `[✓web]` — BSD-2-Clause, **verdadeiramente aberto** (pesos + dados de treino + script de treino). Whisper-tiny + classificador linear, ~8M params, **12ms CPU** (60ms em instância AWS barata), int8 e fp32, **23 línguas incl. PT**. Nosso código puxa o `.onnx` mais novo do repo `pipecat-ai/smart-turn-v3` — ou seja **já pega v3.2 automaticamente**. Passa o gate (BSD-2 = permissiva).
> *Delta barato:* fixar a versão do ONNX (hoje `onnxs[-1]` é "o mais novo alfabético" — frágil se o repo publicar `v3.10`), e considerar o int8 pra cortar mais latência no Mac.

### 🧪 TEST — armar experimento barato

**3. "Flush trick" + semantic-VAD-no-ASR (padrão Kyutai STT/Unmute)** `[✓web]` — **a alavanca de latência #1 que ainda não exploramos.** O Kyutai STT prevê, junto do texto, `P(usuário terminou de falar)`, e ao detectar fim **processa o áudio já bufferizado a ~4x tempo-real**, cortando a espera de endpoint de ~500ms → **~125ms**. Não podemos usar os *pesos* deles (STT é só EN/FR), mas o **padrão é replicável com faster-whisper**: quando o smart-turn diz "fim", rodar o Whisper no buffer acumulado imediatamente (já fazemos) — o ganho está em (a) *não* esperar o `endpoint_ms` duro quando o smart-turn tem alta confiança, e (b) decodar o tail agressivamente. **Método é livre** (só uma tática de scheduling). Arm: medir o histograma vad_end→asr no `chat_loop` e cortar a cauda de 500ms.

**4. Barge-in "consciente de backchannel" + truncagem de contexto** `[✓web + código nosso]` — **o que construir no `turn_engine`/`chat_loop` agora.** Dois buracos no barge-in atual:
   - **(a) Backchannel vs. interrupção real:** hoje qualquer fala forte por 256ms corta o agente. Mas "uhum", "tá", "sei" são *backchannels* — o humano quer que o agente **continue**. A régua 2026 `[✓web]`: backchannel mantém o piso; conteúdo novo cede o piso. Lever barato = passar o barge-in por um mini-classificador (o próprio smart-turn/ASR do trecho curto) antes de matar o playback.
   - **(b) Truncar o contexto ouvido (abort-in-flight):** quando há barge-in, o turno do agente entrou *inteiro* no contexto de áudio do CSM em `chat_loop`, mas o usuário só **ouviu a fração `played_samples/total_samples`**. `consume_interruption()` já devolve essa fração — falta **usá-la**: cortar o áudio/texto do agente na fração ouvida antes de adicionar ao contexto (`tts.add_context`). Sem isso, o CSM "acha" que disse coisas que o usuário nunca ouviu → deriva de conversa. **Método livre, ~1 tarde de código.**

**5. Pipecat (orquestrador)** `[✓web]` — BSD-2, Python. Pipeline componível STT→LLM→TTS com **interrupção, VAD (Silero), smart-turn e transport WebRTC/WebSocket embutidos**, e suporte a **TTS self-hosted** (custom service — dá pra plugar nosso CSM/pocket). É a "graduação" natural do nosso loop artesanal: troca ~500 linhas nossas por um framework testado em produção, com WebRTC de brinde (essencial pro caminho iOS/telefonia). Passa o gate (BSD-2).
> *Trade-off honesto:* adiciona peso de dependência e uma curva de aprendizado, e hoje nosso loop **já funciona e é auditável**. Veredito **TEST, não ADOPT**: fazer um spike de 1 dia plugando o CSM/pocket como custom TTS service no Pipecat e comparar latência/robustez de barge-in vs. `turn_engine.py`. Se o WebRTC/telefonia entrar no roadmap, vira ADOPT; pro CLI local, o loop nosso basta.

### 👀 WATCH — vigiar, não integrar agora

**6. Kyutai Unmute (orquestrador full-duplex de referência)** `[✓web]` — código **MIT**; envolve Kyutai STT+TTS (pesos CC-BY `[~inf]`, **EN/FR, sem PT**) num full-duplex real via WebSocket (STT streaming com semantic-VAD + flush → LLM → TTS). Mesma casa do nosso `pocket-tts` (Kyutai, MIT, jan/2026). **Por que WATCH e não TEST:** pesado (≥16GB VRAM, ~450–750ms TTS latency num L40S) e os pesos não são pt-BR. Valor = **é o blueprint do padrão que estamos copiando**; vigiar se sai um STT/TTS Kyutai multilíngue com PT (aí o flush-trick vira plug-and-play). Nota: a semantic-VAD do STT só existe no **servidor Rust**, não no Python.

**7. TEN VAD** `[✓web]` — Apache-2.0 **"com condições adicionais"** (⚠ ler o LICENSE antes de embarcar — pode ferir o gate). VAD ONNX ultraleve, roda em **Linux/Win/macOS/Android/iOS** + WASM. Interessante **só** pro caminho **iOS nativo on-device** (VAD no dispositivo, sem servidor) — aí competiria com o Silero. Pro backend não muda nada (Silero MIT é mais limpo). VIGIAR pra fase iOS; confirmar as "condições adicionais" do LICENSE.

**8. Spine full-duplex nativo (Moshi / Step-Audio R1.1)** `[✓web/~inf]` — o horizonte "duplex de verdade" (STT+TTS num modelo só, streams simultâneos), que substitui a cascata em vez de plugar nela:
   - **Moshi** (Kyutai, CC-BY) — nosso spine parkeado; reavaliar só com 50h+ estéreo (decisão da REVISAO, não re-litigar).
   - **Step-Audio R1.1** (StepFun, **Apache-2.0**, 14/jan/2026) `[✓web]` — topo do Big Bench Audio (97%), full-duplex S2S, licença **melhor que a do Moshi** pro gate. Provável EN/ZH, pesado. VIGIAR como alternativa de spine se/quando a cascata saturar em naturalidade de turn-taking.

### ⛔ SKIP — não pra nós (ou armadilha)

**9. LiveKit Turn Detector v1.0 (multilingual)** `[✓web]` — **a armadilha de licença do dossiê.** Tecnicamente é ótimo e **PT-capaz**: Qwen2.5-0.5B fine-tuned, 14 línguas incl. português, CPU/ONNX <500MB RAM, "-39% de interrupções". **MAS** os *pesos* são "LiveKit Model License" — licença **custom, field-of-use travada**: proibido usar standalone, com frameworks concorrentes, ou fora do ecossistema LiveKit Agents. **Reprova o gate** (não é Apache/MIT/CC-BY/CC0; é lock-in de plataforma). O *framework* LiveKit Agents é Apache-2.0, mas o **modelo não**. Como nosso `src/duplex` é cascata própria (não LiveKit Agents), **não podemos embarcar**. Já temos o smart-turn (BSD-2, PT, 8M) fazendo o mesmo trabalho — **sem esse item perdemos nada**. SKIP pra embarcar; serve só de benchmark comparativo.

**10. TEN Turn Detection** `[✓web]` — Apache-2.0 "com restrições adicionais", base **Qwen2.5-7B** (pesadíssimo pra endpointing), **só EN/ZH, sem PT**. Perde em três eixos (licença-flag, tamanho, idioma) pro smart-turn v3.2. SKIP.

**Referências proprietárias (contexto, não integráveis):** OpenAI Realtime API e Gemini Live fazem full-duplex nativo com barge-in — fechados, sem PT-BR garantido, SKIP pra embarcar. Servem de **norte de UX** de barge-in (latência de corte, backchannel), não de peça.

---

## Ranking de decisão (o que fazer no `src/duplex` esta semana)

| # | Ação | Custo | Ganho |
|---|------|-------|-------|
| 1 | **Truncar contexto na fração ouvida** no barge-in (`consume_interruption` já existe, só usar) | ~1 tarde | Mata deriva de conversa no CSM |
| 2 | **Flush trick**: não esperar `endpoint_ms` duro quando smart-turn tem alta confiança; medir vad→asr | ~1 tarde | −300ms de latência de turno |
| 3 | **Backchannel-aware barge-in** (não cortar em "uhum"/"tá") | ~1 dia | Menos cortes falsos, mais natural |
| 4 | **Pin da versão smart-turn** + testar int8 | ~1h | Robustez + latência |
| 5 | **Spike Pipecat** (CSM/pocket como custom TTS) — só se WebRTC/telefonia entrar no roadmap | ~1 dia | Decisão graduação |

**Nada disso depende de mais dado nem de GPU.** É engenharia de serving pura, roda no Mac do Pedro, e é o que faz a cascata "parecer Maya" no turn-taking.

---

## Notas de gate de licença (resumo)

| Item | Licença | Passa o gate? |
|---|---|---|
| Silero VAD | MIT | ✅ |
| Smart Turn v3.2 | BSD-2 | ✅ |
| Pipecat | BSD-2 | ✅ |
| Unmute (código) | MIT | ✅ (mas pesos Kyutai CC-BY, EN/FR) |
| Step-Audio R1.1 | Apache-2.0 | ✅ (vigiar) |
| TEN VAD / Turn Detection | Apache-2.0 **+ condições adicionais** | ⚠ ler LICENSE |
| **LiveKit Turn Detector (pesos)** | **LiveKit Model License (custom, field-of-use lock)** | ❌ |
| Moshi | CC-BY | ✅ (parkeado) |

---

*Fontes web (2026-07-13):* daily.co/blog (Smart Turn v3/v3.1), github.com/pipecat-ai/smart-turn (BSD-2), huggingface.co/pipecat-ai/smart-turn-v3, github.com/pipecat-ai/pipecat (BSD-2), kyutai.org/stt + /blog/2025-07-03 (semantic VAD + flush trick), github.com/kyutai-labs/unmute (MIT), livekit.com/blog/solving-end-of-turn-detection + github.com/livekit/agents/blob/main/MODEL_LICENSE (field-of-use lock), huggingface.co/livekit/turn-detector, github.com/TEN-framework/ten-turn-detection (Apache+restrições, Qwen2.5-7B, EN/ZH), github.com/snakers4/silero-vad (MIT, v6.2.1), evalgent.com + softcery.com + callsphere.ai (padrões duplex 2026, Step-Audio R1.1).
