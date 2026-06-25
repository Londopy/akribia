"""Multi-task battery + per-task interaction analysis (spec 2.5 / 2.4).

Runs every condition task under each profile and assembles one combined result.
Also implements the §2.4 *per-task* factorial-ablation interaction methodology —
scoped to the levers that actually affect a given task, in that task's own scalar
metric, NEVER summed across incompatible units (trials-to-reconverge vs.
indifference-dollars vs. recovery-steps are not comparable, so there is no single
global additivity number, and claiming one would be exactly the overreach
spec 1.5.2 warns against).

The perturbation-recovery task is the one where two levers (``precision_flexibility``
and ``rpe_noise_std``) genuinely co-act in shared metrics, so that is where the
analysis has teeth. We report it two ways (spec 2.4): the generic ``comorbid``
grid as an *engineering ablation*, and ``audhd_emotion_dysregulation`` as a
*literature replication* asking whether the engine reproduces the §1.5.1
qualitative signature.
"""

from __future__ import annotations

from dataclasses import replace

from .. import profiles
from ..profiles import PrecisionProfile
from ..schema import make_result
from . import (
    delay_discounting_task,
    illusion_task,
    perturbation_recovery_task,
    self_motion_task,
    volatility_learning_task,
)

TASK = "multi_task_battery"

_TASK_MODULES = {
    "illusion_task": illusion_task,
    "volatility_learning_task": volatility_learning_task,
    "delay_discounting_task": delay_discounting_task,
    "self_motion_task": self_motion_task,
    "perturbation_recovery_task": perturbation_recovery_task,
}


def run_all(profile_names: list[str] | None = None) -> dict:
    """Run every task under every requested profile. Returns
    ``{task: {profile: summary}}``."""
    profile_names = profile_names or profiles.names()
    out: dict[str, dict[str, dict]] = {}
    for task_name, mod in _TASK_MODULES.items():
        out[task_name] = {}
        for pname in profile_names:
            res = mod.run(profiles.get(pname))
            out[task_name][pname] = res["summary"]
    return out


def interaction_analysis() -> dict:
    """Per-task predicted-additive vs. observed interaction for the perturbation
    task, where ``precision_flexibility`` and ``rpe_noise_std`` genuinely co-act.

    For each task metric: predicted-additive deviation = sum of single-lever
    deviations-from-baseline; observed = the combined deviation. Interpretation
    (spec 2.4): observed ≈ predicted → independent; observed < predicted →
    masking/dominance; observed > predicted → genuine super-additive interaction.
    """
    base = profiles.BASELINE
    # The audhd levers, isolated and combined (the two that co-act).
    flex_only = replace(base, name="_flex_only", precision_flexibility=0.15)
    noise_only = replace(base, name="_noise_only", rpe_noise_std=0.5)
    both = replace(base, name="_both", precision_flexibility=0.15, rpe_noise_std=0.5)

    def metrics(p: PrecisionProfile) -> dict:
        s = perturbation_recovery_task.run(p)["summary"]
        return {"recovery_time": s["recovery_time_mean"],
                "recovery_jitter": s["recovery_jitter_mean"]}

    m_base = metrics(base)
    m_flex = metrics(flex_only)
    m_noise = metrics(noise_only)
    m_both = metrics(both)

    report = {"task": "perturbation_recovery_task",
              "live_levers": ["precision_flexibility", "rpe_noise_std"],
              "metrics": {}}
    for metric in ("recovery_time", "recovery_jitter"):
        d_flex = m_flex[metric] - m_base[metric]
        d_noise = m_noise[metric] - m_base[metric]
        predicted_additive = d_flex + d_noise
        observed = m_both[metric] - m_base[metric]
        if abs(observed - predicted_additive) <= 0.15 * (abs(predicted_additive) + 1e-9):
            verdict = "independent (additive)"
        elif observed > predicted_additive:
            verdict = "super-additive (genuine interaction)"
        else:
            verdict = "sub-additive (masking/dominance)"
        report["metrics"][metric] = {
            "baseline": m_base[metric],
            "flex_only_delta": d_flex,
            "noise_only_delta": d_noise,
            "predicted_additive_delta": predicted_additive,
            "observed_combined_delta": observed,
            "verdict": verdict,
        }
    return report


def run(profile: PrecisionProfile, *, seed: int | None = None) -> dict:
    """Schema-conformant wrapper: runs the full battery under ``profile`` and the
    interaction analysis, packaged as one AkribiaTaskResult."""
    battery = {t: mod.run(profile)["summary"] for t, mod in _TASK_MODULES.items()}
    summary = {"battery": battery, "interaction_analysis": interaction_analysis()}
    return make_result(profile=profile, task=TASK, parameters={}, summary=summary,
                       trajectory=[], seed=seed)


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(prog="akribia.tasks.multi_task_battery")
    parser.add_argument("--profile", default="comorbid", choices=profiles.names())
    parser.add_argument("--interaction", action="store_true",
                        help="print only the per-task interaction analysis")
    args = parser.parse_args()
    if args.interaction:
        print(json.dumps(interaction_analysis(), indent=2))
    else:
        print(json.dumps(run(profiles.get(args.profile))["summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
