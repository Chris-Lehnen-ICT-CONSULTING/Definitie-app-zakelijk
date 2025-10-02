PY?=python

.PHONY: dev lint test status validation-status

dev:
	@echo "[dev] Starting Streamlit app via run script..."
	bash scripts/run_app.sh

lint:
	@echo "[lint] Ruff check on src/ and config/"
	@$(PY) -m ruff check src config
	@echo "[lint] Black check on src/ and config/"
	@$(PY) -m black --check src config

test:
	@echo "[test] Running fast default test subset (fail-fast)"
	@pytest -q -m "not (integration or performance or benchmark or acceptance or slow or regression)" --maxfail=1

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
	@echo "[test-parallel] Running fast subset in parallel"
	@pytest -q -n auto -m "not (integration or performance or benchmark or acceptance or slow or regression)"

test-cov:
	@echo "[test-cov] Running coverage on src (term-missing)"
	@pytest -q --cov=src --cov-report=term-missing -m "not (performance or benchmark)"

test-cov-ci:
	@echo "[test-cov-ci] Coverage with threshold (85%)"
	@pytest -q --cov=src --cov-report=term-missing --cov-fail-under=85 -m "not (performance or benchmark)"

.PHONY: test-durations
test-durations:
	@echo "[test-durations] Showing 20 slowest tests"
	@pytest -q --durations=20 -m "not (integration or performance or benchmark or acceptance or slow)"

.PHONY: smoke-web-lookup
smoke-web-lookup:
	@echo "[smoke] Running Web Lookup smoke tests"
	@PYTHONPATH=src pytest -q -m smoke_web_lookup

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
