//! Volatility-coupled hierarchical Gaussian filter (spec 2.3).
//!
//! One level up from the plain Kalman filter: the precision driving belief
//! updates is itself *learned* and depends on an estimated volatility at a
//! higher level. This is what lets us model "inflexible precision across
//! contexts" (the HIPPEA / `autism_overfitting` account, spec 1.2) as an
//! emergent dynamic rather than a hardcoded knob.
//!
//! ## Scope / honesty (ADR-004)
//!
//! This is an HGF-*inspired* two-level filter, not a bit-exact reimplementation
//! of the Mathys/TAPAS three-level HGF. Per the ADR in `docs/architecture.md`
//! we take path (a): an existing validated HGF (PyHGF / TAPAS) is the
//! *reference oracle* compared against in `validation/against_hgf_toolbox.py`,
//! and this Rust implementation is reserved for the speed-critical sweep and
//! recovery loops. Its job is to reproduce the *qualitative* volatility-driven
//! learning-rate dynamics the literature predicts, validated to a stated
//! tolerance — never to be linked against or copied from GPL-licensed TAPAS.
//!
//! ## The `precision_flexibility` lever
//!
//! `precision_flexibility` (κ-like, spec 2.4) scales how strongly the level-2
//! volatility estimate responds to surprise. At 1.0 the filter adapts its
//! learning rate normally; near 0.0 the volatility estimate is frozen, so after
//! an unsignalled context switch the filter cannot raise its learning rate and
//! reconverges slowly — the transient reconvergence delay that is the key
//! discriminating signature of the HIPPEA hypothesis (spec 1.2).

use crate::error::{clamp_variance, AkribiaError};

/// Two-level HGF belief + configuration.
#[derive(Debug, Clone, Copy)]
pub struct HgfState {
    /// Level-1 belief mean (the value being tracked).
    pub mu1: f64,
    /// Level-1 variance.
    pub var1: f64,
    /// Level-2 belief: running volatility estimate (EMA of normalised squared
    /// prediction error) driving level-1 process noise.
    pub mu2: f64,
    /// Level-2 variance.
    pub var2: f64,
}

impl HgfState {
    pub fn new(mu1: f64, var1: f64, mu2: f64, var2: f64) -> Self {
        HgfState {
            mu1,
            var1: clamp_variance(var1),
            mu2,
            var2: clamp_variance(var2),
        }
    }
}

/// Configuration for the volatility-coupled HGF.
#[derive(Debug, Clone, Copy)]
pub struct HgfConfig {
    /// Observation noise (sensory variance).
    pub obs_noise: f64,
    /// Meta-learning rate on volatility — the `precision_flexibility` lever.
    /// 1.0 = flexible; → 0 = inflexible (HIPPEA / overfitting).
    pub precision_flexibility: f64,
    /// Baseline process noise floor at level 1.
    pub base_process_noise: f64,
}

impl Default for HgfConfig {
    fn default() -> Self {
        HgfConfig {
            obs_noise: 1.0,
            precision_flexibility: 1.0,
            base_process_noise: 0.01,
        }
    }
}

/// One trajectory record emitted per step (mirrors the JSON `trajectory` schema).
#[derive(Debug, Clone, Copy)]
pub struct HgfStep {
    pub t: f64,
    pub prediction: f64,
    pub observation: f64,
    pub precision: f64,
    pub prediction_error: f64,
    /// Effective level-1 learning rate this step (volatility-driven).
    pub learning_rate: f64,
    pub volatility: f64,
}

/// Single HGF update on one observation. Returns the new state and the step
/// record.
pub fn step(
    state: HgfState,
    observation: f64,
    cfg: &HgfConfig,
    t: f64,
) -> Result<(HgfState, HgfStep), AkribiaError> {
    if !observation.is_finite() {
        return Err(AkribiaError::invalid(
            "observation",
            observation,
            "must be finite",
        ));
    }
    if cfg.precision_flexibility < 0.0 || !cfg.precision_flexibility.is_finite() {
        return Err(AkribiaError::invalid(
            "precision_flexibility",
            cfg.precision_flexibility,
            "must be finite and non-negative",
        ));
    }

    // --- Level 1 predict: random walk + surprise-gated process noise. ---
    // Process noise (inverse prior precision) rises with the running volatility
    // estimate `mu2`, gated by `precision_flexibility`. A FLEXIBLE model raises
    // its learning rate when recent surprise is high (fast reconvergence after a
    // context switch); an INFLEXIBLE model (low flexibility) cannot, so it adapts
    // slowly -- the literature-grounded HIPPEA / volatility-task signature
    // (spec 1.2). In a stable regime surprise is low, so `q` decays toward the
    // base floor and the learning rate settles low (the model becomes confident).
    let q = cfg.base_process_noise + cfg.precision_flexibility * state.mu2.max(0.0);
    let pred_mu1 = state.mu1;
    let pred_var1 = clamp_variance(state.var1 + q);

    // --- Level 1 update: precision-weighted fusion of the observation. ---
    let prec_prior = 1.0 / pred_var1;
    let prec_like = 1.0 / clamp_variance(cfg.obs_noise);
    let post_prec = prec_prior + prec_like;
    let pe = observation - pred_mu1; // prediction error
    let learning_rate = prec_like / post_prec; // Kalman gain
    let mu1 = pred_mu1 + learning_rate * pe;
    let var1 = 1.0 / post_prec;

    if !mu1.is_finite() {
        return Err(AkribiaError::divergence("hgf::step level-1 mean"));
    }

    // --- Level 2 update: the volatility estimate is an EMA of precision-
    // normalised squared prediction error. `mu2` is the recent-surprise level
    // that feeds back into `q` above. The EMA decay is a fixed structural
    // constant; `precision_flexibility` (which gates how much this volatility
    // raises the learning rate) is the lever, not the decay.
    let surprise = (pe * pe) * prec_like;
    const VOL_DECAY: f64 = 0.5;
    let mu2 = ((1.0 - VOL_DECAY) * state.mu2 + VOL_DECAY * surprise).max(0.0);
    let var2 = clamp_variance(state.var2); // kept simple; full HGF tracks this too

    let new_state = HgfState::new(mu1, var1, mu2, var2);
    let rec = HgfStep {
        t,
        prediction: pred_mu1,
        observation,
        precision: post_prec,
        prediction_error: pe,
        learning_rate,
        volatility: q,
    };
    Ok((new_state, rec))
}

/// Run the HGF over a sequence of observations.
pub fn run(
    initial: HgfState,
    observations: &[f64],
    cfg: &HgfConfig,
) -> Result<Vec<HgfStep>, AkribiaError> {
    let mut state = initial;
    let mut out = Vec::with_capacity(observations.len());
    for (i, &z) in observations.iter().enumerate() {
        let (next, rec) = step(state, z, cfg, i as f64)?;
        state = next;
        out.push(rec);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn converges_on_a_stationary_signal() {
        let cfg = HgfConfig::default();
        let obs = vec![5.0; 200];
        let traj = run(HgfState::new(0.0, 1.0, 0.0, 1.0), &obs, &cfg).unwrap();
        let last = traj.last().unwrap();
        assert!(
            (last.prediction - 5.0).abs() < 0.2,
            "pred = {}",
            last.prediction
        );
    }

    #[test]
    fn inflexible_precision_reconverges_more_slowly_after_a_switch() {
        // Build a signal that switches from 0 -> 10 at trial 100.
        let mut obs = vec![0.0; 100];
        obs.extend(vec![10.0; 100]);

        let flexible = HgfConfig {
            precision_flexibility: 1.0,
            ..Default::default()
        };
        let inflexible = HgfConfig {
            precision_flexibility: 0.05,
            ..Default::default()
        };

        let reconverge = |cfg: &HgfConfig| -> usize {
            let traj = run(HgfState::new(0.0, 1.0, 0.0, 1.0), &obs, cfg).unwrap();
            // trials after the switch to come within 1.0 of the new level.
            for (i, s) in traj.iter().enumerate().skip(100) {
                if (s.prediction - 10.0).abs() < 1.0 {
                    return i - 100;
                }
            }
            obs.len()
        };

        let t_flex = reconverge(&flexible);
        let t_inflex = reconverge(&inflexible);
        // The HIPPEA prediction: inflexible precision -> slower reconvergence.
        assert!(
            t_inflex >= t_flex,
            "inflexible {t_inflex} should be >= flexible {t_flex}"
        );
    }

    proptest! {
        #[test]
        fn precision_stays_positive_and_finite(
            obs in proptest::collection::vec(-50.0f64..50.0, 1..50),
            flex in 0.0f64..2.0,
        ) {
            let cfg = HgfConfig { precision_flexibility: flex, ..Default::default() };
            let traj = run(HgfState::new(0.0, 1.0, 0.0, 1.0), &obs, &cfg).unwrap();
            for s in traj {
                prop_assert!(s.precision > 0.0 && s.precision.is_finite());
            }
        }
    }
}
