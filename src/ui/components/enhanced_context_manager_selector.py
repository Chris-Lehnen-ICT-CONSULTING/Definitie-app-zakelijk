"""
Enhanced Context Selector using ContextManager instead of session state.
Properly handles custom "Anders..." options and ensures they're passed to prompts and web lookup.
"""

import logging
from typing import Any

import streamlit as st

from services.context.context_manager import ContextSource, get_context_manager
from validation.sanitizer import (
    ContentType,
    SanitizationLevel,
    get_sanitizer,
)

logger = logging.getLogger(__name__)


class EnhancedContextManagerSelector:
    """Context selector that uses ContextManager for all state management."""

    # Base options for each context type
    ORG_OPTIONS = [
        "OM",
        "ZM",
        "Reclassering",
        "DJI",
        "NP",
        "Justid",
        "KMAR",
        "FIOD",
        "CJIB",
        "Strafrechtketen",
        "Migratieketen",
        "Justitie en Veiligheid",
    ]

    JUR_OPTIONS = [
        "Strafrecht",
        "Civiel recht",
        "Bestuursrecht",
        "Internationaal recht",
        "Europees recht",
        "Migratierecht",
    ]

    WET_OPTIONS = [
        "Wetboek van Strafrecht",
        "Wetboek van Strafvordering",
        "Wet op de rechterlijke organisatie",
        "Algemene wet bestuursrecht",
        "Burgerlijk Wetboek",
        "Wetboek van Burgerlijke Rechtsvordering",
        "Vreemdelingenwet",
        "Uitvoeringswet EU-richtlijnen",
        "Europees Verdrag voor de Rechten van de Mens",
    ]

    def __init__(self):
        """Initialize with ContextManager and sanitizer."""
        self.context_manager = get_context_manager()
        self.sanitizer = get_sanitizer()
        self.max_custom_length = 200

    def render(self) -> dict[str, Any]:
        """
        Render the context selector interface.

        Returns:
            Dictionary with selected context data that will be used in prompts and web lookup
        """
        st.markdown("### 🎯 Context Configuratie")

        # Get current context from ContextManager
        current_context = self.context_manager.get_context()
        current_data = current_context.to_dict() if current_context else {}

        col1, col2, col3 = st.columns(3)

        # Organisatorische Context
        with col1:
            org_context = self._render_context_selector(
                title="📋 Organisatorische context",
                base_options=self.ORG_OPTIONS,
                current_values=current_data.get("organisatorische_context", []),
                custom_key="custom_org_input",
                multiselect_key="org_multiselect",
                help_text="Selecteer één of meerdere organisaties",
            )

        # Juridische Context
        with col2:
            jur_context = self._render_context_selector(
                title="⚖️ Juridische context",
                base_options=self.JUR_OPTIONS,
                current_values=current_data.get("juridische_context", []),
                custom_key="custom_jur_input",
                multiselect_key="jur_multiselect",
                help_text="Selecteer relevante rechtsgebieden",
            )

        # Wettelijke Basis
        with col3:
            wet_context = self._render_context_selector(
                title="📜 Wettelijke basis",
                base_options=self.WET_OPTIONS,
                current_values=current_data.get("wettelijke_basis", []),
                custom_key="custom_wet_input",
                multiselect_key="wet_multiselect",
                help_text="Selecteer relevante wetgeving",
            )

        # Build complete context data
        context_data = {
            "organisatorische_context": org_context,
            "juridische_context": jur_context,
            "wettelijke_basis": wet_context,
        }

        # Store in ContextManager
        self.context_manager.set_context(
            context_data,
            source=ContextSource.UI,
            actor="user",
        )

        # Display current context summary
        self._render_context_summary(context_data)

        return context_data

    def _render_context_selector(
        self,
        title: str,
        base_options: list[str],
        current_values: list[str],
        custom_key: str,
        multiselect_key: str,
        help_text: str,
    ) -> list[str]:
        """
        Render a single context selector with Anders... option.

        Args:
            title: Title for the selector
            base_options: Base predefined options
            current_values: Current selected values from ContextManager
            custom_key: Key for custom input field
            multiselect_key: Key for multiselect widget
            help_text: Help text for the selector

        Returns:
            List of selected values including custom entries
        """
        # Clean up old session state values to prevent conflicts
        # Map multiselect keys to session state keys
        session_key_map = {
            "org_multiselect": "org_context_values",
            "jur_multiselect": "jur_context_values",
            "wet_multiselect": "wet_basis_values",
        }

        session_key = session_key_map.get(multiselect_key)
        if session_key and session_key in st.session_state:
            # Clean up the session state to prevent conflicts
            del st.session_state[session_key]
            logger.debug(f"Cleaned up session state key: {session_key}")

        # Also clean up the global multiselect keys (legacy) and any namespaced variants
        for key_variant in [
            multiselect_key + "_global",
            "cm_" + multiselect_key + "_global",
            multiselect_key,
        ]:
            if key_variant in st.session_state:
                del st.session_state[key_variant]
                logger.debug(f"Cleaned up conflicting widget key: {key_variant}")

        # Extract custom values (those not in base options)
        custom_values = [
            v for v in current_values if v not in base_options and v != "Anders..."
        ]

        # Build complete options list - ensure no duplicates
        all_options = base_options + list(set(custom_values))
        full_options = all_options + ["Anders..."]

        # Filter defaults to only include values that exist in options
        default_values = [v for v in current_values if v in full_options]

        # Render multiselect with try/except for safety
        # Use namespaced keys to avoid collisions with legacy components
        widget_key = f"cm_{multiselect_key}"
        try:
            selected = st.multiselect(
                title,
                options=full_options,
                default=default_values,
                help=help_text,
                key=widget_key,
            )
        except Exception as e:
            logger.warning(f"Multiselect error for {title}: {e}")
            # Fallback: render without defaults
            selected = st.multiselect(
                title,
                options=full_options,
                default=[],  # Empty defaults to avoid crashes
                help=help_text,
                key=widget_key,
            )

        # Handle "Anders..." option
        if "Anders..." in selected:
            custom_input = st.text_input(
                f"Voer aangepaste {title.lower()} in:",
                placeholder="Typ hier uw eigen waarde...",
                key=f"cm_{custom_key}",
                max_chars=self.max_custom_length,
            )

            if custom_input and custom_input.strip():
                # Sanitize the custom input
                sanitized = self._sanitize_custom_input(custom_input.strip())
                if sanitized:
                    # Add to selected values if not already present
                    if sanitized not in selected:
                        selected = [v for v in selected if v != "Anders..."]
                        selected.append(sanitized)

        # Remove "Anders..." from final list
        final_values = [v for v in selected if v != "Anders..."]

        return final_values

    def _sanitize_custom_input(self, value: str) -> str | None:
        """
        Sanitize custom input value.

        Args:
            value: Raw user input

        Returns:
            Sanitized value or None if invalid
        """
        try:
            result = self.sanitizer.sanitize(
                value=value,
                content_type=ContentType.PLAIN_TEXT,
                level=SanitizationLevel.STRICT,
            )

            if result.sanitized_value:
                return result.sanitized_value

            if result.warnings:
                st.warning(f"⚠️ {result.warnings[0]}")

            return None

        except Exception as e:
            logger.error(f"Error sanitizing custom input: {e}")
            st.error("Fout bij verwerken van aangepaste waarde")
            return None

    def _render_context_summary(self, context_data: dict[str, Any]) -> None:
        """
        Render a summary of the selected context.

        Args:
            context_data: Selected context data
        """
        # Only show summary if there's actual context selected
        has_context = any(
            context_data.get(key)
            for key in [
                "organisatorische_context",
                "juridische_context",
                "wettelijke_basis",
            ]
        )

        if has_context:
            with st.expander("📊 Context Overzicht", expanded=False):
                if context_data.get("organisatorische_context"):
                    st.write(
                        "**Organisatorisch:**",
                        ", ".join(context_data["organisatorische_context"]),
                    )
                if context_data.get("juridische_context"):
                    st.write(
                        "**Juridisch:**", ", ".join(context_data["juridische_context"])
                    )
                if context_data.get("wettelijke_basis"):
                    st.write(
                        "**Wettelijk:**", ", ".join(context_data["wettelijke_basis"])
                    )

                # Show how this context will be used
                st.info(
                    "💡 Deze context wordt gebruikt voor:\n"
                    "- Het genereren van definities binnen de juiste context\n"
                    "- Het zoeken naar relevante bronnen via web lookup\n"
                    "- Het toepassen van domein-specifieke validatie regels"
                )


def render_context_selector() -> dict[str, Any]:
    """
    Convenience function to render the context selector.

    Returns:
        Selected context data
    """
    selector = EnhancedContextManagerSelector()
    return selector.render()
