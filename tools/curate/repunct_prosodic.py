#!/usr/bin/env python3
"""Re-pontuação PROSÓDICA dos clipes já curados (2ª passada, CPU, resumível).

Mantém as PALAVRAS do texto curado (verdade humana) e re-deriva a PONTUAÇÃO do
próprio áudio (pausas + F0), via tools/text/prosodic_punct.py:
  1) faster-whisper (word_timestamps=True) no wav → palavras ASR com tempo
  2) alinhamento fuzzy curado↔ASR (difflib, monotônico) → timestamps nas palavras curadas
  3) regras prosódicas (pausa/reset/subida F0) → pontuação nova
Saída: prosodic.jsonl {id, text_pros, align_cov, stats} + relatório markdown antes/depois.

Uso:
  python3 tools/curate/repunct_prosodic.py                # 259 clipes do flywheel/pedro
  python3 tools/curate/repunct_prosodic.py --limit 20     # amostra
  python3 tools/curate/repunct_prosodic.py --report-only  # só re-gera o relatório
"""
import argparse, difflib, json, os, re, sys, time, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "text"))
SRC_JSONL = os.path.join(ROOT, "data", "flywheel", "pedro", "train.jsonl")
SEG_DIR   = os.path.join(ROOT, "data", "flywheel", "pedro", "segments")
OUT_JSONL = os.path.join(ROOT, "data", "flywheel", "pedro", "prosodic.jsonl")
REPORT    = os.path.join(ROOT, "eval", "prosodic_punct_report.md")

def norm_tok(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"\W+", "", w)

def align_words(cur_toks, asr_words):
    """Mapeia palavras curadas → timestamps das palavras ASR (monotônico, difflib).
    Palavras sem par recebem tempo interpolado dos vizinhos. Retorna (words, cobertura)."""
    a = [norm_tok(t) for t in cur_toks]
    b = [norm_tok(w["word"]) for w in asr_words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    ts = [None] * len(cur_toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ts[blk.a + k] = (asr_words[blk.b + k]["start"], asr_words[blk.b + k]["end"])
    matched = sum(1 for t in ts if t)
    # interpola buracos
    total_t0 = asr_words[0]["start"] if asr_words else 0.0
    total_t1 = asr_words[-1]["end"] if asr_words else 0.0
    for i, t in enumerate(ts):
        if t is None:
            prev_end = next((ts[j][1] for j in range(i - 1, -1, -1) if ts[j]), total_t0)
            nxt_start = next((ts[j][0] for j in range(i + 1, len(ts)) if ts[j]), total_t1)
            if nxt_start < prev_end: nxt_start = prev_end
            n_gap = sum(1 for j in range(i, len(ts)) if ts[j] is None and not any(ts[k] for k in range(i, j)))
            ts[i] = (prev_end, min(nxt_start, prev_end + max(0.12, (nxt_start - prev_end) / max(1, n_gap))))
    words = [{"word": cur_toks[i], "start": ts[i][0], "end": ts[i][1]} for i in range(len(cur_toks))]
    return words, matched / max(1, len(cur_toks))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--emit-dataset", action="store_true",
                    help="gera data/flywheel/pedro/train_pros.jsonl (mesmos wavs, texto prosódico) pro arm A/B da rodada 3")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(SRC_JSONL) if l.strip()]
    if a.limit: rows = rows[:a.limit]

    if not a.report_only:
        from faster_whisper import WhisperModel
        from prosodic_punct import ProsodicPunctuator
        done = set()
        if os.path.exists(OUT_JSONL):
            done = {json.loads(l)["id"] for l in open(OUT_JSONL) if l.strip()}
        todo = [r for r in rows if r.get("session_id", r["audio"]) not in done]
        print(f"re-pontuando {len(todo)}/{len(rows)} ({a.model}, CPU)…", flush=True)
        m = WhisperModel(a.model, device="cpu", compute_type="int8")
        t0 = time.time()
        with open(OUT_JSONL, "a") as f:
            for i, r in enumerate(todo):
                rid = r.get("session_id", r["audio"])
                wav = os.path.join(SEG_DIR, os.path.basename(r["audio"]))
                try:
                    segs, _ = m.transcribe(wav, language="pt", word_timestamps=True, beam_size=5)
                    asr = [{"word": w.word.strip(), "start": w.start, "end": w.end}
                           for s in segs for w in s.words if w.word.strip()]
                    cur_toks = [t for t in re.sub(r"[\"“”]", "", r["text"]).split() if norm_tok(t)]
                    if not asr or not cur_toks:
                        raise ValueError("sem palavras")
                    words, cov = align_words(cur_toks, asr)
                    out = ProsodicPunctuator(wav).repunctuate(words)
                    rec = {"id": rid, "audio": os.path.basename(r["audio"]), "text_orig": r["text"],
                           "text_pros": out.text, "align_cov": round(cov, 3), "stats": out.stats}
                except Exception as e:
                    rec = {"id": rid, "audio": os.path.basename(r["audio"]), "erro": str(e)}
                    print(f"  ! {rid}: {e}", flush=True)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                if (i + 1) % 20 == 0 or i == 0:
                    el = time.time() - t0
                    print(f"[{i+1}/{len(todo)}] {el/(i+1):.1f}s/clipe · ETA {el/(i+1)*(len(todo)-i-1)/60:.0f}min", flush=True)
        print(f"✓ {OUT_JSONL}", flush=True)

    # ---------------- relatório ----------------
    recs = [json.loads(l) for l in open(OUT_JSONL) if l.strip()]
    ok = [r for r in recs if "text_pros" in r]
    err = [r for r in recs if "erro" in r]
    def pdens(t, ch): return sum(t.count(c) for c in ch)
    tot_w = sum(len(r["text_orig"].split()) for r in ok) or 1
    o_com = sum(pdens(r["text_orig"], ",") for r in ok); p_com = sum(pdens(r["text_pros"], ",") for r in ok)
    o_ter = sum(pdens(r["text_orig"], ".!") for r in ok); p_ter = sum(pdens(r["text_pros"], ".!") for r in ok)
    o_q   = sum(pdens(r["text_orig"], "?") for r in ok); p_q = sum(pdens(r["text_pros"], "?") for r in ok)
    p_hes = sum(pdens(r["text_pros"], "…") for r in ok)
    changed = sum(1 for r in ok if re.sub(r"[\s]", "", r["text_orig"]) != re.sub(r"[\s]", "", r["text_pros"]))
    cov_med = sorted(r["align_cov"] for r in ok)[len(ok)//2] if ok else 0
    low_cov = [r for r in ok if r["align_cov"] < 0.7]

    ex = sorted(ok, key=lambda r: -(abs(pdens(r["text_orig"], ",") - pdens(r["text_pros"], ","))
                                    + 2 * pdens(r["text_pros"], "…")))[:12]
    lines = [
        "# Re-pontuação prosódica — antes/depois (flywheel/pedro)",
        "",
        f"_Gerado por tools/curate/repunct_prosodic.py · {len(ok)} ok · {len(err)} erros · "
        f"cobertura de alinhamento mediana {cov_med:.0%} · {len(low_cov)} clipes <70% (revisar)_",
        "",
        "| métrica (total no corpus) | atual (Whisper/curado) | prosódica |",
        "|---|---|---|",
        f"| vírgulas /100 palavras | {100*o_com/tot_w:.1f} | {100*p_com/tot_w:.1f} |",
        f"| terminais (. !) /100 palavras | {100*o_ter/tot_w:.1f} | {100*p_ter/tot_w:.1f} |",
        f"| interrogações | {o_q} | {p_q} |",
        f"| hesitações (…) | 0 | {p_hes} |",
        f"| clipes com pontuação alterada | — | {changed}/{len(ok)} |",
        "",
        "## Exemplos (maior mudança)",
        "",
    ]
    for r in ex:
        lines += [f"**{r['id']}** (align {r['align_cov']:.0%})",
                  f"- atual: {r['text_orig']}",
                  f"- prosó: {r['text_pros']}", ""]
    lines += ["## Leitura", "",
              "- A pontuação prosódica só marca vírgula onde HÁ pausa real e fecha ponto onde o contorno",
              "  fechou (pausa longa ou F0 no piso + reset) — é a supervisão que o TTS precisa pra",
              "  aprender melodia de fala espontânea (tese Aluísio/NILC, dataset NURC-SP_ENTOA_TTS).",
              "- `…` marca hesitação/alongamento com pausa — preservado como evento prosódico.",
              "- Próximo passo: A/B no treino (arm com texto prosódico vs atual) na rodada 3.",
              ]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w").write("\n".join(lines))
    print(f"✓ relatório: {REPORT}")

    if a.emit_dataset:
        by_audio = {r["audio"]: r for r in ok}
        out_ds = os.path.join(os.path.dirname(SRC_JSONL), "train_pros.jsonl")
        n = 0
        with open(out_ds, "w") as f:
            for l in open(SRC_JSONL):
                row = json.loads(l)
                r = by_audio.get(os.path.basename(row["audio"]))
                if r and r.get("align_cov", 0) >= 0.7:
                    row["text"] = r["text_pros"]
                    f.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
        print(f"✓ dataset A/B: {out_ds} ({n} clipes, align_cov≥70%) — usar no grid_rodada3 com "
              f"--mix-dirs voz=data/flywheel/pedro --data-file train_pros.jsonl")
    print(f"  vírgulas/100w {100*o_com/tot_w:.1f}→{100*p_com/tot_w:.1f} · terminais/100w {100*o_ter/tot_w:.1f}→{100*p_ter/tot_w:.1f} · ? {o_q}→{p_q} · … 0→{p_hes}")

if __name__ == "__main__":
    main()
