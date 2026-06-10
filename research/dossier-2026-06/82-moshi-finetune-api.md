# 82 — API exata do moshi-finetune (kyutai-labs)

**Data:** 2026-06-10 · **Frente C** do dossiê · Para escrever um notebook Colab fiel.
**Fontes primárias (lidas na fonte, raw do GitHub em 2026-06-10):**
- Repo: https://github.com/kyutai-labs/moshi-finetune
- `README.md`, `train.py`, `example/moshi_7B.yaml`, `annotate.py`, `pyproject.toml`, `finetune/args.py`, `finetune/data/{args,dataset,interleaver,data_loader}.py`, `finetune/checkpointing.py`, `tutorials/moshi_finetune.ipynb`
- Inferência: https://github.com/kyutai-labs/moshi (`moshi/moshi/server.py`, `moshi/moshi/models/loaders.py`, `scripts/import_mlx_lora.py`, `moshi_mlx/moshi_mlx/local_web.py`)

**Estado do repo:** último commit em `main` é de **2025-07-07** ("format"; antes: "overwrite run dir arg"). O repo está estável/parado há ~11 meses — a API abaixo é a vigente. Licença do código: **Apache 2.0** (LICENSE na raiz; deriva de mistral-finetune). Pesos `kyutai/moshiko-pytorch-bf16`: **CC-BY-4.0** (model card HF) — compatível com a régua de licença do projeto.

---

## 1. Instalação e pins

Não existe `requirements.txt` no repo (o README menciona um, mas o arquivo não existe — a fonte é o `pyproject.toml`). Python **>= 3.10**. Kyutai recomenda `uv` (`uv run torchrun ...` instala tudo via pyproject), mas `pip install -e .` funciona.

Dependências exatas do `pyproject.toml` (main, 2026-06-10):

```
fire, simple-parsing, pyyaml, safetensors, tensorboard, tqdm,
torch==2.6,
triton>=3.2,
moshi @ git+https://github.com/kyutai-labs/moshi.git#subdirectory=moshi,
sphn==0.1.12,
auditok==0.2,
whisper_timestamped,
huggingface_hub, torchaudio, submitit,
llvmlite>=0.44, numba>=0.61
```

Pontos de atenção para Colab:
- **`torch==2.6` é pin exato.** Colab costuma vir com torch mais novo; `pip install -e .` vai fazer downgrade (demorado, mas funciona). Se quebrar com a imagem do Colab, instalar torch 2.6 + cu124 explicitamente antes.
- `moshi` vem do git (sem pin de commit/versão — pega o `main` do dia).
- `sphn==0.1.12` é pin exato (o data loader depende de `sphn.dataset_jsonl`, que existe nessa versão).
- O notebook oficial instala exatamente assim: `git clone https://github.com/kyutai-labs/moshi-finetune.git` + `%pip install -e /content/moshi-finetune` (nada mais; `gradio` só na hora da inferência).

## 2. `train.py` — invocação e args

- Entry point: `fire.Fire(train)`; `train(config: str)` recebe **um único argumento posicional: o caminho do YAML**. Não há flags de CLI além disso — toda a configuração vive no YAML.
- Sempre via torchrun, mesmo com 1 GPU:
  ```sh
  torchrun --nproc-per-node 1 -m train example/moshi_7B.yaml
  # multi-GPU: torchrun --nproc-per-node 8 --master_port $RANDOM -m train example/moshi_7B.yaml
  ```
- `TrainArgs.load(config, drop_extra_fields=False)` → **campo desconhecido no YAML = erro** (parsing estrito via simple-parsing).
- **`run_dir` precisa NÃO existir** (RuntimeError se existir), a menos que `overwrite_run_dir: true` (aí ele apaga e recria). No notebook há uma célula comentada `rm -r /content/test` por isso.
- Constraint: `full_finetuning: true` exige `lora.enable: false` e vice-versa (asserts no início).
- Otimizador fixo: AdamW (betas 0.9/0.95, eps 1e-8) + OneCycleLR (`max_lr=optim.lr`, `total_steps=max_steps`, `pct_start=optim.pct_start`). Grad clip `max_norm` (default 1.0). Mixed precision manual: params em `param_dtype` (bf16), upcast p/ fp32 no step do otimizador.
- `num_microbatches` = gradient accumulation (default 1).
- Seta `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` sozinho.

## 3. TODOS os campos do config com defaults

Defaults do código (`finetune/args.py`) vs. o que o `example/moshi_7B.yaml` define:

| Campo | Default (código) | example/moshi_7B.yaml | Notas |
|---|---|---|---|
| `data.train_data` | `""` | `''` (Fill) | caminho do .jsonl (ou dir com .jsonl, ou `path:peso,path2:peso2`) |
| `data.eval_data` | `""` | `''` | opcional |
| `data.shuffle` | `false` | `true` | |
| `run_dir` | **obrigatório** | `""` (Fill) | não pode existir |
| `moshi_paths.hf_repo_id` | `"kyutai/moshiko-pytorch-bf16"` | idem | |
| `moshi_paths.{mimi_path,moshi_path,tokenizer_path,config_path}` | `null` | — | p/ pesos locais |
| `full_finetuning` | `false` | `false` | |
| `lora.enable` | `false` | `true` | |
| `lora.rank` | `64` | `128` | |
| `lora.scaling` | `2.0` | `2.` | |
| `lora.ft_embed` | `false` | `false` | full-FT das embeddings junto com LoRA |
| `first_codebook_weight_multiplier` | `1.0` | `100.` | peso do codebook semântico no loss |
| `text_padding_weight` | `0.5` | `.5` | peso do padding no loss de texto |
| `duration_sec` | `10` | `100` | comprimento da janela de treino (s) |
| `batch_size` | `1` | `16` | por GPU |
| `max_steps` | `100` | `2000` | |
| `num_microbatches` | `1` | — | grad accumulation |
| `max_norm` | `1.0` | — | grad clip |
| `gradient_checkpointing` | `true` | `true` | por camada do transformer |
| `optim.lr` | `1e-4` | `2e-6` | **use 2e-6** (README recomenda) |
| `optim.weight_decay` | `0.1` | `0.1` | |
| `optim.pct_start` | `0.05` | `0.05` | warmup do OneCycleLR |
| `seed` | `0` | `0` | |
| `log_freq` | `1` | `1` | |
| `do_eval` | `false` | `false` | |
| `eval_freq` | `0` | `100` | |
| `do_ckpt` | `true` | `true` | |
| `ckpt_freq` | `0` | `100` | <1 = só o último |
| `num_ckpt_keep` | `3` | — | |
| `save_adapters` | `true` | `true` | `true` = salva só `lora.safetensors`; `false` = merge no base (precisa RAM/VRAM extra) |
| `param_dtype` | `"bfloat16"` | — | |
| `overwrite_run_dir` | `false` | — | |
| `wandb.{project,run_name,key,offline}` | `null/false` | comentado | opcional |

Orçamento de tokens (README): `total tokens = max_steps × num_gpus × batch_size × duration_sec × 9 tokens/step × 12.5 steps/s`.

## 4. Formato exato dos dados

### 4.1 WAV estéreo — qual canal é quem (CONFIRMADO)
README, literal: *"the left channel is used for the audio generated by moshi, whereas the second channel is used for the user's input"*.
- **Canal esquerdo (canal 0) = a voz que o modelo vai FALAR** (no nosso caso: a voz pt-BR carioca alvo).
- **Canal direito (canal 1) = o usuário/interlocutor.**
- Confirmação no código: `annotate.py` transcreve só `channel=0` e rotula tudo `SPEAKER_MAIN`; o `Interleaver` é criado com `keep_main_only=True` → o stream de texto supervisiona apenas o falante do canal esquerdo. O áudio dos DOIS canais vira tokens Mimi (8 codebooks por canal), e o loss de áudio cobre `model.dep_q` codebooks (os do falante principal).

### 4.2 Sample rate
- Mimi opera a **24 kHz** (frame rate 12.5 Hz). O loader (`sphn.dataset_jsonl(..., sample_rate=mimi.sample_rate)`) **resampleia na leitura**, então o WAV pode estar em outra taxa — mas gravar/exportar em 24 kHz estéreo evita resampling implícito.
- O `annotate.py` por sua vez resampleia o canal 0 para **16 kHz** antes do Whisper.

### 4.3 O `.jsonl` do dataset
Uma linha por arquivo:
```json
{"path": "data_stereo/a.wav", "duration": 24.521950113378686}
```
- `path` relativo (resolvido pelo sphn a partir do local do .jsonl, como no exemplo do README com `data/mycooldataset.jsonl` + `data/data_stereo/*.wav`).
- `duration` em segundos (float). Gerado com `sphn.durations(paths)` (snippet no README).
- `data.train_data` aceita: um arquivo .jsonl, um diretório (pega todos `*.jsonl` recursivamente), ou múltiplas fontes com pesos: `"a.jsonl:0.7,b.jsonl:0.3"`.
- Chunking: cada arquivo é fatiado em janelas de `duration_sec` (último segmento é padded; `pad_last_segment=True`).

### 4.4 O `.json` de transcrição (por WAV, mesmo nome)
Formato exato produzido pelo `annotate.py` e consumido pelo `InterleavedTokenizer`:
```json
{
  "alignments": [
    ["palavra", [inicio_s, fim_s], "SPEAKER_MAIN"],
    ...
  ]
}
```
- Lista de `[texto_da_palavra, [start, end], speaker_label]`, **palavra a palavra**, em segundos, ordenável por start.
- O label que importa é `"SPEAKER_MAIN"` (constante `main_speaker_label` no Interleaver). Só ele entra no stream de texto (com `keep_main_only=True`, que é o que o train.py usa).
- Campo opcional: `"text_conditions"` (vira `condition_attributes` — não usado no fluxo básico).
- O .json é localizado por convenção: `os.path.splitext(wav_path)[0] + ".json"`.
- **Dica para o nosso pipeline:** se já tivermos transcrição alinhada própria (ex.: do kit de gravação), podemos gerar esses .json diretamente sem rodar o annotate.py — é só respeitar o formato acima.

## 5. `annotate.py` — args e comportamento

```sh
python annotate.py SEU.jsonl --local --lang pt --whisper_model medium
```

| Arg | Default | Nota |
|---|---|---|
| `egs` (posicional) | — | o .jsonl (aceita .jsonl.gz) |
| `--lang` | `"en"` | **`--lang pt` existe e funciona** (passa direto pro whisper_timestamped; Whisper é multilíngue e suporta português) |
| `--whisper_model` | `"medium"` | help: "use medium for stereo!"; se pedir `large-v3` ele avisa que medium é melhor p/ estéreo com VAD |
| `-l, --local` | off | **OBRIGATÓRIO fora de SLURM** (Colab/local). Sem `--local`, ele tenta submeter jobs via `submitit.SlurmExecutor` |
| `-S, --shards` | `1` | paralelização SLURM (`--shards 64 --partition x`) |
| `--keep_silence_in_segments` | `True` | reintroduz silêncio nas bordas dos segmentos VAD (mitiga palavras deslocadas) |
| `--rerun_errors` | off | re-processa arquivos com `.json.err` |
| `--log_folder`, `--partition`, `-v` | — | SLURM/log |

Comportamento interno:
- Lê o WAV com `sphn`, pega **somente o canal 0** (esquerdo = falante principal), resampleia p/ 16 kHz.
- `whisper_timestamped.transcribe(model, vocals, language=lang, vad="auditok" se duracao>10s, best_of=5, beam_size=5, temperature=(0.0..1.0))` → timestamps por palavra.
- Escreve `<wav>.json` (atômico via rename); em erro não-CUDA cria `<wav>.json.err` e segue. Pula arquivos <1000 bytes e já anotados. Limite de 4h por arquivo.
- Requer GPU (`.cuda()` hard-coded).
- **Atenção pt-BR:** o annotate só transcreve o canal do modelo. O canal do usuário não é transcrito nem supervisionado em texto (só em áudio) — para nosso dataset sintético full-duplex isso simplifica: só a voz-alvo precisa de alinhamento.

## 6. O notebook Colab oficial (`tutorials/moshi_finetune.ipynb`)

Transcrição fiel (raw lido em 2026-06-10; o notebook tem 15 células):

1. **GPU alvo declarada:** *"You can run this notebook in Google Colab using a A100 GPU"* (Colab Pro; A100 40GB).
2. Install: `%cd /content/` + `!git clone https://github.com/kyutai-labs/moshi-finetune.git` + `%pip install -e /content/moshi-finetune`.
3. Dataset: **kyutai/DailyTalkContiguous** (HF dataset, 14 GB) via `snapshot_download("kyutai/DailyTalkContiguous", repo_type="dataset", local_dir="/content/data/daily-talk-contiguous")`. O jsonl vem pronto: `dailytalk.jsonl`.
4. Env: `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `CUDA_VISIBLE_DEVICES=0`.
5. Config usada no Colab (diferenças vs. example yaml em **negrito**):
   - `train_data: /content/data/daily-talk-contiguous/dailytalk.jsonl`, `shuffle: true`
   - `hf_repo_id: kyutai/moshiko-pytorch-bf16`, LoRA `rank 128 / scaling 2.0 / ft_embed false`
   - `first_codebook_weight_multiplier: 100.`, `text_padding_weight: .5`
   - `duration_sec: 100`, **`batch_size: 1`** (vs 16), **`max_steps: 300`** (vs 2000)
   - `gradient_checkpointing: true`, lr `2e-6`, wd `0.1`, `pct_start 0.05`
   - **`log_freq: 10`, `ckpt_freq: 10`**, `do_eval: False`, `save_adapters: True`, `run_dir: /content/test`
   - Comentário no notebook: *"we recommend a sequence duration of 300 seconds"* (apesar de usar 100).
6. Treino: `!cd /content/moshi-finetune && torchrun --nproc-per-node 1 -m train /content/example.yaml`.
7. **Tempo de treino: NÃO informado no notebook** (sem outputs salvos). Estimativa por aritmética: README mede ~12k tokens/s em 1×H100 com batch 16; com batch 1 numa A100 a utilização cai; 300 steps × 1 × 100s × 9 × 12.5 ≈ 3.4M tokens → ordem de dezenas de minutos na A100, não horas (estimativa, não medida).
8. Inferência no próprio Colab: `!pip install gradio` e
   ```sh
   python -m moshi.server --gradio-tunnel \
     --lora-weight=/content/test/checkpoints/checkpoint_000300/consolidated/lora.safetensors \
     --config-path=/content/test/checkpoints/checkpoint_000300/consolidated/config.json
   ```
   (gradio tunnel para levar áudio do browser local até o Colab.)

Layout do checkpoint (de `finetune/checkpointing.py`): `<run_dir>/checkpoints/checkpoint_NNNNNN/consolidated/` contendo `lora.safetensors` (se `save_adapters: true`) **ou** `consolidated.safetensors` (merge/full-FT), + `config.json` (o lm_config com `lora`, `lora_rank`, `lora_scaling` embutidos).

## 7. VRAM real e knobs

Números medidos do README (com a receita recomendada: LoRA rank 128, scaling 2.0, `duration_sec 100`, `batch_size 16`, grad ckpt on, bf16):

| Setup | Tokens/s | Pico de memória alocada |
|---|---|---|
| 1×H100 (80GB) | ≈12k | **39.6 GB** |
| 8×H100 | ≈10.7k | 23.7 GB/GPU |

Knobs disponíveis (ordem recomendada pelo README: primeiro `batch_size`, depois `duration_sec`):
- `batch_size` — alavanca principal; o notebook roda com `batch_size 1` numa A100-40GB.
- `duration_sec` — reduz ativações linearmente; **cuidado**: o README avisa que encurtar demais degrada a experiência (modelo "fica mudo" mais cedo na conversa).
- `num_microbatches` — grad accumulation para manter batch efetivo com menos VRAM.
- `gradient_checkpointing: true` — já é o default.
- `lora.rank` ≤128 (rank 64 é o default do código; menos params treináveis = menos estados de otimizador).
- **Não há suporte 8-bit/bitsandbytes/QLoRA** no repo: otimizador é AdamW fp32 sobre os params treináveis, base congelada em bf16, FSDP via `wrapped_model.get_fsdp_model`.

Estimativas (extrapolação minha, não medida pela Kyutai):
- **A100-80GB:** a receita cheia do README (bs 16, dur 100) cabe (~40GB pico < 80GB), com folga até para bs maior ou `duration_sec 300`.
- **A100-40GB (Colab):** bs 16 + dur 100 NÃO cabe (pico 39.6GB ≈ limite, sem margem p/ fragmentação). Caminho seguro = o do notebook oficial: **bs 1–4, dur 100** (+ `num_microbatches` p/ batch efetivo 16). Alternativa: bs 8 com dur 50.

## 8. Carregando o LoRA treinado para conversar

### 8.1 PyTorch — `moshi.server` (caminho oficial)
```sh
python -m moshi.server \
  --lora-weight=$CKPT/consolidated/lora.safetensors \
  --config-path=$CKPT/consolidated/config.json \
  [--gradio-tunnel]   # p/ Colab
```
- Args relevantes do `moshi/server.py` (lidos na fonte): `--lora-weight`, `--config-path`, `--hf-repo` (base; default moshiko), `--moshi-weight`, `--mimi-weight`, `--tokenizer`, `--cfg-coef` (default 1.0), `--device`, `--half`, `--no_fuse_lora` (por default o LoRA é **fundido** nos pesos ao carregar: `fuse_lora=True`).
- Internamente: `loaders.CheckpointInfo.from_hf_repo(..., lora_weights=..., config_path=...)` → `get_moshi(fuse_lora=True)`. O `config.json` salvo pelo finetune carrega `lora_rank`/`lora_scaling`, então o server reconstrói a arquitetura certa sozinho.
- Full-FT / merge (`save_adapters: false`): `python -m moshi.server --moshi-weight=$CKPT/consolidated/consolidated.safetensors --config-path=$CKPT/consolidated/config.json` (o README tem um typo com `consolidated/consolidated/` duplicado nesse trecho).

### 8.2 MLX (Mac) — via conversão
- `moshi_mlx` (`local.py`/`local_web.py`) **não tem flag `--lora-weight`** — não carrega adapter direto.
- Caminho oficial: script **`scripts/import_mlx_lora.py`** no repo moshi: recebe `--lora-weight`, `--config-path` (+ `--hf-repo`/`--moshi-weight` p/ o base) e um `out.safetensors`; funde o LoRA e exporta os pesos no layout MLX. Depois: `python -m moshi_mlx.local_web --moshi-weight out.safetensors --lm-config <config>` (com `-q 4|8` para quantizar).
- Alternativa equivalente: treinar/checkpointar com `save_adapters: false` e converter o `consolidated.safetensors`.

## 9. Implicações para o TTS-ptbr (notebook 05)

1. **Receita Colab A100-40GB fiel ao oficial:** clone + `pip install -e .`; YAML = o do notebook (bs 1, dur 100, rank 128, lr 2e-6, ckpt_freq 10); subir nosso dataset estéreo 24kHz com a voz carioca no **canal esquerdo**; `annotate.py SEU.jsonl --local --lang pt --whisper_model medium` (ou gerar os `.json` de alignments nós mesmos, formato da §4.4 — preferível, já que teremos transcrição ground-truth do kit de gravação, evitando erros do Whisper em pt).
2. **Licenças OK:** código Apache-2.0, pesos moshiko CC-BY-4.0 — dentro da régua dura do produto.
3. **Riscos/limitações:** (a) base Moshi é treinado em inglês (model card: `language: en`) — fine-tune pt-BR com LoRA rank 128 vai precisar de dados suficientes e talvez `lora.ft_embed: true` p/ vocabulário; (b) repo parado desde 2025-07 com `torch==2.6` pinado — risco de fricção com imagens novas do Colab; (c) `moshi` instalado do git sem pin — considerar pinar um commit no notebook p/ reprodutibilidade.
4. **O que NÃO existe:** QLoRA/8-bit; resume de checkpoint (não há flag de resume no TrainArgs); suporte a mono (o pipeline pressupõe estéreo); flag de língua no treino (a língua entra só pelos dados + tokenizer SentencePiece existente).

## Fontes
- https://github.com/kyutai-labs/moshi-finetune (README; commit main de 2025-07-07)
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/train.py
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/finetune/args.py
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/example/moshi_7B.yaml
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/annotate.py
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/finetune/data/dataset.py · interleaver.py · data_loader.py · args.py
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/pyproject.toml
- https://raw.githubusercontent.com/kyutai-labs/moshi-finetune/main/tutorials/moshi_finetune.ipynb
- https://raw.githubusercontent.com/kyutai-labs/moshi/main/moshi/moshi/server.py · models/loaders.py · scripts/import_mlx_lora.py · moshi_mlx/moshi_mlx/local_web.py
- https://huggingface.co/kyutai/moshiko-pytorch-bf16 (license: cc-by-4.0; language: en)
- https://huggingface.co/datasets/kyutai/DailyTalkContiguous
