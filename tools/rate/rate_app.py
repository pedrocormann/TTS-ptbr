#!/usr/bin/env python3
"""
Rate — app local pra avaliar os áudios E entender o projeto (o "compasso").

Três abas:
  • Avaliar  — ouve cada áudio e dá notas estruturadas (inclui "soa nativo vs gringo",
               naturalidade, parou-certo, voz do Pedro, sotaque, e TAGS de problema
               pra direcionar o que consertar nos próximos modelos).
  • Insights — agrega tudo (por run, por emoção) + ranking dos problemas mais comuns
               → diz o que o PRÓXIMO treino deve atacar.
  • Trilha   — overview do projeto: as 3 abordagens (A/voz, B/spine, M/Maya), onde
               estamos em cada uma, datasets usados (quais partes, como), o que
               aprendemos/implementamos, e pra onde vamos.

Sem dependências (stdlib). Escaneia runpod_samples/ (configurável). Notas → ratings.jsonl.
Uso: python tools/rate/rate_app.py [--dir pasta] [--port 8081]
"""
import argparse, json, os, re, statistics, urllib.parse, webbrowser, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RATINGS = Path(__file__).resolve().parent / 'ratings.jsonl'
MAP_JSON = Path(__file__).resolve().parent / 'trilha_map.json'
BLOCK_FILE = Path(__file__).resolve().parent / 'block.txt'
_RLOCK = threading.Lock()


def load_block():
    try:
        return BLOCK_FILE.read_text(encoding='utf-8').strip() or 'treino-1'
    except Exception:
        return 'treino-1'


# ---------- Curadoria do dataset da voz (aba Curar) ----------
CURATE_SRC = REPO / 'data/raw/elevenlabs2024/transcribed_clean_auto.jsonl'
CURATE_RETRANS = REPO / 'data/raw/elevenlabs2024/retranscribed.jsonl'
CURATE_EDITS = Path(__file__).resolve().parent / 'curate_edits.jsonl'
CURATE_CLEAN = REPO / 'data/raw/elevenlabs2024/transcribed_clean.jsonl'
CURATE_SEG = REPO / 'data/raw/elevenlabs2024/segments'


def _jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()] if p.exists() else []


def load_curate():
    src = _jsonl(CURATE_SRC)
    retr = {r['id']: r.get('text_v2', '') for r in _jsonl(CURATE_RETRANS)}
    edits = {}
    for e in _jsonl(CURATE_EDITS):
        edits[e['id']] = e   # último vence
    out = []
    for r in src:
        e = edits.get(r['id'], {})
        out.append({
            'id': r['id'], 'audio': r.get('audio'), 'style': r.get('style'), 'dur_s': r.get('dur_s'),
            'text_orig': r.get('text', ''), 'text_v2': retr.get(r['id']),
            'text': e.get('text', r.get('text', '')),
            'keep': e.get('keep', True), 'flags': e.get('flags', []), 'edited': bool(e),
        })
    return out


def save_curate(e):
    with _RLOCK:
        with open(CURATE_EDITS, 'a', encoding='utf-8') as f:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
        recs = load_curate()
        with open(CURATE_CLEAN, 'w', encoding='utf-8') as f:
            for r in recs:
                if r.get('keep'):
                    f.write(json.dumps({'id': r['id'], 'audio': r.get('audio'),
                                        'text': r['text'], 'dur_s': r.get('dur_s')}, ensure_ascii=False) + '\n')
ap = argparse.ArgumentParser()
ap.add_argument('--dir', default=str(REPO / 'runpod_samples'))
ap.add_argument('--port', type=int, default=8081)
ARGS = ap.parse_args()
SAMPLES = Path(ARGS.dir)

PROBLEMS = ['sotaque gringo', 'fonema errado', 'entonação robótica', 'cortou/incompleto',
            'ruído/chiado', 'emoção errada', 'repetiu', 'rápido/devagar', 'metálico/artefato']


def load_benchmark():
    bench = {}
    bp = REPO / 'eval' / 'benchmark_ptbr.jsonl'
    if bp.exists():
        for l in bp.read_text(encoding='utf-8').splitlines():
            if l.strip():
                r = json.loads(l); bench[r['id']] = r
    return bench


def _norm_words(s):
    return re.findall(r"\w+", (s or '').lower(), flags=re.UNICODE)


def align_words(ref, hyp):
    """Alinhamento palavra-a-palavra ref↔hyp (os erros que o WER pega, decompostos)."""
    r, h = _norm_words(ref), _norm_words(hyp)
    n, m = len(r), len(h)
    if not n and not m:
        return []
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): dp[i][0] = i
    for j in range(m + 1): dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and r[i - 1] == h[j - 1] and dp[i][j] == dp[i - 1][j - 1]:
            ops.append({'op': 'ok', 'ref': r[i - 1], 'hyp': h[j - 1]}); i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append({'op': 'sub', 'ref': r[i - 1], 'hyp': h[j - 1]}); i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append({'op': 'del', 'ref': r[i - 1], 'hyp': None}); i -= 1
        else:
            ops.append({'op': 'ins', 'ref': None, 'hyp': h[j - 1]}); j -= 1
    ops.reverse()
    return ops


def build_manifest():
    bench = load_benchmark()
    clips = []
    if not SAMPLES.exists():
        return clips
    for run_dir in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        persent = {}
        for pj in run_dir.rglob('per_sentence.jsonl'):
            for l in pj.read_text(encoding='utf-8').splitlines():
                if l.strip():
                    r = json.loads(l); persent[r['id']] = r
            break
        for wav in sorted(run_dir.rglob('*.wav')):
            cid = wav.stem
            b = bench.get(cid, {}); ps = persent.get(cid, {})
            text = b.get('text', ps.get('ref', '')); hyp = ps.get('hyp', '')
            clips.append({
                'run': run_dir.name, 'id': cid,
                'emotion': b.get('emotion', '?'), 'accent': b.get('accent', '?'),
                'text': text,
                'wer': ps.get('wer'), 'dur_s': ps.get('dur_s'), 'hyp': hyp,
                'wer_ops': align_words(text, hyp) if (text and hyp) else [],
                'wav': str(wav.relative_to(REPO)),
            })
    return clips


def load_ratings():
    out = {}
    if RATINGS.exists():
        for l in RATINGS.read_text(encoding='utf-8').splitlines():
            if l.strip():
                r = json.loads(l); out[(r['run'], r['id'])] = r
    return out


def insights():
    clips = build_manifest()
    ratings = load_ratings()
    rated = [{**c, **ratings.get((c['run'], c['id']), {})} for c in clips]
    rated = [r for r in rated if r.get('geral') is not None]

    def agg(rows):
        def m(key):
            vals = [r[key] for r in rows if r.get(key) is not None]
            return round(statistics.mean(vals), 1) if vals else None
        parou = [1 if r.get('parou') else 0 for r in rows if r.get('parou') is not None]
        return {'n': len(rows), 'geral': m('geral'), 'nativo': m('nativo'),
                'natural': m('natural'), 'voz': m('voz'),
                'parou_pct': round(100 * statistics.mean(parou)) if parou else None}
    by_run, by_emo, probs = {}, {}, {}
    for r in rated:
        by_run.setdefault(r['run'], []).append(r)
        by_emo.setdefault(r['emotion'], []).append(r)
        for p in (r.get('problemas') or []):
            probs[p] = probs.get(p, 0) + 1
    # cobertura de marcadores no tempo (o substrato pros agentes do futuro)
    marc_clips, marc_total, marc_tag = 0, 0, {}
    for rr in ratings.values():
        ms = rr.get('markers') or []
        if ms:
            marc_clips += 1
            marc_total += len(ms)
            for m in ms:
                t = m.get('tag', '?'); marc_tag[t] = marc_tag.get(t, 0) + 1
    return {'total_rated': len(rated), 'total': len(clips),
            'por_run': {k: agg(v) for k, v in sorted(by_run.items())},
            'por_emocao': {k: agg(v) for k, v in sorted(by_emo.items())},
            'problemas': dict(sorted(probs.items(), key=lambda x: -x[1])),
            'feedback': {'clips_marcados': marc_clips, 'total_marcadores': marc_total,
                         'por_tag': dict(sorted(marc_tag.items(), key=lambda x: -x[1]))}}


def feedback_records():
    """Registros agent-ready: junta áudio + refs + avaliações + marcadores no tempo.
    É o contrato que um loop de agentes futuro consome (ver tools/rate/FEEDBACK.md)."""
    clips = build_manifest()
    ratings = load_ratings()
    out = []
    for c in clips:
        r = ratings.get((c['run'], c['id']), {})
        out.append({
            'schema_version': 1,
            'run': c['run'], 'id': c['id'], 'audio': c.get('wav'),
            'ref_text': c['text'], 'asr_hyp': c.get('hyp', ''),
            'emotion': c['emotion'], 'accent': c['accent'],
            'wer': c['wer'], 'wer_ops': c.get('wer_ops', []), 'dur_s': c['dur_s'],
            'ratings': {k: r.get(k) for k in ('geral', 'nativo', 'natural', 'voz', 'parou', 'carioca', 'nota')},
            'problems': r.get('problemas') or [],
            'markers': r.get('markers') or [],
            'rated_ts': r.get('ts'),
        })
    return out


def load_map():
    if MAP_JSON.exists():
        try:
            return json.loads(MAP_JSON.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'nodes': [], 'lanes': [], 'hypotheses': [], 'state': {'now': '(mapa não gerado — rode o workflow)', 'next': []}}


PAGE = r"""<!doctype html><html lang=pt-br><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Rate — TTS pt-BR</title>
<link rel=preconnect href="https://fonts.googleapis.com"><link rel=preconnect href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600;900&family=Geist+Mono:wght@400;500;600&display=swap" rel=stylesheet>
<style>
:root{--bg:#08080a;--surface:rgba(255,255,255,0.025);--surface-h:rgba(255,255,255,0.05);--b:rgba(255,255,255,0.06);--bh:rgba(255,255,255,0.14);
--t:#f5f5f7;--t2:rgba(245,245,247,0.6);--tm:rgba(245,245,247,0.35);--tf:rgba(245,245,247,0.18);
--red:#C7302D;--orange:#E45933;--blue:#7da0ff;--green:#28c840;--ac:#f5f5f7;
--serif:'Instrument Serif',Georgia,serif;--disp:'Geist',-apple-system,system-ui,sans-serif;--body:'Geist',-apple-system,system-ui,sans-serif;--mono:'Geist Mono','SF Mono',Menlo,monospace;
--radius:14px;--rsm:8px;--ease:cubic-bezier(0.16,1,0.3,1)}
*{margin:0;padding:0;box-sizing:border-box}
html,body{font-family:var(--body);background:var(--bg);color:var(--t);letter-spacing:-0.005em;-webkit-font-smoothing:antialiased;font-feature-settings:"ss01","cv11";line-height:1.6}
body{background-image:radial-gradient(ellipse 1400px 700px at 50% -20%,rgba(255,255,255,0.025),transparent 60%);position:relative;min-height:100vh}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");opacity:0.4;mix-blend-mode:overlay}
body>*{position:relative;z-index:1}
header{display:flex;align-items:center;gap:14px;padding:14px 28px;border-bottom:1px solid var(--b);position:sticky;top:0;z-index:20;background:rgba(8,8,10,0.72);backdrop-filter:blur(24px) saturate(180%);-webkit-backdrop-filter:blur(24px) saturate(180%)}
h1{font-family:var(--disp);font-size:13px;font-weight:900;letter-spacing:0.12em;text-transform:uppercase}.sp{flex:1}.muted{color:var(--tm)}
.tab{background:transparent;border:1px solid transparent;color:var(--tm);border-radius:var(--rsm);padding:8px 14px;cursor:pointer;font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;font-family:var(--body);transition:all 0.2s var(--ease)}
.tab:hover{color:var(--t2);background:var(--surface)}.tab.on{background:var(--surface-h);color:var(--t);border-color:var(--bh)}
.bar{height:3px;background:rgba(255,255,255,0.05);border-radius:999px;flex:1;max-width:180px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--t);width:0;transition:width 0.8s var(--ease)}
.wrap{max-width:1180px;margin:30px auto;padding:0 20px}#av,#in{max-width:820px;margin:0 auto}.card{background:var(--surface);border:1px solid var(--b);border-radius:var(--radius);padding:24px;margin-bottom:16px}
.tags{font-family:var(--mono);font-size:10px;letter-spacing:0.04em;text-transform:uppercase;color:var(--tm);margin-bottom:4px}
.tags span{display:inline-block;border:1px solid var(--b);border-radius:6px;padding:3px 9px;margin:0 6px 6px 0}
.text{font-family:var(--serif);font-size:28px;font-weight:400;line-height:1.3;letter-spacing:-0.01em;margin:16px 0;color:var(--t)}
.hyp{font-family:var(--mono);font-size:12px;color:var(--tm);background:rgba(255,255,255,0.02);border:1px solid var(--b);border-radius:var(--rsm);padding:10px 12px;margin:10px 0}
audio{width:100%;margin:14px 0}.warn{color:var(--orange)}
.leg{font-size:12px;color:var(--t2);background:rgba(255,255,255,0.02);border:1px solid var(--b);border-radius:var(--rsm);padding:10px 12px;margin:12px 0;line-height:1.55}.leg b{color:var(--t);font-weight:500}
.ind{margin:18px 0}.ihead{font-size:11px;letter-spacing:0.04em;text-transform:uppercase;color:var(--tm);margin-bottom:8px}.ihead b{color:var(--t);font-weight:600}.exp{text-transform:none;letter-spacing:0;color:var(--tm);font-weight:400;margin-left:8px;font-size:12px}
.btn{background:var(--surface);border:1px solid var(--b);color:var(--t2);border-radius:var(--rsm);padding:8px 13px;cursor:pointer;font-size:13px;font-family:var(--body);margin:0 6px 6px 0;transition:all 0.15s var(--ease)}.btn:hover{border-color:var(--bh);color:var(--t)}
.btn.on{background:var(--t);color:var(--bg);border-color:var(--t);font-weight:600}.btn.ok.on{background:var(--green);color:#06210f;border-color:var(--green)}.btn.no.on{background:var(--red);color:#fff;border-color:var(--red)}.btn.fl.on{background:var(--orange);color:#fff;border-color:var(--orange)}
input[type=text]{width:100%;background:rgba(255,255,255,0.02);border:1px solid var(--b);color:var(--t);border-radius:var(--rsm);padding:9px 12px;font-family:var(--body);font-size:14px}
.nav{display:flex;gap:10px;margin:18px 0}.nav .btn{flex:1;text-align:center;padding:11px}.k{font-family:var(--mono);font-size:10px;color:var(--tf);margin-left:5px}
table{width:100%;border-collapse:collapse;margin:10px 0}td,th{padding:7px 10px;border-bottom:1px solid var(--b);text-align:left}th{font-family:var(--mono);font-size:10px;letter-spacing:0.04em;text-transform:uppercase;color:var(--tm);font-weight:500}td{font-family:var(--mono);font-size:13px;font-variant-numeric:tabular-nums;color:var(--t2)}td:first-child{font-family:var(--body);color:var(--t)}
h2{font-family:var(--serif);font-size:26px;font-weight:400;letter-spacing:-0.01em;margin:2px 0 12px}h3{font-family:var(--disp);font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:var(--tm);margin:22px 0 8px}.hide{display:none}
.pill{display:inline-block;border-radius:6px;padding:2px 9px;font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:0.03em;text-transform:uppercase}.pill.go{background:rgba(40,200,64,0.15);color:var(--green)}.pill.wip{background:rgba(228,89,51,0.15);color:var(--orange)}.pill.next{background:rgba(30,51,134,0.3);color:var(--blue)}
.trail b{color:var(--t)}.trail li{margin:4px 0;color:var(--t2)}.trail p{color:var(--tm)}
.t-over{display:flex;align-items:center;gap:12px;margin-top:16px}
.hyps{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.hyp{display:inline-block;font-size:12px;line-height:1.4;padding:6px 11px;border-radius:8px;border:1px solid var(--b);cursor:pointer;color:var(--t2);background:var(--surface);transition:all .15s var(--ease)}
.hyp:hover{border-color:var(--bh);color:var(--t)}.hyp b{font-family:var(--mono);font-size:9px;letter-spacing:0.04em;text-transform:uppercase}
.hyp.validada{border-color:rgba(40,200,64,0.3)}.hyp.validada b{color:var(--green)}
.hyp.aberta{border-color:rgba(228,89,51,0.3)}.hyp.aberta b{color:var(--orange)}
.hyp.refutada{opacity:0.55}.hyp.refutada b{color:var(--red)}
.nexts{margin:8px 0 0 18px;color:var(--t2)}.nexts li{margin:5px 0;padding-left:4px}
.block{border:1px solid var(--b);border-radius:10px;padding:14px 16px;margin-bottom:12px;background:var(--surface)}
.block-h{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:6px}.block-h b{font-family:var(--disp);font-size:14px}
.block-meta{font-family:var(--mono);font-size:10px;color:var(--tm);letter-spacing:0.04em;text-transform:uppercase}
.blockt{width:100%;border-collapse:collapse;margin:6px 0 10px}.blockt th{font-family:var(--mono);font-size:9px;text-transform:uppercase;color:var(--tm);text-align:left;padding:4px 8px;border-bottom:1px solid var(--b)}.blockt td{font-family:var(--mono);font-size:12px;color:var(--t2);padding:4px 8px;border-bottom:1px solid var(--b)}.blockt td:first-child{font-family:var(--body);color:var(--t)}
.block-l{margin:6px 0 0 18px;color:var(--t2)}.block-l li{margin:4px 0}
.block-next{margin-top:10px;font-size:13px;color:var(--t2)}.block-next b{color:var(--blue)}
.gput{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px}
.gput th{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:0.04em;color:var(--tm);text-align:left;padding:6px 8px;border-bottom:1px solid var(--b);white-space:nowrap}
.gput td{padding:8px;border-bottom:1px solid var(--b);color:var(--t2);vertical-align:top}.gput td b{color:var(--t);font-weight:600}
.gpufrac{color:var(--tm);font-size:12px}
#mapwrap{overflow-x:auto;overflow-y:hidden;padding:6px 0 14px;margin-top:6px}
#map{position:relative;min-width:920px}
.lane{position:relative;padding:16px 0;border-top:1px solid var(--b)}.lane:first-child{border-top:none}
.lane-head{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.lane-title{font-family:var(--disp);font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--t2);white-space:nowrap;min-width:210px}
.lane-bar{height:3px;background:rgba(255,255,255,0.06);border-radius:999px;width:90px;overflow:hidden}.lane-bar>i{display:block;height:100%;background:var(--t2);border-radius:999px;transition:width 0.9s var(--ease)}
.lane-pct{font-family:var(--mono);font-size:10px;color:var(--tm)}
.lane-row{display:grid;gap:14px;align-items:start;position:relative;z-index:1}.cell{min-width:0}
.node{background:var(--surface);border:1px solid var(--b);border-left:2px solid var(--bh);border-radius:10px;padding:11px 12px;cursor:pointer;transition:all 0.15s var(--ease)}
.node:hover{border-color:var(--bh);background:var(--surface-h);transform:translateY(-1px)}
.node.done{border-left-color:var(--green)}.node.wip{border-left-color:var(--orange)}.node.next{border-left-color:var(--blue)}.node.idea{border-left-color:var(--tf)}
.node-t{font-size:12px;font-weight:500;color:var(--t);line-height:1.25;margin-bottom:9px}
.node-bar{height:4px;background:rgba(255,255,255,0.07);border-radius:999px;overflow:hidden}.node-bar>i{display:block;height:100%;border-radius:999px;background:var(--t2);transition:width 0.9s var(--ease)}
.node.done .node-bar>i,.node-bar>i.done{background:var(--green)}.node.wip .node-bar>i,.node-bar>i.wip{background:var(--orange)}.node.next .node-bar>i,.node-bar>i.next{background:var(--blue)}
.node-meta{display:flex;align-items:center;gap:6px;margin-top:8px;font-family:var(--mono);font-size:9px;letter-spacing:0.04em;text-transform:uppercase;color:var(--tm)}
.node-meta .dot{width:5px;height:5px;border-radius:50%;background:var(--tf)}
.node.done .dot{background:var(--green)}.node.wip .dot{background:var(--orange)}.node.next .dot{background:var(--blue)}
svg.edges{position:absolute;inset:0;pointer-events:none;z-index:0;overflow:visible}.edge{fill:none;stroke:rgba(245,245,247,0.13);stroke-width:1.5}
.usergrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin-top:12px}
.usercard{background:var(--surface);border:1px solid var(--b);border-radius:var(--rsm);padding:16px;cursor:pointer;transition:all .18s var(--ease)}
.usercard:hover{background:var(--surface-h);border-color:var(--bh);transform:translateY(-1px)}
.usern{font-size:15px;font-weight:600;color:var(--t);margin-bottom:6px}
.usermeta{font-size:12px;color:var(--t2)}.usermeta b{color:var(--orange);font-size:14px}
.avbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.btn.mini{font-size:11px;padding:5px 11px}
.dots{display:flex;flex-wrap:wrap;gap:5px;margin:14px 2px 0}
.pdot{width:8px;height:8px;border-radius:999px;background:var(--tf);cursor:pointer;transition:all .15s var(--ease)}.pdot:hover{transform:scale(1.3)}.pdot.done{background:var(--green)}.pdot.cur{outline:1px solid var(--t);outline-offset:2px}
.panelbg{position:fixed;inset:0;background:rgba(0,0,0,0.5);opacity:0;pointer-events:none;transition:opacity 0.22s var(--ease);z-index:55}.panelbg.open{opacity:1;pointer-events:auto}
.panel{position:fixed;top:0;right:0;width:min(440px,94vw);height:100vh;background:var(--bg);border-left:1px solid var(--bh);padding:26px 26px 60px;overflow-y:auto;transform:translateX(100%);transition:transform 0.28s var(--ease);z-index:60}.panel.open{transform:none}
.panel-x{position:absolute;top:18px;right:18px;background:var(--surface);border:1px solid var(--b);color:var(--t2);width:30px;height:30px;border-radius:8px;cursor:pointer;font-size:13px}.panel-x:hover{color:var(--t);border-color:var(--bh)}
.panel h3.pt{font-family:var(--serif);font-size:26px;font-weight:400;margin:12px 0 0;letter-spacing:-0.01em}.panel .psum{color:var(--t2);font-size:14px;margin:14px 0}
.panel .deep{color:var(--t2);font-size:14px;line-height:1.65}.panel .deep p{margin:9px 0}.panel .deep b{color:var(--t)}.panel .deep code{font-family:var(--mono);font-size:12px;background:var(--surface-h);padding:1px 5px;border-radius:4px;color:var(--t)}.panel .deep ul{margin:9px 0 9px 18px}.panel .deep li{margin:4px 0}
.panel .hyp{display:block;margin:7px 0;cursor:default}
.links{display:flex;flex-wrap:wrap;gap:7px}.linknode{font-size:12px;padding:5px 10px;border-radius:7px;border:1px solid var(--b);background:var(--surface);color:var(--t2);cursor:pointer}.linknode:hover{border-color:var(--bh);color:var(--t)}
.wave{position:relative;width:100%;height:64px;margin:12px 0 6px;background:rgba(255,255,255,0.02);border:1px solid var(--b);border-radius:var(--rsm);overflow:hidden;cursor:crosshair;user-select:none;-webkit-user-select:none}
.wave canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
.playhead{position:absolute;top:0;bottom:0;width:1.5px;background:var(--orange);left:0;pointer-events:none;z-index:4}
.sel{position:absolute;top:0;height:100%;background:rgba(228,89,51,0.22);border-left:1.5px solid var(--orange);border-right:1.5px solid var(--orange);pointer-events:none;z-index:2;display:none}
#pins{position:absolute;inset:0;pointer-events:none;z-index:3}
.pin{position:absolute;top:0;height:100%;min-width:2px;background:rgba(199,48,45,0.16);border-left:2px solid var(--red);pointer-events:auto;cursor:pointer}
.pin::after{content:'';position:absolute;top:-2px;left:-3px;width:8px;height:8px;border-radius:50%;background:var(--red)}
.pin.sev-grave{border-left-color:var(--red);background:rgba(199,48,45,0.18)}.pin.sev-grave::after{background:var(--red)}
.pin.sev-medio{border-left-color:var(--orange);background:rgba(228,89,51,0.16)}.pin.sev-medio::after{background:var(--orange)}
.pin.sev-leve{border-left-color:var(--tm);background:rgba(245,245,247,0.07)}.pin.sev-leve::after{background:var(--tm)}
.sevb{font-family:var(--mono);font-size:9px;letter-spacing:0.04em;text-transform:uppercase;padding:2px 6px;border-radius:5px;border:1px solid var(--b);white-space:nowrap}
.sevb.grave{color:var(--red);border-color:rgba(199,48,45,0.4)}.sevb.medio{color:var(--orange);border-color:rgba(228,89,51,0.4)}.sevb.leve{color:var(--tm)}
.markbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:6px 0}
.msel,.mnote{background:rgba(255,255,255,0.02);border:1px solid var(--b);color:var(--t);border-radius:var(--rsm);padding:7px 10px;font-family:var(--body);font-size:13px}
.mnote{flex:1;min-width:220px}
.mlist{margin-top:2px}
.mrow{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--b);font-size:13px}
.mt{font-family:var(--mono);font-size:12px;color:var(--orange);cursor:pointer;min-width:54px}
.mtg{font-family:var(--mono);font-size:9px;letter-spacing:0.04em;text-transform:uppercase;color:var(--t2);background:var(--surface);border:1px solid var(--b);border-radius:5px;padding:2px 7px;white-space:nowrap}
.mnt{flex:1;color:var(--t2)}
.mx{color:var(--tm);cursor:pointer}.mx:hover{color:var(--red)}
.werbox{margin:12px 0;background:rgba(255,255,255,0.02);border:1px solid var(--b);border-radius:var(--rsm);padding:11px 13px}
.werh{font-size:12px;color:var(--t2);margin-bottom:8px}
.werwords{font-size:15px;line-height:1.95}.werwords .w{padding:1px 2px;border-radius:3px}
.werwords .sub{color:var(--orange);border-bottom:2px solid var(--orange);cursor:help}
.werwords .del{color:var(--red);text-decoration:line-through;cursor:help}
.werwords .ins{color:var(--blue);cursor:help}
.metrics{display:flex;gap:24px;align-items:baseline;flex-wrap:wrap;margin:4px 0 12px}
.metric{display:flex;flex-direction:column;gap:2px}
.metric>b{font-family:var(--mono);font-size:9px;letter-spacing:0.05em;text-transform:uppercase;color:var(--tm)}
.mbig{font-family:var(--mono);font-size:23px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1}
.mv{font-family:var(--mono);font-size:15px;color:var(--t)}.mv .warn{color:var(--orange);font-style:normal;font-size:11px}
.werwords{margin:10px 0}
.transport{display:flex;align-items:center;gap:12px;margin:10px 0 2px}
.playbtn{width:40px;height:40px;border-radius:50%;background:var(--t);color:var(--bg);border:none;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:transform .12s var(--ease)}.playbtn:hover{transform:scale(1.06)}
.ptime{font-family:var(--mono);font-size:13px;color:var(--t2)}
.loophint{font-family:var(--mono);font-size:10px;color:var(--tm);letter-spacing:0.04em}
.selhint{font-size:12px;color:var(--tm);margin:2px 0 8px}
.markbar{flex-wrap:nowrap}
#mtag{max-width:230px;flex-shrink:0}
.mnote{min-width:90px}
.sevwrap{display:flex;align-items:center;gap:7px;white-space:nowrap;flex-shrink:0}
.sevcap{font-family:var(--mono);font-size:9px;letter-spacing:0.04em;text-transform:uppercase;color:var(--tm)}
.sevsl{width:88px;accent-color:var(--orange);cursor:pointer}
.sevval{font-family:var(--mono);font-size:14px;color:var(--orange);width:14px;text-align:center}
.btn.mark{background:var(--orange);color:#fff;border-color:var(--orange);font-weight:600;white-space:nowrap;flex-shrink:0}.btn.mark:hover{filter:brightness(1.12);border-color:var(--orange);color:#fff}
.btn.mark .ent{font-family:var(--mono);font-size:11px;opacity:0.85;margin-left:3px}
.mrow{gap:8px}
.mrowsel{max-width:215px;font-size:12px;padding:5px 8px;flex-shrink:0}
.msev2{width:46px;text-align:center;font-size:12px;padding:5px 4px;flex-shrink:0}.msev2.grave{color:var(--red)}.msev2.medio{color:var(--orange)}.msev2.leve{color:var(--tm)}
.mnt2{flex:1;min-width:70px;background:rgba(255,255,255,0.02);border:1px solid var(--b);color:var(--t2);border-radius:6px;padding:5px 8px;font-size:13px;font-family:var(--body)}
.tagpick{margin:6px 0 4px}
.taggroup{margin-bottom:4px}
.tghead{font-family:var(--mono);font-size:10px;letter-spacing:0.05em;text-transform:uppercase;color:var(--tm);cursor:pointer;user-select:none;padding:3px 0}
.tghead:hover{color:var(--t2)}.tgcaret{display:inline-block;width:12px;color:var(--tm)}
.tgchips{display:flex;flex-wrap:wrap;gap:5px;padding:3px 0 4px}.tgchips.hide{display:none}
.tchip{font-size:11px;padding:4px 9px;border-radius:999px;border:1px solid var(--b);background:var(--surface);color:var(--t2);cursor:pointer;transition:all .12s var(--ease);white-space:nowrap}
.tchip:hover{border-color:var(--bh);color:var(--t)}
.tchip.on{background:var(--orange);color:#fff;border-color:var(--orange);font-weight:500}
.tchip.add{border-style:dashed;color:var(--tm)}.tchip.add:hover{color:var(--t)}
.tagsel{font-size:12px;color:var(--t2);margin:4px 0 2px}.tagsel b{color:var(--t)}
.sidenav{position:fixed;top:50%;transform:translateY(-50%);width:48px;height:148px;background:rgba(20,20,24,0.55);border:1px solid var(--b);color:var(--t2);font-size:30px;cursor:pointer;z-index:45;display:flex;align-items:center;justify-content:center;font-family:var(--body);transition:all .15s var(--ease);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.sidenav:hover{background:var(--surface-h);color:var(--t);border-color:var(--bh)}
.sidenav.left{left:0;border-left:none;border-radius:0 16px 16px 0}.sidenav.right{right:0;border-right:none;border-radius:16px 0 0 16px}
.sidenav.hide{display:none}.sidenav.off{opacity:0.18;pointer-events:none}
@keyframes shake{0%,100%{transform:translateX(0)}20%,60%{transform:translateX(-5px)}40%,80%{transform:translateX(5px)}}
.card.pulse{animation:shake .34s var(--ease);border-color:var(--orange)}
.mrow.on{background:rgba(228,89,51,0.1);box-shadow:inset 2px 0 0 var(--orange);border-radius:6px}.mrow.on .mt{font-weight:600}
.modalbg{position:fixed;inset:0;background:rgba(0,0,0,0.55);opacity:0;pointer-events:none;transition:opacity .2s var(--ease);z-index:70}.modalbg.open{opacity:1;pointer-events:auto}
.modal{position:fixed;top:50%;left:50%;transform:translate(-50%,-46%);width:min(400px,92vw);background:#15161c;border:1px solid var(--bh);border-radius:16px;padding:24px;z-index:71;opacity:0;pointer-events:none;transition:all .22s var(--ease);box-shadow:0 24px 70px rgba(0,0,0,0.55)}
.modal.open{opacity:1;pointer-events:auto;transform:translate(-50%,-50%)}
.modal-t{font-family:var(--serif);font-size:22px;margin-bottom:16px}
.modal-in{width:100%;background:rgba(255,255,255,0.03);border:1px solid var(--b);color:var(--t);border-radius:8px;padding:11px 13px;font-size:14px;font-family:var(--body)}.modal-in:focus{outline:none;border-color:var(--bh)}
.modal-btns{display:flex;gap:8px;justify-content:flex-end;margin-top:18px}
.curtext{width:100%;min-height:72px;background:rgba(255,255,255,0.02);border:1px solid var(--b);color:var(--t);border-radius:var(--rsm);padding:10px 12px;font-family:var(--body);font-size:15px;line-height:1.5;resize:vertical}.curtext:focus{outline:none;border-color:var(--bh)}
.curcmp{margin:10px 0;font-size:13px;color:var(--t2);line-height:1.7}.curcmp .curlbl{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:0.04em;color:var(--tm);margin-right:4px}
.btn.mini{font-size:11px;padding:3px 8px}
.toast{position:fixed;bottom:26px;left:50%;transform:translateX(-50%) translateY(16px);background:rgba(18,18,22,0.92);border:1px solid var(--bh);color:var(--t);padding:8px 16px;border-radius:999px;font-family:var(--mono);font-size:11px;letter-spacing:0.04em;opacity:0;transition:all 0.25s var(--ease);pointer-events:none;z-index:50;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
/* ---- Onde estamos vs Maya (scorecard brutal) ---- */
.gapcard{border-color:rgba(199,48,45,0.28);background:linear-gradient(180deg,rgba(199,48,45,0.04),var(--surface))}
.gapmedia{display:flex;align-items:baseline;gap:8px;margin:10px 0 18px;flex-wrap:wrap}
.gapbig{font-family:var(--serif);font-size:52px;line-height:0.9;color:var(--orange)}
.gapof{font-size:18px;color:var(--tm)}
.gapver{font-size:13px;color:var(--t2);margin-left:10px;line-height:1.45;flex:1;min-width:200px}
.gaprow{display:flex;align-items:center;gap:10px;margin:8px 0;font-size:12px}
.gaplbl{width:130px;color:var(--t2);flex-shrink:0;text-align:right}
.gapbar{width:130px;height:5px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;flex-shrink:0}
.gapbar>i{display:block;height:100%;background:linear-gradient(90deg,var(--red),var(--orange))}
.gapscore{font-family:var(--mono);font-size:11px;color:var(--t);width:40px;flex-shrink:0}
.gapnota{font-size:11px;color:var(--tm);line-height:1.4}
.gapreal{font-size:12.5px;color:var(--t2);line-height:1.65;margin-top:16px;padding-top:14px;border-top:1px solid var(--b)}
.gapreal::before{content:'realismo — ';font-family:var(--mono);font-size:10px;letter-spacing:0.06em;text-transform:uppercase;color:var(--red)}
.blockers{list-style:none;margin-top:6px}.blockers li{font-size:12px;color:var(--t2);line-height:1.5;padding-left:18px;position:relative;margin:5px 0}
.blockers li::before{content:'⛔';position:absolute;left:0;font-size:10px}
/* ---- Trilha redesign: compacto/visual ---- */
.tweethd{display:flex;align-items:center;gap:14px;margin-bottom:6px}.tweethd h2{margin:0}
.tweet{font-family:var(--serif);font-size:19px;line-height:1.4;color:var(--t2)}
.collapse{max-height:0;overflow:hidden;transition:max-height .35s var(--ease)}.collapse.open{max-height:1600px;margin-top:10px}
.gaprows{margin-top:8px}.gaprow{cursor:default}.gapbtn{margin-top:12px}
.fases{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin-top:12px}
.fase{background:var(--surface);border:1px solid var(--b);border-top:2px solid var(--blue);border-radius:var(--rsm);padding:12px;cursor:pointer;transition:all .18s var(--ease)}
.fase:hover{background:var(--surface-h)}.fasen{font-size:12px;font-weight:600;color:var(--t)}
.faseb{font-size:11px;color:var(--tm);line-height:1.45;margin-top:6px;max-height:30px;overflow:hidden;transition:max-height .3s var(--ease)}
.fase.open .faseb{max-height:420px;color:var(--t2)}
.blgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:10px;margin-top:12px}
.blcard{background:rgba(199,48,45,.05);border:1px solid rgba(199,48,45,.25);border-radius:var(--rsm);padding:12px;cursor:pointer;transition:all .18s var(--ease)}
.blcard:hover{background:rgba(199,48,45,.09)}.blt{font-size:12px;font-weight:500;color:var(--t);line-height:1.4}
.blb{font-size:11px;color:var(--tm);line-height:1.5;max-height:0;overflow:hidden;transition:max-height .3s var(--ease)}
.blcard.open .blb{max-height:420px;margin-top:7px}
.gplan{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:10px;margin-top:12px}
.gcard{background:var(--surface);border:1px solid var(--b);border-radius:var(--rsm);padding:12px;cursor:pointer;transition:all .18s var(--ease)}.gcard:hover{background:var(--surface-h)}
.gtop{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.glabel{font-size:12.5px;font-weight:600;color:var(--t)}.gcost{font-family:var(--mono);font-size:11px;color:var(--green)}
.gbar{height:6px;background:rgba(255,255,255,.06);border-radius:99px;overflow:hidden;margin:9px 0 5px}.gbar>i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--orange))}
.ghours{font-family:var(--mono);font-size:10px;color:var(--tm)}
.gdetail{font-size:11px;color:var(--tm);line-height:1.55;max-height:0;overflow:hidden;transition:max-height .3s var(--ease)}.gcard.open .gdetail{max-height:240px;margin-top:8px}
.kpi{display:inline-block;font-family:var(--mono);font-size:10px;color:var(--t2);background:var(--surface-h);border:1px solid var(--b);border-radius:6px;padding:2px 7px;margin-left:6px}
.block-h{cursor:pointer}.blockbody{max-height:0;overflow:hidden;transition:max-height .4s var(--ease)}.block.open .blockbody{max-height:1200px;margin-top:10px}
.insbox h3{font-size:12px;margin:14px 0 6px;color:var(--t2)}
/* ---- Hipóteses kanban ---- */
.kanban{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}
@media(max-width:920px){.kanban{grid-template-columns:repeat(2,1fr)}}
.kcol{background:rgba(255,255,255,0.012);border:1px solid var(--b);border-radius:var(--rsm);padding:10px}
.khead{font-family:var(--mono);font-size:10px;letter-spacing:0.06em;text-transform:uppercase;color:var(--tm);margin-bottom:9px;display:flex;align-items:center;gap:6px}
.kcount{background:var(--surface-h);border-radius:99px;padding:1px 7px;font-size:10px;color:var(--t2)}
.kcol.kv .khead{color:var(--green)}.kcol.kp .khead{color:var(--orange)}.kcol.ka .khead{color:var(--blue)}.kcol.kr .khead{color:var(--tm)}
.kcard{background:var(--surface);border:1px solid var(--b);border-left:2px solid var(--bh);border-radius:8px;padding:10px 11px;margin-bottom:8px;cursor:pointer;transition:all 0.18s var(--ease)}
.kcard:last-child{margin-bottom:0}
.kcard:hover{background:var(--surface-h);border-color:var(--bh)}
.kcard.kv{border-left-color:var(--green)}.kcard.kp{border-left-color:var(--orange)}.kcard.ka{border-left-color:var(--blue)}.kcard.kr{border-left-color:var(--red);opacity:0.62}
.kcard.kr:hover{opacity:0.85}
.kclaim{font-size:12.5px;font-weight:500;line-height:1.4;color:var(--t);display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
.kclaim .kchev{color:var(--tm);font-size:10px;flex-shrink:0;transition:transform 0.2s var(--ease)}
.kcard.open .kchev{transform:rotate(90deg)}
.kcard.kr .kclaim{text-decoration:line-through;text-decoration-color:rgba(199,48,45,0.5)}
.kev{font-size:11px;color:var(--tm);margin-top:5px;line-height:1.45}
.kdetail{max-height:0;overflow:hidden;transition:max-height 0.3s var(--ease)}
.kcard.open .kdetail{max-height:680px;margin-top:9px;padding-top:9px;border-top:1px solid var(--b)}
.kdetail p{margin:5px 0;font-size:11.5px;color:var(--t2);line-height:1.55}
.kdetail ul{margin:5px 0 5px 15px}.kdetail li{font-size:11.5px;color:var(--t2);line-height:1.5}
.kdetail code{font-family:var(--mono);font-size:10.5px;background:rgba(255,255,255,0.05);padding:1px 4px;border-radius:4px}
.kdetail .linknode{margin-top:6px}
</style></head><body>
<header><h1>🎧 TTS pt-BR</h1>
<button class="tab on" id=tGr onclick=view('gr')>Gravar</button>
<button class=tab id=tCu onclick=view('cu')>Curar</button>
<button class=tab id=tAv onclick=view('av')>Avaliar</button>
<button class=tab id=tTr onclick=view('tr')>Trilha</button>
<div class=bar><i id=prog></i></div><span class=muted id=cnt></span><div class=sp></div></header>
<div class=wrap>
<div id=av class=hide><div class=avbar><button class="btn mini" id=todobtn onclick=toggleTodo()>só os que faltam</button><button class="btn mini" onclick=nextTodo()>⏭ pular pro próximo que falta</button></div><div class=card id=card></div>
<div id=dots class=dots></div></div>
<div id=tr class=hide></div>
<div id=cu class=hide></div>
<div id=gr></div>
</div>
<div id=toast class=toast></div>
<button class="sidenav left hide" id=navL onclick=goPrev() title="áudio anterior">‹</button>
<button class="sidenav right hide" id=navR onclick=goNext() title="próximo áudio">›</button>
<div id=panelbg class=panelbg onclick=closePanel()></div>
<div id=panel class=panel></div>
<div id=tagmodalbg class=modalbg onclick=closeTagModal()></div>
<div id=tagmodal class=modal><div class=modal-t>Nova tag de erro</div><input id=tagmodalin class=modal-in placeholder="ex: vogal cortada, estalo, respiração" onkeydown="if(event.key=='Enter'){event.preventDefault();submitTag();}else if(event.key=='Escape'){closeTagModal();}"><div class=modal-btns><button class=btn onclick=closeTagModal()>cancelar</button><button class="btn mark" onclick=submitTag()>adicionar</button></div></div>
<script>
let clips=[],ratings={},i=0;
let MAP={nodes:[],lanes:[],hypotheses:[],state:{now:'',next:[]}};
let CUR=[],ci=0;
const _sq={};
const K=(r,id)=>r+'|'+id;
const NUM=[1,2,3,4,5];
const PROBS=["palavra errada (WER)","sotaque gringo","fonema errado","entonação robótica","cortou/incompleto","ruído/chiado","emoção errada","repetiu","rápido/devagar","metálico/artefato"];
const PTBR=["R forte /ʁ/ virou fraco","vogal nasal sem nasalizar (ã/õ/em)","ti/di sem palatal (tchi/dji)","S coda sem chiado carioca","L coda virou /l/ (não /w/)","vogal aberta/fechada (ó/ô,é/ê)","lh/nh sem palatal","ão/ditongo nasal errado","sílaba tônica errada","ritmo silábico de gringo"];
let CUSTOM=[];try{CUSTOM=JSON.parse(localStorage.getItem('customtags')||'[]');}catch(e){}
try{window._drafts=JSON.parse(localStorage.getItem('drafts')||'{}');}catch(e){window._drafts={};}window._tgOpen={geral:true,ptbr:false};window._selTag="palavra errada (WER)";
async function boot(){clips=await(await fetch('/api/clips')).json();ratings=await(await fetch('/api/ratings')).json();try{MAP=await(await fetch('/api/map')).json();}catch(e){}try{const last=localStorage.getItem('lastclip');if(last){const idx=clips.findIndex(function(c){return K(c.run,c.id)===last;});if(idx>=0)i=idx;}}catch(e){}renderTrail();render();view('gr');}
let onlyTodo=false;
function toggleTodo(){onlyTodo=!onlyTodo;const b=document.getElementById('todobtn');if(b)b.classList.toggle('on',onlyTodo);if(onlyTodo&&cur()&&isComplete(cur()))nextTodo();else{renderDots();updateCount();}flash(onlyTodo?'filtrando: só os que faltam':'mostrando todos');}
function nextTodo(){for(let k=1;k<=clips.length;k++){const idx=(i+k)%clips.length;if(!isComplete(clips[idx])){jump(idx);return;}}flash('tudo avaliado ✓');}
function cur(){return clips[i];}
function rOf(c){return ratings[K(c.run,c.id)]||{};}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function sevInfo(s){
 if(typeof s==='number'){const b=s<=2?'leve':(s<=3?'medio':'grave');return {n:s,bucket:b,label:s+'/5'};}
 const map={leve:1,'médio':3,medio:3,grave:5};const n=map[s]||3;const b=n<=2?'leve':(n<=3?'medio':'grave');return {n:n,bucket:b,label:(s||'médio')};
}
function tagOpts(sel){const ger=PROBS.concat(['pausa estranha','ênfase errada']).concat(CUSTOM);return '<optgroup label="geral">'+ger.map(function(p){return '<option'+(p===sel?' selected':'')+'>'+esc(p)+'</option>';}).join('')+'</optgroup><optgroup label="fonema pt-BR">'+PTBR.map(function(p){return '<option'+(p===sel?' selected':'')+'>'+esc(p)+'</option>';}).join('')+'</optgroup>';}
function setTag(t){window._selTag=t;renderTagPicker();saveDraft();}
function addCustomTag(){const bg=document.getElementById('tagmodalbg'),m=document.getElementById('tagmodal'),inp=document.getElementById('tagmodalin');if(inp)inp.value='';if(bg)bg.classList.add('open');if(m)m.classList.add('open');if(inp)setTimeout(function(){inp.focus();},60);}
function closeTagModal(){const bg=document.getElementById('tagmodalbg'),m=document.getElementById('tagmodal');if(bg)bg.classList.remove('open');if(m)m.classList.remove('open');}
function submitTag(){const inp=document.getElementById('tagmodalin');const t=(inp?inp.value:'').trim();if(!t){closeTagModal();return;}if(CUSTOM.indexOf(t)<0){CUSTOM.push(t);try{localStorage.setItem('customtags',JSON.stringify(CUSTOM));}catch(e){}}window._selTag=t;closeTagModal();renderTagPicker();saveDraft();}
function toggleGroup(g){window._tgOpen[g]=!window._tgOpen[g];renderTagPicker();}
function renderTagPicker(){const el=document.getElementById('tagpick');if(!el)return;
 const ger=PROBS.concat(['pausa estranha','ênfase errada']).concat(CUSTOM);
 function chips(list){return list.map(function(t){return '<span class="tchip'+(t===window._selTag?' on':'')+'" data-t="'+esc(t)+'" onclick="setTag(this.dataset.t)">'+esc(t)+'</span>';}).join('');}
 el.innerHTML='<div class=taggroup><div class=tghead onclick="toggleGroup(\'geral\')"><span class=tgcaret>'+(window._tgOpen.geral?'▾':'▸')+'</span> geral</div><div class="tgchips'+(window._tgOpen.geral?'':' hide')+'">'+chips(ger)+'<span class="tchip add" onclick="addCustomTag()">+ tag</span></div></div>'+
  '<div class=taggroup><div class=tghead onclick="toggleGroup(\'ptbr\')"><span class=tgcaret>'+(window._tgOpen.ptbr?'▾':'▸')+'</span> fonema pt-BR (onde o gringo erra)</div><div class="tgchips'+(window._tgOpen.ptbr?'':' hide')+'">'+chips(PTBR)+'</div></div>'+
  '<div class=tagsel>tipo: <b>'+esc(window._selTag||'—')+'</b></div>';
}
function saveDraft(){const c=cur();if(!c)return;const mn=document.getElementById('mnote'),sv=document.getElementById('msev');const note=mn?mn.value:'';const sev=sv?+sv.value:3;if(window._mStart==null&&!note){delete window._drafts[K(c.run,c.id)];}else{window._drafts[K(c.run,c.id)]={tag:window._selTag,sev:sev,note:note,mStart:window._mStart,mEnd:window._mEnd};}persistDrafts();}
function restoreDraft(c){const d=window._drafts[K(c.run,c.id)];if(!d)return;if(d.tag)window._selTag=d.tag;const sv=document.getElementById('msev');if(sv&&d.sev){sv.value=d.sev;const sl=document.getElementById('sevval');if(sl)sl.textContent=d.sev;}const mn=document.getElementById('mnote');if(mn&&d.note)mn.value=d.note;if(d.mStart!=null){window._mStart=d.mStart;window._mEnd=d.mEnd;renderSel();}}
function jump(idx){saveDraft();i=Math.max(0,Math.min(clips.length-1,idx));render();setTimeout(playFresh,140);}
function reqFields(c){const isVoz=c.run.includes('stage')||c.run.includes('pedro')||c.run.includes('voz');const f=[['geral','nota geral'],['nativo','soa nativo'],['natural','naturalidade'],['parou','parou'],['carioca','sotaque']];if(isVoz)f.push(['voz','soa como Pedro']);return f;}
function filled(r,k){const v=r[k];return v!==undefined&&v!==null&&v!=='';}
function missingReq(c){const r=rOf(c);return reqFields(c).filter(function(f){return !filled(r,f[0]);}).map(function(f){return f[1];});}
function isComplete(c){return missingReq(c).length===0;}
function pulseCard(){const el=document.getElementById('card');if(!el)return;el.classList.remove('pulse');void el.offsetWidth;el.classList.add('pulse');setTimeout(function(){el.classList.remove('pulse');},420);}
function goPrev(){go(-1);}
function goNext(){const c=cur();if(!c)return;const miss=missingReq(c);if(miss.length){flash('pra avançar, preencha: '+miss.join(', '));pulseCard();return;}go(1);}
function persistDrafts(){try{localStorage.setItem('drafts',JSON.stringify(window._drafts));}catch(e){}}
function werMetrics(c){
 const dur=c.dur_s!=null?(c.dur_s.toFixed(1)+'s'):'?';const cap=c.dur_s!=null&&c.dur_s>=12.7;
 const wer=c.wer!=null?Math.round(c.wer*100)+'%':'—';
 const wcol=c.wer==null?'var(--t2)':(c.wer<=0.1?'var(--green)':(c.wer<=0.3?'var(--orange)':'var(--red)'));
 const nerr=(c.wer_ops&&c.wer_ops.length)?c.wer_ops.filter(function(o){return o.op!=='ok';}).length:null;
 return `<div class=metrics><span class=metric><b>WER</b><span class=mbig style="color:${wcol}">${wer}</span></span><span class=metric><b>duração</b><span class=mv>${dur}${cap?' <i class=warn>no teto!</i>':''}</span></span>${nerr!=null?`<span class=metric><b>erros de palavra</b><span class=mv>${nerr}</span></span>`:''}</div>`;
}
function werWords(ops){
 const ws=ops.map(function(o){
  if(o.op=='ok')return `<span class=w>${esc(o.ref)}</span>`;
  if(o.op=='sub')return `<span class="w sub" title="ASR ouviu: ${esc(o.hyp)}">${esc(o.ref)}</span>`;
  if(o.op=='del')return `<span class="w del" title="o modelo não falou">${esc(o.ref)}</span>`;
  return `<span class="w ins" title="o modelo falou a mais">+${esc(o.hyp)}</span>`;
 }).join(' ');
 return `<div class=werwords title="ref vs ASR — laranja=troca · riscado=omissão · azul=a mais">${ws}</div>`;
}
function scale(field,r,lo,hi){return `<div class=ihead><b>${field.label}</b><span class=exp>${field.exp}</span></div>`+NUM.map(n=>`<button class="btn ${r[field.k]==n?'on':''}" onclick="setv('${field.k}',${n})">${n}</button>`).join('')+`<span class=exp>${lo} → ${hi}</span>`;}
function render(){
 const c=cur();if(!c){document.getElementById('card').innerHTML='Nenhum áudio em runpod_samples/.';return;}
 const miss=missingReq(c);const done=miss.length===0;
 let h=`<div class=tags><span>${c.run}</span><span>${c.id}</span><span>${c.emotion}</span><span>${c.accent}</span>${done?'<span style="border-color:var(--green);color:var(--green)">✓ completo</span>':'<span style="border-color:var(--orange);color:var(--orange)">○ falta: '+esc(miss.join(', '))+'</span>'}</div>
 ${werMetrics(c)}
 <div class=text>${esc(c.text)}</div>
 ${c.wer_ops&&c.wer_ops.length?werWords(c.wer_ops):(c.hyp?`<div class=hyp>ASR ouviu: "${esc(c.hyp)}"</div>`:'')}
 <audio id=au src="/audio?run=${encodeURIComponent(c.run)}&id=${encodeURIComponent(c.id)}" preload=auto style="display:none"></audio>
 <div class=transport><button id=playbtn class=playbtn onclick=togglePlay()>▶</button><span id=ptime class=ptime>0:00 / 0:00</span><span class=loophint>↻ loop até pausar</span></div>
 <div class=wave id=wave><canvas id=wc></canvas><div id=sel class=sel></div><div id=ph class=playhead></div><div id=pins></div></div>
 <div id=mtime class=selhint>arraste na onda pra marcar o trecho (início → fim) do erro · clique = vai pro ponto</div>
 <div class=tagpick id=tagpick></div>
 <div class=markbar>
  <div class=sevwrap><span class=sevcap>intensidade</span><input type=range id=msev min=1 max=5 value=3 class=sevsl oninput="document.getElementById('sevval').textContent=this.value;saveDraft()"><span id=sevval class=sevval>3</span></div>
  <input id=mnote class=mnote placeholder="esperado → ouvido (ex: R forte /ʁ/ → R fraco)" oninput="saveDraft()" onkeydown="if(event.key=='Enter'){event.preventDefault();addMarker();}">
  <button id=markbtn class="btn mark" onclick=addMarker()>📍 marcar trecho <span class=ent>↵</span></button></div>
 <div id=mlist class=mlist></div>
 <div id=ctrls></div>`;
 document.getElementById('card').innerHTML=h;
 setupWave(c);renderCtrls();updateCount();
 try{localStorage.setItem('lastclip',K(c.run,c.id));}catch(e){}
}
function renderCtrls(){
 const c=cur();if(!c)return;const r=rOf(c);
 const isVoz=c.run.includes('stage')||c.run.includes('pedro')||c.run.includes('voz');
 let h=`<div class=ind>`+scale({k:'geral',label:'Nota geral',exp:'impressão geral · teclas 1-5'},r,'1 ruim','5 perfeito')+`</div>`;
 h+=`<div class=ind>`+scale({k:'nativo',label:'Soa brasileiro nativo?',exp:'fonemas/sotaque de brasileiro, ou de gringo lendo pt?'},r,'1 gringo','5 nativo')+`</div>`;
 h+=`<div class=ind>`+scale({k:'natural',label:'Naturalidade',exp:'entonação/ritmo humano ou robótico?'},r,'1 robótico','5 humano')+`</div>`;
 if(isVoz)h+=`<div class=ind>`+scale({k:'voz',label:'Soa como o Pedro?',exp:'o timbre parece a tua voz?'},r,'1 nada','5 idêntico')+`</div>`;
 h+=`<div class=ind><div class=ihead><b>Parou certo?</b><span class=exp>parou na hora ou balbuciou? · tecla P</span></div>
 <button class="btn ok ${r.parou===true?'on':''}" onclick="setv('parou',true)">sim</button>
 <button class="btn no ${r.parou===false?'on':''}" onclick="setv('parou',false)">não, balbuciou</button></div>`;
 h+=`<div class=ind><div class=ihead><b>Sotaque carioca?</b><span class=exp>tem o sotaque/registro carioca?</span></div>
 <button class="btn ${r.carioca=='sim'?'on':''}" onclick="setv('carioca','sim')">carioca ✓</button>
 <button class="btn ${r.carioca=='nao'?'on':''}" onclick="setv('carioca','nao')">não</button></div>`;
 h+=`<div class=ind><div class=ihead><b>Problemas</b><span class=exp>marque tudo que ouviu — vira o ranking do que consertar</span></div>`+
   PROBS.map(p=>`<button class="btn fl ${(r.problemas||[]).includes(p)?'on':''}" onclick="togProb('${p}')">${p}</button>`).join('')+`</div>`;
 h+=`<div class=ind><div class=ihead><b>Nota livre</b><span class=exp>salva enquanto você digita · Enter pra confirmar</span></div><input type=text id=nota value="${esc(r.nota||'')}" oninput="saveNota(this.value)" onkeydown="if(event.key=='Enter'||event.key=='Escape'){event.preventDefault();this.blur();}" placeholder="observações..."></div>`;
 document.getElementById('ctrls').innerHTML=h;
}
let _audioCtx=null;
function audioCtx(){if(!_audioCtx){try{_audioCtx=new (window.AudioContext||window.webkitAudioContext)();}catch(e){}}return _audioCtx;}
function clipDur(){const a=document.getElementById('au');return (a&&a.duration&&isFinite(a.duration)&&a.duration>0)?a.duration:((cur()&&cur().dur_s)||1);}
function timeAt(e,w){const rc=w.getBoundingClientRect();const d=clipDur();return Math.max(0,Math.min(d,(e.clientX-rc.left)/rc.width*d));}
function setupWave(c){
 window._mStart=null;window._mEnd=null;window._mDrag=false;window._segLoop=null;clearTimeout(window._segTimer);
 const a=document.getElementById('au');
 if(a){a.loop=true;a.ontimeupdate=function(){updatePlayhead();updateTransport();segTick();};a.onplay=updateTransport;a.onpause=updateTransport;a.onloadedmetadata=updateTransport;}
 const w=document.getElementById('wave');
 if(w){
  w.onmousedown=function(e){e.preventDefault();stopSeg();window._downX=e.clientX;window._downT=timeAt(e,w);window._mDrag=true;window._marking=false;window._mStart=null;window._mEnd=null;const sl=document.getElementById('sel');if(sl)sl.style.display='none';if(a)a.currentTime=window._downT;updatePlayhead();};
  w.onmousemove=function(e){if(!window._mDrag)return;if(!window._marking&&Math.abs(e.clientX-window._downX)>6){window._marking=true;window._mStart=window._downT;}if(window._marking){window._mEnd=timeAt(e,w);renderSel();labelSel();}};
 }
 if(!window._selTag)window._selTag=PROBS[0];
 const sel=document.getElementById('sel');if(sel)sel.style.display='none';
 drawWave(c);renderPins();renderMarkerList();restoreDraft(c);renderTagPicker();labelSel();updateTransport();
}
function fmt(s){s=Math.max(0,s||0);const m=Math.floor(s/60),x=Math.floor(s%60);return m+':'+(x<10?'0':'')+x;}
function togglePlay(){const a=document.getElementById('au');if(!a)return;if(a.paused){const p=a.play();if(p)p.catch(function(){flash('clique na onda pra liberar o som');});}else{a.pause();clearTimeout(window._segTimer);}updateTransport();}
function updateTransport(){const a=document.getElementById('au'),pb=document.getElementById('playbtn'),pt=document.getElementById('ptime');if(a&&pb)pb.textContent=a.paused?'▶':'⏸';if(a&&pt)pt.textContent=fmt(a.currentTime)+' / '+fmt(clipDur());}
function endDrag(){if(!window._mDrag)return;window._mDrag=false;
 if(window._marking&&window._mStart!=null){
  if(window._mEnd<window._mStart){const t=window._mStart;window._mStart=window._mEnd;window._mEnd=t;}
  labelSel();saveDraft();
 }else{
  window._mStart=null;window._mEnd=null;const sel=document.getElementById('sel');if(sel)sel.style.display='none';labelSel();
 }
 window._marking=false;
}
function renderSel(){const el=document.getElementById('sel');if(!el||window._mStart==null)return;const d=clipDur();const a=Math.min(window._mStart,window._mEnd),b=Math.max(window._mStart,window._mEnd);el.style.left=(100*a/d)+'%';el.style.width=Math.max(0.4,100*(b-a)/d)+'%';el.style.display='block';}
function labelSel(){const mt=document.getElementById('mtime');if(!mt)return;if(window._mStart==null){mt.textContent='arraste na onda pra marcar o trecho (início → fim) do erro';return;}const a=Math.min(window._mStart,window._mEnd),b=Math.max(window._mStart,window._mEnd);mt.innerHTML='trecho: <b style="color:var(--orange)">'+a.toFixed(2)+'s → '+b.toFixed(2)+'s</b> ('+(b-a).toFixed(2)+'s) — escolha o tipo e marque';}
function updatePlayhead(){const a=document.getElementById('au'),ph=document.getElementById('ph');if(!a||!ph)return;ph.style.left=(100*(a.currentTime/clipDur()))+'%';}
async function drawWave(c){
 const cv=document.getElementById('wc');if(!cv)return;
 const W=Math.max(2,cv.clientWidth||600),H=cv.clientHeight||64;cv.width=W;cv.height=H;
 const ctx=cv.getContext('2d');ctx.clearRect(0,0,W,H);
 try{
  const ac=audioCtx();if(!ac)throw 0;
  const buf=await(await fetch('/audio?run='+encodeURIComponent(c.run)+'&id='+encodeURIComponent(c.id))).arrayBuffer();
  const ab=await ac.decodeAudioData(buf);
  if(cur()!==c)return;
  const data=ab.getChannelData(0);const step=Math.max(1,Math.floor(data.length/W));
  ctx.fillStyle='rgba(245,245,247,0.30)';
  for(let x=0;x<W;x++){let mn=1,mx=-1;for(let j=0;j<step;j++){const v=data[x*step+j]||0;if(v<mn)mn=v;if(v>mx)mx=v;}const y1=(1-(mx+1)/2)*H,y2=(1-(mn+1)/2)*H;ctx.fillRect(x,y1,1,Math.max(1,y2-y1));}
 }catch(e){ctx.strokeStyle='rgba(245,245,247,0.16)';ctx.beginPath();ctx.moveTo(0,H/2);ctx.lineTo(W,H/2);ctx.stroke();}
}
function curMarkers(){const c=cur();return c?(rOf(c).markers||[]):[];}
function addMarker(){
 if(window._mStart==null){flash('arraste na onda pra marcar o trecho');return;}
 const a=Math.min(window._mStart,window._mEnd),b=Math.max(window._mStart,window._mEnd);
 const c=cur();const r=rOf(c);const tag=window._selTag||PROBS[0];const note=document.getElementById('mnote').value;
 const sv=document.getElementById('msev');const sev=sv?(+sv.value):3;
 const m=(r.markers||[]).slice();m.push({t_start:Math.round(a*100)/100,t_end:Math.round(b*100)/100,tag:tag,sev:sev,note:note});m.sort(function(x,y){return x.t_start-y.t_start;});
 r.markers=m;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;
 const mn=document.getElementById('mnote');if(mn)mn.value='';
 window._mStart=null;window._mEnd=null;const sel=document.getElementById('sel');if(sel)sel.style.display='none';
 delete window._drafts[K(c.run,c.id)];persistDrafts();
 labelSel();renderPins();renderMarkerList();updateCount();flash('marcado ✓');queueSave(c,r);
}
function removeMarker(idx){const c=cur();const r=rOf(c);if(!r.markers)return;r.markers.splice(idx,1);r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;renderPins();renderMarkerList();updateCount();flash('removido');queueSave(c,r);}
function seekTo(t){const a=document.getElementById('au');if(a){a.currentTime=t;const p=a.play();if(p)p.catch(function(){});}}
function loopSeg(idx){const ms=curMarkers();const m=ms[idx];if(!m)return;const sp=mSpan(m);if(window._segLoop&&window._segLoop.idx===idx){stopSeg();return;}window._segLoop={start:sp[0],end:sp[1],idx:idx};const a=document.getElementById('au');if(a){a.loop=false;a.currentTime=sp[0];const p=a.play();if(p)p.catch(function(){});}renderMarkerList();updateTransport();}
function stopSeg(){if(!window._segLoop)return;window._segLoop=null;clearTimeout(window._segTimer);const a=document.getElementById('au');if(a)a.loop=true;renderMarkerList();}
function segTick(){const s=window._segLoop;if(!s)return;const a=document.getElementById('au');if(!a)return;if(a.currentTime>=s.end){a.pause();clearTimeout(window._segTimer);window._segTimer=setTimeout(function(){if(window._segLoop){const a2=document.getElementById('au');if(a2){a2.currentTime=window._segLoop.start;const p=a2.play();if(p)p.catch(function(){});}}},1000);}}
function mSpan(m){const a=m.t_start!=null?m.t_start:m.t;const b=m.t_end!=null?m.t_end:a;return [a,b];}
function renderPins(){const el=document.getElementById('pins');if(!el)return;const d=clipDur();el.innerHTML=curMarkers().map(function(m){const s=mSpan(m),a=s[0],b=s[1];const si=sevInfo(m.sev);return '<i class="pin sev-'+si.bucket+'" style="left:'+(100*a/d)+'%;width:'+Math.max(0.6,100*(b-a)/d)+'%" title="'+esc('['+si.label+'] '+m.tag+' @ '+a.toFixed(2)+'–'+b.toFixed(2)+'s'+(m.note?' — '+m.note:''))+'" onclick="seekTo('+a+')"></i>';}).join('');}
function updateMarker(idx,field,val){const c=cur();const r=rOf(c);if(!r.markers||!r.markers[idx])return;r.markers[idx][field]=(field==='sev'?(+val):val);r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;if(field==='sev')renderPins();flash('salvo ✓');queueSave(c,r);}
function renderMarkerList(){const el=document.getElementById('mlist');if(!el)return;const ms=curMarkers();el.innerHTML=ms.length?(`<div class=ihead style="margin-top:12px">Marcadores no tempo <span class=exp>${ms.length} — clique no tempo pra ouvir o trecho em loop (1s de descanso) · edite tipo/intensidade/nota</span></div>`+ms.map(function(m,idx){const s=mSpan(m),a=s[0],b=s[1];const si=sevInfo(m.sev);const on=window._segLoop&&window._segLoop.idx===idx;return `<div class="mrow${on?' on':''}"><span class=mt onclick="loopSeg(${idx})">${on?'↻ ':''}${a.toFixed(2)}–${b.toFixed(2)}s</span><select class="msel mrowsel" onchange="updateMarker(${idx},'tag',this.value)">${tagOpts(m.tag)}</select><select class="msev2 sevb ${si.bucket}" onchange="updateMarker(${idx},'sev',this.value)">`+[1,2,3,4,5].map(function(n){return `<option value=${n}${si.n===n?' selected':''}>${n}</option>`;}).join('')+`</select><input class=mnt2 value="${esc(m.note||'')}" oninput="updateMarker(${idx},'note',this.value)" placeholder="nota"><span class=mx onclick="removeMarker(${idx})">✕</span></div>`;}).join('')):'';}
function updateCount(){
 const rated=clips.filter(function(x){return isComplete(x);}).length;
 document.getElementById('cnt').textContent=`${i+1}/${clips.length} · ${rated} completos · ${clips.length-rated} faltam`;
 document.getElementById('prog').style.width=(clips.length?100*rated/clips.length:0)+'%';
 const nl=document.getElementById('navL'),nr=document.getElementById('navR');
 if(nl)nl.classList.toggle('off',i<=0);if(nr)nr.classList.toggle('off',i>=clips.length-1);
 renderDots();
}
function renderDots(){const el=document.getElementById('dots');if(!el)return;el.innerHTML=clips.map(function(c,idx){return '<i class="pdot'+(isComplete(c)?' done':'')+(idx==i?' cur':'')+'" title="'+esc(c.run+' · '+c.id)+'" onclick="jump('+idx+')"></i>';}).join('');}
async function save(r){await fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});}
function queueSave(c,r){const key=K(c.run,c.id);const prev=_sq[key]||Promise.resolve();const p=prev.then(function(){return save(Object.assign({},r));}).catch(function(){});_sq[key]=p;return p;}
function setv(k,v){const c=cur();const r=rOf(c);r[k]=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;renderCtrls();updateCount();flash('salvo ✓');queueSave(c,r);}
function saveNota(v){const c=cur();const r=rOf(c);r.nota=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;clearTimeout(window._nt);window._nt=setTimeout(function(){queueSave(c,r);},400);}
function flash(m){const t=document.getElementById('toast');if(!t)return;t.textContent=m;t.classList.add('show');clearTimeout(window._ft);window._ft=setTimeout(function(){t.classList.remove('show');},900);}
function togProb(p){const c=cur();const r=rOf(c);const a=r.problemas||[];const j=a.indexOf(p);if(j<0){a.push(p);}else{a.splice(j,1);}r.problemas=a;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;renderCtrls();flash('salvo ✓');queueSave(c,r);}
function go(d){saveDraft();let ni=i+d;if(onlyTodo){let k=0;while(ni>=0&&ni<clips.length&&isComplete(clips[ni])&&++k<=clips.length)ni+=d;}i=Math.max(0,Math.min(clips.length-1,ni));render();setTimeout(playFresh,140);}
function playFresh(){const a=document.getElementById('au');if(a){const p=a.play();if(p)p.catch(function(){});}}
let ALLCUR=[],curUser=null;
async function showCurate(){
 try{ALLCUR=await(await fetch('/api/curate')).json();}catch(e){ALLCUR=[];}
 if(!ALLCUR.length){document.getElementById('cu').innerHTML='<div class=card><div class=ihead>Curar</div><p class=muted>Nada pra curar ainda. O Whisper roda nas gravações da sala, quebra em frases e popula aqui — por pessoa. (O exemplo já curado aparece assim que houver dado.)</p></div>';return;}
 if(!curUser){renderCurPicker();return;}
 CUR=ALLCUR.filter(function(x){return (x.usuario||'?')===curUser;});
 ci=Math.max(0,Math.min(ci,CUR.length-1));renderCur();
}
function renderCurPicker(){
 const u={};ALLCUR.forEach(function(x){const k=x.usuario||'?';(u[k]=u[k]||{t:0,r:0});u[k].t++;if(x.edited)u[k].r++;});
 const cards=Object.keys(u).sort().map(function(k){const d=u[k];return `<div class=usercard onclick="pickUser('${k.replace(/'/g,"\\\\'")}')"><div class=usern>${esc(k)}</div><div class=usermeta><b>${d.t-d.r}</b> pra curar <span class=exp>· ${d.t} no total · ${d.r} revisados</span></div></div>`;}).join('');
 document.getElementById('cu').innerHTML=`<div class=card><div class=ihead>Curar por pessoa <span class=exp>escolha quem você vai curar — todos veem todos, mas na prática cure o seu</span></div><div class=usergrid>${cards}</div></div>`;
}
function pickUser(u){curUser=u;ci=0;showCurate();}
const CFLAGS=['2 vozes','ruído','corte ruim','sobreposição','eco/metálico','outro'];
function renderCur(){
 const c=CUR[ci];if(!c)return;
 const done=CUR.filter(x=>x.edited).length;
 let h=`<div class=card>
 <button class="btn mini" onclick="curUser=null;showCurate()" style="margin-bottom:12px">← trocar pessoa (${esc(curUser||'')})</button>
 <div class=tags><span>${ci+1}/${CUR.length}</span><span>${esc(c.id)}</span><span>${esc(c.style||'')}</span><span>dur ${c.dur_s!=null?c.dur_s.toFixed(1)+'s':'?'}</span>${c.edited?'<span style="border-color:var(--green);color:var(--green)">✓ revisado</span>':'<span style="border-color:var(--orange);color:var(--orange)">○ pendente</span>'}${c.keep===false?'<span style="border-color:var(--red);color:var(--red)">descartado</span>':''}</div>
 <audio controls src="/curate/audio?id=${encodeURIComponent(c.id)}" style="width:100%;margin:12px 0"></audio>
 <div class=ihead><b>Transcrição</b> <span class=exp>corrija pra bater EXATO com o áudio</span></div>
 <textarea id=curtext class=curtext oninput="curEdit('text',this.value)" placeholder="transcrição...">${esc(c.text||'')}</textarea>
 <div class=curcmp>
  <div><span class=curlbl>original (Whisper):</span> ${esc(c.text_orig||'—')}</div>
  ${c.text_v2!=null?`<div><span class=curlbl>ASR-v2 (medium):</span> ${esc(c.text_v2||'(vazio)')} ${(c.text_v2&&c.text_v2!==c.text)?'<button class="btn mini" onclick=useV2()>usar v2</button>':''}</div>`:'<div class=curlbl>ASR-v2: re-transcrevendo no CPU… (recarregue pra atualizar)</div>'}
 </div>
 <div class=ind><div class=ihead><b>Manter?</b></div>
  <button class="btn ok ${c.keep!==false?'on':''}" onclick="curEdit('keep',true)">manter</button>
  <button class="btn no ${c.keep===false?'on':''}" onclick="curEdit('keep',false)">descartar</button></div>
 <div class=ind><div class=ihead><b>Problemas</b></div>${CFLAGS.map(fl=>`<button class="btn fl ${(c.flags||[]).includes(fl)?'on':''}" onclick="curFlag('${fl}')">${fl}</button>`).join('')}</div>
 <div class=nav><button class=btn onclick="curGo(-1)">‹ anterior</button><button class=btn onclick="curGo(1)">próximo ›</button><span class=muted style="margin-left:12px">${done}/${CUR.length} revisados · mantidos ${CUR.filter(x=>x.keep!==false).length}</span></div>
 </div>`;
 document.getElementById('cu').innerHTML=h;
}
function saveCurNow(){const c=CUR[ci];if(!c)return;fetch('/api/curate/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:c.id,text:c.text,keep:c.keep!==false,flags:c.flags||[]})}).catch(function(){});}
function curEdit(field,val){const c=CUR[ci];if(!c)return;c[field]=val;c.edited=true;if(field=='keep')renderCur();clearTimeout(window._ce);window._ce=setTimeout(saveCurNow,400);flash('salvo ✓');}
function curFlag(fl){const c=CUR[ci];if(!c)return;const a=c.flags||[];const j=a.indexOf(fl);if(j<0){a.push(fl);}else{a.splice(j,1);}c.flags=a;c.edited=true;renderCur();saveCurNow();flash('salvo ✓');}
function useV2(){const c=CUR[ci];if(!c||c.text_v2==null)return;c.text=c.text_v2;c.edited=true;renderCur();saveCurNow();flash('usou ASR-v2');}
function curGo(d){saveCurNow();ci=Math.max(0,Math.min(CUR.length-1,ci+d));renderCur();}
function view(v){
 for(const x of ['av','tr','cu','gr']){document.getElementById(x).classList.toggle('hide',x!=v);}
 document.getElementById('tAv').classList.toggle('on',v=='av');
 document.getElementById('tTr').classList.toggle('on',v=='tr');
 document.getElementById('tCu').classList.toggle('on',v=='cu');
 document.getElementById('tGr').classList.toggle('on',v=='gr');
 document.getElementById('navL').classList.toggle('hide',v!='av');document.getElementById('navR').classList.toggle('hide',v!='av');
 if(v=='tr'){requestAnimationFrame(drawEdges);}
 if(v=='cu'){showCurate();}
 if(v=='gr'){loadGravar();}
}
function loadGravar(){const g=document.getElementById('gr');if(!g.dataset.loaded){g.dataset.loaded=1;
 g.innerHTML='<iframe src="/gravar" allow="microphone" style="width:100%;height:84vh;border:1px solid var(--border);border-radius:14px;background:var(--bg)"></iframe>';}}
async function loadInsTrilha(){
 const box=document.getElementById('instr');if(!box)return;
 if(box.dataset.loaded){box.classList.toggle('open');return;}
 box.dataset.loaded=1;box.classList.add('open');box.innerHTML='<p class=muted>carregando…</p>';
 const d=await(await fetch('/api/insights')).json();
 const tbl=(o,hd)=>`<table><tr><th>${hd}</th><th>n</th><th>geral</th><th>nativo</th><th>natural</th><th>voz</th><th>parou%</th></tr>`+
  Object.entries(o).map(([k,a])=>`<tr><td>${k}</td><td>${a.n}</td><td>${a.geral??'-'}</td><td>${a.nativo??'-'}</td><td>${a.natural??'-'}</td><td>${a.voz??'-'}</td><td>${a.parou_pct??'-'}</td></tr>`).join('')+`</table>`;
 const probs=Object.entries(d.problemas||{});
 const fb=d.feedback||{clips_marcados:0,total_marcadores:0,por_tag:{}};
 const ftags=Object.entries(fb.por_tag||{});
 box.innerHTML=`<div class=insbox><p class=exp>${d.total_rated}/${d.total} avaliados</p>
  <h3>Por run</h3>${tbl(d.por_run,'run')}
  <h3>Por emoção</h3>${tbl(d.por_emocao,'emoção')}
  <h3>Problemas mais comuns</h3>${probs.length?`<table><tr><th>problema</th><th>clipes</th></tr>${probs.map(([p,n])=>`<tr><td>${p}</td><td>${n}</td></tr>`).join('')}</table>`:'<p class=muted>marque tags de problema nos áudios pra ver o ranking.</p>'}
  <p class=muted style="margin-top:10px">${fb.clips_marcados} clipes marcados · ${fb.total_marcadores} instantes no tempo (base pros agentes do futuro).</p>
  <div style="margin-top:14px"><button class=btn onclick=exportFeedback()>⬇ exportar feedback (.jsonl)</button></div></div>`;
}
async function exportFeedback(){
 try{const recs=await(await fetch('/api/feedback')).json();
  const jsonl=recs.map(function(r){return JSON.stringify(r);}).join('\n');
  const blob=new Blob([jsonl],{type:'application/x-ndjson'});const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='feedback.jsonl';a.click();URL.revokeObjectURL(url);
  flash('exportado: feedback.jsonl');}catch(e){flash('falha ao exportar');}
}
const STATUS={done:'feito',wip:'em curso',next:'a seguir',idea:'hipótese'};
function tog(id){const e=document.getElementById(id);if(e)e.classList.toggle('open');}
function mayaGapHTML(m){
 const g=m.maya_gap;if(!g)return '';
 const eixos=(g.eixos||[]).map(function(e){const w=Math.max(0,Math.min(100,(e.score||0)/10*100));return `<div class=gaprow title="${esc(e.nota||'')}"><span class=gaplbl>${esc(e.nome)}</span><div class=gapbar><i style="width:${w}%"></i></div><span class=gapscore>${e.score}</span></div>`;}).join('');
 const real=m.realismo||g.realismo||'';
 const ver=(g.veredito||'').split('—')[0].split('. ')[0];
 return `<div class="card gapcard"><div class=ihead>Onde estamos <b>de verdade</b> vs Maya <span class=exp>Maya=10 · passe o mouse nas barras</span></div>
  <div class=gapmedia><span class=gapbig>${g.media!=null?g.media:'?'}</span><span class=gapof>/10</span><span class=gapver>${esc(ver)}</span></div>
  <div class=gaprows>${eixos}</div>
  ${real?`<button class="btn mini gapbtn" onclick="tog('gapreal')">realismo — o texto duro ▾</button><div id=gapreal class=collapse><p class=gapreal>${esc(real)}</p></div>`:''}</div>`;
}
function hypsKanban(m){
 const cols=[{k:'aberta',label:'em aberto',cls:'ka'},{k:'parcial',label:'parciais',cls:'kp'},{k:'refutada',label:'refutadas',cls:'kr'},{k:'validada',label:'validadas',cls:'kv'}];
 const hs=m.hypotheses||[];
 return '<div class=kanban>'+cols.map(function(c){
  const items=hs.filter(function(h){return h.status===c.k;});
  return `<div class="kcol ${c.cls}"><div class=khead>${c.label} <span class=kcount>${items.length}</span></div>`+
   items.map(function(h,idx){const cid=c.k+'-'+idx;
    return `<div class="kcard ${c.cls}" id="kc-${cid}" onclick="toggleHyp('${cid}')">
     <div class=kclaim><span>${esc(h.claim)}</span>${(h.detail||h.node)?'<span class=kchev>▶</span>':''}</div>
     ${h.evidence?`<div class=kev>${esc(h.evidence)}</div>`:''}
     <div class=kdetail>${h.detail?md(h.detail):''}${h.node?`<span class=linknode onclick="event.stopPropagation();openNode('${h.node}')">ir ao bloco →</span>`:''}</div>
    </div>`;}).join('')+`</div>`;
 }).join('')+'</div>';
}
function toggleHyp(cid){const el=document.getElementById('kc-'+cid);if(el)el.classList.toggle('open');}
function gpuPlanHTML(m){
 if(!m.gpu_plan||!m.gpu_plan.length)return '';
 const hrs=m.gpu_plan.map(function(g){return parseFloat(String(g.hours||'').replace(',','.'))||0;});
 const mx=Math.max(1,...hrs);
 const cards=m.gpu_plan.map(function(g,i){const w=Math.round(hrs[i]/mx*100);
  return `<div class=gcard onclick="this.classList.toggle('open')">
   <div class=gtop><span class=glabel>${esc(g.label)}</span><span class=gcost>${esc(g.cost||'')}</span></div>
   <div class=gbar><i style="width:${w}%"></i></div><div class=ghours>${esc(g.hours||'')} · ${esc(g.gpu||'')}</div>
   <div class=gdetail>${esc(g.trilha||'')}<br>${esc(g.dataset||'')}${g.fraction?' · '+esc(g.fraction):''}${g.depends?'<br><span class=exp>depende: '+esc(g.depends)+'</span>':''}</div></div>`;}).join('');
 return `<div class=card><div class=ihead>Plano de GPU <span class=exp>horas por treino · clique num card pro detalhe · base: ${esc(m.cost_basis||'')}</span></div><div class=gplan>${cards}</div>${m.gpu_total?'<div class=block-next><b>→ </b>'+esc(m.gpu_total)+'</div>':''}</div>`;
}
function blocksHTML(m){
 if(!m.blocks||!m.blocks.length)return '';
 return `<div class=card><div class=ihead>Treinos · KPIs <span class=exp>clique num bloco pra abrir métricas + aprendizados</span></div>`+
  m.blocks.slice().reverse().map(function(b){
   let kpi='';
   if(b.metrics){const rs=Object.keys(b.metrics);const w=rs.map(function(r){return b.metrics[r].wer;}).filter(function(x){return x!=null;});const nt=rs.map(function(r){return b.metrics[r].nativo;}).filter(function(x){return x!=null;});const gr=rs.map(function(r){return b.metrics[r].geral;}).filter(function(x){return x!=null;});
    kpi='<span class=kpi>'+rs.length+' runs</span>'+(w.length?'<span class=kpi>WER '+Math.min.apply(null,w)+'–'+Math.max.apply(null,w)+'%</span>':'')+(nt.length?'<span class=kpi>nativo ‹'+Math.max.apply(null,nt)+'/5</span>':'')+(gr.length?'<span class=kpi>geral ‹'+Math.max.apply(null,gr)+'/5</span>':'');}
   let mt='';
   if(b.metrics){mt='<table class=blockt><tr><th>run</th><th>geral</th><th>nativo</th><th>natural</th><th>voz</th><th>parou</th><th>WER</th></tr>'+
    Object.keys(b.metrics).map(function(run){const x=b.metrics[run]||{};return '<tr><td>'+esc(run)+'</td><td>'+(x.geral!=null?x.geral:'-')+'</td><td>'+(x.nativo!=null?x.nativo:'-')+'</td><td>'+(x.natural!=null?x.natural:'-')+'</td><td>'+(x.voz!=null?x.voz:'-')+'</td><td>'+(x.parou!=null?x.parou+'%':'-')+'</td><td>'+(x.wer!=null?x.wer+'%':'-')+'</td></tr>';}).join('')+'</table>';}
   return '<div class=block><div class=block-h onclick="this.parentNode.classList.toggle(\'open\')"><b>'+esc(b.label||b.id)+'</b> '+kpi+'<span class=block-meta>'+esc((b.date||'')+' · '+(b.n||'?')+' aval'+(b.avaliador?' · '+b.avaliador:''))+' ▾</span></div><div class=blockbody>'+mt+
    '<ul class=block-l>'+(b.learnings||[]).map(function(l){return '<li>'+esc(l)+'</li>';}).join('')+'</ul>'+
    ((b.proximos&&b.proximos.length)?'<div class=block-next><b>→ próximos:</b> '+b.proximos.map(esc).join(' · ')+'</div>':'')+'</div></div>';
  }).join('')+`</div>`;
}
function nextsCards(m){
 const nx=(m.state&&m.state.next)||[];if(!nx.length)return '';
 return `<div class=card><div class=ihead>Próximos passos <span class=exp>clique pra abrir cada fase</span></div><div class=fases>`+
  nx.map(function(s,i){const ix=s.indexOf(':');const t=ix>0?s.slice(0,ix):('Passo '+(i+1));const b=ix>0?s.slice(ix+1).trim():s;
   return `<div class=fase onclick="this.classList.toggle('open')"><div class=fasen>${esc(t)}</div><div class=faseb>${esc(b)}</div></div>`;}).join('')+
  `</div></div>`;
}
function blockersCards(m){
 const bl=(m.state&&m.state.blockers)||[];if(!bl.length)return '';
 return `<div class=card><div class=ihead>Blockers reais <span class=exp>o que trava de verdade · clique pra abrir</span></div><div class=blgrid>`+
  bl.map(function(s){let ix=s.indexOf(':');if(ix<0||ix>64)ix=s.indexOf('. ');if(ix<0||ix>64)ix=Math.min(58,s.length);const t=s.slice(0,ix).trim();const b=s.slice(ix).replace(/^[:.]\s*/,'').trim();
   return `<div class=blcard onclick="this.classList.toggle('open')"><div class=blt>⛔ ${esc(t)}</div>${b?`<div class=blb>${esc(b)}</div>`:''}</div>`;}).join('')+
  `</div></div>`;
}
function renderTrail(){
 const m=MAP;
 const overall=m.lanes&&m.lanes.length?Math.round(m.lanes.reduce(function(s,l){return s+l.progress;},0)/m.lanes.length):0;
 const tweet=(m.state&&(m.state.tweet||m.state.now))||'';
 let h=`<div class="card tweetcard"><div class=tweethd><h2>🧭 Trilha</h2><div class=t-over><div class=lane-bar style="width:140px;height:4px"><i style="width:${overall}%"></i></div><span class=lane-pct>${overall}%</span></div></div>
  <p class=tweet>${esc(tweet)}</p>
  ${(m.state&&m.state.now&&m.state.now!==tweet)?`<button class="btn mini" onclick="tog('stnow')">status completo ▾</button><div id=stnow class=collapse><p class=trail>${esc(m.state.now)}</p></div>`:''}</div>`;
 h+=mayaGapHTML(m);
 h+=`<div class=card><div class=ihead>Mapa · o que depende do quê <span class=exp>a parte boa — clique num bloco pro aprofundamento · ↔ arraste</span></div><div id=mapwrap><div id=map></div></div></div>`;
 h+=`<div class=card><div class=ihead>Hipóteses <span class=exp>por status · clique num card pra abrir o real-talk</span></div>${hypsKanban(m)}</div>`;
 h+=nextsCards(m);
 h+=blockersCards(m);
 h+=gpuPlanHTML(m);
 h+=blocksHTML(m);
 h+=`<div class=card><button class="btn mini" id=insbtn onclick="loadInsTrilha()">Insights — notas agregadas ▾</button><div id=instr class=collapse></div></div>`;
 document.getElementById('tr').innerHTML=h;
 const map=document.getElementById('map');
 const COLS=Math.max(0,...m.nodes.map(function(n){return n.col;}))+1;
 let lanes='';
 for(const lane of m.lanes){
  const lns=m.nodes.filter(function(n){return n.lane===lane.key;});
  let cells='';
  for(const n of lns){cells+=`<div class=cell style="grid-column:${n.col+1}">${nodeCard(n)}</div>`;}
  lanes+=`<div class=lane><div class=lane-head><span class=lane-title>${esc(lane.label)}</span><div class=lane-bar><i style="width:${lane.progress}%"></i></div><span class=lane-pct>${lane.progress}%</span></div>
   <div class=lane-row style="grid-template-columns:repeat(${COLS},minmax(140px,1fr))">${cells}</div></div>`;
 }
 map.innerHTML=`<svg class=edges id=edges></svg>`+lanes;
 requestAnimationFrame(drawEdges);
}
function nodeCard(n){
 return `<div class="node ${n.status}" id="nd-${n.id}" onclick="openNode('${n.id}')"><div class=node-t>${esc(n.title)}</div><div class=node-bar><i style="width:${n.progress||0}%"></i></div><div class=node-meta><span>${n.progress||0}%</span><span class=dot></span>${STATUS[n.status]||''}</div></div>`;
}
function drawEdges(){
 try{
  const svg=document.getElementById('edges'),map=document.getElementById('map');if(!svg||!map)return;
  const mr=map.getBoundingClientRect();
  svg.setAttribute('width',map.scrollWidth);svg.setAttribute('height',map.scrollHeight);
  let p='';
  for(const n of MAP.nodes){
   const to=document.getElementById('nd-'+n.id);if(!to)continue;const tr=to.getBoundingClientRect();
   for(const d of (n.deps||[])){
    const f=document.getElementById('nd-'+d);if(!f)continue;const fr=f.getBoundingClientRect();
    const x1=fr.right-mr.left,y1=fr.top+fr.height/2-mr.top,x2=tr.left-mr.left,y2=tr.top+tr.height/2-mr.top;
    const dx=Math.max(22,Math.abs(x2-x1)*0.4);
    p+=`<path class=edge d="M ${x1} ${y1} C ${x1+dx} ${y1}, ${x2-dx} ${y2}, ${x2} ${y2}"/>`;
   }
  }
  svg.innerHTML=p;
 }catch(e){}
}
function md(s){
 s=esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`(.+?)`/g,'<code>$1</code>');
 const lines=s.split('\n');let out='',inl=false;
 for(let ln of lines){
  if(/^\s*[-•]\s+/.test(ln)){if(!inl){out+='<ul>';inl=true;}out+='<li>'+ln.replace(/^\s*[-•]\s+/,'')+'</li>';}
  else{if(inl){out+='</ul>';inl=false;}if(ln.trim())out+='<p>'+ln+'</p>';}
 }
 if(inl)out+='</ul>';return out;
}
function openNode(id){
 const n=MAP.nodes.find(function(x){return x.id===id;});if(!n)return;
 const lane=(MAP.lanes.find(function(l){return l.key===n.lane;})||{}).label||n.lane;
 const deps=(n.deps||[]).map(function(d){return MAP.nodes.find(function(x){return x.id===d;});}).filter(Boolean);
 const dependents=MAP.nodes.filter(function(x){return (x.deps||[]).indexOf(id)>=0;});
 const link=function(a){return `<span class=linknode onclick="openNode('${a.id}')">${esc(a.title)}</span>`;};
 let h=`<button class=panel-x onclick=closePanel()>✕</button>
  <div class=tags><span>${esc(lane)}</span><span>${STATUS[n.status]||''}</span></div>
  <h3 class=pt>${esc(n.title)}</h3>
  <div class=node-bar style="margin:12px 0 6px;height:5px"><i class="${n.status}" style="width:${n.progress||0}%"></i></div>
  <div class=lane-pct>${n.progress||0}% pronto</div>
  <p class=psum>${esc(n.summary||'')}</p>
  <div class=deep>${md(n.deep||'')}</div>`;
 if((n.hyp||[]).length){h+=`<div class=ihead style="margin-top:20px">Hipóteses</div>`+n.hyp.map(function(hy){return `<div class="hyp ${hy.status}">${esc(hy.claim)} · <b>${hy.status}</b></div>`;}).join('');}
 if(deps.length){h+=`<div class=ihead style="margin-top:20px">Depende de</div><div class=links>${deps.map(link).join('')}</div>`;}
 if(dependents.length){h+=`<div class=ihead style="margin-top:20px">Habilita</div><div class=links>${dependents.map(link).join('')}</div>`;}
 const panel=document.getElementById('panel');panel.innerHTML=h;panel.classList.add('open');document.getElementById('panelbg').classList.add('open');
}
function closePanel(){document.getElementById('panel').classList.remove('open');document.getElementById('panelbg').classList.remove('open');}
document.addEventListener('keydown',e=>{
 if(e.key=='Escape'){closePanel();closeTagModal();}
 const tg=e.target.tagName;if(tg=='INPUT'||tg=='SELECT'||tg=='TEXTAREA')return;
 if(!document.getElementById('av').classList.contains('hide')){
  if(e.key==' '){e.preventDefault();togglePlay();}
  else if(e.key=='Enter'&&window._mStart!=null){e.preventDefault();addMarker();}
  else if(e.key>='1'&&e.key<='5'){setv('geral',+e.key);}
  else if(e.key.toLowerCase()=='p'){setv('parou',!(rOf(cur()).parou===true));}
 }
});
document.addEventListener('mouseup',function(){endDrag();});
document.addEventListener('click',function(e){if(e.target&&e.target.tagName=='BUTTON')e.target.blur();});
window.addEventListener('resize',function(){if(!document.getElementById('tr').classList.contains('hide'))drawEdges();});
boot();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a): pass

    def _serve_range(self, data, ctype):
        """Serve bytes com suporte a HTTP Range (206) — necessário pro <audio> dar seek."""
        total = len(data)
        rng = self.headers.get('Range')
        start, end, partial = 0, total - 1, False
        if rng and rng.startswith('bytes='):
            try:
                s, e = rng[6:].split('-', 1)
                if s.strip():
                    start = int(s); end = int(e) if e.strip() else total - 1
                else:
                    start = max(0, total - int(e)); end = total - 1
                end = min(end, total - 1)
                if start < 0 or start > end or start >= total:
                    self.send_response(416); self.send_header('Content-Range', f'bytes */{total}')
                    self.send_header('Content-Length', '0'); self.end_headers(); return
                partial = True
            except Exception:
                start, end, partial = 0, total - 1, False
        chunk = data[start:end + 1]
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        if partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{total}')
        self.send_header('Content-Length', str(len(chunk)))
        self.end_headers()
        try:
            self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/':
            self._send(200, PAGE, 'text/html; charset=utf-8')
        elif u.path == '/gravar':
            rec = Path(__file__).resolve().parent.parent / 'recording' / 'maya_recorder.html'
            self._send(200, rec.read_text(encoding='utf-8'), 'text/html; charset=utf-8')
        elif u.path == '/api/clips':
            self._send(200, build_manifest())
        elif u.path == '/api/ratings':
            self._send(200, {f"{k[0]}|{k[1]}": v for k, v in load_ratings().items()})
        elif u.path == '/api/insights':
            self._send(200, insights())
        elif u.path == '/api/map':
            self._send(200, load_map())
        elif u.path == '/api/feedback':
            self._send(200, feedback_records())
        elif u.path == '/api/curate':
            self._send(200, load_curate())
        elif u.path == '/curate/audio':
            cid = re.sub(r'[^\w-]', '', q.get('id', [''])[0])
            p = CURATE_SEG / (cid + '.wav')
            if cid and p.exists():
                self._serve_range(p.read_bytes(), 'audio/wav')
            else:
                self._send(404, b'no audio', 'text/plain')
        elif u.path == '/audio':
            run = q.get('run', [''])[0]; cid = q.get('id', [''])[0]
            matches = list((SAMPLES / run).rglob(f'{cid}.wav'))
            if matches:
                self._serve_range(matches[0].read_bytes(), 'audio/wav')
            else:
                self._send(404, b'no audio', 'text/plain')
        else:
            self._send(404, b'404', 'text/plain')

    def do_POST(self):
        if self.path == '/api/rate':
            n = int(self.headers.get('Content-Length', 0))
            r = json.loads(self.rfile.read(n))
            r['block'] = r.get('block') or load_block()
            with _RLOCK:
                data = load_ratings()
                data.setdefault((r['run'], r['id']), {}).update(r)   # merge defensivo (não apaga campos de POST parcial)
                tmp = RATINGS.with_suffix('.tmp')
                with open(tmp, 'w', encoding='utf-8') as f:
                    for v in data.values():
                        f.write(json.dumps(v, ensure_ascii=False) + '\n')
                tmp.replace(RATINGS)
            self._send(200, {'ok': True})
        elif self.path == '/api/curate/save':
            n = int(self.headers.get('Content-Length', 0))
            save_curate(json.loads(self.rfile.read(n)))
            self._send(200, {'ok': True})
        else:
            self._send(404, b'404', 'text/plain')


if __name__ == '__main__':
    n = len(build_manifest())
    print(f"🎧 Rate — {n} áudios · Avaliar / Insights / Trilha")
    print(f"   http://localhost:{ARGS.port}   (notas → {RATINGS.name})")
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{ARGS.port}')).start()
    ThreadingHTTPServer(('127.0.0.1', ARGS.port), H).serve_forever()
