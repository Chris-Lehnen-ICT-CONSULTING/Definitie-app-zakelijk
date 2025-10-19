"""
Pytest fixtures voor Web Lookup tests.

Provides:
- Mock LookupResult objecten
- Mock SynoniemenService met test data
- Sample juridische content
- Configuratie fixtures

Usage:
    from tests.fixtures.web_lookup_fixtures import mock_lookup_result

    def test_something(mock_lookup_result):
        result = mock_lookup_result(term="test", definition="definitie")
        assert result.term == "test"
"""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.services.web_lookup.synonym_service import JuridischeSynoniemlService

# =============================================================================
# Mock LookupResult Fixtures
# =============================================================================


@dataclass
class MockLookupResult:
    """
    Mock LookupResult voor testing.

    Simuleert de interface van een echte LookupResult zonder
    dependencies op de volledige service stack.
    """

    term: str
    definition: str
    source: MagicMock

    def __init__(
        self,
        term: str = "test_term",
        definition: str = "test definitie",
        url: str = "https://example.com",
        confidence: float = 0.5,
        is_juridical: bool = False,
    ):
        """
        Create mock lookup result.

        Args:
            term: Zoekterm
            definition: Definitie tekst
            url: Bron URL
            confidence: Confidence score (0.0 - 1.0)
            is_juridical: Of bron juridisch is
        """
        self.term = term
        self.definition = definition

        # Mock source object
        self.source = MagicMock()
        self.source.url = url
        self.source.confidence = confidence
        self.source.is_juridical = is_juridical


@pytest.fixture
def mock_lookup_result():
    """
    Factory fixture voor MockLookupResult.

    Usage:
        def test_something(mock_lookup_result):
            result = mock_lookup_result(term="test", definition="def")
    """
    return MockLookupResult


@pytest.fixture
def juridische_lookup_result(mock_lookup_result):
    """
    Pre-configured juridisch lookup result.

    Returns:
        MockLookupResult met juridische kenmerken
    """
    return mock_lookup_result(
        term="voorlopige hechtenis",
        definition="Artikel 12 Sv bepaalt voorlopige hechtenis voor strafzaken",
        url="https://www.rechtspraak.nl/uitspraken/123",
        confidence=0.7,
        is_juridical=True,
    )


@pytest.fixture
def wikipedia_lookup_result(mock_lookup_result):
    """
    Pre-configured Wikipedia lookup result.

    Returns:
        MockLookupResult van Wikipedia bron
    """
    return mock_lookup_result(
        term="voorlopige hechtenis",
        definition="Voorlopige hechtenis is een vorm van vrijheidsbeneming",
        url="https://nl.wikipedia.org/wiki/Voorlopige_hechtenis",
        confidence=0.6,
        is_juridical=False,
    )


@pytest.fixture
def mixed_lookup_results(juridische_lookup_result, wikipedia_lookup_result):
    """
    Lijst met mixed lookup results (juridisch + algemeen).

    Returns:
        List[MockLookupResult]
    """
    return [
        juridische_lookup_result,
        wikipedia_lookup_result,
        MockLookupResult(
            term="test",
            definition="Algemene definitie zonder juridische keywords",
            url="https://example.com",
            confidence=0.5,
        ),
    ]


# =============================================================================
# Synonym Service Fixtures
# =============================================================================


@pytest.fixture
def temp_synonym_yaml(tmp_path):
    """
    Create temporary YAML file met synoniemen.

    Returns:
        Path naar temporary YAML file

    Usage:
        def test_something(temp_synonym_yaml):
            yaml_path = temp_synonym_yaml(content="...")
    """

    def _create_yaml(content: str) -> Path:
        yaml_file = tmp_path / "test_synoniemen.yaml"
        yaml_file.write_text(content, encoding="utf-8")
        return yaml_file

    return _create_yaml


@pytest.fixture
def basic_synonym_yaml(temp_synonym_yaml):
    """
    Basic synoniemen YAML met veel voorkomende termen.

    Returns:
        Path naar YAML file
    """
    content = """
voorlopige_hechtenis:
  - voorarrest
  - bewaring
  - inverzekeringstelling

onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak

verdachte:
  - beklaagde
  - beschuldigde
  - aangeklaagde
"""
    return temp_synonym_yaml(content)


@pytest.fixture
def synonym_service_basic(basic_synonym_yaml):
    """
    JuridischeSynoniemlService met basic test data.

    Returns:
        JuridischeSynoniemlService instance
    """
    return JuridischeSynoniemlService(config_path=str(basic_synonym_yaml))


@pytest.fixture
def synonym_service_empty(tmp_path):
    """
    JuridischeSynoniemlService met lege database.

    Returns:
        JuridischeSynoniemlService met geen synoniemen
    """
    empty_yaml = tmp_path / "empty.yaml"
    empty_yaml.write_text("")
    return JuridischeSynoniemlService(config_path=str(empty_yaml))


@pytest.fixture
def synonym_service_extensive(temp_synonym_yaml):
    """
    JuridischeSynoniemlService met extensive test data (alle categorieën).

    Returns:
        JuridischeSynoniemlService met uitgebreide synoniemen database
    """
    content = """
# Strafrecht
voorlopige_hechtenis:
  - voorarrest
  - bewaring
  - inverzekeringstelling

dagvaarding:
  - oproeping
  - gerechtelijke oproeping

verdachte:
  - beklaagde
  - beschuldigde

# Procesrecht
hoger_beroep:
  - appel
  - appelprocedure

vonnis:
  - uitspraak
  - rechterlijke beslissing

# Bestuursrecht
beschikking:
  - besluit
  - bestuursrechtelijk besluit

bezwaar:
  - bezwaarschrift
  - bezwaarprocedure

# Burgerlijk recht
overeenkomst:
  - contract
  - verbintenis

schadevergoeding:
  - smartengeld
  - compensatie
"""
    return temp_synonym_yaml(content)


# =============================================================================
# Sample Content Fixtures
# =============================================================================


@pytest.fixture
def sample_juridische_definitie():
    """
    Sample juridische definitie met keywords, artikel refs, etc.

    Returns:
        str met juridische content
    """
    return (
        "Artikel 12 lid 2 Sv bepaalt dat de rechter een vonnis uitspreekt "
        "in strafrechtelijke zaken. Het wetboek van strafrecht regelt de "
        "procedure voor voorlopige hechtenis van de verdachte."
    )


@pytest.fixture
def sample_neutrale_definitie():
    """
    Sample neutrale definitie zonder juridische kenmerken.

    Returns:
        str met neutrale content
    """
    return (
        "Dit is een algemene definitie zonder specifieke juridische termen. "
        "Het beschrijft een concept in gewone taal voor algemeen publiek."
    )


@pytest.fixture
def sample_wikipedia_definitie():
    """
    Sample Wikipedia-stijl definitie (algemeen + wat juridische termen).

    Returns:
        str met Wikipedia-style content
    """
    return (
        "Voorlopige hechtenis is een vrijheidsbeneming in het Nederlandse "
        "strafrecht. Het wordt toegepast voordat een rechter een definitief "
        "vonnis heeft uitgesproken in een strafzaak."
    )


@pytest.fixture
def sample_rechtspraak_definitie():
    """
    Sample Rechtspraak.nl-stijl definitie (hoog juridisch).

    Returns:
        str met Rechtspraak.nl-style content
    """
    return (
        "Ingevolge artikel 63 lid 1 Sv kan de rechter-commissaris de "
        "voorlopige hechtenis van de verdachte bevelen indien er ernstige "
        "bezwaren tegen deze bestaan en aan de voorwaarden van artikel 67 "
        "Sv is voldaan. De rechtbank oordeelt dat de maatregel noodzakelijk "
        "is gezien de aard van het misdrijf en het gevaar voor herhaling."
    )


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def mock_web_lookup_config():
    """
    Mock web lookup configuratie.

    Returns:
        Dict met configuratie parameters
    """
    return {
        "providers": {
            "wikipedia": {
                "enabled": True,
                "weight": 0.7,
                "timeout": 5.0,
            },
            "sru": {
                "enabled": True,
                "weight": 1.0,
                "timeout": 10.0,
            },
        },
        "synonym_fallback": {
            "enabled": True,
            "max_synonyms": 3,
        },
        "juridische_ranking": {
            "enabled": True,
            "boost_factors": {
                "juridische_bron": 1.2,
                "artikel_ref": 1.15,
                "lid_ref": 1.05,
                "keywords_per_unit": 1.1,
                "keywords_max": 1.3,
            },
        },
        "circuit_breaker": {
            "enabled": True,
            "consecutive_empty_threshold": 2,
        },
    }


@pytest.fixture
def mock_sru_endpoints():
    """
    Mock SRU endpoints configuratie.

    Returns:
        Dict met SRU endpoint URLs
    """
    return {
        "overheid": "https://zoekservice.overheid.nl/sru",
        "rechtspraak": "https://data.rechtspraak.nl/sru",
        "wetgeving_nl": "https://wetgeving.nl/sru",
        "overheid_zoek": "https://repository.overheid.nl/sru",
    }


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def juridische_keywords_sample():
    """
    Sample set van juridische keywords voor testing.

    Returns:
        set van keywords
    """
    return {
        "wetboek",
        "artikel",
        "rechter",
        "vonnis",
        "strafrecht",
        "verdachte",
        "wet",
        "rechtbank",
        "uitspraak",
    }


@pytest.fixture
def juridische_domeinen_sample():
    """
    Sample set van juridische domeinen voor testing.

    Returns:
        set van domain names
    """
    return {
        "rechtspraak.nl",
        "overheid.nl",
        "wetgeving.nl",
        "wetten.overheid.nl",
    }


@pytest.fixture
def test_terms_strafrecht():
    """
    Test termen uit strafrecht domein.

    Returns:
        List van test termen
    """
    return [
        "voorlopige hechtenis",
        "verdachte",
        "dagvaarding",
        "onherroepelijk",
        "strafbaar feit",
        "schuldig",
    ]


@pytest.fixture
def test_terms_procesrecht():
    """
    Test termen uit procesrecht domein.

    Returns:
        List van test termen
    """
    return [
        "hoger beroep",
        "cassatie",
        "vonnis",
        "getuige",
        "bewijs",
        "procesdossier",
    ]


# =============================================================================
# Performance Testing Fixtures
# =============================================================================


@pytest.fixture
def large_synonym_database(temp_synonym_yaml):
    """
    Large synoniemen database voor performance testing.

    Returns:
        Path naar YAML met 100+ termen
    """
    # Generate 100 terms with 5 synoniemen each
    terms = []
    for i in range(100):
        terms.append(f"term_{i}:")
        for j in range(5):
            terms.append(f"  - syn_{i}_{j}")

    content = "\n".join(terms)
    return temp_synonym_yaml(content)


@pytest.fixture
def mock_slow_lookup_service():
    """
    Mock lookup service met simulated latency.

    Returns:
        Async mock function met delay
    """
    import asyncio

    async def slow_lookup(term: str, delay: float = 0.1):
        """Simulate slow lookup with delay."""
        await asyncio.sleep(delay)
        return [
            MockLookupResult(
                term=term,
                definition=f"Definitie voor {term}",
                url="https://example.com",
            )
        ]

    return slow_lookup


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def assert_boosted_higher():
    """
    Utility fixture voor asserting boost effects.

    Returns:
        Function die assert dat een result hoger geboost is
    """

    def _assert(
        original_confidence: float, boosted_confidence: float, min_boost: float = 1.1
    ):
        """Assert dat boost is toegepast."""
        actual_boost = (
            boosted_confidence / original_confidence if original_confidence > 0 else 0
        )
        assert actual_boost >= min_boost, (
            f"Expected boost >= {min_boost}x, got {actual_boost:.2f}x "
            f"(original: {original_confidence}, boosted: {boosted_confidence})"
        )

    return _assert


@pytest.fixture
def create_lookup_results():
    """
    Factory fixture voor het maken van multiple lookup results.

    Returns:
        Function die lijst van results maakt
    """

    def _create(count: int = 3, **kwargs) -> list[MockLookupResult]:
        """Create multiple lookup results."""
        results = []
        for i in range(count):
            result = MockLookupResult(
                term=kwargs.get("term", f"term_{i}"),
                definition=kwargs.get("definition", f"definitie {i}"),
                url=kwargs.get("url", f"https://example.com/{i}"),
                confidence=kwargs.get("confidence", 0.5 + (i * 0.1)),
            )
            results.append(result)
        return results

    return _create
