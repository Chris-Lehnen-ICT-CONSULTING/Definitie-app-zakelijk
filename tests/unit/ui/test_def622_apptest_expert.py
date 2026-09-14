"""DEF-622 ketenbewijs van de expertactie met de échte Streamlit `AppTest`.

De pytest-conftest vervangt `streamlit` procesbreed door een mock, dus
`AppTest` draait via de driver `tests/apptest/run_def622_expert_apptest.py`
als subprocess met de echte Streamlit, achter de offline-bootstrap, op een
synthetische database in `tmp_path`. De driver levert waarnemingen als JSON.

Bewezen keten op de echte `ExpertReviewTab._render_definition_review` en de
echte container (workflow-service, orchestrator):

* uitgangssituatie: CON-01 "Nog te beoordelen" met de gevonden naam, gate
  geblokkeerd; zonder gebruikersidentiteit is vastleggen uitgeschakeld (K5);
* reviewer naam (bestaand widget) + naamfunctie + reden → "Leg beoordeling
  vast" → beoordeling op het record met actor en versiebinding; CON-01
  "Voldoet"; gate "toegestaan";
* "Re-validate" → de orchestrator ziet de beoordeling als toegepast (K3);
* "Vaststellen" (overige gatevoorwaarden expliciet geïsoleerd: synthetische
  score, geen kritieke issues; DEF-630 blijft eigenaar van de algemene gate)
  → established, versie +1, beoordeling gebonden aan de nieuwe versie (V2c);
* de vijf CON-01-weergaven uit de gedeelde validatieweergave: Voldoet,
  Voldoet niet, Nog te beoordelen, Voldoet niet + Nog te beoordelen (B-08)
  en Technisch probleem (B-06) — allemaal zonder cijfer.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

REPO = Path(__file__).resolve().parents[3]
DRIVER = REPO / "tests" / "apptest" / "run_def622_expert_apptest.py"
REVIEWER = "Reviewer Rood"


@pytest.fixture(scope="module")
def waarnemingen(tmp_path_factory) -> dict:
    db = tmp_path_factory.mktemp("def622-expert-apptest") / "expert.db"
    proces = subprocess.run(
        [sys.executable, str(DRIVER), str(db)],
        cwd=str(REPO),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-6000:]
    gelezen = json.loads(proces.stdout.strip().splitlines()[-1])
    bewijsmap = REPO / "reports" / "def622" / "apptest"
    if bewijsmap.is_dir():
        (bewijsmap / "expert-waarnemingen.json").write_text(
            json.dumps(gelezen, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return gelezen


def _tekst(deel: dict, sleutel: str = "teksten") -> str:
    return "\n".join(deel[sleutel])


def test_kindproces_draait_achter_de_offline_gate(waarnemingen):
    assert waarnemingen["bootstrap"]["gate_actief"] is True
    assert waarnemingen["bootstrap"]["db_binnen_sessieroot"] is True


def test_uitgangssituatie_open_signaal_gate_geblokkeerd_en_geen_actor(waarnemingen):
    start = waarnemingen["start"]
    tekst = _tekst(start).lower()
    assert "nog te beoordelen" in tekst
    assert "stichting zilver" in tekst
    assert "gate: blokkade" in tekst
    assert "totaalscore" not in tekst or "niet beschikbaar" in tekst
    # Zonder identiteit: vastleggen uitgeschakeld met de reden in de hulptekst;
    # vaststellen geblokkeerd door de gate.
    assert start["vastleggen"]["disabled"] is True
    assert start["vaststellen"]["disabled"] is True
    assert start["rij"]["review"] is None
    assert start["rij"]["status"] == "review"
    assert start["rij"]["version_number"] == 1


def test_vastleggen_bindt_beoordeling_aan_record_en_opent_de_gate(waarnemingen):
    assert waarnemingen["ingevuld"]["vastleggen"]["disabled"] is False
    na = waarnemingen["na_vastleggen"]
    rij = na["rij"]
    review = rij["review"]
    assert review is not None
    assert review["actor"] == REVIEWER
    assert rij["updated_by"] == REVIEWER
    assert rij["version_number"] == 2
    assert review["version_number"] == 2
    beslissing = next(iter(review["decisions"].values()))
    assert beslissing["function"] == "necessary"
    assert "exclusieve uitgever" in beslissing["reason"].lower()
    # Het geselecteerde record is ververst naar de actuele versie.
    assert na["geselecteerde_versie"] == 2
    tekst = _tekst(na).lower()
    assert (
        "voldoet" in tekst and "nog te beoordelen" not in tekst.split("## toetsing")[0]
    )
    assert "gate: toegestaan" in tekst
    assert na["vaststellen"]["disabled"] is False


def test_revalidate_ziet_de_beoordeling(waarnemingen):
    na = waarnemingen["na_revalidate"]
    assert na["con01_status"] == "pass"
    assert na["review"]["applied"] is True
    assert na["review"]["actor"] == REVIEWER
    assert na["overall_score"] is None


def test_vaststellen_behoudt_de_binding(waarnemingen):
    rij = waarnemingen["na_vaststellen"]["rij"]
    assert rij["status"] == "established"
    assert rij["version_number"] == 3
    assert rij["review"]["version_number"] == 3
    assert rij["review"]["actor"] == REVIEWER
    assert rij["geschiedenis"].count("status_changed") == 1


def test_vijf_weergaven_zonder_cijfer(waarnemingen):
    weergaven = waarnemingen["weergaven"]
    assert weergaven["voldoet"]["con01_status"] == "pass"
    assert weergaven["open"]["con01_status"] == "review_required"
    assert weergaven["voldoet_niet"]["con01_status"] == "fail"
    assert weergaven["voldoet_niet_en_open"]["con01_status"] == "fail"
    assert weergaven["technisch"]["con01_status"] == "error"
    assert all(w["overall_score"] is None for w in weergaven.values())

    tekst = _tekst(waarnemingen, "weergave_teksten")
    for geval in (
        "voldoet",
        "open",
        "voldoet_niet",
        "voldoet_niet_en_open",
        "technisch",
    ):
        assert f"Geval: {geval}" in tekst
    laag = tekst.lower()
    assert "totaalscore:** niet beschikbaar" in laag
    for label in ("voldoet", "voldoet niet", "nog te beoordelen", "technisch probleem"):
        assert label in laag, label
    # B-08: falen en open blijven samen zichtbaar; B-06: geen interne fout
    # als normuitleg.
    assert "stichting goud" in laag
    assert "synthetische storing" not in laag
