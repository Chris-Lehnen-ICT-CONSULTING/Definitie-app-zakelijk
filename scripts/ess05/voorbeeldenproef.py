"""DEF-768 (ESS-05) voorbeeldenproef: grensgevallen blind laten bedenken en toetsen.

Meet of een "voorbeeldenaanpak" voor ESS-05 ("voldoende onderscheidend") op de
10 definities van de goldset hetzelfde oordeel geeft als Chris. Per definitie
precies twee modelaanroepen:

- A (blind): het model ziet de definitietekst NIET en noemt verwante begrippen
  met gevallen die wel onder het verwante begrip vallen en niet onder het
  doelbegrip.
- B (toets): het model krijgt alleen nr en geval-tekst uit A en beoordeelt per
  geval letterlijk of het onder de definitie valt.

De uitkomst wordt deterministisch in code bepaald. Geen reparatie van
modeluitvoer, geen herhaalpoging. Het script rapporteert cijfers en trekt zelf
geen conclusie.

Volledig los van de app: alleen standaardbibliotheek plus ``anthropic`` (en dat
pakket alleen in ``--echt``).

Gebruik::

    python scripts/ess05/voorbeeldenproef.py --droog --uitmap PAD
    python scripts/ess05/voorbeeldenproef.py --echt --run 1 [--env-file PAD]
    python scripts/ess05/voorbeeldenproef.py --vergelijk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[2]
UITVOERBASIS = REPO / "logs" / "def768" / "voorbeeldenproef-v1"
GOLDSET_PAD = UITVOERBASIS / "goldset-v1.json"
STANDAARD_ENV = Path("/Users/chrislehnen/Projecten/Definitie-app/.env")

MODEL = "claude-opus-5"
#: Vast, zodat een ANTHROPIC_BASE_URL in de omgeving de sleutel niet omleidt.
API_BASIS_URL = "https://api.anthropic.com"
MAX_TOKENS = 2000
MAX_RETRIES = 0
TEMPERATUUR = "niet gezet (API-standaard gebruikt)"

#: claude-opus-5: USD 5 / 25 per miljoen tokens = 5000 / 25000 n$ per token
#: (zelfde tarieven als scripts/ess05/praktijktest_p1.py op de DEF-768-branch).
TARIEF_INVOER_NUSD = 5_000
TARIEF_UITVOER_NUSD = 25_000
PLAFOND_NUSD = 2_000_000_000  # USD 2,00 per run
STAPMARGE_NUSD = 150_000_000  # USD 0,15 ruimte voor de volgende aanroep
MAX_AANROEPEN = 25

VOLDOET = "voldoet"
VOLDOET_NIET = "voldoet niet"
TWIJFEL = "twijfel"
NIET_GEDRAAID = "niet gedraaid"
OORDEELWAARDEN = ("ja", "nee", "onzeker")

CRITERIA = (
    "succes: ≥ 8/10 gelijk aan goldset, 0 onterecht voldoet; "
    "stabiliteit (vergelijk): ≥ 8/10 gelijk tussen run 1 en run 2"
)

SYSTEEM_A = (
    "Je bent een materiedeskundige voor begrippenkaders van de Nederlandse "
    "overheid en de strafrechtketen. Je antwoordt uitsluitend met geldige JSON."
)
SYSTEEM_B = (
    "Je beoordeelt of gevallen onder een definitie vallen. Je leest de definitie "
    "letterlijk. Je antwoordt uitsluitend met geldige JSON."
)

SJABLOON_A = """Begrip: {begrip}
Context: organisatorisch: {organisatorische_context}; juridisch: {juridische_context}
Neem in elk geval dit verwante begrip op: {verwant_volgens_bron}

Opdracht:
1. Noem 2 tot 5 verwante begrippen die in deze context met '{begrip}' verward kunnen worden of deels dezelfde gevallen dekken. Geen bovenbegrip, geen onderbegrip, geen synoniem.
2. Geef per verwant begrip 1 of 2 concrete, korte gevallen (één zin) die volgens de gangbare betekenis wél onder het verwante begrip vallen en níet onder '{begrip}'. Geen gevallen die onder beide vallen.
3. Gebruik je algemene kennis en domeinkennis. Geef bij elk geval in één zin waarom het niet onder '{begrip}' valt, in termen van de gangbare betekenis.

Antwoord uitsluitend met JSON, zonder tekst eromheen:
{"verwante_begrippen":[{"begrip":"...","reden_verwant":"...","gevallen":[{"geval":"...","waarom_niet_doelbegrip":"..."}]}]}"""

SJABLOON_B = """Begrip: {begrip}
Definitie: "{definitie_schoon}"
Context: organisatorisch: {organisatorische_context}; juridisch: {juridische_context}

Beoordeel per geval uitsluitend aan de hand van de tekst van de definitie of het geval eronder valt. Lees de definitie letterlijk en vul niets aan.
- "nee": de definitie sluit het geval uit. Citeer letterlijk (exact, aaneengesloten) het deel van de definitie dat het uitsluit.
- "ja": het geval voldoet aan alle elementen van de definitie.
- "onzeker": de tekst laat beide lezingen toe.

Gevallen:
{gevallen}

Antwoord uitsluitend met JSON, zonder tekst eromheen. Geef "citaat" alleen bij "nee"; "toelichting" is optioneel:
{"oordelen":[{"nr":1,"valt_onder":"ja|nee|onzeker","citaat":"...","toelichting":"..."}]}"""

_PLAATSHOUDER = re.compile(r"\{([a-z_]+)\}")


class ProefError(Exception):
    """Weigering of onherstelbare fout; de proef draait (verder) niet."""


class AanroepError(Exception):
    """Een modelaanroep is mislukt (zonder sleutel in de melding)."""


# --- deterministische bouwstenen ---------------------------------------------


def sha256_tekst(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def sha256_bestand(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


def maak_schoon(definitie_db: str) -> str:
    """Stap 0: verwijder metaregels, bronmarkers en toelichting uit de DB-tekst."""
    tekst = definitie_db
    positie = tekst.find("Toelichting:")
    if positie >= 0:
        tekst = tekst[:positie]
    regels = tekst.splitlines()
    if regels and regels[0].strip().casefold() == "soort":
        regels = regels[1:]
    behouden = []
    for regel in regels:
        kaal = regel.strip()
        if kaal.startswith("- Ontologische categorie:"):
            continue
        if re.fullmatch(r"\*\*.+\*\*", kaal):
            continue
        behouden.append(regel)
    tekst = "\n".join(behouden)
    tekst = re.sub(r"\[Bron\s*\d+\]", "", tekst)
    return re.sub(r"\s+", " ", tekst).strip()


def _normaliseer(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst).strip().casefold()


def citaat_staat_in(citaat: str | None, definitie_schoon: str) -> bool:
    """Letterlijk aanwezig, hoofdletterongevoelig en ongevoelig voor witruimte."""
    genormaliseerd = _normaliseer(citaat or "")
    return bool(genormaliseerd) and genormaliseerd in _normaliseer(definitie_schoon)


def _contexttekst(item: dict[str, Any], sleutel: str) -> str:
    waarden = item.get(sleutel) or []
    return ", ".join(waarden) if waarden else "onbekend"


def _vul_in(sjabloon: str, waarden: dict[str, str]) -> str:
    return _PLAATSHOUDER.sub(lambda m: waarden[m.group(1)], sjabloon)


def bouw_prompt_a(item: dict[str, Any]) -> str:
    verwant = item.get("verwant_volgens_bron") or []
    sjabloon = SJABLOON_A
    if not verwant:
        sjabloon = "\n".join(
            regel
            for regel in sjabloon.split("\n")
            if "{verwant_volgens_bron}" not in regel
        )
    return _vul_in(
        sjabloon,
        {
            "begrip": item["begrip"],
            "organisatorische_context": _contexttekst(item, "organisatorische_context"),
            "juridische_context": _contexttekst(item, "juridische_context"),
            "verwant_volgens_bron": ", ".join(verwant),
        },
    )


def bouw_prompt_b(
    item: dict[str, Any], definitie_schoon: str, gevallen: list[dict[str, Any]]
) -> str:
    """Alleen nr en geval-tekst: geen verwant begrip, geen waarom-tekst."""
    lijst = [{"nr": g["nr"], "geval": g["geval"]} for g in gevallen]
    return _vul_in(
        SJABLOON_B,
        {
            "begrip": item["begrip"],
            "definitie_schoon": definitie_schoon,
            "organisatorische_context": _contexttekst(item, "organisatorische_context"),
            "juridische_context": _contexttekst(item, "juridische_context"),
            "gevallen": json.dumps(lijst, ensure_ascii=False),
        },
    )


def _is_tekst(waarde: Any, *, leeg_mag: bool = True) -> bool:
    return isinstance(waarde, str) and (leeg_mag or bool(waarde.strip()))


def parse_a(tekst: str) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Gevallen doorlopend genummerd vanaf 1, of een foutreden."""
    try:
        data = json.loads(tekst)
    except json.JSONDecodeError as fout:
        return None, f"A is geen geldige JSON ({fout.msg})"
    if not isinstance(data, dict) or not isinstance(
        data.get("verwante_begrippen"), list
    ):
        return None, "A mist de lijst 'verwante_begrippen'"
    aantal_verwant = len(data["verwante_begrippen"])
    if not 2 <= aantal_verwant <= 5:
        return None, f"A levert {aantal_verwant} verwante begrippen, vereist 2 tot 5"
    gevallen: list[dict[str, Any]] = []
    for i, verwant in enumerate(data["verwante_begrippen"], start=1):
        if not isinstance(verwant, dict):
            return None, f"A: verwant begrip {i} is geen object"
        if not _is_tekst(verwant.get("begrip"), leeg_mag=False):
            return None, f"A: verwant begrip {i} mist 'begrip'"
        if not _is_tekst(verwant.get("reden_verwant")):
            return None, f"A: verwant begrip {i} mist 'reden_verwant'"
        if not isinstance(verwant.get("gevallen"), list):
            return None, f"A: verwant begrip {i} mist de lijst 'gevallen'"
        if not 1 <= len(verwant["gevallen"]) <= 2:
            return None, (
                f"A: verwant begrip {i} heeft {len(verwant['gevallen'])} gevallen, "
                "vereist 1 of 2"
            )
        for geval in verwant["gevallen"]:
            if not isinstance(geval, dict) or not _is_tekst(
                geval.get("geval"), leeg_mag=False
            ):
                return None, f"A: verwant begrip {i} heeft een geval zonder 'geval'"
            if not _is_tekst(geval.get("waarom_niet_doelbegrip")):
                return None, (
                    f"A: verwant begrip {i} heeft een geval zonder "
                    "'waarom_niet_doelbegrip'"
                )
            gevallen.append(
                {
                    "nr": len(gevallen) + 1,
                    "geval": geval["geval"],
                    "verwant_begrip": verwant["begrip"],
                    "waarom_niet_doelbegrip": geval["waarom_niet_doelbegrip"],
                }
            )
    # Minimaal 2 gevallen volgt uit 2-5 begrippen met elk 1-2 gevallen.
    return gevallen, None


def parse_b(tekst: str, aantal: int) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Oordelen gesorteerd op nr; elk nr 1..aantal precies één keer."""
    try:
        data = json.loads(tekst)
    except json.JSONDecodeError as fout:
        return None, f"B is geen geldige JSON ({fout.msg})"
    if not isinstance(data, dict) or not isinstance(data.get("oordelen"), list):
        return None, "B mist de lijst 'oordelen'"
    oordelen: dict[int, dict[str, Any]] = {}
    for i, oordeel in enumerate(data["oordelen"], start=1):
        if not isinstance(oordeel, dict):
            return None, f"B: oordeel {i} is geen object"
        nr = oordeel.get("nr")
        if not isinstance(nr, int) or isinstance(nr, bool):
            return None, f"B: oordeel {i} heeft geen geheel getal als 'nr'"
        if not 1 <= nr <= aantal:
            return None, f"B: onbekend nr {nr}"
        if nr in oordelen:
            return None, f"B: nr {nr} komt dubbel voor"
        if oordeel.get("valt_onder") not in OORDEELWAARDEN:
            return None, (
                f"B: nr {nr} heeft onbekende waarde "
                f"{oordeel.get('valt_onder')!r} voor 'valt_onder'"
            )
        # citaat alleen verplicht (niet-leeg) bij "nee"; toelichting optioneel.
        if oordeel["valt_onder"] == "nee" and not _is_tekst(
            oordeel.get("citaat"), leeg_mag=False
        ):
            return None, f"B: nr {nr} is 'nee' zonder niet-leeg 'citaat'"
        for veld in ("citaat", "toelichting"):
            if not (oordeel.get(veld) is None or isinstance(oordeel[veld], str)):
                return None, f"B: nr {nr} heeft '{veld}' dat geen tekst is"
        oordelen[nr] = {
            "nr": nr,
            "valt_onder": oordeel["valt_onder"],
            "citaat": oordeel.get("citaat"),
            "toelichting": oordeel.get("toelichting"),
        }
    ontbrekend = [nr for nr in range(1, aantal + 1) if nr not in oordelen]
    if ontbrekend:
        return None, f"B mist nr {', '.join(map(str, ontbrekend))}"
    return [oordelen[nr] for nr in sorted(oordelen)], None


@dataclass(frozen=True)
class Uitkomst:
    uitkomst: str
    reden: str
    onbruikbaar: bool = False
    gevallen_ja: tuple[int, ...] = ()
    gevallen_onzeker: tuple[int, ...] = ()
    citaat_ongeldig: tuple[int, ...] = ()


def bepaal_uitkomst(
    fout: str | None, oordelen: list[dict[str, Any]] | None, definitie_schoon: str
) -> Uitkomst:
    """De vier regels, in volgorde."""
    if fout is not None or oordelen is None:
        return Uitkomst(TWIJFEL, f"uitvoer onbruikbaar: {fout}", onbruikbaar=True)
    ja = tuple(o["nr"] for o in oordelen if o["valt_onder"] == "ja")
    if ja:
        return Uitkomst(
            VOLDOET_NIET,
            "geval(len) vallen volgens B onder de definitie: nr "
            + ", ".join(map(str, ja)),
            gevallen_ja=ja,
        )
    onzeker = tuple(o["nr"] for o in oordelen if o["valt_onder"] == "onzeker")
    ongeldig = tuple(
        o["nr"]
        for o in oordelen
        if o["valt_onder"] == "nee"
        and not citaat_staat_in(o["citaat"], definitie_schoon)
    )
    if onzeker or ongeldig:
        delen = []
        if onzeker:
            delen.append("onzeker: nr " + ", ".join(map(str, onzeker)))
        if ongeldig:
            delen.append(
                "'nee' zonder letterlijk citaat: nr " + ", ".join(map(str, ongeldig))
            )
        return Uitkomst(
            TWIJFEL,
            "; ".join(delen),
            gevallen_onzeker=onzeker,
            citaat_ongeldig=ongeldig,
        )
    return Uitkomst(
        VOLDOET, f"alle {len(oordelen)} gevallen 'nee' met een letterlijk citaat"
    )


# --- modelaanroep en budget --------------------------------------------------


@dataclass(frozen=True)
class Antwoord:
    tekst: str
    invoer_tokens: int | None
    uitvoer_tokens: int | None
    stop_reason: str | None = None
    model_gemeld: str | None = None
    bericht_id: str | None = None


Client = Callable[[str, str], Antwoord]


def kosten_nusd(invoer_tokens: int, uitvoer_tokens: int) -> int:
    return invoer_tokens * TARIEF_INVOER_NUSD + uitvoer_tokens * TARIEF_UITVOER_NUSD


def usd(nusd: int) -> str:
    return f"{nusd / 1e9:.6f}"


def bovengrens_nusd(systeem: str, gebruiker: str) -> int:
    """Conservatieve kostengrens van één aanroep: tekens/2 invoer + max_tokens."""
    invoer_tokens = -(-(len(systeem) + len(gebruiker)) // 2)
    return kosten_nusd(invoer_tokens, MAX_TOKENS)


class Budget:
    """Harde teller: stopt vóór een aanroep bij het maximum of het kostenplafond."""

    def __init__(
        self,
        max_aanroepen: int = MAX_AANROEPEN,
        plafond_nusd: int = PLAFOND_NUSD,
        marge_nusd: int = STAPMARGE_NUSD,
    ) -> None:
        self.max_aanroepen = max_aanroepen
        self.plafond_nusd = plafond_nusd
        self.marge_nusd = marge_nusd
        self.aanroepen = 0
        self.kosten_nusd = 0
        self.kosten_volledig = True
        self.stopreden: str | None = None

    def mag_aanroepen(self, bovengrens: int) -> bool:
        """Stop als kosten + max(marge, bovengrens van deze aanroep) > plafond."""
        if self.stopreden is None and self.aanroepen >= self.max_aanroepen:
            self.stopreden = f"maximum van {self.max_aanroepen} aanroepen bereikt"
        ruimte = max(self.marge_nusd, bovengrens)
        if self.stopreden is None and self.kosten_nusd + ruimte > self.plafond_nusd:
            self.stopreden = (
                f"kosten USD {usd(self.kosten_nusd)} + max(marge USD "
                f"{usd(self.marge_nusd)}, bovengrens aanroep USD {usd(bovengrens)})"
                f" boven plafond USD {usd(self.plafond_nusd)}"
            )
        return self.stopreden is None


def _roep(
    client: Client, budget: Budget, systeem: str, gebruiker: str
) -> dict[str, Any]:
    """Eén aanroep, geteld vóór verzending; geen herhaalpoging."""
    budget.aanroepen += 1
    record: dict[str, Any] = {
        "systeem": systeem,
        "prompt": gebruiker,
        "bovengrens_kosten_usd": usd(bovengrens_nusd(systeem, gebruiker)),
    }
    try:
        antwoord = client(systeem, gebruiker)
    except AanroepError as fout:
        budget.stopreden = f"aanroep mislukt ({fout}); kosten onbekend"
        budget.kosten_volledig = False
        record["fout"] = str(fout)
        record["kosten_usd"] = None
        return record
    record.update(
        {
            "ruw": antwoord.tekst,
            "stop_reason": antwoord.stop_reason,
            "model_gemeld": antwoord.model_gemeld,
            "bericht_id": antwoord.bericht_id,
            "usage": {
                "input_tokens": antwoord.invoer_tokens,
                "output_tokens": antwoord.uitvoer_tokens,
            },
        }
    )
    if antwoord.invoer_tokens is None or antwoord.uitvoer_tokens is None:
        budget.stopreden = "usage ontbreekt in het antwoord; kosten onbekend"
        budget.kosten_volledig = False
        record["kosten_nusd"] = None
        record["kosten_usd"] = None
        return record
    kosten = kosten_nusd(antwoord.invoer_tokens, antwoord.uitvoer_tokens)
    budget.kosten_nusd += kosten
    record["kosten_nusd"] = kosten
    record["kosten_usd"] = usd(kosten)
    return record


class EchteClient:
    """Anthropic-client met vaste base_url en max_retries=0; geen temperatuur."""

    def __init__(self, api_sleutel: str) -> None:
        import anthropic

        self._sleutel = api_sleutel
        self._client = anthropic.Anthropic(
            api_key=api_sleutel,
            base_url=API_BASIS_URL,
            max_retries=MAX_RETRIES,
        )

    def __call__(self, systeem: str, gebruiker: str) -> Antwoord:
        try:
            respons = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=systeem,
                messages=[{"role": "user", "content": gebruiker}],
            )
            tekst = "".join(
                blok.text
                for blok in respons.content
                if getattr(blok, "type", None) == "text"
            )
            usage = getattr(respons, "usage", None)
            return Antwoord(
                tekst=tekst,
                invoer_tokens=getattr(usage, "input_tokens", None),
                uitvoer_tokens=getattr(usage, "output_tokens", None),
                stop_reason=respons.stop_reason,
                model_gemeld=respons.model,
                bericht_id=respons.id,
            )
        except Exception as fout:
            melding = str(fout).replace(self._sleutel, "[verborgen]")[:500]
            raise AanroepError(f"{type(fout).__name__}: {melding}") from None


# --- stub voor de droogrun ---------------------------------------------------

#: Eén scenario per goldset-item (op volgorde); samen dekken ze alle uitkomstpaden.
STUBSCENARIOS = (
    "voldoet",
    "voldoet_niet",
    "onzeker",
    "citaat_ongeldig",
    "a_onparseerbaar",
    "a_te_weinig",
    "b_mist_nr",
    "b_onbekende_waarde",
    "voldoet",
    "b_onparseerbaar",
)


class StubClient:
    """Deterministische stubantwoorden; geen sleutel, geen netwerk."""

    def __init__(self, scenarios: tuple[str, ...] = STUBSCENARIOS) -> None:
        self.scenarios = scenarios
        self.prompts: list[tuple[str, str]] = []
        self._a_aanroepen = 0
        self._huidig = scenarios[0]

    def __call__(self, systeem: str, gebruiker: str) -> Antwoord:
        self.prompts.append((systeem, gebruiker))
        if systeem == SYSTEEM_A:
            self._huidig = self.scenarios[self._a_aanroepen % len(self.scenarios)]
            self._a_aanroepen += 1
            tekst = self._antwoord_a()
        else:
            tekst = self._antwoord_b(gebruiker)
        return Antwoord(
            tekst=tekst,
            invoer_tokens=len(systeem + gebruiker) // 4,
            uitvoer_tokens=len(tekst) // 4,
            stop_reason="end_turn",
            model_gemeld=f"stub-{MODEL}",
            bericht_id=f"stub-{len(self.prompts)}",
        )

    def _antwoord_a(self) -> str:
        if self._huidig == "a_onparseerbaar":
            return "Hier zijn de verwante begrippen: ontvluchting, ontsnapping."
        verwanten = [
            {
                "begrip": "stub-verwant-1",
                "reden_verwant": "stub-reden-1",
                "gevallen": [
                    {
                        "geval": "Stubgeval een.",
                        "waarom_niet_doelbegrip": "stub-waarom-1",
                    },
                    {
                        "geval": "Stubgeval twee.",
                        "waarom_niet_doelbegrip": "stub-waarom-2",
                    },
                ],
            },
            {
                "begrip": "stub-verwant-2",
                "reden_verwant": "stub-reden-2",
                "gevallen": [
                    {
                        "geval": "Stubgeval drie.",
                        "waarom_niet_doelbegrip": "stub-waarom-3",
                    }
                ],
            },
        ]
        if self._huidig == "a_te_weinig":
            verwanten = verwanten[1:]
        return json.dumps({"verwante_begrippen": verwanten}, ensure_ascii=False)

    def _antwoord_b(self, gebruiker: str) -> str:
        definitie = re.search(r'^Definitie: "(.*)"$', gebruiker, re.MULTILINE)
        gevallen = json.loads(
            gebruiker.split("Gevallen:\n", 1)[1].split("\n\nAntwoord", 1)[0]
        )
        woorden = (definitie.group(1) if definitie else "").split()[:4]
        # Afwijkende hoofdletters en witruimte: de citaatcontrole moet dit negeren.
        citaat = "  ".join(woorden).upper()
        oordelen = [
            {
                "nr": g["nr"],
                "valt_onder": "nee",
                "citaat": citaat,
                "toelichting": "stub",
            }
            for g in gevallen
        ]
        scenario = self._huidig
        if scenario == "voldoet_niet":
            # Minimaal geldig: bij "ja" geen citaat en geen toelichting.
            oordelen[0] = {"nr": 1, "valt_onder": "ja"}
        elif scenario == "onzeker":
            oordelen[0].update(valt_onder="onzeker", citaat="")
        elif scenario == "citaat_ongeldig":
            oordelen[0]["citaat"] = "tekst die niet in de definitie staat"
        elif scenario == "b_mist_nr":
            oordelen = oordelen[:-1]
        elif scenario == "b_onbekende_waarde":
            oordelen[0]["valt_onder"] = "misschien"
        tekst = json.dumps({"oordelen": oordelen}, ensure_ascii=False)
        if scenario == "b_onparseerbaar":
            return f"```json\n{tekst}\n```"
        return tekst


# --- de proef ----------------------------------------------------------------


def verwerk_item(
    item: dict[str, Any], client: Client, budget: Budget
) -> dict[str, Any]:
    definitie_schoon = maak_schoon(item["definitie_db"])
    record: dict[str, Any] = {
        "id": item["id"],
        "begrip": item["begrip"],
        "oordeel_chris": item["oordeel_chris"],
        "definitie_db": item["definitie_db"],
        "definitie_schoon": definitie_schoon,
        "organisatorische_context": item.get("organisatorische_context") or [],
        "juridische_context": item.get("juridische_context") or [],
        "verwant_volgens_bron": item.get("verwant_volgens_bron") or [],
    }

    def niet_gedraaid() -> dict[str, Any]:
        record.update(uitkomst=NIET_GEDRAAID, reden=budget.stopreden, onbruikbaar=False)
        return record

    prompt_a = bouw_prompt_a(item)
    if not budget.mag_aanroepen(bovengrens_nusd(SYSTEEM_A, prompt_a)):
        return niet_gedraaid()
    record["aanroep_a"] = _roep(client, budget, SYSTEEM_A, prompt_a)
    if "fout" in record["aanroep_a"]:
        return niet_gedraaid()
    gevallen, fout = parse_a(record["aanroep_a"]["ruw"])
    record["gevallen"] = gevallen
    oordelen = None
    if fout is None and gevallen is not None:
        prompt_b = bouw_prompt_b(item, definitie_schoon, gevallen)
        if not budget.mag_aanroepen(bovengrens_nusd(SYSTEEM_B, prompt_b)):
            return niet_gedraaid()
        record["aanroep_b"] = _roep(client, budget, SYSTEEM_B, prompt_b)
        if "fout" in record["aanroep_b"]:
            return niet_gedraaid()
        oordelen, fout = parse_b(record["aanroep_b"]["ruw"], len(gevallen))
        if oordelen is not None:
            for oordeel in oordelen:
                oordeel["citaat_letterlijk"] = citaat_staat_in(
                    oordeel["citaat"], definitie_schoon
                )
    record["oordelen"] = oordelen
    uitkomst = bepaal_uitkomst(fout, oordelen, definitie_schoon)
    record.update(
        uitkomst=uitkomst.uitkomst,
        reden=uitkomst.reden,
        onbruikbaar=uitkomst.onbruikbaar,
        gevallen_ja=list(uitkomst.gevallen_ja),
        gevallen_onzeker=list(uitkomst.gevallen_onzeker),
        citaat_ongeldig=list(uitkomst.citaat_ongeldig),
    )
    return record


def _git(*args: str) -> str | None:
    try:
        resultaat = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return resultaat.stdout.strip()


def _schrijf_json(pad: Path, data: Any) -> None:
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")


def vat_samen(
    records: list[dict[str, Any]], budget: Budget, kop: dict[str, Any]
) -> dict[str, Any]:
    items = [
        {
            "id": r["id"],
            "begrip": r["begrip"],
            "oordeel_chris": r["oordeel_chris"],
            "uitkomst": r["uitkomst"],
            "gelijk": r["uitkomst"] == r["oordeel_chris"],
            "onbruikbaar": r["onbruikbaar"],
            "reden": r["reden"],
        }
        for r in records
    ]
    onterecht = [
        i["id"]
        for i in items
        if i["uitkomst"] == VOLDOET and i["oordeel_chris"] in (TWIJFEL, VOLDOET_NIET)
    ]
    return {
        **kop,
        "criteria": CRITERIA,
        "aantal_items": len(items),
        "aantal_gelijk": sum(i["gelijk"] for i in items),
        "gelijk_waarvan_onbruikbaar": sum(
            i["gelijk"] and i["onbruikbaar"] for i in items
        ),
        "onterecht_voldoet": len(onterecht),
        "onterecht_voldoet_ids": onterecht,
        "aantal_onbruikbaar": sum(i["onbruikbaar"] for i in items),
        "aantal_niet_gedraaid": sum(i["uitkomst"] == NIET_GEDRAAID for i in items),
        "aantal_aanroepen": budget.aanroepen,
        # Bekende kosten en volledigheid apart: een onbekend totaal is nooit 0.
        "kosten_bekend_nusd": budget.kosten_nusd,
        "kosten_bekend_usd": usd(budget.kosten_nusd),
        "kosten_volledig": budget.kosten_volledig,
        "budget": {
            "max_aanroepen": budget.max_aanroepen,
            "plafond_usd": usd(budget.plafond_nusd),
            "stapmarge_usd": usd(budget.marge_nusd),
            "stopreden": budget.stopreden,
        },
        "items": items,
    }


def _kostentekst(s: dict[str, Any]) -> str:
    if s["kosten_volledig"]:
        return f"USD {s['kosten_bekend_usd']} (volledig)"
    return (
        f"totaal onbekend; bekend deel USD {s['kosten_bekend_usd']}"
        " (niet van alle aanroepen is usage bekend)"
    )


def samenvatting_md(s: dict[str, Any]) -> str:
    regels = [
        f"# ESS-05 voorbeeldenproef — {s['modus']}",
        "",
        f"Vooraf vastgelegde criteria: {s['criteria']}",
        "",
        "Dit overzicht rapporteert cijfers; het trekt geen conclusie.",
        "",
        "| id | begrip | oordeel_chris | uitkomst | gelijk | reden |",
        "|---|---|---|---|---|---|",
    ]
    for i in s["items"]:
        reden = str(i["reden"]).replace("|", "\\|")
        regels.append(
            f"| {i['id']} | {i['begrip']} | {i['oordeel_chris']} | {i['uitkomst']}"
            f" | {'ja' if i['gelijk'] else 'nee'} | {reden} |"
        )
    regels += [
        "",
        (
            f"- Gelijk aan goldset: {s['aantal_gelijk']}/{s['aantal_items']}"
            f" (waarvan via onbruikbare uitvoer: {s['gelijk_waarvan_onbruikbaar']})"
        ),
        (
            f"- onterecht_voldoet: {s['onterecht_voldoet']}"
            f" ({', '.join(s['onterecht_voldoet_ids']) or '-'})"
        ),
        f"- Onbruikbaar: {s['aantal_onbruikbaar']}",
        f"- Niet gedraaid: {s['aantal_niet_gedraaid']}",
        f"- Aanroepen: {s['aantal_aanroepen']}",
        f"- Kosten: {_kostentekst(s)}",
        f"- Budgetstop: {s['budget']['stopreden'] or '-'}",
        (
            f"- Model: {s['model']} (temperatuur: {s['temperatuur']},"
            f" max_tokens {s['max_tokens']}, max_retries {s['max_retries']})"
        ),
        f"- Git HEAD: {s['git_head']} (werkboom schoon: {s['werkboom_schoon']})",
        f"- sha256 goldset: {s['goldset_sha256']}",
        f"- sha256 sjabloon A: {s['sjabloon_a_sha256']}",
        f"- sha256 sjabloon B: {s['sjabloon_b_sha256']}",
        f"- sha256 script: {s['script_sha256']}",
        "",
    ]
    return "\n".join(regels)


def voer_proef_uit(
    goldset_pad: Path,
    uitmap: Path,
    client: Client,
    modus: str,
    budget: Budget | None = None,
) -> dict[str, Any]:
    """Draai alle items, schrijf per item een JSON en de samenvatting."""
    budget = budget or Budget()
    goldset = json.loads(goldset_pad.read_text("utf-8"))
    try:
        uitmap.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        msg = f"uitvoermap bestaat al: {uitmap}; geweigerd"
        raise ProefError(msg) from None
    status = _git("status", "--porcelain")
    kop = {
        "modus": modus,
        "model": MODEL,
        "temperatuur": TEMPERATUUR,
        "max_tokens": MAX_TOKENS,
        "max_retries": MAX_RETRIES,
        "git_head": _git("rev-parse", "HEAD") or "onbekend",
        "werkboom_schoon": None if status is None else status == "",
        "goldset_pad": str(goldset_pad),
        "goldset_sha256": sha256_bestand(goldset_pad),
        "sjabloon_a_sha256": sha256_tekst(SJABLOON_A),
        "sjabloon_b_sha256": sha256_tekst(SJABLOON_B),
        "script_sha256": sha256_bestand(Path(__file__)),
    }
    records = []
    for volgnr, item in enumerate(goldset["definities"], start=1):
        record = verwerk_item(item, client, budget)
        records.append(record)
        _schrijf_json(uitmap / f"item-{volgnr:02d}-{item['id']}.json", record)
        logger.info("%s: %s (%s)", item["id"], record["uitkomst"], record["reden"])
    samenvatting = vat_samen(records, budget, kop)
    _schrijf_json(uitmap / "samenvatting.json", samenvatting)
    (uitmap / "samenvatting.md").write_text(samenvatting_md(samenvatting), "utf-8")
    return samenvatting


def lees_api_sleutel(env_bestand: Path) -> str:
    """Leest alleen ANTHROPIC_API_KEY; de waarde wordt nooit getoond of gelogd."""
    if not env_bestand.is_file():
        msg = f"env-bestand ontbreekt: {env_bestand}"
        raise ProefError(msg)
    for regel in env_bestand.read_text("utf-8").splitlines():
        regel = regel.strip()
        if regel.startswith("export "):
            regel = regel[len("export ") :].strip()
        naam, is_gelijk, waarde = regel.partition("=")
        if is_gelijk and naam.strip() == "ANTHROPIC_API_KEY":
            waarde = _env_waarde(waarde.strip(), env_bestand)
            if waarde:
                return waarde
    msg = f"ANTHROPIC_API_KEY ontbreekt of is leeg in {env_bestand}"
    raise ProefError(msg)


def _env_waarde(ruw: str, env_bestand: Path) -> str:
    """Gequote waarde letterlijk; ongequote waarde met inlinecommentaar geweigerd.

    Foutmeldingen noemen nooit de waarde zelf.
    """
    if ruw[:1] in ("'", '"'):
        einde = ruw.find(ruw[0], 1)
        rest = ruw[einde + 1 :].strip() if einde > 0 else ""
        if einde < 0 or (rest and not rest.startswith("#")):
            msg = f"ANTHROPIC_API_KEY in {env_bestand} heeft ongeldige quotes"
            raise ProefError(msg)
        return ruw[1:einde]
    if re.search(r"\s#", ruw):
        msg = (
            f"ANTHROPIC_API_KEY in {env_bestand} heeft inlinecommentaar achter een "
            "ongequote waarde; zet de waarde tussen quotes of verwijder het commentaar"
        )
        raise ProefError(msg)
    return ruw


def voer_echt_uit(
    run: int,
    env_bestand: Path,
    basis: Path = UITVOERBASIS,
    goldset_pad: Path = GOLDSET_PAD,
    client_fabriek: Callable[[str], Client] = EchteClient,
) -> dict[str, Any]:
    uitmap = basis / f"run-{run}"
    if uitmap.exists():
        msg = f"run-map bestaat al: {uitmap}; geweigerd"
        raise ProefError(msg)
    if not goldset_pad.is_file():
        msg = f"goldset ontbreekt: {goldset_pad}"
        raise ProefError(msg)
    client = client_fabriek(lees_api_sleutel(env_bestand))
    return voer_proef_uit(goldset_pad, uitmap, client, modus=f"echt run {run}")


def vergelijk(basis: Path = UITVOERBASIS) -> dict[str, Any]:
    """Stabiliteit: gelijke uitkomst per item tussen run-1 en run-2."""
    runs = []
    for n in (1, 2):
        pad = basis / f"run-{n}" / "samenvatting.json"
        if not pad.is_file():
            msg = f"samenvatting ontbreekt: {pad}"
            raise ProefError(msg)
        runs.append(json.loads(pad.read_text("utf-8")))
    een, twee = ({i["id"]: i for i in run["items"]} for run in runs)
    if set(een) != set(twee):
        msg = "run-1 en run-2 bevatten niet dezelfde items"
        raise ProefError(msg)
    items = [
        {
            "id": item_id,
            "uitkomst_run_1": een[item_id]["uitkomst"],
            "uitkomst_run_2": twee[item_id]["uitkomst"],
            "gelijk": een[item_id]["uitkomst"] == twee[item_id]["uitkomst"]
            and een[item_id]["uitkomst"] != NIET_GEDRAAID,
        }
        for item_id in een
    ]
    resultaat = {
        "criteria": CRITERIA,
        "aantal_items": len(items),
        "aantal_gelijk": sum(i["gelijk"] for i in items),
        "zelfde_goldset": runs[0]["goldset_sha256"] == runs[1]["goldset_sha256"],
        "zelfde_sjablonen": all(
            runs[0][k] == runs[1][k] for k in ("sjabloon_a_sha256", "sjabloon_b_sha256")
        ),
        "items": items,
    }
    uit_json, uit_md = basis / "vergelijking.json", basis / "vergelijking.md"
    if uit_json.exists() or uit_md.exists():
        msg = f"vergelijking bestaat al in {basis}; geweigerd"
        raise ProefError(msg)
    _schrijf_json(uit_json, resultaat)
    regels = [
        "# ESS-05 voorbeeldenproef — vergelijking run 1 en run 2",
        "",
        f"Vooraf vastgelegde criteria: {CRITERIA}",
        "",
        "| id | run 1 | run 2 | gelijk |",
        "|---|---|---|---|",
        *(
            f"| {i['id']} | {i['uitkomst_run_1']} | {i['uitkomst_run_2']}"
            f" | {'ja' if i['gelijk'] else 'nee'} |"
            for i in items
        ),
        "",
        (
            f"- Gelijk tussen run 1 en run 2: {resultaat['aantal_gelijk']}"
            f"/{resultaat['aantal_items']} ('niet gedraaid' telt niet als gelijk)"
        ),
        (
            f"- Zelfde goldset: {resultaat['zelfde_goldset']};"
            f" zelfde sjablonen: {resultaat['zelfde_sjablonen']}"
        ),
        "",
    ]
    uit_md.write_text("\n".join(regels), "utf-8")
    return resultaat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modus = parser.add_mutually_exclusive_group(required=True)
    modus.add_argument("--droog", action="store_true", help="stubantwoorden")
    modus.add_argument("--echt", action="store_true", help="echte modelaanroepen")
    modus.add_argument("--vergelijk", action="store_true", help="run-1 vs run-2")
    parser.add_argument("--uitmap", type=Path, help="uitvoermap (alleen --droog)")
    parser.add_argument("--run", type=int, choices=(1, 2), help="alleen --echt")
    parser.add_argument("--env-file", type=Path, default=STANDAARD_ENV)
    parser.add_argument("--goldset", type=Path, help="alleen --droog")
    parser.add_argument("--basis", type=Path, help="alleen --vergelijk")
    args = parser.parse_args(argv)

    if args.droog and (args.uitmap is None or args.run is not None):
        parser.error("--droog vereist --uitmap en geen --run")
    if args.echt and (
        args.run is None or args.uitmap or args.goldset or args.basis is not None
    ):
        parser.error("--echt vereist --run 1|2 en schrijft altijd naar run-{n}")
    if args.vergelijk and (args.uitmap or args.run or args.goldset):
        parser.error("--vergelijk neemt alleen --basis")

    try:
        if args.droog:
            samenvatting = voer_proef_uit(
                args.goldset or GOLDSET_PAD, args.uitmap, StubClient(), modus="droog"
            )
        elif args.echt:
            samenvatting = voer_echt_uit(args.run, args.env_file)
        else:
            resultaat = vergelijk(args.basis or UITVOERBASIS)
            logger.info(
                "gelijk tussen run 1 en run 2: %s/%s",
                resultaat["aantal_gelijk"],
                resultaat["aantal_items"],
            )
            return 0
    except ProefError as fout:
        logger.error("geweigerd: %s", fout)
        return 2
    logger.info(
        "gelijk %s/%s, onterecht_voldoet %s, onbruikbaar %s, aanroepen %s, "
        "kosten: %s",
        samenvatting["aantal_gelijk"],
        samenvatting["aantal_items"],
        samenvatting["onterecht_voldoet"],
        samenvatting["aantal_onbruikbaar"],
        samenvatting["aantal_aanroepen"],
        _kostentekst(samenvatting),
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
