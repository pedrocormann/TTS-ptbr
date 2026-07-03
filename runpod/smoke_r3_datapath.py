#!/usr/bin/env python3
"""Smoke do caminho de DADOS da Rodada 3 — SEM GPU, sem datasets, sem treino.

Cria um mini-dataset fake em /tmp (senos de 2s @ 24kHz + train.jsonl no layout do
export_flywheel) e prova que load_rows/filter_rows/split_holdout/apply_mix do
train_voice.py produzem as contagens esperadas, são determinísticos e não vazam
held-out pro treino. Rodar ANTES de qualquer grid (pré-requisito do RUNBOOK-rodada3):

  python3 runpod/smoke_r3_datapath.py
"""
import json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_voice as tv  # módulo-level = só stdlib (heavy imports ficam dentro do main)

ROOT = '/tmp/r3_smoke'
FAILS = []


def check(name, got, want):
    ok = got == want
    print(f"  {'✓' if ok else '✗'} {name}: {got}" + ('' if ok else f'  (esperado: {want})'))
    if not ok:
        FAILS.append(name)


def write_wav(path, secs=2.0, sr=24000, freq=220.0):
    import numpy as np, soundfile as sf
    t = np.arange(int(secs * sr)) / sr
    sf.write(path, (0.3 * np.sin(2 * np.pi * freq * t)).astype('float32'), sr, subtype='PCM_16')


def build_fake():
    shutil.rmtree(ROOT, ignore_errors=True)
    # --- voz: layout do export_flywheel (train.jsonl + segments/, audio = basename) ---
    vd = f'{ROOT}/voz/segments'; os.makedirs(vd)
    for i in range(1, 4):                       # 3 wavs de seno de 2s @ 24kHz (o mini-dataset pedido)
        write_wav(f'{vd}/v{i:02d}.wav', freq=200 + 20 * i)
    write_wav(f'{vd}/v_curto.wav', secs=0.5)    # <1s → deve cair no filtro
    rows = [{'audio': f'v{i:02d}.wav', 'text': f'frase de teste número {i} da voz'} for i in range(1, 4)]
    rows += [{'audio': 'v_curto.wav', 'text': 'curto demais pra valer'},   # dura 0.5s → filtro
             {'audio': 'v01.wav', 'text': 'oi'},                           # 1 palavra → filtro
             {'audio': 'nao_existe.wav', 'text': 'wav sumido do jsonl'}]   # sem áudio → load pula
    with open(f'{ROOT}/voz/train.jsonl', 'w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    # --- base: layout antigo (transcribed.jsonl) → testa o fallback de nome do load_rows ---
    bd = f'{ROOT}/base/segments'; os.makedirs(bd)
    brows = []
    for i in range(1, 21):
        write_wav(f'{bd}/b{i:02d}.wav', freq=100 + 5 * i)
        brows.append({'audio': f'b{i:02d}.wav', 'text': f'clipe público número {i} da base'})
    with open(f'{ROOT}/base/transcribed.jsonl', 'w') as f:
        for r in brows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def main():
    build_fake()
    paths = lambda rs: sorted(r['audio'] for r in rs)

    print("— load_rows + filter_rows (duração via soundfile.info, sem decode) —")
    voz = tv.load_rows(f'{ROOT}/voz')                    # auto: train.jsonl
    check('voz carregada (6 linhas, 1 sem wav)', len(voz), 5)
    voz_f = tv.filter_rows(voz)
    check('voz filtrada (cai 0.5s + 1 palavra)', len(voz_f), 3)
    base = tv.load_rows(f'{ROOT}/base')                  # auto: fallback transcribed.jsonl
    base_f = tv.filter_rows(base)
    check('base carregada+filtrada', (len(base), len(base_f)), (20, 20))

    print("— split_holdout (seed fixa, ANTES do treino) —")
    v_tr, v_ho = tv.split_holdout(voz_f, 0.34)
    check('voz 3 clipes @34% → 2 treino + 1 held-out', (len(v_tr), len(v_ho)), (2, 1))
    b_tr, b_ho = tv.split_holdout(base_f, 0.05)
    check('base 20 clipes @5% → 19 treino + 1 held-out', (len(b_tr), len(b_ho)), (19, 1))
    check('held-out ∩ treino = ∅ (voz)', set(paths(v_ho)) & set(paths(v_tr)), set())
    v_tr2, v_ho2 = tv.split_holdout(voz_f, 0.34)
    check('holdout determinístico (mesma seed → mesmo split)', paths(v_ho2), paths(v_ho))

    print("— apply_mix (replica/subamostra por peso + interleave) —")
    mixed, comp = tv.apply_mix({'voz': v_tr, 'base': b_tr}, {'voz': 1.0, 'base': 0.15})
    check('mix15: voz usa 2 (peso 1.0)', comp['voz']['used'], 2)
    check('mix15: base usa 3 (19×0.15≈3)', comp['base']['used'], 3)
    check('mix15: total 5', len(mixed), 5)
    m30, c30 = tv.apply_mix({'voz': v_tr, 'base': b_tr}, {'voz': 1.0, 'base': 0.30})
    check('mix30: base usa 6 (19×0.30≈6) · total 8', (c30['base']['used'], len(m30)), (6, 8))
    m2x, c2x = tv.apply_mix({'voz': v_tr, 'base': b_tr}, {'voz': 2.0, 'base': 0.15})
    check('peso 2.0 replica: voz usa 4 (2 clipes × 2 passadas)', c2x['voz']['used'], 4)
    mixed_b, _ = tv.apply_mix({'voz': v_tr, 'base': b_tr}, {'voz': 1.0, 'base': 0.15})
    check('mix determinístico (mesma seed → mesma ordem)', [r['audio'] for r in mixed_b],
          [r['audio'] for r in mixed])
    leak = (set(paths(v_ho)) | set(paths(b_ho))) & set(paths(mixed))
    check('held-out NUNCA entra no mix (sem vazamento)', leak, set())

    print("— extras —")
    kv = tv.parse_kv('voz=1.0,base=0.15', float)
    check('parse_kv (ordem preservada)', list(kv.items()), [('voz', 1.0), ('base', 0.15)])
    anc = tv.pick_anchors(v_tr + v_tr)  # com réplica → dedupe
    check('pick_anchors dedupa réplicas', len(anc), 2)
    fp1 = tv.tok_fingerprint(mixed, 'raw'); fp2 = tv.tok_fingerprint(mixed, 'raw')
    check('fingerprint estável', fp1 == fp2, True)
    check('fingerprint muda com text_mode', fp1 != tv.tok_fingerprint(mixed, 'normalize'), True)
    alt = [dict(r, text=r['text'] + ' editado') for r in mixed]
    check('fingerprint muda se o texto muda', fp1 != tv.tok_fingerprint(alt, 'raw'), True)

    print()
    if FAILS:
        print(f"❌ SMOKE FALHOU: {len(FAILS)} checagem(ns): {FAILS}")
        sys.exit(1)
    print(f"✅ SMOKE OK — caminho de dados da Rodada 3 validado sem GPU (fake em {ROOT})")


if __name__ == '__main__':
    main()
