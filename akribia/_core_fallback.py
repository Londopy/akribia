"""Pure-Python reference implementation of the akribia core engine.

This mirrors the Rust crate ``core/`` exactly for the deterministic math, and uses
an explicitly-seeded NumPy generator for the stochastic parts (spec 2.6.1). It
exists so the project is runnable and verifiable without a Rust toolchain; the
compiled :mod:`akribia._core` is preferred when available and
``validation/against_hgf_toolbox.py`` checks the two agree to a stated tolerance.

The deterministic functions (Kalman, HGF, discounting) are bit-identical in intent
to the Rust versions. The noise-driven functions (TD with ``rpe_noise_std``, the
forward model with ``injury_noise_std``) reproduce the same *distribution* as the
Rust core but not the same exact draws, because NumPy's PRNG and Rust's ChaCha8
are different streams — a limit explicitly acknowledged in spec 2.6.1.
"""

from __future__ import annotations

import numpy as np

# The minimum positive variance permitted anywhere (matches core/src/error.rs).
VAR_EPSILON = 1e-6

BACKEND = "python"


class AkribiaException(Exception):
    """Base class mirroring the Rust AkribiaError hierarchy (spec 2.13)."""


class InvalidParameter(AkribiaException):
    pass


class NumericalDivergence(AkribiaException):
    pass


def clamp_variance(var: float) -> float:
    """Floor a variance at VAR_EPSILON before it is inverted (spec 2.3)."""
    if np.isnan(var):
        return VAR_EPSILON
    return max(var, VAR_EPSILON)


# --------------------------------------------------------------------------- #
# Kalman filter (baseline precision-weighted Bayesian update)                 #
# --------------------------------------------------------------------------- #
def kalman_run(
    initial_mean: float,
    initial_var: float,
    observations,
    process_noise: float,
    obs_noise: float,
    prior_precision_cap: float | None = None,
) -> list[tuple[float, float]]:
    """Run the 1-D Kalman filter; returns ``[(mean, var), ...]`` per step."""
    if process_noise < 0 or not np.isfinite(process_noise):
        raise InvalidParameter("process_noise must be finite and non-negative")
    if obs_noise < 0 or not np.isfinite(obs_noise):
        raise InvalidParameter("obs_noise must be finite and non-negative")
    mean, var = initial_mean, clamp_variance(initial_var)
    prec_like = 1.0 / clamp_variance(obs_noise)
    out: list[tuple[float, float]] = []
    for z in observations:
        if not np.isfinite(z):
            raise InvalidParameter("observation must be finite")
        # predict
        var = clamp_variance(var + process_noise)
        prec_prior = 1.0 / var
        if prior_precision_cap is not None:
            if prior_precision_cap <= 0 or not np.isfinite(prior_precision_cap):
                raise InvalidParameter("prior_precision_cap must be finite and positive")
            prec_prior = min(prec_prior, prior_precision_cap)
        # update
        post_prec = prec_prior + prec_like
        mean = (prec_prior * mean + prec_like * z) / post_prec
        var = 1.0 / post_prec
        out.append((mean, var))
    return out


# --------------------------------------------------------------------------- #
# Volatility-coupled HGF                                                       #
# --------------------------------------------------------------------------- #
def hgf_run(
    observations,
    obs_noise: float,
    precision_flexibility: float,
    base_process_noise: float = 0.01,
    mu1: float = 0.0,
    var1: float = 1.0,
    mu2: float = 0.0,
    var2: float = 1.0,
):
    """Run the volatility-coupled HGF.

    Returns one tuple per step:
    ``(t, prediction, observation, precision, prediction_error, learning_rate, volatility)``.
    """
    if precision_flexibility < 0 or not np.isfinite(precision_flexibility):
        raise InvalidParameter("precision_flexibility must be finite and non-negative")
    prec_like = 1.0 / clamp_variance(obs_noise)
    out = []
    for t, z in enumerate(observations):
        if not np.isfinite(z):
            raise InvalidParameter("observation must be finite")
        # Surprise-gated process noise: flexible models raise the learning rate
        # when recent surprise (mu2) is high; inflexible ones cannot (spec 1.2).
        q = base_process_noise + precision_flexibility * max(mu2, 0.0)
        pred_var1 = clamp_variance(var1 + q)
        prec_prior = 1.0 / pred_var1
        post_prec = prec_prior + prec_like
        pe = z - mu1
        lr = prec_like / post_prec
        pred = mu1  # prediction BEFORE the update
        mu1 = mu1 + lr * pe
        var1 = 1.0 / post_prec
        # level-2 volatility = EMA of precision-normalised squared PE.
        surprise = (pe * pe) * prec_like
        vol_decay = 0.5
        mu2 = max((1.0 - vol_decay) * mu2 + vol_decay * surprise, 0.0)
        var2 = clamp_variance(var2)
        out.append((float(t), pred, z, post_prec, pe, lr, q))
    return out


# --------------------------------------------------------------------------- #
# TD / Rescorla-Wagner reward learning                                         #
# --------------------------------------------------------------------------- #
def td_learn_sequence(
    initial_value: float,
    rewards,
    learning_rate: float,
    discount_factor: float,
    rpe_noise_std: float,
    seed: int,
) -> list[float]:
    """Learn a value estimate across a reward sequence; returns the trajectory."""
    if not (0.0 <= learning_rate <= 1.0):
        raise InvalidParameter("learning_rate must be in [0, 1]")
    if rpe_noise_std < 0 or not np.isfinite(rpe_noise_std):
        raise InvalidParameter("rpe_noise_std must be finite and non-negative")
    rng = np.random.default_rng(seed)
    v = initial_value
    out: list[float] = []
    for r in rewards:
        rpe = r - v
        if rpe_noise_std > 0:
            rpe += rng.normal(0.0, rpe_noise_std)
        v = v + learning_rate * rpe
        out.append(v)
    return out


def discounted_value(reward: float, delay: float, discount_factor: float) -> float:
    """Subjective discounted value of ``reward`` after ``delay`` steps."""
    return (discount_factor**delay) * reward


# --------------------------------------------------------------------------- #
# Forward model (PPCS)                                                         #
# --------------------------------------------------------------------------- #
def forward_simulate(
    motor_command,
    update_rate: float,
    injury_noise_std: float,
    sensory_gain: float,
    seed: int,
) -> list[tuple[float, float, float, float]]:
    """Simulate the self-motion forward model.

    Returns ``(t, predicted, actual, mismatch)`` per step.
    """
    if not (0.0 <= update_rate <= 1.0):
        raise InvalidParameter("update_rate must be in [0, 1]")
    if injury_noise_std < 0 or not np.isfinite(injury_noise_std):
        raise InvalidParameter("injury_noise_std must be finite and non-negative")
    rng = np.random.default_rng(seed)
    model_estimate = 0.0
    out = []
    for i, cmd in enumerate(motor_command):
        predicted = model_estimate
        actual = sensory_gain * cmd
        if injury_noise_std > 0:
            actual += rng.normal(0.0, injury_noise_std)
        mismatch = actual - predicted
        model_estimate += update_rate * mismatch
        if not np.isfinite(model_estimate):
            raise NumericalDivergence("forward_model estimate diverged")
        out.append((float(i), predicted, actual, mismatch))
    return out
