#!/usr/bin/env python3
"""Exporta a curadoria do flywheel pro formato de treino do harness (runpod/train_voice.py).

Fecha o elo que faltava: gravar → process_recording.py → curar (cockpit/rate_app) → **exportar** → treinar.

Fontes:
  --source supabase (default)  tabela curar_itens (keep/manter=true, sem flags de descarte),
                               baixa os wavs do bucket público tts-curate, agrupa por `usuario`
  --source local               data/raw/elevenlabs2024 + tools/rate/curate_edits.jsonl
                               (merge: último edit por id vence — mesma lógica do rate_app.load_curate)

Saída por locutor (formato que o train_voice.py espera):
  data/flywheel/<usuario>/segments/<id>.wav   24kHz mono PCM_16
  data/flywheel/<usuario>/train.jsonl         {"audio": "<id>.wav", "text": "..."} + extras
                                              (estilo_nl/emocoes/session_id/t_start/t_end/fonte
                                               quando existirem — o train_voice ignora extras)
  data/flywheel/<usuario>/rejects.jsonl       descartes da curadoria + reprovados nos gates, com motivo

Gates de qualidade (espelham o filter do train_voice): 1-12s, texto ≥2 palavras, WAV legível.

Uso:
  python3 tools/data/export_flywheel.py --source local          # funciona hoje (dataset do Pedro)
  python3 tools/data/export_flywheel.py --source supabase       # quando houver coleta nova
  python3 tools/data/export_flywheel.py --source supabase --dry # só o resumo, sem escrever

Config supabase: env SUPABASE_URL / SUPABASE_KEY (defaults = os mesmos do process_recording.py).
"""
import argparse, io, json, os, re, sys, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_ROOT = REPO / "data" / "flywheel"

# mesmos defaults do tools/recording/process_recording.py (anon key, RLS aberto)
SUPA = os.environ.get("SUPABASE_URL", "https://yyxmtjqpmkonxlinflxu.supabase.co")
KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_iyI5855XjkDE-7yep4f69w_A9OXFZq2")
BUCKET = "tts-curate"

# fontes do caminho local (mesmos paths do rate_app.py)
CURATE_SRC = REPO / "data/raw/elevenlabs2024/transcribed_clean_auto.jsonl"
CURATE_EDITS = REPO / "tools/rate/curate_edits.jsonl"
CURATE_SEG = REPO / "data/raw/elevenlabs2024/segments"

# flags que descartam mesmo com keep=true: quebram o pareamento áudio↔texto.
# 'ruído'/'eco/metálico' são aviso de qualidade — se o curador manteve, respeitamos.
DROP_FLAGS = {"2 vozes", "sobreposição", "corte ruim"}

DUR_MIN, DUR_MAX, MIN_WORDS, SR = 1.0, 12.0, 2, 24000


def _jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def _n_words(s):
    return len(re.findall(r"\w+", s or "", flags=re.UNICODE))


def resample(audio, sr, target):
    if sr == target:
        return audio
    try:
        import soxr
        return soxr.resample(audio, sr, target)
    except ImportError:
        pass
    try:
        from math import gcd
        from scipy.signal import resample_poly
        g = gcd(sr, target)
        return resample_poly(audio, target // g, sr // g).astype("float32")
    except ImportError:
        import numpy as np  # fallback linear (pip install soxr pra qualidade)
        x_old = np.linspace(0, 1, audio.size)
        x_new = np.linspace(0, 1, int(audio.size * target / sr))
        return np.interp(x_new, x_old, audio).astype(np.float32)


# ---------- coleta de itens (um dict padronizado por clipe) ----------
# item = {id, usuario, text, keep, flags, dur_s, src (path|url), extras{...}}

def collect_local():
    src = _jsonl(CURATE_SRC)
    if not src:
        raise SystemExit(f"❌ fonte local não encontrada: {CURATE_SRC}")
    edits = {}
    for e in _jsonl(CURATE_EDITS):
        edits[e["id"]] = e  # último vence (mesma lógica do load_curate)
    items = []
    for r in src:
        e = edits.get(r["id"], {})
        wav = REPO / r["audio"]
        if not wav.exists():
            wav = CURATE_SEG / Path(r["audio"]).name
        extras = {"session_id": r.get("session"), "fonte": "local:elevenlabs2024"}
        for k in ("estilo_nl", "emocoes", "t_start", "t_end"):
            v = e.get(k) or r.get(k)
            if v:
                extras[k] = v
        items.append({"id": r["id"], "usuario": r.get("speaker", "pedro"),
                      "text": (e.get("text", r.get("text", "")) or "").strip(),
                      "keep": e.get("keep", True), "flags": e.get("flags", []),
                      "dur_s": r.get("dur_s"), "src": wav, "extras": extras})
    return items


def _supa_get(path):
    req = urllib.request.Request(SUPA + path, headers={"apikey": KEY, "Authorization": "Bearer " + KEY})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def collect_supabase():
    try:
        rows, off, page = [], 0, 1000
        while True:
            batch = _supa_get(f"/rest/v1/curar_itens?select=*&order=id&limit={page}&offset={off}")
            rows += batch
            if len(batch) < page:
                break
            off += page
    except Exception as ex:
        raise SystemExit(
            f"❌ não consegui ler curar_itens em {SUPA}: {ex}\n"
            "   configure: export SUPABASE_URL=https://<projeto>.supabase.co\n"
            "              export SUPABASE_KEY=<anon/publishable key>\n"
            "   (defaults = os mesmos hardcoded no tools/recording/process_recording.py)")
    items = []
    for r in rows:
        extras = {"fonte": f"supabase:{BUCKET}",
                  "session_id": re.sub(r"[-_]seg\d+$", "", r["id"])}  # id = <user>-<meeting>-segNNN
        for k in ("estilo_nl", "emocoes", "t_start", "t_end"):
            if r.get(k):
                extras[k] = r[k]
        items.append({"id": r["id"], "usuario": r.get("usuario", "desconhecido"),
                      "text": (r.get("texto") or r.get("text_orig") or "").strip(),
                      "keep": bool(r.get("manter", True)), "flags": r.get("flags") or [],
                      "dur_s": r.get("dur_s"),
                      "src": f"{SUPA}/storage/v1/object/public/{BUCKET}/{r['audio']}",
                      "extras": extras})
    return items


# ---------- gates + escrita ----------

def load_audio(item, dry):
    """→ (audio, sr) ou (None, None) em dry. Levanta exceção se ilegível."""
    import soundfile as sf
    if isinstance(item["src"], Path):
        if not item["src"].exists():
            raise FileNotFoundError(f"wav ausente: {item['src']}")
        if dry:
            info = sf.info(str(item["src"]))
            item["dur_s"] = round(info.duration, 2)
            return None, None
        audio, sr = sf.read(str(item["src"]), dtype="float32", always_2d=False)
    else:  # URL do bucket
        if dry:
            return None, None  # dry não baixa; usa dur_s da tabela
        raw = urllib.request.urlopen(item["src"], timeout=120).read()
        audio, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    item["dur_s"] = round(len(audio) / sr, 2)
    return audio, sr


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="supabase", choices=["supabase", "local"])
    ap.add_argument("--out-root", default=str(OUT_ROOT))
    ap.add_argument("--dry", action="store_true", help="só o resumo, sem baixar/escrever")
    ap.add_argument("--strict-emilia", action="store_true",
                    help="reprova outliers de duração/char (default: só avisa — dado curado tem enumerações lentas legítimas)")
    a = ap.parse_args()

    print(f"🔄 coletando itens curados (source={a.source})…", flush=True)
    items = collect_supabase() if a.source == "supabase" else collect_local()
    print(f"   {len(items)} itens em curar_itens" if a.source == "supabase"
          else f"   {len(items)} itens ({CURATE_SRC.name} + merge de {CURATE_EDITS.name})")

    out_root = Path(a.out_root)
    users = {}  # usuario → {rows, rejects, total}
    for it in sorted(items, key=lambda x: (x["usuario"], x["id"])):
        u = users.setdefault(it["usuario"], {"rows": [], "rejects": [], "total": 0})
        u["total"] += 1

        def reject(motivo):
            u["rejects"].append({"id": it["id"], "motivo": motivo, "text": it["text"],
                                 "dur_s": it.get("dur_s"), "flags": it["flags"]})

        if not it["keep"]:
            reject("descartado na curadoria (keep=false)"); continue
        bad = DROP_FLAGS & set(it["flags"])
        if bad:
            reject(f"flag de descarte: {', '.join(sorted(bad))}"); continue
        if _n_words(it["text"]) < MIN_WORDS:
            reject(f"texto <{MIN_WORDS} palavras: {it['text']!r}"); continue
        try:
            audio, sr = load_audio(it, a.dry)
        except Exception as ex:
            reject(f"wav ilegível: {ex}"); continue
        dur = it.get("dur_s")
        if dur is None:
            reject("sem duração conhecida (dry sem dur_s na fonte)"); continue
        if not (DUR_MIN <= dur <= DUR_MAX):
            reject(f"duração fora de {DUR_MIN:g}-{DUR_MAX:g}s ({dur}s)"); continue

        wav_name = it["id"] + ".wav"
        if not a.dry:
            import soundfile as sf
            seg_dir = out_root / it["usuario"] / "segments"
            seg_dir.mkdir(parents=True, exist_ok=True)
            sf.write(seg_dir / wav_name, resample(audio, sr, SR), SR, subtype="PCM_16")
        row = {"audio": wav_name, "text": it["text"]}
        row.update({k: v for k, v in it["extras"].items() if v})
        u["rows"].append({**row, "dur_s": dur})

    # gate Emilia (verificado, arXiv 2407.05361): outlier de duração-por-caractere = proxy
    # barato de desalinhamento texto-áudio. Em dado CURADO (verdade humana) só AVISA —
    # auditoria de 02/jul mostrou que enumerações lentas de nomes caem no filtro e são dado
    # legítimo/raro. --strict-emilia reprova de verdade (usar em dado NÃO curado).
    for user, u in users.items():
        if len(u["rows"]) < 12:
            continue  # amostra pequena demais pra estatística
        dpcs = sorted(r["dur_s"] / max(1, len(re.sub(r"\W", "", r["text"])))
                      for r in u["rows"] if r.get("dur_s"))
        q1, q3 = dpcs[len(dpcs)//4], dpcs[3*len(dpcs)//4]
        lo, hi = q1 - 1.5*(q3-q1), q3 + 1.5*(q3-q1)
        keep, drop = [], []
        for r in u["rows"]:
            dpc = r["dur_s"] / max(1, len(re.sub(r"\W", "", r["text"]))) if r.get("dur_s") else None
            (keep if (dpc is None or lo <= dpc <= hi) else drop).append(r)
        if drop and a.strict_emilia:
            for r in drop:
                u["rejects"].append({"id": r["audio"].replace(".wav", ""), "motivo":
                    f"outlier duração/char (gate Emilia): {r['dur_s']}s p/ {len(r['text'])} chars",
                    "text": r["text"], "dur_s": r["dur_s"], "flags": []})
            print(f"  ⚠ {user}: {len(drop)} clipe(s) REPROVADOS no gate Emilia (--strict-emilia)")
            u["rows"] = keep
        elif drop:
            print(f"  ⚠ {user}: {len(drop)} clipe(s) com duração/char fora de [{lo:.2f},{hi:.2f}] s/char "
                  f"(gate Emilia, só aviso — revisar se são silêncio/desalinhamento):")
            for r in drop:
                print(f"      {r['audio']} · {r['dur_s']}s · {r['text'][:60]!r}")

    if not a.dry:
        for user, u in users.items():
            udir = out_root / user
            udir.mkdir(parents=True, exist_ok=True)
            with (udir / "train.jsonl").open("w", encoding="utf-8") as f:
                for r in u["rows"]:
                    f.write(json.dumps({k: v for k, v in r.items() if k != "dur_s"}, ensure_ascii=False) + "\n")
            with (udir / "rejects.jsonl").open("w", encoding="utf-8") as f:
                for r in u["rejects"]:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---------- RESUMO (o placar da fase de coleta) ----------
    print(f"\n📊 RESUMO DO EXPORT — source={a.source}{' · DRY (nada escrito)' if a.dry else ''}")
    tot_n = tot_min = 0
    for user in sorted(users):
        u = users[user]
        mins = sum(r["dur_s"] or 0 for r in u["rows"]) / 60
        tot_n += len(u["rows"]); tot_min += mins
        rate = 100 * len(u["rows"]) / u["total"] if u["total"] else 0
        print(f"  {user:<12} {len(u['rows']):>4} clipes · {mins:5.1f} min · "
              f"keep {rate:.0f}% ({len(u['rows'])}/{u['total']}) · {len(u['rejects'])} rejeitados")
        motivos = {}
        for r in u["rejects"]:
            m = r["motivo"].split(":")[0].split("(")[0].strip()
            motivos[m] = motivos.get(m, 0) + 1
        for m, n in sorted(motivos.items(), key=lambda x: -x[1]):
            print(f"    ↳ {n}× {m}")
    print(f"  {'─' * 56}")
    print(f"  TOTAL        {tot_n:>4} clipes · {tot_min:5.1f} min")
    if not a.dry and tot_n:
        print(f"\n✅ exportado em {out_root}/<usuario>/{{segments/,train.jsonl,rejects.jsonl}}")
        print("   treinar: aponte o train_voice pro locutor, ex.:")
        print(f"   --data-dir {out_root.relative_to(REPO) if out_root.is_relative_to(REPO) else out_root}/pedro --data-file train.jsonl")
    elif not tot_n:
        print("\n⚠️ nada exportado — confere a curadoria/fonte.")


if __name__ == "__main__":
    main()
