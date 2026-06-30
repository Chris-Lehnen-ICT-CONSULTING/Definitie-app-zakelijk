"""Tests voor stille-failure-fix in de repository/service-laag (DEF-469).

Deelstap 1 — duplicaat-detectie (data-integriteit):
`DefinitionRepository.find_duplicates` retourneerde bij élke exception een lege
lijst. De aanroeper kon "fout" niet van "geen duplicaten" onderscheiden, waardoor
een DB-fout een duplicaat liet passeren als uniek record. De fix laat de fout
als `RepositoryError` propageren; de import-service breekt dan fail-closed af
i.p.v. een mogelijk dubbel record op te slaan.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import AsyncMock, Mock

import pytest

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
    repo.save.assert_not_called()
