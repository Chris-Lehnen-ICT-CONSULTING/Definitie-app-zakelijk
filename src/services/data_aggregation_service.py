"""
Data Aggregation Service.

Centralized service voor het verzamelen en aggregeren van data voor export en andere doeleinden.
Dit elimineert de directe afhankelijkheid van services op UI session state.
"""

import logging
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import splits_definitietekst
from domain.int03.contract import Beoordelingsbinding as Int03Binding
from domain.int03.opslag import exportdocument as int03_exportdocument

logger = logging.getLogger(__name__)

# DEF-622 (K2): de contractvelden die uitsluitend van het opgeslagen record
# komen. Aanvullende exportdata kan ze niet vervangen — validator en uitvoer
# gebruiken zo exact dezelfde recordgegevens. DEF-743: de bronvelden van het
# kerncontract (bronset, AI-beoordeling, deskundigenuitzondering, peildatum)
# horen daar ook bij.
_CONTRACT_METADATA: tuple[str, ...] = (
    "id",
    "versie",
    "context_review",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
    "sources",
    "provenance_sources",
    "source_assessment",
    "source_review",
    "peildatum",
)
_CONTRACT_CONTEXT: tuple[str, ...] = ("organisatorisch", "juridisch", "wettelijk")

#: DEF-772: de contextlijsten van de uitvoer (`context_dict`) onder de
#: contractsleutels waaraan de INT-03-beoordeling is gebonden.
_INT03_CONTEXTVELDEN: dict[str, str] = {
    "organisatorische_context": "organisatorisch",
    "juridische_context": "juridisch",
    "wettelijke_basis": "wettelijk",
}

#: Sleutels van het exporteerbare bronbewijs (DEF-743 §5 persistentiecontract).
_BRONBEWIJS_LEEG: dict[str, Any] = {
    "status": "absent",
    "current": False,
    "reason": None,
    "source_reference": None,
    "peildatum": None,
    "sources": [],
    "source_receipt": None,
    "source_assessment": None,
    "source_review": None,
    "source_review_status": {"status": "absent", "reason": None},
    "source_assessment_status": {"applicable": False, "reason": None},
    "con02": None,
    "history": [],
    "review_history": [],
    "proposals": [],
}


def con02_replay(
    record: DefinitieRecord,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """De actuele CON-02-uitkomst van het record via de kernreplay (bevinding 3).

    `beoordeel_bronbasis` (C) bindt de opgeslagen AI-beoordeling en de
    deskundigenuitzondering aan de vingerafdruk van precies dit record; een
    beoordeling van een eerdere bronidentiteit/peildatum/tekst wordt daar
    níet toegepast. Geeft (regelresultaat of None, toepasbaarheidsstatus).
    Zonder kernhelpers: geen replay en expliciet niet toepasbaar — nooit een
    pass louter omdat het bewijsomhulsel bij de kandidaat past.
    """
    bewijs = record.get_source_evidence()
    if bewijs is None or bewijs.get("source_assessment") is None:
        return None, {
            "applicable": False,
            "reason": "geen opgeslagen AI-bronbeoordeling",
        }
    try:
        from domain.sources.contract import beoordeel_bronbasis
    except ImportError as e:
        return None, {
            "applicable": False,
            "reason": f"kernhelpers niet beschikbaar: {e}",
        }
    try:
        uitkomst = beoordeel_bronbasis(
            record.begrip or "",
            record.get_definitie_tekst(),
            record.get_contextlijsten(),
            bewijs.get("sources") or [],
            assessment=bewijs.get("source_assessment"),
            review=record.get_source_review(),
            definitie_versie=record.version_number,
            peildatum=bewijs.get("peildatum"),
        ).als_dict()
    except Exception as e:  # replay mag de export niet breken; wel eerlijk
        logger.warning("CON-02-replay voor export mislukte: %s", e, exc_info=True)
        return None, {"applicable": False, "reason": f"replay mislukt: {e}"}
    samenvatting = (uitkomst.get("review") or {}).get("assessment") or {}
    return uitkomst, {
        "applicable": samenvatting.get("applied") is True,
        "reason": samenvatting.get("reason"),
    }


def bronbewijs_uit_record(record: DefinitieRecord) -> dict[str, Any]:
    """Het exporteerbare bronbewijs, uitsluitend uit het opgeslagen record.

    Volledige bronset (citaten, coördinaten, geneste metadata), kwitantie,
    AI-beoordeling (delen, bewijs, onzekerheid, afgewezen bewijs, technische
    fout, attributie), deskundigenuitzondering + status (een uitzondering
    blijft herkenbaar als uitzondering), stale-status, en samenvattingen van
    historie en voorstellen. Geen cijfer: er is er geen. Een record met alleen
    `source_reference` is onvolledig bewijs (`reference_only`); er wordt
    niets bij verzonnen.
    """
    status = record.get_source_evidence_status()
    bewijs = record.get_source_evidence() or {}
    geschiedenis = record.get_source_evidence_history()
    voorstelrecords = record.get_source_proposals()
    if not (
        isinstance(status, dict)
        and isinstance(bewijs, dict)
        and isinstance(geschiedenis, list)
        and isinstance(voorstelrecords, list)
    ):
        # Geen echt record (vervanger in tests): geen bewijs, niets verzonnen.
        return deepcopy(_BRONBEWIJS_LEEG)
    historie = [
        {
            "origin": h.get("origin"),
            "version_number": h.get("version_number"),
            "recorded_at": h.get("recorded_at"),
            "superseded_at": h.get("superseded_at"),
            "superseded_on_version": h.get("superseded_on_version"),
            "candidate": (h.get("candidate") or {}).get("definitie"),
            "source_count": len(h.get("sources") or []),
            "assessment_status": (h.get("source_assessment") or {}).get("status"),
            "assessment_fingerprint": (h.get("source_assessment") or {}).get(
                "fingerprint"
            ),
        }
        for h in geschiedenis
        if isinstance(h, dict)
    ]
    voorstellen = [
        {
            "proposal_id": v.get("proposal_id"),
            "status": v.get("status"),
            "actor": v.get("actor"),
            "reserved_at": v.get("reserved_at"),
            "original_text": (v.get("original") or {}).get("text"),
            "candidate_text": (v.get("outcome") or {}).get("candidate_text"),
            "rationale": (v.get("outcome") or {}).get("rationale"),
            "events": list(v.get("events") or []),
        }
        for v in voorstelrecords
        if isinstance(v, dict)
    ]
    con02, toepasbaarheid = con02_replay(record)
    reviewhistorie = record.get_source_review_history()
    return {
        **_BRONBEWIJS_LEEG,
        "status": status["status"],
        "current": status["current"],
        "reason": status["reason"],
        "source_reference": record.source_reference,
        "peildatum": bewijs.get("peildatum"),
        "sources": list(bewijs.get("sources") or []),
        "source_receipt": bewijs.get("source_receipt"),
        # Ruwe opgeslagen beoordeling (historisch bewijs) + of zij nog op dit
        # record van toepassing is volgens de kernbinding.
        "source_assessment": bewijs.get("source_assessment"),
        "source_assessment_status": toepasbaarheid,
        # De actuele, eerlijke CON-02-uitkomst (replay): status/parts/review.
        "con02": con02,
        "source_review": record.get_source_review(),
        "source_review_status": record.get_source_review_status(),
        "history": historie,
        "review_history": reviewhistorie if isinstance(reviewhistorie, list) else [],
        "proposals": voorstellen,
    }


def bronregels_uit_bewijs(bronbewijs: dict[str, Any]) -> list[str]:
    """Korte, leesbare bronregels (titel · route · vindplaats/URL) uit het bewijs."""
    regels: list[str] = []
    for bron in bronbewijs.get("sources") or []:
        if not isinstance(bron, dict):
            continue
        titel = str(bron.get("title") or bron.get("filename") or "onbekende bron")
        delen = [titel]
        if bron.get("provider"):
            delen.append(f"route: {bron['provider']}")
        if bron.get("citation_label"):
            delen.append(f"vindplaats: {bron['citation_label']}")
        if bron.get("url"):
            delen.append(str(bron["url"]))
        regels.append(" · ".join(delen))
    return regels


@dataclass
class CategoryChangeState:
    """State container voor category change regeneration preview."""

    # Category change info
    old_category: str
    new_category: str
    begrip: str
    current_definition: str

    # Impact analysis
    impact_analysis: list[str] = field(default_factory=list)

    # UI state
    show_regeneration_preview: bool = False
    saved_record_id: int | None = None

    # Workflow data
    requires_regeneration: bool = True
    success_message: str = ""


@dataclass
class DefinitieExportData:
    """Data container voor definitie export."""

    # Core definitie data
    begrip: str
    definitie_origineel: str
    definitie_gecorrigeerd: str
    definitie_aangepast: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Context informatie
    context_dict: dict[str, list[str]] = field(default_factory=dict)

    # Toetsing en beoordeling
    toetsresultaten: dict[str, Any] = field(default_factory=dict)
    beoordeling: list[str] = field(default_factory=list)
    beoordeling_gen: list[str] = field(default_factory=list)

    # Voorbeelden en uitleg
    voorbeeld_zinnen: list[str] = field(default_factory=list)
    praktijkvoorbeelden: list[str] = field(default_factory=list)
    tegenvoorbeelden: list[str] = field(default_factory=list)
    toelichting: str = ""

    # Taalkundige informatie
    synoniemen: str = ""
    antoniemen: str = ""
    voorkeursterm: str = ""

    # Bronnen en validatie
    bronnen: list[str] = field(default_factory=list)
    bronnen_gebruikt: str = ""

    # Expert review
    expert_review: str = ""

    # DEF-743: het opgeslagen bronbewijs (zie `bronbewijs_uit_record`).
    bronbewijs: dict[str, Any] = field(
        default_factory=lambda: deepcopy(_BRONBEWIJS_LEEG)
    )

    # DEF-770: de opgeslagen INT-01-deeluitkomst (onderdelen, redenen en
    # binding aan kern en versie) met `applied`; None = niet opgeslagen.
    int01_beoordeling: dict[str, Any] | None = None

    # DEF-772: de opgeslagen INT-03-beoordeling als gestructureerde
    # exportuitkomst (replay met actuele binding, `applied`, verwijzingen,
    # herkomst, volledig document); None = niet opgeslagen (nooit stil pass).
    int03_beoordeling: dict[str, Any] | None = None

    # Technische metadata
    marker: str | None = None
    prompt_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DataAggregationService:
    """
    Service voor het aggregeren van data uit verschillende bronnen.

    Deze service haalt data op uit:
    - Database (DefinitieRepository)
    - Business services (WorkflowService, CategoryService, etc.)
    - Domain models

    Zonder directe afhankelijkheid van UI session state.
    """

    def __init__(
        self,
        repository: DefinitieRepository,
        *,
        int03_binding: Int03Binding | Callable[[], Int03Binding | None] | None = None,
    ):
        """Initialiseer data aggregation service.

        Args:
            repository: de definitierepository.
            int03_binding: DEF-772 — de actuele INT-03-beoordelingsbinding
                (promptversie, norm, provider/model) waaraan de export de
                opgeslagen beoordeling bindt, als waarde of als lazy
                resolver. `None` = bepaal haar uit code, regelrecord en
                configuratie (`int03_assessment_service.actuele_binding`).
        """
        self.repository = repository
        self._int03_binding = int03_binding
        logger.info("DataAggregationService geïnitialiseerd")

    def _int03_bindingswaarde(self) -> Int03Binding | None:
        """De actuele INT-03-binding voor de replay; None = onbekend (de replay
        benoemt dat en past geen opgeslagen beoordeling toe)."""
        binding = self._int03_binding
        if binding is None:
            from services.validation.int03_assessment_service import actuele_binding

            return actuele_binding()
        if callable(binding):
            try:
                return binding()
            except Exception as exc:
                logger.warning(
                    "INT-03-beoordelingsbinding voor export niet beschikbaar: %s",
                    type(exc).__name__,
                )
                return None
        return binding

    def _int03_exportdocument(
        self, definitie_record: DefinitieRecord, export_data: DefinitieExportData
    ) -> dict[str, Any] | None:
        """De opgeslagen INT-03-beoordeling, herbonden aan exact de kandidaat
        die de export draagt en aan de actuele binding.

        Ná de definitieve samenstelling (review v1): begrip, de geëxporteerde
        tekst (`definitie_aangepast` als die er is — zoals ook de validatiegate
        haar toetst —, anders `definitie_origineel`), de drie contextlijsten
        van de uitvoer en de uiteindelijke toelichting (`explanation`,
        aanvullende data of expliciet leeg). Wijkt die kandidaat af van de
        beoordeelde, dan is de beoordeling zichtbaar historisch; het document
        blijft als bewijs in de uitvoer en op het record.
        """
        document = definitie_record.get_int03_assessment()
        if not isinstance(document, dict):
            return None  # afwezig, of geen echt record (vervanger in tests)
        historie = definitie_record.get_int03_assessment_history()
        tekstveld = (
            "definitie_aangepast"
            if export_data.definitie_aangepast
            else "definitie_origineel"
        )
        context = export_data.context_dict
        toelichting = export_data.toelichting
        return int03_exportdocument(
            export_data.begrip or "",
            getattr(export_data, tekstveld) or "",
            {
                contract: list(
                    (context.get(uitvoer) if isinstance(context, dict) else None) or []
                )
                for contract, uitvoer in _INT03_CONTEXTVELDEN.items()
            },
            toelichting if isinstance(toelichting, str) else None,
            assessment=document,
            binding=self._int03_bindingswaarde(),
            history_count=len(historie) if isinstance(historie, list) else 0,
            kandidaatvelden={
                "begrip": "begrip",
                "text": tekstveld,
                "toelichting": "toelichting",
                "context": "context_dict",
            },
        )

    def aggregate_definitie_for_export(
        self,
        definitie_id: int | None = None,
        definitie_record: DefinitieRecord | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> DefinitieExportData:
        """
        Aggregeer alle data voor een definitie export.

        Args:
            definitie_id: ID van definitie om te exporteren
            definitie_record: Bestaande definitie record (optioneel)
            additional_data: Extra data om toe te voegen

        Returns:
            DefinitieExportData object met alle benodigde data
        """
        # Haal definitie record op indien nodig
        if definitie_record is None and definitie_id is not None:
            definitie_record = self.repository.get_definitie(definitie_id)
            if not definitie_record:
                msg = f"Definitie met ID {definitie_id} niet gevonden"
                raise ValueError(msg)

        # Basis export data. Tekstbasis (DEF-622, K4): de definitiezin; een in
        # de kolom ingebedde toelichting blijft een afzonderlijk gegeven.
        zin, ingebedde_toelichting = splits_definitietekst(
            definitie_record.definitie if definitie_record else ""
        )
        export_data = DefinitieExportData(
            begrip=definitie_record.begrip if definitie_record else "",
            definitie_origineel=zin,
            definitie_gecorrigeerd=zin,
        )

        # Vul metadata
        if definitie_record:
            export_data.metadata = {
                "id": definitie_record.id,
                "status": definitie_record.status,
                "versie": definitie_record.version_number,
                "categorie": definitie_record.categorie,
                "datum_voorstel": definitie_record.created_at,
                "voorsteller": definitie_record.created_by or "Systeem",
            }

            # Context uit definitie record (V2: drie lijsten)
            import json as _json

            def _parse_list(val: Any) -> list[str]:
                try:
                    if not val:
                        return []
                    if isinstance(val, str):
                        s = val.strip()
                        if s.startswith("["):
                            return list(_json.loads(s))
                        # Split op komma voor legacy samengestelde strings
                        parts = [p.strip() for p in s.split(",") if p.strip()]
                        return parts or []
                    if isinstance(val, list):
                        return val
                except (TypeError, ValueError):
                    # DEF-246: JSON parse or list conversion failed
                    return []
                return []

            org_list = _parse_list(
                getattr(definitie_record, "organisatorische_context", None)
            )
            jur_list = _parse_list(
                getattr(definitie_record, "juridische_context", None)
            )
            wet_raw = (
                definitie_record.get_wettelijke_basis_list()
                if hasattr(definitie_record, "get_wettelijke_basis_list")
                else []
            )
            if isinstance(wet_raw, list):
                wet_list = wet_raw
            elif not wet_raw:
                wet_list = []
            else:
                wet_list = [wet_raw]
            # Indien legacy 'context' dict aanwezig is op record, geef die prioriteit voor export-compatibiliteit
            legacy_ctx = getattr(definitie_record, "context", None)
            if isinstance(legacy_ctx, dict) and legacy_ctx:
                export_data.context_dict = legacy_ctx
            else:
                export_data.context_dict = {
                    "organisatorisch": org_list,
                    "juridisch": jur_list,
                    "wettelijk": wet_list,
                }
            # Ook handige stringrepresentaties in metadata voor CSV
            export_data.metadata["organisatorische_context"] = ", ".join(
                map(str, org_list)
            )
            export_data.metadata["juridische_context"] = ", ".join(map(str, jur_list))
            export_data.metadata["wettelijke_basis"] = ", ".join(map(str, wet_list))
            # DEF-622: de vastgelegde CON-01-expertbeoordeling reist mee naar
            # de validatiegate vóór export (en is zo ook exporteerbaar bewijs).
            if hasattr(definitie_record, "get_context_review"):
                review = definitie_record.get_context_review()
                if review is not None:
                    export_data.metadata["context_review"] = review
            # DEF-743: het opgeslagen bronbewijs — bronset, AI-beoordeling,
            # deskundigenuitzondering, peildatum en stale-status — komt
            # uitsluitend van het record. De contractsleutels landen in de
            # metadata (validatiegate + uitvoer), het volledige bewijs in
            # `bronbewijs`; zonder bewijs ontbreken de bronsleutels (niets
            # verzonnen) en zegt de status `reference_only`/`absent`.
            if isinstance(definitie_record, DefinitieRecord):
                export_data.bronbewijs = bronbewijs_uit_record(definitie_record)
                self._zet_broncontractvelden(export_data, definitie_record)
                if not export_data.bronnen:
                    export_data.bronnen = bronregels_uit_bewijs(export_data.bronbewijs)
                # DEF-770: uitsluitend van het record, nooit uit aanvullende data.
                export_data.int01_beoordeling = definitie_record.get_int01_beoordeling()
                # DEF-772: de INT-03-replay volgt onderaan, ná de definitieve
                # samenstelling van tekst, context en toelichting.

            # Timestamps
            export_data.created_at = definitie_record.created_at
            export_data.updated_at = definitie_record.updated_at

            # Haal voorbeelden op uit database (DEF-43 fix)
            if definitie_record.id:
                try:
                    voorbeelden_dict = self.repository.get_voorbeelden_by_type(
                        definitie_record.id
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to retrieve voorbeelden for definitie {definitie_record.id}: {e}"
                    )
                    voorbeelden_dict = {}

                # Map database types naar export fields
                export_data.voorbeeld_zinnen = voorbeelden_dict.get("sentence", [])
                export_data.praktijkvoorbeelden = voorbeelden_dict.get("practical", [])
                export_data.tegenvoorbeelden = voorbeelden_dict.get("counter", [])

                # Synoniemen/antoniemen: CSV-compatible comma separator (not newline!)
                # Multiple DB rows joined with ", " for proper CSV export
                synoniemen_list = voorbeelden_dict.get("synonyms", [])
                export_data.synoniemen = (
                    ", ".join(str(s) for s in synoniemen_list if s)
                    if synoniemen_list
                    else ""
                )

                antoniemen_list = voorbeelden_dict.get("antonyms", [])
                export_data.antoniemen = (
                    ", ".join(str(a) for a in antoniemen_list if a)
                    if antoniemen_list
                    else ""
                )

                # Toelichting: double newline for multi-paragraph text
                toelichting_list = voorbeelden_dict.get("explanation", [])
                export_data.toelichting = (
                    "\n\n".join(str(t) for t in toelichting_list if t)
                    if toelichting_list
                    else ""
                )

            # Voorkeursterm uit definitie record (al aanwezig in database)
            if definitie_record.voorkeursterm:
                export_data.voorkeursterm = definitie_record.voorkeursterm

        # Merge met additional data indien aanwezig
        if additional_data:
            # Warn about conflicts between database and session data (DEF-43)
            if definitie_record and definitie_record.id:
                list_fields = [
                    "voorbeeld_zinnen",
                    "praktijkvoorbeelden",
                    "tegenvoorbeelden",
                ]
                for field in list_fields:
                    db_value = getattr(export_data, field, [])
                    session_value = additional_data.get(field, [])
                    if db_value and session_value and db_value != session_value:
                        logger.warning(
                            f"Export conflict for {field}: DB has {len(db_value)} items, "
                            f"session has {len(session_value)} items. Using session data."
                        )

            self._merge_additional_data(export_data, additional_data)
            if isinstance(definitie_record, DefinitieRecord):
                self._borg_contractvelden(export_data, definitie_record)

        # Zelfde tekstconventie voor een expliciet meegegeven (legacy)tekst
        # (DEF-622, K4): de zin is de tekstbasis, de toelichting blijft apart.
        if export_data.definitie_aangepast:
            zin_aangepast, toelichting_aangepast = splits_definitietekst(
                export_data.definitie_aangepast
            )
            export_data.definitie_aangepast = zin_aangepast
            if toelichting_aangepast and not export_data.toelichting:
                export_data.toelichting = toelichting_aangepast
        if ingebedde_toelichting and not export_data.toelichting:
            export_data.toelichting = ingebedde_toelichting

        # DEF-772 (review v1): de INT-03-actualiteit wordt pas nu bepaald —
        # gebonden aan exact de kandidaat die de export draagt (begrip, tekst,
        # context, uiteindelijke toelichting), nooit aan het record vóór
        # aanvullende data. Uitsluitend van het record; aanvullende data kan
        # het document niet vervangen, alleen de kandidaat waaraan het wordt
        # herbonden.
        if isinstance(definitie_record, DefinitieRecord):
            export_data.int03_beoordeling = self._int03_exportdocument(
                definitie_record, export_data
            )

        logger.debug(f"Geaggregeerde export data voor begrip '{export_data.begrip}'")
        return export_data

    @staticmethod
    def _zet_broncontractvelden(
        export_data: DefinitieExportData, definitie_record: DefinitieRecord
    ) -> None:
        """De CON-02-contractsleutels van het record in de exportmetadata (DEF-743)."""
        velden = definitie_record.get_contractvelden()
        if not isinstance(velden, dict):
            return  # geen echt record (vervanger in tests)
        for sleutel in (
            "sources",
            "provenance_sources",
            "source_assessment",
            "source_review",
            "peildatum",
        ):
            if velden.get(sleutel) is not None:
                export_data.metadata[sleutel] = velden[sleutel]
            else:
                export_data.metadata.pop(sleutel, None)

    @staticmethod
    def _borg_contractvelden(
        export_data: DefinitieExportData, definitie_record: DefinitieRecord
    ) -> None:
        """Zet de contractvelden terug op de recordwaarden na de merge (K2).

        Aanvullende exportdata kon id, versie, context en beoordeling
        overschrijven; de validator oordeelde dan op andere gegevens dan de
        uitvoer bevatte. Een poging daartoe wordt gelogd, niet gehonoreerd.
        DEF-743: hetzelfde geldt voor de bronvelden en het bronbewijs.
        """
        lijsten = definitie_record.get_contextlijsten()
        review = definitie_record.get_context_review()
        if not isinstance(lijsten, dict) or not (
            review is None or isinstance(review, dict)
        ):
            # Geen echt record (vervanger in tests): niets te borgen.
            return
        contract = definitie_record.get_contractvelden()
        if not isinstance(contract, dict):
            return
        recordwaarden: dict[str, Any] = {
            "id": definitie_record.id,
            "versie": definitie_record.version_number,
            "context_review": review,
            "organisatorische_context": ", ".join(lijsten["organisatorische_context"]),
            "juridische_context": ", ".join(lijsten["juridische_context"]),
            "wettelijke_basis": ", ".join(lijsten["wettelijke_basis"]),
            "sources": contract.get("sources"),
            "provenance_sources": contract.get("provenance_sources"),
            "source_assessment": contract.get("source_assessment"),
            "source_review": contract.get("source_review"),
            "peildatum": contract.get("peildatum"),
        }
        recordbewijs = bronbewijs_uit_record(definitie_record)
        if export_data.bronbewijs != recordbewijs:
            logger.warning(
                "Export: aanvullende data probeerde het bronbewijs te vervangen; "
                "recordbewijs behouden"
            )
            export_data.bronbewijs = recordbewijs
        recordcontext = {
            "organisatorisch": list(lijsten["organisatorische_context"]),
            "juridisch": list(lijsten["juridische_context"]),
            "wettelijk": list(lijsten["wettelijke_basis"]),
        }
        afgewezen = [
            veld
            for veld in _CONTRACT_METADATA
            if export_data.metadata.get(veld) != recordwaarden[veld]
        ] + [
            f"context_dict.{veld}"
            for veld in _CONTRACT_CONTEXT
            if export_data.context_dict.get(veld) != recordcontext[veld]
        ]
        if afgewezen:
            logger.warning(
                "Export: aanvullende data probeerde contractvelden te vervangen; "
                "recordwaarden behouden voor %s",
                ", ".join(afgewezen),
            )
        for veld, waarde in recordwaarden.items():
            if waarde is None:
                export_data.metadata.pop(veld, None)
            else:
                export_data.metadata[veld] = waarde
        export_data.context_dict.update(recordcontext)

    def _merge_additional_data(
        self, export_data: DefinitieExportData, additional_data: dict[str, Any]
    ) -> None:
        """Merge additionele data in export data object."""
        # Direct mappings
        direct_fields = [
            "definitie_aangepast",
            "toelichting",
            "synoniemen",
            "antoniemen",
            "voorkeursterm",
            "bronnen_gebruikt",
            "expert_review",
            "marker",
            "prompt_text",
        ]

        for field_name in direct_fields:
            if field_name in additional_data:
                setattr(export_data, field_name, additional_data[field_name])

        # List fields
        list_fields = [
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "bronnen",
            "beoordeling",
            "beoordeling_gen",
        ]

        for field_name in list_fields:
            if field_name in additional_data:
                value = additional_data[field_name]
                if isinstance(value, list):
                    setattr(export_data, field_name, value)

        # Dict fields
        if "toetsresultaten" in additional_data:
            export_data.toetsresultaten = additional_data["toetsresultaten"]

        if "context_dict" in additional_data:
            export_data.context_dict.update(additional_data["context_dict"])

        if "metadata" in additional_data:
            export_data.metadata.update(additional_data["metadata"])

        # Ketenpartners (special handling)
        if "ketenpartners" in additional_data:
            export_data.metadata["ketenpartners"] = additional_data["ketenpartners"]

    def prepare_export_dict(self, export_data: DefinitieExportData) -> dict[str, Any]:
        """
        Bereid export data voor in dictionary formaat voor legacy export functies.

        Args:
            export_data: DefinitieExportData object

        Returns:
            Dictionary compatible met legacy export functies
        """
        return {
            "begrip": export_data.begrip,
            "definitie_origineel": export_data.definitie_origineel,
            "definitie_gecorrigeerd": export_data.definitie_gecorrigeerd,
            "definitie_aangepast": export_data.definitie_aangepast,
            "metadata": export_data.metadata,
            "context_dict": export_data.context_dict,
            "toetsresultaten": export_data.toetsresultaten,
            "beoordeling": export_data.beoordeling,
            "beoordeling_gen": export_data.beoordeling_gen,
            "voorbeeld_zinnen": export_data.voorbeeld_zinnen,
            "praktijkvoorbeelden": export_data.praktijkvoorbeelden,
            "tegenvoorbeelden": export_data.tegenvoorbeelden,
            "toelichting": export_data.toelichting,
            "synoniemen": export_data.synoniemen,
            "antoniemen": export_data.antoniemen,
            "voorkeursterm": export_data.voorkeursterm,
            "bronnen": export_data.bronnen,
            "bronnen_gebruikt": export_data.bronnen_gebruikt,
            "expert_review": export_data.expert_review,
            "bronbewijs": export_data.bronbewijs,
            "int01_beoordeling": export_data.int01_beoordeling,  # DEF-770
            "int03_beoordeling": export_data.int03_beoordeling,  # DEF-772
            "marker": export_data.marker,
            "prompt_text": export_data.prompt_text,
        }

    def aggregate_from_generation_result(
        self,
        generation_result: dict[str, Any],
        context_dict: dict[str, list[str]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DefinitieExportData:
        """
        Aggregeer data vanuit een generatie resultaat.

        Args:
            generation_result: Resultaat van definitie generatie
            context_dict: Context informatie
            metadata: Extra metadata

        Returns:
            DefinitieExportData object
        """
        export_data = DefinitieExportData(
            begrip=generation_result.get("begrip", ""),
            definitie_origineel=generation_result.get("definitie", ""),
            definitie_gecorrigeerd=generation_result.get(
                "definitie_gecorrigeerd", generation_result.get("definitie", "")
            ),
        )

        # Vul vanuit generation result
        if "voorbeeld_zinnen" in generation_result:
            export_data.voorbeeld_zinnen = generation_result["voorbeeld_zinnen"]

        if "praktijkvoorbeelden" in generation_result:
            export_data.praktijkvoorbeelden = generation_result["praktijkvoorbeelden"]

        if "tegenvoorbeelden" in generation_result:
            export_data.tegenvoorbeelden = generation_result["tegenvoorbeelden"]

        if "toelichting" in generation_result:
            export_data.toelichting = generation_result["toelichting"]

        if "synoniemen" in generation_result:
            export_data.synoniemen = generation_result["synoniemen"]

        if "antoniemen" in generation_result:
            export_data.antoniemen = generation_result["antoniemen"]

        if "bronnen" in generation_result:
            export_data.bronnen = generation_result["bronnen"]

        if "toetsresultaten" in generation_result:
            export_data.toetsresultaten = generation_result["toetsresultaten"]

        if "marker" in generation_result:
            export_data.marker = generation_result["marker"]

        # Context en metadata
        if context_dict:
            export_data.context_dict = context_dict

        if metadata:
            export_data.metadata = metadata

        # Timestamps
        export_data.created_at = datetime.now()

        return export_data

    def create_category_change_state(
        self,
        old_category: str,
        new_category: str,
        begrip: str,
        current_definition: str,
        impact_analysis: list[str],
        saved_record_id: int | None = None,
        success_message: str = "",
    ) -> CategoryChangeState:
        """
        Creëer category change state voor UI rendering.

        Args:
            old_category: Oude categorie
            new_category: Nieuwe categorie
            begrip: Het begrip
            current_definition: Huidige definitie
            impact_analysis: Impact analyse van de wijziging
            saved_record_id: ID van opgeslagen record (optioneel)
            success_message: Success bericht

        Returns:
            CategoryChangeState object voor UI
        """
        return CategoryChangeState(
            old_category=old_category,
            new_category=new_category,
            begrip=begrip,
            current_definition=current_definition,
            impact_analysis=impact_analysis,
            show_regeneration_preview=True,
            saved_record_id=saved_record_id,
            success_message=success_message,
        )
