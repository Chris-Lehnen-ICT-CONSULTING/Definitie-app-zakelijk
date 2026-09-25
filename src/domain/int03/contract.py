"""INT-03 — het verwijzingscontract (DEF-772 WP3, besluiten van 25 september 2026).

Pure domeinlogica, zonder Streamlit, database of AI-client. De evaluator
(`services.validation.evaluators.pronoun_reference_assessment`) roept
`beoordeel_verwijzingen` aan en vertaalt de uitkomst naar het runtimecontract;
de beoordelingsdienst (`services.validation.int03_assessment_service`)
gebruikt `structuurfout_modeluitvoer` en `valideer_oordeel` om de
modeluitvoer fail-closed te valideren; een latere persistentie-/UI-laag (WP4)
gebruikt `bereken_int03_vingerafdruk` en `valideer_beoordeling` om een
opgeslagen beoordeling aan exact dezelfde invoer te binden.

Wat de regel toetst (K1(a), ASTRA-getrouw): is voor ieder verwijzend gebruikt
woord in de ongewijzigde definitie — persoonlijk, aanwijzend, betrekkelijk of
bezittelijk voornaamwoord, of voornaamwoordelijk bijwoord — voor de lezer
zonder context eenduidig welk antecedent in de definitie bedoeld is? De term
is ondersteunend; context en toelichting zijn uitsluitend eventuele
betekenisgrond en vervangen geen antecedent in de kern (K6).

Drie modeluitkomsten (`verdict`), elk met onderbouwing en door code
gecontroleerde citaten; de **bevinding** (subtype voor de UI) leidt de code
zelf af uit de per-woord-statussen, zodat het model die niet kan opleggen:

- **pass** — voldoet: elk verwijzend woord heeft een eenduidig antecedent
  (`clear`), óf de definitie bevat geen verwijzend woord (`no_referring_word`;
  K7: pas ná de inhoudelijke controle, met exact de motivering
  `MOTIVERING_GEEN_VERWIJZEND_WOORD`);
- **fail** — voldoet niet: een aantoonbaar onduidelijke verwijzing, met woord,
  passage en werkelijk plausibele kandidaten (`ambiguous`, minstens twee), of
  een woord zonder enig antecedent in de definitie (`no_antecedent`, lege
  kandidatenlijst met motivering). Een herstelvraag mag ernaast staan; de
  fout blijft fail als de herstelbedoeling onbekend is;
- **insufficient_information** — nog te beoordelen: uitsluitend semantische
  twijfel of ontbrekende betekenisgrond (`undetermined`), met precies één
  gerichte vraag.

Rolverdeling: **code** controleert binding (vingerafdruk over term, tekst,
context en toelichting; promptversie, norm, provider/model), de gesloten
structuur, de consistentie tussen verdict en bevinding en het citaatbestaan
(staat elk verwijzend woord als heel woord in de definitie én in zijn
passage, staat elke passage en elk kandidaatscitaat letterlijk in de
definitie?); de **AI** beoordeelt taalfunctie, antecedent en plausibiliteit
van lezingen. Interpretatie (`reading`, `reason`) staat los van de citaten en
wordt niet gecontroleerd — formaatcontrole bewijst geen semantische
juistheid. Een technische fout is apart herkenbaar (`error`) en nooit pass
of fail; dat geldt ook voor een corrupt document (geen object, geen geldige
status) en voor een beoordeling die bij replay structureel ongeldig blijkt of
waarvan een citaat niet in de tekst staat (`invalid` in de samenvatting) —
alleen een ontbrekende (`None`), niet beschikbare of historische beoordeling
blijft open (`review_required`). Meldingen en redenen dragen
nooit tekst uit het modelantwoord: afgewezen citaten en modelwaarden blijven
in `rejected[].detail` van het document, buiten logs en foutmeldingen. Geen
cijfer, geen automatisch herstel, geen eigen poort: een negatieve uitkomst is
zichtbaar met advisory-ernst, zoals ESS-03.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from domain.context.contract import CONTEXT_VELDEN, Deeluitkomst
from domain.context.normalisatie import contextsleutel
from domain.sources.contract import vind_citaat

logger = logging.getLogger(__name__)

__all__ = [
    "ASSESSMENT_STATUSSEN",
    "BASIS_ASSESSMENT",
    "BEVINDINGEN",
    "BEVINDING_DUIDELIJK",
    "BEVINDING_GEEN_ANTECEDENT",
    "BEVINDING_GEEN_VERWIJZEND_WOORD",
    "BEVINDING_MEERDUIDIG",
    "BEVINDING_ONBESLIST",
    "CONTRACTVERSIE",
    "MOTIVERING_GEEN_VERWIJZEND_WOORD",
    "ONDERDEEL_VERWIJZING",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_OPEN",
    "STATUS_PASS",
    "VERDICTS",
    "VERDICT_FAIL",
    "VERDICT_INSUFFICIENT",
    "VERDICT_PASS",
    "VERWIJZINGSSTATUSSEN",
    "VERWIJZING_DUIDELIJK",
    "VERWIJZING_GEEN_ANTECEDENT",
    "VERWIJZING_MEERDUIDIG",
    "VERWIJZING_NIET_VERWIJZEND",
    "VERWIJZING_ONBESLIST",
    "Beoordelingsbinding",
    "GevalideerdOordeel",
    "Int03Uitkomst",
    "Verwijzing",
    "afgeleide_bevinding",
    "beoordeel_verwijzingen",
    "beoordeling_niet_beschikbaar",
    "beoordeling_technische_fout",
    "bereken_int03_vingerafdruk",
    "status_voor_verdict",
    "structuurfout_modeluitvoer",
    "toelichting_uit_context",
    "valideer_beoordeling",
    "valideer_oordeel",
]

#: Beleidsversie van dit contract; onderdeel van de vingerafdruk.
CONTRACTVERSIE = "int03/1"

#: Het ene zichtbare onderdeel van INT-03 in `rule_results`.
ONDERDEEL_VERWIJZING = "pronoun_reference"

#: Waarde van `Deeluitkomst.field`: het oordeel komt van de AI-beoordeling.
BASIS_ASSESSMENT = "int03_assessment"

VERDICT_PASS = "pass"
VERDICT_FAIL = "fail"
VERDICT_INSUFFICIENT = "insufficient_information"
VERDICTS: tuple[str, ...] = (VERDICT_PASS, VERDICT_FAIL, VERDICT_INSUFFICIENT)

#: Status van één verwijzend (of niet-verwijzend gebruikt) woord, door het model.
VERWIJZING_DUIDELIJK = "clear"
VERWIJZING_MEERDUIDIG = "ambiguous"
VERWIJZING_GEEN_ANTECEDENT = "no_antecedent"
VERWIJZING_NIET_VERWIJZEND = "non_referring"
VERWIJZING_ONBESLIST = "undetermined"
VERWIJZINGSSTATUSSEN: tuple[str, ...] = (
    VERWIJZING_DUIDELIJK,
    VERWIJZING_MEERDUIDIG,
    VERWIJZING_GEEN_ANTECEDENT,
    VERWIJZING_NIET_VERWIJZEND,
    VERWIJZING_ONBESLIST,
)

#: Bevinding (subtype voor de UI), door code afgeleid uit de verwijzingen.
BEVINDING_DUIDELIJK = "clear"
BEVINDING_GEEN_VERWIJZEND_WOORD = "no_referring_word"
BEVINDING_MEERDUIDIG = "ambiguous"
BEVINDING_GEEN_ANTECEDENT = "no_antecedent"
BEVINDING_ONBESLIST = "undetermined"
BEVINDINGEN: tuple[str, ...] = (
    BEVINDING_DUIDELIJK,
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    BEVINDING_MEERDUIDIG,
    BEVINDING_GEEN_ANTECEDENT,
    BEVINDING_ONBESLIST,
)

#: Welke bevindingen bij welk verdict horen (consistentie-eis, R2-lijn).
_BEVINDINGEN_BIJ_VERDICT: dict[str, frozenset[str]] = {
    VERDICT_PASS: frozenset({BEVINDING_DUIDELIJK, BEVINDING_GEEN_VERWIJZEND_WOORD}),
    VERDICT_FAIL: frozenset({BEVINDING_MEERDUIDIG, BEVINDING_GEEN_ANTECEDENT}),
    VERDICT_INSUFFICIENT: frozenset({BEVINDING_ONBESLIST}),
}

#: Deelstatussen (spiegelen `toetsregels.runtime_contract.ResultStatus`).
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_OPEN = "review_required"
STATUS_ERROR = "error"

#: Technische status van een verkregen beoordeling.
ASSESSMENT_STATUSSEN: tuple[str, ...] = ("assessed", "error", "unavailable")

#: K7: de exacte motivering bij `pass` zonder verwijzend woord.
MOTIVERING_GEEN_VERWIJZEND_WOORD = (
    "niet van toepassing: de definitie bevat geen verwijzend voornaamwoord"
)

_ACTIE_NIET_BEOORDEELD = (
    "Valideer opnieuw; de INT-03-beoordeling wordt daarbij automatisch uitgevoerd."
)
_ACTIE_FOUT = (
    "Controleer opnieuw. Blijft dit terugkomen, meld het dan als technisch probleem."
)
_ACTIE_PASS = "Geen actie nodig."
_ACTIE_FAIL = (
    "Herhaal het bedoelde zelfstandig naamwoord of herformuleer met behoud van "
    "betekenis, zonder het begrip zelf in te voegen. Toetsen wijzigt de tekst "
    "niet; herstel volgt alleen op verzoek, niet automatisch."
)
_ACTIE_VRAAG = (
    "Beantwoord de vraag (bijvoorbeeld in de toelichting) en toets opnieuw; de "
    "definitie wordt niet automatisch herschreven."
)
_ACTIE_HISTORISCH = (
    "Valideer opnieuw; de eerdere beoordeling blijft als historie bewaard en "
    "geldt niet meer als actueel oordeel."
)

#: De gesloten veldensets van het modelantwoord.
_ANTWOORDVELDEN: frozenset[str] = frozenset(
    {"verdict", "reason", "references", "question", "uncertainty"}
)
_VERWIJZINGSVELDEN: frozenset[str] = frozenset(
    {"word", "passage", "status", "reading", "candidates"}
)
_KANDIDAATVELDEN: frozenset[str] = frozenset({"quote", "reason"})

_WHITESPACE = re.compile(r"\s+")


# --- hulpfuncties ----------------------------------------------------------------------


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _genormaliseerd(tekst: Any) -> str:
    return _WHITESPACE.sub(" ", str(tekst or "")).strip()


def _heel_woord_in(tekst: str, woord: str) -> bool:
    """Staat `woord` als heel woord (niet als deel van een ander woord) in `tekst`?

    Case-insensitief en whitespace-tolerant, verder letterlijk: 'het' in
    'Geheel' is géén voorkomen. Dit is een bestaanstoets, geen interpretatie.
    """
    w = _genormaliseerd(woord)
    if not w:
        return False
    patroon = rf"(?<!\w){re.escape(w)}(?!\w)"
    return re.search(patroon, _genormaliseerd(tekst), re.IGNORECASE) is not None


def toelichting_uit_context(context: Mapping[str, Any] | None) -> str | None:
    """De toelichting uit een validatiecontext (record- of editorpad).

    Leest alleen wat er werkelijk staat: `toelichting` top-level, anders onder
    `definition`. Niets wordt verzonnen.
    """
    context = context or {}
    toelichting = _tekst(context.get("toelichting"))
    if not toelichting:
        definitie = context.get("definition")
        if isinstance(definitie, Mapping):
            toelichting = _tekst(definitie.get("toelichting"))
    return toelichting or None


# --- vingerafdruk en binding --------------------------------------------------------------


def bereken_int03_vingerafdruk(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    toelichting: str | None,
) -> str:
    """Bind een beoordeling aan term, exacte tekst, de drie contextlijsten en
    de toelichting. Wijzigt daar iets, dan geldt een eerdere beoordeling niet."""
    contexten = contexten or {}
    basis = {
        "versie": CONTRACTVERSIE,
        "term": str(begrip or ""),
        "tekst": str(tekst or ""),
        "context": {
            veld: list(contextsleutel(contexten.get(veld))) for veld in CONTEXT_VELDEN
        },
        "toelichting": _tekst(toelichting) or None,
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Beoordelingsbinding:
    """De actuele beoordelingsconfiguratie waaraan een opgeslagen beoordeling
    moet voldoen om als actueel te gelden (ADR-001: expliciete prompt-/norm-/
    modelbinding). De waarden komen zonder netwerk uit de dienst
    (`Int03AssessmentService.binding()`)."""

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
    document["reason"] = str(reden or "INT-03-beoordelingsdienst niet beschikbaar")
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


# --- het gevalideerde oordeel ---------------------------------------------------------


@dataclass(frozen=True)
class Verwijzing:
    """Eén door het model aangewezen woord: citaten (`word`, `passage`,
    `candidates[].quote`) zijn door code gecontroleerd; `reading` en
    `candidates[].reason` zijn interpretatie."""

    word: str
    passage: str
    status: str
    reading: str
    candidates: tuple[dict[str, str], ...]

    def als_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "passage": self.passage,
            "status": self.status,
            "reading": self.reading,
            "candidates": [dict(c) for c in self.candidates],
        }


@dataclass(frozen=True)
class GevalideerdOordeel:
    """Het AI-oordeel na de codecontrole: verdict, afgeleide status en
    bevinding, gecontroleerde verwijzingen, eventuele vraag."""

    verdict: str
    status: str
    finding: str
    reason: str
    references: tuple[Verwijzing, ...]
    question: str | None
    uncertainty: str | None

    def als_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "status": self.status,
            "finding": self.finding,
            "reason": self.reason,
            "references": [r.als_dict() for r in self.references],
            "question": self.question,
            "uncertainty": self.uncertainty,
        }


def status_voor_verdict(verdict: str) -> str:
    """De deelstatus die bij een (onderbouwd) verdict hoort."""
    return {
        VERDICT_PASS: STATUS_PASS,
        VERDICT_FAIL: STATUS_FAIL,
        VERDICT_INSUFFICIENT: STATUS_OPEN,
    }[verdict]


def _status_van(verwijzing: Any) -> str:
    if isinstance(verwijzing, Verwijzing):
        return verwijzing.status
    if isinstance(verwijzing, Mapping):
        return str(verwijzing.get("status") or "")
    return ""


def afgeleide_bevinding(references: Iterable[Any]) -> str:
    """De bevinding (subtype) uit de per-woord-statussen, in deze voorrang:
    meerduidig > geen antecedent > onbeslist > duidelijk > geen verwijzend woord.

    Alleen niet-verwijzend gebruik (lidwoord, loos 'het', voegwoord 'dat') of
    een lege lijst betekent: de definitie bevat geen verwijzend woord (K7).
    """
    statussen = {_status_van(r) for r in references}
    if VERWIJZING_MEERDUIDIG in statussen:
        return BEVINDING_MEERDUIDIG
    if VERWIJZING_GEEN_ANTECEDENT in statussen:
        return BEVINDING_GEEN_ANTECEDENT
    if VERWIJZING_ONBESLIST in statussen:
        return BEVINDING_ONBESLIST
    if VERWIJZING_DUIDELIJK in statussen:
        return BEVINDING_DUIDELIJK
    return BEVINDING_GEEN_VERWIJZEND_WOORD


# --- validatie van de modeluitvoer ---------------------------------------------------


def _is_een_gerichte_vraag(waarde: Any) -> bool:
    """Precies één gerichte vraag: niet-lege tekst die op '?' eindigt en één
    vraagteken bevat."""
    vraag = _tekst(waarde)
    return bool(vraag) and vraag.endswith("?") and vraag.count("?") == 1


def _veldenfout(geparsed: Mapping[str, Any]) -> str | None:
    """Exact de vijf antwoordvelden: niets onbekend, niets ontbrekend.

    Onbekende veldnamen komen uit het modelantwoord en worden niet
    herhaald; ontbrekende namen komen uit het contract zelf.
    """
    onbekend = set(geparsed) - _ANTWOORDVELDEN
    if onbekend:
        return (
            f"onbekend veld in antwoord ({len(onbekend)} veld(en) buiten het contract)"
        )
    ontbrekend = sorted(_ANTWOORDVELDEN - set(geparsed))
    if ontbrekend:
        return f"veld ontbreekt in antwoord: {', '.join(ontbrekend)}"
    return None


def _waardenfout(geparsed: Mapping[str, Any]) -> str | None:
    if geparsed["verdict"] not in VERDICTS:
        return "verdict is onbekend (niet uit de gesloten set)"
    if not isinstance(geparsed["reason"], str) or not _tekst(geparsed["reason"]):
        return "reason ontbreekt of is leeg"
    for veld in ("question", "uncertainty"):
        waarde = geparsed[veld]
        if waarde is not None and not isinstance(waarde, str):
            return f"{veld} moet tekst of null zijn"
    if not isinstance(geparsed["references"], list):
        return "references is geen lijst"
    return None


def _kandidatenfout(index: int, item: Mapping[str, Any]) -> str | None:
    kandidaten = item["candidates"]
    if not isinstance(kandidaten, list):
        return f"references[{index}].candidates is geen lijst"
    for k_index, kandidaat in enumerate(kandidaten):
        if not isinstance(kandidaat, Mapping) or set(kandidaat) != _KANDIDAATVELDEN:
            return (
                f"references[{index}].candidates[{k_index}] heeft niet exact de "
                "velden quote en reason"
            )
        if not all(isinstance(kandidaat[v], str) for v in _KANDIDAATVELDEN):
            return (
                f"references[{index}].candidates[{k_index}]: quote en reason "
                "moeten tekst zijn"
            )
    status = item["status"]
    if status == VERWIJZING_MEERDUIDIG and len(kandidaten) < 2:
        return (
            f"references[{index}]: status '{VERWIJZING_MEERDUIDIG}' vereist minstens "
            "twee kandidaten (werkelijk plausibele lezingen)"
        )
    if (
        status in (VERWIJZING_GEEN_ANTECEDENT, VERWIJZING_NIET_VERWIJZEND)
        and kandidaten
    ):
        return (
            f"references[{index}]: status '{status}' vereist een lege kandidatenlijst"
        )
    return None


def _verwijzingenfout(geparsed: Mapping[str, Any]) -> str | None:
    """Per verwijzing exact vijf velden, tekstvelden niet leeg (reading mag
    leeg), status uit de gesloten set, kandidaten passend bij de status."""
    for index, item in enumerate(geparsed["references"]):
        if not isinstance(item, Mapping):
            return f"references[{index}] is geen object"
        if set(item) != _VERWIJZINGSVELDEN:
            return (
                f"references[{index}] heeft niet exact de velden word, passage, "
                "status, reading en candidates"
            )
        for veld in ("word", "passage", "reading"):
            if not isinstance(item[veld], str):
                return f"references[{index}].{veld} moet tekst zijn"
        if not _tekst(item["word"]) or not _tekst(item["passage"]):
            return f"references[{index}]: word en passage mogen niet leeg zijn"
        if item["status"] not in VERWIJZINGSSTATUSSEN:
            return f"references[{index}].status is onbekend (niet uit de gesloten set)"
        fout = _kandidatenfout(index, item)
        if fout is not None:
            return fout
    return None


def _consistentiefout(geparsed: Mapping[str, Any]) -> str | None:
    """Verdict strookt met de afgeleide bevinding; question precies één
    gerichte vraag bij insufficient_information, optioneel (één) bij fail,
    nooit bij pass."""
    verdict = geparsed["verdict"]
    bevinding = afgeleide_bevinding(geparsed["references"])
    if bevinding not in _BEVINDINGEN_BIJ_VERDICT[verdict]:
        return (
            f"verdict '{verdict}' strookt niet met de uit de verwijzingen afgeleide "
            f"bevinding '{bevinding}'"
        )
    vraag = geparsed["question"]
    if verdict == VERDICT_INSUFFICIENT and not _is_een_gerichte_vraag(vraag):
        return (
            "insufficient_information vereist precies één gerichte vraag "
            "(question: één zin die op '?' eindigt)"
        )
    if verdict == VERDICT_PASS and _tekst(vraag):
        return f"question is niet toegestaan bij '{VERDICT_PASS}'"
    if verdict == VERDICT_FAIL and _tekst(vraag) and not _is_een_gerichte_vraag(vraag):
        return (
            f"question bij '{VERDICT_FAIL}' moet precies één gerichte vraag zijn "
            "(één zin die op '?' eindigt)"
        )
    return None


#: In deze volgorde: elke controle mag op de vorige vertrouwen.
_STRUCTUURCONTROLES = (_veldenfout, _waardenfout, _verwijzingenfout, _consistentiefout)


def structuurfout_modeluitvoer(geparsed: Any) -> str | None:
    """Waarom het JSON-object niet de vereiste antwoordstructuur heeft, of None.

    Gesloten contract: exact de vijf antwoordvelden; `verdict` uit de gesloten
    set; niet-lege `reason`; `references` een lijst van objecten met exact
    `word`, `passage`, `status`, `reading`, `candidates` (elke kandidaat
    exact `quote` en `reason`); kandidaten passend bij de status; verdict
    consistent met de afgeleide bevinding; `question` precies één gerichte
    vraag bij `insufficient_information`, hooguit één bij `fail`, nooit bij
    `pass`. Elke afwijking is een technische fout — geen stil herstel. De
    melding benoemt de soort afwijking en de positie, nooit een waarde of
    veldnaam uit het modelantwoord (die kan gaan naar logs).
    """
    if not isinstance(geparsed, Mapping):
        return "geen object"
    for controle in _STRUCTUURCONTROLES:
        fout = controle(geparsed)
        if fout is not None:
            return fout
    return None


def _verifieer_verwijzingen(
    ruw: list[Mapping[str, Any]], tekst: str, rejected: list[dict[str, Any]]
) -> tuple[Verwijzing, ...]:
    """Alleen verwijzingen waarvan woord, passage en kandidaten letterlijk in
    de definitie staan. Elk afgewezen item landt in `rejected`; de aanroeper
    beslist dat één afgewezen item het hele oordeel onbruikbaar maakt."""
    geverifieerd: list[Verwijzing] = []
    for item in ruw:
        woord, passage = item["word"], item["passage"]
        if not _heel_woord_in(tekst, woord):
            rejected.append(
                {
                    "reason": "verwijzend woord niet in de definitie",
                    "detail": woord[:80],
                }
            )
            continue
        if not vind_citaat(tekst, passage):
            rejected.append(
                {"reason": "passage niet in de definitie", "detail": passage[:120]}
            )
            continue
        if not _heel_woord_in(passage, woord):
            rejected.append(
                {
                    "reason": "verwijzend woord niet in zijn passage",
                    "detail": f"{woord[:80]} / {passage[:120]}",
                }
            )
            continue
        kandidaten: list[dict[str, str]] = []
        afgewezen = False
        for kandidaat in item["candidates"]:
            citaat = kandidaat["quote"]
            if not _tekst(citaat):
                rejected.append({"reason": "leeg kandidaatscitaat", "detail": woord})
                afgewezen = True
                break
            if not vind_citaat(tekst, citaat):
                rejected.append(
                    {
                        "reason": "kandidaatscitaat niet in de definitie",
                        "detail": citaat[:120],
                    }
                )
                afgewezen = True
                break
            kandidaten.append({"quote": citaat, "reason": str(kandidaat["reason"])})
        if afgewezen:
            continue
        geverifieerd.append(
            Verwijzing(
                word=woord,
                passage=passage,
                status=str(item["status"]),
                reading=_tekst(item["reading"]),
                candidates=tuple(kandidaten),
            )
        )
    return tuple(geverifieerd)


def valideer_oordeel(
    ruw: Any, tekst: str
) -> tuple[GevalideerdOordeel | None, list[dict[str, Any]]]:
    """Valideer één modeloordeel tegen de ongewijzigde definitietekst.

    Geeft (gevalideerd oordeel, []) of (None, afgewezen items). Fail-closed:
    een structuurfout of één niet-verifieerbaar citaat (verwijzend woord niet
    als heel woord in de definitie of in zijn passage, passage of kandidaat
    niet letterlijk in de definitie) maakt het hele oordeel onbruikbaar. De
    term, context en toelichting zijn géén bewijsplaats: het antecedent moet
    in de definitie staan (K6(5)).
    """
    structuurfout = structuurfout_modeluitvoer(ruw)
    if structuurfout is not None:
        return None, [{"reason": "structuurfout", "detail": structuurfout}]
    rejected: list[dict[str, Any]] = []
    verwijzingen = _verifieer_verwijzingen(ruw["references"], tekst, rejected)
    if rejected:
        return None, rejected
    verdict = str(ruw["verdict"])
    return (
        GevalideerdOordeel(
            verdict=verdict,
            status=status_voor_verdict(verdict),
            finding=afgeleide_bevinding(verwijzingen),
            reason=_tekst(ruw["reason"]),
            references=verwijzingen,
            question=_tekst(ruw["question"]) or None,
            uncertainty=_tekst(ruw["uncertainty"]) or None,
        ),
        [],
    )


# --- replay van een opgeslagen of zojuist verkregen beoordeling ------------------


def _statusafwijzing(
    assessment: Mapping[str, Any], status: Any
) -> tuple[str | None, bool]:
    """(reden, corrupt): `unavailable`/`error` dragen hun eigen reden; een
    ontbrekende of onbekende status is documentcorruptie (de waarde wordt
    niet herhaald), geen ontbrekende beoordeling."""
    if status == "unavailable":
        return (
            _tekst(assessment.get("reason"))
            or "INT-03-beoordelingsdienst niet beschikbaar"
        ), False
    if status == "error":
        fout = assessment.get("error")
        soort = _tekst(fout.get("type")) if isinstance(fout, Mapping) else ""
        melding = _tekst(fout.get("message")) if isinstance(fout, Mapping) else ""
        return f"technische fout ({soort or 'unknown'}): {melding}".strip(), False
    if status != "assessed":
        return (
            "beoordelingsdocument zonder geldige status (corrupt document)",
            True,
        )
    return None, False


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
            "eerdere beoordeling geldt niet meer: tekst, term, context of "
            "toelichting zijn gewijzigd"
        )
    if not model:
        return "beoordeling zonder benoemd model (herkomst onbekend) genegeerd"
    return None


def _configuratieafwijzing(
    samenvatting: Mapping[str, Any], binding: Beoordelingsbinding | None
) -> str | None:
    """Promptversie, norm en provider/model moeten de actuele binding zijn."""
    if binding is None:
        return (
            "actuele beoordelingsbinding onbekend (geen INT-03-dienst beschikbaar); "
            "een opgeslagen beoordeling kan niet als actueel gelden"
        )
    if samenvatting.get("prompt_version") != binding.prompt_version:
        return (
            f"beoordeling hoort bij promptversie {samenvatting.get('prompt_version')!r}; "
            f"actueel is {binding.prompt_version!r}"
        )
    if samenvatting.get("norm_sha256") != binding.norm_sha256:
        return "beoordeling hoort bij een eerdere versie van de INT-03-norm"
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


def _lege_samenvatting() -> dict[str, Any]:
    return {
        "applied": False,
        "historical": False,
        "invalid": False,
        "status": None,
        "reason": None,
        "model": None,
        "provider": None,
        "prompt_version": None,
        "norm_sha256": None,
        "expected_binding": None,
        "verdict": None,
        "finding": None,
        "question": None,
        "rejected": 0,
    }


def _vul_samenvatting(
    samenvatting: dict[str, Any], assessment: Mapping[str, Any]
) -> None:
    """Herkomst en (historisch) verdict uit het document — ook als het niet telt.
    Alleen een status uit de gesloten set wordt overgenomen (R2: geen
    documentwaarde in de samenvatting)."""
    status = assessment.get("status")
    samenvatting["status"] = status if status in ASSESSMENT_STATUSSEN else None
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
    binding: Beoordelingsbinding | None,
) -> tuple[str | None, bool, bool]:
    """(reden, historisch, corrupt): status → contract/vingerafdruk/model →
    binding."""
    reden, corrupt = _statusafwijzing(assessment, samenvatting.get("status"))
    if reden is not None:
        return reden, False, corrupt
    reden = _bindingsafwijzing(assessment, fingerprint, samenvatting.get("model"))
    if reden is not None:
        return reden, True, False
    reden = _configuratieafwijzing(samenvatting, binding)
    if reden is not None:
        return reden, binding is not None, False
    return None, False, False


def _kaal_opgeslagen_oordeel(oordeel_ruw: Any) -> tuple[Any, str | None]:
    """Het opgeslagen oordeel zonder de afgeleide velden `status` en `finding`,
    die buiten de gesloten antwoordcontrole blijven en opnieuw worden
    afgeleid. (oordeel, reden) — reden gezet bij een strijdige status."""
    if not isinstance(oordeel_ruw, Mapping):
        return oordeel_ruw, None
    verdict = oordeel_ruw.get("verdict")
    if (
        "status" in oordeel_ruw
        and verdict in VERDICTS
        and oordeel_ruw["status"] != status_voor_verdict(verdict)
    ):
        return None, "opgeslagen status strookt niet met het verdict"
    return {
        k: v for k, v in oordeel_ruw.items() if k not in ("status", "finding")
    }, None


def _afwijzingscategorie(rejected: Iterable[Mapping[str, Any]]) -> str:
    """Alleen de soorten afwijzing — vaste teksten van de code, nooit het
    afgewezen citaat zelf (dat blijft in `rejected[].detail`). Bij een
    structuurfout hoort haar (modeltekstvrije) omschrijving erbij."""
    soorten: list[str] = []
    for item in rejected:
        soort = str(item.get("reason") or "onbekend")
        if soort == "structuurfout":
            soort = f"structuurfout: {item.get('detail')}"
        if soort not in soorten:
            soorten.append(soort)
    return "; ".join(soorten) or "onbekend"


def valideer_beoordeling(
    assessment: Any,
    fingerprint: str,
    tekst: str,
    *,
    binding: Beoordelingsbinding | None = None,
) -> tuple[GevalideerdOordeel | None, dict[str, Any]]:
    """Valideer een (opgeslagen of zojuist verkregen) beoordeling tegen de invoer.

    Geeft (gevalideerd oordeel of None, samenvatting). Een beoordeling telt
    alleen bij gelijke contractversie én vingerafdruk, status `assessed`, een
    benoemd model en de actuele beoordelingsbinding (promptversie, norm,
    provider/model); het oordeel zelf wordt opnieuw tegen de actuele tekst
    gelegd (citaatbestaan). Een geldig uitgevoerde beoordeling die niet meer
    actueel is, is `historical`: zichtbaar, niet toegepast. Alleen `None` is
    een ontbrekende beoordeling. Een aangeleverd niet-object, een document
    zonder geldige status, en een actueel gebonden beoordeling waarvan het
    oordeel structureel ongeldig is, met de opgeslagen status strijdig is of
    een citaat draagt dat niet in de tekst staat, zijn `invalid`: een
    technische fout, geen open reviewpunt. Wat niet telt wordt benoemd — met
    de soort afwijzing, nooit met het afgewezen citaat of een documentwaarde
    — nooit stil genegeerd, nooit stil pass.
    """
    samenvatting = _lege_samenvatting()
    samenvatting["expected_binding"] = binding.als_dict() if binding else None
    if assessment is None:
        samenvatting["reason"] = (
            "AI-beoordeling niet uitgevoerd (geen beoordeling aangeleverd)"
        )
        return None, samenvatting
    if not isinstance(assessment, Mapping):
        samenvatting["reason"] = "beoordeling is geen object (corrupt document)"
        samenvatting["invalid"] = True
        return None, samenvatting
    _vul_samenvatting(samenvatting, assessment)

    reden, historisch, corrupt = _actualiteitsafwijzing(
        assessment, samenvatting, fingerprint, binding
    )
    if reden is not None:
        samenvatting["reason"] = reden
        samenvatting["historical"] = historisch
        samenvatting["invalid"] = corrupt
        return None, samenvatting

    kaal_oordeel, reden = _kaal_opgeslagen_oordeel(assessment.get("judgment"))
    if reden is not None:
        samenvatting["reason"] = reden
        samenvatting["invalid"] = True
        return None, samenvatting
    oordeel, rejected = valideer_oordeel(kaal_oordeel, tekst)
    if oordeel is None:
        samenvatting["reason"] = (
            "beoordeling zonder bruikbaar oordeel (technisch ongeldig): "
            + _afwijzingscategorie(rejected)
        )
        samenvatting["rejected"] += len(rejected)
        samenvatting["invalid"] = True
        return None, samenvatting
    samenvatting.update(
        {
            "applied": True,
            "verdict": oordeel.verdict,
            "finding": oordeel.finding,
            "question": oordeel.question,
        }
    )
    return oordeel, samenvatting


# --- samenstelling -------------------------------------------------------------------


@dataclass(frozen=True)
class Int03Uitkomst:
    """De samengestelde INT-03-uitkomst: status, vingerafdruk, één onderdeel,
    samenvatting én het volledige beoordelingsdocument (voor opslag/UI, WP4)."""

    status: str
    fingerprint: str
    parts: tuple[Deeluitkomst, ...]
    review: dict[str, Any]
    assessment: dict[str, Any] | None = None

    def als_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": None,
            "contract_version": CONTRACTVERSIE,
            "fingerprint": self.fingerprint,
            "parts": [p.als_dict() for p in self.parts],
            "review": deepcopy(self.review),
            "assessment": deepcopy(self.assessment),
        }


def _kandidatentekst(verwijzing: Verwijzing) -> str:
    return ", ".join(f"'{c['quote']}' ({c['reason']})" for c in verwijzing.candidates)


def _verwijzingstekst(verwijzing: Verwijzing) -> str:
    """Eén leesbare regel per woord: citaat, status en interpretatie."""
    kop = f"'{verwijzing.word}' in “{verwijzing.passage}”"
    if verwijzing.status == VERWIJZING_NIET_VERWIJZEND:
        return f"{kop}: niet verwijzend gebruikt ({verwijzing.reading})."
    if verwijzing.status == VERWIJZING_GEEN_ANTECEDENT:
        return f"{kop}: geen antecedent in de definitie ({verwijzing.reading})."
    if verwijzing.status == VERWIJZING_MEERDUIDIG:
        return f"{kop}: meer plausibele lezingen — kandidaten {_kandidatentekst(verwijzing)}."
    if verwijzing.status == VERWIJZING_ONBESLIST:
        return f"{kop}: nog te beoordelen ({verwijzing.reading})."
    antecedent = verwijzing.reading or _kandidatentekst(verwijzing)
    return f"{kop} → {antecedent}."


def _ai_reden(oordeel: GevalideerdOordeel, model: str) -> str:
    """De leesbare reden: oordeel, per woord de bevinding, vraag, onzekerheid."""
    if oordeel.finding == BEVINDING_GEEN_VERWIJZEND_WOORD:
        return MOTIVERING_GEEN_VERWIJZEND_WOORD
    kop = (
        f"Nog te beoordelen ({model})"
        if oordeel.status == STATUS_OPEN
        else f"AI-beoordeling van verwijzingen ({model})"
    )
    delen = [f"{kop}: {oordeel.reason}"]
    delen.extend(_verwijzingstekst(r) for r in oordeel.references)
    if oordeel.question:
        delen.append(f"Vraag: {oordeel.question}")
    if oordeel.uncertainty:
        delen.append(f"Onzekerheid: {oordeel.uncertainty}")
    return " ".join(delen)


def _bewijs(oordeel: GevalideerdOordeel) -> str | None:
    for verwijzing in oordeel.references:
        if verwijzing.status != VERWIJZING_NIET_VERWIJZEND:
            return verwijzing.passage
    return None


def _ai_deel(
    oordeel: GevalideerdOordeel, samenvatting: Mapping[str, Any]
) -> Deeluitkomst:
    model = samenvatting.get("model") or "onbekend model"
    if oordeel.status == STATUS_PASS:
        actie = _ACTIE_PASS
    elif oordeel.status == STATUS_FAIL:
        actie = _ACTIE_FAIL
    else:
        actie = _ACTIE_VRAAG
    return Deeluitkomst(
        id=ONDERDEEL_VERWIJZING,
        status=oordeel.status,
        evidence=_bewijs(oordeel),
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
            id=ONDERDEEL_VERWIJZING,
            status=STATUS_OPEN,
            field=BASIS_ASSESSMENT,
            reason=(
                f"De eerdere AI-beoordeling{oordeeltekst} is historisch en geldt niet "
                f"als actueel oordeel: {reden}."
            ),
            action=_ACTIE_HISTORISCH,
        )
    return Deeluitkomst(
        id=ONDERDEEL_VERWIJZING,
        status=STATUS_OPEN,
        field=BASIS_ASSESSMENT if samenvatting.get("status") else None,
        reason=f"De verwijzingen zijn niet beoordeeld: {reden}.",
        action=_ACTIE_NIET_BEOORDEELD,
    )


def _foutdeel(samenvatting: Mapping[str, Any]) -> Deeluitkomst:
    reden = samenvatting.get("reason") or "technische fout"
    if samenvatting.get("invalid"):
        tekst = (
            "De INT-03-beoordeling is technisch ongeldig en levert geen inhoudelijk "
            f"oordeel ({reden})."
        )
    else:
        tekst = (
            "De INT-03-controle kon niet worden uitgevoerd; er is geen inhoudelijk "
            f"oordeel gegeven ({reden})."
        )
    return Deeluitkomst(
        id=ONDERDEEL_VERWIJZING,
        status=STATUS_ERROR,
        field=BASIS_ASSESSMENT,
        reason=tekst,
        action=_ACTIE_FOUT,
    )


def beoordeel_verwijzingen(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    toelichting: str | None,
    *,
    assessment: Any = None,
    binding: Beoordelingsbinding | None = None,
) -> Int03Uitkomst:
    """De INT-03-beoordeling van één definitietekst (replay).

    Zuiver en synchroon: consumeert een eerder verkregen, gestructureerde
    beoordeling (`assessment`) en bindt haar aan de vingerafdruk van exact
    deze invoer en de actuele beoordelingsbinding (`binding`; zonder binding
    is niets actueel). Voert zelf geen AI-aanroep uit. Zonder toepasbare
    beoordeling (ontbrekend, niet beschikbaar, historisch) is de regel open
    (`review_required`) met de reden — nooit pass; een technische fout, een
    corrupt document en een structureel ongeldige of niet-verifieerbare
    beoordeling zijn `error`; nooit een cijfer.
    """
    fingerprint = bereken_int03_vingerafdruk(begrip, tekst, contexten, toelichting)
    try:
        oordeel, samenvatting = valideer_beoordeling(
            assessment, fingerprint, tekst, binding=binding
        )
    except Exception as exc:  # pragma: no cover - defensief: replay mag nooit crashen
        # Alleen het uitzonderingstype: de tekst kan documentinhoud dragen.
        logger.warning(
            "INT-03: validatie van de beoordeling mislukte: %s", type(exc).__name__
        )
        # Onleesbaar = corrupt: een technische fout, geen open reviewpunt.
        oordeel, samenvatting = (
            None,
            {
                **_lege_samenvatting(),
                "reason": "beoordeling onleesbaar (corrupt document)",
                "invalid": True,
            },
        )

    if samenvatting.get("status") == "error" or samenvatting.get("invalid"):
        deel = _foutdeel(samenvatting)
    elif oordeel is None:
        deel = _open_deel(samenvatting)
    else:
        deel = _ai_deel(oordeel, samenvatting)
    return Int03Uitkomst(
        status=deel.status,
        fingerprint=fingerprint,
        parts=(deel,),
        review={"assessment": dict(samenvatting)},
        assessment=dict(assessment) if isinstance(assessment, Mapping) else None,
    )
