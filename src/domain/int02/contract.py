"""INT-02 — beoordelingscontract def835-int02-assessment/3 (norm def771-int02/2).

Zuiver domein (DEF-835 WP1, plan-v1 §Ontwerpvoorstel): geen AI-client,
database of Streamlit. Een beoordelaar (model of mens) bepaalt per passage de
functie; deze code controleert alleen wat mechanisch controleerbaar is:

- **invoer**: exacte, onveranderlijke snapshot van begrip, kern, bevestigde
  bedoeling (`None` = expliciet onbekend), de drie contextlijsten en de
  aangeleverde bronpassages;
- **binding**: contract-, normversie en -hash, promptversie,
  routeringshash, gevraagde provider/model en hashes van begrip, kern,
  bedoeling, context en bronnen;
- **uitvoer**: een gesloten structuur (onbekende velden, verkeerde typen en
  bool-als-int worden geweigerd) met per passage- en grondcitaat alleen het
  letterlijke citaat en het veld;
- **posities**: door deze code afgeleid, nooit door de beoordelaar geleverd
  (/2, besluit 9 optie A). Een citaat moet precies één keer als exacte
  substring (Python-codepunten, geen normalisatie) in de kern of in het
  genoemde grondveld staan: `start` is die vindplaats, `end` = `start` +
  `len(quote)`, einde exclusief. Nul of meer vindplaatsen (ook overlappend)
  of een leeg citaat is `invalid_citation` met een `foutdetail`. Uitvoer die
  zelf `start`/`end` meelevert, heeft onbekende velden (`invalid_output`);
- **status**: de mapping uit synthese v5 §4 (pass, fail, review_required,
  not_evaluated, error, not_applicable), zonder cijfer, met exacte meldingen;
- **dienstregel discretie zonder bedoeling** (/3, besluit 12 optie A): geeft
  een model (actor `ai`) `fail`, is de bevestigde bedoeling onbekend en
  hebben alle passages die de fail dragen functie
  `discretionary_decision_rule` met uitsluitend het veld `kern` als grond,
  dan is de status `review_required` / `insufficient_information` met de
  vaste vraag `VRAAG_DISCRETIE_ZONDER_BEDOELING`. De omzetting staat
  zichtbaar in `Beoordelingsdocument.omzetting`; het bewaarde oordeel blijft
  de geaccepteerde uitvoer (verdict `fail`). Een actorvoorschrift of een
  andere grond houdt de fail in stand (besluit 1); er komt geen pass-pad bij.

Het bewaarde oordeel is de geaccepteerde uitvoer mét de afgeleide posities,
in dezelfde vorm als onder /1, zodat melding, UI en export ongewijzigd
werken. Een bewaard /1- of /2-document wordt bij replay nog volgens de regels
van zijn eigen versie op integriteit getoetst en is daarna historisch (niet
`error`). Ongeldige uitvoer wordt nooit gerepareerd en geeft `error`, nooit
fail of review_required. De code bewijst geen semantische juistheid of
volledigheid van de beoordeling. Opslag valt buiten dit contract (DEF-626).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any, cast

__all__ = [
    "CONTRACTVERSIE",
    "NORMVERSIE",
    "ONBEKEND",
    "Actualiteit",
    "Beoordelingsdocument",
    "Binding",
    "Bronpassage",
    "Configuratie",
    "Int02ContractError",
    "Int02Invoer",
    "Uitvoering",
    "beoordeel",
    "bereken_binding",
    "maak_invoer",
    "ontbrekende_invoer",
    "toets_actualiteit",
]

#: /1: posities door de beoordelaar. /2: posities door deze code afgeleid
#: (besluit 9, optie A). /3: plus de dienstregel discretie zonder bedoeling
#: (besluit 12, optie A). Documenten onder /1 en /2 zijn daardoor historisch.
CONTRACTVERSIE = "def835-int02-assessment/3"
#: Vorige versies. Een bewaard /1- of /2-document wordt volgens de regels van
#: zijn eigen versie op integriteit getoetst (`_herleidbaar`) en is daarna
#: historisch, geen error.
_CONTRACTVERSIE_V1 = "def835-int02-assessment/1"
_CONTRACTVERSIE_V2 = "def835-int02-assessment/2"
#: Versies waarvan een bewaard document herleidbaar kan zijn; andere → error.
_BEKENDE_CONTRACTVERSIES = frozenset(
    {_CONTRACTVERSIE_V1, _CONTRACTVERSIE_V2, CONTRACTVERSIE}
)
NORMVERSIE = "def771-int02/2"
#: Expliciete waarde voor een niet-gerapporteerde meting; nooit 0 of None.
ONBEKEND = "unknown"

STATUSSEN = frozenset(
    {"pass", "fail", "review_required", "not_evaluated", "error", "not_applicable"}
)
#: Redenen bij review_required: inhoudelijk onvoldoende informatie tegenover
#: nog niet beoordeeld tegenover historisch.
REDENEN = frozenset({"insufficient_information", "not_assessed", "historical"})

VERDICTS = frozenset({"pass", "fail", "insufficient_information", "not_applicable"})
BESCHRIJVEND = frozenset({"criterion", "derivation"})
GEBREK = frozenset({"actor_prescription", "discretionary_decision_rule"})
FUNCTIES = BESCHRIJVEND | GEBREK | {"unclear"}
ONZEKERHEDEN = frozenset({"none", "non_decisive", "decisive"})
DEKKINGEN = frozenset({"complete", "partial", "none"})

ACTOREN = frozenset({"ai", "human"})
UITVOERINGSSTATUSSEN = frozenset({"completed", "failed", "not_executed"})
#: Door transport of provider gemelde fouten; alleen bij status `failed`.
TRANSPORTFOUTEN = frozenset({"timeout", "transport", "provider"})
#: Door deze code vastgestelde fouten in de uitvoer.
FOUT_UITVOER = "invalid_output"
FOUT_CITAAT = "invalid_citation"
#: Onderscheidbare redenen bij `invalid_citation` (`Beoordelingsdocument.foutdetail`).
CITAAT_NIET_GEVONDEN = "niet_gevonden"
CITAAT_NIET_UNIEK = "niet_uniek"
CITAAT_LEEG = "leeg"
GROND_NIET_HERLEIDBAAR = "grond_niet_herleidbaar"
#: /3 (besluit 12): zichtbare omzetting van fail naar review_required /
#: insufficient_information (`Beoordelingsdocument.omzetting`).
OMZETTING_DISCRETIE_ZONDER_BEDOELING = "discretie_zonder_bedoeling"
#: Vaste, invoeronafhankelijke vraag bij die omzetting. Ook als het model bij
#: zijn fail zelf een vraag gaf: die gaat volgens de T-tekst over andere open
#: punten (SC-C-03) en blijft zichtbaar in het oordeel.
VRAAG_DISCRETIE_ZONDER_BEDOELING = (
    "Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor "
    "een afweging voorschrijft?"
)
#: Betekenisgrond in de O-melding bij die omzetting; `{citaat}` is de eerste
#: dragende passage.
REDEN_DISCRETIE_ZONDER_BEDOELING = (
    "De bevestigde bedoeling is onbekend; alleen de kern zelf draagt de lezing "
    "van '{citaat}' als discretionaire beslisregel"
)

_UITVOERVELDEN = frozenset(
    {"verdict", "passages", "reason", "question", "uncertainty"}
    | {"scope_reason", "coverage"}
)
_PASSAGEVELDEN = frozenset({"quote", "function", "ground"})
_GRONDVELDEN = frozenset({"field", "ref", "quote"})
#: Door deze code afgeleid en alleen in het bewaarde oordeel aanwezig.
_POSITIEVELDEN = ("start", "end")
#: /1 (alleen voor de integriteitscontrole van bewaarde /1-documenten):
#: posities door de beoordelaar, als verplichte velden.
_PASSAGEVELDEN_V1 = _PASSAGEVELDEN | frozenset(_POSITIEVELDEN)
_GRONDVELDEN_V1 = _GRONDVELDEN | frozenset(_POSITIEVELDEN)
_SCALAIRE_GRONDEN = ("kern", "begrip", "bedoeling")
_CONTEXTVELDEN = ("organisatorische_context", "juridische_context", "wettelijke_basis")
_GRONDLABEL = {
    "kern": "de kern",
    "begrip": "het begrip",
    "bedoeling": "de bevestigde bedoeling",
    "organisatorische_context": "de organisatorische context",
    "juridische_context": "de juridische context",
    "wettelijke_basis": "de wettelijke basis",
}
_FUNCTIELABEL = {"criterion": "een criterium", "derivation": "een afleiding"}
#: Alleen een termlabel zoals 'Toegang:' is geen definitiekern (C23; O1-regel).
_LABEL_ZONDER_KERN = re.compile(r"[^:.!?;\n]{1,80}:")
_HEX64 = re.compile(r"[0-9a-f]{64}")

# Letterlijke appmeldingen uit synthese v5 §4 (B3 V06).
MELDING_V = (
    "INT-02 — Voldoet. '{passage}' beschrijft {criterium/afleiding/kenmerk}; "
    "grond: {grond}. Andere toetsregels zijn hiermee niet beoordeeld."
)
MELDING_VN = (
    "INT-02 — Voldoet niet. '{passage}' schrijft {handeling/afweging} voor in "
    "plaats van het begrip af te bakenen. Grond: {grond}. De tekst is ongewijzigd."
)
MELDING_VN_DISCRETIE = (
    "Deze passage functioneert als discretionaire beslisregel voor het handelen: "
    "'{citaat}'. Dat is onder de gekozen INT-02-norm geen beschrijvende afbakening "
    "van dit begrip. Het enkele beschrijven van een bevoegdheid of besluit is geen "
    "overtreding."
)
MELDING_O = (
    "INT-02 — Onvoldoende informatie. {ontbrekende of strijdige betekenisgrond}. "
    "Vraag: {één vraag}"
)
MELDING_NE = (
    "INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk "
    "oordeel."
)
MELDING_E = (
    "INT-02 — De beoordeling kon niet worden uitgevoerd door een technische fout. "
    "Er is geen inhoudelijk oordeel; de tekst is ongewijzigd."
)
MELDING_HISTORISCH = (
    "INT-02 — Eerdere beoordeling hoort bij een andere tekst-, betekenis-, "
    "context-, bron- of normversie. Opnieuw beoordelen is nodig."
)
# Uitvoeringstekst van dit contract, geen sjabloon uit synthese §4: de
# T-toestand "nog te beoordelen — beoordeling niet uitgevoerd" en NA met
# reikwijdtegrond.
MELDING_NIET_BEOORDEELD = "INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd."
MELDING_NVT = (
    "INT-02 — Niet van toepassing. {reikwijdtegrond}. Er is geen oordeel over de "
    "definitiekern."
)


class Int02ContractError(ValueError):
    """Invoer, configuratie of metadata voldoet niet aan het gesloten contract."""


def _eis(voorwaarde: bool, bericht: str) -> None:
    if not voorwaarde:
        raise Int02ContractError(bericht)


def _is_int(waarde: Any) -> bool:
    return isinstance(waarde, int) and not isinstance(waarde, bool)


def _gevuld(waarde: Any) -> bool:
    return isinstance(waarde, str) and bool(waarde.strip())


def _in(waarde: Any, toegestaan: Iterable[str]) -> bool:
    """Enum-lidmaatschap zonder TypeError voor niet-hashbare waarden."""
    return isinstance(waarde, str) and waarde in toegestaan


def _hash(waarde: Any) -> str:
    """SHA-256 over canonieke JSON (ASCII-escapes: injectief, ook bij surrogaten)."""
    tekst = json.dumps(waarde, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(tekst.encode("ascii")).hexdigest()


# --- Invoer --------------------------------------------------------------------


@dataclass(frozen=True)
class Bronpassage:
    """Een expliciet aangeleverde bronpassage; ondersteunende betekenisgrond."""

    id: str
    tekst: str

    def __post_init__(self) -> None:
        _eis(_gevuld(self.id), "bron-ID moet een niet-lege tekst zijn")
        _eis(isinstance(self.tekst, str), "brontekst moet tekst zijn")


@dataclass(frozen=True)
class Int02Invoer:
    """Onveranderlijke snapshot van de exact beoordeelde invoer.

    De kern wordt bytegelijk bewaard (geen strip of normalisatie); alle
    posities in de beoordeling verwijzen naar deze exacte tekst.
    """

    begrip: str
    kern: str
    bedoeling: str | None
    organisatorische_context: tuple[str, ...]
    juridische_context: tuple[str, ...]
    wettelijke_basis: tuple[str, ...]
    bronnen: tuple[Bronpassage, ...]

    def __post_init__(self) -> None:
        _eis(isinstance(self.begrip, str), "begrip moet tekst zijn")
        _eis(isinstance(self.kern, str), "kern moet tekst zijn")
        _eis(
            self.bedoeling is None or _gevuld(self.bedoeling),
            "bedoeling is een niet-lege tekst of None (expliciet onbekend)",
        )
        for veld in _CONTEXTVELDEN:
            waarden = getattr(self, veld)
            _eis(isinstance(waarden, tuple), f"{veld} moet een tuple zijn")
            _eis(all(_gevuld(w) for w in waarden), f"{veld} bevat alleen tekst")
        _eis(
            isinstance(self.bronnen, tuple)
            and all(isinstance(b, Bronpassage) for b in self.bronnen),
            "bronnen moet een tuple van Bronpassage zijn",
        )
        ids = [b.id for b in self.bronnen]
        _eis(len(ids) == len(set(ids)), "bron-ID's moeten uniek zijn")

    def context(self) -> dict[str, list[str]]:
        return {veld: list(getattr(self, veld)) for veld in _CONTEXTVELDEN}

    def als_dict(self) -> dict[str, Any]:
        return {
            "begrip": self.begrip,
            "kern": self.kern,
            "bedoeling": self.bedoeling,
            **self.context(),
            "bronnen": [{"id": b.id, "tekst": b.tekst} for b in self.bronnen],
        }


def _lijst(veld: str, waarden: Any) -> tuple[str, ...]:
    _eis(isinstance(waarden, list | tuple), f"{veld} moet een lijst zijn")
    return tuple(waarden)


def _bron(bron: Any) -> Bronpassage:
    _eis(
        isinstance(bron, Mapping) and set(bron) == {"id", "tekst"},
        "een bron heeft precies de velden id en tekst",
    )
    return Bronpassage(id=bron["id"], tekst=bron["tekst"])


def maak_invoer(
    *,
    begrip: str,
    kern: str,
    bedoeling: str | None,
    organisatorische_context: Iterable[str],
    juridische_context: Iterable[str],
    wettelijke_basis: Iterable[str],
    bronnen: Iterable[Mapping[str, str]],
) -> Int02Invoer:
    """Leg de exacte invoer vast als defensieve, onveranderlijke kopie."""
    _eis(isinstance(bronnen, list | tuple), "bronnen moet een lijst zijn")
    return Int02Invoer(
        begrip=begrip,
        kern=kern,
        bedoeling=bedoeling,
        organisatorische_context=_lijst(
            "organisatorische_context", organisatorische_context
        ),
        juridische_context=_lijst("juridische_context", juridische_context),
        wettelijke_basis=_lijst("wettelijke_basis", wettelijke_basis),
        bronnen=tuple(_bron(b) for b in bronnen),
    )


def ontbrekende_invoer(invoer: Int02Invoer) -> str | None:
    """'kern', 'context', 'kern en context' of None (K-9; lege kern of los label)."""
    kern = invoer.kern.strip()
    ontbreekt = []
    if not kern or _LABEL_ZONDER_KERN.fullmatch(kern):
        ontbreekt.append("kern")
    if not any(invoer.context().values()):
        ontbreekt.append("context")
    return " en ".join(ontbreekt) or None


# --- Configuratie, uitvoering en binding --------------------------------------


@dataclass(frozen=True)
class Configuratie:
    """Norm-, prompt-, routerings- en modelconfiguratie van een beoordeling."""

    normhash: str
    promptversie: str
    routeringshash: str
    provider: str
    model: str
    normversie: str = NORMVERSIE

    def __post_init__(self) -> None:
        for veld in ("normhash", "routeringshash"):
            waarde = getattr(self, veld)
            _eis(
                isinstance(waarde, str) and bool(_HEX64.fullmatch(waarde)),
                f"{veld} moet een SHA-256 in kleine hex zijn",
            )
        for veld in ("promptversie", "provider", "model", "normversie"):
            _eis(_gevuld(getattr(self, veld)), f"{veld} moet een niet-lege tekst zijn")


@dataclass(frozen=True)
class Uitvoering:
    """Uitvoeringsmetadata; wat niet gerapporteerd is, is expliciet `unknown`."""

    actor: str
    status: str
    foutcategorie: str | None = None
    tijdstip: str = ONBEKEND
    transportpogingen: int | str = ONBEKEND
    invoertokens: int | str = ONBEKEND
    uitvoertokens: int | str = ONBEKEND
    duur_ms: int | str = ONBEKEND
    kosten: Decimal | str = ONBEKEND
    modelversie: str = ONBEKEND

    def __post_init__(self) -> None:
        _eis(_in(self.actor, ACTOREN), "actor is 'ai' of 'human'")
        _eis(_in(self.status, UITVOERINGSSTATUSSEN), "onbekende uitvoeringsstatus")
        if self.status == "failed":
            _eis(
                _in(self.foutcategorie, TRANSPORTFOUTEN),
                "een mislukte uitvoering heeft een transportfoutcategorie",
            )
        else:
            _eis(self.foutcategorie is None, "foutcategorie alleen bij 'failed'")
        for veld in ("tijdstip", "modelversie"):
            _eis(_gevuld(getattr(self, veld)), f"{veld} is tekst of 'unknown'")
        for veld in ("transportpogingen", "invoertokens", "uitvoertokens", "duur_ms"):
            waarde = getattr(self, veld)
            _eis(
                waarde == ONBEKEND or (_is_int(waarde) and waarde >= 0),
                f"{veld} is een niet-negatief geheel getal of 'unknown'",
            )
        _eis(
            self.kosten == ONBEKEND
            or (
                isinstance(self.kosten, Decimal)
                and self.kosten.is_finite()
                and self.kosten >= 0
            ),
            "kosten is een niet-negatieve Decimal of 'unknown'",
        )

    def als_dict(self) -> dict[str, Any]:
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        if isinstance(self.kosten, Decimal):
            data["kosten"] = str(self.kosten)
        return data


@dataclass(frozen=True)
class Binding:
    """Versie- en hashbinding: elke wijziging maakt een oud oordeel historisch.

    De gerapporteerde modelversie staat in `Uitvoering`: zij is vóór een
    nieuwe beoordeling onbekend en hoort daarom niet bij de replayvergelijking.
    """

    contractversie: str
    normversie: str
    normhash: str
    promptversie: str
    routeringshash: str
    provider: str
    model: str
    begrip_hash: str
    kern_hash: str
    bedoeling_hash: str
    context_hash: str
    bronnen_hash: str

    def __post_init__(self) -> None:
        for f in fields(self):
            waarde = getattr(self, f.name)
            if f.name.endswith("hash"):
                _eis(
                    isinstance(waarde, str) and bool(_HEX64.fullmatch(waarde)),
                    f"{f.name} moet een SHA-256 in kleine hex zijn",
                )
            else:
                _eis(_gevuld(waarde), f"{f.name} moet een niet-lege tekst zijn")

    def configuratie(self) -> Configuratie:
        return Configuratie(
            normhash=self.normhash,
            promptversie=self.promptversie,
            routeringshash=self.routeringshash,
            provider=self.provider,
            model=self.model,
            normversie=self.normversie,
        )


def bereken_binding(invoer: Int02Invoer, configuratie: Configuratie) -> Binding:
    return _bereken_binding(invoer, configuratie, CONTRACTVERSIE)


def _bereken_binding(
    invoer: Int02Invoer, configuratie: Configuratie, contractversie: str
) -> Binding:
    _eis(isinstance(invoer, Int02Invoer), "invoer moet een Int02Invoer zijn")
    _eis(isinstance(configuratie, Configuratie), "configuratie ontbreekt")
    data = invoer.als_dict()
    return Binding(
        contractversie=contractversie,
        normversie=configuratie.normversie,
        normhash=configuratie.normhash,
        promptversie=configuratie.promptversie,
        routeringshash=configuratie.routeringshash,
        provider=configuratie.provider,
        model=configuratie.model,
        begrip_hash=_hash(data["begrip"]),
        kern_hash=_hash(data["kern"]),
        bedoeling_hash=_hash(data["bedoeling"]),
        context_hash=_hash(invoer.context()),
        bronnen_hash=_hash(data["bronnen"]),
    )


# --- Validatie van de beoordelaarsuitvoer -------------------------------------


class _AfwijzingError(Exception):
    """Interne afwijzing van de uitvoer met foutcategorie (nooit naar buiten)."""

    def __init__(self, categorie: str, detail: str | None = None) -> None:
        super().__init__(categorie)
        self.categorie = categorie
        self.detail = detail


def _vorm(voorwaarde: bool) -> None:
    if not voorwaarde:
        raise _AfwijzingError(FOUT_UITVOER)


def _citaat(voorwaarde: bool, detail: str) -> None:
    if not voorwaarde:
        raise _AfwijzingError(FOUT_CITAAT, detail)


def _object(waarde: Any, velden: frozenset[str]) -> None:
    _vorm(isinstance(waarde, dict) and set(waarde) == velden)


def _positie(tekst: str, citaat: str) -> tuple[int, int]:
    """(start, end) van de enige exacte vindplaats; anders `invalid_citation`.

    Exacte substring in Python-codepunten, zonder normalisatie. Ook een
    overlappende tweede vindplaats maakt het citaat niet uniek.
    """
    _citaat(bool(citaat), CITAAT_LEEG)
    start = tekst.find(citaat)
    _citaat(start >= 0, CITAAT_NIET_GEVONDEN)
    _citaat(tekst.find(citaat, start + 1) < 0, CITAAT_NIET_UNIEK)
    return start, start + len(citaat)


def _staat_op(tekst: str, citaat: str, start: int, eind: int) -> bool:
    """/1: het citaat staat exact op de door de beoordelaar opgegeven posities."""
    return 0 <= start < eind <= len(tekst) and tekst[start:eind] == citaat


def _controleer_grondvorm(grond: Any, v1: bool) -> None:
    _object(grond, _GRONDVELDEN_V1 if v1 else _GRONDVELDEN)
    veld, ref = grond["field"], grond["ref"]
    _vorm(_in(veld, _GRONDLABEL.keys() | {"bron"}))
    if veld in _SCALAIRE_GRONDEN:
        _vorm(ref is None)
    elif veld == "bron":
        _vorm(_gevuld(ref))
    else:
        _vorm(_is_int(ref))
    if not v1:
        _vorm(grond["quote"] is None or isinstance(grond["quote"], str))
        return
    geciteerd = (grond["quote"], grond["start"], grond["end"])
    _vorm(
        geciteerd == (None, None, None)
        or (
            isinstance(geciteerd[0], str)
            and _is_int(geciteerd[1])
            and _is_int(geciteerd[2])
        )
    )


def _controleer_structuur(uitvoer: Any, v1: bool = False) -> None:
    """Gesloten vorm: exacte velden, typen en enums (bool is geen int).

    `v1` alleen voor de integriteitscontrole van een bewaard /1-document:
    dan zijn `start`/`end` verplichte gehele getallen (of samen null bij een
    grond zonder citaat), zoals onder /1.
    """
    _object(uitvoer, _UITVOERVELDEN)
    _vorm(_in(uitvoer["verdict"], VERDICTS))
    _vorm(_gevuld(uitvoer["reason"]))
    _vorm(uitvoer["question"] is None or isinstance(uitvoer["question"], str))
    _vorm(uitvoer["scope_reason"] is None or isinstance(uitvoer["scope_reason"], str))
    _vorm(_in(uitvoer["uncertainty"], ONZEKERHEDEN))
    _vorm(_in(uitvoer["coverage"], DEKKINGEN))
    _vorm(isinstance(uitvoer["passages"], list))
    for passage in uitvoer["passages"]:
        _object(passage, _PASSAGEVELDEN_V1 if v1 else _PASSAGEVELDEN)
        _vorm(isinstance(passage["quote"], str))
        if v1:
            _vorm(_is_int(passage["start"]) and _is_int(passage["end"]))
        _vorm(_in(passage["function"], FUNCTIES))
        _controleer_grondvorm(passage["ground"], v1)


def _grondbron(grond: dict[str, Any], invoer: Int02Invoer) -> str:
    """De exacte tekst waarnaar een grond verwijst; anders niet herleidbaar.

    Ook zonder grondcitaat moet die tekst gevuld zijn: een onbekende
    bedoeling, een leeg of alleen-witruimte begrip en een lege bron kunnen
    geen oordeel dragen (review WP1 P2-1).
    """
    veld, ref = grond["field"], grond["ref"]
    if veld in _SCALAIRE_GRONDEN:
        tekst = getattr(invoer, veld)
    elif veld == "bron":
        teksten = {b.id: b.tekst for b in invoer.bronnen}
        _citaat(ref in teksten, GROND_NIET_HERLEIDBAAR)
        tekst = teksten[ref]
    else:
        waarden = getattr(invoer, veld)
        _citaat(0 <= ref < len(waarden), GROND_NIET_HERLEIDBAAR)
        tekst = waarden[ref]
    _citaat(_gevuld(tekst), GROND_NIET_HERLEIDBAAR)
    # _gevuld eist isinstance(tekst, str); anders werpt _citaat hierboven.
    return cast(str, tekst)


def _met_posities(uitvoer: dict[str, Any], invoer: Int02Invoer) -> dict[str, Any]:
    """Nieuwe kopie van de uitvoer met afgeleide posities; elke grond herleidbaar.

    Elk passagecitaat krijgt zijn enige vindplaats in de kern, elk grondcitaat
    die in zijn grondtekst; een grond zonder citaat krijgt `start`/`end` None.
    De meegegeven uitvoer wordt niet gewijzigd.
    """
    passages = []
    for passage in uitvoer["passages"]:
        start, end = _positie(invoer.kern, passage["quote"])
        grond = dict(passage["ground"])
        tekst = _grondbron(grond, invoer)
        grondpositie = (None, None)
        if grond["quote"] is not None:
            grondpositie = _positie(tekst, grond["quote"])
        grond.update(zip(_POSITIEVELDEN, grondpositie, strict=True))
        passages.append({**passage, "start": start, "end": end, "ground": grond})
    return {**uitvoer, "passages": passages}


def _controleer_citaten_v1(
    uitvoer: dict[str, Any], invoer: Int02Invoer
) -> dict[str, Any]:
    """/1: elk citaat staat exact op zijn opgegeven posities; elke grond herleidbaar.

    Alleen voor de integriteitscontrole van een bewaard /1-document; de regel
    is letterlijk die van contract /1. De uitvoer blijft ongewijzigd het oordeel.
    """
    for passage in uitvoer["passages"]:
        _citaat(
            _staat_op(invoer.kern, passage["quote"], passage["start"], passage["end"]),
            CITAAT_NIET_GEVONDEN,
        )
        grond = passage["ground"]
        tekst = _grondbron(grond, invoer)
        if grond["quote"] is not None:
            _citaat(
                _staat_op(tekst, grond["quote"], grond["start"], grond["end"]),
                CITAAT_NIET_GEVONDEN,
            )
    return uitvoer


def _een_vraag(vraag: Any) -> bool:
    """Mechanisch: één niet-lege tekst die eindigt op het enige vraagteken."""
    return (
        isinstance(vraag, str)
        and vraag.count("?") == 1
        and vraag.rstrip().endswith("?")
        and bool(vraag.rstrip("? \t\n"))
    )


def _controleer_samenhang(uitvoer: dict[str, Any]) -> None:
    """Verdict, passages, vraag, onzekerheid, reikwijdte en dekking passen samen."""
    verdict = uitvoer["verdict"]
    functies = {p["function"] for p in uitvoer["passages"]}
    vraag, scope = uitvoer["question"], uitvoer["scope_reason"]
    if verdict != "not_applicable":
        _vorm(scope is None)
    if verdict == "pass":
        _vorm(bool(functies) and functies <= BESCHRIJVEND)
        _vorm(uitvoer["coverage"] == "complete")
        _vorm(uitvoer["uncertainty"] != "decisive" and vraag is None)
    elif verdict == "fail":
        _vorm(bool(functies & GEBREK))
        _vorm(vraag is None or _een_vraag(vraag))
    elif verdict == "insufficient_information":
        _vorm(not functies & GEBREK and _een_vraag(vraag))
        _vorm(uitvoer["uncertainty"] == "decisive")
    else:
        _vorm(_gevuld(scope) and not uitvoer["passages"] and vraag is None)
        _vorm(uitvoer["coverage"] == "none" and uitvoer["uncertainty"] == "none")


# --- Meldingen -----------------------------------------------------------------


def _zonder_slotpunt(tekst: str) -> str:
    tekst = tekst.rstrip()
    return tekst[:-1] if tekst.endswith(".") else tekst


def _grondtekst(grond: dict[str, Any]) -> str:
    if grond["field"] == "bron":
        label = f"bronpassage {grond['ref']}"
    else:
        label = _GRONDLABEL[grond["field"]]
    if grond["quote"] is not None:
        label += f" ('{grond['quote']}')"
    return label


def _eerste(passages: list[dict[str, Any]], functies: frozenset[str]) -> dict:
    return min(
        (p for p in passages if p["function"] in functies),
        key=lambda p: (p["start"], p["end"]),
    )


def _vul(sjabloon: str, waarden: dict[str, str]) -> str:
    """Vul de plaatshouders van het sjabloon in één doorgang.

    Alleen het oorspronkelijke sjabloon wordt gescand; ingevoegde waarden
    (citaat, grond, reden, vraag) worden nooit opnieuw geïnterpreteerd, ook
    niet als zij zelf '{grond}' of '{één vraag}' bevatten (review WP1 P2-2).
    """
    patroon = re.compile("|".join(re.escape(sleutel) for sleutel in waarden))
    return patroon.sub(lambda treffer: waarden[treffer.group(0)], sjabloon)


def _status_en_melding(uitvoer: dict[str, Any]) -> tuple[str, str | None, str]:
    verdict = uitvoer["verdict"]
    if verdict == "pass":
        p = _eerste(uitvoer["passages"], BESCHRIJVEND)
        melding = _vul(
            MELDING_V,
            {
                "{passage}": p["quote"],
                "{criterium/afleiding/kenmerk}": _FUNCTIELABEL[p["function"]],
                "{grond}": _grondtekst(p["ground"]),
            },
        )
        return "pass", None, melding
    if verdict == "fail":
        p = _eerste(uitvoer["passages"], GEBREK)
        discretie = p["function"] == "discretionary_decision_rule"
        melding = _vul(
            MELDING_VN,
            {
                "{passage}": p["quote"],
                "{handeling/afweging}": (
                    "een afweging" if discretie else "een handeling"
                ),
                "{grond}": _grondtekst(p["ground"]),
            },
        )
        if discretie:
            melding += " " + _vul(MELDING_VN_DISCRETIE, {"{citaat}": p["quote"]})
        return "fail", None, melding
    if verdict == "insufficient_information":
        melding = _vul(
            MELDING_O,
            {
                "{ontbrekende of strijdige betekenisgrond}": _zonder_slotpunt(
                    uitvoer["reason"]
                ),
                "{één vraag}": uitvoer["question"],
            },
        )
        return "review_required", "insufficient_information", melding
    melding = _vul(
        MELDING_NVT, {"{reikwijdtegrond}": _zonder_slotpunt(uitvoer["scope_reason"])}
    )
    return "not_applicable", None, melding


# --- Dienstregel discretie zonder bedoeling (/3, besluit 12) ---------------------


def _discretie_zonder_bedoeling(
    oordeel: dict[str, Any], invoer: Int02Invoer, uitvoering: Uitvoering
) -> bool:
    """Draagt alleen de kern een discretionaire fail van het model, zonder bedoeling?

    Alle passages met een gebrekfunctie tellen; andere passages dragen de
    fail niet. Eén `actor_prescription` of één andere grond dan `kern`
    (begrip, bedoeling, context of bron) houdt de fail in stand.
    """
    if (
        oordeel["verdict"] != "fail"
        or uitvoering.actor != "ai"
        or _gevuld(invoer.bedoeling)
    ):
        return False
    dragend = [p for p in oordeel["passages"] if p["function"] in GEBREK]
    return all(
        p["function"] == "discretionary_decision_rule"
        and p["ground"]["field"] == "kern"
        for p in dragend
    )


def _omzetting_discretie(oordeel: dict[str, Any]) -> tuple[str, str, str, str]:
    """(status, reden, melding, vraag) na de omzetting; de O-melding met vaste vraag."""
    p = _eerste(oordeel["passages"], GEBREK)
    melding = _vul(
        MELDING_O,
        {
            "{ontbrekende of strijdige betekenisgrond}": _vul(
                REDEN_DISCRETIE_ZONDER_BEDOELING, {"{citaat}": p["quote"]}
            ),
            "{één vraag}": VRAAG_DISCRETIE_ZONDER_BEDOELING,
        },
    )
    return (
        "review_required",
        "insufficient_information",
        melding,
        VRAAG_DISCRETIE_ZONDER_BEDOELING,
    )


# --- Document en replay ---------------------------------------------------------


@dataclass(frozen=True)
class Beoordelingsdocument:
    """Onveranderlijk document: exacte invoer, binding, uitvoering en oordeel.

    `oordeel_json` is de canonieke JSON van de geaccepteerde uitvoer met de
    door deze code afgeleide posities, of None als er geen geldig oordeel is.
    `foutdetail` onderscheidt bij `invalid_citation` niet gevonden, niet
    uniek, leeg citaat en niet-herleidbare grond; anders is het None.
    `omzetting` is `OMZETTING_DISCRETIE_ZONDER_BEDOELING` als de dienstregel
    van /3 een fail heeft omgezet (het oordeel houdt dan verdict `fail`);
    anders None, ook onder /1 en /2.
    `toets_actualiteit` accepteert een document alleen als het opnieuw exact
    uit zijn eigen invoer, binding, uitvoering en oordeel volgt; een direct
    samengesteld of gemanipuleerd document is dus nooit stil een actueel
    oordeel.
    """

    contractversie: str
    invoer: Int02Invoer
    binding: Binding
    uitvoering: Uitvoering
    status: str
    reden: str | None
    melding: str
    vraag: str | None
    foutcategorie: str | None
    oordeel_json: str | None
    foutdetail: str | None = None
    omzetting: str | None = None

    @property
    def oordeel(self) -> dict[str, Any] | None:
        """Een verse kopie van het geaccepteerde oordeel."""
        return None if self.oordeel_json is None else json.loads(self.oordeel_json)

    def als_dict(self) -> dict[str, Any]:
        return {
            "contractversie": self.contractversie,
            "invoer": self.invoer.als_dict(),
            "binding": {f.name: getattr(self.binding, f.name) for f in fields(Binding)},
            "uitvoering": self.uitvoering.als_dict(),
            "status": self.status,
            "reden": self.reden,
            "melding": self.melding,
            "vraag": self.vraag,
            "foutcategorie": self.foutcategorie,
            "foutdetail": self.foutdetail,
            "omzetting": self.omzetting,
            "oordeel": self.oordeel,
        }


@dataclass(frozen=True)
class Actualiteit:
    """Wat een bewaard document nu betekent voor de actuele invoer en configuratie."""

    status: str
    reden: str | None
    melding: str

    def __post_init__(self) -> None:
        _eis(_in(self.status, STATUSSEN), "onbekende status")
        if self.status == "review_required":
            _eis(_in(self.reden, REDENEN), "review_required vraagt een geldige reden")
        else:
            _eis(self.reden is None, "een reden hoort alleen bij review_required")
        _eis(_gevuld(self.melding), "melding ontbreekt")


def beoordeel(
    invoer: Int02Invoer,
    configuratie: Configuratie,
    modeluitvoer: Any,
    uitvoering: Uitvoering,
) -> Beoordelingsdocument:
    """Valideer de beoordelaarsuitvoer en leg het oordeel vast; nooit repareren.

    Volgorde: ontbrekende kern/context (NE, oordeel genegeerd) → mislukte
    uitvoering (error) → niet uitgevoerd (nog te beoordelen) → structuur →
    citaten, posities en gronden → samenhang → status → dienstregel
    discretie zonder bedoeling. Een nieuw document valt altijd onder de
    actuele `CONTRACTVERSIE`.
    """
    return _beoordeel(invoer, configuratie, modeluitvoer, uitvoering, CONTRACTVERSIE)


def _beoordeel(
    invoer: Int02Invoer,
    configuratie: Configuratie,
    modeluitvoer: Any,
    uitvoering: Uitvoering,
    contractversie: str,
) -> Beoordelingsdocument:
    """`beoordeel` volgens de regels van `contractversie` (/3, of /1 en /2 voor replay).

    Onder /1 levert de beoordelaar de posities en is het oordeel de uitvoer
    zelf; /1 kende geen `foutdetail`. Onder /2 en /3 leidt deze code de
    posities af. Alleen /3 kent de dienstregel discretie zonder bedoeling.
    """
    v1 = contractversie == _CONTRACTVERSIE_V1
    _eis(isinstance(uitvoering, Uitvoering), "uitvoering moet een Uitvoering zijn")
    binding = _bereken_binding(invoer, configuratie, contractversie)

    def document(
        status: str,
        melding: str,
        reden: str | None = None,
        fout: str | None = None,
        uitvoer: dict[str, Any] | None = None,
        vraag: str | None = None,
        foutdetail: str | None = None,
        omzetting: str | None = None,
    ) -> Beoordelingsdocument:
        oordeel = None
        if uitvoer is not None:
            oordeel = json.dumps(uitvoer, ensure_ascii=False, sort_keys=True)
        return Beoordelingsdocument(
            contractversie=contractversie,
            invoer=invoer,
            binding=binding,
            uitvoering=uitvoering,
            status=status,
            reden=reden,
            melding=melding,
            vraag=vraag,
            foutcategorie=fout,
            oordeel_json=oordeel,
            foutdetail=foutdetail,
            omzetting=omzetting,
        )

    ontbreekt = ontbrekende_invoer(invoer)
    if ontbreekt:
        return document(
            "not_evaluated", MELDING_NE.replace("{kern/context}", ontbreekt)
        )
    if uitvoering.status == "failed":
        return document("error", MELDING_E, fout=uitvoering.foutcategorie)
    if uitvoering.status == "not_executed" and modeluitvoer is None:
        return document(
            "review_required", MELDING_NIET_BEOORDEELD, reden="not_assessed"
        )
    try:
        _vorm(uitvoering.status == "completed")
        _controleer_structuur(modeluitvoer, v1)
        if v1:
            oordeel = _controleer_citaten_v1(modeluitvoer, invoer)
        else:
            oordeel = _met_posities(modeluitvoer, invoer)
        _controleer_samenhang(oordeel)
    except _AfwijzingError as afwijzing:
        detail = None if v1 else afwijzing.detail
        return document("error", MELDING_E, fout=afwijzing.categorie, foutdetail=detail)
    status, reden, melding = _status_en_melding(oordeel)
    vraag, omzetting = oordeel["question"], None
    if contractversie == CONTRACTVERSIE and _discretie_zonder_bedoeling(
        oordeel, invoer, uitvoering
    ):
        status, reden, melding, vraag = _omzetting_discretie(oordeel)
        omzetting = OMZETTING_DISCRETIE_ZONDER_BEDOELING
    return document(
        status,
        melding,
        reden=reden,
        uitvoer=oordeel,
        vraag=vraag,
        omzetting=omzetting,
    )


def _zonder_posities(oordeel: Any) -> Any:
    """Het bewaarde oordeel terug in modelvorm: zonder de afgeleide posities.

    Alleen voor replay. Een oordeel dat niet de verwachte vorm heeft, blijft
    ongewijzigd; `beoordeel` wijst het dan zelf af.
    """
    if not isinstance(oordeel, dict) or not isinstance(oordeel.get("passages"), list):
        return oordeel

    def zonder(waarde: Any) -> Any:
        if not isinstance(waarde, dict):
            return waarde
        return {k: v for k, v in waarde.items() if k not in _POSITIEVELDEN}

    passages = []
    for passage in oordeel["passages"]:
        kaal = zonder(passage)
        if isinstance(kaal, dict) and "ground" in kaal:
            kaal["ground"] = zonder(kaal["ground"])
        passages.append(kaal)
    return {**oordeel, "passages": passages}


def _hervalideer(waarde: Any, soort: type) -> Any:
    """Herbouw via de constructor, zodat een omzeilde validatie alsnog faalt."""
    _eis(isinstance(waarde, soort), f"{soort.__name__} verwacht")
    return soort(**{f.name: getattr(waarde, f.name) for f in fields(soort)})


def _herleidbaar(document: Beoordelingsdocument) -> bool:
    """Volgt het document exact uit zijn eigen invoer, binding en oordeel?

    Vangt directe constructie en manipulatie (bijvoorbeeld via
    `object.__setattr__`): alleen een document dat `beoordeel` opnieuw
    identiek oplevert, kan een actueel oordeel dragen.

    De controle volgt de *originele* contractversie van het document (review
    Codex 07-10-2026): onder /2 en /3 worden de bewaarde posities weggelaten
    en opnieuw afgeleid; onder /1 gelden de /1-regels (opgeslagen posities,
    `tekst[start:end] == quote` exact). Alleen onder /3 hoort de dienstregel
    erbij: een ontbrekende, gewijzigde of onterechte `omzetting` maakt het
    document niet-herleidbaar, net als een gewijzigde of ontbrekende positie
    of quote; een onbekende contractversie is nooit herleidbaar. Een
    herleidbaar /1- of /2-document is daarna via de bindingstoets historisch.
    """
    versie = document.contractversie
    if not _in(versie, _BEKENDE_CONTRACTVERSIES):
        return False
    try:
        invoer = _hervalideer(document.invoer, Int02Invoer)
        for bron in invoer.bronnen:
            _hervalideer(bron, Bronpassage)
        binding = _hervalideer(document.binding, Binding)
        uitvoering = _hervalideer(document.uitvoering, Uitvoering)
        _eis(
            document.oordeel_json is None or isinstance(document.oordeel_json, str),
            "oordeel_json is tekst of None",
        )
    except Int02ContractError:
        return False
    try:
        oordeel = document.oordeel
    except (ValueError, RecursionError):
        # Niet te decoderen: ongeldige JSON (JSONDecodeError), een getal boven
        # de cijferlimiet van int of te diepe nesting (review WP1 P2-3).
        return False
    if versie != _CONTRACTVERSIE_V1:
        oordeel = _zonder_posities(oordeel)
    try:
        opnieuw = _beoordeel(
            invoer, binding.configuratie(), oordeel, uitvoering, versie
        )
    except Int02ContractError:
        return False
    return opnieuw == document


def toets_actualiteit(
    document: Beoordelingsdocument | None,
    invoer: Int02Invoer,
    configuratie: Configuratie,
) -> Actualiteit:
    """Pas een bewaard document toe op de actuele invoer en configuratie.

    Volgorde: actuele kern/context ontbreekt (NE) → geen document (nog te
    beoordelen) → technische fout of niet-herleidbaar document (error) →
    andere binding (historisch) → het bewaarde oordeel. Het document zelf
    wordt nooit gewijzigd.
    """
    actueel = bereken_binding(invoer, configuratie)
    ontbreekt = ontbrekende_invoer(invoer)
    if ontbreekt:
        melding = MELDING_NE.replace("{kern/context}", ontbreekt)
        return Actualiteit("not_evaluated", None, melding)
    if document is None:
        return Actualiteit("review_required", "not_assessed", MELDING_NIET_BEOORDEELD)
    if (
        not isinstance(document, Beoordelingsdocument)
        or document.status == "error"
        or not _herleidbaar(document)
    ):
        return Actualiteit("error", None, MELDING_E)
    if document.binding != actueel:
        return Actualiteit("review_required", "historical", MELDING_HISTORISCH)
    return Actualiteit(document.status, document.reden, document.melding)
