# Src Root Analysis - Central Application Files

## Overview

This document analyzes the main application files located in the root of the src directory. These files represent the core application entry points and demonstrate the evolution of the application architecture.

## Files Analyzed

### 1. **centrale_module_definitie_kwaliteit.py** - Main Application (1089 lines)
### 2. **main.py** - Modern Entry Point (63 lines)

---

## 1. centrale_module_definitie_kwaliteit.py

### Overview
This is the main Streamlit application file that orchestrates the entire definition generation and validation workflow. It serves as the central hub for the user interface and business logic.

### Key Components

#### **Application Structure**
```python
# Imports and initialization
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Configuration
st.set_page_config(page_title="DefinitieAgent", page_icon="🧠")

# Module imports
from logs.application.log_definitie import get_logger, log_definitie
from config.config_loader import laad_toetsregels, laad_verboden_woorden
from definitie_generator.generator import genereer_definitie
from ai_toetser import toets_definitie
```

#### **Core Functions**

##### 1. **Definition Generation**
```python
def genereer_definitie(begrip, context_dict):
    """Generate definition using AI"""
    # Calls unified definition service
    # Returns raw GPT response with metadata
    
def genereer_toelichting(begrip, context=None, juridische_context=None):
    """Generate explanation for the term"""
    # Creates explanatory text
    # Uses GPT with lower temperature
```

##### 2. **Example Generation**
```python
def genereer_synoniemen(begrip, context=None):
    """Generate synonyms for the term"""
    # Max 5 synonyms
    # Government context aware
    
def genereer_antoniemen(begrip, context=None):
    """Generate antonyms for the term"""
    # Max 5 antonyms
    # Context-specific
```

#### **User Interface Architecture**

##### **Input Section**
```python
# Term input
begrip = st.text_input("Voer een term in...")

# Context selection
contextopties = st.multiselect(
    "Organisatorische context",
    ["OM", "ZM", "Reclassering", "DJI", "NP", "Justid", "KMAR", ...]
)

juridische_opties = st.multiselect(
    "Juridische context", 
    ["Strafrecht", "Civiel recht", "Bestuursrecht", ...]
)

wetopties = st.multiselect(
    "Wettelijke basis",
    ["Wetboek van Strafvordering", "Wet op de Identificatieplicht", ...]
)
```

##### **Three-Tab Interface**
```python
tab_ai, tab_aangepast, tab_expert = st.tabs([
    "🤖 AI-gegenereerde definitie",
    "✍️ Aangepaste definitie", 
    "📋 Expert-review & toelichting"
])
```

#### **Business Logic Flow**

##### **1. Definition Generation Process**
```python
if actie and begrip:
    # 1. Generate raw definition
    raw = genereer_definitie(begrip, context_dict)
    
    # 2. Parse metadata
    marker = None
    regels = raw.splitlines()
    for regel in regels:
        if regel.lower().startswith("ontologische categorie:"):
            marker = regel.split(":",1)[1].strip()
    
    # 3. Clean definition
    from opschoning.opschoning import opschonen
    definitie_gecorrigeerd = opschonen(definitie_origineel, begrip)
    
    # 4. AI validation
    st.session_state.beoordeling_gen = toets_definitie(
        definitie_gecorrigeerd,
        toetsregels,
        begrip=begrip,
        marker=marker,
        voorkeursterm=st.session_state["voorkeursterm"],
        bronnen_gebruikt=st.session_state.get("bronnen_gebruikt", None)
    )
```

##### **2. Additional Content Generation**
```python
# Generate examples and context
st.session_state.voorbeeld_zinnen = genereer_voorbeeld_zinnen(begrip, definitie_origineel, context_dict)
st.session_state.praktijkvoorbeelden = genereer_praktijkvoorbeelden(begrip, definitie_origineel, context_dict)
st.session_state.tegenvoorbeelden = genereer_tegenvoorbeelden(begrip, definitie_origineel, context_dict)
st.session_state.toelichting = genereer_toelichting(begrip, context_dict)
st.session_state.synoniemen = genereer_synoniemen(begrip, context, context_dict)
st.session_state.antoniemen = genereer_antoniemen(begrip, context, juridische_context, wet_basis)
```

#### **Tab 1: AI-Generated Definition**
```python
with tab_ai:
    st.markdown("### 📘 AI-gegenereerde definitie")
    st.markdown(st.session_state.gegenereerd)
    
    if st.session_state.get("marker"):
        st.markdown(f"**Ontologische categorie:** {st.session_state['marker']}")
    
    st.markdown("### ✨ Opgeschoonde definitie")
    st.markdown(st.session_state.get("definitie_gecorrigeerd", ""))
    
    # Examples sections
    # Synonyms with preference selection
    # Export functionality
```

#### **Tab 2: Adapted Definition**
```python
with tab_aangepast:
    st.session_state.aangepaste_definitie = st.text_area(
        "Pas de definitie aan:",
        value=st.session_state.gegenereerd,
        height=100
    )
    
    if st.button("🔁 Hercontroleer aangepaste definitie"):
        st.session_state.beoordeling = toets_definitie(
            st.session_state.aangepaste_definitie,
            toetsregels,
            begrip=begrip,
            # ... parameters
        )
```

#### **Tab 3: Expert Review**
```python
with tab_expert:
    st.session_state.expert_review = st.text_area(
        "Expert review ruimte",
        placeholder="Juridische beoordeling...",
        height=150
    )
    
    # Forbidden words management
    with st.expander("⚙️ Verboden startwoorden beheren"):
        # Permanent word list management
        # Temporary override functionality
        # Individual word testing
```

#### **Logging System**
```python
# Centralized logging for all versions
log_definitie(
    versietype="AI",
    begrip=begrip,
    context=context,
    definitie_origineel=definitie_origineel,
    definitie_gecorrigeerd=definitie_gecorrigeerd,
    toetsing=st.session_state.beoordeling_gen,
    # ... all other parameters
)
```

#### **Advanced Features**

##### **1. Forbidden Words Management**
```python
from config.verboden_woorden import laad_verboden_woorden, sla_verboden_woorden_op

# Permanent list editing
woorden_input = st.text_area(
    "Verboden startwoorden:",
    value=", ".join(huidige_lijst)
)

# Temporary override
gebruik_override = st.checkbox("Gebruik tijdelijke override")
if gebruik_override:
    tijdelijke_lijst = process_override_input(tijdelijke_input)
```

##### **2. Word Testing System**
```python
# Test individual words
test_woord = st.text_input("Te testen woord")
test_zin = st.text_input("Testzin")

if st.button("Voer test uit"):
    woord_norm = test_woord.strip().lower()
    zin_norm = test_zin.strip().lower()
    
    komt_voor = woord_norm in zin_norm
    regex_match = bool(re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm))
    
    log_test_verboden_woord(test_woord, test_zin, komt_voor, regex_match)
```

##### **3. Export Functionality**
```python
if st.button("📤 Exporteer definitie naar TXT"):
    from export import exporteer_naar_txt
    
    gegevens = {
        "begrip": st.session_state.get("begrip", ""),
        "definitie_gecorrigeerd": st.session_state.get("definitie_gecorrigeerd", ""),
        "metadata": st.session_state.get("metadata", {}),
        # ... all export data
    }
    
    pad = exporteer_naar_txt(gegevens)
    st.success(f"Geëxporteerd naar: {pad}")
```

### **Issues and Code Quality**

#### **1. Monolithic Structure**
- Single 1089-line file handles everything
- Mixed UI and business logic
- Difficult to test and maintain

#### **2. Session State Management**
- Heavy reliance on st.session_state
- Complex state interactions
- No centralized state management

#### **3. Code Organization**
- Commented-out code (lines 80-154)
- Duplicate functionality (word testing)
- Inconsistent error handling

#### **4. Performance Issues**
- Loads all toetsregels at startup
- No caching mechanisms
- Repeated expensive operations

#### **5. Security Concerns**
- Direct file operations
- No input validation
- API keys in session state

---

## 2. main.py

### Overview
Modern entry point for the application that demonstrates architectural evolution. This file shows the intended direction of the application - modular, testable, and well-structured.

### Key Components

#### **Application Structure**
```python
"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.
"""

import streamlit as st
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="DefinitieAgent",
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()

# Import modules
from logs.application.log_definitie import get_logger
from ui.session_state import SessionStateManager
from ui.tabbed_interface import TabbedInterface
from utils.exceptions import log_and_display_error
```

#### **Main Function**
```python
def main():
    """Main application function.
    
    This function is the entry point for the DefinitieAgent application.
    It initializes all required components and starts the user interface.
    
    Raises:
        Exception: All unexpected errors are logged and shown to user
    """
    try:
        # Initialize session state
        SessionStateManager.initialize_session_state()
        
        # Create and render tabbed interface
        interface = TabbedInterface()
        interface.render()
            
    except Exception as e:
        # Log and display startup errors
        logger.error(f"Application error: {str(e)}")
        st.error(log_and_display_error(e, "applicatie opstarten"))
```

### **Architectural Improvements**

#### **1. Separation of Concerns**
- UI logic separated from business logic
- Session state management centralized
- Error handling abstracted

#### **2. Modular Design**
- Clear module boundaries
- Proper import structure
- Single responsibility principle

#### **3. Error Handling**
- Centralized error logging
- User-friendly error messages
- Graceful degradation

#### **4. Documentation**
- Comprehensive docstrings
- Clear module purpose
- Usage examples

---

## Comparison: Legacy vs Modern

### **centrale_module_definitie_kwaliteit.py (Legacy)**
- **Size**: 1089 lines
- **Structure**: Monolithic
- **Concerns**: Mixed UI/business logic
- **State**: Direct st.session_state usage
- **Testing**: Difficult to test
- **Maintainability**: Low

### **main.py (Modern)**
- **Size**: 63 lines
- **Structure**: Modular
- **Concerns**: Clear separation
- **State**: Centralized management
- **Testing**: Testable design
- **Maintainability**: High

---

## Integration Analysis

### **Current State**
The application has two entry points:
1. **centrale_module_definitie_kwaliteit.py** - Active legacy implementation
2. **main.py** - Modern architecture demonstration

### **Dependencies**
Both files depend on:
- Streamlit for UI
- dotenv for configuration
- Project modules for business logic
- Logging system

### **Migration Status**
- **Legacy**: Fully functional but monolithic
- **Modern**: Architectural skeleton, needs implementation
- **Status**: Partial migration incomplete

---

## Recommendations

### **1. Complete Migration** (High Priority)
- Migrate all functionality from legacy to modern architecture
- Implement TabbedInterface with proper separation
- Test thoroughly before deprecating legacy

### **2. Refactor Legacy Code**
- Extract business logic from UI
- Create proper service layer
- Implement proper error handling

### **3. State Management**
- Implement proper session state management
- Reduce direct st.session_state usage
- Create state validation

### **4. Testing Strategy**
- Unit tests for business logic
- Integration tests for UI components
- End-to-end testing for workflows

### **5. Documentation**
- Document migration process
- Create developer guides
- Update user documentation

---

## Conclusion

The src root contains two contrasting approaches to application architecture:

**Legacy (centrale_module_definitie_kwaliteit.py)**:
- Fully functional but monolithic
- All logic in single file
- Difficult to maintain and test
- Shows application evolution

**Modern (main.py)**:
- Clean architectural pattern
- Proper separation of concerns
- Testable and maintainable
- Shows intended direction

The contrast highlights the technical debt and architectural evolution of the application. The modern approach in main.py demonstrates good practices but needs full implementation to replace the legacy system.

**Priority Actions**:
1. Complete the migration to modern architecture
2. Extract business logic from UI components
3. Implement proper testing framework
4. Create comprehensive documentation
5. Deprecate legacy entry point

This analysis reveals both the current state and the intended future of the application architecture.