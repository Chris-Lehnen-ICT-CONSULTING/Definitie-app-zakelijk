"""DEF-772 WP4 — de editor-route van INT-03 met gemockte `st`.

Echte state-route: `DefinitionEditTab` op een echte tijdelijke SQLite-database
(`DefinitionEditRepository`), de echte `_validate_definition`-route (wrapper +
`ModularValidationService` + fake INT-03-dienst via een vervangen
servicecontainer), `_save_definition` en `_render_fullwidth_validation_results`
/`_render_int03_section`. Streamlit zelf is een `MagicMock`: er is geen
browser en geen widgetrendering; de sessiestaat is een dict.

Bewezen:

* de INT-03-beoordeling van de laatste toetsing wordt bij Opslaan gebonden
  vastgelegd en gemeld; een niet-gebonden beoordeling wordt benoemd, nooit
  stil;
* de INT-03-sectie toont de opgeslagen uitkomst als replay (woord, passage,
  kandidaten, vraag, fout) en 'historisch' na een wijziging in het formulier;
* het normale resultatenblok toont een eerder 'Voldoet' nooit als actuele pass
  zodra tekst, toelichting, term of context in het formulier afwijken; de
  binding is inhoudelijk (terugzetten herstelt haar);
* opnieuw toetsen beoordeelt de werkelijk bewerkte kandidaat (de fake-dienst
  ontvangt exact de formuliertekst en -toelichting) — nooit de oude tekst.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    int03_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def772_fakes import (
    BINDING,
    FakeInt03Assessor,
    bouw_int03_beoordeling,
)
from toetsregels.manager import get_toetsregel_manager
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TOELICHTING = "Synthetische toelichting bij de archiefkaart."
ORG = ["Stichting Zilver"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "int03-ui.db"))


def _mock_st() -> MagicMock:
    m = MagicMock()
    m.text_input.side_effect = lambda *a, **kw: ""
    m.text_area.side_effect = lambda *a, **kw: ""
    m.button.side_effect = lambda *a, **kw: False
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _teksten(m: MagicMock) -> list[str]:
    uit: list[str] = []
    for api in ("markdown", "success", "warning", "error", "info", "caption", "text"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return uit


def _beoordeling(
    scenario: str = "pass", *, tekst: str = TEKST, toelichting=TOELICHTING
):
    return bouw_int03_beoordeling(
        BEGRIP, tekst, CONTEXT, toelichting, scenario=scenario
    )


def _definition(**meta: Any) -> Definition:
    metadata: dict[str, Any] = {"status": "draft", "created_by": "generator"}
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        metadata=metadata,
    )


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    # De actuele bindingen komen in de app uit de gecachte diensten; hier de
    # binding van de fake INT-03-dienst en geen ESS-03-dienst.
    tab._ess03_binding = lambda: None  # type: ignore[method-assign]
    tab._int03_binding = lambda: BINDING  # type: ignore[method-assign]
    return tab


def _vul_editor(did: int, geladen: Definition, **extra: Any) -> None:
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    waarden = {
        "begrip": geladen.begrip,
        "definitie": geladen.definitie,
        "organisatorische_context": list(geladen.organisatorische_context or []),
        "juridische_context": [],
        "wettelijke_basis": [],
        "categorie": "type",
        "toelichting": geladen.toelichting or "",
        "status": "draft",
        **extra,
    }
    for veld, waarde in waarden.items():
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)


def _valideer_via_editor(tab, assessor: FakeInt03Assessor) -> dict[str, Any]:
    """Zoals de knop 'Valideren': de editorroute met de echte wrapper."""
    container = MagicMock()
    container.orchestrator.return_value.validation_service = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        int03_assessment_service=assessor,
    )
    with (
        patch(
            "ui.cached_services.get_cached_service_container", return_value=container
        ),
        patch("ui.components.definition_edit_tab.st", _mock_st()),
    ):
        resultaat = tab._validate_definition()
    assert isinstance(resultaat, dict), resultaat
    tab._bewaar_sessieresultaat(
        resultaat, SessionStateManager.get_value("editing_definition_id")
    )
    return resultaat


def _render_blok(tab) -> list[str]:
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_fullwidth_validation_results()
    return _teksten(m)


def _int03_kop(teksten: list[str]) -> str:
    """De regelkop van INT-03 uit `render_rule_results` (niet de uitlegexpander)."""
    koppen = [t for t in teksten if t.startswith("**INT-03** ·")]
    assert len(koppen) == 1, teksten
    return koppen[0]


def _is_actuele_pass(teksten: list[str]) -> bool:
    kop = _int03_kop(teksten)
    return "Voldoet" in kop.replace("Voldoet niet", "")


def _passtelling(teksten: list[str]) -> int:
    regel = next(t for t in teksten if t.startswith("📋 **Beoordelingsdekking**"))
    deel = next(d for d in regel.split(" · ") if d.endswith(" voldoet"))
    return int(deel.split()[1])  # "✅ {n} voldoet"


def test_sessiebeoordeling_int03_komt_uit_de_laatste_toetsing(sessie):
    from ui.components.definition_edit_tab import DefinitionEditTab

    assert DefinitionEditTab._sessiebeoordeling_int03() is None
    SessionStateManager.set_value(
        "edit_last_validation", {"int03_assessment": {"a": 1}}
    )
    assert DefinitionEditTab._sessiebeoordeling_int03() == {"a": 1}
    SessionStateManager.set_value(
        "edit_last_validation",
        {"raw_v2": {"rule_results": {"INT-03": {"assessment": {"b": 2}}}}},
    )
    assert DefinitionEditTab._sessiebeoordeling_int03() == {"b": 2}
    SessionStateManager.set_value(
        "edit_last_validation", {"raw_v2": {"rule_results": {"INT-03": {}}}}
    )
    assert DefinitionEditTab._sessiebeoordeling_int03() is None


def test_int03_binding_komt_uit_de_gecachte_dienst_of_is_onbekend(sessie):
    from ui.components.definition_edit_tab import DefinitionEditTab

    container = MagicMock()
    container.int03_assessment_service.return_value.binding.return_value = BINDING
    with patch(
        "ui.cached_services.get_cached_service_container", return_value=container
    ):
        assert DefinitionEditTab._int03_binding() == BINDING
    with patch(
        "ui.cached_services.get_cached_service_container",
        side_effect=RuntimeError("geen container"),
    ):
        assert DefinitionEditTab._int03_binding() is None


def test_opslaan_legt_gebonden_int03_beoordeling_vast_en_meldt_dat(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    SessionStateManager.set_value("user", "tester")
    SessionStateManager.set_value(
        "edit_last_validation",
        {
            "raw_v2": {
                "rule_results": {"INT-03": {"assessment": _beoordeling("fail")}}
            },
        },
    )
    tab = _tab(repo)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata["int03_assessment"] == _beoordeling("fail")
    assert vers.definitie == TEKST  # opslaan wijzigt de tekst niet
    tekst = "\n".join(_teksten(m))
    assert "INT-03" in tekst and "opgeslagen" in tekst.lower()
    assert "AI-beoordeling" in tekst


def test_opslaan_benoemt_een_niet_gebonden_int03_beoordeling(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen, definitie=TEKST + " Aangepast.")
    SessionStateManager.set_value("user", "tester")
    SessionStateManager.set_value(
        "edit_last_validation", {"int03_assessment": _beoordeling("pass"), "raw_v2": {}}
    )
    tab = _tab(repo)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata.get("int03_assessment") is None
    tekst = "\n".join(_teksten(m))
    assert "INT-03" in tekst and "niet opgeslagen" in tekst.lower()
    assert "gewijzigd" in tekst


def test_int03_sectie_toont_replay_en_historisch_na_wijziging(repo, sessie):
    did = repo.save(_definition(int03_assessment=_beoordeling("insufficient")))
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_int03_section(geladen)
    tekst = "\n".join(_teksten(m))
    assert "INT-03" in tekst
    assert "Onvoldoende informatie" in tekst
    assert "Vraag: Naar welk antecedent verwijst het aangewezen woord?" in tekst
    assert "AI-beoordeling" in tekst
    assert "geen deskundigenoordeel" in tekst

    # Na een toelichtingwijziging in de editor is de opgeslagen beoordeling
    # historisch: geen vraag meer alsof zij actueel is.
    SessionStateManager.set_value(f"edit_{did}_toelichting", "Andere toelichting.")
    m2 = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m2),
        patch("ui.components.validation_view.st", m2),
    ):
        tab._render_int03_section(geladen)
    tekst2 = "\n".join(_teksten(m2))
    assert "historisch" in tekst2.lower()
    assert "gewijzigd" in tekst2.lower()
    assert "Vraag: Naar welk antecedent" not in tekst2


def test_int03_sectie_zonder_opgeslagen_beoordeling(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_int03_section(geladen)
    tekst = "\n".join(_teksten(m))
    assert "Nog geen INT-03-beoordeling opgeslagen" in tekst


def test_normaal_validatieresultaat_volgt_de_huidige_binding(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    SessionStateManager.set_value("user", "tester")
    tab = _tab(repo)
    assessor = FakeInt03Assessor(scenario="pass")
    resultaat = _valideer_via_editor(tab, assessor)
    (call,) = assessor.calls
    assert call["tekst"] == TEKST and call["toelichting"] == TOELICHTING
    assert resultaat["raw_v2"]["rule_statuses"]["INT-03"] == "pass"
    assert resultaat["int03_assessment"]["judgment"]["verdict"] == "pass"

    # Uitgangspunt: direct na de toetsing is INT-03 een actuele pass.
    basis = _render_blok(tab)
    assert _is_actuele_pass(basis)
    assert not any("historisch" in t.lower() and "INT-03" in t for t in basis)
    pass_basis = _passtelling(basis)

    # 1. Toelichting gewijzigd zonder opslaan: geen actuele pass, historisch.
    SessionStateManager.set_value(f"edit_{did}_toelichting", "Andere toelichting.")
    gewijzigd = _render_blok(tab)
    assert not _is_actuele_pass(gewijzigd), _int03_kop(gewijzigd)
    assert any("historisch" in t.lower() and "pass" in t for t in gewijzigd)
    assert _passtelling(gewijzigd) == pass_basis - 1
    assert not any(t.startswith("✅") and "INT-03" in t for t in gewijzigd)
    uitkomst = tab._actueel_sessieresultaat()["raw_v2"]
    assert uitkomst["rule_statuses"]["INT-03"] == "review_required"
    assert "INT-03" not in uitkomst["passed_rules"]

    # 1b. Dezelfde toelichting terugzetten: de binding klopt weer.
    SessionStateManager.set_value(f"edit_{did}_toelichting", TOELICHTING)
    assert _is_actuele_pass(_render_blok(tab))

    # 1c. Tekst-, term- of contextwijziging zonder opslaan: evenmin een pass.
    for veld, waarde in (
        ("definitie", TEKST + " Aangepast."),
        ("begrip", "archiefstuk"),
        ("organisatorische_context", ["Stichting Goud"]),
    ):
        origineel = SessionStateManager.get_value(f"edit_{did}_{veld}")
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)
        assert not _is_actuele_pass(_render_blok(tab)), veld
        SessionStateManager.set_value(f"edit_{did}_{veld}", origineel)
    assert _is_actuele_pass(_render_blok(tab))

    # 2. Opnieuw toetsen op de gewijzigde tekst: de dienst beoordeelt exact de
    #    formuliertekst, het resultaat bindt aan die kandidaat.
    nieuwe_tekst = TEKST + " Aangepast."
    SessionStateManager.set_value(f"edit_{did}_definitie", nieuwe_tekst)
    assessor2 = FakeInt03Assessor(scenario="fail")
    _valideer_via_editor(tab, assessor2)
    (call2,) = assessor2.calls
    assert call2["tekst"] == nieuwe_tekst
    opnieuw = _render_blok(tab)
    assert "Voldoet niet" in _int03_kop(opnieuw)
    assert not any("historisch" in t.lower() and "INT-03" in t for t in opnieuw)
    # Terug naar de oude tekst: het nieuwe resultaat is daar historisch voor.
    SessionStateManager.set_value(f"edit_{did}_definitie", TEKST)
    assert "Nog te beoordelen" in _int03_kop(_render_blok(tab))

    # 3. Annuleren wist het sessieresultaat; opnieuw openen toont geen oud blok.
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._cancel_edit()
    assert SessionStateManager.get_value("edit_last_validation") is None
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._start_edit_session(did)
    assert SessionStateManager.get_value("editing_definition_id") == did
    assert not any(t.startswith("**INT-03") for t in _render_blok(tab))


def test_toelichting_reist_als_betekenisgrond_mee_maar_repareert_geen_antecedent(
    repo, sessie
):
    """Een ontbrekend antecedent in de kern (`no_antecedent` → voldoet niet)
    wordt door een nieuwe toelichting niet stil een pass: de hertoets beoordeelt
    de kern opnieuw (met de toelichting als betekenisgrond) en de uitkomst
    blijft afkeur zolang de dienst dat oordeelt; het oude resultaat geldt na
    de toelichtingwijziging niet meer als actueel."""
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    assessor = FakeInt03Assessor(scenario="no_antecedent")
    _valideer_via_editor(tab, assessor)
    assert "Voldoet niet" in _int03_kop(_render_blok(tab))

    SessionStateManager.set_value(
        f"edit_{did}_toelichting", "Met 'die' worden de documenten bedoeld."
    )
    # Zonder hertoets: het oude oordeel is historisch, geen pass en geen fail.
    assert "Nog te beoordelen" in _int03_kop(_render_blok(tab))
    assessor2 = FakeInt03Assessor(scenario="no_antecedent")
    _valideer_via_editor(tab, assessor2)
    (call,) = assessor2.calls
    assert call["toelichting"] == "Met 'die' worden de documenten bedoeld."
    assert call["tekst"] == TEKST
    assert "Voldoet niet" in _int03_kop(_render_blok(tab))


def test_opslaan_na_toetsing_legt_de_beoordeling_gebonden_vast(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    SessionStateManager.set_value("user", "tester")
    tab = _tab(repo)
    _valideer_via_editor(tab, FakeInt03Assessor(scenario="fail"))
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
    assert uitkomst["status"] == "fail"
    assert uitkomst["review"]["assessment"]["applied"] is True
    assert vers.metadata["int03_assessment"]["judgment"]["verdict"] == "fail"
    assert any("INT-03" in t and "opgeslagen" in t.lower() for t in _teksten(m))
