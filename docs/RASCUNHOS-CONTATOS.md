# Rascunhos de contato — colaborações BR (02/jul/2026)

> Gerados a partir da pesquisa verificada (research/dossier-2026-07/80). Revisar, ajustar o tom
> e enviar. Os dois ganchos são trocas concretas, não pedido de favor.

---

## 1. Frederico Oliveira (UFMT/AKCIT-UFG) — TAGARELA

**Para**: fred.santos.oliveira@gmail.com (checar no site fredso.com.br / HF freds0)
**Assunto**: TAGARELA — subset carioca + troca: eval perceptual carioca

Oi Frederico,

sou o Pedro, da Unflat Studio (RJ). A gente está construindo uma voz conversacional pt-BR
com sotaque carioca — gravamos nosso próprio dataset dirigido (voz-semente carioca curada,
com consentimento LGPD) e mantemos um cockpit de avaliação perceptual (notas humanas de
"soa carioca", marcadores de prosódia no tempo, WER decomposto).

Acompanho o TAGARELA desde o release (parabéns pelo ICASSP!) e vi que o corpus tem rótulo
de dialeto. Duas perguntas + uma troca:

1. O classificador de dialeto/sotaque que vocês usaram está disponível (checkpoint ou código)?
   Queremos minerar um subset carioca do TAGARELA pra experimentos (uso estritamente de
   pesquisa, dentro da CC-BY-NC-SA).
2. Os modelos TTS treinados no TAGARELA que estão "coming soon" têm previsão? Adoraríamos
   usar como baseline.

Em troca, oferecemos: (a) nossa bateria de avaliação perceptual carioca (n humano real, cego)
rodada nos modelos de vocês, com relatório; (b) nossa voz-semente carioca curada como test set
de sotaque, se for útil pra validar o classificador. Se fizer sentido algo mais formal, a
Unflat topa conversar sobre o caminho EMBRAPII.

Abraço,
Pedro

---

## 2. Grupo Aluísio (NILC/USP) — via Julio Galdino

**Para**: juliogaldino@usp.br, cc sandra@icmc.usp.br
**Assunto**: Implementamos a segmentação prosódica de vocês num pipeline TTS carioca — resultados + proposta

Oi Julio (cc profa. Sandra),

sou o Pedro, da Unflat Studio (RJ). Estamos construindo TTS conversacional pt-BR carioca com
dataset próprio, e o trabalho de vocês virou peça central do nosso pipeline:

- Implementamos re-pontuação prosódica pós-Whisper (pausa ≥300ms como sinal dominante, como
  no PROPOR 2024; F0 pra terminal/continuação; fillers preservados com a lista do NURC) e
  segmentação só em fronteira terminal, espelhando o config `prosodic` do ENTOA_TTS.
- Rodamos também uma versão do scorecard acústico do "robótico" (taxa de fala, sílaba nuclear,
  SD, pausas — na linha do ENIAC 2024) comparando nossos treinos vs a voz natural: os sintéticos
  mostram exatamente a assinatura que vocês descrevem (menos pausa, ritmo achatado).
- Próximo passo: A/B de treino (mesma receita, texto prosódico vs gramatical) num CSM-1B
  adaptado pra pt-BR — a versão "no nosso modelo" do resultado de vocês no BRACIS 2025.

Três coisas que talvez interessem a vocês:
1. Compartilhamos os resultados do A/B assim que rodarem (relatório + amostras).
2. Nosso dado é fala carioca espontânea dirigida com consentimento — nenhum corpus do TaRSila
   cobre essa variedade; se servir como test set externo pra prosódia/dialeto, é de vocês.
3. O buraco que o review de vocês aponta (eval perceptual de prosódia desenhada pra prosódia)
   é exatamente o que precisamos construir — teria interesse em co-desenhar esse protocolo
   (na variedade carioca) com a gente como estudo de caso? Também nos interessa muito a linha
   PSST (Whisper emitindo fronteira de IU) em pt-BR.

Uma dúvida de registro: o card do ENTOA_TTS no HF diz MIT, mas o paper menciona CC-BY-NC-ND —
qual vale? (Pra sabermos o que podemos fazer além de pesquisa.)

Abraço,
Pedro

---

## 3. (Opcional, mais tarde) Arnaldo Candido Jr (UNESP)

Gancho: replicar o paper 2026 de fine-tuning emocional pt-BR (YourTTS, poucos dados) na voz
do Pedro (~$5 de GPU na nossa esteira) e mandar os resultados com divergências + proposta de
experimento conjunto "expressividade com sotaque carioca". Escrever só depois de ter o
replicado rodado — o e-mail forte é o que chega com resultado anexo.
