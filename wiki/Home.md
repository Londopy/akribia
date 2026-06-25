# akribia Wiki

**One inference engine. Three miscalibrations. Same math.**

akribia implements one predictive-coding / precision-weighting engine with pluggable
"lesion profiles" reproducing literature behaviour for autism, ADHD, and PPCS, plus
a literature-grounded AuDHD comorbidity mode.

| Condition | Where precision miscalibration lives | Core failure mode |
|---|---|---|
| Autism (perceptual) | sensory/perceptual priors, level 1–2 | inflexible precision: persistently high (overfitting) or low (raw-data dominant) |
| ADHD (reward/valuation) | dopaminergic RPE, temporal discounting | discount rate too steep or reward gain unstable |
| PPCS (sensorimotor) | forward-model / efference-copy comparison | post-injury forward model miscalibrated; persistent mismatch |

**Canonical-content split (spec 7):** `docs/THEORY.md` (in the repo) holds the single
tight, citable theory version backed by `docs/references.bib`. This Wiki holds the
plain-language layered expansions and FAQ that don't need to be diffable against code.
One canonical home per piece of content — no duplicated literature reviews.

Pages: [Profile Catalog](./Profile-Catalog.md) · [Math Reference](./Math-Reference.md)
· [Validation Methodology](./Validation-Methodology.md) ·
[Architecture Decisions](./Architecture-Decisions.md) · [FAQ & Limitations](./FAQ-Limitations.md)

> Not a diagnostic tool. See `docs/LIMITATIONS.md`.
