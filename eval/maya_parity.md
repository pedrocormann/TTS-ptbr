# Maya Parity Checklist — eval da Trilha M (v0, 2026-06-10)

> Protocolo pra responder "o Maya-BR está no nível da Maya?" com números e
> escuta estruturada, não vibe. Rodar a cada marco da Trilha M; comparar SEMPRE
> contra a Maya real (app iOS — Pedro tem acesso) na MESMA bateria.
> Pareia com `benchmark_ptbr.jsonl` (conteúdo) e `benchmark_sotaque_carioca.jsonl`
> (sotaque). Resultados → `research/VIGIL-LOG.md` + REPLAN.

## A. Latência percebida (medir com gravação de tela/áudio, 10 trocas)

| Métrica | Como medir | Maya (medir!) | Alvo Maya-BR |
|---|---|---|---|
| Resposta de turno p50 | fim da minha fala → primeiro áudio dela | ___ ms | ≤ Maya +20% |
| Resposta de turno p95 | idem, pior caso | ___ ms | ≤ 1.5× p50 |
| Latência de barge-in | eu interrompo → ela CALA | ___ ms | ≤ 300 ms |
| Retomada pós-interrupção | ela retoma coerente? | sim/não | sim |
| Falsos turnos | ela entra enquanto eu só pausei pra pensar | n/10 | ≤ Maya |

## B. Comportamento conversacional (sessão livre de 5 min, gravada)

- [ ] **Backchannels**: ela faz "uhum/é/hm" enquanto EU falo? Soam no momento certo?
- [ ] **Overlap natural**: começa a falar levemente sobreposta sem atropelar?
- [ ] **Prosódia contextual**: a emoção da resposta acompanha a MINHA (eu animado → ela acompanha)?
- [ ] **Hesitações humanas**: usa "é...", "tipo", respirações — sem exagero?
- [ ] **Riso**: ri quando algo é engraçado (não aleatório)?
- [ ] **Memória de sessão**: referencia o que falei 2+ minutos atrás?
- [ ] **Consistência de persona**: mesma personalidade/timbre a sessão inteira?

Pontuação: 0 (ausente) / 1 (presente mas artificial) / 2 (indistinguível de gente).
Maya real: ___/14 · Maya-BR: ___/14.

## C. Voz e sotaque (bateria objetiva)

1. Sintetizar `benchmark_ptbr.jsonl` → WER (whisper-large-v3) + spk-sim + TTSDS2.
2. Sintetizar `benchmark_sotaque_carioca.jsonl` → escuta cega com 3+ cariocas:
   "soa carioca?" (1-5) e "de onde?" (aberto); transcrição fonética dos traços
   (chiado /ʃ/ em coda, africadas tʃ/dʒ, /χ/, l→w) — o G2P do kit
   (`tools/recording/g2p_pt.py`) lista o esperado por frase (campo `traits`).
3. CMOS A/B cego vs Maya real falando inglês? NÃO — comparar expressividade
   relativa: gravar Maya em EN e Maya-BR em PT com conteúdo equivalente e
   perguntar "qual soa mais viva?" (admitidamente imperfeito; anotar viés).

## D. Conteúdo (separar voz de cérebro)

Falhas de CONTEÚDO (resposta burra/sem graça) são do LLM plugável, não da fala —
anotar separado. Trocar o LLM não pode exigir retreinar a voz (interface limpa).

## Veredito por marco

| Data | Setup Maya-BR | A (latência) | B (/14) | C (sotaque 1-5) | Decisão |
|---|---|---|---|---|---|
| | | | | | |
