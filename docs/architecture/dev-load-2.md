# Dev Load 2: UI Components & State Management

## Overview

Dit document beschrijft de Streamlit UI architectuur, componenten, en session state management voor DefinitieAgent.

## UI Architecture

### Tab Structure (10 tabs)

```python
TABS = {
    "🏠 Definitie Generator": definition_generator_tab,     # ✅ Werkend
    "✅ Kwaliteitscontrole": quality_control_tab,          # ✅ Basis werkend
    "👥 Expert Review": expert_review_tab,                 # ⚠️ Gedeeltelijk
    "📊 Management": management_tab,                       # ❌ Niet werkend
    "🎭 Orchestratie": orchestration_tab,                 # ❌ Niet werkend
    "📜 Geschiedenis": history_tab,                       # ✅ Werkend
    "💾 Export": export_tab,                             # ⚠️ Basis alleen
    "📈 Monitoring": monitoring_tab,                      # ❌ Niet werkend
    "🌐 Externe Bronnen": external_sources_tab,          # ❌ Niet werkend
    "🔍 Web Lookup": web_lookup_tab                      # ❌ Niet werkend
}
```

### Session State Structure

```python
# Core session state keys
st.session_state = {
    # Current definition
    'current_term': str,
    'current_definition': str,
    'current_context': str,
    'validation_results': dict,
    'ontology_score': float,
    
    # History
    'definition_history': list,
    'selected_definition_id': int,
    
    # UI State
    'active_tab': str,
    'show_prompt': bool,
    'edit_mode': bool,
    'developer_mode': bool,
    
    # Cached data
    'cached_prompts': dict,
    'cached_validations': dict,
    
    # Settings
    'temperature': float,
    'model': str,
    'validation_rules': list
}
```

## Component Patterns

### 1. Tab Component Structure

```python
def tab_component():
    # Header
    st.header("Tab Naam")
    
    # Sidebar controls
    with st.sidebar:
        # Tab-specific settings
        
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Primary content
        
    with col2:
        # Secondary/info content
        
    # Actions
    if st.button("Action"):
        # Handle action
```

### 2. Form Patterns

```python
# Definition generation form
with st.form("definition_form"):
    term = st.text_input("Begrip", key="term_input")
    context = st.text_area("Context", key="context_input")
    
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3)
    with col2:
        model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"])
    
    submitted = st.form_submit_button("Genereer")
```

### 3. Display Components

```python
# Definition display with metadata
def display_definition(definition_data):
    # Main definition
    st.info(definition_data['definition'])
    
    # Metadata in expander
    with st.expander("Details"):
        st.json({
            "Score": definition_data['score'],
            "Model": definition_data['model'],
            "Context": definition_data['context']
        })
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Kopieer"):
            st.write("Gekopieerd!")
    with col2:
        if st.button("✏️ Bewerk"):
            st.session_state.edit_mode = True
    with col3:
        if st.button("💾 Bewaar"):
            save_definition(definition_data)
```

## Legacy UI Recovery Guide

### From centrale_module_definitie_kwaliteit_legacy.py

**Key UI elements to restore:**

1. **Prompt Viewer**
```python
# Show full prompt with copy button
with st.expander("🔍 Bekijk Prompt"):
    st.code(prompt, language='text')
    if st.button("📋 Kopieer Prompt"):
        pyperclip.copy(prompt)
        st.success("Prompt gekopieerd!")
```

2. **Score Visualisatie**
```python
# Ontology score display
score_col1, score_col2 = st.columns(2)
with score_col1:
    st.metric("Validatie Score", f"{validation_score}%")
with score_col2:
    st.metric("Ontologie Score", f"{ontology_score:.1f}/10")
```

3. **Edit Mode**
```python
# Inline definition editing
if st.session_state.get('edit_mode'):
    edited = st.text_area("Pas definitie aan:", 
                         value=current_definition,
                         height=200)
    if st.button("💾 Opslaan"):
        st.session_state.current_definition = edited
        st.session_state.edit_mode = False
```

## Widget Key Management

### Current Bug
```python
# PROBLEEM: Random keys veroorzaken widget reset
key = f"widget_{random.randint(1000, 9999)}"  # ❌ FOUT

# OPLOSSING: Stabiele keys based op context
key = f"widget_{tab_name}_{widget_type}_{index}"  # ✅ GOED
```

### Key Generator Pattern
```python
class WidgetKeyManager:
    @staticmethod
    def get_key(prefix: str, suffix: str = "") -> str:
        """Generate stable widget key"""
        base = f"{prefix}_{st.session_state.get('active_tab', 'default')}"
        if suffix:
            return f"{base}_{suffix}"
        return base
```

## State Management Best Practices

### 1. Initialize State
```python
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'definition_history': [],
        'current_term': '',
        'validation_results': {},
        'developer_mode': False
    }
    
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
```

### 2. State Callbacks
```python
def on_term_change():
    """Callback when term changes"""
    st.session_state.definition_generated = False
    st.session_state.validation_results = {}

# Usage
st.text_input("Term", key="term", on_change=on_term_change)
```

### 3. State Persistence
```python
# Save state to database
def persist_state():
    state_data = {
        'term': st.session_state.current_term,
        'definition': st.session_state.current_definition,
        'timestamp': datetime.now()
    }
    save_to_db(state_data)
```

## Common UI Patterns

### 1. Loading States
```python
with st.spinner("Definitie wordt gegenereerd..."):
    result = generate_definition(term)
```

### 2. Error Handling
```python
try:
    result = process_action()
    st.success("✅ Actie succesvol uitgevoerd!")
except Exception as e:
    st.error(f"❌ Fout: {str(e)}")
```

### 3. Progress Indicators
```python
progress = st.progress(0)
for i in range(100):
    progress.progress(i + 1)
    # Do work
```

### 4. Conditional Display
```python
if st.session_state.get('developer_mode'):
    with st.expander("🔧 Developer Info"):
        st.json(debug_info)
```

## Tab Implementation Status

| Tab | Status | Missing Features |
|-----|--------|------------------|
| Definitie Generator | ✅ 90% | Metadata fields activation |
| Kwaliteitscontrole | ✅ 70% | Detailed rule explanations |
| Expert Review | ⚠️ 40% | Review workflow |
| Management | ❌ 0% | Full implementation |
| Orchestratie | ❌ 10% | Multi-agent coordination |
| Geschiedenis | ✅ 80% | Search functionality |
| Export | ⚠️ 50% | PDF export |
| Monitoring | ❌ 0% | Metrics dashboard |
| Externe Bronnen | ❌ 20% | Upload improvements |
| Web Lookup | ❌ 0% | UTF-8 fix needed |

## Performance Optimizations

### 1. Caching
```python
@st.cache_data
def expensive_operation(param):
    return compute_result(param)
```

### 2. Lazy Loading
```python
if st.checkbox("Show advanced options"):
    # Only load when needed
    advanced_component()
```

### 3. Batch Updates
```python
# Update multiple state variables at once
for key, value in updates.items():
    st.session_state[key] = value
```

---
*Dit document wordt automatisch geladen door BMAD dev agents*