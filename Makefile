PY?=python

.PHONY: dev lint complexity-check audit test status validation-status

dev:
	@echo "[dev] Starting Streamlit app via run script..."
	bash scripts/run_app.sh

lint:
	@echo "[lint] Ruff check on src/ and config/"
	@$(PY) -m ruff check src config
	@echo "[lint] Black check on src/ and config/"
	@$(PY) -m black --check src config

complexity-check:
	@echo "[complexity] Ratchet on src/ (DEF-418) — fails if violations grow above baseline"
	@$(PY) scripts/complexity_ratchet.py

audit:
	@echo "[audit] pip-audit CVE-scan op requirements.txt (DEF-426)"
	@$(PY) -m pip_audit --requirement requirements.txt --desc

test: test-markers-check
	@echo "[test] Running fast unit tests (fail-fast, excludes slow)"
	@pytest -q -m "unit and not slow" --maxfail=1

.PHONY: test-all test-unit test-integration test-acceptance test-performance test-smoke

test-all:
	@echo "[test-all] Running full test suite"
	@pytest -q

test-unit:
	@echo "[test-unit] Running unit tests"
	@pytest -q -m unit

test-integration:
	@echo "[test-integration] Running integration tests"
	@pytest -q -m integration

test-acceptance:
	@echo "[test-acceptance] Running acceptance tests"
	@pytest -q -m acceptance

test-performance:
	@echo "[test-performance] Running performance/benchmark tests"
	@pytest -q -m "performance or benchmark"

test-smoke:
	@echo "[test-smoke] Running smoke tests"
	@pytest -q -m smoke

.PHONY: test-parallel test-cov test-cov-ci

test-parallel:
	@echo "[test-parallel] Running unit tests in parallel"
	@pytest -q -n auto -m unit

test-cov:
	@echo "[test-cov] Coverage op unit-tests (deterministisch; integration hangt — DEF-428/429)"
	@pytest -q --cov=src --cov-report=term-missing -m unit

test-cov-ci:
	@echo "[test-cov-ci] Coverage met ratchet-vloer 45% (baseline DEF-416; verhogen in Fase 1)"
	@pytest -q --cov=src --cov-report=term-missing --cov-fail-under=45 -m unit

.PHONY: test-durations
test-durations:
	@echo "[test-durations] Showing 20 slowest unit tests"
	@pytest -q --durations=20 -m unit

.PHONY: smoke-web-lookup
smoke-web-lookup:
	@echo "[smoke] Running Web Lookup smoke tests"
	@PYTHONPATH=src pytest -q -m smoke_web_lookup

test-markers-check:
	@echo "[markers] Checking test marker coverage"
	@$(PY) scripts/testing/check_test_markers.py

status: validation-status

validation-status:
	@echo "[status] Running validation status updater..."
	$(PY) scripts/validation/validation-status-updater.py
	@echo "[status] Output written to reports/status/validation-status.json"

.PHONY: dashboard
dashboard:
	@echo "[dashboard] Generating static requirements dashboard..."
	$(PY) scripts/generate_requirements_dashboard.py
	@echo "[dashboard] Open file://$$(pwd)/docs/backlog/dashboard/index.html in your browser"

# Workflow automation tools (EPIC-025 US-431)
.PHONY: wip phase workflow-guard install-post-commit

wip:
	@echo "[wip] Showing work in progress..."
	@bash scripts/wip_tracker.sh

phase:
	@echo "[phase] Showing TDD phase..."
	@$(PY) scripts/phase-tracker.py

workflow-guard:
	@echo "[workflow-guard] Checking TDD workflow compliance..."
	@$(PY) scripts/workflow-guard.py

install-post-commit:
	@echo "[install-post-commit] Installing post-commit review reminder..."
	@cp scripts/hooks/post-commit-review-reminder .git/hooks/post-commit
	@chmod +x .git/hooks/post-commit
	@echo "[install-post-commit] Post-commit hook installed successfully"
