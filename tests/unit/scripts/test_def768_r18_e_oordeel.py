"""DEF-768 R18A — het voorwaardeoordeel van Chris bij casus E (aanvulling v4).

Besluit optie 2: E wordt nooit automatisch als voorwaarde-behouden gescoord.
Deze tests draaien een R18A-fase met een nep-provider (geen netwerk, geen
modeluitvoer) en toetsen daarop het beoordelingsblad, het oordeelbestand en
het eindoordeel (`r18_e_oordeel`, `bewijsscorer.eindoordeel`).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys

import pytest

from tests.unit.scripts.test_def768_bewijsscorer import _e
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r18_proef import (
    _i18,
    _i_invoer,
    _items,
    _juist,
    _R18Provider,
    _records,
    _samenvatting_i,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import bewijsscorer as bs
import r18_e_oordeel as eo
import run_ess05_proef as runner

E_SLEUTELS = [f"interpretatie|E|{n}" for n in (1, 2, 3)]


@pytest.fixture(autouse=True)
def _gepind(tmp_path, monkeypatch):
    """De testinvoer (`_i_invoer`) als gepinde proefinvoer, zoals de runner hem kreeg."""
    pad = _i_invoer(tmp_path)
    monkeypatch.setattr(runner, "R18_I_INVOER_SHA256", _sha(pad))
    return pad


def _sha(pad) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


def _run18(tmp_path, maak_e=None):
    """Een volledige R18A-fase (12 runs); E desgewenst met `maak_e(vergelijking)`."""

    def antwoord(naam, _n, verg):
        ruw = maak_e(verg) if naam == "E" and maak_e else _juist(naam, verg)
        return json.dumps(ruw, ensure_ascii=False)

    provider = _R18Provider(_items(), antwoord=antwoord)
    _i18(_omgeving8(provider), tmp_path, tmp_path / "i-invoer.json")
    (calls,) = sorted((tmp_path / "uit").glob("interpretatie-*/calls"))
    return calls


def _lees(tmp_path, *callmappen):
    return eo.lees_runs(list(callmappen), tmp_path / "i-invoer.json")


def _record(calls, naam, h):
    (pad,) = sorted(calls.glob(f"*-interpretatie-{naam}-{h}.json"))
    return pad, json.loads(pad.read_text(encoding="utf-8"))


def _herschrijf(pad, record):
    pad.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def _oordeel(runs, statussen):
    e_runs = [r for r in runs if r["e_uitvoer_sha256"]]
    return {
        "schema": bs.E_OORDEELSCHEMA,
        "oordelen": [
            {"run": r["sleutel"], "e_uitvoer_sha256": r["e_uitvoer_sha256"],
             "status": s, "beoordelaar": "Chris Lehnen", "datum": "2026-09-30"}
            for r, s in zip(e_runs, statussen, strict=True)
        ],
    }  # fmt: skip


def _schrijf(pad, data):
    pad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return pad


class TestRuns:
    def test_twaalf_runs_met_de_hash_van_de_e_uitvoer(self, tmp_path):
        calls = _run18(tmp_path)
        runs = _lees(tmp_path, calls)
        assert [r["sleutel"] for r in runs] == [
            f"interpretatie|{n}|{h}" for n in "ACDE" for h in (1, 2, 3)
        ]
        per_sleutel = {r["sleutel"]: r for r in _records(tmp_path)}
        for r in runs:
            ruw = per_sleutel[r["sleutel"]]["reserveringen"][0]["ruw_antwoord"]
            if r["sleutel"] in E_SLEUTELS:
                assert (
                    r["e_uitvoer_sha256"]
                    == hashlib.sha256(ruw.encode("utf-8")).hexdigest()
                )
                assert r["categorie"] == "handmatig_beoordelen"
            else:
                assert r["e_uitvoer_sha256"] is None

    def test_zelfde_proefoordeel_als_de_runner(self, tmp_path):
        calls = _run18(tmp_path)
        assert bs.proefoordeel(_lees(tmp_path, calls)) == (
            _samenvatting_i(tmp_path)["proefoordeel"]
        )

    def test_gewijzigde_e_uitvoer_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "E", 2)
        record["reserveringen"][0]["ruw_antwoord"] += " "
        _herschrijf(pad, record)
        with pytest.raises(bs.OordeelfoutError, match="ruw_antwoord_sha256"):
            _lees(tmp_path, calls)

    def test_dubbele_run_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        with pytest.raises(bs.OordeelfoutError, match="dubbel"):
            _lees(tmp_path, calls, calls)

    def test_geen_callrecords_geweigerd(self, tmp_path):
        (tmp_path / "leeg").mkdir()
        with pytest.raises(bs.OordeelfoutError, match="geen callrecords"):
            _lees(tmp_path, tmp_path / "leeg")


class TestBestandsrouteWeigert:
    """Codex-hercontrole v4, B5/B6 (aanvulling v5): de bestandsroute herleidt E uit
    de gepinde invoer, herberekent elke score uit de gehashte ruwe uitvoer en
    weigert elk record dat niet bij de proefinvoer past; er wordt niets geschreven."""

    def _weigert(self, tmp_path, calls, melding):
        with pytest.raises(bs.OordeelfoutError, match=melding):
            _lees(tmp_path, calls)
        with pytest.raises(bs.OordeelfoutError, match=melding):
            eo.beoordelingsblad([calls], tmp_path / "i-invoer.json")
        oordeel = _schrijf(tmp_path / "oordeel-leeg.json",
                           {"schema": bs.E_OORDEELSCHEMA, "oordelen": []})  # fmt: skip
        doel = tmp_path / "eind-weigering.json"
        with pytest.raises(bs.OordeelfoutError, match=melding):
            eo.main(["eindoordeel", "--calls", str(calls), "--invoer",
                     str(tmp_path / "i-invoer.json"), "--oordeel", str(oordeel),
                     "--doel", str(doel)])  # fmt: skip
        assert not doel.exists()

    def test_codex_gewijzigde_e_metadata_bij_ongewijzigde_ruwe_tekst(self, tmp_path):
        """B6: E-scoremetadata als niet-E en geslaagd, ruwe tekst en hashes gelijk."""
        calls = _run18(tmp_path)
        for h in (1, 2, 3):
            pad, record = _record(calls, "E", h)
            record["runoordeel"].update(
                voorwaarde_behouden=None, voorwaarde_status=None,
                categorie="geslaagd", m_d_telt=True, handmatig=[],
            )  # fmt: skip
            record["score"].update(voorwaarde_behouden=None, voorwaarde_status=None)
            _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "strijdig")

    @pytest.mark.parametrize(
        "gekregen", ["pass", "fail", "error/ongeldig_schema", None]
    )
    def test_codex_b7_andere_uitkomst_via_bestanden_geweigerd(self, tmp_path, gekregen):
        """B7 via bestanden: `gekregen` van elke E-run gewijzigd, ruwe tekst gelijk."""
        calls = _run18(tmp_path)
        for h in (1, 2, 3):
            pad, record = _record(calls, "E", h)
            record["runoordeel"]["gekregen"] = gekregen
            _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "strijdig")

    @pytest.mark.parametrize("veld", ["score", "runoordeel"])
    def test_gewijzigde_niet_e_metadata_geweigerd(self, tmp_path, veld):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "D", 1)
        if veld == "score":
            record["score"]["m_b_dragend_ok"] = not record["score"]["m_b_dragend_ok"]
        else:
            record["runoordeel"]["categorie"] = "niet_geslaagd"
        _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "strijdig")

    def test_gewijzigde_geparste_interpretatie_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "A", 2)
        record["interpretatie"]["ruw"]["kern"] = []
        _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "strijdig")

    def test_ontbrekende_run_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, _ = _record(calls, "C", 3)
        pad.rename(tmp_path / "apart.json")
        self._weigert(tmp_path, calls, "ontbrekende runs")

    def test_onbekende_run_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        _, record = _record(calls, "E", 3)
        record.update(sleutel="interpretatie|E|4", herhaling=4, seq=999)
        record["reserveringen"][0]["seq"] = 999
        _herschrijf(calls / "999-interpretatie-E-4.json", record)
        self._weigert(tmp_path, calls, "herhaling")

    def test_codex_e1_als_e2_en_e3_gekopieerd_geweigerd(self, tmp_path):
        """B5 via bestanden: de E1-uitvoer op de plaats van E2 en E3."""
        calls = _run18(tmp_path)
        _, e1 = _record(calls, "E", 1)
        for h in (2, 3):
            pad, _ = _record(calls, "E", h)
            _herschrijf(pad, e1)
        self._weigert(tmp_path, calls, "dubbel")

    def test_e1_herlabeld_als_e2_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        _, e1 = _record(calls, "E", 1)
        pad, _ = _record(calls, "E", 2)
        _herschrijf(pad, {**e1, "sleutel": "interpretatie|E|2", "herhaling": 2})
        self._weigert(tmp_path, calls, "seq")

    def test_verkeerde_invoerhash_in_record_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "A", 1)
        record["invoerbestand_sha256"] = "0" * 64
        _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "invoerbestand_sha256")

    def test_niet_gepinde_invoer_geweigerd(self, tmp_path, monkeypatch):
        calls = _run18(tmp_path)
        monkeypatch.setattr(runner, "R18_I_INVOER_SHA256", "0" * 64)
        self._weigert(tmp_path, calls, "gepind")

    def test_verwisselde_item_id_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "E", 2)
        record["item_id"] = "D"
        _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "sleutel")

    def test_verwisselde_runs_d_en_e_geweigerd(self, tmp_path):
        """Sleutel, item en herhaling consequent verwisseld: de inhoud past niet."""
        calls = _run18(tmp_path)
        pad_d, d2 = _record(calls, "D", 2)
        pad_e, e2 = _record(calls, "E", 2)
        velden = ("sleutel", "item_id")
        _herschrijf(pad_d, {**d2, **{k: e2[k] for k in velden}})
        _herschrijf(pad_e, {**e2, **{k: d2[k] for k in velden}})
        self._weigert(tmp_path, calls, "geval_sha256")

    def test_andere_fase_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        pad, record = _record(calls, "A", 3)
        record["fase"] = "lokaal"
        _herschrijf(pad, record)
        self._weigert(tmp_path, calls, "interpretatie-callrecord")

    def test_invoer_met_andere_e_casus_geweigerd(self, tmp_path, monkeypatch):
        """E volgt uit de gepinde invoer: een invoer waarin D de voorwaarde draagt
        past niet op de proefstructuur."""
        calls = _run18(tmp_path)
        pad = tmp_path / "i-invoer.json"
        data = json.loads(pad.read_text(encoding="utf-8"))
        (d,) = [i for i in data["items"] if i["id"] == "D"]
        d["orakel"]["voorwaarde"] = "storing"
        pad.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(runner, "R18_I_INVOER_SHA256", _sha(pad))
        self._weigert(tmp_path, calls, "proefstructuur")


class TestBeoordelingsblad:
    def test_volledige_e_uitvoer_per_run_zonder_hints(self, tmp_path):
        calls = _run18(tmp_path)
        blad = eo.beoordelingsblad([calls], tmp_path / "i-invoer.json")
        runs = {r["sleutel"]: r for r in _lees(tmp_path, calls)}
        for sleutel in E_SLEUTELS:
            assert f"## {sleutel}" in blad
            assert runs[sleutel]["e_uitvoer_sha256"] in blad
        for sleutel in ("interpretatie|A|1", "interpretatie|D|3"):
            assert f"## {sleutel}" not in blad
        # Voorwaarden, kenmerken, bewijseenheden met hun tekst en de uitkomst.
        assert "| K2 | doel | bevestigd | bij storing |" in blad
        assert "Uitleen: bij storing stelt de servicedesk" in blad
        assert "error/buiten_bereik" in blad
        assert '"kern"' in blad and '"antwoorden"' in blad
        # Geen lexicale hint of voorlopige status bovenaan of elders.
        for woord in ("hint", "markering", "vermoedelijk", "automatisch behouden"):
            assert woord not in blad.casefold(), woord

    def test_sjabloon_voor_het_oordeelbestand(self, tmp_path):
        calls = _run18(tmp_path)
        blad = eo.beoordelingsblad([calls], tmp_path / "i-invoer.json")
        sjabloon = json.loads(re.findall(r"```json\n(.*?)```", blad, re.S)[-1])
        assert sjabloon["schema"] == bs.E_OORDEELSCHEMA
        assert [o["run"] for o in sjabloon["oordelen"]] == E_SLEUTELS
        assert {o["status"] for o in sjabloon["oordelen"]} == {""}
        # Een niet ingevuld sjabloon is geen geldig oordeel.
        with pytest.raises(bs.OordeelfoutError, match="status"):
            bs.eindoordeel(_lees(tmp_path, calls), sjabloon)

    def test_cli_schrijft_nieuw_en_weigert_een_bestaand_doel(self, tmp_path):
        calls = _run18(tmp_path)
        doel = tmp_path / "blad.md"
        args = ["blad", "--calls", str(calls), *_inv(tmp_path), "--doel", str(doel)]
        assert eo.main(args) == 0
        assert doel.read_text(encoding="utf-8") == eo.beoordelingsblad(
            [calls], tmp_path / "i-invoer.json"
        )
        with pytest.raises(FileExistsError):
            eo.main(args)


def _inv(tmp_path) -> list[str]:
    return ["--invoer", str(tmp_path / "i-invoer.json")]


class TestEindoordeelCli:
    def _eind(self, tmp_path, calls, data):
        oordeel = _schrijf(tmp_path / "oordeel.json", data)
        doel = tmp_path / "eindoordeel.json"
        assert eo.main(["eindoordeel", "--calls", str(calls), *_inv(tmp_path),
                        "--oordeel", str(oordeel), "--doel", str(doel)]) == 0  # fmt: skip
        return json.loads(doel.read_text(encoding="utf-8"))

    def test_drie_keer_behouden_is_geslaagd(self, tmp_path):
        calls = _run18(tmp_path)
        runs = _lees(tmp_path, calls)
        uit = self._eind(tmp_path, calls, _oordeel(runs, ["behouden"] * 3))
        assert uit["oordeel"] == "geslaagd"
        assert (uit["m_d_juist"], uit["e_voorwaarde_behouden"]) == (12, [3, 3])
        assert uit["invoerbestand_sha256"] == runner.R18_I_INVOER_SHA256

    def test_een_ontkend_is_niet_geslaagd(self, tmp_path):
        calls = _run18(tmp_path)
        runs = _lees(tmp_path, calls)
        data = _oordeel(runs, ["behouden", "ontkend", "behouden"])
        assert self._eind(tmp_path, calls, data)["oordeel"] != "geslaagd"

    def test_afwijkende_hash_geweigerd_en_niets_geschreven(self, tmp_path):
        calls = _run18(tmp_path)
        data = _oordeel(_lees(tmp_path, calls), ["behouden"] * 3)
        data["oordelen"][0]["e_uitvoer_sha256"] = "f" * 64
        oordeel = _schrijf(tmp_path / "oordeel.json", data)
        doel = tmp_path / "eindoordeel.json"
        with pytest.raises(bs.OordeelfoutError, match="sha256 wijkt af"):
            eo.main(["eindoordeel", "--calls", str(calls), *_inv(tmp_path),
                     "--oordeel", str(oordeel), "--doel", str(doel)])  # fmt: skip
        assert not doel.exists()

    def test_standaardinvoer_is_v5(self):
        assert eo.INVOER == ROOT / "reports" / "DEF-768-AI-20260928-R18" / (
            "bewijsregel-invoer-v5.json"
        )

    def test_codex_combinatie_wacht_en_slaagt_alleen_door_chris(self, tmp_path):
        """Hercontrole v3: `["bij storing", "deze voorwaarde is optioneel"]`."""
        calls = _run18(
            tmp_path,
            lambda v: _e(v, ("bevestigd", ["Uitleen:"],
                             ["bij storing", "deze voorwaarde is optioneel"])),
        )  # fmt: skip
        runs = _lees(tmp_path, calls)
        assert bs.proefoordeel(runs)["oordeel"] == "wacht_op_handmatige_beoordeling"
        uit = self._eind(tmp_path, calls, _oordeel(runs, ["ontkend"] * 3))
        assert uit["oordeel"] != "geslaagd"
        assert uit["e_voorwaarde_behouden"] == [0, 3]
