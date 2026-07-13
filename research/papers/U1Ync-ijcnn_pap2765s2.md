# GAF-Flow: An Auditory-Perceptual Flow Model for Enhanced Speech Synthesis

**Autores:** Rao Deng, Weike You, Linna Zhou, Hong Guo
**Instituições:** School of Cyberspace Security, Beijing University of Posts and Telecommunications (BUPT); Shanghai Key Laboratory of Forensic Medicine / Key Laboratory of Forensic Science, Ministry of Justice (China).
**Venue:** IJCNN (International Joint Conference on Neural Networks) — inferido pelo nome do arquivo (`ijcnn_pap2765s2`). O **ano não consta** no corpo do texto; pelas referências citadas (Hearing Research 2025, COLING 2025, Interspeech 2025) é **2025 ou posterior**. Sem arXiv ID visível.
**Financiamento:** programas nacionais de C&T da China (National Key R&D 2023YFC3305401, NSFC 62172053 / 62302059) — pesquisa acadêmica chinesa, ligada a laboratório de medicina/ciência forense.

---

## TL;DR

GAF-Flow é uma variação de **front-end acústico** para TTS neural construída **em cima do Matcha-TTS** (flow matching / OT-CFM + vocoder HiFi-GAN). A tese: o Mel-espectrograma padrão é "máquina-cêntrico" e perde resolução acima de 2 kHz, onde estão pistas de timbre/consoante que o ouvido humano valoriza. A solução tem 3 peças: (1) um **filterbank híbrido Gammatone-Mel** (Mel abaixo de 2 kHz, Gammatone acima de 2 kHz → representação de 80 canais); (2) **Channel-wise Adaptive Normalization (CAN)** para colar as estatísticas heterogêneas dos dois domínios e matar a "fratura espectral" na fronteira de 2 kHz; (3) **supervisão por prior auditivo** (duas perdas extras: L1 nas bandas Gammatone de alta-freq + regularizador de suavidade temporal). Reportam ganhos sobre Matcha/Grad/VITS em LJSpeech e VCTK (inglês), mantendo a latência do flow matching. **Não é um modelo de voz conversacional, não trata sotaque/prosódia, é só inglês, e não há liberação de código/pesos declarada.**

---

## Método (o que eles realmente fazem)

Pipeline (Fig. 1 do paper): áudio bruto → STFT → magnitude é dividida em duas trilhas de filterbank paralelas.

1. **Gammatone-Mel Hybrid Filterbank**
   - Mel (40 filtros) para o **band baixo (<2 kHz)** — bom pra estrutura tonal grave.
   - Gammatone (40 filtros) para o **band alto (>2 kHz)** — inspirado na decomposição coclear, dá mais resolução no agudo (onde o Mel logarítmico "comprime demais").
   - Compressão logarítmica `L = log(|S| + 1e-5)` em cada trilha; concatena no eixo de frequência → **X_GM ∈ R^{80×T}** (80 canais). Mantém compatibilidade dimensional com a interface do Matcha-TTS.
   - Esse X_GM vira: (a) alvo do flow-matching, (b) domínio da regularização perceptual, e (c) alvo de fine-tuning do HiFi-GAN.

2. **Channel-wise Adaptive Normalization (CAN)**
   - Diagnóstico: Mel e Gammatone vivem em espaços estatísticos diferentes; a energia alta do Mel domina e "achata" as texturas Gammatone → descontinuidade abrupta na fronteira de 2 kHz ("**spectral fracture**", Fig. 3), que gera gradientes conflitantes, descontinuidade de fase e artefatos audíveis.
   - Solução: normalização **por canal** com média `μ_f` e desvio `σ_f` pré-calculados no conjunto de treino (80 canais), `ŷ = (y − μ_f)/(σ_f + ε)`. Projeta os dois domínios num espaço latente com média 0 / variância 1 por canal. Na inferência há a **denormalização** correspondente ("physiological scale recovery") antes do vocoder.

3. **Supervisão por prior auditivo (dual-supervision)**
   - **Auditory Loss (L_aud):** L1 restrito às bandas Gammatone de alta-freq H, pra forçar reconstrução fiel de envelopes espectrais finos (clareza de consoante / timbre).
   - **Auditory Prior Regularizer (L_hf):** penaliza flutuações quadro-a-quadro nas bandas H (suavidade temporal), pra evitar "jitter" não-natural.
   - Perda total: `L_total = L_dur + L_prior^orig + L_diff + α·L_aud + β·L_hf`, com **α=0.01, β=0.001**, ambos com warmup linear (0 nos primeiros 100 epochs, depois sobem ao valor final).

**Vocoder:** HiFi-GAN **fine-tuned** especificamente nos espectrogramas híbridos Gammatone-Mel (não é o HiFi-GAN Mel padrão).

---

## Setup experimental

- **Datasets:** LJSpeech (~24 h, 1 locutora feminina, inglês) — split 12.500 treino / 100 val / 500 teste. VCTK (subset de 20 locutores) para generalização cross-speaker — 90% fine-tune / 10% teste.
- **Pré-proc:** resample 22.050 Hz; texto fonemizado com **Phonemizer**; STFT FFT=1024, janela=1024, hop=256; f_min=0, f_max=8000 Hz.
- **Treino:** AdamW (β1=0.8, β2=0.99), seed 1234, lr 2e-4, decay exponencial 0.999/epoch, batch 16, **1× RTX 4090**.
- **Eval:** MOS com 30 ouvintes (MOS-N = naturalidade, MOS-S = similaridade de locutor), 20 enunciados, escala 1–5, IC 95%. Objetivas: **MCD** (distorção mel-cepstral) e **PESQ** (correlação r≥0.9 com MOS). Latência: wall-clock por comprimento de texto (30–1500 chars) em 1× V100.

---

## Números-chave

**Tabela I — LJSpeech / VCTK (MOS-N ↑, SMOS ↑, MCD dB ↓, PESQ ↑):**

| Dataset | Método | MOS-N | SMOS | MCD | PESQ |
|---|---|---|---|---|---|
| LJSpeech | Ground Truth | 4.41 | 4.22 | — | 4.12 |
| | VITS | 4.17 | 3.92 | 6.15 | 3.21 |
| | Matcha-TTS | 4.11 | 4.03 | 6.48 | 3.08 |
| | Grad-TTS | 4.06 | 3.97 | 6.92 | 2.88 |
| | **GAF-Flow (Ours)** | **4.22** | **4.09** | **5.82** | **3.42** |
| VCTK | Ground Truth | 4.38 | 4.15 | — | 4.01 |
| | VITS | 4.10 | 3.82 | 6.38 | 3.12 |
| | Matcha-TTS | 3.96 | 3.84 | 6.81 | 2.89 |
| | Grad-TTS | 3.88 | 3.76 | 7.24 | 2.72 |
| | **GAF-Flow (Ours)** | **4.16** | **3.98** | **6.15** | **3.28** |

Leitura honesta: o ganho de MOS-N sobre o baseline flow-matching (Matcha-TTS) é **+0.11 no LJSpeech e +0.20 no VCTK** — pequeno, mas o de PESQ é mais expressivo (**+0.34 / +0.39**) e o MCD melhora ~0.6–0.7 dB. GAF-Flow chega a **empatar/superar o Ground Truth em MOS-N no LJSpeech** (4.22 vs 4.41 — na verdade abaixo; a alegação de "melhor entre modelos sintetizados" se mantém).

**Tabela II — Ablação (LJSpeech, MOS ↑ / PESQ ↑):**

| Configuração | MOS | PESQ |
|---|---|---|
| GAF-Flow completo | 4.22 | 3.42 |
| − L_aud (Auditory Loss) | 4.15 | 3.26 |
| − L_hf (Prior Regularizer) | 4.19 | 3.31 |
| **− CAN** | **3.98** | **2.92** |
| − representação GM (baseline Mel puro) | 4.10 | 3.10 |

Achado central: **remover o CAN é o mais destrutivo** (MOS cai abaixo de 4.0, PESQ para 2.92) — evidência de que a "fratura espectral" é o problema real e a normalização por canal é a peça que segura tudo. As perdas auditivas contribuem mais em PESQ (agudo) que em MOS.

**Latência:** GAF-Flow fica ~na par com Matcha-TTS (o baseline flow), mais rápido que o difusivo Grad-TTS, escala O(L). O overhead extra (features híbridas + CAN) dilui conforme o enunciado cresce.

---

## O que pode servir pra gente (concreto e honesto)

**Contexto do projeto:** voz conversacional pt-BR carioca, qualidade "Maya", baixa latência full-duplex, sobre **CSM** (codec Mimi/RVQ, tokens discretos a 12.5 Hz). Gaps ativos: **sotaque gringo (#1), prosódia robótica (#2), leitura de número (#3)**; gargalo = **dado limpo pt-BR com licença comercial**.

**Veredito: relevância BAIXA.** Motivos, sem enfeite:

1. **Backbone errado.** GAF-Flow é um truque de **front-end mel-espectrograma + vocoder HiFi-GAN**. O nosso caminho é CSM sobre o **codec Mimi**, que já aprende sua própria representação latente do áudio — não há um "Mel-espectrograma de 80 bins" pra trocar por Gammatone-Mel. O filterbank híbrido + CAN **não se plugam** num modelo de tokens de codec. Portar isso significaria abandonar o CSM/Mimi (não é o plano).

2. **Não toca nos nossos gaps.** O paper melhora **fidelidade espectral de agudo / timbre / artefato "metálico"/"airiness"**. Nossos problemas são **sotaque, prosódia e número** — eixos ortogonais. Nada aqui ajuda o sotaque carioca nem a entoação.

3. **Só inglês, sem transferência declarada.** LJSpeech + VCTK. Zero pt-BR; o paper não faz nenhuma alegação cross-língua. O método é em tese agnóstico de língua (é feature de sinal), mas isso é dedução nossa, não resultado do paper.

4. **Sem release.** O paper **não declara liberação de código nem pesos**. Não é uma ferramenta que a gente baixa e usa — é uma ideia num PDF. (Matcha-TTS-base = MIT, HiFi-GAN = MIT, mas o GAF-Flow em si = desconhecido/não liberado.)

**O único fio aproveitável (nível insight, não ferramenta):**

- A tese de que **"MSE sobre bins de Mel é perceptualmente indiscriminante"** e de que vale **ponderar a perda por saliência auditiva** (priorizar bandas onde o ouvido/artefato mais aparecem) é uma boa provocação de design de perda/eval. Se em algum momento a gente treinar um componente que opere em espectrograma contínuo (ex.: um vocoder próprio, ou uma métrica de eval espectral), a ideia de **loss auditivo ponderado (Gammatone/coclear)** e o diagnóstico de "fratura espectral" podem inspirar uma métrica perceptual pt-BR mais fina que MCD cru. Encaixa marginalmente na frente de **eval** (nosso scorecard do "robótico"/F0-RMSE), não nas de dado/sotaque/prosódia.
- **Não** é candidato a implementação. No máximo, referência conceitual pra a discussão "perceptual loss / eval perceptual".

**Onde NÃO encaixa:** cascata Maya-BR v0 (é toda CSM), Estágio A/B (LoRA da voz do Pedro sobre CSM), coleta de dado, transcrição prosódica, front-end de número. Nada disso é tocado.

---

## Licença / proveniência

- **Código / pesos do GAF-Flow:** **não há menção de liberação** no paper → tratar como não-disponível/desconhecido. **Não** é ativo utilizável em produto.
- **Base Matcha-TTS:** MIT (permissiva). **HiFi-GAN:** MIT (permissiva).
- **Datasets:** LJSpeech = domínio público; VCTK = CC-BY-4.0 (ambos ok pra pesquisa; VCTK exige atribuição). Nenhum dado pt-BR.
- **Gate de licença do nosso produto (Apache/MIT/CC-BY/CC0):** irrelevante aqui porque não há artefato liberado pra adotar. Se algum dia o código sair sob MIT, ainda assim esbarra no problema (1): não é a arquitetura que a gente usa.

**Caveat final:** paper legítimo e bem-feito na sua caixinha (fidelidade espectral em TTS mel+vocoder, inglês), mas **ortogonal ao nosso projeto** em backbone, língua e gaps. Ganhos de MOS modestos sobre o baseline; o ganho real é em métricas objetivas de agudo. Sem release, sem pt-BR, sem prosódia/sotaque. Guardar como referência conceitual de "perceptual loss / eval", não como ferramenta ou receita.
