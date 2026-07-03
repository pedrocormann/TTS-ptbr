# SESSION-STATE — 2026-07-02 (sessão "revisão geral + fixes + Voz Lab")

> Fonte de verdade do projeto: **docs/REVISAO-2026-07-02.md** (substitui specs/ onde contradiz).
> Trilha no app atualizada (tools/rate/trilha_map.json). Estado anterior deste arquivo estava
> congelado em 10-11/jun — histórico está no git.

## Onde o projeto está

- **Fase M0.5 — "flywheel medido"**: coleta declarada em 21/jun produziu 0h novas até hoje.
  O pipeline agora fecha ponta-a-ponta: gravar (gravador consertado) → processar → curar →
  **exportar** (`tools/data/export_flywheel.py`, NOVO) → treinar. Placar atual: **259 clipes /
  24,4 min do Pedro**. João e Guilherme: 0h e consentimento NÃO assinado.
- **Ciência recalibrada** (verificada em fonte primária): identidade de voz satura ~2-3h;
  horas grandes pertencem à LÍNGUA (CPT 500-3000h) e ao TIPO de dado (conversa multi-turno).
  M1 = 5h bem compostas do Pedro (~1 mês a 30min/dia), não 20h.
- **GPU não é gargalo**: programa completo ~$330-480 (preços 02/jul verificados + throughput
  medido do harness). Gargalo = gravar, ouvir, assinar, ligar.
- **Prosódia tem baseline objetiva pela 1ª vez** (`eval/prosody_baseline_2026-07-02.md`):
  robótico = menos pausa + ritmo achatado vs Pedro real; curadoria deixou MAIS robótico.

## O que esta sessão entregou (02/jul)

1. **Fixes P0**: gravador (`whoVal` recursivo, maya_recorder.html), chain CPT
   (`prep_base_pt.py` shippable hardcoded + `cpt_base_pt.py` path `segments/` + `--smoke`),
   `prosody_scorecard.py` (relative_to), rate_app (toast de save honesto + curar local
   persiste emoções + sumário na Trilha).
2. **`tools/data/export_flywheel.py`** — o elo que faltava curadoria→treino (local + supabase,
   testado de verdade nos 259 clipes).
3. **Harness rodada 3** (`runpod/train_voice.py` + `grid_rodada3.sh` + `RUNBOOK-rodada3.md`):
   --push-hub, mistura ponderada base+voz, held-out, cache de tokenização, spk-sim +
   prosódia no eval, multi-voz.
4. **Revisão geral**: `docs/REVISAO-2026-07-02.md` (o que fizemos, o que morre, metas
   M0.5/M1/M2/M3, orçamento GPU verificado, roadmap 30 dias) + dossiês novos em
   `research/dossier-2026-07/` (Sesame, escala de dados, custos GPU, competitivo, voice UI).
5. **Voz Lab** (`tools/voice_ui/voz_lab.html`): 8 direções de identidade visual do agente
   (AURA/SAMANTHA/TRAMA/FUNDIÇÃO/NOVATRIX/ESPECTRO/PRESENÇA/VIDRO), orb WebGL2
   audio-reativo, estados repouso/ouvindo/pensando/falando, mic real + demo, Pepi embutida.
   Servir com `python3 -m http.server` e abrir no celular (mic exige https/localhost).

## Retomar por aqui (semana 1 da REVISAO)

1. **Assinar consentimento** João + Guilherme (corrigir cláusula watermark antes).
2. **1ª sessão dirigida** dos 3 (30 min cada) — gravador funciona local agora.
3. **Eval humana do Treino 2** — top-4 no rate_app (block.txt já aponta treino-2), 1 tarde.
4. **maya_parity.md** — 30 min com o app da Sesame lado-a-lado.
5. **Chatterbox v3 pt-BR (MIT, 10/jun)** — baixar, gerar as 14 frases, baseline cega no
   rate_app. Se ganhar de lavada do CSM, re-justificar a espinha.
6. Semana 2+: smoke chain ($3) → mini-grid ($27) → **CPT base-pt-v2 1.000h (~$200)**.

## Decisões desta revisão (não re-litigar)

G2P morto · curadoria-como-alavanca-de-WER morta (curar só estilo/emoção/lixo/números) ·
Moshi deixa de ser "a aposta" (cascata é a arquitetura; reavaliar com 50h+ estéreo) ·
FreeSVC morto até eval existir · voz F contratada fora do MVP · gate MOS 4.0 vira norte
distante (gates novos mensuráveis na REVISAO §6).
