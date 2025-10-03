---
id: EPIC-026-HARDCODED-LOGIC-EXTRACTION-SUMMARY
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: senior-developer
status: draft
priority: CRITICAL
---

# Hardcoded Logic Extraction - Executive Summary

**Full Plan:** `hardcoded_logic_extraction_plan.md` (61,957 characters, comprehensive analysis)

---

## The Problem (TL;DR)

**TWO CRITICAL CATEGORIES** of hardcoded business logic block EPIC-026 refactoring:

1. **Rule Reasoning Logic** (definition_generator_tab.py)
   - 70 LOC of hardcoded validation heuristics
   - Duplicates logic already in `src/toetsregels/regels/*.json`
   - 13 rules hardcoded in if/else chains

2. **Ontological Patterns** (tabbed_interface.py)
   - 42 pattern strings **DUPLICATED IN 3 DIFFERENT METHODS**
   - 100% duplication between `_generate_category_reasoning()` and `_get_category_scores()`
   - NOT configurable, NOT maintainable

**Impact:**
- Cannot extract services cleanly (hardcoded logic stays in services)
- Changing patterns requires editing 3 methods
- High regression risk
- NOT data-driven

---

## The Solution (TL;DR)

**Extract ALL hardcoded logic to YAML configs BEFORE god object refactoring**

### New Config Files

```
config/
├── validation/
│   └── rule_reasoning_config.yaml      # 13 rule heuristics
└── ontology/
    └── category_patterns.yaml          # 42 patterns (single source!)
```

### New Services

```
src/services/
├── validation/
│   └── rule_reasoning_service.py       # Data-driven rule reasoning
└── ontology/
    └── ontological_pattern_service.py  # Data-driven pattern matching
```

### Config Infrastructure

```
src/config/
└── config_loader.py                    # YAML loader with Pydantic validation
```

---

## Timeline (TL;DR)

**Duration:** 2 weeks (parallel to EPIC-026 Phase 1 Days 3-5)

**Week 1: Rule Reasoning**
- Days 1-2: Config schema + loader + validation
- Days 3-4: RuleReasoningService + tests
- Day 5: Integration + backward compat validation

**Week 2: Ontological Patterns**
- Days 6-7: Pattern config schema + loader
- Days 8-9: OntologicalPatternService + tests
- Day 10: Integration + cleanup (remove 3-way duplication!)

**CRITICAL:** EPIC-026 Phase 2 (Extraction) CANNOT start until this is COMPLETE.

---

## Impact on EPIC-026 (TL;DR)

### Complexity Reduction

| Service | LOC Before | LOC After | Reduction |
|---------|-----------|-----------|-----------|
| ValidationResultsPresentationService | 70 hardcoded | 5 delegated | **-65 LOC** |
| OntologicalCategoryService | 150 hardcoded | 20 delegated | **-130 LOC** |
| DefinitionGenerationOrchestrator | 380 + patterns | 330 clean | **-50 LOC** |
| **TOTAL** | | | **-245 LOC** |

### Timeline Impact

- **+2 weeks:** Logic extraction (parallel track)
- **-1 week:** Faster service extraction (simpler services)
- **Net:** +1 week to overall EPIC-026 timeline

### Quality Impact

✅ Extracted services are data-driven from Day 1
✅ No need to refactor services again later
✅ Better testability (config mocks)
✅ Better maintainability (YAML, not code)

---

## Decision Point (TL;DR)

**RECOMMENDATION:** Extract logic BEFORE god object refactoring

**Rationale:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Extract BEFORE** | ✅ Reduces god object complexity FIRST<br>✅ Smaller service scope<br>✅ Lower risk (one change at a time) | ❌ +2 weeks timeline | **CHOSEN** |
| **Extract DURING** | ✅ Faster timeline | ❌ Two changes at once (HIGH RISK!)<br>❌ Cannot test independently | **REJECTED** |
| **Extract AFTER** | ✅ Services separated | ❌ Must refactor services AGAIN<br>❌ Hardcoded logic stays in NEW code | **REJECTED** |

---

## Code Example (TL;DR)

### BEFORE: Hardcoded (70 lines)

```python
def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
    rid = ensure_string(rule_id).upper()
    m = self._compute_text_metrics(text)
    w, c, cm = m.get("words", 0), m.get("chars", 0), m.get("commas", 0)

    if rid == "VAL-EMP-001":
        return f"Niet leeg (tekens={c} > 0)." if c > 0 else ""
    if rid == "VAL-LEN-001":
        return f"Lengte OK: {w} woorden ≥ 5 en {c} tekens ≥ 15." if (w >= 5 and c >= 15) else ""
    # ... 11 more hardcoded rules (70 lines total)
```

### AFTER: Data-Driven (5 lines)

```python
def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
    service = get_rule_reasoning_service()
    return service.build_pass_reason(rule_id, text, begrip)
```

**Logic moved to:** `config/validation/rule_reasoning_config.yaml`

```yaml
rules:
  VAL-EMP-001:
    pass_reason_template: "Niet leeg (tekens={chars} > 0)."
    logic:
      type: "threshold_check"
      metric: "chars"
      operator: ">"
      threshold: 0
```

**Result:**
- UI: 70 LOC → 5 LOC (**-65 LOC**)
- Logic: Code → Config (configurable without code changes!)
- Testability: Hardcoded → Mockable config

---

## Pattern Duplication Example (TL;DR)

### BEFORE: 3-Way Duplication (150 lines)

```python
# Method 1: _generate_category_reasoning (lines 354-405)
patterns = {
    "proces": ["atie", "eren", "ing", "verificatie", ...],  # 15 patterns
    "type": ["bewijs", "document", "middel", ...],          # 10 patterns
    # ... 42 patterns total
}

# Method 2: _get_category_scores (lines 426-478)
proces_indicators = ["atie", "eren", "ing", "verificatie", ...]  # EXACT DUPLICATE!
type_indicators = ["bewijs", "document", "middel", ...]          # EXACT DUPLICATE!
# ... 42 patterns total - 100% DUPLICATION!

# Method 3: _legacy_pattern_matching (lines 334-345)
if any(begrip_lower.endswith(p) for p in ["atie", "ing", "eren"]):  # Partial overlap
    return "Proces patroon gedetecteerd"
# ... 9 patterns total (subset of above)
```

**DUPLICATION:** 42 patterns × 2 methods + 9 patterns × 1 method = **93 pattern instances!**

### AFTER: Single Source of Truth (20 lines)

```python
# All 3 methods delegate to service
def _generate_category_reasoning(self, begrip, category, scores):
    service = get_ontological_pattern_service()
    return service.generate_reasoning(begrip, category, scores)

def _get_category_scores(self, begrip):
    service = get_ontological_pattern_service()
    return service.calculate_scores(begrip)

def _legacy_pattern_matching(self, begrip):
    service = get_ontological_pattern_service()
    return service.legacy_match(begrip)
```

**Patterns moved to:** `config/ontology/category_patterns.yaml`

```yaml
categories:
  proces:
    all_patterns:
      - "atie"
      - "eren"
      - "ing"
      - "verificatie"
      # ... 15 patterns total (SINGLE SOURCE!)
```

**Result:**
- Duplication: 93 instances → 42 instances (**-55% duplication**)
- Maintenance: Edit 3 methods → Edit 1 YAML file
- Consistency: Impossible to get out of sync

---

## Success Criteria (TL;DR)

**Logic Extraction COMPLETE when:**

- [ ] All 13 rule heuristics in `rule_reasoning_config.yaml`
- [ ] All 42 patterns in `category_patterns.yaml` (zero duplication!)
- [ ] Config loader with Pydantic validation
- [ ] RuleReasoningService + OntologicalPatternService implemented
- [ ] 100% backward compatibility (old vs new identical output)
- [ ] 100% test coverage for services
- [ ] <10% performance overhead
- [ ] Hardcoded logic REMOVED from UI (3 methods refactored)
- [ ] Code review approved
- [ ] Merged to main

---

## Risk Assessment (TL;DR)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Config loading fails | CRITICAL | ✅ Schema validation<br>✅ Fallback to embedded config |
| Behavior regressions | CRITICAL | ✅ Backward compat tests (11+ cases)<br>✅ Easy rollback plan |
| Performance regressions | MEDIUM | ✅ Config caching<br>✅ Benchmarks (<0.1ms overhead) |
| Timeline overruns | MEDIUM | ✅ 2-week buffer<br>✅ Daily standups |

---

## Next Steps (TL;DR)

**Immediate:**
1. ✅ Review this extraction plan
2. ✅ Approve parallel track approach
3. ✅ Assign senior developer + code architect
4. ✅ Create config directories

**Week 1:**
1. Implement rule reasoning extraction
2. Test backward compatibility
3. Integrate with definition_generator_tab

**Week 2:**
1. Implement pattern extraction
2. Test backward compatibility
3. Integrate with tabbed_interface
4. ELIMINATE 3-way duplication!

**Week 3+:**
1. Begin EPIC-026 Phase 2 (Service Extraction)
2. Use clean, data-driven services
3. Celebrate NO hardcoded logic in extracted code!

---

## Documentation Structure

```
docs/backlog/EPIC-026/phase-1/
├── hardcoded_logic_extraction_plan.md       # Full plan (61,957 chars)
│   ├── Part 1: Complete Logic Inventory
│   ├── Part 2: Data-Driven Design (YAML schemas)
│   ├── Part 3: Migration Strategy
│   ├── Part 4: Integration with EPIC-026
│   ├── Part 5: Testing Strategy
│   ├── Part 6: Risk Assessment
│   ├── Part 7: Success Criteria
│   └── Part 8: Code Examples
│
└── hardcoded_logic_extraction_summary.md    # This summary (TL;DR)
```

---

## Key Metrics

**Hardcoded Logic Count:**
- Rule reasoning: 13 heuristics (70 LOC)
- Ontological patterns: 42 patterns (93 instances across 3 methods)
- **TOTAL:** 55 distinct pieces of business logic to extract

**Duplication:**
- Pattern duplication: 100% (42 patterns × 2 methods)
- Total duplication instances: 42 patterns
- **Reduction:** 93 instances → 42 instances (**-55%**)

**LOC Impact:**
- UI code reduction: -200 LOC (hardcoded logic removed)
- New service code: +250 LOC (reusable, testable)
- Config code: +150 LOC (YAML, easily editable)
- **Net:** More code, but BETTER architecture

**Timeline:**
- Extraction: 2 weeks (parallel)
- Integration: Included in extraction
- **EPIC-026 Impact:** +1 week net (2 weeks added, 1 week saved later)

---

**Status:** DRAFT - Ready for Review
**Full Plan:** See `hardcoded_logic_extraction_plan.md` for complete details
**Author:** Senior Developer
**Date:** 2025-10-02
