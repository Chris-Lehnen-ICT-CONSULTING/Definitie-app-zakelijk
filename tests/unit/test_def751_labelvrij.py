"""DEF-751 B2 (commit 2) — labelvrije keten na schemaversie 4.

Een definitie zonder categorielabel wordt als NULL opgeslagen; nergens in de
actieve keten (handler → duplicaatvoorcontrole → service → prompt → opslag →
import → readback) valt een ontbrekend label terug op een fictief "proces".
Ongeldige waarden blijven zichtbaar geweigerd (niet als NULL genormaliseerd).
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.definition_import_service import DefinitionImportService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from ui.components.tabs.import_export_beheer.csv_importer import CSVImporter
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]

CONTEXT = {"organisatorische_context": [], "wettelijke_basis": ["Regeling Z"]}
_CSV_MODULE = "ui.components.tabs.import_export_beheer.csv_importer"


# ------------------------------------------------------------------ opslag


def test_definitie_zonder_label_wordt_null_zonder_default(tmp_path):
    db_path = str(tmp_path / "labelvrij.db")
    did = DefinitionRepository(db_path).save(
        Definition(
            begrip="keurmerk",
            definitie="Een synthetische definitie.",
            categorie=None,
            organisatorische_context=["DJI"],
            metadata={"status": "draft"},
        )
    )
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.categorie is None
    assert record.get_category_choice() is None
    assert record.get_category_choice_status()["status"] == "absent"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT categorie FROM definities WHERE id = ?", (did,)
        ).fetchone() == (None,)
    opnieuw = DefinitionRepository(db_path).get(did)
    assert opnieuw.categorie is None
    assert opnieuw.metadata["category_choice_status"]["status"] == "absent"


def test_record_zonder_label_via_db_laag(tmp_path):
    repo = DefinitieRepository(str(tmp_path / "db.db"))
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="zonder", definitie="kern", organisatorische_context="[]"
        )
    )
    assert repo.get_definitie(did).categorie is None
    with pytest.raises(sqlite3.IntegrityError):
        repo.create_definitie(
            DefinitieRecord(begrip="fout", definitie="kern", categorie="Type")
        )


# ------------------------------------------------------------------ handler


def test_handler_genereert_zonder_label_als_er_geen_keuze_en_geen_voorstel_is():
    """Alleen wettelijke basis als context (CON-01-conform): er is geen
    voorstel (classificatie draait alleen op org/jur) en geen override. De
    generatie loopt door met categorie None — geen blokkade, geen PROCES."""
    handler = DefinitionGenerationHandler(
        checker=MagicMock(), definition_service=MagicMock(), repository=MagicMock()
    )
    # Een geslaagd resultaat: de test borgt de *gate* (geen blokkade vóór de
    # generatie). Sinds DEF-751 stap 2 meldt de handler een niet-geslaagde
    # generatie eerlijk via st.error, dus een fake `success: False` zou hier
    # ten onrechte als blokkade lezen.
    handler.definition_service.to_ui_response.return_value = {"success": True}
    handler.checker.check_before_generation.return_value = MagicMock(action="PROCEED")
    sessie = {"generation_options": {"model": "x"}}
    sm = MagicMock()
    sm.get_value = Mock(side_effect=lambda k, d=None: sessie.get(k, d))
    mock_st = MagicMock()
    mock_st.error = Mock()

    from integration.definitie_checker import CheckAction

    handler.checker.check_before_generation.return_value = MagicMock(
        action=CheckAction.PROCEED
    )
    with patch("ui.helpers.async_bridge.run_async", lambda coro, **kw: coro):
        handler.handle_definition_generation("keurmerk", CONTEXT, _st=mock_st, _sm=sm)

    mock_st.error.assert_not_called()
    assert handler.checker.check_before_generation.call_args.kwargs["categorie"] is None
    aanroep = handler.definition_service.generate_definition.call_args
    assert aanroep.kwargs["categorie"] is None
    assert "category_choice" not in aanroep.kwargs["options"]


# ------------------------------------------------------------------ import


@pytest.fixture
def csv_repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "import.db"))


def _importeer(repo: DefinitieRepository, rijen: list[dict]) -> MagicMock:
    m = MagicMock()
    with patch(f"{_CSV_MODULE}.st", m):
        CSVImporter(repo)._process_import(
            pd.DataFrame(rijen), skip_duplicates=False, auto_validate=False
        )
    return m


def test_csv_zonder_categorie_wordt_labelvrij_bewaard_met_importherkomst(csv_repo):
    m = _importeer(
        csv_repo,
        [
            {
                "begrip": "zonder",
                "definitie": "kern zonder categorie",
                "context": "DJI",
            },
            {
                "begrip": "hoofdletter",
                "definitie": "kern",
                "context": "DJI",
                "categorie": "Type",
            },
            {
                "begrip": "met",
                "definitie": "kern",
                "context": "DJI",
                "categorie": "ENT",
            },
        ],
    )
    fouten = [str(c.args[0]) for c in m.error.call_args_list]
    assert len(fouten) == 1 and "'Type'" in fouten[0]  # ongeldig blijft geweigerd
    assert "2 geïmporteerd" in str(m.success.call_args[0][0])
    zonder = csv_repo.search_definities(query="zonder")[0]
    assert zonder.categorie is None
    assert zonder.get_category_choice()["origin"] == "import"
    assert zonder.get_category_choice_status()["status"] == "imported_missing"
    met = csv_repo.search_definities(query="met")[0]
    assert met.categorie == "ENT"
    assert met.get_category_choice_status()["status"] == "imported"


def test_importservice_normaliseert_niet_meer_naar_type():
    svc = DefinitionImportService(repository=Mock(), validation_orchestrator=Mock())
    zonder = svc._payload_to_definition(
        {"begrip": "b", "definitie": "d", "organisatorische_context": ["DJI"]}
    )
    assert zonder.categorie is None
    assert (
        svc._payload_to_definition(
            {"begrip": "b", "definitie": "d", "categorie": "ENT"}
        ).categorie
        == "ENT"
    )
    for ongeldig in ("Type", "entiteit", "object"):
        with pytest.raises(ValueError, match="opslagwaarde"):
            svc._payload_to_definition(
                {"begrip": "b", "definitie": "d", "categorie": ongeldig}
            )
