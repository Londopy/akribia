//! # akribia-core
//!
//! The akribia inference engine — precision-weighted Bayesian / predictive-coding
//! math, fast and GC-free (spec 2.2). Pure numerical code with no I/O; the Python
//! layer ([`crate`] compiled as `akribia._core`) orchestrates, visualises and
//! validates, and the Tauri GUI links this same crate directly (spec 11.1).
//!
//! ## Modules
//!
//! * [`kalman`] — 1-D Kalman filter; the baseline precision-weighted update that
//!   *is* the autism module under different parameterizations.
//! * [`hgf`] — volatility-coupled hierarchical Gaussian filter; models inflexible
//!   precision (HIPPEA / `autism_overfitting`).
//! * [`td_learning`] — Rescorla-Wagner / TD reward learning; the ADHD module
//!   (`discount_factor`, `rpe_noise_std`).
//! * [`forward_model`] — state-space self-motion forward model; the PPCS module.
//! * [`error`] — [`error::AkribiaError`] and the variance-clamping guard.
//!
//! Every fallible function returns [`error::AkribiaError`]; the variance clamp in
//! [`error::clamp_variance`] guards every division-by-variance in the engine.

pub mod error;
pub mod forward_model;
pub mod hgf;
pub mod kalman;
pub mod td_learning;

pub use error::AkribiaError;

#[cfg(feature = "python")]
mod python;
