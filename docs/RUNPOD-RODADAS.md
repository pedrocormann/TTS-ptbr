# Rodas de código pro RunPod (próximas execuções)

Mapa do que rodar, em ordem, e qual linha de pesquisa cada roda alimenta (ver docs/LINHAS-DE-PESQUISA.md).
Tudo respeita o gate de licença (`tools/data/ingest.py` · `assert_license_gate`) — só dado shippável vira peso.

## Pré-condição (1x, barato, CPU)
- `python tools/data/ingest.py --check` — valida o registry (licença×shippable).
- `python tools/data/ingest.py --build-manifest T0` — gera o manifest dos shippáveis T0.

## F1 — Base-PT / Língua (GPU)
1. `python runpod/prep_base_pt.py --sources cml,mls,cv --out data/manifests/base_pt.jsonl`
   baixa os ~417h CC-BY/CC0, monta o manifest (NUNCA TAGARELA/NC).
   - opcional: `--sources granary --dnsmos 3.0` (in-the-wild, filtra qualidade).
2. `python runpod/cpt_base_pt.py --manifest data/manifests/base_pt.jsonl --version v1 --minutes 600`
   continued pre-train → `runs/base_pt_v1/` (o checkpoint que a voz herda). Gate de licença antes de gastar GPU.
   **Meta:** WER de leitura (held-out 50 frases) < 15% mantendo timbre.

## F2 — Voz & Sotaque Carioca (GPU)
3. `python runpod/train_voice.py --base-adapter runs/base_pt_v1 --data-dir <voz_limpa> --lora-r 16 --lr 5e-5 --minutes 60`
   LoRA r16 barato SOBRE o base-pt-v1, só com gravação dirigida limpa (ZERO público). 1 adapter por voz.
   - antes: medir 2 semanas REAIS do flywheel (h/semana) — mata as ETAs-fantasia.

## F3 — Prosódia & Expressividade (CPU eval + GPU treino)
4. `python tools/prosody/prosody_scorecard.py --dir runpod_samples/treino2_all` — 1º número objetivo do 'robótico'
   (taxa de fala, sílaba nuclear, pausas, SD) vs os alvos naturais pt-BR da Aluísio. **Roda JÁ, não precisa treinar.**
5. (depois) rotulagem de estilo-por-contexto + DPO usando o rate_app como gerador de pares A/B.

## F4 — Eval & Instrumentação
6. `python tools/recording/predict_emotion.py` — emotion2vec+ pré-prediz emoção (sugestão da IA no Curar).
7. carregar TAGARELA-clean como eval-set FIXO no rate_app (uso legal do NC) + 1ª rodada de eval humana do Treino 2.

## F5 — Augmentação & Dados-Baratos (GPU)
8. `python tools/voice_conversion/freesvc_augment.py` — converte fala pt-BR genérica → voz do Pedro (gate: só entra no treino se a eval HUMANA melhorar).
9. (pipeline) Câmara dos Deputados (CC-BY): download→VAD→ParlaSpeech-align→DNSMOS→tier T0 — 1ª fonte espontânea licenciada.

## Fluxo de dado contínuo (quando houver gravação)
- `python tools/recording/process_recording.py --user <nome> --audio <faixa>` — Whisper→quebra em frases→Curar.

> Regra-mãe: **público e voz NUNCA no mesmo passo de gradiente.** C0 (língua) → C1 (conversa) → C2 (voz limpa). Ver docs/ESTRATEGIA-DADOS.md.
