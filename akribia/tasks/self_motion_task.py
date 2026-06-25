"""Self-motion / vestibular mismatch task (spec 2.5 / 1.4).

Simulate a head-rotation command (a 30°/s rotation held for 500 ms, discretised),
compute the forward model's predicted sensory consequence, and compare against a
noisy "actual" vestibular signal (true rotation + Gaussian sensor noise scaled by
the profile's ``injury_noise_std``). Plot mismatch-over-time and the recovery
curve (time for mismatch to decay below threshold) under ``baseline`` vs
``ppcs_forward_model``.

Healthy: the mismatch resolves as the forward model updates. PPCS: the impaired
``forward_model_update_rate`` plus injury noise leaves a persistent unresolved
prediction error that does not habituate.
"""

from __future__ import annotations

import numpy as np

from .. import core
from ..profiles import BASELINE, PrecisionProfile
from ..schema import make_result
from ..seeding import derive_seed
from . import _common

TASK = "self_motion_task"

DT_MS = 10
HOLD_MS = 500
ANGULAR_VELOCITY = 30.0   # deg/s
N_STEPS = HOLD_MS // DT_MS + 30   # include a post-motion settling window
RECOVERY_THRESHOLD = 1.0
N_ENSEMBLE = 40           # seeds averaged for the noisy recovery metric


def _command() -> list[float]:
    cmd = [ANGULAR_VELOCITY] * (HOLD_MS // DT_MS)
    cmd += [0.0] * (N_STEPS - len(cmd))
    return cmd


def run(profile: PrecisionProfile, *, seed: int | None = None) -> dict:
    if seed is None:
        seed = derive_seed(profile.name, TASK)
    cmd = _command()

    traj_raw = core.forward_simulate(
        motor_command=cmd,
        update_rate=profile.forward_model_update_rate,
        injury_noise_std=profile.injury_noise_std,
        sensory_gain=1.0,
        seed=seed,
    )
    mismatches = np.array([row[3] for row in traj_raw])

    # Ensemble recovery time (steps for |mismatch| to fall below threshold and
    # stay), averaged over seeds because injury noise makes a single run noisy.
    recov_samples = []
    for k in range(N_ENSEMBLE):
        tr = core.forward_simulate(cmd, profile.forward_model_update_rate,
                                   profile.injury_noise_std, 1.0,
                                   derive_seed(profile.name, TASK, k))
        m = np.abs(np.array([r[3] for r in tr]))
        rt = next((i for i in range(len(m))
                   if np.all(m[i: i + 5] < RECOVERY_THRESHOLD)), len(m))
        recov_samples.append(rt)
    recovery_steps = float(np.mean(recov_samples))

    trajectory = [
        {"t": float(row[0]), "prediction": float(row[1]), "observation": float(row[2]),
         "precision": 0.0, "prediction_error": float(row[3])}
        for row in traj_raw
    ]
    summary = {
        "forward_model_update_rate": profile.forward_model_update_rate,
        "injury_noise_std": profile.injury_noise_std,
        "recovery_steps_mean": recovery_steps,
        "recovery_steps_std": float(np.std(recov_samples)),
        "peak_mismatch": float(np.max(np.abs(mismatches))),
        "residual_mismatch": float(np.mean(np.abs(mismatches[-10:]))),
        "n_ensemble": N_ENSEMBLE,
    }
    return make_result(
        profile=profile, task=TASK,
        parameters={"angular_velocity": ANGULAR_VELOCITY, "hold_ms": HOLD_MS},
        summary=summary, trajectory=trajectory, seed=seed,
    )


def plot(result: dict):
    import matplotlib.pyplot as plt

    from ..profiles import get
    from ..viz.style import apply_theme, profile_style
    apply_theme()

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, prof in enumerate([BASELINE.name, result["profile"]]):
        r = run(get(prof))
        m = [abs(p["prediction_error"]) for p in r["trajectory"]]
        st = profile_style(prof, i)
        ax.plot(m, color=st["color"], linestyle=st["linestyle"],
                label=f"{prof} (recovery≈{r['summary']['recovery_steps_mean']:.0f} steps)")
    ax.axhline(RECOVERY_THRESHOLD, color="gray", lw=0.7, label="recovery threshold")
    ax.set_xlabel("time step (10 ms)"); ax.set_ylabel("|sensorimotor mismatch|")
    ax.set_title("Vestibular mismatch: PPCS forward model fails to habituate")
    ax.legend()
    return fig


def main() -> None:
    _common.standard_cli(TASK, run, plot)


if __name__ == "__main__":
    main()
