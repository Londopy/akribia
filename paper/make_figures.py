"""Generate every figure and LaTeX table used by the akribia papers.

Run from the repo root:  python paper/make_figures.py
Outputs: paper/figures/*.pdf  and  paper/tables/*.tex  and paper/data/*.json

All numbers come from live runs of the installed package — nothing is transcribed
from documentation.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import SymLogNorm

from akribia import core, profiles
from akribia.tasks import illusion_task as IL
from akribia.tasks import multi_task_battery as MB
from akribia.tasks import perturbation_recovery_task as PR
from akribia.tasks import self_motion_task as SM
from akribia.tasks import volatility_learning_task as VL
from akribia.validation import parameter_recovery as PREC
from akribia.validation import sensitivity as SENS
from akribia.viz.style import OKABE_ITO, profile_style

# Headless rendering: set before any figure is created, after the import block
# so the imports stay sorted.
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
TAB = ROOT / "tables"
DATA = ROOT / "data"
for d in (FIG, TAB, DATA):
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 9,
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
})

SHORT = {
    "baseline": "baseline",
    "autism_weak_prior": "autism\nweak prior",
    "autism_overfitting": "autism\noverfitting",
    "adhd_discounting": "ADHD\ndiscounting",
    "adhd_rpe_noise": "ADHD\nRPE noise",
    "ppcs_forward_model": "PPCS\nfwd model",
    "comorbid": "comorbid\n(ablation)",
    "audhd_emotion_dysregulation": "AuDHD\nemot. dysreg.",
}
ORDER = list(SHORT)

TASK_METRIC = {
    "illusion_task": ("illusion_score", "Illusion\nsusceptibility"),
    "volatility_learning_task": ("trials_to_reconverge", "Trials to\nreconverge"),
    "delay_discounting_task": ("auc_impulsivity", "Discounting\nAUC"),
    "self_motion_task": ("recovery_steps_mean", "Vestibular\nrecovery steps"),
    "perturbation_recovery_task": ("recovery_time_mean", "Perturbation\nrecovery time"),
}


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", FIG / f"{name}.pdf")


# --------------------------------------------------------------------------
# Data collection
# --------------------------------------------------------------------------
print("running battery...")
battery = MB.run_all(ORDER)
interaction = MB.interaction_analysis()
recovery = PREC.run_suite(n_seeds=20)
sweeps = SENS.run_all()
# Seed-provenance probe: two of the five tasks derive their ensemble seeds from
# the PROFILE NAME, so identical parameters under a different name see a
# different noise stream. We measure how large that confound is rather than
# assuming it away (reported in the Limitations section of the papers).
def _name_seed_spread():
    out = {}
    for task_mod, task_key, prof_name, metric in (
            (PR, "perturbation_recovery_task", "audhd_emotion_dysregulation", "recovery_time_mean"),
            (PR, "perturbation_recovery_task", "audhd_emotion_dysregulation", "recovery_jitter_mean"),
            (SM, "self_motion_task", "ppcs_forward_model", "recovery_steps_mean")):
        base_p = profiles.get(prof_name)
        vals = [task_mod.run(replace(base_p, name=f"_nameprobe{k}"))["summary"][metric]
                for k in range(12)]
        out[f"{task_key}.{metric}"] = {
            "n_renames": 12, "mean": float(np.mean(vals)), "sd": float(np.std(vals)),
            "min": float(min(vals)), "max": float(max(vals))}
    return out

name_seed = _name_seed_spread()
json.dump({"battery": battery, "interaction": interaction,
           "recovery": recovery, "sweeps": sweeps,
           "name_seed_sensitivity": name_seed, "backend": core.BACKEND},
          open(DATA / "results.json", "w"), indent=2)


# --------------------------------------------------------------------------
# Figure 1 — the dissociation matrix (headline)
# --------------------------------------------------------------------------
def fig_dissociation():
    tasks = list(TASK_METRIC)
    M = np.zeros((len(ORDER), len(tasks)))
    txt = np.empty((len(ORDER), len(tasks)), dtype=object)
    for i, p in enumerate(ORDER):
        for j, t in enumerate(tasks):
            key = TASK_METRIC[t][0]
            v = battery[t][p][key]
            b = battery[t]["baseline"][key]
            rel = (v - b) / abs(b) if b else 0.0
            M[i, j] = rel
            # exact equality: these cells really are bit-identical to baseline
            txt[i, j] = "—" if v == b else f"{rel*100:+.0f}%"

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    norm = SymLogNorm(linthresh=0.05, vmin=-1.2, vmax=10, base=10)
    im = ax.imshow(M, cmap="RdBu_r", norm=norm, aspect="auto")
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels([TASK_METRIC[t][1] for t in tasks], fontsize=8)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([SHORT[p].replace("\n", " ") for p in ORDER], fontsize=8)
    for i in range(len(ORDER)):
        for j in range(len(tasks)):
            ax.text(j, i, txt[i, j], ha="center", va="center", fontsize=7.5,
                    color="black" if abs(M[i, j]) < 0.8 else "white")
    ax.set_xticks(np.arange(-.5, len(tasks), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("signed change from baseline (symlog)", fontsize=8)
    ax.set_title("Lever effects stay confined to the modules they are wired into",
                 fontsize=9.5)
    save(fig, "fig_dissociation")


# --------------------------------------------------------------------------
# Figure 2 — illusion task (the golden path)
# --------------------------------------------------------------------------
def fig_illusion():
    profs = ["baseline", "autism_weak_prior", "autism_overfitting"]
    # NOTE on the first bar: this is the inferred P(triangle), computed from the
    # real inducer edges with the prior-precision cap deliberately BYPASSED
    # (illusion_task.py passes prior_precision_cap=None there). It is therefore
    # identical across profiles by construction, not as an empirical finding.
    # The control bar is identically zero for every profile for the same reason:
    # _perceived(top_down=0, bottom_up=0) returns 0 for any cap. Only the middle
    # bar is a profile-sensitive quantity.
    labels = ["inferred P(triangle)\nfrom real edges\n(cap bypassed)",
              "illusory midpoint\n(top-down, capped)",
              "control\n(identically 0)"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9),
                             gridspec_kw={"width_ratios": [1.5, 1]})

    ax = axes[0]
    w = 0.25
    x = np.arange(3)
    for k, p in enumerate(profs):
        r = IL.run(profiles.get(p))
        s = r["summary"]
        traj = r["trajectory"]
        inducer = float(np.mean([q["prediction"] for q in traj[:3]]))
        vals = [inducer, s["midpoint_perceived"], s["control_perceived"]]
        st = profile_style(p, k)
        ax.bar(x + (k - 1) * w, vals, w, label=p.replace("_", " "),
               color=st["color"], edgecolor="black", linewidth=0.5,
               hatch=["", "//", "xx"][k], alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("perceived contour strength")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Kanizsa probe responses", fontsize=9)

    ax = axes[1]
    sw = sweeps["prior_precision_cap"]
    ax.plot(sw["x"], sw["y"], color=OKABE_ITO["blue"], lw=1.6)
    base = battery["illusion_task"]["baseline"]["illusion_score"]
    ax.axhline(base, color="black", ls="--", lw=0.9)
    ax.text(1.55, base + 0.012, "baseline (uncapped)", fontsize=7)
    ax.plot([0.3], [battery["illusion_task"]["autism_weak_prior"]["illusion_score"]],
            marker="s", color=OKABE_ITO["blue"], ms=6, ls="none", zorder=5)
    ax.annotate("autism_weak_prior\n(cap = 0.3)", xy=(0.3, 0.2285),
                xytext=(0.75, 0.13), fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.set_xlabel("prior precision cap")
    ax.set_ylabel("illusion score")
    ax.set_title("Continuous mechanism, not two hardcoded outputs", fontsize=8)
    fig.tight_layout()
    save(fig, "fig_illusion")


# --------------------------------------------------------------------------
# Figure 3 — volatility / reconvergence
# --------------------------------------------------------------------------
def fig_volatility():
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8),
                             gridspec_kw={"width_ratios": [1.7, 1]})
    ax = axes[0]
    for k, p in enumerate(["baseline", "autism_overfitting", "audhd_emotion_dysregulation"]):
        r = VL.run(profiles.get(p))
        preds = [q["prediction"] for q in r["trajectory"]]
        st = profile_style(p, k)
        ax.plot(preds, color=st["color"], ls=st["linestyle"], lw=1.4,
                label=f"{p.replace('_',' ')} ({r['summary']['trials_to_reconverge']:.2f})")
        flip = r["summary"]["flip_trial"]
    ax.axvline(flip, color="grey", ls=":", lw=1.0)
    ax.text(flip + 1.5, 1.16, "unsignalled\ncontext switch", fontsize=6.5, va="top")
    ax.axhline(0.8, color="grey", lw=0.5)
    ax.axhline(0.2, color="grey", lw=0.5)
    ax.set_ylim(-0.05, 1.55)
    ax.set_yticks([0, 0.2, 0.5, 0.8, 1.0])
    ax.set_xlabel("trial")
    ax.set_ylabel("belief P(reward | arm A)")
    ax.legend(fontsize=6, frameon=False, loc="upper left", ncol=1,
              title="profile (trials to reconverge)", title_fontsize=6)
    ax.set_title("Volatility learning", fontsize=9)

    ax = axes[1]
    sw = sweeps["precision_flexibility"]
    ax.plot(sw["x"], sw["y"], color=OKABE_ITO["sky_blue"], lw=1.6, marker="^", ms=3)
    ax.set_xlabel("precision flexibility")
    ax.set_ylabel("trials to reconverge")
    ax.set_title("Reconvergence vs. flexibility", fontsize=8)
    fig.tight_layout()
    save(fig, "fig_volatility")


# --------------------------------------------------------------------------
# Figure 4 — AuDHD quadrant + interaction
# --------------------------------------------------------------------------
def fig_audhd():
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.1),
                             gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    pts = ["baseline", "autism_overfitting", "adhd_rpe_noise",
           "audhd_emotion_dysregulation", "comorbid"]
    offsets = {"baseline": (10, -4), "autism_overfitting": (-4, 12),
               "adhd_rpe_noise": (-58, 12), "audhd_emotion_dysregulation": (-30, -20),
               "comorbid": (10, 2)}
    for k, p in enumerate(pts):
        s = battery["perturbation_recovery_task"][p]
        st = profile_style(p, k)
        ax.errorbar(s["recovery_jitter_mean"], s["recovery_time_mean"],
                    yerr=s["recovery_time_std"], marker=st["marker"],
                    color=st["color"], ms=9, ls="none", capsize=2, lw=1)
        ax.annotate(p.replace("_", " ").replace("emotion dysregulation", "emot.dysreg."),
                    (s["recovery_jitter_mean"], s["recovery_time_mean"]),
                    textcoords="offset points", xytext=offsets[p], fontsize=6.5)
    # the naive-average prediction the AuDHD hypothesis denies
    a = battery["perturbation_recovery_task"]["autism_overfitting"]
    d = battery["perturbation_recovery_task"]["adhd_rpe_noise"]
    ax.plot([(a["recovery_jitter_mean"] + d["recovery_jitter_mean"]) / 2],
            [(a["recovery_time_mean"] + d["recovery_time_mean"]) / 2],
            marker="x", ms=9, color="grey", ls="none")
    ax.annotate("naive average of the\ntwo single-lever profiles",
                ((a["recovery_jitter_mean"] + d["recovery_jitter_mean"]) / 2,
                 (a["recovery_time_mean"] + d["recovery_time_mean"]) / 2),
                textcoords="offset points", xytext=(8, -6), fontsize=6.5, color="grey")
    ax.set_xlabel("recovery jitter (erratic $\\rightarrow$)")
    ax.set_ylabel("recovery time (slow $\\uparrow$)")
    ax.set_title("AuDHD recovery signature", fontsize=9)
    ax.set_xscale("symlog", linthresh=1e-3)
    ax.set_ylim(0, 36)
    ax.set_xlim(-1e-4, 1.2)

    ax = axes[1]
    met = interaction["metrics"]
    names = ["recovery_time", "recovery_jitter"]
    x = np.arange(2)
    pred = [met[m]["predicted_additive_delta"] for m in names]
    obs = [met[m]["observed_combined_delta"] for m in names]
    # normalise each metric by its predicted-additive value for a shared axis
    predn = [1.0, 1.0]
    obsn = [o / p if p else 0 for o, p in zip(obs, pred, strict=True)]
    ax.bar(x - 0.19, predn, 0.36, label="predicted additive", color="lightgrey",
           edgecolor="black", lw=0.5)
    ax.bar(x + 0.19, obsn, 0.36, label="observed combined", color=OKABE_ITO["reddish_purple"],
           edgecolor="black", lw=0.5, hatch="//")
    for xi, o in zip(x, obsn, strict=True):
        ax.text(xi + 0.19, o + 0.03, f"{o:.2f}×", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(["recovery\ntime", "recovery\njitter"], fontsize=8)
    ax.set_ylabel("deviation / additive prediction", fontsize=8)
    ax.axhline(1.0, color="black", lw=0.6, ls=":")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Additivity test", fontsize=9)
    fig.tight_layout()
    save(fig, "fig_audhd")


# --------------------------------------------------------------------------
# Figure 5 — parameter recovery
# --------------------------------------------------------------------------
def fig_recovery():
    from akribia.seeding import derive_seed
    fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.5))
    rng_specs = list(PREC.RECOVER_GRIDS)
    for ax, name in zip(axes, rng_specs, strict=True):
        grid = PREC.RECOVER_GRIDS[name]
        rng = np.random.default_rng(derive_seed("recovery", name))
        truths = rng.uniform(grid.min(), grid.max(), 20)
        rec = []
        for k, t in enumerate(truths):
            seed = derive_seed("recovery", name, k)
            if name == "discount_factor":
                rec.append(PREC._fit_discounting(PREC._simulate_discounting(t)))
            elif name == "prior_precision_cap":
                rec.append(PREC._fit_kalman_cap(PREC._simulate_kalman_cap(t)))
            else:
                rec.append(PREC._fit_flex(PREC._simulate_flex(t, seed), seed))
        r = recovery["parameters"][name]
        ok = r["recovers_reliably"]
        ax.plot([grid.min(), grid.max()], [grid.min(), grid.max()],
                color="grey", ls=":", lw=0.8)
        ax.plot(truths, rec, "o", ms=4,
                color=OKABE_ITO["bluish_green"] if ok else OKABE_ITO["vermillion"],
                alpha=0.85)
        verdict = "recovers" if ok else "weakly identified"
        ax.set_title(
            f"{name}\n$r$ = {r['correlation_true_recovered']:.2f} ({verdict})",
            fontsize=8)
        ax.set_xlabel("ground truth", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("recovered", fontsize=8)
    fig.tight_layout()
    save(fig, "fig_recovery")


# --------------------------------------------------------------------------
# Figure 6 — discounting + PPCS (the other two conditions)
# --------------------------------------------------------------------------
def fig_adhd_ppcs():
    fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.4))

    ax = axes[0]
    delays = np.linspace(1, 90, 90)
    for k, p in enumerate(["baseline", "adhd_discounting"]):
        g = profiles.get(p).discount_factor
        vals = [core.discounted_value(1.0, float(d), g) for d in delays]
        st = profile_style(p, k)
        auc = battery["delay_discounting_task"][p]["auc_impulsivity"]
        ax.plot(delays, vals, color=st["color"], ls=st["linestyle"], lw=1.5,
                label=f"$\\gamma$={g} (AUC {auc:.3f})")
    ax.set_yscale("log")
    ax.set_xlabel("delay (days)")
    ax.set_ylabel("subjective value fraction")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Delay discounting", fontsize=9)

    ax = axes[1]
    for k, p in enumerate(["baseline", "ppcs_forward_model"]):
        r = SM.run(profiles.get(p))
        mm = [abs(q["prediction_error"]) for q in r["trajectory"]]
        st = profile_style(p, k)
        ax.plot(mm[:40], color=st["color"], ls=st["linestyle"], lw=1.4,
                label=f"{p.replace('_',' ')}")
    ax.set_yscale("symlog", linthresh=1e-2)
    ax.set_xlabel("step after head movement")
    ax.set_ylabel("|sensory mismatch|")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Self-motion (PPCS)", fontsize=9)

    ax = axes[2]
    sw = sweeps["discount_factor"]
    ax.plot(sw["x"], sw["y"], color=OKABE_ITO["vermillion"], lw=1.6)
    ax.set_xlabel("discount factor $\\gamma$")
    ax.set_ylabel("AUC impulsivity")
    ax.set_title("Steep, monotone sweep", fontsize=9)
    fig.tight_layout()
    save(fig, "fig_adhd_ppcs")


# --------------------------------------------------------------------------
# LaTeX tables
# --------------------------------------------------------------------------
def esc(s):
    return s.replace("_", "\\_")


def table_battery():
    tasks = list(TASK_METRIC)
    hdr = {"illusion_task": "Illusion score",
           "volatility_learning_task": "Reconv. trials",
           "delay_discounting_task": "Disc. AUC",
           "self_motion_task": "Vestib. steps",
           "perturbation_recovery_task": "Perturb. time"}
    lines = [r"\begin{tabular}{l" + "r" * len(tasks) + "}", r"\toprule",
             "Profile & " + " & ".join(hdr[t] for t in tasks) + r" \\",
             r"\midrule"]
    for p in ORDER:
        cells = []
        for t in tasks:
            k = TASK_METRIC[t][0]
            v = battery[t][p][k]
            b = battery[t]["baseline"][k]
            s = f"{v:.3f}" if abs(v) < 100 else f"{v:.1f}"
            if v != b:  # exact inequality, matching the figure
                s = r"\textbf{" + s + "}"
            cells.append(s)
        lines.append(esc(p) + " & " + " & ".join(cells) + r" \\")
        if p == "baseline":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "battery.tex").write_text("\n".join(lines) + "\n")


def table_recovery():
    lines = [r"\begin{tabular}{lrrrc}", r"\toprule",
             r"Parameter & $n$ seeds & $r$(true, recovered) & mean rel.\ error & Gate \\",
             r"\midrule"]
    for name, r in recovery["parameters"].items():
        lines.append(
            f"{esc(name)} & {r['n_seeds']} & {r['correlation_true_recovered']:.3f} & "
            f"{r['mean_relative_error']:.3f} & "
            + (r"\checkmark" if r["recovers_reliably"] else r"$\times$") + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "recovery.tex").write_text("\n".join(lines) + "\n")


def table_interaction():
    lines = [r"\begin{tabular}{lrrrl}", r"\toprule",
             r"Metric & Predicted additive $\Delta$ & Observed $\Delta$ & Ratio & Verdict \\",
             r"\midrule"]
    for m, d in interaction["metrics"].items():
        ratio = d["observed_combined_delta"] / d["predicted_additive_delta"]
        lines.append(
            f"{esc(m)} & {d['predicted_additive_delta']:.4f} & "
            f"{d['observed_combined_delta']:.4f} & {ratio:.2f} & {d['verdict']} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "interaction.tex").write_text("\n".join(lines) + "\n")


def table_predictions():
    """Build the pre-registration table.

    IMPORTANT: the Outcome column is COMPUTED from the live battery, using the
    same comparison the corresponding assertion in tests/test_predictions.py
    makes. It is not hardcoded; if a prediction failed, this table would print
    "FAILED" and the paper would have to report it.
    """
    b = battery
    IL, VL, DD, SM, PR_ = ("illusion_task", "volatility_learning_task",
                           "delay_discounting_task", "self_motion_task",
                           "perturbation_recovery_task")

    def m(task, prof, key):
        return b[task][prof][key]

    audhd = b[PR_]["audhd_emotion_dysregulation"]
    base_p = b[PR_]["baseline"]
    autism_p = b[PR_]["autism_overfitting"]
    adhd_p = b[PR_]["adhd_rpe_noise"]

    rows = [
        ("P1", "Weak priors reduce illusion susceptibility",
         f"{m(IL, 'autism_weak_prior', 'illusion_score'):.3f} $<$ "
         f"{m(IL, 'baseline', 'illusion_score'):.3f}",
         m(IL, "autism_weak_prior", "illusion_score") < m(IL, "baseline", "illusion_score")),

        ("P2", "Inflexible precision does \\emph{not} reduce the static illusion score",
         f"{m(IL, 'autism_overfitting', 'illusion_score'):.3f} $\\geq$ "
         f"{m(IL, 'baseline', 'illusion_score'):.3f}",
         m(IL, "autism_overfitting", "illusion_score") >= m(IL, "baseline", "illusion_score") - 1e-9),

        ("P3", "Inflexible precision delays post-switch reconvergence",
         f"{m(VL, 'autism_overfitting', 'trials_to_reconverge'):.2f} $>$ "
         f"{m(VL, 'baseline', 'trials_to_reconverge'):.2f} trials",
         m(VL, "autism_overfitting", "trials_to_reconverge") > m(VL, "baseline", "trials_to_reconverge")),

        ("P4", "Steep discounting lowers the delay-discounting AUC",
         f"{m(DD, 'adhd_discounting', 'auc_impulsivity'):.4f} $<$ "
         f"{m(DD, 'baseline', 'auc_impulsivity'):.4f}",
         m(DD, "adhd_discounting", "auc_impulsivity") < m(DD, "baseline", "auc_impulsivity")),

        ("P5", "Impaired forward model resolves the mismatch more slowly",
         f"{m(SM, 'ppcs_forward_model', 'recovery_steps_mean'):.2f} $>$ "
         f"{m(SM, 'baseline', 'recovery_steps_mean'):.2f} steps",
         m(SM, "ppcs_forward_model", "recovery_steps_mean") > m(SM, "baseline", "recovery_steps_mean")),

        ("P6", "AuDHD is both slower and more erratic than baseline",
         f"$t$ {audhd['recovery_time_mean']:.1f} $>$ "
         f"{base_p['recovery_time_mean']:.1f}; "
         f"$j$ {audhd['recovery_jitter_mean']:.3f} $>$ "
         f"{base_p['recovery_jitter_mean']:.3f}",
         (audhd["recovery_time_mean"] > base_p["recovery_time_mean"]
          and audhd["recovery_jitter_mean"] > base_p["recovery_jitter_mean"]
          and autism_p["recovery_time_mean"] > base_p["recovery_time_mean"]
          and autism_p["recovery_jitter_mean"] < adhd_p["recovery_jitter_mean"]
          and adhd_p["recovery_jitter_mean"] > base_p["recovery_jitter_mean"])),
    ]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"ID & Pre-registered prediction & Observed & Outcome \\", r"\midrule"]
    for i, d, o, ok in rows:
        lines.append(f"{i} & {d} & {o} & "
                     + (r"held" if ok else r"\textbf{FAILED}") + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "predictions.tex").write_text("\n".join(lines) + "\n")
    print("predictions computed from data:",
          {i: ("held" if ok else "FAILED") for i, _, _, ok in rows})


if __name__ == "__main__":
    fig_dissociation()
    fig_illusion()
    fig_volatility()
    fig_audhd()
    fig_recovery()
    fig_adhd_ppcs()
    table_battery()
    table_recovery()
    table_interaction()
    table_predictions()
    print("done; backend =", core.BACKEND)
