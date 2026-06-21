#!/usr/bin/env python3
"""Porta o cockpit (rate_app PAGE) pro app deployado: interceptor de fetch → Supabase/bundle/Storage.
Saída: app-unflat/src/app/tts-ptbr/dashboard.html.ts (cockpit) + recorder.html.ts (gravador)."""
import sys, json, base64, re, pathlib

REPO = pathlib.Path.home()/"Downloads/TTS-ptbr"
APP  = pathlib.Path.home()/"Downloads/app-unflat/src/app/tts-ptbr"
SUPA_URL = "https://yyxmtjqpmkonxlinflxu.supabase.co"
SUPA_KEY = "sb_publishable_iyI5855XjkDE-7yep4f69w_A9OXFZq2"

# importa rate_app com argv controlado (build_manifest lê SAMPLES = --dir)
sys.argv = ["rate_app", "--dir", str(REPO/"runpod_samples/treino2_all")]
sys.path.insert(0, str(REPO/"tools/rate"))
import rate_app

clips  = rate_app.build_manifest()
trilha = rate_app.load_map()
bundle = {"clips": clips, "trilha": trilha, "curate": []}  # curate vazio: é pro dado do flywheel (a vir)
bundle_json = json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")
print(f"clips={len(clips)} · trilha lanes={len(trilha.get('lanes',[]))} nodes={len(trilha.get('nodes',[]))}")

# ---- PAGE ----
PAGE = rate_app.PAGE

# 1) título limpo + favicon do hub Unflat (/favicon.png)
PAGE = PAGE.replace("<title>Rate — TTS pt-BR</title>", '<title>TTS PT-BR</title><link rel="icon" href="/favicon.png">')

# 2) reescreve os 3 src de áudio pro Storage público
PAGE = PAGE.replace(
  'src="/audio?run=${encodeURIComponent(c.run)}&id=${encodeURIComponent(c.id)}"',
  'src="${AUDIO(c.run,c.id)}"')
PAGE = PAGE.replace(
  "'/audio?run='+encodeURIComponent(c.run)+'&id='+encodeURIComponent(c.id)",
  "AUDIO(c.run,c.id)")
PAGE = PAGE.replace(
  'src="/curate/audio?id=${encodeURIComponent(c.id)}"',
  'src="${CAUDIO(c.id)}"')
# novo player do Curar usa a forma concatenada
PAGE = PAGE.replace(
  '"/curate/audio?id="+encodeURIComponent(c.id)',
  'CAUDIO(c.id)')

# 3) aba Gravar → rota same-origin (getUserMedia simples)
PAGE = PAGE.replace('src="/gravar"', 'src="/tts-ptbr/gravar"')

# 4) interceptor de fetch + supabase-js (bloqueante) injetados antes do <script> do app
INTERCEPT = r"""<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function(){
const SUPA_URL=%SUPA_URL%,SUPA_KEY=%SUPA_KEY%,STORAGE=SUPA_URL+"/storage/v1/object/public";
const SB=window.supabase.createClient(SUPA_URL,SUPA_KEY);
window.AUDIO=(run,id)=>STORAGE+"/tts-eval/"+encodeURIComponent(run)+"/"+encodeURIComponent(id)+".wav";
window.CAUDIO=(id)=>STORAGE+"/tts-curate/"+encodeURIComponent(id)+".wav";
const BUNDLE=%BUNDLE%;
const jr=o=>new Response(JSON.stringify(o),{status:200,headers:{"Content-Type":"application/json"}});
const mean=a=>a.length?Math.round(a.reduce((x,y)=>x+y,0)/a.length*10)/10:null;
async function loadRatings(){const r=await SB.from("avaliacoes").select("run,clip,payload");const o={};(r.data||[]).forEach(x=>o[x.run+"|"+x.clip]=x.payload);return o;}
async function saveRate(x){await SB.from("avaliacoes").upsert({run:x.run,clip:x.id,payload:x,atualizado:new Date().toISOString()});return jr({ok:true});}
async function loadCurate(){const r=await SB.from("curar_itens").select("*").order("usuario");return (r.data||[]).map(x=>({id:x.id,usuario:x.usuario,audio:x.audio,style:"",dur_s:x.dur_s,text_orig:x.text_orig,text_v2:x.text_v2,text:x.texto,keep:x.manter,flags:x.flags||[],edited:x.editado,emocoes:x.emocoes||[],emocoes_auto:x.emocoes_auto||[],delivery:x.delivery||[],eventos:x.eventos||[],estilo_nl:x.estilo_nl||""}));}
async function saveCurate(b){await SB.from("curar_itens").update({texto:b.text,manter:b.keep,flags:b.flags||[],emocoes:b.emocoes||[],delivery:b.delivery||[],eventos:b.eventos||[],estilo_nl:b.estilo_nl||null,intensidade:b.intensidade||null,editado:true}).eq("id",b.id);return jr({ok:true});}
async function insights(){
 const R=await loadRatings();
 const rated=BUNDLE.clips.map(c=>Object.assign({},c,R[c.run+"|"+c.id]||{})).filter(r=>r.geral!=null);
 const agg=rows=>{const m=k=>mean(rows.filter(r=>r[k]!=null).map(r=>r[k]));const p=rows.filter(r=>r.parou!=null).map(r=>r.parou?1:0);return{n:rows.length,geral:m("geral"),nativo:m("nativo"),natural:m("natural"),voz:m("voz"),parou_pct:p.length?Math.round(100*p.reduce((x,y)=>x+y,0)/p.length):null};};
 const byRun={},byEmo={},probs={};
 rated.forEach(r=>{(byRun[r.run]=byRun[r.run]||[]).push(r);(byEmo[r.emotion]=byEmo[r.emotion]||[]).push(r);(r.problemas||[]).forEach(p=>probs[p]=(probs[p]||0)+1);});
 let mc=0,mt=0;const mtag={};Object.values(R).forEach(rr=>{const ms=(rr&&rr.markers)||[];if(ms.length){mc++;mt+=ms.length;ms.forEach(m=>{const t=m.tag||"?";mtag[t]=(mtag[t]||0)+1;});}});
 const srt=o=>Object.fromEntries(Object.entries(o).sort((a,b)=>b[1]-a[1]));
 const ao=o=>Object.fromEntries(Object.entries(o).sort().map(([k,v])=>[k,agg(v)]));
 return{total_rated:rated.length,total:BUNDLE.clips.length,por_run:ao(byRun),por_emocao:ao(byEmo),problemas:srt(probs),feedback:{clips_marcados:mc,total_marcadores:mt,por_tag:srt(mtag)}};
}
async function feedbackRecs(){const R=await loadRatings();return BUNDLE.clips.map(c=>{const r=R[c.run+"|"+c.id]||{};return{schema_version:1,run:c.run,id:c.id,audio:c.wav,ref_text:c.text,asr_hyp:c.hyp||"",emotion:c.emotion,accent:c.accent,wer:c.wer,wer_ops:c.wer_ops||[],dur_s:c.dur_s,ratings:{geral:r.geral,nativo:r.nativo,natural:r.natural,voz:r.voz,parou:r.parou,carioca:r.carioca,nota:r.nota},problems:r.problemas||[],markers:r.markers||[],rated_ts:r.ts};});}
const _f=window.fetch.bind(window);
window.fetch=async(u,o)=>{
 if(typeof u!=="string"||!(u.startsWith("/api/")||u.startsWith("/audio")||u.startsWith("/curate/")))return _f(u,o);
 const p=u.split("?")[0];
 if(p==="/api/clips")return jr(BUNDLE.clips);
 if(p==="/api/map")return jr(BUNDLE.trilha);
 if(p==="/api/ratings")return jr(await loadRatings());
 if(p==="/api/insights")return jr(await insights());
 if(p==="/api/feedback")return jr(await feedbackRecs());
 if(p==="/api/curate")return jr(await loadCurate());
 if(p==="/api/rate")return saveRate(JSON.parse(o.body));
 if(p==="/api/curate/save")return saveCurate(JSON.parse(o.body));
 return _f(u,o);
};
})();
</script>
<script>"""
INTERCEPT = (INTERCEPT
  .replace("%SUPA_URL%", json.dumps(SUPA_URL))
  .replace("%SUPA_KEY%", json.dumps(SUPA_KEY))
  .replace("%BUNDLE%", bundle_json))
# injeta antes do PRIMEIRO <script> (o app), só 1x
PAGE = PAGE.replace("<script>", INTERCEPT, 1)

# 5) link "← apps" no header (toque do portal). Header começa com <h1>...
PAGE = PAGE.replace(
  '<header>',
  '<header><a href="/" style="color:var(--tm);text-decoration:none;font-size:11px;letter-spacing:.06em;text-transform:uppercase;margin-right:6px">← apps</a>', 1)

# saída base64
b64 = base64.b64encode(PAGE.encode("utf-8")).decode()
(APP/"dashboard.html.ts").write_text(f'// gerado por /tmp/gen_cockpit.py — cockpit completo (Avaliar/Insights/Trilha/Curar/Gravar)\nexport const HTML_B64 = "{b64}";\n', encoding="utf-8")

# recorder (aba Gravar, rota same-origin)
rec = (REPO/"tools/recording/maya_recorder.html").read_text(encoding="utf-8")
rb64 = base64.b64encode(rec.encode("utf-8")).decode()
(APP/"recorder.html.ts").write_text(f'// gravador (flywheel) — servido em /tts-ptbr/gravar\nexport const REC_B64 = "{rb64}";\n', encoding="utf-8")

# checagens
assert "AUDIO(c.run,c.id)" in PAGE, "rewrite audio falhou"
assert "/tts-ptbr/gravar" in PAGE, "iframe rewrite falhou"
assert "window.supabase.createClient" in PAGE, "interceptor não injetado"
assert PAGE.count("← apps")==1, "back-link"
print(f"OK · PAGE {len(PAGE)//1024}KB · dashboard b64 {len(b64)//1024}KB · recorder b64 {len(rb64)//1024}KB")
