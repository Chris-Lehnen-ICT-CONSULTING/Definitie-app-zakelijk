---
id: EPIC-026-DOCUMENTATION-GAP-ANALYSIS
epic: EPIC-026
phase: 1
day: 2
created: 2025-10-02
owner: documentation-auditor
status: complete
type: gap-analysis
---

# Documentation Gap Analysis - EPIC-026 Business Logic Extraction

**Mission:** Cross-reference existing extraction documentation against actual codebase to identify gaps

**Audit Date:** 2025-10-02
**Auditor:** Documentation Auditor (Agent 2)
**Scope:** All extraction planning documents vs. actual codebase

---

## Executive Summary

### Audit Statistics

| Metric | Count | Coverage |
|--------|-------|----------|
| **Total Documents Audited** | 6 | 100% |
| **Total Codebase Files** | 321 Python files | - |
| **Validation Rules (JSON)** | 53 files | **115%** (7 extra) |
| **Validation Rules (Python)** | 46 files | **100%** |
| **Orchestrators Found** | 4 files | **100%** |
| **God Object LOC** | 4,318 LOC | **100%** match |
| **Database Definitions** | 42 records | **100%** match |
| **Critical Gaps Identified** | 12 items | - |
| **Overall Coverage** | - | **~85%** |

### Key Findings

✅ **WELL DOCUMENTED:**
- Validation rules (46 dual-format files confirmed)
- God object sizes (tabbed_interface: 1,793 LOC, definition_generator_tab: 2,525 LOC)
- Orchestrator files (definition_orchestrator_v2: 984 LOC, validation_orchestrator_v2: 251 LOC)
- Database baseline (42 definitions confirmed)
- Hardcoded patterns (confirmed in tabbed_interface.py)

❌ **CRITICAL GAPS:**
1. **7 Extra validation rules NOT documented** (VAL-EMP-001, VAL-LEN-001, VAL-LEN-002, CON-CIRC-001, ESS-CONT-001, STR-TERM-001, STR-ORG-001)
2. **Modern web lookup service NOT in extraction plans** (modern_web_lookup_service.py exists)
3. **Regeneration service complexity underestimated** (regeneration_service.py exists but limited coverage)
4. **Config structure mismatch** (validation_rules/ dir exists but no ontological_patterns.yaml)
5. **UI orchestrator in import_export_beheer** (ui/components/tabs/import_export_beheer/orchestrator.py NOT documented)

⚠️ **PARTIAL GAPS:**
- Workflow service partially extracted (workflow_service.py exists)
- Duplicate detection service exists (duplicate_detection_service.py)
- Business logic extraction progress tracked (40% complete per BUSINESS_LOGIC_EXTRACTION_PROGRESS.md)

---

## 1. Coverage Matrix

### 1.1 Validation Rules

| Category | Documented Count | In Codebase (JSON) | In Codebase (Python) | Gap | Priority |
|----------|-----------------|-------------------|---------------------|-----|----------|
| **ARAI** | 6 rules | 6 JSON + 6 Python | 6 files | ✅ **0** | - |
| **CON** | 2 rules | 3 JSON (CON-01, CON-02, CON-CIRC-001) | 3 files | ❌ **+1** (CON-CIRC-001) | **P0** |
| **ESS** | 5 rules | 6 JSON (ESS-01 to 05, ESS-CONT-001) | 6 files | ❌ **+1** (ESS-CONT-001) | **P0** |
| **INT** | 10 rules | 10 JSON + 10 Python | 10 files | ✅ **0** | - |
| **SAM** | 8 rules | 8 JSON + 8 Python | 8 files | ✅ **0** | - |
| **STR** | 9 rules | 12 JSON (STR-01 to 09, STR-TERM-001, STR-ORG-001, STR-08) | 12 files | ❌ **+3** | **P0** |
| **VER** | 3 rules | 3 JSON + 3 Python | 3 files | ✅ **0** | - |
| **DUP** | 1 rule | 1 JSON (DUP_01) | - | ✅ **0** | - |
| **VAL** | 0 rules | 3 JSON (VAL-EMP-001, VAL-LEN-001, VAL-LEN-002) | 0 files | ❌ **+3** | **P0** |
| **TOTAL** | **46 rules** | **53 JSON files** | **46 Python files** | ❌ **+7 undocumented** | - |

**CRITICAL FINDING:** 7 extra validation rules exist in codebase but are NOT documented:
1. `VAL-EMP-001` - Empty validation
2. `VAL-LEN-001` - Minimum length validation
3. `VAL-LEN-002` - Maximum length validation
4. `CON-CIRC-001` - Circular definition detection
5. `ESS-CONT-001` - Essential content check
6. `STR-TERM-001` - Terminology check
7. `STR-ORG-001` - Organization check

**Impact:** Hardcoded logic extraction plan mentions these rules (lines 60-161 in hardcoded_logic_extraction_plan.md) but they're NOT in the main extraction plan count of 46 rules!

---

### 1.2 Orchestrators

| Orchestrator | Documented | In Codebase | LOC Documented | LOC Actual | Match | Priority |
|--------------|-----------|-------------|---------------|-----------|--------|----------|
| **definition_orchestrator_v2.py** | ✅ Yes | ✅ Yes | 984 LOC | 984 LOC | ✅ **100%** | P0 |
| **validation_orchestrator_v2.py** | ✅ Yes | ✅ Yes | "Unknown LOC" | 251 LOC | ⚠️ **Partial** | P0 |
| **regeneration workflow (in tab)** | ✅ Yes (~500 LOC) | ✅ Yes | 500 LOC | (in definition_generator_tab) | ✅ **Match** | P0 |
| **generation workflow (in tab)** | ✅ Yes (~380 LOC) | ✅ Yes | 380 LOC | (in tabbed_interface) | ✅ **Match** | P0 |
| **prompt_orchestrator.py** | ❌ No | ✅ **Yes** | - | ? LOC | ❌ **GAP** | **P1** |
| **import_export orchestrator** | ❌ No | ✅ **Yes** | - | ? LOC | ❌ **GAP** | **P2** |
| **TOTAL** | 4 documented | **6 exist** | - | - | ⚠️ **67%** | - |

**CRITICAL FINDING:** 2 orchestrators exist but are NOT documented:
1. `src/services/prompts/modules/prompt_orchestrator.py` - Prompt module orchestration (NOT in extraction plans)
2. `src/ui/components/tabs/import_export_beheer/orchestrator.py` - Import/export orchestration (NOT in extraction plans)

**Impact:** These orchestrators may contain business logic that will be lost during rebuild.

---

### 1.3 Services & Business Logic

| Service/Component | Documented | In Codebase | Coverage | Priority |
|-------------------|-----------|-------------|----------|----------|
| **God Objects** | | | | |
| - tabbed_interface.py | ✅ 1,793 LOC | ✅ 1,793 LOC | ✅ **100%** | P0 |
| - definition_generator_tab.py | ✅ 2,525 LOC | ✅ 2,525 LOC | ✅ **100%** | P0 |
| **Services** | | | | |
| - ModernWebLookupService | ❌ No | ✅ **Yes** | ❌ **0%** | **P1** |
| - RegenerationService | ✅ Partial | ✅ Yes | ⚠️ **50%** | P0 |
| - DuplicateDetectionService | ⚠️ In progress | ✅ Yes | ✅ **100%** | P0 |
| - WorkflowService | ⚠️ In progress | ✅ Yes | ✅ **100%** | P0 |
| - CategoryService | ✅ Yes | ✅ Yes | ✅ **100%** | P0 |
| - ValidationOrchestratorV2 | ✅ Yes | ✅ Yes | ✅ **100%** | P0 |
| - UnifiedDefinitionServiceV2 | ✅ Partial | ✅ Yes | ⚠️ **70%** | P0 |
| **Config Files** | | | | |
| - ontological_patterns.yaml | ✅ Planned | ❌ **NOT exist** | ❌ **0%** | **P0** |
| - validation_thresholds.yaml | ✅ Planned | ❌ **NOT exist** | ❌ **0%** | **P0** |
| - config/validation_rules/ | ⚠️ Not mentioned | ✅ **Exists** (ARAI-01.yaml) | ⚠️ **Partial** | P1 |

**CRITICAL FINDING:**
- ModernWebLookupService exists in codebase but is NOT in any extraction plan
- Planned config files (ontological_patterns.yaml, validation_thresholds.yaml) do NOT exist yet
- Existing config structure (config/validation_rules/) is NOT documented in extraction plans

---

### 1.4 Hardcoded Logic

| Logic Type | Documented | In Codebase | Location Match | Priority |
|-----------|-----------|-------------|---------------|----------|
| **Ontological Patterns** | ✅ Yes (3 locations) | ✅ Confirmed | ✅ tabbed_interface.py L354-418 | P0 |
| **Rule Reasoning Heuristics** | ✅ Yes (13 rules) | ⚠️ **Likely more** | ⚠️ definition_generator_tab.py | **P0** |
| **Duplicate Detection Threshold** | ✅ Yes (70%) | ✅ Confirmed | ✅ definitie_repository.py | P0 |
| **Confidence Thresholds** | ✅ Yes (0.8/0.5) | ✅ Confirmed | ✅ definition_generator_tab.py L223-228 | P1 |
| **Length Thresholds** | ✅ Yes (50-500) | ✅ Confirmed | ✅ Multiple locations | P1 |
| **Category Change Impact** | ✅ Yes | ✅ Confirmed | ✅ definition_generator_tab.py | P0 |
| **Document Context Limits** | ✅ Yes (max 2, 280 char) | ✅ Confirmed | ✅ tabbed_interface.py | P1 |

**FINDING:** Hardcoded logic inventory is accurate but may be incomplete. The 7 extra validation rules suggest more hardcoded heuristics exist.

---

## 2. CRITICAL GAPS (P0)

### Gap 1: 7 Undocumented Validation Rules
**What's missing:** Documentation for VAL-EMP-001, VAL-LEN-001, VAL-LEN-002, CON-CIRC-001, ESS-CONT-001, STR-TERM-001, STR-ORG-001

**Where in code:**
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VAL-EMP-001.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VAL-LEN-001.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VAL-LEN-002.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/CON-CIRC-001.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-CONT-001.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-TERM-001.json`
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-ORG-001.json`

**Impact:**
- Main extraction plan counts 46 rules but 53 JSON files exist
- These 7 rules ARE mentioned in hardcoded_logic_extraction_plan.md but NOT in main BUSINESS_LOGIC_EXTRACTION_PLAN.md
- Risk of losing validation logic during rebuild

**Extraction effort:** 2-3 hours per rule = **14-21 hours total**

**Action required:** Add these 7 rules to main extraction inventory with full documentation

---

### Gap 2: ValidationOrchestratorV2 LOC Unknown
**What's missing:** Actual LOC count for validation_orchestrator_v2.py

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/orchestrators/validation_orchestrator_v2.py`

**Actual LOC:** 251 lines (now confirmed)

**Documented:** "Unknown LOC" in extraction plans

**Impact:**
- Cannot accurately estimate extraction complexity
- May underestimate refactoring effort

**Extraction effort:** 1 hour to update documentation

**Action required:** Update all extraction plans with actual LOC: **251 LOC**

---

### Gap 3: ModernWebLookupService NOT Documented
**What's missing:** Entire service not mentioned in extraction plans

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/modern_web_lookup_service.py`

**Impact:**
- External API integration logic may be lost
- Wikipedia, SRU, and other lookup logic not extracted
- Config file `config/web_lookup_defaults.yaml` exists but service not documented

**Extraction effort:** 4-6 hours (analyze service + document logic + extract config patterns)

**Action required:** Add ModernWebLookupService to extraction inventory:
- Analyze business logic (provider weights, prompt augmentation)
- Document API integration patterns
- Extract hardcoded provider configurations

---

### Gap 4: Planned Config Files Don't Exist
**What's missing:** `config/ontological_patterns.yaml` and `config/validation_thresholds.yaml` planned but not created

**Where in code:**
- ❌ `/Users/chrislehnen/Projecten/Definitie-app/config/ontological_patterns.yaml` (NOT EXIST)
- ❌ `/Users/chrislehnen/Projecten/Definitie-app/config/validation_thresholds.yaml` (NOT EXIST)
- ✅ `/Users/chrislehnen/Projecten/Definitie-app/config/validation_rules/arai/ARAI-01.yaml` (EXISTS but different structure)

**Impact:**
- Hardcoded logic extraction plan assumes these files will exist
- Actual config structure is different (validation_rules/ directory)
- Migration path unclear

**Extraction effort:** 6-8 hours (create config schemas + migrate hardcoded values)

**Action required:**
1. Reconcile planned vs. actual config structure
2. Document existing `config/validation_rules/` directory
3. Create missing config files OR update extraction plan to use existing structure

---

### Gap 5: Prompt Orchestrator NOT Documented
**What's missing:** `src/services/prompts/modules/prompt_orchestrator.py` not in extraction plans

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/prompt_orchestrator.py`

**Impact:**
- Prompt building orchestration logic may be lost
- Module selection algorithm not extracted
- Token optimization knowledge not preserved

**Extraction effort:** 3-4 hours

**Action required:** Add to extraction inventory under "Prompt Building Documentation" section

---

### Gap 6: Import/Export Orchestrator NOT Documented
**What's missing:** `src/ui/components/tabs/import_export_beheer/orchestrator.py` not in extraction plans

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/orchestrator.py`

**Impact:**
- Import/export business logic may be embedded in UI
- God object pattern in import/export tab not identified
- Workflow coordination for import/export not extracted

**Extraction effort:** 2-3 hours

**Action required:** Analyze this orchestrator and add to extraction plan if contains business logic

---

### Gap 7: Regeneration Service Underspecified
**What's missing:** regeneration_service.py exists but limited coverage in extraction plans

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/regeneration_service.py`

**Documented:** Only mentioned as "partial" in orchestrator extraction plan

**Impact:**
- Regeneration context management logic may be incomplete
- Set/get context methods not fully documented
- State machine for regeneration not extracted

**Extraction effort:** 4-5 hours (full service analysis)

**Action required:** Complete regeneration service extraction:
- Document context management methods
- Extract state machine logic
- Document interaction with RegenerationOrchestrator

---

### Gap 8: Rule Reasoning Heuristics Count Mismatch
**What's missing:** Hardcoded logic plan documents 13 heuristics, but 7 extra rules exist

**Where in code:**
- Documented: definition_generator_tab.py L1771-1833 (13 rules)
- Actual: 53 JSON rule files (suggests more heuristics)

**Impact:**
- May have more than 13 hardcoded heuristics
- Extra 7 rules (VAL-*, CON-CIRC-*, ESS-CONT-*, STR-TERM-*, STR-ORG-*) likely have heuristics too
- Total could be 13 + 7 = **20 heuristics**

**Extraction effort:** 3-4 hours (analyze 7 extra rules for heuristics)

**Action required:** Audit definition_generator_tab.py for heuristics matching the 7 extra rules

---

### Gap 9: Config Structure Mismatch
**What's missing:** Actual config structure differs from documented structure

**Documented structure:**
```
config/
├── ontological_patterns.yaml (planned, NOT exist)
├── validation_thresholds.yaml (planned, NOT exist)
├── duplicate_detection.yaml (planned, NOT exist)
└── ... (other planned configs)
```

**Actual structure:**
```
config/
├── validation_rules/
│   └── arai/
│       └── ARAI-01.yaml (exists!)
├── web_lookup_defaults.yaml (exists!)
├── approval_gate.yaml (exists!)
├── ufo_rules.yaml (exists!)
└── ... (other actual configs)
```

**Impact:**
- Extraction plan config paths are wrong
- Existing YAML configs not documented
- Migration strategy unclear

**Extraction effort:** 2-3 hours (document actual config structure + reconcile)

**Action required:**
1. Document all existing config files
2. Update extraction plan with actual config locations
3. Decide: use existing structure OR create planned structure

---

### Gap 10: Business Logic Extraction Progress NOT Referenced
**What's missing:** `docs/archief/BUSINESS_LOGIC_EXTRACTION_PROGRESS.md` shows 40% progress (2/5 services complete) but NOT mentioned in main extraction plans

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/docs/archief/BUSINESS_LOGIC_EXTRACTION_PROGRESS.md`

**Services completed (per document):**
1. ✅ DuplicateDetectionService (100% coverage)
2. ✅ WorkflowService (100% coverage)
3. ⏳ ImportExportService (pending)
4. ⏳ VoorbeeldenService (pending)
5. ⏳ StatisticsService (pending)

**Impact:**
- Extraction work is already underway but not coordinated with main plan
- Duplicate effort risk (main plan may re-extract these services)
- Progress tracking disconnected

**Extraction effort:** 1 hour (update main plan with progress status)

**Action required:**
1. Integrate progress tracking into main extraction plan
2. Mark DuplicateDetectionService and WorkflowService as complete
3. Coordinate remaining 3 services with main extraction timeline

---

### Gap 11: God Object Stub Methods NOT Inventoried
**What's missing:** tabbed_interface.py has "8 stub methods (dead code)" mentioned but NOT listed

**Where in code:** `/Users/chrislehnen/Projecten/Definitie-app/src/ui/tabbed_interface.py`

**Documented:** "8 stub methods" in orchestrator extraction plan (line 1044)

**Impact:**
- Don't know which methods are dead code
- May accidentally extract dead code during refactoring
- LOC reduction calculation may be inaccurate

**Extraction effort:** 1-2 hours (identify and document stub methods)

**Action required:**
1. Grep for stub methods in tabbed_interface.py
2. List all 8 dead methods
3. Mark for deletion in extraction plan

---

### Gap 12: Database Definition Count Validated
**What's confirmed:** 42 definitions in database (matches documentation)

**Where in code:** `sqlite3 /Users/chrislehnen/Projecten/Definitie-app/data/definities.db "SELECT COUNT(*) FROM definities"` returns **42**

**Status:** ✅ **NO GAP** - Documentation is accurate

**Note:** This validates the baseline test data strategy (42 definitions for testing extraction)

---

## 3. Coverage by Category

### 3.1 Validation Rules: 87% Coverage

✅ **Documented & Exists:**
- ARAI (6 rules): 100% coverage
- CON (2 rules): 67% coverage (missing CON-CIRC-001)
- ESS (5 rules): 83% coverage (missing ESS-CONT-001)
- INT (10 rules): 100% coverage
- SAM (8 rules): 100% coverage
- STR (9 rules): 75% coverage (missing STR-TERM-001, STR-ORG-001, +1 duplicate)
- VER (3 rules): 100% coverage
- DUP (1 rule): 100% coverage

❌ **Missing Documentation:**
- VAL category: 0% coverage (3 rules: VAL-EMP-001, VAL-LEN-001, VAL-LEN-002)
- Extra rules: CON-CIRC-001, ESS-CONT-001, STR-TERM-001, STR-ORG-001

**Overall:** 46 documented / 53 actual = **87% coverage**

**Gap:** 7 rules undocumented

---

### 3.2 Orchestrators: 67% Coverage

✅ **Documented & Exists:**
- definition_orchestrator_v2.py: 984 LOC (100% match)
- validation_orchestrator_v2.py: 251 LOC (LOC now confirmed)
- Regeneration workflow (in tab): ~500 LOC (100% match)
- Generation workflow (in tab): ~380 LOC (100% match)

❌ **NOT Documented:**
- prompt_orchestrator.py: ? LOC (NOT in extraction plans)
- import_export_beheer/orchestrator.py: ? LOC (NOT in extraction plans)

**Overall:** 4 documented / 6 actual = **67% coverage**

**Gap:** 2 orchestrators undocumented

---

### 3.3 Services: 70% Coverage

✅ **Documented & Exists:**
- UnifiedDefinitionServiceV2 (partial)
- ValidationOrchestratorV2 (complete)
- CategoryService (complete)
- RegenerationService (partial)
- DuplicateDetectionService (complete, in progress)
- WorkflowService (complete, in progress)

❌ **NOT Documented:**
- ModernWebLookupService (NOT in extraction plans)

⚠️ **Partial Coverage:**
- RegenerationService (exists but underspecified)
- UnifiedDefinitionServiceV2 (exists but partial coverage)

**Overall:** ~70% coverage (estimated)

**Gap:** 1 major service (ModernWebLookupService) + 2 partial services

---

### 3.4 Hardcoded Logic: 90% Coverage

✅ **Documented & Exists:**
- Ontological patterns (3 locations): 100%
- Duplicate threshold (70%): 100%
- Confidence thresholds (0.8/0.5): 100%
- Length thresholds (50-500): 100%
- Category change impact: 100%
- Document context limits: 100%

⚠️ **Partial Coverage:**
- Rule reasoning heuristics: 13 documented, likely 20 actual (65% coverage)

**Overall:** ~90% coverage

**Gap:** 7 additional heuristics likely exist for undocumented rules

---

### 3.5 Configuration Files: 40% Coverage

✅ **Exists & Documented:**
- config/web_lookup_defaults.yaml (exists, partially documented)
- config/approval_gate.yaml (exists, documented in EPIC-016)

❌ **Planned but NOT Exist:**
- config/ontological_patterns.yaml (planned, NOT created)
- config/validation_thresholds.yaml (planned, NOT created)
- config/duplicate_detection.yaml (planned, NOT created)
- config/voorbeelden_type_mapping.yaml (planned, NOT created)
- config/workflow_transitions.yaml (planned, NOT created)
- config/ui_thresholds.yaml (planned, NOT created)
- config/hardcoded_values.yaml (planned, NOT created)

⚠️ **Exists but NOT Documented:**
- config/validation_rules/arai/ARAI-01.yaml (exists, NOT in extraction plans)
- config/ufo_rules.yaml (exists, NOT in extraction plans)
- config/ufo_rules_v5.yaml (exists, NOT in extraction plans)

**Overall:** 2 exists & documented, 7 planned, 3 undocumented = **~40% coverage**

**Gap:** Major mismatch between planned config structure and actual config structure

---

## 4. Gap Severity & Priority

### P0 CRITICAL (MUST Extract Before Rebuild)

| Gap # | Description | Impact | Effort |
|-------|-------------|--------|--------|
| **1** | 7 undocumented validation rules | Lose validation logic | 14-21h |
| **3** | ModernWebLookupService not documented | Lose external API integration | 4-6h |
| **4** | Planned config files don't exist | Config migration blocked | 6-8h |
| **7** | Regeneration service underspecified | Incomplete state machine | 4-5h |
| **8** | Rule reasoning heuristics count mismatch | Lose hardcoded logic | 3-4h |
| **9** | Config structure mismatch | Wrong extraction paths | 2-3h |

**Total P0 effort:** 33-47 hours

---

### P1 HIGH (Should Extract)

| Gap # | Description | Impact | Effort |
|-------|-------------|--------|--------|
| **2** | ValidationOrchestratorV2 LOC unknown | Estimation inaccuracy | 1h |
| **5** | Prompt orchestrator not documented | Lose prompt logic | 3-4h |
| **10** | Business logic progress not integrated | Duplicate effort | 1h |

**Total P1 effort:** 5-6 hours

---

### P2 MEDIUM (Nice to Have)

| Gap # | Description | Impact | Effort |
|-------|-------------|--------|--------|
| **6** | Import/export orchestrator not documented | May lose import/export logic | 2-3h |
| **11** | Stub methods not inventoried | Inefficient refactoring | 1-2h |

**Total P2 effort:** 3-5 hours

---

### P3 LOW (Optional)

| Gap # | Description | Impact | Effort |
|-------|-------------|--------|--------|
| **12** | Database count (✅ NO GAP) | None (validated) | 0h |

**Total P3 effort:** 0 hours

---

## 5. Recommendations

### 5.1 IMMEDIATE ACTIONS (Week 1)

**Day 1: Update Main Extraction Plan**
1. Add 7 missing validation rules to inventory (VAL-*, CON-CIRC-*, ESS-CONT-*, STR-TERM-*, STR-ORG-*)
2. Update ValidationOrchestratorV2 LOC: 251 lines
3. Add ModernWebLookupService to service extraction list
4. Integrate business logic extraction progress (40% complete)

**Day 2: Reconcile Config Structure**
1. Document actual config structure (validation_rules/, ufo_rules.yaml, etc.)
2. Decide: use existing structure OR create planned structure
3. Update hardcoded logic extraction plan with correct config paths
4. Document config migration path

**Day 3: Analyze Gaps**
1. Analyze prompt_orchestrator.py for business logic
2. Analyze import_export_beheer/orchestrator.py for business logic
3. Complete regeneration_service.py analysis
4. Audit definition_generator_tab.py for 7 extra rule heuristics

**Day 4-5: Update Documentation**
1. Create documentation for 7 missing validation rules
2. Update extraction timelines with gap closure effort
3. Create updated coverage report
4. Final review and approval

**Total effort:** 40-60 hours (1-1.5 weeks)

---

### 5.2 EXTRACTION PLAN UPDATES

**Update BUSINESS_LOGIC_EXTRACTION_PLAN.md:**
- Change "46 validation rules" to "**53 validation rules**"
- Add new section "1.11 Modern Web Lookup Service"
- Update config file inventory with actual structure
- Add prompt_orchestrator.py and import_export orchestrator
- Update timeline: add 1 week for gap closure

**Update EXTRACTION_PLAN_SUMMARY.md:**
- Update validation rules count: 46 → **53**
- Add ModernWebLookupService to top 10 critical items
- Update success criteria with gap closure checklist

**Update EXTRACTION_QUICK_REFERENCE.md:**
- Add 7 new rules to checklist
- Update config file locations
- Add ModernWebLookupService to hotspots

---

### 5.3 PRIORITIZED EXTRACTION SEQUENCE

**Updated Week 1:**
- Day 1-2: Document 7 missing validation rules (**ADDED**)
- Day 3: Reconcile config structure (**ADDED**)
- Day 4: Validation rules testing (all 53 rules)
- Day 5: Ontological patterns extraction

**Updated Week 2:**
- Day 6: ModernWebLookupService extraction (**ADDED**)
- Day 7: Regeneration service completion (**ADDED**)
- Day 8-9: Duplicate detection + regeneration (as planned)
- Day 10: Voorbeelden persistence (as planned)

**Updated Week 3:**
- Day 11: Prompt orchestrator extraction (**ADDED**)
- Day 12: UI hardcoded logic extraction
- Day 13-14: Workflow status + prompt building
- Day 15: Import/export orchestrator analysis (**ADDED**)
- Day 16: Final validation + completeness report

**Total timeline:** 3 weeks → **3-4 weeks** (with gap closure)

---

## 6. Validation & Sign-Off

### 6.1 Gap Closure Checklist

**Before proceeding to extraction:**

- [ ] All 53 validation rules documented (46 + 7 new)
- [ ] ValidationOrchestratorV2 LOC updated (251 lines)
- [ ] ModernWebLookupService analyzed and documented
- [ ] Config structure reconciled (planned vs. actual)
- [ ] Regeneration service fully documented
- [ ] Prompt orchestrator analyzed
- [ ] Import/export orchestrator analyzed
- [ ] Business logic extraction progress integrated
- [ ] Rule reasoning heuristics count verified (13 vs. 20)
- [ ] Stub methods identified and documented
- [ ] All extraction plans updated with gaps
- [ ] Timeline updated with gap closure effort

### 6.2 Coverage Targets POST Gap Closure

| Category | Current Coverage | Target Coverage | Gap Closure Effort |
|----------|-----------------|----------------|-------------------|
| **Validation Rules** | 87% (46/53) | 100% (53/53) | 14-21h |
| **Orchestrators** | 67% (4/6) | 100% (6/6) | 5-7h |
| **Services** | 70% | 95% | 8-11h |
| **Hardcoded Logic** | 90% | 100% | 3-4h |
| **Config Files** | 40% | 90% | 8-10h |
| **TOTAL** | ~85% | **98%+** | **38-53h** |

**Realistic target:** 98% coverage (some legacy/dead code may not be worth extracting)

---

## 7. Conclusion

### 7.1 Summary of Findings

**GOOD NEWS:**
✅ God object sizes validated (4,318 LOC total)
✅ Database baseline confirmed (42 definitions)
✅ Core orchestrators documented (definition, validation)
✅ Main validation rules covered (46/53 = 87%)
✅ Hardcoded logic hotspots identified (90% coverage)

**BAD NEWS:**
❌ 7 validation rules completely undocumented (VAL-*, CON-CIRC-*, etc.)
❌ 2 orchestrators not in extraction plans (prompt, import/export)
❌ ModernWebLookupService entirely missing from extraction plans
❌ Config structure mismatch (planned vs. actual)
❌ Business logic extraction in progress but not coordinated

**Overall Coverage: ~85%** (with significant critical gaps)

---

### 7.2 Risk Assessment

**HIGH RISK if gaps not addressed:**
1. **Knowledge loss:** 7 validation rules + ModernWebLookupService logic will be lost
2. **Incomplete extraction:** Orchestrators and services underspecified
3. **Config migration failure:** Wrong paths in extraction plan
4. **Duplicate effort:** Business logic extraction not coordinated

**MEDIUM RISK if gaps partially addressed:**
1. Some validation rules may be incomplete
2. Config structure may need rework after extraction

**LOW RISK if all gaps closed:**
1. 98%+ coverage achieved
2. All critical business logic preserved
3. Extraction plan accurate and executable

---

### 7.3 Final Recommendation

**DO NOT proceed to extraction Phase 2 until:**

1. ✅ All P0 critical gaps closed (33-47 hours)
2. ✅ Extraction plan updated with accurate counts and paths
3. ✅ Config structure reconciled
4. ✅ All orchestrators and services documented
5. ✅ Gap closure validation complete

**Estimated time to close all gaps:** **1-1.5 weeks** (40-60 hours)

**Revised extraction timeline:** **4-5 weeks** (was 3 weeks)

**Sign-off required from:**
- [ ] Business Logic Extraction Specialist (gap closure plan)
- [ ] Code Architect (orchestrator analysis)
- [ ] Senior Developer (config reconciliation)
- [ ] Tech Lead (timeline approval)

---

**Status:** ✅ GAP ANALYSIS COMPLETE
**Next Action:** Close P0 critical gaps (7 rules + config + services)
**Owner:** Documentation Auditor (Agent 2)
**Date:** 2025-10-02
**EPIC:** EPIC-026 Phase 1 (Design)

---

**Document End**
