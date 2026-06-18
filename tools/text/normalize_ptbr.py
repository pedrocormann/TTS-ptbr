#!/usr/bin/env python3
"""
Normalização de texto pt-BR pro front-end do TTS — o PONTO DE INJEÇÃO ÚNICO.

Por quê: o Treino 1 (avaliação do Pedro) mostrou que a LEITURA DE NÚMERO quebra
(hard-01: CEP 22290-160, protocolo 4-7-9, R$ 1.350,90 — 3 trechos graves). O CSM
recebe dígito cru e não sabe ler. Isso NÃO é a voz — é front-end de texto.

Este módulo converte número/CEP/protocolo/moeda/% por extenso ANTES do texto entrar
no modelo (treino E inferência). É o mesmo ponto onde o G2P (fonemizar) vai entrar depois.

Determinístico, sem GPU, testável. Rode `python tools/text/normalize_ptbr.py` pro self-test.
"""
import re

_UNI = ['zero', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove',
        'dez', 'onze', 'doze', 'treze', 'catorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
_DEZ = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
_CEM = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
_SCALE = {2: ('milhão', 'milhões'), 3: ('bilhão', 'bilhões'), 4: ('trilhão', 'trilhões')}


def _ate999(n):
    if n == 0:
        return ''
    if n == 100:
        return 'cem'
    parts = []
    c, d = n // 100, n % 100
    if c:
        parts.append(_CEM[c])
    if d:
        if d < 20:
            parts.append(_UNI[d])
        else:
            dd, u = d // 10, d % 10
            parts.append(_DEZ[dd] + (' e ' + _UNI[u] if u else ''))
    return ' e '.join(parts)


def num_to_words(n):
    """Inteiro → por extenso pt-BR (com as regras de 'e')."""
    n = int(n)
    if n == 0:
        return 'zero'
    neg, n = n < 0, abs(n)
    groups = []
    while n > 0:
        groups.append(n % 1000); n //= 1000   # groups[0]=unidades, [1]=milhares, ...
    chunks = []   # (texto, valor_do_grupo)
    for idx in range(len(groups) - 1, -1, -1):
        v = groups[idx]
        if v == 0:
            continue
        if idx == 0:
            chunks.append((_ate999(v), v))
        elif idx == 1:
            chunks.append(('mil' if v == 1 else _ate999(v) + ' mil', v))
        else:
            sing, plur = _SCALE[idx]
            chunks.append((_ate999(v) + ' ' + (sing if v == 1 else plur), v))
    res = chunks[0][0]
    for k in range(1, len(chunks)):
        text, v = chunks[k]
        last = (k == len(chunks) - 1)
        res += (' e ' if (last and (v < 100 or v % 100 == 0)) else ' ') + text
    return ('menos ' + res) if neg else res


def _spell_digits(s):
    return ', '.join(_UNI[int(d)] for d in s if d.isdigit())


def _currency(m):
    inteiro = int(m.group(1).replace('.', ''))
    cents = m.group(2)
    out = num_to_words(inteiro) + (' real' if inteiro == 1 else ' reais')
    if cents and int(cents) > 0:
        c = int(cents)
        out += ' e ' + num_to_words(c) + (' centavo' if c == 1 else ' centavos')
    return out


def _cep(m):
    return num_to_words(int(m.group(1))) + ', ' + num_to_words(int(m.group(2)))


def _percent(m):
    whole, frac = m.group(1), m.group(2)
    out = num_to_words(int(whole))
    if frac and int(frac) > 0:
        out += ' vírgula ' + _spell_digits(frac)
    return out + ' por cento'


def _decimal(m):
    return num_to_words(int(m.group(1))) + ' vírgula ' + _spell_digits(m.group(2))


def _plain(m):
    s = m.group(0)
    return _spell_digits(s) if len(s) > 6 else num_to_words(int(s))


def normalize_ptbr(text):
    """Aplica as normalizações na ordem certa (estruturadas antes do inteiro solto)."""
    s = text
    s = re.sub(r'R\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{2}))?', _currency, s)          # moeda
    s = re.sub(r'(?<!\d)(\d{5})-(\d{3})(?!\d)', _cep, s)                                # CEP
    s = re.sub(r'(?<![\d-])\d(?:-\d)+(?![\d-])', lambda m: _spell_digits(m.group(0)), s)  # protocolo/código N-N-N
    s = re.sub(r'(\d+)(?:,(\d+))?\s*%', _percent, s)                                    # porcentagem
    s = re.sub(r'(?<!\d)(\d{1,3}(?:\.\d{3})+)(?!\d)', lambda m: num_to_words(int(m.group(1).replace('.', ''))), s)  # milhar com ponto
    s = re.sub(r'(?<!\d)(\d+),(\d+)(?!\d)', _decimal, s)                                # decimal
    s = re.sub(r'(?<!\d)\d+(?!\d)', _plain, s)                                          # inteiro solto
    return s


if __name__ == '__main__':
    casos = [
        ('O CEP é 22290-160, o protocolo termina em 4-7-9, e o repasse é de R$ 1.350,90.',
         'O CEP é vinte e dois mil duzentos e noventa, cento e sessenta, o protocolo termina em quatro, sete, nove, e o repasse é de mil trezentos e cinquenta reais e noventa centavos.'),
        ('Custa R$ 1,00 e o desconto é de 50%.', 'Custa um real e o desconto é de cinquenta por cento.'),
        ('Tinha 100 pessoas e 1000 ingressos.', 'Tinha cem pessoas e mil ingressos.'),
        ('Foram 2.000.000 de votos.', 'Foram dois milhões de votos.'),
        ('A taxa subiu 12,5%.', 'A taxa subiu doze vírgula cinco por cento.'),
    ]
    ok = 0
    for inp, exp in casos:
        got = normalize_ptbr(inp)
        good = got == exp
        ok += good
        print(('✓' if good else '✗'), repr(inp))
        if not good:
            print('   esperado:', exp)
            print('   obtido:  ', got)
    # checagens unitárias de num_to_words
    units = {0: 'zero', 100: 'cem', 101: 'cento e um', 160: 'cento e sessenta', 1000: 'mil',
             1005: 'mil e cinco', 1300: 'mil e trezentos', 1350: 'mil trezentos e cinquenta',
             22290: 'vinte e dois mil duzentos e noventa', 1000000: 'um milhão'}
    ufail = [(n, num_to_words(n), e) for n, e in units.items() if num_to_words(n) != e]
    print(f'\nnum_to_words: {len(units)-len(ufail)}/{len(units)} ok', ('· falhas: ' + str(ufail)) if ufail else '')
    print(f'frases: {ok}/{len(casos)} ok')
