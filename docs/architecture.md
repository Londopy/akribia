# Architecture

This file explains *why* the repo looks the way it does, as opposed to the Wiki /
THEORY.md (which explain the *theory* it implements). Written to be read by a
future contributor — or future author — six months removed from the context.

## 1. System overview

```
                 ┌──────────────────────────────────────────────┐
                 │              core/  (Rust crate)             │
   speed-        │  kalman.rs · hgf.rs · td_learning.rs ·       │
   critical      │  forward_model.rs · error.rs                 │
   math          └───────────────┬───────────────┬──────────────┘
                                  │ PyO3          │ rlib (direct link)
                 ┌────────────────▼───┐   ┌───────▼───────────────┐
                 │  akribia/ (Python) │   │  gui/src-tauri (Rust) │
                 │  core loader →     │   │  Tauri commands call  │
                 │  _core or fallback │   │  core/ directly       │
                 │  profiles/ tasks/  │   └───────────────────────┘
                 │  viz/ validation/  │
                 └─────────┬──────────┘
                           │ every task emits schemas/task_result.json
        ┌──────────────────┼───────────────────┐
        ▼                  ▼                   ▼
   viz/ (plots)     validation/ (recovery)   GUI (display only)
```

The Python layer is the *research* surface (notebooks, sweeps, CI-enforced
validation). The GUI is a *presentation* surface that links the same Rust crate
directly. Neither reimplements the other's job.

## 2. Why Rust core + Python orchestration (spec 2.2)

The core filtering math (Kalman/HGF update) is a tight numerical loop — a good Rust
use case, with no GC pauses, meaningfully faster for the parameter-sweep and
recovery workloads. Python (numpy/scipy/matplotlib/Jupyter) is the right layer for
visualisation, notebooks, and gluing tasks together. Benchmarks (see
[BENCHMARKS.md](./BENCHMARKS.md)) quantify the gap rather than asserting it: the
pure-Rust Kalman core is ~5.6× faster than a pure-Python equivalent on the
boundary-free hot loop.

## 3. The profile abstraction (spec 2.4)

One frozen `PrecisionProfile` dataclass, six levers, used by every condition. The
engine never knows which condition it runs — only which numbers to use. This is the
thesis ("same math, different miscalibration") made true at the *code* level, not
just conceptually. There is no per-condition code path.

## 4. Deterministic seeding policy (spec 2.6.1)

- Pass an explicit seed (or seed-derived RNG state) through every function boundary
  that touches randomness — never ambient/global RNG on either side of the PyO3
  boundary (Rust's ChaCha8 and NumPy's PRNG do not share state).
- `akribia.seeding.derive_seed` fans one master seed out into stable, collision-
  resistant per-(profile, task, replicate) sub-seeds via SHA-256, so a whole battery
  is reproducible from one integer.
- Store the seed used for every benchmark/validation run alongside its results.
- **Honest limit:** same seed + same code reproduces the same distribution and, on
  identical hardware, the same exact trajectory — but *not* bit-for-bit across CPU
  architectures (FP summation is not associative). See LIMITATIONS.md.

## 5. Third-party licensing boundaries (spec 1.7)

- **TAPAS is GPL — compared against, never linked or copied from.** Running TAPAS
  separately and diffing its numeric output against akribia's own independently-
  implemented HGF is fine. Copying, adapting, or linking any TAPAS code into the
  MIT-licensed `core/` crate would obligate the combined work under GPL and
  silently invalidate the MIT decision. This boundary is enforced by *never
  depending on TAPAS in code*: `validation/against_hgf_toolbox.py` only talks to
  akribia's own backends and self-contained references.
- PyHGF / pymdp (MIT/BSD-ish) would be safe to depend on directly if used; verify
  each license rather than assuming.
- `cargo deny check` in CI (spec 2.16) also fails the build if any transitive
  dependency ever pulls in a GPL license, catching an accidental violation.

## 6. Error handling and logging convention (spec 2.13)

- **Rust core:** every fallible function returns `Result<T, AkribiaError>` with a
  proper enum (`InvalidParameter`, `SingularMatrix`, `NumericalDivergence`,
  `DimensionMismatch`). Panics are reserved for genuine programmer-error invariant
  violations, not expected failures like bad user parameters.
- **PyO3 boundary:** each variant maps to a specific Python exception
  (`akribia._core.InvalidParameter`, …) so callers catch failure modes instead of
  parsing strings. The Python fallback mirrors the same exception hierarchy.
- **GUI:** Tauri commands surface these as structured errors the frontend renders as
  toast notifications with the specific reason visible.
- **Logging:** `tracing` (Rust) + Python `logging` configured to a matching format,
  so a failure three hours into an overnight sweep is traceable to the exact
  profile/task/parameter combination.

## 7. GUI integration boundary (spec 11.3)

The GUI calls `core/` directly via Tauri commands (same crate, no PyO3, no
serialisation overhead). It does **not** reimplement validation/recovery — if it
ever surfaces validation results it reads the artifact `validation.yml` already
produces. Display, don't recompute.

## 8. Lockfiles, toolchain pinning, layout

- `Cargo.lock`, `package-lock.json` are **committed** (this ships binaries, so
  pinned reproducible deps are exactly what we want).
- `rust-toolchain.toml` (1.78.0) and `.python-version` (3.11) are committed and must
  match the devcontainer Dockerfile.
- Dependency versions are pinned where Rust 1.78 compatibility requires it (clap,
  half, rayon, tempfile, proptest); see `Cargo.lock`.

## 9. Architecture Decision Records (ADR log)

> Written as decisions, not as a transcript. *Decision → Rationale.*

- **ADR-001 — Rust core + Python orchestration.** Rationale: hot-loop math wants a
  compiled, GC-free language; viz/notebooks want Python. Demonstrated by a measured
  ~5.6× core speedup, not asserted.
- **ADR-002 — MIT license (not AGPL).** Rationale: maximise reuse for a portfolio/
  research tool; the TAPAS GPL boundary (ADR-005) is kept clean so MIT stays valid.
- **ADR-003 — Kalman before HGF.** Rationale: the precision-weighted Kalman update is
  the simplest correct version of the whole thesis; get it right, then add the
  volatility layer as a variant.
- **ADR-004 — HGF: implement an HGF-*inspired* volatility-coupled filter in Rust,
  validated against a reference oracle to tolerance (path b-lite), rather than
  bit-exact TAPAS reproduction or a hard PyHGF dependency.** Rationale: the
  qualitative volatility dynamics are what the thesis needs; bit-exact TAPAS matching
  is weeks of work for little additional portfolio value, and PyHGF/TAPAS remain the
  external reference oracle.
- **ADR-005 — TAPAS compared-against, never linked.** Rationale: GPL/MIT boundary
  (see §5). Enforced by `cargo deny` and by never importing it.
- **ADR-006 — Tauri over Electron.** Rationale: Tauri's Rust backend links `core/`
  directly; Electron would mean reimplementing the math in JS or shelling out to a
  Python sidecar — strictly worse fits. Also ~3–10 MB binaries vs. 100 MB+.
- **ADR-007 — React + Vite over Next.js.** Rationale: no server inside a desktop
  shell; SSR/API-routes/file-routing add build complexity for zero benefit.
- **ADR-008 — Pure-Python fallback core alongside the Rust extension.** Rationale:
  the project must be runnable and verifiable without a Rust toolchain; the fallback
  mirrors the deterministic math and is checked against the Rust core to ~1e-16. The
  active backend is reported by `akribia.core.BACKEND`.
- **ADR-009 — `akribia/` is the Python import package containing profiles/, tasks/,
  viz/, validation/.** Rationale: the spec's architecture tree lists those at the
  repo root, but the §0.1 quickstart invokes `python -m akribia.tasks.illusion_task`,
  which requires an importable `akribia` package. Making `akribia/` the package
  reconciles the two; the Rust crate stays in `core/` and compiles into
  `akribia._core`. (A documented reconciliation of two slightly inconsistent parts of
  the spec, not an oversight.)
- **ADR-010 — `gui/src-tauri` is a *separate* workspace, not a root member.**
  Rationale: the root workspace pins Rust 1.78 (spec) to keep the numerical core's
  reproducibility guarantee, but Tauri 2's dependency tree needs a newer toolchain.
  A separate workspace lets the GUI build under current stable (`gui.yml`) while
  still linking `core/` directly via a path dependency — so "the GUI calls core/
  directly" (spec 11.1) holds regardless of workspace membership. This is a
  documented resolution of a genuine spec-internal tension (pin 1.78 AND use
  Tauri 2), not a drift from intent.
