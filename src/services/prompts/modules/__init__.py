"""
Prompt Modules - Elke module is verantwoordelijk voor één logisch blok van de prompt.

Orchestrator pattern: PromptOrchestrator roept modules aan in de juiste volgorde.
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
from .output_specification_module import OutputSpecificationModule

# Orchestrator
from .prompt_orchestrator import PromptOrchestrator
from .quality_rules_module import QualityRulesModule
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
    # Implemented modules
    "ExpertiseModule",
    "GrammarModule",
    "IntegrityRulesModule",
    "ModuleContext",
    "ModuleOutput",
    "OutputSpecificationModule",
    # Orchestrator
    "PromptOrchestrator",
    "QualityRulesModule",
    "SemanticCategorisationModule",
    "StructureRulesModule",
    "TemplateModule",
]
