# Research Vigil Log

Weekly scan (per CHRONOGRAM standing ritual): review watched orgs/people/arXiv →
log findings here → decide incorporate into the spine / test in parallel / ignore.

---

## 2026-05-17 — Deep scan #1 (autonomous, 5-front + code reads)

Dossier written: `research/dossier/{00-SYNTHESIS,10..50}.md`. Highlights:

**Incorporate into the bet:**
- **J-Moshi (arXiv 2506.02979)** — non-EN/FR Moshi recipe = CPT + tokenizer/embed
  swap + stereo FT, Mimi frozen. ⇒ pt-BR plan is CPT, not LoRA-only. Use
  `nu-dialogue/moshi-finetune` + `nu-dialogue/j-moshi` as references. **Adopted.**
- **Moshi weights = CC-BY-4.0** (verified in cloned repo README) — commercial OK
  w/ attribution. Bet legal. **Confirmed.**
- **Codec = freeze/clone Mimi recipe** (12.5 Hz split-RVQ WavLM-distilled causal).
  Foundational, upstream of spine. **Adopted into Phase-0 (test #1 = Mimi freeze).**
- **Emotion = implicit + NL prompt + light paralinguistic-RL** (Step-Audio 2,
  arXiv 2507.16632, ~2× GPT-4o-Audio). **Adopted for Phase-3 method.**

**Test in parallel / watch:**
- Qwen3-Omni (2509.17765, Apache-2.0) — co-bet hedge; verify pt speech-output.
- Step-Audio 2 (2507.16632) — emotion/paralinguistic-RL method study.
- Full-Duplex-Bench v1.5/v2 (2507.23159 / 2510.07838), URO-Bench (2502.17810) —
  eval harness blueprint (pt-BR version = strategic asset, none exists).
- Codecs: U-Codec/FlexiCodec/TS3 5-Hz frontier (watch, don't adopt yet).
- Watermarking: AudioSeal (2401.17264), VoiceMark (2505.21568) — day-one.

**New facts logged:**
- ElevenLabs $11B (Feb-26), entering Brazil, pure usage pricing → wedge durable.
- Sesame $250M Series B, pivot to wearables, not selling pt-BR API.
- FINEP R$300M Digital-Tech edital, deadline 2026-09-30 (priority funding).
- SDumont +575% capacity ("first step of PBIA"); free training-only confirmed.
- ANPD voice-biometrics rules expected 2026; voice = sensitive data (LGPD).

**Watchlist (scan weekly):**
- Orgs/repos: kyutai-labs (moshi/finetune/DSM/hibiki releases), QwenLM (Qwen-Omni),
  stepfun-ai (Step-Audio), SesameAILabs (csm), canopyai (Orpheus), nu-dialogue
  (J-Moshi lineage), Edresson (pt-BR TTS).
- People: Edresson Casanova (NVIDIA), Kyutai team (Défossez/Zeghidour), Maritaca CEO.
- Sources: arXiv eess.AS/cs.SD/cs.CL (pt-BR / full-duplex / speech-LM / codec),
  HF papers daily (audio), finep.gov.br, sdumont.lncc.br/call.php, gov.br/anpd,
  elevenlabs.io + kyutai.org blogs.
- Recheck at ship: per-repo license text, Moshi watermarker presence, annotate.py
  model versions, Qwen3-Omni pt speech-out.

### 2026-05-17 — scan #1 continued (2 verification frentes)

**Qwen3-Omni pt verified (2 primary sources):** `pt` IS in the speech-OUTPUT
set (HF card + arXiv 2509.17765 Table 3). Genuine co-bet. Caveats: generic "pt"
(likely EU-leaning, pt-BR needs FT); emotion control **weak** (3 fixed speakers
Ethan/Chelsie/Aiden + system prompt only, no tags/clone); no official LoRA;
heavy (~79GB bf16 → 2×A100, community AWQ-4bit only). Apache-2.0 ✅.
- **New emotion model to study: Step-Audio-EditX** (3B, Apache, emotion/style/
  paralinguistic edit + RL) + Step-Audio-2-mini — best-in-class controllable
  emotion, lighter than Qwen. **GLM-4-Voice-9B** (26 langs, low-lat FD, small)
  = 3rd candidate. MiMo-Audio (MIT). No Moshi v2; CSM-3B/8B still closed.

**2-party pt-BR sourcing (dossier 21):** corrects dossier 20. **Câmara CC-BY-4.0**
+ **court/CNJ Art. 8º public-domain** = real commercial 2-party lane (formal
register). **Senado = NC, do not use.** Synthetic via **Kokoro (Apache)/
Chatterbox (MIT)** only — XTTS/F5 NC poisons output. pyannote **community-1** >
3.1. Phase-0 needs ~1–3 h (synth = fastest, no-spend, this week). J-Moshi mix
≈ 602 synth : 344 real on mono-dialogue CPT.

**Action deltas:** to_stereo.py → community-1; tools/data + eval harness built;
spike_c requirements fixed (torch 2.6 conflict — separate venvs B vs C).

### 2026-05-17 — scan #2 (compute budget + voice/watermark) → dossier 60, 70

**CPT probably SKIPPABLE for pt-BR (big).** Finetune ≈ 6–20 GH200-h / <US$60 /
<1 day. Heavy CPT (~920–1,540 GH200-h) only forced by tokenizer-swap/embedding-
re-init — pt-BR (Latin, Helium EN/EU-heavy) likely keeps Helium tokenizer ⇒
**LoRA-only is the first bet; CPT is the fallback gated by native-speaker eval,
not metrics.** Do scenario M (SDumont LoRA, ~free) regardless. SDumont: 1 UA =
1 CPU-core-h, Standard ≥750k covers all; confirm GPU→UA w/ helpdesk-sdumont.

**Voice path CORRECTED.** For a Moshi spine: NOT per-voice LoRA, NOT CSM-front
(CSM doesn't compose with FD Moshi — either/or). Use **Kyutai-TTS/DSM voice-
EMBEDDING conditioning** (re-anchored, no drift); ~5–15 min/voice; LoRA staged
fallback. ⇒ corrects dossier 50's "CSM = the voice component" for the Moshi case.

**Watermark CORRECTED.** Sony RAW-Bench: post-waveform marks (AudioSeal etc.)
ERASED by neural-codec re-encode; our output IS Mimi-decoded. Ship AudioSeal
(MIT) day-one as **provenance signal only**; codec-embedded/Latent-Mark = the
durable Phase-3+ upgrade. VoiceMark license unstated → don't ship.

**Action deltas:** synth 2-party pipeline built + CPU-tested (gen_dialogues +
compose_stereo ✓); eval harness CPU-validated; dossier 50/00 get correction
pointers; PARKING-LOT += helpdesk-sdumont email, privacy counsel, VoiceMark lic.

Next scan: 2026-05-24 (weekly). Big review folds this: 2026-06-17 (`/sdd` ATUALIZAR).

---

## 2026-06-10 — Deep scan #3 (8-front web sweep; the big review, 1 week early)

Dossier: `research/dossier-2026-06/10..60-*.md`. Plan: `specs/REPLAN-2026-06-10.md`.

**Incorporated into the bet:**
- **Qwen3-TTS (jan/2026, Apache, pt native, 97ms TTFA, official finetune)** —
  Track-A candidate #1; also replaces Kokoro as synthetic-data generator.
- **Kyutai interactivity-RL (2026-06-10!, `moshika-rl-seamless` CC-BY-4.0, arXiv
  2606.11167)** — adopted as F5 post-training blueprint (supersedes Step-Audio-2
  as primary reference).
- **PersonaPlex-7B (NVIDIA, jan/2026)** — Moshi-architecture validation + public
  persona/voice-prompt recipe (paper 2602.06053). Weights NVIDIA OML = outside
  whitelist; replicate recipe, don't touch weights.
- **Colab Pro+ A100-80/G4-96GB** — moshi-finetune fits in Colab now.
- **Unsloth CSM-1B T4 notebook** — no public pt-BR CSM finetune exists; open lane.
- **Eval v2**: TTSDS2 + Audiobox-Aesthetics + DNSMOS + Parakeet-v3 second-ASR +
  emotion2vec+ SER head; UTMOS demoted. BIPA (CC-BY, Rio IPA) for accent eval.

**Watch / vetoes:**
- Pocket-TTS-pt (CC-BY, CPU 200ms) — listening test pending (pt-BR vs pt-PT).
- NILC `NURC-SP_ENTOA_TTS` MIT tag — email NILC before training shippable weights.
- New vetoes: Voxtral TTS (NC), Higgs v2/v3, Spark-TTS (relicensed NC!), Fish
  S2-Pro (research), TAGARELA (NC, eval-only), CETUC (research-only).
- Reg: PL 2338 pending vote; **PL 1460/2026** (voice replicas: consent+watermark
  mandatory) — our design is already compliant.

### 2026-06-10 — addendum (Pedro): Frederico Oliveira + programa OSINT-Sesame

- **Frederico Santos de Oliveira** (fredso.com.br · HF `freds0` · UFG/cluster
  Edresson) adicionado à watchlist como **perfil pt-BR #2** (ao lado do Edresson).
  Obra a destrinchar (deep-read agendado p/ próxima sessão de pesquisa):
  TAGARELA (2603.15326) · **SER multimodal grafos+prosódia (2506.02088,
  Interspeech 2025 — insumo direto do nosso SER pt-BR)** · FreeSVC (2501.05586) ·
  CORAA (2110.15731) · wav2vec2-pt (2107.11414) · SC-GlowTTS (2104.05557) ·
  TTS-Portuguese (2005.05144) · Speech2Phone (2002.11213).
  Busca ADS: author:"Santos de Oliveira, Frederico". Contato → PARKING-LOT.
- **Programa OSINT-Sesame formalizado (Trilha M do REPLAN):** vigiar semanalmente
  org GitHub SesameAILabs (forks novos + diffs vs upstream), HF sesame, blog,
  autores do post CSM e ex-funcionários (Scholar/arXiv/LinkedIn/X), vagas e
  patentes. Objetivo: refinar a hipótese arquitetural Maya v0 (cascata
  engenheirada + CSM-Medium condicionado em áudio-contexto) e reproduzi-la
  como **Maya-BR v0** (CSM-1B-pt + LLM pt + turn-engine silero/Unmute).

### 2026-06-10 — noite: deep-read Frederico (dossiê 80) + OSINT-Sesame r1 (dossiê 81)

**Frederico/UFMT-AKCIT (80-frederico-oliveira.md):**
- Perfil: prof UFMT, PhD UFG, pesquisador **AKCIT** (instituto MCTI/EMBRAPII —
  ângulo de parceria/FINEP além do CEIA). HF freds0 ativíssimo (update há 20h).
- SER (2506.02088): receita copiável p/ nosso eval (F0-RMVPE quantizado +
  weighted-CE + ensemble 13 variantes); código público SEM LICENSE — pedir
  permissão antes de derivar. GAT só +1.3pt vs concat.
- TAGARELA: NC-SA reconfirmado; **evidência de ouro: Orpheus/Chatterbox FT no
  clean-2.800h → MOS 4,16 (GT 4,23)** — valida a Trilha A em podcast pt.
  Campo `accent` existe no dataset. ⚠️ **Checkpoints "Coming Soon"** — se
  saírem, são NC-tainted (treinados em NC): NÃO usar pesos, mas é o comp direto.
- **BRSpeechMOS (2306.09979) = único preditor MOS calibrado pt-BR → adotar no
  eval harness** (camada 2). FreeSVC sugere ECAPA2 como 2ª opinião de spk-sim.
- Vigiar: BrSpeech-YT (stub vazio — corpus YouTube vindo?); BRSpeech-TTS (76k
  linhas, campo accent, licença indocumentada).

**OSINT-Sesame r1 (81-sesame-osint.md):**
- Hipótese Maya CONFIRMADA (cascata) e refinada: orquestrador com tool-use
  assíncrono + re-síntese incremental; ~2min de áudio-contexto no CSM;
  **produção possivelmente CSM-1B (não Medium!)**; sglang fork com commits
  reais (logit bias/clamps, CTO); watermark silentcipher; vagas pedem
  vLLM+SGLang+K8s+GCP; **zero patentes** (moat = dados+eng).
- Pessoas → watchlist: **Schalkwyk saiu p/ Meta Superintelligence (jun/25)**
  — vigiar publicações; Dan Lyth (Parler-TTS: anotação sintética de estilo =
  pista da receita de dados); Eskimez (E2-TTS/EmoCtrl); Sanabria (multi-sotaque).
- Lacunas p/ OSINT r2: diff completo dos forks, ASR de produção, VAD client vs
  server, "curiosity engine".
- Delta de código nosso: src/duplex TODO v0.2 = re-síntese incremental
  (sentença-a-sentença com pivô), não TTS por turno.

### 2026-06-10 — rodada 2 (dossiês 82-85): forks/emoção, orquestradores, CSM prática, bases

- **Sesame r2 (82):** sglang = 7 commits próprios; o decisivo é 1 linha do CTO
  (abort 1s→**20ms** = a digital do barge-in/pivô) + logit_bias + OUTLINES
  (JSON constrainado). faster-whisper-plus/silero = espelhos puros. silentcipher
  no csm = 3 linhas no generate(), fork com MPS (roda no M2) → **adotar no
  Maya-BR v0**. Emoção da Sesame = implícita por áudio-contexto (sem tags).
  Schalkwyk = Voice Lead do MSL (PlayAI+WaveForms sob ele), zero publicações.
  **r3: ouvir podcast a16z c/ Ankit Kumar na íntegra (YouTube bTcpNQH8ViQ).**
- **Orquestradores (83):** decisão = manter src/duplex no v0.2 + **smart-turn
  v3 (BSD-2)** no turn_engine + espelhar interfaces do Pipecat; Pipecat = v0.3+
  (transporte). LiveKit fora (licença dos pesos), vocode morto, TEN não auditado.
  Nenhum framework tem TTS-com-estado nem re-síntese incremental.
- **CSM prática (84):** receita georgiana = referência (35h LIMPAS, r=64/α=64,
  LR 5e-5, ~14 ep → CER 2,8%); lições: dado limpo > horas; fillers SEMPRE
  transcritos (finlandês cospe "Ööö"); inglês sai com sotaque da língua nova.
  ZERO finetunes pt/es — somos os primeiros. Multi-turno: suportado no chat
  template HF (sem mask por turno; csm-mlx tem `--mask-speaker-ids` nativo) —
  **ablação contexto-vs-sem = contribuição inédita nossa**. Elise DMCA
  confirmado; emoção agora: laions_got_talent (Apache, proveniência OpenAI*) +
  auto-anotação (emotion2vec/BUD-E-Whisper). Tags = texto puro no tokenizer
  Llama → usar conjunto Orpheus exato, inline, dezenas-centenas por tag.
  **csm-mlx no M2: finetune LoRA comprovado (M2 Air 16GB, 44min/época)** —
  bancada de smoke local antes do Colab. Marvis-TTS prova CSM-style on-device.
- **Bases (85):** **CML-TTS pt = 67,95h train (CC-BY)** — o "1.100h" era o
  alemão; pool CC-clean lido recalibrado ~430h. **BRSpeechMOS: dataset+código
  públicos, SEM checkpoint/licença → treinar o nosso** (Whisper-Small, LCC~0,70).
  NURC tag-MIT frágil (upstream NC-ND explícito). CETUC: nem o texto pode.
  SOTAQUE: CDLA ok mas vazio. **AKCIT = R$80M MCTI/Embrapii, grupo de fala =
  Frederico**; BRSpeech-DF (459k amostras, CC-BY) serve pro nosso anti-spoof;
  parceria via porta Embrapii/Sebrae-GO. Monitorar org AKCIT-Speech no HF
  (migração do BRSpeech-TTS = onde a licença destravaria).

### 2026-06-10 — noite: podcast a16z c/ Ankit Kumar digerido (dossiê 86 + transcript integral)

CTO da Sesame confirma: cascata ASR-incremental→LLM(texto)→CSM; LLM cego pra
paralinguística (lacuna admitida); sub-500ms = systems engineering; "even the
1B is very good" (escala = long-tail, não naturalidade); turn-taking =
heurísticas fora do modelo; evals = pronúncia + arena + win-rate vs humano
(WER saturado); roadmap full-duplex ~100ms citando Moshi. Validações diretas:
CSM-1B suficiente p/ Trilha A; nossa cascata = a arquitetura da Maya viral;
Trilha B endossada pelo próprio CTO. Transcript: research/dossier-2026-06/
transcripts/a16z-ankit-kumar-2025-03.txt.

### 2026-06-10 — madrugada: primeiro eval local (gate F0.5 r1) — eval/results/2026-06-10-zeroshot-local-m2.md

CSM zero-shot no M2: timbre 0.973 (teto) MAS pt embolado (WER 47-100%) —
finetune é o desbloqueio (como previsto). 4-bit precisa ≥3 âncoras
(0.618→0.973). Pocket = WER 7% mas voz genérica. Finetune local de 48min
rodando (transcrição→LoRA r16→amostras).

### 2026-06-10 — madrugada: OSINT competitivo (dossiês 87-90 + 87-SINTESE)

ElevenLabs deep + Inworld/Voice.ai + Google/bigtech + arquitetura de agentes
ao vivo. Fatos-chave: nem o ElevenLabs entrega full-duplex em produção
(cascading; expressivo v3 não streama × Flash rápido sem emoção = NOSSO gap-
alvo continua aberto); CEO da ElevenLabs: o moat é data/labeling pipeline, não
arquitetura; latência de mercado 2026 = p50 v2v ~800ms (>800 = "Zoom moment"),
SOTA produção ~465-620ms; sotaque na big tech = prompt sem intensidade (pt-BR
regional NÃO confirmado em fonte primária — ameaça média); Inworld: GRPO com
reward composto WER+spk-sim+DNSMOS (adotar na Trilha A/B); métodos de latência
(SoundStorm non-AR, VALL-E 2 grouped-code, overlap SpeechLM↔decoder).
**IMPLEMENTADO na hora (ações #1 e #2 do dossiê 90):** smart-turn v3.2 (BSD-2,
ONNX 8MB) como 2º estágio do turn_engine — endpointing semântico em ~98ms CPU
no M2 (frase completa do Pedro → prob 0.74 ✓), silêncio curto 280ms + fallback
duro; e truncamento de contexto pós-barge-in (LLM history + CSM context cortados
no ponto OUVIDO — padrão item.truncate/AgentResponseCorrection). Sondas de
pronúncia pt-BR criadas (eval/benchmark_pronuncia_ptbr.jsonl, 27 itens).
Achados de produto/preço isolados na §5 da síntese (não poluir startup mode).

Next scan: 2026-06-17 (weekly). Next hard review: **2026-07-17**.
