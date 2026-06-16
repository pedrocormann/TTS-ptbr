# Contrato de feedback — o substrato pros agentes do futuro

**Por que isto existe.** WER mede se as *palavras* saíram certas, mas não pega o que mais importa na voz: fonema de gringo, entonação robótica, chiado, corte. A ideia (Pedro, jun/2026) é **acumular feedback humano estruturado e localizado no tempo** para que, no futuro, um **loop de agentes** consiga: pegar "fonema errado em t=2.30s do clipe X", **recortar aquele trecho**, identificar o fonema, e **corrigir no próximo treino** (mais dado daquele fonema, ajuste de base, regra de pronúncia, etc.).

> Não construímos os agentes agora. Construímos o **terreno**: a captura certa, num formato que o agente consiga consumir. Este doc é o contrato desse formato.

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
  "ratings": {                     // julgamento humano por dimensão (1-5 / bool)
    "geral": 4, "nativo": 2, "natural": 3,
    "voz": 4, "parou": true, "carioca": "sim", "nota": "texto livre"
  },
  "problems": ["sotaque gringo", "fonema errado"],   // tags no nível do clipe
  "markers": [                     // ⭐ o sinal localizado no tempo
    { "t": 2.30, "tag": "fonema errado", "note": "disse 'rato' com R de gringo" },
    { "t": 3.81, "tag": "chiado", "note": "" }
  ],
  "rated_ts": 1718560000000
}
```

### `markers[]` — o coração agent-ready
- `t` (float, segundos): instante do erro no áudio. Resolução de centésimo.
- `tag` (string): categoria do erro (taxonomia abaixo).
- `note` (string): descrição humana livre — pra fonema, idealmente **esperado → ouvido**.

### Taxonomia de `tag` (atual)
`fonema errado` · `sotaque gringo` · `entonação robótica` · `cortou/incompleto` · `ruído/chiado` · `emoção errada` · `repetiu` · `rápido/devagar` · `metálico/artefato` · `pausa estranha` · `ênfase errada`

## Como um agente futuro consome isto
1. Filtra `markers` por `tag` (ex.: todos os `fonema errado`).
2. Para cada um: abre `audio`, **recorta** `[t-0.3s, t+0.3s]` (janela de contexto), opcionalmente alinha com `ref_text` (forced alignment) pra achar o grafema/fonema.
3. Agrega: quais fonemas/contextos erram mais → vira **alvo de dado** (gravar/minerar mais daquele fonema) ou **regra** (lexicon/G2P).
4. Re-treina e **re-mede no mesmo benchmark** → fecha o loop.

## A pergunta aberta (Pedro): esse pool é o ideal ou falta sinal?

Provável que a gente **aprenda com a primeira leva de anotação** se falta algo. Candidatos a estender o schema, por ordem de provável valor:
- **`severity`** por marcador (leve/médio/grave) — prioriza o que dói mais.
- **região `[t_start, t_end]`** em vez de ponto — pra erros que duram (chiado, corte). Hoje é ponto + janela fixa.
- **`expected` / `heard`** estruturados pra fonema (ex.: `/ʁ/` → `/r/`), não só nota livre — alimenta G2P direto.
- **alinhamento ao `ref_text`** (índice do caractere/palavra no instante) — liga o tempo ao texto sem forced-alignment posterior.
- **concordância entre avaliadores** (multi-rater) — saber se um erro é consenso ou gosto de 1 pessoa.
- **exemplos positivos** ("aqui ficou ótimo") — não só erros; ancora o que preservar.
- **confiança do avaliador** no marcador.

Decisão: começamos **enxuto** (`{t, tag, note}` + ratings + tags) pra não atrapalhar a anotação, e **medimos a cobertura** (Insights) pra decidir o que adicionar. Quando os agentes entrarem, este doc evolui pra `v2` com os campos que provarem necessários.

## Onde fica
- Captura: `tools/rate/rate_app.py` (aba Avaliar, waveform + marcadores).
- Store: `tools/rate/ratings.jsonl` (1 linha por clipe, reescrito por chave — não duplica).
- Export agent-ready: botão na aba Insights → `feedback.jsonl` (junta áudio+refs+ratings+markers via `/api/feedback`).
