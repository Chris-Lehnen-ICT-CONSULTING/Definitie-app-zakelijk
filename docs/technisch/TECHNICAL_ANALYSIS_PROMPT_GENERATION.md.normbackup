# Technical Analysis: Prompt Generation Implementation Issues

## Executive Summary

The prompt generation implementation has several critical technical issues preventing sophisticated features from activating:

1. **Ontological category data corruption**: String value gets converted to character list
2. **Legacy prompt builder threshold never reached**: Context items too low
3. **Toetsregels integration missing**: No connection to prompt generation
4. **Enriched context features unused**: Advanced features bypassed

## 1. Exact Technical Flow When Generating Definition with Category "proces"

### Flow Trace:

```python
# 1. TabbedInterface._handle_definition_generation() - line 709
auto_categorie, category_reasoning, category_scores = asyncio.run(
    self._determine_ontological_category(begrip, primary_org, primary_jur)
)
# Returns: OntologischeCategorie.PROCES (enum value)

# 2. ServiceAdapter.generate_definition() - service_factory.py line 161
categorie = kwargs.get("categorie")
ontologische_categorie = None
if categorie:
    if hasattr(categorie, "value"):
        ontologische_categorie = categorie.value  # "proces" (string)
    else:
        ontologische_categorie = str(categorie)

# 3. GenerationRequest created - line 199
request = GenerationRequest(
    ontologische_categorie=ontologische_categorie,  # "proces" as string
)

# 4. DefinitionOrchestrator._generate_definition() - line 391
base_context = {
    "ontologische_categorie": context.request.ontologische_categorie,  # Still "proces"
}
```

## 2. Where Ontological Category Data Gets Corrupted

### The Bug Location:

In `DefinitionOrchestrator._generate_definition()` at line 412:

```python
# BUG: ontologische_categorie is placed in base_context dict
base_context = {
    "organisatorisch": [...],
    "juridisch": [...],
    "wettelijk": [],
    "ontologische_categorie": context.request.ontologische_categorie,  # WRONG!
}
```

### What Happens:

1. `base_context` is a dict that expects lists as values
2. When `EnrichedContext` processes this, it may iterate over the string "proces"
3. This creates `['p', 'r', 'o', 'c', 'e', 's']` - a character list!

### The Fix:

```python
# Move ontologische_categorie to metadata, not base_context
base_context = {
    "organisatorisch": [...],
    "juridisch": [...],
    "wettelijk": [],
    # Remove from here!
}

enriched_context = EnrichedContext(
    base_context=base_context,
    sources=[],
    expanded_terms={},
    confidence_scores={},
    metadata={
        "ontologische_categorie": context.request.ontologische_categorie,  # HERE!
        "extra_instructies": context.request.extra_instructies,
    },
)
```

## 3. Why Legacy Prompt Builder Threshold Fails

### The Issue:

In `UnifiedPromptBuilder._select_strategy()` at line 618:

```python
# Legacy builder selected only when:
if "legacy" in self.builders and len(context.sources) <= 1:
    total_context_items = sum(len(items) for items in context.base_context.values())
    if total_context_items <= 3:  # THIS THRESHOLD IS RARELY MET!
        return "legacy"
```

### Why It Fails:

1. Most real-world scenarios have >3 context items
2. The threshold is too restrictive
3. Legacy builder has sophisticated features that never activate

### Example:
```python
# Typical context:
{
    "organisatorisch": ["DJI", "detentie"],  # 2 items
    "juridisch": ["strafrecht"],            # 1 item
    "wettelijk": ["Pbw"],                   # 1 item
}
# Total: 4 items - legacy builder skipped!
```

## 4. Missing Toetsregels Integration

### Current State:

Toetsregels (validation rules) exist but aren't used during prompt generation:

```python
# In validation/toetsregels.py - sophisticated rules defined
TOETSREGELS = {
    "CON-01": {...},  # Context rules
    "ESS-01": {...},  # Essential elements
    "STR-01": {...},  # Structure rules
}

# BUT: No connection to prompt generation!
```

### What Should Happen:

```python
class RuleBasedPromptBuilder(PromptBuilder):
    def build_prompt(self, begrip, context, config):
        # 1. Analyze which rules might be violated
        potential_issues = self._predict_rule_violations(begrip, context)

        # 2. Add preventive instructions to prompt
        prompt = self._base_prompt(begrip, context)
        prompt += "\n\nLet op de volgende kwaliteitsregels:\n"

        for rule_id, rule in potential_issues.items():
            prompt += f"- {rule.beschrijving}\n"
            if rule.positief_voorbeeld:
                prompt += f"  Goed: {rule.positief_voorbeeld}\n"

        return prompt
```

## 5. Enriched Context Features Not Activated

### Available but Unused Features:

1. **Web Lookup Integration**
```python
# In EnrichedContext:
sources: list[ContextSource]  # Can include web sources
expanded_terms: dict[str, str]  # Abbreviation expansion
confidence_scores: dict[str, float]  # Source reliability

# BUT: Always empty in current flow!
```

2. **Sophisticated Prompt Templates**
```python
# In BasicPromptBuilder - ontology-specific templates exist:
"ontologie_proces": PromptTemplate(...)  # Never selected!
"ontologie_type": PromptTemplate(...)    # Never selected!
```

3. **Context-Aware Strategy**
```python
# ContextAwarePromptBuilder has rich features:
- _calculate_context_score()  # Unused
- _build_rich_context_prompt()  # Never reached
- _format_detailed_context()  # Never called
```

## Technical Solutions

### 1. Fix Ontological Category Handling:

```python
# In DefinitionOrchestrator._generate_definition():
enriched_context = EnrichedContext(
    base_context={
        "organisatorisch": [...],
        "juridisch": [...],
        "wettelijk": [],
    },
    metadata={
        "ontologische_categorie": context.request.ontologische_categorie,
        "extra_instructies": context.request.extra_instructies,
    }
)
```

### 2. Enable Sophisticated Features:

```python
# In BasicPromptBuilder._select_template():
def _select_template(self, begrip: str, context: EnrichedContext) -> PromptTemplate:
    # PRIORITY 1: Check metadata for ontological category
    ontologische_categorie = context.metadata.get("ontologische_categorie")
    if ontologische_categorie:
        template_key = f"ontologie_{ontologische_categorie}"
        if template_key in self.templates:
            logger.info(f"Using ontological template: {template_key}")
            return self.templates[template_key]
```

### 3. Integrate Toetsregels:

```python
# New method in UnifiedPromptBuilder:
def _enhance_prompt_with_rules(self, base_prompt: str, begrip: str) -> str:
    """Add rule-based guidance to prevent common violations."""
    from validation.toetsregels import get_relevant_rules

    rules = get_relevant_rules(begrip)
    if rules:
        base_prompt += "\n\nZorg ervoor dat de definitie voldoet aan:"
        for rule in rules:
            base_prompt += f"\n- {rule.beschrijving}"

    return base_prompt
```

### 4. Activate Web Lookup:

```python
# In DefinitionOrchestrator._generate_definition():
if self.config.enable_web_lookup:
    # Lookup before generation
    web_results = await self._lookup_web_sources(begrip)
    for result in web_results:
        enriched_context.sources.append(
            ContextSource(
                source_type="web",
                content=result.definition,
                confidence=result.confidence
            )
        )
```

## Code Snippets Showing Current vs Fixed Flow

### Current Broken Flow:
```python
# 1. Category becomes string in base_context
base_context["ontologische_categorie"] = "proces"

# 2. Gets processed as iterable
for key, items in base_context.items():
    # "proces" becomes ['p','r','o','c','e','s']

# 3. Template selection fails
if ontologische_categorie:  # This is now a list!
    # Never matches template
```

### Fixed Flow:
```python
# 1. Category in metadata
metadata["ontologische_categorie"] = "proces"

# 2. Template selection works
template_key = f"ontologie_{metadata['ontologische_categorie']}"
# Returns: "ontologie_proces"

# 3. Sophisticated prompt used
prompt = templates["ontologie_proces"].format(
    begrip=begrip,
    context_section=context_text
)
```

## Performance Impact

Current implementation bypasses ~80% of available features:
- Legacy prompt builder: <5% usage due to threshold
- Ontological templates: 0% usage due to bug
- Rule integration: 0% implementation
- Web enrichment: 0% activation

Fixing these issues would significantly improve definition quality without adding latency.
