# Implementation Plan: FeedbackBuilder Refactoring
## US-062: Refactor FeedbackBuilder naar moderne service

---

## 📋 Executive Summary
Refactor de FeedbackBuilder logica uit `src/orchestration/definitie_agent.py` naar een moderne, testbare `FeedbackServiceV2` die technische validation output vertaalt naar menselijke feedback.

**⚠️ KRITIEKE DEPENDENCY:** US-064 (Edit Interface) moet EERST geïmplementeerd worden voor volledige waarde

**Geschatte effort:** 8 story points  
**Geschatte duur:** 2-3 dagen  
**Risk level:** HIGH (beperkte waarde zonder edit functionaliteit)  
**Value:** MEDIUM nu, HIGH na US-064 implementatie

### 🎯 Het Kernprobleem
**Huidige situatie:** 
1. Gebruikers krijgen onbegrijpelijke technische validatie output
2. **EN kunnen er NIETS mee doen** (geen edit mogelijkheid)

```
❌ VER-03: specifieke data of tijdstippen gevonden: 
- Ontologische categorie: soort, Gegevens die kenmerken...
```

**Gewenste situatie (vereist US-064):** 
1. Gebruikers krijgen concrete instructies
2. **EN kunnen deze direct toepassen** via edit interface

```
❌ "Vervang '1 januari 2024' door 'datum van inwerkingtreding'"
[Edit Knop] → User past aan → Nieuwe validatie → Betere feedback
```

### 💡 Gefaseerde Aanpak (NIEUW)
**Fase 1:** Implementeer US-064 (Edit Interface) - **8 story points**
**Fase 2:** Implementeer US-062 (FeedbackBuilder) - **8 story points**
**Totaal:** 16 story points voor complete oplossing

### ⚠️ Waarschuwing conform CLAUDE.md
Volgens "Doe wat gevraagd is; niets meer, niets minder" principe:
- FeedbackBuilder heeft BEPERKTE waarde zonder edit mogelijkheid
- Overweeg om eerst US-064 te prioriteren
- Of implementeer alleen minimale feedback mappings (2 story points)

---

## 🎯 Doelstellingen

1. **Extract** FeedbackBuilder logica uit legacy code
2. **Moderniseer** naar V2 service patterns
3. **Behoud** alle business intelligence en algoritmes
4. **Verbeter** testbaarheid en onderhoudbaarheid
5. **Integreer** als aanvulling op bestaande validation services
6. **Vertaal** technische violations naar menselijke feedback
7. **Voorbereid** voor toekomstige edit/import features

---

## 🚀 Use Cases & Werkelijke Waarde Analyse

### Use Case 1: Feedback tijdens Generatie (BEPERKTE WAARDE ⚠️)
**Scenario:** Gebruiker genereert definitie → Validatie faalt → Krijgt betere errors  
**Realiteit:** Gebruiker kan alleen opnieuw genereren, niet echt verbeteren
**Werkelijke waarde:** LAAG - Alleen informatief, niet actionable
**Vereist:** Geen dependencies

### Use Case 2: Iteratieve Definitie Verbetering (HOOFDWAARDE ✅)
**Scenario:** Genereer → Edit → Valideer → Feedback → Verbeter → Repeat
**Realiteit:** WERKT NIET zonder US-064 (Edit Interface)
**Werkelijke waarde:** HOOG - Dit is waar FeedbackBuilder voor bedoeld is
**Vereist:** US-064 MOET eerst geïmplementeerd zijn

### Use Case 3: Externe Definitie Validatie (TOEKOMSTIG)
**Scenario:** Import definitie uit Word/Excel → Valideer → Feedback
**Realiteit:** Import functionaliteit bestaat nog niet (US-027)
**Werkelijke waarde:** MEDIUM - Nuttig voor migraties
**Vereist:** US-027 (Import) + US-064 (Edit)

### Use Case 4: Bulk Import Kwaliteitsrapport (TOEKOMSTIG)
**Scenario:** Import 100+ definities → Batch validatie → Feedback rapport
**Realiteit:** Bulk import bestaat nog niet (US-062 in EPIC-005)
**Werkelijke waarde:** LAAG - Nice to have
**Vereist:** US-062 (Bulk Import) + US-027 (Import)

### 📊 Realistische Waarde Assessment
| Use Case | Zonder US-064 | Met US-064 | Prioriteit |
|----------|---------------|------------|------------|
| Generatie Feedback | 20% waarde | 30% waarde | LOW |
| Iteratieve Verbetering | 0% waarde | 90% waarde | CRITICAL |
| Import Validatie | 0% waarde | 70% waarde | MEDIUM |
| Bulk Import | 0% waarde | 40% waarde | LOW |

---

## 🔄 Integratie Architectuur

### Geen Duplicatie - Pure Aanvulling
```
User Input
    ↓
ValidationService (BESTAAND - blijft intact)
    ├─ Detecteert violations
    ├─ Berekent scores
    └─ Match patterns
         ↓
    [Technische Output]
         ↓
FeedbackServiceV2 (NIEUW - vertaallaag)
    ├─ Vertaalt violations → menselijke taal
    ├─ Prioriteert feedback items
    └─ Genereert contextual suggesties
         ↓
    [Menselijke Feedback]
         ↓
UI Display (beide outputs beschikbaar)
```

### Integratie Opties

#### Optie A: Decorator Pattern (algemeen)
```python
class ValidationOrchestratorV2:
    def validate_definition(self, definition: str) -> ValidationResult:
        # Bestaande validatie logic blijft intact
        result = self.validation_service.validate(definition)
        
        # NIEUW: Optionele feedback toevoeging
        if self.feedback_service and self.include_feedback:
            result.human_feedback = self.feedback_service.generate_feedback(
                violations=result.violations,
                context=FeedbackContext(
                    iteration=self.current_iteration,
                    previous_score=self.previous_score,
                    current_score=result.overall_score
                )
            )
        
        return result
```

**Voordelen:**
- Backwards compatible
- Feedback is opt-in
- Single result object
- Clean separation of concerns

#### Optie A.1: Decorator in DefinitionOrchestratorV2 (AANBEVOLEN ⭐)
```python
# Schematisch, async V2 voorbeeld (post-validatie)
class DefinitionOrchestratorV2:
    async def create_definition(self, request, context=None):
        # ... PHASE 5: Cleaning
        # ... PHASE 6: Validation
        validation_result = await self.validation_service.validate_text(
            begrip=request.begrip,
            text=cleaned_text,
            ontologische_categorie=request.ontologische_categorie,
            context=validation_context,
        )

        # NIEUW: feedbackverrijking na validatie (opt-in via config/feature flag)
        if getattr(self.config, "enable_feedback_loop", True) and self.feedback_engine:
            suggestions = await self.feedback_engine.process_validation_feedback(
                definition_id=generation_id,
                validation_result=validation_result,
                original_request=request,
            )
            validation_result["improvement_suggestions"] = suggestions

        # ... PHASE 8..11 blijven ongewijzigd
        return definition_response
```

**Voordelen extra:**
- Validator blijft dun (geen businesslogica)
- Sluit aan op bestaand `improvement_suggestions` veld
- Eenvoudige feature‑flagged rollout

#### Optie B: Pipeline Pattern
```python
# In UI layer
validation_result = orchestrator.validate(definition)
feedback = feedback_service.process(validation_result)
display_results(validation_result, feedback)
```

**Voordelen:**
- Volledig ontkoppeld
- UI beslist over gebruik
- Flexibele compositie

#### Optie C: Observer Pattern
```python
class FeedbackObserver:
    def on_validation_complete(self, result: ValidationResult):
        feedback = self.generate_feedback(result)
        self.publish_feedback(feedback)
```

**Voordelen:**
- Event-driven
- Loose coupling
- Async mogelijk

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
    violations: list[RuleViolation]
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

## 🔧 Implementatie Opties

### Optie A: Volledige Implementatie (NIET AANBEVOLEN ❌)
**Wanneer:** Alleen als US-064 al in development is
**Effort:** 8 story points
**Stappen:** Alle phases zoals hieronder beschreven

### Optie B: Minimale Implementatie (OVERWEGEN ⚠️)
**Wanneer:** Als quick win gewenst zonder US-064
**Effort:** 2 story points
**Stappen:** 
- Alleen violation-to-feedback mappings (45 regels)
- Simpele vertaalservice zonder iteratie logica
- Geen history, geen stagnatie detectie

### Optie C: Prioriteit Verschuiving (AANBEVOLEN ✅)
**Wanneer:** Voor maximale waarde
**Effort:** 16 story points totaal
**Stappen:**
1. **EERST:** Implementeer US-064 (Edit Interface) - 8 points
2. **DAN:** Implementeer US-062 (FeedbackBuilder) - 8 points

---

## 📅 Gefaseerde Implementatie Plan

### FASE 1: US-064 Implementation (Week 1-2)
**Doel:** Edit mogelijkheid creëren
- [ ] Plain text editor implementeren
- [ ] Definitie opslaan/laden functionaliteit
- [ ] Real-time validation integratie
- [ ] Version history basis
- [ ] UI navigatie naar edit mode

### FASE 2: US-062 Basis (Week 3 - Dag 1)
**Doel:** Feedback mappings zonder complexiteit
- [ ] Creëer FeedbackServiceV2 skeleton
- [ ] Implementeer 45 violation-to-feedback mappings
- [ ] Simpele prioritering (Critical → High → Medium → Low)
- [ ] Integreer met DefinitionOrchestratorV2 (post‑validatie hook)

### FASE 3: US-062 Advanced (Week 3 - Dag 2-3)
**Doel:** Intelligente features toevoegen
- [ ] Iteratie-aware feedback (1/2/3 verschillende strategieën)
- [ ] Stagnatie detectie implementeren
- [ ] History management (FIFO, max 10)
- [ ] Contextual suggestions voor edit mode

### FASE 4: Integratie & Testing (Week 4)
**Doel:** Alles samenvoegen en valideren
- [ ] Edit + Feedback loop testen
- [ ] Performance optimalisatie
- [ ] A/B testing tegen legacy
- [ ] Gebruikersacceptatie tests
 - [ ] Single Import flow: endpoint/CLI voor “validate_imported_definition” (validatie + top‑5 feedback)
 - [ ] Bulk Import: batch API/CLI, CSV/Excel exporter (per item score + top‑3), aggregatierapport (acceptatie‑ratio, top violations, p95 duur)

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
5. **Legacy parity:** Nieuwe output matcht legacy via adapter op vaste fixtures
6. **Bulk export:** CSV/Excel inhoud en aggregaties kloppen en zijn deterministisch
5. **History:** FIFO met max 10 items

---

## 📊 Business Rules Mapping

### Gedocumenteerde Violation-to-Feedback Mappings (11 uit legacy code)
| Violation | Technische Output | FeedbackBuilder Output | Priority |
|-----------|------------------|------------------------|----------|
| CON-01 | "Context niet expliciet" | "Maak de juridische context expliciet, bijvoorbeeld: 'in het kader van...'" | HIGH |
| CON-02 | "Geen bronnen gevonden" | "Voeg juridische bronnen toe zoals wetsartikelen (bijv. 'conform artikel 7:1 BW')" | HIGH |
| ESS-01 | "Pattern 'wordt gebruikt voor'" | "Beschrijf WAT het begrip is, niet waarvoor het gebruikt wordt" | CRITICAL |
| ESS-02 | "Type niet gespecificeerd" | "Specificeer of dit een proces, resultaat of entiteit betreft" | CRITICAL |
| ESS-03 | "Geen unieke kenmerken" | "Voeg onderscheidende kenmerken toe die dit begrip uniek maken" | HIGH |
| ESS-04 | "Geen meetbare criteria" | "Gebruik objectief meetbare criteria zoals termijnen, bedragen of aantallen" | MEDIUM |
| ESS-05 | "Geen onderscheid" | "Benadruk wat dit begrip onderscheidt van vergelijkbare begrippen" | MEDIUM |
| INT-01 | "Meerdere zinnen" | "Formuleer als één samenhangende zin zonder opsommingen" | HIGH |
| INT-03 | "Vage verwijzing 'deze'" | "Vervang 'deze' door het specifieke begrip waar je naar verwijst" | MEDIUM |
| STR-01 | "Begint niet met naamwoord" | "Begin je definitie met het kernbegrip, bijvoorbeeld: 'Een [begrip] is...'" | HIGH |
| STR-02 | "Vage terminologie" | "Gebruik concrete, juridisch specifieke terminologie" | HIGH |

### Contextual Feedback Examples
| Situatie | Standaard Feedback | Contextual Enhancement |
|----------|-------------------|------------------------|
| Iteratie 1 | "Vermijd vage termen" | "Vervang 'mogelijk' door 'kan' of 'mag'" |
| Iteratie 2 | "Nog steeds vage termen" | "Probeer: 'is bevoegd tot' i.p.v. 'mogelijk'" |
| Iteratie 3 | "Vage termen persistent" | "Overweeg complete herformulering zonder modaliteiten" |
| Stagnatie | "Score verbetert niet" | "Focus op één aspect tegelijk, begin met structuur" |

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
# In DefinitionOrchestratorV2 (post-validatie)
from services.feature_flags import FEEDBACK_SERVICE_V2

validation_result = await self.validation_service.validate_text(...)
if getattr(self.config, "enable_feedback_loop", True) and FEEDBACK_SERVICE_V2 and self.feedback_engine:
    suggestions = await self.feedback_engine.process_validation_feedback(
        definition_id=generation_id,
        validation_result=validation_result,
        original_request=request,
    )
    validation_result["improvement_suggestions"] = suggestions
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
- `src/services/validation/modular_validation_service.py` - Voor violations input
- `src/services/orchestrators/validation_orchestrator_v2.py` - Voor validatie orchestratie
- `src/services/validation/interfaces.py` - Voor data types (RuleViolation, ValidationResult)
- `src/services/container.py` - Voor service registration

### Knowledge Dependencies
- [BUSINESS_KNOWLEDGE_EXTRACTION.md](../US-061/BUSINESS_KNOWLEDGE_EXTRACTION.md)
- Legacy code analyse
- V2 architectuur patterns

### Feature Dependencies (Toekomstig)
| Feature | User Story | Status | Impact op FeedbackBuilder |
|---------|------------|--------|---------------------------|
| Definition Edit | US-064 | Open (HIGH) | Enables iterative feedback during editing |
| Import Validation | US-027 | Nog te bepalen | Feedback voor imported definitions |
| Bulk Import | US-062 | Open (HIGH) | Batch feedback + CSV/Excel export + aggregatie |
| Batch Operations | US-028 | Nog te bepalen | Performance optimalisaties nodig |

### Critical Dependency
⚠️ **US-064 (Definition Edit Interface)** is kritiek voor volledige waarde van FeedbackBuilder:
- Zonder edit: Feedback alleen informatief
- Met edit: Feedback wordt actionable
- **Mitigatie:** Design FeedbackService met edit-ready API vanaf begin

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

---

## 📦 Bulk Rapportage (Specificatie)

### Exportformaat
- CSV/Excel met kolommen:
  - `id`, `bron`, `begrip`, `score`, `is_acceptable`, `violations_count`, `duration_ms`, `top1_feedback`, `top2_feedback`, `top3_feedback`

### Aggregaties
- Acceptatie‑ratio (aantal acceptabel / totaal)
- Top 5 meest voorkomende violations (rule_id + count)
- Tijdsverdeling: p50/p95 `duration_ms`

### Criteria
- Deterministisch bij gelijke input
- Geen duplicaten in top‑3 per item
- Uitvoer < 100ms per item (excl. validatie)

---

## 🏁 Conclusie & Beslispunten

### Realistische Assessment
1. **Beperkte directe waarde** - Zonder edit (US-064) is feedback alleen informatief
2. **Hoge dependency** - Hoofdwaarde komt pas met US-064
3. **Over-engineered risk** - 8 points voor feature die nu beperkt nuttig is
4. **CLAUDE.md conflict** - "Doe wat gevraagd is" vs bouwen voor toekomst

### Aanbevolen Beslissing

#### 🎯 **BESTE OPTIE: Prioriteit Verschuiving (Optie C)**
**Waarom:**
- US-064 (Edit) geeft directe waarde aan gebruikers
- FeedbackBuilder wordt dan logische follow-up
- Totaal 16 points maar met gegarandeerde waarde
- Conform CLAUDE.md: geen over-engineering

**Implementatie volgorde:**
1. **Sprint 1-2:** US-064 (Edit Interface) - 8 points
2. **Sprint 3:** US-062 (FeedbackBuilder) - 8 points

#### ⚠️ **ALTERNATIEF: Minimale Quick Win (Optie B)**
**Wanneer overwegen:**
- Als US-064 lang duurt
- Voor immediate kleine verbetering
- Slechts 2 story points investment

**Wat krijg je:**
- 45 violation → feedback mappings
- Betere error messages
- Geen complexe features

### Go/No-Go Decision Matrix

| Criterium | Optie A (Full) | Optie B (Minimal) | Optie C (Phased) |
|-----------|----------------|-------------------|------------------|
| Directe waarde | ❌ Laag | ⚠️ Matig | ✅ Hoog |
| Effort | ❌ 8 points | ✅ 2 points | ⚠️ 16 points |
| Risk | ❌ Hoog | ✅ Laag | ✅ Laag |
| CLAUDE.md conform | ❌ Nee | ✅ Ja | ✅ Ja |
| **Aanbeveling** | ❌ | ⚠️ | ✅✅✅ |

### Verwachte Impact PER OPTIE

**Optie A (Full zonder US-064):**
- Gebruikerstevredenheid: +10% (alleen betere messages)
- Definitie kwaliteit: Geen verbetering
- ROI: Negatief

**Optie B (Minimal):**
- Gebruikerstevredenheid: +20% (begrijpelijke errors)
- Definitie kwaliteit: +5% (betere prompts)
- ROI: Positief

**Optie C (Phased met US-064):**
- Gebruikerstevredenheid: +60% (edit + feedback)
- Definitie kwaliteit: +40% (iteratieve verbetering)
- ROI: Zeer positief
