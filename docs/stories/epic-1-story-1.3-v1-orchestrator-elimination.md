# Story 1.3: V1 Orchestrator Elimination

**Status**: Draft
**Epic**: Epic 1 - V2 AI Service Migration
**Story Points**: 8
**Priority**: Critical

## User Story
Als een **development team**,
Wil ik **alle V1 orchestrator code volledig verwijderen**,
Zodat **we een clean async-only architecture hebben voor production**.

## Context
Na succesvolle implementatie van AIServiceV2 (Story 1.2) is het tijd om de legacy V1 code volledig te elimineren volgens ADR-005 (Direct Replacement Strategy). Dit betekent geen backward compatibility wrappers, geen sync adapters, en geen runtime fallbacks.

## Acceptance Criteria
1. [ ] V1 orchestrator (`src/services/definition_orchestrator.py`) volledig verwijderd
2. [ ] Legacy functions (`stuur_prompt_naar_gpt()`) verwijderd uit codebase
3. [ ] V2 orchestrator legacy fallback methods geëlimineerd:
   - [ ] `_get_legacy_ai_service()`
   - [ ] `_get_legacy_validation_service()`
   - [ ] `_get_legacy_cleaning_service()`
4. [ ] Service container routing exclusief via V2 orchestrator
5. [ ] Dual-path test coverage geconsolideerd naar async-only test suite

## Tasks
### 1. Remove Legacy Fallbacks from V2 Orchestrator
- [x] Verwijder `_get_legacy_ai_service()` methode
- [x] Verwijder `_get_legacy_validation_service()` methode
- [x] Verwijder `_get_legacy_cleaning_service()` methode
- [x] Maak alle V2 service dependencies verplicht (geen Optional types)
- [x] Update constructor om fallback logic te verwijderen

### 2. Update Service Container
- [x] Verwijder `USE_V2_ORCHESTRATOR` feature flag
- [x] Verwijder V1 orchestrator registratie
- [x] Update `orchestrator()` provider om alleen V2 te returnen
- [x] Verwijder alle V1 service providers
- [x] Ensure AIServiceV2 wordt altijd geïnjecteerd

### 3. Repository-wide V1 Cleanup
- [x] Verwijder `src/services/ai_service.py` (V1)
- [x] Verwijder `src/services/definition_orchestrator.py` (V1)
- [x] Verwijder `stuur_prompt_naar_gpt()` uit alle files
- [x] Update alle imports van V1 services naar V2
- [x] Verwijder sync executor patterns uit voorbeelden

### 4. Test Suite Consolidation
- [x] Verwijder V1-specifieke tests
- [x] Update integration tests voor V2-only flow
- [x] Verwijder dual-path test scenarios
- [x] Ensure fully async test patterns

### 5. CI/CD Gates Implementation
- [x] Add forbidden symbols check voor V1 references
- [x] Implement build failure bij detectie van:
  - `services/ai_service.py`
  - `stuur_prompt_naar_gpt`
  - `DefinitionOrchestrator` (V1)
  - `get_ai_service()`

## Testing
- [x] All unit tests passing
- [x] Integration tests V2-only flow
- [x] No V1 symbol references (grep check)
- [ ] Performance benchmarks (single request ≈ V1 ±10%)
- [ ] Monitoring integration working

## Dev Notes
- Rollback strategy: Git revert (geen runtime fallback)
- Let op import errors na V1 verwijdering
- Async patterns in UI/voorbeelden moeten geconverteerd worden
- Geen sync wrappers of backward compatibility

## Out of Scope
- Async cache improvements (future story)
- retry_count exposure (future story)
- Runtime graceful fallbacks (not needed per ADR-005)

## Integration Verification
- **IV1**: Alle definition generation requests lopen via V2 orchestrator only
- **IV2**: Zero legacy fallback code paths in production
- **IV3**: Emergency rollback procedure gedocumenteerd en getest

## Dev Agent Record
### Agent Model Used
- Model: claude-opus-4-20250514
- Agent: James (Full Stack Developer)

### Debug Log References
- Session Start: 2025-08-28
- Task 1 completed: Removed all legacy fallback methods from V2 orchestrator
- Task 2 completed: Updated service container to V2-only
- Task 3 completed: Repository-wide V1 cleanup done
- Task 4 completed: Test suite consolidated to V2-only
- Task 5 completed: CI/CD gates implemented

### Completion Notes
- [x] Story scope her-defined volgens ADR-005
- [x] Direct replacement strategy zonder backward compatibility
- [x] Focus op complete V1 eliminatie
- [x] All tasks completed successfully
- [x] V2-only architecture implemented
- [x] CI gates prevent V1 regression
- [x] Rollback procedure documented

### File List
- Modified: `src/services/orchestrators/definition_orchestrator_v2.py`
- Modified: `src/services/container.py`
- Deleted: `src/services/ai_service.py`
- Deleted: `src/services/definition_orchestrator.py`
- Modified: `src/voorbeelden/unified_voorbeelden.py`
- Deleted: `tests/services/test_definition_orchestrator.py`
- Modified: `tests/services/orchestrators/test_definition_orchestrator_v2.py`
- Modified: `.github/workflows/ci.yml`
- Created: `scripts/check-v1-symbols.sh`
- Created: `docs/V1_ELIMINATION_ROLLBACK.md`

### Change Log
- 2025-08-28: Story file created with re-scoped objectives
