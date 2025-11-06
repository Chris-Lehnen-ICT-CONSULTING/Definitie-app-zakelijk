"""
Classification Services Package.

DEF-35: Term-Based Classifier met externe configuratie.
"""

from services.classification.term_config import (
    TermPatternConfig,
    load_term_config,
    reset_config_cache,
)

__all__ = [
    "TermPatternConfig",
    "load_term_config",
    "reset_config_cache",
]
