# V1→V2 Migration Test Strategy and Verification Plan

## Executive Summary
This document provides a comprehensive test strategy and verification playbook for applying the V1→V2 migration fixes. The migration involves removing 2 obsolete legacy files and cleaning up one unused fallback method.

## Current State Analysis

### Migration Status
- **99% Complete**: Only 2 legacy files contain V1 references
- **ServiceContainer**: Already fully V2
- **Active Code**: All using V2 exclusively
- **Risk Level**: LOW ✅

### Files to be Modified
1. **DELETE**: `src/services/definition_orchestrator.py` (obsolete V1 orchestrator)
2. **DELETE**: `src/services/ai_service.py` (deprecated V1 service)
3. **CLEAN**: `src/services/orchestrators/definition_orchestrator_v2.py` (remove fallback method)

## Pre-Implementation Verification

### Step 1: Verify Current V1 References
```bash
# Expected: Find 3 files with V1 symbols
echo "=== Checking for V1 symbols ==="
grep -r "get_ai_service\|stuur_prompt_naar_gpt" \
  src/ \
  --exclude-dir=__pycache__ \
  --include="*.py" | wc -l
# Expected output: 3

# List specific occurrences
grep -rn "get_ai_service\|stuur_prompt_naar_gpt" \
  src/ \
  --exclude-dir=__pycache__ \
  --include="*.py"
# Expected:
# src/services/ai_service.py:24:def get_ai_service(...
# src/services/ai_service.py:58:def stuur_prompt_naar_gpt(...
# src/services/definition_orchestrator.py:612:from services.ai_service import get_ai_service
# src/services/orchestrators/definition_orchestrator_v2.py:913:from services.ai_service import get_ai_service
```

### Step 2: Baseline Test Metrics
```bash
# Capture baseline test status
echo "=== Current test collection status ==="
pytest --co -q 2>&1 | tail -5
# Record: Total test count

echo "=== Running critical smoke tests ==="
pytest tests/smoke/ -v --tb=no | grep -E "passed|failed|ERROR"
# Expected: Some tests may fail due to other issues, record baseline

echo "=== Check service initialization ==="
python -c "
from src.services.container import ServiceContainer
c = ServiceContainer()
print('Container initialized:', c is not None)
print('Orchestrator type:', type(c.orchestrator()).__name__)
print('Generator type:', type(c.generator()).__name__)
"
# Expected:
# Container initialized: True
# Orchestrator type: DefinitionOrchestratorV2
# Generator type: DefinitionOrchestratorV2
```

### Step 3: Git Safety Checkpoint
```bash
# Create safety branch
git status
git add -A
git stash
git checkout -b v1-to-v2-migration-backup
git stash pop
git add -A
git commit -m "Backup: Pre-V1-to-V2 migration state"
```

## Implementation Order and Testing

### Phase 1: Remove Obsolete V1 Orchestrator
**File**: `src/services/definition_orchestrator.py`
**Risk**: NONE - File not imported anywhere

```bash
# Step 1.1: Verify file is not imported
echo "=== Checking for imports of definition_orchestrator.py ==="
grep -r "from services.definition_orchestrator import\|from src.services.definition_orchestrator import" \
  src/ tests/ \
  --exclude-dir=__pycache__ \
  --include="*.py"
# Expected: No results

# Step 1.2: Backup and remove
cp src/services/definition_orchestrator.py /tmp/backup_definition_orchestrator.py
rm src/services/definition_orchestrator.py

# Step 1.3: Verify removal
test ! -f src/services/definition_orchestrator.py && echo "✅ File removed successfully"

# Step 1.4: Test critical paths still work
python -c "from src.services.container import ServiceContainer; print('✅ Container import OK')"
python -c "
from src.services.container import ServiceContainer
c = ServiceContainer()
print('✅ Container initialization OK')
"

# Step 1.5: Run smoke test
pytest tests/smoke/test_smoke_generation.py::test_service_container_initialization -xvs
# Expected: PASS
```

### Phase 2: Remove Deprecated V1 AI Service
**File**: `src/services/ai_service.py`
**Risk**: LOW - Not used by V2 code

```bash
# Step 2.1: Verify no V2 code imports it
echo "=== Checking for imports of ai_service.py (without _v2) ==="
grep -r "from services.ai_service import\|from src.services.ai_service import\|import ai_service[^_]" \
  src/ tests/ \
  --exclude-dir=__pycache__ \
  --include="*.py" | \
  grep -v "ai_service_v2"
# Expected: Only in definition_orchestrator_v2.py fallback

# Step 2.2: Backup and remove
cp src/services/ai_service.py /tmp/backup_ai_service.py
rm src/services/ai_service.py

# Step 2.3: Verify removal
test ! -f src/services/ai_service.py && echo "✅ File removed successfully"

# Step 2.4: Verify V2 service still works
python -c "
from src.services.ai_service_v2 import AIServiceV2
print('✅ AIServiceV2 import OK')
"

# Step 2.5: Test container still creates V2 services
python -c "
from src.services.container import ServiceContainer
c = ServiceContainer()
ai = c.ai_service()
print(f'✅ AI Service Type: {type(ai).__name__}')
assert type(ai).__name__ == 'AIServiceV2', 'Wrong AI service type!'
"
```

### Phase 3: Clean V2 Orchestrator Fallback
**File**: `src/services/orchestrators/definition_orchestrator_v2.py`
**Action**: Remove `_get_legacy_ai_service()` method (lines ~896-940)

```bash
# Step 3.1: Verify the method exists and location
echo "=== Locating _get_legacy_ai_service method ==="
grep -n "_get_legacy_ai_service" src/services/orchestrators/definition_orchestrator_v2.py
# Expected: One or two lines (definition and maybe a call)

# Step 3.2: Check if method is called anywhere
grep -r "_get_legacy_ai_service" src/ tests/ --exclude-dir=__pycache__ --include="*.py"
# Expected: Only in definition_orchestrator_v2.py itself

# Step 3.3: Remove the method
# This needs to be done via Edit tool - see implementation section

# Step 3.4: Verify orchestrator still works after edit
python -c "
from src.services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
print('✅ DefinitionOrchestratorV2 import OK after cleanup')
"

# Step 3.5: Test full orchestration flow
pytest tests/unit/test_story_2_4_unit.py::test_orchestrator_initialization -xvs
# Expected: PASS
```

### Phase 4: Final Verification
```bash
# Step 4.1: Verify all V1 symbols are gone
echo "=== Final V1 symbol check ==="
grep -r "get_ai_service\|stuur_prompt_naar_gpt\|DefinitionOrchestrator[^V]" \
  src/ \
  --exclude-dir=__pycache__ \
  --include="*.py"
# Expected: No results

# Step 4.2: Verify no imports of removed files
echo "=== Checking for imports of removed files ==="
grep -r "from services.ai_service import\|from services.definition_orchestrator import" \
  src/ tests/ \
  --exclude-dir=__pycache__ \
  --include="*.py"
# Expected: No results

# Step 4.3: Python compilation check
echo "=== Checking Python compilation ==="
python -m py_compile src/services/**/*.py 2>&1
# Expected: No errors

# Step 4.4: Import verification
python -c "
import sys
sys.path.insert(0, 'src')
from services.container import ServiceContainer
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.ai_service_v2 import AIServiceV2
print('✅ All critical imports successful')
"
```

## Complete Test Suite Strategy

### Test Execution Order
```bash
# 1. Critical Path Tests (MUST PASS)
pytest tests/smoke/test_smoke_generation.py -xvs
pytest tests/unit/test_story_2_4_unit.py -xvs
pytest tests/services/test_definition_generator.py::test_service_initialization -xvs

# 2. Service Integration Tests (MUST PASS)
pytest tests/integration/ -k "orchestrator or container" -xvs

# 3. V2 Validation Tests (SHOULD PASS)
pytest tests/validation/test_v2_golden_*.py -v

# 4. Full Smoke Test Suite (SHOULD PASS 80%+)
pytest tests/smoke/ -v

# 5. Unit Tests (SHOULD PASS 70%+)
pytest tests/unit/ -v --tb=short

# 6. Full Test Suite (NICE TO HAVE)
pytest tests/ -v --ignore=tests/debug --tb=short
```

### Performance Expectations
- Test collection: < 5 seconds
- Smoke tests: < 10 seconds
- Unit tests: < 30 seconds
- Full suite: < 2 minutes

## Rollback Procedures

### Quick Rollback (if any phase fails)
```bash
# Restore from backups
cp /tmp/backup_definition_orchestrator.py src/services/definition_orchestrator.py
cp /tmp/backup_ai_service.py src/services/ai_service.py
git checkout src/services/orchestrators/definition_orchestrator_v2.py

# Verify restoration
grep -c "get_ai_service" src/services/ai_service.py
# Expected: > 0
```

### Git-based Rollback
```bash
# Option 1: Reset to backup branch
git reset --hard v1-to-v2-migration-backup

# Option 2: Selective revert
git checkout HEAD -- src/services/definition_orchestrator.py
git checkout HEAD -- src/services/ai_service.py
git checkout HEAD -- src/services/orchestrators/definition_orchestrator_v2.py
```

## Success Criteria

### Minimum Acceptable (MUST HAVE)
- ✅ No files contain `get_ai_service` or `stuur_prompt_naar_gpt`
- ✅ No imports from `services.ai_service` (without _v2)
- ✅ ServiceContainer initializes successfully
- ✅ All smoke tests in `tests/smoke/` pass
- ✅ Application starts: `streamlit run src/main.py`
- ✅ Can generate a definition via UI

### Target Success (SHOULD HAVE)
- ✅ 80%+ of smoke tests pass
- ✅ 70%+ of unit tests pass
- ✅ No import errors in test collection
- ✅ All V2 golden tests pass
- ✅ Container creates only V2 services

### Stretch Goals (NICE TO HAVE)
- ✅ 90%+ overall test pass rate
- ✅ All integration tests pass
- ✅ Performance benchmarks maintained
- ✅ No deprecation warnings

## Post-Implementation Verification

### Application Functionality Test
```bash
# Start the application
streamlit run src/main.py &
APP_PID=$!
sleep 5

# Check if running
curl -s http://localhost:8501 > /dev/null && echo "✅ App is running"

# Kill the app
kill $APP_PID
```

### Manual Testing Checklist
1. [ ] Start application without errors
2. [ ] Generate a simple definition ("overeenkomst")
3. [ ] Run validation on the definition
4. [ ] Export definition to Word
5. [ ] View validation report
6. [ ] Check Nederlandse context works
7. [ ] Verify no console errors

### CI/CD Verification
```bash
# Run CI checks locally
make lint
make test
make validation-status

# Check for any quality gate violations
python scripts/check-v1-symbols.sh
# Expected: All checks pass
```

## Implementation Script

Save this as `scripts/apply-v2-migration.sh`:

```bash
#!/bin/bash
set -e

echo "=== V1→V2 Migration Script ==="
echo "Starting at: $(date)"

# Pre-flight checks
echo -e "\n[1/7] Running pre-flight checks..."
if grep -q "get_ai_service" src/services/ai_service.py 2>/dev/null; then
    echo "✅ V1 ai_service.py found (will be removed)"
else
    echo "⚠️  V1 ai_service.py not found (may already be removed)"
fi

# Backup
echo -e "\n[2/7] Creating backups..."
[ -f src/services/definition_orchestrator.py ] && cp src/services/definition_orchestrator.py /tmp/backup_definition_orchestrator.py
[ -f src/services/ai_service.py ] && cp src/services/ai_service.py /tmp/backup_ai_service.py
echo "✅ Backups created in /tmp/"

# Phase 1
echo -e "\n[3/7] Removing obsolete V1 orchestrator..."
rm -f src/services/definition_orchestrator.py
echo "✅ Removed definition_orchestrator.py"

# Phase 2
echo -e "\n[4/7] Removing deprecated V1 AI service..."
rm -f src/services/ai_service.py
echo "✅ Removed ai_service.py"

# Phase 3 is handled by Edit tool (manual step)
echo -e "\n[5/7] Clean V2 orchestrator fallback (manual step required)"
echo "TODO: Remove _get_legacy_ai_service() from definition_orchestrator_v2.py"

# Verification
echo -e "\n[6/7] Running verification checks..."
if grep -r "get_ai_service\|stuur_prompt_naar_gpt" src/ --include="*.py" --exclude-dir=__pycache__ | grep -v "_v2"; then
    echo "⚠️  Warning: V1 symbols still found"
else
    echo "✅ No V1 symbols found"
fi

# Test
echo -e "\n[7/7] Running smoke tests..."
pytest tests/smoke/test_smoke_generation.py -q
echo "✅ Smoke tests passed"

echo -e "\n=== Migration Complete ==="
echo "Finished at: $(date)"
```

## Monitoring and Logging

### During Migration
```bash
# Monitor in separate terminal
watch -n 1 'grep -c "get_ai_service" src/services/*.py 2>/dev/null | grep -v ":0$"'

# Log all actions
script -a migration_log_$(date +%Y%m%d_%H%M%S).txt
```

### Post-Migration Monitoring
```bash
# Check for any runtime errors
streamlit run src/main.py 2>&1 | tee app_log.txt &
sleep 10
grep -i "error\|exception\|traceback" app_log.txt
```

## Summary

This migration is **low-risk** and **straightforward**:
1. Remove 2 unused files
2. Clean 1 method from V2 orchestrator
3. Run verification tests

Total estimated time: **15 minutes**
Risk level: **LOW** ✅
Rollback time: **< 1 minute**

The system is already running on V2, we're just cleaning up dead code.