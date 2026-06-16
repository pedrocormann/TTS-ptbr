"""Investiga: o zero-pad a 12s está sendo TREINADO nos labels? (causa do balbucio)"""
import os, json
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_bateria as tb
tb.heavy_imports()
import torch
from datasets import Dataset, Audio

rows = [json.loads(l) for l in open('/workspace/pedro_data/transcribed.jsonl')]
short = [r for r in rows if 2.5 < float(r.get('dur_s', 0)) < 4.5][:1]
print("CLIPE:", round(float(short[0]['dur_s']), 1), "s ·", short[0]['text'][:45])
for r in short:
    r['audio'] = os.path.join('/workspace/pedro_data/segments', os.path.basename(r['audio']))
ds = Dataset.from_list([{'audio': r['audio'], 'text': r['text']} for r in short]).cast_column('audio', Audio(24000))
_, processor = tb.load_csm()
o = tb.build_prep(processor, 288001)(ds[0], 0)

print("=== CAMPOS ===")
for k, v in o.items():
    t = v if torch.is_tensor(v) else torch.as_tensor(v)
    print(f"  {k}: shape={tuple(t.shape)} dtype={t.dtype}")

lab = o['labels'] if torch.is_tensor(o['labels']) else torch.as_tensor(o['labels'])
print("=== LABELS ===")
print(" shape", tuple(lab.shape), "| total", lab.numel(),
      "| -100(masked)", int((lab == -100).sum()), "| TREINÁVEIS", int((lab != -100).sum()))
# áudio real ~3.5s ≈ ~88-150 frames. Se TREINÁVEIS do áudio ≈ 300+ → pad está sendo treinado = balbucio
print("DICA: clipe de ~3.5s deveria treinar poucos frames de áudio; se treináveis >> isso, o pad de silêncio está sendo aprendido.")
sys.stdout.flush()
import os as _o
_o._exit(0)
