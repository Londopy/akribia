"""Volatility-switching learning task (spec 2.5 / 1.2).

A two-armed bandit whose higher-reward-probability arm flips (0.8/0.2 -> 0.2/0.8)
at an unsignalled, randomised trial (uniformly in [40, 60] of a 100-trial block).
This is the standard paradigm for testing flexible precision adjustment, and it
directly tests the overfitting (HIPPEA) hypothesis by measuring
**trials-to-reconverge** after the flip — NOT just the steady-state endpoint.

The literature's specific, pre-registered prediction (spec 1.2): autistic profiles
show a *slower convergence curve* after the switch — a transient reconvergence
delay, not a permanent steady-state deficit. The interesting effect is in the
transient. ``autism_overfitting`` (low ``precision_flexibility``) should therefore
take more trials to reconverge than ``baseline``; both should ultimately reach a
comparable belief.
"""

from __future__ import annotations

import numpy as np

from .. import core
from ..profiles import BASELINE, PrecisionProfile
from ..schema import make_result
from ..seeding import derive_seed
from . import _common

TASK = "volatility_learning_task"

N_TRIALS = 100
P_HIGH = 0.8
P_LOW = 0.2
FLIP_WINDOW = (40, 60)
N_ENSEMBLE = 60  # stimulus seeds averaged for the headline metric (spec 2.6)


def _generate_outcomes(seed: int) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(seed)
    flip = int(rng.integers(FLIP_WINDOW[0], FLIP_WINDOW[1] + 1))
    outcomes = np.empty(N_TRIALS)
    outcomes[:flip] = (rng.random(flip) < P_HIGH).astype(float)
    outcomes[flip:] = (rng.random(N_TRIALS - flip) < P_LOW).astype(float)
    return outcomes, flip


def _adapt_trials(predictions: np.ndarray, flip: int) -> int:
    """Trials after the flip for the belief to travel HALFWAY from its pre-flip
    level toward the new level. Robust to each profile's own pre-flip belief (so
    it measures adaptation *speed*, not a fixed absolute threshold a sluggish
    learner could trivially satisfy). Saturates at the trials available."""
    pre = float(np.mean(predictions[max(0, flip - 10) : flip]))
    target = pre + 0.5 * (P_LOW - pre)
    for i in range(flip, len(predictions)):
        if predictions[i] <= target:
            return i - flip
    return len(predictions) - flip


def run(profile: PrecisionProfile, *, seed: int | None = None) -> dict:
    # Stimulus seed is profile-INDEPENDENT so every profile sees the same
    # outcome sequence and flip point — the only thing that varies is the
    # profile's precision_flexibility (a fair within-stimulus comparison).
    if seed is None:
        seed = derive_seed(TASK, "stimulus")
    outcomes, flip = _generate_outcomes(seed)

    traj_raw = core.hgf_run(
        observations=outcomes.tolist(),
        obs_noise=1.0,
        precision_flexibility=profile.precision_flexibility,
    )
    predictions = np.array([row[1] for row in traj_raw])  # pred per step
    pre_flip_belief = float(np.mean(predictions[max(0, flip - 10) : flip]))
    end_belief = float(np.mean(predictions[-10:]))

    # Headline metric is an ENSEMBLE MEAN over many profile-independent stimulus
    # seeds (spec 2.6: report distributions, not point estimates) -- a single
    # trial's trials-to-reconverge is too noisy to compare profiles by.
    adapt_samples = []
    for k in range(N_ENSEMBLE):
        outs_k, flip_k = _generate_outcomes(derive_seed(TASK, "stimulus", k))
        tr_k = core.hgf_run(outs_k.tolist(), 1.0, profile.precision_flexibility)
        preds_k = np.array([r[1] for r in tr_k])
        adapt_samples.append(_adapt_trials(preds_k, flip_k))
    reconv = float(np.mean(adapt_samples))
    reconv_std = float(np.std(adapt_samples))

    trajectory = [
        {
            "t": float(i),
            "prediction": float(row[1]),
            "observation": float(row[2]),
            "precision": float(row[3]),
            "prediction_error": float(row[4]),
        }
        for i, row in enumerate(traj_raw)
    ]
    summary = {
        "flip_trial": flip,
        "trials_to_reconverge": reconv,            # ensemble mean (spec 2.6)
        "trials_to_reconverge_std": reconv_std,
        "n_ensemble": N_ENSEMBLE,
        "pre_flip_belief": pre_flip_belief,
        "end_belief": end_belief,
        "precision_flexibility": profile.precision_flexibility,
    }
    return make_result(
        profile=profile, task=TASK, parameters={"n_trials": N_TRIALS},
        summary=summary, trajectory=trajectory, seed=seed,
    )


def plot(result: dict):
    import matplotlib.pyplot as plt

    from ..viz.style import apply_theme, profile_style
    apply_theme()

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, prof in enumerate([BASELINE.name, result["profile"]]):
        from ..profiles import get
        r = run(get(prof))
        preds = [p["prediction"] for p in r["trajectory"]]
        st = profile_style(prof, i)
        ax.plot(preds, color=st["color"], linestyle=st["linestyle"], label=prof)
        ax.axvline(r["summary"]["flip_trial"], color=st["color"], linestyle=":", alpha=0.4)
    ax.axhline(P_HIGH, color="gray", lw=0.6); ax.axhline(P_LOW, color="gray", lw=0.6)
    ax.set_xlabel("trial"); ax.set_ylabel("belief about arm-A reward prob.")
    ax.set_title("Volatility switch: trials-to-reconverge after an unsignalled flip")
    ax.legend()
    return fig


def main() -> None:
    _common.standard_cli(TASK, run, plot)


if __name__ == "__main__":
    main()
