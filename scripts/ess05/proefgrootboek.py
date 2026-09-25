"""DEF-768 WP7 — callgrootboek en netwerkbewaking van de ESS-05-proefrunner.

Het grootboek is het enige budgetgeheugen van de proef, over alle fases en
hervattingen heen (uitvoercontract v2, variant A: 13 ontwikkeling + 20 T-eind
+ 8 T-herhalingen + 16 G + 3 technische reserve = 60 echte calls):

- **append-only JSONL met hashketen** — elke regel draagt de sha256 van de
  vorige; een gewijzigde, verwijderde of afgekapte regel maakt het grootboek
  onbruikbaar (fail-closed), nooit een stille nulstand;
- **reservering vóór netwerk** — een reservering telt, ook als de aanroep
  daarna faalt, afloopt, vóór het netwerk strandt (`niet_verzonden`) of het
  proces crasht (reservering zonder afsluiting);
- **harde caps** per fase en in totaal; de reserve alleen expliciet
  (`technische_herhaling=True`) en alleen voor een sleutel waarvan de laatste
  poging technisch mislukte of onafgesloten bleef — nooit na een inhoudelijk
  modelantwoord (dat zou uitkomsten uitzoeken zijn);
- **één sleutel = één poging** — geen tweede ontwikkelronde;
- **bevroren invoer per fase** — de eerste reservering legt de invoerhash vast;
- **eindbinding** — `t_eind` en `t_herhaling` (ook hun technische reserve)
  delen één binding: datasethash, voorafgekozen `herhaal_ids`, codehash en
  de hash van de effectieve model-/promptconfiguratie. De ontwikkelronde
  heeft geen eindbinding (correcties vóór de freeze); een technische
  herhaling vereist in élke fase dezelfde prompt- en configuratiehash;
- **anker** (`<grootboek>.anker.json`) — een afzonderlijk, na elke regel
  bijgewerkt eindpunt (proef-id, aantal regels, kophash). Een leeg, afgekapt,
  ouder of ander grootboek, of een ontbrekend anker, valt daardoor op; een
  nieuw grootboek naast een bestaand anker (nulreset) wordt geweigerd.
  Crashvolgorde: eerst de regel (fsync), dan het anker; één regel vóór op
  het anker is de crash daartussen en telt mee. Wie grootboek én anker
  moedwillig verwijdert, wordt hiermee niet tegengehouden.

Proefidentiteiten: `R1` (hierboven, standaard, ongewijzigd) en `R2` (ronde 2,
DEF-768-AI-20260924-R2: 9 T-ontwikkeling + 4 G-ontwikkeling + 20 T-eind + 8
T-herhalingen + 16 G-eind + 3 reserve = 60; eindgroepen T en G, beide met
`freeze_sha256` in de binding; samen met R1 nooit boven 117, zie
`controleer_cumulatief`) en `R3` (ronde 3, DEF-768-AI-20260924-R3: dezelfde
verdeling van 60; samen met R2 en R1 nooit boven 174) en `R4` (ronde 4,
DEF-768-AI-20260924-R4: dezelfde verdeling van 60; samen met R3, R2 en R1
nooit boven 231) en `R5` (ronde 5, DEF-768-AI-20260925-R5: dezelfde
verdeling van 60; samen met R4 t/m R1 nooit boven 288) en `R6` (ronde 6,
DEF-768-AI-20260925-R6: alleen T — 9 ontwikkeling + 20 T-eind + 8
T-herhalingen + 3 reserve = 40, alleen eindgroep T; samen met R5 t/m R1 nooit
boven 325) en `R7` (ronde 7, DEF-768-AI-20260925-R7: dezelfde T-verdeling van
40, alleen eindgroep T; samen met R6 t/m R1 nooit boven 362). Het anker draagt de
proef-id; een grootboek opent alleen onder zijn eigen identiteit. Andere
identiteiten bestaan niet.

De bewaking (`BewaakteClient`, `installeer_sdk_wacht`) laat per actieve
reservering precies één providerclientaanroep en één SDK-aanroep toe, met
SDK-retries aantoonbaar 0, en leest de werkelijke usage uit de SDK-respons.

Meerstapspogingen (ADR-003, DEF-768 WP5): een geval met meerdere modelstappen
(bv. conceptoordeel en semantische verificatie) krijgt per stap een eigen
reservering (`Stappenpoging`), met dezelfde pogingidentiteit (`poging`) en
een eigen `stap`. Een stap wordt pas bij haar aanroep gereserveerd, alleen
direct na de vorige stap van dezelfde poging, en nooit tweemaal; een
technische herhaling van een meerstapspoging is niet vastgelegd en wordt
geweigerd. Welke identiteit hoeveel stappen per geval goedkeurt, staat in
`Proefidentiteit.modelstappen_per_geval` (R1 t/m R7: één).
`BudgetSchendingError` is bewust géén `AIClientError`: de retrylus van
`AsyncGPTClient` herhaalt hem nooit.
"""

from __future__ import annotations

import contextlib
import contextvars
import fcntl
import hashlib
import json
import logging
import os
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

__all__ = [
    "AFSLUITSTATUSSEN",
    "BINDINGSVELDEN",
    "EINDFASES",
    "FASECAPS",
    "PROEF_ID",
    "R1",
    "R2",
    "R3",
    "R4",
    "R5",
    "R6",
    "R7",
    "RESERVE_MAX",
    "TOTAAL_MAX",
    "BewaakteClient",
    "BudgetSchendingError",
    "Eindgroep",
    "Grootboek",
    "Proefidentiteit",
    "Proefslot",
    "Reservering",
    "Stappenpoging",
    "actief",
    "ankerpad",
    "controleer_cumulatief",
    "installeer_sdk_wacht",
    "kosten",
    "schrijf_nieuw",
    "scrub",
    "voorgangerketen",
]

logger = logging.getLogger("ess05.proefgrootboek")

#: Uitvoercontract v2, variant A (akkoord Chris, Linear DEF-768 b097eff4).
FASECAPS: dict[str, int] = {
    "ontwikkeling": 13,
    "t_eind": 20,
    "t_herhaling": 8,
    "g": 16,
}
RESERVE_MAX = 3
TOTAAL_MAX = sum(FASECAPS.values()) + RESERVE_MAX
#: De fases die samen aan één eindbinding hangen (zie `BINDINGSVELDEN`).
EINDFASES = frozenset({"t_eind", "t_herhaling"})
#: Eindbinding: dataset, herhaal_ids, code en de effectieve (niet-geheime)
#: model-/promptconfiguratie van de runner.
BINDINGSVELDEN = ("dataset_sha256", "herhaal_ids", "code_sha256", "config_sha256")
#: Een technische herhaling is dezelfde call: zelfde prompt en configuratie.
_RESERVE_GELIJK = (
    ("prompt_sha256", "prompt"),
    ("config_sha256", "effectieve configuratie"),
)
#: De canonieke identiteit van deze proef (anker en grootboek dragen hem).
PROEF_ID = "DEF-768-WP7-ess05-proef-20260924"
_ANKERSCHEMA = "def768-ess05-grootboekanker/1"


@dataclass(frozen=True)
class Eindgroep:
    """Fases die samen aan één eindbinding hangen."""

    naam: str
    fases: frozenset[str]
    #: Vereist aantal voorafgekozen `herhaal_ids` in de binding.
    herhaal_aantal: int


@dataclass(frozen=True)
class Proefidentiteit:
    """Een vaste proef: id, fasecaps, reserve en eindgroepen.

    Alleen `R1` en `R2` hieronder bestaan; een andere identiteit wordt bij
    openen en aanmaken geweigerd (geen vrij configureerbare caps of reset).
    """

    proef_id: str
    fasecaps: Mapping[str, int]
    reserve_max: int
    eindgroepen: tuple[Eindgroep, ...]
    bindingsvelden: tuple[str, ...]
    #: De vorige ronde; samen nooit boven `cumulatief_max` echte calls.
    voorganger: Proefidentiteit | None = None
    cumulatief_max: int | None = None
    #: Modelstappen per geval waarvoor deze ronde is goedgekeurd (budgetbesluit).
    modelstappen_per_geval: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "fasecaps", MappingProxyType(dict(self.fasecaps)))

    @property
    def totaal_max(self) -> int:
        return sum(self.fasecaps.values()) + self.reserve_max

    def eindgroep(self, fase: str) -> Eindgroep | None:
        return next((g for g in self.eindgroepen if fase in g.fases), None)


#: Ronde 1 (uitvoercontract v2, variant A) — de standaard, ongewijzigd.
R1 = Proefidentiteit(
    proef_id=PROEF_ID,
    fasecaps=FASECAPS,
    reserve_max=RESERVE_MAX,
    eindgroepen=(Eindgroep("t", EINDFASES, 4),),
    bindingsvelden=BINDINGSVELDEN,
)
#: Ronde 2 (besluit Chris 24-09, max 60 extra calls, cumulatief max 117):
#: 9 T-ontwikkeling, 4 G-ontwikkeling, 20 T-eind, 8 T-herhaling, 16 G-eind en
#: 3 technische reserve. Beide eindgroepen zijn aan een freeze gebonden.
R2 = Proefidentiteit(
    proef_id="DEF-768-AI-20260924-R2",
    fasecaps={
        "ontwikkeling": 9,
        "g_ontwikkeling": 4,
        "t_eind": 20,
        "t_herhaling": 8,
        "g": 16,
    },
    reserve_max=3,
    eindgroepen=(
        Eindgroep("t", frozenset({"t_eind", "t_herhaling"}), 4),
        Eindgroep("g", frozenset({"g"}), 0),
    ),
    bindingsvelden=(*BINDINGSVELDEN, "freeze_sha256"),
    voorganger=R1,
    cumulatief_max=117,
)
#: Ronde 3 (besluit Chris 24-09, derde herstelvoorstel): max 60 aanvullende
#: calls met dezelfde verdeling als R2; samen met R1 en R2 nooit boven 174
#: (114 werkelijke R1+R2-calls + 60). Ongebruikte R1/R2-reserve telt niet mee.
R3 = Proefidentiteit(
    proef_id="DEF-768-AI-20260924-R3",
    fasecaps=R2.fasecaps,
    reserve_max=3,
    eindgroepen=R2.eindgroepen,
    bindingsvelden=R2.bindingsvelden,
    voorganger=R2,
    cumulatief_max=174,
)
#: Ronde 4 (besluit Chris 24-09, gericht vervolg na R3): max 60 extra calls
#: met dezelfde verdeling; samen met R3, R2 en R1 nooit boven 231 (171
#: werkelijke R1+R2+R3-calls + 60). Oude reserves zijn gesloten.
R4 = Proefidentiteit(
    proef_id="DEF-768-AI-20260924-R4",
    fasecaps=R3.fasecaps,
    reserve_max=3,
    eindgroepen=R3.eindgroepen,
    bindingsvelden=R3.bindingsvelden,
    voorganger=R3,
    cumulatief_max=231,
)
#: Ronde 5 (akkoord Chris 25-09, R4 uitkomst-en-vervolg-v1 §vervolg): max 60
#: nieuwe calls met dezelfde verdeling; samen met R4 t/m R1 nooit boven 288
#: (228 werkelijke R1–R4-calls + 60). Oude reserves zijn gesloten.
R5 = Proefidentiteit(
    proef_id="DEF-768-AI-20260925-R5",
    fasecaps=R4.fasecaps,
    reserve_max=3,
    eindgroepen=R4.eindgroepen,
    bindingsvelden=R4.bindingsvelden,
    voorganger=R4,
    cumulatief_max=288,
)
#: Ronde 6 (akkoord Chris 25-09, R5 uitkomst-en-vervolg-v1 §vervolg): max 40
#: nieuwe uitsluitend T-calls (9 ontwikkeling, 20 T-eind, 8 T-herhaling, 3
#: reserve); samen met R5 t/m R1 nooit boven 325 (285 werkelijke R1–R5-calls
#: + 40). G-fases bestaan in deze ronde niet en worden dus geweigerd.
R6 = Proefidentiteit(
    proef_id="DEF-768-AI-20260925-R6",
    fasecaps={"ontwikkeling": 9, "t_eind": 20, "t_herhaling": 8},
    reserve_max=3,
    eindgroepen=(R5.eindgroepen[0],),
    bindingsvelden=R5.bindingsvelden,
    voorganger=R5,
    cumulatief_max=325,
)
#: Ronde 7 (akkoord Chris 25-09, R6 uitkomst-en-vervolg-v1 §vervolg): max 40
#: nieuwe uitsluitend T-calls (9 ontwikkeling, 20 T-eind, 8 T-herhaling, 3
#: reserve); samen met R6 t/m R1 nooit boven 362 (322 werkelijke R1–R6-calls
#: + 40). G-fases bestaan in deze ronde niet en worden dus geweigerd.
R7 = Proefidentiteit(
    proef_id="DEF-768-AI-20260925-R7",
    fasecaps={"ontwikkeling": 9, "t_eind": 20, "t_herhaling": 8},
    reserve_max=3,
    eindgroepen=R6.eindgroepen,
    bindingsvelden=R6.bindingsvelden,
    voorganger=R6,
    cumulatief_max=362,
)
_IDENTITEITEN = {i.proef_id: i for i in (R1, R2, R3, R4, R5, R6, R7)}


def _bekende_identiteit(identiteit: Proefidentiteit) -> Proefidentiteit:
    if _IDENTITEITEN.get(identiteit.proef_id) is not identiteit:
        msg = f"onbekende proefidentiteit {identiteit.proef_id!r}; alleen R1 t/m R7"
        raise BudgetSchendingError(msg)
    return identiteit


_HEX64 = re.compile(r"[0-9a-f]{64}")

#: `voltooid` = modelantwoord ontvangen en verwerkt; `modelfout` = antwoord
#: ontvangen maar inhoudelijk onbruikbaar (geen reserve!); `technisch` =
#: transportfout/timeout; `niet_verzonden` = na reservering, vóór het netwerk
#: mislukt (telt wel); `afgebroken` = deadline/annulering van de runner.
AFSLUITSTATUSSEN = frozenset(
    {"voltooid", "modelfout", "technisch", "niet_verzonden", "afgebroken"}
)
_RESERVE_TOEGESTAAN_NA = frozenset({"technisch", "niet_verzonden", "afgebroken"})
_NUL = "0" * 64
_SECRET_RE = re.compile(r"sk-[\w-]{10,}")


class BudgetSchendingError(RuntimeError):
    """Een budget-, bewakings- of integriteitsregel is geschonden (fail-closed)."""


def scrub(tekst: str) -> str:
    """Vervang alles wat op een API-sleutel lijkt."""
    return _SECRET_RE.sub("[REDACTED]", tekst)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _nu() -> str:
    return datetime.now(UTC).isoformat()


def ankerpad(pad: Path) -> Path:
    """Het afzonderlijke eindpuntbestand naast het grootboek."""
    pad = Path(pad)
    return pad.with_name(pad.name + ".anker.json")


def _fsync_map(map_: Path) -> None:
    fd = os.open(map_, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _schrijf_anker(pad: Path, regels: int, kop: str, proef_id: str) -> None:
    """Werk het anker atomair bij (tijdelijk bestand, fsync, vervangen, map-fsync)."""
    anker = ankerpad(pad)
    tijdelijk = anker.with_name(f"{anker.name}.{os.getpid()}.tmp")
    data = {
        "schema": _ANKERSCHEMA,
        "proef_id": proef_id,
        "grootboek": Path(pad).name,
        "regels": regels,
        "kop_sha256": kop,
        "tijd": _nu(),
    }
    with tijdelijk.open("w", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    tijdelijk.replace(anker)
    _fsync_map(anker.parent)


def _lees_anker(pad: Path, proef_id: str) -> tuple[int, str]:
    anker = ankerpad(pad)
    if not anker.is_file():
        msg = (
            f"anker {anker.name} ontbreekt: grootboek zonder vastgelegd eindpunt "
            "(verwijderd anker of verwisseld pad); geen nulstand"
        )
        raise BudgetSchendingError(msg)
    try:
        data = json.loads(anker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"anker {anker.name} is onleesbaar: {exc}"
        raise BudgetSchendingError(msg) from exc
    if (
        data.get("schema") != _ANKERSCHEMA
        or data.get("proef_id") != proef_id
        or data.get("grootboek") != Path(pad).name
        or not isinstance(data.get("regels"), int)
        or data["regels"] < 0
        or not isinstance(data.get("kop_sha256"), str)
    ):
        msg = f"anker {anker.name} hoort niet bij deze proef of dit grootboek"
        raise BudgetSchendingError(msg)
    return data["regels"], data["kop_sha256"]


class Grootboek:
    """Het duurzame, append-only callgrootboek (zie moduledocstring)."""

    def __init__(
        self,
        pad: Path,
        records: list[dict[str, Any]],
        kop: str,
        identiteit: Proefidentiteit = R1,
        *,
        alleen_lezen: bool = False,
    ) -> None:
        self.pad = pad
        self._records = records
        self._kop = kop
        self.identiteit = identiteit
        self._alleen_lezen = alleen_lezen

    # --- openen -------------------------------------------------------------

    @classmethod
    def nieuw(cls, pad: Path, identiteit: Proefidentiteit = R1) -> Grootboek:
        """Een leeg grootboek; weigert als het bestand of zijn anker al bestaat."""
        identiteit = _bekende_identiteit(identiteit)
        pad = Path(pad)
        if pad.exists():
            msg = (
                f"grootboek {pad} bestaat al; hervat met open(), nooit opnieuw beginnen"
            )
            raise BudgetSchendingError(msg)
        if ankerpad(pad).exists():
            msg = (
                f"anker {ankerpad(pad).name} bestaat al zonder grootboek: een nieuw "
                "grootboek zou een nulreset zijn en wordt geweigerd"
            )
            raise BudgetSchendingError(msg)
        pad.parent.mkdir(parents=True, exist_ok=True)
        with pad.open("x", encoding="utf-8"):
            pass
        _schrijf_anker(pad, 0, _NUL, identiteit.proef_id)
        return cls(pad, [], _NUL, identiteit)

    @classmethod
    def open(cls, pad: Path, identiteit: Proefidentiteit = R1) -> Grootboek:
        """Een bestaand grootboek, na volledige keten- en ankercontrole."""
        return cls._laad(pad, identiteit, herstel_anker=True)

    @classmethod
    def lees(cls, pad: Path, identiteit: Proefidentiteit = R1) -> Grootboek:
        """Alleen lezen (bv. de voorganger): zelfde controles, schrijft nooit.

        Een regel vóór op het anker (crash) telt mee, maar het anker wordt
        niet hersteld; reserveren en afsluiten zijn geweigerd.
        """
        return cls._laad(pad, identiteit, herstel_anker=False)

    @classmethod
    def _laad(
        cls, pad: Path, identiteit: Proefidentiteit, *, herstel_anker: bool
    ) -> Grootboek:
        identiteit = _bekende_identiteit(identiteit)
        pad = Path(pad)
        if not pad.is_file():
            msg = (
                f"grootboek {pad} ontbreekt; een ontbrekend grootboek is geen nulstand"
            )
            raise BudgetSchendingError(msg)
        anker_regels, anker_kop = _lees_anker(pad, identiteit.proef_id)
        records, koppen = cls._lees_keten(pad)
        cls._controleer_anker(
            pad,
            len(records),
            koppen,
            anker_regels,
            anker_kop,
            proef_id=identiteit.proef_id if herstel_anker else None,
        )
        return cls(pad, records, koppen[-1], identiteit, alleen_lezen=not herstel_anker)

    @staticmethod
    def _controleer_anker(
        pad: Path,
        aantal: int,
        koppen: list[str],
        regels: int,
        kop: str,
        *,
        proef_id: str | None,
    ) -> None:
        """`proef_id=None`: alleen lezen, het anker wordt niet hersteld."""
        if aantal < regels:
            msg = (
                f"grootboek heeft {aantal} regels, het anker {regels}: afgekapt of "
                "teruggezet naar een oudere versie (geen nulstand)"
            )
            raise BudgetSchendingError(msg)
        if koppen[regels] != kop:
            msg = "grootboek wijkt af van het anker: ander of vervangen grootboek"
            raise BudgetSchendingError(msg)
        if aantal > regels + 1:
            msg = (
                f"grootboek loopt {aantal - regels} regels vóór op het anker; "
                "alleen één regel (crash tussen regel en anker) is verklaarbaar"
            )
            raise BudgetSchendingError(msg)
        if aantal == regels + 1 and proef_id is not None:
            logger.warning(
                "grootboek één regel vóór op het anker (crash na regel, vóór anker); "
                "anker hersteld, de reservering telt mee"
            )
            _schrijf_anker(pad, aantal, koppen[-1], proef_id)

    @staticmethod
    def _lees_keten(pad: Path) -> tuple[list[dict[str, Any]], list[str]]:
        """(records, koppen) met koppen[i] = kophash na i regels."""
        records: list[dict[str, Any]] = []
        kop = _NUL
        koppen = [kop]
        for nr, regel in enumerate(pad.read_bytes().splitlines(keepends=True), 1):
            if not regel.endswith(b"\n"):
                msg = f"grootboekregel {nr} is onleesbaar (afgekapt)"
                raise BudgetSchendingError(msg)
            try:
                record = json.loads(regel)
            except json.JSONDecodeError as exc:
                msg = f"grootboekregel {nr} is onleesbaar: {exc}"
                raise BudgetSchendingError(msg) from exc
            if record.get("vorige_sha256") != kop:
                msg = f"hashketen gebroken bij regel {nr}: grootboek is gewijzigd"
                raise BudgetSchendingError(msg)
            kop = _sha(regel)
            koppen.append(kop)
            records.append(record)
        return records, koppen

    # --- lezen --------------------------------------------------------------

    def _reserveringen(self) -> list[dict[str, Any]]:
        return [r for r in self._records if r["soort"] == "reservering"]

    def _afsluitingen(self) -> dict[int, dict[str, Any]]:
        return {r["seq"]: r for r in self._records if r["soort"] == "afsluiting"}

    def gereserveerd(self, sleutel: str) -> bool:
        return any(r["sleutel"] == sleutel for r in self._reserveringen())

    def poging_gestart(self, poging: str) -> bool:
        """Is er voor deze poging (enkelvoudig of een van haar stappen) gereserveerd?"""
        return any(
            r["sleutel"] == poging or r.get("poging") == poging
            for r in self._reserveringen()
        )

    def samenvatting(self) -> dict[str, Any]:
        caps = self.identiteit.fasecaps
        reserveringen = self._reserveringen()
        afgesloten = self._afsluitingen()
        per_fase = dict.fromkeys(caps, 0)
        per_status: dict[str, int] = {}
        for r in reserveringen:
            if r["budget_bron"] == "fase":
                per_fase[r["fase"]] += 1
            status = afgesloten.get(r["seq"], {}).get("status", "onafgesloten")
            per_status[status] = per_status.get(status, 0) + 1
        return {
            "proef_id": self.identiteit.proef_id,
            "totaal": len(reserveringen),
            "totaal_max": self.identiteit.totaal_max,
            "per_fase": per_fase,
            "fasecaps": dict(caps),
            "reserve": sum(1 for r in reserveringen if r["budget_bron"] == "reserve"),
            "reserve_max": self.identiteit.reserve_max,
            "onafgesloten": per_status.get("onafgesloten", 0),
            "per_status": per_status,
            "netwerk_gestart": sum(
                1 for a in afgesloten.values() if a.get("netwerk_gestart")
            ),
            "kop_sha256": self._kop,
        }

    # --- schrijven ----------------------------------------------------------

    def _voeg_toe(self, record: dict[str, Any]) -> dict[str, Any]:
        if self._alleen_lezen:
            msg = f"grootboek {self.pad.name} is alleen-lezen geopend"
            raise BudgetSchendingError(msg)
        record = {**record, "vorige_sha256": self._kop, "tijd": _nu()}
        regel = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        with self.pad.open("ab") as f:
            f.write(regel)
            f.flush()
            os.fsync(f.fileno())
        self._kop = _sha(regel)
        self._records.append(record)
        # Crashvolgorde: pas ná de duurzame regel het anker (zie moduledocstring).
        _schrijf_anker(
            self.pad, len(self._records), self._kop, self.identiteit.proef_id
        )
        return record

    def _controleer_reserve(self, sleutel: str, details: Mapping[str, Any]) -> str:
        pogingen = [
            r
            for r in self._reserveringen()
            if r["basissleutel"] == sleutel.split("#", 1)[0]
        ]
        if not pogingen:
            msg = f"reserve voor {sleutel!r}: geen eerdere poging"
            raise BudgetSchendingError(msg)
        laatste = pogingen[-1]
        eerste = pogingen[0].get("details") or {}
        for veld, wat in _RESERVE_GELIJK:
            if eerste.get(veld) is not None and details.get(veld) != eerste[veld]:
                msg = (
                    f"reserve voor {sleutel!r}: andere {wat} dan de oorspronkelijke "
                    "poging; een technische herhaling is geen nieuwe inhoudelijke poging"
                )
                raise BudgetSchendingError(msg)
        status = self._afsluitingen().get(laatste["seq"], {}).get("status")
        if status is not None and status not in _RESERVE_TOEGESTAAN_NA:
            msg = (
                f"reserve voor {sleutel!r}: laatste poging eindigde met {status!r}, "
                "geen technische fout"
            )
            raise BudgetSchendingError(msg)
        if sum(1 for r in self._reserveringen() if r["budget_bron"] == "reserve") >= (
            self.identiteit.reserve_max
        ):
            msg = "technische reserve is op"
            raise BudgetSchendingError(msg)
        return f"{laatste['basissleutel']}#technisch-{len(pogingen)}"

    def reserveer(
        self,
        fase: str,
        sleutel: str,
        *,
        invoer_sha256: str,
        binding: Mapping[str, Any] | None = None,
        technische_herhaling: bool = False,
        details: Mapping[str, Any] | None = None,
        poging: str | None = None,
        stap: str | None = None,
        vorige_stap: str | None = None,
    ) -> dict[str, Any]:
        """Reserveer één echte call vóór het netwerk; faalt hard buiten het budget.

        `binding` = de `bindingsvelden` van de identiteit (R1: dataset_sha256,
        herhaal_ids, code_sha256, config_sha256; R2 plus freeze_sha256);
        verplicht en gelijk voor alle reserveringen van één eindgroep.
        Een stap van een meerstapspoging (`poging`, `stap`, `vorige_stap`; sleutel
        `<poging>/<stap>`) volgt de stapregels uit de moduledocstring.
        """
        caps = self.identiteit.fasecaps
        if fase not in caps:
            msg = f"onbekende fase {fase!r} voor {self.identiteit.proef_id}"
            raise BudgetSchendingError(msg)
        if poging is not None or stap is not None:
            self._controleer_stap(
                sleutel, poging, stap, vorige_stap, technische_herhaling
            )
        reserveringen = self._reserveringen()
        totaal_max = self.identiteit.totaal_max
        if len(reserveringen) >= totaal_max:
            msg = f"totaalbudget van {totaal_max} echte calls is op"
            raise BudgetSchendingError(msg)
        vastgelegd = next(
            (r["invoer_sha256"] for r in reserveringen if r["fase"] == fase), None
        )
        if vastgelegd is not None and vastgelegd != invoer_sha256:
            msg = f"fase {fase!r} is met andere invoer begonnen (bevroren invoer)"
            raise BudgetSchendingError(msg)
        binding = self.controleer_binding(fase, invoer_sha256, binding)
        if technische_herhaling:
            definitief = self._controleer_reserve(sleutel, details or {})
            bron = "reserve"
        else:
            if self.gereserveerd(sleutel):
                msg = f"sleutel {sleutel!r} is al gereserveerd (geen tweede ronde)"
                raise BudgetSchendingError(msg)
            gebruikt = sum(
                1
                for r in reserveringen
                if r["fase"] == fase and r["budget_bron"] == "fase"
            )
            if gebruikt >= caps[fase]:
                msg = f"fasecap {fase}={caps[fase]} is bereikt"
                raise BudgetSchendingError(msg)
            definitief = sleutel
            bron = "fase"
        record: dict[str, Any] = {
            "soort": "reservering",
            "seq": len(reserveringen) + 1,
            "fase": fase,
            "sleutel": definitief,
            "basissleutel": sleutel.split("#", 1)[0],
            "budget_bron": bron,
            "invoer_sha256": invoer_sha256,
            "binding": binding,
            "details": dict(details or {}),
        }
        if poging is not None:
            record.update({"poging": poging, "stap": stap})
        return self._voeg_toe(record)

    def _controleer_stap(
        self,
        sleutel: str,
        poging: str | None,
        stap: str | None,
        vorige_stap: str | None,
        technisch: bool,
    ) -> None:
        """Stapregels van een meerstapspoging (zie moduledocstring)."""
        if not poging or not stap or sleutel != f"{poging}/{stap}":
            msg = (
                f"meerstapsreservering {sleutel!r} vereist poging en stap met "
                "sleutel poging/stap"
            )
            raise BudgetSchendingError(msg)
        if technisch:
            msg = (
                f"technische herhaling van meerstapspoging {poging!r} is niet "
                "vastgelegd (een eerdere stap kreeg al een modelantwoord); "
                "vereist een eigen besluit"
            )
            raise BudgetSchendingError(msg)
        reserveringen = self._reserveringen()
        if any(r["sleutel"] in (sleutel, poging) for r in reserveringen):
            msg = (
                f"stap {stap!r} van {poging!r} is al gereserveerd: geen tweede "
                "(semantische) poging"
            )
            raise BudgetSchendingError(msg)
        eerder = [r for r in reserveringen if r.get("poging") == poging]
        laatste = eerder[-1]["stap"] if eerder else None
        if laatste != vorige_stap:
            msg = (
                f"stap {stap!r} van {poging!r} volgt niet op {vorige_stap!r} "
                f"(laatste gereserveerde stap: {laatste!r}); geen stap overslaan"
            )
            raise BudgetSchendingError(msg)

    def controleer_binding(
        self, fase: str, invoer_sha256: str, binding: Mapping[str, Any] | None
    ) -> dict[str, Any] | None:
        """De eindbinding (zie moduledocstring); None buiten de eindgroepen."""
        groep = self.identiteit.eindgroep(fase)
        velden = self.identiteit.bindingsvelden
        if binding is None:
            if groep is not None:
                msg = f"fase {fase!r} vereist een eindbinding ({', '.join(velden)})"
                raise BudgetSchendingError(msg)
            return None
        herhaal_aantal = groep.herhaal_aantal if groep is not None else 4
        vorm = (
            set(binding) == set(velden)
            and binding["dataset_sha256"] == invoer_sha256
            and all(
                isinstance(binding[veld], str)
                and _HEX64.fullmatch(binding[veld]) is not None
                for veld in velden
                if veld not in {"dataset_sha256", "herhaal_ids"}
            )
            and isinstance(binding["herhaal_ids"], list)
            and len(set(binding["herhaal_ids"]))
            == len(binding["herhaal_ids"])
            == herhaal_aantal
        )
        if not vorm:
            msg = f"ongeldige binding voor fase {fase!r} (vorm of datasethash)"
            raise BudgetSchendingError(msg)
        schoon = {
            veld: list(binding[veld]) if veld == "herhaal_ids" else binding[veld]
            for veld in velden
        }
        if groep is not None:
            eerste = next(
                (
                    r.get("binding")
                    for r in self._reserveringen()
                    if r["fase"] in groep.fases
                ),
                None,
            )
            if eerste is not None and eerste != schoon:
                msg = (
                    f"fase {fase!r} wijkt af van de eindbinding van de eerste "
                    "eindreservering (dataset, herhaal_ids, code of effectieve "
                    "configuratie gewijzigd)"
                )
                raise BudgetSchendingError(msg)
        return schoon

    def sluit(
        self,
        seq: int,
        status: str,
        *,
        netwerk_gestart: bool,
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sluit een reservering af; eenmalig, alleen met een bekende status."""
        if status not in AFSLUITSTATUSSEN:
            msg = f"onbekende afsluitstatus {status!r}"
            raise BudgetSchendingError(msg)
        if not any(r["seq"] == seq for r in self._reserveringen()):
            msg = f"onbekende reservering {seq}"
            raise BudgetSchendingError(msg)
        if seq in self._afsluitingen():
            msg = f"reservering {seq} is al afgesloten"
            raise BudgetSchendingError(msg)
        return self._voeg_toe(
            {
                "soort": "afsluiting",
                "seq": seq,
                "status": status,
                "netwerk_gestart": bool(netwerk_gestart),
                "details": dict(details or {}),
            }
        )


def voorgangerketen(identiteit: Proefidentiteit) -> tuple[Proefidentiteit, ...]:
    """Alle voorgangers, nieuwste eerst (R3 → (R2, R1))."""
    keten: list[Proefidentiteit] = []
    vorige = identiteit.voorganger
    while vorige is not None:
        keten.append(vorige)
        vorige = vorige.voorganger
    return tuple(keten)


def controleer_cumulatief(
    eigen: Grootboek,
    voorganger: Grootboek | tuple[Grootboek, ...] | list[Grootboek],
    extra: int,
) -> None:
    """Alle voorgangers + eigen grootboek + `extra` geplande calls ≤ `cumulatief_max`.

    `voorganger` is één grootboek of de volledige keten, nieuwste eerst (R3:
    R2 dan R1). Elke schakel moet exact de voorgangeridentiteit dragen
    (gecontroleerd bij het openen via zijn anker); een ontbrekende of
    verwisselde schakel wordt geweigerd, zodat geen ronde uit de telling valt.
    """
    identiteit = eigen.identiteit
    if identiteit.voorganger is None or identiteit.cumulatief_max is None:
        msg = f"{identiteit.proef_id} heeft geen voorganger met cumulatieve grens"
        raise BudgetSchendingError(msg)
    boeken = (voorganger,) if isinstance(voorganger, Grootboek) else tuple(voorganger)
    verwacht = voorgangerketen(identiteit)
    gekregen = tuple(b.identiteit for b in boeken)
    if len(gekregen) != len(verwacht) or any(
        g is not v for g, v in zip(gekregen, verwacht, strict=True)
    ):
        msg = (
            f"voorgangerketen {[g.proef_id for g in gekregen]} is niet "
            f"{[v.proef_id for v in verwacht]}"
        )
        raise BudgetSchendingError(msg)
    vorig = sum(b.samenvatting()["totaal"] for b in boeken)
    nu = eigen.samenvatting()["totaal"]
    if vorig + nu + extra > identiteit.cumulatief_max:
        herkomst = ", ".join(v.proef_id for v in verwacht)
        msg = (
            f"cumulatief {vorig} ({herkomst}) + {nu} + {extra} "
            f"gepland > {identiteit.cumulatief_max} echte calls (niets gestart)"
        )
        raise BudgetSchendingError(msg)


class Proefslot:
    """Exclusief bestandsslot: nooit twee proefrunners tegelijk."""

    def __init__(self, pad: Path) -> None:
        self._pad = Path(pad)
        self._f: Any = None

    def __enter__(self) -> Proefslot:
        self._pad.parent.mkdir(parents=True, exist_ok=True)
        self._f = self._pad.open("a+")
        try:
            fcntl.flock(self._f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._f.close()
            msg = f"een andere runner houdt het slot {self._pad} vast"
            raise BudgetSchendingError(msg) from exc
        return self

    def __exit__(self, *exc: object) -> None:
        fcntl.flock(self._f.fileno(), fcntl.LOCK_UN)
        self._f.close()


# --- bewaking per reservering ---------------------------------------------------


@dataclass
class Reservering:
    """De runtime-staat van één gereserveerde call."""

    seq: int
    sleutel: str
    client_aanroepen: int = 0
    sdk_aanroepen: int = 0
    netwerk_gestart: bool = False
    antwoord: dict[str, Any] = field(default_factory=dict)
    sdk: dict[str, Any] = field(default_factory=dict)
    fout: str | None = None
    #: Een weigering door de bewaking (ADR-003). Blijft zichtbaar, ook als een
    #: hogere laag de `BudgetSchendingError` inpakt in een eigen fouttype.
    schending: str | None = None


def _weiger(reservering: Reservering, msg: str) -> BudgetSchendingError:
    reservering.schending = msg
    return BudgetSchendingError(msg)


_ACTIEF: contextvars.ContextVar[Reservering | None] = contextvars.ContextVar(
    "def768_ess05_reservering", default=None
)


@contextlib.contextmanager
def actief(reservering: Reservering) -> Iterator[Reservering]:
    """Maak `reservering` de enige toegestane aanroep binnen dit blok."""
    token = _ACTIEF.set(reservering)
    try:
        yield reservering
    finally:
        _ACTIEF.reset(token)


def _vereis_reservering(laag: str) -> Reservering:
    reservering = _ACTIEF.get()
    if reservering is None:
        msg = f"{laag}-aanroep zonder reservering geweigerd"
        raise BudgetSchendingError(msg)
    return reservering


class Stappenpoging:
    """Eén geval met meerdere modelstappen, elk met een eigen reservering.

    `stappen` = de vaste volgorde `(task_type, stapnaam)`. `stap(task_type,
    prompt_sha256)` reserveert pas bij de werkelijke aanroep (nooit vooraf) en
    maakt die reservering de enige toegestane aanroep binnen het blok. Een
    weigering (volgorde, budget, binding) blijft in `schending` zichtbaar, ook
    als een hogere laag de `BudgetSchendingError` inpakt. Afsluiten doet de
    aanroeper, per gemaakte reservering (`gereserveerd`).
    """

    def __init__(
        self,
        boek: Grootboek,
        *,
        fase: str,
        poging: str,
        stappen: tuple[tuple[str, str], ...],
        invoer_sha256: str,
        binding: Mapping[str, Any] | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self._boek = boek
        self._fase = fase
        self.poging = poging
        self._stappen = tuple(stappen)
        self._invoer_sha256 = invoer_sha256
        self._binding = binding
        self._details = dict(details or {})
        #: (stapnaam, grootboekrecord, runtime-reservering), in aanroepvolgorde.
        self.gereserveerd: list[tuple[str, dict[str, Any], Reservering]] = []
        self._weigering: str | None = None

    @property
    def schending(self) -> str | None:
        """De eerste bewakingsweigering in deze poging, of None."""
        if self._weigering is not None:
            return self._weigering
        return next((r.schending for _, _, r in self.gereserveerd if r.schending), None)

    @contextlib.contextmanager
    def stap(self, task_type: str, prompt_sha256: str) -> Iterator[Reservering]:
        index = len(self.gereserveerd)
        if index >= len(self._stappen) or self._stappen[index][0] != task_type:
            volgorde = [t for t, _ in self._stappen]
            self._weigering = (
                f"modelstap {task_type!r} buiten de vaste volgorde {volgorde} van "
                f"{self.poging!r} (al {index} gereserveerd)"
            )
            raise BudgetSchendingError(self._weigering)
        naam = self._stappen[index][1]
        try:
            res = self._boek.reserveer(
                self._fase,
                f"{self.poging}/{naam}",
                invoer_sha256=self._invoer_sha256,
                binding=self._binding,
                details={**self._details, "stap_prompt_sha256": prompt_sha256},
                poging=self.poging,
                stap=naam,
                vorige_stap=self._stappen[index - 1][1] if index else None,
            )
        except BudgetSchendingError as exc:
            self._weigering = str(exc)
            raise
        reservering = Reservering(seq=res["seq"], sleutel=res["sleutel"])
        self.gereserveerd.append((naam, res, reservering))
        with actief(reservering):
            yield reservering


class BewaakteClient:
    """AsyncAIClient-proxy: één aanroep per reservering, SDK-retries expliciet 0."""

    def __init__(self, echt: Any) -> None:
        self._echt = echt

    def __getattr__(self, naam: str) -> Any:
        return getattr(self._echt, naam)

    async def chat_completion(self, messages: Any, model: str, **kwargs: Any) -> Any:
        reservering = _vereis_reservering("client")
        if kwargs.get("max_retries") != 0:
            msg = f"max_retries moet 0 zijn, kreeg {kwargs.get('max_retries')!r}"
            raise _weiger(reservering, msg)
        if reservering.client_aanroepen >= 1:
            msg = f"tweede clientaanroep binnen reservering {reservering.seq} geweigerd"
            raise _weiger(reservering, msg)
        reservering.client_aanroepen += 1
        try:
            antwoord = await self._echt.chat_completion(messages, model, **kwargs)
        except Exception as exc:
            reservering.fout = scrub(f"{type(exc).__name__}: {exc}")
            raise
        reservering.antwoord = {
            "text": getattr(antwoord, "text", None),
            "model": getattr(antwoord, "model", None),
            "tokens_used_provider_som": getattr(antwoord, "tokens_used", None),
            "stop_reason": getattr(antwoord, "stop_reason", None),
        }
        return antwoord


def _sdk_metadata(resp: Any) -> dict[str, Any]:
    usage = getattr(resp, "usage", None)
    meta: dict[str, Any] = {
        "id": getattr(resp, "id", None),
        "model": getattr(resp, "model", None),
        "stop_reason": getattr(resp, "stop_reason", None),
    }
    if usage is not None:
        meta["usage"] = {
            naam: getattr(usage, naam)
            for naam in ("input_tokens", "output_tokens")
            if isinstance(getattr(usage, naam, None), int)
        }
    return meta


def installeer_sdk_wacht(klasse: Any) -> Any:
    """Bewaak `klasse.create` (bv. `anthropic...AsyncMessages`) op klasseniveau.

    Klasseniveau, omdat de client per aanroep `with_options(...)` en per
    eventloop een verse SDK-client gebruikt. Vóór het netwerk: reservering
    actief, nog geen SDK-aanroep in deze reservering, en `max_retries == 0` op
    de SDK-client die de aanroep doet. Geeft een herstelfunctie terug.
    """
    origineel = klasse.create

    async def create(self: Any, *args: Any, **kwargs: Any) -> Any:
        reservering = _vereis_reservering("SDK")
        retries = getattr(getattr(self, "_client", None), "max_retries", None)
        if retries != 0:
            msg = f"SDK-client met max_retries={retries!r} geweigerd (moet 0 zijn)"
            raise _weiger(reservering, msg)
        if reservering.sdk_aanroepen >= 1:
            msg = f"tweede SDK-aanroep binnen reservering {reservering.seq} geweigerd"
            raise _weiger(reservering, msg)
        reservering.sdk_aanroepen += 1
        reservering.netwerk_gestart = True
        resp = await origineel(self, *args, **kwargs)
        reservering.sdk = _sdk_metadata(resp)
        return resp

    klasse.create = create

    def herstel() -> None:
        klasse.create = origineel

    return herstel


def kosten(
    sdk: Mapping[str, Any], prijs: Mapping[str, float], *, prijs_bekend: bool
) -> dict[str, Any]:
    """Kosten uit werkelijke SDK-usage × routertarief, of onbekend met reden."""
    usage = sdk.get("usage") or {}
    invoer, uitvoer = usage.get("input_tokens"), usage.get("output_tokens")
    if not isinstance(invoer, int) or not isinstance(uitvoer, int):
        return {"usd": None, "reden": "geen werkelijke usage uit de SDK-respons"}
    if not prijs_bekend:
        return {
            "usd": None,
            "reden": "model staat niet in de pricing-config; terugvaltarief niet gebruikt",
            "input_tokens": invoer,
            "output_tokens": uitvoer,
        }
    return {
        "usd": round(invoer * prijs["input"] + uitvoer * prijs["output"], 6),
        "bron": "sdk_usage×router_pricing",
        "input_tokens": invoer,
        "output_tokens": uitvoer,
        "tarief_per_token": {"input": prijs["input"], "output": prijs["output"]},
    }


def schrijf_nieuw(pad: Path, data: Any, *, geheimen: tuple[str, ...]) -> str:
    """Schrijf JSON naar een nieuw bestand (nooit overschrijven); geef sha256.

    Alles wat op een sleutel lijkt wordt vervangen; een bekend geheim dat dan
    nog in de tekst staat is een harde fout en er wordt niets geschreven.
    """
    tekst = scrub(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    if any(g and g in tekst for g in geheimen):
        msg = f"geheim in uitvoer voor {pad.name}; niets geschreven"
        raise BudgetSchendingError(msg)
    pad.parent.mkdir(parents=True, exist_ok=True)
    with pad.open("x", encoding="utf-8") as f:
        f.write(tekst + "\n")
    return _sha((tekst + "\n").encode("utf-8"))
