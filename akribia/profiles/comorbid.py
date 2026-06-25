"""Generic six-lever comorbid ablation profile (spec 2.4).

The engineering ablation case: all six non-default overrides simultaneously.
Reported as a *collection* of per-task interaction results, never collapsed into
one cross-task sum — the levers mostly drive different tasks in non-comparable
units (spec 2.4 interaction methodology).
"""
from .base import PrecisionProfile

COMORBID = PrecisionProfile(
    name="comorbid",
    prior_precision_cap=0.3,
    precision_flexibility=0.1,
    discount_factor=0.6,
    rpe_noise_std=0.4,
    forward_model_update_rate=0.3,
    injury_noise_std=0.2,
)
