"""CategoryService voor het beheren van definitie categorieën."""

import logging

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from models.category_models import (
    CategoryChangeResult,
)

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
        self, definition_id: int, new_category: str, update_session_data: bool = True
    ) -> tuple[bool, str | None]:
        """Legacy method - gebruik update_category_v2 voor nieuwe code."""
        result = self.update_category_v2(definition_id, new_category, "web_user")
        return result.success, None if result.success else result.message

    def update_category_v2(
        self,
        definition_id: int,
        new_category: str,
        user: str,
        reason: str | None = None,
    ) -> CategoryChangeResult:
        """Update de categorie van een definitie met volledige audit trail.

        Args:
            definition_id: ID van de definitie
            new_category: Nieuwe categorie code
            user: Gebruiker die wijziging doet
            reason: Optionele reden voor wijziging

        Returns:
            CategoryChangeResult met status en details
        """
        try:
            # Valideer categorie
            valid_categories = ["ENT", "REL", "ACT", "ATT", "AUT", "STA", "OTH"]
            if new_category not in valid_categories:
                return CategoryChangeResult(
                    success=False, message=f"Ongeldige categorie: {new_category}"
                )

            # Haal definitie op
            definition = self.repository.get_definitie_by_id(definition_id)
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
                return CategoryChangeResult(success=False, message=error_msg)

            # Bewaar oude categorie
            old_category = definition.categorie

            # Update categorie
            definition.categorie = new_category

            # Sla op in database
            success = self.repository.update_definitie(definition)

            if success:
                logger.info(
                    f"Categorie bijgewerkt voor definitie {definition_id}: "
                    f"{old_category} -> {new_category} door {user}"
                )

                # TODO: Publish event hier wanneer event bus beschikbaar is

                return CategoryChangeResult(
                    success=True,
                    message=f"Categorie succesvol gewijzigd naar {self.get_category_display_name(new_category)}",
                    previous_category=old_category,
                    new_category=new_category,
                )

            return CategoryChangeResult(
                success=False, message="Database update mislukt"
            )

        except Exception as e:
            error_msg = f"Fout bij bijwerken categorie: {e!s}"
            logger.error(error_msg, exc_info=True)
            return CategoryChangeResult(success=False, message=error_msg)

    def get_category_display_name(self, category_code: str) -> str:
        """Geef de display naam voor een categorie code.

        Args:
            category_code: De categorie code (bijv. 'ENT')

        Returns:
            De display naam (bijv. 'Entiteit')
        """
        category_map = {
            "ENT": "Entiteit",
            "REL": "Relatie",
            "ACT": "Activiteit",
            "ATT": "Attribuut",
            "AUT": "Autorisatie",
            "STA": "Status",
            "OTH": "Overig",
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
        # Business rule: Goedgekeurde definities mogen niet van categorie wijzigen
        if definition.status == "APPROVED":
            return False, "Goedgekeurde definities kunnen niet van categorie wijzigen"

        # Toekomstige business rules kunnen hier toegevoegd worden
        # Bijvoorbeeld: role-based permissions, workflow status checks, etc.

        return True, None
