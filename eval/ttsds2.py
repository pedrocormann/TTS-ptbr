"""
TTSDS2 — métrica DISTRIBUTIVA principal de qualidade (REPLAN 2026-06-10, eval v2).

Por quê: única métrica (de 16) com Spearman>0,5 vs MOS humano em todos os
domínios; validada multilíngue (14 línguas); não depende de MOS de treino —
compara a DISTRIBUIÇÃO do áudio gerado contra fala REAL de referência
(arXiv 2506.19441; código MIT github.com/ttsds/ttsds). UTMOS fica rebaixado a
número histórico (não calibrado pt-BR, instável entre runs — dossiê 30 §4).

Uso (Colab/GPU recomendado — baixa vários modelos-sonda na 1ª execução):
  pip install ttsds
  python -m eval.ttsds2 --gen-dir gen/ --ref-dir ref_pedro/ [--multilingual]

ref-dir = fala REAL (clipes do Pedro). gen-dir = áudio sintetizado.
Os diretórios não precisam ter os mesmos textos nem o mesmo nº de arquivos.
Saída: _ttsds2_results.csv no gen-dir + score agregado no stdout.
API verificada em 2026-06-10 (README do repo).
"""
import argparse
from pathlib import Path


def run(gen_dir: str, ref_dir: str, multilingual: bool = True):
    from ttsds import BenchmarkSuite
    from ttsds.util.dataset import DirectoryDataset

    out_csv = str(Path(gen_dir) / "_ttsds2_results.csv")
    suite = BenchmarkSuite(
        datasets=[DirectoryDataset(gen_dir, name=Path(gen_dir).name)],
        reference_datasets=[DirectoryDataset(ref_dir, name="reference")],
        write_to_file=out_csv,
        skip_errors=True,
        include_environment=False,
        multilingual=multilingual,
    )
    suite.run()
    agg = suite.get_aggregated_results()
    return agg, out_csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", required=True, help="áudios sintetizados (.wav)")
    ap.add_argument("--ref-dir", required=True, help="fala REAL de referência (.wav)")
    ap.add_argument("--multilingual", action="store_true", default=True)
    ap.add_argument("--no-multilingual", dest="multilingual", action="store_false")
    a = ap.parse_args()
    agg, out_csv = run(a.gen_dir, a.ref_dir, a.multilingual)
    print(agg)
    print(f"-> {out_csv}")


if __name__ == "__main__":
    main()
