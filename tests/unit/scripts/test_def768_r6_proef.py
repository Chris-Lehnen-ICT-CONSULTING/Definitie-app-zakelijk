"""DEF-768 ronde 6 — proefidentiteit DEF-768-AI-20260925-R6, offline, alleen T.

Besluit Chris 25-09 (reports/DEF-768-AI-20260925-R5/uitkomst-en-vervolg-v1.md,
gericht vervolgvoorstel, 'ja'): maximaal 40 nieuwe uitsluitend T-appcalls
(9 ontwikkeling + 20 T-eind + 8 T-herhaling + 3 alleen technisch), cumulatief
maximaal 325 vanaf 285 werkelijke R1–R5-calls. Geen G-fases: G en
G-ontwikkeling worden fail-closed geweigerd. Oude reserves gesloten: R1 t/m R5
zijn alleen-lezen voorgangers.

Ontwikkelinvoer (bekende ontwikkeldata, geen onafhankelijke gold): R514, R508,
R504, R512, R511, R516, R507, R506 uit de R5-eindset en R313 uit de R3-eindset.

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
from tests.unit.scripts.test_def768_r3_proef import _binding_voor, _boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner

try:  # de R6-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r6_ontwikkelinvoer as mk
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk = None

R6_ID = "DEF-768-AI-20260925-R6"
R6_MAP = ROOT / "reports" / R6_ID
R5_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R5"
R3_MAP = ROOT / "reports" / "DEF-768-AI-20260924-R3"
R5_EINDSET = R5_MAP / "onafhankelijke-eindset-v1.json"
R3_EINDSET = R3_MAP / "onafhankelijke-eindset-v1.json"
R6_SELECTIE = R6_MAP / "ontwikkelselectie-v1.json"
bron_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (R5_EINDSET, R3_EINDSET)),
    reason="git-ignored R3/R5-bronbestanden ontbreken",
)
T_IDS = ["R514", "R508", "R504", "R512", "R511", "R516", "R313", "R507", "R506"]
GESLOTEN = ["R1", "R2", "R3", "R4", "R5"]
G_FASES = ["g", "g_ontwikkeling"]


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _t_bronnen() -> tuple[bytes, bytes]:
    return R5_EINDSET.read_bytes(), R3_EINDSET.read_bytes()


def _voorgangers(tmp_path: Path, r1=2, r2=2, r3=2, r4=2, r5=2):
    """(R5-, R4-, R3-, R2-, R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    opslagen = []
    for naam, identiteit, n in (
        ("r5", gb.R5, r5),
        ("r4", gb.R4, r4),
        ("r3", gb.R3, r3),
        ("r2", gb.R2, r2),
        ("r1", gb.R1, r1),
    ):
        opslag = runner.Proefopslag(tmp_path / naam)
        _boek(opslag.root, identiteit, n)
        opslagen.append(opslag)
    return tuple(opslagen)


def _r6(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R6"], **anders)


def _t(omg, tmp_path, pad, proef, voorgangers, fase="ontwikkeling", **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r6"),
            proef=proef,
            voorganger_opslag=voorgangers,
            **kw,
        )
    )


def _g(omg, tmp_path, fase, proef):
    return asyncio.run(
        runner.voer_g_fase(
            omg,
            fase=fase,
            g_invoerpad=tmp_path / "bestaat-niet.json",
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "opslag"),
            proef=proef,
            voorganger_opslag=None,
            nieuw_grootboek=True,
        )
    )


# --- identiteit en cumulatieve grens ---------------------------------------------------


class TestIdentiteit:
    def test_r6_alleen_t_caps_reserve_en_voorganger(self):
        r6 = gb.R6
        assert r6.proef_id == R6_ID
        assert dict(r6.fasecaps) == {"ontwikkeling": 9, "t_eind": 20, "t_herhaling": 8}
        assert (r6.reserve_max, r6.totaal_max) == (3, 40)
        assert r6.voorganger is gb.R5
        assert r6.cumulatief_max == 325
        assert [g.naam for g in r6.eindgroepen] == ["t"]
        assert r6.eindgroep("g") is None
        assert "freeze_sha256" in r6.bindingsvelden
        assert gb.voorgangerketen(r6) == (gb.R5, gb.R4, gb.R3, gb.R2, gb.R1)

    def test_r5_identiteit_ongewijzigd(self):
        assert (gb.R5.cumulatief_max, gb.R5.voorganger, gb.R5.totaal_max) == (
            288,
            gb.R4,
            60,
        )

    def test_r6_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R6)
        assert gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R6) is not None
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R5)

    @pytest.mark.parametrize("fase", G_FASES)
    def test_grootboek_weigert_g_reservering(self, tmp_path, fase):
        boek = gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R6)
        with pytest.raises(gb.BudgetSchendingError, match="onbekende fase"):
            boek.reserveer(
                fase,
                f"{fase}|x",
                invoer_sha256="a" * 64,
                binding=_binding_voor(gb.R5, fase),
            )
        assert boek.samenvatting()["totaal"] == 0


class TestCumulatief:
    @staticmethod
    def _keten(tmp_path, r1, r2, r3, r4, r5, r6):
        o5, o4, o3, o2, o1 = _voorgangers(tmp_path, r1, r2, r3, r4, r5)
        eigen = _boek(tmp_path / "r6", gb.R6, r6)
        return eigen, [
            gb.Grootboek.lees(o.grootboek, identiteit=i)
            for o, i in (
                (o5, gb.R5),
                (o4, gb.R4),
                (o3, gb.R3),
                (o2, gb.R2),
                (o1, gb.R1),
            )
        ]

    def test_precies_325_past_en_326_niet(self, tmp_path):
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57, 57, 37)
        gb.controleer_cumulatief(eigen, keten, 3)  # 285 + 37 + 3 = 325
        with pytest.raises(gb.BudgetSchendingError, match="325"):
            gb.controleer_cumulatief(eigen, keten, 4)

    def test_ongebruikt_r5_budget_gaat_niet_over(self, tmp_path):
        """Minder R5-calls geeft R6 geen extra fasecalls: de eigen caps blijven."""
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57, 50, 37)
        gb.controleer_cumulatief(eigen, keten, 3)
        with pytest.raises(gb.BudgetSchendingError):
            eigen.reserveer(
                "ontwikkeling",
                "ontwikkeling|extra",
                invoer_sha256="a" * 64,
                binding=_binding_voor(gb.R6, "ontwikkeling"),
            )
        assert eigen.samenvatting()["totaal"] == 37

    def test_onvolledige_of_verwisselde_keten_geweigerd(self, tmp_path):
        eigen, (r5, r4, r3, r2, r1) = self._keten(tmp_path, 1, 1, 1, 1, 1, 0)
        for keten in ([r5, r4, r3, r2], [r5], [r4, r3, r2, r1], [r4, r5, r3, r2, r1]):
            with pytest.raises(gb.BudgetSchendingError, match="keten"):
                gb.controleer_cumulatief(eigen, keten, 1)


# --- proeven en afsluiting ----------------------------------------------------------------


class TestProeven:
    def test_r6_gesloten_met_eigen_opslag_en_freeze(self):
        # R7: ronde 6 is afgerond (37/40) en gesloten voor echte calls; haar
        # opslag, freeze-eis en invoerbinding blijven voor de keten gelijk.
        r6 = runner.PROEVEN["R6"]
        assert r6.identiteit is gb.R6
        assert r6.opslag.root == R6_MAP
        assert (r6.echt_toegestaan, r6.freeze_vereist) == (False, True)
        assert r6.t_ontwikkelinvoer_sha256 == runner.R6_T_ONTWIKKELINVOER_SHA256
        assert r6.g_ontwikkelinvoer_sha256 is None
        assert runner.STANDAARD_PROEF is runner.PROEVEN["R1"]

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_oude_rondes_gesloten_voor_echt(self, naam):
        assert runner.PROEVEN[naam].echt_toegestaan is False

    def test_r5_behoudt_zijn_bindingen(self):
        r5 = runner.PROEVEN["R5"]
        assert (r5.identiteit, r5.opslag.root, r5.freeze_vereist) == (
            gb.R5,
            R5_MAP,
            True,
        )
        assert r5.t_ontwikkelinvoer_sha256 == runner.R5_T_ONTWIKKELINVOER_SHA256
        assert r5.g_ontwikkelinvoer_sha256 == runner.R5_G_ONTWIKKELINVOER_SHA256

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_cli_echt_op_oude_ronde_geweigerd_zonder_omgeving(
        self, monkeypatch, tmp_path, naam
    ):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen fase voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_t_fase", geen_fase)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", naam, "--fase", "ontwikkeling", "--gevallen",
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

    @pytest.mark.parametrize("naam", ["R2", "R3", "R4", "R5"])
    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_oude_ronde_geweigerd_voor_invoer_grootboek_en_netwerk(
        self, tmp_path, naam, fase
    ):
        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            _g(omg, tmp_path, fase, runner.PROEVEN[naam])
        assert provider.aanroepen == []
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("fase", G_FASES)
    def test_cli_echt_g_op_r5_geweigerd_zonder_omgeving(
        self, monkeypatch, tmp_path, fase
    ):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen fase voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_g_fase", geen_fase)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R5", "--fase", fase, "--g-invoer",
                         str(tmp_path / "bestaat-niet.json"), "--echt"])  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("echt", [True, False])
    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_programmatisch_geweigerd_in_r6(self, tmp_path, fase, echt):
        """G bestaat niet in R6: geweigerd vóór invoer, grootboek en netwerk,
        ook in de canonieke opslag en ook zonder echte omgeving."""
        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=echt)
        with pytest.raises(gb.BudgetSchendingError, match="bestaat niet in ronde R6"):
            _g(omg, tmp_path, fase, runner.PROEVEN["R6"])
        assert provider.aanroepen == []
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_droog_geweigerd_in_r6(self, tmp_path, fase):
        with pytest.raises(gb.BudgetSchendingError, match="bestaat niet in ronde R6"):
            asyncio.run(
                runner.droogrun(
                    fase,
                    tmp_path / "bestaat-niet.json",
                    tmp_path / "d",
                    proef=runner.PROEVEN["R6"],
                )
            )
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("modus", ["--echt", "--droog"])
    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_cli_geweigerd_in_r6(self, monkeypatch, tmp_path, fase, modus):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een G-fase in R6")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen G-fase in R6")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_g_fase", geen_fase)
        monkeypatch.setattr(runner, "droogrun", geen_fase)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R6", "--fase", fase, "--g-invoer",
                         str(tmp_path / "bestaat-niet.json"), modus,
                         "--uitmap", str(tmp_path / "uit")])  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []

    def test_echt_r6_gesloten_ook_in_eigen_opslag(self, tmp_path):
        # R7: R6 is gesloten, dus ook haar canonieke opslag weigert echte calls.
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        for opslag in (
            runner.Proefopslag(tmp_path),
            runner.PROEVEN["R5"].opslag,
            runner.PROEVEN["R6"].opslag,
        ):
            with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
                runner._controleer_opslag(omg, opslag, runner.PROEVEN["R6"])

    def test_echte_calls_tellen_alleen_tegen_canonieke_voorgangers(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            runner._lees_voorganger(omg, runner.PROEVEN["R6"], _voorgangers(tmp_path))

    def test_cli_echt_r6_geweigerd_zonder_omgeving(self, monkeypatch, tmp_path):
        # R7: echte calls op R6 via de CLI worden vóór omgeving en fase geweigerd.
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        async def geen_fase(*_a, **_k):
            raise AssertionError("geen fase voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        monkeypatch.setattr(runner, "voer_t_fase", geen_fase)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R6", "--fase", "ontwikkeling", "--gevallen",
                         str(tmp_path / "bestaat-niet.json"), "--echt"])  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.skipif(
        not (R5_MAP / "callgrootboek.jsonl").is_file(), reason="R5-grootboek ontbreekt"
    )
    def test_canonieke_keten_leest_285_zonder_te_schrijven(self):
        """De werkelijke R5→R1-grootboeken, alleen-lezen: 5 × 57."""
        namen = ("R5", "R4", "R3", "R2", "R1")
        bestanden = []
        for proef in (runner.PROEVEN[n] for n in namen):
            g = proef.opslag.grootboek
            bestanden += [g, g.with_name(g.name + ".anker.json")]
        voor = {p: _sha(p) for p in bestanden}
        keten = runner._lees_voorganger(
            _omgeving(_FakeProvider()), runner.PROEVEN["R6"], None
        )
        assert [b.identiteit for b in keten] == [gb.R5, gb.R4, gb.R3, gb.R2, gb.R1]
        assert [b.samenvatting()["totaal"] for b in keten] == [57] * 5
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
        assert len({g["id"] for g in selectie["gevallen"]}) == 9  # geen duplicaten
        assert "herhaal_ids" not in selectie
        assert "geen onafhankelijke gold" in selectie["status"]
        mk.controleer_t_selectie(selectie, *_t_bronnen())

    def test_andere_bronnen_geweigerd(self):
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_t_selectie(b"{}", b"{}", bron_pad="x")

    def test_geen_g_invoer(self):
        assert not hasattr(mk, "maak_g_invoer")

    @bron_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        t = tmp_path / "t.json"
        assert mk.main(["--t-doel", str(t)]) == 0
        with pytest.raises(FileExistsError):
            mk.main(["--t-doel", str(t)])


class TestVastgelegdeR6Invoer:
    @pytest.mark.skipif(not R6_SELECTIE.is_file(), reason="R6-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert runner.PROEVEN["R6"].t_ontwikkelinvoer_sha256 == _sha(R6_SELECTIE)
        assert _sha(R6_SELECTIE) == runner.R6_T_ONTWIKKELINVOER_SHA256

    @bron_nodig
    @pytest.mark.skipif(not R6_SELECTIE.is_file(), reason="R6-selectie ontbreekt")
    def test_vastgelegde_invoer_is_reproduceerbaar(self):
        vast = json.loads(R6_SELECTIE.read_text(encoding="utf-8"))
        assert vast == mk.maak_t_selectie(
            *_t_bronnen(), bron_pad=vast["herkomst"]["bron_pad_aanroep"]
        )


# --- runner: binding vóór reservering/netwerk ---------------------------------------------


class TestR6Runner:
    def test_ontwikkelcalls_over_de_volledige_keten(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        uitkomst = _t(_omgeving(provider), tmp_path, pad,
                      _r6(t_ontwikkelinvoer_sha256=_sha(pad)),
                      _voorgangers(tmp_path), nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        stand = uitkomst["voorganger_grootboek"]
        assert [k["proef_id"] for k in stand["keten"]] == [
            gb.R5.proef_id,
            gb.R4.proef_id,
            gb.R3.proef_id,
            gb.R2.proef_id,
            gb.R1.proef_id,
        ]
        assert (stand["keten_totaal"], stand["cumulatief_max"]) == (10, 325)

    def test_andere_t_ontwikkelinvoer_voor_grootboek_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            _t(_omgeving(provider), tmp_path, pad, runner.PROEVEN["R6"],
               _voorgangers(tmp_path), nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r6" / "callgrootboek.jsonl").exists()

    def test_keten_zonder_r1_geweigerd_voor_grootboek(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        o5, o4, o3, o2, _ = _voorgangers(tmp_path)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="onvolledig"):
            _t(_omgeving(provider), tmp_path, pad,
               _r6(t_ontwikkelinvoer_sha256=_sha(pad)), (o5, o4, o3, o2),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r6" / "callgrootboek.jsonl").exists()

    def test_cumulatieve_grens_voor_elke_call_geweigerd(self, tmp_path):
        """Grens tijdelijk op 291 (285 + 6) om de runnerroute te bewijzen."""
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        voorgangers = _voorgangers(tmp_path, 57, 57, 57, 57, 57)
        object.__setattr__(gb.R6, "cumulatief_max", 291)
        try:
            with pytest.raises(gb.BudgetSchendingError, match="291"):
                _t(_omgeving(provider), tmp_path, pad,
                   _r6(t_ontwikkelinvoer_sha256=_sha(pad)), voorgangers,
                   nieuw_grootboek=True, max_calls=4)  # fmt: skip
        finally:
            object.__setattr__(gb.R6, "cumulatief_max", 325)
        assert gb.R6.cumulatief_max == 325
        assert provider.aanroepen == []
        boek = gb.Grootboek.lees(tmp_path / "r6" / "callgrootboek.jsonl",
                                 identiteit=gb.R6)  # fmt: skip
        assert boek.samenvatting()["totaal"] == 0

    def test_eindfase_zonder_freeze_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R6"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_r5_freeze_past_niet_op_r6(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R5"], "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 20), runner.PROEVEN["R6"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(
        not (R5_MAP / "eindfreeze-t-v1.json").is_file(), reason="geen R5-freeze"
    )
    def test_echte_r5_eindfreeze_geweigerd_op_r6(self, tmp_path):
        """De definitieve R5-freeze (T/11) start geen R6-call."""
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="past niet"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R6"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True, freeze=R5_MAP / "eindfreeze-t-v1.json")  # fmt: skip
        assert provider.aanroepen == []


class TestDroogR6:
    @pytest.mark.skipif(not R6_SELECTIE.is_file(), reason="R6-selectie ontbreekt")
    def test_droog_t_negen_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R6", "--fase", "ontwikkeling", "--gevallen",
                            str(R6_SELECTIE), "--uitmap", str(tmp_path), "--droog",
                            "--timeout", "60", "--max-tokens-t", "1500"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R6_ID, 9)
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_eindfreeze_draagt_de_r6_identiteit(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        droog = asyncio.run(runner.droogrun("t_eind", pad, tmp_path / "d",
                                            proef=runner.PROEVEN["R6"]))  # fmt: skip
        assert droog["freezevelden"]["proef_id"] == R6_ID
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
