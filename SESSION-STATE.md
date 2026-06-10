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

## Trabalho em voo no momento do corte (pode ter terminado ou não)

- **Workflow de pesquisa** (runId `wf_ff245249-d44`): faltava só a síntese final
  → `research/dossier-2026-06/00-SYNTHESIS.md`. Se o arquivo não existir, os 8
  relatórios 10..60 + o REPLAN já cobrem o conteúdo (eu li todos e o REPLAN é a
  síntese). Para retomar o workflow:
  `Workflow({scriptPath: "<session-dir>/workflows/scripts/tts-ptbr-research-refresh-wf_ff245249-d44.js", resumeFromRunId: "wf_ff245249-d44"})` — agents concluídos vêm do cache.
- **3 agentes de extração de API** (p/ escrever os notebooks de finetune fiéis às
  APIs reais): (a) Qwen3-TTS finetune (QwenLM/Qwen3-TTS + cheeweijie/
  qwen3-tts-lora-finetuning patchado), (b) CSM-1B Unsloth (notebook oficial
  Sesame_CSM_(1B)-TTS.ipynb + docs Unsloth + knottwill), (c) Chatterbox-pt-br +
  Pocket-TTS-pt (uso/clone/finetune). Se os resultados não chegaram, a próxima
  sessão refaz essas 3 buscas (prompts descritos acima) antes de escrever os
  notebooks 02-04.

## Próximos passos (na ordem)

1. **Escrever notebooks** (com as APIs reais extraídas):
   - `notebooks/02_baseline_zeroshot.ipynb` — clone zero-shot do Pedro em
     Chatterbox-pt-br + Pocket-TTS-pt + Qwen3-TTS(3s); eval WER+spk-sim sobre
     `eval/benchmark_ptbr.jsonl`; decide candidato #1 (gate F0.5 do REPLAN).
   - `notebooks/03_finetune_qwen3tts.ipynb` — LoRA sobre dataset_v1 (canonical).
   - `notebooks/04_finetune_csm_unsloth.ipynb` — LoRA T4 sobre formato csm.
2. Atualizar `specs/roadmap.md` (apontar pro REPLAN) e `phase0/RUNBOOK.md`
   (trocar Kokoro→Qwen3-TTS/Chatterbox-pt-br no passo de síntese; nota A100-80/G4).
3. `eval/`: adicionar wrapper TTSDS2 + trocar default do README (UTMOS rebaixado).
4. VIGIL-LOG: registrar scan de 10/jun (Kyutai RL + Qwen3-TTS + PersonaPlex).
5. Pedro (não-Claude): Colab Pro+, gravar G0, rodar notebook 02, e-mail NILC.

## Estado das tasks (painel)

#1 pesquisa = concluída na prática (falta só o 00-SYNTHESIS automático);
#2 REPLAN = **feito**; #3 kit de gravação = feito; #4 notebooks = 01 feito,
02-04 pendentes (dependem dos 3 agentes acima); #5 eval/memória = speaker_sim
feito, TTSDS2 pendente, memória persistente gravada.
