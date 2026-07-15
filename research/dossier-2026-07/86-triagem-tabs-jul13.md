# Triagem de papers — lote 2 (7 abas do Chrome, 13/jul/2026)

> 7 abas que o Pedro abriu no browser. Lidas na íntegra (arXiv/ACL baixados; Springer/ProQuest via abstract +
> full-text open-access). PDFs em `research/papers/`. Avaliado por **arquitetura/add-on, não idioma**
> ([[feedback-arquitetura-nao-idioma]]). Cruza com o mapa vivo [dossiê 85](85-arquiteturas-addons.md).
> **Veredito:** 4 somam (emoção training-free, streaming, codec-disentangle, dados-completude), 1 MED (loss FM),
> 1 LOW (front-end de texto), 1 SKIP (lip-reading). Nenhum embarcável direto; método é livre.

## Tabela-resumo

| # | Paper | O que é | Tier | O que soma pra nós | Onde encaixa (dossiê 85) |
|---|---|---|---|---|---|
| 1 | **TED-TTS** — Training-Free Intra-Utterance Emotion & Duration Control (ACL 2026, long 1077, NUS) | Controle de emoção+duração **DENTRO do enunciado**, **sem treinar**: causal masking + monotonic stream alignment pra isolar condicionamento por segmento + EOS logit steering pra duração. Dataset MED-TTS 30k + Qwen3-8B pra prompt. | **MED-HIGH** | É a **instância concreta** do "steering training-free" que estava só WATCH no 85 — e sobre **AR semantic LM** (porta melhor pro CSM que os flow). Emoção **intra-enunciado** (muda no meio da frase) sem retreinar. → novo arm `emo_ted_steering`. | train-control-emotion (steering) — sobe de WATCH p/ **TEST** |
| 2 | **S5-TTS** — Streaming T5-TTS with Limited Lookahead (arXiv 2606.21882, NVIDIA) | TTS **incremental palavra-a-palavra**: lookahead-causal masks + monotonic alignment + interleaved distillation. Começa a falar após as 1ªs palavras; **k=2 lookahead recupera 88–94%** do full-context; integra com Llama 3.3 (começa na 3ª palavra). | **MED** | Referência de método pros ADOPTs de deploy do 85 (stream LLM→TTS, chunk). CSM já streama; o valor é o **padrão lookahead-limitado + distillation pra naturalidade sob lookahead** + a prova de que **k=2 basta**. | deploy-latency (streaming) — referência |
| 3 | **SDP-Codec** — Speaker-Decoupled + Pitch Injection (arXiv 2606.21157, KAIST) | Codec single-codebook 0.45 kbps que **desacopla locutor (global) de conteúdo+prosódia (local)** e **injeta F0 normalizado**; zero-shot VC; single-stage; menor speaker-leakage. **Código aberto** (github.com/hanshounsu/sdpcodec-open). | **MED** | (a) codec — WATCH (mantemos Mimi fundido no CSM); (b) o método **desacoplar locutor + injetar pitch** é referência pro **disentangle timbre×sotaque** (gap #1) e pro **VC como reforço de identidade pós-TTS** (kNN-VC-like, já no 85). | arch-codecs (WATCH) + data-addons (VC) |
| 4 | **Penang Hokkien** — Phonetic Completeness Over Prosodic Diversity (IJACSA 2026, Lai et al.) | 1º TTS de Penang Hokkien (tonal, ameaçado): **45 min real + 2 h concatenativo syllable-level → ~2.000 combos sílaba-tom → MOS 3.92**; cross-fade 600 ms. **Tese: priorizar COMPLETUDE FONÉTICA no corpus sintético base; prosódia vem do fine-tune em fala real.** | **MED** | Princípio direto pra dados + gap #1: **garantir cobertura fonética completa (todos os fones/contextos cariocas) barato via síntese**, deixando a prosódia pro dado real dirigido. Ecoa nosso kit (49 fones) e o `data_synth_dpo`. → arm `data_phonetic_complete`. | data-addons (synth) |
| 5 | **SR-FD** — Fréchet Distance Loss on Speech Reps (arXiv 2607.06027, NTU+Amazon) | **Loss distribucional de treino** (Fréchet de features Whisper+CTC vs referência) pra TTS **few-step flow-matching** (VoxCPM2). WER 2.23→**1.41%** few-step, sem discriminador/custo de inferência. Achado: **raw FD é seletor de checkpoint FRACO** (Spearman 0.38, p=0.14) — WER externo ainda necessário. | **MED** | (a) loss só relevante **se adotarmos o `decode_fm_chunk`** (FM decoder) — aí regulariza o few-step; (b) **nuance de eval**: reforça o guardrail "métrica distribucional única é seletor fraco" — complementa TTSDS2 (que agrega vários fatores), não substitui win-rate/WER. | arch-flow-nonar (FM) + eval-metrics |
| 6 | **pt-BR Grammar Correction Synthetic Dataset** (Springer AIED 2026, Cabral et al., IF-PE/UFAL) | Dataset sintético de correção gramatical/ortográfica **pt-BR** + avaliação de LLMs offline (Bode/LLaMA/Gemma/Mistral). Achado: **maior detecção ≠ melhor** (overcorrection/viés). | **LOW** | Não é fala. Marginal: (a) referência pro **front-end de texto** ("reparo P&C com LLM + guardrail" já em TRANSCRICAO-PROSODICA §5.3) — o achado "overcorrection" é alerta pro nosso reparo com LLM; (b) grupo BR (contato). | front-end de texto (arquivo) |
| 7 | **VSRo-200** — Romanian Visual Speech Recognition (arXiv 2607.08112, U Bucharest) | Dataset de **leitura labial** (lip-reading) romeno, 200 h; pseudo-label vs humano; AVSR robustez a ruído. | **SKIP** | Modalidade e tarefa diferentes (visual speech recognition, não TTS/conversação). Eco genérico só: "pseudo-label escala; humano melhor a escala fixa" — já temos de outras fontes. | — |

## Ações no plano / código
- **`emo_ted_steering`** (novo arm em `runpod/experiments.py`): controle de emoção+duração **training-free intra-enunciado** (TED-TTS) — depois do `emo_dualref` ($0), antes de treinar. Testa se o mecanismo (causal mask + EOS logit steering) porta pro AR do CSM.
- **`data_phonetic_complete`** (novo arm): augmentation que maximiza **completude fonética carioca** (todos os fones/contextos) via síntese/concatenação, prosódia do dado real. Casa com `data_synth_dpo` (par com DPO anti-erosão).
- **Nuance de eval** (reforço, não novo): SR-FD confirma que **métrica distribucional única (FD/FID-like) é seletor fraco** — mantém win-rate/CMOS + TTSDS2 (multi-fator) + WER, nunca um FD escalar.
- **Referência de deploy:** S5-TTS entra como método do "stream LLM→TTS + lookahead limitado (k=2)" no `src/duplex`.
- **Referência de disentangle/VC:** SDP-Codec (speaker-decouple + pitch-inject, código aberto) pro braço de sotaque/VC.

## Licença (gate)
Métodos livres. Artefatos: TED-TTS (MED-TTS dataset TBD; base Qwen3 Apache), S5-TTS (NVIDIA; código?), SDP-Codec
(código aberto, NRF Korea — checar licença do repo antes de embarcar), SR-FD (método), Penang (IJACSA open-access),
Springer/pt-BR (fechado). Nenhum pt-BR plug-and-play; valor = método/insight.
