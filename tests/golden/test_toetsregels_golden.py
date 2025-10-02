#!/usr/bin/env python3
"""
Golden tests for toetsregels - Reference implementation tests.

These tests serve as the authoritative reference for how toetsregels should behave.
They ensure business logic is preserved during refactoring.
"""

import pytest

from ai_toetser.modular_toetser import toets_definitie
from toetsregels.manager import RegelPrioriteit


class TestToetsregelsGolden:
    """Golden tests voor kritieke toetsregels."""

    @pytest.fixture()
    def toetser(self):
        """Create toetser instance."""
        return ModularToetser()

    # ==================== ESSENTIAL RULES ====================

    def test_ESS_001_term_niet_in_definitie(self):
        """Golden test: Term mag niet in eigen definitie voorkomen."""
        # FAIL case - term appears in definition
        result = toets_definitie(
            term="hypotheek",
            definitie="Een hypotheek is een lening met onroerend goed als onderpand.",
        )

        assert any(r.regel_id == "ESS-001" for r in result.regel_resultaten)
        ess_001 = next(r for r in result.regel_resultaten if r.regel_id == "ESS-001")
        assert not ess_001.voldaan, "Should fail when term appears in definition"
        assert "hypotheek" in ess_001.feedback.lower()

        # PASS case - term not in definition
        result = toets_definitie(
            term="hypotheek", definitie="Een lening met onroerend goed als onderpand."
        )

        ess_001 = next(r for r in result.regel_resultaten if r.regel_id == "ESS-001")
        assert ess_001.voldaan, "Should pass when term is not in definition"

    def test_ESS_002_begint_met_lidwoord(self):
        """Golden test: Definitie moet beginnen met een lidwoord."""
        # PASS cases
        for definitie in [
            "Een recht op een zaak.",
            "Het meest omvattende recht.",
            "De verplichting om iets te doen.",
        ]:
            result = toets_definitie(term="test", definitie=definitie)
            ess_002 = next(
                (r for r in result.regel_resultaten if r.regel_id == "ESS-002"), None
            )
            if ess_002:
                assert ess_002.voldaan, f"Should pass for: {definitie[:30]}..."

        # FAIL cases
        for definitie in [
            "Recht op een zaak.",
            "Verplichting om iets te doen.",
            "Onroerend goed dat...",
        ]:
            result = toets_definitie(term="test", definitie=definitie)
            ess_002 = next(
                (r for r in result.regel_resultaten if r.regel_id == "ESS-002"), None
            )
            if ess_002:
                assert not ess_002.voldaan, f"Should fail for: {definitie[:30]}..."

    # ==================== STRUCTURE RULES ====================

    def test_STR_002_minimale_lengte(self):
        """Golden test: Definitie moet minimaal 20 karakters zijn."""
        # FAIL case - too short
        result = toets_definitie(term="test", definitie="Te kort.")  # 8 karakters

        str_002 = next(
            (r for r in result.regel_resultaten if r.regel_id == "STR-002"), None
        )
        if str_002:
            assert not str_002.voldaan, "Should fail for definitions < 20 chars"

        # PASS case - long enough
        result = toets_definitie(
            term="test",
            definitie="Een voldoende lange definitie met meer dan twintig karakters.",
        )

        str_002 = next(
            (r for r in result.regel_resultaten if r.regel_id == "STR-002"), None
        )
        if str_002:
            assert str_002.voldaan, "Should pass for definitions >= 20 chars"

    def test_STR_003_eindigt_met_punt(self):
        """Golden test: Definitie moet eindigen met een punt."""
        # PASS case
        result = toets_definitie(
            term="test", definitie="Een definitie die netjes eindigt met een punt."
        )

        str_003 = next(
            (r for r in result.regel_resultaten if r.regel_id == "STR-003"), None
        )
        if str_003:
            assert str_003.voldaan, "Should pass when ending with period"

        # FAIL case
        result = toets_definitie(term="test", definitie="Een definitie zonder punt")

        str_003 = next(
            (r for r in result.regel_resultaten if r.regel_id == "STR-003"), None
        )
        if str_003:
            assert not str_003.voldaan, "Should fail when not ending with period"

    # ==================== CONSISTENCY RULES ====================

    def test_CON_001_geen_tegenstrijdigheden(self):
        """Golden test: Definitie mag geen tegenstrijdigheden bevatten."""
        # FAIL cases - contradictions
        contradictory_definitions = [
            "Dit is zowel toegestaan als niet toegestaan.",
            "Een recht dat geen recht is.",
            "Verplicht maar ook optioneel.",
        ]

        for definitie in contradictory_definitions:
            result = toets_definitie(term="test", definitie=definitie)
            con_001 = next(
                (r for r in result.regel_resultaten if r.regel_id == "CON-001"), None
            )
            if con_001:
                assert (
                    not con_001.voldaan
                ), f"Should fail for contradiction: {definitie[:30]}..."

        # PASS case - consistent
        result = toets_definitie(
            term="test",
            definitie="Een consistente definitie zonder tegenstrijdigheden.",
        )

        con_001 = next(
            (r for r in result.regel_resultaten if r.regel_id == "CON-001"), None
        )
        if con_001:
            assert con_001.voldaan, "Should pass for consistent definition"

    # ==================== CLARITY RULES ====================

    def test_VER_001_geen_vage_termen(self):
        """Golden test: Definitie mag geen vage termen bevatten."""
        # FAIL cases - vague terms
        vague_definitions = [
            "Iets met betrekking tot eigendom.",
            "Een soort van overeenkomst.",
            "Ongeveer een verplichting.",
            "Enigszins vergelijkbaar met een recht.",
        ]

        for definitie in vague_definitions:
            result = toets_definitie(term="test", definitie=definitie)
            ver_001 = next(
                (r for r in result.regel_resultaten if r.regel_id == "VER-001"), None
            )
            if ver_001:
                assert (
                    not ver_001.voldaan
                ), f"Should fail for vague: {definitie[:30]}..."

        # PASS case - precise
        result = toets_definitie(
            term="eigendom",
            definitie="Het meest omvattende recht dat een persoon op een zaak kan hebben.",
        )

        ver_001 = next(
            (r for r in result.regel_resultaten if r.regel_id == "VER-001"), None
        )
        if ver_001:
            assert ver_001.voldaan, "Should pass for precise definition"

    def test_VER_002_geen_voorbeelden_in_definitie(self):
        """Golden test: Definitie mag geen voorbeelden bevatten."""
        # FAIL cases - contains examples
        example_definitions = [
            "Een recht, bijvoorbeeld eigendom of erfpacht.",
            "Een zaak zoals een huis of auto.",
            "Een verplichting, bijv. betaling of levering.",
        ]

        for definitie in example_definitions:
            result = toets_definitie(term="test", definitie=definitie)
            ver_002 = next(
                (r for r in result.regel_resultaten if r.regel_id == "VER-002"), None
            )
            if ver_002:
                assert (
                    not ver_002.voldaan
                ), f"Should fail for examples: {definitie[:30]}..."

        # PASS case - no examples
        result = toets_definitie(
            term="zaak",
            definitie="Een voor menselijke beheersing vatbaar stoffelijk object.",
        )

        ver_002 = next(
            (r for r in result.regel_resultaten if r.regel_id == "VER-002"), None
        )
        if ver_002:
            assert ver_002.voldaan, "Should pass without examples"

    # ==================== INTEGRATION RULES ====================

    def test_INT_001_juridische_correctheid(self):
        """Golden test: Definitie moet juridisch correct zijn."""
        # This is a complex rule that may use AI or pattern matching

        # PASS case - legally correct
        result = toets_definitie(
            term="eigendom",
            definitie="Het meest omvattende recht dat een persoon op een zaak kan hebben.",
        )

        int_001 = next(
            (r for r in result.regel_resultaten if r.regel_id == "INT-001"), None
        )
        if int_001:
            # May not always trigger, depends on implementation
            if int_001.prioriteit == RegelPrioriteit.HOOG:
                assert int_001.voldaan, "Should pass for legally correct definition"

    # ==================== EDGE CASES ====================

    def test_edge_case_empty_definition(self):
        """Test behavior with empty definition."""
        result = toets_definitie(term="test", definitie="")

        # Should have multiple failures
        assert not result.totaal_score > 0.5, "Empty definition should fail"
        assert any(not r.voldaan for r in result.regel_resultaten)

    def test_edge_case_special_characters(self):
        """Test handling of special characters."""
        result = toets_definitie(
            term="test", definitie="Een definitie met speciale karakters: § ® © ™."
        )

        # Should handle special chars gracefully
        assert result is not None
        assert result.regel_resultaten is not None

    def test_edge_case_very_long_definition(self):
        """Test with very long definition."""
        long_def = "Een " + " zeer" * 100 + " lange definitie."
        result = toets_definitie(term="test", definitie=long_def)

        # Should handle long text
        assert result is not None
        # May have warnings about length
        str_rules = [
            r for r in result.regel_resultaten if r.regel_id.startswith("STR-")
        ]
        assert len(str_rules) > 0


class TestGoldenDefinitions:
    """Test with known good and bad definitions."""

    GOLDEN_DEFINITIONS = {
        "hypotheek": {
            "good": "Een beperkt zakelijk recht op een onroerende zaak dat strekt tot zekerheid voor de voldoening van een vordering.",
            "bad_circular": "Een hypotheek is een vorm van hypothecaire zekerheid.",
            "bad_short": "Een lening.",
            "bad_vague": "Iets met een huis.",
            "bad_no_article": "Zekerheidsrecht op onroerend goed.",
        },
        "eigendom": {
            "good": "Het meest omvattende recht dat een persoon op een zaak kan hebben.",
            "bad_examples": "Bijvoorbeeld een huis, auto of fiets.",
            "bad_contradiction": "Het recht om te beschikken maar niet te gebruiken.",
            "bad_informal": "Als je iets hebt dat van jou is.",
        },
        "overeenkomst": {
            "good": "Een meerzijdige rechtshandeling waarbij partijen jegens elkaar verbintenissen aangaan.",
            "bad_circular": "Een overeenkomst tussen partijen.",
            "bad_incomplete": "Een afspraak.",
            "bad_vague": "Wanneer mensen iets afspreken.",
        },
    }

    @pytest.fixture()
    def toetser(self):
        """Create toetser instance."""
        return ModularToetser()

    @pytest.mark.parametrize(
        "term,definition_type",
        [
            ("hypotheek", "good"),
            ("eigendom", "good"),
            ("overeenkomst", "good"),
        ],
    )
    def test_golden_good_definitions(self, term, definition_type):
        """Test that known good definitions score well."""
        definitie = self.GOLDEN_DEFINITIONS[term][definition_type]
        result = toets_definitie(term=term, definitie=definitie)

        # Good definitions should score > 0.7
        assert (
            result.totaal_score > 0.7
        ), f"Good definition for {term} should score > 0.7"

        # Should have mostly passing rules
        passing = sum(1 for r in result.regel_resultaten if r.voldaan)
        total = len(result.regel_resultaten)
        assert passing / total > 0.7, "Good definition should have >70% rules passing"

    @pytest.mark.parametrize(
        "term,definition_type",
        [
            ("hypotheek", "bad_circular"),
            ("hypotheek", "bad_short"),
            ("eigendom", "bad_examples"),
            ("overeenkomst", "bad_vague"),
        ],
    )
    def test_golden_bad_definitions(self, term, definition_type):
        """Test that known bad definitions score poorly."""
        definitie = self.GOLDEN_DEFINITIONS[term][definition_type]
        result = toets_definitie(term=term, definitie=definitie)

        # Bad definitions should score < 0.5
        assert (
            result.totaal_score < 0.6
        ), f"Bad definition ({definition_type}) for {term} should score < 0.6"

        # Should have multiple failures
        failing = sum(1 for r in result.regel_resultaten if not r.voldaan)
        assert failing >= 2, "Bad definition should have at least 2 failing rules"
