# Implementation Plan: FeedbackBuilder Refactoring
## US-062: Refactor FeedbackBuilder naar moderne service

---

## 📋 Executive Summary
Refactor de FeedbackBuilder logica uit `src/orchestration/definitie_agent.py` naar een moderne, testbare `FeedbackServiceV2` die past binnen de V2 architectuur.

**Geschatte effort:** 8 story points  
**Geschatte duur:** 2-3 dagen  
**Risk level:** MEDIUM (kritieke business logica)

---

## 🎯 Doelstellingen

1. **Extract** FeedbackBuilder logica uit legacy code
2. **Moderniseer** naar V2 service patterns
3. **Behoud** alle business intelligence en algoritmes
4. **Verbeter** testbaarheid en onderhoudbaarheid
5. **Integreer** met bestaande V2 orchestrator

---

## 📐 Architectuur Design

### Service Structuur
```
src/services/feedback/
├── feedback_service_v2.py         # Hoofdservice
├── feedback_builder.py            # Builder logica
├── feedback_prioritizer.py        # Prioritering algoritmes
├── feedback_history.py            # History management
└── __init__.py
```

### Service Contract
```python
@dataclass
class FeedbackItem:
    type: Literal["critical", "suggestion", "improvement"]
    message: str
    violation_code: str | None
    priority: int
    iteration_aware: bool = False

@dataclass
class FeedbackContext:
    iteration: int
    previous_score: float
    current_score: float
    violations: list[ValidationViolation]
    history: list[FeedbackItem]

class FeedbackServiceV2:
    def generate_feedback(
        self,
        context: FeedbackContext,
        max_items: int = 5
    ) -> list[FeedbackItem]:
        """Genereer intelligente, geprioriteerde feedback"""
        
    def detect_stagnation(
        self,
        scores: list[float],
        threshold: float = 0.05
    ) -> bool:
        """Detecteer of verbetering stagneert"""
        
    def suggest_alternative_approach(
        self,
        iteration: int,
        violation_pattern: str
    ) -> str:
        """Genereer alternatieve suggesties per iteratie"""
```

---

## 🔧 Implementatie Stappen

### Phase 1: Service Setup (Dag 1 - Ochtend)
- [ ] Creëer service directory structuur
- [ ] Implementeer basis FeedbackServiceV2 class
- [ ] Setup dependency injection in ServiceContainer
- [ ] Creëer data classes (FeedbackItem, FeedbackContext)

### Phase 2: Core Logic Migration (Dag 1 - Middag)
- [ ] Migreer violation-to-feedback mappings (11 rules)
- [ ] Implementeer feedback prioritering algoritme
- [ ] Port iteratie-bewuste feedback logica
- [ ] Implementeer stagnatie detectie

### Phase 3: Advanced Features (Dag 2 - Ochtend)
- [ ] Implementeer feedback groepering per type
- [ ] Port lerende feedback mechanisme
- [ ] Implementeer FIFO history management (max 10)
- [ ] Add deduplicatie logica

### Phase 4: Integration (Dag 2 - Middag)
- [ ] Integreer met ValidationOrchestratorV2
- [ ] Update DefinitionGeneratorService calls
- [ ] Behoud backwards compatibility waar nodig
- [ ] Update ServiceContainer configuratie

### Phase 5: Testing & Validation (Dag 3)
- [ ] Unit tests voor alle publieke methods
- [ ] Integratie tests met orchestrator
- [ ] Performance benchmarks
- [ ] Valideer business rules behoud

---

## 🧪 Test Strategie

### Unit Tests
```python
tests/services/feedback/
├── test_feedback_service_v2.py
├── test_feedback_builder.py
├── test_feedback_prioritizer.py
└── test_feedback_history.py
```

### Test Coverage Targets
- FeedbackServiceV2: 95%+
- Business logic: 100%
- Edge cases: Stagnatie, regressie, max iteraties

### Kritieke Test Scenarios
1. **Prioritering:** Kritiek > Suggesties > Overig
2. **Max Items:** Nooit meer dan 5 feedback items
3. **Stagnatie:** Detectie bij <0.05 verbetering
4. **Iteratie Aware:** Verschillende feedback per iteratie
5. **History:** FIFO met max 10 items

---

## 📊 Business Rules Mapping

### Violation-to-Feedback Rules
| Violation | Feedback Message | Priority |
|-----------|-----------------|----------|
| CON-01 | "Context-specifiek zonder expliciete vermelding" | HIGH |
| CON-02 | "Baseer op authentieke bronnen" | HIGH |
| ESS-01 | "Beschrijf WAT het is, niet waarvoor" | CRITICAL |
| ESS-02 | "Maak type/proces/resultaat expliciet" | CRITICAL |
| ESS-03 | "Voeg unieke identificerende kenmerken toe" | HIGH |
| ESS-04 | "Gebruik objectief meetbare criteria" | MEDIUM |
| ESS-05 | "Benadruk onderscheidende eigenschappen" | MEDIUM |
| INT-01 | "Formuleer als één zin zonder opsommingen" | HIGH |
| INT-03 | "Vervang onduidelijke verwijzingen" | MEDIUM |
| STR-01 | "Start met centraal zelfstandig naamwoord" | HIGH |
| STR-02 | "Gebruik concrete, specifieke terminologie" | HIGH |

### Iteratie Strategieën
| Iteratie | Feedback Stijl | Voorbeeld |
|----------|---------------|----------|
| 1 | Direct | "Vermijd deze patronen..." |
| 2 | Alternatief | "Nog steeds aanwezig, probeer..." |
| 3 | Fundamenteel | "Overweeg complete herformulering..." |

---

## ⚠️ Risico's & Mitigaties

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Verlies business logica | HIGH | Uitgebreide tests, side-by-side validatie |
| Performance degradatie | MEDIUM | Benchmarks, caching strategieën |
| Integration issues | MEDIUM | Gefaseerde rollout, feature flags |
| Regression in feedback kwaliteit | HIGH | A/B testing met legacy |

---

## 🔄 Migration Path

### Stap 1: Parallel Running
```python
# In ValidationOrchestratorV2
if settings.USE_NEW_FEEDBACK_SERVICE:
    feedback = self.feedback_service_v2.generate_feedback(context)
else:
    feedback = self._legacy_feedback_builder(violations)
```

### Stap 2: Gradual Rollout
- Week 1: 10% traffic naar nieuwe service
- Week 2: 50% traffic (monitor metrics)
- Week 3: 100% traffic
- Week 4: Remove legacy code

### Stap 3: Legacy Cleanup
- Archive `definitie_agent.py` FeedbackBuilder code
- Update alle references
- Remove feature flags

---

## 📈 Success Metrics

### Functioneel
- ✅ Alle 11 violation mappings werkend
- ✅ Feedback prioritering identiek aan legacy
- ✅ Stagnatie detectie accuraat
- ✅ Iteratie-aware feedback actief

### Technisch
- ✅ Test coverage >95%
- ✅ Response time <100ms
- ✅ Memory footprint <50MB
- ✅ Zero regression in feedback kwaliteit

### Business
- ✅ Definitie acceptatie rate gelijk of beter
- ✅ Gemiddeld aantal iteraties gelijk of lager
- ✅ User satisfaction behouden

---

## 🔗 Dependencies

### Code Dependencies
- `src/services/validation/modular_validation_service.py` - Voor violations
- `src/services/orchestration/validation_orchestrator_v2.py` - Voor integratie
- `src/models/validation_models.py` - Voor data types

### Knowledge Dependencies
- [BUSINESS_KNOWLEDGE_EXTRACTION.md](../US-061/BUSINESS_KNOWLEDGE_EXTRACTION.md)
- Legacy code analyse
- V2 architectuur patterns

---

## 📝 Documentatie Updates

Na implementatie updaten:
- [ ] EPIC-012.md met completion status
- [ ] ServiceContainer documentatie
- [ ] API documentatie voor FeedbackServiceV2
- [ ] Migration guide voor developers

---

## 👥 Team & Resources

**Lead Developer:** Backend Team  
**Code Reviewer:** Senior Architect  
**Business Validator:** Product Owner  

**Geschatte Timeline:**
- Start: Direct na goedkeuring plan
- Design Review: Dag 1, 14:00
- Code Complete: Dag 2, 17:00
- Testing Complete: Dag 3, 12:00
- Production Ready: Dag 3, 17:00

---

## ✅ Definition of Done

- [ ] Alle unit tests groen (>95% coverage)
- [ ] Integratie tests passed
- [ ] Performance benchmarks acceptable
- [ ] Code review approved
- [ ] Business rules validated
- [ ] Documentation updated
- [ ] No regression in functionality
- [ ] Legacy code archived (niet verwijderd)