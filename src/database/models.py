"""Data models voor de database laag.

Bevat de dataclasses en enums die door alle database sub-modules
en service-lagen worden gebruikt.
"""

import hashlib
import json
import logging
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast

from domain.context.normalisatie import contextsleutel, lees_contextwaarden

logger = logging.getLogger(__name__)


def normalize_wettelijke_basis(basis: list[str] | None) -> str:
    """Normaliseer wettelijke basis naar gesorteerde, unieke JSON string."""
    try:
        norm = sorted({str(x).strip() for x in (basis or [])})
        return json.dumps(norm, ensure_ascii=False)
    except Exception as e:
        logger.debug(f"Wettelijke basis normalisatie gefaald, gebruik raw dump: {e}")
        return json.dumps(basis or [], ensure_ascii=False)


class VaststelconflictError(ValueError):
    """Er is al een vastgesteld, leidend record voor dit begrip en deze context.

    DEF-622 (B-03/B-10): maximaal één vastgestelde definitie per begrip +
    volledige genormaliseerde context, ongeacht categorie. Wordt op de
    persistentiegrens gegooid, zodat geen enkele schrijfroute er stil omheen
    kan. Vervanging is een bewuste keuze in `DefinitionWorkflowService`.
    """

    def __init__(self, message: str, conflict_id: int | None = None) -> None:
        super().__init__(message)
        self.conflict_id = conflict_id


#: Marker van de vastgelegde CON-01-expertbeoordeling in `validation_issues`.
CONTEXT_REVIEW_CODE = "CON-01-REVIEW"

#: Marker van de vastgelegde CON-02-deskundigenuitzondering in `validation_issues`
#: (DEF-743). Payload: het `source_review`-schema van het kerncontract (§5).
SOURCE_REVIEW_CODE = "CON-02-REVIEW"

#: Sleutels in `generation_prompt_data` (DEF-743): actueel bronbewijs, de
#: append-only historie van vervangen bewijsdocumenten en de herstelvoorstellen.
SOURCE_EVIDENCE_KEY = "source_evidence"
SOURCE_EVIDENCE_HISTORY_KEY = "source_evidence_history"
SOURCE_PROPOSALS_KEY = "source_proposals"
SOURCE_REVIEW_HISTORY_KEY = "source_review_history"
SOURCE_EVIDENCE_SCHEMA = "def743-bronbewijs/2"

#: De drie contextvelden zoals het bewijs ze vastlegt (zelfde namen als het record).
_CONTEXTVELDEN: tuple[str, ...] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)


def lees_generatieregistratie(ruw: str | None) -> dict[str, Any] | None:
    """De `generation_prompt_data`-JSON als dict, of None (leeg/misvormd/geen dict)."""
    if not ruw:
        return None
    try:
        data = json.loads(ruw)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def serialiseer_generatieregistratie(registratie: dict[str, Any]) -> str:
    """Strikte JSON-serialisatie van de generatieregistratie.

    Bewust zonder `default=str`: een niet-serialiseerbaar bronobject wordt een
    zichtbare `ValueError` en laat de opslag falen. Bronbewijs wordt nooit
    stil weggelaten of verminkt (DEF-743).
    """
    try:
        return json.dumps(registratie, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        msg = f"bronbewijs niet serialiseerbaar: {e}"
        raise ValueError(msg) from e


def issues_uit_validatieresultaat(validation: Any) -> list[dict[str, Any]]:
    """Vertaal de `violations` van een validatieresultaat naar `validation_issues`.

    Dezelfde itemvorm als de bestaande lezers gebruiken (experttab, gate,
    CLI, export): `code`, `rule_id`, `severity`, `description`, plus
    `category`/`location`/`suggestions` wanneer aanwezig. Niets wordt
    verzonnen: een ontbrekend veld blijft leeg.
    """
    if not isinstance(validation, dict):
        return []
    items: list[dict[str, Any]] = []
    for violation in validation.get("violations") or []:
        if not isinstance(violation, dict):
            continue
        item: dict[str, Any] = {
            "code": violation.get("code") or violation.get("rule_id") or "",
            "rule_id": violation.get("rule_id") or violation.get("code") or "",
            "severity": violation.get("severity") or "",
            "description": (
                violation.get("message") or violation.get("description") or ""
            ),
        }
        for extra in ("category", "location", "suggestions"):
            if violation.get(extra) is not None:
                item[extra] = deepcopy(violation[extra])
        items.append(item)
    return items


#: De tekststadia van de kandidaat die het bewijs zelfstandig meedraagt
#: (dezelfde sleutels als de DEF-622-generatieregistratie).
KANDIDAATSTADIA: tuple[str, ...] = (
    "definitie_origineel",
    "definitie_kern_geextraheerd",
    "definitie_eindtekst",
    "tekst_na_generatie_aangepast",
)


def generatie_identiteit(
    begrip: str,
    kandidaat: str,
    sources: list[Any],
    generated_at: Any,
) -> str:
    """Stabiele identiteit van één oorspronkelijke generatie (DEF-743, max 1 voorstel).

    sha256 over begrip, de gegenereerde kandidaat, de exacte aangeleverde
    bronlijst en het generatietijdstip. Bewust zónder recordversie,
    beoordeling of status: die veranderen, de generatie niet. Een expliciete
    `generation_id` in de metadata wint (zie `bouw_bronbewijs`).
    """
    try:
        basis = {
            "begrip": str(begrip or ""),
            "kandidaat": str(kandidaat or ""),
            "generated_at": generated_at if isinstance(generated_at, str) else None,
            "sources": [
                hashlib.sha256(
                    json.dumps(bron, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()
                for bron in sources
            ],
        }
        return hashlib.sha256(
            json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError) as e:
        msg = f"bronbewijs niet serialiseerbaar: {e}"
        raise ValueError(msg) from e


def bouw_bronbewijs(
    *,
    begrip: str,
    definitie_tekst: str,
    contexten: dict[str, list[str]],
    sources: list[Any],
    source_receipt: Any,
    source_assessment: Any,
    peildatum: Any,
    origin: str,
    version_number: int,
    recorded_by: str | None,
    generation_identity: str | None = None,
    generation_id: Any = None,
    generated_at: Any = None,
    tekststadia: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Het zelfstandige bronbewijsdocument (`source_evidence`, DEF-743 §2).

    Alles wordt deepcopied: geneste bronmetadata blijft onafhankelijk van de
    invoer. Alleen aanwezige tekststadia worden opgenomen; niets wordt
    verzonnen.
    """
    kandidaat: dict[str, Any] = {"definitie": str(definitie_tekst or "")}
    for veld in KANDIDAATSTADIA:
        if tekststadia and tekststadia.get(veld) is not None:
            kandidaat[veld] = deepcopy(tekststadia[veld])
    bronnen = deepcopy(list(sources))
    # Volgorde: een expliciet doorgegeven (bewaarde) identiteit wint — een
    # correctie of herbeoordeling is geen nieuwe generatie; daarna de
    # expliciete generatie-id van de kern; pas dan de afgeleide identiteit.
    identiteit = generation_identity
    if not identiteit and isinstance(generation_id, str) and generation_id.strip():
        identiteit = f"generation_id:{generation_id.strip()}"
    if not identiteit:
        identiteit = generatie_identiteit(
            begrip,
            (tekststadia or {}).get("definitie_eindtekst") or definitie_tekst,
            bronnen,
            generated_at,
        )
    return {
        "schema": SOURCE_EVIDENCE_SCHEMA,
        "origin": origin,
        "generation_identity": identiteit,
        "version_number": version_number,
        "recorded_at": datetime.now(UTC).isoformat(),
        "recorded_by": recorded_by,
        "begrip": str(begrip or ""),
        "peildatum": peildatum if isinstance(peildatum, str) else None,
        "candidate": kandidaat,
        "context": {veld: list(contexten.get(veld) or []) for veld in _CONTEXTVELDEN},
        "sources": bronnen,
        "source_receipt": deepcopy(source_receipt),
        "source_assessment": deepcopy(source_assessment),
        # De expliciete generatie-id (kern C) blijft ruw bewaard zodat herladen
        # hem kan terugzetten; nooit afgeleid of verzonnen.
        "generation_id": (
            generation_id.strip()
            if isinstance(generation_id, str) and generation_id.strip()
            else None
        ),
    }


@dataclass(frozen=True)
class Voorstelreservering:
    """Uitkomst van `reserve_source_proposal` (DEF-743, pakket F).

    `status`: `reserved` | `version_conflict` | `attempt_consumed` |
    `no_evidence` | `not_found`. Bij `reserved` is `version_number` de nieuwe
    recordversie; bij `attempt_consumed` verwijst `proposal_id` naar de al
    verbruikte poging.
    """

    status: str
    proposal_id: str | None = None
    version_number: int | None = None
    generation_identity: str | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "reserved"


@dataclass(frozen=True)
class Voorsteltoepassing:
    """Uitkomst van `apply_source_proposal` (DEF-743, pakket F).

    `status`: `applied` | `version_conflict` | `not_found` | `invalid_status` |
    `stale_original` | `assessment_not_bound` | `technical_error`. Alleen bij
    `applied` is er geschreven; `version_number` is dan de nieuwe recordversie.
    """

    status: str
    version_number: int | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "applied"


@dataclass(frozen=True)
class Bronmetadatatoepassing:
    """Uitkomst van `vul_bronmetadata_aan` (DEF-808).

    `status`: `applied` | `version_conflict` | `not_found` | `no_evidence` |
    `no_matching_source`. Alleen bij `applied` is er geschreven;
    `version_number` is dan de nieuwe recordversie en `aantal_bronnen` het
    aantal documentpassages dat de opgave kreeg.
    """

    status: str
    version_number: int | None = None
    reason: str | None = None
    aantal_bronnen: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "applied"


# Scheiding waarmee de servicelaag een toelichting in de kolom `definitie`
# inbedt; de enige plek waar die conventie is vastgelegd.
TOELICHTING_SCHEIDING = "\n\nToelichting:"


def splits_definitietekst(tekst: str) -> tuple[str, str | None]:
    """Splits een recordtekst in (definitiezin, toelichting-of-None)."""
    if TOELICHTING_SCHEIDING not in tekst:
        return tekst, None
    zin, toelichting = tekst.split(TOELICHTING_SCHEIDING, 1)
    return zin, toelichting.strip() or None


class DefinitieStatus(Enum):
    """Status van een definitie in het systeem."""

    IMPORTED = "imported"
    DRAFT = "draft"
    REVIEW = "review"
    ESTABLISHED = "established"
    ARCHIVED = "archived"


class SourceType(Enum):
    """Type van de bron waaruit definitie komt."""

    GENERATED = "generated"
    IMPORTED = "imported"
    MANUAL = "manual"


@dataclass
class DefinitieRecord:
    """Representatie van een definitie record in de database."""

    # Basis definitie informatie
    id: int | None = None
    begrip: str = ""
    definitie: str = ""
    categorie: str = ""
    organisatorische_context: str = ""
    juridische_context: str | None = ""
    wettelijke_basis: str | None = None
    ufo_categorie: str | None = None

    # Procesmatige velden
    toelichting_proces: str | None = None

    # Status en versioning
    status: str = DefinitieStatus.DRAFT.value
    version_number: int = 1
    previous_version_id: int | None = None

    # Validation
    validation_score: float | None = None
    validation_date: datetime | None = None
    validation_issues: str | None = None

    # Source tracking
    source_type: str = SourceType.GENERATED.value
    source_reference: str | None = None
    imported_from: str | None = None

    # Voorkeursterm (single source of truth op definitie-niveau)
    voorkeursterm: str | None = None

    # Metadata
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    # Legacy metadata fields
    datum_voorstel: datetime | None = None
    ketenpartners: str | None = None

    # Approval
    approved_by: str | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None

    # Export
    last_exported_at: datetime | None = None
    export_destinations: str | None = None

    # Generation Prompt Storage (DEF-151)
    generation_prompt_data: str | None = None

    # Deprecated
    voorkeursterm_is_begrip: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    def get_validation_issues_list(self) -> list[dict[str, Any]]:
        """Haal validation issues op als list."""
        if not self.validation_issues:
            return []
        try:
            return cast(list[dict[str, Any]], json.loads(self.validation_issues))
        except json.JSONDecodeError:
            return []

    def set_validation_issues(self, issues: list[dict[str, Any]]) -> None:
        """Set validation issues als JSON string."""
        self.validation_issues = json.dumps(issues, ensure_ascii=False)

    def get_definitie_tekst(self) -> str:
        """De definitiezin: de recordtekst zonder ingebedde toelichting.

        De kolom `definitie` kan `"<zin>\\n\\nToelichting: <toelichting>"`
        bevatten (servicelaag). Het CON-01-contract, de vaststelgate, de
        experttab, readback en validatie gebruiken allemaal déze tekstbasis,
        zodat één beoordeling overal dezelfde vingerafdruk heeft (DEF-622,
        koppelingenbevinding K4).
        """
        return splits_definitietekst(self.definitie or "")[0]

    def get_contextlijsten(self) -> dict[str, list[str]]:
        """De drie opgeslagen contextlijsten, gelezen zoals het contract ze leest."""
        return {
            "organisatorische_context": lees_contextwaarden(
                self.organisatorische_context
            ),
            "juridische_context": lees_contextwaarden(self.juridische_context),
            "wettelijke_basis": lees_contextwaarden(self.wettelijke_basis),
        }

    def get_contractvelden(self) -> dict[str, Any]:
        """De CON-01- én CON-02-contractvelden zoals dit opgeslagen record ze draagt.

        Eén adapter voor vaststelgate, experttab, export en herhaalde
        validatie (koppelingenbevindingen K2/K3): de drie contextlijsten,
        id, recordversie, de vastgelegde CON-01-beoordeling en (DEF-743) de
        opgeslagen bronset, AI-bronbeoordeling, deskundigenuitzondering en
        peildatum komen uitsluitend van het record — een aanroeper kan ze
        niet vervangen. `provenance_sources` is de canonieke sleutel voor de
        validatiecontext, `sources` de legacy-alias; beide dragen dezelfde
        (onafhankelijke) kopie. Zonder opgeslagen bewijs ontbreken de
        bronsleutels: er wordt niets verzonnen.
        """
        velden: dict[str, Any] = {
            **self.get_contextlijsten(),
            "definition_id": self.id,
            "definition_version": self.version_number,
            "context_review": self.get_context_review(),
            "source_review": self.get_source_review(),
            "source_evidence_status": self.get_source_evidence_status(),
        }
        bewijs = self.get_source_evidence()
        if bewijs is not None:
            velden["sources"] = deepcopy(bewijs.get("sources") or [])
            velden["provenance_sources"] = deepcopy(bewijs.get("sources") or [])
            velden["source_assessment"] = deepcopy(bewijs.get("source_assessment"))
            velden["peildatum"] = bewijs.get("peildatum")
            # Reviewbevinding 4: de kwitantie (feitelijk brontransport) hoort
            # bij het contract — de voorsteldiagnose leest exact deze sleutel.
            velden["source_receipt"] = deepcopy(bewijs.get("source_receipt"))
        return velden

    # ----------------------------------------------------- bronbewijs (DEF-743)

    def get_generatieregistratie(self) -> dict[str, Any] | None:
        """De `generation_prompt_data`-JSON als dict (DEF-151), of None."""
        return lees_generatieregistratie(self.generation_prompt_data)

    def get_source_evidence(self) -> dict[str, Any] | None:
        """Het actuele bronbewijsdocument, of None (afwezig of misvormd).

        Bewaard onder `source_evidence` in de bestaande generatieregistratie
        (`generation_prompt_data`): geen schemawijziging. Alleen een
        welgevormd document telt — een misvormd document is expliciet
        ongeldig (`get_source_evidence_status`), nooit "de eerste gunstige".
        """
        registratie = self.get_generatieregistratie()
        if registratie is None:
            return None
        bewijs = registratie.get(SOURCE_EVIDENCE_KEY)
        if not isinstance(bewijs, dict) or not isinstance(bewijs.get("sources"), list):
            return None
        return deepcopy(bewijs)

    def get_source_evidence_status(self) -> dict[str, Any]:
        """`{"status", "current", "reason"}` van het bronbewijs.

        `status`: `present` (welgevormd bewijs), `reference_only` (alleen
        de korte `source_reference`, historisch record: onvolledig bewijs),
        `absent` (niets) of `invalid` (misvormd document in de kolom).
        `current`: het bewijs hoort structureel nog bij begrip, definitiezin
        en canonieke context van dít record. De gezaghebbende stale-bepaling
        (incl. bronidentiteit/peildatum/beleidsversie) is de bronvingerafdruk
        van het kerncontract in de evaluator; dit is de goedkope
        recordcontrole waarmee UI en export "niet meer actueel" kunnen tonen
        zonder AI of domeinhelper.
        """
        registratie = self.get_generatieregistratie()
        ruw = registratie.get(SOURCE_EVIDENCE_KEY) if registratie else None
        if ruw is None:
            if self.source_reference and str(self.source_reference).strip():
                return {"status": "reference_only", "current": False, "reason": None}
            return {"status": "absent", "current": False, "reason": None}
        bewijs = self.get_source_evidence()
        if bewijs is None:
            return {
                "status": "invalid",
                "current": False,
                "reason": "bronbewijs in generation_prompt_data is misvormd",
            }
        afwijkend = self._bewijsafwijkingen(bewijs)
        return {
            "status": "present",
            "current": not afwijkend,
            "reason": (
                "bewijs hoort bij een eerdere " + ", ".join(afwijkend)
                if afwijkend
                else None
            ),
        }

    def _bewijsafwijkingen(self, bewijs: dict[str, Any]) -> list[str]:
        """Welke recordvelden niet meer overeenkomen met het bewijs."""
        afwijkend: list[str] = []
        if str(bewijs.get("begrip") or "") != str(self.begrip or ""):
            afwijkend.append("begrip")
        kandidaat = bewijs.get("candidate")
        tekst = kandidaat.get("definitie") if isinstance(kandidaat, dict) else None
        if str(tekst or "") != self.get_definitie_tekst():
            afwijkend.append("definitie")
        context = bewijs.get("context")
        context = context if isinstance(context, dict) else {}
        actueel = self.get_contextlijsten()
        for veld in _CONTEXTVELDEN:
            if contextsleutel(context.get(veld)) != contextsleutel(actueel[veld]):
                afwijkend.append(veld)
        return afwijkend

    def get_source_evidence_history(self) -> list[dict[str, Any]]:
        """De append-only lijst van vervangen bewijsdocumenten (oud → nieuw)."""
        registratie = self.get_generatieregistratie() or {}
        historie = registratie.get(SOURCE_EVIDENCE_HISTORY_KEY)
        if not isinstance(historie, list):
            return []
        return [deepcopy(h) for h in historie if isinstance(h, dict)]

    def get_source_review_history(self) -> list[dict[str, Any]]:
        """Append-only historie van vervangen/verwijderde CON-02-reviews.

        Elke gebeurtenis draagt actor, tijd, recordversie, de vorige payload
        en haar status (present/stale/invalid) en de kandidaatbinding (tekst +
        bronvingerafdruk) op dat moment. Nooit herschreven of verwijderd.
        """
        registratie = self.get_generatieregistratie() or {}
        historie = registratie.get(SOURCE_REVIEW_HISTORY_KEY)
        if not isinstance(historie, list):
            return []
        return [deepcopy(h) for h in historie if isinstance(h, dict)]

    def get_gewone_validation_issues(self) -> list[dict[str, Any]]:
        """De validatie-issues zonder de CON-01-/CON-02-beoordelingsmarkers."""
        return [
            issue
            for issue in self.get_validation_issues_list()
            if not (
                isinstance(issue, dict)
                and issue.get("code") in (CONTEXT_REVIEW_CODE, SOURCE_REVIEW_CODE)
            )
        ]

    def vervang_gewone_validation_issues(self, issues: list[dict[str, Any]]) -> None:
        """Vervang de gewone issues; de beoordelingsmarkers blijven staan.

        De markers zijn de vastgelegde deskundigenbeoordelingen (CON-01/
        CON-02) met hun eigen versie-/vingerafdrukbinding; die vervallen bij
        een tekstwijziging maar worden niet weggegooid.
        """
        markers = [
            issue
            for issue in self.get_validation_issues_list()
            if isinstance(issue, dict)
            and issue.get("code") in (CONTEXT_REVIEW_CODE, SOURCE_REVIEW_CODE)
        ]
        self.set_validation_issues([*issues, *markers])

    def get_source_proposals(self) -> list[dict[str, Any]]:
        """De append-only lijst van herstelvoorstellen (DEF-743, pakket F)."""
        registratie = self.get_generatieregistratie() or {}
        voorstellen = registratie.get(SOURCE_PROPOSALS_KEY)
        if not isinstance(voorstellen, list):
            return []
        return [deepcopy(v) for v in voorstellen if isinstance(v, dict)]

    def get_source_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        """Eén voorstel op id, of None."""
        for voorstel in self.get_source_proposals():
            if voorstel.get("proposal_id") == proposal_id:
                return voorstel
        return None

    def _source_review_markers(self) -> list[dict[str, Any]]:
        return [
            issue
            for issue in self.get_validation_issues_list()
            if isinstance(issue, dict) and issue.get("code") == SOURCE_REVIEW_CODE
        ]

    def get_source_review(self) -> dict[str, Any] | None:
        """De vastgelegde CON-02-deskundigenuitzondering (DEF-743), of None.

        Eén markerelement (`code == SOURCE_REVIEW_CODE`) in `validation_issues`,
        naast de CON-01-marker. Meer dan één marker of een misvormde payload
        is fail-closed géén beoordeling — nooit de eerste of de gunstigste.
        De binding aan tekst/context/term/bronset zit in de vingerafdruk in
        de beoordeling zelf; de versiebinding in `version_number`.
        """
        markers = self._source_review_markers()
        if len(markers) != 1:
            return None
        review = markers[0].get("source_review")
        return deepcopy(review) if isinstance(review, dict) else None

    def get_source_review_status(self) -> dict[str, Any]:
        """`{"status", "reason"}`: `present`, `absent`, `invalid` of `stale`.

        `stale` = de beoordeling draagt niet het versienummer van dit record
        (tekst/context/bron is daarna gewijzigd zonder behoud van de binding).
        Een ongeldig getypeerd versienummer telt niet als gebonden (V2b).
        """
        markers = self._source_review_markers()
        if not markers:
            return {"status": "absent", "reason": None}
        if len(markers) > 1:
            return {
                "status": "invalid",
                "reason": f"{len(markers)} CON-02-beoordelingsmarkers: ambigu",
            }
        review = self.get_source_review()
        if review is None:
            return {"status": "invalid", "reason": "misvormde CON-02-beoordeling"}
        gebonden = review.get("version_number")
        if not (isinstance(gebonden, int) and not isinstance(gebonden, bool)):
            return {
                "status": "stale",
                "reason": "beoordeling draagt geen geldig versienummer",
            }
        if gebonden != self.version_number:
            return {
                "status": "stale",
                "reason": (
                    f"beoordeling hoort bij versie {gebonden}; het record is "
                    f"versie {self.version_number}"
                ),
            }
        return {"status": "present", "reason": None}

    def set_source_review(self, review: dict[str, Any] | None) -> None:
        """Vervang (of verwijder bij None) de CON-02-marker; overige issues blijven."""
        overig = [
            issue
            for issue in self.get_validation_issues_list()
            if not (isinstance(issue, dict) and issue.get("code") == SOURCE_REVIEW_CODE)
        ]
        if review is not None:
            overig.append(
                {
                    "code": SOURCE_REVIEW_CODE,
                    "rule_id": "CON-02",
                    "severity": "info",
                    "description": (
                        "Deskundigenuitzondering bronbasis (CON-02, "
                        f"{review.get('type') or 'onbekend type'}) door "
                        f"{review.get('actor') or 'onbekend'}"
                    ),
                    "source_review": deepcopy(review),
                }
            )
        self.set_validation_issues(overig)

    def get_context_review(self) -> dict[str, Any] | None:
        """De vastgelegde CON-01-expertbeoordeling van de naamfunctie (DEF-622).

        Bewaard als één markerelement (`code == CONTEXT_REVIEW_CODE`) in de
        bestaande `validation_issues`-lijst: geen schemawijziging, en de
        beoordeling reist mee met het record. De binding aan tekst/context/
        term zit in de vingerafdruk in de beoordeling zelf.
        """
        markers = [
            issue
            for issue in self.get_validation_issues_list()
            if isinstance(issue, dict) and issue.get("code") == CONTEXT_REVIEW_CODE
        ]
        if len(markers) != 1:
            # Geen marker: geen beoordeling. Meer dan één: ambigu, en een
            # ambigue beoordeling is fail-closed géén beoordeling
            # (reviewbevinding E3) — nooit de eerste of de gunstigste kiezen.
            return None
        review = markers[0].get("context_review")
        return dict(review) if isinstance(review, dict) else None

    def set_context_review(self, review: dict[str, Any] | None) -> None:
        """Vervang (of verwijder bij None) de vastgelegde CON-01-beoordeling."""
        overig = [
            issue
            for issue in self.get_validation_issues_list()
            if not (
                isinstance(issue, dict) and issue.get("code") == CONTEXT_REVIEW_CODE
            )
        ]
        if review is not None:
            overig.append(
                {
                    "code": CONTEXT_REVIEW_CODE,
                    "rule_id": "CON-01",
                    "severity": "info",
                    "description": (
                        "Expertbeoordeling van de naamfunctie (CON-01) door "
                        f"{review.get('actor') or 'onbekend'}"
                    ),
                    "context_review": dict(review),
                }
            )
        self.set_validation_issues(overig)

    def get_wettelijke_basis_list(self) -> list[str]:
        """Haal wettelijke basis op als list."""
        if not self.wettelijke_basis:
            return []
        try:
            return cast(list[str], json.loads(self.wettelijke_basis))
        except json.JSONDecodeError:
            return []

    def set_wettelijke_basis(self, basis: list[str]) -> None:
        """Set wettelijke basis als JSON string."""
        self.wettelijke_basis = normalize_wettelijke_basis(basis)

    def get_export_destinations_list(self) -> list[str]:
        """Haal export destinations op als list."""
        if not self.export_destinations:
            return []
        try:
            return cast(list[str], json.loads(self.export_destinations))
        except json.JSONDecodeError:
            return []

    def add_export_destination(self, destination: str) -> None:
        """Voeg export destination toe."""
        destinations = self.get_export_destinations_list()
        if destination not in destinations:
            destinations.append(destination)
            self.export_destinations = json.dumps(destinations)

    def get_ketenpartners_list(self) -> list[str]:
        """Haal ketenpartners op als list."""
        if not self.ketenpartners:
            return []
        try:
            return cast(list[str], json.loads(self.ketenpartners))
        except json.JSONDecodeError:
            return []

    def set_ketenpartners(self, partners: list[str]) -> None:
        """Set ketenpartners als JSON string."""
        self.ketenpartners = json.dumps(partners, ensure_ascii=False)


@dataclass
class VoorbeeldenRecord:
    """Representatie van een voorbeelden record in de database."""

    id: int | None = None
    definitie_id: int = 0
    voorbeeld_type: str = ""
    voorbeeld_tekst: str = ""
    voorbeeld_volgorde: int = 1
    is_voorkeursterm: bool = False

    # Generation metadata
    gegenereerd_door: str = "system"
    generation_model: str | None = None
    generation_parameters: str | None = None

    # Status
    actief: bool = True
    beoordeeld: bool = False
    beoordeeling: str | None = None
    beoordeeling_notities: str | None = None
    beoordeeld_door: str | None = None
    beoordeeld_op: datetime | None = None

    # Metadata
    aangemaakt_op: datetime | None = None
    bijgewerkt_op: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    def get_generation_parameters_dict(self) -> dict[str, Any]:
        """Haal generation parameters op als dictionary."""
        if not self.generation_parameters:
            return {}
        try:
            return cast(dict[str, Any], json.loads(self.generation_parameters))
        except json.JSONDecodeError:
            return {}

    def set_generation_parameters(self, params: dict[str, Any]) -> None:
        """Stel generatie parameters in als JSON string."""
        self.generation_parameters = json.dumps(params, ensure_ascii=False)


@dataclass
class DuplicateMatch:
    """Representatie van een mogelijk duplicaat match."""

    definitie_record: DefinitieRecord
    match_score: float
    match_reasons: list[str]
