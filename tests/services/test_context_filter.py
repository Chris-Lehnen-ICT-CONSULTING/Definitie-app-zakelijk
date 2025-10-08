"""
Unit tests voor Comprehensive Fix B: Context filtering en relevance scoring.
"""

import pytest

from src.services.web_lookup.context_filter import ContextFilter, ContextMatch


class TestContextFilter:
    """Test suite voor ContextFilter."""

    def setup_method(self):
        """Setup voor elke test."""
        self.filter = ContextFilter()

    def test_match_context_no_context(self):
        """Test dat geen context geen matches geeft."""
        match = self.filter.match_context("Some random text")
        assert match.relevance_score == 0.0
        assert match.match_count == 0
        assert not match.has_org_match
        assert not match.has_jur_match
        assert not match.has_wet_match

    def test_match_context_org_om(self):
        """Test organisational match voor OM."""
        text = "Het Openbaar Ministerie heeft aangekondigd..."
        match = self.filter.match_context(text, org_context=["OM"])
        assert match.has_org_match
        assert "OM" in match.org_matches
        assert match.relevance_score == 0.2  # org weight
        assert match.match_count == 1

    def test_match_context_jur_strafrecht(self):
        """Test juridical domain match voor strafrecht."""
        text = "In strafrechtelijke procedures is het gebruikelijk..."
        match = self.filter.match_context(text, jur_context=["Strafrecht"])
        assert match.has_jur_match
        assert "Strafrecht" in match.jur_matches
        assert match.relevance_score == 0.3  # jur weight
        assert match.match_count == 1

    def test_match_context_wet_sv(self):
        """Test legal basis match voor Sv."""
        text = "Artikel 67 van het Wetboek van Strafvordering bepaalt..."
        match = self.filter.match_context(text, wet_context=["Sv"])
        assert match.has_wet_match
        assert "Sv" in match.wet_matches
        assert match.relevance_score == 0.5  # wet weight (highest)
        assert match.match_count == 1

    def test_match_context_multiple_matches(self):
        """Test multiple context matches verhogen score."""
        text = "Het Openbaar Ministerie vordert op grond van het Wetboek van Strafvordering in deze strafzaak..."
        match = self.filter.match_context(
            text, org_context=["OM"], jur_context=["Strafrecht"], wet_context=["Sv"]
        )
        assert match.has_org_match
        assert match.has_jur_match
        assert match.has_wet_match
        assert match.match_count == 3
        # Base: 0.2 (org) + 0.3 (jur) + 0.5 (wet) = 1.0
        # Bonus: +0.1 * (3-1) = +0.2, maar max 1.0
        assert match.relevance_score == 1.0

    def test_match_context_case_insensitive(self):
        """Test dat matching case-insensitive is."""
        text = "OPENBAAR MINISTERIE in STRAFZAAK"
        match = self.filter.match_context(
            text, org_context=["OM"], jur_context=["Strafrecht"]
        )
        assert match.has_org_match
        assert match.has_jur_match

    def test_match_context_abbreviations(self):
        """Test dat abbreviations ook matchen."""
        text = "De OM vordert op grond van Sv artikel 67..."
        match = self.filter.match_context(text, org_context=["OM"], wet_context=["Sv"])
        assert match.has_org_match
        assert match.has_wet_match
        assert match.relevance_score >= 0.7  # org + wet

    def test_filter_results_no_context(self):
        """Test dat zonder context alle results behouden blijven."""
        results = [
            {"title": "Result 1", "score": 0.8},
            {"title": "Result 2", "score": 0.6},
        ]
        filtered = self.filter.filter_results(results)
        assert len(filtered) == 2

    def test_filter_results_with_min_score(self):
        """Test dat min_score filtering werkt."""
        results = [
            {
                "title": "Relevant",
                "snippet": "Openbaar Ministerie Wetboek van Strafvordering",
                "score": 0.8,
            },
            {"title": "Irrelevant", "snippet": "Nothing related here", "score": 0.9},
        ]
        filtered = self.filter.filter_results(
            results, org_context=["OM"], wet_context=["Sv"], min_score=0.5
        )
        # Alleen eerste result heeft context match >= 0.5
        assert len(filtered) == 1
        assert filtered[0]["title"] == "Relevant"

    def test_filter_results_adds_context_match_metadata(self):
        """Test dat context match metadata wordt toegevoegd."""
        results = [
            {
                "title": "Test",
                "snippet": "Openbaar Ministerie strafrecht",
                "score": 0.8,
            }
        ]
        filtered = self.filter.filter_results(
            results, org_context=["OM"], jur_context=["Strafrecht"]
        )
        assert "context_match" in filtered[0]
        assert "relevance_score" in filtered[0]["context_match"]
        assert "match_count" in filtered[0]["context_match"]
        assert filtered[0]["context_match"]["match_count"] == 2

    def test_filter_results_sorts_by_relevance(self):
        """Test dat results gesorteerd worden op relevance score."""
        results = [
            {"title": "Low", "snippet": "Nothing relevant", "score": 0.9},
            {
                "title": "High",
                "snippet": "Openbaar Ministerie Sv strafrecht",
                "score": 0.5,
            },
            {"title": "Medium", "snippet": "Strafrecht", "score": 0.7},
        ]
        filtered = self.filter.filter_results(
            results,
            org_context=["OM"],
            jur_context=["Strafrecht"],
            wet_context=["Sv"],
        )
        # High heeft meeste context matches en moet eerst staan
        assert filtered[0]["title"] == "High"
        assert filtered[1]["title"] == "Medium"
        assert filtered[2]["title"] == "Low"

    def test_boost_score_no_match(self):
        """Test dat boost_score zonder match original score behoudt."""
        match = ContextMatch(relevance_score=0.0)
        boosted = self.filter.boost_score(0.7, match)
        assert boosted == 0.7

    def test_boost_score_with_match(self):
        """Test dat boost_score met match score verhoogt."""
        match = ContextMatch(relevance_score=0.8, match_count=2)
        boosted = self.filter.boost_score(0.6, match, boost_factor=0.3)
        # 0.6 + (0.8 * 0.3) = 0.6 + 0.24 = 0.84
        assert boosted == pytest.approx(0.84)

    def test_boost_score_capped_at_one(self):
        """Test dat boost_score gecapped is op 1.0."""
        match = ContextMatch(relevance_score=1.0, match_count=3)
        boosted = self.filter.boost_score(0.9, match, boost_factor=0.5)
        # 0.9 + (1.0 * 0.5) = 1.4, maar max 1.0
        assert boosted == 1.0

    def test_wet_pattern_matching_variations(self):
        """Test verschillende variaties van wet references."""
        test_cases = [
            ("Sv artikel 67", "Sv", True),
            ("Wetboek van Strafvordering", "Sv", True),
            ("strafvordering procedure", "Sv", True),
            ("Sr artikel 310", "Sr", True),
            ("Wetboek van Strafrecht", "Sr", True),
            ("AWB artikel 3:2", "Awb", True),
            ("Algemene wet bestuursrecht", "Awb", True),
            ("Rv artikel 21", "Rv", True),
            ("civiele procedure", "Rv", False),  # Rv pattern doesn't match this
        ]

        for text, wet_token, should_match in test_cases:
            match = self.filter.match_context(text, wet_context=[wet_token])
            if should_match:
                assert match.has_wet_match, f"Expected '{text}' to match {wet_token}"
            else:
                assert (
                    not match.has_wet_match
                ), f"Expected '{text}' NOT to match {wet_token}"

    def test_empty_results_list(self):
        """Test dat lege results list geen error geeft."""
        filtered = self.filter.filter_results([], org_context=["OM"])
        assert filtered == []

    def test_results_without_text_fields(self):
        """Test dat results zonder text fields niet crashen."""
        results = [{"score": 0.8}]  # No title, snippet, etc.
        filtered = self.filter.filter_results(results, org_context=["OM"])
        # Should not crash, but no matches expected
        assert len(filtered) == 1
        assert filtered[0]["context_match"]["relevance_score"] == 0.0
