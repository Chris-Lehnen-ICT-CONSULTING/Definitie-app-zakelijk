# Module 1: Monoliet vs Modulaire Aanpak

## Probleem: Monolithische Implementatie

De eerste versie van de verbeterde CoreInstructionsModule was één grote methode:

```python
def _build_role_and_basic_rules(self, begrip: str) -> str:
    # Alles in één methode:
    # - Metadata extractie
    # - Woordsoort detectie
    # - String building
    # - Conditionele logica
    # - Formatting
    # ~50 regels code in één methode
```

### Nadelen van Monolithische Aanpak
1. **Moeilijk te testen**: Je moet de hele methode testen
2. **Lage cohesie**: Verschillende verantwoordelijkheden in één methode
3. **Moeilijk uit te breiden**: Elke wijziging raakt de hele methode
4. **Code duplicatie**: Logica kan niet hergebruikt worden

## Oplossing: Modulaire Aanpak

### Architectuur

```
ModularPromptBuilder
    └── _build_role_and_basic_rules()
         ├── RoleDefinitionBuilder
         │   └── build() → "Je bent een expert..."
         ├── TaskInstructionBuilder
         │   └── build() → "**Je opdracht**:..."
         ├── WordTypeAdvisor
         │   ├── get_advice(begrip)
         │   └── _detect_word_type(begrip)
         ├── RequirementsBuilder
         │   └── build() → "**Vereisten**:..."
         └── CharacterLimitBuilder
             └── build(metadata) → "⚠️ Maximaal X karakters..."
```

### Voordelen van Modulaire Aanpak

#### 1. **Single Responsibility Principle**
Elke builder heeft één duidelijke verantwoordelijkheid:
- `RoleDefinitionBuilder`: Alleen rol definitie
- `WordTypeAdvisor`: Alleen woordsoort detectie en advies
- `CharacterLimitBuilder`: Alleen karakter limiet logica

#### 2. **Testbaarheid**
```python
def test_word_type_advisor():
    advisor = WordTypeAdvisor()
    assert advisor._detect_word_type("beheren") == "werkwoord"
    assert advisor._detect_word_type("opsporing") == "deverbaal"
    assert advisor.get_advice("beheren") == "Als het begrip een handeling..."
```

#### 3. **Herbruikbaarheid**
```python
# WordTypeAdvisor kan gebruikt worden in andere modules
class OntologicalCategoryModule:
    def __init__(self):
        self.word_advisor = WordTypeAdvisor()

    def determine_category(self, begrip):
        word_type = self.word_advisor._detect_word_type(begrip)
        # Use word type for category determination
```

#### 4. **Uitbreidbaarheid**
Nieuwe features toevoegen zonder bestaande code te raken:
```python
class ContextSensitiveRequirementsBuilder(RequirementsBuilder):
    """Uitbreiding voor context-specifieke requirements."""

    def build(self, context=None):
        base_requirements = super().build()
        if context and context.get('juridisch'):
            base_requirements += "\n• Gebruik juridische terminologie"
        return base_requirements
```

### Code Vergelijking

#### Monolithisch (Oud)
```python
def _build_role_and_basic_rules(self, begrip: str) -> str:
    metadata = getattr(self, '_current_metadata', {})
    woordsoort = self._bepaal_woordsoort(begrip)

    lines = ["Je bent een ervaren...", "", "**Je opdracht**:...", ""]

    if woordsoort == "werkwoord":
        lines.append("Als het begrip een handeling...")
    elif woordsoort == "deverbaal":
        lines.append("Als het begrip een resultaat...")
    else:
        lines.append("Gebruik een zakelijke...")

    lines.extend(["", "**Vereisten**:", "• Begin NIET...", "..."])

    max_chars = metadata.get('max_chars', 4000)
    available = max_chars - 1500
    if available < 2500:
        lines.append(f"• ⚠️ Maximaal {available}...")

    return "\n".join(lines)
```

#### Modulair (Nieuw)
```python
def _build_role_and_basic_rules(self, begrip: str) -> str:
    if not hasattr(self, '_core_builders_initialized'):
        self._initialize_core_builders()

    metadata = getattr(self, '_current_metadata', {})
    sections = []

    # Elke builder doet één ding
    sections.append(self._role_builder.build())
    sections.append(self._task_builder.build())
    sections.append(self._word_type_advisor.get_advice(begrip))
    sections.append(self._requirements_builder.build())

    limit_warning = self._limits_builder.build(metadata)
    if limit_warning:
        sections.append(limit_warning)

    return self._combine_core_sections(sections)
```

### Performance Impact

Modulaire aanpak heeft minimale performance impact:
- **Lazy loading**: Builders worden alleen geïnitialiseerd bij eerste gebruik
- **Memory**: ~5KB extra voor builder objecten
- **Execution time**: <1ms overhead door method calls

### Best Practices Toegepast

1. **Composition over Inheritance**: Gebruik builders als componenten
2. **Dependency Injection**: Builders kunnen vervangen worden voor testing
3. **Interface Segregation**: Elke builder heeft minimale interface
4. **Open/Closed Principle**: Open voor uitbreiding, gesloten voor modificatie

## Conclusie

De modulaire aanpak transformeert een 50-regel monolithische methode naar een set van kleine, gefocuste componenten. Dit maakt de code:
- ✅ Makkelijker te begrijpen
- ✅ Makkelijker te testen
- ✅ Makkelijker uit te breiden
- ✅ Makkelijker te onderhouden
- ✅ Herbruikbaar in andere contexten

Dit patroon kan toegepast worden op alle andere modules in de ModularPromptBuilder.

---
*Document created: 2025-08-26*
*Architectural pattern: Component-based design*
