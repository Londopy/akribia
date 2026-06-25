# Contributing

Thanks for your interest. This is a research/portfolio project; contributions that
keep it rigorous are welcome.

## Dev environment

One command — open the repo in VS Code Dev Containers / GitHub Codespaces and the
[devcontainer](./.devcontainer) builds the Rust+Python toolchain and runs
`maturin develop` automatically. Outside a container:

```bash
maturin develop                 # builds akribia._core and installs the package
pip install -e ".[dev]"         # dev tooling (pytest, ruff, mypy, hypothesis)
pre-commit install              # run the same checks CI runs, before every commit
```

No Rust toolchain? The package still runs — it falls back to the pure-Python core
(`akribia.core.BACKEND == "python"`).

## Adding a new profile (the main extension point — spec 2.4)

1. Add `akribia/profiles/<condition>_<mechanism>.py` defining one
   `PrecisionProfile` instance (override only the levers your account implicates).
2. Register it in `akribia/profiles/__init__.py`'s `CATALOG`.
3. Add a literature-grounded entry to `docs/THEORY.md` and a citation to
   `docs/references.bib` — a profile without a literature basis won't be merged.
4. Add/extend a task that makes its predicted behaviour visible, with a
   pre-registered prediction encoded in `tests/test_predictions.py`.
5. Bump `MINOR` in `CHANGELOG.md` (the profile catalog is public API).

## Adding a new task

Add `akribia/tasks/<task>.py` exposing `run(profile, *, seed=None) -> dict` (emit
the `schemas/task_result.json` shape via `akribia.schema.make_result`) and a
`main()` via `akribia.tasks._common.standard_cli`. Add a schema-conformance test.

## PRs that touch `core/`

Re-run validation: `python -m akribia.validation.parameter_recovery` and
`python -m akribia.validation.against_hgf_toolbox`. CI (`validation.yml`) enforces
the recovery gate on the reliably-recoverable parameters.

## Questions

Found a bug or have a question? Open an issue.
