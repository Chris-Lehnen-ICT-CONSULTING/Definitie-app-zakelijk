"""DEF-768 ronde 5 — proefidentiteit DEF-768-AI-20260925-R5, offline.

Besluit Chris 25-09 (reports/DEF-768-AI-20260924-R4/uitkomst-en-vervolg-v1.md,
concreet vervolgvoorstel, 'ja akkoord'): maximaal 60 nieuwe appcalls
(9/4/20/8/16 + 3 alleen technisch), cumulatief maximaal 288 vanaf 228
werkelijke R1–R4-calls. Oude reserves gesloten: R1 t/m R4 zijn alleen-lezen
voorgangers; geen overdracht van ongebruikt budget.

Ontwikkelinvoer (bekende ontwikkeldata, geen onafhankelijke gold):
T = R410, R411, R414, R409, R412, R417, R403 (R4-eindset), R313 (R3-eindset),
R3P1 (R3-ontwikkelselectie); G = R4G1 tweemaal (uniek id), R3G3, R2G4.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.

Sinds ronde 6 (R5 uitkomst-en-vervolg-v1, akkoord 25-09) is R5 gesloten voor
echte calls: alleen-lezen voorganger met behoud van zijn bindingen.
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
from tests.unit.scripts.test_def768_r3_proef import _binding_voor, _boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r5_ontwikkelinvoer as mk
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R5_ID = "DEF-768-AI-20260925-R5"
R5_MAP = ROOT / "reports" / R5_ID
R4_MAP = ROOT / "reports" / "DEF-768-AI-20260924-R4"
R3_MAP = ROOT / "reports" / "DEF-768-AI-20260924-R3"
R4_EINDSET = R4_MAP / "onafhankelijke-eindset-v1.json"
R4_G = R4_MAP / "onafhankelijke-g-invoer-v2.json"
R3_EINDSET = R3_MAP / "onafhankelijke-eindset-v1.json"
R3_SELECTIE = R3_MAP / "ontwikkelselectie-v1.json"
R3_G = R3_MAP / "onafhankelijke-g-invoer-v1.json"
R2_G = ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-g-invoer-v1.json"
R5_SELECTIE = R5_MAP / "ontwikkelselectie-v1.json"
R5_G = R5_MAP / "g-ontwikkelinvoer-v1.json"
BRONNEN = (R4_EINDSET, R3_EINDSET, R3_SELECTIE, R4_G, R3_G, R2_G)
bron_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in BRONNEN),
    reason="git-ignored R2/R3/R4-bronbestanden ontbreken",
)
T_IDS = ["R410", "R411", "R414", "R409", "R412", "R417", "R403", "R313", "R3P1"]
G_IDS = ["R4G1", "R4G1-D2", "R3G3", "R2G4"]
GESLOTEN = ["R1", "R2", "R3", "R4"]


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _t_bronnen() -> tuple[bytes, bytes, bytes]:
    return R4_EINDSET.read_bytes(), R3_EINDSET.read_bytes(), R3_SELECTIE.read_bytes()


def _g_bronnen() -> tuple[bytes, bytes, bytes]:
    return R4_G.read_bytes(), R3_G.read_bytes(), R2_G.read_bytes()


def _voorgangers(tmp_path: Path, r1=2, r2=2, r3=2, r4=2):
    """(R4-, R3-, R2-, R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    opslagen = []
    for naam, identiteit, n in (
        ("r4", gb.R4, r4),
        ("r3", gb.R3, r3),
        ("r2", gb.R2, r2),
        ("r1", gb.R1, r1),
    ):
        opslag = runner.Proefopslag(tmp_path / naam)
        _boek(opslag.root, identiteit, n)
        opslagen.append(opslag)
    return tuple(opslagen)


def _r5(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R5"], **anders)


def _t(omg, tmp_path, pad, proef, voorgangers, fase="ontwikkeling", **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r5"),
            proef=proef,
            voorganger_opslag=voorgangers,
            **kw,
        )
    )


# --- identiteit en cumulatieve grens ---------------------------------------------------


class TestIdentiteit:
    def test_r5_caps_reserve_en_voorganger(self):
        r5 = gb.R5
        assert r5.proef_id == R5_ID
        assert dict(r5.fasecaps) == {
            "ontwikkeling": 9,
            "g_ontwikkeling": 4,
            "t_eind": 20,
            "t_herhaling": 8,
            "g": 16,
        }
        assert (r5.reserve_max, r5.totaal_max) == (3, 60)
        assert r5.voorganger is gb.R4
        assert r5.cumulatief_max == 288
        assert "freeze_sha256" in r5.bindingsvelden
        assert gb.voorgangerketen(r5) == (gb.R4, gb.R3, gb.R2, gb.R1)

    def test_r4_identiteit_ongewijzigd(self):
        assert (gb.R4.cumulatief_max, gb.R4.voorganger) == (231, gb.R3)

    def test_r5_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R5)
        assert gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R5) is not None
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R4)


class TestCumulatief:
    @staticmethod
    def _keten(tmp_path, r1, r2, r3, r4, r5):
        o4, o3, o2, o1 = _voorgangers(tmp_path, r1, r2, r3, r4)
        eigen = _boek(tmp_path / "r5", gb.R5, r5)
        return eigen, [
            gb.Grootboek.lees(o.grootboek, identiteit=i)
            for o, i in ((o4, gb.R4), (o3, gb.R3), (o2, gb.R2), (o1, gb.R1))
        ]

    def test_precies_288_past_en_289_niet(self, tmp_path):
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57, 57)
        gb.controleer_cumulatief(eigen, keten, 3)  # 228 + 57 + 3 = 288
        with pytest.raises(gb.BudgetSchendingError, match="288"):
            gb.controleer_cumulatief(eigen, keten, 4)

    def test_ongebruikt_r4_budget_gaat_niet_over(self, tmp_path):
        """Minder R4-calls geeft R5 geen extra fasecalls: de eigen caps blijven."""
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 50, 57)
        gb.controleer_cumulatief(eigen, keten, 3)  # 278, ruim onder 288
        with pytest.raises(gb.BudgetSchendingError):
            eigen.reserveer(
                "ontwikkeling",
                "ontwikkeling|extra",
                invoer_sha256="a" * 64,
                binding=_binding_voor(gb.R5, "ontwikkeling"),
            )
        assert eigen.samenvatting()["totaal"] == 57

    def test_onvolledige_of_verwisselde_keten_geweigerd(self, tmp_path):
        eigen, (r4, r3, r2, r1) = self._keten(tmp_path, 1, 1, 1, 1, 0)
        for keten in ([r4, r3, r2], [r4], [r3, r2, r1], [r3, r4, r2, r1]):
            with pytest.raises(gb.BudgetSchendingError, match="keten"):
                gb.controleer_cumulatief(eigen, keten, 1)

    def test_r4_keten_ongewijzigd(self, tmp_path):
        o4, o3, o2, o1 = _voorgangers(tmp_path, 57, 57, 57, 57)
        r4 = gb.Grootboek.lees(o4.grootboek, identiteit=gb.R4)
        keten = [
            gb.Grootboek.lees(o.grootboek, identiteit=i)
            for o, i in ((o3, gb.R3), (o2, gb.R2), (o1, gb.R1))
        ]
        gb.controleer_cumulatief(r4, keten, 3)  # 231
        with pytest.raises(gb.BudgetSchendingError, match="231"):
            gb.controleer_cumulatief(r4, keten, 4)


# --- proeven en afsluiting ----------------------------------------------------------------


class TestProeven:
    def test_r5_gesloten_met_eigen_opslag_en_freeze(self):
        r5 = runner.PROEVEN["R5"]
        assert r5.identiteit is gb.R5
        assert r5.opslag.root == R5_MAP
        assert (r5.echt_toegestaan, r5.freeze_vereist) == (False, True)
        assert runner.STANDAARD_PROEF is runner.PROEVEN["R1"]

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_oude_rondes_gesloten_voor_echt(self, naam):
        assert runner.PROEVEN[naam].echt_toegestaan is False

    def test_r4_behoudt_zijn_bindingen(self):
        r4 = runner.PROEVEN["R4"]
        assert r4.identiteit is gb.R4
        assert r4.opslag.root == R4_MAP
        assert r4.freeze_vereist is True
        assert r4.t_ontwikkelinvoer_sha256 == runner.R4_T_ONTWIKKELINVOER_SHA256
        assert r4.g_ontwikkelinvoer_sha256 == runner.R4_G_ONTWIKKELINVOER_SHA256

    @pytest.mark.parametrize("naam", GESLOTEN)
    @pytest.mark.parametrize("fase", ["ontwikkeling", "g_ontwikkeling"])
    def test_cli_echt_op_oude_ronde_geweigerd_zonder_omgeving(
        self, monkeypatch, tmp_path, naam, fase
    ):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen fase voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_t_fase", geen_fase)
        monkeypatch.setattr(runner, "voer_g_fase", geen_fase)
        if fase not in runner.PROEVEN[naam].identiteit.fasecaps:
            pytest.skip(f"fase {fase} bestaat niet in {naam}")
        invoer = "--g-invoer" if fase == "g_ontwikkeling" else "--gevallen"
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", naam, "--fase", fase, invoer,
                         str(tmp_path / "bestaat-niet.json"), "--echt"])  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_t_programmatisch_geweigerd_voor_invoer_grootboek_en_netwerk(
        self, tmp_path, naam
    ):
        """Niet-bestaande invoer en lege opslag: de weigering komt eerst."""
        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            asyncio.run(
                runner.voer_t_fase(
                    omg,
                    fase="ontwikkeling",
                    gevallenpad=tmp_path / "bestaat-niet.json",
                    uitmap=tmp_path / "uit",
                    opslag=runner.Proefopslag(tmp_path / "opslag"),
                    proef=runner.PROEVEN[naam],
                    voorganger_opslag=None,
                    nieuw_grootboek=True,
                )
            )
        assert provider.aanroepen == []
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("naam", ["R2", "R3", "R4"])
    def test_g_programmatisch_geweigerd_voor_invoer_grootboek_en_netwerk(
        self, tmp_path, naam
    ):
        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            asyncio.run(
                runner.voer_g_fase(
                    omg,
                    fase="g_ontwikkeling",
                    g_invoerpad=tmp_path / "bestaat-niet.json",
                    uitmap=tmp_path / "uit",
                    opslag=runner.Proefopslag(tmp_path / "opslag"),
                    proef=runner.PROEVEN[naam],
                    voorganger_opslag=None,
                    nieuw_grootboek=True,
                )
            )
        assert provider.aanroepen == []
        assert list(tmp_path.iterdir()) == []

    def test_echt_r5_gesloten_ook_in_canonieke_opslag(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        for opslag in (
            runner.Proefopslag(tmp_path),
            runner.PROEVEN["R4"].opslag,
            runner.PROEVEN["R5"].opslag,
        ):
            with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
                runner._controleer_opslag(omg, opslag, runner.PROEVEN["R5"])

    def test_echte_calls_tellen_alleen_tegen_canonieke_voorgangers(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            runner._lees_voorganger(omg, runner.PROEVEN["R5"], _voorgangers(tmp_path))

    def test_cli_echt_r5_geweigerd_zonder_omgeving(self, monkeypatch):
        def verboden(**_):
            raise AssertionError("geen omgeving voor de gesloten R5")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen fase voor de gesloten R5")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_t_fase", geen_fase)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R5", "--fase", "ontwikkeling", "--gevallen",
                         "x.json", "--echt"])  # fmt: skip
        assert exc.value.code != 0

    @pytest.mark.skipif(
        not (R4_MAP / "callgrootboek.jsonl").is_file(), reason="R4-grootboek ontbreekt"
    )
    def test_canonieke_keten_leest_228_zonder_te_schrijven(self):
        """De werkelijke R4→R3→R2→R1-grootboeken, alleen-lezen: 4 × 57."""
        namen = ("R4", "R3", "R2", "R1")
        bestanden = []
        for proef in (runner.PROEVEN[n] for n in namen):
            g = proef.opslag.grootboek
            bestanden += [g, g.with_name(g.name + ".anker.json")]
        voor = {p: _sha(p) for p in bestanden}
        keten = runner._lees_voorganger(
            _omgeving(_FakeProvider()), runner.PROEVEN["R5"], None
        )
        assert [b.identiteit for b in keten] == [gb.R4, gb.R3, gb.R2, gb.R1]
        assert sum(b.samenvatting()["totaal"] for b in keten) == 228
        assert {p: _sha(p) for p in bestanden} == voor


# --- ontwikkelinvoer ------------------------------------------------------------------------


class TestOntwikkelinvoerMaker:
    @bron_nodig
    def test_t_selectie_negen_met_exacte_bronnen(self):
        selectie = mk.maak_t_selectie(*_t_bronnen(), bron_pad="x")
        assert [g["id"] for g in selectie["gevallen"]] == T_IDS
        bron = {}
        for data in _t_bronnen():
            bron |= {g["id"]: g for g in json.loads(data)["gevallen"]}
        for geval in selectie["gevallen"]:
            assert json.dumps(geval, sort_keys=True) == json.dumps(
                bron[geval["id"]], sort_keys=True
            ), geval["id"]
        assert selectie["herkomst"]["ontwikkel_ids"] == {}
        assert "herhaal_ids" not in selectie
        assert "geen onafhankelijke gold" in selectie["status"]
        mk.controleer_t_selectie(selectie, *_t_bronnen())

    @bron_nodig
    def test_g_invoer_vier_met_exacte_invoeren_en_actuele_binding(self):
        g = mk.maak_g_invoer(*_g_bronnen(), bron_pad="x")
        assert [i["id"] for i in g["invoeren"]] == G_IDS
        bron = {}
        for data in _g_bronnen():
            bron |= {i["id"]: i for i in json.loads(data)["invoeren"]}
        for invoer in g["invoeren"]:
            verwacht = {**bron[mk.oorsprong_id(invoer["id"])], "id": invoer["id"]}
            assert invoer == verwacht
        assert g["herkomst"]["ontwikkel_ids"] == {"R4G1-D2": "R4G1"}
        # R4G1 behoudt de verliesvrije segmentatie uit de v2-invoer.
        assert (
            g["invoeren"][0]["documenten"]
            == json.loads(R4_G.read_bytes())["invoeren"][0]["documenten"]
        )
        assert g["invoeren"][0] == {**g["invoeren"][1], "id": "R4G1"}
        # Basis blijft de oorspronkelijke git-HEAD-tekst; alleen actueel bindt nieuw.
        for data in _g_bronnen():
            assert g["g_teksten"]["basis"] == json.loads(data)["g_teksten"]["basis"]
        actueel = hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        assert g["g_teksten"]["actueel"]["sha256"] == actueel
        runner.controleer_g_teksten(g)

    def test_andere_bronnen_geweigerd(self):
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_t_selectie(b"{}", b"{}", b"{}", bron_pad="x")
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_g_invoer(b"{}", b"{}", b"{}", bron_pad="x")

    @bron_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        t, g = tmp_path / "t.json", tmp_path / "g.json"
        args = ["--t-doel", str(t), "--g-doel", str(g)]
        assert mk.main(args) == 0
        with pytest.raises(FileExistsError):
            mk.main(args)


class TestVastgelegdeR5Invoer:
    @pytest.mark.skipif(not R5_SELECTIE.is_file(), reason="R5-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert runner.PROEVEN["R5"].t_ontwikkelinvoer_sha256 == _sha(R5_SELECTIE)
        assert _sha(R5_SELECTIE) == runner.R5_T_ONTWIKKELINVOER_SHA256

    @pytest.mark.skipif(not R5_G.is_file(), reason="R5-G-invoer ontbreekt")
    def test_runner_bindt_de_vastgelegde_g_invoer(self):
        assert runner.PROEVEN["R5"].g_ontwikkelinvoer_sha256 == _sha(R5_G)
        runner.controleer_g_teksten(json.loads(R5_G.read_text(encoding="utf-8")))

    @bron_nodig
    @pytest.mark.skipif(not R5_SELECTIE.is_file(), reason="R5-selectie ontbreekt")
    def test_vastgelegde_invoer_is_reproduceerbaar(self):
        vast_t = json.loads(R5_SELECTIE.read_text(encoding="utf-8"))
        vast_g = json.loads(R5_G.read_text(encoding="utf-8"))
        herkomst_pad = vast_t["herkomst"]["bron_pad_aanroep"]
        assert vast_t == mk.maak_t_selectie(*_t_bronnen(), bron_pad=herkomst_pad)
        assert vast_g == mk.maak_g_invoer(
            *_g_bronnen(), bron_pad=vast_g["herkomst"]["bron_pad_aanroep"]
        )


# --- runner: binding vóór reservering/netwerk ---------------------------------------------


class TestR5Runner:
    def test_ontwikkelcalls_over_de_volledige_keten(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        uitkomst = _t(_omgeving(provider), tmp_path, pad,
                      _r5(t_ontwikkelinvoer_sha256=_sha(pad)),
                      _voorgangers(tmp_path), nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        stand = uitkomst["voorganger_grootboek"]
        assert [k["proef_id"] for k in stand["keten"]] == [
            gb.R4.proef_id,
            gb.R3.proef_id,
            gb.R2.proef_id,
            gb.R1.proef_id,
        ]
        assert (stand["keten_totaal"], stand["cumulatief_max"]) == (8, 288)

    def test_andere_t_ontwikkelinvoer_voor_grootboek_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            _t(_omgeving(provider), tmp_path, pad, runner.PROEVEN["R5"],
               _voorgangers(tmp_path), nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r5" / "callgrootboek.jsonl").exists()

    def test_keten_zonder_r1_geweigerd_voor_grootboek(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        o4, o3, o2, _ = _voorgangers(tmp_path)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="onvolledig"):
            _t(_omgeving(provider), tmp_path, pad,
               _r5(t_ontwikkelinvoer_sha256=_sha(pad)), (o4, o3, o2),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r5" / "callgrootboek.jsonl").exists()

    def test_cumulatieve_grens_voor_elke_call_geweigerd(self, tmp_path):
        """Grens tijdelijk op 234 (228 + 6) om de runnerroute te bewijzen."""
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        voorgangers = _voorgangers(tmp_path, 57, 57, 57, 57)
        object.__setattr__(gb.R5, "cumulatief_max", 234)
        try:
            with pytest.raises(gb.BudgetSchendingError, match="234"):
                _t(_omgeving(provider), tmp_path, pad,
                   _r5(t_ontwikkelinvoer_sha256=_sha(pad)), voorgangers,
                   nieuw_grootboek=True, max_calls=4)  # fmt: skip
        finally:
            object.__setattr__(gb.R5, "cumulatief_max", 288)
        assert gb.R5.cumulatief_max == 288
        assert provider.aanroepen == []
        boek = gb.Grootboek.lees(tmp_path / "r5" / "callgrootboek.jsonl",
                                 identiteit=gb.R5)  # fmt: skip
        assert boek.samenvatting()["totaal"] == 0

    def test_geen_nulreset_naast_bestaand_anker(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r5(t_ontwikkelinvoer_sha256=_sha(pad))
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
               runner.PROEVEN["R5"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_r4_freeze_past_niet_op_r5(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R4"], "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 20), runner.PROEVEN["R5"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(
        not (R4_MAP / "eindfreeze-t-v1.json").is_file(), reason="geen R4-freeze"
    )
    def test_echte_r4_eindfreeze_geweigerd_op_r5(self, tmp_path):
        """De definitieve R4-freeze (T/10) start geen R5-call."""
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="past niet"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R5"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True, freeze=R4_MAP / "eindfreeze-t-v1.json")  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(not R5_G.is_file(), reason="R5-G-invoer ontbreekt")
    def test_g_ontwikkeling_r5_vier_actuele_calls(self, tmp_path):
        provider = _FakeProvider(tekst="Ontologische categorie: type\nRol.")
        uitkomst = asyncio.run(
            runner.voer_g_fase(
                _omgeving(provider),
                fase="g_ontwikkeling",
                g_invoerpad=R5_G,
                uitmap=tmp_path / "uit",
                opslag=runner.Proefopslag(tmp_path / "r5"),
                proef=runner.PROEVEN["R5"],
                voorganger_opslag=_voorgangers(tmp_path),
                nieuw_grootboek=True,
            )
        )
        assert len(provider.aanroepen) == 4
        assert uitkomst["vergelijkingsaard"] == runner.G_ONTWIKKELAARD_R5
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
                    g_invoerpad=ROOT
                    / "tests"
                    / "fixtures"
                    / "ess05"
                    / "g_invoer_v2.json",
                    uitmap=tmp_path / "uit",
                    opslag=runner.Proefopslag(tmp_path / "r5"),
                    proef=runner.PROEVEN["R5"],
                    voorganger_opslag=_voorgangers(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert provider.aanroepen == []


class TestDroogR5:
    @pytest.mark.skipif(not R5_SELECTIE.is_file(), reason="R5-selectie ontbreekt")
    def test_droog_t_negen_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R5", "--fase", "ontwikkeling", "--gevallen",
                            str(R5_SELECTIE), "--uitmap", str(tmp_path), "--droog",
                            "--timeout", "60", "--max-tokens-t", "1500"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R5_ID, 9)
        assert not list(tmp_path.rglob("*.jsonl"))

    @pytest.mark.skipif(not R5_G.is_file(), reason="R5-G-invoer ontbreekt")
    def test_droog_g_vier_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R5", "--fase", "g_ontwikkeling", "--g-invoer",
                            str(R5_G), "--uitmap", str(tmp_path), "--droog",
                            "--timeout", "60"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-g_ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R5_ID, 4)
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_eindfreeze_draagt_de_r5_identiteit(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        droog = asyncio.run(runner.droogrun("t_eind", pad, tmp_path / "d",
                                            proef=runner.PROEVEN["R5"]))  # fmt: skip
        assert droog["freezevelden"]["proef_id"] == R5_ID
        # ADR-003: de droge freeze volgt de actuele tweestaps-T (/14 plus
        # verificatieprompt); zo past zij niet meer op de eenstaps-/13-freeze.
        # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
        # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
        # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
        # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
        assert droog["freezevelden"]["prompt_version"] == "ess05-assess/18"
        assert droog["freezevelden"]["verification_prompt_version"] == (
            "ess05-verify/4"
        )
        assert droog["freezevelden"]["code_sha256"] == runner.code_sha256()
