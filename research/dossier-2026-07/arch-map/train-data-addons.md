# Add-ons de treino — ENGENHARIA DE DADOS (train-data-addons)

_Digest de decisão — 2026-07-13. Foco: o que MULTIPLICA o valor do nosso dado carioca escasso.
Lente: mérito do MÉTODO (agnóstico de idioma); idioma só pesa em dado/licença/sotaque._

## TL;DR (o delta que move a agulha)

1. **Nossa maior alavanca barata não é coletar mais — é (a) segmentar por prosódia [já fazemos], (b) condicionar cada enunciado no CONTEXTO/turno anterior, e (c) expandir com dado sintético do NOSSO próprio modelo, MAS pagando o pedágio da "Synthetic Erosion" com alinhamento de preferência.** Os três atacam diretamente nossos gaps #1 (sotaque), #2 (prosódia robótica) e o gargalo de volume.
2. **Aviso da fronteira (verificado, arXiv 2605.27383, jul/2026):** dado sintético melhora fonética/WER mas ACHATA a prosódia de forma monotônica — o colapso ("Synthetic Erosion") começa por volta de **50% de razão sintética** (entropia de token cai, repetição sobe, NMOS despenca 4.5→3.1 a 100%). Ou seja: encher o dataset de synth "cura o sotaque e mata a alma". A correção existe e é barata (DPO de duplo objetivo contra o próprio synth). Isto casa perfeitamente com nosso gap #2.
3. **Condicionamento em turno é de graça e melhora MOS** (verificado, arXiv 2505.07202): treinar por ENUNCIADO **condicionado no contexto** bate treinar a conversa inteira (a conversa-inteira alucina similaridade de locutor). Isso refina nosso C1 sem custo.

Gate de licença: **todos os MÉTODOS abaixo são livres** (algoritmo não é licenciável). O cuidado é só com PESOS/DADOS de terceiros que embarcariam — sinalizado item a item. O sintetizador da nossa pipeline de dado sintético deve ser o NOSSO CSM (Apache-2.0), nunca XTTS (Coqui CPML, não-comercial).

---

## 1. Auto-destilação / dado sintético do próprio modelo (LLM→texto → nosso CSM → filtro WER) — **TEST**

**O que é.** Pipeline "LLM-to-Speech": um LLM gera texto carioca diverso (gírias, números falados, perguntas conversacionais) → sintetiza com o NOSSO checkpoint CSM pt → filtra com Whisper por WER e descarta o lixo. Verificado como receita publicada para dialeto sub-representado (árabe egípcio, arXiv 2602.15675, repo NileTTS **CC-BY-4.0**), usando XTTS+Whisper.

**Por que pra nós.** É o multiplicador de volume mais direto: transforma nosso gargalo de ÁUDIO limpo em um problema de TEXTO+compute (barato). Ataca especialmente leitura de número (#3) e cobertura fonética/sotaque (#1) — dá pra fabricar milhares de enunciados com dígitos, datas, valores. Encaixa em C0/C1 (língua/conversa), NÃO na voz-alvo.

**Cuidado / delta.** (a) O sintetizador tem de ser o nosso CSM (Apache-2.0), não XTTS (peso não-comercial); a RECEITA do NileTTS é reusável, o peso não. (b) Dado sintético sozinho achata prosódia → **obrigatório** parear com o item 2. (c) Filtro por WER é o gate de qualidade; mantenha uma fração de real oversampled (padrão ZeSTA/2603.04219).

**Licença:** método livre; receita NileTTS CC-BY-4.0 (ok); sintetizar só com peso do nosso gate.
**Maturidade:** released+usável (receita publicada, repos existem). **Verificado:** web, jul/2026.

## 2. Alinhamento de preferência contra o sintético — antídoto da "Synthetic Erosion" — **TEST**

**O que é.** Depois de treinar com muito synth, você recupera a expressividade perdida com **DPO de duplo objetivo** ("pares relativos" no sentido literal): gere do mesmo texto duas saídas — `y_expr` (com style tokens, expressiva mas às vezes errada) e `y_stab` (sem, estável mas plana) — e monte pares de preferência contra o real (DGSA, arXiv 2605.27383). Ativa peso dinâmico só quando a erosão aparece (`λ ∝ (α−α*)`). Para escassez extrema há a variante TDSC (multi-temperatura + self-critique). **Entropia de token** é o proxy barato pra monitorar diversidade prosódica (ganho reportado a α=80%: NMOS 3.61→4.42, spk-sim 3.54→4.53, mantendo WER).

**Por que pra nós.** É a resposta DIRETA ao nosso gap #2 (prosódia robótica) e o par obrigatório do item 1. Reusa infra que já planejamos: o MOS/SER-judge interno (T3) vira o avaliador de preferência; a voz do Pedro (real) é o lado "preferido". Não precisa de mais coleta humana — os pares saem do próprio modelo.

**Cuidado / delta.** Requer um sinal de preferência confiável (nosso judge). O paper é **CC-BY-NC-SA** → método/ideia livres, mas NÃO reusar pesos/dados deles. É experimento de arm, não plug-and-play — por isso TEST, não ADOPT.
**Licença:** método livre (paper NC-SA cobre só o artefato deles). **Maturidade:** paper 2026 + landscape maduro (RLAIF-SPA, Emo-LiPO, F5R-GRPO, fine-grained PO 2502.02950). **Verificado:** web, jul/2026.

## 3. Treino por ENUNCIADO condicionado no CONTEXTO/turno (não a conversa inteira) — **ADOPT**

**O que é.** Cada alvo de treino é 1 enunciado, mas condicionado no(s) turno(s) anterior(es) — texto E áudio — como contexto. Verificado (arXiv 2505.07202): utterance-level **com** condicionamento de contexto supera treinar a conversa inteira; a conversa-inteira sofre "alucinação de similaridade de locutor" (mistura vozes entre turnos) e custa mais compute (~37% reportado; ~20 h-H100 no estudo). Ganho de MOS reportado 4.3 vs 3.7 (estudo pequeno — direção sólida, número a confirmar).

**Por que pra nós.** É exatamente o design nativo do CSM (audio-conditioned sobre histórico) e é a alavanca barata que o próprio playbook Sesame/a16z aponta: **condicionar em turnos/contexto** rende prosódia coerente sem dado novo. Refina nosso C1 (ADAPT-CONV) e como montamos o flywheel 2-party: guardar pares (turno_anterior → resposta) já formatados. Casa com a trava #3 (condicionamento de locutor) do ESTRATEGIA-DADOS.

**Cuidado / delta.** Não migrar para "treinar diálogo inteiro num passo" (tentador, mas pior). Manter a perda no enunciado; contexto entra como condicionamento, não como alvo.
**Licença:** método livre. **Maturidade:** released (é como CSM já opera) + estudo comparativo 2025. **Verificado:** web, jul/2026.

## 4. Segmentação prosódica por unidade entoacional (PSST/SAMPA) — **ADOPT (já default)**

**O que é.** Cortar o dado de treino em Unidades Entoacionais (fronteiras prosódicas), não em pontuação/timestamp. PSST (arXiv 2302.01984, Whisper fine-tune, MIT) e o SAMPA pt-BR (arXiv 2607.07408, Galdino coautor — nosso dossiê 83).

**Por que pra nós.** Já é `prosodic_punct.py` default na coleta e já PROVAMOS a tese em pt-BR: WER 0.50→0.43, CER 0.35→0.31, contorno de pitch mais natural (menos "plano"), F0 RMSE ~44→~39 Hz (verificado no follow-up arXiv 2511.14779, NURC-SP). Ganho é modesto porém real e ~grátis no pré-processamento.

**Cuidado / delta.** Gera ~25–30% menos segmentos (mais longos/variáveis) — ajustar batch/padding. O ganho grande do espontâneo continua sendo VOLUME de fala espontânea limpa, não a segmentação em si.
**Licença:** Whisper MIT; SAMPA fine-tune próprio (checar redistribuição do peso, mas uso interno ok). **Maturidade:** released+em produção interna. **Verificado:** web, jul/2026.

## 5. Augmentation de sinal (FFmpeg pitch/tempo, RIR, SpecAugment, speed-perturb) — **TEST (escopo restrito)**

**O que é.** Perturbações baratas de DSP: pitch-shift, time-stretch, ruído/reverb (RIR), SpecAugment, speed-perturbation ±10%. O "arroz-com-feijão" de low-resource.

**Por que pra nós.** Barato e útil para ROBUSTEZ e cobertura da LÍNGUA (C0/C1): mais variação acústica sem gravar. Ajuda o modelo a não colar em condição de microfone única.

**Cuidado / delta (importante).** **NÃO** aplicar pitch/tempo agressivo na camada VOZ-CARIOCA (C2): shift de pitch/formante CORROMPE a identidade que estamos clonando (spk-sim cai). Restringir DSP-aug a C0/C1 (língua/robustez); na voz, no máximo augment de canal (ruído leve/reverb) preservando F0. Por isso TEST-com-escopo, não ADOPT cego.
**Licença:** método livre (FFmpeg/SoX). **Maturidade:** released, trivial. **Verificado:** conhecimento estabelecido (não precisa web).

## 6. Transferência de emoção cross-speaker (VC + pitch-shift) para emoção com POUCO dado — **TEST**

**O que é.** Como temos ≈0h de emoção aberta do Pedro: pegar emoção de OUTRO locutor (corpus emotivo qualquer) e transferir para a voz-alvo via voice conversion não-paralela + pitch-shift aug (linha Casanova/Candido Jr; arXiv 2204.10020; síntese de style-transfer 2409.17364). Alternativa moderna: controle de INTENSIDADE via preferência (Emo-LiPO 2606.13006) reusando o item 2.

**Por que pra nós.** Destrava emoção controlável sem precisar gravar o Pedro atuando cada emoção — nosso maior buraco de dado depois de volume. "Pares relativos" de intensidade (mais/menos alegre) precisam de pouquíssimo rótulo.

**Cuidado / delta.** VC herda artefatos; validar spk-sim pós-transfer. Corpora emotivos costumam ser NC → use-os como FONTE de estilo em treino de pesquisa/adapter descartável, nunca como peso/dado embarcado; o produto embarca só o adapter de emoção treinado, não o corpus. kNN-VC (código MIT) é um VC leve utilizável.
**Licença:** método livre; VC-tool MIT (kNN-VC, inferido); corpora emotivos checar caso a caso. **Maturidade:** released (técnicas 2022–2026 maduras). **Verificado:** web parcial (papers confirmados; detalhe de licença de VC inferido).

## 7. Mitigação de esquecimento catastrófico: experience-replay + canary + LoRA-onde — **ADOPT**

**O que é.** Ao fazer o LoRA da voz (C2), misturar uma pequena fração de dado pt-base a cada passo (experience replay) + monitorar um CANARY (frases pt fixas) pra pegar colapso do idioma cedo. Verificado (2025): LoRA "learns less and forgets less"; replay é a mitigação mais robusta em adaptação de fala; O-LoRA (ortogonal) ajuda em sequências de tarefas. PEFT sozinho NÃO garante retenção.

**Por que pra nós.** É literalmente nosso gotcha #6 (lr alto/run longo destrói o pt → WER 300%) e a trava #4 do ESTRATEGIA-DADOS (assimetria de LR/LoRA). Formaliza o que já intuímos: LoRA r16 curto + réplica pt + canary como CI. Barato, alto retorno de segurança.

**Cuidado / delta.** Definir a fração de replay (tipicamente 5–15%) e as camadas do LoRA (attn q/v costuma bastar; MLP arrisca reaprender língua). Canary vira gate automático no watchdog do pod.
**Licença:** método livre. **Maturidade:** released, prática consolidada. **Verificado:** web, jul/2026.

## 8. Currículo cross-lingual / warm-start de língua próxima (ES / PT-eu) — **WATCH**

**O que é.** Pré-treinar/curriculum a partir de língua relacionada (espanhol, português europeu) antes do pt-BR — relatedness ajuda transfer (verificado: seleção de língua-fonte por proximidade, phone-mapping, embeddings SSL; multilingual strategy Springer 2026).

**Por que pra nós — e por que só WATCH.** Nosso C0 já é multi-fonte pt (CML+MLS+CV+Granary ~400h+ legais) e o CSM base já traz priors. O ganho marginal de adicionar ES quando já temos centenas de horas de pt é PEQUENO — relatedness importa quando você tem ~0h do alvo, não é nosso caso. Vigiar como plano B se algum fonema/registro específico faltar; não priorizar agora.
**Licença:** método livre; datasets ES/PT-eu (MLS, CV) são CC/permissivos (ok no gate). **Maturidade:** released. **Verificado:** web, jul/2026.

---

## O que eu **descartaria** (SKIP, honestidade)

- **VC pra MULTIPLICAR IDENTIDADES de locutor no corpus (kNN-VC/RVC gerando "novos falantes"):** útil pra speaker-recognition, mas nós queremos UMA voz carioca. Inflar identidades sintéticas na camada de voz polui o alvo e não ajuda spk-sim. Onde diversidade de locutor importa (C0/C1 língua), o dado real multi-locutor já basta. **SKIP** pra voz; irrelevante pro nosso alvo.
- **Back-translation de fala como no ASR (2505.16972):** brilha pra reconhecimento, não pra síntese — pra TTS o análogo é o item 1 (LLM→synth), que já cobre isso melhor. **SKIP** como linha separada.
- **Treinar a conversa inteira num passo** (ver item 3): tentador, mas mede pior. **SKIP.**

## Fio condutor pra decisão

- **Fazer já (ADOPT):** 3 (contexto/turno em C1), 4 (prosódia — já roda), 7 (replay+canary+LoRA-onde no C2).
- **Arm de experimento barato (TEST):** 1+2 juntos (synth do nosso CSM **+** DPO anti-erosão — nunca 1 sem 2), 5 (DSP-aug só em C0/C1), 6 (emoção cross-speaker).
- **Vigiar (WATCH):** 8 (warm-start ES) — só se faltar fonema.
- **Regra de ouro verificada da fronteira:** _synth resolve fonética/sotaque e destrói prosódia; o alinhamento de preferência é o que devolve a alma._ Isso amarra nossos gaps #1 e #2 num único pipeline.
