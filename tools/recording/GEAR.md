# GEAR — lista de compra (setup “do zero”, 3 vozes + reuniões diárias)

> Objetivo duplo: (1) sessões solo de dataset (voz dedicada) e (2) **reuniões
> UNFLAT com 1 canal por pessoa**. Por isso a escolha-chave é **microfone
> DINÂMICO de proximidade**, não condensador: condensador numa sala de reunião
> capta TODO MUNDO (crosstalk entre canais arruína a separação por falante);
> dinâmico colado na boca isola cada voz e perdoa sala sem tratamento.

## Kit recomendado (~R$ 3,5-5,5k total, jun/2026 — preços de referência BR)

| Item | Qtd | Opções (qualquer uma serve) | ~Preço un. |
|---|---|---|---|
| Mic dinâmico de broadcast | 3 | Audio-Technica AT2040 · Shure MV7 (modo XLR) · Samson Q9U · (budget: Samson Q2U, serve bem) | R$ 800-1.600 (Q2U ~R$ 500) |
| Interface 4 entradas XLR | 1 | Behringer UMC404HD (melhor custo) · Focusrite Scarlett 4i4 · MOTU M4 | R$ 1.200-2.500 |
| Braço articulado ou pedestal de mesa | 3 | qualquer um decente | R$ 80-150 |
| Pop filter/espuma | 3 | espuma já vem em alguns dinâmicos | R$ 30-60 |
| Cabo XLR 3m | 3 | balanceado | R$ 50-80 |
| Fone fechado (monitorar sessões solo) | 1 | ATH-M20x/M40x ou similar | R$ 300-700 |

**Por que 1 interface e não 3 mics USB:** três USB no mesmo computador têm clock
independente → drift de sincronia entre canais ao longo de 1h de reunião (mata o
alinhamento por falante). Uma interface multi-canal grava os 3 canais com UM
clock — o `record_meeting.py` espera exatamente isso (1 device, N canais).

## Setup da sala de reunião

- Mic a **5-10 cm da boca** de cada um (dinâmico pede proximidade), levemente
  off-axis; falar “por cima” do mic, não por trás.
- Ganho por canal: pico entre −12 e −6 dBFS falando normal (calibrar 1x, marcar
  o knob com fita). Sala não precisa de tratamento com dinâmicos, mas desligue
  AC barulhento se puder.
- Computador da gravação com tomada (sessões de 1h+) e disco livre: 48kHz/24-bit
  ×3 canais ≈ **1,5 GB/h** — um mês de reuniões ≈ 30-60 GB (HD externo ou Drive).

## Sessões solo (dataset de voz dedicada)

O mesmo mic dinâmico serve (broadcast/podcast usam dinâmico justamente pra isso).
Se quiser upgrade futuro pra timbre máximo nas sessões solo: 1 condensador
(AT2020/AT2035, ~R$ 700-1.100) numa sala tratada (closet com roupas).

## Ordem de compra mínima (se for escalonar)

1. 1 mic + interface → desbloqueia G0/G1 (sessões solo do Pedro) **já**.
2. +2 mics + acessórios → desbloqueia o flywheel de reuniões.
