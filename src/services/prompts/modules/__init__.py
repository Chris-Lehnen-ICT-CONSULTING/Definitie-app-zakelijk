"""
Prompt Modules - Elke module is verantwoordelijk voor één logisch blok van de prompt.

Orchestrator pattern: PromptOrchestrator roept modules aan in de juiste volgorde.

DEF-156 Phase 1: JSON-based rule modules consolidated into JSONBasedRulesModule.
"""

# Base classes
from .base_module import BasePromptModule, CompositeModule, ModuleContext, ModuleOutput
from .context_awareness_module import ContextAwarenessModule
from .definition_task_module import DefinitionTaskModule
from .error_prevention_module import ErrorPreventionModule

# Concrete modules
from .expertise_module import ExpertiseModule
from .grammar_module import GrammarModule
from .integrity_rules_module import IntegrityRulesModule

# Generic JSON-based rule module (DEF-156: replaces ARAI, CON, ESS, SAM, VER wrappers)
from .json_based_rules_module import JSONBasedRulesModule
from .metrics_module import MetricsModule
from .output_specification_module import OutputSpecificationModule

# Orchestrator
from .prompt_orchestrator import PromptOrchestrator

# Other modules
from .semantic_categorisation_module import SemanticCategorisationModule
from .structure_rules_module import StructureRulesModule
from .template_module import TemplateModule

__all__ = [
    # Base classes
    "BasePromptModule",
    "CompositeModule",
    "ContextAwarenessModule",
    "DefinitionTaskModule",
    "ErrorPreventionModule",
    # Core modules
    "ExpertiseModule",
    "GrammarModule",
    "IntegrityRulesModule",
    # Generic JSON-based module (DEF-156)
    "JSONBasedRulesModule",
    "MetricsModule",
    "ModuleContext",
    "ModuleOutput",
    "OutputSpecificationModule",
    # Orchestrator
    "PromptOrchestrator",
    # Other modules
    "SemanticCategorisationModule",
    "StructureRulesModule",
    "TemplateModule",
]
