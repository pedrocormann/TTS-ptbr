#!/usr/bin/env python3
"""Gera amostras de comparação com o adapter LoRA do csm-mlx (pós-finetune).

  python tools/recording/gen_csmmlx_samples.py \
      --adapter data/csmmlx_runs/v1/<ckpt>.safetensors --out data/testes_maya
"""
from __future__ import annotations

import argparse
import pathlib
import time

import numpy as np
import soundfile as sf

SENTS = [
    ("ft1_neutro", "E aí, tudo certo? Esse aqui sou eu depois do primeiro finetune, treinado em quarenta e oito minutos da minha própria voz."),
    ("ft2_carioca", "Mas que isso, são dez biscoitos e duas águas por trinta reais? Tá caro demais, vou nessa."),
    ("ft3_animado", "Caraca, funcionou! Agora é gravar mais horas, botar emoção, e subir essa escada degrau por degrau!"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", default="data/testes_maya")
    ap.add_argument("--ref", default="data/raw/elevenlabs2024/segments/found_08_seg019.wav")
    ap.add_argument("--ref-text", default="Então é um projeto que vai ser muito incrível, também super complexo. A gente vai precisar de vários meses de desenvolvimento, vai precisar de vários meses de pesquisa.")
    ap.add_argument("--no-context", action="store_true",
                    help="gera SEM âncora (testa se a voz ficou no peso)")
    args = ap.parse_args()

    from csm_mlx import CSM, csm_1b, generate, Segment, load_adapters
    from huggingface_hub import hf_hub_download
    from mlx_lm.sample_utils import make_sampler

    csm = CSM(csm_1b())
    csm.load_weights(hf_hub_download(repo_id="senstella/csm-1b-mlx",
                                     filename="ckpt.safetensors"))
    load_adapters(csm, args.adapter)
    print(f"adapter carregado: {args.adapter}")

    ctx = [] if args.no_context else [
        Segment(speaker=0, text=args.ref_text, audio_path=pathlib.Path(args.ref))]
    sampler = make_sampler(temp=0.8, top_k=50)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    suffix = "_noctx" if args.no_context else ""
    for name, text in SENTS:
        t0 = time.time()
        audio = generate(csm, text=text, speaker=0, context=ctx,
                         max_audio_length_ms=15_000, sampler=sampler)
        arr = np.array(audio, dtype=np.float32)
        sf.write(out / f"{name}{suffix}.wav", arr, 24000)
        print(f"  {name}{suffix}: {len(arr)/24000:.1f}s em {time.time()-t0:.0f}s")
    print(f"✅ amostras em {out}")


if __name__ == "__main__":
    main()
