# Toetsregel-Prompt Module Architecture Proposal

## Executive Summary

Dit document beschrijft een architecturaal voorstel voor het implementeren van een **Single Source of Truth** systeem waarbij elke toetsregel zowel validatie als prompt-generatie logica beheert. Dit voorstel sluit aan bij de bestaande Enterprise Architecture en Solution Architecture documenten.

## Alignment met Bestaande Architectuur

### Requirements Alignment (REQUIREMENTS_AND_FEATURES_COMPLETE.md)
- **Epic 2: Kwaliteitstoetsing**: 85% Compleet, 45/46 regels werkend
- **KWA-001**: "Per regel resultaat" - Dit voorstel maakt dat consistent
- **KWA-004**: "Custom toetsregels" - Dit framework maakt dat mogelijk
- **UI-014**: "Ontologische score" - Backend calculation via modules
- **Missie**: "46 kwaliteitsregels" - Single source voor alle 46

### EA Alignment
- **Business Capability**: "Multi-Level Quality Validation" (EA regel 37)
- **Current State**: "45/46 toetsregels actief" (EA regel 23)
- **Tech Debt**: "Legacy UnifiedDefinitionService te groot" (EA regel 28)
- **Architectural Principle**: "Reuse Before Build" (EA regel 284)

### SA Alignment
- **Validation Framework**: "78 validation rules in src/rules/" (SA regel 148)
- **PromptBuilderInterface**: Reeds genoemd maar nog niet geïmplementeerd (SA regel 21, 582)
- **Key Design Decision #7**: "Single Source of Truth" al toegevoegd (SA regel 58)
- **Token Reductie**: Van 7.250 naar ~2.000-3.000 tokens (SA regel 17)

## Probleemstelling

### Huidige Situatie
1. **Duplicatie**: Validatieregels in `/src/toetsregels/` en prompt instructies in `/src/services/prompts/` zijn gescheiden
2. **Inconsistentie**: Dezelfde regel kan anders geïmplementeerd zijn voor validatie vs generatie
3. **Token Verspilling**: Alle 45+ regels worden in prompt gezet (~7.250 tokens) ongeacht context
4. **Onderhoudbaarheid**: Bij wijziging regel moet op 2+ plekken aangepast worden

### Impact
- **Performance**: Elke prompt kost €0.03-0.05 door onnodige tokens
- **Kwaliteit**: Inconsistentie tussen wat gevalideerd wordt en wat gegenereerd wordt
- **Velocity**: Dubbel werk bij regel aanpassingen

## Voorgestelde Architectuur

### Conceptueel Model

```python
# Single Source of Truth per Toetsregel
class ToetsregelModule(ABC):
    """Base class voor alle toetsregels."""

    @abstractmethod
    def get_metadata(self) -> ToetsregelMetadata:
        """Regel ID, naam, prioriteit, categorie, etc."""
        pass

    @abstractmethod
    def validate(self, definition: str, context: Context) -> ValidationResult:
        """Valideer definitie tegen deze regel."""
        pass

    @abstractmethod
    def get_prompt_instruction(self, context: Context) -> PromptFragment:
        """Genereer prompt fragment voor deze regel."""
        pass

    @abstractmethod
    def is_applicable(self, context: Context) -> bool:
        """Bepaal of regel relevant is voor context."""
        pass
```

### Component Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│                    ToetsregelRegistry                       │
│              (Central Registration & Discovery)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬───────────────┐
        ▼              ▼              ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ARAI Modules │ │ CON Modules  │ │ ESS Modules  │ │ STR Modules  │
│   (15 rules) │ │  (5 rules)   │ │  (10 rules)  │ │  (15 rules)  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │              │              │               │
        └──────────────┴──────────────┴───────────────┘
                       │
                       ▼
              ┌────────────────┐
              │PromptComposer  │
              │ (Dynamic)      │
              └────────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ ValidationService│        │ GenerationService │
│  (Uses validate) │        │ (Uses get_prompt)│
└──────────────────┘        └──────────────────┘
```

## Implementatie Strategie

### Fase 1: Foundation (Week 1-2)
1. **Creëer base classes**:
   - `ToetsregelModule` abstract base class
   - `ToetsregelRegistry` voor centrale registratie
   - `PromptComposer` voor dynamische samenstelling

2. **Pilot met 5 regels**:
   - ARAI-01 t/m ARAI-05
   - Test validate() en get_prompt_instruction()
   - Benchmark token gebruik

### Fase 2: Migration (Week 3-4)
1. **Migreer alle 45 regels**:
   - Behoud backwards compatibility via adapters
   - Parallel testing: oude vs nieuwe implementatie

2. **Integratie met bestaande services**:
   - `ModularValidationService` gebruikt nieuwe modules
   - `PromptServiceV2` gebruikt `PromptComposer`

### Fase 3: Optimization (Week 5-6)
1. **Context-aware selectie**:
   - Alleen relevante regels in prompt
   - Token budget management

2. **Performance tuning**:
   - Cache prompt fragments
   - Lazy loading van regels

## Technische Implementatie Details

### Directory Structuur
```
src/
├── toetsregels/
│   ├── base/
│   │   ├── __init__.py
│   │   ├── module.py          # ToetsregelModule ABC
│   │   └── registry.py        # ToetsregelRegistry
│   ├── modules/
│   │   ├── arai/
│   │   │   ├── __init__.py
│   │   │   ├── arai_01_geen_werkwoord.py
│   │   │   ├── arai_02_containerbegrippen.py
│   │   │   └── ...
│   │   ├── con/
│   │   ├── ess/
│   │   └── str/
│   └── composer/
│       ├── __init__.py
│       └── prompt_composer.py
```

### Voorbeeld Implementatie

```python
# src/toetsregels/modules/arai/arai_02_containerbegrippen.py
from toetsregels.base import ToetsregelModule, ValidationResult, PromptFragment

class ARAI02ContainerbegrippenModule(ToetsregelModule):
    """ARAI-02: Vermijd vage containerbegrippen."""

    VERBODEN_WOORDEN = ['aspect', 'element', 'proces', 'activiteit', 'voorziening']

    def get_metadata(self):
        return ToetsregelMetadata(
            id="ARAI-02",
            naam="Vermijd containerbegrippen",
            categorie="Algemene Regels AI",
            prioriteit=Priority.HIGH,
            weight=0.8
        )

    def validate(self, definition: str, context: Context) -> ValidationResult:
        """Valideer of definitie geen containerbegrippen bevat."""
        violations = []
        for woord in self.VERBODEN_WOORDEN:
            if woord in definition.lower():
                violations.append(woord)

        return ValidationResult(
            passed=len(violations) == 0,
            score=1.0 if len(violations) == 0 else 0.0,
            feedback=f"Containerbegrippen gevonden: {', '.join(violations)}" if violations else "Geen containerbegrippen",
            suggestions=["Vervang vage termen door specifieke beschrijvingen"] if violations else []
        )

    def get_prompt_instruction(self, context: Context) -> PromptFragment:
        """Genereer prompt instructie voor deze regel."""
        return PromptFragment(
            instruction="Vermijd vage containerbegrippen zoals 'aspect', 'element', 'proces'",
            examples_good=["maatregel die gericht is op risicobeheersing"],
            examples_bad=["proces ter ondersteuning"],
            estimated_tokens=45
        )

    def is_applicable(self, context: Context) -> bool:
        """Deze regel is altijd van toepassing."""
        return True
```

## Voordelen

### Technische Voordelen
1. **DRY Principle**: Één definitie per regel
2. **Consistency**: Validatie = Generatie logica
3. **Testability**: Elke regel isolated testbaar
4. **Performance**: 65% minder tokens (van 7.250 naar ~2.500)
5. **Maintainability**: Wijziging op één plek

### Business Voordelen
1. **Cost Reduction**: €0.02-0.03 per prompt besparing
2. **Quality**: Consistente definities (validatie aligned met generatie)
3. **Velocity**: Snellere regel updates
4. **Scalability**: Makkelijk nieuwe regels toevoegen

## Risico's en Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| Breaking changes | Hoog | Medium | Backwards compatibility via adapters |
| Performance degradatie | Medium | Laag | Caching en lazy loading |
| Test coverage gaps | Medium | Medium | Parallel testing oude vs nieuwe |
| Team weerstand | Laag | Medium | Gefaseerde rollout met quick wins |

## Metrics voor Succes

1. **Token Reductie**: Van 7.250 naar <3.000 tokens (>58% reductie)
2. **Test Coverage**: 100% coverage op alle ToetsregelModules
3. **Performance**: <100ms voor prompt compositie
4. **Consistency**: 0 verschillen tussen validatie en generatie logica
5. **Maintainability**: 1 locatie per regel (was 3-5)

## Aanbeveling

Dit voorstel past perfect binnen de bestaande architectuur en lost concrete problemen op:
- Sluit aan bij EA's "Multi-Level Quality Validation" capability
- Implementeert SA's PromptBuilderInterface concept
- Lost tech debt op van "Legacy UnifiedDefinitionService"
- Realiseert 65% token reductie zoals genoemd in SA

**Advies**: Start met Fase 1 pilot (5 regels) om concept te bewijzen, daarna gefaseerde migratie.

## Appendix: Relatie tot Bestaande Documenten

### Product Requirements
- **REQUIREMENTS_AND_FEATURES_COMPLETE.md**: Epic 2 (Kwaliteitstoetsing) - 85% compleet
- **User Story KWA-001**: Gedetailleerde validatie per regel
- **User Story KWA-004**: Custom toetsregels (niet gestart) - dit framework maakt het mogelijk
- **Project Missie**: "46 kwaliteitsregels" - gecentraliseerd in modules

### Architecture Documents
- **EA Section 1.1**: Business Capability "Multi-Level Quality Validation"
- **EA Section 4.3**: Innovation Roadmap "Advanced AI (GPT-4+)"
- **SA Section 1.2**: Service Specification "Validation Service"
- **SA Key Decision #7**: "Single Source of Truth"
- **docs/toetsregels/TOETSREGELS_MODULE_GUIDE.md**: Bestaande documentatie kan uitgebreid worden

### Status Documents
- **Feature Status**: 26% totaal compleet, Kwaliteitstoetsing 85% compleet
- **45/46 toetsregels actief**: Deze architectuur maakt 46/46 mogelijk
