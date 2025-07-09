"""
Voorbeelden package for DefinitieAgent.
Provides unified example generation system consolidating all previous implementations.
"""

# Import from unified system
from .unified_voorbeelden import (
    # Main classes
    UnifiedExamplesGenerator,
    ExampleRequest,
    ExampleResponse,
    ExampleType,
    GenerationMode,
    
    # Convenience functions
    genereer_voorbeeld_zinnen,
    genereer_praktijkvoorbeelden,
    genereer_tegenvoorbeelden,
    genereer_synoniemen,
    genereer_antoniemen,
    genereer_toelichting,
    
    # Batch functions
    genereer_alle_voorbeelden,
    genereer_alle_voorbeelden_async,
    
    # Utility functions
    get_examples_generator
)

# Backward compatibility - import from legacy files if needed
try:
    from .voorbeelden import (
        genereer_voorbeeld_zinnen as legacy_genereer_voorbeeld_zinnen,
        genereer_praktijkvoorbeelden as legacy_genereer_praktijkvoorbeelden,
        genereer_tegenvoorbeelden as legacy_genereer_tegenvoorbeelden,
        genereer_synoniemen as legacy_genereer_synoniemen,
        genereer_antoniemen as legacy_genereer_antoniemen,
        genereer_toelichting as legacy_genereer_toelichting
    )
except ImportError:
    # Legacy files not available
    pass

__all__ = [
    # Main classes
    "UnifiedExamplesGenerator",
    "ExampleRequest",
    "ExampleResponse",
    "ExampleType",
    "GenerationMode",
    
    # Convenience functions
    "genereer_voorbeeld_zinnen",
    "genereer_praktijkvoorbeelden",
    "genereer_tegenvoorbeelden",
    "genereer_synoniemen",
    "genereer_antoniemen",
    "genereer_toelichting",
    
    # Batch functions
    "genereer_alle_voorbeelden",
    "genereer_alle_voorbeelden_async",
    
    # Utility functions
    "get_examples_generator"
]

# Version info
__version__ = "2.0.0"
__author__ = "DefinitieAgent Development Team"
__description__ = "Unified examples generation system with sync, async, cached, and resilient modes"
