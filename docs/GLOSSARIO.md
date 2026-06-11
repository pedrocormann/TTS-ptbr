# Glossário do projeto (termos em inglês, explicações em português)

> Vivo — adicionar termo novo sempre que aparecer no projeto. Início: 2026-06-10.

## Conceitos de base

- **SOTA** (*state of the art*) — o melhor resultado conhecido no mundo para uma
  tarefa, agora. "Pesquisa SOTA" = mapear o topo antes de construir.
- **Spine** — apelido nosso pro modelo central que carrega a conversa (a
  "espinha dorsal"). Aposta de longo prazo: Moshi (Trilha B).
- **TTS** (*text-to-speech*) — texto → fala. **ASR** (*automatic speech
  recognition*) — fala → texto. **VAD** (*voice activity detection*) — detector
  de "tem gente falando agora?".
- **ASR incremental/streaming** — transcreve ENQUANTO você fala (intérprete
  simultâneo), emitindo hipóteses parciais; o LLM começa a pensar antes de você
  terminar. ASR comum = intérprete consecutivo (espera o fim). Fonte de
  centenas de ms da Maya.
- **LLM** (*large language model*) — o "cérebro" de texto (Gemini, Maritaca…).
  No nosso desenho é plugável e fica no bastidor (backstage).
- **Full-duplex** — ouvir e falar AO MESMO TEMPO (como pessoa: "uhum" enquanto
  o outro fala). **Half-duplex** — um de cada vez (walkie-talkie); nosso app
  local usa half-duplex em caixa de som por causa do eco.
- **Barge-in** — interromper o agente falando por cima, e ele cala na hora.
- **Cascata** (*cascade*) — arquitetura em etapas: VAD → ASR → LLM → TTS.
  A Maya viral é uma cascata MUITO bem engenheirada (confirmado pelo CTO).

## Modelos do projeto

- **CSM** (*Conversational Speech Model*, Sesame) — modelo de voz da Sesame
  (parte aberta, 1B, Apache-2.0). Diferencial: é **audio-conditioned** — ouve o
  áudio da conversa inteira e fala condicionado nisso (prosódia/emoção
  "presentes"). Nosso clonador de voz. CTO: "even the 1B is very good".
- **Moshi** (Kyutai) — único grande modelo aberto full-duplex de verdade
  (CC-BY-4.0). Texto é paralelo (Inner Monologue), áudio é o core. Trilha B.
- **Mimi** — o codec de áudio neural (waveform ⇄ tokens, 12.5Hz) usado por CSM
  E Moshi. Decisão nossa: congelado.
- **Pocket-TTS** (Kyutai) — TTS de 100M que roda em CPU em tempo real. Papel:
  fallback de latência; não compete em qualidade de voz.
- **Qwen3-TTS / Chatterbox-pt-br** — candidatos Apache/MIT da Trilha A com
  português nativo (ver REPLAN §2).

## Treino

- **Finetune** — continuar o treino de um modelo pronto com SEUS dados, pra
  especializá-lo (ex.: ensinar pt-BR com a voz do Pedro ao CSM).
- **LoRA** (*low-rank adaptation*) — finetune barato: acopla "adaptadores"
  pequenos que aprendem só o delta, sem mexer no modelo inteiro (lente nova na
  câmera, não câmera nova). **Adapter** = o arquivo resultante.
- **Zero-shot / in-context** — sem treino nenhum: o modelo imita a partir de
  exemplos no prompt (ex.: clonar voz com 8s de referência). **Âncora** =
  esses exemplos de referência; no CSM 4-bit, usar ≥3 (medimos 0.618→0.973).
- **CPT** (*continued pretraining*) — re-treino pesado de língua; nosso
  fallback se LoRA não bastar (SDumont).
- **RL** (*reinforcement learning*) — aprender por tentativa e nota (recompensa)
  em vez de exemplos. **GRPO/DPO** = receitas de RL/preferência usadas pra
  lapidar interatividade/emoção (Fase 5).
- **Quantização** (*quantization*) — comprimir os pesos (16-bit → 8/4-bit) pra
  rodar mais rápido/leve, com possível perda de qualidade. 4-bit + 3 âncoras =
  tempo real no M2 sem perder o timbre.

## Métricas e eval

- **WER** (*word error rate*) — % de palavras erradas (substituições+inserções+
  omissões ÷ total). Usamos em **round-trip**: TTS fala → ASR ouve → compara
  com o texto. Detector de inteligibilidade. ⚠️ "saturado" pra separar o topo
  (todo TTS bom ≈ 0) — serve de gate, não de ranking.
- **spk-sim** (*speaker similarity*) — cosseno entre embeddings de voz
  (WavLM-SV): "é a mesma pessoa?". Reportar sempre com o teto real-vs-real da
  mesma rodada (~0.965 no nosso setup; escala comprime!).
- **RTF** (*real-time factor*) — velocidade de síntese vs duração do áudio
  (RTF 0.5× = gera na metade da velocidade da fala; ≥1× = tempo real).
  **TTFA/TTFB** (*time to first audio/byte*) — latência até o primeiro som.
- **MOS / CMOS** (*[comparative] mean opinion score*) — nota humana de
  qualidade (1-5) / comparação A/B. **TTSDS2** — métrica distributiva
  multilíngue (nossa principal automática). **UTMOS** — proxy antigo,
  rebaixado (não calibrado pt-BR).
- **Eval da Sesame** (dossiê 86): WER saturou → eles usam (1) **sondas de
  pronúncia** (homógrafos: "sede" empresa vs "sede" d'água — quantificável,
  não satura), (2) **arena de preferência** (A/B cego, Elo), (3) **win-rate vs
  continuação humana**: corta uma conversa real, modelo gera a próxima fala,
  juízes comparam com o que o humano REALMENTE disse — 50% = indistinguível de
  gente, e (4) hill-climbing qualitativo ("trying it, feeling it").
- **SER** (*speech emotion recognition*) — classificador de emoção no áudio;
  vamos treinar o nosso pt-BR (receita Frederico) pra medir controle de emoção.

## Engenharia da Maya (Trilha M)

- **Orquestrador** — o maestro: não fala nem ouve, coordena VAD→ASR→LLM→TTS e
  a interrupção. Nosso: `src/duplex`. **Pipecat** — framework pronto pra isso
  (BSD-2); decisão: adotar só na v0.3+ (transporte).
- **TTS com estado** (*stateful TTS*) — TTS que LEMBRA dos turnos anteriores
  (áudio seu e dele) e mantém coerência — o que o CSM faz e nenhum framework
  suporta nativamente.
- **Re-síntese incremental** — começar a falar antes de terminar de pensar e
  poder **pivotar no meio da frase** (ex.: chegou resultado de busca). Segredo
  técnico da Maya: abort de geração em 20ms no sglang + JSON constrainado.
- **OSINT** (*open-source intelligence*) — investigação só com fontes públicas
  (forks, papers, vagas, podcasts). Como fizemos a engenharia reversa.
- **Watermark** — marca d'água inaudível no áudio gerado (proveniência/
  anti-fraude). Sesame usa silentcipher (3 linhas, roda no M2); PL 1460 vai
  exigir.

## Datasets de referência

- **EARS / Expresso** (Meta) — datasets expressivos de referência (100h/22
  emoções; 40h/26 estilos em diálogo atuado). Licença NC = não usamos o áudio;
  copiamos o PROTOCOLO de gravação no nosso kit.
- **Elise** — dataset de 3h com tags de emoção que era o padrão dos tutoriais
  (caiu por DMCA); nosso dataset segue o formato de tags dele (conjunto
  Orpheus: `<laugh> <sigh>`…).
- **TAGARELA** (Frederico/UFG) — 8.972h de podcasts pt; licença NC = só eval.
  **CML-TTS** — 68h pt lidas, CC-BY (corrigido: NÃO são 1.100h).
