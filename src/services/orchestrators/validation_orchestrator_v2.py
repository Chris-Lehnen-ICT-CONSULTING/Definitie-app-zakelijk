"""ValidationOrchestratorV2 — sequentiële orchestrator voor validatie.

Deze orchestrator levert een dunne, async-first laag bovenop de
`ValidationServiceInterface`, met optionele pre-cleaning. Batchverwerking
gebeurt sequentieel; parallelisme volgt in een latere iteratie.
"""

from __future__ import annotations

import copy
import logging
import uuid
from collections.abc import Iterable
from typing import Any

from domain.context.normalisatie import canoniseer_contextlijst
from services.interfaces import (
    CleaningServiceInterface,
    Definition,
    ValidationServiceInterface,
)
from services.validation.interfaces import (
    ValidationContext,
    ValidationOrchestratorInterface,
    ValidationRequest,
    ValidationResult,
)
from services.validation.mappers import create_degraded_result, ensure_schema_compliance

logger = logging.getLogger(__name__)


class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    """Orchestrator voor validatie (V2).

    Afhankelijkheden worden via de constructor geïnjecteerd. De orchestrator
    zelf bevat geen businessregels; die leven in de onderliggende service/validator.

    Story 2.2: Core Implementation
    - Concrete implementatie van ValidationOrchestratorInterface
    - Dunne orchestration laag bovenop bestaande services
    - Sequentiële batch processing (parallelisme in latere story)
    - Optionele pre-cleaning support
    """

    def __init__(
        self,
        validation_service: ValidationServiceInterface,
        cleaning_service: CleaningServiceInterface | None = None,
    ) -> None:
        if validation_service is None:
            msg = "validation_service is vereist"
            raise ValueError(msg)
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service

    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer losse tekst met optionele pre-cleaning.

        Args:
            begrip: Het begrip waarvoor de tekst wordt gevalideerd
            text: Te valideren tekst (mag leeg zijn)
            ontologische_categorie: Optionele categorie voor contextuele regels
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat
        """
        # Extract correlation ID from context
        correlation_id = (
            str(context.correlation_id)
            if context and context.correlation_id
            else str(uuid.uuid4())
        )

        # DEF-198: Clean architecture - import from utils/, callback registered by UI
        from utils.progress_callback import operation_progress

        with operation_progress("validating_definition"):
            try:
                cleaned_text = text
                if self.cleaning_service is not None:
                    cleaning = await self.cleaning_service.clean_text(text, begrip)
                    cleaned_text = cleaning.cleaned_text if cleaning else text

                # Geen verrijking met 'definition' hier: die is in validate_text
                # niet beschikbaar. Context (incl. de drie lijsten) komt via
                # ValidationContext.metadata.
                # DEF-622: CON-01 bindt bewijs en beoordeling aan de exacte
                # invoertekst — onvoorwaardelijk uit het `text`-argument, ook
                # zonder cleaning en ongeacht wat een aanroeper in metadata
                # onder `record_text` meegeeft. Anders kon een aanroeper de
                # binding spoofen en een oude beoordeling laten gelden voor
                # een nieuwe tekst (reviewbevinding R3).
                context_dict = dict(self._context_dict(context) or {})
                context_dict["record_text"] = text

                # Call underlying service
                result = await self.validation_service.validate_definition(
                    begrip=begrip,
                    text=cleaned_text,
                    ontologische_categorie=ontologische_categorie,
                    context=context_dict,
                )

                # Ensure result is schema-compliant
                return ensure_schema_compliance(result, correlation_id)

            except Exception as e:
                logger.error(
                    f"Validation failed for begrip='{begrip}', correlation_id='{correlation_id}': {e}"
                )
                return create_degraded_result(
                    error=str(e), correlation_id=correlation_id, begrip=begrip
                )

    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer een volledig Definition-object met optionele pre-cleaning.

        Args:
            definition: Te valideren Definition object
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat met detailed_scores
        """
        # Extract correlation ID from context
        correlation_id = (
            str(context.correlation_id)
            if context and context.correlation_id
            else str(uuid.uuid4())
        )

        # DEF-198: Clean architecture - import from utils/, callback registered by UI
        from utils.progress_callback import operation_progress

        with operation_progress("validating_definition"):
            try:
                # DEF-622: het record is de bron van zijn eigen context. De
                # drie lijsten, id en categorie reizen altijd mee — ook zonder
                # ValidationContext en ook als een lijst leeg is — zodat
                # CON-01 en DUP_01 op het record oordelen en niet op wat een
                # aanroeper toevallig in metadata heeft gezet. Vóór de
                # cleaning: `clean_definition` schrijft de opgeschoonde tekst
                # in het object terug, en de CON-01-binding (record_text,
                # vingerafdruk) hoort bij de recordtekst zoals opgeslagen —
                # anders vervalt een geldige beoordeling zodra cleaning een
                # hoofdletter of punt toevoegt (koppelingenbevinding).
                context_dict = self._enrich_context_with_definition_fields(
                    self._context_dict(context), definition
                )

                text = definition.definitie
                if self.cleaning_service is not None:
                    cleaned = await self.cleaning_service.clean_definition(definition)
                    text = cleaned.cleaned_text if cleaned else definition.definitie

                result = await self.validation_service.validate_definition(
                    begrip=definition.begrip,
                    text=text,
                    ontologische_categorie=definition.ontologische_categorie,
                    context=context_dict,
                )

                # Ensure result is schema-compliant
                return ensure_schema_compliance(result, correlation_id)

            except Exception as e:
                logger.error(
                    f"Validation failed for definition begrip='{definition.begrip}', correlation_id='{correlation_id}': {e}"
                )
                return create_degraded_result(
                    error=str(e),
                    correlation_id=correlation_id,
                    begrip=definition.begrip,
                )

    async def batch_validate(
        self, items: Iterable[ValidationRequest], max_concurrency: int = 1
    ) -> list[ValidationResult]:
        """Valideer meerdere items sequentieel.

        Args:
            items: Itereerbare van ValidationRequest objects
            max_concurrency: Maximum parallelle validaties (genegeerd in v2.2)

        Returns:
            List[ValidationResult]: Resultaten in zelfde volgorde als input

        Note:
            - max_concurrency wordt genegeerd in deze versie (Story 2.2)
            - Parallelisme wordt toegevoegd in Story 2.3
            - Individuele failures resulteren in degraded results, niet batch failure
        """
        results: list[ValidationResult] = []
        for item in items:
            results.append(
                await self.validate_text(
                    begrip=item.begrip,
                    text=item.text,
                    ontologische_categorie=item.ontologische_categorie,
                    context=item.context,
                )
            )
        return results

    # Internal helpers
    @staticmethod
    def _context_dict(context: ValidationContext | None) -> dict[str, Any] | None:
        """Vertaal een ValidationContext naar de dict die de service verwacht.

        DEF-622: `metadata` reist mee. Daarin zitten de drie contextlijsten,
        `options` (force_duplicate) en de contextbeoordeling voor CON-01; vóór
        deze wijziging verdween dat blok stil op deze grens, waardoor CON-01
        en DUP_01 nooit context zagen. Een deep copy, zodat de service en de
        verrijking hieronder de invoer van de aanroeper niet kunnen muteren.
        """
        if context is None:
            return None
        context_dict: dict[str, Any] = {}
        if context.metadata:
            context_dict.update(copy.deepcopy(dict(context.metadata)))
        if context.profile:
            context_dict["profile"] = context.profile
        if context.correlation_id:
            context_dict["correlation_id"] = str(context.correlation_id)
        if context.locale:
            context_dict["locale"] = context.locale
        if context.feature_flags:
            context_dict["feature_flags"] = dict(context.feature_flags)
        return context_dict

    def _enrich_context_with_definition_fields(
        self, ctx: dict | None, definition: Definition
    ) -> dict:
        """Add definition fields to context metadata for richer validation.

        DEF-622: de drie contextlijsten van het record zijn gezaghebbend en
        worden altijd gezet — canoniek (getrimd, ontdubbeld, gesorteerd, met
        behoud van schrijfwijze) en ook wanneer ze leeg zijn. Een lege lijst
        expliciet doorgeven is nodig: anders blijft een verouderde waarde uit
        de aanroeper-metadata staan en oordeelt CON-01/DUP_01 op context die
        het record niet draagt. Geen soft-fail op dit contract: een record
        waarvan de contextlijsten niet te lezen zijn, is een defect record.
        """
        enriched: dict = dict(ctx or {})

        # Top-level context velden (compatibel met validator meta-checks)
        enriched["organisatorische_context"] = canoniseer_contextlijst(
            definition.organisatorische_context
        )
        enriched["juridische_context"] = canoniseer_contextlijst(
            definition.juridische_context
        )
        enriched["wettelijke_basis"] = canoniseer_contextlijst(
            definition.wettelijke_basis
        )
        # Ook categorie en id zijn recordwaarden en worden altijd gezet — óók
        # als het record ze niet heeft. Anders blijft een conflicterende
        # aanroeperwaarde staan en zoekt DUP_01 op een categorie die het
        # record niet draagt (reviewbevinding op de transportcommit).
        enriched["categorie"] = definition.categorie
        enriched["ontologische_categorie"] = definition.ontologische_categorie
        # Voor de duplicaatcontrole: het record mag niet zijn eigen duplicaat
        # zijn; `None` betekent expliciet 'nog niet opgeslagen'.
        enriched["definition_id"] = definition.id
        # DEF-622: CON-01 bindt bewijs en beoordeling aan de exacte
        # recordtekst, ook wanneer cleaning de getoetste tekst wijzigt.
        enriched["record_text"] = definition.definitie
        # De op het record vastgelegde expertbeoordeling van de naamfunctie
        # (B-07). Alleen uit het record; een aanroeper kan haar hier niet
        # meegeven voor een ander record. Vervalt vanzelf bij een gewijzigde
        # tekst/context/term (vingerafdruk).
        review = (definition.metadata or {}).get("context_review")
        enriched["context_review"] = review if isinstance(review, dict) else None
        # De recordversie waartegen de beoordeling wordt gelegd (E2).
        enriched["definition_version"] = (definition.metadata or {}).get(
            "version_number"
        )

        # Gebundelde definition metadata onder sleutel 'definition'
        try:
            def_meta = {
                "begrip": definition.begrip,
                "synoniemen": list(definition.synoniemen or []),
                "toelichting": definition.toelichting or "",
                "gerelateerde_begrippen": list(definition.gerelateerde_begrippen or []),
                "ontologische_categorie": definition.ontologische_categorie,
            }
            base = enriched.get("definition")
            if isinstance(base, dict):
                base.update({k: v for k, v in def_meta.items() if v})
            else:
                enriched["definition"] = {k: v for k, v in def_meta.items() if v}
        except (TypeError, AttributeError) as e:
            # DEF-248: Log metadata enrichment failures
            logger.warning(
                f"Failed to enrich definition metadata: {type(e).__name__}: {e}",
                extra={"begrip": getattr(definition, "begrip", "unknown")},
            )

        return enriched
