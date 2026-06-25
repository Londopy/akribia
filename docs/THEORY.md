# Theory

> **Plain-language version first.** Each section opens with a short, jargon-free
> paragraph, then goes deeper. Read until it stops being useful to you and stop
> there. Terms in `code font` are defined in [GLOSSARY.md](./GLOSSARY.md).
> Citations resolve against [references.bib](./references.bib).

> **akribia is not a diagnostic tool.** It implements *published, contested*
> mathematical models to illustrate theoretical mechanisms. See
> [LIMITATIONS.md](./LIMITATIONS.md). The autism precision-weighting literature
> in particular is actively contested; this project models competing hypotheses,
> not settled fact.

---

## 1. The one idea everything else is built on

**Plain language.** Your brain is constantly guessing what comes next. When a
guess (a *prediction*) meets reality (*sensory evidence*), the gap between them
is a *prediction error*. The brain doesn't trust every signal equally — it
weights each by how reliable it thinks that signal is. That reliability weight is
called *precision*. akribia's thesis is that **the same precision-weighting math,
miscalibrated at different points, produces three phenotypically distinct
conditions** — autism, ADHD, and PPCS — and that a comorbid case is just running
more than one miscalibration at once.

**Deeper.** Predictive coding casts the brain as a hierarchical inference machine
[@friston2009predictive; @clark2013whatever]. At each level a top-down prediction
meets a bottom-up signal; the prediction error is scaled by `precision` (inverse
variance — `1/σ²`) before it drives belief updates. Precision is thought to be
implemented neurally as the synaptic gain on error-reporting neurons
[@friston2010free]. The baseline update akribia implements is the precision-
weighted Gaussian (Kalman) step:

```
posterior_precision = precision_prior + precision_likelihood
posterior_mean      = (precision_prior·prior_mean + precision_likelihood·obs) / posterior_precision
```

This single block, parameterised differently, *is* the autism module — there is
no separate code path per condition (see [architecture.md](./architecture.md) §3).

---

## 2. Autism — the contested precision debate

**Plain language.** Two competing stories. (1) *Weak priors*: autistic perception
leans less on expectation and more on raw data, which would reduce certain visual
illusions. (2) *Inflexible precision (HIPPEA)*: not that priors are weak, but that
the brain can't flexibly adjust how much it trusts prediction errors as context
changes. akribia ships both as switchable profiles and lets the simulation show
where they diverge — because the evidence is genuinely mixed.

**Deeper.**
- **Weak priors / hypo-priors** [@pellicano2012worlds] → profile
  `autism_weak_prior` (`prior_precision_cap = 0.3`). Predicts reduced illusion
  susceptibility and a local-over-global bias. akribia's illusion task confirms a
  *reduced* illusion-susceptibility score under this profile.
- **HIPPEA — High, Inflexible Precision of Prediction Errors in Autism**
  [@vandecruys2014precise] → profile `autism_overfitting`
  (`precision_flexibility = 0.1`). The claim is *not* uniformly weak priors but an
  inability to flexibly adjust prediction-error precision across contexts. This is
  one account expressed through one lever, explaining both rigidity (overfitting
  to specific contexts) and, in volatile environments, exhausting hypervigilance.
  > **Verification note (spec 1.2).** This attribution — that Van de Cruys et al.
  > (2014), *Precise minds in uncertain worlds*, is the source of the HIPPEA
  > terminology — is plausible and the mechanisms line up, but should be confirmed
  > against the primary source before being treated as settled. It is stated here
  > with that caveat.
- **Overweighting of sensory input** [@brock2012alternative] — functionally
  similar outcome, different mechanism (high sensory precision rather than literally
  weak priors).
- **Aberrant/imbalanced precision** [@lawson2014aberrant] — it's the *relative*
  balance of sensory vs. prior precision that's off. Closely related to HIPPEA;
  both are "deficient precision estimation" accounts.
- **Empirical test, not a fifth theory** [@karvelis2018autistic] — weighs weak-priors
  against inflexible-precision; cited as evidence in the debate.
- **State of the field.** A 2020 systematic review found highly mixed evidence, a
  slight majority finding *no* significant difference in prior integration. akribia
  builds this uncertainty in: competing hypotheses are switchable profiles, not
  settled facts.

**The genuinely distinct sub-mechanisms are *within* HIPPEA**, not a separate
profile: (1) precision-encoding itself fixed high vs. (2) a deficient meta-learning
signal. These would be `autism_hippea_fixed` vs. `autism_hippea_metalearning` —
documented here as an extension; the initial build ships the single
`autism_overfitting` knob.

**Pre-registered prediction (spec 1.2 / 1.5.2).** The volatility task should show a
*transient* reconvergence delay after an unsignalled context switch for
`autism_overfitting` — not a permanent steady-state deficit. akribia's
implementation reproduces this: ~3.9 vs. ~1.85 trials-to-reconverge (overfitting
vs. baseline), with comparable pre-flip beliefs.

---

## 3. ADHD — reward-prediction-error and temporal discounting

**Plain language.** ADHD is modelled here as a *reward/valuation* problem, not a
perceptual one. Either delayed rewards are devalued too steeply (impulsivity), or
the reward signal itself is unstable/noisy. Notably, when ADHD adults were tested
on the *perceptual*-precision paradigm used in the autism literature, their prior
learning came out **intact** — a real null result that justifies giving ADHD a
different lever than autism rather than collapsing them together.

**Deeper.** Dopamine reward-prediction-error (RPE) [@schultz1997neural], formalised
as temporal-difference learning with a discount factor γ [@sutton2018reinforcement];
ADHD is frequently modelled as excessively steep discounting (low γ) →
`adhd_discounting` (`discount_factor = 0.6`). A second presentation is *unstable*
rather than steep: noise injected into the RPE signal → `adhd_rpe_noise`
(`rpe_noise_std = 0.4`). Striatal dopamine operates across a spectrum of time
horizons, motivating "different presentations as different distributions over
discount rates." The perceptual-precision account of ADHD is included only as an
explicitly-named *null* test (`adhd_perceptual_precision_null` would be the honest
name), never as an established mechanism.

---

## 4. PPCS — sensorimotor forward-model mismatch

**Plain language.** After a concussion, the brain's prediction of what its own head
movement *should* feel like stops matching the actual signal from the balance
organs. That unresolved mismatch is modelled here as dizziness that won't settle.
This is the most mathematically distinct module — a control-theory forward model,
not a perceptual prior or a reward signal.

**Deeper.** The NERD model [@nerd2025] frames persistent post-concussion symptoms as
systems-level failure to gate vestibular afferents; an active-inference account
frames it as inappropriate updating of the predict-and-explain loop. akribia
implements an explicit state-space forward model: predicted sensory consequence of
self-motion vs. noisy afferent signal, with an impaired update rate
(`forward_model_update_rate = 0.3`, `injury_noise_std = 0.2`) leaving a persistent
mismatch.

> **Honest framing (spec 1.4).** A genuine non-neuro-computational competitor — the
> **Fear-Avoidance Model** (catastrophising and fear-avoidance behaviour, a
> biopsychosocial mechanism) — predicts persistent post-mTBI symptoms at least as
> well, and psychological/social factors are in some studies *stronger* predictors
> than biological ones. akribia implements the forward-model account specifically
> *because that is the account expressible in this engine's math* — not because it
> is the field's settled explanation. The choice of which theory to implement does
> not imply it is the only one.

---

## 5. AuDHD — the comorbid centerpiece

**Plain language.** Autism and ADHD co-occur often, and a recent account argues the
combination is *not* simply additive. Autism's side contributes high, slow-updating
precision (states get "stuck", outlasting their cause — emotional inertia); ADHD's
side contributes unstable gain (rapid, erratic swings). akribia models this as its
own profile, distinct from naively stacking all six levers.

**Deeper.** `audhd_emotion_dysregulation` [@audhd2026] sets `precision_flexibility
= 0.15` (sluggish updating — autism side, *not* low precision, almost the opposite
lever from `autism_weak_prior`) and `rpe_noise_std = 0.5` (unstable gain — ADHD
side, *not* steep discounting). The perturbation-recovery task is the matching
demonstration. **Pre-registered prediction (spec 1.5.1):** autism-side profiles
recover slowly and smoothly (inertia); ADHD-side profiles recover fast but
erratically; `audhd_emotion_dysregulation` is *qualitatively distinct* — slow AND
erratic — not the numeric average. akribia reproduces exactly this: recovery time
≈25 steps (slow, like autism) with high jitter (erratic, like ADHD), landing in its
own quadrant. The generic `comorbid` profile (all six levers) is kept separately as
an *engineering ablation*, reported per-task, never collapsed into one number.

---

## 6. The unifying frame

Predictive coding offers a neurally plausible implementation of Bayesian inference
[@friston2013lawson], and computational psychiatry increasingly conceptualises
disorders as specific alterations in the brain's predictive machinery — the same
handful of parameters (precision, learning rate, discount rate) reproducing
different clinical pictures depending on *where* in the hierarchy and *in which
direction* they are perturbed. That is akribia's thesis, made literal: one
`PrecisionProfile` dataclass, six levers, one engine.

---

## 7. The deepest honesty this project owes: the framework itself has serious critics

This section is deliberately placed *with the theory it critiques*, not buried in
LIMITATIONS.md (spec 1.5.2).

Everything above treats the *application* of precision-weighting to specific
conditions as contested. Beneath that is a sharper charge: the Bayesian brain
hypothesis *itself* has a substantial critical literature questioning whether it is
a real mechanistic theory at all [@bayesianbrain_critique]. The core objections:

1. **Unfalsifiability via free parameters.** With prior distributions, likelihoods,
   and precision weights all free, a Bayesian model can be fit to almost any
   behavioural or neural data *after the fact*.
2. **Immunisation against failure.** When evidence contradicts a Bayesian
   prediction, researchers tend to protect the framework with post-hoc auxiliary
   hypotheses or redefined precision parameters, turning empirical failures into
   theoretical "successes."
3. **Tenuous neural correspondence.** Such models often serve as descriptive tools
   without a clear mapping to identifiable neural mechanisms, making "the brain *is*
   Bayesian" a much stronger claim than the behavioural fit licenses.

**Why this matters concretely for akribia.** The profile system is *structurally
exactly* the "add a parameter, tune it until behaviour matches" machinery the
critique describes. The honest defence is not to argue the critique is wrong — it is
to make akribia falsifiable *on its own terms* by committing to predictions *before*
running experiments and reporting failures as failures:

- The volatility-task prediction (§2) is a *transient* reconvergence delay, not any
  difference-from-baseline. If `autism_overfitting` merely looked different with no
  reconvergence-time signature, that is a failure of the hypothesis as implemented,
  not a cue to add a parameter. (Encoded as `tests/test_predictions.py`.)
- The AuDHD prediction (§5) is a *qualitatively distinct* recovery signature, not
  the average of the two single-mechanism profiles. If the comorbid output *were*
  just the average, that is evidence against the non-additive hypothesis, reported
  as such. (Also encoded as a hard test.)
- The interaction analysis (`multi_task_battery.interaction_analysis`) attaches a
  *number* to "did this match the prediction," so confirmation can't be eyeballed.

A project that cites the literature questioning its own foundational paradigm, and
shows concrete steps taken to avoid that paradigm's documented failure mode, is more
rigorous than one that ignores the critique or spends a sentence on it and moves on.
