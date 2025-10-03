---
id: EPIC-026-EXTRACTION-PLAN-SUMMARY
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: business-logic-specialist
status: complete
type: executive-summary
---

# Business Logic Extraction Plan - Executive Summary

**Full Plan:** See `BUSINESS_LOGIC_EXTRACTION_PLAN.md` (33 pages, comprehensive)

**Mission:** Extract ALL business logic before rebuild to prevent knowledge loss

---

## Quick Facts

| Metric | Value |
|--------|-------|
| **Total Codebase** | 83,319 LOC |
| **Validation Rules** | 46 files (dual JSON+Python) |
| **Hidden Orchestrators** | ~1,113 LOC |
| **Hardcoded Patterns** | 728 occurrences in 99 files |
| **God Objects** | 3 files (6,133 LOC total) |
| **Test Data** | 42 definitions in database |
| **Extraction Duration** | 2-3 weeks |

---

## What We're Extracting (Top 10 Critical Items)

### Priority 1: MUST Extract (Week 1)
1. **46 Validation Rules** - Dutch legal domain expertise
   - Dual format: JSON metadata + Python validators
   - Categories: ARAI, CON, ESS, INT, SAM, STR, VER, DUP
   - Effort: 3 days

2. **Ontological Category Logic** - Hardcoded in 3 locations!
   - Patterns for: proces, type, resultaat, exemplaar
   - 6-step protocol with 3-level fallback
   - Effort: 1 day

3. **Definition Generation Orchestration** - 380 LOC god method
   - 10-step workflow
   - 5+ service orchestration
   - Effort: 1 day

### Priority 2: SHOULD Extract (Week 2)
4. **Duplicate Detection** - 3-stage matching algorithm
   - 70% Jaccard similarity threshold (hardcoded!)
   - Exact → Synonym → Fuzzy matching
   - Effort: 2 days

5. **Regeneration Workflows** - State machine
   - Category change impact analysis
   - Context preservation rules
   - Effort: 2 days

6. **Voorbeelden Persistence** - Complex transaction
   - Type normalization mapping
   - Voorkeursterm single source policy
   - Effort: 1 day

### Priority 3: CAN Extract (Week 3)
7. **UI Hardcoded Logic** - Thresholds and patterns
8. **Workflow Status Management** - State transitions
9. **Prompt Building** - Module orchestration
10. **Performance Optimizations** - Caching strategies

---

## Timeline Overview

```
Week 1: CRITICAL PATH (Must-Have)
├── Day 1-2: Validation Rules (46 rules)
├── Day 3: Testing validation rules against 42 definitions
├── Day 4: Ontological Category Logic
└── Day 5: Generation Orchestration Workflow

Week 2: IMPORTANT LOGIC (Should-Have)
├── Day 6-7: Duplicate Detection Algorithm
├── Day 8-9: Regeneration State Machine
└── Day 10: Voorbeelden Transaction Logic

Week 3: POLISH & VALIDATION (Can-Have)
├── Day 11-12: UI Hardcoded Logic Extraction
├── Day 13: Workflow Status Management
├── Day 14-15: Prompt Building Documentation
└── Day 16: Final Validation & Completeness Report
```

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Incomplete extraction** | Rebuild fails | Grep ALL patterns, cross-reference 42 test definitions |
| **Logic ambiguity** | Wrong behavior | Test EVERY edge case against OLD system |
| **Domain knowledge loss** | Missing legal expertise | Capture ALL ASTRA references, interview experts |
| **Time overrun** | > 3 weeks | Daily tracking, prioritize MUST items only |

---

## Success Criteria

**Minimum Acceptable Criteria (MAC):**
- ✅ 100% of MUST-extract items documented
- ✅ 90%+ of SHOULD-extract items documented
- ✅ 42 baseline definitions - 100% validation match
- ✅ 42 baseline definitions - 100% category match
- ✅ All workflows documented with diagrams
- ✅ All hardcoded thresholds extracted to config

**DONE = Rebuild team confirms: "We have enough to rebuild without knowledge loss"**

---

## Major Deliverables

### Documentation (15+ files)
- Validation Rules Catalog (46 rules documented)
- Workflow Diagrams (5 sequence diagrams)
- Algorithm Specifications (4 algorithms)
- Business Rules Catalog (CSV)
- Hardcoded Logic Inventory
- Extraction Completeness Report

### Configuration (7 new files)
- `config/ontological_patterns.yaml`
- `config/validation_thresholds.yaml`
- `config/duplicate_detection.yaml`
- `config/voorbeelden_type_mapping.yaml`
- `config/workflow_transitions.yaml`
- `config/ui_thresholds.yaml`
- `config/hardcoded_values.yaml`

### Test Suite (8 test files)
- Baseline validation tests (46 rules × 42 definitions)
- Categorization baseline
- Duplicate detection baseline
- Generation workflow tests
- Regeneration tests
- Edge case tests
- Completeness validation

### Baseline Data
- 42 definitions export (JSON)
- OLD system validation results
- OLD system categorization
- OLD system duplicate detection
- OLD system regeneration outputs

---

## Critical Hardcoded Logic Hotspots

### 1. Ontological Patterns (DUPLICATED 3x!)
**Location:** `src/ui/tabbed_interface.py` L354-418
```python
patterns = {
    "proces": ["atie", "eren", "ing", "verificatie", ...],
    "type": ["bewijs", "document", "middel", ...],
    "resultaat": ["besluit", "uitslag", "rapport", ...],
    "exemplaar": ["specifiek", "individueel", ...]
}
```
**Problem:** Same patterns in 3 different methods!

### 2. Validation Thresholds (Scattered)
- Length: 50-500 chars (ARAI-01)
- Confidence: 0.8 high, 0.5 medium, <0.5 low
- Similarity: 70% Jaccard threshold
- Sentence count: max 3 (SAM-01)
- Optimal length: 100-300 chars (VER-01)

### 3. Rule Reasoning (DUPLICATED in UI!)
**Location:** `src/ui/components/definition_generator_tab.py` L1771-1835
**Problem:** 7 validation rules logic duplicated in UI rendering!

---

## Validation Strategy

### Baseline Testing with 42 Definitions

**Export baseline:**
```bash
python scripts/export_baseline_definitions.py
# Creates: docs/business-logic/baseline_42_definitions.json
```

**Compare OLD vs NEW:**
```python
# After rebuild
baseline = load_baseline()
old_results = run_old_validation(baseline)
new_results = run_new_validation(baseline)

assert old_results == new_results  # 100% match required!
```

**Match Metrics:**
- Validation score match: 100%
- Category assignment match: 100%
- Duplicate detection match: 100%
- Regeneration output match: ≥95% (allow edge case differences)

---

## Next Steps

### Immediate Actions (Day 1)
1. ✅ Review this plan with team
2. ✅ Set up extraction workspace: `docs/business-logic/`
3. ✅ Export 42 baseline definitions
4. ✅ Begin validation rules extraction (ARAI-01 first)

### Quality Gates
- **End of Week 1:** 46 rules + categorization + orchestration documented
- **End of Week 2:** Duplicate + regeneration + voorbeelden documented
- **End of Week 3:** All extracted, 100% baseline match, completeness report

### Handoff to Rebuild
- Deliver all documentation, configs, tests, baselines
- Train rebuild team on extracted logic
- **GO/NO-GO decision:** Ready to rebuild?

---

## Templates & Resources

**Full plan includes:**
- Validation Rule Documentation Template (detailed)
- Workflow Documentation Template (with Mermaid)
- Business Rules Catalog Template (CSV)
- Hardcoded Logic Inventory Template
- Extraction Completeness Checklist (50+ items)
- Edge Cases Documentation Template

**See:** `BUSINESS_LOGIC_EXTRACTION_PLAN.md` for full details

---

## Contact

**Questions about extraction plan?**
- Read full plan first (33 pages, comprehensive)
- Check templates for guidance
- Escalate ambiguous business logic to domain experts

**Daily standup:**
- What did you extract yesterday?
- What are you extracting today?
- Any blockers? (ambiguous logic, missing docs, etc.)

---

**Status:** ✅ PLAN COMPLETE - READY TO EXECUTE
**Next Action:** Begin Day 1 - Validation Rules Extraction
**Owner:** Business Logic Extraction Specialist
**Date:** 2025-10-02
