#!/usr/bin/env python3
"""Mypy error-count ratchet for DefinitieAgent (DEF-419).

Runs `mypy src/ --check-untyped-defs` and compares the error count against a
committed baseline. Fails (exit 1) when the count GROWS ("freeze the growth",
Fase 1); --update ratchets the baseline down when the count shrinks.

The `--check-untyped-defs` flag is passed explicitly so the project-wide
pyproject config — and the existing `mypy src/services` gate — stays untouched.

Usage:
    python scripts/mypy_ratchet.py            # check (CI gate)
    python scripts/mypy_ratchet.py --update   # ratchet the baseline down
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MYPY_ARGS = ("src/", "--check-untyped-defs")
# DEF-569: the KRITIEK AI-validatie-engine subtree. Its per-subtree zero-floor
# used to be a standalone `mypy src/services` gate in test.yml (removed in
# DEF-568 as redundant while the global baseline is 0). This ratchet re-asserts
# it whenever the global baseline is raised above 0 — see main().
SERVICES_ARGS = ("src/services", "--check-untyped-defs")
BASELINE_PATH = Path(__file__).with_name("mypy_baseline.txt")
# Anchored on the mypy summary line ("Found N errors in M files ...") at line
# start so a diagnostic line that happens to contain "Found N error" cannot match.
_FOUND_RE = re.compile(r"^Found (\d+) errors? in \d+ files?", re.MULTILINE)
_SUCCESS_RE = re.compile(r"Success: no issues found")


def count_errors(args: tuple[str, ...] = MYPY_ARGS) -> int:
    """Run mypy over `args` and return the total error count from its summary line."""
    result = subprocess.run(
        [sys.executable, "-m", "mypy", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    out = result.stdout
    if _SUCCESS_RE.search(out):
        return 0
    match = _FOUND_RE.search(out)
    if not match:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(
            f"mypy_ratchet: could not parse mypy output (exit {result.returncode})"
        )
    return int(match.group(1))


def read_baseline(path: Path = BASELINE_PATH) -> int:
    """Read the committed baseline count."""
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(
            f"mypy_ratchet: cannot read baseline at {path} ({exc}). "
            "Restore scripts/mypy_baseline.txt to a single integer."
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
        help="Lower the baseline to the current count (ratchet down).",
    )
    args = parser.parse_args(argv)

    current = count_errors()
    baseline = read_baseline()

    # DEF-569: the baseline is a GLOBAL count over src/ — it does not partition
    # per subtree. While baseline == 0 the whole tree (incl. the KRITIEK
    # src/services AI-engine) is guaranteed clean, so this guard is skipped (no
    # extra mypy run — keeps the perf win from DEF-568). But once the baseline is
    # deliberately raised above 0, errors could accumulate anywhere — including
    # src/services — without failing the aggregate check. Re-assert the
    # zero-tolerance floor on that critical subtree whenever baseline > 0.
    if baseline > 0:
        services_errors = count_errors(SERVICES_ARGS)
        if services_errors > 0:
            print(
                f"FAIL: {services_errors} mypy error(s) in src/services while the "
                f"global baseline is {baseline} (>0). The critical AI-validation "
                "subtree must stay mypy-clean even when the global baseline is "
                "raised. Fix the src/services errors before raising the baseline."
            )
            return 1

    if current > baseline:
        print(
            f"FAIL: mypy errors grew {baseline} -> {current} (+{current - baseline}). "
            "Add type annotations to the code you touched, or — only if truly "
            "unavoidable — raise the baseline deliberately with a justification."
        )
        return 1

    if current < baseline:
        message = (
            f"mypy errors dropped {baseline} -> {current} (-{baseline - current})."
        )
        if args.update:
            write_baseline(current)
            print(f"{message}\nBaseline ratcheted down to {current}.")
        else:
            print(
                f"{message}\nRun 'python scripts/mypy_ratchet.py --update' "
                "to lock in the improvement."
            )
        return 0

    print(f"OK: mypy at baseline ({current}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
