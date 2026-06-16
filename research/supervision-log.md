# Supervisão overnight — Head of ML × Head of Data Science (alternando 10min)

Início: 2026-06-16 ~02:55 (UTC). Noite focada no RunPod (tag_base → mix_base → cml_long → Stage B).
Cada ciclo: snapshot do pod → agente (persona alternada) investiga → achados → ações aplicadas.

| ciclo | hora | persona | achados-chave | ação |
|---|---|---|---|---|
| 1 | 03:00 UTC | Head of ML | modelo BALBUCIA (10/14 áudios colam no teto 30s, WER 116% = nível-ruído); recipe subdimensionada pro time-cap (LR 2e-4 baixo + cosine de 24750 steps truncado em 660); fix de shape validado (TAGARELA/MLS 0 mismatch); grad_norm folgado 2.6 | **REPLANO**: LR 2e-4→5e-4, 60min→180min, runs longos CML+TAGARELA @ agressivo; eval teto 375→160 tokens + métrica "aprendeu a parar". Relançado. |
| 2 | 03:25 UTC | Head of DS | **DESAFIOU o ML e acertou**: "116%" era artefato (mediana real **70%**; modelo JÁ fala pt — emp-01/sad-01 = 0% WER; problema = não PARA, enche 30s de lixo); WER favorece CML mas **TAGARELA = registro certo** do produto (CML = leitura de livro séc.XIX); eval mudou no meio (não comparável); **voz do Pedro = mono-prosódia, 1 sessão, 0 variação emocional**; n=14 + ref-voz confundida = ±40pp ruído | eval salva **por-frase + mediana** (aplicado); manter cml_long (melhora pt de verdade); decisão de fonte = **de OUVIDO** não WER; **hipótese forte: zero-pad 12s ensina "encher 12s" = causa do não-parar**; FLAG p/ Pedro: gravar **emoções variadas** pro dataset de voz real |
