# DEF-513: kale `python` bestaat niet op macOS/CI-runners (alleen `python3`) —
# prefereer de project-venv, val terug op python3. Overridebaar: `make PY=... <target>`.
PY?=$(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
PYTEST := $(PY) -m pytest
REQUIRED_PYTHON_VERSION ?= 3.13

# DEF-519: de verplichte gates lopen alle via één bewaakte runner, zodat er geen
# tweede, verborgen selectie kan ontstaan. De runner zet de offline-bootstrap
# vóór elke import, draait in een verse werkmap en meldt lege selectie,
# collectiefout, toolfout, testfalen en budgetoverschrijding elk als eigen
# nonzero status. Alleen de rapportlocatie en het (eindige) budget zijn
# configureerbaar; er is bewust GEEN doorgeefluik voor vrije pytest-argumenten,
# want daarmee zouden scope of vloer via de omgeving kunnen krimpen.
RUNNER := $(PY) scripts/testing/run_profile.py
GATE_REPORTS ?= reports/gates
GATE_BUDGET ?= 900
GATE_DIR = $(abspath $(GATE_REPORTS))

.PHONY: check-python dev lint complexity-check mypy-check overrides-check pins-check orphan-check silent-except-check audit lock lock-check test status validation-status

check-python:
	@actual_version="$$($(PY) -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"; \
	if [ "$$actual_version" != "$(REQUIRED_PYTHON_VERSION)" ]; then \
		echo "FOUT: Python $(REQUIRED_PYTHON_VERSION) vereist; $(PY) gebruikt $$actual_version."; \
		echo "Maak de project-venv opnieuw: uv venv --python $(REQUIRED_PYTHON_VERSION) .venv"; \
		exit 1; \
	fi

dev:
	@echo "[dev] Starting Streamlit app via run script..."
	bash scripts/deployment/run_app.sh

lint:
	@echo "[lint] Ruff check on src/ and config/"
	@$(PY) -m ruff check src config
	@echo "[lint] Black check on src/ and config/"
	@$(PY) -m black --check src config

complexity-check:
	@echo "[complexity] Ratchet on src/ (DEF-418) — fails if violations grow above baseline"
	@$(PY) scripts/complexity_ratchet.py

mypy-check:
	@echo "[mypy] Ratchet on src/ (DEF-419) — fails if type-errors grow above baseline"
	@$(PY) scripts/mypy_ratchet.py

overrides-check:
	@echo "[mypy-overrides] Ratchet on the disallow_untyped_defs override list (DEF-431) — fails if it grows"
	@$(PY) scripts/mypy_overrides_ratchet.py

pins-check:
	@echo "[pins] Tool-pin consistency (DEF-430) — ruff/mypy must match across all sources"
	@$(PY) scripts/check_tool_pins.py

orphan-check:
	@echo "[orphan] Ratchet on src/ (DEF-600) — fails if modules without any importer grow"
	@$(PY) scripts/detect_orphan_modules.py

silent-except-check:
	@echo "[silent-except] Ratchet on src/ (DEF-393) — fails if silent broad excepts grow"
	@$(PY) scripts/silent_except_ratchet.py

audit:
	@echo "[audit] pip-audit CVE-scan op requirements.txt (DEF-426)"
	@$(PY) -m pip_audit --requirement requirements.txt --desc

lock:
	@echo "[lock] Compileer hashed requirements uit .in-bronnen (DEF-426)"
	@# DEF-711: genereren en verifiëren delen één implementatie, zodat de
	@# vlaggenset en de versievoorkeur niet uiteen kunnen lopen. Het script
	@# compileert bovendien naar een verse werkmap met een versie-only
	@# voorkeur; rechtstreeks naar het bestaande requirements.txt schrijven
	@# liet uv hashes accumuleren (41 dubbele regels na één run) en bestaande
	@# hash-corruptie ongemoeid.
	@bash scripts/ci/check_lock_sync.sh --write

lock-check:
	@# DEF-711: de logica staat in scripts/ci/check_lock_sync.sh, zodat het
	@# gedrag testbaar is. Make vertaalt elke gefaalde recipe naar exit 2, dus de
	@# exit-codes van het script (1 = desync, 2 = resolve-fout, 3 = preconditie)
	@# zijn alleen zichtbaar bij een directe aanroep — wat de unit-test doet.
	@bash scripts/ci/check_lock_sync.sh

test: check-python test-markers-check
	@echo "[test] Alias van de unitgate — zelfde scope als 'make test-unit'"
	@$(MAKE) --no-print-directory test-unit

.PHONY: test-all test-unit test-integration test-acceptance test-performance test-smoke test-contract

test-all: check-python
	@echo "[test-all] Running full test suite"
	@$(PYTEST) -q

test-unit: check-python
	@echo "[test-unit] Canonieke unitgate: ALLE unittests, inclusief slow"
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) unit --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/unit-inventaris.json \
		--junitxml=$(GATE_DIR)/unit-junit.xml

test-integration: check-python
	@echo "[test-integration] Canonieke integrationgate: tests/integration/ + integrationmarker"
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) integration --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/integration-inventaris.json \
		--junitxml=$(GATE_DIR)/integration-junit.xml

test-acceptance: check-python
	@echo "[test-acceptance] Canonieke acceptance-smoke-gate"
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) acceptance-smoke --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/acceptance-smoke-inventaris.json \
		--junitxml=$(GATE_DIR)/acceptance-smoke-junit.xml

test-contract: check-python
	@echo "[test-contract] Contractgate (required check 'Validation Contract Tests')"
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) contract --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/contract-inventaris.json \
		--junitxml=$(GATE_DIR)/contract-junit.xml

test-performance: check-python
	@echo "[test-performance] Running performance/benchmark tests"
	@$(PYTEST) -q -m "performance or benchmark"

test-smoke: check-python
	@echo "[test-smoke] Alias van de acceptance-smoke-gate"
	@$(MAKE) --no-print-directory test-acceptance

.PHONY: test-parallel test-cov test-cov-ci

test-parallel: check-python
	@echo "[test-parallel] Running unit tests in parallel"
	@$(PYTEST) -q -n auto -m unit

test-cov: check-python
	@echo "[test-cov] Lokale coverage op de unitgate — GEEN CI-ratchet (zie test-cov-ci)"
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) unit --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/unit-cov-lokaal-inventaris.json \
		--cov=$(CURDIR)/src --cov-report=term-missing

test-cov-ci: check-python
	@echo "[test-cov-ci] Unitgate met ratchet-vloer 45% (baseline DEF-416; verhogen in Fase 1)"
	@# DEF-519: dezelfde unitselectie als test-unit (ALLE unit, inclusief slow),
	@# gemeten via de seriële Coverage-API-route van de runner. De oude `-n 4`
	@# is vervallen: de runner-allowlist laat geen xdist-vlaggen door, omdat de
	@# gedeelde inventaris controller- en workerinformatie niet gescheiden
	@# vastlegt. Er wordt hier dus geen versnelling geclaimd, alleen dezelfde
	@# scope en dezelfde vloer. De datafile blijft in de verse sessieroot van de
	@# runner; het `.coverage` van de checkout wordt nooit gelezen of
	@# overschreven. Het pad staat in de inventaris onder `coverage_artefacten`.
	@mkdir -p $(GATE_REPORTS)
	@$(RUNNER) unit --budget=$(GATE_BUDGET) \
		--inventory=$(GATE_DIR)/unit-cov-inventaris.json \
		--junitxml=$(GATE_DIR)/unit-cov-junit.xml \
		--cov=$(CURDIR)/src --cov-report=term-missing \
		--cov-report=xml:$(GATE_DIR)/unit-coverage.xml \
		--cov-fail-under=45

.PHONY: test-durations
test-durations: check-python
	@echo "[test-durations] Showing 20 slowest unit tests"
	@$(PYTEST) -q --durations=20 -m unit

.PHONY: smoke-web-lookup
smoke-web-lookup: check-python
	@echo "[smoke] Running Web Lookup smoke tests"
	@PYTHONPATH=src $(PYTEST) -q -m smoke_web_lookup

test-markers-check: check-python
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
