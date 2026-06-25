"""The pre-registered, literature-grounded predictions as hard assertions
(spec 1.5.2 pre-registration discipline).

These encode the predictions committed *before* running the experiments. If one
fails, it is a reportable negative result about the implementation — NOT a cue to
retune parameters until it passes. They are the project's falsifiability test on
its own terms.
"""
from akribia import profiles
from akribia.tasks import (
    delay_discounting_task,
    illusion_task,
    perturbation_recovery_task,
    self_motion_task,
    volatility_learning_task,
)


def _run(mod, name):
    return mod.run(profiles.get(name))["summary"]


def test_illusion_weak_prior_below_baseline():
    # spec 1.2 / 2.5: weak priors -> reduced illusion susceptibility.
    base = _run(illusion_task, "baseline")["illusion_score"]
    weak = _run(illusion_task, "autism_weak_prior")["illusion_score"]
    assert weak < base


def test_illusion_overfitting_not_below_baseline_on_static_trial():
    # spec 2.5: overfitting is high-but-context-rigid; its failure is to UPDATE
    # across trials (the volatility task), not a reduced static score.
    base = _run(illusion_task, "baseline")["illusion_score"]
    over = _run(illusion_task, "autism_overfitting")["illusion_score"]
    assert over >= base - 1e-9


def test_volatility_overfitting_reconverges_more_slowly():
    # spec 1.2: a transient reconvergence delay, not a permanent deficit.
    base = _run(volatility_learning_task, "baseline")["trials_to_reconverge"]
    over = _run(volatility_learning_task, "autism_overfitting")["trials_to_reconverge"]
    assert over > base


def test_discounting_adhd_more_impulsive():
    # spec 1.3: steeper discounting -> lower AUC (more impulsive).
    base = _run(delay_discounting_task, "baseline")["auc_impulsivity"]
    adhd = _run(delay_discounting_task, "adhd_discounting")["auc_impulsivity"]
    assert adhd < base


def test_ppcs_recovers_more_slowly_than_baseline():
    # spec 1.4: impaired forward model -> persistent, slow-resolving mismatch.
    base = _run(self_motion_task, "baseline")["recovery_steps_mean"]
    ppcs = _run(self_motion_task, "ppcs_forward_model")["recovery_steps_mean"]
    assert ppcs > base


def test_perturbation_audhd_is_slow_and_erratic():
    # spec 1.5.1: autism-side slow+smooth, ADHD-side fast+erratic, AuDHD distinct
    # (slow AND erratic) — not the average of the two.
    base = _run(perturbation_recovery_task, "baseline")
    autism = _run(perturbation_recovery_task, "autism_overfitting")
    adhd = _run(perturbation_recovery_task, "adhd_rpe_noise")
    audhd = _run(perturbation_recovery_task, "audhd_emotion_dysregulation")

    # autism-side: slow (high recovery time), smooth (low jitter)
    assert autism["recovery_time_mean"] > base["recovery_time_mean"]
    assert autism["recovery_jitter_mean"] < adhd["recovery_jitter_mean"]
    # ADHD-side: fast (low recovery time), erratic (high jitter)
    assert adhd["recovery_jitter_mean"] > base["recovery_jitter_mean"]
    # AuDHD: slow like autism AND erratic (distinct quadrant)
    assert audhd["recovery_time_mean"] > base["recovery_time_mean"]
    assert audhd["recovery_jitter_mean"] > base["recovery_jitter_mean"]
