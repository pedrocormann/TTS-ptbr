# 70 — Receitas de API verificadas (2026-06-10) — base dos notebooks 02-04

> Extração via leitura direta de fonte (notebooks oficiais, código, model cards).
> Os notebooks `notebooks/02-04` implementam isto; aqui ficam os fatos que importam
> se algo quebrar.

## CSM-1B via Unsloth (notebook 04)

- Pins do notebook oficial: `transformers==4.52.3`, `trl==0.22.2` (--no-deps),
  `torchcodec`, `datasets>=3.4.1,<4.0.0`; xformers escolhido pela versão do torch.
- Base: `unsloth/csm-1b` (mirror Apache **sem gate**; `sesame/csm-1b` é gated-auto).
- Dataset: colunas `text`+`audio` (24kHz cast), tags de emoção INLINE no texto
  (padrão Elise); `role` da conversa = speaker id ("0").
- Preprocess: `processor.apply_chat_template(conv, tokenize=True, return_dict=True,
  output_labels=True, text_kwargs={max_length, pad_to_multiple_of=8},
  audio_kwargs={sampling_rate:24000, max_length:<MAIOR CLIPE+1>, padding:'max_length'})`.
  Oficial usa 240001 (=10s); calcular do dataset. `depth_decoder_labels_ratio` existe
  no processor (amortização).
- Treino: `FastModel.from_pretrained(auto_model=CsmForConditionalGeneration,
  load_in_4bit=False)` + `get_peft_model(r=32..64, target qkvo+mlp)` + `Trainer` HF
  puro (batch 2, ga 4, lr 2e-4, adamw_8bit).
- Geração: SEM contexto a voz VARIA (base model). Sempre 2 turnos: [referência
  texto+áudio, texto novo]. `max_new_tokens=125`≈10s — aumentar p/ falas longas.
- Full-FT p/ língua (knottwill): lr 3e-5, wd 0.002, batch 8, decoder_loss_weight 0.5,
  warmup 1000, max_grad_norm 1.3; depth decoder em 1/16 dos frames; stack
  torchtune/moshi (transformers 4.49), NÃO o caminho HF.

## Qwen3-TTS-1.7B (notebook 03)

- `pip install qwen-tts` (pina `transformers==4.57.3`, `accelerate==1.12.0` — NÃO
  atualizar). Scripts de finetune só no clone do repo.
- Base de finetune: **`Qwen3-TTS-12Hz-1.7B-Base`** (CustomVoice não documenta FT;
  0.6B-Base crasha — issues #120/#174/#198/#297).
- **T4 NÃO** (sem bf16); L4 24GB ok (LoRA validado em 3090 24GB); A100 folga.
- Dataset JSONL: `{audio (24kHz mono OBRIGATÓRIO), text (SEM tags!), ref_audio
  (o MESMO 3-10s em todas as linhas)}` → `finetuning/prepare_data.py` (codes;
  memory leak #5 — chunks) → treino.
- Bugs do `sft_12hz.py` oficial: (1) `text_projection` faltante (1.7B treina
  silenciosamente errado); (2) double label-shift → fala ACELERA a cada época
  (issue #179/PR #178). Usar `cheeweijie/qwen3-tts-lora-finetuning` (patch sobre
  commit `0c6a7cb`): LoRA r=16/α=32/dropout .05, **lr 2e-6** (2e-5 default = ruído).
- Inferência LoRA: `LORA_SCALE` 0.25-0.35 (1.0 over-steers); sweep 0.2/0.3/0.35/0.5.
  Gen params validados: temp .8, top_p .85, top_k 30, rep 1.05, eos_token_id=
  [2150,2157,151670,151673,151645,151643]. 3-5 épocas; >10 = robótico.
- `instruct` (emoção) é capacidade do CustomVoice/VoiceDesign; em Base finetunado =
  empírico, testar. Streaming nativo (~97ms); vLLM-Omni só inferência offline.

## Chatterbox-Multilingual-pt-br (notebook 02-A)

- `pip install chatterbox-tts` (0.1.7; se `t3_model=` der TypeError → instalar do git).
- Pack pt-BR é repo separado (`ResembleAI/Chatterbox-Multilingual-pt-br`, MIT) e o
  `from_pretrained` tem REPO_ID hardcoded → montar pasta e usar **`from_local`**:
  `t3_pt_br.safetensors` + `s3gen_v3.pt`→renomear `s3gen.pt` + `grapheme_*.json`
  (do pack) + `ve.pt`/`conds.pt`/`Cangjie5_TC.json` (do repo base);
  `from_local(d, device, t3_model='t3_pt_br.safetensors')`.
- Multilingual amplo soa **pt-PT** (issue #281) — o pack pt-br existe pra isso.
- `generate(text, language_id='pt', audio_prompt_path=ref, exaggeration=.5,
  cfg_weight=.5, temperature=.8)`; expressivo: exag .7 + cfg .3. Referência
  truncada em 10s (decoder)/6s (encoder). Saída 24kHz. Watermark Perth SEMPRE
  (sem flag p/ desligar). `max_new_tokens=1000` hardcoded → textos curtos.
  CPU quebrado (#351) — GPU.
- Finetune comunitário (gokhaneraslan): LJSpeech format, ≥30min, LoRA r=64/α=128
  config em `src/config.py`; sem números de VRAM publicados.

## Pocket-TTS pt (notebook 02-B)

- `pip install pocket-tts` (2.1.0). Configs pt: **`portuguese`** (100M destilado) e
  **`portuguese_24l`** (qualidade). Voz default pt = "rafael" (CC0).
- Clone: pesos gated (`kyutai/pocket-tts`, aceitar termos + HF_TOKEN); fallback
  automático sem clone (`...-without-voice-cloning`). `export-voice ref.wav
  voz.safetensors --language portuguese` → `generate --voice voz.safetensors`.
- `serve --language portuguese` (localhost:8000); ~200ms TTFA, 6× RT em CPU M4;
  `--quantize` +30%. Card HF "English only" está DESATUALIZADO (pt nos configs).
- Vozes `expresso/`/`ears/` do catálogo tts-voices = **NC** (não usar no produto).
