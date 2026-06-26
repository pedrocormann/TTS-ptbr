#!/usr/bin/env python3
"""FreeSVC — augmentação BARATA de dado por voice conversion zero-shot.  [PRÓXIMA SPRINT]

IDEIA: a gente tem POUCA voz do Pedro (~24min seed) e o gargalo é DADO. FreeSVC (voice
conversion zero-shot, AKCIT/UFG, arXiv 2501.05586, MIT-ish) converte QUALQUER fala pt-BR
pra voz-alvo do Pedro usando uma referência curta. Então dá pra pegar HORAS de fala pt-BR
genérica (CML-TTS, NURC-SP, MuPe...) e convertê-las pra "voz do Pedro" → multiplica o dado
de treino do clone SEM o Pedro gravar mais.

HIPÓTESE (a testar, não garantida): treinar/condicionar o CSM-1B com dado real do Pedro +
dado convertido por FreeSVC melhora a similaridade/robustez. RISCO conhecido (da pesquisa):
sintético-convertido DEGRADA similaridade — por isso é EXPERIMENTO, com gate de eval.

PLANO DA SPRINT (rodar no pod, não bloqueia a coleta):
  1) clonar FreeSVC:            git clone https://github.com/freds0/FreeSVC  (ou repo AKCIT)
  2) baixar checkpoint + deps:  pip install -r requirements.txt
  3) referência-alvo:           3-10s limpos da voz do Pedro (data/raw/elevenlabs2024/segments)
  4) fonte a converter:         N horas de pt-BR (começar com 50-100 clipes de CML-TTS/NURC)
  5) converter:                 cada fonte → voz do Pedro  (ver convert() abaixo, a preencher
                                com a API real do FreeSVC após clonar o repo)
  6) montar dataset aug:        runpod_samples/aug_freesvc/  (wav + transcrição herdada da fonte)
  7) GATE de eval:              comparar 3 condições no rate_app + métricas objetivas:
                                  (a) CSM-1B só com dado real do Pedro
                                  (b) + dado FreeSVC
                                  (c) baseline (Qwen3/XTTS)
                                medir: voz/similaridade, naturalidade, WER, e (quando houver)
                                a métrica de prosódia da linha da Sandra Aluísio.
  DECISÃO: só entra no treino "de verdade" se (b) > (a) na eval HUMANA de similaridade.

Este arquivo é o SCAFFOLD (o pipe). A função convert() vira chamada real depois de clonar o repo.
"""
import argparse, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "runpod_samples" / "aug_freesvc"
REF_DIR = REPO / "data/raw/elevenlabs2024/segments"   # voz do Pedro (referência-alvo)


def convert(source_wav, target_ref_wav, out_wav, model=None):
    """Converte source_wav pra a voz de target_ref_wav. Preencher com a API do FreeSVC
    após `git clone` do repo (provável: model.convert(source, reference) → wav 24k)."""
    raise NotImplementedError(
        "Clonar o FreeSVC (github freds0/AKCIT) e plugar a chamada real aqui. "
        "Scaffold pronto: refs em REF_DIR, saída em OUT.")


def main():
    ap = argparse.ArgumentParser(description="FreeSVC augment (scaffold da sprint)")
    ap.add_argument("--sources", help="dir com fala pt-BR fonte a converter (CML/NURC)")
    ap.add_argument("--ref", default=None, help="wav de referência da voz do Pedro")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--dry", action="store_true", default=True, help="só mostra o plano (default)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print("FreeSVC augment — SCAFFOLD (próxima sprint).")
    print(f"  referência-alvo (voz do Pedro): {a.ref or (str(REF_DIR)+'/<um clipe limpo>')}")
    print(f"  fontes a converter: {a.sources or '(definir: subset CML-TTS / NURC-SP)'}")
    print(f"  saída: {OUT}")
    print("  PRÓXIMO: clonar o repo FreeSVC + plugar convert(); rodar no pod; GATE de eval humana.")


if __name__ == "__main__":
    main()
