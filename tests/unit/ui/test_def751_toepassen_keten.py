"""DEF-751 B2 — de echte Toepassen-keten: handler → renderer → workflow → SQLite.

Herreviewbevinding 3: de handler leverde `saved_record=None`, de renderer
stuurde `definition_id=None`/`expected_version=None` en de workflow meldde
succes zonder databasewijziging. Nu draagt het generatieresultaat het
werkelijk opgeslagen record (id én versie), de workflow schrijft via het
keuzecommando met die versie, en succes wordt pas gemeld na bevestigde
opslag. Een gelijktijdige wijziging tussen tonen en Toepassen is een
conflict — geen verse versie ophalen om het conflict te omzeilen.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from database.definitie_repository import DefinitieRepository
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.unit.database.test_def751_review2_reproducties import (
    CONTEXT,
    _handler,
    _sm,
    generatieresultaat,
)
from ui.components.category_renderer import CategoryRenderer

pytestmark = [pytest.mark.unit]


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "keten.db")


def _genereer(db_path: str) -> dict[str, Any]:
    handler, _service = _handler(db_path)
    sm = _sm(determined_category="proces", category_reasoning="r")
    with patch(
        "ui.helpers.async_bridge.run_async",
        lambda coro, **kw: __import__("asyncio").run(coro),
    ):
        handler.handle_definition_generation(
            "keurmerk", CONTEXT, _st=MagicMock(), _sm=sm
        )
    return generatieresultaat(sm)


def _renderer() -> CategoryRenderer:
    renderer = CategoryRenderer.__new__(CategoryRenderer)
    from services.workflow_service import WorkflowService

    renderer.workflow_service = WorkflowService()
    return renderer


def test_toepassen_schrijft_via_het_commando_met_de_getoonde_versie(db_path):
    resultaat = _genereer(db_path)
    did = resultaat["saved_definition_id"]
    assert resultaat["saved_record"] is not None
    assert resultaat["saved_record"].id == did

    m = MagicMock()
    with (
        patch("ui.components.category_renderer.st", m),
        patch(
            "database.definitie_repository.get_definitie_repository",
            return_value=DefinitieRepository(db_path),
        ),
    ):
        _renderer()._update_category("resultaat", resultaat)

    assert m.success.called, m.error.call_args_list
    assert not m.error.called
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.categorie == "resultaat" and record.version_number == 2
    keuze = record.get_category_choice()
    assert keuze["origin"] == "manual" and keuze["actor"] is None
    assert record.get_category_choice_status()["status"] == "manual_unattributed"
    assert record.get_category_choice_history()[0]["event"]["origin"] == "model"


def test_toepassen_na_gelijktijdige_wijziging_is_een_conflict_zonder_succes(
    db_path,
):
    resultaat = _genereer(db_path)
    did = resultaat["saved_definition_id"]
    # Tussen tonen en Toepassen wijzigt een ander de term (versie 1 → 2).
    assert DefinitieRepository(db_path).update_definitie(
        did, {"begrip": "vergunning"}, "ander"
    )

    m = MagicMock()
    with (
        patch("ui.components.category_renderer.st", m),
        patch(
            "database.definitie_repository.get_definitie_repository",
            return_value=DefinitieRepository(db_path),
        ),
    ):
        _renderer()._update_category("resultaat", resultaat)

    assert m.error.called and not m.success.called
    assert "versieconflict" in str(m.error.call_args[0][0]).lower()
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.begrip == "vergunning" and record.categorie == "proces"
    assert record.version_number == 2
    assert record.get_category_choice()["origin"] == "model"


def test_toepassen_zonder_opgeslagen_record_meldt_geen_succes(db_path):
    """Zonder opgeslagen record (generatie niet opgeslagen) is er niets om
    op toe te passen: geen succeslabel, geen sessie-override."""
    resultaat = {
        "begrip": "keurmerk",
        "determined_category": "proces",
        "saved_record": None,
        "saved_definition_id": None,
        "agent_result": {"definitie_gecorrigeerd": "x"},
    }
    m = MagicMock()
    sm_set = Mock()
    with (
        patch("ui.components.category_renderer.st", m),
        patch("ui.components.category_renderer.SessionStateManager.set_value", sm_set),
    ):
        _renderer()._update_category("resultaat", resultaat)
    assert m.error.called and not m.success.called
    assert not any(
        c.args[0] == "manual_ontological_category" for c in sm_set.call_args_list
    )
    assert resultaat["determined_category"] == "proces"


def test_definitie_object_in_tmp_db_is_echt(db_path):
    """Sanity: de fake service slaat werkelijk op via de servicelaag."""
    resultaat = _genereer(db_path)
    geladen = DefinitionRepository(db_path).get(resultaat["saved_definition_id"])
    assert isinstance(geladen, Definition) and geladen.begrip == "keurmerk"
