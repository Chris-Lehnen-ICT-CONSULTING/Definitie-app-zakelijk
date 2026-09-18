"""DEF-808 — bronmetadata-formulieren met échte Streamlit-widgets (AppTest, subprocess).

Zelfde opzet als ``test_def743_editor_apptest.py``: de pytest-conftest vervangt
``streamlit`` procesbreed door een mock, dus dit bestand start zichzelf als
subprocess-driver achter ``tests.offline_bootstrap`` en leest de waarnemingen
terug. Tijdelijke SQLite-database en tijdelijke documentopslag; geen model.

Bewezen met echte reruns (browserbevinding 18 september 2026 op c18a7ec3):

* editor-aanvulformulier zonder ingelogde gebruiker: de reviewer naam wordt
  ingevuld (rerun), daarna wordt de hyperlink ingevuld (rerun) — de naam
  blijft staan, het widget blijft bestaan en de knop blijft beschikbaar.
  Streamlit ruimt de sessiewaarde van een widget op zodra dat widget in een
  run niet meer wordt gerenderd; een naamveld dat verdwijnt zodra zijn eigen
  waarde is gevonden, verliest die waarde dus bij de eerstvolgende rerun;
* met een bestaande gebruikersidentiteit (`user`) wordt géén naamveld getoond
  en blijft die identiteit de handelende gebruiker;
* het uploadformulier (per geselecteerd document) houdt zijn velden over
  reruns en legt de opgave vast bij de documentprocessor.
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
ACTOR = "Reviewer Rood"
NAAMVELD = "edit_bronmeta_reviewer_name_input"


# ------------------------------------------------------------------ driver
#
# `AppTest.from_function` voert de functie als los script uit; procesbrede
# staat leeft op de fixturemodule (één object in `sys.modules`).


def _opzet() -> dict:
    import tempfile
    from copy import deepcopy
    from unittest.mock import patch

    from document_processing.document_processor import DocumentProcessor
    from services.definition_edit_repository import DefinitionEditRepository
    from services.interfaces import Definition
    from tests.fixtures import def808_p01
    from tests.fixtures.def808_p01 import (
        BEGRIP,
        DOCUMENTBRONNEN,
        JUR,
        P01_TEKST,
        PASSAGE_1,
        WET,
        bouw_documentbeoordeling,
    )

    map_ = Path(tempfile.mkdtemp())
    repo = DefinitionEditRepository(str(map_ / "apptest.db"))

    def _record(begrip: str) -> int:
        return repo.save(
            Definition(
                begrip=begrip,
                definitie=P01_TEKST,
                categorie="resultaat",
                organisatorische_context=[],
                juridische_context=list(JUR),
                wettelijke_basis=list(WET),
                metadata={
                    "status": "draft",
                    "sources": deepcopy(DOCUMENTBRONNEN),
                    "provenance_sources": deepcopy(DOCUMENTBRONNEN),
                    "source_assessment": bouw_documentbeoordeling(
                        P01_TEKST, DOCUMENTBRONNEN, begrip=begrip
                    ),
                },
            )
        )

    did = _record(BEGRIP)  # zonder ingelogde gebruiker: naamveld
    did_user = _record(BEGRIP + " (ingelogd)")  # met `user`: geen naamveld

    opslag = map_ / "docs"
    processor = DocumentProcessor(storage_dir=str(opslag))
    with patch(
        "document_processing.document_processor.extract_text_from_file",
        return_value=PASSAGE_1,
    ):
        doc = processor.process_uploaded_file(
            PASSAGE_1.encode("utf-8"), "awb-1-3-20260815.txt", "text/plain"
        )
    staat = {
        "pad": repo.db_path,
        "did": did,
        "did_user": did_user,
        "opslag": str(opslag),
        "doc_id": doc.id,
        "actor": ACTOR,
    }
    def808_p01.APPTEST_STATE = staat  # type: ignore[attr-defined]
    return staat


def _app() -> None:
    import streamlit as st

    from document_processing.document_processor import DocumentProcessor
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import DefinitionEditService
    from services.definition_repository import DefinitionRepository
    from tests.fixtures import def808_p01
    from ui.components.definition_edit_tab import DefinitionEditTab
    from ui.renderers.document_upload_renderer import DocumentUploadRenderer
    from ui.session_state import SessionStateManager

    staat = def808_p01.APPTEST_STATE  # type: ignore[attr-defined]
    repo = DefinitionEditRepository(staat["pad"])
    # De driver kiest het record; met `apptest_user` is er een ingelogde gebruiker.
    did = SessionStateManager.get_value("apptest_did") or staat["did"]
    gebruiker = SessionStateManager.get_value("apptest_user")
    if gebruiker:
        SessionStateManager.set_value("user", gebruiker)
    # Elke run vers uit de DB (ID-only), zoals de editor het record laadt.
    geladen = DefinitionRepository(staat["pad"]).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)

    st.markdown("## Editor — bronmetadata aanvullen")
    tab._render_bronmetadata_section(geladen)

    st.markdown("## Upload — bronmetadata per document")
    processor = DocumentProcessor(storage_dir=staat["opslag"])
    doc = processor.get_document_by_id(staat["doc_id"])
    DocumentUploadRenderer._render_bronmetadata_invoer(processor, doc)


def _tekstinvoer(at, sleutel: str):
    """Het text_input met deze key, of None als het (niet meer) bestaat."""
    for ti in at.text_input:
        if ti.key == sleutel:
            return ti
    return None


def _knop(at, sleutel: str):
    for knop in at.button:
        if knop.key == sleutel:
            return knop
    return None


def _sessietekst(at, sleutel: str):
    """`SafeSessionState` van AppTest kent geen `.get`; lees fail-safe."""
    if sleutel in at.session_state:
        return at.session_state[sleutel]
    return None


def _alle_tekst(at) -> str:
    return "\n".join(
        str(getattr(el, "value", el))
        for verzameling in (
            at.markdown,
            at.caption,
            at.success,
            at.info,
            at.warning,
            at.error,
            at.text,
        )
        for el in verzameling
    )


def _stap(at, did: int) -> dict:
    naam = _tekstinvoer(at, NAAMVELD)
    knop = _knop(at, f"edit_{did}_bronmeta_vastleggen")
    return {
        "exceptions": [str(e.value) for e in at.exception],
        "naamveld_aanwezig": naam is not None,
        "naam_widget": naam.value if naam is not None else None,
        "naam_sessie": _sessietekst(at, NAAMVELD),
        "url_widget": getattr(
            _tekstinvoer(at, f"edit_{did}_bronmeta_url"), "value", None
        ),
        "versie_widget": getattr(
            _tekstinvoer(at, f"edit_{did}_bronmeta_versie"), "value", None
        ),
        "vindplaats_widget": getattr(
            _tekstinvoer(at, f"edit_{did}_bronmeta_vindplaats"), "value", None
        ),
        "knop_aanwezig": knop is not None,
        "knop_disabled": bool(knop.disabled) if knop is not None else None,
        "knop_help": knop.help if knop is not None else None,
    }


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    offline_bootstrap.install()
    from streamlit.testing.v1 import AppTest

    from database.definitie_repository import DefinitieRepository
    from document_processing.document_processor import DocumentProcessor
    from tests.fixtures.def808_p01 import P01_URL, P01_VERSIE, P01_VINDPLAATS

    w: dict = {"gate_actief": offline_bootstrap.gate_is_actief(), "stappen": {}}
    staat = _opzet()
    did = staat["did"]
    facade = DefinitieRepository(staat["pad"])
    k = f"edit_{did}_bronmeta"

    at = AppTest.from_function(_app, default_timeout=180)
    at.run()
    w["stappen"]["render"] = {**_stap(at, did), "tekst": _alle_tekst(at)}

    # Reviewer naam invullen + Tab (rerun).
    at.text_input(key=NAAMVELD).input(ACTOR).run()
    w["stappen"]["na_naam"] = _stap(at, did)

    # Volgende veld (hyperlink) invullen + Tab (rerun): de naam moet blijven.
    at.text_input(key=f"{k}_url").input(P01_URL).run()
    w["stappen"]["na_url"] = _stap(at, did)

    # Overige velden; opnieuw reruns.
    if _tekstinvoer(at, f"{k}_versie") is not None:
        at.text_input(key=f"{k}_versie").input(P01_VERSIE).run()
        at.text_input(key=f"{k}_vindplaats").input(P01_VINDPLAATS).run()
    w["stappen"]["na_alles"] = _stap(at, did)

    # Vastleggen via de echte knop (alleen als hij beschikbaar is).
    knop = _knop(at, f"{k}_vastleggen")
    if knop is not None and not knop.disabled:
        knop.click().run()
    rec = facade.get_definitie(did)
    bewijs = rec.get_source_evidence() or {}
    documenten = [
        b for b in bewijs.get("sources") or [] if b.get("provider") == "documents"
    ]
    w["stappen"]["vastgelegd"] = {
        **_stap(at, did),
        "resultaat": (
            dict(_sessietekst(at, f"{k}_resultaat") or {})
            if isinstance(_sessietekst(at, f"{k}_resultaat"), dict)
            else None
        ),
        "versie_db": rec.version_number,
        "urls": [b.get("url") for b in documenten],
        "versies": [b.get("source_version") for b in documenten],
        "vindplaatsen": [b.get("locator") for b in documenten],
        "declared_by": [
            (b.get("declared_metadata") or {}).get("declared_by") for b in documenten
        ],
        "historie": len(rec.get_source_evidence_history()),
        "tekst": _alle_tekst(at),
    }

    # Met ingelogde gebruiker: geen naamveld; `user` blijft de handelende gebruiker.
    did_user = staat["did_user"]
    at.session_state["apptest_did"] = did_user
    at.session_state["apptest_user"] = "Ingelogde Gebruiker"
    at.run()
    ku = f"edit_{did_user}_bronmeta"
    at.text_input(key=f"{ku}_url").input(P01_URL).run()
    w["stappen"]["ingelogd"] = _stap(at, did_user)
    at.button(key=f"{ku}_vastleggen").click().run()
    rec_u = facade.get_definitie(did_user)
    w["stappen"]["ingelogd_vastgelegd"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "declared_by": sorted(
            {
                (b.get("declared_metadata") or {}).get("declared_by")
                for b in (rec_u.get_source_evidence() or {}).get("sources") or []
                if b.get("provider") == "documents"
            }
        ),
        "updated_by": rec_u.updated_by,
    }

    # Uploadroute: velden over reruns, dan vastleggen.
    doc_id = staat["doc_id"]
    kd = f"docmeta_{doc_id}"
    at.text_input(key=f"{kd}_url").input(P01_URL).run()
    at.text_input(key=f"{kd}_versie").input(P01_VERSIE).run()
    at.text_input(key=f"{kd}_vindplaats").input(P01_VINDPLAATS).run()
    w["stappen"]["upload_na_velden"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "url_widget": getattr(_tekstinvoer(at, f"{kd}_url"), "value", None),
        "versie_widget": getattr(_tekstinvoer(at, f"{kd}_versie"), "value", None),
        "vindplaats_widget": getattr(
            _tekstinvoer(at, f"{kd}_vindplaats"), "value", None
        ),
        "knop_aanwezig": _knop(at, f"{kd}_vastleggen") is not None,
    }
    at.button(key=f"{kd}_vastleggen").click().run()
    herladen = DocumentProcessor(storage_dir=staat["opslag"]).get_document_by_id(doc_id)
    w["stappen"]["upload_vastgelegd"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "opgave_op_schijf": herladen.source_metadata if herladen else None,
        "success": [str(x.value) for x in at.success],
        "errors": [str(x.value) for x in at.error],
        "url_widget": getattr(_tekstinvoer(at, f"{kd}_url"), "value", None),
    }
    Path(uit_pad).write_text(
        json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def808-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-8000:]
    return json.loads(uit.read_text(encoding="utf-8"))


def test_driver_draait_achter_de_gate_zonder_ui_excepties(w):
    assert w["gate_actief"] is True
    for naam, stap in w["stappen"].items():
        assert stap.get("exceptions", []) == [], (naam, stap.get("exceptions"))


def test_reviewer_naam_blijft_staan_over_reruns_en_andere_velden(w):
    """Browserbevinding: naam invullen + Tab, daarna hyperlink invullen + Tab —
    de naam mag niet verdwijnen en de knop niet weer uitvallen."""
    render = w["stappen"]["render"]
    assert render["naamveld_aanwezig"] is True and render["naam_widget"] == ""
    assert render["knop_aanwezig"] is True and render["knop_disabled"] is True
    assert "reviewer" in (render["knop_help"] or "").lower()
    assert "geen authenticiteitsbewijs" in render["tekst"].lower()

    na_naam = w["stappen"]["na_naam"]
    assert na_naam["naamveld_aanwezig"] is True
    assert na_naam["naam_widget"] == ACTOR and na_naam["naam_sessie"] == ACTOR
    assert na_naam["knop_disabled"] is True  # nog geen invoer: knop terecht uit

    na_url = w["stappen"]["na_url"]
    assert na_url["naamveld_aanwezig"] is True, na_url
    assert na_url["naam_widget"] == ACTOR and na_url["naam_sessie"] == ACTOR, na_url
    assert na_url["url_widget"]  # de zojuist ingevulde hyperlink staat er nog
    assert na_url["knop_disabled"] is False, na_url

    na_alles = w["stappen"]["na_alles"]
    assert na_alles["naam_widget"] == ACTOR
    assert na_alles["versie_widget"] == "2026-08-15"
    assert na_alles["vindplaats_widget"] == "artikel 1:3 lid 1 Awb"
    assert na_alles["knop_disabled"] is False


def test_vastleggen_via_echte_knop_schrijft_met_de_ingevulde_reviewer(w):
    vast = w["stappen"]["vastgelegd"]
    assert vast["resultaat"] is not None, vast
    assert vast["resultaat"].get("status") == "applied", vast["resultaat"]
    assert vast["versie_db"] == 2
    assert len(vast["urls"]) == 2 and all(u for u in vast["urls"])
    assert vast["versies"] == ["2026-08-15", "2026-08-15"]
    assert vast["vindplaatsen"] == ["artikel 1:3 lid 1 Awb"] * 2
    assert vast["declared_by"] == [ACTOR, ACTOR]
    assert vast["historie"] == 1
    assert "geen authenticiteitsbewijs" in vast["tekst"].lower()
    # Na het vastleggen blijft de identiteit van de reviewer beschikbaar.
    assert vast["naam_widget"] == ACTOR


def test_bestaande_gebruikersidentiteit_wordt_niet_vervangen_door_een_naamveld(w):
    ingelogd = w["stappen"]["ingelogd"]
    assert ingelogd["naamveld_aanwezig"] is False
    assert ingelogd["knop_disabled"] is False
    vast = w["stappen"]["ingelogd_vastgelegd"]
    assert vast["declared_by"] == ["Ingelogde Gebruiker"]
    assert vast["updated_by"] == "Ingelogde Gebruiker"


def test_uploadformulier_houdt_velden_over_reruns_en_legt_vast(w):
    velden = w["stappen"]["upload_na_velden"]
    assert velden["url_widget"] and velden["versie_widget"] == "2026-08-15"
    assert velden["vindplaats_widget"] == "artikel 1:3 lid 1 Awb"
    assert velden["knop_aanwezig"] is True
    vast = w["stappen"]["upload_vastgelegd"]
    assert vast["errors"] == []
    assert any("vastgelegd" in s.lower() for s in vast["success"])
    opgave = vast["opgave_op_schijf"]
    assert opgave is not None
    assert opgave["source_version"] == "2026-08-15"
    assert opgave["locator"] == "artikel 1:3 lid 1 Awb"
    assert opgave["url"].startswith("https://wetten.overheid.nl/")
    assert vast["url_widget"] == opgave["url"]  # veld blijft gevuld na vastleggen


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
    else:  # pragma: no cover - alleen als driver bedoeld
        raise SystemExit("gebruik: --driver <uitvoer.json>")
