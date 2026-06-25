"""Every task emits a result conforming to schemas/task_result.json (spec 2.1.1)."""
import pytest

from akribia import profiles
from akribia.schema import validate
from akribia.tasks import (
    delay_discounting_task,
    illusion_task,
    perturbation_recovery_task,
    self_motion_task,
    volatility_learning_task,
)

TASK_MODULES = [
    illusion_task, volatility_learning_task, delay_discounting_task,
    self_motion_task, perturbation_recovery_task,
]


@pytest.mark.parametrize("mod", TASK_MODULES, ids=lambda m: m.TASK)
@pytest.mark.parametrize("pname", ["baseline", "comorbid"])
def test_task_output_conforms_to_schema(mod, pname):
    result = mod.run(profiles.get(pname))
    validate(result)  # raises on non-conformance
    assert result["profile"] == pname
    assert result["task"] == mod.TASK
    assert "summary" in result and isinstance(result["summary"], dict)


@pytest.mark.parametrize("mod", TASK_MODULES, ids=lambda m: m.TASK)
def test_every_run_records_a_seed(mod):
    # Deterministic seeding policy (spec 2.6.1): every run carries its seed.
    assert "seed" in mod.run(profiles.get("baseline"))
