"""
Expand seed_dialogues.jsonl into many pt-BR 2-party dialogues — DETERMINISTIC
slot-filling, NO API/model needed (so it runs anywhere, today, zero license/auth).
Optional --llm hook documented for later scale (needs a key — parked).

Schema (in & out, one JSON/line):
  {"id","scenario","accent","turns":[{"spk":"A|B","emotion","intensity","text"}]}
  A = agent (Moshi role → LEFT channel). B = human (user role → RIGHT channel).

  python tools/data/synth/gen_dialogues.py --seeds tools/data/synth/seed_dialogues.jsonl \
      --out synth_dialogues.jsonl --variants 6
"""
import argparse, json, re

# Slot pools — substituted into {slot} markers if present; also light surface
# variation so expanded copies aren't byte-identical (helps the LM see variety).
POOLS = {
    "nome":   ["Joana Ribeiro", "Carlos Menezes", "Patrícia Lima", "Rafael Souza",
               "Mariclea Santos", "Bruno Carvalho", "Aline Tavares", "Diego Rocha"],
    "produto":["o pedido", "a encomenda", "o ingresso", "a assinatura",
               "a reserva", "o equipamento"],
    "lugar":  ["a exposição", "o museu", "o evento", "a feira", "a mostra",
               "a ativação"],
    "valor":  ["cinquenta e oito e noventa", "cento e vinte reais",
               "trinta e nove e noventa", "duzentos e dez reais"],
}
# Gentle paraphrase swaps applied per-variant (idx-seeded) for surface variety.
PARAPHRASE = [
    (r"\bbeleza\b", "tranquilo"), (r"\bda hora\b", "massa"),
    (r"\bvaleu\b", "obrigado"), (r"\btá bom\b", "tudo certo"),
    (r"\bpoxa\b", "puxa"), (r"\bcaraca\b", "nossa"),
]


def vary(text: str, idx: int) -> str:
    # deterministic: variant 0 = original; >0 applies idx-many paraphrase swaps
    out = text
    for k in range(idx % (len(PARAPHRASE) + 1)):
        pat, rep = PARAPHRASE[k]
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    # fill any {slot} markers deterministically by idx
    for slot, pool in POOLS.items():
        if "{" + slot + "}" in out:
            out = out.replace("{" + slot + "}", pool[idx % len(pool)])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", type=int, default=6,
                    help="copies per seed (variant 0 = verbatim)")
    ap.add_argument("--llm", default=None,
                    help="[parked] optional 'openai'/'gemini' to paraphrase via API "
                         "for real scale — needs a key (PARKING-LOT). Not required.")
    a = ap.parse_args()

    seeds = [json.loads(l) for l in open(a.seeds, encoding="utf-8") if l.strip()]
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for s in seeds:
            for v in range(max(1, a.variants)):
                d = {
                    "id": f"{s['id']}-v{v}",
                    "scenario": s["scenario"],
                    "accent": s["accent"],
                    "turns": [
                        {"spk": t["spk"], "emotion": t["emotion"],
                         "intensity": t["intensity"], "text": vary(t["text"], v)}
                        for t in s["turns"]
                    ],
                }
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
                n += 1
    if a.llm:
        print(f"[note] --llm '{a.llm}' is a parked hook; needs an API key "
              f"(research/PARKING-LOT.md). Ran deterministic expansion instead.")
    print(f"{len(seeds)} seeds x {a.variants} -> {n} dialogues -> {a.out}\n"
          f"next: synth_tts.py (Kokoro/Chatterbox) -> compose_stereo.py")


if __name__ == "__main__":
    main()
