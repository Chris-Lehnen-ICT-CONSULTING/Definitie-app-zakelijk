import pytest

pytestmark = pytest.mark.unit

from services.prompts.synonym_research_prompt import build_synonym_research_prompt


def test_prompt_bevat_term_en_json_instructie():
    system, user = build_synonym_research_prompt(term="verdachte")
    assert "verdachte" in user
    assert "json" in user.lower()
    assert "synoniem" in user.lower()
    assert "confidence" in user.lower()
    assert "rationale" in user.lower()


def test_prompt_bevat_geen_provider_of_modelnaam():
    # Kern van DEF-459: de prompt mag geen enkel model/provider hardcoderen.
    system, user = build_synonym_research_prompt(term="verdachte")
    haystack = (system + user).lower()
    for verboden in ("gpt-4", "gpt4", "gpt", "claude", "openai", "anthropic"):
        assert verboden not in haystack, f"verboden token in prompt: {verboden}"


def test_prompt_verwerkt_juridische_context():
    system, user = build_synonym_research_prompt(
        term="verdachte",
        juridische_context=["Wetboek van Strafvordering"],
    )
    assert "Wetboek van Strafvordering" in user


def test_prompt_zonder_context_is_geldig():
    system, user = build_synonym_research_prompt(term="besluit")
    assert isinstance(system, str) and system.strip()
    assert isinstance(user, str) and "besluit" in user


def test_prompt_verwerkt_definitie():
    _, user = build_synonym_research_prompt(
        term="verdachte", definitie="persoon tegen wie een vervolging is gericht"
    )
    assert "persoon tegen wie een vervolging is gericht" in user


def test_prompt_verwerkt_min_count():
    _, user = build_synonym_research_prompt(term="verdachte", min_count=3)
    assert "3" in user


def test_prompt_filtert_lege_context_items():
    # Lege strings in de lijst mogen geen kale "; "-prefix of lege context-regel geven.
    _, user = build_synonym_research_prompt(
        term="verdachte", juridische_context=["", "Awb"]
    )
    assert "Awb" in user
    assert ": ; " not in user  # geen lege prefix voor de eerste item


def test_prompt_zonder_geldige_context_geeft_geen_context_regel():
    _, user = build_synonym_research_prompt(term="verdachte", juridische_context=[""])
    assert "Relevante juridische context" not in user
