"""
Base Module Interface voor Modulaire Prompt Architectuur.

Dit bestand definieert de abstract base class voor alle prompt modules.
Elke module moet deze interface implementeren voor consistente werking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext


@dataclass
class ModuleContext:
    """Context object dat tussen modules wordt doorgegeven."""

    begrip: str
    enriched_context: EnrichedContext
    config: UnifiedGeneratorConfig
    shared_state: dict[str, Any]  # Voor inter-module communicatie

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Haal metadata op uit enriched context."""
        return self.enriched_context.metadata.get(key, default)

    def set_shared(self, key: str, value: Any) -> None:
        """Sla gedeelde state op voor andere modules."""
        self.shared_state[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Haal gedeelde state op van andere modules."""
        return self.shared_state.get(key, default)


@dataclass
class ModuleOutput:
    """Output van een module execution."""

    content: str  # De gegenereerde prompt sectie
    metadata: dict[str, Any]  # Module-specifieke metadata
    success: bool = True
    error_message: str | None = None

    @property
    def is_empty(self) -> bool:
        """Check of de output leeg is."""
        return not self.content or not self.content.strip()


class BasePromptModule(ABC):
    """
    Abstract base class voor alle prompt modules.

    Elke module is verantwoordelijk voor één aspect van de prompt generatie.
    Modules kunnen onafhankelijk getest en vervangen worden.
    """

    def __init__(self, module_id: str, module_name: str, priority: int = 50):
        """
        Initialize base module.

        Args:
            module_id: Unieke identifier voor de module
            module_name: Menselijk leesbare naam
            priority: Module prioriteit (0-100, hoger = belangrijker)
        """
        self.module_id = module_id
        self.module_name = module_name
        self.priority = priority
        self._initialized = False
        self._config: dict[str, Any] = {}

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module-specifieke configuratie
        """

    @abstractmethod
    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer of deze module kan/moet draaien met gegeven context.

        Args:
            context: Module context met alle benodigde info

        Returns:
            Tuple van (is_valid, error_message)
        """

    @abstractmethod
    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Voer module logic uit en genereer prompt sectie.

        Args:
            context: Module context met alle benodigde info

        Returns:
            ModuleOutput met gegenereerde content
        """

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """
        Retourneer lijst van module IDs waarvan deze module afhankelijk is.

        Returns:
            Lijst van module IDs
        """

    def get_info(self) -> dict[str, Any]:
        """
        Retourneer module informatie voor debugging/monitoring.

        Returns:
            Dictionary met module info
        """
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "priority": self.priority,
            "initialized": self._initialized,
            "dependencies": self.get_dependencies(),
            "config": self._config,
        }

    def __repr__(self) -> str:
        """String representatie voor debugging."""
        return f"{self.__class__.__name__}(id='{self.module_id}', name='{self.module_name}')"


class CompositeModule(BasePromptModule):
    """
    Een module die uit meerdere sub-modules bestaat.

    Useful voor het groeperen van gerelateerde functionaliteit.
    """

    def __init__(self, module_id: str, module_name: str):
        """Initialize composite module."""
        super().__init__(module_id, module_name)
        self.sub_modules: list[BasePromptModule] = []

    def add_sub_module(self, module: BasePromptModule) -> None:
        """Voeg sub-module toe."""
        self.sub_modules.append(module)

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize alle sub-modules."""
        self._config = config
        for module in self.sub_modules:
            sub_config = config.get(module.module_id, {})
            module.initialize(sub_config)
        self._initialized = True

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Valideer input voor alle sub-modules."""
        for module in self.sub_modules:
            is_valid, error = module.validate_input(context)
            if not is_valid:
                return False, f"[{module.module_id}] {error}"
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Execute alle sub-modules en combineer output."""
        outputs = []
        combined_metadata = {}

        for module in self.sub_modules:
            output = module.execute(context)
            if not output.success:
                return ModuleOutput(
                    content="",
                    metadata={"failed_module": module.module_id},
                    success=False,
                    error_message=f"Sub-module {module.module_id} failed: {output.error_message}",
                )

            if not output.is_empty:
                outputs.append(output.content)
                combined_metadata[module.module_id] = output.metadata

        # Combineer outputs met newlines
        combined_content = "\n\n".join(outputs)

        return ModuleOutput(
            content=combined_content,
            metadata={
                "sub_modules": [m.module_id for m in self.sub_modules],
                "sub_module_metadata": combined_metadata,
            },
        )

    def get_dependencies(self) -> list[str]:
        """Verzamel alle dependencies van sub-modules."""
        all_deps = []
        for module in self.sub_modules:
            all_deps.extend(module.get_dependencies())
        # Remove duplicates while preserving order
        return list(dict.fromkeys(all_deps))
