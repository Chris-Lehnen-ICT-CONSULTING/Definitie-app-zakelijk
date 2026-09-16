"""B1: uitsluitend toetsen bewaart object en exact validatortransport."""

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from services.cleaning_service import CleaningConfig, CleaningService
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("route", ["text", "definition"])
async def test_echte_cleaner_mag_toetsinvoer_niet_veranderen(route):
    tekst = "  Toezicht is een activiteit In Het Kader Van uitvoering.  "
    definition = Definition(
        begrip="toezicht", definitie=tekst, metadata={"own": "value"}
    )
    before = deepcopy(definition)
    cleaner = CleaningService(CleaningConfig(log_operations=False))
    # Bewijs dat deze echte cleaner de gekozen invoer daadwerkelijk zou veranderen.
    assert (await cleaner.clean_text(tekst, definition.begrip)).cleaned_text != tekst
    cleaner.clean_text = AsyncMock(wraps=cleaner.clean_text)
    cleaner.clean_definition = AsyncMock(wraps=cleaner.clean_definition)
    service = ModularValidationService(get_toetsregel_manager(), None, None)
    service.validate_definition = AsyncMock(wraps=service.validate_definition)
    orchestrator = ValidationOrchestratorV2(service, cleaning_service=cleaner)
    if route == "text":
        result = await orchestrator.validate_text(definition.begrip, tekst)
    else:
        result = await orchestrator.validate_definition(definition)
    kwargs = service.validate_definition.call_args.kwargs
    assert kwargs["text"] == tekst
    assert kwargs["context"]["record_text"] == tekst
    assert definition == before
    cleaner.clean_text.assert_not_called()
    cleaner.clean_definition.assert_not_called()
    assert result["rule_statuses"]["ESS-01"] == "review_required"
    item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-01")
    assert "In Het Kader Van" in item["reason"]
