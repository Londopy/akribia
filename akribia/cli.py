"""``akribia`` console entry point (configured in pyproject [project.scripts]).

Thin dispatcher over the task and validation modules so the package is usable as a
single command in addition to ``python -m akribia.tasks.<task>``.
"""

from __future__ import annotations

import argparse

from . import __version__, core, profiles
from .tasks import TASKS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="akribia", description=__doc__)
    parser.add_argument("--version", action="version", version=f"akribia {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("info", help="show backend and profile catalog")

    run_p = sub.add_parser("run", help="run a task under a profile")
    run_p.add_argument("task", choices=TASKS)
    run_p.add_argument("--profile", default="baseline", choices=profiles.names())
    run_p.add_argument("--plot", action="store_true")

    sub.add_parser("recover", help="run the per-parameter recovery suite")
    sub.add_parser("validate", help="run the reference-oracle comparison")

    args = parser.parse_args(argv)

    if args.command == "info" or args.command is None:
        print(f"akribia {__version__}")
        print(f"backend: {core.BACKEND}")
        print("profiles:")
        for name in profiles.names():
            ov = profiles.get(name).overrides()
            print(f"  - {name}: {ov or 'defaults'}")
        return 0

    if args.command == "run":
        import importlib

        mod = importlib.import_module(f"akribia.tasks.{args.task}")
        result = mod.run(profiles.get(args.profile))
        import json

        print(json.dumps(result["summary"], indent=2, default=str))
        if args.plot and hasattr(mod, "plot"):
            mod.plot(result)
            print("(plot rendered; use the task module's --plot to save a PNG)")
        return 0

    if args.command == "recover":
        import json

        from .validation.parameter_recovery import run_suite

        print(json.dumps(run_suite(), indent=2))
        return 0

    if args.command == "validate":
        import json

        from .validation.against_hgf_toolbox import run_suite

        print(json.dumps(run_suite(), indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
