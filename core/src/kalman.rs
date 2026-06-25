//! 1-D Kalman filter — the simplest correct implementation of precision-weighted
//! Bayesian updating (spec 2.3).
//!
//! This single block of math, with different fixed/variable parameterizations,
//! *is* the autism module. Build it once, parameterize it many ways. The
//! `predict` step propagates the state forward and **adds** process noise
//! (uncertainty grows); the `update` step fuses an observation and **never**
//! increases uncertainty. The property tests at the bottom encode that
//! distinction precisely — the variance-shrinking invariant holds for `update`
//! alone, not the full predict→update cycle (spec 2.5.1).

use crate::error::{clamp_variance, precision_of, AkribiaError};

/// Belief over a 1-D latent scalar: a Gaussian with `mean` and `var`iance.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Gaussian {
    pub mean: f64,
    pub var: f64,
}

impl Gaussian {
    pub fn new(mean: f64, var: f64) -> Self {
        Gaussian {
            mean,
            var: clamp_variance(var),
        }
    }

    /// Precision (inverse variance) of this belief.
    #[inline]
    pub fn precision(&self) -> f64 {
        precision_of(self.var)
    }
}

/// Configuration of a 1-D Kalman filter.
///
/// `prior_precision_cap` is the autism lever (spec 2.4): if `Some(cap)`, the
/// prior's precision is never allowed to exceed `cap`, which models *weak
/// priors* — the top-down prediction can never become confident enough to
/// override raw sensory evidence, producing more "literal" perception.
#[derive(Debug, Clone, Copy)]
pub struct KalmanConfig {
    /// Process noise added during the predict step (drives uncertainty growth).
    pub process_noise: f64,
    /// Observation noise (sensory variance); its inverse is sensory precision.
    pub obs_noise: f64,
    /// Optional ceiling on prior precision — the `autism_weak_prior` mechanism.
    pub prior_precision_cap: Option<f64>,
}

impl Default for KalmanConfig {
    fn default() -> Self {
        KalmanConfig {
            process_noise: 0.01,
            obs_noise: 1.0,
            prior_precision_cap: None,
        }
    }
}

/// Predict step: propagate the belief forward and add process noise.
///
/// Uncertainty **increases** here — this is the step a whole-cycle variance test
/// would (correctly) see grow. The latent is assumed to follow a random walk, so
/// the mean is unchanged and the variance accrues `process_noise`.
pub fn predict(prev: Gaussian, process_noise: f64) -> Result<Gaussian, AkribiaError> {
    if process_noise < 0.0 || !process_noise.is_finite() {
        return Err(AkribiaError::invalid(
            "process_noise",
            process_noise,
            "must be finite and non-negative",
        ));
    }
    let var = clamp_variance(prev.var + process_noise);
    Ok(Gaussian::new(prev.mean, var))
}

/// Measurement-update step: fuse `observation` (with `obs_noise` variance) into
/// the prior belief using precision-weighted averaging.
///
/// ```text
/// precision_prior      = 1 / prior_var      (optionally capped)
/// precision_likelihood = 1 / obs_var
/// posterior_precision  = precision_prior + precision_likelihood
/// posterior_mean       = (precision_prior * prior_mean
///                         + precision_likelihood * observation) / posterior_precision
/// posterior_var        = 1 / posterior_precision
/// ```
///
/// Posterior variance never exceeds the (post-cap) prior variance — adding data
/// cannot increase uncertainty. The `prior_precision_cap` lever can *lower*
/// prior precision (raise its effective variance), shifting weight toward the
/// observation; that is the weak-prior mechanism, and it still never violates
/// the shrink-on-update invariant.
pub fn update(
    prior: Gaussian,
    observation: f64,
    cfg: &KalmanConfig,
) -> Result<Gaussian, AkribiaError> {
    if !observation.is_finite() {
        return Err(AkribiaError::invalid(
            "observation",
            observation,
            "must be finite",
        ));
    }
    if cfg.obs_noise < 0.0 || !cfg.obs_noise.is_finite() {
        return Err(AkribiaError::invalid(
            "obs_noise",
            cfg.obs_noise,
            "must be finite and non-negative",
        ));
    }

    let mut precision_prior = prior.precision();
    if let Some(cap) = cfg.prior_precision_cap {
        if cap <= 0.0 || !cap.is_finite() {
            return Err(AkribiaError::invalid(
                "prior_precision_cap",
                cap,
                "must be finite and positive",
            ));
        }
        precision_prior = precision_prior.min(cap);
    }

    let precision_likelihood = precision_of(cfg.obs_noise);
    let posterior_precision = precision_prior + precision_likelihood;
    if posterior_precision <= 0.0 || !posterior_precision.is_finite() {
        return Err(AkribiaError::divergence(
            "kalman::update posterior precision",
        ));
    }

    let posterior_mean =
        (precision_prior * prior.mean + precision_likelihood * observation) / posterior_precision;
    let posterior_var = 1.0 / posterior_precision;

    if !posterior_mean.is_finite() {
        return Err(AkribiaError::divergence("kalman::update posterior mean"));
    }
    Ok(Gaussian::new(posterior_mean, posterior_var))
}

/// Run a full predict→update sweep over a sequence of observations, returning the
/// posterior belief at every step. This is the hot loop benchmarked in
/// `benches/kalman_bench.rs`.
pub fn run(
    initial: Gaussian,
    observations: &[f64],
    cfg: &KalmanConfig,
) -> Result<Vec<Gaussian>, AkribiaError> {
    let mut belief = initial;
    let mut out = Vec::with_capacity(observations.len());
    for &z in observations {
        let prior = predict(belief, cfg.process_noise)?;
        belief = update(prior, z, cfg)?;
        out.push(belief);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    use proptest::prelude::*;

    #[test]
    fn precision_weighted_average_is_correct() {
        // Equal precision prior and likelihood -> posterior mean is the midpoint.
        let prior = Gaussian::new(0.0, 1.0);
        let cfg = KalmanConfig {
            process_noise: 0.0,
            obs_noise: 1.0,
            prior_precision_cap: None,
        };
        let post = update(prior, 2.0, &cfg).unwrap();
        assert_relative_eq!(post.mean, 1.0, epsilon = 1e-12);
        assert_relative_eq!(post.var, 0.5, epsilon = 1e-12);
    }

    #[test]
    fn weak_prior_cap_shifts_weight_toward_observation() {
        let prior = Gaussian::new(0.0, 0.01); // very confident prior
        let strong = update(
            prior,
            5.0,
            &KalmanConfig {
                process_noise: 0.0,
                obs_noise: 1.0,
                prior_precision_cap: None,
            },
        )
        .unwrap();
        let weak = update(
            prior,
            5.0,
            &KalmanConfig {
                process_noise: 0.0,
                obs_noise: 1.0,
                prior_precision_cap: Some(0.3),
            },
        )
        .unwrap();
        // Capping prior precision pulls the posterior closer to the observation.
        assert!(
            weak.mean > strong.mean,
            "weak={} strong={}",
            weak.mean,
            strong.mean
        );
    }

    #[test]
    fn zero_noise_observation_collapses_variance() {
        // A (near) perfectly certain observation collapses posterior variance
        // regardless of the prior (spec 2.5.1 invariant).
        let prior = Gaussian::new(0.0, 1000.0);
        let cfg = KalmanConfig {
            process_noise: 0.0,
            obs_noise: 1e-9,
            prior_precision_cap: None,
        };
        let post = update(prior, 3.0, &cfg).unwrap();
        // Posterior variance collapses to the engine's variance floor (the clamp
        // from spec 2.3 prevents it going below VAR_EPSILON), and the mean snaps
        // to the (near-perfectly-certain) observation regardless of the prior.
        assert!(
            post.var <= crate::error::VAR_EPSILON * (1.0 + 1e-9),
            "var = {}",
            post.var
        );
        assert_relative_eq!(post.mean, 3.0, epsilon = 1e-3);
    }

    #[test]
    fn rejects_non_finite_observation() {
        let prior = Gaussian::new(0.0, 1.0);
        let err = update(prior, f64::NAN, &KalmanConfig::default()).unwrap_err();
        assert!(matches!(err, AkribiaError::InvalidParameter { .. }));
    }

    proptest! {
        // Property: the UPDATE step alone never increases variance (spec 2.5.1).
        // Pointed at update() in isolation, NOT the predict->update cycle.
        #[test]
        fn update_never_increases_variance(
            prior_mean in -100.0f64..100.0,
            prior_var in 1e-3f64..1e3,
            obs in -100.0f64..100.0,
            obs_noise in 1e-3f64..1e3,
        ) {
            let prior = Gaussian::new(prior_mean, prior_var);
            let cfg = KalmanConfig { process_noise: 0.0, obs_noise, prior_precision_cap: None };
            let post = update(prior, obs, &cfg).unwrap();
            prop_assert!(post.var <= prior.var + 1e-9, "post.var {} > prior.var {}", post.var, prior.var);
        }

        // Property: precision is always strictly positive — catches the variance
        // clamp being removed or bypassed (spec 2.5.1 / 2.3).
        #[test]
        fn precision_always_positive(
            mean in -1e6f64..1e6,
            var in -10.0f64..1e6,
        ) {
            let g = Gaussian::new(mean, var);
            prop_assert!(g.precision() > 0.0 && g.precision().is_finite());
        }

        // Property: the predict step never DECREASES variance (process noise >= 0).
        #[test]
        fn predict_never_decreases_variance(
            mean in -100.0f64..100.0,
            var in 1e-3f64..1e3,
            q in 0.0f64..10.0,
        ) {
            let prior = Gaussian::new(mean, var);
            let pred = predict(prior, q).unwrap();
            prop_assert!(pred.var >= prior.var - 1e-9);
        }
    }
}
