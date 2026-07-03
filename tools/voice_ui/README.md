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
| **BRUMA** ★ | fluido de DUAS FASES do vídeo real do GPT (Studio Dumbar, 20fps): slosh lateral, microgiros (vórtices locais que giram e voltam), rotas serpenteando, núcleo quente, pluma, SUSTOS; círculo NUNCA deforma; temperamento vivo↔calmo por variação | **anil** (default) · gpt · jade · grafite · **anil//grão** · gpt//grão (granulado colorDodge do novatrix) |

Mortas na curadoria (git guarda): AURA, SAMANTHA, ESPECTRO, PRESENÇA, VIDRO + variações
ciano/unflat/pêssego + bruma laranja/lilás/rosa + o glitch RGB (Pedro: "glitch" = granulado).

## Motor

- Estados repouso/ouvindo/pensando/falando (pills, teclas 1-4) · MIC real · DEMO (ciclo simulado)
- Família = fragment shader; variação = DADOS (paleta u_c1-3 + params u_p1-3, lerp 8%/frame)
- `u_flow` = relógio de fluido acumulado (acelera com a voz, sem salto) — a animação vive no fluido
- `u_kick` = SUSTO: dardo direcional repentino (do vídeo real: dedo brilhante dispara na diagonal
  em ~250ms e assenta em ~1s). JS `kick()` dispara em onsets de fala + timers estocásticos por
  estado; envelope `exp(-t/.25)*.8+exp(-t/.9)*.25`. No shader, desloca a advecção com peso
  central, o núcleo quente pula junto e a pluma alinha na direção do dardo.
  As 4 famílias reagem ao kick (TRAMA/FUNDIÇÃO/NOVATRIX via coords do noise).
- `u_spin` = GIRO-susto: um ou outro susto vem como REDEMOINHO largo transiente (sobe ~140ms,
  reassenta no tau do estado; sentido ALTERNA — nunca vira rotação contínua). No PENSANDO o giro
  lento É o susto padrão (dardo quase nulo, tau 1.4s, um termina antes do outro) e o slosh
  lateral acalma → assinatura própria do estado. REPOUSO = bem parado: zero sustos e relógio
  de fluido quase congelado (0.13 vs 0.32).
- BRUMA p1=zoom · p2=temperamento (vivo↔calmo, conceito do vídeo Dumbar: cada voz GPT = mesmo
  shader, outros parâmetros) · p3=rigidez do círculo (>1 = +granulado colorDodge)
- Análises-fonte: research/dossier-2026-07/91-voice-ui-refs.md + frames 12/20fps no scratchpad
