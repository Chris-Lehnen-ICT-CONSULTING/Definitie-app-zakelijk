---
id: EPIC-026-EXTRACTION-QUICK-REFERENCE
epic: EPIC-026
phase: 1
created: 2025-10-02
type: quick-reference-card
---

# Business Logic Extraction - Quick Reference Card

**Print this and keep it at your desk during extraction!**

---

## 🎯 Your Mission

**Extract ALL business logic from 83,319 LOC codebase before rebuild**

**Zero knowledge loss = Success**

---

## 📋 Daily Checklist

```
Morning:
□ What am I extracting today? (check timeline)
□ Do I have the right template? (see Templates below)
□ Do I have test data ready? (42 baseline definitions)

During extraction:
□ Document WHAT the logic does (business purpose)
□ Document WHY it exists (rationale)
□ Document HOW it works (algorithm)
□ Extract ALL hardcoded values (patterns, thresholds, magic numbers)
□ Note ANY ambiguities (ask domain expert)

End of day:
□ Test extracted logic against baseline (42 definitions)
□ Commit documentation with clear message
□ Update progress tracker
□ Note blockers for tomorrow
```

---

## 📍 Critical Hotspots (Where to Look)

### 🔥 Top 5 God Objects
1. **definition_generator_tab.py** - 2,525 LOC, 60 methods
   - Rule reasoning logic (L1771-1835)
   - Regeneration workflows (L2008-2438)
   - Validation rendering (L1527-1697)

2. **tabbed_interface.py** - 1,793 LOC, 39 methods
   - Ontological categorization (L272-419) ← HARDCODED 3x!
   - Generation orchestration (L821-1201) ← 380 LOC god method!
   - Document processing (L1207-1497)

3. **definitie_repository.py** - 1,815 LOC, 41 methods
   - Duplicate detection (L192-305) ← 70% threshold
   - Voorbeelden persistence (L254-464)
   - Status transitions

4. **definition_orchestrator_v2.py** - 984 LOC
   - Full generation orchestration
   - Service coordination

5. **validation_orchestrator_v2.py** - Unknown LOC
   - 46 rules orchestration
   - Approval gate policy

### 🎯 Hardcoded Pattern Locations
```bash
# Find ALL hardcoded logic
grep -r "HARDCODED\|TODO\|FIXME\|pattern\|threshold" src/

# Ontological patterns (CRITICAL!)
src/ui/tabbed_interface.py:354-418  # DUPLICATED 3x!

# Validation thresholds
src/toetsregels/regels/ARAI-01.py  # 50-500 chars
src/ui/components/definition_generator_tab.py:223-228  # 0.8/0.5 confidence
src/database/definitie_repository.py:192  # 70% similarity

# Rule reasoning
src/ui/components/definition_generator_tab.py:1771-1835  # 7 rules DUPLICATED!
```

---

## 🗂️ Templates (Copy These!)

### Validation Rule Template
```markdown
# Validation Rule: {RULE-ID}

## Metadata
- ID: {RULE-ID}
- Category: ARAI|CON|ESS|INT|SAM|STR|VER
- Priority: high|medium|low

## Business Purpose
- What: {what does it check}
- Why: {why important}
- When: {when applied}

## Implementation
- Algorithm: {pseudocode}
- Thresholds: {values + rationale}
- Patterns: {regex patterns}

## Examples
- Good: {examples that pass}
- Bad: {examples that fail}

## Tests
- Test 1: {input} → {output}
```

### Workflow Template
```markdown
# Workflow: {Name}

## Steps
1. Step 1: {action} → {result}
2. Step 2: {action} → {result}

## Business Rules
- Rule 1: {description}

## Diagram
[Mermaid sequence diagram]

## Tests
- Happy path: {scenario}
- Error path: {scenario}
```

---

## 🧪 Testing Commands

### Export Baseline
```bash
# Export 42 definitions
python -c "
from database.definitie_repository import get_definitie_repository
import json

repo = get_definitie_repository()
defs = repo.search_definities(query='', limit=100)

with open('baseline_42.json', 'w') as f:
    json.dump([d.to_dict() for d in defs], f, indent=2, ensure_ascii=False)
"
```

### Test Validation Rules
```bash
# Test all 46 rules against baseline
pytest tests/business-logic/test_validation_rules_baseline.py -v

# Test specific rule
pytest tests/business-logic/test_validation_rules_baseline.py::test_ARAI_01
```

### Find Hardcoded Values
```bash
# All hardcoded patterns
rg "0\.[0-9]+|[0-9]+\s*(chars|seconds|minutes)" src/

# Magic numbers
rg "\b(50|500|0\.8|0\.5|0\.7|70)\b" src/ --type py

# Pattern definitions
rg "patterns\s*=\s*\{|pattern_list|herkenbaar_patronen" src/
```

---

## 📊 Progress Tracking

### Week 1 Goals
- [ ] Day 1-2: 46 validation rules documented
- [ ] Day 3: Baseline tests passing
- [ ] Day 4: Ontological patterns extracted
- [ ] Day 5: Generation workflow documented

### Week 2 Goals
- [ ] Day 6-7: Duplicate detection algorithm
- [ ] Day 8-9: Regeneration state machine
- [ ] Day 10: Voorbeelden transaction logic

### Week 3 Goals
- [ ] Day 11-12: UI hardcoded logic
- [ ] Day 13: Workflow status management
- [ ] Day 14-15: Prompt building
- [ ] Day 16: Final validation

---

## 🚨 When to Escalate

**Escalate immediately if:**
1. ❌ Logic is ambiguous - can't determine exact behavior
2. ❌ Baseline test fails - extracted logic doesn't match OLD system
3. ❌ Missing domain knowledge - don't understand Dutch legal terminology
4. ❌ Time overrun - task taking 2x expected time
5. ❌ Conflicting logic - found duplicated/inconsistent rules

**How to escalate:**
1. Document the issue clearly
2. Show specific code location
3. Show what you tried
4. Ask specific question
5. Tag domain expert or project lead

---

## 🎓 Extraction Tips

### DO's ✅
- ✅ Document EVERY threshold value (even "obvious" ones)
- ✅ Test extracted logic against baseline IMMEDIATELY
- ✅ Note ANY assumptions you make
- ✅ Extract patterns to config files (not hardcoded)
- ✅ Create diagrams for complex workflows
- ✅ Cross-reference related logic (e.g., rule in validator + UI)

### DON'Ts ❌
- ❌ Skip "trivial" logic - extract EVERYTHING
- ❌ Assume business rules - verify with tests
- ❌ Leave ambiguities undocumented
- ❌ Forget to commit daily
- ❌ Work in isolation - ask questions!
- ❌ Trust memory - write it down!

---

## 🔍 Common Extraction Patterns

### Pattern 1: Hardcoded Threshold
```python
# OLD (in code)
if len(definitie) > 500:
    return "Too long"

# NEW (extract to config)
# config/validation_thresholds.yaml
ARAI-01:
  max_length: 500
  rationale: "Readability limit per ASTRA guidelines"
```

### Pattern 2: Duplicated Logic
```python
# FOUND: Same patterns in 3 files!
# tabbed_interface.py L354
# tabbed_interface.py L408
# Quick analyzer L42

# ACTION: Extract to single config
# config/ontological_patterns.yaml
categories:
  proces:
    patterns: ["atie", "eren", "ing"]
```

### Pattern 3: Implicit Business Rule
```python
# OLD (implicit)
if confidence > 0.8:
    color = "green"

# NEW (explicit)
# Document in business_rules_catalog.csv:
# BR-042,UI,Confidence,High confidence threshold,>0.8,User experience,Green color
```

---

## 📞 Who to Ask

| Question Type | Ask |
|--------------|-----|
| **Dutch legal terminology** | Domain expert / original developer |
| **ASTRA compliance** | Legal consultant / ASTRA documentation |
| **Validation rules** | Check ASTRA links in rule JSON |
| **Technical ambiguity** | Code architect / senior developer |
| **Timeline concerns** | Project manager |
| **Test failures** | QA / test engineer |

---

## 🏆 Success Metrics

**Daily:**
- Documents created: {target per day}
- Baseline tests passing: {percentage}
- Config files updated: {count}

**Weekly:**
- Week 1: 46 rules + categorization + orchestration ✅
- Week 2: Duplicate + regeneration + voorbeelden ✅
- Week 3: UI logic + workflow + prompt + validation ✅

**Final:**
- 100% of MUST items extracted ✅
- 90%+ of SHOULD items extracted ✅
- 42 baseline - 100% validation match ✅
- 42 baseline - 100% category match ✅
- Completeness checklist 100% ✅

---

## 🛠️ Useful Commands

### Count LOC
```bash
wc -l src/ui/components/definition_generator_tab.py
wc -l src/ui/tabbed_interface.py
```

### Find God Methods
```bash
# Methods > 100 LOC
rg "^\s*def " src/ -A 100 | grep -B 1 "^\s*def "
```

### Extract Rule IDs
```bash
# List all validation rules
ls src/toetsregels/regels/*.json | sed 's/.*\///' | sed 's/\.json//'
```

### Search for Patterns
```bash
# Find all pattern definitions
rg "pattern|PATTERN|herkenbaar_patronen" src/toetsregels/
```

---

## 📚 Required Reading

**Before starting:**
1. `BUSINESS_LOGIC_EXTRACTION_PLAN.md` (full 33-page plan)
2. `EXTRACTION_PLAN_SUMMARY.md` (executive summary)
3. Current responsibility maps:
   - `definition_generator_tab_responsibility_map.md`
   - `tabbed_interface_responsibility_map.md`
   - `definitie_repository_responsibility_map.md`

**Daily reference:**
- This quick reference card
- Relevant template (validation/workflow/algorithm)
- Baseline test results

---

## 🎯 Remember

**The rebuild team depends on YOUR extraction quality!**

**If you don't extract it, we lose it forever.**

**When in doubt:**
1. Extract it anyway (better too much than too little)
2. Document the ambiguity
3. Test against baseline
4. Ask for help

**Your mantra:**
> "Zero knowledge loss. Document everything. Test everything. Extract everything."

---

**Print Date:** 2025-10-02
**Version:** 1.0
**Owner:** Business Logic Extraction Team
