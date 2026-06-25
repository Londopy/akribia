"""Side-by-side condition comparison plots (spec 2.5 / 9).

Every plot pairs colour with a distinct line style/marker per profile (never
colour alone) via :mod:`akribia.viz.style`, so figures stay readable in
grayscale and colorblind vision.
"""

from __future__ import annotations

from .. import profiles
from .style import apply_theme, profile_style


def trajectory_grid(task_module, profile_names: list[str] | None = None,
                    value_key: str = "prediction", title: str | None = None):
    """Overlay one task's trajectory across several profiles on a single axis."""
    import matplotlib.pyplot as plt

    apply_theme()
    profile_names = profile_names or profiles.names()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, pname in enumerate(profile_names):
        res = task_module.run(profiles.get(pname))
        series = [pt[value_key] for pt in res["trajectory"]]
        if not series:
            continue
        st = profile_style(pname, i)
        ax.plot(series, color=st["color"], linestyle=st["linestyle"], label=pname)
    ax.set_xlabel("time step")
    ax.set_ylabel(value_key)
    ax.set_title(title or f"{getattr(task_module, 'TASK', 'task')} across profiles")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def metric_bars(task_module, metric_key: str, profile_names: list[str] | None = None,
                title: str | None = None):
    """Bar chart of one scalar summary metric across profiles (hatched per
    profile so it reads in grayscale)."""
    import matplotlib.pyplot as plt

    apply_theme()
    profile_names = profile_names or profiles.names()
    hatches = ["", "//", "..", "xx", "\\\\", "++", "oo", "**"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, pname in enumerate(profile_names):
        res = task_module.run(profiles.get(pname))
        val = res["summary"].get(metric_key)
        if val is None:
            continue
        st = profile_style(pname, i)
        ax.bar(i, val, color=st["color"], edgecolor="black",
               hatch=hatches[i % len(hatches)], label=pname)
    ax.set_xticks(range(len(profile_names)))
    ax.set_xticklabels(profile_names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(metric_key)
    ax.set_title(title or f"{metric_key} across profiles")
    fig.tight_layout()
    return fig
