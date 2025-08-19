# Epic 3: UI Quick Wins

**Epic Goal**: Verbeter direct zichtbare UI issues voor betere gebruikerservaring.

**Business Value**: Verhoog gebruikerstevredenheid met kleine maar impactvolle fixes.

**Total Story Points**: 8

**Target Sprint**: 2

## Stories

### STORY-003-01: Fix Widget Key Generator

**Story Points**: 2

**Als een** developer
**wil ik** unieke widget keys genereren
**zodat** Streamlit geen duplicate key errors geeft.

#### Acceptance Criteria
- [ ] Widget key generator functie gefixt
- [ ] Geen duplicate key warnings in console
- [ ] Keys persistent over reruns
- [ ] Unit test voor key generator

#### Root Cause
Het huidige systeem genereert keys gebaseerd op widget type + index, wat faalt bij dynamische UI updates.

#### Solution
```python
import hashlib
from typing import Any

def generate_widget_key(widget_type: str, *args: Any) -> str:
    """Generate unique, stable widget key."""
    # Combine all identifying information
    key_parts = [widget_type] + [str(arg) for arg in args]
    key_string = "_".join(key_parts)

    # Create stable hash for long keys
    if len(key_string) > 50:
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    return key_string

# Usage
key = generate_widget_key("selectbox", "term_input", tab_name, row_index)
```

#### Test Cases
- Dynamic list rendering
- Tab switching
- Form resets
- Concurrent users

---

### STORY-003-02: Activeer Term Input Field

**Story Points**: 1

**Als een** gebruiker
**wil ik** direct een term invoeren op de homepage
**zodat** ik snel kan beginnen.

#### Acceptance Criteria
- [ ] Input field prominent op homepage
- [ ] Enter key triggert definitie generatie
- [ ] Placeholder text met voorbeeld
- [ ] Focus op page load

#### Implementation
```python
# In main app.py
def render_homepage():
    st.title("🔍 DefinitieAgent")

    # Auto-focus input field
    term = st.text_input(
        "Voer een term in",
        placeholder="Bijvoorbeeld: aansprakelijkheid",
        key="main_term_input",
        on_change=trigger_generation
    )

    # Enter key handling
    if term and st.session_state.get('enter_pressed'):
        generate_definition(term)
```

#### UX Requirements
- Input field minstens 60% viewport breedte
- Contrast ratio 4.5:1 voor accessibility
- Clear button altijd zichtbaar

---

### STORY-003-03: Fix Session State Persistence

**Story Points**: 3

**Als een** gebruiker
**wil ik** dat mijn data bewaard blijft
**zodat** ik niet opnieuw moet invoeren na reload.

#### Acceptance Criteria
- [ ] Form data persist bij page reload
- [ ] Tab selectie blijft behouden
- [ ] Definitie geschiedenis beschikbaar
- [ ] Clear session optie toegevoegd

#### Session State Structure
```python
# Initialize session state properly
def init_session_state():
    defaults = {
        'current_tab': 0,
        'term_history': [],
        'current_term': '',
        'current_definition': None,
        'form_data': {},
        'user_preferences': {
            'temperature': 0.3,
            'model': 'gpt-4',
            'context': 'juridisch'
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Persist form data
def save_form_data(form_key: str, data: dict):
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    st.session_state.form_data[form_key] = data
```

#### Edge Cases
- Browser refresh
- Back button
- Multiple tabs open
- Session timeout

---

### STORY-003-04: Toon Metadata Velden

**Story Points**: 2

**Als een** gebruiker
**wil ik** metadata van definities zien
**zodat** ik context heb over de gegenereerde content.

#### Acceptance Criteria
- [ ] Context type zichtbaar (juridisch/algemeen/etc)
- [ ] Model versie getoond
- [ ] Temperature setting zichtbaar
- [ ] Timestamp van generatie

#### UI Layout
```python
def display_definition_metadata(definition: Definition):
    """Show metadata in collapsed expander."""
    with st.expander("📊 Metadata", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Context", definition.context_type)
            st.metric("Model", definition.model_version)

        with col2:
            st.metric("Temperature", f"{definition.temperature:.1f}")
            st.metric("Tokens", definition.token_count)

        with col3:
            st.metric("Score", f"{definition.validation_score}%")
            st.caption(f"Gegenereerd: {definition.created_at}")
```

#### Metadata Fields
- Context: juridisch/algemeen/technisch/medisch
- Model: gpt-4/gpt-3.5-turbo
- Temperature: 0.0-1.0
- Validation score: 0-100%
- Token usage: prompt/completion/total
- Generation time: timestamp

## Definition of Done (Epic Level)

- [ ] Alle 4 stories completed
- [ ] Geen UI errors in console
- [ ] User feedback positief
- [ ] Performance niet gedegradeerd
- [ ] Mobile responsive waar mogelijk
- [ ] Documentatie bijgewerkt

## Testing Strategy

### Manual Testing
1. Test op verschillende browsers
2. Test met verschillende schermgroottes
3. Test met 5+ concurrent users
4. Test session persistence scenarios

### Automated Testing
```python
# Widget key generator tests
def test_unique_keys():
    key1 = generate_widget_key("input", "term", 1)
    key2 = generate_widget_key("input", "term", 2)
    assert key1 != key2

def test_stable_keys():
    key1 = generate_widget_key("input", "term", 1)
    key2 = generate_widget_key("input", "term", 1)
    assert key1 == key2
```

## Success Metrics

- Zero duplicate key errors
- Session state complaints -90%
- Time to first action <3 seconds
- User satisfaction score +20%

## UI Style Guide

- Primary color: #1E88E5
- Success color: #43A047
- Error color: #E53935
- Font: Inter/system default
- Border radius: 4px
- Shadow: subtle (0 2px 4px rgba(0,0,0,0.1))

---
*Epic owner: Frontend Team*
*Last updated: 2025-01-18*
