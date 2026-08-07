# Review environment

- Captured at (UTC): `2026-08-07T08:26:23Z`
- macOS: `26.6` (`25G72`)
- Python: `3.13.8`
- pip: `25.3`
- pytest: `9.0.3`
- Ruff: `0.15.17`
- mypy: `1.18.2`
- Dependency environment: existing project virtualenv at `/Users/chrislehnen/Projecten/Definitie-app/.venv`

## Clean-worktree baseline

- `make ... test-markers-check`: PASS — all 317 collected test files have classification markers.
- `pytest -q -m "unit and not slow" --maxfail=1`: PASS (exit code 0).
- Baseline warnings include unclosed SQLite connections and never-awaited coroutines. These are evidence to classify during the detailed review, not silently ignored.

The virtualenv is invoked through its absolute interpreter path so no dependency installation or environment mutation is needed in the isolated worktree.
