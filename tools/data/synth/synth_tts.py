"""
Dialogues jsonl -> per-turn wavs, using a COMMERCIAL-SAFE TTS only.

Engines (REPLAN 2026-06-10 — preferir os dois primeiros; Kokoro = fallback leve):
  qwen3            Qwen3-TTS CustomVoice (Apache-2.0, pt nativo) — vozes preset +
                   `instruct` em linguagem natural POR TURNO (emoção do diálogo
                   entra na síntese — nenhum outro engine faz isso).
  chatterbox-ptbr  Chatterbox-Multilingual-pt-br (MIT, pack pt-BR dedicado) —
                   clone por referência; o multilingual amplo soa pt-PT (#281).
  chatterbox       Chatterbox multilingual genérico (MIT) — legado.
  kokoro           Kokoro (Apache) lang 'p' — leve/CPU, sem emoção, qualidade média.
NEVER XTTS/F5/Fish here — CC-BY-NC/CPML poisons commercial output (dossier 21).
Agent A = LEFT/Moshi voice, Agent B = RIGHT/user voice.

  # qwen3 (GPU; vozes preset do CustomVoice; emocao via instruct automático):
  python tools/data/synth/synth_tts.py --dialogues synth_dialogues.jsonl \
      --out-dir synth_turns --engine qwen3 --voice-a Ethan --voice-b Chelsie
  # chatterbox-ptbr (GPU; voice-a/b = wavs de referência ~7-10s):
  python tools/data/synth/synth_tts.py --dialogues synth_dialogues.jsonl \
      --out-dir synth_turns --engine chatterbox-ptbr --voice-a refA.wav --voice-b refB.wav

APIs verificadas 2026-06-10 (research/dossier-2026-06/70-api-recipes.md).
"""
import argparse, json, os

# instrução de estilo por emoção do diálogo (qwen3 instruct)
EMOTION_INSTRUCT = {
    "neutro": None,
    "caloroso": "fale com tom caloroso e acolhedor",
    "animado": "fale com muita animação e energia",
    "empatico": "fale com empatia, tom suave e compreensivo",
    "triste": "fale com tom triste e desanimado",
    "surpreso": "fale com surpresa genuína",
    "irritado": "fale irritado, com impaciência contida",
    "sussurro": "fale sussurrando",
}


def synth_kokoro(turns, out_dir, did, voice_a, voice_b, sr=24000):
    from kokoro import KPipeline  # lang 'p' = Brazilian Portuguese
    import soundfile as sf
    import numpy as np
    pipe = KPipeline(lang_code="p")
    man = []
    for i, t in enumerate(turns):
        voice = voice_a if t["spk"] == "A" else voice_b
        chunks = [a for _, _, a in pipe(t["text"], voice=voice)]
        audio = np.concatenate(chunks) if chunks else np.zeros(1, "float32")
        fn = f"{did}_t{i:02d}_{t['spk']}.wav"
        sf.write(os.path.join(out_dir, fn), audio, sr)
        man.append({"file": fn, "spk": t["spk"], "text": t["text"],
                    "emotion": t["emotion"], "intensity": t["intensity"]})
    return man


_CHATTERBOX = {"model": None}


def _load_chatterbox_ptbr():
    """Monta o pack pt-BR (repo separado; from_pretrained tem REPO_ID hardcoded)."""
    from huggingface_hub import hf_hub_download
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    import pathlib, shutil
    d = pathlib.Path(os.environ.get("CHATTERBOX_PTBR_DIR", "ckpt_chatterbox_ptbr"))
    d.mkdir(exist_ok=True)
    for f in ["t3_pt_br.safetensors", "s3gen_v3.pt", "grapheme_mtl_merged_expanded_v1.json"]:
        if not (d / f).exists():
            shutil.copy(hf_hub_download("ResembleAI/Chatterbox-Multilingual-pt-br", f), d / f)
    for f in ["ve.pt", "conds.pt", "Cangjie5_TC.json"]:  # voice encoder vem do repo base
        if not (d / f).exists():
            shutil.copy(hf_hub_download("ResembleAI/chatterbox", f), d / f)
    if (d / "s3gen_v3.pt").exists() and not (d / "s3gen.pt").exists():
        (d / "s3gen_v3.pt").rename(d / "s3gen.pt")  # from_local carrega 's3gen.pt'
    return ChatterboxMultilingualTTS.from_local(d, device="cuda",
                                                t3_model="t3_pt_br.safetensors")


def synth_chatterbox(turns, out_dir, did, voice_a, voice_b, sr=24000, ptbr=False):
    import soundfile as sf
    if _CHATTERBOX["model"] is None:
        if ptbr:
            _CHATTERBOX["model"] = _load_chatterbox_ptbr()
        else:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            _CHATTERBOX["model"] = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    model = _CHATTERBOX["model"]
    man = []
    for i, t in enumerate(turns):
        ref = voice_a if t["spk"] == "A" else voice_b
        # emoção: exaggeration sobe p/ estilos fortes (recomendação do README)
        strong = t.get("emotion") in ("animado", "irritado", "surpreso")
        wav = model.generate(t["text"], language_id="pt", audio_prompt_path=ref,
                             exaggeration=0.7 if strong else 0.5,
                             cfg_weight=0.3 if strong else 0.5)
        fn = f"{did}_t{i:02d}_{t['spk']}.wav"
        sf.write(os.path.join(out_dir, fn), wav.squeeze(0).cpu().numpy(), model.sr)
        man.append({"file": fn, "spk": t["spk"], "text": t["text"],
                    "emotion": t["emotion"], "intensity": t["intensity"]})
    return man


_QWEN3 = {"model": None}


def synth_qwen3(turns, out_dir, did, voice_a, voice_b, sr=24000):
    """Qwen3-TTS CustomVoice: vozes preset (--voice-a/b = nome do speaker) +
    instruct de emoção por turno. transformers fica pinado pelo qwen-tts."""
    import soundfile as sf
    import torch
    if _QWEN3["model"] is None:
        from qwen_tts import Qwen3TTSModel
        _QWEN3["model"] = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", device_map="cuda:0",
            dtype=torch.bfloat16, attn_implementation="sdpa")
    model = _QWEN3["model"]
    man = []
    for i, t in enumerate(turns):
        speaker = voice_a if t["spk"] == "A" else voice_b
        instruct = EMOTION_INSTRUCT.get(t.get("emotion"))
        kwargs = dict(text=t["text"], language="Portuguese", speaker=speaker)
        if instruct:
            kwargs["instruct"] = instruct
        wavs, out_sr = model.generate_custom_voice(**kwargs)
        wav = wavs[0] if isinstance(wavs, (list, tuple)) else wavs
        if hasattr(wav, "cpu"):
            wav = wav.cpu().numpy()
        fn = f"{did}_t{i:02d}_{t['spk']}.wav"
        sf.write(os.path.join(out_dir, fn), wav, out_sr)
        man.append({"file": fn, "spk": t["spk"], "text": t["text"],
                    "emotion": t["emotion"], "intensity": t["intensity"]})
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dialogues", required=True)
    ap.add_argument("--out-dir", default="synth_turns")
    ap.add_argument("--engine", default="kokoro",
                    choices=["qwen3", "chatterbox-ptbr", "chatterbox", "kokoro"])
    ap.add_argument("--voice-a", default="pm_alex",
                    help="kokoro: pm_* | chatterbox*: ref wav | qwen3: speaker preset (ex. Ethan)")
    ap.add_argument("--voice-b", default="pf_dora",
                    help="kokoro: pf_* | chatterbox*: ref wav | qwen3: speaker preset (ex. Chelsie)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    def fn(turns, out_dir, did, va, vb):
        if a.engine == "kokoro":
            return synth_kokoro(turns, out_dir, did, va, vb)
        if a.engine == "qwen3":
            return synth_qwen3(turns, out_dir, did, va, vb)
        return synth_chatterbox(turns, out_dir, did, va, vb,
                                ptbr=(a.engine == "chatterbox-ptbr"))

    rows = [json.loads(l) for l in open(a.dialogues, encoding="utf-8") if l.strip()]
    idx = {}
    for d in rows:
        man = fn(d["turns"], a.out_dir, d["id"], a.voice_a, a.voice_b)
        idx[d["id"]] = {"scenario": d["scenario"], "accent": d["accent"],
                        "turns": man}
    with open(os.path.join(a.out_dir, "_turns_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print(f"{len(rows)} dialogues -> per-turn wavs in {a.out_dir} "
          f"(engine={a.engine}). next: compose_stereo.py")


if __name__ == "__main__":
    main()
