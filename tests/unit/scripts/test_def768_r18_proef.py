"""DEF-768 B3 — registratie R18A (alleen interpretatie) en R18B (lokale controle), offline.

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B3,
met de aanvullingen van de opdracht: één ronde R18 met twee fases,
`interpretatie` (R18A: `interpreteer()`, 4 gevallen × 3 herhalingen = 12, geen
retry of cache, scorer in het record, acceptatie per run volgens deel C) en
`lokale_verificatie` (R18B: 6 pakketten uit de synthetisch herbonden
R17-interpretaties A en C). Budget: 18 aanroepen, cumulatief 399 → max 417
binnen 427, gecontroleerd tegen het R17-grootboek.

Veiligheid: er is GEEN budgetbesluit en GEEN freeze. Zonder gepind besluit
start geen enkele route een netwerkaanroep (`--echt` en een echte omgeving
weigeren vóór client en grootboek; een niet-echte run draait onder
`geen_netwerk`). Alle providers hier zijn nep; geen netwerk, geen betaalde call.
"""

from __future__ import annotations

import asyncio
import collections
import copy
import dataclasses
import json
import socket
import sys
from pathlib import Path

import pytest

from services.ai.base_client import ChatResponse
from tests.unit.scripts.test_def768_bewijsscorer import (
    _UITLEEN4,
    BUUR,
    ORAKEL_A,
    ORAKEL_D,
    ORAKEL_E,
    _a_juist,
    _d_juist,
    _e,
    _e_met_m,
    _ruw,
    _u,
)
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r9_proef import _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    HUIDIG_CONTRACT,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _r9_boek,
    _sha,
)
from tests.unit.scripts.test_def768_r11_proef import _r10_boek
from tests.unit.scripts.test_def768_r12_microproef import _r11_boek
from tests.unit.scripts.test_def768_r13_herkenbare_gevallen import _r12_boek
from tests.unit.scripts.test_def768_r14_herproef import _r13_boek
from tests.unit.scripts.test_def768_r15_lokale_proef import _r14_boek
from tests.unit.scripts.test_def768_r16_bewijsregelproef import (
    H3,
    OUDE_RONDES,
    VERWACHT,
    V,
    W,
    _BewijsProvider,
    _r15_boek,
)
from tests.unit.scripts.test_def768_r17_bewijsregelproef import (
    R17_CONTRACT,
    _keten17,
    _r16_boek,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import bewijsscorer as bs
import maak_r16_bewijsregel_invoer as mk16
import maak_r18_bewijsregel_invoer as mk18
import maak_r18b_lokale_invoer as mk18b
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

from domain.ess05 import bewijsregels as br
from services.validation.ess05_bewijsregel_service import (
    bouw_interpretatieprompt,
    interpretatiesysteemprompt,
)

R18_ID = "DEF-768-AI-20260928-R18"
R18_MAP = ROOT / "reports" / R18_ID
#: Aanvulling v4 (Codex-hercontrole v3, besluit optie 2): de invoer -v5 (schema
#: /6, E-orakel zonder lexicale voorwaardevelden; oordeel van Chris).
I18 = R18_MAP / "bewijsregel-invoer-v5.json"
L18 = R18_MAP / "lokale-invoer-v1.json"
I18_SHA256 = "b2c3c34dbe91d0c8b49746d8438793f3994b098620700ea4cbfe9f4a7619d8c4"
#: De vierde invoer (schema /5, geregistreerde formuleringen): blijft staan, geweigerd.
I18_V4 = R18_MAP / "bewijsregel-invoer-v4.json"
I18_V4_SHA256 = "75c975806704520bd3abee39f7a7525dab2722fad14fde24ad48f676ce92f135"
#: De derde invoer (schema /4, behoud via aanhef): blijft staan, wordt geweigerd.
I18_V3 = R18_MAP / "bewijsregel-invoer-v3.json"
I18_V3_SHA256 = "21c1ad911cbe13b02c377c2799f17b4e0475f9e9a006d39f87ec96f2bc5a09ac"
#: De tweede invoer (schema /3, E ook review_required): blijft staan, wordt geweigerd.
I18_V2 = R18_MAP / "bewijsregel-invoer-v2.json"
I18_V2_SHA256 = "fab905cc9d81f803401ebb35409ade36ce63fb6fd4162adfbb55153c78978932"
#: De eerste invoer (schema /2, orakelveld `eenheden`): blijft staan, wordt geweigerd.
I18_V1 = R18_MAP / "bewijsregel-invoer-v1.json"
I18_V1_SHA256 = "fe6bd5d1ce58405cc4560ce0956996b4bc0d7e3d3bbefe086f9b9fdc04873598"
LOGS = ROOT / "logs" / "def768"
BESLUIT18 = LOGS / "ronde18-budgetbesluit-v1.json"
#: De kop van het afgesloten R17-grootboek (3 calls, 0 open), gelezen 28-09.
R17_KOP_SHA256 = "b1fa47de331d578bdc9da38e76583a2b4e63bcecd74730374ad1cbe76b4e171b"
#: De werkelijke R17-kosten (3 SDK-calls, USD 0,152390).
R17_KOSTEN_NUSD = 152_390_000
#: USD 25 − werkelijke R8–R17-kosten (USD 3,201135).
KADERREST18_NUSD = 21_798_865_000
LABEL = "SYNTHETISCH, GEEN MODELUITVOER"
ORAKEL_C = mk18.ORAKELS["C"]
GECORRIGEERD = (
    ROOT
    / "reports"
    / "DEF-768-AI-20260928-R17"
    / ("oorzakenonderzoek-ess05-v1-reproductie")
)
echte_grootboeken_nodig = pytest.mark.skipif(
    not all(
        runner.PROEVEN[n].opslag.grootboek.is_file()
        for n in (*OUDE_RONDES, "R16", "R17")
    ),
    reason="git-ignored echte grootboeken ontbreken",
)
r18_invoer_nodig = pytest.mark.skipif(
    not (I18.is_file() and L18.is_file() and GECORRIGEERD.is_dir()),
    reason="git-ignored R17/R18-invoer ontbreekt",
)


# --- hulpen: invoer zonder git-ignored bestanden ----------------------------------------------


def _items() -> list[dict]:
    """A/C/D/E zoals de R18-maker, op H3 (= R17-item A) in plaats van de R17-invoer."""
    oud = {
        n: mk16._item(n, g, variant=f"variant {n}", synthetisch=n != "A",
                      onvolledig=[], verwacht=VERWACHT[n], herkomst={"bron": "test"})
        for n, g in (("A", H3), ("C", mk16._geval_c(H3)))
    }  # fmt: skip
    return [
        mk18._uit_r17(oud["A"], {"bron": "test"}),
        mk18._uit_r17(oud["C"], {"bron": "test"}),
        mk18._synthetisch("D", oud["A"], mk18.BRON_D, {"bron": "test"}),
        mk18._synthetisch("E", oud["A"], mk18.BRON_E, {"bron": "test"}),
    ]


def _invoerdata(items=None) -> dict:
    return {
        "schema": mk18.INVOERSCHEMA,
        "contract": runner.bewijsregel_contractidentiteit(),
        "items": _items() if items is None else items,
    }


def _i_invoer(tmp_path: Path, data=None) -> Path:
    pad = tmp_path / "i-invoer.json"
    pad.write_text(
        json.dumps(_invoerdata() if data is None else data), encoding="utf-8"
    )
    return pad


def _juist(naam: str, vergelijking) -> dict:
    """De vooraf vastgelegde, juiste interpretatie per geval (geen modeluitvoer)."""
    if naam == "A":
        return _a_juist(vergelijking)
    if naam == "C":
        return _ruw(vergelijking, _UITLEEN4, {
            "K1": ("ontkend", ["Verhuur:", BUUR]), "K2": ("onbesproken", []),
            "K3": ("bevestigd", ["Verhuur:"]), "K4": ("onbesproken", []),
        })  # fmt: skip
    if naam == "D":
        return _d_juist(vergelijking)
    return _e(vergelijking, ("bevestigd", ["Uitleen:"], ["bij storing"]))


class _R18Provider(_BewijsProvider):
    """Interpretatie: per geval een vooraf opgestelde tekst; controle zoals R16.

    `antwoord(naam, herhaling, vergelijking)` geeft de modeltekst. Met
    `netwerkpoging` probeert elke aanroep eerst een lokale socketverbinding
    (127.0.0.1) en legt de fout vast: zo is zichtbaar of `geen_netwerk` actief is.
    """

    def __init__(self, items, *, antwoord=None, netwerkpoging=False, **kw):
        super().__init__(**kw)
        self.per_prompt = {
            bouw_interpretatieprompt(mk18.vergelijkingsinvoer(i))[1]: i for i in items
        }
        self.antwoord = antwoord or (
            lambda naam, _n, verg: json.dumps(_juist(naam, verg), ensure_ascii=False)
        )
        self.netwerkpoging = netwerkpoging
        self.netwerkfouten: list[str] = []
        self.per_item: collections.Counter = collections.Counter()

    async def chat_completion(self, messages, model, **kwargs):
        if self.netwerkpoging:
            try:
                socket.create_connection(("127.0.0.1", 9), timeout=0.2).close()
                self.netwerkfouten.append("verbonden")
            except OSError as exc:
                self.netwerkfouten.append(str(exc))
        system = next(m.content for m in messages if m.role == "system")
        if system != interpretatiesysteemprompt():
            return await super().chat_completion(messages, model, **kwargs)
        user = "\n".join(m.content for m in messages if m.role != "system")
        self.berichten.append((system, user))
        self.aanroepen.append({"model": model, **kwargs})
        if self.fout_bij is not None and len(self.berichten) == self.fout_bij:
            raise ConnectionError("netwerk weg")
        item = self.per_prompt[user]
        self.per_item[item["id"]] += 1
        tekst = self.antwoord(
            item["id"], self.per_item[item["id"]], mk18.vergelijkingsinvoer(item)
        )
        return ChatResponse(
            text=tekst, tokens_used=10, model=model, stop_reason=self.stop
        )


# --- hulpen: keten en runs --------------------------------------------------------------------


def _r17_boek(root: Path, *, kosten: int = R17_KOSTEN_NUSD) -> gb.Grootboek:
    """Een R17-grootboek zoals het echte: A, B, C elk alleen de interpretatie."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R17)
    binding = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
               "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip
    for naam in ("A", "B", "C"):
        poging = f"bewijsregels|{naam}|1"
        res = boek.reserveer("bewijsregels", f"{poging}/interpretatie",
                             invoer_sha256="a" * 64, poging=poging, stap="interpretatie",
                             vorige_stap=None, task_type=V, binding=binding)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                   kosten_werkelijk_nusd=kosten // 3)  # fmt: skip
        boek.registreer_geval("bewijsregels", poging, geaccepteerd=False, reden="r17",
                              technisch_afgerond=True)  # fmt: skip
    return boek


def _keten18(tmp_path: Path):
    r17 = runner.Proefopslag(tmp_path / "r17")
    boek17 = _r17_boek(r17.root)
    _, keten17 = _keten17(tmp_path)
    return boek17, (r17, *keten17)


def _bestaande_keten18(tmp_path: Path):
    namen = ("r17", "r16", "r15", "r14", "r13", "r12", "r11", "r10", "r9", "r8",
             "r7", "r6", "r5", "r4", "r3", "r2", "r1")  # fmt: skip
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag18(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r18")


def _freeze(omg, tmp_path: Path, proef, groep: str) -> Path:
    pad = tmp_path / f"freeze-{groep}.json"
    if not pad.exists():
        pad.write_text(
            json.dumps(runner.freezevelden(omg, proef, groep)), encoding="utf-8"
        )
    return pad


def _i18(omg, tmp_path, pad, *, nieuw=True, proef=None, **kw):
    proef = proef or dataclasses.replace(
        runner.PROEVEN["R18"], i_invoer_sha256=_sha(pad)
    )
    keten = _keten18(tmp_path)[1] if nieuw else _bestaande_keten18(tmp_path)
    return asyncio.run(
        runner.voer_i_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag18(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef, "i"),
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _records(tmp_path: Path, fase: str = "interpretatie") -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for callmap in sorted((tmp_path / "uit").glob(f"{fase}-*/calls"))
        for p in sorted(callmap.glob("*.json"))
    ]


def _samenvatting_i(tmp_path: Path) -> dict:
    """De samenvatting van de (enige) interpretatierun, ook als die stopte."""
    (pad,) = sorted((tmp_path / "uit").glob("interpretatie-*/samenvatting.json"))
    return json.loads(pad.read_text(encoding="utf-8"))


def _grootboekregels(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag18(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


# --- identiteit en budget ---------------------------------------------------------------------


class TestIdentiteit:
    def test_twee_fases_18_stappen_cumulatief_417(self):
        r18 = gb.R18
        assert r18.proef_id == R18_ID
        assert dict(r18.fasecaps) == {"interpretatie": 12, "lokale_verificatie": 6}
        assert (r18.reserve_max, r18.totaal_max) == (0, 18)
        assert r18.voorganger is gb.R17
        assert r18.cumulatief_max == 417 == 399 + 18 <= 427 == gb.R8.cumulatief_max
        assert dict(r18.fasestappen) == {
            "interpretatie": (V,),
            "lokale_verificatie": (W,),
        }
        assert dict(r18.fasevolgorde) == {"interpretatie": (), "lokale_verificatie": ()}
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r18.eindgroepen] == [
            ("i", {"interpretatie"}, 0),
            ("l", {"lokale_verificatie"}, 0),
        ]
        assert r18.modelstappen_per_geval == 1
        assert (r18.gedeelde_codebinding, r18.stop_bij_eerste_fout) == (True, True)
        assert (r18.stop_alleen_technisch, r18.vroege_stop_toegestaan) == (True, False)
        assert r18.bindingsvelden == gb.R17.bindingsvelden

    def test_plafond_de_volledige_stapbegroting_binnen_de_kaderrest(self):
        kb = gb.R18.kostenbewaking
        assert kb == dataclasses.replace(
            gb.R8.kostenbewaking, plafond_nusd=6_030_000_000
        )
        # 12 × 0,315 (interpretatie) + 6 × 0,375 (lokale controle) = USD 6,03.
        assert kb.stapgrens_nusd(V) == 315_000_000
        assert kb.stapgrens_nusd(W) == 375_000_000
        assert (
            kb.plafond_nusd
            == gb.begroting_nusd(gb.R18)
            == 12 * 315_000_000 + 6 * 375_000_000
        )
        assert kb.plafond_nusd <= KADERREST18_NUSD
        assert gb.R18.kostenkader_nusd == 25_000_000_000

    def test_historische_identiteiten_ongewijzigd(self):
        assert (gb.R17.voorganger, gb.R17.cumulatief_max) == (gb.R16, 408)
        assert (gb.R16.voorganger, gb.R16.cumulatief_max) == (gb.R15, 403)
        assert dict(gb.R17.fasecaps) == {"bewijsregels": 12}
        gb._bekende_identiteit(gb.R18)
        with pytest.raises(gb.BudgetSchendingError, match="alleen R1 t/m R18"):
            gb._bekende_identiteit(dataclasses.replace(gb.R18, proef_id="R19"))

    def test_budgetgetallen_in_de_registratie(self):
        budget = runner.R18_BUDGET
        assert budget["modelaanroepen"] == 18 == gb.R18.totaal_max
        assert dict(budget["fasen"]) == dict(gb.R18.fasecaps)
        assert budget["historisch_verbruik"] == 399
        assert budget["cumulatief_max"] == 417 == gb.R18.cumulatief_max
        assert budget["historisch_verbruik"] + budget["modelaanroepen"] == 417
        assert budget["cumulatief_plafond"] == 427 == gb.R8.cumulatief_max
        assert budget["kostenplafond_nusd"] == gb.R18.kostenbewaking.plafond_nusd
        assert budget["kaderrest_nusd"] == KADERREST18_NUSD == runner.R18_KADERREST_NUSD

    def test_cumulatief_399_plus_18_past_19_niet(self, tmp_path):
        keten = [
            _r17_boek(tmp_path / "r17"),
            _r16_boek(tmp_path / "r16"),
            _r15_boek(tmp_path / "r15"),
            _r14_boek(tmp_path / "r14"),
            _r13_boek(tmp_path / "r13"),
            _r12_boek(tmp_path / "r12"),
            _r11_boek(tmp_path / "r11"),
            _r10_boek(tmp_path / "r10"),
            _r9_boek(tmp_path / "r9"),
            _r8_boek(tmp_path / "r8"),
        ]
        for naam, identiteit, n in (("r7", gb.R7, 37), ("r6", gb.R6, 37),
                                    ("r5", gb.R5, 57), ("r4", gb.R4, 57),
                                    ("r3", gb.R3, 57), ("r2", gb.R2, 57),
                                    ("r1", gb.R1, 57)):  # fmt: skip
            keten_boek(tmp_path / naam, identiteit, n)
            keten.append(
                gb.Grootboek.lees(tmp_path / naam / "callgrootboek.jsonl", identiteit)
            )
        assert sum(b.samenvatting()["totaal"] for b in keten) == 399
        boek = gb.Grootboek.nieuw(_opslag18(tmp_path).grootboek, gb.R18)
        gb.controleer_cumulatief(boek, keten, 18)
        with pytest.raises(gb.BudgetSchendingError, match="417"):
            gb.controleer_cumulatief(boek, keten, 19)

    @echte_grootboeken_nodig
    def test_echte_grootboeken_399_calls_usd_3_201135_en_r17_kop(self, tmp_path):
        """De budgetgetallen gecontroleerd tegen de echte (alleen gelezen) grootboeken."""
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed((*OUDE_RONDES, "R16", "R17"))
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 399
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:10])
        assert lopend == 3_201_135_000 == 25_000_000_000 - KADERREST18_NUSD
        assert keten[0].kostenstand()["lopend_nusd"] == R17_KOSTEN_NUSD
        assert keten[0].samenvatting()["onafgesloten"] == 0
        assert keten[0].samenvatting()["kop_sha256"] == R17_KOP_SHA256
        runner._controleer_voorgangerkop(runner.PROEVEN["R18"], tuple(keten))
        boek = gb.Grootboek.nieuw(_opslag18(tmp_path).grootboek, gb.R18)
        gb.controleer_cumulatief(boek, keten, 18)
        with pytest.raises(gb.BudgetSchendingError, match="417"):
            gb.controleer_cumulatief(boek, keten, 19)


# --- registratie ------------------------------------------------------------------------------


class TestRegistratie:
    def test_r18_geregistreerd_zonder_besluit(self):
        proef = runner.PROEVEN["R18"]
        assert proef.identiteit is gb.R18
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R18_MAP
        assert proef.i_invoer_sha256 == runner.R18_I_INVOER_SHA256 == I18_SHA256
        assert proef.l_invoer_sha256 == runner.R18_L_INVOER_SHA256
        assert (proef.t_ontwikkelinvoer_sha256, proef.v_invoer_sha256,
                proef.b_invoer_sha256) == (None, None, None)  # fmt: skip
        # Geen budgetbesluit: pad vastgelegd, hash niet; elke echte call weigert.
        assert proef.budgetbesluit == BESLUIT18 == runner.R18_BUDGETBESLUIT
        assert proef.budgetbesluit_sha256 is None is runner.R18_BUDGETBESLUIT_SHA256
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == HUIDIG_CONTRACT
        assert dict(proef.lokaal_contract) == dict(runner.R15_LOKAAL_CONTRACT)
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST18_NUSD
        assert proef.voorganger_kop_sha256 == R17_KOP_SHA256 == runner.R17_KOP_SHA256

    def test_bewijsregelcontract_is_de_berekende_contractidentiteit(self):
        proef = runner.PROEVEN["R18"]
        assert (
            dict(proef.bewijsregel_contract) == runner.bewijsregel_contractidentiteit()
        )
        assert dict(runner.R18_BEWIJSREGEL_CONTRACT) == dict(proef.bewijsregel_contract)
        assert (
            proef.bewijsregel_contract["bewijsregel_version"] == "ess05-bewijsregels/6"
        )
        runner._controleer_contract(_omgeving8(_BewijsProvider()), proef)
        runner._controleer_lokaal_contract(proef)
        runner._controleer_bewijsregel_contract(proef)

    @pytest.mark.parametrize(
        "veld",
        [
            "bewijsregel_version",
            "interpretation_schema_version",
            "render_version",
            "interpretation_prompt_version",
            "interpretation_system_prompt_sha256",
        ],
    )
    def test_afwijkend_bewijsregelcontract_geweigerd(self, veld):
        contract = {**runner.R18_BEWIJSREGEL_CONTRACT, veld: "anders"}
        proef = dataclasses.replace(
            runner.PROEVEN["R18"], bewijsregel_contract=contract
        )
        with pytest.raises(gb.BudgetSchendingError, match="geen call gestart"):
            runner._controleer_bewijsregel_contract(proef)

    def test_r16_en_r17_blijven_historisch_gepind_en_geweigerd(self):
        assert dict(runner.PROEVEN["R17"].bewijsregel_contract) == R17_CONTRACT
        assert runner.PROEVEN["R17"].b_invoer_sha256 == runner.R17_B_INVOER_SHA256
        for naam in ("R16", "R17"):
            with pytest.raises(gb.BudgetSchendingError, match="geen call gestart"):
                runner._controleer_bewijsregel_contract(runner.PROEVEN[naam])

    def test_freezegroep_i_bindt_product_lokaal_en_bewijsregelcontract(self):
        omg = _omgeving8(_BewijsProvider())
        velden = runner.freezevelden(omg, runner.PROEVEN["R18"], "i")
        assert (velden["groep"], velden["proef_id"]) == ("i", R18_ID)
        for bron in (runner.contractidentiteit(omg), runner.lokale_contractidentiteit(),
                     runner.bewijsregel_contractidentiteit()):  # fmt: skip
            for sleutel, waarde in bron.items():
                assert velden[sleutel] == waarde, sleutel

    def test_freezegroep_l_van_r18_bindt_ook_het_bewijsregelcontract(self):
        omg = _omgeving8(_BewijsProvider())
        r18 = runner.freezevelden(omg, runner.PROEVEN["R18"], "l")
        for sleutel, waarde in runner.bewijsregel_contractidentiteit().items():
            assert r18[sleutel] == waarde, sleutel
        # R15 (historisch) blijft zonder bewijsregelcontract.
        r15 = runner.freezevelden(omg, runner.PROEVEN["R15"], "l")
        assert "bewijsregel_version" not in r15

    def test_besluit_zonder_gepinde_hash_weigert_ook_als_er_een_bestand_is(
        self, tmp_path
    ):
        with pytest.raises(gb.BudgetSchendingError, match="geen budgetbesluit"):
            runner.controleer_budgetbesluit(runner.PROEVEN["R18"])
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps({"type": "gebruikersgoedkeuring-proefbudget"}),
                       encoding="utf-8")  # fmt: skip
        proef = dataclasses.replace(runner.PROEVEN["R18"], budgetbesluit=pad)
        with pytest.raises(gb.BudgetSchendingError, match="geen budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    def test_codemanifest_bevat_de_scorer(self):
        """De runner scoort elke run: de scorer valt onder code_sha256 en de freeze.
        De makers draaien niet mee; hun uitvoer is op hash gepind."""
        assert "scripts/ess05/bewijsscorer.py" in runner.codemanifest()


# --- veiligheid: geen netwerk zonder budgetbesluit --------------------------------------------


def _geen_live(*_a, **_k):
    raise AssertionError("live_omgeving mag zonder budgetbesluit nooit gebouwd worden")


class TestGeenNetwerkZonderBesluit:
    @pytest.mark.parametrize("fase", ["interpretatie", "lokale_verificatie"])
    def test_cli_echt_weigert_voor_client_en_grootboek(
        self, tmp_path, monkeypatch, fase
    ):
        monkeypatch.setattr(runner, "live_omgeving", _geen_live)
        grootboek = runner.PROEVEN["R18"].opslag.grootboek
        bestond = grootboek.exists()
        pad = tmp_path / "invoer.json"
        pad.write_text("{}", encoding="utf-8")
        with pytest.raises(SystemExit):
            runner.main(["--proef", "R18", "--fase", fase, "--gevallen", str(pad),
                         "--echt", "--freeze", str(tmp_path / "f.json")])  # fmt: skip
        assert grootboek.exists() is bestond is False

    def test_echte_omgeving_i_fase_weigert_voor_elke_call(self, tmp_path):
        provider = _R18Provider(_items())
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        proef = runner.PROEVEN["R18"]
        pad = _i_invoer(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="geen budgetbesluit"):
            asyncio.run(
                runner.voer_i_fase(omg, gevallenpad=pad, uitmap=tmp_path / "uit",
                                   opslag=proef.opslag, proef=proef,
                                   freeze=_freeze(omg, tmp_path, proef, "i"))
            )  # fmt: skip
        assert provider.berichten == [] and provider.aanroepen == []
        assert not proef.opslag.grootboek.exists()
        assert not (tmp_path / "uit").exists()

    def test_echte_omgeving_l_fase_weigert_voor_elke_call(self, tmp_path):
        provider = _R18Provider(_items())
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        proef = runner.PROEVEN["R18"]
        pad, _ = _l_invoer(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="geen budgetbesluit"):
            asyncio.run(
                runner.voer_l_fase(omg, gevallenpad=pad, uitmap=tmp_path / "uit",
                                   opslag=proef.opslag, proef=proef,
                                   freeze=_freeze(omg, tmp_path, proef, "l"))
            )  # fmt: skip
        assert provider.berichten == [] and provider.aanroepen == []
        assert not proef.opslag.grootboek.exists()

    def test_niet_echte_i_run_zonder_besluit_draait_onder_geen_netwerk(self, tmp_path):
        provider = _R18Provider(_items(), netwerkpoging=True)
        oud = socket.create_connection
        _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path), max_calls=2)
        assert len(provider.netwerkfouten) == 2
        assert all("netwerk is geblokkeerd" in f for f in provider.netwerkfouten)
        assert socket.create_connection is oud

    def test_niet_echte_l_run_zonder_besluit_draait_onder_geen_netwerk(self, tmp_path):
        provider = _R18Provider(_items(), netwerkpoging=True)
        _l18(_omgeving8(provider), tmp_path, max_calls=1)
        assert provider.netwerkfouten
        assert all("netwerk is geblokkeerd" in f for f in provider.netwerkfouten)

    def test_andere_fases_bestaan_niet_in_r18(self, tmp_path):
        omg = _omgeving8(_R18Provider(_items()))
        pad = _i_invoer(tmp_path)
        for fase in ("bewijsregels", "ontwikkeling", "verificatie_alleen"):
            with pytest.raises(gb.BudgetSchendingError, match="bestaat niet"):
                runner._fase_van(runner.PROEVEN["R18"], fase,
                                 (*runner.B_FASES, *runner.T_FASES, *runner.V_FASES))  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="bestaat niet"):
            asyncio.run(
                runner.voer_b_fase(omg, gevallenpad=pad, uitmap=tmp_path / "uit",
                                   opslag=_opslag18(tmp_path),
                                   proef=runner.PROEVEN["R18"])
            )  # fmt: skip


# --- I-invoer ---------------------------------------------------------------------------------


class TestIInvoer:
    def test_geldige_invoer_twaalf_runs(self):
        items = runner.valideer_i_invoer(_invoerdata(), _omgeving8(_BewijsProvider()))
        assert [i.sleutel for i in items] == [
            f"interpretatie|{n}|{h}" for n in "ACDE" for h in (1, 2, 3)
        ]
        assert [i.herhaling for i in items] == [1, 2, 3] * 4
        for ii in items:
            assert ii.prompt[0] == interpretatiesysteemprompt()

    @pytest.mark.parametrize(
        ("wijzig", "melding"),
        [
            (lambda i: i["geval"].update(tekst="anders"), "geval_sha256"),
            (lambda i: i.update(geval_sha256="0" * 64), "geval_sha256"),
            (lambda i: i["materiaal_sha256"].update(context="0" * 64), "materiaal"),
            (lambda i: i.update(prompt_sha256="0" * 64), "interpretatieprompt"),
            (lambda i: i.update(buren=[["x", "y"]]), "buur"),
            (lambda i: i.update(herhalingen=0), "herhalingen"),
            (lambda i: i.update(herhalingen=True), "herhalingen"),
            (lambda i: i.update(herhalingen="3"), "herhalingen"),
            (lambda i: i.pop("herhalingen"), "herhalingen"),
            (lambda i: i["orakel"]["kenmerken"].update(x={"huur": {"toestand": ["bevestigd"]}}), "orakel"),
            (lambda i: i["orakel"].update(dragend=["onbekend"]), "orakel"),
            (lambda i: i.pop("orakel"), "orakel"),
            # Aanvulling C3: het oude orakelveld `eenheden` is geen geldige structuur.
            (lambda i: i["orakel"]["kenmerken"]["kosteloos"]["doel"].update(
                eenheden=["Voor uitleen betaalt"]), "orakel"),
            (lambda i: i["orakel"]["kenmerken"]["kosteloos"]["verhuur"].pop("vereist"),
             "orakel"),
            (lambda i: i.update(label="gewoon"), "label"),
            (lambda i: i.update(synthetisch="ja"), "label"),
        ],
    )  # fmt: skip
    def test_gemanipuleerd_item_geweigerd(self, wijzig, melding):
        data = _invoerdata()
        wijzig(data["items"][2])
        with pytest.raises(pi.InvoerfoutError, match=melding):
            runner.valideer_i_invoer(data, _omgeving8(_BewijsProvider()))

    def test_ander_contract_geweigerd(self):
        data = _invoerdata()
        data["contract"] = R17_CONTRACT
        with pytest.raises(pi.InvoerfoutError, match="ander bewijsregelcontract"):
            runner.valideer_i_invoer(data, _omgeving8(_BewijsProvider()))

    def test_dubbele_ids_geweigerd(self):
        items = _items()
        items[1] = copy.deepcopy(items[0])
        with pytest.raises(pi.InvoerfoutError, match="dubbele"):
            runner.valideer_i_invoer(_invoerdata(items), _omgeving8(_BewijsProvider()))

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"schema": "def768-ess05-bewijsregel-invoer/1", "items": [1]},
            {"schema": mk18.INVOERSCHEMA, "items": []},
            {"schema": mk18.INVOERSCHEMA, "items": [1]},
            [],
        ],
    )
    def test_verkeerd_schema_geweigerd(self, data):
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_i_invoer(data, _omgeving8(_BewijsProvider()))

    def test_b_fase_weigert_de_i_invoer_en_omgekeerd(self):
        omg = _omgeving8(_BewijsProvider())
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_b_invoer(_invoerdata(), omg)


# --- R18A: interpretatiefase ------------------------------------------------------------------


class TestInterpretatieFase:
    def test_juiste_interpretaties_twaalf_runs_wachten_op_chris(self, tmp_path):
        """Aanvulling v4: ook met alle juiste interpretaties is de proef nooit
        automatisch geslaagd; de drie E-runs wachten op het oordeel van Chris."""
        provider = _R18Provider(_items())
        uit = _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert uit["aanroepen_gestart"] == 12
        assert uit["grootboek_na"]["per_fase"] == {
            "interpretatie": 12,
            "lokale_verificatie": 0,
        }
        assert uit["grootboek_na"]["totaal"] == 12
        # Alleen interpretaties: geen enkele controle-aanroep.
        assert len(provider.berichten) == 12
        assert {s for s, _ in provider.berichten} == {interpretatiesysteemprompt()}
        assert dict(provider.per_item) == {"A": 3, "C": 3, "D": 3, "E": 3}
        oordeel = uit["proefoordeel"]
        assert oordeel["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert (oordeel["runs"], oordeel["m_d_juist"], oordeel["m_c_dragend"],
                oordeel["m_b_dragend"]) == (12, 9, 12, 12)  # fmt: skip
        assert oordeel["e_voorwaarde_behouden"] == [0, 3]
        assert oordeel["kritiek"] == [] and oordeel["f7"] == []

    def test_record_met_ruwe_interpretatie_en_scorer(self, tmp_path):
        provider = _R18Provider(_items())
        _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        records = _records(tmp_path)
        assert len(records) == 12
        assert [r["sleutel"] for r in records] == [
            f"interpretatie|{n}|{h}" for n in "ACDE" for h in (1, 2, 3)
        ]
        for r in records:
            assert r["schema"] == "def768-ess05-interpretatiecall/1"
            assert r["interpretatie"]["ruw"] == json.loads(
                r["reserveringen"][0]["ruw_antwoord"]
            )
            assert r["score"]["m_d"]["ok"] is True
            assert r["dienstuitkomst"] == {
                "uitkomst": r["score"]["m_d"]["uitkomst"],
                "fout": r["score"]["m_d"]["fout"],
            }
            assert r["m_d_gelijk_aan_dienst"] is True
            e = r["item_id"] == "E"
            assert r["runoordeel"]["categorie"] == (
                "handmatig_beoordelen" if e else "geslaagd"
            )
            assert r["orakel"] == mk18.ORAKELS[r["item_id"]]
            assert r["contract"] == runner.bewijsregel_contractidentiteit()
            assert r["prompt"]["komt_overeen_met_dienst"] is True
            assert len(r["reserveringen"]) == 1
            assert r["reserveringen"][0]["task_type"] == V
            assert r["acceptatie"] == {
                "geaccepteerd": not e,
                "reden": r["acceptatie"]["reden"],
                "technisch_afgerond": True,
            }
        assert {r["item_id"]: r["synthetisch"] for r in records} == {
            "A": False, "C": True, "D": True, "E": True,
        }  # fmt: skip

    def test_blind_hergebruik_in_d_stopt_voor_de_volgende_aanroep(self, tmp_path):
        """Correctie B1 (aanvulling C1): een kritieke run stopt R18A direct."""

        def antwoord(naam, _n, verg):
            ruw = _d_juist(verg, ("Uitleen:",)) if naam == "D" else _juist(naam, verg)
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        with pytest.raises(gb.BudgetSchendingError, match="kritieke run"):
            _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        # A1–A3, C1–C3 en D1: de kritieke D1 is de laatste aanroep.
        assert len(provider.berichten) == 7
        assert dict(provider.per_item) == {"A": 3, "C": 3, "D": 1}
        records = _records(tmp_path)
        assert [r["sleutel"] for r in records][-1] == "interpretatie|D|1"
        assert records[-1]["runoordeel"]["categorie"] == "kritiek"
        assert records[-1]["runoordeel"]["kritiek"] == ["pass/fail bij M-b onwaar"]
        uit = _samenvatting_i(tmp_path)
        assert uit["aanroepen_gestart"] == 7
        assert uit["stop"] == {
            "run": "interpretatie|D|1",
            "reden": uit["stop"]["reden"],
            "niet_gestart": 5,
        }
        assert "kritieke run" in uit["stop"]["reden"]
        assert "M-b onwaar" in uit["stop"]["reden"]
        assert uit["proefoordeel"]["oordeel"] == "afgekeurd"
        assert uit["grootboek_na"]["inhoudelijke_stop"] == [
            {"fase": "interpretatie", "poging": "interpretatie|D|1",
             "reden": uit["stop"]["reden"]}
        ]  # fmt: skip

    def test_na_een_kritieke_run_vertrekt_geen_aanroep_meer(self, tmp_path):
        """Duurzaam: ook een herstart (nieuw proces, bestaand grootboek) start niets."""

        def antwoord(naam, _n, verg):
            ruw = _d_juist(verg, ("Uitleen:",)) if naam == "D" else _juist(naam, verg)
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        omg = _omgeving8(provider)
        pad = _i_invoer(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="kritieke run"):
            _i18(omg, tmp_path, pad)
        (geval,) = [g for g in _grootboekregels(tmp_path, "geval")
                    if g["poging"] == "interpretatie|D|1"]  # fmt: skip
        assert "kritieke run" in geval["inhoudelijke_stop"]
        assert geval["details"]["niet_gestart"] == 5
        for _ in range(2):
            with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
                _i18(omg, tmp_path, pad, nieuw=False)
        assert len(provider.berichten) == 7
        assert len(_grootboekregels(tmp_path, "reservering")) == 7
        # Ook het grootboek zelf weigert elke volgende reservering in de fase.
        boek = gb.Grootboek.open(_opslag18(tmp_path).grootboek, gb.R18)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            boek.controleer_fasestart("interpretatie")

    def test_afkeur_bij_de_laatste_run_stopt_zonder_resterende_aanroepen(
        self, tmp_path
    ):
        """Aanvulling v4: E is niet meer lexicaal kritiek; de laatste run (E3) stopt
        de proef nog wel deterministisch, hier via de M-d-afkeur (vierde misser)."""

        def antwoord(naam, n, verg):
            if naam == "C" or (naam == "E" and n == 3):
                return "geen json"
            return json.dumps(_juist(naam, verg), ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        with pytest.raises(gb.BudgetSchendingError, match="M-d"):
            _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert len(provider.berichten) == 12
        stop = _samenvatting_i(tmp_path)["stop"]
        assert (stop["run"], stop["niet_gestart"]) == ("interpretatie|E|3", 0)

    def test_m_d_afkeur_stopt_zodra_elf_niet_meer_haalbaar_is(self, tmp_path):
        """Deel C: 'Ook bij M-d ≤ 8/12 stopt de proef' — na de vierde M-d-misser."""

        def antwoord(naam, n, verg):
            if naam == "C" or (naam == "D" and n == 1):
                return "geen json"
            return json.dumps(_juist(naam, verg), ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        with pytest.raises(gb.BudgetSchendingError, match="M-d"):
            _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert len(provider.berichten) == 7
        uit = _samenvatting_i(tmp_path)
        assert (uit["stop"]["run"], uit["stop"]["niet_gestart"]) == (
            "interpretatie|D|1",
            5,
        )
        assert uit["proefoordeel"]["kritiek"] == []
        assert uit["proefoordeel"]["oordeel"] == "afgekeurd"

    def test_m_d_afkeur_telt_ook_runs_uit_een_eerdere_start(self, tmp_path):
        """De M-d-telling komt uit het grootboek, niet alleen uit dit proces."""

        def antwoord(naam, n, verg):
            if naam == "C" or (naam == "D" and n == 1):
                return "geen json"
            return json.dumps(_juist(naam, verg), ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        omg = _omgeving8(provider)
        pad = _i_invoer(tmp_path)
        _i18(omg, tmp_path, pad, max_calls=5)  # A1–A3, C1, C2: nog geen afkeur
        with pytest.raises(gb.BudgetSchendingError, match="M-d"):
            _i18(omg, tmp_path, pad, nieuw=False)
        assert len(provider.berichten) == 7

    def test_stop_in_r18a_laat_r18b_uitvoerbaar(self, tmp_path):
        """De inhoudelijke stop geldt voor de eigen fase (aanvulling C1)."""

        def antwoord(naam, _n, verg):
            ruw = _d_juist(verg, ("Uitleen:",)) if naam == "D" else _juist(naam, verg)
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        omg = _omgeving8(provider)
        i_pad = _i_invoer(tmp_path)
        l_pad, _ = _l_invoer(tmp_path)
        proef = dataclasses.replace(
            runner.PROEVEN["R18"],
            i_invoer_sha256=_sha(i_pad),
            l_invoer_sha256=_sha(l_pad),
        )
        with pytest.raises(gb.BudgetSchendingError, match="kritieke run"):
            _i18(omg, tmp_path, i_pad, proef=proef)
        uit = asyncio.run(
            runner.voer_l_fase(omg, gevallenpad=l_pad, uitmap=tmp_path / "uit",
                               opslag=_opslag18(tmp_path), proef=proef,
                               freeze=_freeze(omg, tmp_path, proef, "l"),
                               voorganger_opslag=_bestaande_keten18(tmp_path))
        )  # fmt: skip
        assert uit["aanroepen_gestart"] == 6
        assert uit["grootboek_na"]["per_fase"] == {
            "interpretatie": 7,
            "lokale_verificatie": 6,
        }

    def test_inhoudelijke_stop_alleen_voor_r18(self, tmp_path):
        boek = _r17_boek(tmp_path)
        assert gb.R18.inhoudelijke_stop is True
        assert [
            n for n, p in runner.PROEVEN.items() if p.identiteit.inhoudelijke_stop
        ] == ["R18"]
        with pytest.raises(gb.BudgetSchendingError, match="inhoudelijke stop"):
            boek.registreer_geval("bewijsregels", "bewijsregels|A|1",
                                  geaccepteerd=False, reden="x",
                                  technisch_afgerond=True, stop="kritiek")  # fmt: skip

    def _alle_e(self, tmp_path, maak):
        """Alle drie E-runs met `maak(vergelijking)`; A, C en D juist."""

        def antwoord(naam, n, verg):
            ruw = maak(verg) if naam == "E" else _juist(naam, verg)
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        uit = _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert uit["aanroepen_gestart"] == 12 and uit["stop"] is None
        return uit

    @pytest.mark.parametrize(
        "voorwaarden",
        [["bij afwezigheid van storing"], ["bij storing", "deze voorwaarde is optioneel"],
         ["bij storing", "als storing ontbreekt"], ["bij storing", "of op verzoek"],
         ["bij storing"]],
    )  # fmt: skip
    def test_e_met_voorwaarde_wacht_op_chris_geen_12_van_12(
        self, tmp_path, voorwaarden
    ):
        """Hercontroles v2/v3 (aanhef en combinaties) en de juiste formulering:
        de fase wacht op het oordeel van Chris, nooit automatisch 12/12."""
        uit = self._alle_e(
            tmp_path, lambda v: _e(v, ("bevestigd", ["Uitleen:"], voorwaarden))
        )
        oordeel = uit["proefoordeel"]
        assert oordeel["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert (oordeel["m_d_juist"], oordeel["e_voorwaarde_behouden"]) == (9, [0, 3])
        assert [h["sleutel"] for h in oordeel["handmatig_beoordelen"]] == [
            f"interpretatie|E|{n}" for n in (1, 2, 3)
        ]
        assert oordeel["kritiek"] == []

    def test_verwijzend_m_kenmerk_naast_exacte_voorwaarde_wacht(self, tmp_path):
        """Hercontrole v3: 'geldigheid van deze voorwaarde' = 'optioneel'."""

        def maak(v):
            ruw = _e_met_m(v, "optioneel", kenmerk="geldigheid van deze voorwaarde")
            (k2,) = [a for a in ruw["antwoorden"]
                     if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"]  # fmt: skip
            k2["voorwaarden"] = ["bij storing"]
            return ruw

        oordeel = self._alle_e(tmp_path, maak)["proefoordeel"]
        assert oordeel["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert oordeel["e_voorwaarde_behouden"] == [0, 3]

    @pytest.mark.parametrize(
        "waarde", ["ook zonder storing", "storing is optioneel", "alleen bij storing"]
    )
    def test_e_als_m_kenmerk_is_automatisch_niet_geslaagd_zonder_stop(
        self, tmp_path, waarde
    ):
        """Zonder onverwerkte voorwaarde geeft bepaal review_required: M-d fout, dus
        deterministisch niet geslaagd; geen lexicale kritiek en geen stop meer."""
        uit = self._alle_e(tmp_path, lambda v: _e_met_m(v, waarde))
        e1 = next(r for r in _records(tmp_path) if r["sleutel"] == "interpretatie|E|1")
        assert e1["score"]["voorwaarde_status"] == "handmatig_beoordelen"
        assert e1["runoordeel"]["categorie"] == "niet_geslaagd"
        assert e1["acceptatie"]["geaccepteerd"] is False
        oordeel = uit["proefoordeel"]
        assert (oordeel["oordeel"], oordeel["m_d_juist"]) == ("tussengebied", 9)
        assert oordeel["handmatig_beoordelen"] == [] and oordeel["kritiek"] == []

    def test_weggevallen_voorwaarde_is_automatisch_niet_geslaagd(self, tmp_path):
        def antwoord(naam, n, verg):
            if naam == "E" and n == 2:
                ruw = _e(verg, ("bevestigd", ["Uitleen:"]))
            else:
                ruw = _juist(naam, verg)
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        uit = _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert uit["aanroepen_gestart"] == 12 and uit["stop"] is None
        (e2,) = [r for r in _records(tmp_path) if r["sleutel"] == "interpretatie|E|2"]
        assert e2["score"]["m_d"]["uitkomst"] == "review_required"
        assert e2["score"]["m_d"]["ok"] is False
        assert (e2["runoordeel"]["categorie"], e2["runoordeel"]["kritiek"]) == (
            "niet_geslaagd",
            [],
        )
        oordeel = uit["proefoordeel"]
        assert oordeel["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert [h["sleutel"] for h in oordeel["handmatig_beoordelen"]] == [
            "interpretatie|E|1",
            "interpretatie|E|3",
        ]

    def test_alleen_buiten_bereik_wacht_ook_op_chris(self, tmp_path):
        uit = self._alle_e(
            tmp_path,
            lambda v: _e(v, ("bevestigd", ["Uitleen:"]),
                         buiten_bereik=[{"citaat": "bij storing", "reden": "voorwaardelijk"}]),
        )  # fmt: skip
        assert uit["proefoordeel"]["oordeel"] == "wacht_op_handmatige_beoordeling"

    def test_f7_is_apart_niet_geslaagd_en_niet_kritiek(self, tmp_path):
        def antwoord(naam, n, verg):
            ruw = _juist(naam, verg)
            if naam == "A" and n == 1:
                (k2,) = [a for a in ruw["antwoorden"]
                         if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"]  # fmt: skip
                k2.update(toestand="ontkend", citaten=[_u(verg, BUUR)])
            return json.dumps(ruw, ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        uit = _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        (a1,) = [r for r in _records(tmp_path) if r["sleutel"] == "interpretatie|A|1"]
        assert a1["score"]["m_d"]["uitkomst"] == "pass"
        assert a1["runoordeel"]["categorie"] == "f7"
        assert a1["runoordeel"]["kritiek"] == []
        assert a1["acceptatie"]["geaccepteerd"] is False
        assert uit["proefoordeel"]["f7"] == [
            {
                "sleutel": "interpretatie|A|1",
                "afwijkingen": ["kosteloos/verhuur: ['ontkend']"],
            }
        ]
        assert uit["proefoordeel"]["kritiek"] == []
        # Aanvulling v4: de E-runs wachten op Chris; dat gaat vóór het F7-besluit.
        assert uit["proefoordeel"]["oordeel"] == "wacht_op_handmatige_beoordeling"

    def test_onleesbare_uitvoer_is_modelfout_en_geen_stop(self, tmp_path):
        def antwoord(naam, n, verg):
            if naam == "C" and n == 1:
                return "geen json"
            return json.dumps(_juist(naam, verg), ensure_ascii=False)

        provider = _R18Provider(_items(), antwoord=antwoord)
        uit = _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert uit["aanroepen_gestart"] == 12
        (c1,) = [r for r in _records(tmp_path) if r["sleutel"] == "interpretatie|C|1"]
        assert c1["score"] is None
        assert c1["dienstuitkomst"] == {
            "uitkomst": "error",
            "fout": "malformed_response",
        }
        assert c1["runoordeel"]["categorie"] == "geen_interpretatie"
        assert c1["afsluitstatus"] == "modelfout"
        assert c1["acceptatie"]["technisch_afgerond"] is True
        # Aanvulling v4: M-d telt E pas na het oordeel van Chris (8 + 3 wachtend).
        assert uit["proefoordeel"]["m_d_juist"] == 8
        assert uit["proefoordeel"]["oordeel"] == "wacht_op_handmatige_beoordeling"

    def test_technische_fout_stopt_duurzaam_zonder_retry(self, tmp_path):
        provider = _R18Provider(_items(), fout_bij=2)
        omg = _omgeving8(provider)
        pad = _i_invoer(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match=r"niet geaccepteerd|gestopt"):
            _i18(omg, tmp_path, pad)
        assert len(provider.berichten) == 2
        # Geen tweede poging en geen doorloop: de proef blijft gestopt.
        with pytest.raises(gb.BudgetSchendingError):
            _i18(omg, tmp_path, pad, nieuw=False)
        assert len(provider.berichten) == 2
        assert len(_grootboekregels(tmp_path, "reservering")) == 2

    def test_providerweigering_stopt(self, tmp_path):
        provider = _R18Provider(_items(), stop="refusal")
        with pytest.raises(gb.BudgetSchendingError):
            _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
        assert len(provider.berichten) == 1

    def test_geen_tweede_poging_per_sleutel(self, tmp_path):
        provider = _R18Provider(_items())
        omg = _omgeving8(provider)
        pad = _i_invoer(tmp_path)
        _i18(omg, tmp_path, pad)
        tweede = _i18(omg, tmp_path, pad, nieuw=False)
        assert tweede["aanroepen_gestart"] == 0
        assert tweede["overgeslagen_al_gereserveerd"] == 12
        assert len(provider.berichten) == 12

    def test_dertiende_run_boven_de_fasecap_geweigerd(self, tmp_path):
        data = _invoerdata()
        data["items"][0]["herhalingen"] = 4
        pad = _i_invoer(tmp_path, data)
        provider = _R18Provider(_items())
        with pytest.raises(gb.BudgetSchendingError, match="13 calls"):
            _i18(_omgeving8(provider), tmp_path, pad)
        assert provider.berichten == []

    def test_technische_herhaling_geweigerd(self, tmp_path):
        provider = _R18Provider(_items())
        with pytest.raises(gb.BudgetSchendingError, match="technische herhaling"):
            _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path),
                 technische_herhalingen=("interpretatie|A|1",))  # fmt: skip
        assert provider.berichten == []

    def test_andere_invoer_dan_de_gepinde_geweigerd(self, tmp_path):
        provider = _R18Provider(_items())
        pad = _i_invoer(tmp_path)
        proef = runner.PROEVEN["R18"]  # gepind op de echte R18-invoer
        with pytest.raises(gb.BudgetSchendingError, match="interpretatie-invoer"):
            _i18(_omgeving8(provider), tmp_path, pad, proef=proef)
        assert provider.berichten == []

    def test_afwijkend_contract_geweigerd(self, tmp_path):
        provider = _R18Provider(_items())
        pad = _i_invoer(tmp_path)
        proef = dataclasses.replace(
            runner.PROEVEN["R18"], i_invoer_sha256=_sha(pad),
            bewijsregel_contract={**runner.R18_BEWIJSREGEL_CONTRACT,
                                  "interpretation_prompt_version": "anders"},
        )  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            _i18(_omgeving8(provider), tmp_path, pad, proef=proef)
        assert provider.berichten == []


# --- R18B: lokale controle uit de herbonden R17-interpretaties --------------------------------


def _l_items() -> list[dict]:
    """De zes pakketten zoals de R18B-maker, op vooraf opgestelde interpretaties."""
    items = _items()
    uit = []
    for item in items[:2]:  # A en C
        vergelijking = mk18.vergelijkingsinvoer(item)
        ruw = _juist(item["id"], vergelijking)
        if item["id"] == "C":
            # Zoals gecorrigeerd-R17-C: een ander bovenbegrip, dus een eigen kernpakket.
            ruw["kern"][
                "bovenbegrip"
            ] = "ter beschikking stellen van apparatuur aan een medewerker"
        interpretatie = br.valideer_interpretatie(ruw, vergelijking)
        uit += mk18b.lokale_items(item["id"], item, interpretatie, vergelijking,
                                  {"interpretatie": "test"})  # fmt: skip
    return uit


def _l_invoer(tmp_path: Path, items=None) -> tuple[Path, list[dict]]:
    items = _l_items() if items is None else items
    pad = tmp_path / "l-invoer.json"
    pad.write_text(
        json.dumps({"schema": mk18b.INVOERSCHEMA, "items": items}), encoding="utf-8"
    )
    return pad, items


def _l18(omg, tmp_path, *, items=None, **kw):
    pad, _ = _l_invoer(tmp_path, items)
    proef = dataclasses.replace(runner.PROEVEN["R18"], l_invoer_sha256=_sha(pad))
    return asyncio.run(
        runner.voer_l_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag18(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef, "l"),
            voorganger_opslag=_keten18(tmp_path)[1],
            nieuw_grootboek=True,
            **kw,
        )
    )


class TestLokaleFase:
    def test_zes_pakketten_kern_doel_buur_gelabeld(self):
        items = _l_items()
        assert [i["id"] for i in items] == [
            "A-kern", "A-doel", "A-buur", "C-kern", "C-doel", "C-buur",
        ]  # fmt: skip
        for item in items:
            assert (item["soort"], item["verwacht"]) == ("positief", "supported")
            assert item["herkomst"]["label"] == LABEL
            assert item["binding"]["regelversie"] == "ess05-bewijsregels/6"
            assert item["specificatie"]["rol"] == "material"
        valide = runner.valideer_l_invoer(
            {"schema": mk18b.INVOERSCHEMA, "items": items},
            _omgeving8(_BewijsProvider()),
        )
        assert [li.sleutel for li in valide] == [
            f"lokale_verificatie|{i['id']}|1" for i in items
        ]

    def test_zes_controles_elk_eenmaal_supported(self, tmp_path):
        provider = _R18Provider(_items())
        uit = _l18(_omgeving8(provider), tmp_path)
        assert uit["aanroepen_gestart"] == 6
        assert uit["grootboek_na"]["per_fase"] == {
            "interpretatie": 0,
            "lokale_verificatie": 6,
        }
        assert [r["gekregen"] for r in uit["resultaten"]] == ["supported"] * 6
        assert all(r["geaccepteerd"] for r in uit["resultaten"])
        assert len(provider.berichten) == 6
        assert interpretatiesysteemprompt() not in {s for s, _ in provider.berichten}

    def test_zevende_pakket_boven_de_fasecap_geweigerd(self, tmp_path):
        items = _l_items()
        extra = copy.deepcopy(items[0])
        items.append(extra)
        extra["id"] = "A-kern-2"
        # Een ander pakket (unieke hash) met dezelfde, geldige opbouw.
        extra["specificatie"]["uitspraak"] = extra["pakket"]["uitspraak"] = (
            extra["pakket"]["uitspraak"] + " Extra."
        )
        from domain.ess05 import lokale_controle as lc
        from services.validation.ess05_local_verification_service import (
            bouw_lokale_prompt,
        )
        from services.validation.ess05_verification_service import prompthash

        materiaal, buren, _ = runner.mig.verificatiemateriaal(extra["geval"])
        pakket = runner._l_pakket(extra["specificatie"], materiaal,
                                  {b.id: b.term for b in buren})  # fmt: skip
        extra.update(pakket=dict(pakket.inhoud), pakket_hash=pakket.hash,
                     binding=dict(pakket.binding),
                     prompt_sha256=prompthash(*bouw_lokale_prompt(pakket)))  # fmt: skip
        assert isinstance(pakket, lc.Lokaalpakket)
        provider = _R18Provider(_items())
        with pytest.raises(gb.BudgetSchendingError, match="7 calls"):
            _l18(_omgeving8(provider), tmp_path, items=items)
        assert provider.berichten == []

    def test_l_fase_bindt_het_bewijsregelcontract_van_r18(self, tmp_path):
        pad, _ = _l_invoer(tmp_path)
        proef = dataclasses.replace(
            runner.PROEVEN["R18"], l_invoer_sha256=_sha(pad),
            bewijsregel_contract={**runner.R18_BEWIJSREGEL_CONTRACT,
                                  "render_version": "anders"},
        )  # fmt: skip
        omg = _omgeving8(_BewijsProvider())
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            asyncio.run(
                runner.voer_l_fase(omg, gevallenpad=pad, uitmap=tmp_path / "uit",
                                   opslag=_opslag18(tmp_path), proef=proef)
            )  # fmt: skip

    def test_naar_eenheden_faalt_dicht(self):
        item = _items()[0]
        vergelijking = mk18.vergelijkingsinvoer(item)
        ruw = {"antwoorden": [{"citaten": [{"material_id": "definition",
                                            "citaat": "tijdelijk"}]}],
               "buurgroepen": []}  # fmt: skip
        with pytest.raises(mk18b.MakerfoutError, match="eenheden"):
            mk18b.naar_eenheden(ruw, vergelijking)
        ruw["antwoorden"][0]["citaten"] = [
            {"material_id": mk18b.BRON_ID, "citaat": "de medewerker geeft de apparatuur daarna terug"}
        ]  # fmt: skip
        with pytest.raises(mk18b.MakerfoutError, match="eenduidig"):
            mk18b.naar_eenheden(ruw, vergelijking)

    def test_dubbel_pakket_is_een_makerfout(self):
        items = _l_items()
        mk18b.controleer_uniek(items)
        with pytest.raises(mk18b.MakerfoutError, match="dubbel"):
            mk18b.controleer_uniek([*items, copy.deepcopy(items[0])])
        tweeling = copy.deepcopy(items[0])
        tweeling["id"] = "C-kern-2"
        with pytest.raises(mk18b.MakerfoutError, match="dubbel"):
            mk18b.controleer_uniek([*items, tweeling])

    def test_doel_wordt_niet_overschreven(self, tmp_path):
        doel = tmp_path / "l.json"
        doel.write_text("bestaand", encoding="utf-8")
        with pytest.raises(FileExistsError):
            mk18b.main(["--doel", str(doel)])
        assert doel.read_text(encoding="utf-8") == "bestaand"


@r18_invoer_nodig
class TestEchteInvoer:
    def test_i_invoer_gepind_en_gelijk_aan_de_maker(self):
        assert _sha(I18) == runner.R18_I_INVOER_SHA256 == I18_SHA256
        tekst = json.dumps(mk18.maak_bewijsregel_invoer(), ensure_ascii=False, indent=2)
        assert I18.read_text(encoding="utf-8") == tekst + "\n"

    def test_l_invoer_gepind_en_gelijk_aan_de_maker(self):
        assert _sha(L18) == runner.R18_L_INVOER_SHA256
        tekst = json.dumps(mk18b.maak_lokale_invoer(), ensure_ascii=False, indent=2)
        assert L18.read_text(encoding="utf-8") == tekst + "\n"

    def test_l_invoer_zes_pakketten_uit_de_herbonden_r17_interpretaties(self):
        data = json.loads(L18.read_text(encoding="utf-8"))
        assert data["schema"] == "def768-ess05-lokale-invoer/1"
        assert [i["id"] for i in data["items"]] == [
            "A-kern", "A-doel", "A-buur", "C-kern", "C-doel", "C-buur",
        ]  # fmt: skip
        assert LABEL in data["status"]
        for item in data["items"]:
            herkomst = item["herkomst"]
            assert herkomst["label"] == LABEL
            naam = item["id"][0]
            assert herkomst["interpretatie"]["pad"].endswith(
                f"gecorrigeerd-R17-{naam}.json"
            )
            assert (
                _sha(ROOT / herkomst["interpretatie"]["pad"])
                == herkomst["interpretatie"]["sha256"]
            )
        runner.valideer_l_invoer(data, _omgeving8(_BewijsProvider()))

    def test_historische_r17_bestanden_ongewijzigd(self):
        for pad, sha in mk18b.GECORRIGEERD.values():
            assert _sha(pad) == sha
        assert _sha(mk18b.R17_INVOER) == mk18b.R17_INVOER_SHA256

    def test_i_invoer_valideert_tegen_de_huidige_code(self):
        data = json.loads(I18.read_text(encoding="utf-8"))
        items = runner.valideer_i_invoer(data, _omgeving8(_BewijsProvider()))
        assert len(items) == 12

    def test_v1_blijft_staan_maar_wordt_geweigerd(self, tmp_path):
        """Aanvulling C3/v2: de runner pint -v3; -v1 weigert op hash, schema en orakel."""
        assert _sha(I18_V1) == I18_V1_SHA256 != runner.R18_I_INVOER_SHA256
        data = json.loads(I18_V1.read_text(encoding="utf-8"))
        omg = _omgeving8(_BewijsProvider())
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_i_invoer(data, omg)
        data["schema"] = mk18.INVOERSCHEMA
        with pytest.raises(pi.InvoerfoutError, match="orakel"):
            runner.valideer_i_invoer(data, omg)
        provider = _R18Provider(_items())
        with pytest.raises(gb.BudgetSchendingError, match="interpretatie-invoer"):
            _i18(_omgeving8(provider), tmp_path, I18_V1, proef=runner.PROEVEN["R18"])
        assert provider.berichten == []
        with pytest.raises(gb.BudgetSchendingError, match="interpretatie-invoer"):
            asyncio.run(runner.droogrun("interpretatie", I18_V1, tmp_path,
                                        proef=runner.PROEVEN["R18"]))  # fmt: skip

    @pytest.mark.parametrize(
        ("pad", "sha"),
        [(I18_V2, I18_V2_SHA256), (I18_V3, I18_V3_SHA256), (I18_V4, I18_V4_SHA256)],
        ids=["v2", "v3", "v4"],
    )
    def test_oudere_invoer_blijft_staan_maar_wordt_geweigerd(self, tmp_path, pad, sha):
        """Aanvulling v2–v4: de runner pint -v5; -v2 t/m -v4 weigeren op schema en hash."""
        assert _sha(pad) == sha != runner.R18_I_INVOER_SHA256
        data = json.loads(pad.read_text(encoding="utf-8"))
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_i_invoer(data, _omgeving8(_BewijsProvider()))
        provider = _R18Provider(_items())
        with pytest.raises(gb.BudgetSchendingError, match="interpretatie-invoer"):
            _i18(_omgeving8(provider), tmp_path, pad, proef=runner.PROEVEN["R18"])
        assert provider.berichten == []
        with pytest.raises(gb.BudgetSchendingError, match="interpretatie-invoer"):
            asyncio.run(runner.droogrun("interpretatie", pad, tmp_path,
                                        proef=runner.PROEVEN["R18"]))  # fmt: skip

    def test_droog_i_fase_zonder_netwerk_en_zonder_grootboek(self, tmp_path):
        uit = asyncio.run(
            runner.droogrun("interpretatie", I18, tmp_path, proef=runner.PROEVEN["R18"])
        )
        assert uit["echte_calls"] == 0 and uit["geplande_calls"] == 12
        assert uit["freezevelden"]["groep"] == "i"
        assert uit["freezevelden"]["dataset_sha256"] == I18_SHA256
        assert not runner.PROEVEN["R18"].opslag.grootboek.exists()


# --- runoordeel en proefoordeel (deel C) ------------------------------------------------------


def _score(**over) -> dict:
    basis = {
        "m_a": {"items": 0, "fouten": []},
        "m_b_dragend_ok": True,
        "m_c_dragend_ok": True,
        "m_b_dragend_ok_zonder_f7": True,
        "m_c_dragend_ok_zonder_f7": True,
        "m_d": {"uitkomst": "pass", "fout": None, "verwacht": ["pass"], "ok": True},
        "voorwaarde_behouden": None,
        "voorwaarde_status": None,
        "f7_afwijkingen": [],
        "feiten": [],
    }
    for k, v in over.items():
        basis[k] = v
    if "voorwaarde_status" in over:
        basis["voorwaarde_behouden"] = over["voorwaarde_status"] == "behouden"
    return basis


class TestRunoordeel:
    def test_geslaagd(self):
        o = bs.runoordeel(_score(), ORAKEL_D)
        assert (o["categorie"], o["m_d_telt"], o["kritiek"]) == ("geslaagd", True, [])

    @pytest.mark.parametrize("uitkomst", ["pass", "fail"])
    @pytest.mark.parametrize(
        ("maat", "reden"),
        [
            ("m_c_dragend_ok_zonder_f7", "pass/fail bij M-c onwaar"),
            ("m_b_dragend_ok_zonder_f7", "pass/fail bij M-b onwaar"),
        ],
    )
    def test_pass_of_fail_zonder_dragend_bewijs_is_kritiek(self, uitkomst, maat, reden):
        score = _score(**{maat: False, "m_d": {"uitkomst": uitkomst, "fout": None,
                                               "verwacht": ["pass"], "ok": uitkomst == "pass"}})  # fmt: skip
        o = bs.runoordeel(score, ORAKEL_D)
        assert o["categorie"] == "kritiek" and o["kritiek"] == [reden]

    def test_review_required_zonder_dragend_bewijs_is_niet_kritiek(self):
        score = _score(m_b_dragend_ok=False, m_b_dragend_ok_zonder_f7=False,
                       m_d={"uitkomst": "review_required", "fout": None,
                            "verwacht": ["review_required"], "ok": True})  # fmt: skip
        o = bs.runoordeel(score, ORAKEL_A)
        assert (o["categorie"], o["kritiek"]) == ("niet_geslaagd", [])

    @pytest.mark.parametrize(
        "status", ["behouden", "ontkend", "weggevallen", "handmatig_beoordelen", None]
    )
    def test_e_met_juiste_uitkomst_wacht_altijd_op_chris(self, status):
        """Aanvulling v4: welke status de score ook claimt, E met error/buiten_bereik
        wacht op het oordeel van Chris; M-d telt pas na dat oordeel."""
        orakel = mk18.ORAKELS["E"]
        md = {"uitkomst": "error", "fout": "buiten_bereik",
              "verwacht": orakel["uitkomst"], "ok": True}  # fmt: skip
        o = bs.runoordeel(_score(m_d=md, voorwaarde_status=status), orakel)
        assert (o["categorie"], o["m_d_telt"], o["kritiek"]) == (
            "handmatig_beoordelen",
            False,
            [],
        )
        assert o["handmatig"] == [bs.HANDMATIG_E]
        assert (o["voorwaarde_status"], o["voorwaarde_behouden"]) == (
            "handmatig_beoordelen",
            False,
        )

    @pytest.mark.parametrize(
        ("uitkomst", "fout"),
        [
            ("review_required", None),
            ("pass", None),
            ("fail", None),
            ("error", "schemafout"),
        ],
    )
    @pytest.mark.parametrize("status", ["behouden", "ontkend", "weggevallen"])
    def test_e_met_m_d_fout_is_automatisch_niet_geslaagd(self, uitkomst, fout, status):
        orakel = mk18.ORAKELS["E"]
        md = {"uitkomst": uitkomst, "fout": fout, "verwacht": orakel["uitkomst"],
              "ok": False}  # fmt: skip
        o = bs.runoordeel(_score(m_d=md, voorwaarde_status=status), orakel)
        assert (o["categorie"], o["m_d_telt"], o["kritiek"], o["handmatig"]) == (
            "niet_geslaagd",
            False,
            [],
            [],
        )

    def test_f7_apart(self):
        score = _score(m_b_dragend_ok=False, m_c_dragend_ok=False,
                       f7_afwijkingen=["kosteloos/verhuur: ['ontkend']"],
                       m_d={"uitkomst": "pass", "fout": None,
                            "verwacht": ["review_required"], "ok": False})  # fmt: skip
        o = bs.runoordeel(score, ORAKEL_A)
        assert (o["categorie"], o["kritiek"]) == ("f7", [])

    def test_f7_met_ander_kritiek_feit_blijft_kritiek(self):
        score = _score(m_b_dragend_ok=False, m_b_dragend_ok_zonder_f7=False,
                       f7_afwijkingen=["kosteloos/verhuur: ['ontkend']"])  # fmt: skip
        assert bs.runoordeel(score, ORAKEL_A)["categorie"] == "kritiek"

    def test_zonder_score_geen_interpretatie(self):
        o = bs.runoordeel(None, ORAKEL_A)
        assert (o["categorie"], o["m_d_telt"]) == ("geen_interpretatie", False)


def _run(categorie="geslaagd", *, m_d=True, m_b=True, m_c=True, e=None, **over):
    return {"sleutel": over.pop("sleutel", "x"), "categorie": categorie,
            "m_d_telt": m_d, "m_b_dragend_ok": m_b, "m_c_dragend_ok": m_c,
            "voorwaarde_behouden": e,
            "voorwaarde_status": None if e is None else ("behouden" if e else "weggevallen"),
            "kritiek": over.pop("kritiek", []), "f7": over.pop("f7", []),
            "handmatig": over.pop("handmatig", [])}  # fmt: skip


class TestProefoordeel:
    def _runs(self, n_md=12, **kw):
        runs = [_run(e=True if i >= 9 else None) for i in range(12)]
        for r in runs[n_md:]:
            r.update(categorie="niet_geslaagd", m_d_telt=False)
        return runs

    def test_geslaagd_vanaf_11(self):
        assert bs.proefoordeel(self._runs(12))["oordeel"] == "geslaagd"
        assert bs.proefoordeel(self._runs(11))["oordeel"] == "geslaagd"

    @pytest.mark.parametrize(("n", "oordeel"), [(10, "tussengebied"), (9, "tussengebied"),
                                                (8, "afgekeurd"), (0, "afgekeurd")])  # fmt: skip
    def test_grenzen_m_d(self, n, oordeel):
        assert bs.proefoordeel(self._runs(n))["oordeel"] == oordeel

    def test_m_c_of_m_b_niet_12_is_niet_geslaagd(self):
        runs = self._runs(12)
        runs[0].update(m_c_dragend_ok=False, categorie="niet_geslaagd")
        assert bs.proefoordeel(runs)["oordeel"] == "tussengebied"

    def test_een_kritieke_run_keurt_af(self):
        runs = self._runs(12)
        runs[3].update(
            categorie="kritiek", kritiek=["pass/fail bij M-b onwaar"], sleutel="k"
        )
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] == "afgekeurd"
        assert uit["kritiek"] == [
            {"sleutel": "k", "redenen": ["pass/fail bij M-b onwaar"]}
        ]

    def test_e_voorwaarde_3_van_3_vereist(self):
        runs = self._runs(12)
        runs[11].update(voorwaarde_behouden=False, categorie="kritiek",
                        kritiek=["E: voorwaarde weggevallen"])  # fmt: skip
        uit = bs.proefoordeel(runs)
        assert uit["e_voorwaarde_behouden"] == [2, 3]
        assert uit["oordeel"] == "afgekeurd"

    def test_f7_wacht_op_besluit(self):
        runs = self._runs(12)
        runs[0].update(categorie="f7", m_c_dragend_ok=False, m_d_telt=False,
                       f7=["kosteloos/verhuur: ['ontkend']"], sleutel="a")  # fmt: skip
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] == "wacht_op_f7_besluit"
        assert uit["f7"] == [
            {"sleutel": "a", "afwijkingen": ["kosteloos/verhuur: ['ontkend']"]}
        ]

    def _handmatig(self, runs, *indexen):
        for i in indexen:
            runs[i].update(categorie="handmatig_beoordelen", m_d_telt=False,
                           voorwaarde_behouden=False,
                           voorwaarde_status="handmatig_beoordelen",
                           handmatig=[bs.HANDMATIG_E],
                           sleutel=f"interpretatie|E|{i - 8}")  # fmt: skip
        return runs

    def test_handmatige_e_run_apart_en_wacht_op_beoordeling(self):
        uit = bs.proefoordeel(self._handmatig(self._runs(12), 11))
        assert uit["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert uit["handmatig_beoordelen"] == [
            {"sleutel": "interpretatie|E|3", "redenen": [bs.HANDMATIG_E]}
        ]  # fmt: skip
        assert uit["kritiek"] == []
        assert uit["m_d_juist"] == 11
        assert uit["e_voorwaarde_behouden"] == [2, 3]
        assert uit["categorieen"]["handmatig_beoordelen"] == 1

    def test_handmatige_runs_keuren_niet_automatisch_af(self):
        """M-d 9 plus 2 handmatige: niet afgekeurd, maar wachten (die kunnen juist
        blijken); M-d 6 plus 2 handmatige blijft ≤ 8: afgekeurd."""
        runs = self._handmatig(self._runs(11), 9, 10)
        assert sum(r["m_d_telt"] for r in runs) == 9
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] == "wacht_op_handmatige_beoordeling"
        runs = self._handmatig(self._runs(6), 9, 10)
        assert sum(r["m_d_telt"] for r in runs) == 6
        assert bs.proefoordeel(runs)["oordeel"] == "afgekeurd"  # 6 + 2 + 0 ≤ 8

    def test_handmatig_zonder_haalbare_elf_is_tussengebied(self):
        runs = self._handmatig(self._runs(9), 10)  # M-d 9, 1 handmatig: max 10
        assert bs.proefoordeel(runs)["oordeel"] == "tussengebied"

    def test_onvolledig_bij_minder_dan_12_runs(self):
        assert bs.proefoordeel(self._runs(12)[:10])["oordeel"] == "onvolledig"

    def test_statistische_grens_vermeld(self):
        assert "66%" in bs.proefoordeel(self._runs(12))["grens"]
