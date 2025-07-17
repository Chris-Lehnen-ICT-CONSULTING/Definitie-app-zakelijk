# Analyse: Bestaande Validatie Componenten

## Wat bestaat er AL?

### 1. **DefinitieValidator** (`src/validation/definitie_validator.py`)
✅ **COMPLEET** - Een volledig uitgewerkte validator klasse met:
- `ValidationResult` dataclass met scores, violations, suggestions
- `RuleViolation` dataclass voor specifieke overtredingen
- `ViolationSeverity` enum (CRITICAL, HIGH, MEDIUM, LOW)
- `ViolationType` enum (FORBIDDEN_PATTERN, MISSING_ELEMENT, etc.)
- `ValidationRegelInterpreter` voor het interpreteren van toetsregels
- Volledige implementatie van validatie logica
- Score berekening en acceptance criteria

**Key features:**
```python
validator = DefinitieValidator()
result = validator.validate(
    definitie="...",
    categorie=OntologischeCategorie.PROCES,
    context={"organisatie": "DJI"}
)
# result bevat: overall_score, violations, improvement_suggestions, etc.
```

### 2. **ModularToetser** (`src/ai_toetser/modular_toetser.py`)
✅ **BESTAAT** - Huidige validator orchestrator met:
- Registry pattern voor validators
- Backward compatibility met legacy output (List[str])
- 16 validators geïmplementeerd (CON, ESS, STR categorieën)

### 3. **Validators** (`src/ai_toetser/validators/`)
✅ **GEDEELTELIJK** - Geïmplementeerde validators:
- ✅ CON-01, CON-02 (content_rules.py)
- ✅ ESS-01 t/m ESS-05 (essential_rules.py)
- ✅ STR-01 t/m STR-09 (structure_rules.py)
- ❌ INT-01 t/m INT-08 (ONTBREEKT)
- ❌ SAM-01 t/m SAM-08 (ONTBREEKT)
- ❌ VER-01 t/m VER-05 (ONTBREEKT)
- ❌ ARAI01 t/m ARAI06 (ONTBREEKT)

### 4. **Andere Validation Componenten**
✅ **input_validator.py** - Input sanitization
✅ **dutch_text_validator.py** - Nederlandse taal validatie
✅ **sanitizer.py** - Security sanitization

## Wat MIST er nog?

### 1. **UI Componenten**
❌ **Geen aparte validation UI component**
- Validatie resultaten worden inline getoond in definition_generator_tab
- Geen dedicated validation panel/tab
- Geen standalone "Valideer Definitie" functionaliteit

### 2. **Service Layer Scheiding**
❌ **Geen onafhankelijke ValidationService**
- Validatie is gekoppeld aan generatie in UnifiedDefinitionService
- Geen aparte API/endpoint voor validatie

### 3. **Ontbrekende Validators**
❌ **30 van de 46 validators ontbreken**:
- INT categorie (8 regels)
- SAM categorie (8 regels)
- VER categorie (5 regels)
- ARAI categorie (9 regels)

### 4. **Session State Scheiding**
❌ **Validatie en definitie opgeslagen als één geheel**
- Geen aparte storage voor validatie resultaten
- Geen mogelijkheid om validatie los te koppelen

## Conclusie

De **DefinitieValidator** klasse is al ZEER COMPLEET en klaar voor gebruik! Wat ontbreekt is:

1. **UI integratie** - Een aparte UI component voor validatie
2. **Service scheiding** - Validatie losgekoppeld van generatie
3. **Volledigheid** - 30 ontbrekende validator implementaties
4. **Data scheiding** - Aparte opslag van validatie resultaten

## Aanbeveling

We hoeven GEEN nieuwe validator te bouwen, maar moeten:
1. De bestaande `DefinitieValidator` gebruiken
2. Een UI component maken die deze aanroept
3. De service layer refactoren om validatie onafhankelijk te maken
4. De ontbrekende validators implementeren (kunnen we uit legacy halen)