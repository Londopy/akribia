"""Precision dashboard (spec 2.5 / 4) — one view tying all tasks + profiles
together, plus a per-run prior/posterior/precision time-series view.
"""

from __future__ import annotations

from .. import profiles
from ..tasks import (
    delay_discounting_task,
    illusion_task,
    perturbation_recovery_task,
    self_motion_task,
    volatility_learning_task,
)
from .style import apply_theme, profile_style


def precision_timeseries(task_module, profile_name: str = "baseline"):
    """Plot observation, prediction and precision over time for one run."""
    import matplotlib.pyplot as plt

    apply_theme()
    res = task_module.run(profiles.get(profile_name))
    traj = res["trajectory"]
    t = [p["t"] for p in traj]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(t, [p["observation"] for p in traj], color="gray", alpha=0.6, label="observation")
    ax1.plot(t, [p["prediction"] for p in traj], color="black", label="prediction")
    ax1.set_ylabel("value"); ax1.legend(fontsize=8)
    ax2.plot(t, [p["precision"] for p in traj], color="#0072B2", label="precision")
    ax2.set_xlabel("time step"); ax2.set_ylabel("precision"); ax2.legend(fontsize=8)
    fig.suptitle(f"{getattr(task_module,'TASK','task')} — {profile_name}")
    fig.tight_layout()
    return fig


def battery_dashboard(profile_names: list[str] | None = None):
    """A single figure tying every task to a headline metric across profiles."""
    import matplotlib.pyplot as plt

    apply_theme()
    profile_names = profile_names or profiles.names()
    panels = [
        (illusion_task, "illusion_score", "Illusion susceptibility"),
        (volatility_learning_task, "trials_to_reconverge", "Volatility: trials-to-reconverge"),
        (delay_discounting_task, "auc_impulsivity", "Discounting: AUC (low=impulsive)"),
        (self_motion_task, "recovery_steps_mean", "Vestibular: recovery steps"),
        (perturbation_recovery_task, "recovery_time_mean", "Perturbation: recovery time"),
        (perturbation_recovery_task, "recovery_jitter_mean", "Perturbation: jitter (erratic)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    hatches = ["", "//", "..", "xx", "\\\\", "++", "oo", "**"]
    for ax, (mod, key, title) in zip(axes.flat, panels, strict=False):
        for i, pname in enumerate(profile_names):
            val = mod.run(profiles.get(pname))["summary"].get(key)
            if val is None:
                continue
            st = profile_style(pname, i)
            ax.bar(i, val, color=st["color"], edgecolor="black",
                   hatch=hatches[i % len(hatches)])
        ax.set_title(title, fontsize=10)
        ax.set_xticks(range(len(profile_names)))
        ax.set_xticklabels([p.replace("_", "\n") for p in profile_names],
                           rotation=0, fontsize=6)
    fig.suptitle("akribia — one engine, three miscalibrations, six levers", fontsize=14)
    fig.tight_layout()
    return fig
