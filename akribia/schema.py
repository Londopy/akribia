"""Shared task-result construction and validation (spec 2.1.1).

Every task in :mod:`akribia.tasks` produces an ``AkribiaTaskResult`` matching
``schemas/task_result.json``. profiles/, viz/, validation/ and the GUI all read
this one shape — one schema, many consumers, zero ad-hoc parsing.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "task_result.json"


def schema_path() -> Path:
    return _SCHEMA_PATH


def load_schema() -> dict[str, Any]:
    with _SCHEMA_PATH.open() as f:
        return json.load(f)


def make_result(
    *,
    profile: Any,
    task: str,
    parameters: dict[str, Any],
    summary: dict[str, Any],
    trajectory: list[dict[str, float]] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Assemble a schema-conformant result dict.

    ``profile`` may be a ``PrecisionProfile`` (its name is used) or a plain string.
    """
    profile_name = getattr(profile, "name", profile)
    params = dict(parameters)
    if is_dataclass(profile) and not isinstance(profile, type):
        # fold the full profile config into parameters for full provenance
        params = {**asdict(profile), **params}
    result: dict[str, Any] = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "profile": profile_name,
        "task": task,
        "parameters": params,
        "trajectory": trajectory or [],
        "summary": summary,
    }
    if seed is not None:
        result["seed"] = int(seed)
    return result


def validate(result: dict[str, Any]) -> None:
    """Validate a result against the JSON Schema. Raises on non-conformance.

    Uses ``jsonschema`` when available; otherwise performs a minimal structural
    check so the package still works in a bare environment.
    """
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover - fallback path
        required = {"timestamp", "profile", "task", "parameters", "trajectory", "summary"}
        missing = required - result.keys()
        if missing:
            raise ValueError(
                f"task result missing required keys: {sorted(missing)}"
            ) from None
        return
    jsonschema.validate(instance=result, schema=load_schema())


def save_result(result: dict[str, Any], path: str | Path) -> Path:
    """Validate and write a result to ``path`` as JSON. Returns the path."""
    validate(result)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(result, f, indent=2)
    return path
