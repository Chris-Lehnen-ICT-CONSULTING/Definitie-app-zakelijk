# Validation Rules Quick Reference

**For Rebuild Developers:** Fast lookup of critical business logic

---

## Critical Rules (Must Preserve Exactly)

### CON-01: Context + Duplicate Detection
```python
# Context must be implicit, not explicit
# Forbidden: "binnen DJI", "in strafrechtelijke context", "volgens OM"
# Allowed: Context shapes meaning, not mentioned in text

# Duplicate Detection Formula:
match = (
    same_begrip AND
    same_organisatorische_context AND
    same_juridische_context AND
    same_wettelijke_basis (order-independent)
)

# Normalization:
def normalize_context_list(lst):
    return sorted({x.strip().lower() for x in lst})
```

**Why:** Legal definitions must be context-specific but reusable. Duplicate detection prevents data corruption.

---

### ESS-02: Ontological Category Disambiguation
```python
# 4 categories (exactly one must be detected):
categories = {
    "type": ["categorie", "soort", "klasse"],
    "particulier": ["exemplaar", "specifiek exemplaar"],
    "proces": ["proces", "activiteit", "handeling", "gebeurtenis"],
    "resultaat": ["resultaat van", "uitkomst", "effect", "product"]
}

# Logic:
hits = count_category_matches(text)
if len(hits) == 1: PASS
elif len(hits) > 1: FAIL "Ambiguous"
else: FAIL "Missing ontological marker"
```

**Why:** Many terms are polysemous (e.g., "registratie" = process OR result). Must disambiguate.

---

### Weighted Scoring Formula
```python
# Step 1: Calculate raw weighted score
overall = sum(rule_score * weight) / sum(weight)

# Step 2: Apply quality band scaling (length-based)
if word_count < 12: scale = 0.75
elif word_count < 20: scale = 0.9
elif word_count > 100: scale = 0.85
elif word_count > 60: scale = 0.9
else: scale = 1.0

overall = round(overall * scale, 2)

# Step 3: Calculate category scores
detailed = {
    "taal": avg([ARAI/VER scores]),
    "juridisch": avg([ESS/VAL scores]),
    "structuur": avg([STR/INT scores]),
    "samenhang": avg([CON/SAM scores])
}
```

**Why:** Calibrated to legal definition quality standards. Scale factors align with "golden bands."

---

### Acceptance Gates (EPIC-016)
```python
# Hard gates:
gate1 = (critical_violations == 0)
gate2 = (overall >= 0.75)
gate3 = all(category_score >= 0.70 for category in detailed)

acceptance_gate = gate1 AND gate2 AND gate3

# Soft acceptance floor (business policy):
blocking_errors = ["VAL-EMP", "CON-CIRC", "VAL-LEN-002", "LANG-*", "STR-FORM-001"]
soft_ok = (overall >= 0.65) AND (no errors in blocking_errors)

is_acceptable = acceptance_gate OR soft_ok
```

**Why:** Balances quality standards with usability. Soft floor prevents overly strict rejection.

---

## Rule Priority Matrix

| Rule | Priority | Weight | Scoring | Critical for |
|------|----------|--------|---------|--------------|
| CON-01 | High | 1.0 | Excluded (0.0) | Context management |
| CON-02 | High | 1.0 | Included | Legal validity |
| ESS-02 | High | 1.0 | Included | Polysemy resolution |
| ARAI-06 | High | 1.0 | Excluded (0.0) | Structure integrity |
| DUP-01 | High | 1.0 | N/A (pre-check) | Data quality |
| VAL-EMP-001 | High | 1.0 | Excluded (0.0) | Baseline safeguard |
| VAL-LEN-001 | High | 0.9 | Excluded (0.0) | Baseline safeguard |
| INT-01 | Medium | 0.7 | Included | Readability |
| SAM-02 | High | 1.0 | Included | Qualified terms |

**Note:** Rules with weight=0.0 are safeguards, not quality metrics. They block but don't score.

---

## Rule Evaluation Order (Deterministic)

```python
# ALWAYS evaluate in sorted order:
sorted_rules = sorted([
    "ARAI-01", "ARAI-02", "ARAI-02SUB1", "ARAI-02SUB2", "ARAI-03",
    "ARAI-04", "ARAI-04SUB1", "ARAI-05", "ARAI-06",
    "CON-01", "CON-02", "CON-CIRC-001",
    "DUP-01",
    "ESS-01", "ESS-02", "ESS-03", "ESS-04", "ESS-05", "ESS-CONT-001",
    "INT-01", "INT-02", "INT-03", "INT-04", "INT-06", "INT-07", "INT-08", "INT-09", "INT-10",
    "SAM-01", "SAM-02", "SAM-03", "SAM-04", "SAM-05", "SAM-06", "SAM-07", "SAM-08",
    "STR-01", "STR-02", "STR-03", "STR-04", "STR-05", "STR-06", "STR-07", "STR-08", "STR-09", "STR-ORG-001", "STR-TERM-001",
    "VAL-EMP-001", "VAL-LEN-001", "VAL-LEN-002",
    "VER-01", "VER-02", "VER-03"
])

for rule_id in sorted_rules:
    score, violation = evaluate_rule(rule_id, context)
```

**Why:** Reproducibility for testing and debugging.

---

## Special-Case Rules (Custom Logic)

### ESS-02: Ontological Category
- **Special:** Pattern matching per category with cache
- **Cache:** `_compiled_ess02_cache` for performance
- **Logic:** Count hits per category, ambiguity if >1

### SAM-02: Qualified Terms
- **Special:** Extracts head term (last word of multi-word begrip)
- **Check 1:** Definition must NOT start with "head:"
- **Check 2:** Must NOT contain base definition phrases
- **Example:** "strafbaar delict" → "delict waarvoor..." (NOT "delict: ...")

### SAM-04: Compound Terms
- **Special:** For one-word compounds (e.g., "procesmodel")
- **Logic:** First word in definition must be substring of begrip
- **Example:** "procesmodel: model..." ✓ NOT "procesmodel: proces..." ✗

### VER-03: Verb-Term Infinitive
- **Special:** For verb terms (werkwoorden)
- **Check:** Must NOT end with `-t` or `-d` (conjugated)
- **Pattern:** `r".+[td]$"` → likely conjugated
- **Example:** "beoordelen" ✓ NOT "beoordeelt" ✗

### CON-01: Duplicate Detection
- **Special:** Database query for exact context match
- **Query:** `count_exact_by_context(begrip, org, jur, wet)`
- **Normalization:** Context lists normalized before comparison

---

## Pattern Compilation & Caching

```python
# Per-rule pattern cache
_compiled_json_cache: dict[str, list[re.Pattern]] = {}

# ESS-02 category cache (special)
_compiled_ess02_cache: dict[str, dict[str, list[re.Pattern]]] = {}

# Compile once on first evaluation:
if rule_id not in _compiled_json_cache:
    _compiled_json_cache[rule_id] = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in rule["herkenbaar_patronen"]
    ]

# Reuse compiled patterns:
compiled_patterns = _compiled_json_cache[rule_id]
```

**Why:** Regex compilation is expensive. Cache for 50x+ performance boost.

---

## Violation Structure (Standard Format)

```python
violation = {
    "code": "RULE-ID",                      # e.g., "CON-01"
    "severity": "error" | "warning",        # error=blocking, warning=advisory
    "severity_level": "critical" | "high" | "medium" | "low",
    "message": "User-friendly NL text",     # Dutch language
    "description": "Same as message",       # For consistency
    "rule_id": "RULE-ID",                   # Same as code
    "category": "taal" | "juridisch" | "structuur" | "samenhang",
    "suggestion": "Actionable fix (NL)",    # How to resolve
    "metadata": {                           # Optional
        "detected_pattern": "regex",
        "position": 42,
        "existing_definition_id": 123
    }
}
```

---

## Category Mapping (Rule Prefix → Category)

```python
def _category_for(code: str) -> str:
    if code.startswith("STR-"): return "structuur"
    if code.startswith("CON-"): return "samenhang"
    if code.startswith(("ESS-", "VAL-")): return "juridisch"
    if code.startswith("SAM-"): return "samenhang"
    if code.startswith(("ARAI", "ARAI-")): return "taal"
    if code.startswith("INT-"): return "structuur"
    if code.startswith("VER-"): return "taal"
    return "system"
```

---

## Weight Assignment Logic

```python
def _calculate_rule_weight(rule_data: dict) -> float:
    # Explicit weight (if provided)
    if "weight" in rule_data and rule_data["weight"] is not None:
        return float(rule_data["weight"])

    # Priority-based weight
    priority = rule_data.get("prioriteit", "midden")
    priority_weights = {
        "hoog": 1.0,
        "midden": 0.7,
        "laag": 0.4
    }
    return priority_weights.get(priority, 0.4)
```

**Note:** After calculation, baseline internal + ARAI family weights set to 0.0 (excluded from scoring).

---

## Soft Acceptance Floor Logic

```python
def _has_blocking_errors(violations: list) -> bool:
    for v in violations:
        if v["severity"] != "error":
            continue
        code = v["code"]
        if code.startswith(("VAL-EMP", "CON-CIRC", "VAL-LEN-002", "LANG-", "STR-FORM-001")):
            return True
    return False

soft_ok = (overall_score >= 0.65) and (not _has_blocking_errors(violations))
is_acceptable = acceptance_gate["acceptable"] or soft_ok
```

**Why:** Business decision to allow "acceptable minimal" quality (0.60-0.75 range) if no critical errors.

---

## Baseline Internal Rules (Always Evaluated)

```python
_baseline_internal = [
    "VAL-EMP-001",    # Empty text check
    "VAL-LEN-001",    # Minimum length (5 words, 15 chars)
    "VAL-LEN-002",    # Maximum length (80 words, 600 chars)
    "ESS-CONT-001",   # Essential content present (6+ words)
    "CON-CIRC-001",   # No circular definition
    "STR-TERM-001",   # Consistent terminology (hyphenation)
    "STR-ORG-001"     # Sentence structure and redundancy
]
```

**Why:** These are safeguards that MUST always run, even if ToetsregelManager unavailable.

---

## JSON Rule Definition Schema

```json
{
    "id": "RULE-ID",
    "naam": "Short rule name (NL)",
    "uitleg": "Explanation (NL)",
    "toelichting": "Extended explanation (NL)",
    "toetsvraag": "Test question (NL)",
    "herkenbaar_patronen": ["regex1", "regex2"],
    "goede_voorbeelden": ["good example 1"],
    "foute_voorbeelden": ["bad example 1"],
    "prioriteit": "hoog" | "midden" | "laag",
    "aanbeveling": "verplicht" | "aanbevolen" | "optioneel",
    "geldigheid": "alle" | "specific scope",
    "status": "definitief" | "conceptueel",
    "type": "rule type",
    "thema": "theme",
    "brondocument": "ASTRA | other source",
    "relatie": [
        {
            "fulltext": "Related rule name",
            "fullurl": "https://astraonline.nl/..."
        }
    ]
}
```

---

## Performance Benchmarks (Target)

- **Single definition validation:** < 100ms
- **Batch validation (10 definitions):** < 1 second (sequential)
- **Pattern compilation (53 rules):** < 50ms (one-time, cached)
- **Database duplicate check:** < 200ms
- **Full validation + scoring + gates:** < 150ms

**Current bottlenecks:**
1. Database queries (duplicate detection) - optimize with indexing
2. Regex pattern matching (large text) - pre-filter before heavy patterns

---

## Testing Strategy

### Unit Tests (Per Rule)
```python
def test_con01_explicit_context():
    # Given: Definition with explicit context
    text = "proces binnen DJI voor behandeling van zaken"
    context = {"organisatorische_context": ["DJI"]}

    # When: Validate
    result = validator.validate(text, "proces", context)

    # Then: Should fail
    assert result["is_acceptable"] == False
    assert any(v["code"] == "CON-01" for v in result["violations"])
```

### Integration Tests (Full Flow)
```python
async def test_validation_orchestrator_flow():
    # Given: Complete definition input
    begrip = "sanctie"
    text = "maatregel die volgt op normovertreding"
    context = {...}

    # When: Validate via orchestrator
    result = await orchestrator.validate_definition(begrip, text, context)

    # Then: Should have all expected fields
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "acceptance_gate" in result
```

### Golden Tests (Known Examples)
```python
GOLDEN_EXAMPLES = [
    {
        "begrip": "sanctie",
        "text": "maatregel die volgt op normovertreding conform het Wetboek van Strafrecht",
        "expected_score": 0.85,
        "expected_acceptable": True,
        "expected_violations": []
    },
    # ... more examples
]
```

---

## Integration Dependencies

### Required Services
1. **ToetsregelManager** - loads JSON rule definitions
2. **DefinitieRepository** - duplicate detection, context matching
3. **CleaningService** (optional) - text normalization
4. **Config** (optional) - thresholds, weights overrides

### Dependency Injection Pattern
```python
class ModularValidationService:
    def __init__(
        self,
        toetsregel_manager: ToetsregelManager | None = None,
        cleaning_service: CleaningService | None = None,
        config: Config | None = None,
        repository: DefinitieRepository | None = None
    ):
        self.toetsregel_manager = toetsregel_manager
        self.cleaning_service = cleaning_service
        self.config = config
        self._repository = repository

        # Load rules if manager available
        if self.toetsregel_manager:
            self._load_rules_from_manager()
        else:
            self._set_default_rules()  # Fallback to baseline
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Forgetting Context Normalization
```python
# WRONG:
if context in existing_contexts:
    return "duplicate"

# RIGHT:
def normalize(lst):
    return sorted({x.strip().lower() for x in lst})

if normalize(context) == normalize(existing_context):
    return "duplicate"
```

### Pitfall 2: Not Excluding Baseline Rules from Scoring
```python
# WRONG:
overall_score = sum(all_rule_scores * weights) / sum(weights)

# RIGHT:
for code in baseline_internal + ARAI_family:
    weights[code] = 0.0  # Exclude from scoring

overall_score = sum(rule_scores * weights) / sum(weights)
```

### Pitfall 3: Ignoring Quality Band Scaling
```python
# WRONG:
return overall_score  # Raw score

# RIGHT:
scale = calculate_quality_band_scale(word_count)
return round(overall_score * scale, 2)
```

### Pitfall 4: Hard-Coding Thresholds
```python
# WRONG:
if score >= 0.75:
    acceptable = True

# RIGHT:
threshold = config.thresholds.overall_accept  # Default: 0.75
if score >= threshold:
    acceptable = True
```

---

## Migration Checklist (For Rebuild)

- [ ] Preserve CON-01 duplicate detection logic (exact algorithm)
- [ ] Preserve ESS-02 ontological disambiguation (4-category logic)
- [ ] Preserve weighted scoring formula + quality band scaling
- [ ] Preserve soft acceptance floor (0.65 + no blocking errors)
- [ ] Preserve pattern compilation caching
- [ ] Preserve deterministic evaluation order (sorted)
- [ ] Preserve context normalization (sorted, lowercased, stripped)
- [ ] Preserve weight exclusion (baseline internal + ARAI family)
- [ ] Preserve category score calculation (prefix-based)
- [ ] Preserve violation structure (standard format)
- [ ] Test against golden examples (known good/bad)
- [ ] Benchmark performance (< 150ms full validation)

---

## Quick Command Reference

```bash
# Run all validation tests
pytest tests/services/test_definition_validator.py -v

# Run specific rule test
pytest tests/services/test_definition_validator.py::test_con01_explicit_context

# Generate validation status report
make validation-status

# Benchmark validation performance
pytest tests/performance/test_validation_speed.py --benchmark

# Validate single definition (CLI)
python scripts/validate_definition.py --begrip "sanctie" --text "maatregel..."
```

---

**END OF QUICK REFERENCE**

*For complete details, see VALIDATION-EXTRACTION.md*
