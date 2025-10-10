# Data Integrity Fix: Idempotent add_group_member()

**Date**: 2025-10-10
**Issue**: ERROR - Member 'oproeping' bestaat al in groep 7 (ID: 29)
**Root Cause**: Upstream code probeert duplicates toe te voegen, add_group_member() raised error instead of gracefully handling
**Fix**: Made add_group_member() idempotent (return existing ID instead of raising error)

## Problem Statement

The synonym sync process (`_sync_synonyms_to_registry()`) was failing with duplicate errors when trying to add the same member to a group multiple times:

```
ERROR - Member 'oproeping' bestaat al in groep 7 (ID: 29)
```

This occurred because:
1. Upstream code (definitie_repository.py) calls add_group_member() during sync
2. Due to race conditions or upstream bugs, duplicate entries could occur
3. add_group_member() raised ValueError instead of handling gracefully

## Solution

### Changed Files

1. **src/repositories/synonym_registry.py** (lines 359-473)
   - Made add_group_member() idempotent
   - Returns existing member_id if duplicate found (no error raised)
   - Logs warning for debugging when duplicate detected
   - Updated docstring to document idempotent behavior

2. **src/services/container.py** (line 412)
   - Fixed import path: `repositories.synonym_registry` → `src.repositories.synonym_registry`

3. **tests/repositories/test_synonym_registry_idempotent.py** (NEW)
   - Comprehensive test suite for idempotent behavior
   - 12 tests covering all edge cases
   - Realistic sync scenario tests
   - Cache invalidation tests

### Implementation Details

**Before (raised error on duplicate)**:
```python
existing = cursor.fetchone()
if existing:
    msg = f"Member '{term}' bestaat al in groep {group_id} (ID: {existing[0]})"
    raise ValueError(msg)
```

**After (idempotent - returns existing ID)**:
```python
existing = cursor.fetchone()
if existing:
    existing_id = existing[0]
    logger.warning(
        f"Member '{term}' already in group {group_id}, "
        f"returning existing ID {existing_id} (idempotent)"
    )
    return existing_id
```

### Behavior Changes

| Scenario | Before | After |
|----------|--------|-------|
| First add_group_member() | Creates new member | ✅ Creates new member |
| Duplicate add_group_member() | ❌ Raises ValueError | ✅ Returns existing ID |
| Empty term | ❌ Raises ValueError | ❌ Still raises ValueError (validation) |
| Invalid weight | ❌ Raises ValueError | ❌ Still raises ValueError (validation) |
| Non-existent group | ❌ Raises ValueError | ❌ Still raises ValueError (validation) |

**Key Point**: Idempotency only applies to duplicate (group_id, term) pairs. All other validation errors still raise ValueError as expected.

## Test Results

### New Tests (test_synonym_registry_idempotent.py)
```
✅ 12 tests PASSED
```

Test coverage includes:
- Idempotent behavior for duplicate adds
- No errors raised on duplicates
- Warning logged for duplicates
- Cache invalidation behavior
- Realistic sync scenarios with batch processing
- Edge cases (empty term, invalid weight, non-existent group)

### Existing Tests (regression check)
```
✅ 37 tests PASSED (test_synonym_registry_delete.py + test_synonym_registry_sql_injection.py)
```

No regressions - all existing functionality preserved.

### Smoke Test (end-to-end)
```python
registry = container.synonym_registry()
group = registry.get_or_create_group('test')
member_id1 = registry.add_group_member(group.id, 'test_term', 1.0)  # Returns: 201
member_id2 = registry.add_group_member(group.id, 'test_term', 1.0)  # Returns: 201 (idempotent)
assert member_id1 == member_id2  # ✅ PASS
```

## Impact Assessment

### Positive Impact
1. **Sync Errors Fixed**: No more "bestaat al" errors during synonym sync
2. **Data Integrity**: Prevents duplicate members in database
3. **Robustness**: Gracefully handles upstream duplicate attempts
4. **Debugging**: Warning logs help identify upstream issues
5. **Performance**: No extra database calls for duplicate checks

### No Breaking Changes
1. ✅ All existing tests pass
2. ✅ API signature unchanged
3. ✅ Return type unchanged (always returns int)
4. ✅ Validation errors still raised for invalid input

### Affected Workflows
1. **Manual Synonym Editing** (`save_voorbeelden()`)
   - Previously: Could fail with duplicate errors
   - Now: Idempotent sync, no errors

2. **Batch Synonym Processing**
   - Previously: Failed on first duplicate
   - Now: Continues processing, handles duplicates gracefully

3. **Definition Generation with Synonyms**
   - Previously: Could fail during enrichment
   - Now: Robust synonym enrichment

## Verification Steps

1. **Unit Tests**: Run `pytest tests/repositories/test_synonym_registry_idempotent.py -v`
2. **Regression Tests**: Run `pytest tests/repositories/ -v`
3. **Smoke Test**: Use container to create group + add duplicate members
4. **Integration Test**: Manual synonym editing in Streamlit UI

## Rollback Plan

If issues arise, revert commit and restore original behavior:

```python
# Revert to raising error on duplicate
existing = cursor.fetchone()
if existing:
    msg = f"Member '{term}' bestaat al in groep {group_id} (ID: {existing[0]})"
    raise ValueError(msg)
```

However, this is **NOT RECOMMENDED** as it would bring back the sync errors.

## Monitoring

Post-deployment monitoring:
1. Check logs for "already in group" warnings (indicates upstream duplicate attempts)
2. Monitor synonym sync success rate
3. Verify no duplicate members in database (DB constraint enforces this)

## Related Issues

- **Original Error**: ERROR - Member 'oproeping' bestaat al in groep 7 (ID: 29)
- **Architecture**: Synonym Orchestrator v3.1 (PHASE 3.3: Manual edit sync)
- **Related Files**:
  - `src/database/definitie_repository.py` (calls add_group_member during sync)
  - `src/repositories/synonym_registry.py` (idempotent fix)
  - `docs/architectuur/synonym-orchestrator-architecture-v3.1.md` (architecture spec)

## Conclusion

The fix successfully makes `add_group_member()` idempotent, preventing sync errors while maintaining all validation and error handling for truly invalid inputs. The implementation is well-tested, has no breaking changes, and improves system robustness.

**Status**: ✅ COMPLETE - Ready for production use
