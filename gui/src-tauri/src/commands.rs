//! Tauri commands — thin wrappers calling straight into the akribia-core crate
//! (spec 11.4). Errors are returned as structured strings the frontend renders as
//! toast notifications (spec 2.13); the GUI never reimplements validation logic.

use akribia_core::{hgf, kalman, td_learning};
use serde::Serialize;

#[derive(Serialize)]
pub struct ProfileInfo {
    pub name: String,
    pub prior_precision_cap: Option<f64>,
    pub precision_flexibility: f64,
    pub discount_factor: f64,
    pub rpe_noise_std: f64,
    pub forward_model_update_rate: f64,
    pub injury_noise_std: f64,
}

/// The eight-profile catalog, mirrored from akribia/profiles (kept in sync via a
/// shared schema in a fuller build; inlined here so the shell is self-contained).
#[tauri::command]
pub fn list_profiles() -> Vec<ProfileInfo> {
    let mk = |name: &str, cap, flex, disc, rpe, fwd, inj| ProfileInfo {
        name: name.to_string(),
        prior_precision_cap: cap,
        precision_flexibility: flex,
        discount_factor: disc,
        rpe_noise_std: rpe,
        forward_model_update_rate: fwd,
        injury_noise_std: inj,
    };
    vec![
        mk("baseline", None, 1.0, 0.95, 0.0, 1.0, 0.0),
        mk("autism_weak_prior", Some(0.3), 1.0, 0.95, 0.0, 1.0, 0.0),
        mk("autism_overfitting", None, 0.1, 0.95, 0.0, 1.0, 0.0),
        mk("adhd_discounting", None, 1.0, 0.6, 0.0, 1.0, 0.0),
        mk("adhd_rpe_noise", None, 1.0, 0.95, 0.4, 1.0, 0.0),
        mk("ppcs_forward_model", None, 1.0, 0.95, 0.0, 0.3, 0.2),
        mk("comorbid", Some(0.3), 0.1, 0.6, 0.4, 0.3, 0.2),
        mk("audhd_emotion_dysregulation", None, 0.15, 0.95, 0.5, 1.0, 0.0),
    ]
}

/// Illusion task: returns the illusion-susceptibility score for a given
/// prior_precision_cap (the live slider in the GUI, spec 11.2).
#[tauri::command]
pub fn run_illusion(prior_precision_cap: Option<f64>) -> Result<f64, String> {
    // Infer P(C) from inducer evidence, then perceived contour at midpoint/control.
    let inducers = [1.0_f64; 3];
    let c = kalman::run(kalman::Gaussian::new(0.0, 10.0), &inducers,
        &kalman::KalmanConfig { process_noise: 0.0, obs_noise: 0.3, prior_precision_cap: None })
        .map_err(|e| e.to_string())?;
    let p_c = c.last().unwrap().mean.clamp(0.0, 1.0);

    let perceived = |top_down: f64, bottom_up: f64| -> Result<f64, String> {
        let t = kalman::run(kalman::Gaussian::new(top_down, 1.0), &[bottom_up],
            &kalman::KalmanConfig { process_noise: 0.0, obs_noise: 1.0, prior_precision_cap })
            .map_err(|e| e.to_string())?;
        Ok(t.last().unwrap().mean)
    };
    let midpoint = perceived(p_c, 0.0)?;
    let control = perceived(0.0, 0.0)?;
    Ok(midpoint - control)
}

/// Volatility task: returns the per-step belief trajectory for charting.
#[tauri::command]
pub fn run_volatility(precision_flexibility: f64) -> Result<Vec<f64>, String> {
    let mut outcomes = vec![1.0; 50];
    outcomes.extend(vec![0.0; 50]);
    let traj = hgf::run(hgf::HgfState::new(0.0, 1.0, 0.0, 1.0), &outcomes,
        &hgf::HgfConfig { obs_noise: 1.0, precision_flexibility, base_process_noise: 0.005 })
        .map_err(|e| e.to_string())?;
    Ok(traj.into_iter().map(|s| s.prediction).collect())
}

/// Delay discounting: indifference amounts at standard delays for a given γ.
#[tauri::command]
pub fn run_discounting(discount_factor: f64) -> Result<Vec<f64>, String> {
    let delays = [1.0, 7.0, 30.0, 90.0];
    let cfg = td_learning::TdConfig { discount_factor, ..Default::default() };
    Ok(delays.iter().map(|&d| 10.0 / td_learning::discounted_value(1.0, d, &cfg)).collect())
}
