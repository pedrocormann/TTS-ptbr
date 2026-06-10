#!/usr/bin/env python3
"""Monta planos de sessão de gravação a partir do conteúdo em content/.

Cada sessão é um JSONL ordenado de itens que o record.py apresenta um a um.
Tipos de sessão:
  core      — frases foneticamente balanceadas (seleção gulosa por cobertura)
  emotion   — blocos por estilo emocional (cartões de direção + frases do estilo)
  accent    — blocos por sub-variação carioca
  conversa  — monólogos improvisados, diálogos e paralinguísticos
  mix       — sessão equilibrada com um pouco de cada (default)

Uso:
  python tools/recording/build_session.py --kind mix --minutes 45 --out sessions/ses01.jsonl
  python tools/recording/build_session.py --kind core --all --out sessions/core_full.jsonl
  python tools/recording/build_session.py --coverage   # só relatório de cobertura
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import g2p_pt  # noqa: E402

HERE = Path(__file__).parent
CONTENT = HERE / "content"

# estimativa de duração por item (segundos, fala + respiro + conferência)
EST = {"curta": 8, "media": 12, "longa": 18, "emotion": 14, "accent": 12,
       "monologo": 110, "dialogo": 90, "paralinguistico": 10}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def greedy_coverage_order(sentences: list[dict]) -> list[dict]:
    """Ordena frases para maximizar cobertura fonética incremental."""
    remaining = list(sentences)
    chosen: list[dict] = []
    seen: set[str] = set()
    phone_cache = {s["id"]: set(g2p_pt.text_to_phones(s["text"])) for s in sentences}
    while remaining:
        best = max(remaining, key=lambda s: len(phone_cache[s["id"]] - seen))
        gain = len(phone_cache[best["id"]] - seen)
        if gain == 0:
            # cobertura saturou: o resto vai em ordem aleatória estável
            random.Random(7).shuffle(remaining)
            chosen.extend(remaining)
            break
        chosen.append(best)
        seen |= phone_cache[best["id"]]
        remaining.remove(best)
    return chosen


def items_core(limit_s: float | None) -> list[dict]:
    sents = load_jsonl(CONTENT / "sentences_core.jsonl")
    ordered = greedy_coverage_order(sents)
    items, t = [], 0.0
    for s in ordered:
        dur = EST.get(s.get("len", "media"), 12)
        if limit_s and t + dur > limit_s:
            break
        items.append({
            "id": s["id"], "kind": "sentenca", "text": s["text"],
            "style": "neutro", "intensity": "media", "accent": "carioca-medio",
            "direction": "Leitura natural, como se explicasse pra um amigo. Sem voz de locutor.",
        })
        t += dur
    return items


def items_emotion(limit_s: float | None, styles: list[str] | None = None) -> list[dict]:
    cards = load_jsonl(CONTENT / "emotion_cards.jsonl")
    anchors = load_jsonl(CONTENT / "anchors.jsonl")
    items, t = [], 0.0
    for card in cards:
        if styles and card["style"] not in styles:
            continue
        # bloco 1 — frases-ÂNCORA: as MESMAS frases neutras em todos os estilos
        # (pares mínimos de estilo; ouro p/ treino e eval de controle — protocolo EARS)
        for a in anchors:
            dur = EST["emotion"]
            if limit_s and t + dur > limit_s:
                return items
            items.append({
                "id": f"emo_{card['style']}_anchor_{a['id']}",
                "kind": "emocao", "text": a["text"], "style": card["style"],
                "intensity": "media", "accent": "carioca-medio",
                "direction": card["direction"] + " (Frase-âncora: o TEXTO é neutro de "
                             "propósito — toda a emoção vem da sua entrega.)",
            })
            t += dur
        # bloco 2 — frases congruentes com a emoção, nas 3 intensidades
        for intensity in card.get("intensities", ["media"]):
            for k, sent in enumerate(card["sentences"]):
                dur = EST["emotion"]
                if limit_s and t + dur > limit_s:
                    return items
                items.append({
                    "id": f"emo_{card['style']}_{intensity}_{k:02d}",
                    "kind": "emocao", "text": sent, "style": card["style"],
                    "intensity": intensity, "accent": "carioca-medio",
                    "direction": card["direction"] + f" Intensidade: {intensity}.",
                })
                t += dur
        # bloco 3 — monólogo improvisado no estilo (protocolo Expresso/EARS freeform)
        dur = EST["monologo"]
        if limit_s and t + dur > limit_s:
            return items
        items.append({
            "id": f"emo_{card['style']}_freeform",
            "kind": "monologo", "text": f"[IMPROVISO 2–3min no estilo {card['style']}] "
                                        "Conte uma situação sua, real ou inventada, nesse estado emocional.",
            "style": card["style"], "intensity": "media", "accent": "carioca-medio",
            "direction": card["direction"],
        })
        t += dur
    return items


def items_accent(limit_s: float | None, accents: list[str] | None = None) -> list[dict]:
    cards = load_jsonl(CONTENT / "accent_cards.jsonl")
    items, t = [], 0.0
    for card in cards:
        if accents and card["accent"] not in accents:
            continue
        for k, sent in enumerate(card["sentences"]):
            dur = EST["accent"]
            if limit_s and t + dur > limit_s:
                return items
            items.append({
                "id": f"acc_{card['accent']}_{k:02d}",
                "kind": "sotaque", "text": sent, "style": "neutro",
                "intensity": "media", "accent": card["accent"],
                "direction": card["direction"],
            })
            t += dur
    return items


def items_conversa(limit_s: float | None) -> list[dict]:
    prompts = load_jsonl(CONTENT / "conversational_prompts.jsonl")
    items, t = [], 0.0
    for k, p in enumerate(prompts):
        kind = p["kind"]
        dur = EST.get(kind, 60)
        if limit_s and t + dur > limit_s:
            break
        if kind == "monologo":
            items.append({
                "id": f"mono_{k:02d}", "kind": "monologo",
                "text": f"[IMPROVISO 60–90s] Tema: {p['topic']}",
                "style": "conversa", "intensity": "media", "accent": "carioca-medio",
                "direction": p.get("direction", "Fala espontânea, como num papo de verdade."),
            })
        elif kind == "dialogo":
            turns = "\n".join(f"  {tu['who']}: {tu['text']}" for tu in p["turns"])
            items.append({
                "id": f"dial_{k:02d}", "kind": "dialogo",
                "text": f"[DIÁLOGO — {p['title']}]\n{turns}",
                "style": "conversa", "intensity": "media", "accent": "carioca-medio",
                "direction": "Leia os DOIS papéis com vozes/energias levemente distintas, "
                             "ou grave com parceiro. Mantenha backchannels e risadas.",
            })
        else:
            items.append({
                "id": f"para_{k:02d}", "kind": "paralinguistico",
                "text": f"[{p['item']}] — 3 a 5 repetições variadas",
                "style": "paralinguistico", "intensity": "media", "accent": "carioca-medio",
                "direction": p.get("direction", ""),
            })
        t += dur
    return items


def build(kind: str, minutes: float | None, args) -> list[dict]:
    limit = minutes * 60 if minutes else None
    if kind == "core":
        return items_core(limit)
    if kind == "emotion":
        return items_emotion(limit, args.styles)
    if kind == "accent":
        return items_accent(limit, args.accents)
    if kind == "conversa":
        return items_conversa(limit)
    if kind == "mix":
        # 40% core / 25% emoção / 15% sotaque / 20% conversa
        if limit is None:
            limit = 45 * 60
        parts = [
            items_core(limit * 0.40),
            items_emotion(limit * 0.25, None),
            items_accent(limit * 0.15, None),
            items_conversa(limit * 0.20),
        ]
        return [it for part in parts for it in part]
    raise SystemExit(f"kind desconhecido: {kind}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", default="mix", choices=["core", "emotion", "accent", "conversa", "mix"])
    ap.add_argument("--minutes", type=float, default=45, help="duração-alvo da sessão (min)")
    ap.add_argument("--all", action="store_true", help="ignora --minutes, inclui tudo")
    ap.add_argument("--styles", nargs="*", default=None, help="filtra estilos emocionais")
    ap.add_argument("--accents", nargs="*", default=None, help="filtra sub-sotaques")
    ap.add_argument("--out", default=None, help="arquivo de saída .jsonl")
    ap.add_argument("--coverage", action="store_true", help="só imprime cobertura fonética do core")
    args = ap.parse_args()

    if args.coverage:
        sents = load_jsonl(CONTENT / "sentences_core.jsonl")
        cov = g2p_pt.coverage([s["text"] for s in sents])
        print(json.dumps({k: cov[k] for k in ("total_phones", "distinct", "target_size", "missing", "rare")},
                         ensure_ascii=False, indent=2))
        return

    items = build(args.kind, None if args.all else args.minutes, args)
    # dígitos só importam em texto LIDO (instruções de improviso podem ter números)
    scripted = ("sentenca", "emocao", "sotaque", "dialogo")
    digit_warn = [it["id"] for it in items
                  if it["kind"] in scripted and g2p_pt.has_digits(it.get("text", ""))]
    if digit_warn:
        print(f"⚠️  itens com dígitos (escreva por extenso): {digit_warn}", file=sys.stderr)

    out = Path(args.out) if args.out else HERE / "sessions" / f"{args.kind}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    est = sum(EST.get(it["kind"] if it["kind"] in EST else
                      ("monologo" if it["kind"] == "monologo" else "media"), 12) for it in items)
    print(f"✅ {len(items)} itens → {out}  (estimativa {est/60:.0f} min de sessão)")


if __name__ == "__main__":
    main()
