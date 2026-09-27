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

`R8` (DEF-768-AI-20260925-R8, ADR-003-keten; livevervolg-proefvoorstel-
technisch-v1 §3/§6 met de leidende rootcorrecties) telt modelstappen, geen
gevallen: 6 ontwikkeling (3 gevallen × 2), 6 verifier-only, 40 T-eind (20 ×
2) en 16 T-herhaling (8 × 2), reserve 0; samen met R7 t/m R1 nooit boven 427.
Daarbovenop, alleen voor R8:

- **kostenbewaking** (`Kostenbewaking`) — elke stap reserveert vóór het
  netwerk een kostengrens uit een vaste bytegrens per taak, een expliciete
  overheadmarge en `max_tokens`; de lopende som (werkelijke kosten waar de
  usage bekend is, anders de grens: crash, timeout) plus de nieuwe grens mag
  het routerbudget niet overschrijden. Dit is een begrenzing onder expliciete
  aannames (tokens ≤ payloadbytes + overhead, routertarief), geen
  factuurplafond;
- **vaste taak per stap** (`fasestappen`) en **fasevolgorde** — een fase
  begint pas als elk geval van haar voorganger geaccepteerd is;
- **stopregel** — één niet-geaccepteerd geval (`registreer_geval`) stopt de
  proef duurzaam; geen verborgen herhaling of extra ronde;
- **gedeelde codebinding** — V en T delen code en configuratie; elke eindgroep heeft een eigen freeze.

`R9` (DEF-768-AI-20260926-R9, gerichte herproef na het R8-offsetherstel;
besluit Chris 26-09, `logs/def768/ronde9-herproefgoedkeuring-v1.json`) volgt
dezelfde regels als R8 met 2 ontwikkeling (alleen R720 × 2), 6 verifier-only,
40 T-eind en 16 T-herhaling, reserve 0; samen met R8 t/m R1 nooit boven 424
(360 werkelijke + 64). Het routerplafond is USD 24,901265; het
**kostenkader** (`kostenkader_nusd`, USD 25) begrenst de lopende kosten van
de voorgangers onder kostenbewaking (R8, uit zijn grootboek) plus dit plafond
(`controleer_cumulatief`), zodat R8 en R9 samen binnen het oorspronkelijke
budget blijven.

`R10` (DEF-768-AI-20260926-R10, gerichte proef na het R9-bewijsherstel;
besluit Chris 26-09, `logs/def768/ronde10-herproefgoedkeuring-v1.json`) volgt
dezelfde regels met 2 ontwikkeling (alleen R720 × 2), 7 verifier-only, 40
T-eind en 16 T-herhaling, reserve 0; samen met R9 t/m R1 nooit boven 427
(362 werkelijke + 65). Het routerplafond is USD 24,722355; het kostenkader
(USD 25) telt de lopende kosten van R8 én R9 uit hun grootboeken mee.

`R11` (DEF-768-AI-20260926-R11, gerichte proef na het R10-C3-herstel; besluit
Chris 26-09, `logs/def768/ronde11-herproefgoedkeuring-v1.json`) volgt dezelfde
regels met 2 ontwikkeling (alleen R720 × 2), 8 verifier-only, 40 T-eind en 16
T-herhaling, reserve 0; samen met R10 t/m R1 nooit boven 430 (364 werkelijke +
66). Dat is 3 boven het oorspronkelijke kader van 427; die verruiming is
uitsluitend aan het gepinde R11-besluit gebonden (runner). Het routerplafond is
USD 24,529390; het kostenkader (USD 25) telt de lopende kosten van R8, R9 én
R10 uit hun grootboeken mee.

`R12` (DEF-768-AI-20260926-R12, kleine beslissende praktijkvergelijking;
besluit Chris 26-09, `logs/def768/answer2-microproef-goedkeuring-v1.json`)
volgt dezelfde regels met maximaal 4 modelstappen in omgekeerde fasevolgorde:
eerst 2 verifier-only (R9-C5, dan R10-C3), pas daarna 2 ontwikkeling (alleen
R720: beoordeling + verificatie); geen T-eind of T-herhaling, reserve 0,
stop bij de eerste fout; samen met R11 t/m R1 nooit boven 369 (365 werkelijke
+ 4). Het lokale routerplafond is USD 1,44, de volledige stapbegroting van
precies deze vier stappen; het kostenkader (USD 25) telt de lopende kosten van
R8 t/m R11 uit hun grootboeken mee.

`R13` (DEF-768-AI-20260926-R13, vijf herkenbare gevallen; besluit Chris 26-09,
"Go", `logs/def768/herkenbare-gevallen-goedkeuring-v1.json`) kent alleen
ontwikkeling: 5 onafhankelijke gevallen × 2 stappen = 10, reserve 0; samen met
R12 t/m R1 nooit boven 376 (366 werkelijke + 10); lokaal plafond USD 3,45.
Onder `stop_alleen_technisch` draagt elk geval naast `geaccepteerd`
(inhoudelijk) ook `technisch_afgerond`; alleen een technisch niet-afgerond
geval of een open poging stopt de proef.

`R14` (DEF-768-AI-20260927-R14, herproef na het R13-herstel; opdracht Chris
27-09, `logs/def768/r13-herstel-gebruikersopdracht-v1.json`) volgt dezelfde
regels als R13 met twee onafhankelijke fases: 2 verifier-only (twee gerichte
negatieven) en 10 ontwikkeling (H1–H5 × 2), geen fasevolgorde, reserve 0;
samen met R13 t/m R1 nooit boven 388 (376 werkelijke + 12); lokaal plafond USD
4,20 (de volledige stapbegroting). Ook de V-stap draagt `technisch_afgerond`:
een inhoudelijk gemiste negatief stopt de vijf gevallen niet.

`R15` (DEF-768-AI-20260928-R15, fase A bewijsisolatie; opdracht Chris 27-09,
`logs/def768/isolatie-gebruikersopdracht-v1.json`) kent alleen
`lokale_verificatie`: precies 4 lokale controles van elk één modelstap
(verificatietaak), reserve 0; samen met R14 t/m R1 nooit boven 391 (387
werkelijke + 4); lokaal plafond USD 1,50 (de volledige stapbegroting). Zoals
R13/R14 stopt alleen een technisch niet-afgeronde controle of een open poging.

De SDK-wacht laat onder een stapgrens alleen platte-tekstpayload door (model,
`max_tokens`, thinking uit, tekst-`system`, tekstberichten; geen tools,
caching of blokken) binnen de bytegrens, en toetst achteraf de usage aan de
aangenomen grens (schending = stop).
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
from dataclasses import dataclass, field, replace
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
    "R8",
    "R9",
    "R10",
    "R11",
    "R12",
    "R13",
    "R14",
    "R15",
    "RESERVE_MAX",
    "TOTAAL_MAX",
    "BewaakteClient",
    "BudgetSchendingError",
    "Eindgroep",
    "Grootboek",
    "Kostenbewaking",
    "Proefidentiteit",
    "Proefslot",
    "Reservering",
    "Stapgrens",
    "Stappenpoging",
    "actief",
    "ankerpad",
    "begroting_nusd",
    "controleer_cumulatief",
    "installeer_sdk_wacht",
    "kosten",
    "kosten_nusd",
    "payloadbytes",
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
class Stapgrens:
    """De toegelaten payload en kostengrens van één modelstap (R8)."""

    task_type: str
    model: str
    max_tokens: int
    #: Compacte UTF-8-JSON-bytes van de verzonden body (zonder `timeout`).
    bytegrens: int
    #: Aangenomen providertokens bovenop de payloadbytes (opmaak, rollen).
    overhead_tokens: int


@dataclass(frozen=True)
class Kostenbewaking:
    """Fail-closed routerbudget in nanodollars (1 USD = 10⁹ n$), zonder floats.

    Stapgrens = (bytegrens + overhead_tokens) × invoertarief + max_tokens ×
    uitvoertarief. Aanname: een providertoken dekt minstens één payloadbyte;
    overhead_tokens is een expliciete marge, geen bewezen providergrens. De
    SDK-wacht toetst die aanname achteraf per stap (schending = stop).
    """

    plafond_nusd: int
    model: str
    tarief_invoer_nusd: int
    tarief_uitvoer_nusd: int
    max_tokens: int
    overhead_tokens: int
    bytegrens: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "bytegrens", MappingProxyType(dict(self.bytegrens)))

    def stapgrens(self, task_type: str) -> Stapgrens:
        if task_type not in self.bytegrens:
            msg = f"onbekende taak {task_type!r} voor de kostenbewaking"
            raise BudgetSchendingError(msg)
        return Stapgrens(
            task_type=task_type,
            model=self.model,
            max_tokens=self.max_tokens,
            bytegrens=self.bytegrens[task_type],
            overhead_tokens=self.overhead_tokens,
        )

    def stapgrens_nusd(self, task_type: str) -> int:
        grens = self.stapgrens(task_type)
        return (
            grens.bytegrens + grens.overhead_tokens
        ) * self.tarief_invoer_nusd + grens.max_tokens * self.tarief_uitvoer_nusd

    def als_dict(self) -> dict[str, Any]:
        return {
            "plafond_nusd": self.plafond_nusd,
            "model": self.model,
            "tarief_invoer_nusd": self.tarief_invoer_nusd,
            "tarief_uitvoer_nusd": self.tarief_uitvoer_nusd,
            "max_tokens": self.max_tokens,
            "overhead_tokens": self.overhead_tokens,
            "bytegrens": dict(self.bytegrens),
            "stapgrens_nusd": {t: self.stapgrens_nusd(t) for t in self.bytegrens},
        }


@dataclass(frozen=True)
class Proefidentiteit:
    """Een vaste proef: id, fasecaps, reserve en eindgroepen.

    Alleen `R1` t/m `R15` hieronder bestaan; een andere identiteit wordt bij
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
    #: R8: kostenplafond en stapgrenzen; None = geen kostenbewaking (R1–R7).
    kostenbewaking: Kostenbewaking | None = None
    #: R8: de vaste taak per stap, per fase (fasecaps tellen stappen).
    fasestappen: Mapping[str, tuple[str, ...]] | None = None
    #: R8: fases die volledig geaccepteerd moeten zijn vóór deze fase begint.
    fasevolgorde: Mapping[str, tuple[str, ...]] | None = None
    #: R8: alle eindgroepen delen code en configuratie (freeze per groep).
    gedeelde_codebinding: bool = False
    #: R8: één niet-geaccepteerd geval stopt de proef duurzaam.
    stop_bij_eerste_fout: bool = False
    #: R9: gezamenlijk routerbudget (nUSD) met de voorgangers onder
    #: kostenbewaking: hun lopende kosten plus het eigen plafond; None = geen.
    kostenkader_nusd: int | None = None
    #: R13: de stopregel telt alleen een technisch niet-afgerond geval (plus
    #: een open poging); een inhoudelijk niet-geaccepteerd geval stopt niet.
    stop_alleen_technisch: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fasecaps", MappingProxyType(dict(self.fasecaps)))
        for veld in ("fasestappen", "fasevolgorde"):
            waarde = getattr(self, veld)
            if waarde is not None:
                object.__setattr__(self, veld, MappingProxyType(dict(waarde)))

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
_BEOORDELING, _VERIFICATIE = "validation", "ess05_verification"
#: Ronde 8 (voorbereid, budget nog niet goedgekeurd; ADR-003-keten): 68
#: modelstappen — 6 ontwikkeling (R720, R715, R717 × 2), 6 verifier-only (de
#: zes migratiegevallen), 40 T-eind (20 × 2) en 16 T-herhaling (8 × 2),
#: reserve 0; samen met R7 t/m R1 nooit boven 427 (359 werkelijke + 68).
#: Kosten: productiegrens 3000 uitvoertokens per stap, routertarief
#: claude-opus-5 ($5/$25 per 1M tokens), bytegrens per taak en 12000
#: overheadtokens; volledige begroting 23,64 ≤ 25 USD (`begroting_nusd`).
R8 = Proefidentiteit(
    proef_id="DEF-768-AI-20260925-R8",
    fasecaps={
        "ontwikkeling": 6,
        "verificatie_alleen": 6,
        "t_eind": 40,
        "t_herhaling": 16,
    },
    reserve_max=0,
    eindgroepen=(
        Eindgroep("t", frozenset({"t_eind", "t_herhaling"}), 4),
        Eindgroep("v", frozenset({"verificatie_alleen"}), 0),
    ),
    bindingsvelden=R7.bindingsvelden,
    voorganger=R7,
    cumulatief_max=427,
    modelstappen_per_geval=2,
    kostenbewaking=Kostenbewaking(
        plafond_nusd=25_000_000_000,
        model="claude-opus-5",
        tarief_invoer_nusd=5_000,
        tarief_uitvoer_nusd=25_000,
        max_tokens=3000,
        overhead_tokens=12_000,
        bytegrens={_BEOORDELING: 36_000, _VERIFICATIE: 48_000},
    ),
    fasestappen={
        "ontwikkeling": (_BEOORDELING, _VERIFICATIE),
        "verificatie_alleen": (_VERIFICATIE,),
        "t_eind": (_BEOORDELING, _VERIFICATIE),
        "t_herhaling": (_BEOORDELING, _VERIFICATIE),
    },
    fasevolgorde={
        "ontwikkeling": (),
        "verificatie_alleen": ("ontwikkeling",),
        "t_eind": ("verificatie_alleen",),
        "t_herhaling": ("t_eind",),
    },
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
)
#: Ronde 9 (besluit Chris 26-09, "Ja" op offsetherstel-vervolgproef-voorstel-
#: v1): gerichte herproef na het R8-offsetherstel, max 64 modelstappen — 2
#: ontwikkeling (alleen R720 × 2), 6 verifier-only, 40 T-eind (20 × 2) en 16
#: T-herhaling (8 × 2), reserve 0; samen met R8 t/m R1 nooit boven 424 (360
#: werkelijke + 64). Zelfde model, tarief, bytegrenzen en productiegrens als
#: R8; plafond USD 24,901265 = kader USD 25 − werkelijke R8-kosten 0,098735.
#: Begroting 22,26 USD (`begroting_nusd`).
R9 = Proefidentiteit(
    proef_id="DEF-768-AI-20260926-R9",
    fasecaps={
        "ontwikkeling": 2,
        "verificatie_alleen": 6,
        "t_eind": 40,
        "t_herhaling": 16,
    },
    reserve_max=0,
    eindgroepen=R8.eindgroepen,
    bindingsvelden=R8.bindingsvelden,
    voorganger=R8,
    cumulatief_max=424,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=24_901_265_000),
    fasestappen=R8.fasestappen,
    fasevolgorde=R8.fasevolgorde,
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
)
#: Ronde 10 (besluit Chris 26-09, "ja" op bewijsherstel-vervolgproef-voorstel-
#: v1): gerichte proef na het R9-bewijsherstel, max 65 modelstappen — 2
#: ontwikkeling (alleen R720 × 2), 7 verifier-only (de zes R8-controles plus
#: het ongewijzigde R9-C5-concept), 40 T-eind (20 × 2) en 16 T-herhaling
#: (8 × 2), reserve 0; samen met R9 t/m R1 nooit boven 427 (362 werkelijke +
#: 65). Zelfde model, tarief, bytegrenzen en productiegrens als R8; plafond
#: USD 24,722355 = kader USD 25 − werkelijke R8- (0,098735) en R9-kosten
#: (0,178910). Begroting 22,635 USD (`begroting_nusd`).
R10 = Proefidentiteit(
    proef_id="DEF-768-AI-20260926-R10",
    fasecaps={
        "ontwikkeling": 2,
        "verificatie_alleen": 7,
        "t_eind": 40,
        "t_herhaling": 16,
    },
    reserve_max=0,
    eindgroepen=R9.eindgroepen,
    bindingsvelden=R9.bindingsvelden,
    voorganger=R9,
    cumulatief_max=427,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=24_722_355_000),
    fasestappen=R9.fasestappen,
    fasevolgorde=R9.fasevolgorde,
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
)
#: Ronde 11 (besluit Chris 26-09, "akkoord" op c3-herstel-vervolgproef-
#: voorstel-v1): gerichte proef na het R10-C3-herstel, max 66 modelstappen — 2
#: ontwikkeling (alleen R720 × 2), 8 verifier-only (V7 plus het ongewijzigde
#: R10-C3-concept), 40 T-eind (20 × 2) en 16 T-herhaling (8 × 2), reserve 0;
#: samen met R10 t/m R1 nooit boven 430 (364 werkelijke + 66), expliciet 3
#: boven het oorspronkelijke 427. Zelfde model, tarief, bytegrenzen en
#: productiegrens als R8; plafond USD 24,529390 = kader USD 25 − werkelijke
#: R8- (0,098735), R9- (0,178910) en R10-kosten (0,192965). Begroting
#: 23,010 USD (`begroting_nusd`).
R11 = Proefidentiteit(
    proef_id="DEF-768-AI-20260926-R11",
    fasecaps={
        "ontwikkeling": 2,
        "verificatie_alleen": 8,
        "t_eind": 40,
        "t_herhaling": 16,
    },
    reserve_max=0,
    eindgroepen=R10.eindgroepen,
    bindingsvelden=R10.bindingsvelden,
    voorganger=R10,
    cumulatief_max=430,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=24_529_390_000),
    fasestappen=R10.fasestappen,
    fasevolgorde=R10.fasevolgorde,
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
)
#: Ronde 12 (besluit Chris 26-09, "Ja akkoord" op een kleine beslissende
#: praktijkvergelijking, answer2-microproef-goedkeuring-v1.json): max 4
#: modelstappen — eerst 2 verifier-only (R9-C5, dan R10-C3, de oorspronkelijke
#: concepten uit V8), pas daarna 2 ontwikkeling (alleen R720 × 2); geen T-eind
#: of T-herhaling, reserve 0, stop bij de eerste fout; samen met R11 t/m R1
#: nooit boven 369 (365 werkelijke + 4). Zelfde model, tarief, bytegrenzen en
#: productiegrens als R8. Lokaal plafond USD 1,44 = de volledige stapbegroting
#: van precies deze vier stappen (2 × 0,375 + 0,315 + 0,375; `begroting_nusd`),
#: binnen de kaderrest USD 24,427230 (USD 25 − werkelijke R8–R11-kosten).
R12 = Proefidentiteit(
    proef_id="DEF-768-AI-20260926-R12",
    fasecaps={"verificatie_alleen": 2, "ontwikkeling": 2},
    reserve_max=0,
    # R12-01: ook R720 is een eindgroep (eigen freeze en dataset), zodat de
    # gedeelde codebinding haar code en configuratie aan die van V bindt.
    eindgroepen=(
        Eindgroep("v", frozenset({"verificatie_alleen"}), 0),
        Eindgroep("o", frozenset({"ontwikkeling"}), 0),
    ),
    bindingsvelden=R11.bindingsvelden,
    voorganger=R11,
    cumulatief_max=369,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=1_440_000_000),
    fasestappen={
        "verificatie_alleen": (_VERIFICATIE,),
        "ontwikkeling": (_BEOORDELING, _VERIFICATIE),
    },
    fasevolgorde={"verificatie_alleen": (), "ontwikkeling": ("verificatie_alleen",)},
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
)
#: Ronde 13 (besluit Chris 26-09, "Go" op vijf herkenbare gevallen,
#: herkenbare-gevallen-goedkeuring-v1.json): max 10 modelstappen — 5
#: onafhankelijke ontwikkelgevallen × (beoordeling + verificatie), reserve 0;
#: samen met R12 t/m R1 nooit boven 376 (366 werkelijke + 10). Zelfde model,
#: tarief, bytegrenzen en productiegrens als R8. Lokaal plafond USD 3,45 = de
#: volledige stapbegroting (5 × 0,69), onder de harde grens USD 4 en binnen de
#: kaderrest USD 24,324085. Vijf onafhankelijke gevallen: een inhoudelijke
#: mismatch of appafkeuring stopt de reeks niet, een technische fout, een
#: bewakingsweigering of een open poging wel (`stop_alleen_technisch`).
R13 = Proefidentiteit(
    proef_id="DEF-768-AI-20260926-R13",
    fasecaps={"ontwikkeling": 10},
    reserve_max=0,
    eindgroepen=(Eindgroep("o", frozenset({"ontwikkeling"}), 0),),
    bindingsvelden=R12.bindingsvelden,
    voorganger=R12,
    cumulatief_max=376,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=3_450_000_000),
    fasestappen={"ontwikkeling": (_BEOORDELING, _VERIFICATIE)},
    fasevolgorde={"ontwikkeling": ()},
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
    stop_alleen_technisch=True,
)
#: Ronde 14 (opdracht Chris 27-09, "Ok kun je het nu wel fixen?",
#: r13-herstel-gebruikersopdracht-v1.json): herproef na het R13-herstel. Max 12
#: modelstappen in twee onafhankelijke fases: 2 verifier-only (de twee gerichte
#: negatieven) en 10 ontwikkeling (H1–H5 × beoordeling + verificatie); geen
#: fasevolgorde, reserve 0; samen met R13 t/m R1 nooit boven 388 (376
#: werkelijke + 12). Zelfde model, tarief, bytegrenzen en productiegrens als R8.
#: Lokaal plafond USD 4,20 = de volledige stapbegroting (2 × 0,375 + 5 × 0,69),
#: onder de grens USD 5 en binnen de kaderrest USD 23,330410. Zoals R13 stopt
#: alleen een technisch niet-afgerond geval of een open poging.
R14 = Proefidentiteit(
    proef_id="DEF-768-AI-20260927-R14",
    fasecaps={"verificatie_alleen": 2, "ontwikkeling": 10},
    reserve_max=0,
    eindgroepen=(
        Eindgroep("v", frozenset({"verificatie_alleen"}), 0),
        Eindgroep("o", frozenset({"ontwikkeling"}), 0),
    ),
    bindingsvelden=R13.bindingsvelden,
    voorganger=R13,
    cumulatief_max=388,
    modelstappen_per_geval=2,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=4_200_000_000),
    fasestappen={
        "verificatie_alleen": (_VERIFICATIE,),
        "ontwikkeling": (_BEOORDELING, _VERIFICATIE),
    },
    fasevolgorde={"verificatie_alleen": (), "ontwikkeling": ()},
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
    stop_alleen_technisch=True,
)
#: Ronde 15 (opdracht Chris 27-09, "Akkoord om het zo op te pakken",
#: isolatie-gebruikersopdracht-v1.json): fase A van de bewijsisolatie. Precies
#: 4 lokale controles (2 negatief, 2 positief), elk één afzonderlijke
#: verificatieaanroep; geen generatie of globale controle, reserve 0; samen met
#: R14 t/m R1 nooit boven 391 (387 werkelijke + 4). Zelfde model, tarief,
#: bytegrenzen en productiegrens als R8. Lokaal plafond USD 1,50 = de volledige
#: stapbegroting (4 × 0,375), binnen de kaderrest USD 22,229960. Elke controle
#: loopt eenmaal ongeacht haar uitkomst; alleen een technisch niet-afgeronde
#: controle of een open poging stopt.
R15 = Proefidentiteit(
    proef_id="DEF-768-AI-20260928-R15",
    fasecaps={"lokale_verificatie": 4},
    reserve_max=0,
    eindgroepen=(Eindgroep("l", frozenset({"lokale_verificatie"}), 0),),
    bindingsvelden=R14.bindingsvelden,
    voorganger=R14,
    cumulatief_max=391,
    modelstappen_per_geval=1,
    kostenbewaking=replace(R8.kostenbewaking, plafond_nusd=1_500_000_000),
    fasestappen={"lokale_verificatie": (_VERIFICATIE,)},
    fasevolgorde={"lokale_verificatie": ()},
    gedeelde_codebinding=True,
    stop_bij_eerste_fout=True,
    kostenkader_nusd=25_000_000_000,
    stop_alleen_technisch=True,
)
_IDENTITEITEN = {
    i.proef_id: i
    for i in (R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15)
}
#: Velden die alle eindgroepen delen bij `gedeelde_codebinding`. De freeze is
#: per eindgroep (`groep` v of t in `freezevelden`) en dus bewust niet gedeeld.
_GEDEELDE_BINDING = ("code_sha256", "config_sha256")


def begroting_nusd(identiteit: Proefidentiteit) -> int:
    """De volledige stapbegroting: elke fasecap gevuld met de maximale stapgrens."""
    kb, stappen = identiteit.kostenbewaking, identiteit.fasestappen
    if kb is None or stappen is None:
        msg = f"{identiteit.proef_id} heeft geen kostenbewaking"
        raise BudgetSchendingError(msg)
    totaal = 0
    for fase, cap in identiteit.fasecaps.items():
        gevallen, rest = divmod(cap, len(stappen[fase]))
        if rest:
            msg = f"fasecap {fase}={cap} is geen veelvoud van de stappen per geval"
            raise BudgetSchendingError(msg)
        totaal += gevallen * sum(kb.stapgrens_nusd(t) for t in stappen[fase])
    return totaal


def _bekende_identiteit(identiteit: Proefidentiteit) -> Proefidentiteit:
    if _IDENTITEITEN.get(identiteit.proef_id) is not identiteit:
        msg = f"onbekende proefidentiteit {identiteit.proef_id!r}; alleen R1 t/m R15"
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

    def _gevallen(self) -> list[dict[str, Any]]:
        return [r for r in self._records if r["soort"] == "geval"]

    def kostenstand(self) -> dict[str, int]:
        """Lopende kosten: werkelijk waar de usage bekend is, anders de grens.

        Een onafgesloten reservering (crash) en een afsluiting zonder werkelijke
        kosten (timeout, geen usage) tellen met hun volledige stapgrens.
        """
        kb = self.identiteit.kostenbewaking
        if kb is None:
            msg = f"{self.identiteit.proef_id} heeft geen kostenbewaking"
            raise BudgetSchendingError(msg)
        afgesloten = self._afsluitingen()
        gereserveerd = werkelijk = lopend = 0
        for r in self._reserveringen():
            grens = r["kosten_grens_nusd"]
            echt = afgesloten.get(r["seq"], {}).get("kosten_werkelijk_nusd")
            gereserveerd += grens
            werkelijk += echt or 0
            lopend += grens if echt is None else echt
        return {
            "plafond_nusd": kb.plafond_nusd,
            "gereserveerd_nusd": gereserveerd,
            "werkelijk_bekend_nusd": werkelijk,
            "lopend_nusd": lopend,
            "resterend_nusd": kb.plafond_nusd - lopend,
        }

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
        extra: dict[str, Any] = {}
        if self.identiteit.kostenbewaking is not None:
            gevallen: dict[str, dict[str, int]] = {}
            for g in self._gevallen():
                teller = gevallen.setdefault(
                    g["fase"], {"geaccepteerd": 0, "geweigerd": 0}
                )
                teller["geaccepteerd" if g["geaccepteerd"] else "geweigerd"] += 1
            extra = {
                "kosten": self.kostenstand(),
                "gevallen": gevallen,
                "gestopt": self._stopgeval() is not None,
            }
        return {
            **extra,
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
        task_type: str | None = None,
    ) -> dict[str, Any]:
        """Reserveer één echte call vóór het netwerk; faalt hard buiten het budget.

        `binding` = de `bindingsvelden` van de identiteit (R1: dataset_sha256,
        herhaal_ids, code_sha256, config_sha256; R2 plus freeze_sha256);
        verplicht en gelijk voor alle reserveringen van één eindgroep.
        Een stap van een meerstapspoging (`poging`, `stap`, `vorige_stap`; sleutel
        `<poging>/<stap>`) volgt de stapregels uit de moduledocstring.
        Onder kostenbewaking (R8) is elke reservering een stap met `task_type`
        en gelden stopregel, fasevolgorde, vaste taak en kostenplafond.
        """
        caps = self.identiteit.fasecaps
        if fase not in caps:
            msg = f"onbekende fase {fase!r} voor {self.identiteit.proef_id}"
            raise BudgetSchendingError(msg)
        kosten_grens: int | None = None
        if self.identiteit.kostenbewaking is not None:
            kosten_grens = self._controleer_kosten_en_volgorde(fase, poging, task_type)
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
        if kosten_grens is not None:
            record.update({"task_type": task_type, "kosten_grens_nusd": kosten_grens})
        return self._voeg_toe(record)

    def _open_poging(self, behalve: str | None) -> str | None:
        """Een gestarte poging zonder duurzame gevaluitkomst (crash, onderbreking)."""
        geregistreerd = {g["poging"] for g in self._gevallen()}
        return next(
            (
                r["poging"]
                for r in self._reserveringen()
                if r.get("poging") not in (None, behalve, *geregistreerd)
            ),
            None,
        )

    def _stopgeval(self) -> dict[str, Any] | None:
        """Het eerste geval dat de proef stopt: niet geaccepteerd, of onder
        `stop_alleen_technisch` (R13) alleen een technisch niet-afgerond geval."""
        if self.identiteit.stop_alleen_technisch:
            return next(
                (
                    g
                    for g in self._gevallen()
                    if g.get("technisch_afgerond") is not True
                ),
                None,
            )
        return next((g for g in self._gevallen() if not g["geaccepteerd"]), None)

    def controleer_fasestart(self, fase: str, poging: str | None = None) -> None:
        """R8: stopregel en fasevolgorde; ook vooraf door de runner te toetsen.

        Een eerder gestarte poging zonder gevaluitkomst (crash na reservering of
        na afsluiting, vóór `registreer_geval`) stopt de proef net als een
        niet-geaccepteerd geval; alleen de lopende `poging` zelf mag haar
        volgende stap reserveren. Geen hervatting of reparatie.
        """
        identiteit = self.identiteit
        if identiteit.fasestappen is None:
            return
        gevallen = self._gevallen()
        geweigerd = self._stopgeval()
        if identiteit.stop_bij_eerste_fout and geweigerd is not None:
            msg = (
                f"proef gestopt na niet-geaccepteerd geval {geweigerd['poging']!r} "
                f"({geweigerd['reden']}); geen verdere modelstap"
            )
            raise BudgetSchendingError(msg)
        open_poging = self._open_poging(poging)
        if identiteit.stop_bij_eerste_fout and open_poging is not None:
            msg = (
                f"proef gestopt: poging {open_poging!r} is gestart zonder duurzame "
                "gevaluitkomst (onderbroken vóór registratie); geen hervatting en "
                "geen volgende poging"
            )
            raise BudgetSchendingError(msg)
        for voorganger in (identiteit.fasevolgorde or {}).get(fase, ()):
            nodig = identiteit.fasecaps[voorganger] // len(
                identiteit.fasestappen[voorganger]
            )
            klaar = sum(
                1 for g in gevallen if g["fase"] == voorganger and g["geaccepteerd"]
            )
            if klaar < nodig:
                msg = (
                    f"fase {fase!r} begint pas na volledig geaccepteerde fase "
                    f"{voorganger!r} ({klaar}/{nodig} gevallen)"
                )
                raise BudgetSchendingError(msg)

    def _controleer_kosten_en_volgorde(
        self, fase: str, poging: str | None, task_type: str | None
    ) -> int:
        """R8-regels vóór het netwerk; geeft de kostengrens van deze stap."""
        identiteit = self.identiteit
        kb = identiteit.kostenbewaking
        if kb is None or identiteit.fasestappen is None:
            msg = f"{identiteit.proef_id} heeft geen kostenbewaking met fasestappen"
            raise BudgetSchendingError(msg)
        self.controleer_fasestart(fase, poging)
        if not poging:
            msg = f"fase {fase!r} vereist een meerstapspoging (poging en stap)"
            raise BudgetSchendingError(msg)
        if task_type is None:
            msg = f"stap van {poging!r} vereist een task_type (kostenbewaking)"
            raise BudgetSchendingError(msg)
        stappen = identiteit.fasestappen[fase]
        index = sum(1 for r in self._reserveringen() if r.get("poging") == poging)
        if index >= len(stappen) or stappen[index] != task_type:
            msg = (
                f"taak {task_type!r} is niet stap {index + 1} van fase {fase!r} "
                f"(vaste volgorde {list(stappen)})"
            )
            raise BudgetSchendingError(msg)
        grens = kb.stapgrens_nusd(task_type)
        lopend = self.kostenstand()["lopend_nusd"]
        if lopend + grens > kb.plafond_nusd:
            msg = (
                f"kostenplafond: lopend {lopend} + stapgrens {grens} > "
                f"{kb.plafond_nusd} nUSD (niets verzonden)"
            )
            raise BudgetSchendingError(msg)
        return grens

    def registreer_geval(
        self,
        fase: str,
        poging: str,
        *,
        geaccepteerd: bool,
        reden: str,
        details: Mapping[str, Any] | None = None,
        technisch_afgerond: bool | None = None,
    ) -> dict[str, Any]:
        """Leg de uitkomst van één geval duurzaam vast (R8-stopregel en volgorde).

        Alleen na volledig afgesloten stappen en eenmalig; een geaccepteerd
        geval heeft al zijn stappen gebruikt. Een niet-geaccepteerd geval stopt
        de proef (zie `_controleer_kosten_en_volgorde`); onder
        `stop_alleen_technisch` (R13) is `technisch_afgerond` verplicht en stopt
        alleen een technisch niet-afgerond geval.
        """
        stappen = (self.identiteit.fasestappen or {}).get(fase)
        if stappen is None:
            msg = f"{self.identiteit.proef_id} registreert geen gevallen in {fase!r}"
            raise BudgetSchendingError(msg)
        if self.identiteit.stop_alleen_technisch != isinstance(
            technisch_afgerond, bool
        ):
            msg = (
                f"geval {poging!r}: technisch_afgerond hoort bij "
                f"stop_alleen_technisch ({self.identiteit.proef_id})"
            )
            raise BudgetSchendingError(msg)
        eigen = [
            r
            for r in self._reserveringen()
            if r.get("poging") == poging and r["fase"] == fase
        ]
        if not eigen:
            msg = f"geval {poging!r}: geen reservering in fase {fase!r}"
            raise BudgetSchendingError(msg)
        afgesloten = self._afsluitingen()
        if any(r["seq"] not in afgesloten for r in eigen):
            msg = f"geval {poging!r}: niet alle stappen zijn afgesloten"
            raise BudgetSchendingError(msg)
        if any(g["poging"] == poging for g in self._gevallen()):
            msg = f"geval {poging!r} is al geregistreerd"
            raise BudgetSchendingError(msg)
        if geaccepteerd and len(eigen) != len(stappen):
            msg = (
                f"geval {poging!r}: geaccepteerd met {len(eigen)} van "
                f"{len(stappen)} stappen"
            )
            raise BudgetSchendingError(msg)
        record = {
            "soort": "geval",
            "fase": fase,
            "poging": poging,
            "geaccepteerd": bool(geaccepteerd),
            "reden": reden,
            "seqs": [r["seq"] for r in eigen],
            "details": dict(details or {}),
        }
        if technisch_afgerond is not None:
            record["technisch_afgerond"] = technisch_afgerond
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
        if self.identiteit.gedeelde_codebinding:
            gedeeld = next(
                (r["binding"] for r in self._reserveringen() if r.get("binding")),
                None,
            )
            for veld in _GEDEELDE_BINDING:
                if gedeeld is not None and gedeeld.get(veld) != schoon.get(veld):
                    msg = (
                        f"{veld} van fase {fase!r} wijkt af van de gedeelde "
                        "binding van V en T (zelfde code en configuratie)"
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
        kosten_werkelijk_nusd: int | None = None,
    ) -> dict[str, Any]:
        """Sluit een reservering af; eenmalig, alleen met een bekende status.

        `kosten_werkelijk_nusd` (R8) = kosten uit de werkelijke SDK-usage;
        None = onbekend, dan telt de stapgrens (`kostenstand`).
        """
        if status not in AFSLUITSTATUSSEN:
            msg = f"onbekende afsluitstatus {status!r}"
            raise BudgetSchendingError(msg)
        if not any(r["seq"] == seq for r in self._reserveringen()):
            msg = f"onbekende reservering {seq}"
            raise BudgetSchendingError(msg)
        if seq in self._afsluitingen():
            msg = f"reservering {seq} is al afgesloten"
            raise BudgetSchendingError(msg)
        record: dict[str, Any] = {
            "soort": "afsluiting",
            "seq": seq,
            "status": status,
            "netwerk_gestart": bool(netwerk_gestart),
            "details": dict(details or {}),
        }
        if kosten_werkelijk_nusd is not None:
            if (
                isinstance(kosten_werkelijk_nusd, bool)
                or not isinstance(kosten_werkelijk_nusd, int)
                or kosten_werkelijk_nusd < 0
            ):
                msg = f"ongeldige werkelijke kosten {kosten_werkelijk_nusd!r}"
                raise BudgetSchendingError(msg)
            record["kosten_werkelijk_nusd"] = kosten_werkelijk_nusd
        return self._voeg_toe(record)


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
    _controleer_kostenkader(identiteit, boeken)


def _controleer_kostenkader(
    identiteit: Proefidentiteit, boeken: tuple[Grootboek, ...]
) -> None:
    """R9–R11: lopende kosten van de voorgangers onder kostenbewaking + eigen plafond.

    Werkelijk waar de usage bekend is, anders de stapgrens (`kostenstand`);
    zo blijven de rondes samen binnen het oorspronkelijke kader.
    """
    kader, kb = identiteit.kostenkader_nusd, identiteit.kostenbewaking
    if kader is None:
        return
    if kb is None:
        msg = f"{identiteit.proef_id}: kostenkader zonder eigen kostenbewaking"
        raise BudgetSchendingError(msg)
    eerder = sum(
        b.kostenstand()["lopend_nusd"]
        for b in boeken
        if b.identiteit.kostenbewaking is not None
    )
    if eerder + kb.plafond_nusd > kader:
        msg = (
            f"kostenkader: voorgangers lopend {eerder} + plafond {kb.plafond_nusd} "
            f"> {kader} nUSD (niets gestart)"
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
    #: R8: de toegelaten payload van deze stap; None = geen payloadwacht.
    grens: Stapgrens | None = None
    #: R8: gemeten compacte JSON-bytes van de verzonden body.
    payload_bytes: int | None = None


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
        kb = self._boek.identiteit.kostenbewaking
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
                task_type=task_type if kb is not None else None,
            )
        except BudgetSchendingError as exc:
            self._weigering = str(exc)
            raise
        reservering = Reservering(
            seq=res["seq"],
            sleutel=res["sleutel"],
            grens=kb.stapgrens(task_type) if kb is not None else None,
        )
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
            for naam in ("input_tokens", "output_tokens", *_CACHEVELDEN)
            if isinstance(getattr(usage, naam, None), int)
        }
    return meta


_CACHEVELDEN = ("cache_read_input_tokens", "cache_creation_input_tokens")
#: De enige SDK-argumenten die onder een stapgrens het netwerk op mogen.
_TOEGELATEN_PAYLOAD = frozenset(
    {"model", "max_tokens", "temperature", "thinking", "system", "messages", "timeout"}
)
_THINKING_UIT = {"type": "disabled"}


def _is_weggelaten(waarde: Any) -> bool:
    """`anthropic.omit`/`NOT_GIVEN`: de SDK verzendt het veld niet."""
    soort = type(waarde)
    return soort.__module__.startswith("anthropic") and soort.__name__ in {
        "Omit",
        "NotGiven",
    }


def _is_getal(waarde: Any) -> bool:
    return isinstance(waarde, int | float) and not isinstance(waarde, bool)


def _payloadfout(
    grens: Stapgrens, args: tuple, velden: Mapping[str, Any]
) -> str | None:
    """Reden waarom deze payload buiten de toegelaten platte tekst valt, of None."""
    vreemd = sorted(set(velden) - _TOEGELATEN_PAYLOAD)
    berichten = velden.get("messages")
    if args or vreemd:
        return f"payloadveld(en) {vreemd or 'positioneel'} niet toegestaan"
    if velden.get("model") != grens.model:
        return f"model {velden.get('model')!r} is niet {grens.model!r}"
    if not isinstance(velden.get("max_tokens"), int) or (
        velden["max_tokens"] != grens.max_tokens
    ):
        return f"max_tokens {velden.get('max_tokens')!r} is niet {grens.max_tokens}"
    if velden.get("thinking") != _THINKING_UIT:
        return f"thinking {velden.get('thinking')!r} is niet {_THINKING_UIT}"
    if "system" in velden and not isinstance(velden["system"], str):
        return "system moet platte tekst zijn (geen blokken of cache_control)"
    if "temperature" in velden and not _is_getal(velden["temperature"]):
        return "temperature moet een getal zijn"
    if "timeout" in velden and not _is_getal(velden["timeout"]):
        return "timeout moet een getal zijn"
    if (
        not isinstance(berichten, list)
        or not berichten
        or not all(
            isinstance(b, dict)
            and set(b) == {"role", "content"}
            and b["role"] in {"user", "assistant"}
            and isinstance(b["content"], str)
            for b in berichten
        )
    ):
        return (
            "messages moeten tekstberichten {role: user|assistant, content: str} zijn"
        )
    return None


def payloadbytes(velden: Mapping[str, Any]) -> int:
    """Compacte UTF-8-JSON-bytes van de verzonden body (zonder `timeout`).

    Dezelfde maat als de SDK-wacht; ook voor de vooraftoets van de runner.
    """
    body = {k: v for k, v in velden.items() if k != "timeout"}
    return len(
        json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def _usagefout(
    grens: Stapgrens, payload_bytes: int, sdk: Mapping[str, Any]
) -> str | None:
    """Reden waarom de werkelijke usage buiten de aangenomen stapgrens valt."""
    usage = sdk.get("usage") or {}
    invoer, uitvoer = usage.get("input_tokens"), usage.get("output_tokens")
    if not isinstance(invoer, int) or not isinstance(uitvoer, int):
        return "geen werkelijke usage in de SDK-respons: kosten niet te begrenzen"
    if any(usage.get(veld) for veld in _CACHEVELDEN):
        return f"cachetokens in de usage ({usage}); caching is niet toegelaten"
    if invoer > payload_bytes + grens.overhead_tokens:
        return (
            f"input_tokens {invoer} > payloadbytes {payload_bytes} + overhead "
            f"{grens.overhead_tokens}: de aanname tokens ≤ bytes + overhead houdt "
            "geen stand; proef stoppen"
        )
    if uitvoer > grens.max_tokens:
        return f"output_tokens {uitvoer} > max_tokens {grens.max_tokens}"
    return None


def installeer_sdk_wacht(klasse: Any) -> Any:
    """Bewaak `klasse.create` (bv. `anthropic...AsyncMessages`) op klasseniveau.

    Klasseniveau, omdat de client per aanroep `with_options(...)` en per
    eventloop een verse SDK-client gebruikt. Vóór het netwerk: reservering
    actief, nog geen SDK-aanroep in deze reservering, en `max_retries == 0` op
    de SDK-client die de aanroep doet. Draagt de reservering een stapgrens
    (R8), dan ook: alleen toegelaten platte-tekstpayload binnen de bytegrens,
    en achteraf usage binnen de aangenomen grens. Geeft een herstelfunctie terug.
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
        grens = reservering.grens
        if grens is not None:
            velden = {k: v for k, v in kwargs.items() if not _is_weggelaten(v)}
            fout = _payloadfout(grens, args, velden)
            if fout is None:
                reservering.payload_bytes = payloadbytes(velden)
                if reservering.payload_bytes > grens.bytegrens:
                    fout = (
                        f"payload {reservering.payload_bytes} bytes > bytegrens "
                        f"{grens.bytegrens} voor {grens.task_type}"
                    )
            if fout is not None:
                raise _weiger(reservering, f"vóór het netwerk geweigerd: {fout}")
        reservering.sdk_aanroepen += 1
        reservering.netwerk_gestart = True
        resp = await origineel(self, *args, **kwargs)
        reservering.sdk = _sdk_metadata(resp)
        if grens is not None:
            fout = _usagefout(grens, reservering.payload_bytes or 0, reservering.sdk)
            if fout is not None:
                raise _weiger(reservering, f"usage buiten de stapgrens: {fout}")
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


def kosten_nusd(sdk: Mapping[str, Any], kb: Kostenbewaking) -> int | None:
    """Werkelijke stapkosten in nUSD uit de SDK-usage, of None zonder usage.

    Cachetokens (die de wacht al weigert) tellen conservatief als tweemaal
    het invoertarief.
    """
    usage = sdk.get("usage") or {}
    invoer, uitvoer = usage.get("input_tokens"), usage.get("output_tokens")
    if not isinstance(invoer, int) or not isinstance(uitvoer, int):
        return None
    cache = sum(usage.get(veld) or 0 for veld in _CACHEVELDEN)
    return (invoer + 2 * cache) * kb.tarief_invoer_nusd + uitvoer * (
        kb.tarief_uitvoer_nusd
    )


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
