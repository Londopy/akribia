"""Shared colorblind-safe palette + line-style theme (spec 9).

A project visualizing perceptual/cognitive differences has an obvious reason to
make its own outputs perceivable by the widest audience — including the exact
populations it models. Two rules, applied here once so they can't drift:

1. The default cycle is the **Okabe-Ito** colorblind-safe palette, not
   matplotlib's default (the multi-profile comparison grids are unreadable to
   ~1 in 12 men under default colors).
2. **Never encode meaning in colour alone** — every profile gets a distinct
   ``(color, linestyle, marker)`` triple, so figures stay interpretable in
   grayscale, colorblind vision, or a quick low-fidelity glance.

Import :func:`profile_style` / :func:`apply_theme` everywhere; do not hand-pick
colours per plot.
"""

from __future__ import annotations

# Okabe & Ito (2008) colorblind-safe qualitative palette.
OKABE_ITO = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
}

# A stable (color, linestyle, marker) per profile — colour is never the only cue.
PROFILE_STYLE: dict[str, dict[str, str]] = {
    "baseline": {"color": OKABE_ITO["black"], "linestyle": "-", "marker": "o"},
    "autism_weak_prior": {"color": OKABE_ITO["blue"], "linestyle": "--", "marker": "s"},
    "autism_overfitting": {"color": OKABE_ITO["sky_blue"], "linestyle": "-.", "marker": "^"},
    "adhd_discounting": {"color": OKABE_ITO["vermillion"], "linestyle": "--", "marker": "D"},
    "adhd_rpe_noise": {"color": OKABE_ITO["orange"], "linestyle": ":", "marker": "v"},
    "ppcs_forward_model": {"color": OKABE_ITO["bluish_green"], "linestyle": "-.", "marker": "P"},
    "comorbid": {"color": OKABE_ITO["reddish_purple"], "linestyle": "--", "marker": "X"},
    "audhd_emotion_dysregulation": {"color": OKABE_ITO["reddish_purple"], "linestyle": "-", "marker": "*"},
}

_FALLBACK_CYCLE = list(OKABE_ITO.values())


def profile_style(name: str, index: int = 0) -> dict[str, str]:
    """Return the ``(color, linestyle, marker)`` triple for a profile name."""
    if name in PROFILE_STYLE:
        return PROFILE_STYLE[name]
    linestyles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "D", "v", "P", "X", "*"]
    return {
        "color": _FALLBACK_CYCLE[index % len(_FALLBACK_CYCLE)],
        "linestyle": linestyles[index % len(linestyles)],
        "marker": markers[index % len(markers)],
    }


def apply_theme() -> None:
    """Set the Okabe-Ito palette as matplotlib's default property cycle."""
    import matplotlib as mpl
    from cycler import cycler

    mpl.rcParams["axes.prop_cycle"] = cycler(color=list(OKABE_ITO.values()))
    mpl.rcParams["figure.facecolor"] = "white"
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.alpha"] = 0.3
    mpl.rcParams["font.size"] = 11
