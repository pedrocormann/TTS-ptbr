Verificação completa. Compilando os vereditos e retornando o relatório integral.

# VERIFICAÇÃO (verificador adversarial, 02/jul/2026)

Método: 8 claims load-bearing checados na fonte citada via fetch direto + pelo menos 1 fonte independente cada. Fontes primárias fetchadas hoje: runpod.io/pricing, lambda.ai/pricing, computeprices.com/gpus/h100, arXiv 2504.19146 (HTML), arXiv 2404.09956v2 (HTML), arXiv 2410.06885v3 (HTML), unsloth.ai/docs, busca independente para Vast.ai, e o runbook local do projeto.

| # | Claim | Veredito | Justificativa |
|---|---|---|---|
| V1 | RunPod Community: H100 SXM $3.29 / PCIe $2.89 / A100 $1.39–1.49 / B200 $5.89 / 4090 $0.69 / 5090 $0.99 — **preço-base do modelo inteiro** | **CONFIRMADO** | Fetch de runpod.io/pricing hoje (02/jul/2026): todos os 7 números batem exatamente. |
| V2 | Lambda H100 SXM $3.99–4.29 on-demand; A100 80GB $2.79 só em nó 8× | **CONFIRMADO** | Fetch de lambda.ai/pricing hoje: valores idênticos; A100 80GB de fato só 8×. Omissão menor: Lambda TEM H100 PCIe 1× a $3.29 (tabela mostra "—") — não muda decisão. |
| V3 | Vast.ai H100 ~$1.87 "verified", faixa $1.60–2.30; modelo usa $2.00 | **PLAUSÍVEL** | Página da Vast é JS (confirmado: fetch não renderiza preço). Independentes hoje: vast.ai/pricing/gpu/H100-PCIE anuncia $2.00/h, Thunder Compute/IntuitionLabs mostram start ~$2.01. O **$2.00 usado no modelo de custo está CONFIRMADO**; o ponto $1.87 e o piso $1.60 podem estar ~10% otimistas. |
| V4 | Vast.ai RTX 4090 $0.31–0.35 (âncora da recomendação "eval/geração em 4090 Vast") | **CONFIRMADO** | Página da Vast anuncia "$0.35/hr" no título; independentes (SynpixCloud abr/2026, getdeploying): interruptible $0.29–0.31, on-demand $0.35–0.50. Faixa citada é o piso on-demand — realista. |
| V5 | Muyan-TTS (T2 + headline): 19.200 A100-h para 100k h × 15 ép. (→ ~78 h-áudio/A100-h); **$30k dos $50k foram dados (60.000 A10-h, 150k→100k h)**; base Llama-3.2-3B | **CONFIRMADO** | arXiv 2504.19146 verbatim: Table 1 = $30K dados + $19.2K LLM ($1/A100-h) + $1.34K decoder = $50.54K; "60,000 GPU hours" em A10; "15 epochs"; "Llama-3.2-3B". Aritmética 100.000×15/19.200 = 78.1 fecha. Claim mais load-bearing do relatório e o mais sólido. |
| V6 | Tango 2 (T6): ~15k pares, 2×A100, ~3.5h total (1 ép. SFT + 4 ép. DPO) — âncora de que DPO-treino é barato | **CONFIRMADO** | arXiv 2404.09956 verbatim: "≈15k samples" (15.025), "executed on two A100 GPUs which takes about 3.5 hours in total", 1 SFT + 4 DPO. |
| V7 | F5-TTS (T5): 100k updates ≈ 8h em 8×H100 | **CONFIRMADO** (com ressalva) | arXiv 2410.06885 Appendix B.7 verbatim: "Every 100K update takes approximately 8 hours on 8 NVIDIA H100 SXM GPUs" — mas refere-se aos modelos *small* dos ablations; o base foi 1.2M updates, ~1 semana em 8×A100. Como o relatório usa só como "ref. de outra arquitetura", ok. |
| V8 | Unsloth (T4): 1.5× mais rápido / −50% VRAM; "algumas épocas em 3h de dados = 1–2h num T4" | **CONFIRMADO** | Docs da Unsloth verbatim: "1.5x faster with 50% less memory" e "on a Colab T4 GPU, a few epochs on 3h of data may take 1-2 hours". |

Ressalvas menores (não mudam decisões):
- **RunPod "Secure $2.69"** (via computeprices): o número $2.69 existe no agregador (atualizado 02/jul), mas o agregador não rotula Community/Secure, e Secure é normalmente MAIS cara que Community ($3.29) — rótulo provavelmente invertido. Irrelevante: o modelo usa $3.29. → PLAUSÍVEL.
- **T1 (âncora local, 50 h-áudio/H100-h)**: runbook local confirma 1.4s/it, batch 8, H100 $3.29/h; aritmética (8 clipes × ~10s ÷ 1.45s ≈ 55 h-áudio/h) fecha com os ~50 declarados. Inconsistência interna: o runbook registra "GPU 90-99%" pós-fix, não "util ~57%" — se a util real era maior, a tabela é ainda mais teto do que o texto sugere. Não verificável na web (medição própria).

**Conclusão do verificador**: nenhum claim load-bearing refutado. Os preços-âncora (RunPod $3.29, Vast $2.00, 4090 $0.31–0.35) e as três âncoras de throughput de papers (Muyan, Tango 2, F5-TTS) conferem na fonte primária, várias verbatim. O headline (~US$ 900–1.800 RunPod / ~US$ 500–1.000 Vast; "dado é o gargalo, não GPU") é aritmética consistente sobre âncoras confirmadas. Único ajuste sugerido: tratar Vast H100 como ~$2.00 (não $1.87) e ignorar o rótulo "Secure $2.69".

---

# Custos de GPU para fine-tune de TTS pt-BR — pesquisa de preços e modelo de custo (02/jul/2026)

## 1. Tabela de preços (US$/GPU-hora)

| GPU | RunPod (Community) | RunPod (Secure) | Lambda (on-demand) | Vast.ai (marketplace) |
|---|---|---|---|---|
| **H100 80GB SXM** | $3.29 [runpod.io/pricing](https://www.runpod.io/pricing) (02/jul/2026) | $2.69 [computeprices](https://computeprices.com/gpus/h100) (02/jul/2026); [Northflank](https://northflank.com/blog/runpod-gpu-pricing) (dez/2025) | $3.99–4.29 [lambda.ai/pricing](https://lambda.ai/pricing) (02/jul/2026) | ~$1.87 verified, faixa $1.60–2.30 [vast.ai](https://vast.ai/pricing) (jul/2026, flutuante) |
| **H100 80GB PCIe** | $2.89 (runpod.io, 02/jul) | $2.39 (Northflank, dez/2025) | — | ~$1.50–1.80 (Hyperbolic $1.50 como ref. de piso, computeprices 02/jul) |
| **A100 80GB** | $1.39 PCIe / $1.49 SXM (runpod.io, 02/jul) | $1.49 (Northflank, dez/2025) | $2.79 (só nó 8×; lambda.ai, 02/jul) | **$0.735** SXM 80GB [computeprices/vast](https://computeprices.com/providers/vast) (05/jun/2026) |
| **B200 (180/192GB)** | $5.89 (runpod.io, 02/jul) | $5.19 (Northflank, dez/2025) | $6.69–6.99 (lambda.ai, 02/jul); $4.99–5.29 em mai/2026 ([Spheron](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/)) | pouca oferta, n/d |
| **RTX 4090 24GB** | $0.69 (runpod.io, 02/jul); $0.34 em dez/2025 (Northflank) | — | — | **$0.31–0.35** [vast.ai/pricing/gpu/RTX-4090](https://vast.ai/pricing/gpu/RTX-4090) (jul/2026) |
| **RTX 5090 32GB** | $0.99 (runpod.io, 02/jul) | — | — | ~$0.40–0.70 (hosts recebem $0.30–0.60; [vast.ai article](https://vast.ai/article/how-much-money-can-you-earn-renting-out-your-gpu-on-vast-ai), jul/2026 — confiança baixa) |

Notas: (i) Vast.ai é leilão — o mesmo H100 varia ±50% no dia; páginas de preço deles são JS, números acima vêm de agregadores + páginas estáticas. (ii) O agregador computeprices lista "Modal $0.067/h H100" — é anomalia de billing serverless por fatia, ignorar. (iii) Spot RunPod/Spheron ≈ 40–65% de desconto ([Spheron, mai/2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/)). (iv) Hyperscalers fora de cogitação: AWS H100 ~$6.88, Azure ~$12.29.

## 2. Premissas de throughput (com fonte)

| # | Premissa | Valor | Fonte |
|---|---|---|---|
| T1 | **CSM-1B FT em H100 SXM (medido NESTE projeto)**: batch 8 (eff. 32), 1.4–1.45 s/it após fix de dataloader (util média ~57%), clipes ~10s → 8 clipes/1.45s ≈ **50 audio-h processadas por H100-h** (faixa 35–65 conforme duração média do clipe) | ~50 h-áudio/H100-h | logs locais: `runpod/RUNBOOK-overnight.md` + memória `project-csm-training-gotchas.md` (jun/2026) |
| T2 | Muyan-TTS (Llama-3.2-**3B full CPT**): 100k h × 15 épocas = 1.5M passes-hora-áudio em 19.200 A100-h → **~78 h-áudio/A100-h** (multi-nó otimizado, packing) | ~78 h-áudio/A100-h | [arXiv 2504.19146](https://arxiv.org/html/2504.19146v1) |
| T3 | Moshi LoRA r128 = 39.6 GB em 1×H100, ~12k tok/s | ~12k tok/s | [moshi-finetune README](https://github.com/kyutai-labs/moshi-finetune) (via dossiê local `60-compute-budget.md`) |
| T4 | Unsloth: TTS FT 1.5× mais rápido / −50% VRAM; "algumas épocas em 3h de dados = 1–2h num T4" → H100 ≈ 10–20× T4, consistente com T1 | — | [Unsloth TTS docs](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning) |
| T5 | F5-TTS (ref. de outra arquitetura): 100k updates ≈ 8h em 8×H100 | — | [arXiv 2410.06885](https://arxiv.org/pdf/2410.06885) |
| T6 | DPO em áudio: Tango 2 = **15k pares, 2×A100, ~3.5h total** (SFT 1 ép. + DPO 4 ép.) = 7 A100-h | 15k pares ≈ 7 A100-h | [arXiv 2404.09956](https://arxiv.org/pdf/2404.09956) |

Derivadas (conservadoras): LoRA/FT CSM-1B = 50 h-áudio/H100-h; **full-FT 1B = ×0.7** (35); **Orpheus-3B = ×0.4** (20). Overhead fixo por run (setup, ckpt, geração de amostra): +15–30%.

## 3. Modelo de custo (preço base: H100 RunPod $3.29/h · Vast $2.00/h)

### (a) SFT LoRA — 15h de áudio × 3 vozes × grid de 5 configs = 15 runs
3 épocas/run = 45 passes-hora-áudio ÷ 50 = 0.9 H100-h + overhead ≈ **1.2–1.5 H100-h/run** → 18–23 H100-h total.
- **RunPod H100: US$ 60–75** · Vast H100: US$ 36–46 · RTX 4090 (LoRA 1B cabe em 24GB, ~3–4× mais lento): 55–90 GPU-h ≈ US$ 20–60
- Grid com 10 épocas: ×3 → **US$ 180–250** (RunPod H100)

### (b) CPT pt-BR (2–3 épocas, +15% overhead)
| Cenário | H100-h | RunPod ($3.29) | Vast ($2.00) | Wall-time (1×H100) |
|---|---|---|---|---|
| 1.000h, LoRA-large (r≥128 + embeddings) | 46–70 | **US$ 150–230** | US$ 92–140 | 2–3 dias |
| 1.000h, full-FT 1B | 66–100 | **US$ 220–330** | US$ 130–200 | 3–4 dias |
| 2.800h, LoRA-large | 130–195 | **US$ 430–640** | US$ 260–390 | 5.5–8 dias |
| 2.800h, full-FT 1B | 185–275 | **US$ 610–905** | US$ 370–550 | 8–11 dias → usar 4×H100 (+10–15%) |

Sanity check: pelo rate do Muyan (T2, 3B full multi-nó), 2.800h×3 ép. sairia ~108 A100-h ≈ **US$ 150** — ou seja, com packing de sequência e util >90% dá pra ficar 2–4× abaixo da tabela. A tabela usa o throughput MEDIDO do projeto (util 57%), então é teto realista, não otimista.

### (c) Rodadas de eval/geração em lote
500–1.000 clipes de ~10s por rodada (1.5–3h de áudio gerado), geração batched 2–6× tempo real → 0.5–2 GPU-h/rodada.
- H100: **US$ 2–7/rodada** · 4090/5090: **US$ 0.50–2/rodada** → 20 rodadas/mês ≈ US$ 10–140/mês. Eval é ruído no orçamento; rodar em 4090 Vast.

### (d) DPO com 5–20k pares de preferência
Duas parcelas — o treino é barato, **gerar os candidatos é o custo dominante**:
- Treino DPO (policy+ref, 2 ép., 20k pares ≈ 330 passes-hora-áudio-equivalentes): 7–10 H100-h → **US$ 25–35** (âncora T6: 15k pares = 7 A100-h ≈ US$ 10)
- Geração de candidatos (40–80k amostras de ~10s = 110–220h de áudio): 20–110 GPU-h → US$ 15–110 em 4090/5090 Vast, US$ 65–360 se teimar em H100
- Scoring (Whisper/judge): ~US$ 5
- **Total por rodada DPO: US$ 50–200 (20k pares) · US$ 15–60 (5k pares)**

### Headline
O programa de compute inteiro (a+b+c+d, incluindo 1 CPT full em 2.800h + 2 rodadas DPO + 3 meses de eval) cabe em **~US$ 900–1.800 no RunPod H100, ~US$ 500–1.000 no Vast**. O gargalo financeiro não é GPU: no Muyan-TTS, US$ 30k dos US$ 50k foram **processamento de dados** (60.000 A10-h para limpar 150k→100k horas ≈ 2.5h de áudio limpas por GPU-h) — coerente com o diagnóstico do projeto de que dado é o gargalo, não treino.

Sources:
- [RunPod Pricing](https://www.runpod.io/pricing) · [Lambda Pricing](https://lambda.ai/pricing) · [Vast.ai Pricing](https://vast.ai/pricing) · [Vast RTX 4090](https://vast.ai/pricing/gpu/RTX-4090)
- [Northflank: RunPod pricing breakdown](https://northflank.com/blog/runpod-gpu-pricing) · [Spheron: GPU Cloud Pricing 2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/) · [ComputePrices H100](https://computeprices.com/gpus/h100) · [ComputePrices Vast](https://computeprices.com/providers/vast) · [aimultiple GPU index](https://aimultiple.com/gpu-index)
- [Muyan-TTS (arXiv 2504.19146)](https://arxiv.org/html/2504.19146v1) · [Tango 2 DPO (arXiv 2404.09956)](https://arxiv.org/pdf/2404.09956) · [F5-TTS (arXiv 2410.06885)](https://arxiv.org/pdf/2410.06885) · [Unsloth TTS docs](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning) · [Llasa (arXiv 2502.04128)](https://arxiv.org/abs/2502.04128) · [Llasagna: LLaSA em italiano](https://huggingface.co/blog/Steveeeeeeen/llasagna) · [Speechmatics: finetune CSM em novas línguas](https://blog.speechmatics.com/sesame-finetune) · [Align2Speak (arXiv 2509.21718)](https://arxiv.org/pdf/2509.21718)
- Âncoras locais do projeto: `/Users/pedrocormann/Downloads/TTS-ptbr/runpod/RUNBOOK-overnight.md` (1.4s/it, batch 8, H100 $3.29/h) · `/Users/pedrocormann/Downloads/TTS-ptbr/research/dossier/60-compute-budget.md` (moshi 12k tok/s)

Fontes de verificação independentes usadas: [Thunder Compute H100 pricing (jul/2026)](https://www.thundercompute.com/blog/nvidia-h100-pricing) · [IntuitionLabs H100 comparison](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison) · [Vast H100 PCIe $2.00/hr](https://vast.ai/pricing/gpu/H100-PCIE) · [SynpixCloud Vast vs RunPod 4090](https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing) · [getdeploying RTX 4090](https://getdeploying.com/gpus/nvidia-rtx-4090)