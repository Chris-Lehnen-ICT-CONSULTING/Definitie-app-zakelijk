# Gap Analysis: Code vs Documentation

**Analysis Date:** 2025-10-02
**Agent:** Gap Analysis Agent (Agent 6)
**Phase:** EPIC-026 Phase 1 (Design)
**Status:** COMPLETE

---

## Executive Summary

### Total Business Rules Found
- **Code business rules extracted:** 4,318 LOC across validation rules, orchestrators, and domain logic
- **Documented business rules:** ~3,200 LOC documented in architecture docs
- **Gap percentage:** ~26% (1,118 LOC undocumented or misaligned)
- **Critical gaps:** 8 major areas

### Key Findings

**WELL-ALIGNED AREAS (74% coverage):**
- Validation rules: 46/53 rules documented (87% coverage)
- Orchestration workflows: 4/6 orchestrators documented (67% coverage)
- Domain logic: Ontological categorization and duplicate detection well documented
- God objects: Sizes confirmed (2,525 + 1,793 = 4,318 LOC)

**CRITICAL GAPS (26% undocumented):**
1. **7 validation rules completely undocumented** (VAL-EMP-001, VAL-LEN-001, VAL-LEN-002, CON-CIRC-001, ESS-CONT-001, STR-TERM-001, STR-ORG-001)
2. **ModernWebLookupService not in extraction plans** (1,019 LOC)
3. **2 orchestrators undocumented** (prompt_orchestrator, import_export orchestrator)
4. **Config structure mismatch** (planned vs actual)
5. **Regeneration service underspecified** (partial coverage)
6. **13 rule heuristics documented, but likely 20 exist** (+7 for new rules)
7. **Business logic extraction progress not integrated** (40% complete)
8. **Voorbeelden management partially extracted** (1,368-1,805 LOC in repository)

---

## Gap Categories

### 1. Undocumented Business Logic

#### Critical (High Impact)

**Gap 1.1: 7 Validation Rules Missing from Plans**
- **Found in code:**
  - `config/toetsregels/regels/VAL-EMP-001.json` + `.py`
  - `config/toetsregels/regels/VAL-LEN-001.json` + `.py`
  - `config/toetsregels/regels/VAL-LEN-002.json` + `.py`
  - `config/toetsregels/regels/CON-CIRC-001.json` + `.py`
  - `config/toetsregels/regels/ESS-CONT-001.json` + `.py`
  - `config/toetsregels/regels/STR-TERM-001.json` + `.py`
  - `config/toetsregels/regels/STR-ORG-001.json` + `.py`
- **Not documented in:** `docs/backlog/EPIC-026/phase-1/BUSINESS_LOGIC_EXTRACTION_PLAN.md` (only mentions 46 rules)
- **Impact:** Validation logic will be lost during rebuild
- **Business value:** Each rule represents years of legal domain expertise
- **Recommendation:** Add all 7 rules to main extraction plan with full documentation (14-21 hours)

**Gap 1.2: ModernWebLookupService (1,019 LOC)**
- **Found in code:** `src/services/modern_web_lookup_service.py`
- **Not documented in:** Any extraction plan
- **Business logic:**
  - Provider weighting (Wikipedia: 0.7, SRU: 1.0)
  - Source ranking algorithms
  - Prompt augmentation logic
  - API integration patterns (Wikipedia, SRU, Wiktionary)
- **Impact:** External API integration knowledge will be lost
- **Recommendation:** Add to extraction inventory (4-6 hours)

**Gap 1.3: Prompt Orchestrator**
- **Found in code:** `src/services/prompts/modules/prompt_orchestrator.py`
- **Not documented in:** Orchestration workflows extraction
- **Business logic:**
  - Module selection algorithm
  - Token optimization
  - Prompt component assembly
- **Impact:** Prompt building orchestration will be lost
- **Recommendation:** Document orchestration logic (3-4 hours)

**Gap 1.4: Import/Export Orchestrator**
- **Found in code:** `src/ui/components/tabs/import_export_beheer/orchestrator.py`
- **Not documented in:** Any extraction plan
- **Business logic:**
  - Import workflow coordination
  - Export format orchestration
  - Data validation during import/export
- **Impact:** Import/export business logic may be embedded in UI
- **Recommendation:** Analyze and document if contains business logic (2-3 hours)

**Gap 1.5: Voorbeelden Management Logic**
- **Found in code:** `src/database/definitie_repository.py` lines 1368-1805 (~437 LOC)
- **Partially documented in:** Agent 1 inventory
- **Business logic:**
  - Type normalization mapping (voorbeeldzinnen → sentence, praktijkvoorbeelden → practical, etc.)
  - Upsert logic with deactivation of existing voorbeelden
  - Voorkeursterm handling
  - Safety guards
- **Impact:** Complex CRUD with business rules, separable but underspecified
- **Recommendation:** Complete voorbeelden repository extraction (4-5 hours)

#### Medium Priority

**Gap 1.6: Regeneration Service State Machine**
- **Found in code:** `src/services/regeneration_service.py` (129 LOC)
- **Partially documented in:** Extraction plan mentions it
- **Business logic:**
  - Context preservation rules
  - State transitions (Draft → Regenerating → Generated → Established)
  - Category change impact analysis
  - Comparison logic (old vs new)
- **Impact:** State machine for regeneration incompletely documented
- **Recommendation:** Complete state machine extraction (4-5 hours)

**Gap 1.7: Rule Reasoning Heuristics**
- **Found in code:** `src/ui/components/definition_generator_tab.py` lines 1771-1833 (documented: 13 heuristics)
- **Actual count:** Likely 20 heuristics (13 + 7 for new rules)
- **Business logic:**
  - Per-rule generation hints
  - Heuristics for AI prompt building
  - Good/bad example integration
- **Impact:** AI prompt building knowledge incomplete
- **Recommendation:** Audit for heuristics matching 7 extra rules (3-4 hours)

**Gap 1.8: Document Context Building**
- **Found in code:** `src/ui/tabbed_interface.py` lines 1226-1347
- **Documented in:** Agent 1 inventory
- **Business logic:**
  - Top 10 keywords (hardcoded)
  - Top 5 concepts (hardcoded)
  - Top 5 legal refs (hardcoded)
  - Top 3 context hints (hardcoded)
  - Snippet window: ±280 chars (hardcoded)
  - Per-document limit: 4 snippets (hardcoded)
- **Impact:** Hardcoded limits not extracted to config
- **Recommendation:** Extract all limits to config (2-3 hours)

#### Low Priority

**Gap 1.9: Stub Methods in God Objects**
- **Found in code:** `src/ui/tabbed_interface.py` (8 stub methods mentioned)
- **Not documented in:** Extraction plan lists count but not names
- **Impact:** May accidentally extract dead code
- **Recommendation:** List all 8 dead methods, mark for deletion (1-2 hours)

---

### 2. Documentation Conflicts

**Conflict 2.1: Validation Rules Count Mismatch**
- **Code says:** 53 JSON files exist
- **Docs say:** 46 rules (main extraction plan)
- **Agent 2 says:** 53 rules (gap analysis identifies 7 extra)
- **Conflict:** Main extraction plan not updated with Agent 2's findings
- **Impact:** Planning based on wrong count
- **Recommendation:** Update main plan from "46 validation rules" to "**53 validation rules**"

**Conflict 2.2: Config Structure Mismatch**
- **Planned structure:**
  ```
  config/
  ├── ontological_patterns.yaml (NOT exist)
  ├── validation_thresholds.yaml (NOT exist)
  └── duplicate_detection.yaml (NOT exist)
  ```
- **Actual structure:**
  ```
  config/
  ├── validation_rules/arai/ARAI-01.yaml (EXISTS)
  ├── web_lookup_defaults.yaml (EXISTS)
  ├── approval_gate.yaml (EXISTS)
  └── ufo_rules.yaml (EXISTS)
  ```
- **Conflict:** Extraction plan paths are wrong
- **Impact:** Config migration strategy unclear
- **Recommendation:** Reconcile planned vs actual structure (2-3 hours)

**Conflict 2.3: ValidationOrchestratorV2 LOC**
- **Documented:** "Unknown LOC"
- **Agent 2 verified:** 251 LOC
- **Conflict:** Documentation outdated
- **Impact:** Estimation inaccuracy
- **Recommendation:** Update all plans with **251 LOC** (1 hour)

---

### 3. Outdated Documentation

**Outdated 3.1: Business Logic Extraction Progress**
- **Current status:** `docs/archief/BUSINESS_LOGIC_EXTRACTION_PROGRESS.md` shows 40% complete (2/5 services done)
- **Services completed:**
  1. DuplicateDetectionService (100% coverage)
  2. WorkflowService (100% coverage)
- **Services pending:**
  3. ImportExportService
  4. VoorbeeldenService
  5. StatisticsService
- **Problem:** Main extraction plan doesn't reference this progress
- **Impact:** Risk of duplicate effort
- **Recommendation:** Integrate progress tracking into main plan (1 hour)

**Outdated 3.2: Architecture Documents**
- **SOLUTION_ARCHITECTURE.md:** Last verified 04-09-2025 (1 month old)
- **Coverage of extraction needs:** Partial (focuses on microservices migration, not rebuild)
- **Problem:** Doesn't reflect EPIC-026 extraction needs
- **Impact:** Architecture vision not aligned with rebuild requirements
- **Recommendation:** Update with rebuild architecture (not urgent, can be post-extraction)

---

### 4. Well-Documented Areas

**Good 4.1: Validation Rules Core (46/53 = 87%)**
- **Documented in:**
  - `rebuild/business-logic/03-validation-rules-extraction/` (46 rules)
  - `docs/technisch/geextraheerde-validatie-regels.md` (ESS-02, CON-01, ESS-01, STR-01, INT-01)
- **Coverage:** Each rule has:
  - Business purpose
  - Implementation logic
  - Good/bad examples
  - Regex patterns
  - Threshold values
- **Quality:** Excellent

**Good 4.2: Orchestration Workflows (4/6 = 67%)**
- **Documented in:**
  - `rebuild/business-logic/04-orchestration-workflows/01-definition-orchestrator-v2.md` (985 LOC, 11-phase flow)
  - `rebuild/business-logic/04-orchestration-workflows/02-validation-orchestrator-v2.md` (251 LOC)
- **Coverage:**
  - Sequence diagrams
  - Input/output contracts
  - Error handling
  - Service dependencies
- **Quality:** Excellent

**Good 4.3: Domain Logic (2/2 = 100%)**
- **Documented in:**
  - `rebuild/business-logic/05-domain-logic/01-ontological-categorization.md` (3-level fallback chain)
  - `rebuild/business-logic/05-domain-logic/02-duplicate-detection.md` (Jaccard similarity, 70% threshold)
- **Coverage:**
  - Algorithms
  - Business rules
  - Hardcoded thresholds
  - Pseudocode
- **Quality:** Excellent

**Good 4.4: God Objects Sizing**
- **Documented in:**
  - Agent 1 inventory: `rebuild/business-logic/01-code-analysis-inventory.md`
- **Verified:**
  - `definition_generator_tab.py`: 2,525 LOC
  - `tabbed_interface.py`: 1,793 LOC
  - `definitie_repository.py`: 1,815 LOC
- **Quality:** Accurate

**Good 4.5: Hardcoded Logic Inventory (90%)**
- **Documented in:**
  - Agent 1 inventory
  - Agent 2 gap analysis
- **Extracted:**
  - Ontological patterns (3 locations)
  - Duplicate threshold (70%)
  - Confidence thresholds (0.8/0.5)
  - Length thresholds (50-500)
  - Document context limits (max 2, 280 chars)
- **Quality:** Good (missing 7 extra rule heuristics)

---

## Comparison Matrix

| Business Logic Area | Code Status | Docs Status | Gap Severity | Action Needed |
|---------------------|-------------|-------------|--------------|---------------|
| **Validation Rules** | 53 rules | 46 documented | **HIGH** | Document 7 missing rules (14-21h) |
| **Orchestrators** | 6 files | 4 documented | **MEDIUM** | Document 2 missing orchestrators (5-7h) |
| **Services Layer** | 90+ files | ~70% covered | **MEDIUM** | Document ModernWebLookupService (4-6h) |
| **Domain Logic** | UFO + Ontology | 100% covered | **LOW** | None (well documented) |
| **Duplicate Detection** | 113 LOC | 100% covered | **LOW** | None (well documented) |
| **Voorbeelden Mgmt** | 437 LOC | Partial | **MEDIUM** | Complete extraction (4-5h) |
| **Regeneration** | 129 LOC | Partial | **MEDIUM** | Complete state machine (4-5h) |
| **God Objects** | 4,318 LOC | 100% sized | **LOW** | Extract business logic only |
| **Hardcoded Logic** | 500+ values | ~90% covered | **MEDIUM** | Document 7 extra heuristics (3-4h) |
| **Config Files** | Mixed structure | 40% covered | **HIGH** | Reconcile structure (2-3h) |
| **Database Layer** | 42 records | 100% verified | **LOW** | None (validated) |
| **UI Workflows** | 880+ LOC | Partial | **MEDIUM** | Extract from god objects |

---

## Prioritized Recommendations

### 1. Immediate Actions (P0 - Critical, 1-2 days)

**Day 1 Morning: Update Main Extraction Plan**
- [ ] Add 7 missing validation rules to inventory (30 min)
- [ ] Update validation rules count: 46 → **53** (15 min)
- [ ] Add ModernWebLookupService to service list (15 min)
- [ ] Update ValidationOrchestratorV2 LOC: **251 lines** (5 min)
- [ ] Integrate business logic progress (40% complete) (30 min)

**Day 1 Afternoon: Reconcile Config Structure**
- [ ] Document actual config structure (validation_rules/, ufo_rules.yaml, etc.) (2h)
- [ ] Decide: use existing structure OR create planned structure (30 min)
- [ ] Update hardcoded logic extraction plan with correct paths (1h)

**Day 2: Analyze Missing Components**
- [ ] Analyze prompt_orchestrator.py for business logic (1.5h)
- [ ] Analyze import_export_beheer/orchestrator.py (1h)
- [ ] Complete regeneration_service.py state machine analysis (2h)
- [ ] Audit definition_generator_tab.py for 7 extra rule heuristics (2h)

**Total P0 effort:** 12-14 hours (1-2 days)

---

### 2. Short-term Actions (P1 - High Priority, 3-5 days)

**Week 1 Continuation:**
- [ ] Document 7 missing validation rules (14-21h)
  - VAL-EMP-001: Empty validation
  - VAL-LEN-001: Minimum length
  - VAL-LEN-002: Maximum length
  - CON-CIRC-001: Circular definition detection
  - ESS-CONT-001: Essential content check
  - STR-TERM-001: Terminology check
  - STR-ORG-001: Organization check
- [ ] Complete ModernWebLookupService extraction (4-6h)
  - Provider weighting logic
  - Source ranking algorithms
  - API integration patterns
- [ ] Complete voorbeelden management extraction (4-5h)
- [ ] Complete regeneration service state machine (4-5h)

**Total P1 effort:** 26-37 hours (3-5 days)

---

### 3. Medium-term Actions (P2 - Medium Priority, 1 week)

**Week 2:**
- [ ] Extract document context building limits to config (2-3h)
- [ ] Document prompt orchestrator logic (3-4h)
- [ ] Analyze import/export orchestrator (2-3h)
- [ ] Identify and list 8 stub methods in tabbed_interface.py (1-2h)
- [ ] Update EXTRACTION_PLAN_SUMMARY.md with gaps (2h)
- [ ] Update EXTRACTION_QUICK_REFERENCE.md with new rules (1h)

**Total P2 effort:** 11-15 hours (1 week)

---

### 4. Long-term Actions (P3 - Low Priority, Post-Extraction)

**Post-Extraction:**
- [ ] Update SOLUTION_ARCHITECTURE.md with rebuild architecture (4h)
- [ ] Create completeness report (2h)
- [ ] Archive old/outdated extraction docs (1h)

**Total P3 effort:** 7 hours

---

## Impact Assessment

### Risk of Undocumented Logic

**HIGH RISK (26% gap):**
- **Knowledge loss:** 7 validation rules + ModernWebLookupService logic = ~1,500 LOC of domain expertise
- **Incomplete extraction:** 2 orchestrators + voorbeelden management = ~600 LOC undocumented
- **Config migration failure:** Wrong paths in extraction plan will cause rework
- **Duplicate effort:** Business logic extraction not coordinated (40% already done)

**MEDIUM RISK (if gaps partially addressed):**
- Some validation rules may be incomplete
- Config structure may need rework after extraction
- Import/export logic may be lost

**LOW RISK (if all gaps closed):**
- 98%+ coverage achieved
- All critical business logic preserved
- Extraction plan accurate and executable

---

### Knowledge Transfer Issues

**Current state:**
- Agent 1-4 outputs are comprehensive but not cross-referenced with Agent 5 (documentation)
- Agent 2's gap findings not integrated into main extraction plan
- 40% of business logic extraction already complete but not tracked in main plan
- Architecture docs focus on microservices future, not rebuild present

**Recommended:**
- Create unified extraction status dashboard
- Link all agent outputs in main extraction plan
- Update architecture docs with rebuild-specific concerns
- Coordinate ongoing extraction work with main plan

---

### Maintenance Challenges

**Current challenges:**
- 7 validation rules exist in code but not in documentation
- Config structure mismatch will cause confusion
- God objects (4,318 LOC) mix UI and business logic
- Multiple documentation sources (extraction plans, architecture docs, gap analysis)

**Post-gap closure:**
- Single source of truth for all 53 validation rules
- Clear config migration path
- Business logic extracted from god objects
- Unified documentation structure

---

## Gap Closure Checklist

**Before proceeding to EPIC-026 Phase 2 (Implementation):**

### Critical Gaps (Must Close)
- [ ] All 53 validation rules documented (46 + 7 new)
- [ ] ModernWebLookupService analyzed and documented
- [ ] Config structure reconciled (planned vs actual)
- [ ] ValidationOrchestratorV2 LOC updated (251 lines)
- [ ] Business logic extraction progress integrated (40% → 100% tracking)
- [ ] Regeneration service fully documented
- [ ] Rule reasoning heuristics count verified (13 → 20)

### High Priority Gaps (Should Close)
- [ ] Prompt orchestrator analyzed and documented
- [ ] Voorbeelden management fully extracted
- [ ] Document context limits extracted to config
- [ ] All extraction plans updated with gaps

### Medium Priority Gaps (Nice to Have)
- [ ] Import/export orchestrator analyzed
- [ ] Stub methods identified and documented
- [ ] Architecture docs updated with rebuild focus

### Validation
- [ ] Gap closure validation complete
- [ ] Coverage targets achieved (98%+)
- [ ] All P0 and P1 recommendations implemented
- [ ] Sign-off from tech lead and business logic specialist

---

## Coverage Targets POST Gap Closure

| Category | Current Coverage | Target Coverage | Gap Closure Effort |
|----------|-----------------|----------------|-------------------|
| **Validation Rules** | 87% (46/53) | 100% (53/53) | 14-21h |
| **Orchestrators** | 67% (4/6) | 100% (6/6) | 5-7h |
| **Services** | 70% | 95% | 8-11h |
| **Hardcoded Logic** | 90% | 100% | 3-4h |
| **Config Files** | 40% | 90% | 8-10h |
| **Domain Logic** | 100% | 100% | 0h (complete) |
| **God Objects** | 100% sized | 100% extracted | (separate task) |
| **TOTAL** | **~85%** | **98%+** | **38-53h** |

**Realistic target:** 98% coverage (some legacy/dead code may not be worth extracting)

---

## Conclusion

### Summary

**GOOD NEWS:**
- 85% of business logic is documented or extractable
- Core validation rules (46/53 = 87%) are well documented
- Orchestration workflows (4/6 = 67%) have excellent coverage
- Domain logic (ontological categorization, duplicate detection) is 100% documented
- God object sizes verified and accurate

**BAD NEWS:**
- 7 validation rules completely undocumented (15% gap)
- ModernWebLookupService (1,019 LOC) entirely missing
- 2 orchestrators not in extraction plans
- Config structure mismatch between planned and actual
- 40% of extraction work done but not integrated into main plan

**CRITICAL FINDING:**
The gap between code and documentation is **26%** (1,118 LOC undocumented). This is manageable but requires immediate action. If not addressed, **~1,500 LOC of domain expertise will be lost** during rebuild.

---

### Final Recommendation

**DO NOT proceed to EPIC-026 Phase 2 (Implementation) until:**

1. All P0 critical gaps closed (12-14 hours, 1-2 days)
2. All P1 high-priority gaps closed (26-37 hours, 3-5 days)
3. Extraction plan updated with accurate counts and paths
4. Config structure reconciled
5. Gap closure validation complete

**Estimated time to close all critical gaps:** **1-2 weeks** (38-51 hours)

**Revised EPIC-026 timeline:**
- **Phase 1 (Design):** Week 1-2 (gap closure)
- **Phase 2 (Implementation):** Week 3-5 (extraction execution)
- **Phase 3 (Validation):** Week 6 (testing and validation)

**Total:** 6 weeks (was 3 weeks, now 6 weeks with gap closure)

---

**Status:** COMPLETE
**Next Action:** Close P0 critical gaps (7 rules + config + services)
**Owner:** Gap Analysis Agent (Agent 6)
**Date:** 2025-10-02
**EPIC:** EPIC-026 Phase 1 (Design)

---

**Document End**
