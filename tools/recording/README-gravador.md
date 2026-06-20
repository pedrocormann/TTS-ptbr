# Gravador de voz — flywheel TTS pt-BR

Ambiente pra gravar conversas (Pedro / João / Guilherme), **1 faixa limpa por pessoa**, em alta,
local-first + upload pro acervo. Decisão: **faixas SEPARADAS** (não juntar) — voz limpa por
falante, sem diarização, cada um corrige a sua.

## Componentes
- **`maya_recorder.html`** — app de 1 clique (navegador). Mic CRU (sem AGC/supressão), **24 kHz
  mono WAV** (taxa nativa do CSM, cabe no free tier), grava em pedaços na IndexedDB (à prova de
  crash/reload), **salva local sempre** + sobe pro Supabase via signed URL. Identidade Unflat.
- **Supabase** (projeto `unrefs`, sa-east-1):
  - bucket **privado** `reunioes-voz` (criado pela Storage API — bucket criado via SQL NÃO
    registra no serviço de storage e dá 403 no upload; tem que ser pela API).
  - edge function **`voz-upload-url`** (verify_jwt=false): recebe `{meeting, who, ts}`, gera
    `createSignedUploadUrl` com service-role → o navegador faz PUT direto pro bucket privado.
    Sem anon-insert/RLS; arquivo grande não passa pela function. **Testado: HTTP 200.**

### Fonte da edge function `voz-upload-url/index.ts`
```ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors = { "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS" };
const J=(o,s=200)=>new Response(JSON.stringify(o),{status:s,headers:{...cors,"Content-Type":"application/json"}});
Deno.serve(async (req)=>{
  if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
  try{
    const b=await req.json();
    const m=String(b.meeting||"sem-codigo").replace(/[^a-zA-Z0-9_-]/g,"_").slice(0,60);
    const w=String(b.who||"x").replace(/[^a-zA-Z0-9_-]/g,"_").slice(0,30);
    const ts=String(b.ts||new Date().toISOString()).replace(/[:.]/g,"-").slice(0,40);
    const path=`${m}/${w}__${ts}.wav`;
    const sb=createClient(Deno.env.get("SUPABASE_URL"),Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"));
    const {data,error}=await sb.storage.from("reunioes-voz").createSignedUploadUrl(path);
    if(error) return J({error:error.message},400);
    return J({signedUrl:data.signedUrl,token:data.token,path});
  }catch(e){ return J({error:String(e)},400); }
});
```

## Como rodar / hospedar
- **Local (teste rápido, Mac):** `cd tools/recording && python3 -m http.server 8899` → abrir
  `http://localhost:8899/maya_recorder.html` (getUserMedia funciona em localhost).
- **Distribuído (os 3, em casa):** precisa de HTTPS → hospedar o `maya_recorder.html` (bucket
  público / Vercel / Pages) e mandar o link. **[TODO segunda]**

## Fluxo da reunião
1. Os 3 em call normal + **fone de ouvido** (essencial: sem fone, o mic capta os outros e suja a faixa).
2. Cada um abre o link, digita o **mesmo código de reunião** + seu nome, clica Gravar (juntos).
3. Falam. No fim: Parar → WAV salvo local + sobe pro bucket em `reuniao/nome__timestamp.wav`.
4. Pós: Whisper por faixa → cada um corrige a sua na aba **Curar** do rate_app.

## Puxar as faixas (service role)
`reunioes-voz` é privado; baixar via MCP/service-role ou signed download URL. NÃO deixar público.
