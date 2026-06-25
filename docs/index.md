# akribia — API reference

Generated from docstrings in the `akribia` package (spec 2.12). Build locally with:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

For the **theory & literature**, see the [Wiki](../wiki/Home.md) and
[THEORY.md](./THEORY.md). For the **Rust core** API, run `cargo doc --open -p akribia-core`.

## Modules

- `akribia.core` — backend loader (Rust `_core` or Python fallback).
- `akribia.profiles` — the `PrecisionProfile` catalog.
- `akribia.tasks` — the six demo tasks.
- `akribia.viz` — colorblind-safe plotting.
- `akribia.validation` — per-parameter recovery, reference-oracle comparison, sweeps.
