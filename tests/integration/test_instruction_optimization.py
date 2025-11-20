"""
Validation Test Suite for Instruction Files Optimization

Tests validate that optimized instruction files:
1. Preserve all critical rules
2. Reduce token count by ≥20%
3. Improve clarity and usability
4. Maintain backwards compatibility
5. Enable BMad lazy-loading

Run with: pytest tests/integration/test_instruction_optimization.py -v
"""

import re
from pathlib import Path

import pytest

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def count_tokens_estimate(file_path: Path) -> int:
    """
    Estimate token count for file.
    Rough estimate: ~1.3 tokens/word, ~6 words/line for markdown.
    For YAML: ~4 words/line.
    """
    if not file_path.exists():
        return 0

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    is_yaml = file_path.suffix in [".yaml", ".yml"]
    words_per_line = 4 if is_yaml else 6
    tokens_per_word = 1.3

    total_lines = len([line for line in lines if line.strip()])
    return int(total_lines * words_per_line * tokens_per_word)


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
CLAUDE_MD_V3 = PROJECT_ROOT / "CLAUDE.md"
CLAUDE_MD_V4 = PROJECT_ROOT / "CLAUDE.md.v4.0"
UNIFIED_V3 = Path.home() / ".ai-agents" / "UNIFIED_INSTRUCTIONS.md"
UNIFIED_V31 = Path.home() / ".ai-agents" / "UNIFIED_INSTRUCTIONS.md.v3.1"


# ============================================================================
# TEST 1: TOKEN REDUCTION
# ============================================================================


class TestTokenReduction:
    """Validate token count reduction targets."""

    def test_claude_md_token_reduction(self):
        """CLAUDE.md should reduce by ≥20% (target: 1,700 tokens from 8,500)."""
        v3_tokens = count_tokens_estimate(CLAUDE_MD_V3)
        v4_tokens = count_tokens_estimate(CLAUDE_MD_V4)

        reduction = v3_tokens - v4_tokens
        reduction_pct = (reduction / v3_tokens * 100) if v3_tokens > 0 else 0

        print("\nCLAUDE.md Token Reduction:")
        print(f"  v3.0: {v3_tokens} tokens")
        print(f"  v4.0: {v4_tokens} tokens")
        print(f"  Reduction: {reduction} tokens ({reduction_pct:.1f}%)")
        print("  Target: ≥20% (1,700 tokens)")

        assert (
            reduction_pct >= 18
        ), f"CLAUDE.md reduction {reduction_pct:.1f}% < target 20% (within 10% tolerance: 18%)"

    def test_unified_token_reduction(self):
        """UNIFIED should reduce by ≥20% (target: 1,518 tokens from 6,318)."""
        v3_tokens = count_tokens_estimate(UNIFIED_V3)
        v31_tokens = count_tokens_estimate(UNIFIED_V31)

        reduction = v3_tokens - v31_tokens
        reduction_pct = (reduction / v3_tokens * 100) if v3_tokens > 0 else 0

        print("\nUNIFIED Token Reduction:")
        print(f"  v3.0: {v3_tokens} tokens")
        print(f"  v3.1: {v31_tokens} tokens")
        print(f"  Reduction: {reduction} tokens ({reduction_pct:.1f}%)")
        print("  Target: ≥24% (1,518 tokens)")

        assert (
            reduction_pct >= 22
        ), f"UNIFIED reduction {reduction_pct:.1f}% < target 24% (within 10% tolerance: 22%)"


# ============================================================================
# TEST 2: CRITICAL RULES PRESERVATION
# ============================================================================


class TestCriticalRulesPreservation:
    """Validate that all critical rules are preserved."""

    @pytest.mark.parametrize(
        ("rule_name", "pattern"),
        [
            ("Project Root Policy", r"(NO|NEVER|FORBIDDEN).*files? in (project )?root"),
            ("SessionStateManager", r"SessionStateManager.*ONLY"),
            ("Approval Gate", r">100 lines.*>5 files"),
            ("No Backwards Compatibility", r"(NO|NEVER).*backwards compat"),
            ("Canonical Names", r"ValidationOrchestratorV2"),
            ("Forbidden Imports", r"import streamlit.*services"),
        ],
    )
    def test_claude_md_preserves_rule(self, rule_name, pattern):
        """CLAUDE.md v4.0 must preserve all critical rules."""
        content = read_file_content(CLAUDE_MD_V4)
        assert contains_pattern(
            content, pattern, case_sensitive=False
        ), f"CLAUDE.md v4.0 missing critical rule: {rule_name}"

    @pytest.mark.parametrize(
        ("rule_name", "pattern"),
        [
            ("Approval Ladder", r">100 lines.*>5 files"),
            ("Forbidden Patterns", r"(NO|NEVER).*import streamlit.*services"),
            ("Naming Conventions", r"organisatorische_context"),
            ("Workflow Selection", r"ANALYSIS.*HOTFIX.*FULL_TDD"),
            ("Vibe Coding", r"Archaeology First|Show Me First"),
        ],
    )
    def test_unified_preserves_rule(self, rule_name, pattern):
        """UNIFIED v3.1 must preserve all critical rules."""
        content = read_file_content(UNIFIED_V31)
        assert contains_pattern(
            content, pattern, case_sensitive=False
        ), f"UNIFIED v3.1 missing critical rule: {rule_name}"


# ============================================================================
# TEST 3: BMAD LAZY-LOAD NOTICE
# ============================================================================


class TestBMadLazyLoad:
    """Validate BMad lazy-load notices are present."""

    def test_claude_md_has_bmad_notice(self):
        """CLAUDE.md v4.0 must have BMad lazy-load notice."""
        content = read_file_content(CLAUDE_MD_V4)

        # Check for notice
        assert contains_pattern(
            content, r"BMad.*on-demand", case_sensitive=False
        ), "CLAUDE.md v4.0 missing BMad lazy-load notice"

        # Check for token warning
        assert contains_pattern(
            content, r"57K tokens|57,000 tokens|57,378 tokens", case_sensitive=False
        ), "CLAUDE.md v4.0 missing BMad token warning"

        # Check for invocation instruction
        assert contains_pattern(
            content, r"/BMad:agents:.*bmad-master", case_sensitive=False
        ), "CLAUDE.md v4.0 missing BMad invocation instruction"

    def test_unified_has_bmad_notice(self):
        """UNIFIED v3.1 must have BMad lazy-load notice in TL;DR."""
        content = read_file_content(UNIFIED_V31)

        # Check TL;DR section has notice
        tldr_section = re.search(r"## ⚡ TL;DR.*?(?=##|\Z)", content, re.DOTALL)
        assert tldr_section, "UNIFIED v3.1 missing TL;DR section"

        tldr_content = tldr_section.group(0)
        assert contains_pattern(
            tldr_content, r"BMad.*load ONLY", case_sensitive=False
        ), "UNIFIED v3.1 TL;DR missing BMad lazy-load notice"


# ============================================================================
# TEST 4: FILLER LANGUAGE REMOVAL
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
    def test_claude_md_no_filler(self, filler_phrase):
        """CLAUDE.md v4.0 should not contain filler language."""
        content = read_file_content(CLAUDE_MD_V4)
        assert not contains_pattern(
            content, re.escape(filler_phrase), case_sensitive=False
        ), f"CLAUDE.md v4.0 contains filler language: '{filler_phrase}'"

    @pytest.mark.parametrize(
        "filler_phrase",
        [
            "It's important to remember that",
            "Please note that",
            "Remember that",
        ],
    )
    def test_unified_no_filler(self, filler_phrase):
        """UNIFIED v3.1 should not contain filler language."""
        content = read_file_content(UNIFIED_V31)
        assert not contains_pattern(
            content, re.escape(filler_phrase), case_sensitive=False
        ), f"UNIFIED v3.1 contains filler language: '{filler_phrase}'"


# ============================================================================
# TEST 5: ACTION-ORIENTED LANGUAGE
# ============================================================================


class TestActionOrientedLanguage:
    """Validate action-oriented language conversion."""

    @pytest.mark.parametrize(
        "suggestive_phrase",
        [
            "You might consider",
            "It would be good to",
            "The agent should",
            "Try to",
        ],
    )
    def test_unified_no_suggestive_language(self, suggestive_phrase):
        """UNIFIED v3.1 should use imperative, not suggestive language."""
        content = read_file_content(UNIFIED_V31)

        # Allow in examples/anti-patterns sections
        content_without_examples = re.sub(
            r"(?:❌|⚠️).*?(?=\n|$)", "", content, flags=re.MULTILINE
        )

        assert not contains_pattern(
            content_without_examples, re.escape(suggestive_phrase), case_sensitive=False
        ), f"UNIFIED v3.1 contains suggestive language: '{suggestive_phrase}'"


# ============================================================================
# TEST 6: QUICK LOOKUP TABLES
# ============================================================================


class TestQuickLookupTables:
    """Validate Quick Lookup Tables structure."""

    def test_claude_md_has_10_tables(self):
        """CLAUDE.md v4.0 should have 10 Quick Lookup Tables."""
        content = read_file_content(CLAUDE_MD_V4)

        # Find Quick Lookup section
        quick_lookup = re.search(
            r"## 🔍 Quick Lookup Tables.*?(?=## |\Z)", content, re.DOTALL
        )
        assert quick_lookup, "CLAUDE.md v4.0 missing Quick Lookup Tables section"

        # Count tables (markdown tables start with |)
        tables_section = quick_lookup.group(0)

        # Each table has 1-2 header rows (header + separator), so count unique tables
        # Simplified: check for "### Table X" headings
        table_headings = re.findall(r"### Table \d+:", tables_section)

        print(f"\nQuick Lookup Tables found: {len(table_headings)}")
        assert (
            len(table_headings) >= 9
        ), f"CLAUDE.md v4.0 has {len(table_headings)} tables, target: 10 (±1 tolerance)"

    def test_tables_have_consistent_format(self):
        """Quick Lookup Tables should have consistent markdown format."""
        content = read_file_content(CLAUDE_MD_V4)

        # Find Quick Lookup section
        quick_lookup = re.search(
            r"## 🔍 Quick Lookup Tables.*?(?=## |\Z)", content, re.DOTALL
        )
        tables_section = quick_lookup.group(0) if quick_lookup else ""

        # Check for table format (| header | header |)
        table_rows = re.findall(r"^\|.*\|$", tables_section, re.MULTILINE)
        assert (
            len(table_rows) > 0
        ), "Quick Lookup Tables section contains no markdown tables"


# ============================================================================
# TEST 7: ULTRA-TL;DR SECTION
# ============================================================================


class TestUltraTLDR:
    """Validate ULTRA-TL;DR section exists and is concise."""

    def test_claude_md_has_ultra_tldr(self):
        """CLAUDE.md v4.0 should have ULTRA-TL;DR section."""
        content = read_file_content(CLAUDE_MD_V4)
        assert contains_pattern(
            content, r"## ⚡ ULTRA-TL;DR", case_sensitive=False
        ), "CLAUDE.md v4.0 missing ULTRA-TL;DR section"

    def test_ultra_tldr_is_concise(self):
        """ULTRA-TL;DR should be ≤200 words (30-second read)."""
        content = read_file_content(CLAUDE_MD_V4)

        # Extract ULTRA-TL;DR section
        ultra_tldr = re.search(r"## ⚡ ULTRA-TL;DR.*?(?=## |\Z)", content, re.DOTALL)
        assert ultra_tldr, "CLAUDE.md v4.0 missing ULTRA-TL;DR section"

        tldr_content = ultra_tldr.group(0)
        word_count = len(re.findall(r"\b\w+\b", tldr_content))

        print(f"\nULTRA-TL;DR word count: {word_count}")
        assert (
            word_count <= 250
        ), f"ULTRA-TL;DR too long: {word_count} words (target: ≤200, tolerance: 250)"


# ============================================================================
# TEST 8: PRECEDENCE METADATA
# ============================================================================


class TestPrecedenceMetadata:
    """Validate precedence metadata is present."""

    def test_unified_has_precedence_metadata(self):
        """UNIFIED v3.1 should have precedence metadata."""
        content = read_file_content(UNIFIED_V31)

        # Check for metadata block
        assert contains_pattern(
            content, r"precedence:\s*1", case_sensitive=False
        ), "UNIFIED v3.1 missing precedence metadata (precedence: 1)"

        # Check for overrides list
        assert contains_pattern(
            content, r"overrides:.*CLAUDE", case_sensitive=False
        ), "UNIFIED v3.1 missing overrides metadata"


# ============================================================================
# TEST 9: NO INFORMATION LOSS
# ============================================================================


class TestNoInformationLoss:
    """Validate no critical information was lost in optimization."""

    def test_all_canonical_names_preserved(self):
        """All canonical names from v3.0 must exist in v4.0."""
        canonical_names = [
            "ValidationOrchestratorV2",
            "UnifiedDefinitionGenerator",
            "ModularValidationService",
            "SessionStateManager",
            "organisatorische_context",
            "juridische_context",
        ]

        content = read_file_content(CLAUDE_MD_V4)

        for name in canonical_names:
            assert name in content, f"CLAUDE.md v4.0 missing canonical name: {name}"

    def test_all_file_locations_preserved(self):
        """All critical file locations must be preserved."""
        critical_locations = [
            "data/definities.db",
            "src/services/container.py",
            "src/ui/session_state.py",
            "tests/",
            "scripts/",
        ]

        content = read_file_content(CLAUDE_MD_V4)

        for location in critical_locations:
            assert (
                location in content
            ), f"CLAUDE.md v4.0 missing critical location: {location}"


# ============================================================================
# TEST 10: BACKWARDS COMPATIBILITY
# ============================================================================


class TestBackwardsCompatibility:
    """Validate backwards compatibility for existing prompts."""

    def test_section_headers_preserved(self):
        """Key section headers should be preserved for reference continuity."""
        critical_headers = [
            "Quick Lookup",
            "Critical Rules",
            "Architecture",
            "Streamlit",
            "Development",
        ]

        content = read_file_content(CLAUDE_MD_V4)

        for header in critical_headers:
            assert contains_pattern(
                content, header, case_sensitive=False
            ), f"CLAUDE.md v4.0 missing critical header: {header}"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
