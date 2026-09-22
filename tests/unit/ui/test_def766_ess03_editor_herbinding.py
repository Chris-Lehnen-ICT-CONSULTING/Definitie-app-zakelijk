"""DEF-766 correctieronde 2, punt A (R1/R5) — het normale editor-validatieresultaat
volgt de huidige formulier-/recordbinding.

Echte state-route met gemockte `st`: een echte validatie (wrapper +
ModularValidationService + fake ESS-03-dienst) op de editorkandidaat mét
verduidelijking levert `edit_last_validation` met ESS-03 'Voldoet'. Daarna:

* wijzigen zónder opslaan (verduidelijking wissen, tekst wijzigen): het
  bovenste resultatenblok toont ESS-03 niet meer als actuele pass, maar als
  historisch — geen nieuwe modelaanroep;
* wissen én opslaan: idem, ook na herladen van het record;
* de binding is inhoudelijk: dezelfde verduidelijking terugzetten maakt het
  oordeel weer actueel (geen blinde invalidatie);
* Annuleren wist het sessieresultaat; opnieuw openen toont geen oud blok.

Het browserbewijs (browser-verification-v2.md, stap 5) toonde precies dit gat:
DB en aparte replaysectie correct, bovenste blok nog 'Voldoet'.
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
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def766_fakes import BINDING, FakeEss03Assessor
from toetsregels.manager import get_toetsregel_manager
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."
ORG = ["Synthetisch Waterschap"]
VERDUIDELIJKING = "Peil P is het zomerpeil van het waterschap."


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "ess03-herbinding.db"))


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


def _ess03_kop(teksten: list[str]) -> str:
    koppen = [t for t in teksten if t.startswith("**ESS-03")]
    assert koppen, teksten
    return koppen[0]


def _definition() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        metadata={
            "status": "draft",
            "created_by": "generator",
            "ess03_verduidelijking": VERDUIDELIJKING,
        },
    )


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    tab._ess03_binding = lambda: BINDING  # type: ignore[method-assign]
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
        "ess03_verduidelijking": geladen.metadata.get("ess03_verduidelijking", ""),
        **extra,
    }
    for veld, waarde in waarden.items():
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)


def _echte_toetsing(tab, did: int, geladen: Definition) -> dict[str, Any]:
    """Zoals 'Valideren' in de app: echte wrapper op de editorkandidaat."""
    kandidaat = Definition(
        id=did,
        begrip=SessionStateManager.get_value(f"edit_{did}_begrip"),
        definitie=SessionStateManager.get_value(f"edit_{did}_definitie"),
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        categorie="type",
        toelichting=SessionStateManager.get_value(f"edit_{did}_toelichting"),
        metadata={
            "status": "draft",
            "ess03_verduidelijking": tab._sessieverduidelijking(did),
        },
    )
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        ess03_assessment_service=FakeEss03Assessor(scenario="pass"),
    )
    ruw = asyncio.run(
        wrapper.validate_text(
            begrip=kandidaat.begrip,
            text=kandidaat.definitie,
            ontologische_categorie=kandidaat.categorie,
            context=ValidationContext(
                metadata=bouw_validatiecontext(kandidaat, dict(geladen.metadata))
            ),
        )
    )
    assert ruw["rule_statuses"]["ESS-03"] == "pass"
    return normaliseer_validatieresultaat(ruw)


def _render_blok(tab) -> list[str]:
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_fullwidth_validation_results()
    return _teksten(m)


def _is_actuele_pass(teksten: list[str]) -> bool:
    kop = _ess03_kop(teksten)
    return "Voldoet" in kop.replace("Voldoet niet", "")


def _passtelling(teksten: list[str]) -> int:
    regel = next(t for t in teksten if t.startswith("📋 **Beoordelingsdekking**"))
    deel = next(d for d in regel.split(" · ") if d.endswith(" voldoet"))
    return int(deel.split()[1])  # "✅ {n} voldoet"


def test_normaal_validatieresultaat_volgt_de_huidige_binding(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    SessionStateManager.set_value("user", "tester")
    tab = _tab(repo)
    SessionStateManager.set_value(
        "edit_last_validation", _echte_toetsing(tab, did, geladen)
    )

    # Uitgangspunt: direct na de toetsing is ESS-03 een actuele pass.
    basis = _render_blok(tab)
    assert _is_actuele_pass(basis)
    assert any("historisch" in t.lower() for t in basis) is False
    pass_basis = _passtelling(basis)

    # 1. Wijzigen zonder opslaan: verduidelijking bewust gewist.
    SessionStateManager.set_value(f"edit_{did}_ess03_verduidelijking", "")
    gewist = _render_blok(tab)
    assert not _is_actuele_pass(gewist), _ess03_kop(gewist)
    assert any("historisch" in t.lower() and "pass" in t for t in gewist)
    assert _passtelling(gewist) == pass_basis - 1
    assert not any(
        t.startswith("✅") and "ESS-03" in t for t in gewist
    ), "ESS-03 mag niet meer onder de geslaagde regels staan"

    # 1b. Dezelfde verduidelijking terugzetten: de binding klopt weer.
    SessionStateManager.set_value(f"edit_{did}_ess03_verduidelijking", VERDUIDELIJKING)
    assert _is_actuele_pass(_render_blok(tab))

    # 1c. Tekstwijziging zonder opslaan: evenmin een actuele pass.
    SessionStateManager.set_value(f"edit_{did}_definitie", TEKST + " Aangepast.")
    assert not _is_actuele_pass(_render_blok(tab))
    SessionStateManager.set_value(f"edit_{did}_definitie", TEKST)

    # 2. Wissen én opslaan (zonder hertoets): record leeg, blok geen actuele pass.
    SessionStateManager.set_value(f"edit_{did}_ess03_verduidelijking", "")
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata["ess03_verduidelijking"] == ""
    SessionStateManager.set_value("editing_definition", vers)
    na_opslaan = _render_blok(tab)
    assert not _is_actuele_pass(na_opslaan), _ess03_kop(na_opslaan)
    assert any("historisch" in t.lower() for t in na_opslaan)

    # 3. Annuleren wist het sessieresultaat; opnieuw openen toont geen oud blok.
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._cancel_edit()
    assert SessionStateManager.get_value("edit_last_validation") is None
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._start_edit_session(did)
    assert SessionStateManager.get_value("editing_definition_id") == did
    heropend = _render_blok(tab)
    assert not any(t.startswith("**ESS-03") for t in heropend)


def test_openen_van_een_ander_record_toont_geen_oud_resultaat(repo, sessie):
    did = repo.save(_definition())
    ander = repo.save(
        Definition(
            begrip="kiezel",
            definitie="Steen die door natuurlijke erosie is afgerond.",
            organisatorische_context=list(ORG),
            juridische_context=[],
            wettelijke_basis=[],
            metadata={"status": "draft"},
        )
    )
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    SessionStateManager.set_value(
        "edit_last_validation", _echte_toetsing(tab, did, geladen)
    )
    assert _is_actuele_pass(_render_blok(tab))
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._start_edit_session(ander)
    assert SessionStateManager.get_value("edit_last_validation") is None
    assert not any(t.startswith("**ESS-03") for t in _render_blok(tab))
