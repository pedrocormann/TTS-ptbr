"""
Speaker similarity (fidelidade de clone) — cosseno entre embeddings de locutor.

Backend default: WavLM-base-plus-sv (microsoft, HF) — o mesmo usado em Seed-TTS-eval
e na maioria dos papers 2025/26. Fallback: resemblyzer (CPU leve, menos preciso).

Uso (Colab/GPU ou CPU):
  python -m eval.speaker_sim --ref-dir ref_pedro/ --gen-dir gen/
  python -m eval.speaker_sim --ref-dir ref_pedro/ --gen-dir gen/ --backend resemblyzer

Saída: _spksim_results.jsonl em gen/ + média no stdout.
Leitura: >0.70 = mesma voz claramente; 0.60–0.70 = parecido; <0.50 = clone falhou.
(Calibração exata depende do backend — compare sempre dentro do MESMO backend.)
"""
import argparse
import json
from pathlib import Path


def _load_audio_16k(path):
    import librosa
    wav, _ = librosa.load(path, sr=16000, mono=True)
    return wav


def embed_wavlm(paths, device):
    import torch
    from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector
    name = "microsoft/wavlm-base-plus-sv"
    fe = Wav2Vec2FeatureExtractor.from_pretrained(name)
    model = WavLMForXVector.from_pretrained(name).to(device).eval()
    embs = []
    with torch.no_grad():
        for p in paths:
            wav = _load_audio_16k(p)
            inputs = fe(wav, sampling_rate=16000, return_tensors="pt").to(device)
            e = model(**inputs).embeddings
            embs.append(torch.nn.functional.normalize(e, dim=-1).squeeze(0).cpu())
    return embs


def embed_resemblyzer(paths, _device):
    import numpy as np
    import torch
    from resemblyzer import VoiceEncoder, preprocess_wav
    enc = VoiceEncoder()
    return [torch.from_numpy(np.asarray(enc.embed_utterance(preprocess_wav(p))))
            for p in paths]


def run(ref_dir: str, gen_dir: str, backend: str = "wavlm", ext: str = "wav"):
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    refs = sorted(Path(ref_dir).rglob(f"*.{ext}"))
    gens = sorted(Path(gen_dir).rglob(f"*.{ext}"))
    if not refs or not gens:
        raise SystemExit(f"sem áudio: refs={len(refs)} gens={len(gens)}")

    embed = embed_wavlm if backend == "wavlm" else embed_resemblyzer
    ref_embs = embed(refs, dev)
    ref_centroid = torch.stack(ref_embs).mean(0)
    ref_centroid = ref_centroid / ref_centroid.norm()

    out = Path(gen_dir) / "_spksim_results.jsonl"
    tot = 0.0
    gen_embs = embed(gens, dev)
    with open(out, "w", encoding="utf-8") as f:
        for p, e in zip(gens, gen_embs):
            e = e / e.norm()
            cos = float(torch.dot(ref_centroid, e))
            tot += cos
            f.write(json.dumps({"wav": p.stem, "spk_sim": round(cos, 4)}) + "\n")
        avg = tot / len(gens)
        f.write(f"\nSPK_SIM ({backend}, ref n={len(refs)}): {avg:.4f}\n")
    return avg, len(gens), str(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-dir", required=True, help="áudios de referência da voz real")
    ap.add_argument("--gen-dir", required=True, help="áudios gerados pelo modelo")
    ap.add_argument("--backend", default="wavlm", choices=["wavlm", "resemblyzer"])
    ap.add_argument("--ext", default="wav")
    a = ap.parse_args()
    avg, n, out = run(a.ref_dir, a.gen_dir, a.backend, a.ext)
    print(f"SPK_SIM={avg:.4f} n={n} backend={a.backend} -> {out}")


if __name__ == "__main__":
    main()
