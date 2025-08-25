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
