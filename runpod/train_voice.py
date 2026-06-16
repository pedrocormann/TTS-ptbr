#!/usr/bin/env python3
"""Estágio B — finetune da VOZ DO PEDRO sobre uma BASE-PT.

Carrega o CSM, FUNDE o adapter BASE-PT (--base-adapter, o vencedor do grid de língua),
adiciona um LoRA novo e treina nos clipes do Pedro (transcribed.jsonl, 362 segmentos).
No fim, gera as 14 frases do benchmark NA VOZ DELE (usando um clipe do Pedro como
contexto) → é isso que a gente ouve pra julgar se ficou parecido.

Reusa as funções já validadas do train_bateria.py (load_csm, build_prep, add_lora, etc.).

Uso:
  python runpod/train_voice.py --base-adapter /workspace/.../battery_A1_cml_cml_long/final \
      --data-dir /workspace/pedro_data --out /workspace/TTS-ptbr-data/runs/stage_b_pedro
"""
import argparse, os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_bateria as tb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-adapter', default='', help='adapter BASE-PT a fundir antes (vazio = CSM cru)')
    ap.add_argument('--data-dir', default='/workspace/pedro_data')
    ap.add_argument('--out', default='/workspace/TTS-ptbr-data/runs/stage_b_pedro')
    ap.add_argument('--lr', type=float, default=1e-4)
    ap.add_argument('--lora-r', type=int, default=64)
    ap.add_argument('--minutes', type=int, default=60)
    ap.add_argument('--load-only', action='store_true', help='só valida o dataset (sem treinar)')
    args = ap.parse_args()

    assert os.environ.get('HF_TOKEN'), '❌ HF_TOKEN ausente'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
    os.makedirs(args.out, exist_ok=True)
    tb.heavy_imports()
    from datasets import Dataset, Audio
    import torch

    # --- dataset do Pedro (jsonl local) ---
    rows = [json.loads(l) for l in open(f'{args.data_dir}/transcribed.jsonl', encoding='utf-8') if l.strip()]
    data = []
    for r in rows:
        wav = os.path.join(args.data_dir, 'segments', os.path.basename(r['audio']))
        if os.path.exists(wav) and str(r.get('text', '')).strip():
            data.append({'audio': wav, 'text': str(r['text']).strip()})
    print(f"Pedro: {len(data)}/{len(rows)} clipes com áudio+texto")
    assert data, '❌ nenhum clipe válido — confere /workspace/pedro_data/segments e transcribed.jsonl'
    raw = Dataset.from_list(data).cast_column('audio', Audio(sampling_rate=24000))
    raw = raw.filter(lambda ex: 1.0 <= len(ex['audio']['array']) / 24000 <= 20 and len(str(ex['text']).split()) >= 2)
    raw = raw.shuffle(seed=42)
    print(f"após filtro: {len(raw)} clipes")
    if args.load_only:
        print(f"✓ load-only OK · sample: {raw[0]['text'][:50]!r} · {len(raw[0]['audio']['array'])} samples")
        sys.stdout.flush(); os._exit(0)

    MAX_AUDIO = 288000 + 1

    # --- modelo: CSM + funde BASE-PT + LoRA novo ---
    model, processor = tb.load_csm()
    if args.base_adapter and os.path.isdir(args.base_adapter):
        from peft import PeftModel
        print(f"fundindo BASE-PT: {args.base_adapter}")
        model = PeftModel.from_pretrained(model, args.base_adapter).merge_and_unload()
        model = model.to('cuda'); model.train(); model.codec_model.eval()
    else:
        print("⚠️ sem BASE-PT (CSM cru) — voz entra mas português vem só dos 48min do Pedro")

    ds = raw.map(tb.build_prep(processor, MAX_AUDIO), with_indices=True,
                 remove_columns=raw.column_names, desc='tok')
    model = tb.add_lora(model, args.lora_r, args.lora_r)

    # --- treino (time-capped, warmup fixo — mesmos fixes do grid) ---
    CSMTrainer = tb.make_trainer_cls()
    from transformers import TrainingArguments, TrainerCallback
    class TimeCap(TrainerCallback):
        def __init__(s, m): s.dl = time.time() + m * 60
        def on_step_end(s, a, st, c, **k):
            if time.time() > s.dl: c.should_training_stop = True
            return c
    tr = CSMTrainer(model=model, train_dataset=ds, args=TrainingArguments(
        per_device_train_batch_size=2, gradient_accumulation_steps=16,
        num_train_epochs=99, learning_rate=args.lr, lr_scheduler_type='cosine', warmup_steps=20,
        bf16=tb.BF16, fp16=not tb.BF16, logging_steps=10, optim='adamw_8bit', weight_decay=0.01,
        seed=3407, output_dir=args.out, report_to='none', save_steps=200, save_total_limit=1,
        remove_unused_columns=False), callbacks=[TimeCap(args.minutes)])
    tr.train()
    model.save_pretrained(f'{args.out}/final'); processor.save_pretrained(f'{args.out}/final')

    # --- gera as 14 frases NA VOZ DO PEDRO (clipe dele = contexto) ---
    wer = tb.eval_wer(model, processor, raw[0], args.out)
    json.dump({'stage': 'B', 'base_adapter': args.base_adapter, 'clips': len(raw),
               'lr': args.lr, 'rank': args.lora_r, 'steps': tr.state.global_step, 'wer': wer},
              open(f'{args.out}/stage_b_result.json', 'w'), ensure_ascii=False, indent=1)
    print(f"✅ STAGE B: WER {wer:.1%} · áudios (voz do Pedro) em {args.out}/gen/ · adapter em {args.out}/final")
    sys.stdout.flush(); os._exit(0)


if __name__ == '__main__':
    main()
