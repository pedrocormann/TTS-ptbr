# VERIFICAÇÃO (verificador adversarial — 02/jul/2026)

Método: WebFetch nas fontes citadas + APIs brutas (iTunes lookup, Ashby JSON, GitHub API, RSS Apple) + 2 buscas independentes. Vereditos dos 8 claims mais load-bearing:

**1. "Nenhum blog post, modelo, paper ou rodada nova na janela 15/jun–02/jul" — CONFIRMADO.**
Checado direto: sesame.com/blog (últimos posts 27/mai/2026 ✓), sesame.com/research (só fev/2025 ✓), HF org (só csm-1b, update 01/dez/2025, 310k downloads/2.4k likes ✓), GitHub csm (último push 27/mai/2025 ✓); busca independente por notícias de jun/2026 não retornou nenhum anúncio novo.

**2. "App English-only, iOS 18+, 4.9/812, v29 ~30/jun" — CONFIRMADO** (via API iTunes lookup, dado bruto: version 29.0, release 2026-06-30, rating 4.92, 812 ratings, languageCodes ['EN'], minOS 18.0 — bate exatamente).
*Ressalva embutida:* as datas de **v27 (16/jun) e v28 (23/jun)** não são verificáveis pela API (só mostra a versão atual) → **PLAUSÍVEL** — aritmética de cadência semanal fecha com o 30/jun confirmado, mas sem fonte direta.

**3. "Vagas novas na janela: Research Engineer 17/jun (eval pipelines) + Data Engineer ML 23/jun; 26 vagas totais" — CONFIRMADO.**
JSON bruto da Ashby: 26 vagas ✓; "Research Engineer" publicada 2026-06-17 ✓ com quotes verbatim ("own evaluation pipelines... offline and live evals that keep our speech and multimodal models honest in production", "privacy-aware dataset curation", "metrics... that actually predict user happiness"); Data Engineer ML 2026-06-23 ✓ ("conversations, voice, sensor signals, and product telemetry", versioning/lineage, Airflow/Dagster/Prefect, Ray/Spark, GKE/EKS, vector DBs); Sr Executive Assistant 29/jun ✓. *Nota menor:* o título real é "Research Engineer", sem o "(Machine Learning)" do relatório.

**4. "Stack = Google Gemma 4 (LLM) + CSM-1B custom (voz)" — PLAUSÍVEL.**
A PCWorld (03/jun/2026) diz literalmente isso ✓, mas é **fonte única** para o Gemma 4 — busca independente só reencontra a própria PCWorld; nenhuma confirmação oficial da Sesame. A parte CSM-1B é multi-confirmada (HF, the-decoder, GitHub). Tratar "Gemma 4" como reportagem de um veículo, não fato estabelecido.

**5. "Reviews mostram FR/ES funcionando + reclamações de guardrails" — CONFIRMADO.**
RSS oficial da Apple, verificado review a review: "Multi lingual — Spoke in French... answered perfectly" (24/jun, 5★) ✓; "Studying Spanish" com Simone (20/jun) ✓; 1★ de 29/jun com "guardrails set so narrow" ✓; "Love it but less Guardrails" (25/jun) ✓; bug de microfone (29/jun) ✓. Zero menção a português nos 50 reviews mais recentes ✓. *Nota:* "presumivelmente com sotaque/prosódia de inglês" é inferência do relatório, não está nas fontes.

**6. "Android ainda waitlist-only" — CONFIRMADO.** Página verificada em 02/jul: "coming soon", waitlist, Android 8.0+, Beta Testing Agreement ✓.

**7. "Lançamento iOS 28/mai/2026, 39 países, grátis 'por enquanto', 4 agentes; sem rodada desde Series B $250M out/2025" — CONFIRMADO.**
TechCrunch 28/mai confirma tudo (39 países, grátis, Maya/Miles/Simone/Charlie, 1M+ no preview) ✓; busca independente por funding não acha nada pós-out/2025 (PitchBook/a16z/Sacra todos param na Series B) ✓.

**8. Implicação "Sesame não está em expansão de idiomas → nicho pt-BR aberto" — CONFIRMADO com ressalva importante.**
Os fatos da janela sustentam (English-only, zero vaga de localization, zero anúncio). **Porém** a página de research (fev/2025) declara oficialmente a intenção de "expand language support to over 20 languages" — a expansão multilíngue é roadmap público declarado, só não está sendo executada visivelmente agora. O nicho está aberto *hoje*; não tratar como garantia estrutural.

**Bônus verificado:** a lista de forks do GitHub confere integralmente via API (torchtune push dez/2025 ✓, moshi ago/2025 ✓, ClearerVoice-Studio ago/2025 ✓, sglang, torchtitan, silentcipher, whisperX, silero-vad, ultralytics ✓).

**Balanço adversarial:** nenhum claim refutado; o relatório é fiel às fontes. Os dois pontos mais frágeis para decisão: (a) "Gemma 4" tem fonte única de imprensa; (b) a conclusão "não em expansão de idiomas" ignora que 20+ idiomas é meta oficial publicada desde fev/2025 — o relógio do nicho pt-BR está correndo, não parado.

---

# Sesame AI — varredura 2026-06-15 → 2026-07-02

## Resumo executivo
Período quieto em anúncios públicos: **nenhum blog post, modelo, paper ou rodada nova** no intervalo. O que se move está nos bastidores: 3 updates do app iOS (v27, v28, v29), Android ainda em waitlist, e **2 vagas novas de ML publicadas dentro da janela** que revelam a direção (eval pipelines em produção, data engineering multimodal). Nenhum sinal de pt-BR ou multilíngue oficial — mas reviews de usuários confirmam que os agentes já conversam em francês/espanhol (via LLM Gemma 4), com App Store listando "Languages: English" apenas.

---

## (1) App iOS/Android — novidades

**Updates do app na janela** (fonte: [App Store — Sesame: Personal Agents](https://apps.apple.com/us/app/sesame-personal-agents/id6756329076)):
- **v27** (16/jun/2026), **v28** (23/jun/2026), **v29** (~30/jun/2026) — release notes genéricas ("Features and bug fixes"). Cadência semanal de release.
- Rating atual: **4.9/5 com ~812 avaliações** (US). Requer iOS 18+. Idioma listado: **English only**.

**Reviews recentes de usuários** (via feed RSS oficial da Apple, 20-29/jun/2026):
- Elogios consistentes: "voz mais realista do mercado", uso como terapia/companhia e **estudo de idiomas** ("Studying Spanish" com a agente Simone, 20/jun; "Multi lingual — Spoke in French... answered perfectly", 24/jun).
- Reclamações recorrentes: **guardrails restritivos demais** ("walk on eggshells", review 1★ de 29/jun; pedido de "less guardrails" com verificação de idade, 25/jun), risadas fora de hora da Maya, bugs de microfone.

**Android**: ainda **waitlist-only** ("coming soon", requer Android 8.0+, Beta Testing Agreement) — [sesame.com/android-preview](https://www.sesame.com/android-preview). Nada lançado na janela.

**Contexto imediatamente anterior à janela** (relevante):
- Lançamento público iOS em 39 países, 28/mai/2026, grátis "por enquanto"; 4 agentes (Maya, Miles, **Simone, Charlie**); busca paralela enquanto fala, search cards, notes, text mode, incognito mode; agentes com "ação em nome do usuário" no roadmap — [TechCrunch, 28/mai/2026](https://techcrunch.com/2026/05/28/sesame-the-conversational-ai-startup-from-oculus-founders-launches-its-ios-app/)
- Review PCWorld (03/jun/2026, 12 dias antes da janela): **revela stack = Google Gemma 4 (LLM) + CSM-1B custom (voz)**; melhor voice app testado; preocupações éticas com antropomorfização — [PCWorld](https://www.pcworld.com/article/3151873/sesame-ai-voice-app-is-the-best-ive-tested-thats-what-worries-me.html)

Números de downloads/usuários na janela: **nada novo encontrado** (último dado público: 1M+ usuários no research preview).

## (2) Release novo de modelo/pesquisa/blog

**Nada novo encontrado.**
- Blog oficial: últimos posts são "Voice your curiosity" e "Getting started", ambos de **27/mai/2026** — [sesame.com/blog](https://www.sesame.com/blog). Nada em jun/jul.
- Página de research: continua só com "Conversational speech generation" (27/fev/2025) — [sesame.com/research](https://www.sesame.com/research)
- HuggingFace: org [sesame](https://huggingface.co/sesame) segue com **apenas csm-1b** (last update 01/dez/2025; 310k downloads, 2.4k likes). Nenhum modelo novo.
- GitHub [SesameAILabs](https://github.com/SesameAILabs/csm): repo csm sem push desde 27/mai/2025. Nenhuma atividade pública na janela. **Bônus de inteligência**: os forks da org revelam o stack interno — torchtune (post-training, dez/2025), torchtitan (treino em escala), sglang (serving), moshi (Kyutai, ago/2025), silentcipher (watermarking), whisperX/faster-whisper-plus/silero-vad (pipeline de dados), ClearerVoice-Studio (enhancement/separação — relevante pra limpeza de dataset), ultralytics YOLO11 (visão → óculos).

## (3) Entrevistas/podcasts recentes do time

**Nada novo encontrado na janela.** A entrevista mais recente e substancial continua sendo a do CTO Ankit Kumar no podcast [AI + a16z](https://a16z.com/podcast/building-the-next-generation-of-conversational-ai/) (mar/2025 — full-duplex, multimodal, otimização de latência). Nenhum podcast/entrevista de Iribe, Mitchell ou Ankit encontrado entre 15/jun e 02/jul/2026. Nenhum detalhe novo público sobre RL/DPO em áudio.

## (4) Vagas de emprego (sinal de direção)

**3 vagas novas publicadas DENTRO da janela** (fonte: [jobs.ashbyhq.com/sesame](https://jobs.ashbyhq.com/sesame), via API Ashby — 26 vagas abertas no total, todas presenciais SF/Taipei/Bellevue):

- **Research Engineer (Machine Learning)** — 17/jun/2026: "own evaluation pipelines — offline and live evals que mantêm nossos modelos de fala e multimodais honestos em produção"; "dataset curation versionada e privacy-aware"; "treinar e deployar modelos de voz SOTA"; PyTorch expert; "eval expert — métricas que realmente predizem felicidade do usuário". → Confirma a aposta deles em **eval como produto interno** (mesma tese do rate_app/scorecard de vocês).
- **Data Engineer, Machine Learning** — 23/jun/2026: pipelines para "conversas, voz, sinais de sensores e telemetria de produto"; dataset versioning/lineage; data labeling pipelines; menção a "dados de hardware/sensores em tempo real" (→ óculos). Stack citado: Airflow/Dagster/Prefect, Ray/Spark, GKE/EKS, vector DBs.
- **Senior Executive Assistant** — 29/jun/2026 (irrelevante tecnicamente).

Contexto pré-janela que reforça: **TPM, Data** (16/mar/2026) — liderar "coleta e anotação de dados de ÁUDIO", gerenciar vendors de labeling. O fosso continua sendo operação de dados, como já mapeado. Vagas de hardware (Supply Chain FATP 10/jun, Taipei CapEx, Lab Manager, Audio Systems) mostram os óculos 2027 andando pra manufatura.

## (5) Planos multilíngues / outros idiomas

**Nenhum anúncio oficial — nada novo encontrado.** Evidências na janela:
- App Store lista **"Languages: English"** apenas; nenhuma vaga de localization/multilingual entre as 26 abertas; nenhum blog/post sobre idiomas.
- Porém, reviews de jun/2026 mostram os agentes **funcionando em francês e espanhol na prática** (o Gemma 4 é multilíngue; a voz CSM responde, presumivelmente com sotaque/prosódia de inglês). Zero menção a português/pt-BR em qualquer fonte.
- Atenção: sites como sesameaivoice.org / aisesame.net que alegam "40+ idiomas" são **clones SEO não-oficiais** — descartar.

**Implicação pro projeto**: a janela de 15 dias confirma que o nicho pt-BR segue aberto; Sesame está focada em eval de produção, operação de dados e hardware — não em expansão de idiomas.

---

## Fontes (todas)
- https://apps.apple.com/us/app/sesame-personal-agents/id6756329076 (App Store, versões 16-30/jun/2026)
- https://itunes.apple.com/us/rss/customerreviews/id=6756329076/sortBy=mostRecent/json (reviews 20-29/jun/2026)
- https://www.sesame.com/android-preview (waitlist, acesso 02/jul/2026)
- https://www.sesame.com/blog (últimos posts 27/mai/2026)
- https://www.sesame.com/research (inalterada desde 27/fev/2025)
- https://jobs.ashbyhq.com/sesame + api.ashbyhq.com/posting-api/job-board/sesame (vagas 17/jun, 23/jun, 29/jun/2026)
- https://techcrunch.com/2026/05/28/sesame-the-conversational-ai-startup-from-oculus-founders-launches-its-ios-app/ (28/mai/2026)
- https://www.pcworld.com/article/3151873/sesame-ai-voice-app-is-the-best-ive-tested-thats-what-worries-me.html (03/jun/2026 — revela Gemma 4 + CSM-1B)
- https://huggingface.co/sesame (csm-1b, update 01/dez/2025)
- https://github.com/SesameAILabs/csm + api.github.com/orgs/SesameAILabs/repos (forks/atividade)
- https://a16z.com/podcast/building-the-next-generation-of-conversational-ai/ (Ankit Kumar, mar/2025 — nada mais novo)
- https://techcrunch.com/2025/10/21/sesame-the-conversational-ai-startup-from-oculus-founders-raises-250m-and-launches-beta/ (Series B out/2025 — sem rodada nova desde então)
- https://www.techmeme.com/251022/p5 (Techmeme Series B; nada de Sesame no Techmeme na janela jun/2026)
- https://research.contrary.com/company/sesame-ai (perfil/contexto)