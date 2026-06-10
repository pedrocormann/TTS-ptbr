# 12 — Pool de modelos abertos de fala (varredura exaustiva 2025–2026)

**Data:** 2026-06-10 · **Frente 3** do dossiê de re-pesquisa · Baseline de crenças: 2026-05-17
**Método:** verificação web primária (HuggingFace model cards, GitHub READMEs/releases, blogs oficiais, arXiv) para licença, pt-BR na saída, emoção, clonagem, latência, VRAM, código de treino e atividade. Nada abaixo é de memória de treino do agente sem fonte.

---

## TL;DR — o que mudou desde 2026-05-17

1. **Qwen3-TTS (22/jan/2026)** é o release que mais muda o jogo: Apache-2.0 (pesos E código), 0.6B/1.7B, **português entre as 10 línguas nativas**, TTFA ~97ms, clone com 3s, voice design por texto, **código de finetune oficial** e vLLM day-0. Vira candidato #1 para o TTS expressivo pt-BR no Colab. ([GitHub](https://github.com/QwenLM/Qwen3-TTS), [MarkTechPost](https://www.marktechpost.com/2026/01/22/qwen-researchers-release-qwen3-tts-an-open-multilingual-tts-suite-with-real-time-latency-and-fine-grained-voice-control/))
2. **Chatterbox virou família V3 (MIT)** com **pack dedicado pt-BR** (`ResembleAI/Chatterbox-Multilingual-pt-br`, 0.5B) e **Chatterbox-Turbo** (350M, tags paralinguísticas `[laugh]`, alvo sub-200ms). ([HF pt-br](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br), [GitHub](https://github.com/resemble-ai/chatterbox))
3. Dois "monstros Apache com pt" novos de 2026: **VoxCPM2** (OpenBMB, abr/2026, 2B, 30 línguas, LoRA oficial com webUI, 8GB) e **família MOSS-TTS** (OpenMOSS/MOSI.AI, fev–mai/2026, Apache, 31 línguas com pt, do Nano-100M-CPU ao 8B, **MOSS-TTS-Realtime 1.7B com 180ms TTFB** e docs oficiais de finetune). ([VoxCPM](https://github.com/OpenBMB/VoxCPM), [MOSS-TTS](https://github.com/OpenMOSS/MOSS-TTS))
4. **Vetos novos importantes**: Voxtral TTS da Mistral (mar/2026) é **CC-BY-NC** apesar do hype; Higgs Audio v3 (jun/2026) é **NC**; Higgs v2 tem community license com teto de 100k usuários; **Spark-TTS foi re-licenciado de Apache para CC-BY-NC-SA**; Fish S2-Pro (topo da arena) é research license.
5. **Aposta do spine (Moshi/Kyutai) sai reforçada**: Kyutai segue ativíssima — Pocket-TTS (jan/2026, 100M, CPU, ~200ms) ganhou **português** em mai/2026, e **MoshiRAG** (abr/2026) mostra o stack Moshi evoluindo. Nenhum full-duplex aberto novo destronou Moshi.
6. A **cascata ficou mais rápida que o previsto**: com Qwen3-TTS (97ms TTFA) ou MOSS-TTS-Realtime (180ms TTFB) como perna de TTS, o "piso de latência" da cascata cai para a faixa do alvo (p50 < 800ms com folga; ~300–500ms plausível). Cascata deixa de ser só piso e vira plano B sério.

---

## Tabela mestre A — Candidatos license-clean (Apache/MIT/CC-BY) COM português na saída

| Modelo | Licença (pesos/código) | pt-BR na saída | Emoção | Clonagem | Latência/streaming | VRAM (inf / finetune) | Código de treino | Atividade |
|---|---|---|---|---|---|---|---|---|
| **Qwen3-TTS-12Hz 0.6B/1.7B** (Alibaba, jan/2026) | Apache-2.0 / Apache-2.0 | **pt nativo** (1 das 10 línguas; variante BR a validar de ouvido) | controle por instrução/semântica do texto (tom, ritmo, emoção); VoiceDesign por descrição | sim, 3s áudio+transcrição, prompt reutilizável | **TTFA ~97ms**, streaming nativo, vLLM day-0 | ~4–8GB inf (1.7B bf16) / LoRA cabe em T4-16GB | **oficial (Qwen3-TTS-Finetuning)** + LoRA comunitário (bugs conhecidos no `sft_12hz.py` oficial — ver ficha) | muito alta (release jan/2026, vLLM, ModelScope) |
| **Chatterbox-Multilingual-pt-br 0.5B** (Resemble, V3 2025) | MIT / MIT | **pack dedicado pt-BR** | exaggeration/CFG; Turbo tem tags `[laugh]` `[cough]` | sim (referência de áudio) | normal: ~RTF<1 em GPU; **Turbo 350M: alvo sub-200ms** (en) | ~6GB inf fp32 / full ~18GB, LoRA menos | não-oficial maduro: gokhaneraslan/chatterbox-finetuning (23 línguas, LoRA), davidbrowne17/chatterbox-streaming | alta (HF atualizado constantemente; 1.67M downloads) |
| **VoxCPM2 2B** (OpenBMB, abr/2026) | Apache-2.0 / Apache-2.0 | **pt** (30 línguas) | clonagem "controlável" com style guidance (emoção, ritmo) + voice design por texto | sim ("ultimate cloning" com referência+transcrição) | RTF ~0.30 (4090) → ~0.13 com Nano-vLLM; 48kHz; não é streaming-first | **~8GB inf** / LoRA oficial (webUI `lora_ft_webui.py`), full FT disponível | **oficial: LoRA + full** | muito alta (28.2k stars, 14 releases) |
| **MOSS-TTS família** (OpenMOSS/MOSI.AI, fev–mai/2026) | Apache-2.0 / Apache-2.0 | **pt** (31 línguas, v1.5 mai/2026) | controle por pontuação/prosódia, `[pause X.Ys]`, VoiceGenerator (voz por descrição) | sim (zero-shot; v1.5 mais estável) | **MOSS-TTS-Realtime 1.7B: 180ms TTFB**, RTF 0.51 (L20); Nano 100M roda em CPU | 8B quantizado cabe em 8GB (llama.cpp); 1.7B em T4 / finetune: docs por arquitetura (Delay/Local/Realtime) | **oficial (tutoriais de finetune por modelo)** | muito alta (releases fev→mai/2026) |
| **OmniVoice** (k2-fsa, 2026) | Apache-2.0 / Apache-2.0 | pt entre **646 línguas** (qualidade pt-BR a validar) | limitado (NAR/diffusion; sem tags) | sim (zero-shot) | NAR diffusion — rápido em batch, não streaming token-a-token | leve (encoder Qwen3-0.6B) / treino: ecossistema k2-fsa/icefall | 2.1M downloads; ativo | alta |
| **Kokoro-82M** (hexgrad) | Apache-2.0 / Apache-2.0 | **pt-BR: 3 vozes** (pf_dora, pm_alex, pm_santa; grau de qualidade baixo/médio) | não (vozes fixas) | **não** | ~36x tempo real em T4; CPU ok | <2GB / treino não liberado | sem código de treino oficial | média (estável, sem release grande desde 2025) |
| **Pocket-TTS** (Kyutai, jan/2026; multilingual mai/2026) | pesos CC-BY-4.0 / código MIT | **pt** (1 das 6 línguas desde 2026-05-04; variante BR não documentada; card HF principal ainda diz "English only" — checar checkpoint multilingual) | não explícito | sim (wav de referência, `export-voice`) | **~200ms TTFA em CPU**, 6x tempo real em M4 | CPU (2 cores) / sem código de finetune publicado | sem treino oficial | alta (Kyutai ativa) |

## Tabela mestre B — License-clean SEM português (úteis como base de finetune, ferramenta ou referência)

| Modelo | Licença | Línguas | Emoção | Clone | Latência | VRAM | Treino | Atividade / nota |
|---|---|---|---|---|---|---|---|---|
| **Orpheus-TTS 3B** (Canopy) | Apache-2.0 | en + multilingual preview (es/it/fr/de/ko/hi/zh/ar — **sem pt**) | **tags** `<laugh>` `<sigh>` etc. | zero-shot + finetune | streaming ~200ms (realtime API) | inf ~16GB bf16; **Unsloth 4-bit cabe em T4** | scripts oficiais + **Unsloth Colab** | média-alta (release abr/2026 do pack árabe; issues ativas) |
| **CSM-1B** (Sesame) | Apache-2.0 | en (treino) | implícita (contexto conversacional) | in-context | RVQ+Mimi; não-streaming out-of-box | ~8GB / **Unsloth Colab grátis (T4)** | não-oficial: Unsloth, knottwill/sesame-finetune, csm-streaming | baixa (repo congelado desde 2025; **nenhum release novo da Sesame até jun/2026**) |
| **Maya1 3B** (Maya Research, nov/2025) | Apache-2.0 | en (voice design por descrição) | **20+ tags** (`<laugh>`, `<whisper>`, `<cry>`…) | via descrição de voz (não clone por referência) | sub-100ms com vLLM streaming | 16GB bf16 | sem treino oficial (arq. Llama → adaptável) | média |
| **Dia-1.6B / Dia2 1B-2B** (Nari Labs) | Apache-2.0 | en apenas | tags não-verbais (laughs etc.) | condicionamento por áudio | **Dia2 (nov/2025): streaming dialogue em tempo real** | ~10GB / sem código de treino oficial | média | Dia2 é referência de arquitetura conversacional streaming |
| **CosyVoice 2 / Fun-CosyVoice 3-0.5B** (Alibaba FunAudio, CV3 aberto 15/dez/2025) | Apache-2.0 | zh/en/ja/ko/de/es/fr/it/ru + 18 dialetos zh — **sem pt** | instruct (estilo/dialeto/emoção por texto) | zero-shot 3s | CV2: streaming ~150ms; CV3 similar | 0.5B: ~4GB / **stack completo de treino oficial** | muito alta | candidato a CPT pt-BR se Qwen3-TTS falhar (mesma casa) |
| **MegaTTS3 0.45B** (ByteDance) | Apache-2.0 | zh/en | limitado | **encoder WaveVAE oficial retido** (clone só com latents pré-extraídos; comunidade liberou encoder não-oficial) | RTF bom, não-streaming | ~6GB | parcial | baixa-média; veto prático para clone próprio |
| **Muyan-TTS** (MYZY, 2025) | Apache-2.0 | **en apenas** | prosódia podcast | finetune por falante (dozens of minutes) | 0.33s/1s áudio | médio / **treino completo aberto (~$50k budget paper)** | baixa | boa referência de receita de treino barato |
| **SoulX-Podcast-1.7B** (Soul, out/2025) | Apache-2.0 | zh/en + dialetos zh | paralinguística dialogal | zero-shot | longform podcast | ~8GB | inferência apenas | média | referência multi-speaker |
| **VibeVoice 1.5B/7B + Realtime-0.5B** (Microsoft) | MIT | en/zh (pt "exploratório", não suportado) | expressivo longform | sim | **Realtime-0.5B: streaming de texto em tempo real** | 7B: ~18GB; 0.5B: leve | sem treino oficial (repo MS esvaziado; fork comunitário vibevoice-community) | turbulenta (takedown set/2025, restaurado sem código) |
| **Parler-TTS** (HF) | Apache-2.0 | en | descrição textual de estilo | não (vozes por descrição) | não-streaming | ~6GB / **treino oficial HF completo** | parado desde ~2024 | referência didática |
| **Zonos-v0.1 1.6B** (Zyphra) | Apache-2.0 | en/zh/ja/fr/es/de — **sem pt** | embeddings de emoção explícitos | sim (5–30s) | ~2x tempo real (4090) | ~8GB | sem treino oficial | **parada desde 2025** (sem v0.2) |
| **dots.tts 2B** (rednote-hilab, 2026) | Apache-2.0 | en/zh foco (+24 testadas) | boa prosódia | sim | RTF bom | ~8GB | n/d | alta (trending) |
| **Supertonic-3 99M** (Supertone, abr/2026) | código MIT / **pesos OpenRAIL-M** (uso comercial com restrições de uso — não está na lista dura) | 31 línguas (checar pt) | tags de expressão | n/d | **on-device ONNX, >1200 chars/s CPU** | CPU | não | alta | cinza de licença |
| **Kani-TTS** (nineninesix) | Apache-2.0 (a verificar) | en + variantes | n/d | n/d | rápido, 400M | leve | n/d | baixa visibilidade jun/2026 |

## Tabela mestre C — VETADOS por licença (NC / research / community-cap / CPML) — só referência

| Modelo | Licença real (verificada) | Por que importa mesmo vetado |
|---|---|---|
| **Voxtral TTS 4B** (Mistral, 26/mar/2026) | **CC-BY-NC-4.0** ([TechCrunch](https://techcrunch.com/2026/03/26/mistral-releases-a-new-open-source-model-for-speech-generation/), [Mistral](https://mistral.ai/news/voxtral-tts/)) | 9 línguas **com pt**, 70ms, clone 3s — benchmark de qualidade/latência a bater |
| **Higgs Audio v3 4B** (Boson, 04/jun/2026) | **Research/NC**; comercial só com contrato ([Boson blog](https://www.boson.ai/blog/higgs-audio-v3-tts)) | 102 línguas, 21 emoções inline, chat-nativo streaming — é o teto técnico atual de TTS expressivo aberto-mas-NC |
| **Higgs Audio v2 3B** | Boson Community License (teto 100k usuários/ano, attribution Meta, naming) ([HF LICENSE](https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base/blob/main/LICENSE)) | tecnicamente forte; teto fere a restrição dura |
| **Fish-Speech / OpenAudio-S1-mini** | pesos **CC-BY-NC-SA-4.0** (código Apache) ([HF](https://huggingface.co/fishaudio/openaudio-s1-mini)) | — |
| **Fish Audio S2-Pro** (mar/2026) | **Fish Audio Research License** (comercial só com contrato) ([blog](https://fish.audio/blog/fish-audio-open-sources-s2/)) | **#1 open-weights na arena** (Elo 1123) — referência de teto de qualidade |
| **Spark-TTS-0.5B** | **re-licenciado Apache → CC-BY-NC-SA** ([commit HF](https://huggingface.co/SparkAudio/Spark-TTS-0.5B/commit/b63203d4bda1e47848dca3437411c6f2478b4d4b)) | alerta: licença de pesos pode mudar DEPOIS do release |
| **IndexTTS-2** (Bilibili, set/2025) | código Apache; **pesos: comercial só via indexspeech@bilibili.com** ([GitHub](https://github.com/index-tts/index-tts)) | SOTA de **desacoplamento emoção×timbre** (vetores 8-dim de emoção) — copiar a *técnica*, não os pesos |
| **Llasa-1B/3B/8B** (HKUST) | **CC-BY-NC-4.0** ([HF](https://huggingface.co/HKUSTAudio/Llasa-3B)) | receita de treino aberta (LLM+XCodec2) é útil academicamente |
| **F5-TTS / E2-TTS** | pesos CC-BY-NC (veto já registrado) | referência flow-matching |
| **XTTS-v2** (Coqui) | CPML (veto já registrado) | ainda 8.8M downloads — só baseline histórico |
| **MisoTTS 8B** (Miso Labs, 03/jun/2026) | "MIT modificado" com teto 50M MAU/US$10M/mês ([MarkTechPost](https://www.marktechpost.com/2026/06/04/miso-labs-releases-misotts-an-8b-emotive-text-to-speech-model-with-open-weights/)) | en-only; emotivo via contexto de áudio; cinza — fora da lista dura |
| **LFM2-Audio / LFM2.5-Audio 1.5B** (Liquid) | LFM Open License v1.0 (teto US$10M receita) ([Liquid](https://www.liquid.ai/lfm-license)) | speech-to-speech on-device interessante, mas licença fora da lista dura |
| **GLM-4-Voice** (Zhipu) | código Apache; **pesos sob GLM Model License** | zh/en; fora |
| **MiniCPM-o 2.6** (OpenBMB) | código Apache; pesos sob licença OpenBMB própria | fala out só zh/en; fora |
| **Kimi-Audio 7B** (Moonshot) | código MIT/Apache; pesos com termos próprios | zh/en; útil só como referência de audio-LLM |

## Tabela mestre D — Spine conversacional (full-duplex / omni)

| Modelo | Licença | pt na fala de SAÍDA | Latência | VRAM | Treino | Status jun/2026 |
|---|---|---|---|---|---|---|
| **Moshi 7B + Mimi** (Kyutai) | pesos **CC-BY-4.0**, código MIT/Apache | não (en; adaptação via receita J-Moshi) | **~200ms full-duplex** | bf16 ~17GB; int8 menos; finetune LoRA em 1×A100/L4 via moshi-finetune | **oficial (moshi-finetune)** | **ativa**: MoshiRAG (abr/2026), Pocket-TTS (jan/2026), ecossistema DSM/Unmute |
| **Qwen3-Omni-30B-A3B** (Instruct) | **Apache-2.0** | **sim — pt é 1 das 10 línguas de saída de fala** ([HF](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct)) | streaming talker em tempo real | ~70GB bf16 (MoE 30B/3B ativos); AWQ-4bit ~20GB+ — não cabe em Colab grátis, ok no GH200 | código de SFT em ecossistema (ms-swift etc.) | ativa; **Qwen3-Omni-Flash (dez/2025) aparenta ser API/não-aberto — só a família base é Apache** |
| **MoshiRAG** (Kyutai, abr/2026) | CC-BY-4.0 (linha Moshi) | não (en) | full-duplex + retrieval assíncrono | similar Moshi | aberto | novo — confirma a tese do spine Moshi |
| **Dia2 1B/2B** (Nari, nov/2025) | Apache-2.0 | não (en) | streaming conversacional (gera com poucos tokens de input) | ~6–10GB | sem treino oficial | referência de TTS conversacional streaming |
| **Step-Audio-2-mini (~8B)** (StepFun) | Apache-2.0 ([HF](https://huggingface.co/stepfun-ai/Step-Audio-2-mini)) | não (zh/en) | end-to-end conversa | ~18GB | parcial | referência GRPO paralinguístico (mantida) |
| **Step-Audio-EditX 3B** (nov/2025) | Apache-2.0 | zh/en (edição) | offline (edição iterativa) | 12–16GB | inferência | **ferramenta**: editar emoção/estilo de áudio existente → útil p/ gerar pares de dados emocionais do dataset do Pedro |
| **GLM-4-Voice / Kimi-Audio / MiniCPM-o / LFM2-Audio** | ver Tabela C | zh/en | — | — | — | fora por licença de pesos e/ou ausência de pt |

**Arena (contexto):** na TTS-Arena-V2 / Artificial Analysis (jun/2026), nenhum modelo open-weights está no top-10 geral; o melhor open-weights é Fish S2-Pro (Elo ~1123, research license). Kokoro segue o melhor "Apache pequeno" em custo. ([leaderboard](https://artificialanalysis.ai/text-to-speech/leaderboard), [TTS-Arena-V2](https://huggingface.co/spaces/TTS-AGI/TTS-Arena-V2))

---

## Fichas dos finalistas

### 1. Qwen3-TTS-12Hz (0.6B / 1.7B) — candidato #1 para (a)
- **Licença:** Apache-2.0 em pesos e código (confirmado no [repo oficial](https://github.com/QwenLM/Qwen3-TTS)). Releases: Base, CustomVoice, VoiceDesign (1.91M downloads no 1.7B-CustomVoice em ~5 meses).
- **pt-BR:** português é 1 das 10 línguas nativas. **Variante (BR vs PT) não documentada** — validar de ouvido antes de comprometer; de todo modo o finetune com a voz do Pedro fixa o sotaque carioca.
- **Emoção:** controle adaptativo de tom/ritmo/emoção por instrução e semântica; VoiceDesign cria persona por descrição em linguagem natural.
- **Clonagem:** 3s de áudio + transcrição; prompt de voz reutilizável (pré-computado).
- **Latência:** TTFA **97ms** end-to-end (streaming por caractere); vLLM day-0.
- **VRAM:** 1.7B bf16 ≈ 4–6GB inferência; LoRA finetune cabe em T4/L4 do Colab; full em A100-40GB.
- **Treino:** finetune oficial (link "Qwen3-TTS-Finetuning" no README). **Atenção:** a comunidade documentou 2 bugs no `sft_12hz.py` oficial (falta de `text_projection` e double label-shift que acelera a fala progressivamente) — o repo companheiro [qwen3-tts-lora-finetuning](https://github.com/cheeweijie/qwen3-tts-lora-finetuning) traz patches + scripts LoRA/eval/bench. Usar a versão patchada.
- **Risco:** modelo novo (jan/2026) — qualidade pt-BR específica ainda pouco reportada; tokenizer 12Hz próprio (menos ferramentas que Mimi/SNAC).

### 2. Chatterbox V3 / pt-BR pack + Turbo — candidato #2 e baseline imediato
- **Licença:** MIT em toda a família ([GitHub](https://github.com/resemble-ai/chatterbox)).
- **pt-BR:** [`ResembleAI/Chatterbox-Multilingual-pt-br`](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br) é um **finetune dedicado a português brasileiro** (0.5B, T3+S3Gen V3) — exatamente o nicho do projeto, e já resolve "dado sintético license-clean em pt-BR" hoje (substitui/complementa Kokoro).
- **Emoção:** exaggeration/CFG no V3; Turbo (350M, en-only) tem tags paralinguísticas `[laugh]`/`[cough]`.
- **Clonagem:** zero-shot por referência em 23 línguas.
- **Latência:** Turbo mira sub-200ms (serviço); o pt-br pack é um modelo "qualidade", não o mais rápido.
- **Treino:** nada oficial, mas o ecossistema comunitário é o mais maduro do pool: [gokhaneraslan/chatterbox-finetuning](https://github.com/gokhaneraslan/chatterbox-finetuning) (LoRA+full, 23 línguas, extensão de vocabulário), [davidbrowne17/chatterbox-streaming](https://github.com/davidbrowne17/chatterbox-streaming). Full FT pede ~18GB (L4/A100 Colab); LoRA menos.
- **Bônus ético:** watermark Perth embutido — alinhado com a frente 70-voice-watermark.

### 3. VoxCPM2 (2B, OpenBMB) — candidato qualidade/48kHz
- Apache-2.0, 30 línguas com pt, 2M horas de treino, 48kHz nativo, clonagem com style guidance (emoção/ritmo preservando timbre), **LoRA oficial com webUI** + full FT, ~8GB inferência, RTF 0.13 (Nano-vLLM). Tokenizer-free (não-AR puro) → **não é streaming-first**: melhor para gravação/dataset/conteúdo que para conversa de 200ms. Repo muito ativo (28k stars). ([GitHub](https://github.com/OpenBMB/VoxCPM))

### 4. Família MOSS-TTS (OpenMOSS) — candidato duplo (a)+(b)
- Apache-2.0, 31 línguas com pt (v1.5, mai/2026). Peças: v1.5 8B (flagship), Local-Transformer 1.7B (streaming), **Realtime 1.7B (TTFB 180ms pós-warmup, RTF 0.51 em L20, total ~377ms com LLM)**, VoiceGenerator 1.7B (voz por descrição), Nano 100M (CPU). **Docs oficiais de finetune por arquitetura.** 8B quantizado roda em 8GB via llama.cpp; 1.7B treina em Colab. É hoje o stack Apache mais completo para a perna TTS de um agente conversacional em pt. Risco: muito novo, qualidade pt-BR a validar de ouvido. ([GitHub](https://github.com/OpenMOSS/MOSS-TTS))

### 5. Orpheus-TTS (3B) — ainda no páreo, agora como plano C
- Apache-2.0, tags de emoção, streaming ~200ms, **Unsloth Colab T4 grátis** — a melhor DX de finetune do pool. Mas: **sem pt no pré-treino** (multilingual preview cobre es/it/fr/de/ko/hi/zh/ar) → adaptar exige CPT de língua (mais dados/compute que um finetune de voz). Atividade ok (release árabe abr/2026), porém o frescor está nos concorrentes. ([GitHub](https://github.com/canopyai/Orpheus-TTS), [Unsloth](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning))

### Spine — estado da aposta
- **Moshi/Kyutai (CC-BY-4.0) permanece a aposta certa.** Nada open-source full-duplex melhor apareceu até jun/2026; a Kyutai está ativa (MoshiRAG abr/2026; Pocket-TTS jan/2026 + multilingual mai/2026 com pt). Receita J-Moshi + moshi-finetune LoRA-first inalterada. ([kyutai.org](https://kyutai.org/), [MoshiRAG](https://kyutai.org/blog/2026-04-30-moshi-rag))
- **Qwen3-Omni-30B-A3B (Apache) co-aposta mantida** — pt nativo na saída de fala; continua não cabendo em Colab (GH200/SDumont ok). Qwen3-Omni-Flash (dez/2025): tudo indica API-only; **não** assumir pesos abertos.
- **CSM-1B:** papel inalterado (componente de voz, não spine), mas a crença "sem código de treino" está obsoleta na prática: **Unsloth tem notebook Colab grátis para finetune do CSM-1B** + repos comunitários (knottwill/sesame-finetune, csm-streaming). Sesame não lançou nada aberto novo desde 2025.
- **Cascata revalorizada:** faster-whisper → LLM → **Qwen3-TTS streaming (97ms) ou MOSS-TTS-Realtime (180ms)** deve entregar p50 bem abaixo de 800ms. Vale construir como Fase-0/fallback enquanto o Moshi-pt não fica pronto.

---

## Veredicto — PRIORIDADE

### (a) TTS expressivo pt-BR finetunado com a voz do Pedro no Colab
1. **Qwen3-TTS-12Hz-1.7B** (Apache, pt nativo, finetune oficial+LoRA, 97ms, T4-ok) — **novo candidato #1**.
2. **Chatterbox-Multilingual-pt-br** (MIT, pack pt-BR dedicado, finetune comunitário maduro, watermark) — #2 e baseline/dado sintético já.
3. **MOSS-TTS (1.7B Local/Realtime ou 8B)** (Apache, pt, finetune oficial, perna realtime) — #3.
4. **VoxCPM2** (Apache, pt, LoRA webUI, 48kHz) — #4, foco qualidade de estúdio/dataset.
5. **Orpheus-3B via Unsloth** (Apache, tags de emoção, melhor DX Colab; exige CPT pt) — #5/plano C.
   - *Mantém no kit:* Kokoro (pt-BR, leve, dado sintético), OmniVoice (clone zero-shot 646 línguas — testar pt-BR), Step-Audio-EditX (Apache; editar emoção dos áudios do dataset).

### (b) Spine conversacional de baixa latência
1. **Moshi/Kyutai + receita J-Moshi** — inalterado e reforçado (ecossistema vivo).
2. **Qwen3-Omni-30B-A3B** — co-aposta inalterada (pt na fala, Apache; GH200).
3. **Cascata turbinada**: faster-whisper → LLM → Qwen3-TTS/MOSS-TTS-Realtime — promovida de "piso" a plano B real (~300–500ms plausível).
4. **Dia2** — referência arquitetural de TTS conversacional streaming (Apache, en).
5. **Pocket-TTS** — wildcard de edge/CPU com pt (CC-BY-4.0, 100M, ~200ms) para protótipos baratos.

## Correções ao registro de crenças (2026-05-17 → 2026-06-10)
- "TTS license-clean para dado sintético = Kokoro + Chatterbox" → **adicionar Qwen3-TTS, VoxCPM2, MOSS-TTS e o pack Chatterbox pt-BR**; Kokoro deixa de ser o único com pt.
- "CSM-1B sem código de treino" → **desatualizado na prática** (Unsloth Colab + 2 repos comunitários); segue sem código *oficial*.
- "Cascata = piso de latência, não destino" → **suavizar**: com TTFA de 97–180ms na perna TTS, cascata vira fallback competitivo.
- Spark-TTS **saiu** do universo permitido (re-licenciado NC). Higgs v2/v3, Voxtral TTS, Fish S2-Pro, IndexTTS-2, MisoTTS, LFM2-Audio: **vetados/cinza** — usar só como referência de técnica e benchmark.

## Fontes primárias principais
- https://github.com/QwenLM/Qwen3-TTS · https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
- https://github.com/resemble-ai/chatterbox · https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br
- https://github.com/OpenBMB/VoxCPM · https://huggingface.co/openbmb/VoxCPM2
- https://github.com/OpenMOSS/MOSS-TTS · https://huggingface.co/OpenMOSS-Team/MOSS-TTS-v1.5
- https://github.com/kyutai-labs/pocket-tts · https://kyutai.org/blog/2026-05-04-pocket-tts-multilingual · https://kyutai.org/blog/2026-04-30-moshi-rag
- https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct · https://github.com/QwenLM/Qwen3-Omni
- https://mistral.ai/news/voxtral-tts/ · https://techcrunch.com/2026/03/26/mistral-releases-a-new-open-source-model-for-speech-generation/
- https://www.boson.ai/blog/higgs-audio-v3-tts · https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base/blob/main/LICENSE
- https://fish.audio/blog/fish-audio-open-sources-s2/ · https://huggingface.co/fishaudio/openaudio-s1-mini
- https://huggingface.co/SparkAudio/Spark-TTS-0.5B/commit/b63203d4bda1e47848dca3437411c6f2478b4d4b
- https://github.com/index-tts/index-tts · https://huggingface.co/HKUSTAudio/Llasa-3B
- https://github.com/canopyai/Orpheus-TTS · https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning
- https://github.com/FunAudioLLM/CosyVoice · https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512
- https://github.com/nari-labs/dia2 · https://github.com/k2-fsa/OmniVoice · https://github.com/supertone-inc/supertonic
- https://huggingface.co/stepfun-ai/Step-Audio-2-mini · https://github.com/stepfun-ai/Step-Audio-EditX
- https://www.marktechpost.com/2026/06/04/miso-labs-releases-misotts-an-8b-emotive-text-to-speech-model-with-open-weights/ · https://www.liquid.ai/lfm-license
- https://artificialanalysis.ai/text-to-speech/leaderboard · https://huggingface.co/spaces/TTS-AGI/TTS-Arena-V2
- https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md · https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS
- https://github.com/cheeweijie/qwen3-tts-lora-finetuning · https://github.com/gokhaneraslan/chatterbox-finetuning
- https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B · https://github.com/vibevoice-community/VibeVoice
