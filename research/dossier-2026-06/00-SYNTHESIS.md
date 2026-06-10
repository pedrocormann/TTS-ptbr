# Dossiê 00 — SÍNTESE (re-pesquisa autônoma, 2026-06-10)

> Documento-chave da rodada de junho. Consolida as frentes 10–60 deste diretório
> **já filtradas pela verificação adversarial dos fatos decisivos** (vereditos de
> 2026-06-10): tudo que foi *refutado* está corrigido aqui; tudo *incerto* está
> marcado como não-confiável. Baseline de crenças: `research/dossier/00-SYNTHESIS.md`
> (2026-05-17). Restrição dura do produto: **só Apache-2.0 / MIT / CC-BY / CC0**.

---

## 1. O QUE MUDOU desde 2026-05-17 (delta honesto)

### 1.1 O maior fato novo: a Kyutai publicou HOJE o pós-treino que íamos inventar
`kyutai/moshika-rl-seamless` (lançado 2026-06-10, **CC-BY-4.0**, gated auto,
pesos 7.69B bf16) é o Moshi pós-treinado com **GRPO + recompensas por eixo de
interatividade (pausa, turn-taking, backchannel, interrupção) + LLM-judge**,
sobre ~4.000h do Seamless Interaction (Meta). Paper: arXiv 2606.11167 (com o
autor do J-Moshi na equipe). Resultado verificado: menos interrupções indevidas
e latência de turno substancialmente menor.
**Implicação:** a crença "emoção/interatividade = base implícita + style prompt +
RL paralinguístico leve" está confirmada e agora tem receita pronta DA PRÓPRIA
KYUTAI sobre o nosso spine. Substitui Step-Audio 2 como blueprint de pós-treino.
Caveat: inglês-only; os rewards precisam de proxy pt-BR.
Fontes: https://huggingface.co/kyutai/moshika-rl-seamless · https://arxiv.org/abs/2606.11167 · https://kyutai.org/blog/2026-06-10-interactivity

### 1.2 Qwen3-TTS muda a trilha A
**Qwen3-TTS (22/jan/2026, Apache-2.0 em pesos E código, 0.6B/1.7B)** tem
**português entre as 10 línguas de SAÍDA** (verificado no tech report arXiv
2601.15621: speaker similarity 0.817 em pt), TTFA 97ms (número do vendor, no
vLLM interno deles), clone com 3s, controle de emoção por instrução NL,
tokenizer 12.5Hz e **código oficial de finetune** (`finetuning/sft_12hz.py`,
SFT single-speaker, JSONL audio/text/ref_audio). É o novo candidato #1 da
trilha A. Caveats verificados: nenhuma fonte primária diz se o pt é BRASILEIRO
(teste de escuta é gate); "cabe no Colab" é inferência (sem specs de VRAM
publicadas); bugs comunitários documentados no sft oficial → usar a versão
patchada (cheeweijie/qwen3-tts-lora-finetuning).
Fontes: https://github.com/QwenLM/Qwen3-TTS · https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base

### 1.3 Chatterbox ganhou pack DEDICADO pt-BR
`ResembleAI/Chatterbox-Multilingual-pt-br` (**MIT nos pesos**, 0.5B, T3+S3Gen V3,
"optimized for Portuguese as spoken in Brazil" — há pack pt-PT separado, o que
confirma a distinção). É o único modelo do pool com pt-BR *declarado* na fonte
primária. Chatterbox-Turbo (MIT, 350M, tags `[laugh]`/`[cough]`) é EN-only e o
"sub-200ms" do card refere-se ao serviço PAGO da Resemble, não aos pesos abertos.
Fonte: https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br

### 1.4 Mais dois stacks Apache com pt + Pocket TTS português
- **VoxCPM2** (OpenBMB, abr/2026): Apache-2.0, 2B, 30 línguas com pt na saída
  (WER 1.48% em pt no README), 48kHz, ~8GB inferência, **LoRA oficial com webUI**
  + full FT. Não é streaming-first. https://github.com/OpenBMB/VoxCPM
- **MOSS-TTS** (OpenMOSS, fev–mai/2026): Apache, 31 línguas com pt, do Nano-100M
  ao 8B, Realtime 1.7B com 180ms TTFB, docs oficiais de finetune.
  ⚠️ *Não passou pela verificação adversarial desta rodada* — tratar números
  como single-source até validar. https://github.com/OpenMOSS/MOSS-TTS
- **Kyutai Pocket TTS** ganhou modelos **portugueses dedicados** (v2.0 21/abr e
  v2.1 04/mai/2026; `languages/portuguese` 6L + `portuguese_24l`), pesos
  CC-BY-4.0, código MIT, clonagem local de qualquer wav, ~200ms em CPU
  (número auto-reportado, presumivelmente do modelo inglês 100M/6L). pt-BR vs
  pt-PT não documentado; card HF desatualizado ("English only").
  https://github.com/kyutai-labs/pocket-tts/releases

### 1.5 Vetos novos e mudanças de licença (vigiar licença DEPOIS do release)
- **Voxtral TTS** (Mistral, mar/2026, 4B, pt, 70ms): **CC-BY-NC-4.0 → VETADO**.
- **Spark-TTS-0.5B**: **RE-licenciado** de Apache para CC-BY-NC-SA (commit
  b63203d4 no HF) → saiu do universo permitido. Precedente importante: licença
  de pesos pode mudar após o release — *pinar revisão de pesos baixados*.
- **Higgs v3** (jun/2026): research/NC → veto. **Higgs v2**: Boson Community
  License — nuance verificada: PERMITE comercial <100k usuários/ano; nosso veto
  é conservador, não literal.
- **Fish S2-Pro** (melhor open-weights na arena): research license → veto.
- **Llasa**: CC-BY-NC-4.0 (corrigido: não é NC-ND) → veto igual. **Oute**: NC → veto.
- **Hibiki-Zero** (Kyutai, fev/2026, {fr,es,pt,de}→en, GRPO sem dados alinhados,
  "<1000h para língua nova de entrada"): CC-BY-NC-SA → pesos vetados; a RECEITA
  é o que vale.
- **PersonaPlex-7B-v1** (NVIDIA, jan/2026): full-duplex sobre os pesos do Moshi
  (**MoshiKO**, corrigido — não Moshika), persona por prompt de texto + voz por
  prompt de áudio, turn-taking 170ms. Código MIT; pesos **NVIDIA Open Model
  License** (comercial OK mas grant REVOGÁVEL, Seção 2.1) → fora da whitelist;
  inglês-only na saída. Valida a arquitetura Moshi; o paper (2602.06053) é a
  receita pública de persona-control para as 5 variações cariocas.

### 1.6 CSM/Sesame: empresa fechou, ecossistema comunitário abriu
- Sesame = produto consumer (Series B US$250M out/2025; app iOS público
  28/mai/2026; óculos 2027). **Sem CSM-2, sem API, sem modelo aberto novo**; repo
  oficial dormente desde 27/mai/2025 (verificado: 0 releases, 0 código de treino).
- Mas o custo de entrada do finetune do csm-1b **despencou**: treino nativo no
  HF Transformers (`CsmForConditionalGeneration`, `output_labels=True`,
  `depth_decoder_labels_ratio`), notebook oficial Unsloth em Colab T4 grátis,
  knottwill/sesame-finetune (MIT, full FT), csm-streaming (Apache, LoRA ≥12GB,
  RTF 0.28x em 4090), csm-mlx (Mac). Ressalvas da verificação: compatibilidade
  PEFT é inferência (não declarada em fonte primária); o dataset Elise dos
  notebooks Unsloth está **DISABLED no HF por DMCA** — o notebook pode falhar
  como está e o dataset é arriscado comercialmente (usar dado próprio).
- **CORREÇÃO (fato refutado):** a alegação "não existe finetune pt/es do csm-1b"
  é falsa na forma estrita — existe o LoRA multilíngue
  `Codyfederer/csm-clean-1m-multilingual-v1-adapter` (27/mai/2026, inclui 100k
  linhas pt + 100k es, qualidade fraca fora de en/tr, sem licença própria
  declarada). O que continua aberto é o nicho **finetune DEDICADO pt-BR** (o
  único repo nomeado pt-BR, dunkirkf/CSM-ptbr-mTEDx, está vazio).
- **CORREÇÃO (fato refutado):** "nenhum finetune comunitário publica métricas" é
  falso — o georgiano (NMikka/CSM-1B-Georgian) publica WER 0.1363/CER 0.0281 e
  MCD 5.43dB. E "adaptação de língua provada" é exagero: árabe admite resultado
  "below average", finlandês admite artefatos. A rota existe, mas não está
  "provada"; nossa publicação seria "primeiro pt-BR dedicado e bem-medido", não
  "primeiro com métricas".

### 1.7 Colab mudou de patamar — o LoRA do spine cabe
Colab agora oferece **A100-80GB, H100 e G4 (RTX PRO 6000 Blackwell, ~96GB VRAM,
~960 BF16 TFLOPs ≈ +50% vs A100-80)** — anúncio oficial @GoogleColab (verificado;
H100/A100-80 têm só corroboração secundária). Como o **moshi-finetune LoRA r=128
tem pico verificado de 39,6GB** e tem notebook Colab oficial, **o LoRA do spine
Moshi cabe no Colab Pro+** ($49,99/mês, 500 CU ≈ 66h de A100-80 ou 57h de G4).
RunPod/Thunder viram válvula de escape para runs >24h, não necessidade.

### 1.8 Dados pt-BR: a fronteira moveu em fala espontânea (com asteriscos)
- **TAGARELA** (mar/2026): 8.972h de podcasts pt (8.130h pt-BR) + 2.800h clean
  p/ TTS — **CC-BY-NC-SA → vetado** (verificado: o "CC-BY" do arXiv é o badge do
  preprint, não do dado; e a fonte é o corpus acadêmico Spotify). Usar só como
  eval + blueprint de pipeline (pyannote → bootstrap Whisper-FT → Vocos).
- **NILC/TaRSila**: `NURC-SP_ENTOA_TTS` com **tag MIT** (verificada na API HF;
  conflita com o NC-ND histórico do CORAA/NURC → e-mail de confirmação é a ação
  de maior alavancagem) e `nurc_tts_24khz` (320k clips 24kHz, SP+Recife, 83GB,
  **ainda sem licença**).
- **Common Voice pt 25.0**: 228,79h/187,33h validadas, CC0 mantido, com termos
  novos do Mozilla Data Collective (sem re-host, sem re-identificação); pt-BR
  domina (85k clips vs 3,4k pt-PT). Spontaneous Speech segue **sem pt**
  (correção: o SPS tem 72 línguas, não 21).
- **Emocional pt-BR commercial-safe continua ≈ 0h** → o moat da gravação
  dirigida do Pedro está intacto.
- **CORREÇÃO (fato refutado):** "TTS-Portuguese Corpus é o ÚNICO corpus pt-BR
  license-clean" é falso — **CML-TTS pt e MLS-pt (~160h) são CC-BY-4.0 e CV é
  CC0**. ⚠️ Contradição não resolvida: o dossiê 20 atribui ~1.100–1.200h pt ao
  CML-TTS; a verificação apurou ~68h (23h M + 45h F) — **verificar no OpenSLR
  146 antes de planejar CPT com esse número**.
- Regulação: PL 2338 não votado (TDM livre só p/ pesquisa; comercial ⇒
  remuneração+opt-out); **PL 1460/2026** (réplicas digitais) exige consentimento
  prévio + watermark para réplica de voz — nosso desenho já é
  compliance-by-design. Scraping de novela/filme/podcast p/ sotaque: veto total
  mantido. Novidade a monitorar: **SOTAQUE** (sotaque.ia.br, CDLA-Permissive-2.0,
  consentimento LGPD nativo) — embrionário, possível parceria.

### 1.9 Crenças de 2026-05-17 — placar
| Crença | Status jun/2026 |
|---|---|
| Spine = Moshi/Kyutai (CC-BY-4.0, LoRA-first, Mimi congelado) | **MANTIDA E REFORÇADA** (RL da Kyutai, MoshiRAG, PersonaPlex valida a arquitetura, LLM-jp-Moshi prova adaptação de língua com release Apache) |
| Co-aposta = Qwen3-Omni-30B (Apache, pt na fala) | Mantida (segue não cabendo em Colab; GH200 ok) |
| CSM-1B = componente de voz, não spine | Mantida; "sem código de treino" ficou obsoleta NA PRÁTICA (Unsloth/HF Transformers) |
| Emoção = implícita + NL prompt + RL leve | **CONFIRMADA** e commoditizada (2606.11167, GLM-TTS MIT, EMORL-TTS, Step-Audio-EditX com código SFT/DPO/GRPO p/ 3B em 12GB) |
| Cascata = piso, não destino | **SUAVIZADA**: com Qwen3-TTS (~97ms) / Pocket-TTS-pt na perna TTS, cascata vira **plano B real** (~300–500ms plausível); o teto de naturalidade segue no full-duplex (a própria Kyutai confirma ao fazer RL no modelo, não na cascata) |
| TTS license-clean p/ dado sintético = Kokoro + Chatterbox | **SUPERADA**: adicionar Qwen3-TTS, Chatterbox-pt-br, VoxCPM2, (MOSS-TTS*), Pocket-TTS-pt |

---

## 2. POOL RANQUEADO — Trilha A: voz expressiva pt-BR (finetune com a voz do Pedro no Colab JÁ)

> Critérios: licença dura OK · pt na saída (fonte primária) · código de finetune ·
> cabe em T4/L4/A100-40 · interface de emoção. **Gate universal: teste de escuta
> pt-BR vs pt-PT antes de comprometer — nenhum dos Apache declara variante BR,
> só o Chatterbox-pt-br declara.**

| # | Modelo | Licença (pesos) | pt-BR? | VRAM | Caminho de finetune | Por quê |
|---|---|---|---|---|---|---|
| **1** | **Qwen3-TTS-12Hz 1.7B (e 0.6B)** | Apache-2.0 (verificado no card + tech report) | pt nativo na saída (variante BR a validar de ouvido) | inf ~4–6GB bf16; LoRA estimado T4/L4 (sem specs oficiais; batch default 32 exige ajuste) | SFT oficial (`finetuning/sft_12hz.py`) **patchado** via cheeweijie/qwen3-tts-lora-finetuning; LoRA comunitário | Único com: pt + Apache + finetune oficial + 97ms streaming + emoção por instrução NL + voice design. Risco: pt genérico; 97ms é número de vendor |
| **2** | **Chatterbox-Multilingual-pt-br 0.5B** | MIT (verificado) | **SIM — único com pt-BR declarado** | inf ~6GB; full ~18GB (L4/A100), LoRA menos | gokhaneraslan/chatterbox-finetuning (LoRA+full, formato LJSpeech); precedente indic-LoRA prova variante de língua via LoRA | Baseline imediato + gerador de dado sintético pt-BR HOJE; watermark Perth embutido (alinha com PL 1460). Sem tags paralinguísticas (só exaggeration) |
| **3** | **VoxCPM2 2B** | Apache-2.0 (verificado, pesos e código) | pt na saída (WER 1.48% no README; variante não declarada) | **~8GB inf**; LoRA oficial com webUI | `lora_ft_webui.py` oficial + full SFT | Qualidade/48kHz para dataset e conteúdo; clonagem com style guidance. Não é streaming-first → não é a perna de latência |
| **4** | **MOSS-TTS (1.7B Local/Realtime)** ⚠️ | Apache-2.0 (single-source, **não verificado adversarialmente**) | pt (31 línguas, v1.5) | 1.7B treina em T4; 8B quantizado roda em 8GB | docs oficiais de finetune por arquitetura | Único Apache com perna realtime declarada (180ms TTFB). Validar licença+pt+números antes de subir no ranking |
| **5** | **CSM-1B (estratégia 2 estágios)** | Apache-2.0 (gated leve; usar mirror unsloth/csm-1b) | NÃO (inglês + contaminação) — é aposta de adaptação | LoRA voz: T4 (Unsloth, ≥12GB); full FT língua: L4/A100-40 | Estágio A = full FT pt-BR 50–200h (knottwill/HF Trainer, compute amortization 1/16) → Estágio B = LoRA voz do Pedro 3–10h com tags de emoção | Aposta estratégica/publicação ("primeiro csm-1b pt-BR dedicado e medido"). NÃO é o caminho mais rápido; janela existe mas há adapter multilíngue com pt desde mai/2026 |

**Rebaixados/fora:** Orpheus-3B caiu para "referência de receita de tags": a
verificação confirmou que a release multilingual **não tem pt** (12 modelos:
fr/de/es_it/zh/ko/hi), os pretrains multilingual usaram ~5.000 HORAS por língua
(a citação "few thousand samples → decente" não existe em fonte primária), os
repos são gated e vários pesos pretrain são licença Llama-3.2, não Apache.
pt-BR via Orpheus = projeto de pretrain, não finetune. Kokoro segue no kit
(dado sintético leve, 3 vozes pt-BR, sem treino oficial). Vetados por licença:
Voxtral, Higgs v2/v3, Fish S2-Pro, Spark, Llasa, Oute, IndexTTS-2, Vevo, XTTS.

---

## 3. POOL RANQUEADO — Trilha B: spine conversacional full-duplex <800ms

**A aposta Moshi se sustenta? SIM — e saiu mais forte do que entrou.** Quatro
evidências novas: (i) a Kyutai publicou o pós-treino de interatividade
(moshika-rl-seamless, CC-BY-4.0) exatamente na camada que diferencia a "Maya";
(ii) a NVIDIA validou a arquitetura construindo o PersonaPlex sobre os pesos do
Moshi; (iii) LLM-jp-Moshi-v1 (Apache-2.0, fev/2026) provou que a adaptação de
língua se repete fora do grupo original E pode ser lançada com licença
permissiva (Moshi 7B + 69kh J-CHAT + 1kh Zoom; ≥24GB VRAM); (iv) o LoRA do
moshi-finetune (pico 39,6GB) agora cabe no Colab Pro+ (A100-80/G4).

| # | Opção | Licença | pt na saída | Latência | Veredito |
|---|---|---|---|---|---|
| **1** | **Moshi 7B + moshi-finetune (LoRA-first) + receita RL 2606.11167** | pesos CC-BY-4.0; código MIT/Apache; finetune Apache | não (en) — adaptação é o NOSSO trabalho (receita J-Moshi/LLM-jp; Hibiki-Zero sugere <1000h por língua de entrada via GRPO) | ~160–200ms full-duplex | **Aposta principal mantida.** Risco central inalterado: nenhum precedente público de Moshi-pt; LoRA-only para língua nova é hipótese a testar (URO-Bench alerta catastrophic forgetting → LoRA-first correto) |
| **2** | **Qwen3-Omni-30B-A3B Instruct** | Apache-2.0 | **SIM (pt é 1 das 10 línguas de saída)** | streaming talker | Co-aposta mantida; ~70GB bf16 → GH200/SDumont, não Colab. Hedge se a adaptação do Moshi travar |
| **3** | **Cascata turbinada**: faster-whisper → LLM → Qwen3-TTS streaming / Pocket-TTS-pt | tudo Apache/MIT/CC-BY | sim (perna TTS pt) | ~300–500ms plausível (Unmute de referência: voz-a-voz <1s em produção; componentes 220–450ms) | **Promovida de "piso" a plano B real e produto v1 provável.** Estruturalmente sem overlap/backchannel verdadeiro — não é o destino |
| 4 | PersonaPlex-7B-v1 | código MIT; pesos NVIDIA OML (revogável) | não (en-only) | 170ms turn-taking | Fora da whitelist → não tocar nos pesos sem decisão explícita de política. **Usar o paper** como receita de persona/voz-por-prompt no Moshi |
| 5 | Pocket-TTS-pt (wildcard edge) | CC-BY-4.0 / MIT | pt (variante?) | ~200ms em CPU (auto-reportado) | TTS da cascata e on-device; sem código de finetune (mantenedor confirmou em mar/2026 que NÃO vai liberar — não esperar) |

**Atenção Kyutai TTS 1.6B/STT:** descartados para pt (EN/FR, sem código de
treino — recusa explícita do mantenedor —, encoder de clonagem fechado).
No repo `kyutai/tts-voices` (não-gated): usar só `voice-donations`/`voice-zero`
(CC0) e `vctk`/`cml-tts` (CC-BY); **as pastas `expresso/` e `ears/` são CC-NC —
não usar essas embeddings no produto**.

---

## 4. IMPLICAÇÕES PARA DADOS/GRAVAÇÃO (o que o Pedro grava)

**Lições novas que mudam o desenho (verificadas):**
1. **IWSDS 2026 (LLM-jp/Moshi):** as propriedades INTERACIONAIS do corpus moldam
   o comportamento do modelo; qualidade de áudio transfere direto; mismatch de
   domínio degrada coerência → gravar **diálogo espontâneo no estilo-alvo**
   (conversa casual carioca), não só leitura.
2. **Precedente Dia-1.6B pt-BR (verificado):** 144h de leitura limpa (CETUC) em
   1×4090/20h ensinou a língua mas **apagou risadas/emoções/inglês** → dataset
   com tags de emoção e fala conversacional **desde o dia 1**, e finetune sempre
   misturando dado expressivo.
3. **3 camadas de rótulo por take** (habilita as 3 interfaces de controle de uma
   vez): (i) tags de evento (`<risada>`, `<suspiro>`, "uhum"), (ii) descrição NL
   de estilo ("irônico, acelerando no final") + intensidade 1–3, (iii) tag de
   variação carioca (`[carioca:cria]`).
4. **Formato spine:** estéreo 2 canais (1 por falante) + jsonl + transcrições
   com timestamps (WhisperX gera) — exatamente o que moshi-finetune consome e o
   formato do Expresso (cujo PROTOCOLO copiamos; os ÁUDIOS são CC-NC, vetados).

**Plano de gravação (total ~25–40h úteis; regra 4:1 de tempo de trabalho):**
| Fase | Conteúdo | Volume | Âncora de evidência |
|---|---|---|---|
| 0 piloto | 200 frases Alcaim-1992 (única lista balanceada calibrada no português DO RIO — verificado) + 100 conversacionais | ~1h | valida pipeline gravação→QC→LoRA |
| 1 núcleo lido | 1.000–1.500 frases trifone-greedy (método 2402.05794) estressando /S/ coda carioca, africadas, /R/ de coda + narração | 4–6h | adaptação de voz (Orpheus: 300+ exemplos/falante; ~1h/voz de 2501.14273 — *fonte fraca, tratar como ordem de grandeza*) |
| 2 emoções | 8–10 estilos × 30–45min, protocolo EARS (3 frases fixas + descrição de imagem + freeform) + frases-âncora idênticas em todos os estilos | 5–7h | **≥30min/emoção = "Good" em MUSHRA (verificado, arXiv 2407.14056** — em línguas indianas, não pt; sem evidência pt-BR) |
| 3 sub-sotaques | 5 personas cariocas × 30–60min (léxico típico + improviso) | 3–5h | sem literatura de suporte p/ "sub-accent acting" → eval cega com nativos; risco de caricatura e de colapso das 5 variações |
| 4 conversacional | diálogo improvisado por cenário + entrevista freeform + Pedro como OUVINTE ativo (backchannels!), estéreo 1 canal/falante | 10–20h | exemplo oficial moshi-finetune = ~20h (DailyTalk, verificado) |

**Protocolo técnico:** 48kHz/24-bit, cardioide, ~1 punho do mic, ganho fixo,
picos −12/−6dB, mesma sala sempre; normalizar −23 LUFS (nunca peak); QC por
clipe: SNR ≥32dB, banda ≥13kHz, zero clipping, DNSMOS ≥3.2/NISQA ≥4.0,
verificação ASR vs script (gate <10% WER). Ferramenta: fork do
piper-recording-studio (MIT) com prompts pt-BR + gate de QC no upload; diálogos
a 2 direto no Reaper multitrack. Sessões 45–60min com 10min de pausa/h.

**Dados de terceiros no mix (license-clean):** CV-pt 25.0 (CC0), MLS-pt (CC-BY),
CML-TTS-pt (CC-BY — *confirmar horas reais*, ver §6), TTS-Portuguese (CC-BY),
Granary/YODAS-pt (CC-BY-3.0, qualidade ASR), Câmara **só transmissões ao vivo**
(CC-BY-4.0, método ParlaSpeech), 228 vozes CC0 do kyutai/tts-voices para
diversidade de conditioning. Pendente e-mail NILC: NURC ENTOA_TTS (MIT?) e
nurc_tts_24khz (sem licença). Dado sintético: Qwen3-TTS/Chatterbox-pt-br/
Pocket-TTS-pt como "usuário" no canal 2 do diálogo semi-sintético.

---

## 5. EVAL — o que adotar agora

**Fato central confirmado: não existe arena nem benchmark de TTS pt-BR.**
Construir o "ptBR-TTS-eval" é necessidade E ativo publicável (PROPOR 2027).

**Stack (com correções da verificação):**
- **Camada 0 (gate de gravação):** DNSMOS OVRL + Audiobox-Aesthetics PQ/CE
  (CC-BY-4.0) por take.
- **Camada 1 (regressão por run):** WER round-trip com **whisper-large-v3**
  (canônico) + **Parakeet-TDT-0.6B-v3** (CC-BY-4.0, pt WER ~6%; caveat do
  próprio card: treinado com **pt europeu** — pode penalizar fonética carioca);
  SIM com WavLM-SV (primário) + ECAPA-TDNN (secundário; Resemblyzer obsoleto);
  **TTSDS2** (MIT, multilíngue — *confirmar pt entre as 14 línguas antes de
  promover a métrica principal*); SER com emotion2vec+ (MIT) + cabeça
  fine-tuned em VERBO + CORAA-SER + takes emotadas do Pedro (não existe SER
  pt-BR off-the-shelf). **UTMOS/UTMOSv2 nunca para decidir checkpoint**
  (não calibrados p/ pt; inconsistência entre runs do UTMOSv2 — citação correta:
  **arXiv 2603.10904**, não 2605.23859 como circulou).
- **Camada 2 (expressividade):** port pt-BR do pipeline EmergentTTS-Eval
  (Apache-2.0, judge LALM) + subset pt do **MINT-Bench** — *rebaixado pela
  verificação*: o split pt tem só ~300 casos, variante pt não especificada,
  são 14 sistemas (não 16) e o claim de "primeiro" não se sustenta. Útil como
  teste externo barato, não como pilar.
- **Camada 3 (full-duplex):** ⚠️ **CORREÇÃO IMPORTANTE (fato refutado): a
  família Full-Duplex-Bench NÃO é MIT — o LICENSE do repo é CC BY-NC 4.0
  (código E dados)**. Para produto comercial: não redistribuir nem integrar;
  decisão recomendada = replicar as MÉTRICAS (pause handling, backchannel,
  stop/response latency, examiner em tempo real) em harness próprio com áudios
  pt-BR — que é o que faríamos de qualquer forma. HumDial @ ICASSP 2026 como
  referência adicional. Metas: stop/response latency p50 <800ms (ideal
  200–300ms), backchannel não-nulo, sem floor-holding patológico.
- **Camada 4 (gate de release):** CMOS A/B cego com ≥30 ouvintes BR + MUSHRA
  leve de sotaque ("soa carioca de onde?") + classificador de variação treinado
  no próprio dataset (se ele não separa as 5 variações, o TTS não vai separar).
- **Pronúncia regional:** BIPA (PROPOR 2026, 350k transcrições IPA com variante
  Rio) como base de G2P/teste de sotaque — ⚠️ fonte Wiktionary CC-BY-SA:
  cuidado share-alike se redistribuirmos o léxico.
- **Eval-only (NC):** TAGARELA, Expresso, EARS, DailyTalk (CC-BY-SA), CORAA.

---

## 6. RISCOS E CONTRADIÇÕES NÃO RESOLVIDAS (honestidade)

1. **pt-BR vs pt-PT é o risco nº 1 da trilha A e ninguém documenta**: Qwen3-TTS,
   VoxCPM2, MOSS, Pocket-TTS e até o MINT-Bench dizem só "Portuguese". Tudo
   depende de um teste de escuta que ainda não fizemos. Único com pt-BR
   declarado: Chatterbox-pt-br.
2. **Contradição entre frentes — licença do TAGARELA:** a frente 5
   (30-benchmarks) registra "CC-BY-4.0"; a frente 4 e a verificação adversarial
   confirmam **CC-BY-NC-SA** (o CC-BY do arXiv é o badge do preprint). Prevalece
   NC-SA: **vetado**; corrigir qualquer plano que o use como corpus de CPT.
3. **Contradição — horas pt do CML-TTS:** dossiê 20 diz ~1.100–1.200h; a
   verificação apurou ~68h. Diferença de 16× muda o plano de CPT. Resolver na
   fonte (OpenSLR 146 / paper 2306.10097) antes de orçar treino.
4. **Full-Duplex-Bench não é MIT** (CC-BY-NC): o plano de eval da frente 5
   assumia reuso direto do harness; replicação própria custa tempo não orçado.
5. **Moshi-pt continua sem precedente público.** Tudo que temos é analogia
   (japonês: J-Moshi NC, LLM-jp Apache; Hibiki-Zero "<1000h" é para língua de
   ENTRADA em tradução, não para o spine falar pt). LoRA-only para língua nova
   é hipótese; o go/no-go da Fase 2 existe exatamente para isso. O fallback
   (CPT) depende de SDumont/GH200 e de corpus espontâneo cuja licença está
   pendente (NILC).
6. **Tensão cascata vs spine entre frentes:** a frente 3 promove a cascata a
   "plano B sério (~300–500ms)"; a frente 2 mantém "piso, não teto". Síntese
   adotada: cascata = produto v1 e rede de segurança; spine = diferencial. O
   risco real é a cascata "boa o suficiente" desviar o foco do spine — decidir
   por gate, não por inércia.
7. **Números de latência são quase todos do vendor** (97ms Qwen, 180ms MOSS,
   200ms Pocket, sub-200ms Turbo = serviço pago). Nenhum medido por nós nem
   independente. O eval harness mede TTFA local antes de qualquer promessa.
8. **Licenças instáveis:** Spark provou que pesos podem ser re-licenciados após
   release; Step-Audio-EditX tem **pesos sem licença declarada** (código Apache
   não basta — não usar pesos sem confirmação da StepFun); pesos pretrain do
   Orpheus são Llama-license. Mitigação: snapshot local + registro de
   commit/licença na data do download.
9. **Dependências cinzas do caminho CSM:** tokenizer de texto Llama-3.2
   (Community License) na cadeia; mirror ungated necessário; Elise (DMCA) fora.
10. **Regulatório:** PL 2338 pode criar dever de remuneração/transparência
    retroativa-ish para treino comercial; PL 1460 (consentimento + watermark)
    nos favorece, mas exige executar o watermark de verdade (AudioSeal day-one é
    sinal, não proteção durável — re-encode por codec neural mata marcas
    pós-waveform).
11. **Sub-sotaques atuados por 1 falante** seguem sem literatura de suporte —
    risco de caricatura/colapso; plano B = doadores de voz por variação (termo
    CC0 estilo Kyutai) ou dados SOTAQUE quando houver volume.

---

## 7. FASEAMENTO RECOMENDADO (go/no-go explícitos)

### Fase 0.5 — "Escutar antes de treinar" (esta semana, custo ~R$0)
- Teste de escuta pt-BR (rubrica: sotaque, prosódia, naturalidade) em:
  Qwen3-TTS 1.7B, Chatterbox-pt-br, VoxCPM2, Pocket-TTS `portuguese_24l`
  (+ MOSS se sobrar tempo) — inclusive clone zero-shot com 10min do Pedro.
- E-mail ao NILC (tag MIT do ENTOA_TTS + licença do nurc_tts_24khz).
- Gravação piloto: ~1h (200 frases Alcaim + 100 conversacionais) no protocolo §4.
- Confirmar horas reais do CML-TTS-pt (OpenSLR 146) e pt no TTSDS2.
- Mimi pt-BR round-trip freeze test (pendência herdada do plano de maio).
- **GO/NO-GO A:** ≥1 modelo Apache/MIT soa aceitavelmente brasileiro → ele é o
  candidato #1 da Fase 1. Se NENHUM soar BR → Chatterbox-pt-br finetunado vira
  o caminho de menor risco e o CSM Estágio A sobe de prioridade.

### Fase 1 — "Voz do Pedro v0" (semanas 1–4, Colab Pro/T4-L4, <50 CU)
- Gravar núcleo lido (4–6h) + começar emoções (2–3h com 3 camadas de rótulo).
- LoRA da voz do Pedro no vencedor da 0.5 (receita patchada Qwen3 OU
  chatterbox-finetuning); em paralelo, LoRA CSM-1B via Unsloth com dado próprio
  (NUNCA Elise/DMCA) como 2ª opinião barata.
- Eval Camadas 0–1 rodando em CI (WER 2-ASR, SIM, TTSDS2, DNSMOS).
- **GO/NO-GO B:** SIM (WavLM-SV) do finetune > clone zero-shot do mesmo modelo
  E CMOS interno favorável E WER round-trip ≤ baseline do modelo base → emoções
  e variações na Fase 2. Caso contrário: mais/melhor dado antes de mais treino
  (diagnóstico via 2603.10904: diversidade do dado governa o ganho).

### Fase 2 — "Expressividade + spine smoke" (meses 2–3, Colab Pro+, ~150–300 CU)
- Completar emoções (≥30min/emoção) + 5 variações v0 (voice-prompt) e v1 (tag
  textual); classificador de variação como gate.
- DPO leve de emoção (pares julgados por SER-pt + Pedro); GRPO só depois do
  harness confiável (lição RRPO: sem reward bom, RL amplifica viés).
- Começar dataset estéreo conversacional (meta 10h) + diálogo semi-sintético.
- **Smoke do spine:** moshi-finetune LoRA no Colab A100-80/G4 com ~1h estéreo
  pt-BR (preset oficial inalterado) → pipeline + queda de loss + amostras.
- **GO/NO-GO C (decisão de spine):** se o LoRA do Moshi mostra pt-BR emergente
  inteligível (mesmo ruim) → escalar dados/LoRA na Fase 3. Se produz colapso/
  inglês persistente → orçar CPT no SDumont (números J-Moshi como teto) E
  lançar produto v1 na cascata turbinada sem esperar o spine.

### Fase 3 — "Spine pt-BR + produto" (meses 3–6, Colab Pro+ → SDumont GH200)
- Trilho produto: cascata turbinada (faster-whisper → LLM → TTS da Fase 1/2)
  com watermark + consentimento (PL 1460 compliance-by-design); medir p50 real.
- Trilho spine: LoRA Moshi com 10–20h estéreo (paridade com o exemplo oficial);
  se gate C mandou, CPT no GH200; depois **RL de interatividade à la
  arXiv 2606.11167** com rewards proxy pt-BR (pausa/turno/backchannel medidos
  no nosso harness) + persona-control à la PersonaPlex (paper, não pesos).
- Publicações alavancáveis: ptBR-TTS-eval; primeiro csm-1b/TTS pt-BR dedicado
  **com métricas completas** (o georgiano já publicou WER — nosso diferencial é
  o pacote pt-BR + MOS + protocolo).
- **GO/NO-GO D (release):** Camada 4 (CMOS ≥30 ouvintes BR + sotaque) + p50
  <800ms medido + checklist de licença/consentimento/watermark fechado.

---

## Apêndice — Mapa de fontes por frente
- Frente 1 (Sesame/CSM): `10-sesame-csm.md`
- Frente 2 (Kyutai): `11-kyutai.md`
- Frente 3 (pool de modelos): `12-model-pool.md`
- Frente 4 (dados pt-BR): `20-data-ptbr.md`
- Frente 5 (benchmarks/eval): `30-benchmarks-eval.md` ⚠️ corrigir lá: TAGARELA é
  CC-BY-NC-SA (não CC-BY) e Full-Duplex-Bench é CC-BY-NC (não MIT)
- Frente 6 (Colab/compute): `40-colab-compute.md`
- Frente 7 (emoção/sotaque): `50-emotion-accent.md`
- Frente 8 (protocolo de gravação): `60-recording-protocol.md` ⚠️ corrigir lá:
  TTS-Portuguese NÃO é o "único" corpus pt-BR license-clean (CML-TTS/MLS/CV)
- Crenças anteriores: `../dossier/00-SYNTHESIS.md` (2026-05-17)

*Síntese escrita em 2026-06-10 com os vereditos da verificação adversarial
aplicados: 5 fatos refutados corrigidos no corpo (finetunes csm pt/es; métricas
dos finetunes csm; licença do Full-Duplex-Bench; exclusividade do
TTS-Portuguese; contagem de línguas do CV-SPS) e 2 incertos rebaixados
(MINT-Bench como pilar; citação do UTMOSv2 + claim "1h/voz").*
