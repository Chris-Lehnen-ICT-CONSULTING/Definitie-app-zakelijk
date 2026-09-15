"""
DefinitionWorkflowService - Combineert workflow en repository acties.

US-072: Deze service consolideert workflow transities (review/approve/reject)
met de bijbehorende repository-updates en audit/event-publicatie zodat UI-code
geen losse services hoeft te coördineren en we consistente businessregels afdwingen.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from database.definitie_repository import (
    UNSET,
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
    Unset,
    VaststelconflictError,
)
from domain.context.contract import STATUS_FAIL, STATUS_PASS, beoordeel_context
from domain.context.normalisatie import lees_contextwaarden
from services.workflow_service import WorkflowService

# US-160: Policy service voor gate-checks
try:  # pragma: no cover - import guard for isolated tests
    from services.policies.approval_gate_policy import GatePolicyService
except Exception:  # pragma: no cover - optional during tests
    GatePolicyService = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class _VaststellingMisluktError(Exception):
    """Interne signalering binnen ``approve()``: rol de transactie terug."""

    def __init__(self, message: str, gate_status: str | None = None) -> None:
        super().__init__(message)
        self.gate_status = gate_status


def ufo_categorie_uit_selectie(selectie: object) -> str | Unset:
    """Vertaal een UI-selectie naar het ``change_status``-contract.

    ``None`` (geen keuze gemaakt) laat de kolom staan; ``""`` maakt haar leeg;
    elke andere waarde wordt gezet. Houdt persistentiesemantiek uit de UI.
    """
    return UNSET if selectie is None else str(selectie)


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

    def __post_init__(self) -> None:
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
        ufo_categorie: str | Unset | None = UNSET,
        *,
        expected_version: int,
        vervang_definitie_id: int | None = None,
    ) -> WorkflowResult:
        """
        Stel een definitie vast (DEF-482: één atomaire unit-of-work).

        Status, approval-metadata, ketenpartners, UFO-categorie en de app-auditrij
        committen samen of helemaal niet. Alleen exact de beoordeelde versie kan
        worden vastgesteld (optimistic lock op ``version_number``). ``approve()``
        is eigenaar van de transactie: een al open transactie op deze thread
        wordt geweigerd. Audit-logger en event bus draaien pas ná de commit en
        kunnen een gecommitte vaststelling niet meer ongedaan maken.

        DEF-622 (B-03/B-10): er is maximaal één vastgesteld, leidend record per
        begrip + volledige genormaliseerde context, ongeacht categorie. Bestaat
        er al zo'n record, dan wordt de vaststelling geweigerd
        (``gate_status="conflict"``) tenzij de gebruiker het bewust vervangt via
        ``vervang_definitie_id``: dan wordt dat record in dezelfde transactie
        gearchiveerd (reguliere statusaudit, met verwijzing naar de opvolger) en
        de nieuwe definitie vastgesteld. Het conflict wordt onder de schrijflock
        hercontroleerd, zodat gelijktijdige pogingen nooit twee leidende records
        overlaten. Dit is de inter-recordafhandeling; de per-recordgarantie
        (versie, audit, metadata samen) is en blijft DEF-482.

        Args:
            definition_id: ID van de definitie
            user: Gebruiker die de actie uitvoert
            notes: Optionele notities
            ketenpartners: Optioneel; ``None`` laat de kolom ongemoeid
            user_role: Rol voor de transitiecontrole
            ufo_categorie: ``UNSET`` laat staan, ``""`` maakt leeg, anders zet
            expected_version: de ``version_number`` die de reviewer beoordeeld
                heeft (het getoonde snapshot). Wijkt de opgeslagen versie daarvan
                af, dan wordt niets beoordeeld of geschreven (``gate_status="stale"``).
            vervang_definitie_id: het vastgestelde record dat de gebruiker
                bewust door deze definitie vervangt (B-10).

        Returns:
            WorkflowResult met status en metadata
        """
        try:
            if self.repository.in_transaction():
                return self._mislukt(
                    "Vaststellen geweigerd: er is al een transactie actief op deze thread"
                )

            definition = self.repository.get_definitie(definition_id)
            if not definition:
                return self._mislukt(f"Definitie {definition_id} niet gevonden")
            current_status = definition.status
            # Controles vóór de transactie (kort lockvenster): versie, transitie,
            # gate (US-160) en conflict (DEF-622). De version guard en de
            # hercontrole ónder de schrijflock hieronder blijven bindend.
            geweigerd, gate = self._vooraf_geweigerd(
                definition,
                expected_version=expected_version,
                user_role=user_role,
                notes=notes,
                vervang_definitie_id=vervang_definitie_id,
            )
            if geweigerd is not None:
                return geweigerd

            try:
                with self.repository.transaction():
                    # Hercontrole onder de lock: een gelijktijdige vaststelling
                    # die zojuist committe, is nu zichtbaar.
                    actueel = self.repository.get_definitie(definition_id)
                    if actueel is None:
                        raise _VaststellingMisluktError(
                            f"Definitie {definition_id} niet gevonden"
                        )
                    conflict = self._conflict_met_leidend_record(
                        actueel, vervang_definitie_id
                    )
                    if conflict is not None:
                        raise _VaststellingMisluktError(
                            f"Vaststellen geblokkeerd: {conflict}",
                            gate_status="conflict",
                        )
                    if vervang_definitie_id is not None:
                        # B-10: bewuste vervanging — het eerdere leidende record
                        # wordt in dezelfde handeling gearchiveerd (historie en
                        # reguliere statusaudit blijven), mét opvolgerverwijzing.
                        gearchiveerd = self.repository.change_status(
                            definitie_id=vervang_definitie_id,
                            new_status=DefinitieStatus.ARCHIVED,
                            changed_by=user,
                            notes=f"vervangen door definitie {definition_id}",
                        )
                        if not gearchiveerd:
                            raise _VaststellingMisluktError(
                                f"Vervanging mislukt: definitie {vervang_definitie_id} "
                                "kon niet worden gearchiveerd",
                                gate_status="conflict",
                            )
                    success = self.repository.change_status(
                        definitie_id=definition_id,
                        new_status=DefinitieStatus.ESTABLISHED,
                        changed_by=user,
                        notes=notes,
                        ketenpartners=ketenpartners,
                        ufo_categorie=ufo_categorie,
                        expected_version=expected_version,
                    )
                    if not success:
                        # `False` betekent hier: de UPDATE raakte nul rijen. Een
                        # repositoryfout propageert binnen een open transactie als
                        # exceptie (facade), dus deze herlezing ziet nooit een eigen
                        # onbevestigde versiebump.
                        actueel = self.repository.get_definitie(definition_id)
                        if (
                            actueel is None
                            or actueel.version_number != expected_version
                        ):
                            raise _VaststellingMisluktError(
                                "Definitie is intussen gewijzigd; beoordeel opnieuw",
                                gate_status="stale",
                            )
                        raise _VaststellingMisluktError(
                            "Status update mislukt in repository"
                        )
            except VaststelconflictError as e:
                # De persistentiegrens ving een conflict dat de hercontrole
                # hierboven niet zag (bv. een concurrerende commit tussen
                # beide leesmomenten). Zelfde uitkomst, zelfde gate-status.
                return self._mislukt(
                    f"Vaststellen geblokkeerd: {e}",
                    gate_status="conflict",
                    gate_reasons=[str(e)],
                )
            except _VaststellingMisluktError as e:
                return self._mislukt(
                    str(e),
                    gate_status=e.gate_status,
                    gate_reasons=gate["reasons"] if e.gate_status else None,
                )

            # Bijeffecten pas na bewezen commit; een fout hier mag de
            # gecommitte vaststelling niet als mislukt rapporteren.
            events = self._publiceer_na_commit(
                definition_id=definition_id,
                from_status=current_status,
                to_status=DefinitieStatus.ESTABLISHED.value,
                user=user,
                notes=notes,
                event_type="definition.approved",
            )

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
            return self._mislukt(str(e))

    @staticmethod
    def _mislukt(
        error_message: str,
        gate_status: str | None = None,
        gate_reasons: list[str] | None = None,
    ) -> WorkflowResult:
        return WorkflowResult(
            success=False,
            new_status=None,
            updated_by=None,
            notes=None,
            events=[],
            error_message=error_message,
            gate_status=gate_status,
            gate_reasons=gate_reasons,
        )

    def _vooraf_geweigerd(
        self,
        definition: DefinitieRecord,
        *,
        expected_version: int,
        user_role: str | None,
        notes: str,
        vervang_definitie_id: int | None,
    ) -> tuple[WorkflowResult | None, dict[str, Any]]:
        """De controles van `approve` vóór de transactie, in deze volgorde:
        versie (stale), transitie, gate (US-160), conflict (DEF-622).

        Geeft (weigering of None, gate). De gate wordt pas geëvalueerd als
        versie en transitie kloppen.
        """
        leeg: dict[str, Any] = {"status": "blocked", "reasons": []}
        if definition.version_number != expected_version:
            # Het beoordeelde snapshot (UI) is ouder dan de database: niet
            # beoordelen, niet schrijven. Dezelfde waarde dient in `approve`
            # als SQL-guard voor wijzigingen tussen gate en UPDATE.
            return (
                self._mislukt(
                    "Definitie is intussen gewijzigd; beoordeel opnieuw",
                    gate_status="stale",
                    gate_reasons=[],
                ),
                leeg,
            )
        if not self.workflow_service.can_change_status(
            definition.status, "established", user_role
        ):
            return (
                self._mislukt(
                    f"Transitie van {definition.status} naar ESTABLISHED niet toegestaan"
                ),
                leeg,
            )
        gate = self._evaluate_gate(definition)
        if gate["status"] == "blocked":
            return (
                self._mislukt(
                    f"Vaststellen geblokkeerd: {'; '.join(gate['reasons'])}",
                    gate_status="blocked",
                    gate_reasons=gate["reasons"],
                ),
                gate,
            )
        if gate["status"] == "override_required" and not (notes and notes.strip()):
            return (
                self._mislukt(
                    "Override vereist: geef een reden op in het notitieveld",
                    gate_status="override_required",
                    gate_reasons=gate["reasons"],
                ),
                gate,
            )
        # DEF-622: conflictcontrole vóór de transactie (duidelijke melding);
        # de bindende hercontrole zit in `approve` ónder de schrijflock.
        conflict = self._conflict_met_leidend_record(definition, vervang_definitie_id)
        if conflict is not None:
            return (
                self._mislukt(
                    f"Vaststellen geblokkeerd: {conflict}",
                    gate_status="conflict",
                    gate_reasons=[conflict],
                ),
                gate,
            )
        return None, gate

    def _publiceer_na_commit(
        self,
        *,
        definition_id: int,
        from_status: str,
        to_status: str,
        user: str,
        notes: str,
        event_type: str,
    ) -> list[str]:
        """Audit-logger en event bus ná de commit; fouten worden gelogd, niet doorgegooid."""
        events: list[str] = []
        if self.audit_logger:
            try:
                self.audit_logger.log_transition(
                    definition_id=definition_id,
                    from_status=from_status,
                    to_status=to_status,
                    user=user,
                    notes=notes,
                )
            except Exception:
                logger.exception(
                    "Audit-logging na commit mislukt voor definitie %s", definition_id
                )
        if self.event_bus:
            try:
                self.event_bus.publish(
                    {
                        "type": event_type,
                        "definition_id": definition_id,
                        "user": user,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                events.append(event_type)
            except Exception:
                logger.exception(
                    "Eventpublicatie na commit mislukt voor definitie %s", definition_id
                )
        return events

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
        from database.models import DefinitieStatus

        try:
            # Convert string to enum (case insensitive)
            status_enum = DefinitieStatus[new_status.upper()]

            # Delegate to repository
            return cast(
                bool,
                self.repository.change_status(
                    definitie_id=definition_id,
                    new_status=status_enum,
                    changed_by=user,
                    notes=notes,
                ),
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
            return cast(
                list[str],
                self.workflow_service.get_allowed_transitions(current_status),
            )

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
                # DEF-439: defensieve fallback voor repo-varianten zonder
                # get_definitie (service-laag heeft .get); cast houdt mypy rustig.
                else cast(Any, self.repository).get(definition_id)
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

    def _evaluate_gate(self, definition: DefinitieRecord) -> dict[str, Any]:
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
        org_list, jur_list, wb_list = self._gate_contextlijsten(definition)

        if policy.hard_requirements.get("min_one_context_required", True):
            if not (org_list or jur_list or wb_list):
                reasons.append("Geen context ingevuld (minimaal één vereist)")

        # 2) Validatiescore en issues
        score = getattr(definition, "validation_score", None)
        issues: list[dict[str, Any]] = []
        if hasattr(definition, "get_validation_issues_list"):
            issues = definition.get_validation_issues_list() or []
        severities = {str(i.get("severity", "")).lower() for i in issues}
        has_critical = "critical" in severities
        has_high = "high" in severities and not has_critical

        # 3) Hard conditions
        hard_min = policy.hard_min_score
        soft_min = policy.soft_min_score

        if score is None:
            # DEF-622: ook 'totaalscore niet beschikbaar' (CON-01 zonder
            # cijfer) landt hier als None. De blokkade blijft fail-closed;
            # de herdefinitie van de scoregate zonder totaalscore is DEF-630.
            reasons.append("Geen validatieresultaat beschikbaar (eerst (her)valideren)")

        if (
            policy.hard_requirements.get("forbid_critical_issues", True)
            and has_critical
        ):
            reasons.append("Kritieke issues aanwezig")

        if score is not None and float(score) < hard_min:
            reasons.append(f"Score onder harde drempel ({hard_min:.2f})")

        # DEF-622 (B-07): het contextcontract is een vaststelvoorwaarde die
        # niet met een notitie te overrulen is. Geen context, een open
        # naamfunctie, een beoordeling die niet meer bij de huidige tekst/
        # context hoort, of registratiegebruik: geen vaststelling. Het concept
        # blijft gewoon bewerkbaar. Herberekend op het record zelf, zodat een
        # verouderde beoordeling nooit kan doortellen.
        niet_overrulebaar: list[str] = []
        if not (org_list or jur_list or wb_list):
            niet_overrulebaar.append(
                "Geen context vastgelegd bij het record (CON-01, B-01); "
                "vaststellen is niet mogelijk zonder context"
            )
        else:
            niet_overrulebaar.extend(self._con01_blokkades(definition))
        # DEF-743 (CON-02): verouderd, technisch mislukt of ontbrekend bronbewijs
        # kan niet als goedgekeurd gelden; een geaccepteerde deskundige
        # uitzondering wordt als uitzondering herkend. Smalle guard naast de
        # bestaande scoregate (die blijft ongewijzigd, incl. de blokkade bij
        # `validation_score is None` — DEF-630).
        niet_overrulebaar.extend(self._con02_blokkades(definition))

        hard_block = any(
            r in reasons
            for r in [
                "Geen context ingevuld (minimaal één vereist)",
                "Kritieke issues aanwezig",
                f"Score onder harde drempel ({hard_min:.2f})",
                "Geen validatieresultaat beschikbaar (eerst (her)valideren)",
            ]
        )

        if niet_overrulebaar:
            return {"status": "blocked", "reasons": niet_overrulebaar + reasons}

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

    @staticmethod
    def _gate_contextlijsten(
        definition: DefinitieRecord,
    ) -> tuple[list[Any], list[Any], list[Any]]:
        """(organisatorisch, juridisch, wettelijk) zoals de gate ze leest.

        JSON-arrays in TEXT voor org/jur; wet via de recordhelper. Onleesbare
        waarden tellen als leeg (DEF-246).
        """
        import json as _json

        def _parse_list(val: Any) -> list[Any]:
            try:
                if not val:
                    return []
                return list(_json.loads(val)) if isinstance(val, str) else list(val)
            except (TypeError, ValueError):
                return []

        org_list = _parse_list(getattr(definition, "organisatorische_context", []))
        jur_list = _parse_list(getattr(definition, "juridische_context", []))
        wb_list: list[Any] = []
        if hasattr(definition, "get_wettelijke_basis_list"):
            wb_list = definition.get_wettelijke_basis_list() or []
        return org_list, jur_list, wb_list

    @staticmethod
    def _con01_blokkades(definition: DefinitieRecord) -> list[str]:
        """De CON-01-vaststelvoorwaarde (B-07), herberekend op het record.

        Gebruikt de vastgelegde expertbeoordeling (`get_context_review`) —
        die telt alleen wanneer haar vingerafdruk bij de huidige tekst,
        context en term hoort. Uitkomsten: Voldoet → geen blokkade; Voldoet
        niet → blokkade met de reden; Nog te beoordelen → blokkade met wat er
        nog beoordeeld moet worden. Een technisch probleem blokkeert ook:
        een vereiste beoordeling is dan niet uitgevoerd.
        """
        # Eén tekst- en contextbasis met experttab, readback en export (K4):
        # de definitiezin en de contractvelden zoals het record ze draagt.
        # Een vervanger zonder recordadapter (tests met kale objecten) krijgt
        # de kale velden: geen beoordeling, geen bekende versie.
        if isinstance(definition, DefinitieRecord):
            velden = definition.get_contractvelden()
            tekst = definition.get_definitie_tekst()
        else:
            velden = {
                "organisatorische_context": lees_contextwaarden(
                    getattr(definition, "organisatorische_context", None)
                ),
                "juridische_context": lees_contextwaarden(
                    getattr(definition, "juridische_context", None)
                ),
                "wettelijke_basis": lees_contextwaarden(
                    getattr(definition, "wettelijke_basis", None)
                ),
                "context_review": None,
                "definition_version": None,
            }
            tekst = getattr(definition, "definitie", None) or ""
        review = velden["context_review"]
        uitkomst = beoordeel_context(
            getattr(definition, "begrip", None) or "",
            tekst,
            {
                sleutel: velden[sleutel]
                for sleutel in (
                    "organisatorische_context",
                    "juridische_context",
                    "wettelijke_basis",
                )
            },
            review=review,
            # E2: de beoordeling geldt voor precies deze recordversie.
            definitie_versie=velden["definition_version"],
        )
        if uitkomst.status == STATUS_PASS:
            return []
        label = (
            "Voldoet niet" if uitkomst.status == STATUS_FAIL else "Nog te beoordelen"
        )
        blokkades: list[str] = []
        for part in uitkomst.parts:
            if part.status == STATUS_PASS:
                continue
            aanleiding = f" (aanleiding: '{part.evidence}')" if part.evidence else ""
            blokkades.append(
                f"CON-01 {label}{aanleiding}: {part.reason} Vervolgstap: {part.action}"
            )
        # Een aangeleverde maar niet toegepaste beoordeling verdwijnt niet
        # stil: de reden (vingerafdruk, versie, beoordelaar) staat erbij.
        samenvatting = uitkomst.review if isinstance(uitkomst.review, dict) else {}
        if review is not None and not samenvatting.get("applied"):
            reden = samenvatting.get("reason") or "beoordeling niet bruikbaar"
            blokkades.append(f"CON-01: eerdere beoordeling niet toegepast: {reden}")
        return blokkades or [f"CON-01 {label}: contextcontract niet voldaan"]

    @staticmethod
    def _gedekt_door_uitzondering(part: Any, uitzondering: Any) -> bool:
        """Onderdelen die door een geaccepteerde uitzondering gedekt zijn:
        het uitzonderingsonderdeel zelf, en bij 'geen passende bron' de
        AI-onderdelen die alleen open staan omdat er geen bron is. Een
        deskundige *correctie* (C §6b) is géén uitzondering: haar onderdeel
        telt gewoon op status (fail/open blokkeert, pass niet)."""
        from domain.sources.contract import (
            AI_ONDERDELEN,
            BASIS_REVIEW,
            ONDERDEEL_UITZONDERING_GEEN_BRON,
            ONDERDEEL_VERWIJZING,
            STATUS_ERROR,
            STATUS_FAIL,
        )

        if part.field == BASIS_REVIEW and (
            part.id == ONDERDEEL_UITZONDERING_GEEN_BRON
            or (uitzondering == "reference" and part.id == ONDERDEEL_VERWIJZING)
        ):
            return True
        return bool(
            uitzondering == "no_source"
            and part.id in AI_ONDERDELEN
            and part.field is None
            and part.status not in (STATUS_FAIL, STATUS_ERROR)
        )

    @staticmethod
    def _con02_blokkades(definition: DefinitieRecord) -> list[str]:
        """De CON-02-bronbewijsvoorwaarde (DEF-743), herberekend op het record.

        Pure replay van de kern (`beoordeel_bronbasis`) op de opgeslagen
        tekst, context, bronset, AI-beoordeling en deskundige uitzondering —
        geen AI-aanroep. Voldoet → geen blokkade; Voldoet niet / technisch
        probleem / nog te beoordelen (verouderd of onbewezen bronbewijs, geen
        beoordeling) → blokkade met de reden. Een geaccepteerde uitzondering (`review.accepted_exception`)
        wordt als uitzondering herkend: het onderdeel dat zij dekt blokkeert
        niet; de overige onderdelen blijven onverminderd gelden. Een
        niet-toegepaste eerdere uitzondering wordt benoemd, nooit stil
        genegeerd.

        Een record ZONDER bronnen is 'nog te beoordelen' en blokkeert óók:
        ontbrekend bronbewijs kan niet als goedgekeurd gelden. De route is de
        gedocumenteerde deskundige uitzondering "geen passende bron" (besluit
        15-09-2026); een geaccepteerde uitzondering wordt hier als uitzondering
        herkend en blokkeert niet. Een deskundige *correctie* (C §6b) is geen
        uitzondering: haar onderdeel telt op status.

        Alleen voor een echt `DefinitieRecord`: een kale vervanger zonder
        bronvelden (tests) heeft geen bronbewijs om te beoordelen en krijgt
        geen verzonnen blokkade. Zonder bronkern: fail-closed blokkade.
        """
        if not isinstance(definition, DefinitieRecord):
            return []
        try:
            from domain.sources.contract import (
                STATUS_ERROR,
                STATUS_FAIL,
                STATUS_PASS,
                beoordeel_bronbasis,
            )
        except ImportError as e:
            logger.error("Bronbeoordelingskern niet beschikbaar: %s", e)
            return ["CON-02: bronbeoordelingskern niet beschikbaar (fail-closed)"]

        velden = definition.get_contractvelden()
        bronnen = velden.get("provenance_sources")
        if bronnen is None:
            bronnen = velden.get("sources")
        review = velden.get("source_review")
        uitkomst = beoordeel_bronbasis(
            definition.begrip or "",
            definition.get_definitie_tekst(),
            definition.get_contextlijsten(),
            list(bronnen or []),
            assessment=velden.get("source_assessment"),
            review=review,
            definitie_versie=velden.get("definition_version"),
            peildatum=velden.get("peildatum"),
        )
        if uitkomst.status == STATUS_PASS:
            return []
        samenvatting = uitkomst.review if isinstance(uitkomst.review, dict) else {}
        uitzondering = samenvatting.get("accepted_exception")
        label = {
            STATUS_FAIL: "Voldoet niet",
            STATUS_ERROR: "Technisch probleem",
        }.get(uitkomst.status, "Nog te beoordelen")
        blokkades: list[str] = []
        for part in uitkomst.parts:
            if part.status == STATUS_PASS:
                continue
            if DefinitionWorkflowService._gedekt_door_uitzondering(part, uitzondering):
                continue
            aanleiding = f" (aanleiding: '{part.evidence}')" if part.evidence else ""
            blokkades.append(
                f"CON-02 {label}{aanleiding}: {part.reason} Vervolgstap: {part.action}"
            )
        if review is not None and not samenvatting.get("applied"):
            reden = samenvatting.get("reason") or "uitzondering niet bruikbaar"
            blokkades.append(f"CON-02: eerdere uitzondering niet toegepast: {reden}")
        beoordeling = samenvatting.get("assessment")
        # Alleen een bestaande beoordeling die niet (meer) bindt is 'verouderd';
        # zonder bronnen is er per definitie geen beoordeling (dat dekt de
        # uitzondering of de open onderdelen hierboven).
        if (
            isinstance(beoordeling, dict)
            and beoordeling.get("applied") is False
            and beoordeling.get("status") == "assessed"
        ):
            blokkades.append(
                "CON-02: bronbeoordeling verouderd/niet toegepast: "
                f"{beoordeling.get('reason') or 'hoort niet bij deze tekst, context of bronset'}"
            )
        return blokkades

    def _conflict_met_leidend_record(
        self, definition: DefinitieRecord, vervang_definitie_id: int | None
    ) -> str | None:
        """De B-03/B-10-conflictcontrole: reden van weigering, of None.

        Er mag maximaal één vastgesteld record zijn per begrip + volledige
        context, ongeacht categorie. Bestaat er al zo'n record, dan is
        vaststellen alleen toegestaan als de gebruiker precies dát record
        bewust vervangt. Een `vervang_definitie_id` dat niet het leidende
        record is, wordt geweigerd: vervanging is geen vrijbrief.
        """
        leidend = self.repository.find_leidende_definitie(
            definition.begrip,
            definition.organisatorische_context,
            definition.juridische_context or "",
            definition.get_wettelijke_basis_list(),
            eigen_id=definition.id,
        )
        if leidend is None:
            if vervang_definitie_id is not None:
                return (
                    f"definitie {vervang_definitie_id} is niet het leidende record "
                    "voor dit begrip en deze context; er valt niets te vervangen"
                )
            return None
        if vervang_definitie_id == leidend.id:
            return None
        return (
            f"er is al een vastgestelde definitie (ID {leidend.id}) voor "
            f"'{definition.begrip}' met dezelfde context; kies bewust of die "
            "definitie wordt vervangen (maximaal één leidend record per begrip "
            "en context, DEF-622)"
        )

    def _get_policy(self) -> Any:
        # Prefer geïnjecteerde service; val terug op best-effort loader
        gate_policy_service = getattr(self, "gate_policy_service", None)
        if gate_policy_service:
            return gate_policy_service.get_policy()
        # DEF-439: GatePolicyService is None bij gefaalde optionele import.
        if GatePolicyService is not None:
            try:
                return GatePolicyService().get_policy()
            except Exception:  # pragma: no cover
                # DEF-469: niet stil terugvallen op defaults — een fout hier kan
                # betekenen dat een afwijkend geconfigureerde gate-policy genegeerd
                # wordt (verkeerde goedkeuring/afkeuring). Log expliciet; de
                # fallback naar defaults blijft als laatste vangnet.
                logger.error(
                    "GatePolicyService.get_policy() faalde, val terug op defaults",
                    exc_info=True,
                )

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
