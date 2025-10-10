"""
Prompt Modules - Elke module is verantwoordelijk voor één logisch blok van de prompt.

Orchestrator pattern: PromptOrchestrator roept modules aan in de juiste volgorde.
"""

# Base classes
# Rule modules - elke categorie heeft eigen module
from .arai_rules_module import AraiRulesModule
from .base_module import BasePromptModule, CompositeModule, ModuleContext, ModuleOutput
from .con_rules_module import ConRulesModule
from .context_awareness_module import ContextAwarenessModule
from .definition_task_module import DefinitionTaskModule
from .error_prevention_module import ErrorPreventionModule
from .ess_rules_module import EssRulesModule

# Concrete modules
from .expertise_module import ExpertiseModule
from .grammar_module import GrammarModule
from .integrity_rules_module import IntegrityRulesModule
from .metrics_module import MetricsModule
from .output_specification_module import OutputSpecificationModule

# Orchestrator
from .prompt_orchestrator import PromptOrchestrator
from .sam_rules_module import SamRulesModule

# Other modules
from .semantic_categorisation_module import SemanticCategorisationModule
from .structure_rules_module import StructureRulesModule
from .template_module import TemplateModule
from .ver_rules_module import VerRulesModule

__all__ = [
    # Rule modules
    "AraiRulesModule",
    # Base classes
    "BasePromptModule",
    "CompositeModule",
    "ConRulesModule",
    "ContextAwarenessModule",
    "DefinitionTaskModule",
    "ErrorPreventionModule",
    "EssRulesModule",
    # Core modules
    "ExpertiseModule",
    "GrammarModule",
    "IntegrityRulesModule",
    "MetricsModule",
    "ModuleContext",
    "ModuleOutput",
    "OutputSpecificationModule",
    # Orchestrator
    "PromptOrchestrator",
    "SamRulesModule",
    # Other modules
    "SemanticCategorisationModule",
    "StructureRulesModule",
    "TemplateModule",
    "VerRulesModule",
]
