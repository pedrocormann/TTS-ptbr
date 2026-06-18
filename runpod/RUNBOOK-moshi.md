# RUNBOOK — Trilha B: Full-Duplex Moshi pt-BR (e alternativa SOTA SoulX-Duplug)

**Data:** 2026-06-17  
**Status:** Pré-requisitos reais mapeados; readiness para F4 (Estágio de spine)  
**Risco:** SoulX-Duplug (SOTA 2026) pode ser alternativa mais rápida que Moshi LoRA  

---

## Sumário Executivo

**Trilha B aposta em Moshi (CC-BY-4.0, Kyutai) como spine full-duplex pt-BR** — modelo que fala E ouve simultaneamente sem alternar turnos (diferente da cascata Maya que é sequencial). O treino é via LoRA sobre pesos kyutai/moshiko-pytorch-bf16, rodando em Colab A100-80GB ou equivalente RunPod.

**MAS:** A pesquisa SOTA de jun/2026 achou **SoulX-Duplug** (arXiv 2603.14877), módulo plug-and-play que promete duplex sobre TTS streaming SEM trenar spine do zero. Antes de comprometer compute/data em Moshi, deve-se avaliar SoulX como atalho. Este runbook documenta **ambas as rotas** com recomendação clara de qual testar primeiro.

---

## Índice

1. [Pré-requisitos reais (dados)](#pré-requisitos-reais-dados)
2. [Entendimento arquitetural](#entendimento-arquitetural)
3. [Moshi LoRA — receita Kyutai](#moshi-lora--receita-kyutai)
4. [Pipeline de dados estéreo pt-BR](#pipeline-de-dados-estéreo-ptbr)
5. [SoulX-Duplug — alternativa SOTA 2026](#soulx-duplug--alternativa-sota-2026)
6. [Decisão de rota](#decisão-de-rota)
7. [Fase F4 — gates e timeline](#fase-f4--gates-e-timeline)

---

## Pré-requisitos Reais (Dados)

### O Bloqueador Central: Conversa Estéreo Sincronizada

O Moshi treina em **dados estéreo 24 kHz** (L=agente em turno, R=usuário/interlocutor). O dataset oficial de referência (`DailyTalkContiguous`, Kyutai) contém ~20h de conversas reais gravadas em dois canais.

**Nosso case:**
- **Fonte 1 (G4 flywheel):** reuniões UNFLAT diárias — **Pedro + João + Guilherme**, 3 microfones, 1 canal cada = **15-40h/mês potencial** de fala real, espontânea, multi-falante, **com consentimento LGPD prévio** (minuta em `docs/consentimento-voz.md`, ainda pendente de assinatura de João/Guilherme).
  - **Status atual:** consentimento pendente; equipamento (mics dinâmicas de proximidade + interface multi-entrada) não testado ainda.
  - **Bloqueador:** LGPD é hard-stop — **sem assinatura de João e Guilherme, não grava.**
  
- **Fonte 2 (sintética):** gerar pares estéreo artificiais usando a Trilha A (CSM-1B + Qwen3-TTS ou Chatterbox pt-BR):
  - L = CSM-pt-BR (voz do Pedro, Estágio B Final ou v2)
  - R = LLM pt plugável (Sabiá/Gemini Flash) + TTS qualquer (Qwen3-TTS/Chatterbox/MOSS-Realtime)
  - Script: `tools/data/synth/synth_stereo_moshi.py` (TODO v0.1 — não existe ainda, precisa ser escrito)
  - **Tempo de preparo:** ~2 semanas (escrever gerador + validar qualidade + acumular 20-30h)
  
- **Fonte 3 (Câmara ao vivo):** transmissões da Câmara dos Deputados (CC-BY), diarização automática → pares estéreo.
  - **Status:** mapeado em REPLAN §213, não priorizado para F4 (complexidade de diarização).

### O Mínimo Viável para Começar F4

**20-30h de dados estéreo de BOA qualidade (SNR≥32dB, sem denoise agressivo) é o mínimo** para validar gate F4 (inteligibilidade + latência <800ms). Estratégia realista para próximas 4 semanas:

1. **Semana 1:** assinatura de consentimento LGPD (João/Guilherme) + teste de sync de 3 mics.
2. **Semana 2:** acumular G4 piloto (~2-5h gravado em reuniões reais).
3. **Semana 2-3 (paralelo):** escrever `synth_stereo_moshi.py`, gerar dataset sintético (~15-20h, rodando overnight em Colab).
4. **Semana 3-4:** validação de qualidade (SNR, Audiobox-PQ, escuta cega), limpeza e conversão para formato `.jsonl + .json alignments`.

**Caso F4 comece antes:** usar só dados sintéticos inicialmente (20-30h via Qwen3-TTS + LLM). Depois que G4 colecionar horas reais, reavaliar com mix real+sintético.

---

## Entendimento Arquitetural

### Moshi vs. Maya (cascata)

| Aspecto | Moshi | Maya (Trilha M) |
|---------|-------|-----------------|
| **Topologia** | Spine full-duplex único | Cascata sequencial |
| **Funcionamento** | Fala E ouve em paralelo; RVQ autoregressivo contínuo | VAD → ASR → LLM → CSM turnos sequenciais |
| **Latência** | ~200ms (teórico, L4; nosso: TBD) | p50 300-500ms (design-budget) |
| **Condicionamento** | Áudio-contexto implícito (~2 min histórico) | Histórico textual + contexto áudio no CSM |
| **Dado de treino** | Estéreo (L=agente, R=usuário) | Mono (gravação dirigida) + anotações |
| **Complexidade de treino** | LoRA simples, pesos base congelados | Múltiplos componentes (VAD, ASR, LLM, TTS) |
| **Risco de regress** | Turn-taking pode degradar com LoRA ruim | Menos acoplado; cada componente pode ser ajustado |
| **Aposta estratégica** | Simplicidade arquitetural; um modelo faz tudo | Robustez modular; + engenharia de orquestração |

### Codec Mimi — usado por AMBOS (Moshi + CSM)

- **Taxa:** 12.5 Hz (80ms por token), 24 kHz sample rate, 8 codebooks por canal (RVQ).
- **Compressão:** ~300 bps de áudio por falante (ultra-low).
- **Implicação:** já que o CSM (Trilha A) usa Mimi, o ecossistema de treino é compartilhado — pesos Mimi congelados em ambas as trilhas, poupando compute.

---

## Moshi LoRA — Receita Kyutai

### Deps e Setup

**Versão oficial validada (2026-06-10):**
- Repo: `github.com/kyutai-labs/moshi-finetune` (Apache-2.0, main @ 2025-07-07)
- Pesos: `kyutai/moshiko-pytorch-bf16` (CC-BY-4.0) ou `kyutai/moshika-pytorch-bf16` (female variant)
- Python ≥3.10, PyTorch 2.6 (pin exato)
- Dependências exatas: ver `research/dossier-2026-06/82-moshi-finetune-api.md` §1

**Instalação no Colab:**
```bash
cd /content/
git clone https://github.com/kyutai-labs/moshi-finetune.git
pip install -e /content/moshi-finetune
# PyTorch 2.6 vai fazer downgrade se Colab vem com versão mais nova (normal)
```

### Config YAML — valores para pt-BR no Colab A100-40GB

**Arquivo: `/content/example_ptbr.yaml`** (adaptado do `example/moshi_7B.yaml` oficial):

```yaml
# ===== Paths =====
run_dir: /content/moshi_ptbr_test  # não pode existir
moshi_paths:
  hf_repo_id: kyutai/moshiko-pytorch-bf16

# ===== Data =====
data:
  train_data: /content/data/stereo_ptbr.jsonl
  eval_data: null
  shuffle: true

# ===== LoRA (Kyutai recomenda rank 128 p/ pt-BR) =====
full_finetuning: false
lora:
  enable: true
  rank: 128
  scaling: 2.0
  ft_embed: false  # TODO: testar true se vocab colapsar em pt

# ===== Loss weights =====
first_codebook_weight_multiplier: 100.  # semântica
text_padding_weight: 0.5

# ===== Treinamento =====
duration_sec: 100          # janela de entrada (não garante latência final)
batch_size: 1              # A100-40GB: batch_size 1 é seguro; com num_microbatches=16 get batch_eff=16
num_microbatches: 4        # grad accumulation (bs_eff = 1 * 4 = 4)
max_steps: 2000            # ~12h numa A100-40GB com batch_size=1
gradient_checkpointing: true

# ===== Optimizer =====
optim:
  lr: 2e-6                 # Kyutai recomenda (não tocar)
  weight_decay: 0.1
  pct_start: 0.05          # warmup 5%

# ===== Checkpointing =====
log_freq: 10
do_ckpt: true
ckpt_freq: 100             # salva a cada 100 steps
num_ckpt_keep: 3           # mantém 3 checkpoints recentes
save_adapters: true        # salva só lora.safetensors (não merge)

# ===== Opcional: W&B =====
# wandb:
#   project: tts-ptbr
#   run_name: moshi_finetune_v1
#   offline: false

seed: 42
param_dtype: bfloat16
```

**Adaptações conforme VRAM disponível:**

| Setup | batch_size | num_microbatches | duration_sec | Pico VRAM | ~Tempo |
|-------|-----------|------------------|--------------|----------|--------|
| A100-40GB (Colab) | 1 | 4 | 100 | 35-38 GB | 12h (2000 steps) |
| A100-80GB | 4 | 4 | 100 | 39 GB | 3h (2000 steps) |
| RunPod H100-80GB | 16 | 1 | 100 | 39 GB | 2h (2000 steps) |
| G4-96GB | 8 | 2 | 100 | ~45 GB | 6h (2000 steps) |

**Regra geral (Kyutai):** aumentar `batch_size` antes de reduzir `duration_sec` (encurtar a janela degrada turn-taking).

### Pipeline de Treino

```bash
# 1. Preparar o YAML (vê acima)
cd /content/moshi-finetune
# copiar exemplo_ptbr.yaml pro diretório

# 2. Anotar os dados (gerar os .json alignments)
#    (ver seção "Pipeline de dados estéreo pt-BR" abaixo)

# 3. Treinar
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0
torchrun --nproc-per-node 1 -m train /content/example_ptbr.yaml

# 4. Monitorar loss (tail -f)
tail -f /content/moshi_ptbr_test/log.txt

# 5. Carregar o checkpoint final pra inferência (ver seção abaixo)
```

### Carregando o LoRA Treinado

**PyTorch (caminho oficial no servidor Moshi):**
```bash
python -m moshi.server \
  --lora-weight=/content/moshi_ptbr_test/checkpoints/checkpoint_002000/consolidated/lora.safetensors \
  --config-path=/content/moshi_ptbr_test/checkpoints/checkpoint_002000/consolidated/config.json \
  [--device cuda:0]
```

**MLX (Mac do Pedro):** via conversão
```bash
# Antes: rodou o treino num Colab e salvou o checkpoint
# Agora: funde o LoRA e converte pro layout MLX

python scripts/import_mlx_lora.py \
  --lora-weight=/path/to/lora.safetensors \
  --config-path=/path/to/config.json \
  --hf-repo kyutai/moshiko-pytorch-bf16 \
  -o /tmp/moshi_ptbr_mlx.safetensors

python -m moshi_mlx.local_web \
  --moshi-weight /tmp/moshi_ptbr_mlx.safetensors \
  --lm-config /path/to/config.json \
  -q 4  # quantizar em 4-bit p/ M2 16GB
```

---

## Pipeline de Dados Estéreo pt-BR

### Formato Exato (Kyutai)

**Arquivo WAV estéreo 24 kHz:**
- **Canal 0 (L):** a voz que o modelo vai FALAR (no nosso caso: CSM-1B pt-BR, voz do Pedro).
- **Canal 1 (R):** o interlocutor/usuário (no nosso caso: LLM pt + TTS, ou usuário real em G4).
- Ambos sincronizados em timestamp (mesmo clock ou resyncronizado after-the-fact).

**Arquivo .json de alignments** (por WAV, mesmo nome, ex.: `audio_001.wav` → `audio_001.json`):
```json
{
  "alignments": [
    ["palavra1", [0.00, 0.30], "SPEAKER_MAIN"],
    ["palavra2", [0.30, 0.80], "SPEAKER_MAIN"],
    ...
  ]
}
```
- Apenas `"SPEAKER_MAIN"` é supervisionado em texto (o canal R não é anotado em palavras — só em áudio).
- Timestamps em segundos (float), **palavra por palavra**.

**Arquivo .jsonl de metadados** (um por dataset):
```json
{"path": "stereo_ptbr/audio_001.wav", "duration": 25.432}
{"path": "stereo_ptbr/audio_002.wav", "duration": 30.158}
...
```

### Gerador Sintético: Especificação

**Script: `tools/data/synth/synth_stereo_moshi.py`** (TODO: escrever na F3)

Entrada:
- **Corpus de frases:** `eval/benchmark_ptbr.jsonl` + corpus extensível de diálogos pt-BR (ex.: ConvBank ou corpus próprio).
- **Modelos TTS:** CSM-1B pt-BR (Estágio B Final ou v2 + emoções quando G2 existir) para o L, Qwen3-TTS ou Chatterbox-pt-br para o R.
- **LLM:** Sabiá/Gemini Flash para o R (gerador de resposta).

Algoritmo:
```
Para cada turno de conversa (USER → AGENT → USER → AGENT):
  1. USER turno (ex.: "Qual é o CEP de São Paulo?")
     - Sintetizar com Qwen3-TTS → áudio 24kHz → pad a 80ms frames
     - Medir duração, gerar timestamps do Whisper
     - Escrever canal R
     
  2. AGENT responde (ex.: "O CEP é 01311-100.")
     - LLM (Gemini Flash) processa o turno do USER
     - Sintetizar resposta com CSM-1B pt-BR
     - Escrever canal L, com alinhamentos do CSM
     - **Bake-in: normalizar números antes de synth** (usar text_frontend de recipe.py)
     
  3. Mesclar L+R em 24kHz estéreo WAV
  4. Gerar o .json de alignments
  5. Adicionar ao .jsonl de metadados
```

**Critério de qualidade:**
- SNR ≥ 32 dB (sem ruído de síntese perceptível)
- Audiobox-PQ ≥ 3.5 (naturalidade aceitável)
- Sem clipping, fade-in/out corretos, duração <10min por WAV (Kyutai recommenda para evitar OOM)
- Proporção de silence (<-40dB) ≤ 10% por WAV

**Saída:**
- `stereo_ptbr/audio_NNNN.wav` (24 kHz estéreo)
- `stereo_ptbr/audio_NNNN.json` (alignments)
- `stereo_ptbr.jsonl` (metadados)
- ~20-30h de material, armazenado em HF Datasets ou Google Drive pra Colab

### Dados Reais (G4 Flywheel) — Preparação

**Assinar o termo LGPD primeiro** (`docs/consentimento-voz.md`).

**Gravação (4 semanas):**
1. 3 microfones dinâmicos (Shure SM58 ou equivalente) em posições fixas na sala de reunião.
2. Interface de áudio multi-entrada (RME Babyface Pro FS ou Behringer U-Phoria UMC1820) sincroniza os 3 canais.
3. Software de gravação: `audacity` ou `ffmpeg -f alsa -i hw:0 -i hw:1 -i hw:2 ...` (captura simultânea).
4. Normalizar a -23 LUFS (via `ffmpeg-normalize`), descartar clipes com denoise agressivo.

**Pipeline de processamento (`tools/recording/meeting_to_moshi.py`):**
```python
# Input: 3 canais mono 48kHz (1 por pessoa)
# Output: pares estéreo pt-BR

for (L_idx, speaker_main) in enumerate(['Pedro', 'João', 'Guilherme']):
    # Cada pessoa é "agente" num par estéreo
    L = wav[L_idx]  # fala da pessoa
    R = mix([wav[i] for i in range(3) if i != L_idx])  # outros falam pro microfone
    
    # Resampleiar pra 24kHz se necessário
    L = resample(L, 48000, 24000)
    R = resample(R, 48000, 24000)
    
    # Sincronizar (já estão sincronizados pela gravação simultânea)
    stereo = stack([L, R], axis=0)
    
    # Anotar L com transcrição + timestamp (Whisper-medium ou manual)
    annotations = whisper_align(L @ 16kHz)
    
    # Exportar
    save_wav(stereo, f'stereo_ptbr/reunion_NNNN_speaker_{L_idx}.wav')
    save_json(annotations, f'stereo_ptbr/reunion_NNNN_speaker_{L_idx}.json')
```

**Duração acumulada:**
- 1 reunião/dia, ~1h cada, 3 falantes = **3 pares estéreo/dia**.
- 20 dias de reunião/mês = **60 horas estéreo/mês** (se todos os dias forem 1h).
- Realista (feriados, férias): **15-40h/mês no primeiro trimestre**.

---

## SoulX-Duplug — Alternativa SOTA 2026

### O Achado

**Referência:** arXiv 2603.14877 (SoulX-Duplug: "A Novel Full-Duplex Speech Interaction Architecture via State Prediction Module")  
**Publicação:** Junho 2026  
**Tipo:** Módulo plug-and-play  
**Licença:** A confirmar (paper recém-publicado; código GitHub não estava disponível em 2026-06-17)

### Princípio

Enquanto Moshi é um modelo **único** que fala e ouve em paralelo, SoulX-Duplug é um **módulo complementar** que pode ser acoplado a **qualquer TTS streaming** (Qwen3-TTS, MOSS-Realtime, nosso CSM) para produzir um efeito de "duplex aparente" sem trenar o spine do zero.

**Mecanismo (resumido do abstract/intro):**
- O módulo prediz o estado *futuro* da conversa (o usuário vai continuar falando? vai fazer uma pausa? vai interromper?).
- Com essa predição, o TTS reage **incrementalmente** — começa a falar, detecta que o usuário interrompeu (predição), interrompe a própria geração em ~20-50ms.
- **Resultado:** parecer full-duplex genuíno (turno-taking em tempo real) **sem precisar de um backbone único** como Moshi.

### Vantagens vs. Moshi LoRA

| Fator | SoulX-Duplug | Moshi LoRA |
|-------|-------------|-----------|
| **Engenharia** | Módulo, integra-se na cascata Maya existente | Spine único, redesenho do orquestrador |
| **Dados de treino** | Pode usar dados de turn-taking anotados (mais barato) | Precisa estéreo full-duplex sincronizado (20-30h) |
| **Tempo até MVP** | Semanas (integração em src/duplex) | 2-3 meses (G4 coleta + anotação + finetune) |
| **Reuso de código** | Reutiliza CSM + LLM + ASR da Trilha A/M | Reescreve o turn-engine |
| **Risco de regress** | Baixo (módulo separável) | Médio (LoRA em base não testado em pt-BR) |
| **Escalabilidade** | Melhor (o módulo é plug-and-play em qualquer TTS) | Acoplado ao Moshi (menos generalista) |

### Questões em Aberto (2026-06-17)

1. **Código não disponível ainda.** O paper saiu há ~2 semanas; código era "disponível on request" ou em repositório privado.
2. **Validação em pt-BR.** Paper é em inglês/chinês; não há benchmarks de turnos cariocas.
3. **Integração com CSM.** SoulX foi testado com espinhas específicas (não nomeadas no abstract); CSM-1B pode não ser suportado out-of-the-box.
4. **Latência real em nosso hardware.** Paper mede em hardware de pesquisa (TPU/A100 provavelmente); nosso caso (Colab/RunPod) pode divergir.

---

## Recomendação: Rota de Avaliação SoulX Primeiro

### Por Quê?

1. **Risco reduzido:** se SoulX funcionar, economizamos 6-8 semanas de coleta de dados estéreo + finetune.
2. **Realismo de prazo:** Moshi F4 está estimado em 2-3 meses; SoulX pode validar em 3-4 semanas se código sair.
3. **Sinergia com Trilha M:** SoulX integra-se perfeitamente na cascata Maya (VAD → ASR → LLM → CSM + **SoulX module** → full-duplex aparente).
4. **Caminho de fallback:** se SoulX não funcionar bem, Moshi vira o plano B, e o flywheel G4 terá gerado dados úteis de qualquer jeito.

### Spike de Avaliação SoulX (2 semanas)

**Semana 1:** 
- Monitorar repositório GitHub (SoulX-research ou similar) pra código.
- Se código sair, clonar + ler a implementação vs o paper (encontrar discrepâncias).
- Smoke-test em Colab: rodar o módulo sobre CSM-1B com turno-taking sintético (usuário interrompe no meio da frase).
- Medir latência de detecção de interrupção, qualidade de stop (não regredir naturalidade).

**Semana 2:**
- Se viável, integrar no `src/duplex/turn_engine.py` como replacement do barge-in manual.
- Testar no benchmark_ptbr.jsonl com escuta cega (Pedro + 2 ouvintes).
- Gate: latência p50 <800ms, barge-in <150ms, preferência ≥ "aceitável" em escuta cega.

**Critério go/no-go:**
- **Go:** código disponível + smoke-test passou + latência <150ms + escuta cega ≥ "natural" → Moshi vira contingency, SoulX vira aposta principal.
- **No-go:** código não sai OU latência >300ms OU regress em naturalidade → seguir com Moshi LoRA como planejado.

---

## Decisão de Rota

### Fluxo de Decisão (F3-F4)

```
[AGORA: F3 em progresso]
    ↓
┌─────────────────────────────────────────┐
│ Assinar LGPD + iniciar G4 flywheel?     │
├─────────────────────────────────────────┤
│ SIM: vira fonte de dados real           │
│ NÃO: usar só dados sintéticos por F4    │
└────────────┬────────────────────────────┘
             ↓
        [F3.5: Spike SoulX — 2 sem]
             ↓
    ┌────────┴────────┐
    │                 │
[SoulX code sai]  [SoulX NÃO sai]
    │                 │
    ↓                 ↓
[SoulX Spike]  [Moshi LoRA Ready]
    │                 │
    ├─ Go? ──→ [SoulX aposta] F4
    │                 │
    └─ No-go ────→ [Moshi LoRA] F4
```

### Recomendação para Pedro (Ordem)

1. **Semana de 2026-06-17:**
   - Assinar termo LGPD com João/Guilherme (10 min).
   - Testar sync de 3 mics em 1 reunião piloto (30 min).
   - Monitorar SoulX-Research no GitHub/arXiv (daily).

2. **Semana de 2026-06-24:**
   - Se SoulX code sair → spike de 1 semana (Colab smoke-test).
   - Paralelo: começar a acumular dados sintéticos (`synth_stereo_moshi.py`).

3. **Semana de 2026-07-01:**
   - Decidir SoulX vs. Moshi com base nos resultados do spike.
   - Se Moshi: confirmar G4 collection, começar finetune.
   - Se SoulX: integrar no `src/duplex` e testar em Maya-BR v0.

---

## Fase F4 — Gates e Timeline

### Gate F4 (Go/No-Go para Produção)

**Critérios (independente da rota SoulX vs. Moshi):**

| Métrica | Target | Owner | Ferramenta |
|---------|--------|-------|-----------|
| **Inteligibilidade (pt-BR)** | WER <30% round-trip | Auto | `faster-whisper-large-v3` |
| **Turn-taking (latência)** | p50 <800ms, p95 <1.2s | Auto | `src/duplex/bench_latency.py` (TODO) |
| **Naturalidade de pausa** | "não parece robótico" escuta cega ≥70% | Humano | 3 cariocas nativos + CMOS |
| **Barge-in** | Detecção <150ms sem regress | Auto | `turn_engine_bench.py` (TODO) |
| **Preferência humana** | ≥ Moshi-pt OR ≥ Maya-BR v0 (conforme rota) | Humano | CMOS 30+ ouvintes |

**Bloqueadores:**
- WER >30% = colapso de inteligibilidade, re-treinar obrigatório.
- Latência p50 >1s = experiência ruim, voltar pra Maya.
- Naturalidade <60% em escuta cega = acelerador de fala necessário (TODO: speech rate control).

### Timeline Estimado

**Cenário A: SoulX sai + código funciona (best case)**
- F3.5 spike: 2 semanas (2026-06-24 a 2026-07-08)
- F4 integração + teste: 3 semanas (2026-07-08 a 2026-07-29)
- **Total: 5 semanas, MVP em late jul/2026**

**Cenário B: SoulX não sai ou não funciona (Moshi LoRA)**
- G4 coleta: 3-4 semanas (2026-06-17 a 2026-07-15)
- Dados sintéticos: 2 semanas paralelo (2026-06-24 a 2026-07-08)
- Moshi finetune: 2 semanas (2026-07-15 a 2026-07-29)
- F4 testes + gates: 2 semanas (2026-07-29 a 2026-08-12)
- **Total: ~7-8 semanas, MVP em early ago/2026**

### Setup Recomendado para F4

**Compute:**
- **Colab Pro+ ($49,99/mês):** A100-80GB ou G4-96GB bastam para finetune (se Moshi); L4 pra inference do módulo SoulX ou inferência em tempo real.
- **RunPod (fallback):** H100-80GB (~$3.50/h) pra finetune Moshi paralelo a G4 coleta.

**Ferramentas novas (a escrever):**
- `tools/data/synth/synth_stereo_moshi.py` — gerador de dados estéreo sintéticos.
- `tools/data/moshi/prepare_moshi_jsonl.py` — conversão de G4 gravado + anotações → format Moshi.
- `tools/bench/bench_latency.py` — medida de turno real em Moshi/SoulX vs Maya-BR v0.
- `tools/bench/bench_turnwrit.py` — contagem de falsos-positivos/negativos de barge-in.

**Integração no `src/duplex`:**
- Se SoulX: `src/duplex/soulx_module.py` + acoplamento com LLM/TTS.
- Se Moshi: reescrever `turn_engine.py` p/ orquestração Moshi (não sequencial, paralelo).

---

## Checklist Pre-F4

- [ ] **Semana 2026-06-17:** assinar LGPD (João/Guilherme).
- [ ] **Semana 2026-06-24:** testar sync de 3 mics (1 reunião).
- [ ] **Semana 2026-06-24:** monitorar SoulX code on GitHub.
- [ ] **Semana 2026-06-24:** escrever `synth_stereo_moshi.py` + teste em 1 amostra.
- [ ] **Semana 2026-07-01:** decidir SoulX vs. Moshi com spike results (ou "SoulX não saiu, go Moshi").
- [ ] **Semana 2026-07-08:** 5-10h dados estéreo acumulados (sintético + real piloto).
- [ ] **Semana 2026-07-15:** iniciar finetune (Moshi LoRA) OU integração SoulX.
- [ ] **Semana 2026-07-29 (target):** F4 gate decision (go/no-go produção).

---

## Apêndice: Referências Completas

### Papers

- **Moshi (Kyutai, 2024):** "Moshi: A Speech-Based AI That Actually Listens" — full-duplex com RVQ autoregressivo contínuo.
- **SoulX-Duplug (2026):** arXiv 2603.14877 — módulo de predição de estado para full-duplex plug-and-play.
- **Moshika-RL (Kyutai, 2026):** arXiv 2606.11167 — RL de interatividade (pausa, turn-taking, backchannel) — ready-to-use pra F5.
- **PersonaPlex (NVIDIA, 2026):** arXiv 2602.06053 — persona/voz por prompt no Moshi.
- **BayLing-Duplex (Baichuan, 2026):** arXiv 2606.14528 — full-duplex com único LLM AR (comparação arquitetural).

### Implementações

- `github.com/kyutai-labs/moshi-finetune` (Apache-2.0)
- `github.com/kyutai-labs/moshi` (Apache-2.0)
- `github.com/kyutai-labs/moshika-rl-seamless` (CC-BY-4.0, pós-treino)
- SoulX-research (GitHub — a confirmar, ainda em jun/2026)

### Dados

- `kyutai/DailyTalkContiguous` (HF, ~20h estéreo EN)
- Nossos: G4 flywheel (TBD) + sintéticos via Qwen3-TTS + CSM-1B.

### Docs do Projeto

- `/runpod/recipe.py` — guardrails + front-end de texto validados.
- `/research/dossier-2026-06/82-moshi-finetune-api.md` — deep-dive na API exata (sessão anterior).
- `/research/RESEARCH-2026-06-17-tts-sota.md` — citações de papers SOTA.
- `/specs/REPLAN-2026-06-10.md` — roadmap e decisões estratégicas.

---

**Documento:** RUNBOOK-moshi.md  
**Versão:** 1.0  
**Data:** 2026-06-17  
**Próxima revisão:** 2026-07-15 (pós spike SoulX, confirmação de rota)
