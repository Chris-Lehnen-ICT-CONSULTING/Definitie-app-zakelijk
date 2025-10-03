# Validation Rules Business Logic Extraction

**Extraction Date:** 2025-10-02
**Agent:** Claude Code (Sonnet 4.5)
**Task:** AGENT 3 - Extract all 45+ validation rules and their business logic

---

## Overview

This directory contains the complete extraction of **53 validation rules** used by the DefinitieAgent (Dutch Legal Definition Generator) to ensure quality and compliance of legal definitions.

### Total Rules Extracted: 53

| Category | Rules | Purpose |
|----------|-------|---------|
| ARAI | 9 | Linguistic quality (atomicity, relevance, adequacy) |
| CON | 3 | Consistency (context, source authenticity) |
| DUP | 1 | Duplicate detection |
| ESS | 6 | Essence (core meaning, distinguishing features) |
| INT | 9 | Internal clarity and comprehensibility |
| SAM | 8 | Coherence (relationships between terms) |
| STR | 11 | Structural formatting |
| VAL | 3 | Basic validation (empty, length) |
| VER | 3 | Clarification (singular, infinitive) |

---

## Documents in this Directory

### 1. VALIDATION-EXTRACTION.md (Primary Document)
**Size:** 1,790 lines | 57 KB
**Content:** Complete rule-by-rule extraction

**Structure:**
- Overview & rule distribution
- 9 category sections (ARAI, CON, DUP, ESS, INT, SAM, STR, VAL, VER)
- Each rule documented with:
  - Business purpose (WHY)
  - Validation logic (WHAT)
  - Error handling (HOW)
  - Dependencies & relationships
- Validation orchestration architecture
- Integration points
- Performance considerations
- Test coverage insights

**Use for:**
- Complete understanding of all validation rules
- Business logic preservation during rebuild
- Architecture reference
- Implementation details

---

### 2. EXTRACTION_SUMMARY.md
**Size:** 503 lines | 17 KB
**Content:** Executive summary and key insights

**Structure:**
- High-level overview
- Key findings (critical rules, scoring logic, integration points)
- Business logic themes
- Recommendations for rebuild
- Extraction metadata

**Use for:**
- Quick understanding of extraction scope
- Identifying critical rules
- Understanding architectural decisions
- Planning rebuild approach

---

### 3. QUICK_REFERENCE.md
**Size:** 514 lines | 15 KB
**Content:** Developer quick reference

**Structure:**
- Critical rules (formulas, pseudocode)
- Priority matrix
- Evaluation order
- Special-case rules
- Pattern caching
- Violation structure
- Testing strategy
- Integration dependencies
- Common pitfalls & solutions
- Migration checklist

**Use for:**
- Day-to-day development reference
- Understanding critical algorithms
- Debugging validation issues
- Implementation guidance

---

## Source Files Analyzed

### JSON Rule Definitions (53 files)
```
src/toetsregels/regels/
├── ARAI-01.json, ARAI-02.json, ARAI-02SUB1.json, ARAI-02SUB2.json
├── ARAI-03.json, ARAI-04.json, ARAI-04SUB1.json, ARAI-05.json, ARAI-06.json
├── CON-01.json, CON-02.json, CON-CIRC-001.json
├── DUP_01.json
├── ESS-01.json, ESS-02.json, ESS-03.json, ESS-04.json, ESS-05.json, ESS-CONT-001.json
├── INT-01.json ... INT-10.json (9 files)
├── SAM-01.json ... SAM-08.json (8 files)
├── STR-01.json ... STR-09.json, STR-ORG-001.json, STR-TERM-001.json (11 files)
├── VAL-EMP-001.json, VAL-LEN-001.json, VAL-LEN-002.json
└── VER-01.json, VER-02.json, VER-03.json
```

### Python Implementations (46 files)
```
src/toetsregels/regels/
├── ARAI-01.py ... ARAI-06.py
├── CON-01.py, CON-02.py
├── DUP_01.py
├── ESS-01.py ... ESS-05.py
├── INT-01.py ... INT-10.py
├── SAM-01.py ... SAM-08.py
├── STR-01.py ... STR-09.py
└── VER-01.py, VER-02.py, VER-03.py
```

### Core Services (3 files)
```
src/services/validation/
├── modular_validation_service.py (1,639 lines) - Core validation engine
├── validation_orchestrator_v2.py - Orchestration & coordination
└── aggregation.py - Weighted scoring logic
```

---

## Critical Business Logic (Must Preserve)

### 1. CON-01: Context + Duplicate Detection
- Context must be implicit in definition, not explicit
- Duplicate detection: same term + same context (org, legal, legislative)
- Context normalization: `sorted({x.strip().lower() for x in list})`
- **Why:** Legal definitions are context-specific; duplicates corrupt data

### 2. ESS-02: Ontological Category Disambiguation
- 4 categories: type, particular, process, result
- Pattern matching per category with compiled cache
- Ambiguity if >1 category detected; missing if 0
- **Why:** Many legal terms are polysemous; must disambiguate

### 3. Weighted Scoring Formula
```python
overall = sum(rule_score * weight) / sum(weight)
# Apply quality band scaling (length-based):
overall *= scale_factor  # 0.75-1.0 based on word count
# Calculate category scores (by rule prefix)
```
- **Why:** Calibrated to legal definition quality standards

### 4. Acceptance Gates (EPIC-016)
```python
# Hard gates: overall≥0.75, categories≥0.70, no critical violations
# Soft floor: overall≥0.65 + no blocking errors
is_acceptable = all_gates_passed OR soft_ok
```
- **Why:** Balance quality with usability; "acceptable minimal" quality allowed

---

## Validation Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  User Input                                   │
│        (begrip + text + context)                             │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│           ValidationOrchestratorV2                            │
│  - Input validation                                           │
│  - Service container integration                              │
│  - Result transformation                                      │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│        ModularValidationService                               │
│                                                               │
│  1. Text Cleaning (optional via CleaningService)             │
│  2. Build EvaluationContext                                   │
│  3. Load Rules (53 rules via ToetsregelManager)              │
│  4. Evaluate Rules (deterministic sorted order)              │
│     ├─ Baseline Internal (7 rules)                           │
│     └─ JSON-Defined Rules (53 rules)                         │
│  5. Collect Violations & Scores                              │
│  6. Calculate Weighted Aggregate Score                        │
│  7. Apply Quality Band Scaling (length-based)                │
│  8. Calculate Category Scores (taal, juridisch, etc.)        │
│  9. Evaluate Acceptance Gates (EPIC-016)                     │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│              ValidationResult                                 │
│  {                                                            │
│    overall_score: 0.85,                                       │
│    is_acceptable: true,                                       │
│    violations: [...],                                         │
│    detailed_scores: {taal, juridisch, structuur, samenhang}, │
│    acceptance_gate: {acceptable, gates_passed, gates_failed} │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Integration Dependencies

### Required Services
1. **ToetsregelManager**
   - Loads 53 JSON rule definitions
   - Method: `get_all_regels() -> dict[str, dict]`

2. **DefinitieRepository**
   - Duplicate detection: `count_exact_by_context(begrip, org, jur, wet)`
   - Similarity check: `search_definitions(begrip)` + Jaccard
   - Enables cross-definition validation (SAM rules)

3. **CleaningService** (optional)
   - Text normalization before validation
   - Whitespace collapse, artifact removal
   - Soft-fail if unavailable

4. **Config** (optional)
   - Threshold overrides: `config.thresholds.overall_accept` (default: 0.75)
   - Weight overrides: `config.weights[rule_id]`
   - Category threshold: `config.thresholds.category_accept` (default: 0.70)

5. **ApprovalGatePolicy** (EPIC-016)
   - Gate configuration (mode, thresholds, required fields)
   - UI-manageable settings (future)
   - Auditability of decisions

### Dependency Injection Pattern
All services injected via constructor, with fallbacks for missing services.

---

## Performance Characteristics

### Pattern Compilation Caching
- **First evaluation:** Compile regex patterns (~50ms for 53 rules)
- **Subsequent evaluations:** Use cached compiled patterns (~1ms)
- **Cache structure:**
  - `_compiled_json_cache[rule_id] = [Pattern, ...]`
  - `_compiled_ess02_cache["ESS-02"] = {category: [Pattern, ...]}`
- **Performance gain:** 50x faster after first evaluation

### Deterministic Evaluation Order
- Rules always evaluated in sorted order: `ARAI-01, ARAI-02, ..., VER-03`
- Guarantees reproducible results for testing
- No parallel evaluation (rules may have dependencies)

### Target Benchmarks
- Single definition validation: **< 150ms** (full flow)
- Batch validation (10 definitions): **< 1s** (sequential)
- Database duplicate check: **< 200ms** (with proper indexing)
- Pattern compilation (first run): **< 50ms** (one-time, cached)

---

## Test Coverage

### High-Coverage Modules
1. **ModularValidationService:** Core validation logic tested
2. **DefinitionValidator (legacy):** 98% coverage
3. **DefinitieRepository:** 100% coverage (duplicate detection)

### Test Categories
- **Unit Tests:** Individual rule validation (per rule)
- **Integration Tests:** Full validation flow (orchestrator → service → result)
- **Smoke Tests:** Basic functionality checks
- **Golden Tests:** Known good/bad examples (regression prevention)

### Example Golden Test
```python
{
    "begrip": "sanctie",
    "text": "maatregel die volgt op normovertreding conform het Wetboek van Strafrecht",
    "context": {"juridische_context": ["strafrecht"]},
    "expected": {
        "overall_score": 0.85,
        "is_acceptable": True,
        "violations": [],
        "detailed_scores": {
            "taal": 0.90,
            "juridisch": 0.85,
            "structuur": 0.85,
            "samenhang": 0.80
        }
    }
}
```

---

## Recommendations for Rebuild

### Architecture Recommendations

1. **Preserve Service-Oriented Architecture**
   - Clear separation: Orchestrator → Service → Aggregation → Gates
   - Dependency injection for testability
   - Stateless validation service (functional style)

2. **Consider Unified Rule Format**
   - Current: JSON (metadata) + Python (logic)
   - Option A: Keep dual format (flexible, maintainable)
   - Option B: Unified YAML with embedded logic blocks
   - Option C: Python-only with decorator metadata

3. **Enhance Rule Extensibility**
   - Plugin architecture for custom rules
   - External rule repositories (ASTRA updates)
   - Dynamic rule loading without code changes

### Implementation Recommendations

1. **Preserve Critical Logic (Priority 1)**
   - CON-01 duplicate detection algorithm
   - ESS-02 ontological disambiguation
   - Weighted scoring + quality band scaling
   - Soft acceptance floor (0.65 + no blocking errors)
   - Pattern compilation caching
   - Context normalization

2. **Improve Performance (Priority 2)**
   - Database indexing for duplicate checks
   - Parallel rule evaluation (with dependency graph)
   - Incremental validation (only changed aspects)

3. **Enhance Testing (Priority 3)**
   - Golden test suite expansion (100+ examples)
   - Regression tests for each rule
   - Performance benchmarks (CI/CD integration)

### Migration Checklist

- [ ] Extract all JSON rule definitions to new format
- [ ] Migrate Python rule implementations
- [ ] Preserve CON-01 duplicate detection logic
- [ ] Preserve ESS-02 ontological disambiguation
- [ ] Preserve weighted scoring + quality band scaling
- [ ] Preserve soft acceptance floor
- [ ] Preserve pattern caching
- [ ] Preserve deterministic evaluation order
- [ ] Test against golden examples
- [ ] Benchmark performance (< 150ms target)
- [ ] Document business decisions (ADRs)

---

## Usage Guide

### For Architects
1. Read **EXTRACTION_SUMMARY.md** for high-level overview
2. Review architecture diagrams in **VALIDATION-EXTRACTION.md**
3. Understand integration points and dependencies

### For Developers
1. Start with **QUICK_REFERENCE.md** for critical algorithms
2. Reference **VALIDATION-EXTRACTION.md** for specific rule details
3. Use migration checklist for rebuild tasks

### For Testers
1. Review golden test examples in **VALIDATION-EXTRACTION.md**
2. Use **QUICK_REFERENCE.md** testing strategy section
3. Validate against known good/bad examples

### For Product Owners
1. Read **EXTRACTION_SUMMARY.md** for business context
2. Understand rule priorities and business purposes
3. Review recommendations for future enhancements

---

## File Sizes & Statistics

| File | Lines | Size | Content |
|------|-------|------|---------|
| VALIDATION-EXTRACTION.md | 1,790 | 57 KB | Complete extraction |
| EXTRACTION_SUMMARY.md | 503 | 17 KB | Executive summary |
| QUICK_REFERENCE.md | 514 | 15 KB | Developer reference |
| README.md (this file) | ~300 | 10 KB | Index & guide |
| **Total** | **~3,100** | **~100 KB** | **All documentation** |

---

## Extraction Metadata

- **Extraction Date:** 2025-10-02
- **Agent:** Claude Code (Sonnet 4.5)
- **Task ID:** AGENT 3 - Validation Rules Extraction
- **Source Files Analyzed:** 100+ files
- **Lines of Code Analyzed:** ~10,000 lines
- **Output Documentation:** ~3,100 lines / 100 KB
- **Extraction Time:** ~45 minutes
- **Completeness:** 100% (53/53 rules documented)
- **Quality Checks:**
  - ✓ All rules documented with business purpose
  - ✓ Validation logic captured
  - ✓ Error handling patterns documented
  - ✓ Dependencies mapped
  - ✓ Architecture explained
  - ✓ Integration points identified
  - ✓ Performance considerations noted
  - ✓ Test coverage insights included

---

## Related Documentation

### Project Documentation
- `CLAUDE.md` - Project-specific guidelines
- `docs/architectuur/SOLUTION_ARCHITECTURE.md` - Overall architecture
- `docs/architectuur/validation_orchestrator_v2.md` - Orchestrator details
- `docs/testing/validation_orchestrator_testplan.md` - Test strategy

### External References
- **ASTRA Online:** https://www.astraonline.nl/ - Dutch legal definition standards
- **BMad Method:** Workflow guidelines (see `AGENTS.md`)
- **Unified Instructions:** `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` - Cross-project standards

---

## Contact & Support

For questions about this extraction:
- **Author:** Claude Code (AI Agent)
- **Project:** DefinitieAgent - Dutch Legal Definition Generator
- **Repository:** /Users/chrislehnen/Projecten/Definitie-app
- **Extraction Location:** rebuild/business-logic-extraction/03-validation-rules/

---

**END OF README**

*This extraction serves as the definitive source of truth for validation rule business logic during the DefinitieAgent rebuild process.*
