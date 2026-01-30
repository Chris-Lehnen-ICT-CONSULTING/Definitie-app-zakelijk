"""
Prompt Orchestrator - Coördineert alle prompt modules voor modulaire prompt generatie.

Deze orchestrator is verantwoordelijk voor:
1. Module registratie en lifecycle management
2. Dependency resolution en execution order
3. Parallel en sequential execution
4. Output combinatie en validatie
"""

import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ModuleExecutionError(Exception):
    """Raised wanneer een module executie faalt."""


class DependencyCycleError(Exception):
    """Raised wanneer er een cyclische dependency is."""


class PromptOrchestrator:
    """
    Orchestreert de uitvoering van prompt modules.

    Beheert module registratie, dependency resolution, parallel execution,
    en output combinatie voor het genereren van de complete prompt.
    """

    def __init__(self, max_workers: int = 4, module_order: list[str] | None = None):
        """
        Initialize de orchestrator.

        Args:
            max_workers: Maximum aantal parallel workers voor module execution
            module_order: Optionele lijst met module IDs voor output volgorde
        """
        self.modules: dict[str, BasePromptModule] = {}
        self.module_order: list[str] = module_order or []
        self.dependency_graph: dict[str, set[str]] = defaultdict(set)
        self.max_workers = max_workers
        self._execution_metadata: dict[str, Any] = {}
        self._custom_module_order = module_order or self._get_default_module_order()

        # Log after modules are registered instead
        logger.debug(f"PromptOrchestrator created with {max_workers} workers")

    def register_module(self, module: BasePromptModule) -> None:
        """
        Registreer een module bij de orchestrator.

        Args:
            module: De module om te registreren

        Raises:
            ValueError: Als module ID al geregistreerd is
        """
        if module.module_id in self.modules:
            msg = f"Module '{module.module_id}' is al geregistreerd"
            raise ValueError(msg)

        self.modules[module.module_id] = module
        dependencies = module.get_dependencies()
        self.dependency_graph[module.module_id] = set(dependencies)

        logger.debug(
            f"Module '{module.module_id}' geregistreerd met {len(dependencies)} dependencies"
        )

    def initialize_modules(self, config: dict[str, dict[str, Any]]) -> None:
        """
        Initialize alle geregistreerde modules met hun configuratie.

        Args:
            config: Dictionary met module_id -> module config mapping
        """
        for module_id, module in self.modules.items():
            module_config = config.get(module_id, {})
            try:
                module.initialize(module_config)
                logger.debug(f"Module '{module_id}' succesvol geïnitialiseerd")
            except Exception as e:
                logger.error(f"Fout bij initialiseren module '{module_id}': {e}")
                raise

    def resolve_execution_order(self) -> list[list[str]]:
        """
        Bepaal de execution order op basis van dependencies.

        Returns:
            List van batches - elke batch kan parallel uitgevoerd worden

        Raises:
            DependencyCycleError: Als er een cyclische dependency is
        """
        # Kahn's algorithm voor topological sort met batch detection
        in_degree = dict.fromkeys(self.modules, 0)

        # Bereken in-degrees - tel hoeveel modules afhankelijk zijn van elke module
        for module_id, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                if dep in in_degree:  # Skip externe dependencies
                    in_degree[module_id] += 1  # module_id is afhankelijk van dep

        # Vind modules zonder dependencies (kunnen parallel)
        batches = []
        remaining = set(self.modules.keys())

        while remaining:
            # Vind alle modules die nu uitgevoerd kunnen worden
            current_batch = [
                module_id for module_id in remaining if in_degree[module_id] == 0
            ]

            if not current_batch:
                # Cyclische dependency gedetecteerd
                msg = f"Cyclische dependency gedetecteerd in modules: {remaining}"
                raise DependencyCycleError(msg)

            batches.append(current_batch)

            # Update in-degrees voor volgende iteratie
            for module_id in current_batch:
                remaining.remove(module_id)
                for dependent in self.modules:
                    if module_id in self.dependency_graph[dependent]:
                        in_degree[dependent] -= 1

        logger.debug(f"Execution order bepaald: {len(batches)} batches")
        return batches

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """
        Bouw de complete prompt door alle modules te orchestreren.

        Args:
            begrip: Het begrip om te definiëren
            context: Verrijkte context informatie
            config: Generator configuratie

        Returns:
            Complete prompt string

        Raises:
            ModuleExecutionError: Als een module faalt
        """
        start_time = time.time()

        # DEF-123: Bepaal welke modules actief zijn op basis van context
        active_modules = self._get_active_modules(context, config)

        # Maak module context voor sharing tussen modules
        module_context = ModuleContext(
            begrip=begrip, enriched_context=context, config=config, shared_state={}
        )

        # Bepaal execution order
        try:
            execution_batches = self.resolve_execution_order()
        except DependencyCycleError as e:
            logger.error(f"Dependency cycle error: {e}")
            raise

        # Execute modules batch voor batch (DEF-123: alleen actieve modules)
        all_outputs: dict[str, ModuleOutput] = {}

        for batch_idx, batch in enumerate(execution_batches):
            # DEF-123: Filter batch to only include active modules
            active_batch = [m for m in batch if m in active_modules]

            if not active_batch:
                logger.debug(f"Skipping batch {batch_idx + 1}: no active modules")
                continue

            logger.debug(f"Executing batch {batch_idx + 1}: {active_batch}")

            if len(active_batch) == 1:
                # Single module - execute sequentially
                module_id = active_batch[0]
                output = self._execute_module(module_id, module_context)
                all_outputs[module_id] = output
            else:
                # Multiple modules - execute parallel
                batch_outputs = self._execute_batch_parallel(
                    active_batch, module_context
                )
                all_outputs.update(batch_outputs)

        # Combineer alle outputs in de juiste volgorde
        combined_prompt = self._combine_outputs(all_outputs)

        # Verzamel execution metadata (DEF-123: include active/skipped info)
        execution_time = time.time() - start_time
        skipped_modules = set(self.modules.keys()) - active_modules
        self._execution_metadata = {
            "begrip": begrip,
            "total_modules": len(self.modules),
            "active_modules": len(active_modules),
            "skipped_modules": sorted(skipped_modules),
            "execution_batches": len(execution_batches),
            "execution_time_ms": round(execution_time * 1000, 2),
            "prompt_length": len(combined_prompt),
            "module_metadata": {
                module_id: output.metadata for module_id, output in all_outputs.items()
            },
        }

        logger.info(
            f"Prompt gebouwd voor '{begrip}': {len(combined_prompt)} chars "
            f"in {self._execution_metadata['execution_time_ms']}ms "
            f"({len(active_modules)}/{len(self.modules)} modules)"
        )

        return combined_prompt

    def _execute_module(self, module_id: str, context: ModuleContext) -> ModuleOutput:
        """
        Execute een enkele module.

        Args:
            module_id: ID van de module
            context: Module context

        Returns:
            Module output

        Raises:
            ModuleExecutionError: Als module executie faalt
        """
        module = self.modules[module_id]

        try:
            # Valideer input
            is_valid, error_msg = module.validate_input(context)
            if not is_valid:
                logger.warning(f"Module '{module_id}' validation failed: {error_msg}")
                return ModuleOutput(
                    content="",
                    metadata={"skipped_reason": error_msg},
                    success=False,
                    error_message=error_msg,
                )

            # Execute module
            start_time = time.time()
            output = module.execute(context)
            execution_time = time.time() - start_time

            # Voeg execution time toe aan metadata
            output.metadata["execution_time_ms"] = round(execution_time * 1000, 2)

            if output.success:
                logger.debug(
                    f"Module '{module_id}' executed successfully in "
                    f"{output.metadata['execution_time_ms']}ms"
                )
            else:
                logger.warning(f"Module '{module_id}' failed: {output.error_message}")

            return output

        except Exception as e:
            logger.error(f"Module '{module_id}' execution error: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"exception": str(e)},
                success=False,
                error_message=f"Module execution failed: {e!s}",
            )

    def _execute_batch_parallel(
        self, batch: list[str], context: ModuleContext
    ) -> dict[str, ModuleOutput]:
        """
        Execute een batch van modules parallel.

        Args:
            batch: List van module IDs om parallel uit te voeren
            context: Module context

        Returns:
            Dictionary van module_id -> output
        """
        outputs = {}

        with ThreadPoolExecutor(
            max_workers=min(len(batch), self.max_workers)
        ) as executor:
            future_to_module = {
                executor.submit(self._execute_module, module_id, context): module_id
                for module_id in batch
            }

            for future in as_completed(future_to_module):
                module_id = future_to_module[future]
                try:
                    output = future.result()
                    outputs[module_id] = output
                except Exception as e:
                    logger.error(f"Parallel execution error voor '{module_id}': {e}")
                    outputs[module_id] = ModuleOutput(
                        content="",
                        metadata={"parallel_error": str(e)},
                        success=False,
                        error_message=f"Parallel execution failed: {e!s}",
                    )

        return outputs

    def _combine_outputs(self, outputs: dict[str, ModuleOutput]) -> str:
        """
        Combineer module outputs in de juiste volgorde.

        Args:
            outputs: Dictionary van module outputs

        Returns:
            Gecombineerde prompt string
        """
        ordered_sections = []

        # Gebruik custom module order of default
        module_order = self._custom_module_order

        # Verzamel outputs in volgorde
        for module_id in module_order:
            if module_id in outputs:
                output = outputs[module_id]
                if output.success and not output.is_empty:
                    ordered_sections.append(output.content)

        # Voeg ook outputs toe van modules die niet in de standaard volgorde staan
        for module_id, output in outputs.items():
            if module_id not in module_order and output.success and not output.is_empty:
                ordered_sections.append(output.content)

        # Combineer met consistent spacing
        return "\n\n".join(ordered_sections)

    def set_module_order(self, module_order: list[str]) -> None:
        """
        Update de module output volgorde.

        Args:
            module_order: Lijst met module IDs in gewenste volgorde
        """
        self._custom_module_order = module_order
        logger.debug(f"Module volgorde aangepast: {module_order}")

    def _get_default_module_order(self) -> list[str]:
        """
        Verkrijg de standaard module volgorde.

        Returns:
            Lijst met module IDs in standaard volgorde
        """
        return [
            "expertise",
            "context_awareness",  # DEF-188: Moved to position 2 (was 4)
            "output_specification",
            "grammar",
            "semantic_categorisation",
            "template",
            # Validatie regels in logische volgorde
            "arai_rules",  # Algemene regels eerst
            "con_rules",  # Context regels
            "ess_rules",  # Essentie regels
            "structure_rules",  # Structuur regels
            "integrity_rules",  # Integriteit regels
            "sam_rules",  # Samenhang regels
            "ver_rules",  # Vorm regels
            "error_prevention",
            "metrics",
            "definition_task",
        ]

    def _get_active_modules(
        self, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> set[str]:
        """
        DEF-123: Bepaal welke modules actief moeten zijn op basis van context.

        Filtert modules op basis van:
        - Core modules: altijd actief
        - Context modules: alleen als relevante context aanwezig is
        - Debug modules: alleen in debug mode
        - Unknown modules: altijd actief (voor backwards compatibility en tests)

        Args:
            context: Verrijkte context informatie
            config: Generator configuratie

        Returns:
            Set van actieve module IDs
        """
        # Known modules that we can filter
        known_modules = {
            "expertise",
            "output_specification",
            "definition_task",
            "semantic_categorisation",
            "grammar",
            "template",
            "context_awareness",
            "arai_rules",
            "con_rules",
            "ess_rules",
            "structure_rules",
            "integrity_rules",
            "sam_rules",
            "ver_rules",
            "error_prevention",
            "metrics",
        }

        # Core modules - altijd actief (essential for any definition)
        active = {
            "expertise",
            "output_specification",
            "definition_task",
            "semantic_categorisation",  # Needed to determine category
            "grammar",  # Basic grammar rules always needed
            "template",  # Template structure always useful
        }

        # Context-aware modules (DEF-123 optimization)
        if context.has_any_context():
            active.add("context_awareness")
            logger.debug(
                "DEF-123: context_awareness module activated (context present)"
            )
        else:
            logger.debug("DEF-123: context_awareness module skipped (no context)")

        # Rule modules - always include core rules
        # ARAI (general rules) and VER (form rules) are always needed
        active.add("arai_rules")
        active.add("ver_rules")

        # Context-dependent rule modules
        if context.has_juridische_context() or context.has_wettelijke_context():
            # Legal context requires integrity and coherence rules
            active.add("integrity_rules")
            active.add("sam_rules")
            active.add("con_rules")
            logger.debug("DEF-123: Legal rule modules activated (juridische context)")

        # ESS and STR rules are category-dependent but we don't know category yet
        # Include both for now - can be optimized in Phase 2 with pre-classification
        active.add("ess_rules")
        active.add("structure_rules")

        # Debug/metrics module - only in debug mode
        debug_mode = getattr(config, "debug_mode", False) or getattr(
            config, "include_metrics", False
        )
        if debug_mode:
            active.add("metrics")
            logger.debug("DEF-123: metrics module activated (debug mode)")
        else:
            logger.debug("DEF-123: metrics module skipped (not in debug mode)")

        # Get all registered modules
        registered = set(self.modules.keys())

        # Unknown modules (not in our known list) are always active
        # This ensures backwards compatibility and test modules work
        unknown_modules = registered - known_modules
        if unknown_modules:
            active.update(unknown_modules)
            logger.debug(f"DEF-123: Unknown modules always active: {unknown_modules}")

        # Filter to only registered modules
        active_registered = active & registered

        # Log summary
        skipped = registered - active_registered
        if skipped:
            logger.info(
                f"DEF-123: {len(active_registered)}/{len(registered)} modules active, "
                f"skipped: {sorted(skipped)}"
            )

        return active_registered

    def get_execution_metadata(self) -> dict[str, Any]:
        """
        Verkrijg metadata van de laatste prompt generatie.

        Returns:
            Dictionary met execution metadata
        """
        return self._execution_metadata.copy()

    def get_registered_modules(self) -> list[dict[str, Any]]:
        """
        Verkrijg informatie over alle geregistreerde modules.

        Returns:
            List van module informatie dictionaries gesorteerd op prioriteit
        """
        modules_info = [
            {
                "module_id": module_id,
                "module_name": module.module_name,
                "priority": module.priority,
                "dependencies": list(self.dependency_graph[module_id]),
                "info": module.get_info(),
            }
            for module_id, module in self.modules.items()
        ]

        # Sorteer op prioriteit (hoogste eerst)
        return sorted(modules_info, key=lambda x: x["priority"], reverse=True)

    def get_modules_by_priority(self) -> list[str]:
        """
        Verkrijg module IDs gesorteerd op prioriteit.

        Returns:
            Lijst van module IDs gesorteerd op prioriteit (hoogste eerst)
        """
        sorted_modules = sorted(
            self.modules.items(), key=lambda x: x[1].priority, reverse=True
        )
        return [module_id for module_id, _ in sorted_modules]
