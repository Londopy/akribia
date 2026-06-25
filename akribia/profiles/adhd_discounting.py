"""Steep temporal-discounting ADHD profile (Sutton & Barto; spec 1.3)."""
from .base import PrecisionProfile

#: Excessively steep devaluation of delayed reward (low γ): impulsive choice in
#: the delay-discounting task, distant value collapses.
ADHD_DISCOUNTING = PrecisionProfile(name="adhd_discounting", discount_factor=0.6)
