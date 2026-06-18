#!/usr/bin/env python3
"""Re-transcreve o clean-v1 (262) com faster-whisper medium no CPU. Resumível.
Saída: retranscribed.jsonl {id, text_v2} — vira a sugestão 'ASR-v2' na aba Curar."""
import json, os, sys, time
from faster_whisper import WhisperModel
SRC = 'data/raw/elevenlabs2024/transcribed_clean_auto.jsonl'
OUT = 'data/raw/elevenlabs2024/retranscribed.jsonl'
rows = [json.loads(l) for l in open(SRC) if l.strip()]
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)['id'] for l in open(OUT) if l.strip()}
todo = [r for r in rows if r['id'] not in done]
print(f"re-transcrevendo {len(todo)}/{len(rows)} (medium, CPU)...", flush=True)
m = WhisperModel('medium', device='cpu', compute_type='int8')
t0 = time.time()
with open(OUT, 'a') as f:
    for i, r in enumerate(todo):
        p = r['audio'] if os.path.exists(r['audio']) else 'data/raw/elevenlabs2024/segments/' + os.path.basename(r['audio'])
        try:
            segs, _ = m.transcribe(p, language='pt', beam_size=5)
            text = ' '.join(s.text.strip() for s in segs).strip()
        except Exception as e:
            text = ''; print(f"  ! {r['id']} erro: {e}", flush=True)
        f.write(json.dumps({'id': r['id'], 'text_v2': text}, ensure_ascii=False) + '\n'); f.flush()
        if (i+1) % 20 == 0 or i == 0:
            el = time.time()-t0; print(f"[{i+1}/{len(todo)}] {el/ (i+1):.1f}s/clipe · ETA {el/(i+1)*(len(todo)-i-1)/60:.0f}min", flush=True)
print(f"✓ done em {(time.time()-t0)/60:.0f}min → {OUT}", flush=True)
