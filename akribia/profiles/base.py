"""The profile abstraction (spec 2.4).

A profile is a plain config object — one dataclass shape, consistent across every
condition, so the engine never needs to know *which* condition it is running,
only *which numbers* to use. This is the actual mechanism behind the §0 thesis
("same math, different miscalibration"): it is true at the code level, not just
conceptually. There is no separate code path per condition — only different
numbers passed into the same ``core`` functions.

The six levers, and which module each one perturbs:

============================  ===========================  =========================
Field                         Module                       Account
============================  ===========================  =========================
``prior_precision_cap``       Kalman (autism)              weak priors / hypo-priors
``precision_flexibility``     HGF (autism)                 HIPPEA / inflexible precision
``discount_factor``           TD learning (ADHD)           steep temporal discounting
``rpe_noise_std``             TD learning (ADHD)            unstable reward gain
``forward_model_update_rate`` Forward model (PPCS)         impaired forward-model update
``injury_noise_std``          Forward model (PPCS)         post-injury afferent noise
============================  ===========================  =========================
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class PrecisionProfile:
    """A condition parameterization. Every named profile is one instance of this
    single shape with specific fields overridden."""

    name: str
    #: ``None`` = unconstrained/learnable. A finite cap models *weak priors*
    #: (autism): prior precision can never exceed this, so raw sensory evidence
    #: dominates and perception is more "literal".
    prior_precision_cap: float | None = None
    #: Meta-learning rate on precision itself (the HGF volatility term). 1.0 =
    #: flexible; → 0 = inflexible (HIPPEA / ``autism_overfitting``).
    precision_flexibility: float = 1.0
    #: γ, the ADHD discounting lever. Lower = steeper devaluation of delayed reward.
    discount_factor: float = 0.95
    #: Injected variance (std-dev) on the reward-prediction-error signal (ADHD).
    rpe_noise_std: float = 0.0
    #: PPCS lever; 1.0 = healthy, lower = impaired forward-model update.
    forward_model_update_rate: float = 1.0
    #: Additive noise (std-dev) on the forward-model comparison (PPCS).
    injury_noise_std: float = 0.0

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def overrides(self) -> dict:
        """The fields that differ from ``baseline`` — useful for the ablation
        grid (spec 2.4) and for legible plot annotations."""
        base = BASELINE
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if f.name != "name" and getattr(self, f.name) != getattr(base, f.name)
        }


#: The neurotypical/healthy reference every other profile is compared against.
#: Not optional even though it is the "boring" one — every task and every plot
#: needs a baseline run as the comparison point (spec 2.4).
BASELINE = PrecisionProfile(name="baseline")
