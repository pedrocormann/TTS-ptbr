#!/usr/bin/env python3
"""Pipeline Whisper-first do flywheel: gravação → transcrição → quebra em FRASES → curar_itens (por pessoa).

Roda DEPOIS da sessão de gravação e ANTES de a pessoa curar. Para cada faixa (1 por pessoa):
  1) faster-whisper (large-v3) com timestamps por palavra/segmento
  2) quebra em frases de ~3-12s em fronteira de pausa/pontuação (ver `segmentar`)
  3) sobe cada segmento .wav pro bucket tts-curate (via edge function upload-file)
  4) insere uma linha em curar_itens (usuario, text_orig=Whisper, texto=Whisper, editado=false)
Depois a pessoa só corrige o texto no cockpit (aba Curar → escolhe o nome dela).

Uso:
  python process_recording.py --user pedro --meeting "papo-23jun" --audio /caminho/faixa_pedro.wav
  (roda no pod/Colab com faster-whisper instalado; SUPABASE_KEY no env ou usa a publishable embutida)

DECISÃO DE TAMANHO (ver doc no fim): frases completas em fronteira de pausa, alvo 3-12s.
NÃO fragmentos minúsculos (matam prosódia) NEM blocos >15s (estouram contexto/alinhamento).
"""
import argparse, base64, json, os, re, sys, urllib.request, pathlib

SUPA = "https://yyxmtjqpmkonxlinflxu.supabase.co"
KEY  = os.environ.get("SUPABASE_KEY", "sb_publishable_iyI5855XjkDE-7yep4f69w_A9OXFZq2")  # anon (RLS aberto)
UPLOAD_FN = "https://yyxmtjqpmkonxlinflxu.functions.supabase.co/upload-file"

# ---------- quebra em frases (a decisão) ----------
def segmentar(segs, alvo_min=3.0, alvo_max=12.0, hard_max=15.0, min_manter=1.5, pausa=0.6):
    """segs: lista do Whisper [{start,end,text}]. Agrupa em frases de ~3-12s.
    Fecha um chunk quando: já tem alvo_min E (terminou frase OU tem pausa real),
    ou quando incluir o próximo estouraria alvo_max. Junta <min_manter no vizinho."""
    chunks, cur = [], None
    for s in segs:
        t = (s["text"] or "").strip()
        if cur is None:
            cur = {"start": s["start"], "end": s["end"], "text": t}; continue
        dur = cur["end"] - cur["start"]
        gap = s["start"] - cur["end"]
        fim_frase = cur["text"].rstrip().endswith((".", "?", "!", "…"))
        prox = s["end"] - s["start"]
        if (dur >= alvo_min and (fim_frase or gap >= pausa)) or (dur + prox > alvo_max):
            chunks.append(cur); cur = {"start": s["start"], "end": s["end"], "text": t}
        else:
            cur["end"] = s["end"]; cur["text"] = (cur["text"] + " " + t).strip()
    if cur: chunks.append(cur)
    # junta fragmentos curtos demais no anterior
    merged = []
    for c in chunks:
        if merged and (c["end"] - c["start"]) < min_manter:
            merged[-1]["end"] = c["end"]; merged[-1]["text"] += " " + c["text"]
        else:
            merged.append(c)
    for c in merged:  # marca os que passaram do hard_max (revisar manual)
        c["longo"] = (c["end"] - c["start"]) > hard_max
    return merged

def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=60).read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="pedro|joao|guilherme")
    ap.add_argument("--meeting", required=True)
    ap.add_argument("--audio", required=True, help="wav da faixa dessa pessoa")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--dry", action="store_true", help="não sobe/insere, só mostra a quebra")
    ap.add_argument("--prosodic", action="store_true", default=True,
                    help="pontuação prosódica + segmentação por unidade entoacional (abordagem Aluísio/NILC; default)")
    ap.add_argument("--no-prosodic", dest="prosodic", action="store_false",
                    help="volta pro modo antigo (pontuação gramatical do Whisper + quebra por pausa)")
    a = ap.parse_args()

    import soundfile as sf
    from faster_whisper import WhisperModel
    audio, sr = sf.read(a.audio)
    if audio.ndim > 1: audio = audio.mean(axis=1)
    print(f"[{a.user}] {a.audio} · {len(audio)/sr:.0f}s @ {sr}Hz · transcrevendo com {a.model}…", flush=True)
    model = WhisperModel(a.model, device="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu",
                         compute_type="float16" if os.environ.get("CUDA_VISIBLE_DEVICES") else "int8")
    segs_it, info = model.transcribe(a.audio, language="pt", vad_filter=True,
                                     word_timestamps=a.prosodic,
                                     vad_parameters={"min_silence_duration_ms": 400})
    if a.prosodic:
        # pontuação prosódica (pausas+F0 do próprio áudio) + segmentação por IU
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "text"))
        from prosodic_punct import ProsodicPunctuator, iu_segments
        words = [{"word": w.word.strip(), "start": w.start, "end": w.end}
                 for s in segs_it for w in (s.words or []) if w.word.strip()]
        pp = ProsodicPunctuator(a.audio)
        out = pp.repunctuate(words)
        print(f"  prosódica: {out.stats['terminal']} terminais · {out.stats['nonterminal']} vírgulas · "
              f"{out.stats['hesitation']} hesitações · {out.stats['question']} perguntas", flush=True)
        chunks = []
        for sg in iu_segments(out.words, out.boundaries):
            txt = " ".join(t for t in out.tokens[sg["i0"]:sg["i1"] + 1] if t).strip()
            chunks.append({"start": sg["start"], "end": sg["end"], "text": txt,
                           "longo": (sg["end"] - sg["start"]) > 15.0})
        n_unid = len(out.words)
    else:
        segs = [{"start": s.start, "end": s.end, "text": s.text} for s in segs_it]
        chunks = segmentar(segs)
        n_unid = len(segs)
    durs = [c["end"] - c["start"] for c in chunks]
    longos = sum(1 for c in chunks if c.get("longo"))
    print(f"  {n_unid} {'palavras' if a.prosodic else 'segs Whisper'} → {len(chunks)} frases · "
          f"dur med={sorted(durs)[len(durs)//2]:.1f}s min={min(durs):.1f} max={max(durs):.1f}"
          f"{' · '+str(longos)+' >15s (revisar)' if longos else ''}", flush=True)

    base = re.sub(r"[^a-z0-9]+", "-", f"{a.user}-{a.meeting}".lower()).strip("-")
    rows = []
    for i, c in enumerate(chunks):
        sid = f"{base}-seg{i:03d}"
        s0, s1 = int(c["start"] * sr), int(c["end"] * sr)
        clip = audio[s0:s1]
        if not a.dry:
            import io
            bio = io.BytesIO(); sf.write(bio, clip, sr, format="WAV", subtype="PCM_16"); bio.seek(0)
            b64 = base64.b64encode(bio.read()).decode()
            _post(UPLOAD_FN, {"b64": b64, "path": sid + ".wav", "bucket": "tts-curate", "contentType": "audio/wav"},
                  {"Content-Type": "application/json"})
        rows.append({"id": sid, "usuario": a.user, "audio": sid + ".wav",
                     "text_orig": c["text"], "text_v2": None, "texto": c["text"],
                     "manter": True, "flags": (["longo>15s"] if c.get("longo") else []),
                     "dur_s": round(c["end"] - c["start"], 2), "editado": False})
        if a.dry: print(f"  {sid} · {rows[-1]['dur_s']}s · {c['text'][:70]}")

    if not a.dry and rows:
        _post(SUPA + "/rest/v1/curar_itens", rows,
              {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json",
               "Prefer": "resolution=merge-duplicates"})
        print(f"✅ {len(rows)} frases subidas + inseridas em curar_itens (usuario={a.user}). "
              f"Agora {a.user} abre o cockpit → Curar → escolhe o nome dele e corrige o texto.")
    elif a.dry:
        print(f"(dry) {len(rows)} frases — nada subido.")

if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------------
# POR QUE FRASES DE ~3-12s (e não fragmentos nem blocos):
#  - PROSÓDIA: uma frase completa mantém a curva de entonação inteira → o modelo
#    aprende melodia natural. Fragmento de 1 palavra = prosódia picotada (é o nosso
#    defeito #2: robótico). Frase-nível ataca exatamente esse problema.
#  - CSM usa CONTEXTO entre turnos; a unidade de treino é a utterância/frase.
#  - PRECISÃO: o Whisper acerta mais com contexto de frase (palavra solta é ambígua),
#    e curar é mais fácil (você lê 1 frase e confere). Bloco >15s → transcrição
#    desalinha + difícil pegar erro + domina o loss + estoura contexto.
#  A quebra anterior (elevenlabs2024) já caiu nesse ponto: mediana 5.3s, máx 12s.
#  Mantemos isso; só evitamos os <2s (juntando no vizinho aqui).
