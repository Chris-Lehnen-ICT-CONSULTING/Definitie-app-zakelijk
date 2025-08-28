# Workflow: Module 1 - Core Instructions Module Evaluatie & Verbetering

## Overzicht
Dit document beschrijft de systematische aanpak voor het evalueren en verbeteren van de eerste module van de ModularPromptBuilder: **CoreInstructionsModule** (`_build_role_and_basic_rules`).

## Module Informatie
- **Naam**: CoreInstructionsModule
- **Functie**: Definieert de AI rol en basis instructies
- **Locatie**: `src/services/prompts/modular_prompt_builder.py:143-248`
- **Output grootte**: ~2000-3000 karakters
- **Kriticaliteit**: HOOG - Zet de toon voor de gehele prompt

## Fase 1: Analyse (Current State)

### 1.1 Component Inventarisatie
- [ ] Documenteer huidige component structuur
- [ ] Identificeer alle sub-secties binnen de module
- [ ] Meet karakter count per sectie
- [ ] Analyseer conditionele logica

### 1.2 Output Analyse
```python
# Test script voor module output
def test_core_instructions_module():
    """Test alleen de CoreInstructionsModule output"""
    # TODO: Implementeren
```

### 1.3 Kwaliteitsmetrieken
- [ ] Duidelijkheid van instructies (1-10)
- [ ] Compleetheid t.o.v. requirements
- [ ] Consistentie met andere modules
- [ ] Redundantie niveau

## Fase 2: Testing Framework

### 2.1 Unit Test Opzet
```python
# tests/test_core_instructions_module.py
class TestCoreInstructionsModule:
    def test_basic_output_structure(self):
        """Test basis structuur van module output"""
        pass

    def test_conditional_elements(self):
        """Test conditionele elementen (bijv. resterend chars)"""
        pass

    def test_character_limits(self):
        """Test karakter limieten en waarschuwingen"""
        pass
```

### 2.2 Isolatie Testing
- [ ] Cre??er mock objects voor EnrichedContext
- [ ] Test module in isolatie
- [ ] Vergelijk met legacy output

### 2.3 Edge Cases
- [ ] Extreem lange begrippen
- [ ] Speciale karakters in begrip
- [ ] Ontbrekende context elementen
- [ ] Maximum karakter scenario's

## Fase 3: Evaluatie Criteria

### 3.1 Functionele Requirements
| Requirement | Status | Notes |
|------------|--------|-------|
| Definieer AI rol als Nederlandse expert | ? | |
| Stel definitie generatie taak | ? | |
| Specificeer output format | ? | |
| Include karakter limieten | ? | |
| Vermeld ESS normen | ? | |

### 3.2 Kwaliteitscriteria
1. **Helderheid**: Is de opdracht ondubbelzinnig?
2. **Volledigheid**: Zijn alle essentiële instructies aanwezig?
3. **Efficiëntie**: Gebruikt het onnodige tokens/ruimte?
4. **Flexibiliteit**: Kan het verschillende scenarios aan?

### 3.3 Performance Metrics
- Build tijd (ms)
- Memory footprint
- Token efficiency ratio

## Fase 4: Verbetervoorstellen

### 4.1 Structurele Verbeteringen
- [ ] Identificeer redundante secties
- [ ] Optimaliseer instructie volgorde
- [ ] Verbeter conditionele logica flow

### 4.2 Content Optimalisatie
- [ ] Herformuleer vage instructies
- [ ] Consolideer overlappende requirements
- [ ] Voeg ontbrekende edge case handling toe

### 4.3 Code Kwaliteit
- [ ] Extract magic numbers naar constants
- [ ] Verbeter error handling
- [ ] Add comprehensive logging
- [ ] Documenteer design decisions

## Fase 5: Implementatie

### 5.1 Refactoring Plan
1. **Backup huidige implementatie**
2. **Incrementele aanpassingen**:
   - Eerst structure improvements
   - Dan content optimalisatie
   - Tot slot performance tuning

### 5.2 A/B Testing Setup
```python
# Compare oude vs nieuwe module output
def compare_module_outputs(begrip, context):
    old_output = legacy_module.build(begrip, context)
    new_output = improved_module.build(begrip, context)
    return analyze_differences(old_output, new_output)
```

### 5.3 Rollout Strategy
- [ ] Test met 10 sample begrippen
- [ ] Vergelijk output kwaliteit
- [ ] Gradual rollout met feature flag

## Fase 6: Validatie

### 6.1 Output Vergelijking
- [ ] Side-by-side vergelijking legacy vs nieuw
- [ ] Kwalitatieve beoordeling door team
- [ ] Kwantitatieve metrics (lengte, structuur)

### 6.2 Integration Testing
- [ ] Test met complete prompt builder
- [ ] Valideer downstream effecten
- [ ] Performance regression tests

### 6.3 Acceptance Criteria
- [ ] Geen regressie in definitie kwaliteit
- [ ] Verbeterde leesbaarheid/structuur
- [ ] Performance binnen acceptable bounds
- [ ] Alle tests groen

## Tools & Scripts

### Analyse Tool
```bash
# Analyseer module output voor verschillende inputs
python analyze_core_module.py --begrippen "data/test_begrippen.json"
```

### Vergelijkingstool
```bash
# Vergelijk legacy vs nieuwe implementatie
python compare_modules.py --module core_instructions --samples 50
```

## Documentatie Updates
- [ ] Update inline code documentatie
- [ ] Voeg design rationale toe
- [ ] Document breaking changes
- [ ] Update integration guide

## Success Metrics
1. **Korte termijn** (Sprint 1):
   - Module geïsoleerd en testbaar
   - Baseline metrics vastgesteld
   - Verbetervoorstellen gedocumenteerd

2. **Middellange termijn** (Sprint 2-3):
   - Verbeteringen geïmplementeerd
   - A/B test resultaten positief
   - Performance verbeterd met 10%

3. **Lange termijn** (Sprint 4+):
   - Module volledig geoptimaliseerd
   - Template voor andere modules
   - Bijdrage aan overall prompt kwaliteit +15%

## Next Steps
1. Begin met Fase 1: Analyseer huidige implementatie
2. Setup test framework voor module isolatie
3. Documenteer findings in evaluation report
4. Plan improvement sprint based op findings

---
*Last updated: 2025-08-26*
*Owner: Development Team*
*Status: ACTIVE - Ready for Phase 1*
