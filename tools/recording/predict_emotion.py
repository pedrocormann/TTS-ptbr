#!/usr/bin/env python3
"""Pré-prediz a emoção de cada clipe (emotion2vec+) → escreve em curar_itens.emocoes_auto.
A IA SUGERE; o humano valida no cockpit (aceitar/ajustar). Não substitui a anotação humana — acelera.

Modelo: emotion2vec_plus_large (iic/emotion2vec_plus_large) — é o mesmo backbone do SER pt-BR
de referência (arXiv:2506.02088, emotion2vec+BERTimbau). 9 classes → mapeadas pros nossos rótulos de afeto.

Roda onde tiver o ambiente ML (pod/Colab):
  pip install funasr modelscope torch torchaudio
  python predict_emotion.py            # processa quem está sem emocoes_auto
  python predict_emotion.py --all      # reprocessa todos
  python predict_emotion.py --user pedro
"""
import argparse, json, os, tempfile, urllib.request, urllib.parse

SUPA = "https://yyxmtjqpmkonxlinflxu.supabase.co"
KEY  = os.environ.get("SUPABASE_KEY", "sb_publishable_iyI5855XjkDE-7yep4f69w_A9OXFZq2")
STORAGE = SUPA + "/storage/v1/object/public/tts-curate/"
HDR = {"apikey": KEY, "Authorization": "Bearer " + KEY}

# emotion2vec+ (9 classes, bilíngue zh/en) → nossos rótulos de afeto (EN)
MAP = {"angry": "angry", "disgusted": "disgusted", "fearful": "anxious",
       "happy": "happy", "neutral": "neutral", "sad": "sad", "surprised": "surprised"}

def rest(path, method="GET", body=None, extra=None):
    h = dict(HDR); h["Content-Type"] = "application/json"
    if extra: h.update(extra)
    req = urllib.request.Request(SUPA + "/rest/v1/" + path,
        data=(json.dumps(body).encode() if body is not None else None), headers=h, method=method)
    r = urllib.request.urlopen(req, timeout=40).read()
    return json.loads(r) if r else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="reprocessa todos (default: só sem emocoes_auto)")
    ap.add_argument("--user", default=None)
    a = ap.parse_args()

    from funasr import AutoModel
    print("carregando emotion2vec_plus_large…", flush=True)
    model = AutoModel(model="iic/emotion2vec_plus_large", disable_update=True)

    q = "curar_itens?select=id,audio,usuario"
    if not a.all: q += "&emocoes_auto=eq.%5B%5D"          # []  (só os vazios)
    if a.user: q += "&usuario=eq." + urllib.parse.quote(a.user)
    rows = rest(q + "&limit=5000")
    print(f"{len(rows)} clipes a prever", flush=True)

    ok = 0
    for i, r in enumerate(rows):
        try:
            url = STORAGE + (r.get("audio") or (r["id"] + ".wav"))
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(urllib.request.urlopen(url, timeout=30).read()); tmp = f.name
            rec = model.generate(tmp, granularity="utterance", extract_embedding=False)
            os.unlink(tmp)
            labels = rec[0]["labels"]; scores = rec[0]["scores"]
            pairs = sorted(zip(labels, scores), key=lambda x: -x[1])
            out = []
            for lab, sc in pairs[:2]:
                en = lab.split("/")[-1].strip().lower()         # "高兴/happy" → "happy"
                m = MAP.get(en)
                if m and m not in out and (sc > 0.15 or not out):  # top-1 sempre; 2º só se >0.15
                    out.append(m)
            rest("curar_itens?id=eq." + urllib.parse.quote(r["id"]), "PATCH",
                 {"emocoes_auto": out}, {"Prefer": "return=minimal"})
            ok += 1
        except Exception as e:
            print(f"  erro {r.get('id')}: {e}", flush=True)
        if (i + 1) % 50 == 0: print(f"  {i+1}/{len(rows)} (ok={ok})", flush=True)
    print(f"FIM: {ok}/{len(rows)} com sugestão da IA. Agora aparece o banner '🤖 a IA ouviu…' no Curar.", flush=True)

if __name__ == "__main__":
    main()
