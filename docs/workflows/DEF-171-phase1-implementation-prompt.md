# DEF-171 Phase 1 Implementation Prompt

**Branch:** DEF-171-prompt-optimization-v3
**Status:** Analysis complete, implementation needed
**Estimated effort:** 2-3 hours
**Risk:** Low (conservative changes only)

---

## Context

Phase 1 analyse is compleet en gecommit. De analyse identificeerde 3 categorieën content die verwijderd kunnen worden uit de modulaire prompt code voor een geschatte 19.8% token reductie (~1,650 tokens).

**BELANGRIJK:** Een vorige poging heeft per ongeluk een export file aangepast (`/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24.txt`). Dat is NIET de bedoeling. De echte implementatie moet gebeuren in de modulaire prompt code in `src/services/prompts/modules/`.

---

## Reference Files

### Analysis Documentation
- **Implementation summary:** `docs/workflows/DEF-171-phase1-implementation-summary.md`
- **Full analysis:** `docs/workflows/prompt-analysis-DEF-171-v3-summary.md`
- **Action checklist:** `docs/workflows/DEF-171-action-checklist.md`
- **Root cause analysis:** `docs/workflows/DEF-171-root-cause-analysis.md`

### Reference Export (DO NOT MODIFY!)
- **Current prompt export:** `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24.txt`
- **Purpose:** Referentie om te zien wat de huidige output is
- **Use case:** Vergelijken before/after, identificeren wat waar zit

### Modular Prompt Architecture
```
src/services/prompts/modules/
├── prompt_orchestrator.py       # Orchestrates all modules
├── metrics_module.py            # ⚠️  MODIFY: Remove quality metrics
├── semantic_categorisation_module.py  # ⚠️  MODIFY: Remove ontology determination
├── json_based_rules_module.py   # ⚠️  CHECK: Toetsvraag patterns
├── error_prevention_module.py   # ⚠️  CHECK: Toetsvraag patterns
├── structure_rules_module.py    # ⚠️  CHECK: Toetsvraag patterns
├── integrity_rules_module.py    # ⚠️  CHECK: Toetsvraag patterns
└── [other modules]              # No changes needed
```

---

## Phase 1 Implementation Tasks

### Task 1: Remove Quality Metrics Section (27 lines estimated)

**Target module:** `src/services/prompts/modules/metrics_module.py`

**What to remove:**
- Quality metrics zoals karakterlimieten, minimum/maximum lengtes
- Complexity checks
- Quality measurement criteria

**What to KEEP:**
- Instructies die de GENERATIE sturen (niet output metrics)
- Examples die laten zien HOE te schrijven
- Style guidance

**Rationale:** Output metrics guide post-generation validation, not generation itself. ValidationOrchestratorV2 handles this.

**Steps:**
1. Read `metrics_module.py` volledig
2. Identify quality metrics section (kijk naar export reference voor exacte tekst)
3. Remove metrics, keep generation guidance
4. Test: Generate 1 definitie, check quality niet gedaald
5. Commit: "feat(DEF-171): remove quality metrics from MetricsModule (Phase 1.1)"

---

### Task 2: Remove Ontology Determination Logic (37 lines estimated)

**Target module:** `src/services/prompts/modules/semantic_categorisation_module.py`

**What to remove:**
- "Bepaal de juiste categorie..." instructies
- Logic die het LLM vraagt om PROCES vs TYPE vs EIGENSCHAP te kiezen
- Decision trees voor category selection

**What to KEEP:**
- Kick-off patterns PER categorie (nuttig zodra categorie bekend is):
  - PROCES: "activiteit waarbij..."
  - TYPE: "[kernwoord] dat/die [kenmerk]"
  - EIGENSCHAP: "kenmerk waarbij..."
  - HOEDANIGHEID: "toestand waarbij..."

**Rationale:** UI provides category via dropdown (see DEF-126 commits). LLM doesn't need to determine it.

**Steps:**
1. Read `semantic_categorisation_module.py` volledig
2. Identify category determination logic
3. Remove determination, preserve kick-off patterns
4. Verify module receives category from context/config
5. Test: Generate 1 definitie per category (4 total), check kick-offs correct
6. Commit: "feat(DEF-171): remove ontology determination from SemanticCategorisationModule (Phase 1.2)"

---

### Task 3: Remove Toetsvraag Validation Patterns (39 lines estimated)

**Target modules:** Check ALL rule modules:
- `json_based_rules_module.py`
- `error_prevention_module.py`
- `structure_rules_module.py`
- `integrity_rules_module.py`

**What to remove:**
- ALL "Toetsvraag:" patterns (39 occurrences in export)
- Example: "- Toetsvraag: Is de definitie circulair?"
- Example: "- Toetsvraag: Bevat de definitie metaforen?"

**What to KEEP:**
- ALL "Instructie:" or "**Instructie:**" patterns (10 occurrences in export)
- Example: "- **Instructie:** Gebruik concrete, verifieerbare termen"
- Example: "- **Instructie:** Vermijd circulaire definities"

**Rationale:**
- "Toetsvraag:" = post-generation validation → handled by ValidationOrchestratorV2
- "Instructie:" = generation guidance → still needed

**Steps:**
1. Grep all modules: `grep -n "Toetsvraag:" src/services/prompts/modules/*.py`
2. For each occurrence:
   a. Check if it's validation (remove) or generation guidance (keep)
   b. Remove if validation
3. Verify: `grep -n "Instructie:" src/services/prompts/modules/*.py` → should have ~10 results
4. Test: Generate 3 definities, check geen kwaliteitsverlies
5. Commit: "feat(DEF-171): remove Toetsvraag validation patterns from rule modules (Phase 1.3)"

---

## Validation Protocol

After ALL changes:

### Step 1: Generate Test Definitions (3 required)
```bash
# Start applicatie
bash scripts/run_app.sh

# Genereer 3 definities handmatig via UI:
# 1. PROCES: "aanbesteding"
# 2. TYPE: "vergunning"
# 3. EIGENSCHAP: "rechtsgeldigheid"

# Save outputs to: docs/workflows/DEF-171-test-outputs/
```

### Step 2: Quality Comparison
Compare tegen baseline (previous good definitions):
- ✅ Kick-off patterns correct per category
- ✅ No circular definitions
- ✅ No forbidden patterns
- ✅ Proper structure (opbouw, kenmerken, grenzen, etc.)
- ✅ No quality degradation

### Step 3: Token Measurement
```bash
# Generate full prompt export via applicatie
# Save to: /Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24-OPTIMIZED.txt

# Count tokens (manual if tiktoken unavailable):
wc -m /Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24-OPTIMIZED.txt
# Divide by 4 for estimate

# Expected: ~6,679 tokens (was ~8,329)
# Target reduction: 19.8%
```

### Step 4: Smoke Tests
```bash
pytest -m smoke --tb=short
# All tests should pass
```

---

## Implementation Strategy

### Approach: Conservative & Iterative
1. **One task at a time:** Complete Task 1, test, commit. Then Task 2, etc.
2. **Read before edit:** Always read full module before making changes
3. **Use reference export:** Compare against `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24.txt` to find exact text
4. **Test after each change:** Generate 1 definitie to verify no breakage
5. **Commit granularly:** One commit per task (3 commits total)

### DO NOT:
- ❌ Modify export files in `/Users/chrislehnen/Downloads/`
- ❌ Make changes to multiple modules in one commit
- ❌ Remove "Instructie:" patterns (only "Toetsvraag:")
- ❌ Remove kick-off patterns (keep them!)
- ❌ Batch all changes without testing in between

### DO:
- ✅ Modify only modules in `src/services/prompts/modules/`
- ✅ Test after each module change
- ✅ Preserve all generation guidance
- ✅ Remove only validation content
- ✅ Use export as reference, not as target

---

## Success Criteria

### Required:
- [ ] MetricsModule: Quality metrics removed
- [ ] SemanticCategorisationModule: Ontology determination removed, kick-offs kept
- [ ] Rule modules: All 39 "Toetsvraag:" patterns removed, 10 "Instructie:" kept
- [ ] 3 test definitions generated with good quality
- [ ] Token reduction measured: ~19.8% achieved
- [ ] Smoke tests passing
- [ ] 3 granular commits created

### Optional:
- [ ] Before/after comparison documented
- [ ] Linear DEF-171 updated with completion status

---

## Expected Timeline

- **Task 1 (Metrics):** 30-45 min (read, edit, test, commit)
- **Task 2 (Ontology):** 45-60 min (read, edit, verify context flow, test, commit)
- **Task 3 (Toetsvragen):** 45-60 min (grep all modules, edit, test, commit)
- **Validation:** 30-45 min (generate 3 defs, compare, measure tokens)

**Total:** 2.5-3.5 hours

---

## Rollback Plan

If kwaliteit daalt of tests falen:

```bash
# Rollback laatste commit
git reset --soft HEAD~1

# Or rollback all Phase 1 changes
git reset --soft <commit-before-phase1>

# Restore files
git restore src/services/prompts/modules/
```

---

## Next Session Checklist

1. [ ] Checkout branch: `git checkout DEF-171-prompt-optimization-v3`
2. [ ] Read this prompt volledig
3. [ ] Read reference export: `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-24.txt`
4. [ ] Read implementation summary: `docs/workflows/DEF-171-phase1-implementation-summary.md`
5. [ ] Start with Task 1 (MetricsModule)
6. [ ] Follow Conservative & Iterative approach
7. [ ] Test after EVERY change
8. [ ] Create 3 granular commits

---

**Questions? Check:**
- Analysis: `docs/workflows/prompt-analysis-DEF-171-v3-summary.md`
- Root cause: `docs/workflows/DEF-171-root-cause-analysis.md`
- Architecture: `CLAUDE.md` §Streamlit UI Patterns, §Architecture

**Good luck! 🚀**
