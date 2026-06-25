"""Perturbation-recovery task (spec 1.5.1 / 2.5) — the AuDHD literature replication.

Apply a single large, salient prediction error mid-run (analogous to an
emotionally arousing event), then track how long the model's arousal/precision
state takes to return to its pre-perturbation baseline. Run under ``baseline``,
both autism profiles, both ADHD profiles, and ``audhd_emotion_dysregulation``.

The arousal state is modelled with the core reward-learning primitive: an arousal
value relaxes back toward baseline at a rate set by the profile's
``precision_flexibility`` (sluggish updating → slow, smooth recovery — emotional
inertia), under gain noise set by ``rpe_noise_std`` (unstable gain → erratic,
fluctuating recovery). This is exactly the lever split the §1.5.1 hypothesis
makes: autism's contribution is *slow updating* (inertia); ADHD's is *unstable
gain* (erraticness).

Pre-registered predictions (spec 1.5.1 / 1.5.2 discipline):
    * autism-side profiles  -> SLOW, smooth recovery (high recovery time, low
      recovery variability)
    * ADHD-side profiles    -> FAST but ERRATIC recovery (low recovery time, high
      variability) — not uniformly fast
    * audhd_emotion_dysregulation -> a QUALITATIVELY DISTINCT combination (slow
      AND erratic), NOT the numeric average of the two. If it *is* just the
      average, that is evidence against the non-additive hypothesis and is
      reported as such — not quietly reparameterised.
"""

from __future__ import annotations

import numpy as np

from .. import core
from ..profiles import PrecisionProfile
from ..schema import make_result
from ..seeding import derive_seed
from . import _common

TASK = "perturbation_recovery_task"

N_STEPS = 80
PERTURB_AT = 30
PERTURB_MAGNITUDE = 10.0
RECOVERY_THRESHOLD = 1.0     # |arousal| considered "returned to baseline"
N_ENSEMBLE = 60


def _learning_rate(precision_flexibility: float) -> float:
    """Map precision_flexibility -> arousal relaxation rate. Sluggish updating
    (low flexibility) gives a small learning rate = slow return to baseline."""
    return 0.05 + 0.25 * min(precision_flexibility, 1.0)


def _arousal_trajectory(profile: PrecisionProfile, seed: int) -> np.ndarray:
    """Arousal stays at baseline, gets the SAME large kick at the perturbation
    (a salient event hits everyone equally), then RELAXES back toward baseline at
    a rate gated by precision_flexibility, under gain noise gated by rpe_noise_std.

    The relaxation is the core reward-learning primitive run from an initial
    arousal value of PERTURB_MAGNITUDE toward zero "rewards": a small learning
    rate (low flexibility) decays slowly (inertia); rpe noise makes the descent
    erratic. This separates the kick magnitude (same for all) from the recovery
    dynamics (the lever), which the earlier formulation conflated."""
    lr = _learning_rate(profile.precision_flexibility)
    post = core.td_learn_sequence(
        initial_value=PERTURB_MAGNITUDE,
        rewards=[0.0] * (N_STEPS - PERTURB_AT),
        learning_rate=lr,
        discount_factor=profile.discount_factor,
        rpe_noise_std=profile.rpe_noise_std,
        seed=seed,
    )
    arousal = np.concatenate([np.zeros(PERTURB_AT), np.abs(np.array(post))])
    return arousal


def _metrics(arousal: np.ndarray) -> tuple[float, float]:
    """(recovery_time, recovery_jitter).

    * ``recovery_time`` — steps for |arousal| to fall below threshold and stay.
      Slow = emotional inertia (the autism-side signal).
    * ``recovery_jitter`` — mean |second difference| of the settled tail. The
      second difference is ~0 for ANY smooth monotonic curve (whether still
      gently descending or fully settled) and large only for genuine erratic
      fluctuation, so it isolates unstable-gain erraticness (the ADHD-side
      signal) from the smooth-descent trend. This is what makes
      ``audhd_emotion_dysregulation`` land in its own quadrant (slow AND erratic)
      rather than on the line between the two single-mechanism profiles."""
    post = arousal[PERTURB_AT:]
    rt = next((i for i in range(len(post))
               if np.all(post[i: i + 5] < RECOVERY_THRESHOLD)), len(post))
    tail = arousal[-30:]
    jitter = float(np.mean(np.abs(np.diff(tail, 2)))) if len(tail) >= 3 else 0.0
    return float(rt), jitter


def run(profile: PrecisionProfile, *, seed: int | None = None) -> dict:
    if seed is None:
        seed = derive_seed(profile.name, TASK)

    primary = _arousal_trajectory(profile, seed)

    rts, varis = [], []
    for k in range(N_ENSEMBLE):
        a = _arousal_trajectory(profile, derive_seed(profile.name, TASK, k))
        rt, v = _metrics(a)
        rts.append(rt)
        varis.append(v)

    trajectory = [
        {"t": float(i), "prediction": 0.0, "observation": float(primary[i]),
         "precision": 0.0, "prediction_error": float(primary[i])}
        for i in range(len(primary))
    ]
    summary = {
        "recovery_time_mean": float(np.mean(rts)),
        "recovery_time_std": float(np.std(rts)),
        "recovery_jitter_mean": float(np.mean(varis)),
        "perturb_at": PERTURB_AT,
        "precision_flexibility": profile.precision_flexibility,
        "rpe_noise_std": profile.rpe_noise_std,
        "n_ensemble": N_ENSEMBLE,
    }
    return make_result(
        profile=profile, task=TASK,
        parameters={"perturb_magnitude": PERTURB_MAGNITUDE},
        summary=summary, trajectory=trajectory, seed=seed,
    )


def plot(result: dict):
    """Recovery curves + a recovery-time-vs-variability scatter that places
    audhd_emotion_dysregulation in its own quadrant (the §1.5.1 'distinct, not
    averaged' claim)."""
    import matplotlib.pyplot as plt

    from ..profiles import get
    from ..viz.style import apply_theme, profile_style
    apply_theme()

    panel = ["baseline", "autism_overfitting", "adhd_rpe_noise",
             "audhd_emotion_dysregulation"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for i, prof in enumerate(panel):
        r = run(get(prof))
        a = [p["observation"] for p in r["trajectory"]]
        st = profile_style(prof, i)
        ax1.plot(a, color=st["color"], linestyle=st["linestyle"], label=prof)
        ax2.scatter(r["summary"]["recovery_time_mean"],
                    r["summary"]["recovery_jitter_mean"],
                    s=120, color=st["color"], marker=st["marker"],
                    edgecolor="black", label=prof)
    ax1.axvline(PERTURB_AT, color="gray", lw=0.7)
    ax1.set_xlabel("time step"); ax1.set_ylabel("arousal |deviation|")
    ax1.set_title("Recovery curves after a salient perturbation")
    ax1.legend(fontsize=8)
    ax2.set_xlabel("recovery time (slow →)")
    ax2.set_ylabel("recovery jitter (erratic ↑)")
    ax2.set_title("AuDHD is distinct, not the average")
    ax2.legend(fontsize=8)
    return fig


def main() -> None:
    _common.standard_cli(TASK, run, plot)


if __name__ == "__main__":
    main()
