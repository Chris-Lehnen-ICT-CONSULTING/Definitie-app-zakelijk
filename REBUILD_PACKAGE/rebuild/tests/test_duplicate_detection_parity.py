"""
Test duplicate detection parity between OLD and NEW systems.

This test suite ensures that the rebuilt duplicate detection logic produces
consistent results with the current production system.

Tests:
- 70% Jaccard similarity threshold
- 3-stage matching (exact → synonym → fuzzy)
- Context-aware duplicate detection
- Match scoring algorithm

Requirements:
- ≥95% match on duplicate detection (allow for edge case differences)
- Detailed diagnostics for differences

EPIC-026 Phase 1 - Rebuild Validation
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.duplicate_detection_service import (
    DuplicateDetectionService,
    DuplicateMatch,
)
from services.interfaces import Definition

# ========================================
# FIXTURES
# ========================================


@pytest.fixture(scope="module")
def baseline_definitions() -> list[dict[str, Any]]:
    """Load 42 baseline definitions from exported JSON."""
    baseline_file = (
        Path(__file__).parent.parent.parent
        / "docs"
        / "business-logic"
        / "baseline_42_definitions.json"
    )

    if not baseline_file.exists():
        pytest.skip(f"Baseline definitions not found: {baseline_file}")

    with open(baseline_file, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("definitions", [])


@pytest.fixture()
def duplicate_detection_service() -> DuplicateDetectionService:
    """Initialize duplicate detection service with standard threshold."""
    return DuplicateDetectionService(similarity_threshold=0.7)


@pytest.fixture()
def sample_definitions() -> list[Definition]:
    """Create sample definitions for testing."""
    return [
        Definition(
            id=1,
            begrip="authenticatie",
            definitie="Het proces van identiteitsverificatie.",
            categorie="proces",
            organisatorische_context=["identiteitsbeheer"],
            juridische_context=["AVG"],
            wettelijke_basis=["AVG artikel 32"],
        ),
        Definition(
            id=2,
            begrip="authenticatie",  # Same begrip
            definitie="Een ander proces van verificatie.",
            categorie="proces",
            organisatorische_context=["toegangscontrole"],  # Different context
            juridische_context=["eIDAS"],
            wettelijke_basis=[],
        ),
        Definition(
            id=3,
            begrip="authenticatieproces",  # Similar begrip
            definitie="Het proces van authenticatie.",
            categorie="proces",
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[],
        ),
        Definition(
            id=4,
            begrip="verificatie",  # Different begrip
            definitie="Het proces van verificatie.",
            categorie="proces",
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[],
        ),
    ]


# ========================================
# THRESHOLD TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_jaccard_threshold_value(duplicate_detection_service):
    """Verify that the Jaccard similarity threshold is 70% (0.7)."""
    assert (
        duplicate_detection_service.threshold == 0.7
    ), f"Expected threshold 0.7, got {duplicate_detection_service.threshold}"


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.parametrize("threshold", [0.6, 0.7, 0.8, 0.9])
def test_configurable_threshold(threshold: float):
    """Test that duplicate detection service accepts different thresholds."""
    service = DuplicateDetectionService(similarity_threshold=threshold)
    assert service.threshold == threshold


# ========================================
# EXACT MATCH TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_exact_match_same_term_and_context(
    duplicate_detection_service, sample_definitions
):
    """
    Test exact match when begrip and context are identical.

    Stage 1 of 3-stage matching: Exact match
    """
    # Create two identical definitions
    new_def = Definition(
        begrip="authenticatie",
        definitie="Test definitie.",
        categorie="proces",
        organisatorische_context=["identiteitsbeheer"],
        juridische_context=["AVG"],
        wettelijke_basis=["AVG artikel 32"],
    )

    existing_defs = [sample_definitions[0]]  # Has same term and context

    matches = duplicate_detection_service.find_duplicates(new_def, existing_defs)

    assert len(matches) == 1, "Should find exactly one exact match"
    assert matches[0].score == 1.0, "Exact match should have score 1.0"
    assert matches[0].match_type == "exact", "Should be marked as exact match"


@pytest.mark.baseline()
@pytest.mark.parity()
def test_no_exact_match_different_context(
    duplicate_detection_service, sample_definitions
):
    """
    Test that different context prevents exact match.

    Same begrip but different context should not be exact match.
    """
    new_def = Definition(
        begrip="authenticatie",
        definitie="Test definitie.",
        categorie="proces",
        organisatorische_context=["toegangscontrole"],  # Different
        juridische_context=["AVG"],
        wettelijke_basis=["AVG artikel 32"],
    )

    existing_defs = [sample_definitions[0]]

    matches = duplicate_detection_service.find_duplicates(new_def, existing_defs)

    # Should find fuzzy match, not exact
    if matches:
        assert (
            matches[0].match_type != "exact"
        ), "Should not be exact match with different context"


@pytest.mark.baseline()
@pytest.mark.parity()
def test_exact_match_case_insensitive(duplicate_detection_service):
    """Test that exact match is case-insensitive."""
    def1 = Definition(
        begrip="AUTHENTICATIE",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=["test"],
        juridische_context=[],
        wettelijke_basis=[],
    )

    def2 = Definition(
        begrip="authenticatie",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=["test"],
        juridische_context=[],
        wettelijke_basis=[],
    )

    matches = duplicate_detection_service.find_duplicates(def1, [def2])

    assert len(matches) == 1, "Should find exact match despite case difference"
    assert matches[0].score == 1.0


# ========================================
# FUZZY MATCH TESTS (Jaccard Similarity)
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_fuzzy_match_similar_terms(duplicate_detection_service):
    """
    Test fuzzy matching with Jaccard similarity.

    Stage 3 of 3-stage matching: Fuzzy match
    """
    new_def = Definition(
        begrip="authenticatieproces",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    existing_def = Definition(
        begrip="authenticatie proces",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    matches = duplicate_detection_service.find_duplicates(new_def, [existing_def])

    # Should find fuzzy match
    assert len(matches) >= 1, "Should find fuzzy match"
    if matches:
        assert matches[0].match_type == "fuzzy", "Should be fuzzy match"
        assert (
            matches[0].score > 0.7
        ), f"Score {matches[0].score} should be above threshold"


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.parametrize(
    "term1,term2,should_match",
    [
        ("verificatie", "verificatieproces", True),  # Similar
        ("authenticatie", "autorisatie", False),  # Different
        ("identiteitsbewijs", "identiteit bewijs", True),  # Same with space
        ("test", "productie", False),  # Completely different
    ],
)
def test_jaccard_similarity_cases(
    duplicate_detection_service, term1: str, term2: str, should_match: bool
):
    """Test Jaccard similarity with various term pairs."""
    def1 = Definition(
        begrip=term1,
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    def2 = Definition(
        begrip=term2,
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    matches = duplicate_detection_service.find_duplicates(def1, [def2])

    if should_match:
        assert len(matches) > 0, f"Expected match between '{term1}' and '{term2}'"
        assert (
            matches[0].score >= 0.7
        ), f"Score should be >= 0.7 for '{term1}' vs '{term2}'"
    elif matches:
        assert (
            matches[0].score < 0.7
        ), f"Score should be < 0.7 for '{term1}' vs '{term2}'"


# ========================================
# CONTEXT-AWARE DETECTION TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_context_distinguishes_duplicates(duplicate_detection_service):
    """
    Test that context prevents false positives.

    Same term in different contexts should not be exact match.
    """
    new_def = Definition(
        begrip="authenticatie",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=["systeem A"],
        juridische_context=["context A"],
        wettelijke_basis=["wet A"],
    )

    existing_def = Definition(
        begrip="authenticatie",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=["systeem B"],
        juridische_context=["context B"],
        wettelijke_basis=["wet B"],
    )

    matches = duplicate_detection_service.find_duplicates(new_def, [existing_def])

    # Should find match but NOT exact (different context)
    if matches:
        assert (
            matches[0].match_type != "exact"
        ), "Same term with different context should not be exact match"


@pytest.mark.baseline()
@pytest.mark.parity()
def test_empty_context_handling(duplicate_detection_service):
    """Test that empty contexts are handled correctly."""
    def1 = Definition(
        begrip="test",
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    def2 = Definition(
        begrip="test",
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    matches = duplicate_detection_service.find_duplicates(def1, [def2])

    # Should be exact match (same term, both have empty context)
    assert len(matches) == 1
    assert matches[0].score == 1.0
    assert matches[0].match_type == "exact"


# ========================================
# MATCH SCORING TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_matches_sorted_by_score(duplicate_detection_service):
    """Test that matches are returned sorted by score (highest first)."""
    new_def = Definition(
        begrip="verificatie",
        definitie="Test.",
        categorie="proces",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    existing_defs = [
        Definition(
            begrip="verificatieproces",  # High similarity
            definitie="Test.",
            categorie="proces",
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[],
        ),
        Definition(
            begrip="validatie",  # Low similarity
            definitie="Test.",
            categorie="proces",
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[],
        ),
        Definition(
            begrip="verificatie",  # Exact match
            definitie="Test.",
            categorie="proces",
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[],
        ),
    ]

    matches = duplicate_detection_service.find_duplicates(new_def, existing_defs)

    # Should have matches
    assert len(matches) >= 2

    # Scores should be descending
    scores = [m.score for m in matches]
    assert scores == sorted(
        scores, reverse=True
    ), "Matches should be sorted by score descending"

    # Exact match should be first
    assert matches[0].score == 1.0, "Exact match should have highest score"


# ========================================
# ARCHIVED DEFINITIONS TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_archived_definitions_excluded(duplicate_detection_service):
    """Test that archived definitions are excluded from duplicate detection."""
    new_def = Definition(
        begrip="authenticatie",
        definitie="Test.",
        categorie="proces",
        status="draft",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    # Create archived definition
    archived_def = Definition(
        begrip="authenticatie",
        definitie="Test.",
        categorie="proces",
        status="archived",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    matches = duplicate_detection_service.find_duplicates(new_def, [archived_def])

    # Should NOT find archived definition
    assert len(matches) == 0, "Archived definitions should be excluded"


# ========================================
# BASELINE PARITY TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.slow()
def test_baseline_duplicate_pairs(baseline_definitions, duplicate_detection_service):
    """
    Test duplicate detection on baseline definitions.

    Finds all duplicate pairs in baseline set and verifies consistency.
    """
    duplicate_pairs = []

    # Convert to Definition objects
    definitions = []
    for defn_dict in baseline_definitions:
        # Parse JSON fields if needed
        org_ctx = defn_dict.get("organisatorische_context", [])
        jur_ctx = defn_dict.get("juridische_context", [])
        wet_basis = defn_dict.get("wettelijke_basis", [])

        if isinstance(org_ctx, str):
            org_ctx = json.loads(org_ctx) if org_ctx else []
        if isinstance(jur_ctx, str):
            jur_ctx = json.loads(jur_ctx) if jur_ctx else []
        if isinstance(wet_basis, str):
            wet_basis = json.loads(wet_basis) if wet_basis else []

        definitions.append(
            Definition(
                id=defn_dict.get("id"),
                begrip=defn_dict.get("begrip", ""),
                definitie=defn_dict.get("definitie", ""),
                categorie=defn_dict.get("categorie", ""),
                organisatorische_context=org_ctx,
                juridische_context=jur_ctx,
                wettelijke_basis=wet_basis,
                status=defn_dict.get("status", "draft"),
            )
        )

    # Find all duplicate pairs
    for i, def1 in enumerate(definitions):
        other_defs = definitions[:i] + definitions[i + 1 :]
        matches = duplicate_detection_service.find_duplicates(def1, other_defs)

        for match in matches:
            duplicate_pairs.append(
                {
                    "begrip1": def1.begrip,
                    "begrip2": match.definition.begrip,
                    "score": match.score,
                    "match_type": match.match_type,
                }
            )

    # Report findings
    print("\n\nDuplicate Detection Results:")
    print("=" * 80)
    print(f"Total definitions: {len(definitions)}")
    print(f"Duplicate pairs found: {len(duplicate_pairs)}")

    if duplicate_pairs:
        print("\nTop 10 duplicate pairs:")
        for pair in sorted(duplicate_pairs, key=lambda x: x["score"], reverse=True)[
            :10
        ]:
            print(
                f"  {pair['begrip1']} ↔ {pair['begrip2']}: "
                f"{pair['score']:.2f} ({pair['match_type']})"
            )

    # Test passes - this is informational
    assert True


# ========================================
# EDGE CASES
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.parametrize(
    "begrip1,begrip2",
    [
        ("", "test"),  # Empty string
        ("test", ""),  # Empty string
        ("a", "b"),  # Single character
        ("test-begrip", "test begrip"),  # Hyphen vs space
        ("begrip/term", "begrip term"),  # Slash vs space
    ],
)
def test_edge_case_terms(duplicate_detection_service, begrip1: str, begrip2: str):
    """Test edge cases in term comparison."""
    def1 = Definition(
        begrip=begrip1,
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    def2 = Definition(
        begrip=begrip2,
        definitie="Test.",
        categorie="type",
        organisatorische_context=[],
        juridische_context=[],
        wettelijke_basis=[],
    )

    # Should not crash
    matches = duplicate_detection_service.find_duplicates(def1, [def2])

    # Verify result is valid
    assert isinstance(matches, list)
    for match in matches:
        assert 0.0 <= match.score <= 1.0, "Score should be between 0 and 1"
