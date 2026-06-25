//! Kalman update throughput (spec 2.10): updates/sec for the Rust core. The
//! Python comparison lives in benches/py_kalman_bench.py; docs/BENCHMARKS.md
//! holds the side-by-side table.
use akribia_core::kalman::{run, Gaussian, KalmanConfig};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_kalman(c: &mut Criterion) {
    let obs: Vec<f64> = (0..10_000).map(|i| (i as f64 * 0.01).sin()).collect();
    let cfg = KalmanConfig::default();
    c.bench_function("kalman_run_10k", |b| {
        b.iter(|| run(Gaussian::new(0.0, 1.0), black_box(&obs), &cfg).unwrap())
    });
}

criterion_group!(benches, bench_kalman);
criterion_main!(benches);
