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
  python prep_base_pt.py --sources cml,mls,cv --out data/base_pt/base_pt.jsonl
  python cpt_base_pt.py --manifest data/base_pt/base_pt.jsonl --smoke     # valida caminhos SEM GPU
  python cpt_base_pt.py --manifest data/base_pt/base_pt.jsonl --version v1 --minutes 600
  # → produz runs/base_pt_v1/  → usar como --base-adapter no train_voice.py da voz
  # (--mode commercial: FALHA se houver clipe NC/ND no manifest; default research só marca proveniência)
"""
import argparse, json, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "data"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(REPO / "data/base_pt/base_pt.jsonl"))
    ap.add_argument("--version", default="v1")
    ap.add_argument("--lr", type=float, default=7e-5)          # conservador (gotcha #6)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--minutes", type=int, default=600)        # CPT longo (≠ 60min de voz)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--text-mode", default="normalize")
    ap.add_argument("--mode", default="research", choices=["research", "commercial"],
                    help="research (padrão): NC/ND entra, proveniência marcada · commercial: FALHA se houver NC/ND")
    ap.add_argument("--smoke", action="store_true",
                    help="valida (sem GPU) que os wavs do manifest existem no caminho que o train_voice.py monta")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    man = pathlib.Path(a.manifest)
    if not man.exists():
        sys.exit(f"manifest não existe: {man} — rode prep_base_pt.py primeiro")

    # --- GATE de licença antes de gastar GPU ---
    from ingest import assert_license_gate, gate_license
    rows = [json.loads(l) for l in man.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert_license_gate(rows, mode=a.mode)           # commercial: SystemExit se licença NC/ND
    horas = sum(r.get("dur_s", 0) for r in rows) / 3600
    fontes = sorted({r.get("source", "?") for r in rows})

    def _ship(r):   # usa o bool do manifest; fallback: deriva da licença (manifests antigos)
        s = r.get("shippable")
        return s if isinstance(s, bool) else gate_license(r.get("license", ""))
    n_ship = sum(1 for r in rows if _ship(r))
    n_research = len(rows) - n_ship
    print(f"manifest: {len(rows)} clipes · {horas:.1f}h · fontes {fontes}")
    print(f"  licenças: {n_ship} shippáveis · {n_research} research-only (NC/ND)")
    if a.mode == "commercial" and n_research:
        src = sorted({r.get('source', '?') for r in rows if not _ship(r)})
        sys.exit(f"❌ --mode commercial com {n_research} clipe(s) NÃO-shippáveis no manifest "
                 f"(fontes: {src}). Bloqueado — remova NC/ND ou rode --mode research.")

    # --- SMOKE: valida (sem GPU) o caminho que o train_voice.py monta ---
    # train_voice.py:67 → os.path.join(data_dir, 'segments', basename(audio)); cpt passa data_dir=man.parent
    if a.smoke:
        seg = [man.parent / "segments" / pathlib.Path(r["audio"]).name for r in rows]
        ok = sum(1 for p in seg if p.exists())
        print(f"--smoke: {ok}/{len(seg)} wavs existem em <data-dir>/segments/ (data-dir = {man.parent})")
        for p in seg[:3]:
            print(f"  {'✓' if p.exists() else '✗'} {p}")
        if ok != len(seg):
            sys.exit(f"❌ smoke: {len(seg) - ok} wav(s) ausentes — prep gravou fora de {man.parent / 'segments'}?")
        print("✓ smoke OK — caminhos batem com o que o train_voice.py resolve")
        return

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
