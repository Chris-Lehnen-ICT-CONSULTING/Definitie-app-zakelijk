"""Core CRUD operaties voor definities."""

import json
import logging
import uuid
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_duplicates import DefinitieDuplicateRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import (
    SOURCE_EVIDENCE_HISTORY_KEY,
    SOURCE_EVIDENCE_KEY,
    SOURCE_PROPOSALS_KEY,
    SOURCE_REVIEW_CODE,
    SOURCE_REVIEW_HISTORY_KEY,
    TOELICHTING_SCHEIDING,
    DefinitieRecord,
    DefinitieStatus,
    VaststelconflictError,
    Voorstelreservering,
    Voorsteltoepassing,
    bouw_bronbewijs,
    generatie_identiteit,
    issues_uit_validatieresultaat,
    serialiseer_generatieregistratie,
    splits_definitietekst,
)
from domain.context.contract import is_versienummer
from domain.context.normalisatie import lees_contextwaarden

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Bronhelpers:
    """De kernhelpers van het broncontract (pakket C, `domain.sources`).

    `vingerafdruk(begrip, tekst, contexten, bronnen_ruw, peildatum)` en
    `valideer_review(review, fingerprint, bronnen_ruw, definitie_versie)`.
    De persistentie berekent zelf geen vingerafdruk en beoordeelt zelf geen
    uitzondering; zij bindt uitsluitend aan het OPGESLAGEN record via déze
    helpers. Productie gebruikt altijd de echte kernhelpers; er is geen
    nep-helper als terugval — ontbreken ze, dan faalt elke bindingscontrole
    gesloten (`ValueError`) en wordt niets geschreven.
    """

    vingerafdruk: Callable[..., str]
    valideer_review: Callable[..., tuple[dict[str, Any] | None, dict[str, Any]]]


def _standaard_bronhelpers() -> Bronhelpers:
    """De echte kernhelpers, lazy geïmporteerd (de DB-laag laadt geen AI)."""
    from domain.sources.contract import bereken_bronvingerafdruk, valideer_bronreview

    def _vingerafdruk(
        begrip: str,
        tekst: str,
        contexten: Mapping[str, Any],
        bronnen: Any,
        peildatum: Any,
    ) -> str:
        # Beide helpers accepteren de ruwe opgeslagen bronlijst en canoniseren
        # zelf (deep copy); de persistentie projecteert niets.
        return str(
            bereken_bronvingerafdruk(
                begrip, tekst, contexten, bronnen, peildatum=peildatum
            )
        )

    def _valideer(
        review: Any, fingerprint: str, bronnen: Any, definitie_versie: Any
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        toepasbaar, samenvatting = valideer_bronreview(
            review, fingerprint, bronnen, definitie_versie
        )
        return toepasbaar, dict(samenvatting or {})

    return Bronhelpers(vingerafdruk=_vingerafdruk, valideer_review=_valideer)


#: Statussen van een herstelvoorstel (DEF-743 §4c); `events` is de historie.
_VOORSTEL_UITKOMSTEN: frozenset[str] = frozenset({"proposed", "blocked", "error"})
_VOORSTEL_AFSLUITINGEN: frozenset[str] = frozenset({"rejected", "superseded"})

#: Validatieresultaat-statussen die voor de bronregel zelf een technische,
#: niet-inhoudelijke uitkomst markeren (bestaand contract DEF-621/DEF-624).
_TECHNISCHE_REGELSTATUSSEN: frozenset[str] = frozenset({"error", "not_evaluated"})
#: De regel waarover een herstelvoorstel gaat; die moet werkelijk zijn beoordeeld.
_BRONREGEL = "CON-02"


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _nu() -> str:
    return datetime.now(UTC).isoformat()


def _geparste_issuelijst(basis_json: str | None) -> list[Any] | None:
    """De `validation_issues`-JSON als lijst, of None (leeg/misvormd/geen lijst)."""
    if not basis_json:
        return None
    try:
        issues = json.loads(basis_json)
    except (TypeError, ValueError):
        return None
    return issues if isinstance(issues, list) else None


def _technische_resultaatfout(validation: Mapping[str, Any]) -> str | None:
    """Technische onbruikbaarheid op resultaatniveau: status, readiness, dekking.

    DEF-624: alleen een expliciete `validated` is een uitgevoerde run. Een
    afwezige, null of ongeldige status is geen runbewijs en levert dezelfde
    afwijzing als `validation_unknown`, met de contractreden erbij.
    """
    from services.validation.result_contract import bepaal_runstatus

    runstatus = bepaal_runstatus(validation)
    if not runstatus.uitgevoerd:
        reden = f" ({runstatus.reason})" if runstatus.reason else ""
        return f"validation_status={runstatus.status}{reden}"
    readiness = validation.get("validation_readiness")
    if isinstance(readiness, Mapping) and readiness.get("ready") is False:
        return "validation_readiness.ready=False"
    dekking = validation.get("evaluation_coverage")
    if isinstance(dekking, Mapping):
        fouten = dekking.get("error")
        if isinstance(fouten, int | float) and fouten > 0:
            return f"evaluation_coverage.error={fouten}"
    return None


def _technische_regelfout(validation: Mapping[str, Any]) -> str | None:
    """Technische onbruikbaarheid per regel: `error`, of de bronregel `not_evaluated`."""
    statussen = validation.get("rule_statuses")
    if isinstance(statussen, Mapping):
        for regel, status in statussen.items():
            if status == "error" or (
                regel == _BRONREGEL and status in _TECHNISCHE_REGELSTATUSSEN
            ):
                return f"rule_statuses[{regel}]={status}"
    resultaten = validation.get("rule_results")
    if isinstance(resultaten, Mapping):
        for regel, resultaat in resultaten.items():
            if not isinstance(resultaat, Mapping):
                continue
            status = resultaat.get("status")
            if status == "error" or (
                regel == _BRONREGEL and status in _TECHNISCHE_REGELSTATUSSEN
            ):
                return f"rule_results[{regel}].status={status}"
    return None


@dataclass(frozen=True)
class _Toepassingsinvoer:
    """De onder de lock gecontroleerde invoer voor `apply_source_proposal`."""

    voorstellen: list[Any]
    voorstel: dict[str, Any]
    huidig: dict[str, Any]
    kandidaat: str


# De velden die samen de vaststel-identiteit vormen (B-03/B-10): begrip plus
# de drie contextlijsten. Categorie hoort daar bewust niet bij.
_IDENTITEITSVELDEN: tuple[str, ...] = (
    "begrip",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)

# De velden waarop de CON-01-beoordeling inhoudelijk rust (de vingerafdruk:
# term, tekst en context). Een schrijfactie op één ervan laat de binding
# van de beoordeling aan de recordversie vervallen (DEF-622, E2/V2c).
_BEOORDELINGSVELDEN: tuple[str, ...] = ("definitie", *_IDENTITEITSVELDEN)


# Eén strikte versieconventie voor invoer, gate en behoud bij vaststelling
# (V2b): de test van het contract zelf, zodat de persistentie nooit iets
# aanneemt wat de gate weigert — of andersom.
_is_versienummer = is_versienummer


class Unset:
    """Type van de ``UNSET``-sentinel: parameter niet meegegeven (anders dan ``None``)."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final[Unset] = Unset()


class DefinitieCrudRepository:
    """Core CRUD repository voor definities."""

    def __init__(
        self,
        db: DatabaseConnection,
        audit: AuditHelpers,
        duplicates: DefinitieDuplicateRepository,
        search: DefinitieSearchRepository,
        bronhelpers: Bronhelpers | None = None,
    ):
        self._db = db
        self._audit = audit
        self._duplicates = duplicates
        self._search = search
        # DEF-743: None = de echte kernhelpers (lazy). Alleen voor isolatie in
        # tests te vervangen; productie kent geen terugval.
        self._bronhelpers_override = bronhelpers

    # ------------------------------------------------ bronbinding (DEF-743)

    def _bronhelpers(self) -> Bronhelpers:
        if self._bronhelpers_override is not None:
            return self._bronhelpers_override
        try:
            return _standaard_bronhelpers()
        except ImportError as e:
            msg = (
                "kernhelpers van het broncontract (domain.sources) niet "
                "beschikbaar; de bronbinding kan niet worden gecontroleerd en er "
                "wordt niets geschreven"
            )
            raise ValueError(msg) from e

    def _bronvingerafdruk(
        self,
        record: DefinitieRecord,
        tekst: str | None = None,
        bewijs: dict[str, Any] | None = None,
    ) -> str:
        """De bronvingerafdruk over het OPGESLAGEN record (kernhelper).

        Begrip, definitiezin (of een expliciet meegegeven kandidaat), de drie
        contextlijsten, de opgeslagen bronset en de opgeslagen peildatum —
        nooit aanroeperwaarden.
        """
        bewijs = record.get_source_evidence() if bewijs is None else bewijs
        return self._bronhelpers().vingerafdruk(
            record.begrip,
            record.get_definitie_tekst() if tekst is None else tekst,
            record.get_contextlijsten(),
            (bewijs or {}).get("sources") or [],
            (bewijs or {}).get("peildatum"),
        )

    def create_definitie(
        self,
        record: DefinitieRecord,
        allow_duplicate: bool = False,
        duplicate_reason: str | None = None,
    ) -> int:
        """Maak nieuwe definitie aan.

        DEF-622 (besluit 5): naast een bestaande definitie met gelijk begrip en
        gelijke context mag alleen bewust worden aangemaakt, mét reden. Die
        reden komt in de audit van het nieuwe record; het bestaande record
        wordt niet aangeraakt. `allow_duplicate=True` zonder reden wordt
        geweigerd zodra er werkelijk een duplicaat is — zonder duplicaat is
        er niets te verantwoorden.
        """
        # DEF-198: Clean architecture - import from utils/, callback registered by UI
        from utils.progress_callback import operation_progress

        # Alleen betekenisvolle tekst is een auditreden; een ander type
        # (bytes, getal, lijst) is een programmeerfout en wordt geweigerd vóór
        # het record wordt aangeraakt (reviewbevinding D4).
        if duplicate_reason is not None and not isinstance(duplicate_reason, str):
            msg = (
                "duplicate_reason moet tekst zijn (auditreden), niet "
                f"{type(duplicate_reason).__name__}"
            )
            raise ValueError(msg)
        reden = (duplicate_reason or "").strip()

        with operation_progress("saving_to_database"):
            now = datetime.now(UTC)
            record.created_at = now
            record.updated_at = now

            wb_value = (
                record.wettelijke_basis if record.wettelijke_basis is not None else "[]"
            )

            # DEF-391: INSERT + audit-log atomair (all-or-nothing).
            # DEF-482/DEF-483: de duplicaatcontrole draait binnen dezelfde
            # BEGIN IMMEDIATE, zodat gelijktijdige creates geserialiseerd worden
            # en de tweede de gecommitte rij van de eerste ziet.
            with self._db.transaction() as conn:
                bestaand = self._actief_duplicaat(record)
                if bestaand is not None and not allow_duplicate:
                    msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
                    raise ValueError(msg)
                if bestaand is not None and not reden:
                    msg = (
                        f"Definitie voor '{record.begrip}' bestaat al in deze "
                        "context; bewust een nieuw concept ernaast aanmaken "
                        "vereist een reden voor de audit"
                    )
                    raise ValueError(msg)
                if record.status == DefinitieStatus.ESTABLISHED.value:
                    # B-03/B-10: ook een direct als vastgesteld aangemaakt
                    # record (import, tooling) mag geen tweede leidend record
                    # naast een bestaand vastgesteld record zetten.
                    self._eis_geen_vaststelconflict(
                        record.begrip,
                        record.organisatorische_context,
                        record.juridische_context,
                        record.wettelijke_basis,
                        eigen_id=None,
                    )
                include_legacy = AuditHelpers.has_legacy_columns_in_conn(conn)
                columns, values = AuditHelpers.build_insert_columns(
                    record, wb_value, include_legacy
                )
                column_sql = ", ".join(columns)
                placeholders = ", ".join("?" for _ in columns)

                cursor = conn.execute(
                    f"INSERT INTO definities ({column_sql}) VALUES ({placeholders})",
                    tuple(values),
                )

                record_id = cursor.lastrowid

                if record_id is None:
                    raise RuntimeError("Failed to get lastrowid after INSERT")

                audit = f"Nieuwe definitie aangemaakt voor '{record.begrip}'"
                if bestaand is not None:
                    audit += (
                        f" — bewust naast bestaande definitie {bestaand} "
                        f"(zelfde begrip en context); reden: {reden}"
                    )
                self._audit.log_geschiedenis(
                    record_id, "created", record.created_by, audit
                )

            logger.info(f"Created definitie {record_id}")
            return record_id

    def _actief_duplicaat(self, record: DefinitieRecord) -> int | None:
        """Het id van een actieve definitie met gelijk begrip en gelijke context.

        DEF-622: via `find_duplicates`, dat op de genormaliseerde volledige
        context vergelijkt. Bewust die naad en niet rechtstreeks de
        kandidaatselectie: de racetest (DEF-482/DEF-727) hangt zijn handshake
        aan `find_duplicates` binnen de schrijftransactie. Een gearchiveerd
        record is historie en telt niet als duplicaat.
        """
        duplicates = self._duplicates.find_duplicates(
            record.begrip,
            record.organisatorische_context,
            record.juridische_context or "",
            categorie=record.categorie,
            wettelijke_basis=(
                json.loads(record.wettelijke_basis) if record.wettelijke_basis else []
            ),
        )
        for match in duplicates:
            bestaand = match.definitie_record
            if bestaand.status != DefinitieStatus.ARCHIVED.value and bestaand.id:
                return int(bestaand.id)
        return None

    def _weiger_duplicaat(self, record: DefinitieRecord) -> None:
        """Gooi ``ValueError`` als er al een actieve definitie in deze context is."""
        if self._actief_duplicaat(record) is not None:
            msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
            raise ValueError(msg)

    def find_leidende_definitie(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any = "",
        wettelijke_basis: Any = None,
        *,
        eigen_id: int | None = None,
    ) -> DefinitieRecord | None:
        """Het vastgestelde, leidende record voor begrip + volledige context.

        Ongeacht categorie (B-03/B-10): categorie mag de exclusiviteit niet
        ongemerkt uitschakelen. `eigen_id` sluit het record zelf uit. Leest
        via een kale connectie en ziet dus ook de nog niet gecommitte staat
        binnen een lopende transactie — precies wat de hercontrole onder de
        schrijflock nodig heeft.
        """
        for rij in self._duplicates.zoek_gelijke_context(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            categorie=None,
            status=DefinitieStatus.ESTABLISHED,
        ):
            if rij.id is None or rij.id == eigen_id:
                continue
            if rij.via_synoniem:
                # De exclusiviteit geldt voor hetzelfde begrip (B-10). Een
                # ánder begrip dat dit begrip als synoniem voert, hoort bij
                # de generatielookup, niet bij de vaststelinvariant
                # (reviewbevinding E1).
                continue
            record = self.get_definitie(int(rij.id))
            if record is not None:
                return record
        return None

    def _eis_geen_vaststelconflict(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any,
        wettelijke_basis: Any,
        *,
        eigen_id: int | None,
    ) -> None:
        """De B-03/B-10-invariant op de persistentiegrens."""
        leidend = self.find_leidende_definitie(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            eigen_id=eigen_id,
        )
        if leidend is not None:
            msg = (
                f"Er is al een vastgestelde definitie (ID {leidend.id}) voor "
                f"'{begrip}' met dezelfde context; maximaal één leidend record "
                "per begrip en context (DEF-622). Vervang die bewust of archiveer "
                "haar eerst."
            )
            raise VaststelconflictError(msg, conflict_id=leidend.id)

    def set_context_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Leg de CON-01-expertbeoordeling vast op het record (DEF-622, B-07).

        Lees-wijzig-schrijf binnen één transactie op `validation_issues`;
        de overige issues blijven staan. Een gewone update: versie en audit
        volgen het bestaande pad.

        Herkomst (reviewbevinding V3): de beoordelaar in de beoordeling is de
        handelende gebruiker die haar opslaat (`updated_by`, de auditactor).
        Een payload met een andere beoordelaar wordt vóór mutatie geweigerd;
        ontbreekt de beoordelaar, dan wordt de handelende gebruiker gestempeld.
        Wie later vaststelt mag een ander zijn (bestaand contract).

        Versiebinding (reviewbevinding E2, deltareview V2a): `expected_version`
        is de recordversie die de beoordelaar vóór zich had. Ónder de
        schrijflock moet het record nog precies die versie dragen, anders
        wordt niets geschreven (``False``, zoals de optimistic lock van
        `approve`). Een payload die zelf een ander versienummer draagt is
        verouderde invoer (een eerder opgeslagen beoordeling die opnieuw
        wordt aangeboden) en wordt vóór mutatie geweigerd: alleen actuele
        invoer bindt aan de resulterende opslagversie (`expected_version + 1`).
        Elke latere schrijfactie op term, tekst of context laat de binding
        vervallen; zie `update_definitie`.
        """
        if not _is_versienummer(expected_version):
            msg = (
                "set_context_review vereist expected_version: de recordversie "
                f"die de beoordelaar beoordeeld heeft (gekregen: {expected_version!r})"
            )
            raise ValueError(msg)
        handelend = (
            None
            if review is None
            else self._geldige_beoordelaar(review, updated_by, expected_version)
        )

        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current:
                return False
            if current.version_number != expected_version:
                logger.warning(
                    f"set_context_review geweigerd: definitie {definitie_id} is "
                    f"versie {current.version_number}, beoordeeld is versie "
                    f"{expected_version}"
                )
                return False
            if review is not None:
                review = {
                    **review,
                    "actor": handelend,
                    # De versie die het record ná deze opslag draagt.
                    "version_number": expected_version + 1,
                }
            current.set_context_review(review)
            return self.update_definitie(
                definitie_id,
                {
                    "validation_issues": current.validation_issues,
                    # SQL-guard op dezelfde versie (WHERE version_number = ?).
                    "version_number": expected_version,
                },
                updated_by,
            )

    def _bewaak_vaststelinvariant(
        self, definitie_id: int, actueel: DefinitieRecord, updates: dict[str, Any]
    ) -> None:
        """Hercontrole van 'maximaal één vastgesteld record' op de resulterende
        staat, ónder de schrijflock (B-03/B-10).

        Alleen wanneer de update een record vastgesteld maakt of de identiteit
        (begrip/context) van een vastgesteld record raakt; categorie is bewust
        geen onderdeel van de identiteit.
        """
        nieuwe_status = updates.get("status", actueel.status)
        raakt_identiteit = any(veld in updates for veld in _IDENTITEITSVELDEN)
        if nieuwe_status == DefinitieStatus.ESTABLISHED.value and (
            actueel.status != DefinitieStatus.ESTABLISHED.value or raakt_identiteit
        ):
            self._eis_geen_vaststelconflict(
                updates.get("begrip", actueel.begrip),
                updates.get(
                    "organisatorische_context", actueel.organisatorische_context
                ),
                updates.get("juridische_context", actueel.juridische_context),
                updates.get("wettelijke_basis", actueel.wettelijke_basis),
                eigen_id=definitie_id,
            )

    @staticmethod
    def _geldige_beoordelaar(
        review: Any, updated_by: str | None, expected_version: int
    ) -> str:
        """Controleer de payload vóór mutatie; geeft de handelende gebruiker.

        Weigert (ValueError) een payload die geen dict is, zonder handelende
        gebruiker, met een afwijkende beoordelaar (V3), zonder of met een
        ongeldig getypeerd versienummer (V2b: de payload draagt zelf de
        beoordeelde versie als strikt geheel getal; `expected_version` is
        alleen de concurrency-guard, geen vervanging) of met een andere
        versie dan beoordeeld (V2a: verouderde invoer).
        """
        if not isinstance(review, dict):
            msg = "context_review moet een dict zijn"
            raise ValueError(msg)
        handelend = (updated_by if isinstance(updated_by, str) else "").strip()
        if not handelend:
            msg = (
                "set_context_review vereist een handelende gebruiker "
                "(updated_by) als betrouwbare beoordelaarsbron"
            )
            raise ValueError(msg)
        actor = review.get("actor")
        if actor is not None and (
            not isinstance(actor, str) or actor.strip() != handelend
        ):
            msg = (
                f"beoordelaar in de beoordeling ({actor!r}) wijkt af van de "
                f"handelende gebruiker ({handelend!r}); geweigerd vóór opslag"
            )
            raise ValueError(msg)
        meegegeven = review.get("version_number")
        if not _is_versienummer(meegegeven):
            # Strikt type (V2b): ontbrekend, null, `True`/`1.0`/`"1"` zijn
            # geen versienummer — numerieke gelijkheid volstaat niet, en een
            # kloppende expected_version vervangt de payloadversie niet.
            msg = (
                "beoordeling draagt geen geldig versienummer "
                f"({meegegeven!r}); de beoordeelde recordversie hoort als "
                "geheel getal in de beoordeling zelf; geweigerd vóór opslag"
            )
            raise ValueError(msg)
        if meegegeven != expected_version:
            msg = (
                f"beoordeling hoort bij versie {meegegeven!r}, maar beoordeeld "
                f"is versie {expected_version}: verouderde invoer, geweigerd "
                "vóór opslag; beoordeel de actuele versie opnieuw"
            )
            raise ValueError(msg)
        return handelend

    @staticmethod
    def _meegroeiende_beoordeling(
        actueel: DefinitieRecord, updates: dict[str, Any]
    ) -> str | None:
        """De `validation_issues`-JSON met de beoordeling op de nieuwe versie,
        of None wanneer er niets mee te nemen valt.

        Alleen een beoordeling die nú — met een strikt geheel versienummer —
        aan de actuele recordversie gebonden is groeit mee, en alleen bij een
        update die term, tekst en context niet schrijft en `validation_issues`
        niet zelf zet. Een al vervallen of verkeerd getypeerde binding
        herleeft hier dus nooit (reviewbevinding E2, tweede deltareview V2b).
        """
        if "validation_issues" in updates or any(
            veld in updates for veld in _BEOORDELINGSVELDEN
        ):
            return None
        review = actueel.get_context_review()
        if review is None:
            return None
        gebonden = review.get("version_number")
        if not _is_versienummer(gebonden) or gebonden != actueel.version_number:
            return None
        actueel.set_context_review(
            {**review, "version_number": actueel.version_number + 1}
        )
        return actueel.validation_issues

    # ------------------------------------------ bronbewijs (DEF-743, pakket D)

    @staticmethod
    def _bewijsinvoer(invoer: Any) -> dict[str, Any]:
        """Controleer de structurele bronbewijs-invoer (`source_evidence`-sleutel)."""
        if not isinstance(invoer, dict) or not isinstance(invoer.get("sources"), list):
            msg = "source_evidence-invoer vereist een dict met een lijst `sources`"
            raise ValueError(msg)
        return invoer

    def _bronbewijs_samenvoegen(
        self,
        actueel: DefinitieRecord,
        updates: Mapping[str, Any],
        invoer: Any,
        updated_by: str | None,
    ) -> tuple[str | None, bool]:
        """Nieuwe generatieregistratie-JSON (of None) en of de bronset wijzigt.

        Eerst de generatiecheck, dán de bewijsvergelijking (Codex-follow-up
        P2): een wérkelijk nieuwe generatie (afwijkende expliciete
        `generation_id`, of zonder id een nieuwe generatieregistratie) krijgt
        altijd een nieuw bewijsdocument met eigen identiteit — ook wanneer het
        model exact dezelfde bronset, kwitantie, beoordeling en peildatum
        opleverde; anders zou de verbruikte voorstelpoging van de vorige
        generatie blijven gelden. Binnen dezelfde generatie geldt: bewijs
        gelijk ⇒ niets (ook niet wanneer de tekst in dezelfde update wijzigt —
        dan hoort het oude bewijs bij de oude tekst en toont `current: false`
        dat eerlijk); anders gaat het oude document naar de append-only
        historie en wordt het nieuwe actueel, gebonden aan de tekst/context
        die deze update oplevert, mét behoud van de identiteit (max. één
        voorstel per oorspronkelijke generatie).
        """
        invoer = self._bewijsinvoer(invoer)
        huidig = actueel.get_source_evidence()
        begrip = updates.get("begrip", actueel.begrip)
        nieuwe_generatie = self._is_nieuwe_generatie(huidig, invoer, begrip)
        sleutels = ("sources", "source_receipt", "source_assessment", "peildatum")
        if (
            huidig is not None
            and not nieuwe_generatie
            and all(huidig.get(s) == invoer.get(s) for s in sleutels)
        ):
            return None, False

        bronnen_gewijzigd = (
            huidig is None
            or huidig.get("sources") != invoer.get("sources")
            or huidig.get("peildatum") != invoer.get("peildatum")
        )
        tekst = updates.get("definitie", actueel.definitie)
        contexten = {
            veld: lees_contextwaarden(updates.get(veld, getattr(actueel, veld)))
            for veld in _IDENTITEITSVELDEN
            if veld != "begrip"
        }
        if nieuwe_generatie:
            origin = "generation"
        elif bronnen_gewijzigd:
            origin = "correction"
        else:
            origin = "revalidation"
        nieuw = bouw_bronbewijs(
            begrip=begrip,
            definitie_tekst=splits_definitietekst(str(tekst or ""))[0],
            contexten=contexten,
            sources=invoer["sources"],
            source_receipt=invoer.get("source_receipt"),
            source_assessment=invoer.get("source_assessment"),
            peildatum=invoer.get("peildatum"),
            origin=origin,
            version_number=actueel.version_number + 1,
            recorded_by=updated_by,
            # Reviewbevinding 2: de generatie-identiteit overleeft handmatige
            # bron-/context-/peildatumcorrecties en herbeoordelingen; alleen
            # een werkelijk nieuwe generatie krijgt een nieuwe identiteit.
            generation_identity=(
                None
                if nieuwe_generatie or huidig is None
                else huidig.get("generation_identity")
            ),
            generation_id=(
                invoer.get("generation_id")
                if nieuwe_generatie or huidig is None
                else (huidig.get("generation_id") or invoer.get("generation_id"))
            ),
            generated_at=invoer.get("generated_at"),
            tekststadia=invoer.get("tekststadia"),
        )
        registratie = self._registratie_met_nieuw_bewijs(actueel, huidig, nieuw)
        return serialiseer_generatieregistratie(registratie), bronnen_gewijzigd

    @staticmethod
    def _is_nieuwe_generatie(
        huidig: dict[str, Any] | None, invoer: Mapping[str, Any], begrip: str
    ) -> bool:
        """Of de bewijs-invoer een wérkelijk nieuwe generatie is (reviewbevinding 2).

        Zonder opgeslagen bewijs: ja (eerste bewijs). Met een expliciete
        `generation_id` (kern C, gezaghebbend): alleen wanneer die afwijkt
        van de bewaarde identiteit. Zonder expliciete id: alleen wanneer de
        invoer een eigen generatieregistratie draagt (generatietijdstip én
        `definitie_eindtekst`) waarvan de afgeleide identiteit afwijkt. Een
        handmatige correctie (herladen record, geen generatiestadia) is
        nooit een nieuwe generatie en geeft dus nooit een extra voorstelpoging.
        """
        if huidig is None:
            return True
        bewaard = str(huidig.get("generation_identity") or "")
        gid = invoer.get("generation_id")
        if isinstance(gid, str) and gid.strip():
            return f"generation_id:{gid.strip()}" != bewaard
        stadia = invoer.get("tekststadia") or {}
        eindtekst = (
            stadia.get("definitie_eindtekst") if isinstance(stadia, dict) else None
        )
        generated_at = invoer.get("generated_at")
        if not (isinstance(eindtekst, str) and isinstance(generated_at, str)):
            return False
        afgeleid = generatie_identiteit(
            begrip, eindtekst, deepcopy(list(invoer["sources"])), generated_at
        )
        return afgeleid != bewaard

    def _verwerk_bewijsinvoer(
        self,
        actueel: DefinitieRecord,
        updates: Mapping[str, Any],
        bewijsinvoer: Any,
        velden: dict[str, Any],
        updated_by: str | None,
    ) -> tuple[bool, bool]:
        """Voeg bewijs-invoer (indien aanwezig) samen; geeft (bronset gewijzigd, niets te schrijven).

        Ónder de lock. Gewijzigd bewijs landt als `generation_prompt_data` in
        `velden`; ongewijzigd bewijs zonder andere kolommen betekent "niets te
        schrijven" (zelfde contract als een update zonder toegestane velden).
        """
        if bewijsinvoer is None:
            return False, False
        registratie_json, bronnen_gewijzigd = self._bronbewijs_samenvoegen(
            actueel, updates, bewijsinvoer, updated_by
        )
        if registratie_json is not None:
            velden["generation_prompt_data"] = registratie_json
            return bronnen_gewijzigd, False
        return bronnen_gewijzigd, not velden

    def _behoud_bronbinding(
        self,
        actueel: DefinitieRecord,
        updates: Mapping[str, Any],
        velden: dict[str, Any],
        bronnen_gewijzigd: bool,
        bronbinding_ongewijzigd: bool,
    ) -> None:
        """Neem een geldig gebonden CON-02-review mee als deze update de binding niet raakt.

        Term/tekst/context-velden, een gewijzigde bronset of een ruwe
        `generation_prompt_data`-schrijfactie (tenzij expliciet ongewijzigd)
        raken de binding; dan groeit niets mee en vervalt de review door de
        versiebump.
        """
        bronbinding_geraakt = (
            any(veld in updates for veld in _BEOORDELINGSVELDEN)
            or bronnen_gewijzigd
            or ("generation_prompt_data" in updates and not bronbinding_ongewijzigd)
        )
        if bronbinding_geraakt:
            return
        basis = velden.get("validation_issues", actueel.validation_issues)
        meegroeiend_bron = self._meegroeiende_bronbeoordeling(actueel, basis)
        if meegroeiend_bron is not None:
            velden["validation_issues"] = meegroeiend_bron

    @staticmethod
    def _registratie_met_nieuw_bewijs(
        actueel: DefinitieRecord,
        huidig: dict[str, Any] | None,
        nieuw: dict[str, Any],
    ) -> dict[str, Any]:
        """De generatieregistratie met `nieuw` actueel en `huidig` in de historie."""
        registratie = actueel.get_generatieregistratie() or {}
        historie = registratie.get(SOURCE_EVIDENCE_HISTORY_KEY)
        historie = list(historie) if isinstance(historie, list) else []
        if huidig is not None:
            historie.append(
                {
                    **huidig,
                    "superseded_at": _nu(),
                    "superseded_on_version": actueel.version_number,
                }
            )
        registratie[SOURCE_EVIDENCE_HISTORY_KEY] = historie
        registratie[SOURCE_EVIDENCE_KEY] = nieuw
        return registratie

    @staticmethod
    def _meegroeiende_bronbeoordeling(
        actueel: DefinitieRecord, basis_json: str | None
    ) -> str | None:
        """`validation_issues` met de CON-02-beoordeling op de nieuwe versie, of None.

        Alleen precies één marker die nú — met een strikt geheel versienummer
        — aan de actuele recordversie gebonden is groeit mee. Een al
        vervallen of misvormde binding herleeft hier nooit.
        """
        issues = _geparste_issuelijst(basis_json)
        if issues is None:
            return None
        markers = [
            i
            for i in issues
            if isinstance(i, dict) and i.get("code") == SOURCE_REVIEW_CODE
        ]
        if len(markers) != 1:
            return None
        review = markers[0].get("source_review")
        if not isinstance(review, dict):
            return None
        gebonden = review.get("version_number")
        if not _is_versienummer(gebonden) or gebonden != actueel.version_number:
            return None
        markers[0]["source_review"] = {
            **review,
            "version_number": actueel.version_number + 1,
        }
        return json.dumps(issues, ensure_ascii=False)

    @staticmethod
    def _eis_versienummer(waarde: Any, naam: str) -> int:
        if not _is_versienummer(waarde):
            msg = (
                f"{naam} moet de recordversie als strikt geheel getal zijn "
                f"(gekregen: {waarde!r})"
            )
            raise ValueError(msg)
        return int(waarde)

    @staticmethod
    def _eis_handelende_gebruiker(updated_by: Any, actie: str) -> str:
        handelend = _tekst(updated_by)
        if not handelend:
            msg = (
                f"{actie} vereist een handelende gebruiker (updated_by) als "
                "betrouwbare actorbron"
            )
            raise ValueError(msg)
        return handelend

    def set_source_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Leg de CON-02-deskundigenuitzondering vast (DEF-743, freeze punt 1).

        Zelfde actor-/versiecontroles als `set_context_review`; daarbovenop
        bindt de beoordeling via de bronvingerafdruk aan het OPGESLAGEN
        record (term, tekst, context, bronset, peildatum) en beoordeelt
        uitsluitend de kernhelper `valideer_bronreview` de inhoudelijke
        eisen (type, acceptatie, motivering, bron-id/hash/versie/locator,
        gedocumenteerd zoeken). Vervalste actor, ongeldig versienummer of
        niet-toepasbare payload: `ValueError` vóór mutatie. Versieconflict
        of afwijkende vingerafdruk (stale/vervalst): `False`, niets
        geschreven. Opgeslagen met `version_number = expected_version + 1`.
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        handelend: str | None = None
        if review is not None:
            handelend = self._geldige_bronreviewinvoer(
                review, updated_by, expected_version
            )

        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current:
                return False
            if current.version_number != expected_version:
                logger.warning(
                    f"set_source_review geweigerd: definitie {definitie_id} is "
                    f"versie {current.version_number}, beoordeeld is versie "
                    f"{expected_version}"
                )
                return False
            if review is not None:
                review = self._gebonden_bronreview(
                    current, review, handelend, expected_version
                )
                if review is None:
                    return False
            updates: dict[str, Any] = {
                "validation_issues": None,
                "version_number": expected_version,
            }
            # Auditgat: een vervangen of verwijderde CON-02-review verdwijnt
            # nergens anders duurzaam (de auditlog kent alleen sleutels/actor,
            # de schematrigger alleen tekst/context/status). Bewaar hem —
            # mét status, actor, tijd en kandidaatbinding — append-only in de
            # generatieregistratie, in dezelfde transactie als de vervanging.
            gebeurtenis = self._reviewgebeurtenis(
                current, review, handelend or _tekst(updated_by) or None
            )
            if gebeurtenis is not None:
                registratie = current.get_generatieregistratie() or {}
                historie = registratie.get(SOURCE_REVIEW_HISTORY_KEY)
                historie = list(historie) if isinstance(historie, list) else []
                registratie[SOURCE_REVIEW_HISTORY_KEY] = [*historie, gebeurtenis]
                updates["generation_prompt_data"] = serialiseer_generatieregistratie(
                    registratie
                )
            current.set_source_review(review)
            updates["validation_issues"] = current.validation_issues
            return self.update_definitie(
                definitie_id, updates, updated_by, _bronbinding_ongewijzigd=True
            )

    def _geldige_bronreviewinvoer(
        self, review: Any, updated_by: str | None, expected_version: int
    ) -> str:
        """Controleer de reviewpayload vóór mutatie; geeft de handelende gebruiker.

        Weigert (ValueError) een payload die geen dict is, zonder handelende
        gebruiker, met een afwijkende beoordelaar, of zonder strikt geheel,
        gelijk versienummer — dezelfde controles als `set_context_review`.
        """
        if not isinstance(review, dict):
            msg = "source_review moet een dict zijn"
            raise ValueError(msg)
        handelend = self._eis_handelende_gebruiker(updated_by, "set_source_review")
        actor = review.get("actor")
        if actor is not None and (
            not isinstance(actor, str) or actor.strip() != handelend
        ):
            msg = (
                f"beoordelaar in de beoordeling ({actor!r}) wijkt af van de "
                f"handelende gebruiker ({handelend!r}); geweigerd vóór opslag"
            )
            raise ValueError(msg)
        meegegeven = review.get("version_number")
        if not _is_versienummer(meegegeven) or meegegeven != expected_version:
            msg = (
                "beoordeling draagt geen geldig, gelijk versienummer "
                f"({meegegeven!r} ≠ {expected_version}); de beoordeelde "
                "recordversie hoort als geheel getal in de beoordeling zelf"
            )
            raise ValueError(msg)
        return handelend

    def _gebonden_bronreview(
        self,
        current: DefinitieRecord,
        review: dict[str, Any],
        handelend: str | None,
        expected_version: int,
    ) -> dict[str, Any] | None:
        """De review gebonden aan het OPGESLAGEN record, of None (stale/vervalst).

        Ónder de lock: vingerafdruk ≠ herberekening ⇒ None (niets schrijven);
        de kernhelper `valideer_bronreview` beoordeelt de inhoudelijke eisen
        (niet toepasbaar ⇒ ValueError). Geeft de payload met de opslagversie
        (`expected_version + 1`) en een gestempeld `reviewed_at`.
        """
        helpers = self._bronhelpers()
        bewijs = current.get_source_evidence() or {}
        vingerafdruk = self._bronvingerafdruk(current, bewijs=bewijs)
        review = {**review, "actor": handelend}
        if review.get("fingerprint") != vingerafdruk:
            logger.warning(
                f"set_source_review geweigerd: vingerafdruk van de "
                f"beoordeling hoort niet bij het opgeslagen record "
                f"{current.id} (stale of vervalste invoer)"
            )
            return None
        toepasbaar, samenvatting = helpers.valideer_review(
            review, vingerafdruk, bewijs.get("sources") or [], expected_version
        )
        if toepasbaar is None:
            reden = samenvatting.get("reason") or "onbekende reden"
            msg = f"bronreview niet toepasbaar: {reden}"
            raise ValueError(msg)
        return {
            **review,
            "version_number": expected_version + 1,
            "reviewed_at": review.get("reviewed_at") or _nu(),
        }

    def _reviewgebeurtenis(
        self,
        current: DefinitieRecord,
        nieuw: dict[str, Any] | None,
        actor: str | None,
    ) -> dict[str, Any] | None:
        """De historiegebeurtenis voor een vervangen/verwijderde CON-02-review.

        None wanneer er niets te bewaren valt (geen bestaande marker). Ook een
        stale of misvormde bestaande review wordt bewaard, met haar status.
        """
        markers = current._source_review_markers()
        if not markers:
            return None
        vorige = current.get_source_review()
        if vorige is None:
            # Meerdere of misvormde markers: bewaar de ruwe payloads.
            vorige_payload: Any = [deepcopy(m.get("source_review")) for m in markers]
        else:
            vorige_payload = vorige
        try:
            vingerafdruk: str | None = self._bronvingerafdruk(current)
        except ValueError:
            vingerafdruk = None
        return {
            "event": "removed" if nieuw is None else "replaced",
            "at": _nu(),
            "actor": actor,
            "version_number": current.version_number,
            "previous_status": current.get_source_review_status()["status"],
            "previous_review": vorige_payload,
            "candidate": {
                "definitie": current.get_definitie_tekst(),
                "fingerprint": vingerafdruk,
            },
            "new_review_type": (nieuw.get("type") if isinstance(nieuw, dict) else None),
        }

    def set_source_assessment(
        self,
        definitie_id: int,
        assessment: dict[str, Any],
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Vervang de AI-bronbeoordeling in het actuele bewijs (herbeoordeling).

        De beoordeling moet via haar vingerafdruk aan het OPGESLAGEN record
        (actuele tekst, context, bronset, peildatum) gebonden zijn, anders
        wordt niets geschreven (`False`). Het vorige bewijsdocument gaat naar
        de historie; bronset, kwitantie en generatie-identiteit blijven. Een
        geldig gebonden CON-02-review groeit mee (bronset ongewijzigd).
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        if not isinstance(assessment, dict) or not _tekst(
            assessment.get("fingerprint")
        ):
            msg = "source_assessment moet een dict met een niet-lege fingerprint zijn"
            raise ValueError(msg)
        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current or current.version_number != expected_version:
                return False
            huidig = current.get_source_evidence()
            if huidig is None:
                msg = (
                    f"definitie {definitie_id} heeft geen opgeslagen bronbewijs; "
                    "een herbeoordeling kan nergens aan binden"
                )
                raise ValueError(msg)
            if assessment["fingerprint"] != self._bronvingerafdruk(
                current, bewijs=huidig
            ):
                logger.warning(
                    f"set_source_assessment geweigerd: beoordeling hoort niet bij "
                    f"het opgeslagen record {definitie_id}"
                )
                return False
            nieuw = bouw_bronbewijs(
                begrip=current.begrip,
                definitie_tekst=current.get_definitie_tekst(),
                contexten=current.get_contextlijsten(),
                sources=huidig["sources"],
                source_receipt=huidig.get("source_receipt"),
                source_assessment=assessment,
                peildatum=huidig.get("peildatum"),
                origin="revalidation",
                version_number=expected_version + 1,
                recorded_by=_tekst(updated_by) or None,
                generation_identity=huidig.get("generation_identity"),
                generation_id=huidig.get("generation_id"),
            )
            registratie = self._registratie_met_nieuw_bewijs(current, huidig, nieuw)
            return self.update_definitie(
                definitie_id,
                {
                    "generation_prompt_data": serialiseer_generatieregistratie(
                        registratie
                    ),
                    "version_number": expected_version,
                },
                updated_by,
                _bronbinding_ongewijzigd=True,
            )

    # ------------------------------------- handmatig voorstel (DEF-743, F)

    def reserve_source_proposal(
        self,
        definitie_id: int,
        *,
        updated_by: str,
        expected_version: int,
    ) -> Voorstelreservering:
        """Reserveer — vóór de modelaanroep — de ene voorstelpoging van deze generatie.

        Onder de schrijflock en de versieguard: bestaat er al een poging met
        dezelfde `generation_identity` (ongeacht status: ook `error`,
        `blocked`, `rejected`), dan is de poging verbruikt. De reservering
        bewaart het onveranderlijke origineel (tekst + bronvingerafdruk) en
        is duurzaam over rerun/reload/dubbelklik.
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        handelend = self._eis_handelende_gebruiker(
            updated_by, "reserve_source_proposal"
        )
        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current:
                return Voorstelreservering("not_found", reason="definitie onbekend")
            if current.version_number != expected_version:
                return Voorstelreservering(
                    "version_conflict",
                    version_number=current.version_number,
                    reason=(
                        f"record is versie {current.version_number}, verwacht "
                        f"{expected_version}"
                    ),
                )
            bewijs = current.get_source_evidence()
            if bewijs is None:
                return Voorstelreservering(
                    "no_evidence",
                    version_number=current.version_number,
                    reason="geen opgeslagen bronbewijs bij dit record",
                )
            identiteit = str(bewijs.get("generation_identity") or "")
            for bestaand in current.get_source_proposals():
                if bestaand.get("generation_identity") == identiteit:
                    return Voorstelreservering(
                        "attempt_consumed",
                        proposal_id=bestaand.get("proposal_id"),
                        version_number=current.version_number,
                        generation_identity=identiteit,
                        reason=(
                            "de ene voorstelpoging van deze generatie is al "
                            f"verbruikt (status {bestaand.get('status')})"
                        ),
                    )
            vingerafdruk = self._bronvingerafdruk(current, bewijs=bewijs)
            proposal_id = uuid.uuid4().hex
            nu = _nu()
            voorstel = {
                "proposal_id": proposal_id,
                "generation_identity": identiteit,
                "status": "reserved",
                "actor": handelend,
                "reserved_at": nu,
                "version_number": expected_version + 1,
                "original": {
                    "text": current.get_definitie_tekst(),
                    "fingerprint": vingerafdruk,
                    "candidate": deepcopy(bewijs.get("candidate")),
                    "peildatum": bewijs.get("peildatum"),
                },
                "outcome": None,
                "applied": None,
                "events": [
                    {
                        "event": "reserved",
                        "at": nu,
                        "actor": handelend,
                        "version_number": expected_version + 1,
                    }
                ],
            }
            registratie = current.get_generatieregistratie() or {}
            voorstellen = registratie.get(SOURCE_PROPOSALS_KEY)
            voorstellen = list(voorstellen) if isinstance(voorstellen, list) else []
            registratie[SOURCE_PROPOSALS_KEY] = [*voorstellen, voorstel]
            ok = self.update_definitie(
                definitie_id,
                {
                    "generation_prompt_data": serialiseer_generatieregistratie(
                        registratie
                    ),
                    "version_number": expected_version,
                },
                handelend,
                _bronbinding_ongewijzigd=True,
            )
            if not ok:
                return Voorstelreservering(
                    "version_conflict", reason="record gewijzigd tijdens reservering"
                )
            return Voorstelreservering(
                "reserved",
                proposal_id=proposal_id,
                version_number=expected_version + 1,
                generation_identity=identiteit,
            )

    def _voorstel_bijwerken(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        updated_by: str,
        expected_version: int,
        van_status: frozenset[str],
        muteer: Callable[[DefinitieRecord, dict[str, Any]], dict[str, Any] | None],
        bronbinding_ongewijzigd: bool = True,
    ) -> bool:
        """Gedeelde lees-wijzig-schrijf op één voorstel onder lock en versieguard.

        `muteer(record, voorstel)` past het voorstel in place aan en geeft de
        extra kolomupdates (of None om af te breken zonder schrijven).
        """
        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current or current.version_number != expected_version:
                return False
            registratie = current.get_generatieregistratie() or {}
            voorstellen = registratie.get(SOURCE_PROPOSALS_KEY)
            if not isinstance(voorstellen, list):
                return False
            doel = next(
                (
                    v
                    for v in voorstellen
                    if isinstance(v, dict) and v.get("proposal_id") == proposal_id
                ),
                None,
            )
            if doel is None or doel.get("status") not in van_status:
                return False
            extra = muteer(current, doel)
            if extra is None:
                return False
            registratie[SOURCE_PROPOSALS_KEY] = voorstellen
            return self.update_definitie(
                definitie_id,
                {
                    **extra,
                    "generation_prompt_data": serialiseer_generatieregistratie(
                        registratie
                    ),
                    "version_number": expected_version,
                },
                updated_by,
                _bronbinding_ongewijzigd=bronbinding_ongewijzigd,
            )

    def record_source_proposal_outcome(
        self,
        definitie_id: int,
        proposal_id: str,
        outcome: dict[str, Any],
        *,
        updated_by: str,
        expected_version: int,
    ) -> bool:
        """Leg de uitkomst van de gereserveerde modelaanroep vast (append-only).

        `proposed` vereist een niet-lege kandidaat (≠ origineel) en motivering;
        `blocked`/`error` verbruiken de poging evengoed. Het origineel blijft
        onveranderlijk; alleen vanuit `reserved`.
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        handelend = self._eis_handelende_gebruiker(
            updated_by, "record_source_proposal_outcome"
        )
        if not isinstance(outcome, dict) or outcome.get("status") not in (
            _VOORSTEL_UITKOMSTEN
        ):
            msg = (
                "outcome.status moet 'proposed', 'blocked' of 'error' zijn "
                f"(gekregen: {outcome.get('status') if isinstance(outcome, dict) else outcome!r})"
            )
            raise ValueError(msg)
        status = str(outcome["status"])
        if status == "proposed":
            if not _tekst(outcome.get("candidate_text")):
                msg = "een voorstel vereist een niet-lege candidate_text"
                raise ValueError(msg)
            if not _tekst(outcome.get("rationale")):
                msg = "een voorstel vereist een niet-lege rationale"
                raise ValueError(msg)

        def _muteer(
            record: DefinitieRecord, voorstel: dict[str, Any]
        ) -> dict[str, Any] | None:
            origineel = (voorstel.get("original") or {}).get("text")
            if status == "proposed" and _tekst(outcome.get("candidate_text")) == _tekst(
                origineel
            ):
                msg = (
                    "candidate_text is gelijk aan het origineel: niets voor te stellen"
                )
                raise ValueError(msg)
            nu = _nu()
            voorstel["outcome"] = {
                **deepcopy(outcome),
                "recorded_at": nu,
                "actor": handelend,
            }
            voorstel["status"] = status
            voorstel.setdefault("events", []).append(
                {
                    "event": status,
                    "at": nu,
                    "actor": handelend,
                    "version_number": expected_version + 1,
                }
            )
            return {}

        return self._voorstel_bijwerken(
            definitie_id,
            proposal_id,
            updated_by=handelend,
            expected_version=expected_version,
            van_status=frozenset({"reserved"}),
            muteer=_muteer,
        )

    def set_source_proposal_status(
        self,
        definitie_id: int,
        proposal_id: str,
        status: str,
        updated_by: str,
        *,
        expected_version: int,
        note: str | None = None,
    ) -> bool:
        """Sluit een voorgesteld voorstel af (`rejected`/`superseded`), append-only.

        `applied` loopt uitsluitend via `apply_source_proposal`.
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        handelend = self._eis_handelende_gebruiker(
            updated_by, "set_source_proposal_status"
        )
        if status not in _VOORSTEL_AFSLUITINGEN:
            msg = (
                f"status {status!r} niet toegestaan; alleen "
                f"{sorted(_VOORSTEL_AFSLUITINGEN)} (toepassen via apply_source_proposal)"
            )
            raise ValueError(msg)

        def _muteer(
            record: DefinitieRecord, voorstel: dict[str, Any]
        ) -> dict[str, Any] | None:
            voorstel["status"] = status
            voorstel.setdefault("events", []).append(
                {
                    "event": status,
                    "at": _nu(),
                    "actor": handelend,
                    "note": _tekst(note) or None,
                    "version_number": expected_version + 1,
                }
            )
            return {}

        return self._voorstel_bijwerken(
            definitie_id,
            proposal_id,
            updated_by=handelend,
            expected_version=expected_version,
            van_status=frozenset({"proposed"}),
            muteer=_muteer,
        )

    @staticmethod
    def _technische_validatiefout(
        validation: Mapping[str, Any], beoordeling: Mapping[str, Any]
    ) -> str | None:
        """Waarom het validatieresultaat technisch onbruikbaar is, of None.

        Volgt het bestaande resultaatcontract (DEF-621/DEF-624):
        `validation_unknown`, een niet-gerede regelset, dekking met `error`,
        een regel met status `error`, de bronregel (CON-02) zelf `error` of
        `not_evaluated`, of een niet-uitgevoerde AI-bronbeoordeling is geen
        inhoudelijk oordeel over de kandidaat. Een `not_evaluated` van een
        ándere regel is in het bestaande contract de reguliere uitkomst bij
        een ontbrekende optionele invoer (bv. SAM-regels zonder voorbeelden
        bij tekstvalidatie) en geen technische storing; die dekking blijft
        zichtbaar in het bewaarde resultaat.
        """
        resultaatfout = _technische_resultaatfout(validation)
        if resultaatfout is not None:
            return resultaatfout
        regelfout = _technische_regelfout(validation)
        if regelfout is not None:
            return regelfout
        if beoordeling.get("status") != "assessed":
            return f"source_assessment.status={beoordeling.get('status')!r}"
        return None

    def _beoordeling_voor_toepassing(
        self, validation: dict[str, Any], source_assessment: dict[str, Any] | None
    ) -> tuple[dict[str, Any] | None, Voorsteltoepassing | None]:
        """De bronbeoordeling voor het toepassen, of de reden waarom niet.

        Vóór de transactie: de beoordeling uit het resultaat (1.4.0) en een
        expliciet meegegeven beoordeling moeten gelijk zijn; er moet een
        beoordeling met vingerafdruk zijn; het resultaat mag technisch niet
        onbruikbaar zijn. Geeft (beoordeling, None) of (None, uitkomst).
        """
        uit_resultaat = validation.get("source_assessment")
        if (
            uit_resultaat is not None
            and source_assessment is not None
            and (uit_resultaat != source_assessment)
        ):
            return None, Voorsteltoepassing(
                "assessment_not_bound",
                reason="source_assessment in het resultaat en de meegegeven beoordeling verschillen",
            )
        beoordeling = uit_resultaat if uit_resultaat is not None else source_assessment
        if not isinstance(beoordeling, dict) or not _tekst(
            beoordeling.get("fingerprint")
        ):
            return None, Voorsteltoepassing(
                "assessment_not_bound",
                reason="geen bronbeoordeling met vingerafdruk voor de kandidaat",
            )
        technisch = self._technische_validatiefout(validation, beoordeling)
        if technisch is not None:
            return None, Voorsteltoepassing(
                "technical_error",
                reason=f"validatie technisch onbruikbaar: {technisch}",
            )
        return beoordeling, None

    @staticmethod
    def _vind_toepasbaar_voorstel(
        current: DefinitieRecord, proposal_id: str, expected_version: int
    ) -> tuple[list[Any], dict[str, Any]] | Voorsteltoepassing:
        """Ónder de lock: versieguard, voorstel opzoeken, status `proposed`."""
        if current.version_number != expected_version:
            return Voorsteltoepassing(
                "version_conflict",
                version_number=current.version_number,
                reason=(
                    f"record is versie {current.version_number}, verwacht "
                    f"{expected_version}"
                ),
            )
        registratie = current.get_generatieregistratie() or {}
        voorstellen = registratie.get(SOURCE_PROPOSALS_KEY)
        voorstellen = voorstellen if isinstance(voorstellen, list) else []
        voorstel = next(
            (
                v
                for v in voorstellen
                if isinstance(v, dict) and v.get("proposal_id") == proposal_id
            ),
            None,
        )
        if voorstel is None:
            return Voorsteltoepassing("not_found", reason="voorstel onbekend")
        if voorstel.get("status") != "proposed":
            return Voorsteltoepassing(
                "invalid_status",
                reason=f"voorstel heeft status {voorstel.get('status')!r}",
            )
        return voorstellen, voorstel

    def _controleer_origineel_en_binding(
        self,
        current: DefinitieRecord,
        voorstellen: list[Any],
        voorstel: dict[str, Any],
        beoordeling: dict[str, Any],
    ) -> _Toepassingsinvoer | Voorsteltoepassing:
        """Ónder de lock: origineel nog actueel en beoordeling gebonden aan de kandidaat."""
        huidig = current.get_source_evidence()
        origineel = voorstel.get("original") or {}
        if huidig is None or huidig.get("generation_identity") != voorstel.get(
            "generation_identity"
        ):
            return Voorsteltoepassing(
                "stale_original",
                reason="bronbewijs hoort niet meer bij de generatie van het voorstel",
            )
        if origineel.get("text") != current.get_definitie_tekst():
            return Voorsteltoepassing(
                "stale_original",
                reason="de definitietekst is sinds het voorstel gewijzigd",
            )
        if origineel.get("fingerprint") != self._bronvingerafdruk(
            current, bewijs=huidig
        ):
            return Voorsteltoepassing(
                "stale_original",
                reason="term, context, bronset of peildatum is sinds het voorstel gewijzigd",
            )
        kandidaat = _tekst((voorstel.get("outcome") or {}).get("candidate_text"))
        if not kandidaat:
            return Voorsteltoepassing(
                "invalid_status", reason="voorstel zonder kandidaattekst"
            )
        if beoordeling["fingerprint"] != self._bronvingerafdruk(
            current, tekst=kandidaat, bewijs=huidig
        ):
            return Voorsteltoepassing(
                "assessment_not_bound",
                reason="bronbeoordeling is niet gebonden aan de voorgestelde kandidaat",
            )
        return _Toepassingsinvoer(voorstellen, voorstel, huidig, kandidaat)

    def _registratie_na_toepassing(
        self,
        current: DefinitieRecord,
        invoer: _Toepassingsinvoer,
        beoordeling: dict[str, Any],
        validation: dict[str, Any],
        handelend: str,
        expected_version: int,
    ) -> str:
        """De generatieregistratie-JSON ná toepassing; zet ook de nieuwe issues op `current`.

        Nieuw bewijs (oud → historie), voorstel `applied` mét het volledige
        validatieresultaat en de vorige gewone issues (reviewbevinding 1),
        en de gewone `validation_issues` van `current` vervangen door die van
        de nieuwe kandidaat (markers blijven).
        """
        huidig = invoer.huidig
        nieuw = bouw_bronbewijs(
            begrip=current.begrip,
            definitie_tekst=invoer.kandidaat,
            contexten=current.get_contextlijsten(),
            sources=huidig["sources"],
            source_receipt=huidig.get("source_receipt"),
            source_assessment=beoordeling,
            peildatum=huidig.get("peildatum"),
            origin="proposal_applied",
            version_number=expected_version + 1,
            recorded_by=handelend,
            generation_identity=huidig.get("generation_identity"),
            generation_id=huidig.get("generation_id"),
        )
        registratie = self._registratie_met_nieuw_bewijs(current, huidig, nieuw)
        nu = _nu()
        # Reviewbevinding 1: de issues van de nieuwe kandidaat worden in
        # dezelfde UPDATE actueel; de oude gewone issues gaan als historie
        # mee in het voorstel. De CON-01-/CON-02-markers blijven staan en
        # vervallen door versie/vingerafdruk (bestaand patroon).
        vorige_issues = current.get_gewone_validation_issues()
        current.vervang_gewone_validation_issues(
            issues_uit_validatieresultaat(validation)
        )
        voorstel = invoer.voorstel
        voorstel["status"] = "applied"
        voorstel["applied"] = {
            "applied_at": nu,
            "actor": handelend,
            "version_number": expected_version + 1,
            "assessment_fingerprint": beoordeling["fingerprint"],
            "validation": deepcopy(validation),
            "previous_validation_issues": vorige_issues,
        }
        voorstel.setdefault("events", []).append(
            {
                "event": "applied",
                "at": nu,
                "actor": handelend,
                "version_number": expected_version + 1,
            }
        )
        registratie[SOURCE_PROPOSALS_KEY] = invoer.voorstellen
        return serialiseer_generatieregistratie(registratie)

    def apply_source_proposal(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        updated_by: str,
        expected_version: int,
        validation: dict[str, Any],
        source_assessment: dict[str, Any] | None = None,
    ) -> Voorsteltoepassing:
        """Pas een voorgesteld voorstel atomair toe (freeze punt 5).

        In één transactie en onder de versieguard: het opgeslagen voorstel is
        `proposed`, hoort bij de actuele generatie, en het origineel (tekst +
        bronvingerafdruk) is nog het actuele record; het volledige
        validatieresultaat is technisch bruikbaar en de bronbeoordeling
        daarin bindt via de vingerafdruk aan de VOORGESTELDE kandidaat met de
        opgeslagen bronset. Dan in dezelfde UPDATE: nieuwe tekst (toelichting
        opnieuw ingebed), nieuw bewijs (oud → historie), voorstel `applied`
        mét het volledige validatieresultaat, `validation_score` van het
        nieuwe resultaat. Model- en validatie-aanroepen gebeuren buiten de
        lock (pakket F); hier wordt alleen de eindcommit bewaakt. Een
        technische validatiefout schrijft nooit nieuwe tekst.
        """
        expected_version = self._eis_versienummer(expected_version, "expected_version")
        handelend = self._eis_handelende_gebruiker(updated_by, "apply_source_proposal")
        if not isinstance(validation, dict):
            msg = "apply_source_proposal vereist `validation`: het volledige validatieresultaat (dict)"
            raise ValueError(msg)
        beoordeling, afwijzing = self._beoordeling_voor_toepassing(
            validation, source_assessment
        )
        if beoordeling is None or afwijzing is not None:
            return afwijzing or Voorsteltoepassing(
                "assessment_not_bound",
                reason="geen bronbeoordeling met vingerafdruk voor de kandidaat",
            )

        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current:
                return Voorsteltoepassing("not_found", reason="definitie onbekend")
            gevonden = self._vind_toepasbaar_voorstel(
                current, proposal_id, expected_version
            )
            if isinstance(gevonden, Voorsteltoepassing):
                return gevonden
            voorstellen, voorstel = gevonden
            invoer = self._controleer_origineel_en_binding(
                current, voorstellen, voorstel, beoordeling
            )
            if isinstance(invoer, Voorsteltoepassing):
                return invoer
            registratie_json = self._registratie_na_toepassing(
                current, invoer, beoordeling, validation, handelend, expected_version
            )
            _, toelichting = splits_definitietekst(current.definitie or "")
            nieuwe_tekst = (
                f"{invoer.kandidaat}{TOELICHTING_SCHEIDING} {toelichting}"
                if toelichting
                else invoer.kandidaat
            )
            ok = self.update_definitie(
                definitie_id,
                {
                    "definitie": nieuwe_tekst,
                    "generation_prompt_data": registratie_json,
                    "validation_score": validation.get("overall_score"),
                    "validation_issues": current.validation_issues,
                    "version_number": expected_version,
                },
                handelend,
            )
            if not ok:
                return Voorsteltoepassing(
                    "version_conflict", reason="record gewijzigd tijdens toepassen"
                )
            return Voorsteltoepassing("applied", version_number=expected_version + 1)

    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        """Haal definitie op op basis van ID.

        DEF-391: kale connectie (geen committende ``with conn:``) zodat een read
        binnen een lopende transaction() die transactie niet vroegtijdig sluit.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT * FROM definities WHERE id = ?", (definitie_id,))
        row = cursor.fetchone()

        if row:
            return self._audit.row_to_record(row)
        return None

    def find_definitie(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        status: DefinitieStatus | None = None,
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> DefinitieRecord | None:
        """Zoek de leidende definitie op begrip (of synoniem) en gelijke context.

        DEF-622 (B-03): de vergelijking loopt over de genormaliseerde
        volledige contextverzameling (`zoek_gelijke_context`), niet over de
        ruwe JSON-strings. Bij meerdere treffers wint het vastgestelde record;
        daarna in beoordeling, dan concept, telkens de hoogste versie.
        Gearchiveerde records tellen alleen bij een expliciete statusvraag.
        """
        kandidaten = self._duplicates.zoek_gelijke_context(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            categorie=categorie,
            status=status,
        )
        for rij in kandidaten:
            if rij.id is None:
                continue
            record = self.get_definitie(int(rij.id))
            if record is not None:
                return record
        return None

    def update_definitie(
        self,
        definitie_id: int,
        updates: dict[str, Any],
        updated_by: str | None = None,
        _skip_audit: bool = False,
        _behoud_beoordeling: bool = False,
        _bronbinding_ongewijzigd: bool = False,
    ) -> bool:
        """Update bestaande definitie.

        ``_behoud_beoordeling`` is voorbehouden aan de atomaire vaststelactie
        (`change_status(..., ESTABLISHED)`): alleen dáár groeit een geldig
        gebonden CON-01-beoordeling mee naar de nieuwe versie. Elke andere
        wijziging — ook zonder tekstwijziging — laat de versiegebonden
        beoordeling vervallen (tweede deltareview V2c).

        DEF-743: de sleutel ``source_evidence`` (geen kolom) draagt nieuwe
        bronbewijs-invoer; die wordt ónder de schrijflock samengevoegd met de
        opgeslagen generatieregistratie (`_bronbewijs_samenvoegen`). De
        CON-02-beoordeling groeit — anders dan CON-01 — mee zolang term,
        tekst, context en bronset ongewijzigd blijven (`_meegroeiende_
        bronbeoordeling`); ``_bronbinding_ongewijzigd`` zegt dat een ruwe
        `generation_prompt_data`-schrijfactie de bronset niet raakt (interne
        herbeoordelings-/voorstelroutes).
        """
        current = self.get_definitie(definitie_id)
        if not current:
            return False

        updates = dict(updates)
        bewijsinvoer = updates.pop("source_evidence", None)

        allowed_fields = {
            "begrip",
            "definitie",
            "bron",
            "status",
            "categorie",
            "ufo_categorie",
            "ontologie",
            "validated",
            "validation_notes",
            # DEF-621: zonder dit veld werd een bijgewerkte score stil
            # genegeerd - de kolom bleef op de waarde van een eerdere,
            # inmiddels vervangen definitietekst staan. `None` hoort hier
            # net zo goed te landen als een float: het is de expliciete
            # vastlegging dat er geen oordeel is.
            "validation_score",
            # DEF-622: de CON-01-expertbeoordeling reist in dit veld mee;
            # zonder dit veld kon een beoordeling nooit worden bijgewerkt.
            "validation_issues",
            "reviewed_by",
            "review_date",
            "improved_version",
            "context_info",
            "metadata",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "toelichting_proces",
            "ketenpartners",
            "approved_by",
            "approved_at",
            "approval_notes",
            # DEF-743: het bronbewijs reist in de generatieregistratie mee;
            # zonder dit veld kon bewijs/historie/voorstel nooit worden
            # bijgewerkt. Servicecallers gebruiken de structurele sleutel
            # `source_evidence`; dit ruwe veld is voor de interne routes.
            "generation_prompt_data",
        }

        velden: dict[str, Any] = {
            field: value
            for field, value in updates.items()
            if hasattr(current, field) and field in allowed_fields
        }

        if not velden and bewijsinvoer is None:
            return False

        expected_version = updates.get("version_number")

        where_clause = "id = ?"
        where_params: list[Any] = [definitie_id]
        if expected_version is not None:
            where_clause += " AND version_number = ?"
            where_params.append(expected_version)

        # DEF-391: UPDATE + audit-log atomair (all-or-nothing).
        with self._db.transaction() as conn:
            # DEF-622 (B-03/B-10): de invariant "maximaal één vastgesteld
            # record per begrip + volledige context" wordt hier, ónder de
            # schrijflock, hercontroleerd op de resulterende staat. Zo kan
            # geen enkele schrijfroute (statuswijziging, begrip-/context-
            # wijziging van een vastgesteld record, gelijktijdige poging) er
            # omheen. Categorie is bewust geen onderdeel van de identiteit.
            # Verse lezing ónder de lock: `current` van vóór de transactie kan
            # door een gelijktijdige vaststelling verouderd zijn.
            actueel = self.get_definitie(definitie_id) or current
            self._bewaak_vaststelinvariant(definitie_id, actueel, updates)

            # DEF-743: bronbewijs samenvoegen ónder de lock — gelijk bewijs is
            # geen wijziging; gewijzigd bewijs gaat met historie in dezelfde
            # UPDATE. Een serialisatiefout laat de hele update falen.
            bronnen_gewijzigd, niets_te_schrijven = self._verwerk_bewijsinvoer(
                actueel, updates, bewijsinvoer, velden, updated_by
            )
            if niets_te_schrijven:
                return False

            # DEF-622 (deltareview V2c): uitsluitend de atomaire vaststelactie
            # neemt de gebonden CON-01-beoordeling in dezelfde UPDATE mee naar
            # de nieuwe versie; anders zou de vaststelling haar eigen, zojuist
            # geldige beoordeling door de statusversiebump laten vervallen.
            # Geen generieke verlengingsregel: elke andere update laat de
            # versiegebonden beoordeling vervallen.
            meegroeiend = (
                self._meegroeiende_beoordeling(actueel, updates)
                if _behoud_beoordeling
                else None
            )
            if meegroeiend is not None:
                velden["validation_issues"] = meegroeiend

            # DEF-743: de CON-02-beoordeling bindt aan term/tekst/context/
            # bronset. Raakt deze update die niet (status, CON-01-review,
            # herbeoordeling), dan groeit een geldig gebonden beoordeling mee;
            # anders vervalt zij door de versiebump en herleeft nooit.
            self._behoud_bronbinding(
                actueel, updates, velden, bronnen_gewijzigd, _bronbinding_ongewijzigd
            )

            set_clauses = [f"{field} = ?" for field in velden]
            params: list[Any] = list(velden.values())
            set_clauses.append("updated_at = ?")
            params.append(datetime.now(UTC))
            if updated_by:
                set_clauses.append("updated_by = ?")
                params.append(updated_by)
            set_clauses.append("version_number = version_number + 1")
            query = (
                "UPDATE definities SET "
                + ", ".join(set_clauses)
                + f" WHERE {where_clause}"
            )

            cursor = conn.execute(query, params + where_params)
            if cursor.rowcount == 0 and expected_version is not None:
                logger.warning(
                    f"Optimistic lock failed for definitie {definitie_id} (expected version {expected_version})"
                )
                return False

            if not _skip_audit:
                self._audit.log_geschiedenis(
                    definitie_id,
                    "updated",
                    updated_by,
                    f"Definitie geupdate: {list(updates.keys())}",
                )

        logger.info(f"Updated definitie {definitie_id}")
        return True

    def change_status(
        self,
        definitie_id: int,
        new_status: DefinitieStatus,
        changed_by: str | None = None,
        notes: str | None = None,
        *,
        ketenpartners: list[str] | None = None,
        ufo_categorie: str | Unset | None = UNSET,
        expected_version: int | None = None,
    ) -> bool:
        """Wijzig status van definitie in één UPDATE (één versiebump).

        DEF-482: ``ketenpartners`` en ``ufo_categorie`` liften mee in dezelfde
        UPDATE als de status; ``ufo_categorie=""`` maakt de kolom leeg, weglaten
        (``UNSET``) laat haar staan. ``expected_version`` is de optimistic lock:
        wijkt de opgeslagen versie af, dan wordt niets geschreven en is het
        resultaat ``False``.
        """
        updates: dict[str, Any] = {"status": new_status.value}

        if new_status == DefinitieStatus.ESTABLISHED and changed_by:
            updates.update(
                {
                    "approved_by": changed_by,
                    "approved_at": datetime.now(UTC),
                    "approval_notes": notes,
                }
            )
        if ketenpartners is not None:
            updates["ketenpartners"] = json.dumps(
                list(ketenpartners), ensure_ascii=False
            )
        if not isinstance(ufo_categorie, Unset):
            updates["ufo_categorie"] = ufo_categorie or None
        if expected_version is not None:
            updates["version_number"] = expected_version

        # DEF-391: status-UPDATE + audit-log atomair. update_definitie opent zelf
        # een transaction() die hier aansluit (nesting-guard) i.p.v. apart te
        # committen, zodat de statuswijziging en de audit-trail all-or-nothing zijn.
        with self._db.transaction():
            success = self.update_definitie(
                definitie_id,
                updates,
                changed_by,
                _skip_audit=True,
                # Alleen de vaststelling neemt een geldig gebonden CON-01-
                # beoordeling mee (DEF-622, V2c); andere statusacties niet.
                _behoud_beoordeling=new_status == DefinitieStatus.ESTABLISHED,
            )

            if success:
                # DEF-622 (B-10): een notitie bij een statuswijziging — zoals
                # de verwijzing naar de opvolger bij archivering — hoort in
                # de reguliere statusaudit.
                reden = f"Status gewijzigd naar {new_status.value}"
                if notes and notes.strip():
                    reden += f": {notes.strip()}"
                self._audit.log_geschiedenis(
                    definitie_id, "status_changed", changed_by, reden
                )

        return success

    def get_all(self) -> list[DefinitieRecord]:
        """Haal alle definities op zonder limit."""
        return self._search.search_definities(limit=None)

    def get_by_status(self, status: str) -> list[DefinitieRecord]:
        """Haal definities op gefilterd op status."""
        try:
            status_enum = DefinitieStatus(status)
        except ValueError as e:
            valid_statuses = ", ".join([s.value for s in DefinitieStatus])
            raise ValueError(
                f"Ongeldige status '{status}'. Toegestane waarden: {valid_statuses}"
            ) from e

        return self._search.search_definities(status=status_enum, limit=None)
