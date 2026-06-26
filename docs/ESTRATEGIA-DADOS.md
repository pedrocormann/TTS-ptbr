# Estratégia de dados em camadas (re-desenho 21/jun/2026)

**Como o público ENSINA português brasileiro SEM POLUIR o dataset limpo carioca.**

## Currículo em 3 camadas de PESOS SEPARADOS + 1 espelho de pesquisa

A regra-mãe: **público e voz NUNCA compartilham o mesmo passo de gradiente.** Não é um pool misturado com filtro de qualidade — é arquitetura de estágios. O público vira *inicialização*, nunca *alvo simultâneo* da voz. Isso é transfer learning canônico (CPT → domain-adapt → speaker-finetune), que já validamos em pequena escala (Estágio A língua / Estágio B voz, spk-sim 0.97).

```
   PRODUTO (pesos shippáveis, lane CC-BY/MIT/CC0)         PESQUISA (descartável)
   ───────────────────────────────────────────           ──────────────────────
C0 BASE-PT — ensina a LÍNGUA                              C0-R  TAGARELA/CORAA
   CML 69h + MLS 161h + CV 187h + Granary(DNSMOS-filt)    (mede TETO do espontâneo,
   multi-locutor, ruído OK, NÃO carioca                    calibra pipeline — pesos
        │ continued-pretrain / CPT-LoRA r64                MORREM aqui, branch research/*)
        ▼
C1 ADAPT-CONV — ensina CONVERSA/espontâneo
   NURC-SP_ENTOA_TTS (se NILC confirmar MIT) + flywheel 2-party
        │ domain-adapt (LR menor, voz condicionada por speaker-id)
        ▼
C2 VOZ-CARIOCA — clona VOZ + sotaque
   SÓ gravação dirigida limpa (Pedro→João/Gui, 1 adapter/voz)
   ZERO público, ZERO TAGARELA, ZERO Granary
        │ LoRA r16 / lr 5e-5 / run curto
        ▼
   CHECKPOINT DE PRODUTO
```

**Onde o TAGARELA "vai entrando":** ele NÃO entra no produto. O "gradual" verdadeiro é Granary/NURC commercial-safe em C0→C1. O TAGARELA vive em C0-R (espelho), papel puramente DIAGNÓSTICO: se 2.800h espontâneas destravam prosódia muito melhor que o ramo de produto, isso QUANTIFICA o valor do espontâneo e justifica investir em coletar espontâneo limpo (flywheel, NURC-confirmado, podcast próprio). Off-accent (MLS PT-eu, NURC SP) vira LÍNGUA/PROSÓDIA, nunca identidade de voz.

## Mecanismo anti-poluição (5 travas, não confiança — CI)

1. **Separação por estágio** — a voz só aparece num finetune posterior, sobre checkpoint congelado. Não há média entre "carioca limpo" e "multi-locutor sujo" porque ocorrem em momentos diferentes.
2. **Tagging obrigatório por clipe (TAGARELA-style, é a herança boa do TAGARELA)** — manifest JSONL com `{clip_id, tier, source, license, speaker_id, clean, dnsmos, accent, shippable, split}`. Um `assert_license_gate()` no data-loader **FALHA O BUILD** se `license=nc-sa` ou `shippable=false` aparecer num split de produto. Assert, não convenção.
3. **Condicionamento de locutor (Kyutai/DSM-style, já decisão travada)** — em C1 público e voz coexistem no dado conversacional, mas amarrados a `spk_public_*` vs `spk_pedro`. O modelo fatora conteúdo/prosódia de identidade; o sotaque do público vive num embedding que a inferência simplesmente não seleciona.
4. **Assimetria de LR/LoRA** — C0 LR de pretrain; C1 LR menor (+freeze parcial do backbone); C2 LoRA r16/lr5e-5/run curto. A baixa capacidade do adapter É uma trava: ele não tem espaço pra reaprender a língua a partir do público (gotcha #6: lr alto/run longo destrói o pt → WER 300%).
5. **Versionamento de proveniência (DVC/git-LFS)** — cada checkpoint registra `{base_ckpt_sha, layer, data_manifest_sha, license_set}`. Um peso de produto SÓ pode ter ancestrais com `license_set ⊆ {cc-by, mit, cc0, próprio}`. Se a árvore incluir SHA de manifest NC → marcado `tainted`, bloqueado pra release. Responde "esse peso viu TAGARELA?" com um comando. 2 ramos: `prod/*` (lane limpa) e `research/*` (TAGARELA-tainted), branch protection rejeita ancestral NC em prod.

## Como TAGARELA entra (lane legal explícita)
- **NÃO** em peso shippável (nem clean-subset).
- **SIM** como: (a) eval-set conversacional (WER/robustez de sotaque — uso permitido do NC), (b) treino do MOS/SER-judge interno (T3, não redistribuído), (c) C0-R diagnóstica, (d) RECEITA de pipeline replicável com componentes MIT/Apache. Isso encerra o ciclo de re-catalogar a mesma licença: está duplamente confirmada (card + site oficial).

## Primeiro passo (fecha o buraco saber→executar)

Criar `data/dataset_registry.yaml` versionado no repo com as colunas do registry acima (dataset, licença-fonte-primária, horas, tier T0-T4, camada, shippable) + um `ingest.py` que recebe um HF id, roda os 4 gates determinísticos (licença → LGPD → qualidade/DNSMOS → fit-de-voz) e cospe o tier — e RODAR essa classificação agora sobre os ~417h já licenciados (CML+MLS+CV) promovendo-os pra manifest T0 de produto, com o `assert_license_gate()` ligado. Esse único movimento transforma 'catalogar' e 'atribuir tier' de passos manuais em PIPE executável, e prova o fechamento do buraco saber-vs-executar entregando o 1º manifest de treino gerado pelo pipe (não pela mão). Agendar em paralelo o CPT do base-pt-v1 sobre esse manifest no pod ocioso quando houver — é dado já legal, não precisa esperar o NILC.
