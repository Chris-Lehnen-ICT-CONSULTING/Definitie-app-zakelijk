# Story 3.1 Implementation Status

**Story**: Metadata First, Prompt Second - Web Lookup Bronnen
**Epic**: Epic 3 - Modern Web Lookup
**Status**: 🔄 IN PROGRESS
**Start Date**: 2025-09-03
**Estimated Completion**: 2025-09-03 (4-6 uur)

## Executive Summary

Story 3.1 focust op het zichtbaar maken van gebruikte bronnen in de UI tijdens preview. Het hoofdprobleem is een onnodige `LegacyGenerationResult` wrapper die metadata["sources"] breekt. We implementeren Optie B: Clean Solution door de legacy wrapper volledig te verwijderen.

## Current Implementation Progress

### ✅ Completed (0%)
- [ ] Legacy wrapper removal in service_factory.py (Optie B - Clean Solution)
- [ ] UI update voor directe V2 response handling
- [ ] Provider-neutraliteit in prompt
- [ ] Juridische citatie formatting
- [ ] UI feedback bij geen bronnen

### 🔄 In Progress
- **Legacy Wrapper Removal** (ACTIVE IMPLEMENTATION)
  - File: `src/services/service_factory.py`
  - Status: Removing LegacyGenerationResult wrapper
  - Approach: Direct V2 response return (geen wrapper meer)
  - Impact: Sources worden zichtbaar in UI preview

### 📋 Implementation Phases

#### Phase 1: Clean Solution - Remove Legacy Wrapper (2 uur)
**Impact**: HIGH - Lost hoofdprobleem permanent op
```python
# src/services/service_factory.py
# Direct V2 response returnen zonder wrapper
def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
    # ... bestaande request building ...
    return response  # GEEN LegacyGenerationResult meer!
```

#### Phase 2: Provider-Neutraliteit (30 min)
**Impact**: MEDIUM - Verbetert prompt kwaliteit
- Vervang "wikipedia:" met "Bron 1:" in prompts
- Behoud provider info in metadata voor UI

#### Phase 3: Juridische Citatie (1 uur)
**Impact**: HIGH - Juridische compliance
- Extract ECLI nummers
- Parse artikel/wet referenties
- Genereer citation_text voor UI

#### Phase 4: UI Feedback (30 min)
**Impact**: LOW - User experience
- Informatieve melding bij geen bronnen
- Badges voor autoritatieve bronnen
- Score weergave

#### Phase 5: Testing & Verificatie (1 uur)
**Impact**: CRITICAL - Quality assurance
- Preview test
- Provider neutraliteit test
- Juridische citatie test
- Determinisme test

## Technical Details

### Root Cause Analysis
- **Problem**: Sources niet zichtbaar in UI preview
- **Cause**: Onnodige `LegacyGenerationResult` wrapper
- **Impact**: `metadata["sources"]` komt niet door naar UI
- **Solution**: Direct V2 response returnen

### Architecture Alignment
- ✅ **EA**: Past bij Single Source of Truth (AD1)
- ✅ **SA**: Compatible met PromptComposer architectuur
- ✅ **TA**: Redis caching & async-first compatible
- ✅ **V2 Orchestrator**: Volledig compatible

## Acceptance Criteria Checklist

- [ ] Sources zichtbaar in UI tijdens preview
- [ ] Provider-neutraal in prompt ("Bron 1", niet "wikipedia")
- [ ] Juridische bronnen tonen citatie (art/lid/ECLI)
- [ ] Autoritatieve bronnen krijgen badge
- [ ] Bij geen bronnen: informatieve melding
- [ ] Metadata["sources"] is single source of truth
- [ ] Prompt gebruikt alleen sources met used_in_prompt=true

## Testing Strategy

### Test Scenarios
1. **Preview Test**: Genereer definitie → bronnen direct zichtbaar
2. **Provider Neutraliteit**: Check prompt voor "Bron 1/2/3"
3. **Juridische Citatie**: Test met juridische term → ECLI zichtbaar
4. **Geen Bronnen**: Disable web lookup → vriendelijke melding
5. **Determinisme**: 2x zelfde input → identieke bronnen volgorde

### Test Commands
```bash
# Run specific tests
pytest tests/web_lookup/test_metadata_first.py -v

# E2E test
python scripts/test_story_3_1.py

# Manual verification
streamlit run src/main.py
# Test met begrip: "aangifte"
# Verwacht: Bronnen sectie met Wikipedia + Overheid.nl
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Breaking existing UI tabs | Low | High | Test alle tabs na change |
| State management issues | Medium | Medium | Test met Streamlit reruns |
| Performance regression | Low | Low | < 5ms overhead acceptabel |
| Backwards compatibility | Low | Medium | Oude records blijven werken |

## Dependencies

- **Blocking**: Geen
- **Blocked by**: Geen
- **Related**: Epic 3 (parent), ValidationOrchestratorV2

## Metrics & KPIs

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Sources display rate | 0% | 100% | 🔄 |
| Provider neutrality | 0% | 100% | 🔄 |
| User satisfaction | N/A | +20% | 📋 |
| Token usage | 7250 | 7250 | ✅ |

## Next Steps

1. **Immediate** (Today):
   - [ ] Implement Phase 1: Remove legacy wrapper
   - [ ] Test UI compatibility

2. **Short-term** (This week):
   - [ ] Implement Phase 2-4
   - [ ] Complete testing
   - [ ] Deploy to staging

3. **Follow-up** (Next sprint):
   - [ ] Story 3.1b: Database migration
   - [ ] Advanced caching
   - [ ] Rate limiting

## Notes & Decisions

- **Decision**: Gekozen voor Optie B (Clean Solution) over Quick Fix
- **Rationale**: Verwijdert technische schuld permanent
- **Trade-off**: 2 uur extra werk voor lange termijn maintainability
- **Alternative**: Quick Fix was mogelijk in 30 min maar behield tech debt

## Resources

- [Story 3.1 Design Doc](./story-3.1-metadata-first-prompt-second.md)
- [Epic 3 Overview](./epic-3-web-lookup-modernization.md)
- [Architecture Docs](../architectuur/)
- [Test Results](../../tests/web_lookup/)

---
*Last Updated: 2025-09-03 15:30*
*Author: Development Team*
*Status: Active Implementation*
