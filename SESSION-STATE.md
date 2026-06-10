# SESSION-STATE — 2026-06-10 (sessão "resgate + replan + kit")

> Doc de retomada. Próxima sessão: leia isto + `specs/REPLAN-2026-06-10.md` e siga de "Próximos passos".

## O que esta sessão fez (tudo commitado)

1. **Contexto resgatado** das conversas anteriores ("TTS pt-br 2" = transcript
   `~/.claude/projects/-Users-pedrocormann-Downloads-unflat-hand-vein/8c200f94-*.jsonl`,
   cobre 09-18/mai; não existe sessão separada "TTS pt-br" — o início está nesse
   mesmo arquivo). Destilado salvo na memória persistente do Claude
   (`~/.claude/projects/-Users-pedrocormann-Downloads-TTS-ptbr/memory/`).
2. **Dossiê jun/2026** (`research/dossier-2026-06/10..60-*.md`): 8 frentes
   pesquisadas na web com verificação. Leia o REPLAN para o resumo executivo.
3. **REPLAN completo**: `specs/REPLAN-2026-06-10.md` — duas trilhas (A voz /
   B spine), pool ranqueado, fases F0.5→F5 com gates, plano de gravação G0→G4,
   eval harness v2, riscos, checklist do Pedro.
4. **Kit de gravação completo** (`tools/recording/`): build_session (planos com
   cobertura fonética 49/49 fones), record.py (QC por take, tom de sala, SNR≥32),
   qc_report, segment_long, export_dataset (formatos canonical/csm/orpheus/
   ljspeech) + conteúdo autoral (260 frases core, 8 cartões de emoção com
   âncoras, 5 cartões de sotaque carioca, 60 prompts conversacionais).
5. **Eval**: `eval/speaker_sim.py` (WavLM-SV) adicionado.
6. **Notebook**: `notebooks/01_dataset_prep.ipynb` (transcrição + verificação WER
   + export no Colab).

## ATUALIZAÇÃO final da sessão (13:57)

- **Notebooks 02, 03 e 04 FEITOS** (APIs extraídas e verificadas na fonte pelos 3
  agentes; fatos críticos preservados em `research/dossier-2026-06/70-api-recipes.md`):
  02 = baselines zero-shot F0.5 (Chatterbox-pt-br from_local + Pocket-TTS pt 6L/24L
  + CSM in-context + eval comparativa); 03 = Qwen3-TTS-1.7B-Base LoRA patchado
  (L4/A100, NÃO T4); 04 = CSM-1B Unsloth LoRA (T4 ok).
- roadmap.md → aponta pro REPLAN; RUNBOOK e VIGIL-LOG atualizados.
- **Único item em voo**: a síntese automática do workflow de pesquisa
  (`00-SYNTHESIS.md`, runId `wf_ff245249-d44`). NÃO é bloqueante — eu li as 8
  frentes na íntegra e o REPLAN É a síntese. Se quiser retomá-la:
  `Workflow({scriptPath: "<session-dir>/workflows/scripts/tts-ptbr-research-refresh-wf_ff245249-d44.js", resumeFromRunId: "wf_ff245249-d44"})`.

## Próximos passos (na ordem)

1. **Pedro**: Colab Pro+ → gravar piloto G0 (README do kit) → rodar **notebook 02**
   → trazer números + impressão de ouvido (pt-BR vs pt-PT é decisivo) →
   **e-mail NILC** (licença NURC-TTS) → seguir gates do REPLAN §F0.5/F1.
2. **Claude (próxima sessão)**: (a) **deep-read da obra do Frederico Oliveira**
   (lista no VIGIL-LOG 2026-06-10 addendum; prioridade arXiv 2506.02088 SER) e
   **1ª rodada do OSINT-Sesame** (Trilha M do REPLAN: mapear autores do post CSM
   + ex-funcionários + diffs dos forks da org); (b) registrar resultado do gate
   F0.5 no VIGIL-LOG + REPLAN; (c) wrapper TTSDS2 no eval/; (d) preparar F4
   (trocar Kokoro→Qwen3-TTS no tools/data/synth e notebook moshi-finetune
   A100-80/G4); (e) montar Maya-BR v0 quando o CSM-pt-BR existir (F2-F3).

## Estado das tasks (painel)

#1 pesquisa = feita (8/8 frentes; síntese automática opcional em voo);
#2 REPLAN = feito; #3 kit de gravação = feito; #4 notebooks 01-04 = FEITOS;
#5 = speaker_sim feito + memória gravada; TTSDS2 pendente (próxima sessão).
