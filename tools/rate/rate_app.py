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
.wrap{max-width:780px;margin:30px auto;padding:0 20px}.card{background:var(--surface);border:1px solid var(--b);border-radius:var(--radius);padding:24px;margin-bottom:16px}
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
<button class=btn onclick=go(1)>→ <span class=k>→</span></button></div></div>
<div id=in class=hide></div>
<div id=tr class=hide></div>
</div>
<script>
let clips=[],ratings={},i=0;
const K=(r,id)=>r+'|'+id;
const NUM=[1,2,3,4,5];
const PROBS=["sotaque gringo","fonema errado","entonação robótica","cortou/incompleto","ruído/chiado","emoção errada","repetiu","rápido/devagar","metálico/artefato"];
async function boot(){clips=await(await fetch('/api/clips')).json();ratings=await(await fetch('/api/ratings')).json();renderTrail();render();}
function cur(){return clips[i];}
function rOf(c){return ratings[K(c.run,c.id)]||{};}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function scale(field,r,lo,hi){return `<div class=ihead><b>${field.label}</b><span class=exp>${field.exp}</span></div>`+NUM.map(n=>`<button class="btn ${r[field.k]==n?'on':''}" onclick="setv('${field.k}',${n})">${n}</button>`).join('')+`<span class=exp>${lo} → ${hi}</span>`;}
function render(){
 const c=cur();if(!c){document.getElementById('card').innerHTML='Nenhum áudio em runpod_samples/.';return;}
 const r=rOf(c);const dur=c.dur_s!=null?c.dur_s+'s':'?';const cap=c.dur_s!=null&&c.dur_s>=12.7;
 const isVoz=c.run.includes('stage')||c.run.includes('pedro')||c.run.includes('voz');
 let h=`<div class=tags><span>${c.run}</span><span>${c.id}</span><span>${c.emotion}</span><span>${c.accent}</span><span>dur ${dur}${cap?' <b class=warn>(no teto!)</b>':''}</span>${c.wer!=null?`<span>WER ${Math.round(c.wer*100)}%</span>`:''}</div>
 <div class=text>${esc(c.text)}</div>${c.hyp?`<div class=hyp>ASR ouviu: "${esc(c.hyp)}"</div>`:''}
 <audio id=au controls src="/audio?run=${encodeURIComponent(c.run)}&id=${encodeURIComponent(c.id)}"></audio>
 <div class=leg><b>WER</b> = erro do reconhecedor (palavras certas? menor=melhor) — mas <b>NÃO</b> mede sotaque. Um áudio pode ter WER 0% e soar gringo: por isso os critérios abaixo.</div>`;
 h+=`<div class=ind>`+scale({k:'geral',label:'Nota geral',exp:'impressão geral · teclas 1-5'},r,'1 ruim','5 perfeito')+`</div>`;
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
 h+=`<div class=ind><div class=ihead><b>Nota livre</b></div><input type=text id=nota value="${esc(r.nota||'')}" onchange="setv('nota',this.value)" placeholder="observações..."></div>`;
 document.getElementById('card').innerHTML=h;
 const rated=clips.filter(x=>rOf(x).geral!=null).length;
 document.getElementById('cnt').textContent=`${i+1}/${clips.length} · ${rated} avaliados`;
 document.getElementById('prog').style.width=(clips.length?100*rated/clips.length:0)+'%';
}
async function save(r){await fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});}
async function setv(k,v){const c=cur();const r=rOf(c);r[k]=v;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;await save(r);render();if(k=='geral'){setTimeout(()=>go(1),250);}}
async function togProb(p){const c=cur();const r=rOf(c);const a=r.problemas||[];const j=a.indexOf(p);if(j<0){a.push(p);}else{a.splice(j,1);}r.problemas=a;r.run=c.run;r.id=c.id;r.ts=Date.now();ratings[K(c.run,c.id)]=r;await save(r);render();}
function go(d){i=Math.max(0,Math.min(clips.length-1,i+d));render();setTimeout(play,120);}
function play(){const a=document.getElementById('au');if(a){if(a.paused){a.play();}else{a.pause();}}}
function view(v){
 for(const x of ['av','in','tr']){document.getElementById(x).classList.toggle('hide',x!=v);}
 document.getElementById('tAv').classList.toggle('on',v=='av');
 document.getElementById('tIn').classList.toggle('on',v=='in');
 document.getElementById('tTr').classList.toggle('on',v=='tr');
 if(v=='in'){showIns();}
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
function renderTrail(){document.getElementById('tr').innerHTML=TRAIL;}
document.addEventListener('keydown',e=>{
 if(e.target.tagName=='INPUT')return;
 if(!document.getElementById('av').classList.contains('hide')){
  if(e.key==' '){e.preventDefault();play();}
  else if(e.key>='1'&&e.key<='5'){setv('geral',+e.key);}
  else if(e.key.toLowerCase()=='p'){setv('parou',!(rOf(cur()).parou===true));}
  else if(e.key=='ArrowRight'){go(1);}
  else if(e.key=='ArrowLeft'){go(-1);}
 }
});
const TRAIL=`__TRAIL__`;
boot();
</script></body></html>"""


TRAIL_HTML = """
<div class="card trail">
<h2>🧭 Trilha do projeto — onde estamos e pra onde vamos</h2>
<p class=muted>Objetivo: TTS conversacional pt-BR "nível Maya da Sesame" — voz do Pedro, emoções, sotaque carioca, baixa latência.</p>

<h3>📍 Onde estamos AGORA (15-16/jun)</h3>
<ul>
<li><b>Modelo pt (cml_long):</b> <span class=pill go>WER 21%</span> — CSM-1B finetunado fala português.</li>
<li><b>Voz do Pedro (stage_b_final):</b> <span class=pill go>WER 17% · para 14/14</span> — tua voz falando pt e parando direito.</li>
<li><b>Bloqueio resolvido:</b> o balbúcio (modelo não parava) — era o token de fim nunca supervisionado. <span class=pill go>EOS corrigido</span></li>
<li><b>O que falta de qualidade:</b> sotaque às vezes "gringo" (fonemas), emoções pouco controladas, dataset da voz é mono-emoção → é o que esta avaliação vai medir.</li>
</ul>

<h3>🛣️ As 3 abordagens (Trilhas)</h3>
<table><tr><th>Trilha</th><th>O que é</th><th>Status</th><th>Próximo</th></tr>
<tr><td><b>A — A Voz</b></td><td>TTS expressivo com a voz do Pedro. Pool: Qwen3-TTS, Chatterbox-pt-br, <b>CSM-1B</b> (escolhido)</td><td><span class=pill wip>em andamento</span> cml_long + stage_b_final feitos</td><td>curar dataset → emoções → sotaque nativo; testar Qwen3-TTS como alternativa</td></tr>
<tr><td><b>B — A Conversa</b></td><td>Spine full-duplex (fala e ouve junto) — Moshi (Kyutai) + Mimi</td><td><span class=pill next>não começou</span></td><td>flywheel de reuniões (dados estéreo) → Moshi LoRA pt-BR (F4)</td></tr>
<tr><td><b>M — Maya</b></td><td>Engenharia reversa da Maya: cascata ASR→LLM→CSM (a Maya é cascata, confirmado pelo CTO deles)</td><td><span class=pill next>scaffold</span> (src/duplex)</td><td>montar Maya-BR v0 quando o CSM-pt estiver bom (A entrega a peça-voz)</td></tr>
</table>
<p class=muted>A voz do Pedro (dataset) serve às TRÊS. Se a Maya (M) se provar, vira a abordagem principal.</p>

<h3>⚙️ Pipeline que usamos (Trilha A / CSM)</h3>
<ul>
<li><b>Estágio A — ensinar português:</b> CSM-1B + LoRA sobre corpus pt. Receita vencedora: CML, LR <b>5e-4</b>, 180min, áudio real, warmup_steps=20 → WER 21%.</li>
<li><b>Estágio B — voz do Pedro:</b> funde a base pt + LoRA novo nos clipes do Pedro (LR baixo 5e-5, curto, pra não overfittar). + fix do EOS → para de balbuciar.</li>
<li><b>Stack:</b> HF puro (não Unsloth, que quebrou), transformers==4.52.3, torchcodec==0.7, rodando em H100 RunPod via SSH.</li>
</ul>

<h3>📚 Datasets — o que usamos, quais partes, como</h3>
<table><tr><th>Dataset</th><th>O que é</th><th>Como usamos</th></tr>
<tr><td><b>CML-TTS</b> (68h, CC-BY)</td><td>leitura limpa de audiobook, pt formal</td><td>~8000 clipes via streaming → Estágio A (deu WER 21%). Registro de "leitura de livro", não conversa.</td></tr>
<tr><td><b>TAGARELA</b> (NC, eval-only)</td><td>podcast espontâneo, fala real carioca</td><td>tentamos pro registro CERTO; o WER favorece CML mas o DS diz que TAGARELA é o registro do produto. Crash corrigido, falta rodar completo.</td></tr>
<tr><td><b>MLS-pt</b> (161h, CC-BY)</td><td>leitura, mais volume</td><td>metade do "mix" (CML+MLS) — testado.</td></tr>
<tr><td><b>ElevenLabs (voz do Pedro)</b></td><td>48min, 362 clipes (carioca-medio)</td><td>Estágio B (tua voz). Problema: 1 sessão, mono-emoção, transcrições do Whisper com erro → <b>curar com o curate_app</b>.</td></tr>
</table>

<h3>🧠 O que aprendemos e implementamos (técnico)</h3>
<ul>
<li><b>Warmup time-capped:</b> usar steps fixos (não ratio) — senão o LR fica em ~0 e não aprende.</li>
<li><b>Streaming decode=False:</b> baixar só os clipes usados (não o dataset inteiro) — disco + velocidade.</li>
<li><b>Áudio real (sem pad de 12s):</b> o pad de silêncio ensinava o modelo a "encher 12s".</li>
<li><b>EOS = frame todo-zero:</b> supervisionar com label 0 (não o token 128003, que estoura o codebook) → o modelo aprende a PARAR.</li>
<li><b>Stage B overfit:</b> dataset pequeno (272 clipes) → LR baixo + run curto.</li>
<li><b>Método:</b> revisar a causa raiz + smoke-test representativo ANTES de gastar GPU. (Detalhes em research/JORNADA-2026-06-16.md)</li>
</ul>

<h3>🎯 Pra onde vamos (por trilha)</h3>
<ul>
<li><b>A (voz):</b> (1) curar o dataset; (2) re-treinar Estágio B sobre o dataset limpo; (3) gravar <b>emoções variadas</b> (G2) e mais vozes; (4) atacar o "sotaque gringo" (esta avaliação aponta onde); (5) Qwen3-TTS como braço alternativo.</li>
<li><b>B (conversa):</b> gravar as reuniões da UNFLAT (flywheel, dados estéreo) → Moshi LoRA pt-BR.</li>
<li><b>M (Maya):</b> com a voz pronta, montar Maya-BR v0 = CSM-pt + LLM (Sabiá/Gemini) + turn-engine (barge-in) → comparar com a Maya real.</li>
</ul>
<p class=muted>Esta avaliação alimenta o passo (4) da Trilha A: suas notas de "nativo/natural/sotaque" + as tags de problema viram o direcional do próximo modelo.</p>
</div>
"""


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
            page = PAGE.replace('__TRAIL__', TRAIL_HTML.replace('`', "'").replace('\\', ''))
            self._send(200, page, 'text/html; charset=utf-8')
        elif u.path == '/api/clips':
            self._send(200, build_manifest())
        elif u.path == '/api/ratings':
            self._send(200, {f"{k[0]}|{k[1]}": v for k, v in load_ratings().items()})
        elif u.path == '/api/insights':
            self._send(200, insights())
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
            with open(RATINGS, 'a', encoding='utf-8') as f:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
            self._send(200, {'ok': True})
        else:
            self._send(404, b'404', 'text/plain')


if __name__ == '__main__':
    n = len(build_manifest())
    print(f"🎧 Rate — {n} áudios · Avaliar / Insights / Trilha")
    print(f"   http://localhost:{ARGS.port}   (notas → {RATINGS.name})")
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{ARGS.port}')).start()
    ThreadingHTTPServer(('127.0.0.1', ARGS.port), H).serve_forever()
