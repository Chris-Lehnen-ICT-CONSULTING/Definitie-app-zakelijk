"""
Metrics Module - Meet en rapporteer kwaliteitsmetrieken voor definities.

Deze module is verantwoordelijk voor:
1. Character count tracking
2. Complexity scoring
3. Rule compliance metrics
4. Quality indicators
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class MetricsModule(BasePromptModule):
    """
    Module voor kwaliteitsmetrieken en scoring.

    Genereert metrics en kwaliteitsindicatoren die gebruikt kunnen
    worden voor monitoring en verbetering van definitie kwaliteit.
    """

    def __init__(self):
        """Initialize de metrics module."""
        super().__init__(
            module_id="metrics",
            module_name="Quality Metrics & Scoring",
            priority=30,
        )
        # Module disabled in DEF-171 - no configuration needed

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self._initialized = True
        logger.debug("MetricsModule initialized (disabled in DEF-171)")

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd maar kan optioneel zijn.

        Args:
            context: Module context

        Returns:
            (is_valid, error_message)
        """
        # Deze module is optioneel en kan altijd draaien
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Metrics module disabled - quality metrics removed in DEF-171 Phase 1.

        Rationale: Output metrics guide post-generation validation, not generation itself.
        ValidationOrchestratorV2 handles quality checks.

        Args:
            context: Module context

        Returns:
            ModuleOutput with empty content
        """
        try:
            # Module generates no content (metrics removed)
            return ModuleOutput(
                content="",
                metadata={
                    "disabled_reason": "DEF-171 Phase 1: Quality metrics removed",
                    "validation_handled_by": "ValidationOrchestratorV2",
                },
            )

        except Exception as e:
            logger.error(f"MetricsModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to execute metrics module: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen harde dependencies.

        Returns:
            Lege lijst
        """
        return []
