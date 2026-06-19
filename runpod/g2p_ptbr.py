#!/usr/bin/env python3
"""G2P pt-BR via CharsiuG2P (ByT5 multilíngue, licença MIT, inclui português).

Front-end FONÉTICO do sotaque (arXiv:2305.04816 decompõe sotaque em fonético+prosódico;
o fonético é resolvível por G2P + léxico). Converte grafema → IPA, palavra-a-palavra,
preservando pontuação. Usado como `g2p=phonemize` em recipe.text_frontend.

⚠️ EXPERIMENTAL: o CSM-1B é um LM de GRAFEMA pré-treinado; alimentá-lo com IPA é um
domain-shift. Por isso o arm G2P roda POR ÚLTIMO no grid e SÓ depois do smoke-test
(self_test() abaixo) confirmar que a tag de língua produz IPA plausível.

Modelo: charsiu/g2p_multilingual_byT5_tiny_16_layers_100 (HF). Formato de entrada do
CharsiuG2P: "<{lang}>: {palavra}". Tag pt-BR via env G2P_LANG (default 'por-bz';
fallback 'por'). Cache por palavra (memoiza — o benchmark/treino repete muita palavra).
"""
import os
import re
import functools

_MODEL = None
_TOK = None
_LANG = os.environ.get('G2P_LANG', 'por-bz')
_HF_ID = os.environ.get('G2P_MODEL', 'charsiu/g2p_multilingual_byT5_tiny_16_layers_100')

# token = run de letras (inclui acentos/ç) OU um não-letra qualquer (pontuação/espaço/dígito).
# Só as runs de letras vão pro G2P; o resto passa intacto (números já viraram palavra no normalize).
_TOKEN_RE = re.compile(r"[^\W\d_]+|[^\w\s]+|\s+", re.UNICODE)


def _load():
    global _MODEL, _TOK
    if _MODEL is None:
        import torch
        from transformers import T5ForConditionalGeneration, AutoTokenizer
        _TOK = AutoTokenizer.from_pretrained(_HF_ID)
        _MODEL = T5ForConditionalGeneration.from_pretrained(_HF_ID)
        _MODEL.eval()
        if torch.cuda.is_available():
            _MODEL = _MODEL.to('cuda')
    return _MODEL, _TOK


@functools.lru_cache(maxsize=50000)
def _phon_word(word: str) -> str:
    """Fonemiza UMA palavra (minúscula) → IPA. Cacheado. Fallback = a própria palavra."""
    import torch
    model, tok = _load()
    inp = tok([f"<{_LANG}>: {word}"], return_tensors='pt', padding=True)
    if torch.cuda.is_available():
        inp = {k: v.to('cuda') for k, v in inp.items()}
    with torch.no_grad():
        out = model.generate(**inp, num_beams=1, max_length=64)
    ipa = tok.batch_decode(out, skip_special_tokens=True)[0].strip()
    return ipa or word


def phonemize(text: str) -> str:
    """Grafema → string de IPA, preservando pontuação/espaços. Robusto: nunca levanta."""
    if not text:
        return text
    try:
        _load()
    except Exception:
        return text   # sem modelo → devolve grafema (o caller já loga o fallback)
    out = []
    for tokn in _TOKEN_RE.findall(text):
        if tokn[:1].isalpha() or (tokn and tokn[0] not in ' \t\n' and not tokn[0].isascii() and tokn.isalpha()):
            try:
                out.append(_phon_word(tokn.lower()))
            except Exception:
                out.append(tokn)
        else:
            out.append(tokn)   # pontuação / espaço — intacto
    return ''.join(out)


def self_test() -> dict:
    """Smoke-test: fonemiza palavras conhecidas; retorna dict pra inspeção ANTES de treinar.
    Critério de sanidade: o IPA difere do grafema e contém símbolos fonéticos (não-ascii)."""
    samples = ['praia', 'coração', 'gente', 'carioca', 'água']
    res = {}
    ok = 0
    for w in samples:
        try:
            ipa = _phon_word(w)
        except Exception as e:
            ipa = f'ERRO: {e}'
        res[w] = ipa
        if isinstance(ipa, str) and ipa != w and any(ord(c) > 127 for c in ipa):
            ok += 1
    res['_lang'] = _LANG
    res['_model'] = _HF_ID
    res['_plausivel'] = f'{ok}/{len(samples)}'
    return res


if __name__ == '__main__':
    import json
    print(json.dumps(self_test(), ensure_ascii=False, indent=2))
    print('frase:', phonemize('Eu tô indo pra praia, parça! Custou 30 reais.'))
