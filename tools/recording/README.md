# Kit de gravação — dataset da voz do Pedro

Pipeline local (Mac, CPU) para gravar, controlar qualidade e exportar o dataset
de treino. O treino em si roda no Colab (`notebooks/`).

## Setup (uma vez)

```bash
cd ~/Downloads/TTS-ptbr
python3 -m venv .venv-rec && source .venv-rec/bin/activate
pip install -r tools/recording/requirements.txt
python tools/recording/record.py --list-devices   # ache o índice do seu mic
```

## Protocolo de estúdio (resumo)

- **Sala:** a mais silenciosa possível (sem AC/ventilador/geladeira audível);
  cobertores/cortinas reduzem reverb. Grave sempre na MESMA sala/posição.
- **Mic:** condensador cardioide a ~15–20 cm, pop filter, levemente fora do eixo.
- **Ganho:** fala normal picando entre −12 e −6 dBFS (o gravador avisa).
- **Formato:** 48 kHz / 24-bit / mono (o kit já força isso).
- **Take:** ~0,5 s de silêncio antes e depois da fala. Errou? `r` regrava na hora.
- **Sessões:** ≤ 60 min por bloco; água; não gravar gripado/rouco (consistência
  de timbre importa mais que volume de horas).

## Fluxo

```bash
# 1. monte um plano de sessão (mix = core + emoção + sotaque + conversa)
python tools/recording/build_session.py --kind mix --minutes 45 --out tools/recording/sessions/ses01.jsonl

# 2. grave (retomável; QC automático por take)
python tools/recording/record.py --plan tools/recording/sessions/ses01.jsonl --session ses01

# 3. relatório de QC (minutos por estilo/sotaque, itens pra regravar)
python tools/recording/qc_report.py --session ses01

# 4. segmente os takes longos (monólogo/diálogo) — transcrição roda no Colab
python tools/recording/segment_long.py --session ses01

# 5. exporte o dataset-mestre (+ formatos por modelo)
python tools/recording/export_dataset.py --sessions ses01 --sr 24000 --format canonical csm orpheus
```

## Quanto gravar (alvos por fase)

| Fase | Conteúdo | Alvo |
|---|---|---|
| F1 — clone/base | `--kind core` (frases neutras balanceadas) | 1–3 h |
| F2 — emoções | `--kind emotion` (8 estilos × 3 intensidades) | 2–4 h |
| F3 — sotaques | `--kind accent` (5 sub-variações cariocas) | 1–2 h por variação |
| F4 — conversa | `--kind conversa` (monólogos/diálogos/paralinguístico) | 2–4 h |

Cobertura fonética do banco core: `python tools/recording/build_session.py --coverage`.

## Estrutura de saída

```
data/raw/<sessao>/            takes aceitos (48k/24-bit) + metadata.jsonl
data/raw/<sessao>/segments/   utterances dos takes longos + to_transcribe.jsonl
data/dataset_v1/              dataset-mestre exportado (train/val + formatos por modelo)
```

`data/` é gitignored — áudio cru e dataset são o "ouro" privado (ver tech-stack).
