# Dossier 50 (jun/2026) — Controle de emoção e sotaque: SOTA 2025-2026

> FRENTE 7 da pesquisa de 2026-06-10. Pergunta-mestra: **o que mudou desde as
> crenças registradas em 2026-05-17** sobre (a) controle de emoção, (b) sotaque/
> dialeto, (c) transferência de emoção entre vozes, (d) tags paralinguísticas
> (backchannel/risada/disfluência) e (e) voice-embedding vs LoRA-por-voz.
> Todas as licenças abaixo foram verificadas na fonte primária (HF API / GitHub)
> em 2026-06-10.

## TL;DR — o que mudou desde 2026-05-17

1. **Qwen3-TTS (22/jan/2026) é o fato novo mais decisivo da frente**: suíte TTS
   open da Alibaba, **Apache-2.0, com português na saída** (10 línguas), tokenizer
   12.5Hz, latência ~97ms, clone de voz com 3s, controle de emoção por instrução
   em linguagem natural, **código oficial de finetune** (SFT single-speaker).
   Substitui Kokoro/Chatterbox como gerador license-clean de dado sintético e
   vira candidato sério a componente de voz/TTS do produto.
2. **A interface de emoção convergiu para natural-language style prompt** (não
   tags discretas): EmoVoice (ACMMM'25), Qwen3-TTS instruct, StepAudio 2.5 TTS
   ("No tags, no preset combos. Just describe what you want"). Tags discretas
   sobrevivem para **eventos pontuais** (risada, suspiro) — vocabulário ~8-20 tags.
3. **RL paralinguístico (GRPO multi-reward) virou receita padrão pós-SFT**, não
   mais exclusividade do Step-Audio 2: EMORL-TTS (ICASSP 2026), GLM-TTS (MIT,
   dez/2025), RRPO, PALLM. E agora **existe código GRPO/DPO/SFT aberto e pequeno**
   (Step-Audio-EditX 3B, 12GB VRAM, código Apache-2.0) — RL leve ficou viável em Colab.
4. **Sotaque por aritmética de pesos (task/accent vectors) é a novidade 2026**:
   Accent Vector (Interspeech 2026) e HE-Vector compõem dialeto+emoção sem dados
   conjuntamente rotulados, com **interpolação contínua de intensidade de sotaque**.
   É o caminho tecnicamente mais elegante para as 5 sub-variações cariocas.
5. **Crença "emoção = base implícita + style prompt + RL leve" CONFIRMADA e
   reforçada.** Crença "Chatterbox/Kokoro para dado sintético" SUPERADA por
   Qwen3-TTS (pt nativo + finetune). Step-Audio 2.5 (mai/2026) é **API-only** —
   não muda nada no produto.

---

## (a) SOTA de controle de emoção em speech-LMs

### As 5 famílias em 2026

| Família | Exemplos | Prós | Contras | Cabe em LoRA pequeno? |
|---|---|---|---|---|
| **Tags discretas inline** | Orpheus `<laugh>`, Dia, Maya1 (20+ tags), CosyVoice3 `[laughter]`/`[breath]`, Chatterbox Turbo `[laugh]` | barato, dado fácil de rotular, eventos pontuais precisos | granularidade limitada, pode soar "colado", interface datada p/ estilo global | **SIM** — Orpheus: efeito visível com ~50 exemplos, ideal ~300/falante |
| **Natural-language style prompt** | EmoVoice (arXiv 2504.12867, ACMMM'25), Qwen3-TTS instruct, StepAudio 2.5 TTS, CosyVoice3 instruct | granularidade livre ("alegria contida com orgulho"), interface vencedora 2026 | exige dado com descrições NL (caption de emoção); cobertura de estilo depende do treino | **SIM com dado certo** — EmoVoice-DB = só 40h com descrições NL e deu SOTA |
| **Referência de áudio (emotion prompt)** | IndexTTS-2, CosyVoice3, EmoVoice variante | controle "mostre, não descreva"; bom p/ transfer | exige clipe de referência por emoção em runtime; IndexTTS-2 = licença restrita (veto) | SIM (in-context, nem precisa treinar) |
| **RL paralinguístico (GRPO/DPO)** | Step-Audio 2 (2507.16632), EMORL-TTS (2510.05758, ICASSP'26), GLM-TTS (2512.14291, MIT), RRPO (2512.04552), PALLM (2603.15981) | maior salto de qualidade percebida 2025→26; alinha emoção SEM rotular tudo | reward model + infra; risco de reward hacking (RRPO ataca isso) | **AGORA SIM** — Step-Audio-EditX libera SFT+DPO+GRPO p/ modelo 3B / 12GB VRAM |
| **Activation steering (training-free)** | EmoSteer-TTS (2508.03543) | ZERO treino; controle contínuo (conversão/interpolação/apagamento de emoção) | só modelos flow-matching (F5-TTS, CosyVoice2, E2-TTS) — não vale p/ spine AR tipo Moshi | n/a (não treina nada) |

### Detalhes que importam

- **EmoVoice** ([arXiv 2504.12867](https://arxiv.org/abs/2504.12867), ACMMM 2025,
  [código/checkpoints](https://github.com/yanghaha0908/EmoVoice)): TTS LLM-based com
  *freestyle* NL emotion prompt + variante "phoneme boost" (fonemas e tokens de áudio
  em paralelo, CoT/CoM) para não degradar inteligibilidade. **EmoVoice-DB: 40h de
  inglês com rótulos finos em linguagem natural — e o SOTA foi atingido com dado
  sintético.** Lição direta: nosso dataset dirigido do Pedro deve ter **descrições NL
  de estilo por trecho** (não só rótulo "feliz/triste"), e 40h é teto, não piso.
- **Step-Audio 2** ([2507.16632](https://arxiv.org/abs/2507.16632)): confirmado o
  pipeline SFT → reward model → PPO (comprimento/qualidade) → **GRPO 400 iterações**
  para realismo perceptual. 76.55% no benchmark paralinguístico próprio (gênero,
  idade, timbre, emoção, pitch, ritmo, velocidade, estilo).
- **StepAudio 2.5** ([tech report 2605.23463](https://huggingface.co/papers/2605.23463),
  [release mai/2026](https://www.marktechpost.com/2026/05/24/stepfun-releases-stepaudio-2-5-realtime-an-end-to-end-voice-model-with-roleplay-specific-rlhf-and-paralinguistic-comprehension/)):
  RLHF específico de persona/roleplay, 1º lugar nos 5 eixos do bench (abr/2026), zh/en,
  **API-only (wss://api.stepfun.com), sem pesos abertos até 2026-06-10** → estudar a
  receita, não usar o modelo. O [TTS 2.5](https://x.com/StepFun_ai/status/2046571983744479499)
  declara a tese da época: *"Control emotion, pacing, pauses and delivery with plain
  natural language. No tags, no preset combos."*
- **GLM-TTS** ([GitHub Apache-2.0](https://github.com/zai-org/GLM-TTS),
  [pesos MIT no HF](https://huggingface.co/zai-org/GLM-TTS), [2512.14291](https://arxiv.org/abs/2512.14291)):
  zero-shot TTS zh/en com **GRPO multi-reward (4 rewards, incl. reward de emoção)**.
  Confirma: a receita RL-para-expressividade está commoditizada e license-clean.
- **EMORL-TTS** ([2510.05758](https://arxiv.org/abs/2510.05758), ICASSP 2026): SFT+GRPO
  com 3 rewards — acurácia de categoria de emoção, **intensidade no espaço VAD
  (valence-arousal-dominance)** e clareza de ênfase local. Modelo de como fazer
  controle de *intensidade* (não só categoria).
- **RRPO** ([2512.04552](https://arxiv.org/abs/2512.04552)): ataca reward hacking em
  otimização de reward diferenciável p/ TTS emocional — ler antes de montar nosso RL.
- **PALLM** ([2603.15981](https://arxiv.org/abs/2603.15981), mar/2026): multi-task RL
  (classificação de sentimento do áudio + geração de resposta paralinguisticamente
  consciente) com CoT; +8-12% sobre baselines em Expresso/IEMOCAP/RAVDESS, supera
  GPT-4o-audio e Gemini-2.5-Pro. Relevante porque alinha **entendimento e geração**
  juntos — exatamente o que um spine conversacional precisa.
- **EmoSteer-TTS** ([2508.03543](https://arxiv.org/abs/2508.03543)): training-free,
  extrai steering vectors de dataset emocional e os aplica na ativação de modelos
  flow-matching (F5-TTS/CosyVoice2/E2-TTS): conversão, **interpolação (intensidade
  contínua)** e remoção de emoção. Não serve para o spine AR (Moshi), mas é útil
  no pipeline de **dado sintético emocional** com F5/CosyVoice.
- **CSP-FT** ([2501.14273](https://arxiv.org/abs/2501.14273)): em TTS LLM-based,
  informação de emoção e de speaker se concentra em camadas específicas; finetune de
  **apenas 2 camadas (~8% dos parâmetros) ≈ full finetune**, 2× mais rápido, mitiga
  catastrophic forgetting. Implicação prática: nosso LoRA não precisa cobrir todas as
  camadas — vale sondar (probing) onde emoção/speaker vivem no backbone escolhido e
  concentrar rank lá.

### O que é prático num finetune LoRA pequeno (Colab)

Receita recomendada, em ordem de custo:
1. **SFT LoRA com mistura: tags pontuais + descrição NL de estilo no texto.**
   Dado: gravação dirigida do Pedro com (i) tags de evento (`<risada>`, `<suspiro>`,
   `<pigarro>`) e (ii) caption NL por trecho ("irônico, acelerando no final").
   Evidência de viabilidade: Orpheus = ~50-300 exemplos/falante p/ tags;
   EmoVoice = 40h c/ descrições NL bastaram p/ SOTA.
2. **Probing de camadas (CSP-FT)** para colocar LoRA onde emoção mora — ganha
   qualidade sem subir rank.
3. **DPO leve antes de GRPO**: pares preferidos/rejeitados julgados por SER pt-BR +
   UTMOS + julgamento humano do Pedro. Código de referência:
   [Step-Audio-EditX `script/`](https://github.com/stepfun-ai/Step-Audio-EditX)
   (SFT, DPO, GRPO liberados em 29/jan/2026; modelo 3B roda em 12-16GB VRAM).
4. **GRPO multi-reward** (categoria + intensidade VAD + naturalidade) só depois que
   o eval harness pt-BR existir — sem reward confiável, RL só amplifica viés.

---

## (b) Sotaque/dialeto em TTS — e as 5 sub-variações cariocas

### O cardápio de mecanismos (2025-2026)

| Mecanismo | Paper/modelo | Estado |
|---|---|---|
| **Speaker embedding "carrega" o sotaque** (entrelaçado) | [2601.14417](https://arxiv.org/abs/2601.14417) quantifica: embeddings de speaker **sobrepõem/preservam regras fonológicas** (métrica *phoneme shift rate*) | baseline implícito de todo zero-shot TTS; pouco interpretável |
| **Accent embedding dedicado** | Scalable Controllable Accented TTS ([2508.07426](https://arxiv.org/abs/2508.07426), ASRU 2025): labels de sotaque descobertos por **geolocalização de fala** (sem anotação humana) + **kNN-VC para augmentar timbre** (desentrelaça sotaque de voz); embedding médio por sotaque sobre CommonVoice; supera XTTS-v2 c/ self-reported labels | maduro; recеita replicável p/ pt-BR via Common Voice/corpora BR |
| **Tags/instrução textual de dialeto** | CosyVoice3 ([2505.17589](https://arxiv.org/abs/2505.17589), [pesos Apache-2.0](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)): 18+ dialetos chineses por instruct, **combina dialeto×emoção** ("cantonês alegre"); Step-Audio-EditX: tag `[Sichuanese]`/`[Cantonese]`; Qwen3-TTS: vozes preset dialetais (Pequim, Sichuan) | provado em escala p/ dialetos chineses; ninguém fez p/ pt-BR |
| **Task/accent vectors (aritmética de pesos)** | **Accent Vector** ([2603.07534](https://arxiv.org/abs/2603.07534), submetido Interspeech 2026): finetuna em fala nativa de outra língua, extrai o delta de pesos como "vetor de sotaque", **escala/interpola → intensidade contínua e sotaques mistos, SEM dado acentuado em inglês**; **HE-Vector** ([2512.18699](https://arxiv.org/abs/2512.18699)): composição hierárquica dialeto+emoção sem dado conjuntamente rotulado | a novidade 2026; elegante p/ sub-variações e p/ compor sotaque×emoção |
| **MoE por dialeto + frontend IPA** | DiaMoE-TTS ([2509.22727](https://arxiv.org/abs/2509.22727)): F5-TTS + MoE dialect-aware sobre IPA unificado; novas variantes via **LoRA + conditioning adapter com poucas horas**; zero-shot p/ dialetos não vistos | melhor resposta acadêmica ao caso "dialeto com <10h de dado" |
| **Vozes separadas por variação** | prática de produto (Fish Audio vende sotaques regionais BR como vozes distintas) | simples, escala mal, mas é o que o mercado faz hoje |

### Tradução para o caso carioca (5 sub-variações, dataset = Pedro)

Realidade: **não existe paper de sotaque carioca/pt-BR** (busca 2026-06-10 não achou
nada acadêmico 2025-26 — só posts comerciais; [Fish Audio](https://novascientia.com.br/melhores-tts-ferramentas-texto-para-fala/)
explora sotaques regionais BR como diferencial de produto). Owning isso é ativo.

Plano recomendado, em camadas de risco crescente:
1. **v0 — referência in-context por variação (custo ~zero):** Pedro grava 30-60min
   *por variação* (carioca médio, zona sul, cria, surfista, interior) com consistência
   interna; cada variação vira um **voice prompt/persona** distinto no modelo
   (in-context cloning). A literatura (2601.14417) diz que o speaker embedding carrega
   sotaque — aqui isso é *feature*, não bug, porque o "speaker" É a variação.
2. **v1 — tag textual de variação no SFT LoRA:** prefixo `[carioca:cria]` etc. no
   texto (receita CosyVoice3/EditX). Requer ≥1-5h por variação; o modelo aprende a
   chavear mantendo o timbre do Pedro. É o mecanismo certo quando as 5 variações
   compartilham a MESMA voz.
3. **v2 — task vectors por variação (Accent Vector/HE-Vector):** 1 LoRA por variação
   → delta de pesos = "vetor carioca-X"; interpolar dá **continuum** (ex.: 0.3·cria
   + 0.7·médio) e compõe com vetor de emoção sem dado rotulado conjunto. Também
   permite *aplicar* a variação numa segunda voz futura.
4. **Se faltar dado:** receita DiaMoE-TTS (IPA frontend + adapter + LoRA, <10h) e
   augmentação kNN-VC (2508.07426) para multiplicar timbres dentro da mesma variação
   (desentrelaça "sotaque" de "voz do Pedro" — útil p/ generalizar depois).

Cuidado registrado pela literatura: variações do MESMO sotaque são muito mais
próximas entre si do que dialetos chineses entre si — o risco de as 5 variações
colapsarem numa só é real. Mitigação: script de gravação maximizando os traços
distintivos (chiado do /s/, vogais, léxico, ritmo), e eval com classificador de
variação treinado no próprio dataset (se um classificador não separa, o TTS não vai separar).

---

## (c) Transferência de emoção entre vozes (dataset X → voz do Pedro)

Estado da arte 2025-2026 — quatro rotas, todas evitando o vazamento de identidade:

1. **Desentrelaçamento explícito (cross-speaker emotion transfer clássico evoluído):**
   - **DiEmo-TTS** ([2505.19687](https://arxiv.org/abs/2505.19687), Interspeech 2025):
     distilação self-supervised + clustering de emoção; minimiza perda de informação
     emocional E preserva identidade do speaker — ataca diretamente o "speaker leakage"
     dos métodos de compressão de timbre.
   - **EMM-TTS** ([2510.11124](https://arxiv.org/abs/2510.11124)): 2 estágios sobre
     representações SSL **perturbadas no speaker** → controle independente de emoção e
     timbre, inclusive cross-lingual (importante: nossa emoção viria de dataset en/zh
     para fala pt — o caso cross-lingual é o nosso).
2. **Task vectors de emoção (HE-Vector, [2512.18699](https://arxiv.org/abs/2512.18699)):**
   treinar vetor de emoção em dataset emocional X, vetor de voz/dialeto no dataset do
   Pedro, **composição hierárquica zero-shot** — sem nunca ver "Pedro bravo" no treino.
   É a rota mais alinhada com LoRA-first.
3. **Training-free (EmoSteer-TTS):** steering vectors de emoção extraídos de dataset
   multi-speaker aplicam-se a **qualquer voz** na inferência (modelos flow-matching).
4. **Edit-after-generate (Step-Audio-EditX, [2511.03601](https://arxiv.org/abs/2511.03601)):**
   gerar neutro com a voz-alvo e **editar a emoção/estilo do áudio pronto** (iterativo,
   melhora a acurácia a cada iteração). Sem pt hoje (zh/en/ja/ko + dialetos zh), mas o
   paradigma (e o código de treino) é portável.

**Implicação prática para o projeto:** a transferência funciona e está madura, MAS
todos os resultados fortes são en/zh. O risco específico nosso é **vazamento de
sotaque/fonética da língua do dataset emocional para o pt-BR**. Estratégia de menor
risco continua sendo **gravar a emoção na própria voz do Pedro** (a gravação dirigida
já planejada deve incluir matriz emoção × variação mínima) e usar transfer (rotas 2-3)
apenas para *ampliar* cobertura de emoções raras + dado sintético emocional pt-BR via
Qwen3-TTS instruct para robustez.

---

## (d) Backchannels, risadas e disfluências controláveis

### Tags paralinguísticas em TTS (quem tem o quê — licenças verificadas)

| Modelo | Tags | Licença (verificada HF API 2026-06-10) | pt? |
|---|---|---|---|
| **Orpheus** ([GitHub](https://github.com/canopyai/Orpheus-TTS)) | `<laugh> <chuckle> <sigh> <cough> <sniffle> <groan> <yawn> <gasp>` | Apache-2.0 | **NÃO** — multilingual preview = de, fr, es_it, ko, zh, hi ([lista HF](https://huggingface.co/canopylabs)) |
| **Dia-1.6B** (nari-labs) | nonverbal `(laughs)` etc. | Apache-2.0 | não (en) |
| **Maya1** ([HF](https://huggingface.co/maya-research/maya1)) | **20+ tags** (`<laugh> <laugh_harder> <sigh> <whisper> <angry> <giggle> <gasp> <cry>`…) + **voice design por descrição NL** `<description="40yo, low-pitch, warm">` | Apache-2.0 | não (en multi-accent; "futuros modelos" p/ outras línguas) |
| **CosyVoice3-0.5B** ([HF](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)) | `[laughter] [breath]` + instruct | Apache-2.0 | não (9 línguas, sem pt) |
| **Chatterbox Turbo** ([HF](https://huggingface.co/ResembleAI/chatterbox-turbo)) | `[laugh] [cough] [chuckle]`… 350M, sub-200ms | MIT | **Turbo: só en.** Chatterbox Multilingual (MIT) tem **pt** mas sem tags (só `exaggeration`) |
| StepAudio 2.5 TTS | **sem tags** — tudo por NL description | API-only | não |

Leitura: o "padrão Orpheus" (tags inline) virou commodity; a fronteira é a fusão
**tags p/ eventos + NL p/ estilo global** (Maya1 = melhor template de produto/dado).
**Ninguém tem tags paralinguísticas em pt-BR** — `<risada>`, `<suspiro>`, "uhum",
"é...", "tipo..." gravados no dataset do Pedro é diferencial barato e imediato.

### Backchannels em conversação (full-duplex)

- Em arquiteturas parallel-stream (dGSLM → Moshi), backchannel/risada **emergem do
  dado de 2 canais** — sem controle explícito. O que mudou em 2026:
- **F-Actor** ([2601.11329](https://arxiv.org/abs/2601.11329), rev. abr/2026):
  **primeiro modelo full-duplex open instruction-following** — controla backchanneling,
  interrupção, voz, tópico e iniciativa **por instrução explícita**, com encoder de
  áudio congelado + finetune só do LM, **apenas ~2.000h de dado**, single-stage,
  modelo+código liberados. É a validação direta da nossa rota "Moshi + LoRA + dado
  dirigido": comportamento conversacional controlável SEM pretrain em escala.
- **DuplexSLA** ([2605.20755](https://arxiv.org/abs/2605.20755), mai/2026): turn-taking
  semântico (pause/interrupt/backchannel) dentro do próprio backbone, sem VAD externo;
  traz DuplexSLA-Bench.
- **Benchmarks/desafios**: [Full-Duplex-Bench v1.5](https://arxiv.org/abs/2507.23159)
  (cenários de overlap incl. backchannel "uh-huh" <1s/<2 palavras),
  [ICASSP 2026 HumDial Challenge](https://arxiv.org/abs/2604.21406) (métricas de
  interação: interrupção, timing, retomada), e **predição contínua e multilíngue de
  backchannel** ([2512.14085](https://arxiv.org/abs/2512.14085)) — cross-lingual, útil
  para validar se padrões de "uhum/aham" pt-BR diferem dos en/ja (diferem).

**Implicação:** para o spine, backchannels pt-BR vêm do **dado estéreo 2 canais**
(reforça a frente de sourcing do dossier 21) + instrução à la F-Actor para ligar/
desligar comportamento ("modo ouvinte ativo"). Para o TTS/voz, tags inline pt-BR.

---

## (e) Voice embedding vs LoRA-por-voz em 2026

### O que a literatura e a prática dizem

- **Zero-shot in-context (referência de áudio) segue dominante para multi-voz**:
  MiniMax-Speech ([2505.07916](https://arxiv.org/abs/2505.07916)) com **learnable
  speaker encoder** (o embedding do speaker é um conjunto de parâmetros otimizáveis —
  ponte entre zero-shot e finetune); Qwen3-TTS-Base = clone com 3s; Chatterbox
  Multilingual = clone zero-shot em 23 línguas incl. pt.
- **LoRA-por-voz ganhou evidência quantitativa em 2026**:
  - *When Fine-Tuning Fails and when it Generalises* ([2603.10904](https://arxiv.org/abs/2603.10904),
    mar/2026): LoRA no backbone LLM (Qwen-0.5B TTS) **melhora consistentemente
    fidelidade de speaker sem degradar a parte linguística — MAS o ganho é governado
    pela DIVERSIDADE do dado**: dado acusticamente uniforme amplifica artefatos/ruído.
    (→ a gravação dirigida do Pedro deve variar microfone? Não — variar *conteúdo,
    energia, prosódia*; manter captação limpa e única.)
  - LoRP-TTS ([2502.07562](https://arxiv.org/abs/2502.07562)), CSP-FT
    ([2501.14273](https://arxiv.org/abs/2501.14273) — 2 camadas ≈ full FT) e a prática
    de mercado ([guia LoRA Qwen3-TTS](https://instavar.com/blog/ai-production-stack/LoRA_Finetuning_Qwen3_TTS_Custom_Voices):
    LoRA é o regime certo até ~10h por voz) consolidam: **LoRA-por-voz = melhor
    fidelidade/estabilidade de identidade quando a voz é "hero"**.
  - **Qwen3-TTS finetune oficial** ([pasta finetuning](https://github.com/QwenLM/Qwen3-TTS/tree/main/finetuning)):
    SFT **single-speaker** (JSONL `audio`/`text`/`ref_audio`); multi-speaker prometido.
- **O caso Kyutai é instrutivo para a ética/UX**: o modelo de voice-embedding do
  Kyutai TTS **não foi liberado** (anti-abuso); em vez disso, repositório
  [kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices) com **228 vozes doadas
  (CC0)** + vozes VCTK CC-BY — i.e., produto multi-voz via **catálogo de embeddings
  pré-computados e consentidos**, não cloning aberto. Modelo a imitar no nosso produto
  (consentimento + watermark, dossier 70).

### Prática vencedora 2026 (síntese)

**Híbrido, não ou-ou:**
1. **Base multi-speaker** treinada/adaptada com dado diverso (evita o colapso apontado
   por 2603.10904);
2. **Identidade por referência in-context** (voice prompt) para vozes "comuns" e para
   as N variações de uma mesma voz;
3. **LoRA pequeno por voz "hero"** (Pedro) por cima — máxima fidelidade e estabilidade
   de identidade em diálogo longo (o speaker drift do dossier 30 segue sem solução
   publicada; LoRA-por-voz é a melhor mitigação disponível);
4. **Variações de sotaque = task vectors/LoRAs componíveis** (seção b), emoção =
   instrução NL + tags (seção a/d) — tudo componível por aritmética de pesos
   (HE-Vector) sem dado conjuntamente rotulado.

---

## Modelos: tabela-resumo de licenças e pt (verificado 2026-06-10)

| Modelo | Licença pesos | pt na saída | Por que importa aqui |
|---|---|---|---|
| **Qwen3-TTS** 0.6B/1.7B (12Hz) | **Apache-2.0** ([HF](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)) | **SIM** | dado sintético pt + candidato a voz do produto + finetune oficial; 97ms |
| GLM-TTS | **MIT** ([HF](https://huggingface.co/zai-org/GLM-TTS)) | não (zh/en) | receita GRPO multi-reward open de ponta a ponta |
| Step-Audio-EditX 3B | código Apache-2.0; **pesos sem licença explícita no HF** ([repo](https://github.com/stepfun-ai/Step-Audio-EditX)) | não (zh/en/ja/ko) | código SFT/DPO/GRPO p/ 3B/12GB; paradigma de edição de emoção |
| Maya1 3B | Apache-2.0 ([HF](https://huggingface.co/maya-research/maya1)) | não (en) | template de produto: 20+ tags + voice design NL; Llama-style+SNAC (≈Orpheus) |
| Chatterbox Multilingual / Turbo | MIT ([HF](https://huggingface.co/ResembleAI/chatterbox-turbo)) | Multilingual: **sim** / Turbo: não | pt zero-shot clone MIT; Turbo mostra tags paralinguísticas em 350M |
| CosyVoice3-0.5B | Apache-2.0 ([HF](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)) | não (9 línguas s/ pt) | melhor referência de instruct dialeto×emoção em escala |
| Orpheus 3B (+multilingual) | Apache-2.0 | **NÃO** (sem par pt) | guia de finetune de tags (50-300 ex.); corrigir qualquer suposição de pt |
| IndexTTS-2 | **ambígua/restrita** (comercial via e-mail bilibili) | — | **VETO mantido** apesar do melhor controle emoção+duração da classe |
| StepAudio 2.5 Realtime | **API-only** | não | estudar receita RLHF de persona; não usável no produto |
| Vevo (Amphion) | **CC-BY-NC-4.0** ([HF](https://huggingface.co/amphion/Vevo)) | — | VETO (NC) — não usar p/ conversão estilo/timbre no produto |

---

## Decisões recomendadas para o REPLAN (2026-06-10)

1. **Adotar Qwen3-TTS (Apache-2.0, pt) como gerador de dado sintético emocional pt-BR
   e candidato nº1 a componente de voz TTS** — rebaixa Kokoro/Chatterbox a fallback.
   Validar qualidade pt-BR de ouvido ANTES de comprometer (sotaque pode ser neutro/PT-PT).
2. **Dataset do Pedro: gravar com 3 camadas de rótulo** — (i) tags de evento
   (`<risada>`, `<suspiro>`, "uhum"), (ii) descrição NL de estilo por trecho,
   (iii) tag de variação carioca. Isso habilita as 3 interfaces de controle de uma vez.
3. **5 variações cariocas: começar com voice-prompt por variação (v0) + tag textual
   (v1); task vectors (v2) quando houver eval.** Construir classificador de variação
   como gate de qualidade do próprio dataset.
4. **Emoção: manter "implícita + NL prompt + RL leve"** — agora com caminho concreto:
   SFT LoRA → DPO leve → GRPO multi-reward (código de referência: Step-Audio-EditX,
   GLM-TTS; rewards: SER pt-BR + intensidade VAD + UTMOS; ler RRPO antes p/ reward hacking).
5. **Backchannels: dado estéreo 2 canais continua sendo o gargalo nº1** (confirma
   dossier 21); adotar receita F-Actor (encoder congelado, ~2kh, instrução de
   comportamento) como referência de controle explícito no spine.
6. **Multi-voz: catálogo de embeddings consentidos (modelo Kyutai/CC0) + LoRA por voz
   hero.** Não liberar cloning aberto no produto.

## Fontes primárias

arXiv: 2504.12867 (EmoVoice) · 2508.03543 (EmoSteer) · 2507.16632 (Step-Audio 2) ·
2605.23463 (StepAudio 2.5) · 2511.03601 (Step-Audio-EditX) · 2510.05758 (EMORL-TTS) ·
2512.14291 (GLM-TTS) · 2512.04552 (RRPO) · 2603.15981 (PALLM) · 2501.14273 (CSP-FT) ·
2603.07534 (Accent Vector) · 2512.18699 (HE-Vector) · 2508.07426 (Scalable Accented) ·
2601.14417 (spk-emb × regras fonológicas) · 2601.19786 (tokens discretos × sotaque) ·
2509.22727 (DiaMoE-TTS) · 2505.19687 (DiEmo-TTS) · 2510.11124 (EMM-TTS) ·
2505.07916 (MiniMax-Speech) · 2603.10904 (When FT Fails) · 2502.07562 (LoRP-TTS) ·
2601.11329 (F-Actor) · 2605.20755 (DuplexSLA) · 2604.21406 (HumDial ICASSP'26) ·
2512.14085 (backchannel multilíngue) · 2507.23159 (FDB v1.5).
HF/GitHub: QwenLM/Qwen3-TTS · Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ·
FunAudioLLM/Fun-CosyVoice3-0.5B-2512 · stepfun-ai/Step-Audio-EditX · zai-org/GLM-TTS ·
maya-research/maya1 · ResembleAI/chatterbox-turbo · canopyai/Orpheus-TTS ·
kyutai/tts-voices · amphion/Vevo (NC, veto).
