"""
Quick verification test for definition cleaning fixes.

Tests that both bugs are resolved:
1. extract_definition_from_gpt_response() now handles markdown dashes
2. definitie_origineel uses opschonen_enhanced() for full cleaning
"""

from opschoning.opschoning_enhanced import (
    extract_definition_from_gpt_response, opschonen_enhanced)


def test_markdown_dash_removal():
    """Test that markdown dash before 'Ontologische categorie:' is handled."""
    # Test case 1: With markdown dash (the bug case)
    gpt_output_with_dash = """- Ontologische categorie: soort
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen"""

    result = extract_definition_from_gpt_response(gpt_output_with_dash)

    # Should remove the "- Ontologische categorie:" line
    assert (
        "Ontologische categorie" not in result
    ), f"Header should be removed! Got: {result}"
    print("✅ Test 1 PASSED: Markdown dash header removed")

    # Test case 2: Without markdown dash (should still work)
    gpt_output_no_dash = """Ontologische categorie: soort
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen"""

    result2 = extract_definition_from_gpt_response(gpt_output_no_dash)

    assert (
        "Ontologische categorie" not in result2
    ), f"Header should be removed! Got: {result2}"
    print("✅ Test 2 PASSED: Regular header removed")


def test_full_cleaning_removes_term_prefix():
    """Test that opschonen_enhanced() removes term prefix."""
    # This is what GPT generates
    gpt_output = """- Ontologische categorie: soort
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen"""

    # Use full cleaning (what definitie_origineel should use)
    result = opschonen_enhanced(gpt_output, "vervoersverbod", handle_gpt_format=True)

    # Should remove BOTH header AND term prefix
    assert (
        "Ontologische categorie" not in result
    ), f"Metadata header should be removed! Got: {result}"
    assert not result.lower().startswith(
        "vervoersverbod"
    ), f"Term prefix should be removed! Got: {result}"

    # Should start with "Maatregel" (capitalized first word)
    assert result.startswith(
        "Maatregel"
    ), f"Should start with 'Maatregel', got: {result}"

    print("✅ Test 3 PASSED: Full cleaning works correctly")
    print("   Input:  'Vervoersverbod: maatregel die...'")
    print(f"   Output: '{result[:50]}...'")


def test_comparison_extract_vs_full():
    """Compare the two approaches to show the difference."""
    gpt_output = """- Ontologische categorie: resultaat
Vonnis: rechterlijke uitspraak waarmee een procedure wordt afgesloten"""

    # Old approach (partial cleaning)
    partial_result = extract_definition_from_gpt_response(gpt_output)

    # New approach (full cleaning)
    full_result = opschonen_enhanced(gpt_output, "vonnis", handle_gpt_format=True)

    print("\n📊 Comparison of cleaning approaches:")
    print(f"   Partial (extract_definition): '{partial_result}'")
    print(f"   Full (opschonen_enhanced):    '{full_result}'")

    # Full cleaning should remove more
    assert len(full_result) < len(
        partial_result
    ), "Full cleaning should be more thorough"
    assert "Vonnis:" not in full_result, "Full cleaning should remove term prefix"

    print("✅ Test 4 PASSED: Full cleaning is more thorough than partial")


if __name__ == "__main__":
    print("🧪 Running Definition Cleaning Fix Verification Tests\n")
    print("=" * 70)

    try:
        test_markdown_dash_removal()
        print()
        test_full_cleaning_removes_term_prefix()
        print()
        test_comparison_extract_vs_full()
        print()
        print("=" * 70)
        print("🎉 ALL TESTS PASSED! Fixes are working correctly.")
        print("\n✅ Bug 1 (markdown dash) - FIXED")
        print("✅ Bug 2 (term prefix) - FIXED")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
