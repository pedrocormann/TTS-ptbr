#!/usr/bin/env python3
"""G2P regra-baseado para português brasileiro (sabor carioca) — para ANÁLISE DE COBERTURA.

Não é um G2P de produção: aproxima o suficiente para medir cobertura fonética de
scripts de gravação (quais fones aparecem, quais faltam, frequências). Vogais
médias abertas/fechadas sem acento gráfico não são desambiguadas (precisaria de
léxico); marcamos como arquifonema E/O quando ambíguo.

Fones usados (aprox. SAMPA-BR adaptado):
  vogais:   a ɐ e ɛ E i o ɔ O u  | nasais: ã ẽ ĩ õ ũ
  ditongos: aj ej ɛj oj ɔj uj aw ew ɛw iw ow ãw̃ ãj̃ õj̃ ũj̃
  consoantes: p b t d k g f v s z ʃ ʒ m n ɲ l ʎ ɾ χ w j tʃ dʒ
Traços cariocas modelados: coda /s/→ʃ (ʒ antes de voz.), coda /r/→χ, /t d/+[i]→tʃ dʒ,
coda /l/→w, redução de e/o átonos finais →i/u.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

VOWELS = "aáàâãeéêiíoóôõuúü"
VOICED_ONSET = set("bdgvzjmnlrwãõáàâéêíóôú" + "aeiou")

# fones do inventário-alvo (para relatório de cobertura)
TARGET_PHONES = [
    "a", "ɐ", "e", "ɛ", "i", "o", "ɔ", "u",
    "ã", "ẽ", "ĩ", "õ", "ũ",
    "aj", "ej", "ɛj", "oj", "ɔj", "uj", "aw", "ew", "iw", "ow",
    "ãw̃", "ãj̃", "õj̃",
    "p", "b", "t", "d", "k", "g", "tʃ", "dʒ",
    "f", "v", "s", "z", "ʃ", "ʒ",
    "m", "n", "ɲ", "l", "ʎ", "ɾ", "χ", "w", "j",
]

_PUNCT_RE = re.compile(r"[^\wáàâãéêíóôõúüç\- ]", re.UNICODE)
_DIGIT_RE = re.compile(r"\d")


def has_digits(text: str) -> bool:
    """Scripts de gravação devem trazer números por extenso."""
    return bool(_DIGIT_RE.search(text))


def normalize(text: str) -> list[str]:
    text = text.lower().replace("-", " ")
    text = _PUNCT_RE.sub(" ", text)
    return [w for w in text.split() if w]


def _is_vowel(ch: str) -> bool:
    return ch in VOWELS


def word_to_phones(word: str) -> list[str]:
    """Transcreve uma palavra ortográfica em lista de fones (aproximação carioca)."""
    w = word
    phones: list[str] = []
    i = 0
    n = len(w)

    def nxt(k: int = 1) -> str:
        return w[i + k] if i + k < n else ""

    def prv() -> str:
        return w[i - 1] if i > 0 else ""

    while i < n:
        c = w[i]
        c2 = w[i : i + 2]

        # --- dígrafos consonantais ---
        if c2 == "ch":
            phones.append("ʃ"); i += 2; continue
        if c2 == "lh":
            phones.append("ʎ"); i += 2; continue
        if c2 == "nh":
            phones.append("ɲ"); i += 2; continue
        if c2 == "rr":
            phones.append("χ"); i += 2; continue
        if c2 == "ss":
            phones.append("s"); i += 2; continue
        if c2 in ("sc", "sç") and nxt(2) in "eéêií":
            phones.append("s"); i += 2; continue
        if c2 == "xc" and nxt(2) in "eéêií":
            phones.append("s"); i += 2; continue
        if c2 == "qu":
            if nxt(2) in "eéêiíè":
                phones.append("k"); i += 2; continue
            phones.append("k"); phones.append("w"); i += 2; continue
        if c2 == "gu" and nxt(2) in "eéêií":
            phones.append("g"); i += 2; continue

        # --- nasalização Vm/Vn em coda ---
        if _is_vowel(c) and nxt() in "mn" and (i + 2 >= n or not _is_vowel(nxt(2))):
            base = unicodedata.normalize("NFD", c)[0]
            nas = {"a": "ã", "e": "ẽ", "i": "ĩ", "o": "õ", "u": "ũ"}.get(base, "ã")
            # ditongo nasal final -am/-em ("falam"→ãw̃, "também"→ẽj̃→aprox ãj̃)
            if i + 2 >= n and nxt() == "m":
                if base == "a":
                    phones.append("ãw̃"); i += 2; continue
                if base == "e":
                    phones.append("ãj̃"); i += 2; continue
            phones.append(nas)
            i += 2
            continue

        # --- vogais nasais com til e ditongos nasais ---
        if c == "ã":
            if nxt() == "o":
                phones.append("ãw̃"); i += 2; continue
            if nxt() == "e":
                phones.append("ãj̃"); i += 2; continue
            phones.append("ã"); i += 1; continue
        if c == "õ":
            if nxt() == "e":
                phones.append("õj̃"); i += 2; continue
            phones.append("õ"); i += 1; continue

        # --- ditongos orais decrescentes ---
        if _is_vowel(c) and nxt() in "iu" and c not in "iu":
            v1 = {"á": "a", "à": "a", "â": "ɐ", "é": "ɛ", "ê": "e",
                  "ó": "ɔ", "ô": "o", "a": "a", "e": "e", "o": "o"}.get(c, c)
            glide = "j" if nxt() == "i" else "w"
            phones.append(v1 + glide)
            i += 2
            continue
        if c == "i" and nxt() == "u":
            phones.append("iw"); i += 2; continue
        if c == "u" and nxt() == "i":
            phones.append("uj"); i += 2; continue

        # --- vogais simples ---
        if c in "aáà":
            phones.append("a"); i += 1; continue
        if c == "â":
            phones.append("ɐ"); i += 1; continue
        if c == "é":
            phones.append("ɛ"); i += 1; continue
        if c in "eê":
            # redução átona final: e→i (carioca)
            if c == "e" and i == n - 1 and n > 1:
                phones.append("i")
            else:
                phones.append("e")
            i += 1
            continue
        if c in "ií":
            phones.append("i"); i += 1; continue
        if c == "ó":
            phones.append("ɔ"); i += 1; continue
        if c in "oô":
            if c == "o" and i == n - 1 and n > 1:
                phones.append("u")
            else:
                phones.append("o")
            i += 1
            continue
        if c in "uúü":
            phones.append("u"); i += 1; continue

        # --- consoantes sensíveis a contexto ---
        if c == "t":
            if nxt() in "ií" or (nxt() == "e" and i + 1 == n - 1):
                phones.append("tʃ")
            else:
                phones.append("t")
            i += 1
            continue
        if c == "d":
            if nxt() in "ií" or (nxt() == "e" and i + 1 == n - 1):
                phones.append("dʒ")
            else:
                phones.append("d")
            i += 1
            continue
        if c == "c":
            phones.append("s" if nxt() in "eéêiíè" else "k"); i += 1; continue
        if c == "ç":
            phones.append("s"); i += 1; continue
        if c == "g":
            phones.append("ʒ" if nxt() in "eéêií" else "g"); i += 1; continue
        if c == "j":
            phones.append("ʒ"); i += 1; continue
        if c == "s":
            if _is_vowel(prv()) and _is_vowel(nxt()):
                phones.append("z")          # intervocálico
            elif nxt() == "" or not _is_vowel(nxt()):
                # coda: chiado carioca; sonoriza antes de consoante sonora
                phones.append("ʒ" if (nxt() and nxt() in VOICED_ONSET and not _is_vowel(nxt())) else "ʃ")
            else:
                phones.append("s")
            i += 1
            continue
        if c == "z":
            if nxt() == "" :
                phones.append("ʃ")          # coda final: "paz" → paʃ
            else:
                phones.append("z")
            i += 1
            continue
        if c == "x":
            if i == 0:
                phones.append("ʃ")
            elif prv() == "e" and i == 1 and _is_vowel(nxt()):
                phones.append("z")          # "exame"
            elif not _is_vowel(nxt()) and nxt() != "":
                phones.append("ʃ")          # coda "texto" (aprox; "fixo"=ks não modelado)
            else:
                phones.append("ʃ")          # default BR
            i += 1
            continue
        if c == "r":
            if i == 0:
                phones.append("χ")          # "rato"
            elif not _is_vowel(nxt()) or nxt() == "":
                phones.append("χ")          # coda carioca "porta", "mar"
            elif not _is_vowel(prv()):
                phones.append("ɾ")          # encontro "prato", "braço"
            else:
                phones.append("ɾ")          # intervocálico "caro"
            i += 1
            continue
        if c == "l":
            if not _is_vowel(nxt()) or nxt() == "":
                phones.append("w")          # coda vocalizada "Brasil", "alto"
            else:
                phones.append("l")
            i += 1
            continue
        if c == "m":
            phones.append("m"); i += 1; continue
        if c == "n":
            phones.append("n"); i += 1; continue
        if c == "h":
            i += 1; continue                # mudo
        if c == "w":
            phones.append("w"); i += 1; continue
        if c == "y":
            phones.append("j"); i += 1; continue
        if c == "k":
            phones.append("k"); i += 1; continue
        if c in "pbtdfv":
            phones.append(c); i += 1; continue

        i += 1  # caractere desconhecido: ignora

    return phones


def text_to_phones(text: str) -> list[str]:
    out: list[str] = []
    for w in normalize(text):
        out.extend(word_to_phones(w))
    return out


def coverage(texts: list[str]) -> dict:
    """Cobertura fonética de um conjunto de textos."""
    counts: Counter[str] = Counter()
    for t in texts:
        counts.update(text_to_phones(t))
    missing = [p for p in TARGET_PHONES if counts[p] == 0]
    rare = [p for p in TARGET_PHONES if 0 < counts[p] < 5]
    total = sum(counts.values())
    return {
        "total_phones": total,
        "distinct": len([p for p in TARGET_PHONES if counts[p] > 0]),
        "target_size": len(TARGET_PHONES),
        "missing": missing,
        "rare": rare,
        "counts": dict(counts.most_common()),
    }


if __name__ == "__main__":
    import json
    import sys

    texts = [line.strip() for line in sys.stdin if line.strip()]
    print(json.dumps(coverage(texts), ensure_ascii=False, indent=2))
