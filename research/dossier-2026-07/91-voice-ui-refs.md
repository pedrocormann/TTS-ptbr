# Refs de UI de agente de voz — pesquisa 02/jul/2026

(pesquisa web pra fundamentar o Voz Lab — tools/voice_ui/voz_lab.html)

## ChatGPT Voice (Advanced Voice Mode)
- 3 gerações: dots pretos (demo 4o) → esfera azul fullscreen set/2024 (blob vidro-fosco, swirl perlin, azul #C9DCFC-#A0B9D1 sobre preto/branco) → 2025-26 "morte do overlay": voz dissolvida no chat (indicador compacto, não um "lugar").
- Estados: idle = pulso lento regular · listening = ondulação assimétrica pela amplitude do usuário · thinking = redemoinho interno sem deformar borda · speaking = deformação da silhueta no ritmo · transições SEMPRE crossfade.

## HER (2013) — OS1/Samantha (verificado)
- Paleta: coral #FA4B12, pêssego #F8A577, vermelho #D41A07, rosa terroso #9F5454, cinza-creme #CFBFB6, vinho #45272F. Azul deliberadamente ELIMINADO da produção.
- Samantha NÃO tem avatar — decisão explícita (anti-uncanny). O único indicador físico: faixa de borda vermelha que acende no cameo phone.
- McFetridge: flatness extrema, "evidência de autoria humana", cor à la Turrell/Rothko (campos verticais).

## ElevenLabs UI (open source — a melhor ref técnica)
- github.com/elevenlabs/ui → orb.tsx: círculo 2D com fragment shader (NÃO é 3D). 7 ovais em espaço polar + 2 sistemas de anéis + rampa preto→cor1→cor2→branco. Cores default #CADCFC/#A0B9D1.
- Estados: null/thinking/listening/talking. Receita de motion QUE FUNCIONA (copiar):
  - idle: sin(t*0.7)*0.07
  - listening: input 0.55+sin(t*3.2)*0.35
  - talking: input 0.65+sin(t*4.8)*0.22 E output 0.75+sin(t*3.6)*0.22 independentes
  - suavização: volume cur+=(target-cur)*0.2 · velocidade lerp 0.12 (resposta quadrática) · CORES lerp 8%/frame ← o segredo do "líquido"

## iOS nativo (quando formos pro app de verdade)
- Protótipo: SwiftUI puro — metasidd/Orb (iOS17+, presets) ou MeshGradient (iOS18) + blur + Circle mask.
- Produção: fragment shader MSL via .colorEffect/.layerEffect + TimelineView(.animation) passando uTime — a técnica ElevenLabs é 2D, não precisa MTKView.
- Áudio: AVAudioEngine.installTap → RMS via vDSP → DOIS canais (inputVolume usuário / outputVolume TTS), suavização exponencial 0.2.
- Glow Siri/Apple Intelligence: jacobamobin/AppleIntelligenceGlowEffect. Acessibilidade: Reduce Motion ⇒ pulso de opacidade sem deformação.

## Direções de identidade (refletidas no Voz Lab)
1. Samantha carioca (HER-first, SEM orb — campo de cor quente + edge glow) → variante PRESENÇA
2. Cristal (ChatGPT-like azul) → variante AURA
3. Tinta viva (fork ElevenLabs, mono+acento) → informou FUNDIÇÃO/NOVATRIX
4. Anti-mascote 2026 (voz dissolvida, shimmering text) → variante PRESENÇA
5. Matéria granular (partículas/grão analógico) → variante TRAMA

Fontes completas no output da pesquisa (sessão 02/jul) — principais: help.openai.com voice FAQ · techcrunch 24/set/2024 · scifiinterfaces.com (série HER) · gizmodo entrevista McFetridge · ui.elevenlabs.io + github.com/elevenlabs/ui · metasidd/Orb · hackingwithswift metal shaders.
