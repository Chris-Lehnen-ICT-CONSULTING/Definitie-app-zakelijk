"""DEF-768 ronde 7 — proefidentiteit DEF-768-AI-20260925-R7, offline, alleen T.

Besluit Chris 25-09 (reports/DEF-768-AI-20260925-R6/uitkomst-en-vervolg-v1.md,
concreet vervolgvoorstel, 'ja'): maximaal 40 nieuwe uitsluitend T-appcalls
(9 ontwikkeling + 20 T-eind + 8 T-herhaling + 3 alleen technisch), cumulatief
maximaal 362 vanaf 322 werkelijke R1–R6-calls. Geen G-fases: G en
G-ontwikkeling worden fail-closed geweigerd. Oude reserves gesloten: R1 t/m R6
zijn alleen-lezen voorgangers.

Ontwikkelinvoer (bekende ontwikkeldata, geen onafhankelijke gold): R614
tweemaal (R614, R614-D2: alleen de technische pogingidentiteit verschilt),
R610, R620, R606 uit de R6-eindset en R514, R508, R504, R516 uit de R5-eindset.

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

try:  # de R7-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r7_ontwikkelinvoer as mk
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk = None

R7_ID = "DEF-768-AI-20260925-R7"
R7_MAP = ROOT / "reports" / R7_ID
R6_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R6"
R5_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R5"
R6_EINDSET = R6_MAP / "onafhankelijke-eindset-v1.json"
R5_EINDSET = R5_MAP / "onafhankelijke-eindset-v1.json"
R7_SELECTIE = R7_MAP / "ontwikkelselectie-v1.json"
bron_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (R6_EINDSET, R5_EINDSET)),
    reason="git-ignored R5/R6-bronbestanden ontbreken",
)
T_IDS = [
    "R614",
    "R614-D2",
    "R514",
    "R508",
    "R504",
    "R516",
    "R610",
    "R620",
    "R606",
]
GESLOTEN = ["R1", "R2", "R3", "R4", "R5", "R6"]
G_FASES = ["g", "g_ontwikkeling"]
KETEN = ("R6", "R5", "R4", "R3", "R2", "R1")


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _t_bronnen() -> tuple[bytes, bytes]:
    return R6_EINDSET.read_bytes(), R5_EINDSET.read_bytes()


def _voorgangers(tmp_path: Path, r1=2, r2=2, r3=2, r4=2, r5=2, r6=2):
    """(R6- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    opslagen = []
    for naam, identiteit, n in (
        ("r6", gb.R6, r6),
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


def _r7(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R7"], **anders)


def _t(omg, tmp_path, pad, proef, voorgangers, fase="ontwikkeling", **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r7"),
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
    def test_r7_alleen_t_caps_reserve_en_voorganger(self):
        r7 = gb.R7
        assert r7.proef_id == R7_ID
        assert dict(r7.fasecaps) == {"ontwikkeling": 9, "t_eind": 20, "t_herhaling": 8}
        assert (r7.reserve_max, r7.totaal_max) == (3, 40)
        assert r7.voorganger is gb.R6
        assert r7.cumulatief_max == 362
        assert [g.naam for g in r7.eindgroepen] == ["t"]
        assert r7.eindgroep("g") is None
        assert "freeze_sha256" in r7.bindingsvelden
        assert gb.voorgangerketen(r7) == (gb.R6, gb.R5, gb.R4, gb.R3, gb.R2, gb.R1)

    def test_r6_identiteit_ongewijzigd(self):
        assert (gb.R6.cumulatief_max, gb.R6.voorganger, gb.R6.totaal_max) == (
            325,
            gb.R5,
            40,
        )

    def test_r7_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R7)
        assert gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R7) is not None
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R6)

    @pytest.mark.parametrize("fase", G_FASES)
    def test_grootboek_weigert_g_reservering(self, tmp_path, fase):
        boek = gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R7)
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
    def _keten(tmp_path, r1, r2, r3, r4, r5, r6, r7):
        opslagen = _voorgangers(tmp_path, r1, r2, r3, r4, r5, r6)
        eigen = _boek(tmp_path / "r7", gb.R7, r7)
        identiteiten = (gb.R6, gb.R5, gb.R4, gb.R3, gb.R2, gb.R1)
        return eigen, [
            gb.Grootboek.lees(o.grootboek, identiteit=i)
            for o, i in zip(opslagen, identiteiten, strict=True)
        ]

    def test_precies_362_past_en_363_niet(self, tmp_path):
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57, 57, 37, 37)
        gb.controleer_cumulatief(eigen, keten, 3)  # 322 + 37 + 3 = 362
        with pytest.raises(gb.BudgetSchendingError, match="362"):
            gb.controleer_cumulatief(eigen, keten, 4)

    def test_ongebruikt_r6_budget_gaat_niet_over(self, tmp_path):
        """Minder R6-calls (37 van 40) geeft R7 geen extra fasecalls."""
        eigen, keten = self._keten(tmp_path, 57, 57, 57, 57, 57, 37, 37)
        with pytest.raises(gb.BudgetSchendingError):
            eigen.reserveer(
                "ontwikkeling",
                "ontwikkeling|extra",
                invoer_sha256="a" * 64,
                binding=_binding_voor(gb.R7, "ontwikkeling"),
            )
        assert eigen.samenvatting()["totaal"] == 37

    def test_onvolledige_of_verwisselde_keten_geweigerd(self, tmp_path):
        eigen, (r6, r5, r4, r3, r2, r1) = self._keten(tmp_path, 1, 1, 1, 1, 1, 1, 0)
        for keten in (
            [r6, r5, r4, r3, r2],
            [r6],
            [r5, r4, r3, r2, r1],
            [r5, r6, r4, r3, r2, r1],
        ):
            with pytest.raises(gb.BudgetSchendingError, match="keten"):
                gb.controleer_cumulatief(eigen, keten, 1)


# --- proeven en afsluiting ----------------------------------------------------------------


def _geen_omgeving(monkeypatch, *fasen):
    def verboden(**_):
        raise AssertionError("geen omgeving voor een geweigerde ronde of fase")

    async def geen_fase(*_a, **_k):
        raise AssertionError("geen fase voor een geweigerde ronde of fase")

    monkeypatch.setattr(runner, "live_omgeving", verboden)
    for naam in fasen:
        monkeypatch.setattr(runner, naam, geen_fase)


class TestProeven:
    def test_r7_eigen_opslag_en_freeze_gesloten_voor_echt(self):
        """Gemigreerd (ADR-003): R7 is gesloten voor echte calls; de huidige
        tweestaps-T past niet op de R7-freeze en het budget blijft ongewijzigd."""
        r7 = runner.PROEVEN["R7"]
        assert r7.identiteit is gb.R7
        assert r7.opslag.root == R7_MAP
        assert (r7.echt_toegestaan, r7.freeze_vereist) == (False, True)
        assert r7.g_ontwikkelinvoer_sha256 is None
        assert runner.STANDAARD_PROEF is runner.PROEVEN["R1"]

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_oude_rondes_gesloten_voor_echt(self, naam):
        assert runner.PROEVEN[naam].echt_toegestaan is False

    def test_r6_behoudt_zijn_bindingen(self):
        r6 = runner.PROEVEN["R6"]
        assert (r6.identiteit, r6.opslag.root, r6.freeze_vereist) == (
            gb.R6,
            R6_MAP,
            True,
        )
        assert r6.t_ontwikkelinvoer_sha256 == runner.R6_T_ONTWIKKELINVOER_SHA256
        assert r6.g_ontwikkelinvoer_sha256 is None

    @pytest.mark.parametrize("naam", GESLOTEN)
    def test_cli_echt_op_oude_ronde_geweigerd_zonder_omgeving(
        self, monkeypatch, tmp_path, naam
    ):
        _geen_omgeving(monkeypatch, "voer_t_fase")
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

    @pytest.mark.parametrize("naam", ["R6", "R7"])
    @pytest.mark.parametrize("echt", [True, False])
    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_programmatisch_geweigerd_in_t_rondes(self, tmp_path, fase, echt, naam):
        """G bestaat niet in R6 en R7: geweigerd vóór invoer, grootboek en netwerk,
        ook zonder echte omgeving."""
        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=echt)
        with pytest.raises(
            gb.BudgetSchendingError, match=f"bestaat niet in ronde {naam}"
        ):
            _g(omg, tmp_path, fase, runner.PROEVEN[naam])
        assert provider.aanroepen == []
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_droog_geweigerd_in_r7(self, tmp_path, fase):
        with pytest.raises(gb.BudgetSchendingError, match="bestaat niet in ronde R7"):
            asyncio.run(
                runner.droogrun(
                    fase,
                    tmp_path / "bestaat-niet.json",
                    tmp_path / "d",
                    proef=runner.PROEVEN["R7"],
                )
            )
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("modus", ["--echt", "--droog"])
    @pytest.mark.parametrize("fase", G_FASES)
    def test_g_cli_geweigerd_in_r7(self, monkeypatch, tmp_path, fase, modus):
        _geen_omgeving(monkeypatch, "voer_g_fase", "droogrun")
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R7", "--fase", fase, "--g-invoer",
                         str(tmp_path / "bestaat-niet.json"), modus,
                         "--uitmap", str(tmp_path / "uit")])  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []

    def test_echt_r7_alleen_canonieke_opslag(self, tmp_path):
        """ADR-003: R7 is gesloten; de opslagregel blijft gelden voor een
        (hypothetisch) open R7 en de gesloten R7 weigert al eerder."""
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        for opslag in (runner.Proefopslag(tmp_path), runner.PROEVEN["R6"].opslag):
            with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
                runner._controleer_opslag(omg, opslag, _r7(echt_toegestaan=True))
            with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
                runner._controleer_opslag(omg, opslag, runner.PROEVEN["R7"])

    def test_echte_calls_tellen_alleen_tegen_canonieke_voorgangers(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            runner._lees_voorganger(omg, runner.PROEVEN["R7"], _voorgangers(tmp_path))

    def test_cli_echt_r7_gebruikt_de_r7_opslag(self, monkeypatch):
        # ADR-003: R7 is gesloten voor echte calls; dit mechaniekbewijs (routing
        # naar de eigen opslag) draait op een hypothetisch open R7.
        monkeypatch.setitem(runner.PROEVEN, "R7", dataclasses.replace(
            runner.PROEVEN["R7"], echt_toegestaan=True))  # fmt: skip
        gezien: dict = {}

        async def vang(omg, **kwargs):
            gezien.update(kwargs)
            return {
                "aanroepen_gestart": 0,
                "grootboek_na": {"totaal": 0},
                "kosten_usd_bekend": 0,
                "kosten_onbekend": 0,
            }

        monkeypatch.setattr(runner, "live_omgeving", lambda **_k: object())
        monkeypatch.setattr(runner, "voer_t_fase", vang)
        code = runner.main(["--proef", "R7", "--fase", "ontwikkeling", "--gevallen",
                            "x.json", "--echt"])  # fmt: skip
        assert code == 0
        assert gezien["opslag"] == runner.PROEVEN["R7"].opslag
        assert gezien["proef"] is runner.PROEVEN["R7"]
        assert gezien["uitmap"] == R7_MAP

    @pytest.mark.skipif(
        not (R6_MAP / "callgrootboek.jsonl").is_file(), reason="R6-grootboek ontbreekt"
    )
    def test_canonieke_keten_leest_322_zonder_te_schrijven(self):
        """De werkelijke R6→R1-grootboeken, alleen-lezen: 37 + 5 × 57."""
        bestanden = []
        for proef in (runner.PROEVEN[n] for n in KETEN):
            g = proef.opslag.grootboek
            bestanden += [g, g.with_name(g.name + ".anker.json")]
        voor = {p: _sha(p) for p in bestanden}
        keten = runner._lees_voorganger(
            _omgeving(_FakeProvider()), runner.PROEVEN["R7"], None
        )
        assert [b.identiteit for b in keten] == [
            gb.R6,
            gb.R5,
            gb.R4,
            gb.R3,
            gb.R2,
            gb.R1,
        ]
        assert [b.samenvatting()["totaal"] for b in keten] == [37] + [57] * 5
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
            oorsprong = mk.oorsprong_id(geval["id"])
            verwacht = {**bron[oorsprong], "id": geval["id"]}
            assert json.dumps(geval, sort_keys=True) == json.dumps(
                verwacht, sort_keys=True
            ), geval["id"]
        assert selectie["herkomst"]["ontwikkel_ids"] == {"R614-D2": "R614"}
        assert len({g["id"] for g in selectie["gevallen"]}) == 9
        assert "herhaal_ids" not in selectie
        assert "geen onafhankelijke gold" in selectie["status"]
        mk.controleer_t_selectie(selectie, *_t_bronnen())

    @bron_nodig
    def test_r614_pogingen_verschillen_alleen_in_id(self):
        per_id = {
            g["id"]: g
            for g in mk.maak_t_selectie(*_t_bronnen(), bron_pad="x")["gevallen"]
        }
        zonder_id = [
            {k: v for k, v in per_id[i].items() if k != "id"}
            for i in ("R614", "R614-D2")
        ]
        assert zonder_id[0] == zonder_id[1]

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


class TestVastgelegdeR7Invoer:
    @pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert runner.PROEVEN["R7"].t_ontwikkelinvoer_sha256 == _sha(R7_SELECTIE)
        assert _sha(R7_SELECTIE) == runner.R7_T_ONTWIKKELINVOER_SHA256

    @bron_nodig
    @pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-selectie ontbreekt")
    def test_vastgelegde_invoer_is_reproduceerbaar(self):
        vast = json.loads(R7_SELECTIE.read_text(encoding="utf-8"))
        assert vast == mk.maak_t_selectie(
            *_t_bronnen(), bron_pad=vast["herkomst"]["bron_pad_aanroep"]
        )


# --- runner: binding vóór reservering/netwerk ---------------------------------------------


class TestR7Runner:
    def test_ontwikkelcalls_over_de_volledige_keten(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        uitkomst = _t(_omgeving(provider), tmp_path, pad,
                      _r7(t_ontwikkelinvoer_sha256=_sha(pad)),
                      _voorgangers(tmp_path), nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        stand = uitkomst["voorganger_grootboek"]
        assert [k["proef_id"] for k in stand["keten"]] == [
            gb.R6.proef_id,
            gb.R5.proef_id,
            gb.R4.proef_id,
            gb.R3.proef_id,
            gb.R2.proef_id,
            gb.R1.proef_id,
        ]
        assert (stand["keten_totaal"], stand["cumulatief_max"]) == (12, 362)

    def test_andere_t_ontwikkelinvoer_voor_grootboek_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            _t(_omgeving(provider), tmp_path, pad, runner.PROEVEN["R7"],
               _voorgangers(tmp_path), nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r7" / "callgrootboek.jsonl").exists()

    def test_keten_zonder_r1_geweigerd_voor_grootboek(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        zonder_r1 = _voorgangers(tmp_path)[:-1]
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="onvolledig"):
            _t(_omgeving(provider), tmp_path, pad,
               _r7(t_ontwikkelinvoer_sha256=_sha(pad)), zonder_r1,
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r7" / "callgrootboek.jsonl").exists()

    def test_cumulatieve_grens_voor_elke_call_geweigerd(self, tmp_path):
        """Grens tijdelijk op 328 (322 + 6) om de runnerroute te bewijzen."""
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _FakeProvider()
        voorgangers = _voorgangers(tmp_path, 57, 57, 57, 57, 57, 37)
        object.__setattr__(gb.R7, "cumulatief_max", 328)
        try:
            with pytest.raises(gb.BudgetSchendingError, match="328"):
                _t(_omgeving(provider), tmp_path, pad,
                   _r7(t_ontwikkelinvoer_sha256=_sha(pad)), voorgangers,
                   nieuw_grootboek=True, max_calls=4)  # fmt: skip
        finally:
            object.__setattr__(gb.R7, "cumulatief_max", 362)
        assert gb.R7.cumulatief_max == 362
        assert provider.aanroepen == []
        boek = gb.Grootboek.lees(tmp_path / "r7" / "callgrootboek.jsonl",
                                 identiteit=gb.R7)  # fmt: skip
        assert boek.samenvatting()["totaal"] == 0

    def test_eindfase_zonder_freeze_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R7"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_r6_freeze_past_niet_op_r7(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R6"], "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 20), runner.PROEVEN["R7"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    @pytest.mark.skipif(
        not (R6_MAP / "eindfreeze-t-v1.json").is_file(), reason="geen R6-freeze"
    )
    def test_echte_r6_eindfreeze_geweigerd_op_r7(self, tmp_path):
        """De definitieve R6-freeze (T/12) start geen R7-call."""
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="past niet"):
            _t(_omgeving(provider), tmp_path, _gevallenbestand(tmp_path, 20),
               runner.PROEVEN["R7"], _voorgangers(tmp_path), fase="t_eind",
               nieuw_grootboek=True, freeze=R6_MAP / "eindfreeze-t-v1.json")  # fmt: skip
        assert provider.aanroepen == []


class TestDroogR7:
    @pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-selectie ontbreekt")
    def test_droog_t_negen_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R7", "--fase", "ontwikkeling", "--gevallen",
                            str(R7_SELECTIE), "--uitmap", str(tmp_path), "--droog",
                            "--timeout", "60", "--max-tokens-t", "1500"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R7_ID, 9)
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_eindfreeze_draagt_de_r7_identiteit(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        droog = asyncio.run(runner.droogrun("t_eind", pad, tmp_path / "d",
                                            proef=runner.PROEVEN["R7"]))  # fmt: skip
        assert droog["freezevelden"]["proef_id"] == R7_ID
        # ADR-003: de droge freeze volgt de actuele tweestaps-T (/14 plus
        # verificatieprompt); zo past zij niet meer op de eenstaps-/13-freeze.
        # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
        # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
        # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
        # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
        assert droog["freezevelden"]["prompt_version"] == "ess05-assess/19"
        assert droog["freezevelden"]["verification_prompt_version"] == (
            "ess05-verify/4"
        )
        assert droog["freezevelden"]["code_sha256"] == runner.code_sha256()
