"""
Unit tests voor de UFO Pattern Matcher (basis-dekking).
Focust op aanwezigheid van patronen en vocabulaire.
"""

import pytest

from src.services.ufo_pattern_matcher import PatternMatcher, UFOCategory, get_pattern_matcher


@pytest.mark.unit
def test_kind_category_has_patterns():
    pm = PatternMatcher()
    data = pm.get_patterns_for_category(UFOCategory.KIND)
    assert isinstance(data, dict)
    assert "patterns" in data and isinstance(data["patterns"], list)
    assert len(data["patterns"]) > 0, "KIND categorie moet patronen bevatten"
    # Negative patterns aanwezig voor disambiguatie
    assert "negative_patterns" in data and isinstance(data["negative_patterns"], list)


@pytest.mark.unit
def test_event_category_has_temporal_keywords():
    pm = get_pattern_matcher()
    data = pm.get_patterns_for_category(UFOCategory.EVENT)
    assert "temporal_keywords" in data
    assert "process_verbs" in data
    assert len(data["temporal_keywords"]) > 0


@pytest.mark.unit
def test_vocabulary_contains_strafrecht_terms():
    pm = PatternMatcher()
    vocab = pm.get_vocabulary_for_domain("strafrecht")
    assert "verdachte" in vocab
    assert "aangifte" in vocab


@pytest.mark.unit
def test_get_singleton_matcher():
    m1 = get_pattern_matcher()
    m2 = get_pattern_matcher()
    assert m1 is m2, "Singleton instance verwacht voor pattern matcher"

