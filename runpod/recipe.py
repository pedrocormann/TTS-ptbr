#!/usr/bin/env python3
"""
RECEITA VALIDADA + GUARDRAILS do TTS pt-BR — os aprendizados codificados.

Importe daqui em QUALQUER experimento novo pra (a) reusar a config que funcionou e
(b) bater nos guardrails que impedem repetir os erros caros da jornada.

Aprendizados embutidos (Treino 1 + jornada 15-16/jun):
- warmup time-capped: use warmup_steps INT fixo (=20), NUNCA ratio — senão LR≈0 e não aprende.
- EOS: o stop real é o frame [0]×32 (codebook_eos). Supervisione com label 0 (não 128003) — senão balbucia.
- áudio REAL (sem zero-pad a 12s) + collator por-batch — senão aprende a "encher 12s".
- Estágio B overfitta fácil (272 clipes): LR baixo (5e-5) + run curto. LR 2e-4 deu WER 300%.
- streaming decode=False + filtro ≤12s; max_text_len 384 (texto longo trunca o áudio → crash).
- Treino 1: a VOZ está provada (não mexer). O gap é SOTAQUE (gringo #1) + NÚMERO + PROSÓDIA.
  → normalizar número (text_frontend) é quick-win; G2P/fonema e base carioca são as alavancas do 'soa nativo'.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.text.normalize_ptbr import normalize_ptbr   # noqa: E402

# ---------- Receita validada (não chutar; foi medida) ----------
STAGE_A = dict(stage='A', lr=5e-4, minutes=180, warmup_steps=20, lora_r=64, lora_alpha=64,
               lr_scheduler='cosine', optim='adamw_8bit', bf16=True,
               max_audio_s=12, max_text_len=384, eos_fix=True, real_audio=True,
               clip_filter=dict(dur_min=1.5, dur_max=12, words_min=3),
               note='base pt: CML → WER 21% (cml_long, vencedor da bateria)')

STAGE_B = dict(stage='B', lr=5e-5, minutes=60, warmup_steps=20, lora_r=64, lora_alpha=64,
               lr_scheduler='cosine', optim='adamw_8bit', bf16=True,
               max_audio_s=12, max_text_len=384, eos_fix=True, real_audio=True,
               clip_filter=dict(dur_min=1.0, dur_max=12, words_min=3),
               note='voz do Pedro sobre a base pt: stage_b_final → WER 12-17%, para 14/14')


def check_config(cfg):
    """Guardrails — aborta cedo se a config repete um erro conhecido. Rode ANTES de gastar GPU."""
    s = cfg.get('stage', '?')
    assert isinstance(cfg.get('warmup_steps'), int) and not isinstance(cfg.get('warmup_steps'), bool), \
        "warmup_steps tem que ser INT fixo (ex.: 20), NUNCA ratio — em run time-capped o LR vira ~0 e não aprende."
    assert cfg.get('eos_fix') is True, \
        "eos_fix obrigatório: label do <|audio_eos|> = 0 (frame de parada [0]×32). Sem isso, balbucia (0/14 param)."
    assert cfg.get('real_audio') is True, \
        "real_audio obrigatório (sem zero-pad a 12s) — senão o modelo aprende a 'encher 12s'."
    assert cfg.get('max_text_len', 0) >= 256, "max_text_len baixo trunca o áudio em texto longo → shape mismatch."
    if s == 'B':
        assert cfg.get('lr', 1) <= 1e-4, \
            f"Estágio B com LR {cfg.get('lr')} alto demais → overfit (lição: 2e-4 deu WER 300%). Use 5e-5."
    return True


def text_frontend(text, normalize_numbers=True, g2p=None):
    """PONTO DE INJEÇÃO ÚNICO do texto — use no treino (build_prep) E na inferência do benchmark,
    pro mesmo texto que o modelo viu treinando ser o que ele vê gerando.

    normalize_numbers: conserta CEP/moeda/número/% por extenso (achado #1 do Treino 1).
    g2p: callable opcional (fonemizar a entrada) — a alavanca SOTA contra o 'sotaque gringo'.
         passe o g2p endurecido aqui pra rodar o ramo de ablação 'G2P' do roadmap.
    """
    s = str(text).strip()
    if normalize_numbers:
        s = normalize_ptbr(s)
    if g2p is not None:
        s = g2p(s)
    return s


if __name__ == '__main__':
    # smoke-test dos guardrails + do front-end
    check_config(STAGE_A); check_config(STAGE_B)
    print('✓ guardrails passam nas receitas validadas (A e B)')
    bad = dict(STAGE_B); bad['lr'] = 2e-4
    try:
        check_config(bad); print('✗ guardrail de overfit NÃO pegou LR alto')
    except AssertionError as e:
        print('✓ guardrail pegou LR alto no Estágio B:', str(e)[:60], '…')
    ex = 'O CEP é 22290-160 e custa R$ 1.350,90.'
    print('text_frontend:', repr(text_frontend(ex)))
