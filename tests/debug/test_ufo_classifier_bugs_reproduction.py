"""
UFO Classifier Bug Reproduction Test Suite
===========================================
Dit bestand reproduceert de 5 kritieke bugs en 8 edge cases uit de debug analyse.

Run met:
    pytest tests/debug/test_ufo_classifier_bugs_reproduction.py -v

Status: XFAIL - Deze tests falen met de huidige implementatie!
Doel: Documentatie van bugs voor fixes.
"""

import logging
import signal
import time
import unicodedata
from typing import List, Tuple

import pytest

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
)

# ============================================================================
# BUG REPRODUCTIONS
# ============================================================================


class TestBug1InputValidation:
    """BUG-1: Geen input validatie - tests verwachten ValueError maar krijgen UNKNOWN."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    @pytest.mark.xfail(
        reason="BUG-1: Classifier retourneert UNKNOWN i.p.v. raising ValueError"
    )
    def test_empty_term_should_raise(self, classifier):
        """Empty term should raise ValueError, not return UNKNOWN."""
        with pytest.raises(ValueError, match="niet-lege"):
            classifier.classify("", "valid definition")

    @pytest.mark.xfail(reason="BUG-1: Same as above")
    def test_empty_definition_should_raise(self, classifier):
        """Empty definition should raise ValueError."""
        with pytest.raises(ValueError, match="niet-lege"):
            classifier.classify("valid term", "")

    @pytest.mark.xfail(reason="BUG-1: Same as above")
    def test_whitespace_only_should_raise(self, classifier):
        """Whitespace-only strings should raise ValueError."""
        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("   ", "valid definition")

        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("valid term", "\t\n\r")

    def test_current_buggy_behavior(self, classifier):
        """Document current (buggy) behavior."""
        # Currently returns UNKNOWN instead of raising
        result = classifier.classify("", "definition")
        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence == 0.1  # MIN_CONFIDENCE


class TestBug2NoneGuards:
    """BUG-2: Missing None guards - should raise TypeError."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    @pytest.mark.xfail(reason="BUG-2: None input returns empty string i.p.v. exception")
    def test_none_term_should_raise(self, classifier):
        """None term should raise ValueError."""
        with pytest.raises((ValueError, TypeError)):
            classifier.classify(None, "definition")

    @pytest.mark.xfail(reason="BUG-2: Same as above")
    def test_none_definition_should_raise(self, classifier):
        """None definition should raise ValueError."""
        with pytest.raises((ValueError, TypeError)):
            classifier.classify("term", None)

    @pytest.mark.xfail(reason="BUG-2: Same as above")
    def test_non_string_types_should_raise(self, classifier):
        """Non-string types should raise TypeError."""
        with pytest.raises(TypeError):
            classifier.classify(123, "definition")

        with pytest.raises(TypeError):
            classifier.classify("term", ["list", "of", "strings"])

        with pytest.raises(TypeError):
            classifier.classify({"term": "dict"}, "definition")

    def test_current_buggy_behavior_none(self, classifier):
        """Document current behavior with None."""
        # Currently: _normalize_text(None) returns ""
        # Then: empty string triggers UNKNOWN path
        result = classifier.classify(None, "definition")
        assert result.primary_category == UFOCategory.UNKNOWN


class TestBug3ScoreCalculation:
    """BUG-3: Score calculation kan leiden tot inconsistente confidence."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_high_ambiguity_reduces_confidence_inconsistently(self, classifier):
        """
        Test dat ambiguity penalty niet resulteert in secondary > primary confidence.

        Scenario:
        - Two categories both score 1.0 initially
        - Primary gets reduced by 20% (ambiguity penalty)
        - Secondary blijft 1.0 internally
        - Dit is inconsistent!
        """
        # Term dat multiple categories matcht
        result = classifier.classify(
            "procedure",
            "Een proces met behandeling en uitvoering als handeling bij gebeurtenis",
        )

        # Check internal consistency
        # (We kunnen dit niet direct testen zonder internal state access)
        # Maar we kunnen wel kijken naar secondary categories

        if result.secondary_categories:
            # Als er secondary categories zijn, moet confidence reflecteren dat het ambiguous is
            assert result.confidence < 0.9, (
                f"High ambiguity (secondary={result.secondary_categories}) "
                f"but confidence still {result.confidence}"
            )

    def test_disambiguation_boost_can_exceed_max(self, classifier):
        """
        Test dat disambiguation boost correct clamped wordt.

        Scenario:
        - Pattern matching: 0.8
        - Disambiguation: +0.3 = 1.1
        - Should clamp to 1.0
        """
        # Use "zaak" with context that triggers disambiguation
        result = classifier.classify(
            "rechtszaak", "Een rechtszaak met procedure en behandeling"
        )

        # Confidence should never exceed 1.0
        assert 0.0 <= result.confidence <= 1.0
        # Even if multiple patterns + disambiguation boost


class TestBug4RegexPerformance:
    """BUG-4: Regex performance op zeer lange teksten zonder timeout."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_regex_performance_large_text(self, classifier):
        """Test regex doesn't hang on large text."""

        def timeout_handler(signum, frame):
            msg = "Regex took too long"
            raise TimeoutError(msg)

        # Set 2 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)

        try:
            huge_text = "juridisch begrip " * 1000  # ~17k chars
            start = time.perf_counter()
            result = classifier.classify("test", huge_text)
            elapsed = (time.perf_counter() - start) * 1000

            signal.alarm(0)  # Cancel alarm

            # Should complete in reasonable time
            assert elapsed < 1000, f"Took {elapsed}ms for {len(huge_text)} chars"
            assert result is not None

        except TimeoutError:
            pytest.fail("Classification timed out - possible regex performance issue")
        finally:
            signal.alarm(0)

    @pytest.mark.xfail(
        reason="BUG-4: Geen ReDoS protection - kan hangen op pathological input"
    )
    def test_redos_protection(self, classifier):
        """Test protection against ReDoS (Regular expression Denial of Service)."""

        # Pathological input for certain regex patterns
        # (Current patterns are safe, but this tests if guards exist)
        evil_input = "a" * 5000 + "!"

        def timeout_handler(signum, frame):
            msg = "Regex took too long"
            raise TimeoutError(msg)

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)  # 1 second should be plenty

        try:
            result = classifier.classify(evil_input, evil_input)
            signal.alarm(0)
            assert result is not None
        except TimeoutError:
            pytest.fail("ReDoS vulnerability detected")
        finally:
            signal.alarm(0)


class TestBug5UnicodeNormalization:
    """BUG-5: Unicode normalization inconsistentie."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_zero_width_characters_not_removed(self, classifier):
        """
        BUG: Zero-width characters blijven staan na normalization.

        Huidige code doet alleen NFC normalization, geen cleanup van invisible chars.
        """
        term_with_zwsp = "test\u200b\u200c\u200d"  # Zero-width spaces
        result = classifier.classify(term_with_zwsp, "definitie")

        # These SHOULD be removed but currently are NOT
        # (Test will pass showing the bug)
        print(f"Term after normalization: {result.term!r}")
        print(f"Contains zero-width? {chr(0x200b) in result.term}")

        # Ideal behavior (currently fails):
        # assert "\u200b" not in result.term
        # assert result.term == "test"

    def test_bom_not_removed(self, classifier):
        """BOM (Byte Order Mark) should be removed but isn't."""
        term_with_bom = "\ufefftest"
        result = classifier.classify(term_with_bom, "definitie")

        print(f"Term with BOM: {result.term!r}")
        # Currently BOM stays: '\ufefftest'
        # Should be: 'test'

    def test_control_characters_not_removed(self, classifier):
        """Control characters should be removed (except tab/newline/return)."""
        term_with_control = "test\x00\x01\x02"  # NULL and control chars
        result = classifier.classify(term_with_control, "definitie")

        print(f"Term with control chars: {result.term!r}")
        # Currently: 'test\x00\x01\x02'
        # Should be: 'test'

    def test_nfc_nfd_consistency(self, classifier):
        """Test dat NFC en NFD input beide consistent behandeld worden."""
        # Composed form (NFC)
        nfc = "café"  # é as single character U+00E9
        # Decomposed form (NFD)
        nfd = "cafe\u0301"  # e + combining acute U+0301

        result_nfc = classifier.classify(nfc, "definitie")
        result_nfd = classifier.classify(nfd, "definitie")

        # Both should normalize to same form
        assert result_nfc.term == result_nfd.term
        print(f"NFC normalized: {result_nfc.term!r}")
        print(f"NFD normalized: {result_nfd.term!r}")


# ============================================================================
# EDGE CASE REPRODUCTIONS
# ============================================================================


class TestEdgeCase1AllScoresZero:
    """EDGE-1: Alle scores 0.0 - geen enkele pattern match."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_no_pattern_matches(self, classifier):
        """Wanneer geen enkel pattern matcht."""
        result = classifier.classify("xyzabc", "qwerty asdf jklö")

        assert result.primary_category == UFOCategory.UNKNOWN

        # ISSUE: DEFAULT_CONFIDENCE = 0.3 maar er is geen evidence!
        # Should be 0.0 or 0.05
        print(f"Confidence with no matches: {result.confidence}")
        assert result.confidence == 0.3  # Current behavior (problematic!)

        # Better behavior would be:
        # assert result.confidence <= 0.05


class TestEdgeCase2SingleHighScore:
    """EDGE-2: Eén score 1.0, rest 0.0."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_single_category_dominates(self, classifier):
        """Wanneer één category heel hoog scoort."""
        # Multiple KIND patterns: persoon, organisatie, document
        result = classifier.classify(
            "rechtspersoon",
            "Een natuurlijk persoon of organisatie met rechtspersoonlijkheid volgens document",
        )

        assert result.primary_category == UFOCategory.KIND
        assert result.confidence >= 0.8  # Should be high

        # Check no spurious secondary categories
        print(f"Secondary categories: {result.secondary_categories}")
        # With threshold 0.2, could have noise
        # Better threshold would be 0.35+


class TestEdgeCase3AllScoresEqual:
    """EDGE-3: Alle scores gelijk - perfecte ambiguity."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_perfect_ambiguity(self, classifier):
        """Wanneer alle categorieën even sterk scoren."""
        # Term designed to hit multiple categories equally
        result = classifier.classify(
            "status",
            "Een toestand waarbij een persoon een rol heeft in een procedure met verplichtingen",
            # toestand=PHASE, persoon=KIND, rol=ROLE, procedure=EVENT, verplichtingen=MODE
        )

        # Should have low confidence
        assert result.confidence <= 0.6
        # Should have secondary categories
        assert len(result.secondary_categories) >= 1

        # Test determinism
        result2 = classifier.classify("status", result.definition)
        assert (
            result.primary_category == result2.primary_category
        ), "Non-deterministic tie-breaking!"

    def test_tie_breaking_determinism(self, classifier):
        """Test dat tie-breaking deterministisch is."""
        term = "handeling"
        definition = "Een procedure die personen uitvoeren"

        # Run 5 times
        results = [classifier.classify(term, definition) for _ in range(5)]

        # All should be identical
        categories = [r.primary_category for r in results]
        assert len(set(categories)) == 1, f"Non-deterministic: {categories}"


class TestEdgeCase6EmptyAfterNormalization:
    """EDGE-6: Text wordt leeg na normalization."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    @pytest.mark.xfail(
        reason="EDGE-6: Whitespace-only treated as valid input, returns UNKNOWN"
    )
    def test_whitespace_only_after_strip(self, classifier):
        """Whitespace-only input should raise ValueError."""
        with pytest.raises(ValueError, match=r".+"):
            classifier.classify("test", "   \t\n\r   ")


class TestEdgeCase7VeryLongText:
    """EDGE-7: Zeer lange tekst (10000+ chars)."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_long_text_truncation(self, classifier, caplog):
        """Test dat lange tekst wordt getrunceerd met warning."""
        long_text = "juridisch begrip " * 1000  # ~17k chars

        with caplog.at_level(logging.WARNING):
            result = classifier.classify("test", long_text)

        # Should truncate
        assert len(result.definition) == 10000

        # ISSUE: Geen warning gelogd!
        print(f"Log messages: {caplog.text}")
        # Currently: geen warning
        # Should log: "Text truncated from X to 10000 chars"


class TestEdgeCase8UnicodeSpecialChars:
    """EDGE-8: Unicode special characters en emoji."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_emoji_handling(self, classifier):
        """Test emoji in juridische tekst."""
        result = classifier.classify(
            "🏛️ rechtbank", "De rechtbank ⚖️ is een juridische instantie"
        )

        # Should classify based on text, not emoji
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence > 0.3

        print(f"Term: {result.term}")
        print(f"Category: {result.primary_category}")

    def test_mixed_scripts(self, classifier):
        """Test gemixte writing systems."""
        result = classifier.classify(
            "test Α 中 א",  # Latin, Greek, Chinese, Hebrew
            "een begrip met mixed scripts",
        )

        assert result is not None
        assert result.primary_category in UFOCategory

    def test_rtl_text(self, classifier):
        """Test Right-to-Left text (Arabic, Hebrew)."""
        result = classifier.classify(
            "test",
            "hebrew: שלום arabic: السلام عليكم",  # RTL text
        )

        assert result is not None


# ============================================================================
# DISAMBIGUATION BUG REPRODUCTIONS
# ============================================================================


class TestDisambiguationBugs:
    """Test disambiguation logic edge cases."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_multiple_disambiguation_patterns_match(self, classifier):
        """
        Bug: Wanneer meerdere disambiguation patterns matchen, wordt alleen eerste gebruikt.

        Scenario:
        - "zaak" matched by: rechts (EVENT), dossier (KIND), eigendom (RELATOR)
        - Only first match gets +0.3 boost
        - Order-dependent = bias
        """
        result = classifier.classify(
            "zaak",
            "Een rechtszaak is een dossier met een nummer voor registratie van eigendom",
        )

        # Should handle all matches, not just first
        print(f"Primary: {result.primary_category} ({result.confidence})")
        print(f"Secondary: {result.secondary_categories}")

        # Current behavior: ambiguous, maar bias naar eerste match
        # Better: proportional boosting

    def test_disambiguation_introduces_bias(self, classifier):
        """Test dat disambiguation niet willekeurig primary category kiest."""
        # Run multiple times to check for bias
        results = []
        for _ in range(10):
            result = classifier.classify(
                "eigendom",
                "Het verkrijgen van eigendom door overdracht van een goed",
                # verkrijgen=EVENT, eigendom=RELATOR, goed=KIND
            )
            results.append(result.primary_category)

        # Should be deterministic
        assert len(set(results)) == 1, f"Biased disambiguation: {results}"


# ============================================================================
# CONFIDENCE FORMULA BUG REPRODUCTIONS
# ============================================================================


class TestConfidenceFormulaBugs:
    """Test confidence calculation issues."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_single_pattern_gets_too_high_confidence(self, classifier):
        """Single pattern match should have lower confidence."""
        result = classifier.classify("test", "een persoon")  # Only 1 KIND pattern

        print(f"Confidence for single pattern: {result.confidence}")

        # Single pattern = 0.4 confidence
        # Is dat te hoog voor "één enkel signaal"?
        # Overwegingen:
        # - Geen context
        # - Geen bevestiging
        # - Could be false positive
        #
        # Better: 0.4 * 0.7 (single pattern penalty) = 0.28

    def test_ambiguity_penalty_too_harsh(self, classifier):
        """Test of ambiguity penalty proportioneel is."""
        # High score, small margin
        result1 = classifier.classify(
            "test1", "persoon organisatie document rechtbank"  # Multiple KIND
        )

        # High score, large margin (na disambiguation)
        result2 = classifier.classify("zaak", "Een rechtszaak met procedure")

        print(f"Result1 (multi-pattern): {result1.confidence}")
        print(f"Result2 (disambiguation): {result2.confidence}")

        # Current: 20% flat reduction if margin < 0.1
        # Better: proportional to margin ratio


# ============================================================================
# SECURITY BUG REPRODUCTIONS
# ============================================================================


class TestSecurityBugs:
    """Test security edge cases."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_sql_injection_attempt(self, classifier):
        """Test dat SQL injection poging safe behandeld wordt."""
        dangerous = "'; DROP TABLE definities; --"

        result = classifier.classify(dangerous, "safe definition")

        # Should handle safely
        assert result is not None
        assert dangerous in result.term  # Preserved as-is, not executed

    def test_command_injection_attempt(self, classifier):
        """Test command injection bescherming."""
        dangerous = "$(rm -rf /)"

        result = classifier.classify(dangerous, "safe definition")

        assert result is not None
        # Should not execute anything

    def test_path_traversal_attempt(self, classifier):
        """Test path traversal bescherming."""
        dangerous = "../../etc/passwd"

        result = classifier.classify(dangerous, "safe definition")

        assert result is not None


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================


def test_bug_summary():
    """Print summary van bugs voor reporting."""
    print("\n" + "=" * 70)
    print("BUG REPRODUCTION SUMMARY")
    print("=" * 70)

    bugs = [
        "BUG-1: Input Validatie - ValueError expected, UNKNOWN returned",
        "BUG-2: None Guards - TypeError expected, silent failure",
        "BUG-3: Score Calculation - Inconsistent confidence bij ambiguity",
        "BUG-4: Regex Performance - Geen timeout protection",
        "BUG-5: Unicode Normalization - Incomplete cleanup",
    ]

    edge_cases = [
        "EDGE-1: All scores 0.0 - DEFAULT_CONFIDENCE te hoog (0.3)",
        "EDGE-2: Single high score - Geen quality check",
        "EDGE-3: All scores equal - Non-deterministic tie-breaking",
        "EDGE-6: Empty after norm - Treated as valid input",
        "EDGE-7: Very long text - No warning logged on truncation",
        "EDGE-8: Unicode special - Zero-width chars not removed",
    ]

    print("\nKRITIEKE BUGS:")
    for i, bug in enumerate(bugs, 1):
        print(f"{i}. {bug}")

    print("\nEDGE CASES:")
    for i, edge in enumerate(edge_cases, 1):
        print(f"{i}. {edge}")

    print("\nOPMERKING: Run met -v flag voor details:")
    print("  pytest tests/debug/test_ufo_classifier_bugs_reproduction.py -v")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
