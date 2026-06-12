#!/usr/bin/env python3
"""Tool-pin consistency guard (DEF-430).

The ruff version is declared in three places and mypy in two; if they drift the
complexity/mypy ratchet baselines silently become wrong. This asserts they are
identical across all sources. Pure file parsing — no tools installed, fully
deterministic, so it runs in the unit suite.

Sources:
- ruff:  requirements-dev.txt (``ruff==``), .pre-commit-config.yaml (``rev:``),
         .github/workflows/quality-gates.yml (``pip install ruff==``)
- mypy:  requirements-dev.txt (``mypy==``),
         .github/workflows/quality-gates.yml (``pip install mypy==``)

Usage:
    python scripts/check_tool_pins.py
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
REQ_DEV = _ROOT / "requirements-dev.txt"
PRE_COMMIT = _ROOT / ".pre-commit-config.yaml"
QUALITY_GATES = _ROOT / ".github" / "workflows" / "quality-gates.yml"


def _extract(pattern: str, text: str, label: str, flags: int = 0) -> str:
    """Return the first capture group, stripped of a leading ``v``."""
    match = re.search(pattern, text, flags)
    if not match:
        raise SystemExit(f"check_tool_pins: could not find {label}")
    return match.group(1).lstrip("v")


def ruff_versions() -> dict[str, str]:
    return {
        "requirements-dev.txt": _extract(
            r"^ruff==(\S+)",
            REQ_DEV.read_text(encoding="utf-8"),
            "ruff in requirements-dev",
            re.MULTILINE,
        ),
        ".pre-commit-config.yaml": _extract(
            r"ruff-pre-commit.*?rev:\s*(\S+)",
            PRE_COMMIT.read_text(encoding="utf-8"),
            "ruff rev in .pre-commit-config.yaml",
            re.DOTALL,
        ),
        "quality-gates.yml": _extract(
            r"pip install ruff==(\S+)",
            QUALITY_GATES.read_text(encoding="utf-8"),
            "ruff in quality-gates.yml",
        ),
    }


def mypy_versions() -> dict[str, str]:
    return {
        "requirements-dev.txt": _extract(
            r"^mypy==(\S+)",
            REQ_DEV.read_text(encoding="utf-8"),
            "mypy in requirements-dev",
            re.MULTILINE,
        ),
        "quality-gates.yml": _extract(
            r"pip install mypy==(\S+)",
            QUALITY_GATES.read_text(encoding="utf-8"),
            "mypy in quality-gates.yml",
        ),
    }


def inconsistency(tool: str, versions: dict[str, str]) -> str | None:
    """Return an error message if the versions disagree, else None."""
    if len(set(versions.values())) > 1:
        detail = ", ".join(f"{src}={ver}" for src, ver in versions.items())
        return f"{tool} version mismatch across sources: {detail}"
    return None


def main() -> int:
    errors = [
        msg
        for tool, versions in (("ruff", ruff_versions()), ("mypy", mypy_versions()))
        if (msg := inconsistency(tool, versions))
    ]
    if errors:
        print("FAIL: tool pins are out of sync.")
        for msg in errors:
            print(f"  - {msg}")
        print("Bump every source to the same version (see DEF-430 comments).")
        return 1

    ruff = next(iter(ruff_versions().values()))
    mypy = next(iter(mypy_versions().values()))
    print(f"OK: ruff=={ruff} and mypy=={mypy} consistent across all sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
