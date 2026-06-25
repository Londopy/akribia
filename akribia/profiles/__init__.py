"""The akribia profile catalog (spec 2.4).

Each named profile is an instance of the single :class:`PrecisionProfile` shape
with specific fields overridden, defined in its own module (one file per profile,
matching the spec's architecture tree). The starting values are placeholders
chosen to produce *visibly different* behaviour; the values worth keeping are
whatever the sensitivity sweeps in ``akribia.validation`` show give a clean,
interpretable effect without saturating (spec 2.4).
"""

from __future__ import annotations

from .adhd_discounting import ADHD_DISCOUNTING
from .adhd_rpe_noise import ADHD_RPE_NOISE
from .audhd_emotion_dysregulation import AUDHD_EMOTION_DYSREGULATION
from .autism_overfitting import AUTISM_OVERFITTING
from .autism_weak_prior import AUTISM_WEAK_PRIOR
from .base import BASELINE, PrecisionProfile
from .comorbid import COMORBID
from .ppcs_forward_model import PPCS_FORWARD_MODEL

#: Canonical registry, keyed by name. ``baseline`` first by convention.
CATALOG: dict[str, PrecisionProfile] = {
    p.name: p
    for p in (
        BASELINE,
        AUTISM_WEAK_PRIOR,
        AUTISM_OVERFITTING,
        ADHD_DISCOUNTING,
        ADHD_RPE_NOISE,
        PPCS_FORWARD_MODEL,
        COMORBID,
        AUDHD_EMOTION_DYSREGULATION,
    )
}


def get(name: str) -> PrecisionProfile:
    """Look up a profile by name. Raises ``KeyError`` listing the valid names."""
    try:
        return CATALOG[name]
    except KeyError as exc:
        raise KeyError(f"unknown profile {name!r}; choose one of {sorted(CATALOG)}") from exc


def names() -> list[str]:
    return list(CATALOG)


__all__ = [
    "ADHD_DISCOUNTING",
    "ADHD_RPE_NOISE",
    "AUDHD_EMOTION_DYSREGULATION",
    "AUTISM_OVERFITTING",
    "AUTISM_WEAK_PRIOR",
    "BASELINE",
    "CATALOG",
    "COMORBID",
    "PPCS_FORWARD_MODEL",
    "PrecisionProfile",
    "get",
    "names",
]
