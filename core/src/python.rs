//! PyO3 bindings — exposes the core engine to the Python layer as `akribia._core`
//! (spec 2.2, 2.13).
//!
//! `AkribiaError` variants are mapped onto a small Python exception hierarchy so
//! callers can `except akribia._core.InvalidParameter` rather than parsing error
//! strings. All RNG-driven functions take an explicit `seed` (spec 2.6.1).

use crate::error::AkribiaError;
use crate::{forward_model, hgf, kalman, td_learning};
use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

create_exception!(
    _core,
    AkribiaException,
    PyException,
    "Base class for all akribia core errors."
);
create_exception!(
    _core,
    InvalidParameter,
    AkribiaException,
    "A parameter was out of its valid range."
);
create_exception!(
    _core,
    SingularMatrix,
    AkribiaException,
    "A matrix could not be inverted."
);
create_exception!(
    _core,
    NumericalDivergence,
    AkribiaException,
    "The filter produced a non-finite value."
);
create_exception!(
    _core,
    DimensionMismatch,
    AkribiaException,
    "Sequence lengths did not match."
);

fn to_py(err: AkribiaError) -> PyErr {
    match err {
        AkribiaError::InvalidParameter { .. } => InvalidParameter::new_err(err.to_string()),
        AkribiaError::SingularMatrix { .. } => SingularMatrix::new_err(err.to_string()),
        AkribiaError::NumericalDivergence { .. } => NumericalDivergence::new_err(err.to_string()),
        AkribiaError::DimensionMismatch { .. } => DimensionMismatch::new_err(err.to_string()),
    }
}

/// Run the 1-D Kalman filter; returns `[(mean, var), ...]` per step.
#[pyfunction]
#[pyo3(signature = (initial_mean, initial_var, observations, process_noise, obs_noise, prior_precision_cap=None))]
fn kalman_run(
    initial_mean: f64,
    initial_var: f64,
    observations: Vec<f64>,
    process_noise: f64,
    obs_noise: f64,
    prior_precision_cap: Option<f64>,
) -> PyResult<Vec<(f64, f64)>> {
    let cfg = kalman::KalmanConfig {
        process_noise,
        obs_noise,
        prior_precision_cap,
    };
    let traj = kalman::run(
        kalman::Gaussian::new(initial_mean, initial_var),
        &observations,
        &cfg,
    )
    .map_err(to_py)?;
    Ok(traj.into_iter().map(|g| (g.mean, g.var)).collect())
}

/// Run the volatility-coupled HGF; returns one tuple per step:
/// `(t, prediction, observation, precision, prediction_error, learning_rate, volatility)`.
#[pyfunction]
#[pyo3(signature = (observations, obs_noise, precision_flexibility, base_process_noise=0.01, mu1=0.0, var1=1.0, mu2=0.0, var2=1.0))]
#[allow(clippy::too_many_arguments)]
fn hgf_run(
    observations: Vec<f64>,
    obs_noise: f64,
    precision_flexibility: f64,
    base_process_noise: f64,
    mu1: f64,
    var1: f64,
    mu2: f64,
    var2: f64,
) -> PyResult<Vec<(f64, f64, f64, f64, f64, f64, f64)>> {
    let cfg = hgf::HgfConfig {
        obs_noise,
        precision_flexibility,
        base_process_noise,
    };
    let traj = hgf::run(
        hgf::HgfState::new(mu1, var1, mu2, var2),
        &observations,
        &cfg,
    )
    .map_err(to_py)?;
    Ok(traj
        .into_iter()
        .map(|s| {
            (
                s.t,
                s.prediction,
                s.observation,
                s.precision,
                s.prediction_error,
                s.learning_rate,
                s.volatility,
            )
        })
        .collect())
}

/// Learn a value estimate across a reward sequence; returns the value trajectory.
#[pyfunction]
#[pyo3(signature = (initial_value, rewards, learning_rate, discount_factor, rpe_noise_std, seed))]
fn td_learn_sequence(
    initial_value: f64,
    rewards: Vec<f64>,
    learning_rate: f64,
    discount_factor: f64,
    rpe_noise_std: f64,
    seed: u64,
) -> PyResult<Vec<f64>> {
    let cfg = td_learning::TdConfig {
        learning_rate,
        discount_factor,
        rpe_noise_std,
    };
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    td_learning::learn_sequence(initial_value, &rewards, &cfg, &mut rng).map_err(to_py)
}

/// Subjective discounted value of `reward` after `delay` steps.
#[pyfunction]
fn discounted_value(reward: f64, delay: f64, discount_factor: f64) -> f64 {
    let cfg = td_learning::TdConfig {
        discount_factor,
        ..Default::default()
    };
    td_learning::discounted_value(reward, delay, &cfg)
}

/// Simulate the self-motion forward model; returns `(t, predicted, actual, mismatch)` per step.
#[pyfunction]
#[pyo3(signature = (motor_command, update_rate, injury_noise_std, sensory_gain, seed))]
fn forward_simulate(
    motor_command: Vec<f64>,
    update_rate: f64,
    injury_noise_std: f64,
    sensory_gain: f64,
    seed: u64,
) -> PyResult<Vec<(f64, f64, f64, f64)>> {
    let cfg = forward_model::ForwardModelConfig {
        update_rate,
        injury_noise_std,
        sensory_gain,
    };
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let traj = forward_model::simulate(&motor_command, &cfg, &mut rng).map_err(to_py)?;
    Ok(traj
        .into_iter()
        .map(|s| (s.t, s.predicted, s.actual, s.mismatch))
        .collect())
}

/// The compiled core module: `akribia._core`.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add(
        "__doc__",
        "Rust core engine for akribia (precision-weighted Bayesian inference).",
    )?;
    m.add(
        "AkribiaException",
        m.py().get_type_bound::<AkribiaException>(),
    )?;
    m.add(
        "InvalidParameter",
        m.py().get_type_bound::<InvalidParameter>(),
    )?;
    m.add("SingularMatrix", m.py().get_type_bound::<SingularMatrix>())?;
    m.add(
        "NumericalDivergence",
        m.py().get_type_bound::<NumericalDivergence>(),
    )?;
    m.add(
        "DimensionMismatch",
        m.py().get_type_bound::<DimensionMismatch>(),
    )?;
    m.add_function(wrap_pyfunction!(kalman_run, m)?)?;
    m.add_function(wrap_pyfunction!(hgf_run, m)?)?;
    m.add_function(wrap_pyfunction!(td_learn_sequence, m)?)?;
    m.add_function(wrap_pyfunction!(discounted_value, m)?)?;
    m.add_function(wrap_pyfunction!(forward_simulate, m)?)?;
    Ok(())
}
