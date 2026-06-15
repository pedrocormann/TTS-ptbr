#!/usr/bin/env bash
# Setup de ambiente do pod RunPod — rodar 1x por pod novo (ou após recriar).
# Mesmos pins do notebook 1b (célula 3). O template "RunPod PyTorch" já traz
# torch/CUDA; aqui só completamos o que falta e tiramos o torchao (peft rejeita).
set -euo pipefail

export HF_HUB_ENABLE_HF_TRANSFER=1

# transformers 4.52.3 = versão EXATA do checkpoint csm-1b (5.x renomeia pesos →
# "embed_audio_tokens MISSING"). bitsandbytes p/ adamw_8bit. faster-whisper p/ eval.
# NÃO pinamos torch — usamos o do template RunPod PyTorch (reinstalar arrastaria CUDA).
# peft/accelerate/bitsandbytes ficam sem pin de propósito (paridade com o notebook 1b,
# que funcionou assim); depois que o pod validar, congelo as versões reais com
# `pip freeze > runpod/requirements.lock.txt` pra reprodutibilidade.
pip install --no-input \
    "transformers==4.52.3" peft accelerate "datasets>=3.4.1,<4.0.0" \
    soundfile jiwer librosa soxr bitsandbytes torchcodec \
    faster-whisper==1.1.0 hf_transfer huggingface_hub

# torchao do ambiente (se vier) é rejeitado pelo peft (quer >0.16) e não usamos.
pip uninstall -y torchao || true

# GUARD: torchcodec tem acoplamento ESTRITO com a versão do torch (datasets>=3.4 usa
# torchcodec pra decodar áudio). Se o pip resolveu um torchcodec incompatível com o
# torch do template, falha AQUI com mensagem clara — não 20min depois no preflight.
python - <<'PY'
import torch
print("torch", torch.__version__)
try:
    import torchcodec
    print("✓ torchcodec", getattr(torchcodec, "__version__", "?"), "importa com este torch")
except Exception as e:
    raise SystemExit(
        f"❌ torchcodec incompatível com torch {torch.__version__}: {e}\n"
        f"   Fix: pinar torchcodec à versão casada com esse torch "
        f"(ex.: pip install 'torchcodec==<v>'). Avisa o Claude com a versão do torch acima.")
PY

echo "✅ setup OK. Confira: python -c 'import transformers; print(transformers.__version__)'  # 4.52.3"
echo "   Não esqueça: export HF_TOKEN=...   (ou setar como env var no template do pod)"
