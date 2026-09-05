"""Tests voor stille-failure-fix in de repository/service-laag (DEF-469).

Deelstap 1 — duplicaat-detectie (data-integriteit):
`DefinitionRepository.find_duplicates` retourneerde bij élke exception een lege
lijst. De aanroeper kon "fout" niet van "geen duplicaten" onderscheiden, waardoor
een DB-fout een duplicaat liet passeren als uniek record. De fix laat de fout
als `RepositoryError` propageren; de import-service breekt dan fail-closed af
i.p.v. een mogelijk dubbel record op te slaan.

Deelstap 3 — actieve callers van `save()` op een echte tijdelijke database: een
niet-bevestigde update geeft geen succeslog (orchestrator) en geen succes-ID of
historyvervolg (editroute). Alleen niet-opslagafhankelijkheden zijn gestubd.
"""

from __future__ import annotations

import logging
import sqlite3
from unittest.mock import AsyncMock, Mock

import pytest

from database.definitie_repository import DefinitieRecord
from services.definition_repository import DefinitionRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]


def _repo_with_failing_legacy() -> DefinitionRepository:
    """DefinitionRepository zonder DB, met een legacy_repo dat een DB-fout gooit."""
    repo = DefinitionRepository.__new__(DefinitionRepository)
    repo.legacy_repo = Mock()
    repo.legacy_repo.find_duplicates.side_effect = sqlite3.OperationalError(
        "database is locked"
    )
    return repo


def test_find_duplicates_reraises_on_db_error():
    """Een DB-fout in duplicaat-detectie wordt een RepositoryError, geen lege lijst."""
    repo = _repo_with_failing_legacy()

    with pytest.raises(RepositoryError):
        repo.find_duplicates(Definition(begrip="Term", definitie="Een definitie"))


def test_find_duplicates_returns_list_on_success():
    """Bij succes blijft find_duplicates een (lege) lijst teruggeven."""
    repo = DefinitionRepository.__new__(DefinitionRepository)
    repo.legacy_repo = Mock()
    repo.legacy_repo.find_duplicates.return_value = []

    result = repo.find_duplicates(Definition(begrip="Term", definitie="Een definitie"))

    assert result == []


async def test_import_single_fails_closed_when_duplicate_check_errors():
    """Faalt de duplicaatcontrole, dan wordt NIET opgeslagen (fail-closed)."""
    from services.definition_import_service import DefinitionImportService

    repo = Mock()
    repo.find_duplicates.side_effect = RepositoryError("find_duplicates", "Term")
    validator = Mock()
    validator.validate_definition = AsyncMock(return_value={"is_acceptable": True})

    svc = DefinitionImportService(repository=repo, validation_orchestrator=validator)
    result = await svc.import_single({"begrip": "Term", "definitie": "Een definitie"})

    assert result.success is False
    assert result.error
    # De foutmelding is generiek — geen rauwe DB-/exception-details naar de UI.
    assert "sqlite" not in result.error.lower()
    assert "find_duplicates" not in result.error
    repo.save.assert_not_called()


async def test_orchestrator_propagates_unconfirmed_save_without_success_log(
    tmp_path, caplog
):
    """Een niet-bevestigde update propageert typed; geen 'Successfully saved'."""
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    orchestrator = DefinitionOrchestratorV2(
        ai_service=Mock(),
        cleaning_service=Mock(),
        repository=DefinitionRepository(str(tmp_path / "orchestrator.db")),
    )
    definition = Definition(id=987654, begrip="Term", definitie="Een definitie")

    with caplog.at_level(logging.INFO), pytest.raises(RepositoryError) as exc:
        await orchestrator._safe_save_definition(definition)

    assert exc.value.operation == "save_update"
    assert "Successfully saved" not in caplog.text


def _definitie_tekst(db_path: str, definitie_id: int) -> str | None:
    """Onafhankelijke lezer op een eigen connectie: alleen gecommitte data."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT definitie FROM definities WHERE id = ?", (definitie_id,)
        ).fetchone()
    finally:
        conn.close()
    return None if row is None else row[0]


@pytest.mark.parametrize(
    ("verstoring", "na_afloop"),
    [
        ("DELETE FROM definities WHERE id = {id}", None),
        (
            (
                "CREATE TRIGGER weiger BEFORE UPDATE ON definities BEGIN "
                "SELECT RAISE(ABORT, 'UPDATE definities; {pad}'); END"
            ),
            "Origineel",
        ),
    ],
    ids=["rij-verdwenen", "update-trigger-abort"],
)
def test_edit_route_reports_failure_without_history(tmp_path, verstoring, na_afloop):
    """Verdwijnt de rij of faalt de UPDATE tussen lezen en opslaan, dan geen
    succes-ID, geen history en geen ruwe SQL-/padtekst in de fout (Codex-review)."""
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import DefinitionEditService

    repo = DefinitionEditRepository(str(tmp_path / "edit.db"))
    definitie_id = repo.legacy_repo.create_definitie(
        DefinitieRecord(begrip="Term", definitie="Origineel", categorie="proces")
    )
    svc = DefinitionEditService(repository=repo, validation_service=Mock())

    def verstoor_tijdens_validatie(_definition):
        conn = sqlite3.connect(repo.db_path)
        with conn:
            conn.execute(verstoring.format(id=definitie_id, pad=repo.db_path))
        conn.close()

    svc._validate_definition = verstoor_tijdens_validatie
    repo._add_history_entry = Mock()

    result = svc.save_definition(
        definitie_id, {"definitie": "Nieuw"}, user="tester", reason="bewerking"
    )

    assert result["success"] is False
    assert "definition_id" not in result
    assert "sqlite" not in result["error"].lower()
    assert str(tmp_path) not in result["error"]
    assert "UPDATE definities" not in result["error"]
    repo._add_history_entry.assert_not_called()
    assert _definitie_tekst(repo.db_path, definitie_id) == na_afloop
