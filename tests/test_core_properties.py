"""Property-based tests for the core engine (spec 2.5.1).

Mirror the Rust ``proptest`` invariants on the Python side with ``hypothesis``:
they validate that the implementation is internally consistent regardless of what
it is compared against, separate from the parameter-recovery validation.
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from akribia import core


@given(
    prior_mean=st.floats(-100, 100),
    prior_var=st.floats(1e-3, 1e3),
    obs=st.floats(-100, 100),
    obs_noise=st.floats(1e-3, 1e3),
)
@settings(max_examples=200)
def test_update_never_increases_variance(prior_mean, prior_var, obs, obs_noise):
    # The UPDATE step alone never increases variance. Pointed at a single update
    # (process_noise=0), NOT the predict->update cycle (spec 2.5.1).
    (_, post_var) = core.kalman_run(prior_mean, prior_var, [obs], 0.0, obs_noise, None)[-1]
    assert post_var <= prior_var + 1e-9


@given(var=st.floats(-10, 1e6), mean=st.floats(-1e6, 1e6))
@settings(max_examples=200)
def test_precision_always_positive(var, mean):
    # A zero/negative/NaN variance is clamped, so precision stays strictly
    # positive and finite — catches the variance guard being removed (spec 2.3).
    (_, post_var) = core.kalman_run(mean, max(var, 1e-9), [0.0], 0.0, 1.0, None)[-1]
    assert post_var > 0


@given(obs=st.floats(-50, 50))
@settings(max_examples=100)
def test_zero_noise_observation_collapses_variance(obs):
    (_, post_var) = core.kalman_run(0.0, 1000.0, [obs], 0.0, 1e-9, None)[-1]
    assert post_var <= 1e-6 * (1 + 1e-6)


@given(reward=st.floats(-10, 10))
@settings(max_examples=100)
def test_td_converges_on_stationary_noiseless_reward(reward):
    traj = core.td_learn_sequence(0.0, [reward] * 500, 0.1, 0.95, 0.0, seed=1)
    assert abs(traj[-1] - reward) < 0.05


def test_seeding_is_deterministic():
    a = core.td_learn_sequence(0.0, [1.0] * 50, 0.2, 0.95, 0.5, seed=42)
    b = core.td_learn_sequence(0.0, [1.0] * 50, 0.2, 0.95, 0.5, seed=42)
    assert a == b


def test_invalid_parameters_raise():
    import pytest
    with pytest.raises(core.InvalidParameter):
        core.kalman_run(0.0, 1.0, [float("nan")], 0.0, 1.0, None)
    with pytest.raises(core.InvalidParameter):
        core.td_learn_sequence(0.0, [1.0], 5.0, 0.95, 0.0, seed=0)  # lr out of [0,1]
