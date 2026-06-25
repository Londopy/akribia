"""Unstable reward-gain ADHD profile (RPE-noise presentation; spec 1.3)."""
from .base import PrecisionProfile

#: Inconsistent learning from reward — "noisy" rather than uniformly steep
#: discounting. There is literature support for both presentations.
ADHD_RPE_NOISE = PrecisionProfile(name="adhd_rpe_noise", rpe_noise_std=0.4)
