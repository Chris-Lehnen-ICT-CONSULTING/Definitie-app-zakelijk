"""Regressietests voor DEF-502: Expert Review-wachtrij crasht op statusfilter.

De tab gaf kale status-strings ("review", "archived", "established") door aan de
repository-laag met een runtime-no-op `cast("DefinitieStatus", ...)`, terwijl
`definitie_search.py` en `definitie_crud.py` een echte `DefinitieStatus`-enum
verwachten en er `.value` op aanroepen — `AttributeError: 'str' object has no
attribute 'value'` op drie paden: wachtrij laden, review-geschiedenis en
afwijzen. Deze tests draaien tegen een échte repository (temp-DB) zodat ze
falen zodra de tab weer strings doorgeeft.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import DefinitieStatus

pytestmark = [pytest.mark.unit]


class _FakeSessionStateManager:
    """Dict-backed vervanger voor SessionStateManager (geen Streamlit-runtime)."""

    _store: dict[str, Any] = {}

    @classmethod
    def get_value(cls, key: str, default: Any = None) -> Any:
        return cls._store.get(key, default)

    @classmethod
    def set_value(cls, key: str, value: Any) -> None:
        cls._store[key] = value

    @classmethod
    def clear_value(cls, key: str) -> None:
        cls._store.pop(key, None)


def _mock_streamlit(
    *, checkbox: bool = False, status_filter: str = "In review"
) -> MagicMock:
    """Mock van de streamlit-module zoals de tab die gebruikt."""
    st = MagicMock()

    def _selectbox(label: str, options: Any = None, **_kwargs: Any) -> Any:
        if "Status filter" in label:
            return status_filter
        # Overige selectboxen (bv. "Sorteer op"): eerste optie
        return next(iter(options)) if options else None

    st.selectbox.side_effect = _selectbox
    st.text_input.return_value = ""
    st.multiselect.return_value = []
    st.checkbox.return_value = checkbox
    st.button.return_value = False
    st.columns.side_effect = lambda spec, **_kw: [
        MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))
    ]
    return st


@pytest.fixture(autouse=True)
def _reset_fake_session_state():
    """Voorkom order-afhankelijke vervuiling via de class-level _store."""
    _FakeSessionStateManager._store.clear()
    yield
    _FakeSessionStateManager._store.clear()


@pytest.fixture
def repo(tmp_path):
    return DefinitieRepository(str(tmp_path / "def502.db"))


def _maak_record(repo: DefinitieRepository, status: DefinitieStatus) -> int:
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="toetsbegrip",
            definitie="Een begrip waarmee de review-wachtrij wordt getest",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )
    repo.change_status(def_id, status, changed_by="tester")
    return def_id


def _tab(repo: DefinitieRepository):
    from ui.components.expert_review_tab import ExpertReviewTab

    return ExpertReviewTab(repo)


@pytest.mark.parametrize(
    ("filter_label", "record_status"),
    [
        ("In review", DefinitieStatus.REVIEW),
        ("Gearchiveerd", DefinitieStatus.ARCHIVED),
    ],
)
def test_review_wachtrij_laadt_met_statusfilter(repo, filter_label, record_status):
    """Wachtrij per statusfilter: geen foutmelding, record getoond."""
    _maak_record(repo, record_status)
    st = _mock_streamlit(checkbox=False, status_filter=filter_label)  # kaartweergave

    with (
        patch("ui.components.expert_review_tab.st", st),
        patch(
            "ui.components.expert_review_tab.SessionStateManager",
            _FakeSessionStateManager,
        ),
    ):
        _tab(repo)._render_review_queue()

    assert (
        not st.error.called
    ), f"Review-wachtrij gaf een fout: {st.error.call_args_list}"
    markdown_teksten = [str(c.args[0]) for c in st.markdown.call_args_list if c.args]
    assert any(
        "1 definities wachten op review" in t for t in markdown_teksten
    ), f"Wachtrij-telling niet gerenderd; markdown-calls: {markdown_teksten}"


def test_review_geschiedenis_laadt_zonder_statusfout(repo):
    """Geschiedenis (status established): geen foutmelding, record in expander."""
    _maak_record(repo, DefinitieStatus.ESTABLISHED)
    st = _mock_streamlit(checkbox=True)  # "Toon Review Geschiedenis" aangevinkt

    with (
        patch("ui.components.expert_review_tab.st", st),
        patch(
            "ui.components.expert_review_tab.SessionStateManager",
            _FakeSessionStateManager,
        ),
    ):
        _tab(repo)._render_review_history()

    assert (
        not st.error.called
    ), f"Review-geschiedenis gaf een fout: {st.error.call_args_list}"
    assert st.expander.called, "Goedgekeurde definitie niet getoond in geschiedenis"


def test_afwijzen_archiveert_definitie(repo):
    """Afwijzen zet de status daadwerkelijk op archived in de database."""
    def_id = _maak_record(repo, DefinitieStatus.REVIEW)
    definitie = repo.get_definitie(def_id)
    st = _mock_streamlit()

    with (
        patch("ui.components.expert_review_tab.st", st),
        patch(
            "ui.components.expert_review_tab.SessionStateManager",
            _FakeSessionStateManager,
        ),
    ):
        _tab(repo)._submit_review(
            definitie, decision="❌ Afwijzen", comments="niet ok", reviewer="tester"
        )

    record = repo.get_definitie(def_id)
    assert record is not None
    assert (
        record.status == DefinitieStatus.ARCHIVED.value
    ), f"Status is '{record.status}' — afwijzen heeft de definitie niet gearchiveerd"
