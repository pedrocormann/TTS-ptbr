# TTS-ptbr — One-Pager (Dia 1, 2026-05-17)

> Voz conversacional **pt-BR**, full-duplex, emocional, qualidade Maya-class.
> Código aberto / **pesos fechados**. Repo privado: github.com/pedrocormann/TTS-ptbr

---

### 🎯 O QUE É
Motor de **conversa em áudio pt-BR** (não TTS clássico): emoção, full-duplex
(turn-taking, barge-in), clonagem de voz, latência-alvo **<800ms p50**.

### 🧠 A APOSTA (arquitetura)
**Áudio é a espinha; texto é paralelo/bastidor, não o core.**
- **Aposta = Moshi** (full-duplex real, CC-BY-4.0, LoRA oficial, Inner-Monologue)
- **Co-aposta = Qwen3-Omni** (Apache-2.0, fala pt nativo)
- **CSM** = componente de voz · **Cascata** = só piso de latência
- Decidido por dado na **Fase 0** (não no papel)

### 💰 O NEGÓCIO (wedge)
Voz-assinatura **experiencial** — arquétipo **Mariclea/Sesc**: cliente cultural
recorrente (R$350k em 3 anos, PO adiada **travada no custo da ElevenLabs**).
- Pacote: **preço fixo anual + cota + fail-closed** (o cliente pediu isso)
- **Moat:** modelo 1B próprio → serving **~R$0,02-0,12/min (~10-40× < ElevenLabs)**
- Motion **A→B**: linha embutida em contrato Unflat agora → produto depois

### 🥊 POR QUE GANHA
ElevenLabs ($11B, entrando no BR) é **puro custo variável** — não segue
preço-fixo sem canibalizar US$330M ARR. Serving barato é **estrutural** (modelo
pequeno e nosso); SDumont grátis cobre o treino. Posição comercial não-contestada.

### ⚠️ RISCOS (4)
1. Latência do CSM não-publicada → mitiga na Fase 0
2. pt-BR do zero (base inglesa)
3. **Dado expressivo pt-BR rotulado ≈ 0 aberto** (o gargalo **e** o moat)
4. Licença/LGPD-ANPD (voz = dado sensível)

### 📊 DADO (gargalo nº1 + solução)
Aberto = só fala lida. Spontaneous/emocional pt-BR = NC-vetado. Emoção×sotaque
= **0h aberto → in-house ~12-16h** (o moat). Pistas comerciais achadas:
**Câmara CC-BY-4.0** + judicial (Art. 8º) + **sintético Kokoro/Chatterbox**.
Receita J-Moshi: ~602h sintético : 344h real. **CPT provavelmente dispensável**
(LoRA-first; finetune <US$60).

### ✅ STATUS DIA 1 (~6h líquidas)
Constituição SDD v0.2 · dossiê de pesquisa (00→70) · spikes Fase-0 escritos
contra API real + testados (CPU) · pipeline sintético full-duplex testado · eval
harness · **18 commits**. **Caminho crítico DESTRAVADO** (token criado;
Moshi/Mimi/Kokoro ungated). Output ≈ **2-4 semanas-pessoa** em ~6h.

### ▶️ PRÓXIMO PASSO
Token + Colab → `phase0/RUNBOOK.md` (copy-paste): dado sintético → Spike C Moshi
(teto de latência) → **teste decisivo #1: Mimi pt-BR freeze** → LoRA proof.
**Gate:** avaliação humana pt-BR. **Revisão dura: 2026-06-17.**

### ⏳ PENDÊNCIAS (Pedro — `research/PARKING-LOT.md`)
Llama/Meta (em revisão, secundário) · Colab Pro+ / W&B / Inception · advogado
LGPD · **FINEP R$300M, prazo 2026-09-30** (alvo de fomento) · alocação SDumont.

---
*Layout Miro sugerido: 3 colunas — [O QUE É · APOSTA · DADO] | [NEGÓCIO · POR QUE
GANHA · RISCOS] | [STATUS · PRÓXIMO PASSO · PENDÊNCIAS]. Fonte: `specs/` +
`research/dossier/00-SYNTHESIS.md`.*
