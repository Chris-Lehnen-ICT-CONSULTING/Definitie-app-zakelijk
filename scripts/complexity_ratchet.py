#!/usr/bin/env python3
"""Complexity ratchet for DefinitieAgent (DEF-418).

`ruff check src/` passes because PLR0911/0912/0915 sit in the global ignore and
C901 is not selected — so CI is blind to complexity debt. Rather than masking it
with ~200 inline ``# noqa`` comments, this script counts the complexity
violations and compares the total against a committed baseline.

- Fails (exit 1) when the count GROWS above the baseline -> "freeze the growth".
- Passes when the count stays equal.
- When the count SHRINKS, it prints how far it dropped and (with ``--update``)
  rewrites the baseline so the ceiling can only ratchet downwards.

The codes counted bypass the project's global ``ignore`` (via an explicit CLI
``--select``) so the real debt is visible here even though ``make lint`` stays
green.

Usage:
    python scripts/complexity_ratchet.py            # check (CI gate)
    python scripts/complexity_ratchet.py --update   # ratchet the baseline down
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Complexity rules deliberately tracked here (globally ignored in pyproject).
COMPLEXITY_CODES = ("C901", "PLR0911", "PLR0912", "PLR0915")
TARGET = "src/"
BASELINE_PATH = Path(__file__).with_name("complexity_baseline.txt")


def count_violations() -> tuple[int, Counter[str]]:
    """Run ruff and return (total, per-code counts) for the complexity codes."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            TARGET,
            "--select",
            ",".join(COMPLEXITY_CODES),
            "--output-format=json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # ruff exit codes: 0 = no violations, 1 = violations found (expected here),
    # >= 2 = ruff itself failed (bad config, invalid rule, crash).
    if result.returncode >= 2:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"complexity_ratchet: ruff failed (exit {result.returncode})")

    try:
        violations = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        sys.stderr.write(result.stdout)
        raise SystemExit(
            f"complexity_ratchet: ruff produced invalid JSON ({exc})"
        ) from exc

    per_code = Counter(v["code"] for v in violations)
    return len(violations), per_code


def read_baseline(path: Path = BASELINE_PATH) -> int:
    """Read the committed baseline count."""
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(
            f"complexity_ratchet: cannot read baseline at {path} ({exc}). "
            "Restore scripts/complexity_baseline.txt to a single integer."
        ) from exc


def write_baseline(value: int, path: Path = BASELINE_PATH) -> None:
    """Persist a new baseline count."""
    path.write_text(f"{value}\n", encoding="utf-8")


def _format_breakdown(per_code: Counter[str]) -> str:
    return ", ".join(f"{code}={per_code.get(code, 0)}" for code in COMPLEXITY_CODES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip().splitlines()[0]
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Lower the baseline to the current count (ratchet down).",
    )
    args = parser.parse_args(argv)

    current, per_code = count_violations()
    baseline = read_baseline()
    breakdown = _format_breakdown(per_code)

    if current > baseline:
        print(
            f"FAIL: complexity violations grew {baseline} -> {current} "
            f"(+{current - baseline}). [{breakdown}]\n"
            "New complex code was added. Refactor it, or — only if truly "
            "unavoidable — raise the baseline deliberately in "
            f"{BASELINE_PATH.name} with a justification."
        )
        return 1

    if current < baseline:
        message = (
            f"Complexity dropped {baseline} -> {current} (-{baseline - current}). "
            f"[{breakdown}]"
        )
        if args.update:
            write_baseline(current)
            print(f"{message}\nBaseline ratcheted down to {current}.")
        else:
            print(
                f"{message}\nRun 'python scripts/complexity_ratchet.py --update' "
                "to lock in the improvement."
            )
        return 0

    print(f"OK: complexity at baseline ({current}). [{breakdown}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
