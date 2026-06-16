#!/usr/bin/env python3
"""Agrega todos os resultados do grid overnight num relatório mestre (OVERNIGHT_REPORT.md).
Lê os BATERIA_parcial_*.json de cada run e monta uma tabela ordenada por WER."""
import json, glob

ROOT = '/workspace/TTS-ptbr-data/runs'
rows = []
for f in sorted(glob.glob(f'{ROOT}/BATERIA_parcial_*.json')):
    try:
        for r in json.load(open(f)):
            rows.append(r)
    except Exception as e:
        print(f"skip {f}: {e}")

rows.sort(key=lambda x: x.get('wer', 9))
out = [
    "# Relatório overnight — grid CSM pt-BR",
    "",
    f"{len(rows)} runs concluídos. Ordenado por WER (menor = melhor; <100% = inteligível).",
    "Áudios em cada `runs/battery_*/gen/*.wav`.",
    "",
    "| run | fonte | LR | rank | clipes | steps | min | WER |",
    "|---|---|---|---|---|---|---|---|",
]
for r in rows:
    wer = r.get('wer', 0)
    out.append(f"| {r.get('tag','-')} | {r.get('source','?')} | {r.get('lr','?')} | "
               f"{r.get('rank','?')} | {r.get('clips','?')} | {r.get('steps','?')} | "
               f"{r.get('min','?')} | {wer*100:.0f}% |")

if rows:
    b = rows[0]
    out += ["", f"🏆 **Melhor:** `{b.get('tag')}` — WER {b.get('wer',0)*100:.0f}%, "
            f"fonte {b.get('source')}, LR {b.get('lr')}, rank {b.get('rank')}, {b.get('min')}min."]
    # leituras rápidas por eixo
    by_src = {}
    for r in rows:
        by_src.setdefault(r.get('source'), []).append(r.get('wer', 9))
    out.append("")
    out.append("**Por fonte (melhor WER):** " + " · ".join(
        f"{s}={min(w)*100:.0f}%" for s, w in by_src.items()))
else:
    out.append("\n(nenhum run concluiu — ver overnight.log)")

txt = "\n".join(out)
open(f'{ROOT}/OVERNIGHT_REPORT.md', 'w').write(txt + "\n")
print(f"relatório salvo: {ROOT}/OVERNIGHT_REPORT.md ({len(rows)} runs)\n")
print(txt)
