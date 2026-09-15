"""DEF-622 (B-09): de drie bestaande keuzes bij een gevonden definitie.

Gebruik Deze, Bewerk en Genereer Nieuw blijven behouden én doen wat ze
beloven. Vóór DEF-622 zette "Gebruik Deze" alleen een sessiesleutel die
niets las, en liet "Genereer Nieuw" `force_duplicate` zonder reden in de
generatie-opties achter — ook voor de volgende, ongerelateerde generatie.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from ui.components.duplicate_check_renderer import DuplicateCheckRenderer
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]


def _record(definitie_id: int = 7) -> DefinitieRecord:
    return DefinitieRecord(
        id=definitie_id,
        begrip="keurmerk",
        definitie="kwaliteitsmerk voor gecontroleerde producten",
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        juridische_context='["privaatrecht"]',
        wettelijke_basis='["Regeling Z"]',
        status=DefinitieStatus.ESTABLISHED.value,
        created_at=datetime(2026, 9, 1, tzinfo=UTC),
    )


@pytest.fixture
def sessie(monkeypatch):
    """Echte SessionStateManager op een verse dict-sessie."""
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    SessionStateManager.set_value("generation_options", {})
    SessionStateManager.set_value("last_check_result", SimpleNamespace(action="x"))
    return st.session_state


@pytest.fixture
def mock_st():
    with patch("ui.components.duplicate_check_renderer.st") as m:
        m.columns.side_effect = lambda spec: [
            MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))
        ]
        yield m


def _markdown_tekst(mock_st: MagicMock) -> str:
    return "\n".join(str(c.args[0]) for c in mock_st.markdown.call_args_list if c.args)


class TestGebruikDeze:
    def test_kiest_het_record_en_vervangt_de_duplicaatmelding(self, sessie, mock_st):
        record = _record()
        DuplicateCheckRenderer()._use_existing_definition(record)
        assert SessionStateManager.get_value("selected_definition") is record
        # De keuze vervangt de melding; anders blijven beide naast elkaar staan
        # en is niet zichtbaar dat er gekozen is.
        assert SessionStateManager.get_value("last_check_result") is None

    def test_gekozen_record_wordt_zichtbaar_getoond(self, sessie, mock_st):
        record = _record()
        DuplicateCheckRenderer().render_selected_definition(record)
        tekst = _markdown_tekst(mock_st)
        assert "kwaliteitsmerk voor gecontroleerde producten" in tekst
        assert "Stichting Zilver" in tekst
        assert "established" in tekst
        assert "ID: 7" in tekst


class TestBewerk:
    def test_opent_het_bewerkpad_met_dit_record(self, sessie, mock_st):
        record = _record(11)
        DuplicateCheckRenderer()._edit_existing_definition(record)
        assert SessionStateManager.get_value("editing_definition_id") == 11
        assert SessionStateManager.get_value("active_tab") == "edit"
        mock_st.rerun.assert_called_once()


class TestGenereerNieuw:
    def test_zonder_reden_wordt_niets_geforceerd(self, sessie, mock_st):
        DuplicateCheckRenderer()._trigger_new_generation(reden="   ")
        opties = SessionStateManager.get_value("generation_options")
        assert not opties.get("force_generate")
        assert not opties.get("force_duplicate")
        assert not SessionStateManager.get_value("trigger_auto_generation")
        mock_st.rerun.assert_not_called()
        assert mock_st.warning.called or mock_st.error.called

    def test_met_reden_start_een_nieuwe_generatie_met_die_reden(self, sessie, mock_st):
        DuplicateCheckRenderer()._trigger_new_generation(
            reden="Bestaande definitie dekt de nieuwe regeling niet."
        )
        opties = SessionStateManager.get_value("generation_options")
        assert opties["force_generate"] is True
        assert opties["force_duplicate"] is True
        assert (
            opties["force_duplicate_reason"]
            == "Bestaande definitie dekt de nieuwe regeling niet."
        )
        assert SessionStateManager.get_value("trigger_auto_generation") is True
        assert SessionStateManager.get_value("selected_definition") is None
        mock_st.rerun.assert_called_once()


class TestForceVlagPlaktNiet:
    """Na de geforceerde generatie zijn de force-opties weg — ook bij een fout."""

    @staticmethod
    def _handler(service: Any):
        from ui.handlers.definition_generation_handler import (
            DefinitionGenerationHandler,
        )

        return DefinitionGenerationHandler(
            checker=MagicMock(), definition_service=service, repository=MagicMock()
        )

    @staticmethod
    def _fake_st() -> MagicMock:
        fake = MagicMock()
        fake.spinner.return_value.__enter__ = MagicMock()
        fake.spinner.return_value.__exit__ = MagicMock(return_value=False)
        return fake

    @staticmethod
    def _sessie_met_force():
        SessionStateManager.set_value(
            "generation_options",
            {
                "force_generate": True,
                "force_duplicate": True,
                "force_duplicate_reason": "synthetische reden",
            },
        )
        SessionStateManager.set_value("determined_category", "type")
        SessionStateManager.set_value("selected_documents", [])

    def _draai(self, service: Any) -> None:
        with patch(
            "ui.helpers.async_bridge.run_async",
            side_effect=lambda coro, timeout=None: _sluit(coro),
        ):
            self._handler(service).handle_definition_generation(
                "keurmerk",
                {"organisatorische_context": ["Stichting Zilver"]},
                _st=self._fake_st(),
                _sm=SessionStateManager,
            )

    def test_na_geslaagde_generatie(self, sessie):
        self._sessie_met_force()
        service = MagicMock()
        service.generate_definition = MagicMock(return_value=_coro({"success": True}))
        service.to_ui_response.return_value = {
            "success": True,
            "saved_definition_id": 99,
            "definitie_gecorrigeerd": "tekst",
        }
        self._draai(service)
        opties = SessionStateManager.get_value("generation_options")
        assert "force_generate" not in opties
        assert "force_duplicate" not in opties
        assert "force_duplicate_reason" not in opties
        # En de reden is wél meegereisd naar de service.
        aanroep = service.generate_definition.call_args.kwargs
        assert aanroep["options"]["force_duplicate_reason"] == "synthetische reden"

    def test_na_mislukte_generatie(self, sessie):
        self._sessie_met_force()
        service = MagicMock()
        service.generate_definition = MagicMock(
            side_effect=RuntimeError("synthetische storing")
        )
        self._draai(service)
        opties = SessionStateManager.get_value("generation_options")
        assert "force_generate" not in opties
        assert "force_duplicate" not in opties
        assert "force_duplicate_reason" not in opties

    def test_na_geweigerd_begrip(self, sessie):
        """Reviewbevinding: de vroege afwijzing van een ongeldig begrip liet
        de force-opties staan en raakte zo de volgende, geldige aanvraag."""
        self._sessie_met_force()
        service = MagicMock()
        self._handler(service).handle_definition_generation(
            "12345",  # geen letter: afgewezen vóór generatie
            {"organisatorische_context": ["Stichting Zilver"]},
            _st=self._fake_st(),
            _sm=SessionStateManager,
        )
        service.generate_definition.assert_not_called()
        opties = SessionStateManager.get_value("generation_options")
        assert "force_generate" not in opties
        assert "force_duplicate" not in opties
        assert "force_duplicate_reason" not in opties


async def _coro(waarde: Any) -> Any:
    return waarde


def _sluit(coro: Any) -> Any:
    """Voer een coroutine synchroon uit (vervanger van run_async in tests)."""
    import asyncio

    return asyncio.run(coro) if asyncio.iscoroutine(coro) else coro
