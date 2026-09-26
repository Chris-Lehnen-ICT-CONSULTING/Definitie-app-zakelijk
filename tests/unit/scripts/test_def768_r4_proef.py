"""DEF-768 ronde 4 — proefidentiteit DEF-768-AI-20260924-R4, offline.

Besluit Chris 24-09 (reports/DEF-768-AI-20260924-R3/uitkomst-en-vervolg-v1.md,
gericht vervolg): maximaal 60 extra appcalls (9/4/20/8/16 + 3 alleen
technisch), cumulatief maximaal 231 vanaf 171 werkelijke R1+R2+R3-calls. Oude
reserves gesloten: R1, R2 en R3 zijn alleen-lezen voorgangers.

Ontwikkelinvoer (bekende ontwikkeldata, geen onafhankelijke gold):
T = R308, R312, R313 + twee R313-kopieën met ontwikkel-id, R302, R3P1, R3P2,
R320; G = R3G3 tweemaal (uniek id), R2G4, R3G1.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import (
    ROOT,
    _FakeProvider,
    _gevallenbestand,
    _omgeving,
)
from tests.unit.scripts.test_def768_r3_proef import _boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r4_ontwikkelinvoer as mk
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R4_ID = "DEF-768-AI-20260924-R4"
R3_MAP = ROOT / "reports" / "DEF-768-AI-20260924-R3"
R3_EINDSET = R3_MAP / "onafhankelijke-eindset-v1.json"
R3_SELECTIE = R3_MAP / "ontwikkelselectie-v1.json"
R3_G = R3_MAP / "onafhankelijke-g-invoer-v1.json"
R2_G = ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-g-invoer-v1.json"
R4_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260924-R4" / "ontwikkelselectie-v1.json"
R4_G = ROOT / "reports" / "DEF-768-AI-20260924-R4" / "g-ontwikkelinvoer-v1.json"
R4_G_ACTUEEL_SHA = "199dcf1c9f7e5b6e7f14c650de7126d0e934b5640855db50b52bd828e43ddbed"
bron_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (R3_EINDSET, R3_SELECTIE, R3_G, R2_G)),
    reason="git-ignored R2/R3-bronbestanden ontbreken",
)
T_IDS = ["R308", "R312", "R313", "R313-D2", "R313-D3", "R302", "R3P1", "R3P2", "R320"]
G_IDS = ["R3G3", "R3G3-D2", "R2G4", "R3G1"]


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _voorgangers(tmp_path: Path, r1: int = 2, r2: int = 2, r3: int = 2):
    """(R3-, R2-, R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    opslagen = []
    for naam, identiteit, n in (
        ("r3", gb.R3, r3),
        ("r2", gb.R2, r2),
        ("r1", gb.R1, r1),
    ):
        opslag = runner.Proefopslag(tmp_path / naam)
        _boek(opslag.root, identiteit, n)
        opslagen.append(opslag)
    return tuple(opslagen)


def _r4(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R4"], **anders)


def _t(omg, tmp_path, pad, proef, voorgangers, fase="ontwikkeling", **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r4"),
            proef=proef,
            voorganger_opslag=voorgangers,
            **kw,
        )
    )


# --- identiteit en cumulatieve grens ---------------------------------------------------


class TestIdentiteit:
    def test_r4_caps_reserve_en_voorganger(self):
        r4 = gb.R4
        assert r4.proef_id == R4_ID
        assert dict(r4.fasecaps) == {
            "ontwikkeling": 9,
            "g_ontwikkeling": 4,
            "t_eind": 20,
            "t_herhaling": 8,
            "g": 16,
        }
        assert (r4.reserve_max, r4.totaal_max) == (3, 60)
        assert r4.voorganger is gb.R3
        assert r4.cumulatief_max == 231
        assert "freeze_sha256" in r4.bindingsvelden
        assert gb.voorgangerketen(r4) == (gb.R3, gb.R2, gb.R1)

    def test_r4_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R4)
        assert gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R4) is not None
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R3)


class TestCumulatief:
    @staticmethod
    def _keten(tmp_path, r1, r2, r3, r4):
        o3, o2, o1 = _voorgangers(tmp_path, r1, r2, r3)
        eigen = _boek(tmp_path / "r4", gb.R4, r4)
        return eigen, [
            gb.Grootboek.lees(o.grootboek, identiteit=i)
            for o, i in ((o3, gb.R3), (o2, gb.R2), (o1, gb.R1))
        ]

    def test_precies_231_past_en_232_niet(self, tmp_path):
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57)
        gb.controleer_cumulatief(eigen, keten, 3)  # 171 + 57 + 3 = 231
        with pytest.raises(gb.BudgetSchendingError, match="231"):
            gb.controleer_cumulatief(eigen, keten, 4)

    def test_onvolledige_of_verwisselde_keten_geweigerd(self, tmp_path):
        eigen, (r3, r2, r1) = self._keten(tmp_path, 1, 1, 1, 0)
        for keten in ([r3, r2], [r3], [r2, r3, r1], [r3, r1, r2]):
            with pytest.raises(gb.BudgetSchendingError, match="keten"):
                gb.controleer_cumulatief(eigen, keten, 1)

    def test_r3_keten_ongewijzigd(self, tmp_path):
        o3, o2, o1 = _voorgangers(tmp_path, 57, 57, 57)
        r3 = gb.Grootboek.lees(o3.grootboek, identiteit=gb.R3)
        r2 = gb.Grootboek.lees(o2.grootboek, identiteit=gb.R2)
        r1 = gb.Grootboek.lees(o1.grootboek, identiteit=gb.R1)
        gb.controleer_cumulatief(r3, [r2, r1], 3)  # 174
        with pytest.raises(gb.BudgetSchendingError, match="174"):
            gb.controleer_cumulatief(r3, [r2, r1], 4)


# --- proeven en afsluiting ----------------------------------------------------------------


class TestProeven:
    def test_r4_gesloten_met_eigen_opslag_en_freeze(self):
        """R5: R4 is afgerond (57/60) en alleen-lezen voorganger."""
        r4 = runner.PROEVEN["R4"]
        assert r4.identiteit is gb.R4
        assert r4.opslag.root == ROOT / "reports" / "DEF-768-AI-20260924-R4"
        assert (r4.echt_toegestaan, r4.freeze_vereist) == (False, True)
        assert runner.STANDAARD_PROEF is runner.PROEVEN["R1"]

    @pytest.mark.parametrize("naam", ["R1", "R2", "R3", "R4"])
    def test_oude_rondes_gesloten_voor_echt(self, naam):
        assert runner.PROEVEN[naam].echt_toegestaan is False

    def test_r3_behoudt_zijn_bindingen(self):
        r3 = runner.PROEVEN["R3"]
        assert r3.t_ontwikkelinvoer_sha256 == runner.R3_T_ONTWIKKELINVOER_SHA256
        assert r3.g_ontwikkelinvoer_sha256 == runner.R3_G_ONTWIKKELINVOER_SHA256

    def test_cli_echt_op_r3_geweigerd_zonder_omgeving(self, monkeypatch, tmp_path):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit):
            runner.main(["--proef", "R3", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip

    def test_echte_omgeving_op_r3_geweigerd(self):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, runner.PROEVEN["R3"].opslag,
                                      runner.PROEVEN["R3"])  # fmt: skip

    def test_echt_r4_geweigerd_ook_met_canonieke_opslag(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        for opslag in (runner.Proefopslag(tmp_path), runner.PROEVEN["R4"].opslag):
            with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
                runner._controleer_opslag(omg, opslag, runner.PROEVEN["R4"])

    def test_echte_calls_tellen_alleen_tegen_canonieke_voorgangers(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            runner._lees_voorganger(omg, runner.PROEVEN["R4"], _voorgangers(tmp_path))

    @pytest.mark.skipif(
        not (R3_MAP / "callgrootboek.jsonl").is_file(), reason="R3-grootboek ontbreekt"
    )
    def test_canonieke_keten_leest_171_zonder_te_schrijven(self):
        """De werkelijke R3→R2→R1-grootboeken, alleen-lezen: 57+57+57."""
        paden = [
            p.opslag.grootboek for p in (runner.PROEVEN[n] for n in ("R3", "R2", "R1"))
        ]
        voor = [_sha(p) for p in paden]
        keten = runner._lees_voorganger(
            _omgeving(_FakeProvider()), runner.PROEVEN["R4"], None
        )
        assert [b.identiteit for b in keten] == [gb.R3, gb.R2, gb.R1]
        assert sum(b.samenvatting()["totaal"] for b in keten) == 171
        assert [_sha(p) for p in paden] == voor


# --- ontwikkelinvoer ------------------------------------------------------------------------


class TestOntwikkelinvoerMaker:
    @bron_nodig
    def test_t_selectie_negen_met_exacte_bronnen_en_r313_ontwikkel_ids(self):
        selectie = mk.maak_t_selectie(
            R3_EINDSET.read_bytes(), R3_SELECTIE.read_bytes(), bron_pad="x"
        )
        assert [g["id"] for g in selectie["gevallen"]] == T_IDS
        bron = {g["id"]: g for g in json.loads(R3_EINDSET.read_bytes())["gevallen"]}
        bron |= {g["id"]: g for g in json.loads(R3_SELECTIE.read_bytes())["gevallen"]}
        for geval in selectie["gevallen"]:
            oorsprong = mk.oorsprong_id(geval["id"])
            verwacht = {**bron[oorsprong], "id": geval["id"]}
            assert json.dumps(geval, sort_keys=True) == json.dumps(
                verwacht, sort_keys=True
            ), geval["id"]
        assert selectie["herkomst"]["ontwikkel_ids"] == {
            "R313-D2": "R313",
            "R313-D3": "R313",
        }
        assert "herhaal_ids" not in selectie
        assert "geen onafhankelijke gold" in selectie["status"]
        mk.controleer_t_selectie(
            selectie, R3_EINDSET.read_bytes(), R3_SELECTIE.read_bytes()
        )

    @bron_nodig
    def test_g_invoer_vier_met_exacte_invoeren_en_actuele_binding(self):
        g = mk.maak_g_invoer(R3_G.read_bytes(), R2_G.read_bytes(), bron_pad="x")
        assert [i["id"] for i in g["invoeren"]] == G_IDS
        bron = {i["id"]: i for i in json.loads(R3_G.read_bytes())["invoeren"]}
        bron |= {i["id"]: i for i in json.loads(R2_G.read_bytes())["invoeren"]}
        for invoer in g["invoeren"]:
            verwacht = {**bron[mk.oorsprong_id(invoer["id"])], "id": invoer["id"]}
            assert invoer == verwacht
        assert (
            g["g_teksten"]["basis"]
            == json.loads(R3_G.read_bytes())["g_teksten"]["basis"]
        )
        actueel = hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        assert g["g_teksten"]["actueel"]["sha256"] == actueel
        runner.controleer_g_teksten(g)

    def test_andere_bronnen_geweigerd(self):
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_t_selectie(b"{}", b"{}", bron_pad="x")
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_g_invoer(b"{}", b"{}", bron_pad="x")

    @bron_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        t, g = tmp_path / "t.json", tmp_path / "g.json"
        args = ["--t-doel", str(t), "--g-doel", str(g)]
        assert mk.main(args) == 0
        with pytest.raises(FileExistsError):
            mk.main(args)


class TestVastgelegdeR4Invoer:
    @pytest.mark.skipif(not R4_SELECTIE.is_file(), reason="R4-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert runner.PROEVEN["R4"].t_ontwikkelinvoer_sha256 == _sha(R4_SELECTIE)

    @pytest.mark.skipif(not R4_G.is_file(), reason="R4-G-invoer ontbreekt")
    def test_runner_bindt_de_vastgelegde_g_invoer(self):
        """De historische R4-binding blijft; haar actuele G-hash is die van R4,
        niet meer die van de werkboom (R5 wijzigde de G-instructie)."""
        assert runner.PROEVEN["R4"].g_ontwikkelinvoer_sha256 == _sha(R4_G)
        data = json.loads(R4_G.read_text(encoding="utf-8"))
        assert data["g_teksten"]["actueel"]["sha256"] == R4_G_ACTUEEL_SHA
        huidig = hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        assert huidig != R4_G_ACTUEEL_SHA


# --- runner: binding vóór reservering/netwerk ---------------------------------------------


class TestR4Runner:
    def test_ontwikkelcalls_over_de_volledige_keten(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        uitkomst = _t(_omgeving(provider), tmp_path, pad,
                      _r4(t_ontwikkelinvoer_sha256=_sha(pad)),
                      _voorgangers(tmp_path), nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        stand = uitkomst["voorganger_grootboek"]
        assert [k["proef_id"] for k in stand["keten"]] == [
            gb.R3.proef_id,
            gb.R2.proef_id,
            gb.R1.proef_id,
        ]
        assert (stand["keten_totaal"], stand["cumulatief_max"]) == (6, 231)

    def test_andere_t_ontwikkelinvoer_voor_grootboek_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            _t(_omgeving(provider), tmp_path, pad, runner.PROEVEN["R4"],
               _voorgangers(tmp_path), nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r4" / "callgrootboek.jsonl").exists()

    def test_keten_zonder_r1_geweigerd_voor_grootboek(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        o3, o2, _ = _voorgangers(tmp_path)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="onvolledig"):
            _t(_omgeving(provider), tmp_path, pad,
               _r4(t_ontwikkelinvoer_sha256=_sha(pad)), (o3, o2),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r4" / "callgrootboek.jsonl").exists()

    def test_cumulatieve_grens_voor_elke_call_geweigerd(self, tmp_path):
        """Grens tijdelijk op 177 (171 + 6) om de runnerroute te bewijzen."""
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        voorgangers = _voorgangers(tmp_path, 57, 57, 57)
        object.__setattr__(gb.R4, "cumulatief_max", 177)
        try:
            with pytest.raises(gb.BudgetSchendingError, match="177"):
                _t(_omgeving(provider), tmp_path, pad,
                   _r4(t_ontwikkelinvoer_sha256=_sha(pad)), voorgangers,
                   nieuw_grootboek=True, max_calls=4)  # fmt: skip
        finally:
            object.__setattr__(gb.R4, "cumulatief_max", 231)
        assert gb.R4.cumulatief_max == 231
        assert provider.aanroepen == []
        boek = gb.Grootboek.lees(tmp_path / "r4" / "callgrootboek.jsonl",
                                 identiteit=gb.R4)  # fmt: skip
        assert boek.samenvatting()["totaal"] == 0

    def test_geen_nulreset_naast_bestaand_anker(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r4(t_ontwikkelinvoer_sha256=_sha(pad))
        _t(_omgeving(_FakeProvider()), tmp_path, pad, proef, _voorgangers(tmp_path),
           nieuw_grootboek=True, max_calls=1)  # fmt: skip
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError):
            _t(_omgeving(provider), tmp_path, pad, proef, _voorgangers(tmp_path / "b"),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_eindfase_zonder_freeze_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R4"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_r3_freeze_past_niet_op_r4(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R3"], "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 20), runner.PROEVEN["R4"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(
        not (R3_MAP / "eindfreeze-t-v1.json").is_file(), reason="geen R3-freeze"
    )
    def test_echte_r3_eindfreeze_geweigerd_op_r4(self, tmp_path):
        """De definitieve R3-freeze (T/7, oude code) start geen R4-call."""
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="past niet"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R4"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True, freeze=R3_MAP / "eindfreeze-t-v1.json")  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(not R4_G.is_file(), reason="R4-G-invoer ontbreekt")
    def test_g_ontwikkeling_r4_vier_actuele_calls(self, tmp_path):
        provider = _FakeProvider(tekst="Ontologische categorie: type\nRing.")
        uitkomst = asyncio.run(
            runner.voer_g_fase(
                _omgeving(provider),
                fase="g_ontwikkeling",
                g_invoerpad=R4_G,
                uitmap=tmp_path / "uit",
                opslag=runner.Proefopslag(tmp_path / "r4"),
                proef=runner.PROEVEN["R4"],
                voorganger_opslag=_voorgangers(tmp_path),
                nieuw_grootboek=True,
            )
        )
        assert len(provider.aanroepen) == 4
        assert uitkomst["vergelijkingsaard"] == runner.G_ONTWIKKELAARD_R4
        assert (
            uitkomst["g_actueel_instructie_sha256"]
            == hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        )

    def test_g_ontwikkeling_op_andere_invoer_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="G-ontwikkel"):
            asyncio.run(
                runner.voer_g_fase(
                    _omgeving(provider),
                    fase="g_ontwikkeling",
                    g_invoerpad=runner.PROJECT_ROOT
                    / "tests"
                    / "fixtures"
                    / "ess05"
                    / "g_invoer_v2.json",
                    uitmap=tmp_path / "uit",
                    opslag=runner.Proefopslag(tmp_path / "r4"),
                    proef=runner.PROEVEN["R4"],
                    voorganger_opslag=_voorgangers(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert provider.aanroepen == []


class TestDroogR4:
    @pytest.mark.skipif(not R4_SELECTIE.is_file(), reason="R4-selectie ontbreekt")
    def test_droog_t_negen_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R4", "--fase", "ontwikkeling", "--gevallen",
                            str(R4_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R4_ID, 9)
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_eindfreeze_draagt_de_r4_identiteit(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        droog = asyncio.run(runner.droogrun("t_eind", pad, tmp_path / "d",
                                            proef=runner.PROEVEN["R4"]))  # fmt: skip
        assert droog["freezevelden"]["proef_id"] == R4_ID
        # De droge freeze volgt de actuele T-versie (R5: /11).
        # ADR-003: de droge freeze volgt de actuele tweestaps-T (/14 plus
        # verificatieprompt); zo past zij niet meer op de eenstaps-/13-freeze.
        # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
        # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
        # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
        assert droog["freezevelden"]["prompt_version"] == "ess05-assess/17"
        assert droog["freezevelden"]["verification_prompt_version"] == (
            "ess05-verify/4"
        )
        assert droog["freezevelden"]["code_sha256"] == runner.code_sha256()
