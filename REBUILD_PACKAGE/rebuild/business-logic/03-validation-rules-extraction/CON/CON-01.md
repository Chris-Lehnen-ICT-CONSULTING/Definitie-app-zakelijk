# CON-01: Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming

## Metadata
- **ID:** CON-01
- **Category:** CON
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/CON-01.py`
- **Class Name:** `CON01Validator`
- **Lines of Code:** 214

## Business Purpose

### What
Formuleer de definitie zó dat deze past binnen de opgegeven context(en), zonder deze expliciet te benoemen in de definitie zelf. Bij de generatiestap wordt tevens een duplicate‑controle toegepast op begrip én synoniemen: als er al een definitie met gelijke context bestaat (organisatorisch, juridisch en wettelijke basis), verschijnt een duplicate‑gate met uitleg.

### Why
Een definitie moet afgestemd zijn op de organisatorische, juridische en/of wettelijke context die via invoervelden door de gebruiker is opgegeven. Deze context mag niet letterlijk in de definitie worden herhaald of benoemd. De contextuele betekenis moet impliciet doorklinken in de formulering. Tijdens de definitie‑generatie vindt een duplicate‑controle plaats op zowel het begrip als de opgegeven synoniemen (case‑insensitief). Wanneer met identieke context (organisatorisch, juridisch en wettelijke basis; wettelijke basis is orde‑onafhankelijk) al een definitie bestaat, wordt dit gemeld met een duidelijke toelichting (bijv. ‘Gevonden via synoniem … met gelijke context’), zodat je bewust kunt kiezen voor hergebruik of nieuwe generatie.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from CON01Validator)
def validate(definitie: str, begrip: str, context: dict | None = None) -> tuple[bool, str, float]:
    # 1. Extract patterns from config
    # 2. Match patterns against definition
    # 3. Check good/bad examples
    # 4. Return (success, message, score)
    pass
```

**Key Steps:**
1. Load recognizable patterns from JSON config
2. Use regex matching to find violations
3. Compare with good/bad examples
4. Calculate score: 1.0 (pass), 0.5 (warning), 0.0 (fail)

### Patterns
```python
# Regex patterns used for detection
herkenbaar_patronen = [
    r"\b(in de context van)\b",
    r"\b(in het kader van)\b",
    r"\bbinnen de context\b",
    r"\bvolgens de .*context\b",
    r"\bjuridisch(e)?\b",
    r"\bbeleidsmatig(e)?\b",
    r"\boperationeel\b",
    r"\btechnisch(e)?\b",
    r"\bcontext\b",
    r"\bin juridische context\b",
    r"\bin operationele context\b",
    r"\bin technische context\b",
    r"\bin beleidsmatige context\b",
    r"\b(Dienst Justiti[eë]le Inrichtingen|DJI|Openbaar Ministerie|OM|ZM|KMAR)\b",
    r"\bstrafrecht\b",
    r"\bbestuursrecht\b",
    r"\bciviel recht\b",
    r"\binternationaal recht\b",
    r"\bvolgens het Wetboek van (Strafvordering|Strafrecht|Bestuursrecht)\b",
    r"\bop grond van de (wet|regelgeving|bepaling)\b",
    r"\bmet basis in de (wet|regeling)\b",
    r"\bwettelijke grondslag\b",
    r"\bzoals toegepast binnen\b",
]
```

### Thresholds
| Threshold | Value | Usage | Notes |
|-----------|-------|-------|-------|
| Pass score | 1.0 | Perfect validation | No violations found |
| Warning score | 0.5 | Partial pass | Minor issues detected |
| Fail score | 0.0 | Validation failed | Violations found |

### Error Messages
- **Pass:** "✔️ {rule_id}: [validation passed message]"
- **Warning:** "🟡 {rule_id}: [warning message with details]"
- **Fail:** "❌ {rule_id}: [failure message with found violations]"

## Test Cases

### Good Examples (Should PASS)
1. "Toezicht is het systematisch volgen van handelingen om te beoordelen of ze voldoen aan vastgestelde normen."
2. "Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem."
3. "Een maatregel is een opgelegde beperking of correctie bij vastgestelde overtredingen."

### Bad Examples (Should FAIL)
1. "Toezicht is controle uitgevoerd door DJI in juridische context, op basis van het Wetboek van Strafvordering."
2. "Registratie: het vastleggen van persoonsgegevens binnen de organisatie DJI, in strafrechtelijke context."
3. "Een maatregel is, binnen de context van het strafrecht, een corrigerende sanctie."

### Edge Cases
- Empty definition
- Very short definition (< 10 characters)
- Very long definition (> 500 characters)
- Special characters and unicode
- Multiple pattern matches

## Dependencies
**Imports:**
- `logging`
- `typing`

**Called by:**
- ModularValidationService
- ValidationOrchestratorV2

## ASTRA References
- **Guideline:** Eigen definitie voor elke context
- **URL:** [https://www.astraonline.nl/index.php/Eigen_definitie_voor_elke_context](https://www.astraonline.nl/index.php/Eigen_definitie_voor_elke_context)

**Compliance requirement:** verplicht

## Notes
- **Type:** context
- **Theme:** contextgevoeligheid
- **Test Question:** Is de betekenis van het begrip contextspecifiek geformuleerd, zonder dat de context letterlijk of verwijzend in de definitie wordt genoemd?

## Extraction Date
2025-10-02
