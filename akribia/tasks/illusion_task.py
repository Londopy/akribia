"""Illusion task — a Kanizsa-triangle illusory-contour test (spec 2.5).

The critical design point (spec 2.5): a pixel stimulus must *not* be fed raw into
a Kalman/HGF update. Instead we specify an explicit generative model and feed the
filter a small vector of edge-evidence scalars.

Generative model
----------------
* **Latent** ``C`` — "an illusory triangle is present". Its prior precision is
  what the autism profiles modulate.
* **Observations** — at K probe locations a local edge-evidence scalar
  ``e_k in [0,1]`` from a fixed front end. Three classes of location:
    - *inducer edges* (the real luminance edges of the pac-man mouths): high e_k.
    - *illusory-contour midpoints* (the empty span where a human "sees" an edge):
      e_k ~ 0 — no local evidence.
    - *control region* (an empty patch the triangle hypothesis does NOT predict
      an edge at): e_k ~ 0 — a true negative.
* The triangle ``C`` predicts high edge-evidence at *both* the inducers *and* the
  illusory midpoints, and predicts nothing at the control region.

Inference & score
-----------------
1. Infer ``P(C)`` from the inducer evidence (real bottom-up signal) via the same
   precision-weighted Kalman update used everywhere else.
2. At each probe, the *perceived contour* is the precision-weighted fusion of the
   top-down prediction (``P(C)`` where the triangle predicts an edge, else 0;
   weighted by prior precision — the autism lever) and the bottom-up evidence
   (weighted by sensory precision). This is literally one Kalman update with the
   top-down prediction as prior mean and the local evidence as the observation.
3. **Illusion-susceptibility score** = perceived(illusory midpoint) −
   perceived(control). The control subtraction makes it a clean measure rather
   than a baseline-credulity artifact.

Predicted profile ordering, committed in advance (spec 1.5.2 pre-registration
discipline — NOT a post-hoc fit):
    * ``baseline``           -> clear positive illusion score
    * ``autism_weak_prior``  -> *reduced* score (absent local evidence dominates)
    * ``autism_overfitting`` -> score high but context-rigid (its failure is to
      *update* across trials — the volatility task's job, not this one's)

If ``autism_weak_prior`` does NOT come out lower than baseline here, the
weak-prior implementation has failed and that is a reportable negative result,
not a cue to retune.
"""

from __future__ import annotations

from .. import core
from ..profiles import BASELINE, PrecisionProfile
from ..schema import make_result
from ..seeding import derive_seed
from . import _common

TASK = "illusion_task"

# A 3-inducer Kanizsa triangle: 3 inducer probes, 3 illusory-midpoint probes
# (one per triangle side), and 3 control probes in empty space.
N_INDUCERS = 3
N_MIDPOINTS = 3
N_CONTROLS = 3


def _perceived(top_down: float, bottom_up: float, profile: PrecisionProfile,
               prior_var: float = 1.0, obs_var: float = 1.0) -> float:
    """Precision-weighted fusion of a top-down prediction and local evidence,
    using the core Kalman update with the profile's prior_precision_cap lever."""
    traj = core.kalman_run(
        initial_mean=top_down,
        initial_var=prior_var,
        observations=[bottom_up],
        process_noise=0.0,
        obs_noise=obs_var,
        prior_precision_cap=profile.prior_precision_cap,
    )
    return traj[-1][0]


def run(profile: PrecisionProfile, *, seed: int | None = None,
        inducer_reliability: float = 1.0) -> dict:
    """Run the illusion task under ``profile``. Deterministic (no RNG used)."""
    if seed is None:
        seed = derive_seed(profile.name, TASK)

    # Front-end edge evidence (fixed, not learned).
    inducer_e = [inducer_reliability] * N_INDUCERS   # strong real edges
    midpoint_e = [0.0] * N_MIDPOINTS                 # illusory: no local evidence
    control_e = [0.0] * N_CONTROLS                   # true negative

    # 1. Infer P(C) from inducer evidence: a precision-weighted accumulation.
    #    Prior mean 0 (no triangle), then fuse the real inducer edges.
    c_traj = core.kalman_run(
        initial_mean=0.0, initial_var=10.0,
        observations=inducer_e,
        process_noise=0.0, obs_noise=0.3,
        prior_precision_cap=None,  # inferring C from real evidence is bottom-up
    )
    p_c = max(0.0, min(1.0, c_traj[-1][0]))

    # 2. Perceived contour at each probe.
    #    Top-down prediction: P(C) where the triangle predicts an edge (inducers,
    #    midpoints), 0 at controls (triangle predicts nothing there).
    midpoint_perceived = [
        _perceived(top_down=p_c, bottom_up=e, profile=profile) for e in midpoint_e
    ]
    control_perceived = [
        _perceived(top_down=0.0, bottom_up=e, profile=profile) for e in control_e
    ]

    mp = sum(midpoint_perceived) / len(midpoint_perceived)
    cp = sum(control_perceived) / len(control_perceived)
    illusion_score = mp - cp

    trajectory = []
    for i, e in enumerate(inducer_e):
        trajectory.append({"t": float(i), "prediction": p_c, "observation": e,
                           "precision": 0.0, "prediction_error": e - p_c})
    for j, (e, perc) in enumerate(zip(midpoint_e, midpoint_perceived, strict=False)):
        trajectory.append({"t": float(N_INDUCERS + j), "prediction": perc,
                           "observation": e, "precision": 0.0,
                           "prediction_error": e - perc})

    summary = {
        "p_triangle": p_c,
        "midpoint_perceived": mp,
        "control_perceived": cp,
        "illusion_score": illusion_score,
        "inducer_reliability": inducer_reliability,
    }
    return make_result(
        profile=profile, task=TASK,
        parameters={"inducer_reliability": inducer_reliability},
        summary=summary, trajectory=trajectory, seed=seed,
    )


def plot(result: dict):
    """Plot this profile's illusion score against the baseline reference."""
    import matplotlib.pyplot as plt

    from ..viz.style import apply_theme, profile_style
    apply_theme()

    base = run(BASELINE)
    this = result
    names = [base["profile"], this["profile"]]
    scores = [base["summary"]["illusion_score"], this["summary"]["illusion_score"]]

    fig, ax = plt.subplots(figsize=(5, 4))
    for i, (n, s) in enumerate(zip(names, scores, strict=False)):
        st = profile_style(n, i)
        ax.bar(i, s, color=st["color"], edgecolor="black", hatch=["", "//"][i % 2], label=n)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_ylabel("illusion-susceptibility score\n(midpoint − control)")
    ax.set_title("Kanizsa illusory contour: same engine, different prior precision")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend()
    return fig


def main() -> None:
    _common.standard_cli(TASK, run, plot)


if __name__ == "__main__":
    main()
