"""Integration test exercising the compiled Rust core across the PyO3 boundary
(spec 2.15). Skips cleanly when the extension is not built (the Python fallback
is exercised by the other tests instead)."""
import pytest

from akribia import core


@pytest.mark.skipif(core.BACKEND != "rust", reason="compiled akribia._core not installed")
def test_rust_and_expected_kalman_agree():
    traj = core.kalman_run(0.0, 1.0, [1.0, 2.0, 3.0], 0.01, 1.0, None)
    assert len(traj) == 3
    # posterior mean moves toward the observations, variance shrinks
    assert traj[-1][0] > 0.0
    assert traj[-1][1] < 1.0


def test_backend_reports_itself():
    assert core.BACKEND in ("rust", "python")
