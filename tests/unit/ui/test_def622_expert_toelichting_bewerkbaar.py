"""DEF-622 reviewbevinding 3 — bestaande inhoudelijke toelichting blijft bewerkbaar.

Batch 2 scheidde in de expertweergave de definitiezin van een ingebedde
toelichting en bood alleen de zin ter bewerking aan; bij opslaan werd de
oorspronkelijke toelichting teruggezet. Vóór die wijziging was de
samengevoegde kolomtekst (dus ook de toelichting) bewerkbaar — een regressie
(reviewrapport, bevinding 3).

Herstel: de bestaande inhoudelijke toelichting krijgt een eigen bewerkveld
naast de zin (geen nieuw veld voor een CON-01-naamgrond; zonder bestaande
toelichting geen veld); opslaan bedt zin en toelichting opnieuw in volgens de
opslagconventie; de kern (`get_definitie_tekst`) blijft de zin alleen, zodat de
CON-01-toetsing de toelichting niet meeneemt.
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
from database.models import TOELICHTING_SCHEIDING
from ui.components.expert_review_tab import ExpertReviewTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ZIN = "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend."
TOELICHTING = "Stichting Goud verleent een ander merk."
NIEUWE_TOELICHTING = "Stichting Goud verleent het Goudkeurmerk, een ander merk."
NIEUWE_ZIN = "Kwaliteitskeurmerk dat door Stichting Zilver wordt verleend."


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "expert-toelichting.db"))


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    SessionStateManager.set_value("user", "synthetische-expert")
    return st.session_state


def _record(repo: DefinitieRepository, *, definitie: str) -> DefinitieRecord:
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="Zilverkeurmerk",
            definitie=definitie,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.9,
        )
    )
    gelezen = repo.get_definitie(did)
    assert gelezen is not None
    return gelezen


def _mock_st(widgetwaarden: dict[str, str] | None = None) -> MagicMock:
    """Mock-`st` waarvan elke `text_area` de waarde voor zijn eigen key
    teruggeeft (zoals Streamlit dat per widget doet)."""
    m = MagicMock()
    m.columns.side_effect = lambda spec: [
        MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)
    ]
    waarden = widgetwaarden or {}

    def _text_area(_label: str, **kw: Any) -> str:
        return waarden.get(kw["key"], SessionStateManager.get_value(kw["key"], ""))

    m.text_area.side_effect = _text_area
    return m


def _widgets(m: MagicMock) -> dict[str, str]:
    """key → label van elke gerenderde text_area."""
    return {c.kwargs["key"]: c.args[0] for c in m.text_area.call_args_list}


def test_bewerkweergave_biedt_zin_en_toelichting_afzonderlijk_aan(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    m = _mock_st()
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._render_comparison_view(rec)

    widgets = _widgets(m)
    assert f"edit_def_{rec.id}" in widgets
    assert f"edit_toel_{rec.id}" in widgets, widgets
    assert "toelichting" in widgets[f"edit_toel_{rec.id}"].lower()
    # Beginwaarden: de zin en de toelichting elk in hun eigen veld, nooit de
    # samengevoegde kolomtekst.
    assert SessionStateManager.get_value(f"edit_def_{rec.id}") == ZIN
    assert SessionStateManager.get_value(f"edit_toel_{rec.id}") == TOELICHTING
    # Ongewijzigd: niets als bewerkt gemarkeerd.
    assert SessionStateManager.get_value(f"edited_definition_{rec.id}") is None
    assert SessionStateManager.get_value(f"edited_toelichting_{rec.id}") is None


def test_zonder_bestaande_toelichting_geen_toelichtingsveld(repo, sessie):
    rec = _record(repo, definitie=ZIN)
    m = _mock_st()
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._render_comparison_view(rec)

    widgets = _widgets(m)
    assert list(widgets) == [f"edit_def_{rec.id}"], widgets


def test_gewijzigde_toelichting_wordt_gemarkeerd(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    m = _mock_st({f"edit_toel_{rec.id}": NIEUWE_TOELICHTING})
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._render_comparison_view(rec)

    assert (
        SessionStateManager.get_value(f"edited_toelichting_{rec.id}")
        == NIEUWE_TOELICHTING
    )
    assert SessionStateManager.get_value(f"edited_definition_{rec.id}") is None


def test_teruggezette_toelichting_wist_de_bewerkt_markering(repo, sessie):
    """Bewerken en daarna terugzetten naar het origineel: geen achtergebleven
    markering die bij een latere opslag een oude wijziging zou meenemen."""
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    SessionStateManager.set_value(f"edited_toelichting_{rec.id}", NIEUWE_TOELICHTING)
    m = _mock_st({f"edit_toel_{rec.id}": TOELICHTING})
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._render_comparison_view(rec)

    assert SessionStateManager.get_value(f"edited_toelichting_{rec.id}") is None


def test_bewerkte_toelichting_wordt_opgeslagen_bij_ongewijzigde_zin(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    SessionStateManager.set_value(f"edited_toelichting_{rec.id}", NIEUWE_TOELICHTING)
    with patch("ui.components.expert_review_tab.st", _mock_st()):
        ExpertReviewTab(repo)._submit_review(
            rec, "📝 Wijzigingen Vereist", "", "synthetische-expert"
        )

    na = repo.get_definitie(rec.id)
    assert na.definitie == f"{ZIN}{TOELICHTING_SCHEIDING} {NIEUWE_TOELICHTING}"
    # Kern apart: de CON-01-toetsing ziet de naam uit de toelichting niet.
    assert na.get_definitie_tekst() == ZIN
    assert "Stichting Goud" not in na.get_definitie_tekst()


def test_zin_en_toelichting_samen_bewerkt_worden_beide_opgeslagen(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    SessionStateManager.set_value(f"edited_definition_{rec.id}", NIEUWE_ZIN)
    SessionStateManager.set_value(f"edited_toelichting_{rec.id}", NIEUWE_TOELICHTING)
    with patch("ui.components.expert_review_tab.st", _mock_st()):
        ExpertReviewTab(repo)._submit_review(
            rec, "📝 Wijzigingen Vereist", "", "synthetische-expert"
        )

    na = repo.get_definitie(rec.id)
    assert na.definitie == f"{NIEUWE_ZIN}{TOELICHTING_SCHEIDING} {NIEUWE_TOELICHTING}"
    assert na.get_definitie_tekst() == NIEUWE_ZIN


def test_geleegde_toelichting_wordt_verwijderd_en_zin_blijft(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    SessionStateManager.set_value(f"edited_toelichting_{rec.id}", "")
    with patch("ui.components.expert_review_tab.st", _mock_st()):
        ExpertReviewTab(repo)._submit_review(
            rec, "📝 Wijzigingen Vereist", "", "synthetische-expert"
        )

    na = repo.get_definitie(rec.id)
    assert na.definitie == ZIN
    assert na.get_definitie_tekst() == ZIN
