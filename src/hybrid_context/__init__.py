"""
Hybrid Context Module voor DefinitieAgent.

Combineert web lookup en document processing voor optimale context verrijking.
Voorziet in intelligente bron selectie en context fusie voor verbeterde definitie generatie.
"""

# Importeer hybrid context componenten voor intelligente context verrijking
from .hybrid_context_engine import HybridContextEngine, HybridContext  # Hoofdengine en context container
from .smart_source_selector import SmartSourceSelector  # Intelligente bron selectie
from .context_fusion import ContextFusion  # Context fusie en samenvoeging

# Exporteer publieke interface - alle hybrid context componenten
__all__ = [
    'HybridContextEngine',  # Hoofdengine voor hybride context verrijking
    'HybridContext',        # Container voor gecombineerde context data
    'SmartSourceSelector',  # Intelligente selectie van beste bronnen
    'ContextFusion'         # Fusie van verschillende context bronnen
]