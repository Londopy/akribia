"""Python-side benchmarks for the Rust-vs-Python claim (spec 2.10).

Quantifies the gap instead of asserting it. Reports updates/sec for the active
akribia backend vs a naive pure-Python Kalman loop, plus a sweep wall-clock. The
numbers land in docs/BENCHMARKS.md. These are NOT correctness tests and never run
in the fast PR CI loop (spec 2.15) — they belong in the scheduled validation run.

Run: ``python benches/py_kalman_bench.py``  (or via pytest-benchmark if desired).
"""

from __future__ import annotations

import time

import numpy as np

from akribia import core


def _naive_python_kalman(initial_mean, initial_var, obs, q, r):
    mean, var = initial_mean, initial_var
    prec_like = 1.0 / r
    out = []
    for z in obs:
        var = var + q
        prec_prior = 1.0 / var
        post = prec_prior + prec_like
        mean = (prec_prior * mean + prec_like * z) / post
        var = 1.0 / post
        out.append((mean, var))
    return out


def _time(fn, *args, repeat=5):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)
    return best


def bench_kalman(n: int = 100_000) -> dict:
    obs = np.sin(np.linspace(0, 100, n)).tolist()
    t_backend = _time(core.kalman_run, 0.0, 1.0, obs, 0.01, 1.0, None)
    t_naive = _time(_naive_python_kalman, 0.0, 1.0, obs, 0.01, 1.0)
    return {
        "n_updates": n,
        "active_backend": core.BACKEND,
        "backend_sec": t_backend,
        "naive_python_sec": t_naive,
        "backend_updates_per_sec": n / t_backend,
        "speedup_vs_naive_python": t_naive / t_backend,
    }


def bench_sweep(points: int = 50, length: int = 2000) -> dict:
    obs = [0.0] * (length // 2) + [10.0] * (length // 2)
    t0 = time.perf_counter()
    for k in range(points):
        flex = 0.02 + k * 0.03
        core.hgf_run(obs, 1.0, flex)
    return {"sweep_points": points, "series_length": length,
            "active_backend": core.BACKEND, "wall_clock_sec": time.perf_counter() - t0}


def main() -> None:
    import json
    print(json.dumps({"kalman": bench_kalman(), "sweep": bench_sweep()}, indent=2))


if __name__ == "__main__":
    main()
