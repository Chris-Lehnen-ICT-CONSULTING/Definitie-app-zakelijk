# CONSENSUS RAPPORT: Prompt Optimalisatie Analyses
**Datum:** 2025-11-07
**Vergelijking:** DEF-101 (prompt-6) vs Nieuwe Analyse (prompt-7)
**Doel:** Identificeer consensus, unieke inzichten en samengesteld actieplan

---

## EXECUTIVE SUMMARY

Beide analyses identificeren **dezelfde fundamentele problemen** maar vanuit verschillende invalshoeken:
- **DEF-101**: Focus op BLOCKING contradictions die prompt unusable maken
- **Nieuwe Analyse**: Focus op architectuur (16 modules) + dubbel gebruik validatieregels

**Kritieke consensus:** Prompt is overengineered met ~65% redundantie en fundamentele conflicten.
**Verschil in aanpak:** DEF-101 lost conflicten op, Nieuwe Analyse verwijdert validatieregels volledig.

---

## 1. OVERLAPPENDE PROBLEMEN (CONSENSUS)

### 1.1 CONFLICT #1: "is" Paradox (IDENTIEK)

| Aspect | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Conflict** | ESS-02 requires "is een activiteit" BUT Line 300 forbids "is" | Regel 323-325 ❌ "Start niet met 'is'" VS Regel 73-77 ✅ "start met 'activiteit waarbij...'" |
| **Impact** | BLOCKING - NO VALID SOLUTION | AI krijgt tegengestelde instructies |
| **Severity** | 🔴 CRITICAL | 🔴 CRITICAL |
| **Status** | IDENTICAL ISSUE | IDENTICAL ISSUE |

**Consensus:** Dit is het meest kritieke conflict dat beide analyses identificeren.

---

### 1.2 CONFLICT #2: Containerbegrip Paradox (IDENTIEK)

| Aspect | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Conflict** | ARAI-02 forbids "proces", "activiteit" BUT ESS-02 templates use them | ARAI-02: "Vermijd 'proces', 'activiteit'" BUT ESS-02: "MOET starten met 'proces', 'activiteit'" |
| **Lines** | Line 126 (ARAI-02) vs Line 75 (ESS-02) | ARAI-02 vs ESS-02 regel |
| **Impact** | BLOCKING - ESS-02 requires what ARAI-02 forbids | ESS-02 vereist wat ARAI-02 verbiedt |
| **Status** | IDENTICAL ISSUE | IDENTICAL ISSUE |

**Consensus:** Beide analyses vinden exact hetzelfde conflict tussen ARAI-02 en ESS-02.

---

### 1.3 REDUNDANTIE: Enkelvoud Regel (CONSENSUS)

| Metric | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Herhalingen** | 5× (80% redundancy) | 5× (regels 26-31, 288-290, 299, 386) |
| **Locations** | Lines 26-31, 288, 289, 299, 386 | Exact dezelfde locaties |
| **Impact** | 80% redundant | 40% overall redundantie |

**Consensus:** Enkelvoud regel is kritieke redundantie in beide versies.

---

### 1.4 REDUNDANTIE: Koppelwerkwoord Verbod (CONSENSUS)

| Metric | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Herhalingen** | 6× (83% redundancy) | 6× (regels 78, 134, 294, 301-318, 344) |
| **Lines** | 133, 150-156, 294, 300-316, 344, 386 | Exact dezelfde locaties |
| **Impact** | 83% redundant | Belangrijk onderdeel 40% totaal |

**Consensus:** Koppelwerkwoord verbod is meest herhaalde regel.

---

### 1.5 REDUNDANTIE: Ontologische Categorie (CONSENSUS)

| Metric | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Herhalingen** | 5× (80% redundancy) | 3× (ESS-02, regel 141, STR-06) |
| **Lines 71-108** | 38 lines SHOULD BE 20 lines | Onderdeel van validatieregels |
| **Impact** | 80% redundant | Concept "essentie niet doel" 3× |

**Consensus:** ESS-02 is te uitgebreid en herhaald, maar nieuwe analyse meet minder herhalingen.

---

### 1.6 COGNITIEVE OVERLOAD (CONSENSUS)

| Metric | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Cognitive Load** | 9/10 (CRITICAL) → 4/10 | LLM Compliance ~60% → ~90% |
| **Forbidden Patterns** | 42 bullets linear | 42 regels (294-335) |
| **Individual Rules** | 45+ (3× over limit) | 53 validatieregels |
| **Impact** | Impossible to memorize | Te veel voor consistent LLM gedrag |

**Consensus:** Beide analyses identificeren severe cognitive overload door te veel regels.

---

### 1.7 FLOW PROBLEMEN (CONSENSUS)

| Aspect | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Metadata Position** | Lines 401-419 (END) | Should be line 10-15 |
| **Ontological Category** | Line 71 (BURIED) | Should be TOP 5 concepts |
| **Flow Score** | 4/10 → 8/10 | N/A (geen score) |

**Consensus:** Kritieke concepten zijn begraven, metadata komt te laat.

---

## 2. UNIEKE INZICHTEN PER ANALYSE

### 2.1 DEF-101 UNIEK (prompt-6)

#### A. BLOCKING Contradictions Framework
- **5 BLOCKING contradictions** expliciet gelabeld (DEF-101 priority)
- **Real Impact Examples** met concrete scenario's:
  ```
  Task: Define "vermogen" as RESULTAAT
  Attempt 1 (Following ESS-02): "is het resultaat van..." ❌ FAILS
  Attempt 2 (Following STR-01): "resultaat van processen..." ❌ FAILS
  Result: NO VALID SOLUTION
  ```

#### B. Exception Clause Solutions
- **Detailed fix strategies** met Python code examples:
  ```python
  # Add ESS-02 Exception in error_prevention_module.py
  exceptions_note = """
  ⚠️ EXCEPTION voor Ontologische Categorie (ESS-02):
  Bij het markeren van ontologische categorie MAG je starten met:
  - "activiteit waarbij..." (PROCES)
  - "resultaat van..." (RESULTAAT)
  """
  ```

#### C. 3-Tier Priority System
- **TIER 1 (10 rules):** ABSOLUTE REQUIREMENTS
- **TIER 2 (20 rules):** STRONG RECOMMENDATIONS
- **TIER 3 (15 rules):** QUALITY POLISH
- Visuele badges: ⚠️ (TIER 1), ✅ (TIER 2), ℹ️ (TIER 3)

#### D. Module Sync Verification
- ✅ **PERFECT SYNC** met codebase (16 modules)
- Module mapping table (lines → modules)
- Bevestiging: "Prompt is complete and up-to-date with codebase"

#### E. Comprehensive Test Suite
- `test_ess02_exception_clause_present()`
- `test_no_blocking_contradictions()`
- `test_redundancy_below_threshold()`
- `test_forbidden_patterns_categorized()`

#### F. Risk Assessment & Rollback Plan
- Risk matrix (probability × impact × mitigation)
- Feature flags per module voor gradual rollout
- Git rollback procedure

---

### 2.2 NIEUWE ANALYSE UNIEK (prompt-7)

#### A. DUBBEL GEBRUIK VALIDATIEREGELS (NIEUW!)
**Kritiek inzicht:** 48% van tokens (3.500) zijn regels die toch automatisch worden gevalideerd!

```python
# In Prompt (3.500 tokens):
AraiRulesModule → Voegt ARAI-01 t/m ARAI-06 toe aan prompt

# In Post-Processing (zelfde regels):
ModularValidationService → Voert ARAI-01.py uit op output
```

**Impact:** Grootste optimalisatie kans (-3.500 tokens) die DEF-101 niet identificeert!

#### B. Architectuur: 16 Modules Analysis
**Probleem:** Alle 16 modules draaien ALTIJD, ongeacht context of behoefte.

```
PromptServiceV2.build_generation_prompt()
    ↓
16 Prompt Modules (ALWAYS ACTIVE)
    ├── 6 Core Modules
    ├── 7 Validation Modules (3.500 tokens dubbel!)
    └── 3 Support Modules
    ↓
419 regels, 7.250 tokens
```

**Oplossing:** Conditional module loading + cache static modules

#### C. Token Reduction Metrics
- **Huidig:** 7.250 tokens
- **Quick Wins:** 5.000 tokens (-31%)
- **Volledig:** 2.650 tokens (-63%)
- **DEF-101:** 419 → 354 lines (-15.5%)

**Nieuwe analyse heeft agressievere target!**

#### D. Quick Wins Strategy (30 minuten)
1. **Verwijder validatieregels uit prompt** (-3.500 tokens)
2. **Consolideer verboden lijst** (-750 tokens)
3. **Fix conflicten** (0 tokens, +100% consistency)

**Total: -4.250 tokens in 30 minuten werk!**

#### E. Inverted Pyramid Structure (NIEUW!)
```
NIVEAU 1: MISSION (50 tokens)
NIVEAU 2: 3 GOLDEN RULES (300 tokens)
NIVEAU 3: TEMPLATES (400 tokens)
NIVEAU 4: REFINEMENT (800 tokens)
NIVEAU 5: CHECKLIST (100 tokens)
```

**DEF-101 heeft linear restructure, nieuwe analyse heeft hierarchical pyramid.**

#### F. Conditional Module Loading
```python
class PromptOrchestrator:
    def _filter_modules(self, context):
        if not context.has_juridische_context:
            skip_modules.append("legal_module")
```

**DEF-101 focus op reordering, nieuwe analyse op conditional execution.**

---

## 3. OPLOSSINGEN VERGELIJKING

### 3.1 CONFLICT RESOLUTIE

| Conflict | DEF-101 Oplossing | Nieuwe Analyse Oplossing | BESTE AANPAK |
|----------|-------------------|--------------------------|--------------|
| **"is" Paradox** | Add exception clause in `error_prevention_module.py` | Verduidelijk regel 323: "is een proces" vs "activiteit" | **DEF-101** (meer compleet) |
| **Container Terms** | Exempt ontological markers from ARAI-02 | Principle: ESS-02 vereist wat ARAI-02 verbiedt | **DEF-101** (concrete fix) |
| **Relative Clauses** | Replace "Vermijd bijzinnen" with "Minimize..." + exceptions | N/A (niet expliciet addressed) | **DEF-101** (alleen oplossing) |
| **Article "een"** | Add exception for ESS-02 ontological marking | N/A (niet expliciet addressed) | **DEF-101** (alleen oplossing) |
| **Context Usage** | Clarify "Implicit vs Explicit" context usage | N/A (niet expliciet addressed) | **DEF-101** (alleen oplossing) |

**Consensus:** DEF-101 heeft completere conflict resolutie strategie.

---

### 3.2 REDUNDANTIE ELIMINATIE

| Type | DEF-101 Aanpak | Nieuwe Analyse Aanpak | BESTE AANPAK |
|------|----------------|----------------------|--------------|
| **Enkelvoud** | Keep Grammar module, delete VER-01/02/03, cross-reference | Consolideer naar 1 locatie | **DEF-101** (meer detail) |
| **Koppelwerkwoord** | Keep STR-01 (best examples), merge forbidden list into 5 categories | Consolideer naar 3 templates | **NIEUWE** (agressiever) |
| **Ontologische** | Reduce lines 71-108 from 38 to 20 lines | Principle: Regels in post-processing, summary in prompt | **NIEUWE** (meer reductie) |
| **Forbidden Patterns** | Categorize 42 bullets into 7 groups | Replace 42 regels with 3 templates | **NIEUWE** (drastischer) |

**Consensus:** Nieuwe analyse heeft agressievere reductie, DEF-101 heeft veiligere incrementele aanpak.

---

### 3.3 FLOW RESTRUCTURING

| Aspect | DEF-101 Oplossing | Nieuwe Analyse Oplossing | BESTE AANPAK |
|--------|-------------------|--------------------------|--------------|
| **Module Order** | Reorder 16 modules (metadata first, ontological category #3) | N/A (niet expliciet) | **DEF-101** |
| **Metadata Position** | Move lines 401-419 to top (definition_task_module) | "Should be line 10-15" (geen implementatie) | **DEF-101** (concrete) |
| **Structure** | Hierarchical: TASK → CRITICAL → STRUCTURAL → QUALITY → VALIDATION | Inverted Pyramid: MISSION → 3 GOLDEN RULES → TEMPLATES → REFINEMENT → CHECKLIST | **NIEUWE** (innovatiever) |

**Consensus:** DEF-101 heeft concrete module reordering, Nieuwe Analyse heeft innovatievere structuur.

---

## 4. NIEUWE PROBLEMEN (prompt-7 vs prompt-6)

### 4.1 DUBBEL GEBRUIK VALIDATIEREGELS ⭐ GROOTSTE NIEUW INZICHT

**Probleem:** 53 validatieregels in prompt (7 modules: ARAI, CON, ESS, INT, SAM, STR, VER) EN in post-processing (ModularValidationService).

**Impact:**
- **3.500 tokens (48%)** zijn duplicate guidance
- **7 modules** doen dubbel werk
- **45+ regels** worden zowel geprompt als gevalideerd

**DEF-101 Blind Spot:** Gaat ervan uit dat validatieregels in prompt MOETEN blijven, focust op reducing redundancy binnen prompt.

**Nieuwe Analyse Inzicht:** Validatieregels kunnen VOLLEDIG uit prompt gehaald worden → -48% tokens!

---

### 4.2 CONDITIONAL MODULE LOADING

**Probleem:** Alle 16 modules draaien ALTIJD, zelfs modules die niet relevant zijn voor context.

**Impact:**
- **Juridische modules** draaien voor niet-juridische termen
- **Legal module** altijd actief
- **Performance overhead** van irrelevante modules

**DEF-101 Blind Spot:** Focus op reordering modules, niet op conditional execution.

**Nieuwe Analyse Inzicht:** Implementeer context-aware module filtering → alleen relevante modules.

---

### 4.3 STATIC MODULE CACHING

**Probleem:** Static modules (grammar, expertise) worden elke keer opnieuw gegeneerd.

**Nieuwe Analyse Oplossing:**
```python
@st.cache_data(ttl=3600)
def get_grammar_module_output():
    return GrammarModule().execute()
```

**DEF-101 Blind Spot:** Geen caching strategie voor static content.

---

### 4.4 TOKEN COUNT METRICS

**Nieuwe Analyse Insight:** Concrete token counts ontbreken in DEF-101.

| Metric | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) |
|--------|-------------------|---------------------------|
| **Total Tokens** | 419 lines (geen tokens) | **7.250 tokens** |
| **Validation Rules** | 45+ rules (geen tokens) | **3.500 tokens (48%)** |
| **Forbidden Patterns** | 42 bullets (geen tokens) | **750 tokens** |
| **ESS-02** | 38 lines (geen tokens) | Onderdeel van 3.500 tokens |

**Impact:** Nieuwe analyse heeft meetbare optimalisatie targets, DEF-101 heeft line counts.

---

## 5. GEÏNTEGREERD ACTIEPLAN

### FASE 1: QUICK WINS (Week 1, 4 uur) - COMBINEER BEIDE

#### DEF-101 Quick Wins:
1. ✅ **Resolve BLOCKING contradictions** (3 uur)
   - Add ESS-02 exception clause (DEF-101 strategy)
   - Exempt ontological markers from ARAI-02
   - Clarify relative clause usage

#### Nieuwe Analyse Quick Wins:
2. ✅ **Remove validation rules from prompt** (30 min) ⭐ HOOGSTE IMPACT
   - Delete 7 validation modules from prompt generation
   - Keep only summary: "✅ ARAI: Zelfstandig naamwoord, geen containerbegrippen"
   - **Impact:** -3.500 tokens (-48%)

3. ✅ **Consolidate forbidden list** (30 min)
   - Replace 42 bullets with 3 templates (Nieuwe Analyse strategy)
   - **Impact:** -750 tokens (-10%)

**Total Week 1: -4.250 tokens (-58%) + 0 conflicts**

---

### FASE 2: STRUCTURELE REFACTOR (Week 2, 8 uur) - COMBINEER BEIDE

#### DEF-101 Structural Changes:
1. ✅ **Reorder modules** (1 uur)
   - Metadata first (definition_task)
   - Ontological category #3 (semantic_categorisation)
   - Templates AFTER rules

#### Nieuwe Analyse Structural Changes:
2. ✅ **Implement Inverted Pyramid structure** (3 uur)
   - NIVEAU 1: MISSION (50 tokens)
   - NIVEAU 2: 3 GOLDEN RULES (300 tokens)
   - NIVEAU 3: TEMPLATES (400 tokens)
   - NIVEAU 4: REFINEMENT (800 tokens)
   - NIVEAU 5: CHECKLIST (100 tokens)

3. ✅ **Conditional module loading** (2 uur)
   ```python
   def _filter_modules(self, context):
       if not context.has_juridische_context:
           skip_modules.append("legal_module")
   ```

4. ✅ **Cache static modules** (1 uur)
   ```python
   @st.cache_data(ttl=3600)
   def get_grammar_module_output():
       return GrammarModule().execute()
   ```

5. ✅ **Add visual hierarchy** (1 uur) - DEF-101 3-Tier System
   - ⚠️ TIER 1 (ABSOLUTE)
   - ✅ TIER 2 (STRONG)
   - ℹ️ TIER 3 (POLISH)

**Total Week 2: Inverted Pyramid + Conditional Loading + Caching + Tiers**

---

### FASE 3: VALIDATIE & TESTING (Week 3, 4 uur) - DEF-101 STRATEGIE

#### DEF-101 Testing:
1. ✅ **Create PromptValidator** (2 uur)
   - `test_ess02_exception_clause_present()`
   - `test_no_blocking_contradictions()`
   - `test_redundancy_below_threshold()`
   - `test_forbidden_patterns_categorized()`

2. ✅ **Regression testing** (1 uur)
   - Use prompt-6 as golden reference
   - Compare key sections (ESS-02, ARAI)

3. ✅ **A/B test v7 vs v8** (1 uur)
   - Test with 50 begrippen (Nieuwe Analyse test set)
   - Measure quality + expert review

**Total Week 3: Comprehensive test coverage + A/B validation**

---

### FASE 4: DOCUMENTATION (Optional, 2 uur) - DEF-101 STRATEGIE

1. ✅ **Document module dependencies** (1 uur)
   - `docs/architectuur/prompt_module_dependency_map.md`

2. ✅ **Create ADR** (30 min)
   - ADR-XXX: Removal of Validation Rules from Prompt

3. ✅ **Update EPIC-016** (30 min)
   - Link prompt optimization to Beheer & Configuratie Console

---

## 6. EFFORT VERGELIJKING

| Fase | DEF-101 (prompt-6) | Nieuwe Analyse (prompt-7) | GEÏNTEGREERD |
|------|--------------------|---------------------------|--------------|
| **Week 1: Quick Wins** | 4 uur | 4 uur | **4 uur** |
| **Week 2: Structural** | 8 uur | 8 uur | **8 uur** |
| **Week 3: Testing** | 4 uur | 4 uur | **4 uur** |
| **Total** | **16 uur** | **16 uur** | **16 uur** |

**Consensus:** Beide analyses hebben identieke effort estimate (16 uur / 2 sprint weken).

---

## 7. SUCCESS METRICS VERGELIJKING

| Metric | DEF-101 Target | Nieuwe Analyse Target | GEÏNTEGREERD |
|--------|----------------|----------------------|--------------|
| **Usability** | UNUSABLE → USABLE | 4/10 → 8/10 | ✅ USABLE (0 blockers) |
| **Cognitive Load** | 9/10 → 4/10 | LLM Compliance 60% → 90% | **4/10 + 90% compliance** |
| **Redundancy** | 65% → <30% | 40% → <5% | **<5%** (agressiever) |
| **Flow Quality** | 4/10 → 8/10 | N/A | **8/10** |
| **File Size** | 419 → 354 lines (-15.5%) | N/A | **354 lines** |
| **Token Count** | N/A | 7.250 → 2.650 (-63%) | **2.650 tokens** |
| **Conflicts** | 5 → 0 | 10 → 0 | **0 conflicts** |

**Geïntegreerd Target:**
- ✅ **0 BLOCKING contradictions** (DEF-101 + Nieuwe Analyse)
- ✅ **2.650 tokens (-63%)** (Nieuwe Analyse target)
- ✅ **Cognitive Load 4/10** (DEF-101 target)
- ✅ **Flow 8/10** (DEF-101 target)
- ✅ **<5% redundancy** (Nieuwe Analyse target)

---

## 8. PRIORITEITEN & TRADE-OFFS

### 8.1 CONFLICT RESOLUTIE vs TOKEN REDUCTION

**Trade-off:**
- **DEF-101 aanpak:** Voeg exception clauses toe → meer tokens, maar veiliger
- **Nieuwe Analyse:** Verwijder validatieregels volledig → minder tokens, maar risico

**Aanbeveling:** **COMBINEER**
1. **Week 1:** Voeg exception clauses toe (DEF-101) → 0 conflicts
2. **Week 2:** Verwijder validatieregels (Nieuwe Analyse) → -3.500 tokens
3. **Week 3:** Test beide aanpakken → A/B validation

**Rationale:** Eerst conflicts fixen (veiligheid), dan token reduction (optimalisatie).

---

### 8.2 INCREMENTAL vs AGGRESSIVE REDUCTION

**Trade-off:**
- **DEF-101:** Incrementele reductie (65% → <30%) → veiliger
- **Nieuwe Analyse:** Aggressive reductie (40% → <5%) → risicovol

**Aanbeveling:** **GEFASEERD**
- **Fase 1 (Week 1):** Quick wins (DEF-101 + Nieuwe Analyse) → -58% tokens
- **Fase 2 (Week 2):** Structural refactor → Inverted Pyramid + Conditional Loading
- **Fase 3 (Week 3):** A/B test → Meet impact op definitie kwaliteit

**Rationale:** Start met quick wins (hoogste ROI), test impact, dan verdere optimalisatie.

---

### 8.3 MODULE REORDERING vs INVERTED PYRAMID

**Trade-off:**
- **DEF-101:** Reorder bestaande modules → backward compatible
- **Nieuwe Analyse:** Nieuwe Inverted Pyramid structuur → breaking change

**Aanbeveling:** **HYBRIDE**
1. **Week 2 Day 1:** Implementeer Inverted Pyramid structuur (Nieuwe Analyse)
2. **Week 2 Day 2:** Reorder modules binnen Pyramid levels (DEF-101)
3. **Week 3:** A/B test beide structuren

**Rationale:** Nieuwe structuur is innovatiever, maar DEF-101 module ordering binnen levels toevoegen.

---

### 8.4 VALIDATION RULES: IN PROMPT vs POST-ONLY

**Trade-off:**
- **DEF-101 assumptie:** Validatieregels blijven in prompt, reduce redundancy
- **Nieuwe Analyse:** Validatieregels VOLLEDIG uit prompt → -48% tokens

**Aanbeveling:** **NIEUWE ANALYSE STRATEGIE**

**Rationale:**
1. **Validatieregels worden toch gevalideerd** in post-processing (ModularValidationService)
2. **LLM compliance ~60%** betekent dat LLM regels vaak negeert anyway
3. **Post-validation is authoritative** - prompt guidance is redundant
4. **3.500 tokens (-48%)** is grootste optimalisatie kans

**Implementatie:**
```python
# VOOR: Volledige regel in prompt (7 modules)
AraiRulesModule → ARAI-01 t/m ARAI-06 (detailed)

# NA: Alleen kernprincipes
"✅ Algemene Regels: Begin met zelfstandig naamwoord, essentie niet doel"
```

**Test strategie:**
- Week 1: Implementeer summary-only validation rules
- Week 3: A/B test prompt-6 (full rules) vs prompt-8 (summary only)
- Metric: Validatie success rate (moet ≥90% blijven)

---

## 9. KRITIEKE BESLISSINGEN

### BESLISSING 1: Validatieregels Strategie ⭐ MEEST KRITIEK

**Vraag:** Houden we validatieregels in prompt of alleen in post-processing?

| Optie | Voordelen | Nadelen | Impact |
|-------|-----------|---------|--------|
| **A. Keep in prompt (DEF-101 assumptie)** | Veiliger, LLM heeft guidance | 3.500 tokens redundant, LLM compliance ~60% | Reduce redundancy 65% → 30% |
| **B. Remove from prompt (Nieuwe Analyse)** | -48% tokens, focus op core principles | Risico: LLM maakt meer fouten, post-validation moet alles opvangen | -3.500 tokens (-48%) |
| **C. Summary only (HYBRIDE)** | Balance: high-level guidance + token reduction | Moet juiste balance vinden | -2.500 tokens (-34%) |

**AANBEVELING:** **OPTIE B - Remove from prompt** ⭐

**Rationale:**
1. Post-validation is authoritative anyway (ModularValidationService)
2. LLM compliance ~60% betekent guidance vaak genegeerd wordt
3. Focus prompt op core principles (3 GOLDEN RULES) + templates
4. Test met A/B: meet impact op validatie success rate

**Implementatie Week 1:**
- Delete 7 validation modules from prompt generation
- Keep only: "✅ ALGEMENE REGELS: Zelfstandig naamwoord, essentie niet doel, ontologische categorie expliciet"
- Test: 50 begrippen, compare success rate prompt-6 vs prompt-8

**Success Criteria:**
- Validatie success rate ≥90% (target: geen impact vs prompt-6)
- Generatie tijd < 3 seconden (target: 25% sneller)
- Expert score > 8/10 (target: kwaliteit behouden)

---

### BESLISSING 2: Prompt Structuur

**Vraag:** Linear reordering (DEF-101) of Inverted Pyramid (Nieuwe Analyse)?

**AANBEVELING:** **Inverted Pyramid** met DEF-101 module ordering binnen levels

**Implementatie:**
```
NIVEAU 1: TASK & CONTEXT (50 tokens)
├── definition_task module (DEF-101 #1)
│
NIVEAU 2: CRITICAL REQUIREMENTS (300 tokens)
├── expertise module (DEF-101 #2)
├── semantic_categorisation module (DEF-101 #3) ← MOST CRITICAL
├── output_specification module (DEF-101 #4)
│
NIVEAU 3: TEMPLATES (400 tokens)
├── template module (DEF-101 #8)
│
NIVEAU 4: REFINEMENT (800 tokens)
├── grammar module (DEF-101 #5)
├── context_awareness module (DEF-101 #6)
├── structure_rules module (DEF-101 #7)
│
NIVEAU 5: VALIDATION CHECKLIST (100 tokens)
├── Final checklist (DEF-101 checklist items)
```

**Rationale:** Nieuwe structuur is innovatiever EN incorporeert DEF-101 best practices.

---

### BESLISSING 3: Quick Wins Prioriteit

**Vraag:** Start met conflicts (DEF-101) of token reduction (Nieuwe Analyse)?

**AANBEVELING:** **HYBRIDE - Beide parallel**

**Week 1 Day 1 (3 uur):**
1. Resolve BLOCKING contradictions (DEF-101) → 0 conflicts
2. Remove validation rules from prompt (Nieuwe Analyse) → -3.500 tokens

**Week 1 Day 2 (1 uur):**
3. Consolidate forbidden list (Nieuwe Analyse) → -750 tokens

**Rationale:** Conflicten EN token reduction zijn beide quick wins, geen dependency.

---

## 10. IMPLEMENTATIE ROADMAP - GEÏNTEGREERD

### WEEK 1: QUICK WINS (4 uur)

#### Day 1 (3 uur)
**09:00-10:30 | CONFLICTS (DEF-101 strategy)**
- ✅ Add ESS-02 exception clause in `error_prevention_module.py` (30 min)
- ✅ Exempt ontological markers from ARAI-02 (30 min)
- ✅ Clarify relative clause usage (30 min)

**10:30-12:00 | TOKEN REDUCTION (Nieuwe Analyse strategy)** ⭐
- ✅ Remove validation rules from prompt (90 min)
  - Delete 7 validation rule modules from prompt generation
  - Keep summary: "✅ ALGEMENE REGELS: ..."
  - **Impact: -3.500 tokens (-48%)**

#### Day 2 (1 uur)
**09:00-10:00 | FORBIDDEN PATTERNS (Nieuwe Analyse strategy)**
- ✅ Replace 42 bullets with 3 templates (1 uur)
  - **Impact: -750 tokens (-10%)**

**Week 1 Results:**
- ✅ **0 BLOCKING contradictions** (DEF-101 success)
- ✅ **-4.250 tokens (-58%)** (Nieuwe Analyse success)
- ✅ **Test:** Run 20 begrippen, verify validatie success rate ≥90%

---

### WEEK 2: STRUCTURAL REFACTOR (8 uur)

#### Day 1 (4 uur)
**09:00-12:00 | INVERTED PYRAMID (Nieuwe Analyse strategy)**
- ✅ Implement 5-level structure (3 uur)
  - NIVEAU 1: TASK & CONTEXT (50 tokens)
  - NIVEAU 2: CRITICAL REQUIREMENTS (300 tokens)
  - NIVEAU 3: TEMPLATES (400 tokens)
  - NIVEAU 4: REFINEMENT (800 tokens)
  - NIVEAU 5: CHECKLIST (100 tokens)

**13:00-14:00 | MODULE REORDERING (DEF-101 strategy)**
- ✅ Reorder modules within Pyramid levels (1 uur)
  - Use DEF-101 optimal_modules order

#### Day 2 (4 uur)
**09:00-11:00 | CONDITIONAL LOADING (Nieuwe Analyse strategy)**
- ✅ Implement context-aware module filtering (2 uur)
  ```python
  def _filter_modules(self, context):
      if not context.has_juridische_context:
          skip_modules.append("legal_module")
  ```

**11:00-12:00 | STATIC CACHING (Nieuwe Analyse strategy)**
- ✅ Cache static modules (1 uur)
  ```python
  @st.cache_data(ttl=3600)
  def get_grammar_module_output():
      return GrammarModule().execute()
  ```

**13:00-14:00 | VISUAL HIERARCHY (DEF-101 strategy)**
- ✅ Add 3-Tier badges (1 uur)
  - ⚠️ TIER 1 (ABSOLUTE)
  - ✅ TIER 2 (STRONG)
  - ℹ️ TIER 3 (POLISH)

**Week 2 Results:**
- ✅ **Inverted Pyramid structure** (Nieuwe Analyse)
- ✅ **Conditional module loading** (Nieuwe Analyse)
- ✅ **Static module caching** (Nieuwe Analyse)
- ✅ **Visual hierarchy** (DEF-101)

---

### WEEK 3: VALIDATIE & TESTING (4 uur)

#### Day 1 (2 uur)
**09:00-11:00 | PROMPTVALIDATOR (DEF-101 strategy)**
- ✅ Create `src/services/prompts/prompt_validator.py` (2 uur)
  - `test_ess02_exception_clause_present()`
  - `test_no_blocking_contradictions()`
  - `test_redundancy_below_threshold()`
  - `test_forbidden_patterns_categorized()`

#### Day 2 (2 uur)
**09:00-10:00 | REGRESSION TESTING (DEF-101 strategy)**
- ✅ Use prompt-6 as golden reference (1 uur)
  - Compare key sections (ESS-02, ARAI)
  - Check no contradictions introduced

**10:00-11:00 | A/B TESTING (Nieuwe Analyse strategy)**
- ✅ Test prompt-6 vs prompt-8 with 50 begrippen (1 uur)
  - Measure: validatie success rate, generatie tijd, expert score
  - Target: success rate ≥90%, generatie tijd <3s, expert score >8/10

**Week 3 Results:**
- ✅ **Comprehensive test coverage** (DEF-101)
- ✅ **A/B validation** (Nieuwe Analyse)
- ✅ **Metrics:** 0 conflicts, 2.650 tokens (-63%), success rate ≥90%

---

## 11. FILES TO MODIFY - GEÏNTEGREERD

### Week 1 Files (Quick Wins):

**Conflict Resolution (DEF-101):**
- `src/services/prompts/modules/error_prevention_module.py` - Add ESS-02 exception
- `src/services/prompts/modules/arai_rules_module.py` - Exempt ontological markers
- `src/services/prompts/modules/structure_rules_module.py` - Clarify relative clauses

**Token Reduction (Nieuwe Analyse):**
- `src/services/prompts/modules/arai_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/con_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/ess_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/int_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/sam_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/str_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/ver_rules_module.py` - DELETE (replace with summary)
- `src/services/prompts/modules/error_prevention_module.py` - Consolidate forbidden patterns

### Week 2 Files (Structural):

**Inverted Pyramid (Nieuwe Analyse):**
- `src/services/prompts/prompt_orchestrator.py` - Implement 5-level structure
- `src/services/prompts/modules/definition_task_module.py` - NIVEAU 1
- `src/services/prompts/modules/expertise_module.py` - NIVEAU 2
- `src/services/prompts/modules/semantic_categorisation_module.py` - NIVEAU 2
- `src/services/prompts/modules/template_module.py` - NIVEAU 3

**Conditional Loading (Nieuwe Analyse):**
- `src/services/prompts/prompt_orchestrator.py` - Add `_filter_modules()` method

**Caching (Nieuwe Analyse):**
- `src/services/prompts/modules/grammar_module.py` - Add `@st.cache_data`
- `src/services/prompts/modules/expertise_module.py` - Add `@st.cache_data`

**Visual Hierarchy (DEF-101):**
- `src/services/prompts/modules/structure_rules_module.py` - Add ⚠️/✅/ℹ️ badges
- `src/services/prompts/modules/integrity_rules_module.py` - Add badges

### Week 3 Files (Testing):

**Testing (DEF-101):**
- `src/services/prompts/prompt_validator.py` - **NEW FILE**
- `tests/services/prompts/test_prompt_contradictions.py` - **NEW FILE**
- `tests/services/prompts/test_prompt_v6_vs_v8_ab.py` - **NEW FILE** (Nieuwe Analyse)

---

## 12. SUCCESS CRITERIA - GEÏNTEGREERD

### Week 1 Success Criteria:
- ✅ **0 BLOCKING contradictions** (DEF-101 automated validator)
- ✅ **-4.250 tokens (-58%)** (Nieuwe Analyse token count)
- ✅ **Validatie success rate ≥90%** (test with 20 begrippen)
- ✅ **Geen regressie** in definitie kwaliteit (expert review)

### Week 2 Success Criteria:
- ✅ **Inverted Pyramid implemented** (5 levels, 2.650 tokens total)
- ✅ **Conditional loading works** (only relevant modules active)
- ✅ **Static caching works** (grammar module cached, TTL 3600s)
- ✅ **Visual hierarchy clear** (TIER badges on all rules)

### Week 3 Success Criteria:
- ✅ **All tests pass** (PromptValidator, contradiction tests, A/B tests)
- ✅ **Regression tests pass** (vs prompt-6 golden reference)
- ✅ **A/B validation:** prompt-8 ≥ prompt-6 quality
- ✅ **Metrics achieved:**
  - Conflicts: 0
  - Tokens: 2.650 (-63%)
  - Cognitive Load: 4/10
  - Flow: 8/10
  - Redundancy: <5%
  - Validatie success rate: ≥90%
  - Generatie tijd: <3s
  - Expert score: >8/10

---

## 13. RISK MITIGATION - GEÏNTEGREERD

### RISK 1: Validatieregels Removal Breaks Quality

**Probability:** MEDIUM
**Impact:** HIGH
**Mitigation (DEF-101 + Nieuwe Analyse):**
1. A/B test prompt-6 vs prompt-8 with 50 begrippen (Week 3)
2. Rollback plan: Feature flag `USE_LEGACY_PROMPT=true` (DEF-101 strategy)
3. Gradual rollout: 10% traffic → 50% → 100% (DEF-101 strategy)
4. Monitoring: Track validatie success rate dashboard (Nieuwe Analyse metric)

### RISK 2: Module Reordering Breaks Dependencies

**Probability:** LOW
**Impact:** MEDIUM
**Mitigation (DEF-101):**
1. Document module dependencies (Week 3, `prompt_module_dependency_map.md`)
2. Dependency graph validation in `prompt_orchestrator.py`
3. Integration tests for module execution order

### RISK 3: Conditional Loading Skips Critical Modules

**Probability:** LOW
**Impact:** HIGH
**Mitigation (Nieuwe Analyse):**
1. Whitelist CRITICAL modules (never skip): expertise, semantic_categorisation, output_specification
2. Unit tests for `_filter_modules()` logic
3. Logging: track which modules skipped per request

### RISK 4: Inverted Pyramid Confuses LLM

**Probability:** MEDIUM
**Impact:** MEDIUM
**Mitigation (Nieuwe Analyse + DEF-101):**
1. A/B test linear (DEF-101) vs pyramid (Nieuwe Analyse) structure
2. LLM compliance measurement (% rules followed)
3. Fallback: Use DEF-101 linear restructure if pyramid fails

---

## 14. ROLLBACK PLAN - DEF-101 STRATEGIE

### Immediate Rollback (< 5 min):
```bash
# Rollback laatste commit
git revert <commit-hash>
git push
```

### Feature Flag Rollback:
```python
# In prompt_orchestrator.py
USE_LEGACY_PROMPT = os.getenv("USE_LEGACY_PROMPT", "false") == "true"

if USE_LEGACY_PROMPT:
    return read_file("prompts/legacy/_Definitie_Generatie_prompt-6.txt")
```

### Gradual Rollback (A/B Testing):
```python
# 10% traffic to prompt-8, 90% to prompt-6
import random
if random.random() < 0.10:
    use_prompt_v8()
else:
    use_prompt_v6()
```

---

## 15. DOCUMENTATION UPDATES

### New Documentation (Week 3):
1. **`docs/architectuur/prompt_module_dependency_map.md`** (DEF-101)
2. **`docs/analyses/PROMPT_ANALYSIS_CONSENSUS_REPORT.md`** (THIS FILE)
3. **`docs/adr/ADR-XXX-remove-validation-rules-from-prompt.md`** (Nieuwe Analyse)

### Update Documentation:
1. **`README.md`** - Prompt optimization section
2. **`CLAUDE.md`** - Prompt modules section
3. **`docs/backlog/EPIC-016/EPIC-016.md`** - Link to prompt optimization

---

## 16. NEXT STEPS (IMMEDIATE)

### 🔴 VANDAAG (30 min):
1. ✅ Review this consensus report
2. ⬜ **BESLISSING:** Approve Optie B (Remove validation rules from prompt)
3. ⬜ **BESLISSING:** Approve Inverted Pyramid structure (Nieuwe Analyse)
4. ⬜ Create GitHub issue: "DEF-101: Prompt Optimization - Integrated Plan"

### 🟡 WEEK 1 (4 uur):
1. ⬜ Implement Quick Wins (Day 1: conflicts + token reduction, Day 2: forbidden patterns)
2. ⬜ Test with 20 begrippen
3. ⬜ Measure: tokens, conflicts, validatie success rate

### 🟢 WEEK 2-3 (12 uur):
1. ⬜ Implement Inverted Pyramid + Conditional Loading + Caching + Visual Hierarchy
2. ⬜ Create PromptValidator + test suite
3. ⬜ A/B test prompt-6 vs prompt-8 with 50 begrippen
4. ⬜ Deploy to production (gradual rollout)

---

## 17. CONCLUSIE

### Consensus:
- ✅ **Beide analyses identificeren DEZELFDE kernproblemen:**
  - 5 BLOCKING contradictions (DEF-101) / 10 kritieke conflicten (Nieuwe Analyse)
  - ~65% redundantie (DEF-101) / 40% redundantie (Nieuwe Analyse)
  - Severe cognitive overload (9/10 → 4/10)
  - Poor flow (4/10 → 8/10)

### Unieke Inzichten:
- ✅ **DEF-101 (prompt-6):**
  - Completere conflict resolutie strategie (exception clauses, 3-Tier system)
  - Concrete module reordering plan
  - Comprehensive test suite + rollback plan

- ✅ **Nieuwe Analyse (prompt-7):**
  - **GROOTSTE INZICHT:** Dubbel gebruik validatieregels (-3.500 tokens = -48%)
  - Conditional module loading + static caching
  - Inverted Pyramid structure (innovatiever dan linear restructure)
  - Aggressive token reduction target (7.250 → 2.650 = -63%)

### Beste Aanpak:
**GEÏNTEGREERD PLAN - Combineer beste van beide:**
1. **Week 1 Quick Wins:** DEF-101 conflict resolution + Nieuwe Analyse token reduction
2. **Week 2 Structural:** Nieuwe Analyse Inverted Pyramid + DEF-101 module ordering binnen levels
3. **Week 3 Testing:** DEF-101 test suite + Nieuwe Analyse A/B validation

### Expected Results:
- ✅ **0 BLOCKING contradictions** (DEF-101 success)
- ✅ **2.650 tokens (-63%)** (Nieuwe Analyse success)
- ✅ **Cognitive Load 4/10** (DEF-101 success)
- ✅ **Flow 8/10** (DEF-101 success)
- ✅ **<5% redundancy** (Nieuwe Analyse success)
- ✅ **Validatie success rate ≥90%** (beide analyses success)

### Total Effort:
**16 uur (2 sprint weken)** - Identiek aan beide analyses

---

**STATUS:** ✅ CONSENSUS BEREIKT
**AANBEVELING:** Approve geïntegreerd plan en start Week 1 Quick Wins
**NEXT ACTION:** Review met stakeholder + create GitHub issue DEF-101

---

**Document Metadata:**
- **Created:** 2025-11-07
- **Authors:** Consensus van DEF-101 (prompt-6) + Nieuwe Analyse (prompt-7)
- **Review Status:** Pending approval
- **Related Documents:**
  - `docs/analyses/PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md` (DEF-101)
  - `docs/analyses/PROMPT_OPTIMIZATION_ANALYSIS.md` (Nieuwe Analyse)
- **Related Issues:** DEF-101 (Linear), EPIC-016 (Beheer Console)
