"""Tests voor DEF-469 deelstap 2b — resterende stille failures zichtbaar maken.

- search_with_filters: re-raiset i.p.v. stil [] (false-negative maskeert DB-fout).
- approve(): ketenpartners gaan mee in de atomaire vaststelling (DEF-482);
  een fout daarin betekent niet vastgesteld, geen waarschuwing.
- _get_policy(): logt nu expliciet bij een loader-fout i.p.v. stille `pass`.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, Mock, patch

import pytest

pytestmark = [pytest.mark.unit]


# --------------------------------------------------------------------------- #
# #6 search_with_filters re-raise
# --------------------------------------------------------------------------- #
def test_search_with_filters_reraises_on_db_error():
    from services.definition_edit_repository import DefinitionEditRepository
    from services.exceptions import RepositoryError

    repo = DefinitionEditRepository.__new__(DefinitionEditRepository)
    repo._get_connection = Mock(side_effect=sqlite3.OperationalError("db kapot"))

    with pytest.raises(RepositoryError):
        repo.search_with_filters(search_term="x")


# --------------------------------------------------------------------------- #
# #7 approve(): ketenpartners gaan mee in één atomaire statuswijziging.
# DEF-482 keert het DEF-469-besluit "status blijft staan met waarschuwing" om:
# faalt de ketenpartners-opslag, dan is de definitie níet vastgesteld.
# --------------------------------------------------------------------------- #
def _approve_service_met_mock_repo():
    from services.definition_workflow_service import DefinitionWorkflowService

    svc = DefinitionWorkflowService.__new__(DefinitionWorkflowService)
    definition = Mock()
    definition.status = "review"
    definition.version_number = 3

    svc.repository = MagicMock()
    svc.repository.in_transaction.return_value = False
    svc.repository.get_definitie.return_value = definition
    svc.repository.change_status.return_value = True
    svc.workflow_service = Mock()
    svc.workflow_service.can_change_status.return_value = True
    svc.audit_logger = None
    svc.event_bus = None
    svc._evaluate_gate = Mock(return_value={"status": "pass", "reasons": []})
    return svc


def test_approve_fails_closed_when_ketenpartners_save_fails():
    svc = _approve_service_met_mock_repo()
    svc.repository.change_status.side_effect = sqlite3.OperationalError("boom")

    result = svc.approve(1, "tester", ketenpartners=["Partner A"], expected_version=3)

    assert result.success is False
    assert not hasattr(result, "warning")
    assert "boom" in (result.error_message or "")


def test_approve_passes_ketenpartners_and_version_in_one_change_status():
    svc = _approve_service_met_mock_repo()

    result = svc.approve(1, "tester", ketenpartners=["Partner A"], expected_version=3)

    assert result.success is True
    svc.repository.change_status.assert_called_once()
    kwargs = svc.repository.change_status.call_args.kwargs
    assert kwargs["ketenpartners"] == ["Partner A"]
    assert kwargs["expected_version"] == 3
    svc.repository.update_definitie.assert_not_called()


def test_approve_leaves_ketenpartners_untouched_when_none():
    """Zonder ketenpartners blijft de kolom ongemoeid (None, geen lege lijst)."""
    svc = _approve_service_met_mock_repo()

    result = svc.approve(1, "tester", ketenpartners=None, expected_version=3)

    assert result.success is True
    assert svc.repository.change_status.call_args.kwargs["ketenpartners"] is None
    svc.repository.update_definitie.assert_not_called()


# --------------------------------------------------------------------------- #
# #8 _get_policy(): logt bij loader-fout en valt terug op defaults
# --------------------------------------------------------------------------- #
def test_get_policy_logs_and_falls_back_on_loader_error():
    from services import definition_workflow_service as mod

    svc = mod.DefinitionWorkflowService.__new__(mod.DefinitionWorkflowService)

    failing_loader = Mock()
    failing_loader.return_value.get_policy.side_effect = RuntimeError("yaml weg")

    with (
        patch.object(mod, "GatePolicyService", failing_loader),
        patch.object(mod.logger, "error") as mock_error,
    ):
        policy = svc._get_policy()

    # Fout wordt niet langer stil geslikt
    assert mock_error.called
    # Fallback naar defaults blijft als laatste vangnet
    assert policy.hard_min_score == 0.75
