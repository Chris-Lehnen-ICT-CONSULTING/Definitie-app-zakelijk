"""
Unit tests voor OntologyValidator.

Test rules-based validatie van ontologische classificaties.
"""

import pytest

from src.services.classification.ontology_validator import OntologyValidator


@pytest.fixture()
def validator():
    """Validator instance."""
    return OntologyValidator()


class TestOntologyValidator:
    """Tests voor OntologyValidator."""

    def test_validate_type_with_strong_indicators(self, validator):
        """Test TYPE met sterke indicatoren - minimale warnings."""
        warnings = validator.validate(
            level="TYPE",
            begrip="appel",
            definitie="Een soort fruit dat is een categorie kernvruchten",
        )

        # Mogelijk warning over 'dat' (demonstratief), maar dat is mild
        # Belangrijkste is dat er geen GROTE red flags zijn
        assert (
            len(
                [
                    w
                    for w in warnings
                    if "anti-indicator" in w.lower() and "handeling" in w
                ]
            )
            == 0
        )

    def test_validate_type_with_anti_indicators(self, validator):
        """Test TYPE met anti-indicatoren - waarschuwingen."""
        warnings = validator.validate(
            level="TYPE",
            begrip="verwerking",
            definitie="De handeling waarbij documenten worden verwerkt",
        )

        # "handeling" is anti-indicator voor TYPE
        assert len(warnings) > 0
        assert any("anti-indicator" in w.lower() for w in warnings)

    def test_validate_exemplaar_with_specific_indicators(self, validator):
        """Test EXEMPLAAR met specifieke verwijzingen."""
        warnings = validator.validate(
            level="EXEMPLAAR",
            begrip="dit document",
            definitie="Deze specifieke instantie van een document",
        )

        assert warnings == []

    def test_validate_exemplaar_too_generic(self, validator):
        """Test EXEMPLAAR dat te generiek klinkt."""
        warnings = validator.validate(
            level="EXEMPLAAR",
            begrip="algemeen type document",
            definitie="Een algemeen document",
        )

        # "algemeen" en "type" zijn red flags voor EXEMPLAAR
        assert len(warnings) > 0
        assert any("generiek" in w.lower() for w in warnings)

    def test_validate_proces_with_strong_indicators(self, validator):
        """Test PROCES met sterke proces indicatoren."""
        warnings = validator.validate(
            level="PROCES",
            begrip="verificatie",
            definitie="De handeling van controleren en valideren",
        )

        assert warnings == []

    def test_validate_proces_for_static_object(self, validator):
        """Test PROCES voor statisch object - waarschuwing."""
        warnings = validator.validate(
            level="PROCES",
            begrip="document",
            definitie="Een schriftelijk stuk met informatie",
        )

        # "document" is statisch object, niet proces
        assert len(warnings) > 0
        assert any("statisch object" in w.lower() for w in warnings)

    def test_validate_resultaat_with_indicators(self, validator):
        """Test RESULTAAT met resultaat indicatoren."""
        warnings = validator.validate(
            level="RESULTAAT",
            begrip="verleende vergunning",
            definitie="Het resultaat dat is verkregen na afloop van de vergunning",
        )

        # Mogelijk domain warning over 'vergunning' (legal context), maar geen anti-indicators
        assert len([w for w in warnings if "anti-indicator" in w.lower()]) == 0

    def test_validate_resultaat_with_anti_indicators(self, validator):
        """Test RESULTAAT met proces anti-indicatoren."""
        warnings = validator.validate(
            level="RESULTAAT", begrip="proces", definitie="De activiteit van verwerken"
        )

        # "proces" en "activiteit" zijn anti-indicators voor RESULTAAT
        assert len(warnings) > 0
        assert any("anti-indicator" in w.lower() for w in warnings)

    def test_validate_onbeslist_no_warnings(self, validator):
        """Test dat ONBESLIST geen validatie triggert."""
        warnings = validator.validate(
            level="ONBESLIST",
            begrip="wat dan ook",
            definitie="Compleet random definitie met proces en type woorden",
        )

        # ONBESLIST should skip all validation
        assert warnings == []

    def test_domain_rule_biology_expects_type(self, validator):
        """Test domein regel voor biologische termen."""
        warnings = validator.validate(
            level="PROCES",  # Wrong - biologische term is meestal TYPE
            begrip="soort",
            definitie="Een taxonomische categorie in de biologie",
        )

        # Should warn about biology domain expecting TYPE
        assert len(warnings) > 0
        assert any("biology" in w.lower() or "soort" in w.lower() for w in warnings)

    def test_domain_rule_legal_procedure_expects_proces(self, validator):
        """Test domein regel voor juridische procedures."""
        warnings = validator.validate(
            level="TYPE",  # Wrong - procedure is meestal PROCES
            begrip="beroepsprocedure",
            definitie="De juridische procedure voor beroep",
        )

        # Should warn about legal_procedure domain expecting PROCES
        assert len(warnings) > 0
        assert any("procedure" in w.lower() for w in warnings)

    def test_get_pattern_matches_type(self, validator):
        """Test pattern matching voor TYPE."""
        matches = validator.get_pattern_matches(
            level="TYPE", text="Dit is een soort algemene categorie"
        )

        assert len(matches["strong_indicators"]) > 0
        assert "soort" in str(matches["strong_indicators"]).lower()

    def test_get_pattern_matches_proces(self, validator):
        """Test pattern matching voor PROCES."""
        matches = validator.get_pattern_matches(
            level="PROCES", text="De behandeling en verificatie van documenten"
        )

        assert len(matches["strong_indicators"]) > 0
        # Should match "behandeling" or "verificatie"

    def test_get_pattern_matches_anti_indicators(self, validator):
        """Test detectie van anti-indicators."""
        matches = validator.get_pattern_matches(
            level="TYPE", text="Deze specifieke handeling"
        )

        # "deze" en "handeling" zijn anti-indicators voor TYPE
        assert len(matches["anti_indicators"]) > 0

    def test_multiple_warnings_accumulate(self, validator):
        """Test dat meerdere validatie problemen geaccumuleerd worden."""
        warnings = validator.validate(
            level="TYPE",
            begrip="algemeen soort",
            definitie="Deze specifieke handeling betreft een proces van behandeling",
        )

        # Should have multiple warnings:
        # 1. Anti-indicators: "deze", "handeling", "proces"
        # 2. Mogelijk domain rules
        assert len(warnings) >= 2

    def test_validate_empty_definitie(self, validator):
        """Test validatie met lege definitie."""
        warnings = validator.validate(level="TYPE", begrip="test", definitie="")

        # Should warn about missing strong indicators
        assert len(warnings) > 0
        assert any("geen sterke" in w.lower() for w in warnings)

    def test_case_insensitive_matching(self, validator):
        """Test dat pattern matching case-insensitive is."""
        warnings1 = validator.validate(
            level="TYPE", begrip="Test", definitie="SOORT categorie"
        )

        warnings2 = validator.validate(
            level="TYPE", begrip="test", definitie="soort categorie"
        )

        # Beide moeten zelfde aantal warnings hebben
        assert len(warnings1) == len(warnings2)

    def test_patterns_exist_for_all_levels(self, validator):
        """Test dat alle levels patronen hebben gedefinieerd."""
        levels = ["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"]

        for level in levels:
            assert level in validator.PATTERNS
            assert "strong_indicators" in validator.PATTERNS[level]
            assert "anti_indicators" in validator.PATTERNS[level]

    def test_domain_rules_configured(self, validator):
        """Test dat domein regels geconfigureerd zijn."""
        assert len(validator.DOMAIN_RULES) > 0

        for domain, rule in validator.DOMAIN_RULES.items():
            assert "keywords" in rule
            assert "expected_level" in rule
            assert isinstance(rule["keywords"], list)
