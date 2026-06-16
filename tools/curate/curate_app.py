#!/usr/bin/env python3
"""
Curate — app local pra LIMPAR o dataset de treino (voz do Pedro).

Sem dependências. Carrega um .jsonl de dataset (default: o transcribed.jsonl do
elevenlabs2024), e pra cada clipe deixa você: ouvir, CORRIGIR a transcrição (o Whisper
erra), marcar manter/descartar, e flaggar problemas (sobreposição, ruído, corte ruim,
2 vozes, vazio). Pré-flagga os suspeitos (curto <2s, vazio, longo >12s) pra revisar
rápido. Exporta um dataset limpo (transcribed_clean.jsonl) só com os mantidos + texto
corrigido — é esse que vira o treino do Estágio B.

Uso:
  python tools/curate/curate_app.py                         # elevenlabs2024
  python tools/curate/curate_app.py --jsonl caminho.jsonl   # outro dataset
  python tools/curate/curate_app.py --port 8078
Teclado (fora do campo de texto): Espaço=tocar · K=manter · D=descartar · ←/→=navegar · F=só flaggados
"""
import argparse, json, urllib.parse, webbrowser, threading, statistics, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--jsonl', default=str(REPO / 'data/raw/elevenlabs2024/segments/transcribed.jsonl'))
ap.add_argument('--port', type=int, default=8078)
ARGS = ap.parse_args()
SRC = Path(ARGS.jsonl)
EDITS = Path(__file__).resolve().parent / (SRC.stem + '_edits.jsonl')
CLEAN = SRC.parent.parent / (SRC.stem.replace('transcribed', '') + 'transcribed_clean.jsonl').replace('__', '_')


def audio_path(row):
    p = Path(row['audio'])
    for cand in (p, REPO / row['audio'], SRC.parent / p.name):
        if cand.exists():
            return cand
    return None


def rows():
    out = []
    for l in SRC.read_text(encoding='utf-8').splitlines():
        if l.strip():
            out.append(json.loads(l))
    return out


def preflags(r):
    f, d = [], float(r.get('dur_s', 0))
    if not str(r.get('text', '')).strip(): f.append('vazio')
    if d and d < 2: f.append('curto')
    if d and d > 12: f.append('longo')
    return f


def load_edits():
    out = {}
    if EDITS.exists():
        for l in EDITS.read_text(encoding='utf-8').splitlines():
            if l.strip():
                e = json.loads(l); out[e['id']] = e
    return out


def manifest():
    edits = load_edits()
    out = []
    for r in rows():
        e = edits.get(r['id'], {})
        out.append({
            'id': r['id'], 'source_id': r.get('source_id', ''), 'dur_s': r.get('dur_s'),
            'text_orig': r.get('text', ''), 'pre': preflags(r),
            'text': e.get('text', r.get('text', '')),
            'keep': e.get('keep', True), 'flags': e.get('flags', []), 'nota': e.get('nota', ''),
            'reviewed': r['id'] in edits,
        })
    return out


def export_clean():
    edits = load_edits()
    src = {r['id']: r for r in rows()}
    n = 0
    with open(CLEAN, 'w', encoding='utf-8') as f:
        for cid, r in src.items():
            e = edits.get(cid)
            keep = e.get('keep', True) if e else True
            if not keep:
                continue
            r2 = dict(r)
            if e and e.get('text'):
                r2['text'] = e['text']
            if e and e.get('flags'):
                r2['flags'] = e['flags']
            f.write(json.dumps(r2, ensure_ascii=False) + '\n')
            n += 1
    return n, str(CLEAN)


def stats():
    m = manifest()
    rev = [c for c in m if c['reviewed']]
    kept = [c for c in m if c['keep']]
    dur_kept = sum(float(c['dur_s'] or 0) for c in kept) / 60
    flagc = {}
    for c in m:
        for fl in c['flags']:
            flagc[fl] = flagc.get(fl, 0) + 1
    return {'total': len(m), 'revisados': len(rev), 'manter': len(kept),
            'descartar': len(m) - len(kept), 'min_mantidos': round(dur_kept, 1), 'flags': flagc}


PAGE = r"""<!doctype html><html lang=pt-br><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Curate — dataset</title><style>
:root{--bg:#0e0f13;--card:#1a1c22;--b:#2a2d36;--t:#e8e9ed;--t2:#9aa0ab;--ac:#6ea8fe;--ok:#4ade80;--no:#f87171;--am:#fbbf24}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font:15px/1.5 -apple-system,system-ui,sans-serif}
header{display:flex;align-items:center;gap:14px;padding:12px 20px;border-bottom:1px solid var(--b);position:sticky;top:0;background:var(--bg)}
h1{font-size:16px;margin:0}.sp{flex:1}.muted{color:var(--t2)}.bar{height:5px;background:#23262f;border-radius:3px;flex:1;max-width:220px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--ac)}
.wrap{max-width:760px;margin:22px auto;padding:0 16px}.card{background:var(--card);border:1px solid var(--b);border-radius:14px;padding:20px}
.tags span{display:inline-block;background:#23262f;border:1px solid var(--b);border-radius:6px;padding:2px 9px;font-size:12px;margin-right:6px;color:var(--t2)}
.pre{color:var(--am)!important;border-color:var(--am)!important}
audio{width:100%;margin:12px 0}textarea{width:100%;min-height:70px;background:#16181d;border:1px solid var(--b);color:var(--t);border-radius:8px;padding:10px;font:15px/1.5 inherit;resize:vertical}
.orig{font-size:12px;color:var(--t2);margin:6px 0}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0;align-items:center}.row b{width:90px;color:var(--t2);font-size:13px}
.btn{background:#23262f;border:1px solid var(--b);color:var(--t);border-radius:8px;padding:7px 13px;cursor:pointer;font-size:14px}.btn:hover{border-color:var(--ac)}
.btn.on{background:var(--ac);color:#08111f;font-weight:600}.btn.ok.on{background:var(--ok);color:#06210f}.btn.no.on{background:var(--no);color:#2a0808}.btn.fl.on{background:var(--am);color:#241a00}
.nav{display:flex;gap:10px;margin-top:18px}.nav .btn{flex:1;text-align:center;padding:10px}.k{font-size:11px;color:var(--t2);margin-left:5px}
table{width:100%;border-collapse:collapse}td,th{padding:6px 10px;border-bottom:1px solid var(--b);text-align:left;font-size:14px}th{color:var(--t2);font-weight:500}
</style></head><body>
<header><h1>🧹 Curate — dataset</h1><div class=bar><i id=prog></i></div><span class=muted id=cnt></span><div class=sp></div>
<button class=btn onclick=onlyFlag()>Só p/ revisar <span class=k>F</span></button>
<button class=btn onclick=exp()>Exportar limpo</button></header>
<div class=wrap><div class=card id=card></div>
<div class=nav><button class=btn onclick=go(-1)>← <span class=k>←</span></button>
<button class=btn onclick=play()>▶ Tocar <span class=k>espaço</span></button>
<button class=btn onclick=go(1)>→ <span class=k>→</span></button></div>
<p class=muted id=msg style=margin-top:12px>Teclas: espaço tocar · K manter · D descartar · ←/→ navegar · F filtrar suspeitos</p></div>
<script>
let all=[],list=[],i=0,filt=false;const FLAGS=['sobreposição','ruído','corte-ruim','2-vozes','vazio','outro'];
async function boot(){all=await(await fetch('/api/manifest')).json();applyFilter();render()}
function applyFilter(){list=filt?all.filter(c=>(c.pre.length||!c.reviewed)):all;if(i>=list.length)i=0}
function cur(){return list[i]}
function render(){const c=cur();if(!c){document.getElementById('card').innerHTML='Nada aqui.';return}
const warn=c.pre.length?`<span class="pre" style="border:1px solid">${c.pre.join(' ')}</span>`:'';
document.getElementById('card').innerHTML=`
<div class=tags><span>${c.id}</span><span>${c.source_id}</span><span>${c.dur_s}s</span>${warn} ${c.reviewed?'<span style=color:var(--ok)>revisado</span>':''}</div>
<audio id=au controls src="/audio?id=${encodeURIComponent(c.id)}"></audio>
<div class=orig>Whisper transcreveu (corrija abaixo se errado):</div>
<textarea id=txt onchange="setv('text',this.value)">${esc(c.text)}</textarea>
<div class=row><b>Manter?</b>
<button class="btn ok ${c.keep?'on':''}" onclick="setv('keep',true)">manter ✓ <span class=k>K</span></button>
<button class="btn no ${!c.keep?'on':''}" onclick="setv('keep',false)">descartar <span class=k>D</span></button></div>
<div class=row><b>Problemas</b>${FLAGS.map(f=>`<button class="btn fl ${c.flags.includes(f)?'on':''}" onclick="togFlag('${f}')">${f}</button>`).join('')}</div>
<div class=row><b>Nota</b><input style="flex:1;background:#16181d;border:1px solid var(--b);color:var(--t);border-radius:8px;padding:7px" id=nota value="${esc(c.nota)}" onchange="setv('nota',this.value)"></div>`;
const rev=all.filter(c=>c.reviewed).length;document.getElementById('cnt').textContent=`${i+1}/${list.length} · ${rev}/${all.length} revisados`;
document.getElementById('prog').style.width=(100*rev/all.length)+'%';}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
async function save(c){c.reviewed=true;await fetch('/api/edit',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({id:c.id,text:c.text,keep:c.keep,flags:c.flags,nota:c.nota,ts:Date.now()})})}
async function setv(k,v){const c=cur();c[k]=v;await save(c);render()}
async function togFlag(f){const c=cur();const j=c.flags.indexOf(f);if(j<0)c.flags.push(f);else c.flags.splice(j,1);await save(c);render()}
function go(d){i=Math.max(0,Math.min(list.length-1,i+d));render();setTimeout(play,120)}
function play(){const a=document.getElementById('au');if(a){a.paused?a.play():a.pause()}}
function onlyFlag(){filt=!filt;i=0;applyFilter();render();document.getElementById('msg').textContent=filt?'Mostrando só suspeitos/não-revisados.':'Mostrando todos.'}
async function exp(){const r=await(await fetch('/api/export',{method:'POST'})).json();const s=await(await fetch('/api/stats')).json();
document.getElementById('msg').innerHTML=`✓ Exportado ${r.n} clipes limpos → <code>${r.path}</code> · ${s.min_mantidos}min mantidos · descartados ${s.descartar} · flags ${JSON.stringify(s.flags)}`}
document.addEventListener('keydown',e=>{if(e.target.tagName=='TEXTAREA'||e.target.tagName=='INPUT')return;
if(e.key==' '){e.preventDefault();play();}
else if(e.key=='ArrowRight'){go(1);}
else if(e.key=='ArrowLeft'){go(-1);}
else if(e.key.toLowerCase()=='k'){setv('keep',true);}
else if(e.key.toLowerCase()=='d'){setv('keep',false);}
else if(e.key.toLowerCase()=='f'){onlyFlag();}});
boot();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/': self._send(200, PAGE, 'text/html; charset=utf-8')
        elif u.path == '/api/manifest': self._send(200, manifest())
        elif u.path == '/api/stats': self._send(200, stats())
        elif u.path == '/audio':
            cid = q.get('id', [''])[0]
            r = next((x for x in rows() if x['id'] == cid), None)
            p = audio_path(r) if r else None
            if p:
                data = p.read_bytes()
                self.send_response(200); self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            else: self._send(404, b'no audio', 'text/plain')
        else: self._send(404, b'404', 'text/plain')

    def do_POST(self):
        if self.path == '/api/edit':
            n = int(self.headers.get('Content-Length', 0)); e = json.loads(self.rfile.read(n))
            with open(EDITS, 'a', encoding='utf-8') as f: f.write(json.dumps(e, ensure_ascii=False) + '\n')
            self._send(200, {'ok': True})
        elif self.path == '/api/export':
            n, path = export_clean(); self._send(200, {'n': n, 'path': path})
        else: self._send(404, b'404', 'text/plain')


if __name__ == '__main__':
    print(f"🧹 Curate — {len(rows())} clipes de {SRC.name}")
    print(f"   Abra: http://localhost:{ARGS.port}   (edições → {EDITS.name} · export → {CLEAN.name})")
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{ARGS.port}')).start()
    ThreadingHTTPServer(('127.0.0.1', ARGS.port), H).serve_forever()
