"""
WER round-trip — the core pt-BR intelligibility metric, reused by every spike +
the Mimi freeze test. Generate/encode audio from text -> ASR it back -> WER vs
the source text. Cheap, automatic, CPU-capable (tiny/medium). Keep the LABELER
(annotate.py = whisper medium) and this JUDGE distinct on purpose.

CLI (judge a folder against a transcripts jsonl):
  python -m eval.wer_roundtrip --in-dir gen/ --transcripts gen/trans.jsonl \
      [--model medium] [--lang pt]
trans.jsonl: {"audio": "<name>.wav", "text": "<exact source text>"} per line.

Library:
  from eval.wer_roundtrip import transcribe, wer, asr_model
"""
import argparse, json, os, statistics

_NORM = None


def _norm():
    global _NORM
    if _NORM is None:
        import jiwer
        _NORM = jiwer.Compose([
            jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
            jiwer.RemoveMultipleSpaces(), jiwer.Strip(),
        ])
    return _NORM


def wer(reference: str, hypothesis: str) -> float:
    import jiwer
    n = _norm()
    r, h = n(reference), n(hypothesis)
    if not r.strip():
        return 0.0 if not h.strip() else 1.0
    return jiwer.wer(r, h)


def asr_model(model: str = "medium"):
    import os
    from faster_whisper import WhisperModel
    # CPU por padrão: o eval transcreve poucas frases (~1-2 min) e na GPU o
    # ctranslate2/cuDNN9 pode CRASHAR o kernel no Colab (não é exceção — abort do
    # processo, derruba a sessão). CPU é à prova de bala. Force GPU com WER_DEVICE=cuda.
    dev = os.environ.get("WER_DEVICE", "cpu")
    ct = "float16" if dev == "cuda" else "int8"
    return WhisperModel(model, device=dev, compute_type=ct)


def transcribe(model, wav_path: str, lang: str = "pt") -> str:
    segs, _ = model.transcribe(wav_path, language=lang, beam_size=5)
    return " ".join(s.text for s in segs).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--model", default="medium",
                    help="tiny/base/small/medium/large-v3 (tiny = CPU smoke)")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--cap", action="store_true",
                    help="clamp per-utterance WER at 1.0 in the AGGREGATE so one "
                         "catastrophic hallucination doesn't blow the median "
                         "(raw per-utterance value still logged to the jsonl). "
                         "Default off = raw/correct WER (can exceed 100%%, which "
                         "is real and signals bad generations — don't hide it "
                         "blindly). Found via the 2026-05-17 harness self-test.")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.transcripts, encoding="utf-8")]
    m = asr_model(args.model)
    wers = []
    out = os.path.join(args.in_dir, "_wer_results.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            p = os.path.join(args.in_dir, r["audio"])
            if not os.path.isfile(p):
                print(f"[skip] missing {p}")
                continue
            hyp = transcribe(m, p, args.lang)
            w = wer(r["text"], hyp)               # raw (can exceed 1.0 — correct)
            wers.append(min(w, 1.0) if args.cap else w)
            f.write(json.dumps({"audio": r["audio"], "wer": w, "hyp": hyp},
                                ensure_ascii=False) + "\n")  # jsonl always raw
    if wers:
        agg = "capped@1.0" if args.cap else "raw"
        print(f"WER p50={statistics.median(wers)*100:.1f}%  "
              f"mean={sum(wers)/len(wers)*100:.1f}%  n={len(wers)} ({agg}) -> {out}")
    else:
        print("no audio scored")


if __name__ == "__main__":
    main()
