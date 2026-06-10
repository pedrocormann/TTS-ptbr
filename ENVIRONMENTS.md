# ENVIRONMENTS — qual ambiente pra quê (2026-06-10)

> **Regra de ouro: 1 notebook = 1 runtime fresco do Colab. Nunca instale dois
> stacks de TTS no mesmo runtime** — os pins de `transformers`/`torch` conflitam
> entre si (matriz abaixo). No Mac, um venv por função.

## Mac do Pedro (local, CPU)

| venv | Instala | Usado por |
|---|---|---|
| `.venv-rec` | `pip install -r tools/recording/requirements.txt` | kit de gravação (record/qc/export) |
| `.venv-duplex` | `pip install sounddevice soundfile numpy faster-whisper pocket-tts openai` | **Maya-BR v0 local**: `python -m src.duplex.chat_loop --tts pocket …` (clone de voz exige aceitar o gate em hf.co/kyutai/pocket-tts + `hf auth login`) |

## Colab (1 runtime por notebook)

| Notebook | GPU mínima | Stack (pins críticos) | Conflita com |
|---|---|---|---|
| 01 dataset prep | T4 | faster-whisper 1.1.0, jiwer | — |
| 02-A/B baselines (chatterbox+pocket) | T4 | `chatterbox-tts` (deps pinadas próprias) + `pocket-tts` | seção C (transformers) |
| 02-C / 04 CSM (Unsloth) | T4 | **transformers==4.52.3**, trl==0.22.2 (--no-deps), unsloth, torchcodec | nb03 (4.57.3), nb05 |
| 03 Qwen3-TTS LoRA | **L4/A100 (NÃO T4)** | `qwen-tts` (**transformers==4.57.3**, accelerate==1.12.0 — não atualizar), peft, repo patchado | nb02-C/04 (4.52.3) |
| 05 Moshi LoRA (spine) | **A100-80 / G4-96** | `pip -e moshi-finetune` (torch≥2.6, sphn) | nb04 (stack CSM) |
| eval TTSDS2 | T4+ | `ttsds` (baixa modelos-sonda na 1ª run) | rodar isolado de preferência |
| synth qwen3 (dado sintético) | L4 | `qwen-tts` | mesmo runtime do nb03 OK |

## Secrets do Colab (Runtime → Secrets, uma vez)

- `GH_TOKEN` — clone do repo privado
- `HF_TOKEN` — HuggingFace (gates aceitos: sesame/csm-1b ✅, pyannote ✅,
  kyutai/pocket-tts p/ clone, Llama-3.2-1B pendente Meta)
- (opcional) `GEMINI_KEY`/chave do LLM pro chat_loop

## Drive (layout esperado pelos notebooks)

```
MyDrive/TTS-ptbr-data/
  raw/                 sessões do kit de gravação (upload do Mac)
  dataset_v1/          export final (nb01 espelha)
  ref_pedro.wav        referência ~7-10s p/ nb02
  stereo_ptbr/         wavs estéreo p/ nb05 (pipeline sintético/diálogos)
  checkpoints/         adapters salvos (nb03/nb04)
  runs/                run_dir do moshi-finetune (nb05; checkpoints sobrevivem à sessão)
```

## Histórico de conflitos conhecidos (não repetir)

- mai/2026: moshi-finetune (torch 2.6 + sphn 0.1.12) × CSM original (torch 2.4 +
  moshi 0.2.2) quebraram no mesmo venv → venvs/runtimes separados SEMPRE.
- jun/2026: qwen-tts pina transformers 4.57.3; Unsloth/CSM pina 4.52.3 →
  incompatíveis no mesmo runtime.
- flash-attn: só Ampere+ (L4/A100); no T4 usar `attn_implementation="sdpa"`.
