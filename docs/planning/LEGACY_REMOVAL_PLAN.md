# Legacy Code Removal Plan
<!-- moved from project root to canonical docs location -->

## Directories marked for removal:

### 1. `/src/ai_toetser/`
- **Status**: DEPRECATED - Replaced by V2 validation
- **Dependencies**: 11 test files still reference this
- **Action**: Update tests first, then remove

### 2. `/src/analysis/`
- **Status**: DEPRECATED - Analytics moved to services
- **Dependencies**: Multiple test files
- **Action**: Migrate functionality to services layer

## Tests that need updating:
- tests/unit/test_modular_toetser.py
- tests/unit/test_ai_toetser.py
- tests/unit/test_working_system.py
- tests/integration/test_integration_comprehensive.py
- tests/integration/test_new_services_functionality.py
- tests/integration/test_legacy_vs_new_parity.py
- tests/integration/test_comprehensive_system.py
- tests/integration/test_ui_comprehensive.py
- tests/test_json_validators.py
- tests/performance/test_performance_comprehensive.py
- tests/test_regression_suite.py

## Recommended approach:
1. Create new test files for V2 validation
2. Update imports in existing tests
3. Remove legacy directories after all tests pass

## Timeline:
- Target: Next sprint
- Estimate: 4-6 hours for complete removal
