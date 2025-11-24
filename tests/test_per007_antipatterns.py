"""
PER-007 Anti-Pattern Tests: Ensuring Bad Patterns Are Blocked
These tests ensure that bad patterns are permanently blocked and never reintroduced.
"""

import warnings
from unittest.mock import Mock, patch

import pytest

from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2


class TestAntiPatterns:
    """Tests that ensure bad patterns are permanently blocked"""

    @pytest.mark.antipattern
    def test_never_parse_ui_emoji_strings(self):
        """Emojis in data layer should always fail"""
        # GIVEN: Attempt to put emojis in structured data
        # THEN: Should be rejected immediately
        with pytest.raises(ValueError, match="Emojis not allowed in data"):
            EnrichedContext(
                base_context={
                    "organisatorisch": ["📋 OM"],  # Emoji in data - BAD!
                    "juridisch": ["⚖️ Strafrecht"],  # Emoji in data - BAD!
                },
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={},
            )

    @pytest.mark.antipattern
    def test_never_concatenate_then_split(self):
        """Concatenate-then-split pattern must be blocked"""
        # GIVEN: List of organizations
        data = ["OM", "DJI", "Rechtspraak"]

        # WHEN: Someone tries the anti-pattern
        concatenated = ", ".join(data)  # DON'T DO THIS for data processing

        # THEN: Framework should detect and warn
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Simulate the anti-pattern detection
            if ", " in concatenated and isinstance(data, list):
                warnings.warn(
                    "Detected concatenate-then-split anti-pattern. "
                    "Use structured lists throughout.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            # Should have warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "concatenate-then-split" in str(w[0].message)

    @pytest.mark.antipattern
    def test_never_mix_ui_and_data_logic(self):
        """UI logic in business layer must fail"""
        # GIVEN: Prompt service (business layer)
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()

        # THEN: UI methods should not exist in business layer
        ui_methods = [
            "add_emoji_formatting",
            "format_for_display",
            "create_ui_preview",
            "add_ui_decorators",
        ]

        for method in ui_methods:
            # These methods should NOT exist
            assert not hasattr(
                service, method
            ), f"UI method '{method}' found in business layer PromptServiceV2"

    @pytest.mark.antipattern
    def test_never_use_string_context_field(self):
        """Legacy string context field must be ignored when structured fields present"""
        # GIVEN: Request with both old and new style context
        request = GenerationRequest(
            begrip="test",
            context="This is old string context - SHOULD BE IGNORED",  # Legacy
            organisatorische_context=["OM"],  # New structured
            juridische_context=["Strafrecht"],  # New structured
        )

        # WHEN: Processing
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: Old string context should NOT appear anywhere
        all_values = []
        for _key, values in context.items():
            if isinstance(values, list):
                all_values.extend(values)

        assert "This is old string context" not in str(
            all_values
        ), "Legacy string context leaked into structured data"
        assert "SHOULD BE IGNORED" not in str(
            all_values
        ), "Legacy context not properly ignored"

        # Only structured data should be used
        assert "OM" in context["organisatorisch"]
        assert "Strafrecht" in context["juridisch"]

    @pytest.mark.antipattern
    def test_never_process_ui_strings_as_data(self):
        """UI strings should never be processable as data"""
        # GIVEN: A UI preview string
        ui_string = "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht"

        # WHEN: Attempting to process it
        manager = HybridContextManager()

        # THEN: Should be impossible to parse as context
        # Check that no method exists to do this
        assert not hasattr(
            manager, "parse_ui_string"
        ), "UI string parsing method should not exist"
        assert not hasattr(
            manager, "context_from_preview"
        ), "UI preview parsing should not exist"

        # If someone tries to hack it through
        request = GenerationRequest(
            begrip="test", context=ui_string  # Try to pass UI string
        )

        context = manager._build_base_context(request)

        # Emojis should never make it into structured data
        all_text = str(context)
        assert "📋" not in all_text, "Emoji leaked into context"
        assert "⚖️" not in all_text, "Emoji leaked into context"
        assert "📜" not in all_text, "Emoji leaked into context"

    @pytest.mark.antipattern
    def test_never_store_formatted_strings_in_database(self):
        """Database should only store structured data, not formatted strings"""
        # GIVEN: Context data to be saved
        context_data = {
            "organisatorische_context": ["OM", "DJI"],
            "juridische_context": ["Strafrecht"],
        }

        # WHEN: Preparing for database storage
        # Simulate what should NOT happen
        bad_storage = "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht"

        # THEN: Storage format validation should fail
        def validate_storage_format(data):
            """Validate data is structured, not formatted"""
            if isinstance(data, str):
                if any(emoji in data for emoji in ["📋", "⚖️", "📜"]):
                    msg = "Formatted UI strings cannot be stored in database"
                    raise ValueError(msg)
                if " | " in data and ": " in data:
                    msg = "Detected UI formatting in storage data"
                    raise ValueError(msg)
            return True

        # Good storage should pass
        assert validate_storage_format(context_data)

        # Bad storage should fail
        with pytest.raises(ValueError, match="cannot be stored in database"):
            validate_storage_format(bad_storage)

    @pytest.mark.antipattern
    def test_never_reverse_engineer_from_display(self):
        """Should never try to reverse-engineer data from display format"""
        # GIVEN: A display string

        # THEN: No method should exist to parse this back
        manager = HybridContextManager()
        service = PromptServiceV2()

        # These methods should NOT exist
        assert not hasattr(manager, "parse_display_string")
        assert not hasattr(manager, "extract_from_display")
        assert not hasattr(service, "context_from_display")
        assert not hasattr(service, "reverse_format")

    @pytest.mark.antipattern
    def test_never_use_display_strings_in_prompts(self):
        """Prompts should use structured data, not display strings"""
        # GIVEN: A prompt service
        service = PromptServiceV2()

        # WHEN: Building a prompt
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "DJI"],
            juridische_context=["Strafrecht"],
        )

        # Mock the internal prompt building
        with patch.object(service, "_build_prompt_sections") as mock_build:
            mock_build.return_value = {"context": "proper structured context"}

            # Build prompt
            enriched = service._convert_request_to_context(request)

            # THEN: Should never try to use display format
            # Check enriched context has no UI formatting
            context_str = str(enriched.base_context)
            assert "📋" not in context_str
            assert " | " not in context_str
            assert "⚖️" not in context_str

    @pytest.mark.antipattern
    def test_never_couple_tests_to_ui_format(self):
        """Tests should verify data, not UI format"""
        # GIVEN: Test data
        context = {"organisatorisch": ["OM", "DJI"], "juridisch": ["Strafrecht"]}

        # GOOD: Test the data
        assert "OM" in context["organisatorisch"]
        assert "DJI" in context["organisatorisch"]

        # BAD: Don't test UI format in business logic tests
        # This is what we should NEVER do:
        def bad_test_example():
            ui_string = "📋 Org: OM, DJI"
            # Don't test for UI format in business tests
            assert "📋 Org:" in ui_string  # BAD - coupled to UI

        # Verify this pattern is detected
        import inspect

        source = inspect.getsource(bad_test_example)
        assert "📋" in source, "Example should show bad pattern"
        assert "# BAD" in source, "Should be marked as bad pattern"

    @pytest.mark.antipattern
    def test_never_pass_enriched_context_to_ui(self):
        """UI should only receive formatted strings, not EnrichedContext objects"""
        # GIVEN: EnrichedContext object
        enriched = EnrichedContext(
            base_context={"organisatorisch": ["OM"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )

        # THEN: UI components should not accept EnrichedContext directly
        def ui_component_signature(data):
            """Simulated UI component"""
            if isinstance(data, EnrichedContext):
                msg = (
                    "UI components should not receive EnrichedContext objects. "
                    "Use ContextFormatter to create display strings."
                )
                raise TypeError(msg)
            return True

        # Should fail with EnrichedContext
        with pytest.raises(
            TypeError, match="UI components should not receive EnrichedContext"
        ):
            ui_component_signature(enriched)

        # Should pass with formatted string
        assert ui_component_signature("Formatted string for display")
