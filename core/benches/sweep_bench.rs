//! HGF parameter-sweep wall-clock (spec 2.10) — the realistic workload where the
//! Rust/Python gap actually matters, more representative than a single update.
use akribia_core::hgf::{run, HgfConfig, HgfState};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_sweep(c: &mut Criterion) {
    let obs: Vec<f64> = (0..1_000)
        .map(|i| if i < 500 { 0.0 } else { 10.0 })
        .collect();
    // 50-point sweep over precision_flexibility, mirroring validation/sensitivity.
    c.bench_function("hgf_sweep_50x1000", |b| {
        b.iter(|| {
            for k in 0..50 {
                let flex = 0.02 + (k as f64) * 0.04;
                let cfg = HgfConfig {
                    precision_flexibility: flex,
                    ..Default::default()
                };
                let _ = run(HgfState::new(0.0, 1.0, 0.0, 1.0), black_box(&obs), &cfg).unwrap();
            }
        })
    });
}

criterion_group!(benches, bench_sweep);
criterion_main!(benches);
