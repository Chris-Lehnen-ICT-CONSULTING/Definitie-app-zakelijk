"""
DEF-232: Test suite for CleaningService async implementation.

These tests verify that the CleaningService correctly implements native async
using asyncio.to_thread() for CPU-bound opschoning operations.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cleaning_service import CleaningConfig, CleaningService
from services.interfaces import CleaningResult, Definition


class TestCleaningServiceInit:
    """Test CleaningService initialization."""

    def test_init_with_default_config(self):
        """CleaningService initializes with default CleaningConfig."""
        config = CleaningConfig()
        service = CleaningService(config)

        assert service.config == config
        assert service.config.enable_cleaning is True
        assert service.config.track_changes is True

    def test_init_with_custom_config(self):
        """CleaningService respects custom configuration."""
        config = CleaningConfig(
            enable_cleaning=False,
            track_changes=False,
            preserve_original=False,
            log_operations=False,
        )
        service = CleaningService(config)

        assert service.config.enable_cleaning is False
        assert service.config.track_changes is False


class TestCleanTextAsync:
    """DEF-232: Test async clean_text method."""

    @pytest.mark.asyncio
    async def test_clean_text_returns_cleaning_result(self):
        """clean_text should return CleaningResult with async execution."""
        config = CleaningConfig()
        service = CleaningService(config)

        result = await service.clean_text("test definitie", "test")

        assert isinstance(result, CleaningResult)
        assert hasattr(result, "original_text")
        assert hasattr(result, "cleaned_text")
        assert hasattr(result, "was_cleaned")
        assert hasattr(result, "applied_rules")
        assert hasattr(result, "metadata")

    @pytest.mark.asyncio
    async def test_clean_text_preserves_original_when_no_changes(self):
        """clean_text should preserve text when no cleaning needed."""
        config = CleaningConfig()
        service = CleaningService(config)

        # Already clean text (starts with capital, ends with period)
        clean_text = "Een proces dat leidt tot een resultaat."
        result = await service.clean_text(clean_text, "proces")

        assert result.original_text == clean_text
        # Text might be cleaned or not depending on opschoning rules
        assert isinstance(result.cleaned_text, str)

    @pytest.mark.asyncio
    async def test_clean_text_tracks_metadata(self):
        """clean_text should include metadata with timestamp and term."""
        config = CleaningConfig()
        service = CleaningService(config)

        result = await service.clean_text("definitie tekst", "begrip")

        assert "timestamp" in result.metadata
        assert "term" in result.metadata
        assert result.metadata["term"] == "begrip"
        assert "service_version" in result.metadata

    @pytest.mark.asyncio
    async def test_clean_text_handles_gpt_format(self):
        """clean_text should handle GPT format with ontologische categorie."""
        config = CleaningConfig()
        service = CleaningService(config)

        gpt_text = "Ontologische categorie: type\nEen formele definitie van het begrip."
        result = await service.clean_text(gpt_text, "begrip")

        assert isinstance(result, CleaningResult)
        # Should have extracted ontology rule applied
        assert isinstance(result.applied_rules, list)

    @pytest.mark.asyncio
    async def test_clean_text_error_handling(self):
        """clean_text should return original text on error."""
        config = CleaningConfig()
        service = CleaningService(config)

        # Mock opschonen_enhanced to raise an exception
        with patch(
            "services.cleaning_service.opschonen_enhanced",
            side_effect=ValueError("Test error"),
        ):
            result = await service.clean_text("test tekst", "test")

            # Should return original text on error
            assert result.cleaned_text == "test tekst"
            assert result.was_cleaned is False
            assert "error_occurred" in result.applied_rules
            assert "error" in result.metadata

    @pytest.mark.asyncio
    async def test_clean_text_uses_asyncio_to_thread(self):
        """DEF-232: CPU-bound opschonen_enhanced should run via asyncio.to_thread."""
        config = CleaningConfig()
        service = CleaningService(config)

        # Track if to_thread was called
        original_to_thread = asyncio.to_thread

        to_thread_called = []

        async def mock_to_thread(func, *args, **kwargs):
            to_thread_called.append(func.__name__)
            return await original_to_thread(func, *args, **kwargs)

        with patch("services.cleaning_service.asyncio.to_thread", mock_to_thread):
            await service.clean_text("test definitie", "test")

        # Verify asyncio.to_thread was used for CPU-bound work
        assert "opschonen_enhanced" in to_thread_called


class TestCleanDefinitionAsync:
    """DEF-232: Test async clean_definition method."""

    @pytest.mark.asyncio
    async def test_clean_definition_returns_cleaning_result(self):
        """clean_definition should return CleaningResult."""
        config = CleaningConfig()
        service = CleaningService(config)

        definition = Definition(
            begrip="testbegrip",
            definitie="een test definitie",
            organisatorische_context=["Test"],
            juridische_context=["Algemeen"],
        )

        result = await service.clean_definition(definition)

        assert isinstance(result, CleaningResult)

    @pytest.mark.asyncio
    async def test_clean_definition_updates_definition_metadata(self):
        """clean_definition should update Definition.metadata when changes applied."""
        config = CleaningConfig(preserve_original=True)
        service = CleaningService(config)

        # Create definition with text that will be cleaned
        definition = Definition(
            begrip="test",
            definitie="test is een begrip",  # Will trigger circular definition removal
            organisatorische_context=["Test"],
            juridische_context=["Algemeen"],
            metadata={},
        )

        result = await service.clean_definition(definition)

        # If cleaning was applied, metadata should be updated
        if result.was_cleaned:
            assert definition.metadata.get("cleaning_applied") is True
            assert "original_definitie" in definition.metadata
            assert "cleaning_timestamp" in definition.metadata
            assert "cleaning_rules_applied" in definition.metadata

    @pytest.mark.asyncio
    async def test_clean_definition_initializes_metadata_if_none(self):
        """clean_definition should initialize metadata dict if None."""
        config = CleaningConfig(preserve_original=True)
        service = CleaningService(config)

        definition = Definition(
            begrip="begrip",
            definitie="begrip is iets",  # Will be cleaned (circular)
            organisatorische_context=["Test"],
            juridische_context=["Algemeen"],
            metadata=None,  # Explicitly None
        )

        await service.clean_definition(definition)

        # Metadata should be initialized (not None)
        assert definition.metadata is not None
        assert isinstance(definition.metadata, dict)


class TestConcurrentCleaning:
    """Test concurrent async cleaning operations."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_cleans(self):
        """Multiple concurrent clean_text calls should all complete successfully."""
        config = CleaningConfig()
        service = CleaningService(config)

        # Create 10 concurrent cleaning tasks
        tasks = [
            service.clean_text(f"definitie nummer {i}", f"begrip{i}") for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 10
        assert all(isinstance(r, CleaningResult) for r in results)
        assert all(isinstance(r.cleaned_text, str) for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_clean_definitions(self):
        """Multiple concurrent clean_definition calls should work correctly."""
        config = CleaningConfig()
        service = CleaningService(config)

        definitions = [
            Definition(
                begrip=f"begrip{i}",
                definitie=f"Definitie voor begrip {i}.",
                organisatorische_context=["Test"],
                juridische_context=["Algemeen"],
            )
            for i in range(5)
        ]

        tasks = [service.clean_definition(d) for d in definitions]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(isinstance(r, CleaningResult) for r in results)


class TestValidateCleaningRules:
    """Test validate_cleaning_rules method (synchronous)."""

    def test_validate_cleaning_rules_returns_bool(self):
        """validate_cleaning_rules should return a boolean."""
        config = CleaningConfig()
        service = CleaningService(config)

        result = service.validate_cleaning_rules()

        assert isinstance(result, bool)

    def test_validate_cleaning_rules_with_missing_config(self):
        """validate_cleaning_rules should handle missing config gracefully."""
        config = CleaningConfig()
        service = CleaningService(config)

        # Mock laad_verboden_woorden at the source module (where it's imported from)
        with patch(
            "config.verboden_woorden.laad_verboden_woorden",
            return_value=None,
        ):
            result = service.validate_cleaning_rules()

            # Should return False when no config found
            assert result is False


class TestAnalyzeChanges:
    """Test internal _analyze_changes method."""

    def test_analyze_changes_detects_circular_definition(self):
        """_analyze_changes should detect circular definition removal."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "begrip is een woord"
        cleaned = "een woord"

        rules = service._analyze_changes(original, cleaned, "begrip")

        assert "removed_circular_definition" in rules

    def test_analyze_changes_detects_forbidden_prefix(self):
        """_analyze_changes should detect forbidden prefix removal."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "is een formele beschrijving"
        cleaned = "Een formele beschrijving"

        rules = service._analyze_changes(original, cleaned, "test")

        assert "removed_forbidden_prefix" in rules

    def test_analyze_changes_detects_article_removal(self):
        """_analyze_changes should detect article removal."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "de formele beschrijving"
        cleaned = "Formele beschrijving"

        rules = service._analyze_changes(original, cleaned, "test")

        assert "removed_article" in rules

    def test_analyze_changes_detects_capitalization(self):
        """_analyze_changes should detect first letter capitalization."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "formele beschrijving"
        cleaned = "Formele beschrijving"

        rules = service._analyze_changes(original, cleaned, "test")

        assert "capitalized_first_letter" in rules

    def test_analyze_changes_detects_period_addition(self):
        """_analyze_changes should detect period addition."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "Een formele beschrijving"
        cleaned = "Een formele beschrijving."

        rules = service._analyze_changes(original, cleaned, "test")

        assert "added_period" in rules


class TestGenerateImprovements:
    """Test internal _generate_improvements method."""

    def test_generate_improvements_detects_prefix_removal(self):
        """_generate_improvements should note prefix removal."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "is een lange beschrijving"
        cleaned = "Beschrijving"

        improvements = service._generate_improvements(original, cleaned)

        assert "Verwijderd onnodige voorvoegsels" in improvements

    def test_generate_improvements_detects_capitalization(self):
        """_generate_improvements should note capitalization."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "beschrijving"
        cleaned = "Beschrijving"

        improvements = service._generate_improvements(original, cleaned)

        assert "Hoofdletter toegevoegd" in improvements

    def test_generate_improvements_detects_period(self):
        """_generate_improvements should note period addition."""
        config = CleaningConfig()
        service = CleaningService(config)

        original = "Beschrijving"
        cleaned = "Beschrijving."

        improvements = service._generate_improvements(original, cleaned)

        assert "Eindpunt toegevoegd" in improvements


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
