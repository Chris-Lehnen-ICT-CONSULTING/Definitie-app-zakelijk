# Ontological Classifier - Quick Reference Cheatsheet

**Voor developers die snel aan de slag willen**

---

## Installation

```python
# Already done! OntologicalClassifier is in ServiceContainer
# No pip install needed
```

---

## Basic Usage (UI)

### 1. Get Classifier from DI

```python
container = st.session_state.service_container
classifier = container.ontological_classifier()
```

### 2. Classify Single Term

```python
result = classifier.classify(
    begrip="Overeenkomst",
    organisatorische_context="Gemeente administratie",
    juridische_context="Burgerlijk wetboek"
)

# Result attributes:
result.level                 # OntologicalLevel (U/F/O enum)
result.confidence            # float (0.0-1.0)
result.confidence_level      # ClassificationConfidence (HIGH/MEDIUM/LOW)
result.rationale            # str (waarom dit niveau?)
result.scores               # dict {"U": 0.08, "F": 0.89, "O": 0.03}
result.is_reliable          # bool (confidence >= 60%)
result.to_string_level()    # str ("U"/"F"/"O") voor GenerationRequest
```

### 3. Use in Generation Request

```python
request = GenerationRequest(
    begrip="Overeenkomst",
    ontologische_categorie=result.to_string_level(),  # ← SET THIS
    organisatorische_context="...",
    juridische_context="...",
    # ... rest
)

response = await orchestrator.create_definition(request)
```

---

## Complete UI Flow Example

```python
def handle_generate_definition():
    """Complete flow: classify → show → generate"""

    # Step 1: Get services
    container = st.session_state.service_container
    classifier = container.ontological_classifier()
    orchestrator = container.orchestrator()

    # Step 2: Classify
    classification = classifier.classify(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context
    )

    # Step 3: Show classification to user
    st.info(
        f"🔶 Geclassificeerd als: **{classification.level.value}** "
        f"(confidence: {classification.confidence:.1%})"
    )

    # Step 4: Check reliability
    if not classification.is_reliable:
        st.warning("⚠️ Lage betrouwbaarheid")

        # Optional: Allow manual override
        if st.checkbox("Handmatig niveau selecteren?"):
            level = st.radio("Kies niveau:", ["U", "F", "O"])
            # Override classification.level here

    # Step 5: Build request with classification
    request = GenerationRequest(
        begrip=begrip,
        ontologische_categorie=classification.to_string_level(),
        organisatorische_context=org_context,
        juridische_context=jur_context,
        # ... rest
    )

    # Step 6: Generate definition
    with st.spinner("Genereer definitie..."):
        response = await orchestrator.create_definition(request)

    # Step 7: Show results
    if response.success:
        st.success("✅ Definitie gegenereerd!")
        st.write(response.definition_text)
```

---

## Batch Processing

### Classify Multiple Terms

```python
# Input
begrippen = ["Overeenkomst", "Perceel", "Rechtspersoon"]

# Classify batch
classifier = container.ontological_classifier()
results = classifier.classify_batch(
    begrippen=begrippen,
    shared_context=("Gemeente", "BW")  # Optional
)

# Results is dict[str, ClassificationResult]
for begrip, result in results.items():
    print(f"{begrip}: {result.level.value} ({result.confidence:.1%})")
```

### Export to CSV

```python
import pandas as pd

# Convert results to DataFrame
df = pd.DataFrame([
    {
        "begrip": begrip,
        "niveau": result.level.value,
        "confidence": f"{result.confidence:.1%}",
        "betrouwbaar": "Ja" if result.is_reliable else "Nee"
    }
    for begrip, result in results.items()
])

# Save to CSV
df.to_csv("classificatie_resultaten.csv", index=False)
```

---

## Validation of Existing Definitions

### Single Validation

```python
classifier = container.ontological_classifier()

is_correct, reason = classifier.validate_existing_definition(
    begrip="Overeenkomst",
    claimed_level="F",
    definition_text="Een overeenkomst is..."
)

if not is_correct:
    print(f"❌ Mismatch: {reason}")
else:
    print("✅ Classificatie correct")
```

### Batch Validation

```python
# Get all definitions from DB
repo = container.repository()
definitions = repo.get_all()

# Validate each
classifier = container.ontological_classifier()
mismatches = []

for definition in definitions:
    is_correct, reason = classifier.validate_existing_definition(
        begrip=definition.begrip,
        claimed_level=definition.ontologische_categorie,
        definition_text=definition.definitie
    )

    if not is_correct:
        mismatches.append({
            "begrip": definition.begrip,
            "claimed": definition.ontologische_categorie,
            "reason": reason
        })

# Report
print(f"Found {len(mismatches)} mismatches:")
for m in mismatches:
    print(f"  {m['begrip']}: {m['reason']}")
```

---

## ServiceAdapter (Optional Convenience)

### Auto-Classify + Generate

```python
# Get adapter
adapter = container.service_adapter()

# One call does classify + generate
response, classification = await adapter.generate_with_auto_classification(
    begrip="Overeenkomst",
    organisatorische_context="...",
    juridische_context="...",
    # ... rest
)

# Use results
print(f"Classification: {classification.level.value}")
print(f"Definition: {response.definition_text}")
```

### Manual Classification + Generate

```python
adapter = container.service_adapter()

# Step 1: Classify only
classification = adapter.classify_only(
    begrip="Overeenkomst",
    organisatorische_context="..."
)

# Step 2: Show to user, allow override
print(f"Classification: {classification.level.value}")
# ... user interaction

# Step 3: Generate with (possibly modified) classification
response = await adapter.generate_with_classification(
    classification=classification,
    begrip="Overeenkomst",
    organisatorische_context="...",
    # ... rest
)
```

---

## Common Patterns

### Pattern 1: Simple UI Integration

```python
# Minimal changes to existing flow
classifier = container.ontological_classifier()
classification = classifier.classify(begrip, org_ctx, jur_ctx)

request.ontologische_categorie = classification.to_string_level()
response = await orchestrator.create_definition(request)
```

### Pattern 2: Show Classification with Details

```python
classification = classifier.classify(...)

# Show level
emoji = {"U": "🔷", "F": "🔶", "O": "🟠"}[classification.level.value]
st.success(f"{emoji} Niveau: {classification.level.value}")

# Show confidence
st.write(f"Confidence: {classification.confidence:.1%}")

# Show rationale
with st.expander("Waarom dit niveau?"):
    st.write(classification.rationale)
```

### Pattern 3: Allow Manual Override

```python
classification = classifier.classify(...)

if not classification.is_reliable:
    st.warning("Lage betrouwbaarheid")

    if st.checkbox("Handmatig kiezen?"):
        chosen_level = st.radio("Niveau:", ["U", "F", "O"],
                                index=["U", "F", "O"].index(classification.level.value))

        # Create new classification with chosen level
        from src.toetsregels.level_classifier import OntologicalLevel
        classification.level = OntologicalLevel(chosen_level)
```

### Pattern 4: Batch with Progress

```python
import streamlit as st

begrippen = ["Term1", "Term2", "Term3", ...]

progress_bar = st.progress(0)
results = {}

for i, begrip in enumerate(begrippen):
    result = classifier.classify(begrip)
    results[begrip] = result

    progress_bar.progress((i + 1) / len(begrippen))

st.success(f"✅ {len(results)} begrippen geclassificeerd!")
```

---

## Testing

### Unit Test

```python
import pytest
from unittest.mock import Mock

def test_classify():
    mock_ai_service = Mock()
    classifier = OntologicalClassifier(mock_ai_service)

    result = classifier.classify("Overeenkomst")

    assert result.level in [OntologicalLevel.UNIVERSEEL,
                            OntologicalLevel.FUNCTIONEEL,
                            OntologicalLevel.OPERATIONEEL]
    assert 0.0 <= result.confidence <= 1.0
```

### Integration Test

```python
@pytest.mark.integration
async def test_full_flow():
    container = ServiceContainer()
    classifier = container.ontological_classifier()
    orchestrator = container.orchestrator()

    # Classify
    classification = classifier.classify("Overeenkomst")

    # Generate
    request = GenerationRequest(
        begrip="Overeenkomst",
        ontologische_categorie=classification.to_string_level()
    )

    response = await orchestrator.create_definition(request)

    assert response.success
```

---

## Error Handling

### Handle Classification Errors

```python
try:
    result = classifier.classify(begrip, org_ctx, jur_ctx)

except ValueError as e:
    # Empty begrip
    st.error(f"Invalid input: {e}")

except RuntimeError as e:
    # Classification failed
    st.error(f"Classification failed: {e}")
    # Fallback: ask user to manually select level
```

### Handle Low Confidence

```python
result = classifier.classify(...)

if not result.is_reliable:
    st.warning(
        f"⚠️ Lage betrouwbaarheid ({result.confidence:.1%}). "
        "Voeg meer context toe of kies handmatig."
    )

    # Option 1: Stop and ask for more context
    if st.button("Voeg context toe"):
        # Return to context input

    # Option 2: Allow manual override
    if st.button("Kies handmatig niveau"):
        # Show manual level selector
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.getLogger("services.classification").setLevel(logging.DEBUG)
logging.getLogger("src.toetsregels.level_classifier").setLevel(logging.DEBUG)
```

### Inspect Classification Details

```python
result = classifier.classify(...)

# Print all details
print(f"Level: {result.level.value}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Confidence Level: {result.confidence_level.value}")
print(f"Rationale: {result.rationale}")
print(f"Scores: {result.scores}")
print(f"Metadata: {result.metadata}")
print(f"Is Reliable: {result.is_reliable}")
```

---

## CLI Usage (Future)

```bash
# Single term
python -m scripts.classify_term "Overeenkomst" \
    --org-context "Gemeente" \
    --jur-context "BW"

# Batch
python -m scripts.classify_batch \
    --input begrippen.csv \
    --output results.csv
```

---

## Quick Reference Table

| Use Case | Method | Returns |
|----------|--------|---------|
| Single term | `classify(begrip, ...)` | `ClassificationResult` |
| Multiple terms | `classify_batch(begrippen, ...)` | `dict[str, ClassificationResult]` |
| Validate existing | `validate_existing_definition(...)` | `(bool, Optional[str])` |
| Auto classify + generate | `adapter.generate_with_auto_classification(...)` | `(GenerationResponse, ClassificationResult)` |
| Manual classify + generate | `adapter.generate_with_classification(classification, ...)` | `GenerationResponse` |

---

## Common Issues

### Issue: Import Error

```python
# ❌ Wrong
from services.ontological_classifier import OntologicalClassifier

# ✅ Correct
from services.classification import OntologicalClassifier
```

### Issue: Classification Not Used in Generation

```python
# ❌ Wrong - classification not used
classification = classifier.classify(begrip)
request = GenerationRequest(begrip=begrip)  # Missing ontologische_categorie!

# ✅ Correct - use classification result
classification = classifier.classify(begrip)
request = GenerationRequest(
    begrip=begrip,
    ontologische_categorie=classification.to_string_level()
)
```

### Issue: Classifier Not in Container

```python
# ❌ Wrong - direct instantiation
classifier = OntologicalClassifier(ai_service)

# ✅ Correct - via DI container
container = st.session_state.service_container
classifier = container.ontological_classifier()
```

---

## Tips & Best Practices

1. **Always classify BEFORE generation** - Niveau bepaalt prompt template
2. **Use DI container** - Don't instantiate classifier directly
3. **Show classification to user** - Transparency builds trust
4. **Allow override for low confidence** - User knows context better
5. **Cache results in session state** - Avoid re-classification on rerun
6. **Log all classifications** - Useful for analysis and improvement
7. **Test with real terms** - Mock tests are good, but test with real data too

---

## See Also

- **Full Architecture**: `docs/architectuur/ontological_classifier_standalone_architecture.md`
- **Executive Summary**: `docs/architectuur/ONTOLOGICAL_CLASSIFIER_SUMMARY.md`
- **UI Examples**: `docs/examples/classifier_integration_ui.py`
- **Adapter Examples**: `docs/examples/service_adapter_with_classifier.py`
