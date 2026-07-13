# Mapa vivo — Arquiteturas & Add-ons (treino · deploy · eval) — 13/jul/2026

> Levantamento de 11 frentes (sweep `arch-addons-map`), **avaliado por mérito de arquitetura/add-on, não por
> idioma** ([[feedback-arquitetura-nao-idioma]]). Digests completos por frente em
> [`arch-map/`](arch-map/) (1 arquivo por célula, com fontes web jul/2026 e marcação verificado-vs-inferido).
> Este doc é o índice de decisão + a **matriz de experimentos** (arms toggleáveis). Complementa dossiês 83 (SAMPA)
> e 84 (triagem). Gate de produto: só Apache/MIT/CC-BY/CC0 embarca PESO/DADO; **método é sempre livre**.

## As 7 decisões que mudam o plano

1. **O CSM deixou de ser a única opção de spine.** Surgiu o **Qwen3-TTS** (Alibaba, **Apache-2.0**, jan/2026): LM AR
   sobre codec RVQ a **12,5 Hz** (o mesmo paradigma do Mimi/CSM), **pt-BR nativo forte** (WER 1.53, spk-sim 0.817 >
   ElevenLabs), 101 ms first-packet, `-Base` fine-tunável. Ataca o **gap #1** na raiz (a base do CSM é enviesada pro
   inglês). **→ arm de maior alavancagem do trimestre: bake-off Qwen3-TTS-0.6B-Base vs CSM vs Kyutai-TTS-pt na voz do
   Pedro.** Hipótese a matar: *base pt-nativa dissolve o Estágio A inteiro*. (Único déficit do Qwen3: não condiciona em
   turnos de diálogo — irrelevante pra cascata.)
2. **Flow-matching: o lever não é trocar de spine, é o DECODER.** F5/E2/MegaTTS (NAR puro) não streamam → maus spines.
   O ouro é o **decoder flow-matching chunk-wise** (padrão CosyVoice/Kimi): mantém o LM AR do CSM, troca só o
   detokenizer acústico do Mimi → ataca #1/#2 **sem retreinar o LM**. Arm barato, alta prioridade.
3. **Deploy é "systems engineering, não modelo" (tese Sesame confirmada).** Várias ADOPTs baratas que rodam no Mac,
   sem GPU nem dado: **CUDA-graph do decode Mimi** (2,2×), **streaming+chunk adaptativo**, **stream LLM→TTS + WS
   multiplex + sessão isolada**, **barge-in por abort+flush (<300 ms)**, e — de graça no nosso código — **truncar o
   contexto na fração ouvida** (`consume_interruption()` já existe, só usar) + **flush-trick** (−300 ms de latência de
   turno). O `turn_engine.py` já é a receita moderna (Silero + Smart-Turn v3.2).
4. **Emoção: sequência de arms do mais barato ao mais caro, todos preservando o timbre do Pedro:** dual-reference áudio
   ($0) → tags-inline na LoRA → **CSP-FT** (probe: em que camada mora a emoção) → **botão α por task-vector** (autor BR,
   CC-BY, LM-based). Guardrail que decide tudo: **misturar 25–30 % do dado de pré-treino no FT** (single-speaker sem
   mistura degrada 40–50 %).
5. **RL: a ordem está PROVADA — DPO-humano de prosódia ANTES de GRPO.** GRPO sobre WER/spk-sim **colapsa a prosódia em
   fala monótona** (reward hacking, arXiv 2509.18531). ~600 julgamentos humanos de A/B restauram a prosódia. GRPO só
   escopado a **número/#3**, guardado (KL forte). Custo de treino é trivial; o custo é gerar o par (escuta).
6. **Dado sintético: "cura o sotaque e mata a alma".** Synth do nosso CSM multiplica volume e ataca #1/#3, MAS achata a
   prosódia a partir de ~50 % de razão sintética (**Synthetic Erosion**, arXiv 2605.27383). Antídoto barato e
   obrigatório: **alinhamento de preferência de duplo objetivo** contra o próprio synth. Nunca usar synth sem esse par.
7. **Eval: o measurement stack está definido.** ADOPT **win-rate/CMOS carioca** + **TTSDS2** (contra referência
   própria) + **VERSA** (plumbing Apache) + **accent-scorecard** (já construído) + TTScore/emotion2vec (TEST). **SKIP
   MOS automático como oráculo** (já virou guardrail no `eval/README`). Deploy também traz uma **obrigação legal**:
   **watermark inline** (AudioSeal MIT / silentcipher — PL 2338 + Selo Nacional de Conteúdo Sintético).

## Tabela-mestra de decisão (todos os itens, por eixo)

**Legenda:** ★ = alta alavancagem. ADOPT = plugar; TEST = arm de experimento; WATCH = vigiar; SKIP = fora.

### Arquitetura — spine (LM AR codec) · flow/NAR · codecs · full-duplex
| Item | Veredito | Nota (licença) |
|---|---|---|
| **Qwen3-TTS-12Hz-Base** | **TEST ★** | Apache — candidato a spine, pt-nativo; bake-off vs CSM |
| CSM-1B (incumbente) | TEST | Apache — baseline; único com audio-context de turnos |
| Kyutai-TTS pt | TEST | CC-BY — 3º no bake-off; sobre Mimi |
| Higgs v3-4B | WATCH/SKIP-peso | **NC** — só método (delay-pattern); v2 Apache = TEST |
| Step-Audio 2 mini / R1.1 | WATCH | Apache — spine full-duplex alt. ao Moshi (8B, ZH/EN) |
| VoxCPM2 | WATCH | Apache — tokenizer-free (fora do paradigma RVQ) |
| CosyVoice 3 / VibeVoice | SKIP | superado / off-task (long-form EN-ZH) |
| **Decoder FM chunk-wise (Kimi/StreamFlow)** | **TEST ★** | método livre — o lever real do flow-matching |
| CosyVoice 2/3-0.5B | TEST | Apache — bake-off do padrão AR+FM-decoder |
| F5/E2-TTS | WATCH | pesos **NC** (Emilia) — método/baseline só |
| Matcha / SoundStorm / MegaTTS3 | WATCH/SKIP | baseline limpo / método / capado (WaveVAE) |
| **Mimi** | **ADOPT** (manter) | CC-BY — fundido no CSM, bem escolhido |
| **T-Mimi (decoder transformer)** | **TEST→ADOPT ★** | método — 42→4,4 ms on-device, zero mudança no CSM (iOS) |
| DualCodec / XCodec2 / WavTokenizer | WATCH | MIT — só se pivotar de spine |
| DAC / SNAC | SKIP/WATCH | MIT — codec de outro stack |
| AffectCodec / U-Codec / FlexiCodec | WATCH | paper — fronteira de frame-rate/emoção |
| **SoulX-Duplug** | **ADOPT-padrão / TEST ★** | Apache — controlador de barge-in plug sobre a cascata |
| Moshi / PersonaPlex | WATCH | CC-BY / NVIDIA-OML — spine nativo parkeado |
| Freeze-Omni / LSLM | TEST-método | Freeze-Omni peso **NC**; método (LLM congelado + ouvido) livre |
| Full-Duplex-Bench | ADOPT-eval | instrumento de eval de turn-taking |

### Add-ons de TREINO — controle/emoção · RL · dados
| Item | Veredito | Nota |
|---|---|---|
| **Dual-reference áudio (timbre+emoção)** | **TEST ★** ($0) | método livre — usa o audio-conditioning do CSM |
| Tags-inline na LoRA (Orpheus/Elise) | TEST | método livre; **não embarcar peso Orpheus (base Llama)** |
| **Task-vector α (arXiv 2606.05367)** | **TEST ★** | **CC-BY, autor BR, LM-based** — botão α, preserva locutor |
| CSP-FT (probe de camada) | TEST | método — "onde mora a emoção no CSM?", publicável c/ USP |
| DTRF (conceitos) | WATCH | CC-BY — α/âncora-neutra portam; módulos NAR não |
| Steering training-free | WATCH | só flow/DiT hoje; se portar p/ AR = graal ($0) |
| **Mixed-training replay 25–30 %** | **ADOPT ★** | método — evita esquecimento (degradação 40–50 % sem) |
| **DPO-humano de prosódia** | **ADOPT ★** | método — antes de GRPO; ~600 julgamentos |
| GRPO verificável (escopado a #3) | TEST | método — só número/inteligibilidade, guardado |
| moshika-rl-seamless | WATCH | pesos **NC-SA** + 32×H100 — só se Moshi reabrir |
| RRPO / GSRM / GLM-TTS | WATCH/TEST | canário anti-hacking / RM generativo / receita GRPO MIT |
| **Contexto/turno por enunciado** | **ADOPT ★** | método — bate treinar conversa inteira (que alucina) |
| **Prosódia por IU (PSST/SAMPA)** | **ADOPT** (já default) | `prosodic_punct.py` |
| Synth do nosso CSM + DPO anti-erosão | TEST | **par obrigatório** — synth sozinho achata prosódia |
| DSP-aug (FFmpeg pitch/tempo) | TEST | **só C0/C1** — corrompe timbre se aplicado na voz |
| Emoção cross-speaker (kNN-VC) | TEST | destrava emoção pouca-data; corpus fonte NC |
| Warm-start ES / back-translation / VC-multiply | WATCH/SKIP | ganho marginal / tarefa errada / polui a voz |

### Add-ons de DEPLOY — latência · duplex/turn · compressão/edge
| Item | Veredito | Nota |
|---|---|---|
| **CUDA-graph do decode Mimi** | **ADOPT ★** | método — 2,2× no decode per-frame |
| **Streaming + chunk adaptativo** | **ADOPT ★** | método — TTFA de segundos → ~150 ms |
| **Cascata: stream LLM→TTS + WS multiplex + sessão isolada** | **ADOPT ★** | engenharia — a espinha do "parece Maya" |
| **Barge-in: abort-in-flight + flush (<300 ms)** | **ADOPT ★** | método — cancelamento, não modelo |
| **Truncar contexto na fração ouvida** | **ADOPT ★** | **código nosso pronto** (`consume_interruption`), só usar |
| **Flush-trick / endpoint semântico** | **TEST ★** | −300 ms de latência de turno; Smart-Turn já dá o sinal |
| Silero VAD + Smart-Turn v3.2 | ADOPT (já) | MIT / BSD-2 — pinar versão do ONNX |
| Backchannel-aware barge-in | TEST | não cortar em "uhum/tá" |
| sglang-omni servindo CSM | TEST | Apache — porte (CSM não é first-class); abort/logit_bias têm bug |
| Kyutai STT streaming | TEST | CC-BY — alt. ao faster-whisper, timings nativos |
| Pipecat (orquestrador) | TEST | BSD-2 — graduação se WebRTC/telefonia entrar |
| Speculative / coarse-SD / TLDR (patch-AR) | WATCH | método — quando latência virar gargalo medido |
| **Watermark (AudioSeal / silentcipher)** | **ADOPT ★** | MIT — **obrigação legal** (PL 2338 / Selo) |
| Quant 8-bit backbone / 4-bit AWQ | ADOPT / TEST | método — moat R$/min; **codec conservador (Q8/FP16)** |
| **SonoEdit (patch de pronúncia)** | **TEST ★** | LLM-based (não FlowEdit) — corrige nome/marca sem retreinar |
| Pocket-TTS pt / NeuTTS Air | TEST / WATCH | CC-BY? / Apache — edge/CPU + baseline pt-BR |
| LiveKit Turn Detector | SKIP | **licença field-of-use lock** — usar Smart-Turn (BSD-2) |
| Flow-distillation / Kokoro / FlowEdit (p/ CSM) | SKIP | flow-only / sem clone-pt / flow-only |

### Eval & métricas
| Item | Veredito | Nota |
|---|---|---|
| **Win-rate / CMOS carioca (vs ground-truth Pedro)** | **ADOPT ★** | régua-mãe; receita Sesame |
| **TTSDS2 (contra referência própria)** | **ADOPT ★** | distribucional, ρ≈0,67 vs MOS; roda sem pt no bench deles |
| **VERSA (Apache)** | **ADOPT** | plumbing — WER (#3) + spk-sim + F0 num config |
| **Accent-scorecard fonológico** | **ADOPT** (construído) | `eval/accent_scorecard.py` — gap #1 objetivo |
| TTScore (ref-free) / emotion2vec-UAR | TEST | prosódia sem referência única / emoção com juiz independente |
| MOS-preditores (UTMOS/NISQA/DNSMOS) | **SKIP-oráculo** | cegos a prosódia + viés F0 (guardrail no eval) |
| SpeechJudge / audio-LLM-judge | WATCH | pesos NC; automatizar win-rate no futuro (base Qwen-Omni Apache) |

## A matriz de experimentos (arms toggleáveis — "não deixar nada passar")

Organizada por etapa do pipeline. Cada arm = hipótese + métrica + custo + toggle no código. Os de treino ligáveis
via `runpod/experiments.py` (ARMS); os de deploy/eval no `src/duplex`/`eval/`. **Regra:** rodar grid ≤ capacidade de
escuta; medir todos na MESMA bateria (`eval/`).

### Etapa 0 — DADO (multiplicar o carioca escasso; sem GPU pesada)
| Arm | Hipótese | Métrica | Custo | Verdict |
|---|---|---|---|---|
| `data_prosodic` (SAMPA/IU) | segmentar por IU > por pausa | WER↓/F0-RMSE↓ (já: .50→.43) | $0 (já default) | ADOPT |
| `data_context_turn` | condicionar no turno anterior > conversa inteira | spk-sim + naturalidade | $0 (formato) | ADOPT |
| `data_synth_dpo` | synth-do-CSM **+** DPO anti-erosão multiplica volume sem achatar | entropia de token + NMOS | $ (compute texto) | TEST (par obrigatório) |
| `data_dspaug_c01` | DSP-aug (pitch/tempo) só em C0/C1 dá robustez | WER cauda | $0 | TEST (nunca na voz) |
| `data_emo_vc` | emoção cross-speaker via kNN-VC destrava emoção pouca-data | SER-UAR | $ | TEST |

### Etapa 1 — SPINE / BASE (o bake-off que pode dissolver o Estágio A)
| Arm | Hipótese | Métrica | Custo | Verdict |
|---|---|---|---|---|
| `spine_qwen3_base` ★ | base pt-nativa (Qwen3-TTS-0.6B-Base + LoRA Pedro) mata Estágio A e o gringo | WER + spk-sim + accent-scorecard | ~$3-6/run | **TEST (prioridade)** |
| `spine_csm` (controle) | CSM + Estágio A é o baseline honesto | idem | ~$6 | TEST |
| `spine_kyutai_pt` | Kyutai-TTS-pt (CC-BY, Mimi) como 3ª opção | idem | ~$3 | TEST |
| `decode_fm_chunk` ★ | trocar só o decoder do Mimi por FM chunk-wise melhora #1/#2 sem tocar o LM | F0/robótico | $$ (treina detokenizer) | TEST |

### Etapa 2 — VOZ (Estágio B; já no `experiments.py`)
`b2_clean` · `b2_g2p` · `b2_prop_30_70/50_50/100` (existentes) **+** `b_mixed_replay` (25–30 % replay + canary — ADOPT
como guardrail, não arm) · `b_context` (contexto de turno no treino de voz).

### Etapa 3 — CONTROLE / EMOÇÃO (do mais barato ao mais caro; F2/F3)
| Arm | Hipótese | Métrica | Custo | Verdict |
|---|---|---|---|---|
| `emo_dualref` ★ | 2ª ref só-emoção transfere estilo sem treino | SER-UAR (juiz indep.) | $0 | TEST 1º |
| `emo_tags_lora` | tags `<laugh>/<sigh>` treinadas na LoRA | detecção de evento | $ | TEST |
| `emo_cspft_probe` | congelar camadas de locutor, mexer nas de emoção | spk-sim preservado | $$ | TEST |
| `emo_taskvector_alpha` | botão α por diff de pesos (emo−neutro) | intensidade + spk-sim | $$ | TEST |
| (guardado) `emo_dpo` / `emo_grpo` | RL de emoção **só** com ≥30 min/estilo | SER-UAR | — | SKIP por ora |

### Etapa 4 — DEPLOY (roda no Mac; sem GPU/dado)
| Arm | Hipótese | Métrica | Verdict |
|---|---|---|---|
| `dep_cudagraph` ★ | CUDA-graph do decode Mimi | RTF/TTFA (alvo 2×) | ADOPT |
| `dep_stream_chunk` ★ | chunk adaptativo (1º pequeno) | TTFA <200 ms | ADOPT |
| `dep_cascade_ws` ★ | stream LLM→TTS + WS multiplex + sessão isolada | p50 <800 ms | ADOPT |
| `dep_bargein_truncate` ★ | abort+flush + **truncar contexto ouvido** | barge-in <300 ms + sem deriva | ADOPT (código pronto) |
| `dep_flush_semantic` ★ | não esperar `endpoint_ms` quando Smart-Turn confia | −300 ms turno | TEST |
| `dep_watermark` ★ | AudioSeal/silentcipher inline | detectável (compliance) | ADOPT (release) |
| `dep_quant` | 8-bit backbone (4-bit AWQ TEST), codec conservador | R$/min × qualidade no rate_app | ADOPT/TEST |
| `dep_sonoedit` | patch de pronúncia one-shot (nome/marca) | PER do alvo, resto preservado | TEST |

### Etapa 5 — EVAL (a régua que decide todos os arms acima)
`eval_winrate_carioca` (ADOPT) · `eval_ttsds2` (ADOPT) · `eval_versa` (ADOPT, plumbing) · `eval_accent_scorecard`
(ADOPT, construído) · `eval_ttscore` (TEST) · `eval_emotion2vec_uar` (TEST). **SKIP:** MOS-preditor como decisão.

## Licença (resumo do gate)
- **Passam (Apache/MIT/CC-BY/CC0):** Qwen3-TTS, Kyutai/Moshi/Pocket, Step-Audio-2, VoxCPM, CosyVoice, Matcha, Mimi,
  SoulX-Duplug, Silero, Smart-Turn, Pipecat, VERSA, AudioSeal, NeuTTS, GLM-TTS(pesos MIT), Higgs-v2. Todo **método** é livre.
- **NÃO embarcam como peso (método livre):** Higgs-**v3** (NC), F5/E2 (Emilia NC), moshika-rl-seamless (NC-SA),
  Freeze-Omni (Tencent NC), SpeechJudge-GRM (NC), **LiveKit Turn Detector** (field-of-use lock), Orpheus (base Llama),
  ESD/corpora emotivos (research-only). PersonaPlex (NVIDIA-OML — ler termos).
- **Obrigação legal:** watermark inline no release (PL 2338 / Selo Nacional de Conteúdo Sintético).

## Deep-dives (as 11 células, verificadas)
[`arch-map/arch-ar-codeclm.md`](arch-map/arch-ar-codeclm.md) · [`arch-flow-nonar.md`](arch-map/arch-flow-nonar.md) ·
[`arch-fullduplex.md`](arch-map/arch-fullduplex.md) · [`arch-codecs.md`](arch-map/arch-codecs.md) ·
[`train-control-emotion.md`](arch-map/train-control-emotion.md) · [`train-rl-pref.md`](arch-map/train-rl-pref.md) ·
[`train-data-addons.md`](arch-map/train-data-addons.md) · [`deploy-latency.md`](arch-map/deploy-latency.md) ·
[`deploy-duplex-turn.md`](arch-map/deploy-duplex-turn.md) · [`deploy-compress-edge.md`](arch-map/deploy-compress-edge.md) ·
[`eval-metrics.md`](arch-map/eval-metrics.md).
