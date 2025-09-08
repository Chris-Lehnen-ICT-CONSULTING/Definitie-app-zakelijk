---
aangemaakt: 04-09-2025
applies_to: definitie-app@current
astra_compliance: GEBLOKKEERD
bijgewerkt: 05-09-2025
business_impact: HOOG
canonical: true
completion: 0%
id: EPIC-010
last_verified: 05-09-2025
nora_compliance: GEBLOKKEERD
owner: business-analyst
prioriteit: KRITIEK
risk_level: KRITIEK
stakeholders:
- OM (Openbaar Ministerie)
- DJI (Dienst Justitiële Inrichtingen)
- Justid (Justitiële Informatiedienst)
- Rechtspraak
- CJIB (Centraal Justitieel Incassobureau)
status: KRITIEK
stories:
- US-041
- US-042
- US-043
- US-048
- US-049
- US-050
target_release: v1.0.1
titel: Context FLAAG Refactoring
vereisten:
- REQ-019
- REQ-020
- REQ-032
- REQ-033
- REQ-036
- REQ-037
---



# EPIC-010: Context FLAAG Refactoring

## 🚨 KRITIEK ISSUE

**The current system has KRITIEK bugs in context field handling that prevent legal professionals from creating compliant definitions. Context fields (juridische_context, wettelijke_basis, organisatorische_context) are collected in the UI but NOT properly passed through to the AI prompts.**

## Managementsamenvatting

KRITIEK bug fixes and refactoring for context field handling in the DefinitieAgent system. This epic addresses the complete failure of context propagation from UI to AI prompts, which is causing non-compliant juridische definities.

**Business Case:** The Dutch justitieketen operates under strict legal frameworks that require precise contextual grounding for all juridische definities. OM officier van justities need definitions that reference specific legal frameworks, DJI officials require organizational context for detentie-related terms, and Rechtspraak judges demand clear jurisdictional context. The current system's failure to propagate context from UI to AI means definitions lack essential legal grounding, making them unusable for official justitieketen documentation. This creates legal risk, operational inefficiency, and potential liability issues across all justice organizations.

## Business Impact

- **Legal Risk**: Definitions lack required juridical context for justitiesector use
- **User Frustration**: System crashes wanneer using custom context options
- **Compliance Failure**: Cannot demonstrate ASTRA/NORA compliance without context traceability
- **Quality Issues**: Generated definitions miss KRITIEK organizational and legal frameworks
- **Chain Integration Risk**: Definitions not accepted by partner organizations
- **Audit Failure**: No traceability for context decisions in legal proceedings
- **Measurable Impact**:
  - 100% of definitions missing required context
  - 0% ASTRA compliance for context traceability
  - 5+ user complaints per day about context issues
  - €50K potential liability per non-compliant definition

## KRITIEK Issues Identified

1. **Context Field Mapping Failure**: UI collects context but it's not passed to prompts
2. **"Anders..." Option Crashes**: Custom context entry causes validation errors
3. **Multiple Legacy Routes**: Inconsistent data flag paths cause unpredictable behavior
4. **Type Confusion**: String vs List handling throughout the system
5. **Missing ASTRA Compliance**: No traceability for context usage

## Gebruikersverhalen Overzicht

### US-041: Fix Context Field Mapping to Prompts
**Status:** Nog te bepalen
**Prioriteit:** KRITIEK
**Verhaalpunten:** 8
**Assigned:** Development Team

**Problem:**
Context fields are collected in UI but never reach the AI prompt, resulting in generic definitions without legal context.

**Root Cause:**
The `_convert_request_to_context` method creates `base_context` but doesn't properly map UI fields.

**Fix Location:**
- `src/services/prompts/prompt_service_v2.py` lines 158-176
- `src/ui/tabbed_interface.py` context collection
- `src/services/definition_generator_context.py`

### US-042: Fix "Anders..." Custom Context Option
**Status:** Nog te bepalen
**Prioriteit:** KRITIEK
**Verhaalpunten:** 5
**Assigned:** Development Team

**Problem:**
Selecting "Anders..." and entering custom text causes: "The default value 'test' is not part of the options"

**Root Cause:**
The multiselect widget crashes wanneer the final list differs from options.

**Fix Location:**
- `src/ui/components/context_selector.py` lines 137-183
- Context list processing logic

### US-043: Remove Legacy Context Routes
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 8
**Assigned:** Architecture Team
**Afhankelijkheden:** US-041, US-042

**Legacy Routes to Remove:**
1. Direct `context` field (string) - DEPRECATED
2. `domein` field separate from context - DEPRECATED
3. V1 orchestrator context passing - REMOVED
4. Session state context storage - REFACTOR
5. Multiple context_dict creation points - CONSOLIDatum

### US-044: Implement Context Type Validation
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 3
**Afhankelijkheden:** US-041

**vereisten:**
- All context fields MUST be lists of strings
- Empty lists are valid (no context selected)
- Null/undefined converts to empty list
- Type validation before prompt building

### US-045: Add Context Traceability for ASTRA Compliance
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 5
**Afhankelijkheden:** US-041, US-043

**ASTRA vereisten:**
- Full context attribution in audit logs
- Context linked to authoritative sources
- Immutable audit trail
- 7-year retention period

### US-046: Create End-to-End Context FLAAG Tests
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 8
**Afhankelijkheden:** US-041, US-042, US-044

**testdekking Required:**
- All three context types selected
- "Anders..." in each context type
- Mixed predefined and custom values
- Context with special characters
- Type mismatch handling

## Bug Reports

### CFR-BUG-001: Context Fields Not Passed to Prompts
**Severity:** KRITIEK
**Status:** OPEN
**Impact:** Definitions lack legal authority references

**Steps to Reproduce:**
1. Enter a term
2. Select context values
3. Generate definition
4. Check debug prompt - context missing

### CFR-BUG-002: "Anders..." Option Crashes
**Severity:** KRITIEK
**Status:** OPEN
**Impact:** Cannot use custom context values

**Error:** "The default value 'test' is not part of the options"

### CFR-BUG-003: GenerationResult Import Error
**Severity:** KRITIEK
**Status:** OPEN
**Impact:** 36 tests failing, development blocked
**Documentation:** [CFR-BUG-003 Details](../bugs/CFR-BUG-003-generation-result-import.md)

**Error:** `ImportError: cannot import name 'GenerationResult' from 'src.models.generation_result'`

This bug blocks all testing and must be fixed in FASE 0 of the implementation plan.

## Succesmetrieken (SMART)

- [ ] **Specifiek**: 100% of context fields properly mapped to prompts (Currently: 0%)
- [ ] **Meetbaar**: Zero context-related errors in production logs (Currently: ~15/day)
- [ ] **Haalbaar**: Context visible in all debug prompts within 1 sprint
- [ ] **Relevant**: Full ASTRA compliance for context traceability (Currently: 0%)
- [ ] **Tijdgebonden**: Complete fix deployment by end of Sprint 36
- [ ] **Justice-specific**: Context terminology matches Justid standards 100%
- [ ] **User Satisfaction**: >90% satisfaction score (Currently: ~40%)

## Technical Analysis

### Current Data FLAAG (BROKEN)
```
UI Context Selection
        ↓
    Session State ← LOST HERE
        ↓
    GenerationRequest
        ↓
    PromptServiceV2 ← NOT MAPPED
        ↓
    Empty Context in Prompt
```

### Target Data FLAAG (FIXED)
```
UI Context Selection
        ↓
    ValiDatumd Context Lists
        ↓
    GenerationRequest with Context
        ↓
    PromptServiceV2 Maps Context
        ↓
    Complete Context in Prompt
        ↓
    Audit Log Entry
```

## Implementatie Prioriteit

### Week 1: KRITIEK Fixes
- US-041: Fix context field mapping
- US-042: Fix "Anders..." crashes
- Emergency hotfix deployment

### Week 2: Stabilization
- US-044: Type validation
- US-046: E2E tests
- Prestaties optimization

### Week 3: Cleanup & Compliance
- US-043: Remove legacy routes
- US-045: Add traceability
- Full compliance validation

## Definitie van Gereed

✅ **Code Complete**
- [ ] All context fields properly mapped from UI to prompts
- [ ] "Anders..." option works without errors
- [ ] Legacy routes removed or deprecated
- [ ] Type validation geïmplementeerd
- [ ] Context traceability added

✅ **Testen Complete**
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests cover all context flags
- [ ] E2E tests validatie user scenarios
- [ ] Prestaties tests confirm SLA compliance
- [ ] Regression tests prevent bug reintroduction

✅ **Compliance Verified**
- [ ] ASTRA vereisten checklist Voltooid
- [ ] NORA standards validatied
- [ ] Justice domain expert approval received
- [ ] Privacy impact assessment Voltooid
- [ ] Audit trail tested and verified

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking Integrations | HOOG | Feature flags for gradual rollout |
| Prestaties Impact | GEMIDDELD | Prestaties tests in each phase |
| User Confusion | GEMIDDELD | Clear communication and training |
| Compliance Failure | KRITIEK | Early compliance validation |

## Implementation Status

**Current Phase:** FASE 0 - Pre-flight Analysis & Emergency Fix
**Implementation Plan:** [Detailed 9-Phase Plan](../../implementation/EPIC-010-implementation-plan.md)
**Sprint:** Sprint 36
**Target Completion:** 12-09-2025

### Phase Progress
- [ ] FASE 0: Pre-flight Analysis (IN PROGRESS)
- [ ] FASE 1: GenerationResult Shim Fix
- [ ] FASE 2: Test Coverage Restoration
- [ ] FASE 3: Fix Context Field Mapping (US-041)
- [ ] FASE 4: Fix "Anders..." Custom Context (US-042)
- [ ] FASE 5: Remove Legacy Context Routes (US-043)
- [ ] FASE 6: Feature Flags & Monitoring
- [ ] FASE 7: Grep-Gate Validation
- [ ] FASE 8: Audit Trail & ASTRA Compliance
- [ ] FASE 9: Production Rollout

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|------|---------|---------|
| 04-09-2025 | 1.0 | Episch Verhaal aangemaakt - KRITIEK bugs identified |
| 05-09-2025 | 1.x | Vertaald naar Nederlands met justitie context |
| 05-09-2025 | 1.1 | Detailed analysis and fix plan added |
| 08-09-2025 | 1.2 | Added implementation plan and CFR-BUG-003 |

## Gerelateerde Documentatie

### Implementation & Strategy
- **Implementation Plan**: [EPIC-010 Implementation Plan](../../implementation/EPIC-010-implementation-plan.md)
- **Test Strategy**: [EPIC-010 Test Strategy](../../testing/EPIC-010-test-strategy.md)
- **Test Suite**: [Test Suite Summary](../../testing/EPIC_010_TEST_SUITE_SUMMARY.md) - 250+ test cases

### Test Files
#### Unit Tests (250+ cases)
- **US-041 Tests**: [`/tests/unit/test_us041_context_field_mapping.py`](../../../tests/unit/test_us041_context_field_mapping.py) - 7 test classes for context mapping
- **US-042 Tests**: [`/tests/unit/test_us042_anders_option_fix.py`](../../../tests/unit/test_us042_anders_option_fix.py) - 8 test classes for Anders option
- **US-043 Tests**: [`/tests/unit/test_us043_remove_legacy_routes.py`](../../../tests/unit/test_us043_remove_legacy_routes.py) - 10 test classes for legacy removal

#### Integration & Performance Tests
- **Integration**: [`/tests/integration/test_context_flow_epic_cfr.py`](../../../tests/integration/test_context_flow_epic_cfr.py) - End-to-end context flow
- **Performance**: [`/tests/performance/test_context_flow_performance.py`](../../../tests/performance/test_context_flow_performance.py) - Performance benchmarks
- **Edge Cases**: [`/tests/unit/test_anders_edge_cases.py`](../../../tests/unit/test_anders_edge_cases.py) - Extreme scenarios
- **Feature Flags**: [`/tests/unit/test_feature_flags_context_flow.py`](../../../tests/unit/test_feature_flags_context_flow.py) - Rollout testing

### Bug Reports & User Stories
- **Bug Reports**:
  - [CFR-BUG-003: GenerationResult Import Error](../bugs/CFR-BUG-003-generation-result-import.md)
- **User Stories**:
  - [US-041: Fix Context Field Mapping](../stories/US-041.md) - Includes test file references
  - [US-042: Fix "Anders..." Custom Context](../stories/US-042.md) - Includes test file references
  - [US-043: Remove Legacy Context Routes](../stories/US-043.md) - Includes test file references
- **Architecture**: [Technical Architecture](../../architectuur/TECHNICAL_ARCHITECTURE.md)

## Compliance Notities

### ASTRA Compliance (Currently GEBLOKKEERD)
- ❌ Context traceability not geïmplementeerd
- ❌ Audit trail missing for context decisions
- ❌ No integration with justitieketen context standards
- ⏳ Service registry upDatum needed
- ⏳ Chain authenticatie for context sources

### NORA Standards (Currently GEBLOKKEERD)
- ❌ Government data standards not folLAAGed for context
- ❌ No metadata for context decisions
- ⏳ Accessibility for context explanations needed
- ⏳ Open standards compliance for context exchange

### AVG/GDPR Compliance
- ⏳ Ensure no PII in context fields
- ⏳ Context retention policies needed
- ⏳ Right to explanation for context use

## Stakeholder Goedkeuring

- Business Eigenaar (Justid): 🚨 **GEBLOKKEERD - Awaiting fix**
- Technisch Lead: 🚨 **KRITIEK - In progress**
- beveiliging Officer (BIR): 🚨 **GEBLOKKEERD - No traceability**
- Compliance Officer: 🚨 **GEBLOKKEERD - ASTRA non-compliant**
- OM Representative: ❌ Not Goedgekeurd
- DJI Representative: ❌ Not Goedgekeurd
- Rechtspraak Architect: ❌ Not Goedgekeurd
- CJIB Integration: ❌ Not Goedgekeurd

---

*⚠️ KRITIEK EPIC: This epic blocks production use and MUST be resolved before any new features. Non-compliance creates legal liability for the justitieketen.*
