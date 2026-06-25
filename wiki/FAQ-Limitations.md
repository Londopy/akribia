# FAQ & Limitations

**Is this clinically validated?** No. It implements published *theoretical* models on
synthetic data. It is not a diagnostic tool and has not been validated against patient
data. See `docs/LIMITATIONS.md`.

**Doesn't this overstate how settled the autism literature is?** No — that's the point
of the design. The competing accounts (weak priors vs. HIPPEA) are switchable profiles,
not settled fact, and a 2020 systematic review found highly mixed evidence. See
`docs/THEORY.md` §2.

**Isn't the Bayesian brain hypothesis itself contested?** Yes, and akribia says so
prominently (`docs/THEORY.md` §7). The profile system is structurally the kind of
parameter-tuning the critique targets; the response is pre-registered predictions
encoded as tests (`tests/test_predictions.py`), not a claim the critique is wrong.

**Why model PPCS with a forward model and not the Fear-Avoidance Model?** Because the
forward-model account is the one expressible in this engine's math — not because it is
the field's settled explanation over FAM. See `docs/THEORY.md` §4.

**Does it collect any data about me?** No. It runs entirely on synthetic, simulated
data and stores/transmits nothing. See the no-data statement in `docs/LIMITATIONS.md`.

**Can I run it without Rust?** Yes — it falls back to a pure-Python core
(`akribia.core.BACKEND == "python"`), validated against the Rust core to ~1e-16.
