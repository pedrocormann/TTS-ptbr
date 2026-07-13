# RUNBOOK — Rodada 3 (multi-voz: pedro/gui/joao)

> ## ▶️ COMEÇAR POR AQUI (prioridade do sweep arch-addons, 13/jul — dossiê 85)
> Antes/ao lado dos 12 arms de treino: os **4 primeiros custam ~$0 e rodam no Mac** (deploy/eval,
> não dependem de dado nem GPU); o **5º é o arm de GPU de maior alavancagem**. Ordem:
>
> 1. **Barge-in: truncar o contexto na fração ouvida** — `consume_interruption()` já devolve a fração;
>    só usá-la antes de `tts.add_context`. Mata deriva de conversa no CSM. ~1 tarde, `src/duplex`.
> 2. **Flush-trick** — não esperar o `endpoint_ms` duro quando o Smart-Turn tem alta confiança →
>    **−300 ms** de latência de turno. ~1 tarde, `turn_engine`/`chat_loop`.
> 3. **CUDA-graph do decode Mimi (2,2×) + streaming/chunk adaptativo + WS multiplex + sessão isolada** —
>    a cascata "parece Maya" sem trocar modelo. `src/duplex`.
> 4. **Régua girando:** arena carioca (win-rate vs gravação real do Pedro) + **TTSDS2** + **VERSA** +
>    **`eval/accent_scorecard.py`** (gap #1 objetivo). É o que decide todos os arms.
> 5. **Bake-off de spine (GPU, ~$3-6):** `spine_qwen3_base` vs `spine_csm` vs `spine_kyutai_pt`
>    (`runpod/experiments.py`) na voz curada, mesmo eval. **Hipótese a matar: base pt-nativa
>    (Qwen3-TTS, Apache) dissolve o Estágio A e o gap #1 (gringo).**
>
> **Guardrails obrigatórios** em qualquer arm: `runpod.experiments.SWEEP_GUARDRAILS` (mixed-replay
> 25–30%, synth só com DPO anti-erosão, DPO antes de GRPO, quant codec conservador, DSP-aug só C0/C1,
> sem MOS-oráculo). Menu completo: `research/dossier-2026-07/85-arquiteturas-addons.md`.

**Quando rodar:** quando a fase de coleta entregar **≥5h por voz** exportadas pelo flywheel.
**O que responde:** (1) a receita provada do Pedro generaliza pra outras vozes? (2) misturar
base pública (0.15/0.30) melhora a língua **sem poluir a voz**? (3) qual a variância entre seeds?

**12 arms** (no teto — ver "Escuta" abaixo): por voz `r3_<voz>_solo` · `r3_<voz>_mix15` · `r3_<voz>_mix30`
+ `r3_pedro_pros` (A/B pontuação prosódica: mesmo dado do pedro_solo com train_pros.jsonl — docs/TRANSCRICAO-PROSODICA.md; requer `repunct_prosodic.py --report-only --emit-dataset` antes do rsync) + 2 seeds extras do vencedor esperado (`r3_pedro_mix15_s2/_s3`).
Receita FIXA (grid de 26 arms): lr 5e-5 · r=64 · texto raw · base-PT fundida · batch 8×4 · holdout 5%.

---

## 1 · Pré-requisitos (tudo ANTES de ligar a H100)

1. **Export do flywheel** (no Mac) — precisa fechar com ≥300 min/voz no resumo:
   ```bash
   python3 tools/data/export_flywheel.py --source supabase        # → data/flywheel/<voz>/{train.jsonl,segments/}
   python3 tools/data/export_flywheel.py --source supabase --dry  # só conferir os minutos por voz
   ```
2. **Dataset base do mix** em `data/base_pt/` (train.jsonl|transcribed.jsonl + segments/, 24kHz).
   É o corpus público local que "ensina língua" — 8 dos 12 arms usam ele; sem ele o preflight aborta.
3. **Smoke local sem GPU** (obrigatório — valida load/filter/mix/holdout):
   ```bash
   python3 runpod/smoke_r3_datapath.py    # tem que terminar em "✅ SMOKE OK"
   ```
4. **Pod:** base-PT em `/workspace/TTS-ptbr-data/runs/battery_A1_cml_cml_long/final`,
   `HF_TOKEN` em `/workspace/.env`, repo atualizado (`git pull`), e as métricas opcionais:
   ```bash
   pip install resemblyzer praat-parselmouth   # sem elas: spk_sim/prosody = null (treino roda igual)
   ```

## 2 · Passo a passo

```bash
# (Mac) sobe os dados — 1 rsync, confere contagem no fim (nada de 2>/dev/null)
rsync -av --progress -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  data/flywheel data/base_pt root@<IP>:/workspace/TTS-ptbr/data/
ssh root@<IP> -p <PORT> -i ~/.ssh/id_ed25519 \
  'wc -l /workspace/TTS-ptbr/data/flywheel/*/train.jsonl /workspace/TTS-ptbr/data/base_pt/*.jsonl'

# (pod) smoke do harness com o dado REAL, sem treinar (~2 min):
cd /workspace/TTS-ptbr && python3 runpod/train_voice.py --base-adapter '' \
  --mix "voz=1.0,base=0.15" --mix-dirs "voz=data/flywheel/pedro,base=data/base_pt" \
  --holdout 0.05 --speaker pedro --load-only

# (pod) lança o grid (fila resumível — pode relançar à vontade, pula o que já fechou):
setsid nohup bash runpod/grid_rodada3.sh > /workspace/grid/r3.out 2>&1 < /dev/null &

# monitorar:
tail -f /workspace/grid/r3.log            # fila + placar
cat /workspace/grid/r3.blocked            # se existir: preflight abortou (dado/base faltando)
watch -n60 nvidia-smi                     # GPU deve ficar 90-99%

# knobs (env, antes de lançar): PER_ARM_MIN=30 BUDGET_MIN=480 MIN_AUDIO_MIN=60 VOZES="pedro"
```

**Coleta (fim do grid, automática no pod):** o script gera **UM tar** verificado
(`/workspace/grid/r3_artifacts.tar.gz`) e imprime o comando de scp. No Mac:
```bash
mkdir -p runpod_samples/rodada3
scp -P <PORT> -i ~/.ssh/id_ed25519 root@<IP>:/workspace/grid/r3_artifacts.tar.gz runpod_samples/rodada3/
tar -tzf runpod_samples/rodada3/r3_artifacts.tar.gz | wc -l    # confere com o nº impresso no r3.log
tar -xzf runpod_samples/rodada3/r3_artifacts.tar.gz -C runpod_samples/rodada3/
```
Se aparecer `/workspace/grid/r3_collect.FAILED`, a coleta FALHOU de verdade — inspecionar
`$RUNS/r3_*` à mão. (Aprendizado do review_overnight.sh: scp por-arm com `2>/dev/null`
produziu 26 diretórios vazios. Nunca mais.)

## 3 · Custos (medido: **~50 h-áudio/H100-h** · H100 $3.29/h)

Treino ≈ `épocas × horas_de_áudio / 50` H100-h; alvo ~3 épocas → `PER_ARM_MIN ≈ 3.6 × h_áudio da fonte`.
Overhead fixo por arm (setup+eval WER+spk_sim/prosódia+push) ≈ 12 min.

| dado/voz | PER_ARM_MIN sugerido | 12 arms (treino+overhead) | custo |
|---|---|---|---|
| 5h  | 25 | ~6.8h  | **~$22** |
| 10h | 40 | ~9.5h  | **~$31** |
| 15h | 45 (cap: ~2.5 épocas) | ~10.5h | **~$35** |

`BUDGET_MIN=720` (12h) cobre o pior caso com folga; teto de gasto ≈ **$39**.
Cache de tokenização: o 1º arm de cada composição tokeniza (~min em 15h), os demais REUSAM
(`tok-cache: ... (REUSO)` no log) — é o que mantém a conta acima realista.

## 4 · Go / No-go

**GO pra ligar a GPU** (todos):
- [ ] export ≥ **300 min/voz** (resumo do export_flywheel) — abaixo disso, volta pra coleta (a Rodada 3 não conserta falta de dado);
- [ ] `smoke_r3_datapath.py` = ✅ e `--load-only` no pod = ✓ pras 3 vozes;
- [ ] `data/base_pt` presente (senão só arms solo fazem sentido — rode `VOZES=... ` com o grid editado, não ignore o preflight).

**GO pós-rodada (promover um arm a checkpoint da voz):** POR VOZ, comparar mix15/mix30 vs solo:
- WER mediana do mix ≤ solo **E** spk_sim do mix ≥ solo − 0.02 → mistura aprovada;
- Δ entre arms só é sinal se for **maior que a variância entre s2/s3** (senão é ruído de seed);
- eval_loss do held-out: mix ≤ solo = generalização real (não decorou);
- **escuta humana decide o vencedor final** — WER não mede sotaque (Treino 1: "soa gringo" foi invisível no WER).

**NO-GO / alarme:** WER do mix cai mas spk_sim despenca → a base está **poluindo a voz**
(regra do projeto: público ensina língua, NUNCA polui a voz) → descartar mix30, re-testar mix a 0.05-0.10.

## 5 · Escuta (o gargalo real — dimensione por ela)

Capacidade: **~top-4 arms por noite** de escuta (4×14 = 56 frases). 12 arms = **3 noites**.
Ordem: (1) melhor WER por voz, (2) o solo da mesma voz (par A/B), (3) s2/s3 só se o vencedor for mix15.
**NÃO adicione arms ao grid sem adicionar noites de escuta** — arm que ninguém ouve é GPU queimada:
o teto de 12 não é técnico, é humano.
