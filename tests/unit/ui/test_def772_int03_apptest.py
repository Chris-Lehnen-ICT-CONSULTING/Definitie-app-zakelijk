"""DEF-772 WP4 — de INT-03-editorroute met échte Streamlit-widgets (AppTest).

Zelfde opzet als ``test_def743_editor_apptest.py``: de pytest-conftest
vervangt ``streamlit`` procesbreed door een mock, dus dit bestand start zichzelf
als subprocess-driver achter ``tests.offline_bootstrap`` (dummy sleutels,
netwerk- en DB-gate) en leest de waarnemingen terug. De volledige
`DefinitionEditTab` rendert op een tijdelijke SQLite-database; de
INT-03-binding komt uit de échte gecachte servicecontainer (promptversie
uit code, norm uit het regelrecord, provider/model uit `config.yaml`) — er
wordt géén modelaanroep gedaan: de opgeslagen beoordeling is een
synthetisch document van `tests.fixtures.def772_fakes`, gebonden aan exact
die actuele binding, en de sessietoetsing is een vooraf gezet resultaat.

Bewezen met echte widgets:

* de INT-03-sectie van het opgeslagen record toont de opgeslagen
  AI-uitkomst (voldoet niet, verwijzend woord, kandidaten, AI-herkomst)
  zonder UI-exceptie; de binding uit de container is dezelfde als de
  standaardbinding van de export (`actuele_binding`);
* een bewerking in het échte toelichting-widget maakt de opgeslagen
  beoordeling zichtbaar historisch (geen 'Voldoet niet' meer als actueel);
* een sessietoetsing die bij de bewerkte kandidaat hoort verschijnt in het
  normale resultatenblok als actueel; de échte Opslaan-knop legt haar
  gebonden vast (historie met het vorige document, versie +1, tekst
  ongewijzigd) en meldt dat; na herladen toont de sectie de nieuwe
  beoordeling als actueel.
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
BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TOELICHTING = "Synthetische toelichting bij de archiefkaart."
TOELICHTING_NIEUW = "Andere toelichting na bewerking."
ORG = ["Stichting Zilver"]
JUR = ["privaatrecht"]
WET = ["Regeling Z"]


def _gebonden_document(binding, *, toelichting: str, scenario: str) -> dict:
    """Een fake-beoordeling voor exact deze kandidaat, gebonden aan de
    werkelijke binding van de app (promptversie, norm, provider, model)."""
    from tests.fixtures.def772_fakes import bouw_int03_beoordeling

    document = bouw_int03_beoordeling(
        BEGRIP,
        TEKST,
        {
            "organisatorische_context": ORG,
            "juridische_context": JUR,
            "wettelijke_basis": WET,
        },
        toelichting,
        scenario=scenario,
        model=binding.model,
    )
    document["prompt_version"] = binding.prompt_version
    document["norm_sha256"] = binding.norm_sha256
    document["attribution"]["provider"] = binding.provider
    document["attribution"]["model"] = binding.model
    return document


def _opzet() -> dict:
    """Eenmalig per driverproces: tmp-DB, record met gebonden INT-03-document."""
    import tempfile

    from services.definition_edit_repository import DefinitionEditRepository
    from services.interfaces import Definition
    from services.validation.int03_assessment_service import actuele_binding
    from tests.fixtures import def772_fakes

    binding = actuele_binding()
    assert binding is not None, "actuele INT-03-binding niet te bepalen"
    pad = Path(tempfile.mkdtemp()) / "int03-apptest.db"
    repo = DefinitionEditRepository(str(pad))
    did = repo.save(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            toelichting=TOELICHTING,
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={
                "status": "draft",
                "int03_assessment": _gebonden_document(
                    binding, toelichting=TOELICHTING, scenario="fail"
                ),
            },
        )
    )
    staat = {
        "pad": str(pad),
        "did": did,
        "actor": ACTOR,
        "binding": binding.als_dict(),
        "sessiedocument": _gebonden_document(
            binding, toelichting=TOELICHTING_NIEUW, scenario="pass"
        ),
    }
    def772_fakes.APPTEST_STATE = staat  # type: ignore[attr-defined]
    return staat


def _app() -> None:
    import streamlit as st

    from services.definition_edit_repository import DefinitionEditRepository
    from tests.fixtures import def772_fakes
    from ui.components.definition_edit_tab import DefinitionEditTab
    from ui.session_state import SessionStateManager

    # `AppTest.from_function` voert deze functie als los script uit:
    # modulevariabelen zijn hier niet zichtbaar, de staat leeft op de
    # fixturemodule.
    staat = def772_fakes.APPTEST_STATE  # type: ignore[attr-defined]
    SessionStateManager.set_value("user", staat["actor"])
    # De binding zoals de editor haar werkelijk bepaalt (gecachte container).
    ui_binding = DefinitionEditTab._int03_binding()
    SessionStateManager.set_value(
        "apptest_ui_binding", ui_binding.als_dict() if ui_binding else None
    )
    st.markdown("## Volledige editor")
    tab = DefinitionEditTab(repository=DefinitionEditRepository(staat["pad"]))
    SessionStateManager.set_value("editing_definition_id", staat["did"])
    tab.render()


def _sessiewaarde(at, sleutel: str):
    """`SafeSessionState` van AppTest kent geen `.get`; lees fail-safe."""
    try:
        return at.session_state[sleutel]
    except KeyError:
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


def _expander_teksten(at) -> dict[str, str]:
    uit: dict[str, str] = {}
    for e in at.expander:
        delen = []
        for soort in (
            "markdown",
            "caption",
            "text",
            "warning",
            "error",
            "success",
            "info",
        ):
            delen.extend(str(x.value) for x in getattr(e, soort, []))
        uit[str(e.label)] = "\n".join(delen)
    return uit


def _sessieresultaat(staat: dict, did: int) -> dict:
    """Een normaal (genormaliseerd) toetsresultaat zoals 'Valideren' het in de
    sessie zet, met de INT-03-beoordeling voor de bewerkte kandidaat."""
    from domain.int03.contract import Beoordelingsbinding, beoordeel_verwijzingen

    binding = Beoordelingsbinding(**staat["binding"])
    detail = beoordeel_verwijzingen(
        BEGRIP,
        TEKST,
        {
            "organisatorische_context": ORG,
            "juridische_context": JUR,
            "wettelijke_basis": WET,
        },
        TOELICHTING_NIEUW,
        assessment=staat["sessiedocument"],
        binding=binding,
    ).als_dict()
    detail["signals"] = []
    raw = {
        "version": "2.1.0",
        "validation_status": "validated",
        "overall_score": None,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": ["INT-03"],
        "detailed_scores": {},
        "system": {},
        "rule_statuses": {"INT-03": detail["status"]},
        "rule_results": {"INT-03": detail},
        "review_required": [],
        "evaluation_coverage": {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "review_required": 0,
            "error": 0,
            "not_evaluated": 0,
            "not_applicable": 0,
            "evaluated": 1,
            "coverage_ratio": 1.0,
        },
    }
    return {
        "valid": False,
        "score": None,
        "issues": [],
        "rule_results": raw["rule_results"],
        "rule_statuses": raw["rule_statuses"],
        "evaluation_coverage": raw["evaluation_coverage"],
        "review_required": [],
        "validation_status": "validated",
        "int03_assessment": staat["sessiedocument"],
        "raw_v2": raw,
        "editing_definition_id": did,
    }


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    offline_bootstrap.install()
    from streamlit.testing.v1 import AppTest

    from database.definitie_repository import DefinitieRepository

    w: dict = {"gate_actief": offline_bootstrap.gate_is_actief(), "stappen": {}}
    staat = _opzet()
    did = staat["did"]
    facade = DefinitieRepository(staat["pad"])
    sleutel_toelichting = f"edit_{did}_toelichting"
    sectie = "🔗 Verwijzingen (INT-03) — opgeslagen AI-beoordeling"

    at = AppTest.from_function(_app, default_timeout=180)
    at.run()
    for e in at.exception:  # zichtbaar in de subprocess-stderr bij een fout
        print("APPTEST-EXCEPTIE:", e.value, file=sys.stderr)
    voor = facade.get_definitie(did)
    w["stappen"]["render"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "binding_export": staat["binding"],
        "binding_ui": _sessiewaarde(at, "apptest_ui_binding"),
        "expanders": [str(e.label) for e in at.expander],
        "int03_sectie": _expander_teksten(at).get(sectie, ""),
        "toelichting_widget": at.text_area(key=sleutel_toelichting).value,
        "versie_db": voor.version_number,
        "tekst": _alle_tekst(at),
    }

    # Echte bewerking van het toelichting-widget: de opgeslagen beoordeling
    # hoort niet meer bij de kandidaat in het formulier.
    at.text_area(key=sleutel_toelichting).set_value(TOELICHTING_NIEUW).run()
    w["stappen"]["toelichting_gewijzigd"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "int03_sectie": _expander_teksten(at).get(sectie, ""),
        "toelichting_widget": at.text_area(key=sleutel_toelichting).value,
        "versie_db": facade.get_definitie(did).version_number,
    }

    # Een sessietoetsing die bij de bewerkte kandidaat hoort (zoals na
    # 'Valideren'): het normale resultatenblok toont haar als actueel.
    at.session_state["edit_last_validation"] = _sessieresultaat(staat, did)
    at.run()
    w["stappen"]["sessieresultaat"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "tekst": _alle_tekst(at),
        "save_disabled": next(
            (bool(b.disabled) for b in at.button if b.key == "save_btn"), None
        ),
    }

    # De échte Opslaan-knop.
    at.button(key="save_btn").click().run()
    na = facade.get_definitie(did)
    w["stappen"]["opgeslagen"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "success": [str(s.value) for s in at.success],
        "warning": [str(x.value) for x in at.warning],
        "document_db": na.get_int03_assessment(),
        "historie_db": [h["assessment"] for h in na.get_int03_assessment_history()],
        "tekst_db": na.get_definitie_tekst(),
        "definitie_db": na.definitie,
        "versie_db": na.version_number,
        "updated_by": na.updated_by,
    }

    # Herladen (verse editor-sessie): de sectie toont de nieuwe beoordeling.
    at.session_state["editing_definition"] = None
    at.session_state["edit_last_validation"] = None
    at.run()
    w["stappen"]["herladen"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "int03_sectie": _expander_teksten(at).get(sectie, ""),
        "toelichting_widget": at.text_area(key=sleutel_toelichting).value,
    }
    Path(uit_pad).write_text(
        json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def772-int03-apptest") / "waarnemingen.json"
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


def test_sectie_toont_opgeslagen_uitkomst_met_de_echte_binding(w):
    render = w["stappen"]["render"]
    assert render["binding_ui"] == render["binding_export"]
    assert render["binding_ui"]["model"], render["binding_ui"]
    assert any("Verwijzingen (INT-03)" in e for e in render["expanders"])
    sectie = render["int03_sectie"]
    assert "**INT-03** · ❌ Voldoet niet" in sectie
    assert "AI-beoordeling" in sectie
    assert "Verwijzend woord 'die'" in sectie
    assert "Kandidaten: 'Beschrijving'" in sectie
    assert "historisch" not in sectie.lower()
    assert "geen deskundigenoordeel" in sectie
    assert render["toelichting_widget"] == TOELICHTING


def test_bewerking_in_echt_widget_maakt_de_beoordeling_historisch(w):
    stap = w["stappen"]["toelichting_gewijzigd"]
    assert stap["toelichting_widget"] == TOELICHTING_NIEUW
    assert stap["versie_db"] == w["stappen"]["render"]["versie_db"]  # niets opgeslagen
    sectie = stap["int03_sectie"]
    assert "**INT-03** · 🟠 Nog te beoordelen" in sectie
    assert "historisch" in sectie.lower() and "gewijzigd" in sectie
    assert "eerder oordeel: fail" in sectie
    assert "Verwijzend woord" not in sectie  # oude verwijzingen niet als actueel


def test_sessieresultaat_voor_de_bewerkte_kandidaat_is_actueel(w):
    stap = w["stappen"]["sessieresultaat"]
    assert stap["save_disabled"] is False
    assert "**INT-03** · ✅ Voldoet" in stap["tekst"]
    assert "Verwijzend woord 'die'" in stap["tekst"]


def test_echte_opslaanknop_legt_de_beoordeling_gebonden_vast(w):
    """De DB-effecten van de échte knop. De meldingen van de opslaan-run zelf
    (o.a. '… van de laatste toetsing opgeslagen …') zijn in AppTest niet
    waarneembaar: `_save_definition` eindigt met `st.rerun()` en de boom
    toont daarna de verse run (bestaand gedrag, ook voor de ESS-03- en
    bronmeldingen); de meldingtekst is gedekt door
    `test_def772_int03_editor.py`."""
    voor = w["stappen"]["render"]
    stap = w["stappen"]["opgeslagen"]
    assert not any("INT-03" in s and "niet opgeslagen" in s for s in stap["warning"])
    assert stap["document_db"]["judgment"]["verdict"] == "pass"
    assert stap["document_db"]["attribution"]["model"] == voor["binding_ui"]["model"]
    [vorige] = stap["historie_db"]
    assert vorige["judgment"]["verdict"] == "fail"
    assert stap["versie_db"] == voor["versie_db"] + 1
    assert stap["tekst_db"] == TEKST  # opslaan wijzigt de definitietekst niet
    assert TOELICHTING_NIEUW in stap["definitie_db"]
    assert stap["updated_by"] == ACTOR


def test_na_herladen_toont_de_sectie_de_nieuwe_beoordeling_actueel(w):
    stap = w["stappen"]["herladen"]
    assert stap["toelichting_widget"] == TOELICHTING_NIEUW
    sectie = stap["int03_sectie"]
    assert "**INT-03** · ✅ Voldoet" in sectie
    assert "Verwijzend woord 'die'" in sectie
    assert "historisch" not in sectie.lower()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
    else:  # pragma: no cover - alleen als driver bedoeld
        raise SystemExit("gebruik: --driver <uitvoer.json>")
