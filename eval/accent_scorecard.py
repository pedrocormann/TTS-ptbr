#!/usr/bin/env python3
"""Accent-scorecard carioca — sotaque OBJETIVO, por-segmento, com DIREÇÃO do erro.

Torna o gap #1 ("soa gringo") uma métrica, não uma reclamação. Ideia (reimplementada do
método de Barman/Sharma/Mahanta, "Phonology-Informed Evaluation of Multilingual TTS",
arXiv:2607.01965 / repo TTSEvalVH — SEM licença declarada, então aqui é REIMPLEMENTAÇÃO do
método, que é livre; nenhum código/dado deles foi copiado):

  1. treina um classificador (LR/RF) num CONTRASTE fonológico do pt-BR usando a fala HUMANA
     do Pedro (carioca real) como benchmark — features acústicas normalizadas;
  2. aplica cross-domain na saída do CSM (fala sintética);
  3. mede, por vogal, quanto o TTS cai do lado ERRADO da fronteira, e em QUE DIREÇÃO
     (o CSM abre demais? fecha demais? neutraliza a distinção?).

Diferente de MOS/WER (globais, opacos): dá diagnóstico sub-palavra acionável ("o CSM
sistematicamente FECHA as médias abertas → alvo de dado/loss"), e é NÃO-saturável.

CONTRASTES pt-BR (correlato acústico claro em F1/F2 — análogo ao ±ATR do paper):
  - mid_e : /e/ fechado ("vê", "mesa") × /ɛ/ aberto ("pé", "café")  → F1 separa (aberto = F1 alto)
  - mid_o : /o/ fechado ("avô", "bola") × /ɔ/ aberto ("avó", "pó")  → idem
  - (v2 carioca: elevação de átona final /e/→[i] /o/→[u]; chiado /s/→[ʃ] em coda = consoante,
     precisa de centroide espectral, não formante — hook separado em audit_chiado, TODO.)

DEPENDÊNCIAS DE DADO (o que alimenta este módulo — cada uma tem um hook):
  - segmentação de vogal no tempo  → forced alignment (MFA pt-BR / ctc-segmentation) [TODO align]
  - formantes por vogal (F1/F2/F3/B1 + duração) → parselmouth/Praat (já usamos em prosodic_punct)
  - rótulo aberto/fechado por token → léxico pt-BR (tools/text/g2p_lexicon; BIPA dialeto-Rio) [TODO lex]

Este arquivo já roda a LÓGICA (classificador + cross-domain + auditoria de direção) num
self-test sintético; a extração real de formantes fica atrás dos hooks acima.

CLI (com tabelas de formante prontas):
  python -m eval.accent_scorecard --human human_formants.parquet --tts csm_formants.parquet --contrast mid_e
Self-test (sem dado, prova a lógica):
  python eval/accent_scorecard.py --selftest
"""
import argparse
import numpy as np

# --- Esquema da tabela de formantes (uma linha por VOGAL medida) ---
# colunas: speaker_id, word, vowel_label, aperture ('open'|'closed'), F1_Hz, F2_Hz, F3_Hz, B1_Hz, duration_ms
FEATURES = ["F1_z", "F2_z", "F3_z", "B1_Hz", "duration_ms"]
OUTLIER = dict(B1_Hz=(0, 400), F1_Hz=(150, 1100), F2_Hz=(500, 3200), F3_Hz=(1800, 4200))

CONTRASTS = {
    "mid_e": {"open": "ɛ", "closed": "e"},   # pé × vê
    "mid_o": {"open": "ɔ", "closed": "o"},   # avó × avô
}


def _apply_outlier(df):
    import pandas as pd  # noqa
    mask = df["F1_Hz"].notna()
    for col, (lo, hi) in OUTLIER.items():
        if col in df:
            mask &= df[col].between(lo, hi)
    return df[mask].copy()


def _lobanov(df):
    """z-score de formante POR falante (remove fisiologia antes de comparar entre-falantes)."""
    for f in ["F1_Hz", "F2_Hz", "F3_Hz"]:
        mu = df.groupby("speaker_id")[f].transform("mean")
        sd = df.groupby("speaker_id")[f].transform("std").replace(0, 1e-6)
        df[f.replace("_Hz", "_z")] = (df[f] - mu) / sd
    return df


def _global_z(df):
    """z-score global (para a voz sintética, tratada como 1 'falante')."""
    for f in ["F1_Hz", "F2_Hz", "F3_Hz"]:
        sd = df[f].std() or 1e-6
        df[f.replace("_Hz", "_z")] = (df[f] - df[f].mean()) / sd
    return df


def _models():
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    return {
        "LR": lambda: LogisticRegression(penalty="l2", C=1.0, class_weight="balanced",
                                         solver="lbfgs", max_iter=1000, random_state=42),
        "RF": lambda: RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                             min_samples_leaf=5, random_state=42, n_jobs=-1),
    }


def crossdomain(human_df, tts_df):
    """Treina no humano, avalia H→H (CV por falante), H→TTS, TTS→TTS, TTS→H. y=1 se 'open'.
    Retorna dict de macro-F1. H→H alto + H→TTS baixo = o TTS diverge das normas humanas."""
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import GroupKFold, StratifiedKFold
    from sklearn.metrics import f1_score

    yh = (human_df["aperture"] == "open").astype(int).values
    yt = (tts_df["aperture"] == "open").astype(int).values
    Xh, Xt = human_df[FEATURES].values, tts_df[FEATURES].values
    groups = human_df["speaker_id"].values
    out = {}
    for name, mk in _models().items():
        gkf = GroupKFold(n_splits=min(5, max(2, human_df["speaker_id"].nunique())))
        cv = np.zeros(len(yh))
        for tr, te in gkf.split(Xh, yh, groups):
            sc = StandardScaler(); m = mk()
            m.fit(sc.fit_transform(Xh[tr]), yh[tr]); cv[te] = m.predict(sc.transform(Xh[te]))
        sc = StandardScaler(); m = mk(); m.fit(sc.fit_transform(Xh), yh)
        y_ht = m.predict(sc.transform(Xt))
        sct = StandardScaler(); Xts = sct.fit_transform(Xt)
        skf = StratifiedKFold(n_splits=min(5, max(2, int(min(np.bincount(yt))))), shuffle=True, random_state=42)
        cvt = np.zeros(len(yt))
        for tr, te in skf.split(Xts, yt):
            m2 = mk(); m2.fit(Xts[tr], yt[tr]); cvt[te] = m2.predict(Xts[te])
        m3 = mk(); m3.fit(Xts, yt); y_th = m3.predict(sct.transform(Xh))
        out[name] = dict(HH=f1_score(yh, cv, average="macro"), HtoTTS=f1_score(yt, y_ht, average="macro"),
                         TTStoTTS=f1_score(yt, cvt, average="macro"), TTStoH=f1_score(yh, y_th, average="macro"))
    return out


def audit_direction(human_df, tts_df):
    """A parte mais valiosa: NÃO só 'erra', mas 'erra pra que lado'. Treina no humano, prediz
    no TTS, e compara o rótulo predito vs o gold. over_open = fechado→predito aberto; over_close =
    aberto→predito fechado. Assimetria = viés sistemático do TTS (ex.: 'fecha as abertas')."""
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    yh = (human_df["aperture"] == "open").astype(int).values
    sc = StandardScaler(); m = _models()["LR"]()
    m.fit(sc.fit_transform(human_df[FEATURES].values), yh)
    gold = (tts_df["aperture"] == "open").astype(int).values
    pred = m.predict(sc.transform(tts_df[FEATURES].values))
    mism = (gold != pred)
    over_open = ((gold == 0) & (pred == 1)).sum() / max(1, (gold == 0).sum())   # fechou→abriu
    over_close = ((gold == 1) & (pred == 0)).sum() / max(1, (gold == 1).sum())  # abriu→fechou
    by_vowel = {}
    for v in sorted(set(tts_df["vowel_label"])):
        mv = (tts_df["vowel_label"].values == v)
        if mv.sum():
            by_vowel[v] = dict(N=int(mv.sum()), mismatch=float(mism[mv].mean()))
    return dict(mismatch_rate=float(mism.mean()), over_open=float(over_open),
                over_close=float(over_close), by_vowel=by_vowel)


# ---- hooks de extração de dado real (a preencher quando plugar áudio) ----
def extract_formants(wav_path, alignment):  # TODO align+parselmouth
    """Extrai F1/F2/F3/B1+duração no ponto médio de cada vogal, dado o alinhamento forçado.
    Usar parselmouth (já é dep do prosodic_punct) + MFA/ctc-segmentation pra as fronteiras de vogal."""
    raise NotImplementedError("plugar parselmouth + forced alignment (ver docstring)")


def label_aperture(word, vowel, lexicon):  # TODO lex
    """Rótulo aberto/fechado do token via léxico pt-BR (tools/text/g2p_lexicon; BIPA dialeto-Rio)."""
    raise NotImplementedError("plugar léxico pt-BR com marcação ɛ/e ɔ/o")


def _selftest():
    """Prova a lógica com formantes sintéticos: humano separa aberto(F1 alto)/fechado(F1 baixo);
    o 'TTS' FECHA demais as abertas (F1 baixo onde deveria ser alto) → audit deve gritar over_close."""
    import numpy as np, pandas as pd
    rng = np.random.RandomState(0)
    def rows(n, aperture, f1, spk, tts=False):
        return pd.DataFrame(dict(
            speaker_id=spk, word=[f"w{i}" for i in range(n)],
            vowel_label=("ɛ" if aperture == "open" else "e"), aperture=aperture,
            F1_Hz=rng.normal(f1, 35, n), F2_Hz=rng.normal(1900, 90, n),
            F3_Hz=rng.normal(2700, 90, n), B1_Hz=rng.normal(80, 15, n),
            duration_ms=rng.normal(90, 12, n)))
    human = pd.concat([rows(120, "closed", 400, "pedro"), rows(120, "open", 620, "pedro"),
                       rows(100, "closed", 410, "joao"),  rows(100, "open", 640, "joao")])
    # TTS: fechadas ok, mas ABERTAS saem fechadas demais (F1 ~500 em vez de ~620) = "gringo"
    tts = pd.concat([rows(80, "closed", 405, "csm", tts=True), rows(80, "open", 505, "csm", tts=True)])
    _lobanov(human)
    _global_z(tts)
    cd = crossdomain(human, tts)
    au = audit_direction(human, tts)
    print("cross-domain macro-F1:", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in cd.items()})
    print("audit:", dict(mismatch_rate=round(au["mismatch_rate"], 3),
                         over_open=round(au["over_open"], 3), over_close=round(au["over_close"], 3)))
    assert au["over_close"] > au["over_open"], "esperava viés de FECHAR as abertas no TTS sintético"
    assert cd["LR"]["HH"] > 0.8, "humano deveria separar aberto/fechado facilmente"
    print("✓ self-test ok — a lógica de scorecard + direção do erro roda "
          "(o 'TTS' foi flagrado fechando as vogais abertas, como um sotaque neutralizante).")


def main():
    ap = argparse.ArgumentParser(description="Accent-scorecard carioca (contraste fonológico objetivo).")
    ap.add_argument("--human", help="tabela de formantes da fala REAL do Pedro (parquet/csv)")
    ap.add_argument("--tts", help="tabela de formantes da saída do CSM")
    ap.add_argument("--contrast", default="mid_e", choices=list(CONTRASTS))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not (a.human and a.tts):
        return _selftest()
    import pandas as pd
    rd = lambda p: pd.read_parquet(p) if p.endswith(".parquet") else pd.read_csv(p)
    pair = CONTRASTS[a.contrast]; keep = set(pair.values())
    human = _lobanov(_apply_outlier(rd(a.human)))
    tts = _global_z(_apply_outlier(rd(a.tts)))
    human = human[human["vowel_label"].isin(keep)]; tts = tts[tts["vowel_label"].isin(keep)]
    print(f"[{a.contrast}] human={len(human)} tok / tts={len(tts)} tok")
    print("cross-domain:", crossdomain(human, tts))
    print("direção do erro:", audit_direction(human, tts))


if __name__ == "__main__":
    main()
