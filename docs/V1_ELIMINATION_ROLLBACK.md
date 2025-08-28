# V1 Orchestrator Elimination - Rollback Procedure

## Overview
This document describes the rollback procedure in case issues arise after the V1 orchestrator elimination (Story 1.3).

## Rollback Strategy
As per ADR-005, we use a **Direct Replacement Strategy** with no runtime fallbacks. Therefore, rollback is achieved through Git revert.

## Emergency Rollback Steps

1. **Identify the commit to revert to**:
   ```bash
   # Find the commit before V1 elimination
   git log --oneline | grep -B5 "V1 orchestrator elimination"
   ```

2. **Create a rollback branch**:
   ```bash
   git checkout -b emergency/rollback-v1-elimination
   ```

3. **Revert the changes**:
   ```bash
   # Revert the merge commit that introduced V1 elimination
   git revert <commit-hash>
   ```

4. **Restore deleted files**:
   ```bash
   # Restore V1 files
   git checkout <previous-commit> -- src/services/ai_service.py
   git checkout <previous-commit> -- src/services/definition_orchestrator.py
   git checkout <previous-commit> -- tests/services/test_definition_orchestrator.py
   ```

5. **Disable CI gates temporarily**:
   ```bash
   # Comment out the V1 symbol check in CI
   # Edit .github/workflows/ci.yml and comment out step 8
   ```

6. **Test the rollback**:
   ```bash
   # Run tests
   python -m pytest

   # Verify V1 orchestrator works
   python -m pytest tests/services/test_definition_orchestrator.py
   ```

7. **Deploy rollback**:
   ```bash
   # Create PR for rollback
   git push origin emergency/rollback-v1-elimination
   # Create emergency PR with title: "EMERGENCY: Rollback V1 elimination"
   ```

## Files Affected by V1 Elimination

### Deleted Files:
- `src/services/ai_service.py`
- `src/services/definition_orchestrator.py`
- `tests/services/test_definition_orchestrator.py`

### Modified Files:
- `src/services/orchestrators/definition_orchestrator_v2.py` (removed fallbacks)
- `src/services/container.py` (V2-only configuration)
- `src/voorbeelden/unified_voorbeelden.py` (V2 imports)
- `tests/services/orchestrators/test_definition_orchestrator_v2.py` (async mocks)
- `.github/workflows/ci.yml` (V1 prevention gates)

## Post-Rollback Actions

1. **Investigate root cause**
2. **Re-enable feature flag** (if needed for gradual rollout):
   ```python
   # In src/services/container.py, temporarily add:
   use_v2_orchestrator = os.getenv("USE_V2_ORCHESTRATOR", "false").lower() == "true"
   ```
3. **Plan fix for V2 orchestrator**
4. **Schedule re-deployment** with fixes

## Prevention Measures

To prevent future rollback needs:
1. Extensive testing in staging environment
2. Gradual rollout with feature flags (future stories)
3. Monitor error rates closely post-deployment
4. Have V2-specific dashboards ready

## Contact

For emergency assistance:
- Development Team Lead
- DevOps Team
- Architecture Team (for ADR-005 questions)
