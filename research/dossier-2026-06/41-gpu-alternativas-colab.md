# GPU fora do Colab — 2ª esteira de treino (pesquisa 2026-06-15)

> Pesquisa multi-agente (7 frentes + síntese) sobre onde treinar CSM/Moshi/Qwen3
> a partir do Brasil, em paralelo ao Colab. Preços verificados na web em 2026-06-15.
> Complementa `40-colab-compute.md` (baseline Colab) — aqui preenchemos as lacunas
> de pagamento BR, $/h por GPU e free credits.

## Veredito

**A 2ª esteira não é pra economizar** — o **Colab Pro+ continua a A100/h mais barata**
(~$0,54/h efetivo via CU). Ela serve pra **paralelizar** e **furar limites do Colab**.

- **Esteira GRÁTIS, paralela, HOJE → Kaggle Notebooks.** Gêmeo do Colab, US$0,
  30h GPU/semana, T4x2 (32GB). CSM-1B LoRA cabe folgado (precisa ≥12GB).
  Porte baixo: Drive→`/kaggle/working`, Colab Secrets→Kaggle Secrets, **bf16→fp16**
  (T4/P100 não têm bf16). Gargalo = sessão até 12h (Estágio A em T4 ~6-9h; usar
  "Save & Run All" headless).
- **Esteira PAGA barata + flexível → RunPod.** Roda nosso `.ipynb` quase igual ao
  Colab (Jupyter nativo, ~30s), A100 80GB $1,39/h Community, Network Volume
  substitui o Drive. Estágio A ~$4,17. Porte ~1 célula/notebook.
- **Plano B nacional (sem IOF) → GPUBrasil.** PIX, BRL, A100 40GB self-service
  (~R$12,87/h). Estágio A ~R$38,61. Provider pequeno; trate disco como efêmero
  (checkpoint pro HF Hub).
- **Upside → Modal Startup Program ($25k, sem equity).** Aplicar em paralelo; se
  aprovar, vira esteira "de graça" pra escala. Porte = script (`@app.function`).

## Tabela comparativa (do mais recomendado pro menos)

| # | Provider | GPU p/ nós + US$/h | Roda .ipynb | Porte | Estágio A (3h) | Pagamento BR | Free tier |
|---|----------|--------------------|-------------|-------|----------------|--------------|-----------|
| 1 | **Kaggle** | T4x2 32GB / P100 — **US$0** | Sim (gêmeo Colab) | low (bf16→fp16) | **US$0** (~6-9h) | grátis | 30h/sem, sessão 12h |
| 2 | **RunPod** | A100 80GB $1,39; L4 $0,39; 4090 $0,69 | Sim (Jupyter ~30s) | low | **~$4,17** | cartão BR (USD+IOF) ou cripto | ~$5 após gastar $10 |
| 3 | **GPUBrasil** | A100 40GB ~$2,38; A4000 16GB | Parcial (IaaS) | low | **~$7,15** sem IOF | **PIX+BRL** ✅ | R$25 no 1º depósito |
| 4 | **Modal** | A100 40GB $2,10/80GB $2,50; L4 $0,80 | Não (script) | low-med | **~$6,30** | cartão BR (USD+IOF) | **$30/mês** + $25k startup |
| 5 | **Vast.ai** | A100 40GB $0,56; T4 $0,15; 4090 $0,40 | Parcial | low-med | **~$1,68** (+ barato/h) | cartão BR/cripto | simbólico |
| 6 | **Lightning AI** | A100 40GB ~$1,89; L4 ~$0,70 | Parcial (Studio) | low-med | **~$5,67** | cartão BR (USD+IOF) | **$15/mês** (~80h) |
| 7 | **HF Jobs** | A100 80GB $2,50; L4 $0,80; T4 $0,40 | Não (train.py) | low-med | **~$7,50** + PRO $9/mês | cartão BR (USD+IOF) | nenhum (PRO obrig.) |
| 8 | **AWS sa-east-1** | g6 L4 24GB $1,66 / **$0,19 spot** | Parcial | medium | **~$1 spot** (sem A100 em SP) | **BRL+PIX** ✅ | $100-200 signup |
| 9 | **Magalu Cloud** | L40S 48GB ~$1,60 (sem A100) | Parcial (CLI mgc) | low-med | **~$4,80** sem IOF | cartão BR; PIX sob pedido | nenhum |
| 10 | **SaladCloud** | A100 40GB **$0,40** (interrompível) | Não (Docker) | med-high | **~$1,20** (com risco) | cartão (USD+IOF) | nenhum |

Descartados por má aderência: Replicate/Baseten (servir, não treinar), Paperspace
(em transição p/ DigitalOcean), Vertex/Colab Enterprise (burocrático, quota gating),
Azure Brazil South / OCI SP (pagamento BR fraco, A100 gated), AutoTrain/ZeroGPU
(não treina horas), SDumont (air-gapped). **Thunder Compute** ($0,78/h A100-80, o
mais barato de A100-80 do dossiê 40) ficou fora das 7 frentes — **revalidar preço 2026**.

## Pegadinhas pro Brasil

- **IOF = 3,50%** (unificado por decreto mai/2025, qualquer pagamento externo no
  cartão). Irrelevante em runs de $4-8; soma no fixo mensal (Modal/HF PRO/Lightning).
  **Cripto (USDC) ou provider BR (PIX/BRL) zeram o IOF.**
- **Quota de GPU em hyperscaler = bloqueador real, não preço.** Conta nova vem com
  quota 0/baixa; aumento leva minutos a ~1 semana. AWS sa-east-1 nem tem A100 farto
  (Moshi fica fora de SP). Hyperscaler-SP **não** é "2ª esteira hoje" — é projeto à parte.
- **Latência de upload RJ→US:** subir ~30-40h de áudio é lento. Mitigação: dataset já
  vive no **HF Hub** — puxa direto com `hf_transfer` (já nos notebooks); só o
  checkpoint volta.
- **Storage efêmero = perda nº1 de run.** RunPod/Vast/Salad/GPUBrasil/Modal-sem-Volume
  zeram o disco ao parar. **Sempre** checkpoint no Network Volume / modal.Volume / HF Hub.
- **bf16 não roda em T4/P100** (Kaggle grátis, GCP-SP, AWS g4dn). Onde for T4: fp16 ou QLoRA.
- **SaladCloud é armadilha sedutora:** A100 $0,40/h é o + barato do mundo, mas nós caem
  sem aviso — sem checkpoint-resume robusto (código novo), perde 3h de treino.

## Reconciliação com o baseline Colab (dossiê 40)

| Run | **Colab Pro+ (baseline)** | Kaggle | RunPod | GPUBrasil | Modal |
|-----|---------------------------|--------|--------|-----------|-------|
| Estágio A 3h A100 | **~$1,62** (A100-40) / ~$2,26 (bateria A100-80) | **$0** (T4, 2-3x + lento) | ~$4,17 | ~$7,15 | ~$6,30 |
| Estágio B ~1h | ~$0,12 (T4) / ~$0,17 (L4) | **$0** | ~$0,39 | ~$0,33 | ~$0,59 |

Colab Pro+ continua o A100/h mais barato. A 2ª esteira é pra **paralelizar** e
**furar limites**, não pra economizar.

## Plano de ação

### Fase 1 — Kaggle grátis (HOJE, ~2-3h de adaptação dos notebooks)
1. **Pedro:** conta Kaggle → verifica telefone (BR ok) pra liberar GPU + "Internet on".
   `HF_TOKEN` em *Add-ons → Secrets*.
2. **Claude:** adapta nb2 (Estágio B) primeiro — Drive→`/kaggle/working` (+ Kaggle
   Dataset privado p/ artefatos), `userdata.get`→`UserSecretsClient().get_secret`,
   **`bf16=True`→`fp16=True`**, `attn_implementation="sdpa"`.
3. **Claude:** versão "Save & Run All" headless do Estágio A (até 12h), `save_steps`
   baixo escrevendo em `/kaggle/working` + push pro HF Hub no fim.
4. **Custo:** US$0. Estágio B ~1h; Estágio A ~6-9h num commit.

### Fase 2 — RunPod paga (quando precisar de A100 sem cap de tempo, ~1-2h)
1. **Pedro:** conta RunPod, deposita ~$10 (cartão BR/Stripe ou USDC). Network Volume
   ~50GB (~$5/mês) em `/workspace`. Pod template "RunPod PyTorch" (Jupyter), `HF_TOKEN`
   como env var.
2. **Claude:** reescreve 1 célula de setup/notebook: Drive→`/workspace`, Colab Secrets→
   `os.environ['HF_TOKEN']`. Resto idêntico (transformers==4.52.3, peft, CSMTrainer).
3. **Custo:** Estágio A ~$4,17 + ~$5/mês volume.
4. **Paralelo:** aplicar no Modal Startup Program ($25k).
