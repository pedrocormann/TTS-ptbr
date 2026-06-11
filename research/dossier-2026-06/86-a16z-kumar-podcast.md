# 86 — Podcast a16z × Ankit Kumar (Trilha M: "ouvindo" o CTO da Sesame)

**Episódio:** "Building the Next Generation of Conversational AI" — AI + a16z
**Guest:** Ankit Kumar (co-founder/CTO, Sesame AI) · **Host:** Anjney Midha (GP a16z, board da Sesame)
**Publicado:** 14/mar/2025 · **Duração:** 1h41 · **YouTube:** `bTcpNQH8ViQ`
**Data da coleta:** 2026-06-10 · **Método:** transcrição integral obtida via
`yt-dlp --write-auto-subs` (legendas auto-geradas do YouTube, `en-orig`, ~2.900 cues,
900 KB de VTT → texto limpo). a16c.com **não** publica transcript do episódio
(verificado); a página oficial só tem show-notes.
**Confiança:** [P] = quote verbatim da transcrição (ressalva: ASR automático do
YouTube — pequenos erros de palavra possíveis, sem diarização; atribuição
Kumar/Midha inferida pelo contexto). Timestamps em `[hh:mm:ss]`.

> **Aviso de escopo:** o episódio NÃO menciona "1M horas de áudio" nem detalhes de
> tokenizer/RVQ/Mimi — isso está no blog post "Crossing the Uncanny Valley of Voice"
> (ver dossiê 10). O termo "voice presence" também não é dito no podcast (é
> vocabulário do blog). Tudo abaixo é o que Kumar disse *no episódio*, sem mistura.

---

## 0. TL;DR técnico (o que o episódio confirma de novo)

1. **A demo Maya é uma CASCATA**: ASR incremental → LLM (conteúdo) → CSM (speech
   generation). Kumar admite explicitamente. O CSM é *audio-conditioned* (vê todo o
   áudio da conversa), mas o LLM só vê texto — paralinguística do usuário é perdida.
2. **Turn-taking/interrupção HOJE = heurísticas + modelos auxiliares**, fora do CSM.
   "These models today do not model the structure of the conversation at all."
3. **Roadmap declarado (mar/2025):** (a) curto prazo: um único transformer multimodal
   — primeiro *audio understanding* (mais fácil), depois *audio generation*; (b) longo
   prazo: **full-duplex** com decisões a cada frame (~100 ms), citando **Moshi** e
   trabalhos da Meta nominalmente.
4. **AR vs diffusion:** backbone tem que ser **causal** (AR transformer); diffusion não
   é nativamente causal, mas o **head de geração de áudio pode virar diffusion** no
   futuro — eles estavam trabalhando nisso.
5. **Latência:** alvo **sub-500 ms** de response time; "é tudo systems engineering" —
   ASR incremental, pipelining, pré-computação, caching, otimização de cada estágio.
6. **Escala:** 1B/3B/8B treinados; "even the 1B is very good"; escala compra
   long-tail contextual (homógrafos, consistência de pronúncia), não naturalidade base.
7. **Evals:** WER saturou; usam pronúncia como probe quantificável + preferência
   humana (win-rate do modelo vs continuação humana real de uma conversa).
8. **LLM:** não pré-treinam; usam open-source LLMs e "adicionam modalidades".
   Trade-off assumido: Maya raciocina pior que assistentes frontier, de propósito.
9. **Time:** software inteiro < 15 pessoas; core ML ~7–8.
10. **Open source:** só o **base model do CSM** (sem vozes Maya/Miles embutidas;
    cloning é in-context learning, zero/few-shot). A demo (LLM, ASR, orquestração,
    otimizações de latência) **não** foi aberta.

---

## a) Arquitetura: como a Maya funciona (estado mar/2025)

### a.1 Cascata com ASR — confirmado pelo próprio CTO

Pergunta da comunidade sobre "bridge transcription and text processing" `[00:05:17]`:

> [P] "So we do use transcription in the product, in the demo. And I wouldn't say
> there's anything particularly special about the transcription part, but getting it
> to be very fast is a big challenge. (…) This demo does use transcription and mostly
> it's about speed. And it's about getting the latency of **incremental
> transcription** down as much as possible. And that's more of a systems challenge
> and less of an ML challenge." `[00:05:17–00:06:03]`

E o plano de remover o ASR:

> [P] "A pretty clear path that a lot of labs are taking and we are taking as well
> (…) is just kind of **transcription-free**, just go straight into the text
> component. (…) That's coming and that's not years away or anything. That's coming
> soon. (…) The LM takes as input the audio directly and generates the response. (…)
> the user's audio never goes through text." `[00:05:39–00:06:24]`

### a.2 O que a demo NÃO ouve (limitação paralinguística)

> [P] "The current demo does not hear the user from the perspective of their
> **paralinguistic** kind of emotional tone and so forth. And humans, of course,
> convey a lot of information through their speech that is not the words (…) and
> transcription misses that entirely." `[00:06:49–00:07:37]`

**Nuance importante** `[00:29:10]`: quando Midha diz "it doesn't even understand
audio yet", Kumar corrige:

> [P] "Well, to be fair, the **speech generation part is conditioned on all the
> audio of the conversation**. So the speech generation part is audio-conditioned."

Ou seja: o *CSM* ouve o áudio do usuário (prosódia entra no condicionamento da fala
gerada — daí o "espelhamento" emocional), mas o *LLM de conteúdo* só vê transcrição.
A demo "sente" seu tom na hora de falar, mas não na hora de *decidir o que dizer*.

### a.3 Componentes do sistema completo (o que NÃO foi open-sourced)

> [P] "We're open sourcing the speech generation model that is powering the voice of
> the demo. The demo is a broader system than just that. There's of course the LM
> component, the text content generation component. There's also **audio
> understanding, transcription**, and there's a lot of **system optimization** to
> bring the latencies very low and to have this fluid back and forth conversation.
> (…) we've done a lot of work to try to get the **interruptions** to just feel
> better. That has nothing to do really with the core speech generation model that
> we're open sourcing." `[00:20:58–00:21:44]`

### a.4 Turn-taking e interrupção hoje: heurísticas

> [P] "These models today do not model the structure of the conversation at all.
> They only model the content, text and speech. And because of that you still need
> some other set of models or systems that kind of **drive the conversation**
> actually. Like when should the system respond, when should it get interrupted, how
> should the interruption be manifested and so forth." `[01:01:40–01:02:05]`

> [P] "I don't think you want to in the long term have those dynamics be like
> heuristics and so on — **which they kind of are now. They're models involved in
> some heuristics** and so forth." `[01:03:34]`

Sobre a complexidade do problema `[00:41:11–00:42:20]`: cross-talk a negociar,
**backchannels** ("indicate to the other person that you're listening with like a
little sound"), interrupções que são rudes vs. interrupções boas ("the other person
is taking a lot of time to explain something that you already understand and you
should cut them off").

### a.5 Receita para recriar uma "Maya local" (dita por ele)

> [P] "You're going to have to pick some **transcription option** probably and some
> **LM option** and you can prompt it however you want (…) and then use the model
> that we're open sourcing, probably **fine-tune it for the voice of your choice**
> and hook it up in a kind of **cascaded way**." `[00:22:34–00:22:58]`

---

## b) AR vs diffusion — o argumento completo

Trecho central do episódio para nós `[01:05:51–01:08:37]`. Midha pergunta: dados
contínuos → por que não diffusion?

> [P] "Diffusion models are continuous in the sense that the data that they model is
> continuous data. But they're **not natively in any way causal**. They're not
> continuous in the time dimension per se. The autoregressive transformers, they
> **are causal** and so they have an axis which is time, which makes sense from a
> conversational perspective. (…) Causal meaning every time step is conditional on
> what's before and not after." `[01:06:13–01:06:41]`

Mas diffusion não está descartada — só não no backbone:

> [P] "We are also working, by the way, on ideas that make the **audio generation
> part diffusion**. (…) You have a **transformer backbone** which is where most of
> the hard reasoning happens. When you want to add a new modality to the
> understanding path, you have some **adapter** that takes that modality and puts it
> into the backbone. And then you have a **generation path** that takes the backbone
> and generates out the audio. **That path can be diffusion. We want that to possibly
> be diffusion in the future. There are some great advantages to diffusion. But the
> core backbone will need to remain causal.**" `[01:07:04–01:07:50]`

Sobre alternativas e a inércia de engenharia dos transformers:

> [P] "There are other architectures slowly gaining popularity — **Mamba and SSMs**
> and so on, and there's some exciting things there. But transformers are this
> tried-and-true thing and **I wouldn't bet against transformers, not in the short
> term anyways**." `[01:07:50–01:08:12]`

> [P] "If you want to make a different architecture that competes with it, you have
> to make a better core architecture — but then you also have to compete with **all
> of the engineering optimization that has happened on transformers** over the last
> three, four, five years. (…) Transformers are not natively the best — you can
> imagine a better architecture for low-latency inference — but because of all the
> engineering work the community has done, it's very good." `[01:08:37–01:09:43]`

Com $10B a mais? "I don't know the answer (…) there's not another architecture to
bet on today." `[01:08:12–01:08:37]`

---

## c) Dados, escala e o que se ganha com tamanho

### c.1 Variantes treinadas e scaling laws para fala

Pergunta: "How do the scaling laws for speech differ from text?" `[00:47:01]`

> [P] "We published in our blog post — we trained three variants. We trained
> **1 billion, 3 billion, and 8 billion** of just speech generation. And **even the
> 1 billion is very good at speech generation**. What you find as you scale up is you
> really are starting to hit the kind of **long tail things and the contextual
> things**." `[00:47:01–00:47:16]`

Os dois probes de escala que ele detalha:

1. **Homograph disambiguation** — "lead/lead", "row/row": gera a frase, transcreve
   com **phoneme transcriber**, verifica qual pronúncia o modelo escolheu pela
   semântica da frase. "As the models get bigger, they're much better at picking the
   right pronunciation." `[00:47:16–00:48:47]`
2. **Pronunciation consistency** — palavras com variantes válidas no inglês americano
   ("route/root"): prompt de áudio com uma variante → o modelo deve **manter a mesma
   pronúncia** na continuação (clonar voz = clonar pronúncia/accent). Também melhora
   com escala. `[00:48:47–00:49:36]`

> [P] "The contextual things are what we care the most about. Are they able to pick
> up more and more information from the context to condition what they generate?"
> `[00:49:36–00:49:57]`

### c.2 Dados mencionados (pouco — o episódio não cobre curadoria)

- **Não há menção a "1M horas"** nem a fontes/curadoria/anotação do corpus de
  pré-treino no episódio inteiro (verificado por grep em "million/hours/dataset").
- Única menção a dados: para **evals** — "some datasets that are academic datasets.
  We also have some datasets that are kind of like just **two people in a
  conversation or sometimes they're actors**, but trying to be a real conversation."
  `[00:54:06]`
- Sobre vozes: o base model "doesn't know Maya or Miles at all. It doesn't have any
  voices baked in" `[00:23:19]`; "**we fine-tuned this model for Maya and Miles
  separately**" `[00:24:50]`.

### c.3 Voice cloning = in-context learning (não feature dedicada)

> [P] "Typically with some other text-to-speech models the voice cloning is like an
> explicit feature — the model has dedicated voice cloning input. For us, it's just
> a **string of text-audio-text-audio conversational back and forth**. And the voice
> cloning is just in-context learning." `[00:23:41–00:24:28]`

> [P] "It's capable of **zero-shot**, it's capable of **few-shot**. You can set up a
> prompt of more than one utterance. It's not just one 15 seconds and then it clones
> it. You can set up as many as you want and then generate speech at the end."
> `[00:24:28–00:25:11]`

E nota de mercado (mar/2025): "at least to our knowledge there's not another model
out there that is open source that is a contextual thing where you can put **two
participants in a conversation, even more, three**, and generate a conversation
between them — you providing the text and then it generates the audio."
`[00:25:36–00:26:02]` (caso de uso tipo NotebookLM citado explicitamente).

---

## d) Latência: números e técnicas

Pergunta da comunidade: "how is it so fast?" `[00:43:36]`

> [P] "**How is it so fast is a bunch of systems engineering.**" `[00:43:36]`

> [P] "There are the core systems — transcription and the LM and our speech
> generation — and each of those you **hyper-optimize** as much as you can, and you
> want to **pipe them together in an optimized way**. You want to do some
> **pre-computation and caching** to try to minimize latency across everything you
> possibly can. I wouldn't say there's one trick." `[00:44:28–00:45:14]`

> [P] "There's a lot of places in the system where latency can creep in. We want
> **sub-500 millisecond response times**, and a lot of things that feel like not a
> big deal — **50 milliseconds here, 50 milliseconds there — can really add up**.
> It's a focus across the stack on just systems engineering." `[00:45:14–00:45:32]`

Outros pontos de latência espalhados pelo episódio:
- O gargalo do ASR é a "latency of **incremental transcription**" `[00:05:39]` —
  sugere ASR streaming com hipóteses parciais.
- Escalar o backend pós-viral mantendo latência baixa "across a bunch of users" foi
  um desafio de infra à parte `[00:44:04–00:44:28]`.
- Transformers não são "natively the best" para inferência de baixa latência — eles
  compensam com a engenharia acumulada do ecossistema `[01:09:21]`.

---

## e) Roadmap de pesquisa: multimodal único → full-duplex

### e.1 Fase 1 (próximos meses, na época): um transformer só

> [P] "CSM is kind of the first step of making a multimodal transformer-based
> architecture that generates speech. The path that we're going to take over the
> next few months is making a **single transformer that does both audio
> understanding, text content generation, and speech generation**." `[01:00:06]`

Ordem das modalidades, com justificativa:

> [P] "**It's much harder to add a generative modality to a pre-trained model than
> it is to add an understanding modality. So very soon we're going to add an
> understanding modality.**" (exemplo do Midha: "if I cough, it'll understand I just
> coughed" — "Right.") `[01:00:31–01:00:54]`

> [P] "**We don't intend to pre-train the LLMs. We love the open-source LLMs that
> are out there. We'll continue building on top of them. In general we take the
> open-source LLMs and we add modalities to it.**" `[01:00:54–01:01:15]`

Duas linhas de trabalho que se fundem: (1) CSM (geração contextual de fala);
(2) audio understanding sobre LLM pré-treinado → "we'll merge the two into a single
model that can both understand and generate speech and text." `[01:01:15–01:01:40]`

### e.2 Fase 2 (longo prazo): full-duplex por frame

> [P] "This research area of conversational voice has to really move to **full
> duplex models**. There are in the literature some early and compelling
> architectures and paths. **There's some from Meta, there's some from other research
> labs. There's one called Moshi that's kind of interesting.** We need to get to ways
> where we can create those architectures but **initialize them or maintain the
> capabilities and knowledge of LLMs — and that's a little bit unclear how exactly to
> do that**. But that's really what we're looking towards long term."
> `[01:02:28–01:02:50]`

> [P] "We'll have these duplex architectures (…) **all of the turn-taking and back
> channels and so on will be implicit in the architecture. It's generating audio
> every time slice, every frame. And that is I think the path to getting systems
> that really feel truly real.** (…) those complicated dynamics do need to be
> **learned from data**." `[01:03:10–01:03:34]`

A justificativa RL-style do frame de ~100 ms:

> [P] "It's probably frame — say **100 milliseconds** of time. You want the model to
> make as many decisions as it can. Right now (…) you're making a full *sentence* of
> a decision at a time. The model is like 'I'm going to say this in this way' — but
> it's a full sentence, and it can't update that decision on its own until the end
> of the sentence. (…) **That's just too long of a decision.** You need to make
> decisions at the 100-millisecond time segment, so that if you're talking and the
> other person starts making some noises that make it seem like they're trying to
> interrupt you, you can **back off and let them say something — or not**. Those
> decisions need to be made constantly." `[01:03:58–01:05:28]`

E a admissão honesta sobre o presente:

> [P] "The models that we have today, like CSM for example, **and probably some of
> the models that we'll have in the short term** (…) will still not be modeling the
> conversational dynamics because they're making decisions at sentence at a time."
> `[01:05:28–01:05:51]`

### e.3 Por que TTS contextual ≠ TTS

> [P] "There are an infinite number of ways that you can say any line of text. So
> you need more context to tell what is an appropriate way for this moment in the
> conversation. (…) There's some kind of **mirroring** of the other person's
> emotions, but it's not necessarily just copying it — if the other person's
> excited, you might be more excited; if the other person is sad, you might not be
> sad, you might be more **consoling**. Those dynamics are very complicated. You
> can't just have an if-then thing. **It really does need to be learned from data.**"
> `[00:26:46–00:28:24]`

> [P] "**Traditional text-to-speech is kind of like it can only be flat. Or in other
> words, if it tries to not be flat, it's very likely wrong.**" (a explicação dele
> para por que voice assistants históricos soam chapados — sem contexto, o ótimo é o
> "lowest common denominator", neutro-robótico) `[00:28:24–00:28:48]`

---

## f) Evals: como medem qualidade

### f.1 O problema: WER saturou

> [P] "Earlier on in the speech generation community very often you'd look at **word
> error rate** (…) **those metrics are getting saturated basically**. These models
> are just good enough (…) at a corpus-wide level these models are very very good
> now." `[00:52:56–00:53:21]`

### f.2 A escada de evals da Sesame (do quantificável ao qualitativo)

1. **Pronúncia como probe** (quantificável): homógrafos + consistência de variante
   (seção c.1) + **pronúncia de nomes próprios** — "that's a good example of a
   **product-centric evaluation** (…) when a voice assistant says your name wrong,
   it feels bad" `[00:50:59–00:51:23]`. Anedota do Midha: Maya pronunciava "Anj"
   errado todo dia até que um checkpoint passou a preservar a pronúncia ensinada.
2. **Preferência humana estilo arena**: "those evaluations look very similar to how
   LLM evaluations go — preferences, an arena, head-to-head ranking."
   `[00:53:43–00:54:06]`
3. **Win-rate contra humano real**: "we'll take the conditioning of some snippet of
   the conversation and then show a human rater **the real continuation and the
   model's continuation**. So it's like a win rate against real." `[00:54:06–00:54:31]`
   (— é o CMOS "no context / with context" do blog post, descrito em palavras.)
4. **Loop qualitativo de produto**: "It's not the case that we're looking at numbers
   going up and we say, well, it hit X metric, time to ship. It is more a constant
   feedback loop of **trying it, feeling it**, having other people try it."
   `[00:02:33–00:03:45]` — com o caveat de que o time interno "esgota" as primeiras
   impressões ("you can only get so many first reactions").

> [P] "How do you **hill climb effectively on what is really an ML problem** (…)
> when the metric that you really want to target is some sort of **qualitative human
> reaction**? That is very hard to quantify." `[00:02:57–00:03:20]`

> [P] "**If you have your evaluations too divorced from the product experience, you
> might not find these product-feeling qualitative upsides.**" `[01:11:20–01:11:46]`

---

## g) Produto, persona, visão

### g.1 Trade-off assumido: naturalidade > inteligência

> [P] "If you talk to Maya and Miles, you probably will not be able to get the same
> quality of reasoning capabilities or intelligence as other systems, but in return
> you're getting this much more natural, fluid interaction." `[00:09:15]`

> [P] "**We are not a frontier model company. We're not pre-training LLMs at insane
> scale. We're really a company that's trying to marry great technology with
> creative taste to produce a great experience.**" `[00:09:40]` (Pixar citada como
> empresa aspiracional `[00:10:03]`.)

### g.2 Imperfeições de propósito

> [P] "The demos are imperfect in a way that feels natural. (…) Maya and Miles might
> say the wrong thing or **back up a little bit and say something else** — and
> **that's on purpose**. If you just looked at the text from a purely textual
> perspective, you might call that wrong. **But it actually feels more real.**"
> `[01:10:30–01:11:20]`

### g.3 A crítica "Maya parece atriz" — e a resposta

Midha (ex-Discord) observa que conversa de voz real (canais de voz do Discord) é
majoritariamente mundana — "people just hanging out talking" — enquanto Maya "keeps
trying to inject excitement, almost like an actor" `[00:55:19–00:56:08]`. Kumar:

> [P] "I think it's that way because **we have more work to do**, more or less. (…)
> Often it's too happy, too energetic, too positive, feels like it's acting, feels
> like it's forced. **That's just work that we need to do.**" `[00:56:08, 00:58:13]`

> [P] "Voice is a much higher bar because it's such a high-bandwidth communication —
> even such little things will make you feel like the person on the other side is
> fake. (…) Text is a compression of the entity on the other side; **voice is this
> kind of open duplex thing. Voice is harder.**" `[00:56:32–00:56:58]`

E a questão de design em aberto: "these systems are superhuman — they know much
more (…) What are the things you want this thing to feel human around, and where do
you want it to be superhuman?" `[00:57:20–00:58:13]`

### g.4 Por que não API (foco) — e o que vem (app, memória)

> [P] "People ask for an API a lot. The main reason is **focus**. (…) **Anything
> that's not that path is basically a distraction right now.** (…) everything is a
> drag on engineering." `[00:36:22–00:38:00]`

Razão técnica adicional: "when you make an API you are baking in some interfaces to
that system — how do you control it, how do you tune it — and **it's just a little
early** (…) those things start constraining you if you want to make major changes."
`[00:40:28–00:40:47]` E: "making a great personality voice interface system — we
can't turn it into an API that produces super high quality outcome today (…) it
takes more than voice clone plus change the prompt." `[00:39:14–00:39:41]`

Produto: "**We are making an app.** It'll be a product (…) you'll talk to Maya or
Miles or whatever character you want and **it will remember you**." `[00:58:42–00:59:48]`
Companion precisa de: memória/relacionamento `[00:30:16]`, personalidades
customizáveis ("we don't see our product as one companion that's the same for
everyone" `[00:38:26]`), e — longo prazo — agência via sistemas downstream.

### g.5 Óculos como form factor

> [P] "Glasses are really pretty optimally placed to be a sort of **mirror of your
> perceptions** — right where your eyes, ears, etc. are. (…) **it's where all your
> perception organs are basically.** And it's a product category that billions of
> people wear all day every day." `[01:33:35ish → 00:33:11–00:33:56]`

Por que "everyday, all day": "It takes a lot to earn hardware on someone's body.
(…) **All day everyday allows it to become a habit.** If you have to think 'do I
have it on or not right now', the friction is high." `[00:34:19–00:35:54]`
Com visão (sight) como contexto: "it will feel very much like it's in the room with
you, kind of over your shoulder." `[00:30:41–00:31:09]`

### g.6 Companion = camada de interface de computação

Visão de stack `[01:27:11–01:29:19]`: telefone continua sendo o compute primário;
por cima, uma **companion layer** ("AI interface layer") com memória, naturalidade,
personalidade — e essa camada conversa com **downstream services** (busca, serviços
digitais, *outros sistemas de IA* que fazem tool-calling/raciocínio). A divisão de
otimização: na camada companion otimiza-se **delightfulness/personalidade**; no
downstream, **capability/reasoning**. "Which one has a personality that you want to
talk to — it's more of a product question." `[01:20:53]`

> [P] "I think the best product experience will be built by a **very focused small
> team**." `[01:30:54]` (resposta a "por que as big techs não tomam essa camada?")

### g.7 Time e contratação

- "The full software team today is still **under 15 people**" — incluindo ML e
  infra `[00:08:26]`. "The core ML team is something like **seven or eight**"
  `[00:45:32]`.
- Perfil: generalistas — "there's really no one that has 10 years of experience
  serving transformers at scale (…) you need people who are excited to learn"
  `[00:46:24–00:46:50]`. Pesquisadores com "bent" para experiência do usuário
  ("do you care about doing the little things right to get interruptions to feel
  really good?" `[00:13:48]`).

### g.8 Por que open-sourcear o CSM

> [P] "We're open sourcing mostly as a kind of research-axis thing. We are not a
> developer-facing business. We're not making an API. (…) It's not for customer
> acquisition. **We just want to give back and be part of the research community.**"
> `[00:19:04–00:20:13]` ("We'll hold some things back for sure. We have to build a
> business." `[00:20:36]`)

Taste em ML para uma startup pequena `[00:14:38–00:15:51]`: "picking the things that
you have to do and not doing the things that you don't have to do" — não construir o
que a comunidade/big labs vão entregar de graça (LLM base), construir só o que
diferencia (speech generation contextual, personalidade) — "we didn't think and we
still don't think [that] will just be done by the community." `[00:17:28]`

---

## h) Mapa do episódio (timestamps úteis)

| Tempo | Assunto |
|---|---|
| 00:00–00:01 | Cold open: a própria Maya apresenta o episódio |
| 00:01–00:05 | Reação ao viral; como decidiram lançar (gut + evals) |
| 00:05–00:07 | **Cascata/ASR; transcription-free "coming soon"; paralinguística perdida** |
| 00:07–00:14 | Por que é melhor que os outros; time <15; Pixar; foco |
| 00:14–00:18 | "Good taste in ML" = o que construir vs. herdar da comunidade |
| 00:18–00:26 | **Open source do CSM: o quê, por quê, receita de uso, ICL cloning** |
| 00:26–00:29 | **TTS contextual vs TTS; mirroring; "can only be flat"** |
| 00:29–00:36 | Contexto além do áudio; memória; **óculos all-day** |
| 00:36–00:41 | Por que não API |
| 00:41–00:43 | **Complexidade da conversa humana: turn-taking, backchannels, interrupção** |
| 00:43–00:46 | **Latência: systems engineering, sub-500ms, 50ms somam** |
| 00:46–00:51 | **Scaling laws da fala: 1B/3B/8B, homógrafos, consistência de pronúncia** |
| 00:51–00:55 | **Evals: WER saturado, arena, win-rate vs humano real** |
| 00:55–00:58 | Crítica "parece atriz"; voz como meio de alta largura de banda |
| 00:58–01:00 | App vindo; memória; demo continua no ar |
| 01:00–01:06 | **Roadmap: multimodal único (understanding→generation); full-duplex ~100ms; Moshi/Meta** |
| 01:06–01:10 | **AR vs diffusion; backbone causal; head diffusion possível; Mamba/SSM** |
| 01:10–01:16 | Imperfeições de propósito; medo de "regressão tipo ChatGPT" — companion ≠ assistant |
| 01:16–01:31 | Companion como interface de computação; stack futuro; small focused team |
| 01:31–01:35 | Plugins/ecossistema "cedo demais"; contratação |

---

## i) O que o episódio NÃO responde (lacunas)

- **Dados de pré-treino**: zero detalhe sobre o corpus (~1M h é só no blog post),
  fontes, filtragem, anotação, licenciamento, quantas vozes.
- **Tokenizer/codec**: nenhuma menção a Mimi/RVQ/semantic+acoustic tokens (blog cobre).
- **Decoder de dois estágios do CSM** (backbone + audio decoder): só aludido
  genericamente na discussão de diffusion head.
- **Quem é a voz da Maya** / como gravaram os fine-tunes de personagem.
- **Números de tráfego/custos de inferência** pós-viral.
- **Latência decomposta** por estágio (ASR vs LLM vs CSM) — só o alvo agregado <500ms.

---

## j) Implicações para o Maya-BR

1. **A cascata está oficialmente validada como ponto de partida.** O próprio CTO
   descreve a demo viral como ASR incremental → LLM → CSM e dá a receita: "pick some
   transcription option, some LM option, fine-tune [CSM] for the voice of your
   choice, hook it up in a cascaded way". Nossa Fase 0/1 (Whisper-streaming + LLM
   open pt-BR + CSM-1B fine-tuned) é literalmente a arquitetura da Maya de mar/2025
   — não é uma aproximação pobre, é A arquitetura.
2. **1B é suficiente para naturalidade.** "Even the 1 billion is very good at speech
   generation" — escala (3B/8B) compra long-tail de pronúncia contextual, não a
   naturalidade base. Para o nosso budget (Colab/finetune, dossiês 40/84), insistir
   no CSM-1B é defensável com a palavra do próprio Kumar.
3. **Onde investir o esforço (em ordem): sistemas > persona > modelo.** O "como é
   tão rápido" é pré-computação, caching, pipelining, ASR incremental e
   hiper-otimização por estágio — sub-500ms como alvo, orçamento mental de "50ms
   somam". Isso valida a prioridade do orquestrador (dossiê 83) sobre treinar
   modelos maiores. Meta concreta pro Maya-BR: **orçamento de latência por estágio
   somando <500ms**, medido desde o fim da fala do usuário.
4. **Turn-taking não precisa esperar full-duplex.** A Maya viral fazia
   interrupção/backchannel com "models involved in some heuristics". Podemos fazer
   igual: VAD + regras + (opcional) classificador leve de end-of-turn. A versão
   full-duplex (decisão a cada ~100ms) é o longo prazo — e Kumar cita **Moshi**
   nominalmente como caminho compelling, o que valida nossa trilha dupla CSM+Moshi
   (dossiês 11/82). O problema em aberto que ele admite ("como inicializar
   arquiteturas duplex mantendo conhecimento de LLM") é exatamente o gargalo que o
   Moshi-finetune contorna por já vir pronto.
5. **LLM: não treinar, adaptar.** Sesame não pré-treina LLM; usa open-source e
   adiciona modalidades. Para nós: LLM pt-BR open (ou multilíngue com bom pt) +
   prompt de persona, e eventualmente adapter de audio understanding — na ordem que
   ele indica (understanding antes de generation, por ser mais fácil acoplar).
6. **Evals copiáveis amanhã:** (a) homógrafos/heterófonos pt-BR como probe de
   contexto — pares tipo *gosto* (verbo/substantivo), *jogo/jogo*, *olho/olho*,
   *colher/colher*, *sede/sede*, *seca/seca*, *governo/governo* (vogal aberta vs
   fechada) — gerar frase desambiguadora, transcrever com phoneme transcriber,
   medir acerto; (b) **consistência de sotaque**: prompt de áudio com variante
   regional (ex.: /t/ palatalizado carioca vs não-palatalizado, "porta" com /r/
   retroflexo caipira vs fricativo) → a continuação deve manter a variante — é o
   eval route/root transplantado para a nossa tese de sotaque (dossiês 50/85);
   (c) win-rate vs continuação humana real em conversas pt-BR; (d) pronúncia de
   **nomes próprios brasileiros** como eval product-centric.
7. **Persona: imperfeição é feature.** Auto-correções, hesitações, "voltar atrás" —
   de propósito. Incluir nos dados de fine-tune da persona BR (roteiros com
   disfluências naturais, dossiê 60) e NÃO limpar disfluências agressivamente na
   curadoria. Mas calibrar: a crítica "parece atriz" (energia/positividade demais)
   é o erro a evitar — conversa real é mundana; mirar o registro "papo de varanda",
   não "apresentadora de podcast".
8. **CSM é audio-conditioned — usar isso.** O espelhamento emocional da Maya vem do
   condicionamento do CSM no áudio da conversa toda (incluindo o usuário), não do
   LLM. No nosso pipeline, alimentar o contexto de áudio real do usuário no CSM
   (não só o texto) é o diferencial barato que separa "TTS bom" de "presença".
9. **Não construir o que a comunidade entrega.** A lição de "taste em ML" dele é o
   nosso filtro de escopo: ASR (Whisper), LLM (open), codec (Mimi) — herdar;
   fine-tune de voz/persona pt-BR, dados de sotaque, orquestração de latência,
   evals pt-BR — construir, porque ninguém vai fazer por nós.
10. **Expectativa de mercado:** Kumar admite que "they're going to get better
    voices, for sure, across the board" e que a Sesame não tem "magical secret
    sauce" técnica — a defesa é produto/persona/foco. Para o Maya-BR a leitura é a
    mesma: a vantagem durável não é o modelo, é persona + sotaque + latência + o
    gosto de quem monta.

---

## Fontes

- Transcrição integral: legendas auto-geradas do YouTube (`bTcpNQH8ViQ`), coletadas
  2026-06-10 via yt-dlp (`en-orig.vtt`, 900 KB). [P]
- Página do episódio: https://a16z.com/podcast/building-the-next-generation-of-conversational-ai/ (sem transcript) [P]
- Outline de terceiros: https://podwise.ai/dashboard/episodes/3320382 (confirma duração 1h41 e tópicos) [S]
- Cross-refs internas: dossiês 10 (CSM/blog post), 11 (Kyutai/Moshi), 81/82 (OSINT
  Sesame), 83 (orquestradores), 84 (finetune CSM), 50/85 (sotaque/eval pt-BR).
