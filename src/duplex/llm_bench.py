"""Bench de LLM pro Maya-BR: latência até a 1ª SENTENÇA (o que destrava o TTS).

Compara endpoints OpenAI-compatible com a persona real e prompts de conversa.
Decisão Gemini × Maritaca (REPLAN: testar os dois) com números, não vibe.

  python -m src.duplex.llm_bench \
    --endpoint gemini=https://generativelanguage.googleapis.com/v1beta/openai/:gemini-2.0-flash:$GEMINI_KEY \
    --endpoint maritaca=https://chat.maritaca.ai/api:sabia-3:$MARITACA_KEY \
    --rounds 5

Saída: p50/p95 de (1º token, 1ª sentença, resposta completa) + nº de sentenças
+ amostra de resposta por modelo. Cole o resultado no VIGIL-LOG.
"""
from __future__ import annotations

import argparse
import statistics
import time

from .llm import LLM

PROMPTS = [
    "Oi, tudo bem? Tava pensando em ir à praia amanhã cedo, o que acha?",
    "Caraca, perdi o ônibus de novo e cheguei atrasado na reunião…",
    "Me explica rapidinho por que o céu é azul?",
    "Tô muito feliz, fechei um projeto grande hoje!",
    "Qual o melhor caminho da Tijuca pra Barra num dia de jogo no Maracanã?",
]


def bench(name: str, base_url: str, model: str, key: str, rounds: int):
    t_first_sent, t_total, n_sents = [], [], []
    sample = ""
    for r in range(rounds):
        llm = LLM(base_url=base_url, model=model, api_key=key)  # histórico zerado
        prompt = PROMPTS[r % len(PROMPTS)]
        t0 = time.perf_counter()
        sents = []
        for sent in llm.reply_stream(prompt):
            if not sents:
                t_first_sent.append(time.perf_counter() - t0)
            sents.append(sent)
        t_total.append(time.perf_counter() - t0)
        n_sents.append(len(sents))
        if r == 0:
            sample = " ".join(sents)

    def p(v, q):
        return statistics.quantiles(v, n=100)[q - 1] if len(v) > 1 else v[0]

    print(f"\n=== {name} ({model}) — {rounds} rodadas ===")
    print(f"  1ª sentença : p50 {p(t_first_sent,50)*1000:6.0f} ms · p95 {p(t_first_sent,95)*1000:6.0f} ms")
    print(f"  total       : p50 {p(t_total,50)*1000:6.0f} ms · p95 {p(t_total,95)*1000:6.0f} ms")
    print(f"  sentenças/resposta: {statistics.mean(n_sents):.1f}")
    print(f"  amostra: {sample[:160]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", action="append", required=True,
                    help="nome=base_url:model:key (repetível)")
    ap.add_argument("--rounds", type=int, default=5)
    a = ap.parse_args()
    for spec in a.endpoint:
        name, rest = spec.split("=", 1)
        base_url, model, key = rest.rsplit(":", 2)
        try:
            bench(name, base_url, model, key, a.rounds)
        except Exception as e:
            print(f"\n=== {name}: FALHOU — {e}")


if __name__ == "__main__":
    main()
