"""DEF-768 WP4: de ESS-05-editorroute met echte sessiestaat en tijdelijke SQLite.

Echte state-route met gemockte `st`: een echte toetsing (wrapper +
ModularValidationService + fake ESS-05-dienst + echte repository-buren) op de
editorkandidaat levert `edit_last_validation`. Daarna:

* de sessiehelpers lezen de beoordeling en de actieve burenlijst van die
  toetsing (genormaliseerd en ruw);
* de kandidaat uit het formulier draagt de expertbesluiten van de sessie
  (ook een bewust gewiste lege ruimte `{}`) en de gerelateerde begrippen;
* een expertbesluit (bevestigen) maakt de oude ESS-05-beoordeling
  historisch zonder nieuwe modelaanroep (ADR-003: buurstatus zit in de
  bindingscontext); zonder actor wordt niets vastgelegd;
* opslaan legt het besluit vast en de niet meer bindende beoordeling níet
  (met reden); een nieuwe toetsing met de bevestigde buur voldoet;
* een nieuwe bewerksessie begint zonder niet-opgeslagen besluiten.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bouw_validatiecontext,
    normaliseer_validatieresultaat,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def768_fakes import BINDING, FakeEss05Assessor
from toetsregels.manager import get_toetsregel_manager
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
ORG = ["Synthetische Uitleendienst"]


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def opzet(tmp_path, sessie):
    repo = DefinitionEditRepository(str(tmp_path / "ess05-editor-ui.db"))
    buur = repo.save(
        Definition(
            begrip="klant",
            definitie="Persoon die iets afneemt.",
            categorie="type",
            organisatorische_context=list(ORG),
            metadata={"status": "draft", "created_by": "tester"},
        )
    )
    did = repo.save(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=[],
            wettelijke_basis=[],
            gerelateerde_begrippen=[],
            metadata={"status": "draft", "created_by": "tester"},
        )
    )
    return repo, did, buur


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


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    tab._ess03_binding = lambda: None  # type: ignore[method-assign]
    tab._ess05_binding = lambda: BINDING  # type: ignore[method-assign]
    return tab


def _vul_editor(did: int, geladen: Definition) -> None:
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
    }
    for veld, waarde in waarden.items():
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)


def _echte_toetsing(repo, did: int, assessor: FakeEss05Assessor) -> dict[str, Any]:
    """Zoals 'Valideren': echte wrapper met echte repository-buren."""
    geladen = DefinitionRepository(repo.db_path).get(did)
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(get_toetsregel_manager(), repository=repo),
        ess05_assessment_service=assessor,
        ess05_burenbron=DefinitionRepository(repo.db_path),
    )
    ruw = asyncio.run(
        wrapper.validate_text(
            begrip=geladen.begrip,
            text=geladen.definitie,
            ontologische_categorie=geladen.categorie,
            context=ValidationContext(
                metadata=bouw_validatiecontext(geladen, dict(geladen.metadata))
            ),
        )
    )
    return normaliseer_validatieresultaat(ruw)


def _ess05_kop(teksten: list[str]) -> str:
    koppen = [t for t in teksten if t.startswith("**ESS-05")]
    assert koppen, teksten
    return koppen[0]


def _render_blok(tab) -> list[str]:
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_fullwidth_validation_results()
    return _teksten(m)


def _voldoet(kop: str) -> bool:
    return "Voldoet" in kop.replace("Voldoet niet", "")


class TestSessiehelpers:
    def test_beoordeling_en_buren_uit_de_laatste_toetsing(self, sessie):
        from ui.components.definition_edit_tab import DefinitionEditTab

        assert DefinitionEditTab._sessiebeoordeling_ess05() is None
        assert DefinitionEditTab._sessie_actieve_buren() is None
        SessionStateManager.set_value(
            "edit_last_validation",
            {
                "raw_v2": {
                    "ess05_assessment": {"status": "assessed"},
                    "ess05_actieve_buren": [{"id": "repository:1"}],
                }
            },
        )
        assert DefinitionEditTab._sessiebeoordeling_ess05() == {"status": "assessed"}
        assert DefinitionEditTab._sessie_actieve_buren() == [{"id": "repository:1"}]
        SessionStateManager.set_value(
            "edit_last_validation",
            {"ess05_assessment": {"status": "error"}, "ess05_actieve_buren": []},
        )
        assert DefinitionEditTab._sessiebeoordeling_ess05() == {"status": "error"}
        assert DefinitionEditTab._sessie_actieve_buren() == []

    def test_kandidaat_draagt_sessiebesluiten_en_gerelateerde_begrippen(self, opzet):
        repo, did, _ = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        geladen.metadata["ess05_lege_ruimte"] = {"fingerprint": "oud"}
        geladen.gerelateerde_begrippen = ["werknemer"]
        _vul_editor(did, geladen)
        tab = _tab(repo)

        kandidaat = tab._kandidaat_uit_formulier(geladen)
        assert kandidaat.metadata["ess05_lege_ruimte"] == {"fingerprint": "oud"}
        assert kandidaat.gerelateerde_begrippen == ["werknemer"]

        # De sessie wint, ook een bewust gewiste bevestiging.
        SessionStateManager.set_value(f"edit_{did}_ess05_lege_ruimte", {})
        SessionStateManager.set_value(f"edit_{did}_ess05_buren", [{"term": "x"}])
        kandidaat = tab._kandidaat_uit_formulier(geladen)
        assert kandidaat.metadata["ess05_lege_ruimte"] == {}
        assert kandidaat.metadata["ess05_buren"] == [{"term": "x"}]
        assert tab._ess05_sessiebesluiten(did) == {
            "ess05_buren": [{"term": "x"}],
            "ess05_lege_ruimte": {},
        }


class TestExpertbesluitEnOpslaan:
    def test_bevestigen_maakt_historisch_zonder_modelaanroep_en_hertoetsing_voldoet(
        self, opzet
    ):
        """Gemigreerd (ADR-003, `/1` → `/2`): onder `/1` gaf bevestigen direct
        'Voldoet' en werd de oude beoordeling opgeslagen. Nu is de buurstatus
        deel van de bindingscontext: de oude beoordeling wordt historisch (geen
        stille pass, geen modelaanroep), het besluit wordt opgeslagen, de oude
        beoordeling niet; pas een nieuwe, expliciete toetsing voldoet."""
        repo, did, buur = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value("user", "deskundige")
        tab = _tab(repo)
        assessor = FakeEss05Assessor(scenario="pass")
        SessionStateManager.set_value(
            "edit_last_validation", _echte_toetsing(repo, did, assessor)
        )
        assert len(assessor.calls) == 1

        # Onbevestigde repository-buur: open, nooit een stille pass.
        assert not _voldoet(_ess05_kop(_render_blok(tab)))

        with patch("ui.components.definition_edit_tab.st", _mock_st()):
            fout = tab._pas_ess05_besluit_toe(
                geladen, "bevestig", buur_id=f"repository:{buur}"
            )
        assert fout is None
        besluit = SessionStateManager.get_value(f"edit_{did}_ess05_buren")
        assert besluit[0]["bevestigd"] is True
        assert besluit[0]["actor"] == "deskundige"

        # Geen stille 'Voldoet' op een oude beoordeling, geen nieuwe modelaanroep.
        assert not _voldoet(_ess05_kop(_render_blok(tab)))
        assert len(assessor.calls) == 1

        m = _mock_st()
        with patch("ui.components.definition_edit_tab.st", m):
            tab._save_definition()
        heropend = DefinitionRepository(repo.db_path).get(did)
        assert heropend.metadata["ess05_buren"] == besluit
        assert "ess05_assessment" not in heropend.metadata
        assert any(
            "niet opgeslagen" in t and "buurbevestiging" in t for t in _teksten(m)
        )

        # Een nieuwe, expliciete toetsing op de opgeslagen kandidaat voldoet.
        SessionStateManager.set_value(
            "edit_last_validation", _echte_toetsing(repo, did, assessor)
        )
        assert len(assessor.calls) == 2
        assert _voldoet(_ess05_kop(_render_blok(tab)))

    def test_zonder_actor_wordt_geen_besluit_vastgelegd(self, opzet):
        repo, did, buur = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        tab = _tab(repo)
        SessionStateManager.set_value(
            "edit_last_validation",
            _echte_toetsing(repo, did, FakeEss05Assessor(scenario="pass")),
        )
        fout = tab._pas_ess05_besluit_toe(
            geladen, "bevestig", buur_id=f"repository:{buur}"
        )
        assert fout and "naam" in fout
        assert SessionStateManager.get_value(f"edit_{did}_ess05_buren") is None

    def test_afwijzen_vereist_grond(self, opzet):
        repo, did, buur = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value("user", "deskundige")
        tab = _tab(repo)
        SessionStateManager.set_value(
            "edit_last_validation",
            _echte_toetsing(repo, did, FakeEss05Assessor(scenario="pass")),
        )
        fout = tab._pas_ess05_besluit_toe(
            geladen, "wijs_af", buur_id=f"repository:{buur}", grond="  "
        )
        assert fout and "grond" in fout
        assert SessionStateManager.get_value(f"edit_{did}_ess05_buren") is None

    def test_lege_ruimte_bevestigen_bindt_aan_de_huidige_kandidaat(
        self, tmp_path, sessie
    ):
        repo = DefinitionEditRepository(str(tmp_path / "ess05-leeg.db"))
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="type",
                organisatorische_context=list(ORG),
                metadata={"status": "draft", "created_by": "tester"},
            )
        )
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value("user", "deskundige")
        tab = _tab(repo)
        fout = tab._pas_ess05_besluit_toe(
            geladen, "lege_ruimte", grond="Enig begrip in deze synthetische context."
        )
        assert fout is None
        from services.definition_edit_service import ess05_uitkomst_van_definition

        kandidaat = tab._kandidaat_uit_formulier(geladen)
        assert ess05_uitkomst_van_definition(kandidaat, [], BINDING)["status"] == "pass"
        # Tekst wijzigen: de bevestiging vervalt vanzelf.
        SessionStateManager.set_value(f"edit_{did}_definitie", TEKST + " Anders.")
        kandidaat = tab._kandidaat_uit_formulier(geladen)
        assert ess05_uitkomst_van_definition(kandidaat, [], BINDING)["status"] != "pass"

    def test_sectieknop_legt_besluit_vast_zonder_sleutelbotsing(self, opzet):
        repo, did, buur = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value("user", "deskundige")
        tab = _tab(repo)
        SessionStateManager.set_value(
            "edit_last_validation",
            _echte_toetsing(repo, did, FakeEss05Assessor(scenario="pass")),
        )
        m = _mock_st()
        m.button.side_effect = lambda *a, **kw: kw.get("key") == (
            f"edit_{did}_ess05_bevestig_0"
        )
        with (
            patch("ui.components.definition_edit_tab.st", m),
            patch("ui.components.validation_view.st", m),
        ):
            tab._render_ess05_section(geladen)
        teksten = _teksten(m)
        assert any(t.startswith("**ESS-05") for t in teksten), teksten
        assert any("klant (repository, onbevestigd)" in t for t in teksten)
        besluit = SessionStateManager.get_value(f"edit_{did}_ess05_buren")
        assert besluit[0]["id"] == f"repository:{buur}"
        assert besluit[0]["bevestigd"] is True
        m.rerun.assert_called()
        widgetsleutels = {
            c.kwargs.get("key")
            for api in ("button", "text_input", "text_area")
            for c in getattr(m, api).call_args_list
        }
        assert f"edit_{did}_ess05_buren" not in widgetsleutels
        assert f"edit_{did}_ess05_lege_ruimte" not in widgetsleutels

    def test_nieuwe_bewerksessie_begint_zonder_onopgeslagen_besluiten(self, opzet):
        repo, did, _ = opzet
        SessionStateManager.set_value(f"edit_{did}_ess05_buren", [{"term": "x"}])
        SessionStateManager.set_value(f"edit_{did}_ess05_lege_ruimte", {})
        tab = _tab(repo)
        with patch("ui.components.definition_edit_tab.st", _mock_st()):
            tab._start_edit_session(did)
        assert SessionStateManager.get_value(f"edit_{did}_ess05_buren") is None
        assert SessionStateManager.get_value(f"edit_{did}_ess05_lege_ruimte") is None
