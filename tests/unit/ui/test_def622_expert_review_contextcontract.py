"""DEF-622 (B-07): de expert legt de naamfunctie vast in de bestaande reviewflow.

Keten: open naamsignaal zichtbaar → expert kiest functie + reden → "Leg
beoordeling vast" → beoordeling op het record (versiebump) → geselecteerd
record ververst naar de actuele versie → de vaststelgate ziet CON-01 als
Voldoet (met de overige gatecomponenten synthetisch positief) → na een
tekstwijziging vervalt de beoordeling weer.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from ui.components.expert_review_tab import ExpertReviewTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

TEKST = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "expert.db"))


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    SessionStateManager.set_value("user", "synthetische-expert")
    return st.session_state


def _record(repo: DefinitieRepository) -> DefinitieRecord:
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie=TEKST,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context='["privaatrecht"]',
            wettelijke_basis='["Regeling Z"]',
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.9,
        )
    )
    rec = repo.get_definitie(did)
    assert rec is not None
    return rec


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


def test_open_naamsignaal_is_zichtbaar_met_uitleg(repo, sessie):
    rec = _record(repo)
    with (
        patch(
            "ui.components.expert_review_tab.st", _mock_st("necessary", "", False)
        ) as m,
        patch("ui.components.validation_view.st", m),
    ):
        ExpertReviewTab(repo)._render_contextcontract(rec)
    tekst = _teksten(m)
    assert "Nog te beoordelen" in tekst
    assert "Stichting Zilver" in tekst
    assert "Laat de expert de functie van de naam beoordelen" in tekst
    # Zonder reden is vastleggen uitgeschakeld.
    assert m.button.call_args.kwargs.get("disabled") is True


def test_vastleggen_bewaart_beoordeling_ververst_versie_en_maakt_vaststelbaar(
    repo, sessie
):
    from services.definition_repository import DefinitionRepository
    from services.definition_workflow_service import DefinitionWorkflowService
    from services.workflow_service import WorkflowService

    rec = _record(repo)
    SessionStateManager.set_value("selected_review_definition", rec)
    m = _mock_st("necessary", "Exclusieve uitgever van dit keurmerk.", True)
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        ExpertReviewTab(repo)._render_contextcontract(rec)

    # Beoordeling op het record, met actor en gebonden vingerafdruk.
    vers = repo.get_definitie(rec.id)
    assert vers is not None
    review = vers.get_context_review()
    assert review is not None and review["actor"] == "synthetische-expert"
    assert next(iter(review["decisions"].values()))["function"] == "necessary"
    # Opslaan bumpt de versie; het geselecteerde record is ververst.
    assert vers.version_number == rec.version_number + 1
    geselecteerd: Any = SessionStateManager.get_value("selected_review_definition")
    assert geselecteerd.version_number == vers.version_number
    m.rerun.assert_called_once()

    # De vaststelgate ziet CON-01 nu als Voldoet en de vaststelling slaagt
    # tegen de actuele versie (overige gatecomponenten synthetisch positief).
    service_repo = DefinitionRepository(repo.db_path)
    workflow = DefinitionWorkflowService(WorkflowService(), service_repo)
    gate = workflow.preview_gate(rec.id)
    assert not any("CON-01" in r for r in gate["reasons"]), gate
    uitkomst = workflow.approve(
        rec.id,
        "synthetische-expert",
        user_role="reviewer",
        notes="",
        expected_version=vers.version_number,
    )
    assert uitkomst.success is True, uitkomst.error_message


def test_beoordeling_vervalt_na_tekstwijziging(repo, sessie):
    rec = _record(repo)
    SessionStateManager.set_value("selected_review_definition", rec)
    m = _mock_st("necessary", "Exclusieve uitgever.", True)
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        ExpertReviewTab(repo)._render_contextcontract(rec)
    assert repo.update_definitie(rec.id, {"definitie": TEKST + " aan leden"})

    gewijzigd = repo.get_definitie(rec.id)
    m2 = _mock_st("necessary", "", False)
    with (
        patch("ui.components.expert_review_tab.st", m2),
        patch("ui.components.validation_view.st", m2),
    ):
        ExpertReviewTab(repo)._render_contextcontract(gewijzigd)
    assert "Nog te beoordelen" in _teksten(m2)
