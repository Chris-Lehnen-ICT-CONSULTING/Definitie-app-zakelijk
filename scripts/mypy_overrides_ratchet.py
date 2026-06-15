#!/usr/bin/env python3
"""Mypy per-module override ratchet for DefinitieAgent (DEF-431, Fase 2).

Counts the legacy modules that are exempted from ``disallow_untyped_defs`` via
``[[tool.mypy.overrides]]`` in ``pyproject.toml`` and compares that count to a
committed baseline. Fails (exit 1) when the list GROWS — that would mean a new
untyped module was grandfathered in to dodge the global ``disallow_untyped_defs``
gate. ``--update`` ratchets the baseline DOWN when a package-PR annotates modules
and removes them from the list.

This is the shrinking debt-teller for the mypy strictness inversion: the existing
mypy error-count ratchet (``mypy_ratchet.py``) blocks new untyped code in
non-legacy files; this script blocks the escape hatch of adding files to the
override list.

Usage:
    python scripts/mypy_overrides_ratchet.py            # check (CI gate)
    python scripts/mypy_overrides_ratchet.py --update   # ratchet the baseline down
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"
BASELINE_PATH = Path(__file__).with_name("mypy_overrides_baseline.txt")


def count_overrides(pyproject: Path = PYPROJECT_PATH) -> int:
    """Return the number of modules exempted from disallow_untyped_defs.

    Sums the ``module`` entries of every ``[[tool.mypy.overrides]]`` block that
    sets ``disallow_untyped_defs = false``.
    """
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    overrides = data.get("tool", {}).get("mypy", {}).get("overrides", [])
    total = 0
    for block in overrides:
        if block.get("disallow_untyped_defs") is False:
            module = block.get("module", [])
            total += len(module) if isinstance(module, list) else 1
    return total


def read_baseline(path: Path = BASELINE_PATH) -> int:
    """Read the committed baseline count."""
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(
            f"mypy_overrides_ratchet: cannot read baseline at {path} ({exc}). "
            "Restore scripts/mypy_overrides_baseline.txt to a single integer."
        ) from exc


def write_baseline(value: int, path: Path = BASELINE_PATH) -> None:
    """Persist a new baseline count."""
    path.write_text(f"{value}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip().splitlines()[0]
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Lower the baseline to the current override count (ratchet down).",
    )
    args = parser.parse_args(argv)

    current = count_overrides()
    baseline = read_baseline()

    if current > baseline:
        print(
            f"FAIL: mypy override list grew {baseline} -> {current} "
            f"(+{current - baseline}). A module was grandfathered out of "
            "disallow_untyped_defs. Annotate the module instead of adding it to "
            "the [[tool.mypy.overrides]] list."
        )
        return 1

    if current < baseline:
        message = (
            f"mypy overrides dropped {baseline} -> {current} "
            f"(-{baseline - current})."
        )
        if args.update:
            write_baseline(current)
            print(f"{message}\nBaseline ratcheted down to {current}.")
        else:
            print(
                f"{message}\nRun 'python scripts/mypy_overrides_ratchet.py "
                "--update' to lock in the improvement."
            )
        return 0

    print(f"OK: mypy override list at baseline ({current}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
