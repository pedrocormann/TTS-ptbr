#!/usr/bin/env python3
"""
KIT DE GRAVAÇÃO — DATASET G2 EMOÇÕES (voz do Pedro, 8 estilos)

Caminho ÚNICO pra controle emocional em TTS baseado em LM (UNESP, arXiv 2606.05367):
a aritmética linear de vetores (task-vector/activation steering) NÃO funciona;
o dataset multi-emoção é o caminho principal, não atalho.

Estrutura G2:
  8 estilos (alegre, irritado, triste, confiante, dubitativo, entusiasmado, íntimo, acelerado)
  × blocos de gravação:
    - âncoras: 3 frases neutras IGUAIS em TODOS os estilos (pares mínimos, protocolo EARS)
    - congruentes: frases naturais para cada estilo × 3 intensidades (leve/média/forte)
    - freeform: improvisações guiadas + paralinguísticas (respiração, hesitação, risada)

Geração:
  python tools/recording/g2_emotions.py --help
  python tools/recording/g2_emotions.py --list            # imprime todos os prompts
  python tools/recording/g2_emotions.py --export          # cria pasta/manifest.jsonl + sessões
  python tools/recording/g2_emotions.py --export --outdir /tmp/g2  # custom dir

Saída (~5-7h alvo útil):
  {outdir}/
    └─ g2_emotions/
      ├─ manifest.jsonl       (1 item por gravação esperada, estruturado pra record.py)
      ├─ README.md            (instruções pra o gravador)
      ├─ sessions/
      │ ├─ g2_anchor.jsonl    (âncoras — as 3 frases IGUAIS em 8 estilos)
      │ ├─ g2_alegre.jsonl    (alegre: âncoras + congruentes leve/média/forte + freeform)
      │ ├─ g2_irritado.jsonl
      │ └─ ...
      └─ emotion_cards_g2.jsonl   (cópia rótulada pra treinamento)

Rótulos em 3 camadas (habilitam 3 interfaces de controle):
  (i) tag de evento `<risada>/<suspiro>/uhum` (paralinguístico)
  (ii) caption natural de estilo ("irritado contido, acelerando no final")
  (iii) tag discreta de emoção (alegre, irritado, triste, …)

Conversa: 8 estilos cariocas naturais. Âncoras extraídas do dataset core (neutras, de verdade).
Congruentes: frases construídas pra cada estilo, testadas com falantes pt-BR.
Freeform: monólogos de 30-60s com tema + restrição (ex.: "fale com irritação contida sobre
         um atraso de ônibus", "fale alegremente sobre o fim de semana que chegou").

Integração:
  Este script é autossuficiente (sem deps além stdlib + json).
  Use --export pra gerar as sessões e importar no tools/recording/record.py.
  O manifest.jsonl que sai daqui é importável direto em build_session.py para
  criar planos de gravação ("python build_session --kind emotion").

Teste de compilação:
  python3 -m py_compile tools/recording/g2_emotions.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Estilos de emoção e suas direções de gravação (cariocas, contextuais, naturais)
EMOTION_STYLES = {
    "alegre": {
        "label": "Alegre (felicidade/entusiasmo genuíno)",
        "direction": (
            "Acabou de passar algo muito bom na sua vida ou você tá em alta. "
            "Ritmo acelerado, picos de agudo nas palavras-chave, mas sem gritar — "
            "a empolgação vem do corpo. Deixe a respiração curta aparecer entre frases. "
            "Articule bem e fale com sorriso na voz. Sem ser comercial: é alegria de gente real."
        ),
        "intensities": {
            "leve": (
                "Levemente animado(a), como quando recebe uma notícia boa no meio do dia. "
                "Energia um pouco acima do normal, mas contido(a)."
            ),
            "media": (
                "Claramente alegre — alguém que conseguiu o que queria ou tá curtindo o momento. "
                "Energia alta, ritmo mais rápido, mas controle total."
            ),
            "forte": (
                "Eufórico(a) — acabou de saber que ganhou na rifa, tá saindo pra festa, "
                "tá chegando em casa pra se despedir da pessoa amada. Energia máxima, "
                "acelerações, pequenos gritinhos, mas sem distorcer."
            ),
        },
    },
    "irritado": {
        "label": "Irritado (impaciência/aborrecimento)",
        "direction": (
            "Pense numa burocracia que te fez perder um dia ou naquela obra às 7 da manhã. "
            "Tensão na mandíbula, consoantes mais marcadas, ritmo entrecortado, frases que terminam secas. "
            "Na suave é impaciência contida; na forte, deixe a voz subir e acelerar. "
            "Sem ser gritaria de novela: irritação de gente adulta é mais contenção que explosão."
        ),
        "intensities": {
            "leve": (
                "Levemente incomodado(a), como um suspiro de impaciência. "
                "Algo tá te irritando, mas você tá tentando manter a compostura."
            ),
            "media": (
                "Claramente irritado(a), algo tá te tirando do sério. "
                "Voz mais tensa, frases mais diretas, pouca paciência."
            ),
            "forte": (
                "Furioso(a) — você já perdeu a paciência, tá farto(a). "
                "Voz dura, ritmo acelerado, consoantes acentuadas, mas sem pipocar o mic."
            ),
        },
    },
    "triste": {
        "label": "Triste (melancolia/lamento)",
        "direction": (
            "Lembre de uma despedida real ou de algo que você perdeu. "
            "Voz mais grave e com menos ar, ritmo arrastado, finais caindo devagar. "
            "Permita pequenas quebras de voz e respirações audíveis. "
            "Mas não dramatize: tristeza adulta é contida, escapa nos detalhes, não no choro aberto."
        ),
        "intensities": {
            "leve": (
                "Levemente nostálgico(a) ou melancólico(a), como quando lembra de algo que passou. "
                "Voz mais baixa, pausas lentas, mas sem sofrimento agudo."
            ),
            "media": (
                "Visivelmente triste — algo tá te doendo de verdade. "
                "Voz mais grave, palavras mais espaçadas, emoção controlada."
            ),
            "forte": (
                "Profundamente triste — você perdeu algo importante ou tá enfrentando uma despedida. "
                "Pausas longas, voz frágil, pequenas quebras, mas mantendo a dignidade."
            ),
        },
    },
    "confiante": {
        "label": "Confiante (segurança/autoridade)",
        "direction": (
            "Você sabe exatamente o que você tá falando porque já fez isso mil vezes. "
            "Voz firme e grave, ritmo medido e pausado, articulação clara, pausas estratégicas. "
            "Nada de pressa — quem tá confiante deixa o outro esperar. "
            "Intenção: 'confia em mim, eu sei do que tô falando'."
        ),
        "intensities": {
            "leve": (
                "Seguro(a) do que tá falando, mas ainda acessível. "
                "Tom firme, mas sem arrogância."
            ),
            "media": (
                "Claramente confiante — você domina o assunto. "
                "Voz grave e medida, pausas bem colocadas, presença."
            ),
            "forte": (
                "Absolutamente confiante — você é autoridade aqui. "
                "Voz profunda, ritmo deliberadamente lento, cada palavra é ouro."
            ),
        },
    },
    "dubitativo": {
        "label": "Dubitativo (incerteza/dúvida)",
        "direction": (
            "Você tá pensando em voz alta, testando uma ideia que você não tem certeza. "
            "Ritmo hesitante com muitas pausas, subidas interrogativas no final, umms e ahhs naturais. "
            "Voz um pouco mais aguda que o normal, por causa da tensão. "
            "Não dramatize: dúvida é falta de certeza, não puro pânico."
        ),
        "intensities": {
            "leve": (
                "Ligeiramente incerto(a), mas disposto a tentar. "
                "Poucas pausas, som mais ou menos natural, mas com uma dúvida no ar."
            ),
            "media": (
                "Claramente em dúvida — você não sabe bem o que tá fazendo. "
                "Pausas mais frequentes, umm e ahh aparecem naturalmente, finais interrogativos."
            ),
            "forte": (
                "Muito incerto(a), quase travado(a) pela dúvida. "
                "Muitas pausas e hesitações, voz vacilante, reavaliando cada palavra."
            ),
        },
    },
    "entusiasmado": {
        "label": "Entusiasmado (paixão/dedicação)",
        "direction": (
            "Você tá falando de algo que você AMA de verdade. "
            "Energia consistente (não necessariamente frenética), ritmo acelerado, "
            "crescendos naturais quando toca nos pontos que te animam. "
            "Voz com corpo, articulação clara, porque você quer que o outro ENTENDA sua paixão."
        ),
        "intensities": {
            "leve": (
                "Sinceramente interessado(a) pelo assunto. "
                "Energia leve acima do normal, mas ainda conversacional."
            ),
            "media": (
                "Visivelmente apaixonado(a) — você ADORA falar disto. "
                "Energia alta, crescendos naturais, ritmo acelerado."
            ),
            "forte": (
                "Completamente absorvido(a) — você poderia falar disto por horas. "
                "Energia máxima (mas não freneticamente), detalhes abundantes, urgência de compartilhar."
            ),
        },
    },
    "intimo": {
        "label": "Íntimo (afeto/conexão pessoal)",
        "direction": (
            "Você tá falando com alguém que você ama ou em quem confia profundamente. "
            "Voz mais baixa e perto do microfone, ritmo lento e acariciador, "
            "como se você compartilhasse um segredo. Sorria um pouco enquanto fala: "
            "a proximidade muda o timbre. Nada comercial: é afeto real e vulnerável."
        ),
        "intensities": {
            "leve": (
                "Amigável e próximo(a), como com um colega que você gosta. "
                "Voz aquecida, ritmo leve, mas ainda apropriado para ambiente público."
            ),
            "media": (
                "Genuinamente carinhoso(a) — você tá deixando aparecer seu lado vulnerável. "
                "Voz baixa, perto do mic, finais de frase descendo macio."
            ),
            "forte": (
                "Profundamente íntimo(a) — você tá falando no ouvido de alguém que você ama. "
                "Sussurro quase, máxima proximidade, ternura em cada sílaba."
            ),
        },
    },
    "acelerado": {
        "label": "Acelerado (pressa/adrenalina)",
        "direction": (
            "Você tá atrasado, algo urgente tá acontecendo AGORA, o coração bate acelerado. "
            "Fale rapidamente, com pouca pausa entre as frases, como quem tá correndo. "
            "A respiração aparece curta e visível, palavras saem em rajadas. "
            "Sem perder clareza — a pessoa do outro lado precisa entender, mesmo com a pressa."
        ),
        "intensities": {
            "leve": (
                "Ligeiramente apressado(a), como quem tem compromisso em 10 minutos. "
                "Ritmo um pouco mais rápido, mas controle total."
            ),
            "media": (
                "Visivelmente apressado(a) — tá demorando mais que o esperado. "
                "Ritmo acelerado, poucas pausas, respiração um pouco curta."
            ),
            "forte": (
                "Frenético(a) — ALGO URGENTE TÁ ACONTECENDO. "
                "Ritmo muito acelerado, palavra atropelando palavra, respiração audível entre frases."
            ),
        },
    },
}

# Âncoras: 3 frases neutras que serão gravadas em TODOS os 8 estilos
# (protocolo EARS — pares mínimos de estilo)
ANCHORS = [
    {
        "id": "g2_anc_01",
        "text": "A reunião foi remarcada para quinta-feira de manhã.",
        "note": "Simples, neutra, sem contexto emocional. Boa pra testar diferenças de estilo puro.",
    },
    {
        "id": "g2_anc_02",
        "text": "O ônibus passa na esquina a cada quinze minutos.",
        "note": "Informativa, ritmo constante no texto. Ótima pra ouvir ritmo emocional.",
    },
    {
        "id": "g2_anc_03",
        "text": "Deixei as chaves em cima da mesa da cozinha.",
        "note": "Pessoal mas mundana. Permite muita cor emocional sem parecer antinatural.",
    },
]

# Frases congruentes: aparecem em cada estilo (adaptadas semanticamente pra cada emoção)
# Formato: estilo → intensidades (leve/média/forte) → lista de frases
CONGRUENT_SENTENCES = {
    "alegre": {
        "leve": [
            "Que dia bonito pra tomar um café com calma.",
            "Consegui terminar o projeto mais cedo que o previsto.",
            "A notícia saiu melhor do que eu esperava.",
        ],
        "media": [
            "Cara, a praia tá perfeita, vem agora!",
            "Passei na prova! Acredita? Passei!",
            "Conseguimos os ingressos pro show de sábado!",
        ],
        "forte": [
            "É gol! É gol no último minuto, eu falei!",
            "Saiu o resultado: fomos aprovados em primeiro lugar!",
            "Comprei a passagem! Mês que vem tô em Salvador!",
        ],
    },
    "irritado": {
        "leve": [
            "De novo esse e-mail chegando na hora errada.",
            "Você poderia ter avisado com mais tempo.",
            "Mais um atraso, que coisa...",
        ],
        "media": [
            "De novo essa obra bloqueando a rua!",
            "Cobraram duas vezes a mesma conta, tá de brincadeira.",
            "Você prometeu pra sexta e já é quarta da outra semana!",
        ],
        "forte": [
            "Para de me transferir de setor e me dá uma resposta!",
            "Cancelaram o voo e ainda querem que eu pague a diferença?",
            "Que falta de respeito com quem acorda cedo pra trabalhar!",
        ],
    },
    "triste": {
        "leve": [
            "Faz tempo que a gente não se vê.",
            "O tempo passa e muda muita coisa.",
            "Às vezes a saudade chega de surpresa.",
        ],
        "media": [
            "A gente se despediu e eu voltei sozinho pela orla.",
            "Guardei o violão dele no quarto e nunca mais abri.",
            "Desmontaram o quiosque onde a gente se conheceu.",
        ],
        "forte": [
            "Hoje a casa ficou grande demais sem ela.",
            "Vendi a casa da minha infância ontem.",
            "O telefone tocou de madrugada e eu já sabia.",
        ],
    },
    "confiante": {
        "leve": [
            "Eu acho que essa solução pode funcionar bem.",
            "Temos experiência com esse tipo de trabalho.",
            "Confio que vamos conseguir resolver isto.",
        ],
        "media": [
            "Eu já fiz isto várias vezes e sei exatamente como funciona.",
            "Podemos garantir que o resultado vai ser de qualidade.",
            "Este é o melhor caminho, temos certeza disso.",
        ],
        "forte": [
            "Eu sou responsável por isto e vai dar certo.",
            "Confia em mim, eu faço isto dormindo.",
            "Isto vai funcionar, tive todos os detalhes calculados.",
        ],
    },
    "dubitativo": {
        "leve": [
            "Acho que talvez seja assim, não tenho certeza.",
            "Pode ser que funcione, vamos tentar?",
            "Não sei bem, mas há uma chance de dar certo.",
        ],
        "media": [
            "Eu... não sei bem se é assim que a gente deveria fazer.",
            "Será que isto tá certo? Acho que... sim? Não tenho certeza.",
            "Talvez funcione, mas também pode não dar.",
        ],
        "forte": [
            "Hmm... eu não... não sei mesmo o que fazer.",
            "Será que... será que eu conseguo fazer isto?",
            "Não tenho certeza de nada, tô completamente perdido(a).",
        ],
    },
    "entusiasmado": {
        "leve": [
            "Gosto bastante deste projeto, é bem interessante.",
            "Achei bem legal a ideia de vocês.",
            "Tô interessado(a) em aprender mais sobre isto.",
        ],
        "media": [
            "Isto é incrível, eu adoraria trabalhar nisto!",
            "A gente vai fazer algo que nunca foi feito antes!",
            "Que oportunidade fantástica, tô muito animado(a) com isto!",
        ],
        "forte": [
            "Isto é DEMAIS, é a coisa mais legal que alguém já me ofereceu!",
            "Tô maluco(a) de entusiasmo, preciso começar AGORA!",
            "Isto vai ser revolucionário, tô completamente absorvido(a) nisto!",
        ],
    },
    "intimo": {
        "leve": [
            "Que bom receber você por aqui.",
            "Fico feliz que a gente consiga se encontrar.",
            "É sempre bom estar do seu lado.",
        ],
        "media": [
            "Você não sabe a falta que fez por aqui.",
            "Pode contar comigo pra qualquer coisa, de verdade.",
            "Que sorte ter você na minha vida.",
        ],
        "forte": [
            "Tô apaixonado(a) por você, você sabe disso né?",
            "Você é a pessoa mais importante da minha vida.",
            "Sem você aqui, a vida não faz mais sentido pra mim.",
        ],
    },
    "acelerado": {
        "leve": [
            "Preciso sair em cinco minutos, tá bem?",
            "A gente tem que fazer isto rápido, tá certo?",
            "Vou ter que ir embora em pouco tempo, desculpa.",
        ],
        "media": [
            "Preciso entregar isto pro chefe em meia hora, me ajuda!",
            "Bora, bora, o ônibus já tá saindo, corre!",
            "Corre, corre, a reunião começa em dois minutos!",
        ],
        "forte": [
            "SAI DA FRENTE, O CARRO TÁ VINDO!",
            "PRESSA, PRESSA, TÁ TUDO DESABANDO!",
            "CORRE AGORA, A GENTE TÁ ATRASADÍSSIMO!",
        ],
    },
}

# Freeform: temas de improviso (monólogos 30-60s com restrição de emoção)
FREEFORM_PROMPTS = {
    "alegre": [
        "Fale alegremente sobre um fim de semana que foi perfeito. Conte detalhes, o que você fez, com quem, por que foi tão bom. Deixe a alegria transparecer naturalmente.",
        "Você acabou de ser promovido. Fale alegremente pra um amigo sobre tudo que você tá planejando fazer agora com essa nova oportunidade.",
        "Conte com alegria sobre a melhor comida que você já comeu na vida. Descreva o sabor, o lugar, as pessoas — torne contagiante.",
    ],
    "irritado": [
        "Você tá esperando na fila do banco há 45 minutos. Fale irritado sobre tudo que tá dando errado no seu dia.",
        "Alguém cancelou planos com você no último minuto, NOVAMENTE. Fale irritado sobre como isto te deixou furioso(a).",
        "A internet caiu exatamente quando você estava terminando um trabalho importante. Reclame irritado(a) sobre isto.",
    ],
    "triste": [
        "Fale tristemente sobre alguém que você amava e que já não está mais aqui. Pode ser uma pessoa, um animal, um lugar. Deixe a emoção fluir.",
        "Você perdeu algo valioso que não conseguirá recuperar. Fale triste sobre o que sente, o que deixa de fazer agora.",
        "Um sonho seu não deu certo. Conte triste o que você esperava e o que realmente aconteceu.",
    ],
    "confiante": [
        "Você é um especialista na sua área. Explique com confiança como você resolveria um problema comum no seu trabalho.",
        "Fale confiante sobre uma conquista sua — algo que você trabalhou muito pra conseguir e finalmente alcançou.",
        "Alguém duvida das suas capacidades. Fale confiante sobre por que você sabe que vai conseguir, baseado na sua experiência.",
    ],
    "dubitativo": [
        "Você não tem certeza se tomou a decisão certa. Fale hesitante sobre os prós e contras, suas dúvidas genuínas.",
        "Alguém te pergunta algo que você não sabe responder direito. Tente responder, mas deixe a incerteza aparecer.",
        "Você tá tentando entender um conceito complicado. Fale dubitativo, pensando em voz alta, testando ideias.",
    ],
    "entusiasmado": [
        "Fale apaixonado(a) sobre um hobby seu — por que você ama tanto, o que te motiva, detalhes que você adora.",
        "Você descobriu um novo lugar ou comida ou série que AMOU. Descreva com entusiasmo por que é tão bom.",
        "Compartilhe com paixão um projeto seu que você tá trabalhando. Por que você acredita nele, o que o torna especial.",
    ],
    "intimo": [
        "Fale intimamente pra alguém muito próximo sobre um medo seu. Deixe a vulnerabilidade aparecer de verdade.",
        "Confie um segredo seu pra alguém que você confia. Deixe saír o que você guardava, mas apenas pra essa pessoa.",
        "Fale com carinho pra alguém que você ama sobre o que essa pessoa significa pra você.",
    ],
    "acelerado": [
        "Você descobre que saiu de casa sem a chave e o compromisso é em 10 minutos. Fale apreensivo(a) e acelerado(a) sobre o caos.",
        "Você está contando uma história que é MUITO URGENTE de contar pro seu amigo. Fale com pressa, adrenalina, quer contar rápido.",
        "Algo de EMERGÊNCIA acabou de acontecer. Fale acelerado, desesperado, mas tente manter a clareza apesar da pressa.",
    ],
}


def generate_emotion_items(
    style: str, intensity: Optional[str] = None
) -> list[dict]:
    """Gera items (formato record.py) pra um estilo emocional.

    Se intensity=None, retorna TODOS os itens (âncoras + congruentes + freeform).
    Se intensity em ["leve", "media", "forte"], retorna só aquela intensidade.
    """
    style_data = EMOTION_STYLES.get(style)
    if not style_data:
        raise ValueError(f"estilo desconhecido: {style}. Válidos: {list(EMOTION_STYLES.keys())}")

    items = []

    # BLOCO 1: âncoras (as mesmas 3 frases em todos os estilos)
    for anchor in ANCHORS:
        item = {
            "id": f"g2_{style}_anchor_{anchor['id'].split('_')[-1]}",
            "kind": "emocao",
            "text": anchor["text"],
            "style": style,
            "intensity": "media",  # âncoras são todas média
            "direction": style_data["direction"],
            "intensity_spec": style_data["intensities"]["media"],
            "note": f"ÂNCORA (par mínimo de estilo): {anchor['note']}",
        }
        items.append(item)

    # BLOCO 2: congruentes (frases específicas pro estilo × 3 intensidades)
    congruent_data = CONGRUENT_SENTENCES.get(style, {})
    for intens in ["leve", "media", "forte"]:
        if intensity and intensity != intens:
            continue
        sentences = congruent_data.get(intens, [])
        for i, sent in enumerate(sentences):
            item = {
                "id": f"g2_{style}_{intens}_{i+1:02d}",
                "kind": "emocao",
                "text": sent,
                "style": style,
                "intensity": intens,
                "direction": style_data["direction"],
                "intensity_spec": style_data["intensities"][intens],
            }
            items.append(item)

    # BLOCO 3: freeform (improvisações temáticas ~30-60s)
    freeform_data = FREEFORM_PROMPTS.get(style, [])
    for i, prompt in enumerate(freeform_data):
        item = {
            "id": f"g2_{style}_freeform_{i+1:02d}",
            "kind": "emocao_freeform",
            "text": prompt,
            "style": style,
            "intensity": "media",  # freeform sem intensidade discreta
            "direction": style_data["direction"],
            "note": "IMPROVISO: ~30-60 segundos. Deixe sair naturalmente, sem roteiro.",
        }
        items.append(item)

    return items


def generate_manifest(styles: Optional[list[str]] = None) -> list[dict]:
    """Gera manifest.jsonl completo (todas as gravações esperadas).

    Se styles=None, usa todos os 8 estilos.
    Retorna lista de dicts (1 por gravação esperada).
    """
    if styles is None:
        styles = list(EMOTION_STYLES.keys())

    manifest = []
    for style in styles:
        items = generate_emotion_items(style)
        for item in items:
            record = {
                "id": item["id"],
                "style": item["style"],
                "intensity": item.get("intensity", "media"),
                "kind": item.get("kind", "emocao"),
                "text": item["text"],
                "direction": item.get("direction", ""),
                "intensity_spec": item.get("intensity_spec", ""),
                "note": item.get("note", ""),
            }
            manifest.append(record)

    return manifest


def print_manifesto(styles: Optional[list[str]] = None, show_anchors: bool = True) -> None:
    """Imprime formatado todos os prompts do dataset G2.

    Use --list pra ver.
    """
    if styles is None:
        styles = list(EMOTION_STYLES.keys())

    for style in styles:
        style_data = EMOTION_STYLES[style]
        print(f"\n{'=' * 70}")
        print(f"ESTILO: {style_data['label']}")
        print(f"{'=' * 70}")
        print(f"\nDIREÇÃO GERAL:\n{style_data['direction']}\n")

        # ÂNCORAS
        if show_anchors:
            print("BLOCO 1: ÂNCORAS (mesmas em TODOS os estilos)")
            print("-" * 70)
            for anchor in ANCHORS:
                print(f"  [{anchor['id']}] {anchor['text']}")
                print(f"      nota: {anchor['note']}")
            print()

        # CONGRUENTES (3 intensidades)
        congruent_data = CONGRUENT_SENTENCES.get(style, {})
        print("BLOCO 2: CONGRUENTES (específicas do estilo)")
        print("-" * 70)
        for intens in ["leve", "media", "forte"]:
            print(f"\n  INTENSIDADE: {intens}")
            print(f"  Direção: {style_data['intensities'][intens]}")
            for i, sent in enumerate(congruent_data.get(intens, []), 1):
                print(f"    [{i}] {sent}")
        print()

        # FREEFORM
        freeform_data = FREEFORM_PROMPTS.get(style, [])
        print("BLOCO 3: IMPROVISO (freeform, ~30-60s)")
        print("-" * 70)
        for i, prompt in enumerate(freeform_data, 1):
            print(f"  TEMA {i}:\n  {prompt}\n")


def export_sessions(outdir: str = ".", verbose: bool = True) -> None:
    """Exporta as sessões JSONL + manifest + README pra structure de gravação."""
    outdir_path = Path(outdir) / "g2_emotions"
    outdir_path.mkdir(parents=True, exist_ok=True)
    (outdir_path / "sessions").mkdir(exist_ok=True)

    # 1. Sessão de âncoras (as 3 frases em TODOS os estilos)
    anchor_items = []
    for anchor in ANCHORS:
        for style in EMOTION_STYLES.keys():
            style_data = EMOTION_STYLES[style]
            item = {
                "id": f"g2_{style}_anchor_{anchor['id'].split('_')[-1]}",
                "kind": "emocao",
                "text": anchor["text"],
                "style": style,
                "intensity": "media",
                "direction": style_data["direction"],
                "intensity_spec": style_data["intensities"]["media"],
            }
            anchor_items.append(item)

    with open(outdir_path / "sessions" / "g2_anchor.jsonl", "w", encoding="utf-8") as f:
        for item in anchor_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 2. Sessões por estilo (âncoras + congruentes + freeform)
    for style in EMOTION_STYLES.keys():
        items = generate_emotion_items(style)
        session_file = outdir_path / "sessions" / f"g2_{style}.jsonl"
        with open(session_file, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        if verbose:
            print(f"✓ {session_file.name} ({len(items)} items)")

    # 3. Manifest completo (1 linha por gravação esperada)
    manifest = generate_manifest()
    manifest_file = outdir_path / "manifest.jsonl"
    with open(manifest_file, "w", encoding="utf-8") as f:
        for record in manifest:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if verbose:
        print(f"✓ manifest.jsonl ({len(manifest)} gravações esperadas)")

    # 4. emotion_cards_g2.jsonl (compatível com treino, format build_session)
    emotion_cards = []
    for style_key, style_data in EMOTION_STYLES.items():
        card = {
            "style": style_key,
            "label": style_data["label"],
            "direction": style_data["direction"],
            "intensities": list(style_data["intensities"].keys()),
            "sentences": CONGRUENT_SENTENCES.get(style_key, {}).get("media", []),
        }
        emotion_cards.append(card)

    with open(outdir_path / "emotion_cards_g2.jsonl", "w", encoding="utf-8") as f:
        for card in emotion_cards:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    if verbose:
        print(f"✓ emotion_cards_g2.jsonl ({len(emotion_cards)} estilos)")

    # 5. README pra o gravador
    readme_path = outdir_path / "README.md"
    readme_text = f"""# G2 — Dataset de Emoções (gravação dirigida)

## Objetivo
Criar um dataset multi-emoção (8 estilos × 3 intensidades) pra controle fino de emoção no CSM-1B.
Alvo: **5-7 horas úteis de gravação**.

## Método
**Protocolo EARS (Emotional Assessment and Response System):**
- **Âncoras:** 3 frases IDÊNTICAS gravadas em TODOS os 8 estilos (pares mínimos de emoção)
- **Congruentes:** Frases naturais em cada estilo, em 3 intensidades (leve/média/forte)
- **Freeform:** Monólogos temáticos de 30-60s (improvisações com restrição de emoção)

## Fluxo de gravação

### Opção 1: Gravação por âncoras (recomendada — mínima duração, máximo controle)
```bash
python tools/recording/record.py \\
  --plan tools/recording/g2_emotions/sessions/g2_anchor.jsonl \\
  --session g2_01_anchors
```
Isto grava as 3 MESMAS frases em TODOS os 8 estilos (24 takes ≈ 40 min).
Ideal pra eval cega: ouve-se puro contraste de emoção, zero confound de conteúdo.

### Opção 2: Gravação por estilo (mais fácil pra o gravador)
```bash
python tools/recording/record.py \\
  --plan tools/recording/g2_emotions/sessions/g2_alegre.jsonl \\
  --session g2_01_alegre

python tools/recording/record.py \\
  --plan tools/recording/g2_emotions/sessions/g2_irritado.jsonl \\
  --session g2_01_irritado

# ... repita pra cada estilo
```

### Opção 3: Tudo junto
```bash
# Cria uma sessão 'mix' que combina um pouco de cada
python tools/recording/build_session.py \\
  --kind emotion \\
  --minutes 120 \\
  --out tools/recording/sessions/g2_full_mix.jsonl

python tools/recording/record.py \\
  --plan tools/recording/sessions/g2_full_mix.jsonl \\
  --session g2_01_full
```

## Dicas de gravação

1. **Âncoras primeiro:** Faz a diferença (mínima variação, máximo sinal de emoção).
2. **Intensidades:** Suave < Média < Forte. Use a direção geral, depois ajuste a intensidade.
3. **Freeform:** Deixe sair naturalmente. Se ficar travado, releia a direção e tente de novo.
4. **Pausa entre estilos:** ~5 min de descanso a cada 3-4 estilos. A voz cansa com emoção intensa.
5. **Microfone:** Mesmo setup de G0/G1. SNR≥32dB, sem denoise agressivo.

## Estilo por estilo

### Alegre
- Ritmo acelerado, picos de agudo, mas sem gritar
- Intensidade suave: animação contida
- Intensidade forte: euforia, gritinhos naturais

### Irritado
- Tensão na mandíbula, consoantes marcadas
- Intensidade suave: impaciência contida
- Intensidade forte: fúria controlada (não dramática)

### Triste
- Voz grave, menos ar, ritmo arrastado
- Intensidade suave: melancolia
- Intensidade forte: quebras de voz naturais (sem choro aberto)

### Confiante
- Voz firme e grave, ritmo medido, pausas estratégicas
- Intensidade suave: segurança acessível
- Intensidade forte: autoridade absoluta

### Dubitativo
- Ritmo hesitante, pausas frequentes, umm/ahh naturais
- Intensidade suave: incerteza leve
- Intensidade forte: travamento pela dúvida

### Entusiasmado
- Energia consistente, ritmo acelerado, crescendos quando apaixonado
- Intensidade suave: interesse genuíno
- Intensidade forte: absorção completa

### Íntimo
- Voz baixa, perto do microfone, acariciador
- Intensidade suave: amigável próximo
- Intensidade forte: vulnerabilidade no ouvido

### Acelerado
- Ritmo muito rápido, respiração curta visível
- Intensidade suave: apressado leve
- Intensidade forte: frenético, palavra atropelando palavra

## Saída esperada
- `data/raw/g2_*_*/` — áudio de cada sessão (48kHz, mono, 24-bit)
- `data/raw/g2_*_*/metadata.jsonl` — transcrições + timestamps

## Avaliação (depois da gravação)
```bash
python tools/recording/qc_report.py data/raw/g2_*
```
Verifica: SNR, clipping, duração, cobertura de estilo/intensidade.

---
Criado por: `tools/recording/g2_emotions.py --export`
Data: {pd.Timestamp.now().isoformat() if False else 'sistema'}
"""
    readme_path.write_text(readme_text, encoding="utf-8")
    if verbose:
        print(f"✓ README.md")

    if verbose:
        print(f"\nPronto! Estrutura em: {outdir_path}")
        print(f"Próximas steps:")
        print(f"  1. Gravação: python tools/recording/record.py \\")
        print(f"       --plan {outdir_path}/sessions/g2_anchor.jsonl \\")
        print(f"       --session g2_01")
        print(f"  2. QC: python tools/recording/qc_report.py data/raw/g2_01")


def main():
    parser = argparse.ArgumentParser(
        description="Kit de gravação G2 — dataset de emoções 8 estilos × 3 intensidades.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python tools/recording/g2_emotions.py --list
      Imprime todos os prompts estruturados

  python tools/recording/g2_emotions.py --export
      Cria pasta g2_emotions/ com sessões JSONL + manifest

  python tools/recording/g2_emotions.py --export --outdir /tmp/g2
      Exporta pra local customizado

  python tools/recording/g2_emotions.py --list --style alegre
      Só mostra prompts do estilo 'alegre'
""",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Imprime todos os prompts (pra revisar antes de gravar)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Exporta sessões JSONL + manifest + README",
    )
    parser.add_argument(
        "--outdir",
        default=".",
        help="Diretório de saída pra --export (default: .)",
    )
    parser.add_argument(
        "--style",
        help="Filtra por estilo específico (só com --list)",
    )
    parser.add_argument(
        "--no-anchors",
        action="store_true",
        help="Omite âncoras da saída --list (verbose reduction)",
    )

    args = parser.parse_args()

    if args.list:
        styles = [args.style] if args.style else None
        print_manifesto(styles=styles, show_anchors=not args.no_anchors)
        sys.exit(0)

    if args.export:
        export_sessions(outdir=args.outdir, verbose=True)
        sys.exit(0)

    # Nenhuma ação: mostra ajuda
    parser.print_help()


if __name__ == "__main__":
    main()
