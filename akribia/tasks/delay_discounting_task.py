"""Delay-discounting task (spec 2.5 / 1.3).

A series of binary choices between a fixed smaller-sooner reward ($10 now) and a
larger-later reward whose delay varies (1, 7, 30, 90 days). Standard
behavioural-economics indifference-point elicitation. Run under
``adhd_discounting`` (steep γ) and ``adhd_rpe_noise``; plot the indifference curve
(the LL amount at which choice crosses 50%).

The subjective value of the larger-later reward is the core engine's exponential
discounting ``γ^delay * amount``. The indifference amount at a given delay is the
LL value whose subjective value equals the smaller-sooner reward — i.e.
``SS / γ^delay``. Steeper discounting (lower γ, ADHD) makes the indifference
amount rise far more steeply with delay (you must be offered much more to wait),
which collapses the normalised area-under-the-curve impulsivity measure.
"""

from __future__ import annotations

import numpy as np

from .. import core
from ..profiles import BASELINE, PrecisionProfile
from ..schema import make_result
from ..seeding import derive_seed
from . import _common

TASK = "delay_discounting_task"

SMALLER_SOONER = 10.0
DELAYS = [1, 7, 30, 90]          # days


def _indifference_amount(delay: float, gamma: float) -> float:
    """LL amount whose subjective value equals the smaller-sooner reward."""
    # discounted_value(A, delay, gamma) == SS  ->  A = SS / gamma^delay
    return SMALLER_SOONER / (gamma**delay)


def run(profile: PrecisionProfile, *, seed: int | None = None) -> dict:
    if seed is None:
        seed = derive_seed(profile.name, TASK)
    gamma = profile.discount_factor

    indiff = [_indifference_amount(d, gamma) for d in DELAYS]
    # Subjective value as a fraction of the LL reward at each delay = gamma^delay.
    subj_fraction = [gamma**d for d in DELAYS]
    # Normalised area-under-the-curve impulsivity measure (Myerson et al.):
    # AUC over normalised delay of the subjective-value fraction. Lower = more
    # impulsive. Steep discounting (low gamma) collapses this.
    x = np.array(DELAYS) / max(DELAYS)
    y = np.array(subj_fraction)
    _trapz = getattr(np, "trapezoid", np.trapezoid)  # NumPy 2.0 renamed trapz
    auc = float(_trapz(y, x))

    trajectory = [
        {"t": float(d), "prediction": core.discounted_value(SMALLER_SOONER, d, gamma),
         "observation": SMALLER_SOONER, "precision": 0.0,
         "prediction_error": 0.0}
        for d in DELAYS
    ]
    summary = {
        "discount_factor": gamma,
        "indifference_amounts": {str(d): a for d, a in zip(DELAYS, indiff, strict=False)},
        "subjective_value_fraction": {str(d): f for d, f in zip(DELAYS, subj_fraction, strict=False)},
        "auc_impulsivity": auc,
    }
    return make_result(
        profile=profile, task=TASK, parameters={"smaller_sooner": SMALLER_SOONER,
                                                 "delays": DELAYS},
        summary=summary, trajectory=trajectory, seed=seed,
    )


def plot(result: dict):
    import matplotlib.pyplot as plt

    from ..profiles import get
    from ..viz.style import apply_theme, profile_style
    apply_theme()

    fig, ax = plt.subplots(figsize=(6, 4))
    for i, prof in enumerate([BASELINE.name, result["profile"]]):
        r = run(get(prof))
        amts = [r["summary"]["indifference_amounts"][str(d)] for d in DELAYS]
        st = profile_style(prof, i)
        ax.plot(DELAYS, amts, color=st["color"], linestyle=st["linestyle"],
                marker=st["marker"], label=f"{prof} (AUC={r['summary']['auc_impulsivity']:.2f})")
    ax.set_xlabel("delay (days)"); ax.set_ylabel("indifference amount ($, log)")
    ax.set_yscale("log")
    ax.set_title("Delay discounting: steeper γ → must be offered much more to wait")
    ax.legend()
    return fig


def main() -> None:
    _common.standard_cli(TASK, run, plot)


if __name__ == "__main__":
    main()
