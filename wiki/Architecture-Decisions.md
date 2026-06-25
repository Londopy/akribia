# Architecture Decisions

The full ADR log lives in `docs/architecture.md` §9 (versioned with the code). Summary:

- Rust core + Python orchestration (measured ~5.6× core speedup).
- MIT license; TAPAS GPL compared-against-never-linked (enforced by `cargo deny`).
- Kalman before HGF; HGF-inspired filter validated to tolerance, not bit-exact TAPAS.
- Tauri over Electron (links `core/` directly); React+Vite over Next.js.
- Pure-Python fallback core alongside the Rust extension.
- `akribia/` is the import package (reconciles the spec tree with the CLI contract).
