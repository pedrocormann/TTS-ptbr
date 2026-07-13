# Fronteira: controle de estilo/EMOÇÃO como ADD-ON de treino sobre o CSM

> Sub-tópico **train-control-emotion** — mapeado ao nosso stack (CSM = LM autoregressivo sobre codec
> Mimi/RVQ 12.5Hz, audio-conditioned; treino 2-estágios; deploy baixa latência; preservar a voz do Pedro).
> Compilado 13/jul/2026. Lente: **avaliar por mérito de arquitetura/add-on, não por idioma**. Gate de
> produto = DADO/PESO de terceiros (Apache/MIT/CC-BY/CC0); **método é livre pra reimplementar**.
> Marcação honesta **[V]=verificado na web hoje / [I]=inferido do conhecimento/dossiê**.

---

## TL;DR — o que muda pra nós

1. **O lever mais barato já está no CSM**: ele é *audio-conditioned*. Dá pra controlar estilo **sem treinar
   nada** condicionando numa TURN/áudio-referência emocional (dual-reference: ref-de-timbre = Pedro, ref-de-emoção
   = qualquer clipe atuado, inclusive de outra língua). É a versão pobre do IndexTTS2. **Faz isso primeiro.** [I]
2. **O lever de treino mais alinhado ao CSM são TAGS INLINE via a MESMA LoRA que já rodamos** (paradigma
   Orpheus; já existe LoRA "Elise" que faz isso *no próprio CSM*). Requer só marcar a **localização** do
   evento no texto (`<laugh>`, `<sigh>`), não taxonomia fina (aprendizado #11 Székely). [V]
3. **Dois papers novos batem exatamente no que o Pedro pediu** e são **LM-based como o CSM** (portam melhor que
   os NAR/flow): **Task-Vector Arithmetic** (botão α por aritmética de pesos, backbone congelado, preserva
   locutor, **CC-BY**, autor BR) e **CSP-FT** (descobre em *quais camadas* mora emoção vs locutor e só mexe nas
   de emoção → preserva o timbre do Pedro). Ambos = **arms baratos**, não produto pronto. [V]
4. **Steering training-free (EmoSteer/CoCoEmo) é lindo mas hoje só existe em DiT/flow-matching** — ninguém
   mostrou em codec-LM autoregressivo. Fica em **WATCH** (se portar, é o Santo Graal: zero treino, S-SIM ~0.65). [V]
5. **Guardrail transversal** (não é add-on, é receita): **misturar 25–30% do dado de pré-treino** durante o
   fine-tune evita esquecimento; single-speaker FT sem mistura degrada **40–50%** fora-de-domínio. Vale pros
   Estágios A e B — é assim que se **preserva a voz do Pedro** enquanto se ensina emoção. [V]

---

## O mapa das famílias (mapeadas ao CSM)

| Família de controle | Como plugaria no CSM | Custo | Preserva a voz do Pedro? |
|---|---|---|---|
| **Reference-audio prompt** (condicionar em áudio de emoção) | Já nativo (audio-conditioned) — dar 2 refs: timbre + emoção | **~$0, zero treino** | Sim (timbre vem da ref do Pedro) |
| **Tags inline** (`<laugh>`, `<sigh>`) | Tokens no texto, treinados na LoRA que já rodamos | Baixo (precisa dado rotulado por localização) | Sim, se LoRA leve + mistura |
| **Aritmética de tarefa / α-knob** (task-vector) | Diff de pesos (emo − neutro) somado ao backbone congelado | Baixo p/ aplicar; **precisa dado emo p/ construir o vetor** | Sim (aditivo, backbone intacto) |
| **Partial FT por característica** (CSP-FT) | Achar camadas de emoção, congelar as de locutor | Médio (probing) | **Sim, por design** (congela locutor) |
| **Adapter/ControlNet residual + α** (DTRF) | ControlNet acústico sobre backbone congelado | Médio-alto (reimplementar p/ AR) | Sim (âncora-neutra/resíduo relativo) |
| **Steering training-free** (EmoSteer/CoCoEmo) | Vetor de ativação em inferência | **$0 se existisse p/ AR** | Sim (S-SIM ~0.65) — **mas só DiT hoje** |
| **Instrução em linguagem natural** (instruct-prompt) | Prefixo de instrução → exige treino de condicionamento | Alto (retreino pesado) | Depende |

---

## Vereditos por item

### 1. Condicionamento nativo do CSM / dual-reference emocional — **TEST (quase ADOPT)**  [I, método]
O CSM já gera condicionado em áudio de contexto. O lever barato (já anotado na nossa MEMORY: *"condicionar em
TURNOS/contexto"*) é dar ao modelo, além da ref de timbre do Pedro, **uma segunda ref só de emoção** (um clipe
atuado — pode ser de outra voz/idioma, porque só queremos o *estilo*, não o timbre). É a intuição do **IndexTTS2**
(duas refs: uma de timbre, uma de emoção) feita de graça em cima do que o CSM já sabe fazer. **Sem retreino.**
- **Fit**: máximo — usa o backbone Apache-2.0 como está; é literalmente um experimento de *prompting*.
- **Risco honesto**: o CSM base é enviesado pro inglês e a força/estabilidade do transfer de estilo por contexto
  em pt-BR é **não medida** (n=0). É o primeiro arm a rodar porque custa ~$0 e informa todo o resto.
- **Licença**: método livre; CSM = Apache-2.0. **Passa.**

### 2. Tags inline treinadas na LoRA (paradigma Orpheus; precedente Elise-no-CSM) — **TEST**  [V]
Orpheus (Canopy, mar/2025) provou o paradigma num **codec-LM Llama-3B**: tags `<laugh>/<sigh>/<gasp>` são
**features treinadas**, não hack de prompt, com ~200ms de latência streaming. Existe uma **LoRA "Elise" que faz
isso no próprio sesame/csm-1b** — ou seja, é reproduzível **na nossa exata arquitetura, com a LoRA que já rodamos
na voz do Pedro**. Marcar só a **localização** do evento basta (aprendizado #11).
- **Fit**: alto — é o add-on de treino mais barato e mais alinhado; entra como um subset de dados na LoRA do Pedro.
- **Licença (atenção)**: o *código+pesos do Orpheus* dizem Apache-2.0, **mas a base é Llama-3.2-3B-Instruct → a
  licença Llama continua valendo sobre os pesos** (atribuição + cláusula >700M MAU + uso aceitável). Llama **NÃO
  está no nosso gate** (Apache/MIT/CC-BY/CC0). ⇒ **não embarcar pesos do Orpheus; reimplementar o método no CSM**
  (Apache). O dataset Elise é HF de terceiros — **licença a verificar antes de usar o dado**. [V que Orpheus=Llama-base]
- **Veredito**: TEST — método livre, plugável já; cuidado com dado/peso de terceiros.

### 3. Task-Vector Arithmetic — botão α por aritmética de pesos (arXiv 2606.05367) — **TEST**  [V]
Constrói um **"vetor de emoção" = pesos-emo − pesos-neutro** e soma ao **backbone congelado**, com **coeficiente α
contínuo** (intensidade fina, não categoria discreta). **Preserva a identidade do locutor** (aditivo, não retreina).
Testado em **Qwen3-TTS (LM-based, como o CSM)**. Repositório público (github.com/danielbrito91/xvector-emotion-arithmetic)
— **autor aparentemente brasileiro** (parceria potencial). **Licença do paper: CC-BY 4.0.**
- **Fit**: alto no *conceito* — é o "botão α" que o DTRF promete, mas numa família **LM-based** que porta melhor
  pro CSM que os NAR/flow. Aditivo ⇒ não ameaça o timbre do Pedro.
- **Risco honesto**: pra **construir** o vetor você precisa de **um fine-tune emocional** (por emoção) de onde
  subtrair o neutro — ou seja, **ainda precisa de dado emocional** (que não temos em pt-BR ≈ 0h). Atalho possível:
  construir os vetores com dado emo de outra língua e testar se o α transfere só o *estilo* (não verificado).
  Casa com a receita FFmpeg de pares relativos do FineCombo (dossiê 84) pra fabricar o dado barato.
- **Veredito**: TEST — arm barato de aplicar, CC-BY, LM-based; gargalo é o dado pra montar os vetores.

### 4. CSP-FT — Partial Fine-Tuning por característica (arXiv 2501.14273) — **TEST**  [V]
Acha, por *probing*, que **emoção e locutor moram em camadas diferentes** do TTS-LLM, e faz **fine-tune só das
camadas da característica-alvo**. Isso é **disentangle por localização de camada** — e é exatamente o mecanismo pra
**preservar a voz do Pedro**: congela as camadas de locutor, mexe só nas de emoção (ou vice-versa). Reporta
adaptação com **1–5 min de áudio**, com qualidade ≥ full-FT e muito menos parâmetros treináveis. Backbone da linha
CosyVoice (LM-based).
- **Fit**: alto — responde direto ao "onde a emoção mora?" que o Pedro citou (CSP-FT). É a versão *treinada* do
  disentangle, complementar ao steering (versão *não-treinada*).
- **Risco honesto**: o mapa de camadas do CosyVoice **não transfere direto** — teríamos que **refazer o probing no
  CSM** (experimento real, mas barato e publicável junto com a linha USP/Aluísio). Menos "esquecimento" que full-FT,
  o que ecoa o alerta do FlowEdit (dossiê 84).
- **Licença**: paper CC-BY (método livre); sem pesos pt-BR embarcáveis. **Passa como método.**
- **Veredito**: TEST — o experimento "em que camada do CSM mora a emoção carioca?" é de alto valor.

### 5. DTRF — Dual-Track Residual + adapter + α + âncora-neutra (applsci-16-06613, dossiê 84) — **WATCH**  [I/V]
O "padrão-premium" de add-on: **ControlNet acústico + adapter de duração sobre backbone congelado**, botão **α de
intensidade**, e **resíduo relativo (E_alvo − E_neutro)** pra preservar timbre. Confirma com número que emoção mexe
em **duração/ritmo** (angry −15%), reforçando corte por IU.
- **Fit**: as **ideias** portam e são load-bearing (α, âncora-neutra, eval SER-independente pra evitar
  circularidade). Os **módulos NÃO portam**: backbone é **Matcha (NAR, com duration predictor)**; o CSM é AR/RVQ
  sem predictor explícito de duração. Reimplementar um ControlNet residual sobre o CSM é obra maior.
- **Licença**: paper CC-BY; sem pesos.
- **Veredito**: WATCH — adotar os *conceitos* (já refletidos nos itens 3–4 e na nossa eval), não os módulos.

### 6. Steering training-free / activation steering (EmoSteer 2508.03543; CoCoEmo 2602.03420) — **WATCH**  [V]
**Zero treino**: acha os poucos tokens/ativações que carregam emoção e injeta um **vetor de steering em inferência**
(conversão, interpolação com α, **erasure** com β, blending composável). Preserva locutor (**S-SIM ~0.64–0.65**).
- **Fit — o freio**: hoje **só existe em flow-matching/DiT (F5-TTS, CosyVoice2, E2-TTS)**. **Nenhuma demonstração em
  codec-LM autoregressivo** como o CSM. O paper **não discute** aplicabilidade a AR. Conceito porta (LMs têm o mesmo
  fenômeno de "poucas dimensões carregam o estilo"), mas seria **P&D nosso**, não plug.
- **Licença**: código em apêndice/demo; **sem licença explícita declarada** — citar, não copiar.
- **Veredito**: WATCH — se alguém portar activation-steering pra AR-TTS (ou se fizermos o probing), vira o lever mais
  barato que existe (zero treino, preserva Pedro). Vigiar de perto; candidato a experimento próprio depois do CSP-FT.

### 7. Instrução em linguagem natural / instruct-prompt (Qwen3-TTS instruct; InstructTTS/EmoVoice) — **WATCH**  [V]
Controle de emoção/prosódia/timbre por **descrição em linguagem natural** (o `instruct` do Qwen3-TTS, 15–40 palavras).
**Qwen3-TTS é Apache-2.0**, pesos no HF (jan/2026) — **passa o gate** e tem clone + voice-design.
- **Fit como ADD-ON ao CSM**: **fraco** — pra dar "instruct" ao CSM seria preciso **treinar um condicionamento de
  instrução** (dado instrução↔fala em escala), retreino pesado; não é plug. Benchmark de instrução: **InstructTTSEval**
  (arXiv 2506.16381).
- **Fit como BASELINE/ATALHO**: **forte** — Qwen3-TTS (Apache, 12.5Hz como o Mimi, streaming, clone) é o candidato
  óbvio a **baseline cega no rate_app** e possível atalho de produto se o carioca clonar bem. Alinha com a nota da
  MEMORY (Qwen3/Chatterbox como baseline/atalho).
- **Veredito**: WATCH — como add-on ao CSM é caro; como **baseline pt-capaz e Apache** merece um arm de benchmark.

---

## Guardrail transversal (preservar a voz do Pedro enquanto se ensina emoção)  [V]
Não é um add-on de emoção, mas decide se qualquer um dos itens acima estraga o timbre:
- **Mixed training** (arXiv 2603.10904): manter **25–30% do dado de pré-treino** na mistura de FT evita esquecimento
  catastrófico; **single-speaker FT sem mistura degrada 40–50% fora-de-domínio**; precisa de **~10–15 locutores** pra
  generalização razoável. ⇒ **Estágio A** com 25–30% do dado multilíngue original; **Estágio B (LoRA emoção/voz)**
  com regularização + mistura. Ranquear checkpoints **não** por MOS automático (cego a prosódia, dossiê 84).
- **FlowEdit** (dossiê 84): full-FT causa drift (PER 4,1→15,3) e **LoRA às vezes piora o geral** → rodar o *canary*
  anti-drift a cada checkpoint. Reforça manter a LoRA **leve** e a mistura **alta**.

---

## Sequência recomendada (arms, do mais barato ao mais caro)
1. **[$0] Dual-reference / condicionamento em contexto** (item 1) — mede se o CSM transfere estilo por áudio-ref em pt-BR.
2. **[$] Tags inline na LoRA do Pedro** (item 2) — subset `<laugh>/<sigh>` marcado por localização; reusa pipeline atual.
3. **[$$] Probing "onde mora a emoção no CSM" (CSP-FT)** (item 4) — congela camadas de locutor, publicável com USP.
4. **[$$] Botão α por task-vector** (item 3) — se conseguirmos montar vetores (dado emo sintético FineCombo / outra língua).
5. **[watch] Steering training-free em AR** (item 6) e **DTRF-ControlNet** (item 5) — só se 1–4 travarem.
6. **[bench] Qwen3-TTS instruct** (item 7) — arm de baseline cega, não add-on.

Todos batem no mesmo gargalo real: **dado emocional pt-BR ≈ 0h**. O que destrava emoção não é arquitetura — é
**gravar ≥30min/estilo dirigido** (já no plano M2). Os itens 1–4 são o que faz esse pouco dado render sem estragar
o timbre do Pedro.

---

## Fontes (verificadas 13/jul/2026)
- Task-Vector Arithmetic for Emotional Expressivity Control in LM-based TTS — arXiv 2606.05367 (CC-BY; github.com/danielbrito91/xvector-emotion-arithmetic; Qwen3-TTS). [V]
- Efficient Emotion and Speaker Adaptation in LLM-Based TTS via Characteristic-Specific Partial Fine-Tuning (CSP-FT) — arXiv 2501.14273. [V]
- EmoSteer-TTS: Training-Free Emotion-Controllable TTS via Activation Steering — arXiv 2508.03543 (F5/CosyVoice2/E2, DiT/flow-only, S-SIM 0.64–0.65). [V]
- CoCoEmo: Composable and Controllable Emotional TTS via Activation Steering — arXiv 2602.03420. [V, título]
- TED-TTS: Training-Free Intra-Utterance Emotion and Duration Control — arXiv 2601.03170. [V, título]
- When Fine-Tuning Fails and when it Generalises (mixed training) — arXiv 2603.10904. [V]
- Orpheus-TTS (Canopy Labs; Llama-3.2-3B base; código+pesos Apache-2.0 mas licença Llama incide sobre pesos) — canopylabs/orpheus-3b-0.1-ft; sesame-csm Elise-LoRA (HF keanteng/sesame-csm-elise-lora). [V]
- Qwen3-TTS (Alibaba, Apache-2.0, jan/2026, instruct/VoiceDesign/clone) — HF Qwen/Qwen3-TTS-12Hz-1.7B; simonwillison.net/2026/Jan/22. [V]
- InstructTTSEval — arXiv 2506.16381. [V, título]
- IndexTTS2 (dual-reference: timbre + emoção) — arXiv 2506.21619; ReStyle-TTS (controle relativo/contínuo + TCO timbre) — arXiv 2601.03632; FC-TTS — arXiv 2605.24618. [V, títulos]
- DTRF (applsci-16-06613, CC-BY) + FlowEdit (2606.20518) + FineCombo (2606.19209) — dossiê 84 (research/dossier-2026-07/84-triagem-papers-jul13.md). [I, projeto]
