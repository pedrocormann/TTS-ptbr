# arch-ar-codeclm — LM autoregressivo sobre codec neural (o paradigma do CSM)

**Sub-tópico:** arquitetura da família "LM AR sobre codec RVQ" — o spine de VOZ.
**Pergunta de decisão:** o CSM-1B AR ainda é a escolha certa de spine, ou algum AR-codec-LM aberto novo é melhor (pt-nativo, mais streamável, licença ok)?
**Data:** 13/jul/2026. Verificado via WebSearch/WebFetch onde marcado; inferências marcadas.

---

## TL;DR — a decisão mudou

**O CSM deixou de ser a única opção óbvia de spine.** Em jan/2026 a Alibaba abriu o **Qwen3-TTS** — um LM AR sobre codec RVQ a **12,5 Hz** (o *mesmo paradigma e a mesma taxa do Mimi/CSM*), em **Apache-2.0**, **0.6B e 1.7B**, com **pt-BR nativo forte** (WER 1.526, spk-sim 0.817 no relatório deles, batendo ElevenLabs em similaridade) e **first-packet 101 ms**. Isso ataca de frente o nosso **gap #1 (sotaque gringo)**, que existe justamente porque a **base do CSM é enviesada pro inglês**.

**Recomendação central:** promover o **Qwen3-TTS-12Hz (0.6B → depois 1.7B)-Base** a **candidato a spine** e rodar um *bake-off* contra o CSM na voz do Pedro (Estágio B LoRA). Não é "trocar já às cegas" — é que a hipótese "começar de uma base pt-nativa em vez de ensinar pt ao CSM do zero (Estágio A)" pode **dissolver o Estágio A inteiro** e encurtar o caminho pra Maya-BR. Único ponto onde o CSM ainda ganha: **condicionamento em contexto/turnos de diálogo em áudio** (o diferencial do CSM). Pra cascata *Maya-BR v0* (VAD→ASR→LLM→TTS), esse diferencial **não é load-bearing** — a voz é chamada turno-a-turno.

**Gate de licença:** Apache-2.0/MIT/CC-BY passam (Qwen3-TTS, Step-Audio 2, VoxCPM, Kyutai/Moshi, Higgs-v2, VibeVoice). **Reprova:** Higgs-**v3** (NC), e provavelmente Llasa/XCodec2 e Spark-TTS (NC — verificar antes de embarcar peso).

---

## Tabela de decisão

| Modelo | Paradigma | Licença (peso) | pt-BR | Streaming | Contexto/full-duplex | Veredito |
|---|---|---|---|---|---|---|
| **Qwen3-TTS-12Hz** (Alibaba) | AR multi-codebook RVQ 12,5 Hz (16 quant.) + decoder ConvNet causal | **Apache-2.0** ✅ | **Nativo, forte** (WER 1.53) | **101 ms** first-packet | Não (TTS controlável, sem turnos) | **ADOPT/TEST** — candidato a spine |
| **CSM-1B** (Sesame) — incumbente | AR sobre Mimi RVQ 12,5 Hz, audio-conditioned | **Apache-2.0** ✅ | Não-nativo (base EN → exige Estágio A) | ~ns (AR streamável) | **Sim — turnos de diálogo em áudio** (diferencial) | **TEST/WATCH** — desafiado |
| **Higgs Audio v3-4B** (Boson) | AR sobre Qwen3-4B, tokenizer próprio 8 cb @25fps, delay pattern | **NC** ❌ (Research/Non-Commercial) | **<5 WER/CER** (102 idiomas) | sub-seg TTFA (SGLang/vLLM) | Não | **WATCH** (método) / **SKIP** (peso NC) |
| **Higgs Audio v2** (Boson) | idem família, jul/2025 | **Apache-2.0** ✅ | plausível (inferido) | rápido local | Não | **TEST** (fallback Apache da família) |
| **Step-Audio 2 mini** (StepFun) | S2S MLLM 8B, thinker-talker, tokens texto+áudio | **Apache-2.0** ✅ | fraco (ZH/EN) | streaming | **Full-duplex** (thinker-talker) | **WATCH** — alt. de spine ao Moshi |
| **Kyutai TTS / Moshi / Pocket** | Delayed-Streams sobre **Mimi**; Moshi full-duplex | **CC-BY-4.0** ✅ | **pt adicionado abr/2026** | 1.6B stream; **Pocket 100M em CPU** | **Moshi = full-duplex** | **TEST** (Kyutai-TTS) / **WATCH** (Moshi spine) |
| **VoxCPM2** (OpenBMB) | **tokenizer-free**: AR sobre representação contínua + difusão local | **Apache-2.0** ✅ | 30 idiomas (pt plausível) | streaming | context-aware (não-duplex) | **WATCH** — fora do paradigma RVQ |
| **CosyVoice 3** (Alibaba) | AR codec-LM | Apache (histórico) | multi | streaming | Não | **SKIP** — superado pelo Qwen3-TTS (mesmo lab) |
| **VibeVoice** (Microsoft) | next-token diffusion, long-form multi-speaker | **MIT** ✅ | **Não (EN/ZH)** | batch/long-form | Multi-speaker, não conversacional | **SKIP** — sem pt, caso de uso errado |

---

## Detalhe por item (o que é NOVO / decisivo)

### 1) Qwen3-TTS-12Hz — o desafiante sério do CSM  · **ADOPT/TEST** · Apache-2.0 ✅
- **Verificado (WebFetch relatório + GitHub, 13/jul):** liberado **22/jan/2026**; Apache-2.0 peso+código; variantes **0.6B e 1.7B** em `Base` (fine-tunável), `CustomVoice`, `VoiceDesign` no HF.
- **Por que importa pra nós:** é **o mesmo paradigma do CSM** — LM AR sobre codec RVQ multi-codebook a **12,5 Hz** (16 quantizadores, codebook 2048) + **decoder ConvNet causal leve** (dispensa DiT/flow do variante 25Hz). Ou seja: a nossa intuição de arquitetura (Mimi/RVQ 12,5 Hz) migra 1:1.
- **pt-BR:** avalia **"Brazilian and standard Portuguese"**; WER **1.526** e **spk-sim 0.817** (12Hz-1.7B) — spk-sim **acima do ElevenLabs (0.711)**, WER perto (EL 1.331). Bate CosyVoice 3 e MiniMax. Isso é o antídoto direto do **gap #1**.
- **Latência:** **101 ms first-packet** (LM TTFT 97 ms + decoder 4 ms). Mais streamável que a nossa referência.
- **Fine-tune:** existe repo `Qwen3-TTS-Finetuning`; os `-Base` são feitos pra isso → **plugável no nosso Estágio B (LoRA da voz do Pedro)**.
- **Limite honesto:** é **TTS controlável (ChatML pra instrução)**, **sem condicionamento em turnos de diálogo em áudio**. Não substitui o CSM *se* o produto exigir memória prosódica de contexto conversacional. Para a cascata Maya-BR v0, não exige.
- **Ação:** *bake-off* Qwen3-TTS-12Hz-0.6B-Base **vs** CSM-1B na voz curada do Pedro (mesmo eval: WER + spk-sim + scorecard-robótico/IU). Hipótese a matar: "base pt-nativa mata o Estágio A".

### 2) CSM-1B — incumbente, agora sob pressão  · **TEST/WATCH** · Apache-2.0 ✅
- **Verificado (dossiê 81):** **sem update desde 01/dez/2025**; Sesame virou produto (app iOS EN-only), sem pt-BR. Base **enviesada pro inglês** = causa-raiz do sotaque.
- **Diferencial real que sobrevive:** **audio-conditioning em turnos** (condiciona na fala anterior do diálogo) — é a peça "conversacional" que Qwen3-TTS/Higgs/VoxCPM **não** têm. Vale se/quando sairmos da cascata pro full-duplex.
- **Veredito:** manter como baseline e como spine **default** enquanto o bake-off não decidir; deixar de tratar como "a única opção".

### 3) Higgs Audio v3-4B — método-ouro, licença mata o peso  · **WATCH / SKIP-peso** · NC ❌
- **Verificado:** **"Boson Higgs TTS 3 Research and Non-Commercial License"** → **reprova o gate de produto**. 4B AR sobre **Qwen3-4B**, tokenizer 8 codebooks @25fps, **delay pattern** escalonado. pt-BR/pt-EU **<5 WER/CER**, **102 idiomas**, sub-seg TTFA em SGLang/vLLM, 211k downloads/mês.
- **Uso legítimo:** **referência de método** (delay-pattern multi-codebook, backbone-LLM-como-talker) e **gerador de dado sintético NÃO-embarcável** (o peso é NC; o áudio gerado herda restrição — cuidado). Não embarca peso.
- **Fallback Apache:** **Higgs Audio v2** (jul/2025, **Apache-2.0**) — mesma família, testável e comercial-ok. pt de v2 = **inferido**, verificar.

### 4) Step-Audio 2 mini — full-duplex Apache (alt. ao Moshi)  · **WATCH** · Apache-2.0 ✅
- **Verificado:** **Apache-2.0** (mini / mini-Base / mini-Think); **S2S 8B**, arquitetura **thinker-talker** (full-duplex I/O), CoT+RL, entende para-linguística. Supera GPT-4o-Audio em benchmarks (claim do lab).
- **Fit:** é um **spine full-duplex Apache** — concorrente direto do **Moshi (parkeado)** para o plano de longo prazo. Mas: **8B (pesado pro nosso GPU <$500)**, foco **ZH/EN** (pt fraco), e é **S2S com LLM embutido** (não casa com a cascata que separa LLM da voz). **Vigiar** como opção de spine duplex quando/se a cascata evoluir.

### 5) Kyutai TTS / Moshi / Pocket TTS — CC-BY, Mimi, pt novo  · **TEST/WATCH** · CC-BY-4.0 ✅
- **Verificado:** **CC-BY-4.0** (passa). Framework **Delayed-Streams** sobre **Mimi** (o codec que embasa nossa intuição). **Moshi** = full-duplex, ~200 ms. **Kyutai TTS 1.6B** streaming (Unmute). **Kyutai Pocket TTS** (jan/2026, **100M, CPU real-time**); **pt adicionado em abr/2026** (+EN/FR/DE/ES/IT).
- **Fit:** Kyutai-TTS = alternativa **streaming, CC-BY, com pt** — e o **Pocket 100M em CPU** é uma história de **deploy barato** interessante (edge/latência). Moshi segue sendo a aposta de **full-duplex** de longo prazo. **Testar** Kyutai-TTS pt no bake-off como 3º competidor; **vigiar** Moshi.

### 6) VoxCPM2 — Apache e context-aware, mas fora do paradigma RVQ  · **WATCH** · Apache-2.0 ✅
- **Verificado:** **Apache-2.0** peso+código. **VoxCPM2 = 2B, ~2M h, 30 idiomas** (pt **plausível**, verificar), context-aware, clonagem "true-to-life", supera CosyVoice 3.
- **Ressalva de paradigma:** é **tokenizer-free** — AR sobre **representação contínua + difusão local**, *não* um LM sobre codec RVQ discreto. Diverge do nosso stack (Mimi/RVQ) e da intuição de tokens discretos. **Vigiar** como plano-B arquitetural (se o codec discreto travar qualidade), não como plug direto.

### 7) CosyVoice 3 — superado pelo próprio lab  · **SKIP/WATCH**
- AR codec-LM da Alibaba; **o Qwen3-TTS (mesmo lab) o supera** em zero-shot e cross-lingual (redução de 66% de erro zh→ko citada). Sem razão pra adotar CosyVoice 3 tendo Qwen3-TTS Apache. Arquivar.

### 8) VibeVoice — MIT, mas caso de uso errado  · **SKIP**
- **Verificado:** **MIT**; long-form multi-speaker (até 90 min, 4 vozes), **EN/ZH apenas**, next-token diffusion. **Sem pt**, otimizado pra podcast/long-form, **não** pra baixa latência conversacional. Fora do nosso alvo.

---

## Consequências pro roadmap (o delta de decisão)

1. **Abrir um arm de bake-off de spine** (barato): Qwen3-TTS-12Hz-0.6B-Base **vs** CSM-1B **vs** Kyutai-TTS-pt, todos com LoRA/fine-tune na voz curada do Pedro, medidos no *mesmo* eval (WER + spk-sim + scorecard-robótico por IU). É o experimento de maior alavancagem do trimestre porque testa se a **base pt-nativa** dissolve o **Estágio A** e o **gap #1**.
2. **Reenquadrar o Estágio A:** se Qwen3-TTS-12Hz vencer, "ensinar pt-BR ao CSM" deixa de ser pré-requisito — vira "adaptar timbre/prosódia carioca sobre base já-pt". Muda o custo de dado e de GPU.
3. **Licença:** todo o topo do cardápio passa no gate (Apache/CC-BY). O único peso quente que **reprova** é o Higgs-v3 (NC) — usar só como referência de método, nunca embarcar peso nem dado gerado por ele.
4. **Full-duplex de longo prazo:** Moshi (CC-BY) e Step-Audio 2 mini (Apache) são as duas opções abertas de spine duplex; ambas parkeadas até a cascata amadurecer. Step-Audio 2 é o novo nome a vigiar (Apache, thinker-talker).

**Verificado vs inferido:** licenças, taxas de frame, datas e números de WER/latência do Qwen3-TTS, Higgs, Step-Audio 2, Kyutai e VoxCPM foram checados na web (jan–jul/2026). Inferidos/plausíveis (marcados): pt de Higgs-v2 e VoxCPM2; que o `-Base` do Qwen3-TTS aceita LoRA no nosso Estágio B (documentação diz "designed for fine-tuning", não testamos); licenças NC de Llasa/XCodec2/Spark-TTS (presumidas, verificar antes de qualquer uso de peso).
