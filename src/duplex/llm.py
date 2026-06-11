"""LLM de conteúdo — plugável via endpoint OpenAI-compatible (REPLAN: o cérebro
é trocável sem tocar na voz). Funciona com Gemini (openai-compat), Maritaca,
sglang, ollama, vLLM. Streaming p/ mandar a 1ª sentença ao TTS o quanto antes."""
from __future__ import annotations

import re
from pathlib import Path

PERSONA_PATH = Path(__file__).parent / "persona_ptbr.txt"
_SENT_END = re.compile(r"[.!?…]\s")


class LLM:
    def __init__(self, base_url: str, model: str, api_key: str = "x",
                 persona_path: Path = PERSONA_PATH, max_history: int = 16):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.history: list[dict] = []
        self.max_history = max_history
        self.system = persona_path.read_text(encoding="utf-8")

    def reply_stream(self, user_text: str):
        """Gera a resposta; yield por SENTENÇA (p/ TTS começar cedo)."""
        self.history.append({"role": "user", "content": user_text})
        msgs = ([{"role": "system", "content": self.system}]
                + self.history[-self.max_history:])
        stream = self.client.chat.completions.create(
            model=self.model, messages=msgs, stream=True,
            temperature=0.8, max_tokens=160)
        buf, full = "", ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            buf += delta
            full += delta
            m = _SENT_END.search(buf)
            while m:
                sent, buf = buf[: m.end()].strip(), buf[m.end():]
                if sent:
                    yield sent
                m = _SENT_END.search(buf)
        if buf.strip():
            yield buf.strip()
        self.history.append({"role": "assistant", "content": full.strip()})

    def mark_interrupted(self, frac: float):
        """Pós barge-in: o usuário só ouviu `frac` da última resposta — corrige o
        histórico pra o LLM não 'achar que falou' o que foi cortado."""
        if not self.history or self.history[-1]["role"] != "assistant" or frac >= 0.99:
            return
        words = self.history[-1]["content"].split()
        cut = max(1, int(len(words) * frac))
        self.history[-1]["content"] = (" ".join(words[:cut])
                                       + " … [interrompido pelo usuário]")
