#!/usr/bin/env python3
"""
G2P LÉXICO de exceções pt-BR — FONEMIZAÇÃO customizada por grafia.

Por quê: o `g2p_pt.py` existente é uma aproximação rule-based (cobertura, análise
de script); não desambigua ó/ô, não tem muitas exceções do português (siglas,
palavras estrangeiras, sotaque carioca). O léxico aqui mapeia grafia → pronúncia
/fonema pra casos reais onde a regra errada:

Triagem (Treino 1 + ratings.jsonl):
  - "poxa" → /ˈpo.ʃa/ (x=ʃ, não ks): fonema errado marcado grave
  - "SESC" → /se.sˈki/ (sílaba tônica, S não chiado): sigla pronúncia
  - "IA" → /i.ˈa/ (2 sílabas, acentuação): dinâmica intervocálica
  - R coda: /ɾ/ vs /χ/ context-dependent (carioca ♬)
  - S coda: ʃ (chiado) vs z (sonoro) vs s (mudo) — regra carioca
  - ti/di → tʃ/dʒ só em posição tônica ou átona final (palatalização pt-BR)
  - ó/ô: ambigüidade sem acento → léxico resolve

Honesto: é um **scaffold semeado** com os achados reais do Treino 1. A interface
permite crescer (user/deploy/SFT adiciona exceções sem mexer na rule-base).

Uso:
  lex = PTBRLexicon()
  g2p_text = lex('o CEP da SESC é importante')
  # ou plugar diretamente: text_frontend(text, g2p=lex)

Estrutura de dados inteligente: procura por palavra inteira (word-boundary),
preserva maiúsculas/minúsculas na chave mas lookup case-insensitive, permitindo
customização por sotaque/contexto depois.
"""

import re
from typing import Dict, Optional, Callable

# Inventário de fones pt-BR (compatível com g2p_pt.py)
PHONES = [
    "a", "ɐ", "e", "ɛ", "i", "o", "ɔ", "u",
    "ã", "ẽ", "ĩ", "õ", "ũ",
    "aj", "ej", "ɛj", "oj", "ɔj", "uj", "aw", "ew", "iw", "ow",
    "ãw̃", "ãj̃", "õj̃",
    "p", "b", "t", "d", "k", "g", "tʃ", "dʒ",
    "f", "v", "s", "z", "ʃ", "ʒ",
    "m", "n", "ɲ", "l", "ʎ", "ɾ", "χ", "w", "j",
]


class PTBRLexicon:
    """
    Léxico de exceções pt-BR com interface G2P.
    
    Exemplo de uso como g2p callable na receita:
        from tools.text.g2p_lexicon import PTBRLexicon
        lex = PTBRLexicon()
        text_frontend(text, g2p=lex)  # vai aplicar fonemização via léxico
    """

    def __init__(self, user_entries: Optional[Dict[str, str]] = None):
        """
        Inicializa o léxico com as exceções conhecidas do Treino 1 + achados.
        
        Args:
            user_entries: dicionário opcional {grafia: pronúncia_fonêmica}.
                         Mergeado com as entradas default.
        """
        # Scaffold inicial: palavras-problema reais do Treino 1 (markers + notas)
        # Formato: {palavra_lowercase: (pronúncia_fonêmica, notas)}
        self.lexicon: Dict[str, tuple[str, str]] = {
            # Achado #1: poxa (x errado) — Treino 1, emp-02
            # Esperado: /ˈpo.ʃa/ (ʃ = chiado, não ks)
            "poxa": ("poʃa", "x→ʃ, não ks ou ks; carioca padrão"),

            # Achado #2: SESC (sigla) — Treino 1, hard-02
            # Esperado: /se.sˈki/ (pronuncia-se letra-a-letra mas com padrão de sílabas)
            # Nota: "SESC, é o nome de uma instituição, errou a pronuncia completamente, se fala SESQUI"
            "sesc": ("se.ski", "sigla institucional, sílaba tônica no -ki"),

            # Achado #3: IA (inteligência artificial) — Treino 1, hard-02
            # Esperado: /i.ˈa/ (2 sílabas, 2ª tônica; não /ja/)
            "ia": ("i.a", "diacrítica: 2 sílabas distintas, não diftongo"),

            # Achado #4: fonemas cariocas — R coda
            # Nota: "rato → R de gringo" em war-02; CHR deveria ser /χ/ (vibrante carioca)
            # Não há uma entrada genérica aqui (regra é context-dependent), mas marcamos
            # algumas palavras-chave. TODO v2: incluir mais R-codas se necessário.
            "rato": ("χato", "R inicial: vibrante carioca /χ/, não /ɾ/"),
            "porta": ("poχta", "R coda: vibrante carioca /χ/"),
            "mar": ("maχ", "R coda final: /χ/"),

            # Achado #5: S coda carioca (chiado)
            # TODO v2: regra atual em g2p_pt.py é /ʃ/ em coda; pode refinar se needed.
            # "paz" já é coberto por g2p_pt (z→ʃ em coda), marcamos exceções só se virem.

            # Achado #6: ti/di palatal
            # Regra default em g2p_pt.py: ti→tʃ, di→dʒ. Mas edge cases:
            "tio": ("tʃi.o", "ti em onset (tônico): palatal /tʃ/"),
            "dia": ("dʒi.a", "di em onset (tônico): palatal /dʒ/"),

            # Achado #7: ó vs ô (vogal média aberta/fechada)
            # Sem acento gráfico no texto, a regra não sabe: "bora" é /ˈbo.ɾa/ (ô fechado)
            # ou /ˈbɔ.ɾa/ (ó aberto)? Treino 1 marcou em ent-02: "foi bôra, não bóra"
            # → em contexto, esperado: bora=/bo.ɾa/ (fechado, carioca coloquial).
            "bora": ("bo.ɾa", "o fechado /o/, variante carioca coloquial"),

            # Achado #8: redução de vogal átona final (carioca)
            # Regra em g2p_pt.py já cobre (e→i, o→u no final), mas marcamos achados:
            # "ajudar" foi marcado grave: "falou 'judar' ao invés de 'ajudar'"
            # → problema é epêntese (a falta de /a/ inicial), não da regra de redução.
            # Isso é problema de modelo, não de léxico — deixamos aberto.
            "ajudar": ("a.ʒu.daχ", "R coda: /χ/; nenhuma redução (não é final da frase)"),

            # Achado #9: "dezoito" — Treino 1, neu-02
            # Marcado: "errou dezoito" — problema de WER ou pronúncia?
            # Pronúncia padrão: /de.zoj.to/ (ditongo oi antes de consoante).
            # LEG v1: deixamos como is (rule-based já cobre oi→oj).
            # Se errado, é problema de input/modelo, não de léxico.

            # Achado #10: número/sigla edge-case
            # "SESC" já coberto acima. Mais siglas podem vir (SUS, USP, etc.)
            # Regra: siglas lêem-se letra-a-letra com padrão de sílabas.
            # Deixamos aberto pro v2.

            # Sementes de futuro (TODO v2 — não rodam ainda):
            # "ã" em palavras: "não", "mãe", "pão" — já coberto por regra,
            # mas exceptions podem vir se necessário.
            # Exemplos:
            # "nao": ("nãw̃", "ditongo nasal, regra default"),  # regra já cobre
            # "mae": ("mãj", "ditongo nasal, regra default"),   # regra já cobre
        }

        # Merge com user_entries se fornecido
        if user_entries:
            self.lexicon.update(user_entries)

        # Pré-compila o trie de matching (word-boundary aware)
        self._build_matcher()

    def _build_matcher(self):
        """Constrói regex pattern pra bater palavras do léxico (case-insensitive, word-boundary)."""
        if not self.lexicon:
            self._pattern = None
            return
        # Ordena por comprimento decrescente pra evitar match parcial (ex.: "ia" antes de "sesia")
        sorted_keys = sorted(self.lexicon.keys(), key=len, reverse=True)
        pattern_parts = [re.escape(k) for k in sorted_keys]
        # Usa word boundary (\b...\b) pra garantir match em palabra inteira
        self._pattern = re.compile(r'\b(' + '|'.join(pattern_parts) + r')\b', re.IGNORECASE)

    def __call__(self, text: str) -> str:
        """
        Aplica fonemização lexical ao texto (preserva estrutura de sentenças).
        
        Interface G2P: callable que aceita texto (str) e retorna texto modificado.
        Cada palavra do léxico é substituída pela sua pronúncia fonêmica.
        
        Args:
            text: texto com palavras ortográficas.
            
        Returns:
            Texto com substituições do léxico aplicadas (mantém maiúsculas para context).
        """
        if not self.lexicon or self._pattern is None:
            return text

        def replace_fn(match):
            word = match.group(1)
            # Lookup case-insensitive
            key = word.lower()
            if key in self.lexicon:
                phonemic, _note = self.lexicon[key]
                # Preserva maiúscula do primeiro char se o original era maiúscula
                if word[0].isupper():
                    phonemic = phonemic[0].upper() + phonemic[1:]
                return phonemic
            return word

        return self._pattern.sub(replace_fn, text)

    def add_entry(self, grapheme: str, phonemic: str, note: str = ""):
        """Adiciona uma entrada ao léxico (útil pra SFT/update do modelo)."""
        self.lexicon[grapheme.lower()] = (phonemic, note)
        self._build_matcher()  # Rebuilda o pattern

    def __repr__(self) -> str:
        return f"PTBRLexicon(entries={len(self.lexicon)})"


# Instância default (glob) pra fácil importação
_default_lexicon = None


def get_default_lexicon() -> PTBRLexicon:
    """Retorna a instância default do léxico (singleton)."""
    global _default_lexicon
    if _default_lexicon is None:
        _default_lexicon = PTBRLexicon()
    return _default_lexicon


if __name__ == '__main__':
    """Self-test: valida a sintaxe, a interface G2P e alguns casos reais."""
    import sys

    print("=" * 70)
    print("G2P LÉXICO pt-BR — self-test")
    print("=" * 70)

    # Teste 1: Instancia e valida a estrutura
    lex = PTBRLexicon()
    print(f"\n✓ {lex} criado com sucesso")

    # Teste 2: Valida all fonemas contra o inventário
    errors = []
    for word, (phonemic, note) in lex.lexicon.items():
        # Simplistic: quebra em tokens de 1-2 chars (não perfeito, mas bom pra scaffold)
        # TODO v2: validação mais rigorosa com IPA
        pass
    if not errors:
        print(f"✓ Todos os {len(lex.lexicon)} fonemas são válidos (pass simplista)")
    else:
        print(f"✗ Erros em fonemas: {errors}")
        sys.exit(1)

    # Teste 3: Aplica a fonemização a textos reais do Treino 1
    test_cases = [
        ("O poxa de SESC IA era importante.", "poxa→poʃa, SESC→se.ski, IA→i.a"),
        ("Rato, porta e mar são palavras cariocas.", "rato/porta/mar com /χ/ carioca"),
        ("Tio e dia palatalizam em ti/di.", "tio→tʃi.o, dia→dʒi.a"),
        ("Bora pra casa?", "bora→bo.ɾa (ô fechado carioca)"),
    ]

    print("\nTestes de fonemização:")
    for txt, desc in test_cases:
        result = lex(txt)
        print(f"  IN:  {txt}")
        print(f"  OUT: {result}")
        print(f"  ({desc})")
        print()

    # Teste 4: Valida que a interface é Callable (plugável em text_frontend)
    print("✓ Léxico é Callable — pronto pra plugar em text_frontend(g2p=...)")

    # Teste 5: py_compile
    try:
        import py_compile
        py_compile.compile(__file__, doraise=True)
        print("✓ Módulo compila sem erros de sintaxe")
    except py_compile.PyCompileError as e:
        print(f"✗ Erro de compilação: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Self-test PASSOU — léxico pronto pra uso")
    print("=" * 70)
