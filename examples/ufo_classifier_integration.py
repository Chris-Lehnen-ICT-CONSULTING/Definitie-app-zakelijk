#!/usr/bin/env python3
"""
Integratie voorbeeld voor UFO Classifier in de Definitie App.

Dit voorbeeld toont hoe de UFO Classifier Service kan worden geïntegreerd
in de bestaande applicatie architectuur.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

import streamlit as st

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassificationResult,
    get_ufo_classifier,
)


class UFOClassifierIntegration:
    """
    Integratie klasse voor UFO Classifier in de Definitie App.

    Deze klasse toont hoe de classifier kan worden gebruikt in verschillende
    onderdelen van de applicatie.
    """

    def __init__(self):
        self.classifier = get_ufo_classifier()

    def classify_in_generator_tab(self, term: str, definition: str) -> dict[str, Any]:
        """
        Gebruik in de Generator Tab voor automatische suggestie.

        Args:
            term: Het gegenereerde begrip
            definition: De gegenereerde definitie

        Returns:
            Dictionary met categorie suggestie en UI elementen
        """
        # Classificeer het begrip
        result = self.classifier.classify(term, definition)

        # Bepaal UI feedback
        ui_data = {
            "category": result.primary_category.value,
            "confidence": result.confidence,
            "show_override": result.confidence
            < 0.6,  # Toon override optie bij lage confidence
            "confidence_color": self._get_confidence_color(result.confidence),
            "explanation": result.explanation,
            "secondary_tags": [tag.value for tag in result.secondary_tags],
        }

        # Log voor audit trail
        self._log_classification(term, result, "generator_tab")

        return ui_data

    def classify_in_edit_tab(
        self, term: str, definition: str, current_category: str | None = None
    ) -> dict[str, Any]:
        """
        Gebruik in de Edit Tab voor herclassificatie.

        Args:
            term: Het te bewerken begrip
            definition: De definitie
            current_category: Huidige categorie indien bekend

        Returns:
            Dictionary met classificatie en vergelijking
        """
        # Classificeer het begrip
        result = self.classifier.classify(term, definition)

        # Vergelijk met huidige categorie
        category_changed = False
        change_confidence = 0.0

        if current_category and current_category != result.primary_category.value:
            category_changed = True
            # Bereken zekerheid van de wijziging
            change_confidence = result.confidence

        return {
            "suggested_category": result.primary_category.value,
            "current_category": current_category,
            "category_changed": category_changed,
            "change_confidence": change_confidence,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "matched_patterns": result.matched_patterns,
        }

    def classify_batch_for_review(self, definitions: list) -> list:
        """
        Batch classificatie voor Expert Review Tab.

        Args:
            definitions: Lijst van (id, term, definition) tuples

        Returns:
            Lijst met classificatie resultaten voor review
        """
        review_items = []

        # Prepare batch
        batch = [(term, definition, None) for _, term, definition in definitions]

        # Classify in batch
        results = self.classifier.batch_classify(batch)

        # Process results for review
        for (def_id, term, definition), result in zip(
            definitions, results, strict=False
        ):
            review_item = {
                "id": def_id,
                "term": term,
                "definition": definition,
                "suggested_category": result.primary_category.value,
                "confidence": result.confidence,
                "needs_review": result.confidence < 0.5,  # Flag voor review
                "priority": self._calculate_review_priority(result),
                "explanation": result.explanation[0] if result.explanation else "",
            }
            review_items.append(review_item)

        # Sorteer op prioriteit (laagste confidence eerst)
        review_items.sort(key=lambda x: x["priority"])

        return review_items

    def integrate_with_validation_service(
        self, term: str, definition: str, validation_context: dict
    ) -> dict:
        """
        Integratie met de Validation Service voor contextrijke classificatie.

        Args:
            term: Het begrip
            definition: De definitie
            validation_context: Context van validatie service

        Returns:
            Verrijkte classificatie met validatie context
        """
        # Extract relevante context
        context = {
            "domain": validation_context.get("domain", "general"),
            "has_examples": bool(validation_context.get("voorbeelden")),
            "definition_length": len(definition),
            "validation_score": validation_context.get("score", 0),
        }

        # Classificeer met context
        result = self.classifier.classify(term, definition, context)

        # Combineer met validatie insights
        return {
            "category": result.primary_category.value,
            "confidence": result.confidence,
            "validation_aligned": self._check_validation_alignment(
                result.primary_category, validation_context
            ),
            "combined_score": (result.confidence + validation_context.get("score", 0))
            / 2,
            "recommendations": self._generate_recommendations(
                result, validation_context
            ),
        }

    def streamlit_ui_component(self) -> None:
        """
        Streamlit UI component voor UFO classificatie.

        Deze functie kan worden gebruikt in de Streamlit tabs.
        """
        st.subheader("🎯 UFO/OntoUML Categorie")

        # Haal definitie gegevens op
        term = st.session_state.get("current_term", "")
        definition = st.session_state.get("current_definition", "")

        if term and definition:
            # Classificeer
            result = self.classifier.classify(term, definition)

            # Toon resultaat
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                # Categorie met confidence indicator
                confidence_emoji = self._get_confidence_emoji(result.confidence)
                st.write(
                    f"**Categorie:** {result.primary_category.value} {confidence_emoji}"
                )

                # Uitleg
                if result.explanation:
                    with st.expander("Waarom deze categorie?"):
                        for exp in result.explanation:
                            st.write(f"• {exp}")

            with col2:
                # Confidence meter
                st.metric("Zekerheid", f"{result.confidence:.0%}")

            with col3:
                # Override optie
                if result.confidence < 0.6:
                    st.warning("⚠️ Lage zekerheid")
                    if st.button("Handmatig aanpassen"):
                        st.session_state["show_category_override"] = True

            # Secundaire tags
            if result.secondary_tags:
                st.write("**Aanvullende tags:**")
                tag_cols = st.columns(len(result.secondary_tags))
                for i, tag in enumerate(result.secondary_tags):
                    with tag_cols[i]:
                        st.info(tag.value)

            # Gevonden patronen (debug/transparency)
            if st.checkbox("Toon technische details"):
                st.json(result.to_dict())

        else:
            st.info(
                "Voer eerst een term en definitie in om de UFO categorie te bepalen."
            )

    def save_classification_to_database(
        self,
        definition_id: int,
        result: UFOClassificationResult,
        user_override: str | None = None,
    ) -> bool:
        """
        Sla classificatie op in de database.

        Args:
            definition_id: ID van de definitie
            result: Classificatie resultaat
            user_override: Eventuele handmatige override door gebruiker

        Returns:
            True als opslag succesvol
        """
        # Deze functie zou integreren met de DefinitionRepository
        # Voor nu een placeholder implementatie

        classification_data = {
            "definition_id": definition_id,
            "auto_category": result.primary_category.value,
            "confidence": result.confidence,
            "user_category": user_override,
            "is_manual": user_override is not None,
            "explanation": result.explanation,
            "matched_patterns": result.matched_patterns,
        }

        # TODO: Implementeer database opslag via DefinitionRepository
        print(f"Would save classification: {classification_data}")

        return True

    # Helper functies
    def _get_confidence_color(self, confidence: float) -> str:
        """Bepaal kleur op basis van confidence niveau."""
        if confidence >= 0.8:
            return "green"
        if confidence >= 0.5:
            return "orange"
        return "red"

    def _get_confidence_emoji(self, confidence: float) -> str:
        """Bepaal emoji op basis van confidence niveau."""
        if confidence >= 0.8:
            return "✅"
        if confidence >= 0.5:
            return "⚠️"
        return "❓"

    def _calculate_review_priority(self, result: UFOClassificationResult) -> float:
        """Bereken review prioriteit (lager = hogere prioriteit)."""
        # Laagste confidence heeft hoogste prioriteit
        return 1.0 - result.confidence

    def _check_validation_alignment(
        self, category: UFOCategory, validation_context: dict
    ) -> bool:
        """
        Check of categorie aligned is met validatie context.

        Bijvoorbeeld: Events zouden tijd-gerelateerde validatie issues kunnen hebben.
        """
        # Placeholder logica
        if category == UFOCategory.EVENT:
            return "temporal" in validation_context.get("issues", [])
        return True

    def _generate_recommendations(
        self, result: UFOClassificationResult, validation_context: dict
    ) -> list:
        """Genereer aanbevelingen op basis van classificatie en validatie."""
        recommendations = []

        if result.confidence < 0.5:
            recommendations.append("Consider manual review due to low confidence")

        if result.primary_category == UFOCategory.UNKNOWN:
            recommendations.append("Add more specific terms to improve classification")

        # Voeg categorie-specifieke aanbevelingen toe
        category_recommendations = {
            UFOCategory.EVENT: "Ensure temporal markers are present",
            UFOCategory.ROLE: "Verify that bearer/context is clearly defined",
            UFOCategory.RELATOR: "Check that multiple parties are identified",
            UFOCategory.QUANTITY: "Include units of measurement if applicable",
        }

        if result.primary_category in category_recommendations:
            recommendations.append(category_recommendations[result.primary_category])

        return recommendations

    def _log_classification(
        self, term: str, result: UFOClassificationResult, source: str
    ) -> None:
        """Log classificatie voor audit trail."""
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            f"UFO Classification - Term: {term}, "
            f"Category: {result.primary_category.value}, "
            f"Confidence: {result.confidence:.2f}, "
            f"Source: {source}"
        )


def main():
    """Demo van de integratie."""
    print("=" * 60)
    print("UFO CLASSIFIER INTEGRATION DEMO")
    print("=" * 60)

    integration = UFOClassifierIntegration()

    # Test 1: Generator Tab
    print("\n📝 Generator Tab Integration:")
    ui_data = integration.classify_in_generator_tab(
        "Verdachte",
        "Een persoon die wordt verdacht van het plegen van een strafbaar feit",
    )
    print(f"  Category: {ui_data['category']}")
    print(f"  Confidence: {ui_data['confidence']:.0%}")
    print(f"  Show override: {ui_data['show_override']}")

    # Test 2: Edit Tab
    print("\n✏️ Edit Tab Integration:")
    edit_data = integration.classify_in_edit_tab(
        "Contract",
        "Een overeenkomst tussen twee of meer partijen",
        current_category="Kind",
    )
    print(f"  Current: {edit_data['current_category']}")
    print(f"  Suggested: {edit_data['suggested_category']}")
    print(f"  Changed: {edit_data['category_changed']}")

    # Test 3: Batch Review
    print("\n👥 Batch Review:")
    test_definitions = [
        (1, "Persoon", "Een natuurlijk mens"),
        (2, "Proces", "Een reeks handelingen"),
        (3, "XYZ", "Onbekend begrip zonder context"),
    ]
    review_items = integration.classify_batch_for_review(test_definitions)
    for item in review_items:
        print(
            f"  [{item['id']}] {item['term']}: {item['suggested_category']} "
            f"({item['confidence']:.0%}) - Review: {item['needs_review']}"
        )

    # Test 4: Validation Integration
    print("\n🔍 Validation Service Integration:")
    validation_context = {
        "domain": "legal",
        "score": 0.85,
        "voorbeelden": ["Example 1", "Example 2"],
    }
    enhanced = integration.integrate_with_validation_service(
        "Dagvaarding",
        "Een oproep om voor de rechter te verschijnen",
        validation_context,
    )
    print(f"  Category: {enhanced['category']}")
    print(f"  Combined Score: {enhanced['combined_score']:.2f}")
    print(f"  Recommendations: {enhanced['recommendations']}")

    print("\n✅ Integration demo completed successfully!")


if __name__ == "__main__":
    main()
