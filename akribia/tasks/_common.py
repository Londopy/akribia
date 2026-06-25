"""Shared task plumbing: a uniform CLI and a results directory helper."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from .. import profiles
from ..schema import save_result

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"


def results_path(task: str, profile_name: str) -> Path:
    return RESULTS_DIR / f"{task}__{profile_name}.run.json"


def standard_cli(
    task_name: str,
    run_fn: Callable[..., dict],
    plot_fn: Callable[[dict], object] | None = None,
) -> None:
    """A consistent ``--profile/--seed/--plot/--out`` CLI for every task."""
    parser = argparse.ArgumentParser(prog=f"akribia.tasks.{task_name}")
    parser.add_argument(
        "--profile",
        default="baseline",
        choices=profiles.names(),
        help="precision profile to run (default: baseline)",
    )
    parser.add_argument("--seed", type=int, default=None, help="override deterministic seed")
    parser.add_argument("--plot", action="store_true", help="render the comparison plot")
    parser.add_argument("--out", default=None, help="path to write the JSON result")
    parser.add_argument(
        "--no-save", action="store_true", help="do not write a JSON result file"
    )
    args = parser.parse_args()

    profile = profiles.get(args.profile)
    kwargs = {} if args.seed is None else {"seed": args.seed}
    result = run_fn(profile, **kwargs)

    print(json.dumps(result["summary"], indent=2))

    if not args.no_save:
        out = Path(args.out) if args.out else results_path(task_name, args.profile)
        save_result(result, out)
        print(f"\nwrote {out}")

    if args.plot:
        if plot_fn is None:
            print("(no plot available for this task)")
        else:
            fig = plot_fn(result)
            try:
                import matplotlib.pyplot as plt  # noqa: F401

                out_png = (args.out and Path(args.out).with_suffix(".png")) or (
                    RESULTS_DIR / f"{task_name}__{args.profile}.png"
                )
                out_png.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(out_png, dpi=130, bbox_inches="tight")
                print(f"wrote {out_png}")
            except Exception as exc:  # pragma: no cover
                print(f"(plotting skipped: {exc})")
