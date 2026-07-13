# arch-fullduplex — Frontier de full-duplex mapeada ao stack Maya-BR

**Sub-tópico:** arquitetura full-duplex NATIVO vs. duplex-sobre-cascata. Como "ouvir-e-falar ao mesmo tempo" (barge-in, overlap) SEM treinar spine do zero.
**Data:** 2026-07-13. Verificado na web (buscas jul/2026) onde marcado; resto inferido do conhecimento e MARCADO.
**Lente:** avalio por mérito de arquitetura/add-on, não por idioma. O gate de licença só morde no PESO/DADO que embarca — o MÉTODO é sempre livre.

---

## TL;DR da decisão

1. **Não saia da cascata agora.** O upgrade de maior alavancagem/custo é plugar um **CONTROLADOR duplex** por cima da cascata Maya-BR v0 (VAD→whisper→LLM→CSM) — não trocar o CSM por um spine nativo.
2. **A peça concreta que existe HOJE, Apache-2.0, e faz exatamente isso é o SoulX-Duplug** (0.6B, "semantic VAD" streaming que roda ASR no áudio do usuário ENQUANTO o CSM fala e emite estado idle/speak/interrupt). É o nosso caminho barato pra barge-in. **ADOPT o padrão / TEST o checkpoint.**
3. **Full-duplex NATIVO (Moshi/PersonaPlex) fica em WATCH.** Substituir o CSM por um spine nativo joga fora a qualidade de voz do CSM e exige treinar o spine em pt-BR do zero — sem dado, é anti-alavancagem. Note que **a própria Sesame ainda NÃO entregou full-duplex**: o roadmap deles diz literalmente que é trabalho futuro que "exige mudanças fundamentais em toda a stack de IA".
4. **Gate de licença mata dois candidatos como PESO:** Freeze-Omni (licença Tencent, academic/NC — proibido comercial) e, com cautela, PersonaPlex (NVIDIA Open Model License, fora da allowlist estrita). O MÉTODO dos dois continua livre pra copiar.

---

## Framing: as duas famílias (survey 2606.19453, verificado)

O survey de full-duplex 2026 confirma a taxonomia que importa pra nós:

- **Nativo / end-to-end (parallel-stream):** um único modelo processa entrada e saída em canais paralelos e simultâneos (Moshi, dGSLM, Freeze-Omni). Interrupção/overlap emergem do modelo. Latência baixíssima (~80ms/frame a 12.5Hz), mas você **é dono do spine** — treina tudo, inclusive a voz, no seu idioma/dado.
- **Modular / cascata + controlador:** ASR+LLM+TTS clássicos MAIS um módulo controlador que gerencia turno em paralelo (quem fala, quando ceder/segurar/interromper), via uma **máquina de estados de turn-taking**. É onde a cascata Maya-BR v0 vive. O controlador é o que falta pra ela virar duplex.

**Decisão-chave:** o salto "half-duplex → duplex" NÃO exige salto "cascata → nativo". Dá pra ficar modular e ganhar barge-in só adicionando o controlador. É isso que muda o jogo pra nós.

---

## Itens, veredito e nota de licença

### 1. SoulX-Duplug — **ADOPT (padrão) / TEST (checkpoint)** ⭐
- **O que é (verificado):** módulo plug-and-play de "semantic VAD" streaming (0.6B) da Soul AI. Roda ASR streaming no áudio do usuário e prediz estado de diálogo (idle / non-idle / speak / interrupt) — serve como controlador de turno pra qualquer TTS/pipeline streaming. Latência média ~250ms EN/ZH. Checkpoint + servidor de inferência + cliente exemplo publicados (HF, mar/2026). arXiv 2603.14877.
- **Licença:** **Apache-2.0** (verificado) → **passa o gate** (código + pesos 0.6B).
- **Fit ao stack:** é LITERALMENTE o "plug duplex sobre TTS streaming" que o sub-tópico pede. Ele não toca o CSM: fica ouvindo o usuário em paralelo e diz ao orquestrador "o cara começou a falar → corta o CSM" (barge-in) ou "silêncio semântico, pode responder". Encaixa por cima da Maya-BR v0 sem retreinar o CSM.
- **Pegadinha / delta:** checkpoint é EN/ZH. Pra pt-BR: ou trocamos o ASR interno por whisper streaming, ou fine-tuna o preditor de estado com nosso áudio. Pela lente do projeto, o **padrão transfere de idioma**; o checkpoint em si é TEST (medir se o estado prediz bem em pt-BR carioca).

### 2. Moshi / Hibiki (Kyutai) — **WATCH (spine) / a infra de inferência é reusável**
- **O que é (verificado):** Moshi = spine full-duplex nativo sobre o codec Mimi (o MESMO Mimi/RVQ 12.5Hz que o CSM usa), streams paralelos usuário+agente. Hibiki = tradução S2S simultânea sobre a mesma arquitetura multi-stream (Hibiki-Zero, fev/2026).
- **Licença:** código MIT, pesos **CC-BY 4.0**, Mimi CC-BY (verificado) → **passa o gate**.
- **Fit:** trocar CSM→Moshi te dá duplex nativo de graça, MAS: (a) voz do Moshi < CSM em qualidade percebida; (b) base EN/FR, exige treinar pt-BR no spine inteiro (pior que o nosso plano de 2 estágios no CSM). **Não vale trocar.** O que É reusável já: o framework de inferência multi-stream do Moshi (mesmo Mimi) como referência de engenharia pra streaming de baixa latência.
- **Hibiki isolado: SKIP** — tarefa errada (tradução, não turn-taking de diálogo).

### 3. PersonaPlex (NVIDIA) — **WATCH**
- **O que é (verificado):** spine full-duplex Moshi (Temporal + Depth Transformer) 7B com DOIS controles adicionados: clonagem de voz (tokens de áudio de referência) e controle de papel/persona (prompt de texto). Treinado em diálogos sintéticos. arXiv 2602.06053, pesos em HF (nvidia/personaplex-7b-v1).
- **Licença:** **NVIDIA Open Model License + CC-BY-4.0**, marcado "ready for commercial use" (verificado). **Cautela de gate:** NVIDIA Open Model License NÃO está na allowlist estrita (Apache/MIT/CC-BY/CC0). Antes de embarcar peso, ler os termos (é permissiva mas custom). O CC-BY cobre a atribuição.
- **Fit / por que importa:** é a **prova pública de que dá pra pendurar clonagem-de-voz + persona num spine Moshi** — exatamente o tipo de add-on que a gente quer no CSM. Valor pra nós é como REFERÊNCIA DE MÉTODO (como condicionar voz num modelo duplex), não como peso a embarcar (7B EN, longe do carioca). WATCH: acompanhar como fazem o voice-conditioning.

### 4. Freeze-Omni (VITA-MLLM / Tencent) — **TEST (método) / peso SKIP (gate)**
- **O que é (verificado):** S2S de baixa latência sobre um **LLM de texto CONGELADO** — encoder de fala streaming + decoder AR de codebook único + uma camada de classificação por chunk que prediz interrupção. O congelamento evita o "esquecimento" do LLM. arXiv 2411.00774.
- **Licença:** **licença custom Tencent — academic/research/education APENAS, comercial PROIBIDO** (verificado no License.txt). → **peso REPROVA o gate.**
- **Fit / delta:** o **método é ouro e livre**: "LLM congelado + adaptadores de fala + classificador de estado" é receita direta pra dar duplex a um pipeline sem retreinar o cérebro. Encaixa na nossa filosofia de 2 estágios (não mexer no que já funciona). TEST como método de R&D; nunca embarcar os pesos deles.

### 5. LSLM — Listening-while-Speaking (Ma et al., 2024) — **TEST (método)**
- **O que é (verificado):** modelo que ADICIONA um canal de escuta a um TTS decoder-only baseado em tokens: encoder SSL streaming pra ouvir + fusão (early/middle/late; middle vence) pra detectar interrupção enquanto fala, com um token de "turn-taking". arXiv 2408.02622.
- **Licença:** paper/método (livre). Sem pesos OFICIAIS; só repo não-oficial (sanowl) de licença/qualidade incertas → não embarcar.
- **Fit / por que é o mais relevante metodologicamente:** o CSM É um decoder-only TTS baseado em tokens (Mimi) — exatamente o alvo do LSLM. LSLM descreve **como transformar o próprio CSM num modelo que ouve-enquanto-fala** adicionando um canal de escuta + token de interrupção, sem trocar o spine. É o caminho "duplex nativo barato SOBRE o CSM". TEST em bancada de R&D (mais ambicioso que o SoulX-Duplug, mas ataca o mesmo problema por dentro).

### 6. dGSLM (Meta, 2022) — **SKIP (produto) / WATCH (fundacional)**
- **O que é (inferido, não re-verificado hoje):** primeiro modelo de diálogo "textless" dual-tower com dois canais de áudio paralelos que aprendem timing/overlap/backchannel só de prosódia. Origem da ideia parallel-stream.
- **Licença:** código no ecossistema fairseq/textlesslib (permissivo, inferido) — mas é research, sem texto, sem controlabilidade, qualidade longe de produto.
- **Fit:** valor é histórico/conceitual (de onde vem o parallel-stream). Nada a plugar. SKIP pro produto.

### 7. Roadmap ~full-duplex da Sesame — **WATCH**
- **O que é (verificado, blog "Crossing the uncanny valley", mar/2025 + updates):** roadmap deles = escalar modelo, +20 idiomas, aproveitar LMs pré-treinados, e "caminhar pra modelos totalmente duplex que aprendem a dinâmica de conversa IMPLICITAMENTE dos dados — o que exigirá mudanças fundamentais em toda a stack de IA".
- **Leitura pra nós:** confirma que **full-duplex nativo com qualidade CSM ainda NÃO existe nem na Sesame** — é aspiração, não release. Reforça: nosso caminho é cascata+controlador agora; full-duplex nativo é vigiar, não perseguir. O ~100ms/frame é meta, não fato entregue (referências de frame rate reais rodam ~80ms a 12.5Hz).

### 8. Full-Duplex-Bench (+ survey de decision-state-machine) — **ADOPT (instrumento de eval)**
- **O que é (verificado):** benchmark de turn-taking full-duplex (usado e estendido pelo PersonaPlex pra papéis múltiplos) — mede latência de resposta, qualidade de barge-in, cessão de turno. O survey 2606.19453 dá a moldura da máquina de estados (yield/hold/grab).
- **Licença:** verificar antes de usar (inferido open) — mas é MÉTODO/eval, gate não morde no produto.
- **Fit:** se a gente for medir "o duplex funciona?", é com um bench desses + a scorecard-robótico que já temos. ADOPT como instrumento quando começarmos a testar o controlador.

---

## Recomendação operacional (o delta de decisão)

- **Agora:** manter cascata Maya-BR v0. Prototipar barge-in plugando o **padrão SoulX-Duplug** (semantic-VAD streaming como controlador de turno) por cima — ASR streaming pt-BR (whisper) alimentando um preditor de estado que corta o CSM quando o usuário fala. Custo: baixo (0.6B + orquestração), sem retreinar CSM.
- **Bancada de R&D (paralelo, sem parar coleta):** estudar o método LSLM/Freeze-Omni pra, no futuro, dar ouvido interno ao próprio CSM (canal de escuta + token de interrupção) — nativo-barato sobre o spine que já provamos.
- **Gatilho pra sair da cascata (só então):** (a) surgir spine full-duplex com voz nível-CSM E dado pt-BR pra treinar, OU (b) o piso de latência de turno da cascata (~300ms+ round-trip) virar o gargalo de UX medido — não antes.
- **Não embarcar como peso:** Freeze-Omni (NC academic). **Cautela:** PersonaPlex (NVIDIA Open Model License — ler termos). **Livres pra peso:** SoulX-Duplug (Apache), Moshi/Mimi (CC-BY).
