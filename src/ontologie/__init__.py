"""
Ontologie Module - Verbeterde ontologische classificatie.

Implementeert context-aware pattern matching voor accurate begripsclassificatie
met 3-context support (organisatorisch, juridisch, wettelijk).
"""

from .improved_classifier import (
    ImprovedOntologyClassifier,
    QuickOntologischeAnalyzer,  # Backward compatibility
)

__all__ = ["ImprovedOntologyClassifier", "QuickOntologischeAnalyzer"]
