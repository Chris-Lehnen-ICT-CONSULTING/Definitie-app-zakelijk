---
aangemaakt: 04-09-2025
applies_to: definitie-app@v2
bijgewerkt: '08-09-2025'
canonical: false
last_verified: 04-09-2025
owner: testing
prioriteit: medium
status: active
story_id: PER-007
test_phase: RED
---



# PER-007 TDD Test Plan: Context Flow Refactoring

## Executive Summary

This test plan validates the critical architecture decision: **UI preview strings are presentation layer only and must NEVER be used as data source**. We follow strict TDD methodology with RED-GREEN-REFACTOR cycles to ensure the implementation meets all vereistes.

## Critical Architecture Decisions to Validate

1. **Single Source of Truth**: DefinitionGeneratorContext is the ONLY path for context processing
2. **UI Preview vs Data Separation**: UI strings are DERIVED from EnrichedContext, never used as input
3. **Custom "Anders..." Entries**: Must work without validation failures
4. **ASTRA Compliance**: Warnings only, never blocking errors

## TDD Phase 1: RED Tests (Must Fail First)

### Test Suite 1: UI Preview String Rejection Tests

These tests MUST fail initially to prove the system incorrectly accepts UI strings as data source.

```python
# tests/test_per007_ui_separation_red.py
import pytest
from unittest.mock import Mock, patch
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.definition_generator_context import HybridContextManager, EnrichedContext
from services.interfaces import GenerationRequest

class TestUIPreviewRejection:
    """Tests that MUST fail in RED phase - proving UI strings are wrongly accepted"""

    def test_prompt_builder_rejects_ui_preview_string(self):
        """MUST FAIL: System should reject UI preview strings as input"""
        # GIVEN: A UI preview string with emojis and formatting
        ui_preview = "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht | 📜 Wet: Art. 27 Sv"

        # WHEN: Someone tries to use it as context input
        prompt_service = PromptServiceV2()

        # THEN: System should raise TypeError or ValueError
        with pytest.raises((TypeError, ValueError),
                         match="UI preview strings cannot be used as data source"):
            # This should fail in RED phase - system wrongly accepts this
            prompt_service._parse_ui_string_as_context(ui_preview)

    def test_context_manager_rejects_concatenated_strings(self):
        """MUST FAIL: Context manager should reject concatenated context strings"""
        # GIVEN: A request with UI-formatted context
        request = GenerationRequest(
            begrip="verdachte",
            context="📋 Org: OM | ⚖️ Juridisch: Strafrecht"  # UI string
        )

        # WHEN: Processing the context
        manager = HybridContextManager()

        # THEN: Should raise error about using UI strings
        with pytest.raises(ValueError, match="Use structured lists, not UI strings"):
            # This should fail in RED phase - system processes it incorrectly
            manager.process_ui_string_context(request)

    def test_enriched_context_validates_source_type(self):
        """MUST FAIL: EnrichedContext should validate it's built from lists, not strings"""
        # GIVEN: Attempt to create context from wrong source
        # WHEN: Building EnrichedContext from UI string
        # THEN: Should fail validation
        with pytest.raises(TypeError, match="EnrichedContext requires structured lists"):
            EnrichedContext.from_ui_string("📋 Org: OM | ⚖️ Juridisch: Strafrecht")

### Test Suite 2: Single Source of Truth Tests

```python
# tests/test_per007_single_source_red.py
class TestSingleSourceOfTruth:
    """Tests that MUST fail initially - proving multiple paths exist"""

    def test_only_one_context_processing_path_exists(self):
        """MUST FAIL: Currently multiple paths exist for context processing"""
        # GIVEN: The application's context processing components
        from services import context_paths

        # WHEN: Analyzing all context processing paths
        paths = context_paths.find_all_context_routes()

        # THEN: Only ONE path should exist
        assert len(paths) == 1, f"Found {len(paths)} context paths, expected 1"
        assert paths[0] == "DefinitionGeneratorContext", "Wrong single source"

    def test_legacy_context_manager_is_blocked(self):
        """MUST FAIL: Legacy context_manager should be blocked"""
        # GIVEN: Attempt to use legacy context manager
        from orchestration.context_manager import LegacyContextManager  # Should not exist

        # THEN: Should raise ImportError or be marked deprecated
        with pytest.raises(ImportError):
            manager = LegacyContextManager()

    def test_prompt_context_legacy_path_blocked(self):
        """MUST FAIL: Legacy prompt_context path should be blocked"""
        # GIVEN: Legacy prompt building path
        from services.legacy_prompt import build_prompt_with_context

        # THEN: Should be blocked or raise DeprecationWarning
        with pytest.warns(DeprecationWarning):
            build_prompt_with_context("test", {})

### Test Suite 3: Custom "Anders..." Entry Tests

```python
# tests/test_per007_anders_option_red.py
class TestAndersOption:
    """Tests for custom 'Anders...' option - MUST fail initially"""

    def test_anders_in_organisatorische_context(self):
        """MUST FAIL: Anders option currently crashes"""
        # GIVEN: User selects "Anders..." and enters custom text
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "Anders...", "CustomOrg"]
        )

        # WHEN: Processing the request
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: Should handle gracefully
        assert "CustomOrg" in context["organisatorisch"]
        assert "Anders..." not in context["organisatorisch"]  # Removed after processing

    def test_anders_with_empty_custom_value(self):
        """MUST FAIL: Empty Anders value currently crashes"""
        # GIVEN: Anders selected but no custom value entered
        request = GenerationRequest(
            begrip="test",
            juridische_context=["Strafrecht", "Anders...", ""]
        )

        # WHEN: Processing
        manager = HybridContextManager()

        # THEN: Should handle empty gracefully
        context = manager._build_base_context(request)
        assert "Anders..." not in context["juridisch"]
        assert "" not in context["juridisch"]

    def test_anders_preserves_session_state(self):
        """MUST FAIL: Custom entries not preserved in session"""
        # GIVEN: Custom entry via Anders
        custom_org = "Bijzondere Eenheid X"

        # WHEN: Added to session
        import streamlit as st
        st.session_state.custom_organisations = [custom_org]

        # THEN: Should persist across requests
        # This will fail - session preservation not geïmplementeerd
        assert custom_org in st.session_state.get('preserved_custom_orgs', [])

### Test Suite 4: ASTRA Compliance Tests

```python
# tests/test_per007_astra_compliance_red.py
class TestASTRACompliance:
    """ASTRA compliance tests - MUST fail initially"""

    def test_invalid_org_gives_warning_not_error(self):
        """MUST FAIL: Currently blocks on invalid orgs"""
        # GIVEN: Invalid organization name
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["InvalidOrg", "OM"]
        )

        # WHEN: Validation occurs
        manager = HybridContextManager()
        with patch('logging.warning') as mock_warn:
            context = manager._build_base_context(request)

            # THEN: Should warn, not error
            mock_warn.assert_called_with(
                "ASTRA validation: Organization 'InvalidOrg' not in ASTRA registry"
            )
            # Maar still process the request
            assert "InvalidOrg" in context["organisatorisch"]  # Still included
            assert "OM" in context["organisatorisch"]

    def test_fuzzy_matching_suggestions(self):
        """MUST FAIL: No fuzzy matching geïmplementeerd"""
        # GIVEN: Misspelled organization
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["DJI2"]  # Typo
        )

        # WHEN: Validation
        from services.validation.astra_validator import validate_organization
        valid, suggestion = validate_organization("DJI2")

        # THEN: Should suggest correct spelling
        assert not valid
        assert "Did you mean: DJI" in suggestion

    def test_telemetry_tracks_custom_entries(self):
        """MUST FAIL: Telemetry not geïmplementeerd"""
        # GIVEN: Custom organization entry
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["CustomOrg"]
        )

        # WHEN: Processed
        manager = HybridContextManager()
        with patch('services.telemetry.track_custom_entry') as mock_track:
            manager._build_base_context(request)

            # THEN: Should track for reporting
            mock_track.assert_called_with("organisatorisch", "CustomOrg")

## TDD Phase 2: GREEN Tests (Make Tests Pass)

### Implementatie Checklist for GREEN Phase

```python
# Implementatie required to make RED tests pass:

1. Create ContextFormatter class:
   - format_ui_preview(context: EnrichedContext) -> str
   - format_prompt_context(context: EnrichedContext) -> dict
   - NEVER accept UI strings as input

2. Update HybridContextManager:
   - Remove/block process_ui_string_context()
   - Add Anders... handling logic
   - Add order-preserving deduplication

3. Create ASTRA Validator:
   - validate_organization() with fuzzy matching
   - Warning-only mode (never blocking)
   - Telemetry integration

4. Block legacy paths:
   - Mark old context_manager deprecated
   - Remove prompt_context legacy route
   - Single path through DefinitionGeneratorContext
```

## TDD Phase 3: REFACTOR Tests

### Test Suite 5: Prestaties Benchmarks

```python
# tests/test_per007_performance.py
import time
import pytest
from services.definition_generator_context import HybridContextManager

class TestPerformance:
    """Prestaties benchmarks - run after GREEN phase"""

    @pytest.mark.benchmark
    def test_context_processing_under_100ms(self, benchmark):
        """Context processing must complete in < 100ms"""
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak"],
            juridische_context=["Strafrecht", "Bestuursrecht"],
            wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv", "AWB"]
        )

        manager = HybridContextManager()

        # Benchmark the processing
        result = benchmark(manager._build_base_context, request)

        # Assert performance
        assert benchmark.stats['mean'] < 0.1  # 100ms
        assert result["organisatorisch"] == ["OM", "DJI", "Rechtspraak"]

    @pytest.mark.benchmark
    def test_deduplication_performance(self, benchmark):
        """Deduplication must be efficient even with large lists"""
        # GIVEN: Large list with duplicates
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM"] * 100 + ["DJI"] * 100
        )

        manager = HybridContextManager()

        # WHEN: Processing with deduplication
        result = benchmark(manager._build_base_context, request)

        # THEN: Fast and correct
        assert benchmark.stats['mean'] < 0.05  # 50ms
        assert result["organisatorisch"] == ["OM", "DJI"]  # Order preserved

    @pytest.mark.benchmark
    def test_ui_formatting_performance(self, benchmark):
        """UI preview generation must be fast"""
        from services.ui.formatters import ContextFormatter

        context = EnrichedContext(
            base_context={
                "organisatorisch": ["OM", "DJI", "Rechtspraak"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Art. 27 Sv"]
            },
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={}
        )

        formatter = ContextFormatter()

        # Benchmark UI string generation
        result = benchmark(formatter.format_ui_preview, context)

        # Prestaties assertion
        assert benchmark.stats['mean'] < 0.001  # 1ms
        assert "📋 Org:" in result
        assert "⚖️ Juridisch:" in result
```

## TDD Phase 4: Acceptance Tests

### Test Suite 6: End-to-End Acceptance Tests

```python
# tests/test_per007_acceptance.py
class TestAcceptanceCriteria:
    """Full acceptance tests - validate architecture decisions"""

    def test_ac1_ui_preview_never_used_as_source(self):
        """AC1: UI preview is display only, never data source"""
        # GIVEN: Complete context flow
        request = GenerationRequest(
            begrip="verdachte",
            organisatorische_context=["OM", "DJI"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Art. 27 Sv"]
        )

        # WHEN: Processing through entire pipeline
        from services.container import ServiceContainer
        container = ServiceContainer()

        # Get UI preview
        ui_preview = container.get_ui_formatter().format_preview(request)
        assert "📋 Org: OM, DJI" in ui_preview

        # Try to use UI preview as input (should fail)
        with pytest.raises(TypeError):
            container.get_prompt_service().build_from_ui_string(ui_preview)

        # Correct path: use structured data
        prompt = container.get_prompt_service().build_prompt(request)
        assert "organisatorische context: OM, DJI" in prompt

    def test_ac2_single_context_path(self):
        """AC2: Only ONE path for context processing exists"""
        # Trace all context processing paths
        import ast
        import os

        context_paths = []
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        tree = ast.parse(f.read())
                        # Find context processing functions
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                if "context" in node.name and "build" in node.name:
                                    context_paths.append(f"{filepath}:{node.name}")

        # Should only find DefinitionGeneratorContext path
        valid_paths = [p for p in context_paths
                      if "definition_generator_context" in p]
        assert len(valid_paths) > 0, "No context path found"

        # No legacy paths should exist
        legacy_paths = [p for p in context_paths
                       if "legacy" in p or "v1" in p.lower()]
        assert len(legacy_paths) == 0, f"Legacy paths still exist: {legacy_paths}"

    def test_ac3_anders_works_all_lists(self):
        """AC3: Anders... option works in all three context lists"""
        test_cases = [
            ("organisatorische_context", ["OM", "Anders...", "CustomOrg"]),
            ("juridische_context", ["Strafrecht", "Anders...", "CustomDomain"]),
            ("wettelijke_basis", ["Art. 27 Sv", "Anders...", "CustomLaw"])
        ]

        for field_name, field_value in test_cases:
            # GIVEN: Request with Anders option
            request = GenerationRequest(begrip="test")
            setattr(request, field_name, field_value)

            # WHEN: Processing
            manager = HybridContextManager()
            context = manager._build_base_context(request)

            # THEN: Custom value included, Anders removed
            context_key = field_name.replace("_context", "").replace("_basis", "")
            if context_key == "organisatorische":
                context_key = "organisatorisch"
            elif context_key == "wettelijke":
                context_key = "wettelijk"

            assert field_value[2] in context[context_key]  # Custom value
            assert "Anders..." not in context[context_key]  # Marker removed

    def test_ac4_astra_warnings_not_errors(self):
        """AC4: ASTRA validation gives warnings, never blocks"""
        # GIVEN: Mix of valid and invalid organizations
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "InvalidOrg", "DJI", "FakeOrg"]
        )

        # WHEN: Processing with logging capture
        import logging
        with self.capture_logs(logging.WARNING) as logs:
            manager = HybridContextManager()
            context = manager._build_base_context(request)

        # THEN: Warnings logged but all orgs processed
        assert len(logs) == 2  # Two invalid orgs
        assert "InvalidOrg" in str(logs)
        assert "FakeOrg" in str(logs)

        # Maar ALL organizations still in context
        assert set(context["organisatorisch"]) == {"OM", "InvalidOrg", "DJI", "FakeOrg"}
```

## Negative Tests: Preventing Regression

### Test Suite 7: Anti-Patterns That Must Always Fail

```python
# tests/test_per007_antipatterns.py
class TestAntiPatterns:
    """Tests that ensure bad patterns are permanently blocked"""

    def test_never_parse_ui_emoji_strings(self):
        """Emojis in data layer should always fail"""
        with pytest.raises(ValueError, match="Emojis not allowed in data"):
            EnrichedContext(
                base_context={"organisatorisch": ["📋 OM"]},  # Emoji in data
                sources=[], expanded_terms={},
                confidence_scores={}, metadata={}
            )

    def test_never_concatenate_then_split(self):
        """Concatenate-then-split pattern must be blocked"""
        # This anti-pattern must always fail
        data = ["OM", "DJI", "Rechtspraak"]
        concatenated = ", ".join(data)  # DON'T DO THIS

        with pytest.raises(DeprecationWarning):
            # This pattern should be detected and blocked
            split_again = concatenated.split(", ")  # Anti-pattern

    def test_never_mix_ui_and_data_logic(self):
        """UI logic in business layer must fail"""
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()

        # This should not exist or raise error
        with pytest.raises(AttributeError):
            # UI formatting doesn't belong in prompt service
            service.add_emoji_formatting({"org": ["OM"]})

    def test_never_use_string_context_field(self):
        """Legacy string context field must be ignored"""
        request = GenerationRequest(
            begrip="test",
            context="This is old string context",  # Legacy field
            organisatorische_context=["OM"]  # New structured field
        )

        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # Old string context should NOT appear anywhere
        assert "This is old string context" not in str(context)
        # Only structured data should be used
        assert context["organisatorisch"] == ["OM"]
```

## Prestaties Benchmark Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Context Processing | < 100ms | TBD | 🔴 RED |
| UI Preview Generation | < 1ms | TBD | 🔴 RED |
| Deduplication (100 items) | < 50ms | TBD | 🔴 RED |
| ASTRA Validation | < 10ms | TBD | 🔴 RED |
| End-to-end Flow | < 200ms | TBD | 🔴 RED |

## Test Execution Plan

### Phase 1: RED (Current State)
1. Run all test suites - ALL MUST FAIL
2. Document failure reasons
3. Create implementation tasks

### Phase 2: GREEN (Implementatie)
1. Implement ContextFormatter
2. Update HybridContextManager
3. Create ASTRA Validator
4. Block legacy paths
5. Run tests - ALL MUST PASS

### Phase 3: REFACTOR (Optimization)
1. Run performance benchmarks
2. Optimize slow paths
3. Remove code duplication
4. Improve error messages

### Phase 4: CONFIRM (Final Validation)
1. Run complete test suite
2. Verify performance targets met
3. Check code coverage > 95%
4. Validate architecture compliance

## Test Coverage Vereisten

- **Unit Tests**: 95% coverage of new code
- **Integration Tests**: All context flow paths
- **E2E Tests**: User scenarios from Episch Verhaal CFR
- **Prestaties Tests**: All critical paths benchmarked
- **Regression Tests**: Anti-patterns permanently blocked

## Continuous Validation

```yaml
# .github/workflows/per007-validation.yml
name: PER-007 Architecture Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check UI strings not in data layer
        run: |
          # Grep for emoji usage in non-UI files
          ! grep -r "📋\|⚖️\|📜" src/services --include="*.py"

      - name: Check single context path
        run: |
          # Count context processing paths
          paths=$(grep -r "def.*build.*context" src --include="*.py" | wc -l)
          [ "$paths" -eq 1 ] || exit 1

      - name: Run PER-007 test suite
        run: |
          pytest tests/test_per007_*.py -v --tb=short

      - name: Prestaties benchmarks
        run: |
          pytest tests/test_per007_performance.py --benchmark-only
```

## Definition of Done

✅ **All RED tests written and failing**
- [ ] UI separation tests fail (system accepts UI strings)
- [ ] Single source tests fail (multiple paths exist)
- [ ] Anders option tests fail (crashes on custom values)
- [ ] ASTRA tests fail (blocks instead of warns)

✅ **Implementatie makes all tests GREEN**
- [ ] ContextFormatter geïmplementeerd
- [ ] HybridContextManager updated
- [ ] ASTRA Validator created
- [ ] Legacy paths blocked
- [ ] All tests passing

✅ **REFACTOR improves code quality**
- [ ] Prestaties targets met
- [ ] No code duplication
- [ ] Clear separation of concerns
- [ ] Comprehensive error messages

✅ **Architecture validated**
- [ ] UI strings never used as data source
- [ ] Single context processing path
- [ ] Anders option works everywhere
- [ ] ASTRA warnings only
- [ ] Anti-patterns permanently blocked

## Risk Mitigation

| Risk | Impact | Mitigation | Test Coverage |
|------|--------|------------|---------------|
| UI string used as data | Critical | Type checking, validation | test_prompt_builder_rejects_ui_preview_string |
| Multiple context paths | High | Code analysis, deprecation | test_only_one_context_processing_path_exists |
| Anders crashes | High | Null checks, validation | test_anders_with_empty_custom_value |
| ASTRA blocks | Medium | Warning-only mode | test_invalid_org_gives_warning_not_error |
| Prestaties degradation | Medium | Benchmarks, caching | test_context_processing_under_100ms |

## Appendix: Test Data Fixtures

```python
# tests/fixtures/per007_fixtures.py
import pytest
from services.interfaces import GenerationRequest

@pytest.fixture
def valid_request():
    """Standard valid request with all context fields"""
    return GenerationRequest(
        begrip="verdachte",
        organisatorische_context=["OM", "DJI"],
        juridische_context=["Strafrecht"],
        wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv"]
    )

@pytest.fixture
def anders_request():
    """Request with Anders... custom values"""
    return GenerationRequest(
        begrip="test",
        organisatorische_context=["OM", "Anders...", "CustomOrg"],
        juridische_context=["Strafrecht", "Anders...", "NewDomain"],
        wettelijke_basis=["Art. 27 Sv", "Anders...", "Custom Law"]
    )

@pytest.fixture
def invalid_org_request():
    """Request with invalid organizations for ASTRA testing"""
    return GenerationRequest(
        begrip="test",
        organisatorische_context=["InvalidOrg", "OM", "FakeOrg", "DJI"]
    )

@pytest.fixture
def ui_preview_string():
    """Example UI preview string that must never be used as data"""
    return "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht | 📜 Wet: Art. 27 Sv"

@pytest.fixture
def legacy_request():
    """Legacy request format that should be handled gracefully"""
    return GenerationRequest(
        begrip="test",
        context="Old style context string",  # Legacy
        organisatie="OM",  # Legacy single field
        domein="Strafrecht"  # Legacy single field
    )
```

---

*This TDD test plan ensures that PER-007 implementation follows strict architecture principles with comprehensive test coverage at every phase.*
