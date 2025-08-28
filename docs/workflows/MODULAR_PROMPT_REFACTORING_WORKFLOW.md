# Workflow: Modular Prompt Architecture Refactoring

## Overzicht
Complete herstructurering van het prompt systeem naar een echt modulaire architectuur met individuele modules en een orchestrator.

## Fase 1: Planning & Analyse (James - Dev Agent)

### 1.1 Inventarisatie Huidige Situatie
- [ ] Analyseer `ModularPromptBuilder` - identificeer alle prompt secties
- [ ] Analyseer legacy `PromptBouwer` - begrijp volledige flow
- [ ] Identificeer alle dependencies en imports
- [ ] Document huidige prompt structuur (15-20k karakters)

### 1.2 Definieer Module Interfaces
```python
# Base interface voor alle modules
class PromptModule(ABC):
    @abstractmethod
    def build_section(self, begrip: str, context: Context) -> str:
        """Build dit deel van de prompt."""
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """Volgorde in de prompt (1-8)."""
        pass

    @abstractmethod
    def is_required(self, context: Context) -> bool:
        """Is deze module nodig voor deze context?"""
        pass
```

### 1.3 Module Specificaties
Per module documenteren:
- Input requirements
- Output format
- Dependencies op andere modules
- Business rules

## Fase 2: Archivering & Cleanup (James)

### 2.1 Archiveer Verouderde Code
- [ ] Verplaats huidige `ModularPromptBuilder` → `/docs/archief/2025-08-26-prompt-refactor/`
- [ ] Verplaats test bestanden → zelfde archief folder
- [ ] Verplaats analyse documenten → archief

### 2.2 Cleanup
- [ ] Verwijder experimental files (core_instructions_v2.py, etc.)
- [ ] Update imports die naar oude code verwijzen
- [ ] Maak backup: `git checkout -b backup/pre-modular-refactor`

## Fase 3: Module Ontwikkeling (James)

### 3.1 Create Module Structure
```
src/services/prompts/
├── modules/
│   ├── __init__.py
│   ├── base.py                    # PromptModule interface
│   ├── expertise_module.py        # Module 1
│   ├── output_specification_module.py  # Module 2
│   ├── grammar_module.py          # Module 3
│   ├── context_awareness_module.py     # Module 4
│   ├── semantic_categorisation_module.py # Module 5
│   ├── quality_rules_module.py    # Module 6
│   ├── error_prevention_module.py # Module 7
│   └── definition_task_module.py  # Module 8
└── orchestrator/
    ├── __init__.py
    └── prompt_orchestrator.py
```

### 3.2 Implementeer Modules (één voor één)
Voor elke module:
1. Implementeer de module class
2. Schrijf unit tests
3. Code review
4. Integreer met orchestrator

#### Module 1: ExpertiseModule
```python
class ExpertiseModule(PromptModule):
    """Definieert de expert rol voor ChatGPT."""

    def build_section(self, begrip: str, context: Context) -> str:
        # Implementatie
        pass
```

## Fase 4: Orchestrator Implementatie (James)

### 4.1 PromptOrchestrator
```python
class PromptOrchestrator:
    """Coördineert alle modules om complete prompt te bouwen."""

    def __init__(self):
        self.modules = self._initialize_modules()

    def build_prompt(self, begrip: str, context: Context) -> str:
        prompt_sections = []

        for module in self._get_active_modules(context):
            section = module.build_section(begrip, context)
            if section:
                prompt_sections.append(section)

        return self._combine_sections(prompt_sections)
```

## Fase 5: Testing Strategy (James + Quinn for QA)

### 5.1 Unit Tests per Module
- [ ] Test elke module individueel
- [ ] Test edge cases
- [ ] Test met verschillende contexten
- [ ] Validate output format

### 5.2 Integration Tests
- [ ] Test orchestrator met alle modules
- [ ] Test met subset van modules
- [ ] Test module ordering
- [ ] Test section combination

### 5.3 Regression Tests
- [ ] Vergelijk output met legacy prompt builder
- [ ] Test met 100+ begrippen
- [ ] Validate tegen bestaande toetsregels
- [ ] Performance benchmarks

### 5.4 Code Quality (Quinn - QA Agent)
```bash
# Voor elke module en orchestrator
*run-tests
python -m pytest tests/prompts/modules/ -v --cov
python -m pylint src/services/prompts/modules/
python -m mypy src/services/prompts/modules/
```

## Fase 6: Code Review Checklist (Quinn)

### Per Module Review
- [ ] Single Responsibility: Doet de module één ding?
- [ ] Interface Compliance: Implementeert PromptModule correct?
- [ ] Error Handling: Graceful degradation?
- [ ] Documentation: Docstrings en comments aanwezig?
- [ ] Test Coverage: >90% coverage?
- [ ] Performance: Geen onnodige operations?

### Orchestrator Review
- [ ] Module Loading: Efficient en foutbestendig?
- [ ] Ordering Logic: Correct en configureerbaar?
- [ ] Section Combining: Behoud formatting?
- [ ] Error Recovery: Wat als module faalt?
- [ ] Extensibility: Makkelijk nieuwe modules toevoegen?

## Fase 7: Migration & Integration (James)

### 7.1 Update Dependencies
- [ ] Update `UnifiedPromptBuilder` om orchestrator te gebruiken
- [ ] Update `DefinitionOrchestrator` imports
- [ ] Update configuration files

### 7.2 Feature Toggle
```python
USE_MODULAR_ORCHESTRATOR = os.getenv('USE_MODULAR_ORCHESTRATOR', 'false') == 'true'

if USE_MODULAR_ORCHESTRATOR:
    prompt_builder = PromptOrchestrator()
else:
    prompt_builder = LegacyPromptBuilder()
```

### 7.3 Gradual Rollout
1. Test in development
2. Enable voor 10% van requests
3. Monitor metrics
4. Full rollout als stabiel

## Fase 8: Documentation (James)

### 8.1 Technical Documentation
- [ ] Architecture diagram
- [ ] Module interaction flow
- [ ] Configuration guide
- [ ] Extension guide

### 8.2 Migration Guide
- [ ] Breaking changes
- [ ] Update instructions
- [ ] Rollback procedure

## Success Criteria

### Functioneel
- [ ] Alle 8 modules geïmplementeerd en getest
- [ ] Orchestrator combineert modules correct
- [ ] Output identiek aan legacy (waar gewenst)
- [ ] Performance gelijk of beter

### Code Kwaliteit
- [ ] 90%+ test coverage per module
- [ ] Alle code reviews goedgekeurd
- [ ] Geen kritieke issues van linters
- [ ] Documentatie compleet

### Business Value
- [ ] Modules individueel configureerbaar
- [ ] Makkelijk nieuwe modules toevoegen
- [ ] Duidelijke separation of concerns
- [ ] Maintainable en uitbreidbaar

## Rollback Plan
Als issues tijdens rollout:
1. `export USE_MODULAR_ORCHESTRATOR=false`
2. Revert naar legacy prompt builder
3. Analyseer logs voor root cause
4. Fix issues in feature branch
5. Retry rollout

## Timeline Estimate
- Fase 1-2: 1 dag (Planning & Cleanup)
- Fase 3-4: 3 dagen (8 modules + orchestrator)
- Fase 5-6: 2 dagen (Testing & Review)
- Fase 7-8: 1 dag (Integration & Docs)

**Totaal: ~1 week**

---
*Workflow aangemaakt: 2025-08-26*
*Agents: James (Dev), Quinn (QA)*
*Status: READY TO START*
