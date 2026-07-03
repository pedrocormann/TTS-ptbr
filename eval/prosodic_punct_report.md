# Re-pontuação prosódica — antes/depois (flywheel/pedro)

_Gerado por tools/curate/repunct_prosodic.py · 259 ok · 0 erros · cobertura de alinhamento mediana 94% · 25 clipes <70% (revisar)_

| métrica (total no corpus) | atual (Whisper/curado) | prosódica |
|---|---|---|
| vírgulas /100 palavras | 11.0 | 3.6 |
| terminais (. !) /100 palavras | 8.9 | 5.5 |
| interrogações | 11 | 2 |
| hesitações (…) | 0 | 67 |
| clipes com pontuação alterada | — | 242/259 |

## Exemplos (maior mudança)

**elevenlabs2024** (align 79%)
- atual: o cara pegou uma trilha, escalou e fez, que eu já fiz essa trilha, eu escalei, então eu fico imaginando um cara em 1800 e antigamente, 1900 e antigamente.
- prosó: O cara pegou uma trilha escalou e fez que eu já fiz essa trilha eu escalei… Então… Eu fico imaginando um cara em 1800 e antigamente 1900 e antigamente…

**elevenlabs2024** (align 92%)
- atual: em que você podia... tinha uma régua de anos, assim, que você podia separar o intervalo de de anos, por exemplo, de 1800 a 1920.
- prosó: Em que você podia, tinha uma régua de anos assim… Que você podia separar o intervalo de de anos por exemplo de 1800 a 1920…

**elevenlabs2024** (align 100%)
- atual: Então, tipo, eu lá procurando por esse livro obscuro sobre lendas urbanas, certo?
- prosó: Então… Tipo… Eu lá procurando por esse livro obscuro sobre lendas urbanas certo.

**elevenlabs2024** (align 97%)
- atual: sons, mas eu acho que vai ser um grande exercício, muito interessante de exploração para as pessoas ouvirem diferentes sons que formam, é, o choro, no caso, o chorinho.
- prosó: Sons, mas eu acho que vai ser um grande exercício muito interessante de exploração para as pessoas ouvirem diferentes sons que formam é o choro no caso o chorinho…

**elevenlabs2024** (align 90%)
- atual: e eles vão ter que fazer ali uma harmonia de eé maior e depois, a partir do que a pessoa cantou, óbvio que muitas vezes as músicas se repetem, as pessoas já se reconhecem, as músicas já lembram como tocar, mas enfim...
- prosó: E eles vão ter que fazer ali uma harmonia de eé maior e depois a partir do que a pessoa cantou óbvio que muitas vezes as músicas se repetem as pessoas já se reconhecem as músicas já lembram como tocar mas enfim…

**elevenlabs2024** (align 89%)
- atual: pra inserirem a roda de samba que ele conhece, que ele sabe que não tá no mapa, porque com certeza todo mundo vai explorar e vai procurar ali suas 5, suas 10 rodas de samba preferidas
- prosó: Pra inserirem a roda de samba que ele conhece que ele sabe que não tá no mapa porque com certeza todo mundo vai explorar e vai procurar ali suas 5… Suas 10 rodas de samba preferidas…

**elevenlabs2024** (align 94%)
- atual: que respondem ao toque, é... a voz, ao corpo ao movimento, realidades aumentadas que constituem danças, rítmos...
- prosó: Que respondem ao toque é a voz… Ao corpo ao movimento. Realidades aumentadas que constituem danças rítmos.

**elevenlabs2024** (align 100%)
- atual: Um, dois, três, quatro, um, dois, três, quatro.
- prosó: Um dois três quatro, um dois três quatro.

**elevenlabs2024** (align 81%)
- atual: E, de repente, fica-se uma melodia, uma melodia muito para cima, alegre, feliz, e depois volta a ficar triste de novo.
- prosó: E de repente fica-se uma melodia uma melodia muito para cima alegre feliz e depois volta a ficar triste de novo.

**elevenlabs2024** (align 85%)
- atual: Quando eu tocava samba, eu tinha um amigo que era pandeirista do, do principal grupo do grupo de pagode, grupo de samba que eu toquei por mais tempo, a "banda de samba" em que eu toquei por mais tempo.
- prosó: Quando eu tocava samba… Eu tinha um amigo que era pandeirista do do principal grupo do grupo de pagode grupo de samba que eu toquei por mais tempo, a banda de samba em que eu toquei por mais tempo.

**elevenlabs2024** (align 100%)
- atual: E ele conseguia criar, enfim, muitos efeitos, só nas horas vagas dele a noite, (ele) ainda tinha outro emprego como designer
- prosó: E ele conseguia criar enfim… Muitos efeitos, só nas horas vagas dele a noite (ele) ainda tinha outro emprego como designer.

**elevenlabs2024** (align 73%)
- atual: o Guilherme já era um grande amigo de longa data, enfim, ele... ele fez várias graduações, ele é designer de interação, ele é produtor cultural, ele gosta de tecnologias emergentes.
- prosó: O Guilherme já era um grande amigo de longa data enfim ele ele fez várias graduações, ele é designer de interação ele é produtor cultural, ele gosta de tecnologias emergentes…

## Leitura

- A pontuação prosódica só marca vírgula onde HÁ pausa real e fecha ponto onde o contorno
  fechou (pausa longa ou F0 no piso + reset) — é a supervisão que o TTS precisa pra
  aprender melodia de fala espontânea (tese Aluísio/NILC, dataset NURC-SP_ENTOA_TTS).
- `…` marca hesitação/alongamento com pausa — preservado como evento prosódico.
- Próximo passo: A/B no treino (arm com texto prosódico vs atual) na rodada 3.