# Ontology Classification - Quick Start Guide

**Voor:** Developers die het nieuwe classificatie systeem willen gebruiken
**Tijd:** 5 minuten

## TL;DR

```python
# 1. Get service from container
from utils.container_manager import get_cached_container

container = get_cached_container()
classifier = container.ontology_classifier()

# 2. Classificeer begrip
result = classifier.classify(
    begrip="verificatie",
    definitie="Het controleren van de juistheid"
)

# 3. Check resultaat
print(f"{result.level} (confidence: {result.confidence:.0%})")
# Output: PROCES (confidence: 92%)
```

## Ontologische Categorieën

| Categorie | Emoji | Beschrijving | Voorbeeld |
|-----------|-------|--------------|-----------|
| **TYPE** | 📦 | Algemene categorieën en soorten | "appel", "voertuig" |
| **EXEMPLAAR** | 🎯 | Specifieke instanties | "dit document", "Artikel 6 GDPR" |
| **PROCES** | ⚙️ | Handelingen en activiteiten | "verificatie", "aanvragen" |
| **RESULTAAT** | ✅ | Uitkomsten van processen | "verleende vergunning" |
| **ONBESLIST** | ❓ | Onduidelijk zonder meer context | (vermijd dit) |

## Basis Gebruik

### Simpele Classificatie

```python
classifier = container.ontology_classifier()

result = classifier.classify(
    begrip="appel",
    definitie="Een soort fruit"
)

print(f"Level: {result.level}")
print(f"Confidence: {result.confidence:.0%}")
print(f"Rationale: {result.rationale}")
```

### Met Context

Voor betere accuracy, voeg context toe:

```python
result = classifier.classify(
    begrip="verificatie",
    definitie="Het controleren van de juistheid van gegevens",
    context="Juridische procedures voor identiteitscontrole",
    voorbeelden=[
        "Het verifiëren van identiteit bij aanmelding",
        "De verificatie van documenten door de ambtenaar"
    ]
)
```

### Batch Classificatie

Voor meerdere begrippen tegelijk:

```python
items = [
    {"begrip": "appel", "definitie": "Een soort fruit"},
    {"begrip": "plukken", "definitie": "Het verwijderen van fruit"},
    {"begrip": "geplukte appel", "definitie": "Resultaat van plukken"}
]

results = classifier.classify_batch(items)

for item, result in zip(items, results):
    print(f"{item['begrip']} → {result.level}")
```

## UI Weergave

### Full Display

```python
from ui.components.ontology_classification_display import display_ontology_classification

# In Streamlit context
display_ontology_classification(result, mode="full")
```

### Compact Display

Voor inline weergave:

```python
display_ontology_classification(result, mode="compact")
# Output: ⚙️ PROCES (92%)
```

### Met Prompt Transparency

```python
import yaml

with open("config/prompts/ontology_classification.yaml") as f:
    prompt_config = yaml.safe_load(f)

display_ontology_classification(
    result,
    mode="with_prompt",
    prompt_content=prompt_config['system']
)
```

## Validatie Warnings Interpreteren

### Geen Warnings = Goede Classificatie

```python
result = classifier.classify("appel", "Een soort fruit")

if not result.validation_warnings:
    print("✓ Classificatie lijkt plausibel")
```

### Met Warnings = Controleer

```python
result = classifier.classify(
    "document",  # Statisch object
    "De handeling van opstellen"  # PROCES definitie
)

if result.validation_warnings:
    print("⚠️ Waarschuwingen:")
    for warning in result.validation_warnings:
        print(f"  - {warning}")

# Output:
# ⚠️ Waarschuwingen:
#   - PROCES classificatie onwaarschijnlijk voor statisch object: document
#   - Anti-indicator gevonden voor PROCES: 'document' in begrip
```

## Common Patterns

### In UI Tab

```python
class MyTab:
    def render(self):
        begrip = st.text_input("Begrip")
        definitie = st.text_area("Definitie")

        if st.button("Classificeer"):
            classifier = self.container.ontology_classifier()

            result = classifier.classify(begrip, definitie)

            # Display result
            display_ontology_classification(result, mode="full")

            # Store in session state
            st.session_state.ontology_result = result
```

### Caching Results

```python
# Cache per begrip + definitie hash
cache_key = f"ontology_{begrip}_{hash(definitie)}"

if cache_key not in st.session_state:
    st.session_state[cache_key] = classifier.classify(begrip, definitie)

result = st.session_state[cache_key]
```

### Backward Compatibility

Voor legacy code die score dict verwacht:

```python
result = classifier.classify(begrip, definitie)

# Convert to legacy format
legacy_scores = {
    "type": 1.0 if result.level == "TYPE" else 0.0,
    "exemplaar": 1.0 if result.level == "EXEMPLAAR" else 0.0,
    "proces": 1.0 if result.level == "PROCES" else 0.0,
    "resultaat": 1.0 if result.level == "RESULTAAT" else 0.0
}

# Convert to enum
from domain.ontological_categories import OntologischeCategorie
categorie = OntologischeCategorie[result.level]
```

## Troubleshooting

### Lage Confidence (<60%)

**Oplossingen:**
- Voeg context toe
- Verbeter definitie kwaliteit
- Voeg voorbeeldzinnen toe

```python
# Slecht (lage confidence)
result = classifier.classify("systeem", "Een geheel")

# Beter (hogere confidence)
result = classifier.classify(
    "systeem",
    "Een gestructureerd geheel van samenhangende onderdelen",
    context="IT infrastructuur",
    voorbeelden=["Het computersysteem", "Een managementsysteem"]
)
```

### Veel ONBESLIST

Als >20% classificaties ONBESLIST zijn:

1. Check definitie kwaliteit (te vaag?)
2. Voeg meer context toe
3. Controleer of begrip überhaupt classificeerbaar is

### API Errors

Bij API errors krijg je ONBESLIST fallback:

```python
result = classifier.classify(begrip, definitie)

if result.level == "ONBESLIST" and result.confidence == 0.0:
    if result.validation_warnings:
        error_msg = result.validation_warnings[0]
        if "ERROR:" in error_msg:
            st.error(f"API fout: {error_msg}")
```

## Performance Tips

### 1. Cache Results

```python
# Eenmaal classificeren, hergebruiken
if 'classifications' not in st.session_state:
    st.session_state.classifications = {}

key = f"{begrip}_{hash(definitie)}"
if key not in st.session_state.classifications:
    st.session_state.classifications[key] = classifier.classify(begrip, definitie)

result = st.session_state.classifications[key]
```

### 2. Batch Processing

```python
# Efficiënter dan loopen
items = [{"begrip": b, "definitie": d} for b, d in begrip_definitie_pairs]
results = classifier.classify_batch(items)
```

### 3. Skip Re-classification

```python
# Alleen herclassificeren bij significante wijzigingen
if st.session_state.get('last_definitie') != definitie:
    result = classifier.classify(begrip, definitie)
    st.session_state.last_definitie = definitie
    st.session_state.last_result = result
else:
    result = st.session_state.last_result
```

## Testing

### Unit Test Example

```python
from unittest.mock import Mock
import json

def test_my_classification():
    # Mock AI service
    ai_service = Mock()
    ai_service.generate_completion.return_value = json.dumps({
        "level": "TYPE",
        "confidence": 0.85,
        "rationale": "Test",
        "linguistic_cues": []
    })

    # Create classifier
    classifier = OntologyClassifierService(ai_service)
    classifier.system_prompt = "Test"
    classifier.user_template = "{begrip} {definitie}"

    # Test
    result = classifier.classify("appel", "Een fruit")

    assert result.level == "TYPE"
    assert result.confidence == 0.85
```

## Demo

Run de demo voor interactieve voorbeelden:

```bash
python scripts/demo_ontology_classification.py
```

Dit toont:
- Basis classificatie
- Classificatie met context
- Batch processing
- Validatie warnings
- Alle categorieën

## Next Steps

- **Integration Guide:** `docs/technisch/ontology_classification_integration.md`
- **Implementation Roadmap:** `docs/architectuur/ontology_classification_implementation_roadmap.md`
- **API Docs:** `src/services/classification/ontology_classifier.py`
- **Tests:** `tests/services/classification/`

## Help & Support

**Issues:**
- Lage confidence? → Voeg context/voorbeelden toe
- Veel warnings? → Review classificatie, mogelijk terecht
- API errors? → Check logs, API key, rate limits

**Questions:**
- Check documentation in `docs/technisch/`
- Review test cases in `tests/services/classification/`
- Run demo script voor voorbeelden
