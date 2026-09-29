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

E_SLEUTELS = [f"interpretatie|E|{n}" for n in (1, 2, 3)]


def _run18(tmp_path, maak_e=None):
    """Een volledige R18A-fase (12 runs); E desgewenst met `maak_e(vergelijking)`."""

    def antwoord(naam, _n, verg):
        ruw = maak_e(verg) if naam == "E" and maak_e else _juist(naam, verg)
        return json.dumps(ruw, ensure_ascii=False)

    provider = _R18Provider(_items(), antwoord=antwoord)
    _i18(_omgeving8(provider), tmp_path, _i_invoer(tmp_path))
    (calls,) = sorted((tmp_path / "uit").glob("interpretatie-*/calls"))
    return calls


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
        runs = eo.lees_runs([calls])
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
        assert bs.proefoordeel(eo.lees_runs([calls])) == (
            _samenvatting_i(tmp_path)["proefoordeel"]
        )

    def test_gewijzigde_e_uitvoer_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        (pad,) = sorted(calls.glob("*-interpretatie-E-2.json"))
        record = json.loads(pad.read_text(encoding="utf-8"))
        record["reserveringen"][0]["ruw_antwoord"] += " "
        pad.write_text(json.dumps(record), encoding="utf-8")
        with pytest.raises(bs.OordeelfoutError, match="ruw_antwoord_sha256"):
            eo.lees_runs([calls])

    def test_dubbele_run_geweigerd(self, tmp_path):
        calls = _run18(tmp_path)
        with pytest.raises(bs.OordeelfoutError, match="dubbel"):
            eo.lees_runs([calls, calls])

    def test_geen_callrecords_geweigerd(self, tmp_path):
        (tmp_path / "leeg").mkdir()
        with pytest.raises(bs.OordeelfoutError, match="geen callrecords"):
            eo.lees_runs([tmp_path / "leeg"])


class TestBeoordelingsblad:
    def test_volledige_e_uitvoer_per_run_zonder_hints(self, tmp_path):
        calls = _run18(tmp_path)
        blad = eo.beoordelingsblad([calls])
        runs = {r["sleutel"]: r for r in eo.lees_runs([calls])}
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
        blad = eo.beoordelingsblad([calls])
        sjabloon = json.loads(re.findall(r"```json\n(.*?)```", blad, re.S)[-1])
        assert sjabloon["schema"] == bs.E_OORDEELSCHEMA
        assert [o["run"] for o in sjabloon["oordelen"]] == E_SLEUTELS
        assert {o["status"] for o in sjabloon["oordelen"]} == {""}
        # Een niet ingevuld sjabloon is geen geldig oordeel.
        with pytest.raises(bs.OordeelfoutError, match="status"):
            bs.eindoordeel(eo.lees_runs([calls]), sjabloon)

    def test_cli_schrijft_nieuw_en_weigert_een_bestaand_doel(self, tmp_path):
        calls = _run18(tmp_path)
        doel = tmp_path / "blad.md"
        assert eo.main(["blad", "--calls", str(calls), "--doel", str(doel)]) == 0
        assert doel.read_text(encoding="utf-8") == eo.beoordelingsblad([calls])
        with pytest.raises(FileExistsError):
            eo.main(["blad", "--calls", str(calls), "--doel", str(doel)])


class TestEindoordeelCli:
    def _eind(self, tmp_path, calls, data):
        oordeel = _schrijf(tmp_path / "oordeel.json", data)
        doel = tmp_path / "eindoordeel.json"
        assert eo.main(["eindoordeel", "--calls", str(calls), "--oordeel", str(oordeel),
                        "--doel", str(doel)]) == 0  # fmt: skip
        return json.loads(doel.read_text(encoding="utf-8"))

    def test_drie_keer_behouden_is_geslaagd(self, tmp_path):
        calls = _run18(tmp_path)
        runs = eo.lees_runs([calls])
        uit = self._eind(tmp_path, calls, _oordeel(runs, ["behouden"] * 3))
        assert uit["oordeel"] == "geslaagd"
        assert (uit["m_d_juist"], uit["e_voorwaarde_behouden"]) == (12, [3, 3])

    def test_een_ontkend_is_niet_geslaagd(self, tmp_path):
        calls = _run18(tmp_path)
        runs = eo.lees_runs([calls])
        data = _oordeel(runs, ["behouden", "ontkend", "behouden"])
        assert self._eind(tmp_path, calls, data)["oordeel"] != "geslaagd"

    def test_afwijkende_hash_geweigerd_en_niets_geschreven(self, tmp_path):
        calls = _run18(tmp_path)
        data = _oordeel(eo.lees_runs([calls]), ["behouden"] * 3)
        data["oordelen"][0]["e_uitvoer_sha256"] = "f" * 64
        oordeel = _schrijf(tmp_path / "oordeel.json", data)
        doel = tmp_path / "eindoordeel.json"
        with pytest.raises(bs.OordeelfoutError, match="sha256 wijkt af"):
            eo.main(["eindoordeel", "--calls", str(calls), "--oordeel", str(oordeel),
                     "--doel", str(doel)])  # fmt: skip
        assert not doel.exists()

    def test_codex_combinatie_wacht_en_slaagt_alleen_door_chris(self, tmp_path):
        """Hercontrole v3: `["bij storing", "deze voorwaarde is optioneel"]`."""
        calls = _run18(
            tmp_path,
            lambda v: _e(v, ("bevestigd", ["Uitleen:"],
                             ["bij storing", "deze voorwaarde is optioneel"])),
        )  # fmt: skip
        runs = eo.lees_runs([calls])
        assert bs.proefoordeel(runs)["oordeel"] == "wacht_op_handmatige_beoordeling"
        uit = self._eind(tmp_path, calls, _oordeel(runs, ["ontkend"] * 3))
        assert uit["oordeel"] != "geslaagd"
        assert uit["e_voorwaarde_behouden"] == [0, 3]
