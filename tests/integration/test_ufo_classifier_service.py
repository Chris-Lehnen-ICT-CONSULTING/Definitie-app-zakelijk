"""
Tests voor UFO Classifier Service.

Test de complete UFO classificatie functionaliteit inclusief:
- Alle 16 UFO categorieën
- Disambiguatie voor complexe termen
- Confidence berekeningen
- Pattern matching
- Juridische domein aanpassingen
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.services.ufo_classifier_service import (
    DisambiguationNote,
    PatternMatch,
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
)


class TestUFOClassifierService:
    """Test suite voor UFO Classifier Service."""

    @pytest.fixture()
    def classifier(self):
        """Maak een UFO classifier instance voor tests."""
        return UFOClassifierService()

    @pytest.fixture()
    def sample_definitions(self):
        """Sample definities voor verschillende UFO categorieën."""
        return {
            "Kind": {
                "term": "rechtspersoon",
                "definition": "Een rechtspersoon is een zelfstandige juridische entiteit die rechten en plichten kan hebben, zoals een BV, NV of stichting.",
            },
            "Event": {
                "term": "arrestatie",
                "definition": "Een arrestatie is de handeling waarbij een opsporingsambtenaar iemand van zijn vrijheid berooft tijdens het onderzoek naar een strafbaar feit.",
            },
            "Role": {
                "term": "verdachte",
                "definition": "Een persoon die in de hoedanigheid van verdachte wordt aangemerkt wanneer er redelijke verdenking bestaat dat hij een strafbaar feit heeft gepleegd.",
            },
            "Phase": {
                "term": "voorlopige hechtenis",
                "definition": "De fase waarin een verdachte in afwachting van zijn berechting in detentie wordt gehouden.",
            },
            "Relator": {
                "term": "koopovereenkomst",
                "definition": "Een overeenkomst tussen koper en verkoper waarbij de verkoper zich verbindt een zaak te geven en de koper om daarvoor een prijs in geld te betalen.",
            },
            "Mode": {
                "term": "bevoegdheid",
                "definition": "De eigenschap van een persoon of organisatie om bepaalde rechtshandelingen te mogen verrichten.",
            },
            "Quantity": {
                "term": "koopsom",
                "definition": "Het bedrag in euro's dat de koper aan de verkoper verschuldigd is voor de gekochte zaak.",
            },
            "Quality": {
                "term": "betrouwbaarheid",
                "definition": "De mate waarin een getuigenverklaring als waarheidsgetrouw kan worden beschouwd.",
            },
        }

    def test_initialization(self, classifier):
        """Test dat de classifier correct initialiseert."""
        assert classifier is not None
        assert len(classifier.domain_lexicons) > 0
        assert len(classifier.compiled_patterns) > 0
        assert classifier.stats["total_classifications"] == 0

    def test_classify_kind(self, classifier, sample_definitions):
        """Test classificatie van Kind entiteit."""
        sample = sample_definitions["Kind"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Kind"
        assert result.confidence > 0.5
        assert len(result.matched_patterns) > 0
        assert len(result.all_scores) == 8  # Minimaal 8 hoofdcategorieën
        assert result.detailed_explanation != ""

    def test_classify_event(self, classifier, sample_definitions):
        """Test classificatie van Event."""
        sample = sample_definitions["Event"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Event"
        assert result.confidence > 0.5
        assert any(p.category == "Event" for p in result.matched_patterns)
        assert "handeling" in result.detailed_explanation.lower()

    def test_classify_role(self, classifier, sample_definitions):
        """Test classificatie van Role."""
        sample = sample_definitions["Role"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Role"
        assert result.confidence > 0.5
        assert any("hoedanigheid" in p.matched_text for p in result.matched_patterns)

    def test_classify_phase(self, classifier, sample_definitions):
        """Test classificatie van Phase."""
        sample = sample_definitions["Phase"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Phase"
        assert result.confidence > 0.4
        assert "fase" in result.detailed_explanation.lower()

    def test_classify_relator(self, classifier, sample_definitions):
        """Test classificatie van Relator."""
        sample = sample_definitions["Relator"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Relator"
        assert result.confidence > 0.5
        assert any(p.category == "Relator" for p in result.matched_patterns)
        assert "tussen" in result.detailed_explanation.lower()

    def test_classify_mode(self, classifier, sample_definitions):
        """Test classificatie van Mode."""
        sample = sample_definitions["Mode"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Mode"
        assert result.confidence > 0.4
        assert "eigenschap" in result.detailed_explanation.lower()

    def test_classify_quantity(self, classifier, sample_definitions):
        """Test classificatie van Quantity."""
        sample = sample_definitions["Quantity"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Quantity"
        assert result.confidence > 0.5
        assert any(
            "euro" in str(p.matched_text).lower() for p in result.matched_patterns
        )

    def test_classify_quality(self, classifier, sample_definitions):
        """Test classificatie van Quality."""
        sample = sample_definitions["Quality"]
        result = classifier.classify(sample["term"], sample["definition"])

        assert result.primary_category == "Quality"
        assert result.confidence > 0.4
        assert "mate" in result.detailed_explanation.lower()

    def test_disambiguation_zaak(self, classifier):
        """Test disambiguatie voor de term 'zaak'."""
        # Test rechtszaak -> Event
        result1 = classifier.classify(
            "rechtszaak",
            "Een rechtszaak is een procedure voor de rechter waarin een juridisch geschil wordt beslecht.",
        )
        assert result1.primary_category == "Event"

        # Test roerende zaak -> Kind
        result2 = classifier.classify(
            "roerende zaak",
            "Een roerende zaak is een fysiek voorwerp dat verplaatst kan worden, zoals een auto of meubel.",
        )
        assert result2.primary_category == "Kind"

        # Check voor disambiguation notes
        if "zaak" in result2.detailed_explanation.lower():
            assert len(result2.disambiguation_notes) > 0

    def test_disambiguation_huwelijk(self, classifier):
        """Test disambiguatie voor de term 'huwelijk'."""
        # Test huwelijksvoltrekking -> Event
        result1 = classifier.classify(
            "huwelijksvoltrekking",
            "De ceremonie waarbij twee personen voor de wet in het huwelijk treden.",
        )
        assert result1.primary_category == "Event"

        # Test huwelijk als relatie -> Relator
        result2 = classifier.classify(
            "huwelijk",
            "Een huwelijk is een wettelijke verbintenis tussen twee personen met wederzijdse rechten en plichten.",
        )
        assert result2.primary_category == "Relator"

    def test_disambiguation_overeenkomst(self, classifier):
        """Test disambiguatie voor de term 'overeenkomst'."""
        result = classifier.classify(
            "overeenkomst",
            "Een contract waarbij partijen zich over en weer verbinden tot het verrichten van prestaties.",
        )
        assert result.primary_category == "Relator"
        assert result.confidence > 0.5

    def test_secondary_tags(self, classifier):
        """Test dat secundaire tags correct worden toegepast."""
        result = classifier.classify(
            "bijzondere overeenkomst",
            "Een specifiek type contract met bijzondere voorwaarden die afwijken van het algemene contractenrecht.",
        )

        assert len(result.secondary_tags) > 0
        # Mogelijk Subkind, Category of Abstract tag
        assert any(
            tag in ["Subkind", "Category", "Abstract"] for tag in result.secondary_tags
        )

    def test_domain_adjustments(self, classifier):
        """Test domein-specifieke aanpassingen."""
        # Strafrecht context
        strafrecht_context = {"juridische_context": ["Strafrecht"]}

        result = classifier.classify(
            "verdachte",
            "Persoon tegen wie een verdenking van een strafbaar feit bestaat.",
            context=strafrecht_context,
        )

        assert result.primary_category == "Role"
        # Check dat strafrecht boost is toegepast
        assert (
            "strafrecht" in result.detailed_explanation.lower()
            or result.confidence > 0.5
        )

    def test_low_confidence_manual_override(self, classifier):
        """Test dat lage confidence een manual override vereist."""
        # Gebruik een vage definitie die lage confidence zou moeten geven
        result = classifier.classify("iets", "Dit is een ding.")

        if result.confidence < 0.3:
            assert result.manual_override_required
            assert result.override_reason is not None

    def test_all_categories_evaluated(self, classifier):
        """Test dat alle categorieën worden geëvalueerd."""
        result = classifier.classify(
            "test begrip",
            "Een test definitie voor het controleren van de volledige evaluatie.",
        )

        # Check dat alle hoofdcategorieën een score hebben
        assert len(result.all_scores) >= 8
        assert UFOCategory.KIND.value in result.all_scores
        assert UFOCategory.EVENT.value in result.all_scores
        assert UFOCategory.ROLE.value in result.all_scores
        assert UFOCategory.PHASE.value in result.all_scores
        assert UFOCategory.RELATOR.value in result.all_scores
        assert UFOCategory.MODE.value in result.all_scores
        assert UFOCategory.QUANTITY.value in result.all_scores
        assert UFOCategory.QUALITY.value in result.all_scores

    def test_decision_path_complete(self, classifier):
        """Test dat het volledige beslispad wordt vastgelegd."""
        result = classifier.classify(
            "verdachte",
            "Een persoon die verdacht wordt van het plegen van een strafbaar feit.",
        )

        assert len(result.decision_path) >= 9  # Alle 9 stappen
        assert "1. Kind evaluatie" in result.decision_path[0]
        assert "9. Subcategorieën" in result.decision_path[8]

    def test_pattern_matching(self, classifier):
        """Test pattern matching functionaliteit."""
        result = classifier.classify(
            "koopsom",
            "Het bedrag van 50.000 euro dat betaald moet worden voor de woning.",
        )

        assert len(result.matched_patterns) > 0
        # Check voor euro pattern match
        assert any(
            "euro" in p.matched_text or "€" in p.pattern_text
            for p in result.matched_patterns
        )

    def test_processing_time_tracked(self, classifier):
        """Test dat processing tijd wordt bijgehouden."""
        result = classifier.classify("test", "Een simpele test definitie.")

        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 1000  # Moet onder 1 seconde zijn

    def test_statistics_updated(self, classifier):
        """Test dat statistieken worden bijgewerkt."""
        initial_total = classifier.stats["total_classifications"]

        classifier.classify("test1", "Definitie 1")
        classifier.classify("test2", "Definitie 2")

        assert classifier.stats["total_classifications"] == initial_total + 2
        assert classifier.stats["successful_classifications"] > initial_total

    def test_batch_classify(self, classifier, sample_definitions):
        """Test batch classificatie functionaliteit."""
        definitions = [
            (sample["term"], sample["definition"])
            for sample in sample_definitions.values()
        ]

        results = classifier.batch_classify(definitions)

        assert len(results) == len(definitions)
        assert all(isinstance(r, UFOClassificationResult) for r in results)
        assert all(
            r.primary_category in [cat.value for cat in UFOCategory] for r in results
        )

    def test_to_dict_serialization(self, classifier):
        """Test dat resultaten correct serialiseren naar dict."""
        result = classifier.classify(
            "rechtspersoon", "Een juridische entiteit met rechtspersoonlijkheid."
        )

        result_dict = result.to_dict()

        assert "primary_category" in result_dict
        assert "confidence" in result_dict
        assert "all_scores" in result_dict
        assert "matched_patterns" in result_dict
        assert "detailed_explanation" in result_dict
        assert isinstance(result_dict["matched_patterns"], list)

    def test_complex_legal_definitions(self, classifier):
        """Test complexe juridische definities."""
        complex_definitions = [
            {
                "term": "dwangsom",
                "definition": "Een geldsom die een schuldenaar moet betalen indien hij niet of niet tijdig aan een rechterlijke uitspraak voldoet.",
                "expected": ["Quantity", "Relator"],  # Kan beide zijn
            },
            {
                "term": "curator",
                "definition": "Persoon die door de rechtbank is aangesteld om het beheer te voeren over het vermogen van een failliet verklaarde.",
                "expected": ["Role"],
            },
            {
                "term": "bestuursorgaan",
                "definition": "Een orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld of een ander persoon of college met enig openbaar gezag bekleed.",
                "expected": ["Kind", "Role"],  # Kan beide aspecten hebben
            },
        ]

        for test_case in complex_definitions:
            result = classifier.classify(test_case["term"], test_case["definition"])
            assert result.primary_category in test_case["expected"]
            assert result.confidence > 0.3

    def test_confidence_thresholds(self, classifier):
        """Test confidence drempel configuratie."""
        # Hoge confidence
        result_high = classifier.classify(
            "rechtspersoon",
            "Een rechtspersoon is een zelfstandige juridische entiteit zoals een BV, NV of stichting met volledige rechtsbevoegdheid.",
        )
        assert result_high.confidence > 0.6

        # Lage confidence (vage definitie)
        result_low = classifier.classify("dinges", "Dat ding daar.")
        assert result_low.confidence < 0.6

    def test_empty_input_handling(self, classifier):
        """Test handling van lege input."""
        result = classifier.classify("", "")
        assert result.primary_category == "Kind"  # Default
        assert result.confidence == 0.0

    def test_very_long_definition(self, classifier):
        """Test handling van zeer lange definities."""
        long_definition = " ".join(
            ["Een zeer uitgebreide definitie die veel verschillende aspecten belicht"]
            * 50
        )

        result = classifier.classify("lang begrip", long_definition)
        assert result is not None
        assert result.processing_time_ms < 2000  # Max 2 seconden

    def test_special_characters_handling(self, classifier):
        """Test handling van speciale karakters."""
        result = classifier.classify(
            "test-begrip", "Een definitie met speciale karakters zoals €, %, & en @."
        )
        assert result is not None
        assert result.primary_category in [cat.value for cat in UFOCategory]

    def test_get_statistics(self, classifier):
        """Test statistieken ophalen."""
        # Doe enkele classificaties
        classifier.classify("test1", "Definitie 1")
        classifier.classify("test2", "Definitie 2")

        stats = classifier.get_statistics()

        assert "total_classifications" in stats
        assert "success_rate" in stats
        assert "average_confidence" in stats
        assert "most_common_category" in stats
        assert stats["total_classifications"] >= 2
        assert 0 <= stats["success_rate"] <= 1
