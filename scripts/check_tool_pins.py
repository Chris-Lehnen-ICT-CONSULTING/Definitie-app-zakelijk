#!/usr/bin/env python3
"""Tool-pin consistency guard (DEF-430, DEF-442).

ruff and black are each declared in two places; if they drift the
complexity/format baselines silently become wrong. This asserts they are
identical across all sources. Pure file parsing — no tools installed, fully
deterministic, so it runs in the unit suite AND as a dedicated CI gate
(quality-gates.yml) so it cannot be skipped by profile-based test selection.

Sources (DEF-442: the workflow no longer hardcodes versions — both the mypy- and
complexity-ratchet jobs derive their pin from requirements-dev.txt, so it is the
single source of truth and is not cross-checked here):
- ruff:  requirements-dev.txt (``ruff==``), .pre-commit-config.yaml (``rev:``)
- black: requirements-dev.txt (``black==``), .pre-commit-config.yaml (``rev:``)
         — the pre-commit rev is the format authority and must match the pinned
         dev version (DEF-432).
- mypy:  requirements-dev.txt (``mypy==``) only — single source, nothing to
         cross-check; the baseline measurement is tied to this pin.

Usage:
    python scripts/check_tool_pins.py
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
REQ_DEV = _ROOT / "requirements-dev.txt"
PRE_COMMIT = _ROOT / ".pre-commit-config.yaml"


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
    }


def mypy_versions() -> dict[str, str]:
    # DEF-442: single source — the workflow derives its mypy pin from this file.
    return {
        "requirements-dev.txt": _extract(
            r"^mypy==(\S+)",
            REQ_DEV.read_text(encoding="utf-8"),
            "mypy in requirements-dev",
            re.MULTILINE,
        ),
    }


def black_versions() -> dict[str, str]:
    return {
        "requirements-dev.txt": _extract(
            r"^black==(\S+)",
            REQ_DEV.read_text(encoding="utf-8"),
            "black in requirements-dev",
            re.MULTILINE,
        ),
        ".pre-commit-config.yaml": _extract(
            r"github\.com/psf/black\b.*?rev:\s*(\S+)",
            PRE_COMMIT.read_text(encoding="utf-8"),
            "black rev in .pre-commit-config.yaml",
            re.DOTALL,
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
        for tool, versions in (
            ("ruff", ruff_versions()),
            ("mypy", mypy_versions()),
            ("black", black_versions()),
        )
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
    black = next(iter(black_versions().values()))
    print(
        f"OK: ruff=={ruff}, mypy=={mypy} and black=={black} "
        "consistent across all sources."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
