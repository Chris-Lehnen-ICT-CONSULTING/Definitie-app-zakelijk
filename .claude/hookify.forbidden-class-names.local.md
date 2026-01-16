---
name: forbidden-class-names
enabled: true
event: file
action: warn
conditions:
  - field: file_content
    operator: regex_match
    # Detecteert verboden class/variable namen die V1 of niet-canonical zijn
    # Let op: ValidationOrchestratorV2 is OK, maar ValidationOrchestrator zonder V2 niet
    # Negative lookahead voorkomt false positives op correcte namen
    pattern: \b(ValidationOrchestrator(?!V2)|ValidationOrchestratorV1|(?<!Unified)DefinitionGenerator|(?<!Modular)ValidationService(?!V2)|(?<!Session)StateManager|st\.session_state\[)\b
---

**VERBODEN CLASS/VARIABLE NAAM GEDETECTEERD**

Je gebruikt een verouderde of niet-canonical naam. Dit project gebruikt de **V2 architectuur**.

**Canonical Namen (verplicht):**

| Correct | Verboden |
|---------|----------|
| `ValidationOrchestratorV2` | `ValidationOrchestrator`, `V1` |
| `UnifiedDefinitionGenerator` | `DefinitionGenerator` |
| `ModularValidationService` | `ValidationService` |
| `SessionStateManager` | `StateManager`, `st.session_state[...]` |

**SessionState access:**
```python
# CORRECT
from ui.session_state import SessionStateManager
value = SessionStateManager.get_value("key", default="")
SessionStateManager.set_value("key", "value")

# WRONG - Nooit direct st.session_state gebruiken
st.session_state["key"]  # Verboden!
```

**Waarom deze regel:**
- V2 services zijn de actuele implementaties
- SessionStateManager centraliseert state management en voorkomt race conditions
- Consistente naamgeving maakt de codebase begrijpelijker

**Zie:** CLAUDE.md §Canonical Names, §Streamlit Patterns
