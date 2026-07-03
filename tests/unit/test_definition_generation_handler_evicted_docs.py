"""Tests voor DEF-514 review-fix: geselecteerd-maar-evicted documenten.

Een geselecteerd document dat uit de begrensde documentcache is geëvict
mag niet stil uit de generatie-context vallen: de gebruiker krijgt een
waarschuwing en de generatie gaat door met de resterende documenten.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]


def _make_handler() -> DefinitionGenerationHandler:
    return DefinitionGenerationHandler(
        checker=MagicMock(), definition_service=MagicMock(), repository=MagicMock()
    )


def _make_sm(selected: list[str]) -> MagicMock:
    sm = MagicMock()
    sm.get_value.return_value = selected
    return sm


class TestEvictedDocumentSelection:
    def test_evicted_selection_warns_and_continues_with_rest(self, caplog):
        """Evicted ID -> st.warning + logger.warning; rest blijft meedoen."""
        handler = _make_handler()
        st_mock = MagicMock()
        processor = MagicMock()
        # doc-evicted is uit de cache; doc-aanwezig bestaat nog
        processor.get_document_by_id.side_effect = lambda doc_id: (
            None if doc_id == "doc-evicted" else MagicMock()
        )
        processor.get_aggregated_context.return_value = {
            "document_count": 1,
            "total_text_length": 100,
        }

        with (
            patch(
                "ui.handlers.definition_generation_handler.get_document_processor",
                return_value=processor,
            ),
            caplog.at_level(logging.WARNING),
        ):
            result = handler._get_document_context(
                _st=st_mock, _sm=_make_sm(["doc-evicted", "doc-aanwezig"])
            )

        # Generatie gaat door met de resterende documenten
        assert result is not None
        assert result["document_count"] == 1
        processor.get_aggregated_context.assert_called_once_with(["doc-aanwezig"])

        # Gebruiker en log worden expliciet gewaarschuwd
        st_mock.warning.assert_called_once()
        assert "doc-evicted" in st_mock.warning.call_args[0][0]
        assert "niet meer beschikbaar" in st_mock.warning.call_args[0][0]
        assert any(
            "doc-evicted" in rec.message and rec.levelno == logging.WARNING
            for rec in caplog.records
        )

    def test_all_selected_docs_evicted_returns_none_with_warnings(self):
        """Alle selecties geëvict -> None (geen aggregatie-call), wel warnings."""
        handler = _make_handler()
        st_mock = MagicMock()
        processor = MagicMock()
        processor.get_document_by_id.return_value = None

        with patch(
            "ui.handlers.definition_generation_handler.get_document_processor",
            return_value=processor,
        ):
            result = handler._get_document_context(
                _st=st_mock, _sm=_make_sm(["doc-a", "doc-b"])
            )

        assert result is None
        processor.get_aggregated_context.assert_not_called()
        assert st_mock.warning.call_count == 2

    def test_no_warning_when_all_selected_docs_available(self):
        """Regressie: geen warnings als alle geselecteerde docs nog bestaan."""
        handler = _make_handler()
        st_mock = MagicMock()
        processor = MagicMock()
        processor.get_document_by_id.return_value = MagicMock()
        processor.get_aggregated_context.return_value = {"document_count": 2}

        with patch(
            "ui.handlers.definition_generation_handler.get_document_processor",
            return_value=processor,
        ):
            result = handler._get_document_context(
                _st=st_mock, _sm=_make_sm(["doc-a", "doc-b"])
            )

        assert result == {"document_count": 2}
        st_mock.warning.assert_not_called()
        processor.get_aggregated_context.assert_called_once_with(["doc-a", "doc-b"])
