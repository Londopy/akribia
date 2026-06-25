"""Backend loader for the akribia inference engine.

Tries to import the compiled Rust extension :mod:`akribia._core`; if it is not
present, transparently falls back to the pure-Python reference in
:mod:`akribia._core_fallback`. Either way the same call surface is exported, so
the rest of the package (profiles, tasks, viz, validation) never needs to know
which backend is running.

    >>> from akribia import core
    >>> core.BACKEND          # 'rust' or 'python'
    >>> traj = core.kalman_run(0.0, 1.0, [1, 2, 3], 0.01, 1.0)
"""

from __future__ import annotations

try:  # pragma: no cover - exercised by whichever backend is installed
    from . import _core as _backend  # type: ignore[attr-defined]

    BACKEND = "rust"
    AkribiaException = _backend.AkribiaException
    InvalidParameter = _backend.InvalidParameter
    NumericalDivergence = _backend.NumericalDivergence
except ImportError:
    from . import _core_fallback as _backend

    BACKEND = "python"
    AkribiaException = _backend.AkribiaException
    InvalidParameter = _backend.InvalidParameter
    NumericalDivergence = _backend.NumericalDivergence

kalman_run = _backend.kalman_run
hgf_run = _backend.hgf_run
td_learn_sequence = _backend.td_learn_sequence
discounted_value = _backend.discounted_value
forward_simulate = _backend.forward_simulate

__all__ = [
    "BACKEND",
    "AkribiaException",
    "InvalidParameter",
    "NumericalDivergence",
    "discounted_value",
    "forward_simulate",
    "hgf_run",
    "kalman_run",
    "td_learn_sequence",
]
