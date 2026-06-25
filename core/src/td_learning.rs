//! Temporal-difference / Rescorla-Wagner reward learning (the ADHD module, spec 2.3).
//!
//! ```text
//! prediction_error = reward_received - predicted_value
//! predicted_value += learning_rate * prediction_error          (Rescorla-Wagner)
//! discounted_future_value = Σ γ^t * reward[t]                   (TD with delay)
//! ```
//!
//! Two ADHD levers (spec 2.4):
//! * `discount_factor` (γ) — steep devaluation of delayed reward (impulsivity).
//! * `rpe_noise_std` — Gaussian noise injected into the RPE signal itself,
//!   modelling *unstable* rather than uniformly *steep* learning. Distinct
//!   presentations in the literature support both.
//!
//! All randomness is driven by an explicitly seeded RNG passed in by the caller
//! (spec 2.6.1) — never ambient global state, so a re-run reproduces the same
//! trajectory on the same hardware.

use crate::error::AkribiaError;
use rand::Rng;
use rand_distr::{Distribution, Normal};

/// Configuration for the reward-learning agent.
#[derive(Debug, Clone, Copy)]
pub struct TdConfig {
    /// Base learning rate (α) on the reward-prediction error.
    pub learning_rate: f64,
    /// Discount factor γ ∈ (0, 1]; lower = steeper discounting (ADHD lever).
    pub discount_factor: f64,
    /// Std-dev of Gaussian noise added to the RPE signal (ADHD lever).
    pub rpe_noise_std: f64,
}

impl Default for TdConfig {
    fn default() -> Self {
        TdConfig {
            learning_rate: 0.2,
            discount_factor: 0.95,
            rpe_noise_std: 0.0,
        }
    }
}

/// One step of Rescorla-Wagner value learning under a (possibly noisy) RPE.
///
/// Returns `(new_value, realized_rpe)`. The realized RPE includes any injected
/// noise, which is what downstream metrics see.
pub fn rw_step<R: Rng>(
    predicted_value: f64,
    reward: f64,
    cfg: &TdConfig,
    rng: &mut R,
) -> Result<(f64, f64), AkribiaError> {
    if cfg.learning_rate < 0.0 || cfg.learning_rate > 1.0 {
        return Err(AkribiaError::invalid(
            "learning_rate",
            cfg.learning_rate,
            "must be in [0, 1]",
        ));
    }
    if cfg.rpe_noise_std < 0.0 || !cfg.rpe_noise_std.is_finite() {
        return Err(AkribiaError::invalid(
            "rpe_noise_std",
            cfg.rpe_noise_std,
            "must be finite and non-negative",
        ));
    }
    let mut rpe = reward - predicted_value;
    if cfg.rpe_noise_std > 0.0 {
        let normal = Normal::new(0.0, cfg.rpe_noise_std).map_err(|_| {
            AkribiaError::invalid("rpe_noise_std", cfg.rpe_noise_std, "invalid normal")
        })?;
        rpe += normal.sample(rng);
    }
    let new_value = predicted_value + cfg.learning_rate * rpe;
    Ok((new_value, rpe))
}

/// Subjective (discounted) value of a `reward` available after `delay` steps,
/// under exponential discounting `γ^delay`. This is what the delay-discounting
/// task uses to elicit indifference points.
pub fn discounted_value(reward: f64, delay: f64, cfg: &TdConfig) -> f64 {
    cfg.discount_factor.powf(delay) * reward
}

/// Learn a value estimate across a sequence of rewards (a single bandit arm),
/// returning the value trajectory.
pub fn learn_sequence<R: Rng>(
    initial_value: f64,
    rewards: &[f64],
    cfg: &TdConfig,
    rng: &mut R,
) -> Result<Vec<f64>, AkribiaError> {
    let mut v = initial_value;
    let mut out = Vec::with_capacity(rewards.len());
    for &r in rewards {
        let (next, _rpe) = rw_step(v, r, cfg, rng)?;
        v = next;
        out.push(v);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;

    #[test]
    fn steeper_discounting_devalues_delayed_reward_more() {
        let baseline = TdConfig {
            discount_factor: 0.95,
            ..Default::default()
        };
        let adhd = TdConfig {
            discount_factor: 0.6,
            ..Default::default()
        };
        let v_base = discounted_value(50.0, 10.0, &baseline);
        let v_adhd = discounted_value(50.0, 10.0, &adhd);
        assert!(
            v_adhd < v_base,
            "adhd {v_adhd} should be < baseline {v_base}"
        );
    }

    #[test]
    fn noiseless_rpe_converges_to_stationary_reward() {
        let cfg = TdConfig {
            rpe_noise_std: 0.0,
            ..Default::default()
        };
        let mut rng = ChaCha8Rng::seed_from_u64(0);
        let traj = learn_sequence(0.0, &vec![1.0; 200], &cfg, &mut rng).unwrap();
        assert!((traj.last().unwrap() - 1.0).abs() < 1e-3);
    }

    #[test]
    fn seeding_is_deterministic() {
        let cfg = TdConfig {
            rpe_noise_std: 0.5,
            ..Default::default()
        };
        let run = || {
            let mut rng = ChaCha8Rng::seed_from_u64(42);
            learn_sequence(0.0, &vec![1.0; 50], &cfg, &mut rng).unwrap()
        };
        assert_eq!(run(), run());
    }

    proptest! {
        // PE -> 0 monotonically (in expectation) as the model converges on a
        // stationary, noiseless reward distribution (spec 2.5.1).
        #[test]
        fn converges_on_stationary_noiseless_reward(reward in -10.0f64..10.0) {
            let cfg = TdConfig { rpe_noise_std: 0.0, learning_rate: 0.1, ..Default::default() };
            let mut rng = ChaCha8Rng::seed_from_u64(1);
            let traj = learn_sequence(0.0, &vec![reward; 500], &cfg, &mut rng).unwrap();
            let final_err = (traj.last().unwrap() - reward).abs();
            prop_assert!(final_err < 0.05, "final_err = {final_err}");
        }
    }
}
