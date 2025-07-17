# Consolidatieplan: ai_toetser + validation/definitie_validator

## 🎯 Doel
Combineer `ai_toetser/` en `validation/definitie_validator.py` tot één geünificeerd validatie systeem dat:
1. Scheiding tussen validatie en generatie volledig respecteert
2. Rich dataclasses gebruikt voor gedetailleerde feedback
3. Bestaande UI compatibiliteit behoudt
4. Modulaire architectuur verder uitbreidt

## 📊 Huidige Situatie Analyse

### ai_toetser/modular_toetser.py
- **Sterke punten:**
  - Modulaire architectuur met registry pattern
  - 16 validators al geïmplementeerd
  - Goede scheiding van verantwoordelijkheden
  - UI-vriendelijke string output
  
- **Zwakke punten:**
  - Simpele string output (geen rich feedback)
  - Geen scoring mechanisme
  - Geen severity levels

### validation/definitie_validator.py
- **Sterke punten:**
  - Rich dataclasses (ValidationResult, RuleViolation)
  - Scoring en severity systeem
  - Intelligent interpreteren van toetsregels
  - Gedetailleerde feedback mogelijkheden
  
- **Zwakke punten:**
  - Geen modulaire validators implementatie
  - Duplicatie met ai_toetser functionaliteit
  - Niet direct UI-compatible

## 🏗️ Nieuwe Architectuur

```
src/toetsregels/                     # NIEUWE unified locatie
├── __init__.py                      # Export facade
├── engine.py                        # ToetsregelEngine (orchestrator)
├── validator.py                     # DefinitieValidator (rich validation)
├── models.py                        # Dataclasses (ValidationResult, etc.)
├── interpreter.py                   # ValidationRegelInterpreter
├── registry.py                      # ValidatorRegistry
├── adapters/
│   ├── __init__.py
│   └── ui_adapter.py               # Convert rich results naar UI strings
└── rules/                          # Modulaire validators
    ├── __init__.py
    ├── base.py                     # BaseValidator
    ├── content/
    │   ├── __init__.py
    │   ├── con_01.py              # CON-01 validator
    │   └── con_02.py              # CON-02 validator
    ├── essential/
    │   ├── __init__.py
    │   ├── ess_01.py              # ESS-01 validator
    │   └── ...
    └── structure/
        ├── __init__.py
        ├── str_01.py              # STR-01 validator
        └── ...
```

## 🔄 Integratie Strategie

### Fase 1: Structuur Setup
1. Maak nieuwe `src/toetsregels/` directory structuur
2. Kopieer dataclasses uit `validation/definitie_validator.py` naar `models.py`
3. Kopieer registry uit `ai_toetser/validators/__init__.py` naar `registry.py`
4. Setup basis imports en exports

### Fase 2: Engine Integratie
1. Combineer `ModularToetser` en `DefinitieValidator` in nieuwe `ToetsregelEngine`
2. Engine gebruikt:
   - Registry pattern van ModularToetser
   - Rich output van DefinitieValidator
   - Modulaire validators van ai_toetser

### Fase 3: Validator Migratie
1. Update `BaseValidator` om `ValidationOutput` te returnen (niet strings)
2. Migreer alle 16 bestaande validators naar nieuwe structuur
3. Behoud backward compatibility via adapters

### Fase 4: UI Adapter
1. Maak `UIAdapter` class die:
   - `ValidationResult` → `List[str]` converteert
   - Emoji formatting toepast
   - Score samenvattingen genereert
2. Gebruik adapter in orchestration layer

## 🔌 API Design

### Unified API:
```python
# Single, rich API voor alle gebruik
from toetsregels import ToetsregelEngine
engine = ToetsregelEngine()
result = engine.validate(definitie, categorie)  # Returns ToetsregelValidationResult
```

### UI Integratie:
De UI wordt geüpdatet om direct met het rich validation result te werken:
- Toon overall score prominent
- Groepeer violations op severity
- Toon suggesties voor verbetering
- Visualiseer scores per regel

## 📝 Implementatie Volgorde

1. **models.py** - Dataclasses consolidatie
2. **registry.py** - Registry pattern
3. **base.py** - Updated BaseValidator
4. **engine.py** - Hoofdorchestrator
5. **ui_adapter.py** - UI compatibility layer
6. **rules/** - Migreer validators één voor één
7. **__init__.py** - Public API exports

## ✅ Acceptatie Criteria

- [ ] Alle 16 bestaande validators werken zonder wijziging
- [ ] UI output blijft identiek voor gebruikers
- [ ] Rich validation data beschikbaar voor nieuwe features
- [ ] Geen breaking changes in bestaande code
- [ ] Tests blijven slagen
- [ ] Performance verbetert of blijft gelijk

## 🚫 Wat NIET te doen

1. NIET de JSON configuratie files aanpassen
2. NIET de UI direct updaten (gebruik adapter)
3. NIET legacy functies meteen verwijderen
4. NIET de orchestration layer (UnifiedDefinitionService) aanpassen

## 🎯 Eindresultaat

Een geünificeerd systeem met:
- Modulaire validators (uitbreidbaar)
- Rich validation feedback (voor toekomstige UI)
- Backward compatible API's
- Cleane scheiding tussen validatie en generatie
- Performance optimalisaties mogelijk