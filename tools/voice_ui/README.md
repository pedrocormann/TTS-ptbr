# Voz Lab v2 — laboratório de identidade visual do agente de voz

`voz_lab.html` — arquivo único, self-contained (Pepi embutida, zero deps, WebGL2).
**6 famílias × 4 variações** (I · II · III · BR) = 24 combinações. Regras da rodada 02/jul:
**zero giro · nada rápido demais · cada família tem uma variação nas cores do Brasil**
(anil #2A4DA8 · verde bandeira #009E3D · canarinho #FFDB1A).

## Rodar

```bash
cd tools/voice_ui && python3 -m http.server 8765
# http://localhost:8765/voz_lab.html  (mic exige https ou localhost)
```

## Controles

- **deslizar horizontal / setas / dots** — troca de FAMÍLIA
- **chips sob o nome / deslizar vertical / ↑↓** — troca de VARIAÇÃO (cores fazem crossfade 8%/frame)
- **toque no nome** — conceito + notas das variações · **pills/1-4** — estados · **MIC**/**DEMO**

## As 6 famílias

| Família | O que é | Variações |
|---|---|---|
| **AURA** | círculo de borda REDONDA, nuvens lentas dentro, glitch contido nos ataques | gelo · prata · petróleo · **canarinho** (um sol) |
| **TRAMA** | tecido de pixels Bayer 8×8 respirando — sem cara de olho, sem pressa | tinta · ciano · âmbar · **bandeira** (verde→canarinho na fala) |
| **FUNDIÇÃO** | metal líquido escorrendo devagar, eixo fixo, veios fundidos na fala | cromo · ouro · cobre · **verde-ouro** |
| **NOVATRIX** | malha de gradiente DOMADA (5 iterações, tempo 40%, mistura suave — sem flicker) | unflat · pêssego · oceano · **bandeira** (anil/verde/amarelo) |
| **ESPECTRO** | aurora boreal: cortinas verticais ondulando devagar | boreal · austral · espectral (arco-íris físico lento) · **verde-amarela** |
| **BRUMA** | GPT fiel, água & fumaça com ZOOM (nuvens grandes) | gpt · zoom+ · grafite · **anil** |

Removidas nesta rodada (vivem no git): SAMANTHA, PRESENÇA, VIDRO.

## Movimento (regras)

Sem rotação em nenhuma família — "pensando" agora é: deriva mais funda / warp / respiração
longa, nunca giro. Velocidades ~40-60% da v1. Valores que ficam: idle `sin(t·0.7)·0.07`,
falando duas senoides 4.8/3.6 Hz (BRUMA), suavização de nível 0.2, cores lerp 8%/frame.
Refs: research/dossier-2026-07/91-voice-ui-refs.md · caminho iOS nativo (SwiftUI+Metal) idem.

## Estender

Família nova = 1 fragment shader (uniforms u_c1/u_c2/u_c3 + u_p1/u_p2) + entrada em
FAMILIES[] com `vars:[{k,accent,c1,c2,c3,p1,p2,note}]`. Variação nova = só dados.
