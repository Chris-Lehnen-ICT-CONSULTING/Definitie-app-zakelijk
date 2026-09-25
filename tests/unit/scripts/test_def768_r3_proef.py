"""DEF-768 ronde 3 — proefidentiteit DEF-768-AI-20260924-R3, offline.

Besluit Chris 24-09 (reports/DEF-768-AI-20260924-R2/uitkomst-en-vervolg-v2.md):
maximaal 60 aanvullende appcalls (9/4/20/8/16 + 3 technische reserve),
cumulatief maximaal 174 vanaf de 114 werkelijke R1+R2-calls. R1 en R2 zijn
gesloten voor echte calls en alleen-lezen voorgangers.

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
from tests.unit.scripts.test_def768_r2_proefidentiteit import _binding_voor

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r3_ontwikkelinvoer as mk
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R3_ID = "DEF-768-AI-20260924-R3"
R2_EINDSET = (
    ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-eindset-v1.json"
)
R2_G = ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-g-invoer-v1.json"
R3_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260924-R3" / "ontwikkelselectie-v1.json"
R3_G = ROOT / "reports" / "DEF-768-AI-20260924-R3" / "g-ontwikkelinvoer-v1.json"
bron_nodig = pytest.mark.skipif(
    not (R2_EINDSET.is_file() and R2_G.is_file()),
    reason="git-ignored R2-bronbestanden ontbreken",
)


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _boek(pad: Path, identiteit, n: int):
    """Grootboek met `n` reserveringen, fases op volgorde tot hun cap gevuld."""
    boek = gb.Grootboek.nieuw(pad / "callgrootboek.jsonl", identiteit=identiteit)
    plekken = [
        (fase, i) for fase, cap in identiteit.fasecaps.items() for i in range(cap)
    ]
    for fase, i in plekken[:n]:
        boek.reserveer(
            fase,
            f"{fase}|v-{i}",
            invoer_sha256="a" * 64,
            binding=_binding_voor(identiteit, fase),
        )
    return boek


def _voorgangers(tmp_path: Path, r1: int = 2, r2: int = 2):
    """(R2-opslag, R1-opslag) in tmp met r1/r2 reserveringen."""
    o1 = runner.Proefopslag(tmp_path / "r1")
    o2 = runner.Proefopslag(tmp_path / "r2")
    _boek(o1.root, gb.R1, r1)
    _boek(o2.root, gb.R2, r2)
    return (o2, o1)


def _r3(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R3"], **anders)


# --- identiteit en cumulatieve grens ---------------------------------------------------


class TestIdentiteit:
    def test_r3_caps_reserve_en_voorganger(self):
        r3 = gb.R3
        assert r3.proef_id == R3_ID
        assert dict(r3.fasecaps) == {
            "ontwikkeling": 9,
            "g_ontwikkeling": 4,
            "t_eind": 20,
            "t_herhaling": 8,
            "g": 16,
        }
        assert (r3.reserve_max, r3.totaal_max) == (3, 60)
        assert r3.voorganger is gb.R2
        assert r3.cumulatief_max == 174
        assert "freeze_sha256" in r3.bindingsvelden
        assert {g.naam for g in r3.eindgroepen} == {"t", "g"}

    def test_r3_is_een_bekende_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "g.jsonl", identiteit=gb.R3)
        assert gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R3) is not None
        assert boek.samenvatting()["totaal_max"] == 60
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(tmp_path / "g.jsonl", identiteit=gb.R2)


class TestCumulatief:
    @staticmethod
    def _keten(tmp_path, r1, r2, r3):
        o2, o1 = _voorgangers(tmp_path, r1, r2)
        eigen = _boek(tmp_path / "r3", gb.R3, r3)
        return (
            eigen,
            gb.Grootboek.lees(o2.grootboek, identiteit=gb.R2),
            gb.Grootboek.lees(o1.grootboek, identiteit=gb.R1),
        )

    def test_precies_174_past(self, tmp_path):
        eigen, r2, r1 = self._keten(tmp_path, 57, 57, 0)
        gb.controleer_cumulatief(eigen, [r2, r1], 60)

    def test_boven_174_geweigerd(self, tmp_path):
        eigen, r2, r1 = self._keten(tmp_path, 57, 57, 57)  # fasecaps vol
        gb.controleer_cumulatief(eigen, [r2, r1], 3)  # 174
        with pytest.raises(gb.BudgetSchendingError, match="174"):
            gb.controleer_cumulatief(eigen, [r2, r1], 4)

    def test_r1_telt_mee(self, tmp_path):
        """Alleen R2 meetellen zou 57 R1-calls vergeten."""
        eigen, r2, _ = self._keten(tmp_path, 57, 57, 0)
        with pytest.raises(gb.BudgetSchendingError, match="keten"):
            gb.controleer_cumulatief(eigen, [r2], 1)

    def test_verkeerde_volgorde_geweigerd(self, tmp_path):
        eigen, r2, r1 = self._keten(tmp_path, 1, 1, 0)
        with pytest.raises(gb.BudgetSchendingError, match="keten"):
            gb.controleer_cumulatief(eigen, [r1, r2], 1)

    def test_r2_met_een_voorganger_ongewijzigd(self, tmp_path):
        o1 = runner.Proefopslag(tmp_path / "r1")
        _boek(o1.root, gb.R1, 57)
        eigen = _boek(tmp_path / "r2", gb.R2, 0)
        r1 = gb.Grootboek.lees(o1.grootboek, identiteit=gb.R1)
        gb.controleer_cumulatief(eigen, r1, 60)
        with pytest.raises(gb.BudgetSchendingError, match="117"):
            gb.controleer_cumulatief(eigen, r1, 61)


# --- proeven en afsluiting ----------------------------------------------------------------


class TestProeven:
    def test_r3_eigen_opslag_en_freeze_en_na_afsluiting_dicht(self):
        """Ronde 4: R3 is afgerond (57/60) en alleen-lezen voorganger."""
        r3 = runner.PROEVEN["R3"]
        assert r3.identiteit is gb.R3
        assert r3.opslag.root == ROOT / "reports" / "DEF-768-AI-20260924-R3"
        assert (r3.echt_toegestaan, r3.freeze_vereist) == (False, True)
        assert runner.STANDAARD_PROEF is runner.PROEVEN["R1"]

    @pytest.mark.parametrize("naam", ["R1", "R2"])
    def test_r1_en_r2_gesloten_voor_echt(self, naam):
        assert runner.PROEVEN[naam].echt_toegestaan is False

    @pytest.mark.parametrize("naam", ["R1", "R2"])
    def test_cli_echt_op_gesloten_ronde_geweigerd(self, naam, monkeypatch, tmp_path):
        def verboden(**_):
            raise AssertionError("geen omgeving voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit):
            runner.main(["--proef", naam, "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip

    def test_echte_omgeving_op_r2_geweigerd(self, tmp_path):
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, runner.PROEVEN["R2"].opslag,
                                      runner.PROEVEN["R2"])  # fmt: skip


# --- ontwikkelinvoer ------------------------------------------------------------------------


class TestOntwikkelinvoerMaker:
    @bron_nodig
    def test_selectie_kopieert_zeven_r2_gevallen_exact(self):
        selectie = mk.maak_t_selectie(R2_EINDSET.read_bytes(), bron_pad="x")
        bron = {g["id"]: g for g in json.loads(R2_EINDSET.read_bytes())["gevallen"]}
        ids = [g["id"] for g in selectie["gevallen"]]
        assert ids[:7] == ["R215", "R220", "R209", "R203", "R214", "R208", "R217"]
        for geval in selectie["gevallen"][:7]:
            assert json.dumps(geval, sort_keys=True) == json.dumps(
                bron[geval["id"]], sort_keys=True
            )
        assert len(ids) == 9 and len(set(ids)) == 9
        assert selectie["herkomst"]["bron_sha256"] == mk.T_BRON_SHA256
        assert "herhaal_ids" not in selectie
        mk.controleer_t_selectie(selectie, R2_EINDSET.read_bytes())

    @bron_nodig
    def test_twee_positieve_voorstelgevallen_zonder_buren_met_brongrond(self):
        selectie = mk.maak_t_selectie(R2_EINDSET.read_bytes(), bron_pad="x")
        nieuw = selectie["gevallen"][7:]
        assert [g["id"] for g in nieuw] == list(selectie["herkomst"]["nieuwe_ids"])
        for geval in nieuw:
            assert geval["buren"] == [] and geval["verwacht_per_buur"] == []
            assert geval["verwacht"] == "review_required"
            # Het voorgestelde zusterbegrip staat letterlijk in de bron.
            zuster = mk.VERWACHTE_ZUSTERS[geval["id"]]
            assert zuster in geval["bronnen"][0]["snippet"]
            assert zuster not in geval["tekst"]
        pi.valideer_gevallenbestand(selectie, herhaal_vereist=False)
        assert "geen onafhankelijke gold" in selectie["status"]

    @bron_nodig
    def test_nieuwe_gevallen_lekken_geen_labels(self):
        from services.validation.ess05_assessment_service import laad_ess05_norm

        norm = laad_ess05_norm()
        for geval in mk.maak_t_selectie(R2_EINDSET.read_bytes(), bron_pad="x")[
            "gevallen"
        ][7:]:
            prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_andere_bron_geweigerd(self):
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_t_selectie(b'{"gevallen": []}', bron_pad="x")
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_g_invoer(b'{"invoeren": []}', bron_pad="x")

    @bron_nodig
    def test_g_invoer_vier_r2_invoeren_exact_met_actuele_binding(self):
        g = mk.maak_g_invoer(R2_G.read_bytes(), bron_pad="x")
        bron = json.loads(R2_G.read_bytes())
        assert g["invoeren"] == bron["invoeren"]
        assert len(g["invoeren"]) == 4
        assert g["g_teksten"]["basis"] == bron["g_teksten"]["basis"]
        actueel = hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        assert g["g_teksten"]["actueel"]["sha256"] == actueel
        assert g["herkomst"]["bron_sha256"] == mk.G_BRON_SHA256
        runner.controleer_g_teksten(g)

    @bron_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        t, g = tmp_path / "t.json", tmp_path / "g.json"
        args = ["--t-bron", str(R2_EINDSET), "--g-bron", str(R2_G),
                "--t-doel", str(t), "--g-doel", str(g)]  # fmt: skip
        assert mk.main(args) == 0
        with pytest.raises(FileExistsError):
            mk.main(args)


class TestVastgelegdeR3Invoer:
    @pytest.mark.skipif(not R3_SELECTIE.is_file(), reason="R3-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert runner.PROEVEN["R3"].t_ontwikkelinvoer_sha256 == _sha(R3_SELECTIE)

    @pytest.mark.skipif(not R3_G.is_file(), reason="R3-G-invoer ontbreekt")
    def test_runner_bindt_de_vastgelegde_g_invoer(self):
        assert runner.PROEVEN["R3"].g_ontwikkelinvoer_sha256 == _sha(R3_G)
        # Ronde 4 wijzigde de G-instructie: de R3-G-binding (d8a0663c…) past
        # niet meer bij de code en wordt geweigerd.
        with pytest.raises(pi.InvoerfoutError, match="bevroren hash"):
            runner.controleer_g_teksten(json.loads(R3_G.read_text(encoding="utf-8")))

    def test_r2_behoudt_zijn_g_binding(self):
        r2 = runner.PROEVEN["R2"]
        assert r2.g_ontwikkelinvoer_sha256 == runner.G_ONTWIKKELINVOER_SHA256
        assert r2.t_ontwikkelinvoer_sha256 is None


# --- runner: binding vóór reservering/netwerk ---------------------------------------------


def _t(omg, tmp_path, pad, proef, voorgangers, fase="ontwikkeling", **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r3"),
            proef=proef,
            voorganger_opslag=voorgangers,
            **kw,
        )
    )


class TestR3Runner:
    def test_ontwikkelcalls_op_de_gebonden_selectie(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r3(t_ontwikkelinvoer_sha256=_sha(pad))
        provider = _FakeProvider()
        uitkomst = _t(_omgeving(provider), tmp_path, pad, proef,
                      _voorgangers(tmp_path), nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        boek = gb.Grootboek.open(tmp_path / "r3" / "callgrootboek.jsonl",
                                 identiteit=gb.R3)  # fmt: skip
        assert boek.samenvatting()["per_fase"]["ontwikkeling"] == 4
        assert uitkomst["voorganger_grootboek"] is not None

    def test_andere_t_ontwikkelinvoer_voor_grootboek_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r3(t_ontwikkelinvoer_sha256="0" * 64)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            _t(_omgeving(provider), tmp_path, pad, proef, _voorgangers(tmp_path),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "r3" / "callgrootboek.jsonl").exists()

    def test_cumulatieve_grens_voor_elke_call_geweigerd(self, tmp_path):
        """Runner roept de ketencontrole vóór reservering en netwerk aan.

        57+57 volle voorgangers + 8 gepland (4 gevallen × 2 stappen) haalt 174 niet; de grens wordt hier
        tijdelijk op 120 gezet om de weigeringsroute in de runner te bewijzen.
        """
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r3(t_ontwikkelinvoer_sha256=_sha(pad))
        provider = _FakeProvider()
        voorgangers = _voorgangers(tmp_path, r1=57, r2=57)
        object.__setattr__(gb.R3, "cumulatief_max", 120)
        try:
            with pytest.raises(gb.BudgetSchendingError, match="120"):
                _t(_omgeving(provider), tmp_path, pad, proef, voorgangers,
                   nieuw_grootboek=True, max_calls=4)  # fmt: skip
        finally:
            object.__setattr__(gb.R3, "cumulatief_max", 174)
        assert gb.R3.cumulatief_max == 174
        assert provider.aanroepen == []
        boek = gb.Grootboek.lees(tmp_path / "r3" / "callgrootboek.jsonl",
                                 identiteit=gb.R3)  # fmt: skip
        assert boek.samenvatting()["totaal"] == 0

    def test_zonder_r1_voorganger_geweigerd(self, tmp_path):
        """Een voorgangerketen zonder R1 is onvolledig; niets gereserveerd."""
        pad = _gevallenbestand(tmp_path, 9)
        proef = _r3(t_ontwikkelinvoer_sha256=_sha(pad))
        o2, _ = _voorgangers(tmp_path)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError):
            _t(_omgeving(provider), tmp_path, pad, proef, (o2,),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_eindfase_zonder_freeze_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t(_omgeving(provider), tmp_path, pad, runner.PROEVEN["R3"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_r2_freeze_past_niet_op_r3(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        velden = runner.freezevelden(omg, runner.PROEVEN["R2"], "t")
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(velden), encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 20), runner.PROEVEN["R3"],
               _voorgangers(tmp_path), fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    def test_g_ontwikkeling_op_andere_invoer_geweigerd(self, tmp_path):
        proef = _r3(g_ontwikkelinvoer_sha256="0" * 64)
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
                    opslag=runner.Proefopslag(tmp_path / "r3"),
                    proef=proef,
                    voorganger_opslag=_voorgangers(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert provider.aanroepen == []

    @pytest.mark.skipif(not R3_G.is_file(), reason="R3-G-invoer ontbreekt")
    def test_g_ontwikkeling_r3_vier_actuele_calls(self, tmp_path):
        """G-ontwikkeling legt de huidige instructie vast (alleen_actueel); de
        sluiting van R3 zit in de CLI (echt_toegestaan), niet in deze functie."""
        provider = _FakeProvider(tekst="Ontologische categorie: type\nPakket.")
        uitkomst = asyncio.run(
            runner.voer_g_fase(
                _omgeving(provider),
                fase="g_ontwikkeling",
                g_invoerpad=R3_G,
                uitmap=tmp_path / "uit",
                opslag=runner.Proefopslag(tmp_path / "r3"),
                proef=runner.PROEVEN["R3"],
                voorganger_opslag=_voorgangers(tmp_path),
                nieuw_grootboek=True,
            )
        )
        assert len(provider.aanroepen) == 4
        assert (
            uitkomst["g_actueel_instructie_sha256"]
            == hashlib.sha256(pi.huidige_g_instructie().encode()).hexdigest()
        )


class TestDroogR3:
    @pytest.mark.skipif(not R3_SELECTIE.is_file(), reason="R3-selectie ontbreekt")
    def test_droog_t_negen_zonder_grootboek(self, tmp_path):
        code = runner.main(["--proef", "R3", "--fase", "ontwikkeling", "--gevallen",
                            str(R3_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R3_ID, 9)
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_t_op_andere_selectie_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkel"):
            asyncio.run(runner.droogrun("ontwikkeling", pad, tmp_path / "d",
                                        proef=runner.PROEVEN["R3"]))  # fmt: skip

    def test_droog_eindfreeze_draagt_de_r3_identiteit(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 20)
        droog = asyncio.run(runner.droogrun("t_eind", pad, tmp_path / "d",
                                            proef=runner.PROEVEN["R3"]))  # fmt: skip
        assert droog["freezevelden"]["proef_id"] == R3_ID
        # De droge freeze volgt de actuele T-versie (R4: /8).
        # ADR-003: de droge freeze volgt de actuele tweestaps-T (/14 plus
        # verificatieprompt); zo past zij niet meer op de eenstaps-/13-freeze.
        assert droog["freezevelden"]["prompt_version"] == "ess05-assess/14"
        assert droog["freezevelden"]["verification_prompt_version"] == (
            "ess05-verify/2"
        )
