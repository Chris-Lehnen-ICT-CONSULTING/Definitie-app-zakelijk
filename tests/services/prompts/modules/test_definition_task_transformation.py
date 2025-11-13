"""
Test DefinitionTaskModule transformation for DEF-126 - constructive language shift.

These tests MUST FAIL initially (red phase of TDD) until the transformation
is implemented. They validate the shift from validation checklist to
construction guide.

OLD: "CHECKLIST - Controleer voor je antwoord"
NEW: "CONSTRUCTIE GUIDE - Bouw je definitie op"
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.services.prompts.modules.base_module import EnrichedContext, ModuleContext
from src.services.prompts.modules.definition_task_module import DefinitionTaskModule


class TestDefinitionTaskTransformation:
    """Test suite for definition task module language transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = DefinitionTaskModule()
        self.module.initialize(
            {"include_quality_control": True, "include_metadata": True}
        )

        # Create a mock context with all required attributes
        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"

        # Mock enriched context for juridical/legal basis
        enriched = MagicMock(spec=EnrichedContext)
        enriched.base_context = {}
        self.context.enriched_context = enriched

        # Mock shared data retrieval
        self.context.get_shared = MagicMock(side_effect=self._get_shared_mock)

    def _get_shared_mock(self, key, default=None):
        """Mock implementation for get_shared."""
        shared_data = {
            "word_type": "overig",
            "ontological_category": "proces",
            "organization_contexts": ["gemeente"],
            "juridical_contexts": [],
            "legal_basis_contexts": [],
        }
        return shared_data.get(key, default)

    def test_checklist_becomes_construction_guide(self):
        """
        Test that CHECKLIST is replaced with CONSTRUCTIE GUIDE.

        The language should shift from validation-focused "controleer"
        to construction-focused "bouw op".
        """
        result = self.module.execute(self.context)

        # Check that old checklist language is gone
        assert (
            "CHECKLIST - Controleer voor je antwoord" not in result.content
        ), "Old validation-focused checklist language should be removed"

        # Check that new construction guide is present
        assert (
            "CONSTRUCTIE GUIDE" in result.content
        ), "New construction guide header must be present"

        assert (
            "Bouw je definitie op" in result.content
        ), "Construction-focused language 'Bouw je definitie op' must be present"

    def test_no_controleer_in_main_sections(self):
        """
        Test that "controleer" (check/validate) is removed from main sections.

        The word might still appear in metadata or specific validation contexts,
        but should not be in the main instructional content.
        """
        result = self.module.execute(self.context)

        # Split content into main and metadata sections
        main_content = result.content.split("METADATA voor traceerbaarheid")[0]

        # "Controleer" should not be in main instructional content
        assert (
            "Controleer" not in main_content
        ), "Validation language 'Controleer' should be removed from main instructions"

    def test_constructive_language_in_guide(self):
        """
        Test that the guide uses constructive, building-focused language.

        Should use words like "bouw", "construeer", "vorm", "creëer"
        instead of "check", "controleer", "toets".
        """
        result = self.module.execute(self.context)

        # Look for the guide section
        guide_start = result.content.find("CONSTRUCTIE GUIDE")
        if guide_start == -1:
            guide_start = result.content.find("📋")  # Alternative marker

        guide_section = result.content[guide_start : guide_start + 1000]

        # Check for constructive language
        constructive_words = ["bouw", "construeer", "vorm", "creëer", "stel", "maak"]
        found_constructive = any(
            word in guide_section.lower() for word in constructive_words
        )

        assert (
            found_constructive
        ), "Construction guide should use constructive language like 'bouw', 'construeer', 'vorm'"

    def test_checklist_items_become_construction_steps(self):
        """
        Test that checklist items are reframed as construction steps.

        Instead of "□ Check X", should be "→ Build/Create Y"
        or similar constructive format.
        """
        result = self.module.execute(self.context)

        # At least the checkbox format should change
        checkbox_count = result.content.count("□")

        # Could use arrows or other construction-focused markers
        arrow_count = result.content.count("→")
        plus_count = result.content.count("✓")
        step_count = result.content.lower().count("stap")

        assert (
            arrow_count > 0 or plus_count > 0 or step_count > 0 or checkbox_count == 0
        ), (
            "Checklist items should be transformed to construction steps "
            "using arrows (→), checkmarks (✓), or step indicators"
        )

    def test_quality_control_uses_positive_framing(self):
        """
        Test that quality control section uses positive, constructive framing.

        Instead of "check if not X", should be "ensure Y" or "build with Z".
        """
        result = self.module.execute(self.context)

        if "KWALITEITSCONTROLE" in result.content:
            quality_section = result.content[
                result.content.find("KWALITEITSCONTROLE") : result.content.find(
                    "KWALITEITSCONTROLE"
                )
                + 500
            ]

            # Should use positive framing
            positive_indicators = [
                "zorg",
                "bouw",
                "maak",
                "creëer",
                "waarborg",
                "realiseer",
                "bewerkstellig",
            ]

            has_positive = any(
                ind in quality_section.lower() for ind in positive_indicators
            )

            assert (
                has_positive
            ), "Quality control should use positive, constructive language"

    def test_task_assignment_is_constructive(self):
        """
        Test that the task assignment uses constructive language.

        Should focus on building/creating rather than checking/validating.
        """
        result = self.module.execute(self.context)

        # Find task assignment section
        task_section = None
        if "Definitieopdracht:" in result.content:
            start = result.content.find("Definitieopdracht:")
            task_section = result.content[start : start + 200]

        if task_section:
            # Should use "Formuleer", "Bouw", "Creëer" or similar
            assert any(
                word in task_section
                for word in ["Formuleer", "Bouw", "Creëer", "Construeer", "Stel op"]
            ), "Task assignment should use constructive verbs"

    def test_no_negative_commands_in_guide(self):
        """
        Test that the guide minimizes negative commands.

        Instead of multiple "Geen X", "Niet Y", "Vermijd Z",
        should focus on what TO do.
        """
        result = self.module.execute(self.context)

        # Count negative indicators
        guide_section = result.content[
            : (
                result.content.find("METADATA")
                if "METADATA" in result.content
                else len(result.content)
            )
        ]

        negative_count = (
            guide_section.count("Geen ")
            + guide_section.count("Niet ")
            + guide_section.count("Vermijd ")
            + guide_section.count("niet ")
        )

        # Some negatives might be necessary, but should be minimal
        assert negative_count < 10, (
            f"Guide has {negative_count} negative commands. "
            "Should focus on positive construction instructions instead"
        )

    def test_ontological_marker_instructions_are_constructive(self):
        """
        Test that ontological marker instructions are framed constructively.
        """
        result = self.module.execute(self.context)

        if "Ontologische marker" in result.content:
            marker_section = result.content[
                result.content.find("Ontologische marker") : result.content.find(
                    "Ontologische marker"
                )
                + 200
            ]

            # Should instruct to "provide" or "specify" rather than "check"
            assert (
                "controleer" not in marker_section.lower()
            ), "Ontological marker should not use validation language"

    def test_final_instruction_emphasizes_creation(self):
        """
        Test that the final instruction emphasizes creating/building the definition.
        """
        result = self.module.execute(self.context)

        # Find the final instruction (usually contains the begrip)
        final_instruction = None
        lines = result.content.split("\n")
        for line in lines:
            if self.context.begrip in line and "definitie" in line.lower():
                final_instruction = line
                break

        if final_instruction:
            # Should use creative/constructive language
            constructive_verbs = ["Geef", "Formuleer", "Creëer", "Bouw", "Stel op"]
            assert any(
                verb in final_instruction for verb in constructive_verbs
            ), "Final instruction should use constructive verbs like 'Geef' or 'Formuleer'"

    def test_metadata_section_unchanged(self):
        """
        Test that metadata section remains functional but uses appropriate language.

        Metadata can remain mostly unchanged as it's for traceability,
        not instruction.
        """
        result = self.module.execute(self.context)

        # Metadata should still be present
        assert "METADATA" in result.content or "Metadata" in result.content
        assert "Timestamp" in result.content or "timestamp" in result.content

    @pytest.mark.parametrize(
        ("ontological_category", "expected_hint"),
        [
            ("proces", "activiteit/handeling"),
            ("type", "soort/categorie"),
            ("resultaat", "uitkomst/gevolg"),
            ("exemplaar", "specifiek geval"),
        ],
    )
    def test_ontological_hints_use_constructive_language(
        self, ontological_category, expected_hint
    ):
        """
        Test that ontological category hints are framed constructively.
        """
        self.context.get_shared = MagicMock(
            side_effect=lambda key, default=None: (
                ontological_category if key == "ontological_category" else default
            )
        )

        result = self.module.execute(self.context)

        # Should still provide the hint but in constructive context
        if expected_hint in result.content:
            # Find the context around the hint
            hint_pos = result.content.find(expected_hint)
            context_around = result.content[max(0, hint_pos - 50) : hint_pos + 50]

            # Should be framed as guidance, not restriction
            assert (
                "Focus:" in context_around
                or "Bouw" in context_around
                or "als" in context_around
            ), f"Ontological hint for {ontological_category} should be framed constructively"


class TestDefinitionTaskBackwardCompatibility:
    """Test that essential functionality is preserved during transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = DefinitionTaskModule()
        self.module.initialize({})

        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"
        enriched = MagicMock(spec=EnrichedContext)
        enriched.base_context = {}
        self.context.enriched_context = enriched
        self.context.get_shared = MagicMock(return_value=None)

    def test_module_structure_preserved(self):
        """Test that the module structure remains valid."""
        assert self.module.module_id == "definition_task"
        assert self.module.module_name == "Final Instructions & Task Definition"

    def test_execute_returns_valid_output(self):
        """Test that execute still returns valid ModuleOutput."""
        result = self.module.execute(self.context)

        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "success")

    def test_all_required_sections_present(self):
        """Test that all required sections are still generated."""
        result = self.module.execute(self.context)

        # Essential sections should still exist (perhaps with new names)
        essential_elements = [
            "FINALE INSTRUCTIES",  # Or new equivalent
            "Definitieopdracht",  # Task assignment
            self.context.begrip,  # The actual term
            "📋",  # Some form of guide/checklist
        ]

        for element in essential_elements:
            assert (
                element in result.content or element.lower() in result.content.lower()
            ), f"Essential element '{element}' should still be present"

    def test_metadata_still_tracked(self):
        """Test that metadata is still properly tracked."""
        result = self.module.execute(self.context)

        assert result.metadata is not None
        assert "begrip" in result.metadata
        assert result.metadata["begrip"] == "vergunning"

    def test_dependencies_still_declared(self):
        """Test that module dependencies are still declared."""
        deps = self.module.get_dependencies()
        assert "semantic_categorisation" in deps


class TestDefinitionTaskEdgeCases:
    """Test edge cases and boundary conditions for the transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = DefinitionTaskModule()
        self.module.initialize({})

    def test_handles_missing_enriched_context(self):
        """Test handling when enriched context is missing."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.enriched_context = None
        context.get_shared = MagicMock(return_value=None)

        result = self.module.execute(context)

        # Should still work and include construction guide
        assert result.success is True
        assert "CONSTRUCTIE GUIDE" in result.content or "📋" in result.content

    def test_handles_all_context_types(self):
        """Test that all context types are handled in new format."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"

        enriched = MagicMock(spec=EnrichedContext)
        enriched.base_context = {
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Wetboek van Strafrecht"],
        }
        context.enriched_context = enriched

        context.get_shared = MagicMock(
            side_effect=lambda key, default=None: {
                "organization_contexts": ["OM", "ZM"],
                "juridical_contexts": ["Strafrecht"],
                "legal_basis_contexts": ["Wetboek van Strafrecht"],
            }.get(key, default)
        )

        result = self.module.execute(context)

        # Should handle all contexts appropriately
        assert result.success is True
        assert "CONSTRUCTIE GUIDE" in result.content or "Bouw" in result.content.lower()

    def test_config_flags_respected(self):
        """Test that configuration flags are still respected."""
        # Test with quality control disabled
        module1 = DefinitionTaskModule()
        module1.initialize({"include_quality_control": False})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.enriched_context = None
        context.get_shared = MagicMock(return_value=None)

        result1 = module1.execute(context)

        # Test with quality control enabled
        module2 = DefinitionTaskModule()
        module2.initialize({"include_quality_control": True})

        result2 = module2.execute(context)

        # With quality control should have more content
        assert len(result2.content) >= len(result1.content)

    def test_very_long_begrip(self):
        """Test handling of very long begrippen."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "zeer uitgebreide en gedetailleerde begripsomschrijving met vele componenten"
        context.enriched_context = None
        context.get_shared = MagicMock(return_value=None)

        module = DefinitionTaskModule()
        module.initialize({})
        result = module.execute(context)

        assert result.success is True
        assert "CONSTRUCTIE GUIDE" in result.content or "Bouw" in result.content.lower()

    def test_special_characters_handled(self):
        """Test handling of special characters in begrip."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "e-mail & web-based"
        context.enriched_context = None
        context.get_shared = MagicMock(return_value=None)

        module = DefinitionTaskModule()
        module.initialize({})
        result = module.execute(context)

        assert result.success is True
        assert context.begrip in result.content  # Special chars preserved
