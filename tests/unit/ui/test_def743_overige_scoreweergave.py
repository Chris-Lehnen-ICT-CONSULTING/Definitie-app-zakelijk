"""DEF-743 (besluit 3, geen totaalcijfer): resterende kwaliteitscijfers in de UI.

Twee presentatieplekken toonden nog een numeriek kwaliteitstotaal van een
definitie: de bestaande-definitie-kaart bij de duplicaatcontrole (historische
`validation_score` uit het record) en de definitievergelijking na een
categoriewijziging (`validation_score` in het nieuwe resultaat, die bij `None`
zelfs een TypeError gaf). Beide tonen geen cijfer meer; status, categorie,
datum, context, definitietekst, keuzes en redenering blijven. Zoek-/match- en
categorie-classificatiescores zijn aparte feitelijke metrieken en blijven
buiten deze test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from integration.definitie_checker import CheckAction, DefinitieCheckResult
from ui.components.category_renderer import CategoryRenderer
from ui.components.duplicate_check_renderer import DuplicateCheckRenderer
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]


def _record(validation_score: float | None) -> DefinitieRecord:
    return DefinitieRecord(
        id=7,
        begrip="keurmerk",
        definitie="kwaliteitsmerk voor gecontroleerde producten",
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        status=DefinitieStatus.ESTABLISHED.value,
        validation_score=validation_score,
        created_at=datetime(2026, 9, 1, tzinfo=UTC),
    )


def _kolommen(spec):
    return [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]


def _markdown_tekst(mock_st: MagicMock) -> str:
    return "\n".join(str(c.args[0]) for c in mock_st.markdown.call_args_list if c.args)


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    SessionStateManager.set_value("generation_options", {})
    return st.session_state


@pytest.fixture
def dup_st():
    with patch("ui.components.duplicate_check_renderer.st") as m:
        m.columns.side_effect = _kolommen
        m.button.return_value = False
        yield m


@pytest.fixture
def cat_st():
    with patch("ui.components.category_renderer.st") as m:
        m.columns.side_effect = _kolommen
        m.button.return_value = False
        yield m


class TestBestaandeDefinitieBijDuplicaatcontrole:
    @pytest.mark.parametrize(
        "score", [0.85, 0.0, None], ids=["positief", "nul", "geen"]
    )
    def test_toont_geen_kwaliteitstotaal_maar_wel_de_rest(self, sessie, dup_st, score):
        record = _record(score)
        DuplicateCheckRenderer().render_check_results(
            DefinitieCheckResult(
                action=CheckAction.USE_EXISTING,
                existing_definitie=record,
                message="Bestaande definitie gevonden",
                confidence=0.9,
            )
        )
        tekst = _markdown_tekst(dup_st)

        assert "**Score:**" not in tekst
        assert "0.85" not in tekst
        assert "Kwaliteit" not in tekst
        # Wat wél blijft: definitie, context, status, categorie, datum.
        assert "kwaliteitsmerk voor gecontroleerde producten" in tekst
        assert "Stichting Zilver" in tekst
        assert "`established`" in tekst
        assert "`type`" in tekst
        assert "2026-09-01" in tekst
        # De drie keuzes en het redenveld blijven aanwezig.
        labels = [c.args[0] for c in dup_st.button.call_args_list]
        assert any("Gebruik Deze" in label for label in labels)
        assert any("Bewerk" in label for label in labels)
        assert any("Genereer Nieuw" in label for label in labels)
        assert dup_st.text_input.called

    def test_gekozen_record_toont_ook_geen_cijfer(self, sessie, dup_st):
        DuplicateCheckRenderer().render_selected_definition(_record(0.85))
        tekst = _markdown_tekst(dup_st)
        assert "0.85" not in tekst
        assert "Score" not in tekst
        assert "`established`" in tekst


class TestDefinitievergelijkingNaCategoriewijziging:
    @pytest.mark.parametrize(
        "nieuw",
        [
            {"definitie_gecorrigeerd": "nieuwe tekst", "validation_score": 0.91},
            {"definitie_gecorrigeerd": "nieuwe tekst", "validation_score": None},
            {"definitie": "nieuwe tekst"},
        ],
        ids=["positief", "geen-oordeel", "zonder-veld"],
    )
    def test_toont_beide_definities_zonder_kwaliteitscijfer(self, cat_st, nieuw):
        CategoryRenderer().render_definition_comparison(
            old_definition="oude tekst",
            new_result=nieuw,
            old_category="proces",
            new_category="type",
        )
        tekst = _markdown_tekst(cat_st)
        assert "Kwaliteitsscore" not in tekst
        assert "0.91" not in tekst
        assert "Oude Definitie" in tekst
        assert "Nieuwe Definitie" in tekst
        cat_st.info.assert_called_once_with("oude tekst")
        cat_st.success.assert_called_once_with("nieuwe tekst")

    def test_object_resultaat_zonder_dict(self, cat_st):
        class _Resultaat:
            final_definitie = "object tekst"
            validation_score = 0.5

        CategoryRenderer().render_definition_comparison(
            "oude tekst", _Resultaat(), "type", "proces"
        )
        assert "0.5" not in _markdown_tekst(cat_st)
        cat_st.success.assert_called_once_with("object tekst")
