---
id: EPIC-026-TEST-IMPLEMENTATION-GUIDE
epic: EPIC-026
phase: 0
created: 2025-10-02
owner: test-engineer
status: implementation-guide
---

# EPIC-026 Test Implementation Guide

**Practical guide for implementing the 5-week test recovery plan**

---

## Week 0: Test Infrastructure Setup (5 days)

### Day 1: Streamlit Test Harness

**Goal:** Configure pytest to test Streamlit applications

**Tasks:**

1. **Install dependencies:**
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
pip install pytest-playwright playwright
pip install pytest-recording responses
playwright install
```

2. **Create test utilities:**

```python
# tests/utils/streamlit_test_harness.py
"""Utilities for testing Streamlit apps without full UI."""

import streamlit as st
from unittest.mock import MagicMock
from typing import Any, Dict

class StreamlitTestContext:
    """Mock Streamlit context for testing."""

    def __init__(self):
        self.session_state = {}
        self.widgets = {}
        self.markdown_calls = []
        self.error_calls = []
        self.success_calls = []

    def __enter__(self):
        # Mock st.session_state
        st.session_state = self.session_state

        # Mock UI functions
        st.markdown = lambda text, **kwargs: self.markdown_calls.append(text)
        st.error = lambda text: self.error_calls.append(text)
        st.success = lambda text: self.success_calls.append(text)
        st.button = lambda label, **kwargs: False  # Default: not clicked
        st.text_input = lambda label, **kwargs: kwargs.get('value', '')

        return self

    def __exit__(self, *args):
        pass

    def set_button_clicked(self, label: str, clicked: bool = True):
        """Simulate button click."""
        st.button = lambda l, **kwargs: clicked if l == label else False
```

3. **Create session state fixtures:**

```python
# tests/fixtures/session_state_fixtures.py
"""Fixtures for session state testing."""

import pytest
from ui.session_state import SessionStateManager

@pytest.fixture
def clean_session_state():
    """Provide clean session state for each test."""
    # Clear existing state
    if hasattr(st, 'session_state'):
        st.session_state.clear()

    SessionStateManager.initialize_session_state()
    yield

    # Cleanup
    if hasattr(st, 'session_state'):
        st.session_state.clear()

@pytest.fixture
def session_state_with_context():
    """Session state with pre-populated context."""
    clean_session_state()

    SessionStateManager.set_value("global_context", {
        "organisatorische_context": ["DJI", "OM"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": ["Art. 27 Sv"]
    })

    yield

    st.session_state.clear()
```

### Day 2: Mock Factories

**Goal:** Create reusable mocks for all services

**Tasks:**

1. **Service mock factory:**

```python
# tests/factories/service_mocks.py
"""Mock factories for service dependencies."""

from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

class ServiceMockFactory:
    """Create consistent service mocks."""

    @staticmethod
    def create_definition_service(
        success: bool = True,
        definition: str = "Test definitie",
        score: float = 0.85
    ) -> MagicMock:
        """Mock definition service."""
        service = MagicMock()
        service.generate_definition = AsyncMock(return_value={
            "success": success,
            "definitie_origineel": definition,
            "definitie_gecorrigeerd": definition,
            "final_score": score,
            "validation_details": {
                "overall_score": score,
                "is_acceptable": score >= 0.60,
                "violations": [],
                "passed_rules": ["CON-001", "ESS-002"]
            },
            "voorbeelden": {},
            "metadata": {"generation_id": "test-123"},
            "sources": []
        })
        return service

    @staticmethod
    def create_repository(definitions: list = None) -> MagicMock:
        """Mock repository."""
        repo = MagicMock()
        repo.get_all_definities.return_value = definitions or []
        repo.save_definitie.return_value = 1  # Mock ID
        return repo

    @staticmethod
    def create_checker(
        action: str = "PROCEED",
        existing_def: Any = None
    ) -> MagicMock:
        """Mock definitie checker."""
        from integration.definitie_checker import CheckAction

        checker = MagicMock()
        result = MagicMock()
        result.action = getattr(CheckAction, action)
        result.existing_definitie = existing_def
        result.duplicates = []

        checker.check_before_generation.return_value = result
        return checker
```

2. **Test data factory:**

```python
# tests/factories/test_data.py
"""Test data factories."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class GenerationResultFactory:
    """Create generation result test data."""

    @staticmethod
    def create_success_result(begrip: str = "authenticatie") -> Dict[str, Any]:
        return {
            "begrip": begrip,
            "check_result": None,
            "agent_result": {
                "success": True,
                "definitie_origineel": f"Definitie van {begrip}",
                "definitie_gecorrigeerd": f"Gecorrigeerde definitie van {begrip}",
                "final_score": 0.85,
                "validation_details": {
                    "overall_score": 0.85,
                    "is_acceptable": True,
                    "violations": [],
                    "passed_rules": ["CON-001", "ESS-002", "INT-001"]
                },
                "voorbeelden": {
                    "voorbeeldzinnen": ["Voorbeeld 1", "Voorbeeld 2"],
                    "praktijkvoorbeelden": ["Praktijk 1"]
                },
                "metadata": {"generation_id": "test-456"},
                "sources": [
                    {
                        "provider": "wikipedia",
                        "title": "Test bron",
                        "snippet": "Test snippet"
                    }
                ]
            },
            "saved_definition_id": 1,
            "determined_category": "proces",
            "category_reasoning": "Proces patroon gedetecteerd",
            "category_scores": {"proces": 3, "type": 0}
        }

    @staticmethod
    def create_validation_failure(begrip: str = "test") -> Dict[str, Any]:
        result = GenerationResultFactory.create_success_result(begrip)
        result["agent_result"]["success"] = False
        result["agent_result"]["final_score"] = 0.45
        result["agent_result"]["validation_details"]["is_acceptable"] = False
        result["agent_result"]["validation_details"]["violations"] = [
            {
                "regel_id": "CON-001",
                "severity": "high",
                "message": "Begrip niet aanwezig"
            }
        ]
        return result
```

### Day 3: Golden Master Recording

**Goal:** Setup infrastructure to capture current behavior

**Tasks:**

1. **Create golden master recorder:**

```python
# tests/utils/golden_master.py
"""Golden master testing utilities."""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict

class GoldenMaster:
    """Record and compare golden master test results."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.golden_dir = Path("tests/golden_masters")
        self.golden_dir.mkdir(exist_ok=True)

    def record(self, data: Any, suffix: str = ""):
        """Record golden master."""
        filepath = self._get_path(suffix)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Golden master recorded: {filepath}")

    def verify(self, data: Any, suffix: str = "") -> bool:
        """Verify against golden master."""
        filepath = self._get_path(suffix)

        if not filepath.exists():
            raise FileNotFoundError(f"Golden master not found: {filepath}")

        with open(filepath) as f:
            expected = json.load(f)

        return self._compare(expected, data)

    def _get_path(self, suffix: str) -> Path:
        filename = f"{self.test_name}{suffix}.json"
        return self.golden_dir / filename

    def _compare(self, expected: Any, actual: Any) -> bool:
        """Deep comparison of data structures."""
        if type(expected) != type(actual):
            return False

        if isinstance(expected, dict):
            if expected.keys() != actual.keys():
                return False
            return all(self._compare(expected[k], actual[k]) for k in expected)

        if isinstance(expected, list):
            if len(expected) != len(actual):
                return False
            return all(self._compare(e, a) for e, a in zip(expected, actual))

        return expected == actual
```

2. **Usage example:**

```python
# tests/test_generation_golden.py
"""Golden master tests for generation flow."""

def test_generation_flow_golden_master(clean_session_state):
    """Test generation flow matches golden master."""
    gm = GoldenMaster("generation_flow")

    # Setup
    interface = TabbedInterface()
    begrip = "authenticatie"
    context = {"organisatorische_context": ["DJI"]}

    # Record mode (run once to create golden master)
    # result = interface._handle_definition_generation(begrip, context)
    # gm.record(result, suffix="_success")

    # Verify mode (run on every test)
    result = interface._handle_definition_generation(begrip, context)
    assert gm.verify(result, suffix="_success")
```

### Day 4-5: Async Testing & Playwright Setup

**Goal:** Configure async and UI testing infrastructure

**Tasks:**

1. **Async test utilities:**

```python
# tests/utils/async_helpers.py
"""Async testing utilities."""

import asyncio
from typing import Any, Coroutine

def run_async_test(coro: Coroutine) -> Any:
    """Run async function in sync test context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@pytest.fixture
def async_test():
    """Fixture for async tests."""
    return run_async_test
```

2. **Playwright configuration:**

```toml
# pytest.ini additions
[pytest]
playwright_headed = false
playwright_slow_mo = 0
playwright_browser = chromium
```

---

## Weeks 1-2: Critical Path Testing (10 days)

### Critical Test Pattern Template

**Use this template for all orchestrator tests:**

```python
# tests/critical/test_generation_orchestrator.py
"""Critical path tests for definition generation orchestrator."""

import pytest
from tests.factories.service_mocks import ServiceMockFactory
from tests.utils.streamlit_test_harness import StreamlitTestContext

class TestGenerationOrchestrator:
    """Test _handle_definition_generation god method."""

    @pytest.fixture
    def interface(self):
        """Create interface with mocked services."""
        interface = TabbedInterface()
        interface.definition_service = ServiceMockFactory.create_definition_service()
        interface.checker = ServiceMockFactory.create_checker()
        interface.repository = ServiceMockFactory.create_repository()
        return interface

    # HAPPY PATH TESTS

    def test_basic_generation_with_org_context(self, interface, clean_session_state):
        """Test basic generation with organizational context."""
        with StreamlitTestContext() as ctx:
            begrip = "authenticatie"
            context = {"organisatorische_context": ["DJI"]}

            interface._handle_definition_generation(begrip, context)

            # Verify service called
            interface.definition_service.generate_definition.assert_called_once()

            # Verify session state updated
            result = SessionStateManager.get_value("last_generation_result")
            assert result["begrip"] == begrip
            assert result["agent_result"]["success"] is True

            # Verify UI feedback
            assert any("succesvol" in msg.lower() for msg in ctx.success_calls)

    def test_generation_with_all_contexts(self, interface, clean_session_state):
        """Test generation with org + juridisch + wettelijk context."""
        # Implementation
        pass

    def test_generation_with_document_context(self, interface, clean_session_state):
        """Test generation with uploaded documents."""
        # Implementation
        pass

    # ERROR PATH TESTS

    def test_generation_fails_with_empty_begrip(self, interface, clean_session_state):
        """Test error when begrip is empty."""
        with StreamlitTestContext() as ctx:
            interface._handle_definition_generation("", {})

            # Verify error shown
            assert any("begrip" in msg.lower() for msg in ctx.error_calls)

    def test_generation_fails_with_no_context(self, interface, clean_session_state):
        """Test error when all contexts are empty."""
        # Implementation
        pass

    def test_service_timeout_handling(self, interface, clean_session_state):
        """Test timeout during async generation."""
        # Mock service to timeout
        interface.definition_service.generate_definition = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        # Verify graceful handling
        # Implementation
        pass

    # EDGE CASES

    def test_very_long_begrip(self, interface, clean_session_state):
        """Test with begrip > 200 characters."""
        begrip = "a" * 250
        # Implementation
        pass

    def test_unicode_in_begrip(self, interface, clean_session_state):
        """Test with unicode characters."""
        begrip = "café_protocol_验证"
        # Implementation
        pass

    def test_concurrent_generation_requests(self, interface, clean_session_state):
        """Test handling of concurrent generation requests."""
        # Implementation
        pass
```

### Week 1 Test Schedule

**Day 1: Generation Orchestrator (Part 1)**
- Setup test class with fixtures (2h)
- Happy path tests 1-6 (4h)
- Error path tests 1-3 (2h)
**Target: 25 tests**

**Day 2: Generation Orchestrator (Part 2)**
- Error path tests 4-9 (3h)
- Edge cases 1-5 (3h)
- Integration with real services (2h)
**Target: 30 tests**

**Day 3: Regeneration Orchestrator (Part 1)**
- Setup + happy path (6h)
- Error paths (2h)
**Target: 30 tests**

**Day 4: Regeneration Orchestrator (Part 2)**
- Edge cases (4h)
- Category change scenarios (4h)
**Target: 30 tests**

**Day 5: Category Determination**
- 6-step protocol tests (3h)
- Fallback chain tests (2h)
- Pattern matching tests (3h)
**Target: 40 tests**

### Week 2 Test Schedule

**Day 1: Document Processing**
- Upload tests (2h)
- Extraction tests (3h)
- Snippet tests (3h)
**Target: 35 tests**

**Day 2: Generation Results Rendering**
- Basic rendering (3h)
- Validation display (2h)
- Sources display (3h)
**Target: 25 tests**

**Day 3: Examples & Persistence**
- Persistence logic (3h)
- Deduplication (2h)
- Database integration (3h)
**Target: 30 tests**

**Day 4: Validation Presentation**
- Violation formatting (3h)
- Passed rules display (2h)
- Rule hints (3h)
**Target: 30 tests**

**Day 5: Actions & Utilities**
- Action handlers (3h)
- Duplicate check (2h)
- Context guards (3h)
**Target: 43 tests**

---

## Week 3: Coverage Completion (5 days)

### Gap Analysis Process

**Daily routine:**

1. **Morning: Coverage Analysis (1h)**
```bash
pytest --cov=src/ui/components/definition_generator_tab --cov-report=html
pytest --cov=src/ui/tabbed_interface --cov-report=html
open htmlcov/index.html
```

2. **Identify gaps:**
- Uncovered lines (red in report)
- Uncovered branches (yellow in report)
- Missing edge cases

3. **Afternoon: Gap Filling (7h)**
- Write tests for uncovered code
- Focus on highest-risk gaps first
- Target +13-14 tests per day

**Week 3 Schedule:**

- **Day 1:** Context guards + edge cases (15 tests)
- **Day 2:** Rule reasoning completion (15 tests)
- **Day 3:** Duplicate check scenarios (15 tests)
- **Day 4:** Async/sync edge cases (13 tests)
- **Day 5:** Final gaps + buffer (10 tests)

**Target: 68 tests to reach 436 total**

---

## Week 4: Test Refinement (5 days)

### Characterization → Behavioral Conversion

**Pattern: Convert "it does X" to "it should do X"**

**Before (Characterization):**
```python
def test_generation_returns_dict():
    """Test that generation returns a dict."""
    result = interface._handle_definition_generation("test", {})
    assert isinstance(result, dict)
```

**After (Behavioral):**
```python
def test_generation_should_create_complete_result_structure():
    """Generation should return result with all required fields."""
    result = interface._handle_definition_generation("authenticatie", {
        "organisatorische_context": ["DJI"]
    })

    # Behavioral assertions
    assert result["begrip"] == "authenticatie", "Should preserve input begrip"
    assert "agent_result" in result, "Should include generation result"
    assert "determined_category" in result, "Should determine category"
    assert "category_reasoning" in result, "Should explain category choice"

    # Quality assertions
    agent_result = result["agent_result"]
    assert agent_result["success"] is True, "Should succeed with valid input"
    assert agent_result["final_score"] >= 0.6, "Should meet quality threshold"
```

### Test Organization

**Reorganize tests by feature:**

```
tests/
├── critical/                    # Critical path tests
│   ├── test_generation_orchestrator.py
│   ├── test_regeneration_orchestrator.py
│   └── test_category_determination.py
├── features/                    # Feature-based organization
│   ├── generation/
│   │   ├── test_generation_flow.py
│   │   ├── test_validation_integration.py
│   │   └── test_result_rendering.py
│   ├── regeneration/
│   │   ├── test_category_change.py
│   │   └── test_impact_analysis.py
│   └── document_processing/
│       ├── test_upload.py
│       ├── test_extraction.py
│       └── test_snippet_creation.py
└── regression/                  # Regression test suite
    ├── test_regression_suite.py
    └── golden_masters/
```

### Week 4 Schedule

- **Day 1:** Convert critical path tests (all generation tests)
- **Day 2:** Convert orchestrator tests (regeneration, category)
- **Day 3:** Reorganize by feature, create test suites
- **Day 4:** Extract test utilities, reduce duplication
- **Day 5:** Documentation, test naming improvements

---

## Week 5: Validation & Documentation (5 days)

### Day 1-2: Test Validation

**Checklist:**

1. **Run full suite:**
```bash
pytest -v --cov=src --cov-report=html --cov-report=term
```

2. **Check coverage:**
```bash
# Should see:
# definition_generator_tab.py: 70%+
# tabbed_interface.py: 75%+
# Overall: 85%+
```

3. **Check for flaky tests:**
```bash
pytest --count=10 tests/critical/
```

4. **Performance check:**
```bash
pytest --durations=20
# Full suite should run < 5min
```

5. **Mutation testing:**
```bash
mutmut run
mutmut results
# Should see 70%+ mutation score
```

### Day 3-4: Documentation

**Create test documentation:**

1. **Test strategy doc:**
```markdown
# Test Strategy - EPIC-026

## Overview
This document describes the test strategy for god object refactoring.

## Test Architecture
- Critical path tests (60%): Focus on orchestrators
- Feature tests (30%): Organized by user story
- Regression tests (10%): Golden masters

## Coverage Targets
- definition_generator_tab: 70%
- tabbed_interface: 75%
- Orchestrators: 95%

## Test Types
- Integration tests: 60%
- Unit tests: 40%

## Running Tests
...
```

2. **Coverage report:**
```markdown
# Test Coverage Report

## Summary
- Total tests: 436
- Total coverage: 85%
- Critical path coverage: 95%

## By Component
...
```

3. **Maintenance guide:**
```markdown
# Test Maintenance Guide

## Adding New Tests
When adding new functionality:
1. Write test first (TDD)
2. Ensure coverage >= 80%
3. Add to appropriate suite

## Test Organization
...
```

### Day 5: Phase Transition

**Handoff to Phase 1 (Design):**

1. **Final checkpoint meeting:**
- Review all success criteria
- Confirm 85%+ coverage achieved
- Approve transition to Phase 1

2. **Handoff documentation:**
- Test suite overview
- Known gaps (if any)
- Maintenance responsibilities

3. **Phase 1 kickoff:**
- Design can now begin safely
- Test suite provides safety net
- Refactoring can proceed

---

## Tools & Resources

### Essential Tools

```bash
# Install all test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio \
    pytest-playwright pytest-recording responses \
    pytest-benchmark pytest-flakefinder mutmut
```

### Pytest Configuration

```toml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-branch
markers =
    critical: Critical path tests
    integration: Integration tests
    unit: Unit tests
    slow: Slow tests (>1s)
    flaky: Known flaky tests
```

### Coverage Configuration

```toml
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
precision = 2
show_missing = true
skip_covered = false

[html]
directory = htmlcov
```

---

## Quick Reference

### Test Metrics Dashboard

**Check daily:**

```bash
# Coverage
pytest --cov=src --cov-report=term-missing

# Flaky tests
pytest --count=5 --fail-on-flaky

# Performance
pytest --durations=10

# All metrics
make test-metrics
```

### Common Test Patterns

**Pattern 1: Mock Streamlit UI**
```python
with StreamlitTestContext() as ctx:
    # Test code
    assert "success" in ctx.success_calls[0]
```

**Pattern 2: Async Service Test**
```python
@pytest.mark.asyncio
async def test_async_service():
    result = await service.async_method()
    assert result
```

**Pattern 3: Golden Master**
```python
gm = GoldenMaster("test_name")
# First run: gm.record(result)
assert gm.verify(result)
```

**Pattern 4: Integration Test**
```python
def test_full_flow(clean_session_state):
    # Setup
    interface = TabbedInterface()

    # Execute
    interface._handle_definition_generation(...)

    # Verify end-to-end
    result = SessionStateManager.get_value("last_generation_result")
    assert result["success"]
```

---

## Success Metrics

**Track weekly:**

| Metric | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Target |
|--------|--------|--------|--------|--------|--------|--------|
| Total Tests | 165 | 333 | 401 | 436 | 436 | 436+ |
| Coverage % | 45% | 68% | 80% | 85% | 85% | 85%+ |
| Flaky Rate | 8% | 6% | 4% | 2% | <1% | <5% |
| Exec Time (min) | 3.2 | 4.1 | 4.8 | 4.5 | 4.2 | <5 |
| Mutation Score | - | - | - | 68% | 72% | 70%+ |

---

**This guide provides the practical implementation details for the 5-week test recovery plan. Follow it step-by-step to achieve 85%+ coverage and safe refactoring capability.**
