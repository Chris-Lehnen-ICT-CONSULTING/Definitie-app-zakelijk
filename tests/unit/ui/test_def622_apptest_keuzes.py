"""DEF-622 ketenbewijs met de échte Streamlit `AppTest` (B-08/B-09).

De pytest-conftest vervangt `streamlit` procesbreed door een mock, dus
`AppTest` kan hier niet in-process draaien. De driver
`tests/apptest/run_def622_apptest.py` draait daarom als subprocess met de
echte Streamlit, installeert zelf de offline-bootstrap vóór elke
productimport (onder `run_profile` erft hij hem al via `sitecustomize` op
``PYTHONPATH`` — die omgeving wordt ongewijzigd doorgegeven), werkt op een
synthetische database in `tmp_path` en levert zijn waarnemingen als JSON.

Bewezen keten per keuze: klik → consument → zichtbaar resultaat.

* Gebruik Deze → gekozen record wordt getoond, melding verdwijnt.
* Bewerk → de echte `DefinitionEditTab` laadt het record in de editor.
* Genereer Nieuw zonder reden → niets geforceerd, waarschuwing, DB ongewijzigd.
* Genereer Nieuw met reden → echte handler/container (AI bevroren) slaat een
  nieuw concept op met de reden in de audit; het vastgestelde record blijft
  ongemoeid; de force-opties zijn opgebruikt.
* CON-01-uitleg (aanleiding/reden/vervolgstap) is zichtbaar zonder cijfer.
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
DRIVER = REPO / "tests" / "apptest" / "run_def622_apptest.py"
BESTAANDE_TEKST = "kwaliteitsmerk voor gecontroleerde producten"
REDEN = "Bestaande definitie dekt de nieuwe regeling niet."


@pytest.fixture(scope="module")
def waarnemingen(tmp_path_factory) -> dict:
    db = tmp_path_factory.mktemp("def622-apptest") / "keuzes.db"
    proces = subprocess.run(
        [sys.executable, str(DRIVER), str(db)],
        cwd=str(REPO),
        # Bewust de bestaande omgeving: onder run_profile draagt PYTHONPATH de
        # sitecustomize met de offline-gate; de driver installeert hem anders
        # zelf. Dummykeys/dotenv-uit komen van de gate, niet van hier.
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-6000:]
    gelezen = json.loads(proces.stdout.strip().splitlines()[-1])
    # Bewijsartefact (reports/ is gitignored): alleen wanneer de map bestaat.
    bewijsmap = REPO / "reports" / "def622" / "apptest"
    if bewijsmap.is_dir():
        (bewijsmap / "waarnemingen.json").write_text(
            json.dumps(gelezen, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return gelezen


def test_kindproces_draait_achter_de_offline_gate(waarnemingen):
    bootstrap = waarnemingen["bootstrap"]
    assert bootstrap["gate_actief"] is True
    assert bootstrap["db_binnen_sessieroot"] is True


def test_melding_toont_de_drie_keuzes(waarnemingen):
    labels = " | ".join(waarnemingen["knoppen"])
    assert "Gebruik Deze" in labels
    assert "Bewerk" in labels
    assert "Genereer Nieuw" in labels
    start = "\n".join(waarnemingen["start_teksten"])
    # De genormaliseerde lookup vond het bestaande record via afwijkende
    # schrijfwijze/volgorde van dezelfde context.
    assert "Vastgestelde definitie bestaat al" in start


def test_gebruik_deze_toont_het_gekozen_record(waarnemingen):
    na = waarnemingen["na_gebruik_deze"]
    assert na["selected_id"] == waarnemingen["bestaand_id"]
    assert na["check_result_weg"] is True
    tekst = "\n".join(na["teksten"])
    assert "Gekozen bestaande definitie" in tekst
    assert BESTAANDE_TEKST in tekst
    assert "Stichting Zilver" in tekst
    assert "established" in tekst


def test_bewerk_laadt_het_record_in_de_echte_editor(waarnemingen):
    na = waarnemingen["na_bewerk"]
    assert na["editing_definition_id"] == waarnemingen["bestaand_id"]
    assert na["active_tab"] == "edit"
    # De consument (DefinitionEditTab) heeft het record daadwerkelijk geladen
    # en toont de tekst in de editor.
    assert na["editing_definition_geladen_id"] == waarnemingen["bestaand_id"]
    assert any(BESTAANDE_TEKST in t for t in na["text_areas"]), na["text_areas"]
    assert "Definitie Editor" in "\n".join(na["teksten"])


def test_genereer_nieuw_zonder_reden_forceert_niets(waarnemingen):
    na = waarnemingen["nieuw_zonder_reden"]
    assert not na["options"].get("force_generate")
    assert not na["options"].get("force_duplicate")
    assert na["trigger"] is False
    assert any("reden" in w.lower() for w in na["waarschuwingen"])
    assert [r["id"] for r in na["rijen"]] == [waarnemingen["bestaand_id"]]


def test_genereer_nieuw_met_reden_slaat_concept_op_naast_bestaand_record(
    waarnemingen,
):
    na = waarnemingen["nieuw_met_reden"]
    assert not na["fouten"], na["fouten"]
    bestaand_id = waarnemingen["bestaand_id"]

    # Nieuw concept door productiecode opgeslagen, naast het bestaande record.
    assert len(na["nieuwe_ids"]) == 1, na["rijen"]
    nieuw = next(r for r in na["rijen"] if r["id"] == na["nieuwe_ids"][0])
    assert nieuw["status"] == "draft"
    assert nieuw["begrip"] == "keurmerk"
    assert nieuw["definitie"] != BESTAANDE_TEKST

    # Bestaand vastgesteld record ongemoeid.
    bestaand = next(r for r in na["rijen"] if r["id"] == bestaand_id)
    assert bestaand["status"] == "established"
    assert bestaand["definitie"] == BESTAANDE_TEKST
    assert bestaand["version_number"] == 1
    assert [g["wijziging_type"] for g in na["geschiedenis_bestaand"]] == ["created"]

    # De reden staat in de audit van het nieuwe concept.
    aangemaakt = [
        g for g in na["geschiedenis_nieuw"] if g["wijziging_type"] == "created"
    ]
    assert aangemaakt and REDEN in aangemaakt[0]["wijziging_reden"]
    assert f"bestaande definitie {bestaand_id}" in aangemaakt[0]["wijziging_reden"]

    # Force-opties zijn opgebruikt; het nieuwe concept staat klaar voor de editor.
    for sleutel in ("force_generate", "force_duplicate", "force_duplicate_reason"):
        assert sleutel not in na["options"], na["options"]
    assert na["trigger"] is False
    assert na["editing_definition_id"] == na["nieuwe_ids"][0]
    assert na["last_generation_result_aanwezig"] is True


MELDING = "De tekst is na generatie aangepast. Bekijk wijzigingen."


def test_tekstvergelijking_bij_gegenereerde_definitie(waarnemingen):
    """Besluit tekstvergelijking (Chris): in de echte generatietab verschijnt
    na een echte wijziging door de app de exacte melding met de uitklapbare
    vergelijking van de echte kern vóór nabewerking en de eindtekst; het
    bewijs is per record bewaard."""
    tw = waarnemingen["tekstwijziging_generatie"]
    assert MELDING in tw["waarschuwingen"]
    assert "Bekijk wijzigingen" in tw["expanders"]
    bewijs = tw["bewijs"]
    assert bewijs and bewijs["tekst_na_generatie_aangepast"] is True
    assert bewijs["definitie_eindtekst"] == tw["gegenereerde_tekst"]
    assert bewijs["definitie_kern_geextraheerd"] != bewijs["definitie_eindtekst"]
    letterlijk = "\n".join(tw["letterlijk"])
    assert bewijs["definitie_kern_geextraheerd"] in letterlijk
    assert bewijs["definitie_eindtekst"] in letterlijk
    assert "[-" in letterlijk and "{+" in letterlijk


def test_historisch_record_in_editor_zonder_tekstvergelijking(waarnemingen):
    """Het gezaaide record heeft geen generatiebewijs: de echte editor toont
    geen melding en geen vergelijking (geen verzonnen beginversie)."""
    na = waarnemingen["na_bewerk"]
    assert MELDING not in na["waarschuwingen"]
    assert "Bekijk wijzigingen" not in na["expanders"]


def test_con01_uitleg_is_zichtbaar(waarnemingen):
    start = "\n".join(waarnemingen["start_teksten"]).lower()
    assert "totaalscore:** niet beschikbaar" in start
    assert "nog te beoordelen" in start
    assert "stichting zilver" in start
    assert "laat de expert de functie van de naam beoordelen" in start
