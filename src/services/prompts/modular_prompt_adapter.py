"""
Modular Prompt Adapter - Bridge tussen oude ModularPromptBuilder interface en nieuwe modulaire architectuur.

Deze adapter zorgt voor backwards compatibility terwijl het nieuwe
PromptOrchestrator + modules systeem wordt gebruikt.
"""

import logging
import threading
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext

from .modules import (
    AraiRulesModule,
    ConRulesModule,
    ContextAwarenessModule,
    DefinitionTaskModule,
    ErrorPreventionModule,
    EssRulesModule,
    ExpertiseModule,
    GrammarModule,
    IntegrityRulesModule,
    MetricsModule,
    OutputSpecificationModule,
    PromptOrchestrator,
    SamRulesModule,
    SemanticCategorisationModule,
    StructureRulesModule,
    TemplateModule,
    VerRulesModule,
)

logger = logging.getLogger(__name__)

# Singleton orchestrator cache
_global_orchestrator: PromptOrchestrator | None = None
_orchestrator_lock = threading.Lock()


def get_cached_orchestrator() -> PromptOrchestrator:
    """
    Get or create singleton PromptOrchestrator.
    Thread-safe lazy initialization.

    Returns:
        Cached PromptOrchestrator instance
    """
    global _global_orchestrator

    if _global_orchestrator is None:
        with _orchestrator_lock:
            # Double-check locking pattern
            if _global_orchestrator is None:
                logger.info("🎯 Creating singleton PromptOrchestrator")
                orchestrator = PromptOrchestrator(max_workers=4)

                # Register all 16 modules
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
                    IntegrityRulesModule(),  # INT regels
                    SamRulesModule(),  # SAM regels
                    StructureRulesModule(),  # STR regels
                    VerRulesModule(),  # VER regels
                    ErrorPreventionModule(),
                    MetricsModule(),
                    DefinitionTaskModule(),
                ]

                for module in modules:
                    orchestrator.register_module(module)

                logger.info(
                    f"✅ PromptOrchestrator cached: {len(orchestrator.modules)} modules registered"
                )
                _global_orchestrator = orchestrator

    return _global_orchestrator


class ModularPromptAdapter:
    """
    Adapter die de oude ModularPromptBuilder interface implementeert
    maar het nieuwe echt modulaire systeem gebruikt.

    Deze klasse is een drop-in replacement voor ModularPromptBuilder.
    """

    def __init__(self, component_config: Any | None = None):
        """
        Initialize adapter met component configuratie.

        Args:
            component_config: Configuratie compatibel met oude ModularPromptBuilder
        """
        # Import here to avoid circular import
        from .modular_prompt_builder import PromptComponentConfig

        self.component_config = component_config or PromptComponentConfig()
        self._orchestrator: PromptOrchestrator | None = None
        self._initialized = False

        # Initialize het nieuwe systeem
        self._setup_orchestrator()

        logger.info(
            "ModularPromptAdapter geïnitialiseerd - gebruikt nieuwe modulaire architectuur"
        )

    def _setup_orchestrator(self) -> None:
        """Setup de PromptOrchestrator met alle modules."""
        # Use cached singleton
        self._orchestrator = get_cached_orchestrator()

        # Converteer component config naar module configs
        module_configs = self._convert_config_to_module_configs()

        # Initialize modules met this adapter's config
        self._orchestrator.initialize_modules(module_configs)
        self._initialized = True

        logger.debug(
            f"Adapter using cached orchestrator with {len(self._orchestrator.modules)} modules"
        )

    def _convert_config_to_module_configs(self) -> dict[str, dict[str, Any]]:
        """
        Converteer PromptComponentConfig naar individuele module configuraties.

        Returns:
            Dictionary met module_id -> config mappings
        """
        config = self.component_config

        return {
            "expertise": {
                # ExpertiseModule heeft geen specifieke config nodig
            },
            "output_specification": {
                # Map character limits indien aanwezig
                "default_min_chars": getattr(config, "min_chars", 150),
                "default_max_chars": getattr(config, "max_chars", 350),
            },
            "context_awareness": {
                # Enhanced context module configuratie
                "adaptive_formatting": not config.compact_mode,  # Adaptive formatting uit in compact mode
                "confidence_indicators": config.enable_component_metadata,  # Confidence indicators bij metadata
                "include_abbreviations": config.include_examples_in_rules,  # Afkortingen bij examples
            },
            "semantic_categorisation": {
                # Map detailed guidance setting
                "detailed_guidance": config.detailed_category_guidance,
            },
            # Regel modules configuratie
            "arai_rules": {
                "include_examples": config.include_examples_in_rules,
            },
            "con_rules": {
                "include_examples": config.include_examples_in_rules,
            },
            "ess_rules": {
                "include_examples": config.include_examples_in_rules,
            },
            "sam_rules": {
                "include_examples": config.include_examples_in_rules,
            },
            "ver_rules": {
                "include_examples": config.include_examples_in_rules,
            },
            "error_prevention": {
                # Error prevention settings
                "include_validation_matrix": not config.compact_mode,
                "extended_forbidden_list": not config.compact_mode,
            },
            "definition_task": {
                # Task module settings
                "include_quality_control": not config.compact_mode,
                "include_metadata": config.enable_component_metadata,
            },
            "grammar": {
                # Grammar module settings
                "include_examples": config.include_examples_in_rules,
                "strict_mode": False,  # Kan later configureerbaar gemaakt worden
            },
            "structure_rules": {
                # Structure rules settings
                "include_examples": config.include_examples_in_rules,
            },
            "integrity_rules": {
                # Integrity rules settings
                "include_examples": config.include_examples_in_rules,
            },
            "template": {
                # Template module settings
                "include_examples": config.include_examples_in_rules,
                "detailed_templates": config.detailed_category_guidance,
            },
            "metrics": {
                # Metrics module settings
                "include_detailed_metrics": not config.compact_mode,
                "track_history": False,
            },
        }

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """
        Build volledige prompt uit modules.

        Dit is de hoofdmethode die compatibel is met de oude interface.

        Args:
            begrip: Het begrip om te definiëren
            context: Verrijkte context informatie
            config: Unified generator configuratie

        Returns:
            Volledige prompt string

        Raises:
            ValueError: Als essentiële componenten ontbreken
        """
        if not self._initialized:
            msg = "Adapter niet geïnitialiseerd"
            raise RuntimeError(msg)

        # Valideer input (compatibel met oude gedrag)
        if not begrip or not begrip.strip():
            msg = "Begrip mag niet leeg zijn"
            raise ValueError(msg)

        try:
            # Gebruik orchestrator om prompt te bouwen
            prompt = self._orchestrator.build_prompt(begrip, context, config)

            # Apply compact mode post-processing indien nodig
            if self.component_config.compact_mode:
                prompt = self._apply_compact_mode(prompt)

            # Apply max length indien geconfigureerd
            if self.component_config.max_prompt_length < len(prompt):
                logger.warning(
                    f"Prompt te lang ({len(prompt)} chars), "
                    f"truncating to {self.component_config.max_prompt_length}"
                )
                prompt = prompt[: self.component_config.max_prompt_length]

            return prompt

        except Exception as e:
            logger.error(
                f"ModularPromptAdapter.build_prompt failed voor '{begrip}': {e!s}",
                exc_info=True,
            )
            raise

    def get_strategy_name(self) -> str:
        """
        Verkrijg naam van deze strategy.

        Behoudt compatibiliteit met oude interface.
        """
        return "modular"

    def get_component_metadata(
        self, begrip: str | None = None, context: EnrichedContext | None = None
    ) -> dict[str, Any]:
        """
        Verkrijg metadata over gebruikte componenten.

        Compatibel met oude interface maar gebruikt nieuwe data.

        Returns:
            Dictionary met component informatie
        """
        if not self._initialized:
            return {"error": "Adapter niet geïnitialiseerd"}

        # Basis metadata
        metadata = {
            "builder_type": "ModularPromptAdapter (True Modular Architecture)",
            "total_available_components": len(self._orchestrator.modules),
            "active_components": self._count_active_components(),
            "uses_orchestrator": True,
            "architecture_version": "2.0",
        }

        # Component configuratie info
        metadata["component_config"] = {
            "include_role": self.component_config.include_role,
            "include_context": self.component_config.include_context,
            "include_ontological": self.component_config.include_ontological,
            "include_validation_rules": self.component_config.include_validation_rules,
            "include_forbidden_patterns": self.component_config.include_forbidden_patterns,
            "include_final_instructions": self.component_config.include_final_instructions,
            "compact_mode": self.component_config.compact_mode,
        }

        # Module info
        metadata["modules"] = self._orchestrator.get_registered_modules()

        # Execution metadata indien beschikbaar
        exec_metadata = self._orchestrator.get_execution_metadata()
        if exec_metadata:
            metadata["last_execution"] = exec_metadata

        return metadata

    def _count_active_components(self) -> int:
        """Tel actieve componenten op basis van configuratie."""
        count = 0
        config = self.component_config

        # Deze mapping is voor backwards compatibility
        if config.include_role:
            count += 1  # ExpertiseModule
        if config.include_context:
            count += 1  # ContextAwarenessModule
        if config.include_ontological:
            count += 1  # SemanticCategorisationModule
        if config.include_validation_rules:
            count += 7  # Alle regel modules (ARAI, CON, ESS, INT, SAM, STR, VER)
        if config.include_forbidden_patterns:
            count += 1  # ErrorPreventionModule
        if config.include_final_instructions:
            count += 1  # DefinitionTaskModule
        # OutputSpecificationModule is altijd actief
        count += 1

        return count

    def _apply_compact_mode(self, prompt: str) -> str:
        """
        Apply compact mode transformaties.

        In compact mode verwijderen we enkele secties voor kortere prompts.
        """
        if not self.component_config.compact_mode:
            return prompt

        # Simpele implementatie: verwijder voorbeelden
        lines = prompt.split("\n")
        filtered_lines = []
        skip_examples = False

        for line in lines:
            # Skip voorbeeld regels
            if "✅" in line or "❌" in line:
                continue
            # Skip validation matrix in compact mode
            if "| Probleem" in line:
                skip_examples = True
            if skip_examples and line.strip() == "":
                skip_examples = False
                continue
            if not skip_examples:
                filtered_lines.append(line)

        compacted = "\n".join(filtered_lines)
        logger.debug(
            f"Compact mode: reduced from {len(prompt)} to {len(compacted)} chars"
        )

        return compacted


# Voor backwards compatibility - alias naar adapter
ModularPromptBuilder = ModularPromptAdapter
