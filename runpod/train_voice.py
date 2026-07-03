#!/usr/bin/env python3
"""Estágio B — finetune de VOZ sobre uma BASE-PT (RODADA 3: multi-voz).

Carrega o CSM, FUNDE o adapter BASE-PT (--base-adapter, o vencedor do grid de língua),
adiciona um LoRA novo e treina nos clipes do locutor. No fim, gera as 14 frases do
benchmark NA VOZ do locutor (clipe real como contexto) → WER (critério de decisão,
inalterado) + spk_sim + prosódia (só ADICIONAM números, não decidem).

Reusa as funções já validadas do train_bateria.py (load_csm, build_prep, add_lora, etc.).
Receita do grid de 26 arms: lr 5e-5 (1e-4 degrada), r=64, texto raw, base-PT fundida.

Novidades da RODADA 3 (a CLI antiga continua funcionando IGUAL):
  --mix/--mix-dirs  mistura ponderada de N datasets jsonl (ex.: voz=1.0,base=0.15)
  --holdout         held-out REAL (separado antes do treino, nunca treina; eval_loss no fim)
  --speaker         nome do locutor → result json + prefixo do run name
  --push-hub        adapter final + stage_b_result.json pro HF Hub (falha só avisa)
  --tok-cache       cache de tokenização (fingerprint por dados+args; 'off' desliga)
  spk_sim/prosody   métricas por frase gerada (resemblyzer / prosody_scorecard — opcionais,
                    caem pra null se não instalados)

Uso (voz do flywheel, mistura com base pública):
  python runpod/train_voice.py --base-adapter /workspace/.../battery_A1_cml_cml_long/final \
      --mix "voz=1.0,base=0.15" --mix-dirs "voz=data/flywheel/pedro,base=data/base_pt" \
      --speaker pedro --holdout 0.05 --push-hub pedrocormann/tts-ptbr-rodada3 \
      --out /workspace/TTS-ptbr-data/runs/r3_pedro_mix15

Uso antigo (1 fonte, compatível com grid_overnight.sh):
  python runpod/train_voice.py --base-adapter ... --data-dir /workspace/pedro_data \
      --data-file transcribed.jsonl --out /workspace/TTS-ptbr-data/runs/stage_b_pedro
"""
import argparse, glob, hashlib, json, os, random, statistics, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_bateria as tb

HOLDOUT_SEED = 777   # FIXO e independente de --seed: o held-out é o MESMO entre arms/seeds (comparável)
MIX_SEED = 42        # interleave determinístico (mesma família do shuffle histórico seed=42)
TOK_VER = 'tok-v1'   # bump manual se build_prep/max_length/collator mudarem → invalida o cache


# ─────────── caminho de dados: funções PURAS (testáveis sem GPU/datasets) ───────────

def parse_kv(spec, cast=str):
    """'voz=1.0,base=0.15' → {'voz': 1.0, 'base': 0.15} (ordem de inserção preservada)."""
    out = {}
    for part in (spec or '').split(','):
        part = part.strip()
        if not part:
            continue
        assert '=' in part, f'❌ item sem "=": {part!r} (formato: nome=valor,nome=valor)'
        k, v = part.split('=', 1)
        out[k.strip()] = cast(v.strip())
    return out


def load_rows(data_dir, data_file=None):
    """Lê um dataset jsonl ({'audio','text'} + extras ignorados) e resolve o caminho do wav.
    data_file=None → tenta train.jsonl (layout do export_flywheel) e cai pra transcribed.jsonl.
    O 'audio' pode ser: caminho absoluto · relativo ao dir · segments/<basename> (flywheel/pedro_data)."""
    cands = [data_file] if data_file else ['train.jsonl', 'transcribed.jsonl']
    jf = next((os.path.join(data_dir, c) for c in cands if os.path.exists(os.path.join(data_dir, c))), None)
    assert jf, f'❌ nenhum jsonl em {data_dir} (procurei: {", ".join(cands)})'
    rows, miss = [], 0
    for l in open(jf, encoding='utf-8'):
        if not l.strip():
            continue
        r = json.loads(l)
        text = str(r.get('text', '')).strip()
        a = str(r.get('audio', ''))
        paths = [a] if os.path.isabs(a) else [os.path.join(data_dir, a),
                                              os.path.join(data_dir, 'segments', os.path.basename(a))]
        wav = next((p for p in paths if os.path.exists(p)), None)
        if wav and text:
            rows.append({'audio': wav, 'text': text})
        else:
            miss += 1
    print(f"  {os.path.basename(data_dir.rstrip('/')) or data_dir}: {len(rows)} clipes válidos "
          f"({os.path.basename(jf)}{f', {miss} sem áudio/texto' if miss else ''})")
    return rows


def filter_rows(rows, min_s=1.0, max_s=12.0, min_words=2):
    """Mesmos limiares do filtro antigo (1-12s, ≥2 palavras), mas via soundfile.info
    (header: frames/samplerate) SEM decodificar o áudio — em 15h economiza horas por grid."""
    import soundfile as sf
    keep = []
    for r in rows:
        try:
            info = sf.info(r['audio'])
            dur = info.frames / float(info.samplerate)
        except Exception:
            continue   # wav ilegível = fora (mesmo efeito do decode falhar antes)
        if min_s <= dur <= max_s and len(str(r['text']).split()) >= min_words:
            keep.append(r)
    return keep


def split_holdout(rows, frac, seed=HOLDOUT_SEED):
    """Separa o held-out ANTES do treino (seed FIXA ≠ --seed → mesmo held-out em todos os arms).
    Ordena por path antes de embaralhar → estável à ordem do jsonl. Retorna (train, holdout)."""
    if not frac or frac <= 0 or len(rows) < 2:
        return list(rows), []
    order = sorted(range(len(rows)), key=lambda i: rows[i]['audio'])
    random.Random(seed).shuffle(order)
    n_hold = min(max(1, int(len(rows) * frac + 0.5)), len(rows) - 1)
    hold = set(order[:n_hold])
    return [rows[i] for i in range(len(rows)) if i not in hold], [rows[i] for i in sorted(hold)]


def apply_mix(sources, weights, seed=MIX_SEED):
    """Mistura ponderada por AMOSTRAGEM DE ÍNDICES (simples e determinística):
    peso 1.0 = a fonte inteira 1x por época · 0.15 = 15% (subamostra sem reposição, seed fixa)
    · 2.0 = 2 passadas. Réplicas inteiras + resto amostrado; shuffle final = interleave.
    Retorna (rows, composição) — a composição vai pro stage_b_result.json."""
    rng = random.Random(seed)
    mixed, comp = [], {}
    for name in sources:                       # dict preserva a ordem do --mix-dirs
        rows, w = sources[name], float(weights.get(name, 1.0))
        n = max(1, int(len(rows) * w + 0.5)) if (rows and w > 0) else 0
        take = []
        while len(take) < n:
            idx = list(range(len(rows)))
            rng.shuffle(idx)
            take += idx[:n - len(take)]
        mixed += [rows[i] for i in take]
        comp[name] = {'weight': w, 'clips': len(rows), 'used': n}
    rng.shuffle(mixed)                         # interleave (época = este dataset já misturado)
    return mixed, comp


def pick_anchors(rows, k=3):
    """k clipes REAIS do locutor, espalhados (início/meio/fim da lista ordenada por path,
    dedupe de réplicas do mix) — âncoras do spk_sim + contexto da geração do benchmark."""
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: r['audio']):
        if r['audio'] not in seen:
            seen.add(r['audio'])
            uniq.append(r)
    if len(uniq) <= k:
        return uniq
    return [uniq[int(i * (len(uniq) - 1) / (k - 1))] for i in range(k)]


def tok_fingerprint(rows, text_mode, extra=''):
    """Fingerprint do cache de tokenização: modelo + text_mode + versão + a LISTA ORDENADA de
    (path, size, mtime, texto). Qualquer mudança em dado/mix/holdout/front-end → arquivo novo."""
    h = hashlib.sha1(f'{tb.MODEL_ID}|{text_mode}|{TOK_VER}|{extra}'.encode())
    for r in rows:
        try:
            st = os.stat(r['audio'])
            meta = f'{st.st_size}|{int(st.st_mtime)}'
        except OSError:
            meta = '?'
        h.update(f"{r['audio']}|{meta}|{r['text']}\n".encode())
    return h.hexdigest()[:16]


def _load_source(data_dir, data_file=None, holdout_frac=0.0):
    rows = load_rows(data_dir, data_file)
    kept = filter_rows(rows)
    train_rows, hold = split_holdout(kept, holdout_frac)
    print(f"    filtro 1-12s/≥2 palavras: {len(kept)}/{len(rows)} · held-out: {len(hold)}")
    return train_rows, hold


# ─────────── métricas extras do eval (ADITIVAS — o WER continua sendo o critério) ───────────

def compute_spk_sim(gen_dir, anchor_wavs):
    """Similaridade de locutor: cosine(embedding do gerado, média de 3 âncoras REAIS).
    resemblyzer (VoiceEncoder, leve, CPU) é OPCIONAL — sem ele retorna None ('spk_sim': null)."""
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        import numpy as np
        enc = VoiceEncoder('cpu', verbose=False)
        anchors = [enc.embed_utterance(preprocess_wav(p)) for p in anchor_wavs]
        ref = np.mean(anchors, axis=0)
        ref = ref / (np.linalg.norm(ref) + 1e-9)
        per = {}
        for w in sorted(glob.glob(f'{gen_dir}/*.wav')):
            e = enc.embed_utterance(preprocess_wav(w))
            per[os.path.splitext(os.path.basename(w))[0]] = \
                round(float(np.dot(ref, e / (np.linalg.norm(e) + 1e-9))), 4)
        if not per:
            return None
        vals = list(per.values())
        return {'mean': round(float(np.mean(vals)), 4),
                'median': round(float(statistics.median(vals)), 4),
                'n_anchors': len(anchors), 'per_id': per}
    except Exception as e:
        print(f"⚠️ spk_sim indisponível ({type(e).__name__}: {e}) → 'spk_sim': null "
              f"(pip install resemblyzer p/ ativar)")
        return None


def compute_prosody(gen_dir):
    """Scorecard objetiva de prosódia (Aluísio/USP) nos wavs gerados — import POR CAMINHO de
    tools/prosody/prosody_scorecard.py. OPCIONAL: qualquer falha → None ('prosody': null)."""
    try:
        import importlib.util
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'tools', 'prosody', 'prosody_scorecard.py')
        spec = importlib.util.spec_from_file_location('prosody_scorecard', p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rows, per = [], {}
        for w in sorted(glob.glob(f'{gen_dir}/*.wav')):
            r = mod.analyse(w)
            if r:
                rows.append(r)
                per[os.path.splitext(os.path.basename(w))[0]] = {
                    k: r.get(k) for k in ('taxa_fala', 'nuclear_ms', 'sd_silaba_ms', 'pausas_silenciosas')}
        if not rows:
            return None
        def _m(k):
            v = [x[k] for x in rows if x.get(k) is not None]
            return round(statistics.mean(v), 1) if v else None
        agg = {'taxa_fala': _m('taxa_fala'), 'nuclear_ms': _m('nuclear_ms'),
               'sd_silaba_ms': _m('sd_silaba_ms'), 'pausas_media': _m('pausas_silenciosas')}
        agg['flags'] = mod.verdict({'taxa_fala': agg['taxa_fala'], 'nuclear_ms': agg['nuclear_ms'],
                                    'sd_silaba_ms': agg['sd_silaba_ms'],
                                    'pausas_silenciosas_media': agg['pausas_media']})
        agg['per_id'] = per
        return agg
    except Exception as e:
        print(f"⚠️ prosody_scorecard indisponível ({type(e).__name__}: {e}) → 'prosody': null "
              f"(pip install praat-parselmouth p/ ativar)")
        return None


def augment_per_sentence(gen_dir, spk_sim, prosody):
    """Anexa spk_sim/prosody por frase ao per_sentence.jsonl escrito pelo eval_wer."""
    pf = os.path.join(gen_dir, 'per_sentence.jsonl')
    if not os.path.exists(pf):
        return
    rows = [json.loads(l) for l in open(pf, encoding='utf-8') if l.strip()]
    for r in rows:
        sid = str(r.get('id'))
        r['spk_sim'] = (spk_sim or {}).get('per_id', {}).get(sid)
        r['prosody'] = (prosody or {}).get('per_id', {}).get(sid)
    with open(pf, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def push_to_hub(out, repo_id, run_name):
    """Safety net (molde do train_bateria.push_to_hub): adapter final + stage_b_result.json
    (o 'card' do run) pro HF Hub. Falha NÃO derruba o treino — só avisa (disco do pod é efêmero,
    mas o Network Volume segura o resultado)."""
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=os.environ['HF_TOKEN'])
        api.create_repo(repo_id, repo_type='model', exist_ok=True, private=True)
        api.upload_folder(folder_path=f'{out}/final', path_in_repo=f'{run_name}/final',
                          repo_id=repo_id, repo_type='model')
        api.upload_file(path_or_fileobj=f'{out}/stage_b_result.json',
                        path_in_repo=f'{run_name}/stage_b_result.json',
                        repo_id=repo_id, repo_type='model')
        print(f"📤 adapter + result no HF Hub: {repo_id}/{run_name}")
    except Exception as e:
        print(f"⚠️ push pro Hub falhou (adapter segue salvo em {out}/final): {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-adapter', default='', help='adapter BASE-PT a fundir antes (vazio = CSM cru)')
    ap.add_argument('--data-dir', default='/workspace/pedro_data')
    ap.add_argument('--out', default='/workspace/TTS-ptbr-data/runs/stage_b_pedro')
    ap.add_argument('--lr', type=float, default=1e-4)
    ap.add_argument('--lora-r', type=int, default=64)
    ap.add_argument('--minutes', type=int, default=60)
    ap.add_argument('--batch', type=int, default=8, help='per_device batch (era 2; 8 satura a H100)')
    ap.add_argument('--accum', type=int, default=4, help='grad accum (batch*accum = effective; 8*4=32 = recipe validada)')
    ap.add_argument('--workers', type=int, default=8, help='dataloader workers (prefetch p/ não deixar a GPU data-starved)')
    ap.add_argument('--seed', type=int, default=3407, help='seed de TREINO (mix/holdout usam seeds fixas próprias)')
    ap.add_argument('--data-file', default='transcribed.jsonl', help='jsonl de dados dentro de --data-dir (ignorado com --mix)')
    ap.add_argument('--text-mode', default='raw', choices=['raw', 'normalize', 'g2p'],
                    help='front-end de texto aplicado no treino E no eval (TEXT_FN). '
                         'raw=grafema · normalize=número→palavra · g2p=fonemização CharsiuG2P (experimental)')
    ap.add_argument('--load-only', action='store_true', help='só valida o dataset (sem treinar)')
    # ---- RODADA 3 ----
    ap.add_argument('--mix', default='', help='pesos por fonte, ex.: "voz=1.0,base=0.15" (requer --mix-dirs)')
    ap.add_argument('--mix-dirs', default='',
                    help='dirs por fonte, ex.: "voz=data/flywheel/pedro,base=data/base_pt" '
                         '(cada dir: train.jsonl|transcribed.jsonl + segments/)')
    ap.add_argument('--holdout', type=float, default=0.0,
                    help='fração held-out REAL (ex. 0.05): separada ANTES do treino c/ seed fixa, '
                         'nunca treina; eval_loss vai pro stage_b_result.json. As 14 frases seguem como estão.')
    ap.add_argument('--speaker', default='', help='nome do locutor → campo no result json + prefixo do run name')
    ap.add_argument('--push-hub', default=os.environ.get('PUSH_HUB', ''),
                    help='repo_id do HF Hub p/ adapter final + stage_b_result.json (falha de push só avisa)')
    ap.add_argument('--tok-cache', default='',
                    help="dir do cache de tokenização ('' = <dir do --out>/tok_cache · 'off' = desliga, re-tokeniza tudo)")
    args = ap.parse_args()

    assert os.environ.get('HF_TOKEN'), '❌ HF_TOKEN ausente'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
    os.makedirs(args.out, exist_ok=True)
    out_base = os.path.basename(args.out.rstrip('/'))
    run_name = out_base if (not args.speaker or args.speaker in out_base) else f'{args.speaker}_{out_base}'

    # BACKSTOP DE HANG (revisão overnight): TimeCap só capa on_step_end; um step/eval travado
    # em Python nunca para. O SIGALRM mata o processo no teto TOTAL (setup+treino+eval+margem) e
    # grava um sentinel pra a fila resumível AVANÇAR (não re-rodar o mesmo hang). NÃO resolve
    # deadlock C-level de CUDA (aí o watchdog externo via pkill é a rede primária) — é o cinto.
    if not args.load_only:
        import signal
        def _walltime_kill(signum, frame):
            try:
                json.dump({'stage': 'B', 'wer': None, 'killed': 'walltime',
                           'data_file': args.data_file, 'seed': args.seed,
                           'speaker': args.speaker or None, 'mix': args.mix or None},
                          open(f'{args.out}/stage_b_result.json', 'w'))
            finally:
                os._exit(2)
        signal.signal(signal.SIGALRM, _walltime_kill)
        # +28min: setup (~4) + eval WER (~8) + holdout/spk_sim/prosody/push (~10) + margem
        signal.alarm((args.minutes + 28) * 60)

    # --- dados: 1 fonte (CLI antiga, intocada) ou MISTURA PONDERADA (--mix) ---
    if args.mix:
        weights = parse_kv(args.mix, float)
        dirs = parse_kv(args.mix_dirs)
        assert dirs and set(dirs) == set(weights), \
            f'❌ --mix ({sorted(weights)}) e --mix-dirs ({sorted(dirs)}) precisam das MESMAS chaves'
        # holdout POR FONTE, ANTES do peso: réplica do mix nunca vaza pro held-out
        srcs, hold_rows = {}, []
        for name, d in dirs.items():
            srcs[name], ho = _load_source(d, None, args.holdout)
            hold_rows += ho
        data, mix_comp = apply_mix(srcs, weights)
        # âncoras + contexto do eval = a VOZ (fonte 'voz' se existir, senão a de maior peso) —
        # nunca um clipe da base pública (geraria o benchmark na voz errada)
        voice_rows = srcs.get('voz') or srcs[max(weights, key=lambda k: weights[k])]
    else:
        data, hold_rows = _load_source(args.data_dir, args.data_file, args.holdout)
        mix_comp, voice_rows = None, data
    assert data, '❌ nenhum clipe válido pós-filtro — confere jsonl + segments/'
    anchors = pick_anchors(voice_rows)
    print(f"treino: {len(data)} clipes · held-out: {len(hold_rows)} · mix: {mix_comp or '—'} · run: {run_name}")

    tb.heavy_imports()
    from datasets import Dataset, Audio

    raw = Dataset.from_list(data).cast_column('audio', Audio(sampling_rate=24000))
    raw = raw.shuffle(seed=42)   # (filtro de duração já foi feito via soundfile.info, sem decode)

    # --- front-end de texto (TEXT_FN): mesmo texto no TREINO e no EVAL ---
    if args.text_mode == 'raw':
        print("text-mode: raw (grafema pt-BR)")
    elif args.text_mode == 'normalize':
        from recipe import text_frontend
        tb.TEXT_FN = lambda t: text_frontend(t, normalize_numbers=True, g2p=None)
        print(f"text-mode: normalize · ex: {tb.TEXT_FN('liguei pro 0800 e paguei R$ 1.250')!r}")
    elif args.text_mode == 'g2p':
        from recipe import text_frontend
        try:
            from g2p_ptbr import phonemize
            tb.TEXT_FN = lambda t: text_frontend(t, normalize_numbers=True, g2p=phonemize)
            print(f"text-mode: g2p (CharsiuG2P) · ex: {tb.TEXT_FN('eu tô indo pra praia')!r}")
        except Exception as e:
            tb.TEXT_FN = lambda t: text_frontend(t, normalize_numbers=True, g2p=None)
            print(f"⚠️ g2p indisponível ({e}); caí pra normalize")
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
        print("⚠️ sem BASE-PT (CSM cru) — voz entra mas português vem só dos clipes do locutor (WER ~79% no grid)")

    # --- tokenização com CACHE (fingerprint por dados+args): re-rodar o mesmo dado = load instantâneo ---
    cache_dir = None
    tok_kw = {'load_from_cache_file': False}
    if args.tok_cache != 'off':
        cache_dir = args.tok_cache or os.path.join(os.path.dirname(os.path.abspath(args.out.rstrip('/'))), 'tok_cache')
        os.makedirs(cache_dir, exist_ok=True)
        cf = os.path.join(cache_dir, f'tok_{tok_fingerprint(data, args.text_mode, "shuffle42")}.arrow')
        tok_kw = {'cache_file_name': cf, 'load_from_cache_file': True}
        print(f"tok-cache: {cf} {'(REUSO)' if os.path.exists(cf) else '(novo)'}")
    ds = raw.map(tb.build_prep(processor, MAX_AUDIO), with_indices=True,
                 remove_columns=raw.column_names, desc='tok', **tok_kw)
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
        per_device_train_batch_size=args.batch, gradient_accumulation_steps=args.accum,
        num_train_epochs=99, learning_rate=args.lr, lr_scheduler_type='cosine', warmup_steps=20,
        bf16=tb.BF16, fp16=not tb.BF16, logging_steps=10, optim='adamw_8bit', weight_decay=0.01,
        seed=args.seed, output_dir=args.out, report_to='none', save_steps=200, save_total_limit=1,
        run_name=run_name,
        # eval do held-out: só loss (logits do CSM são gigantes — não acumular)
        per_device_eval_batch_size=args.batch, prediction_loss_only=True,
        # SATURA A H100: sem workers a GPU ficava data-starved (util 0%↔92% picotado — a
        # collation de áudio rodava no main thread entre steps). Workers prefetcham batches
        # em paralelo → a GPU não espera. persistent evita re-spawn por época.
        dataloader_num_workers=args.workers, dataloader_pin_memory=True,
        dataloader_persistent_workers=(args.workers > 0), dataloader_prefetch_factor=(4 if args.workers else None),
        remove_unused_columns=False), callbacks=[TimeCap(args.minutes)])
    tr.train()
    model.save_pretrained(f'{args.out}/final'); processor.save_pretrained(f'{args.out}/final')

    # --- held-out REAL: eval_loss em clipes que o modelo NUNCA viu (métrica de overfit) ---
    hold_loss = None
    if hold_rows:
        try:
            hraw = Dataset.from_list(hold_rows).cast_column('audio', Audio(sampling_rate=24000))
            hkw = {'load_from_cache_file': False}
            if cache_dir:
                hcf = os.path.join(cache_dir, f'tok_{tok_fingerprint(hold_rows, args.text_mode, "holdout")}.arrow')
                hkw = {'cache_file_name': hcf, 'load_from_cache_file': True}
            hds = hraw.map(tb.build_prep(processor, MAX_AUDIO), with_indices=True,
                           remove_columns=hraw.column_names, desc='tok-holdout', **hkw)
            hold_loss = round(float(tr.evaluate(eval_dataset=hds)['eval_loss']), 4)
            print(f"  held-out ({len(hold_rows)} clipes nunca treinados): eval_loss {hold_loss}")
        except Exception as e:
            print(f"⚠️ eval do held-out falhou (segue sem eval_loss): {e}")

    # --- gera as 14 frases NA VOZ do locutor (âncora real = contexto) ---
    ref = Dataset.from_list([{'audio': anchors[0]['audio'], 'text': anchors[0]['text']}]) \
                 .cast_column('audio', Audio(sampling_rate=24000))[0]
    wer = tb.eval_wer(model, processor, ref, args.out)

    # --- métricas ADITIVAS (WER continua o critério de escolha) ---
    spk_sim = compute_spk_sim(f'{args.out}/gen', [a['audio'] for a in anchors])
    prosody = compute_prosody(f'{args.out}/gen')
    augment_per_sentence(f'{args.out}/gen', spk_sim, prosody)
    _strip = lambda d: ({k: v for k, v in d.items() if k != 'per_id'} if d else None)

    json.dump({'stage': 'B', 'run': run_name, 'speaker': args.speaker or None,
               'base_adapter': args.base_adapter, 'clips': len(raw),
               'lr': args.lr, 'rank': args.lora_r, 'batch': args.batch, 'accum': args.accum,
               'text_mode': args.text_mode, 'data_file': args.data_file, 'seed': args.seed,
               'mix': mix_comp,
               'holdout': {'frac': args.holdout, 'n': len(hold_rows), 'eval_loss': hold_loss},
               'steps': tr.state.global_step, 'wer': wer,
               'spk_sim': _strip(spk_sim), 'prosody': _strip(prosody)},
              open(f'{args.out}/stage_b_result.json', 'w'), ensure_ascii=False, indent=1)
    _ss = (spk_sim or {}).get('mean')
    print(f"✅ STAGE B [{run_name}]: WER {wer:.1%} · spk_sim {_ss if _ss is not None else 'null'} · "
          f"eval_loss {hold_loss if hold_loss is not None else 'null'} · áudios em {args.out}/gen/ · adapter em {args.out}/final")

    if args.push_hub:
        push_to_hub(args.out, args.push_hub, run_name)
    sys.stdout.flush(); os._exit(0)


if __name__ == '__main__':
    main()
