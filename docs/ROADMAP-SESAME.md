# ROADMAP-SESAME — o playbook deles, na nossa escala (02/jul/2026)

> **→ Compilado em [ROADMAP.md](ROADMAP.md) (o roadmap único).** Este doc segue vivo como deep-dive.

> Cada pilar: **o que a Sesame faz** (OSINT verificado: blog técnico, repo, podcast a16z do CTO,
> vagas de jun/2026, reviews do app) → **a nossa versão** (com custo e estado real).
> Irmão de docs/REVISAO-2026-07-02.md (metas M0.5-M3 e orçamento detalhado lá).
> Renderizado na aba Trilha do cockpit (seção "Playbook Sesame").

## A tese em 3 linhas

A Sesame não venceu por arquitetura secreta — o CSM-1B deles é público e a Maya é uma **cascata
orquestrada** (CTO no a16z: ASR→LLM→CSM audio-conditioned, "even the 1B is very good").
O fosso deles é **dado conversacional em escala + eval que prevê felicidade + engenharia de
latência**. Todos os três são replicáveis em escala de nicho — nenhum exige $307M, exigem disciplina.

## Os 10 pilares

### P1 · Modelo base de áudio
- **Eles**: CSM próprio, ~1M h de áudio (maj. inglês) × 5 épocas, tokens Mimi/RVQ. Multilinguismo só "emerge por contaminação" — admitido no blog.
- **Nós**: o próprio CSM-1B deles (Apache via unsloth) + **CPT pt-BR** — base-pt-v1 já provou a alavanca (WER 116→21%); v2 com 1.000h públicas custa **$150-230**. TAGARELA 2.800h no espelho de pesquisa ($430-640) se o v2 justificar.
- **Estado**: ✅ v1 provado · 🔧 chain do v2 consertado hoje (path+shippable+--smoke) · ▶️ rodar semanas 3-4.

### P2 · Personas (a "Maya")
- **Eles**: 4 personas = variantes fine-tunadas do CSM + condicionamento em contexto de áudio. Volume por voz nunca divulgado.
- **Nós**: LoRA r64 por locutor sobre base-pt (receita provada no grid). Evidência pública: **identidade satura ~2-3h** — 3-5h dirigidas por voz bastam pra identidade production-grade; o resto é cobertura.
- **Estado**: ✅ timbre do Pedro clona com 24min (6,5/10) · ⛔ 0,41h vs 5h da meta M1; João/Gui = 0h **sem consentimento assinado** ← o item mais barato e mais bloqueante do projeto inteiro.

### P3 · Dado conversacional multi-turno (o coração da receita)
- **Eles**: o CSM **condiciona em diálogo** (texto+áudio intercalados dos dois falantes) — a naturalidade vem DISSO, não de horas soltas. O dado deles é conversa espontânea em escala.
- **Nós**: flywheel de conversa 2-party estéreo (1 mic/pessoa, cômodos separados), manifest preservando `session_id/ordem/speaker/t_start-t_end` (o export já grava), **treino com contexto de turnos na rodada 3** (harness pronto hoje). 40% da composição de M2 (6h/voz).
- **Estado**: 🔧 gravador consertado hoje (bug whoVal) · ✅ exportador fecha o ciclo · ⛔ 0h estéreo gravadas — **a fase atual É este pilar**.

### P4 · Cascata orquestrada (o produto que parece mágica)
- **Eles**: mic → VAD → ASR → LLM texto (reportado: Gemma 4) → CSM condicionado no áudio da conversa. A mágica é engenharia: **abort 1s→20ms, re-síntese incremental, busca paralela enquanto fala, JSON separando fala de tool-call**.
- **Nós**: Trilha M — `run_maya.sh` (Pocket-TTS+Gemini no Mac) existe e **nunca foi medido ponta-a-ponta**. Passos: (1) medir latência e2e real; (2) barge-in half-duplex; (3) trocar o TTS pelo nosso CSM na M1. Custo: $0 de GPU, semanas de engenharia — é o pilar que transforma "voz boa" em "demo que vende".
- **Estado**: ⛔ nunca medido (score 1,5 é chute) · o eixo mais subestimado do plano.

### P5 · Eval que prevê felicidade (o segredo operacional)
- **Eles**: vaga de 17/jun revela: "own evaluation pipelines… offline and live evals that keep our models honest… metrics that actually predict user happiness". E o blog: **WER saturou** como métrica.
- **Nós**: rate_app (o compasso) + scorecard de prosódia (**baseline objetiva rodada HOJE**: robótico = menos pausa + ritmo achatado) + spk-sim no eval automático (harness de hoje) + painel cego de 5 cariocas (gate M2) + CMOS vs ElevenLabs (gate M3).
- **Estado**: 🔧 instrumentos prontos · ⛔ T2 com n=0 humano; n=1 avaliador estrutural. **Grid futuro ≤ capacidade de escuta (top-4/noite).**

### P6 · Data engine com proveniência
- **Eles**: vaga de 23/jun: curadoria privacy-aware, versioning/lineage, Airflow/Ray. Watermark: forkam silentcipher.
- **Nós**: dataset_registry.yaml + ingest gates (licença/LGPD/DNSMOS/fit) + manifest com licença REAL por fonte (consertado hoje — antes tudo era `shippable:True` hardcoded) + consentimento LGPD como gate de entrada + silentcipher no release público (e corrigir a cláusula do termo ANTES de assinar).
- **Estado**: ✅ pipeline honesto pós-fix · ⛔ consentimentos + revisão jurídica pendentes.

### P7 · RL/DPO em áudio
- **Eles**: CTO no a16z: RL no domínio de áudio é o próximo lever (recompensas de preferência humana em prosódia/naturalidade).
- **Nós**: os ratings + markers do rate_app viram **pares de preferência** → DPO-LoRA ($15-60/rodada, âncora Tango 2: 15k pares = 7 A100-h). Começa quando houver ~20+ avaliações novas por rodada.
- **Estado**: ⛔ 0 pares (depende do P5 girar). Não gastar antes.

### P8 · Produto: app + guardrails + memória
- **Eles**: app iOS (4,9★), personas, busca-enquanto-fala, memória, incognito; reclamação nº1 = guardrails restritivos; Android waitlist; grátis "por enquanto".
- **Nós**: wedge Sesc = **preço fixo anual + cota + fail-closed** (aprovado em mai, parado desde então). Identidade visual do agente: **Voz Lab pronto com 8 direções** (tools/voice_ui). Demo web na M1; app iOS nativo (SwiftUI+Metal, receita no dossiê 91) depois do demo validar.
- **Estado**: ✅ Voz Lab hoje · ⛔ conversa Sesc sem data; preço [TBD] há 6 semanas.

### P9 · Multilíngue — a janela
- **Eles**: English-only no app (verificado 02/jul: languageCodes ['EN'], zero vaga de localização) MAS "20+ idiomas" é meta pública desde fev/2025. FR/ES já saem via LLM com sotaque inglês.
- **Nós**: é a razão do projeto existir. Corolário verificado: **ninguém fechou o nicho em jun/2026** (Chatterbox v3 pt-BR MIT é TTS puro, não conversacional; Gradium é API fechada). Janela aberta, relógio correndo.
- **Estado**: ▶️ baseline Chatterbox no rate_app esta semana — se ganhar do nosso CSM, re-justificar a espinha (MIT permite até trocá-la).

### P10 · Time e cadência
- **Eles**: ~7-8 core ML de elite, $307M, cadência de release semanal no app.
- **Nós**: 1 pessoa + esteira de agentes. A versão honesta da "cadência semanal": **30 min/dia gravando · 20 min/dia ouvindo · grids dimensionados pela escuta · 1 doc de verdade (REVISAO) atualizado por sessão**. Governança pesada morreu em 3 semanas — não recriar rituais que não sobrevivem.

## Sequência (amarra com M0.5→M3 da REVISAO)

```
AGORA (M0.5, 2 sem)    → P2 consentimentos + P3 primeiras sessões estéreo + P5 eval T2 + P9 baseline Chatterbox
M1 (1 mês)             → P1 CPT v2 ($200) + P2 5h Pedro + P4 cascata medida + P5 scorecard a cada treino
M2 (3-4 meses)         → P3 treino com turnos + P7 primeiro DPO + P5 painel de 5 + P8 demo web + Sesc
M3 (6+ meses)          → P1 v3 (TAGARELA se justificar) + P8 app + P6 watermark release + CMOS vs ElevenLabs
```

Custo GPU acumulado até M3: **~$330-480**. O que NÃO é GPU: gravar, ouvir, assinar, ligar — e é
exatamente onde a Sesame está contratando. O playbook deles, na nossa escala, é 80% disciplina.
