# Validation Rules Extraction Summary

**Date:** 2025-10-02
**Agent:** Claude Code (Sonnet 4.5)
**Task:** AGENT 3 - Extract all 45+ validation rules business logic

---

## Extraction Scope

### Files Analyzed
- **53 JSON rule definitions:** `src/toetsregels/regels/*.json`
- **46 Python implementations:** `src/toetsregels/regels/*.py`
- **Core validation service:** `src/services/validation/modular_validation_service.py` (1639 lines)
- **Orchestrator:** `src/services/validation/validation_orchestrator_v2.py`
- **Aggregation logic:** `src/services/validation/aggregation.py`

### Total Rules Extracted: 53

| Category | Rules | Priority | Purpose |
|----------|-------|----------|---------|
| ARAI | 9 | H:1, M:8 | Linguistic quality (atomicity, relevance, adequacy) |
| CON | 3 | H:3 | Consistency (context, source authenticity) |
| DUP | 1 | H:1 | Duplicate detection |
| ESS | 6 | H:5, M:1 | Essence (core meaning, distinguishing features) |
| INT | 9 | H:3, M:6 | Internal clarity and comprehensibility |
| SAM | 8 | H:4, M:4 | Coherence (relationships between terms) |
| STR | 11 | H:4, M:7 | Structural formatting |
| VAL | 3 | H:3 | Basic validation (empty, length) |
| VER | 3 | H:1, M:2 | Clarification (singular, infinitive) |

---

## Key Findings

### 1. Dual Architecture (JSON + Python)
- **JSON files** define rule metadata, patterns, examples
- **Python files** implement validation logic
- **ModularValidationService** evaluates both types dynamically

### 2. Critical Rules for Legal Definitions

#### CON-01: Context Management (HIGHEST PRIORITY)
- Context must be implicit, NOT explicit in definition text
- Duplicate detection: same term + context + synonyms
- Database integration: `DefinitieRepository.count_exact_by_context()`

#### CON-02: Authentic Source Basis
- Definitions must reference official sources (legislation, policy)
- Pattern matching for legal references (AVG, WvSr, articles)

#### ESS-02: Ontological Category Disambiguation
- Polysemy resolution: type vs. particular vs. process vs. result
- Prevents definitional ambiguity in multi-meaning terms

#### ARAI-06: Composite Structure Rule
- Combines 3 checks: no article start, no copula, no self-reference
- Ensures definitions are reusable and non-circular

### 3. Validation Orchestration Flow

```
User Input (begrip + text + context)
    ↓
ValidationOrchestratorV2
    ↓
ModularValidationService
    ↓
┌─────────────────────────────────────┐
│ 1. Text Cleaning (optional)         │
│ 2. Build EvaluationContext          │
│ 3. Evaluate 53 rules (deterministic)│
│ 4. Collect violations & scores      │
│ 5. Calculate weighted aggregate     │
│ 6. Apply quality band scaling       │
│ 7. Calculate category scores        │
│ 8. Evaluate acceptance gates        │
└─────────────────────────────────────┘
    ↓
ValidationResult {
    overall_score: 0.85,
    is_acceptable: true,
    violations: [...],
    detailed_scores: {taal, juridisch, structuur, samenhang},
    acceptance_gate: {acceptable, gates_passed, gates_failed}
}
```

### 4. Scoring & Aggregation Logic

#### Weighted Scoring
```python
overall_score = Σ(rule_score * weight) / Σ(weight)

# Weight assignment:
# - High priority: 1.0
# - Medium priority: 0.7
# - Low priority: 0.4
# - Excluded (weight=0.0): baseline internal + ARAI family
```

#### Quality Band Scaling
```python
# Length-based penalty/bonus
if word_count < 12: scale = 0.75    # Too short
elif word_count < 20: scale = 0.9   # Short but acceptable
elif word_count > 100: scale = 0.85 # Too long
elif word_count > 60: scale = 0.9   # Approaching long
else: scale = 1.0                   # Ideal length

overall_score *= scale
```

#### Category Scores
```python
detailed_scores = {
    "taal": avg([ARAI, VER rule scores]),
    "juridisch": avg([ESS, VAL rule scores]),
    "structuur": avg([STR, INT rule scores]),
    "samenhang": avg([CON, SAM rule scores])
}
```

#### Acceptance Gates (EPIC-016)
```python
gates = {
    "no_critical_violations": critical_count == 0,
    "overall_threshold": overall_score >= 0.75,
    "category_thresholds": all(cat_score >= 0.70 for cat in categories)
}

# Soft acceptance floor:
soft_ok = (overall >= 0.65) AND (no blocking errors)
is_acceptable = all_gates_passed OR soft_ok
```

### 5. Rule Dependencies & Relationships

#### Composite Rules
- **ARAI-06** = STR-01 + STR-02 + SAM-05

#### Parent-Child Rules
- **ARAI-02** → ARAI-02SUB1, ARAI-02SUB2
- **ARAI-04** → ARAI-04SUB1

#### Conceptual Relationships
- ARAI-05 ↔ INT-10 (implicit assumptions vs. inaccessible knowledge)
- CON-CIRC-001 ↔ SAM-05 (circular definitions)
- ESS-01 ↔ INT-06 (essence vs. explanations)

### 6. Business Logic Themes

#### Theme 1: Linguistic Quality (ARAI)
- **No verbs as core** - prevent action-based definitions
- **No vague container terms** - avoid "aspect", "element", "process" without specification
- **Limit adjectives** - reduce subjectivity
- **No modal verbs** - avoid "can", "should", "may"
- **No implicit assumptions** - self-contained definitions

#### Theme 2: Context Management (CON)
- **Implicit context** - context in meaning, not text
- **Duplicate detection** - same term + context + synonyms
- **Authentic source** - legal basis required

#### Theme 3: Semantic Precision (ESS)
- **Ontological clarity** - type vs. particular vs. process vs. result
- **Unique identification** - countable terms need unique IDs
- **Testability** - objective criteria required
- **Distinguishing features** - contrast with related terms

#### Theme 4: Structural Integrity (STR)
- **Noun start** - definitions begin with noun, not verb/article
- **No tautology** - kick-off ≠ term itself
- **Not just synonym** - must add differentia
- **Genus + differentia** - proper definitional structure

#### Theme 5: Clarity & Comprehensibility (INT)
- **Single sentence** - compact, no complex clauses
- **No decision rules** - describe concept, not application logic
- **Clear references** - pronouns and articles unambiguous
- **Positive formulation** - avoid negatives

#### Theme 6: Coherence (SAM)
- **Consistent qualifications** - don't deviate from base meaning
- **No base repetition** - qualified terms use genus+differentia
- **Proper compounds** - start with specializing component

---

## Critical Integration Points

### 1. ToetsregelManager
- Loads 53 JSON rule definitions
- Provides `get_all_regels()` → dict of rule configs

### 2. DefinitieRepository
- **CON-01 duplicate detection:** `count_exact_by_context(begrip, org, jur, wet)`
- **DUP-01 similarity check:** `search_definitions(begrip)` + Jaccard similarity
- Enables cross-definition validation (SAM rules)

### 3. ServiceContainer (DI)
- Injects: ToetsregelManager, CleaningService, Config, Repository
- Singleton pattern for ModularValidationService
- Ensures consistent dependencies

### 4. ApprovalGatePolicy (EPIC-016)
- **Overall threshold:** 0.75 (configurable)
- **Category threshold:** 0.70 (configurable)
- **Required fields** enforcement before approval
- UI-manageable configuration (future)
- Auditability of decisions

### 5. CleaningService
- Optional text normalization before validation
- Whitespace collapse, artifact removal
- Soft-fail if unavailable

---

## Performance Optimizations

### 1. Pattern Compilation & Caching
```python
# Compiled once per rule
_compiled_json_cache[rule_id] = [re.compile(p) for p in patterns]

# Compiled once per category (ESS-02)
_compiled_ess02_cache["ESS-02"] = {
    "type": [compiled patterns],
    "particulier": [...],
    "proces": [...],
    "resultaat": [...]
}
```

### 2. Deterministic Evaluation Order
```python
# Rules evaluated in sorted order for reproducibility
for code in sorted(self._internal_rules):
    score, violation = self._evaluate_rule(code, ctx)
```

### 3. Lazy Repository Initialization
```python
# Avoid circular imports, initialize on first use
try:
    from database.definitie_repository import DefinitieRepository
    self.repository = DefinitieRepository()
except Exception:
    self.repository = None  # Soft-fail
```

### 4. Batch Validation Support
```python
async def batch_validate(items, max_concurrency=1):
    # Sequential by default (max_concurrency=1)
    # Parallel with semaphore control if max_concurrency > 1
    semaphore = asyncio.Semaphore(max_concurrency)
```

---

## Error Handling Patterns

### 1. Structured Violations
```python
violation = {
    "code": "RULE-ID",
    "severity": "error" | "warning",
    "severity_level": "critical" | "high" | "medium" | "low",
    "message": "User-friendly NL description",
    "description": "Same as message",
    "rule_id": "RULE-ID",
    "category": "taal" | "juridisch" | "structuur" | "samenhang",
    "suggestion": "Actionable fix (NL)",
    "metadata": {  # Optional
        "detected_pattern": "regex",
        "position": 42,
        "existing_definition_id": 123  # For CON-01
    }
}
```

### 2. User-Friendly Messaging
- **Emoji indicators:** ✔️ (pass), ❌ (fail), 🟡 (warning)
- **Dutch language** throughout
- **Actionable suggestions** in every violation

### 3. Graceful Degradation
- **Missing services** → skip optional checks
- **Invalid patterns** → log warning, continue
- **Soft-fail** on non-critical errors

---

## Business Logic Preservation Priorities

### CRITICAL (Must Preserve Exactly)
1. **CON-01 duplicate detection logic** - term + context + synonyms matching
2. **ESS-02 ontological disambiguation** - 4-category pattern matching
3. **Weighted scoring formula** - priority-based weights + quality scaling
4. **Acceptance gates** - overall + category thresholds + blocking errors
5. **Pattern compilation caching** - performance optimization

### HIGH (Preserve Core Logic)
1. **All 53 rule patterns** - regex patterns define rule behavior
2. **Category score calculation** - rule prefix-based aggregation
3. **Soft acceptance floor** - 0.65 threshold with no blocking errors
4. **Baseline internal rules** - 7 safeguard rules always evaluated

### MEDIUM (Preserve Intent)
1. **Rule dependency relationships** - parent-child, composite rules
2. **Error message templates** - user-friendly NL messages
3. **Generation hints** - AI prompting guidance per rule

---

## Extraction Deliverables

### Primary Document
**`VALIDATION-EXTRACTION.md`** (25,000+ words)
- Complete rule-by-rule extraction
- Business purpose for each rule
- Validation logic details
- Error handling patterns
- Dependencies and relationships
- Orchestration architecture
- Integration points
- Performance considerations

### Content Structure
1. Overview & Distribution (by category)
2. ARAI Category (9 rules)
3. CON Category (3 rules)
4. DUP Category (1 rule)
5. ESS Category (6 rules)
6. INT Category (9 rules)
7. SAM Category (8 rules)
8. STR Category (11 rules)
9. VAL Category (3 rules)
10. VER Category (3 rules)
11. Validation Orchestration (architecture)
12. Rule Dependencies & Relationships
13. Business Logic by Theme
14. Critical Integration Points
15. Performance Considerations
16. Error Handling Philosophy
17. Test Coverage Insights
18. Future Enhancement Opportunities

### Extraction Quality Metrics
- **Completeness:** 53/53 rules documented (100%)
- **Detail Level:** Business purpose + validation logic + error handling for each
- **Architecture Coverage:** Orchestrator + Service + Aggregation + Gates
- **Integration Mapping:** Repository + ToetsregelManager + DI Container + Gates
- **Performance Notes:** Caching + ordering + lazy init + batch support

---

## Key Insights for Rebuild

### 1. Dual Format is Intentional
- **JSON:** Declarative rule metadata (patterns, examples, priority)
- **Python:** Imperative special-case logic (ESS-02, SAM-02, SAM-04, VER-03)
- **Reason:** Generic pattern matching + custom business logic
- **Rebuild Implication:** Preserve both layers or create unified format

### 2. Weight Exclusion Strategy
- **Baseline internal rules** (VAL-*, STR-*) excluded from scoring (weight=0.0)
- **ARAI family** excluded from scoring (language-focused, not core quality)
- **Reason:** Prevent double-counting; they're safeguards, not quality metrics
- **Rebuild Implication:** Maintain weight=0.0 for these rules

### 3. Context Normalization is Critical
- **CON-01** normalizes context lists: `sorted(set(lower(strip(x))))` for comparison
- **Wettelijke basis** is order-independent (sorted before comparison)
- **Reason:** User can enter contexts in any order; must match existing definitions
- **Rebuild Implication:** Preserve exact normalization logic

### 4. Soft Acceptance Floor is Business Policy
- **Hard gates:** overall≥0.75, categories≥0.70, no critical violations
- **Soft floor:** overall≥0.65 + no blocking errors → acceptable
- **Reason:** Balance quality standards with practical usability
- **Rebuild Implication:** Document this business decision clearly

### 5. Quality Band Scaling is Calibrated
- **Scale factors:** 0.75 (too short), 0.85 (too long), 0.9 (approaching limits), 1.0 (ideal)
- **Reason:** Align with "golden bands" - acceptable minimal ≈ 0.60-0.75, high ≥ 0.75, perfect ≥ 0.80
- **Rebuild Implication:** These are tuned values; preserve or re-calibrate carefully

### 6. Rule Evaluation Order Matters
- **Deterministic:** Sorted by rule code (ARAI-01, ARAI-02, ..., VER-03)
- **Reason:** Reproducible results for testing and debugging
- **Rebuild Implication:** Maintain sorted evaluation order

---

## Recommendations for Rebuild

### Architecture Recommendations

1. **Preserve Service-Oriented Architecture**
   - ModularValidationService as core engine
   - ValidationOrchestratorV2 as coordinator
   - ApprovalGatePolicy as business rules layer
   - Clear separation of concerns

2. **Consider Unified Rule Format**
   - Current: JSON (metadata) + Python (logic) = maintenance burden
   - Option A: Keep dual format (more flexible)
   - Option B: Migrate to single format (YAML + embedded logic blocks?)
   - Option C: Python-only with decorators for metadata

3. **Enhance Rule Extensibility**
   - Plugin architecture for custom rules
   - External rule repositories (ASTRA updates?)
   - Dynamic rule loading without code changes

### Implementation Recommendations

1. **Preserve Critical Business Logic**
   - CON-01 duplicate detection (exact algorithm)
   - ESS-02 ontological disambiguation (4-category logic)
   - Weighted scoring + quality scaling (calibrated values)
   - Soft acceptance floor (0.65 with no blocking errors)

2. **Improve Performance**
   - Pattern compilation caching (✓ already implemented)
   - Consider parallel rule evaluation (with dependency graph)
   - Incremental validation (only re-validate changed aspects)

3. **Enhance Testing**
   - Golden test suite (known good/bad examples)
   - Regression tests for each rule
   - Integration tests for orchestration flow
   - Performance benchmarks

### Documentation Recommendations

1. **Rule Documentation**
   - Each rule needs: WHY (business purpose) + WHAT (validation logic) + HOW (implementation)
   - Examples: good vs. bad
   - User-facing explanations (for UI help text)

2. **Architecture Documentation**
   - Flow diagrams (orchestration, evaluation, scoring)
   - Dependency graphs (rules, services, data)
   - Decision logs (why soft floor? why these thresholds?)

3. **Maintenance Guide**
   - How to add a new rule
   - How to modify existing rule
   - How to tune weights and thresholds
   - How to test rule changes

---

## Next Steps (Post-Extraction)

### For Rebuild Agent
1. Use this extraction as source of truth
2. Design new validation architecture preserving critical logic
3. Create migration plan (if changing architecture)
4. Implement with test-first approach
5. Validate against golden test suite

### For Documentation Agent
1. Generate user-facing rule documentation
2. Create UI help text from rule explanations
3. Document business decisions (soft floor, thresholds, weights)
4. Maintain architectural decision records (ADRs)

### For Testing Agent
1. Create comprehensive rule test suite
2. Develop golden test cases (per rule)
3. Build integration test harness
4. Establish performance benchmarks

---

## Files Created

1. **`VALIDATION-EXTRACTION.md`** - Complete business logic extraction (25,000+ words)
2. **`EXTRACTION_SUMMARY.md`** - This summary document

**Location:** `/Users/chrislehnen/Projecten/Definitie-app/rebuild/business-logic-extraction/03-validation-rules/`

---

## Extraction Metadata

- **Agent:** Claude Code (Sonnet 4.5)
- **Task:** AGENT 3 - Validation Rules (45+) Extraction
- **Date:** 2025-10-02
- **Files Analyzed:** 100+ files (JSON, Python, services)
- **Total Lines Analyzed:** ~10,000 lines of code
- **Output Size:** 25,000+ words of documentation
- **Extraction Time:** ~30 minutes
- **Completeness:** 100% (all 53 rules documented)

---

**END OF EXTRACTION SUMMARY**
