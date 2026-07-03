# Transcrição prosódica — pesquisa + implementação (02/jul/2026)

> **→ Compilado em [ROADMAP.md](ROADMAP.md) (o roadmap único).** Este doc segue vivo como deep-dive.

> A abordagem da **Sandra Aluísio (NILC/ICMC-USP)** de ajustar transcrições por prosódia,
> implementada no nosso pipeline e cruzada com benchmarks globais. Tudo verificado em fonte
> primária: dossiês `research/dossier-2026-07/82` (Aluísio), `21` (global), `80` (pesquisadores BR).

## A tese (e a evidência)

Fala espontânea deve ser segmentada e pontuada por **UNIDADES ENTOACIONAIS** (fronteiras
prosódicas reais do áudio), não por gramática. O Whisper pontua gramaticalmente — vírgula sem
pausa, ponto sem contorno fechado — e o TTS aprende a melodia errada.

Evidência quantitativa (verificada):
- **BRACIS 2025** (arXiv:2511.14779, grupo Aluísio): TTS treinado nos segmentos **prosódicos** do
  ENTOA vs segmentação automática (WhisperX): **WER 0,43 vs 0,50 (p<0,01) · F0-RMSE ~39,1 vs ~44,1 Hz**.
- **Speech Prosody 2026** (FastSpeech2, 3 condições de segmentação): segmentação automática não
  captura pausas/variações de F0; **70% dos contornos nucleares sintetizados divergem** do natural.
- **DisfluencySpeech** (arXiv:2406.08820): transcrição "limpa demais" sobre áudio espontâneo
  **não converge** (CER 60%) vs verbatim (CER 15%) — o texto TEM que cobrir o que soa.
- **Vietnamita** (arXiv:2004.09607/VLSP): pontuar onde o áudio pausa (>0,3s) melhora MOS.
- **Balalaika** (Interspeech 2026, russo): pontuação restaurada + marca de stress = ganhos
  complementares de MOS.

Regras-chave do grupo (PROPOR 2024 + IberSPEECH 2022, verificadas):
- **Silêncio ≥300ms é O sinal** — "heurísticas de silêncio sozinhas ≈ todas as outras (Δ0-3%)".
- **"Pausa sempre indica quebra; nem toda quebra tem pausa"** (regra de ouro) — o teto das
  heurísticas é limitado (macro-F1 31% no ProsSegue heurístico); o caminho de ponta é
  **PSST** (CoNLL 2023): Whisper fine-tunado emite a fronteira de IU como token (F1 0,87).
- Fáticos/fillers **sempre escritos** (lista NURC: hum, uhum, éh, ah, ahn, hein…);
  concordância humana κ 0,67-0,88 (ou seja: nem humanos concordam 100% — heurística razoável basta).

## O que implementamos (hoje)

1. **[tools/text/prosodic_punct.py](../tools/text/prosodic_punct.py)** — re-pontuador prosódico:
   palavras com timestamp (faster-whisper) + F0 (parselmouth) → vírgula só onde há pausa real
   (≥0,15s), ponto onde o contorno fechou (pausa ≥0,6s, ou ≥0,32s com F0 no piso do falante /
   reset), "?" só com subida final + pista lexical interrogativa (senão é continuação → "…"),
   hesitação = filler/alongamento + pausa → "…", fillers preservados. Segmentação por IU
   (`iu_segments`): corta APENAS em fronteira terminal — igual ao config `prosodic` do ENTOA.
2. **[tools/recording/process_recording.py](../tools/recording/process_recording.py)** — modo
   `--prosodic` é o **default** do pipeline de coleta (as gravações novas dos 3 já entram certas).
   `--no-prosodic` volta ao antigo.
3. **[tools/curate/repunct_prosodic.py](../tools/curate/repunct_prosodic.py)** — 2ª passada nos
   259 clipes já curados: mantém as PALAVRAS curadas (verdade humana), alinha timestamps por
   difflib e re-deriva só a PONTUAÇÃO do áudio. Relatório antes/depois em
   `eval/prosodic_punct_report.md` + `--emit-dataset` gera `train_pros.jsonl` pro A/B.
4. **Arm A/B na rodada 3**: treinar `train.jsonl` (pontuação atual) vs `train_pros.jsonl`
   (prosódica) com a mesma receita — mede no NOSSO modelo o ganho que o BRACIS mediu no deles.

Resultado da calibração nos primeiros clipes reais: vírgulas 10,5→2,5/100 palavras (só onde há
pausa), hesitações e continuações marcadas, zero falso-"?" após o aperto lexical.

## O que adotar em seguida (do benchmark global, por custo/benefício)

1. **Filtro Emilia** no export: descartar outlier de duração-por-caractere + DNSMOS<3 (barato, evita o pior).
2. **Verbatim-first**: o Whisper large-v3 APAGA fillers sistematicamente (WhisperD provou) — pra
   coleta nova, avaliar 2ª passada com **CrisperWhisper** (CC-BY-NC, ok pesquisa) que é SOTA em
   fillers + timestamps precisos.
3. **Reparo P&C com LLM + guardrail** (receita Granary): LLM corrige caixa/pontuação, reverte se
   desviar >5% CER — melhor que restauradores gramaticais (kredor/dominguesm) pra fala espontânea.
4. **Tags de evento inline** (`[risada]`, `[respira]`) padrão CosyVoice/Dia quando houver eventos.
5. **Teto (colaboração USP)**: PSST-pt — fine-tunar Whisper pra emitir fronteira de IU em pt-BR.
   É a proposta de co-autoria perfeita: eles têm método+anotação, nós temos dado carioca+produto.

## Bônus da pesquisa BR (mudam outras frentes)

- **TAGARELA tem rótulo de DIALETO** → dá pra minerar subset **carioca** (pesquisa) e pedir ao
  Frederico o classificador de sotaque — ataca a falha nº1 (95% "não soa carioca") por um flanco
  novo. Gancho de e-mail: trocamos eval carioca do rate_app + voz-semente como test set.
- **BIPA (PROPOR 2026)**: G2P dialetal com **dialeto-Rio** — se algum dia reabrirmos fonema, é por aí.
- **Arnaldo Candido Jr (UNESP, 2026)**: playbook publicado de **fine-tuning emocional pt-BR com
  poucos dados** (YourTTS) — replicável na nossa esteira por ~$5 de GPU; candidato a arm da F3.
- Correção de registro: TAGARELA = 8.972h ASR total; 2.800h = subset clean p/ TTS (CC-BY-NC-SA).
- **ENTOA_TTS**: conflito de licença real (HF card=MIT vs paper=CC-BY-NC-ND) — registrado no
  registry como pesquisa até esclarecerem; e os campos dele incluem `normalized_text` (par
  texto cru/normalizado — útil de espelhar no nosso manifest).
