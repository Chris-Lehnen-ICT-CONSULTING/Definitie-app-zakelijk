"""
Modular Toetser met JSON/Python validator support.

Deze versie van de modular toetser gebruikt individuele JSON/Python
validator paren in plaats van de BaseValidator architectuur.
"""

import logging
from typing import Any, Dict, List, Optional

from .json_validator_loader import json_validator_loader

logger = logging.getLogger(__name__)


class ModularToetser:
    """
    Modulaire toetser die werkt met individuele JSON/Python validators.

    Deze implementatie biedt volledige flexibiliteit voor het toevoegen
    en aanpassen van individuele toetsregels.
    """

    def __init__(self):
        """Initialiseer de JSON-based modular toetser."""
        self.loader = json_validator_loader
        self._available_rules = None

    def validate_definition(
        self,
        definitie: str,
        toetsregels: Dict[str, Dict[str, Any]],
        begrip: str = "",
        marker: Optional[str] = None,
        voorkeursterm: Optional[str] = None,
        bronnen_gebruikt: Optional[str] = None,
        contexten: Optional[Dict[str, List[str]]] = None,
        gebruik_logging: bool = False,
    ) -> List[str]:
        """
        Valideer definitie met JSON/Python validators.

        Args:
            definitie: Definitie tekst om te valideren
            toetsregels: Regel configuraties (gebruikt voor regel selectie)
            begrip: Original term being defined
            marker: Ontological category marker
            voorkeursterm: Preferred term
            bronnen_gebruikt: Sources used
            contexten: Context information
            gebruik_logging: Whether to use detailed logging

        Returns:
            List of validation result strings
        """
        if gebruik_logging:
            logger.info(f"Starting JSON validation voor term: {begrip}")

        # Bepaal welke regels te gebruiken
        if toetsregels:
            regel_ids = list(toetsregels.keys())
        else:
            regel_ids = self.get_available_rules()

        # Bouw context dictionary
        context = {
            "marker": marker,
            "voorkeursterm": voorkeursterm,
            "bronnen_gebruikt": bronnen_gebruikt,
            "contexten": contexten or {},
            "gebruik_logging": gebruik_logging,
        }

        # Voer validatie uit
        results = self.loader.validate_definitie(
            definitie=definitie, begrip=begrip, regel_ids=regel_ids, context=context
        )

        if gebruik_logging:
            logger.info(f"Validation complete: {len(results)} results")

        return results

    def get_available_rules(self) -> List[str]:
        """Haal lijst op van beschikbare validatie regels."""
        if self._available_rules is None:
            self._available_rules = self.loader.get_all_regel_ids()
            logger.info(f"Geladen {len(self._available_rules)} validatie regels")
        return self._available_rules

    def validate_single_rule(
        self, rule_id: str, definitie: str, regel_config: Dict[str, Any], **kwargs
    ) -> Optional[str]:
        """
        Valideer met een enkele regel.

        Args:
            rule_id: ID van de regel
            definitie: Definitie tekst
            regel_config: Regel configuratie (niet gebruikt, voor compatibility)
            **kwargs: Extra context parameters

        Returns:
            Validatie resultaat string of None
        """
        # Bouw context
        context = {
            "marker": kwargs.get("marker"),
            "voorkeursterm": kwargs.get("voorkeursterm"),
            "bronnen_gebruikt": kwargs.get("bronnen_gebruikt"),
            "contexten": kwargs.get("contexten", {}),
            "gebruik_logging": kwargs.get("gebruik_logging", False),
        }

        # Valideer met enkele regel
        results = self.loader.validate_definitie(
            definitie=definitie,
            begrip=kwargs.get("begrip", ""),
            regel_ids=[rule_id],
            context=context,
        )

        # Return eerste resultaat (skip summary)
        if len(results) > 1:
            return results[1]
        return None


# Globale instantie voor backward compatibility
modular_toetser = ModularToetser()


def toets_definitie(
    definitie: str,
    toetsregels: Dict[str, Dict[str, Any]],
    begrip: str = "",
    marker: Optional[str] = None,
    voorkeursterm: Optional[str] = None,
    bronnen_gebruikt: Optional[str] = None,
    contexten: Optional[Dict[str, List[str]]] = None,
    gebruik_logging: bool = False,
) -> List[str]:
    """
    Hoofdfunctie voor definitie validatie met JSON validators.

    Deze functie behoudt backward compatibility met de bestaande API.
    """
    return modular_toetser.validate_definition(
        definitie=definitie,
        toetsregels=toetsregels,
        begrip=begrip,
        marker=marker,
        voorkeursterm=voorkeursterm,
        bronnen_gebruikt=bronnen_gebruikt,
        contexten=contexten,
        gebruik_logging=gebruik_logging,
    )
