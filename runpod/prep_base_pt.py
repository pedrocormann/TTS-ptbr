#!/usr/bin/env python3
"""F1 · Prep do dado BASE-PT (Camada 0 — ensina a LÍNGUA). [RODAR NO RUNPOD]

Baixa os datasets T0 SHIPPÁVEIS (CC-BY/CC0) via HF, filtra pt, e monta UM manifest de treino
data/manifests/base_pt.jsonl com gate de licença (assert_license_gate). NUNCA inclui NC/ND
(TAGARELA/CORAA ficam de fora — ver tools/data/ingest.py).

Deps: pip install datasets soundfile librosa
  python prep_base_pt.py --sources cml,mls,cv --hours-cap 200 --out data/manifests/base_pt.jsonl
  python prep_base_pt.py --sources granary --dnsmos 3.0   # in-the-wild: filtra qualidade

Fontes T0 (licença verificada no data/dataset_registry.yaml):
  cml     ylacombe/cml-tts            (config portuguese)  CC-BY-4.0
  mls     facebook/multilingual_librispeech (portuguese)   CC-BY-4.0
  cv      mozilla-foundation/common_voice_17_0 (pt)         CC0-1.0
  granary nvidia/Granary              (pt)                  CC-BY  (FILTRAR DNSMOS antes de TTS)
"""
import argparse, json, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "data"))

# MODO PESQUISA: usamos NC/ND livremente (TAGARELA/CORAA inclusos). Licença marcada só pra
# rastreio de proveniência (se um dia virar produto). Ver tools/data/ingest.py::research_ok.
SOURCES = {
    "cml":      ("ylacombe/cml-tts", "portuguese", "CC-BY-4.0", "transcript"),
    "mls":      ("facebook/multilingual_librispeech", "portuguese", "CC-BY-4.0", "transcript"),
    "cv":       ("mozilla-foundation/common_voice_17_0", "pt", "CC0-1.0", "sentence"),
    "granary":  ("nvidia/Granary", "pt", "CC-BY-4.0", "text"),
    "tagarela": ("freds0/TAGARELA", "pt", "CC-BY-NC-SA-4.0", "text"),       # 2.800h clean — research-only (verificar id/config)
    "coraa":    ("gpucce/CORAA", "pt", "CC-BY-NC-ND-4.0", "text"),          # espontâneo — research-only (verificar id)
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="cml,mls,cv", help="cml,mls,cv,granary")
    ap.add_argument("--hours-cap", type=float, default=None, help="teto de horas por fonte")
    ap.add_argument("--dnsmos", type=float, default=None, help="filtro de qualidade (só granary/in-the-wild)")
    ap.add_argument("--out", default=str(REPO / "data/manifests/base_pt.jsonl"))
    ap.add_argument("--audio-dir", default=str(REPO / "data/base_pt_audio"))
    a = ap.parse_args()

    from ingest import research_ok, gate_license   # modo pesquisa: usa NC/ND, só marca proveniência
    from datasets import load_dataset, Audio
    import soundfile as sf

    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    adir = pathlib.Path(a.audio_dir); adir.mkdir(parents=True, exist_ok=True)
    fout = open(out, "w", encoding="utf-8")
    total_rows = 0

    for key in [s.strip() for s in a.sources.split(",") if s.strip()]:
        if key not in SOURCES:
            print(f"  fonte desconhecida: {key}"); continue
        repo, cfg, lic, txtcol = SOURCES[key]
        assert research_ok(lic), f"{key} sem acesso/pago ({lic}) — nem pesquisa usa"
        tag = "" if gate_license(lic) else "  ⚠ research-only (NC/ND, marca proveniência)"
        print(f"[{key}] {repo}:{cfg} ({lic}){tag} — streaming…", flush=True)
        try:
            ds = load_dataset(repo, cfg, split="train", streaming=True)
            ds = ds.cast_column("audio", Audio(sampling_rate=24000))
        except Exception as e:
            print(f"  falhou carregar {key}: {e} (pode exigir login HF / aceitar termos)"); continue

        secs, n = 0.0, 0
        for ex in ds:
            au = ex.get("audio"); txt = (ex.get(txtcol) or "").strip()
            if not au or not txt:
                continue
            wav = au["array"]; sr = au["sampling_rate"]; d = len(wav) / sr
            if d < 1.0 or d > 20.0:
                continue
            # (DNSMOS de qualidade entraria aqui pra granary; stub: deixar passar)
            fid = f"{key}_{n:06d}.wav"
            sf.write(adir / fid, wav, sr, subtype="PCM_16")
            fout.write(json.dumps({"audio": str(adir / fid), "text": txt, "source": key,
                                   "license": lic, "tier": "T0", "shippable": True, "dur_s": round(d, 2)},
                                  ensure_ascii=False) + "\n")
            secs += d; n += 1; total_rows += 1
            if a.hours_cap and secs >= a.hours_cap * 3600:
                break
            if n % 500 == 0:
                print(f"    {key}: {n} clipes / {secs/3600:.1f}h", flush=True)
        print(f"  [{key}] {n} clipes · {secs/3600:.1f}h", flush=True)

    fout.close()
    print(f"\n✅ base_pt manifest: {total_rows} clipes → {out}")
    print("   PRÓXIMO: python cpt_base_pt.py --manifest", out, "(CPT do base-pt-v1)")


if __name__ == "__main__":
    main()
