"""Tests voor DEF-469 deelstap 2b — resterende stille failures zichtbaar maken.

- search_with_filters: re-raiset i.p.v. stil [] (false-negative maskeert DB-fout).
- approve(): ketenpartners-fout wordt niet meer stil geslikt maar als waarschuwing
  teruggegeven (status-transitie blijft geslaagd).
- _get_policy(): logt nu expliciet bij een loader-fout i.p.v. stille `pass`.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import Mock, patch

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
# #7 approve(): ketenpartners-fout -> waarschuwing, transitie blijft geslaagd
# --------------------------------------------------------------------------- #
def test_approve_sets_warning_when_ketenpartners_save_fails():
    from services.definition_workflow_service import DefinitionWorkflowService

    svc = DefinitionWorkflowService.__new__(DefinitionWorkflowService)
    definition = Mock()
    definition.status = "review"

    svc.repository = Mock()
    svc.repository.get_definitie.return_value = definition
    svc.repository.change_status.return_value = True
    svc.repository.update_definitie.side_effect = sqlite3.OperationalError("boom")
    svc.workflow_service = Mock()
    svc.workflow_service.can_change_status.return_value = True
    svc.audit_logger = None
    svc.event_bus = None
    svc._evaluate_gate = Mock(return_value={"status": "pass", "reasons": []})

    result = svc.approve(1, "tester", ketenpartners=["Partner A"])

    assert result.success is True
    assert result.warning is not None
    assert "ketenpartners" in result.warning.lower()


def test_approve_no_warning_when_ketenpartners_ok():
    from services.definition_workflow_service import DefinitionWorkflowService

    svc = DefinitionWorkflowService.__new__(DefinitionWorkflowService)
    definition = Mock()
    definition.status = "review"

    svc.repository = Mock()
    svc.repository.get_definitie.return_value = definition
    svc.repository.change_status.return_value = True
    svc.repository.update_definitie.return_value = True
    svc.workflow_service = Mock()
    svc.workflow_service.can_change_status.return_value = True
    svc.audit_logger = None
    svc.event_bus = None
    svc._evaluate_gate = Mock(return_value={"status": "pass", "reasons": []})

    result = svc.approve(1, "tester", ketenpartners=["Partner A"])

    assert result.success is True
    assert result.warning is None


def test_approve_no_warning_and_no_save_when_no_ketenpartners():
    """Zonder ketenpartners wordt er geen ketenpartners-save gedaan, geen warning."""
    from services.definition_workflow_service import DefinitionWorkflowService

    svc = DefinitionWorkflowService.__new__(DefinitionWorkflowService)
    definition = Mock()
    definition.status = "review"

    svc.repository = Mock()
    svc.repository.get_definitie.return_value = definition
    svc.repository.change_status.return_value = True
    svc.workflow_service = Mock()
    svc.workflow_service.can_change_status.return_value = True
    svc.audit_logger = None
    svc.event_bus = None
    svc._evaluate_gate = Mock(return_value={"status": "pass", "reasons": []})

    result = svc.approve(1, "tester", ketenpartners=None)

    assert result.success is True
    assert result.warning is None
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
