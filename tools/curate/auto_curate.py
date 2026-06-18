#!/usr/bin/env python3
"""Passe AUTOMÁTICO de curadoria (sem GPU, stdlib) — primeiro filtro do dataset da voz.
NÃO substitui a revisão humana (não conserta transcrição do Whisper nem pega 2-vozes sutil),
mas derruba o lixo determinístico (fragmento, vazio, silêncio, clipping, duração ruim) e
gera um clean-v1 + relatório do que revisar. Erros de transcrição => re-transcrever (pod/ASR)."""
import json, wave, math, re, os
from pathlib import Path
SRC = Path('data/raw/elevenlabs2024/segments/transcribed.jsonl')
OUT = Path('data/raw/elevenlabs2024/transcribed_clean_auto.jsonl')
REP = Path('tools/curate/curation_report.md')

def audio_stats(p):
    try:
        w = wave.open(p, 'rb'); sw, ch, fr, n = w.getsampwidth(), w.getnchannels(), w.getframerate(), w.getnframes()
        raw = w.readframes(n); w.close()
        step = ch * sw * 40  # decima: ~1 amostra a cada 40 frames
        peak = 0; sq = 0.0; c = 0; full = float(1 << (8*sw - 1))
        for i in range(0, len(raw) - sw, step):
            v = int.from_bytes(raw[i:i+sw], 'little', signed=True)
            a = abs(v); peak = a if a > peak else peak; sq += v*v; c += 1
        if not c: return None
        return {'peak': peak/full, 'rms': math.sqrt(sq/c)/full, 'fr': fr, 'dur': n/fr}
    except Exception as e:
        return {'err': str(e)}

def txt(r): return (r.get('text') or '').strip()
def garbage(t):
    toks = t.lower().split()
    if len(toks) >= 4 and len(set(toks)) <= 2: return True   # repetição
    if t and len(t) <= 2: return True
    return False

rows = [json.loads(l) for l in open(SRC) if l.strip()]
kept, dropped, flagged = [], [], []
for r in rows:
    t = txt(r); w = len(t.split()); dur = r.get('dur_s')
    p = r['audio'] if os.path.exists(r['audio']) else str(SRC.parent / os.path.basename(r['audio']))
    st = audio_stats(p) if os.path.exists(p) else {'err': 'sem wav'}
    reasons = []
    if not t: reasons.append('vazio')
    if w and w < 3: reasons.append(f'fragmento ({w} pal)')
    if dur is not None and dur < 1.0: reasons.append(f'curto {dur:.1f}s')
    if dur is not None and dur > 12.0: reasons.append(f'longo {dur:.1f}s')
    if garbage(t): reasons.append('repetição/garbage')
    if st and 'err' not in st:
        if st['rms'] < 0.004: reasons.append(f'quase-silêncio (rms {st["rms"]:.3f})')
        if st['peak'] > 0.995: reasons.append(f'clipping (peak {st["peak"]:.3f})')
    elif st and 'err' in st: reasons.append('wav ilegível: ' + st['err'])
    if reasons:
        dropped.append((r['id'], '; '.join(reasons), t[:60]))
        continue
    # mantidos — mas marca suspeitos pra spot-check humano
    sus = []
    if re.search(r'\d', t): sus.append('tem número (alvo de re-transcrição)')
    if dur is not None and dur > 10.5: sus.append(f'quase no teto ({dur:.1f}s)')
    if w > 40: sus.append(f'run-on ({w} pal)')
    if sus: flagged.append((r['id'], '; '.join(sus)))
    kept.append(r)

with open(OUT, 'w') as f:
    for r in kept: f.write(json.dumps(r, ensure_ascii=False) + '\n')

tot_dur_keep = sum(r.get('dur_s', 0) for r in kept)
lines = [f"# Curadoria automática (passe 1, sem GPU) — {SRC.name}", "",
         f"- **{len(rows)}** clipes → **{len(kept)} mantidos** ({tot_dur_keep/60:.1f} min) · **{len(dropped)} descartados** · **{len(flagged)} a revisar (spot-check)**",
         "- ⚠️ Este passe NÃO conserta transcrição (Whisper ~5-10% erro) nem pega 2-vozes/corte sutil — isso é re-transcrição (pod/ASR) + teu ouvido nos flaggados.", "",
         "## Descartados (lixo determinístico)"]
for i, (id_, why, t) in enumerate(dropped):
    lines.append(f"- `{id_}` — {why}" + (f' · "{t}"' if t else ''))
lines += ["", f"## A revisar / spot-check ({len(flagged)} mantidos, mas suspeitos)"]
for id_, why in flagged: lines.append(f"- `{id_}` — {why}")
REP.write_text('\n'.join(lines), encoding='utf-8')
print(f"✓ {len(rows)} → {len(kept)} mantidos / {len(dropped)} descartados / {len(flagged)} a revisar")
print(f"  clean-v1: {OUT}  ({tot_dur_keep/60:.1f} min)")
print(f"  relatório: {REP}")
print("\n  descartes por motivo:")
from collections import Counter
mc = Counter(why.split(';')[0].split('(')[0].strip() for _, why, _ in dropped)
for k, v in mc.most_common(): print(f"    {v:>3}× {k}")
