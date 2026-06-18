#!/usr/bin/env python3
"""
enrich_markers.py — v2 do FEEDBACK.md (pós-processador de markers com forced-alignment).

Propósito: fechar o loop do feedback localizado no tempo. Transforma marcadores humanos
('soa gringo em t=2.3s') em feedback sub-palavra acionável (esperado_fonema vs ouvido_fonema).

Fluxo de dados:
  ratings.jsonl (com markers: t_start/t_end/tag/sev/note)
    ↓
  enrich_markers.py
    ├─ (1) ler ratings.jsonl
    ├─ (2) p/ cada clip: forced-alignment ref_text ↔ áudio (TODO: MFA/ctc-segmentation)
    ├─ (3) cruzar marker.t_start/t_end com fonema por tempo → expected_phoneme/grapheme
    ├─ (4) GOP score (TODO: encoder de confiança)
    ├─ (5) escrever markers_enriched.jsonl
    ↓
  rate_app (Insights tab) usa expected_phoneme pra ranking sub-palavra

Aprendizados do plano (REPLAN §14-15, RESEARCH §14-15):
  - GOP/MDD pt-BR (arXiv 2309.07719, QCRI): localiza o fonema errado via
    fonema canônico (esperado via G2P) vs verbatim (ouvido via forced-align).
  - GOP score (Goodness of Pronunciation): confiança de que o fonema foi pronunciado certo.
  - Segmentation-free GOP (arXiv 2507.16838): não precisa de alinhamento perfeito.
  - MDD "L1-aware" (arXiv 2309.07719): modela a discrepância nativo vs estrangeiro.

Status do scaffold (2026-06-17):
  - Estrutura de dados: ✓ (lê/escreve jsonl, estrutura certa)
  - Pipeline Dry-run: ✓ (roda sem erro, lê e reescreve)
  - Forced-alignment: TODO (MFA pt-BR ou ctc-segmentation como dependência)
  - GOP score: TODO (encoder de confiança, hoje retorna 0.0)
  - Caching de áudio: TODO (hoje carrega do disco sempre)

Reusar do g2p_pt.py:
  - word_to_phones(word) → [fonemas] — espera palavra já normalizada
  - text_to_phones(text) → [fonemas] — entrada de texto livre

Uso:
  python tools/feedback/enrich_markers.py [--input ratings.jsonl] [--output markers_enriched.jsonl]
  
Testes:
  python tools/feedback/enrich_markers.py --dry-run  # lê ratings.jsonl, não escreve
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Optional, Any

# Adiciona o repo root ao path pra reusar módulos
REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.recording.g2p_pt import text_to_phones, word_to_phones  # noqa: E402
from tools.text.normalize_ptbr import normalize_ptbr  # noqa: E402


# ============================================================================
# Data structures
# ============================================================================

class Marker:
    """Um marcador de tempo + tipo de erro (do avaliador humano)."""
    def __init__(self, t_start: float, t_end: float, tag: str, sev: Any, note: str):
        self.t_start = t_start
        self.t_end = t_end
        self.tag = tag
        self.sev = _norm_sev(sev)  # converte "grave"/"medio"/"leve" → 5/3/1
        self.note = note
        # Enriquecido pelo pipeline:
        self.expected_phoneme: Optional[str] = None
        self.expected_grapheme: Optional[str] = None
        self.gop_score: float = 0.0
        self.context: Optional[str] = None

    def to_dict(self) -> dict:
        """Serializa pro jsonl (com campos opcionais só se preenchidos)."""
        d = {
            't_start': self.t_start,
            't_end': self.t_end,
            'tag': self.tag,
            'sev': self.sev,
            'note': self.note,
        }
        if self.expected_phoneme:
            d['expected_phoneme'] = self.expected_phoneme
        if self.expected_grapheme:
            d['expected_grapheme'] = self.expected_grapheme
        if self.gop_score > 0:
            d['gop_score'] = round(self.gop_score, 3)
        if self.context:
            d['context'] = self.context
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'Marker':
        m = cls(d['t_start'], d['t_end'], d['tag'], d['sev'], d.get('note', ''))
        m.expected_phoneme = d.get('expected_phoneme')
        m.expected_grapheme = d.get('expected_grapheme')
        m.gop_score = float(d.get('gop_score', 0.0))
        m.context = d.get('context')
        return m


class FeedbackRecord:
    """Um registro do feedback (1 clipe = 1 record)."""
    def __init__(self, data: dict):
        self.run = data.get('run', '')
        self.id = data.get('id', '')
        self.audio_path = data.get('audio', '')
        self.ref_text = data.get('ref_text', '')
        self.asr_hyp = data.get('asr_hyp', '')
        self.emotion = data.get('emotion', '')
        self.accent = data.get('accent', '')
        self.wer = float(data.get('wer', 0.0))
        self.dur_s = float(data.get('dur_s', 0.0))
        self.markers: list[Marker] = []
        self.ratings = data.get('ratings', {})
        self.problems = data.get('problems', [])
        self.rated_ts = data.get('rated_ts', 0)
        self.schema_version = int(data.get('schema_version', 1))
        # Parse markers from input
        for m_dict in data.get('markers', []):
            self.markers.append(Marker.from_dict(m_dict))

    def to_dict(self) -> dict:
        """Serializa o record enriched pro jsonl."""
        return {
            'run': self.run,
            'id': self.id,
            'audio': self.audio_path,
            'ref_text': self.ref_text,
            'asr_hyp': self.asr_hyp,
            'emotion': self.emotion,
            'accent': self.accent,
            'wer': self.wer,
            'dur_s': self.dur_s,
            'wer_ops': data_dict.get('wer_ops', []),  # preserva se existir
            'markers': [m.to_dict() for m in self.markers],
            'ratings': self.ratings,
            'problems': self.problems,
            'rated_ts': self.rated_ts,
            'schema_version': self.schema_version,
        }


def _norm_sev(sev: Any) -> int:
    """Normaliza severity: "grave"→5, "medio"→3, "leve"→1, int→int."""
    if isinstance(sev, int):
        return max(1, min(5, sev))
    if isinstance(sev, str):
        return {'grave': 5, 'medio': 3, 'médio': 3, 'leve': 1}.get(sev.lower(), 3)
    return 3


# ============================================================================
# Forced-alignment stub (TODO: MFA/ctc-segmentation como dependência)
# ============================================================================

class ForcedAligner:
    """
    Stub de forced-alignment: alinha ref_text → áudio e retorna [fonema por tempo].
    
    Campos retornados por fonema:
      {
        'phoneme': 'a',
        'grapheme': 'a',
        'start_s': 0.1,
        'end_s': 0.25,
        'confidence': 0.95
      }
    
    TODO (dependências):
      - MFA pt-BR (Montreal Forced Aligner): requer treinamento; heavy (~1h setup).
      - ctc-segmentation (Nvidia): CTC-based, mais leve; requer modelo ASR com CTC.
      - Manual alignment de benchmark: pré-computado, mais rápido pra validar.
    """
    def __init__(self):
        self._cache: dict[str, list[dict]] = {}

    def align(self, ref_text: str, audio_path: str, sr: int = 16000) -> list[dict]:
        """
        Alinha texto vs áudio e retorna lista de fonemas com timestamps.
        
        Args:
            ref_text: texto-alvo (ex: "Olá, tudo bem?")
            audio_path: caminho do arquivo de áudio
            sr: sample rate (default 16000)
        
        Returns:
            [{'phoneme': 'o', 'grapheme': 'O', 'start_s': 0.0, 'end_s': 0.1, 'confidence': 0.95}, ...]
        
        Status: TODO
            - Sem modelo de alignment, retorna uma sequência APROXIMADA via G2P
              + duração total do clipe.
            - Cada fonema recebe duração uniforme (distribuição ingênua).
            - Confiança hard-coded em 0.5 (incerto).
        """
        if audio_path in self._cache:
            return self._cache[audio_path]

        # Stub: transcreve texto em fonemas via G2P
        phonemes_list = text_to_phones(ref_text)
        if not phonemes_list:
            return []

        # Aproximação ingênua: distribui duração uniformemente
        # TODO: substituir por MFA/ctc-segmentation
        duration_s = float(self.dur_s) if hasattr(self, 'dur_s') else 4.0
        frame_duration = duration_s / len(phonemes_list) if phonemes_list else 0.1

        alignments = []
        for i, ph in enumerate(phonemes_list):
            alignments.append({
                'phoneme': ph,
                'grapheme': ph,  # TODO: back-map do phoneme pro grafema
                'start_s': i * frame_duration,
                'end_s': (i + 1) * frame_duration,
                'confidence': 0.5,  # TODO: GOP score real via encoder
            })
        self._cache[audio_path] = alignments
        return alignments

    def phoneme_at_time(
        self,
        ref_text: str,
        audio_path: str,
        t_start: float,
        t_end: float,
    ) -> tuple[Optional[str], Optional[str], float]:
        """
        Retorna o fonema (esperado) que cai no intervalo [t_start, t_end].
        
        Returns:
            (phoneme, grapheme, confidence)
            Se múltiplos fonemas caem na janela, retorna o dominante.
        """
        alignments = self.align(ref_text, audio_path)
        
        # Filtra fonemas que caem na janela
        in_window = [
            a for a in alignments
            if a['start_s'] < t_end and a['end_s'] > t_start
        ]
        
        if not in_window:
            return None, None, 0.0
        
        # Heurística: maior overlap
        best = max(in_window, key=lambda a: min(a['end_s'], t_end) - max(a['start_s'], t_start))
        return best['phoneme'], best['grapheme'], best['confidence']


# ============================================================================
# GOP score (TODO: encoder de confiança)
# ============================================================================

class GOPScorer:
    """
    Goodness of Pronunciation (GOP): estima confiança de que o fonema foi pronunciado certo.
    
    Entradas: fonema canônico (esperado via G2P) + áudio + timestamp.
    Saída: score [0, 1] de confiança.
    
    Técnicas (refs RESEARCH §14-15):
      - GOP clássico (arXiv 2309.07719): encoder ASR no fonema esperado vs ouvido.
      - Segmentation-free GOP (arXiv 2507.16838): dispensa alinhamento perfeito.
      - MDD L1-aware (arXiv 2309.07719): discrimina sotaque L1 vs L2.
    
    Status: TODO (encoder real requer modelo ASR finetunado em pt-BR).
    """
    def __init__(self):
        self._encoder = None  # TODO: carregar modelo SER/ASR pt-BR

    def score(
        self,
        ref_phoneme: str,
        audio_path: str,
        t_start: float,
        t_end: float,
    ) -> float:
        """
        Estima GOP score do fonema esperado no intervalo de tempo.
        
        Args:
            ref_phoneme: fonema canônico (ex: 'a', 'χ')
            audio_path: caminho do áudio completo
            t_start: início do intervalo
            t_end: fim do intervalo
        
        Returns:
            score [0, 1]. 1.0 = pronuncia perfeitamente, 0.0 = pronuncia totalmente errado.
        
        Status: TODO
            - Sem modelo, retorna score heurístico baseado no tag do marcador.
            - Se marcador é "fonema errado" com severity alta → score baixo.
            - Se sem marcador → score=0.5 (desconhecido).
        """
        # Stub: retorna score fixo (dependeria de encoder real)
        return 0.5


# ============================================================================
# Pipeline principal
# ============================================================================

def load_ratings_jsonl(path: Path) -> list[dict]:
    """Lê ratings.jsonl e retorna lista de records (dict bruto)."""
    records = []
    if not path.exists():
        return records
    
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"WARN: linha inválida em {path}: {e}", file=sys.stderr)
    return records


def enrich_record(record: dict, aligner: ForcedAligner, gop_scorer: GOPScorer) -> dict:
    """
    Enriquece um record de feedback: injeta expected_phoneme/grapheme + GOP nos markers.
    
    Args:
        record: dict bruto do ratings.jsonl
        aligner: ForcedAligner (forced-alignment offline)
        gop_scorer: GOPScorer (Goodness of Pronunciation)
    
    Returns:
        record enriquecido (mesmo record + campos novos nos markers)
    """
    ref_text = record.get('ref_text', '')
    audio_path = record.get('audio', '')
    dur_s = float(record.get('dur_s', 4.0))
    
    # Passa duração pro aligner (stub precisa saber duração total)
    aligner.dur_s = dur_s
    
    # Enriquece cada marker
    enriched_markers = []
    for m_dict in record.get('markers', []):
        m = Marker.from_dict(m_dict)
        
        # Forced-alignment: que fonema cai nesta janela de tempo?
        exp_ph, exp_gr, align_conf = aligner.phoneme_at_time(
            ref_text, audio_path, m.t_start, m.t_end
        )
        
        if exp_ph:
            m.expected_phoneme = exp_ph
            m.expected_grapheme = exp_gr
            
            # GOP score: quão bem foi pronunciado?
            m.gop_score = gop_scorer.score(exp_ph, audio_path, m.t_start, m.t_end)
        
        enriched_markers.append(m.to_dict())
    
    # Retorna record original com markers enriquecidos
    record['markers'] = enriched_markers
    return record


def process_ratings_jsonl(
    input_path: Path,
    output_path: Path,
    dry_run: bool = False,
) -> int:
    """
    Pipeline completo: lê ratings.jsonl, enriquece markers, escreve markers_enriched.jsonl.
    
    Args:
        input_path: ratings.jsonl
        output_path: markers_enriched.jsonl
        dry_run: se True, não escreve (validate only)
    
    Returns:
        número de records processados
    """
    records = load_ratings_jsonl(input_path)
    if not records:
        print(f"WARN: nenhum record em {input_path}", file=sys.stderr)
        return 0
    
    aligner = ForcedAligner()
    gop_scorer = GOPScorer()
    
    enriched = []
    for i, record in enumerate(records):
        try:
            enriched_record = enrich_record(record, aligner, gop_scorer)
            enriched.append(enriched_record)
            
            n_markers = len(enriched_record.get('markers', []))
            n_enriched = sum(
                1 for m in enriched_record.get('markers', [])
                if m.get('expected_phoneme')
            )
            if n_markers > 0:
                print(
                    f"[{i+1}/{len(records)}] {record.get('id', '?')}: "
                    f"{n_enriched}/{n_markers} markers enriquecidos",
                    file=sys.stderr
                )
        except Exception as e:
            print(f"ERRO ao processar record {i}: {e}", file=sys.stderr)
            enriched.append(record)  # fallback: retorna record original
    
    # Escreve output (ou dry-run sem escrever)
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            for record in enriched:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        print(f"OK: {len(enriched)} records salvos em {output_path}", file=sys.stderr)
    else:
        print(f"DRY-RUN: {len(enriched)} records processados (nenhum escrito)", file=sys.stderr)
    
    return len(enriched)


# ============================================================================
# CLI
# ============================================================================

def main():
    ap = argparse.ArgumentParser(
        description='Enriqueça markers com forced-alignment + GOP (v2 do FEEDBACK.md)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  python tools/feedback/enrich_markers.py
  python tools/feedback/enrich_markers.py --input custom_ratings.jsonl --output custom_enriched.jsonl
  python tools/feedback/enrich_markers.py --dry-run  # validate, não escreve

Status do scaffold (2026-06-17):
  - Estrutura de dados: OK (lê/escreve jsonl)
  - Pipeline dry-run: OK (roda, lê e reescreve)
  - Forced-alignment: TODO (MFA/ctc-segmentation como dependência)
  - GOP score: TODO (encoder de confiança)
        '''
    )
    ap.add_argument(
        '--input',
        type=Path,
        default=None,
        help='Caminho de ratings.jsonl (default: tools/rate/ratings.jsonl)'
    )
    ap.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Caminho de saída (default: markers_enriched.jsonl next to input)'
    )
    ap.add_argument(
        '--dry-run',
        action='store_true',
        help='Valida sem escrever (teste)'
    )
    
    args = ap.parse_args()
    
    # Resolve caminhos default
    input_path = args.input or (REPO / 'tools' / 'rate' / 'ratings.jsonl')
    output_path = args.output or input_path.parent / 'markers_enriched.jsonl'
    
    print(f"input:  {input_path}", file=sys.stderr)
    print(f"output: {output_path}", file=sys.stderr)
    print(f"dry_run: {args.dry_run}", file=sys.stderr)
    
    # Valida input exists
    if not input_path.exists():
        print(f"ERRO: {input_path} não existe", file=sys.stderr)
        return 1
    
    # Roda pipeline
    try:
        n = process_ratings_jsonl(input_path, output_path, dry_run=args.dry_run)
        print(f"Sucesso: {n} records processados", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"ERRO fatal: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
