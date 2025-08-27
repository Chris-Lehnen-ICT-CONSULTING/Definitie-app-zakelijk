"""
Context Awareness Module - Verwerkt organisatorische en domein context.

Deze module is verantwoordelijk voor:
1. Organisatorische context verwerking
2. Domein context verwerking
3. Context formatting voor de prompt
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ContextAwarenessModule(BasePromptModule):
    """
    Module voor het verwerken van organisatorische en domein context.

    Genereert de context sectie van de prompt alleen wanneer
    daadwerkelijk context informatie beschikbaar is.
    """

    def __init__(self):
        """Initialize de context awareness module."""
        super().__init__(
            module_id="context_awareness", module_name="Context Processing Module"
        )

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self._initialized = True
        logger.info("ContextAwarenessModule geïnitialiseerd")

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer of er context informatie beschikbaar is.

        Args:
            context: Module context

        Returns:
            (True, None) als er context is, anders (False, reason)
        """
        # Check of er context informatie is
        base_context = context.enriched_context.base_context
        has_org_context = bool(base_context.get("organisatorisch"))
        has_domain_context = bool(base_context.get("domein"))

        if not (has_org_context or has_domain_context):
            return False, "Geen context informatie beschikbaar"

        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer context sectie voor de prompt.

        Args:
            context: Module context met context informatie

        Returns:
            ModuleOutput met context sectie
        """
        try:
            base_context = context.enriched_context.base_context

            # Extract context informatie
            org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
            domain_contexts = self._extract_contexts(base_context.get("domein"))

            # Sla op voor andere modules (zoals ErrorPreventionModule)
            if org_contexts:
                context.set_shared("organization_contexts", org_contexts)
            if domain_contexts:
                context.set_shared("domain_contexts", domain_contexts)

            # Bouw context sectie
            content = self._build_context_section(org_contexts, domain_contexts)

            return ModuleOutput(
                content=content,
                metadata={
                    "organization_count": len(org_contexts),
                    "domain_count": len(domain_contexts),
                    "organizations": org_contexts,
                    "domains": domain_contexts,
                },
            )

        except Exception as e:
            logger.error(f"ContextAwarenessModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate context section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _extract_contexts(self, context_value: Any) -> list[str]:
        """
        Extract context lijst uit verschillende input formaten.

        Args:
            context_value: Context waarde (bool, str, list, etc.)

        Returns:
            Lijst van context strings
        """
        if not context_value:
            return []

        # Handle verschillende input types
        if isinstance(context_value, bool):
            # Legacy support: True betekent geen specifieke context
            return []
        if isinstance(context_value, str):
            return [context_value]
        if isinstance(context_value, list):
            return [str(item) for item in context_value if item]
        logger.warning(
            f"Onbekend context type: {type(context_value)} - {context_value}"
        )
        return []

    def _build_context_section(
        self, org_contexts: list[str], domain_contexts: list[str]
    ) -> str:
        """
        Bouw de context sectie.

        Args:
            org_contexts: Lijst van organisatorische contexten
            domain_contexts: Lijst van domein contexten

        Returns:
            Geformatteerde context sectie
        """
        lines = ["📌 Context:"]

        # Organisatorische context
        if org_contexts:
            contexts_str = ", ".join(org_contexts)
            lines.append(f"- Organisatorische context(en): {contexts_str}")
            logger.debug(f"Organisatorische context toegevoegd: {org_contexts}")

        # Domein context
        if domain_contexts:
            domains_str = ", ".join(domain_contexts)
            lines.append(f"- domein: {domains_str}")
            logger.debug(f"Domein context toegevoegd: {domain_contexts}")

        return "\n".join(lines)
