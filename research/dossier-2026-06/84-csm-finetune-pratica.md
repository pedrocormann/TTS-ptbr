# 84 — CSM-1B finetune NA PRÁTICA (rodada 2)

**Data:** 2026-06-10 · **Frente C** do dossiê · Pesquisa web com fontes primárias.
**Contexto:** vamos treinar a voz do Pedro no CSM-1B (guia Unsloth já em mãos). Aqui: o que a comunidade REALMENTE conseguiu em outras línguas, como treinar conversacional (multi-turno), o que usar de emoção pós-DMCA da Elise, e se o csm-mlx serve para iterar no M2 24GB.

**Método:** tudo abaixo foi verificado em fonte primária (model cards HF, issues GitHub, docs oficiais). Onde não há evidência pública, está escrito "não verificável / não encontrado" — explicitamente.

---

## 1. Qualidade real dos finetunes comunitários de língua

Lista completa de finetunes públicos do `sesame/csm-1b` (≈26 modelos): https://huggingface.co/models?other=base_model%3Afinetune%3Asesame%2Fcsm-1b

### 1.1 Georgiano — o único com avaliação séria (caso-referência para o pt-BR)

**Modelo:** [NMikka/CSM-1B-Georgian](https://huggingface.co/NMikka/CSM-1B-Georgian) (44 downloads)

| Item | Valor |
|---|---|
| Dados | `NMikka/Common-Voice-Geo-Cleaned` — **21.421 amostras, 12 falantes, ~35 h** |
| Método | **LoRA r=64, α=64** via Unsloth, depois merged nos pesos base |
| Hiperparâmetros | batch 64 (efetivo 128 c/ grad. accum.), **LR 5e-5 cosine**, ~14 épocas |
| Compute | ~25 h em 1× RTX A6000; 58M params treináveis (3,44% de 1,69B) |
| Métricas | **CER in-domain 0,0281**; CER FLEURS (fora de domínio) 0,1081; WER in-domain 0,1363 |
| Falhas | **4,1% dos testes com CER >50%** (colapso em texto complexo); alucinação/truncamento em frases longas; pouca diversidade de voz (só 12 falantes) |

Sem MOS humano. Mas é a prova de que **35 h de Common Voice limpo + LoRA r=64 ensinam uma língua nova inteligível ao CSM** — com cauda de falhas catastróficas de ~4%.

### 1.2 Árabe (CV17) — full-FT, resultado admitido como fraco

**Modelo:** [MAdel121/Seasmed-Fine-Tuned-on-Common-Voice-17-Arabic](https://huggingface.co/MAdel121/Seasmed-Fine-Tuned-on-Common-Voice-17-Arabic) (clone: samehelalfi/...)

- **Full finetune** do csm-1b em Common Voice 17 árabe (horas não declaradas).
- Hiperparâmetros: batch 24, **LR 3e-6**, 25 épocas, warmup 569, AdamW + decay exponencial, mixed precision.
- Veredito do próprio autor no card: *"The model did show learning the new language… However performance was below average"* — culpa apontada: **ruído do Common Voice** (precisa de pré-processamento melhor) e **variação dialetal** do árabe.
- Zero métricas formais. Lição: CV cru + LR muito baixo + 25 épocas = aprende a língua mas soa ruim. Dataset limpo importa mais que receita.

### 1.3 Finlandês (parlamento, full-FT) — aprendeu os vícios do corpus

**Modelo:** [ArttuPakarinen/sesame-csm-FIN-parlament-full-finetune](https://huggingface.co/ArttuPakarinen/sesame-csm-FIN-parlament-full-finetune) (1 download)

- Dados: `Aalto-Speech-Synthesis/Nord-Parl-TTS` (discursos parlamentares). Sem hiperparâmetros, sem métricas, sem compute documentado.
- Limitação admitida no card: **"Produces a lot of 'Ööö, äää öhm…'"** e "better with longer sentences" — ou seja, o modelo **aprendeu as hesitações/fillers da fala parlamentar espontânea** e as cospe sem controle.
- Lição direta para o Pedro: fala espontânea sem tags/limpeza → o CSM clona os fillers. Se quiser "uhm/é/tipo" controláveis, eles têm que estar **transcritos e/ou tagueados**, não soltos.

### 1.4 Suaíli — em produção, mas card vazio

**Modelo:** [Nadhari/swa-csm-1b](https://huggingface.co/Nadhari/swa-csm-1b) (141 downloads — o mais baixado dos linguísticos)

- Afirma ser "the best open-source Swahili TTS", **sem nenhum benchmark, sem dados de treino, sem hiperparâmetros**.
- Único sinal de qualidade: alimenta um produto real, o assistente de voz [Soga](https://nadhari.ai/soga). Nota que "requer contexto conversacional para resultados ótimos" (herda do CSM base).

### 1.5 Bengali — usou o pipeline knottwill (full-FT)

**Modelos:** [Mizbaul-Haque-Maruf/csm-bangla-finetuned](https://huggingface.co/Mizbaul-Haque-Maruf/csm-bangla-finetuned) e `-40000`

- Treinado com [knottwill/sesame-finetune](https://github.com/knottwill/sesame-finetune) (checkpoints de 38k/40k steps, run "bangla-v2"). Dataset: `csm-bangla-merged` (tamanho não declarado). **Sem métricas, sem report de qualidade.**

### 1.6 Bônus: Dinamarquês — o melhor report de "sotaque"

**Modelo:** [nicolajreck/csm-1b-danish-tts](https://huggingface.co/nicolajreck/csm-1b-danish-tts) (112 downloads)

- Dados: **~35.415 amostras** (CV17 dinamarquês 10.224 + CoRal-TTS 16.547 + extensão privada 8.644), clipes 0,6–16 s.
- **LoRA r=16, α=32, dropout 0,05**, FP16, 1× RTX 3090 (LoRA cabe em GPU de 24 GB).
- Qualidade reportada (qualitativa): ritmo natural, boa pronúncia — e um efeito colateral revelador: **"Exceptional English with Danish accent"** → o finetune de língua transfere sotaque para o inglês residual; espere o mesmo no pt-BR (inglês com sotaque brasileiro depois do treino).

### 1.7 Outros encontrados (sem reports úteis)

- Indonésio: `Ellbendls/csm-1b-indonesian-fine-tuned` (0 downloads); Hindi: `namankhurpia/csm-1b-hindi-lora` (2 downloads). Cards vazios.

### 1.8 Português / Espanhol: alguém tentou e desistiu?

- **Nenhum finetune público pt/es do CSM existe** (busca na HF API `?search=csm&filter=text-to-speech` + web, 2026-06-10): zero modelos PT, ES, FR, DE, JA, KO, TR.
- Nas discussões do `sesame/csm-1b` ([índice](https://huggingface.co/sesame/csm-1b/discussions)): pedido de **persa** sem resposta (discussion #21), nada de pt/es.
- No [knottwill/sesame-finetune issue #3](https://github.com/knottwill/sesame-finetune/issues/3) (Urdu, 21 h single-speaker): o autor da issue menciona que **tentativas anteriores de árabe com o mesmo repo "produziram resultados subótimos"** — sem resposta do maintainer. Issues #4 (incluir loss nos tokens de texto ajuda língua nova?) e #5 (VRAM) também **sem resposta**.
- **Não encontrei** report explícito de alguém que tentou pt/es e falhou/desistiu — não verificável. O que existe é um vácuo: ninguém publicou. Para o pt-BR, o projeto do Pedro seria o primeiro público.

### 1.9 Armadilha clássica pós-finetune (vai acontecer com você)

[unsloth/csm-1b discussion #2](https://huggingface.co/unsloth/csm-1b/discussions/2): após finetune, **saída sempre com 10 s exatos** (ruído/silêncio de padding ou truncamento) + fala lenta. Causa confirmada pela equipe Unsloth: `max_new_tokens` default = **125 tokens = 10 s de áudio** — é parâmetro de inferência, não bug do treino. Fala lenta = qualidade/ritmo do dataset. Anotar no notebook: sempre subir `max_new_tokens` na avaliação.

### 1.10 Receita do guia "sério" (Speechmatics/knottwill)

[Blog Speechmatics](https://blog.speechmatics.com/sesame-finetune) + [repo](https://github.com/knottwill/sesame-finetune) (110 stars): para **mudança de língua, full-FT > LoRA** ("higher compute burden but much better for significant domain shifts like new languages"). Config exemplo: **LR 3e-5, weight decay 0,002, batch 8**, sweep com Optuna, pré-tokenização obrigatória (`pretokenize.py`). É tutorial, não case study — sem métricas próprias publicadas.

**Síntese da frente 1:** padrão consistente nos casos reais: (a) 20–35 h ensinam a língua; (b) Common Voice cru produz qualidade "abaixo da média" (árabe) — limpeza compensa (georgiano); (c) corpus espontâneo sem anotação contamina o modelo com fillers (finlandês); (d) LoRA r=16–64 já funciona para língua com 35 h, contradizendo na prática o dogma "full-FT obrigatório" — mas ninguém comparou os dois de forma controlada; (e) cauda de ~4% de falhas graves mesmo no melhor caso.

---

## 2. Finetune CONVERSACIONAL com áudio-contexto (multi-turno)

### 2.1 Suporte oficial: SIM, e está nos docs do transformers

[Docs oficiais do CSM no transformers v5.x](https://huggingface.co/docs/transformers/en/model_doc/csm), seção *Training* — o exemplo oficial de treino **já é multi-turno com áudio em todos os turnos**:

```python
ds = load_dataset("hf-internal-testing/dailytalk-dummy", split="train")
ds = ds.cast_column("audio", Audio(sampling_rate=24000))
conversation = []
for text, audio, speaker_id in zip(ds[:4]["text"], ds[:4]["audio"], ds[:4]["speaker_id"]):
    conversation.append({
        "role": f"{speaker_id}",
        "content": [{"type": "text", "text": text},
                    {"type": "audio", "path": audio["array"]}],
    })
inputs = processor.apply_chat_template(conversation, tokenize=True,
                                       return_dict=True, output_labels=True)
out = model(**inputs); out.loss.backward()
```

- **`output_labels=True` existe e funciona no chat template multi-turno.** Semântica dos labels (docs do `CsmProcessor.__call__`):
  - `-100` → ignorado na loss;
  - `-101` → frame de áudio usado **só pelo backbone** (primeiro codebook como label), não pelo depth decoder;
  - `depth_decoder_labels_ratio` (default 1.0) → fração dos frames que recebem label no depth decoder.
- Formato do texto: speaker id embutido como prefixo `[0]`/`[1]` (o template gera isso a partir do `role`).

### 2.2 A pegadinha: não há mascaramento por turno embutido

`output_labels=True` rotula **todos os frames de áudio da conversa** — contexto incluído. Para o regime "prever o turno final dado o contexto" (que reduz speaker drift sem treinar nas vozes dos interlocutores), é preciso **mascarar manualmente** os labels dos turnos de contexto com `-100` (pós-processamento do dict retornado). O template não tem flag para isso. Não encontrei issue no transformers pedindo esse recurso (busca por `CsmForConditionalGeneration labels` — nada específico de CSM).

Alternativa pronta: o **csm-mlx tem `--mask-speaker-ids`** (CLI) e mask por falante na API Python — exclui falantes específicos da loss, que é exatamente o mecanismo para "treina só na voz do Pedro, com os outros como contexto". Fonte: [FINETUNING_CLI.md](https://github.com/senstella/csm-mlx/blob/master/FINETUNING_CLI.md).

### 2.3 Quem treina multi-turno hoje

| Pipeline | Multi-turno no treino? | Fonte |
|---|---|---|
| transformers (oficial) | **Sim** (exemplo oficial com 4 turnos do DailyTalk) | docs acima |
| **csm-mlx** | **Sim, nativo**: dataset = `list[list[Segment]]` (text, audio_path, speaker_id); conversor de pastas preserva ordem da conversa; `--mask-speaker-ids` | [FINETUNING.md](https://github.com/senstella/csm-mlx/blob/master/FINETUNING.md) |
| Unsloth (notebook oficial) | **Não** — treina utterance isolada | [docs Unsloth TTS](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning) |
| knottwill/sesame-finetune | **Não** — metadados por utterance, sem campo de conversa | [repo](https://github.com/knottwill/sesame-finetune) |
| davidbrowne17/csm-streaming (`lora.py`) | **Não** — pasta de WAVs crus, sem contexto | [repo](https://github.com/davidbrowne17/csm-streaming) |

### 2.4 Receita/discussão sobre treinar com contexto para reduzir speaker drift?

- O **speaker drift do CSM base é documentado** ("voice variation across generations… speaker ID tokens mainly help within a conversation, not across separate generations" — card unsloth/csm-1b; mitigação canônica = contexto de áudio na inferência).
- **Não existe report comunitário publicado com ablação "treino com contexto vs sem contexto"** para CSM — não encontrado em issues do unsloth, transformers, SesameAILabs/csm nem nos model cards. O que existe é o fato de o modelo original da Sesame ter sido treinado em conversas inteiras (paper "Crossing the uncanny valley of voice") e o suporte de ferramenta descrito acima.
- **Implicação prática:** treinar com janelas multi-turno é tecnicamente suportado (transformers e csm-mlx), inédito como report público — o experimento do Pedro (utterance-only vs janelas de 2–4 turnos com mask no contexto) seria contribuição original. Receita concreta: gerar `conversation` com N-1 turnos de contexto + turno final do Pedro, `output_labels=True`, zerar labels (-100) dos frames anteriores ao último turno via `input_values_cutoffs`.

---

## 3. Dataset de emoção PÓS-Elise (DMCA confirmado)

### 3.1 Status da Elise (verificado em 2026-06-10)

- [MrDragonFox/Elise](https://huggingface.co/datasets/MrDragonFox/Elise): **"Access to this dataset has been disabled" — DMCA takedown notice** na página. Era ~3 h, 1.195 amostras, MIT (autodeclarado), tags `<laughs>` (336), `<sighs>` (156), `<giggles>` (76), `<chuckles>` (20), whispers/gasps/etc. **18 modelos** foram treinados nela antes da queda.
- [Jinsaryko/Elise](https://huggingface.co/datasets/Jinsaryko/Elise) (a origem): página e API retornam **HTTP 401** → repo desabilitado/inacessível também. A discussion "borrowed your dataset" já apontava a cópia.
- O [guia da Unsloth](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning) **ainda referencia a Elise** — está desatualizado; não seguir o link de dataset de lá.
- Sucessor do próprio autor: [MrDragonFox/elise_new_large](https://huggingface.co/datasets/MrDragonFox/elise_new_large) — 26,5 GB, 10K–100K amostras, **GATED (acesso manual), sem licença declarada, README vazio** → **inutilizável para produto com licença dura**.

### 3.2 O que a comunidade usa AGORA

**(a) Sintético em escala — LAION's Got Talent (a aposta principal, com um asterisco):**
[laion/laions_got_talent](https://huggingface.co/datasets/laion/laions_got_talent) — metadado HF: **Apache 2.0**. Voice acting 100% sintético **gerado com OpenAI Voice API (modelos gpt-4o-audio) via Hyprlab** ([README](https://huggingface.co/datasets/laion/laions_got_talent/blob/main/README.md)). Contém vocal bursts (risadas, suspiros, gasps), ~40 categorias de emoção, 11 vozes; README fala "110 hours, will grow"; material do projeto BUD-E/LAION cita EN ~2.156 h, **ES ~888 h**, DE ~716 h, FR ~881 h (números divergem entre README e blog — conferir o split atual antes de baixar). Variantes: `laions_got_talent_raw`, `laions_got_talent_clean_with_captions`.
**Asterisco jurídico:** a licença declarada é Apache 2.0, mas a proveniência é output da OpenAI (termos da OpenAI restringem uso para treinar modelos concorrentes). Para a régua "Apache/MIT/CC-BY/CC0 dura" do projeto: o artefato é Apache 2.0 e o risco recai sobre quem gerou (LAION) — mas é uma decisão consciente a registrar, não um automatismo.

**(b) Benchmark/anotadores da mesma família LAION:** [EmoNet-Voice](https://arxiv.org/pdf/2506.09827) (benchmark de SER expert-verified), [laion/Empathic-Insight-Voice](https://huggingface.co/laion/Empathic-Insight-Voice-Small) e [laion/BUD-E-Whisper](https://huggingface.co/laion/BUD-E-Whisper) (Whisper adaptado para **caption emocional de fala**) — úteis como ANOTADORES do dataset do Pedro.

**(c) Expresso (Meta/ylacombe):** usado pelo autor do csm-mlx no [senstella/csm-expressiva-1b](https://huggingface.co/senstella/csm-expressiva-1b) — mas é **CC-BY-NC-4.0** (o próprio card herda a licença NC) → **vetado** para o produto do Pedro.

**(d) Auto-anotação (a via que substitui a Elise para datasets próprios):**
- **SER**: [emotion2vec_plus_large](https://huggingface.co/emotion2vec/emotion2vec_plus_large) ([código ACL 2024](https://github.com/ddlBoJack/emotion2vec)) — pseudo-label de emoção categorial (angry/happy/sad/surprised/…) em escala.
- **LLM sobre transcrição**: atribuição de emoção por frase com GPT-4o-mini (receita do paper [Optimizing Multilingual TTS with Accents & Emotions](https://arxiv.org/pdf/2506.16310)).
- **Vocal bursts**: BUD-E-Whisper/Whisper adaptado para detectar e transcrever risadas/suspiros como eventos ([abordagem](https://arxiv.org/pdf/2309.08108)).
- Não existe "a nova Elise" canônica — a comunidade fragmentou em sintético (LAION) + auto-anotação do próprio corpus.

**(e) Para pré-treino de língua (sem emoção) license-clean:** MrDragonFox/`*_Emilia_Yodas` (EN 616 h, DE 680 h, JA 266 h) são **CC-BY-4.0** — sem PT, mas confirmam o padrão Emilia-YODAS como fonte CC-BY (o split pt do Emilia-YODAS é a pista para o Pedro, já mapeada no dossiê 20).

### 3.3 Formato exato das tags para o CSM (recomendação)

Fato técnico: o tokenizer do CSM é o do **Llama 3.2** — `<laugh>` **não é token especial**, é texto puro quebrado em subwords. Não há tratamento especial de tags no processor (docs HF não mencionam tags; nenhum token de emoção no vocabulário). Logo, o modelo aprende a associação tag→som **por estatística no finetune** — foi exatamente assim que os 18 finetunes da Elise funcionaram.

Recomendação de formato para o dataset do Pedro (máxima compatibilidade com o ecossistema):

1. **Conjunto Orpheus** (padrão de fato da comunidade, [README oficial](https://github.com/canopyai/Orpheus-TTS/blob/main/README.md)): `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>` — minúsculas, ASCII, sem espaços internos.
2. Tag **inline na posição exata do evento** (não no início da frase): `"pois é <laugh> eu sei"`.
3. **Consistência absoluta** (uma grafia por evento; nada de `<risada>`/`<laughs>`/`<Laugh>` misturados). Se quiser tags pt-BR, vale — mas aí abre mão da compatibilidade com checkpoints/ferramentas que esperam o conjunto Orpheus; o ganho de tokenização é nulo (ambas viram subwords).
4. Mínimo de ocorrências por tag para aprender: a Elise funcionava com ~336 `<laughs>` e ~156 `<sighs>` em 1.195 amostras — mire **dezenas a centenas de exemplos por tag**, não unidades.
5. Fillers conversacionais ("uhm", "é…", risadinha curta) devem estar **transcritos literalmente** (lição do finetune finlandês, §1.3): o que não está no texto vira ruído incontrolável.

---

## 4. csm-mlx no Apple Silicon (M2 24 GB)

**Repo:** [senstella/csm-mlx](https://github.com/senstella/csm-mlx) (116 commits; destaque no Awesome MLX em mar/2026 — vivo).

### 4.1 Finetune local: funciona? SIM — evidência direta em M2

- **Prova concreta:** o próprio autor treinou o [senstella/csm-expressiva-1b](https://huggingface.co/senstella/csm-expressiva-1b) **num MacBook Air M2 16 GB ("heavy swap usage"), em ~43 min 47 s** — LoRA r=8, α=16, LR 1e-4, batch 1, 1 época, targets attention+codebook head+projeções, sobre a voz whispering do Expresso. Resultado qualitativo: SFT "somewhat mitigates CSM base model failure cases" (silêncio sem fim etc.). → **No M2 24 GB do Pedro, LoRA com batch 1–2 roda com folga maior que a do autor.**
- CLI completa ([FINETUNING_CLI.md](https://github.com/senstella/csm-mlx/blob/master/FINETUNING_CLI.md)): `full` e `lora`; defaults — full: epochs 5, batch 4, LR 1e-5; LoRA: epochs 10, batch 8, LR 5e-4, r=8/α=16. Flags decisivas: **`--train-embeddings`** (essencial p/ língua nova), **`--mask-speaker-ids`** (mascara falantes na loss — o mecanismo multi-turno do §2.2), `--gradient-ckpt`, `--max-audio-length-ms`.
- **Dataset nativamente conversacional**: JSON `list[list[Segment]]` (text, audio_path, speaker_id) — único pipeline com multi-turno de primeira classe (§2.3).
- **Limitação de memória documentada** ([FINETUNING.md](https://github.com/senstella/csm-mlx/blob/master/FINETUNING.md)): sem "compute amortization" → *"might require a ton of RAM for large batch sizes! (Mac Studio recommended)"*. Mitigação: batch pequeno + gradient checkpointing + `--max-audio-length-ms` curto.
- **Não há benchmarks publicados** de tokens/s ou GB exatos de finetune por chip — não verificável; só os dados do caso expressiva acima.

### 4.2 Limitações vs CUDA / qualidade

- TODO do repo: **RoPE incompleto** e sem watermarking; otimização de performance pendente → paridade numérica exata com o checkpoint CUDA não garantida.
- Issues de qualidade: [#21 "voice cloning is not so good"](https://github.com/senstella/csm-mlx/issues/21) (fechada), [#22 "choppy TTS generation"](https://github.com/senstella/csm-mlx/issues/22) (aberta) — inferência streaming tem ressalvas de qualidade.
- [#16 "Training another language"](https://github.com/senstella/csm-mlx/issues/16) (50–500k frases, full vs LoRA): **sem resposta** — ninguém reportou treino de língua completo no MLX.
- Conversão de checkpoints: ida e volta com o formato mainline/Transformers tratada nas issues [#14](https://github.com/senstella/csm-mlx/issues/14) (fechada/completed) e [#23](https://github.com/senstella/csm-mlx/issues/23) → dá para **iterar local e levar o adapter/pesos para o Colab** (e vice-versa), com verificação manual.
- Python <3.13 (sentencepiece).

### 4.3 Inferência/streaming no M2 (RTF)

- README: `generate()` + `stream_generate()` (chunks configuráveis), quantização MLX integrada; afirmação qualitativa: **"nearly real-time on M2 Air" quantizado**. **Nenhum RTF numérico publicado** para M2 — não verificável. (Comparação CUDA: [csm-streaming](https://github.com/davidbrowne17/csm-streaming) reporta RTF 0,28× em RTX 4090.)
- Sinal de maturidade do ecossistema: [Marvis-TTS](https://huggingface.co/Marvis-AI/marvis-tts-250m-v0.2) (arquitetura CSM 250M+60M, [blog](https://huggingface.co/blog/prince-canuma/introducing-marvis-tts)) faz streaming real-time on-device via MLX (~500 MB quantizado) — inferência CSM-style em Apple Silicon é viável em produção.

### 4.4 Veredito para o fluxo do Pedro

**Vale iterar localmente, com papel definido:** M2 24 GB = bancada de **smoke-test** (validar formato do dataset multi-turno, tags de emoção, mask de speaker, 1 época LoRA em 30–60 min, ouvir resultado) usando o csm-mlx — é o único pipeline com multi-turno + mask prontos. Treino sério de língua (pt-BR, dezenas de horas, full-FT ou LoRA r=64 + `--train-embeddings`/embeddings treináveis) → **Colab/CUDA (Unsloth ou knottwill)**, porque (a) ninguém validou treino de língua no MLX, (b) sem amortização de compute a RAM explode com batch real, (c) RoPE incompleto = risco numérico.

---

## 5. Decisões recomendadas (Frente C → plano de treino)

1. **Dados:** mirar ≥20–35 h pt-BR LIMPAS (lição georgiano vs árabe). Common Voice cru não basta — curadoria/filtragem é o multiplicador.
2. **Método:** começar com **LoRA r=64/α=64, LR 5e-5 cosine, ~14 épocas, batch efetivo ~128** (receita georgiana, a única com CER publicado) + comparar com full-FT LR 3e-5 (receita knottwill) num subset. Treinar embeddings em ambos.
3. **Conversacional:** treinar com janelas de 2–4 turnos e loss só no turno-alvo (transformers: `output_labels=True` + mask manual `-100` no contexto; ou csm-mlx `--mask-speaker-ids`). Não há report público disso — documentar como contribuição.
4. **Emoção:** conjunto de tags Orpheus em `<minúsculas>`, inline, dezenas–centenas de exemplos por tag; fillers sempre transcritos. Fonte externa: `laion/laions_got_talent` (Apache 2.0, com asterisco de proveniência OpenAI); anotar o corpus próprio com emotion2vec + BUD-E-Whisper + LLM.
5. **Inferência pós-treino:** lembrar `max_new_tokens` > 125 (senão tudo sai com 10 s).
6. **Local vs Colab:** csm-mlx no M2 só para iteração rápida/smoke-tests e inferência demo; treino final no Colab.

## 6. Fontes primárias (índice)

- Finetunes: https://huggingface.co/models?other=base_model%3Afinetune%3Asesame%2Fcsm-1b · https://huggingface.co/NMikka/CSM-1B-Georgian · https://huggingface.co/MAdel121/Seasmed-Fine-Tuned-on-Common-Voice-17-Arabic · https://huggingface.co/ArttuPakarinen/sesame-csm-FIN-parlament-full-finetune · https://huggingface.co/Nadhari/swa-csm-1b · https://huggingface.co/Mizbaul-Haque-Maruf/csm-bangla-finetuned · https://huggingface.co/nicolajreck/csm-1b-danish-tts
- Pipelines: https://blog.speechmatics.com/sesame-finetune · https://github.com/knottwill/sesame-finetune (issues #3, #4, #5) · https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning · https://github.com/davidbrowne17/csm-streaming · https://huggingface.co/unsloth/csm-1b/discussions/2
- Multi-turno: https://huggingface.co/docs/transformers/en/model_doc/csm (seção Training; `CsmProcessor.__call__` → `output_labels`, `-100/-101`, `depth_decoder_labels_ratio`)
- Emoção: https://huggingface.co/datasets/MrDragonFox/Elise (DMCA) · https://huggingface.co/datasets/MrDragonFox/elise_new_large · https://huggingface.co/datasets/laion/laions_got_talent · https://huggingface.co/laion/BUD-E-Whisper · https://huggingface.co/emotion2vec/emotion2vec_plus_large · https://github.com/canopyai/Orpheus-TTS/blob/main/README.md · https://arxiv.org/pdf/2506.16310 · https://arxiv.org/pdf/2506.09827
- csm-mlx: https://github.com/senstella/csm-mlx (+FINETUNING.md, FINETUNING_CLI.md, issues #14, #16, #21, #22, #23) · https://huggingface.co/senstella/csm-expressiva-1b · https://huggingface.co/blog/prince-canuma/introducing-marvis-tts
