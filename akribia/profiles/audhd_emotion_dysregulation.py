"""Literature-grounded AuDHD emotion-dysregulation profile (spec 1.5.1).

Distinct from generic ``comorbid``: this encodes a specific published hypothesis
about autism-ADHD comorbidity as a *non-additive* mechanism. Autism's
contribution is high/slow-updating precision (NOT low precision — almost the
opposite lever from ``autism_weak_prior``); ADHD's is *unstable gain*
(``rpe_noise_std``, NOT steep ``discount_factor``). The behavioural signature a
faithful simulation should reproduce: large-but-rare departures that take a long
time to settle (autism inertia) combined with frequent, smaller, erratic
fluctuations (ADHD) — qualitatively distinct from the average of the two.
"""
from .base import PrecisionProfile

AUDHD_EMOTION_DYSREGULATION = PrecisionProfile(
    name="audhd_emotion_dysregulation",
    prior_precision_cap=None,        # autism side: NOT capped low
    precision_flexibility=0.15,      # autism side: sluggish updating
    discount_factor=0.95,            # ADHD reward-discounting stays at baseline
    rpe_noise_std=0.5,               # ADHD side: unstable gain
    forward_model_update_rate=1.0,   # PPCS not implicated in this account
    injury_noise_std=0.0,
)
