"""DEF-768 R17 — gerichte echte proef bewijsregels/5 + prompt/3: registratie, offline.

Opdracht Chris 28-09 ("go?", logs/def768/ronde17-gebruikersopdracht-v1.json),
startmandaat logs/def768/ronde17-startmandaat-v1.md en het budgetbesluit
logs/def768/ronde17-bewijsregels-budgetbesluit-v1.json: dezelfde drie gevallen
A/B/C als R16, inhoudelijk ongewijzigd, op de herstelde bewijsregels (v5,
prompt /3). Max 12 stappen (verwacht 9), plafond USD 4,32, cumulatief 396 + 12
= 408 binnen 427, kaderrest USD 21,951255, reserve 0, geen retry/cache.

Sinds bewijsregels v6 (prompt /4, schema /3) is R17 historisch gepind op v5 en
weigert de runner R17 fail-closed (zoals R16); de mechaniek hieronder draait op
het huidige contract.

Alleen de nieuwe registratiebinding wordt hier getoetst; de bewezen
domeinlogica en de R16-runnermechaniek niet opnieuw. De provider is een fake;
geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import sys
from pathlib import Path

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r10_proef import (
    HUIDIG_CONTRACT,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _sha,
)
from tests.unit.scripts.test_def768_r16_bewijsregelproef import (
    B16,
    OUDE_RONDES,
    R16_CONTRACT_V3,
    VERWACHT,
    V,
    W,
    _BewijsProvider,
    _freeze,
    _invoerdata,
    _items,
    _keten16,
    _r8_boek,
    _r9_boek,
    _r10_boek,
    _r11_boek,
    _r12_boek,
    _r13_boek,
    _r14_boek,
    _r15_boek,
    keten_boek,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R17_ID = "DEF-768-AI-20260928-R17"
R17_MAP = ROOT / "reports" / R17_ID
B17 = R17_MAP / "bewijsregel-invoer-v1.json"
LOGS = ROOT / "logs" / "def768"
BESLUIT17 = LOGS / "ronde17-bewijsregels-budgetbesluit-v1.json"
BESLUIT17_SHA256 = "1f825a6daab976b5e4a1a41631a35798fe49ce6a293856a0a456e8e0c0fcfeda"
OPDRACHT17 = LOGS / "ronde17-gebruikersopdracht-v1.json"
MANDAAT17 = LOGS / "ronde17-startmandaat-v1.md"
#: De kop van het afgesloten R16-grootboek (5 calls, 0 open).
R16_KOP_SHA256 = "58f5a17ec921d67e66899882441c8629fae9a41476d3485c697cd3614141cee8"
#: De werkelijke R16-kosten (5 SDK-calls).
R16_KOSTEN_NUSD = 212_380_000
#: USD 25 − werkelijke R8–R16-kosten (USD 3,048745).
KADERREST17_NUSD = 21_951_255_000
#: De gereviewde bewijsregels (v5, prompt /3; HEAD e7000feaf), letterlijk gepind.
R17_CONTRACT = {
    "bewijsregel_version": "ess05-bewijsregels/5",
    "interpretation_schema_version": "ess05-interpretatie/2",
    "render_version": "ess05-bewijsregels-render/2",
    "interpretation_prompt_version": "ess05-interpretatie-prompt/3",
    "interpretation_system_prompt_sha256": (
        "c0f1f856c02da8237fdaaa61d02d84db9788bc9801c72a5737fb25aeb420c687"
    ),
}
#: Velden die de R17-invoer ongewijzigd uit de R16-invoer overneemt.
GEVALVELDEN = (
    "id",
    "variant",
    "synthetisch",
    "label",
    "geval",
    "geval_sha256",
    "materiaal_sha256",
    "buren",
    "onvolledig",
    "verwacht",
    "herkomst",
)

besluit17_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT17, OPDRACHT17, MANDAAT17)),
    reason="git-ignored R17-besluiten ontbreken",
)
r17_invoer_nodig = pytest.mark.skipif(
    not (B17.is_file() and B16.is_file()), reason="git-ignored R16/R17-invoer ontbreekt"
)


def _r16_boek(root: Path, *, kosten: int = R16_KOSTEN_NUSD) -> gb.Grootboek:
    """Een R16-grootboek zoals het echte: A 1, B 1, C 3 stappen, niets geaccepteerd."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R16)
    binding = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
               "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip
    stappen = (("interpretatie", V), ("controle_1", W), ("controle_2", W))
    for naam, n in (("A", 1), ("B", 1), ("C", 3)):
        poging, vorige = f"bewijsregels|{naam}|1", None
        for stap, taak in stappen[:n]:
            res = boek.reserveer("bewijsregels", f"{poging}/{stap}",
                                 invoer_sha256="a" * 64, poging=poging, stap=stap,
                                 vorige_stap=vorige, task_type=taak, binding=binding)  # fmt: skip
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                       kosten_werkelijk_nusd=kosten // 5)  # fmt: skip
            vorige = stap
        boek.registreer_geval("bewijsregels", poging, geaccepteerd=False, reden="r16",
                              technisch_afgerond=True)  # fmt: skip
    return boek


def _keten17(tmp_path: Path):
    r16 = runner.Proefopslag(tmp_path / "r16")
    boek = _r16_boek(r16.root)
    return boek, (r16, *_keten16(tmp_path))


def _opslag17(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r17")


def _b17(omg, tmp_path, pad):
    boek16, keten = _keten17(tmp_path)
    # R17-mechaniek op het huidige contract (R17 zelf is op v5 gepind), zoals
    # _huidig16 bij R16.
    proef = dataclasses.replace(
        runner.PROEVEN["R17"],
        b_invoer_sha256=_sha(pad),
        voorganger_kop_sha256=boek16.samenvatting()["kop_sha256"],
        bewijsregel_contract=runner.bewijsregel_contractidentiteit(),
    )
    return asyncio.run(
        runner.voer_b_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag17(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef),
            voorganger_opslag=keten,
            nieuw_grootboek=True,
        )
    )


# --- identiteit ------------------------------------------------------------------------------


class TestIdentiteit:
    def test_r17_zoals_r16_met_voorganger_r16_en_cumulatief_408(self):
        r17, r16 = gb.R17, gb.R16
        assert r17.proef_id == R17_ID
        assert r17.voorganger is r16
        assert r17.cumulatief_max == 408 == 396 + 12 <= 427
        for veld in ("fasecaps", "reserve_max", "eindgroepen", "bindingsvelden",
                     "modelstappen_per_geval", "kostenbewaking", "fasestappen",
                     "fasevolgorde", "gedeelde_codebinding", "stop_bij_eerste_fout",
                     "kostenkader_nusd", "stop_alleen_technisch",
                     "vroege_stop_toegestaan"):  # fmt: skip
            assert getattr(r17, veld) == getattr(r16, veld), veld
        assert r17.totaal_max == 12 and r17.reserve_max == 0
        assert (
            r17.kostenbewaking.plafond_nusd == gb.begroting_nusd(r17) == 4_320_000_000
        )
        assert r17.kostenbewaking.plafond_nusd <= KADERREST17_NUSD
        assert r17.kostenkader_nusd == 25_000_000_000

    def test_historische_identiteiten_ongewijzigd(self):
        assert (gb.R16.voorganger, gb.R16.cumulatief_max) == (gb.R15, 403)
        assert (gb.R15.totaal_max, gb.R15.cumulatief_max) == (4, 391)

    def test_cumulatief_396_plus_12_past_13_niet(self, tmp_path):
        # Zelfde keten als de R16-cumulatieftest (391 calls), plus R16 (5 calls).
        keten = [
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
        assert sum(b.samenvatting()["totaal"] for b in keten) == 396
        boek = gb.Grootboek.nieuw(_opslag17(tmp_path).grootboek, gb.R17)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="408"):
            gb.controleer_cumulatief(boek, keten, 13)

    @pytest.mark.skipif(
        not all(
            runner.PROEVEN[n].opslag.grootboek.is_file() for n in (*OUDE_RONDES, "R16")
        ),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_396_calls_usd_3_048745_en_r16_kop(self, tmp_path):
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed((*OUDE_RONDES, "R16"))
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 396
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:9])
        assert lopend == 3_048_745_000 == 25_000_000_000 - KADERREST17_NUSD
        assert keten[0].kostenstand()["lopend_nusd"] == R16_KOSTEN_NUSD
        assert keten[0].samenvatting()["onafgesloten"] == 0
        assert keten[0].samenvatting()["kop_sha256"] == R16_KOP_SHA256
        runner._controleer_voorgangerkop(runner.PROEVEN["R17"], tuple(keten))
        boek = gb.Grootboek.nieuw(_opslag17(tmp_path).grootboek, gb.R17)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="408"):
            gb.controleer_cumulatief(boek, keten, 13)


# --- registratie en besluit ------------------------------------------------------------------


class TestRegistratie:
    def test_r17_geregistreerd_op_het_gereviewde_contract(self):
        proef = runner.PROEVEN["R17"]
        assert proef.identiteit is gb.R17
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R17_MAP
        assert proef.b_invoer_sha256 == runner.R17_B_INVOER_SHA256
        assert (proef.t_ontwikkelinvoer_sha256, proef.v_invoer_sha256,
                proef.l_invoer_sha256) == (None, None, None)  # fmt: skip
        assert (proef.budgetbesluit, proef.budgetbesluit_sha256) == (
            BESLUIT17,
            BESLUIT17_SHA256,
        )
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == HUIDIG_CONTRACT
        assert dict(proef.lokaal_contract) == dict(runner.R15_LOKAAL_CONTRACT)
        # Historisch gepind op v5; de huidige code (v6) draagt dat contract niet meer.
        assert dict(proef.bewijsregel_contract) == R17_CONTRACT
        assert runner.bewijsregel_contractidentiteit() != R17_CONTRACT
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST17_NUSD
        assert proef.voorganger_kop_sha256 == R16_KOP_SHA256 == runner.R16_KOP_SHA256
        runner._controleer_contract(_omgeving8(_BewijsProvider()), proef)
        runner._controleer_lokaal_contract(proef)
        with pytest.raises(gb.BudgetSchendingError, match="geen call gestart"):
            runner._controleer_bewijsregel_contract(proef)

    def test_r16_registratie_historisch_ongewijzigd(self):
        proef = runner.PROEVEN["R16"]
        assert proef.identiteit is gb.R16
        assert (
            proef.b_invoer_sha256
            == runner.R16_B_INVOER_SHA256
            == ("11730986c6e5faf4afedb811426fae26856c234bb96315efb3bb9b3b30111cd2")
        )
        assert dict(proef.bewijsregel_contract) == R16_CONTRACT_V3
        assert proef.voorganger_kop_sha256 == runner.R15_KOP_SHA256
        assert proef.opslag.root == ROOT / "reports" / "DEF-768-AI-20260928-R16"

    def test_freezegroep_b_bindt_het_contract_van_de_code(self):
        # v6: zoals bij R16 bindt de freeze het contract van de code, niet het
        # gepinde R17-contract; een echte R17-call weigert de runner daarom.
        velden = runner.freezevelden(
            _omgeving8(_BewijsProvider()), runner.PROEVEN["R17"], "b"
        )
        assert (velden["groep"], velden["proef_id"]) == ("b", R17_ID)
        for sleutel, waarde in runner.bewijsregel_contractidentiteit().items():
            assert velden[sleutel] == waarde, sleutel
        assert {k: velden[k] for k in R17_CONTRACT} != R17_CONTRACT

    @besluit17_nodig
    def test_besluit_gebonden_aan_opdracht_mandaat_en_past_op_r17(self):
        assert _sha(BESLUIT17) == BESLUIT17_SHA256
        data = json.loads(BESLUIT17.read_text(encoding="utf-8"))
        bron = json.loads(OPDRACHT17.read_text(encoding="utf-8"))
        assert data["bron_sha256"] == _sha(OPDRACHT17)
        assert data["startmandaat_sha256"] == _sha(MANDAAT17)
        assert data["gebruikersantwoord"] == bron["gebruikersantwoord"] == "go?"
        assert (data["extra_modelaanroepen_max"], data["cumulatief_max"],
                data["historisch_verbruik"], data["reserve"]) == (12, 408, 396, 0)  # fmt: skip
        assert runner._nusd(data["kostenbudget_usd"]) == 4_320_000_000
        assert runner._nusd(data["kaderrest_usd"]) == KADERREST17_NUSD
        assert runner._nusd(data["r16_verbruik_usd"]) == R16_KOSTEN_NUSD
        assert data["r16_verbruik_modelstappen"] == 5
        assert data["r16_grootboekkop_sha256"] == R16_KOP_SHA256
        assert (
            data["verwacht_modelstappen"]
            == 9
            == sum(v["aanroepen"] for v in VERWACHT.values())
        )
        assert (
            runner.controleer_budgetbesluit(runner.PROEVEN["R17"]) == BESLUIT17_SHA256
        )

    @besluit17_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 13},
            {"cumulatief_max": 409},
            {"historisch_verbruik": 395},
            {"reserve": 1},
            {"kostenbudget_usd": "4.500000"},
            {"kaderrest_usd": "21.951256"},
            {"r16_verbruik_usd": "0.212381"},
            {"r16_verbruik_usd": None},
            {"r16_verbruik_modelstappen": 6},
        ],
    )
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        data = json.loads(BESLUIT17.read_text(encoding="utf-8"))
        for sleutel, waarde in anders.items():
            if waarde is None:
                data.pop(sleutel)
            else:
                data[sleutel] = waarde
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        proef = dataclasses.replace(
            runner.PROEVEN["R17"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)


# --- R17-invoer: gevalinhoud exact die van R16 -----------------------------------------------


@r17_invoer_nodig
class TestInvoer:
    def test_gepind_en_deterministisch_uit_de_maker(self):
        import maak_r17_bewijsregel_invoer as mk17

        assert _sha(B17) == runner.R17_B_INVOER_SHA256
        data = json.loads(B17.read_text(encoding="utf-8"))
        assert data["contract"] == R17_CONTRACT
        # v6: de maker op de huidige code wijkt alleen af in contract en
        # prompthash (zoals bij R16); de gepinde invoer blijft ongewijzigd.
        nu = mk17.maak_bewijsregel_invoer()
        assert nu["contract"] == runner.bewijsregel_contractidentiteit()
        assert {k: v for k, v in nu.items() if k not in ("contract", "items")} == {
            k: v for k, v in data.items() if k not in ("contract", "items")
        }
        zonder = [{k: v for k, v in i.items() if k != "prompt_sha256"}
                  for i in data["items"]]  # fmt: skip
        assert [{k: v for k, v in i.items() if k != "prompt_sha256"}
                for i in nu["items"]] == zonder  # fmt: skip

    def test_gevalinhoud_en_markers_gelijk_aan_r16_alleen_binding_nieuw(self):
        r16 = json.loads(B16.read_text(encoding="utf-8"))
        r17 = json.loads(B17.read_text(encoding="utf-8"))
        assert r17["schema"] == r16["schema"]
        assert [{k: i[k] for k in GEVALVELDEN} for i in r17["items"]] == [
            {k: i[k] for k in GEVALVELDEN} for i in r16["items"]
        ]
        assert [set(i) for i in r17["items"]] == [set(i) for i in r16["items"]]
        assert [i["verwacht"] for i in r17["items"]] == [VERWACHT[n] for n in "ABC"]
        assert [i["onvolledig"] for i in r17["items"]] == [
            [],
            ["source:doc:testwerkinstructie-apparatuuruitgifte"],
            [],
        ]
        # Nieuw: contract en prompthash (prompt /3); de historische R16 blijft v3.
        assert r17["contract"] == R17_CONTRACT and r16["contract"] == R16_CONTRACT_V3
        for oud, nieuw in zip(r16["items"], r17["items"], strict=True):
            assert oud["prompt_sha256"] != nieuw["prompt_sha256"]

    def test_runner_weigert_de_historische_invoer(self):
        # v6 (was: test_runner_bindt_de_invoer_opnieuw): R17 is historisch gepind;
        # de invoer hoort bij v5 en wordt onder de huidige code geweigerd.
        data = json.loads(B17.read_text(encoding="utf-8"))
        with pytest.raises(pi.InvoerfoutError, match="ander bewijsregelcontract"):
            runner.valideer_b_invoer(data, _omgeving8(_BewijsProvider()))

    def test_geregistreerde_r17_start_geen_call(self, tmp_path):
        # v6 (was: test_juiste_interpretatie_geeft_elke_verwachting_in_negen_stappen
        # op de echte invoer): de runner weigert R17 fail-closed, zonder call en
        # zonder grootboek; de mechaniek staat in TestMechaniek.
        pad = tmp_path / "b17.json"
        pad.write_bytes(B17.read_bytes())
        provider = _BewijsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            asyncio.run(
                runner.voer_b_fase(
                    _omgeving8(provider),
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=_opslag17(tmp_path),
                    proef=runner.PROEVEN["R17"],
                    voorganger_opslag=_keten17(tmp_path)[1],
                    nieuw_grootboek=True,
                )
            )
        assert provider.berichten == []
        assert not _opslag17(tmp_path).grootboek.exists()

    def test_droog_op_de_geregistreerde_r17_weigert(self, tmp_path):
        # v6 (was: test_droog_op_de_geregistreerde_r17): zoals bij R16.
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            runner.main(["--proef", "R17", "--fase", "bewijsregels",
                         "--gevallen", str(B17), "--uitmap", str(tmp_path),
                         "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("droogrun.json"))
        assert not list(tmp_path.rglob("*.jsonl"))


class TestMechaniek:
    """De R17-registratie op de synthetische R16-testinvoer (huidig contract)."""

    def test_keten_met_r16_negen_stappen_en_eigen_grootboek(self, tmp_path):
        pad = tmp_path / "b-invoer.json"
        pad.write_text(json.dumps(_invoerdata(_items())), encoding="utf-8")
        provider = _BewijsProvider()
        samenvatting = _b17(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 9
        assert samenvatting["grootboek_na"]["gestopt"] is False
        boek = gb.Grootboek.lees(_opslag17(tmp_path).grootboek, identiteit=gb.R17)
        assert boek.samenvatting()["proef_id"] == R17_ID

    def test_r16_kop_exact_anders_geweigerd(self, tmp_path):
        # Echte calls controleren de kop vóór het grootboek; hier direct getoetst.
        boek = _r16_boek(tmp_path / "r16")
        with pytest.raises(gb.BudgetSchendingError, match="voorgangergrootboek"):
            runner._controleer_voorgangerkop(runner.PROEVEN["R17"], (boek,))
        kop = boek.samenvatting()["kop_sha256"]
        proef = dataclasses.replace(runner.PROEVEN["R17"], voorganger_kop_sha256=kop)
        runner._controleer_voorgangerkop(proef, (boek,))
