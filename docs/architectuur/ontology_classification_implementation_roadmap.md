# Ontology Classification Implementation Roadmap

**Datum:** 2025-10-07
**Auteur:** Implementation Analysis
**Status:** Ready for Implementation

## Executive Summary

Dit document beschrijft de complete implementatie roadmap voor het nieuwe **Hybrid Ontology Classification System** in DefinitieAgent.

### Architectuur Beslissing

**AANBEVELING: Hybrid Approach (LLM Primary + Rules Validation)**

```
┌─────────────────────────────────────────┐
│         Begrip + Definitie              │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│    LLM Classificatie (GPT-4)            │
│  - End-to-end: begrip → categorie       │
│  - Context-aware, flexibel              │
│  - Temperature: 0.3 (consistent)        │
└────────────┬────────────────────────────┘
             │
             ↓ {level, confidence, rationale}
             │
┌─────────────────────────────────────────┐
│    Rules-based Validator                │
│  - Sanity checks                        │
│  - Linguistic patterns                  │
│  - Domain heuristics                    │
└────────────┬────────────────────────────┘
             │
             ↓ + validation_warnings
             │
┌─────────────────────────────────────────┐
│         UI Display                      │
│  - Classification result                │
│  - Confidence score                     │
│  - Rationale                            │
│  - Warnings (if any)                    │
└─────────────────────────────────────────┘
```

## Vergelijking: Rules-Based vs LLM vs Hybrid

| Aspect | Rules-Based | LLM-Based | **Hybrid (AANBEVOLEN)** |
|--------|-------------|-----------|-------------------------|
| **Score Generatie** | ❌ Externe dependency | ✅ Built-in | ✅ Built-in |
| **Snelheid** | ✅ <10ms | ❌ 1-2s | ⚠️ 1-2s (LLM bottleneck) |
| **Kosten** | ✅ Gratis | ❌ $0.002/call | ❌ $0.002/call |
| **Flexibiliteit** | ❌ Beperkt | ✅ Hoog | ✅ Hoog |
| **Transparantie** | ✅ Exact traceable | ⚠️ AI rationale | ✅ AI + Rule checks |
| **Deterministisch** | ✅ Ja | ❌ Nee | ⚠️ Nee (LLM primary) |
| **Onderhoudbaarheid** | ❌ Regex updates | ✅ Prompt tuning | ✅ Prompt + Rules |
| **Edge Cases** | ❌ Vast programma | ✅ Adaptief | ✅ Adaptief + Checks |
| **Implementatie Tijd** | 8u | 6u | **10u** |

**Conclusie:** Hybrid biedt beste balans tussen flexibiliteit en betrouwbaarheid.

## Implementatie Fases

### Fase 1: Core Service (4 uur)

**Deliverable:** `src/services/classification/ontology_classifier.py`

**Functionaliteit:**
- LLM-based classificatie via GPT-4
- Prompt template loading uit YAML
- JSON response parsing
- Error handling met ONBESLIST fallback
- Batch classificatie support

**Key Methods:**
```python
classify(begrip, definitie, context, voorbeelden) → ClassificationResult
classify_batch(items) → List[ClassificationResult]
```

**Dependencies:**
- AIServiceV2 (existing)
- OntologyValidator (fase 2)

### Fase 2: Rules-based Validator (2 uur)

**Deliverable:** `src/services/classification/ontology_validator.py`

**Functionaliteit:**
- Linguistic pattern matching (regex)
- Anti-indicator detection
- Domain-specific heuristics (legal, biology)
- Sanity checks (PROCES ≠ document)

**Validation Types:**
1. **Linguistic Patterns:** Zoek naar (anti-)indicatoren in definitie
2. **Domain Rules:** Check domein-specifieke verwachtingen
3. **Sanity Checks:** Detecteer implausibele combinaties

### Fase 3: Prompt Configuration (1 uur)

**Deliverable:** `config/prompts/ontology_classification.yaml`

**Configuratie:**
```yaml
system: |
  Expert instructies + categorieën uitleg + Nederlandse voorbeelden

user_template: |
  Begrip: {begrip}
  Definitie: {definitie}
  {context_section}

  Return JSON: {level, confidence, rationale, linguistic_cues}

version: "1.0.0"
model_requirements:
  temperature: 0.3
  max_tokens: 500
  model: "gpt-4"
```

### Fase 4: Service Container Integration (1 uur)

**Deliverable:** Update `src/services/container.py`

**Toevoegen:**
```python
def ontology_classifier(self):
    """Get or create OntologyClassifierService singleton."""
    if "ontology_classifier" not in self._instances:
        ai_service = AIServiceV2(...)
        self._instances["ontology_classifier"] = OntologyClassifierService(ai_service)
    return self._instances["ontology_classifier"]
```

### Fase 5: UI Components (2 uur)

**Deliverable:** `src/ui/components/ontology_classification_display.py`

**Display Modes:**
1. **Full:** Complete weergave met details + warnings
2. **Compact:** Inline emoji + confidence
3. **With Prompt:** Transparantie via prompt visibility

**UI Features:**
- Emoji per categorie (📦 TYPE, ⚙️ PROCES, etc.)
- Color-coded confidence (groen >0.8, oranje 0.6-0.8, rood <0.6)
- Expandable details + validation warnings
- Prompt visibility toggle

### Fase 6: Unit Tests (3 uur)

**Deliverables:**
- `tests/services/classification/test_ontology_classifier.py`
- `tests/services/classification/test_ontology_validator.py`

**Test Coverage:**
- ✅ Successful classifications (alle levels)
- ✅ Context/voorbeelden integratie
- ✅ Validation warning triggers
- ✅ JSON parsing (valid, markdown, invalid)
- ✅ Error handling (API errors → ONBESLIST)
- ✅ Batch processing
- ✅ Temperature/max_tokens settings
- ✅ Pattern matching (alle levels)
- ✅ Domain rules
- ✅ Anti-indicator detection

### Fase 7: Integration & Documentation (2 uur)

**Deliverables:**
- Integration guide: `docs/technisch/ontology_classification_integration.md`
- Update `src/ui/tabbed_interface.py` met nieuwe methode
- Update `CLAUDE.md` met classificatie info

**Documentation Inclusief:**
- API specificatie
- Gebruik voorbeelden
- Display modes
- Performance overwegingen
- Troubleshooting guide
- Migration path van legacy code

## Totale Implementatie Tijd

| Fase | Tijd |
|------|------|
| 1. Core Service | 4u |
| 2. Rules Validator | 2u |
| 3. Prompt Config | 1u |
| 4. Container Integration | 1u |
| 5. UI Components | 2u |
| 6. Unit Tests | 3u |
| 7. Integration & Docs | 2u |
| **TOTAAL** | **15 uur** |

## Architectuur Beslissing: Layer Keuze

### Gekozen: ServiceAdapter Layer (Optie 2)

**Rationale:**

✅ **Voor ServiceAdapter:**
- Eigen service boundary (single responsibility)
- Herbruikbaar voor toekomstige features
- Testbaar in isolatie
- Dependency injection via container
- Niet afhankelijk van orchestrator complexity

❌ **Tegen UI Layer (Optie 1):**
- 61 LOC orchestration in tabbed_interface.py = God Object anti-pattern
- Business logic gemixed met presentatie
- Moeilijk testbaar
- Niet herbruikbaar

❌ **Tegen Orchestrator (Optie 3):**
- 18u werk voor marginale voordelen
- Over-engineered voor current use case
- Alleen zinvol als classificatie deel wordt van core workflow

## Code Structuur

```
src/services/classification/
├── __init__.py
├── ontology_classifier.py          # 150 LOC - LLM classificatie
└── ontology_validator.py           # 200 LOC - Rules validatie

config/prompts/
└── ontology_classification.yaml    # Prompt templates

src/ui/components/
└── ontology_classification_display.py  # 250 LOC - UI component

tests/services/classification/
├── test_ontology_classifier.py     # 300 LOC
└── test_ontology_validator.py      # 250 LOC

docs/
├── technisch/
│   └── ontology_classification_integration.md
└── architectuur/
    └── ontology_classification_implementation_roadmap.md (dit document)
```

## Integration Met Bestaande Code

### Vervangen: QuickAnalyzer Pattern

**Voor (legacy):**
```python
# OLD: 1054 LOC analyzer met score generatie + classificatie
analyzer = OntologischeAnalyzer()
categorie, analyse = await analyzer.bepaal_ontologische_categorie(...)

# Fallback: QuickAnalyzer
quick_analyzer = QuickOntologischeAnalyzer()
categorie, reasoning = quick_analyzer.quick_categoriseer(begrip)
```

**Na (nieuw):**
```python
# NEW: Clean service-based approach
classifier = container.ontology_classifier()
result = classifier.classify(begrip, definitie, context, voorbeelden)

# Convert voor backward compatibility
categorie = OntologischeCategorie[result.level]
reasoning = result.rationale
```

### Backward Compatibility

```python
# Legacy code verwacht scores dict
legacy_scores = {
    "type": 1.0 if result.level == "TYPE" else 0.0,
    "exemplaar": 1.0 if result.level == "EXEMPLAAR" else 0.0,
    "proces": 1.0 if result.level == "PROCES" else 0.0,
    "resultaat": 1.0 if result.level == "RESULTAAT" else 0.0
}
```

## Performance Profiel

### LLM Calls

- **Frequency:** 1x per begrip classificatie
- **Latency:** 1-2 seconden (GPT-4)
- **Cost:** ~$0.002 per classificatie
- **Caching:** AIServiceV2 cache hergebruikt identical prompts

### Optimalisatie

1. **Session State Caching:**
   ```python
   cache_key = f"ontology_{begrip}_{hash(definitie)}"
   if cache_key not in st.session_state:
       st.session_state[cache_key] = classifier.classify(...)
   ```

2. **Batch Processing:**
   ```python
   results = classifier.classify_batch([
       {"begrip": "appel", "definitie": "..."},
       {"begrip": "plukken", "definitie": "..."}
   ])
   ```

3. **Skip Re-classification:**
   - Alleen herdoen als begrip/definitie wezenlijk verandert

## Security & Privacy

- ✅ Geen sensitive data in prompts (alleen begrip + definitie)
- ✅ API key via environment variable
- ✅ No PII in classificatie context
- ✅ Prompts zijn raadpleegbaar (transparency)

## Monitoring Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| **Average Confidence** | >0.75 | <0.6 |
| **ONBESLIST Rate** | <10% | >20% |
| **Validation Warning Rate** | <30% | >50% |
| **API Latency P95** | <3s | >5s |
| **API Error Rate** | <1% | >5% |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM Non-determinisme** | Inconsistente classificaties | Temperature=0.3, Validation checks |
| **API Kosten** | Budget overschrijding | Cache results, Monitor usage |
| **API Latency** | Slechte UX | Session state cache, Batch processing |
| **Prompt Drift** | Accuracy degradatie | Version control prompts, A/B testing |
| **Validation Overlap** | Te veel warnings | Tune rules, Feedback loop |

## Success Criteria

✅ **Functionaliteit:**
- Classificeert begrippen naar 5 categorieën (TYPE/EXEMPLAAR/PROCES/RESULTAAT/ONBESLIST)
- Confidence scores >0.75 gemiddeld
- <10% ONBESLIST rate
- Validation warnings bij implausibele classificaties

✅ **Performance:**
- Response tijd <3s (P95)
- Session state caching werkend
- <$10/maand API kosten (bij 500 classificaties/maand)

✅ **Kwaliteit:**
- Unit test coverage >80%
- Integration tests passing
- Documentation compleet
- No regression in bestaande features

✅ **Usability:**
- Duidelijke UI weergave met emoji's
- Validation warnings actionable
- Prompt transparency optie
- Backward compatible met legacy code

## Next Steps

### Immediate (Week 1)

1. ✅ Implementeer Fase 1-3 (Core + Validator + Prompts) - **7 uur**
2. ✅ Unit tests voor core functionaliteit - **2 uur**
3. ✅ Container integration - **1 uur**

### Short-term (Week 2)

4. ⏳ UI component implementatie - **2 uur**
5. ⏳ Integration in tabbed_interface.py - **1 uur**
6. ⏳ Complete test suite - **2 uur**

### Mid-term (Week 3-4)

7. 📋 User acceptance testing
8. 📋 Prompt tuning based on feedback
9. 📋 Performance monitoring setup
10. 📋 Documentation finalization

### Long-term (Future Epics)

- **Fine-tuned Model:** Train GPT-3.5 fine-tune op NL juridische begrippen
- **Ensemble Approach:** Combine LLM + Rules + Linguistic analyzer
- **Active Learning:** Feedback loop voor prompt improvement
- **Multi-language:** Uitbreiden naar Engels/Frans

## Conclusie

Het **Hybrid Ontology Classification System** lost de volgende problemen op:

1. ✅ **Score Generatie Gap:** LLM doet end-to-end classificatie
2. ✅ **Flexibiliteit:** LLM kan nuances oppikken
3. ✅ **Betrouwbaarheid:** Rules valideren LLM output
4. ✅ **Transparantie:** Prompt visibility + rationale
5. ✅ **Onderhoudbaarheid:** Prompt tuning > regex updates
6. ✅ **Service Boundary:** Clean separation of concerns

**Implementatie tijd:** 15 uur
**ROI:** Betere classificatie accuracy + minder onderhoud
**Risk Level:** Medium (LLM dependency, API kosten)

---

**Status:** Ready for Implementation
**Next Action:** Start Fase 1 (Core Service) implementatie
