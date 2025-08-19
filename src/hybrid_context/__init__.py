"""
Hybrid Context Module voor DefinitieAgent.

Combineert web lookup en document processing voor optimale context verrijking.
Voorziet in intelligente bron selectie en context fusie voor verbeterde definitie generatie.
"""

from .context_fusion import ContextFusion  # Context fusie en samenvoeging

# Importeer hybrid context componenten voor intelligente context verrijking
from .hybrid_context_engine import (  # Hoofdengine en context container
    HybridContext,
    HybridContextEngine,
)
from .smart_source_selector import SmartSourceSelector  # Intelligente bron selectie

# Exporteer publieke interface - alle hybrid context componenten
__all__ = [
    "ContextFusion",  # Fusie van verschillende context bronnen
    "HybridContext",  # Container voor gecombineerde context data
    "HybridContextEngine",  # Hoofdengine voor hybride context verrijking
    "SmartSourceSelector",  # Intelligente selectie van beste bronnen
]
