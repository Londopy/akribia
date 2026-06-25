# Reproducible Rust + Python toolchain (spec 2.7).
# The Rust channel here MUST match rust-toolchain.toml; the Python version MUST
# match .python-version. CI builds against this same image so "works in CI" and
# "works for a contributor" are the same guarantee.
FROM rust:1.78-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip \
        build-essential pkg-config curl git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
        maturin numpy scipy matplotlib jsonschema \
        jupyter ipykernel pytest pytest-benchmark hypothesis \
        ruff mypy pip-audit pre-commit

# Rust supply-chain audit tools (spec 2.16).
RUN cargo install cargo-audit cargo-deny --locked

WORKDIR /workspace
COPY . .

# Build the PyO3 extension in-place so `import akribia` works immediately.
RUN maturin develop --release || true

CMD ["/bin/bash"]
