# RunPod — runbook da 2ª esteira de treino

> **Pra que serve:** rodar o treino do CSM numa A100 paga (~$1,39/h) **sem cap de
> sessão do Colab** e, principalmente, deixar o **Claude debugar direto via SSH**
> (sem você relayar erro a cada bug). Não é pra economizar — o Colab Pro+ ainda é
> a A100/h mais barata. É pra **paralelizar** e pra **velocidade de debug**.
> Ver `research/dossier-2026-06/41-gpu-alternativas-colab.md`.

## TL;DR (o caminho feliz)
1. Cria conta RunPod + deposita **$60** (cartão BR ou USDC).
2. Adiciona a **chave SSH pública do seu Mac** em *Settings → SSH Public Keys*.
3. Cria um **Network Volume 50GB** (`/workspace`) numa região com A100.
4. Sobe um **Pod** (template *RunPod PyTorch*), GPU A100-80, anexa o volume, seta
   env vars `HF_TOKEN` e `GH_TOKEN`.
5. Me cola o **comando SSH** do pod → eu clono o repo, rodo `setup.sh` e disparo a
   bateria, tudo direto.
6. No fim: resultado vai pro **HF Hub** (`--push-hub`) → **desligo o pod** (volume fica).

---

## 1. Conta + crédito
- Cria conta em **runpod.io**.
- *Billing* → deposita **$60**. Cartão BR funciona (Stripe) — leva **IOF 3,5%**
  (~R$11 sobre $60). Pra zerar o IOF, dá pra pagar em **USDC** (cripto). Crédito
  **não expira**.

## 2. Chave SSH (é assim que eu te ajudo direto)
No seu Mac, confere se já tem chave:
```bash
ls ~/.ssh/id_ed25519.pub        # se existir, pula a geração
ssh-keygen -t ed25519 -C "runpod"   # ENTER em tudo se NÃO existir
cat ~/.ssh/id_ed25519.pub        # copia ESSA linha (a .pub — a PÚBLICA)
```
No RunPod: *Settings → SSH Public Keys → cola a linha `.pub`*.
> ⚠️ A chave **privada** (`id_ed25519`, sem `.pub`) **NUNCA** sai do seu Mac e
> **nunca** vai pro chat. Você só me passa o *comando* de conexão (host + porta).

## 3. Network Volume (persistência — substitui o Drive)
- *Storage → Network Volumes → New*. Tamanho **50GB** (~$5/mês). Escolhe uma
  **região que tenha A100** (ex.: `EU-RO-1` ou `US`). Anota a região — o Pod tem
  que ser criado na MESMA.
- O volume monta em **`/workspace`** e sobrevive ao desligar o pod. **Tudo que
  importa mora aqui** (repo + checkpoints).

## 4. Criar o Pod
- *Pods → Deploy*. GPU: **A100 PCIe 80GB** ($1,39/h, Community) pro treino; ou
  **RTX 4090 / L4** ($0,39–0,69/h) pra debug barato.
- *Template:* **RunPod PyTorch** (já vem Jupyter + SSH + torch/CUDA).
- *Network Volume:* anexa o de 50GB (mesma região).
- *Environment Variables* (engrenagem do template) — adiciona:
  - `HF_TOKEN` = teu token HF
  - `GH_TOKEN` = teu token GitHub (pra clonar o repo privado)
- Deploy. Em ~30s o pod sobe e mostra o **comando SSH**.

## 5. Me dá o acesso
Cola aqui no chat **só o comando de conexão** que o RunPod mostrar, algo como:
```
ssh root@213.xxx.xxx.xxx -p 40xxx -i ~/.ssh/id_ed25519
```
(ou a variante `ssh xxxx@ssh.runpod.io -i ~/.ssh/id_ed25519`). Com isso eu rodo, a
partir do **teu Mac**, comandos no pod — sem você no meio.

## 6. Primeira vez no pod (eu faço, ou você cola e roda)
```bash
cd /workspace
git clone https://$GH_TOKEN@github.com/pedrocormann/TTS-ptbr.git
cd TTS-ptbr
bash runpod/setup.sh            # instala deps (~3-5 min)
```

## 7. Rodar
```bash
# valida o ambiente em ~3 min (1 step + 1 geração) — SEMPRE antes da bateria:
python runpod/train_bateria.py --preflight-only

# bateria completa em background (some pro log, não segura o SSH):
bash runpod/run_bg.sh --push-hub pedrocormann/tts-ptbr-bateria
tail -f /workspace/bateria.log
```
Flags úteis (eu uso pra dirigir experimentos):
`--experiments A1_cml` · `--lr 2e-5` · `--per-exp-min 30` · `--batch 4 --accum 8`

## 8. Salvar + DESLIGAR (importante!)
- Com `--push-hub`, o `BATERIA_results.md` + adapters vão pro teu **HF Hub**
  (repo privado) a cada experimento — seguro mesmo se o pod morrer.
- **Quando acabar: *Pods → Stop/Terminate*.** Pod ligado **queima crédito mesmo
  parado de treinar**. O Network Volume **continua** (você só paga o storage ~$5/mês),
  então é só subir outro pod e anexar o volume da próxima vez.

---

## Custos (referência)
| Item | Custo |
|---|---|
| Bateria completa (3 exp, ~2,5h A100-80) | ~$3,50 |
| Estágio A cheio (3h) | ~$4,17 |
| Network Volume 50GB | ~$5/mês |
| Debug em 4090 ($0,69/h) | centavos por hora |
| **Teu saldo $60 cobre** | dezenas de runs + semanas de folga |

## Checklist anti-vacilo
- [ ] Pod e Network Volume na **mesma região**
- [ ] `HF_TOKEN` e `GH_TOKEN` setados como **env var do pod** (não no chat)
- [ ] Rodou `--preflight-only` antes da bateria
- [ ] Usou `--push-hub` (disco do pod é efêmero)
- [ ] **Desligou o pod** ao terminar (volume fica)

## Pra debug barato (recomendado)
Sobe o pod numa **4090/L4** pra eu acertar o código (preflight, ajustes), e só
troca pra **A100-80** quando for soltar o run de verdade. GPU barata + meu loop
de debug = quase de graça.
