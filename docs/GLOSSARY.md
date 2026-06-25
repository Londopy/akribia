# Glossary

Plain-English, one line each. Linked from the top of every theory page so a reader
without a computational-neuroscience background can still follow the plots (spec 9).

- **Prior** — what the model expects before seeing new data (a top-down prediction).
- **Posterior** — the updated belief after combining the prior with new evidence.
- **Prediction error** — the gap between what was predicted and what was observed.
- **Precision** — how much the system trusts a signal; mathematically `1/variance`
  (inverse variance). High precision = high trust = strong influence on the update.
- **Likelihood** — how probable the observed data is under a given hypothesis; its
  precision is "sensory precision."
- **Variance** — spread/uncertainty of a distribution. Low variance = high precision.
- **Free energy** — a quantity the brain is hypothesised to minimise; loosely,
  long-run prediction error. The unifying principle behind predictive coding.
- **Reward prediction error (RPE)** — the gap between received and expected reward;
  the dopamine-linked teaching signal in reinforcement learning.
- **Discount factor (γ)** — how much future rewards are devalued relative to
  immediate ones. Lower γ = steeper discounting = more impulsive.
- **Learning rate (α)** — how much each prediction error moves the belief.
- **Forward model** — an internal predictor of the sensory consequence of one's own
  action (e.g. the expected vestibular signal from a head turn).
- **Efference copy** — a copy of a motor command used to predict its sensory result.
- **Volatility** — how fast the world is changing; a higher level in the hierarchy
  that controls how quickly lower-level precision should adapt.
- **Kalman filter** — the simplest correct precision-weighted Bayesian update for a
  Gaussian belief over time.
- **HGF (Hierarchical Gaussian Filter)** — a filter where precision itself is
  learned and depends on an estimated volatility one level up.
- **Precision flexibility** — (akribia's lever) how readily the model adjusts its
  learning rate in response to surprise; low = inflexible (the HIPPEA mechanism).
- **HIPPEA** — High, Inflexible Precision of Prediction Errors in Autism.
- **PPCS** — persistent post-concussion symptoms.
- **AuDHD** — co-occurring autism and ADHD.
