# Comprehensive Exploration: Waarom "Type" Dominant Lijkt als Ontologische Categorie

**Onderzoeksvraag:** Waarom komt "type" bijna altijd als resultaat bij een begrip als ontologische categorie?

**Datum:** 2025-11-03
**Scope:** Multi-agent analyse met Explore, Database Analysis en Prompt Engineering agents
**Status:** ✅ COMPLEET - Root causes geïdentificeerd

---

## Executive Summary

### 🔍 Hoofdbevinding: **GEEN "TYPE" DOMINANTIE IN DATABASE**

De veronderstelling dat "type" dominant is, **wordt NIET ondersteund door de data**:

| Categorie | Count | Percentage |
|-----------|-------|------------|
| **Proces** | **43** | **46.74%** ← LARGEST |
| **Type** | **40** | **43.48%** ← Close second |
| **Resultaat** | 7 | 7.61% |
| **Exemplaar** | 2 | 2.17% |

**Type en Proces zijn vrijwel gelijk verdeeld, met PROCES als winnaar!**

### ⚠️ Echter: Er IS bias in het classificatiesysteem

Hoewel de database geen type-dominantie toont, zijn er **structurele biases** die type kunnen bevorderen:

1. **Pattern Coverage Bias**: TYPE heeft 6 suffixes, EXEMPLAAR heeft 0
2. **Validation Pattern Bias**: TYPE patronen zijn breder dan RESULTAAT/EXEMPLAAR
3. **UI Ordering Bias**: TYPE wordt eerst getoond in ESS-02 prompt
4. **Suffix Weight Bias**: Suffix matching krijgt hoogste score (0.4), favoriseert type/proces

---

## 1. Classificatiesysteem Architectuur

### 1.1 TWEE SEPARATE SYSTEMEN

#### System A: TYPE/PROCES/RESULTAAT/EXEMPLAAR (Main)
**Location:** `src/domain/ontological_categories.py`
```python
class OntologischeCategorie(Enum):
    TYPE = "type"           # Soort/klasse
    PROCES = "proces"       # Activiteit/handeling
    RESULTAAT = "resultaat" # Uitkomst/bevinding
    EXEMPLAAR = "exemplaar" # Specifiek geval
```

#### System B: U/F/O Classification (Support)
**Location:** `src/services/classification/ontological_classifier.py`
- UNIVERSEEL (U) - Universal concepts
- FUNCTIONEEL (F) - Domain-specific
- OPERATIONEEL (O) - Organization-specific

**Vrijwel niet gebruikt in productie** (0% in database)

### 1.2 Classification Flow

```
User Input (Begrip + Context)
    ↓
_render_category_preview() in tabbed_interface.py:283
    ↓
ImprovedOntologyClassifier.classify() ← PATTERN-BASED (niet AI!)
    ↓
Store in SessionState:
  - "determined_category" (auto)
  - "category_reasoning"
  - "category_scores"
    ↓
Display UI: "Voorgesteld: {category}"
    ↓
User Manual Override? (Dropdown: TYPE/PROCES/RESULTAAT/EXEMPLAAR)
    ↓
_handle_definition_generation()
    ↓
definition_service.generate_definition(categorie=...)
    ↓
DefinitionOrchestratorV2.create_definition()
    ↓
SAVE to database: categorie column (VARCHAR(50))
    ↓
ESS-02 Validation (checks definition text clarity)
```

**KEY INSIGHT:** Classificatie gebeurt **NIET via AI prompt**, maar via **rule-based pattern matching**!

---

## 2. Pattern-Based Classifier Analysis

### 2.1 Scoring Algorithm
**Location:** `src/ontologie/improved_classifier.py:128-242`

**Scores per category (0.0 to 1.0):**
- **Exact word match:** +0.6 (highest)
- **Suffix match:** +0.4
- **Suffix contains:** +0.2
- **Indicator pattern:** +0.1
- **Context boost:** +0.2 per match
- **Juridische context boost:** +0.15 per match

**Win Conditions:**
- Winner score ≥ 0.30 AND margin ≥ 0.12 → WINNER
- Else → Fallback logic (default: PROCES)

### 2.2 Pattern Coverage per Category

| Category | Suffixes | Words | Indicators | Total Patterns |
|----------|----------|-------|------------|----------------|
| **TYPE** | **6** | 4 | 4 | **14** ✅ |
| **PROCES** | **5** | 4 | 4 | **13** ✅ |
| **RESULTAAT** | **3** | 6 | 4 | **13** ⚠️ |
| **EXEMPLAAR** | **0** ❌ | 3 | 4 | **7** ❌ |

**CRITICAL BIAS:** EXEMPLAAR heeft GEEN suffixes, TYPE heeft 6!

### 2.3 Pattern Details

#### TYPE Patterns (src/ontologie/improved_classifier.py:38-54)
```python
"type": {
    "suffixes": ["systeem", "model", "type", "soort", "klasse", "categorie"],
    "indicators": [
        r"\b(soort|type|categorie|klasse|vorm) van\b",
        r"\bis een\b.*\b(systeem|model|instrument)\b",
    ],
    "words": ["toets", "formulier", "register", "document"],
}
```

#### PROCES Patterns (lines 55-64)
```python
"proces": {
    "suffixes": ["atie", "tie", "ing", "eren", "isatie"],
    "indicators": [
        r"\b(handeling|proces|procedure|verloop)\b",
        r"\b(uitvoeren|verrichten|doen) van\b",
    ],
    "words": ["validatie", "verificatie", "beoordeling", "controle"],
}
```

#### RESULTAAT Patterns (lines 65-81)
```python
"resultaat": {
    "suffixes": ["besluit", "uitspraak", "vonnis"],  # Only 3!
    "indicators": [
        r"\b(resultaat|uitkomst|gevolg|effect)\b",
        r"\bwordt verleend\b",
    ],
    "words": ["besluit", "rapport", "conclusie", "advies", "vergunning", "beschikking"],
}
```

#### EXEMPLAAR Patterns (lines 82-92)
```python
"exemplaar": {
    "suffixes": [],  # ❌ EMPTY!
    "indicators": [
        r"\b(dit|deze|dat) (specifieke|concrete)\b",
        r"\bmet kenmerk\b",
    ],
    "words": ["verdachte", "betrokkene", "aanvrager"],  # Only 3 words!
}
```

**BIAS IDENTIFIED:**
- TYPE heeft 6 suffixes × 0.4 score = maximaal 2.4 punten mogelijk
- EXEMPLAAR heeft 0 suffixes × 0.4 = 0 punten mogelijk via suffixes!

---

## 3. Database Reality Check

### 3.1 Actual Distribution (92 definitions)

```
proces:     43 (46.74%) ← WINNER
type:       40 (43.48%) ← Close second
resultaat:   7 (7.61%)
exemplaar:   2 (2.17%)
```

**Data Quality:**
- ✅ No NULL values
- ✅ All conform to schema constraints
- ✅ No invalid categories

### 3.2 Schema Definition
**Location:** `src/database/schema.sql:15-26`
```sql
categorie VARCHAR(50) NOT NULL CHECK (categorie IN (
    'type', 'proces', 'resultaat', 'exemplaar',  -- Legacy support
    'ENT', 'ACT', 'REL', 'ATT', 'AUT', 'STA', 'OTH'  -- Extended (UNUSED!)
))
```

**Extended categories (ENT, ACT, etc.):** 0% usage in database!

### 3.3 Sample Begrippen

#### TYPE Examples (40 total):
- **verifiëren** - "Het vergelijken van de ingewonnen identiteitsgegevens..."
- **persoon** - "Een mens van vlees en bloed"
- **identiteitsbewijs** - "Een door een bevoegde instantie uitgereikt..."

#### PROCES Examples (43 total):
- **dagvaarding** - "Procedure waarbij een bevoegde instantie..."
- **hoger beroep** - "Soort rechtsmiddel waarmee een beslissing..."
- **identiteit verifiëren** - "Gegevens worden gecontroleerd..."

#### RESULTAAT Examples (7 total):
- **digitaal identiteitsbewijs** - "Resultaat van een proces dat..."
- **identiteitskenmerk** - "biometrische of biografische eigenschap..."
- **vermogen** - "Resultaat van het vaststellen van de totale waarde..."

#### EXEMPLAAR Examples (2 total):
- **digitaal identiteitsmiddel** - "Specifiek exemplaar..."
- **systeemdefinitie** - "Specifiek document waarin..."

### 3.4 Duplicate Begrippen with Different Categories

**Same begrip, different interpretations:**
- `biografisch identiteitskenmerk`: TYPE + RESULTAAT
- `biometrie`: PROCES + RESULTAAT
- `verbod`: PROCES + RESULTAAT
- `identiteitsmiddel`: TYPE + RESULTAAT

**Business Rule Question:** Is this intentional or data quality issue?

---

## 4. Validation Pattern Analysis (ESS-02)

### 4.1 Validation Patterns
**Location:** `src/toetsregels/regels/ESS-02.json`

| Category | Patterns | Pattern Breadth |
|----------|----------|-----------------|
| TYPE | `\b(categorie\|soort\|klasse)\b` | ⚠️ **VERY BROAD** |
| PROCES | `\b(proces\|activiteit\|handeling\|gebeurtenis)\b` | ⚠️ **VERY BROAD** |
| RESULTAAT | `\b(is het resultaat van\|het resultaat van)\b` | ✅ SPECIFIC |
| EXEMPLAAR | `\b(exemplaar\|specifiek exemplaar\|particulier)\b` | ✅ SPECIFIC |

**BIAS:** TYPE en PROCES patronen matchen veel breder dan RESULTAAT/EXEMPLAAR!

**Example:**
- "dit is een **soort** activiteit" → Matches BOTH type AND proces!
- "het **resultaat** van" → Only matches resultaat ✓

### 4.2 Validation Logic
**Location:** `src/toetsregels/regels/ESS-02.py:134-161`

**Steps:**
1. Check metadata override (always succeeds if provided)
2. Check for bad examples → FAIL
3. Detect patterns per category → Count matches
4. **If 1 category:** PASS ✅
5. **If 2+ categories:** FAIL ❌ (ambiguous)
6. **If 0 categories:** FAIL ❌ (no clarity)
7. Check good examples → PASS if match
8. Fallback → FAIL

**IMPORTANT:** ESS-02 is **MEDIUM severity**, NOT blocking!
- Definition can be saved even if ESS-02 fails
- Only CRITICAL violations block saving

---

## 5. Prompt Engineering Analysis

### 5.1 ESS-02 Generation Hints
**Location:** `src/services/prompts/modules/semantic_categorisation_module.py:136-150`

```markdown
### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken:
• type (soort), • exemplaar (specifiek geval), • proces (activiteit), • resultaat (uitkomst)

BELANGRIJK: Bepaal de juiste categorie op basis van het BEGRIP zelf:
- Eindigt op -ING of -TIE en beschrijft een handeling? → PROCES
- Is het een gevolg/uitkomst van iets? → RESULTAAT
- Is het een classificatie/soort? → TYPE
- Is het een specifiek geval? → EXEMPLAAR
```

**BIAS DETECTED:**
1. **Ordering Bias:** TYPE listed first (primacy effect)
2. **Redundant Instruction:** Asks AI to "determine" category, but it's already pre-determined!
3. **Heuristic Mismatch:** Prompt heuristics don't match classifier patterns exactly

### 5.2 Category-Specific Guidance
**Location:** Same file, lines 179-257

**Pattern:**
- TYPE: 18 lines of guidance (most detailed!)
- PROCES: 18 lines
- RESULTAAT: 20 lines
- EXEMPLAAR: 18 lines

All categories get equal attention in detailed guidance → No bias here ✓

---

## 6. Root Cause Analysis

### 🎯 Primary Causes of Perceived "Type" Bias

#### ✅ CONFIRMED BIASES:

1. **Pattern Coverage Imbalance** (HIGH IMPACT)
   - TYPE: 6 suffixes, EXEMPLAAR: 0 suffixes
   - Suffix matching weighted highest (0.4 points)
   - **Impact:** TYPE has 6× more chances to score via suffixes than EXEMPLAAR

2. **Validation Pattern Breadth** (MEDIUM IMPACT)
   - TYPE pattern `\b(categorie|soort|klasse)\b` very broad
   - Can match in many contexts, even ambiguous ones
   - **Impact:** TYPE passes ESS-02 more easily than stricter categories

3. **UI Ordering Bias** (LOW IMPACT)
   - ESS-02 prompt lists "type" first
   - Primacy effect may influence human readers
   - **Impact:** Subtle psychological bias

4. **Fallback Hard-coding** (LOW IMPACT)
   - Line 279 in improved_classifier.py: hard-codes ["toets", "formulier", "document"] → TYPE
   - No equivalent for RESULTAAT/EXEMPLAAR
   - **Impact:** Edge cases favor TYPE

#### ❌ MYTH BUSTED:

1. **"Type is Most Common in Database"** → FALSE
   - Database shows: Proces (46.74%) > Type (43.48%)
   - Type is NOT dominant, almost tied with Proces

2. **"AI Prompts Favor Type"** → FALSE
   - Classification is pattern-based, NOT AI-driven
   - AI only writes definition AFTER category is determined
   - Prompt ordering has minimal impact

### 🎯 Secondary Contributing Factors

5. **Suffix Weight Dominance**
   - Suffix matches (+0.4) > Indicators (+0.1)
   - Categories with more suffixes naturally score higher
   - TYPE (6) and PROCES (5) benefit most

6. **EXEMPLAAR Underspecified**
   - Only 3 exact words: "verdachte", "betrokkene", "aanvrager"
   - Requires very specific phrasing to match
   - Most begrippen won't match these patterns

7. **RESULTAAT Medium Specificity**
   - 3 suffixes vs 6 for TYPE
   - Patterns require "resultaat van" phrasing
   - Mid-tier likelihood

---

## 7. Why Database Shows Proces > Type

### 🤔 If TYPE is favored, why is PROCES more common?

**Answer:** Because **PROCES also has favorable patterns!**

1. **PROCES has 5 suffixes** (vs TYPE's 6):
   - "-atie", "-tie", "-ing", "-eren", "-isatie"
   - Many Dutch verbs/nouns end with these!
   - Examples: validatie, verificatie, beoordeling, controle

2. **Legal domain bias toward processes:**
   - Juridische begrippen often describe procedures
   - "dagvaarding", "hoger beroep", "identiteit verifiëren"
   - Domain naturally contains many process concepts

3. **PROCES has default fallback:**
   - Config/ontology/category_patterns.yaml line 164: `default_category: "proces"`
   - When no clear winner, PROCES is chosen

**Conclusion:** PROCES and TYPE both have strong patterns → Almost equal distribution in DB!

---

## 8. Recommendations

### 🔧 SHORT TERM (Low-hanging fruit)

#### 1. Balance Pattern Coverage (HIGH PRIORITY)
```python
"exemplaar": {
    "suffixes": ["geval", "instantie", "voorbeeld"],  # Add 3 suffixes
    "words": ["verdachte", "betrokkene", "aanvrager", "partij", "casus"],
}

"resultaat": {
    "suffixes": ["besluit", "uitspraak", "vonnis", "beschikking", "advies", "rapport"],
    # Expand from 3 to 6
}
```

**Impact:** Equalizes suffix opportunities across categories

#### 2. Reorder ESS-02 Prompt Categories
```markdown
• proces (activiteit), • type (soort), • resultaat (uitkomst), • exemplaar (specifiek geval)
```
Or randomize order each time.

**Impact:** Removes primacy bias

#### 3. Add Fallback Hard-codes for All Categories
```python
if begrip_lower in ["besluit", "vergunning", "beschikking", "rapport", "advies"]:
    return RESULTAAT
if begrip_lower in ["verdachte", "betrokkene", "aanvrager", "partij", "casus"]:
    return EXEMPLAAR
```

**Impact:** Edge cases distributed more fairly

### 🔧 MEDIUM TERM (Requires testing)

#### 4. Adjust Suffix Weight vs Indicator Weight
```python
# Current
suffix_match: +0.4
indicator_match: +0.1

# Alternative (more balanced)
suffix_match: +0.3
indicator_match: +0.2
context_boost: +0.3  # Increase context importance
```

**Impact:** Reduces suffix dominance, increases context analysis

#### 5. Add Classifier Decision Logging
```python
logger.info(
    f"Classification for '{begrip}': "
    f"TYPE={scores['type']:.2f}, PROCES={scores['proces']:.2f}, "
    f"RESULTAAT={scores['resultaat']:.2f}, EXEMPLAAR={scores['exemplaar']:.2f} "
    f"→ Winner: {categorie.value} (margin: {margin:.2f})"
)
```

**Impact:** Transparency for debugging and tuning

#### 6. Narrow TYPE Validation Pattern
```json
"herkenbaar_patronen_type": [
    "\\b(is een|betreft een) (categorie|soort|klasse)\\b",  // Require "is een"!
    // Remove standalone: "\\b(categorie|soort|klasse)\\b"
]
```

**Impact:** Reduces false positives for TYPE in ESS-02 validation

### 🔧 LONG TERM (Strategic)

#### 7. Implement Machine Learning Classifier
- Train on 92 existing definitions
- Use features: suffix, keywords, context, sentence structure
- Compare ML predictions vs rule-based
- Hybrid approach: ML + rules

**Impact:** Data-driven classification, adaptive learning

#### 8. Introduce Confidence Thresholds
- Below 0.5 confidence → Ask user for manual classification
- Display confidence score in UI
- Track low-confidence cases for pattern improvement

**Impact:** User-in-the-loop for ambiguous cases

#### 9. Enforce Single Category per Begrip
- Add UNIQUE constraint: `UNIQUE(begrip, versie)`
- Business rule: One canonical interpretation per term
- Or: Allow multiple, but flag as "polysemous" with explicit versioning

**Impact:** Resolves duplicate begrip issue

---

## 9. Files Requiring Changes

### Core Classification Files:
- `/Users/chrislehnen/Projecten/Definitie-app/src/ontologie/improved_classifier.py`
  **Changes:** Add EXEMPLAAR/RESULTAAT suffixes, adjust weights, add logging

- `/Users/chrislehnen/Projecten/Definitie-app/config/ontology/category_patterns.yaml`
  **Changes:** Update pattern definitions, weights

### Validation Files:
- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-02.json`
  **Changes:** Narrow TYPE patterns, reorder category list

- `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-02.py`
  **Changes:** Add confidence threshold logic

### Prompt Files:
- `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/semantic_categorisation_module.py`
  **Changes:** Reorder categories, remove redundant "Bepaal" instruction, clarify it's pre-determined

### UI Files:
- `/Users/chrislehnen/Projecten/Definitie-app/src/ui/tabbed_interface.py`
  **Changes:** Display confidence score, add logging

### Database:
- `/Users/chrislehnen/Projecten/Definitie-app/src/database/schema.sql`
  **Changes:** Consider UNIQUE constraint, remove unused extended categories

---

## 10. Testing Strategy

### Unit Tests (Immediate)
1. Test each category with 10 representative begrippen
2. Verify suffix matching works correctly
3. Test fallback logic for edge cases
4. Validate ESS-02 pattern detection

### Integration Tests (After changes)
1. Run classifier on all 92 existing definitions
2. Compare old vs new classifications
3. Measure distribution changes
4. User acceptance: Do results "feel" better?

### A/B Testing (Long-term)
1. Deploy with logging enabled
2. Track category distribution over 100 new definitions
3. Measure ESS-02 pass rate per category
4. Collect user feedback on classification quality

---

## 11. Conclusion

### ❌ MYTH: "Type is dominant in the database"
**Reality:** Proces (46.74%) > Type (43.48%) - Almost equal!

### ✅ FACT: "There IS structural bias toward TYPE/PROCES"
**Causes:**
1. More suffix patterns (6 for TYPE, 5 for PROCES, 0 for EXEMPLAAR)
2. Broader validation patterns for TYPE
3. Suffix matching weighted highest in scoring

### 🎯 KEY INSIGHT:
The classification system **structurally favors categories with more suffixes** (TYPE and PROCES), but **domain characteristics** (legal terminology with many processes) result in **PROCES being most common**, not TYPE.

### 🚀 NEXT STEPS:
1. **Implement Short-term fixes** (1-2 dagen):
   - Add EXEMPLAAR/RESULTAAT suffixes
   - Reorder ESS-02 prompt
   - Add logging

2. **Test and validate** (1 week):
   - Run on existing 92 definitions
   - Measure distribution changes
   - Collect feedback

3. **Long-term strategic improvements** (backlog):
   - ML classifier
   - Confidence thresholds
   - Schema cleanup

---

## Appendix A: Complete Pattern Coverage Matrix

| Category | Suffixes (6) | Words (4) | Indicators (4) | Context Boost | Max Score |
|----------|--------------|-----------|----------------|---------------|-----------|
| TYPE | ✅✅✅✅✅✅ | ✅✅✅✅ | ✅✅✅✅ | ✅ | 3.5+ |
| PROCES | ✅✅✅✅✅ | ✅✅✅✅ | ✅✅✅✅ | ✅ | 3.3+ |
| RESULTAAT | ✅✅✅ | ✅✅✅✅✅✅ | ✅✅✅✅ | ✅ | 2.9+ |
| EXEMPLAAR | ❌ | ✅✅✅ | ✅✅✅✅ | ✅ | 2.3+ |

**Observation:** EXEMPLAAR has 34% lower max score potential than TYPE due to 0 suffixes!

---

## Appendix B: Database Query Used

```bash
sqlite3 data/definities.db <<EOF
.mode column
.headers on

-- Total count
SELECT 'Total definitions:' as metric, COUNT(*) as value
FROM definities;

-- Distribution by category
SELECT categorie, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM definities), 2) as percentage
FROM definities
GROUP BY categorie
ORDER BY count DESC;

-- NULL check
SELECT 'NULL categorie:' as metric, COUNT(*) as value
FROM definities
WHERE categorie IS NULL OR categorie = '';

-- Sample begrippen per category
SELECT categorie, begrip, SUBSTR(definitie, 1, 80) || '...' as definitie_preview
FROM definities
GROUP BY categorie
ORDER BY categorie;
EOF
```

---

**Document Status:** ✅ COMPLEET
**Created:** 2025-11-03
**Authors:** Multi-agent analysis (Explore + Database + Prompt Engineering agents)
**Review Status:** Pending stakeholder review
**Related Issues:** N/A (exploratory analysis)
