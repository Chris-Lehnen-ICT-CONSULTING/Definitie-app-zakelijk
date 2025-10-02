# Test Plan: ImportExportBeheer Tab Consolidatie

## Executive Summary

Dit document beschrijft de testing strategie voor de consolidatie van Export en Management tabs naar de nieuwe ImportExportBeheer tab.

**Scope Reductie**: Van 2811 naar ~400 regels code
**Tijdsinvestering**: 12-16 uur totaal
**Risk Level**: Medium (single-user app, geen productie impact)

## Test Strategie

### 1. Unit Tests (2 uur)

#### Core Functionaliteit
- [ ] CSV import parsing
- [ ] Export format generation (CSV, Excel, JSON, TXT)
- [ ] Bulk status changes
- [ ] Database statistics calculation

#### Edge Cases
- [ ] Empty CSV import
- [ ] Malformed CSV data
- [ ] Large dataset handling (>1000 records)
- [ ] Unicode/special characters in export

### 2. Integration Tests (2 uur)

#### Database Operations
- [ ] Import with duplicate detection
- [ ] Bulk update transactions
- [ ] Database reset safety checks
- [ ] Concurrent operations handling

#### Service Integration
- [ ] Lazy loading of definition service
- [ ] Fallback to dummy service
- [ ] Session state management
- [ ] Repository interactions

### 3. UI/UX Tests (1 uur)

#### Manual Testing Checklist
- [ ] Tab navigation works
- [ ] File upload component renders
- [ ] Progress bars display correctly
- [ ] Download buttons functional
- [ ] Error messages clear
- [ ] Confirmation dialogs work

#### Streamlit Specific
- [ ] Session state persists across reruns
- [ ] File uploaders reset properly
- [ ] Download buttons generate correct files
- [ ] Progress indicators update smoothly

### 4. Performance Tests (1 uur)

#### Benchmarks
- [ ] Import 100 records: < 5 seconds
- [ ] Import 1000 records: < 30 seconds
- [ ] Export 1000 records: < 3 seconds
- [ ] Memory usage: < 100MB for 10k records

#### Stress Testing
- [ ] Large CSV import (10k+ rows)
- [ ] Multiple concurrent exports
- [ ] Rapid tab switching
- [ ] Memory leak detection

### 5. Regression Tests (30 min)

#### Verify No Breaking Changes
- [ ] Existing imports still work
- [ ] Export formats unchanged
- [ ] Database structure intact
- [ ] API contracts maintained

## Test Execution Plan

### Phase 1: Pre-Migration (1 uur)
```bash
# Run existing tests to establish baseline
pytest tests/ -v --cov=src/ui/components

# Document current functionality
python scripts/analysis/analyze_test_scenarios.py
```

### Phase 2: Migration Testing (2 uur)
```bash
# Run migration in dry-run mode
python scripts/migration/consolidate_tabs_migration.py --dry-run

# Test new tab in isolation
pytest tests/integration/test_import_export_beheer_tab.py -v

# Run integration tests
pytest tests/integration/ -k "import or export" -v
```

### Phase 3: Post-Migration (1 uur)
```bash
# Full test suite
pytest tests/ -v

# Performance profiling
python -m cProfile -o profile.stats src/main.py

# Memory profiling
mprof run python src/main.py
mprof plot
```

## Test Data

### Sample CSV Files
Located in: `/samples/import/`
- `test_import_10_rows.csv` - Kleine dataset
- `test_import_100_rows.csv` - Medium dataset
- `test_import_1000_rows.csv` - Grote dataset
- `test_import_unicode.csv` - Special characters
- `test_import_malformed.csv` - Error testing

### Expected Outputs
- CSV export should match import format
- Excel export should have proper headers
- JSON export should be valid JSON
- TXT export should be human-readable

## Risk Mitigation

### High Priority Risks
1. **Data Loss During Migration**
   - Mitigation: Complete backup before migration
   - Recovery: Restore script in backup directory

2. **Import Functionality Broken**
   - Mitigation: Extensive CSV parsing tests
   - Recovery: Rollback to old tabs

3. **Export Format Changes**
   - Mitigation: Format validation tests
   - Recovery: Keep old export logic accessible

### Medium Priority Risks
1. **Performance Degradation**
   - Mitigation: Performance benchmarks
   - Recovery: Profile and optimize

2. **UI Components Not Rendering**
   - Mitigation: Manual UI testing
   - Recovery: Debug with st.echo()

## Acceptance Criteria

### Functional Requirements
- ✅ All 4 core functions work (Import, Export, Bulk, Reset)
- ✅ No data loss during operations
- ✅ Error handling present
- ✅ User feedback clear

### Non-Functional Requirements
- ✅ Code reduction achieved (>80% less code)
- ✅ Performance maintained or improved
- ✅ Memory usage reasonable
- ✅ Code maintainability improved

### Definition of Done
- [ ] All tests passing (>90% coverage on new code)
- [ ] Migration script executed successfully
- [ ] Old tabs archived properly
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] No critical bugs found

## Test Commands Summary

```bash
# Quick smoke test
pytest tests/integration/test_import_export_beheer_tab.py::TestImportFunctionality -v

# Full test suite
pytest tests/integration/test_import_export_beheer_tab.py -v --cov=src/ui/components/import_export_beheer_tab

# Performance test
python -m timeit -s "from tests.performance import test_large_import" "test_large_import()"

# Manual UI test
streamlit run src/main.py --server.headless false

# Migration dry run
python scripts/migration/consolidate_tabs_migration.py --dry-run
```

## Rollback Plan

Als tests falen:
1. Stop migration immediately
2. Run rollback: `bash backups/tab_consolidation/[timestamp]/restore.sh`
3. Verify old tabs work: `streamlit run src/main.py`
4. Analyze failure logs
5. Fix issues and retry

## Sign-off Checklist

- [ ] Developer testing complete
- [ ] Code review passed
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Backup verified
- [ ] Ready for migration

---

**Note**: Dit is een single-user development applicatie. Focus op functionaliteit en code kwaliteit, niet op productie-grade testing.