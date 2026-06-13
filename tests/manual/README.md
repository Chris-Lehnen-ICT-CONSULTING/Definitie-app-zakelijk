# tests/manual

Handmatige diagnostische scripts — **buiten de geautomatiseerde test-suite**.

Deze map is uitgesloten van pytest-collectie (`norecursedirs = ... manual` in
`pytest.ini`) en van de markers-guard (`EXCLUDED_DIRS` in
`scripts/testing/_marker_utils.py`). Niets hier draait mee in `make test`,
`make test-integration` of de coverage-gate.

## Waarom

De scripts zijn print-zware diagnose-runners met een `if __name__ == "__main__"`-
runner en **zonder asserts** — ze verifiëren niets en horen daarom niet in de
gate (DEF-429, sluit aan op DEF-420). Ze zijn behouden als handmatig
diagnose-gereedschap, niet weggegooid.

## rate_limiting/

Acht handmatige scripts rond de `SmartRateLimiter` / `IntegratedResilienceSystem`.
De geautomatiseerde regressiedekking voor de rate-limiter staat nu in:

- `tests/unit/utils/test_rate_limiter_xloop_regression.py` (DEF-429: cross-loop self-healing)
- `tests/unit/utils/test_resilience_timeout.py` (DEF-428: execution-timeout)
- `tests/unit/test_smart_rate_limiter.py` (TokenBucket-gedrag)

## Draaien

```bash
python tests/manual/rate_limiting/test_endpoint_rate_limiting.py
```
