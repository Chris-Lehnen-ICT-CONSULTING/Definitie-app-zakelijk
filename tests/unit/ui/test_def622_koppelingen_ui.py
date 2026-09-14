"""DEF-622 koppelingenreview (6b233060f): UI-aansluitingen op het CON-01-contract.

* K1 — de editor vervoerde `context_review` maar niet de geladen recordversie;
  een verlopen beoordeling telde in de editor als Voldoet.
* K3 — "Re-validate" in de experttab bouwde een nieuw `Definition` zonder id,
  beoordeling en versie, met niet-bestaande `get_org_list`/`get_jur_list`
  (lege context). Nu loopt hij via de canonieke recordadapter
  (`DefinitionRepository.get`) en de echte orchestrator.
* K5 — de nieuwe expertactie verzon de actor "expert" bij een ontbrekende
  gebruikersidentiteit. Vereist is de bestaande identiteit (sessie-`user` of
  de "Reviewer naam" van de reviewflow); ontbreekt die, dan is vastleggen
  geblokkeerd.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from services.definition_repository import DefinitionRepository
from ui.components.expert_review_tab import ExpertReviewTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ZIN = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
ACTOR = "synthetische-expert"


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "koppelingen-ui.db"))


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


def _record(repo: DefinitieRepository, definitie: str = ZIN) -> DefinitieRecord:
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie=definitie,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.9,
        )
    )
    rec = repo.get_definitie(did)
    assert rec is not None
    return rec


def _beoordeel(repo: DefinitieRepository, rec: DefinitieRecord) -> None:
    from domain.context.contract import beoordeel_context
    from domain.context.normalisatie import lees_contextwaarden

    uitkomst = beoordeel_context(
        rec.begrip,
        rec.get_definitie_tekst(),
        {
            "organisatorische_context": lees_contextwaarden(
                rec.organisatorische_context
            ),
            "juridische_context": [],
            "wettelijke_basis": [],
        },
    )
    naam = next(p for p in uitkomst.parts if p.evidence)
    assert repo.set_context_review(
        rec.id,
        {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            "version_number": rec.version_number,
            "decisions": {naam.id: {"function": "necessary", "reason": "Uitgever."}},
        },
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )


def _echte_validatie():
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    return ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        )
    )


def _mock_st(functie: str, reden: str, klik: bool) -> MagicMock:
    m = MagicMock()
    m.selectbox.return_value = functie
    m.text_input.return_value = reden
    m.button.return_value = klik
    return m


def _teksten(m: MagicMock) -> str:
    uit: list[str] = []
    for api in ("markdown", "success", "warning", "error", "info", "caption", "write"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return "\n".join(uit)


# ------------------------------------------------------------------ K1 editor


def test_editor_validatie_vervoert_de_geladen_recordversie(repo, sessie):
    """K1: reviewversie 2, geladen recordversie 4 (tekst teruggezet): de
    editor moet dezelfde versiegebonden uitkomst geven als het contract."""
    from ui.components.definition_edit_tab import DefinitionEditTab

    rec = _record(repo)
    _beoordeel(repo, rec)  # versie 2
    assert repo.update_definitie(rec.id, {"definitie": ZIN + " (v2)"})
    assert repo.update_definitie(rec.id, {"definitie": ZIN})
    geladen = DefinitionRepository(repo.db_path).get(rec.id)
    assert geladen is not None
    assert geladen.metadata["version_number"] == 4
    assert geladen.metadata["context_review"]["version_number"] == 2

    SessionStateManager.set_value("editing_definition_id", rec.id)
    SessionStateManager.set_value("editing_definition", geladen)
    for veld, waarde in (
        ("begrip", geladen.begrip),
        ("definitie", geladen.definitie),
        ("organisatorische_context", list(geladen.organisatorische_context)),
        ("juridische_context", []),
        ("wettelijke_basis", []),
        ("categorie", "type"),
        ("toelichting", ""),
        ("status", "review"),
    ):
        SessionStateManager.set_value(f"edit_{rec.id}_{veld}", waarde)

    orchestrator = _echte_validatie()
    container = SimpleNamespace(
        orchestrator=lambda: SimpleNamespace(validation_service=orchestrator)
    )
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.edit_service = SimpleNamespace(_validate_definition=lambda _d: None)
    with patch(
        "ui.cached_services.get_cached_service_container", return_value=container
    ):
        resultaat: Any = tab._validate_definition()

    assert resultaat is not None
    v2 = resultaat["raw_v2"]
    assert v2["rule_statuses"]["CON-01"] == "review_required"
    assert v2["rule_results"]["CON-01"]["review"]["applied"] is False
    assert "versie" in v2["rule_results"]["CON-01"]["review"]["reason"]


# -------------------------------------------------------------- K3 revalidate


def test_revalidate_gebruikt_de_canonieke_recordadapter(repo, sessie):
    """K3: geldig beoordeeld record met uitsluitend organisatorische context:
    ook na "Re-validate" is CON-01 Voldoet (context, id, versie en
    beoordeling reizen mee)."""
    rec = _record(repo)
    _beoordeel(repo, rec)
    actueel = repo.get_definitie(rec.id)
    assert actueel is not None

    container = SimpleNamespace(
        repository=lambda: DefinitionRepository(repo.db_path),
        orchestrator=lambda: SimpleNamespace(validation_service=_echte_validatie()),
    )
    m = MagicMock()
    with (
        patch(
            "ui.cached_services.get_cached_service_container", return_value=container
        ),
        patch("ui.components.expert_review_tab.st", m),
    ):
        ExpertReviewTab(repo)._revalidate_definition(actueel)

    v2: Any = SessionStateManager.get_value(f"review_v2_validation_{rec.id}")
    assert isinstance(v2, dict), _teksten(m)
    assert v2["rule_statuses"]["CON-01"] == "pass"
    assert v2["rule_results"]["CON-01"]["review"]["applied"] is True
    m.rerun.assert_called_once()


def test_revalidate_ververst_selectie_en_resultaat_uit_hetzelfde_record(repo, sessie):
    """K3 (delta 3): is het record intussen gewijzigd, dan horen het getoonde
    record en het validatieresultaat bij dezelfde actuele lezing — geen oude
    v2-selectie naast een v3-uitkomst."""
    rec = _record(repo)
    _beoordeel(repo, rec)
    oud = repo.get_definitie(rec.id)  # versie 2, Zilver-tekst, met beoordeling
    SessionStateManager.set_value("selected_review_definition", oud)
    assert repo.update_definitie(
        rec.id,
        {"definitie": "ander kwaliteitsmerk", "organisatorische_context": "[]"},
    )

    container = SimpleNamespace(
        repository=lambda: DefinitionRepository(repo.db_path),
        orchestrator=lambda: SimpleNamespace(validation_service=_echte_validatie()),
    )
    m = MagicMock()
    with (
        patch(
            "ui.cached_services.get_cached_service_container", return_value=container
        ),
        patch("ui.components.expert_review_tab.st", m),
    ):
        ExpertReviewTab(repo)._revalidate_definition(oud)

    v2: Any = SessionStateManager.get_value(f"review_v2_validation_{rec.id}")
    assert v2["rule_statuses"]["CON-01"] == "fail"  # geen context meer
    getoond: Any = SessionStateManager.get_value("selected_review_definition")
    assert getoond.version_number == 3
    assert getoond.definitie == "ander kwaliteitsmerk"
    assert getoond.get_context_review() is None or (
        getoond.get_context_review()["version_number"] != 3
    )


# ------------------------------------------------------------------ K5 actor


def test_zonder_gebruikersidentiteit_is_vastleggen_geblokkeerd(repo, sessie):
    """K5: geen sessie-`user` en geen reviewer naam: de knop is uitgeschakeld
    en een klik legt niets vast; er wordt geen actor verzonnen."""
    rec = _record(repo)
    SessionStateManager.set_value("selected_review_definition", rec)
    m = _mock_st("necessary", "Exclusieve uitgever.", True)
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        ExpertReviewTab(repo)._render_contextcontract(rec)

    assert m.button.call_args.kwargs.get("disabled") is True
    assert "reviewer" in (m.button.call_args.kwargs.get("help") or "").lower()
    na = repo.get_definitie(rec.id)
    assert na.get_context_review() is None
    assert na.version_number == rec.version_number
    assert na.updated_by != "expert"


def test_reviewer_naam_uit_de_reviewflow_is_de_actor(repo, sessie):
    """K5: de bestaande identiteit van de reviewflow ("Reviewer naam") telt
    als handelende gebruiker; geen nieuwe loginarchitectuur."""
    rec = _record(repo)
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("reviewer_name_input", "  Reviewer Rood  ")
    m = _mock_st("necessary", "Exclusieve uitgever.", True)
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        ExpertReviewTab(repo)._render_contextcontract(rec)

    assert m.button.call_args.kwargs.get("disabled") is False
    na = repo.get_definitie(rec.id)
    review = na.get_context_review()
    assert review is not None and review["actor"] == "Reviewer Rood"
    assert na.updated_by == "Reviewer Rood"
