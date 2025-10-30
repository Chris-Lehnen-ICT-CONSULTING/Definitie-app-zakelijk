# Streamlit Best Practices & Anti-Patterns

**Status:** Active | **Last Updated:** 2025-10-29 | **Source:** DEF-56 Root Cause Analysis

Deze richtlijnen zijn gebaseerd op concrete bugs gevonden in DefinitieAgent en gevalideerd door Streamlit officiële documentatie (Context7 MCP) en deep research (Perplexity MCP).

---

## 🎯 Core Principle: Key-Only Widget Pattern

**REGEL:** Gebruik ALLEEN `key` parameter voor widgets die session state gebruiken. **NOOIT** `value` + `key` combineren.

### ✅ CORRECT Pattern

```python
import streamlit as st
from ui.session_state import SessionStateManager

# 1️⃣ Initialize session state VOOR widget declaratie
state_key = "my_text_area"
if not SessionStateManager.get_value(state_key):
    SessionStateManager.set_value(state_key, "default value")

# 2️⃣ Widget met ALLEEN key parameter
text = st.text_area(
    "Label",
    key=state_key,  # ✅ Key only
    help="Help text"
)

# 3️⃣ Gebruik widget return value of haal op uit session state
value = SessionStateManager.get_value(state_key)
```

### ❌ INCORRECT Pattern (Race Condition!)

```python
# ❌ NEVER DO THIS: value + key combinatie
text = st.text_area(
    "Label",
    value=some_variable,  # ❌ Race condition!
    key=state_key         # Widget bewaart oude state
)
```

**Waarom dit fout gaat:**
1. Widget krijgt `value="old data"` bij eerste render
2. User genereert nieuwe data → `some_variable` wordt ge-update
3. `st.rerun()` triggert page refresh
4. Widget's interne state blijft "old data" → **nieuwe `value` wordt genegeerd**
5. Result: Widget toont oude data ondanks correcte session state

---

## 🔄 State Synchronization Pattern

### Scenario: AI-Gegenereerde Content in Text Areas

**Use Case:** Genereer data met AI, vul text areas, preserveer user edits.

```python
from typing import Any
from ui.session_state import SessionStateManager

def sync_data_to_widgets(
    data: dict[str, Any],
    prefix: str,
    force_overwrite: bool = False
) -> None:
    """Sync data dictionary naar Streamlit widget session keys.

    Args:
        data: Dictionary met veld data
        prefix: Session key prefix (bijv. 'edit_42')
        force_overwrite: True = overschrijf alles (post-generatie)
                        False = preserveer bestaande values (pre-widget)
    """
    for field_name, widget_suffix in FIELD_CONFIG:
        widget_key = f"{prefix}_{widget_suffix}"

        # Skip als al gezet EN niet force (preserveer user edits)
        if not force_overwrite:
            existing = SessionStateManager.get_value(widget_key, None)
            if existing is not None:
                continue

        # Haal data op en format
        value = data.get(field_name, "")
        formatted = format_value(value)  # bijv. list → "\n".join()

        # Schrijf naar session state
        SessionStateManager.set_value(widget_key, formatted)

# VOOR widget declaratie (preserveer edits)
sync_data_to_widgets(current_data, "edit_23", force_overwrite=False)

# Declareer widgets (key-only!)
st.text_area("Field 1", key="edit_23_field1")
st.text_area("Field 2", key="edit_23_field2")

# NA AI generatie (force sync)
new_data = generate_with_ai()
sync_data_to_widgets(new_data, "edit_23", force_overwrite=True)
st.rerun()  # Widgets tonen nieuwe data na rerun
```

---

## 🏗️ Architecture Compliance

### SessionStateManager is MANDATORY

**REGEL:** Alle `st.session_state` toegang MOET via `SessionStateManager`.

#### ✅ CORRECT

```python
from ui.session_state import SessionStateManager

# Read
value = SessionStateManager.get_value("my_key", default="fallback")

# Write
SessionStateManager.set_value("my_key", new_value)

# Clear
SessionStateManager.clear_value("my_key")
```

#### ❌ INCORRECT

```python
import streamlit as st

# ❌ NEVER direct access
value = st.session_state.get("my_key")
st.session_state["my_key"] = new_value
del st.session_state["my_key"]
```

**Waarom:**
- Centrale controle over state management
- Debuggen en logging op één plek
- Voorkomt circulaire dependencies
- Consistent met DefinitieAgent architectuur

---

## 🚫 Common Anti-Patterns

### 1. Widget State Pollution

**Problem:** Widget state blijft hangen tussen tabs/sessions.

```python
# ❌ BAD: Generieke keys zonder context
st.text_input("Name", key="name")  # Conflict tussen tabs!

# ✅ GOOD: Context-specific keys
st.text_input("Name", key=f"{context}_name")
st.text_input("Name", key="edit_23_name")
```

### 2. Conditional Widget Keys

**Problem:** Widget keys veranderen tussen reruns → state verlies.

```python
# ❌ BAD: Conditie kan wijzigen
key = "edit" if editing else "view"
st.text_input("Name", key=key)  # Key wijzigt → state reset!

# ✅ GOOD: Stable keys
if editing:
    st.text_input("Name", key="name_edit")
else:
    st.text_input("Name", key="name_view", disabled=True)
```

### 3. Late State Initialization

**Problem:** Widget wordt gedeclareerd voordat session state is ge-initialiseerd.

```python
# ❌ BAD: Widget voor state init
st.text_area("Text", key="my_text")
st.session_state["my_text"] = "default"  # Te laat!

# ✅ GOOD: State voor widget
SessionStateManager.set_value("my_text", "default")
st.text_area("Text", key="my_text")
```

---

## 🧪 Testing Patterns

### Unit Test: State Synchronization

```python
import pytest
from ui.session_state import SessionStateManager
from unittest.mock import patch, MagicMock

@patch('streamlit.session_state', new_callable=dict)
def test_sync_preserves_user_edits(mock_session_state):
    """Test dat sync user edits NIET overschrijft."""
    # Setup: User heeft edit gemaakt
    SessionStateManager.set_value("edit_23_field1", "user edit")

    # Act: Sync nieuwe data met force_overwrite=False
    new_data = {"field1": "ai generated"}
    sync_data_to_widgets(new_data, "edit_23", force_overwrite=False)

    # Assert: User edit is gepreserveerd
    assert SessionStateManager.get_value("edit_23_field1") == "user edit"

@patch('streamlit.session_state', new_callable=dict)
def test_sync_force_overwrite(mock_session_state):
    """Test dat force sync user edits WEL overschrijft."""
    # Setup: User heeft edit gemaakt
    SessionStateManager.set_value("edit_23_field1", "user edit")

    # Act: Sync met force_overwrite=True
    new_data = {"field1": "ai generated"}
    sync_data_to_widgets(new_data, "edit_23", force_overwrite=True)

    # Assert: AI data heeft user edit overschreven
    assert SessionStateManager.get_value("edit_23_field1") == "ai generated"
```

### Integration Test: Widget Behavior

```python
from streamlit.testing.v1 import AppTest

def test_text_area_populates_after_generation():
    """Test dat text areas gevuld worden na AI generatie."""
    at = AppTest.from_file("src/main.py")
    at.run()

    # Navigate to Bewerk tab
    at.sidebar.selectbox[0].select("Bewerk definitie")
    at.run()

    # Trigger generation
    generate_button = at.button("✨ Genereer voorbeelden (AI)")
    generate_button.click()
    at.run()

    # Assert: Text areas are populated
    text_areas = at.text_area
    assert len(text_areas[0].value) > 0  # Voorbeeldzinnen
    assert len(text_areas[1].value) > 0  # Praktijkvoorbeelden
```

---

## 📋 Pre-Flight Checklist

**Voor elke nieuwe Streamlit component:**

- [ ] Widget gebruikt key-only pattern (GEEN `value` parameter)
- [ ] Session state geïnitialiseerd VOOR widget declaratie
- [ ] Key is context-specific (geen generieke keys)
- [ ] SessionStateManager gebruikt (GEEN directe `st.session_state`)
- [ ] Conditional logic beïnvloedt NIET widget keys
- [ ] Error handling voor state access
- [ ] Unit tests voor state sync logic

---

## 🔍 Debugging Tips

### Widget Toont Verkeerde Data

**Symptoom:** Widget content komt niet overeen met session state.

**Checklist:**
1. ✅ Check widget gebruikt key-only pattern (geen `value`)
2. ✅ Check session state is ge-set VOOR widget declaratie
3. ✅ Check widget key is correct (geen typo's)
4. ✅ Log session state value direct voor widget:
   ```python
   value = SessionStateManager.get_value("my_key")
   logger.debug(f"Session state voor widget: {value}")
   st.text_area("Label", key="my_key")
   ```

### State Verdwijnt Na Rerun

**Symptoom:** Widget reset naar lege value na `st.rerun()`.

**Checklist:**
1. ✅ Check widget key is stable (wijzigt NIET tussen reruns)
2. ✅ Check geen conditional logic wijzigt key
3. ✅ Check session state wordt NIET cleared tijdens rerun
4. ✅ Gebruik Streamlit Session State viewer:
   ```python
   if st.checkbox("Debug Session State"):
       st.write("Session State:", dict(st.session_state))
   ```

---

## 📚 References

- **DEF-56 Root Cause Analysis:** `docs/backlog/EPIC-XXX/US-XXX/DEF-56/DEF-56.md`
- **Streamlit Docs (Context7):** Widget state management best practices
- **Perplexity Research:** Streamlit widget lifecycle and race conditions
- **SessionStateManager:** `src/ui/session_state.py`

---

## ✅ Enforcement

**Pre-Commit Hook:** Detecteer Streamlit anti-patterns

```bash
# .pre-commit-config.yaml
- id: streamlit-anti-patterns
  name: Check Streamlit Anti-Patterns
  entry: python scripts/check_streamlit_patterns.py
  language: system
  files: 'src/ui/.*\.py$'
```

**Automated Checks:**
- ❌ Detect `st.text_area(value=..., key=...)` combinatie
- ❌ Detect direct `st.session_state[...]` access in UI modules
- ❌ Detect generieke widget keys ("name", "text", etc.)
- ✅ Enforce SessionStateManager import in UI modules

---

**Status:** Deze patterns zijn gevalideerd door DEF-56 fix en moeten worden toegepast op ALLE Streamlit components in DefinitieAgent.
