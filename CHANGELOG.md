# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com); this project uses semantic
versioning (`MAJOR.MINOR.PATCH`). Bump `MINOR` for each new profile/task (a public
change to the profile catalog), `PATCH` for fixes, reserve `MAJOR` for breaking
changes to the core engine interface.

## [Unreleased]

### Added
- Rust core engine: `kalman.rs`, `hgf.rs` (volatility-coupled), `td_learning.rs`,
  `forward_model.rs`, with PyO3 bindings (`akribia._core`) and a typed
  `AkribiaError` hierarchy.
- Pure-Python reference core fallback (`akribia._core_fallback`), selected
  automatically when the compiled extension is absent.
- Eight precision profiles (one `PrecisionProfile` shape): `baseline`,
  `autism_weak_prior`, `autism_overfitting`, `adhd_discounting`, `adhd_rpe_noise`,
  `ppcs_forward_model`, `comorbid`, `audhd_emotion_dysregulation`.
- Six demo tasks: illusion, volatility-switching, delay-discounting, self-motion,
  perturbation-recovery, multi-task battery (with per-task interaction analysis).
- Validation: per-parameter recovery, reference-oracle comparison, sensitivity
  sweeps. Benchmarks (Rust criterion + Python).
- Visualization layer with the Okabe-Ito colorblind-safe theme.
- Property-based tests (Rust proptest + Python hypothesis) and pre-registered
  prediction tests.
- Docs: THEORY, LIMITATIONS, architecture (ADR log), BENCHMARKS, GLOSSARY,
  references.bib. Devcontainer, CI workflows, governance files.

## [0.1.0] - 2026-06-24
- Initial public scaffold.
