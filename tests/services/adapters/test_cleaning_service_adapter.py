import asyncio

import pytest

from services.adapters.cleaning_service_adapter import CleaningServiceAdapterV1toV2
from services.interfaces import CleaningResult, Definition


class FakeSyncCleaningService:
    def clean_text(self, text: str, term: str) -> CleaningResult:
        return CleaningResult(
            original_text=text,
            cleaned_text=text.strip(),
            was_cleaned=text != text.strip(),
            applied_rules=["strip"],
        )

    def clean_definition(self, definition: Definition) -> CleaningResult:
        return CleaningResult(
            original_text=definition.definitie,
            cleaned_text=definition.definitie.replace("  ", " "),
            was_cleaned="  " in definition.definitie,
            applied_rules=["dedupe-spaces"],
        )

    def validate_cleaning_rules(self) -> bool:
        return True


@pytest.mark.asyncio()
async def test_cleaning_service_adapter_clean_text():
    adapter = CleaningServiceAdapterV1toV2(FakeSyncCleaningService())
    result = await adapter.clean_text("  tekst  ", "begrip")
    assert isinstance(result, CleaningResult)
    assert result.cleaned_text == "tekst"
    assert result.was_cleaned is True
    assert "strip" in result.applied_rules


@pytest.mark.asyncio()
async def test_cleaning_service_adapter_clean_definition():
    adapter = CleaningServiceAdapterV1toV2(FakeSyncCleaningService())
    definition = Definition(begrip="test", definitie="a  b")
    result = await adapter.clean_definition(definition)
    assert isinstance(result, CleaningResult)
    assert result.cleaned_text == "a b"
    assert result.was_cleaned is True
    assert "dedupe-spaces" in result.applied_rules


def test_cleaning_service_adapter_validate_rules_sync():
    adapter = CleaningServiceAdapterV1toV2(FakeSyncCleaningService())
    assert adapter.validate_cleaning_rules() is True
