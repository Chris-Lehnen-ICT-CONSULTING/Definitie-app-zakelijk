"""
PROMPT V8 OPTIMIZATION - CODE EXAMPLES
Concrete implementatie voorbeelden voor prompt optimalisatie
"""

# ============================================================================
# EXAMPLE 1: Optimized Rule Module (Van 3500 naar 200 tokens)
# ============================================================================


class AraiRulesModuleV8(BasePromptModule):
    """
    V8: Alleen high-level principes, geen individuele regels.
    Rationale: Regels worden toch gevalideerd in post-processing.
    """

    def execute(self, context: ModuleContext) -> List[str]:
        # VOOR V7: Laadde 9 JSON files, formatteerde elk met voorbeelden
        # NA V8: Alleen samenvattende principes

        return [
            "### ✅ Algemene Regels (ARAI):",
            "- Begin met zelfstandig naamwoord (geen werkwoord/koppelwerkwoord)",
            "- Vermijd vage containerbegrippen zonder specificatie",
            "- Essentie beschrijven, niet het doel",
            "- Volledige validatie gebeurt automatisch na generatie",
            "",
        ]
        # Token count: ~50 (was ~500 per module)


# ============================================================================
# EXAMPLE 2: Error Prevention Module met Positive Templates
# ============================================================================


class ErrorPreventionModuleV8(BasePromptModule):
    """
    V8: Positive templates in plaats van 42 verboden.
    """

    def _build_error_section(self) -> List[str]:
        # VOOR V7: 42 individuele "Start niet met..." regels
        # NA V8: 3 approved patterns + 1 summary

        return [
            "### ✅ APPROVED START PATTERNS:",
            "",
            "**PROCES:** [activiteit/handeling] waarbij [actor] [actie] uitvoert",
            "   Voorbeeld: handeling waarbij gegevens worden geclassificeerd",
            "",
            "**TYPE:** [soort/categorie] [bovenbegrip] met kenmerk",
            "   Voorbeeld: categorie documenten met vertrouwelijke informatie",
            "",
            "**RESULTAAT:** [uitkomst] van [proces] dat [functie]",
            "   Voorbeeld: besluit van de rechter dat rechtsgevolgen vaststelt",
            "",
            "🚫 VERMIJD: Koppelwerkwoorden ('is'), lidwoorden ('de/het'), term-herhaling",
            "",
        ]
        # Token count: ~150 (was ~900)


# ============================================================================
# EXAMPLE 3: Conditional Module Loading
# ============================================================================


class PromptOrchestratorV8:
    """
    V8: Alleen relevante modules laden op basis van context.
    """

    def build_prompt(self, context: ModuleContext) -> str:
        # Filter modules based on context
        active_modules = self._get_active_modules(context)

        sections = []
        for module_name in active_modules:
            module = self.modules.get(module_name)
            if module:
                result = module.execute(context)
                sections.extend(result)

        return "\n".join(sections)

    def _get_active_modules(self, context: ModuleContext) -> List[str]:
        """
        Dynamically select modules based on request context.
        Reduces from 16 modules always to 6-10 conditional.
        """

        # Always include core (essential for any definition)
        modules = [
            "expertise",  # ~50 tokens
            "output_specification",  # ~100 tokens
            "task",  # ~100 tokens
        ]

        # Conditional modules based on context
        if context.has_organisatorische_context():
            modules.append("context_awareness")  # ~200 tokens

        if context.has_juridische_context():
            modules.append("legal_references")  # ~150 tokens

        # Only include most relevant rule module (not all 7)
        if context.begrip_type == "proces":
            modules.append("ess_rules")  # Essential for processes
        elif context.begrip_type == "resultaat":
            modules.append("structure_rules")  # Important for results
        else:
            modules.append("arai_rules")  # General fallback

        # Templates only if complex definition needed
        if context.complexity_score > 0.7:
            modules.append("template")
            modules.append("semantic_categorisation")

        # Grammar only for formal contexts
        if context.formality_level == "hoog":
            modules.append("grammar")

        return modules
        # Result: 6-10 modules instead of 16


# ============================================================================
# EXAMPLE 4: Static Module Caching
# ============================================================================

from functools import lru_cache

import streamlit as st


class ModuleCacheV8:
    """
    V8: Cache static content that doesn't change per request.
    """

    @st.cache_data(ttl=3600)
    def get_static_modules(self) -> Dict[str, str]:
        """
        Cache modules that never change.
        Saves ~1000ms per request.
        """
        return {
            "grammar": self._load_grammar_rules(),
            "error_patterns": self._load_error_patterns(),
            "base_templates": self._load_base_templates(),
        }

    @lru_cache(maxsize=128)
    def get_category_template(self, category: str) -> str:
        """
        Cache templates per category.
        Most users generate similar categories repeatedly.
        """
        if category == "proces":
            return "[activiteit/handeling] waarbij [actor] [actie] uitvoert"
        if category == "type":
            return "[soort/categorie] [bovenbegrip] met kenmerk"
        if category == "resultaat":
            return "[uitkomst] van [proces] dat [functie]"
        return "[entiteit] die [kenmerk] heeft"


# ============================================================================
# EXAMPLE 5: Inverted Pyramid Template
# ============================================================================


class InvertedPyramidTemplateV8:
    """
    V8: Nieuwe prompt structuur met prioriteit van informatie.
    """

    def build(self, context: PromptContext) -> str:
        """
        Build prompt with most critical info first.
        Total: ~2650 tokens (was 7250).
        """

        sections = []

        # LEVEL 1: Mission (50 tokens)
        sections.append(self._build_mission(context))

        # LEVEL 2: Golden Rules (300 tokens)
        sections.append(self._build_golden_rules())

        # LEVEL 3: Templates (400 tokens)
        sections.append(self._build_templates(context.category))

        # LEVEL 4: Refinement Rules (800 tokens)
        # Only include if quality requirement is high
        if context.quality_requirement >= "high":
            sections.append(self._build_refinement_rules())

        # LEVEL 5: Checklist (100 tokens)
        sections.append(self._build_checklist())

        return "\n\n".join(sections)

    def _build_mission(self, context: PromptContext) -> str:
        return f"""## MISSION STATEMENT
Formuleer een **heldere, contextuele definitie** voor overheidsgebruik die het begrip **{context.begrip}** precies afbakent.

**Format**: Eén enkele zin | 150-350 karakters | Geen punt aan einde

**Context** (impliciet verwerken):
- Organisatorisch: {context.organisatorische_context or 'geen'}
- Juridisch: {context.juridische_context or 'geen'}"""

    def _build_golden_rules(self) -> str:
        return """## ⭐ 3 GOLDEN RULES

1️⃣ **START MET ZELFSTANDIG NAAMWOORD**
   ✅ "proces dat identificeert"
   ❌ "is een proces"

2️⃣ **EXPLICITEER CATEGORIE**
   Gebruik juiste kick-off term voor categorie

3️⃣ **ESSENTIE, NIET DOEL**
   WAT het is, niet WAARVOOR"""


# ============================================================================
# EXAMPLE 6: Priority-Based Rule Selection
# ============================================================================


class RulePrioritySelectorV8:
    """
    V8: Alleen hoogste prioriteit regels in prompt.
    """

    RULE_PRIORITIES = {
        # CRITICAL (altijd in prompt)
        "ESS-02": 1,  # Ontologische categorie
        "STR-01": 1,  # Start met zelfstandig naamwoord
        "INT-01": 1,  # Eén zin
        # HIGH (meestal in prompt)
        "ESS-01": 2,  # Essentie niet doel
        "CON-01": 2,  # Context verwerking
        "STR-02": 2,  # Kick-off ≠ term
        # MEDIUM (alleen bij complexe definities)
        "INT-02": 3,  # Geen beslisregel
        "INT-08": 3,  # Positieve formulering
        # LOW (alleen in validatie, niet in prompt)
        "VER-01": 4,  # Enkelvoud
        "SAM-05": 4,  # Geen cirkeldefinities
    }

    def select_rules_for_prompt(
        self, complexity: float, max_rules: int = 8
    ) -> List[str]:
        """
        Select only most relevant rules for prompt.
        """

        if complexity < 0.3:
            # Simple definition: only critical rules
            priority_threshold = 1
        elif complexity < 0.7:
            # Medium complexity: critical + high
            priority_threshold = 2
        else:
            # Complex: include some medium rules
            priority_threshold = 3

        selected = [
            rule
            for rule, priority in self.RULE_PRIORITIES.items()
            if priority <= priority_threshold
        ]

        return selected[:max_rules]


# ============================================================================
# EXAMPLE 7: Metrics-Driven Optimization
# ============================================================================


class PromptOptimizerV8:
    """
    V8: Track en optimaliseer prompt performance.
    """

    def __init__(self):
        self.metrics = {
            "module_token_counts": {},
            "module_value_scores": {},
            "generation_times": [],
        }

    def optimize_prompt(self, context: ModuleContext) -> str:
        """
        Build optimized prompt based on historical metrics.
        """

        # Get module value scores (based on validation success)
        module_scores = self._calculate_module_scores()

        # Select modules with best value/token ratio
        selected_modules = self._select_optimal_modules(
            module_scores, target_tokens=2500
        )

        # Build prompt with selected modules
        return self._build_with_modules(selected_modules, context)

    def _calculate_module_scores(self) -> Dict[str, float]:
        """
        Calculate value score per token for each module.
        Higher score = more valuable per token.
        """

        scores = {}
        for module, token_count in self.metrics["module_token_counts"].items():
            value = self.metrics["module_value_scores"].get(module, 0.5)
            scores[module] = value / max(token_count, 1)

        return scores

    def _select_optimal_modules(
        self, scores: Dict[str, float], target_tokens: int
    ) -> List[str]:
        """
        Select modules that maximize value within token budget.
        """

        # Sort by value/token ratio
        sorted_modules = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        selected = []
        current_tokens = 0

        for module, score in sorted_modules:
            module_tokens = self.metrics["module_token_counts"].get(module, 100)

            if current_tokens + module_tokens <= target_tokens:
                selected.append(module)
                current_tokens += module_tokens

            if current_tokens >= target_tokens * 0.9:
                break

        return selected


# ============================================================================
# EXAMPLE 8: A/B Testing Implementation
# ============================================================================


class PromptABTestV8:
    """
    V8: Test prompt versions systematically.
    """

    def __init__(self):
        self.test_config = {
            "v7": {"builder": PromptBuilderV7(), "weight": 0.1},
            "v8": {"builder": PromptBuilderV8(), "weight": 0.9},
        }

    async def generate_with_ab_test(self, begrip: str, context: Dict) -> Dict:
        """
        Generate definition with A/B testing.
        """

        # Select version based on weights
        version = self._select_version()

        # Generate with selected version
        builder = self.test_config[version]["builder"]
        prompt = builder.build(begrip, context)

        # Track metrics
        start_time = time.time()
        result = await self._call_llm(prompt)
        generation_time = time.time() - start_time

        # Log results for analysis
        self._log_test_result(
            {
                "version": version,
                "begrip": begrip,
                "prompt_tokens": self._count_tokens(prompt),
                "generation_time": generation_time,
                "validation_passed": self._validate(result),
                "result": result,
            }
        )

        return {
            "definition": result,
            "version": version,
            "metrics": {"tokens": self._count_tokens(prompt), "time": generation_time},
        }

    def _select_version(self) -> str:
        """Select version based on configured weights."""

        import random

        rand = random.random()
        cumulative = 0

        for version, config in self.test_config.items():
            cumulative += config["weight"]
            if rand < cumulative:
                return version

        return "v8"  # Default fallback
