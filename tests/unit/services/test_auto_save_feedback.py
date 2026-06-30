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


def test_auto_save_saved_ignores_repository_return_value():
    """SAVED hangt op 'geen exception', niet op de bool-return van de repo."""
    svc = _service()
    svc.repository.auto_save_draft.return_value = False  # mag genegeerd worden

    assert svc.auto_save(1, {"begrip": "x"}) is AutoSaveResult.SAVED


def test_auto_save_sets_timestamp_in_content():
    """De service zet een auto_save_timestamp op de content."""
    svc = _service()
    svc.repository.auto_save_draft.return_value = True
    content: dict = {"begrip": "x"}

    svc.auto_save(1, content)

    assert "auto_save_timestamp" in content


# --------------------------------------------------------------------------- #
# UI-laag: _perform_auto_save reageert op de drie uitkomsten
# --------------------------------------------------------------------------- #
def _make_tab(result: AutoSaveResult):
    from ui.components import definition_edit_tab as mod

    tab = mod.DefinitionEditTab.__new__(mod.DefinitionEditTab)
    tab.edit_service = Mock()
    tab.edit_service.auto_save.return_value = result
    return mod, tab


def _patch_ui(monkeypatch, mod):
    mock_st = Mock()
    mock_ssm = Mock()
    # editing_definition_id moet truthy zijn; overige keys irrelevant.
    mock_ssm.get_value.side_effect = lambda key, *a, **k: (
        1 if key == "editing_definition_id" else "x"
    )
    monkeypatch.setattr(mod, "st", mock_st)
    monkeypatch.setattr(mod, "SessionStateManager", mock_ssm)
    return mock_st, mock_ssm


def test_perform_auto_save_warns_on_failed(monkeypatch):
    mod, tab = _make_tab(AutoSaveResult.FAILED)
    mock_st, mock_ssm = _patch_ui(monkeypatch, mod)

    tab._perform_auto_save()

    mock_st.warning.assert_called_once()
    # last_auto_save niet gezet bij FAILED
    assert all(c.args[0] != "last_auto_save" for c in mock_ssm.set_value.call_args_list)


def test_perform_auto_save_sets_timestamp_on_saved(monkeypatch):
    mod, tab = _make_tab(AutoSaveResult.SAVED)
    mock_st, mock_ssm = _patch_ui(monkeypatch, mod)

    tab._perform_auto_save()

    mock_st.warning.assert_not_called()
    assert any(c.args[0] == "last_auto_save" for c in mock_ssm.set_value.call_args_list)


def test_perform_auto_save_silent_on_disabled(monkeypatch):
    mod, tab = _make_tab(AutoSaveResult.DISABLED)
    mock_st, mock_ssm = _patch_ui(monkeypatch, mod)

    tab._perform_auto_save()

    mock_st.warning.assert_not_called()
    assert all(c.args[0] != "last_auto_save" for c in mock_ssm.set_value.call_args_list)
