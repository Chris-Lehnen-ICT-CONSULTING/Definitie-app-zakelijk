# Business Knowledge Extraction Document
## US-061: Legacy Code Business Logic Documentation

Dit document bevat alle geëxtraheerde business kennis uit de legacy code van het DefinitieAgent systeem. Deze kennis is kritiek voor het behoud van functionaliteit tijdens refactoring.

---

## 1. FEEDBACKBUILDER ALGORITMES

### 1.1 Feedback Prioritering Algoritme

**Locatie:** `src/orchestration/definitie_agent.py:299-544`

#### Business Logica:
1. **Kritieke Violations Eerst** (regel 321-328)
   - Maximaal 3 kritieke issues tegelijk presenteren
   - Voorkomt overwhelming van AI model
   - Focus op meest impactvolle problemen eerst

2. **Violation Groepering** (regel 329-337)
   - Groepeer violations per type voor efficiënte behandeling
   - Voorkomt duplicate feedback voor vergelijkbare problemen
   - Maakt feedback meer actionable

3. **Iteratie-Bewuste Feedback** (regel 437-444)
   - Eerste iteratie: directe instructies ("Vermijd deze patronen")
   - Latere iteraties: alternatieve suggesties ("Nog steeds aanwezig... probeer alternatieve formuleringen")
   - Voorkomt stagnatie door variatie in aanpak

4. **Lerende Feedback** (regel 469-496)
   - Detecteert stagnatie: scores die niet verbeteren
   - Detecteert regressie: huidige score < vorige score
   - Suggereert fundamentele herformulering bij stagnatie
   - Threshold: 0.05 score verschil voor stagnatie detectie

5. **Feedback Prioritering** (regel 511-544)
   - Volgorde: 🚨 Kritiek → 💡 Suggesties → Overig
   - Maximum 5 feedback items per iteratie
   - Deduplicatie van feedback items
   - Behoud van meest actionable feedback

### 1.2 Violation-to-Feedback Mapping

**Business Rules:**
```python
violation_feedback_mapping = {
    "CON-01": "Context-specifiek zonder expliciete vermelding",
    "CON-02": "Baseer op authentieke bronnen",
    "ESS-01": "Beschrijf WAT het is, niet waarvoor",
    "ESS-02": "Maak type/proces/resultaat expliciet",
    "ESS-03": "Voeg unieke identificerende kenmerken toe",
    "ESS-04": "Gebruik objectief meetbare criteria",
    "ESS-05": "Benadruk onderscheidende eigenschappen",
    "INT-01": "Formuleer als één zin zonder opsommingen",
    "INT-03": "Vervang onduidelijke verwijzingen",
    "STR-01": "Start met centraal zelfstandig naamwoord",
    "STR-02": "Gebruik concrete, specifieke terminologie"
}
```

---

## 2. STATUS BEPALING REGELS

### 2.1 Definitie Acceptatie Criteria

**Locatie:** `src/validation/definitie_validator.py:666-687`

#### Drie-Staps Acceptatie Logica:

1. **Critical Violations Check**
   - GEEN kritieke violations toegestaan
   - Direct reject als critical > 0
   - Business reden: Kritieke regels zijn juridisch verplicht

2. **Overall Score Check**
   - Minimum score: 0.8 (80%)
   - Weighted average van alle regel scores
   - Weging op basis van prioriteit × aanbeveling

3. **Category Compliance Check**
   - Minimum: 0.75 (75%) voor categorie-specifieke regels
   - Lager dan overall omdat categorie-specifiek
   - Zorgt voor flexibiliteit bij cross-categorie begrippen

### 2.2 Score Berekening Algoritme

**Locatie:** `src/validation/definitie_validator.py:635-654`

#### Weighted Scoring:
```
Score = Σ(regel_score × regel_weight) / Σ(regel_weight)

Waarbij:
- regel_weight = base_weight × requirement_multiplier
- base_weight: hoog=1.0, midden=0.7, laag=0.4
- requirement_multiplier: verplicht=1.5, aanbevolen=1.0, optioneel=0.8
```

#### Score Penalties:
- Forbidden pattern: -0.3 × count × severity_multiplier
- Missing element: -0.4 × severity_multiplier
- Structure issue: -0.25 × severity_multiplier

#### Severity Multipliers:
- CRITICAL: 2.0
- HIGH: 1.5
- MEDIUM: 1.0
- LOW: 0.5

---

## 3. ITERATIVE IMPROVEMENT LOGICA

### 3.1 Iteratie Control Flow

**Locatie:** `src/orchestration/definitie_agent.py:644-683`

#### Business Rules:

1. **Maximum Iteraties:** 3 (configureerbaar)
   - Balans tussen kwaliteit en performance
   - Voorkomt infinite loops
   - Genoeg voor meeste verbeteringen

2. **Improvement Threshold:** 0.05
   - Minimum verbetering per iteratie
   - Voorkomt nutteloze iteraties
   - Detecteert stagnatie

3. **Best Iteration Tracking**
   - Houdt beste score bij over alle iteraties
   - Gebruikt beste resultaat als finale output
   - Voorkomt regressie in finale resultaat

4. **Voorbeelden Optimalisatie** (regel 739-758)
   - Genereer voorbeelden alleen in eerste iteratie
   - Hergebruik voorbeelden in volgende iteraties
   - Bespaart ~2-3 seconden per iteratie
   - Voorbeelden blijven consistent

### 3.2 Feedback History Management

**Locatie:** `src/orchestration/definitie_agent.py:869-883`

#### Business Logic:
- Maximum 10 feedback items in history
- FIFO: oudste feedback wordt verwijderd
- Voorkomt prompt bloat
- Houdt focus op recente issues

---

## 4. ENHANCEMENT STRATEGIEËN

### 4.1 Clarity Enhancement

**Locatie:** `src/services/definition_generator_enhancement.py:81-185`

#### Vagueness Detection:
```python
unclear_patterns = [
    "enigszins|soms|wellicht|mogelijk|misschien",  # Vague terms
    "enzovoort|etc|enz",                           # Non-specific endings
    "diverse|verschillende|meerdere",              # Vague quantities
    "dergelijke|soortgelijke"                      # Vague references
]

vagueness_score = matches / words × 10 (max 1.0)
Threshold: > 0.3 voor enhancement
```

#### Circular Reasoning Detection:
- Check: begrip komt >1 keer voor in definitie
- Fix: vervang 2e+ occurrence met "dit"
- Voorkomt tautologieën

### 4.2 Context Integration

**Locatie:** `src/services/definition_generator_enhancement.py:188-231`

#### Business Rules:
- Domein field verwijderd (EPIC-010/US-043)
- Context alleen toevoegen als niet al aanwezig
- Format: "... (binnen de context van X, Y)"
- Alleen relevante context delen (>2 karakters)

### 4.3 Completeness Enhancement

**Locatie:** `src/services/definition_generator_enhancement.py:234-296`

#### Missing Aspects Detection:
```python
completeness_aspects = {
    "doel": ["doel", "bedoeling", "functie", "nut"],
    "scope": ["omvang", "bereik", "toepassingsgebied"],
    "voorwaarden": ["voorwaarde", "vereiste", "criteria"],
    "proces": ["stap", "procedure", "methode", "proces"],
    "verantwoordelijk": ["verantwoordelijk", "bevoegd", "eigenaar"]
}
```

**Trigger:** ≥2 missing aspects
**Action:** Voeg generieke completeness hints toe

### 4.4 Linguistic Enhancement

**Locatie:** `src/services/definition_generator_enhancement.py:299-364`

#### Improvements:
1. **Passive to Active:** "wordt X" → "X wordt"
2. **Redundancy Removal:** Detecteer word repetition
3. **Formality:** "je/jij/wij" → "men"
4. **Begrip Simplification:** "het begrip X" → "X"

---

## 5. PERFORMANCE OPTIMALISATIES

### 5.1 Voorbeelden Caching

**Business Logic:**
- Genereer voorbeelden alleen in iteratie 1
- Store in `_first_iteration_voorbeelden`
- Reuse in iteraties 2-3
- Besparing: ~2-3 sec per iteratie

### 5.2 Enhancement Confidence Threshold

**Locatie:** `src/services/definition_generator_enhancement.py:433`

- Default threshold: 0.6
- Alleen enhancements met confidence ≥ threshold
- Maximum 3 enhancements per definitie
- Sorteer op confidence, pas hoogste toe eerst

### 5.3 Feedback Limiting

**Business Rules:**
- Max 5 feedback items per iteratie

