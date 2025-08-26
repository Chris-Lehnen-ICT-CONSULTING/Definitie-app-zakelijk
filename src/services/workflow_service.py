"""
Workflow Service - Business logic voor definitie status workflow.

Deze service bevat alle business logic voor status transities,
zonder enige database dependencies.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowAction(Enum):
    """Mogelijke UI acties na een workflow stap."""

    SHOW_REGENERATION_PREVIEW = "show_regeneration_preview"
    NAVIGATE_TO_GENERATOR = "navigate_to_generator"
    SHOW_SUCCESS = "show_success"
    SHOW_ERROR = "show_error"
    NO_ACTION = "no_action"


@dataclass
class CategoryChangeResult:
    """Resultaat van category change workflow."""

    success: bool
    message: str
    action: WorkflowAction
    old_category: str
    new_category: str
    requires_regeneration: bool = True
    preview_data: dict[str, Any] | None = None
    error: str | None = None


class DefinitionStatus(Enum):
    """Status van een definitie in het systeem."""

    DRAFT = "draft"
    REVIEW = "review"
    ESTABLISHED = "established"
    ARCHIVED = "archived"


@dataclass
class StatusChange:
    """Representatie van een status wijziging."""

    from_status: str
    to_status: str
    changed_by: str
    changed_at: datetime
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class WorkflowService:
    """
    Business logic voor definitie status workflow.

    Deze service beheert de regels voor status transities en
    bepaalt welke wijzigingen toegestaan zijn.
    """

    # Toegestane status transities
    ALLOWED_TRANSITIONS = {
        DefinitionStatus.DRAFT.value: [
            DefinitionStatus.REVIEW.value,
            DefinitionStatus.ARCHIVED.value,
        ],
        DefinitionStatus.REVIEW.value: [
            DefinitionStatus.ESTABLISHED.value,
            DefinitionStatus.DRAFT.value,
            DefinitionStatus.ARCHIVED.value,
        ],
        DefinitionStatus.ESTABLISHED.value: [DefinitionStatus.ARCHIVED.value],
        DefinitionStatus.ARCHIVED.value: [
            DefinitionStatus.DRAFT.value  # Restore mogelijk
        ],
    }

    # Rollen die bepaalde transities mogen uitvoeren
    ROLE_PERMISSIONS = {
        "approve_to_established": ["reviewer", "admin"],
        "archive": ["admin"],
        "restore_from_archive": ["admin"],
    }

    def __init__(self):
        """Initialiseer de workflow service."""
        logger.info("WorkflowService initialized")

    def can_change_status(
        self, current_status: str, new_status: str, user_role: str | None = None
    ) -> bool:
        """
        Business rule: check of status transition toegestaan is.

        Args:
            current_status: Huidige status
            new_status: Gewenste nieuwe status
            user_role: Rol van de gebruiker (optioneel)

        Returns:
            True als de transitie toegestaan is
        """
        # Check basic transition rules
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            return False

        # Check role-based permissions
        if new_status == DefinitionStatus.ESTABLISHED.value:
            if user_role not in self.ROLE_PERMISSIONS.get("approve_to_established", []):
                logger.warning(
                    f"User with role '{user_role}' cannot approve to established"
                )
                return False

        if new_status == DefinitionStatus.ARCHIVED.value:
            if user_role and user_role not in self.ROLE_PERMISSIONS.get("archive", []):
                logger.warning(f"User with role '{user_role}' cannot archive")
                return False

        if (
            (
                current_status == DefinitionStatus.ARCHIVED.value
                and new_status == DefinitionStatus.DRAFT.value
            )
            and user_role
            and user_role not in self.ROLE_PERMISSIONS.get("restore_from_archive", [])
        ):
            logger.warning(f"User with role '{user_role}' cannot restore from archive")
            return False

        return True

    def prepare_status_change(
        self,
        definition_id: int,
        current_status: str,
        new_status: str,
        user: str,
        user_role: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Bereid status change voor met business logic.

        Args:
            definition_id: ID van de definitie
            current_status: Huidige status
            new_status: Nieuwe status
            user: Gebruiker die de wijziging uitvoert
            user_role: Rol van de gebruiker
            notes: Optionele notities

        Returns:
            Dictionary met alle wijzigingen die doorgevoerd moeten worden

        Raises:
            ValueError: Als de transitie niet toegestaan is
        """
        if not self.can_change_status(current_status, new_status, user_role):
            msg = (
                f"Invalid transition: {current_status} → {new_status} "
                f"for user with role '{user_role}'"
            )
            raise ValueError(msg)

        # Basis wijzigingen
        changes = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": user,
        }

        # Business rule: established requires approval info
        if new_status == DefinitionStatus.ESTABLISHED.value:
            changes.update(
                {
                    "approved_by": user,
                    "approved_at": datetime.now(timezone.utc),
                    "approval_notes": notes or "Goedgekeurd",
                }
            )

        # Business rule: archived should track reason
        if new_status == DefinitionStatus.ARCHIVED.value:
            changes.update(
                {
                    "archived_by": user,
                    "archived_at": datetime.now(timezone.utc),
                    "archive_reason": notes or "Gearchiveerd",
                }
            )

        # Business rule: restore from archive clears archive info
        if (
            current_status == DefinitionStatus.ARCHIVED.value
            and new_status == DefinitionStatus.DRAFT.value
        ):
            changes.update(
                {
                    "archived_by": None,
                    "archived_at": None,
                    "archive_reason": None,
                    "restored_by": user,
                    "restored_at": datetime.now(timezone.utc),
                }
            )

        logger.info(
            f"Prepared status change for definition {definition_id}: "
            f"{current_status} → {new_status}"
        )

        return changes

    def get_allowed_transitions(
        self, current_status: str, user_role: str | None = None
    ) -> list[str]:
        """
        Get lijst van toegestane status transities voor huidige status.

        Args:
            current_status: Huidige status
            user_role: Rol van de gebruiker

        Returns:
            Lijst van statussen waar naartoe getransitioneerd kan worden
        """
        base_transitions = self.ALLOWED_TRANSITIONS.get(current_status, [])

        if not user_role:
            return base_transitions

        # Filter based on role permissions
        allowed = []
        for status in base_transitions:
            if self.can_change_status(current_status, status, user_role):
                allowed.append(status)

        return allowed

    def validate_status_change_history(self, history: list[StatusChange]) -> bool:
        """
        Valideer of een reeks status wijzigingen geldig is.

        Args:
            history: Lijst van status wijzigingen

        Returns:
            True als alle transities geldig zijn
        """
        if not history:
            return True

        # Start status should be DRAFT
        if history[0].from_status != DefinitionStatus.DRAFT.value:
            logger.error(f"Invalid initial status: {history[0].from_status}")
            return False

        # Validate each transition
        for i, change in enumerate(history):
            # Check transition is allowed
            allowed = self.ALLOWED_TRANSITIONS.get(change.from_status, [])
            if change.to_status not in allowed:
                logger.error(
                    f"Invalid transition at position {i}: "
                    f"{change.from_status} → {change.to_status}"
                )
                return False

            # Check continuity
            if i > 0 and history[i - 1].to_status != change.from_status:
                logger.error(
                    f"Discontinuity at position {i}: "
                    f"previous to_status={history[i-1].to_status}, "
                    f"current from_status={change.from_status}"
                )
                return False

        return True

    def get_status_info(self, status: str) -> dict[str, Any]:
        """
        Get informatie over een specifieke status.

        Args:
            status: Status om info voor op te halen

        Returns:
            Dictionary met status informatie
        """
        status_info = {
            DefinitionStatus.DRAFT.value: {
                "name": "Concept",
                "description": "Definitie is nog in bewerking",
                "color": "gray",
                "icon": "edit",
                "editable": True,
            },
            DefinitionStatus.REVIEW.value: {
                "name": "In Review",
                "description": "Definitie wordt beoordeeld door experts",
                "color": "orange",
                "icon": "eye",
                "editable": False,
            },
            DefinitionStatus.ESTABLISHED.value: {
                "name": "Vastgesteld",
                "description": "Definitie is goedgekeurd en vastgesteld",
                "color": "green",
                "icon": "check",
                "editable": False,
            },
            DefinitionStatus.ARCHIVED.value: {
                "name": "Gearchiveerd",
                "description": "Definitie is niet meer actief",
                "color": "red",
                "icon": "archive",
                "editable": False,
            },
        }

        return status_info.get(
            status,
            {
                "name": status,
                "description": "Onbekende status",
                "color": "gray",
                "icon": "question",
                "editable": False,
            },
        )

    def can_edit_definition(self, status: str, user_role: str | None = None) -> bool:
        """
        Bepaal of een definitie bewerkt mag worden in de huidige status.

        Args:
            status: Huidige status van de definitie
            user_role: Rol van de gebruiker

        Returns:
            True als bewerken toegestaan is
        """
        # Basic rule: only DRAFT can be edited
        if status != DefinitionStatus.DRAFT.value:
            # Admins might have override permissions
            return user_role == "admin"

        return True

    def get_workflow_summary(self) -> dict[str, Any]:
        """
        Get een overzicht van de workflow configuratie.

        Returns:
            Dictionary met workflow informatie
        """
        return {
            "statuses": [status.value for status in DefinitionStatus],
            "transitions": self.ALLOWED_TRANSITIONS,
            "role_permissions": self.ROLE_PERMISSIONS,
            "editable_statuses": [DefinitionStatus.DRAFT.value],
            "final_statuses": [
                DefinitionStatus.ESTABLISHED.value,
                DefinitionStatus.ARCHIVED.value,
            ],
        }

    def submit_for_review(
        self, definition_id: int, user: str = "web_user", notes: str | None = None
    ) -> dict[str, Any]:
        """
        Submit een definitie voor review (DRAFT → REVIEW).

        Dit is een convenience methode die specifiek voor het UI
        de submit-for-review workflow implementeert.

        Args:
            definition_id: ID van de definitie
            user: Gebruiker die submit uitvoert
            notes: Optionele notities

        Returns:
            Dictionary met status change informatie voor de repository layer

        Raises:
            ValueError: Als de huidige status geen DRAFT is

        Note:
            Deze service layer methode bereidt alleen de changes voor.
            De daadwerkelijke database update gebeurt in de repository layer
            volgens het principe van separation of concerns.
        """
        # Dit geeft de changes terug die doorgevoerd moeten worden
        # De repository layer is verantwoordelijk voor de database update
        return self.prepare_status_change(
            definition_id=definition_id,
            current_status=DefinitionStatus.DRAFT.value,
            new_status=DefinitionStatus.REVIEW.value,
            user=user,
            notes=notes or "Submitted for review via web interface",
        )

    # ===== Category Change Orchestration =====

    def execute_category_change_workflow(
        self,
        definition_id: int | None,
        old_category: str,
        new_category: str,
        current_definition: str,
        begrip: str,
        user: str = "web_user",
        reason: str = "Handmatige aanpassing via UI",
    ) -> CategoryChangeResult:
        """
        Orchestreer complete category change workflow volgens SA architectuur.

        Deze methode implementeert de business logic voor category changes
        en coördineert tussen verschillende services zonder zelf data access
        te doen (separation of concerns).

        Workflow stappen:
        1. Valideer category change
        2. Update category (delegeer naar CategoryService)
        3. Bepaal vervolgacties
        4. Prepareer UI response

        Args:
            definition_id: ID van opgeslagen definitie (None voor unsaved)
            old_category: Huidige categorie
            new_category: Nieuwe categorie
            current_definition: Huidige definitie tekst
            begrip: Het begrip
            user: Gebruiker die wijziging uitvoert
            reason: Reden voor wijziging

        Returns:
            CategoryChangeResult met instructies voor UI
        """
        try:
            # Stap 1: Valideer category change
            if old_category == new_category:
                return CategoryChangeResult(
                    success=False,
                    message="Nieuwe categorie is gelijk aan huidige categorie",
                    action=WorkflowAction.NO_ACTION,
                    old_category=old_category,
                    new_category=new_category,
                    requires_regeneration=False,
                    error="Geen wijziging",
                )

            # Stap 2: Update database indien nodig
            actual_old_category = old_category
            if definition_id:
                # Delegeer naar CategoryService voor database update
                # Dit is waar we normaal dependency injection zouden gebruiken
                from database.definitie_repository import get_definitie_repository
                from services.category_service import CategoryService

                repo = get_definitie_repository()
                category_service = CategoryService(repo)

                update_result = category_service.update_category_v2(
                    definition_id, new_category, user=user, reason=reason
                )

                if not update_result.success:
                    return CategoryChangeResult(
                        success=False,
                        message=f"Fout bij update: {update_result.message}",
                        action=WorkflowAction.SHOW_ERROR,
                        old_category=old_category,
                        new_category=new_category,
                        requires_regeneration=False,
                        error=update_result.message,
                    )

                # Gebruik werkelijke oude categorie uit database
                actual_old_category = update_result.previous_category

                # Log voor audit trail
                logger.info(
                    f"Category updated for definition {definition_id}: "
                    f"{actual_old_category} → {new_category} by {user}"
                )

            # Stap 3: Bepaal vervolgacties
            requires_regeneration = self._should_regenerate_for_category_change(
                actual_old_category, new_category
            )

            # Stap 4: Prepareer UI response via DataAggregationService
            preview_data = None
            if requires_regeneration:
                # Gebruik DataAggregationService voor clean state management
                from database.definitie_repository import get_definitie_repository
                from services.data_aggregation_service import DataAggregationService

                data_service = DataAggregationService(get_definitie_repository())

                category_state = data_service.create_category_change_state(
                    old_category=actual_old_category,
                    new_category=new_category,
                    begrip=begrip,
                    current_definition=current_definition,
                    impact_analysis=self._analyze_category_change_impact(
                        actual_old_category, new_category
                    ),
                    saved_record_id=definition_id,
                    success_message=f"Categorie succesvol gewijzigd van '{actual_old_category}' naar '{new_category}'.",
                )

                # Converteer naar dictionary voor backward compatibility
                preview_data = {
                    "category_change_state": category_state,
                    "begrip": begrip,
                    "current_definition": current_definition,
                    "impact_analysis": category_state.impact_analysis,
                    "saved_record_id": definition_id,
                }

            # Bepaal UI actie
            action = (
                WorkflowAction.SHOW_REGENERATION_PREVIEW
                if requires_regeneration
                else WorkflowAction.SHOW_SUCCESS
            )

            # Bouw success message
            message = f"Categorie succesvol gewijzigd van '{actual_old_category}' naar '{new_category}'."
            if requires_regeneration:
                message += " Regeneratie opties zijn beschikbaar."

            # Trigger event voor andere systemen (event-driven architecture)
            self._emit_category_changed_event(
                {
                    "definition_id": definition_id,
                    "old_category": actual_old_category,
                    "new_category": new_category,
                    "user": user,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            return CategoryChangeResult(
                success=True,
                message=message,
                action=action,
                old_category=actual_old_category,
                new_category=new_category,
                requires_regeneration=requires_regeneration,
                preview_data=preview_data,
            )

        except Exception as e:
            logger.error(f"Error in category change workflow: {e}", exc_info=True)
            return CategoryChangeResult(
                success=False,
                message=f"Workflow fout: {e!s}",
                action=WorkflowAction.SHOW_ERROR,
                old_category=old_category,
                new_category=new_category,
                requires_regeneration=False,
                error=str(e),
            )

    def _should_regenerate_for_category_change(
        self, old_category: str, new_category: str
    ) -> bool:
        """
        Business rule: bepaal of regeneratie nodig is bij category change.

        Args:
            old_category: Oude categorie
            new_category: Nieuwe categorie

        Returns:
            True als regeneratie aanbevolen wordt
        """
        # Normaliseer voor vergelijking
        old_normalized = old_category.lower().strip()
        new_normalized = new_category.lower().strip()

        # Geen regeneratie nodig als het alleen een formatting verschil is
        if old_normalized == new_normalized:
            return False

        # Business rule: significante category changes vereisen regeneratie
        significant_changes = {
            ("proces", "type"),  # Van activiteit naar object
            ("type", "proces"),  # Van object naar activiteit
            ("proces", "resultaat"),  # Van activiteit naar uitkomst
            ("type", "resultaat"),  # Van object naar uitkomst
        }

        change_tuple = (old_normalized, new_normalized)

        # Altijd regenereren bij significante wijzigingen
        if change_tuple in significant_changes:
            logger.info(f"Significant category change detected: {change_tuple}")
            return True

        # Default: aanbevelen om te regenereren
        return True

    def _analyze_category_change_impact(
        self, old_category: str, new_category: str
    ) -> list[str]:
        """
        Analyseer de impact van een category wijziging.

        Args:
            old_category: Oude categorie
            new_category: Nieuwe categorie

        Returns:
            Lijst met impact beschrijvingen
        """
        impacts = []

        # Category-specific impact analysis
        category_impacts = {
            ("proces", "type"): [
                "🔄 Focus verschuift van 'hoe' naar 'wat'",
                "📝 Definitie wordt meer beschrijvend dan procedureel",
                "⚖️ Juridische precisie kan toenemen",
            ],
            ("type", "proces"): [
                "🔄 Focus verschuift van 'wat' naar 'hoe'",
                "📋 Definitie wordt meer procedureel",
                "⚙️ Stappen of fasen kunnen worden toegevoegd",
            ],
            ("proces", "resultaat"): [
                "🔄 Focus verschuift van activiteit naar uitkomst",
                "📊 Nadruk op het eindresultaat",
                "🎯 Doelgerichtheid wordt belangrijker",
            ],
            ("type", "resultaat"): [
                "🔄 Focus verschuift van object naar uitkomst",
                "📊 Definitie wordt resultaatgericht",
                "✅ Meetbaarheid kan verbeteren",
            ],
        }

        # Zoek specifieke impacts
        change_tuple = (old_category.lower(), new_category.lower())
        specific_impacts = category_impacts.get(change_tuple, [])

        if specific_impacts:
            impacts.extend(specific_impacts)
        else:
            # Generieke impacts voor andere wijzigingen
            impacts.append(
                f"🔄 Categorie wijzigt van '{old_category}' naar '{new_category}'"
            )

        # Algemene impacts die altijd gelden
        impacts.extend(
            [
                "🎯 Terminologie wordt aangepast aan nieuwe categorie",
                "✅ Kwaliteitstoetsing wordt opnieuw uitgevoerd",
                "📄 Nieuwe versie wordt aangemaakt in historie",
            ]
        )

        return impacts

    def _emit_category_changed_event(self, event_data: dict[str, Any]):
        """
        Emit event voor category change (voor event-driven architecture).

        In een volledig event-driven systeem zou dit een event publisher
        aanroepen. Voor nu loggen we alleen.

        Args:
            event_data: Event data om te verzenden
        """
        # TODO: Implement actual event publishing when event bus is available
        logger.info(f"Category change event: {event_data}")

        # Hier zou normaal een event publisher worden aangeroepen:
        # self.event_publisher.publish('definition.category.changed', event_data)
