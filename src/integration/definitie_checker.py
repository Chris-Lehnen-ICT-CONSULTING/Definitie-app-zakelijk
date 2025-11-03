"""
DefinitieChecker - Integreert duplicate detection met DefinitieAgent.
Voorkomt dubbele generatie door bestaande definities te checken.

Deze module controleert of een definitie al bestaat voordat een nieuwe
wordt gegenereerd, om duplicaten te voorkomen.
"""

import json  # JSON verwerking voor metadata
import logging  # Logging faciliteiten voor debug en monitoring
from dataclasses import dataclass  # Dataklassen voor gestructureerde data
from datetime import UTC, datetime
from enum import Enum  # Enumeraties voor actie types
from typing import Any  # Type hints voor betere code documentatie

# Database en core component imports
from database.definitie_repository import SourceType  # Data modellen en enums
from database.definitie_repository import (
    get_definitie_repository,  # Repository toegang en factory
)
from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
    DuplicateMatch,
)
from domain.ontological_categories import OntologischeCategorie  # Generatie componenten

# Integrated service imports verplaatst naar functie niveau om circulaire imports te voorkomen

logger = logging.getLogger(__name__)  # Logger instantie voor integratie module


class CheckAction(Enum):
    """Actie die ondernomen moet worden na duplicate check."""

    PROCEED = "proceed"  # Ga door met generatie
    USE_EXISTING = "use_existing"  # Gebruik bestaande definitie
    UPDATE_EXISTING = "update"  # Update bestaande definitie
    USER_CHOICE = "user_choice"  # Laat gebruiker kiezen


@dataclass
class DefinitieCheckResult:
    """Resultaat van duplicate check."""

    action: CheckAction
    existing_definitie: DefinitieRecord | None = None
    duplicates: list[DuplicateMatch] = None
    message: str = ""
    confidence: float = 0.0

    def __post_init__(self):  # Post-initialisatie voor default lijst
        if self.duplicates is None:  # Controleer of duplicates lijst bestaat
            self.duplicates = []  # Initialiseer lege lijst als deze niet bestaat


class DefinitieChecker:
    """
    Integreert duplicate detection met definitie generatie workflow.
    Checkt bestaande definities voordat nieuwe worden gegenereerd.
    """

    def __init__(self, repository: DefinitieRepository = None):
        """
        Initialiseer checker met repository.

        Args:
            repository: DefinitieRepository instance, gebruikt default als None
        """
        self.repository = repository or get_definitie_repository()

        # Lazy load integrated service to avoid circular import
        self.integrated_service = None
        self._service_config = {
            "mode": "AUTO",
            "enable_monitoring": True,
            "enable_validation": True,
        }

    def _get_integrated_service(self):
        """Lazy load service adapter (V2) to avoid circular imports.

        Vervangt de niet-bestaande services.integrated_service door de
        ServiceAdapter uit services.service_factory, die de V2 orchestrator
        en services gebruikt met een legacy-compatibele interface.
        """
        if self.integrated_service is None:
            from services.service_factory import get_definition_service

            # Gebruik standaard containerconfig; toggles zitten in de container
            self.integrated_service = get_definition_service()
        return self.integrated_service

    def check_before_generation(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
        wettelijke_basis: list[str] | None = None,
    ) -> DefinitieCheckResult:
        """
        Check voor bestaande definities voordat generatie start.

        Args:
            begrip: Het begrip om te checken
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            categorie: Ontologische categorie

        Returns:
            DefinitieCheckResult met aanbevolen actie
        """
        logger.info(
            f"Checking for existing definitions of '{begrip}' in context {organisatorische_context}"
        )

        # Zoek exact match - inclusief categorie voor category-aware duplicate detection
        existing = self.repository.find_definitie(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            categorie=(
                categorie.value if categorie else None
            ),  # Categorie is onderdeel van unieke key
            wettelijke_basis=wettelijke_basis,
        )
        # Extra filtering: vereis ook match op wettelijke_basis (lijst, order-onafhankelijk)
        if existing:
            try:

                def _norm(lst: list[str] | None) -> tuple[str, ...]:
                    return tuple(sorted([str(x).strip().lower() for x in (lst or [])]))

                if _norm(existing.get_wettelijke_basis_list()) != _norm(
                    wettelijke_basis or []
                ):
                    existing = None
            except Exception:
                # Als er iets misgaat met parsing, behandel als geen exacte match
                pass
        if existing:
            return self._handle_exact_match(existing, search_term=begrip)

        # Zoek duplicates/fuzzy matches - inclusief categorie
        duplicates = self.repository.find_duplicates(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            categorie=(
                categorie.value if categorie else None
            ),  # Categorie is onderdeel van unieke key
            wettelijke_basis=wettelijke_basis,
        )
        # Extra filtering op wettelijke_basis
        if duplicates:
            try:

                def _norm(lst: list[str] | None) -> tuple[str, ...]:
                    return tuple(sorted([str(x).strip().lower() for x in (lst or [])]))

                wb_norm = _norm(wettelijke_basis or [])
                duplicates = [
                    d
                    for d in duplicates
                    if hasattr(d.definitie_record, "get_wettelijke_basis_list")
                    and _norm(d.definitie_record.get_wettelijke_basis_list()) == wb_norm
                ]
            except Exception:
                # Fallback: laat duplicates ongewijzigd
                pass
        if duplicates:
            return self._handle_duplicates(duplicates)

        # Geen duplicates gevonden - ga door met generatie
        return DefinitieCheckResult(
            action=CheckAction.PROCEED,
            message=f"Geen bestaande definitie gevonden voor '{begrip}'. Generatie kan doorgaan.",
            confidence=1.0,
        )

    def generate_with_check(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        wettelijke_basis: list[str] | None = None,
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
        force_generate: bool = False,
        created_by: str | None = None,
        # Hybrid context parameters
        selected_document_ids: list[str] | None = None,
        enable_hybrid: bool = False,
    ) -> tuple[DefinitieCheckResult, Any | None, DefinitieRecord | None]:
        """
        V2-route: voer complete workflow uit via ServiceAdapter (geen legacy agent).
        Ondersteunt hybrid context parameters (doorgegeven indien ondersteund).

        Args:
            begrip: Het begrip om te definiëren
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            categorie: Ontologische categorie
            force_generate: Forceer nieuwe generatie ondanks duplicates
            created_by: Wie de definitie aanmaakt
            selected_document_ids: IDs van documenten voor hybrid context
            enable_hybrid: Of hybrid context enhancement gebruikt moet worden

        Returns:
            Tuple van (check_result, agent_result, saved_record)
        """
        # Stap 1: Check voor duplicates
        check_result = self.check_before_generation(
            begrip,
            organisatorische_context,
            juridische_context,
            categorie,
            wettelijke_basis,
        )

        # Stap 2: Bepaal actie
        if not force_generate and check_result.action != CheckAction.PROCEED:
            # Return bestaande definitie zonder nieuwe generatie
            return check_result, None, check_result.existing_definitie

        # Stap 3: Genereer via geïntegreerde V2 service (sync wrapper)
        logger.info(
            f"Generating new definition for '{begrip}' via V2 service (context: {organisatorische_context})"
        )
        try:
            import asyncio

            adapter = self._get_integrated_service()
            context_dict = {
                "organisatorisch": (
                    [organisatorische_context] if organisatorische_context else []
                ),
                "juridisch": [juridische_context] if juridische_context else [],
                "wettelijk": [],
            }

            extra_kwargs: dict[str, Any] = {"organisatie": organisatorische_context}
            # categorie kan een enum of string zijn
            extra_kwargs["categorie"] = (
                categorie.value if hasattr(categorie, "value") else str(categorie)
            )
            if selected_document_ids is not None:
                extra_kwargs["selected_document_ids"] = selected_document_ids
            if enable_hybrid:
                extra_kwargs["enable_hybrid"] = enable_hybrid

            async def _task():
                return await adapter.generate_definition(
                    begrip, context_dict, **extra_kwargs
                )

            integrated_result = asyncio.run(asyncio.wait_for(_task(), timeout=120))

            if isinstance(integrated_result, dict) and integrated_result.get("success"):
                definitie_text = (
                    integrated_result.get("definitie_gecorrigeerd")
                    or integrated_result.get("definitie_origineel")
                    or ""
                )
                final_score = integrated_result.get("final_score")

                saved_record = self._save_generated_definition_v2(
                    begrip=begrip,
                    definitie_text=definitie_text,
                    categorie=(
                        categorie
                        if isinstance(categorie, OntologischeCategorie)
                        else OntologischeCategorie(str(categorie))
                    ),
                    organisatorische_context=organisatorische_context,
                    juridische_context=juridische_context,
                    final_score=(
                        float(final_score) if final_score is not None else None
                    ),
                    created_by=created_by,
                    source_reference="IntegratedService_V2",
                )
                return check_result, integrated_result, saved_record

            # Mislukking of onverwacht type: log en return
            msg = (
                integrated_result.get("error_message")
                if isinstance(integrated_result, dict)
                else f"Unexpected result type: {type(integrated_result).__name__}"
            )
            logger.warning(f"Failed to generate definition for '{begrip}': {msg}")
            return check_result, integrated_result, None
        except Exception as e:
            logger.error(f"V2 generation error for '{begrip}': {e!s}")
            return check_result, {"success": False, "error_message": str(e)}, None

    def update_existing_definition(
        self, definitie_id: int, updated_by: str | None = None, regenerate: bool = False
    ) -> tuple[bool, Any | None]:
        """
        Update bestaande definitie, optioneel met regeneratie.

        Args:
            definitie_id: ID van definitie om te updaten
            updated_by: Wie de update uitvoert
            regenerate: Of definitie opnieuw gegenereerd moet worden

        Returns:
            Tuple van (success, agent_result)
        """
        existing = self.repository.get_definitie(definitie_id)
        if not existing:
            return False, None

        if not regenerate:
            # Simple metadata update
            success = self.repository.update_definitie(
                definitie_id, {"updated_by": updated_by}, updated_by
            )
            return success, None

        # Regenerate definitie via V2 service
        import asyncio

        categorie = OntologischeCategorie(existing.categorie)
        adapter = self._get_integrated_service()

        def _to_list(val):
            try:
                if not val:
                    return []
                if isinstance(val, str):
                    v = val.strip()
                    if v.startswith("["):
                        import json as _json

                        return list(_json.loads(v))
                    return [val]
                if isinstance(val, list):
                    return val
            except Exception:
                return []
            return []

        context_dict = {
            "organisatorisch": _to_list(
                getattr(existing, "organisatorische_context", None)
            ),
            "juridisch": _to_list(getattr(existing, "juridische_context", None)),
            "wettelijk": [],
        }

        async def _task2():
            return await adapter.generate_definition(
                begrip=existing.begrip,
                context_dict=context_dict,
                categorie=categorie.value,
                organisatie=(
                    context_dict["organisatorisch"][0]
                    if context_dict["organisatorisch"]
                    else ""
                ),
            )

        integrated_result = asyncio.run(asyncio.wait_for(_task2(), timeout=120))

        if isinstance(integrated_result, dict) and integrated_result.get("success"):
            definitie_text = (
                integrated_result.get("definitie_gecorrigeerd")
                or integrated_result.get("definitie_origineel")
                or ""
            )
            final_score = integrated_result.get("final_score") or 0.0
            updates = {
                "definitie": definitie_text,
                "validation_score": float(final_score),
                "version_number": (
                    existing.version_number + 1
                    if getattr(existing, "version_number", None)
                    else 1
                ),
                "previous_version_id": definitie_id,
            }
            success = self.repository.update_definitie(
                definitie_id, updates, updated_by
            )
            return success, integrated_result

        return False, integrated_result

    def approve_definition(
        self, definitie_id: int, approved_by: str, notes: str | None = None
    ) -> bool:
        """
        Keur definitie goed (zet status op ESTABLISHED).

        Args:
            definitie_id: ID van definitie
            approved_by: Wie de definitie goedkeurt
            notes: Optionele goedkeuringsnotities

        Returns:
            True als succesvol goedgekeurd
        """
        return self.repository.change_status(
            definitie_id, DefinitieStatus.ESTABLISHED, approved_by, notes
        )

    def get_pending_definitions(self) -> list[DefinitieRecord]:
        """Haal definities op die wachten op goedkeuring."""
        return self.repository.search_definities(status=DefinitieStatus.REVIEW)

    def get_established_definitions(
        self, organisatorische_context: str | None = None
    ) -> list[DefinitieRecord]:
        """Haal vastgestelde definities op."""
        return self.repository.search_definities(
            status=DefinitieStatus.ESTABLISHED,
            organisatorische_context=organisatorische_context,
        )

    def export_established_definitions(
        self, file_path: str, organisatorische_context: str | None = None
    ) -> int:
        """
        Exporteer vastgestelde definities naar bestand.

        Args:
            file_path: Pad voor export bestand
            organisatorische_context: Optionele filter op organisatie

        Returns:
            Aantal geëxporteerde definities
        """
        filters = {"status": DefinitieStatus.ESTABLISHED}
        if organisatorische_context:
            filters["organisatorische_context"] = organisatorische_context

        return self.repository.export_to_json(file_path, filters)

    def import_external_definitions(
        self, file_path: str, import_by: str | None = None
    ) -> tuple[int, int, list[str]]:
        """
        Importeer definities uit extern bestand.

        Args:
            file_path: Pad naar import bestand
            import_by: Wie de import uitvoert

        Returns:
            Tuple van (succesvol, gefaald, errors)
        """
        return self.repository.import_from_json(file_path, import_by)

    def _handle_exact_match(
        self, existing: DefinitieRecord, search_term: str | None = None
    ) -> DefinitieCheckResult:
        """Behandel exact match scenario."""
        # Bepaal of de hit via synoniem tot stand kwam (i.p.v. exact begrip)
        via_synoniem = False
        try:
            if search_term and search_term.strip():
                via_synoniem = (
                    search_term.strip().lower()
                    != (existing.begrip or "").strip().lower()
                )
        except Exception:
            via_synoniem = False

        # Bouw een iets rijkere uitleg
        def _msg(prefix: str) -> str:
            if via_synoniem and search_term:
                return (
                    f"{prefix} voor '{existing.begrip}' (ID: {existing.id}). "
                    f"Gevonden via synoniem ‘{search_term}’ met gelijke context."
                )
            return f"{prefix} voor '{existing.begrip}' (ID: {existing.id})"

        if existing.status == DefinitieStatus.ESTABLISHED.value:
            return DefinitieCheckResult(
                action=CheckAction.USE_EXISTING,
                existing_definitie=existing,
                message=_msg("Vastgestelde definitie bestaat al"),
                confidence=1.0,
            )
        if existing.status == DefinitieStatus.DRAFT.value:
            return DefinitieCheckResult(
                action=CheckAction.UPDATE_EXISTING,
                existing_definitie=existing,
                message=_msg("Draft definitie bestaat") + ". Overweeg update.",
                confidence=1.0,
            )
        return DefinitieCheckResult(
            action=CheckAction.USER_CHOICE,
            existing_definitie=existing,
            message=_msg(f"Definitie in status '{existing.status}' bestaat"),
            confidence=0.8,
        )

    def _handle_duplicates(
        self, duplicates: list[DuplicateMatch]
    ) -> DefinitieCheckResult:
        """Behandel fuzzy duplicates scenario."""
        best_match = duplicates[0]  # Highest score first

        if best_match.match_score > 0.9:
            return DefinitieCheckResult(
                action=CheckAction.USER_CHOICE,
                existing_definitie=best_match.definitie_record,
                duplicates=duplicates,
                message=f"Zeer vergelijkbare definitie gevonden: '{best_match.definitie_record.begrip}' (score: {best_match.match_score:.2f})",
                confidence=best_match.match_score,
            )
        if best_match.match_score > 0.7:
            return DefinitieCheckResult(
                action=CheckAction.USER_CHOICE,
                duplicates=duplicates,
                message=f"Mogelijke duplicaten gevonden (beste match: {best_match.match_score:.2f})",
                confidence=best_match.match_score,
            )
        return DefinitieCheckResult(
            action=CheckAction.PROCEED,
            duplicates=duplicates,
            message="Zwakke overeenkomsten gevonden, maar generatie kan doorgaan",
            confidence=1.0 - best_match.match_score,
        )

    def _save_generated_definition_v2(
        self,
        *,
        begrip: str,
        definitie_text: str,
        categorie: OntologischeCategorie,
        organisatorische_context: str,
        juridische_context: str,
        final_score: float | None,
        created_by: str | None = None,
        source_reference: str = "IntegratedService_V2",
    ) -> DefinitieRecord:
        """Sla een via V2 service gegenereerde definitie op in database."""
        record = DefinitieRecord(
            begrip=begrip,
            definitie=definitie_text,
            categorie=categorie.value,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            status=DefinitieStatus.REVIEW.value,  # Start in review
            validation_score=final_score,
            source_type=SourceType.GENERATED.value,
            source_reference=source_reference,
            created_by=created_by or "integrated_service",
            datum_voorstel=datetime.now(UTC),
            ketenpartners=json.dumps([]),
        )
        record_id = self.repository.create_definitie(record)
        record.id = record_id
        logger.info(f"Saved generated definition {record_id} for '{begrip}'")
        return record


# Convenience functions
def check_existing_definition(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: str = "type",
) -> DefinitieCheckResult:
    """
    Convenience functie voor snelle duplicate check.

    Args:
        begrip: Het begrip om te checken
        organisatorische_context: Organisatorische context
        juridische_context: Juridische context
        categorie: Ontologische categorie string

    Returns:
        DefinitieCheckResult
    """
    checker = DefinitieChecker()
    cat_enum = OntologischeCategorie(categorie)

    return checker.check_before_generation(
        begrip, organisatorische_context, juridische_context, cat_enum
    )


def generate_or_retrieve_definition(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: str = "type",
    force_new: bool = False,
    created_by: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Convenience functie voor complete workflow: check + genereer + opslag.

    Args:
        begrip: Het begrip
        organisatorische_context: Organisatorische context
        juridische_context: Juridische context
        categorie: Ontologische categorie string
        force_new: Forceer nieuwe generatie
        created_by: Wie de definitie aanmaakt

    Returns:
        Tuple van (definitie_text, metadata_dict)
    """
    checker = DefinitieChecker()
    cat_enum = OntologischeCategorie(categorie)

    check_result, agent_result, saved_record = checker.generate_with_check(
        begrip=begrip,
        organisatorische_context=organisatorische_context,
        juridische_context=juridische_context,
        wettelijke_basis=[],
        categorie=cat_enum,
        force_generate=force_new,
        created_by=created_by,
    )

    if saved_record:
        return saved_record.definitie, {
            "id": saved_record.id,
            "status": saved_record.status,
            "validation_score": saved_record.validation_score,
            "source": "generated",
            "check_action": check_result.action.value,
        }
    if check_result.existing_definitie:
        return check_result.existing_definitie.definitie, {
            "id": check_result.existing_definitie.id,
            "status": check_result.existing_definitie.status,
            "validation_score": check_result.existing_definitie.validation_score,
            "source": "existing",
            "check_action": check_result.action.value,
        }
    # Failure path
    error_msg = None
    if isinstance(agent_result, dict):
        error_msg = agent_result.get("error_message") or agent_result.get("message")
    else:
        # Backward fallback if non-dict is ever returned
        error_msg = getattr(agent_result, "reason", None)
    return "Definitie kon niet worden gegenereerd", {
        "source": "failed",
        "check_action": check_result.action.value,
        "error": error_msg or "Unknown error",
    }

    async def generate_with_integrated_service(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
        force_generate: bool = False,
        created_by: str | None = None,
    ) -> tuple[DefinitieCheckResult, Any | None, DefinitieRecord | None]:
        """
        Generate definition using integrated service layer.
        Provides modern service architecture with legacy fallback.

        Args:
            begrip: Term to define
            organisatorische_context: Organizational context
            juridische_context: Legal context
            categorie: Ontological category
            force_generate: Skip duplicate check
            created_by: Creator identifier

        Returns:
            Tuple of (check_result, integrated_result, saved_record)
        """
        logger.info(
            f"Generating definition with integrated service: '{begrip}' in {organisatorische_context}"
        )

        # Step 1: Check for duplicates (unless forced)
        check_result = self.check_before_generation(
            begrip, organisatorische_context, juridische_context, categorie
        )

        if not force_generate and check_result.action != CheckAction.PROCEED:
            # Return existing without new generation
            return check_result, None, check_result.existing_definitie

        # Step 2: Prepare context for integrated service
        context = {
            "organisatorische_context": (
                [organisatorische_context] if organisatorische_context else []
            ),
            "juridische_context": [juridische_context] if juridische_context else [],
            "categorie": categorie.value,
        }

        # Step 3: Generate using integrated service (async API, V2 dict response)
        try:
            # ServiceAdapter.generate_definition is async and returns a V2 UIResponse-like dict
            integrated_result = (
                await self._get_integrated_service().generate_definition(
                    begrip, context
                )
            )

            # Expect a dict: { success: bool, definitie_gecorrigeerd: str, final_score: float, ... }
            if isinstance(integrated_result, dict) and integrated_result.get("success"):
                definitie_text = (
                    integrated_result.get("definitie_gecorrigeerd")
                    or integrated_result.get("definitie_origineel")
                    or ""
                )

                # Derive validation score from canonical fields
                final_score = integrated_result.get("final_score")
                if final_score is None:
                    vd = integrated_result.get("validation_details") or {}
                    final_score = vd.get("overall_score")

                record = DefinitieRecord(
                    begrip=begrip,
                    definitie=definitie_text,
                    categorie=categorie.value,
                    organisatorische_context=organisatorische_context,
                    juridische_context=juridische_context,
                    status=DefinitieStatus.REVIEW.value,
                    validation_score=(
                        float(final_score) if final_score is not None else None
                    ),
                    source_type=SourceType.GENERATED.value,
                    source_reference="IntegratedService_V2",
                    created_by=created_by or "integrated_service",
                )

                saved_id = self.repository.create_definitie(record)
                if saved_id:
                    saved_record = self.repository.get_definitie(saved_id)
                    logger.info(
                        f"Successfully saved definition for '{begrip}' with ID {saved_id}"
                    )
                    return check_result, integrated_result, saved_record
                logger.error(f"Failed to save definition for '{begrip}' to database")
                return check_result, integrated_result, None

            # Non-success result: return as-is for caller to inspect
            if isinstance(integrated_result, dict):
                logger.warning(
                    f"Integrated service failed for '{begrip}': "
                    f"{integrated_result.get('error_message') or integrated_result.get('message') or 'unknown error'}"
                )
            else:
                logger.warning(
                    f"Integrated service returned unexpected result type for '{begrip}': {type(integrated_result).__name__}"
                )
            return check_result, integrated_result, None

        except Exception as e:
            logger.error(f"Integrated service error for '{begrip}': {e!s}")
            # Create error result
            # Minimal error dict voor compatibiliteit
            error_result = {
                "success": False,
                "operation": "generate_definition",
                "processing_time": 0.0,
                "error_message": str(e),
            }
            return check_result, error_result, None

    async def validate_with_integrated_service(
        self, definitie: str, categorie: str, context: dict[str, Any] | None = None
    ):
        """
        Validate definition using integrated service layer.

        Args:
            definitie: Definition to validate
            categorie: Ontological category
            context: Optional context

        Returns:
            IntegratedResult with validation results
        """
        try:
            # Gebruik ValidationOrchestratorV2 via container
            from services.container import get_container
            from services.validation.interfaces import ValidationContext

            container = get_container()
            orchestrator = container.orchestrator()
            validation_orch = getattr(orchestrator, "validation_service", None)
            if validation_orch is None:
                msg = "Validation orchestrator not available"
                raise RuntimeError(msg)

            vctx = None
            if context:
                vctx = ValidationContext()
            return await validation_orch.validate_text(
                begrip="",
                text=definitie,
                ontologische_categorie=categorie,
                context=vctx,
            )
        except Exception as e:
            logger.error(f"Integrated validation error: {e!s}")
            return {
                "success": False,
                "operation": "validate_definition",
                "processing_time": 0.0,
                "error_message": str(e),
            }

    async def check_duplicates_with_integrated_service(
        self, begrip: str, definitie: str, threshold: float = 0.8
    ):
        """
        Check duplicates using integrated service layer.

        Args:
            begrip: Term to check
            definitie: Definition to check
            threshold: Similarity threshold

        Returns:
            IntegratedResult with duplicate analysis
        """
        try:
            # Gebruik repository + duplicate service
            from services.container import get_container

            container = get_container()
            repo = container.repository()
            # Simpele duplicate analyse: vind records met zelfde begrip/context
            # Hier gebruiken we alleen de tekst niet; threshold wordt genegeerd in fallback
            dups = repo.find_duplicates(
                DefinitieRecord(
                    begrip=begrip, definitie=definitie, organisatorische_context=""
                )
            )
            return {
                "success": True,
                "operation": "check_duplicates",
                "processing_time": 0.0,
                "matches": [
                    {
                        "id": m.definitie_record.id,
                        "begrip": m.definitie_record.begrip,
                        "score": m.match_score,
                    }
                    for m in dups
                ],
            }
        except Exception as e:
            logger.error(f"Integrated duplicate check error: {e!s}")
            return {
                "success": False,
                "operation": "check_duplicates",
                "processing_time": 0.0,
                "error_message": str(e),
            }

    def get_service_info(self) -> dict[str, Any]:
        """Get information about available services."""
        return self._get_integrated_service().get_service_info()

    return None
