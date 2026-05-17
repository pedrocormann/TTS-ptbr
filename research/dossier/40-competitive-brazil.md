# Dossier 40 — Competitive / news / Brazil-funding (web research, 2026-05-17)

> Autonomous web research (Pedro away). Wedge = experiential/cultural/gov clients
> that reject per-minute cost; moat = owned small model → fixed-price/fail-closed.
> ⚠️ Prices are 2026 third-party-aggregated — verify on official pages before
> quoting a client.

## 1. ElevenLabs (incumbent)
- Conversational AI ≈ **$0.08–0.12/min** (Standard/Turbo/Premium); subs Free→…→Business $1,320/mo→Enterprise. **Pure usage-based; NO fixed-price/fail-closed product.**
- Experiential math: 8h/day always-on booth ≈ ~480 min/day ≈ **R$1,150–1,750/day just voice** (Premium) — exactly the wedge barrier.
- **Feb 2026: raised $500M @ $11B** (Sequoia; from $3.3B Jan-2025); >$330M ARR; IPO talk.
- **Explicitly expanding to Brazil** (+MX/IN/JP/SG), has BR office — direct threat, but model stays cost-variable.
- Startup Grant: 12mo free Conv-AI, >680h — runway but lock-in risk; doesn't change their pricing model.
- **Weaknesses for wedge:** unbounded per-min; no cap/fail-closed; closed = no on-prem/offline for low-connectivity installs; generic pt-BR not culturally tuned.

## 2. Other players
Cheap-at-scale: **Cartesia Sonic 3 ~$0.0225/min**, Deepgram components, **Kyutai (free/open)**, self-hosted Sesame/CSM. Premium: ElevenLabs, OpenAI Realtime (~$32/1M in, $64/1M out; Translate $0.034/min), Hume (best emotion). Mid: Google Gemini Live (token-based, Flash cheap), PlayHT, Rime, Deepgram, Speechmatics. Orchestration: Vapi ($0.05/min platform, ~$0.30+ all-in), Retell ($0.07+/min), LiveKit (OSS, $0.004/min+providers). Studio (not real-time): WellSaid, Murf (PT).
**Read:** open full-duplex at 200–300ms is now free/real (Kyutai/Moshi, Sesame CSM) ⇒ the defensible asset is **productization + fixed-price packaging + pt-BR cultural tuning + serving-cost discipline**, not model novelty. Wedge validated.

## 3. Brazilian / pt-BR players
- **Maritaca AI** — leading BR LLM (Sabiá-3.1/4, ~GPT-4o on PT at lower cost). **No TTS/voice** ⇒ text-LLM **partner** candidate, not a voice competitor. CEO pushes sovereignty narrative (useful for FINEP framing).
- **Edresson Casanova** — YourTTS/XTTS/CML-TTS creator, now **Sr Research Scientist @ NVIDIA**. The academic backbone of open pt-BR TTS. **#1 person to watch + collaboration/talent anchor.**
- **CEIA-UFG (Goiás)** — origin of CML-TTS; strongest pt-BR speech-synthesis lab. Academic-commercial bridge target (also strengthens SDumont/FINEP).
- **CPQD** (Campinas) — legacy gov/telecom speech; no 2025-26 conv-AI signal.
- **WideLabs** — BR startup, NVIDIA-partnered (Nemotron Personas Brasil, cultural pt-BR). Watch as competitor or ally.

## 4. Brazil AI sovereignty funding/policy 2025-26
- **FINEP/MCTI Digital Technologies edital — R$300M**, PBIA-aligned, submissions until **2026-09-30** (continuous flow). **Most realistic DIRECT funding vehicle** for a pt-BR sovereign small-model project. Priority target.
- **FINEP+BNDES AI Fund (Apr 2026):** FINEP ≤R$80M + BNDES ≤R$125M, fund-of-funds (equity), manager-selection deadline 2026-05-28 — likely **not directly applicable** (not a grant).
- **PBIA** national umbrella; sovereignty + national infra funded.
- **SDumont/LNCC:** continuous-flow call; 2026 call open. **Upgraded mid-2025: +575% capacity, 18.85 PF, NVIDIA HW — "first step of PBIA."** Confirms plan (SDumont free for *training only*, not serving). Needs academic-aligned proposal (CEIA-UFG/USP partnership helps). Allocation 500k–4.9M UA standard.
- **NVIDIA Inception Brazil** — 1,600+ startups, free GPU credits/discounts. Valid overflow path.
- **"Fala Cidadão"-type gov voice:** gov.br has text chatbots (Transferegov/PEN/EBSERH) — **no voice tender yet**; pt-BR voice gov channel = whitespace, not yet a procurement line.

## 5. News/signals (~12mo)
ElevenLabs $500M@$11B (Feb-26), $330M ARR. **Sesame $250M Series B (Oct-25)**, iOS beta, 5M+ min, CSM-1B open, pivoting to wearables — **not selling pt-BR API ⇒ low direct competition on wedge; open CSM stays usable.** Kyutai TTS+Unmute open-sourced (Jul-25) + Voice Donation → open voices. OpenAI gpt-realtime GA -20% + Realtime-2/Translate. Cartesia Sonic 3 ~$0.0225/min. **ANPD:** biometrics regulation in 2025-26 agenda, rules **expected 2026**; **voice biometrics = sensitive personal data under LGPD**; voice-clone fraud +800%, est. R$4.5B losses 2025 — synthesis-training consent is a live legal risk.

## 6. Pricing-model intelligence
~All incumbents pure usage/per-minute; Vapi/LiveKit add platform fee on stacked variable cost. **No major player offers annual fixed-price + quota + fail-closed.** Anchor proof: Sesc/Mariclea PO frozen *specifically* on ElevenLabs per-min cost. Fixed annual + hard cap + graceful fail-closed = **uncontested commercial position**, enabled only by owning a small model (~R$0.02–0.12/min self-host, 10–40× under ElevenLabs).

## Decision-relevant
1. Moat thesis confirmed: defensible asset = fixed-price/fail-closed packaging + pt-BR cultural tuning + serving discipline, not model novelty.
2. ElevenLabs coming to Brazil but **structurally can't follow on fixed-price** without cannibalizing $330M ARR — pricing wedge durable vs incumbent.
3. **FINEP R$300M Digital Technologies (deadline 2026-09-30) = priority funding target** (direct, PBIA/sovereignty-aligned). The Apr-2026 FINEP+BNDES fund is equity, likely N/A.
4. LGPD/ANPD voice-biometrics rules land 2026 — design consent/data-provenance NOW (moat: compliant-by-design; landmine: training-data consent).
5. CEIA-UFG + Edresson Casanova = pt-BR academic backbone; partnership strengthens SDumont allocation AND FINEP/PBIA positioning.

## Weekly vigil watchlist
Companies: ElevenLabs (BR moves/pricing), Cartesia (price floor), Kyutai (open releases), Sesame (CSM/pivot), Maritaca + WideLabs (pt-BR sovereignty), Hume (emotion bar).
People: Edresson Casanova (NVIDIA, pt-BR TTS SOTA); Maritaca CEO (sovereignty advocacy).
Sources: finep.gov.br/noticias, gov.br/mcti, sdumont.lncc.br/call.php, gov.br/anpd (Reg. Agenda Item 5), elevenlabs.io/pricing+blog, kyutai.org/blog, arXiv cs.CL/cs.SD (pt-BR TTS), instituto.ia.lncc.br.

## Park (needs spend/contact/legal — DO NOT ACT)
Apply FINEP R$300M edital (budget+legal/CNPJ, maybe academic co-proponent CEIA-UFG); ElevenLabs Startup Grant (weigh lock-in); SDumont 2026 proposal (needs PI/academic affiliation — contact CEIA-UFG/USP); NVIDIA Inception application; legal counsel on voice-clone consent + provenance vs LGPD/ANPD 2026 before any voice-donation/cloning collection.
