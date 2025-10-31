# DEF-54: Simplified & Safer Dual Repository Elimination Plan

**Date**: 2025-10-29
**Status**: PROPOSED (Safer Alternative to Original 5-Phase Plan)
**Risk Level**: LOW → MEDIUM (reduced from original MEDIUM)
**Timeline**: 7-10 phases, 6-8 days (vs original 5 phases, 5 days)

---

## Executive Summary

**PROBLEM**: Current 5-phase plan merges 500+ lines at once (Phase 2), high blast radius if issues occur, difficult rollback.

**SOLUTION**: 10-phase Strangler Pattern with method-by-method migration:
- Each phase touches 50-150 lines (not 500+)
- Each phase is independently committable
- Each phase can be rolled back without affecting others
- Feature flag enables instant rollback without git operations
- Schema changes decoupled from code changes

**KEY IMPROVEMENTS**:
1. **Incremental**: 10 smaller phases vs 5 large phases
2. **Safer**: Feature flag for instant rollback
3. **Testable**: Write tests BEFORE each merge
4. **Documented**: Migration guide + architecture docs updated inline
5. **Pragmatic**: No over-engineering, just safer execution

---

## BEFORE → AFTER Metrics

| Metric | Original Plan | Simplified Plan | Benefit |
|--------|---------------|-----------------|---------|
| **Largest Single Change** | 500+ lines | ~150 lines | 70% smaller blast radius |
| **Phases** | 5 phases | 10 phases | 2x more granular |
| **Rollback Strategy** | Git revert only | Feature flag + git | Instant rollback |
| **Test Strategy** | Test after merge | Test-first each phase | Confidence before commit |
| **Schema Changes** | Mixed with code | Separate phase (0) | Decouple data from code |
| **Callsite Updates** | 23 files at once | 3-5 files per phase | Easier debugging |
| **Documentation** | After completion | Inline with phases | Always up-to-date |

---

## Core Principles

### 1. **Strangler Pattern** (Not Big-Bang)
- Keep BOTH repositories temporarily
- Migrate callsites one-by-one
- Delete legacy only when 0 callsites remain
- **Trade-off**: Longer timeline, but MUCH safer

### 2. **Feature Flag Strategy**
Even though solo user, use environment flag:
```python
USE_LEGACY_REPO = os.getenv("USE_LEGACY_REPO", "false") == "true"
```
**Benefit**: Instant rollback without git, just flip env var

### 3. **Test-First Per Phase**
1. Write NEW tests for merged functionality FIRST
2. Ensure they FAIL with current implementation
3. Implement merge to make tests PASS
4. Old tests should also still pass

### 4. **Database Schema First**
Schema changes FIRST (separate PR) before code refactor:
- Does DefinitieRecord have fields that Definition doesn't?
- Do we need ALTER TABLE migrations?
- **Benefit**: Decouple data structure from code refactor

### 5. **Document As You Go**
Update docs inline with each phase:
- CLAUDE.md architecture section
- Architecture diagrams
- API documentation
- **Benefit**: Future-you will thank you

---

## ALTERNATIVE PLAN: 10-Phase Incremental Migration

### PHASE 0: Schema Validation & Preparation (0.5 days)
**Goal**: Ensure database schema is ready for merged repository

**Tasks**:
- [ ] Compare DefinitieRecord vs Definition fields
- [ ] Identify any missing columns in `definities` table
- [ ] Run ALTER TABLE migrations if needed
- [ ] Add database indexes for performance (if missing)
- [ ] **TEST**: Smoke test that schema changes don't break existing code

**Deliverable**: Schema migration script (if needed), schema verification test

**Risk**: LOW (read-only analysis + backwards-compatible schema changes)

**Rollback**: N/A (schema changes are additive, not destructive)

---

### PHASE 1: Feature Flag Infrastructure (0.5 days)
**Goal**: Add safety mechanism for instant rollback

**Tasks**:
- [ ] Add `USE_LEGACY_REPO` environment variable support
- [ ] Update ServiceContainer to respect flag
- [ ] Document flag in CLAUDE.md and .env.example
- [ ] **TEST**: Verify flag toggles between repositories correctly

**Code Change** (~50 lines):
```python
# src/services/container.py
def _create_definition_repository(self) -> DefinitionRepositoryInterface:
    if os.getenv("USE_LEGACY_REPO", "false") == "true":
        # Fallback to legacy wrapper
        from services.definition_repository import DefinitionRepository
        return DefinitionRepository(self.db_path)
    else:
        # Use merged repository (default)
        from database.definitie_repository import DefinitieRepositoryV2
        return DefinitieRepositoryV2(self.db_path)
```

**Risk**: LOW (additive change, doesn't modify existing code)

**Rollback**: Set `USE_LEGACY_REPO=true` in environment

---

### PHASE 2: Core CRUD Tests (Test-First) (1 day)
**Goal**: Write comprehensive tests BEFORE merging methods

**Tasks**:
- [ ] Write tests for `save()` (create + update paths)
- [ ] Write tests for `get()` and `search()`
- [ ] Write tests for `delete()` and `hard_delete()`
- [ ] Write tests for `find_by_begrip()`
- [ ] Write tests for `get_by_status()`
- [ ] **Ensure tests FAIL** with current implementation
- [ ] Document expected behavior in test docstrings

**Deliverable**: `tests/database/test_definitie_repository_v2_crud.py` (~300 lines)

**Risk**: NONE (tests only, no production code changes)

**Rollback**: N/A (tests can be deleted if needed)

---

### PHASE 3a: Merge Core CRUD Methods (1 day)
**Goal**: Migrate basic persistence operations to legacy repository

**Methods to Migrate** (~226 lines total):
- ✅ `save()` → Already exists as `create_definitie()` + `update_definitie()`
- ✅ `get()` → Already exists as `get_definitie()`
- ✅ `search()` → Already exists as `search_definities()`
- ✅ `delete()` → Map to `change_status(ARCHIVED)`
- ✅ `hard_delete()` → New method in legacy repo
- ✅ `find_by_begrip()` → Already exists as `find_definitie()`

**Tasks**:
- [ ] Copy missing methods to `definitie_repository.py`
- [ ] Add type conversion helpers (`_definition_to_record`, `_record_to_definition`)
- [ ] Update callsites in ServiceContainer only (1 file)
- [ ] Run Phase 2 tests → Should PASS
- [ ] Run full test suite → Should PASS

**Risk**: LOW (well-tested CRUD, small scope)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 3b: Migrate Duplicate Detection (1 day)
**Goal**: Move duplicate finding logic to legacy repository

**Methods to Migrate** (~112 lines):
- ✅ `find_duplicates()` → Already exists in legacy repo
- ✅ `set_duplicate_service()` → Dependency injection for DuplicateDetectionService

**Tasks**:
- [ ] Write tests for duplicate detection FIRST
- [ ] Update `find_duplicates()` to use injected service (if available)
- [ ] Update callsites in validation services (3 files)
- [ ] Verify duplicate detection still works end-to-end

**Risk**: LOW (isolated functionality, existing tests)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 3c: Migrate Status & Draft Management (1 day)
**Goal**: Move status management and draft creation

**Methods to Migrate** (~185 lines):
- ✅ `get_by_status()` → Already exists in legacy repo
- ✅ `get_or_create_draft()` → New method in legacy repo
- ✅ `change_status()` → Already exists in legacy repo

**Tasks**:
- [ ] Write tests for draft creation FIRST
- [ ] Add `get_or_create_draft()` to legacy repo
- [ ] Update callsites in UI tabs (5 files)
- [ ] Verify draft workflow end-to-end

**Risk**: MEDIUM (complex business logic, affects UI)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 4: Migrate Voorbeelden (Examples) Management (1 day)
**Goal**: Move example management to legacy repository

**Methods to Migrate** (~150 lines):
- ✅ `save_voorbeelden()` → Already exists in legacy repo (1,453-1,680)
- ✅ `get_voorbeelden()` → Already exists in legacy repo (1,680-1,759)
- ✅ `get_voorbeelden_by_type()` → Already exists in legacy repo (1,759-1,779)

**Tasks**:
- [ ] Write tests for voorbeelden CRUD FIRST
- [ ] Verify synonym sync logic (`_sync_synonyms_to_registry`)
- [ ] Update callsites in UI helpers (2 files)
- [ ] Test example editing workflow end-to-end

**Risk**: MEDIUM (complex synonym sync logic)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 5: Eliminate Type Conversions (1 day)
**Goal**: Remove conversion layer between Definition ↔ DefinitieRecord

**Tasks**:
- [ ] Identify all callsites using Definition interface (23 files)
- [ ] Update callsites to use DefinitieRecord directly
- [ ] Remove `_definition_to_record()` and `_record_to_definition()` helpers
- [ ] Update DefinitionRepositoryInterface to use DefinitieRecord
- [ ] Run full test suite

**Risk**: HIGH (touches 23 files, affects entire codebase)

**Rollback**: Set `USE_LEGACY_REPO=true`, revert interface changes

**ALTERNATIVE**: Keep conversions if they provide value (don't dogmatically eliminate)

---

### PHASE 6a: Update Callsites - Batch 1 (UI Tabs) (0.5 days)
**Goal**: Migrate 5 UI tab files to use merged repository

**Files** (5 files):
- `src/ui/components/definition_generator_tab.py`
- `src/ui/components/definition_edit_tab.py`
- `src/ui/components/expert_review_tab.py`
- `src/ui/components/tabs/import_export_beheer/orchestrator.py`
- `src/ui/components/tabs/import_export_beheer/database_manager.py`

**Tasks**:
- [ ] Update imports to use `definitie_repository`
- [ ] Test each tab manually in Streamlit
- [ ] Run UI smoke tests
- [ ] Verify no regressions

**Risk**: LOW (UI-only changes, easy to test manually)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 6b: Update Callsites - Batch 2 (Services) (0.5 days)
**Goal**: Migrate 8 service files to use merged repository

**Files** (8 files):
- `src/services/orchestrators/definition_orchestrator_v2.py`
- `src/services/export_service.py`
- `src/services/definition_import_service.py`
- `src/services/data_aggregation_service.py`
- `src/services/definition_edit_repository.py`
- `src/services/workflow_service.py`
- `src/services/definition_workflow_service.py`
- `src/services/category_service.py`

**Risk**: MEDIUM (core business logic, requires thorough testing)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 6c: Update Callsites - Batch 3 (Tools & Utils) (0.5 days)
**Goal**: Migrate remaining files (tools, utils, validation rules)

**Files** (~10 files):
- `src/tools/setup_database.py`
- `src/tools/definitie_manager.py`
- `src/integration/definitie_checker.py`
- `src/toetsregels/validators/CON_01.py`
- `src/toetsregels/regels/DUP_01.py`
- `src/toetsregels/regels/CON-01.py`
- `src/ui/helpers/examples.py`
- `src/ui/services/definition_ui_service.py`
- `src/utils/container_manager.py`

**Risk**: LOW (peripheral files, limited impact)

**Rollback**: Set `USE_LEGACY_REPO=true`

---

### PHASE 7: Delete Legacy Wrapper (0.5 days)
**Goal**: Remove `src/services/definition_repository.py`

**Prerequisites**:
- ✅ All 31 callsites migrated to legacy repository
- ✅ All tests passing
- ✅ Manual smoke tests completed
- ✅ Feature flag set to `USE_LEGACY_REPO=false` for 2+ days without issues

**Tasks**:
- [ ] Verify 0 imports of `services.definition_repository`
- [ ] Delete `src/services/definition_repository.py` (887 lines)
- [ ] Remove feature flag infrastructure (Phase 1 code)
- [ ] Update CLAUDE.md to document new architecture
- [ ] Run full test suite + smoke tests

**Risk**: LOW (all callsites already migrated)

**Rollback**: Git revert (feature flag already removed)

---

### PHASE 8: Code Quality Improvements (1 day)
**Goal**: Simplify merged repository after elimination

**Opportunities** (from complexity analysis):
1. **Extract SQL Query Builders**
   - `_build_insert_columns()` is complex (lines 350-419)
   - Extract into `database/sql_builder.py` module

2. **Consolidate Error Handling**
   - Duplicate error handling in `create_definitie()` and `update_definitie()`
   - Extract into `_handle_db_error()` helper

3. **Simplify Type Signatures**
   - Remove `| None` from return types where possible
   - Use `Optional[]` consistently

4. **Extract Validation Logic**
   - `_calculate_similarity()` belongs in validation service, not repository
   - Move to `services/duplicate_detection_service.py`

**Tasks**:
- [ ] Apply DRY principle to error handling
- [ ] Extract SQL builders
- [ ] Move validation logic to services
- [ ] Simplify type signatures
- [ ] Add docstrings for complex methods

**Risk**: LOW (refactoring only, behavior unchanged)

**Rollback**: Git revert

---

### PHASE 9: Documentation & Migration Guide (0.5 days)
**Goal**: Update all documentation to reflect new architecture

**Tasks**:
- [ ] Update `CLAUDE.md` - Remove dual repository references
- [ ] Update `docs/architectuur/ENTERPRISE_ARCHITECTURE.md`
- [ ] Update `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- [ ] Update `docs/architectuur/TECHNICAL_ARCHITECTURE.md`
- [ ] Create `docs/guides/REPOSITORY_MIGRATION_GUIDE.md` for future developers
- [ ] Update API documentation (if exists)
- [ ] Archive this plan in `docs/archief/refactors/DEF-54/`

**Risk**: NONE (documentation only)

**Rollback**: N/A

---

## Complexity Hotspot Analysis

### 🔴 HIGH COMPLEXITY (Refactor BEFORE merging)

**1. `save_voorbeelden()` (226 lines, 1453-1680)**
- **Problem**: God method, too many responsibilities
- **Complexity**: Handles insert, update, duplicate checks, synonym sync
- **Recommendation**:
  - Extract `_sync_synonyms_to_registry()` FIRST (Phase 4 prerequisite)
  - Extract `_validate_voorbeeld_data()` helper
  - Extract `_insert_voorbeeld()` and `_update_voorbeeld()` helpers
- **Benefit**: Easier to test, easier to debug

**2. `_sync_synonyms_to_registry()` (185 lines, implied)**
- **Problem**: Complex business logic buried in repository
- **Complexity**: Bidirectional sync, conflict resolution
- **Recommendation**:
  - Move to `services/synonym_service.py` (belongs in business layer)
  - Repository should just call `synonym_service.sync()`
- **Benefit**: Separation of concerns, testable in isolation

**3. Type Conversion Logic (186 lines total)**
- **Problem**: Adapter pattern adds indirection
- **Complexity**: `_definition_to_record()`, `_record_to_definition()`, `_definition_to_updates()`
- **Recommendation**:
  - **Keep conversions** if they provide value (domain model vs data model)
  - **Delete conversions** if DefinitieRecord can serve as domain model
  - **Decision point**: Phase 5 - measure cognitive load before deciding
- **Benefit**: Simpler if removed, but may lose domain model benefits

---

## Safety Enhancements

### 1. Feature Flag (Phase 1)
```bash
# Instant rollback without git
export USE_LEGACY_REPO=true
streamlit run src/main.py
```

### 2. Schema Decoupling (Phase 0)
- Schema changes FIRST (separate PR)
- Code changes can't break if schema is ready

### 3. Test-First Approach (Phase 2)
- Write tests BEFORE merging methods
- Tests fail → implement → tests pass
- Old tests still pass (regression safety)

### 4. Batch Callsite Updates (Phases 6a-6c)
- 3-5 files per batch, not 23 at once
- Easier debugging if issues occur
- Each batch is committable

### 5. Manual Verification Beyond Tests
After each phase:
- [ ] Run app manually
- [ ] Test full user workflow (generate → validate → export)
- [ ] Load test with 100 definitions (if applicable)
- [ ] Smoke test all UI tabs

---

## Quick Wins (Code Quality)

**Can be simplified DURING merge:**

### 1. Remove Duplicate Error Handling
**Before** (duplicated in `create_definitie` and `update_definitie`):
```python
except sqlite3.IntegrityError as e:
    if "UNIQUE constraint" in str(e):
        raise ValueError(f"Definitie '{begrip}' bestaat al")
    # ... more error handling
```

**After** (extracted to helper):
```python
def _handle_db_error(self, e: Exception, begrip: str, operation: str):
    """Centralized error handling for database operations."""
    if isinstance(e, sqlite3.IntegrityError):
        if "UNIQUE constraint" in str(e):
            raise ValueError(f"Definitie '{begrip}' bestaat al")
        # ... more error handling
```

### 2. Extract SQL Query Builders
**Before** (inline SQL in methods):
```python
cursor.execute("""
    INSERT INTO definities (begrip, definitie, categorie, ...)
    VALUES (?, ?, ?, ...)
""", (record.begrip, record.definitie, ...))
```

**After** (extracted to builder):
```python
from database.sql_builder import build_insert_query
query, params = build_insert_query("definities", record)
cursor.execute(query, params)
```

### 3. Consolidate Validation Logic
**Before** (in repository):
```python
def _calculate_similarity(self, str1: str, str2: str) -> float:
    """Calculate Levenshtein similarity"""
    # ... complex logic
```

**After** (moved to service):
```python
from services.duplicate_detection_service import calculate_similarity
similarity = calculate_similarity(str1, str2)
```

---

## Verification Beyond Tests

### Manual Smoke Tests (After Each Phase)
1. **Generate Definition**
   - Input: "Burger"
   - Verify: Definition generated, validation runs, save to DB works

2. **Edit Definition**
   - Load existing definition
   - Edit definitie text
   - Verify: Update persists, history tracked

3. **Export Definitions**
   - Select 10 definitions
   - Export to CSV, Excel, Markdown
   - Verify: Files created, data correct

4. **Import Definitions**
   - Import sample CSV
   - Verify: Duplicates detected, data imported correctly

5. **Full Workflow**
   - Generate → Validate → Edit → Export → Import
   - Verify: No errors, data persists correctly

### Load Testing (Phase 7)
- Create 100 test definitions
- Measure save time (should be <5s total)
- Measure search time (should be <200ms)
- Verify no memory leaks (check `st.session_state` size)

---

## Risk Assessment Per Phase

| Phase | Risk | Lines Changed | Files Changed | Rollback Ease | Blast Radius |
|-------|------|---------------|---------------|---------------|--------------|
| 0: Schema | LOW | ~50 | 1 | Easy (additive) | Minimal |
| 1: Feature Flag | LOW | ~50 | 2 | Instant (env var) | Minimal |
| 2: Tests | NONE | ~300 | 1 | N/A | None |
| 3a: CRUD | LOW | ~226 | 2 | Instant (flag) | Small |
| 3b: Duplicates | LOW | ~112 | 4 | Instant (flag) | Small |
| 3c: Status | MEDIUM | ~185 | 6 | Instant (flag) | Medium |
| 4: Voorbeelden | MEDIUM | ~150 | 3 | Instant (flag) | Medium |
| 5: Conversions | HIGH | ~186 | 23 | Hard (revert) | Large |
| 6a: UI Tabs | LOW | ~50 | 5 | Instant (flag) | Small |
| 6b: Services | MEDIUM | ~80 | 8 | Instant (flag) | Medium |
| 6c: Utils | LOW | ~40 | 10 | Instant (flag) | Small |
| 7: Delete Legacy | LOW | -887 | 1 | Easy (git) | Minimal |
| 8: Code Quality | LOW | ~100 | 3 | Easy (git) | Minimal |
| 9: Docs | NONE | ~200 | 5 | N/A | None |

**Total Timeline**: 7-10 phases, 6-8 days (vs original 5 phases, 5 days)
**Total Risk**: MEDIUM (vs original MEDIUM, but with more safety mechanisms)

---

## Success Metrics

### Functional Metrics
- ✅ All 31 callsites migrated to legacy repository
- ✅ All existing tests passing (100% pass rate)
- ✅ No regressions in manual smoke tests
- ✅ Legacy wrapper deleted (887 lines removed)
- ✅ Code quality improved (DRY, separation of concerns)

### Quality Metrics
- ✅ Test coverage maintained or improved (>80% for repository)
- ✅ Cyclomatic complexity reduced (target: <10 per method)
- ✅ Documentation updated (CLAUDE.md + architecture docs)
- ✅ No new TODO/FIXME comments introduced

### Performance Metrics
- ✅ Save time <5s (unchanged from before)
- ✅ Search time <200ms (unchanged from before)
- ✅ Memory usage stable (no leaks in `st.session_state`)

---

## Decision Points

### Should We Keep Type Conversions? (Phase 5)

**Arguments FOR keeping**:
- Separation of domain model (Definition) from data model (DefinitieRecord)
- Business logic works with clean Definition interface
- Repository can evolve schema without affecting services

**Arguments AGAINST keeping**:
- Adds indirection (186 lines of conversion code)
- Performance overhead (serialization/deserialization)
- Cognitive load (two models to understand)

**Recommendation**:
- **Measure first**: Track how often services need Definition vs DefinitieRecord
- **Decide later**: Phase 5 is optional, can skip if conversions provide value
- **Pragmatic approach**: Keep if used >10 places, delete if <5 places

---

## Lessons Learned (Post-Completion)

*(To be filled after completion)*

### What Went Well
- [ ] Feature flag saved us from rollback
- [ ] Test-first approach caught bugs early
- [ ] Incremental phases easier to debug

### What Went Wrong
- [ ] Phase X took longer than expected because...
- [ ] Missed edge case in Phase Y...

### Improvements for Next Time
- [ ] Better estimation for complex phases
- [ ] More manual testing before commit

---

## Appendix A: Original 5-Phase Plan Comparison

| Aspect | Original Plan | Simplified Plan | Winner |
|--------|---------------|-----------------|--------|
| **Phase Count** | 5 phases | 10 phases | Simplified (more granular) |
| **Largest Change** | 500+ lines | ~226 lines | Simplified (56% smaller) |
| **Rollback** | Git only | Feature flag + git | Simplified (instant) |
| **Testing** | After merge | Test-first | Simplified (confidence) |
| **Schema** | Mixed | Separate phase | Simplified (decoupled) |
| **Timeline** | 5 days | 6-8 days | Original (faster) |
| **Risk** | MEDIUM | MEDIUM (with safeguards) | Simplified (safer) |

**Verdict**: Simplified plan trades 1-3 extra days for significantly more safety and rollback ease.

---

## Appendix B: Callsite Inventory

**Total**: 31 files importing repository

### UI Layer (10 files)
- `src/ui/tabbed_interface.py`
- `src/ui/components/tabs/import_export_beheer/orchestrator.py`
- `src/ui/components/tabs/import_export_beheer/format_exporter.py`
- `src/ui/components/tabs/import_export_beheer/database_manager.py`
- `src/ui/components/tabs/import_export_beheer/csv_importer.py`
- `src/ui/components/tabs/import_export_beheer/bulk_operations.py`
- `src/ui/components/expert_review_tab.py`
- `src/ui/components/definition_generator_tab.py`
- `src/ui/components/definition_edit_tab.py`
- `src/ui/helpers/examples.py`

### Service Layer (12 files)
- `src/services/orchestrators/definition_orchestrator_v2.py`
- `src/services/definition_repository.py` (wrapper to delete)
- `src/services/export_service.py`
- `src/services/definition_import_service.py`
- `src/services/container.py`
- `src/services/data_aggregation_service.py`
- `src/services/definition_edit_repository.py`
- `src/services/workflow_service.py`
- `src/services/definition_workflow_service.py`
- `src/services/category_service.py`
- `src/services/null_repository.py`
- `src/ui/services/definition_ui_service.py`

### Data Layer (1 file)
- `src/database/definitie_repository.py` (target for merge)

### Tools & Utils (4 files)
- `src/tools/setup_database.py`
- `src/tools/definitie_manager.py`
- `src/integration/definitie_checker.py`
- `src/utils/container_manager.py`

### Validation Rules (4 files)
- `src/toetsregels/validators/CON_01.py`
- `src/toetsregels/regels/DUP_01.py`
- `src/toetsregels/regels/CON-01.py`
- `src/services/interfaces.py`

---

## Appendix C: Code Complexity Metrics

### Before Merge

**Legacy Repository** (`src/database/definitie_repository.py`):
- Lines: 2,100
- Methods: 40+
- Cyclomatic Complexity: High (some methods >15)
- Test Coverage: ~85%

**Service Wrapper** (`src/services/definition_repository.py`):
- Lines: 887
- Methods: 25
- Cyclomatic Complexity: Medium (mostly <10)
- Test Coverage: ~90%

**Total**: 2,987 lines (with duplication)

### After Merge (Target)

**Merged Repository** (`src/database/definitie_repository.py`):
- Lines: ~2,200 (2,100 + 100 new methods - 100 duplicates)
- Methods: 45+
- Cyclomatic Complexity: Medium (target <10 per method after Phase 8)
- Test Coverage: >85%

**Reduction**: -787 lines (26% reduction from 2,987 to 2,200)

---

## Appendix D: Testing Strategy

### Unit Tests (Per Phase)

**Phase 2: Core CRUD Tests**
```python
# tests/database/test_definitie_repository_v2_crud.py

def test_save_create_new_definition():
    """Test creating a new definition."""
    repo = DefinitieRepositoryV2()
    definition = Definition(begrip="Test", definitie="Test def")

    definition_id = repo.save(definition)

    assert definition_id > 0
    saved = repo.get(definition_id)
    assert saved.begrip == "Test"

def test_save_update_existing_definition():
    """Test updating an existing definition."""
    # ... similar pattern
```

### Integration Tests (After Each Phase)

**End-to-End Workflow Test**
```python
def test_full_definition_workflow():
    """Test complete workflow: create → edit → validate → export."""
    # 1. Create
    definition = create_definition("Burger")

    # 2. Edit
    definition.definitie = "Updated definition"
    update_definition(definition)

    # 3. Validate
    results = validate_definition(definition)
    assert results.is_valid

    # 4. Export
    exported = export_to_csv([definition])
    assert len(exported) > 0
```

### Manual Smoke Tests (Checklist)

After each phase, execute:
- [ ] Start app: `streamlit run src/main.py`
- [ ] Generate definition for "Burger"
- [ ] Edit definition text
- [ ] Run validation
- [ ] Export to CSV
- [ ] Import CSV back
- [ ] Check no errors in console

---

## Appendix E: Rollback Procedures

### Immediate Rollback (Feature Flag)
```bash
# Set environment variable
export USE_LEGACY_REPO=true

# Restart Streamlit
streamlit run src/main.py
```
**Time**: <30 seconds
**Risk**: None
**Use When**: Phase 1-6c, immediate issues detected

### Git Rollback (Revert Commit)
```bash
# Find commit to revert
git log --oneline -n 10

# Revert specific commit
git revert <commit-hash>

# Or reset to previous state
git reset --hard HEAD~1
```
**Time**: <2 minutes
**Risk**: Low (if no conflicts)
**Use When**: Phase 7-9, after feature flag removed

### Database Rollback (Schema Changes)
```bash
# Restore from backup (if schema changed)
cp data/definities.db.backup data/definities.db

# Or run migration rollback script
python src/database/migrate_database.py --rollback
```
**Time**: <1 minute
**Risk**: Medium (data loss if no backup)
**Use When**: Phase 0, schema changes cause issues

---

## Sign-Off

**Prepared By**: Code Simplifier (Claude)
**Date**: 2025-10-29
**Review Status**: PENDING
**Approved By**: _(Solo developer - self-approve after review)_

**Next Steps**:
1. Review this simplified plan
2. Compare with original 5-phase plan
3. Decide which approach to use
4. Create feature branch: `feature/DEF-54-simplified`
5. Start with Phase 0 (Schema Validation)

---

**END OF SIMPLIFIED REFACTOR PLAN**
