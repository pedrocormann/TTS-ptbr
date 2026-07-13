# arch-codecs — a fronteira dos CODECS neurais mapeada ao nosso spine

**Sub-tópico:** os codecs neurais em si (a base de tudo). Mimi (nosso), DAC, SNAC, XCodec2, WavTokenizer, BigCodec + a fronteira single-codebook / low-frame-rate.
**Pergunta de decisão:** a escolha do codec importa pro nosso spine? Vale trocar o Mimi algum dia?
**Data:** 2026-07-13. Verificado na web onde marcado `[web Jul/26]`; o resto é inferido do conhecimento e marcado `[inf]`.

---

## TL;DR (a decisão em 5 linhas)

1. **No nosso spine atual (CSM), o codec NÃO é uma peça trocável — ele está FUNDIDO no modelo.** O backbone do CSM prevê o *codebook-0 do Mimi*; o decoder prevê os *demais codebooks do Mimi*. Trocar o codec = retreinar a cabeça de áudio do CSM do zero = **trocar de spine**. Não é flag de config.
2. **Mimi está bem escolhido. Não persiga codec-SOTA pro spine.** 12.5 Hz streaming, split semântico/acústico (o codebook-0 semântico é exatamente o que o backbone modela), CC-BY-4.0 (passa no gate). É praticamente feito sob medida pro nosso desenho AR-LM-sobre-codec.
3. **A ÚNICA coisa codec-adjacente acionável e de alto valor agora é o T-Mimi** (Meta, ICASSP 2026): mantém os *tokens* do Mimi, troca só o *decoder* convolucional por transformer → 42.1ms → 4.4ms on-device. Casa direto com o caminho iOS nativo. Método livre. → **TEST/ADOPT (só o decoder de saída).**
4. **Todo o resto é WATCH**, a menos que a gente pivote de arquitetura. Se um dia formos construir um spine *net-new* (não-CSM), os candidatos de bake-off são: **DualCodec** (o alternativo aberto mais parecido com Mimi, 12.5 Hz) e a linha **single-codebook** (XCodec2/WavTokenizer/BigCodec) que habilita TTS de *stream único* estilo LLaSA — outra aposta de arquitetura.
5. **O gargalo do projeto continua sendo DADO, não o codec.** Nenhum codec desta lista fecha o gap de sotaque/prosódia. Codec mexe em latência, custo de treino e teto de fidelidade — não em "a Maya soa carioca".

---

## O mapa mental: 2 eixos que trocam entre si

Um codec neural comprime waveform → tokens discretos que o LM prevê. Pro nosso caso (LM autoregressivo em cima do codec), três grandezas competem:

- **Frame-rate (Hz)** = quantos passos o LM dá por segundo. Menor = menos passos AR = **menor latência + treino/inferência mais rápidos**. Mas cai num "penhasco de qualidade" se for baixo demais.
- **Nº de codebooks (RVQ)** = quantos tokens por frame. Mais codebooks = mais info por frame (compensa frame-rate baixo), mas complica o LM (precisa prever N streams).
- **Fidelidade / bitrate** = teto de qualidade de reconstrução.

**A tensão central:** dá pra baixar o frame-rate empilhando mais codebooks (Mimi: 12.5 Hz × 8 codebooks) OU manter 1 codebook só e pagar em frame-rate (WavTokenizer/BigCodec/XCodec2: 40–80 Hz × 1 codebook). São **duas famílias de aposta arquitetural**, não "melhor/pior":

| Família | Exemplos | Ganho | Custo |
|---|---|---|---|
| **Low-frame-rate multi-codebook** | **Mimi 12.5Hz**, DAC-12.5Hz, DualCodec | Poucos passos AR → streaming/latência; split semântico | LM precisa prever N codebooks (arq. dual-decoder, tipo CSM) |
| **Single-codebook (1 stream)** | WavTokenizer, BigCodec, **XCodec2**, TS3/FocalCodec | LM vira 1 stream simples (dá pra plugar num LLaMA cru, tipo LLaSA) | Frame-rate mais alto (40–80Hz) → mais passos AR; menos "streaming-nativo" |

**12.5 Hz é o sweet-spot atual pra speech-LLM streaming** e é onde o Mimi vive. Abaixo disso (U-Codec 5Hz, variantes 6.25Hz) ainda é pesquisa com penhasco de qualidade — parcialmente contornável via config de treino (o paper "Probing Low Frame Rate Degradation" mostra que boa parte do cliff em 6.25Hz vem de clip fixo curto no treino, não do frame-rate em si).

---

## Tabela-fronteira (verificado)

| Codec | Frame-rate | Codebooks | SR / bitrate | Licença | Streaming? | Split sem/acu | Fonte |
|---|---|---|---|---|---|---|---|
| **Mimi** (nosso) | 12.5 Hz | 8 (RVQ split: 1 sem + 7 acu) | 24kHz / 1.1 kbps | **CC-BY-4.0** ✅ | **Sim** | **Sim** (distila WavLM no cb-0) | [web Jul/26] |
| **T-Mimi** (Meta) | 12.5 Hz (tokens = Mimi) | idem Mimi | idem | método livre (paper) | Sim | idem Mimi | [web Jul/26] |
| **DAC** (Descript) | 50 Hz (var. 12.5Hz existe) | RVQ (9) | 44.1/24/16kHz / ~8 kbps | **MIT** ✅ | Não (conv, não-causal) | Não | [web Jul/26] |
| **SNAC** | multi-escala (~12/23/47 Hz) | RVQ hierárquico | 24kHz / 0.98 kbps | **MIT** ✅ | parcial | Não | [web Jul/26] |
| **WavTokenizer** | 40 ou 75 Hz | **1** | 24kHz / 0.9 kbps | **MIT** ✅ | Não | Não | [web Jul/26] |
| **BigCodec** | ~80 Hz | **1** (8192) | 16kHz / 1.04 kbps | **MIT** ✅ | Não | Não | [web Jul/26] |
| **XCodec2** (LLaSA) | 50 Hz | **1** (65.536) | 16kHz / ~0.8 kbps | **MIT** ✅ | Não | semi (SSL no encoder) | [web Jul/26] |
| **DualCodec** (Amphion) | **12.5 / 25 Hz** | RVQ + SSL | 24kHz | MIT (Amphion) [inf] | Sim | **Sim** (SSL 1º stream) | [web Jul/26] |
| **AffectCodec** | (paper) | — | — | paper-só [inf] | — | preserva emoção/prosódia | [web Jul/26] |
| **U-Codec** | **5 Hz** | RVQ | — | paper-só [inf] | — | — | [web Jul/26] |
| **FlexiCodec** | **dinâmico** (baixa taxa) | dinâmico | — | paper-só [inf] | — | semi | [web Jul/26] |

> Nota bitrate XCodec2: 50 tok/s × log2(65536)=16 bits ≈ 0.8 kbps (uma fonte auto-calculou "6.4 kbps" — está errada, é 0.8).

---

## Vereditos por item

### Mimi — **ADOPT (manter). NÃO trocar no spine CSM.**
Feito sob medida pro nosso desenho: 12.5 Hz (menos passos AR = streaming real + barge-in viáveis), streaming encode/decode nativo, e o split RVQ com **codebook-0 semântico destilado do WavLM** — que é *exatamente* o que o backbone do CSM prevê, deixando o decoder pequeno pros 7 acústicos. Licença CC-BY-4.0 passa no gate. Trocar isso significa jogar fora o pré-treino da cabeça de áudio do CSM. **Sem motivo pra mexer.**

### T-Mimi — **TEST → ADOPT (só o decoder de saída, caminho iOS).** 🎯
O item mais acionável da lista pra nós. Troca o decoder híbrido conv+transformer do Mimi por um decoder **puramente transformer** (inspirado no TS3-Codec), porque deconvolução é hostil a CPU mobile (XNNPACK). Resultado: **42.1ms → 4.4ms** de latência de decode on-device (>9×), *mantendo os mesmos tokens do Mimi* — ou seja, **zero mudança no CSM**. Casa perfeitamente com o iOS nativo do roadmap. Achado prático: as 2 últimas camadas transformer + lineares finais são sensíveis a quantização e têm que ficar em precisão cheia. Método é livre (paper Meta/ICASSP 2026); teríamos que reimplementar/re-treinar o decoder, mas o custo é baixo e o payoff (latência mobile) é direto. **Braço barato de experimento pro caminho on-device.**

### DualCodec — **TEST-se-pivotarmos / WATCH.**
O alternativo *aberto* mais parecido com o Mimi: 12.5/25 Hz, low-frame-rate, com stream SSL semântico (mesma filosofia do split do Mimi), Amphion (MIT [inf]). É "o primeiro codec aberto de 12.5 Hz desse tipo". **Só entra em jogo se formos construir um spine net-new** (não-CSM) e quisermos um bake-off contra o Mimi. Enquanto o spine for CSM, é WATCH.

### XCodec2 — **WATCH (aposta de arquitetura diferente).**
Habilita a rota **LLaSA**: 1 codebook de 65.536 → TTS como *um LLaMA cru prevendo um stream único de tokens de fala*. Simplíssimo de treinar (sem dual-decoder), MIT, e a linha LLaSA já mostrou escala boa. **Mas é outro spine** (50 Hz, não-streaming-nativo, sem barge-in fácil) — conflita com nossa meta de full-duplex/baixa latência. Vale como plano-B de arquitetura pra TTS one-shot, não pro conversacional.

### WavTokenizer / BigCodec — **WATCH.**
Provas de conceito fortes de que single-codebook a bitrate baixíssimo funciona (WavTokenizer 0.9kbps @ 40-75Hz; BigCodec 1.04kbps @ ~80Hz, 8192 entradas). Ambos MIT. Mesma história do XCodec2: bons pra spine de *stream único*, não pro nosso CSM streaming. Úteis como baseline/benchmark de qualidade de reconstrução se formos medir teto de fidelidade.

### DAC (Descript) — **SKIP pro spine / útil só como ferramenta.**
MIT, alta fidelidade (44.1kHz, ~90× compressão), mas **50 Hz, não-causal/não-streaming, sem split semântico** — errado em todos os eixos que importam pro nosso spine conversacional. Serve como codec de *resynthesis/análise* offline ou baseline de qualidade, não pro pipeline em produção.

### SNAC — **SKIP/WATCH.**
Multi-escala hierárquico (RVQ em resoluções temporais diferentes), MIT, 0.98kbps, é o codec do **Orpheus TTS**. Bonito conceitualmente e comprime bem, mas é o codec de *outro* stack (Orpheus/LLaMA-TTS). Pra nós, mesma categoria do XCodec2: só relevante se trocarmos de spine. WATCH o ecossistema Orpheus como concorrente/benchmark.

### AffectCodec — **WATCH (alinha com a meta de emoção).**
Codec "emotion-preserving": desenhado pra *não jogar fora* prosódia/emoção na quantização. Toca direto no nosso gap #2 (prosódia robótica) e na meta de emoção controlável. Provavelmente paper-só por ora [inf]. **Vigiar:** se validar que codecs padrão (inclusive Mimi) descartam sinal emocional na compressão, isso vira argumento pra fine-tunar/estender o decoder — mas o gargalo real continua sendo *dado emocional aberto ≈ 0h*, não o codec.

### U-Codec (5Hz) / FlexiCodec (dinâmico) / TS3 / FocalCodec — **WATCH (fronteira de pesquisa).**
A vanguarda do frame-rate: U-Codec empurra pra 5 Hz, FlexiCodec faz frame-rate *dinâmico* (mais tokens onde tem info), TS3-Codec (Microsoft) é o transformer-streaming-single que inspirou o T-Mimi, FocalCodec comprime tudo num **codebook binário único**. Interessantíssimos pra latência/custo futuros, mas sem pesos-produto maduros e todos ainda pagam penhasco de qualidade sub-12.5Hz. Não mexer agora; reavaliar quando algum virar peso aberto usável e estável.

---

## Resposta direta às perguntas do brief

**"A escolha do codec importa pro nosso spine?"**
Importou *uma vez* — quando escolhemos CSM+Mimi — e foi uma boa escolha. A partir daí, o codec está *fundido* no spine: não é uma peça que a gente troca. Então no dia-a-dia, **não**: não gaste ciclos comparando codecs pro CSM. Onde importa de verdade agora é **no decoder de saída on-device (T-Mimi)** — aí sim há ganho real (latência mobile) sem tocar no modelo.

**"Trocar o Mimi algum dia?"**
Só num de dois cenários: (a) **pivô de arquitetura** — se abandonarmos o CSM por um spine net-new, aí abre bake-off (DualCodec pro caminho streaming-dual; XCodec2/LLaSA pro caminho stream-único-simples). (b) **um codec estritamente-melhor-e-drop-in** aparecer — mesmo frame-rate 12.5Hz, mesmo split semântico, streaming, licença permissiva, E fidelidade nitidamente superior, com pesos abertos. Nada na fronteira atual é isso. Até lá: **Mimi fica.**

---

## Fontes (web, Jul/2026)
- Mimi / Moshi — https://huggingface.co/kyutai/mimi , https://github.com/kyutai-labs/moshi
- T-Mimi (Meta, ICASSP 2026) — https://arxiv.org/abs/2601.20094
- DAC (Descript) — https://github.com/descriptinc/descript-audio-codec
- SNAC — https://github.com/hubertsiuzdak/snac , https://arxiv.org/abs/2410.14411
- WavTokenizer — https://github.com/jishengpeng/WavTokenizer
- BigCodec — https://github.com/Aria-K-Alethia/BigCodec , https://arxiv.org/abs/2409.05377
- XCodec2 / LLaSA — https://github.com/zhenye234/X-Codec-2.0
- DualCodec (Interspeech 2025) — https://arxiv.org/abs/2505.13000 , https://github.com/jiaqili3/DualCodec
- AffectCodec — https://arxiv.org/pdf/2605.11098
- U-Codec (5Hz) — https://arxiv.org/abs/2510.16718
- FlexiCodec — https://arxiv.org/abs/2510.00981
- TS3-Codec — https://arxiv.org/abs/2411.18803
- Probing Low Frame Rate Degradation — https://arxiv.org/html/2606.16969
- CSM/Mimi acoplamento — https://aiwiki.ai/wiki/sesame_csm
