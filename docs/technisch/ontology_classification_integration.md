# Ontologische Classificatie Integratie Guide

**Datum:** 2025-10-07
**Status:** Implementation Ready
**Versie:** 1.0.0

## Overzicht

Deze guide beschrijft de integratie van het nieuwe **Hybrid Ontology Classification System** in DefinitieAgent.

### Architectuur Keuze: Hybrid Approach

**Primary: LLM-based** classificatie met **Validation: Rules-based** sanity checks.

```
Begrip + Context
    ↓
[LLM Classificatie]  → {level, confidence, rationale, linguistic_cues}
    ↓
[Rule Validator]     → Verify plausibility
    ↓
UI Display
```

**Rationale:**
- LLM lost score generatie probleem op (end-to-end: begrip → categorie)
- Rules dienen als sanity check
- Beste van beide werelden: flexibiliteit + validatie
- Transparantie via prompt visibility

## Service Architectuur

### Layer: ServiceAdapter (Optie 2)

```
src/services/classification/
├── ontology_classifier.py          # LLM-based classificatie service
├── ontology_validator.py           # Rules-based validator
└── prompts/
    └── ontology_classification.yaml  # Prompt configuratie
```

### Service Dependencies

```python
OntologyClassifierService
├── Depends on: AIServiceV2 (GPT-4 calls)
├── Depends on: OntologyValidator (sanity checks)
└── Configures: Temperature=0.3, MaxTokens=500
```

## API Specificatie

### OntologyClassifierService

```python
class OntologyClassifierService:
    """LLM-based ontologische classificatie met rule validatie."""

    def classify(
        self,
        begrip: str,
        definitie: str,
        context: Optional[str] = None,
        voorbeelden: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Classificeer begrip naar ontologische categorie.

        Returns:
            ClassificationResult met:
            - level: TYPE|EXEMPLAAR|PROCES|RESULTAAT|ONBESLIST
            - confidence: 0.0-1.0
            - rationale: Verklaring
            - linguistic_cues: List van aanwijzingen
            - validation_warnings: List van warnings
        """
```

### ClassificationResult

```python
@dataclass
class ClassificationResult:
    level: OntologyLevel              # TYPE/EXEMPLAAR/PROCES/RESULTAAT/ONBESLIST
    confidence: float                 # 0.0-1.0
    rationale: str                    # Verklaring waarom deze classificatie
    linguistic_cues: List[str]        # Linguïstische aanwijzingen
    validation_warnings: List[str]    # Warnings van validator (lege list = OK)
```

## Gebruik in UI

### Basis Integratie

```python
from src.services.classification.ontology_classifier import OntologyClassifierService
from src.ui.components.ontology_classification_display import display_ontology_classification

# 1. Get service from container
container = get_cached_container()
classifier = container.ontology_classifier()

# 2. Classificeer begrip
result = classifier.classify(
    begrip="verificatie",
    definitie="Het controleren van de juistheid van gegevens",
    context="Juridische context",
    voorbeelden=["Het verifiëren van identiteit"]
)

# 3. Display in UI
display_ontology_classification(result, mode="full")
```

### Tabbed Interface Integratie

Update `src/ui/tabbed_interface.py`:

```python
async def _determine_ontological_category_v3(
    self,
    begrip: str,
    definitie: str,
    org_context: str,
    jur_context: str
):
    """Bepaal ontologische categorie via Hybrid LLM + Rules approach."""
    try:
        # Get classifier from container
        classifier = self.container.ontology_classifier()

        # Build context
        context = f"Organisatorisch: {org_context}\nJuridisch: {jur_context}"

        # Classificeer
        result = classifier.classify(
            begrip=begrip,
            definitie=definitie,
            context=context
        )

        # Return tuple voor backward compatibility
        return (
            OntologischeCategorie[result.level],  # Convert to enum
            result.rationale,
            {  # Score dict voor legacy code
                "type": 1.0 if result.level == "TYPE" else 0.0,
                "exemplaar": 1.0 if result.level == "EXEMPLAAR" else 0.0,
                "proces": 1.0 if result.level == "PROCES" else 0.0,
                "resultaat": 1.0 if result.level == "RESULTAAT" else 0.0
            }
        )

    except Exception as e:
        logger.error(f"Ontologische classificatie gefaald: {e}")
        # Fallback naar ONBESLIST
        return (
            OntologischeCategorie.ONBESLIST,
            f"Classificatie gefaald: {str(e)}",
            {"type": 0, "exemplaar": 0, "proces": 0, "resultaat": 0}
        )
```

## Display Modes

### 1. Full Display

Toont alle details inclusief validation warnings:

```python
display_ontology_classification(result, mode="full")
```

### 2. Compact Display

Inline display met emoji + confidence:

```python
display_ontology_classification(result, mode="compact")
```

### 3. With Prompt Visibility

Voor transparency - toont gebruikte prompt:

```python
# Load prompt voor display
import yaml
with open("config/prompts/ontology_classification.yaml") as f:
    prompt_config = yaml.safe_load(f)

display_ontology_classification(
    result,
    mode="with_prompt",
    prompt_content=prompt_config['system']
)
```

## Validation Warnings Interpretatie

De validator kan deze warnings genereren:

| Warning Type | Betekenis | Actie |
|-------------|-----------|-------|
| Anti-indicator gevonden | LLM classificatie contradiceert linguïstische patronen | Controleer classificatie |
| Geen sterke indicatoren | Definitie bevat geen duidelijke aanwijzingen | Mogelijk ONBESLIST |
| Domein mismatch | Verwachte categorie verschilt van classificatie | Review classificatie |
| Sanity check failed | Implausibele classificatie (bijv. PROCES voor "document") | Waarschijnlijk fout |

### Voorbeeld Warnings

```
⚠️ Anti-indicator gevonden voor TYPE: 'handeling' in definitie
⚠️ Domein 'legal_procedure' keywords gevonden (['procedure']),
   verwachte level is PROCES, niet TYPE
```

## Performance Overwegingen

### API Calls

- **Per classificatie:** 1 GPT-4 call (~$0.002)
- **Response tijd:** 1-2 seconden (LLM latency)
- **Caching:** AI Service cache hergebruikt identical prompts

### Optimalisatie Strategieën

1. **Batch Classificatie** voor meerdere begrippen:
   ```python
   results = classifier.classify_batch([
       {"begrip": "appel", "definitie": "..."},
       {"begrip": "proces", "definitie": "..."}
   ])
   ```

2. **Cache Result** in session state:
   ```python
   # Cache result per begrip
   cache_key = f"ontology_{begrip}_{hash(definitie)}"
   if cache_key not in st.session_state:
       st.session_state[cache_key] = classifier.classify(...)
   result = st.session_state[cache_key]
   ```

3. **Skip re-classification** bij definitie wijzigingen:
   - Alleen opnieuw classificeren als begrip of definitie wezenlijk verandert

## Testing

### Unit Tests

```bash
# Run classificatie tests
pytest tests/services/classification/test_ontology_classifier.py -v

# Run validator tests
pytest tests/services/classification/test_ontology_validator.py -v
```

### Integration Tests

```python
def test_full_integration():
    """Test complete flow: begrip → classificatie → display."""
    container = get_cached_container()
    classifier = container.ontology_classifier()

    result = classifier.classify(
        begrip="verificatie",
        definitie="Het controleren van juistheid"
    )

    assert result.level in ["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT", "ONBESLIST"]
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.rationale) > 0
```

## Prompt Customization

Prompts zijn configureerbaar via `config/prompts/ontology_classification.yaml`:

```yaml
system: |
  Je bent een expert in ontologische classificatie...

  [Custom instructies hier]

user_template: |
  Begrip: {begrip}
  Definitie: {definitie}

  [Custom template hier]
```

**Best Practices:**
- Gebruik Nederlandse voorbeelden in system prompt
- Specificeer juridische context-specifieke regels
- Test prompt wijzigingen met diverse begrippen

## Monitoring & Logging

### Metrics to Track

```python
# Log classificatie events
logger.info(
    f"Classificatie resultaat: {result.level}",
    extra={
        "begrip": begrip,
        "confidence": result.confidence,
        "validation_warnings": len(result.validation_warnings),
        "duration_ms": duration
    }
)
```

### Key Metrics

- **Confidence Distribution:** Histogram van confidence scores
- **Validation Warning Rate:** % classificaties met warnings
- **Level Distribution:** Verdeling TYPE/PROCES/RESULTAAT/etc
- **API Latency:** P50, P95, P99 response tijden

## Troubleshooting

### Issue: Lage Confidence Scores

**Symptoom:** Confidence systematisch < 0.6

**Oplossingen:**
1. Verbeter definitie kwaliteit
2. Voeg context toe (org/juridisch)
3. Voeg voorbeelden toe
4. Check prompt template (mogelijk te streng)

### Issue: Veel Validation Warnings

**Symptoom:** >50% classificaties hebben warnings

**Oplossingen:**
1. Review validation rules (mogelijk te streng)
2. Retrain verwachtingen (LLM kan correct zijn)
3. Voeg domein-specifieke rules toe

### Issue: ONBESLIST te vaak

**Symptoom:** >20% classificaties zijn ONBESLIST

**Oplossingen:**
1. Lower confidence threshold in prompt
2. Verbeter system prompt met meer voorbeelden
3. Voeg domain context toe

## Migration Path

### Van Legacy QuickAnalyzer

```python
# OLD (QuickAnalyzer)
analyzer = QuickOntologischeAnalyzer()
categorie, reasoning = analyzer.quick_categoriseer(begrip)

# NEW (OntologyClassifierService)
classifier = container.ontology_classifier()
result = classifier.classify(begrip, definitie)
categorie = OntologischeCategorie[result.level]
reasoning = result.rationale
```

### Backward Compatibility

Service kan scores dict genereren voor legacy code:

```python
result = classifier.classify(begrip, definitie)

# Legacy score format
legacy_scores = {
    "type": 1.0 if result.level == "TYPE" else 0.0,
    "exemplaar": 1.0 if result.level == "EXEMPLAAR" else 0.0,
    "proces": 1.0 if result.level == "PROCES" else 0.0,
    "resultaat": 1.0 if result.level == "RESULTAAT" else 0.0
}
```

## Future Enhancements

### Phase 2: Multi-Model Ensemble

Combine LLM + Rules + Linguistic analyzer:

```python
result_llm = llm_classifier.classify(begrip, definitie)
result_rules = rule_classifier.classify_from_scores(scores)
result_linguistic = linguistic_analyzer.analyze(definitie)

# Weighted ensemble
final_result = ensemble_combine([result_llm, result_rules, result_linguistic])
```

### Phase 3: Fine-Tuned Model

Train fine-tuned model op Nederlandse juridische begrippen:

- Data: 1000+ geannoteerde begrippen
- Model: GPT-3.5 fine-tune
- Benefit: Sneller + goedkoper + betere accuracy

## References

- **Service Code:** `src/services/classification/ontology_classifier.py`
- **Validator Code:** `src/services/classification/ontology_validator.py`
- **Prompt Config:** `config/prompts/ontology_classification.yaml`
- **UI Component:** `src/ui/components/ontology_classification_display.py`
- **Tests:** `tests/services/classification/`
- **Handover Document:** `docs/handovers/HANDOVER_ONTOLOGICAL_CLASSIFICATION_REFACTOR.md`
