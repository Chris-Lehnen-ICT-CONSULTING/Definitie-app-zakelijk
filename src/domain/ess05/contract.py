"""ESS-05 — het onderscheidscontract (DEF-768, besluiten K-1…K-10, synthese v3).

Pure domeinlogica, zonder Streamlit, database of AI-client. De evaluator
(`services.validation.evaluators.distinction_assessment`) roept
`beoordeel_onderscheid` aan; de beoordelingsdienst
(`services.validation.ess05_assessment_service`) gebruikt `valideer_concept`
en `pas_verificatie_toe` om de modeluitvoer fail-closed te valideren.
Specificatie: `docs/plans/2026-09-23-DEF-768-ess05-contract-en-runplan-v1.md`,
aangevuld door ADR-003 (`ess05/2`): een gesloten conceptoordeel met
gecontroleerde bewijsplaatsen (`domain.ess05.bewijs`) wordt pas toegepast na
een volledige, positieve en exact gebonden semantische verificatie. Alleen die
combinatie wordt via een vaste weergave een toepasbaar oordeel.

Wat de regel toetst: onderscheidt de definitiekern het begrip in deze context
kenbaar van de verwante begrippen die zij moet uitsluiten? De vraag per buur
is een *kenmerkvraag* (drukt de kern een onderbouwd verschil in kenmerken uit
ten opzichte van de beschrijving van de buur?), geen extensievraag: overlap
van gevallen is geen gebrek zolang het onderscheidende kenmerk kenbaar is
(K-3b; ESS05-E05 lener/werknemer voldoet). Een citaat dat letterlijk ook in
de buurdefinitie staat bewijst geen onderscheid (ESS05-E06 kan in code nooit
'voldoet' worden).

Rolverdeling: de **AI** oordeelt per verzonden buur en mag buren voorstellen;
de **code** controleert binding, gesloten velden, citaatbestaan en berekent de
uitkomst. Modelvoorstellen blijven onbevestigd (K-1); zonder bevestigde buur
is de regel open met precies één vraag, tenzij een deskundige de lege
vergelijkingsruimte gemotiveerd en versiegebonden bevestigt (K-2). Geen
cijfer, geen blokkade, geen automatische herschrijving.

Sinds DEF-768 stap 2 (plan 2026-09-29 app-aansluiting, besluit Chris A–D)
levert de app het document `ess05/3` van de bewijsregelroute
(`domain.ess05.app_bewijsregels`). Het app-bevestigingsbeleid hierboven blijft
gelden als afbeelding na de regels (B); modelvoorstellen bestaan in die route
niet (A). Een `ess05/2`-document is verouderd: toets opnieuw (D). De
ess05/2-code hieronder blijft staan tot een afzonderlijk verwijderbesluit.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from domain.context.contract import CONTEXT_VELDEN, Deeluitkomst
from domain.context.normalisatie import canoniseer_contextlijst, contextsleutel
from domain.ess03.contract import Intentie, materiaalhashes
from domain.ess05 import app_bewijsregels as app, bewijs, bewijsregels as br
from domain.ess05.bewijs import (
    ANTWOORDSCHEMA,
    CONCEPTSCHEMA,
    RENDERERVERSIE,
    VERIFICATIESCHEMA,
    Ess05Concept,
    Verificatieuitkomst,
    toets_verificatie,
)
from domain.ess05.definitieruis import neutraliseer_definitieruis
from domain.modeluitvoer import parse_modeluitvoer
from domain.sources.contract import vind_citaat
from domain.sources.normalisatie import Bronidentiteit, canoniseer_bronnen

logger = logging.getLogger(__name__)

__all__ = [
    "BASIS_ASSESSMENT",
    "BASIS_LEGE_RUIMTE",
    "CONTRACTVERSIE",
    "FASE_BEOORDELING",
    "FASE_VERIFICATIE",
    "FOUT_CONTROLE",
    "FOUT_SEMANTISCH",
    "HERKOMSTEN",
    "ONDERDEEL_ONDERSCHEID",
    "ONDERSCHEIDINGEN",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_NOT_EVALUATED",
    "STATUS_OPEN",
    "STATUS_PASS",
    "Buur",
    "Ess05Beoordelingsbinding",
    "Ess05Binding",
    "Ess05Concept",
    "Ess05Uitkomst",
    "GevalideerdOnderscheid",
    "OngeldigeBurenlijstError",
    "afleidingsbinding",
    "beoordeel_onderscheid",
    "beoordeling_niet_beschikbaar",
    "beoordeling_technische_fout",
    "beoordelingsmateriaal",
    "bereken_ess05_vingerafdruk",
    "betekenismateriaal",
    "binding_uit_dict",
    "bindingscontext",
    "bronverwijzing",
    "buur_id",
    "contextmateriaal",
    "heeft_context",
    "lege_ruimte_geldig",
    "materiaalhashes",
    "normaliseer_buren",
    "onbruikbare_modeluitvoer",
    "pas_verificatie_toe",
    "repositoryrijen_uit",
    "stel_actieve_buren_samen",
    "stel_burenlijst_samen",
    "valideer_antwoord",
    "valideer_concept",
]

#: Beleidsversie van dit contract; onderdeel van de vingerafdruk. `/2`
#: (ADR-003): gesloten conceptoordeel + semantische verificatie; `/1`-documenten
#: blijven ongewijzigde historie.
CONTRACTVERSIE = "ess05/2"

#: Foutsoort: de verifier keurde het concept niet (volledig) goed. Onbruikbare
#: modeluitvoer, géén oordeel over de definitie.
FOUT_SEMANTISCH = "semantic_verification_failed"
#: Idem voor de bewijsregelroute: een lokale controle keurde de interpretatie niet.
FOUT_CONTROLE = "semantische_controle_mislukt"
FASE_BEOORDELING = "assessment"
FASE_VERIFICATIE = "verification"

#: Het samenvattende onderdeel van ESS-05 in `rule_results`.
ONDERDEEL_ONDERSCHEID = "distinction"

#: `Deeluitkomst.field`: het oordeel komt van de AI-beoordeling / de deskundige.
BASIS_ASSESSMENT = "ess05_assessment"
BASIS_LEGE_RUIMTE = "ess05_empty_space"

#: Herkomst van een buur. `ontologie` is gereserveerd (DEF-300), zonder leverancier.
HERKOMSTEN: tuple[str, ...] = ("gebruiker", "bron", "repository", "model", "ontologie")
_ONBEVESTIGD_VOORSTEL = frozenset({"bron", "model", "ontologie"})

ONDERSCHEIDINGEN: tuple[str, ...] = ("distinguished", "not_distinguished", "unclear")

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_OPEN = "review_required"
STATUS_ERROR = "error"
STATUS_NOT_EVALUATED = "not_evaluated"

_BRONPREFIX = "source:"
_BUURPREFIX = "neighbour:"
_LOCATIE_DEFINITIE = "definition"

_VRAAG_GEEN_BUREN = (
    "Welke verwante begrippen (zelfde bovenbegrip of in deze context verwarbaar) "
    "moet deze definitie uitsluiten?"
)
_ACTIE_PASS = "Geen actie nodig."
_ACTIE_FAIL = (
    "Voeg in de kern het kenmerk toe dat dit begrip onderscheidt van de genoemde "
    "verwante begrippen. Toetsen wijzigt de tekst niet; een verbetervoorstel volgt "
    "alleen op verzoek."
)
_ACTIE_VRAAG = (
    "Beantwoord de vraag: voeg verwante begrippen toe, bevestig of wijs voorstellen "
    "af, of bevestig gemotiveerd dat er geen verwante begrippen zijn. Toets daarna "
    "opnieuw."
)
_ACTIE_NIET_BEOORDEELD = (
    "Valideer opnieuw; de ESS-05-beoordeling wordt daarbij automatisch uitgevoerd."
)
_ACTIE_FOUT = (
    "Controleer opnieuw. Blijft dit terugkomen, meld het dan als technisch probleem."
)
_ACTIE_INVOER = "Vul term, definitie en context in en toets opnieuw."
_ACTIE_HANDMATIG = (
    "Beoordeel zelf of de definitie zich voldoende onderscheidt van de verwante "
    "begrippen. Toets opnieuw na een wijziging van tekst, context of verwante "
    "begrippen."
)

#: Robuustheid P1 (punt 4, besluit Chris 29-09): fouttypen van een
#: `ess05/3`-beoordeling waarbij de modeluitvoer inhoudelijk onbruikbaar is,
#: met een korte reden voor de gebruiker. De app toont dan `review_required`
#: ("beoordeel handmatig"), geen technisch probleem. Elk ander fouttype
#: (transport, timeout, weigering, afkapping, invoerlimiet, burenlookup,
#: teller) blijft `error`. Fail-closed: een onbekend type is technisch.
_ONBRUIKBAAR: dict[str, str] = {
    "malformed_response": "het antwoord van de AI was geen leesbaar JSON-object",
    "schemafout": "het antwoord van de AI had niet de afgesproken vorm",
    "citaatfout": "de AI verwees naar tekst die niet zo in het materiaal staat",
    "onderwerpfout": "de AI koppelde bewijs aan een ander begrip",
    "contextfout": "de AI gebruikte een feit uit een andere context",
    "kerndekking_onvolledig": "de AI dekte niet de hele definitie af",
    "doeldekking_onvolledig": "de AI beantwoordde niet alle verplichte vragen",
    "betekenisfout": "de AI noemde betekeniskenmerken zonder onderbouwing",
    "buiten_bereik": (
        "de definitie bevat een constructie die de automatische beoordeling niet "
        "ondersteunt"
    ),
    "inconsistent": "de AI gaf tegenstrijdige antwoorden",
    "dekking_ontbreekt": (
        "het materiaal is maar deels meegegeven, dus 'niet besproken' bewijst niets"
    ),
    FOUT_CONTROLE: "een controle bevestigde de interpretatie van de AI niet",
    "controle_malformed_response": "een controle gaf geen bruikbaar antwoord",
    "controle_packet_hash_mismatch": "een controle gaf geen bruikbaar antwoord",
}


def onbruikbare_modeluitvoer(assessment: Any) -> bool:
    """Of een `ess05/3`-beoordeling faalde op inhoudelijk onbruikbare modeluitvoer
    (dan `review_required`), en niet op een technische storing (dan `error`)."""
    if not isinstance(assessment, Mapping):
        return False
    fout = assessment.get("error")
    return (
        assessment.get("contract_version") == app.DOCUMENTVERSIE
        and assessment.get("status") == "error"
        and isinstance(fout, Mapping)
        and _tekst(fout.get("type")) in _ONBRUIKBAAR
    )


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


# --- buren ---------------------------------------------------------------------------


class OngeldigeBurenlijstError(ValueError):
    """De aangeleverde burenlijst voldoet niet aan het contract (fail-closed)."""


@dataclass(frozen=True)
class Buur:
    """Een verwant begrip waarvan de definitie zich moet onderscheiden."""

    id: str
    term: str
    definitie: str | None
    herkomst: str
    bevestigd: bool

    def als_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "term": self.term,
            "definitie": self.definitie,
            "herkomst": self.herkomst,
            "bevestigd": self.bevestigd,
        }


def buur_id(herkomst: str, term: str, *, db_id: Any = None) -> str:
    """Stabiel id: `repository:<db-id>` of `<herkomst>:<hash van de term>`."""
    if herkomst == "repository" and db_id is not None:
        return f"repository:{db_id}"
    sleutel = str(term or "").strip().casefold()
    return f"{herkomst}:{hashlib.sha256(sleutel.encode('utf-8')).hexdigest()[:12]}"


def bronverwijzing(item: Mapping[str, Any]) -> dict[str, str] | None:
    """De bronverwijzing (`source_id` + letterlijk `quote`) bij een buur of voorstel.

    Afzonderlijke provenance naast de herkomst: een modelvoorstel met een
    broncitaat blijft `herkomst=model` (K-1); de verwijzing zegt alleen waar
    het model het begrip aantrof. None als er geen volledige verwijzing is.
    """
    bron, citaat = _tekst(item.get("source_id")), _tekst(item.get("quote"))
    return {"source_id": bron, "quote": citaat} if bron and citaat else None


def _bronverwijzingsfout(item: Mapping[str, Any]) -> str | None:
    """Geen of een volledige bronverwijzing; een halve of niet-tekstuele is fout."""
    waarden = [item.get("source_id"), item.get("quote")]
    if all(w is None for w in waarden) or bronverwijzing(item):
        return None
    return "source_id en quote horen samen en zijn beide tekst"


def _buur_uit(item: Any, index: int) -> Buur:
    if isinstance(item, Buur):
        return item
    if not isinstance(item, Mapping):
        raise OngeldigeBurenlijstError(f"buur[{index}] is geen object")
    fout = _bronverwijzingsfout(item)
    if fout:
        raise OngeldigeBurenlijstError(f"buur[{index}]: {fout}")
    term = _tekst(item.get("term"))
    if not term:
        raise OngeldigeBurenlijstError(f"buur[{index}] heeft geen term")
    herkomst = item.get("herkomst")
    if herkomst not in HERKOMSTEN:
        raise OngeldigeBurenlijstError(
            f"buur[{index}] heeft een onbekende herkomst {herkomst!r}"
        )
    bevestigd = item.get("bevestigd")
    if not isinstance(bevestigd, bool):
        raise OngeldigeBurenlijstError(
            f"buur[{index}]: bevestigd moet waar of onwaar zijn"
        )
    definitie = item.get("definitie")
    if definitie is not None and not isinstance(definitie, str):
        raise OngeldigeBurenlijstError(
            f"buur[{index}]: definitie moet tekst of leeg zijn"
        )
    return Buur(
        id=_tekst(item.get("id")) or buur_id(herkomst, term),
        term=term,
        definitie=_tekst(definitie) or None,
        herkomst=herkomst,
        bevestigd=bevestigd,
    )


def normaliseer_buren(ruw: Any) -> tuple[Buur, ...]:
    """De actieve burenlijst; afgewezen buren vallen weg. Fail-closed."""
    if ruw is None:
        return ()
    if not isinstance(ruw, (list, tuple)):
        raise OngeldigeBurenlijstError("burenlijst is geen lijst")
    buren: list[Buur] = []
    gezien: set[str] = set()
    for index, item in enumerate(ruw):
        if isinstance(item, Mapping) and item.get("afgewezen") is True:
            continue
        buur = _buur_uit(item, index)
        if buur.id in gezien:
            raise OngeldigeBurenlijstError(
                f"buur {buur.term!r} staat dubbel in de lijst"
            )
        gezien.add(buur.id)
        buren.append(buur)
    return tuple(buren)


def _repositoryrij(rij: Any) -> tuple[str, str, str | None] | None:
    if not isinstance(rij, Mapping) or rij.get("id") is None:
        return None
    term = _tekst(rij.get("begrip"))
    if not term:
        return None
    return f"repository:{rij['id']}", term, _tekst(rij.get("definitie")) or None


def stel_burenlijst_samen(
    opgeslagen: Any, repository: Iterable[Any] | None
) -> tuple[tuple[Buur, ...], tuple[str, ...]]:
    """(actieve buren, afgewezen termen) uit opgeslagen besluiten + verse repository.

    Een repository-buur komt altijd vers uit de database (actuele term en
    definitie); een opgeslagen besluit erover (bevestigd/afgewezen) blijft
    alleen gelden zolang die buur nog bestaat. Nieuwe repository-buren zijn
    onbevestigd. Afgewezen buren gaan niet mee, maar hun term blijft bekend
    zodat een afgewezen voorstel niet terugkeert.
    """
    if opgeslagen is not None and not isinstance(opgeslagen, (list, tuple)):
        raise OngeldigeBurenlijstError("opgeslagen burenlijst is geen lijst")
    vers = {
        rij[0]: rij for rij in (_repositoryrij(r) for r in (repository or ())) if rij
    }
    actief: list[dict[str, Any]] = []
    afgewezen: list[str] = []
    besloten: set[str] = set()
    for index, item in enumerate(opgeslagen or ()):
        if not isinstance(item, Mapping):
            raise OngeldigeBurenlijstError(f"opgeslagen buur[{index}] is geen object")
        entry = dict(item)
        if entry.get("herkomst") == "repository":
            rij = vers.get(_tekst(entry.get("id")))
            if rij is None:
                continue
            besloten.add(rij[0])
            entry.update({"id": rij[0], "term": rij[1], "definitie": rij[2]})
        if entry.get("afgewezen") is True:
            if _tekst(entry.get("term")):
                afgewezen.append(_tekst(entry.get("term")))
            continue
        actief.append(entry)
    for sleutel in sorted(set(vers) - besloten):
        _, term, definitie = vers[sleutel]
        actief.append(
            {
                "id": sleutel,
                "term": term,
                "definitie": definitie,
                "herkomst": "repository",
                "bevestigd": False,
            }
        )
    return normaliseer_buren(actief), tuple(afgewezen)


def _met_gebruikersburen(opgeslagen: Any, termen: Any, repository: list[Any]) -> Any:
    """De opgeslagen buren plus de door de gebruiker genoemde verwante begrippen.

    `gerelateerde_begrippen` is gebruikersinvoer en telt als bevestigd (§3).
    Een term die al als opgeslagen buur bestaat (ook afgewezen) wordt niet
    verdubbeld; een term die een repository-buur is, bevestigt die buur in
    plaats van een tweede buur te maken. Een ongeldige opgeslagen lijst gaat
    ongewijzigd door, zodat `stel_burenlijst_samen` haar fail-closed afwijst.
    """
    if opgeslagen is not None and not isinstance(opgeslagen, (list, tuple)):
        return opgeslagen
    lijst = [deepcopy(item) for item in (opgeslagen or ())]
    if not isinstance(termen, (list, tuple)):
        return lijst
    bekend = {_tekst(i.get("term")).casefold() for i in lijst if isinstance(i, Mapping)}
    besloten = {_tekst(i.get("id")) for i in lijst if isinstance(i, Mapping)}
    vers = {
        rij[1].casefold(): rij[0]
        for rij in (_repositoryrij(r) for r in repository)
        if rij
    }
    for term in termen:
        schoon = _tekst(term)
        sleutel = schoon.casefold()
        if not schoon or sleutel in bekend:
            continue
        bekend.add(sleutel)
        if sleutel in vers:
            if vers[sleutel] not in besloten:
                lijst.append(
                    {
                        "id": vers[sleutel],
                        "term": schoon,
                        "herkomst": "repository",
                        "bevestigd": True,
                    }
                )
            continue
        lijst.append(
            {
                "term": schoon,
                "definitie": None,
                "herkomst": "gebruiker",
                "bevestigd": True,
            }
        )
    return lijst


def stel_actieve_buren_samen(
    opgeslagen: Any,
    gerelateerde_begrippen: Any,
    repository: Iterable[Any] | None,
) -> tuple[tuple[Buur, ...], tuple[str, ...]]:
    """(actieve buren, afgewezen termen): besluiten + gebruikersinvoer + verse repository.

    Eén samenstelling voor de wrapper (vóór de AI-aanroep) en de editor (na
    een expertbesluit, zonder AI-aanroep). Fail-closed via
    `OngeldigeBurenlijstError`.
    """
    rijen = list(repository or ())
    return stel_burenlijst_samen(
        _met_gebruikersburen(opgeslagen, gerelateerde_begrippen, rijen), rijen
    )


def repositoryrijen_uit(buren: Iterable[Any] | None) -> list[dict[str, Any]]:
    """De repository-rijen die een eerdere samenstelling gebruikte (voor herbinding).

    Zo speelt de editor een besluit af op exact de buren van de toetsing,
    zonder databaselookup; bij de volgende toetsing komen ze weer vers.
    """
    rijen: list[dict[str, Any]] = []
    for buur in buren or ():
        item = buur.als_dict() if isinstance(buur, Buur) else buur
        if not isinstance(item, Mapping) or item.get("herkomst") != "repository":
            continue
        id_ = _tekst(item.get("id"))
        if id_.startswith("repository:"):
            rijen.append(
                {
                    "id": id_.removeprefix("repository:"),
                    "begrip": item.get("term"),
                    "definitie": item.get("definitie"),
                }
            )
    return rijen


# --- vingerafdruk en materiaal --------------------------------------------------------


def heeft_context(contexten: Mapping[str, Any] | None) -> bool:
    contexten = contexten or {}
    return any(contextsleutel(contexten.get(veld)) for veld in CONTEXT_VELDEN)


def _canoniek(bronnen: Any) -> tuple[Bronidentiteit, ...]:
    if isinstance(bronnen, tuple) and all(
        isinstance(b, Bronidentiteit) for b in bronnen
    ):
        return bronnen
    return canoniseer_bronnen(bronnen)


def bereken_ess05_vingerafdruk(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen: Any,
    *,
    intentie: Intentie | None = None,
    buren: Iterable[Buur] = (),
) -> str:
    """Bind een beoordeling aan term, tekst, context, bedoelde betekenis, bronnen en buren.

    Per buur tellen id, term, definitie en herkomst; de bevestigingsstatus
    niet — die weegt de code bij elke toetsing opnieuw mee, zodat een
    deskundig besluit geen nieuwe modelaanroep vergt. Een ESS-03-verduidelijking
    hoort bij ESS-03 en telt hier niet.
    """
    contexten = contexten or {}
    betekenis = replace(intentie or Intentie(), verduidelijking=None)
    basis = {
        "versie": CONTRACTVERSIE,
        "term": str(begrip or ""),
        "tekst": str(tekst or ""),
        "context": {
            veld: list(contextsleutel(contexten.get(veld))) for veld in CONTEXT_VELDEN
        },
        "intentie": betekenis.als_dict(),
        "bronnen": [b.vingerafdrukdeel() for b in _canoniek(bronnen)],
        "buren": sorted([b.id, b.term, b.definitie or "", b.herkomst] for b in buren),
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def contextmateriaal(contexten: Mapping[str, Any] | None) -> str:
    """De context als één bewijsplaats: `veld: waarde, waarde` per regel."""
    contexten = contexten or {}
    regels = []
    for veld in CONTEXT_VELDEN:
        waarden = canoniseer_contextlijst(contexten.get(veld))
        if waarden:
            regels.append(f"{veld}: {', '.join(waarden)}")
    return "\n".join(regels)


def betekenismateriaal(intentie: Intentie | None) -> str:
    """De bedoelde betekenis als bewijsplaats (de opgegeven categorie is geen bewijs)."""
    intentie = intentie or Intentie()
    regels = [
        f"{naam}: {waarde.strip()}"
        for naam, waarde in (
            ("toelichting", intentie.toelichting),
            ("betekenisverduidelijking", intentie.betekenisverduidelijking),
        )
        if isinstance(waarde, str) and waarde.strip()
    ]
    return "\n".join(regels)


def beoordelingsmateriaal(
    begrip: str,
    tekst: str,
    bronnen: Any,
    buren: Iterable[Buur],
    *,
    contexten: Mapping[str, Any] | None = None,
    intentie: Intentie | None = None,
) -> dict[str, str]:
    """Het verzonden materiaal: kern, context, bedoelde betekenis, bronnen, buren.

    Elke vindplaats is een bewijsplaats voor claims (`/2`); een onderscheidend
    kernfragment of kernkenmerk komt alleen uit `definition`. Context en
    bedoelde betekenis zijn alleen een vindplaats als ze niet leeg zijn. De
    term reist mee in de prompt, niet als bewijsplaats.
    """
    del begrip  # de term is geen bewijsplaats
    # Robuustheid P1 (punt 2): definitie- en buurteksten zonder categorie-
    # voorregel en bronlabels; model, dekking en citaten zien dezelfde tekst.
    materiaal: dict[str, str] = {
        _LOCATIE_DEFINITIE: neutraliseer_definitieruis(str(tekst or ""))
    }
    for locatie, inhoud in (
        ("context", contextmateriaal(contexten)),
        ("meaning", betekenismateriaal(intentie)),
    ):
        if inhoud:
            materiaal[locatie] = inhoud
    for bron in _canoniek(bronnen):
        materiaal[f"{_BRONPREFIX}{bron.source_id}"] = bron.passage
    for buur in buren:
        materiaal[f"{_BUURPREFIX}{buur.id}"] = neutraliseer_definitieruis(
            buur.definitie or ""
        )
    return materiaal


def bindingscontext(
    buren: Iterable[Buur], uitgesloten_termen: Iterable[str]
) -> dict[str, list[Any]]:
    """Wat de vingerafdruk bewust níet bevat maar beide stappen wel bindt (ADR-003).

    Buurstatussen (bevestigd of niet) en afgewezen voorstellen. Wijzigt een
    van beide na de beoordeling, dan is die beoordeling niet meer actueel en
    is een nieuwe, expliciete toetsing nodig.
    """
    return {
        "neighbour_status": sorted([b.id, bool(b.bevestigd)] for b in buren),
        "rejected_terms": sorted(
            {_tekst(t).casefold() for t in uitgesloten_termen if _tekst(t)}
        ),
    }


# --- binding -------------------------------------------------------------------------


@dataclass(frozen=True)
class Ess05Beoordelingsbinding:
    """De actuele binding van beide ESS-05-stappen (ADR-003).

    ESS-05-eigen type: de ESS-03-`Beoordelingsbinding` blijft ongewijzigd.
    Bindt beoordelings- en verificatieprompt, concept-, verificatie- en
    rendererversie, norm en beide provider/model-identiteiten.

    `answer_schema_version` bepaalt met welke antwoordversie de replay het
    concept opnieuw afleidt (`concept_derivation`). Het is geen documentveld en
    staat daarom niet in `als_dict`; de actuele binding is answer/2, een
    historisch answer/1-document geldt alleen onder een binding die die
    versie expliciet noemt.
    """

    prompt_version: str
    verification_prompt_version: str
    norm_sha256: str
    provider: str | None
    model: str | None
    verification_provider: str | None
    verification_model: str | None
    schema_version: str = CONCEPTSCHEMA
    verification_schema_version: str = VERIFICATIESCHEMA
    renderer_version: str = RENDERERVERSIE
    answer_schema_version: str = ANTWOORDSCHEMA

    def als_dict(self) -> dict[str, str | None]:
        return {
            "prompt_version": self.prompt_version,
            "verification_prompt_version": self.verification_prompt_version,
            "schema_version": self.schema_version,
            "verification_schema_version": self.verification_schema_version,
            "renderer_version": self.renderer_version,
            "norm_sha256": self.norm_sha256,
            "provider": self.provider,
            "model": self.model,
            "verification_provider": self.verification_provider,
            "verification_model": self.verification_model,
        }

    @classmethod
    def uit_dict(cls, waarde: Any) -> Ess05Beoordelingsbinding | None:
        """Fail-closed: exact de bindingsvelden, versies en norm als tekst.

        De antwoordversie staat niet in het document en is dus de actuele.
        """
        if not isinstance(waarde, Mapping):
            return None
        velden = set(cls.__dataclass_fields__) - {"answer_schema_version"}
        if set(waarde) != velden:
            return None
        verplicht = velden - {
            "provider",
            "model",
            "verification_provider",
            "verification_model",
        }
        if not all(_tekst(waarde[v]) for v in verplicht):
            return None
        if not all(
            waarde[v] is None or isinstance(waarde[v], str) for v in velden - verplicht
        ):
            return None
        return cls(**{v: waarde[v] for v in velden})


#: De binding van een van beide ESS-05-routes. Sinds DEF-768 stap 2 levert de
#: app de bewijsregelbinding (`ess05/3`); de ess05/2-binding blijft bestaan
#: voor de oude, niet meer aangesloten route en haar documenten.
Ess05Binding = Ess05Beoordelingsbinding | app.Ess05Bewijsregelbinding


def binding_uit_dict(waarde: Any) -> Ess05Binding | None:
    """De binding uit haar opgeslagen vorm, welke route ook (fail-closed)."""
    return app.Ess05Bewijsregelbinding.uit_dict(
        waarde
    ) or Ess05Beoordelingsbinding.uit_dict(waarde)


# --- beoordelingsdocumenten ----------------------------------------------------------


def _lege_attributie() -> dict[str, Any]:
    return {
        "provider": None,
        "model": None,
        "task_type": None,
        "cached": None,
        "tokens_used": None,
    }


def _basisdocument(fingerprint: str, status: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": None,
        "verification_prompt_version": None,
        "schema_version": CONCEPTSCHEMA,
        "verification_schema_version": VERIFICATIESCHEMA,
        "renderer_version": RENDERERVERSIE,
        "norm_sha256": None,
        "fingerprint": fingerprint,
        "status": status,
        "error": None,
        "assessed_at": None,
        "verified_at": None,
        "attribution": _lege_attributie(),
        "verification_attribution": _lege_attributie(),
        "input": None,
        "verification_input": None,
        "concept": None,
        "verification": None,
        "judgment": None,
        "rejected": [],
        "raw_response": None,
        "raw_response_sha256": None,
        "concept_derivation": None,
        "verification_raw_response_sha256": None,
    }


def afleidingsbinding(
    raw_response_sha256: str, concept: Ess05Concept, materiaal: Mapping[str, str]
) -> dict[str, Any]:
    """De binding van het afgeleide concept aan ruwe respons en materiaal.

    `raw_response_sha256` is de hash van de ongewijzigd bewaarde ruwe
    respons; `concept_hash` is de kandidaat die de verifier toetst.
    """
    return {
        "answer_schema_version": ANTWOORDSCHEMA,
        "raw_response_sha256": raw_response_sha256,
        "material": materiaalhashes(materiaal),
        "concept_hash": concept.hash,
    }


def beoordeling_niet_beschikbaar(fingerprint: str, reden: str) -> dict[str, Any]:
    document = _basisdocument(fingerprint, "unavailable")
    document["reason"] = str(reden or "ESS-05-beoordelingsdienst niet beschikbaar")
    return document


def beoordeling_technische_fout(
    fingerprint: str,
    soort: str,
    melding: str,
    *,
    prompt_version: str | None = None,
    norm_sha256: str | None = None,
    attribution: Mapping[str, Any] | None = None,
    phase: str = FASE_BEOORDELING,
) -> dict[str, Any]:
    """Foutdocument zonder toepasbaar oordeel; `phase` zegt welke stap faalde."""
    document = _basisdocument(fingerprint, "error")
    document["prompt_version"] = prompt_version
    document["norm_sha256"] = norm_sha256
    document["error"] = {
        "type": str(soort or "unknown"),
        "message": str(melding or ""),
        "phase": str(phase or FASE_BEOORDELING),
    }
    document["attribution"].update(dict(attribution or {}))
    return document


# --- validatie van de modeluitvoer ---------------------------------------------------


@dataclass(frozen=True)
class GevalideerdOnderscheid:
    """Het toegepaste oordeel: vaste weergave van een geverifieerd concept.

    Ontstaat uitsluitend via `pas_verificatie_toe` (volledige, positieve,
    exact gebonden verificatie). `lacks_differentia` is afgeleid uit de
    goedgekeurde kenmerkenlijst; alle teksten zijn gecontroleerde claims.
    """

    lacks_differentia: bool
    reason: str
    neighbours: tuple[dict[str, Any], ...]
    proposed_neighbours: tuple[dict[str, Any], ...]
    question: str | None

    def als_dict(self) -> dict[str, Any]:
        return {
            "lacks_differentia": self.lacks_differentia,
            "reason": self.reason,
            "neighbours": [dict(n) for n in self.neighbours],
            "proposed_neighbours": [dict(p) for p in self.proposed_neighbours],
            "question": self.question,
        }


def valideer_concept(
    ruw: Any, materiaal: Mapping[str, str], buren: Iterable[Buur]
) -> tuple[Ess05Concept | None, list[dict[str, Any]]]:
    """Vaste controle van het conceptoordeel (eerste stap). Fail-closed.

    Een structuurfout of één niet-verifieerbare bewijsplaats maakt het hele
    concept onbruikbaar; dan start er geen verificatie. Een geslaagde controle
    zegt niets over semantische juistheid.
    """
    return bewijs.valideer_concept(ruw, materiaal, {b.id: b.definitie for b in buren})


def valideer_antwoord(
    ruw: Any,
    materiaal: Mapping[str, str],
    buren: Iterable[Buur],
    *,
    schema: str = ANTWOORDSCHEMA,
) -> tuple[Ess05Concept | None, list[dict[str, Any]]]:
    """Leid het concept af uit het modelantwoord in precies `schema`. Fail-closed.

    Standaard het actuele answer/2 (genest, citaat-eerst); de app kent de ID's
    toe, voegt identieke citaten en claims samen en bepaalt elke bewijsplaats
    zelf, alleen bij precies één letterlijke treffer in het aangewezen
    materiaal; daarna gelden dezelfde vaste controles als bij
    `valideer_concept`. Het historische answer/1 alleen als die versie
    expliciet is gevraagd. Geen reparatie, geen herinterpretatie van een
    antwoord in een ander schema.
    """
    return bewijs.valideer_antwoord(
        ruw, materiaal, {b.id: b.definitie for b in buren}, schema=schema
    )


def _filter_voorstellen(
    voorstellen: list[Mapping[str, Any]],
    bekend: set[str],
    rejected: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Voorstellen van een bekende, afgewezen of dubbele term vallen zichtbaar weg."""
    gehouden: list[dict[str, Any]] = []
    for item in voorstellen:
        term = _tekst(item["term"])
        if term.casefold() in bekend:
            rejected.append(
                {"reason": "voorstel genegeerd: al bekend of afgewezen", "detail": term}
            )
            continue
        bekend.add(term.casefold())
        gehouden.append(dict(item, term=term))
    return tuple(gehouden)


def _render(
    concept: Ess05Concept,
    buren: Iterable[Buur],
    *,
    begrip: str,
    uitgesloten_termen: Iterable[str],
) -> tuple[GevalideerdOnderscheid, list[dict[str, Any]]]:
    """Vaste weergave (`RENDERERVERSIE`): alleen gecontroleerde claims en citaten."""
    data = concept.data

    def claim(ref: str | None) -> str | None:
        return concept.claimtekst([ref]) if ref else None

    buuroordelen = tuple(
        {
            "neighbour_id": n["neighbour_id"],
            "distinction": n["distinction"],
            "distinguishing_feature_quote": concept.citaat(n["feature_evidence"]),
            "missing_feature": claim(n["missing_feature_claim"]),
            "reason": concept.claimtekst(n["reason_claims"]),
            "uncertainty": claim(n["uncertainty_claim"]),
        }
        for n in data["neighbours"]
    )
    rejected: list[dict[str, Any]] = []
    bekend = {str(begrip or "").strip().casefold()}
    bekend.update(b.term.casefold() for b in buren)
    bekend.update(_tekst(t).casefold() for t in uitgesloten_termen)
    voorstellen = _filter_voorstellen(
        [
            {
                "term": p["term"],
                "source_id": concept.bron_van(p["source_evidence"]),
                "quote": concept.citaat(p["source_evidence"]),
                "reason": concept.claimtekst(p["reason_claims"]),
            }
            for p in data["proposals"]
        ],
        bekend,
        rejected,
    )
    vraag = data["question"]
    return (
        GevalideerdOnderscheid(
            lacks_differentia=concept.lacks_differentia,
            reason=concept.claimtekst(data["reason_claims"]),
            neighbours=buuroordelen,
            proposed_neighbours=voorstellen,
            question=_tekst(vraag["text"]) if vraag is not None else None,
        ),
        rejected,
    )


def pas_verificatie_toe(
    concept: Ess05Concept,
    verificatie: Any,
    buren: Iterable[Buur],
    *,
    begrip: str,
    uitgesloten_termen: Iterable[str] = (),
) -> tuple[GevalideerdOnderscheid | None, Verificatieuitkomst, list[dict[str, Any]]]:
    """Het toepasbare oordeel, alleen na volledige, positieve verificatie.

    (oordeel, uitkomst, genegeerde voorstellen). Zonder vrijgave is het oordeel
    None: een ongeverifieerd concept wordt nooit als motivering weergegeven.
    """
    uitkomst = toets_verificatie(verificatie, concept)
    if not uitkomst.goedgekeurd:
        return None, uitkomst, []
    oordeel, rejected = _render(
        concept, tuple(buren), begrip=begrip, uitgesloten_termen=uitgesloten_termen
    )
    return oordeel, uitkomst, rejected


# --- replay --------------------------------------------------------------------------

#: Eén controle: (faalt?, melding). Lui geëvalueerd, in volgorde; een latere
#: controle mag aannemen dat de eerdere slaagden.
_Controle = tuple[Callable[[], bool], str]


def _eerste_fout(controles: Iterable[_Controle]) -> str | None:
    """De melding van de eerste falende controle, of None."""
    for faalt, melding in controles:
        if faalt():
            return melding
    return None


def _lege_samenvatting() -> dict[str, Any]:
    return {
        "applied": False,
        "historical": False,
        "status": None,
        "reason": None,
        "error_type": None,
        "phase": None,
        "model": None,
        "provider": None,
        "verification_model": None,
        "verification_provider": None,
        "prompt_version": None,
        "verification_prompt_version": None,
        "schema_version": None,
        "verification_schema_version": None,
        "renderer_version": None,
        "norm_sha256": None,
        "expected_binding": None,
        "verification": None,
        "rejected": 0,
        # Robuustheid P1 (punt 4): onbruikbare modeluitvoer, geen storing.
        "unusable": False,
    }


def _statusafwijzing(assessment: Mapping[str, Any]) -> str | None:
    status = assessment.get("status")
    if status == "unavailable":
        return _tekst(assessment.get("reason")) or "ESS-05-dienst niet beschikbaar"
    if status == "error":
        fout = assessment.get("error")
        fout = fout if isinstance(fout, Mapping) else {}
        fase = _tekst(fout.get("phase"))
        soort = (
            "AI-uitvoer niet bruikbaar"
            if onbruikbare_modeluitvoer(assessment)
            else "technische fout"
        )
        return (
            f"{soort} ({_tekst(fout.get('type')) or 'unknown'}"
            f"{f', fase {fase}' if fase else ''}): {_tekst(fout.get('message'))}"
        ).strip()
    if status != "assessed":
        return f"onbekende beoordelingsstatus {status!r}"
    return None


def _bindingsafwijzing(
    samenvatting: Mapping[str, Any], binding: Ess05Beoordelingsbinding | None
) -> str | None:
    """Welk bindingsveld (prompts, versies, norm, beide modellen) afwijkt, of None."""
    for veld, verwacht in (binding.als_dict() if binding else {}).items():
        if (samenvatting.get(veld) or None) != (verwacht or None):
            return (
                f"beoordeling hoort bij {veld} {samenvatting.get(veld)!r}; "
                f"actueel is {verwacht!r}"
            )
    return None


def _gebonden(assessment: Mapping[str, Any], sleutel: str) -> Mapping[str, Any]:
    invoer = assessment.get(sleutel)
    return invoer if isinstance(invoer, Mapping) else {}


def _actualiteitsafwijzing(
    assessment: Mapping[str, Any],
    samenvatting: Mapping[str, Any],
    fingerprint: str,
    materiaal: Mapping[str, str],
    context: Mapping[str, Any],
    binding: Ess05Beoordelingsbinding | None,
) -> str | None:
    invoer = _gebonden(assessment, "input")
    verificatie_invoer = _gebonden(assessment, "verification_input")
    hashes = materiaalhashes(materiaal)
    return (
        _eerste_fout(
            (
                (
                    lambda: assessment.get("contract_version") != CONTRACTVERSIE,
                    (
                        "beoordeling hoort bij contractversie "
                        f"{assessment.get('contract_version')!r}"
                    ),
                ),
                (
                    lambda: _tekst(assessment.get("fingerprint")) != fingerprint,
                    (
                        "eerdere beoordeling geldt niet meer: tekst, context, term, "
                        "bedoelde betekenis, bronnen of verwante begrippen zijn gewijzigd"
                    ),
                ),
                (
                    lambda: not samenvatting.get("model")
                    or not samenvatting.get("verification_model"),
                    "beoordeling of verificatie zonder benoemd model (herkomst onbekend)",
                ),
                (
                    lambda: binding is None,
                    "actuele beoordelingsbinding onbekend (geen ESS-05-dienst beschikbaar)",
                ),
            )
        )
        or _bindingsafwijzing(samenvatting, binding)
        or _eerste_fout(
            (
                (
                    lambda: invoer.get("materiaal") != hashes
                    or verificatie_invoer.get("materiaal") != hashes,
                    "materiaal gewijzigd sinds de beoordeling",
                ),
                (
                    lambda: any(invoer.get(k) != v for k, v in context.items()),
                    (
                        "buurbevestiging of afgewezen voorstellen gewijzigd sinds de "
                        "beoordeling; toets opnieuw"
                    ),
                ),
            )
        )
    )


def _vul_samenvatting(
    samenvatting: dict[str, Any], assessment: Mapping[str, Any]
) -> None:
    samenvatting["status"] = assessment.get("status")
    for veld in (
        "prompt_version",
        "verification_prompt_version",
        "schema_version",
        "verification_schema_version",
        "renderer_version",
        "norm_sha256",
    ):
        samenvatting[veld] = assessment.get(veld)
    for sleutel, voorvoegsel in (
        ("attribution", ""),
        ("verification_attribution", "verification_"),
    ):
        attributie = _gebonden(assessment, sleutel)
        samenvatting[f"{voorvoegsel}model"] = _tekst(attributie.get("model")) or None
        samenvatting[f"{voorvoegsel}provider"] = (
            _tekst(attributie.get("provider")) or None
        )
    fout = _gebonden(assessment, "error")
    samenvatting["error_type"] = _tekst(fout.get("type")) or None
    samenvatting["phase"] = _tekst(fout.get("phase")) or None
    samenvatting["unusable"] = onbruikbare_modeluitvoer(assessment)


def _afleidingsafwijzing(
    assessment: Mapping[str, Any],
    materiaal: Mapping[str, str],
    buren: tuple[Buur, ...],
    antwoordschema: str,
) -> str | None:
    """Waarom het opgeslagen concept niet de afleiding van de ruwe respons is, of None.

    De ruwe respons moet ongewijzigd bewaard zijn (hash), de afleidingsbinding
    moet exact bij de gebonden antwoordversie, respons, huidig materiaal en
    concept horen, en opnieuw afleiden uit die respons, met precies die
    antwoordversie, moet exact het opgeslagen concept geven.
    """
    ruw = assessment.get("raw_response")
    ruwhash = assessment.get("raw_response_sha256")
    if not isinstance(ruw, str) or (
        hashlib.sha256(ruw.encode("utf-8")).hexdigest() != ruwhash
    ):
        return "ruwe respons ontbreekt of hoort niet bij raw_response_sha256"
    concept = assessment.get("concept")
    verwacht = {
        "answer_schema_version": antwoordschema,
        "raw_response_sha256": ruwhash,
        "material": materiaalhashes(materiaal),
        "concept_hash": bewijs.concepthash(concept),
    }
    afleiding = assessment.get("concept_derivation")
    afleiding = afleiding if isinstance(afleiding, Mapping) else {}
    afwijkend = sorted(
        {k for k in verwacht if afleiding.get(k) != verwacht[k]}
        | (set(afleiding) - set(verwacht))
    )
    if afwijkend:
        return f"afleidingsbinding wijkt af ({', '.join(afwijkend)})"
    afgeleid, _ = valideer_antwoord(
        parse_modeluitvoer(ruw), materiaal, buren, schema=antwoordschema
    )
    if afgeleid is None or dict(afgeleid.data) != concept:
        return "opgeslagen concept is niet afgeleid uit de bewaarde ruwe respons"
    return None


def _geverifieerd_oordeel(
    assessment: Mapping[str, Any],
    materiaal: Mapping[str, str],
    buren: tuple[Buur, ...],
    *,
    begrip: str,
    uitgesloten_termen: Iterable[str],
    antwoordschema: str,
) -> tuple[GevalideerdOnderscheid | None, str, dict[str, Any] | None]:
    """(oordeel, reden-als-niet, verificatiesamenvatting) opnieuw uit het document.

    Het opgeslagen `judgment` is alleen weergave: replay leidt het oordeel
    opnieuw af uit concept + verificatie. Ontbreekt of faalt de verificatie,
    dan is er geen toepasbaar oordeel. Het concept moet bovendien exact de
    afleiding zijn van de bewaarde ruwe respons op dit materiaal, in de
    gebonden antwoordversie.
    """
    reden = _afleidingsafwijzing(assessment, materiaal, buren, antwoordschema)
    if reden is not None:
        return None, f"beoordeling zonder gebonden afleiding: {reden}", None
    concept, fouten = valideer_concept(assessment.get("concept"), materiaal, buren)
    if concept is None:
        return (
            None,
            "beoordeling zonder bruikbaar concept: "
            + str(fouten[0]["detail"] if fouten else "onbekend"),
            None,
        )
    if (
        _gebonden(assessment, "verification_input").get("candidate_hash")
        != concept.hash
    ):
        return None, "verificatie hoort niet bij dit conceptoordeel", None
    oordeel, uitkomst, _ = pas_verificatie_toe(
        concept,
        assessment.get("verification"),
        buren,
        begrip=begrip,
        uitgesloten_termen=uitgesloten_termen,
    )
    verificatie = {"approved": uitkomst.goedgekeurd, "type": uitkomst.soort}
    if oordeel is None:
        return (
            None,
            f"beoordeling zonder geldige semantische verificatie: {uitkomst.melding}",
            verificatie,
        )
    return oordeel, "", verificatie


def _bewijsregelafwijzing(
    assessment: Mapping[str, Any],
    samenvatting: Mapping[str, Any],
    fingerprint: str,
    materiaal: Mapping[str, str],
    context: Mapping[str, Any],
    binding: Ess05Binding | None,
) -> str | None:
    """Waarom een document niet als actueel `ess05/3`-oordeel mag gelden, of None.

    Een ess05/2-document is verouderd (besluit D): de oude route is niet meer
    aangesloten en wordt niet afgespeeld.
    """
    versie = assessment.get("contract_version")
    invoer = _gebonden(assessment, "input")
    opgeslagen = _gebonden(assessment, "binding")
    return _eerste_fout(
        (
            (
                lambda: versie != app.DOCUMENTVERSIE,
                (
                    f"verouderd — toets opnieuw: deze beoordeling (contractversie "
                    f"{versie!r}) komt van de vorige ESS-05-route"
                ),
            ),
            (
                lambda: _tekst(assessment.get("fingerprint")) != fingerprint,
                (
                    "eerdere beoordeling geldt niet meer: tekst, context, term, "
                    "bedoelde betekenis, bronnen of verwante begrippen zijn gewijzigd"
                ),
            ),
            (
                lambda: binding is None,
                "actuele beoordelingsbinding onbekend (geen ESS-05-dienst beschikbaar)",
            ),
            (
                lambda: not isinstance(binding, app.Ess05Bewijsregelbinding),
                (
                    "verouderd — toets opnieuw: de actuele binding hoort bij een "
                    "andere ESS-05-route"
                ),
            ),
        )
    ) or _eerste_fout(
        (
            *(
                (
                    lambda veld=veld, verwacht=verwacht: opgeslagen.get(veld)
                    != verwacht,
                    (
                        f"beoordeling hoort bij {veld} {opgeslagen.get(veld)!r}; "
                        f"actueel is {verwacht!r}"
                    ),
                )
                for veld, verwacht in (binding.als_dict() if binding else {}).items()
            ),
            (
                lambda: (
                    assessment.get("interpretation") is not None
                    and not samenvatting.get("model")
                )
                or (
                    bool(assessment.get("controls"))
                    and not samenvatting.get("verification_model")
                ),
                "interpretatie of controle zonder benoemd model (herkomst onbekend)",
            ),
            (
                lambda: invoer.get("materiaal") != materiaalhashes(materiaal),
                "materiaal gewijzigd sinds de beoordeling",
            ),
            (
                lambda: any(invoer.get(k) != v for k, v in context.items()),
                (
                    "buurbevestiging of afgewezen voorstellen gewijzigd sinds de "
                    "beoordeling; toets opnieuw"
                ),
            ),
        )
    )


def _valideer_bewijsregels(
    assessment: Mapping[str, Any],
    samenvatting: dict[str, Any],
    fingerprint: str,
    materiaal: Mapping[str, str],
    buren: tuple[Buur, ...],
    *,
    begrip: str,
    uitgesloten: tuple[str, ...],
    binding: Ess05Binding | None,
) -> tuple[app.Bewijsregeloordeel | None, dict[str, Any]]:
    """Replay van een `ess05/3`-document: binding en materiaal, dan de regels opnieuw."""
    reden = _bewijsregelafwijzing(
        assessment,
        samenvatting,
        fingerprint,
        materiaal,
        bindingscontext(buren, uitgesloten),
        binding,
    )
    if reden is not None:
        samenvatting.update({"reason": reden, "historical": binding is not None})
        return None, samenvatting
    invoer = br.Vergelijkingsinvoer(
        begrip, materiaal, tuple((b.id, b.term) for b in buren)
    )
    oordeel, reden = app.speel_af(assessment, invoer)
    controles = assessment.get("controls")
    samenvatting["verification"] = {
        "approved": oordeel is not None,
        "type": "lokale_controles",
        "controls": len(controles) if isinstance(controles, list) else 0,
    }
    if oordeel is None:
        samenvatting["reason"] = (
            f"beoordeling zonder geldige bewijsregelcontrole: {reden}"
        )
        return None, samenvatting
    samenvatting["applied"] = True
    return oordeel, samenvatting


def _valideer_beoordeling(
    assessment: Any,
    fingerprint: str,
    materiaal: Mapping[str, str],
    buren: tuple[Buur, ...],
    *,
    begrip: str,
    uitgesloten_termen: Iterable[str],
    binding: Ess05Binding | None,
) -> tuple[GevalideerdOnderscheid | app.Bewijsregeloordeel | None, dict[str, Any]]:
    samenvatting = _lege_samenvatting()
    samenvatting["expected_binding"] = binding.als_dict() if binding else None
    if not isinstance(assessment, Mapping):
        samenvatting["reason"] = "AI-beoordeling niet uitgevoerd"
        return None, samenvatting
    _vul_samenvatting(samenvatting, assessment)
    reden = _statusafwijzing(assessment)
    if reden is not None:
        samenvatting["reason"] = reden
        return None, samenvatting
    uitgesloten = tuple(uitgesloten_termen)
    if assessment.get("contract_version") == app.DOCUMENTVERSIE or isinstance(
        binding, app.Ess05Bewijsregelbinding
    ):
        return _valideer_bewijsregels(
            assessment,
            samenvatting,
            fingerprint,
            materiaal,
            buren,
            begrip=begrip,
            uitgesloten=uitgesloten,
            binding=binding,
        )
    # Hier is de binding de ess05/2-binding of None (de tak hierboven nam de rest).
    oud = binding if isinstance(binding, Ess05Beoordelingsbinding) else None
    reden = _actualiteitsafwijzing(
        assessment,
        samenvatting,
        fingerprint,
        materiaal,
        bindingscontext(buren, uitgesloten),
        oud,
    )
    if reden is not None:
        samenvatting.update({"reason": reden, "historical": oud is not None})
        return None, samenvatting
    oordeel, reden, verificatie = _geverifieerd_oordeel(
        assessment,
        materiaal,
        buren,
        begrip=begrip,
        uitgesloten_termen=uitgesloten,
        # Na de actualiteitscontrole is er altijd een binding.
        antwoordschema=oud.answer_schema_version if oud else ANTWOORDSCHEMA,
    )
    samenvatting["verification"] = verificatie
    if oordeel is None:
        samenvatting["reason"] = reden
        return None, samenvatting
    opgeslagen = assessment.get("rejected")
    samenvatting["rejected"] = len(opgeslagen) if isinstance(opgeslagen, list) else 0
    samenvatting["applied"] = True
    return oordeel, samenvatting


def beoordelingsafwijzing(
    assessment: Any,
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen_ruw: Any,
    *,
    intentie: Intentie | None,
    buren: Any,
    binding: Ess05Binding,
    uitgesloten_termen: Iterable[str] = (),
) -> str | None:
    """Waarom `assessment` níet als actueel ESS-05-bewijs mag gelden, of None.

    Dezelfde volledige controle als de replay (ADR-003): contractversie,
    vingerafdruk, alle bindingsvelden, materiaal, bindingscontext en een
    opnieuw afgeleid, gecontroleerd oordeel (ess05/2: semantisch goedgekeurd
    concept; ess05/3: interpretatie plus lokale controles). Alleen `None` als
    de replay het oordeel daadwerkelijk zou toepassen.
    """
    try:
        actief = normaliseer_buren(buren)
    except OngeldigeBurenlijstError as exc:
        return f"ongeldige burenlijst: {exc}"
    bronnen = canoniseer_bronnen(bronnen_ruw)
    fingerprint = bereken_ess05_vingerafdruk(
        begrip, tekst, contexten, bronnen, intentie=intentie, buren=actief
    )
    materiaal = beoordelingsmateriaal(
        begrip, tekst, bronnen, actief, contexten=contexten, intentie=intentie
    )
    oordeel, samenvatting = _valideer_beoordeling(
        assessment,
        fingerprint,
        materiaal,
        actief,
        begrip=begrip,
        uitgesloten_termen=uitgesloten_termen,
        binding=binding,
    )
    if oordeel is not None:
        return None
    return _tekst(samenvatting.get("reason")) or "beoordeling niet toepasbaar"


# --- samenvoeging --------------------------------------------------------------------


@dataclass(frozen=True)
class Ess05Uitkomst:
    """De samengestelde ESS-05-uitkomst: status, vingerafdruk, onderdelen, review."""

    status: str
    fingerprint: str
    parts: tuple[Deeluitkomst, ...]
    review: dict[str, Any]

    def als_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": None,
            "contract_version": CONTRACTVERSIE,
            "fingerprint": self.fingerprint,
            "parts": [p.als_dict() for p in self.parts],
            "review": deepcopy(self.review),
        }


def _q(term: str) -> str:
    return f"‘{term.replace('?', '')}’"


def _buurstatus(buur: Buur, onderscheid: str) -> str:
    if onderscheid == "distinguished":
        return STATUS_PASS
    if onderscheid == "not_distinguished" and buur.bevestigd:
        return STATUS_FAIL
    return STATUS_OPEN


def _buurdeel(buur: Buur, item: Mapping[str, Any]) -> Deeluitkomst:
    status = _buurstatus(buur, item["distinction"])
    herkomst = f"{buur.herkomst}, {'bevestigd' if buur.bevestigd else 'onbevestigd'}"
    delen = [f"Ten opzichte van {_q(buur.term)} ({herkomst}): {item['reason']}"]
    citaat = item["distinguishing_feature_quote"]
    if citaat and buur.definitie and vind_citaat(buur.definitie, citaat):
        delen.append(
            "Signaal: het citaat staat ook in de buurdefinitie; het onderscheid "
            "moet uit betekenis of context blijken (de code toetst dat niet)."
        )
    if item["missing_feature"]:
        delen.append(f"Ontbrekend of te ruim kenmerk: {item['missing_feature']}.")
    if item["uncertainty"]:
        delen.append(f"Onzekerheid: {item['uncertainty']}")
    actie = {STATUS_PASS: _ACTIE_PASS, STATUS_FAIL: _ACTIE_FAIL}.get(
        status, _ACTIE_VRAAG
    )
    return Deeluitkomst(
        id=f"{_BUURPREFIX}{buur.id}",
        status=status,
        reason=" ".join(delen),
        action=actie,
        evidence=item["distinguishing_feature_quote"],
        context_value=buur.term,
        field=BASIS_ASSESSMENT,
    )


def _voorstellen_als_buren(oordeel: GevalideerdOnderscheid) -> list[dict[str, Any]]:
    """Elk modelvoorstel is `herkomst=model`, onbevestigd (K-1).

    Een `source_id` + letterlijk `quote` (door `valideer_oordeel` al tegen de
    verzonden bronpassage gecontroleerd) blijft als aparte bronverwijzing
    staan; het maakt het voorstel geen bronbuur.
    """
    uitvoer = []
    for voorstel in oordeel.proposed_neighbours:
        uitvoer.append(
            {
                "id": buur_id("model", voorstel["term"]),
                "term": voorstel["term"],
                "definitie": None,
                "herkomst": "model",
                "bevestigd": False,
                "source_id": voorstel["source_id"],
                "quote": voorstel["quote"],
                "reason": voorstel["reason"],
            }
        )
    return uitvoer


def _kies_vraag(
    begrip: str,
    oordeel: GevalideerdOnderscheid,
    buren: Mapping[str, Buur],
    voorstellen: list[dict[str, Any]],
) -> str | None:
    """Precies één vraag, in vaste prioriteit; None als niets open staat."""
    per_buur = {n["neighbour_id"]: n["distinction"] for n in oordeel.neighbours}
    return _vraag_uit(
        begrip, per_buur, oordeel.question, buren, [v["term"] for v in voorstellen]
    )


def _vraag_uit(
    begrip: str,
    per_buur: Mapping[str, str],
    modelvraag: str | None,
    buren: Mapping[str, Buur],
    voorsteltermen: list[str],
) -> str | None:
    """De ene vraag van het app-beleid, voor beide routes (besluit B)."""
    onduidelijk = [
        b for b in buren.values() if b.bevestigd and per_buur[b.id] == "unclear"
    ]
    if onduidelijk:
        return modelvraag or (
            f"Wat onderscheidt {_q(begrip)} in deze context van {_q(onduidelijk[0].term)}?"
        )
    onbevestigd = [
        b.term
        for b in buren.values()
        if not b.bevestigd and b.herkomst in _ONBEVESTIGD_VOORSTEL
    ] + voorsteltermen
    if onbevestigd:
        termen = ", ".join(_q(t) for t in onbevestigd)
        return f"Zijn {termen} verwante begrippen die deze definitie moet uitsluiten?"
    twijfel = [
        b.term
        for b in buren.values()
        if not b.bevestigd and per_buur[b.id] != "distinguished"
    ]
    if twijfel:
        return f"Moet deze definitie zich onderscheiden van {_q(twijfel[0])}?"
    if not any(b.bevestigd for b in buren.values()):
        if buren:
            termen = ", ".join(_q(b.term) for b in buren.values())
            return (
                f"Zijn {termen} de verwante begrippen die deze definitie moet "
                "uitsluiten, of ontbreken er nog?"
            )
        return _VRAAG_GEEN_BUREN
    return None


def _samenvatting_deel(
    status: str, reden: str, actie: str, field: str | None = BASIS_ASSESSMENT
) -> Deeluitkomst:
    return Deeluitkomst(
        id=ONDERDEEL_ONDERSCHEID, status=status, reason=reden, action=actie, field=field
    )


def _samenvoegen(
    begrip: str,
    oordeel: GevalideerdOnderscheid,
    buren: tuple[Buur, ...],
    model: str,
) -> tuple[str, list[Deeluitkomst], str | None, list[dict[str, Any]]]:
    per_id = {b.id: b for b in buren}
    buurdelen = [_buurdeel(per_id[n["neighbour_id"]], n) for n in oordeel.neighbours]
    voorstellen = _voorstellen_als_buren(oordeel)
    kop = f"AI-beoordeling van onderscheid ({model}): {oordeel.reason}"
    if oordeel.lacks_differentia:
        reden = (
            "ESS-05 — Voldoet niet: de definitie kan zonder toespitsing geen enkel "
            f"verwant begrip uitsluiten. {kop}"
        )
        return (
            STATUS_FAIL,
            [_samenvatting_deel(STATUS_FAIL, reden, _ACTIE_FAIL), *buurdelen],
            None,
            voorstellen,
        )
    niet = [
        (per_id[n["neighbour_id"]], n["missing_feature"])
        for n in oordeel.neighbours
        if n["distinction"] == "not_distinguished"
        and per_id[n["neighbour_id"]].bevestigd
    ]
    if niet:
        opsomming = "; ".join(f"{_q(b.term)} (ontbreekt: {k})" for b, k in niet)
        reden = f"ESS-05 — Voldoet niet: niet onderscheiden van {opsomming}. {kop}"
        return (
            STATUS_FAIL,
            [_samenvatting_deel(STATUS_FAIL, reden, _ACTIE_FAIL), *buurdelen],
            None,
            voorstellen,
        )
    vraag = _kies_vraag(begrip, oordeel, per_id, voorstellen)
    if vraag is not None:
        reden = f"ESS-05 — Open: {vraag} {kop}"
        return (
            STATUS_OPEN,
            [_samenvatting_deel(STATUS_OPEN, reden, _ACTIE_VRAAG), *buurdelen],
            vraag,
            voorstellen,
        )
    reden = (
        f"ESS-05 — Voldoet: onderscheiden van alle bevestigde verwante begrippen. {kop}"
    )
    return (
        STATUS_PASS,
        [_samenvatting_deel(STATUS_PASS, reden, _ACTIE_PASS), *buurdelen],
        None,
        voorstellen,
    )


#: Buuroordeel van de bewijsregels → onderscheid in de termen van het app-beleid.
_ONDERSCHEID_VAN = {
    "onderscheiden": "distinguished",
    "niet_onderscheiden": "not_distinguished",
    "open": "unclear",
}


def _bewijsregelbuurdeel(
    buur: Buur, oordeel: br.Buuroordeel, regels: br.Regeluitkomst
) -> Deeluitkomst:
    """Eén buur van de bewijsregelroute als deeluitkomst, met het app-beleid (B)."""
    status = _buurstatus(buur, _ONDERSCHEID_VAN[oordeel.oordeel])
    herkomst = f"{buur.herkomst}, {'bevestigd' if buur.bevestigd else 'onbevestigd'}"
    delen = [
        f"Ten opzichte van {_q(buur.term)} ({herkomst}):",
        *br.buurweergave(regels, oordeel),
    ]
    if oordeel.oordeel == "niet_onderscheiden" and not buur.bevestigd:
        delen.append(
            "Deze buur is nog niet bevestigd: bevestig of wijs haar af; pas een "
            "bevestigde buur maakt dit een 'voldoet niet'."
        )
    kenmerken = {k.id: k for k in regels.kenmerken}
    citaten = [
        kenmerken[a.kenmerk_id].citaat
        for a in oordeel.aspecten
        if a.aspect == "afgrenzend" and kenmerken[a.kenmerk_id].citaat
    ]
    actie = {STATUS_PASS: _ACTIE_PASS, STATUS_FAIL: _ACTIE_FAIL}.get(
        status, _ACTIE_VRAAG
    )
    return Deeluitkomst(
        id=f"{_BUURPREFIX}{buur.id}",
        status=status,
        reason=" ".join(delen),
        action=actie,
        evidence=citaten[0] if citaten else None,
        context_value=buur.term,
        field=BASIS_ASSESSMENT,
    )


def _samenvoegen_bewijsregels(
    begrip: str,
    oordeel: app.Bewijsregeloordeel,
    buren: tuple[Buur, ...],
    model: str,
) -> tuple[str, list[Deeluitkomst], str | None]:
    """(status, onderdelen, vraag) van de bewijsregelroute onder het app-beleid (B).

    Kern zonder kenmerk → fail; niet onderscheiden van een bevestigde buur →
    fail; anders de ene vraag van het app-beleid (onbevestigde buur, open
    oordeel, geen bevestigde buur) → open; anders voldoet. Zonder buren (D)
    is er geen AI-aanroep en is de vraag welke verwante begrippen er zijn.
    Modelvoorstellen bestaan in deze route niet (A).
    """
    regels = oordeel.regels
    if regels is None:
        reden = (
            f"ESS-05 — Open: {_VRAAG_GEEN_BUREN} Er zijn in deze context geen "
            "verwante begrippen bekend; er is geen AI-beoordeling uitgevoerd."
        )
        return (
            STATUS_OPEN,
            [_samenvatting_deel(STATUS_OPEN, reden, _ACTIE_VRAAG)],
            _VRAAG_GEEN_BUREN,
        )
    kop = f"Beoordeling met bewijsregels ({model})."
    if regels.kern_zonder_kenmerk:
        reden = (
            "ESS-05 — Voldoet niet: de kern drukt naast het bovenbegrip geen "
            f"kenmerk uit. {kop}"
        )
        return STATUS_FAIL, [_samenvatting_deel(STATUS_FAIL, reden, _ACTIE_FAIL)], None
    per_id = {b.id: b for b in buren}
    buurdelen = [
        _bewijsregelbuurdeel(per_id[b.buur_id], b, regels) for b in regels.buren
    ]
    niet = [
        per_id[b.buur_id]
        for b in regels.buren
        if b.oordeel == "niet_onderscheiden" and per_id[b.buur_id].bevestigd
    ]
    if niet:
        opsomming = ", ".join(_q(b.term) for b in niet)
        reden = f"ESS-05 — Voldoet niet: niet onderscheiden van {opsomming}. {kop}"
        deel = _samenvatting_deel(STATUS_FAIL, reden, _ACTIE_FAIL)
        return STATUS_FAIL, [deel, *buurdelen], None
    per_buur = {b.buur_id: _ONDERSCHEID_VAN[b.oordeel] for b in regels.buren}
    vraag = _vraag_uit(begrip, per_buur, None, per_id, [])
    if vraag is not None:
        reden = f"ESS-05 — Open: {vraag} {kop}"
        deel = _samenvatting_deel(STATUS_OPEN, reden, _ACTIE_VRAAG)
        return STATUS_OPEN, [deel, *buurdelen], vraag
    reden = (
        f"ESS-05 — Voldoet: onderscheiden van alle bevestigde verwante begrippen. {kop}"
    )
    return (
        STATUS_PASS,
        [_samenvatting_deel(STATUS_PASS, reden, _ACTIE_PASS), *buurdelen],
        None,
    )


def _lege_ruimte_afwijzing(lege_ruimte: Any, fingerprint: str) -> str | None:
    if not isinstance(lege_ruimte, Mapping):
        return "geen bevestiging van een lege vergelijkingsruimte"
    if lege_ruimte.get("contract_version") != CONTRACTVERSIE:
        return "bevestiging hoort bij een andere contractversie"
    if _tekst(lege_ruimte.get("fingerprint")) != fingerprint:
        return "bevestiging geldt niet meer: term, tekst, context, betekenis of bronnen gewijzigd"
    if not _tekst(lege_ruimte.get("grond")) or not _tekst(lege_ruimte.get("actor")):
        return "bevestiging zonder grond of deskundige telt niet"
    return None


def lege_ruimte_geldig(lege_ruimte: Any, fingerprint: str) -> bool:
    """Of een deskundige bevestiging 'vergelijkingsruimte leeg' voor deze invoer geldt."""
    return _lege_ruimte_afwijzing(lege_ruimte, fingerprint) is None


def _uitkomst(
    status: str, fingerprint: str, deel: Deeluitkomst, **review: Any
) -> Ess05Uitkomst:
    return Ess05Uitkomst(
        status=status, fingerprint=fingerprint, parts=(deel,), review=dict(review)
    )


def beoordeel_onderscheid(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen_ruw: Any,
    *,
    intentie: Intentie | None = None,
    buren: Any = None,
    lege_ruimte: Any = None,
    assessment: Any = None,
    binding: Ess05Binding | None = None,
    uitgesloten_termen: Iterable[str] = (),
) -> Ess05Uitkomst:
    """De ESS-05-uitkomst van één kandidaattekst (replay, zonder AI-aanroep)."""
    ontbrekend = _ontbrekende_invoer(begrip, tekst, contexten)
    if ontbrekend is not None:
        return ontbrekend
    try:
        actief = normaliseer_buren(buren)
    except OngeldigeBurenlijstError as exc:
        deel = _samenvatting_deel(
            STATUS_ERROR,
            f"De ESS-05-controle kon niet worden uitgevoerd: ongeldige burenlijst ({exc}).",
            _ACTIE_FOUT,
        )
        return _uitkomst(STATUS_ERROR, "", deel)

    bronnen = canoniseer_bronnen(bronnen_ruw)
    fingerprint = bereken_ess05_vingerafdruk(
        begrip, tekst, contexten, bronnen, intentie=intentie, buren=actief
    )
    buurlijst = [b.als_dict() for b in actief]
    lege_reden = None
    if not actief:
        lege_reden = _lege_ruimte_afwijzing(lege_ruimte, fingerprint)
        if lege_reden is None:
            deel = _samenvatting_deel(
                STATUS_PASS,
                "ESS-05 — Voldoet: een deskundige bevestigde gemotiveerd dat er in "
                f"deze context geen verwante begrippen zijn ({_tekst(lege_ruimte.get('grond'))}).",
                _ACTIE_PASS,
                BASIS_LEGE_RUIMTE,
            )
            return _uitkomst(
                STATUS_PASS,
                fingerprint,
                deel,
                neighbours=[],
                empty_space=dict(lege_ruimte),
            )

    materiaal = beoordelingsmateriaal(
        begrip, tekst, bronnen, actief, contexten=contexten, intentie=intentie
    )
    try:
        oordeel, samenvatting = _valideer_beoordeling(
            assessment,
            fingerprint,
            materiaal,
            actief,
            begrip=begrip,
            uitgesloten_termen=uitgesloten_termen,
            binding=binding,
        )
    except Exception as exc:  # pragma: no cover - defensief: replay mag nooit crashen
        logger.warning("ESS-05: replay mislukte: %s", type(exc).__name__, exc_info=True)
        oordeel, samenvatting = None, {**_lege_samenvatting(), "reason": "onleesbaar"}

    review: dict[str, Any] = {
        "assessment": samenvatting,
        "neighbours": buurlijst,
        "question": None,
        "proposals": [],
    }
    if lege_reden and lege_ruimte is not None:
        review["empty_space_rejected"] = lege_reden
    return _uitkomst_uit_oordeel(
        begrip, oordeel, samenvatting, actief, fingerprint, review
    )


def _ontbrekende_invoer(
    begrip: str, tekst: str, contexten: Mapping[str, Any] | None
) -> Ess05Uitkomst | None:
    """`not_evaluated` zonder term, tekst of context (context is verplicht)."""
    if not _tekst(begrip) or not _tekst(tekst):
        reden = "ESS-05 niet beoordeeld: term of definitietekst ontbreekt."
    elif not heeft_context(contexten):
        reden = (
            "ESS-05 niet beoordeeld: zonder context is niet te bepalen welke "
            "verwante begrippen de definitie moet uitsluiten."
        )
    else:
        return None
    deel = _samenvatting_deel(STATUS_NOT_EVALUATED, reden, _ACTIE_INVOER, None)
    return _uitkomst(STATUS_NOT_EVALUATED, "", deel)


def _uitkomst_uit_oordeel(
    begrip: str,
    oordeel: GevalideerdOnderscheid | app.Bewijsregeloordeel | None,
    samenvatting: Mapping[str, Any],
    actief: tuple[Buur, ...],
    fingerprint: str,
    review: dict[str, Any],
) -> Ess05Uitkomst:
    """Technische fout, open (niet of historisch beoordeeld) of samengevoegd oordeel."""
    if samenvatting.get("unusable"):
        # Robuustheid P1 (punt 4): onbruikbare modeluitvoer is geen storing maar
        # een open punt voor de gebruiker, met een korte reden.
        soort = _tekst(samenvatting.get("error_type"))
        reden = (
            "De AI kon dit niet betrouwbaar automatisch beoordelen; beoordeel "
            f"handmatig. Reden: {_ONBRUIKBAAR[soort]} ({soort})."
        )
        deel = _samenvatting_deel(STATUS_OPEN, reden, _ACTIE_HANDMATIG)
        return Ess05Uitkomst(STATUS_OPEN, fingerprint, (deel,), review)
    if samenvatting.get("status") == "error":
        if samenvatting.get("error_type") == FOUT_SEMANTISCH:
            reden = (
                "De ESS-05-controle leverde geen bruikbaar oordeel: de semantische "
                "verificatie keurde het modeloordeel niet goed. Dit is geen oordeel "
                "over de definitie en er is geen inhoudelijke uitkomst gegeven "
                f"({samenvatting.get('reason')})."
            )
        elif samenvatting.get("error_type") == FOUT_CONTROLE:
            reden = (
                "De ESS-05-controle leverde geen bruikbaar oordeel: een lokale "
                "controle keurde de interpretatie van het materiaal niet goed. Dit is "
                "geen oordeel over de definitie en er is geen inhoudelijke uitkomst "
                f"gegeven ({samenvatting.get('reason')})."
            )
        else:
            reden = (
                "De ESS-05-controle kon niet worden uitgevoerd; er is geen "
                f"inhoudelijk oordeel gegeven ({samenvatting.get('reason')})."
            )
        deel = _samenvatting_deel(STATUS_ERROR, reden, _ACTIE_FOUT)
        return Ess05Uitkomst(STATUS_ERROR, fingerprint, (deel,), review)
    if oordeel is None:
        historisch = samenvatting.get("historical")
        reden = (
            f"De eerdere AI-beoordeling is historisch en geldt niet als actueel "
            f"oordeel: {samenvatting.get('reason')}."
            if historisch
            else f"Het onderscheid is niet beoordeeld: {samenvatting.get('reason')}."
        )
        deel = _samenvatting_deel(
            STATUS_OPEN,
            reden,
            _ACTIE_NIET_BEOORDEELD,
            BASIS_ASSESSMENT if samenvatting.get("status") else None,
        )
        return Ess05Uitkomst(STATUS_OPEN, fingerprint, (deel,), review)

    if isinstance(oordeel, app.Bewijsregeloordeel):
        model = (
            f"interpretatie door {samenvatting.get('model') or 'onbekend model'}; "
            "lokaal gecontroleerd door "
            f"{samenvatting.get('verification_model') or 'onbekend model'}"
        )
        status, delen, vraag = _samenvoegen_bewijsregels(begrip, oordeel, actief, model)
        review.update({"question": vraag, "proposals": []})
        return Ess05Uitkomst(status, fingerprint, tuple(delen), review)
    model = (
        f"{samenvatting.get('model') or 'onbekend model'}; semantisch geverifieerd "
        f"door {samenvatting.get('verification_model') or 'onbekend model'}"
    )
    status, delen, vraag, voorstellen = _samenvoegen(begrip, oordeel, actief, model)
    review.update({"question": vraag, "proposals": voorstellen})
    return Ess05Uitkomst(status, fingerprint, tuple(delen), review)
