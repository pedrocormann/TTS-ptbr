# EVAL & MÉTRICAS — a régua que decide todos os add-ons (pt-BR carioca / stack CSM)

> Sub-tópico do arch-map. Lente: avaliar por **mérito de método**, não por idioma — a régua é
> agnóstica de idioma; pt-BR só entra em (a) qual referência humana você alimenta e (b) o eval
> carioca final. Foco em DECISÃO (plugar / testar / vigiar / pular), honesto sobre verificado-vs-inferido.
> Data da varredura web: **13/jul/2026**.

---

## TL;DR (o que muda pra nós)

1. **Não existe métrica automática única que sirva de oráculo.** O achado central da fronteira (arXiv
   2606.19951, verificado) é que **MOS-preditores (UTMOS/UTMOSv2/NISQA/DNSMOS) são CEGOS a prosódia**
   (humano cai −1,84 MOS com perturbação prosódica; os modelos <0,1) e têm **viés de F0** (premiam voz
   mais grave; DNSMOS r=−0,79). → **nunca rankear checkpoints da voz do Pedro por MOS automático.**
2. **A régua real é preferência humana (win-rate / CMOS)** — é a receita da Sesame e a única que
   sobrevive à crítica acima. É barata de montar (A/B cego) e é o que decide "ficou mais vivo?".
3. **O melhor substituto automático de MOS é distribucional: TTSDS2** (ρ≥0,50 em todo domínio/idioma,
   único de 16 métricas a conseguir isso) — e é **um método que você roda contra a SUA referência
   humana pt-BR**, então funciona mesmo sem pt-BR estar no benchmark pré-pronto deles.
4. **Cada um dos 3 gaps ganha um instrumento objetivo dedicado:**
   - **Sotaque #1** → accent-scorecard fonológico por-segmento (arXiv 2607.01965) + GOP/MDD.
   - **Prosódia #2** → TTScore reference-free (arXiv 2509.20485) + F0-RMSE/variância por IU.
   - **Número #3** → WER via Whisper large-v3 num set dedicado de números/datas/siglas.
5. **A plumbing existe pronta e Apache-2.0: VERSA** (90+ métricas num config). Não reimplementar
   WER/spk-sim/F0/distribucional na mão.
6. **Fronteira quente: audio-LLM-como-juiz** (SpeechJudge/AudioJudge). Promissor pra automatizar o
   win-rate, mas **pesos NC + só EN/ZH** hoje → vigiar, não embarcar.

---

## Itens, com veredito

### 1. TTSDS2 — distribucional, multilíngue, sem painel de MOS  → **ADOPT**
- **O que é:** compara a *distribuição* de features da sua saída sintética vs. uma referência de fala
  humana real, em 4 fatores: **Generic** (WavLM/HuBERT/wav2vec2), **Speaker** (d-vector/WeSpeaker),
  **Prosody** (F0 do WORLD + speaking-rate HuBERT/Allosaurus + embeddings prosódicos), **Intelligibility**
  (wav2vec2/Whisper). Score final = média não-ponderada. (arXiv **2506.19441**, SSW 2025 → **ICLR 2026 Oral**, Minixhofer et al.)
- **Números (verificado):** único de **16 métricas** com ρ Spearman ≥0,50 em *todo* domínio; média
  ρ≈0,67 vs MOS/CMOS/SMOS. Benchmark contínuo em **14 idiomas**, ~11k ratings, com pipeline que recria
  o test set pra evitar leakage.
- **Fit ao nosso stack:** é a **estrela-norte automática** pro "quão perto da fala humana carioca a
  saída do CSM está", sem montar painel de MOS a cada checkpoint. Cobre de graça 2 dos nossos gaps
  (intelligibility → número; speaker → fidelidade da voz do Pedro; prosody → robótico).
- **Sacada pt-BR (CORRIGIDO 13/jul, verificado na web):** **Português ESTÁ nos 14 idiomas** do
  benchmark (n=3 sistemas; lista: EN n=20, JA, ES, DE, **PT n=3**, FR, RU, NL, AR, IT, PL, KO, TR).
  Há **leaderboard público pt** em ttsdsbenchmark.com, atualizado por trimestre com dataset novo
  (pipeline `daisy`, anti-leakage). → dá pra **plotar nosso modelo contra baselines pt já existentes**,
  não só contra referência própria. E o método continua agnóstico: também rodamos contra a
  voz-semente carioca humana pra um score "carioca-específico".
- **Licença:** repo `ttsds/ttsds` = **MIT (verificado no GitHub)**. **Passa o gate.** Usa só modelos
  SSL públicos (WavLM/HuBERT/wav2vec2/Whisper). **Método = livre.**
- **Maturidade:** released+usável.

### 2. Win-rate / CMOS humano (receita Sesame) + TTS Arena V2 como instrumento público → **ADOPT**
- **O que é:** A/B cego — dois áudios (ex.: checkpoint novo vs baseline, ou vs. gravação real do Pedro),
  ouvinte escolhe o mais natural. Agrega em win-rate / Elo. É **a régua que a Sesame usa** e a única que
  não cai na armadilha do MOS-automático. **TTS Arena V2** (HF Space TTS-AGI) é a versão pública/Elo —
  74 modelos até mai/2026, hoje liderada por Inworld/Vocu (verificado). Nenhum modelo pt-BR nativo →
  **nicho aberto** e prova de que ninguém tem carioca no topo.
- **Fit ao nosso stack:** montar **arena carioca interna** (Pedro + 2 ouvintes girando diário, casa com a
  fase de coleta) é o passo mais barato de maior sinal. Usar **ground-truth humano como uma das pernas**
  do A/B (win-rate vs. a própria gravação real) dá o "teto" honesto.
- **Licença:** método/padrão livre; a Arena pública é referência de calibração, não dependência.
- **Maturidade:** released+usável (padrão + Space público).

### 3. MOS-preditores automáticos (UTMOS / UTMOSv2 / NISQA / DNSMOS) → **SKIP como oráculo** (WATCH como sanity solto)
- **Por quê:** arXiv **2606.19951** (verificado) prova com número que são **cegos a erro de prosódia**
  (Δ<0,1 vs humano −1,84) e **enviesados por F0 médio** (DNSMOS r=−0,79, premia voz grave). Rankear a voz
  do Pedro por eles é literalmente medir a coisa errada.
- **Uso permitido:** guard-rail grosso (detectar áudio quebrado/artefato pesado), **nunca** decisão de
  "ficou mais natural/menos robótico". Se usar, **controlar por F0 médio** (confundidor) e usar **variância
  de F0** como feature de "vivo".
- **Licença:** modelos abertos (UTMOS/NISQA permissivos), mas irrelevante — é o *uso* que está errado.
- **Maturidade:** released, porém desaconselhado como oráculo (diagnóstico jun/2026).

### 4. TTScore — prosódia + inteligibilidade reference-free (predição condicional de tokens discretos) → **TEST**
- **O que é:** dois preditores seq2seq condicionados no texto: **TTScore-int** (inteligibilidade via content
  tokens) e **TTScore-pro** (prosódia via prosody tokens). Mede a *verossimilhança* das sequências de token
  — **sem áudio de referência**. (arXiv **2509.20485**, CC-BY.)
- **Por que importa pra nós:** F0-RMSE precisa de uma referência única alinhada — e em fala **conversacional
  não existe "a" prosódia certa** (várias renderizações válidas). TTScore contorna isso: robusto a erro de
  alinhamento, acomoda múltiplas prosódias válidas. Correlação com humano **maior que F0-RMSE** e métricas de
  inteligibilidade existentes (nos benchmarks SOMOS/VoiceMOS/TTSArena). É o candidato direto pro gap **#2
  (robótico)** como métrica automática complementar ao scorecard por IU.
- **Licença:** paper **CC-BY 4.0**; release de código a confirmar (não-verificado). Método = livre.
- **Maturidade:** paper-só (set/2025) — arm de eval barato pra validar contra o nosso A/B humano.

### 5. Accent-scorecard fonológico por-segmento (arXiv 2607.01965) + GOP/MDD → **ADOPT** (instrumento a construir)
- **O que é:** treina um classificador na fala **humana carioca** pra um contraste fonológico, aplica
  cross-domain na saída do CSM e mede quanto cai **do lado errado** — com *direção do erro*. Alvos pt-BR:
  médias abertas/fechadas /e/-/ɛ/, /o/-/ɔ/; redução de átona; chiado. Família técnica = **GOP/MDD** (Goodness
  of Pronunciation / Mispronunciation Detection) do mundo CAPT. (Interspeech 2026, código no GitHub.)
- **Fit ao stack:** transforma o gap **#1 (sotaque gringo)** de "achismo" em métrica **objetiva, por-segmento,
  com direção** ("o CSM está *fechando* as médias abertas?"). É a peça publicável junto com a linha USP/Aluísio.
- **Custo/risco:** exige gravar+segmentar um **benchmark carioca humano** (Praat/MFA) e escolher o contraste.
  É eval, não treino; segmental (não prosódico).
- **Licença:** método livre; dado do paper (assamês) não serve — nós geramos o nosso. **Gate ok** (dado
  próprio, consentido).
- **Maturidade:** paper + código; instrumento a montar (arm quando houver escuta girando).

### 6. VERSA — toolkit que roda 90+ métricas num config → **ADOPT** (a plumbing)
- **O que é:** toolkit do WAVLab/ESPnet (Watanabe), 90+ métricas / 700+ variantes: WER (ASR), speaker-sim,
  F0/prosódia, PESQ, distribucionais, MOS-preditores — tudo por config, `scorer.py` + `aggregate_result.py`.
  (arXiv **2412.17667**.)
- **Fit ao stack:** não reimplementar cada métrica na mão. Aqui plugamos **WER via Whisper large-v3** (num set
  dedicado de **números/datas/siglas** → gap **#3**) e **speaker-similarity** (fidelidade da voz do Pedro) com
  um único harness. Casa com o `rate_app` como camada de cálculo por-trás do cockpit.
- **Licença:** **Apache-2.0 (verificado no GitHub).** **Passa o gate.**
- **Maturidade:** released+usável (v1.0 dez/2024).

### 7. emotion2vec+ / SER com avaliador independente → **TEST**
- **O que é:** foundation model de **Speech Emotion Recognition** (9 classes: raiva/nojo/medo/alegria/neutro/
  outro/triste/surpresa/desconhecido), embeddings por utterance/frame. Usado como **avaliador de emoção**:
  mede **UAR** (unweighted accuracy) da emoção-alvo com um SER **independente** do que condiciona o TTS —
  evita a circularidade de medir emoção com o mesmo modelo que a gerou (receita do DTRF, dossiê 84).
- **Fit ao stack:** dá pra medir **controlabilidade de emoção** (um dos 3 eixos-alvo) **sem dado emocional
  pt-BR rotulado**. Complementa MOS-3-eixos + projeção VAD. Baseline pro botão α antes de SFT→DPO→GRPO.
- **Licença:** código **Apache-2.0** (ddlBoJack); pesos "emotion2vec+" com "model-license" a confirmar
  (não-verificado). Treinado majoritariamente EN/ZH — validar transfer pra pt-BR emocional.
- **Maturidade:** released+usável (ACL 2024 + modelos "+").

### 8. SpeechJudge / audio-LLM-como-juiz (AudioJudge, JASTIN) → **WATCH**
- **O que é:** **SpeechJudge** (arXiv 2511.07931, ICLR 2026) = dataset de 99k pares com preferência humana +
  **reward model generativo (GRM) sobre Qwen2.5-Omni-7B** pra julgar **naturalidade**: 77,2% de concordância
  com humano (79,4% com scaling@10), vs Gemini-2.5-Flash <70% e Bradley-Terry 72,7%. Família = audio-LLM-judge
  (AudioJudge 2507.12705; JASTIN 2605.04505; "Audio LLMs as Descriptive Quality Evaluators" 2501.17202).
- **Por que vigiar:** é **o caminho pra automatizar o win-rate/arena** (item 2) e escala barato. E o
  **padrão** (juiz audio-LLM sobre base **Qwen2.5-Omni, que é Apache-2.0**) é reimplementável no gate.
- **Por que NÃO adotar já:** pesos do **SpeechJudge-GRM = CC-BY-NC-4.0** (verificado) → **reprova o gate de
  produto** como peso embarcado; e suporta **só EN/ZH** (sem pt-BR). Dataset com licença TBD.
- **Maturidade:** paper + pesos NC (ICLR 2026). Vigiar; se um dia automatizarmos juiz, treinar GRM próprio
  sobre Qwen-Omni (Apache) com nosso dado carioca.

---

## O "measurement stack" recomendado (o que rodar, em ordem de sinal/custo)

| Camada | Instrumento | Mede | Veredito |
|---|---|---|---|
| **Régua-mãe** | Win-rate/CMOS carioca interno (vs. ground-truth do Pedro) | "ficou mais vivo/natural?" | **ADOPT** |
| **Norte automático** | TTSDS2 (MIT; leaderboard pt público) + referência carioca própria | distância distribucional à fala humana | **ADOPT** |
| **Plumbing** | VERSA (Apache-2.0) | WER (nº/datas #3), spk-sim (voz Pedro), F0 | **ADOPT** |
| **Sotaque #1** | Accent-scorecard fonológico (2607.01965) + GOP/MDD | erro segmental + direção | **ADOPT** (construir) |
| **Prosódia #2** | TTScore (ref-free) + F0-RMSE/variância por IU | robótico, sem referência única | **TEST** |
| **Emoção** | emotion2vec+ UAR, avaliador independente | controlabilidade de emoção | **TEST** |
| **Anti-oráculo** | UTMOS/NISQA só como sanity, controlado por F0 | artefato grosso apenas | **SKIP** como decisão |
| **Fronteira** | SpeechJudge / audio-LLM-judge | automatizar o win-rate | **WATCH** |

---

## Licença / gate (resumo)
- **Passam o gate (Apache/MIT/CC-BY/CC0):** **TTSDS2 (MIT ✓)**, VERSA (Apache-2.0 ✓), TTScore (paper CC-BY;
  método livre), método do accent-scorecard e do win-rate, base Qwen2.5-Omni (Apache-2.0), código emotion2vec
  (Apache-2.0), modelos SSL do TTSDS2 (públicos). **Método de eval é sempre livre** — é medição, não embarca no peso.
- **NÃO passam como PESO embarcado (mas o método é livre):** **SpeechJudge-GRM = CC-BY-NC-4.0** (reprova),
  pesos "emotion2vec+" a confirmar. Em MODO PESQUISA, usar como ferramenta de medição é ok com rastreabilidade
  (análogo ao Whisper) — o que não pode é embutir o peso NC no produto.
- **Datasets de referência pt-BR:** o gargalo continua sendo **ter a fala humana carioca** que serve de
  referência pra TTSDS2/accent-scorecard/win-rate. A régua depende do dado, igual ao treino.

## Verificado vs inferido
- **Verificado na web (13/jul/2026):** TTSDS2 (2506.19441, componentes + ρ≈0,67; **14 idiomas COM
  Português n=3**; **licença MIT**; **ICLR 2026 Oral**; leaderboard pt público quarterly); MOS-discrepancy
  (2606.19951, cegueira a prosódia + viés F0); TTScore=arXiv 2509.20485 (ref-free, **CC-BY 4.0**, correlação
  > F0-RMSE em SOMOS/VoiceMOS/TTSArena); VERSA Apache-2.0 (65+/90+ métricas, NAACL 2025 demo); 2607.01965
  ("Towards a Phonology-Informed Evaluation of Multilingual TTS", **Interspeech 2026**, classifier-based,
  case ATR-harmony assamês); SpeechJudge (2511.07931) e GRM CC-BY-NC-4.0 EN/ZH; TTS Arena V2 pública
  (74 modelos, mai/2026); emotion2vec (9 classes, código Apache; E-SIM/TEP como métricas de emoção).
- **Não-verificado / inferido:** release de código do TTScore; **licença exata dos pesos "emotion2vec+"**
  (HF label "model-license"→FunASR; um paper cita MIT — ambíguo); transferência dos probes fonológicos
  (assamês/Indic → carioca) e disponibilidade de *prosody tokens* pt-BR pro TTScore; checkpoint XLSR pt
  "limpo" específico pro GOP/MDD.
- **Do nosso corpo de dossiês (não re-derivado):** 2606.19951 e 2607.01965 já têm digest completo em
  `research/papers/` + dossiê `84-triagem-papers-jul13.md`; SAMPA/PSST-pt (fronteira de IU) no dossiê 83.
