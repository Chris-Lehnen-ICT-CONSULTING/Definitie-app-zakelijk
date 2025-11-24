import pytest

from services.adapters.validation_service_adapter import ValidationServiceAdapterV1toV2
from services.interfaces import Definition, ValidationResult


class FakeSyncValidationService:
    def __init__(self):
        self.last_definition: Definition | None = None

    def validate(self, definition: Definition) -> ValidationResult:
        # Keep track of what we received
        self.last_definition = definition
        # Return a minimal valid result
        return ValidationResult(
            is_valid=True, definition_text=definition.definitie, score=0.9
        )


@pytest.mark.asyncio
async def test_validation_service_adapter_builds_definition_and_validates():
    fake = FakeSyncValidationService()
    adapter = ValidationServiceAdapterV1toV2(fake)

    res = await adapter.validate_definition(
        begrip="authenticatie",
        text="Authenticatie is ...",
        ontologische_categorie="juridisch concept",
        context={"profile": "default"},
    )

    assert isinstance(res, ValidationResult)
    assert res.is_valid is True
    assert res.definition_text == "Authenticatie is ..."
    assert fake.last_definition is not None
    assert fake.last_definition.begrip == "authenticatie"
    assert fake.last_definition.ontologische_categorie == "juridisch concept"


@pytest.mark.asyncio
async def test_validation_service_adapter_batch_validate_processes_all():
    fake = FakeSyncValidationService()
    adapter = ValidationServiceAdapterV1toV2(fake)

    items = [("A", "def A"), ("B", "def B")]
    results = await adapter.batch_validate(items)
    assert len(results) == 2
    assert all(isinstance(r, ValidationResult) for r in results)
