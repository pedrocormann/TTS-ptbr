"""Maya-BR v0 — painel web LOCAL (localhost). A API key fica no localStorage do
SEU navegador e na memória do processo; nunca é escrita em disco nem logada.

  source .venv-duplex/bin/activate && pip install flask
  python -m src.duplex.webapp          # abre http://localhost:7860
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time

import numpy as np
from flask import Flask, Response, jsonify, request

from .asr import ASR
from .llm import LLM
from .turn_engine import SR as MIC_SR, TurnEngine
from .tts_adapter import make_tts

app = Flask(__name__)
SESSION: dict = {"thread": None, "stop": None, "events": queue.Queue(), "status": "parado"}


def emit(kind: str, text: str):
    SESSION["events"].put({"kind": kind, "text": text, "t": time.strftime("%H:%M:%S")})


def conversation_loop(cfg: dict, stop_event: threading.Event):
    try:
        emit("status", "carregando modelos…")
        if cfg.get("hf_token"):
            os.environ["HF_TOKEN"] = cfg["hf_token"]
        engine = TurnEngine(endpoint_ms=int(cfg.get("endpoint_ms", 600)),
                            device=cfg.get("device"))
        asr = ASR(model=cfg.get("asr_model", "small"))
        llm = LLM(base_url=cfg["llm_base_url"], model=cfg["llm_model"],
                  api_key=cfg.get("llm_key") or "x")
        tts = make_tts(cfg.get("tts", "pocket"), cfg.get("voice") or None,
                       language=cfg.get("tts_language") or "portuguese_24l",
                       quantize=bool(cfg.get("quantize", False)))
        engine.player.sr_out = tts.sr
        emit("status", f"🎙️ pronto — fale! (tts={cfg.get('tts')}, voz={cfg.get('voice') or 'default'})")
        SESSION["status"] = "conversando"

        while not stop_event.is_set():
            result = engine.listen_turn(stop_event=stop_event)
            if result is None:
                break
            user_audio, _ = result
            t0 = time.perf_counter()
            text = asr.transcribe(user_audio)
            t_asr = time.perf_counter()
            if not text:
                continue
            emit("user", text)
            up = np.interp(np.linspace(0, 1, int(user_audio.size * tts.sr / MIC_SR)),
                           np.linspace(0, 1, user_audio.size), user_audio).astype(np.float32)
            tts.add_context("1", text, up)

            parts, reply, t_llm1, t_tts1 = [], [], None, None
            for sent in llm.reply_stream(text):
                if stop_event.is_set():
                    break
                if t_llm1 is None:
                    t_llm1 = time.perf_counter()
                reply.append(sent)
                wav, _ = tts.synth(sent)
                if t_tts1 is None:
                    t_tts1 = time.perf_counter()
                parts.append(wav)
            if not parts or stop_event.is_set():
                continue
            emit("agent", " ".join(reply))
            emit("lat", f"asr {t_asr-t0:.2f}s · llm₁ {t_llm1-t_asr:.2f}s · "
                        f"tts₁ {t_tts1-t_llm1:.2f}s · total→1ºáudio {t_tts1-t0:.2f}s")
            engine.speak(np.concatenate(parts))
    except Exception as e:  # noqa: BLE001 — erro vai pra UI, não pro void
        emit("error", f"{type(e).__name__}: {e}")
    finally:
        SESSION["status"] = "parado"
        emit("status", "⏹ sessão encerrada")


@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")


@app.get("/devices")
def devices():
    import sounddevice as sd
    devs = [{"index": i, "name": d["name"]}
            for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]
    return jsonify(devs)


@app.post("/start")
def start():
    if SESSION["thread"] and SESSION["thread"].is_alive():
        return jsonify({"ok": False, "msg": "já rodando"}), 409
    cfg = request.get_json(force=True)
    if cfg.get("device") not in (None, ""):
        cfg["device"] = int(cfg["device"])
    else:
        cfg["device"] = None
    SESSION["stop"] = threading.Event()
    SESSION["thread"] = threading.Thread(
        target=conversation_loop, args=(cfg, SESSION["stop"]), daemon=True)
    SESSION["thread"].start()
    return jsonify({"ok": True})


@app.post("/stop")
def stop():
    if SESSION["stop"]:
        SESSION["stop"].set()
    return jsonify({"ok": True})


@app.get("/events")
def events():
    def stream():
        while True:
            try:
                ev = SESSION["events"].get(timeout=25)
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            except queue.Empty:
                yield ": ping\n\n"
    return Response(stream(), mimetype="text/event-stream")


HTML = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Maya-BR v0</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e0f12;--card:#17181d;--tx:#e8e8ea;--mut:#9a9aa5;--ac:#4ade80;--user:#60a5fa}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
font:15px/1.5 -apple-system,system-ui,sans-serif;display:flex;min-height:100vh}
.side{width:340px;padding:24px;background:var(--card);display:flex;flex-direction:column;gap:14px}
h1{font-size:18px;margin:0 0 6px}label{font-size:12px;color:var(--mut);display:block;margin-bottom:4px}
input,select{width:100%;padding:9px;border-radius:8px;border:1px solid #2a2b33;
background:#0e0f12;color:var(--tx);font-size:14px}
button{padding:12px;border:0;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer}
#go{background:var(--ac);color:#0e0f12}#go.stop{background:#f87171}
.main{flex:1;padding:24px;display:flex;flex-direction:column}
#log{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding-bottom:20px}
.msg{max-width:75%;padding:10px 14px;border-radius:14px;white-space:pre-wrap}
.user{background:#1d2b45;align-self:flex-end;border-bottom-right-radius:4px}
.agent{background:#1d3527;align-self:flex-start;border-bottom-left-radius:4px}
.status,.lat,.error{font-size:12px;color:var(--mut);align-self:center}
.error{color:#f87171}.hint{font-size:11px;color:var(--mut)}
</style></head><body>
<div class="side">
 <h1>🎙️ Maya-BR <span style="color:var(--mut);font-weight:400">v0 · local</span></h1>
 <div><label>Provedor LLM</label><select id="prov">
   <option value="https://generativelanguage.googleapis.com/v1beta/openai/">Gemini (AI Studio)</option>
   <option value="https://chat.maritaca.ai/api">Maritaca</option>
   <option value="custom">outro (URL abaixo)</option></select></div>
 <div id="customUrlBox" style="display:none"><label>Base URL</label><input id="customUrl" placeholder="https://…/v1"></div>
 <div><label>Modelo</label><input id="model" value="gemini-2.5-flash"></div>
 <div><label>API key <span class="hint">(fica só no seu navegador)</span></label>
   <input id="key" type="password" placeholder="cole aqui"></div>
 <div><label>Voz (TTS Pocket pt) <span class="hint">wav próprio = clone (exige HF token)</span></label>
   <input id="voice" value="rafael" placeholder="rafael | caminho/do/seu.wav"></div>
 <div><label>Qualidade do TTS</label><select id="quality">
   <option value="portuguese_24l">melhor (24 camadas, ~1,8× RT)</option>
   <option value="portuguese">rápida (6 camadas, ~5× RT)</option></select></div>
 <div><label>HF token <span class="hint">(opcional, só pra clonar voz)</span></label>
   <input id="hf" type="password" placeholder="hf_…"></div>
 <div><label>Microfone</label><select id="device"></select></div>
 <button id="go" onclick="toggle()">▶ Iniciar conversa</button>
 <div class="hint">Fale naturalmente — o VAD detecta. Interrompa falando por cima.
 Latências aparecem no chat. Key nunca é salva em disco.</div>
</div>
<div class="main"><div id="log"></div></div>
<script>
const $=id=>document.getElementById(id);let running=false;
for(const k of ['key','hf','model','voice'])
  if(localStorage['maya_'+k]) $(k).value=localStorage['maya_'+k];
$('prov').onchange=()=>{ $('customUrlBox').style.display = $('prov').value==='custom'?'block':'none';
  if($('prov').value.includes('maritaca')&&!localStorage['maya_model_m']) $('model').value='sabia-3'; };
fetch('/devices').then(r=>r.json()).then(ds=>{
  $('device').innerHTML='<option value="">(padrão do sistema)</option>'+
    ds.map(d=>`<option value="${d.index}">${d.index} · ${d.name}</option>`).join('');
  const wave=ds.find(d=>/wave link microphonefx/i.test(d.name)); if(wave) $('device').value=wave.index;});
function add(kind,text){const d=document.createElement('div');
  d.className = kind==='user'?'msg user':kind==='agent'?'msg agent':kind;
  d.textContent=(kind==='user'?'🧑 ':kind==='agent'?'🤖 ':'')+text;
  $('log').appendChild(d);$('log').scrollTop=1e9;}
new EventSource('/events').onmessage=e=>{const ev=JSON.parse(e.data);add(ev.kind,ev.text);
  if(ev.kind==='status'&&ev.text.includes('encerrada')){running=false;paint();}};
function paint(){$('go').textContent=running?'⏹ Parar':'▶ Iniciar conversa';
  $('go').classList.toggle('stop',running);}
async function toggle(){
  if(running){await fetch('/stop',{method:'POST'});running=false;paint();return;}
  for(const k of ['key','hf','model','voice']) localStorage['maya_'+k]=$(k).value;
  const base = $('prov').value==='custom'?$('customUrl').value:$('prov').value;
  const cfg={llm_base_url:base,llm_model:$('model').value,llm_key:$('key').value,
    tts:'pocket',voice:$('voice').value,hf_token:$('hf').value,device:$('device').value,
    tts_language:$('quality').value};
  const r=await fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(cfg)});
  if(r.ok){running=true;paint();} else add('error','já existe sessão rodando');}
</script></body></html>"""


if __name__ == "__main__":
    print("🌐 Maya-BR v0 → http://localhost:7860  (Ctrl-C para sair)")
    app.run(host="127.0.0.1", port=7860, threaded=True)
