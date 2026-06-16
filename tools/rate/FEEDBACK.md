# Contrato de feedback — o substrato pros agentes do futuro

**Por que isto existe.** WER mede se as *palavras* saíram certas, mas não pega o que mais importa na voz: fonema de gringo, entonação robótica, chiado, corte. A ideia (Pedro, jun/2026) é **acumular feedback humano estruturado e localizado no tempo** para que, no futuro, um **loop de agentes** consiga: pegar "fonema errado em t=2.30s do clipe X", **recortar aquele trecho**, identificar o fonema, e **corrigir no próximo treino** (mais dado daquele fonema, ajuste de base, regra de pronúncia, etc.).

> Não construímos os agentes agora. Construímos o **terreno**: a captura certa, num formato que o agente consiga consumir. Este doc é o contrato desse formato.

**Dois tipos de erro pontual — e o loop resolve os dois:**
1. **Objetivo (WER)** — qual *palavra* saiu errada (troca/omissão/inserção), extraído automaticamente do alinhamento `ref ↔ asr_hyp` → campo `wer_ops`. O WER deixa de ser só um número e vira uma lista de erros acionáveis.
2. **Perceptual (humano)** — fonema de gringo, chiado, entonação, no tempo → campo `markers`. É o que o WER **não** pega (uma palavra pode ser reconhecida certa e ainda soar estrangeira).

Um erro pode aparecer nos dois (a palavra errada está naquele segundo) ou só num. O agente futuro cruza os dois sinais.

## Como se captura (hoje, no rate_app)

Na aba **Avaliar**, além das notas (geral, nativo-vs-gringo, naturalidade, parou, voz, sotaque) e das tags de problema por clipe, há uma **waveform clicável**:
1. clica na onda no instante do erro → fixa o segundo;
2. escolhe o **tipo** (fonema errado, chiado, cortou, pausa estranha, ênfase errada…);
3. escreve **o que ouviu** (ex.: "disse 'rato' com R de gringo");
4. **marcar momento** → vira um marcador `{t, tag, note}` salvo no clipe.

A aba **Insights** mostra a **cobertura** (quantos clipes/instantes marcados, por tipo) e exporta tudo como **`feedback.jsonl`** (agent-ready).

## Schema — `feedback.jsonl` (1 registro por clipe) — v1

```jsonc
{
  "run": "stage_b_final",          // modelo/run que gerou o áudio
  "id": "neu-01",                  // id da frase do benchmark
  "audio": "runpod_samples/stage_b_final/gen/neu-01.wav",  // caminho relativo ao repo
  "ref_text": "Olá, tudo bem com você?",   // texto-alvo (o que devia falar)
  "asr_hyp": "ola tudo bem",       // o que o ASR ouviu (round-trip do WER)
  "emotion": "neu", "accent": "carioca",
  "wer": 0.17, "dur_s": 4.5,       // métricas objetivas já existentes
  "wer_ops": [                     // ⭐ o WER decomposto: erro pontual de PALAVRA (objetivo)
    { "op": "ok",  "ref": "olá",  "hyp": "olá" },
    { "op": "sub", "ref": "você", "hyp": "vc" },   // troca
    { "op": "del", "ref": "bem",  "hyp": null },    // o modelo omitiu
    { "op": "ins", "ref": null,   "hyp": "aí" }     // o modelo falou a mais
  ],
  "ratings": {                     // julgamento humano por dimensão (1-5 / bool)
    "geral": 4, "nativo": 2, "natural": 3,
    "voz": 4, "parou": true, "carioca": "sim", "nota": "texto livre"
  },
  "problems": ["sotaque gringo", "fonema errado"],   // tags no nível do clipe
  "markers": [                     // ⭐ o sinal perceptual localizado no tempo
    { "t": 2.30, "tag": "R forte /ʁ/ virou fraco", "sev": "grave", "note": "rato → R de gringo" },
    { "t": 3.81, "tag": "ruído/chiado", "sev": "leve", "note": "" }
  ],
  "rated_ts": 1718560000000,
  "schema_version": 1              // versionado: os agentes futuros sabem ler/migrar
}
```

### `markers[]` — o coração agent-ready
- `t` (float, segundos): instante do erro no áudio. Resolução de centésimo.
- `tag` (string): categoria do erro (taxonomia abaixo).
- `sev` (string): gravidade — `leve` | `medio` | `grave`. Prioriza o que o agente ataca primeiro.
- `note` (string): descrição humana livre — pra fonema, idealmente **esperado → ouvido**.

### Taxonomia de `tag`
**Geral:** `sotaque gringo` · `fonema errado` · `entonação robótica` · `cortou/incompleto` · `ruído/chiado` · `emoção errada` · `repetiu` · `rápido/devagar` · `metálico/artefato` · `pausa estranha` · `ênfase errada`

**Fonema pt-BR (onde o "gringo" erra)** — categorias acionáveis que o WER nunca pega:
`R forte /ʁ/ virou fraco` · `vogal nasal sem nasalizar (ã/õ/em)` · `ti/di sem palatal (tchi/dji)` · `S coda sem chiado carioca` · `L coda virou /l/ (não /w/)` · `vogal aberta/fechada (ó/ô, é/ê)` · `lh/nh sem palatal` · `ão/ditongo nasal errado` · `sílaba tônica errada` · `ritmo silábico de gringo`

> Essas categorias mapeiam direto pros alvos de correção: cada uma vira "minerar/gravar mais dado deste fonema" ou "regra de G2P/lexicon".

## Como um agente futuro consome isto
1. Filtra `markers` por `tag` (ex.: todos os `fonema errado`).
2. Para cada um: abre `audio`, **recorta** `[t-0.3s, t+0.3s]` (janela de contexto), opcionalmente alinha com `ref_text` (forced alignment) pra achar o grafema/fonema.
3. Agrega: quais fonemas/contextos erram mais → vira **alvo de dado** (gravar/minerar mais daquele fonema) ou **regra** (lexicon/G2P).
4. Re-treina e **re-mede no mesmo benchmark** → fecha o loop.

## A pergunta aberta (Pedro): esse pool é o ideal ou falta sinal?

**Já aplicado (v1):** `severity` por marcador · taxonomia **pt-BR-aware** de fonema · `wer_ops` (WER decomposto) · `schema_version`.

**Candidatos a v2** — decidir **depois da 1ª leva real de anotação** (medindo a cobertura no Insights), pra não inflar o schema cedo demais:
- **região `[t_start, t_end]`** em vez de ponto — pra erros que duram (chiado, corte). Hoje é ponto + janela fixa de ±0.3s.
- **`expected` / `heard`** totalmente estruturados (IPA) pra fonema — hoje aproximado pela tag pt-BR + nota livre.
- **alinhamento do marcador ao `ref_text`** (índice da palavra/caractere no instante) — liga tempo↔texto sem forced-alignment posterior.
- **concordância entre avaliadores** (multi-rater) — saber se um erro é consenso ou gosto de 1 pessoa (hoje só o Pedro avalia → viés a vigiar).
- **exemplos positivos** ("aqui ficou ótimo") — ancora o que preservar, não só o que consertar.
- **mais frases/áudios** — 14 frases × poucos runs dá sinal direcional, não estatístico; ampliar o benchmark quando o foco virar ranking fino.

Princípio: **enxuto e versionado**. Mede a cobertura → adiciona só o que a anotação real provar necessário → bumpa `schema_version`.

## Onde fica
- Captura: `tools/rate/rate_app.py` (aba Avaliar, waveform + marcadores).
- Store: `tools/rate/ratings.jsonl` (1 linha por clipe, reescrito por chave — não duplica).
- Export agent-ready: botão na aba Insights → `feedback.jsonl` (junta áudio+refs+ratings+markers via `/api/feedback`).
