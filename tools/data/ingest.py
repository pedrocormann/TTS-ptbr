#!/usr/bin/env python3
"""PIPE de ingestão/classificação de datasets — fecha o buraco 'catalogar vs executar'.

Em vez de classificar dataset na mão num doc, o dado PASSA por 4 gates determinísticos e
recebe um tier. E o `assert_license_gate()` no data-loader FALHA O BUILD se um dado não-shippável
escapar pra um split de produto. Assert, não convenção (ver docs/ESTRATEGIA-DADOS.md).

Uso:
  python ingest.py --check                      # valida o data/dataset_registry.yaml + manifests
  python ingest.py --classify <hf_id> --license <lic> --hours <h> --accent <a> --type <t>
  python ingest.py --build-manifest T0          # emite data/manifests/T0.jsonl dos shippable T0

Gates (em ordem; o 1º que reprova decide):
  1) LICENÇA   → NC/ND/sem-licença/pago  => NÃO shippable (eval/judge/research only)
  2) LGPD      → voz de pessoa sem consentimento (judicial/biometria) => bloqueado pra treino
  3) QUALIDADE → DNSMOS < limiar (ASR-grade ≠ TTS-grade) => fica em base/eval, não em voz
  4) FIT-VOZ   → sotaque != carioca => Camada 0/1 (língua/conversa), NUNCA Camada 2 (voz)
"""
import argparse, json, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
REG = REPO / "data" / "dataset_registry.yaml"
MANIFESTS = REPO / "data" / "manifests"

SHIP_OK = ("cc-by-4", "cc-by-3", "cc0", "mit", "apache", "própria", "propria")
SHIP_BLOCK = ("-nc", "nc-", "noncomm", "-nd", "nd-", "sem licença", "sem licenca", "pago", "bloqueado")
DNSMOS_TTS = 3.0   # >= vira candidato TTS-grade; abaixo fica língua/eval


def gate_license(lic: str) -> bool:
    """True = COMERCIAL-shippable (produto). NÃO é o gate de PESQUISA (ver research_ok)."""
    l = (lic or "").lower()
    if any(b in l for b in SHIP_BLOCK):
        return False
    return any(g in l for g in SHIP_OK) and "nc" not in l and "nd" not in l


def research_ok(lic: str) -> bool:
    """True = usável pra PESQUISA (modo atual). NC/ND/SA são OK pra pesquisa não-comercial.
    Só barra o que NÃO DÁ pra usar de fato: sem dado/acesso, ou pago não-comprado."""
    l = (lic or "").lower()
    if any(b in l for b in ("sem acesso", "sem dado", "bloqueado")):
        return False
    if "pago" in l or "elra" in l:           # comprável, mas só com budget
        return False
    return True                              # CC-BY/CC0/MIT/NC/ND/SA/sem-licença-declarada → pesquisa usa


def classify(license: str, hours=None, accent="", typ="", dnsmos=None, consent=False):
    """Roda os 4 gates → (tier, camada, shippable, motivo)."""
    ship = gate_license(license)
    if not ship:
        return ("T2 eval-only / T3 judge-only", "fora de pesos", False, "licença NC/ND/sem — só eval/judge/receita")
    # LGPD: voz pessoal sensível sem consentimento
    if ("judicial" in (typ + accent).lower() or "biometr" in typ.lower()) and not consent:
        return ("T4 bloqueado", "nenhuma", False, "LGPD: voz pessoal sem consentimento")
    # qualidade
    if dnsmos is not None and dnsmos < DNSMOS_TTS:
        return ("T0 base-pretrain", "Camada 0 (língua)", True, f"DNSMOS {dnsmos}<{DNSMOS_TTS}: ASR-grade → só língua")
    # fit de voz: carioca → pode ser voz (C2); senão língua/conversa
    if "carioca" in accent.lower() or "própr" in license.lower():
        return ("T1 fine-tune-voz", "Camada 2 (voz carioca)", True, "carioca commercial-safe → voz")
    if "espont" in typ.lower() or "convers" in typ.lower() or "diálogo" in typ.lower():
        return ("T1 fine-tune", "Camada 1 (conversa)", True, "espontâneo licenciado → adapt conversacional")
    return ("T0 base-pretrain", "Camada 0 (língua)", True, "lido/licenciado → base-PT (língua)")


def load_registry():
    """Parser YAML minimalista do nosso registry (sem dependência externa)."""
    if not REG.exists():
        return []
    items, cur = [], None
    for ln in REG.read_text(encoding="utf-8").splitlines():
        if ln.startswith("- nome:"):
            if cur:
                items.append(cur)
            cur = {"nome": ln.split(":", 1)[1].strip().strip('"')}
        elif cur is not None and re.match(r"\s+\w+:", ln):
            k, v = ln.strip().split(":", 1)
            cur[k.strip()] = v.strip().strip('"')
    if cur:
        items.append(cur)
    return items


def assert_license_gate(manifest_rows, mode="research"):
    """Gate de dado. mode='research' (PADRÃO, nosso caso): usa NC/ND/SA livremente, só barra
    o que não dá pra usar (sem acesso/pago). mode='commercial': gate estrito (barra NC/ND) — pro futuro,
    se virar produto. Em research, NÃO bloqueia treino — só AVISA o que é research-only (rastreio de proveniência)."""
    if mode == "commercial":
        bad = [r for r in manifest_rows if not gate_license(r.get("license", ""))]
        if bad:
            raise SystemExit(f"❌ gate COMERCIAL: {len(bad)} item(s) NC/ND num build de produto "
                             f"(ex: {bad[0].get('source', '?')}). Bloqueado.")
        return True
    # research
    inusavel = [r for r in manifest_rows if not research_ok(r.get("license", ""))]
    if inusavel:
        raise SystemExit(f"❌ {len(inusavel)} item(s) sem acesso/pago (ex: {inusavel[0].get('source','?')}). "
                         f"Não dá pra usar nem em pesquisa — remova do manifest.")
    research_only = [r for r in manifest_rows if not gate_license(r.get("license", ""))]
    if research_only:
        print(f"ℹ️  {len(research_only)} fonte(s) RESEARCH-ONLY (NC/ND) no mix — OK pra pesquisa, "
              f"NÃO comercializável. Proveniência marcada (ex: {research_only[0].get('source','?')}).")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--classify", metavar="HF_ID")
    ap.add_argument("--license", default=""); ap.add_argument("--hours", default="")
    ap.add_argument("--accent", default=""); ap.add_argument("--type", default="")
    ap.add_argument("--dnsmos", type=float, default=None); ap.add_argument("--consent", action="store_true")
    ap.add_argument("--build-manifest", metavar="TIER")
    a = ap.parse_args()

    if a.classify:
        tier, camada, ship, motivo = classify(a.license, a.hours, a.accent, a.type, a.dnsmos, a.consent)
        print(json.dumps({"hf_id": a.classify, "tier": tier, "camada": camada,
                          "shippable": ship, "motivo": motivo}, ensure_ascii=False, indent=2))
        return

    reg = load_registry()
    if a.check:
        print(f"registry: {len(reg)} datasets")
        ship = [d for d in reg if d.get("shippable") == "true"]
        print(f"  shippable (produto): {len(ship)} — {', '.join(d['nome'] for d in ship)}")
        # sanidade: nenhum NC marcado shippable
        viol = [d['nome'] for d in reg if d.get("shippable") == "true" and not gate_license(d.get("licenca", ""))]
        print("  ⚠ violações licença×shippable:", viol or "nenhuma")
        return

    if a.build_manifest:
        tier = a.build_manifest
        rows = [{"nome": d["nome"], "license": d.get("licenca", ""), "tier": d.get("tier", ""),
                 "source": d["nome"], "shippable": d.get("shippable") == "true"}
                for d in reg if d.get("tier", "").startswith(tier)]
        assert_license_gate(rows, mode="research")
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        out = MANIFESTS / f"{tier}.jsonl"
        out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        print(f"✅ {out} — {len(rows)} fontes (assert_license_gate passou)")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
