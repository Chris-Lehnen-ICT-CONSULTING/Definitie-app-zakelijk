"""
PER-007 RED Phase Tests: Single Source of Truth
These tests MUST fail initially - proving multiple paths exist for context processing.
"""

import warnings
from unittest.mock import Mock, patch

import pytest


class TestSingleSourceOfTruth:
    """Tests that MUST fail initially - proving multiple paths exist"""

    @pytest.mark.red_phase
    def test_only_one_context_processing_path_exists(self):
        """MUST FAIL: Currently multiple paths exist for context processing"""
        # GIVEN: The application's context processing components
        import ast
        import os

        context_paths = []
        src_path = "src"

        # Scan for context processing functions
        for root, _dirs, files in os.walk(src_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            content = f.read()
                            if "build" in content and "context" in content:
                                tree = ast.parse(content)
                                for node in ast.walk(tree):
                                    if isinstance(node, ast.FunctionDef):
                                        if "context" in node.name.lower() and (
                                            "build" in node.name.lower()
                                            or "convert" in node.name.lower()
                                        ):
                                            context_paths.append(
                                                f"{filepath}:{node.name}"
                                            )
                    except:
                        pass

        # THEN: Only ONE path should exist (through DefinitionGeneratorContext)
        valid_paths = [p for p in context_paths if "definition_generator_context" in p]

        # This will FAIL - multiple paths currently exist
        assert len(context_paths) == len(valid_paths), (
            f"Found {len(context_paths)} total paths but only {len(valid_paths)} valid. "
            f"Multiple context routes exist: {context_paths[:5]}"
        )

    @pytest.mark.red_phase
    def test_legacy_context_manager_is_blocked(self):
        """MUST FAIL: Legacy context_manager should be blocked"""
        # GIVEN: Attempt to use legacy context manager
        try:
            # This should not exist or be marked deprecated
            from orchestration.context_manager import LegacyContextManager

            # If it imports, it should raise DeprecationWarning
            with pytest.warns(DeprecationWarning):
                LegacyContextManager()
        except ImportError:
            # Good - legacy manager doesn't exist
            pass
        else:
            pytest.fail("Legacy context manager still accessible without deprecation")

    @pytest.mark.red_phase
    def test_prompt_context_legacy_path_blocked(self):
        """MUST FAIL: Legacy prompt_context path should be blocked"""
        # Check for legacy prompt building paths
        legacy_methods = []

        # Check if old methods still exist
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()

        # These legacy methods should not exist
        if hasattr(service, "build_prompt_with_context"):
            legacy_methods.append("build_prompt_with_context")
        if hasattr(service, "_parse_context_string"):
            legacy_methods.append("_parse_context_string")
        if hasattr(service, "convert_legacy_context"):
            legacy_methods.append("convert_legacy_context")

        # This will FAIL if legacy methods still exist
        assert len(legacy_methods) == 0, f"Legacy methods still exist: {legacy_methods}"

    @pytest.mark.red_phase
    def test_no_direct_context_string_processing(self):
        """MUST FAIL: No service should directly process context strings"""
        # GIVEN: Services that might process context
        from services.definition_generator_context import HybridContextManager
        from services.prompts.prompt_service_v2 import PromptServiceV2

        # Check for string processing methods
        string_processors = []

        # Check PromptServiceV2
        service = PromptServiceV2()
        if hasattr(service, "_parse_context_string"):
            string_processors.append("PromptServiceV2._parse_context_string")

        # Check HybridContextManager
        manager = HybridContextManager()
        if hasattr(manager, "_parse_context_string"):
            # This one might be OK if it's internal only
            # But should be clearly marked as legacy/deprecated
            import inspect

            source = inspect.getsource(manager._parse_context_string)
            if "@deprecated" not in source and "legacy" not in source.lower():
                string_processors.append("HybridContextManager._parse_context_string")

        # This will FAIL if string processors exist without deprecation
        assert (
            len(string_processors) == 0
        ), f"Direct string processors still active: {string_processors}"

    @pytest.mark.red_phase
    def test_context_flow_has_single_entry_point(self):
        """MUST FAIL: Context should have single entry point"""
        # GIVEN: All possible entry points for context
        entry_points = []

        # Check for multiple ways to create context
        from services.definition_generator_context import (
            EnrichedContext,
            HybridContextManager,
        )

        # Method 1: Direct EnrichedContext creation
        try:
            EnrichedContext(
                base_context={},
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={},
            )
            entry_points.append("EnrichedContext.__init__")
        except:
            pass

        # Method 2: HybridContextManager
        try:
            HybridContextManager()
            entry_points.append("HybridContextManager")
        except:
            pass

        # Method 3: Through PromptService (should not create context)
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()
        if hasattr(service, "_convert_request_to_context"):
            entry_points.append("PromptServiceV2._convert_request_to_context")

        # This will FAIL - multiple entry points exist
        assert (
            len(entry_points) == 1
        ), f"Multiple context entry points: {entry_points}. Should only be HybridContextManager"

    @pytest.mark.red_phase
    def test_no_context_manipulation_in_ui_layer(self):
        """MUST FAIL: UI should not manipulate context data"""
        # GIVEN: UI components
        ui_violations = []

        # Check if UI components have context manipulation logic
        import os

        ui_path = "src/ui"

        if os.path.exists(ui_path):
            for root, _dirs, files in os.walk(ui_path):
                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, encoding="utf-8") as f:
                                content = f.read()
                                # UI should only display, not process
                                if (
                                    "_build_context" in content
                                    or "_parse_context" in content
                                    or "EnrichedContext(" in content
                                ):
                                    ui_violations.append(filepath)
                        except:
                            pass

        # This will FAIL if UI is doing context processing
        assert (
            len(ui_violations) == 0
        ), f"UI layer manipulating context in: {ui_violations}"
