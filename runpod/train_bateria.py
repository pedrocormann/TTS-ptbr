#!/usr/bin/env python3
"""
Bateria de língua pt-BR (Estágio A do CSM) — PORT do notebook 1b pra RunPod.

Mesma lógica do `notebooks/1b_bateria_lingua_overnight.ipynb`, com o MIOLO de
treino preservado verbatim (todos os fixes da maratona de debug). Só muda o que
era específico do Colab:
  - Google Drive  → Network Volume (OUT_ROOT, default /workspace/TTS-ptbr-data)
  - Colab Secrets → env var HF_TOKEN
  - pip install   → runpod/setup.sh (rodar 1x por pod)

Roda headless e é PARAMETRIZÁVEL por CLI (pra eu/Claude dirigir via SSH sem
reeditar arquivo). Exemplos:

  # bateria completa (preflight + A1/A3/A2), igual ao notebook:
  python runpod/train_bateria.py

  # só um experimento, LR mais frio, 30 min, e empurra resultado pro HF Hub:
  python runpod/train_bateria.py --experiments A1_cml --lr 2e-5 --per-exp-min 30 \
      --push-hub pedrocormann/tts-ptbr-bateria

  # só validar o ambiente (1 step + 1 geração, ~3 min):
  python runpod/train_bateria.py --preflight-only

Storage: o disco do container é EFÊMERO. Sempre aponte OUT_ROOT pro Network
Volume (/workspace) E/OU use --push-hub pra não perder o resultado ao desligar.
"""
import argparse, os, sys, time, json, gc, hashlib, pathlib, traceback

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent   # raiz do repo clonado
MODEL_ID = 'unsloth/csm-1b'   # mirror Apache ungated (mesmos pesos do sesame/csm-1b)


# ───────────────────────── CONFIG (CLI > env > default) ─────────────────────────
def parse_args():
    g = lambda k, d: os.environ.get(k, d)
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out-root', default=g('OUT_ROOT', '/workspace/TTS-ptbr-data'),
                   help='raiz de saída (use o Network Volume /workspace)')
    p.add_argument('--experiments', default=g('EXPERIMENTS', 'A1_cml,A3_tagarela,A2_mix'),
                   help='lista separada por vírgula: A1_cml,A3_tagarela,A2_mix')
    p.add_argument('--time-budget-min', type=int, default=int(g('TIME_BUDGET_MIN', 160)))
    p.add_argument('--per-exp-min', type=int, default=int(g('PER_EXP_MIN', 50)))
    p.add_argument('--lora-r', type=int, default=int(g('LORA_R', 64)))
    p.add_argument('--lora-alpha', type=int, default=int(g('LORA_ALPHA', 64)))
    p.add_argument('--lr', type=float, default=float(g('LR', 5e-5)))
    p.add_argument('--batch', type=int, default=int(g('BATCH', 2)))
    p.add_argument('--accum', type=int, default=int(g('ACCUM', 16)))
    p.add_argument('--skip-preflight', action='store_true')
    p.add_argument('--preflight-only', action='store_true')
    p.add_argument('--push-hub', default=g('PUSH_HUB', ''),
                   help='repo_id do HF Hub p/ empurrar resultados+adapters (ex: user/tts-ptbr-bateria)')
    p.add_argument('--run-tag', default=g('RUN_TAG', ''),
                   help='sufixo único pro folder/resultados — evita colisão entre runs do grid overnight')
    return p.parse_args()


# experimentos disponíveis (mesma matriz do notebook)
# clips por experimento (não horas): ~8000 clipes ≈ baixa em ~2-4 min e dá ~1.5-2 epochs
# num run de 50min (baixo overfit, comparação justa). Igual entre fontes = ranking justo.
ALL_EXPS = {
    'A1_cml':      {'name': 'A1_cml',      'source': 'cml',      'clips': 8000},
    'A3_tagarela': {'name': 'A3_tagarela', 'source': 'tagarela', 'clips': 8000},
    'A2_mix':      {'name': 'A2_mix',      'source': 'mix',      'clips': 8000},
}


# ─────────────── imports pesados só depois do parse (falha rápido sem GPU) ───────────────
def heavy_imports():
    global load_dataset, Audio, Dataset, concatenate_datasets
    global AutoProcessor, CsmForConditionalGeneration, TrainingArguments, Trainer, TrainerCallback
    global LoraConfig, get_peft_model, np, torch, BF16
    from datasets import load_dataset, Audio, Dataset, concatenate_datasets
    from transformers import (AutoProcessor, CsmForConditionalGeneration, TrainingArguments,
                              Trainer, TrainerCallback)
    from peft import LoraConfig, get_peft_model
    import numpy as np, torch
    BF16 = torch.cuda.is_bf16_supported()   # A100/L4/4090 = True (bf16); só T4/P100 cairia pra fp16


# ───────────────────────── helpers (VERBATIM do notebook 1b) ─────────────────────────
def _stream_take(name, cfg, text_key, n_clips):
    """STREAMING RÁPIDO: itera SEM decodificar o áudio (Audio(decode=False) → só lê os
    bytes) e pega `n_clips` clipes. Decodificar ao iterar (pra medir duração em segundos)
    era o gargalo — levava >10min pra 30h. Com decode=False a coleta é só I/O de rede
    (~minutos); o áudio é decodificado depois, na tokenização (onde já era de qualquer jeito)."""
    st = load_dataset(name, cfg, split='train', streaming=True) if cfg \
         else load_dataset(name, split='train', streaming=True)
    st = st.cast_column('audio', Audio(decode=False))
    rows = []
    for ex in st:
        txt = ex.get(text_key) or ex.get('text') or ex.get('sentence') or ex.get('transcript') or ''
        rows.append({'audio': ex['audio'], 'text': txt})
        if len(rows) >= n_clips:
            break
    return rows


def load_source(source, clips):
    if source == 'cml':
        rows = _stream_take('ylacombe/cml-tts', 'portuguese', 'text', clips)
    elif source == 'mix':
        rows = _stream_take('ylacombe/cml-tts', 'portuguese', 'text', clips // 2)                      # metade CML
        rows += _stream_take('facebook/multilingual_librispeech', 'portuguese', 'transcript', clips // 2)  # metade MLS
    elif source == 'tagarela':
        rows = _stream_take('freds0/TAGARELA', None, 'sentence', clips)
    ds = Dataset.from_list(rows).cast_column('audio', Audio(sampling_rate=24000)).shuffle(seed=42)
    return ds


def build_prep(processor, max_audio):
    CLIP = 288000   # 12s @ 24kHz — TODO áudio vira EXATAMENTE isto (crop + zero-pad). Sem isso,
                    # áudio curto/variável (TAGARELA/MLS/voz do Pedro) dá nº de frames do codec ≠
                    # nº de placeholders → "shape mismatch [300,2048] vs [290,2048]" no forward.
    def spk(ex, i):
        return str(int(hashlib.md5(str(ex.get('speaker_id', i)).encode()).hexdigest(), 16) % 10)
    def prep(ex, idx):
        arr = np.asarray(ex['audio']['array'], dtype=np.float32)[:CLIP]
        if arr.shape[0] < CLIP:
            arr = np.pad(arr, (0, CLIP - arr.shape[0]))   # zero-pad clipes curtos → comprimento fixo
        conv = [{'role': spk(ex, idx), 'content': [{'type':'text','text':str(ex['text']).strip()},
                                                   {'type':'audio','path':arr}]}]
        o = processor.apply_chat_template(conv, tokenize=True, return_dict=True, output_labels=True,
            text_kwargs={'padding':'max_length','max_length':256,'truncation':True,'pad_to_multiple_of':8,'padding_side':'right'},
            audio_kwargs={'sampling_rate':24000},   # áudio já é uniforme → sem padding aqui
            common_kwargs={'return_tensors':'pt'})
        return {k: v[0] for k, v in o.items()}
    return prep


def load_csm():
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model, _info = CsmForConditionalGeneration.from_pretrained(
        MODEL_ID, output_loading_info=True)  # float32: o codec Mimi gera float32, então o modelo
    # NÃO pode ser bf16 (mismatch no merge). bf16=True no Trainer faz autocast.
    _crit = [k for k in _info.get('missing_keys', []) if 'embed_audio' in k]
    assert not _crit, f'❌ pesos de ÁUDIO faltando no load ({_crit}) — transformers incompatível com o checkpoint'
    model = model.to('cuda')
    model.train(); model.codec_model.eval()    # codec Mimi congelado (exemplo oficial HF)
    return model, processor


def add_lora(model, r, alpha):
    cfg = LoraConfig(r=r, lora_alpha=alpha, lora_dropout=0.0, bias='none',
        target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    return model


def make_trainer_cls():
    class CSMTrainer(Trainer):   # garante o codec Mimi sempre em eval (não treina)
        def training_step(self, model, inputs, *args, **kwargs):
            bm = model.get_base_model() if hasattr(model, 'get_base_model') else model
            if hasattr(bm, 'codec_model'): bm.codec_model.eval()
            return super().training_step(model, inputs, *args, **kwargs)
    return CSMTrainer


def eval_wer(model, processor, ref, out):
    import soundfile as sf, jiwer
    from faster_whisper import WhisperModel
    model.eval()
    bench = [json.loads(l) for l in open(REPO_ROOT/'eval/benchmark_ptbr.jsonl', encoding='utf-8') if l.strip()]
    gd = pathlib.Path(f'{out}/gen'); gd.mkdir(exist_ok=True, parents=True)
    for i, it in enumerate(bench):
        conv = [{'role':'0','content':[{'type':'text','text':str(ref['text'])},{'type':'audio','path':ref['audio']['array']}]},
                {'role':'0','content':[{'type':'text','text':it['text']}]}]
        inp = processor.apply_chat_template(conv, tokenize=True, return_dict=True).to('cuda')
        with torch.no_grad():
            au = model.generate(**inp, output_audio=True, max_new_tokens=375)
        sf.write(gd / f"{it.get('id', i)}.wav", au[0].to(torch.float32).cpu().numpy(), 24000)
    asr = WhisperModel('small', device='cpu', compute_type='int8')  # cpu: evita crash cuDNN
    norm = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(), jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
    ws = []
    for i, it in enumerate(bench):
        segs, _ = asr.transcribe(str(gd / f"{it.get('id', i)}.wav"), language='pt')
        hyp = ' '.join(s.text.strip() for s in segs).strip()
        ws.append(jiwer.wer(norm(it['text']), norm(hyp)) if hyp else 1.0)
    del asr; gc.collect(); torch.cuda.empty_cache()
    model.train()
    return round(float(np.mean(ws)), 3)


def preflight(cfg):
    print('🔍 PREFLIGHT — 4 exemplos, 1 step de treino (HF puro)…')
    CSMTrainer = make_trainer_cls()
    st = load_dataset('ylacombe/cml-tts', 'portuguese', split='train', streaming=True)
    pool = []
    for ex in st:
        pool.append({'audio': ex['audio'], 'text': ex['text']})
        if len(pool) >= 60: break
    pool.sort(key=lambda r: len(r['text']))   # pega curtos E longos: testa o collator de verdade
    rows = pool[:2] + pool[-2:]
    raw = Dataset.from_list(rows).cast_column('audio', Audio(sampling_rate=24000))
    max_audio = 288000 + 1   # 12s fixo
    model, processor = load_csm()
    ds = raw.map(build_prep(processor, max_audio), with_indices=True, remove_columns=raw.column_names)
    model = add_lora(model, 8, 16)
    tr = CSMTrainer(model=model, train_dataset=ds, args=TrainingArguments(
        per_device_train_batch_size=cfg.batch, gradient_accumulation_steps=1, max_steps=1,
        bf16=BF16, fp16=not BF16, logging_steps=1, optim='adamw_8bit',
        output_dir='/tmp/preflight', report_to='none', remove_unused_columns=False))
    tr.train()
    import soundfile as _sf
    model.eval()
    _conv = [{'role':'0','content':[{'type':'text','text':str(raw[0]['text'])},{'type':'audio','path':raw[0]['audio']['array']}]},
             {'role':'0','content':[{'type':'text','text':'Teste rápido de geração.'}]}]
    _inp = processor.apply_chat_template(_conv, tokenize=True, return_dict=True).to('cuda')
    with torch.no_grad():
        _au = model.generate(**_inp, output_audio=True, max_new_tokens=64)
    assert _au[0].shape[-1] > 0, 'geração retornou vazio'
    del model, processor, tr, ds, raw; gc.collect(); torch.cuda.empty_cache()
    print('✅ PREFLIGHT PASSOU — treino E geração OK. A bateria pode rodar segura.')


def run_experiment(exp, deadline_global, cfg):
    CSMTrainer = make_trainer_cls()
    tag = f"_{cfg.run_tag}" if cfg.run_tag else ""
    name, out = exp['name'], f"{cfg.out_root}/runs/battery_{exp['name']}{tag}"
    os.makedirs(out, exist_ok=True); t0 = time.time()
    print(f"\n{'='*64}\n▶ {name}  ({exp['source']}, {exp['clips']} clipes)  {time.strftime('%H:%M')}\n{'='*64}")
    raw = load_source(exp['source'], exp['clips'])
    raw = raw.filter(lambda ex: 1.5 <= len(ex['audio']['array'])/24000 <= 20 and len(str(ex['text']).split()) >= 3)
    MAX_AUDIO = 288000 + 1   # 12s fixo (áudio cortado a 12s no preprocess)
    print(f"  {len(raw)} clipes · max_audio={MAX_AUDIO/24000:.0f}s")
    model, processor = load_csm()
    ds = raw.map(build_prep(processor, MAX_AUDIO), with_indices=True, remove_columns=raw.column_names, desc='tok')
    model = add_lora(model, cfg.lora_r, cfg.lora_alpha)
    cap_min = min(cfg.per_exp_min, (deadline_global - time.time())/60 - 8)
    if cap_min < 5:
        print("  ⏱ sem tempo — pulando"); del model, processor, ds, raw; gc.collect(); torch.cuda.empty_cache(); return None
    print(f"  batch {cfg.batch}×{cfg.accum} (efetivo {cfg.batch*cfg.accum}) · cap {cap_min:.0f}min · LR {cfg.lr}")
    class TimeCap(TrainerCallback):
        def __init__(s, m): s.dl = time.time() + m*60
        def on_step_end(s, a, st, c, **k):
            if time.time() > s.dl: c.should_training_stop = True
            return c
    tr = CSMTrainer(model=model, train_dataset=ds, args=TrainingArguments(
        per_device_train_batch_size=cfg.batch, gradient_accumulation_steps=cfg.accum,
        num_train_epochs=99, learning_rate=cfg.lr, lr_scheduler_type='cosine', warmup_steps=20,
        # warmup_steps FIXO (não ratio): com num_train_epochs=99 o warmup_ratio=0.03 dava
        # 1188 steps de warmup, mas o time-cap para em ~300-540 → a run inteira ficava no
        # warmup com LR ~0 e não aprendia. 20 steps: LR atinge o alvo cedo e treina de verdade.
        bf16=BF16, fp16=not BF16, logging_steps=10, optim='adamw_8bit', weight_decay=0.01,
        seed=3407, output_dir=out, report_to='none', save_steps=100, save_total_limit=1,
        remove_unused_columns=False), callbacks=[TimeCap(cap_min)])
    tr.train()
    steps = tr.state.global_step
    model.save_pretrained(f'{out}/final'); processor.save_pretrained(f'{out}/final')
    wer = eval_wer(model, processor, raw[0], out)
    r = {'name': name, 'source': exp['source'], 'clips': exp['clips'],
         'lr': cfg.lr, 'rank': cfg.lora_r, 'tag': cfg.run_tag or '-',
         'steps': steps, 'wer': wer, 'min': round((time.time()-t0)/60)}
    del model, processor, tr, ds, raw; gc.collect(); torch.cuda.empty_cache()
    print("  ✅", r); return r


def push_to_hub(out_root, repo_id):
    """Safety net: empurra runs/ (results.md + adapters) pro HF Hub (disco do pod é efêmero)."""
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=os.environ['HF_TOKEN'])
        api.create_repo(repo_id, repo_type='model', exist_ok=True, private=True)
        api.upload_folder(folder_path=f'{out_root}/runs', path_in_repo='runs',
                          repo_id=repo_id, repo_type='model')
        print(f"📤 resultados enviados pro HF Hub: {repo_id}/runs")
    except Exception as e:
        print(f"⚠️ push pro Hub falhou (resultado segue salvo em {out_root}/runs): {e}")


# ───────────────────────────────── main ─────────────────────────────────
def main():
    cfg = parse_args()
    assert os.environ.get('HF_TOKEN'), '❌ HF_TOKEN não está no ambiente — `export HF_TOKEN=...` (ver RUNBOOK)'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
    os.makedirs(f'{cfg.out_root}/runs', exist_ok=True)
    heavy_imports()
    print(f"GPU bf16={BF16} · out={cfg.out_root} · exps={cfg.experiments} · LR={cfg.lr}")

    if not cfg.skip_preflight:
        try:
            preflight(cfg)
        except Exception:
            traceback.print_exc()
            print("\n❌ PREFLIGHT FALHOU — não rodo a bateria. (manda o traceback pro Claude)")
            sys.exit(1)
    if cfg.preflight_only:
        print("preflight-only: encerrando."); return

    exps = [ALL_EXPS[n.strip()] for n in cfg.experiments.split(',') if n.strip() in ALL_EXPS]
    _sfx = f"_{cfg.run_tag}" if cfg.run_tag else ""   # sufixo dos arquivos de resultado (grid)
    results = []
    deadline = time.time() + cfg.time_budget_min*60
    for exp in exps:
        if time.time() > deadline - 12*60:
            print(f"⏹ orçamento esgotado — não inicio {exp['name']}"); break
        try:
            r = run_experiment(exp, deadline, cfg)
            if r:
                results.append(r)
                json.dump(results, open(f'{cfg.out_root}/runs/BATERIA_parcial{_sfx}.json','w'), ensure_ascii=False, indent=1)
                if cfg.push_hub: push_to_hub(cfg.out_root, cfg.push_hub)   # salva a cada exp
        except Exception as e:
            traceback.print_exc(); print(f"  ❌ {exp['name']}: {e}")

    print("\n\n" + "="*64 + "\n=== RESULTADOS DA BATERIA ===\n" + "="*64)
    lines = ["| exp | fonte | clipes | steps | WER | min |", "|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: x['wer']):
        ln = f"| {r['name']} | {r['source']} | {r['clips']} | {r['steps']} | {r['wer']:.1%} | {r['min']:.0f} |"
        lines.append(ln); print(ln)
    if results:
        best = min(results, key=lambda x: x['wer'])
        note = f"\n🏆 MELHOR: {best['name']} (WER {best['wer']:.1%}) → BASE-PT do Estágio B (notebook 2)\n"
    else:
        note = "\n(nenhum experimento concluiu — ver erros)\n"
    print(note)
    open(f'{cfg.out_root}/runs/BATERIA_results{_sfx}.md','w').write("# Bateria de língua\n\n" + "\n".join(lines) + "\n" + note)
    print(f"📄 salvo: {cfg.out_root}/runs/BATERIA_results{_sfx}.md")
    if cfg.push_hub: push_to_hub(cfg.out_root, cfg.push_hub)
    # saída dura: o PyAV/torchcodec às vezes segfaulta na finalização do interpretador
    # (depois de tudo salvo). os._exit evita o core dump e garante exit-code 0.
    sys.stdout.flush(); os._exit(0)


if __name__ == '__main__':
    main()
