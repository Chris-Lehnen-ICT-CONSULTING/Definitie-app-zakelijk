"""
DefinitionWorkflowService - Combineert workflow en repository acties.

US-072: Deze service consolideert workflow transities (review/approve/reject) 
met de bijbehorende repository-updates en audit/event-publicatie zodat UI-code 
geen losse services hoeft te coördineren en we consistente businessregels afdwingen.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from database.definitie_repository import DefinitieRepository, DefinitieStatus
from services.workflow_service import WorkflowService

# US-160: Policy service voor gate-checks
try:  # pragma: no cover - import guard for isolated tests
    from services.policies.approval_gate_policy import GatePolicyService
except Exception:  # pragma: no cover - optional during tests
    GatePolicyService = None  # type: ignore[assignment]

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
    # US-160: Gate-uitkomst voor UI en logging
    gate_status: str | None = None  # pass | override_required | blocked
    gate_reasons: list[str] | None = None

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
        gate_policy_service: Any | None = None,
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
        self.gate_policy_service = gate_policy_service

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
            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )

            # Valideer transitie via workflow service (strings)
            current_status = definition.status
            if not self.workflow_service.can_change_status(current_status, "review"):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status} naar REVIEW niet toegestaan",
                )

            # Update status in repository (atomair)
            success = self.repository.change_status(
                definitie_id=definition_id,
                new_status=DefinitieStatus.REVIEW,
                changed_by=user,
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
                    from_status=current_status,
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

            logger.info(f"Definitie {definition_id} submitted for review by {user}")

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
        ketenpartners: list[str] | None = None,
        user_role: str | None = None,
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
            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )

            # Valideer transitie via workflow service (naar ESTABLISHED)
            current_status = definition.status
            if not self.workflow_service.can_change_status(
                current_status, "established", user_role
            ):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status} naar ESTABLISHED niet toegestaan",
                )

            # US-160: Gate-evaluatie vóór statuswijziging
            gate = self._evaluate_gate(definition)
            if gate["status"] == "blocked":
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Vaststellen geblokkeerd: {'; '.join(gate['reasons'])}",
                    gate_status="blocked",
                    gate_reasons=gate["reasons"],
                )
            if gate["status"] == "override_required":
                if not (notes and notes.strip()):
                    return WorkflowResult(
                        success=False,
                        new_status=None,
                        updated_by=None,
                        notes=None,
                        events=[],
                        error_message=(
                            "Override vereist: geef een reden op in het notitieveld"
                        ),
                        gate_status="override_required",
                        gate_reasons=gate["reasons"],
                    )

            # Update status in repository (atomair)
            success = self.repository.change_status(
                definitie_id=definition_id,
                new_status=DefinitieStatus.ESTABLISHED,
                changed_by=user,
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

            # Update ketenpartners indien opgegeven
            if ketenpartners is not None:
                try:
                    self.repository.update_definitie(
                        definition_id,
                        {
                            "ketenpartners": json.dumps(
                                list(ketenpartners), ensure_ascii=False
                            )
                        },
                        updated_by=user,
                    )
                except Exception as e:  # pragma: no cover
                    logger.warning(
                        f"Kon ketenpartners niet opslaan voor {definition_id}: {e}"
                    )

            # Log audit trail
            if self.audit_logger:
                self.audit_logger.log_transition(
                    definition_id=definition_id,
                    from_status=current_status,
                    to_status=DefinitieStatus.ESTABLISHED.value,
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

            logger.info(
                f"Definitie {definition_id} vastgesteld door {user} (gate={gate['status']})"
            )

            return WorkflowResult(
                success=True,
                new_status=DefinitieStatus.ESTABLISHED.value,
                updated_by=user,
                notes=notes,
                events=events,
                gate_status=gate["status"],
                gate_reasons=gate["reasons"],
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
            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Definitie {definition_id} niet gevonden",
                )

            # Valideer transitie via workflow service (strings)
            current_status = definition.status
            if not self.workflow_service.can_change_status(current_status, "draft"):
                return WorkflowResult(
                    success=False,
                    new_status=None,
                    updated_by=None,
                    notes=None,
                    events=[],
                    error_message=f"Transitie van {current_status} naar ARCHIVED niet toegestaan",
                )

            # Update status in repository (atomair)
            success = self.repository.change_status(
                definitie_id=definition_id,
                new_status=DefinitieStatus.DRAFT,
                changed_by=user,
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
                    from_status=current_status,
                    to_status=DefinitieStatus.DRAFT.value,
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
                new_status=DefinitieStatus.DRAFT.value,
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

    def update_status(
        self,
        definition_id: int,
        new_status: str,
        user: str | None = None,
        notes: str = "",
    ) -> bool:
        """
        Adapter voor repository change_status - implements interface.

        Converts string status to DefinitieStatus enum and delegates
        to repository's change_status method.

        Args:
            definition_id: ID of the definition
            new_status: New status as string
            user: User performing the change
            notes: Optional notes

        Returns:
            bool: True if successful
        """
        from models.enums import DefinitieStatus

        try:
            # Convert string to enum (case insensitive)
            status_enum = DefinitieStatus[new_status.upper()]

            # Delegate to repository
            return self.repository.change_status(
                definitie_id=definition_id,
                new_status=status_enum,
                changed_by=user,
                notes=notes,
            )
        except (KeyError, AttributeError) as e:
            logger.error(f"Invalid status '{new_status}': {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False

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
            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return []
            current_status = definition.status
            return self.workflow_service.get_allowed_transitions(current_status)

        except Exception as e:
            logger.error(f"Error getting allowed transitions for {definition_id}: {e}")
            return []

    # ===== US-160: Gate preview & evaluation =====
    def preview_gate(self, definition_id: int) -> dict[str, Any]:
        """Geef gate-status voor UI-presentatie (pass/override_required/blocked + redenen)."""
        try:
            # Gebruik legacy compat method om DefinitieRecord op te halen
            get_method = getattr(self.repository, "get_definitie", None)
            definition = (
                get_method(definition_id)
                if callable(get_method)
                else self.repository.get(definition_id)
            )
            if not definition:
                return {"status": "blocked", "reasons": ["Definitie niet gevonden"]}
            return self._evaluate_gate(definition)
        except Exception as e:  # pragma: no cover - guard
            logger.warning("Gate preview failed: %s", e)
            return {
                "status": "blocked",
                "reasons": ["Technische fout bij gate-preview"],
            }

    def _evaluate_gate(self, definition) -> dict[str, Any]:
        """Implementeert Option B gate-logica.

        Verwacht DefinitieRecord met velden:
        - validation_score (float | None)
        - validation_issues (JSON) via get_validation_issues_list()
        - organisatorische_context (str)
        - juridische_context (str | None)
        - wettelijke_basis (list via get_wettelijke_basis_list())
        """
        policy = self._get_policy()

        reasons: list[str] = []

        # 1) Context aanwezig? (JSON arrays in TEXT voor org/jur; wet via helper)
        import json as _json

        def _parse_list(val):
            try:
                if not val:
                    return []
                return list(_json.loads(val)) if isinstance(val, str) else list(val)
            except Exception:
                return []

        org_list = _parse_list(getattr(definition, "organisatorische_context", []))
        jur_list = _parse_list(getattr(definition, "juridische_context", []))
        wb_list = []
        if hasattr(definition, "get_wettelijke_basis_list"):
            wb_list = definition.get_wettelijke_basis_list() or []

        if policy.hard_requirements.get("min_one_context_required", True):
            if not (org_list or jur_list or wb_list):
                reasons.append("Geen context ingevuld (minimaal één vereist)")

        # 2) Validatiescore en issues
        score = getattr(definition, "validation_score", None)
        issues = []
        if hasattr(definition, "get_validation_issues_list"):
            issues = definition.get_validation_issues_list() or []
        severities = {str(i.get("severity", "")).lower() for i in issues}
        has_critical = "critical" in severities
        has_high = "high" in severities and not has_critical

        # 3) Hard conditions
        hard_min = policy.hard_min_score
        soft_min = policy.soft_min_score

        if score is None:
            reasons.append("Geen validatieresultaat beschikbaar (eerst (her)valideren)")

        if (
            policy.hard_requirements.get("forbid_critical_issues", True)
            and has_critical
        ):
            reasons.append("Kritieke issues aanwezig")

        if score is not None and float(score) < hard_min:
            reasons.append(f"Score onder harde drempel ({hard_min:.2f})")

        hard_block = any(
            r in reasons
            for r in [
                "Geen context ingevuld (minimaal één vereist)",
                "Kritieke issues aanwezig",
                f"Score onder harde drempel ({hard_min:.2f})",
                "Geen validatieresultaat beschikbaar (eerst (her)valideren)",
            ]
        )

        if hard_block:
            # Optioneel: sta override toe voor hard blocks indien policy dit toestaat
            try:
                allow_hard_override = bool(
                    getattr(policy, "soft_requirements", {}).get(
                        "allow_hard_override", False
                    )
                )
            except Exception:
                allow_hard_override = False

            if allow_hard_override:
                # Converteer naar override_required met bestaande redenen (UI vereist reden/notities)
                return {"status": "override_required", "reasons": reasons}
            return {"status": "blocked", "reasons": reasons}

        # 4) Soft conditions
        soft_reasons: list[str] = []
        if score is not None and soft_min <= float(score) < hard_min:
            soft_reasons.append(
                f"Score onder vaststel-drempel maar ≥ soft-drempel ({soft_min:.2f})"
            )
        if (
            policy.soft_requirements.get("allow_high_issues_with_override", True)
            and has_high
        ):
            soft_reasons.append("Alleen hoge issues aanwezig (geen kritieke)")
        if policy.soft_requirements.get("missing_wettelijke_basis_soft", True):
            if not wb_list:
                soft_reasons.append("Wettelijke basis ontbreekt")

        if soft_reasons:
            return {"status": "override_required", "reasons": soft_reasons}

        return {"status": "pass", "reasons": []}

    def _get_policy(self):
        # Prefer geïnjecteerde service; val terug op best-effort loader
        if getattr(self, "gate_policy_service", None):
            return self.gate_policy_service.get_policy()
        if GatePolicyService:
            try:
                return GatePolicyService().get_policy()
            except Exception:  # pragma: no cover
                pass

        # Fallback naar defaults uit policy module
        class _Defaults:
            hard_requirements = {
                "require_org_context": True,
                "require_jur_context": True,
                "forbid_critical_issues": True,
            }
            thresholds = {"hard_min_score": 0.75, "soft_min_score": 0.65}
            soft_requirements = {
                "allow_high_issues_with_override": True,
                "missing_wettelijke_basis_soft": True,
            }

            @property
            def hard_min_score(self) -> float:  # type: ignore[misc]
                return 0.75

            @property
            def soft_min_score(self) -> float:  # type: ignore[misc]
                return 0.65

        logger.warning("GatePolicyService niet beschikbaar - gebruik defaults")
        return _Defaults()
