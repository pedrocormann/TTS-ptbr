# Triagem de papers — lote 13/jul/2026 (9 PDFs)

> Lote que o Pedro salvou em ~/Downloads e mandou incorporar. Cada PDF foi lido na íntegra por um agente
> (workflow `tts-papers-triage`), com digest completo em **`research/papers/<id>.md`** e o PDF em
> **`research/papers/<id>.pdf`**. (O SAMPA, arXiv 2607.07408, também foi movido pra `research/papers/`;
> ele tem dossiê próprio: [83](83-sampa-psst-pt-verificado.md).)
>
> **Veredito do lote — LENTE CORRIGIDA (13/jul, feedback do Pedro: avaliar por ARQUITETURA/ADD-ON, não por idioma; ver [[feedback-arquitetura-nao-idioma]]).**
> Idioma do paper **não** é filtro: pt-BR é nosso problema de DADO/saída, não de arquitetura — o cardápio de
> arquiteturas e add-ons é global e o método transfere mesmo com demo em inglês/chinês. Reavaliados por mérito
> de método pra **treino + deploy** (fit ao stack: CSM AR codec-LM / Moshi full-duplex / LoRA-CPT / baixa latência):
>
> - **Add-ons de treino/deploy mais fortes (o ouro do lote por este critério):** **DTRF** — emoção controlável
>   sobre backbone **CONGELADO** via adaptadores residuais (ControlNet acústico + adapter de duração) + **botão α
>   de intensidade**; é o padrão-premium de add-on "não retreina a base, pluga controle". **FineCombo** —
>   arquitetura de TTS controlável **referência + descrição de texto** via flow-matching (não desemaranha; espaço
>   de atributo unificado) + receita FFmpeg de dados. **FlowEdit** — patch de pronúncia **pós-deploy** com memória
>   associativa, sem esquecer, e o alerta quantificado de que **fine-tuning causa drift/esquecimento**.
> - **Add-ons de eval:** **MOS-discrepancy** (quais métricas confiar; MOS automático é cego a prosódia) +
>   **Phonology-eval** (accent-scorecard objetivo por-segmento).
> - **Pipeline de treino:** **Gradient-alignment** (forced-align universal, agnóstico de modelo). **Loss:** GAF-Flow
>   (ideia de loss perceptual auditivo).
> - **Arquiteturas superadas / off-task:** Myaamia (VITS/Glow/FastSpeech = geração anterior ao codec-LM; serve só
>   de âncora horas→MOS), Lampung (ASR; insight de transfer de línguas próximas p/ o Estágio A).
>
> A coluna "Tier" da tabela abaixo foi escrita com o viés antigo (penalizava idioma) — **ler junto com esta lente
> corrigida**. O gate de produto continua valendo, mas é sobre **DADOS/PESOS** de terceiros (ESD/MMS/F5-NC não
> embarcam); o **MÉTODO/arquitetura é livre** pra reimplementar no nosso stack.

## Tabela-resumo (ordenada por utilidade pra nós)

| # | Paper (id) | Venue | Tier | O que pode ter de bom pra gente | Onde quebra |
|---|---|---|---|---|---|
| 1 | **Human-Model Discrepancies in Speech Quality Assessment** (2606.19951) | preprint (LY Corp/Japão) | **MED⁺** | **Prova com número que MOS-preditores (UTMOS/UTMOSv2/NISQA/DNSMOS/SHEET) são CEGOS a erro de prosódia** (humano −1,84 MOS; modelos <0,1) e têm **viés de F0** (premiam voz mais grave; DNSMOS r=−0,79). → **valida nossa decisão** de construir scorecard próprio (F0-RMSE/IU) e alerta: não rankear checkpoints da voz do Pedro por MOS automático. Toolkit VERSA como opção. | Japonês pitch-accent (o número 1,84 não transfere; o **mecanismo** sim). É diagnóstico, não solução; nenhum instrumento pt-BR. |
| 2 | **Phonology-Informed Evaluation of Multilingual TTS** (2607.01965) | Interspeech 2026 (IIT Guwahati) | **MED⁺** | **O melhor template pra transformar "sotaque gringo" em métrica OBJETIVA por-segmento com direção do erro**: treina classificador na fala HUMANA (carioca) pra um contraste fonológico, aplica cross-domain na saída do CSM, mede quanto cai do lado errado. Contrastes-alvo do PB: médias abertas/fechadas /e/-/ɛ/,/o/-/ɔ/; redução de átona; chiado. Código no GitHub. | Assamês+harmonia ATR (nada do dado/modelo serve direto); é **eval, não treino**; segmental (não prosódico); exige gravar benchmark carioca humano + segmentar no Praat. |
| 3 | **FineCombo-TTS** (2606.19209) | Interspeech 2026 (Tsinghua/Tencent) | **MED** | **Receita FFmpeg de aumento de prosódia** (pitch±/speed± + combinações → pares "relativos" source→descrição→target), barata e **limpa de licença** (herda o áudio-base) — dá pra fabricar subset de controle de prosódia pt-BR/carioca a partir da voz do Pedro + corpora CC-BY, sem dado emocional atuado. Paradigma de controle **relativo** + métricas de aderência (Controlled Accuracy vs Uncontrolled Variation, Emotion-A/emotion2vec). | Inglês puro, sem pesos, arquitetura não-CSM (DAC/FACodec/CFM), 8×A100. O reaproveitável é a **receita de dados**, não o modelo. |
| 4 | **DTRF: Dual-Track Residual (emoção controlável)** (applsci-16-06613) | Applied Sciences/MDPI (CC-BY) | **MED** | **Receita de eval de emoção** (SER-UAR com avaliador **independente** do que condiciona — evita circularidade; MOS 3 eixos + projeção VAD + ASR-WER). **Âncora-neutra/resíduo relativo** (E_alvo−E_neutro) pra preservar timbre — construível **sem dado emocional pt-BR rotulado** via emotion2vec. Confirma com número que **emoção mexe em duração/ritmo** (angry −15%), reforçando prosódia-por-IU. Botão **α** = baseline SFT barato antes de RL. | Inglês/ESD, backbone Matcha (NAR, com duration predictor) — os **módulos não portam** pro CSM (AR/RVQ); só as ideias. Sem pesos liberados. |
| 5 | **FlowEdit: Lifelong Pronunciation Adaptation** (2606.20518) | preprint (UMaryland/Smallest AI) | **MED** | Conserta pronúncia de **nomes próprios/loanwords OOV** num TTS congelado sem retreinar. Insights: **full fine-tuning causa drift/esquecimento** (PER geral 4,1→15,3) e LoRA piora o geral → **canary pro nosso Estágio A/B**; **override de léxico (eSpeak) fica fraco** → mais um ponto contra o G2P/léxico parkeado; F0 subponderado no mel loss. Blueprint de "patch de pronúncia" pós-deploy pra marcas/nomes. | Flow-matching (não-CSM), escopo = nome próprio OOV (nem é nosso gap), zero release. |
| 6 | **Gradient-Based Speech-to-Text Alignment** (2607.06831) | preprint (RWTH Aachen/AppTek) | **MED** | Alinhamento forçado training-free pra **qualquer ASR** (CTC→speech-LLM). Confirma **MFA/WhisperX como baseline forte** pra prep de dados; nicho real: timings de palavra de ASR streaming/speech-LLM sem aligner nativo (único caso onde vence); grade fina (sub-20ms) útil pra timing em eval de F0/duração. | É ASR→texto (alinhamento), não TTS; **caro** (1 backward/token ~10×), pior que MFA em fala lida; só fronteira de palavra (não IU). Arquivar como referência. |
| 7 | **Lampung ASR via XLSR-Wav2Vec2** (1388-4978-1-PB) | J. Applied Data Sciences (CC-BY) | **LOW** | Único insight: **adaptar de línguas PRÓXIMAS > multilíngue genérico** (17% vs 34% WER) — ecoa nosso **Estágio A** (base pt-BR próxima antes do LoRA do Pedro). | ASR, não TTS; Lampung/indonésio (zero transfer p/ pt-BR); dado "upon request". |
| 8 | **Neural TTS for Myaamia** (2026.americasnlp-6.1) | AmericasNLP 2026 (ACL) | **LOW** | **Âncora de realismo horas→MOS**: 8h→3,05 · 17h→3,62 · 25h→3,69 (naturalidade) — reforça "dado é o gargalo, estamos LONGE da Maya". Kit de eval MCD/F0-RMSE/Duration-RMSE + MOS em 2 eixos (geral vs entonação/ritmo com nativo). | Língua indígena algonquiana (sem transfer), não-conversacional, VITS/Glow/FastSpeech (geração anterior ao CSM), dado soberano/fechado. |
| 9 | **GAF-Flow (Auditory-Perceptual Flow)** (U1Ync-ijcnn) | **IJCNN (IEEE)** | **LOW** | Único fio: **loss perceptual ponderado por saliência auditiva** (Gammatone/coclear) + diagnóstico de "fratura espectral" — inspiração conceitual se um dia treinarmos vocoder/métrica espectral própria. **É o único paper de venue IEEE do lote** (ver nota IEEE abaixo). | Front-end mel+HiFi-GAN (não-CSM/Mimi), inglês, sem release, não toca nossos 3 gaps. |

## O que fazer com isso — por frente (o "plano")

- **EVAL (frente mais beneficiada, 2 papers load-bearing):**
  - Guardar 2606.19951 como **justificativa citável** de que MOS automático não serve pra medir prosódia/timbre → mantém a prioridade do **scorecard próprio (F0-RMSE segmentado / IU, linha Aluísio)**. Ao rankear vozes/checkpoints, **controlar por F0 médio** (confundidor) e usar **variância de F0** como feature do "vivo".
  - 2607.01965 vira o **blueprint do "accent-scorecard carioca"**: classificador treinado em fala carioca humana + auditoria cross-domain com **direção do erro** ("o CSM fecha as médias abertas?"). É a forma de tornar o gap #1 (sotaque) objetivo e por-segmento. Custo = gravar/segmentar um benchmark carioca (Praat) + escolher o contraste-alvo. Candidato a **arm de eval** quando houver escuta girando, e a **peça publicável** junto com a linha USP.
- **PROSÓDIA (#2):** receita **FFmpeg de pares relativos** (2606.19209) pra fabricar dado de controle de prosódia limpo a partir da voz do Pedro; a confirmação (DTRF) de que **emoção/estilo mexe em duração/ritmo** reforça o corte por IU (`prosodic_punct.py`).
- **EMOÇÃO:** receita de **eval de emoção** (SER-UAR independente, MOS 3 eixos) e **âncora-neutra/resíduo relativo** (DTRF) — construíveis sem dado emocional pt-BR rotulado; o **botão α** é um baseline SFT antes do SFT→DPO→GRPO. Casa com a linha Candido Jr (emoção pouca-data).
- **DADOS/ALINHAMENTO:** MFA/WhisperX seguem sendo o alinhador (2607.06831 confirma); "adaptar de vizinhos" (1388-4978) reforça o **Estágio A**.
- **FRONT-END:** FlowEdit (2606.20518) = **canary anti-drift** pro fine-tuning (vigiar qualidade-geral) + mais um ponto contra G2P/léxico parkeado.
- **Realismo:** a tabela horas→MOS do Myaamia entra como número de calibração de expectativa no ROADMAP.

## Licença / proveniência (resumo)
Nenhum paper entrega artefato pt-BR embarcável. **Métodos** são livres pra reimplementar. Artefatos de terceiros que **reprovariam** o gate de produto se fôssemos usá-los diretamente: ESD (research-only), MMS (CC-BY-NC), F5-TTS (pesos públicos costumam ser NC — verificar), datasets "upon request" (Lampung) e soberanos/fechados (Myaamia). Artigos CC-BY do lote: applsci-16-06613 (DTRF) e 1388-4978-1-PB (Lampung). Os demais são preprints/venues sem licença de reuso declarada — citar, não copiar figura/texto.

## Nota IEEE 11570809 (pergunta do Pedro)
Não deu pra identificar o paper **só pelo número** do IEEE Xplore: o IEEE bloqueia scraping (HTTP 418) e o número de documento não é indexável por busca web (colide com PMID/patentes não relacionados). O **único paper de venue IEEE deste lote** é o **GAF-Flow (IJCNN)** — se o 11570809 for ele, o Pedro **já tem a versão livre** (`research/papers/U1Ync-ijcnn_pap2765s2.pdf`). Se for outro, playbook pra achar de graça: arXiv (mesmo título), Google Scholar ("All versions"), Semantic Scholar, a **página pessoal/institucional dos autores**, ou pedir o PDF ao autor por e-mail (praxe aceita). Pra eu confirmar, basta o **título**.

## Incorporado no código/plano (13/jul — pedido do Pedro: "coloca nos planos e códigos")

- **Phonology-eval (2607.01965) → `eval/accent_scorecard.py` (CONSTRUÍDO + self-test ✓).** Repo deles
  clonado e lido (`task1_crossdomain.py` + `tts_rule_audit.py`); reimplementado pro pt-BR carioca
  (contrastes /ɛ/-/e/, /ɔ/-/o/; classificador LR/RF + cross-domain H→TTS + direção do erro). Código
  deles **sem LICENSE** → método reimplementado, nada copiado. Falta plugar dado real (formante via
  parselmouth + alinhamento de vogal + rótulo do léxico). É o **accent-scorecard** que torna o gap #1 objetivo.
- **MOS-discrepancy (2606.19951) → guardrail em `eval/README.md` (ADICIONADO).** "Não rankear por MOS
  automático em prosódia; controlar F0; usar variância de F0". Confirma externamente o rebaixamento do UTMOS.
- **DTRF (applsci-16-06613) → arm de experimento specado (a construir na fase de emoção F2/F3).** Add-on:
  emoção sobre backbone CONGELADO via adaptadores residuais + **botão α** + **âncora-neutra/resíduo relativo**
  (preserva timbre, sem rótulo pt-BR via emotion2vec) + **SER-UAR com juiz independente** (evita circularidade).
  Os módulos de duração são NAR-específicos (não portam pro CSM AR); a arquitetura de controle e a receita de
  eval portam. Entra na **matriz de experimentos** (pós-sweep de arquiteturas/add-ons, dossiê 85).
- **FineCombo (2606.19209) → receita de dado (arm):** FFmpeg pitch/speed → pares de controle de prosódia
  relativos a partir da voz do Pedro (limpo de licença). Entra na engenharia de dados da matriz.
- Pendente de consolidação: a **matriz de experimentos/ablação** (add/remove abordagens em cada etapa) sai
  junto com o sweep de arquiteturas+add-ons (`85-arquiteturas-addons.md`).
