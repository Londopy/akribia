# Profile Catalog

Every profile is one `PrecisionProfile` (six levers) with specific overrides. The
literature claim each one tests is in `docs/THEORY.md`.

| Profile | Overrides | Behaviour produced | Discriminating task |
|---|---|---|---|
| `baseline` | (defaults) | neurotypical reference | all |
| `autism_weak_prior` | `prior_precision_cap=0.3` | reduced illusion susceptibility, literal perception | illusion |
| `autism_overfitting` (HIPPEA) | `precision_flexibility=0.1` | context-rigid priors; slow reconvergence after a switch | volatility |
| `adhd_discounting` | `discount_factor=0.6` | steep devaluation of delayed reward | delay discounting |
| `adhd_rpe_noise` | `rpe_noise_std=0.4` | inconsistent/noisy reward learning | perturbation recovery |
| `ppcs_forward_model` | `forward_model_update_rate=0.3`, `injury_noise_std=0.2` | persistent sensorimotor mismatch | self-motion |
| `comorbid` | all six | engineering ablation, reported per-task | battery |
| `audhd_emotion_dysregulation` | `precision_flexibility=0.15`, `rpe_noise_std=0.5` | slow AND erratic recovery (distinct, not averaged) | perturbation recovery |

Starting values are placeholders producing *visibly different* behaviour; the
sensitivity sweeps, not the defaults, are the evidence of a captured mechanism.
**Extension point:** see CONTRIBUTING.md to add a new profile (roadmap: schizophrenia,
anxiety, depression, addiction — they slot into the same architecture).
