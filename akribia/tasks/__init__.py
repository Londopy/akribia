"""Demo tasks — what makes the math visible/legible (spec 2.5).

Every task exposes ``run(profile, *, seed=...) -> dict`` returning an
``AkribiaTaskResult`` (schemas/task_result.json) and a ``main()`` argparse entry
point so ``python -m akribia.tasks.<task> --profile <name> [--plot]`` works
(spec 0.1 quickstart).
"""

from __future__ import annotations

TASKS = [
    "illusion_task",
    "volatility_learning_task",
    "delay_discounting_task",
    "self_motion_task",
    "perturbation_recovery_task",
    "multi_task_battery",
]
