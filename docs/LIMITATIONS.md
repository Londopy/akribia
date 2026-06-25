# Limitations

## Required framing (non-negotiable — spec 5)

> This project is a computational-psychiatry research replication and exploration
> tool. It implements published mathematical models of precision-weighted Bayesian
> inference to illustrate *theoretical mechanisms* proposed in the literature for
> autism, ADHD, and PPCS. **It is not a diagnostic tool, has not been validated
> against patient data, and should not be used to assess, diagnose, or
> characterize any individual's condition** — including the author's. The autism
> precision-weighting literature in particular is actively contested (see
> [THEORY.md §2](./THEORY.md)); this project models competing hypotheses, not
> settled fact.

This is stated twice on purpose (here and in the README), because the field itself
is contested and overclaiming would undercut the project's credibility with anyone
who knows the literature.

## No data collection (spec 2.11)

> akribia runs entirely on synthetic, simulated data. It does not collect, store,
> transmit, or process any personal, behavioral, or health information about its
> users. It is a research and educational tool for exploring published
> computational models — not a self-tracking, screening, or data-collection
> application.

## What "validated" does and does not mean here

- **Per-parameter recovery, honestly reported (spec 2.6).** `discount_factor` and
  `prior_precision_cap` recover cleanly (correlation ≈ 1.0 between ground-truth and
  recovered values). **`precision_flexibility` is weakly identified** (correlation
  ≈ 0.44) — it trades off against the task design and does not recover reliably.
  This is reported as a recovery *table*, not a single headline accuracy number,
  and the CI gate is defined *only* on the parameters that recover reliably. A
  weakly-identified parameter is exactly what the sensitivity sweep predicts:
  flexibility's sweep moves the task metric less sharply than the other levers.
- **Reference comparison, not bit-exact TAPAS reproduction.** The HGF here is an
  HGF-*inspired* volatility-coupled filter, validated against an independent
  reference implementation to a stated tolerance (the two akribia backends agree to
  ~1e-16), not a bit-for-bit reimplementation of the Mathys/TAPAS three-level HGF.
  See the ADR in [architecture.md](./architecture.md).
- **The framework itself is contested.** See [THEORY.md §7](./THEORY.md) — the
  Bayesian brain hypothesis has a serious critical literature, and the profile
  system is structurally the kind of parameter-tuning machinery that critique
  targets. akribia's response is pre-registered predictions encoded as tests, not a
  claim that the critique is wrong.

## Determinism caveat (spec 2.6.1)

Same seed + same code reproduces the same *distribution* and, on the same
machine/architecture, the same exact trajectory. It does **not** guarantee
bit-for-bit identical floating-point results across different CPU architectures
(x86 vs. ARM, different SIMD), because floating-point summation is not associative.
What akribia honestly claims: **reproducible to floating-point tolerance, and
identical on identical hardware** — not unqualified cross-machine bit-exactness.

## Modelling choices that are simplifications

- The arousal/precision state in the perturbation-recovery task is a deliberate
  scalar proxy, not a biophysical model of arousal.
- The illusion task uses a generative model over edge-evidence scalars, not raw
  pixels — by design (a pixel stimulus must not be fed into a Kalman/HGF update;
  see the task docstring).
- Starting parameter values are placeholders that produce *visibly different*
  behaviour; the sensitivity sweeps, not the defaults, are the evidence that the
  model captures a mechanism.

## Not implemented (scoped out, on purpose)

- Bit-exact TAPAS reproduction; the `autism_hippea_fixed` / `_metalearning`
  sub-variant split (documented as an extension in THEORY.md §2).
- Roadmap conditions (schizophrenia, anxiety, depression, addiction) — see the
  README roadmap; the architecture is designed to accept them without restructuring.
