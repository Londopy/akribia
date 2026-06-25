//! Error type for the akribia core engine (spec 2.13).
//!
//! Every fallible function in `core/` returns [`Result<T, AkribiaError>`] rather
//! than panicking or returning a sentinel value. Panics are reserved for genuine
//! programmer-error invariant violations, not expected failure modes like a bad
//! user-supplied parameter. The PyO3 layer (the `python` module, behind the `python` feature) maps each variant
//! onto a specific Python exception type so callers can handle failure modes
//! without parsing error strings.

use thiserror::Error;

/// The minimum positive variance permitted anywhere in the engine.
///
/// Every update divides by variance to obtain precision; as precision is pushed
/// higher (exactly what `autism_overfitting` deliberately does) variance
/// approaches zero and naive division blows up. We clamp variance to this
/// epsilon before computing precision (spec 2.3).
pub const VAR_EPSILON: f64 = 1e-6;

/// All error conditions the akribia core can report.
#[derive(Debug, Error, Clone, PartialEq)]
pub enum AkribiaError {
    /// A variance or precision argument was non-finite or non-positive in a way
    /// the caller is responsible for (as opposed to a value the engine clamps).
    #[error("invalid parameter '{name}': {value} ({reason})")]
    InvalidParameter {
        name: String,
        value: f64,
        reason: String,
    },

    /// A covariance/precision matrix could not be inverted.
    #[error("singular matrix encountered in {context}")]
    SingularMatrix { context: String },

    /// The filter produced a non-finite state (NaN/inf) — usually a sign of a
    /// divergent configuration that escaped the variance clamp.
    #[error("numerical divergence in {context}: produced a non-finite value")]
    NumericalDivergence { context: String },

    /// Two sequences that must be the same length were not.
    #[error("dimension mismatch in {context}: expected {expected}, got {got}")]
    DimensionMismatch {
        context: String,
        expected: usize,
        got: usize,
    },
}

impl AkribiaError {
    pub(crate) fn invalid(name: &str, value: f64, reason: &str) -> Self {
        AkribiaError::InvalidParameter {
            name: name.to_string(),
            value,
            reason: reason.to_string(),
        }
    }

    pub(crate) fn divergence(context: &str) -> Self {
        AkribiaError::NumericalDivergence {
            context: context.to_string(),
        }
    }
}

/// Clamp a variance to a strictly positive value before it is inverted.
///
/// This is the single guard referenced throughout the engine; the property test
/// in each module asserts precision stays strictly positive, which catches any
/// update path that forgets to route through here.
#[inline]
pub fn clamp_variance(var: f64) -> f64 {
    if var.is_nan() {
        VAR_EPSILON
    } else {
        var.max(VAR_EPSILON)
    }
}

/// Convert a clamped variance to a precision (inverse variance).
#[inline]
pub fn precision_of(var: f64) -> f64 {
    1.0 / clamp_variance(var)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clamp_floors_at_epsilon() {
        assert_eq!(clamp_variance(0.0), VAR_EPSILON);
        assert_eq!(clamp_variance(-5.0), VAR_EPSILON);
        assert_eq!(clamp_variance(f64::NAN), VAR_EPSILON);
        assert_eq!(clamp_variance(2.0), 2.0);
    }

    #[test]
    fn precision_is_always_positive_and_finite() {
        for v in [-1.0, 0.0, 1e-12, 1e-6, 1.0, 1e6] {
            let p = precision_of(v);
            assert!(p.is_finite() && p > 0.0, "precision_of({v}) = {p}");
        }
    }
}
