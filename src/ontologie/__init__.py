"""
Ontologie Module - Verbeterde ontologische classificatie.

Implementeert context-aware pattern matching voor accurate begripsclassificatie
met 3-context support (organisatorisch, juridisch, wettelijk).
"""

from .improved_classifier import \
    QuickOntologischeAnalyzer  # Backward compatibility
from .improved_classifier import ImprovedOntologyClassifier

__all__ = ["ImprovedOntologyClassifier", "QuickOntologischeAnalyzer"]
