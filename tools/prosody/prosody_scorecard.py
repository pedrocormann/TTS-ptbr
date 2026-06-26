#!/usr/bin/env python3
"""F3 · Scorecard OBJETIVA de prosódia — mede o 'robótico' em número (receita Aluísio/USP).

Tira o 1º número objetivo de prosódia (hoje n=0). Baseado em Galdino et al. 2024 (ENIAC,
"Acoustic Analysis... YourTTS/SYNTACC"): a assinatura do robótico é (1) taxa de fala alta,
(2) sílaba NUCLEAR curta (alonga só metade), (3) SD baixo (monótono), (4) sem pausa silenciosa.

Roda em CPU (não precisa GPU). Deps: pip install praat-parselmouth numpy soundfile
  python prosody_scorecard.py --dir runpod_samples/treino2_all   # roda em todos os wavs
  python prosody_scorecard.py --wav um.wav                       # um arquivo
Saída: por clipe + agregado, comparado com os ALVOS naturais pt-BR do paper.

ALVOS NATURAIS (pt-BR espontâneo, do paper — o que queremos atingir):
  taxa de fala ~6.67 síl/s · sílaba nuclear ~280ms · com pausas silenciosas · SD ALTO (variado).
SINTÉTICO RUIM (YourTTS): ~9.6 síl/s · nuclear ~150ms · 0 pausa · SD baixo.
"""
import argparse, json, glob, statistics, sys, pathlib

NAT = {"taxa_fala": 6.67, "nuclear_ms": 280, "tem_pausa": True}   # alvos


def analyse(wav_path):
    import parselmouth
    from parselmouth.praat import call
    snd = parselmouth.Sound(str(wav_path))
    dur = snd.get_total_duration()
    intensity = snd.to_intensity(minimum_pitch=70)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=400)

    # --- núcleos silábicos (de Jong & Wempe simplificado): picos de intensidade vozeados ---
    n = call(intensity, "Get number of frames")
    vals = [call(intensity, "Get value in frame", i) for i in range(1, n + 1)]
    times = [call(intensity, "Get time from frame number", i) for i in range(1, n + 1)]
    finite = [v for v in vals if v == v]
    if not finite:
        return None
    thr = (max(finite) - 4.0)                       # ~picos relevantes
    peaks, durs = [], []
    i = 1
    while i < len(vals) - 1:
        if vals[i] == vals[i] and vals[i] > thr and vals[i] >= vals[i-1] and vals[i] > vals[i+1]:
            f0 = call(pitch, "Get value at time", times[i], "Hertz", "Linear")
            if f0 == f0 and f0 > 0:                 # vozeado = núcleo silábico
                peaks.append(times[i])
            i += 3
        else:
            i += 1
    nsyl = len(peaks)
    if nsyl < 2:
        return None
    # duração entre núcleos = proxy de duração silábica
    durs = [(peaks[k+1] - peaks[k]) * 1000 for k in range(len(peaks) - 1)]   # ms

    # --- pausas silenciosas (silêncios > 0.3s) ---
    txt = call(snd, "To TextGrid (silences)", 100, 0, -25, 0.3, 0.1, "silent", "sound")
    n_int = call(txt, "Get number of intervals", 1)
    pausas = sum(1 for k in range(1, n_int + 1) if call(txt, "Get label of interval", 1, k) == "silent")
    fala_dur = dur  # aprox; taxa de fala = núcleos / duração total
    return {
        "dur_s": round(dur, 2),
        "n_silabas": nsyl,
        "taxa_fala": round(nsyl / max(0.1, fala_dur), 2),          # síl/s
        "silaba_media_ms": round(statistics.mean(durs), 0) if durs else None,
        "nuclear_ms": round(max(durs), 0) if durs else None,        # a mais longa ~ proeminência/fronteira
        "sd_silaba_ms": round(statistics.pstdev(durs), 0) if len(durs) > 1 else 0,
        "pausas_silenciosas": pausas,
    }


def verdict(agg):
    flags = []
    if agg["taxa_fala"] and agg["taxa_fala"] > 8: flags.append("rápido demais (>8 síl/s)")
    if agg["nuclear_ms"] and agg["nuclear_ms"] < 220: flags.append(f"sílaba nuclear curta ({agg['nuclear_ms']}ms vs ~280 natural) = não alonga a tônica")
    if agg["pausas_silenciosas_media"] is not None and agg["pausas_silenciosas_media"] < 0.5: flags.append("quase sem pausa silenciosa")
    if agg["sd_silaba_ms"] and agg["sd_silaba_ms"] < 40: flags.append("ritmo monótono (SD baixo)")
    return flags or ["dentro da faixa natural 👍"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir"); ap.add_argument("--wav"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    try:
        import parselmouth  # noqa
    except ImportError:
        sys.exit("instale: pip install praat-parselmouth numpy")
    wavs = [a.wav] if a.wav else sorted(glob.glob(f"{a.dir}/**/*.wav", recursive=True))
    if not wavs:
        sys.exit("nenhum wav. use --dir ou --wav")
    rows = []
    for w in wavs:
        try:
            r = analyse(w)
            if r:
                r["wav"] = str(pathlib.Path(w).relative_to(pathlib.Path.cwd()) if pathlib.Path(w).is_absolute() else w)
                rows.append(r)
        except Exception as e:
            print(f"  erro {w}: {e}", file=sys.stderr)
    if not rows:
        sys.exit("nada analisável")
    def mean(k):
        v = [x[k] for x in rows if x.get(k) is not None];
        return round(statistics.mean(v), 1) if v else None
    agg = {"n": len(rows), "taxa_fala": mean("taxa_fala"), "silaba_media_ms": mean("silaba_media_ms"),
           "nuclear_ms": mean("nuclear_ms"), "sd_silaba_ms": mean("sd_silaba_ms"),
           "pausas_silenciosas_media": mean("pausas_silenciosas")}
    print("=== SCORECARD DE PROSÓDIA (objetiva) ===")
    print(f"  n={agg['n']} clipes")
    print(f"  taxa de fala:     {agg['taxa_fala']} síl/s   (natural ~{NAT['taxa_fala']}; >8 = robótico)")
    print(f"  sílaba nuclear:   {agg['nuclear_ms']} ms      (natural ~{NAT['nuclear_ms']}; <220 = não alonga a tônica)")
    print(f"  SD da sílaba:     {agg['sd_silaba_ms']} ms     (baixo = monótono)")
    print(f"  pausas/ clipe:    {agg['pausas_silenciosas_media']}    (0 = robótico)")
    print("  VEREDITO: " + " · ".join(verdict(agg)))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps({"agg": agg, "clips": rows}, ensure_ascii=False, indent=1))
        print(f"  → {a.out}")


if __name__ == "__main__":
    main()
