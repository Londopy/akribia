//! State-space self-motion forward model (the PPCS module, spec 2.3).
//!
//! This is the one genuinely different piece of math in the engine: it is not a
//! perceptual prior or a reward valuation, but a *forward model* of the sensory
//! consequence of self-generated motion, compared against the actual afferent
//! (vestibular/visual) signal.
//!
//! ```text
//! predicted_sensory_state = forward_model(motor_command, prior_state)
//! actual_sensory_state    = vestibular_input(motor_command) + injury_noise
//! mismatch                = actual_sensory_state - predicted_sensory_state
//! forward_model_update    = update_rate * mismatch   (update_rate is the PPCS lever)
//! ```
//!
//! Healthy: the mismatch resolves as the model updates. PPCS profile: the
//! forward-model `update_rate` is impaired, so the mismatch persists, decaying
//! slowly or not at all — simulated unresolved sensorimotor prediction error
//! ("dizziness" that does not habituate). Implemented as an explicit state-space
//! / control loop, not a static Bayesian update.

use crate::error::AkribiaError;
use rand::Rng;
use rand_distr::{Distribution, Normal};

/// Configuration of the forward-model comparison loop.
#[derive(Debug, Clone, Copy)]
pub struct ForwardModelConfig {
    /// Rate at which the forward model corrects toward the observed mismatch.
    /// 1.0 = healthy (fast resolution); lower = impaired (PPCS lever).
    pub update_rate: f64,
    /// Std-dev of additive sensor/injury noise on the afferent signal (PPCS lever).
    pub injury_noise_std: f64,
    /// Gain mapping a motor command (angular velocity) to its expected sensory
    /// consequence. 1.0 for a well-calibrated head-motion model.
    pub sensory_gain: f64,
}

impl Default for ForwardModelConfig {
    fn default() -> Self {
        ForwardModelConfig {
            update_rate: 1.0,
            injury_noise_std: 0.0,
            sensory_gain: 1.0,
        }
    }
}

/// One step of the forward-model comparison.
#[derive(Debug, Clone, Copy)]
pub struct MismatchStep {
    pub t: f64,
    /// Predicted sensory consequence of the motor command.
    pub predicted: f64,
    /// Actual (noisy) afferent sensory signal.
    pub actual: f64,
    /// actual − predicted; the unresolved prediction error.
    pub mismatch: f64,
}

/// Simulate a head-motion command profile and return the mismatch trajectory.
///
/// `motor_command[t]` is the commanded angular velocity at step `t`. The model's
/// internal estimate of the sensory consequence carries forward and is corrected
/// by `update_rate * mismatch` each step; the true afferent signal is the
/// command scaled by `sensory_gain` plus Gaussian injury noise.
pub fn simulate<R: Rng>(
    motor_command: &[f64],
    cfg: &ForwardModelConfig,
    rng: &mut R,
) -> Result<Vec<MismatchStep>, AkribiaError> {
    if !(0.0..=1.0).contains(&cfg.update_rate) {
        return Err(AkribiaError::invalid(
            "update_rate",
            cfg.update_rate,
            "must be in [0, 1]",
        ));
    }
    if cfg.injury_noise_std < 0.0 || !cfg.injury_noise_std.is_finite() {
        return Err(AkribiaError::invalid(
            "injury_noise_std",
            cfg.injury_noise_std,
            "must be finite and non-negative",
        ));
    }

    let noise = if cfg.injury_noise_std > 0.0 {
        Some(Normal::new(0.0, cfg.injury_noise_std).map_err(|_| {
            AkribiaError::invalid("injury_noise_std", cfg.injury_noise_std, "invalid normal")
        })?)
    } else {
        None
    };

    // The forward model's running estimate of the expected sensory state.
    let mut model_estimate = 0.0;
    let mut out = Vec::with_capacity(motor_command.len());

    for (i, &cmd) in motor_command.iter().enumerate() {
        // Predicted sensory consequence from the (possibly miscalibrated) model.
        let predicted = model_estimate;
        // True afferent signal: command -> sensory via gain, plus injury noise.
        let mut actual = cfg.sensory_gain * cmd;
        if let Some(n) = noise {
            actual += n.sample(rng);
        }
        let mismatch = actual - predicted;
        // The forward model corrects toward the observed consequence at the
        // (impaired) update rate. With update_rate < 1 the estimate lags and the
        // mismatch persists rather than resolving.
        model_estimate += cfg.update_rate * mismatch;

        if !model_estimate.is_finite() {
            return Err(AkribiaError::divergence("forward_model::simulate estimate"));
        }
        out.push(MismatchStep {
            t: i as f64,
            predicted,
            actual,
            mismatch,
        });
    }
    Ok(out)
}

/// Number of steps for the absolute mismatch to first decay below `threshold`
/// after the motion onset, or `None` if it never does (persistent PPCS error).
pub fn recovery_time(traj: &[MismatchStep], threshold: f64) -> Option<usize> {
    traj.iter().position(|s| s.mismatch.abs() < threshold)
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;

    fn step_command(n: usize, level: f64) -> Vec<f64> {
        vec![level; n]
    }

    #[test]
    fn healthy_model_resolves_mismatch_quickly() {
        let cfg = ForwardModelConfig {
            update_rate: 1.0,
            injury_noise_std: 0.0,
            sensory_gain: 1.0,
        };
        let mut rng = ChaCha8Rng::seed_from_u64(0);
        let traj = simulate(&step_command(50, 30.0), &cfg, &mut rng).unwrap();
        // With update_rate 1.0 the mismatch is resolved by the second step.
        assert!(traj[1].mismatch.abs() < 1e-9);
    }

    #[test]
    fn ppcs_model_leaves_persistent_mismatch() {
        let healthy = ForwardModelConfig {
            update_rate: 1.0,
            injury_noise_std: 0.0,
            sensory_gain: 1.0,
        };
        let ppcs = ForwardModelConfig {
            update_rate: 0.3,
            injury_noise_std: 0.2,
            sensory_gain: 1.0,
        };
        let mut rng = ChaCha8Rng::seed_from_u64(7);
        let h = simulate(&step_command(50, 30.0), &healthy, &mut rng).unwrap();
        let mut rng2 = ChaCha8Rng::seed_from_u64(7);
        let p = simulate(&step_command(50, 30.0), &ppcs, &mut rng2).unwrap();

        let h_recover = recovery_time(&h, 1.0).unwrap();
        let p_recover = recovery_time(&p, 1.0).unwrap_or(usize::MAX);
        assert!(
            p_recover > h_recover,
            "ppcs {p_recover} should take longer than healthy {h_recover}"
        );
    }

    #[test]
    fn seeding_is_deterministic() {
        let cfg = ForwardModelConfig {
            update_rate: 0.3,
            injury_noise_std: 0.5,
            sensory_gain: 1.0,
        };
        let run = || {
            let mut rng = ChaCha8Rng::seed_from_u64(99);
            simulate(&step_command(30, 10.0), &cfg, &mut rng)
                .unwrap()
                .iter()
                .map(|s| s.mismatch)
                .collect::<Vec<_>>()
        };
        assert_eq!(run(), run());
    }
}
