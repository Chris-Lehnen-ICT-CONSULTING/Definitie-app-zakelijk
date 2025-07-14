"""
Voorbeelden package voor DefinitieAgent.

Biedt een geünificeerd voorbeeld generatie systeem dat alle vorige implementaties consolideert.
Genereert praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen en toelichtingen.
"""

# Importeer van geünificeerd voorbeelden systeem
from .unified_voorbeelden import (
    # Hoofdklassen voor voorbeeld generatie
    UnifiedExamplesGenerator,     # Geünificeerde generator voor alle voorbeelden
    ExampleRequest,               # Request container voor voorbeeld generatie
    ExampleResponse,              # Response container met gegenereerde voorbeelden
    ExampleType,                  # Type van voorbeeld (praktijk, tegen, synoniem, etc.)
    GenerationMode,               # Generatie modus (sync, async, cached, resilient)
    
    # Convenience functies voor directe voorbeeld generatie
    genereer_voorbeeld_zinnen,    # Genereert voorbeeld zinnen met de term
    genereer_praktijkvoorbeelden, # Genereert praktische gebruiksvoorbeelden
    genereer_tegenvoorbeelden,    # Genereert tegenvoorbeelden ter verduidelijking
    genereer_synoniemen,          # Genereert synoniemen van de term
    genereer_antoniemen,          # Genereert antoniemen van de term
    genereer_toelichting,         # Genereert uitgebreide toelichting
    
    # Batch functies voor efficiënte bulk generatie
    genereer_alle_voorbeelden,      # Synchrone batch generatie van alle voorbeelden
    genereer_alle_voorbeelden_async, # Asynchrone batch generatie voor performance
    
    # Utility functies voor generator management
    get_examples_generator        # Factory functie voor generator instanties
)

# Achterwaartse compatibiliteit - importeer van legacy bestanden indien nodig
# Zorgt voor soepele migratie van oude code naar nieuwe geünificeerde systeem
try:
    from .voorbeelden import (
        genereer_voorbeeld_zinnen as legacy_genereer_voorbeeld_zinnen,    # Legacy voorbeeld zinnen functie
        genereer_praktijkvoorbeelden as legacy_genereer_praktijkvoorbeelden, # Legacy praktijkvoorbeelden functie
        genereer_tegenvoorbeelden as legacy_genereer_tegenvoorbeelden,    # Legacy tegenvoorbeelden functie
        genereer_synoniemen as legacy_genereer_synoniemen,                # Legacy synoniemen functie
        genereer_antoniemen as legacy_genereer_antoniemen,                # Legacy antoniemen functie
        genereer_toelichting as legacy_genereer_toelichting               # Legacy toelichting functie
    )
except ImportError:
    # Legacy bestanden niet beschikbaar - continue met nieuwe implementatie
    pass

# Exporteer publieke interface - alle voorbeeld generatie componenten
__all__ = [
    # Hoofdklassen voor voorbeeld generatie management
    "UnifiedExamplesGenerator",     # Geünificeerde generator hoofdklasse
    "ExampleRequest",               # Request container voor voorbeeld aanvragen
    "ExampleResponse",              # Response container voor gegenereerde voorbeelden
    "ExampleType",                  # Enumeratie van voorbeeld types
    "GenerationMode",               # Enumeratie van generatie modi
    
    # Convenience functies voor directe voorbeeld generatie
    "genereer_voorbeeld_zinnen",    # Directe functie voor voorbeeld zinnen
    "genereer_praktijkvoorbeelden", # Directe functie voor praktijkvoorbeelden
    "genereer_tegenvoorbeelden",    # Directe functie voor tegenvoorbeelden
    "genereer_synoniemen",          # Directe functie voor synoniemen
    "genereer_antoniemen",          # Directe functie voor antoniemen
    "genereer_toelichting",         # Directe functie voor toelichtingen
    
    # Batch functies voor efficiënte bulk operaties
    "genereer_alle_voorbeelden",      # Synchrone batch generatie
    "genereer_alle_voorbeelden_async", # Asynchrone batch generatie
    
    # Utility functies voor generator management
    "get_examples_generator"        # Factory functie voor generator instanties
]

# Versie informatie en package metadata
__version__ = "2.0.0"  # Huidige versie van voorbeelden package
__author__ = "DefinitieAgent Development Team"  # Ontwikkelingsteam
__description__ = "Geünificeerd voorbeeld generatie systeem met sync, async, cached, en resilient modi"  # Package beschrijving
