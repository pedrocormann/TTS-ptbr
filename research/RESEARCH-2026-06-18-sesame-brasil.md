# OSINT — Fundações da Sesame + o cria brasileiro → revisão assertiva do plano (18/jun/2026)

Pesquisa via índice Firecrawl (papers+GitHub, sem key) + web. Objetivo: ser mais assertivo nesta rodada.

## Em que a Sesame realmente se baseia (e o que isso nos libera)
A Maya **não é mágica nem modelo gigante**. É o paradigma **codec-LM** (SoundStream/EnCodec → VALL-E → AudioLM → Mimi 12.5Hz → CSM) montado como **CASCATA de engenharia**: VAD silero → ASR incremental → LLM **só-texto** (sglang, com **abort de geração em ~20ms** + JSON constrainado/OUTLINES) → **CSM-1B condicionado em ~2min de áudio-contexto** → watermark silentcipher. O CTO confirmou no podcast a16z (mar/2025): **"even the 1B is very good"** — a escala (3B/8B) compra *long-tail* (homógrafos, consistência), **NÃO naturalidade base**. A emoção deles é **implícita via áudio-contexto**, sem tags.

**Isso valida 3 coisas nossas:** (a) nosso **CSM-1B basta** pra naturalidade (Treino 1: voz 3.4, WER 12%, para 93%) — não escalar backbone antes do Maya-BR v0 validar UX; (b) o **moat não é arquitetura, é dados+engenharia** (replicável, Apache-2.0, zero patentes); (c) o **gap que o próprio CTO admite** (o LLM perde a paralinguística na transcrição) é a nossa **oportunidade futura** (spine áudio-nativo / backbone multimodal), não um problema de agora. Nossa Trilha M **já é exatamente** a cascata deles — o delta é só o orquestrador incremental.

## O que o cria brasileiro ensina (o complemento que a Sesame não dá: DADO + EVAL pt-BR)
- **Frederico/cluster** publicou o **blueprint de COLETA**, não só os dados: pipeline TAGARELA (`arXiv:2603.15326`) = pyannote diarização → overlap detection → bootstrap-ASR → Vocos denoise → ReDimNet+HDBSCAN. **Copiar a ENGENHARIA** (não o dado NC) no flywheel de reuniões UNFLAT.
- **Eval pt-BR tem dono:** **BRSpeechMOS** (`arXiv:2306.09979`, único MOS calibrado pt-BR, Whisper-Small extractor) + **SER pt-BR** (`arXiv:2506.02088`, F0-RMVPE+emotion2vec+BERTimbau). WER **não pega** o "gringo" (Treino 1: 28× marcado, invisível no WER) → a **camada perceptual** é o que mede o gap.
- **Atalho de emoção MORTO e cruzado:** UNESP (`arXiv:2606.05367`, BR) prova que task-vector NÃO controla emoção em TTS-LM. **G2 multi-emoção (5-7h) é o caminho ÚNICO**, por último na fila, sem ilusão.

## A virada assertiva: SOTAQUE DECOMPÕE em dois fatores separáveis
`arXiv:2305.04816` (verificado): sotaque = **(a) FONÉTICO** (resolvível por **G2P front-end** + léxico de ~5k palavras) + **(b) PROSÓDICO** (pitch/duração, **~3min** de fala do sotaque-alvo basta). → **G2P e prosódia-carioca são ARMS SEPARADOS**, não um treino monolítico. Ataque mais **barato e cirúrgico**.
- **G2P disponível JÁ, sem depender do BIPA:** **CharsiuG2P** (ByT5, MIT, HF, inclui pt — `arXiv:2204.03067`) e **LatPhon** (`arXiv:2509.03300`, 3.5% PER, MIT, on-device, inclui pt). O **BIPA-RIO** (2.66% PER, carioca) é o ideal mas **licença/HF NÃO confirmados** → usar CharsiuG2P/LatPhon agora.
- **Fallback** se BIPA falhar (`arXiv:2301.04606`): sotaque low-resource sem frontend dedicado (voice-conversion + frontend de outra variante). De-risca.
- **NURC é trampa de licença CONFIRMADA:** upstream CC-BY-**NC-ND** (`arXiv:2409.15350`, NURC-SP 239h paulistano); o derivado "MIT" do NILC é frágil. **E-mail ao NILC é pré-requisito** antes de qualquer peso shippável com NURC. Sem isso, "Estágio A carioca" = **ablação de proporção**, não NURC.
- **Dado carioca commercial-safe ≈ 0h aberto** → o **flywheel** (Pedro+João carioca + Guilherme paulista) é a única fonte legal + dá o contraste **carioca×paulista** pra tag de sotaque v1.

## Ajustes ASSERTIVOS no plano desta rodada
1. **[alta] Curar PRIMEIRO** (`curate_app`) — único bloqueador 100% nosso, sem GPU. Sem `transcribed_clean.jsonl`, todo arm fica contaminado (Whisper ~5-10% + fragmentos).
2. **[alta] Desbloquear o sprint do sotaque JÁ** — B2-limpo + B2-G2P + ablação de proporção (**~9h ≈ $30 H100 / $14 A100**), sem esperar NURC nem G2.
3. **[alta] G2P com CharsiuG2P/LatPhon** (não bloquear no BIPA) + tratar **G2P (fonético) e prosódia-carioca como 2 arms**.
4. **[alta] NURC rebaixado** a "bloqueado-até-NILC"; **proporção promovida** (30/70, 50/50, 100% Pedro) como o arm de sotaque desta rodada — testa barato "base CML formal domina o carioca" (transferiu só 2/14).
5. **[media] enrich_markers/GOP offline** (MFA/CTC + GOP L1-aware `arXiv:2309.07719`) sobre os áudios do Treino 1 **antes** do próximo treino — CPU, custo zero. Vira "soa gringo" (global) em fonema-errado-no-tempo.
6. **[media] Eval camada perceptual** antes do próximo gate: **BRSpeechMOS** (treinar o nosso) + **BIPA** (pronúncia dialetal). Manter spk-sim≥0.70 + WER como gates, mas **NÃO decidir sotaque por WER**.
7. **[alta] G2 por último**, ao gravar copiar taxonomia LibriQuote/EARS + rótulo em 3 camadas; **nenhum atalho** (refutado).
8. **[media] Trilha B (Moshi): não tocar** esta rodada (aposta de médio prazo, depende do flywheel). Avaliar **SoulX-Duplug** (`arXiv:2603.14877`) só quando o Maya-BR v0 (cascata) estiver montado.

## Citações-chave
Sesame CSM blog "Crossing the Uncanny Valley of Voice" + repo `SesameAILabs/csm` (Apache-2.0) · a16z podcast (CTO, cascata + "1B is very good" + gap paralinguística) · Moshi/Mimi `arXiv:2410.00037`; J-Moshi `arXiv:2506.02979` · UNESP emoção `arXiv:2606.05367` · TAGARELA `arXiv:2603.15326`; CML-TTS `arXiv:2306.10097`; CORAA `arXiv:2110.15731`; SER `arXiv:2506.02088`; BRSpeechMOS `arXiv:2306.09979`; NURC-SP `arXiv:2409.15350` · Accent: `2410.14997` (G2P+GT sintético), `2305.04816` (decompõe fonético+prosódico), `2301.04606` (fallback sem frontend) · G2P: CharsiuG2P `2204.03067`, LatPhon `2509.03300` · MDD/GOP `2309.07719`, `2507.16838` · BIPA-RIO (PROPOR 2026, licença não-confirmada).
