# FRENTE 6 — Realidade do Colab e receitas de finetune que cabem nele (jun/2026)

> Pesquisa web realizada em 2026-06-10. Tudo abaixo cita fonte primária (HF model cards, GitHub, blogs oficiais, posts oficiais do @GoogleColab). Crenças de 2026-05-17 marcadas como **[MUDOU]** ou **[CONFIRMADO]** quando relevante.

## TL;DR (o que muda para o TTS-ptbr)

1. **[MUDOU] O Colab de jun/2026 não é mais "T4/L4/A100-40"**: agora oferece **A100-80GB** (slider "High RAM"), **H100** e a nova **G4 = NVIDIA RTX PRO 6000 Blackwell com ~96 GB de VRAM** (anúncio oficial do Colab: ~960 BF16 TFLOPs, ~50% mais rápida que A100-80G). Isso significa que **o LoRA do moshi-finetune (pico ~39,6 GB) cabe no Colab Pro+** — o plano "Colab primeiro, GH200 depois" fica mais forte, sem precisar de RunPod para o spine.
2. **Unsloth tem notebooks Colab oficiais e gratuitos (T4) para CSM-1B, Orpheus-3B, Whisper-v3, Llasa, Spark e Oute** — mas **Llasa (CC-BY-NC-ND) e Spark (CC-BY-NC-SA) estão vetados pela nossa regra de licença**. Os utilizáveis no produto são: **CSM-1B (Apache-2.0)** e **Orpheus (Apache-2.0)**.
3. **Orpheus multilingual NÃO tem português** (6 grupos: fr, de, es_it, zh, ko, hi). Adaptar Orpheus para pt-BR = trabalho de pretrain de língua nova, não finetune leve.
4. **Precedente pt-BR concreto**: Dia-1.6B finetunado para pt-BR com **144 h (CETUC)** em **uma RTX 4090, ~20 h de treino** — funcionou, mas **perdeu emoções e inglês** (lição: dataset mono-estilo mata expressividade; preservar tags de emoção no dataset do Pedro é obrigatório).
5. **Chatterbox Turbo (dez/2025, MIT, 350M, ~75 ms)** é novo e ótimo para agente em tempo real, **mas é inglês-only**; para pt continua valendo **Chatterbox Multilingual (500M, MIT, pt incluído)** — segue sendo nossa fonte license-clean de dado sintético e há **toolkits comunitários de finetune com LoRA** para ele.
6. Dados da própria voz: **5–10 s** para clone zero-shot; **15–60 min** (sweet spot) a **~3 h com tags de emoção** para voz dedicada finetunada (receita Elise/Orpheus: ~50 exemplos já mostra efeito, **300+ exemplos/falante** recomendado); **dezenas a ~150 h** para fixar língua/sotaque novo no modelo (referência CETUC/Dia e Kokoro-alemão <100 h).
7. Pipeline de dataset: **WhisperX (faster-whisper + alinhamento forçado wav2vec2 + diarização, ~70× tempo real)** continua o padrão para segmentar gravações longas; **Emilia-Pipe (Amphion)** é o pipeline completo "in-the-wild → dataset pronto" (6 etapas, ~1 h de áudio bruto processada em minutos).

---

## (a) Google Colab em jun/2026 — GPUs, preços, limites — e alternativas

### GPUs e taxas de consumo (medição de mar/2026, Chris McCormick)

| GPU | VRAM | Compute Units/h | Custo efetivo (~$0,10/CU) | Disponível |
|---|---|---|---|---|
| T4 | 15 GB | **1,19** | ~$0,12/h | **Grátis** (preemptível) e pago |
| L4 | 22,5 GB | **1,71** | ~$0,17/h | Pago |
| A100 40GB | 40 GB | **5,40** | ~$0,54/h | Pago |
| A100 80GB (slider High-RAM) | 80 GB | **7,52** | ~$0,75/h | Pago |
| **G4 (RTX PRO 6000 Blackwell)** | **~96 GB** | **8,71** | ~$0,87/h | Pago — **novo** |
| H100 | 80 GB | (taxa ainda não medida) | — | Pago — **novo na lista** |

Fontes: [mccormickml.com — Colab GPUs Features & Pricing, atualizado mar/2026](http://mccormickml.com/2024/04/23/colab-gpus-features-and-pricing/); anúncio oficial da G4: [@GoogleColab no X](https://x.com/GoogleColab/status/2029331896409464974) ("peak rating of 960 BF16 TFLOPs (~50% more than the A100-80G) and 96 GB of VRAM"); [Benjamin Marie](https://x.com/bnjmn_marie/status/2028387339173494946) confirma G4 = RTX Pro 6000.

### Planos (preços inalterados desde 2024)

| Plano | Preço | CU/mês | Sessão máx. | Background exec | Idle timeout |
|---|---|---|---|---|---|
| Free | $0 | — | ~12 h, preemptível | não | ~30 min |
| Pro | $9,99/mês | **100 CU** | até 24 h | não¹ | ~90 min |
| Pro+ | $49,99/mês | **500 CU** | até 24 h | **sim** | ~90 min |
| Pay-as-you-go | $9,99/100 CU | avulso | — | — | — |

¹ Background execution é o diferencial do Pro+ ("background execution for our longest-running sessions" — [Google Workspace Updates](https://workspaceupdates.googleblog.com/2024/06/google-workspace-colab-pro-and-colab-pro-plus.html); limites de sessão: [cloud.google.com/colab/pricing](https://cloud.google.com/colab/pricing), [colab signup](https://colab.research.google.com/signup)).

### Matemática prática para o projeto (Pro+ = 500 CU/mês)

- **A100-40GB**: ~92 h/mês (5,40 CU/h) → suficiente para vários ciclos LoRA de TTS.
- **A100-80GB**: ~66 h/mês — roda moshi-finetune LoRA com folga de VRAM.
- **G4 96GB**: ~57 h/mês — melhor opção para sequências longas de full-duplex (mais VRAM + BF16 ~50% mais rápido que A100-80).
- **L4**: ~292 h/mês — workhorse para dataset prep com GPU (WhisperX, tokenização Mimi) e finetunes pequenos (Chatterbox 500M, CSM-1B).
- **T4 grátis**: roda os notebooks Unsloth de CSM-1B/Orpheus-3B LoRA 16-bit (lentamente; sem bf16 nativo).

Observação de custo: a ~$0,54–0,75/h efetivos de A100, **o Colab Pro+ ficou competitivo até contra RunPod on-demand** — a razão de sair do Colab passa a ser confiabilidade/duração de sessão (>24 h) e multi-GPU, não preço. Taxas de CU flutuam; tratar a tabela como ordem de grandeza.

### Alternativas (jun/2026)

| Plataforma | O que dá | Preço/limite | Fonte |
|---|---|---|---|
| **Kaggle** | T4×2 ou P100, TPU | **Grátis: 30 h/semana de GPU, 9 h/sessão**; T4×2 conta como 1 h de quota por hora real (2 GPUs pelo preço de 1); execução em background suportada | [Kaggle docs — Efficient GPU Usage](https://www.kaggle.com/docs/efficient-gpu-usage), [anúncio T4×2](https://www.kaggle.com/product-feedback/361104) |
| **Lightning AI Studios** | T4/L4/L40S/A100/H100/H200 | Free tier com créditos mensais e até 2 GPUs concorrentes; spot/interruptible com ~80% off; Pro com $240/ano em créditos | [lightning.ai/pricing](https://lightning.ai/pricing/) |
| **Modal** | Serverless por segundo | A100-40 ≈ $0,000583/s (~$2,10/h), A100-80 ≈ $0,000694/s (~$2,50/h), H100 ≈ $0,001097/s (~$3,95/h); **$30/mês de crédito grátis** no Starter | [modal.com/pricing](https://modal.com/pricing) |
| **RunPod** | Pods VM-style + serverless | A100 ~$1,19–1,39/h; H100 SXM ~$2,39–2,69/h on-demand; spot H100 ~$1,30–1,60/h | [runpod.io/pricing](https://www.runpod.io/pricing), [comparativo Northflank](https://northflank.com/blog/runpod-gpu-pricing) |
| **Thunder Compute** | A100-80GB on-demand | **$0,78/h**, cobrança por minuto | [Thunder — Colab alternatives, jun/2026](https://www.thundercompute.com/blog/colab-alternatives-for-cheap-deep-learning-in-2025) |
| **Paperspace** | Notebooks gerenciados | A100-80 ~$3,18/h | idem |

**Recomendação de stack de compute (fase Colab):** Pro+ ($49,99) como base (A100-80/G4 para moshi-finetune; L4 para pipeline), Kaggle T4×2 grátis como "segunda conta" para ablações/eval em paralelo, e RunPod/Thunder como válvula de escape para runs >24 h. SDumont GH200 (96 GB) continua o destino para CPT se o LoRA não bastar.

---

## (b) Unsloth — suporte real a áudio/TTS em jun/2026

Fontes: [docs oficiais — TTS Fine-tuning Guide](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning), [blog unsloth.ai/blog/tts](https://unsloth.ai/blog/tts), [issue #2546 (anúncio)](https://github.com/unslothai/unsloth/issues/2546), [coleção HF](https://huggingface.co/collections/unsloth/text-to-speech-tts-models).

**Modelos com notebook oficial Colab (grátis, T4):**

| Modelo | Tamanho | Licença | Veredito p/ produto |
|---|---|---|---|
| **Sesame CSM-1B** | 1B | Apache-2.0 | ✅ usável |
| **Orpheus-TTS** | 3B (Llama-based) | Apache-2.0 | ✅ usável |
| **Whisper Large V3 (STT)** | 1,5B | Apache-2.0 | ✅ usável (ASR do pipeline) |
| Llasa-TTS | 1B | **CC-BY-NC-ND** | ❌ vetado (NC) |
| Spark-TTS | 0.5B | **CC-BY-NC-SA** | ❌ vetado (NC) |
| Oute-TTS | 1B | CC-BY-NC (HF) | ❌ vetado (NC) |

- Unsloth declara: "Unsloth supports any `transformers` compatible TTS model" — ou seja, **Moshi NÃO entra** (arquitetura própria RQ-Transformer, fora do `transformers`); o spine continua com o `moshi-finetune` oficial da Kyutai.
- Claims de performance: "~1.5x faster with 50% less VRAM compared to all other setups with FA2"; recomendação oficial: **LoRA 16-bit ou FFT** para TTS, com `load_in_4bit = False` (4-bit degrada aprendizado de áudio).
- Dataset: pares áudio+transcrição, 24 kHz (Orpheus), transcrição normalizada; **tags de emoção em colchetes angulares** (`<laugh>`, `<sigh>`) viram tokens distintos — o dataset "Elise" (~3 h, single-speaker, com tags) é o exemplo canônico.
- **Bugs/pegadinhas conhecidas** (docs + anúncio): (1) CSM-1B base tem **variação de voz entre gerações com speaker ID 0** se não der contexto de áudio; (2) saída padrão capada em ~10 s (`max_new_tokens = 125` — aumentar para áudio mais longo); (3) o time corrigiu "issues with Sesame CSM training and output quality/lengths" no release inicial — usar Unsloth atualizado.
- LoRA para TTS: comunidade usa **rank maior que em texto (r=64+)**; Unsloth/moshi-finetune recomendam até r=128.

---

## (c) Receitas públicas de finetune de TTS que FUNCIONARAM

### Orpheus (Apache-2.0) — finetune de voz e de língua
- **README oficial**: "high quality results after ~50 examples but for best results, aim for **300 examples/speaker**"; treino via HF Trainer; LoRA opcional; latência de streaming "~200ms, reducible to ~100ms with input streaming" ([github.com/canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS)).
- **Demonstração reprodutível**: ~1.200 pares áudio-texto, LoRA 16-bit via Unsloth, **~19 min de treino em 1 GPU**, 1 epoch/299 steps ([yuv008/Orpheus-tts](https://github.com/yuv008/Orpheus-tts)); dataset Elise (~3 h c/ tags de emoção) é o benchmark de voz expressiva.
- **Língua nova**: Canopy publicou guia + checkpoints multilingues — **6 grupos (fr, de, es_it, zh, ko, hi), 13 modelos, SEM português** ([coleção HF](https://huggingface.co/collections/canopylabs/orpheus-multilingual-research-release)); aviso oficial: "decent results with short finetunes on a few thousand samples", mas nível do inglês exige muito mais dado; multilingues são "research-preview, not production" ([discussion New Language](https://huggingface.co/canopylabs/orpheus-3b-0.1-pretrained/discussions/1)). Para língua nova recomendam "**finetuning only (no text dataset)**" antes de pensar em pretrain misto.
- Precedente de língua nova fora do roster: **Hypa_Orpheus-3b** para línguas africanas com clonagem e síntese emocional ([model card](https://huggingface.co/okezieowen/hypaai_orpheus)) — prova que a receita generaliza.

### CSM-1B (Apache-2.0) — voz e língua
- **Guia Speechmatics** (melhor receita pública para língua nova): optaram por **full finetune, não LoRA** ("we have elected to fine-tune by modifying the original weights rather than using techniques like LoRA" — ótimo para domain shift de língua); hiperparâmetros sensíveis (lr 3e-5, weight decay 0.002, decoder loss weight 0.5, batch 8; recomendam sweep com Optuna); "compute amortization" treina o decoder em 1/16 dos frames ([blog.speechmatics.com/sesame-finetune](https://blog.speechmatics.com/sesame-finetune)).
- **csm-streaming (davidbrowne17)**: finetune LoRA jogando wavs crus em `audio_data/` + streaming em tempo real ([github.com/davidbrowne17/csm-streaming](https://github.com/davidbrowne17/csm-streaming)).
- Unsloth tem notebook Colab de CSM-1B que roda em T4 grátis (LoRA 16-bit).

### Dia-1.6B → pt-BR (o precedente mais direto para nós)
- **[Alissonerdx/Dia1.6-pt_BR-v1](https://huggingface.co/Alissonerdx/Dia1.6-pt_BR-v1)**: base Dia-1.6B (nari-labs, Apache-2.0), **144 h de pt-BR (CETUC, 100 falantes)**, **1× RTX 4090, ~20 h, 140k steps (~1,4 epochs)**. Funciona para pt-BR limpo, **mas "lost the original English and expressive capabilities (e.g., laughter, emotions)"** e ficou mono-speaker.
- **Lição decisiva**: corpus de leitura limpa (CETUC) ensina a língua mas **apaga a expressividade** — o dataset do Pedro precisa de fala conversacional com tags de emoção/risada desde o dia 1, e o finetune deve misturar dado expressivo para não sofrer catastrophic forgetting do estilo.

### Chatterbox (MIT) — finetune comunitário maduro
- **[gokhaneraslan/chatterbox-finetuning](https://github.com/gokhaneraslan/chatterbox-finetuning)**: toolkit para Chatterbox TTS & **Chatterbox TURBO**, 23 línguas com "smart vocabulary extension", VAD trimming automático, formato LJSpeech, **suporte LoRA** ("train high-quality voices faster and with significantly less VRAM").
- **[chatterbox-indic-lora](https://github.com/reenigne314/chatterbox-indic-lora)**: adicionou **8 línguas indianas via LoRA** ao Chatterbox-Multilingual — prova de que LoRA basta para variante de língua quando o modelo já tem a língua-mãe próxima.
- pt-BR já feito: [FearL0rd/Chatterbox-TTS-Portuguese](https://huggingface.co/FearL0rd/Chatterbox-TTS-Portuguese).

### Kokoro (Apache-2.0) — sem código oficial de treino
- Treino oficial nunca foi liberado ([issue #205](https://github.com/hexgrad/kokoro/issues/205)); receita comunitária completa para **língua nova (alemão)**: [semidark/kikiri-tts](https://github.com/semidark/kikiri-tts) (dataset prep → Stage 1 → Stage 2 → voicepack, StyleTTS2 patchado). Referência de escala: Kokoro original = **~500 GPU-h em A100-80 (~$400) com <100 h de áudio**. Mantê-lo como gerador de dado sintético, não como alvo de finetune.

### Moshi (spine) — encaixe no Colab
- **[kyutai-labs/moshi-finetune](https://github.com/kyutai-labs/moshi-finetune)**: LoRA rank≤128 recomendado; **1×H100 ≈ 12k tokens/s com pico de 39,6 GB**; roda em GPU única ("use `torchrun` even if you're only using a single GPU"); gradient checkpointing para OOM; **notebook Colab oficial existe** ([tutorials/moshi_finetune.ipynb](https://colab.research.google.com/github/kyutai-labs/moshi-finetune/blob/main/tutorials/moshi_finetune.ipynb)). Dataset: wav estéreo (canal E = modelo, canal D = usuário) + manifest `.jsonl` + transcrições com timestamps.
- **Implicação**: pico de ~40 GB ⇒ **A100-80GB ou G4-96GB do Colab Pro+ rodam o LoRA do spine**; em A100-40GB só com `duration_sec`/batch/rank reduzidos.

---

## (d) Quantas horas da própria voz são necessárias?

| Objetivo | Dado necessário | Evidências |
|---|---|---|
| **(i) Clone zero-shot bom** | **5–10 s** de referência limpa (até 1 min) | Chatterbox Turbo clona com ~5–10 s ([the-decoder](https://the-decoder.com/resemble-ai-drops-chatterbox-turbo-an-open-source-text-to-speech-model-that-clones-voices-in-five-seconds/), [HF card](https://huggingface.co/ResembleAI/chatterbox-turbo)); F5-TTS ~10 s; GPT-SoVITS ~1 min; CSM-1B usa clipes in-context |
| **(ii) Voz dedicada finetunada com emoções** | **15–60 min é o sweet spot; ~1–3 h com tags de emoção para expressividade rica** | Orpheus: efeito com ~50 exemplos, **300+ exemplos/falante** recomendado (~30–60 min) ([README](https://github.com/canopyai/Orpheus-TTS)); Elise = ~3 h com `<laugh>/<sigh>` e é o padrão-ouro dos notebooks Unsloth; guia F5: "15 to 60 minutes of clean, single-speaker audio is the sweet spot" ([instavar](https://instavar.com/blog/ai-production-stack/F5_TTS_Fine_Tuning_Voice_Cloning_Guide)); literatura de adaptação de emoção usa ~1 h/emoção em partial finetuning ([arXiv 2501.14273](https://arxiv.org/pdf/2501.14273)) |
| **(iii) Língua/sotaque consistente** | **Dezenas de horas se o modelo já fala pt; ~100–150 h para ensinar a língua do zero** | Dia pt-BR: 144 h (CETUC) bastaram para a língua inteira ([model card](https://huggingface.co/Alissonerdx/Dia1.6-pt_BR-v1)); Kokoro-alemão: <100 h; Orpheus língua nova: "few thousand samples" para resultado decente, muito mais para nível-inglês ([discussion](https://huggingface.co/canopylabs/orpheus-3b-0.1-pretrained/discussions/1)); LoRA de variante (indic sobre multilingual) precisa menos ([chatterbox-indic-lora](https://github.com/reenigne314/chatterbox-indic-lora)) |

**Tradução para o plano de gravação do Pedro:**
- **Fase 0 (já útil)**: 10 min de referência limpa → clone zero-shot em Chatterbox Multilingual/CSM para protótipos.
- **Fase 1 (voz dedicada)**: **3–5 h dirigidas** com tags de emoção (`<laugh>`, `<sigh>`, raiva, sussurro, animação...) e fala conversacional (disfluências controladas) — cobre o finetune de voz em qualquer modelo da lista.
- **Fase 2 (sotaques)**: ~**300 exemplos (≈30–45 min) por sub-variação carioca** seguindo a regra do Orpheus de exemplos/falante — 5 variações ≈ +3 h.
- **Fase 3 (spine full-duplex)**: o gargalo não é a voz e sim **diálogo estéreo** (canal usuário + canal Pedro) para o moshi-finetune; aqui dezenas de horas de conversa (mesmo semi-sintética: TTS license-clean no canal do "usuário") valem mais que horas extras de leitura.

---

## (e) Ferramentas de pipeline de dataset (jun/2026)

- **WhisperX** ([m-bain/whisperX](https://github.com/m-bain/whisperX)) — padrão de fato: faster-whisper batched (**até ~70× tempo real**) + **alinhamento forçado wav2vec2 com timestamps por palavra** + diarização pyannote, num só CLI/API ([guia 2026](https://localaimaster.com/blog/whisperx-guide)). Para pt-BR o alinhador usa wav2vec2 pt (ex.: `jonatasgrosman/wav2vec2-large-xlsr-53-portuguese`). Boas práticas para gravações longas: VAD primeiro, cortar em chunks de 10–15 min com overlap, segmentos finais de ~30 s.
- **Emilia-Pipe** ([Amphion/preprocessors/Emilia](https://github.com/open-mmlab/Amphion/tree/main/preprocessors/Emilia)) — pipeline completo "in-the-wild → dataset de speech generation": **Standardization → Source Separation → Speaker Diarization → VAD fine-grained → ASR → Filtering**; processa 1 h de áudio bruto em poucos minutos; é o pipeline que gerou o Emilia/Emilia-Large (**>200k h**, incl. pt) ([arXiv 2407.05361](https://arxiv.org/html/2407.05361v3)). Útil tanto para o dado do Pedro quanto para minerar pt-BR permissivo em escala.
- **Toolkits de prep acoplados a finetune**: o [chatterbox-finetuning](https://github.com/gokhaneraslan/chatterbox-finetuning) traz preprocessing offline + VAD trimming + formato LJSpeech; os notebooks Unsloth aceitam datasets HF simples (áudio + texto + tags).
- **Para o spine**: o moshi-finetune exige **estéreo 2 canais + `.jsonl` + transcrições com timestamps** — WhisperX gera exatamente os timestamps por palavra necessários para montar o JSON por arquivo.

---

## Implicações diretas / o que mudou vs 2026-05-17

| Crença (mai/2026) | Status (jun/2026) |
|---|---|
| Colab Pro/Pro+ = T4/L4/A100-40 | **[MUDOU]** + A100-80, H100 e G4 (RTX PRO 6000, 96 GB) — VRAM deixou de ser o bloqueio para o LoRA do Moshi no Colab |
| moshi-finetune precisa de H100/GH200 | **[REFINADO]** pico 39,6 GB (LoRA r128) ⇒ cabe em A100-80/G4 do Pro+; notebook Colab oficial existe |
| CSM-1B sem código de treino oficial | **[CONFIRMADO]**, mas ecossistema maduro: Unsloth (notebook T4 grátis), Speechmatics (full-FT p/ língua nova), csm-streaming (LoRA + streaming) |
| Chatterbox (MIT) p/ dado sintético | **[CONFIRMADO+]** e ganhou o **Turbo (dez/2025, MIT, 350M, ~75 ms, tags paralinguísticas nativas)** — porém Turbo é EN-only; pt fica no Multilingual 500M |
| Kokoro p/ dado sintético | **[CONFIRMADO]** (sem treino oficial; receita comunitária kikiri-tts existe) |
| Llasa/Spark como opções de TTS | **[VETADOS]** Llasa = CC-BY-NC-ND; Spark = CC-BY-NC-SA — não entram no produto mesmo com notebooks Unsloth |
| Orpheus como alternativa de TTS pt | **[ALERTA]** multilingual oficial NÃO tem pt; pt-BR via Orpheus = projeto de pretrain (~100k h EN na base; "few thousand samples" só dá resultado "decente") |

### Fontes principais
- Colab: [mccormickml (mar/2026)](http://mccormickml.com/2024/04/23/colab-gpus-features-and-pricing/) · [@GoogleColab G4](https://x.com/GoogleColab/status/2029331896409464974) · [cloud.google.com/colab/pricing](https://cloud.google.com/colab/pricing) · [Workspace Updates (CU por plano)](https://workspaceupdates.googleblog.com/2024/06/google-workspace-colab-pro-and-colab-pro-plus.html)
- Alternativas: [Kaggle docs](https://www.kaggle.com/docs/efficient-gpu-usage) · [lightning.ai/pricing](https://lightning.ai/pricing/) · [modal.com/pricing](https://modal.com/pricing) · [runpod.io/pricing](https://www.runpod.io/pricing) · [Thunder Compute (jun/2026)](https://www.thundercompute.com/blog/colab-alternatives-for-cheap-deep-learning-in-2025)
- Unsloth: [TTS guide](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning) · [blog TTS](https://unsloth.ai/blog/tts) · [issue #2546](https://github.com/unslothai/unsloth/issues/2546)
- Receitas: [Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS) · [coleção multilingual](https://huggingface.co/collections/canopylabs/orpheus-multilingual-research-release) · [Speechmatics CSM](https://blog.speechmatics.com/sesame-finetune) · [Dia pt-BR](https://huggingface.co/Alissonerdx/Dia1.6-pt_BR-v1) · [chatterbox-finetuning](https://github.com/gokhaneraslan/chatterbox-finetuning) · [moshi-finetune](https://github.com/kyutai-labs/moshi-finetune)
- Licenças NC: [Llasa-1B-Multilingual](https://huggingface.co/HKUSTAudio/Llasa-1B-Multilingual) · [Spark-TTS-0.5B README](https://huggingface.co/unsloth/Spark-TTS-0.5B/raw/main/README.md)
- Chatterbox Turbo: [resemble.ai/chatterbox-turbo](https://www.resemble.ai/chatterbox-turbo/) · [HF card](https://huggingface.co/ResembleAI/chatterbox-turbo)
- Pipeline: [WhisperX](https://github.com/m-bain/whisperX) · [Emilia-Pipe](https://github.com/open-mmlab/Amphion/tree/main/preprocessors/Emilia) · [Emilia paper](https://arxiv.org/html/2407.05361v3)
