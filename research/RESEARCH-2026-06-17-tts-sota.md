# Pesquisa SOTA via Firecrawl Research — 17/jun/2026

**Como foi feito:** testamos o *Firecrawl Research* (índice de papers + GitHub, GET síncrono, **não exige API key** no acesso básico — `/v2/search/research/papers`, `/papers/{id}` pra ler passagens, `/github`). Rodamos buscas nas perguntas abertas do plano e lemos passagens dos papers-chave. Reusável a qualquer momento sem credencial.

## Achados que mexem no plano

### 1. Sotaque nativo (nó `a-accent`) — o fork imediato que o avaliador alimenta
O campo chama isso de **Accent Conversion (AC)** + **Mispronunciation Detection & Diagnosis (MDD)**. Três alavancas concretas:
- **Condicionar em fonemas (G2P), não em texto cru.** O paper de AC (`arXiv:2410.14997`) e o de transfer-learning low-resource (`arXiv:2306.00535`) mostram que **entrar com rótulos de fonema** no encoder melhora alinhamento e pronúncia. O CSM hoje recebe **texto** → um **front-end G2P pt-BR** (fonemizar antes) é um lever direto contra o "fala como gringo". **Δ plano:** testar G2P pt-BR no Estágio B v2 como braço.
- **Ground-truth sintético de um TTS nativo** (`arXiv:2410.14997`): gerar a versão *nativa* da mesma frase com um TTS pt-BR bom e usar como alvo de destilação/correção. **Δ plano:** fonte de dado de correção sem precisar regravar.
- **MDD "L1-aware"** (`arXiv:2309.07719`, QCRI): modela exatamente a discrepância L1↔L2 (= o "sotaque de gringo"), via sequência de fonema canônica vs. verbatim + GOP. **Este é o nome acadêmico do nosso problema.**
- Adaptação de sotaque **parameter-efficient/LoRA** existe e funciona (`arXiv:2305.11320`) — casa com nossa receita.

### 2. Feedback → agente (FEEDBACK.md v2 / `enrich_markers.py`)
O "alinhamento offline pra localizar o fonema em t=2.3s" que deixamos como v2 **tem nome e técnica**: **GOP (Goodness of Pronunciation) + MDD**. Versões recentes: GOP *segmentation-free* (`arXiv:2507.16838`), GOP com conhecimento fonológico (`arXiv:2506.02080`), MDD *prompt-free* (`arXiv:2604.22133`). **Δ plano:** o `enrich_markers.py` deve ser um pipeline **GOP/MDD com inventário de fonema pt-BR** — cruza o `wer_ops` (palavra) com o fonema errado no tempo, fechando o loop dos marcadores humanos.

### 3. Emoção (nó `a-emo`) — CUIDADO, nuance que evita ilusão
Tentação: controlar emoção **sem** dataset multi-emoção via aritmética de vetores/activation steering. **Mas** o paper mais relevante (`arXiv:2606.05367`, **da UNESP/Brasil**, jun/2026) faz a engenharia reversa disso em TTS **baseado em LM (= a classe do CSM)** e conclui no estudo de eliminação: *"No operand preceding the x-vector admits emotional control via linear arithmetic"* — ou seja, **a aritmética ingênua de vetores NÃO controla emoção** nessas arquiteturas (a prosódia "emerge da continuação autoregressiva condicionada", não de um embedding separável). Alternativas (CoCoEmo activation steering `arXiv:2602.03420`; DPO/preferência `arXiv:2509.25416`; controle por palavra `arXiv:2509.24629`) existem mas não são plug-and-play. **Δ plano:** **manter** o dataset multi-emoção (G2) como caminho principal — não dá pra pular. Acompanhar o grupo da UNESP (possível parceria/baseline pt-BR). Hipótese de "emoção sem regravar" → rebaixada de aposta a *experimento de risco*.

### 4. Full-duplex (nó `b-moshi`) — o campo passou do Moshi
SOTA 2026 mudou: **SoulX-Duplug** (`arXiv:2603.14877`, módulo de predição de estado **plug-and-play** sobre TTS streaming — encaixa na nossa cascata Maya sem treinar spine do zero), **BayLing-Duplex** (`arXiv:2606.14528`, full-duplex com **um único LLM AR**), **PersonaPlex** (`arXiv:2602.06053`, controle de voz/role em duplex), **OmniFlatten** (`arXiv:2410.17799`). **Δ plano:** antes de comprometer com Moshi+Mimi (Trilha B), avaliar SoulX-Duplug como atalho duplex sobre a Trilha M (cascata) — pode dar "duplex" sem o custo de dados estéreo.

## GitHub (implementação)
`thomasgauthier/csm-hf` (port HF — usamos HF puro), `knottwill/sesame-finetune`, `davidbrowne17/csm-streaming`, `SesameAILabs/csm` (issues #30/#116/#145 = dores reais de finetune). Vale minerar issues antes do Estágio B v2.

## Citações (arXiv)
Sotaque/AC: 2410.14997 · 2506.16580 · 2305.11320 · 2301.04606 · 2005.09271 · 1911.11601
MDD/GOP: 2309.07719 · 2507.16838 · 2506.02080 · 2604.22133 · 2008.08647
Emoção: 2606.05367 (UNESP) · 2602.03420 · 2509.24629 · 2509.25416 · 2603.11683
Full-duplex: 2603.14877 · 2606.14528 · 2602.06053 · 2410.17799
G2P pt/low-resource: 2306.00535 · 2204.03067 · 1708.01464 · 2402.05794
