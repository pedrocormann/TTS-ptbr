# Deploy / Compressão / Edge — mapa de fronteira (jul/2026)

> Sub-tópico: **add-on de deploy** — o que baixa custo de serving (moat R$0,02–0,12/min),
> roda em CPU/edge, e cumpre regulação (PL brasileiro de conteúdo sintético / EU AI Act).
> Lente: **avalio por mérito de método**, não por idioma. O que importa aqui é (a) o método
> transferir pro nosso stack **CSM (LM autoregressivo sobre Mimi/RVQ 12.5Hz)** + cascata, e
> (b) licença de peso/dado embarcável (gate Apache/MIT/CC-BY/CC0).
> Marcação honesta: **[V]** verificado na web hoje · **[I]** inferido do conhecimento.

---

## TL;DR de decisão

1. **Watermark é a única peça de deploy que é obrigação legal, não otimização.** Dois candidatos
   MIT prontos: **AudioSeal** (Meta) e **silentcipher** (Sony). A própria **SesameAILabs forkou o
   silentcipher** — sinal forte de que é o watermark alinhado ao pipeline CSM. Nosso ROADMAP M3 já
   nomeia silentcipher. **ADOPT** um dos dois no release; custa ~1 chamada de função.
2. **"Distillation" no sentido flow-matching NÃO se aplica ao CSM.** CSM é LM autoregressivo, não
   difusão/flow. A explosão de papers de destilação few-step (RapFlow, dots.tts, ZipVoice, IntMeanFlow)
   acelera *decoders de flow* — não o nosso backbone. A alavanca de velocidade correta pro CSM é
   **quantização 4/8-bit + speculative decoding + AR patch-based (TLDR)**. Não gastar tempo caçando
   destilação flow.
3. **Patch de pronúncia pós-deploy: a peça nomeada no brief (FlowEdit) é flow-matching-only e NÃO
   serve.** O primo correto pro CSM é **SonoEdit** (edição null-space de TTS LLM-based, edit em
   forma-fechada, sem loop de treino). É o caminho certo pra corrigir nomes/marcas cariocas depois
   do deploy sem re-treinar. **TEST.**
4. **On-device já é realidade pra speech-LMs do nosso porte.** **NeuTTS Air** (748M, Apache-2.0, GGUF
   Q4 em celular/Pi) e **Pocket-TTS** (Kyutai, 100M, ~6× realtime em CPU, **suporta português**)
   provam que um LM-sobre-codec de 0.1–0.75B quantiza pra Q4 e roda em CPU. Isso é a prova de
   conceito de que **CSM-1B quantizado serve barato** — e um possível atalho de baseline pt-BR.

---

## 1. Watermark inline (compliance — PL brasileiro + EU AI Act)

**Por que agora:** o PL brasileiro de conteúdo sintético (tramitando apensado ao **PL 2338/2023**,
Marco da IA) exige identificador de autenticidade em áudio gerado por IA — "marca d'água + metadados
assinados", Selo Nacional de Conteúdo Sintético. [V] O EU AI Act já exige saída "machine-readable e
detectável como gerada artificialmente". Watermark inline (embutido no waveform, não só metadado que
some no re-encode) é a forma robusta. **Isto é gate de produto, não nice-to-have.**

| Ferramenta | Licença | Estado | Nota pro nosso stack |
|---|---|---|---|
| **AudioSeal** (Meta) | **MIT** (código **e** pesos, desde abr/2024) [V] | Released, v0.2 com **streaming** (dez/2024); SOTA robustez + detector rápido (single-pass, ~2 ordens de grandeza mais rápido) [V] | Funciona em **16k e 24k** — casa com saída Mimi (24kHz). Localizado (detecta trecho a trecho). **ADOPT-candidato #1**: pesos MIT = zero risco de gate. |
| **silentcipher** (Sony) | **MIT** (código); pesos sem licença explícita [V] | Released (INTERSPEECH 2024), pip; robusto a MP3/OGG/AAC 64–256kbps; psicoacústico | **SesameAILabs mantém um fork** → alinhado ao CSM. 16k/44.1k. Já no nosso M3. **ADOPT-candidato #2**; só resolver a lacuna de licença dos pesos antes de embarcar. |
| **Perth Watermarker** | vem embutido no **NeuTTS Air** (Apache) e Chatterbox [V] | Released | Referência: modelos on-device já saem com watermark por padrão. Se adotarmos NeuTTS/Chatterbox como baseline, watermark vem de graça. |

**Veredito:** **ADOPT** (AudioSeal como default por pesos-MIT + streaming + 24kHz nativo; silentcipher
como alternativa por já ser o do Sesame). **Caveat honesto [V]:** existem ataques adaptativos que
removem watermark (HarmonicAttack, arXiv 2511.21577; "Learning to Evade", 2606.22310). Watermark é
**sinal de compliance**, não DRM à prova de adversário — vender como "cumpre a lei", não como
"impossível de remover".

---

## 2. Quantização 4/8-bit (moat de serving)

**Fato central [V/I]:** ninguém publicou benchmark int4/int8 *específico do CSM-1B*. Mas o backbone
do CSM é **Llama-style**, então a receita padrão de deploy (treina 16-bit → quantiza 4-bit;
GGUF/llama.cpp, AWQ, GPTQ, FP8) aplica direto. [V] Prova por vizinhança: **NeuTTS Air (748M speech-LM
Qwen2) roda em Q4/Q8 GGUF em celular e Raspberry Pi** — isto é a evidência de que um LM-sobre-codec do
nosso porte sobrevive a 4-bit sem colapsar. [V]

- **Método é livre** (técnica, não peso de terceiro) — passa o gate trivialmente.
- Alvos práticos: **AWQ/GPTQ 4-bit** pro serving em GPU (4× menos memória, mais requests/GPU →
  ataca o R$/min direto); **GGUF Q4_K_M** pro caminho CPU/edge; **FP8** se formos pra GPU nova.
- ExecuTorch (Meta, 1.0 GA out/2025) e MLX (Apple Silicon) são os runtimes de edge maduros. [V]

**Cuidado [I]:** o **decoder Mimi é GAN, não o gargalo** e é sensível — quantizar o codec agressivo
degrada timbre mais que quantizar o backbone. Quantizar **backbone forte (Q4), codec conservador
(Q8/FP16)**. O gargalo de latência é o backbone AR, e é ali que 4-bit paga.

**Veredito:** **ADOPT** (backbone 8-bit já; testar 4-bit AWQ quando formos medir R$/min).
**TEST** especificamente o par (Q4 backbone × qualidade percebida no rate_app) — nossa régua própria,
não WER, decide.

---

## 3. "Distillation" / aceleração de inferência — a parte que confunde

**Correção estrutural [V]:** a onda 2025–2026 de destilação de TTS (**RapFlow-TTS, dots.tts,
IntMeanFlow, ZipVoice, DSFlow, Fast F5-TTS**) comprime o **ODE de flow-matching** pra 1–4 passos
(RTF 0.03, first-packet 54–85ms). Impressionante — **mas é para arquiteturas flow/difusão. O CSM não
é flow.** Portar isso pro CSM = trocar de arquitetura, não "acelerar o CSM".

O que **de fato** acelera um TTS **autoregressivo** como o CSM [V]:
- **Speculative decoding pra AR-TTS** (Li/Lin 2025) — draft-and-verify em nível de token de codec.
- **TLDR** (arXiv 2606.09019, jun/2026) — modela **patches de tokens de codec** em vez de token a
  token: patch=4 → **1.8× speedup e −75% de KV-cache**. Ataca custo e memória juntos.
- **Quantização** (seção 2).

**Veredito:**
- Destilação flow-matching → **SKIP** pro caminho CSM (WATCH só se algum dia adotarmos um TTS flow —
  aí ZipVoice/dots.tts viram relevantes; ZipVoice é forte e barato).
- Speculative decoding + **TLDR** (patch-AR) → **TEST** quando latência/custo virar gargalo medido.
  Método livre, transfere (é agnóstico de idioma).

---

## 4. Patch de pronúncia pós-deploy (nomes/marcas — o gap #3 vira operável)

O brief pede "patch FlowEdit-style". Aqui há uma **decisão de arquitetura que muda o veredito**:

| Técnica | Aplica ao CSM? | Como funciona | Veredito |
|---|---|---|---|
| **FlowEdit** (arXiv 2606.20518, jul/2026) | **NÃO** — flow-matching only [V] | Memória Hopfield de correções em espaço de embedding; −92,7% PER em nome-alvo; correção em ~15s/1 GPU; zero forgetting | **WATCH** — a técnica nomeada no brief não serve ao nosso stack AR. Guardar caso adotemos TTS flow. |
| **SonoEdit** (arXiv 2601.17086, jan/2026) | **SIM — feito pra TTS LLM-based** [V] | **Null-Space Pronunciation Editing**: acha via causal tracing as camadas que mapeiam texto→pronúncia e faz **um update em forma-fechada** (matriz), corrigindo a palavra e **provadamente preservando o resto**. Sem loop de treino, one-shot. | **TEST** — é o análogo correto do FlowEdit pro **CSM (LM-based)**. |

**Por que isso importa pra nós [I]:** nosso #3 é leitura de número + nomes/marcas. Re-treinar a cada
"Ipanema/Sesc/Niterói/Xerém" que sai errado é caro e arrisca esquecer o resto. Um editor **one-shot,
sem treino, que preserva o modelo** é exatamente a ferramenta de operação pós-deploy — mantém um
"dicionário vivo" de correções cariocas sem tocar nos pesos treinados. Transfere entre falantes
(edição em espaço agnóstico de locutor). **Ambos os papers: método livre; código/licença não
confirmados [V]** — validar disponibilidade antes de depender.

**Veredito:** **TEST SonoEdit** como camada de pronúncia; **SKIP FlowEdit** pro CSM (WATCH arquivado).

---

## 5. Modelos pequenos / on-device (CPU realtime, edge, baseline barato)

| Modelo | Params | Licença | pt-BR? | Nota |
|---|---|---|---|---|
| **Pocket-TTS** (Kyutai) | 100M | **não declarada na página** — padrão Kyutai = CC-BY pesos [I]; **verificar** | **SIM (en/fr/de/pt/it/es)** [V] | **~6× realtime em CPU (M4, 2 cores), ~200ms 1º chunk, clone por wav.** Mesmo lab do **Mimi/Moshi** → codec da mesma família do nosso stack. Jan/2026. **TEST** — possível engine de edge e baseline pt-BR barato. Gate depende da licença (CC-BY passa; confirmar). |
| **NeuTTS Air** (Neuphonic) | 748M (Qwen2) | **Apache-2.0** [V] | en-centrado [V] | **GGUF Q4/Q8 em celular/Pi**, clone em 3s, **Perth watermark embutido**. Prova viva de que um speech-LM ~0.75B quantiza e roda on-device. Irmão **Nano 229M**. **WATCH/TEST** — referência de engenharia pro caminho "CSM on-device"; gate-limpo (Apache). |
| **Kokoro-82M** | 82M | **Apache-2.0** [V] | **não** (en + 7) | CPU 14× realtime (M1 Mini), #1 TTS Arena no lançamento. **SKIP pro core carioca** (não clona, sem pt-BR); **WATCH** como engine de fallback pra utterances não-clonadas/sistema. |

**Leitura estratégica [I]:** não trocamos o CSM por esses — o valor deles é (1) **prova de que
on-device é viável no nosso porte** (calibra a ambição de "CSM-1B Q4 em CPU"), (2) **Pocket-TTS é um
atalho de baseline pt-BR do mesmo ecossistema Kyutai/Mimi** que dá pra plugar no rate_app cego já, e
(3) NeuTTS mostra o combo pronto (GGUF + watermark + clone) que é o alvo de arquitetura do nosso
deploy edge.

---

## Ranking de ação (o que fazer com isto)

- **ADOPT já:** watermark no release (**AudioSeal** MIT/streaming/24kHz, ou **silentcipher** que o
  Sesame usa) — é obrigação legal iminente e custa quase nada. Quantização **8-bit do backbone** no
  serving.
- **TEST (arm barato):** (a) **4-bit AWQ/GGUF do backbone CSM** medido no rate_app (qualidade × R$/min);
  (b) **SonoEdit** como camada de correção de nome/marca carioca pós-deploy; (c) **Pocket-TTS pt-BR**
  como baseline cego no rate_app (confirmar licença antes).
- **WATCH:** TLDR/speculative-decoding (acionar quando latência virar gargalo medido); NeuTTS Air como
  blueprint de edge; FlowEdit e destilação flow-matching (só se adotarmos TTS flow).
- **SKIP:** destilação flow-matching aplicada ao CSM; Kokoro pro core carioca.

## Fontes (verificadas hoje)
- AudioSeal — github.com/facebookresearch/audioseal (MIT código+pesos; v0.2 streaming)
- silentcipher — github.com/sony/silentcipher (MIT); fork em github.com/SesameAILabs/silentcipher
- Kokoro-82M — huggingface.co/hexgrad/Kokoro-82M (Apache-2.0)
- NeuTTS Air — huggingface.co/neuphonic/neutts-air (Apache-2.0, GGUF, Perth watermark)
- Pocket-TTS — kyutai-labs.github.io/pocket-tts (100M, CPU 6×, pt incluído)
- FlowEdit — arXiv 2606.20518 (flow-matching only)
- SonoEdit — arXiv 2601.17086 (null-space edit, LLM-based TTS)
- TLDR (patch AR-TTS) — arXiv 2606.09019 (1.8× / −75% KV)
- PL brasileiro de conteúdo sintético — apensado ao PL 2338/2023 (camara.leg.br)
- Quantização/edge — llama.cpp GGUF, AWQ/GPTQ/FP8, ExecuTorch 1.0, MLX
