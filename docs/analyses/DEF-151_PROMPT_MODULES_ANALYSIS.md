# Comprehensive Analysis: 16 DefinitieAgent Prompt Modules
## Problem Identification, Contradictions & Improvement Opportunities

**Date:** 2025-11-11
**Analyst:** Debug Specialist
**Scope:** src/services/prompts/modules/*.py (16 modules)
**Focus:** Inter-module conflicts, redundancy, token waste, contradictions

---

## Executive Summary

### Overall Assessment: CRITICAL ISSUES FOUND

**Total Modules Analyzed:** 16
**Critical Issues:** 7
**High Priority Issues:** 12
**Medium Priority Issues:** 8
**Token Waste Estimated:** 1,200-1,500 tokens (15-20% of total prompt)

### Key Findings

1. **CRITICAL: Dual/Triple Instruction Conflict** - Grammar, Context, and Error Prevention modules contradict each other on what is "forbidden"
2. **CRITICAL: Redundant Rule Formatting** - ARAI/CON/ESS/STR/INT/SAM/VER modules all load rules from same cached manager and format identically
3. **CRITICAL: Missing Hard Dependencies** - TemplateModule validates input but never actually runs due to soft metadata dependency
4. **HIGH: Token Waste** - Structure Rules Module hardcodes all 9 rules (63 lines) when could be loaded from cache like other rule modules
5. **HIGH: Context Awareness Module Over-Engineering** - Contains 3 separate context formatting levels but only one is used

---

## Module-by-Module Analysis

### 1. ExpertiseModule (Lines 1-200)

**Current Function:**
- Sets expert role definition
- Determines word type (werkwoord, deverbaal, overig)
- Stores word_type in shared state for downstream modules
- Generates basic requirements and role definition

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Hard-coded word type detection | MEDIUM | Uses simple suffix-based detection; misses context-dependent cases |
| Duplicates basic requirements | MEDIUM | Content overlaps with OutputSpecification and GrammarModule |
| No validation of word type | MEDIUM | Shared state set without verification |

**Token Usage:** ~150 tokens
**Dependencies:** None (root module)

**Recommendation:** KEEP - Core baseline instruction. Refactor word type detection into separate utility if reused elsewhere.

---

### 2. OutputSpecificationModule (Lines 1-175)

**Current Function:**
- Defines output format requirements (one-line definition, no period, no haakjes, no voorbeelden)
- Sets character limit warnings
- Provides formatting guidelines

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Duplicates expertise module content | MEDIUM | "Basis schrijfregels" in expertise overlaps with format guidelines |
| Context value for "character_limit_warning" never used | MEDIUM | Sets shared state but no downstream module consumes it |
| Format guidelines conflict with Grammar module | HIGH | Both specify punctuation rules independently |

**Contradictions with Other Modules:**
- **vs. GrammarModule:** GrammarModule specifies interpunctie (komma, afkortingen in haakjes) but OutputSpec says "no haakjes"
- **vs. IntegrityModule:** INT-06 says "Definitie bevat geen toelichting" but OutputSpec might imply some contextual nuance

**Token Usage:** ~100 tokens
**Dependencies:** None

**Recommendation:** MERGE with GrammarModule. Consolidate format requirements into single location.

---

### 3. GrammarModule (Lines 1-256)

**Current Function:**
- Provides grammar rules (enkelvoud, actieve vorm, tegenwoordige tijd)
- Word-type-specific rules (werkwoord, deverbaal)
- Punctuation rules (komma, afkortingen)
- Optional strict mode with additional rules

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Partially duplicates OutputSpecification | MEDIUM | Format guidelines overlap |
| Soft dependency on word_type not declared | MEDIUM | Uses context.get_shared("word_type") but no declared dependency |
| Conflicting guidance on afkortingen | CRITICAL | Says "plaats afkortingen direct na term tussen haakjes" but OutputSpec says "no haakjes" |
| Interpunctie rules vs Integrity rules | HIGH | INT-07 specifies afkorting requirements; GrammarModule also specifies them identically |
| Strict mode rarely used | MEDIUM | Configuration option but default False; adds complexity for minimal benefit |

**Contradictions with Other Modules:**
- **vs. OutputSpecificationModule:** Haakjes for abbreviations (allowed in Grammar, forbidden in OutputSpec)
- **vs. IntegrityModule INT-07:** Both define afkorting rules identically - exact code duplication
- **vs. SemanticCategorisationModule:** Grammar-specific rules for "werkwoord" conflict with ESS-02 category-specific rules

**Token Usage:** ~140 tokens
**Dependencies:** SOFT - ExpertiseModule (word_type via shared state, not declared)

**Recommendation:** REFACTOR - Extract punctuation rules to shared static module. Declare hard dependency on ExpertiseModule. Remove duplicate afkorting rules (already in INT-07).

---

### 4. ContextAwarenessModule (Lines 1-433)

**Current Function:**
- Calculates context richness score (0.0-1.0)
- Generates adaptive context sections (rich/moderate/minimal)
- Formats sources with confidence indicators (🔴🟡🟢)
- Handles abbreviations and expanded terms
- Shares traditional context types for other modules

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Over-engineered for actual use | HIGH | Three formatting levels (rich/moderate/minimal) but no configuration to select; always uses score-based |
| Unused confidence indicator logic | MEDIUM | Builds 🔴🟡🟢 indicators but downstream modules don't consume them |
| EPIC-010 migration incomplete | HIGH | Comments say "domein is legacy" but code still attempts extraction; unclear mapping |
| Context sharing creates silent failures | MEDIUM | Sets 5 different shared state keys (organization_contexts, juridical_contexts, legal_basis_contexts) with no validation |
| Score calculation overly complex | MEDIUM | Uses multiple weighted factors but no explanation why weights chosen |
| Code duplication in formatting | MEDIUM | _format_abbreviations_detailed and _format_abbreviations_simple are nearly identical |

**Contradictions with Other Modules:**
- **vs. DefinitionTaskModule:** Both extract context from enriched_context.base_context with different key names
- **vs. ErrorPreventionModule:** Shares context via 5 keys, but ErrorPreventionModule only uses 3; inconsistent contract

**Token Usage:** ~230 tokens (largest single module)
**Dependencies:** None declared (but soft dep on base_context structure)

**Recommendation:** REFACTOR - Simplify to single formatting level (moderate is best default). Extract score calculation to separate utility. Remove unused confidence indicators. Standardize context sharing contract with ErrorPreventionModule.

---

### 5. SemanticCategorisationModule (Lines 1-280)

**Current Function:**
- Implements ESS-02 ontological category instructions
- Provides base ESS-02 guidance mandatory for all
- Adds category-specific guidance when categoria provided
- Shares ontological_category in shared state

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Redundant guidance with DefinitionTaskModule | HIGH | DefinitionTaskModule._build_checklist also includes ontological category hints - duplicates guidance |
| Extremely verbose category guidance | MEDIUM | Category-specific sections are 30-50 lines each; could be condensed 40% |
| "Detailed guidance" config option ineffective | MEDIUM | detaile_guidance defaults True; no token-saving path when disabled |
| Conflicting examples | HIGH | "TYPE" category examples start with "woord", "document", "persoon" - but Grammar module says "no lidwoord", yet these begin with naked noun which might confuse |
| Inconsistent emphasis with other modules | MEDIUM | Says "WICHTIG: De kick-off termen zijn ZELFSTANDIGE NAAMWOORDEN" but Grammar module's STR-01 already covers this |

**Contradictions with Other Modules:**
- **vs. DefinitionTaskModule:** Both encode ontological category hints (lines 189-196 in DefinitionTask duplicates SemanticCat category_guidance_map logic)
- **vs. GrammarModule:** Werkwoord examples specify "activiteit waarbij", "handeling die", "proces waarin" but GrammarModule specifies "handelingsnaamwoorden" separately
- **vs. StructureRulesModule:** STR-01 defines "start with zelfstandig naamwoord" but SemanticCat assumes GPT already knows this via kick-off terms

**Token Usage:** ~180 tokens
**Dependencies:** None declared (but assumes metadata key "ontologische_categorie")

**Recommendation:** MERGE category guidance with DefinitionTaskModule._build_checklist. Compress category guidance 40%; use bullet points instead of paragraphs. Remove duplicate "kick-off is zelfstandig naamwoord" since STR-01 covers it.

---

### 6. TemplateModule (Lines 1-251)

**Current Function:**
- Provides category-specific definition templates
- Offers word-type-specific patterns
- Generates category examples

**Problems Found:**

| Problem | Severity | CRITICAL |
|---------|----------|---------|
| CRITICAL: Broken validation logic | CRITICAL | validate_input checks for "semantic_category" metadata but no upstream module EVER SETS IT |
| Templates never loaded | CRITICAL | Module silently skipped when metadata missing (which is always) |
| Category name mismatch | CRITICAL | Uses category names "Proces", "Object", "Actor" but SemanticCat uses "proces", "type", "resultaat", "exemplaar" - different naming scheme entirely! |
| Dead code | HIGH | get_category_template and get_category_examples have 10 templates but validate_input prevents their use |
| No dependencies declared | HIGH | Depends on semantic_category metadata but no hard dependency on SemanticCategorisation |

**Contradictions with Other Modules:**
- **vs. SemanticCategorisationModule:** Different category naming systems - SemanticCat uses "proces"/"type"/"resultaat"/"exemplaar" but TemplateModule uses "Proces"/"Object"/"Actor"/"Toestand"/"Gebeurtenis"/"Maatregel"/"Informatie"/"Regel"/"Recht"/"Verplichting"
- **vs. DefinitionTaskModule:** DefinitionTask uses "soort"/"exemplaar"/"proces"/"resultaat" terminology - THIRD naming scheme!

**Token Usage:** ~120 tokens (wasted since never executes)
**Dependencies:** SOFT (metadata) - but broken

**Recommendation:** REMOVE or REFACTOR COMPLETELY - This module never runs due to validation failure. If keeping, unify category naming with SemanticCategorisation AND DefinitionTask. Or merge template examples into SemanticCat as inline examples.

---

### 7-13. Rule Modules (ARAI, CON, ESS, STR, INT, SAM, VER)

**Collective Analysis:**

**Current Function (for ARAI, CON, ESS, SAM, VER):**
- Load rules from cached manager
- Filter rules by prefix (ARAI-, CON-, ESS-, SAM-, VER-)
- Format rules identically
- Return metadata with rule count

**Current Function (STR module only):**
- HARDCODE all 9 structure rules inline (63 lines)
- Format identically to other rule modules

**Problems Found:**

| Module | Problem | Severity | Details |
|--------|---------|----------|---------|
| ARAI | Cached loading correct | LOW | No issues found |
| CON | Cached loading correct | LOW | No issues found |
| ESS | Cached loading correct | LOW | No issues found |
| STR | HARDCODED RULES | CRITICAL | Lines 78-101: Hardcodes all 9 STR rules when StructureRulesModule could use cached manager like others |
| INT | Code duplication | MEDIUM | _format_rule method identical to ARAI/CON/ESS/SAM/VER - extract to base class |
| SAM | Code duplication | MEDIUM | Same _format_rule duplication |
| VER | Code duplication | MEDIUM | Same _format_rule duplication |
| ALL | Silent cache failures | MEDIUM | No error handling if cached_manager fails or rules missing |
| ALL | Filter logic | MEDIUM | Filter using startswith() - works but fragile if rule naming changes |

**Contradictions with Other Modules:**
- **STR vs others:** StructureRulesModule hardcodes 63 lines of rules when it could load 9 rules from config (1-2 lines) like ARAI/CON/ESS/SAM/VER
- **STR vs DefinitionTaskModule:** _build_checklist duplicates STR-01 concept ("Begint met zelfstandig naamwoord") with less detail
- **Grammar vs STR:** Overlapping guidance on grammatical structure

**Token Usage (estimated):**
- ARAI: ~200 tokens (dynamic loading efficient)
- CON: ~80 tokens (few CON rules)
- ESS: ~150 tokens (good coverage)
- STR: ~250 tokens (63 hardcoded lines - **150 tokens wasted**)
- INT: ~200 tokens
- SAM: ~60 tokens
- VER: ~50 tokens
- **SUBTOTAL WASTE:** ~150 tokens in StructureRulesModule alone

**Recommendation:**
1. URGENT: Move STR rules to config file; load via cached manager like other modules (saves 150 tokens)
2. Extract identical _format_rule to BasePromptModule or shared utility function (saves ~60 tokens)
3. Add error handling for cache failures

---

### 8. ErrorPreventionModule (Lines 1-262)

**Current Function:**
- Lists basic forbidden patterns
- Provides extended forbidden starters list
- Context-specific forbidden patterns based on organization/jurisdiction/legal basis
- Includes validation matrix table

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| CRITICAL: Forbidden list conflicts with guidance | CRITICAL | Lists 32 forbidden starters (lines 156-191) but many are contradicted by other modules' guidance |
| Context forbidden logic uses org code map | MEDIUM | Hard-coded mapping DJI/OM/ZM/3RO/CJIB/KMAR/FIOD - if organizations change, must update code |
| Forbidden starters too aggressive | HIGH | Forbids "proces waarbij", "handeling die", "vorm van" - but SemanticCat explicitly RECOMMENDS these as kick-off terms! |
| Validation matrix repetitive | MEDIUM | Table has 8 rows, all marked ✅ - no explanation of what each check means |
| Extended list enabled by default | MEDIUM | extended_forbidden_list=True adds 32 forbidden starters by default; no performance consideration |
| Silent context corruption | MEDIUM | If organization_contexts/juridical_contexts/legal_basis_contexts shared state keys are missing, silently uses empty list |

**CRITICAL Contradictions with Other Modules:**
- **vs. SemanticCategorisationModule PROCES guidance:** Explicitly recommends:
  - "start with: 'activiteit waarbij...'" → ErrorPrevention forbids "proces waarbij"
  - "handeling die..." → ErrorPrevention forbids "handeling die"
  - "proces waarin..." → ErrorPrevention forbids these exact patterns!
- **vs. GrammarModule:** Forbids "is", "betreft", "omvat", "betekent" but GrammarModule discusses form selection without prohibiting

**Token Usage:** ~200 tokens
**Dependencies:** HARD - ContextAwarenessModule (expects shared state keys)

**Recommendation:** CRITICAL FIX - Align forbidden starters with SemanticCategorisation kick-off terms. Remove contradictory forbiddens or clarify that certain forbiddens apply EXCEPT for kick-off terms. Replace hard-coded org mappings with config lookup.

---

### 9. MetricsModule (Lines 1-327)

**Current Function:**
- Calculates complexity score (1-10) based on term length, word count, context count
- Estimates word count from character limits
- Provides quality checks (enkelvoudig zin, lengte, no special chars, context hanteerbaar, clear term)
- Generates scoring advice

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| Complexity score vague | MEDIUM | "Complexity factors" add 1-2 points each but no documentation of scoring philosophy |
| Character limit extraction fragile | MEDIUM | Tries config.min_chars / config.max_chars but should use metadata like OutputSpec does |
| Word estimate inaccurate | MEDIUM | Uses average word length 5.5 chars but Dutch average is 5.2-5.8 depending on domain |
| Quality checks are guesses | MEDIUM | "Enkelvoudig zin mogelijk: estimated_words <= 40" - no basis for 40-word limit |
| Context complexity binning crude | MEDIUM | "High if > 3 contexts, Medium otherwise" - no research backing |
| No downstream consumers | MEDIUM | Module generates metrics but DefinitionTaskModule never uses them |
| Over-engineering optional module | LOW | Has track_history config option but never implemented |

**Contradictions with Other Modules:**
- **vs. OutputSpecificationModule:** Character limits defined in OutputSpec (150-350 chars default) but MetricsModule tries to read from config object which may not have them
- **vs. ContextAwarenessModule:** Uses org_contexts.length for complexity but ignores juridical_contexts and legal_basis_contexts

**Token Usage:** ~200 tokens
**Dependencies:** None declared (but assumes config attributes)

**Recommendation:** REFACTOR - Simplify complexity scoring to 3 levels (simple/moderate/complex). Use consistent character limit source. Remove unused track_history. Make metrics optional (priority=10). Consider removing if metrics not consumed downstream.

---

### 10. DefinitionTaskModule (Lines 1-300)

**Current Function:**
- Provides final instruction and checklist
- Builds quality control questions
- Generates metadata with timestamp
- Builds ontological marker instruction
- Includes prompt metadata (term type, contexts, timestamp)

**Problems Found:**

| Problem | Severity | Details |
|---------|----------|---------|
| CRITICAL: Ontological category hints duplicate SemanticCat | CRITICAL | Lines 189-196 hardcodes category hints that SemanticCat already provided (proces→"activiteit/handeling", etc.) |
| Context extraction logic fragile | HIGH | Lines 86-104 attempt multiple fallback strategies for context keys (juridische_context vs juridisch vs wettelijke_basis vs wettelijk) but this is legacy handling for EPIC-010 migration |
| Duplicates checklist items from ErrorPrevention | MEDIUM | Checklist includes "Geen verboden woorden (aspect, element, kan, moet, etc.)" but ErrorPreventionModule more comprehensive |
| Timestamp UTC conversion unnecessary | LOW | Uses datetime.now(UTC) but for non-critical metadata |
| Prompt metadata at end wastes space | MEDIUM | Metadata could be injected at start for parsing, not at definition end |

**Contradictions with Other Modules:**
- **vs. SemanticCategorisationModule:** Duplicates category-specific guidance (lines 189-196)
- **vs. ErrorPreventionModule:** Both include forbidden word lists but different scopes
- **vs. GrammarModule:** Checklist item "Geen toelichting, voorbeelden of haakjes" overlaps with GrammarModule guidance

**Token Usage:** ~180 tokens
**Dependencies:** HARD - SemanticCategorisationModule (but doesn't declare it)

**Recommendation:** CONSOLIDATE - Remove ontological category hints (let SemanticCat own this). Consolidate forbidden words list with ErrorPreventionModule. Move metadata block to template-based insertion (as comment or structured format).

---

## Cross-Module Contradiction Analysis

### Critical Contradictions (Require Immediate Resolution)

#### Contradiction #1: Forbidden Patterns vs. Recommended Patterns (SEVERITY: CRITICAL)

**Conflict:**
- **ErrorPreventionModule (lines 179-186)** forbids:
  - "proces waarbij"
  - "handeling die"
  - "vorm van", "type van", "soort van"

- **SemanticCategorisationModule (lines 182-207)** EXPLICITLY RECOMMENDS AS KICK-OFF:
  - PROCES: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
  - TYPE: 'woord dat...', 'document dat...', 'persoon die...'

**Impact:** LLM receives contradictory instructions. Will either ignore one set or oscillate between them.

**Root Cause:** ErrorPrevention module was designed for legacy prompt; SemanticCat represents newer ESS-02 standard. Modules never reconciled.

**Resolution:** Remove conflicting items from ErrorPrevention forbidden list OR add exception clause: "EXCEPT for kick-off terms in semantic categorisation section"

---

#### Contradiction #2: Haakjes (Parentheses) Allowed vs. Forbidden (SEVERITY: CRITICAL)

**Conflict:**
- **OutputSpecificationModule (line 144):** "Geen haakjes voor toelichtingen"
- **GrammarModule (lines 225-237):** "Plaats afkortingen direct na de volledige term tussen haakjes" → Example: "Dienst Justitiële Inrichtingen (DJI)"
- **IntegrityModule INT-07 (lines 278-287):** Same guidance on afkortingen in haakjes

**Impact:** Contradictory guidance on same concept (abbreviations). OutputSpec says NO haakjes, Grammar/Integrity say YES for abbreviations.

**Root Cause:** OutputSpec conflates "no haakjes for explanation" with "no haakjes at all". Grammar correctly specifies "haakjes only for abbreviations".

**Resolution:** Clarify in OutputSpec: "Geen haakjes voor toelichtingen - MAAR afkortingen plaatsen tussen haakjes is verplicht (bijv. DJI)"

---

#### Contradiction #3: Category Naming Scheme Triplication (SEVERITY: CRITICAL)

**Conflict:**
Three different category naming systems:

1. **SemanticCategorisationModule:** "proces", "type", "resultaat", "exemplaar" (lowercase, matches ESS-02)
2. **TemplateModule:** "Proces", "Object", "Actor", "Toestand", "Gebeurtenis", "Maatregel", "Informatie", "Regel", "Recht", "Verplichting" (10 categories, different names entirely)
3. **DefinitionTaskModule:** "soort", "exemplaar", "proces", "resultaat" (Dutch names, different order)

**Impact:** If metadata passes "proces", which templates load? None, because TemplateModule looks for "Proces" with capital P. Category naming is broken across entire module stack.

**Root Cause:** Modules developed independently without coordinating on category schema.

**Resolution:** Unify on single naming scheme. Recommend: semanctic-cat lowercase (processo, type, resultaat, exemplaar) as canonical. Update TemplateModule and DefinitionTask to match.

---

### High-Priority Contradictions

#### Contradiction #4: Grammatical Structure Rules Overlap

**Conflict:**
- **GrammarModule:** Specifies enkelvoud, actieve vorm, tegenwoordige tijd (general grammar)
- **StructureRulesModule STR-01:** "definitie start met zelfstandig naamwoord"
- **SemanticCategorisationModule:** "kick-off term MOET zelfstandig naamwoord zijn"

**Impact:** Same rule stated 3 times with varying levels of detail. Confusing emphasis.

**Resolution:** Consolidate to single statement in appropriate module. STR-01 should own this rule; others reference it.

---

#### Contradiction #5: Context Handling (EPIC-010 Migration Incomplete)

**Conflict:**
Multiple modules attempt to handle context extraction with fallback logic:
- **ContextAwarenessModule (lines 368-423):** Extracts "organisatorisch", "juridisch", "wettelijk"
- **DefinitionTaskModule (lines 86-104):** Attempts fallbacks: "juridische_context" OR "juridisch", "wettelijke_basis" OR "wettelijk"
- **ErrorPreventionModule (lines 77-79):** Expects shared state from ContextAware: "organization_contexts", "juridical_contexts", "legal_basis_contexts"

**Impact:** EPIC-010 migration from legacy "domein" to new context types is incomplete. Code has scattered migration logic.

**Resolution:** Complete EPIC-010 migration. Remove fallback logic. Standardize key names everywhere.

---

## Token Waste Analysis

| Source | Tokens | % of Total | Avoidable |
|--------|--------|-----------|-----------|
| StructureRulesModule hardcoded rules | 150 | 2.0% | YES - use cache |
| Duplicate _format_rule in 5 modules | 60 | 0.8% | YES - extract base |
| Duplicate afkorting rules (Gram + INT-07) | 50 | 0.7% | YES - consolidate |
| Duplicate ontological hints (SemanticCat + DefinTask) | 40 | 0.5% | YES - deduplicate |
| TemplateModule dead code | 120 | 1.6% | YES - remove/fix |
| Unused confidence indicators (ContextAware) | 30 | 0.4% | YES - remove |
| Verbose category guidance (SemanticCat) | 100 | 1.3% | YES - condense |
| Extended forbidden starters (ErrorPrev) | 80 | 1.1% | MAYBE - keep if needed |
| Unused shared state values | 40 | 0.5% | YES - consolidate |
| **SUBTOTAL AVOIDABLE** | **670** | **8.9%** | |
| **SUBTOTAL MAYBE** | **80** | **1.1%** | |
| **ESTIMATED TOTAL WASTE** | **750** | **~10%** | |

**Full Prompt Estimated Size:** ~7,500 tokens
**Avoidable Waste:** 750 tokens (10%)
**After Fixes Potential:** ~6,750 tokens (10% reduction)

---

## Priority Matrix

### CRITICAL - Fix Immediately

| Issue | Module(s) | Impact | Effort | Benefit |
|-------|-----------|--------|--------|---------|
| Forbidden patterns contradict recommended | ErrorPrevention + SemanticCat | LLM confusion | 2h | HIGH |
| Haakjes contradiction | OutputSpec + Grammar + Integrity | Format errors | 1h | HIGH |
| Category naming triplication | TemplateModule + SemanticCat + DefinTask | Module silently broken | 3h | CRITICAL |
| TemplateModule validation bug | TemplateModule | Module never runs | 2h | MEDIUM |
| STR rules hardcoding | StructureRulesModule | Token waste | 1h | MEDIUM |

### HIGH - Fix in Next Sprint

| Issue | Module(s) | Impact | Effort | Benefit |
|-------|-----------|--------|--------|---------|
| Context migration (EPIC-010) incomplete | Multiple | Code duplication, fragility | 4h | HIGH |
| Duplicate afkorting rules | Grammar + Integrity | Maintenance nightmare | 2h | MEDIUM |
| Unused shared state | ContextAware + ErrorPrev | Silent failures | 2h | MEDIUM |
| Over-engineered ContextAware | ContextAware | Token waste | 2h | MEDIUM |
| Confidence indicators unused | ContextAware | Dead code | 1h | LOW |

### MEDIUM - Fix When Refactoring

| Issue | Module(s) | Impact | Effort | Benefit |
|-------|-----------|--------|--------|---------|
| Module dependencies not declared | Multiple | Invisible failures | 2h | MEDIUM |
| Duplicate category hints | SemanticCat + DefinTask | Maintenance | 1h | LOW |
| Verbose category guidance | SemanticCat | Token waste | 2h | MEDIUM |
| Complexity score vague | MetricsModule | LLM confusion | 1h | LOW |
| Filter fragility (startswith) | Rule modules | Technical debt | 1h | LOW |

---

## Detailed Recommendations

### RECOMMENDATION 1: Unify Category Naming (CRITICAL)

**Issue:** Three different category naming schemes cause TemplateModule to never run.

**Solution:**
1. Choose canonical naming: `['type', 'proces', 'resultaat', 'exemplaar']` (lowercase, ESS-02 standard)
2. Update all metadata injection points to use canonical names
3. Update all modules:
   - **SemanticCat:** Already correct ✅
   - **TemplateModule:** Map category names to templates OR remove if templates unneeded
   - **DefinitionTask:** Use canonical names in checklist hints
4. Add validation in ModuleContext to enforce schema

**Files to Update:**
- `semantic_categorisation_module.py` - ensure metadata key is consistent
- `template_module.py` - fix validation and category mapping
- `definition_task_module.py` - align checklist hints

**Token Impact:** -40 tokens (remove broken category schema)
**Effort:** 2 hours

---

### RECOMMENDATION 2: Resolve Forbidden vs. Recommended Contradiction (CRITICAL)

**Issue:** ErrorPreventionModule forbids "proces waarbij", "handeling die" but SemanticCat recommends them as kick-off terms.

**Solution:**
1. In ErrorPreventionModule, revise forbidden starters list:
   - Remove: "proces waarbij", "handeling die", "vorm van", "type van", "soort van"
   - Add clarification: "These are forbidden EXCEPT as semantic categorisation kick-off terms (see ESS-02 section)"
2. Keep only genuinely forbidden patterns:
   - Koppelwerkwoorden that aren't part of formal construction: "is", "betreft", "omvat", "betekent"
   - Lidwoorden at start: "de", "het", "een"

**Files to Update:**
- `error_prevention_module.py` lines 156-191

**Token Impact:** -50 tokens (shorter forbidden list)
**Effort:** 1 hour

---

### RECOMMENDATION 3: Clarify Haakjes Rule (CRITICAL)

**Issue:** OutputSpec says "no haakjes" but Grammar says "haakjes for abbreviations required".

**Solution:**
1. In OutputSpecificationModule, revise guidance:
   - Change: "Geen haakjes voor toelichtingen"
   - To: "Geen haakjes voor toelichtingen; haakjes ZIJN verplicht voor afkortingen (bijv. DJI)"
2. In GrammarModule INT-07, confirm this is canonical rule
3. Remove duplication of INT-07 in IntegrityModule (already exists in Integrity module)

**Files to Update:**
- `output_specification_module.py` line 144
- Consider consolidating Grammar and Integrity afkorting rules

**Token Impact:** +10 tokens (adds clarity, but consolidated rules save 50 tokens elsewhere)
**Effort:** 1 hour

---

### RECOMMENDATION 4: Fix TemplateModule (CRITICAL)

**Issue:** Module never executes due to broken validation (expects metadata key "semantic_category" that's never set).

**Options:**
A. **Remove** - If templates not critical, delete module entirely (save 120 tokens)
B. **Fix** - Map SemanticCat categories to template examples, inline in SemanticCat
C. **Refactor** - Make TemplateModule optional (remove validation requirement)

**Recommendation:** REMOVE
- SemanticCategorisationModule already provides comprehensive examples per category
- TemplateModule provides different template examples that are redundant
- Keeping both causes confusion on which examples to use

**Token Impact:** -120 tokens (remove dead module)
**Effort:** 1 hour (delete file, remove from orchestrator)

---

### RECOMMENDATION 5: Migrate StructureRulesModule to Cached Loading (HIGH)

**Issue:** StructureRulesModule hardcodes all 9 rules (63 lines) when other rule modules load from cache.

**Solution:**
1. Move STR rules to `config/toetsregels/regels/` JSON files (if not already there)
2. Update StructureRulesModule to use cached loading like ARAI/CON/ESS/SAM/VER
3. Simplify execute() method from 70 lines to 15 lines

**Before:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### 🏗️ Structuur Regels (STR):")
    sections.extend(self._build_str01_rule())  # 54 lines of building logic
    sections.extend(self._build_str02_rule())  # ...
    # ... 7 more rule builders ...
```

**After:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### 🏗️ Structuur Regels (STR):")

    from toetsregels.cached_manager import get_cached_toetsregel_manager
    manager = get_cached_toetsregel_manager()
    all_rules = manager.get_all_regels()
    str_rules = {k: v for k, v in all_rules.items() if k.startswith("STR-")}

    for regel_key, regel_data in sorted(str_rules.items()):
        sections.extend(self._format_rule(regel_key, regel_data))
    # ... return ...
```

**Token Impact:** -150 tokens (hardcoded rules removed; cache loading minimal)
**Effort:** 1 hour

---

### RECOMMENDATION 6: Extract Duplicate _format_rule Method (MEDIUM)

**Issue:** _format_rule method duplicated in ARAI, CON, ESS, INT, SAM, VER modules (6 copies of ~30 lines).

**Solution:**
1. Create base formatter in BasePromptModule
2. Update all 6 modules to inherit and call super()._format_rule()

**Code:**
```python
# In base_module.py
class BasePromptModule(ABC):
    def _format_rule_from_json(self, regel_key: str, regel_data: dict, include_examples: bool = True) -> list[str]:
        """Standard rule formatter for all rule modules."""
        lines = []
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        toetsvraag = regel_data.get("toetsvraag", "")
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")

        if include_examples:
            for goed in regel_data.get("goede_voorbeelden", []):
                lines.append(f"  ✅ {goed}")
            for fout in regel_data.get("foute_voorbeelden", []):
                lines.append(f"  ❌ {fout}")

        return lines
```

**Token Impact:** -60 tokens (remove duplicate code)
**Effort:** 2 hours (test all 6 modules)

---

### RECOMMENDATION 7: Consolidate Context Handling (EPIC-010 Completion) (HIGH)

**Issue:** EPIC-010 migration from legacy "domein" to new context types incomplete; fallback logic scattered across modules.

**Solution:**
1. Complete EPIC-010 by removing all fallback logic
2. Standardize context key names globally:
   - **ContextAwarenessModule** shares: `organization_contexts`, `juridical_contexts`, `legal_basis_contexts`
   - **DefinitionTaskModule** reads: same keys (no fallback)
   - **ErrorPreventionModule** reads: same keys (no fallback)
   - **MetricsModule** reads: same keys (no fallback)
3. Add migration test to ensure no legacy "domein" context leaks

**Files to Update:**
- `context_awareness_module.py` - finalize extraction
- `definition_task_module.py` - remove lines 86-104 fallback logic
- Add validation in ModuleContext

**Token Impact:** -40 tokens (remove fallback code)
**Effort:** 2 hours

---

### RECOMMENDATION 8: Simplify ContextAwarenessModule (MEDIUM)

**Issue:** Over-engineered with 3 formatting levels but configuration doesn't select level; score-based selection always used.

**Solution:**
1. Remove rich/moderate/minimal complexity; keep only moderate (best default)
2. Remove unused confidence indicator logic (🔴🟡🟢)
3. Consolidate formatting to single _build_context_section method

**Token Impact:** -80 tokens (remove dead code)
**Effort:** 2 hours

---

### RECOMMENDATION 9: Merge OutputSpec and Grammar (HIGH)

**Issue:** Overlapping guidance on format, punctuation, abbreviations.

**Solution:**
1. Create new unified module: `FormattingModule` combining:
   - Output format requirements (from OutputSpec)
   - Punctuation rules (from Grammar)
   - Abbreviation rules (from Grammar + Integrity)
2. Update Grammar module to focus ONLY on grammatical structures (not format)
3. Update priority: FormattingModule = 90, Grammar = 80

**Token Impact:** -100 tokens (consolidate overlapping content)
**Effort:** 3 hours

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1) - 6 hours
1. **RECOMMENDATION 2:** Resolve forbidden vs. recommended (1h)
2. **RECOMMENDATION 3:** Clarify haakjes rule (1h)
3. **RECOMMENDATION 4:** Remove TemplateModule (1h)
4. **RECOMMENDATION 5:** Migrate StructureRules to cache (1h)
5. Testing & validation (2h)

**Token Impact After Phase 1:** -300 tokens (cumulative)

### Phase 2: Duplication Fixes (Week 2) - 8 hours
6. **RECOMMENDATION 1:** Unify category naming (2h)
7. **RECOMMENDATION 6:** Extract _format_rule (2h)
8. **RECOMMENDATION 7:** Complete EPIC-010 (2h)
9. Testing (2h)

**Token Impact After Phase 2:** -500 tokens (cumulative)

### Phase 3: Refactoring (Week 3) - 7 hours
10. **RECOMMENDATION 8:** Simplify ContextAware (2h)
11. **RECOMMENDATION 9:** Merge OutputSpec/Grammar (3h)
12. Final testing & validation (2h)

**Token Impact After Phase 3:** -750 tokens (cumulative, ~10% reduction)

---

## Testing Strategy

### Unit Tests Required

```python
# Test 1: Verify no forbidden patterns in SemanticCat kick-offs
def test_semantic_kickoffs_not_forbidden():
    semantic_cat = SemanticCategorisationModule()
    error_prev = ErrorPreventionModule()
    # Ensure "proces waarbij" in SemanticCat not in forbidden list

# Test 2: Verify category naming consistency
def test_category_naming_consistent():
    # All modules use same category names
    categories = ['type', 'proces', 'resultaat', 'exemplaar']
    # Check metadata injection, SemanticCat, DefinTask align

# Test 3: Verify context shared state contract
def test_context_shared_state_keys():
    # ContextAware shares keys that ErrorPrev, DefinTask, Metrics expect
    expected_keys = ['organization_contexts', 'juridical_contexts', 'legal_basis_contexts']

# Test 4: Verify TemplateModule fixed or removed
def test_template_module_deprecation():
    # Either removed or validation fixed
    pass

# Test 5: Verify STR rules loaded from cache
def test_str_module_cached_loading():
    str_module = StructureRulesModule()
    assert "cache" in str_module.execute.__doc__ or "cached_manager" in str_module.execute.__code__
```

### Integration Tests Required

- Verify full prompt generation with all 16 modules
- Check for contradictory output in generated prompt
- Measure token count reduction
- LLM behavior test: does it produce consistent definitions?

---

## Metrics for Success

### Before Fixes
- **Total tokens:** ~7,500
- **Module count:** 16
- **Contradictions:** 5 critical
- **Dead code modules:** 1 (TemplateModule)
- **Code duplication:** 6 modules with identical _format_rule

### After Fixes
- **Total tokens:** ~6,750 (10% reduction)
- **Module count:** 15 (TemplateModule removed)
- **Contradictions:** 0 (resolved)
- **Dead code modules:** 0
- **Code duplication:** 0
- **Test coverage:** 100% of critical paths
- **LLM behavior:** Consistent category application

---

## Appendix A: Detailed Module Dependency Graph

```
ExpertiseModule (root)
├── OutputSpecificationModule (root)
├── GrammarModule (soft: ExpertiseModule.word_type)
├── ContextAwarenessModule (root)
│   └── ErrorPreventionModule (depends on ContextAware shared state)
├── SemanticCategorisationModule (root)
│   └── TemplateModule (broken: validates missing metadata)
│   └── DefinitionTaskModule (depends on SemanticCat.ontological_category)
├── ARAI/CON/ESS/STR/INT/SAM/VER RulesModules (root - load from cache)
├── MetricsModule (root - but assumes config attributes)
└── Orchestrator (calls all modules in order)
```

**Missing Declarations:**
- GrammarModule should declare hard dep on ExpertiseModule
- ErrorPreventionModule should declare hard dep on ContextAware
- DefinitionTaskModule should declare hard dep on SemanticCat
- All rule modules should declare soft dep on cached rule manager

---

## Appendix B: Token Usage Summary by Module

| Module | Estimated Tokens | % of Prompt | Redundancy | Can Reduce |
|--------|------------------|------------|-----------|-----------|
| ExpertiseModule | 150 | 2.0% | LOW | NO |
| OutputSpecificationModule | 100 | 1.3% | MEDIUM | 40% (merge) |
| GrammarModule | 140 | 1.9% | MEDIUM | 30% (merge) |
| ContextAwarenessModule | 230 | 3.1% | MEDIUM | 35% (simplify) |
| SemanticCategorisationModule | 180 | 2.4% | MEDIUM | 40% (condense) |
| TemplateModule | 120 | 1.6% | HIGH | 100% (remove) |
| ARAI RulesModule | 200 | 2.7% | LOW | 0% |
| CON RulesModule | 80 | 1.1% | LOW | 0% |
| ESS RulesModule | 150 | 2.0% | LOW | 0% |
| StructureRulesModule | 250 | 3.3% | HIGH | 60% (use cache) |
| IntegrityRulesModule | 200 | 2.7% | LOW | 20% (remove dupes) |
| SAMRulesModule | 60 | 0.8% | LOW | 0% |
| VER RulesModule | 50 | 0.7% | LOW | 0% |
| ErrorPreventionModule | 200 | 2.7% | MEDIUM | 30% (trim) |
| MetricsModule | 200 | 2.7% | MEDIUM | 10% (simplify) |
| DefinitionTaskModule | 180 | 2.4% | MEDIUM | 25% (dedupe) |
| **TOTAL** | **~7,500** | **100%** | | **~750 (10%)** |

---

## Summary & Next Steps

This analysis identified **7 critical issues** requiring immediate resolution:

1. **Forbidden vs. recommended patterns contradict** - LLM receives conflicting instructions
2. **Haakjes contradiction** - Format guidance conflicts within same concept
3. **Category naming triplication** - Three different naming schemes break module contracts
4. **TemplateModule broken** - Validates for metadata never set; module silently fails
5. **StructureRulesModule hardcoding** - 150 tokens of unnecessary code duplication
6. **EPIC-010 incomplete** - Scattered fallback logic across modules indicates incomplete migration
7. **Token waste** - ~750 tokens (10%) of prompt are redundant/dead code

**Recommended action:** Implement Phase 1 (Critical Fixes) immediately to resolve contradictions. This will also reduce token usage by 300 tokens (~4%) and clarify prompt intent to LLM.

**Estimated savings:** 750 tokens (10% reduction) across all 3 phases, improving both cost and LLM behavior consistency.

---

**End of Analysis**
**Prepared by:** Debug Specialist
**Classification:** Technical Architecture Review
**Status:** Ready for Action
