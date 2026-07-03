# Voz Lab — laboratório de identidade visual do agente de voz

`voz_lab.html` — arquivo único, self-contained (Pepi embutida, zero deps, WebGL2).
**4 famílias** sobreviventes da curadoria do Pedro (03/jul), cada uma com variações de
cor/temperamento. Regras: zero giro global · nada rápido demais · cores do Brasil presentes.

## Rodar

```bash
cd tools/voice_ui && python3 -m http.server 8765   # http://localhost:8765/voz_lab.html
```
No app: aba **Agente** (local `/agente` · site `/tts-ptbr/agente`, com mic).

## As 4 famílias

| Família | O que é | Variações |
|---|---|---|
| **TRAMA** | nuvens ORGÂNICAS de pixel Bayer 8×8 derivando (sem linhas — nada de spotify; sem olho) | tinta · âmbar · **bandeira** |
| **FUNDIÇÃO** | metal líquido escorrendo devagar, veios fundidos na fala | cromo · ouro · cobre · **verde-ouro** |
| **NOVATRIX** | malha de gradiente domada (sem flicker) | oceano · **bandeira** (anil/verde/amarelo) |
| **BRUMA** ★ | fluido de DUAS FASES do vídeo real do GPT (Studio Dumbar, 20fps): slosh lateral, microgiros (vórtices locais que giram e voltam), rotas serpenteando, núcleo quente, pluma; círculo NUNCA deforma; temperamento vivo↔calmo por variação | **anil** (default) · gpt · laranja · jade · lilás · rosa · grafite · **anil//glitch** (rasga na malha novatrix nos ataques) |

Mortas na curadoria (git guarda): AURA, SAMANTHA, ESPECTRO, PRESENÇA, VIDRO + variações ciano/unflat/pêssego.

## Motor

- Estados repouso/ouvindo/pensando/falando (pills, teclas 1-4) · MIC real · DEMO (ciclo simulado)
- Família = fragment shader; variação = DADOS (paleta u_c1-3 + params u_p1-3, lerp 8%/frame)
- `u_flow` = relógio de fluido acumulado (acelera com a voz, sem salto) — a animação vive no fluido
- BRUMA p1=zoom · p2=temperamento (vivo↔calmo, conceito do vídeo Dumbar: cada voz GPT = mesmo
  shader, outros parâmetros) · p3=rigidez do círculo (>1 = +glitch novatrix)
- Análises-fonte: research/dossier-2026-07/91-voice-ui-refs.md + frames 12/20fps no scratchpad
