"""
SynonymConfiguration - Centralized YAML-based configuration management.

This module provides governance policy, thresholds, and caching configuration
for the Synonym Orchestrator Architecture v3.1.

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 544-599: Configuration specification

Usage:
    from config.synonym_config import get_synonym_config, SynonymPolicy

    config = get_synonym_config()
    if config.policy == SynonymPolicy.STRICT:
        # Only use approved synonyms
        statuses = ['active']
    else:
        # Allow AI-pending synonyms too
        statuses = ['active', 'ai_pending']
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SynonymPolicy(Enum):
    """
    Governance policy voor synoniemen gebruik.

    STRICT: Alleen approved synoniemen (status='active')
    PRAGMATIC: AI-pending ook toegestaan voor weblookup
    """

    STRICT = "strict"
    PRAGMATIC = "pragmatic"


@dataclass
class SynonymConfiguration:
    """
    Centralized configuration voor Synonym Orchestrator.

    Alle thresholds, policies en caching instellingen zijn hier gecentraliseerd
    en laden via YAML met fallback naar defaults.

    Attributes:
        policy: Governance policy (strict vs pragmatic)
        min_synonyms_threshold: Minimum synoniemen voordat GPT-4 enrichment start
        gpt4_timeout_seconds: Timeout voor GPT-4 API calls
        gpt4_max_retries: Maximum retry pogingen bij GPT-4 failures
        cache_ttl_seconds: Time-to-live voor TTL cache (in seconden)
        cache_max_size: Maximum aantal entries in cache
        min_weight_for_weblookup: Minimum weight voor synoniemen in weblookup
        preferred_weight_threshold: Weight threshold voor is_preferred flag
    """

    # Governance
    policy: SynonymPolicy = SynonymPolicy.STRICT

    # Enrichment
    min_synonyms_threshold: int = 5
    gpt4_timeout_seconds: int = 30
    gpt4_max_retries: int = 3

    # Caching
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 1000

    # Weights
    min_weight_for_weblookup: float = 0.7
    preferred_weight_threshold: float = 0.95

    @classmethod
    def from_yaml(cls, path: str) -> "SynonymConfiguration":
        """
        Load configuration from YAML file.

        Merges YAML values with defaults. Handles missing file gracefully by
        using defaults. Validates all values for correct ranges and types.

        Args:
            path: Path naar YAML configuratie bestand (relatief of absoluut)

        Returns:
            SynonymConfiguration instance met merged settings

        Raises:
            ValueError: Bij ongeldige configuratie waarden
        """
        import yaml

        config_path = Path(path)

        # Use defaults if file missing
        if not config_path.exists():
            logger.warning(
                f"Config file not found: {path}, using defaults. "
                f"Create file to customize settings."
            )
            return cls()

        # Load YAML
        try:
            with open(config_path) as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load YAML config from {path}: {e}")
            logger.warning("Falling back to default configuration")
            return cls()

        # Handle empty YAML file (returns None)
        if yaml_data is None:
            logger.warning(f"Empty YAML file: {path}, using defaults")
            return cls()

        # Extract synonym_configuration section
        config_data = yaml_data.get("synonym_configuration", {})

        if not config_data:
            logger.warning(
                f"No 'synonym_configuration' section found in {path}, using defaults"
            )
            return cls()

        # Map YAML keys to dataclass fields with validation
        try:
            # Parse policy (with validation)
            policy_str = config_data.get("policy", "strict")
            try:
                policy = SynonymPolicy(policy_str)
            except ValueError:
                logger.error(
                    f"Invalid policy value: '{policy_str}'. "
                    f"Must be 'strict' or 'pragmatic'. Using default: strict"
                )
                policy = SynonymPolicy.STRICT

            # Parse numeric fields
            min_synonyms = config_data.get("min_synonyms", 5)
            gpt4_timeout = config_data.get("gpt4_timeout", 30)
            gpt4_retries = config_data.get("gpt4_max_retries", 3)
            cache_ttl = config_data.get("cache_ttl", 3600)
            cache_max = config_data.get("cache_max_size", 1000)
            min_weight = config_data.get("min_weight", 0.7)
            preferred_threshold = config_data.get("preferred_threshold", 0.95)

            # Create instance
            config = cls(
                policy=policy,
                min_synonyms_threshold=min_synonyms,
                gpt4_timeout_seconds=gpt4_timeout,
                gpt4_max_retries=gpt4_retries,
                cache_ttl_seconds=cache_ttl,
                cache_max_size=cache_max,
                min_weight_for_weblookup=min_weight,
                preferred_weight_threshold=preferred_threshold,
            )

            # Validate configuration
            errors = config.validate()
            if errors:
                error_msg = "; ".join(errors)
                msg = f"Invalid configuration: {error_msg}"
                raise ValueError(msg)

            logger.info(
                f"Configuration loaded from {path}: "
                f"policy={config.policy.value}, "
                f"min_synonyms={config.min_synonyms_threshold}, "
                f"cache_ttl={config.cache_ttl_seconds}s"
            )

            return config

        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def validate(self) -> list[str]:
        """
        Valideer configuratie en retourneer lijst van problemen.

        Checks all numeric ranges, dependencies and constraints.

        Returns:
            Lege lijst als geldig, anders lijst van error messages
        """
        errors = []

        # Enrichment validation
        if self.min_synonyms_threshold < 1:
            errors.append(
                f"min_synonyms_threshold moet >= 1 zijn, got: {self.min_synonyms_threshold}"
            )

        if self.gpt4_timeout_seconds < 5:
            errors.append(
                f"gpt4_timeout_seconds moet >= 5 zijn (te kort voor API call), "
                f"got: {self.gpt4_timeout_seconds}"
            )

        if self.gpt4_timeout_seconds > 300:
            errors.append(
                f"gpt4_timeout_seconds moet <= 300 zijn (5 min max), "
                f"got: {self.gpt4_timeout_seconds}"
            )

        if self.gpt4_max_retries < 0:
            errors.append(
                f"gpt4_max_retries moet >= 0 zijn, got: {self.gpt4_max_retries}"
            )

        if self.gpt4_max_retries > 10:
            errors.append(
                f"gpt4_max_retries moet <= 10 zijn (excessive retries), "
                f"got: {self.gpt4_max_retries}"
            )

        # Cache validation
        if self.cache_ttl_seconds < 60:
            errors.append(
                f"cache_ttl_seconds moet >= 60 zijn (1 min minimum), "
                f"got: {self.cache_ttl_seconds}"
            )

        if self.cache_ttl_seconds > 86400:
            errors.append(
                f"cache_ttl_seconds moet <= 86400 zijn (24 hours max), "
                f"got: {self.cache_ttl_seconds}"
            )

        if self.cache_max_size < 10:
            errors.append(f"cache_max_size moet >= 10 zijn, got: {self.cache_max_size}")

        if self.cache_max_size > 100000:
            errors.append(
                f"cache_max_size moet <= 100000 zijn (memory concerns), "
                f"got: {self.cache_max_size}"
            )

        # Weight validation
        if not (0.0 <= self.min_weight_for_weblookup <= 1.0):
            errors.append(
                f"min_weight_for_weblookup moet tussen 0.0 en 1.0 zijn, "
                f"got: {self.min_weight_for_weblookup}"
            )

        if not (0.0 <= self.preferred_weight_threshold <= 1.0):
            errors.append(
                f"preferred_weight_threshold moet tussen 0.0 en 1.0 zijn, "
                f"got: {self.preferred_weight_threshold}"
            )

        # Dependency validation
        if self.preferred_weight_threshold < self.min_weight_for_weblookup:
            errors.append(
                f"preferred_weight_threshold ({self.preferred_weight_threshold}) "
                f"moet >= min_weight_for_weblookup ({self.min_weight_for_weblookup}) zijn"
            )

        return errors

    def to_dict(self) -> dict[str, Any]:
        """
        Converteer naar dictionary voor serialization.

        Returns:
            Dictionary representatie van configuratie
        """
        return {
            "policy": self.policy.value,
            "min_synonyms_threshold": self.min_synonyms_threshold,
            "gpt4_timeout_seconds": self.gpt4_timeout_seconds,
            "gpt4_max_retries": self.gpt4_max_retries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_max_size": self.cache_max_size,
            "min_weight_for_weblookup": self.min_weight_for_weblookup,
            "preferred_weight_threshold": self.preferred_weight_threshold,
        }


# ========================================
# SINGLETON PATTERN
# ========================================

_config: SynonymConfiguration | None = None


def get_synonym_config(config_path: str | None = None) -> SynonymConfiguration:
    """
    Haal gedeelde configuratie instance op (singleton pattern).

    Lazy initialization: eerste aanroep laadt config, volgende aanroepen
    retourneren gecachte instance (tenzij reload_config() wordt aangeroepen).

    Environment variable override:
        SYNONYM_CONFIG_PATH: Custom pad naar config file

    Args:
        config_path: Custom pad naar config file (default: config/synonym_config.yaml)

    Returns:
        Singleton SynonymConfiguration instance
    """
    global _config

    if _config is None:
        # Determine config path (priority: param > env var > default)
        if config_path is None:
            config_path = os.getenv("SYNONYM_CONFIG_PATH", "config/synonym_config.yaml")

        _config = SynonymConfiguration.from_yaml(config_path)
        logger.debug(f"Singleton configuration initialized from {config_path}")

    return _config


def reload_config(
    config_path: str = "config/synonym_config.yaml",
) -> SynonymConfiguration:
    """
    Reload configuration from YAML (for admin UI or testing).

    Clears singleton cache and forces reload from file.

    Args:
        config_path: Path naar YAML configuratie bestand

    Returns:
        Nieuw geladen SynonymConfiguration instance
    """
    global _config

    _config = SynonymConfiguration.from_yaml(config_path)
    logger.info(f"Configuration reloaded from {config_path}")

    return _config


# ========================================
# HELPER FUNCTIONS
# ========================================


def get_policy_statuses(policy: SynonymPolicy | None = None) -> list[str]:
    """
    Helper: haal statuses op basis van governance policy.

    Args:
        policy: Custom policy (default: gebruik global config)

    Returns:
        Lijst van toegestane statuses voor queries
    """
    if policy is None:
        config = get_synonym_config()
        policy = config.policy

    if policy == SynonymPolicy.STRICT:
        return ["active"]
    # PRAGMATIC
    return ["active", "ai_pending"]
