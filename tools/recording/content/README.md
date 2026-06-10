# Conteúdo do kit de gravação — TTS-ptbr

Material autoral (escrito para este projeto, sem cópia de corpora) para gravação do dataset de voz do Pedro: cobertura fonética do português carioca, emoções controláveis, sub-variações de sotaque e fala espontânea. Todos os arquivos são JSONL (um objeto JSON válido por linha, UTF-8).

## Arquivos

### `sentences_core.jsonl` — 260 frases
Frases de leitura com cobertura fonética completa do PT-BR/carioca. Campos: `id`, `text`, `focus` (fonemas/contextos alvo), `len`.

- Comprimentos: 97 curtas (37%), 111 médias (43%), 52 longas (20%)
- Modalidades: 37 interrogativas (14%), 25 exclamativas (10%), 18 imperativas (7%)
- 23 frases (9%) com números, datas, horas e valores em reais por extenso
- Cobertura marcada em `focus`: vogais nasais (ã, ẽ, ĩ, õ, ũ), ditongos orais e nasais (ão, õe, ãe, ai, ei, oi, au, eu, ou, ui, iu, éu), chiado carioca em coda (/ʃ/ /ʒ/), palatalização tʃ/dʒ, r inicial /ʁ/ e rr, r em coda, l vocalizado, encontros consonantais (pr, br, tr, cr, gr, fl, pl, bl, pn, ps, tm, dv, fr), hiatos, proparoxítonas, sândi em fronteira de palavra, siglas e estrangeirismos, mais temas do cotidiano carioca (praia, trânsito, comida, trabalho, tecnologia, arte, família, clima, futebol, música)

### `emotion_cards.jsonl` — 8 cartões de emoção (96 frases)
Um cartão por estilo: `neutro`, `caloroso`, `animado`, `empatico`, `triste`, `surpreso`, `irritado`, `sussurro`. Campos: `style`, `direction` (instrução de ator: situação imaginada, energia, ritmo), `sentences` (12 frases específicas da emoção), `intensities` (`suave`/`media`/`forte` — gravar cada frase nas três intensidades).

### `accent_cards.jsonl` — 5 cartões de sotaque (50 frases)
Sub-variações cariocas: `carioca-medio`, `carioca-zona-sul`, `carioca-cria`, `carioca-surfista`, `carioca-interior`. Campos: `accent`, `direction` (autenticidade > caricatura: falar como o Pedro falaria naquele contexto social), `markers` (traços fonéticos/lexicais), `sentences` (10 frases adequadas ao registro), `gírias` (12–15 itens lexicais por variação).

### `conversational_prompts.jsonl` — 60 itens
Material conversacional/espontâneo, três tipos no campo `kind`:

- `monologo` (20): prompts de improviso de 60–90s com `topic` e `direction` — temas que rendem emoção genuína (perrengue de obra, melhor show, praia lotada, Linha Vermelha, comida de boteco...)
- `dialogo` (15): mini-diálogos de 8–14 turnos (154 turnos no total) para dupla ou self-dialogue, com backchannels escritos (uhum, é..., caraca, sério?), interrupções marcadas com `—` e risadas marcadas como `[risada]`
- `paralinguistico` (25): itens não-verbais com direção de gravação (risadas, suspiros, hum pensativo, uhum, tsc, respiração, hesitações, eita, ufa, bocejo, pigarro...)

## Validação

Cada arquivo foi validado linha a linha com `python3` + `json.loads`. Para revalidar:

```bash
python3 -c "import json,sys; [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]" tools/recording/content/sentences_core.jsonl
```

## Resumo de contagens

| Arquivo | Linhas | Conteúdo |
|---|---|---|
| `sentences_core.jsonl` | 260 | frases de leitura com foco fonético |
| `emotion_cards.jsonl` | 8 | 8 estilos × 12 frases × 3 intensidades |
| `accent_cards.jsonl` | 5 | 5 variações × 10 frases + gírias |
| `conversational_prompts.jsonl` | 60 | 20 monólogos + 15 diálogos + 25 paralinguísticos |
