# RUNBOOK — Grid Overnight Treino-2 (18/19-jun-2026)

**Janela:** ~01:57 UTC → **14:00 UTC (11h BRT)** · ~12h · H100 SXM ~$3.29/h ≈ **~$39** dos ~$45.
**Insumo:** voz do Pedro **curada à mão** (`transcribed_clean.jsonl`, 260) + auto (262) + full (362) + subset (130).

## O que está rodando no pod
- `grid_overnight.sh` — orquestrador: 17 arms de ciência + fill, **back-to-back, batch 8 + 8 workers** (~1.4s/it, GPU 90-99%). RESUMÍVEL (pula arm com `stage_b_result.json`), DEADLINE-AWARE (capa minutos p/ fechar antes das 14:00 UTC).
- `watchdog_overnight.sh` — **a prova-de-idle real (roda no pod, imune ao Mac)**: a cada 120s, se a GPU está ociosa e nenhum orquestrador vivo → re-lança o grid. Também limpa checkpoints se disco >90%.
- `review_overnight.sh` — roda no **Mac** via cron a cada 20min: coleta wavs+WER → `runpod_samples/grid_overnight/`, re-lança o watchdog se caiu.

## Os arms (ordem = prioridade; se o deadline cortar a cauda, a ciência-chave já rodou)
| arm | pergunta |
|---|---|
| c0_curated | **control** — Stage B na voz curada (260) |
| c_g2p | **SOTAQUE** (fonético, CharsiuG2P) |
| a0_auto | curado-vs-auto (262) |
| c_norm | número→palavra no treino |
| c_full362 | a curadoria ajudou? (362 brutos) |
| c_lr1e4 / c_lr2e5 | lr ↑ / ↓ |
| c_r128 / c_r32 | capacidade ↑ / ↓ |
| c_long (90min) | convergência |
| c_half130 | curva de escala de dado |
| c_g2p_r128 / c_g2p_long | sotaque + capacidade / convergência |
| c_g2p_auto / c_g2p_full | G2P depende de curadoria? / G2P com mais dado |
| c_norm_full | número × mais dado |
| c_deep (140min) | teto de convergência na voz gold |
| fill_N_* | enche o tail ciclando modo (raw/norm/g2p) com seeds |

## Como ler de manhã
```bash
bash runpod/review_overnight.sh          # tabela de WER + coleta o que falta
ls runpod_samples/grid_overnight/        # 14 wavs por arm, pra ouvir no rate_app
```
- **WER mede balbúcio/inteligibilidade, NÃO sotaque** (Treino 1: "soa gringo" foi invisível no WER). Pros arms de G2P, **ouvir** os samples é o juiz.
- Vencedor candidato = menor WER mediana COM voz natural (ouvir). Vira o bloco **"Treino 2"** na Trilha.

## Parar / pausar
```bash
ssh root@31.24.80.44 -p 17313 -i ~/.ssh/id_ed25519 'pkill -f watchdog_overnight; pkill -f grid_overnight; pkill -f train_voice.py'
# e pausar o pod no painel RunPod p/ parar de cobrar
```
O cron de revisão se auto-deleta depois das 14:00 UTC.
