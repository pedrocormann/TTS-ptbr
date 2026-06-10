# FRENTE 1 — Ecossistema Sesame/CSM (estado em 2026-06-10)

> Dossiê de pesquisa web. Pergunta-mãe: o que mudou no ecossistema Sesame/CSM desde as crenças
> registradas em 2026-05-17, e qual é o caminho prático HOJE para finetunar o csm-1b com a voz
> do Pedro em pt-BR no Colab?

**TL;DR:** A Sesame virou empresa de produto consumer (app iOS lançado em 28/mai/2026, óculos em 2027)
e **não lançou nada open-source novo** — o csm-1b (Apache-2.0, mar/2025) continua sendo o único modelo
público e o repo oficial está dormente desde mai/2025. Em compensação, o ecossistema COMUNITÁRIO de
finetune amadureceu de vez: suporte nativo a treino no HF Transformers, notebook oficial do Unsloth
que roda em Colab T4 grátis, e três repos comunitários sólidos (knottwill/sesame-finetune,
davidbrowne17/csm-streaming, senstella/csm-mlx). Finetunes para línguas novas (árabe, suaíli, finlandês,
georgiano, bengali) provam que adaptação de língua funciona — e **não existe nenhum finetune público
pt-BR nem espanhol**: o campo está aberto para o TTS-ptbr ser o primeiro. A crença atual do projeto
(CSM-1B = componente de voz, não spine) **se mantém e sai reforçada**.

---

## (a) Sesame AI — novidades da empresa (até jun/2026)

### Linha do tempo verificada

| Data | Evento | Fonte |
|---|---|---|
| 2025-02-27 | Post de pesquisa "Conversational Speech Generation" (Crossing the Uncanny Valley of Voice) — único post de pesquisa até hoje | [sesame.com/research](https://www.sesame.com/research) |
| 2025-03-13 | Release open-source do CSM-1B (Apache-2.0) | [TechCrunch](https://techcrunch.com/2025/03/13/sesame-the-startup-behind-the-viral-virtual-assistant-maya-releases-its-base-ai-model/) |
| 2025-05-27 | Último commit no repo oficial (integração HF Transformers v4.52.1) | [github.com/SesameAILabs/csm/commits](https://github.com/SesameAILabs/csm/commits/main/) |
| 2025-10-21 | Series B de **US$ 250M** (Sequoia, Spark); beta fechado do app iOS; pivot declarado para **smart glasses** | [TechCrunch](https://techcrunch.com/2025/10/21/sesame-the-conversational-ai-startup-from-oculus-founders-raises-250m-and-launches-beta/) |
| **2026-05-28** | **Lançamento público do app iOS** em 39 países, grátis "por enquanto"; 4 agentes: Maya, Miles + novos **Simone e Charlie**; busca ao vivo, notas, modo incógnito, memória | [TechCrunch](https://techcrunch.com/2026/05/28/sesame-the-conversational-ai-startup-from-oculus-founders-launches-its-ios-app/) |
| 2027 (planejado) | Óculos inteligentes com o agente embarcado | [sesame.com](https://www.sesame.com/) |

### O que isso significa para o projeto

- **Não existe CSM-2, não existe API pública, não existe novo modelo aberto.** A org `sesame` no
  HuggingFace continua com **1 único modelo público** (csm-1b, ~268k downloads)
  ([huggingface.co/sesame](https://huggingface.co/sesame)). A página de research não ganhou nenhum
  post novo desde fev/2025. Os repos novos na org GitHub (torchtune, moshi, sglang, torchtitan,
  ClearerVoice-Studio, faster-whisper-plus...) são **forks de infraestrutura para uso interno**, não
  releases ([github.com/orgs/SesameAILabs/repositories](https://github.com/orgs/SesameAILabs/repositories)).
  Curiosidade relevante: a Sesame mantém fork do **moshi** da Kyutai — sinal de que o nosso spine
  escolhido é levado a sério até por eles.
- **Maya mudou de status**: deixou de ser demo viral e virou produto (iOS, 39 países, com memória,
  busca e 2 personagens novos). Android "no futuro", sem data. Nenhuma menção a API para
  desenvolvedores no lançamento ([winbuzzer](https://winbuzzer.com/2026/05/29/sesame-launches-iphone-voice-ai-app-with-four-agents-xcxwbn/)).
- O post de pesquisa original prometia "expandir suporte de língua para 20+ línguas" e open-sourcear
  "componentes-chave" — **promessas de fev/2025 não cumpridas no lado aberto até jun/2026**. Tratar a
  Sesame como fornecedora encerrada: o que existe aberto é o csm-1b e ponto.

**Conclusão (a):** a Sesame seguiu o caminho "OpenAI do voice" — demo aberta uma vez, depois produto
fechado. Nenhuma mudança que altere as apostas do projeto; reforça que não dá para esperar nada novo
deles no lado aberto.

---

## (b) Repo oficial SesameAILabs/csm — estado

- **Dormente.** Último commit: **2025-05-27** ("HF Transformers release includes CSM natively, #153").
  Antes disso, só commits de mar/2025. ~24 commits no total, 14.7k stars, **zero releases formais**
  ([commits](https://github.com/SesameAILabs/csm/commits/main/), [releases](https://github.com/SesameAILabs/csm/releases)).
- **Sem código de finetune oficial** — o README continua dizendo que é um "base generation model...
  not fine-tuned on any specific voice", e sobre línguas: *"some capacity for non-English languages
  due to data contamination in the training data, but it likely won't do well"*
  ([README](https://github.com/SesameAILabs/csm/blob/main/README.md)).
- **Issues**: 9 abertas; as relevantes para nós são antigas e sem resposta da Sesame:
  - #116 "Adding Hindi Support to CSM" (mar/2025) — sem orientação oficial.
  - #164 (jun/2025) e #169 (jul/2025) — condicionamento de emoção (54 emotion scores; Emilia anotado
    com EmoNet pronto para treino) — ideias úteis para a nossa fase de emoção, mas sem follow-up.
  - #179 (mai/2026, erro de triton no Windows) — única atividade de 2026, e é um usuário, não a Sesame.
  ([issues](https://github.com/SesameAILabs/csm/issues))
- **Licença**: Apache-2.0 confirmada no repo e no model card. **Nuance nova**: o model card
  `sesame/csm-1b` no HF agora é **gated leve** (pede concordar em compartilhar contato antes de
  baixar) — não muda a licença, mas muda a operação: para pipelines automatizados existem espelhos
  ungated como [unsloth/csm-1b](https://huggingface.co/unsloth/csm-1b) (Apache-2.0) e
  [eustlb/csm-1b](https://huggingface.co/eustlb/csm-1b).
- **Nuance de licença a vigiar (não-bloqueante)**: o fluxo do repo original exige acesso a
  `meta-llama/Llama-3.2-1B` para o **tokenizer de texto** (Llama 3.2 Community License, não Apache).
  Os pesos do csm-1b em si são Apache-2.0 (backbone re-treinado pela Sesame) e a versão HF Transformers
  embute processor/tokenizer no próprio repo Apache do modelo; o codec Mimi vem da Kyutai (CC-BY-4.0,
  já aceito pelo projeto). Veredicto prático: **dentro da restrição de licença do projeto**, com a
  ressalva do tokenizer documentada.

**Conclusão (b):** o repo oficial é peça de museu. O "upstream" real do CSM hoje é a integração no
**HF Transformers** (mantida por Eustache Le Bihan/HF), que inclusive **suporta treino nativamente** —
ver (c).

---

## (c) Ecossistema comunitário de finetune do csm-1b

### c.1 — HF Transformers: treino nativo (o alicerce)

Desde a v4.52.1 (mai/2025) o CSM é classe nativa (`CsmForConditionalGeneration` + `CsmProcessor`), e a
[documentação oficial](https://huggingface.co/docs/transformers/en/model_doc/csm) traz **exemplo de
treino**: `processor.apply_chat_template(conversation, output_labels=True)` devolve labels prontos,
`out.loss.backward()` funciona — compatível com o `Trainer` e, portanto, com **PEFT/LoRA padrão**.
Detalhes técnicos úteis que a doc expõe:

- Formato de dados = conversa multi-turno com `role` = speaker id e content misto texto+áudio **24 kHz**.
- `depth_decoder_labels_ratio` — hiperparâmetro exposto que implementa o *compute amortization* do
  paper da Sesame (treinar o depth decoder só numa fração dos frames).
- Geração com `output_audio=True`, suporte a CUDA graphs / geração estática para latência.

### c.2 — Unsloth: o caminho Colab (oficial, T4 grátis)

- **Existe notebook oficial**: [`Sesame_CSM_(1B)-TTS.ipynb`](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Sesame_CSM_(1B)-TTS.ipynb)
  (repo unslothai/notebooks), anunciado em mai/2025
  ([anúncio](https://x.com/UnslothAI/status/1924848135991656603), [blog](https://unsloth.ai/blog/tts),
  [guia TTS](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning)).
- **Cabe em T4**: o guia confirma treino em **Colab T4 grátis**; claims: ~1.5x mais rápido e ~50% menos
  VRAM que setup FA2 padrão; modelo de 1B em 16-bit LoRA fica folgado nos 15 GB da T4 (e mais ainda em L4).
- **Receita padrão**: LoRA 16-bit (`load_in_4bit=False`) como default; FFT como alternativa se a VRAM
  permitir; batch size 1 + gradient accumulation; exemplo de referência = dataset **Elise**
  (~3 h, ~1.200 amostras) com **tags de emoção no transcript** (`<sigh>`, `<laughs>`) — exatamente o
  padrão que queremos para emoções controláveis. Tempo reportado: **poucas épocas sobre 3 h de áudio
  = 1–2 h numa T4**.
- Mirror [unsloth/csm-1b](https://huggingface.co/unsloth/csm-1b) (Apache-2.0) evita o gate de contato.

### c.3 — knottwill/sesame-finetune + blog da Speechmatics (a receita "língua nova")

- [github.com/knottwill/sesame-finetune](https://github.com/knottwill/sesame-finetune) (**MIT**, ~110
  stars, 69 commits): **full finetune** (pesos originais, não LoRA) — posição explícita do autor:
  full FT *"é o ótimo para domain shifts como línguas novas"*; LoRA para mudanças menores (voz/estilo).
  Features: pré-tokenização (Mimi + tokenizer Llama-3.2) para HDF5, batching com *bucketed sampling*
  (minimiza padding), mixed precision, sweeps com Optuna, W&B, multi-GPU para sweeps.
- Formato de dados: metadata (JSON/CSV/Parquet/HDF5) com `path` do wav, transcrição, start/end
  opcionais, speaker id opcional, sample rate.
- O [blog da Speechmatics](https://blog.speechmatics.com/sesame-finetune) que acompanha o repo é
  **tutorial, não estudo de caso**: explica compute amortization (depth decoder treina em 1/16 dos
  frames; codebook zero em todos) e o pipeline, mas **não publica horas usadas, GPU, nem métricas
  (WER/MOS)**. Calibrar expectativa: a receita é sólida, os números temos que produzir nós mesmos.

### c.4 — davidbrowne17/csm-streaming (LoRA + streaming + latência)

- [github.com/davidbrowne17/csm-streaming](https://github.com/davidbrowne17/csm-streaming)
  (**Apache-2.0**, 84 commits): geração **streaming** com playback em tempo real, demo de chat com voz
  (VAD Silero + vLLM), e **finetune LoRA** (`lora.py`: wavs numa pasta `audio_data`, batch/epochs/lr
  configuráveis no topo do arquivo).
- Requisitos: **GPU CUDA com >= 12 GB de VRAM** para o finetune LoRA.
- Latência: **RTF 0.28x em RTX 4090** (10 s de áudio em ~2.8 s), "40–60% melhor" que o baseline — bom
  para servir, mas note que é RTF de batch, não time-to-first-audio; para conversação o que importa é
  o streaming chunk-a-chunk que o repo implementa.

### c.5 — csm-mlx (Apple Silicon, prototipagem local)

- O repo correto é [**senstella/csm-mlx**](https://github.com/senstella/csm-mlx) (Apache-2.0, ~116
  commits) — *lucasnewman/csm-mlx retorna 404 hoje; o ecossistema MLX consolidou no senstella*.
- Faz inferência + streaming + quantização **e finetune via CLI**: `csm-mlx finetune full` e **LoRA**
  (rank, alpha, target modules configuráveis) — documentado em
  [FINETUNING_CLI.md](https://github.com/senstella/csm-mlx/blob/master/FINETUNING_CLI.md).
- Útil para o Pedro iterar localmente no Mac antes de queimar créditos de Colab. Exemplo divertido que
  valida o fluxo: [Belluxx/GLaDOS-TTS](https://github.com/Belluxx/GLaDOS-TTS) (finetune de voz GLaDOS
  com csm-mlx). Há também [ARahim3/mlx-tune](https://github.com/ARahim3/mlx-tune) (API estilo Unsloth
  no MLX, suporta CSM-1B).

### c.6 — Finetunes comunitários em outras línguas (prova de viabilidade)

Filtro `base_model:finetune:sesame/csm-1b` no HF
([lista](https://huggingface.co/models?other=base_model%3Afinetune%3Asesame%2Fcsm-1b)):

| Modelo | Língua | Notas |
|---|---|---|
| [Nadhari/swa-csm-1b](https://huggingface.co/Nadhari/swa-csm-1b) | **Suaíli** | Apache-2.0; autodeclara "melhor TTS open-source de suaíli"; 141 downloads; card sem métricas |
| MAdel121/ e samehelalfi/ Seasmed-...-Arabic | **Árabe** | Treinados em **Common Voice 17** (mai–jul/2025) |
| ArttuPakarinen/sesame-csm-FIN-parlament-full-finetune | **Finlandês** | **Full finetune** com dados de parlamento (jan/2026) |
| NMikka/CSM-1B-Georgian | **Georgiano** | mar/2026 |
| Mizbaul-Haque-Maruf/csm-bangla-finetuned (+ -40000) | **Bengali** | abr/2026, duas variantes (sufixo sugere ~40k amostras) |

- **NÃO existe finetune público pt-BR, pt-PT nem espanhol** do csm-1b (buscas diretas no HF por
  "csm portuguese" e "csm spanish" = **0 resultados** em 2026-06-10;
  [pt](https://huggingface.co/models?search=csm+portuguese), [es](https://huggingface.co/models?search=csm+spanish)).
  Nas discussions do model card há demanda explícita por es/pt sem entrega
  ([discussão #11](https://huggingface.co/sesame/csm-1b/discussions/11)).
- **Qualidade reportada**: este é o ponto fraco do ecossistema — os cards são opacos (sem MOS, sem WER,
  sem horas declaradas). O sinal positivo é indireto: 5+ línguas tipologicamente distantes do inglês
  (incl. bengali e georgiano, com escrita não-latina) produziram modelos publicáveis a partir de um
  modelo "English-only com contaminação". pt-BR, com fonologia muito mais próxima do mix de treino e
  Common Voice/CORAA abundantes, deve ser caso mais fácil.

---

## (d) Caminho prático HOJE: finetune do csm-1b com a voz do Pedro em pt-BR no Colab

### Estratégia em dois estágios (alinhada ao consenso da comunidade)

**Princípio (knottwill/Speechmatics + Unsloth):** *língua nova → full finetune; voz/estilo → LoRA.*
Como pt-BR é "língua semi-nova" para o CSM (só contaminação), o caminho de menor risco é:

**Estágio A — Adaptação de língua (full FT, base pt-BR genérica)**
1. Dados: 50–200 h de pt-BR multi-falante limpo e licenciado (Common Voice pt / CORAA-derivados
   compatíveis — mesmo padrão dos finetunes árabes que usaram CV17). Re-amostrar para **24 kHz** mono.
2. Código: `knottwill/sesame-finetune` (MIT) ou `Trainer` HF puro com
   `CsmForConditionalGeneration` + `output_labels=True`. Usar `depth_decoder_labels_ratio≈1/16`
   (compute amortization) e bucketed sampling.
3. Hardware: **não cabe confortavelmente em T4 para full FT** — usar **L4 (24 GB) ou A100-40GB do
   Colab Pro+** (1B params em bf16 + Adam ≈ 16 GB só de estados; em A100 é tranquilo, em L4 com
   gradient checkpointing + accumulation passa). Depois escalar no GH200.
4. Sanidade: a cada N steps, gerar frases-sonda pt-BR e medir WER com faster-whisper + similaridade
   de speaker — o ecossistema não publica métricas, as nossas serão o diferencial.

**Estágio B — Voz do Pedro + emoções (LoRA sobre a base do Estágio A)**
1. Dados: **3–10 h** da gravação dirigida do Pedro (o exemplo de referência do Unsloth, Elise, tem ~3 h
   /~1.200 clipes e treina em **1–2 h numa T4**). Transcrições normalizadas com **tags de emoção
   inline** (`<risada>`, `<suspiro>`, `<animado>`...) — o mecanismo Elise funciona e é o caminho para
   as 5 sub-variações cariocas: tratar cada sub-variação como speaker id e/ou tag de estilo.
2. Código: notebook **Unsloth Sesame_CSM_(1B)-TTS** (LoRA 16-bit, `load_in_4bit=False`, batch 1 +
   grad accum). Cabe na **T4 grátis**; em L4 sobra espaço para sequências/batches maiores.
3. Formato do dataset (HF): `Dataset` com colunas `text` (com speaker id `[0]` e tags) + `audio`
   (24 kHz); para contexto conversacional, usar o chat template do `CsmProcessor` com turnos
   alternados (o CSM aceita contexto de conversa — é a sua vantagem nativa sobre TTS comum).
4. Inferência/serving: `davidbrowne17/csm-streaming` (Apache-2.0) para streaming em tempo real
   (referência: RTF 0.28x em 4090); `senstella/csm-mlx` para iterar no Mac.

### Estimativas honestas (o que a evidência sustenta)

| Item | Estimativa | Base |
|---|---|---|
| VRAM LoRA voz (Unsloth) | cabe em T4 15 GB | [Guia Unsloth](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning), [requisitos](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements) |
| VRAM LoRA (repo csm-streaming) | >= 12 GB | [README](https://github.com/davidbrowne17/csm-streaming) |
| Tempo LoRA sobre ~3 h de áudio | 1–2 h em T4 | Guia Unsloth |
| Horas p/ clonar voz/estilo | 3–10 h | Elise ~3 h como referência funcional |
| Horas p/ língua nova | dezenas–centenas (CV17 nos casos árabes) | cards HF; sem número publicado — **gap que nós vamos medir** |
| Qualidade esperada | sem MOS/WER publicados por NINGUÉM no ecossistema | verificação direta dos cards |

### Riscos e mitigação

- **Risco 1 — pular o Estágio A**: LoRA direto sobre a base inglesa com 5 h de pt-BR pode dar sotaque
  gringo/prosódia errada (é o motivo do "full FT para línguas" do knottwill). Mitigar: testar A/B
  cedo com 30 min de treino em cada rota.
- **Risco 2 — métricas inexistentes no ecossistema**: ninguém publicou MOS; não dá para prever
  qualidade por benchmark alheio. Mitigar: eval harness próprio desde o primeiro checkpoint.
- **Risco 3 — gate de contato no `sesame/csm-1b`**: usar mirror `unsloth/csm-1b` em pipelines.
- **Risco 4 — tokenizer Llama-3.2**: documentar a proveniência; se o jurídico apertar, o tokenizer é
  trocável com re-treino do embedding de texto (custoso — só se necessário).

---

## Veredito vs. crenças de 2026-05-17

| Crença registrada | Status em 2026-06-10 |
|---|---|
| CSM-1B = componente de voz/clone, NÃO spine | **Mantida e reforçada** — sem texto, sem código oficial de treino, Sesame fechada |
| "Sem código de treino oficial" | **Parcialmente desatualizada**: continua sem código da Sesame, mas o treino é suportado nativamente no HF Transformers + notebook Unsloth oficial (T4) — o custo de entrada despencou |
| "Treinado em inglês" | Mantida, mas 5+ finetunes comunitários de língua provam a rota de adaptação |
| Spine = Moshi/Kyutai | Nada no ecossistema Sesame ameaça isso; a própria Sesame forka o moshi |
| Emoção via tags/estilo | Convergência: padrão Elise (`<laughs>`, `<sigh>`) já é o default do ecossistema CSM |

**Recomendação:** manter CSM-1B exatamente no papel atual (voz/clone), e **promover o par
"Unsloth Colab T4 (LoRA voz) + knottwill/HF Trainer (full FT língua)" a receita oficial da Fase
Colab do projeto**. Há uma janela aberta para publicar o primeiro csm-1b pt-BR do mundo — com
métricas, o que ninguém no ecossistema fez.

---

## Fontes primárias

- https://github.com/SesameAILabs/csm (+ /commits/main/, /issues, /releases)
- https://huggingface.co/sesame/csm-1b · https://huggingface.co/sesame
- https://huggingface.co/docs/transformers/en/model_doc/csm
- https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning · https://unsloth.ai/blog/tts
- https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Sesame_CSM_(1B)-TTS.ipynb
- https://huggingface.co/unsloth/csm-1b
- https://github.com/knottwill/sesame-finetune · https://blog.speechmatics.com/sesame-finetune
- https://github.com/davidbrowne17/csm-streaming
- https://github.com/senstella/csm-mlx (+ FINETUNING_CLI.md)
- https://huggingface.co/models?other=base_model%3Afinetune%3Asesame%2Fcsm-1b
- https://huggingface.co/Nadhari/swa-csm-1b
- https://techcrunch.com/2026/05/28/sesame-the-conversational-ai-startup-from-oculus-founders-launches-its-ios-app/
- https://techcrunch.com/2025/10/21/sesame-the-conversational-ai-startup-from-oculus-founders-raises-250m-and-launches-beta/
- https://www.sesame.com/research · https://www.sesame.com/
- https://www.voiceaispace.com/news/voice-ai-news-2026-05-25-cz0n
- https://github.com/orgs/SesameAILabs/repositories
