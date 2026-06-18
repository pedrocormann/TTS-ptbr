# EXPERIMENTS-próximos — Trilha A (Treino 2)

**Data:** 2026-06-17  
**Base:** Treino 1 finalizado (voz do Pedro PROVADA: WER 12%, para 14/14, voz 3.4/5)  
**Objetivo:** Atacar os 3 maiores problemas do Treino 1 com ablações systematicas.

---

## Diagnóstico do Treino 1

| Problema | Frequência | Origem | Solver |
|---|---|---|---|
| **Sotaque gringo #1** | 28× | Pronúncia errada (fronema, não palavra) | G2P pt-BR, base carioca |
| **Entonação robótica #2** | 18× | Prosódia monótona (mono-emoção) | Mais dados variados, emoção G2 |
| **Números quebram** | 3 trechos graves | Front-end (texto cru) | Normalização `text_frontend()` |
| Carioca não transfere | 2/14 "sim" | Base CML (formal) domina | Trocar por base carioca |

---

## Roadmap: ordem de execução

```
QUICK-WIN (GPU:none)
  └─→ normalize_ptbr.py → wirar text_frontend em build_prep
      [Entrada: JÁ CONSTRUÍDO; integração: 5 min]

BASELINE LIMPO (GPU: ~90 min / stage B final)
  └─→ 1. Rodar curate_app.py (UI interativa, ~1h manual)
      2. Re-treinar stage_b_final no dataset curado
      └─→ checkpoint: `runs/b2_clean/final`

ABLAÇÕES (GPU: ~90 min × N arms)
  └─→ b2_g2p ........................ fonemizar entrada
  └─→ b2_prop_30_70 ................. 30% base, 70% Pedro
  └─→ b2_prop_50_50 ................. 50/50 (controle)
  └─→ b2_prop_100_pedro ............. 100% Pedro (diagnóstico)
  └─→ b2_base_carioca ............... trocar base por NURC-MIT
```

**Total GPU:** ~450 min (~7h5 em A100-80 ou ~23h em L4)

---

## Passo 1: QUICK-WIN — Normalizar números (SEM GPU)

**Tempo:** 5 min  
**O que:** Wirar `text_frontend(normalize_numbers=True)` no build_prep de train_bateria.py  
**Por quê:** Hard-01 (Treino 1) falhou em "CEP 22290-160", "protocolo 4-7-9", "R$ 1.350,90"

### Edição em `train_bateria.py`

Localizar a função `build_prep()` (linha ~111):

```python
def build_prep(processor, max_audio):
    # ... comentários existentes ...
    def prep(ex, idx):
        arr = np.asarray(ex['audio']['array'], dtype=np.float32)[:CLIP]
        # ANTES (linha ~140, entrada direta ao processor):
        # conv = [{'role': spk(ex, idx), 'content': [{'type':'text','text':str(ex['text']).strip()}, ...]}]
        
        # DEPOIS (wirar text_frontend):
        texto_normalizado = text_frontend(str(ex['text']).strip(), normalize_numbers=True, g2p=None)
        conv = [{'role': spk(ex, idx), 'content': [{'type':'text','text':texto_normalizado},
                                                   {'type':'audio','path':arr}]}]
        # ... resto do código igual ...
```

**Validar:** Após editar, rodar:
```bash
python -m tools.text.normalize_ptbr
# Esperado: "O CEP é 22290-160 e custa R$ 1.350,90." → 
#           "O CEP é vinte e dois mil duzentos e noventa cento e sessenta e custa mil trezentos e cinquenta reais."
```

**Impacto no treino:** O CSM recebe "R$ 1.350,90" → "mil trezentos e cinquenta reais" — não recebe números crus. Esperado: hard-01 deixa de quebrar naqueles 3 trechos.

---

## Passo 2: BASELINE LIMPO — Curação de dataset

**Tempo:** ~1h (manual) + ~90 min (GPU treino)  
**O que:** Rodar curate_app.py, marcar clipes ruins, re-treinar.  
**Por quê:** Treino 1 usou transcribed.jsonl (Whisper ~5-10% erro + fragmentos); limpar melhora a qualidade.

### 2a. Rodar curate_app.py

```bash
cd /Users/pedrocormann/Downloads/TTS-ptbr
python tools/rate/curate_app.py --audio-dir <path_aos_362_clipes> --port 8765
```

A app abre em `http://localhost:8765`:
- Lista os 362 clipes da voz do Pedro
- Exibe waveform + transcrição (Whisper)
- UI: ouve clique a clique, corrige transcrição, marca MANTER/DESCARTAR, flags problema
- Salva em `tools/rate/transcribed_clean.jsonl`

**Flags esperadas:** sobreposição (crosstalk), ruído/chiado, corte, <2s, >12s, transcrição errada.

**Meta:** descartar ~20-30% (keep ~240-280 clipes limpos = alvo de qualidade)

### 2b. Re-treinar Stage B sobre dataset limpo

Editar `train_voice.py` (ou passar flag CLI):

```bash
python runpod/train_voice.py \
    --dataset tools/rate/transcribed_clean.jsonl \
    --exp-name b2_clean \
    --minutes 90 \
    --push-hub pedrocormann/tts-ptbr-bateria
```

**O que acontece internamente:**
1. Carrega BASE-PT do Treino 1 (melhor vencedor do grid A1)
2. Aplica `text_frontend()` em CADA clipe do dataset limpo
3. LoRA novo (r=64) com LR 5e-5 por 90 min
4. Eval: WER round-trip no benchmark_ptbr, spk-sim vs referência

**Esperado:** WER ~15-16% (vs 12% sujo = um pouco pior, é normal em dataset menor/limpo).

**Gate:** spk-sim ≥0.70, WER <20%, escuta cega prefere vs B1.

---

## Passo 3: ABLAÇÕES — rodas em paralelo/sequência

Cada ARM reutiliza a mesma receita (STAGE_B) mas com variações na entrada ou dataset.

### 3a. b2_g2p — fonemizar entrada

**Hipótese:** Condicionar em fonemas melhora alinhamento/pronúncia, reduz "gringo" (arXiv 2410.14997).

**O que:** Antes de passar o texto pro CSM, executar G2P pt-BR.

**Entrada esperada:**
```
"Olá, tudo bem com você?"
  ↓ text_frontend(g2p=g2p_ptbr)
"O la tu du bem kom vo sɛ [IPA-phonemes]"
```

**Implementação:**
1. Instalar candidato G2P:
   ```bash
   pip install g2p-pt  # rule-based, CC-BY
   # ou
   pip install g2p_en phonemizer  # com custom lexicon pt-BR
   ```

2. Em `experiments.py`, linhas ~95:
   ```python
   def _g2p_ptbr(text):
       import g2p_pt  # ou phonemizer
       # TODO: integrar real — por enquanto placeholder
       return text
   ```

3. Rodar ARM:
   ```bash
   python runpod/train_voice.py \
       --exp-name b2_g2p \
       --dataset tools/rate/transcribed_clean.jsonl \
       --enable-g2p \
       --minutes 90
   ```

**Eval metrics:** WER (não deve regredir), spk-sim (≥0.70), perceptual 'soa nativo' (via rate_app).

**Gate:** Perceptual 'nativo' sobe vs b2_clean; WER não piora.

### 3b. b2_prop_30_70 / b2_prop_50_50 / b2_prop_100_pedro — ablação de proporção

**Hipótese:** Aumentar peso da voz do Pedro (vs base CML formal) deixa prosódia mais natural + sotaque carioca transfere.

**O que:** Durante o treino Stage B, variar a proporção base:Pedro em cada época.

**Variações:**
```
b2_prop_50_50    | 50% CML + 50% Pedro  | baseline (controle)
b2_prop_30_70    | 30% CML + 70% Pedro  | maior peso Pedro (esperado: prosódia melhor)
b2_prop_100_pedro| 0% CML + 100% Pedro  | extremo (esperado: overfit/WER >20%)
```

**Implementação:**
1. Em `train_voice.py`, após carregar dataset, fazer weighted sampling:
   ```python
   base_rows = load_dataset('ylacombe/cml-tts', ...)  # N exemplos
   pedro_rows = load_dataset(transcribed_clean.jsonl)  # M exemplos
   
   # Mix por epoch (simples: concatena com proporção)
   mixed = base_rows[: int(len(base_rows) * 0.5)] + pedro_rows[: int(len(pedro_rows) * 0.5)]
   # ou: RandomSampler com weights [0.5, 0.5]
   ```

2. Rodar:
   ```bash
   python runpod/train_voice.py --exp-name b2_prop_30_70 --base-weight 0.3 --pedro-weight 0.7 --minutes 90
   ```

**Esperado:**
- b2_prop_50_50: WER ~15%, nativo score ~2.9/5 (baseline)
- b2_prop_30_70: WER ~15-17%, nativo score +0.2 vs 50/50 (prosódia melhora)
- b2_prop_100_pedro: WER >20%, diagnóstico: a base CML é crítica pra manter português

### 3c. b2_base_carioca — trocar base por NURC-MIT

**Hipótese:** Base CML (formal, paulista?) bloqueia sotaque carioca; trocar por base carioca espontânea melhora transferência.

**O que:** 
1. Confirmar licença NURC-MIT com NILC (via e-mail)
2. Rodar Estágio A em NURC em vez de CML
3. Congelar o modelo pt-BR carioca
4. Stage B sobre essa base

**Edição em `train_bateria.py`:**

Localizar `load_source()` (linha ~99):

```python
def load_source(source, clips):
    if source == 'cml':
        rows = _stream_take('ylacombe/cml-tts', 'portuguese', 'text', clips)
    elif source == 'nurc':  # NOVO
        # TODO: substituir por NURC-MIT após confirmação de licença
        # rows = _stream_take('nilc/nurc_tts_24khz', ..., clips)  # placeholder
        rows = _stream_take('ylacombe/cml-tts', 'portuguese', 'text', clips)  # fallback seguro
    # ... resto igual ...
```

**Rodar:**
```bash
# Passo 1: Stage A em NURC (gera BASE-CARIOCA)
python runpod/train_bateria.py --experiments A1_nurc --per-exp-min 180

# Passo 2: Stage B sobre BASE-CARIOCA
python runpod/train_voice.py \
    --exp-name b2_base_carioca \
    --base-model runs/battery_A1_nurc/final \
    --minutes 90
```

**Esperado:**
- nativo score +0.5-1.0 vs b2_clean (sotaque transfere melhor)
- sotaque_carioca_classifier ≥70% (modelo consegue discriminar)
- WER ~15-17% (não regride)

---

## Passo 4: Avaliar & ranking — rate_app (Treino 2)

Após rodarem todas as ARMs:

1. Gerar áudios do benchmark_ptbr para cada ARM:
   ```bash
   # Para cada ARM:
   cd /Users/pedrocormann/Downloads/TTS-ptbr
   python eval/gen_benchmark.py --model runs/b2_clean/final --audio-dir runpod_samples/treino2/b2_clean/gen
   python eval/gen_benchmark.py --model runs/b2_g2p/final --audio-dir runpod_samples/treino2/b2_g2p/gen
   # ... etc
   ```

2. Abrir rate_app com Treino 2:
   ```bash
   python tools/rate/rate_app.py --run treino2
   ```

3. Classificar os áudios (14×6 = 84 clipes, ~1h):
   - Nativo vs gringo: escuta cega, nota 1-5
   - Tags: sotaque gringo, fonema errado, entonação, artefato, etc.
   - Insights: qual ARM atacou melhor cada problema?

4. Exportar feedback.jsonl:
   ```bash
   # Na aba Insights → download feedback.jsonl
   ```

---

## Passo 5: Decisão & próxima fase

**Critério de sucesso:**

| ARM | Gate | Se passar |
|---|---|---|
| b2_clean | spk-sim ≥0.70, WER <20% | candidato a baseline (é o novo b1) |
| b2_g2p | nativo +0.3 vs b2_clean, WER ≤ -5% | G2P pronto, entra no pipeline |
| b2_prop_30_70 | nativo +0.2 vs 50/50 | aumentar peso Pedro em F2 |
| b2_prop_100_pedro | diagnóstico (WER cai muito?) | valida importância da base |
| b2_base_carioca | nativo +0.5, carioca-classifier ≥70% | trocar base em A1 |

**Próxima fase (F2 — emoções):**
- Vencedor de Treino 2 vira baseline pro Stage B + G2 (emoção)
- Gravar 8 estilos × 3 intensidades (~5-7h)
- Ablação: SFT + DPO leve

---

## Matriz rápida — comandos prontos

```bash
# Smoke-test (validar ARMs)
python runpod/experiments.py

# Rodar 1 ARM
python runpod/train_voice.py --exp-name b2_clean --dataset tools/rate/transcribed_clean.jsonl --minutes 90

# Rodar 3 ARMs em paralelo (RunPod 3 pods, ou sequência)
python runpod/train_voice.py --exp-name b2_g2p --minutes 90 &
python runpod/train_voice.py --exp-name b2_prop_30_70 --minutes 90 &
python runpod/train_voice.py --exp-name b2_prop_100_pedro --minutes 90 &
wait

# Avaliar com rate_app
python tools/rate/rate_app.py --run treino2

# Exportar resultados
# (na aba Insights, botão "Download feedback.jsonl")
```

---

## Notas técnicas

### Text_frontend() = ponto de injeção único

```python
# recipe.py (linha 53)
def text_frontend(text, normalize_numbers=True, g2p=None):
    """PONTO DE INJEÇÃO ÚNICO — use no treino (build_prep) E na inferência."""
    s = str(text).strip()
    if normalize_numbers:
        s = normalize_ptbr(s)  # R$ 1.350,90 → mil trezentos e cinquenta reais
    if g2p is not None:
        s = g2p(s)  # Olá → O la (IPA/SAMPA)
    return s
```

**Hoje:** normalize_numbers=True (quick-win)  
**Depois:** g2p=g2p_ptbr (ablação G2P)

### WER round-trip = métrica objetiva

```
Gerado (TTS) → ASR (whisper) → comparar vs ref
Exemplo: 
  ref:  "O CEP é 22290-160"
  gen:  "O CEP é vinte e dois mil..." (normalizado)
  asr:  "o cê pê é vinte e dois mil..." (ASR ouve)
  WER:  comparar ref vs asr
```

**Esperado:** Normalização → WER não piora muito (hard-01 fica OK).

### Proporção base/Pedro = variável de controle

No collator/sampler, fazer sampling ponderado:
```python
# Simples: concatena proporção fixa
base_idxs = np.arange(len(base_rows))
pedro_idxs = np.arange(len(pedro_rows))

# Mix 30% base, 70% Pedro
mixed_idxs = np.concatenate([
    np.random.choice(base_idxs, size=int(0.3 * batch_size), replace=True),
    np.random.choice(pedro_idxs, size=int(0.7 * batch_size), replace=True),
])
np.random.shuffle(mixed_idxs)
```

Ou usar `torch.utils.data.WeightedRandomSampler` com weights=[0.3, 0.7, 0.3, 0.7, ...].

---

## Checklist executivo

- [ ] Editar `train_bateria.py`: wirar `text_frontend()` no build_prep
- [ ] Rodar curate_app.py e gerar `transcribed_clean.jsonl`
- [ ] Re-treinar b2_clean (Stage B sobre dataset curado)
- [ ] Rodar b2_g2p, b2_prop_30_70, b2_prop_100_pedro (3 ARMs paralelo)
- [ ] (Opcional) Confirmar NURC-MIT e rodar b2_base_carioca
- [ ] Gerar benchmark_ptbr para cada ARM (~6 modelos × 14 frases)
- [ ] Classificar em rate_app → Insights
- [ ] Rankear por nativo score + WER + tags
- [ ] Decidir vencedor → baseline pro F2

---

## Timeline estimado

| Fase | Tempo | Bloqueador | Nota |
|---|---|---|---|
| Curação manual (curate_app) | 1h | nenhum | GPU: nenhuma |
| b2_clean re-treino | 90 min | HF model | ~$0.20 em L4 |
| b2_g2p, prop×3 (paralelo) | 90 min × 3 | G2P impl | se paralelo em 3 pods: 90 min total |
| b2_base_carioca (se NURC) | 180+90 min | NURC licença | e-mail NILC: resposta ~1-2 dias |
| Avaliação (rate_app) | 1h | nenhum | GPU: nenhuma |
| **TOTAL** | **~9h** (serial) | **NURC** | **~3h se paralelo 3 pods** |

---

## Referências

- **Recipe validada:** `runpod/recipe.py` (STAGE_B = receita do Treino 1 vencedor)
- **Normalização:** `tools/text/normalize_ptbr.py` (pronto; sem deps)
- **Curação:** `tools/rate/curate_app.py` (pronto; UI web)
- **Experimentos:** `runpod/experiments.py` (novo, declarativo)
- **Treino Stage B:** `runpod/train_voice.py` (existente, precisa de --enable-g2p flag)
- **Trilha map:** `tools/rate/trilha_map.json` (atualizar com Treino 2 resultados)
