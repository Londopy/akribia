"""akribia — a unified computational model of precision-weighted Bayesian inference
across autism, ADHD, and PPCS.

One inference engine. Three miscalibrations. Same math.

This is the Python orchestration layer (spec 2.2). The numerical core lives in the
Rust crate ``core/`` and is compiled into :mod:`akribia._core`; when that compiled
extension is not present (e.g. a checkout without a Rust toolchain) the package
transparently falls back to a pure-Python reference implementation in
:mod:`akribia._core_fallback` that mirrors the same math. Use
:data:`akribia.core.BACKEND` to see which is active.

NOT a diagnostic tool. See ``docs/LIMITATIONS.md`` and the README framing block.
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import core, profiles

__all__ = ["__version__", "core", "profiles"]
