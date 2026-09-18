"""CategoryService voor het beheren van definitie categorieën."""

import logging

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.categorie_herkomst import HERKOMST_HANDMATIG
from models.category_models import CategoryChangeResult

logger = logging.getLogger(__name__)


class CategoryService:
    """Service voor het beheren van definitie categorieën."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize CategoryService met repository.

        Args:
            repository: De definitie repository voor database operaties
        """
        self.repository = repository

    def update_category(
        self,
        definition_id: int,
        new_category: str,
        update_session_data: bool = True,
        *,
        expected_version: int,
    ) -> tuple[bool, str | None]:
        """Legacy method - gebruik update_category_v2 voor nieuwe code."""
        # DEF-751 B2: geen verzonnen "web_user" meer; zonder identiteit blijft
        # de keuze ongeattribueerd. De versie van de getoonde kandidaat is
        # verplicht (reviewbevinding 3).
        result = self.update_category_v2(
            definition_id, new_category, None, expected_version=expected_version
        )
        return result.success, None if result.success else result.message

    def update_category_v2(
        self,
        definition_id: int,
        new_category: str,
        user: str | None,
        reason: str | None = None,
        *,
        expected_version: int,
    ) -> CategoryChangeResult:
        """Update de categorie van een definitie met volledige audit trail.

        DEF-751 B2: de toepassen-actie is een menselijke keuze en loopt via
        het expliciete commando `record_category_choice`; ``expected_version``
        is de recordversie van de getoonde kandidaat — een tussentijdse
        wijziging is een conflict (reviewbevinding 3).

        Args:
            definition_id: ID van de definitie
            new_category: Nieuwe categorie code
            user: Bestaande lokale identiteit of None (ongeattribueerd)
            reason: Optionele reden voor wijziging
            expected_version: Recordversie die de kiezer vóór zich had

        Returns:
            CategoryChangeResult met status en details
        """
        try:
            # Valideer categorie - ondersteun beide uppercase codes EN lowercase namen
            valid_categories_uppercase = [
                "ENT",
                "REL",
                "ACT",
                "ATT",
                "AUT",
                "STA",
                "OTH",
            ]
            valid_categories_lowercase = ["type", "proces", "resultaat", "exemplaar"]

            if (
                new_category not in valid_categories_uppercase
                and new_category not in valid_categories_lowercase
            ):
                return CategoryChangeResult(
                    success=False, message=f"Ongeldige categorie: {new_category}"
                )

            # Haal definitie op
            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return CategoryChangeResult(
                    success=False,
                    message=f"Definitie met ID {definition_id} niet gevonden",
                )

            # Valideer business rules
            is_valid, error_msg = self.validate_category_change(
                definition, new_category
            )
            if not is_valid:
                return CategoryChangeResult(
                    success=False, message=error_msg or ""  # DEF-439
                )

            # Bewaar oude categorie
            old_category = definition.categorie

            # Het expliciete commando (DEF-751 B2): `user` is de bestaande
            # lokale identiteit of None (dan ongeattribueerd) — nooit een
            # verzonnen "web_user"; de versieguard weigert een gewijzigd record.
            actor = user.strip() if isinstance(user, str) and user.strip() else None
            success = self.repository.record_category_choice(
                definition_id,
                {},
                waarde=new_category,
                herkomst=HERKOMST_HANDMATIG,
                actor=actor,
                actor_source="typed_name" if actor else None,
                updated_by=actor,
                expected_version=expected_version,
            )

            if success:
                logger.info(
                    f"Categorie bijgewerkt voor definitie {definition_id}: "
                    f"{old_category} -> {new_category} door {user}"
                )

                # Event publishing volgt bij introductie van Event Bus (US-060)

                return CategoryChangeResult(
                    success=True,
                    message=f"Categorie succesvol gewijzigd naar {self.get_category_display_name(new_category)}",
                    previous_category=old_category,
                    new_category=new_category,
                )

            return CategoryChangeResult(
                success=False,
                message=(
                    "Definitie is intussen gewijzigd (versieconflict); ververs en "
                    "kies opnieuw"
                ),
            )

        except Exception as e:
            error_msg = f"Fout bij bijwerken categorie: {e!s}"
            logger.error(error_msg, exc_info=True)
            return CategoryChangeResult(success=False, message=error_msg)

    def get_category_display_name(self, category_code: str) -> str:
        """Geef de display naam voor een categorie code.

        Args:
            category_code: De categorie code (bijv. 'ENT' of 'type')

        Returns:
            De display naam (bijv. 'Entiteit' of 'Type/Klasse')
        """
        # Ondersteun zowel uppercase codes als lowercase namen
        category_map = {
            # Uppercase codes (legacy)
            "ENT": "Entiteit",
            "REL": "Relatie",
            "ACT": "Activiteit",
            "ATT": "Attribuut",
            "AUT": "Autorisatie",
            "STA": "Status",
            "OTH": "Overig",
            # Lowercase namen (nieuw)
            "type": "Type/Klasse",
            "proces": "Proces/Activiteit",
            "resultaat": "Resultaat/Uitkomst",
            "exemplaar": "Exemplaar/Instantie",
        }
        return category_map.get(category_code, category_code)

    def validate_category_change(
        self, definition: DefinitieRecord, new_category: str
    ) -> tuple[bool, str | None]:
        """Valideer of een categorie wijziging toegestaan is.

        Dit kan business rules bevatten zoals:
        - Sommige categorieën mogen niet gewijzigd worden na goedkeuring
        - Bepaalde rollen mogen bepaalde categorieën niet wijzigen

        Args:
            definition: De definitie record
            new_category: De nieuwe categorie

        Returns:
            Tuple van (is_valid: bool, error_message: Optional[str])
        """
        # Business rule: Vastgestelde definities mogen niet van categorie wijzigen
        if definition.status == "established":
            return False, "Goedgekeurde definities kunnen niet van categorie wijzigen"

        # Toekomstige business rules kunnen hier toegevoegd worden
        # Bijvoorbeeld: role-based permissions, workflow status checks, etc.

        return True, None
