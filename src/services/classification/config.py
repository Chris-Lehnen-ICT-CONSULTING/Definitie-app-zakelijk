"""
Configuration for OntologyClassifierService using Pydantic BaseSettings.

Environment variables kunnen gebruikt worden om configuratie te overriden:
    ONTOLOGY_PROMPT_PATH: Path to YAML prompt template
    ONTOLOGY_TEMPERATURE: LLM temperature (0.0-2.0)
    ONTOLOGY_MAX_TOKENS: Max tokens for response
    ONTOLOGY_FALLBACK_LEVEL: Fallback classification level
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

OntologyLevel = Literal["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT", "ONBESLIST"]


class OntologyClassifierConfig(BaseSettings):
    """
    Configuration voor OntologyClassifierService.

    Deze configuratie kan worden geïnjecteerd in de service voor:
    - Testbaarheid (mock config voor unit tests)
    - Environment-specifieke settings (dev/staging/prod)
    - Runtime overrides zonder code wijzigingen

    Environment variables:
        ONTOLOGY_PROMPT_PATH: Path to YAML prompt template
        ONTOLOGY_TEMPERATURE: LLM temperature (0.0-2.0)
        ONTOLOGY_MAX_TOKENS: Max tokens for response
        ONTOLOGY_FALLBACK_LEVEL: Fallback classification on errors

    Example:
        >>> # Default config
        >>> config = OntologyClassifierConfig()
        >>>
        >>> # Override via constructor
        >>> config = OntologyClassifierConfig(temperature=0.5)
        >>>
        >>> # Override via environment
        >>> # export ONTOLOGY_TEMPERATURE=0.5
        >>> config = OntologyClassifierConfig()
    """

    prompt_path: Path = Field(
        default=Path("config/prompts/ontology_classification.yaml"),
        description="Path to YAML prompt template",
    )

    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature for classification (lower = more consistent)",
    )

    max_tokens: int = Field(
        default=500,
        gt=0,
        le=4000,
        description="Maximum tokens for LLM response",
    )

    fallback_level: OntologyLevel = Field(
        default="ONBESLIST",
        description="Fallback classification level on errors",
    )

    @field_validator("prompt_path")
    @classmethod
    def validate_prompt_path_exists(cls, v: Path) -> Path:
        """
        Valideer dat prompt template bestaat.

        Raises:
            ValueError: Als prompt bestand niet bestaat
        """
        if not v.exists():
            msg = f"Prompt template niet gevonden: {v}"
            raise ValueError(msg)
        return v

    model_config = {
        "env_prefix": "ONTOLOGY_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore onbekende velden (zoals OPENAI_API_KEY)
    }
