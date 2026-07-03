# Flywheel de dados: gravar → processar → curar → exportar → treinar

O ciclo completo, um comando por etapa:

## 1. Gravar
Sessão de conversa, 1 faixa wav por pessoa (pedro/joão/guilherme).

## 2. Processar (Whisper → frases → Supabase)
```bash
python3 tools/recording/process_recording.py --user pedro --meeting "papo-23jun" --audio faixa_pedro.wav
```
Transcreve, quebra em frases de ~3-12s, sobe os wavs pro bucket `tts-curate` e insere em `curar_itens`.

## 3. Curar (cockpit)
Cockpit → aba **Curar** → escolhe o nome → corrige texto, marca keep/flags/emoções/estilo.
Tudo salva direto na tabela `curar_itens`.

## 4. Exportar (este diretório) — o elo que fecha o ciclo
```bash
python3 tools/data/export_flywheel.py                    # supabase (default) — coleta nova
python3 tools/data/export_flywheel.py --source local     # dataset legado do Pedro (elevenlabs2024 + curate_edits)
python3 tools/data/export_flywheel.py --dry              # só o placar, sem escrever
```
Sai por locutor, no formato que o harness espera:
```
data/flywheel/<usuario>/segments/*.wav    # 24kHz mono PCM_16
data/flywheel/<usuario>/train.jsonl       # {"audio","text"} + extras (estilo_nl/emocoes/session_id/fonte)
data/flywheel/<usuario>/rejects.jsonl     # descartes + reprovados nos gates, com motivo
```
Gates (espelham o filter do train_voice): keep=true, sem flags de descarte
(`2 vozes`/`sobreposição`/`corte ruim`), 1-12s, texto ≥2 palavras, WAV legível.
O RESUMO impresso (clipes/minutos por pessoa + TOTAL) é o **placar da fase de coleta**.

Config supabase: env `SUPABASE_URL`/`SUPABASE_KEY` (defaults = os do `process_recording.py`).

## 5. Treinar (RunPod)
```bash
rsync -av data/flywheel/pedro/ root@POD:/workspace/pedro_data/
python3 runpod/train_voice.py --data-dir /workspace/pedro_data --data-file train.jsonl
```
(o train_voice ignora os campos extras do jsonl.)

## Transcrição prosódica (02/jul — default)

O `process_recording.py` agora pontua por PROSÓDIA (pausas+F0 do áudio, não gramática) e
segmenta por unidade entoacional — abordagem Aluísio/NILC, evidência BRACIS 2025
(WER 0,43 vs 0,50 treinando em segmento prosódico). Doc: docs/TRANSCRICAO-PROSODICA.md

- Coleta nova: automático (flag `--no-prosodic` volta ao antigo).
- Clipes antigos: `python3 tools/curate/repunct_prosodic.py` (2ª passada; mantém palavras
  curadas, re-deriva pontuação do áudio) → relatório em eval/prosodic_punct_report.md
  → `--report-only --emit-dataset` gera train_pros.jsonl pro arm A/B `r3_pedro_pros`.
- Export: gate Emilia (outlier duração/char) avisa por default; `--strict-emilia` reprova
  (usar só em dado não-curado).
