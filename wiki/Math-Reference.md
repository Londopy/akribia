# Math Reference

Every equation in one place (spec 7). Derived in `docs/THEORY.md`; canonical code in
`core/`.

## Precision-weighted Bayesian (Kalman) update — the baseline, = the autism module
```
predict:  prior_var = prev_var + process_noise
          precision_prior = 1 / prior_var          (optionally capped: weak-prior lever)
          precision_like  = 1 / obs_var
update:   posterior_precision = precision_prior + precision_like
          posterior_mean = (precision_prior·prior_mean + precision_like·obs) / posterior_precision
          posterior_var  = 1 / posterior_precision
```
Variance is clamped to ≥ `1e-6` before every inversion (numerical-stability guard).

## Volatility-coupled HGF (autism overfitting / HIPPEA)
```
q  = base_process_noise + precision_flexibility · volatility_estimate   (surprise-gated)
... Kalman update with prior_var = prev_var + q ...
volatility_estimate ← (1−decay)·volatility_estimate + decay·(prediction_error² · precision_like)
```
Low `precision_flexibility` ⇒ q cannot rise on surprise ⇒ slow reconvergence (HIPPEA).

## TD / Rescorla-Wagner (ADHD)
```
prediction_error = reward − predicted_value (+ Gaussian noise·rpe_noise_std)
predicted_value += learning_rate · prediction_error
discounted_value(reward, delay) = discount_factor^delay · reward
```

## Forward model (PPCS)
```
predicted   = model_estimate
actual      = sensory_gain · motor_command + injury_noise
mismatch    = actual − predicted
model_estimate += forward_model_update_rate · mismatch
```
Impaired `update_rate` ⇒ mismatch persists (does not habituate).
