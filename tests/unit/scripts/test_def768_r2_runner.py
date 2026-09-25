"""DEF-768 ronde 2 — runnerondersteuning voor DEF-768-AI-20260924-R2, offline.

Providergrens is een fake; alles daarboven is productie. Bewijst runner-
mechaniek (identiteit, opslag, caps, freeze, eindbinding, G-ontwikkeling,
cumulatieve grens, droog/preflight) en uitdrukkelijk géén modelkwaliteit.
"""

from __future__ import annotations

import asyncio
import copy
import json
import sys
from pathlib import Path

import pytest

from services.ai.model_router import ModelRouter
from tests.unit.scripts.test_def768_ess05_proefrunner import (
    G_INVOER,
    ROOT,
    _FakeProvider,
    _g_invoer_actueel,
    _gevallenbestand,
    _json,
    _omgeving,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r2_ontwikkelselectie as sel
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R1 = runner.PROEVEN["R1"]
R2 = runner.PROEVEN["R2"]


def _opslag(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r2")


def _voorganger(tmp_path: Path, n: int = 2) -> runner.Proefopslag:
    """Een R1-grootboek (tmp) met n ontwikkelreserveringen als voorganger."""
    opslag = runner.Proefopslag(tmp_path / "r1")
    if opslag.grootboek.exists():  # hervatten in dezelfde test
        return opslag
    boek = gb.Grootboek.nieuw(opslag.grootboek)
    for i in range(n):
        boek.reserveer("ontwikkeling", f"ontwikkeling|v-{i}", invoer_sha256="a" * 64)
    return opslag


def _stand(tmp_path: Path) -> dict:
    return gb.Grootboek.open(
        _opslag(tmp_path).grootboek, identiteit=gb.R2
    ).samenvatting()


def _freeze(tmp_path: Path, omg, soort: str, naam: str = "freeze.json", **anders):
    velden = {**runner.freezevelden(omg, R2, soort), "toelichting": "test", **anders}
    for sleutel, waarde in list(velden.items()):
        if waarde is None:
            del velden[sleutel]
    pad = tmp_path / naam
    pad.write_text(json.dumps(velden), encoding="utf-8")
    return pad


def _t(omg, tmp_path, pad, fase="ontwikkeling", **kwargs):
    kwargs.setdefault("voorganger_opslag", _voorganger(tmp_path))
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag(tmp_path),
            proef=R2,
            **kwargs,
        )
    )


def _g(omg, tmp_path, pad, fase="g", **kwargs):
    kwargs.setdefault("voorganger_opslag", _voorganger(tmp_path))
    return asyncio.run(
        runner.voer_g_fase(
            omg,
            fase=fase,
            g_invoerpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag(tmp_path),
            proef=R2,
            **kwargs,
        )
    )


class TestProeven:
    def test_standaard_is_ronde1_en_ronde2_heeft_eigen_opslag(self):
        assert runner.STANDAARD_PROEF is R1
        assert R1.identiteit is gb.R1 and R2.identiteit is gb.R2
        assert R1.opslag == runner.CANONIEKE_OPSLAG
        assert R2.opslag.root == ROOT / "reports" / "DEF-768-AI-20260924-R2"
        assert R2.opslag.grootboek != R1.opslag.grootboek
        # Ronde 3: R2 is afgesloten voor echte calls (alleen-lezen voorganger).
        assert (R1.echt_toegestaan, R2.echt_toegestaan) == (False, False)
        assert (R1.freeze_vereist, R2.freeze_vereist) == (False, True)

    def test_parser_kiest_zonder_proef_ronde1(self):
        args = runner._parser().parse_args(
            ["--fase", "ontwikkeling", "--gevallen", "x.json", "--droog"]
        )
        assert args.proef == "R1"
        assert args.uitmap is None


class TestCLI:
    @staticmethod
    def _geen_omgeving(monkeypatch):
        def geen(**_kwargs):
            raise AssertionError("live_omgeving mag niet worden gebouwd")

        monkeypatch.setattr(runner, "live_omgeving", geen)

    def test_echt_zonder_proef_weigert_de_gesloten_ronde1(self, monkeypatch):
        self._geen_omgeving(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--fase", "t_eind", "--gevallen", "x.json", "--echt"])
        assert exc.value.code != 0

    def test_echt_r2_is_na_afsluiting_geweigerd(self, monkeypatch):
        """Ronde 3: R2 is afgerond en alleen nog alleen-lezen voorganger."""
        self._geen_omgeving(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            runner.main(
                ["--proef", "R2", "--fase", "ontwikkeling", "--gevallen", "x.json",
                 "--echt"]
            )  # fmt: skip
        assert exc.value.code != 0

    def test_echt_r7_gebruikt_de_r7_opslag_en_rapportroot(self, monkeypatch):
        """Ronde 7: R1-R6 gesloten; de open ronde R7 volgt haar eigen opslag."""
        import dataclasses

        # ADR-003: R7 is gesloten voor echte calls; dit mechaniekbewijs (routing
        # naar de eigen opslag) draait op een hypothetisch open R7.
        monkeypatch.setitem(runner.PROEVEN, "R7", dataclasses.replace(
            runner.PROEVEN["R7"], echt_toegestaan=True))  # fmt: skip
        r7 = runner.PROEVEN["R7"]
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
        code = runner.main(
            ["--proef", "R7", "--fase", "ontwikkeling", "--gevallen", "x.json",
             "--echt"]
        )  # fmt: skip
        assert code == 0
        assert gezien["opslag"] == r7.opslag
        assert gezien["proef"] is r7
        assert gezien["uitmap"] == r7.opslag.root
        assert gezien["freeze"] is None

    def test_echt_r7_met_ander_grootboek_geweigerd(self, monkeypatch, tmp_path):
        self._geen_omgeving(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            runner.main(
                ["--proef", "R7", "--fase", "ontwikkeling", "--gevallen", "x.json",
                 "--echt", "--grootboek", str(R1.opslag.grootboek)]
            )  # fmt: skip
        assert exc.value.code != 0

    def test_g_ontwikkeling_bestaat_niet_in_ronde1(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            runner.main(
                ["--fase", "g_ontwikkeling", "--g-invoer", str(G_INVOER), "--droog",
                 "--uitmap", str(tmp_path)]
            )  # fmt: skip
        assert exc.value.code != 0
        assert list(tmp_path.iterdir()) == []


class TestOpslag:
    def test_echte_calls_in_ronde1_gesloten(self, tmp_path):
        import dataclasses

        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            asyncio.run(
                runner.voer_t_fase(
                    omg,
                    fase="ontwikkeling",
                    gevallenpad=_gevallenbestand(tmp_path, 1),
                    uitmap=tmp_path / "uit",
                    opslag=R1.opslag,
                )
            )
        assert provider.aanroepen == []

    def test_echte_calls_r2_na_afsluiting_geweigerd(self, tmp_path):
        """Ronde 3: R2 is gesloten; ook in de eigen opslag geen echte call."""
        import dataclasses

        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 1), nieuw_grootboek=True)
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()


class TestTOntwikkeling:
    def test_ontwikkelcalls_in_het_r2_grootboek(self, tmp_path):
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide, dus in de cap van 9 starten
        # hier 4 van de 9 gevallen (de eigenschap hieronder blijft gelijk).
        provider = _FakeProvider()
        uitkomst = _t(
            _omgeving(provider),
            tmp_path,
            _gevallenbestand(tmp_path, 9),
            nieuw_grootboek=True,
            max_calls=4,
        )
        assert len(provider.aanroepen) == 4
        stand = _stand(tmp_path)
        assert stand["proef_id"] == "DEF-768-AI-20260924-R2"
        assert stand["per_fase"]["ontwikkeling"] == 4
        assert uitkomst["proef_id"] == "DEF-768-AI-20260924-R2"
        assert uitkomst["voorganger_grootboek"]["totaal"] == 2
        assert uitkomst["voorganger_grootboek"]["proef_id"] == gb.PROEF_ID

    def test_tiende_geval_boven_de_cap_voor_elke_call(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="fasecap"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 10),
                nieuw_grootboek=True,
            )
        assert provider.aanroepen == []

    def test_zonder_voorgangergrootboek_niets_aangemaakt(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="ontbreekt"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 1),
                nieuw_grootboek=True,
                voorganger_opslag=runner.Proefopslag(tmp_path / "leeg"),
            )
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()

    def test_voorganger_moet_ronde1_zijn(self, tmp_path):
        ander = runner.Proefopslag(tmp_path / "ander")
        gb.Grootboek.nieuw(ander.grootboek, identiteit=gb.R2)
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="hoort niet bij"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 1),
                nieuw_grootboek=True,
                voorganger_opslag=ander,
            )
        assert provider.aanroepen == []

    def test_freeze_buiten_een_eindfase_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        with pytest.raises(gb.BudgetSchendingError, match="eindfase"):
            _t(
                omg,
                tmp_path,
                _gevallenbestand(tmp_path, 1),
                nieuw_grootboek=True,
                freeze=_freeze(tmp_path, omg, "t"),
            )
        assert provider.aanroepen == []


class TestTEind:
    def test_zonder_freeze_geen_call(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 5),
                fase="t_eind",
                nieuw_grootboek=True,
            )
        assert provider.aanroepen == []

    def test_freeze_gaat_in_de_eindbinding_en_herhaling_volgt(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        eind = _gevallenbestand(tmp_path, 5)
        freeze = _freeze(tmp_path, omg, "t")
        uitkomst = _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True,
                      freeze=freeze)  # fmt: skip
        assert len(provider.aanroepen) == 5
        assert uitkomst["eindbinding"]["freeze_sha256"] == runner._sha_bestand(freeze)
        ander = _freeze(tmp_path, omg, "t", naam="ander.json", toelichting="anders")
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            _t(omg, tmp_path, eind, fase="t_herhaling", freeze=ander)
        assert len(provider.aanroepen) == 5
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide: van de 8 herhalingen passen er
        # 4 in de fasecap van 8 (de eigenschap hieronder blijft gelijk).
        _t(omg, tmp_path, eind, fase="t_herhaling", freeze=freeze, max_calls=4)
        assert len(provider.aanroepen) == 9
        boek = gb.Grootboek.open(_opslag(tmp_path).grootboek, identiteit=gb.R2)
        bindingen = {
            json.dumps(r["binding"], sort_keys=True) for r in boek._reserveringen()
        }
        assert len(bindingen) == 1

    @pytest.mark.parametrize(
        "veld",
        [
            "schema",
            "proef_id",
            "groep",
            "code_sha256",
            "effectieve_config_sha256",
            "prompt_version",
            "system_prompt_sha256",
            "norm_sha256",
        ],
    )
    def test_afwijkend_of_ontbrekend_freezeveld_geweigerd(self, tmp_path, veld):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        eind = _gevallenbestand(tmp_path, 5)
        for naam, waarde in (("afwijkend.json", "x"), ("ontbrekend.json", None)):
            freeze = _freeze(tmp_path, omg, "t", naam=naam, **{veld: waarde})
            with pytest.raises(gb.BudgetSchendingError, match=veld):
                _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True,
                   freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()

    @pytest.mark.parametrize(
        ("veld", "waarde"),
        [("dataset_sha256", "b" * 64), ("herhaal_ids", ["X-00", "X-01"])],
    )
    def test_vastgelegde_dataset_moet_kloppen(self, tmp_path, veld, waarde):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        eind = _gevallenbestand(tmp_path, 5)
        freeze = _freeze(tmp_path, omg, "t", **{veld: waarde})
        with pytest.raises(gb.BudgetSchendingError, match=veld):
            _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        juist = _freeze(
            tmp_path,
            omg,
            "t",
            naam="juist.json",
            dataset_sha256=runner._sha_bestand(eind),
            herhaal_ids=["X-00", "X-01", "X-02", "X-03"],
        )
        _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True, freeze=juist)
        assert len(provider.aanroepen) == 5

    def test_configuratie_na_freeze_gewijzigd_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        freeze = _freeze(tmp_path, _omgeving(provider), "t")
        with pytest.raises(gb.BudgetSchendingError, match="effectieve_config"):
            _t(_omgeving(provider, max_tokens_t=3000), tmp_path,
               _gevallenbestand(tmp_path, 5), fase="t_eind",
               nieuw_grootboek=True, freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    def test_promptdrift_na_freeze_geweigerd(self, tmp_path, monkeypatch):
        import services.validation.ess05_assessment_service as dienstmodule

        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = _freeze(tmp_path, omg, "t")
        origineel = dienstmodule._systeemprompt
        monkeypatch.setattr(
            dienstmodule, "_systeemprompt", lambda norm: origineel(norm) + " "
        )
        with pytest.raises(gb.BudgetSchendingError, match="system_prompt_sha256"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 5), fase="t_eind",
               nieuw_grootboek=True, freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    def test_g_freeze_past_niet_op_de_t_groep(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        with pytest.raises(gb.BudgetSchendingError, match="groep"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 5), fase="t_eind",
               nieuw_grootboek=True, freeze=_freeze(tmp_path, omg, "g"))  # fmt: skip
        assert provider.aanroepen == []


class TestGOntwikkeling:
    def test_vier_actuele_calls_op_de_bestaande_invoer(self, tmp_path):
        provider = _FakeProvider(
            tekst="Ontologische categorie: type\nPersoon met een lening."
        )
        omg = _omgeving(provider)
        uitkomst = _g(omg, tmp_path, G_INVOER, fase="g_ontwikkeling",
                      nieuw_grootboek=True)  # fmt: skip
        assert len(provider.aanroepen) == 4
        assert _stand(tmp_path)["per_fase"]["g_ontwikkeling"] == 4
        records = [
            _json(p) for p in (tmp_path / "uit").glob("g_ontwikkeling-*/calls/*.json")
        ]
        huidig = runner._sha_tekst(pi.huidige_g_instructie())
        assert sorted(r["sleutel"] for r in records) == [
            f"g_ontwikkeling|{i}|actueel|run1"
            for i in ("G1-rol-overlap", "G2-naam-met-trefwoord",
                      "G3-ontbrekend-kenmerk", "G4-meerdere-buren")
        ]  # fmt: skip
        for r in records:
            assert r["variant"] == "actueel"
            assert r["fase"] == "g_ontwikkeling"
            assert r["g_actueel_instructie_sha256"] == huidig
            assert r["prompt"]["tekst"].count(pi.huidige_g_instructie()) == 1
            assert "aandachtspunten" not in json.dumps(r["prompt"])
        assert uitkomst["g_actueel_instructie_sha256"] == huidig
        assert uitkomst["eindbinding"] is None
        _g(omg, tmp_path, G_INVOER, fase="g_ontwikkeling")
        assert len(provider.aanroepen) == 4  # hervatten: niets opnieuw

    def test_andere_invoer_geweigerd(self, tmp_path):
        data = _json(G_INVOER)
        data["invoeren"] = data["invoeren"][:1]
        pad = tmp_path / "ander.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="G-ontwikkelinvoer"):
            _g(_omgeving(provider), tmp_path, pad, fase="g_ontwikkeling",
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []


class TestGEind:
    def test_zonder_freeze_geen_call(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _g(_omgeving(provider), tmp_path, _g_invoer_actueel(tmp_path),
               nieuw_grootboek=True)  # fmt: skip
        assert provider.aanroepen == []

    def test_zestien_calls_met_freezebinding(self, tmp_path):
        provider = _FakeProvider(
            tekst="Ontologische categorie: type\nPersoon met een lening."
        )
        omg = _omgeving(provider)
        freeze = _freeze(tmp_path, omg, "g")
        uitkomst = _g(omg, tmp_path, _g_invoer_actueel(tmp_path),
                      nieuw_grootboek=True, freeze=freeze)  # fmt: skip
        assert len(provider.aanroepen) == 16
        binding = uitkomst["eindbinding"]
        assert binding["herhaal_ids"] == []
        assert binding["freeze_sha256"] == runner._sha_bestand(freeze)
        assert _stand(tmp_path)["per_fase"]["g"] == 16

    def test_andere_g_instructie_dan_de_freeze_geweigerd(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = _freeze(tmp_path, omg, "g", g_actueel_instructie_sha256="0" * 64)
        with pytest.raises(gb.BudgetSchendingError, match="g_actueel_instructie"):
            _g(omg, tmp_path, _g_invoer_actueel(tmp_path), nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []

    def test_bevroren_ronde1_invoer_past_niet_meer(self, tmp_path):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        with pytest.raises(pi.InvoerfoutError, match="actuele G-tekst"):
            _g(omg, tmp_path, G_INVOER, nieuw_grootboek=True,
               freeze=_freeze(tmp_path, omg, "g"))  # fmt: skip
        assert provider.aanroepen == []


class TestDroog:
    def test_droog_ontwikkeling_negen(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 9)
        code = runner.main(
            ["--proef", "R2", "--fase", "ontwikkeling", "--gevallen", str(pad),
             "--uitmap", str(tmp_path / "uit"), "--droog"]
        )  # fmt: skip
        assert code == 0
        (bestand,) = (tmp_path / "uit").glob("droog-ontwikkeling-*/droogrun.json")
        droog = _json(bestand)
        assert (droog["geplande_calls"], droog["fasecap"]) == (9, 9)
        assert droog["proef_id"] == "DEF-768-AI-20260924-R2"
        assert "freezevelden" not in droog

    def test_droog_g_ontwikkeling_vier_binnen_de_grens(self, tmp_path):
        code = runner.main(
            ["--proef", "R2", "--fase", "g_ontwikkeling", "--g-invoer",
             str(G_INVOER), "--uitmap", str(tmp_path / "uit"), "--droog"]
        )  # fmt: skip
        assert code == 0
        (bestand,) = (tmp_path / "uit").glob("droog-g_ontwikkeling-*/droogrun.json")
        droog = _json(bestand)
        assert (droog["geplande_calls"], droog["fasecap"]) == (4, 4)
        assert all(i["promptlengte"] <= pi.g_promptgrens() for i in droog["items"])
        assert not list((tmp_path / "uit").glob("*.jsonl"))

    def test_freezevelden_uit_droog_worden_door_de_echte_run_aanvaard(self, tmp_path):
        eind = _gevallenbestand(tmp_path, 5)
        droog = asyncio.run(
            runner.droogrun("t_eind", eind, tmp_path / "droog", proef=R2,
                            timeout=30, max_tokens_t=1500)
        )  # fmt: skip
        velden = droog["freezevelden"]
        assert velden["dataset_sha256"] == runner._sha_bestand(eind)
        assert velden["herhaal_ids"] == ["X-00", "X-01", "X-02", "X-03"]
        freeze = tmp_path / "freeze.json"
        freeze.write_text(json.dumps(velden), encoding="utf-8")
        provider = _FakeProvider()
        # Zoals --echt de omgeving bouwt (SDK-wacht aan), zonder netwerk.
        omg = runner.bouw_omgeving(
            provider,
            ModelRouter.from_config(),
            timeout=30,
            max_tokens_t=1500,
            sdk_bewaakt=True,
            geheimen=("GEHEIME-SLEUTEL-WAARDE",),
        )
        _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True, freeze=freeze)
        assert len(provider.aanroepen) == 5


class TestCodemanifest:
    def test_bronneninstructie_staat_in_het_manifest(self):
        manifest = runner.codemanifest()
        assert "src/services/prompts/modules/definition_task_module.py" in manifest

    def test_contextmodule_staat_in_het_manifest(self):
        """Ontwikkelcorrectie R2: de G-contextgrens valt onder de freeze."""
        manifest = runner.codemanifest()
        assert "src/services/prompts/modules/context_awareness_module.py" in manifest


class TestOntwikkelselectie:
    @staticmethod
    def _bron(tmp_path: Path) -> bytes:
        basis = _json(_gevallenbestand(tmp_path, 3))
        basis["schema"] = "def768-wp7-eindset/1"
        basis["gevallen"][1]["verwacht_per_buur"] = [
            {"term": "iets", "distinction": "unclear", "grond": "g"}
        ]
        return json.dumps(basis).encode("utf-8")

    def test_kopieert_exact_met_herkomst(self, tmp_path):
        bron = self._bron(tmp_path)
        sha = sel._sha(bron)
        selectie = sel.maak_selectie(
            bron, bron_pad="bron.json", ids=("X-02", "X-01"), bron_sha256=sha
        )
        sel.controleer_selectie(selectie, bron)
        origineel = {g["id"]: g for g in json.loads(bron)["gevallen"]}
        assert selectie["gevallen"] == [origineel["X-02"], origineel["X-01"]]
        assert selectie["herkomst"]["bron_sha256"] == sha
        assert "geen holdout" in selectie["status"]
        assert "herhaal_ids" not in selectie

    def test_gewijzigd_label_valt_op(self, tmp_path):
        bron = self._bron(tmp_path)
        selectie = sel.maak_selectie(
            bron, bron_pad="b", ids=("X-01",), bron_sha256=sel._sha(bron)
        )
        vervalst = copy.deepcopy(selectie)
        vervalst["gevallen"][0]["verwacht_per_buur"][0]["distinction"] = "distinguished"
        with pytest.raises(sel.SelectiefoutError, match="X-01"):
            sel.controleer_selectie(vervalst, bron)

    def test_andere_bron_geweigerd(self, tmp_path):
        with pytest.raises(sel.SelectiefoutError, match="bronhash"):
            sel.maak_selectie(self._bron(tmp_path), bron_pad="b")

    def test_selectie_uit_het_besluit(self):
        assert sel.SELECTIE == (
            "E06", "E09", "E10", "E13", "E14", "E15", "E16", "E05", "E20"
        )  # fmt: skip
        assert R2.identiteit.fasecaps["ontwikkeling"] == len(sel.SELECTIE)

    @pytest.mark.skipif(
        not (sel.BRON.is_file() and sel.DOEL.is_file()),
        reason="rapportbestanden (git-ignored) alleen lokaal aanwezig",
    )
    def test_echte_selectie_is_exact_en_bruikbaar(self):
        bron = sel.BRON.read_bytes()
        selectie = _json(sel.DOEL)
        sel.controleer_selectie(selectie, bron)
        assert [g["id"] for g in selectie["gevallen"]] == list(sel.SELECTIE)
        gevallen, herhaal = pi.valideer_gevallenbestand(selectie, herhaal_vereist=False)
        assert len(gevallen) == 9
        assert herhaal == [] or herhaal is None
