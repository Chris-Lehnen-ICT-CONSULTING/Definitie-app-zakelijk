"""
Prompt Modules - Elke module is verantwoordelijk voor één logisch blok van de prompt.

Orchestrator pattern: PromptOrchestrator roept modules aan in de juiste volgorde.

DEF-127: Geconsolideerde modules toegevoegd om cognitive load te verminderen (19 → 9).
"""

# Base classes
# Legacy modules (deprecated maar behouden voor backward compatibility)
from .arai_rules_module import AraiRulesModule
from .base_module import BasePromptModule, CompositeModule, ModuleContext, ModuleOutput
from .con_rules_module import ConRulesModule

# Core modules (behouden)
from .context_awareness_module import ContextAwarenessModule
from .definition_task_module import DefinitionTaskModule
from .error_prevention_module import ErrorPreventionModule
from .ess_rules_module import EssRulesModule
from .expertise_module import ExpertiseModule
from .grammar_module import GrammarModule
from .integrity_rules_module import IntegrityRulesModule

# Consolidated modules (DEF-127)
from .linguistic_rules_module import LinguisticRulesModule
from .metrics_module import MetricsModule
from .output_format_module import OutputFormatModule
from .output_specification_module import OutputSpecificationModule

# Orchestrator
from .prompt_orchestrator import PromptOrchestrator
from .sam_rules_module import SamRulesModule
from .semantic_categorisation_module import SemanticCategorisationModule
from .structure_rules_module import StructureRulesModule
from .template_module import TemplateModule
from .unified_validation_rules_module import UnifiedValidationRulesModule
from .ver_rules_module import VerRulesModule

__all__ = [
    # Base classes
    "BasePromptModule",
    "CompositeModule",
    "ModuleContext",
    "ModuleOutput",
    # Core modules (9 total)
    "ContextAwarenessModule",
    "DefinitionTaskModule",
    "ErrorPreventionModule",
    "ExpertiseModule",
    "MetricsModule",
    "SemanticCategorisationModule",
    # Orchestrator
    "PromptOrchestrator",
    # Consolidated modules (DEF-127)
    "UnifiedValidationRulesModule",
    "LinguisticRulesModule",
    "OutputFormatModule",
    # Legacy modules (deprecated)
    "AraiRulesModule",
    "ConRulesModule",
    "EssRulesModule",
    "GrammarModule",
    "IntegrityRulesModule",
    "OutputSpecificationModule",
    "SamRulesModule",
    "StructureRulesModule",
    "TemplateModule",
    "VerRulesModule",
]
