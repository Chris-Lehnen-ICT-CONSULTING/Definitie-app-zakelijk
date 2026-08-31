#!/usr/bin/env python3
"""Deterministic Streamlit UI smoke runner for unattended GAT checks.

Uses Streamlit's bundled AppTest API, so it needs no browser extension,
external browser tab, model call, or additional dependency.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest


def run_once(app_path: str, timeout: float) -> dict[str, object]:
    started = time.monotonic()
    cases: list[dict[str, object]] = []
    app = AppTest.from_file(app_path).run(timeout=timeout)

    exceptions = [str(item.value) for item in app.exception]
    errors = [str(item.value) for item in app.error]
    status = next(
        (
            str(item.value)
            for item in app.success
            if "Systeem Online" in str(item.value)
        ),
        "",
    )
    markdown = [str(item.value) for item in app.markdown]

    cases.append(
        {
            "id": "DEF-527",
            "name": "Context Configuratie exact eenmaal",
            "pass": sum("🎯 Context Configuratie" in item for item in markdown) == 1,
            "observed": {
                "heading_count": sum(
                    "🎯 Context Configuratie" in item for item in markdown
                )
            },
        }
    )
    cases.append(
        {
            "id": "DEF-528",
            "name": "Statusbadge echte regeleinde",
            "pass": bool(status)
            and "\\n" not in status
            and "\n" in status
            and "definities beschikbaar" in status,
            "observed": {"status": status},
        }
    )

    app.radio[0].set_value("expert").run(timeout=timeout)
    review_markdown = [str(item.value) for item in app.markdown]
    review_errors = [*exceptions, *errors]
    queue_text = next(
        (item for item in review_markdown if "wachten op review" in item), ""
    )
    cases.append(
        {
            "id": "DEF-526",
            "name": "Expert Review-wachtrij laadt",
            "pass": (
                not review_errors
                and "### 📋 Review Wachtrij" in review_markdown
                and bool(re.search(r"\d+ definities wachten op review", queue_text))
                and not any(
                    "Kon review queue niet laden" in item or "AttributeError" in item
                    for item in review_errors
                )
            ),
            "observed": {"queue": queue_text, "errors": review_errors},
        }
    )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "app": app_path,
        "duration_seconds": round(time.monotonic() - started, 3),
        "pass": all(bool(case["pass"]) for case in cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="src/main.py")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output", type=Path, help="Append one JSON result per run")
    args = parser.parse_args()
    try:
        result = run_once(args.app, args.timeout)
    except Exception as exc:  # Keep unattended runs machine-readable.
        result = {
            "timestamp": datetime.now(UTC).isoformat(),
            "pass": False,
            "error": repr(exc),
        }
    line = json.dumps(result, ensure_ascii=False)
    print(line)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
