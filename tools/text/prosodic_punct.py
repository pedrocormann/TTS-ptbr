#!/usr/bin/env python3
"""Pontuação PROSÓDICA pós-Whisper (abordagem Aluísio/NILC, NURC-SP_ENTOA_TTS).

Tese (Galdino/Svartman/Aluísio): em fala espontânea, a pontuação do texto de treino
de TTS deve refletir FRONTEIRAS PROSÓDICAS (unidades entoacionais), não gramática.
O Whisper pontua gramaticalmente — vírgulas sem pausa, pontos sem fronteira real —
e o TTS aprende a melodia errada. Este módulo re-pontua usando o próprio áudio:

  entrada: palavras com timestamps (faster-whisper word_timestamps=True) + wav
  sinais : pausa entre palavras · reset de F0 · subida final de F0 (pergunta)
           · alongamento final (hesitação) · fillers preservados
  saída  : texto re-pontuado + fronteiras (pra segmentação por IU no pipeline)

Convenções de saída (mapeando a anotação NURC/ENTOA pra texto de treino):
  fronteira NÃO-terminal (IU continua)  → ","
  fronteira TERMINAL (contorno fechou)  → "." (ou "?" se F0 sobe no final)
  hesitação/alongamento com pausa       → "…"
  fillers (é, né, ãh…)                  → preservados como palavras normais

Uso:
  from prosodic_punct import ProsodicPunctuator
  pp = ProsodicPunctuator(audio_path)
  out = pp.repunctuate(words)   # words: [{word,start,end}]
  out.text, out.boundaries, out.stats
CLI (um clipe, pra debug):
  python3 prosodic_punct.py --audio clip.wav [--model small] [--compare "texto atual"]

EVIDÊNCIA (verificada 02/jul/2026 — dossiê research/dossier-2026-07/82 e 21):
  · BRACIS 2025 (arXiv:2511.14779): TTS treinado em segmentos PROSÓDICOS vs automáticos:
    WER 0,43 vs 0,50 (p<0,01) e F0-RMSE ~39 vs ~44 Hz — segmentar por IU melhora o treino.
  · PROPOR 2024 (aclanthology 2024.propor-1.4): silêncio ≥300ms é O sinal — "as heurísticas
    de silêncio sozinhas ≈ todas as outras (Δ0-3%)". Nossos thresholds seguem isso.
  · DisfluencySpeech (arXiv:2406.08820): transcrição "limpa" sobre áudio espontâneo DESTRÓI
    o treino (CER 60%, não converge) vs verbatim (15%) — fillers ficam no texto.
  · Vietnamita (arXiv:2004.09607): vírgula onde o áudio pausa (>0.3s) melhora MOS.
  · Székely SSW'19: marcar a LOCALIZAÇÃO do filler basta; não micro-gerenciar o tipo.
  Divergência documentada da convenção NURC/IberSPEECH-2022: lá "…" marca SÓ silêncio e
  alongamento é "::"; aqui usamos "…" pra hesitação/alongamento-com-pausa porque o texto
  de treino do TTS precisa de pontuação padrão (sem símbolos fora do vocabulário).
  Teto futuro (colaboração USP): Whisper fine-tunado pra emitir fronteira de IU como token
  (PSST, CoNLL 2023, F1 0,87) — substitui estas heurísticas por modelo.
"""
from dataclasses import dataclass, field
import argparse, json, math, os, re, sys

# ---------------- thresholds (calibráveis; ver docs/dossiê ENTOA) ----------------
PAUSE_NONTERM = 0.15   # s — pausa mínima pra fronteira não-terminal (vírgula)
PAUSE_TERM    = 0.60   # s — pausa que por si só fecha contorno (ponto)
PAUSE_TERM_F0 = 0.32   # s — pausa média fecha contorno SE F0 caiu pro piso do falante
F0_LOW_Q      = 0.25   # quantil do F0 do falante que conta como "piso" (fechamento)
F0_RESET_ST   = 3.0    # semitons de reset (sobe após fronteira) que reforçam terminal
RISE_ST       = 2.5    # semitons de subida no último trecho vozeado → "?"
RISE_WIN      = 0.28   # s — janela final pra medir subida
LENGTHEN_X    = 2.2    # duração/char do último token vs mediana do falante → alongamento
# fillers: nossos coloquiais + a lista do PROPOR 2024 (pausas preenchidas do NURC-SP)
FILLERS = {"é","eh","ah","ãh","uh","hum","hm","mm","né","tipo","assim","então","aí","cara","pô","po","olha","bom","enfim","sabe",
           "uhum","éh","ha","ahn","han","uhn","ehn","hein","oh","hun"}
# pistas lexicais de pergunta (pt-BR): sem elas, subida final = CONTINUAÇÃO (…), não "?"
# início interrogativo do segmento (2 primeiras palavras) OU tag no final (2 últimas)
Q_START = re.compile(r"^\s*(o que|que|quem|qual|quais|quando|onde|aonde|como|por que|pra que|cadê|será|quanto|quanta|quantos|quantas|você|vocês|tu|cê)\b", re.IGNORECASE)
Q_TAG   = re.compile(r"\b(né|não é|ou não|certo|tá|entendeu|sacou|beleza)\s*$", re.IGNORECASE)
# ---------------------------------------------------------------------------------

def _hz_to_st(hz, ref=100.0):
    return 12.0 * math.log2(max(hz, 1e-6) / ref)

@dataclass
class Boundary:
    after_word: int      # índice da palavra que precede a fronteira
    t: float             # tempo (fim da palavra)
    kind: str            # 'terminal' | 'nonterminal' | 'hesitation'
    mark: str            # '.', '?', ',', '…'
    pause: float
    f0_before: float | None = None
    f0_after: float | None = None

@dataclass
class Repunct:
    text: str
    boundaries: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    words: list = field(default_factory=list)
    tokens: list = field(default_factory=list)  # 1 token pontuado por palavra ('' se descartada), alinhado a words

class ProsodicPunctuator:
    def __init__(self, audio_path, f0_floor=60, f0_ceil=380):
        import parselmouth
        self.snd = parselmouth.Sound(audio_path)
        self.pitch = self.snd.to_pitch(time_step=0.01, pitch_floor=f0_floor, pitch_ceiling=f0_ceil)
        vals = self.pitch.selected_array["frequency"]
        self._f0_times = [self.pitch.get_time_from_frame_number(i + 1) for i in range(len(vals))]
        self._f0 = vals  # 0 = não-vozeado
        voiced = sorted(v for v in vals if v > 0)
        self.f0_median = voiced[len(voiced)//2] if voiced else 0.0
        self.f0_low = voiced[int(len(voiced)*F0_LOW_Q)] if voiced else 0.0

    # ---- sinais acústicos ----
    def f0_mean(self, t0, t1):
        vs = [f for t, f in zip(self._f0_times, self._f0) if t0 <= t <= t1 and f > 0]
        return sum(vs)/len(vs) if vs else None

    def final_rise_st(self, t_end):
        """subida (em ST) na janela final antes de t_end: fim vs início do trecho vozeado."""
        t0 = t_end - RISE_WIN
        pts = [(t, f) for t, f in zip(self._f0_times, self._f0) if t0 <= t <= t_end and f > 0]
        if len(pts) < 4:
            return 0.0
        k = max(2, len(pts)//3)
        head = sum(f for _, f in pts[:k])/k
        tail = sum(f for _, f in pts[-k:])/k
        return _hz_to_st(tail) - _hz_to_st(head)

    def _is_question(self, words, i):
        """pergunta = subida final + pista lexical: início interrogativo DA UNIDADE
        (desde a última fronteira terminal implícita = início do trecho) ou tag final."""
        head = " ".join(x["word"] for x in words[:2]).strip()
        tail = " ".join(x["word"] for x in words[max(0, i-1):i+1]).strip()
        tail = re.sub(r"[^\w\sáéíóúâêôãõç]", "", tail, flags=re.IGNORECASE)
        return bool(Q_START.search(head) or Q_TAG.search(tail))

    # ---- regra principal ----
    def repunctuate(self, words, keep_fillers=True):
        """words: [{'word','start','end'}] em ordem. Retorna Repunct."""
        words = [w for w in words if (w.get("word") or "").strip()]
        if not words:
            return Repunct(text="", stats={"n_words": 0})
        # mediana de duração-por-caractere (proxy de alongamento)
        dpc = sorted((w["end"]-w["start"]) / max(1, len(re.sub(r"\W", "", w["word"])))
                     for w in words if w["end"] > w["start"])
        dpc_med = dpc[len(dpc)//2] if dpc else 0.08

        toks, bounds = [None] * len(words), []
        n = len(words)
        for i, w in enumerate(words):
            raw = w["word"].strip()
            core = re.sub(r"^[\s,.;:!?…]+|[\s,.;:!?…]+$", "", raw)  # tira pontuação do ASR
            if not core:
                toks[i] = ""
                continue
            is_filler = core.lower().strip("~") in FILLERS
            lengthened = (w["end"]-w["start"]) / max(1, len(re.sub(r"\W", "", core))) > LENGTHEN_X * dpc_med

            gap = (words[i+1]["start"] - w["end"]) if i+1 < n else None
            mark = ""
            if gap is None:  # última palavra do trecho: decide terminal
                rise = self.final_rise_st(w["end"])
                if rise >= RISE_ST:
                    # subida final: pergunta SÓ com pista lexical; senão é continuação
                    mark = "?" if self._is_question(words, i) else "…"
                else:
                    mark = "."
                bounds.append(Boundary(i, w["end"], "terminal", mark, 0.0))
            elif gap >= PAUSE_NONTERM:
                f0b = self.f0_mean(max(0.0, w["end"]-0.15), w["end"])
                f0a = self.f0_mean(words[i+1]["start"], words[i+1]["start"]+0.15)
                rise = self.final_rise_st(w["end"])
                reset = (_hz_to_st(f0a) - _hz_to_st(f0b)) if (f0a and f0b) else 0.0
                terminal = (gap >= PAUSE_TERM
                            or (gap >= PAUSE_TERM_F0 and f0b is not None and f0b <= self.f0_low)
                            or (gap >= PAUSE_TERM_F0 and reset >= F0_RESET_ST))
                if (is_filler or lengthened) and not terminal:
                    mark = "…"
                    bounds.append(Boundary(i, w["end"], "hesitation", mark, gap, f0b, f0a))
                elif terminal:
                    if rise >= RISE_ST:
                        mark = "?" if self._is_question(words, i) else "…"
                    else:
                        mark = "."
                    bounds.append(Boundary(i, w["end"], "terminal", mark, gap, f0b, f0a))
                else:
                    mark = ","
                    bounds.append(Boundary(i, w["end"], "nonterminal", mark, gap, f0b, f0a))
            if not keep_fillers and is_filler and not mark:
                toks[i] = ""
                continue
            toks[i] = core + mark

        text = " ".join(t for t in toks if t)
        text = re.sub(r"\s+", " ", text).strip()
        if text and text[-1] not in ".?!…":
            text += "."
        # capitaliza início e pós-terminal
        text = _capitalize(text)
        stats = {"n_words": len(words),
                 "terminal": sum(1 for b in bounds if b.kind == "terminal"),
                 "nonterminal": sum(1 for b in bounds if b.kind == "nonterminal"),
                 "hesitation": sum(1 for b in bounds if b.kind == "hesitation"),
                 "question": sum(1 for b in bounds if b.mark == "?"),
                 "f0_median": round(self.f0_median, 1)}
        return Repunct(text=text, boundaries=bounds, stats=stats, words=words, tokens=toks)

def _capitalize(text):
    out, cap = [], True
    for ch in text:
        out.append(ch.upper() if (cap and ch.isalpha()) else ch)
        if ch.isalpha():
            cap = False
        if ch in ".?!…":
            cap = True
    return "".join(out)

def iu_segments(words, boundaries, alvo_min=3.0, alvo_max=12.0):
    """Segmentação por IU: corta preferencialmente em fronteira TERMINAL (contorno
    fechado, ≥alvo_min); se o trecho estourar alvo_max sem terminal, fecha na
    próxima fronteira qualquer (não-terminal/hesitação) — proteção contra >15s."""
    segs, cur_start, last_i = [], words[0]["start"] if words else 0.0, 0
    def close(after_word):
        nonlocal cur_start, last_i
        t_end = words[after_word]["end"]
        segs.append({"start": cur_start, "end": t_end, "i0": last_i, "i1": after_word})
        cur_start = words[after_word + 1]["start"] if after_word + 1 < len(words) else t_end
        last_i = after_word + 1
    for b in sorted(boundaries, key=lambda x: x.after_word):
        if b.after_word < last_i:
            continue
        dur = words[b.after_word]["end"] - cur_start
        if b.kind == "terminal" and dur >= alvo_min:
            close(b.after_word)
        elif dur > alvo_max:  # estourou o teto: fecha em QUALQUER fronteira
            close(b.after_word)
    if words and (not segs or segs[-1]["i1"] < len(words) - 1):
        segs.append({"start": cur_start, "end": words[-1]["end"], "i0": last_i, "i1": len(words)-1})
    return segs

# ---------------- CLI de debug ----------------
def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--compare", default=None, help="texto atual pra diff lado-a-lado")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a.audio, language="pt", word_timestamps=True, beam_size=5)
    words = [{"word": w.word, "start": w.start, "end": w.end} for s in segs for w in s.words]
    pp = ProsodicPunctuator(a.audio)
    out = pp.repunctuate(words)
    print("PROSÓDICA :", out.text)
    if a.compare:
        print("ATUAL     :", a.compare)
    print("stats     :", json.dumps(out.stats, ensure_ascii=False))
    for b in out.boundaries:
        print(f"  {b.kind:12s} '{b.mark}' após w{b.after_word:3d} t={b.t:6.2f}s pausa={b.pause:.2f}s"
              + (f" F0 {b.f0_before:.0f}→{b.f0_after:.0f}Hz" if b.f0_before and b.f0_after else ""))

if __name__ == "__main__":
    _main()
