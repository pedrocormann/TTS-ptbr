# ROADMAP — o documento único (compilado 02/jul/2026)

> **Fonte de verdade do projeto.** Compila: revisão geral + playbook Sesame + transcrição
> prosódica + pesquisa verificada (dados, GPU, competitivo, pesquisadores BR). Os deep-dives
> continuam vivos como apêndices (índice no fim). Renderizado na aba **Trilha** do cockpit.

## O norte (1 parágrafo)

Voz conversacional pt-BR **carioca** com a naturalidade percebida da Maya/Sesame, servida a
custo fixo pro nicho cultural (wedge Sesc). A Maya é uma **cascata orquestrada** sobre um
CSM público — o fosso deles é dado conversacional + eval que prevê felicidade + engenharia de
latência, e os três são replicáveis em escala de nicho. Nosso diferencial não tem atalho:
**a única fonte de carioca no mundo somos nós gravando.**

## Onde estamos (placar de 02/jul, sem maquiagem)

- **Dado próprio**: 259 clipes / 24,4 min limpos (Pedro). João/Guilherme: 0h, consentimento pendente.
- **Treinos**: 2 rodadas + grid de 26 arms (~$73). Voz clona (timbre 6,5/10); 95% "não soa carioca";
  eval humana do Treino 2 = n0 (gate da semana).
- **Pipeline**: gravar→transcrever(prosódico)→curar→exportar→treinar **fecha ponta-a-ponta** (02/jul).
- **Nota geral vs Maya: 2,8/10.** O que sobe essa nota: horas gravadas + eval girando, não GPU.

## A ciência que decide por nós (verificada em fonte primária)

| # | Aprendizado | Implicação | Fonte |
|---|---|---|---|
| 1 | **Identidade de voz satura ~2-3h**; ninguém usa >3h/voz | M1 = 5h bem compostas, não 20h | ElevenLabs PVC docs · Azure CNV · XTTS (arXiv:2406.04904) |
| 2 | **Horas grandes pertencem à LÍNGUA**: 35h=inteligível · 90-150h=funcional · ~330h=utilizável · 2.386h=SOTA aberto | CPT 1.000h+ é o passo certo (~$200) | CSM-georgiano (HF NMikka) · F5 polonês #1168 · firstpixel/F5-pt-br · XTTS paper |
| 3 | **Segmentação/pontuação PROSÓDICA melhora TTS**: WER 0,43 vs 0,50 (p<0,01), F0-RMSE 39 vs 44 Hz | Implementado (default na coleta) + arm A/B r3_pedro_pros | Grupo Aluísio, BRACIS 2025 (arXiv:2511.14779) |
| 4 | **Transcrição "limpa demais" NÃO CONVERGE** (CER 60% vs 15% verbatim) | Fillers ficam no texto, sempre | DisfluencySpeech (arXiv:2406.08820) |
| 5 | **Silêncio ≥300ms ≈ todas as heurísticas** de fronteira prosódica (Δ0-3%) | Heurística defensável; teto PSST **realizado → SAMPA** (Whisper-IU pt-BR, F1 0,73-0,80; Galdino coautor) | PROPOR 2024 · **SAMPA (arXiv 2607.07408, jul/26)** |
| 6 | **O "robótico" é mensurável**: menos pausa + ritmo achatado + sílaba nuclear 280→150ms | Scorecard roda a cada treino ($0) | Galdino ENIAC 2024 + nosso baseline (eval/prosody_baseline) |
| 7 | **Curadoria de transcrição não melhora WER e ACHATA prosódia** | Curar só estilo/emoção/lixo/números | Nosso grid 26 arms + baseline de prosódia |
| 8 | **GPU não é gargalo**: programa completo ~$330-480 | Não otimizar centavos; não desperdiçar runs | Preços 02/jul verificados + throughput medido (50h-áudio/H100-h) |
| 9 | **Maya = cascata** (ASR→LLM→CSM audio-conditioned); mágica = orquestração (abort 20ms, re-síntese) | Trilha M: medir a cascata é pilar, não detalhe | CTO Sesame no a16z · PCWorld (stack Gemma4+CSM) |
| 10 | **WER saturou como métrica** (a própria Sesame diz); eval que importa prevê felicidade; **MOS-preditores automáticos (UTMOS/NISQA/DNSMOS) são cegos a prosódia + viés de F0** → régua própria, não MOS; **seleção por ASR + eval na MESMA família de ASR infla WER** (self-bias de linhagem) | Grids ≤ capacidade de escuta (~top-4/noite) · **regra: filtro por ASR (anti-erosão/DPO/BoN) usa família DISJUNTA da eval** | Blog Sesame · vaga Research Eng 17/jun · **arXiv 2606.19951 (dossiê 84)** · **2607.08256 (dossiê 87)** |
| 11 | **Filler: marcar a LOCALIZAÇÃO basta** — modelo escolhe o tipo melhor que anotador | Não micro-gerenciar taxonomia de filler | Székely SSW'19 |
| 12 | **DPO áudio: treino barato, geração cara** (15k pares = 7 A100-h); **DPO-humano de prosódia ANTES de GRPO** (GRPO sobre WER/spk-sim colapsa a prosódia em fala monótona) | Só depois de eval girando (pares humanos); GRPO só escopado a número/#3, guardado | Tango 2 (2404.09956) · No-Verifiable-Reward (2509.18531) |
| 13 | **Spine não é mais só CSM**: **Qwen3-TTS** (Apache, pt-nativo, 12.5Hz como o Mimi) ataca o gringo na raiz; **decoder FM chunk-wise** melhora #1/#2 sem retreinar o LM; **deploy = engenharia** (CUDA-graph 2× + flush-trick −300ms + truncar-contexto-ouvido, tudo no Mac); dado sintético só com DPO anti-erosão. *Linhagem evoluiu (ago/26): Qwen-Audio-3.0-TTS fechado, 12.5Hz FSQ + LM+FM por hidden-states — WATCH até pesos abrirem* | **Bake-off de spine** (pode dissolver o Estágio A) + arms em `runpod/experiments.py`; deploy ADOPT no `src/duplex`; **accent-scorecard** já no `eval/` | Sweep arch-addons — **dossiê 85 + arch-map/** · **2607.23938 (dossiê 87)** |

## O plano — M0.5 → M3

| Marco | O quê | Gates | GPU |
|---|---|---|---|
| **M0.5 · AGORA (2 sem)** | Flywheel MEDIDO: consentimentos assinados → 1ª sessão dirigida dos 3 → eval humana T2 (top-4) → maya_parity → baseline Chatterbox v3 pt-BR (MIT) cega no rate_app | 1h nova no disco · taxa h/semana medida · T2 fora do n=0 | $0 |
| **M1 · ~1 mês** | 5h Pedro bem compostas (2h lido c/ números+siglas · 2h conversa estéreo · 1h estilos) + CPT base-pt-v2 1.000h + rodada 3 (12 arms: solo/mix/prosódico, ≤ capacidade de escuta) + cascata MEDIDA e2e | WER 18→10-13% · números ok · nota 3,1→3,5 | ~$285 |
| **M2 · 3-4 meses** | 15h/voz ×3 (40% conversa estéreo, 25% emoção dirigida ≥30min/estilo, 10% números, 5% code-switching) + treino com TURNOS + 1º DPO + demo web + conversa Sesc | "soa carioca" 5%→40-60% em painel cego de 5 · 4/5 em frases boas | ~$100 |
| **M3 · 6+ meses** | 40h elenco + base madura + app + watermark (silentcipher) em release | CMOS cego vs ElevenLabs pt-BR · voz vendável no nicho | ~$100-640 (se TAGARELA CPT) |

**Cadência que sustenta tudo**: 30 min/dia gravando (dirigido) · 20 min/dia ouvindo (rate_app) ·
1 min/dia no placar do export · grids nunca maiores que a escuta.

## Playbook Sesame → nossa escala (resumo; completo em ROADMAP-SESAME.md)

P1 base de áudio (CPT $150-230) · P2 personas (3-5h/voz, LoRA r64) · P3 **conversa multi-turno**
(o coração — flywheel estéreo + prosódica + turnos) · P4 cascata orquestrada (medir!) · P5 eval
que prevê felicidade · P6 data engine c/ proveniência · P7 DPO em áudio · P8 produto (Voz Lab
pronto; wedge Sesc) · P9 janela pt-BR (aberta, correndo) · P10 cadência de 1 pessoa.

## Pesquisadores BR — créditos, macetes e ganchos (completo em dossiê 80/82)

| Quem | O macete que levamos | Estado |
|---|---|---|
| **Sandra Aluísio, Julio Galdino, Gustavo Araújo, Flaviane Svartman** (NILC/ICMC-USP, TaRSila) | Pontuação/segmentação prosódica (IMPLEMENTADA) · silêncio 300ms · fillers NURC · scorecard do robótico · F0-RMSE segmentado · EyetrackingMOS · **PSST-pt publicado = SAMPA (arXiv 2607.07408, Galdino coautor)** | e-mail rascunhado — **gancho SAMPA: rodar no nosso carioca (gap SP-only deles)** |
| **Frederico Oliveira** (UFMT/AKCIT-UFG) | TAGARELA 8.972h com **rótulo de dialeto** → minerar subset carioca · classificador de sotaque · 2.800h clean TTS | e-mail rascunhado (troca: nossa eval carioca) |
| **Edresson Casanova** (NVIDIA) | YourTTS <1min clone · XTTS 10min⇒SECS 0,72 · pt precisa ~2.400h pra SOTA · Koel-TTS/NanoCodec ≈ nosso stack | referência de receita; responde a comunidade |
| **Arnaldo Candido Jr** (UNESP) | Playbook 2026 de **fine-tuning emocional pt-BR com poucos dados** (~$5 de GPU pra replicar) | replicar → e-mail com resultado |
| **AKCIT/CEIA-UFG** (Anderson Soares) | Caminho formal EMBRAPII · BIPA: G2P com dialeto-Rio (se fonema reabrir) | via Frederico |
| **FalaBrasil** (UFPA) | UFPAlign (alinhamento forçado pt-BR) — se precisarmos de timestamps melhores que Whisper | ferramenta na prateleira |

## O que está morto (não re-litigar)

G2P (WER 46-89%) · curadoria-como-alavanca-de-WER · Moshi-como-aposta-nº1 (cascata é a
arquitetura; reavaliar com 50h+ estéreo) · FreeSVC até eval girar · voz F contratada no MVP ·
5 sub-sotaques · MOS 4.0 como métrica viva (é norte, não gate).

## Índice de deep-dives

- [REVISAO-2026-07-02.md](REVISAO-2026-07-02.md) — a revisão completa (o que erramos, metas detalhadas, riscos)
- [ROADMAP-SESAME.md](ROADMAP-SESAME.md) — os 10 pilares com evidência OSINT
- [TRANSCRICAO-PROSODICA.md](TRANSCRICAO-PROSODICA.md) — pesquisa + implementação da abordagem Aluísio
- [RASCUNHOS-CONTATOS.md](RASCUNHOS-CONTATOS.md) — e-mails prontos (Frederico, grupo USP)
- `research/dossier-2026-07/` — dossiês verificados: 12-competitivo · 20-escala-dados · 21-transcrição-global · 40-custos-GPU · 80-pesquisadores-BR · 81-sesame · 82-aluisio · **83-SAMPA/PSST-pt** · **84-triagem-papers-13jul** · **85-arquiteturas-addons** · **86-triagem-tabs** · **87-triagem-scholar-ago03** · 91-voice-ui
- **[`85-arquiteturas-addons.md`](../research/dossier-2026-07/85-arquiteturas-addons.md)** — MAPA VIVO (11 frentes): tabela-mestra ADOPT/TEST/WATCH/SKIP + **matriz de experimentos** (arms toggleáveis). Deep-dives em `research/dossier-2026-07/arch-map/`.
- `research/papers/` — PDFs + digests completos dos papers triados (lote 13/jul + SAMPA)
- **Código de experimentos:** `runpod/experiments.py` (ARMS + `SWEEP_GUARDRAILS`) · `eval/accent_scorecard.py` (gap #1 objetivo)
- `runpod/RUNBOOK-rodada3.md` — a próxima rodada de treino (12 arms, custos, go/no-go)
- `eval/prosody_baseline_2026-07-02.md` + `eval/prosodic_punct_report.md` — os primeiros números de prosódia
