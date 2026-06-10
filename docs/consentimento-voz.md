# Termo de Consentimento — Uso de Voz para Treinamento de IA (MINUTA)

> ⚠️ **MINUTA de trabalho (2026-06-10) — NÃO usar sem revisão de advogado**
> (LGPD art. 5º/7º/11; voz = dado pessoal e biométrico = sensível; PL 1460/2026
> em tramitação exige consentimento prévio + watermark para réplicas de voz).
> Uma via assinada por pessoa, guardada no registro privado do projeto
> (PARKING-LOT: item “consent-artifact + provenance-log”, dossiê 70 §B).

---

## Termo de Consentimento Livre, Esclarecido e Informado

**Titular:** ______________________________________ CPF: ________________

**Controladora:** UNFLAT (Pedro Cormann), e-mail oi@unflat.studio

### 1. O que será coletado
Gravações da minha voz em: (a) reuniões de trabalho da UNFLAT (canal de
microfone individual), (b) sessões dirigidas de gravação (leituras, emoções,
conversas), no período de ____/____/______ a ____/____/______ (renovável).

### 2. Finalidade
Treinamento, avaliação e demonstração de modelos de síntese e conversação de
voz desenvolvidos pelo projeto TTS-ptbr, incluindo a criação de vozes
sintéticas derivadas da minha voz.

### 3. Direitos que EU mantenho
- **Revogação a qualquer tempo** (efeito: minhas gravações saem dos datasets e
  novas versões de modelos não usarão minha voz; versões já treinadas serão
  descontinuadas em até 90 dias).
- Acesso, cópia e eliminação dos meus dados (LGPD art. 18).
- Minha voz sintética **não** será usada em conteúdo difamatório, político,
  erótico ou enganoso, nem licenciada a terceiros **sem novo consentimento
  específico e por escrito**.

### 4. Compromissos da controladora
- Áudio bruto e modelos derivados em **registro privado** (não publicados).
- **Marca d'água/identificação** em todo áudio sintético gerado com minha voz.
- Registro de proveniência (que gravação treinou qual modelo).
- Em uso comercial da minha voz sintética, condições de remuneração serão
  acordadas em instrumento separado ANTES do uso: ______________________.

### 5. Assinaturas
Titular: ______________________ Data: ____/____/______
Controladora: __________________ Data: ____/____/______

---

**Checklist operacional (por pessoa, antes da 1ª gravação):**
- [ ] Termo assinado e arquivado (PDF no registro privado)
- [ ] Linha no `docs/consent-log.jsonl`: `{"who": "...", "signed": "YYYY-MM-DD", "scope": "reunioes+dirigidas", "doc": "caminho.pdf"}`
- [ ] Combinar sinal de “off the record” nas reuniões (trecho é apagado no QC)
