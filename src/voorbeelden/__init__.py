"""
Voorbeelden package voor DefinitieAgent.

Biedt een geünificeerd voorbeeld generatie systeem dat alle vorige implementaties consolideert.
Genereert praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen en toelichtingen.
"""

# Importeer van geünificeerd voorbeelden systeem
from .unified_voorbeelden import \
    ExampleRequest  # Request container voor voorbeeld generatie
from .unified_voorbeelden import \
    ExampleResponse  # Response container met gegenereerde voorbeelden
from .unified_voorbeelden import \
    ExampleType  # Type van voorbeeld (praktijk, tegen, synoniem, etc.)
from .unified_voorbeelden import \
    GenerationMode  # Generatie modus (sync, async, cached, resilient)
from .unified_voorbeelden import \
    UnifiedExamplesGenerator  # Geünificeerde generator voor alle voorbeelden
from .unified_voorbeelden import \
    genereer_alle_voorbeelden  # Synchrone batch generatie van alle voorbeelden
from .unified_voorbeelden import \
    genereer_alle_voorbeelden_async  # Asynchrone batch generatie voor performance
from .unified_voorbeelden import \
    genereer_antoniemen  # Genereert antoniemen van de term
from .unified_voorbeelden import \
    genereer_praktijkvoorbeelden  # Genereert praktische gebruiksvoorbeelden
from .unified_voorbeelden import \
    genereer_synoniemen  # Genereert synoniemen van de term
from .unified_voorbeelden import \
    genereer_tegenvoorbeelden  # Genereert tegenvoorbeelden ter verduidelijking
from .unified_voorbeelden import \
    genereer_toelichting  # Genereert uitgebreide toelichting
from .unified_voorbeelden import \
    genereer_voorbeeld_zinnen  # Genereert voorbeeld zinnen met de term
from .unified_voorbeelden import \
    get_examples_generator  # Hoofdklassen voor voorbeeld generatie; Convenience functies voor directe voorbeeld generatie; Batch functies voor efficiënte bulk generatie; Utility functies voor generator management; Factory functie voor generator instanties

# Achterwaartse compatibiliteit - check voor legacy bestanden zonder import side-effects
# Gebruik find_spec om te voorkomen dat er een OpenAI client wordt geinstantieerd tijdens test collection
try:
    import importlib.util as _importlib_util

    LEGACY_AVAILABLE = _importlib_util.find_spec("voorbeelden.voorbeelden") is not None
except Exception:
    LEGACY_AVAILABLE = False

# Exporteer publieke interface - alle voorbeeld generatie componenten
__all__ = [
    "ExampleRequest",  # Request container voor voorbeeld aanvragen
    "ExampleResponse",  # Response container voor gegenereerde voorbeelden
    "ExampleType",  # Enumeratie van voorbeeld types
    "GenerationMode",  # Enumeratie van generatie modi
    # Hoofdklassen voor voorbeeld generatie management
    "UnifiedExamplesGenerator",  # Geünificeerde generator hoofdklasse
    # Batch functies voor efficiënte bulk operaties
    "genereer_alle_voorbeelden",  # Synchrone batch generatie
    "genereer_alle_voorbeelden_async",  # Asynchrone batch generatie
    "genereer_antoniemen",  # Directe functie voor antoniemen
    "genereer_praktijkvoorbeelden",  # Directe functie voor praktijkvoorbeelden
    "genereer_synoniemen",  # Directe functie voor synoniemen
    "genereer_tegenvoorbeelden",  # Directe functie voor tegenvoorbeelden
    "genereer_toelichting",  # Directe functie voor toelichtingen
    # Convenience functies voor directe voorbeeld generatie
    "genereer_voorbeeld_zinnen",  # Directe functie voor voorbeeld zinnen
    # Utility functies voor generator management
    "get_examples_generator",  # Factory functie voor generator instanties
]

# Versie informatie en package metadata
__version__ = "2.0.0"  # Huidige versie van voorbeelden package
__author__ = "DefinitieAgent Development Team"  # Ontwikkelingsteam
__description__ = "Geünificeerd voorbeeld generatie systeem met sync, async, cached, en resilient modi"  # Package beschrijving
