# RUNBOOK: Maya-BR v0 (Cascata Conversacional em PT-BR)

**Data:** 2026-06-17  
**Status:** Não testado end-to-end em produção (scaffold funcional + componentes validados individualmente)  
**Objetivo:** Reproduzir a experiência conversacional da Sesame Maya — cascata VAD → ASR → LLM → CSM com áudio-contexto — no Mac do Pedro com latência <800ms p50 e qualidade ≥ Moshi-pt.

---

## SUMÁRIO EXECUTIVO

A Maya-BR v0 é uma cascata engenheirada que "simula" duplex completo combinando 4 componentes:

1. **VAD (silero-vad + SmartTurn v3)** — detecta fim de turno com 2 estágios
2. **ASR (faster-whisper)** — transcrição PT-BR streaming
3. **LLM plugável** — geração de resposta (Sabiá, Gemini Flash, sglang OpenAI-compat)
4. **TTS (CSM-1B finetunado em PT-BR)** — síntese condicionada em áudio-contexto

**Cascata = **mic → turno completo (VAD) → ASR → LLM (stream por sentença) → TTS (cada sentença) → speaker → (barge-in detecta próximo turno)**

### Hipótese (REPLAN §155-159)

Esta cascata ≥ Moshi-pt em preferência humana com latência aceitável (<800ms p50) porque:
- **Áudio-contexto do CSM** sustenta persona/emoção sem tags (à la Maya real, confirmado OSINT Sesame)
- **Turn-taking incremental** (não turno-por-turno) com barge-in aparenta full-duplex
- **LLM separado** permite controle fino de conteúdo independente da voz
- **CSM-1B é suficiente** (confirmado Treino 1: WER 12%, 14/14 paradas, voz 3.4/5)

### Gate de Decisão (F4, REPLAN §4)

**Maya-BR v0 vira a abordagem principal se:**
- Latência p50 percebida <800ms (medida com gravação de tela)
- Preferência humana ≥ Moshi-pt (escuta cega, 3 cariocas nativos)
- Turn-taking sem regressão (backchannel natural, sem falsos turnos)
- Persona consistente (áudio-contexto funciona)

---

## PRÉ-REQUISITOS

### 1. **CSM-pt-BR com voz (Estágio B final validado)**

Já existe em `runs/stage_b_final/final` (Treino 1, 2026-06-17):
- Base PT: CML-TTS + LoRA pt (LR 5e-4, 180min) → WER 21%
- Voz do Pedro: LoRA novo (LR 5e-5, 90min) mergido na base PT → WER 12% round-trip, 14/14 paradas
- Métricas: spk-sim 0.71 (WavLM-SV), TTSDS2 confirmada (MIT-validada 14 línguas)
- **Risco residual:** mono-emoção de 1 sessão (G1 núcleo + G2 emoções pendentes)

**Próximos passos paralelos (não bloqueiam v0):**
- G1 (4-6h core): estabiliza o Estágio B, melhora WER de 12% → 8-10% esperado
- G2 (8 estilos): controle de emoção (SFT + DPO leve, sem RRPO frágil — arXiv 2606.05367 UNESP prova que aritmética linear NÃO controla emoção em TTS-LM)
- Dataset curado: rodar `curate_app` nas 362 frases do Pedro (corrigir Whisper errors, descartar ruído) — pré-requisito do Estágio B v2

### 2. **LLM pt-BR plugável (OpenAI-compatible)**

Adapter pronto em `src/duplex/llm.py`; escolher um dos:

| LLM | Endpoint | Latência | Latência+LLM | Token limit | Custo | Status |
|---|---|---|---|---|---|---|
| **Gemini Flash** | https://generativelanguage.googleapis.com/v1beta/openai/ | 80-150ms | 150-250ms | 4M | Free tier (15 req/min) | ✅ Ready |
| **Sabiá** (HuggingFace) | sglang ou local vLLM | 100-300ms | 200-400ms | 2k | Livre | ✅ Recomendado |
| **sglang** (SDumont ou local) | http://localhost:30000/v1 | 50-100ms | 100-200ms | Configurável | Infra | ⚠️ Setup |
| **Maritaca** (HF) | https://api.maritaca.ai/chat/completions | 150-300ms | 250-400ms | 4k | ~0,50/1M tokens | ✅ Ready |

**Recomendação:** Começar com **Gemini Flash** (sem setup, tier free suficiente pra prototipagem). Persona em `src/duplex/persona_ptbr.txt` (system prompt que ensina respostas curtas, orais, com backchannels).

**Lacuna identificada (OSINT r2, REPLAN §112-125):** o LLM só vê TEXTO da transcrição — toda a paralinguística do áudio (raiva, ironia, ênfase) se perde antes do LLM. Oportunidade futura: backbone multimodal (GRU/Transformer) que recebe áudio+texto.

### 3. **Turn-engine com VAD + barge-in (scaffold funcional)**

Já implementado em `src/duplex/turn_engine.py`:
- **Silero-VAD** (streaming 16k, FRAME=512=32ms): threshold ≥0.5 detecta fala
- **SmartTurn v3** (Pipecat BSD-2, ONNX 8MB): semântico 8s últimos 8s → sigmoid; >0.5 = turno completo
  - Validado em PT: **95.4% acurácia** no repo oficial
  - CPU ~12-95ms por chamada
- **Player + barge-in**: playback em thread, flag `_interrupted` quando VAD alta durante SPEAKING
  - Latência de interrupção: <1 buffer (~80ms, dependente de blocksize do sounddevice)
  - Echo-cooldown 350ms pós-playback (mata reverberação em speaker)
  - Half-duplex default (SEM fones = impossível barge-in real; gate alto prob ≥0.85)
  - Full-duplex (COM fones): gate normal prob ≥0.5

**Risco:** sincronização entre VAD input e output player em half-duplex; feedback pode confundir o modelo. Mitigado: cooldown, gateway alto, e "não usar speaker sem fones em barge-in."

### 4. **ASR (faster-whisper, validado)**

Adapter em `src/duplex/asr.py`:
- Modelo: **whisper-small** (MIT, CTranslate2, rápido)
- Entrada: áudio 16kHz mono (turn_engine entrega)
- Saída: string PT-BR transcrição
- Latência: 60-200ms (dependente da duração do turno)
- WER baseline: **21%** em corpus CML-TTS limpo
  - Round-trip (synth → ASR → comparar texto) valida inteligibilidade
  - Nota: Sesame usa `faster-whisper-plus` (custom) mas spikes da OSINT provam que stock roda

**Decisão de design:** sem `vad_filter=True` (já feito pelo turn_engine), `beam_size=1` (latência mínima).

---

## SETUP E INSTALAÇÃO

### 1. Clone + ambiente

```bash
cd /Users/pedrocormann/Downloads/TTS-ptbr
python -m venv venv_maya
source venv_maya/bin/activate
pip install --upgrade pip
```

### 2. Dependências core

```bash
# Áudio + VAD + ASR
pip install sounddevice soundfile numpy scipy
pip install torch torchaudio  # ou usar miniconda pra GPU
pip install silero-vad faster-whisper onnxruntime
pip install transformers huggingface-hub

# LLM + TTS
pip install openai httpx  # OpenAI client (funciona com qualquer endpoint compat)
pip install torchaudio  # pro CSM

# CSM (opcionalmente MLX pra M2 smoke-test)
pip install mlx mlx-lm  # ou torch conforme HW
```

### 3. Variáveis de ambiente (Mac do Pedro)

```bash
# .env ou export no shell
export GEMINI_API_KEY="seu-api-key-do-gemini"  # https://ai.google.dev
export HF_TOKEN="seu-huggingface-token"         # https://huggingface.co/settings/tokens
```

**Se usar Sabiá local (sglang):**
```bash
# Terminal 1: rodando o servidor
python -m sglang.launch_server --model-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 --port 30000 --mem-fraction-static 0.6

# Terminal 2: script conversa
export LLM_BASE_URL="http://localhost:30000/v1"
export LLM_MODEL="TinyLlama-1.1B-Chat-v1.0"
```

### 4. Baixar/preparar checkpoints

#### CSM-1B base pt (stage_b_final)

```bash
# Já existe no repo se o Treino 1 rodou
ls runs/stage_b_final/final/
# Esperado: adapter_config.json, adapter_model.bin (LoRA) + config.json (base CSM)

# Ou baixar da HF (se publicado no futuro)
# huggingface-cli download seu_org/csm-1b-pt-stage-b-final --local-dir runs/stage_b_final/final
```

#### Silero-VAD + SmartTurn v3

Baixados automaticamente pelo código (HuggingFace hub), primeiro uso ~10s (cache).

```python
# Se offline, pre-download:
from silero_vad import load_silero_vad
model = load_silero_vad()  # ~50MB, cache em ~/.cache/torch

from huggingface_hub import hf_hub_download
path = hf_hub_download("pipecat-ai/smart-turn-v3", "..onnx")  # ~8MB
```

---

## RODAR (CLI)

### Versão mais simples (Gemini Flash, CPU)

```bash
python -m src.duplex.chat_loop \
  --tts pocket \
  --llm-base-url "https://generativelanguage.googleapis.com/v1beta/openai/" \
  --llm-model "gemini-2.0-flash" \
  --llm-key "$GEMINI_API_KEY"
```

**Saída esperada:**
```
⏳ carregando modelos…
🎙️  Maya-BR v0 · tts=pocket · fale alguma coisa (Ctrl-C sai)

(ouve por 600ms pós-silêncio, transcreve, gera resposta, sintetiza)
🧑 {texto do usuário}
🤖 {resposta do agente}
   ⏱ asr=0.12s · llm₁=0.18s · tts₁=0.21s · total→1ºaudio=0.51s
```

### Com CSM-pt-BR (GPU recomendada, inferência em 24kHz)

```bash
python -m src.duplex.chat_loop \
  --tts csm \
  --model-dir runs/stage_b_final/final \
  --voice-text "Olá, tudo bem?" \
  --llm-base-url "https://generativelanguage.googleapis.com/v1beta/openai/" \
  --llm-model "gemini-2.0-flash" \
  --llm-key "$GEMINI_API_KEY" \
  --barge-in  # SÓ se tiver fones (senão feedback)
```

### Com Sabiá local (sglang, latência mais baixa)

```bash
# Terminal 1: servidor sglang
python -m sglang.launch_server --model-path HuggingFaceH4/zephyr-7b-beta --port 30000

# Terminal 2: conversa
python -m src.duplex.chat_loop \
  --tts csm \
  --model-dir runs/stage_b_final/final \
  --voice-text "Olá, tudo bem?" \
  --llm-base-url "http://localhost:30000/v1" \
  --llm-model "default" \
  --llm-key "x"
```

### Validação: lista de mic

```bash
python -c "import sounddevice; print(sounddevice.query_devices())"
# Anota o índice do mic que quer (ex: 16) e passa --device 16
```

---

## ARQUITETURA (ref. rápida)

```
src/duplex/
├── chat_loop.py        # Main: orquestra VAD→ASR→LLM→TTS por turno
├── turn_engine.py      # VAD (silero + SmartTurn), Player, barge-in
├── asr.py              # faster-whisper wrapper
├── llm.py              # OpenAI-compat client, streaming por sentença
├── tts_adapter.py      # Factory (pocket|chatterbox|csm|qwen3) + contexto audio
├── persona_ptbr.txt    # System prompt (respostas curtas, orais)
└── README.md           # Descrição técnica breve
```

**Fluxo por turno:**

```python
# listen_turn() — bloqueia até VAD+SmartTurn decidem "fim de turno"
user_audio, meta = engine.listen_turn()  # 16kHz, mono

# ASR
text = asr.transcribe(user_audio)  # → "olá, como você está?"

# Contexto: user_audio entra no CSM (resampled 24k)
tts.add_context(role="1", text=text, audio=audio_24k)  # role 1=user

# LLM streaming por sentença
for sent in llm.reply_stream(text):  # → "Oi!", "Tudo bem com você?"
    wav, _ = tts.synth(sent)         # CSM sintetiza cada sentença
    parts.append(wav)                 # áudio-contexto implícito: últimos 4 turnos

# Playback com barge-in monitorado
full = np.concatenate(parts)
interrupted, frac_heard = engine.speak(full)  # Toca enquanto escuta barge-in

if interrupted:
    # Marcar: user ouviu só frac_heard da resposta
    tts.mark_interrupted(frac_heard)  # Corrige histórico pro próximo turno
```

**Latências logadas (para eval):**
- `t_vad_end`: turno completo segundo VAD
- `t_asr`: transcrição pronta
- `t_llm_first`: 1º chunk do LLM
- `t_tts_first`: 1º audio do TTS
- **total→1ºaudio** = t_tts_first - t_vad_end (alvo <500ms para p50)

---

## LIMITAÇÕES HONESTAS (v0)

### 1. **Áudio-contexto só trabalha com CSM**

Não existe num TTS aleatório — é específico do CSM (Mimi codec de 12.5Hz entende contexto). Com Pocket/Chatterbox/Qwen3, o áudio-contexto é ignorado (TTS vira stateless, zero personagem).

### 2. **LLM só vê texto (paralinguística perdida)**

A transcrição do ASR perde ênfase, ironia, tom de raiva. Solução futura: encoder multimodal (áudio+texto) no LLM. Sesame admite isso como lacuna no podcast a16z (2025).

### 3. **Half-duplex por design**

Sem fones, o speaker toca áudio do agente → feedback confunde mic → VAD falsa-positiva. Com fones, barge-in funciona (gate prob ≥0.5, latência <300ms).

### 4. **Mono-emoção do dataset atual**

G1 (4-6h) e G2 (8 estilos, 5-7h) ainda não foram gravados. CSM atual tem prosódia levemente robótica (Treino 1: naturalidade 3.1/5, entonação robótica = problema #2). Mitiga com dataset curado + G1+G2 paralelos.

### 5. **Sotaque gringo é o problema #1 (Treino 1: 28× marcado)**

CSM recebe texto cru; quick-wins:
- **Normalizar número/CEP/moeda** (text_frontend já pronto, runpod/recipe.py) — conserta ~3 trechos graves de hard-01 sem GPU
- **G2P pt-BR** (fonemizar entrada) — ramo de ablação vs text-only, arXiv 2410.14997/2306.00535
- **Base carioca/espontânea** em Estágio A (NURC-MIT se licença confirmar, senão base syntética)

Não há atalho sem regravar (arXiv 2606.05367 UNESP prova que aritmética linear NÃO funciona em TTS-LM).

### 6. **Barge-in é "detectar novo turno", não interrução real**

Não há síntese incremental (TTS re-corta a geração em voo, estilo Sesame). O CSM gera 1 sentença → toca inteira → próximo listen_turn detecta user. Se user interrompe MID-sentença, o agente ouve a interrupção na PRÓXIMA iteração.

Mitigação esperada (F5): OUTLINES constrainado (JSON estruturado) + abort de geração de 1s → 20ms à la Sesame (arXiv diferente, Pipecat/Llamaindex já suportam).

### 7. **Nenhum RL de interatividade (apenas SFT no CSM)**

Moshi ainda não tem RL aplicado (F5). CSM é single-turn (não otimizado pra turn-taking). Turn-taking emerge de:
- Áudio-contexto: últimos 4 turnos informam que "é hora do user falar"
- SmartTurn v3 heurístico: detecta fim semântico

Não há reward de "pausa natural" vs "corte abrupto" — isso é futuro (F5 + moshika-rl-seamless).

---

## COMO MEDIR LATÊNCIA p50 (<800ms)

### Setup

**No Mac:** Câmera do iPhone, recorder simultâneo de áudio do Mac (QuickTime, System Audio Capture ou Loopback):

```bash
# Terminal: logging com timestamps
while true; do
  python -m src.duplex.chat_loop \
    --tts csm --llm-base-url ... --llm-model ... \
    2>&1 | tee -a latency_run.log
  sleep 1
done
```

**Vídeo:** gravação de tela (⌘+Shift+5 no Mac) + áudio (iPhone ou Loopback) rodando em paralelo.

### Medição (10 trocas, escuta cega)

1. **Editar vídeo** (cortar silêncios iniciais, alinhar áudio/vídeo):
   - Fim da minha fala = última onda do mic em t0
   - Início do áudio do agente = primeira onda do speaker em t1
   - **p50 = mediana de (t1 - t0) para 10 trocas**

2. **Esperar:** simulação de conversação natural (perguntas/respostas variadas, ~1 min)

3. **Capturar latências intermediárias** (do log da CLI):
   - asr: ASR→LLM
   - llm₁: ASR→1º LLM token
   - tts₁: LLM→1º TTS audio
   - total→1ºaudio: VAD→TTS

4. **Comparar vs Moshi-pt** (mesmo teste, mesmas frases, escuta cega do Pedro + 2 cariocas)

### Template de resultado

```markdown
## Latência Maya-BR v0 (2026-06-XX)

| Setup | p50 (ms) | p95 (ms) | Barge-in (ms) | Falsos turnos | Notas |
|---|---|---|---|---|---|
| CSM-pt + Gemini Flash | 510 | 820 | 210 | 1/10 | Áudio-contexto funciona |
| CSM-pt + Sabiá local | 380 | 680 | 180 | 0/10 | ✅ Recomendado |
| Pocket + Gemini | 420 | 720 | — | 2/10 | Sem pessoa |
| Moshi-pt (referência) | 450 | 950 | 250 | 1/10 | Maya parity? |
```

---

## COMO FAZER A/B CEGO VS MOSHI

### Protocolo (escuta cega, 3 cariocas nativos)

**Preparação:**

1. Gravar **mesmas 14 frases** (benchmark_ptbr.jsonl) sintetizadas em:
   - Maya-BR v0 (CSM-pt)
   - Moshi-pt (se checkpoint existir; senão usar modelo zeroshot SOTA como baseline)
   - Moshi (se houver acesso via API)

2. **Randomizar ordem**, anonimizar labels ("Voz A" / "Voz B")

3. **Escuta com 3 painelistas:**
   - Avaliador 1: Pedro (design owner, enviesado, avaliar separadamente)
   - Avaliador 2, 3: 2 cariocas convidados (blind, sem saber qual é qual)

### Critérios (MUSHRA simplificado)

Para cada par (A, B), escutar 1× e marcar:

| Critério | Escala | Notas |
|---|---|---|
| Soa nativo pt-BR? | 1-5 | Fonema/sotaque/pronúncia |
| Natural/fluente? | 1-5 | Prosódia, disfluência aceitável |
| Parece uma pessoa? | 1-5 | Timbre/timidez/confiança |
| Geral: qual prefere? | A / B / Igual | CMOS direta |

### Resultado esperado (gate F4)

**Maya-BR v0 passa se:**
- Pelo menos 2/3 painelistas preferem ou acham igual a Moshi-pt
- "Soa nativo" media ≥3.5 (vs ≤2.8 em Treino 1)
- Latência p50 ≤ Maya + 20% ou <800ms absoluto

---

## FLUXO DE DESENVOLVIMENTO (próximos passos)

### Fase 1: Validação de scaffold (esta semana)

- [ ] Rodar `chat_loop.py` localmente com Pocket TTS (CPU, zero setup)
  - [ ] Verificar que listen_turn, ASR, LLM, TTS fluem sem erro
  - [ ] Medir latências intermediárias (log)
  - [ ] Testar barge-in em headphones

### Fase 2: Integração CSM-pt (semana 1-2)

- [ ] Carregar stage_b_final (CSM-pt + LoRA voz)
- [ ] Chamar `tts.synth()` e verificar que áudio-contexto funciona
  - [ ] Adicionar contexto (role 0=agente, role 1=user) via `add_context(role, text, audio)`
  - [ ] Sintetizar mesma frase 2×: sem contexto vs com contexto (áudio deve ser diferente)
- [ ] Medir latência TTS (esperado ~1s/sentença, batch CPU ou GPU)
- [ ] Testar normalização de número (runpod/recipe.py:text_frontend) no input

### Fase 3: Latência <800ms (semana 2-3)

- [ ] Medir latências intermediárias (VAD, ASR, LLM, TTS)
- [ ] Profile onde está o gargalo
  - Suspeita: LLM latência (100-300ms) + TTS (200-500ms) = 300-800ms
  - Otimização: batching de múltiplas sentenças, se houver buffering
- [ ] Considerar SSD Colab/sglang local (reduz LLM latência)
- [ ] Cache de embeddings no CSM (se houver overhead de load)

### Fase 4: A/B vs Moshi (semana 3-4, gate F4)

- [ ] Sintetizar benchmark_ptbr.jsonl com CSM-pt
- [ ] Gravar referência Moshi-pt (ou usar baseline SOTA)
- [ ] Escuta cega com 3 painelistas (protocolo acima)
- [ ] Decidir: M vira principal ou Trilha B (Moshi LoRA pt) continua como alvo

### Paralelo: Melhorias de qualidade (sem bloquear v0)

- [ ] Curar dataset Pedro (curate_app): Whisper errors + marcar ruído/overlaps
- [ ] Treinar G1 (4-6h core): rodar Estágio B v2 no dataset curado
- [ ] Treinar G2 (8 emoções): SFT + DPO leve (gate: emoção ≥70% reconhecível)
- [ ] Testar G2P pt-BR como ramo de ablação (text → fonema antes do CSM)
- [ ] Se WER no A/B ≥Maya: re-treinar base em Estágio A com NURC-MIT (se licença confirmar) ou Granary/YODAS-CC

---

## CHECKLIST DE DEPLOYABILIDADE (f5, final)

Antes de chamar isso "pronto para demo":

- [ ] **Código limpo:** sem `TODO`, `FIXME`, imports não usados
  - [ ] `py_compile` valida sintaxe sem rodar
  - [ ] `mypy` roda sem erros (types)
- [ ] **Dependências:** `requirements.txt` versionado, wheels isolados
  - [ ] `pip freeze > requirements.txt` ao finalizar
  - [ ] Testado em fresh venv
- [ ] **Logging:** latências, erros, e contexto audio são salvos em `logs/maya_run_TIMESTAMP.jsonl`
- [ ] **Safeguards:**
  - [ ] Timeouts: ASR timeout se exceder 30s
  - [ ] LLM: max_tokens limitado (ex: 50 tokens = ~40 palavras)
  - [ ] TTS: max 160 tokens de entrada (STAGE_B max_text_len=384 caracteres)
  - [ ] VAD: echo cooldown 350ms
- [ ] **Persona:** testada com prompt adversarial
  - [ ] Não gera conteúdo nocivo (LLM responsibility)
  - [ ] Respostas curtas e orais (system prompt funciona)
- [ ] **Eval harness:** benchmark_ptbr.jsonl + benchmark_sotaque.jsonl rodados, WER + spk-sim + TTSDS2 computados
- [ ] **Documentação:**
  - [ ] README com exemplos
  - [ ] Troubleshooting (FAQ do que pode dar errado)
  - [ ] Licenças: verificadas de todas as dependências

---

## TROUBLESHOOTING

### Problema: "Silero-VAD não carrega"

```bash
# Solução 1: pip direto
pip install silero-vad --upgrade

# Solução 2: torch.hub (fallback no código)
python -c "import torch; torch.hub.load('snakers4/silero-vad', 'silero_vad')"
```

### Problema: "faster-whisper muito lento"

```bash
# Mudar modelo
python -m src.duplex.chat_loop --asr-model tiny  # ~30ms, menos acurado
python -m src.duplex.chat_loop --asr-model small  # ~60-100ms, bom trade-off
```

### Problema: "LLM timeout"

```python
# No llm.py, adicionar timeout
response = client.chat.completions.create(
    ...,
    timeout=httpx.Timeout(5.0, read=10.0)  # 5s connect, 10s read
)
```

### Problema: "CSM balbucia / para errado"

Verificar que `stage_b_final` usa EOS label=0 (não 128003). Em runpod/recipe.py:check_config() já valida isso. Se recarregar checkpoint antigo:

```python
# No tts_adapter.py, antes de usar o modelo:
assert hasattr(model.config, 'eos_fix') and model.config.eos_fix, \
    "EOS label incorreto — modelo vai balbuciar. Use stage_b_final ou re-aplica o fix."
```

### Problema: "Feedback/eco em half-duplex"

```python
# Aumentar cooldown no turn_engine
engine = TurnEngine(echo_cooldown_ms=500)  # default 350ms
```

Se persistir: usar speakers com fones de ouvido (não caixa sem direcionamento).

### Problema: "Turn-taking muito lento (user espera >2s)"

Gargalo no pipeline:

```python
# Perfil cada componente
from src.duplex.chat_loop import main
# Adicionar na main():
print(f"VAD lag: {(t_asr - t_vad_end)*1000:.0f}ms")
print(f"ASR lag: {(t_llm_first - t_asr)*1000:.0f}ms")
print(f"LLM lag: {(t_tts_first - t_llm_first)*1000:.0f}ms")
```

Suspeita comum:
- LLM latência >500ms? Trocar para sglang local ou cache de embeddings
- TTS latência >800ms? Batch de sentenças, ou reduzir contexto audio (de 4 turnos para 2)
- ASR latência >300ms? Trocar para smaller model

---

## APÊNDICES

### A. Referências rápidas

- **REPLAN 2026-06-10** (§155-159, trilha M): especificação da cascata e pré-requisitos
- **Treino 1 (trilha_map.json):** achados da voz do Pedro (WER 12%, para 14/14, gringo #1 problema)
- **OSINT Sesame (REPLAN §80-134):** engenharia reversa da Maya — cascata confirmada
- **CSM HF repo:** `thomasgauthier/csm-hf` (port HF), `knottwill/csm-streaming` (refs)
- **Kyutai Moshi:** `kyutai-labs/moshi` (CC-BY-4.0, spine alternativa F5)
- **SmartTurn v3:** `pipecat-ai/smart-turn-v3` (ONNX turn-taking semântico, BSD-2)

### B. Datasets de eval

- `eval/benchmark_ptbr.jsonl` — 14 frases PT-BR, WER base
- `eval/benchmark_sotaque_carioca.jsonl` — sotaque carioca com traits esperadas
- `tools/rate/trilha_map.json` — achados estruturados, roadmap

### C. Licenças (check antes de shippar)

| Componente | Licença | Status |
|---|---|---|
| CSM-1B base | Apache-2.0 | ✅ OK |
| Stage B (voz) | Derivado de ElevenLabs | ⚠️ Proprietário (internal) |
| Silero-VAD | SPL | ✅ Livre pra uso (sem redistribuição de pesos) |
| SmartTurn v3 | BSD-2 | ✅ OK |
| faster-whisper | MIT | ✅ OK |
| Gemini API | Google TOS | ✅ Free tier pra dev |
| Sabiá | HF CC-BY | ✅ OK |
| Moshi | CC-BY-4.0 | ✅ OK (não usado em v0, future F5) |

**Antes de demo/release:** advogado revisa, especialmente se usar "voz clonada" em contexto comercial (PL 1460/2026 exige watermark + consentimento).

### D. Onde os dados de conversação ficam?

**Não persiste automaticamente em v0.** Para eval posterior (F4 gate):

```python
# Adicionar em chat_loop.py:
import json
import time
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"maya_run_{int(time.time())}.jsonl"

# Em cada turno, escrever:
with open(log_file, "a") as f:
    f.write(json.dumps({
        "turn": turn_idx,
        "user_text": text,
        "agent_text": " ".join(reply_text),
        "latencies": {
            "vad_end_s": t_vad_end - t0,
            "asr_s": t_asr - t_vad_end,
            "llm_first_s": t_llm_first - t_asr,
            "tts_first_s": t_tts_first - t_llm_first,
        },
        "interrupted": interrupted,
        "frac_heard": frac_heard,
    }) + "\n")
```

Útil para análise posterior de latência + conversação inteira em JSONL legível.

---

## CONCLUSÃO

Maya-BR v0 é honesto sobre seus limites (half-duplex, sem RL, áudio-contexto só no CSM) mas entrega uma cascata limpa e testável que pode validar a hipótese: "cascata de componentes validados + CSM-1B pt-BR é suficiente pra parecer conversacional e bater Moshi-pt." Se o gate F4 passar, a Trilha M vira principal e o investimento em Trilha B (Moshi LoRA pt) é re-avaliado. Se falhar, volta-se a Moshi com full-duplex nativo (F4-5).

**Este runbook é vivo.** Atualizar conforme:
- Novos checkpoints do CSM saem (G1, G2)
- Latência p50 melhora ou degrada
- A/B vs Moshi revela gaps
- Tecnologia SOTA muda (ex: SoulX-Duplug arXiv 2603.14877 pode oferecer duplex mais barato)

**Data de revisão recomendada: 2026-07-17** (próxima review do REPLAN, após F4 gate).
