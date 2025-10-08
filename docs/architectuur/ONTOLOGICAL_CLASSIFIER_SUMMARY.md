# Ontological Classifier - Executive Summary

**Datum**: 2025-10-07
**Status**: Design Complete, Ready for Implementation
**Beslissing**: Optie 2 PLUS - Standalone Service met Optional Facade

---

## TL;DR

**OntologicalClassifier is een standalone, first-class service die VOOR definitie generatie classificeert.**

```python
# Gebruik in UI (3 simpele stappen):
classifier = container.ontological_classifier()
result = classifier.classify(begrip, org_ctx, jur_ctx)
request.ontologische_categorie = result.to_string_level()
```

---

## 1. Architectuur Beslissing

### GEKOZEN: Standalone Service (Optie 2 PLUS)

```
ServiceContainer
├── ontological_classifier()  ← STANDALONE (altijd beschikbaar)
├── orchestrator()             ← Gebruikt categorie uit request
└── service_adapter()          ← OPTIONAL facade (gemak)
```

**Waarom Standalone?**

| Criterium | Standalone ✅ | Nested ❌ |
|-----------|--------------|----------|
| **Timing** | VOOR generatie (correct) | Tijdens generatie (te laat) |
| **Herbruikbaar** | UI, CLI, batch, validatie | Alleen via orchestrator |
| **Testbaar** | Unit tests in isolatie | Vereist orchestrator |
| **Flexibel** | UI kan result tonen/override | Hidden binnen orchestrator |

---

## 2. API Design

### 2.1 Core Classifier

```python
from services.classification import OntologicalClassifier, ClassificationResult

# Via DI
classifier = container.ontological_classifier()

# Classificeer single
result = classifier.classify(
    begrip="Overeenkomst",
    organisatorische_context="...",
    juridische_context="..."
)

# Result bevat:
# - result.level: OntologicalLevel (U/F/O)
# - result.confidence: float (0.0-1.0)
# - result.rationale: str (waarom dit niveau?)
# - result.is_reliable: bool (confidence >= 60%)

# Gebruik in request
request.ontologische_categorie = result.to_string_level()  # "U"/"F"/"O"
```

### 2.2 Batch Processing

```python
# Classificeer meerdere begrippen
results = classifier.classify_batch(
    begrippen=["Overeenkomst", "Perceel", "Rechtspersoon"],
    shared_context=("Gemeente", "BW")
)

# Returns: dict[str, ClassificationResult]
for begrip, result in results.items():
    print(f"{begrip}: {result.level.value} ({result.confidence:.1%})")
```

### 2.3 Validation

```python
# Valideer bestaande definitie
is_correct, reason = classifier.validate_existing_definition(
    begrip="Overeenkomst",
    claimed_level="F",
    definition_text="..."
)

if not is_correct:
    print(f"Mismatch: {reason}")
```

---

## 3. UI Integration (Complete Flow)

### Stap 1: Classificeer VOOR Generatie

```python
# In definition_generator_tab.py

def handle_generate_button_click():
    # Haal classifier
    container = st.session_state.service_container
    classifier = container.ontological_classifier()

    # Classificeer
    result = classifier.classify(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context
    )

    # Toon result (optioneel)
    st.info(
        f"🔶 Geclassificeerd als: **{result.level.value}** "
        f"(confidence: {result.confidence:.1%})"
    )

    if not result.is_reliable:
        st.warning("⚠️ Lage betrouwbaarheid, voeg meer context toe")

    # Gebruik in request
    request = GenerationRequest(
        begrip=begrip,
        ontologische_categorie=result.to_string_level(),  # ← HIER
        organisatorische_context=org_context,
        # ... rest
    )

    # Genereer definitie
    response = await orchestrator.create_definition(request)
```

### Stap 2: Toon Classificatie Details (Optioneel)

```python
def display_classification_result(result: ClassificationResult):
    """Toon classificatie aan gebruiker met details"""

    # Header
    emoji = {"U": "🔷", "F": "🔶", "O": "🟠"}[result.level.value]
    st.success(f"{emoji} **Niveau: {result.level.value}**")

    # Confidence indicator
    color = {"high": "green", "medium": "orange", "low": "red"}
    st.markdown(
        f"Betrouwbaarheid: <span style='color:{color[result.confidence_level.value]}'>"
        f"{result.confidence_level.value.upper()}</span>",
        unsafe_allow_html=True
    )

    # Rationale (waarom dit niveau?)
    with st.expander("📖 Waarom dit niveau?"):
        st.write(result.rationale)

        # Alle scores
        for level, score in result.scores.items():
            st.write(f"**{level}**: {score:.1%}")
```

---

## 4. ServiceAdapter (Optional Gemak)

```python
# Optioneel: Gebruik adapter voor auto-classificatie

adapter = container.service_adapter()

# Auto-classify + generate in één call
response, classification = await adapter.generate_with_auto_classification(
    begrip="Overeenkomst",
    organisatorische_context="...",
    juridische_context="..."
)

# Response = GenerationResponse (zoals normaal)
# Classification = ClassificationResult (voor info)
```

**Wanneer Adapter Gebruiken?**

- ✅ Simpele flows zonder gebruiker interactie met classificatie
- ✅ Prototype/testing
- ❌ Als je classificatie wilt tonen aan gebruiker
- ❌ Als je manual override wilt toestaan

---

## 5. Herbruikbaarheid Voorbeelden

### 5.1 CLI Tool

```bash
# Standalone classificatie
python -m scripts.classify_term "Overeenkomst" --org-context "Gemeente"

# Batch classificatie
python -m scripts.classify_batch --input begrippen.csv --output results.csv
```

### 5.2 Database Validatie Script

```python
# scripts/validate_classifications.py

def validate_all_definitions():
    container = ServiceContainer()
    classifier = container.ontological_classifier()
    repo = container.repository()

    definitions = repo.get_all()
    mismatches = []

    for definition in definitions:
        is_correct, reason = classifier.validate_existing_definition(
            begrip=definition.begrip,
            claimed_level=definition.ontologische_categorie,
            definition_text=definition.definitie
        )

        if not is_correct:
            mismatches.append((definition.begrip, reason))

    return mismatches
```

### 5.3 Jupyter Notebook Analyse

```python
# notebooks/classification_analysis.ipynb

import pandas as pd
from services.container import ServiceContainer

container = ServiceContainer()
classifier = container.ontological_classifier()

# Batch classificatie
begrippen = ["Overeenkomst", "Perceel", "Rechtspersoon", ...]
results = classifier.classify_batch(begrippen)

# Analyse
df = pd.DataFrame([
    {
        "begrip": begrip,
        "niveau": r.level.value,
        "confidence": r.confidence,
        "betrouwbaar": r.is_reliable
    }
    for begrip, r in results.items()
])

# Visualiseer
df["niveau"].value_counts().plot(kind="bar")
```

---

## 6. Dependency Injection Setup

### In ServiceContainer

```python
# src/services/container.py

class ServiceContainer:

    def ontological_classifier(self):
        """Standalone ontological classifier (U/F/O)"""
        if "ontological_classifier" not in self._instances:
            from services.classification import OntologicalClassifier
            from services.ai_service_v2 import AIServiceV2

            ai_service = AIServiceV2(
                default_model=self.generator_config.gpt.model,
                use_cache=True
            )

            self._instances["ontological_classifier"] = OntologicalClassifier(
                ai_service
            )

        return self._instances["ontological_classifier"]

    def service_adapter(self):
        """Optional facade (classificatie + generatie)"""
        if "service_adapter" not in self._instances:
            from services.service_adapter import ServiceAdapter

            self._instances["service_adapter"] = ServiceAdapter(
                classifier=self.ontological_classifier(),
                orchestrator=self.orchestrator()
            )

        return self._instances["service_adapter"]
```

---

## 7. File Locations

### Nieuwe Bestanden

```
src/services/classification/
├── __init__.py                      # ✅ UPDATED (export OntologicalClassifier)
├── ontological_classifier.py        # ✅ CREATED (standalone classifier)
└── ontology_classifier.py           # (existing, legacy)

src/services/
├── container.py                     # ✅ UPDATED (add ontological_classifier method)
└── service_adapter.py               # TODO: OPTIONAL (facade)

docs/architectuur/
├── ontological_classifier_standalone_architecture.md  # ✅ CREATED (full design)
└── ONTOLOGICAL_CLASSIFIER_SUMMARY.md                 # ✅ CREATED (this file)

docs/examples/
├── classifier_integration_ui.py                      # ✅ CREATED (UI examples)
└── service_adapter_with_classifier.py                # ✅ CREATED (adapter examples)
```

### Te Wijzigen Bestanden

```
src/ui/components/
└── definition_generator_tab.py      # TODO: Add classification step

src/ui/
└── tabbed_interface.py              # TODO: Wire up classifier in main flow

tests/services/classification/
└── test_ontological_classifier.py   # TODO: Unit tests

tests/integration/
└── test_classification_workflow.py  # TODO: Integration tests
```

---

## 8. Implementation Checklist

### Core Implementation

- [x] Create `OntologicalClassifier` class
- [x] Add to `ServiceContainer`
- [x] Update `__init__.py` exports
- [ ] Write unit tests
- [ ] Write integration tests

### UI Integration

- [ ] Update `definition_generator_tab.py` to use classifier
- [ ] Add classification result display component
- [ ] Add manual override UI (for low confidence)
- [ ] Update main flow in `tabbed_interface.py`

### Optional Enhancements

- [ ] Create `ServiceAdapter` (optional facade)
- [ ] Create CLI classification tool
- [ ] Create batch validation script
- [ ] Create Jupyter notebook for analysis

### Documentation

- [x] Architecture document
- [x] API documentation
- [x] Usage examples
- [ ] Update CLAUDE.md
- [ ] Update INDEX.md

---

## 9. Testing Strategy

### Unit Tests

```python
# tests/services/classification/test_ontological_classifier.py

def test_classify_returns_result():
    classifier = OntologicalClassifier(mock_ai_service)
    result = classifier.classify("Overeenkomst")

    assert isinstance(result, ClassificationResult)
    assert result.level in [U, F, O]
    assert 0.0 <= result.confidence <= 1.0

def test_batch_classification():
    results = classifier.classify_batch(["Term1", "Term2"])
    assert len(results) == 2

def test_validate_existing_definition():
    is_correct, reason = classifier.validate_existing_definition(...)
    assert isinstance(is_correct, bool)
```

### Integration Tests

```python
# tests/integration/test_classification_workflow.py

@pytest.mark.integration
async def test_full_flow():
    # Stap 1: Classificeer
    result = classifier.classify("Overeenkomst")

    # Stap 2: Genereer met classificatie
    request.ontologische_categorie = result.to_string_level()
    response = await orchestrator.create_definition(request)

    assert response.success
```

---

## 10. Key Takeaways

1. **Standalone Service** - OntologicalClassifier is een first-class service, niet nested
2. **Pre-Generation** - ALTIJD classificeren VOOR `create_definition()`
3. **DI Accessible** - Beschikbaar via `container.ontological_classifier()`
4. **Herbruikbaar** - UI, CLI, batch, validatie kunnen allemaal classifier gebruiken
5. **Optional Facade** - ServiceAdapter is gemak, niet verplicht
6. **Type Safe** - ClassificationResult is dataclass met helper methods
7. **Testable** - Unit + integration tests in isolatie

---

## 11. Next Steps

1. **Review**: Team review van design decisions
2. **Implement**: Core `OntologicalClassifier` class (✅ DONE)
3. **Test**: Write unit + integration tests
4. **Integrate**: Update UI to use classifier
5. **Validate**: Test met echte begrippen
6. **Document**: Update CLAUDE.md en INDEX.md

---

## Contact

Voor vragen over deze architectuur, zie:
- **Full Design**: `docs/architectuur/ontological_classifier_standalone_architecture.md`
- **UI Examples**: `docs/examples/classifier_integration_ui.py`
- **Adapter Examples**: `docs/examples/service_adapter_with_classifier.py`
