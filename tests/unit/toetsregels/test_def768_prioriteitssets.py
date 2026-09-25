"""DEF-768 (reviewbevinding 3): prioriteitssets volgen het regelrecord.

ESS-05 heeft sinds DEF-768 prioriteit `midden` (ASTRA) en blokkeert niet
zelfstandig. Volgens de bestaande conventie (ESS-04, SAM-01, STR-05…: midden +
verplicht) staat zo'n regel in `verplicht.json` maar niet in `hoog.json` of
`verplicht-hoog.json`; er is geen aparte midden-set. Dan geeft
`ToetsregelManager.get_kritieke_regels()` hem ook niet als kritisch terug.

De algemene toets gaat één kant op: een set die een regel als 'hoog' claimt,
moet een record met prioriteit `hoog` hebben. Bekende setleden zonder
gelijknamig recordbestand (bv. `ARAI06`) laat hij ongemoeid; dat is geen
DEF-768-scope.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from toetsregels.manager import ToetsregelManager

pytestmark = [pytest.mark.unit]

BASIS = Path(__file__).resolve().parents[3] / "src" / "toetsregels"
REGELS = BASIS / "regels"
SETS = BASIS / "sets" / "per-prioriteit"


def _set(naam: str) -> list[str]:
    return json.loads((SETS / f"{naam}.json").read_text(encoding="utf-8"))["regels"]


def _record(regel_id: str) -> dict | None:
    pad = REGELS / f"{regel_id}.json"
    return json.loads(pad.read_text(encoding="utf-8")) if pad.exists() else None


def test_ess05_record_en_sets_zijn_consistent():
    record = _record("ESS-05")
    assert (record["prioriteit"], record["aanbeveling"]) == ("midden", "verplicht")
    assert "ESS-05" not in _set("hoog")
    assert "ESS-05" not in _set("verplicht-hoog")
    assert "ESS-05" in _set("verplicht")


@pytest.mark.parametrize("setnaam", ["hoog", "verplicht-hoog"])
def test_hoge_sets_bevatten_alleen_regels_met_prioriteit_hoog(setnaam):
    afwijkend = [
        (regel_id, rec.get("prioriteit"))
        for regel_id in _set(setnaam)
        if (rec := _record(regel_id)) is not None and rec.get("prioriteit") != "hoog"
    ]
    assert afwijkend == []


def test_verplicht_hoog_bevat_alleen_verplichte_regels():
    verplicht = set(_set("verplicht"))
    assert [r for r in _set("verplicht-hoog") if r not in verplicht] == []


def test_manager_geeft_ess05_niet_als_kritiek_en_wel_als_verplicht():
    manager = ToetsregelManager()
    kritiek = manager.get_kritieke_regels()
    assert kritiek, "de kritieke set is niet leeg"
    assert all(regel.get("prioriteit") == "hoog" for regel in kritiek)
    assert not any(regel.get("prioriteit") == "midden" for regel in kritiek)
    verplicht_ids = {
        str(regel.get("id", "")).replace("_", "-")
        for regel in manager.get_verplichte_regels()
    }
    kritiek_ids = {str(regel.get("id", "")).replace("_", "-") for regel in kritiek}
    assert "ESS-05" in verplicht_ids
    assert "ESS-05" not in kritiek_ids
