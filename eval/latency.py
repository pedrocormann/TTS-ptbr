"""
Latency / RTF instrumentation, reused by all spikes. RTF = gen_time / audio_sec
(<1 = faster than real-time, the streaming floor). e2e p50/p95 vs the 800ms budget.

  from eval.latency import Timer, summarize
  with Timer() as t: audio = model.generate(...)
  rec.append(t.rtf(audio_seconds=len(audio)/sr))
  summarize(rec, budget_ms=800)
"""
import statistics
import time


class Timer:
    def __enter__(self):
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.synchronize()
        except Exception:
            pass
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.synchronize()
        except Exception:
            pass
        self.dt = time.perf_counter() - self._t0

    def rtf(self, audio_seconds: float) -> float:
        return self.dt / audio_seconds if audio_seconds > 0 else float("inf")


def summarize(latencies_s, budget_ms: float = 800.0, label: str = "e2e"):
    if not latencies_s:
        print(f"[{label}] no samples")
        return {}
    ms = sorted(x * 1000 for x in latencies_s)
    p50 = statistics.median(ms)
    p95 = ms[min(len(ms) - 1, int(0.95 * len(ms)))]
    res = {"p50_ms": p50, "p95_ms": p95, "n": len(ms),
           "pass": p50 < budget_ms}
    print(f"[{label}] p50={p50:.0f}ms p95={p95:.0f}ms n={len(ms)} "
          f"budget={budget_ms:.0f}ms -> {'PASS' if res['pass'] else 'FAIL'}")
    return res
