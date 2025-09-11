"""
DefinitionWorkflowService - Combineert workflow en repository acties.

US-072: Deze service consolideert workflow transities (review/approve/reject) 
met de bijbehorende repository-updates en audit/event-publicatie zodat UI-code 
geen losse services hoeft te coördineren en we consistente businessregels afdwingen.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from database.definitie_repository import DefinitieRepository, DefinitieStatus
from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result van een workflow operatie."""
    
    success: bool
    new_status: str | None
    updated_by: str | None
    notes: str | None
    events: list[str]
    error_message: str | None = None
    timestamp: datetime | None = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DefinitionWorkflowService:
    """
    Service die workflow transities en repository updates combineert.
    
    Deze service zorgt voor:
    - Validatie van workflow transities volgens business regels
    - Atomaire updates van definitie status in repository
    - Audit logging van alle transities
    - Event publishing (indien event bus actief)
    """
    
    def __init__(
        self,
        workflow_service: WorkflowService,
        repository: DefinitieRepository,
        event_bus: Any | None = None,
        audit_logger: Any | None = None,
    ):
        """
        Initialize de workflow service.
        
        Args:
            workflow_service: Service voor workflow validatie
            repository: Repository voor persistentie
            event_bus: Optionele event bus voor event publishing
            audit_logger: Optionele audit logger
        """
        self.workflow_service = workflow_service
        self.repository = repository
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        
    def submit_for_review(
        self,
        definition_id: int,
        user: str,
        notes: str = "",
    ) -> WorkflowResult:
        """
        Submit een definitie voor review.
        
        Args:
            definition_id: ID van de definitie
            user: Gebruiker die de actie uitvoert
            notes: Optionele notities
            
        Returns:
            WorkflowResult met status en metadata
        """
        try:
            # Haal huidige definitie op
            definition = self.repository.get(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )
            
            # Valideer transitie via workflow service
            current_status = DefinitieStatus(definition.status)
            if not self.workflow_service.can_transition(
                current_status, DefinitieStatus.REVIEW
            ):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status.value} naar REVIEW niet toegestaan",
                )
            
            # Update status in repository (atomair)
            success = self.repository.update_status(
                definition_id=definition_id,
                new_status=DefinitieStatus.REVIEW,
                updated_by=user,
                notes=notes,
            )
            
            if not success:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message="Status update mislukt in repository",
                )
            
            # Log audit trail
            if self.audit_logger:
                self.audit_logger.log_transition(
                    definition_id=definition_id,
                    from_status=current_status.value,
                    to_status=DefinitieStatus.REVIEW.value,
                    user=user,
                    notes=notes,
                )
            
            # Publish event
            events = []
            if self.event_bus:
                event = {
                    "type": "definition.submitted_for_review",
                    "definition_id": definition_id,
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                }
                self.event_bus.publish(event)
                events.append("definition.submitted_for_review")
            
            logger.info(
                f"Definitie {definition_id} submitted for review by {user}"
            )
            
            return WorkflowResult(
                success=True,
                new_status=DefinitieStatus.REVIEW.value,
                updated_by=user,
                notes=notes,
                events=events,
            )
            
        except Exception as e:
            logger.error(f"Error submitting definition {definition_id} for review: {e}")
            return WorkflowResult(
                success=False,
                new_status=None,
                updated_by=None,
                notes=None,
                events=[],
                error_message=str(e),
            )
    
    def approve(
        self,
        definition_id: int,
        user: str,
        notes: str = "",
    ) -> WorkflowResult:
        """
        Approve een definitie.
        
        Args:
            definition_id: ID van de definitie
            user: Gebruiker die de actie uitvoert
            notes: Optionele notities
            
        Returns:
            WorkflowResult met status en metadata
        """
        try:
            # Haal huidige definitie op
            definition = self.repository.get(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )
            
            # Valideer transitie via workflow service
            current_status = DefinitieStatus(definition.status)
            if not self.workflow_service.can_transition(
                current_status, DefinitieStatus.APPROVED
            ):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status.value} naar APPROVED niet toegestaan",
                )
            
            # Update status in repository (atomair)
            success = self.repository.update_status(
                definition_id=definition_id,
                new_status=DefinitieStatus.APPROVED,
                updated_by=user,
                notes=notes,
            )
            
            if not success:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message="Status update mislukt in repository",
                )
            
            # Log audit trail
            if self.audit_logger:
                self.audit_logger.log_transition(
                    definition_id=definition_id,
                    from_status=current_status.value,
                    to_status=DefinitieStatus.APPROVED.value,
                    user=user,
                    notes=notes,
                )
            
            # Publish event
            events = []
            if self.event_bus:
                event = {
                    "type": "definition.approved",
                    "definition_id": definition_id,
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                }
                self.event_bus.publish(event)
                events.append("definition.approved")
            
            logger.info(f"Definitie {definition_id} approved by {user}")
            
            return WorkflowResult(
                success=True,
                new_status=DefinitieStatus.APPROVED.value,
                updated_by=user,
                notes=notes,
                events=events,
            )
            
        except Exception as e:
            logger.error(f"Error approving definition {definition_id}: {e}")
            return WorkflowResult(
                success=False,
                new_status=None,
                updated_by=None,
                notes=None,
                events=[],
                error_message=str(e),
            )
    
    def reject(
        self,
        definition_id: int,
        user: str,
        reason: str = "",
    ) -> WorkflowResult:
        """
        Reject een definitie.
        
        Args:
            definition_id: ID van de definitie
            user: Gebruiker die de actie uitvoert
            reason: Reden voor afwijzing
            
        Returns:
            WorkflowResult met status en metadata
        """
        try:
            # Haal huidige definitie op
            definition = self.repository.get(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )
            
            # Valideer transitie via workflow service
            current_status = DefinitieStatus(definition.status)
            if not self.workflow_service.can_transition(
                current_status, DefinitieStatus.REJECTED
            ):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status.value} naar REJECTED niet toegestaan",
                )
            
            # Update status in repository (atomair)
            success = self.repository.update_status(
                definition_id=definition_id,
                new_status=DefinitieStatus.REJECTED,
                updated_by=user,
                notes=reason,
            )
            
            if not success:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message="Status update mislukt in repository",
                )
            
            # Log audit trail
            if self.audit_logger:
                self.audit_logger.log_transition(
                    definition_id=definition_id,
                    from_status=current_status.value,
                    to_status=DefinitieStatus.REJECTED.value,
                    user=user,
                    notes=reason,
                )
            
            # Publish event
            events = []
            if self.event_bus:
                event = {
                    "type": "definition.rejected",
                    "definition_id": definition_id,
                    "user": user,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                }
                self.event_bus.publish(event)
                events.append("definition.rejected")
            
            logger.info(
                f"Definitie {definition_id} rejected by {user} with reason: {reason}"
            )
            
            return WorkflowResult(
                success=True,
                new_status=DefinitieStatus.REJECTED.value,
                updated_by=user,
                notes=reason,
                events=events,
            )
            
        except Exception as e:
            logger.error(f"Error rejecting definition {definition_id}: {e}")
            return WorkflowResult(
                success=False,
                new_status=None,
                updated_by=None,
                notes=None,
                events=[],
                error_message=str(e),
            )
    
    def get_allowed_transitions(
        self,
        definition_id: int,
    ) -> list[str]:
        """
        Haal toegestane transities op voor een definitie.
        
        Args:
            definition_id: ID van de definitie
            
        Returns:
            Lijst met toegestane status transities
        """
        try:
            definition = self.repository.get(definition_id)
            if not definition:
                return []
            
            current_status = DefinitieStatus(definition.status)
            return self.workflow_service.get_allowed_transitions(current_status)
            
        except Exception as e:
            logger.error(f"Error getting allowed transitions for {definition_id}: {e}")
            return []