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
import argparse, json, os, statistics, urllib.parse, webbrowser, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RATINGS = Path(__file__).resolve().parent / 'ratings.jsonl'
MAP_JSON = Path(__file__).resolve().parent / 'trilha_map.json'
_RLOCK = threading.Lock()
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
            clips.append({
                'run': run_dir.name, 'id': cid,
                'emotion': b.get('emotion', '?'), 'accent': b.get('accent', '?'),
                'text': b.get('text', ps.get('ref', '')),
                'wer': ps.get('wer'), 'dur_s': ps.get('dur_s'), 'hyp': ps.get('hyp', ''),
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
    return {'total_rated': len(rated), 'total': len(clips),
            'por_run': {k: agg(v) for k, v in sorted(by_run.items())},
            'por_emocao': {k: agg(v) for k, v in sorted(by_emo.items())},
            'problemas': dict(sorted(probs.items(), key=lambda x: -x[1]))}


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
.dots{display:flex;flex-wrap:wrap;gap:5px;margin:14px 2px 0}
.pdot{width:8px;height:8px;border-radius:999px;background:var(--tf);cursor:pointer;transition:all .15s var(--ease)}.pdot:hover{transform:scale(1.3)}.pdot.done{background:var(--green)}.pdot.cur{outline:1px solid var(--t);outline-offset:2px}
.panelbg{position:fixed;inset:0;background:rgba(0,0,0,0.5);opacity:0;pointer-events:none;transition:opacity 0.22s var(--ease);z-index:55}.panelbg.open{opacity:1;pointer-events:auto}
.panel{position:fixed;top:0;right:0;width:min(440px,94vw);height:100vh;background:var(--bg);border-left:1px solid var(--bh);padding:26px 26px 60px;overflow-y:auto;transform:translateX(100%);transition:transform 0.28s var(--ease);z-index:60}.panel.open{transform:none}
.panel-x{position:absolute;top:18px;right:18px;background:var(--surface);border:1px solid var(--b);color:var(--t2);width:30px;height:30px;border-radius:8px;cursor:pointer;font-size:13px}.panel-x:hover{color:var(--t);border-color:var(--bh)}
.panel h3.pt{font-family:var(--serif);font-size:26px;font-weight:400;margin:12px 0 0;letter-spacing:-0.01em}.panel .psum{color:var(--t2);font-size:14px;margin:14px 0}
.panel .deep{color:var(--t2);font-size:14px;line-height:1.65}.panel .deep p{margin:9px 0}.panel .deep b{color:var(--t)}.panel .deep code{font-family:var(--mono);font-size:12px;background:var(--surface-h);padding:1px 5px;border-radius:4px;color:var(--t)}.panel .deep ul{margin:9px 0 9px 18px}.panel .deep li{margin:4px 0}
.panel .hyp{display:block;margin:7px 0;cursor:default}
.links{display:flex;flex-wrap:wrap;gap:7px}.linknode{font-size:12px;padding:5px 10px;border-radius:7px;border:1px solid var(--b);background:var(--surface);color:var(--t2);cursor:pointer}.linknode:hover{border-color:var(--bh);color:var(--t)}
.toast{position:fixed;bottom:26px;left:50%;transform:translateX(-50%) translateY(16px);background:rgba(18,18,22,0.92);border:1px solid var(--bh);color:var(--t);padding:8px 16px;border-radius:999px;font-family:var(--mono);font-size:11px;letter-spacing:0.04em;opacity:0;transition:all 0.25s var(--ease);pointer-events:none;z-index:50;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
</style></head><body>
<header><h1>🎧 TTS pt-BR</h1>
<button class="tab on" id=tAv onclick=view('av')>Avaliar</button>
<button class=tab id=tIn onclick=view('in')>Insights</button>
<button class=tab id=tTr onclick=view('tr')>Trilha</button>
<div class=bar><i id=prog></i></div><span class=muted id=cnt></span><div class=sp></div></header>
<div class=wrap>
<div id=av><div class=card id=card></div>
<div class=nav><button class=btn onclick=go(-1)>← <span class=k>←</span></button>
<button class=btn onclick=play()>▶ Tocar <span class=k>espaço</span></button>
<button class=btn onclick=go(1)>Próximo → <span class=k>→</span></button></div>
<div id=dots class=dots></div></div>
<div id=in class=hide></div>
<div id=tr class=hide></div>
</div>
<div id=toast class=toast></div>
<div id=panelbg class=panelbg onclick=closePanel()></div>
<div id=panel class=panel></div>
<script>
let clips=[],ratings={},i=0;
let MAP={nodes:[],lanes:[],hypotheses:[],state:{now:'',next:[]}};
const _sq={};
const K=(r,id)=>r+'|'+id;
const NUM=[1,2,3,4,5];
const PROBS=["sotaque gringo","fonema errado","entonação robótica","cortou/incompleto","ruído/chiado","emoção errada","repetiu","rápido/devagar","metálico/artefato"];
async function boot(){clips=await(await fetch('/api/clips')).json();ratings=await(await fetch('/api/ratings')).json();try{MAP=await(await fetch('/api/map')).json();}catch(e){}renderTrail();render();}
function cur(){return clips[i];}
function rOf(c){return ratings[K(c.run,c.id)]||{};}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function scale(field,r,lo,hi){return `<div class=ihead><b>${field.label}</b><span class=exp>${field.exp}</span></div>`+NUM.map(n=>`<button class="btn ${r[field.k]==n?'on':''}" onclick="setv('${field.k}',${n})">${n}</button>`).join('')+`<span class=exp>${lo} → ${hi}</span>`;}
function render(){
 const c=cur();if(!c){document.getElementById('card').innerHTML='Nenhum áudio em runpod_samples/.';return;}
 const dur=c.dur_s!=null?c.dur_s+'s':'?';const cap=c.dur_s!=null&&c.dur_s>=12.7;
 const done=rOf(c).geral!=null;
 let h=`<div class=tags><span>${c.run}</span><span>${c.id}</span><span>${c.emotion}</span><span>${c.accent}</span><span>dur ${dur}${cap?' <b class=warn>(no teto!)</b>':''}</span>${c.wer!=null?`<span>WER ${Math.round(c.wer*100)}%</span>`:''}${done?'<span style="border-color:var(--green);color:var(--green)">✓ avaliado</span>':'<span style="border-color:var(--orange);color:var(--orange)">○ pendente</span>'}</div>
 <div class=text>${esc(c.text)}</div>${c.hyp?`<div class=hyp>ASR ouviu: "${esc(c.hyp)}"</div>`:''}
 <audio id=au controls src="/audio?run=${encodeURIComponent(c.run)}&id=${encodeURIComponent(c.id)}"></audio>
 <div class=leg><b>WER</b> = erro do reconhecedor (palavras certas? menor=melhor) — mas <b>NÃO</b> mede sotaque. Um áudio pode ter WER 0% e soar gringo: por isso os critérios abaixo.</div>
 <div id=ctrls></div>`;
 document.getElementById('card').innerHTML=h;
 renderCtrls();updateCount();
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
function updateCount(){
 const rated=clips.filter(x=>rOf(x).geral!=null).length;
 document.getElementById('cnt').textContent=`${i+1}/${clips.length} · ${rated} avaliados`;
 document.getElementById('prog').style.width=(clips.length?100*rated/clips.length:0)+'%';
 renderDots();
}
function renderDots(){const el=document.getElementById('dots');if(!el)return;el.innerHTML=clips.map(function(c,idx){return '<i class="pdot'+(rOf(c).geral!=null?' done':'')+(idx==i?' cur':'')+'" title="'+esc(c.run+' · '+c.id)+'" onclick="i='+idx+';render();setTimeout(playFresh,140)"></i>';}).join('');}
async function save(r){await fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});}
function queueSave(c,r){const key=K(c.run,c.id);const prev=_sq[key]||Promise.resolve();const p=prev.then(function(){return save(Object.assign({},r));}).catch(function(){});_sq[key]=p;return p;}
function setv(k,v){const c=cur();const r=rOf(c);r[k]=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;renderCtrls();updateCount();flash('salvo ✓');queueSave(c,r);}
function saveNota(v){const c=cur();const r=rOf(c);r.nota=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;clearTimeout(window._nt);window._nt=setTimeout(function(){queueSave(c,r);},400);}
function flash(m){const t=document.getElementById('toast');if(!t)return;t.textContent=m;t.classList.add('show');clearTimeout(window._ft);window._ft=setTimeout(function(){t.classList.remove('show');},900);}
function togProb(p){const c=cur();const r=rOf(c);const a=r.problemas||[];const j=a.indexOf(p);if(j<0){a.push(p);}else{a.splice(j,1);}r.problemas=a;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;renderCtrls();flash('salvo ✓');queueSave(c,r);}
function go(d){i=Math.max(0,Math.min(clips.length-1,i+d));render();setTimeout(playFresh,140);}
function playFresh(){const a=document.getElementById('au');if(a){const p=a.play();if(p)p.catch(function(){});}}
function play(){const a=document.getElementById('au');if(!a)return;if(a.paused){const p=a.play();if(p)p.catch(function(){flash('autoplay bloqueado — aperte ▶');});}else{a.pause();}}
function view(v){
 for(const x of ['av','in','tr']){document.getElementById(x).classList.toggle('hide',x!=v);}
 document.getElementById('tAv').classList.toggle('on',v=='av');
 document.getElementById('tIn').classList.toggle('on',v=='in');
 document.getElementById('tTr').classList.toggle('on',v=='tr');
 if(v=='in'){showIns();}
 if(v=='tr'){requestAnimationFrame(drawEdges);}
}
async function showIns(){
 const d=await(await fetch('/api/insights')).json();
 const tbl=(o,hd)=>`<table><tr><th>${hd}</th><th>n</th><th>geral</th><th>nativo</th><th>natural</th><th>voz</th><th>parou%</th></tr>`+
  Object.entries(o).map(([k,a])=>`<tr><td>${k}</td><td>${a.n}</td><td>${a.geral??'-'}</td><td>${a.nativo??'-'}</td><td>${a.natural??'-'}</td><td>${a.voz??'-'}</td><td>${a.parou_pct??'-'}</td></tr>`).join('')+`</table>`;
 const probs=Object.entries(d.problemas||{});
 document.getElementById('in').innerHTML=`<div class=card><h2>Insights — ${d.total_rated}/${d.total} avaliados</h2>
 <h3>Por run (qual modelo é melhor)</h3>${tbl(d.por_run,'run')}
 <h3>Por emoção (o que falha)</h3>${tbl(d.por_emocao,'emoção')}
 <h3>Problemas mais comuns → o que o próximo treino deve atacar</h3>
 ${probs.length?`<table><tr><th>problema</th><th>nº de clipes</th></tr>${probs.map(([p,n])=>`<tr><td>${p}</td><td>${n}</td></tr>`).join('')}</table>`:'<p class=muted>marque tags de problema nos áudios pra ver o ranking aqui.</p>'}</div>`;
}
const STATUS={done:'feito',wip:'em curso',next:'a seguir',idea:'hipótese'};
function renderTrail(){
 const m=MAP;
 const overall=m.lanes&&m.lanes.length?Math.round(m.lanes.reduce(function(s,l){return s+l.progress;},0)/m.lanes.length):0;
 let h=`<div class=card><h2>🧭 Trilha do projeto</h2>
  <p class=trail>${esc((m.state&&m.state.now)||'')}</p>
  <div class=t-over><div class=lane-bar style="width:280px;height:4px"><i style="width:${overall}%"></i></div><span class=lane-pct>${overall}% no geral</span></div>
  <div class=ihead style="margin-top:22px">Hipóteses que guiam <span class=exp>clique pra ir ao bloco</span></div>
  <div class=hyps>${(m.hypotheses||[]).map(function(hy){return `<span class="hyp ${hy.status}" onclick="openNode('${hy.node}')">${esc(hy.claim)} · <b>${hy.status}</b></span>`;}).join('')}</div>
  <div class=ihead style="margin-top:22px">Próximos passos</div>
  <ol class=nexts>${((m.state&&m.state.next)||[]).map(function(s){return `<li>${esc(s)}</li>`;}).join('')}</ol></div>`;
 h+=`<div class=card><div class=ihead>Mapa · o que depende do quê <span class=exp>clique num bloco pro aprofundamento técnico · ↔ arraste se precisar</span></div><div id=mapwrap><div id=map></div></div></div>`;
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
 if(e.key=='Escape'){closePanel();}
 const inInput=e.target.tagName=='INPUT';
 if(inInput&&!(e.key=='ArrowRight'||e.key=='ArrowLeft'))return;
 if(!document.getElementById('av').classList.contains('hide')){
  if(e.key==' '){e.preventDefault();play();}
  else if(e.key>='1'&&e.key<='5'){setv('geral',+e.key);}
  else if(e.key.toLowerCase()=='p'){setv('parou',!(rOf(cur()).parou===true));}
  else if(e.key=='ArrowRight'){if(inInput)e.target.blur();go(1);}
  else if(e.key=='ArrowLeft'){if(inInput)e.target.blur();go(-1);}
 }
});
window.addEventListener('resize',function(){if(!document.getElementById('tr').classList.contains('hide'))drawEdges();});
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
        if u.path == '/':
            self._send(200, PAGE, 'text/html; charset=utf-8')
        elif u.path == '/api/clips':
            self._send(200, build_manifest())
        elif u.path == '/api/ratings':
            self._send(200, {f"{k[0]}|{k[1]}": v for k, v in load_ratings().items()})
        elif u.path == '/api/insights':
            self._send(200, insights())
        elif u.path == '/api/map':
            self._send(200, load_map())
        elif u.path == '/audio':
            run = q.get('run', [''])[0]; cid = q.get('id', [''])[0]
            matches = list((SAMPLES / run).rglob(f'{cid}.wav'))
            if matches:
                data = matches[0].read_bytes()
                self.send_response(200); self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            else:
                self._send(404, b'no audio', 'text/plain')
        else:
            self._send(404, b'404', 'text/plain')

    def do_POST(self):
        if self.path == '/api/rate':
            n = int(self.headers.get('Content-Length', 0))
            r = json.loads(self.rfile.read(n))
            with _RLOCK:
                data = load_ratings()
                data[(r['run'], r['id'])] = r
                tmp = RATINGS.with_suffix('.tmp')
                with open(tmp, 'w', encoding='utf-8') as f:
                    for v in data.values():
                        f.write(json.dumps(v, ensure_ascii=False) + '\n')
                tmp.replace(RATINGS)
            self._send(200, {'ok': True})
        else:
            self._send(404, b'404', 'text/plain')


if __name__ == '__main__':
    n = len(build_manifest())
    print(f"🎧 Rate — {n} áudios · Avaliar / Insights / Trilha")
    print(f"   http://localhost:{ARGS.port}   (notas → {RATINGS.name})")
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{ARGS.port}')).start()
    ThreadingHTTPServer(('127.0.0.1', ARGS.port), H).serve_forever()
