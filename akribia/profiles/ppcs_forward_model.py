"""Sensorimotor forward-model mismatch PPCS profile (NERD model; spec 1.4)."""
from .base import PrecisionProfile

#: Impaired forward-model update rate plus post-injury afferent noise: persistent
#: unresolved sensorimotor prediction error ("dizziness") that does not habituate.
PPCS_FORWARD_MODEL = PrecisionProfile(
    name="ppcs_forward_model",
    forward_model_update_rate=0.3,
    injury_noise_std=0.2,
)
