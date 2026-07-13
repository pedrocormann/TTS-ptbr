# SAMPA — o "PSST-pt" que a gente esperava, publicado (arXiv 2607.07408, jul/2026)

> **Lido na íntegra do PDF (`research/papers/2607.07408v1.pdf`, 8 pp., submetido ao IEEE, 8/jul/2026).**
> Complementa [82-aluisio-transcricao-prosodica-verificado.md](82-aluisio-transcricao-prosodica-verificado.md)
> e [../../docs/TRANSCRICAO-PROSODICA.md](../../docs/TRANSCRICAO-PROSODICA.md). Este é o artefato que
> materializa o "teto = PSST" / "PSST-pt como colaboração USP" que estava aberto no roadmap.

## O que é (uma frase)

**SAMPA** (*Segmenter for Automatic Marking of Prosodic boundAries in Brazilian Portuguese*) é um
**Whisper large-v3 fine-tunado que transcreve fala espontânea pt-BR e, no meio da transcrição, insere
um marcador de fronteira prosódica TERMINAL** (fim de unidade entoacional). É a adaptação para o
português do **PSST!** (Roll et al., CoNLL 2023) — exatamente o método que o dossiê 82 e o
`prosodic_punct.py` apontam como o **estado da arte / a melhoria v2** da nossa segmentação heurística.

- **Autores:** Rodrigo de Freitas Lima (ICMC-USP), **Julio Cesar Galdino (ICMC-USP)**, Marcos Vinicius Treviso (IST-Lisboa).
- **Por que isso importa em uma linha:** o grupo que a gente já mapeou como parceiro ideal (Aluísio/NILC)
  **publicou a ferramenta que a gente ia propor construir junto** — e o 2º autor, **Galdino, é justamente
  o contato técnico natural** que o dossiê 82 identificou (1º autor do BRACIS 2025, do Speech Prosody 2026
  e da review JBCS). O 1º autor, **Rodrigo Lima**, também já aparecia na órbita do grupo (EyetrackingMOS / Certas Palavras).

## Como funciona (a sacada, explicada do zero)

O problema: **segmentação prosódica** = achar onde uma fala se divide em **unidades entoacionais** (IUs) —
os "pedaços" naturais em que a gente organiza o discurso, delimitados por pausa + movimento de F0 (pitch)
+ alongamento final. Detectar isso tradicionalmente pede regras acústicas à mão (é o que o `ProsSegue`
heurístico faz, e o nosso `prosodic_punct.py`).

A sacada do SAMPA (herdada do PSST): **tratar segmentação prosódica como uma extensão da transcrição.**
Em vez de treinar um classificador acústico separado, você ensina o próprio ASR a **cuspir um token
delimitador** (`"!!!!!"` no paper) entre as palavras, exatamente onde há uma fronteira terminal. Ex.:

> `primeira unidade !!!!! segunda unidade`

Detalhes concretos:
- **Zero mudança de arquitetura.** O delimitador `"!!!!!"` é só mais um token no vocabulário do decoder do
  Whisper. O modelo aprende a emiti-lo como qualquer palavra.
- Por que funciona: o Whisper usa o **áudio** (encoder) + o **contexto linguístico** (decoder) para decidir
  onde cai a fronteira — ou seja, ele combina pista acústica (pausa/F0) com pista morfossintática/semântica.
  A análise de n-gramas do paper confirma: o modelo marca fronteira depois de marcadores de discurso
  (*né, não, é*) e substantivos (*cinema, filme, casa*), e conectivos (*e, mas, porque*) aparecem logo
  **depois** da fronteira. Ele aprendeu a "gramática da prosódia", não só o silêncio.

Isso é o mesmo padrão da nossa ideia de **tags inline no transcript** (o CSM aprende `<risada>` etc.): um
token especial no texto que carrega informação que não é lexical. SAMPA faz isso para a fronteira de IU.

## Dados, treino e números (o que dá pra confiar)

- **Treino/val:** CORAA **NURC-SP Minimal Corpus** (o mesmo do ENTOA) + **CATNA-MT** (Corpus de Áudios e
  Transcrições Não-Alinhadas, do TaRSiLA), ambos **variedade paulista (SP)**, anotados manualmente por IU
  (framework C-ORAL-BRASIL). ~29h de treino, ~3h de teste held-out. Gravações originais em fita → parte
  descartada por ruído.
- **Pré-processamento:** concatenam segmentos consecutivos do mesmo falante enquanto a duração fica < **30s**
  (o teto de entrada do Whisper — acima disso ele trunca e perde fronteira no fim). 16 kHz.
- **Filtros de treino (ablação):** unfiltered · low-pass 3200 Hz · high-pass 400 Hz · high-pass 600 Hz · data-aug.
  4 épocas cada, LR warm-up ~7% depois linear até 1e-5.
- **Métrica:** classificação binária por posição ("tem fronteira terminal aqui, sim/não") → **binary F1**
  (na classe fronteira) + **macro F1** + **WER** (pra checar que ensinar segmentação não estraga a transcrição).
- **Resultados (o número honesto):**
  - **In-domain (NURC-SP test):** melhor = LP 3200 Hz, **WER 0,103 · binary F1 0,731 · macro F1 0,858**.
    Filtragem quase não muda (unfiltered ≈ o melhor filtrado, Δ~0,2%).
  - **Out-of-domain (MuPe-Diversidades, 2,5h, 17 estados, mais limpo):** **binary F1 0,796** (HP 600 Hz);
    HP 400/600 empatam no melhor macro F1 (**0,890**). Os modelos treinados com **high-pass generalizam
    melhor** pro dado mais limpo e diverso; LP e data-aug generalizam pior.
- **Análise acústica-visual (Praat):** os verdadeiros-positivos têm F0 caindo continuamente no fim da IU
  (padrão de declarativa em pt-BR) + reset de pitch + pausa longa. Os falsos-positivos aparecem onde há
  pistas fracas/ambíguas (pausa que não é terminal, F0 caindo de leve) — coerente com "pausa sempre indica
  quebra, mas nem toda quebra é terminal".
- **Release:** código + modelos + datasets processados prometidos no **HuggingFace Hub "upon acceptance"** (ainda não saiu).

## O que isso MUDA pra gente (as decisões)

### 1. "PSST-pt" deixou de ser hipótese — é um artefato (quase) na prateleira
No roadmap e no trilha_map, "fine-tunar Whisper pra emitir fronteira de IU em pt-BR" estava **aberto**, como
"teto" e "colaboração futura". **Agora existe e é o SAMPA.** O nosso `prosodic_punct.py` (heurístico:
pausa≥300ms + F0) continua sendo o stopgap defensável (o próprio dossiê 82 diz que a heurística de silêncio
empata com tudo); **SAMPA é a v2 neural** que substitui/reforça a detecção de fronteira **terminal** quando
os pesos saírem no HF. Plano: quando o release sair, rodar SAMPA no nosso áudio (coleta) e **comparar contra
o `prosodic_punct.py`** (concordância de fronteiras terminais) — é um A/B barato, sem GPU de treino.

### 2. A co-autoria USP ficou óbvia — e temos a moeda de troca perfeita
O ponto mais forte do paper **pra nós** é a fraqueza dele: **SAMPA é treinado só em SP** (NURC-SP + CATNA).
A avaliação out-of-domain (MuPe-Diversidades, 17 estados) mostra que **generaliza razoável, mas não foi
testado em carioca especificamente**. A nossa voz-semente carioca dirigida (com consentimento) é
**exatamente o test set de variedade que o dataset deles não tem** — o gancho de troca que já estava no
e-mail rascunhado, agora com um alvo concreto: "rodamos o SAMPA de vocês no nosso carioca e reportamos onde
ele erra fronteira por causa do sotaque". Atualizar `docs/RASCUNHOS-CONTATOS.md` (feito).

### 3. Não muda o TAMANHO do prêmio da prosódia (realismo, não otimismo)
SAMPA melhora a **ferramenta** que produz os segmentos prosódicos. Mas o ganho *downstream* no TTS continua
sendo a mesma aposta modesta e **ainda não provada em CSM**: o BRACIS 2025 mediu ~7 pontos de WER e ~5 Hz de
F0-RMSE, e **em FastSpeech2, não em modelo tipo CSM/LLM-áudio**. Ou seja: SAMPA **de-risca o passo de
segmentação** e **fortalece a parceria**, mas o nosso arm A/B (`train.jsonl` vs `train_pros.jsonl` na rodada 3)
continua sendo o teste que decide se prosódia move a agulha **no nosso modelo**. SAMPA não é bala de prata pro
"robótico" — é uma peça melhor do front-end.

### 4. Licença / proveniência (registrar, não bloquear)
- **Base (Whisper large-v3): MIT** — permissiva.
- **Dados de treino do SAMPA: NURC-SP MC (CC-BY-NC-ND) + CATNA** → mesmo caso do ENTOA (proveniência NC-ND).
  A licença **dos pesos do SAMPA** ainda é TBD (sai no HF "upon acceptance").
- Nosso uso pretendido é **como ferramenta de anotação** do nosso próprio áudio (marcar fronteira de IU),
  não injetar conteúdo NC no peso do produto — análogo a usar o Whisper (treinado em áudio da web) pra
  transcrever. Para MODO PESQUISA está liberado com rastreabilidade; registrar no `dataset_registry.yaml`
  como proveniência a esclarecer, igual ao ENTOA. Se um dia virar produto, confirmar a licença do release.

## Ações concretas (o delta)

1. **VIGIL-LOG:** logado como achado da varredura (grupo Aluísio, watchlist). ✔
2. **ROADMAP.md / TRANSCRICAO-PROSODICA.md / trilha_map.json:** "PSST-pt = teto/colaboração" → **"SAMPA (PSST-pt) publicado, Galdino coautor; nosso carioca ataca o gap SP-only deles"**. ✔
3. **RASCUNHOS-CONTATOS.md:** e-mail ao Galdino ganha o gancho SAMPA (parabéns + oferta de rodar em carioca). ✔
4. **Quando os pesos saírem no HF:** rodar SAMPA no nosso áudio de coleta; A/B de fronteiras terminais vs `prosodic_punct.py` (sem GPU); considerar SAMPA como o segmentador default se ganhar.
5. **Não mexe** na prioridade M0.5/M1: segue gravar 30min/dia + eval girando. Prosódia continua sendo o defeito #2, atacado pelo arm A/B da rodada 3.

## Fontes
- Paper: arXiv **2607.07408v1** ("Transformer-based segmentation of prosodic boundaries in Brazilian Portuguese"), Lima, Galdino, Treviso, jul/2026 (submetido IEEE).
- PSST original: Roll et al., "Psst! Prosodic Speech Segmentation with Transformers", CoNLL 2023 / arXiv **2302.01984** (F1 0,87 / 96% SBC) — já no dossiê 82.
- Datasets: CORAA NURC-SP Minimal Corpus (IberSPEECH 2022) · CATNA (TaRSiLA) · MuPe-Diversidades (Craveiro & Galdino, 2025).
- Contexto do grupo e a linha ENTOA/BRACIS/ProsSegue: [dossiê 82](82-aluisio-transcricao-prosodica-verificado.md).
