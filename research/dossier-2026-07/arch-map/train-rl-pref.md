# Add-on de treino: RL / preferência para fala (train-rl-pref)

> Sub-tópico do arch-map (13/jul/2026). Foco: **decisão** — plugar / testar / vigiar / pular.
> Lente: avaliar por MÉRITO DE MÉTODO (algoritmo de RL/preferência é livre e agnóstico de idioma);
> idioma/licença só pesa em DADO e PESO de terceiros. Verificado na web onde marcado; resto = inferido.

## TL;DR (o que muda pra nós)

1. **RL/preferência é camada de POLIMENTO, não substituto de dado.** Entra DEPOIS de SFT + um eval
   confiável girando (nosso gate: eval humana do Treino-2 saiu do n=0). Todo o roadmap e toda a
   literatura confirmam: sem sinal de preferência confiável, RL só amplifica o que você já mede.
2. **A alavanca certa pro nosso #2 (prosódia robótica) é DPO iterativo com pares HUMANOS — não GRPO
   multi-reward.** Achado load-bearing (2509.18531, verificado): GRPO otimizando CER + spk-sim
   **colapsa a prosódia em fala quase-monótona** (reward hacking do que é mensurável). ~200 pares
   humanos/rodada × 3 rodadas (≈600 julgamentos, dentro da nossa capacidade de escuta) **restauram a
   prosódia** mantendo CER competitivo. Isso valida e afia o P7/M2 do roadmap.
3. **GRPO multi-reward verificável (WER + spk-sim + DNSMOS) serve pro #3 (números/inteligibilidade),
   mas tem que ser GUARDADO na prosódia.** Ótimo pra "leitura de número/sigla correta"; venenoso se
   deixado solto sobre naturalidade.
4. **Custo de treino é trivial; o custo é gerar o par.** DPO em áudio: ~15k pares = ~7 A100-h (Tango 2)
   → dezenas de dólares. O gargalo é a ESCUTA/rotulagem, não a GPU. Casa com "GPU não é gargalo".
5. **Turn-taking/backchannel por RL (moshika-rl-seamless) é do mundo Moshi full-duplex — parkeado.**
   Hoje nossa cascata resolve turno com heurística (smart-turn v3). Vira relevante só quando o spine
   Moshi reabrir (50h+ estéreo). Já estava no VIGIL-LOG; aqui fica o método detalhado.

---

## A fronteira, item a item (com veredito)

### 1. DPO iterativo com pares HUMANOS de prosódia — **ADOPT** (é o plano; afiar agora)
- **O que é:** coletar A/B humano ("qual soa mais natural em pitch/ritmo?"), rodar DPO padrão, usar o
  checkpoint anterior como referência (π_ref = π_{r-1}) por 2-3 rodadas. Sem desenhar reward automático.
- **Evidência (verificada):**
  - *No Verifiable Reward for Prosody* (arXiv 2509.18531): base Llasa-1B (LLaMA→XCodec2, mesma classe do
    CSM). GRPO em CER+NLL → "colapsa o que não é medido (variação prosódica) em fala quase-monótona".
    **~200 pares/rodada × 3** → DPO Round 2 vence em preferência humana (ELO 1190 vs 1046 comercial)
    com CER 3,6% (vs 2,2% do GRPO monótono). **Retorno decrescente após 2-3 iterações.**
  - *Preference Alignment Improves LM-based TTS* (arXiv 2409.12403, Tencent, código no ESPnet): 1,15B,
    DPO melhora inteligibilidade + spk-sim + MOS-proxy de forma consistente; generaliza pra métricas
    não-vistas. É o estudo empírico de referência da classe LM-TTS.
  - *Tango 2* (arXiv 2404.09956, já no roadmap): **15k pares = 7 A100-h** — o número de custo.
- **Fit ao stack:** direto. CSM é AR-token-LM; DPO opera nos tokens/logits. Nosso `rate_app` já é o
  coletor de preferência (WER + perceptual). O corte por IU (`prosodic_punct.py`) dá o eixo de escuta.
- **Licença:** **método livre** (DPO é algoritmo). Nenhum peso de terceiro embarca. Pares = nossa voz.
- **Quando entra:** M2, depois que a eval humana (rate_app) estiver girando com ≥5 ouvintes. Antes disso
  não há sinal. É o "P7 (DPO em áudio)" — este dossiê confirma a receita e o custo mínimo.

### 2. GRPO multi-reward VERIFICÁVEL (WER + spk-sim + DNSMOS) — **TEST** (só pro #3, guardado)
- **O que é:** amostrar N gerações por prompt, pontuar com rewards automáticos (Whisper-WER,
  ECAPA/spk-sim, DNSMOS), vantagem relativa ao grupo, sem crítico (GRPO). Inworld usa exatamente
  WER+spk-sim+DNSMOS (já logado no dossiê 90). *Multi-Reward GRPO single-codebook* (arXiv 2511.21270,
  verificado) faz 5 rewards — inteligibilidade, spk-sim, penalidade de duração, regularização de
  entropia, e um reward de prosódia anotado por LLM externo — sobre **TTS-LM de codebook único**
  (a arquitetura mais próxima do CSM que achei com GRPO).
- **Por que TEST e não ADOPT:** RLVR (reward verificável) é seguro pra o que É verificável —
  **leitura de número/sigla (nosso #3), pronúncia, estabilidade** — e perigoso pra prosódia
  (ver item 1). Usar como arm barato *escopado a inteligibilidade/número*, com a prosódia protegida
  (KL forte, ou congelar depois do DPO de prosódia). O reward "prosódia anotada por LLM" do 2511.21270
  é a pista de como injetar estrutura de pausa sem colapsar — mas é indireto e não-verificado por nós.
- **Fit:** média. GRPO precisa de N amostras/prompt (geração cara), mas roda em 1 GPU. Reusa Whisper
  (MIT) e emotion2vec (já no eval).
- **Licença:** método livre. 2511.21270 = paper CC-BY-NC-ND (sem pesos; só reimplementar). Inworld = só
  descrição, sem release.
- **Custo:** dominado pela geração (N×), não pelo update. Barato em escala de arm.

### 3. moshika-rl-seamless — RL de turn-taking / backchannel — **WATCH** (mundo Moshi, parkeado)
- **O que é (verificado, arXiv 2606.11167, Kyutai/Ohashi-Zeghidour-Défossez-Kharitonov):** GRPO
  pós-treino em modelo full-duplex com **4 rewards por eixo de interatividade** — pausa (-1 se falar
  durante hesitação), turn-taking (−atraso em s), backchannel (F1 vs ground-truth ±1s), interrupção
  (−atraso pós-barge-in) — **+ um reward de qualidade por LLM-judge (escala 1-3)** que impede a
  degradação semântica ao caçar timing. Bases: **Moshi-7B e PersonaPlex**. Melhora todos os eixos no
  Full-Duplex-Bench v1/v2 mantendo UTMOSv2.
- **Reward hacking documentado:** ablação mostra trade-off pausa↔turn se treinado num eixo só; o
  LLM-judge é o guard-rail. Apêndice reporta degradação de segurança em dado Fisher (viés cooperativo).
- **Custo (verificado):** **32× H100, 100 épocas** — fora da nossa faixa; é escala de lab.
- **Fit ao stack:** BAIXO **agora**. Nossa cascata Maya-BR v0 faz turn-taking com heurística
  (smart-turn v3 BSD-2, ~98ms CPU) + abort 20ms — sem RL. O método só passa a valer quando o spine
  **Moshi** reabrir (gate: 50h+ estéreo). Aí vira o blueprint de pós-treino de interatividade.
- **Licença:** **pesos moshika-rl-seamless / personaplex-rl-seamless = CC-BY-NC-SA 4.0 → NÃO EMBARCAM**
  (NC). Método é livre pra reimplementar. Já estava adotado-como-referência no VIGIL-LOG (10/jun).

### 4. RRPO / DiffRO — anti-reward-hacking + reward model robusto — **WATCH** (canário/insight)
- **O que é (verificado, arXiv 2512.04552, ICASSP 2026):** documenta o modo de falha — a política gera
  **artefatos acústicos não-semânticos (cliques de boca, plosivas duras)** que enganam o reward model e
  ganham reward alto degradando naturalidade. Corrige o RM com **regularização híbrida: label smoothing
  + energy-adaptive mixup + treino adversarial (FGM)**. Sobre CosyVoice2 (codec-LM), 8× A800, 10k
  amostras mandarim 1 locutor. E-MOS 3,78 vs 3,65 do DiffRO.
- **Por que importa pra nós:** é o **canário** de qualquer RL que fizermos — nomeia o sintoma exato
  (artefato acústico que hackeia a métrica) e dá as 3 defesas do RM. Casa direto com nosso achado do
  dossiê 84 (MOS-preditores cegos): se o RM é cego a prosódia/tem viés de F0, o RL o explora.
- **Fit:** conceitual **agora**, prático só quando/se treinarmos um reward model próprio. DiffRO
  (backprop diferenciável via Gumbel-Softmax) é mais caro/instável que DPO — não é o primeiro passo.
- **Licença:** sem release. Método livre.

### 5. EMORL-TTS / Emo-LiPO / HPRO — RL de EMOÇÃO fina — **SKIP por ora** (sem dado; reabre em M2+)
- **O que é:** GRPO/preferência com rewards de emoção. *EMORL-TTS* (arXiv 2510.05758): GRPO sobre
  codec-LM com 3 rewards — classificação de emoção, intensidade, ênfase. *Emo-LiPO* (2606.13006):
  Listwise Preference Optimization pra intensidade de emoção. *HPRO* (2606.28249): reward hierárquico
  progressivo por extração de preferência.
- **Por que SKIP agora:** todos **exigem corpus emocional rotulado** (ESD etc.) — e nosso dado emocional
  pt-BR ≈ 0h (gargalo estrutural conhecido). Sem o dado, não há reward de emoção pra otimizar. O baseline
  barato antes de RL emocional é o **botão α / âncora-neutra do DTRF** (dossiê 84), não estes.
- **Fit:** reabre em M2+ quando houver ≥30min/estilo dirigido (o plano já prevê). Casa com a linha
  Candido Jr (emoção pouca-data).
- **Licença:** ESD = research-only (não embarca dado/peso). EMORL sem release claro. Método livre.

### 6. GSRM — Generative Speech Reward Model — **WATCH** (frontier de reward model)
- **O que é (arXiv 2602.13891):** reward model **generativo** (não discriminativo) pra RLHF de fala;
  gera critério/avaliação em vez de classificar, melhor correlação com humano que MOSNet/UTMOS/UTMOSv2.
- **Por que vigiar:** é a resposta de fronteira ao nosso próprio achado ("MOS-preditores automáticos são
  cegos a prosódia + viés de F0", dossiê 84). Se algum dia precisarmos de um RM escalável melhor que o
  scorecard manual, é a família a olhar. Não é pra plugar — é pra saber que existe.
- **Licença:** research (arXiv nonexclusive). Sem release confirmado.

### 7. GLM-TTS — recipe GRPO **liberada e de licença limpa** — **TEST** (referência de receita)
- **O que é (verificado, arXiv 2512.14291 + HF zai-org/GLM-TTS):** técnico de TTS com **GRPO** pra
  pronúncia + timbre + naturalidade + expressividade emocional. Arquitetura 2-estágios: **Stage-1 LLM
  Llama → tokens de fala; Stage-2 Flow-Matching → mel.** (Mais família CosyVoice que CSM: o CSM é
  RVQ/Mimi puro sem flow-decoder — a GRPO deles opera no Stage-1 LLM, que é o análogo transferível.)
- **Por que TEST:** é **o recipe GRPO-TTS de melhor licença que achei — pesos MIT, código público**.
  Serve de **referência de implementação** (como montar rewards/loop GRPO num LLM-de-fala) mesmo sendo
  zh/en. Não embarca direto (sem pt), mas nada bloqueia estudar/adaptar o código.
- **Licença:** **pesos MIT (embarcáveis em tese)** — mas **só zh/en**, então na prática é receita, não
  peso. Método livre.

### 8. Step-Audio 2 — RL "reasoning-centric" paralinguístico — **WATCH** (entendimento, não geração)
- **O que é (verificado, arXiv 2507.16632):** RL centrado em raciocínio melhora ASR + compreensão
  paralinguística (estilo/emoção). Já estava adotado-como-estudo no VIGIL-LOG (17/mai).
- **Delta:** é mais sobre **entender** paralinguística (lado ASR/LLM da cascata) do que **gerar** melhor
  prosódia. Útil pro lado LLM da Maya-BR (que o CTO Sesame admite ser cego a paralinguística), não pro
  CSM. Vigiar; não é a alavanca de geração. Variantes: ParaS2S (2511.08723, GRPO paralinguístico S2S),
  Koel-TTS (2502.05236, preference alignment — **grupo Casanova/NVIDIA**, contato nosso) e MPO
  (2509.00685, preference multidimensional) na mesma família.

---

## O mapa de decisão (uma tela)

| Técnica | Veredito | Entra quando | Custo GPU | Licença (peso/método) |
|---|---|---|---|---|
| DPO iterativo, pares humanos (prosódia) | **ADOPT** | M2, eval girando | ~7 A100-h / 15k pares | método livre; sem peso 3º |
| GRPO multi-reward verificável (#3/números) | **TEST** | arm barato, escopado + guardado | geração N× (1 GPU) | livre; 2511.21270 CC-BY-NC-ND (sem peso) |
| moshika-rl-seamless (turn-taking/backchannel) | **WATCH** | só se spine Moshi reabrir (50h+ estéreo) | 32× H100 (fora da faixa) | pesos CC-BY-NC-SA (NÃO embarcam); método livre |
| RRPO/DiffRO (anti-hacking, RM robusto) | **WATCH** | se treinarmos RM próprio | 8× A800 | sem release; método livre |
| EMORL/Emo-LiPO/HPRO (RL emoção) | **SKIP p/ agora** | M2+, com ≥30min/estilo | — | ESD research-only; método livre |
| GSRM (reward model generativo) | **WATCH** | se precisar RM escalável | — | research; sem release |
| GLM-TTS (recipe GRPO liberada) | **TEST** | agora, como referência de código | — | **pesos MIT** (mas zh/en → é receita) |
| Step-Audio 2 (reasoning-RL paraling.) | **WATCH** | lado LLM da cascata | — | método livre |

## Três frases pro Pedro
- **A ordem certa é: dado → SFT → eval confiável → DPO humano de prosódia → (só então) GRPO escopado a
  número/inteligibilidade.** Inverter isso (GRPO cedo sobre WER) *piora* a prosódia — está provado.
- **Nada aqui muda o gargalo (dado/eval).** RL/preferência é o verniz de M2, e o mais barato dele
  (DPO, ~600 julgamentos) já é o que a literatura diz ser suficiente pra prosódia.
- **O único peso tentador (GLM-TTS MIT) não fala pt** — vale como **código de referência de GRPO**, não
  como atalho. Turn-taking por RL fica parkeado com o Moshi.
