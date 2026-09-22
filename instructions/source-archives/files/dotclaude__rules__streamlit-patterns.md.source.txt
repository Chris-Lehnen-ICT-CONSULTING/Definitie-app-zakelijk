# Streamlit Patterns (Verplicht)

## Key-Only Widget Pattern

```python
# GOED: Key-only, session state drives value
st.text_area("Label", key="my_key")

# FOUT: value + key veroorzaakt race conditions
st.text_area("Label", value=data, key="my_key")
```

## SessionStateManager (Altijd Gebruiken)

```python
# GOED
from ui.session_state import SessionStateManager
value = SessionStateManager.get_value("my_key", default="")
SessionStateManager.set_value("my_key", "new_value")

# FOUT - Nooit st.session_state direct
st.session_state["my_key"]  # Verboden
```

## Canonical Names (V2 Architectuur)

| Correct | Verboden |
|---------|----------|
| `ValidationOrchestratorV2` | V1, ValidationOrchestrator |
| `UnifiedDefinitionGenerator` | DefinitionGenerator |
| `ModularValidationService` | ValidationService |
| `SessionStateManager` | session_state, StateManager |
| `organisatorische_context` | organizational_context |
| `juridische_context` | legal_context |
