#!/usr/bin/env python3
"""F1 · CPT — Continued Pre-Train do base-pt-vN (Camada 0). [RODAR NO RUNPOD/H100]

Pega o manifest do prep_base_pt.py (CML+MLS+CV+Granary, só CC-BY/CC0) e roda um continued
pre-train do CSM-1B pra ENSINAR português brasileiro — o checkpoint base-pt-vN que TODO
finetune de voz depois herda (em vez de cada treino re-aprender pt do zero).

Reaproveita o harness validado runpod/train_voice.py (mesma máquina CSM por jsonl), só com
config de CPT (mais capacidade, mais dado, LR estável). Gate de licença ANTES de treinar:
recusa se algum item do manifest for não-shippável.

RECEITA (gotchas já aprendidos — ver memory project-csm-training-gotchas):
  - lora-r 64 (capacidade pra reaprender a LÍNGUA; voz depois é r16 barato por cima)
  - LR 5e-5..1e-4 (gotcha #6: LR alto + run longo DESTROI o pt → WER 300%; ir conservador)
  - warmup fixo (NÃO time-capped), lr cosine, streaming decode=False, dataloader workers
  - dado: o manifest base_pt (multi-locutor, ruído OK) — NUNCA mistura a voz limpa do Pedro
  - meta: WER de leitura (held-out 50 frases) < 15% mantendo paridade de timbre

Uso (no pod):
  python prep_base_pt.py --sources cml,mls,cv --out data/manifests/base_pt.jsonl
  python cpt_base_pt.py --manifest data/manifests/base_pt.jsonl --version v1 --minutes 600
  # → produz runs/base_pt_v1/  → usar como --base-adapter no train_voice.py da voz
"""
import argparse, json, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "data"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(REPO / "data/manifests/base_pt.jsonl"))
    ap.add_argument("--version", default="v1")
    ap.add_argument("--lr", type=float, default=7e-5)          # conservador (gotcha #6)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--minutes", type=int, default=600)        # CPT longo (≠ 60min de voz)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--text-mode", default="normalize")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    man = pathlib.Path(a.manifest)
    if not man.exists():
        sys.exit(f"manifest não existe: {man} — rode prep_base_pt.py primeiro")

    # --- GATE de licença antes de gastar GPU ---
    from ingest import gate_license, assert_license_gate
    rows = [json.loads(l) for l in man.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert_license_gate(rows, split="prod")          # FALHA se algum NC/não-shippable
    horas = sum(r.get("dur_s", 0) for r in rows) / 3600
    fontes = sorted({r.get("source", "?") for r in rows})
    print(f"manifest: {len(rows)} clipes · {horas:.1f}h · fontes {fontes} · todas shippáveis ✅")

    out = REPO / "runs" / f"base_pt_{a.version}"
    cmd = [sys.executable, str(REPO / "runpod" / "train_voice.py"),
           "--base-adapter", "",                      # CSM cru (estamos CRIANDO a base)
           "--data-dir", str(man.parent), "--data-file", man.name,
           "--out", str(out), "--lr", str(a.lr), "--lora-r", str(a.lora_r),
           "--minutes", str(a.minutes), "--batch", str(a.batch), "--accum", str(a.accum),
           "--text-mode", a.text_mode]
    print("CPT base-pt-" + a.version + ":")
    print("  " + " ".join(cmd))
    if a.dry:
        print("  (dry — não rodou). Tire --dry pra disparar no pod.")
        return
    print(f"  → checkpoint em {out}  (usar como --base-adapter na voz; eval com tools/prosody/prosody_scorecard.py)")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
