# Security Policy

akribia is a local research/educational tool that runs entirely on synthetic data
(see the no-data-collection statement in [docs/LIMITATIONS.md](./docs/LIMITATIONS.md)).
Its real risk surface is low, but a clear disclosure policy is part of the project's
intent.

## Supported versions

The latest tagged release on `main` is supported.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via GitHub's **Report a
vulnerability** (Security Advisories) on the repository, rather than opening a public
issue. Expected first response: within 7 days. Please include reproduction steps and
the affected version/commit.

## Supply-chain posture (spec 2.16)

- Dependencies are monitored by Dependabot (`.github/dependabot.yml`) across cargo,
  pip, and npm.
- CI runs active audit gates: `cargo audit` / `cargo deny`, `pip-audit`,
  `npm audit` — these *fail the build*, they are not just notifications.
- Releases ship a `SHA256SUMS.txt` for integrity verification; commits and tags are
  SSH-signed; `main` is branch-protected to require signed commits and green CI.
- Publish tokens (PyPI/crates.io/npm) are GitHub environment secrets, minimally
  scoped, behind a required-reviewer approval on the publish job.
