#!/usr/bin/env python3
"""
Rate — app local pra classificar os áudios gerados e tirar insights.

Sem dependências (só stdlib). Escaneia uma pasta de samples (default: runpod_samples/),
casa cada .wav com o benchmark (emoção/sotaque/texto) e o per_sentence (WER/duração/hyp
do ASR), e serve uma página onde você ouve e dá notas rápidas pelo teclado. As notas vão
pra tools/rate/ratings.jsonl. A aba "Insights" agrega tudo (por run, por emoção) pra
decidir o que melhorar nos próximos treinos.

Uso:
  python tools/rate/rate_app.py                 # samples em runpod_samples/
  python tools/rate/rate_app.py --dir caminho   # outra pasta
  python tools/rate/rate_app.py --port 8077
Depois abre http://localhost:8077 (abre sozinho).

Teclado: Espaço=tocar · 1-5=nota geral · P=parou certo · ←/→=anterior/próximo · I=insights
"""
import argparse, json, os, time, html, urllib.parse, webbrowser, threading, statistics
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RATINGS = Path(__file__).resolve().parent / 'ratings.jsonl'
ap = argparse.ArgumentParser()
ap.add_argument('--dir', default=str(REPO / 'runpod_samples'))
ap.add_argument('--port', type=int, default=8077)
ARGS = ap.parse_args()
SAMPLES = Path(ARGS.dir)


def load_benchmark():
    bench = {}
    bp = REPO / 'eval' / 'benchmark_ptbr.jsonl'
    if bp.exists():
        for l in bp.read_text(encoding='utf-8').splitlines():
            if l.strip():
                r = json.loads(l); bench[r['id']] = r
    return bench


def build_manifest():
    """Lista os clipes: para cada run (subpasta) e cada .wav, junta meta do benchmark + per_sentence."""
    bench = load_benchmark()
    clips = []
    if not SAMPLES.exists():
        return clips
    for run_dir in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        run = run_dir.name
        # per_sentence (WER/dur/hyp do ASR), se houver — procura em run_dir e subpastas
        persent = {}
        for pj in run_dir.rglob('per_sentence.jsonl'):
            for l in pj.read_text(encoding='utf-8').splitlines():
                if l.strip():
                    r = json.loads(l); persent[r['id']] = r
            break
        for wav in sorted(run_dir.rglob('*.wav')):
            cid = wav.stem
            b = bench.get(cid, {})
            ps = persent.get(cid, {})
            clips.append({
                'run': run, 'id': cid, 'wav': str(wav.relative_to(SAMPLES)),
                'emotion': b.get('emotion', '?'), 'accent': b.get('accent', '?'),
                'text': b.get('text', ps.get('ref', '')),
                'wer': ps.get('wer'), 'dur_s': ps.get('dur_s'), 'hyp': ps.get('hyp', ''),
            })
    return clips


def load_ratings():
    out = {}  # (run,id) -> rating (último vence)
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
        if not rows: return {}
        g = [r['geral'] for r in rows if r.get('geral') is not None]
        parou = [1 if r.get('parou') else 0 for r in rows if r.get('parou') is not None]
        voz = [r['voz'] for r in rows if r.get('voz')]
        nat = [r['natural'] for r in rows if r.get('natural')]
        return {
            'n': len(rows),
            'geral': round(statistics.mean(g), 1) if g else None,
            'parou_pct': round(100 * statistics.mean(parou)) if parou else None,
            'voz': round(statistics.mean(voz), 1) if voz else None,
            'natural': round(statistics.mean(nat), 1) if nat else None,
        }
    by_run, by_emotion = {}, {}
    for r in rated:
        by_run.setdefault(r['run'], []).append(r)
        by_emotion.setdefault(r['emotion'], []).append(r)
    return {
        'total_rated': len(rated), 'total': len(clips),
        'por_run': {k: agg(v) for k, v in sorted(by_run.items())},
        'por_emocao': {k: agg(v) for k, v in sorted(by_emotion.items())},
        'piores': sorted([{'run': r['run'], 'id': r['id'], 'geral': r['geral'],
                           'parou': r.get('parou'), 'text': r['text'][:50]}
                          for r in rated], key=lambda x: x['geral'])[:8],
    }


PAGE = r"""<!doctype html><html lang=pt-br><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Rate — TTS pt-BR</title><style>
:root{--bg:#0e0f13;--card:#1a1c22;--b:#2a2d36;--t:#e8e9ed;--t2:#9aa0ab;--ac:#6ea8fe;--ok:#4ade80;--no:#f87171;--am:#fbbf24}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font:15px/1.5 -apple-system,system-ui,sans-serif}
header{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--b);position:sticky;top:0;background:var(--bg)}
h1{font-size:16px;font-weight:600;margin:0}.sp{flex:1}.muted{color:var(--t2)}
.wrap{max-width:780px;margin:24px auto;padding:0 16px}
.card{background:var(--card);border:1px solid var(--b);border-radius:14px;padding:22px}
.tags span{display:inline-block;background:#23262f;border:1px solid var(--b);border-radius:6px;padding:2px 9px;font-size:12px;margin-right:6px;color:var(--t2)}
.text{font-size:20px;font-weight:500;margin:14px 0}
.hyp{font-size:13px;color:var(--t2);background:#16181d;border-radius:8px;padding:10px 12px;margin:10px 0}
audio{width:100%;margin:12px 0}
.row{display:flex;align-items:center;gap:10px;margin:14px 0;flex-wrap:wrap}.row b{width:120px;color:var(--t2);font-weight:500;font-size:13px}
.ind{margin:16px 0}.ihead{font-size:13px;margin-bottom:7px}.ihead b{color:var(--t);font-weight:600}.exp{color:var(--t2);font-weight:400;margin-left:8px}
.leg{font-size:12px;color:var(--t2);background:#16181d;border-radius:8px;padding:9px 12px;margin:10px 0;line-height:1.6}.leg b{color:var(--t);font-weight:500}
.btn{background:#23262f;border:1px solid var(--b);color:var(--t);border-radius:8px;padding:7px 13px;cursor:pointer;font-size:14px}
.btn:hover{border-color:var(--ac)}.btn.on{background:var(--ac);color:#08111f;border-color:var(--ac);font-weight:600}
.btn.ok.on{background:var(--ok);color:#06210f}.btn.no.on{background:var(--no);color:#2a0808}
.nav{display:flex;gap:10px;margin-top:20px}.nav .btn{flex:1;text-align:center;padding:10px}
input[type=text]{flex:1;background:#16181d;border:1px solid var(--b);color:var(--t);border-radius:8px;padding:8px 10px}
.bar{height:5px;background:#23262f;border-radius:3px;overflow:hidden;flex:1;max-width:220px}.bar>i{display:block;height:100%;background:var(--ac)}
table{width:100%;border-collapse:collapse;margin:10px 0}td,th{padding:7px 10px;border-bottom:1px solid var(--b);text-align:left;font-size:14px}
th{color:var(--t2);font-weight:500}.k{font-size:11px;color:var(--t2);margin-left:6px}
#ins{display:none}.warn{color:var(--am)}
</style></head><body>
<header><h1>🎧 Rate — TTS pt-BR</h1><div class=bar><i id=prog></i></div><span class=muted id=cnt></span><div class=sp></div>
<button class=btn onclick=toggleView()>Insights <span class=k>I</span></button></header>
<div class=wrap>
<div id=rate><div class=card id=card></div>
<div class=nav><button class=btn onclick=go(-1)>← Anterior <span class=k>←</span></button>
<button class=btn onclick=play()>▶ Tocar <span class=k>espaço</span></button>
<button class=btn onclick=go(1)>Próximo → <span class=k>→</span></button></div>
<p class=muted style=margin-top:14px>Teclas: <b>espaço</b> tocar · <b>1-5</b> nota geral · <b>P</b> parou certo · <b>←/→</b> navegar</p></div>
<div id=ins></div></div>
<script>
let clips=[],ratings={},i=0;
const K=(r,id)=>r+''+id;
async function boot(){clips=await(await fetch('/api/clips')).json();ratings=await(await fetch('/api/ratings')).json();render()}
function cur(){return clips[i]}
function rOf(c){return ratings[K(c.run,c.id)]||{}}
function render(){const c=cur();if(!c){document.getElementById('card').innerHTML='Nenhum áudio em runpod_samples/.';return}
const r=rOf(c);const dur=c.dur_s!=null?c.dur_s+'s':'?';const cap=c.dur_s!=null&&c.dur_s>=12.7;
document.getElementById('card').innerHTML=`
<div class=tags><span>${c.run}</span><span>${c.id}</span><span>${c.emotion}</span><span>${c.accent}</span>
<span>dur ${dur}${cap?' <b class=warn>(no teto!)</b>':''}</span>${c.wer!=null?`<span>WER ${Math.round(c.wer*100)}%</span>`:''}</div>
<div class=text>${esc(c.text)}</div>
${c.hyp?`<div class=hyp>ASR ouviu: "${esc(c.hyp)}"</div>`:''}
<audio id=au controls src="/audio?run=${encodeURIComponent(c.run)}&id=${encodeURIComponent(c.id)}"></audio>
<div class=leg><b>Como ler os números acima:</b> <b>WER</b> = erro do reconhecedor de fala (quão longe o áudio ficou do texto-alvo; <b>menor = mais inteligível</b>, 0% = perfeito) · <b>dur</b> = duração gerada · <b>"no teto"</b> = bateu no limite de tokens e não parou (balbúcio).</div>
<div class=ind><div class=ihead><b>Nota geral</b><span class=exp>impressão geral do áudio · 1 = ruim, 5 = perfeito · teclas 1-5</span></div>${[1,2,3,4,5].map(n=>`<button class="btn ${r.geral==n?'on':''}" onclick="setv('geral',${n})">${n}</button>`).join('')}</div>
<div class=ind><div class=ihead><b>Parou certo?</b><span class=exp>parou na hora certa ou continuou viajando (balbuciou)? · tecla P</span></div>
<button class="btn ok ${r.parou===true?'on':''}" onclick="setv('parou',true)">sim, parou</button>
<button class="btn no ${r.parou===false?'on':''}" onclick="setv('parou',false)">não, balbuciou</button></div>
${c.run.includes('stage')||c.run.includes('pedro')||c.run.includes('voz')?
`<div class=ind><div class=ihead><b>Soa como o Pedro?</b><span class=exp>o timbre/voz parece a tua? · 1 = nada a ver, 5 = idêntico</span></div>${[1,2,3,4,5].map(n=>`<button class="btn ${r.voz==n?'on':''}" onclick="setv('voz',${n})">${n}</button>`).join('')}</div>`:''}
<div class=ind><div class=ihead><b>Natural?</b><span class=exp>soa humano e fluido, ou robótico/artificial? · 1 = robótico, 5 = natural</span></div>${[1,2,3,4,5].map(n=>`<button class="btn ${r.natural==n?'on':''}" onclick="setv('natural',${n})">${n}</button>`).join('')}</div>
<div class=ind><div class=ihead><b>Sotaque carioca?</b><span class=exp>tem o sotaque/registro carioca esperado?</span></div>
<button class="btn ${r.sotaque=='carioca'?'on':''}" onclick="setv('sotaque','carioca')">carioca ✓</button>
<button class="btn ${r.sotaque=='nao'?'on':''}" onclick="setv('sotaque','nao')">não</button></div>
<div class=ind><div class=ihead><b>Nota livre</b><span class=exp>o que você notou (ex: cortou no fim, chiado, emoção errada, ótima entonação)</span></div><input type=text id=nota value="${esc(r.nota||'')}" onchange="setv('nota',this.value)" placeholder="observações..."></div>`;
const rated=clips.filter(c=>rOf(c).geral!=null).length;
document.getElementById('cnt').textContent=`${i+1}/${clips.length} · ${rated} avaliados`;
document.getElementById('prog').style.width=(100*rated/clips.length)+'%';}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
async function setv(k,v){const c=cur();const r=rOf(c);r[k]=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;
await fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});
render();if(k=='geral')setTimeout(()=>go(1),250);}
function go(d){i=Math.max(0,Math.min(clips.length-1,i+d));render();setTimeout(play,120)}
function play(){const a=document.getElementById('au');if(a){if(a.paused)a.play();else a.pause()}}
function toggleView(){const v=document.getElementById('ins'),rt=document.getElementById('rate');
if(v.style.display=='block'){v.style.display='none';rt.style.display='block'}else{showIns()}}
async function showIns(){const d=await(await fetch('/api/insights')).json();
const tbl=(o,h)=>`<table><tr><th>${h}</th><th>n</th><th>geral</th><th>parou%</th><th>voz</th><th>natural</th></tr>`+
Object.entries(o).map(([k,a])=>`<tr><td>${k}</td><td>${a.n}</td><td>${a.geral??'-'}</td><td>${a.parou_pct??'-'}</td><td>${a.voz??'-'}</td><td>${a.natural??'-'}</td></tr>`).join('')+'</table>';
document.getElementById('ins').innerHTML=`<div class=card><h2 style=font-size:16px>Insights — ${d.total_rated}/${d.total} avaliados</h2>
<h3 style="font-size:14px;color:var(--t2)">Por run (qual modelo é melhor)</h3>${tbl(d.por_run,'run')}
<h3 style="font-size:14px;color:var(--t2)">Por emoção (o que falha)</h3>${tbl(d.por_emocao,'emoção')}
<h3 style="font-size:14px;color:var(--t2)">Piores clipes (focar aqui)</h3>
<table><tr><th>run</th><th>id</th><th>geral</th><th>parou</th><th>texto</th></tr>${d.piores.map(p=>`<tr><td>${p.run}</td><td>${p.id}</td><td>${p.geral}</td><td>${p.parou?'✓':'✗'}</td><td class=muted>${esc(p.text)}</td></tr>`).join('')}</table></div>`;
document.getElementById('ins').style.display='block';document.getElementById('rate').style.display='none';}
document.addEventListener('keydown',e=>{if(e.target.tagName=='INPUT')return;
if(e.key==' '){e.preventDefault();play()}else if(e.key>='1'&&e.key<='5')setv('geral',+e.key)
else if(e.key.toLowerCase()=='p')setv('parou',!(rOf(cur()).parou===true))
else if(e.key=='ArrowRight')go(1)else if(e.key=='ArrowLeft')go(-1)
else if(e.key.toLowerCase()=='i')toggleView()});
boot();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)): body = json.dumps(body).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/':
            self._send(200, PAGE, 'text/html; charset=utf-8')
        elif u.path == '/api/clips':
            self._send(200, build_manifest())
        elif u.path == '/api/ratings':
            self._send(200, {f"{k[0]}{k[1]}": v for k, v in load_ratings().items()})
        elif u.path == '/api/insights':
            self._send(200, insights())
        elif u.path == '/audio':
            run = q.get('run', [''])[0]; cid = q.get('id', [''])[0]
            matches = list((SAMPLES / run).rglob(f'{cid}.wav'))
            if matches:
                data = matches[0].read_bytes()
                self.send_response(200); self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(data))); self.end_headers()
                self.wfile.write(data)
            else:
                self._send(404, b'no audio', 'text/plain')
        else:
            self._send(404, b'404', 'text/plain')

    def do_POST(self):
        if self.path == '/api/rate':
            n = int(self.headers.get('Content-Length', 0))
            r = json.loads(self.rfile.read(n))
            with open(RATINGS, 'a', encoding='utf-8') as f:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
            self._send(200, {'ok': True})
        else:
            self._send(404, b'404', 'text/plain')


if __name__ == '__main__':
    n = len(build_manifest())
    print(f"🎧 Rate — {n} áudios em {SAMPLES}")
    print(f"   Abra: http://localhost:{ARGS.port}   (notas → {RATINGS})")
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{ARGS.port}')).start()
    ThreadingHTTPServer(('127.0.0.1', ARGS.port), H).serve_forever()
