# Linhas de pesquisa — workstreams que ACUMULAM (re-desenho 21/jun/2026)

5 frentes de P&D que vão somando checkpoint/dataset/métrica/receita e melhoram a cada treino+teste. **Fase atual: COLETA** (treino pausado até volume). Estratégia: **construir algo muito bom primeiro, mostrar pros acadêmicos depois** — usar só o que é aberto (CC-BY/MIT/CC0).

## F1 — Base-PT / Língua (CPT como ATIVO reusável, não evento)
- **Objetivo:** Resolver o viés-inglês do CSM-1B com um checkpoint base-pt-vN que TODO finetune de voz herda — hoje cada treino re-aprende pt do zero.
- **Acumula:** checkpoint base-pt-vN (peso) + dataset_card.jsonl versionado do mix CPT (só licença limpa: CML/MLS/CV-CC0/Granary-CC-BY3). Cada versão registra horas REAIS contadas do disco, WER pós-CPT, hash do mix.
- **Métrica:** WER de leitura (Whisper-large-v3) em held-out fixo de 50 frases pt-BR + perda de val no codebook-0. Baseline provado: CML levou WER 116→21. Meta próxima iteração: WER<15% mantendo paridade de timbre.
- **1º passo:** Resolver a divergência 16x das horas do CML-TTS (~1.100h dossiê vs ~68h contagem) em OpenSLR-146/arXiv 2306.10097 ANTES de orçar o próximo CPT — o dataset_card carrega a hora REAL do disco, não a do paper.

## F2 — Voz & Sotaque Carioca (o moat; flywheel MEDIDO, não estimado)
- **Objetivo:** Fechar o gap #1 (sotaque gringo, 'soa nativo' ~2.8/5 em TODOS). Única fonte carioca commercial-safe = gravação dirigida própria (Pedro→João→Guilherme).
- **Acumula:** corpus-semente próprio (~0.4h hoje) crescendo via flywheel diário + LoRAs de voz empilhados sobre base-pt-vN, cada gravação com consentimento LGPD assinado (compliance-by-design PL 1460/2026).
- **Métrica:** Taxa REAL do flywheel em h/semana (NUNCA medida — toda ETA de 2.5-12 meses é fantasia até medir 2 semanas reais) + score perceptual 'soa nativo' cego no rate_app. Realismo: ~0.4h vs 10-30h/voz nível-Maya.
- **1º passo:** Medir 2 semanas reais do flywheel (h/semana líquidas) usando o gravador sincronizado multi-sala já feito — mata as ETAs-fantasia e ancora todo o planejamento. Em paralelo: formatar dado+inferência como TURNOS (ROI #1, muda formato não modelo).

## F3 — Prosódia & Expressividade (de robótica a contextual)
- **Objetivo:** Atacar prosódia robótica (3.0/10, 18x marcada, NENHUM método rodado ainda). O gap residual vs Maya é prosódia conversacional dependente de CONTEXTO, não timbre frase-a-frase (timbre já em 6.5).
- **Acumula:** receita de rotulagem de estilo-por-contexto (padrão LibriQuote CC-BY: verbo de fala + advérbio → pseudo-label) aplicada ao corpus próprio + trilha de DPO usando o rate_app como gerador de pares A/B.
- **Métrica:** instrumento de prosódia da Aluísio/USP (F0-RMSE segmentado + scorecard objetiva do 'robótico') + CMOS cego no rate_app. Hoje n=0 — o PRIMEIRO número já é progresso.
- **1º passo:** Rodar o instrumento Aluísio/USP (F0-RMSE segmentado) no output do Treino 1/Treino 2 pra ter o 1º número objetivo de 'robótico' — baseline antes de qualquer método de prosódia.

## F4 — Eval & Instrumentação (o compasso; sem ele todo sprint repete o nulo)
- **Objetivo:** Sem eval perceptual COM contexto otimizamos WER e ficamos cegos ao gringo. Treino 2 tem n=0 avaliação humana (ratings.jsonl = 42 linhas, todas do Treino 1) — não dá pra eleger vencedor por sotaque.
- **Acumula:** rate_app/trilha_map.json como cockpit versionado (FEEDBACK.md schema v1): erro objetivo (wer_ops) + perceptual (markers {t,tag,sev,note} com taxonomia carioca: R /ʁ/, vogal nasal, ti/di palatal, S coda, L coda /w/). Cada modelo vira bloco Treino N — substrato pros futuros agentes de correção.
- **Métrica:** cobertura de feedback (frases × raters anotados) + painel maya_gap (6 eixos) no trilha_map. Próximo salto: MUSHRA/CMOS cego + BRSpeechMOS pt-BR.
- **1º passo:** Carregar o clean-subset do TAGARELA como eval-set conversacional FIXO no rate_app (uso legal do NC) + coletar a 1ª rodada de eval humana do Treino 2 pra sair do n=0.

## F5 — Augmentação & Dados-Baratos (esticar o pouco com licença limpa)
- **Objetivo:** Enquanto o flywheel não acumula volume (gargalo existencial), extrair o máximo de cada hora gravada e de cada fonte CC-limpa, sem NUNCA tocar fonte suja (filme/novela/dublagem = veto total).
- **Acumula:** pipeline de coleta-própria reusável (receita TAGARELA replicada com pyannote+Vocos+Whisper-FT, componentes MIT/Apache) apontado pra fontes LEGAIS: Câmara ao-vivo (CC-BY, método ParlaSpeech) + augmentação de timbre via FreeSVC/Chatterbox (MIT).
- **Métrica:** horas-líquidas-limpas adicionadas/mês ao mix, com WER pós-filtro (dual-ASR agreement) por fonte. Distingue ASR-grade de TTS-grade (curadoria manual foi REFUTADA como alavanca: descartou 0.5%, não os 40-60% orçados).
- **1º passo:** Apontar o pipeline replicado pra Câmara dos Deputados (CC-BY, 2-party espontâneo em escala): download→VAD→ParlaSpeech-align→DNSMOS→tier T0 — 1ª fonte espontânea licenciada operacionalizada.
