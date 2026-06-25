"""Sensitivity analysis (spec 2.6) — sweep each profile's key parameter across a
range and show how the task metric changes *continuously*, demonstrating the
model captures a mechanism rather than hardcoding two outputs. Doubles as an
identifiability probe: a parameter whose sweep barely moves the metric will, by
definition, be hard to recover (which is exactly what parameter_recovery finds
for precision_flexibility)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..profiles import BASELINE
from ..tasks import delay_discounting_task, illusion_task, volatility_learning_task


def sweep_prior_precision_cap(n: int = 25) -> dict:
    caps = np.linspace(0.05, 3.0, n)
    scores = []
    for c in caps:
        p = replace(BASELINE, name="_sweep", prior_precision_cap=float(c))
        scores.append(illusion_task.run(p)["summary"]["illusion_score"])
    return {"parameter": "prior_precision_cap", "x": caps.tolist(), "metric": "illusion_score",
            "y": scores}


def sweep_discount_factor(n: int = 25) -> dict:
    gammas = np.linspace(0.5, 0.99, n)
    aucs = []
    for g in gammas:
        p = replace(BASELINE, name="_sweep", discount_factor=float(g))
        aucs.append(delay_discounting_task.run(p)["summary"]["auc_impulsivity"])
    return {"parameter": "discount_factor", "x": gammas.tolist(), "metric": "auc_impulsivity",
            "y": aucs}


def sweep_precision_flexibility(n: int = 20) -> dict:
    flex = np.linspace(0.02, 1.5, n)
    speeds = []
    for f in flex:
        p = replace(BASELINE, name="_sweep", precision_flexibility=float(f))
        speeds.append(volatility_learning_task.run(p)["summary"]["trials_to_reconverge"])
    return {"parameter": "precision_flexibility", "x": flex.tolist(),
            "metric": "trials_to_reconverge", "y": speeds}


def run_all() -> dict:
    return {
        "prior_precision_cap": sweep_prior_precision_cap(),
        "discount_factor": sweep_discount_factor(),
        "precision_flexibility": sweep_precision_flexibility(),
    }


def main() -> None:
    import json
    print(json.dumps(run_all(), indent=2))


if __name__ == "__main__":
    main()
