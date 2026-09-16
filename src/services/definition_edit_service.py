"""
Service layer for definition edit interface functionality.

This service orchestrates the edit operations and provides
business logic for the definition edit interface.
"""

import logging
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast

from database.models import DefinitieRecord
from services.definition_edit_repository import DefinitionEditRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition
from services.validation.modular_validation_service import ModularValidationService

#: Sleutels uit het geladen record die de toetsing van de bewerkte kandidaat
#: mee moet krijgen (DEF-622 CON-01, DEF-743 CON-02). De bronset is die van
#: het ID-only geladen record; de bewerkte tekst/term/context komen uit de
#: editor. Een `source_assessment` reist bewust NIET mee: de actieve wrapper
#: verkrijgt zelf een beoordeling voor exact deze kandidaat (C-contract §8) en
#: negeert een meegegeven beoordeling — een UI kan zo nooit een oude positieve
#: beoordeling voor een gewijzigde tekst laten gelden.
_RECORDSLEUTELS_VOOR_TOETSING: tuple[str, ...] = (
    "context_review",
    "source_review",
    "peildatum",
)


def bouw_validatiecontext(
    definition: Definition, geladen_metadata: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Eén contextdict voor de sync- én async-toetsing van de bewerkte kandidaat.

    - De drie contextlijsten komen uit de bewerkte kandidaat en gaan altijd
      mee, ook leeg: de editor is gezaghebbend (CON-01-transport, DEF-622).
    - `record_text` = de exacte bewerkte tekst (CON-01/CON-02 binden eraan).
    - `definition_id`/`definition_version`/`context_review`/`source_review`/
      `peildatum` komen uit het geladen record; een verouderde beoordeling
      vervalt in de kern via vingerafdruk + versie, niet via UI-logica.
    - `provenance_sources` = dezelfde bronset als het geladen record (deep
      copy; `sources` als terugval voor oudere metadata). Zonder bronset
      geen sleutel: er wordt niets verzonnen.
    """
    meta: Mapping[str, Any] = geladen_metadata or {}
    ctx: dict[str, Any] = {
        "organisatorische_context": list(definition.organisatorische_context or []),
        "juridische_context": list(definition.juridische_context or []),
        "wettelijke_basis": list(definition.wettelijke_basis or []),
        "definition_id": definition.id,
        "definition_version": meta.get("version_number"),
        "record_text": definition.definitie,
    }
    for sleutel in _RECORDSLEUTELS_VOOR_TOETSING:
        ctx[sleutel] = deepcopy(meta.get(sleutel))
    bronnen = meta.get("provenance_sources")
    if bronnen is None:
        bronnen = meta.get("sources")
    if isinstance(bronnen, list):
        ctx["provenance_sources"] = deepcopy(bronnen)
    return ctx


def _als_mapping(waarde: Any) -> Mapping[str, Any]:
    """Typegetrouwe vernauwing: een mapping, anders een lege mapping."""
    return waarde if isinstance(waarde, Mapping) else {}


def _als_dict(waarde: Any) -> dict[str, Any]:
    """Typegetrouwe vernauwing: een dict, anders een lege dict."""
    return waarde if isinstance(waarde, dict) else {}


@dataclass(frozen=True)
class _Weigering:
    """Een weigering (status/message[/validation]) als onderscheidbaar type,
    zodat een aanroeper haar niet met een validatieresultaat verwart."""

    payload: dict[str, Any]


def normaliseer_validatieresultaat(v: Mapping[str, Any]) -> dict[str, Any]:
    """Vertaal een V2-validatieresultaat naar de UI-structuur van de editor.

    Bewaart alles wat de gebruiker moet kunnen zien: de gestructureerde
    regeluitkomsten (`rule_results`), de status per regel (`rule_statuses`),
    de beoordelingsdekking (`evaluation_coverage`), open onderdelen
    (`review_required`), de validatiestatus/readiness (fail-closed guard) en
    de volledige bronbeoordeling (`source_assessment`, contract 1.4.0). Het
    ruwe resultaat blijft onder `raw_v2`.

    `score` is uitsluitend informatief-intern: `None` wanneer de sleutel
    ontbreekt óf expliciet None is. Er wordt nooit een 0.0 of een positief
    cijfer ingevuld (DEF-622/DEF-743); `valid` blijft fail-closed False bij
    een ontbrekend oordeel.

    DEF-624: de runstatus wordt via het contract expliciet gemaakt. Een
    resultaat zonder geldige `validation_status` is geen uitgevoerde run:
    `valid` is dan False, `validation_status` is `validation_unknown` en
    `unknown_reason` draagt de contractreden - ook in `raw_v2`, dat de
    gedeelde weergave rendert. De bron wordt niet gemuteerd.
    """
    from services.validation.result_contract import met_expliciete_runstatus

    ruw = met_expliciete_runstatus(v)
    violations = ruw.get("violations", []) or []
    normalized_issues = []
    for item in violations:
        if not isinstance(item, dict):
            continue
        normalized_issues.append(
            {
                "rule": item.get("rule_id") or item.get("code"),
                "message": item.get("description") or item.get("message", ""),
                "severity": item.get("severity", "warning"),
            }
        )
    ruwe_score = ruw.get("overall_score")
    try:
        score = None if ruwe_score is None else float(ruwe_score)
    except (TypeError, ValueError):
        score = None
    return {
        "valid": ruw.get("is_acceptable") is True,
        "score": score,
        "issues": normalized_issues,
        "rule_results": deepcopy(dict(ruw.get("rule_results") or {})),
        "rule_statuses": deepcopy(dict(ruw.get("rule_statuses") or {})),
        "evaluation_coverage": deepcopy(ruw.get("evaluation_coverage")),
        "review_required": deepcopy(list(ruw.get("review_required") or [])),
        "validation_status": ruw.get("validation_status"),
        "unknown_reason": ruw.get("unknown_reason"),
        "validation_readiness": deepcopy(ruw.get("validation_readiness")),
        "source_assessment": deepcopy(ruw.get("source_assessment")),
        "raw_v2": ruw,
    }


class AutoSaveResult(Enum):
    """Uitkomst van een auto-save (DEF-469).

    Onderscheidt expliciet "opgeslagen", "uitgeschakeld" en "mislukt" zodat de UI
    de gebruiker kan waarschuwen bij een echte fout i.p.v. een mislukte save te
    verwarren met een uitgeschakelde/overgeslagen save.
    """

    SAVED = "saved"
    DISABLED = "disabled"
    FAILED = "failed"

    # Let op: vergelijk met `is` (elk enum-lid is truthy — een `if auto_save(...)`
    # zou dus altijd waar zijn).


logger = logging.getLogger(__name__)


class DefinitionEditService:
    """
    Service for managing definition editing operations.

    Provides:
    - Edit orchestration with validation
    - Version management
    - Auto-save functionality
    - Conflict resolution
    """

    def __init__(
        self,
        repository: DefinitionEditRepository | None = None,
        validation_service: ModularValidationService | None = None,
        proposal_service: Any | None = None,
    ):
        """
        Initialize the edit service.

        Args:
            repository: Repository for data access
            validation_service: Service for validation
            proposal_service: DEF-743: `SourceProposalService` voor het
                handmatige verbetervoorstel (alleen op expliciet verzoek).
                Zonder dienst is de aanvraag geblokkeerd, nooit stil.
        """
        self.repository = repository or DefinitionEditRepository()
        self.validation_service = validation_service
        self.proposal_service = proposal_service

        # Auto-save configuration
        self.auto_save_interval = 30  # seconds
        self.auto_save_enabled = True

        # Cache for performance
        self._cache: dict[str, tuple[list[dict[str, Any]], datetime]] = {}
        self._cache_ttl = 300  # 5 minutes

        logger.info("DefinitionEditService initialized")

    def start_edit_session(
        self, definitie_id: int, user: str = "system"
    ) -> dict[str, Any]:
        """
        Start een edit sessie voor een definitie.

        Args:
            definitie_id: ID van de te bewerken definitie
            user: Gebruiker die edit sessie start

        Returns:
            Sessie informatie inclusief definitie en lock status
        """
        try:
            # Get definition
            definition = self.repository.get(definitie_id)
            if not definition:
                return {"success": False, "error": "Definitie niet gevonden"}

            # Check for existing auto-save
            auto_save = self.repository.get_latest_auto_save(definitie_id)

            # Get version history
            history = self.repository.get_version_history(definitie_id, limit=5)

            return {
                "success": True,
                "definition": definition,
                "auto_save": auto_save,
                "history": history,
                "session_id": self._generate_session_id(definitie_id, user),
                "locked": False,  # Implement locking if needed
                "user": user,
                "started_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error starting edit session: {e}")
            return {"success": False, "error": str(e)}

    def save_definition(
        self,
        definitie_id: int,
        updates: dict[str, Any],
        user: str = "system",
        reason: str | None = None,
        validate: bool = True,
    ) -> dict[str, Any]:
        """
        Sla definitie wijzigingen op.

        Args:
            definitie_id: ID van de definitie
            updates: Dictionary met updates
            user: Gebruiker die opslaat
            reason: Reden voor wijziging
            validate: Of validatie uitgevoerd moet worden

        Returns:
            Result dictionary met success status
        """
        try:
            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {"success": False, "error": "Definitie niet gevonden"}

            # Check version conflict
            if "version_number" in updates:
                if self.repository.check_version_conflict(
                    definitie_id, updates["version_number"]
                ):
                    return {
                        "success": False,
                        "error": "Versie conflict - definitie is gewijzigd door andere gebruiker",
                        "conflict": True,
                    }

            # Apply updates
            updated_definition = self._apply_updates(current, updates)

            # Validate if requested
            validation_results = None
            if validate and self.validation_service:
                validation_results = self._validate_definition(updated_definition)
                if validation_results and not validation_results.get("valid", True):
                    # Still save but mark validation issues
                    if not updated_definition.metadata:
                        updated_definition.metadata = {}
                    updated_definition.metadata["validation_issues"] = (
                        validation_results.get("issues", [])
                    )

            # Save with history
            saved_id = self.repository.save_with_history(
                updated_definition, wijziging_reden=reason, gewijzigd_door=user
            )

            # Clear cache
            self._clear_cache(definitie_id)

            return {
                "success": True,
                "definition_id": saved_id,
                "validation": validation_results,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error saving definition: {e}")
            return {"success": False, "error": str(e)}

    def auto_save(self, definitie_id: int, content: dict[str, Any]) -> AutoSaveResult:
        """
        Auto-save draft versie.

        Args:
            definitie_id: ID van de definitie
            content: Content om op te slaan

        Returns:
            AutoSaveResult: SAVED bij succes, DISABLED als auto-save uit staat,
            FAILED bij een fout (DEF-469: zodat de UI bij een echte fout kan
            waarschuwen i.p.v. die te verwarren met "uitgeschakeld").
        """
        if not self.auto_save_enabled:
            return AutoSaveResult.DISABLED

        try:
            # Add timestamp
            content["auto_save_timestamp"] = datetime.now().isoformat()

            # Save draft (repository raiset bij een DB-fout — niet langer stil False)
            self.repository.auto_save_draft(definitie_id, content)
            return AutoSaveResult.SAVED

        except RepositoryError as e:
            # Gericht op de repository-fout: onverwachte (programmeer)fouten laten
            # we bewust doorbubbelen i.p.v. te maskeren als "FAILED".
            logger.error(f"Auto-save failed: {e}", exc_info=True)
            return AutoSaveResult.FAILED

    def restore_auto_save(self, definitie_id: int) -> dict[str, Any] | None:
        """
        Herstel auto-save content.

        Args:
            definitie_id: ID van de definitie

        Returns:
            Auto-save content indien beschikbaar
        """
        try:
            result = self.repository.get_latest_auto_save(definitie_id)
            return cast(dict[str, Any] | None, result)
        except Exception as e:
            logger.error(f"Error restoring auto-save: {e}")
            return None

    def get_version_history(
        self, definitie_id: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Haal versie geschiedenis op.

        Args:
            definitie_id: ID van de definitie
            limit: Maximum aantal versies

        Returns:
            Lijst met versie geschiedenis
        """
        try:
            # Check cache
            cache_key = f"history_{definitie_id}_{limit}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                    return cached_data

            # Get from repository
            history = cast(
                list[dict[str, Any]],
                self.repository.get_version_history(definitie_id, limit),
            )

            # Process history entries
            for entry in history:
                # Add human-readable timestamp
                if "gewijzigd_op" in entry:
                    entry["gewijzigd_op_readable"] = self._format_timestamp(
                        entry["gewijzigd_op"]
                    )

                # Add change summary
                entry["summary"] = self._generate_change_summary(entry)

            # Cache result
            self._cache[cache_key] = (history, datetime.now())

            return history

        except Exception as e:
            logger.error(f"Error getting version history: {e}")
            return []

    def revert_to_version(
        self, definitie_id: int, version_id: int, user: str = "system"
    ) -> dict[str, Any]:
        """
        Revert definitie naar eerdere versie.

        Args:
            definitie_id: ID van de definitie
            version_id: ID van de versie om naar te reverten
            user: Gebruiker die revert uitvoert

        Returns:
            Result dictionary
        """
        try:
            # Get version from history
            history = self.repository.get_version_history(definitie_id, limit=100)

            version_entry = None
            for entry in history:
                if entry.get("id") == version_id:
                    version_entry = entry
                    break

            if not version_entry:
                return {"success": False, "error": "Versie niet gevonden"}

            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {"success": False, "error": "Definitie niet gevonden"}

            # Apply value from selected version (prefer new value of that entry)
            if version_entry.get("definitie_nieuwe_waarde"):
                current.definitie = version_entry["definitie_nieuwe_waarde"]
            elif version_entry.get("definitie_oude_waarde"):
                current.definitie = version_entry["definitie_oude_waarde"]

            # Apply context if available (Context Model V2: drie lijsten)
            if version_entry.get("context_snapshot"):
                context = version_entry["context_snapshot"]
                if isinstance(context, dict):
                    if "organisatorische_context" in context:
                        current.organisatorische_context = (
                            context["organisatorische_context"] or []
                        )
                    if "juridische_context" in context:
                        current.juridische_context = context["juridische_context"] or []
                    if "wettelijke_basis" in context:
                        current.wettelijke_basis = context["wettelijke_basis"] or []

            # Save as new version
            return self.save_definition(
                definitie_id,
                self._definition_to_dict(current),
                user=user,
                reason=f"Reverted naar versie {version_id}",
            )

        except Exception as e:
            logger.error(f"Error reverting to version: {e}")
            return {"success": False, "error": str(e)}

    def batch_update(
        self, updates: list[tuple[int, dict[str, Any]]], user: str = "system"
    ) -> dict[str, Any]:
        """
        Update meerdere definities tegelijk.

        Args:
            updates: Lijst van (definitie_id, update_dict) tuples
            user: Gebruiker die update uitvoert

        Returns:
            Result dictionary met successen en fouten
        """
        results: dict[str, Any] = {
            "success": [],
            "failed": [],
            "total": len(updates),
        }
        success_list: list[int] = results["success"]
        failed_list: list[dict[str, Any]] = results["failed"]

        for definitie_id, update_dict in updates:
            try:
                result = self.save_definition(
                    definitie_id,
                    update_dict,
                    user=user,
                    validate=False,  # Skip validation for batch
                )

                if result["success"]:
                    success_list.append(definitie_id)
                else:
                    failed_list.append(
                        {
                            "id": definitie_id,
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                failed_list.append({"id": definitie_id, "error": str(e)})

        return results

    def search_and_replace(
        self,
        search_term: str,
        replace_term: str,
        field: str = "definitie",
        filters: dict[str, Any] | None = None,
        user: str = "system",
    ) -> dict[str, Any]:
        """
        Zoek en vervang in meerdere definities.

        Args:
            search_term: Te zoeken term
            replace_term: Vervangende term
            field: Veld om in te zoeken (definitie, begrip, etc.)
            filters: Extra filters voor zoeken
            user: Gebruiker die operatie uitvoert

        Returns:
            Result dictionary
        """
        try:
            # Search definitions
            # Normalize filters: map legacy 'context' key to 'context_filter'
            normalized_filters = dict(filters) if filters else {}
            if (
                "context" in normalized_filters
                and "context_filter" not in normalized_filters
            ):
                normalized_filters["context_filter"] = normalized_filters.pop("context")

            definitions = self.repository.search_with_filters(
                search_term=search_term, **normalized_filters
            )

            updates = []
            for definition in definitions:
                # DEF-439: batch_update verwacht non-optional ids; sla door-id-loze
                # definities over (kunnen toch niet geadresseerd worden).
                if definition.id is None:
                    continue
                # Check if field contains search term
                field_value = getattr(definition, field, None)
                if field_value and search_term in field_value:
                    # Prepare update
                    new_value = field_value.replace(search_term, replace_term)
                    updates.append((definition.id, {field: new_value}))

            # Execute batch update
            if updates:
                return self.batch_update(updates, user=user)

            return {
                "success": [],
                "failed": [],
                "total": 0,
                "message": "Geen definities gevonden om te updaten",
            }

        except Exception as e:
            logger.error(f"Error in search and replace: {e}")
            return {"success": [], "failed": [], "error": str(e)}

    def _apply_updates(
        self, definition: Definition, updates: dict[str, Any]
    ) -> Definition:
        """Apply updates to definition object."""
        # Create copy
        updated = Definition(
            id=definition.id,
            begrip=updates.get("begrip", definition.begrip),
            definitie=updates.get("definitie", definition.definitie),
            toelichting=updates.get("toelichting", definition.toelichting),
            bron=updates.get("bron", definition.bron),
            organisatorische_context=updates.get(
                "organisatorische_context",
                getattr(definition, "organisatorische_context", []),
            ),
            juridische_context=updates.get(
                "juridische_context", getattr(definition, "juridische_context", [])
            ),
            wettelijke_basis=updates.get(
                "wettelijke_basis", getattr(definition, "wettelijke_basis", [])
            ),
            categorie=updates.get("categorie", definition.categorie),
            ufo_categorie=updates.get(
                "ufo_categorie", getattr(definition, "ufo_categorie", None)
            ),
            created_at=definition.created_at,
            updated_at=datetime.now(),
            metadata=definition.metadata or {},
        )

        # Update metadata fields
        metadata_fields = [
            "status",
            "juridische_context",
            "wettelijke_basis",
            "validation_score",
            "version_number",
        ]
        # DEF-439: metadata is dict|None (dataclass); narrow vóór indexed writes.
        if updated.metadata is None:
            updated.metadata = {}
        for field in metadata_fields:
            if field in updates:
                updated.metadata[field] = updates[field]

        return updated

    def _validate_definition(
        self,
        definition: Definition,
        geladen_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Validate definition using injected validation service (sync only).

        Async validation is not executed here. If only an async API is available,
        return None and let the UI call validation via async_bridge.

        DEF-743: de kandidaat is de ACTUELE bewerkte tekst/term/drie contexten;
        `geladen_metadata` (het ID-only geladen record) levert dezelfde
        bronset, recordversie en vastgelegde beoordelingen als het async pad
        (`bouw_validatiecontext`). Zonder `geladen_metadata` wordt
        `definition.metadata` gebruikt (een via de repository geladen record
        draagt die sleutels zelf).
        """
        if not self.validation_service:
            return None

        try:
            import inspect

            vs = self.validation_service

            # Eén contextdict voor sync én async (pariteit): bewerkte lijsten
            # altijd expliciet (ook leeg), bronset/versie/beoordeling uit het
            # geladen record.
            context_dict: dict[str, Any] = bouw_validatiecontext(
                definition,
                (
                    geladen_metadata
                    if geladen_metadata is not None
                    else (definition.metadata or {})
                ),
            )

            if hasattr(vs, "validate_text"):
                fn = vs.validate_text
                # Sla async API over (UI moet async_bridge gebruiken)
                if inspect.iscoroutinefunction(fn):
                    return None
                results = fn(
                    begrip=definition.begrip,
                    text=definition.definitie,
                    ontologische_categorie=getattr(
                        definition, "ontologische_categorie", None
                    )
                    or definition.categorie,
                    context=context_dict,
                )
            else:
                # Try generic validate_definition
                try:
                    fn = vs.validate_definition
                except AttributeError:
                    fn = getattr(vs, "validate", None)
                if fn is None:
                    return None
                if inspect.iscoroutinefunction(fn):
                    return None
                # Support both signatures
                try:
                    results = fn(definition)
                except TypeError:
                    results = fn(
                        begrip=definition.begrip,
                        text=definition.definitie,
                        ontologische_categorie=getattr(
                            definition, "ontologische_categorie", None
                        )
                        or definition.categorie,
                        context=context_dict,
                    )

            # Normalize result to UI format
            # Case 1: dict schema (ModularValidationService/Orchestrator ensure_schema)
            if isinstance(results, dict):
                # DEF-743: status, onderdelen, bewijs, open/technische
                # onderdelen en dekking blijven behouden; geen 0.0-terugval.
                return normaliseer_validatieresultaat(results)

            # Case 2: legacy object with attributes
            if hasattr(results, "overall_status") or hasattr(
                results, "validation_score"
            ):
                issues_attr = getattr(results, "issues", []) or []
                normalized_issues = []
                for issue in issues_attr:
                    try:
                        normalized_issues.append(
                            {
                                "rule": getattr(issue, "regel_code", None)
                                or getattr(issue, "rule", None),
                                "message": getattr(issue, "message", ""),
                                "severity": getattr(issue, "severity", "warning"),
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Validation issue normalisatie gefaald: {e}")
                # DEF-743: een ontbrekend cijfer blijft None (geen 0.0).
                legacy_score = getattr(results, "validation_score", None)
                return {
                    "valid": getattr(results, "overall_status", "") == "success",
                    "score": None if legacy_score is None else float(legacy_score),
                    "issues": normalized_issues,
                }

            # Unknown format
            return None

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None

    # ===== DEF-743: handmatig verbetervoorstel (CON-02) — alleen op verzoek =====

    def bronbasis_van_record(
        self, record: Any, huidig_resultaat: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """De actuele CON-02-uitkomst + bronbeoordeling voor het OPGESLAGEN record.

        Altijd een pure replay van de kern (`beoordeel_bronbasis`) tegen de
        ACTUELE opgeslagen deskundige beoordeling en recordversie — nooit het
        samengestelde CON-02-verdict uit een eerder sessieresultaat (dat
        kent de sindsdien vastgelegde correctie/uitzondering niet). Als
        beoordelingsinvoer geldt de opgeslagen volledige beoordeling wanneer
        die exact aan het record bindt; alleen als die ontbreekt of niet
        (meer) bindt, de sessiebeoordeling van de eigen wrapper, mits exact
        gebonden (zelfde vingerafdruk, status `assessed`). Nooit een
        AI-aanroep. Het oorspronkelijke AI-oordeel blijft via de kern
        zichtbaar (`applied_correction.original`).
        """
        from domain.sources.contract import (
            beoordeel_bronbasis,
            bereken_bronvingerafdruk,
        )

        velden = record.get_contractvelden()
        bronnen = velden.get("provenance_sources")
        if bronnen is None:
            bronnen = velden.get("sources")
        bronnen = list(bronnen or [])
        contexten = record.get_contextlijsten()
        tekst = record.get_definitie_tekst()
        peildatum = velden.get("peildatum")
        vingerafdruk = bereken_bronvingerafdruk(
            record.begrip or "", tekst, contexten, bronnen, peildatum=peildatum
        )
        basis: dict[str, Any] = {
            "bronnen": bronnen,
            "contexten": contexten,
            "tekst": tekst,
            "peildatum": peildatum,
            "fingerprint": vingerafdruk,
            "receipt": velden.get("source_receipt"),
            "validation_status": None,
        }

        def _gebonden(beoordeling: Any) -> bool:
            return (
                isinstance(beoordeling, Mapping)
                and beoordeling.get("fingerprint") == vingerafdruk
                and beoordeling.get("status") == "assessed"
            )

        assessment = velden.get("source_assessment")
        bron = "record"
        if not _gebonden(assessment) and isinstance(huidig_resultaat, Mapping):
            sessie = huidig_resultaat.get("source_assessment")
            if _gebonden(sessie):
                from services.validation.result_contract import bepaal_runstatus

                assessment = sessie
                bron = "sessie"
                # DEF-624: de status van het sessieresultaat via het contract;
                # een sessieresultaat zonder geldige status is geen run en
                # levert daarmee de technische diagnose, geen voorstel.
                basis["validation_status"] = bepaal_runstatus(huidig_resultaat).status
        uitkomst = beoordeel_bronbasis(
            record.begrip or "",
            tekst,
            contexten,
            bronnen,
            assessment=assessment,
            review=velden.get("source_review"),
            definitie_versie=velden.get("definition_version"),
            peildatum=peildatum,
        )
        basis["con02"] = uitkomst.als_dict()
        basis["assessment"] = assessment
        basis["bron"] = bron
        return basis

    @staticmethod
    def _canonieke_bronnen_met_passage(
        bronnen: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        from domain.sources.normalisatie import canoniseer_bronnen

        uit: list[dict[str, Any]] = []
        for bron in canoniseer_bronnen(bronnen):
            d = bron.als_dict()
            d["passage"] = bron.passage
            uit.append(d)
        return uit

    @staticmethod
    def _weergavecontrole(
        record: Any, expected_version: int | None
    ) -> dict[str, Any] | None:
        """F3: de getoonde versie en de actuele bewerkbaarheid, vóór elke aanroep.

        De UI geeft de recordversie mee die de gebruiker vóór zich had; wijkt
        het opgeslagen record daarvan af, dan is het antwoord een
        versieconflict — nooit stil de nieuwste versie. Een intussen
        vastgesteld of gearchiveerd record is niet bewerkbaar.
        """
        if expected_version is not None and record.version_number != expected_version:
            return {
                "status": "version_conflict",
                "message": (
                    f"De definitie is intussen gewijzigd (getoond: versie "
                    f"{expected_version}, opgeslagen: versie {record.version_number}); "
                    "ververs en beoordeel de actuele versie opnieuw."
                ),
                "version_number": record.version_number,
            }
        if str(getattr(record, "status", "") or "") in ("established", "archived"):
            return {
                "status": "not_editable",
                "message": (
                    f"De definitie heeft status '{record.status}' en is niet bewerkbaar; "
                    "zet haar via de Expert-tab terug naar Concept."
                ),
                "version_number": record.version_number,
            }
        return None

    def _actievoorbereiding(
        self, definitie_id: int, actor: str, expected_version: int | None
    ) -> DefinitieRecord | dict[str, Any]:
        """Gedeelde aanloop van aanvragen/toepassen/afwijzen, in vaste volgorde:
        reviewer-identiteit → record → weergaveversie/bewerkbaarheid (F3).
        Geeft het record, of de weigering (dict) die de aanroeper teruggeeft."""
        if not (actor or "").strip():
            return {
                "status": "no_actor",
                "message": "Een reviewer-identiteit is vereist.",
            }
        record = self.repository.get_definitie(definitie_id)
        if record is None:
            return {"status": "not_found", "message": "Definitie niet gevonden."}
        geweigerd = self._weergavecontrole(record, expected_version)
        if geweigerd is not None:
            return geweigerd
        return record

    @staticmethod
    def _reserveringsweigering(reservering: Any, diagnose: Any) -> dict[str, Any]:
        """De reservering bij D is niet gelukt: geen modelaanroep, met reden."""
        return {
            "status": reservering.status,
            "diagnose": diagnose.als_dict(),
            "message": reservering.reason
            or {
                "attempt_consumed": "Voor deze generatie is al een voorstel aangevraagd "
                "(maximaal één poging per generatie, DEF-638).",
                "version_conflict": "De definitie is intussen gewijzigd; ververs en "
                "probeer opnieuw.",
                "no_evidence": "Geen opgeslagen bronbewijs bij dit record.",
            }.get(reservering.status, reservering.status),
            "proposal_id": getattr(reservering, "proposal_id", None),
        }

    async def vraag_verbetervoorstel(
        self,
        definitie_id: int,
        *,
        actor: str,
        huidig_resultaat: Mapping[str, Any] | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Expliciete aanvraag van één verbetervoorstel (DEF-743, besluit 2).

        Volgorde: oorzaak bepalen (H) → alléén bij een aantoonbare
        tekortkoming een duurzame reservering bij D (max één poging per
        oorspronkelijke generatie) → één modelaanroep → uitkomst
        (`proposed|blocked|error`) vastleggen. De oorspronkelijke tekst
        wordt hier nooit gewijzigd. Geen dienst/geen reservering ⇒ geen
        aanroep, met een expliciete reden.
        """
        from services.source_proposal_service import diagnose_bronbasis

        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        try:
            basis = self.bronbasis_van_record(record, huidig_resultaat)
        except Exception as e:
            logger.error("Bronbasis niet te bepalen: %s", e, exc_info=True)
            return {
                "status": "error",
                "message": f"Bronbasis niet te bepalen: {type(e).__name__}: {e}",
            }
        diagnose = diagnose_bronbasis(
            basis["con02"],
            basis["assessment"],
            validation_status=basis["validation_status"],
            receipt=basis["receipt"],
        )
        if not diagnose.voorstel_mogelijk:
            # Geen modelaanroep en geen reservering: de poging blijft
            # beschikbaar tot er wél een aantoonbare tekortkoming met bewijs is.
            return {
                "status": "blocked",
                "diagnose": diagnose.als_dict(),
                "message": diagnose.toelichting,
                "proposal_id": None,
            }
        if self.proposal_service is None:
            return {
                "status": "unavailable",
                "diagnose": diagnose.als_dict(),
                "message": "Geen voorsteldienst beschikbaar (AI-service niet geconfigureerd).",
            }

        reservering = self.repository.reserve_source_proposal(
            definitie_id, updated_by=actor, expected_version=record.version_number
        )
        # D-contract: bij `reserved` zijn proposal_id en version_number gezet;
        # zonder die binding is er niets om een uitkomst aan vast te leggen —
        # dan geen modelaanroep (fail-closed, dezelfde weigering).
        proposal_id = reservering.proposal_id
        gereserveerde_versie = reservering.version_number
        if (
            reservering.status != "reserved"
            or proposal_id is None
            or gereserveerde_versie is None
        ):
            return self._reserveringsweigering(reservering, diagnose)

        try:
            voorstel = await self.proposal_service.stel_voor(
                begrip=record.begrip or "",
                tekst=basis["tekst"],
                contexten=basis["contexten"],
                bronnen=self._canonieke_bronnen_met_passage(basis["bronnen"]),
                con02=basis["con02"],
                assessment=basis["assessment"],
                peildatum=basis["peildatum"],
                validation_status=basis["validation_status"],
                receipt=basis["receipt"],
            )
        except Exception as e:
            # F7: de reservering staat al; een onverwachte fout in de dienst
            # wordt als duurzame `error`-uitkomst vastgelegd (poging verbruikt,
            # geen herhaling) — zonder prompt- of brontekst in de melding.
            logger.error(
                "Voorsteldienst faalde onverwacht: %s", type(e).__name__, exc_info=True
            )
            from services.source_proposal_service import Voorstel

            voorstel = Voorstel(
                status="error",
                diagnose=diagnose,
                error={
                    "type": "unexpected",
                    "message": f"{type(e).__name__} in de voorsteldienst",
                },
                findings=diagnose.bevindingen,
            )
        vastgelegd = self.repository.record_source_proposal_outcome(
            definitie_id,
            proposal_id,
            voorstel.als_outcome(),
            updated_by=actor,
            expected_version=gereserveerde_versie,
        )
        if not vastgelegd:
            logger.error(
                "Voorsteluitkomst niet vastgelegd (definitie %s, voorstel %s)",
                definitie_id,
                proposal_id,
            )
        self._clear_cache(definitie_id)
        return {
            "status": voorstel.status,
            "proposal_id": proposal_id,
            "diagnose": voorstel.diagnose.als_dict(),
            "candidate_text": voorstel.candidate_text,
            "rationale": voorstel.rationale,
            "behouden": list(voorstel.behouden),
            "onzekerheid": voorstel.onzekerheid,
            "error": voorstel.error,
            "recorded": bool(vastgelegd),
            "message": (
                "Voorstel beschikbaar; de oorspronkelijke tekst is ongewijzigd."
                if voorstel.status == "proposed"
                else voorstel.rationale
                or (voorstel.error or {}).get("message")
                or voorstel.status
            ),
        }

    def _async_validate_text(self) -> Any | None:
        """De async `validate_text` van de geïnjecteerde validatiedienst, of None."""
        vs = self.validation_service
        if vs is None:
            return None
        fn = getattr(vs, "validate_text", None)
        if fn is None:
            fn = getattr(getattr(vs, "validation_service", None), "validate_text", None)
        return fn

    @staticmethod
    def _beoordelingsfout(v: Mapping[str, Any]) -> str | None:
        """Ontbrekende of niet-uitgevoerde bronbeoordeling in de hertoetsing."""
        beoordeling = v.get("source_assessment")
        if not isinstance(beoordeling, Mapping):
            return "geen bronbeoordeling in het hertoetsingsresultaat"
        if beoordeling.get("status") != "assessed":
            return (
                f"bronbeoordeling niet uitgevoerd (status {beoordeling.get('status')})"
            )
        return None

    @classmethod
    def _technische_fout_in_validatie(cls, v: Mapping[str, Any]) -> str | None:
        """Reden waarom een hertoetsing niet als bewijs kan dienen, of None.

        DEF-624: alleen een expliciete `validated` is een uitgevoerde run;
        een afwezige, null of ongeldige status is geen runbewijs.
        """
        from services.validation.interfaces import UNKNOWN_REASON_RULESET_INCOMPLETE
        from services.validation.result_contract import bepaal_runstatus

        runstatus = bepaal_runstatus(v)
        if not runstatus.uitgevoerd:
            if runstatus.reason == UNKNOWN_REASON_RULESET_INCOMPLETE:
                return "validatie niet te bepalen (regelset onvolledig)"
            return (
                "validatie niet te bepalen (geen geldig runbewijs: "
                f"validation_status {runstatus.reason or 'onbekend'})"
            )
        if _als_mapping(v.get("system")).get("degraded_mode"):
            return "validatie draaide in beperkte modus"
        if _als_mapping(v.get("rule_statuses")).get("CON-02") == "error":
            return "bronbeoordeling technisch mislukt (CON-02: error)"
        beoordelingsfout = cls._beoordelingsfout(v)
        if beoordelingsfout is not None:
            return beoordelingsfout
        dekking = v.get("evaluation_coverage")
        if isinstance(dekking, Mapping) and int(dekking.get("error") or 0):
            return f"{dekking.get('error')} regel(s) met technische fout"
        return None

    @staticmethod
    def _toepasbare_kandidaat(
        record: DefinitieRecord, proposal_id: str
    ) -> str | dict[str, Any]:
        """De kandidaattekst van een toepasbaar voorstel, of de weigering.

        Vaste volgorde: voorstel bestaat → status `proposed` → origineel is
        nog de opgeslagen tekst (anders `stale_original`) → kandidaattekst.
        """
        voorstel = record.get_source_proposal(proposal_id)
        if not isinstance(voorstel, dict):
            return {"status": "not_found", "message": "Voorstel niet gevonden."}
        if voorstel.get("status") != "proposed":
            return {
                "status": "invalid_status",
                "message": f"Voorstel heeft status '{voorstel.get('status')}' en is niet toepasbaar.",
            }
        origineel = _als_dict(voorstel.get("original"))
        if origineel.get("text") != record.get_definitie_tekst():
            return {
                "status": "stale_original",
                "message": "De definitietekst is gewijzigd sinds het voorstel; het voorstel "
                "is verouderd.",
            }
        uitkomst = _als_dict(voorstel.get("outcome"))
        kandidaat = str(uitkomst.get("candidate_text") or "").strip()
        if not kandidaat:
            return {
                "status": "invalid_status",
                "message": "Voorstel bevat geen kandidaattekst.",
            }
        return kandidaat

    async def _hertoets_kandidaat(
        self, definitie_id: int, record: DefinitieRecord, kandidaat: str
    ) -> Mapping[str, Any] | _Weigering:
        """Hertoets de kandidaat met DEZELFDE bronset via de async
        `validate_text`. Geeft het volledige validatieresultaat, of een
        `technical_error`-weigering wanneer de hertoetsing niet als bewijs kan
        dienen (het origineel blijft dan intact)."""
        import inspect

        from services.validation.interfaces import ValidationContext

        # De geïnjecteerde dienst is in productie de DefinitionOrchestratorV2
        # (met `.validation_service` = ValidationOrchestratorV2) of direct de
        # validatie-orchestrator; beide leveren de async `validate_text`.
        fn = self._async_validate_text()
        if fn is None or not inspect.iscoroutinefunction(fn):
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": "Geen asynchrone validatiedienst beschikbaar voor hertoetsing.",
                }
            )
        geladen = self.repository.get(definitie_id)
        geladen_meta = dict(getattr(geladen, "metadata", None) or {})
        contexten = record.get_contextlijsten()
        kandidaat_def = Definition(
            id=definitie_id,
            begrip=record.begrip or "",
            definitie=kandidaat,
            organisatorische_context=list(
                contexten.get("organisatorische_context") or []
            ),
            juridische_context=list(contexten.get("juridische_context") or []),
            wettelijke_basis=list(contexten.get("wettelijke_basis") or []),
            categorie=record.categorie,
        )
        vc = ValidationContext(
            correlation_id=None,
            metadata=bouw_validatiecontext(kandidaat_def, geladen_meta),
        )
        try:
            v = await fn(
                begrip=kandidaat_def.begrip,
                text=kandidaat,
                ontologische_categorie=record.categorie,
                context=vc,
            )
        except Exception as e:
            logger.error("Hertoetsing van voorstel mislukt: %s", e, exc_info=True)
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": f"Hertoetsing mislukt: {type(e).__name__}: {e}",
                }
            )
        if not isinstance(v, Mapping):
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": "Hertoetsing gaf geen resultaat.",
                }
            )
        fout = self._technische_fout_in_validatie(v)
        if fout:
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": f"Hertoetsing niet bruikbaar als bewijs: {fout}. "
                    "De oorspronkelijke tekst blijft staan.",
                    "validation": dict(v),
                }
            )
        return v

    async def pas_voorstel_toe(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        actor: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Neem een opgeslagen voorstel over: hertoets mét dezelfde bronset,
        daarna atomair opslaan bij D tegen de getoonde versie.

        Een verouderd of vervalst voorstel wordt geweigerd; een technische
        fout in de hertoetsing laat het origineel intact (het voorstel blijft
        `proposed`, de reden wordt gemeld). Nooit een oude pass behouden: D
        slaat de nieuwe volledige validatie en bronbeoordeling op.
        """
        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        kandidaat = self._toepasbare_kandidaat(record, proposal_id)
        if isinstance(kandidaat, dict):
            return kandidaat
        hertoetsing = await self._hertoets_kandidaat(definitie_id, record, kandidaat)
        if isinstance(hertoetsing, _Weigering):
            return hertoetsing.payload
        v = hertoetsing
        toepassing = self.repository.apply_source_proposal(
            definitie_id,
            proposal_id,
            updated_by=actor,
            expected_version=record.version_number,
            source_assessment=dict(v["source_assessment"]),
            validation=dict(v),
        )
        self._clear_cache(definitie_id)
        return {
            "status": toepassing.status,
            "version_number": getattr(toepassing, "version_number", None),
            "message": getattr(toepassing, "reason", None)
            or (
                "Voorstel toegepast en opnieuw getoetst."
                if toepassing.status == "applied"
                else toepassing.status
            ),
            "validation": dict(v),
            "candidate_text": kandidaat,
        }

    def wijs_voorstel_af(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        actor: str,
        note: str | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Wijs een voorstel expliciet af (status bewaard als bewijs)."""
        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        ok = self.repository.set_source_proposal_status(
            definitie_id,
            proposal_id,
            "rejected",
            actor,
            expected_version=record.version_number,
            note=note,
        )
        self._clear_cache(definitie_id)
        return {
            "status": "rejected" if ok else "version_conflict",
            "message": (
                "Voorstel afgewezen."
                if ok
                else "Afwijzen niet vastgelegd: versie gewijzigd of voorstel niet toepasbaar."
            ),
        }

    def _generate_session_id(self, definitie_id: int, user: str) -> str:
        """Generate unique session ID."""
        import hashlib

        timestamp = datetime.now().isoformat()
        data = f"{definitie_id}_{user}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()

    def _format_timestamp(self, timestamp: str | datetime | Any) -> str:
        """Format timestamp for display."""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return str(timestamp)

        if isinstance(timestamp, datetime):
            delta = datetime.now() - timestamp
            if delta.days > 7:
                return timestamp.strftime("%d-%m-%Y %H:%M")
            if delta.days > 0:
                return f"{delta.days} dagen geleden"
            if delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} uur geleden"
            if delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minuten geleden"
            return "Zojuist"

        return str(timestamp)

    def _generate_change_summary(self, entry: dict[str, Any]) -> str:
        """Generate human-readable change summary."""
        wijziging_type = entry.get("wijziging_type", "")
        gewijzigd_door = entry.get("gewijzigd_door", "Onbekend")

        summaries = {
            "created": f"Aangemaakt door {gewijzigd_door}",
            "updated": f"Bewerkt door {gewijzigd_door}",
            "status_changed": f"Status gewijzigd door {gewijzigd_door}",
            "approved": f"Goedgekeurd door {gewijzigd_door}",
            "archived": f"Gearchiveerd door {gewijzigd_door}",
            "auto_save": "Auto-save",
        }

        return summaries.get(wijziging_type, f"Gewijzigd door {gewijzigd_door}")

    def _definition_to_dict(self, definition: Definition) -> dict[str, Any]:
        """Convert Definition to dictionary."""
        return {
            "begrip": definition.begrip,
            "definitie": definition.definitie,
            "toelichting": definition.toelichting,
            "bron": definition.bron,
            "organisatorische_context": getattr(
                definition, "organisatorische_context", []
            ),
            "juridische_context": getattr(definition, "juridische_context", []),
            "wettelijke_basis": getattr(definition, "wettelijke_basis", []),
            "categorie": definition.categorie,
            **(definition.metadata if definition.metadata else {}),
        }

    def _clear_cache(self, definitie_id: int | None = None) -> None:
        """Clear cache entries."""
        if definitie_id:
            # Clear specific definition cache
            keys_to_remove = [k for k in self._cache if str(definitie_id) in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear all cache
            self._cache.clear()
