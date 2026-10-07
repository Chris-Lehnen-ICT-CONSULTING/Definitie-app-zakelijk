"""INT-02 — beoordelingscontract def835-int02-assessment/4 (norm def771-int02/2).

Zuiver domein (DEF-835 WP1, plan-v1 §Ontwerpvoorstel): geen AI-client,
database of Streamlit.

/4 (besluit 16, `bronfuncties-ontwerp-v1.md`): de beoordelaar levert per
passage een `kernvorm` (de zinsvorm van de passage zelf) en per grondbron
(bevestigde bedoeling, elk contextitem, elke bronpassage; sleutels uit
`grondbronnen`) precies één `function` met een letterlijk citaat waar
vereist, en als laatste zijn eigen `verdict`. Deze code leidt de functie van
elke passage en de status mechanisch af (`_beoordeel_passage`):

1. kernvorm `instruction` → gebrek (besluit 1, K1);
2. een beschrijvende bron naast een voorschrijvende of `not_a_criterion`-bron
   → review (`conflict`), tenzij de bevestigde bedoeling zelf voorschrijft of
   `not_a_criterion` zegt (keuze 1B: alleen naar gebrek);
3. eensluidend beschrijvend → beschrijvend; voorschrijvend of
   `not_a_criterion` alleen met een tweede signaal (kernvorm
   `obligation_form`/`discretion_form`, voorschrift en `not_a_criterion`
   samen, of de bedoeling) → gebrek, anders review (3A, 6A); alleen
   `unclear` → review;
4. alle grondbronnen zwijgen → de kernvorm; `descriptive_act` zonder bedoeling
   → review (5A); `discretion_form` zonder bedoeling → de dienstregel van
   besluit 12.

Over passages gaat gebrek vóór review vóór beschrijvend (SC-C-03); `pass`
vraagt volledige dekking en geen beslissende onzekerheid van de beoordelaar
(besluit 17: anders review, `model_beslissend_onzeker`, vaste vraag; een
afgeleid gebrek blijft fail). Voor een model (actor `ai`) beslist de dienst (2A):
wijkt de status af van het eigen modelverdict, dan staat de beslissende regel
in `Beoordelingsdocument.omzetting` en blijft het modelverdict in het oordeel.
Bij een afgeleide review is de vraag vast (4A). Een menselijke beoordelaar
houdt zijn eigen verdict, dat met de afgeleide passages moet samenhangen.

Wat deze code mechanisch controleert:

- **invoer**: exacte, onveranderlijke snapshot van begrip, kern, bevestigde
  bedoeling (`None` = expliciet onbekend), de drie contextlijsten en de
  aangeleverde bronpassages;
- **binding**: contract-, normversie en -hash, promptversie,
  routeringshash, gevraagde provider/model en hashes van begrip, kern,
  bedoeling, context en bronnen;
- **uitvoer**: een gesloten structuur (onbekende velden, verkeerde typen en
  bool-als-int worden geweigerd). Dezelfde vorm staat als vastgepind
  JSON-schema in `ANTWOORDSCHEMA` (besluit 14, optie A: schema via de API);
  dat schema vervangt geen enkele controle hieronder;
- **grondbronnen**: per passage komt elke sleutel uit `grondbronnen` precies
  één keer voor; een onbekende sleutel (ook `bedoeling` bij een onbekende
  bedoeling) is `invalid_citation` / `grond_niet_herleidbaar`, een
  ontbrekende of dubbele `invalid_output`. Alleen een betekenisdragende
  grondbron (minstens één zichtbare letter) draagt een functie; een bron als
  "..." of alleen witruimte mag alleen zwijgen (anders
  `grond_niet_herleidbaar`), en zo'n bedoeling geldt in stap 4 als onbekend.
  Een citaat is verplicht bij een
  beschrijvende, voorschrijvende of `not_a_criterion`-functie, mag bij
  `unclear` en moet null zijn bij `not_addressed` (anders `invalid_output`);
  een passage- of grondcitaat zonder zichtbare letter is `leeg`;
- **posities**: door deze code afgeleid, nooit door de beoordelaar geleverd
  (/2, besluit 9 optie A). Een citaat moet precies één keer als exacte
  substring (Python-codepunten, geen normalisatie) in de kern of in de tekst
  van de genoemde grondbron staan: `start` is die vindplaats, `end` = `start`
  + `len(quote)`, einde exclusief. Nul of meer vindplaatsen (ook overlappend)
  of een leeg citaat is `invalid_citation` met een `foutdetail`. Uitvoer die
  zelf `start`/`end` meelevert, heeft onbekende velden (`invalid_output`);
- **status**: de mapping uit synthese v5 §4 (pass, fail, review_required,
  not_evaluated, error, not_applicable), zonder cijfer, met exacte meldingen.

Het bewaarde oordeel is de geaccepteerde modeluitvoer mét de afgeleide
posities, plus onder `dienst` de afleiding: de beslissende regel
(`afleiding`), de status van het eigen modelverdict (`modelstatus`) en per
passage de afgeleide functie en grond in de vorm van /3 (`passages`). Een
bewaard /1-, /2- of /3-document wordt bij replay nog volgens de regels van
zijn eigen versie op integriteit getoetst en is daarna historisch (niet
`error`); de dienstregel discretie zonder bedoeling van /3 (besluit 12) blijft
daarvoor bestaan. Ongeldige uitvoer wordt nooit gerepareerd en geeft `error`,
nooit fail of review_required. De code bewijst geen semantische juistheid of
volledigheid van de beoordeling. Opslag valt buiten dit contract (DEF-626).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any, cast

__all__ = [
    "ANTWOORDSCHEMA",
    "ANTWOORDSCHEMA_SHA256",
    "BRONFUNCTIES",
    "CONTRACTVERSIE",
    "KERNVORMEN",
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
    "grondbronnen",
    "maak_invoer",
    "ontbrekende_invoer",
    "toets_actualiteit",
]

#: /1: posities door de beoordelaar. /2: posities door deze code afgeleid
#: (besluit 9, optie A). /3: plus de dienstregel discretie zonder bedoeling
#: (besluit 12, optie A). /4: kernvorm en bronfuncties; de dienst leidt de
#: status af (besluit 16). Documenten onder /1–/3 zijn daardoor historisch.
_CONTRACTVERSIE_V4 = "def835-int02-assessment/4"
CONTRACTVERSIE = _CONTRACTVERSIE_V4
#: Vorige versies. Een bewaard /1-, /2- of /3-document wordt volgens de
#: regels van zijn eigen versie op integriteit getoetst (`_herleidbaar`) en is
#: daarna historisch, geen error. De regels hangen aan de vaste versienaam,
#: niet aan `CONTRACTVERSIE`: die bepaalt alleen welke versie actueel is.
_CONTRACTVERSIE_V1 = "def835-int02-assessment/1"
_CONTRACTVERSIE_V2 = "def835-int02-assessment/2"
_CONTRACTVERSIE_V3 = "def835-int02-assessment/3"
#: Versies waarvan een bewaard document herleidbaar kan zijn; andere → error.
_BEKENDE_CONTRACTVERSIES = frozenset(
    {_CONTRACTVERSIE_V1, _CONTRACTVERSIE_V2, _CONTRACTVERSIE_V3, _CONTRACTVERSIE_V4}
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
#: /4: de zinsvorm van een passage zelf (ontwerp §2.1).
KERNVORMEN = frozenset(
    {"instruction", "obligation_form", "discretion_form", "descriptive_act", "no_act"}
)
#: /4: de functie die een grondbron geeft aan de inhoud van een passage. Naast
#: de functies van /3: `not_a_criterion` (de inhoud bepaalt níét wat tot het
#: begrip behoort; keuze 6A) en `not_addressed` (de grondbron zwijgt).
NIET_KENMERK = "not_a_criterion"
ZWIJGT = "not_addressed"
BRONFUNCTIES = FUNCTIES | {NIET_KENMERK, ZWIJGT}
#: Richting van een bronfunctie in de beslisregel; `not_addressed` telt nergens.
_RICHTING = {
    **dict.fromkeys(BESCHRIJVEND, "B"),
    **dict.fromkeys(GEBREK, "G"),
    NIET_KENMERK: "N",
    "unclear": "O",
}
#: Bij deze functies is het citaat verplicht; bij `unclear` optioneel.
_CITAAT_VERPLICHT = BESCHRIJVEND | GEBREK | {NIET_KENMERK}
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

# --- /4: afleidingsregels, vaste vragen en redenen (besluit 16) ---------------
#: De beslissende regel van een passage (`dienst.afleiding`, en bij een
#: afwijking van het modelverdict ook `Beoordelingsdocument.omzetting`).
REGEL_VOORSCHRIFT_IN_KERN = "voorschrift_in_kern"
REGEL_BEDOELING_BESLIST = "bedoeling_beslist"
REGEL_CONFLICT = "conflict"
REGEL_BRONNEN_BESCHRIJVEND = "bronnen_beschrijvend"
REGEL_VOORSCHRIFT_BEVESTIGD = "voorschrift_bevestigd"
REGEL_BRONVOORSCHRIFT_NIET_OVERGENOMEN = "bronvoorschrift_niet_overgenomen"
REGEL_BRONNEN_OPEN = "bronnen_open"
REGEL_ALLEEN_KERN = "alleen_kern"
REGEL_GEEN_GROND_ZONDER_BEDOELING = "geen_grond_zonder_bedoeling"
REGEL_DISCRETIE_ZONDER_BEDOELING = OMZETTING_DISCRETIE_ZONDER_BEDOELING
#: Over passages heen: geen gebrek of review, maar onvolledige dekking.
REGEL_ONVOLLEDIGE_DEKKING = "onvolledige_dekking"
#: Het eigen verdict `not_applicable` blijft staan (geen passages).
REGEL_NIET_VAN_TOEPASSING = "niet_van_toepassing"
#: Een menselijke `insufficient_information` zonder afgeleide reviewpassage.
REGEL_OORDEEL_MENS = "oordeel_mens"
#: Besluit 17: het model meldt beslissende onzekerheid; geen afgeleide pass.
REGEL_MODEL_BESLISSEND_ONZEKER = "model_beslissend_onzeker"
#: Keuze 4A: vaste, invoeronafhankelijke vraag bij een afgeleide review.
VRAAG_FUNCTIE = (
    "Bepaalt deze passage wat tot het begrip behoort, of schrijft zij een actor "
    "een handeling of afweging voor?"
)
VRAAG_DEKKING = (
    "Welke nog niet beoordeelde passage van de kern bepaalt mede wat tot het "
    "begrip behoort?"
)
_VRAAG_BIJ_REGEL = {
    REGEL_CONFLICT: VRAAG_FUNCTIE,
    REGEL_BRONVOORSCHRIFT_NIET_OVERGENOMEN: VRAAG_FUNCTIE,
    REGEL_BRONNEN_OPEN: VRAAG_FUNCTIE,
    REGEL_GEEN_GROND_ZONDER_BEDOELING: VRAAG_FUNCTIE,
    REGEL_DISCRETIE_ZONDER_BEDOELING: VRAAG_DISCRETIE_ZONDER_BEDOELING,
    REGEL_ONVOLLEDIGE_DEKKING: VRAAG_DEKKING,
    REGEL_MODEL_BESLISSEND_ONZEKER: VRAAG_FUNCTIE,
}
#: Keuze 4A: de betekenisgrond in de O-melding noemt bronnen en citaten.
#: `{voor}`, `{tegen}` en `{open}` zijn grondweergaven ("bronpassage B1 ('…')").
REDEN_CONFLICT = (
    "Strijdige betekenisgrond voor '{passage}': {voor} gebruikt de inhoud als "
    "kenmerk van het begrip; {tegen} {rol}; {slot}"
)
REDEN_BRONVOORSCHRIFT_NIET_OVERGENOMEN = (
    "Alleen {tegen} {rol} bij '{passage}'; de kern neemt dat niet in "
    "voorschrijvende vorm over en geen tweede grond bevestigt het"
)
REDEN_BRONNEN_OPEN = (
    "{open} laat open welke functie '{passage}' heeft; geen andere grond beslist dat"
)
REDEN_GEEN_GROND_ZONDER_BEDOELING = (
    "De bevestigde bedoeling is onbekend en geen aangeleverde grond zegt iets "
    "over de functie van '{passage}'"
)
REDEN_ONVOLLEDIGE_DEKKING = (
    "Niet alle relevante passages van de kern zijn beoordeeld (dekking: {dekking})"
)
#: Besluit 17: `{grond}` is de grondweergave van de dragende kenmerkpassage.
REDEN_MODEL_BESLISSEND_ONZEKER = (
    "Volgens {grond} is '{passage}' een kenmerk van het begrip, maar de "
    "beoordelaar meldt beslissende onzekerheid; dat volstaat niet voor een "
    "goedkeuring"
)
_ROL = {
    "G": "stelt de inhoud als plicht of afweging van een actor",
    "N": "toont dat de inhoud geen kenmerk van het begrip is",
}
_SLOT_CONFLICT = "de bevestigde bedoeling beslist dat niet"
_SLOT_CONFLICT_BEDOELING = (
    "een beschrijvende bedoeling beslecht dat niet (alleen naar een gebrek)"
)
#: SC-C-03: een gebrek blijft VN; een open reviewpassage wordt erbij vermeld.
MELDING_OPEN_PUNT = "Daarnaast onvoldoende informatie: {reden}. Vraag: {één vraag}"
#: Status bij het eigen modelverdict (2A: alleen voor de zichtbare omzetting).
_MODELSTATUS = {
    "pass": "pass",
    "fail": "fail",
    "insufficient_information": "review_required",
    "not_applicable": "not_applicable",
}

_UITVOERVELDEN = frozenset(
    {"verdict", "passages", "reason", "question", "uncertainty"}
    | {"scope_reason", "coverage"}
)
_PASSAGEVELDEN = frozenset({"quote", "function", "ground"})
_GRONDVELDEN = frozenset({"field", "ref", "quote"})
#: /4: passage met kernvorm en bronfuncties; bronfunctie met sleutel en citaat.
_PASSAGEVELDEN_V4 = frozenset({"quote", "kernvorm", "bronfuncties"})
_BRONFUNCTIEVELDEN = frozenset({"bron", "function", "quote"})
#: Het blok met de afleiding van de dienst in het bewaarde /4-oordeel.
_DIENSTVELD = "dienst"
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

#: Besluit 14 (optie A) en 16: het antwoordschema voor native JSON-schema-
#: uitvoer (Anthropic `output_config.format`). Exact de gesloten uitvoervorm
#: die `_controleer_structuur_v4` toetst: dezelfde velden, enums en
#: nullability, elk object gesloten, elk veld verplicht (0 optionele velden,
#: 3 unies). De eigenschapsvolgorde hoort bij de schema-identiteit: eerst de
#: passages met kernvorm en bronfuncties, dan de onderbouwing en als laatste
#: het eigen `verdict`, zodat het model zich per bron vastlegt vóór zijn
#: eindoordeel. Enums zijn gesorteerd: de iteratievolgorde van een frozenset
#: hangt af van PYTHONHASHSEED. Wat het schema niet kan uitdrukken (bestaan,
#: volledigheid en uniciteit van grondbronsleutels, citaatplicht per functie,
#: letterlijkheid en uniciteit van citaten, samenhang) blijft in de code.
_NUL_OF_TEKST: dict[str, Any] = {"anyOf": [{"type": "string"}, {"type": "null"}]}
_BRONFUNCTIESCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "bron": {"type": "string"},
        "function": {"type": "string", "enum": sorted(BRONFUNCTIES)},
        "quote": _NUL_OF_TEKST,
    },
    "required": ["bron", "function", "quote"],
    "additionalProperties": False,
}
ANTWOORDSCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "passages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "kernvorm": {"type": "string", "enum": sorted(KERNVORMEN)},
                    "bronfuncties": {"type": "array", "items": _BRONFUNCTIESCHEMA},
                },
                "required": ["quote", "kernvorm", "bronfuncties"],
                "additionalProperties": False,
            },
        },
        "reason": {"type": "string"},
        "question": _NUL_OF_TEKST,
        "uncertainty": {"type": "string", "enum": sorted(ONZEKERHEDEN)},
        "coverage": {"type": "string", "enum": sorted(DEKKINGEN)},
        "scope_reason": _NUL_OF_TEKST,
        "verdict": {"type": "string", "enum": sorted(VERDICTS)},
    },
    "required": [
        "passages",
        "reason",
        "question",
        "uncertainty",
        "coverage",
        "scope_reason",
        "verdict",
    ],
    "additionalProperties": False,
}
#: Gepinde, eigenschapsvolgorde-gevoelige SHA-256 van `ANTWOORDSCHEMA`
#: (`services.ai.base_client.response_schema_sha256`: compacte JSON zonder
#: sort_keys, de functie waarmee de AI-laag het verzonden schema bevestigt).
#: Hoort bij promptversie def835-int02-prompt/5; een ander schema vraagt een
#: nieuwe promptversie. Vorige pin (/3, prompt /4): `72adfe74…511f17`.
ANTWOORDSCHEMA_SHA256 = (
    "d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715"
)

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


#: Letters (Unicode-categorie Lo) die als leeg renderen en dus geen betekenis
#: tonen (herreview Codex 2, P1-rest):
#: - de Hangul-fillers U+115F (choseong), U+1160 (jungseong), U+3164 (filler)
#:   en U+FFA0 (halfwidth filler);
#: - de Egyptische hiërogliefen U+13441 (FULL BLANK) en U+13442 (HALF BLANK).
#: Dit zijn alle letters met FILLER of BLANK in hun Unicode-naam; een test borgt
#: dat. Codepunten, geen letterlijke tekens: die zijn in de bron onzichtbaar.
ONZICHTBARE_LETTERS = frozenset(
    map(chr, (0x115F, 0x1160, 0x3164, 0xFFA0, 0x13441, 0x13442))
)


def _zichtbare_letter(teken: str) -> bool:
    return (
        unicodedata.category(teken).startswith("L") and teken not in ONZICHTBARE_LETTERS
    )


def _betekenisdragend(waarde: Any) -> bool:
    """Bevat de tekst minstens één zichtbare letter?

    Letter = Unicode-categorie L* (Lu, Ll, Lt, Lm, Lo), dus ook "é", "α", "ж"
    of "日", maar niet de onzichtbare `ONZICHTBARE_LETTERS`. Alleen cijfers,
    leestekens of witruimte ("7", "...", "—") dragen onder /4 geen oordeel
    (herreview Codex, P1-rest en herreview 2). Alleen de /4-route gebruikt
    dit; de invoerconstructors en /1–/3 houden `_gevuld`.
    """
    return isinstance(waarde, str) and any(map(_zichtbare_letter, waarde))


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


def _grondbronmap(invoer: Int02Invoer) -> dict[str, tuple[str, Any, str]]:
    """{sleutel: (veld, ref, tekst)} van de grondbronnen, in vaste volgorde.

    De bevestigde bedoeling (alleen als die bekend is), elk contextitem en
    elke bronpassage. Begrip en kern zijn geen grondbron (ontwerp §2.1).
    """
    bronnen: dict[str, tuple[str, Any, str]] = {}
    if invoer.bedoeling is not None:
        bronnen["bedoeling"] = ("bedoeling", None, invoer.bedoeling)
    for veld in _CONTEXTVELDEN:
        for index, tekst in enumerate(getattr(invoer, veld)):
            bronnen[f"{veld}/{index}"] = (veld, index, tekst)
    for bron in invoer.bronnen:
        bronnen[f"bron/{bron.id}"] = ("bron", bron.id, bron.tekst)
    return bronnen


def grondbronnen(invoer: Int02Invoer) -> tuple[str, ...]:
    """De grondbronsleutels van deze invoer in vaste volgorde (contract /4).

    `bedoeling`, `organisatorische_context/<index>`, `juridische_context/<index>`,
    `wettelijke_basis/<index>` en `bron/<id>`; de dataprompt geeft ze mee.
    """
    _eis(isinstance(invoer, Int02Invoer), "invoer moet een Int02Invoer zijn")
    return tuple(_grondbronmap(invoer))


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


# --- /4: bronfuncties en beslisregel (besluit 16) ----------------------------------


def _controleer_structuur_v4(uitvoer: Any) -> None:
    """Gesloten vorm van /4: exacte velden, typen en enums; geen semantiek."""
    _object(uitvoer, _UITVOERVELDEN)
    _vorm(_in(uitvoer["verdict"], VERDICTS))
    _vorm(_gevuld(uitvoer["reason"]))
    _vorm(uitvoer["question"] is None or isinstance(uitvoer["question"], str))
    _vorm(uitvoer["scope_reason"] is None or isinstance(uitvoer["scope_reason"], str))
    _vorm(_in(uitvoer["uncertainty"], ONZEKERHEDEN))
    _vorm(_in(uitvoer["coverage"], DEKKINGEN))
    _vorm(isinstance(uitvoer["passages"], list))
    for passage in uitvoer["passages"]:
        _object(passage, _PASSAGEVELDEN_V4)
        _vorm(isinstance(passage["quote"], str))
        _vorm(_in(passage["kernvorm"], KERNVORMEN))
        _vorm(isinstance(passage["bronfuncties"], list))
        for bronfunctie in passage["bronfuncties"]:
            _object(bronfunctie, _BRONFUNCTIEVELDEN)
            _vorm(isinstance(bronfunctie["bron"], str))
            _vorm(_in(bronfunctie["function"], BRONFUNCTIES))
            _vorm(bronfunctie["quote"] is None or isinstance(bronfunctie["quote"], str))


def _met_posities_v4(uitvoer: dict[str, Any], invoer: Int02Invoer) -> dict[str, Any]:
    """Nieuwe kopie met afgeleide posities; grondbronnen volledig en herleidbaar.

    Per passage: het citaat is betekenisdragend (anders `leeg`) en staat
    precies één keer in de kern; elke grondbronsleutel bestaat (anders
    `grond_niet_herleidbaar`) en komt precies één keer voor (anders
    `invalid_output`); alleen een betekenisdragende grondbron draagt een
    functie (anders `grond_niet_herleidbaar`); de citaatplicht volgt de
    functie; elk citaat is betekenisdragend (anders `leeg`) en staat precies
    één keer in de tekst van zijn grondbron. Betekenisdragend: minstens één
    zichtbare letter (`_betekenisdragend`, herreview Codex P1-rest en 2).
    """
    bronnen = _grondbronmap(invoer)
    passages = []
    for passage in uitvoer["passages"]:
        _citaat(_betekenisdragend(passage["quote"]), CITAAT_LEEG)
        start, end = _positie(invoer.kern, passage["quote"])
        bronfuncties = []
        for bronfunctie in passage["bronfuncties"]:
            sleutel, functie, citaat = (
                bronfunctie["bron"],
                bronfunctie["function"],
                bronfunctie["quote"],
            )
            _citaat(sleutel in bronnen, GROND_NIET_HERLEIDBAAR)
            # Codex-review P1 en P1-rest: een bron zonder zichtbare letter kan
            # zwijgen, maar geen functie dragen.
            if functie != ZWIJGT:
                _citaat(_betekenisdragend(bronnen[sleutel][2]), GROND_NIET_HERLEIDBAAR)
            if functie in _CITAAT_VERPLICHT:
                _vorm(citaat is not None)
            elif functie == ZWIJGT:
                _vorm(citaat is None)
            positie = (None, None)
            if citaat is not None:
                # Een citaat zonder zichtbare letter toont geen functie.
                _citaat(_betekenisdragend(citaat), CITAAT_LEEG)
                positie = _positie(bronnen[sleutel][2], citaat)
            bronfuncties.append(
                {**bronfunctie, **dict(zip(_POSITIEVELDEN, positie, strict=True))}
            )
        sleutels = [b["bron"] for b in bronfuncties]
        _vorm(len(sleutels) == len(set(sleutels)) and set(sleutels) == set(bronnen))
        passages.append(
            {**passage, "start": start, "end": end, "bronfuncties": bronfuncties}
        )
    return {**uitvoer, "passages": passages}


def _controleer_samenhang_v4(uitvoer: dict[str, Any]) -> None:
    """Het eigen modelverdict hangt intern samen (vraag, onzekerheid, dekking).

    Zoals /3, zonder de voorwaarden op passagefuncties: die levert het model
    onder /4 niet meer; de dienst leidt ze af.
    """
    verdict = uitvoer["verdict"]
    vraag, scope = uitvoer["question"], uitvoer["scope_reason"]
    if verdict != "not_applicable":
        _vorm(scope is None and bool(uitvoer["passages"]))
    if verdict == "pass":
        _vorm(uitvoer["coverage"] == "complete")
        _vorm(uitvoer["uncertainty"] != "decisive" and vraag is None)
    elif verdict == "fail":
        _vorm(vraag is None or _een_vraag(vraag))
    elif verdict == "insufficient_information":
        _vorm(_een_vraag(vraag) and uitvoer["uncertainty"] == "decisive")
    else:
        _vorm(_gevuld(scope) and not uitvoer["passages"] and vraag is None)
        _vorm(uitvoer["coverage"] == "none" and uitvoer["uncertainty"] == "none")


@dataclass(frozen=True)
class _Afgeleid:
    """De door de dienst afgeleide uitkomst van één passage.

    `uitkomst` is gebrek, beschrijvend of review; `functie` de functie in de
    vorm van /3; `grond` de dragende grondbronsleutel (None = de kern);
    `tegen` bij een conflict de bron aan de andere kant.
    """

    uitkomst: str
    regel: str
    functie: str
    grond: str | None
    tegen: str | None = None


def _beoordeel_passage(passage: dict[str, Any], invoer: Int02Invoer) -> _Afgeleid:
    """De mechanische beslisregel van ontwerp §2.3 met de keuzes van besluit 16."""
    kernvorm = passage["kernvorm"]
    functie = {bf["bron"]: bf["function"] for bf in passage["bronfuncties"]}
    # Vaste volgorde van de grondbronnen, niet de volgorde van het model.
    stem = [(k, _RICHTING.get(functie[k])) for k in grondbronnen(invoer)]
    b, g, n, o = ([k for k, r in stem if r == x] for x in ("B", "G", "N", "O"))
    bedoeling = dict(stem).get("bedoeling")
    discretie = kernvorm == "discretion_form" or (
        bool(g) and functie[g[0]] == "discretionary_decision_rule"
    )
    gebrek = "discretionary_decision_rule" if discretie else "actor_prescription"

    # Stap 1 — een zelfstandig voorschrift in de kern blijft fail (besluit 1, K1).
    if kernvorm == "instruction":
        grond = g[0] if g else None
        return _Afgeleid(
            "gebrek", REGEL_VOORSCHRIFT_IN_KERN, "actor_prescription", grond
        )
    # Stap 2 — strijdige betekenisgrond; de bedoeling beslecht alleen naar gebrek (1B).
    if b and (g or n):
        if bedoeling in ("G", "N"):
            return _Afgeleid("gebrek", REGEL_BEDOELING_BESLIST, gebrek, "bedoeling")
        return _Afgeleid("review", REGEL_CONFLICT, "unclear", b[0], (g + n)[0])
    # Stap 3 — één richting; een voorschrift-bron vraagt een tweede signaal (3A, 6A).
    if b:
        return _Afgeleid(
            "beschrijvend", REGEL_BRONNEN_BESCHRIJVEND, functie[b[0]], b[0]
        )
    if g or n:
        tweede_signaal = (
            kernvorm in ("obligation_form", "discretion_form")
            or (bool(g) and bool(n))
            or bedoeling in ("G", "N")
        )
        if tweede_signaal:
            return _Afgeleid("gebrek", REGEL_VOORSCHRIFT_BEVESTIGD, gebrek, (g + n)[0])
        return _Afgeleid(
            "review", REGEL_BRONVOORSCHRIFT_NIET_OVERGENOMEN, "unclear", (g + n)[0]
        )
    if o:
        return _Afgeleid("review", REGEL_BRONNEN_OPEN, "unclear", o[0])
    # Stap 4 — alle grondbronnen zwijgen: alleen de kernvorm. Een bedoeling
    # zonder zichtbare letter geldt als onbekend (herreview Codex, P1-rest).
    onbekend = not _betekenisdragend(invoer.bedoeling)
    if kernvorm == "no_act" or (kernvorm == "descriptive_act" and not onbekend):
        return _Afgeleid("beschrijvend", REGEL_ALLEEN_KERN, "criterion", None)
    if kernvorm == "descriptive_act":  # keuze 5A
        return _Afgeleid("review", REGEL_GEEN_GROND_ZONDER_BEDOELING, "unclear", None)
    if kernvorm == "discretion_form" and onbekend:  # besluit 12
        return _Afgeleid("review", REGEL_DISCRETIE_ZONDER_BEDOELING, "unclear", None)
    return _Afgeleid("gebrek", REGEL_VOORSCHRIFT_IN_KERN, gebrek, None)


def _grond_v3(
    sleutel: str | None, passage: dict[str, Any], invoer: Int02Invoer
) -> dict[str, Any]:
    """De grond in de vorm van /3 (met posities) voor een grondbronsleutel."""
    if sleutel is None:
        return {"field": "kern", "ref": None, "quote": None, "start": None, "end": None}
    veld, ref, _ = _grondbronmap(invoer)[sleutel]
    (bf,) = [b for b in passage["bronfuncties"] if b["bron"] == sleutel]
    return {
        "field": veld,
        "ref": ref,
        "quote": bf["quote"],
        "start": bf["start"],
        "end": bf["end"],
    }


def _reden_v4(
    afgeleid: _Afgeleid, passage: dict[str, Any], dienst: dict[str, Any]
) -> str:
    """De betekenisgrond van een reviewpassage, met bronnen en citaten (4A)."""
    functie = {bf["bron"]: bf["function"] for bf in passage["bronfuncties"]}
    waarden = {"{passage}": passage["quote"]}
    if afgeleid.regel == REGEL_DISCRETIE_ZONDER_BEDOELING:
        return _vul(REDEN_DISCRETIE_ZONDER_BEDOELING, {"{citaat}": passage["quote"]})
    if afgeleid.regel == REGEL_GEEN_GROND_ZONDER_BEDOELING:
        return _vul(REDEN_GEEN_GROND_ZONDER_BEDOELING, waarden)
    if afgeleid.regel == REGEL_BRONNEN_OPEN:
        waarden["{open}"] = _grondtekst(dienst["ground"])
        return _vul(REDEN_BRONNEN_OPEN, waarden)
    tegen = afgeleid.tegen or afgeleid.grond
    tegengrond = dienst["tegen"] if afgeleid.tegen else dienst["ground"]
    waarden["{tegen}"] = _grondtekst(tegengrond)
    waarden["{rol}"] = _ROL[_RICHTING[functie[cast(str, tegen)]]]
    if afgeleid.regel == REGEL_BRONVOORSCHRIFT_NIET_OVERGENOMEN:
        return _vul(REDEN_BRONVOORSCHRIFT_NIET_OVERGENOMEN, waarden)
    waarden["{voor}"] = _grondtekst(dienst["ground"])
    beschrijvende_bedoeling = _RICHTING.get(functie.get("bedoeling", ZWIJGT)) == "B"
    waarden["{slot}"] = (
        _SLOT_CONFLICT_BEDOELING if beschrijvende_bedoeling else _SLOT_CONFLICT
    )
    return _vul(REDEN_CONFLICT, waarden)


@dataclass(frozen=True)
class _Uitkomst:
    """Status, melding en afleiding van een geldig /4-oordeel."""

    status: str
    reden: str | None
    melding: str
    vraag: str | None
    afleiding: str
    dienstpassages: list[dict[str, Any]]


def _vn_melding(p: dict[str, Any]) -> str:
    discretie = p["function"] == "discretionary_decision_rule"
    melding = _vul(
        MELDING_VN,
        {
            "{passage}": p["quote"],
            "{handeling/afweging}": "een afweging" if discretie else "een handeling",
            "{grond}": _grondtekst(p["ground"]),
        },
    )
    if discretie:
        melding += " " + _vul(MELDING_VN_DISCRETIE, {"{citaat}": p["quote"]})
    return melding


def _o_melding(reden: str, vraag: str) -> str:
    return _vul(
        MELDING_O,
        {
            "{ontbrekende of strijdige betekenisgrond}": _zonder_slotpunt(reden),
            "{één vraag}": vraag,
        },
    )


def _leid_af(
    oordeel: dict[str, Any], invoer: Int02Invoer, uitvoering: Uitvoering
) -> _Uitkomst:
    """Status uit de afgeleide passages: gebrek vóór review vóór beschrijvend.

    Een afgeleide pass vraagt bovendien dat de beoordelaar geen beslissende
    onzekerheid meldt; anders review met een vaste vraag (besluit 17). Een
    afgeleid gebrek of een eigen reviewgrond gaat daaraan voor.
    Actor `ai`: de dienst beslist (2A). Actor `human`: het eigen verdict blijft
    de status en moet met de afgeleide passages samenhangen (anders
    `invalid_output`), zoals de samenhangseis van /3.
    """
    verdict = oordeel["verdict"]
    if verdict == "not_applicable":
        status, reden, melding = _status_en_melding(oordeel)
        return _Uitkomst(status, reden, melding, None, REGEL_NIET_VAN_TOEPASSING, [])
    dienst: list[dict[str, Any]] = []
    redenen: list[str | None] = []
    for passage in oordeel["passages"]:
        afgeleid = _beoordeel_passage(passage, invoer)
        p = {
            "quote": passage["quote"],
            "start": passage["start"],
            "end": passage["end"],
            "function": afgeleid.functie,
            "ground": _grond_v3(afgeleid.grond, passage, invoer),
            "uitkomst": afgeleid.uitkomst,
            "regel": afgeleid.regel,
        }
        tegen = {"tegen": _grond_v3(afgeleid.tegen, passage, invoer)}
        reden = None
        if afgeleid.uitkomst == "review":
            reden = _reden_v4(afgeleid, passage, {**p, **tegen})
        dienst.append(p)
        redenen.append(reden)

    def eerste(uitkomst: str) -> int | None:
        indices = [i for i, p in enumerate(dienst) if p["uitkomst"] == uitkomst]
        if not indices:
            return None
        return min(indices, key=lambda i: (dienst[i]["start"], dienst[i]["end"]))

    gebrek, review, beschrijvend = (
        eerste(u) for u in ("gebrek", "review", "beschrijvend")
    )
    open_punt = None
    if review is not None:
        regel = dienst[review]["regel"]
        open_punt = (cast(str, redenen[review]), _VRAAG_BIJ_REGEL[regel], regel)
    elif oordeel["coverage"] != "complete":
        open_punt = (
            _vul(REDEN_ONVOLLEDIGE_DEKKING, {"{dekking}": oordeel["coverage"]}),
            VRAAG_DEKKING,
            REGEL_ONVOLLEDIGE_DEKKING,
        )
    if uitvoering.actor == "human":
        if verdict == "pass":
            _vorm(gebrek is None and review is None)
        elif verdict == "fail":
            _vorm(gebrek is not None)
        else:
            _vorm(gebrek is None)
            regel = (
                dienst[review]["regel"] if review is not None else REGEL_OORDEEL_MENS
            )
            melding = _o_melding(oordeel["reason"], oordeel["question"])
            return _Uitkomst(
                "review_required",
                "insufficient_information",
                melding,
                oordeel["question"],
                regel,
                dienst,
            )
    if gebrek is not None:
        p = dienst[gebrek]
        melding, vraag = _vn_melding(p), None
        if open_punt is not None and review is not None:
            reden, vraag, _ = open_punt
            melding += " " + _vul(
                MELDING_OPEN_PUNT,
                {"{reden}": _zonder_slotpunt(reden), "{één vraag}": vraag},
            )
        return _Uitkomst("fail", None, melding, vraag, p["regel"], dienst)
    if open_punt is not None:
        reden, vraag, regel = open_punt
        return _Uitkomst(
            "review_required",
            "insufficient_information",
            _o_melding(reden, vraag),
            vraag,
            regel,
            dienst,
        )
    p = dienst[cast(int, beschrijvend)]
    if oordeel["uncertainty"] == "decisive":  # besluit 17: geen pass bij twijfel
        reden = _vul(
            REDEN_MODEL_BESLISSEND_ONZEKER,
            {"{grond}": _grondtekst(p["ground"]), "{passage}": p["quote"]},
        )
        return _Uitkomst(
            "review_required",
            "insufficient_information",
            _o_melding(reden, VRAAG_FUNCTIE),
            VRAAG_FUNCTIE,
            REGEL_MODEL_BESLISSEND_ONZEKER,
            dienst,
        )
    melding = _vul(
        MELDING_V,
        {
            "{passage}": p["quote"],
            "{criterium/afleiding/kenmerk}": _FUNCTIELABEL[p["function"]],
            "{grond}": _grondtekst(p["ground"]),
        },
    )
    return _Uitkomst("pass", None, melding, None, p["regel"], dienst)


def _zonder_afleiding_v4(oordeel: Any) -> Any:
    """Een bewaard /4-oordeel terug in modelvorm: zonder `dienst` en posities.

    Alleen voor replay. Een oordeel dat niet de verwachte vorm heeft, blijft
    zoveel mogelijk ongewijzigd; `beoordeel` wijst het dan zelf af.
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
        if isinstance(kaal, dict) and isinstance(kaal.get("bronfuncties"), list):
            kaal["bronfuncties"] = [zonder(bf) for bf in kaal["bronfuncties"]]
        passages.append(kaal)
    model = {k: v for k, v in oordeel.items() if k != _DIENSTVELD}
    return {**model, "passages": passages}


# --- Document en replay ---------------------------------------------------------


@dataclass(frozen=True)
class Beoordelingsdocument:
    """Onveranderlijk document: exacte invoer, binding, uitvoering en oordeel.

    `oordeel_json` is de canonieke JSON van de geaccepteerde uitvoer met de
    door deze code afgeleide posities, of None als er geen geldig oordeel is.
    `foutdetail` onderscheidt bij `invalid_citation` niet gevonden, niet
    uniek, leeg citaat en niet-herleidbare grond; anders is het None.
    `omzetting` is onder /4 de beslissende regel (`dienst.afleiding` in het
    oordeel) als de afgeleide status afwijkt van het eigen modelverdict
    (keuze 2A; ook fail → pass); het oordeel houdt het modelverdict. Onder /3
    is zij `OMZETTING_DISCRETIE_ZONDER_BEDOELING` als de dienstregel een fail
    heeft omgezet. Anders None, ook onder /1 en /2 en voor een mens.
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
    citaten, posities en grondbronnen → samenhang van het modelverdict →
    beslisregel per passage → status (gebrek vóór review vóór pass). Een nieuw
    document valt altijd onder de actuele `CONTRACTVERSIE`.
    """
    return _beoordeel(invoer, configuratie, modeluitvoer, uitvoering, CONTRACTVERSIE)


def _beoordeel(
    invoer: Int02Invoer,
    configuratie: Configuratie,
    modeluitvoer: Any,
    uitvoering: Uitvoering,
    contractversie: str,
) -> Beoordelingsdocument:
    """`beoordeel` volgens de regels van `contractversie` (/4, of /1–/3 voor replay).

    Onder /1 levert de beoordelaar de posities en is het oordeel de uitvoer
    zelf; /1 kende geen `foutdetail`. Onder /2, /3 en /4 leidt deze code de
    posities af. Alleen /3 kent de losse dienstregel discretie zonder
    bedoeling; onder /4 is die de laatste tak van de beslisregel.
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
    if contractversie == _CONTRACTVERSIE_V4:
        try:
            _vorm(uitvoering.status == "completed")
            _controleer_structuur_v4(modeluitvoer)
            oordeel = _met_posities_v4(modeluitvoer, invoer)
            _controleer_samenhang_v4(oordeel)
            uitkomst = _leid_af(oordeel, invoer, uitvoering)
        except _AfwijzingError as afwijzing:
            return document(
                "error",
                MELDING_E,
                fout=afwijzing.categorie,
                foutdetail=afwijzing.detail,
            )
        modelstatus = _MODELSTATUS[oordeel["verdict"]]
        omgezet = uitvoering.actor == "ai" and uitkomst.status != modelstatus
        oordeel[_DIENSTVELD] = {
            "afleiding": uitkomst.afleiding,
            "modelstatus": modelstatus,
            "passages": uitkomst.dienstpassages,
        }
        return document(
            uitkomst.status,
            uitkomst.melding,
            reden=uitkomst.reden,
            uitvoer=oordeel,
            vraag=uitkomst.vraag,
            omzetting=uitkomst.afleiding if omgezet else None,
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
    if contractversie == _CONTRACTVERSIE_V3 and _discretie_zonder_bedoeling(
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
    en opnieuw afgeleid; onder /4 bovendien het blok `dienst`, dat opnieuw
    wordt afgeleid; onder /1 gelden de /1-regels (opgeslagen posities,
    `tekst[start:end] == quote` exact). Onder /3 en /4 hoort de omzetting
    erbij: een ontbrekende, gewijzigde of onterechte `omzetting`, een
    gewijzigd modelverdict of een gewijzigde afleiding maakt het document
    niet-herleidbaar, net als een gewijzigde of ontbrekende positie of quote;
    een onbekende contractversie is nooit herleidbaar. Een herleidbaar /1-,
    /2- of /3-document is daarna via de bindingstoets historisch.
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
    if versie == _CONTRACTVERSIE_V4:
        oordeel = _zonder_afleiding_v4(oordeel)
    elif versie != _CONTRACTVERSIE_V1:
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
