"""
CleaningService voor het opschonen van AI-gegenereerde definities.

Deze service implementeert de moderne architectuur patterns en biedt
een clean interface voor definitie opschoning met metadata tracking.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility

from opschoning.opschoning_enhanced import opschonen_enhanced
from services.interfaces import (CleaningResult, CleaningServiceInterface,
                                 Definition)

logger = logging.getLogger(__name__)


@dataclass
class CleaningConfig:
    """Configuratie voor de CleaningService."""

    enable_cleaning: bool = True
    track_changes: bool = True
    preserve_original: bool = True
    log_operations: bool = True


# CleaningResult en CleaningServiceInterface zijn nu gedefinieerd in interfaces.py


class CleaningService(CleaningServiceInterface):
    """
    Moderne implementatie van definitie opschoning service.

    Integreert de bestaande opschoning.py functionaliteit in een
    clean service architectuur met proper logging en metadata.
    """

    def __init__(self, config: CleaningConfig):
        """
        Initialiseer de CleaningService.

        Args:
            config: CleaningConfig met service instellingen
        """
        self.config = config
        logger.info("CleaningService geïnitialiseerd")

    def clean_definition(self, definition: Definition) -> CleaningResult:
        """
        Schoon een definitie object op en update metadata.

        Args:
            definition: Definition object om op te schonen

        Returns:
            CleaningResult met opschoning details
        """
        # Gebruik clean_text voor de daadwerkelijke opschoning
        result = self.clean_text(definition.definitie, definition.begrip)

        # Update de Definition object metadata als preserve_original enabled is
        if self.config.preserve_original and result.was_cleaned:
            if definition.metadata is None:
                definition.metadata = {}

            definition.metadata.update(
                {
                    "cleaning_applied": True,
                    "original_definitie": result.original_text,
                    "cleaning_timestamp": result.metadata.get("timestamp"),
                    "cleaning_rules_applied": result.applied_rules,
                }
            )

        # Update de definitie tekst met opgeschoond resultaat
        definition.definitie = result.cleaned_text

        if self.config.log_operations and result.was_cleaned:
            logger.info(
                f"Definitie opgeschoond voor '{definition.begrip}': {len(result.applied_rules)} regels toegepast"
            )

        return result

    def clean_text(self, text: str, term: str) -> CleaningResult:
        """
        Schoon definitie tekst op met gedetailleerde tracking.

        Args:
            text: Te schonen definitie tekst
            term: Het begrip dat gedefinieerd wordt

        Returns:
            CleaningResult met complete opschoning informatie
        """

        original_text = text.strip()

        try:
            # Initialiseer tracking lijsten
            applied_rules = []
            improvements = []

            # Check of we GPT format moeten hanteren
            handle_gpt = "ontologische categorie:" in original_text.lower()

            if handle_gpt:
                # Import analyze_gpt_response voor metadata extractie
                from opschoning.opschoning_enhanced import analyze_gpt_response

                # Extract metadata eerst
                gpt_metadata = analyze_gpt_response(original_text)

                # Pas opschoning toe
                cleaned_text = opschonen_enhanced(
                    original_text, term, handle_gpt_format=True
                )

                # Voeg GPT metadata toe aan applied_rules als het relevant is
                if gpt_metadata.get("ontologische_categorie"):
                    applied_rules.append(
                        f"extracted_ontology_{gpt_metadata['ontologische_categorie']}"
                    )
            else:
                # Gebruik ook enhanced voor consistentie, maar zonder GPT format handling
                cleaned_text = opschonen_enhanced(
                    original_text, term, handle_gpt_format=False
                )

            # Analyseer welke wijzigingen zijn toegepast
            if original_text != cleaned_text:
                applied_rules.extend(
                    self._analyze_changes(original_text, cleaned_text, term)
                )
                improvements.extend(
                    self._generate_improvements(original_text, cleaned_text)
                )

            result = CleaningResult(
                original_text=original_text,
                cleaned_text=cleaned_text,
                was_cleaned=original_text != cleaned_text,
                applied_rules=applied_rules,
                improvements=improvements,
                metadata={
                    "timestamp": datetime.now(UTC).isoformat(),
                    "term": term,
                    "service_version": "1.0",
                },
            )

            if self.config.log_operations and result.was_cleaned:
                logger.debug(
                    f"Tekst opgeschoond: '{original_text[:50]}...' -> '{cleaned_text[:50]}...'"
                )

            return result

        except Exception as e:
            logger.error(f"Fout bij opschoning van tekst: {e}")
            # Return origineel bij fout
            return CleaningResult(
                original_text=original_text,
                cleaned_text=original_text,
                was_cleaned=False,
                applied_rules=["error_occurred"],
                metadata={"error": str(e)},
            )

    def validate_cleaning_rules(self) -> bool:
        """
        Valideer of de opschoning configuratie correct is.

        Returns:
            True als configuratie correct is
        """
        try:
            # Test de opschoning configuratie door een simpele test
            from config.verboden_woorden import laad_verboden_woorden

            config = laad_verboden_woorden()

            # Basis validatie
            if not config:
                logger.warning("Geen opschoning configuratie gevonden")
                return False

            if isinstance(config, dict):
                verboden_lijst = config.get("verboden_woorden", [])
            elif isinstance(config, list):
                verboden_lijst = config
            else:
                verboden_lijst = []
            if not verboden_lijst:
                logger.warning("Geen verboden woorden gevonden in configuratie")
                return False

            logger.info(
                f"Opschoning regels gevalideerd: {len(verboden_lijst)} verboden woorden gevonden"
            )
            return True

        except Exception as e:
            logger.error(f"Fout bij validatie van opschoning regels: {e}")
            return False

    def _analyze_changes(self, original: str, cleaned: str, term: str) -> list[str]:
        """
        Analyseer welke specifieke wijzigingen zijn toegepast.

        Args:
            original: Originele tekst
            cleaned: Opgeschoonde tekst
            term: Het begrip

        Returns:
            Lijst van toegepaste regels
        """
        rules = []

        # Basis analyse van wijzigingen
        if original.lower().startswith(term.lower()):
            rules.append("removed_circular_definition")

        if original.lower().startswith(("is ", "omvat ", "betekent ")):
            rules.append("removed_forbidden_prefix")

        if original.lower().startswith(("de ", "het ", "een ")):
            rules.append("removed_article")

        # Hoofdletter correctie
        if original and cleaned and original[0].islower() and cleaned[0].isupper():
            rules.append("capitalized_first_letter")

        # Punt correctie
        if not original.endswith(".") and cleaned.endswith("."):
            rules.append("added_period")

        return rules

    def _generate_improvements(self, original: str, cleaned: str) -> list[str]:
        """
        Genereer lijst van verbeteringen die zijn toegepast.

        Args:
            original: Originele tekst
            cleaned: Opgeschoonde tekst

        Returns:
            Lijst van verbeteringen
        """
        improvements = []

        if len(cleaned) < len(original):
            improvements.append("Verwijderd onnodige voorvoegsels")

        if original and cleaned and original[0] != cleaned[0]:
            improvements.append("Hoofdletter toegevoegd")

        if not original.endswith(".") and cleaned.endswith("."):
            improvements.append("Eindpunt toegevoegd")

        return improvements
