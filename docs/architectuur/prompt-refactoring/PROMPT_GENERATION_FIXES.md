# Prompt Generation Implementation Fixes

## Fix 1: Ontological Category Corruption

### File: `src/services/definition_orchestrator.py`

**Current (BROKEN):**
```python
# Line 406-413
base_context = {
    "organisatorisch": (
        [context.request.context] if context.request.context else []
    ),
    "juridisch": [context.request.domein] if context.request.domein else [],
    "wettelijk": [],
    "ontologische_categorie": context.request.ontologische_categorie,  # BUG!
}
```

**Fixed:**
```python
# Line 406-424
base_context = {
    "organisatorisch": (
        [context.request.context] if context.request.context else []
    ),
    "juridisch": [context.request.domein] if context.request.domein else [],
    "wettelijk": [],
    # REMOVED ontologische_categorie from here
}

enriched_context = EnrichedContext(
    base_context=base_context,
    sources=[],
    expanded_terms={},
    confidence_scores={},
    metadata={
        "ontologische_categorie": context.request.ontologische_categorie,  # MOVED HERE
        "extra_instructies": context.request.extra_instructies,
    },
)
```

## Fix 2: Enable Ontological Templates

### File: `src/services/definition_generator_prompts.py`

**Current (NOT WORKING):**
```python
# Line 326
ontologische_categorie = context.metadata.get("ontologische_categorie")
if ontologische_categorie:
    # This never executes because metadata is not properly set
```

**Add Debug Logging:**
```python
# Line 321
def _select_template(self, begrip: str, context: EnrichedContext) -> PromptTemplate:
    """Selecteer juiste template gebaseerd op begrip en context."""
    begrip_lower = begrip.lower()

    # DEBUG: Log what we receive
    logger.debug(f"Context metadata: {context.metadata}")
    logger.debug(f"Base context keys: {list(context.base_context.keys())}")

    # PRIORITEIT 1: Ontologische categorie uit metadata
    ontologische_categorie = context.metadata.get("ontologische_categorie")
    if ontologische_categorie:
        template_mapping = {
            "type": "ontologie_type",
            "proces": "ontologie_proces",
            "resultaat": "ontologie_resultaat",
            "exemplaar": "ontologie_exemplaar",
        }
        # Ensure we handle enum values
        if hasattr(ontologische_categorie, 'value'):
            category_key = ontologische_categorie.value
        else:
            category_key = str(ontologische_categorie).lower()

        template_key = template_mapping.get(category_key)
        if template_key and template_key in self.templates:
            logger.info(
                f"✅ USING ontological template: {template_key} for category: {category_key}"
            )
            return self.templates[template_key]
        else:
            logger.warning(
                f"⚠️ No template found for category: {category_key}, available: {list(template_mapping.keys())}"
            )
```

## Fix 3: Lower Legacy Threshold

### File: `src/services/definition_generator_prompts.py`

**Current (TOO RESTRICTIVE):**
```python
# Line 618
def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
    if "legacy" in self.builders and len(context.sources) <= 1:
        total_context_items = sum(len(items) for items in context.base_context.values())
        if total_context_items <= 3:  # Too restrictive!
            return "legacy"
```

**Fixed (MORE INCLUSIVE):**
```python
def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
    # Check for force flag first
    if hasattr(self, "_forced_strategy") and self._forced_strategy in self.builders:
        return self._forced_strategy

    # Legacy builder for simpler contexts (raised threshold)
    if "legacy" in self.builders and len(context.sources) <= 2:
        total_context_items = sum(len(items) for items in context.base_context.values())
        if total_context_items <= 10:  # More reasonable threshold
            logger.info(f"Using legacy strategy for {total_context_items} context items")
            return "legacy"
```

## Fix 4: Add Toetsregels Integration

### New File: `src/services/rule_aware_prompt_builder.py`

```python
"""Rule-aware prompt builder that prevents common validation failures."""

import logging
from typing import Dict, List

from services.definition_generator_prompts import PromptBuilder, PromptTemplate
from services.definition_generator_context import EnrichedContext
from services.definition_generator_config import UnifiedGeneratorConfig
from validation.toetsregels import TOETSREGELS, ToetsRegel

logger = logging.getLogger(__name__)


class RuleAwarePromptBuilder(PromptBuilder):
    """Prompt builder that incorporates validation rules proactively."""

    def __init__(self):
        self.rules = TOETSREGELS
        self.critical_rules = self._identify_critical_rules()

    def _identify_critical_rules(self) -> List[str]:
        """Identify rules that should always be included in prompts."""
        return [
            "CON-01",  # Geen expliciete context vermelding
            "ESS-01",  # Beschrijf WAT, niet WAARVOOR
            "STR-01",  # Start met kernzelfstandig naamwoord
        ]

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """Build rule-aware prompt."""

        # Start with base prompt
        base_prompt = self._build_base_prompt(begrip, context)

        # Add rule guidance
        rule_section = self._build_rule_section(begrip, context)

        # Add examples from successful definitions
        example_section = self._build_example_section(context)

        # Combine all sections
        full_prompt = f"{base_prompt}\n\n{rule_section}\n\n{example_section}"

        logger.info(f"Built rule-aware prompt for '{begrip}' with {len(self.critical_rules)} critical rules")

        return full_prompt

    def _build_base_prompt(self, begrip: str, context: EnrichedContext) -> str:
        """Build the base prompt."""
        context_text = context.get_all_context_text()

        ontologische_categorie = context.metadata.get("ontologische_categorie", "type")

        return f"""
Genereer een Nederlandse definitie voor het {ontologische_categorie} begrip: {begrip}

Context informatie:
{context_text}

De definitie moet voldoen aan strenge kwaliteitseisen voor juridisch gebruik.
"""

    def _build_rule_section(self, begrip: str, context: EnrichedContext) -> str:
        """Build section with rule guidance."""
        rules_text = "BELANGRIJKE KWALITEITSREGELS:\n"

        # Add critical rules
        for rule_id in self.critical_rules:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                rules_text += f"\n{rule.regel_id}: {rule.beschrijving}"
                if rule.positief_voorbeeld:
                    rules_text += f"\n  ✓ Goed: {rule.positief_voorbeeld}"
                if rule.negatief_voorbeeld:
                    rules_text += f"\n  ✗ Fout: {rule.negatief_voorbeeld}"
                rules_text += "\n"

        # Add category-specific rules
        category = context.metadata.get("ontologische_categorie", "type")
        if category == "proces":
            rules_text += "\nVoor PROCES definities:\n"
            rules_text += "- Gebruik werkwoorden die de activiteit beschrijven\n"
            rules_text += "- Vermeld begin- en eindpunt van het proces\n"
            rules_text += "- Specificeer betrokken actoren\n"
        elif category == "type":
            rules_text += "\nVoor TYPE definities:\n"
            rules_text += "- Begin met het genus (bovenliggende categorie)\n"
            rules_text += "- Voeg differentia (onderscheidende kenmerken) toe\n"
            rules_text += "- Maak duidelijk wat wel/niet tot deze categorie behoort\n"

        return rules_text

    def _build_example_section(self, context: EnrichedContext) -> str:
        """Build section with positive examples."""
        return """
VOORBEELDEN van goede definities:

Authenticatie (proces): Het vaststellen van de echtheid van een digitale identiteit door het verifiëren van aangeleverde credentials tegen een referentiebron.

Identiteitsbewijs (type): Een door een bevoegde autoriteit uitgegeven document dat persoonsgegevens bevat waarmee de identiteit van de houder kan worden vastgesteld.
"""

    def get_strategy_name(self) -> str:
        return "rule_aware"
```

## Fix 5: Activate Rule-Aware Builder

### File: `src/services/definition_generator_prompts.py`

**Add to `_init_builders()` method:**
```python
# Line 574
def _init_builders(self):
    """Initialiseer beschikbare prompt builders."""

    # Existing builders...
    self.builders["basic"] = BasicPromptBuilder()
    self.builders["context_aware"] = ContextAwarePromptBuilder()

    # ADD: Rule-aware builder
    try:
        from services.rule_aware_prompt_builder import RuleAwarePromptBuilder
        self.builders["rule_aware"] = RuleAwarePromptBuilder()
        logger.info("✅ Rule-aware prompt builder loaded")
    except ImportError:
        logger.warning("Rule-aware prompt builder not available")
```

**Update `_select_strategy()` to prefer rule-aware:**
```python
# Line 618
def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
    """Selecteer beste prompt strategy voor deze situatie."""

    # Force strategy if set
    if hasattr(self, "_forced_strategy") and self._forced_strategy in self.builders:
        return self._forced_strategy

    # PREFER rule-aware builder if available
    if "rule_aware" in self.builders:
        logger.info("Using rule-aware strategy for maximum quality")
        return "rule_aware"

    # Fallback logic...
```

## Fix 6: Web Enrichment Activation

### File: `src/services/definition_orchestrator.py`

**Add before prompt generation:**
```python
# Insert at line 395 (before prompt building)
# Enrich context with web sources if enabled
if self.config.enable_web_lookup and WEB_LOOKUP_AVAILABLE:
    try:
        # Quick web lookup for the term
        web_sources = await zoek_bronnen_voor_begrip(context.request.begrip)

        if web_sources and isinstance(web_sources, list):
            for source in web_sources[:3]:  # Top 3 sources
                enriched_context.sources.append({
                    'source_type': 'web',
                    'content': source.get('description', ''),
                    'confidence': source.get('confidence', 0.5),
                    'name': source.get('name', 'Web bron')
                })
            logger.info(f"Added {len(web_sources)} web sources to context")
    except Exception as e:
        logger.warning(f"Web enrichment failed: {e}")
```

## Testing the Fixes

### Test Script:
```python
"""Test ontological category handling."""

import asyncio
from services import get_definition_service

async def test_category_handling():
    service = get_definition_service()

    # Test with explicit category
    result = service.generate_definition(
        begrip="verificatie",
        context_dict={
            "organisatorisch": ["DJI"],
            "juridisch": ["detentie"],
        },
        categorie="proces"  # Should trigger ontologie_proces template
    )

    # Check if correct template was used
    if hasattr(result, 'metadata'):
        print(f"Prompt template used: {result.metadata.get('prompt_template', 'unknown')[:100]}...")
        assert "PROCES" in result.metadata.get('prompt_template', '')

if __name__ == "__main__":
    asyncio.run(test_category_handling())
```

## Summary of Changes

1. **Move `ontologische_categorie` from `base_context` to `metadata`**
2. **Add proper enum handling in template selection**
3. **Raise legacy builder threshold from 3 to 10**
4. **Create rule-aware prompt builder**
5. **Integrate validation rules into prompt generation**
6. **Activate web source enrichment before generation**

These fixes will enable:
- ✅ Correct ontological template selection
- ✅ Sophisticated prompt features
- ✅ Proactive quality improvement
- ✅ Rich context utilization
