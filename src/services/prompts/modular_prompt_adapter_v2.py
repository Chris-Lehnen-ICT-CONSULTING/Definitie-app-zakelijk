"""
Modular Prompt Adapter V2 - Gebruikt geconsolideerde modules (DEF-127).

Deze versie gebruikt de nieuwe geconsolideerde modules die cognitive load
verminderen van 19 naar 9 modules.

Wijzigingen t.o.v. V1:
- Gebruikt UnifiedValidationRulesModule i.p.v. 5 aparte regel modules
- Gebruikt LinguisticRulesModule i.p.v. 3 aparte grammar modules
- Gebruikt OutputFormatModule i.p.v. 2 aparte output modules
"""

import hashlib
import logging
import threading
from typing import Any

from .modules import (
    ContextAwarenessModule,
    DefinitionTaskModule,
    ErrorPreventionModule,
    ExpertiseModule,
    MetricsModule,
    PromptOrchestrator,
    SemanticCategorisationModule,
)

# Import nieuwe geconsolideerde modules
from .modules.linguistic_rules_module import LinguisticRulesModule
from .modules.output_format_module import OutputFormatModule
from .modules.unified_validation_rules_module import UnifiedValidationRulesModule

logger = logging.getLogger(__name__)

# Singleton orchestrator cache
_global_orchestrator_v2: PromptOrchestrator | None = None
_orchestrator_lock_v2 = threading.Lock()


def get_cached_orchestrator_v2() -> PromptOrchestrator:
    """
    Get or create singleton PromptOrchestrator met geconsolideerde modules.
    Thread-safe lazy initialization.

    Returns:
        Cached PromptOrchestrator instance met 9 modules (ipv 19)
    """
    global _global_orchestrator_v2

    if _global_orchestrator_v2 is None:
        with _orchestrator_lock_v2:
            # Double-check locking pattern
            if _global_orchestrator_v2 is None:
                logger.info("🎯 Creating singleton PromptOrchestrator V2 (DEF-127)")
                orchestrator = PromptOrchestrator(max_workers=4)

                # Register 9 geconsolideerde modules (was 16-19)
                modules = [
                    # Core instruction modules (3)
                    ExpertiseModule(),
                    ErrorPreventionModule(),
                    DefinitionTaskModule(),
                    # Context processing (2)
                    ContextAwarenessModule(),
                    SemanticCategorisationModule(),
                    # Consolidated modules (3)
                    UnifiedValidationRulesModule(),  # Vervangt 5 regel modules
                    LinguisticRulesModule(),  # Vervangt 3 grammar modules
                    OutputFormatModule(),  # Vervangt 2 output modules
                    # Metrics (1)
                    MetricsModule(),
                ]

                for module in modules:
                    orchestrator.register_module(module)

                logger.info(
                    f"✅ PromptOrchestrator V2 cached: {len(orchestrator.modules)} modules "
                    f"(reduced from 19, DEF-127)"
                )
                _global_orchestrator_v2 = orchestrator

    return _global_orchestrator_v2


class ModularPromptAdapterV2:
    """
    Adapter V2 met geconsolideerde modules voor verminderde cognitive load.

    Deze klasse is een drop-in replacement voor ModularPromptBuilder
    maar gebruikt slechts 9 modules i.p.v. 19 (DEF-127).
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
            "ModularPromptAdapterV2 initialized - 9 consolidated modules (DEF-127)"
        )

    def _setup_orchestrator(self) -> None:
        """Setup de PromptOrchestrator met geconsolideerde modules."""
        # Use cached singleton V2
        self._orchestrator = get_cached_orchestrator_v2()

        # Converteer component config naar module configs
        module_configs = self._convert_config_to_module_configs()

        # Initialize modules met this adapter's config
        self._orchestrator.initialize_modules(module_configs)

        logger.debug("Orchestrator V2 setup voltooid met 9 modules")

    def _convert_config_to_module_configs(self) -> dict[str, dict[str, Any]]:
        """
        Converteer oude component config naar nieuwe module configuraties.

        Returns:
            Dictionary met module_id -> module config mapping
        """
        configs = {}

        # Core modules
        configs["expertise"] = {
            "include_role": True,
            "include_task": True,
        }

        configs["error_prevention"] = {
            "include_validation_matrix": getattr(
                self.component_config,
                "include_validation_matrix",
                getattr(self.component_config, "include_validation_rules", True),
            ),
            "extended_instructions": True,
        }

        configs["definition_task"] = {
            "include_checklist": getattr(
                self.component_config, "include_quality_checklist", True
            ),
            "include_metadata": True,
        }

        # Context modules
        configs["context_awareness"] = {
            "enhanced_processing": True,
            "adaptive_formatting": True,
        }

        configs["semantic_categorisation"] = {
            "include_guidance": True,
        }

        # Consolidated modules
        configs["unified_validation_rules"] = {
            "include_examples": getattr(
                self.component_config, "include_examples", True
            ),
            "categories": ["ARAI", "CON", "ESS", "SAM", "INT"],  # Alle categorieën
        }

        configs["linguistic_rules"] = {
            "include_examples": getattr(
                self.component_config, "include_examples", True
            ),
            "extended_grammar": getattr(
                self.component_config, "include_grammar_rules", True
            ),
        }

        configs["output_format"] = {
            "include_templates": getattr(
                self.component_config, "include_templates", True
            ),
            "strict_format": getattr(self.component_config, "strict_format", True),
            "char_limit_warning": 500,
        }

        # Metrics
        configs["metrics"] = {
            "include_scoring": getattr(self.component_config, "include_metrics", True),
        }

        return configs

    def build(
        self,
        term: str,
        examples: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Build complete prompt met geconsolideerde modules.

        Args:
            term: De term om te definiëren
            examples: Optionele voorbeeldzinnen
            context: Optionele context informatie

        Returns:
            Complete gegenereerde prompt
        """
        if not self._orchestrator:
            msg = "Orchestrator niet geïnitialiseerd"
            raise RuntimeError(msg)

        # Build module context
        from .modules import ModuleContext

        module_context = ModuleContext(
            term=term,
            examples=examples or [],
            variables=context or {},
        )

        # Execute orchestrator
        try:
            outputs = self._orchestrator.execute(module_context)

            # Combine outputs in juiste volgorde
            combined = self._orchestrator.combine_outputs(outputs)

            # Log statistics
            self._log_statistics(outputs)

            return combined

        except Exception as e:
            logger.error(f"Fout bij genereren prompt V2: {e}")
            raise

    def _log_statistics(self, outputs: dict[str, Any]) -> None:
        """Log statistieken over gegenereerde prompt."""
        total_length = sum(len(output.content) for output in outputs.values() if output)
        module_count = len([o for o in outputs.values() if o and o.content])

        logger.info(
            f"Prompt gegenereerd met {module_count} modules, "
            f"totale lengte: {total_length} karakters"
        )

    def get_cache_key(
        self,
        term: str,
        examples: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate cache key voor deze prompt configuratie.

        Args:
            term: De term
            examples: Voorbeeldzinnen
            context: Context informatie

        Returns:
            Unique cache key
        """
        key_parts = [
            "v2",  # Version identifier
            term,
            str(sorted(examples or [])),
            str(sorted((context or {}).items())),
            str(self.component_config.__dict__),
        ]

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_module_count(self) -> int:
        """
        Get aantal actieve modules.

        Returns:
            Aantal modules (zou 9 moeten zijn na consolidatie)
        """
        if not self._orchestrator:
            return 0
        return len(self._orchestrator.modules)

    def get_module_info(self) -> dict[str, str]:
        """
        Get informatie over alle modules.

        Returns:
            Dictionary met module_id -> module_name mapping
        """
        if not self._orchestrator:
            return {}

        return {
            module_id: module.module_name
            for module_id, module in self._orchestrator.modules.items()
        }
