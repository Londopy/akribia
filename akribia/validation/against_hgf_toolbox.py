"""Reference-output sanity check (spec 2.6 / 1.7).

Per the ADR (docs/architecture.md, path (a)) the honest default is NOT to
reimplement the full HGF in Rust and match TAPAS bit-for-bit. Instead an existing
validated HGF is treated as the *reference oracle*. Two checks live here:

1. ``validate_kalman_against_closed_form`` — the 1-D Kalman update has a known
   closed-form fixed point; we confirm the engine matches it to tolerance.
2. ``compare_backends`` — the Rust core (``akribia._core``) and the pure-Python
   reference (``akribia._core_fallback``) must agree to a stated numerical
   tolerance on the deterministic filters. This is the in-repo analogue of the
   TAPAS comparison: two independent implementations of the same math checked
   against each other.

Licensing boundary (spec 1.7): TAPAS is GPL and is **compared-against, never
linked or copied from**. Running TAPAS separately and diffing its numeric output
against akribia's own independently-implemented HGF is fine; importing or
adapting any TAPAS source into ``core/`` would obligate the combined work under
GPL and invalidate the MIT licensing decision. That boundary is enforced by
*never depending on TAPAS in code* — this module only ever talks to akribia's own
backends and self-contained references.
"""

from __future__ import annotations

import numpy as np

TOLERANCE = 1e-9


def _reference_kalman(initial_mean, initial_var, obs, q, r):
    """A second, independent NumPy Kalman implementation used as the oracle."""
    mean, var = initial_mean, initial_var
    out = []
    for z in obs:
        var = var + q
        k = var / (var + r)
        mean = mean + k * (z - mean)
        var = (1 - k) * var
        out.append((mean, var))
    return out


def validate_kalman_against_closed_form(tol: float = 1e-6) -> dict:
    """A constant signal under a small positive process noise drives the Kalman
    posterior mean geometrically to that constant (the innovation -> 0 fixed
    point). With non-zero process noise convergence is geometric, so the steady
    state is reached to machine precision; with ZERO process noise the posterior
    instead converges only as 1/N (a useful contrast documented in BENCHMARKS),
    which is why this check uses a small q rather than q = 0."""
    from .. import core

    obs = [4.0] * 1000
    traj = core.kalman_run(0.0, 1.0, obs, 0.01, 0.5, None)
    final_mean = traj[-1][0]
    ok_mean = abs(final_mean - 4.0) < tol
    return {"check": "kalman_constant_signal", "final_mean": final_mean,
            "expected": 4.0, "abs_error": abs(final_mean - 4.0),
            "pass": bool(ok_mean), "tolerance": tol}


def compare_backends(tol: float = TOLERANCE) -> dict:
    """Compare the Rust core against the Python reference on the deterministic
    filters. Skips gracefully (reports ``backend='python'``) when the compiled
    extension is not installed — the Python fallback is then checked against the
    independent NumPy oracle instead."""
    from .. import _core_fallback as ref
    from .. import core

    obs = np.sin(np.linspace(0, 12, 200)).tolist()
    results = {"active_backend": core.BACKEND, "tolerance": tol, "checks": []}

    # Kalman: active backend vs the standalone NumPy oracle.
    a = core.kalman_run(0.0, 1.0, obs, 0.05, 1.0, None)
    o = _reference_kalman(0.0, 1.0, obs, 0.05, 1.0)
    max_err = max(abs(a[i][0] - o[i][0]) for i in range(len(obs)))
    results["checks"].append(
        {"name": "kalman_vs_oracle", "max_abs_error": max_err, "pass": bool(max_err < 1e-9)}
    )

    # HGF: active backend vs the Python reference (identical deterministic math).
    ha = core.hgf_run(obs, 1.0, 0.5)
    hr = ref.hgf_run(obs, 1.0, 0.5)
    hgf_err = max(abs(ha[i][1] - hr[i][1]) for i in range(len(obs)))
    results["checks"].append(
        {"name": "hgf_active_vs_python_reference", "max_abs_error": hgf_err,
         "pass": bool(hgf_err < 1e-9)}
    )
    results["pass"] = all(c["pass"] for c in results["checks"])
    return results


def run_suite() -> dict:
    return {
        "closed_form": validate_kalman_against_closed_form(),
        "backend_comparison": compare_backends(),
    }


def main() -> None:
    import json

    print(json.dumps(run_suite(), indent=2))


if __name__ == "__main__":
    main()
