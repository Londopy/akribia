# Validation Methodology

(Expands `docs/LIMITATIONS.md` and spec 2.6.)

**Parameter recovery, per parameter.** Simulate data with known ground-truth
parameters, fit by grid search, report recovery *per parameter* across ≥20 seeds —
never one global accuracy number.

| Parameter | Recovers? | Correlation (true vs recovered) |
|---|---|---|
| `discount_factor` | ✅ reliably | ≈ 1.0 |
| `prior_precision_cap` | ✅ reliably | ≈ 1.0 |
| `precision_flexibility` | ⚠️ weakly identified | ≈ 0.44 |

The CI gate (`validation.yml`) passes only on the reliably-recoverable parameters,
so it tracks something real. A weakly-identified parameter is exactly what the
sensitivity sweep predicts (its sweep moves the task metric least sharply).

**Reference oracle.** Two independent implementations of the same math (Rust core +
Python reference) agree to ~1e-16. TAPAS is the *external* oracle: compared against,
never linked (GPL/MIT boundary).

**"Passing" means:** reproducible to floating-point tolerance, identical on identical
hardware — not unqualified bit-exactness across CPU architectures.
