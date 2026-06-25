"""Weak-priors / hypo-priors autism profile (Pellicano & Burr 2012, spec 1.2)."""
from .base import PrecisionProfile

#: Reduced illusion susceptibility, stronger reliance on raw sensory data, more
#: "literal" perception. Capping prior precision means the top-down prediction
#: can never become confident enough to override absent local evidence.
AUTISM_WEAK_PRIOR = PrecisionProfile(name="autism_weak_prior", prior_precision_cap=0.3)
