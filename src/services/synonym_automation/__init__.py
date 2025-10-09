"""
Synonym automation services voor juridische termen.

Deze module bevat services voor het automatisch genereren en beheren van synoniemen:
- GPT4SynonymSuggester: AI-gestuurde synoniem suggesties
- YAMLConfigUpdater: Automatische YAML configuratie updates
- SynonymWorkflow: Workflow orchestratie voor suggest + approve
"""

from .gpt4_suggester import GPT4SynonymSuggester, SynonymSuggestion
from .yaml_updater import YAMLConfigUpdater, YAMLUpdateError

__all__ = [
    "GPT4SynonymSuggester",
    "SynonymSuggestion",
    "YAMLConfigUpdater",
    "YAMLUpdateError",
]
