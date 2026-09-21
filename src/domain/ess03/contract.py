"""ESS-03 — het telbaarheidscontract (DEF-766, besluiten van 19 en 21 september 2026).

Pure domeinlogica, zonder Streamlit, database of AI-client. De evaluator
(`services.validation.evaluators.countability_assessment`) roept
`beoordeel_telbaarheid` aan en vertaalt de uitkomst naar het runtimecontract;
de beoordelingsdienst (`services.validation.ess03_assessment_service`) gebruikt
`structuurfout_modeluitvoer` en `valideer_oordeel` om de modeluitvoer
fail-closed te valideren; de persistentie- en UI-laag gebruiken
`bereken_ess03_vingerafdruk` en `valideer_beoordeling` om een opgeslagen
beoordeling aan exact dezelfde invoer te binden.

Wat de regel toetst: maakt de definitiekern bij de bedoelde betekenis
voldoende duidelijk wat als één, dezelfde of een andere instantie geldt — met
voldoende grond voor de relevante eenheidsgrens en een eventuele
continuïteitsconventie? Een naam, nummer, code of het woord 'uniek' bewijst
op zichzelf niets; een niet-telbare stof-, kwaliteits- of verschijnsellezing
valt buiten toepassing.

Vier inhoudelijke uitkomsten (`verdict`) van de AI, elk met onderbouwing en
door code gecontroleerde bewijsplaatsen:

- **pass** — voldoet: de kern draagt de eenheidsgrens (bewijs uit kandidaat,
  bedoelde betekenis, context of aangeleverde bron);
- **fail** — voldoet niet: een aantoonbaar gebrek in de kern of een gesteld
  onderscheidingsmiddel dat de bedoelde instanties niet onderscheidt;
- **not_applicable** — niet van toepassing: geen telbare eenheid bedoeld,
  met grond; een afgeronde uitkomst, geen ontbrekende invoer en niet stil
  gelijk aan 'voldoet';
- **insufficient_information** — onvoldoende informatie: de beslisgrond voor
  de hoofdvraag ontbreekt (noodzakelijke conventie, bron of keuze); precies
  één gerichte vraag.

Rolverdeling: **code** controleert binding (vingerafdruk), gesloten
statussen, citaatbestaan (staat het citaat letterlijk in het werkelijk
aangeleverde materiaal?) en consistentie; de **AI** beoordeelt eenheid,
onderscheid en toepasselijkheid op uitsluitend het aangeleverde materiaal.
Een technische fout is apart herkenbaar (`error`) en nooit pass of fail. Geen
cijfer. Een negatieve uitkomst is zichtbaar en uitlegbaar, maar geen
vaststel- of exportblokkade (besluit 21 september 2026).

Alles is gebonden aan een vingerafdruk over term, exacte kandidaattekst, de
drie contextlijsten, de bedoelde betekenis (toelichting, opgegeven categorie
als te controleren claim, betekenisverduidelijking, ESS-03-verduidelijking)
en de canonieke bronidentiteiten. Wijzigt daar iets, dan geldt een eerdere
beoordeling niet meer.

Volledige binding (correctieronde 1, R1): naast de vingerafdruk is een
opgeslagen beoordeling gebonden aan promptversie, normhash, provider en model
(`Beoordelingsbinding`, door de dienst zonder netwerk geleverd) én aan de
hashes van het werkelijk verzonden materiaal (`materiaalhashes`, onder
`input.materiaal`). `valideer_beoordeling(..., binding=)` wijst elke afwijking
af als historisch (`historical`), met de verwachte binding erbij; hash-
aanwezigheid alleen is geen bewijs. Gesloten antwoord (R2/R3): exact de
afgesproken velden en typen, minstens één bewijsplaats bij een afgerond
oordeel, precies één gerichte vraag bij onvoldoende informatie; één
niet-verifieerbaar citaat maakt het hele oordeel ongeldig (`valideer_oordeel`
geeft dan geen oordeel, alleen de afgewezen items).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from domain.context.contract import CONTEXT_VELDEN, Deeluitkomst
from domain.context.normalisatie import canoniseer_contextlijst, contextsleutel
from domain.sources.contract import vind_citaat
from domain.sources.normalisatie import Bronidentiteit, canoniseer_bronnen

logger = logging.getLogger(__name__)

__all__ = [
    "APPLICABILITIES",
    "ASSESSMENT_STATUSSEN",
    "BASIS_ASSESSMENT",
    "CONTRACTVERSIE",
    "LOCATIE_CONTEXT",
    "LOCATIE_DEFINITIE",
    "LOCATIE_TERM",
    "LOCATIE_TOELICHTING",
    "LOCATIE_VERDUIDELIJKING",
    "ONDERDEEL_TELBAARHEID",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_NOT_APPLICABLE",
    "STATUS_OPEN",
    "STATUS_PASS",
    "VERDICTS",
    "VERDICT_FAIL",
    "VERDICT_INSUFFICIENT",
    "VERDICT_NOT_APPLICABLE",
    "VERDICT_PASS",
    "Beoordelingsbinding",
    "Ess03Uitkomst",
    "GevalideerdOordeel",
    "Intentie",
    "beoordeel_telbaarheid",
    "beoordeling_niet_beschikbaar",
    "beoordeling_technische_fout",
    "beoordelingsmateriaal",
    "bereken_ess03_vingerafdruk",
    "intentie_uit_context",
    "materiaalhashes",
    "status_voor_verdict",
    "structuurfout_modeluitvoer",
    "valideer_beoordeling",
    "valideer_oordeel",
]

#: Beleidsversie van dit contract; onderdeel van de vingerafdruk.
CONTRACTVERSIE = "ess03/1"

#: Het ene zichtbare onderdeel van ESS-03 in `rule_results`.
ONDERDEEL_TELBAARHEID = "countability"

#: Waarde van `Deeluitkomst.field`: het oordeel komt van de AI-beoordeling.
BASIS_ASSESSMENT = "ess03_assessment"

VERDICT_PASS = "pass"
VERDICT_FAIL = "fail"
VERDICT_NOT_APPLICABLE = "not_applicable"
VERDICT_INSUFFICIENT = "insufficient_information"
VERDICTS: tuple[str, ...] = (
    VERDICT_PASS,
    VERDICT_FAIL,
    VERDICT_NOT_APPLICABLE,
    VERDICT_INSUFFICIENT,
)

#: Toepasselijkheid zoals het model haar benoemt; moet met het verdict stroken.
APPLICABILITIES: tuple[str, ...] = ("applicable", "not_applicable", "undetermined")

#: Deelstatussen (spiegelen `toetsregels.runtime_contract.ResultStatus`).
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_NOT_APPLICABLE = "not_applicable"
STATUS_OPEN = "review_required"
STATUS_ERROR = "error"

#: Technische status van een verkregen beoordeling.
ASSESSMENT_STATUSSEN: tuple[str, ...] = ("assessed", "error", "unavailable")

#: Vindplaatsen waaruit een citaat mag komen (naast `source:<bron-id>`).
LOCATIE_DEFINITIE = "definition"
LOCATIE_TERM = "term"
LOCATIE_TOELICHTING = "toelichting"
LOCATIE_VERDUIDELIJKING = "verduidelijking"
LOCATIE_CONTEXT = "context"
_BRONPREFIX = "source:"

_ACTIE_NIET_BEOORDEELD = (
    "Valideer opnieuw; de ESS-03-beoordeling wordt daarbij automatisch uitgevoerd."
)
_ACTIE_FOUT = (
    "Controleer opnieuw. Blijft dit terugkomen, meld het dan als technisch probleem."
)
_ACTIE_PASS = "Geen actie nodig."
_ACTIE_FAIL = (
    "Maak in de kern duidelijk wat als één instantie geldt en waardoor instanties "
    "worden onderscheiden, of lever de ontbrekende conventie/bron aan. Toetsen "
    "wijzigt de tekst niet; een verbetervoorstel volgt alleen op verzoek."
)
_ACTIE_NA = (
    "Geen afzonderlijke identificatie vereist. Is wél een telbare eenheid bedoeld, "
    "leg die dan vast in de bedoelde betekenis en toets opnieuw."
)
_ACTIE_VRAAG = (
    "Beantwoord de vraag in de ESS-03-verduidelijking bij deze kandidaat en toets "
    "opnieuw; de definitie wordt niet automatisch herschreven."
)
_ACTIE_ONBEWEZEN = (
    "Toets opnieuw. Blijft het oordeel zonder aantoonbaar citaat, laat een "
    "deskundige de eenheidsgrens beoordelen."
)
_ACTIE_HISTORISCH = (
    "Valideer opnieuw; de eerdere beoordeling blijft als historie bewaard en "
    "geldt niet meer als actueel oordeel."
)

#: De gesloten veldenset van het modelantwoord (correctieronde 1, R2).
_ANTWOORDVELDEN: frozenset[str] = frozenset(
    {
        "verdict",
        "applicability",
        "unit",
        "reason",
        "evidence",
        "missing_information",
        "question",
        "uncertainty",
    }
)
_OPTIONELE_TEKSTVELDEN: tuple[str, ...] = (
    "unit",
    "missing_information",
    "question",
    "uncertainty",
)
_BEWIJSVELDEN: frozenset[str] = frozenset({"location", "quote"})


# --- bedoelde betekenis --------------------------------------------------------------


@dataclass(frozen=True)
class Intentie:
    """De bedoelde betekenis zoals zij náást de kandidaattekst is aangeleverd.

    `categorie` is de opgegeven (ontologische) categorie: een te controleren
    betekenisclaim, geen bewijs en geen vrijstelling. `verduidelijking` is het
    antwoord op een eerdere ESS-03-vraag, gebonden aan deze kandidaat.
    """

    toelichting: str | None = None
    categorie: str | None = None
    betekenisverduidelijking: str | None = None
    verduidelijking: str | None = None

    def als_dict(self) -> dict[str, str | None]:
        return {
            "toelichting": _tekst(self.toelichting) or None,
            "categorie": _tekst(self.categorie) or None,
            "betekenisverduidelijking": _tekst(self.betekenisverduidelijking) or None,
            "verduidelijking": _tekst(self.verduidelijking) or None,
        }


def intentie_uit_context(context: Mapping[str, Any] | None) -> Intentie:
    """De bedoelde betekenis uit een validatiecontext (record- of editorpad).

    Leest alleen wat er werkelijk staat: `toelichting` (top-level of onder
    `definition`), de opgegeven categorie (`ontologische_categorie` of
    `categorie`), `betekenisverduidelijking` (DEF-751) en
    `ess03_verduidelijking`. Niets wordt verzonnen.
    """
    context = context or {}
    definitie = context.get("definition")
    toelichting = context.get("toelichting")
    if not _tekst(toelichting) and isinstance(definitie, Mapping):
        toelichting = definitie.get("toelichting")
    categorie = context.get("ontologische_categorie") or context.get("categorie")
    return Intentie(
        toelichting=_tekst(toelichting) or None,
        categorie=_tekst(categorie) or None,
        betekenisverduidelijking=_tekst(context.get("betekenisverduidelijking"))
        or None,
        verduidelijking=_tekst(context.get("ess03_verduidelijking")) or None,
    )


# --- vingerafdruk en materiaal --------------------------------------------------------


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _canoniek(bronnen: Any) -> tuple[Bronidentiteit, ...]:
    if isinstance(bronnen, tuple) and all(
        isinstance(b, Bronidentiteit) for b in bronnen
    ):
        return bronnen
    return canoniseer_bronnen(bronnen)


def bereken_ess03_vingerafdruk(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen: Any,
    *,
    intentie: Intentie | None = None,
) -> str:
    """Bind een beoordeling aan term, exacte tekst, context, bedoelde betekenis en bronnen.

    Per bron gaat de canonieke identiteit mee (`Bronidentiteit.vingerafdrukdeel`);
    zoekscore en promptvlaggen bewust niet. Een gewijzigde toelichting,
    categorie of verduidelijking maakt een eerdere beoordeling stale: de
    bedoelde betekenis is onderdeel van de beoordelingsvraag.
    """
    contexten = contexten or {}
    basis = {
        "versie": CONTRACTVERSIE,
        "term": str(begrip or ""),
        "tekst": str(tekst or ""),
        "context": {
            veld: list(contextsleutel(contexten.get(veld))) for veld in CONTEXT_VELDEN
        },
        "intentie": (intentie or Intentie()).als_dict(),
        "bronnen": [b.vingerafdrukdeel() for b in _canoniek(bronnen)],
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def beoordelingsmateriaal(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen: Any,
    intentie: Intentie | None,
) -> dict[str, str]:
    """Het werkelijk aangeleverde materiaal per vindplaats — de enige bewijsbasis.

    Alleen aanwezige vindplaatsen komen erin: zonder toelichting of
    verduidelijking bestaat die vindplaats niet, zodat een citaat 'uit de
    toelichting' bij een record zonder toelichting altijd wordt afgewezen.
    """
    contexten = contexten or {}
    intentie = intentie or Intentie()
    materiaal: dict[str, str] = {
        LOCATIE_DEFINITIE: str(tekst or ""),
        LOCATIE_TERM: str(begrip or ""),
    }
    if _tekst(intentie.toelichting):
        materiaal[LOCATIE_TOELICHTING] = _tekst(intentie.toelichting)
    if _tekst(intentie.verduidelijking):
        materiaal[LOCATIE_VERDUIDELIJKING] = _tekst(intentie.verduidelijking)
    contextwaarden = [
        waarde
        for veld in CONTEXT_VELDEN
        for waarde in canoniseer_contextlijst(contexten.get(veld))
    ]
    if _tekst(intentie.betekenisverduidelijking):
        contextwaarden.append(_tekst(intentie.betekenisverduidelijking))
    if contextwaarden:
        materiaal[LOCATIE_CONTEXT] = "\n".join(contextwaarden)
    for bron in _canoniek(bronnen):
        materiaal[f"{_BRONPREFIX}{bron.source_id}"] = bron.passage
    return materiaal


def materiaalhashes(materiaal: Mapping[str, str]) -> dict[str, str]:
    """sha256 (UTF-8, hex) per vindplaats van exact het verzonden materiaal.

    Dit is de materiaalbinding van een beoordeling (`input.materiaal`): bij
    replay moet het actuele materiaal dezelfde vindplaatsen met dezelfde
    hashes opleveren, anders is de beoordeling historisch (R1/R7).
    """
    return {
        locatie: hashlib.sha256(str(inhoud).encode("utf-8")).hexdigest()
        for locatie, inhoud in materiaal.items()
    }


@dataclass(frozen=True)
class Beoordelingsbinding:
    """De actuele beoordelingsconfiguratie waaraan een opgeslagen beoordeling
    moet voldoen om als actueel te gelden (correctieronde 1, R1).

    Promptversie en normhash zeggen wélke vraag het model kreeg; provider en
    model wie antwoordde. Wijkt een opgeslagen beoordeling hierin af, dan is
    zij historisch — zichtbaar, nooit stil actueel. De waarden komen zonder
    netwerk uit de dienst (`Ess03AssessmentService.binding()`): promptversie
    en norm uit code en regelrecord, provider/model uit de ModelRouter.
    """

    prompt_version: str
    norm_sha256: str
    provider: str | None
    model: str | None

    def als_dict(self) -> dict[str, str | None]:
        return {
            "prompt_version": self.prompt_version,
            "norm_sha256": self.norm_sha256,
            "provider": self.provider,
            "model": self.model,
        }


# --- beoordelingsdocumenten (store-ready dicts) ----------------------------------


def _basisdocument(fingerprint: str, status: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": None,
        "norm_sha256": None,
        "fingerprint": fingerprint,
        "status": status,
        "error": None,
        "assessed_at": None,
        "attribution": {
            "provider": None,
            "model": None,
            "task_type": None,
            "cached": None,
            "tokens_used": None,
        },
        "input": None,
        "judgment": None,
        "rejected": [],
        "raw_response_sha256": None,
    }


def beoordeling_niet_beschikbaar(fingerprint: str, reden: str) -> dict[str, Any]:
    """Een beoordeling die niet kon worden verkregen: geen dienst geïnjecteerd."""
    document = _basisdocument(fingerprint, "unavailable")
    document["reason"] = str(reden or "ESS-03-beoordelingsdienst niet beschikbaar")
    return document


def beoordeling_technische_fout(
    fingerprint: str,
    soort: str,
    melding: str,
    *,
    prompt_version: str | None = None,
    norm_sha256: str | None = None,
    attribution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Een beoordeling die technisch mislukte (timeout, misvormd antwoord, dienstfout)."""
    document = _basisdocument(fingerprint, "error")
    document["prompt_version"] = prompt_version
    document["norm_sha256"] = norm_sha256
    document["error"] = {"type": str(soort or "unknown"), "message": str(melding or "")}
    document["attribution"].update(dict(attribution or {}))
    return document


# --- validatie van de modeluitvoer ---------------------------------------------------


@dataclass(frozen=True)
class GevalideerdOordeel:
    """Het AI-oordeel na de codecontrole: verdict, afgeleide status, bewijs.

    `verdict` is wat het model zei; `status` is wat de code ervan laat
    gelden (een verdict zonder geverifieerd bewijs wordt `review_required`
    en blijft als verdict zichtbaar).
    """

    verdict: str
    status: str
    applicability: str
    unit: str | None
    reason: str
    evidence: tuple[dict[str, str], ...]
    missing_information: str | None
    question: str | None
    uncertainty: str | None

    def als_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "status": self.status,
            "applicability": self.applicability,
            "unit": self.unit,
            "reason": self.reason,
            "evidence": [dict(e) for e in self.evidence],
            "missing_information": self.missing_information,
            "question": self.question,
            "uncertainty": self.uncertainty,
        }


def status_voor_verdict(verdict: str) -> str:
    """De deelstatus die bij een (onderbouwd) verdict hoort."""
    return {
        VERDICT_PASS: STATUS_PASS,
        VERDICT_FAIL: STATUS_FAIL,
        VERDICT_NOT_APPLICABLE: STATUS_NOT_APPLICABLE,
        VERDICT_INSUFFICIENT: STATUS_OPEN,
    }[verdict]


def _is_een_gerichte_vraag(waarde: Any) -> bool:
    """Precies één gerichte vraag: niet-lege tekst die op '?' eindigt en één
    vraagteken bevat. Twee vragen in één string zijn niet de afgesproken vorm."""
    vraag = _tekst(waarde)
    return bool(vraag) and vraag.endswith("?") and vraag.count("?") == 1


def _bewijsstructuurfout(bewijs: list[Any]) -> str | None:
    for index, item in enumerate(bewijs):
        if not isinstance(item, Mapping):
            return f"evidence[{index}] is geen object"
        if set(item) != _BEWIJSVELDEN:
            return (
                f"evidence[{index}] heeft niet exact de velden location en quote "
                f"(gevonden: {sorted(item)})"
            )
        if not isinstance(item["location"], str) or not isinstance(item["quote"], str):
            return f"evidence[{index}]: location en quote moeten tekst zijn"
    return None


def _veldenfout(geparsed: Mapping[str, Any]) -> str | None:
    """Exact de acht antwoordvelden: niets onbekend, niets ontbrekend."""
    onbekend = sorted(set(geparsed) - _ANTWOORDVELDEN)
    if onbekend:
        return f"onbekend veld in antwoord: {', '.join(onbekend)}"
    ontbrekend = sorted(_ANTWOORDVELDEN - set(geparsed))
    if ontbrekend:
        return f"veld ontbreekt in antwoord: {', '.join(ontbrekend)}"
    return None


def _waardenfout(geparsed: Mapping[str, Any]) -> str | None:
    """Gesloten sets voor verdict/applicability; reason niet leeg; optionele
    tekstvelden tekst of null."""
    if geparsed["verdict"] not in VERDICTS:
        return f"verdict is onbekend: {geparsed['verdict']!r}"
    if geparsed["applicability"] not in APPLICABILITIES:
        return f"applicability is onbekend: {geparsed['applicability']!r}"
    if not isinstance(geparsed["reason"], str) or not _tekst(geparsed["reason"]):
        return "reason ontbreekt of is leeg"
    for veld in _OPTIONELE_TEKSTVELDEN:
        waarde = geparsed[veld]
        if waarde is not None and not isinstance(waarde, str):
            return f"{veld} moet tekst of null zijn"
    return None


def _bewijsfout(geparsed: Mapping[str, Any]) -> str | None:
    """Evidence is een lijst van {location, quote}; een afgerond verdict heeft
    minstens één item."""
    bewijs = geparsed["evidence"]
    if not isinstance(bewijs, list):
        return "evidence is geen lijst"
    bewijsfout = _bewijsstructuurfout(bewijs)
    if bewijsfout is not None:
        return bewijsfout
    if geparsed["verdict"] != VERDICT_INSUFFICIENT and not bewijs:
        return (
            f"afgerond oordeel '{geparsed['verdict']}' zonder bewijs (evidence is leeg)"
        )
    return None


def _consistentiefout(geparsed: Mapping[str, Any]) -> str | None:
    """Verdict en applicability stroken; question alleen — en precies één —
    bij insufficient_information."""
    verdict, applicability = geparsed["verdict"], geparsed["applicability"]
    if verdict == VERDICT_NOT_APPLICABLE and applicability != "not_applicable":
        return (
            f"applicability {applicability!r} strookt niet met verdict "
            f"'{VERDICT_NOT_APPLICABLE}'"
        )
    if verdict in (VERDICT_PASS, VERDICT_FAIL) and applicability != "applicable":
        return f"applicability {applicability!r} strookt niet met verdict '{verdict}'"
    vraag = geparsed["question"]
    if verdict == VERDICT_INSUFFICIENT and not _is_een_gerichte_vraag(vraag):
        return (
            "insufficient_information vereist precies één gerichte vraag "
            "(question: één zin die op '?' eindigt)"
        )
    if verdict != VERDICT_INSUFFICIENT and _tekst(vraag):
        return f"question is alleen toegestaan bij '{VERDICT_INSUFFICIENT}'"
    return None


#: In deze volgorde: elke controle mag op de vorige vertrouwen (velden aanwezig).
_STRUCTUURCONTROLES = (_veldenfout, _waardenfout, _bewijsfout, _consistentiefout)


def structuurfout_modeluitvoer(geparsed: Any) -> str | None:
    """Waarom het JSON-object niet de vereiste antwoordstructuur heeft, of None.

    Gesloten contract (correctieronde 1, R2): exact de acht antwoordvelden,
    geen onbekende velden; `verdict` en `applicability` uit hun gesloten set
    en onderling consistent; niet-lege `reason`; `evidence` een lijst van
    objecten met exact `location` en `quote` (tekst) en bij een afgerond
    verdict minstens één item; de optionele tekstvelden tekst of null;
    `question` uitsluitend bij `insufficient_information` en dan precies één
    gerichte vraag. Elke afwijking is een technische fout — geen stil herstel
    door tekst of velden weg te laten.
    """
    if not isinstance(geparsed, Mapping):
        return "geen object"
    for controle in _STRUCTUURCONTROLES:
        fout = controle(geparsed)
        if fout is not None:
            return fout
    return None


def _verifieer_bewijs(
    ruw: list[Mapping[str, str]],
    materiaal: Mapping[str, str],
    rejected: list[dict[str, Any]],
) -> tuple[dict[str, str], ...]:
    """Alleen bewijs dat letterlijk in het werkelijk aangeleverde materiaal staat.

    Elk afgewezen item landt in `rejected`; de aanroeper beslist dat één
    afgewezen item het hele oordeel onbruikbaar maakt (R3).
    """
    geverifieerd: list[dict[str, str]] = []
    for item in ruw:
        locatie = item["location"]
        citaat = item["quote"]
        if locatie not in materiaal:
            rejected.append(
                {"reason": "onbekende vindplaats", "detail": str(locatie)[:120]}
            )
            continue
        if not citaat.strip():
            rejected.append({"reason": "leeg citaat", "detail": locatie})
            continue
        if not vind_citaat(materiaal[locatie], citaat):
            rejected.append(
                {
                    "reason": "citaat niet in materiaal",
                    "detail": f"{locatie}: {citaat[:120]}",
                }
            )
            continue
        geverifieerd.append({"location": locatie, "quote": citaat})
    return tuple(geverifieerd)


def valideer_oordeel(
    ruw: Any, materiaal: Mapping[str, str]
) -> tuple[GevalideerdOordeel | None, list[dict[str, Any]]]:
    """Valideer één modeloordeel tegen het aangeleverde materiaal.

    Geeft (gevalideerd oordeel, []) of (None, afgewezen items). Fail-closed
    (correctieronde 1, R2/R3): een structuurfout of één niet-verifieerbaar
    bewijsitem (onbekende vindplaats, leeg citaat, citaat niet letterlijk in
    het materiaal) maakt het hele oordeel onbruikbaar — een reden waarvan een
    deel van de grond is afgewezen wordt nooit toegepast. De aanroeper
    behandelt `None` als technische fout (`unverifiable_evidence`).
    """
    structuurfout = structuurfout_modeluitvoer(ruw)
    if structuurfout is not None:
        return None, [{"reason": "structuurfout", "detail": structuurfout}]
    rejected: list[dict[str, Any]] = []
    verdict = str(ruw["verdict"])
    bewijs = _verifieer_bewijs(ruw["evidence"], materiaal, rejected)
    if rejected:
        return None, rejected
    return (
        GevalideerdOordeel(
            verdict=verdict,
            status=status_voor_verdict(verdict),
            applicability=str(ruw["applicability"]),
            unit=_tekst(ruw["unit"]) or None,
            reason=_tekst(ruw["reason"]),
            evidence=bewijs,
            missing_information=_tekst(ruw["missing_information"]) or None,
            question=_tekst(ruw["question"]) or None,
            uncertainty=_tekst(ruw["uncertainty"]) or None,
        ),
        [],
    )


# --- replay van een opgeslagen of zojuist verkregen beoordeling ------------------


def _statusafwijzing(assessment: Mapping[str, Any], status: Any) -> str | None:
    """Waarom een beoordeling op haar technische status al niet telt, of None."""
    if status == "unavailable":
        return (
            _tekst(assessment.get("reason"))
            or "ESS-03-beoordelingsdienst niet beschikbaar"
        )
    if status == "error":
        fout = assessment.get("error")
        soort = _tekst(fout.get("type")) if isinstance(fout, Mapping) else ""
        melding = _tekst(fout.get("message")) if isinstance(fout, Mapping) else ""
        return f"technische fout ({soort or 'unknown'}): {melding}".strip()
    if status != "assessed":
        return f"onbekende beoordelingsstatus {status!r}"
    return None


def _bindingsafwijzing(
    assessment: Mapping[str, Any], fingerprint: str, model: str | None
) -> str | None:
    if assessment.get("contract_version") != CONTRACTVERSIE:
        return (
            f"beoordeling hoort bij contractversie "
            f"{assessment.get('contract_version')!r}; actueel is {CONTRACTVERSIE!r}"
        )
    if _tekst(assessment.get("fingerprint")) != fingerprint:
        return (
            "eerdere beoordeling geldt niet meer: tekst, context, term, bedoelde "
            "betekenis of bronnen zijn gewijzigd"
        )
    if not model:
        return "beoordeling zonder benoemd model (herkomst onbekend) genegeerd"
    return None


def _configuratieafwijzing(
    samenvatting: Mapping[str, Any], binding: Beoordelingsbinding | None
) -> str | None:
    """R1: promptversie, norm en provider/model moeten de actuele binding zijn.

    Zonder bekende actuele binding (geen dienst beschikbaar om haar te
    bepalen) kan geen enkele opgeslagen beoordeling als actueel gelden.
    """
    if binding is None:
        return (
            "actuele beoordelingsbinding onbekend (geen ESS-03-dienst beschikbaar); "
            "een opgeslagen beoordeling kan niet als actueel gelden"
        )
    if samenvatting.get("prompt_version") != binding.prompt_version:
        return (
            f"beoordeling hoort bij promptversie {samenvatting.get('prompt_version')!r}; "
            f"actueel is {binding.prompt_version!r}"
        )
    if samenvatting.get("norm_sha256") != binding.norm_sha256:
        return "beoordeling hoort bij een eerdere versie van de ESS-03-norm"
    if (samenvatting.get("provider") or None) != (binding.provider or None):
        return (
            f"beoordeling komt van provider {samenvatting.get('provider')!r}; "
            f"actueel is {binding.provider!r}"
        )
    if samenvatting.get("model") != binding.model:
        return (
            f"beoordeling komt van model {samenvatting.get('model')!r}; "
            f"actueel is {binding.model!r}"
        )
    return None


def _materiaalafwijzing(
    assessment: Mapping[str, Any], materiaal: Mapping[str, str]
) -> str | None:
    """R1/R7: het werkelijk verzonden materiaal moet exact het actuele zijn.

    Per vindplaats dezelfde hash, dezelfde vindplaatsen — niet meer, niet
    minder. Een beoordeling zonder materiaalbinding is niet reconstrueerbaar
    en daarom niet actueel.
    """
    invoer = assessment.get("input")
    gebonden = invoer.get("materiaal") if isinstance(invoer, Mapping) else None
    if not isinstance(gebonden, Mapping):
        return "beoordeling zonder materiaalbinding (input.materiaal) is niet actueel"
    actueel = materiaalhashes(materiaal)
    if set(gebonden) != set(actueel):
        return (
            "materiaal gewijzigd: de beoordeling zag andere vindplaatsen "
            f"({', '.join(sorted(set(gebonden) ^ set(actueel)))})"
        )
    afwijkend = sorted(loc for loc, h in actueel.items() if gebonden.get(loc) != h)
    if afwijkend:
        return "materiaal gewijzigd sinds de beoordeling: " + ", ".join(afwijkend)
    return None


def _lege_samenvatting() -> dict[str, Any]:
    return {
        "applied": False,
        "historical": False,
        "status": None,
        "reason": None,
        "model": None,
        "provider": None,
        "prompt_version": None,
        "norm_sha256": None,
        "expected_binding": None,
        "verdict": None,
        "question": None,
        "unit": None,
        "rejected": 0,
    }


def valideer_beoordeling(
    assessment: Any,
    fingerprint: str,
    materiaal: Mapping[str, str],
    *,
    binding: Beoordelingsbinding | None = None,
) -> tuple[GevalideerdOordeel | None, dict[str, Any]]:
    """Valideer een (opgeslagen of zojuist verkregen) beoordeling tegen de invoer.

    Geeft (gevalideerd oordeel of None, samenvatting). Een beoordeling telt
    alleen bij gelijke contractversie én vingerafdruk, status `assessed`, een
    benoemd model, de actuele beoordelingsbinding (promptversie, norm,
    provider/model — R1) en exact het actuele materiaal (hash per
    vindplaats); het oordeel zelf wordt opnieuw tegen het actuele materiaal
    gelegd (citaatbestaan). Een geldig uitgevoerde beoordeling die niet meer
    actueel is, is `historical`: het verdict blijft in de samenvatting
    zichtbaar, maar wordt niet toegepast. Wat niet telt wordt benoemd — nooit
    stil genegeerd.
    """
    samenvatting = _lege_samenvatting()
    samenvatting["expected_binding"] = binding.als_dict() if binding else None
    if not isinstance(assessment, Mapping):
        samenvatting["reason"] = (
            "AI-beoordeling niet uitgevoerd (geen beoordeling aangeleverd)"
            if assessment is None
            else "beoordeling is geen object"
        )
        return None, samenvatting
    _vul_samenvatting(samenvatting, assessment)

    reden, historisch = _actualiteitsafwijzing(
        assessment, samenvatting, fingerprint, materiaal, binding
    )
    if reden is not None:
        samenvatting["reason"] = reden
        samenvatting["historical"] = historisch
        return None, samenvatting

    kaal_oordeel, reden = _kaal_opgeslagen_oordeel(assessment.get("judgment"))
    if reden is not None:
        samenvatting["reason"] = reden
        return None, samenvatting
    oordeel, rejected = valideer_oordeel(kaal_oordeel, materiaal)
    if oordeel is None:
        samenvatting["reason"] = "beoordeling zonder bruikbaar oordeel: " + str(
            rejected[0]["detail"] if rejected else "onbekend"
        )
        samenvatting["rejected"] += len(rejected)
        return None, samenvatting
    samenvatting.update(
        {
            "applied": True,
            "verdict": oordeel.verdict,
            "question": oordeel.question,
            "unit": oordeel.unit,
        }
    )
    return oordeel, samenvatting


def _vul_samenvatting(
    samenvatting: dict[str, Any], assessment: Mapping[str, Any]
) -> None:
    """Herkomst en (historisch) verdict uit het document — ook als het niet telt."""
    status = assessment.get("status")
    samenvatting["status"] = status if isinstance(status, str) else None
    for sleutel in ("prompt_version", "norm_sha256"):
        waarde = assessment.get(sleutel)
        samenvatting[sleutel] = waarde if isinstance(waarde, str) else None
    attributie = assessment.get("attribution")
    if isinstance(attributie, Mapping):
        samenvatting["model"] = _tekst(attributie.get("model")) or None
        samenvatting["provider"] = _tekst(attributie.get("provider")) or None
    rejected_bestaand = assessment.get("rejected")
    samenvatting["rejected"] = (
        len(rejected_bestaand) if isinstance(rejected_bestaand, list) else 0
    )
    oordeel_ruw = assessment.get("judgment")
    if isinstance(oordeel_ruw, Mapping) and oordeel_ruw.get("verdict") in VERDICTS:
        samenvatting["verdict"] = oordeel_ruw.get("verdict")


def _actualiteitsafwijzing(
    assessment: Mapping[str, Any],
    samenvatting: Mapping[str, Any],
    fingerprint: str,
    materiaal: Mapping[str, str],
    binding: Beoordelingsbinding | None,
) -> tuple[str | None, bool]:
    """(reden, historisch): status → contract/vingerafdruk/model → binding → materiaal.

    Een uitgevoerde beoordeling van een eerdere kandidaatstand, een eerdere
    prompt/norm/modelroute of ander materiaal is historisch (zichtbaar, niet
    actueel); zonder bekende actuele binding is zij niet actueel maar ook
    niet als historisch te kwalificeren.
    """
    reden = _statusafwijzing(assessment, samenvatting.get("status"))
    if reden is not None:
        return reden, False
    reden = _bindingsafwijzing(assessment, fingerprint, samenvatting.get("model"))
    if reden is not None:
        return reden, True
    reden = _configuratieafwijzing(samenvatting, binding) or _materiaalafwijzing(
        assessment, materiaal
    )
    if reden is not None:
        return reden, binding is not None
    return None, False


def _kaal_opgeslagen_oordeel(oordeel_ruw: Any) -> tuple[Any, str | None]:
    """Het opgeslagen oordeel zonder de afgeleide `status`, die apart wordt
    gecontroleerd tegen het verdict en buiten de gesloten antwoordcontrole
    blijft. (oordeel, reden) — reden gezet bij een strijdige status."""
    if not isinstance(oordeel_ruw, Mapping) or "status" not in oordeel_ruw:
        return oordeel_ruw, None
    verdict = oordeel_ruw.get("verdict")
    if verdict in VERDICTS and oordeel_ruw["status"] != status_voor_verdict(verdict):
        return None, (
            f"opgeslagen status {oordeel_ruw['status']!r} strookt niet met het "
            f"verdict {verdict!r}"
        )
    return {k: v for k, v in oordeel_ruw.items() if k != "status"}, None


# --- samenstelling -------------------------------------------------------------------


@dataclass(frozen=True)
class Ess03Uitkomst:
    """De samengestelde ESS-03-uitkomst: status, vingerafdruk, één onderdeel, review."""

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


def _bewijstekst(bewijs: Iterable[Mapping[str, str]]) -> str:
    return "; ".join(f"{item['location']}: “{item['quote']}”" for item in bewijs)


def _ai_reden(oordeel: GevalideerdOordeel, model: str) -> str:
    """De leesbare reden: oordeel, eenheid, ontbrekend, vraag, onzekerheid, bewijs."""
    delen = [f"AI-beoordeling van telbaarheid ({model}): {oordeel.reason}"]
    if oordeel.unit:
        delen.append(f"Bedoelde eenheid: {oordeel.unit}.")
    if oordeel.status == STATUS_NOT_APPLICABLE:
        delen.append("ESS-03 verlangt hier geen afzonderlijke identificatie.")
    for label, waarde in (
        ("Ontbrekende informatie", oordeel.missing_information),
        ("Vraag", oordeel.question),
        ("Onzekerheid", oordeel.uncertainty),
    ):
        if waarde:
            delen.append(f"{label}: {waarde}")
    bewijs = _bewijstekst(oordeel.evidence)
    if bewijs:
        delen.append(f"Bewijs: {bewijs}.")
    return " ".join(delen)


_ACTIE_PER_STATUS = {
    STATUS_PASS: _ACTIE_PASS,
    STATUS_FAIL: _ACTIE_FAIL,
    STATUS_NOT_APPLICABLE: _ACTIE_NA,
}


def _ai_deel(
    oordeel: GevalideerdOordeel, samenvatting: Mapping[str, Any]
) -> Deeluitkomst:
    model = samenvatting.get("model") or "onbekend model"
    actie = _ACTIE_PER_STATUS.get(oordeel.status)
    if actie is None:
        actie = (
            _ACTIE_VRAAG
            if oordeel.verdict == VERDICT_INSUFFICIENT
            else _ACTIE_ONBEWEZEN
        )
    return Deeluitkomst(
        id=ONDERDEEL_TELBAARHEID,
        status=oordeel.status,
        evidence=oordeel.evidence[0]["quote"] if oordeel.evidence else None,
        field=BASIS_ASSESSMENT,
        reason=_ai_reden(oordeel, model),
        action=actie,
    )


def _open_deel(samenvatting: Mapping[str, Any]) -> Deeluitkomst:
    reden = samenvatting.get("reason") or "AI-beoordeling niet uitgevoerd"
    if samenvatting.get("historical"):
        verdict = samenvatting.get("verdict")
        oordeeltekst = f" (eerder oordeel: {verdict})" if verdict else ""
        return Deeluitkomst(
            id=ONDERDEEL_TELBAARHEID,
            status=STATUS_OPEN,
            field=BASIS_ASSESSMENT,
            reason=(
                f"De eerdere AI-beoordeling{oordeeltekst} is historisch en geldt niet "
                f"als actueel oordeel: {reden}."
            ),
            action=_ACTIE_HISTORISCH,
        )
    return Deeluitkomst(
        id=ONDERDEEL_TELBAARHEID,
        status=STATUS_OPEN,
        field=BASIS_ASSESSMENT if samenvatting.get("status") else None,
        reason=f"De telbaarheid is niet beoordeeld: {reden}.",
        action=_ACTIE_NIET_BEOORDEELD,
    )


def _foutdeel(samenvatting: Mapping[str, Any]) -> Deeluitkomst:
    reden = samenvatting.get("reason") or "technische fout"
    return Deeluitkomst(
        id=ONDERDEEL_TELBAARHEID,
        status=STATUS_ERROR,
        field=BASIS_ASSESSMENT,
        reason=(
            "De ESS-03-controle kon niet worden uitgevoerd; er is geen inhoudelijk "
            f"oordeel gegeven ({reden})."
        ),
        action=_ACTIE_FOUT,
    )


def beoordeel_telbaarheid(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen_ruw: Any,
    *,
    intentie: Intentie | None = None,
    assessment: Any = None,
    binding: Beoordelingsbinding | None = None,
) -> Ess03Uitkomst:
    """De ESS-03-beoordeling van één kandidaattekst (replay).

    Zuiver en synchroon: consumeert een eerder verkregen, gestructureerde
    beoordeling (`assessment`) en bindt haar aan de vingerafdruk van exact
    deze invoer, het actuele materiaal en de actuele beoordelingsbinding
    (`binding`: promptversie, norm, provider/model — zonder binding is niets
    actueel). Voert zelf geen AI-aanroep uit. Zonder toepasbare beoordeling
    is de regel open (`review_required`) met de reden; een technische fout is
    `error`; nooit een cijfer.
    """
    bronnen = canoniseer_bronnen(bronnen_ruw)
    fingerprint = bereken_ess03_vingerafdruk(
        begrip, tekst, contexten, bronnen, intentie=intentie
    )
    materiaal = beoordelingsmateriaal(begrip, tekst, contexten, bronnen, intentie)
    try:
        oordeel, samenvatting = valideer_beoordeling(
            assessment, fingerprint, materiaal, binding=binding
        )
    except Exception as exc:  # pragma: no cover - defensief: replay mag nooit crashen
        logger.warning(
            "ESS-03: validatie van de beoordeling mislukte: %s: %s",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        oordeel, samenvatting = (
            None,
            {**_lege_samenvatting(), "reason": "beoordeling onleesbaar"},
        )

    if samenvatting.get("status") == "error":
        deel = _foutdeel(samenvatting)
    elif oordeel is None:
        deel = _open_deel(samenvatting)
    else:
        deel = _ai_deel(oordeel, samenvatting)
    return Ess03Uitkomst(
        status=deel.status,
        fingerprint=fingerprint,
        parts=(deel,),
        review={"assessment": dict(samenvatting)},
    )
