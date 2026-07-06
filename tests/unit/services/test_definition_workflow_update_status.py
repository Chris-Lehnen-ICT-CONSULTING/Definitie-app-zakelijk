"""Regressietest voor de dode import in DefinitionWorkflowService.update_status.

`update_status` importeerde `DefinitieStatus` uit het niet-bestaande
`models.enums` — de ModuleNotFoundError werd door het brede `except Exception`
opgeslokt, waardoor de methode ALTIJD stil False teruggaf. Gevolg in de UI:
"Maak bewerkbaar" en "Herstel uit archief" in de Expert Review-tab faalden
altijd met "Terugzetten/Herstellen mislukt". Gevonden tijdens DEF-502.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from database.models import DefinitieStatus
from services.definition_workflow_service import DefinitionWorkflowService
from services.workflow_service import WorkflowService

pytestmark = [pytest.mark.unit]


@pytest.fixture
def service_met_mock_repo():
    repository = MagicMock()
    repository.change_status.return_value = True
    service = DefinitionWorkflowService(
        workflow_service=WorkflowService(),
        repository=repository,
    )
    return service, repository


def test_update_status_converteert_string_naar_enum(service_met_mock_repo):
    """update_status("draft") delegeert met een echte DefinitieStatus-enum."""
    service, repository = service_met_mock_repo

    ok = service.update_status(
        definition_id=42, new_status="draft", user="tester", notes="herstel"
    )

    assert ok is True, "update_status faalde — dode import van models.enums?"
    repository.change_status.assert_called_once_with(
        definitie_id=42,
        new_status=DefinitieStatus.DRAFT,
        changed_by="tester",
        notes="herstel",
    )


@pytest.mark.parametrize("invoer", ["DRAFT", "Draft", "dRaFt"])
def test_update_status_is_case_insensitive(service_met_mock_repo, invoer):
    """De gedocumenteerde case-insensitieve conversie blijft werken."""
    service, repository = service_met_mock_repo

    ok = service.update_status(definition_id=42, new_status=invoer, user="tester")

    assert ok is True
    assert (
        repository.change_status.call_args.kwargs["new_status"] is DefinitieStatus.DRAFT
    )


def test_update_status_ongeldige_status_geeft_false(service_met_mock_repo):
    service, repository = service_met_mock_repo

    ok = service.update_status(definition_id=42, new_status="bestaat-niet")

    assert ok is False
    repository.change_status.assert_not_called()
