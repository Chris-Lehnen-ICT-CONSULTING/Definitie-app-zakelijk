# 🏗️ MODULAIRE PROMPT ARCHITECTUUR - IMPLEMENTATION WORKFLOW

**Versie**: 1.0
**Datum**: 2025-08-26
**Status**: Ready for Implementation
**Referentie**: SERVICE_ARCHITECTUUR_IMPLEMENTATIE_BLAUWDRUK.md - Sectie 3

---

## 🎯 DOEL

Implementeer **ModularPromptBuilder** die de monolithische LegacyPromptBuilder vervangt door **6 configureerbare componenten** die samen de volledige 17k karakter ESS-02 prompt vormen.

### ✅ SUCCESS CRITERIA

- ✅ **Functionaliteit behouden**: Genereert nog steeds 17k karakter ESS-02 prompt
- ✅ **Modulaire flexibiliteit**: Elke component apart configureerbaar
- ✅ **Category intelligence**: Verschillende guidance per ontologische categorie
- ✅ **Performance maintained**: <5s response tijd behouden
- ✅ **Test coverage**: >95% voor alle componenten
- ✅ **Backward compatible**: Bestaande functionaliteit ongewijzigd

---

## 📋 WORKFLOW STAPPEN

### FASE 1: Foundation Components 🏗️

#### Stap 1.1: Maak ModularPromptBuilder Basis
```bash
# Agent: James (Development specialist)
# Taak: Implementeer basis klasse en configuratie
```

**Deliverables**:
- `src/services/prompts/modular_prompt_builder.py` - Basis klasse
- `PromptComponentConfig` dataclass - Configuratie systeem
- `ModularPromptBuilder.__init__()` en `build_prompt()` framework

#### Stap 1.2: Implementeer Component 1 & 2
```bash
# Agent: James
# Taak: Rol & Context componenten (eenvoudigste eerst)
```

**Deliverables**:
- `_build_role_and_basic_rules(begrip)` methode
- `_build_context_section(context)` methode
- Unit tests voor beide componenten

#### Stap 1.3: Basis Integration Test
```bash
# Agent: James
# Taak: Test dat basis framework werkt
```

**Deliverables**:
- `tests/test_modular_prompt_builder.py` - Basis test setup
- Test dat componenten correct worden samengevoegd
- Performance baseline meting

---

### FASE 2: Core Functionality 🎯

#### Stap 2.1: Implementeer Component 3 (KRITISCH) ⭐
```bash
# Agent: James
# Taak: Ontologische categorie sectie - MEEST COMPLEXE COMPONENT
```

**Deliverables**:
- `_build_ontological_section(context)` methode
- Category-specific guidance voor alle 4 categorieën:
  - "proces" → "activiteit waarbij..."
  - "type" → "soort..."
  - "resultaat" → "resultaat van..."
  - "exemplaar" → "specifiek exemplaar van..."
- Unit tests per categorie

#### Stap 2.2: Category Intelligence Testing
```bash
# Agent: James
# Taak: Valideer dat verschillende categories verschillende prompts genereren
```

**Deliverables**:
- `test_category_specific_guidance()` test
- Verificatie dat 4 categorieën → 4 unieke prompts
- Integration test met V2 orchestrator

---

### FASE 3: Complete Feature Set 📝

#### Stap 3.1: Implementeer Component 4 (Validatie Regels)
```bash
# Agent: James
# Taak: Alle ESS-02 toetsregels gegroepeerd per categorie
```

**Deliverables**:
- `_build_validation_rules_section()` methode
- Gegroepeerd per: STR, ESS, CON, INT, SAM
- Voorbeelden per regel (✅/❌ patterns)

#### Stap 3.2: Implementeer Component 5 (Verboden Patronen)
```bash
# Agent: James
# Taak: Praktische gids voor veelgemaakte fouten
```

**Deliverables**:
- `_build_forbidden_patterns_section()` methode
- Verboden startwoorden, patronen, context-specifieke regels
- Positieve alternatieven

#### Stap 3.3: Implementeer Component 6 (Finale Instructies)
```bash
# Agent: James
# Taak: Afsluitende instructies en metadata
```

**Deliverables**:
- `_build_final_instructions_section(begrip, context)` methode
- Ontologische marker, promptmetadata, finale opdracht
- Configureerbare component metadata

---

### FASE 4: Integration & Deployment 🚀

#### Stap 4.1: UnifiedPromptBuilder Integratie
```bash
# Agent: James
# Taak: Integreer ModularPromptBuilder in bestaande architectuur
```

**Deliverables**:
- Update `src/services/definition_generator_prompts.py`:
  - `_initialize_builders()` - Voeg "modular" toe
  - `_select_strategy()` - Prioriteit: modular > legacy > basic
- Strategy selectie logic voor ontological categories

#### Stap 4.2: V2 Orchestrator Integration
```bash
# Agent: James
# Taak: Test volledige integration met DefinitionOrchestratorV2
```

**Deliverables**:
- Integration test: V2 orchestrator → ModularPromptBuilder → Volledige prompt
- Performance validatie: <5s response tijd behouden
- Logging & monitoring voor prompt generation metadata

#### Stap 4.3: Comprehensive Testing Suite
```bash
# Agent: James
# Taak: Volledige test coverage en edge cases
```

**Deliverables**:
- `test_full_prompt_generation()` - Alle componenten samen
- `test_configurable_components()` - Component in/uitschakeling
- `test_backward_compatibility()` - Legacy prompt vergelijking
- Edge case tests (geen context, onbekende categorie, etc.)

---

### FASE 5: Code Review & Validation 🔍

#### Stap 5.1: Automated Code Review
```bash
# Tool: bmad-post-edit-hook.sh
# Agent: James
# Taak: Kwaliteitscontrole en formatting
```

**Deliverables**:
- Ruff/Black formatting van alle nieuwe files
- Code review rapport
- Performance profiling resultaten

#### Stap 5.2: Manual Code Review
```bash
# Agent: James
# Taak: Architecture compliance en best practices
```

**Deliverables**:
- Architecture compliance check tegen blauwdruk
- Security review (geen PII exposure in prompts)
- Documentation completeness check

#### Stap 5.3: User Acceptance Testing
```bash
# Agent: James
# Taak: Test met echte use cases
```

**Deliverables**:
- Test met "voorwaardelijk" (proces) - referentie case
- Test met alle 4 ontologische categorieën
- Prompt kwaliteit vergelijking: Legacy vs Modular
- Performance benchmark: response tijd < 5s

---

## 🎮 AGENT SELECTIE RICHTLIJNEN

### **James** (Full Stack Developer) 💻
- **Gebruik voor**: Alle implementatie stappen
- **Waarom**: Ervaring met ModularPromptBuilder concept, V2 orchestrator kennis
- **Focus**: Code quality, testing, performance

### **Andere Agents** (indien nodig)
- **Search Agent**: Alleen voor dependency analysis of complex codebase searches
- **Niet gebruiken voor**: Deze workflow is development-focused, James heeft alle benodigde skills

---

## 🧪 TESTING STRATEGIE PER FASE

### Fase 1 Testing:
```python
def test_basic_framework():
    """Test dat ModularPromptBuilder framework werkt."""
    builder = ModularPromptBuilder()
    context = create_test_context()

    # Test dat componenten worden geladen
    prompt = builder.build_prompt("test", context, config)
    assert len(prompt) > 1000
    assert "expert in beleidsmatige definities" in prompt
```

### Fase 2 Testing:
```python
def test_category_intelligence():
    """Test category-specific guidance generation."""
    categories = ["proces", "type", "resultaat", "exemplaar"]

    for category in categories:
        context = create_test_context(ontologische_categorie=category)
        prompt = builder.build_prompt("test", context, config)

        # Elke categorie moet unieke guidance hebben
        assert category in prompt.lower()
        assert category_specific_keywords[category] in prompt
```

### Fase 3 Testing:
```python
def test_complete_prompt_generation():
    """Test volledige prompt met alle componenten."""
    prompt = builder.build_prompt("voorwaardelijk", full_context, config)

    # Alle 6 componenten aanwezig
    assert "expert in beleidsmatige definities" in prompt  # Component 1
    assert "📌 Context:" in prompt                        # Component 2
    assert "ESS-02" in prompt                             # Component 3
    assert "STR-01" in prompt                             # Component 4
    assert "Veelgemaakte fouten" in prompt               # Component 5
    assert "voorwaardelijk" in prompt                    # Component 6

    # Lengte check (moet vergelijkbaar zijn met legacy)
    assert 15000 < len(prompt) < 20000
```

---

## 🚀 EXECUTION COMMANDS

### Start Workflow:
```bash
# Activeer James agent
/dev

# Begin met Fase 1
*help
# Selecteer: implement ModularPromptBuilder foundation

# Voor elke fase:
# 1. Implementeer code
# 2. Run tests: python -m pytest tests/test_modular_prompt_builder.py -v
# 3. Run code review: source .bmad-core/utils/bmad-post-edit-hook.sh
# 4. Valideer resultaten tegen SUCCESS CRITERIA
```

### Quick Reference Commands:
```bash
# Test current implementation
python -m pytest tests/test_modular_prompt_builder.py::TestModularPromptBuilder::test_category_specific_guidance -v

# Test integration with V2 orchestrator
python -m pytest tests/test_ontological_category_fix.py -v

# Performance benchmark
python3 -c "from services.prompts.modular_prompt_builder import ModularPromptBuilder; # benchmark code"

# Code review
source .bmad-core/utils/bmad-post-edit-hook.sh && trigger_post_edit_review "James" "src/services/prompts/"
```

---

## 📊 PROGRESS TRACKING

### Fase 1: Foundation Components (25%)
- [ ] ModularPromptBuilder basis klasse
- [ ] PromptComponentConfig
- [ ] Component 1: Rol & Basis Instructies
- [ ] Component 2: Context Sectie
- [ ] Basis unit tests

### Fase 2: Core Functionality (50%)
- [ ] Component 3: Ontologische Categorie Sectie ⭐
- [ ] Category-specific guidance (4 categorieën)
- [ ] Integration tests category switching
- [ ] V2 orchestrator integration test

### Fase 3: Complete Feature Set (75%)
- [ ] Component 4: Validatie Regels Sectie
- [ ] Component 5: Verboden Patronen Sectie
- [ ] Component 6: Afsluitende Instructies
- [ ] Configureerbare componenten
- [ ] Comprehensive test suite

### Fase 4: Integration & Deployment (90%)
- [ ] UnifiedPromptBuilder integratie
- [ ] Strategy selectie update
- [ ] Performance validatie <5s
- [ ] Backward compatibility check

### Fase 5: Code Review & Validation (100%)
- [ ] Automated code review (ruff/black)
- [ ] Architecture compliance check
- [ ] User acceptance testing
- [ ] Documentation update

---

## 🎯 READY TO START!

**Next Action**: Activeer James agent en begin met Fase 1.1 - ModularPromptBuilder Basis implementatie!

```bash
/dev
# Begin implementation workflow!
```
