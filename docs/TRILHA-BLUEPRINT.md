# TRILHA — blueprint da arquitetura & UI (pra portar pra outros projetos)

> Extraído do cockpit do TTS-ptbr (`tools/rate/rate_app.py`, aba TRILHA + `tools/rate/trilha_map.json`).
> É um **mapa vivo de projeto**: um único JSON descreve estado, plano e execução; a UI renderiza
> tudo client-side (zero dependências, um arquivo HTML/JS servido por qualquer server).
> Este doc contém o modelo de dados, o contrato de renderização e os snippets pra replicar.

## 1 · O conceito

Uma página com **3 zonas** narrativas (a ordem é a mensagem):

| Zona | Pergunta que responde | Cards |
|---|---|---|
| `agora` | "onde estamos HOJE, sem maquiagem" | tweet-resumo + % geral · sumário · scorecard vs referência |
| `o plano` | "qual é a ciência e o caminho" | aprendizados verificados · playbook · pessoas · frentes · **o MAPA** |
| `registro` | "o que foi tentado e custou quanto" | kanban de hipóteses · próximos · blockers · plano de custo · rodadas |

O coração é o **MAPA**: nodes de desenvolvimento organizados em `lanes` (linhas temáticas) ×
`col` (colunas ≈ tempo/fase), com **dependências desenhadas como curvas SVG** entre os cards.
Clicar num node abre um **painel lateral** com aprofundamento, hipóteses ligadas, "depende de" e
"habilita" (navegáveis). Tudo vem de um único `trilha_map.json` — atualizar o projeto = editar JSON.

## 2 · Modelo de dados (`trilha_map.json`)

Chaves que o MAPA exige (o resto é opcional, cada card lê a sua):

```jsonc
{
  "state": {                       // zona AGORA
    "tweet": "resumo de 1 frase (o 'tweet' do projeto)",
    "now":   "status completo (colapsável)",
    "next":  ["próxima ação 1", "..."],
    "blockers": ["Nome do blocker: detalhe", "..."]
  },

  "lanes": [                       // linhas temáticas do mapa
    { "key": "foundation", "label": "Fundação · Datasets", "progress": 49 }
  ],

  "nodes": [                       // os cards do mapa
    {
      "id": "ds-cml",              // único; usado nas deps e no DOM (nd-<id>)
      "lane": "foundation",        // -> lanes[].key
      "col": 0,                    // coluna no grid (0-based; ≈ ordem/fase)
      "deps": ["outro-id"],        // arestas: deps -> este node
      "title": "CML-TTS",
      "status": "done",            // done | wip | next | idea
      "progress": 85,              // 0-100 (barra do card)
      "summary": "1-2 frases mostradas no painel",
      "deep": "markdown-lite (**b**, `code`, - listas) pro aprofundamento",
      "hyp": [                     // opcional: hipóteses ligadas ao node
        { "claim": "...", "status": "validada|refutada|aberta" }
      ]
    }
  ],

  // ---- opcionais (cada um vira um card independente; remova o que não usar) ----
  "hypotheses": [ { "node": "id", "status": "validada", "claim": "...", "evidence": "..." } ],
  "maya_gap":  { "media": 2.8, "veredito": "...", "eixos": [ { "nome": "...", "nota": 6.5 } ] },
  "aprendizados": { "titulo": "...", "itens": [ { "claim": "...", "acao": "...", "fontes": [{"n":"nome","u":"url"}] } ] },
  "research_lines": [ { "id": "F1", "nome": "...", "objetivo": "..." } ],
  "gpu_plan": [ { "fase": 0, "etapa": "...", "gpu": "...", "cost": "$0", "quando": "...", "status": "ativo" } ],
  "blocks":  [ { "id": "treino-1", "label": "Treino 1", "date": "...", "status": "fechado", "metrics": {} } ],
  "sesame_playbook": { "tese": "...", "pilares": [], "sequencia": "..." },
  "pesquisadores_br": { "tese": "...", "cards": [] }
}
```

Regras que fazem o mapa funcionar bem:
- `col` é **global** (o grid usa `max(col)+1` colunas em todas as lanes) — alinha fases entre lanes.
- `deps` pode cruzar lanes; a curva liga a borda direita do dep à esquerda do dependente.
- % da lane é mantido à mão (não é média dos nodes) — permite ponderar o que importa.
- O % geral do projeto = média dos `lanes[].progress`.

## 3 · Contrato de renderização

### Grid do mapa
```js
const COLS = Math.max(0, ...m.nodes.map(n => n.col)) + 1;
// por lane:
`<div class=lane-row style="grid-template-columns:repeat(${COLS},minmax(140px,1fr))">
   ${nodesDaLane.map(n => `<div class=cell style="grid-column:${n.col+1}">${nodeCard(n)}</div>`)}
 </div>`
// wrapper: <div id=mapwrap (overflow-x:auto)> <div id=map> <svg class=edges id=edges></svg> + lanes
```

### Card do node
```js
const STATUS = { done:'feito', wip:'em curso', next:'a seguir', idea:'hipótese' };
function nodeCard(n){
 return `<div class="node ${n.status}" id="nd-${n.id}" onclick="openNode('${n.id}')">
   <div class=node-t>${esc(n.title)}</div>
   <div class=node-bar><i style="width:${n.progress||0}%"></i></div>
   <div class=node-meta><span>${n.progress||0}%</span><span class=dot></span>${STATUS[n.status]||''}</div>
 </div>`;
}
```

### Arestas (o truque todo)
Desenhadas **depois** do layout, medindo o DOM real — funciona com qualquer altura de card:
```js
function drawEdges(){
 const svg=document.getElementById('edges'), map=document.getElementById('map');
 const mr=map.getBoundingClientRect();
 svg.setAttribute('width',map.scrollWidth); svg.setAttribute('height',map.scrollHeight);
 let p='';
 for(const n of MAP.nodes){
  const to=document.getElementById('nd-'+n.id); if(!to)continue;
  const tr=to.getBoundingClientRect();
  for(const d of (n.deps||[])){
   const f=document.getElementById('nd-'+d); if(!f)continue;
   const fr=f.getBoundingClientRect();
   const x1=fr.right-mr.left, y1=fr.top+fr.height/2-mr.top,
         x2=tr.left-mr.left,  y2=tr.top+tr.height/2-mr.top;
   const dx=Math.max(22,Math.abs(x2-x1)*0.4);           // "puxada" da bezier
   p+=`<path class=edge d="M ${x1} ${y1} C ${x1+dx} ${y1}, ${x2-dx} ${y2}, ${x2} ${y2}"/>`;
  }
 }
 svg.innerHTML=p;
}
// chamar com requestAnimationFrame(drawEdges) após injetar o HTML,
// e em window.resize enquanto a aba estiver visível.
```

### Painel de aprofundamento
`openNode(id)` monta: tags (lane + status) → título → barra de progresso → `summary` →
`deep` (markdown-lite) → hipóteses (`hyp[]` como chips coloridos por status) →
**Depende de** (deps resolvidos) e **Habilita** (busca reversa: quem tem `id` nas suas deps) —
ambos clicáveis, navegando de node em node. Fecha com ✕, scrim ou `Escape`.

```js
const dependents = MAP.nodes.filter(x => (x.deps||[]).indexOf(id) >= 0);  // "Habilita"
```

O `deep` usa um markdown-lite de 10 linhas (negrito, `code`, listas com `-`):
```js
function md(s){
 s=esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`(.+?)`/g,'<code>$1</code>');
 const lines=s.split('\n'); let out='',inl=false;
 for(let ln of lines){
  if(/^\s*[-•]\s+/.test(ln)){ if(!inl){out+='<ul>';inl=true;} out+='<li>'+ln.replace(/^\s*[-•]\s+/,'')+'</li>'; }
  else { if(inl){out+='</ul>';inl=false;} if(ln.trim())out+='<p>'+ln+'</p>'; }
 }
 if(inl)out+='</ul>'; return out;
}
```

## 4 · CSS essencial (identidade Unflat/cockpit)

```css
:root{ --acc:#E45933; --acc-soft:rgba(228,89,51,.10) }   /* troque o acento por projeto */
/* status → cor da borda esquerda, barra e dot */
.node{background:var(--surface);border:1px solid var(--b);border-left:2px solid var(--bh);
      border-radius:10px;padding:11px 12px;cursor:pointer;transition:all .15s var(--ease)}
.node.done{border-left-color:var(--green)}
.node.wip {border-left-color:var(--orange)}
.node.next{border-left-color:var(--blue)}
.node.idea{border-left-color:var(--tf)}
.edge{fill:none;stroke:rgba(245,245,247,.13);stroke-width:1.5}

.lane{position:relative;padding:16px 0;border-top:1px solid var(--b)}
.lane-title{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;min-width:210px}
.lane-bar{height:3px;background:rgba(255,255,255,.06);border-radius:999px;width:90px;overflow:hidden}
.lane-row{display:grid;gap:14px;align-items:start;position:relative;z-index:1}

/* zonas narrativas */
.zone-h{display:flex;align-items:center;gap:13px;margin:38px 2px 16px;padding-top:28px;
        border-top:1px solid rgba(255,255,255,.06)}
.zone-k{width:10px;height:10px;border-radius:3px;background:var(--zacc);
        box-shadow:0 0 12px color-mix(in srgb,var(--zacc) 45%,transparent)}
.zone-t{font-family:var(--serif);font-size:23px;font-style:italic}
```

Paleta completa do cockpit em `reference-unflat-design-tokens` / `tools/rate/rate_app.py`
(ink escuro, Instrument Serif pra títulos de zona, Geist/Geist Mono, cards de pele única).

## 5 · Como portar (checklist)

1. **Dados**: crie o `map.json` do novo projeto — comece só com `state`, `lanes`, `nodes`
   (o mínimo que o mapa exige). Adicione os cards opcionais depois, um por um.
2. **Server**: qualquer coisa que sirva o HTML + o JSON (no cockpit é um `http.server` Python
   com rota `/api/map`; um arquivo estático com `fetch('map.json')` também serve).
3. **JS**: copie de `tools/rate/rate_app.py` as funções `renderTrail` (corte os cards que não
   usar), `nodeCard`, `drawEdges`, `openNode`, `closePanel`, `md`, `esc` e o dict `STATUS`.
4. **CSS**: copie os blocos `.zone*`, `.lane*`, `.node*`, `.edge`, `#map/#mapwrap`, `.panel*`
   e os tokens `:root`. Troque `--acc` pela cor do projeto.
5. **Resize**: religue `window.addEventListener('resize', drawEdges)` (só com a aba visível).
6. **Regra de ouro**: a UI nunca guarda estado do projeto — **o JSON é a fonte de verdade**;
   atualizar a trilha = editar o JSON (na mão ou por agente).

## 6 · Padrões que valem manter

- **Tweet no topo**: forçar o resumo do projeto em 1 frase honesta muda o tom da página inteira.
- **% por lane mantido à mão** — média automática de nodes mente (nem todo node pesa igual).
- **Hipóteses com status** (`validada/refutada/aberta`) ligadas aos nodes: o mapa vira registro
  científico, não só kanban — o que foi **refutado** fica visível (anti re-litigação).
- **Zona "registro" com custos** (`gpu_plan`/`blocks`): plano e gasto na mesma página evita
  roadmap descolado da realidade.
- **Cards colapsáveis + painel lateral**: densidade alta sem scroll infinito; o aprofundamento
  mora no clique, não na página.
