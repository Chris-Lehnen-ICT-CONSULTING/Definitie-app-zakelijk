"""ValidationOrchestratorV2 — sequentiële orchestrator voor validatie.

Deze orchestrator levert een dunne, async-first laag bovenop de
`ValidationServiceInterface`, met behoud van de oorspronkelijke invoer. Batchverwerking
gebeurt sequentieel; parallelisme volgt in een latere iteratie.
"""

from __future__ import annotations

import copy
import logging
import uuid
from collections.abc import Iterable
from typing import Any

from domain.context.normalisatie import canoniseer_contextlijst
from domain.ess03 import contract as ess03_contract
from domain.int03 import contract as int03_contract
from domain.sources.contract import (
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import canoniseer_bronnen, kwitantiefout
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


#: Uitkomst van de alias-normalisatie naast de gekozen lijst.
_ALIAS_OK = None
_ALIAS_CONFLICT = "conflict"
_ALIAS_ONGELDIG = "invalid"


def _normaliseer_bronalias(context_dict: dict[str, Any]) -> tuple[Any, str | None]:
    """Eén bronlijst uit `provenance_sources` (canoniek) en/of `sources` (legacy).

    Aanwezigheid en geldigheid worden apart bepaald. Aanwezig = de sleutel
    staat in de context; een aanwezige waarde `None` telt als expliciete
    afwezigheid (D levert `source_*`-velden expliciet als `None` wanneer het
    record ze niet draagt). Een aanwezige waarde die geen lijst en geen `None`
    is (tekst, dict, bool, getal, …) is **ongeldig** en kan de conflictcontrole
    niet omzeilen. Twee aanwezige geldige lijsten moeten gelijk zijn (freeze
    punt 2), anders conflict. Geeft (bronnen, status) met status `None`,
    `"conflict"` of `"invalid"`; er wordt nooit een lege lijst verzonnen. De
    gekozen lijst wordt als deep copy onder `provenance_sources` gezet, zodat
    de evaluator exact dezelfde bronnen ziet als de beoordeling.
    """
    lijsten: dict[str, list[Any]] = {}
    for sleutel in ("provenance_sources", "sources"):
        if sleutel not in context_dict:
            continue
        waarde = context_dict[sleutel]
        if waarde is None:
            continue
        if not isinstance(waarde, list):
            return None, _ALIAS_ONGELDIG
        lijsten[sleutel] = waarde
    if len(lijsten) == 2 and lijsten["provenance_sources"] != lijsten["sources"]:
        return lijsten["provenance_sources"], _ALIAS_CONFLICT
    gekozen = lijsten.get("provenance_sources", lijsten.get("sources"))
    if gekozen is not None:
        context_dict["provenance_sources"] = copy.deepcopy(gekozen)
    return gekozen, _ALIAS_OK


def _technische_blokkade(
    aliasstatus: str | None, receipt: dict[str, Any] | None, correlation_id: str
) -> tuple[str, str] | None:
    """(foutsoort, melding) die de bronbeoordeling vóór elke AI-aanroep blokkeert.

    Vaste volgorde, fail-closed: ongeldige alias → aliasconflict →
    verzamelfout in de kwitantie. Elke blokkade wordt gelogd; `None` betekent
    dat de beoordeling door mag.
    """
    if aliasstatus == _ALIAS_ONGELDIG:
        logger.error(
            "DEF-743: misvormde bronlijst onder 'sources'/'provenance_sources' "
            "(correlation_id=%s); bronbeoordeling niet uitgevoerd",
            correlation_id,
        )
        return (
            "source_alias_invalid",
            "bronlijst onder 'sources' of 'provenance_sources' is geen lijst",
        )
    if aliasstatus == _ALIAS_CONFLICT:
        logger.error(
            "DEF-743: verschillende bronlijsten onder 'sources' en "
            "'provenance_sources' (correlation_id=%s); bronbeoordeling niet "
            "uitgevoerd",
            correlation_id,
        )
        return (
            "source_alias_conflict",
            "verschillende bronlijsten onder 'sources' en 'provenance_sources'",
        )
    verzamelfout = kwitantiefout(receipt)
    if verzamelfout is not None:
        logger.error(
            "DEF-743: kwitantie meldt een verzamelfout (correlation_id=%s): %s",
            correlation_id,
            verzamelfout,
        )
        return "receipt_error", verzamelfout
    return None


class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    """Orchestrator voor validatie (V2).

    Afhankelijkheden worden via de constructor geïnjecteerd. De orchestrator
    zelf bevat geen businessregels; die leven in de onderliggende service/validator.

    Story 2.2: Core Implementation
    - Concrete implementatie van ValidationOrchestratorInterface
    - Dunne orchestration laag bovenop bestaande services
    - Sequentiële batch processing (parallelisme in latere story)
    - Geen cleaning tijdens toetsen; constructorparameter behouden voor compatibiliteit
    """

    def __init__(
        self,
        validation_service: ValidationServiceInterface,
        cleaning_service: CleaningServiceInterface | None = None,
        source_assessment_service: Any | None = None,
        ess03_assessment_service: Any | None = None,
        int03_assessment_service: Any | None = None,
    ) -> None:
        if validation_service is None:
            msg = "validation_service is vereist"
            raise ValueError(msg)
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service
        # DEF-743: de AI-bronbeoordeling (CON-02) is standaard onderdeel van
        # elke validatie met bronnen; deze wrapper verkrijgt haar zelf.
        self.source_assessment_service = source_assessment_service
        # DEF-766: de AI-telbaarheidsbeoordeling (ESS-03) is standaard
        # onderdeel van elke validatie met term en tekst; idem.
        self.ess03_assessment_service = ess03_assessment_service
        # DEF-772: de AI-verwijzingsbeoordeling (INT-03) is standaard
        # onderdeel van elke validatie met tekst; idem.
        self.int03_assessment_service = int03_assessment_service

    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer exact de aangeleverde tekst zonder opschoning.

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
                # DEF-747/624: uitsluitend toetsen gebruikt exact de invoer.
                # Cleaning hoort bij een expliciete generatie-/voorstelstap.
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
                # DEF-766: het afzonderlijke categorieargument is de expliciete
                # betekenisclaim van deze toetsing en hoort in dezelfde context
                # als de recordroute die zet. Zonder dit bereikte een gewijzigde
                # categorie de beoordelaar noch de vingerafdruk, en leverde een
                # oude beoordeling opnieuw een actuele pass (reviewbevinding R2).
                # `None` is 'geen claim van de aanroeper' — de bestaande
                # betekenis blijft dan gelden en een categorie uit de metadata
                # blijft staan; een expliciete waarde (ook een lege) gaat vóór.
                if ontologische_categorie is not None:
                    context_dict["ontologische_categorie"] = ontologische_categorie

                # DEF-743: de bronbeoordeling hoort bij exact deze tekst en
                # wordt hier standaard verkregen (nooit uit aanroepermetadata).
                assessment = await self._beoordeel_bronnen(
                    begrip, text, context_dict, correlation_id
                )
                if assessment is not None:
                    context_dict["source_assessment"] = assessment
                # DEF-766: idem voor de telbaarheidsbeoordeling (ESS-03).
                telbaarheid = await self._beoordeel_telbaarheid(
                    begrip, text, context_dict, correlation_id
                )
                if telbaarheid is not None:
                    context_dict["ess03_assessment"] = telbaarheid
                # DEF-772: idem voor de verwijzingsbeoordeling (INT-03); de
                # payload reist via de evaluator in `rule_results`.
                verwijzingen = await self._beoordeel_verwijzingen(
                    begrip, text, context_dict, correlation_id
                )
                if verwijzingen is not None:
                    context_dict["int03_assessment"] = verwijzingen

                # Call underlying service
                result = await self.validation_service.validate_definition(
                    begrip=begrip,
                    text=text,
                    ontologische_categorie=ontologische_categorie,
                    context=context_dict,
                )

                # Ensure result is schema-compliant
                return self._met_beoordelingen(
                    ensure_schema_compliance(result, correlation_id),
                    assessment,
                    telbaarheid,
                )

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
        """Valideer een volledig Definition-object zonder tekst- of metadatamutatie.

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
                # aanroeper toevallig in metadata heeft gezet. DEF-747/624:
                # toetsing wijzigt geen tekst of metadata; validatie en de
                # CON-01/02-binding gebruiken dezelfde opgeslagen recordtekst.
                context_dict = self._enrich_context_with_definition_fields(
                    self._context_dict(context), definition
                )

                # DEF-743/747: bronbeoordeling en toetsing delen exact de
                # ongewijzigde recordtekst en dezelfde contextbinding.
                recordtekst = context_dict["record_text"]
                assessment = await self._beoordeel_bronnen(
                    definition.begrip, recordtekst, context_dict, correlation_id
                )
                if assessment is not None:
                    context_dict["source_assessment"] = assessment
                # DEF-766: de telbaarheidsbeoordeling bindt aan dezelfde
                # recordtekst, contextlijsten en de toelichting van het record.
                telbaarheid = await self._beoordeel_telbaarheid(
                    definition.begrip, recordtekst, context_dict, correlation_id
                )
                if telbaarheid is not None:
                    context_dict["ess03_assessment"] = telbaarheid
                # DEF-772: de verwijzingsbeoordeling bindt aan dezelfde
                # recordtekst, contextlijsten en de toelichting van het record.
                verwijzingen = await self._beoordeel_verwijzingen(
                    definition.begrip, recordtekst, context_dict, correlation_id
                )
                if verwijzingen is not None:
                    context_dict["int03_assessment"] = verwijzingen

                text = definition.definitie

                result = await self.validation_service.validate_definition(
                    begrip=definition.begrip,
                    text=text,
                    ontologische_categorie=definition.ontologische_categorie,
                    context=context_dict,
                )

                # Ensure result is schema-compliant
                return self._met_beoordelingen(
                    ensure_schema_compliance(result, correlation_id),
                    assessment,
                    telbaarheid,
                )

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
    async def _beoordeel_bronnen(
        self,
        begrip: str,
        tekst: str,
        context_dict: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any] | None:
        """De standaard AI-bronbeoordeling voor exact deze validatie (DEF-743).

        Een door de aanroeper meegegeven `source_assessment` wordt hier
        weggegooid: zij is nooit een kortere weg naar een positief oordeel.
        Volgorde, fail-closed: (1) bronalias normaliseren — `sources` (legacy)
        en `provenance_sources` (canoniek) zijn beide toegestaan, samen alleen
        als ze gelijk zijn, anders een technische fout; (2) een verzamelfout in
        de kwitantie is een technische fout, óók zonder bronnen en óók zonder
        dienst; (3) zonder bronnen geen AI-aanroep en geen beoordeling (`None`:
        de evaluator meldt expliciet open); (4) zonder geïnjecteerde dienst is
        de beoordeling expliciet `unavailable`; (5) een fout in de dienst is een
        technische fout — nooit stil een pass. De aanroepermetadata en de
        kandidaat blijven onaangeroerd.
        """
        context_dict.pop("source_assessment", None)
        bronnen, aliasstatus = _normaliseer_bronalias(context_dict)
        canoniek = canoniseer_bronnen(bronnen)
        peildatum = context_dict.get("peildatum")

        def _vingerafdruk() -> str:
            return bereken_bronvingerafdruk(
                begrip, tekst, context_dict, canoniek, peildatum=peildatum
            )

        receipt = context_dict.get("source_receipt")
        receipt = receipt if isinstance(receipt, dict) else None
        blokkade = _technische_blokkade(aliasstatus, receipt, correlation_id)
        if blokkade is not None:
            soort, melding = blokkade
            return beoordeling_technische_fout(
                _vingerafdruk(), soort, melding, sources=canoniek
            )

        if not canoniek:
            return None

        if self.source_assessment_service is None:
            logger.warning(
                "DEF-743: geen SourceAssessmentService geïnjecteerd; CON-02 blijft "
                "open (correlation_id=%s)",
                correlation_id,
            )
            return beoordeling_niet_beschikbaar(
                _vingerafdruk(),
                "geen bronbeoordelingsdienst beschikbaar; AI-beoordeling niet uitgevoerd",
            )

        # De werkelijke afkapgrens van de dienst gaat mee naar de evaluator,
        # zodat de replay de beoordelingskwitantie aan die grens bindt.
        grens = getattr(self.source_assessment_service, "max_passage_chars", None)
        if isinstance(grens, int) and not isinstance(grens, bool) and grens > 0:
            context_dict["assessment_max_passage_chars"] = grens
        try:
            assessment = await self.source_assessment_service.assess(
                begrip,
                tekst,
                context_dict,
                bronnen,
                peildatum=peildatum,
                correlation_id=correlation_id,
                receipt=receipt,
            )
            document = (
                assessment.als_dict() if hasattr(assessment, "als_dict") else assessment
            )
            if not isinstance(document, dict):
                msg = f"beoordelingsdienst gaf {type(document).__name__} terug"
                raise TypeError(msg)
            return document
        except Exception as exc:
            logger.error(
                "DEF-743: bronbeoordeling mislukt (correlation_id=%s): %s: %s",
                correlation_id,
                type(exc).__name__,
                exc,
            )
            return beoordeling_technische_fout(
                _vingerafdruk(),
                "unknown",
                f"{type(exc).__name__}: {exc}",
                sources=canoniek,
            )

    async def _beoordeel_telbaarheid(
        self,
        begrip: str,
        tekst: str,
        context_dict: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any] | None:
        """De standaard AI-telbaarheidsbeoordeling voor exact deze validatie (DEF-766).

        Een door de aanroeper meegegeven `ess03_assessment` wordt weggegooid:
        zij is nooit een kortere weg naar een positief oordeel. Volgorde,
        fail-closed: (1) zonder term of zonder (niet-lege) tekst geen
        AI-aanroep en geen beoordeling (`None`: de evaluator meldt
        `not_evaluated`); (2) zonder geïnjecteerde dienst is de beoordeling
        expliciet `unavailable`; (3) een fout in de dienst of een dienst die
        geen document geeft is een technische fout — nooit stil een pass. De
        bronlijst is dezelfde als voor CON-02 (alias al genormaliseerd door
        `_beoordeel_bronnen`); de bedoelde betekenis komt uit de context
        (`intentie_uit_context`). Aanroepermetadata en kandidaat blijven
        onaangeroerd.
        """
        context_dict.pop("ess03_assessment", None)
        if not str(begrip or "").strip() or not str(tekst or "").strip():
            return None
        bronnen = context_dict.get("provenance_sources")
        if bronnen is None:
            bronnen = context_dict.get("sources")
        if not isinstance(bronnen, list):
            bronnen = []
        intentie = ess03_contract.intentie_uit_context(context_dict)

        def _vingerafdruk() -> str:
            return ess03_contract.bereken_ess03_vingerafdruk(
                begrip, tekst, context_dict, bronnen, intentie=intentie
            )

        if self.ess03_assessment_service is None:
            logger.warning(
                "DEF-766: geen Ess03AssessmentService geïnjecteerd; ESS-03 blijft "
                "open (correlation_id=%s)",
                correlation_id,
            )
            return ess03_contract.beoordeling_niet_beschikbaar(
                _vingerafdruk(),
                "geen ESS-03-beoordelingsdienst beschikbaar; AI-beoordeling niet "
                "uitgevoerd",
            )
        # R1: de actuele beoordelingsbinding (promptversie, norm, provider/
        # model) gaat mee naar de evaluator, zodat die de verkregen beoordeling
        # tegen exact deze configuratie legt — zonder netwerk.
        binding = getattr(self.ess03_assessment_service, "binding", None)
        if callable(binding):
            try:
                context_dict["ess03_binding"] = binding().als_dict()
            except Exception as exc:  # pragma: no cover - defensief
                logger.warning("DEF-766: beoordelingsbinding niet bepaald: %s", exc)
        try:
            assessment = await self.ess03_assessment_service.assess(
                begrip,
                tekst,
                context_dict,
                bronnen,
                intentie=intentie,
                correlation_id=correlation_id,
            )
            document = (
                assessment.als_dict() if hasattr(assessment, "als_dict") else assessment
            )
            if not isinstance(document, dict):
                msg = f"beoordelingsdienst gaf {type(document).__name__} terug"
                raise TypeError(msg)
            return document
        except Exception as exc:
            logger.error(
                "DEF-766: telbaarheidsbeoordeling mislukt (correlation_id=%s): %s: %s",
                correlation_id,
                type(exc).__name__,
                exc,
            )
            return ess03_contract.beoordeling_technische_fout(
                _vingerafdruk(), "unknown", f"{type(exc).__name__}: {exc}"
            )

    async def _beoordeel_verwijzingen(
        self,
        begrip: str,
        tekst: str,
        context_dict: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any] | None:
        """De standaard AI-verwijzingsbeoordeling voor exact deze validatie (DEF-772).

        Een door de aanroeper meegegeven `int03_assessment` wordt weggegooid:
        zij is nooit een kortere weg naar een positief oordeel. Volgorde,
        fail-closed: (1) zonder (niet-lege) tekst geen AI-aanroep en geen
        beoordeling (`None`: de evaluator meldt `not_evaluated`); een lege term
        is geen belemmering (de term is ondersteunend); (2) zonder
        geïnjecteerde dienst is de beoordeling expliciet `unavailable`; (3) een
        fout bij het bepalen van de binding, een fout in de dienst of een
        dienst die geen document geeft is een technische fout — nooit stil een
        pass, en bij een bindingsfout ook geen modelaanroep; daarbij worden
        alleen foutsoort en uitzonderingstype vastgelegd, nooit de
        uitzonderingstekst (R2). De toelichting komt uit de context
        (`toelichting_uit_context`);
        op de recordroute heeft `_verrijk_met_toelichting` daar de
        recordwaarde gezaghebbend gemaakt (R1). De actuele binding gaat als
        `int03_binding` mee naar de evaluator.
        """
        context_dict.pop("int03_assessment", None)
        if not str(tekst or "").strip():
            return None
        toelichting = int03_contract.toelichting_uit_context(context_dict)

        def _vingerafdruk() -> str:
            return int03_contract.bereken_int03_vingerafdruk(
                begrip, tekst, context_dict, toelichting
            )

        if self.int03_assessment_service is None:
            logger.warning(
                "DEF-772: geen Int03AssessmentService geïnjecteerd; INT-03 blijft "
                "open (correlation_id=%s)",
                correlation_id,
            )
            return int03_contract.beoordeling_niet_beschikbaar(
                _vingerafdruk(),
                "geen INT-03-beoordelingsdienst beschikbaar; AI-beoordeling niet "
                "uitgevoerd",
            )
        binding = getattr(self.int03_assessment_service, "binding", None)
        if callable(binding):
            try:
                context_dict["int03_binding"] = binding().als_dict()
            except Exception as exc:
                # Zonder actuele binding kan geen beoordeling als actueel
                # gelden: technische fout, geen modelaanroep. Alleen het
                # uitzonderingstype; de tekst bereikt log noch document (R2).
                logger.error(
                    "DEF-772: beoordelingsbinding niet bepaald (correlation_id=%s): %s",
                    correlation_id,
                    type(exc).__name__,
                )
                return int03_contract.beoordeling_technische_fout(
                    _vingerafdruk(),
                    "unknown",
                    f"{type(exc).__name__} bij het bepalen van de INT-03-"
                    "beoordelingsbinding (uitzonderingstekst niet opgenomen)",
                )
        try:
            assessment = await self.int03_assessment_service.assess(
                begrip,
                tekst,
                context_dict,
                toelichting=toelichting,
                correlation_id=correlation_id,
            )
            document = (
                assessment.als_dict() if hasattr(assessment, "als_dict") else assessment
            )
        except Exception as exc:
            # Alleen het uitzonderingstype: de tekst kan invoer of
            # credentialfragmenten dragen en bereikt log noch document.
            logger.error(
                "DEF-772: verwijzingsbeoordeling mislukt (correlation_id=%s): %s",
                correlation_id,
                type(exc).__name__,
            )
            return int03_contract.beoordeling_technische_fout(
                _vingerafdruk(),
                "unknown",
                f"{type(exc).__name__} in de INT-03-beoordelingsdienst "
                "(uitzonderingstekst niet opgenomen)",
            )
        if not isinstance(document, dict):
            soort = type(document).__name__
            logger.error(
                "DEF-772: beoordelingsdienst gaf %s terug in plaats van een document "
                "(correlation_id=%s)",
                soort,
                correlation_id,
            )
            return int03_contract.beoordeling_technische_fout(
                _vingerafdruk(),
                "unknown",
                f"beoordelingsdienst gaf {soort} terug in plaats van een document",
            )
        return document

    @staticmethod
    def _met_beoordelingen(
        result: ValidationResult,
        assessment: dict[str, Any] | None,
        telbaarheid: dict[str, Any] | None,
    ) -> ValidationResult:
        """Geef de verkregen beoordelingen volledig terug (contract 1.4.0 / 2.1.0).

        Zo kan de aanroeper (generatie, editor, opslag) ze bewaren zonder
        tweede AI-aanroep. Kopieën: het resultaat mag de context van de
        evaluator niet delen.
        """
        if isinstance(result, dict):
            result["source_assessment"] = copy.deepcopy(assessment)
            result["ess03_assessment"] = copy.deepcopy(telbaarheid)
        return result

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
        self._verrijk_met_bronvelden(enriched, definition)
        self._verrijk_met_ess03_velden(enriched, definition)

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
        # Ná het 'definition'-blok: dat blok laat een lege recordwaarde staan.
        self._verrijk_met_toelichting(enriched, definition)

        return enriched

    @staticmethod
    def _verrijk_met_toelichting(
        enriched: dict[str, Any], definition: Definition
    ) -> None:
        """De toelichting van het record is gezaghebbend op de recordroute
        (DEF-772, reviewbevinding R1) — op beide vindplaatsen die
        `toelichting_uit_context`/`intentie_uit_context` lezen (top-level
        `toelichting` en `definition.toelichting`), en óók wanneer het record
        haar niet (meer) draagt. Anders blijft een verouderde aanroeperwaarde
        de betekenisgrond, de vingerafdruk en de dienstcache bepalen, en geldt
        een oude beoordeling voor een gewijzigde of leeggemaakte toelichting.
        """
        toelichting = definition.toelichting
        if isinstance(toelichting, str) and toelichting.strip():
            enriched["toelichting"] = toelichting
            return
        enriched.pop("toelichting", None)
        blok = enriched.get("definition")
        if isinstance(blok, dict):
            blok.pop("toelichting", None)

    @staticmethod
    def _verrijk_met_ess03_velden(
        enriched: dict[str, Any], definition: Definition
    ) -> None:
        """De bedoelde betekenis van het record voor ESS-03 (DEF-766, R4/R5).

        `betekenisverduidelijking` (DEF-751) komt uit de generatieregistratie
        van het record; de actuele ESS-03-verduidelijking uit de eigen
        recordwaarde (`metadata["ess03_verduidelijking"]`). Beide zijn
        recordwaarden en vervangen aanroeperwaarden onder dezelfde sleutels;
        ontbreken ze, dan wordt niets verzonnen.
        """
        meta = definition.metadata or {}
        registratie = meta.get("generation_prompt_data")
        betekenis = (
            registratie.get("betekenisverduidelijking")
            if isinstance(registratie, dict)
            else None
        )
        if isinstance(betekenis, str) and betekenis.strip():
            enriched["betekenisverduidelijking"] = betekenis.strip()
        else:
            enriched.pop("betekenisverduidelijking", None)
        verduidelijking = meta.get("ess03_verduidelijking")
        if isinstance(verduidelijking, str) and verduidelijking.strip():
            enriched["ess03_verduidelijking"] = verduidelijking.strip()
        else:
            enriched.pop("ess03_verduidelijking", None)

    @staticmethod
    def _verrijk_met_bronvelden(
        enriched: dict[str, Any], definition: Definition
    ) -> None:
        """De bronvelden van het record zijn gezaghebbend (DEF-743).

        Draagt het record `provenance_sources` (canoniek) en/of `sources`
        (rijke alias), dan vervangen die de aanroeperwaarden onder dezelfde
        sleutels (deep copy); de gedeelde alias-normalisatie in
        `_beoordeel_bronnen` kiest daarna de lijst en faalt gesloten bij een
        conflict — voor record- én tekstvalidatie hetzelfde. `source_review` en
        `peildatum` komen eveneens van het record. Een opgeslagen
        `source_receipt` is generatiehistorie en gaat niet mee als invoer voor
        een herbeoordeling; een opgeslagen `source_assessment` wordt hier niet
        overgenomen — de wrapper verkrijgt altijd een verse beoordeling.
        """
        meta = definition.metadata or {}
        if "provenance_sources" in meta or "sources" in meta:
            # Het record wint volledig: aanroeperlijsten onder beide sleutels
            # vervallen, zodat een verouderde aanroeperlijst nooit een
            # schijnconflict met (of stille voorrang op) het record krijgt.
            enriched.pop("provenance_sources", None)
            enriched.pop("sources", None)
        for sleutel in ("provenance_sources", "sources"):
            if sleutel in meta:
                enriched[sleutel] = copy.deepcopy(meta[sleutel])
        if "source_review" in meta:
            review = meta["source_review"]
            enriched["source_review"] = (
                copy.deepcopy(review) if isinstance(review, dict) else None
            )
        if "peildatum" in meta:
            enriched["peildatum"] = meta["peildatum"]
