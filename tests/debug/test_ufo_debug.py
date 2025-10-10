"""
Quick debug test for UFO Classifier issues
"""

from src.services.ufo_classifier_service import (UFOCategory,
                                                 UFOClassifierService)


def test_input_validation():
    """Test actual input validation behavior"""
    classifier = UFOClassifierService()

    print("\n=== Testing Input Validation ===")

    # Test empty strings
    print("\n1. Empty string test:")
    result = classifier.classify("", "valid definition")
    print(
        f"  Empty term result: {result.primary_category}, confidence: {result.confidence}"
    )

    # Test None
    print("\n2. None input test:")
    try:
        result = classifier.classify(None, "definition")
        print(
            f"  None term result: {result.primary_category}, confidence: {result.confidence}"
        )
    except Exception as e:
        print(f"  None term error: {type(e).__name__}: {e}")

    # Test non-string
    print("\n3. Non-string input test:")
    try:
        result = classifier.classify(123, "definition")
        print(
            f"  Number term result: {result.primary_category}, confidence: {result.confidence}"
        )
    except Exception as e:
        print(f"  Number term error: {type(e).__name__}: {e}")

    # Test extremely long input
    print("\n4. Long input test:")
    long_term = "x" * 15000
    long_def = "y" * 15000
    result = classifier.classify(long_term, long_def)
    print(
        f"  Long input truncated to: term={len(result.term)}, def={len(result.definition)}"
    )
    print(
        f"  MAX_TEXT_LENGTH constant: {classifier._normalize_text('x' * 15000) == 'x' * 10000}"
    )


def test_abstract_category():
    """Check if ABSTRACT category exists"""
    print("\n=== Testing ABSTRACT Category ===")
    categories = [c for c in UFOCategory]
    category_names = [c.name for c in categories]
    print(f"All categories: {category_names}")
    print(f"ABSTRACT in categories: {'ABSTRACT' in category_names}")


def test_division_by_zero():
    """Test division by zero scenario"""
    print("\n=== Testing Division by Zero ===")
    classifier = UFOClassifierService()

    # Create a term with no matches
    result = classifier.classify("zzzzz", "xxxxxx")
    print(
        f"No-match result: {result.primary_category}, confidence: {result.confidence}"
    )
    print(f"Explanation: {result.explanation}")


def test_config_loading():
    """Test config loading behavior"""
    print("\n=== Testing Config Loading ===")
    classifier = UFOClassifierService()

    print(f"Config path: {classifier.config_path}")
    print(f"Has config attribute: {hasattr(classifier, 'config')}")

    # Check if config is used at all
    from pathlib import Path

    classifier2 = UFOClassifierService(config_path=Path("/nonexistent/path.yaml"))
    print(f"Nonexistent config - created successfully: {classifier2 is not None}")


def test_memory_reference():
    """Test for potential memory issues"""
    print("\n=== Testing Memory References ===")
    import sys

    classifier = UFOClassifierService()

    # Check reference counting
    result1 = classifier.classify("test", "definition")
    ref_count1 = sys.getrefcount(result1)
    print(f"Result reference count: {ref_count1}")

    # Test compiled patterns sharing
    print(
        f"Compiled patterns are instance variable: {id(classifier.compiled_patterns)}"
    )
    classifier2 = UFOClassifierService()
    print(f"Second instance patterns ID: {id(classifier2.compiled_patterns)}")
    print(
        f"Patterns are shared: {id(classifier.compiled_patterns) == id(classifier2.compiled_patterns)}"
    )


def test_unicode_edge_cases():
    """Test Unicode handling edge cases"""
    print("\n=== Testing Unicode Edge Cases ===")
    classifier = UFOClassifierService()

    # Test various Unicode issues
    test_cases = [
        ("café", "test"),
        ("test\u200b", "zero-width space"),
        ("test\ufeff", "BOM"),
        ("🏛️", "emoji"),
        ("", "empty string"),
    ]

    for term, description in test_cases:
        try:
            result = classifier.classify(term, f"Definition for {description}")
            print(f"  {description}: OK - {result.primary_category}")
        except Exception as e:
            print(f"  {description}: ERROR - {type(e).__name__}: {e}")


def test_pattern_matching():
    """Test pattern matching issues"""
    print("\n=== Testing Pattern Matching ===")
    classifier = UFOClassifierService()

    # Test known classifications
    test_cases = [
        ("persoon", "Een natuurlijk persoon", UFOCategory.KIND),
        ("procedure", "Een proces dat wordt doorlopen", UFOCategory.EVENT),
        ("verdachte", "Persoon verdacht van misdrijf", UFOCategory.ROLE),
    ]

    for term, definition, expected in test_cases:
        result = classifier.classify(term, definition)
        match = result.primary_category == expected
        print(
            f"  {term}: Expected={expected.value}, Got={result.primary_category.value}, Match={match}"
        )


if __name__ == "__main__":
    test_input_validation()
    test_abstract_category()
    test_division_by_zero()
    test_config_loading()
    test_memory_reference()
    test_unicode_edge_cases()
    test_pattern_matching()

    print("\n=== Debug Test Complete ===")
