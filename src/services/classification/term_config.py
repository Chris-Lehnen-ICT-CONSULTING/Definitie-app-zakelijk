"""
Term Pattern Configuration Loader voor Term-Based Classifier.

DEF-35: Externalisatie van hardcoded patterns naar YAML configuratie.

GEBRUIK:
    config = load_term_config()  # Laadt default config
    config = load_term_config("custom/path.yaml")  # Custom path

FEATURES:
- Type-safe dataclass voor config structuur
- YAML loading met error handling
- Validatie van config structuur
- Caching voor performance
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class TermPatternConfig:
    """
    Configuratie voor term-based ontologische classificatie.

    Attributen:
        domain_overrides: Dict van term → categorie voor expliciete classificaties
        suffix_weights: Dict van categorie → {suffix: weight} voor pattern matching
        category_priority: Lijst van categorieën in prioriteitsvolgorde (tie-breaking)
        confidence_thresholds: Dict van label → threshold voor confidence scoring
    """

    domain_overrides: dict[str, str]
    suffix_weights: dict[str, dict[str, float]]
    category_priority: list[str]
    confidence_thresholds: dict[str, float]

    def __post_init__(self):
        """Valideer config na initialisatie."""
        self._validate()

    def _validate(self):
        """
        Valideer config structuur.

        Raises:
            ValueError: Als config invalid is
        """
        # Valideer category_priority bevat alle categorieën
        required_categories = {"TYPE", "PROCES", "RESULTAAT", "EXEMPLAAR"}
        priority_set = set(self.category_priority)

        if not priority_set.issubset(required_categories):
            extra = priority_set - required_categories
            raise ValueError(
                f"Invalid categories in category_priority: {extra}. "
                f"Must be subset of {required_categories}"
            )

        # Valideer confidence thresholds
        required_thresholds = {"high", "medium", "low"}
        if set(self.confidence_thresholds.keys()) != required_thresholds:
            raise ValueError(
                f"confidence_thresholds must contain exactly: {required_thresholds}"
            )

        # Valideer threshold waarden (0.0 <= x <= 1.0)
        for label, value in self.confidence_thresholds.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Threshold {label}={value} must be between 0.0 and 1.0"
                )

        # Valideer threshold volgorde (high > medium > low)
        if not (
            self.confidence_thresholds["high"]
            >= self.confidence_thresholds["medium"]
            >= self.confidence_thresholds["low"]
        ):
            raise ValueError(
                "Thresholds must be ordered: high >= medium >= low. "
                f"Got: high={self.confidence_thresholds['high']}, "
                f"medium={self.confidence_thresholds['medium']}, "
                f"low={self.confidence_thresholds['low']}"
            )

        # Valideer suffix_weights structure
        for category, weights in self.suffix_weights.items():
            if category not in required_categories:
                logger.warning(
                    f"Unknown category in suffix_weights: {category}. "
                    f"Expected one of: {required_categories}"
                )
            # Skip None or empty weights (e.g., EXEMPLAAR has no suffix patterns)
            if weights is None or not weights:
                continue
            for suffix, weight in weights.items():
                if not 0.0 <= weight <= 1.0:
                    raise ValueError(
                        f"Suffix weight {category}.{suffix}={weight} "
                        f"must be between 0.0 and 1.0"
                    )

        # Valideer domain_overrides values
        for term, category in self.domain_overrides.items():
            if category not in required_categories:
                raise ValueError(
                    f"Invalid category for domain override '{term}': {category}. "
                    f"Must be one of: {required_categories}"
                )

        logger.debug("TermPatternConfig validation passed")


# Singleton cache voor config
_config_cache: dict[str, TermPatternConfig] = {}


def load_term_config(
    config_path: str = "config/classification/term_patterns.yaml",
) -> TermPatternConfig:
    """
    Laad term pattern configuratie uit YAML bestand.

    CACHING:
    - Config wordt gecached per path
    - Herhaalde calls met zelfde path returnen cached instance
    - Cache wordt gereset als bestand niet bestaat (voor testing)

    Args:
        config_path: Pad naar YAML configuratie bestand (relatief of absoluut)

    Returns:
        TermPatternConfig instance met gevalideerde configuratie

    Raises:
        FileNotFoundError: Als config bestand niet bestaat
        yaml.YAMLError: Als YAML parsing faalt
        ValueError: Als config structuur invalid is
        KeyError: Als vereiste keys ontbreken in config

    Example:
        >>> config = load_term_config()
        >>> config.domain_overrides["machtiging"]
        'TYPE'
        >>> config.confidence_thresholds["high"]
        0.70
    """
    # Check cache
    if config_path in _config_cache:
        logger.debug(f"Using cached config for: {config_path}")
        return _config_cache[config_path]

    # Resolve path
    path = Path(config_path)
    if not path.is_absolute():
        # Resolve relatief t.o.v. project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        path = project_root / config_path

    # Check existence
    if not path.exists():
        raise FileNotFoundError(
            f"Term pattern config not found: {config_path}\n"
            f"Resolved to: {path}\n"
            f"Expected location: config/classification/term_patterns.yaml"
        )

    # Load YAML
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        logger.error(f"Failed to parse YAML config: {config_path}")
        raise

    # Validate required keys
    required_keys = {
        "domain_overrides",
        "suffix_weights",
        "category_priority",
        "confidence_thresholds",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        raise KeyError(
            f"Missing required keys in config: {missing_keys}\n"
            f"Config file: {config_path}\n"
            f"Required keys: {required_keys}"
        )

    # Create config object (validation happens in __post_init__)
    try:
        config = TermPatternConfig(**data)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to create TermPatternConfig from {config_path}: {e}")
        raise

    # Cache result
    _config_cache[config_path] = config
    logger.info(
        f"✅ TermPatternConfig loaded successfully: {config_path} "
        f"({len(config.domain_overrides)} overrides, "
        f"{len(config.suffix_weights)} categories)"
    )

    return config


def reset_config_cache():
    """
    Reset de config cache (voor testing).

    Gebruik dit om geforceerde reload van configuratie te triggeren.
    """
    global _config_cache
    _config_cache.clear()
    logger.debug("TermPatternConfig cache cleared")


def get_cached_config_count() -> int:
    """
    Get aantal gecachte configs (voor debugging).

    Returns:
        Aantal configs in cache
    """
    return len(_config_cache)
