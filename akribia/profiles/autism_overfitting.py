"""HIPPEA / inflexible-precision autism profile (Van de Cruys et al. 2014, spec 1.2).

This profile *is* the HIPPEA account, not a separate thing from it: the single
``precision_flexibility`` knob is the inflexible-precision mechanism. An optional
later split into ``autism_hippea_fixed`` (knob clamped near zero) vs.
``autism_hippea_metalearning`` (knob present but noise-driven) is documented as
an extension in docs/THEORY.md; we ship the single profile initially (spec 1.2).
"""
from .base import PrecisionProfile

#: Strong, narrow, context-specific priors that fail to generalize on a context
#: shift — exposed by the volatility task's trials-to-reconverge metric.
AUTISM_OVERFITTING = PrecisionProfile(name="autism_overfitting", precision_flexibility=0.1)
