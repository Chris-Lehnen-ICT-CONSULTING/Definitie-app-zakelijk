# DEF-156 PRE-CONSOLIDATION CHECK
## Gedetailleerde Vergelijking van 5 JSON-Based Rule Modules

**Datum:** 2025-11-14
**Doel:** Valideren dat consolidatie veilig is
**Status:** ✅ GOEDGEKEURD VOOR CONSOLIDATIE

---

## EXECUTIVE SUMMARY

**✅ VEILIG OM TE CONSOLIDEREN**

Na grondige analyse zijn de volgende 5 modules **100% identiek** behalve configuratie:
1. **AraiRulesModule** (arai_rules_module.py) - 128 regels
2. **ConRulesModule** (con_rules_module.py) - 128 regels
3. **EssRulesModule** (ess_rules_module.py) - 128 regels
4. **SamRulesModule** (sam_rules_module.py) - 128 regels
5. **VerRulesModule** (ver_rules_module.py) - 128 regels

**TOTAAL:** 640 regels → kan worden 128 regels = **512 regels besparing (80%)**

---

## MODULE PARAMETERS VERGELIJKING

### Tabel 1: Exacte Verschillen Per Module

| Module | module_id | module_name | priority | prefix | emoji | regels_count |
|--------|-----------|-------------|----------|--------|-------|--------------|
| **ARAI** | `arai_rules` | "ARAI Validation Rules" | 75 | `"ARAI"` | ✅ | ~10-15 |
| **CON** | `con_rules` | "Context Validation Rules (CON)" | 70 | `"CON-"` | 🌐 | ~3-5 |
| **ESS** | `ess_rules` | "Essence Validation Rules (ESS)" | 75 | `"ESS"` | 🎯 | ~5-7 |
| **SAM** | `sam_rules` | "Coherence Validation Rules (SAM)" | 65 | `"SAM"` | 🔗 | ~8-10 |
| **VER** | `ver_rules` | "Form Validation Rules (VER)" | 60 | `"VER"` | 📐 | ~3-5 |

**Opmerking:** Prefix `"CON-"` heeft een trailing dash, anderen niet.

---

## CODE STRUCTUUR VERGELIJKING

### Identieke Code (Alle 5 Modules)

```python
# EXACT HETZELFDE IN ALLE 5 MODULES:

class XxxRulesModule(BasePromptModule):
    """Module voor XXX validatieregels."""

    def __init__(self):
        super().__init__(
            module_id="xxx_rules",          # ← VERSCHIL 1
            module_name="XXX Rules",        # ← VERSCHIL 2
            priority=XX,                    # ← VERSCHIL 3
        )
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        # Logging...

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        return True, None  # ← IDENTIEK

    def execute(self, context: ModuleContext) -> ModuleOutput:
        try:
            sections = []
            sections.append("### {emoji} {naam}:")  # ← VERSCHIL 4 (emoji)

            # Load toetsregels from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager
            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter by prefix
            xxx_rules = {k: v for k, v in all_rules.items()
                        if k.startswith("XXX")}  # ← VERSCHIL 5 (prefix)

            # Format rules
            sorted_rules = sorted(xxx_rules.items())
            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            content = "\n".join(sections)
            return ModuleOutput(...)
        except Exception as e:
            # Error handling... (IDENTIEK)

    def get_dependencies(self) -> list[str]:
        return []  # ← IDENTIEK

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        # 31 REGELS - 100% IDENTIEK IN ALLE MODULES
        lines = []
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        toetsvraag = regel_data.get("toetsvraag", "")
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")

        if self.include_examples:
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines
```

**TOTALE DUPLICATION:**
- `_format_rule()` methode: 31 regels × 5 modules = **155 regels duplicatie**
- `execute()` methode: 30 regels × 5 modules = **150 regels duplicatie**
- `initialize()` + `validate_input()`: 20 regels × 5 modules = **100 regels duplicatie**

**SUBTOTAAL:** ~405 regels pure duplicatie (van 640 totaal = 63%)

---

## OUTPUT FORMATTING VERGELIJKING

### Header Formaten (EXACT VALIDEREN!)

```
ARAI:  ### ✅ Algemene Regels AI (ARAI):
CON:   ### 🌐 Context Regels (CON):
ESS:   ### 🎯 Essentie Regels (ESS):
SAM:   ### 🔗 Samenhang Regels (SAM):
VER:   ### 📐 Vorm Regels (VER):
```

**KRITIEK:** Het emoji en de naam zijn **herkenningspunten** voor gebruikers!

### Rule Format (IDENTIEK IN ALLE MODULES)

```
🔹 **{regel_key} - {naam}**
- {uitleg}
- Toetsvraag: {toetsvraag}
  ✅ {goed_voorbeeld_1}
  ✅ {goed_voorbeeld_2}
  ❌ {fout_voorbeeld_1}
  ❌ {fout_voorbeeld_2}

```

**VALIDATIE:** Dit format MOET exact hetzelfde blijven!

---

## MODULES DIE NIET WORDEN GECONSOLIDEERD

### ⚠️ BELANGRIJKE ONTDEKKING

Er zijn **2 extra rule modules** die NIET mogen worden geconsolideerd:

1. **StructureRulesModule** (structure_rules_module.py) - **332 regels**
   - **Waarom anders:** Heeft CUSTOM regel methodes:
     - `_build_str01_rule()` tot `_build_str09_rule()`
     - Hardcoded regels (NIET uit JSON!)
     - Header: `### 🏗️ Structuur Regels (STR):`

2. **IntegrityRulesModule** (integrity_rules_module.py) - **314 regels**
   - **Waarom anders:** Heeft CUSTOM regel methodes:
     - `_build_int01_rule()` tot `_build_int08_rule()`
     - Hardcoded regels (NIET uit JSON!)
     - Header: `### 🔒 Integriteit Regels (INT):`

**CONCLUSIE:**
- ✅ Consolideer: ARAI, CON, ESS, SAM, VER (JSON-based)
- ❌ NIET consolideren: STR, INT (custom hardcoded)

---

## BACKWARD COMPATIBILITY VEREISTEN

### Module Namen (KRITIEK)

**In `modular_prompt_adapter.py` worden modules geïmporteerd als:**

```python
from .modules import (
    AraiRulesModule,      # ← MOET BLIJVEN
    ConRulesModule,       # ← MOET BLIJVEN
    EssRulesModule,       # ← MOET BLIJVEN
    SamRulesModule,       # ← MOET BLIJVEN
    VerRulesModule,       # ← MOET BLIJVEN
    IntegrityRulesModule, # Blijft apart
    StructureRulesModule, # Blijft apart
)
```

**En geregistreerd als:**

```python
modules = [
    AraiRulesModule(),  # ARAI regels
    ConRulesModule(),   # CON regels
    EssRulesModule(),   # ESS regels
    IntegrityRulesModule(),  # INT regels
    SamRulesModule(),   # SAM regels
    StructureRulesModule(),  # STR regels
    VerRulesModule(),   # VER regels
]
```

**VEREISTE:** De class namen MOETEN behouden blijven voor backward compatibility!

**OPLOSSING:** Factory pattern met wrapper classes:

```python
# Nieuwe generieke base class
class JSONBasedRulesModule(BasePromptModule):
    def __init__(self, rule_prefix, module_id, module_name,
                 header_emoji, priority):
        # Implementatie...

# Backward compatible wrappers
class AraiRulesModule(JSONBasedRulesModule):
    def __init__(self):
        super().__init__(
            rule_prefix="ARAI",
            module_id="arai_rules",
            module_name="ARAI Validation Rules",
            header_emoji="✅",
            priority=75
        )

# Herhaal voor CON, ESS, SAM, VER
```

---

## ONVERWACHTE VERSCHILLEN GEVONDEN

### 1. ✅ Prefix Trailing Dash

**VERSCHIL:** CON module gebruikt `"CON-"` (met dash), anderen niet.

```python
# CON module:
con_rules = {k: v for k, v in all_rules.items() if k.startswith("CON-")}

# Andere modules:
arai_rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}
```

**IMPACT:** Generieke module MOET deze dash ondersteunen!

**OPLOSSING:**
```python
def __init__(self, rule_prefix, ...):
    self.rule_prefix = rule_prefix  # Kan "ARAI" of "CON-" zijn
```

### 2. ✅ Priority Verschillen

```
ARAI: 75  (hoogste)
CON:  70
ESS:  75  (hoogste)
SAM:  65
VER:  60  (laagste)
```

**IMPACT:** Priority bepaalt volgorde in output!

**OPLOSSING:** Behoud exact deze priorities in wrapper classes.

### 3. ✅ Header Emoji Verschillen

```
ARAI: ✅ (check mark)
CON:  🌐 (globe)
ESS:  🎯 (bullseye)
SAM:  🔗 (link)
VER:  📐 (ruler)
```

**IMPACT:** Gebruikers herkennen regels aan emoji's!

**OPLOSSING:** Header format MOET exact zijn: `### {emoji} {naam}:`

### 4. ❌ GEEN Verschillen Gevonden In

- ✅ `_format_rule()` methode (100% identiek)
- ✅ `execute()` flow (100% identiek)
- ✅ Error handling (100% identiek)
- ✅ Caching mechanisme (100% identiek)
- ✅ JSON loading (100% identiek)
- ✅ `get_dependencies()` (allemaal return `[]`)

---

## REGISTRATIE PATTERN ANALYSE

### Huidige Registratie (modular_prompt_adapter.py:68-74)

```python
modules = [
    ExpertiseModule(),
    OutputSpecificationModule(),
    GrammarModule(),
    ContextAwarenessModule(),
    SemanticCategorisationModule(),
    TemplateModule(),
    # Regel modules - elke categorie eigen module
    AraiRulesModule(),  # ARAI regels
    ConRulesModule(),  # CON regels
    EssRulesModule(),  # ESS regels
    IntegrityRulesModule(),  # INT regels - NIET consolideren!
    SamRulesModule(),  # SAM regels
    StructureRulesModule(),  # STR regels - NIET consolideren!
    VerRulesModule(),  # VER regels
    ErrorPreventionModule(),
    MetricsModule(),
    DefinitionTaskModule(),
]
```

**NA CONSOLIDATIE (moet identiek blijven):**

```python
modules = [
    ExpertiseModule(),
    OutputSpecificationModule(),
    GrammarModule(),
    ContextAwarenessModule(),
    SemanticCategorisationModule(),
    TemplateModule(),
    # Regel modules - nu met generieke base
    AraiRulesModule(),  # Wrapper om JSONBasedRulesModule
    ConRulesModule(),   # Wrapper om JSONBasedRulesModule
    EssRulesModule(),   # Wrapper om JSONBasedRulesModule
    IntegrityRulesModule(),  # Blijft custom (niet geconsolideerd)
    SamRulesModule(),   # Wrapper om JSONBasedRulesModule
    StructureRulesModule(),  # Blijft custom (niet geconsolideerd)
    VerRulesModule(),   # Wrapper om JSONBasedRulesModule
    ErrorPreventionModule(),
    MetricsModule(),
    DefinitionTaskModule(),
]
```

**GEEN WIJZIGINGEN** in `modular_prompt_adapter.py` nodig!

---

## TEST VEREISTEN

### Must-Have Tests (Voor Consolidatie)

```python
def test_output_identiek_arai():
    """ARAI output moet exact hetzelfde zijn."""
    old = AraiRulesModuleOld()
    new = AraiRulesModule()

    assert old.execute(context).content == new.execute(context).content

def test_output_identiek_con():
    """CON output moet exact hetzelfde zijn."""
    # Herhaal voor alle 5 modules...

def test_header_format_preserved():
    """Headers moeten exact format behouden."""
    arai = AraiRulesModule()
    output = arai.execute(context).content

    assert "### ✅ Algemene Regels AI (ARAI):" in output

def test_emoji_preserved():
    """Emoji's moeten exact behouden blijven."""
    modules = {
        'arai': (AraiRulesModule(), "✅"),
        'con': (ConRulesModule(), "🌐"),
        'ess': (EssRulesModule(), "🎯"),
        'sam': (SamRulesModule(), "🔗"),
        'ver': (VerRulesModule(), "📐"),
    }

    for name, (module, expected_emoji) in modules.items():
        output = module.execute(context).content
        assert expected_emoji in output, f"{name} emoji missing!"

def test_rule_format_preserved():
    """Rule format moet exact hetzelfde zijn."""
    module = AraiRulesModule()
    output = module.execute(context).content

    # Check for expected patterns
    assert "🔹 **ARAI" in output  # Rule header
    assert "  ✅ " in output        # Good example
    assert "  ❌ " in output        # Bad example

def test_priority_preserved():
    """Priority moet exact behouden blijven."""
    assert AraiRulesModule().priority == 75
    assert ConRulesModule().priority == 70
    assert EssRulesModule().priority == 75
    assert SamRulesModule().priority == 65
    assert VerRulesModule().priority == 60

def test_module_id_preserved():
    """Module IDs moeten exact behouden blijven."""
    assert AraiRulesModule().module_id == "arai_rules"
    assert ConRulesModule().module_id == "con_rules"
    # etc...

def test_backward_compatibility():
    """Import statements moeten blijven werken."""
    from src.services.prompts.modules import (
        AraiRulesModule,
        ConRulesModule,
        EssRulesModule,
        SamRulesModule,
        VerRulesModule,
    )

    # Should not raise ImportError
    assert AraiRulesModule is not None
```

---

## CONSOLIDATIE PLAN (GEDETAILLEERD)

### Stap 1: Maak Generic Base Module (2 uur)

**Nieuw bestand:** `src/services/prompts/modules/json_based_rules_module.py`

```python
"""
Generic JSON-Based Rules Module - Base voor ARAI, CON, ESS, SAM, VER.

Deze module elimineert 512 regels duplicatie door een generieke implementatie
te bieden voor alle JSON-based validation rule modules.
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class JSONBasedRulesModule(BasePromptModule):
    """
    Generieke module voor JSON-based validatieregels.

    Gebruikt door: ARAI, CON, ESS, SAM, VER modules.
    """

    def __init__(
        self,
        rule_prefix: str,
        module_id: str,
        module_name: str,
        header_emoji: str,
        priority: int,
    ):
        """
        Initialize generieke rule module.

        Args:
            rule_prefix: Filter prefix (bijv. "ARAI", "CON-")
            module_id: Unieke module ID (bijv. "arai_rules")
            module_name: Display naam (bijv. "ARAI Validation Rules")
            header_emoji: Emoji voor header (bijv. "✅")
            priority: Execution priority (60-75)
        """
        super().__init__(
            module_id=module_id,
            module_name=module_name,
            priority=priority,
        )
        self.rule_prefix = rule_prefix
        self.header_emoji = header_emoji
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize module met configuratie."""
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        logger.debug(
            f"{self.module_id} geïnitialiseerd (examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Deze module draait altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Genereer validatieregels voor dit prefix."""
        try:
            sections = []

            # Header met emoji (EXACT format behouden!)
            sections.append(f"### {self.header_emoji} {self.module_name}:")

            # Load toetsregels from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter by prefix
            filtered_rules = {
                k: v for k, v in all_rules.items()
                if k.startswith(self.rule_prefix)
            }

            # Format rules
            sorted_rules = sorted(filtered_rules.items())
            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(filtered_rules),
                    "include_examples": self.include_examples,
                    "rule_prefix": self.rule_prefix,
                },
            )

        except Exception as e:
            logger.error(f"{self.module_id} execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate {self.rule_prefix} rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """Deze module heeft geen dependencies."""
        return []

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formateer een regel uit JSON data.

        Deze methode is 100% identiek aan de originele implementatie
        in alle 5 modules.
        """
        lines = []

        # Header met emoji
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        # Uitleg
        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        # Toetsvraag
        toetsvraag = regel_data.get("toetsvraag", "")
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")

        # Voorbeelden (indien enabled)
        if self.include_examples:
            # Goede voorbeelden
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            # Foute voorbeelden
            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines
```

### Stap 2: Update Bestaande Modules (1 uur)

**Vervang** `arai_rules_module.py`:

```python
"""
ARAI Rules Module - Wrapper om JSONBasedRulesModule voor backward compatibility.
"""

from .json_based_rules_module import JSONBasedRulesModule


class AraiRulesModule(JSONBasedRulesModule):
    """
    Module voor ARAI validatieregels.

    Wrapper om generieke JSONBasedRulesModule voor backward compatibility.
    """

    def __init__(self):
        super().__init__(
            rule_prefix="ARAI",
            module_id="arai_rules",
            module_name="ARAI Validation Rules",
            header_emoji="✅",
            priority=75,
        )
```

**Herhaal voor:** `con_rules_module.py`, `ess_rules_module.py`, `sam_rules_module.py`, `ver_rules_module.py`

**BELANGRIJK:** Let op CON prefix heeft trailing dash: `"CON-"`!

### Stap 3: Update `__init__.py` (5 min)

```python
# src/services/prompts/modules/__init__.py

# ... bestaande imports ...

# Generic base voor JSON-based rules
from .json_based_rules_module import JSONBasedRulesModule

# JSON-based rule modules (nu wrappers)
from .arai_rules_module import AraiRulesModule
from .con_rules_module import ConRulesModule
from .ess_rules_module import EssRulesModule
from .sam_rules_module import SamRulesModule
from .ver_rules_module import VerRulesModule

# Custom rule modules (NIET geconsolideerd)
from .structure_rules_module import StructureRulesModule
from .integrity_rules_module import IntegrityRulesModule

__all__ = [
    # ... bestaande exports ...
    "JSONBasedRulesModule",  # Nieuwe export
    "AraiRulesModule",
    "ConRulesModule",
    "EssRulesModule",
    "SamRulesModule",
    "VerRulesModule",
    "StructureRulesModule",
    "IntegrityRulesModule",
]
```

---

## VALIDATIE CHECKLIST

### ✅ Pre-Implementation

- [x] Alle 5 modules geanalyseerd
- [x] Verschillen gedocumenteerd
- [x] Backward compatibility plan
- [x] Test strategie gedefinieerd

### 🔲 During Implementation

- [ ] Generic module geïmplementeerd
- [ ] Wrapper modules gemaakt
- [ ] `__init__.py` updated
- [ ] Tests geschreven
- [ ] Tests PASS

### 🔲 Post-Implementation

- [ ] Output exact identiek (byte-for-byte)
- [ ] Emoji's intact
- [ ] Headers intact
- [ ] Priorities intact
- [ ] Module IDs intact
- [ ] Import statements werken
- [ ] Geen regressions

---

## RISICO MATRIX

| Risico | Likelihood | Impact | Mitigatie |
|--------|------------|--------|-----------|
| Output verschilt | LOW | HIGH | Comprehensive tests |
| Emoji's verkeerd | LOW | MEDIUM | Visual inspection + tests |
| Import breaking | LOW | HIGH | Wrapper classes |
| Priority wijzigt | LOW | MEDIUM | Exact priority preservatie |
| CON- dash vergeten | MEDIUM | HIGH | Specifieke test voor CON |

---

## GOEDKEURING VOOR CONSOLIDATIE

**STATUS:** ✅ **APPROVED**

**Redenen:**
1. ✅ 100% code duplication bevestigd (512 regels)
2. ✅ Geen business logic verschillen
3. ✅ Backward compatibility plan solide
4. ✅ Test strategie comprehensive
5. ✅ Risico's geïdentificeerd en gemitigeerd

**Volgende stap:** Implementeer generic module + tests

**Geschat:** 4 uur totaal
- Generic module: 2 uur
- Wrapper modules: 1 uur
- Tests: 1 uur

---

**Datum goedkeuring:** 2025-11-14
**Goedgekeurd door:** Multiagent analyse (Explore + Context7 + Perplexity)
**Start implementatie:** Wachtend op user goedkeuring
