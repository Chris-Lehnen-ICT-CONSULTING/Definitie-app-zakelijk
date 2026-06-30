"""Tests voor auto-save feedback (DEF-469, #5).

`auto_save_draft` swallowde elke DB-fout (return False), waardoor de service-laag
een echte fout niet van "uitgeschakeld" kon onderscheiden en de UI niets toonde —
de gebruiker dacht dat zijn concept was opgeslagen. De fix:
- repo `auto_save_draft` raiset bij een DB-fout (niet langer stil False);
- service `auto_save` geeft een expliciete `AutoSaveResult` terug
  (SAVED / DISABLED / FAILED).
"""

from __future__ import annotations

import sqlite3
from unittest.mock import Mock

import pytest

from services.definition_edit_service import AutoSaveResult, DefinitionEditService
from services.exceptions import RepositoryError

pytestmark = [pytest.mark.unit]


def _service() -> DefinitionEditService:
    svc = DefinitionEditService.__new__(DefinitionEditService)
    svc.auto_save_enabled = True
    svc.repository = Mock()
    return svc


# --------------------------------------------------------------------------- #
# repo-laag: auto_save_draft raiset i.p.v. stil False
# --------------------------------------------------------------------------- #
def test_auto_save_draft_reraises_on_db_error():
    from services.definition_edit_repository import DefinitionEditRepository

    repo = DefinitionEditRepository.__new__(DefinitionEditRepository)
    repo._get_connection = Mock(side_effect=sqlite3.OperationalError("db kapot"))

    with pytest.raises(RepositoryError):
        repo.auto_save_draft(1, {"begrip": "x"})


# --------------------------------------------------------------------------- #
# service-laag: AutoSaveResult
# --------------------------------------------------------------------------- #
def test_auto_save_returns_saved_on_success():
    svc = _service()
    svc.repository.auto_save_draft.return_value = True

    assert svc.auto_save(1, {"begrip": "x"}) is AutoSaveResult.SAVED


def test_auto_save_returns_disabled_when_off():
    svc = _service()
    svc.auto_save_enabled = False

    assert svc.auto_save(1, {"begrip": "x"}) is AutoSaveResult.DISABLED
    svc.repository.auto_save_draft.assert_not_called()


def test_auto_save_returns_failed_on_repository_error():
    svc = _service()
    svc.repository.auto_save_draft.side_effect = RepositoryError("auto_save_draft")

    assert svc.auto_save(1, {"begrip": "x"}) is AutoSaveResult.FAILED
