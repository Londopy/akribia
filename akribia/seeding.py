"""Deterministic seeding policy (spec 2.6.1).

A single, deliberate seeding strategy spanning the Python orchestration and the
Rust core. Every function boundary that touches randomness takes an explicit
seed; nothing reaches for ambient/global RNG state. ``derive_seed`` makes it easy
to fan one master seed out into per-(profile, task, replicate) sub-seeds that are
stable and collision-resistant, so a whole battery is reproducible from one
integer.

Honesty about the limit of this guarantee (spec 2.6.1): same seed + same code
reproduces the same *distribution*, and on the same hardware the same exact
trajectory. It does NOT guarantee bit-for-bit identical floating-point results
across CPU architectures, because floating-point summation is not associative.
What we claim: reproducible to floating-point tolerance, identical on identical
hardware.
"""

from __future__ import annotations

import hashlib

DEFAULT_SEED = 20260624  # the project's canonical master seed


def derive_seed(*parts: object, master: int = DEFAULT_SEED) -> int:
    """Derive a stable 64-bit sub-seed from a master seed and arbitrary labels.

    Deterministic across runs and machines (uses SHA-256 of the string form, not
    Python's salted ``hash``), so ``derive_seed("autism_weak_prior", "illusion", 3)``
    always yields the same value.
    """
    key = "|".join([str(master), *(str(p) for p in parts)])
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")
