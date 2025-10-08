"""
UI Component voor Ontologische Classificatie Display.

Toont resultaten van OntologyClassifierService in Streamlit UI.
"""

import logging

import streamlit as st

from services.classification.ontology_classifier import ClassificationResult

logger = logging.getLogger(__name__)


class OntologyClassificationDisplay:
    """Display component voor ontologische classificatie resultaten."""

    # Emoji mapping voor categorieën
    CATEGORY_EMOJI = {
        "TYPE": "📦",
        "EXEMPLAAR": "🎯",
        "PROCES": "⚙️",
        "RESULTAAT": "✅",
        "ONBESLIST": "❓",
    }

    # Kleur mapping voor confidence levels
    CONFIDENCE_COLOR = {
        "high": "#28a745",  # Groen (>0.8)
        "medium": "#ffc107",  # Oranje (0.6-0.8)
        "low": "#dc3545",  # Rood (<0.6)
    }

    def __init__(self):
        """Initialiseer display component."""

    def render(
        self,
        result: ClassificationResult | None = None,
        show_details: bool = True,
        show_validation: bool = True,
    ):
        """
        Render classificatie resultaat in Streamlit.

        Args:
            result: ClassificationResult om te tonen (None = geen data)
            show_details: Toon linguïstische details
            show_validation: Toon validatie warnings
        """
        if result is None:
            st.info("Geen ontologische classificatie beschikbaar")
            return

        # Main classification display
        self._render_main_result(result)

        # Details sections
        if show_details:
            with st.expander("📊 Classificatie Details", expanded=False):
                self._render_details(result)

        if show_validation and result.validation_warnings:
            with st.expander("⚠️ Validatie Waarschuwingen", expanded=True):
                self._render_validation_warnings(result.validation_warnings)

    def _render_main_result(self, result: ClassificationResult):
        """Render hoofdresultaat met emoji en confidence."""
        emoji = self.CATEGORY_EMOJI.get(result.level, "❓")
        confidence_color = self._get_confidence_color(result.confidence)

        # Hoofdweergave
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                f"### {emoji} **{result.level}**",
                help=f"Ontologische categorie: {result.level}",
            )

        with col2:
            st.markdown(
                f"<div style='text-align: right; padding-top: 10px;'>"
                f"<span style='color: {confidence_color}; font-weight: bold; font-size: 1.2em;'>"
                f"{result.confidence:.0%}</span> "
                f"<span style='color: #666; font-size: 0.9em;'>confidence</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Rationale
        st.markdown(f"**Redenering:** {result.rationale}")

    def _render_details(self, result: ClassificationResult):
        """Render gedetailleerde informatie."""
        st.markdown("**Linguïstische Aanwijzingen:**")

        if result.linguistic_cues:
            for cue in result.linguistic_cues:
                st.markdown(f"- {cue}")
        else:
            st.info("Geen specifieke linguïstische aanwijzingen gevonden")

        # Metadata
        st.markdown("---")
        st.markdown("**Classificatie Metadata:**")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Categorie", result.level)

        with col2:
            st.metric("Betrouwbaarheid", f"{result.confidence:.1%}")

    def _render_validation_warnings(self, warnings: list):
        """Render validatie waarschuwingen."""
        st.markdown("De volgende waarschuwingen zijn gedetecteerd:")

        for warning in warnings:
            st.warning(warning)

        st.info(
            "💡 Deze waarschuwingen duiden op mogelijke inconsistenties "
            "tussen de classificatie en linguïstische patronen. "
            "Controleer of de classificatie correct is."
        )

    def _get_confidence_color(self, confidence: float) -> str:
        """Bepaal kleur gebaseerd op confidence score."""
        if confidence >= 0.8:
            return self.CONFIDENCE_COLOR["high"]
        elif confidence >= 0.6:
            return self.CONFIDENCE_COLOR["medium"]
        else:
            return self.CONFIDENCE_COLOR["low"]

    def render_compact(self, result: ClassificationResult | None):
        """
        Render compacte versie (voor inline display).

        Args:
            result: ClassificationResult om te tonen
        """
        if result is None:
            st.caption("Geen classificatie")
            return

        emoji = self.CATEGORY_EMOJI.get(result.level, "❓")
        confidence_color = self._get_confidence_color(result.confidence)

        st.markdown(
            f"{emoji} **{result.level}** "
            f"(<span style='color: {confidence_color};'>{result.confidence:.0%}</span>)",
            unsafe_allow_html=True,
        )

    def render_with_prompt_visibility(
        self, result: ClassificationResult, prompt_content: str | None = None
    ):
        """
        Render met mogelijkheid om gebruikte prompt te tonen.

        Args:
            result: ClassificationResult
            prompt_content: Gebruikte prompt tekst (voor transparency)
        """
        self.render(result)

        # Toon prompt voor transparency
        if prompt_content:
            with st.expander("🔍 Bekijk Gebruikte Prompt", expanded=False):
                st.code(prompt_content, language="yaml")
                st.caption(
                    "Deze prompt is gebruikt voor de LLM classificatie. "
                    "Dit zorgt voor transparantie over hoe de classificatie tot stand komt."
                )


def display_ontology_classification(
    result: ClassificationResult | None, mode: str = "full", **kwargs
) -> None:
    """
    Convenience functie voor ontology classification display.

    Args:
        result: ClassificationResult om te tonen
        mode: Display mode ("full", "compact", "with_prompt")
        **kwargs: Extra argumenten voor specifieke modes
    """
    display = OntologyClassificationDisplay()

    if mode == "full":
        display.render(result, **kwargs)
    elif mode == "compact":
        display.render_compact(result)
    elif mode == "with_prompt":
        display.render_with_prompt_visibility(result, **kwargs)
    else:
        raise ValueError(f"Unknown display mode: {mode}")
