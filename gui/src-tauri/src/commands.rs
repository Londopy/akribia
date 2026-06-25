//! Tauri commands — thin wrappers calling straight into the akribia-core crate
//! (spec 11.4). Every command computes with the SAME Rust core the research layer
//! validates; the GUI never reimplements the math. Errors surface as structured
//! strings the frontend renders as toast notifications (spec 2.13).

use akribia_core::{forward_model, hgf, kalman, td_learning};
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use serde::Serialize;

/// A profile's full lever set, mirrored from akribia/profiles (spec 2.4).
#[derive(Serialize, Clone)]
pub struct ProfileInfo {
    pub name: String,
    pub label: String,
    pub group: String,
    pub prior_precision_cap: Option<f64>,
    pub precision_flexibility: f64,
    pub discount_factor: f64,
    pub rpe_noise_std: f64,
    pub forward_model_update_rate: f64,
    pub injury_noise_std: f64,
    /// Which levers actually drive behaviour for this profile (UI highlights them).
    pub active_levers: Vec<String>,
}

#[tauri::command]
pub fn list_profiles() -> Vec<ProfileInfo> {
    fn p(
        name: &str, label: &str, group: &str,
        cap: Option<f64>, flex: f64, disc: f64, rpe: f64, fwd: f64, inj: f64,
        active: &[&str],
    ) -> ProfileInfo {
        ProfileInfo {
            name: name.into(), label: label.into(), group: group.into(),
            prior_precision_cap: cap, precision_flexibility: flex, discount_factor: disc,
            rpe_noise_std: rpe, forward_model_update_rate: fwd, injury_noise_std: inj,
            active_levers: active.iter().map(|s| s.to_string()).collect(),
        }
    }
    vec![
        p("baseline", "Baseline", "Reference", None, 1.0, 0.95, 0.0, 1.0, 0.0, &[]),
        p("autism_weak_prior", "Autism — weak prior", "Autism", Some(0.3), 1.0, 0.95, 0.0, 1.0, 0.0, &["prior_precision_cap"]),
        p("autism_overfitting", "Autism — HIPPEA", "Autism", None, 0.1, 0.95, 0.0, 1.0, 0.0, &["precision_flexibility"]),
        p("adhd_discounting", "ADHD — discounting", "ADHD", None, 1.0, 0.6, 0.0, 1.0, 0.0, &["discount_factor"]),
        p("adhd_rpe_noise", "ADHD — unstable gain", "ADHD", None, 1.0, 0.95, 0.4, 1.0, 0.0, &["rpe_noise_std"]),
        p("ppcs_forward_model", "PPCS — forward model", "PPCS", None, 1.0, 0.95, 0.0, 0.3, 0.2, &["forward_model_update_rate", "injury_noise_std"]),
        p("comorbid", "Comorbid (all levers)", "Comorbid", Some(0.3), 0.1, 0.6, 0.4, 0.3, 0.2,
          &["prior_precision_cap", "precision_flexibility", "discount_factor", "rpe_noise_std", "forward_model_update_rate", "injury_noise_std"]),
        p("audhd_emotion_dysregulation", "AuDHD — emotion dysregulation", "Comorbid", None, 0.15, 0.95, 0.5, 1.0, 0.0,
          &["precision_flexibility", "rpe_noise_std"]),
    ]
}

/// Illusion-susceptibility score for a given prior-precision cap (the autism lever).
#[tauri::command]
pub fn run_illusion(prior_precision_cap: Option<f64>) -> Result<f64, String> {
    let inducers = [1.0_f64; 3];
    let c = kalman::run(
        kalman::Gaussian::new(0.0, 10.0), &inducers,
        &kalman::KalmanConfig { process_noise: 0.0, obs_noise: 0.3, prior_precision_cap: None },
    ).map_err(|e| e.to_string())?;
    let p_c = c.last().unwrap().mean.clamp(0.0, 1.0);
    let perceived = |top_down: f64, bottom_up: f64| -> Result<f64, String> {
        let t = kalman::run(
            kalman::Gaussian::new(top_down, 1.0), &[bottom_up],
            &kalman::KalmanConfig { process_noise: 0.0, obs_noise: 1.0, prior_precision_cap },
        ).map_err(|e| e.to_string())?;
        Ok(t.last().unwrap().mean)
    };
    Ok(perceived(p_c, 0.0)? - perceived(0.0, 0.0)?)
}

/// Volatility-switching belief trajectory (per-step prediction) for a flexibility value.
#[tauri::command]
pub fn run_volatility(precision_flexibility: f64) -> Result<Vec<f64>, String> {
    let mut outcomes = vec![1.0; 50];
    outcomes.extend(vec![0.0; 50]);
    let traj = hgf::run(
        hgf::HgfState::new(0.0, 1.0, 0.0, 1.0), &outcomes,
        &hgf::HgfConfig { obs_noise: 1.0, precision_flexibility, base_process_noise: 0.005 },
    ).map_err(|e| e.to_string())?;
    Ok(traj.into_iter().map(|s| s.prediction).collect())
}

/// Delay-discounting subjective-value fraction at fine-grained delays (for a smooth curve).
#[tauri::command]
pub fn run_discounting(discount_factor: f64) -> Vec<[f64; 2]> {
    (0..=90)
        .step_by(2)
        .map(|d| [d as f64, discount_factor.powf(d as f64)])
        .collect()
}

/// Vestibular self-motion |mismatch| trajectory for the PPCS levers.
#[tauri::command]
pub fn run_self_motion(
    update_rate: f64,
    injury_noise_std: f64,
    seed: u64,
) -> Result<Vec<f64>, String> {
    let mut cmd = vec![30.0_f64; 50];
    cmd.extend(vec![0.0; 30]);
    let cfg = forward_model::ForwardModelConfig { update_rate, injury_noise_std, sensory_gain: 1.0 };
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let traj = forward_model::simulate(&cmd, &cfg, &mut rng).map_err(|e| e.to_string())?;
    Ok(traj.into_iter().map(|s| s.mismatch.abs()).collect())
}

/// Perturbation-recovery arousal trajectory for the AuDHD levers.
#[tauri::command]
pub fn run_perturbation(
    precision_flexibility: f64,
    rpe_noise_std: f64,
    seed: u64,
) -> Result<Vec<f64>, String> {
    let n = 80usize;
    let perturb_at = 30usize;
    let magnitude = 10.0;
    let lr = 0.05 + 0.25 * precision_flexibility.min(1.0);
    let cfg = td_learning::TdConfig { learning_rate: lr, discount_factor: 0.95, rpe_noise_std };
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let post = td_learning::learn_sequence(magnitude, &vec![0.0; n - perturb_at], &cfg, &mut rng)
        .map_err(|e| e.to_string())?;
    let mut arousal = vec![0.0; perturb_at];
    arousal.extend(post.iter().map(|v| v.abs()));
    Ok(arousal)
}
