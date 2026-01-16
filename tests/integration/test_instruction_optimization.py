"""
Validation Test Suite for Instruction Files Optimization (v5.0)

Tests validate that CLAUDE.md:
1. Contains all critical rules
2. Has proper structure for quick reference
3. Maintains key patterns and canonical names

Run with: pytest tests/integration/test_instruction_optimization.py -v
"""

import re
from pathlib import Path

import pytest

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def read_file_content(file_path: Path) -> str:
    """Read file content, return empty string if doesn't exist."""
    if not file_path.exists():
        return ""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def contains_pattern(content: str, pattern: str, case_sensitive: bool = True) -> bool:
    """Check if content contains pattern (regex or literal)."""
    flags = 0 if case_sensitive else re.IGNORECASE
    return bool(re.search(pattern, content, flags))


# ============================================================================
# FILE PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


# ============================================================================
# TEST 1: CRITICAL RULES PRESERVATION
# ============================================================================


class TestCriticalRulesPreservation:
    """Validate that all critical rules are preserved in CLAUDE.md v5.0."""

    def test_no_files_in_root_rule(self):
        """Rule 1: No files in project root."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r"No files in project root", case_sensitive=False
        ), "CLAUDE.md missing 'No files in project root' rule"

    def test_session_state_manager_rule(self):
        """Rule 2: SessionStateManager only."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r"SessionStateManager", case_sensitive=True
        ), "CLAUDE.md missing SessionStateManager rule"

    def test_database_location_rule(self):
        """Rule 3: Database location."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r"data/definities\.db", case_sensitive=True
        ), "CLAUDE.md missing database location rule"

    def test_no_backwards_compat_rule(self):
        """Rule 4: No backwards compatibility."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r"No backwards compatibility", case_sensitive=False
        ), "CLAUDE.md missing 'No backwards compatibility' rule"

    def test_approval_gate_rule(self):
        """Rule 5: Ask first for large changes."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r">100 lines.*>5 files", case_sensitive=False
        ), "CLAUDE.md missing approval gate rule (>100 lines OR >5 files)"


# ============================================================================
# TEST 2: CANONICAL NAMES
# ============================================================================


class TestCanonicalNames:
    """Validate canonical names are documented."""

    @pytest.mark.parametrize(
        "name",
        [
            "ValidationOrchestratorV2",
            "UnifiedDefinitionGenerator",
            "ModularValidationService",
            "SessionStateManager",
            "organisatorische_context",
            "juridische_context",
        ],
    )
    def test_canonical_name_present(self, name):
        """Each canonical name must be in CLAUDE.md."""
        content = read_file_content(CLAUDE_MD)
        assert name in content, f"CLAUDE.md missing canonical name: {name}"


# ============================================================================
# TEST 3: STRUCTURE VALIDATION
# ============================================================================


class TestStructure:
    """Validate CLAUDE.md has required sections."""

    @pytest.mark.parametrize(
        "section",
        [
            "Quick Reference",
            "Critical Rules",
            "Architecture",
            "Streamlit Patterns",
            "Canonical Names",
            "File Locations",
            "Code Style",
        ],
    )
    def test_section_exists(self, section):
        """Required sections must exist."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, rf"##.*{section}", case_sensitive=False
        ), f"CLAUDE.md missing section: {section}"


# ============================================================================
# TEST 4: KEY SERVICES TABLE
# ============================================================================


class TestKeyServicesTable:
    """Validate Key Services table contains required services."""

    @pytest.mark.parametrize(
        "service",
        [
            "ServiceContainer",
            "ValidationOrchestratorV2",
            "UnifiedDefinitionGenerator",
            "AIServiceV2",
            "SessionStateManager",
            "RuleCache",
        ],
    )
    def test_service_documented(self, service):
        """Each key service must be documented."""
        content = read_file_content(CLAUDE_MD)
        assert service in content, f"CLAUDE.md missing key service: {service}"


# ============================================================================
# TEST 5: STREAMLIT PATTERNS
# ============================================================================


class TestStreamlitPatterns:
    """Validate Streamlit patterns are documented."""

    def test_key_only_pattern(self):
        """Key-only widget pattern must be documented."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r"key.*only|Key-Only", case_sensitive=False
        ), "CLAUDE.md missing Key-Only Widget Pattern"

    def test_correct_example(self):
        """Correct example must show key-only usage."""
        content = read_file_content(CLAUDE_MD)
        assert contains_pattern(
            content, r'st\.text_area.*key="', case_sensitive=True
        ), "CLAUDE.md missing correct Streamlit example"


# ============================================================================
# TEST 6: IMPORT RULES
# ============================================================================


class TestImportRules:
    """Validate import rules are documented."""

    def test_services_cannot_import_ui(self):
        """Services layer cannot import ui."""
        content = read_file_content(CLAUDE_MD)
        # Check table row: | `services/` | ... | ui/, streamlit |
        assert contains_pattern(
            content, r"services.*ui.*streamlit", case_sensitive=False
        ), "CLAUDE.md missing services->ui import restriction"


# ============================================================================
# TEST 7: FILLER LANGUAGE REMOVAL
# ============================================================================


class TestFillerLanguageRemoval:
    """Validate that filler language has been removed."""

    @pytest.mark.parametrize(
        "filler_phrase",
        [
            "It's important to remember that",
            "Please note that",
            "You should be aware that",
            "It's critical to understand",
        ],
    )
    def test_no_filler(self, filler_phrase):
        """CLAUDE.md should not contain filler language."""
        content = read_file_content(CLAUDE_MD)
        assert not contains_pattern(
            content, re.escape(filler_phrase), case_sensitive=False
        ), f"CLAUDE.md contains filler language: '{filler_phrase}'"


# ============================================================================
# TEST 8: CONCISENESS
# ============================================================================


class TestConciseness:
    """Validate CLAUDE.md is reasonably concise."""

    def test_line_count(self):
        """CLAUDE.md should be under 350 lines for quick reading."""
        content = read_file_content(CLAUDE_MD)
        line_count = len(content.splitlines())
        assert (
            line_count <= 350
        ), f"CLAUDE.md too long: {line_count} lines (target: ≤350)"

    def test_has_code_examples(self):
        """CLAUDE.md should have code examples for clarity."""
        content = read_file_content(CLAUDE_MD)
        code_blocks = re.findall(r"```", content)
        assert len(code_blocks) >= 4, "CLAUDE.md should have at least 2 code blocks"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
