"""
Context Selector Component - Enhanced multi-select context management.
REFACTORED: Now uses centralized ContextManager via adapter (US-043).
"""

import logging
from dataclasses import dataclass
from typing import Any

import streamlit as st

from services.context.context_manager import ContextSource
from ui.helpers.context_adapter import (
    get_context_adapter,
)
from ui.session_state import SessionStateManager
from validation.sanitizer import (
    ContentType,
    SanitizationLevel,
    get_sanitizer,
)

logger = logging.getLogger(__name__)


@dataclass
class ContextPreset:
    """Voorgedefinieerde context combinatie."""

    name: str
    organisatorische_context: list[str]
    juridische_context: list[str]
    wettelijke_basis: list[str]
    description: str = ""


class ContextSelector:
    """Enhanced context selector met presets en validation."""

    def __init__(self):
        """Initialiseer context selector."""
        self.presets = self._load_context_presets()
        self.validation_rules = self._load_validation_rules()
        self.sanitizer = get_sanitizer()
        self.max_custom_length = 200  # US-042: Maximum length for custom input
        # US-043: Use centralized context manager
        self.context_adapter = get_context_adapter()

    def render(self) -> dict[str, Any]:
        """
        Render context selector interface.

        Returns:
            Dictionary met geselecteerde context data
        """
        # US-043: Get existing context from ContextManager
        existing_context = self.context_adapter.get_from_session_state()

        # Preset selector
        selected_preset = self._render_preset_selector()

        if selected_preset:
            # Load preset values
            context_data = self._apply_preset(selected_preset)
        else:
            # Manual selection with existing values as defaults
            context_data = self._render_manual_selector(
                default_org=existing_context.get("organisatorische_context"),
                default_jur=existing_context.get("juridische_context"),
                default_wet=existing_context.get("wettelijke_basis"),
            )

        # US-043: Store context via ContextManager
        self.context_adapter.set_in_session_state(
            context_data, source=ContextSource.UI, actor="user"
        )

        # Validation en feedback
        self._render_context_validation(context_data)

        return context_data

    # Backwards-compatibility for tests expecting older UI API
    def render_context_selection(self) -> dict[str, Any]:
        """Compatibility wrapper returning short-key context dict.

        Maps V2 keys to legacy keys expected by some test fixtures.
        """
        data = self.render()
        return {
            "organisatorisch": data.get("organisatorische_context", []),
            "juridisch": data.get("juridische_context", []),
            "wettelijk": data.get("wettelijke_basis", []),
        }

    def _render_preset_selector(self) -> ContextPreset | None:
        """Render preset selectie."""
        st.markdown("#### 🎯 Snelle Selectie")

        preset_options = ["Handmatig selecteren..."] + [p.name for p in self.presets]

        selected_name = st.selectbox(
            "Kies een voorgedefinieerde context combinatie:",
            options=preset_options,
            help="Selecteer een veelgebruikte context combinatie of kies handmatig",
        )

        if selected_name and selected_name != "Handmatig selecteren...":
            preset = next((p for p in self.presets if p.name == selected_name), None)
            if preset:
                st.info(f"💡 {preset.description}")
                return preset

        return None

    def _apply_preset(self, preset: ContextPreset) -> dict[str, Any]:
        """Pas voorgedefinieerde context toe."""
        st.markdown("#### ✅ Geselecteerde Context")

        # Show preset details
        with st.expander("Context details", expanded=True):
            st.write(
                f"**Organisatorisch:** {', '.join(preset.organisatorische_context)}"
            )
            st.write(f"**Juridisch:** {', '.join(preset.juridische_context)}")
            st.write(f"**Wettelijk:** {', '.join(preset.wettelijke_basis)}")

        # Option to modify
        if st.checkbox("🔧 Aanpassen", help="Wijzig de geselecteerde context"):
            return self._render_manual_selector(
                default_org=preset.organisatorische_context,
                default_jur=preset.juridische_context,
                default_wet=preset.wettelijke_basis,
            )

        return {
            "organisatorische_context": preset.organisatorische_context,
            "juridische_context": preset.juridische_context,
            "wettelijke_basis": preset.wettelijke_basis,
        }

    def _render_manual_selector(
        self,
        default_org: list[str] | None = None,
        default_jur: list[str] | None = None,
        default_wet: list[str] | None = None,
    ) -> dict[str, Any]:
        """Render handmatige context selectie."""
        st.markdown("#### 🛠️ Handmatige Selectie")

        col1, col2 = st.columns(2)

        with col1:
            # Organisatorische context
            org_options = [
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
                "Anders...",
            ]

            # US-042 FIX: Ensure default values are valid for multiselect
            # Filter out any custom values that aren't in the original options
            safe_default_org = (
                [d for d in (default_org or []) if d in org_options]
                if default_org
                else []
            )

            selected_org = st.multiselect(
                "📋 Organisatorische context",
                options=org_options,
                default=safe_default_org,
                help="Selecteer één of meerdere organisaties",
                key="org_context_multiselect",  # US-042: Add key for state management
            )

            # Custom org context
            custom_org = ""
            if "Anders..." in selected_org:
                custom_org = st.text_input(
                    "Aangepaste organisatorische context",
                    placeholder="Voer andere organisatie in...",
                    key="custom_org_input",  # US-042: Add key for state management
                    max_chars=self.max_custom_length,  # US-042: Enforce max length
                    help=f"Maximaal {self.max_custom_length} karakters",
                )

            # Combineer contexts - US-042 FIX: Process without modifying widget state
            final_org = [opt for opt in selected_org if opt != "Anders..."]
            if custom_org and custom_org.strip():  # US-042: Check for None and empty
                # US-042: Sanitize and validate custom input
                sanitized_org = self._sanitize_custom_input(custom_org.strip())
                if sanitized_org:
                    final_org.append(sanitized_org)
                else:
                    # Show warning if input was rejected
                    st.warning("⚠️ Ongeldige invoer voor organisatorische context")

            # US-042 FIX: Don't update the widget variable, use final_org directly
            # This prevents the multiselect crash when custom values are added
            selected_org = final_org

            # Wettelijke basis
            wet_options = [
                "Wetboek van Strafvordering (huidig)",
                "Wetboek van Strafvordering (toekomstig)",
                "Wet op de Identificatieplicht",
                "Wet op de politiegegevens",
                "Wetboek van Strafrecht",
                "Algemene verordening gegevensbescherming",
                "Anders...",
            ]

            selected_wet = st.multiselect(
                "📜 Wettelijke basis",
                options=wet_options,
                default=default_wet or [],
                help="Selecteer relevante wetgeving",
            )

            # Custom legal basis
            custom_wet = ""
            if "Anders..." in selected_wet:
                custom_wet = st.text_input(
                    "Aangepaste wettelijke basis",
                    placeholder="Voer andere wetgeving in...",
                    key="custom_wet_input",  # US-042: Add key for state management
                    max_chars=self.max_custom_length,  # US-042: Enforce max length
                    help=f"Maximaal {self.max_custom_length} karakters",
                )

            # Combineer wettelijke basis
            final_wet = [opt for opt in selected_wet if opt != "Anders..."]
            if custom_wet and custom_wet.strip():  # US-042: Check for None and empty
                # US-042: Sanitize and validate custom input
                sanitized_wet = self._sanitize_custom_input(custom_wet.strip())
                if sanitized_wet:
                    final_wet.append(sanitized_wet)
                else:
                    st.warning("⚠️ Ongeldige invoer voor wettelijke basis")

            # Update selected_wet with final list
            selected_wet = final_wet

        with col2:
            # Juridische context
            jur_options = [
                "Strafrecht",
                "Civiel recht",
                "Bestuursrecht",
                "Internationaal recht",
                "Europees recht",
                "Migratierecht",
                "Anders...",
            ]

            selected_jur = st.multiselect(
                "⚖️ Juridische context",
                options=jur_options,
                default=default_jur or [],
                help="Selecteer juridische gebieden",
            )

            # Custom juridical context
            custom_jur = ""
            if "Anders..." in selected_jur:
                custom_jur = st.text_input(
                    "Aangepaste juridische context",
                    placeholder="Voer ander rechtsgebied in...",
                    key="custom_jur_input",  # US-042: Add key for state management
                    max_chars=self.max_custom_length,  # US-042: Enforce max length
                    help=f"Maximaal {self.max_custom_length} karakters",
                )

            # Combineer juridische context
            final_jur = [opt for opt in selected_jur if opt != "Anders..."]
            if custom_jur and custom_jur.strip():  # US-042: Check for None and empty
                # US-042: Sanitize and validate custom input
                sanitized_jur = self._sanitize_custom_input(custom_jur.strip())
                if sanitized_jur:
                    final_jur.append(sanitized_jur)
                else:
                    st.warning("⚠️ Ongeldige invoer voor juridische context")

            # Update selected_jur with final list
            selected_jur = final_jur

            # Additional metadata
            st.markdown("##### 📝 Metadata")

            voorsteller = st.text_input(
                "Voorgesteld door",
                value=SessionStateManager.get_value("voorsteller", ""),
            )

            ketenpartners = st.multiselect(
                "Akkoord ketenpartners",
                options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"],
                help="Partners die akkoord zijn",
            )

            # Store metadata in session
            SessionStateManager.set_value("voorsteller", voorsteller)
            SessionStateManager.set_value("ketenpartners", ketenpartners)

        return {
            "organisatorische_context": selected_org,
            "juridische_context": selected_jur,
            "wettelijke_basis": selected_wet,
            "voorsteller": voorsteller,
            "ketenpartners": ketenpartners,
        }

    def _render_context_validation(self, context_data: dict[str, Any]):
        """Render context validation en feedback."""
        # US-043: Use centralized validation
        is_valid, error_messages = self.context_adapter.validate()

        issues = error_messages.copy()
        suggestions = []

        # Additional UI-specific validation
        # Organisatorische context is nu optioneel
        # if not context_data.get("organisatorische_context"):
        #     if "Organisatorische context is verplicht" not in issues:
        #         issues.append("❌ Organisatorische context is verplicht")

        # Check voor context combinaties
        org_contexts = context_data.get("organisatorische_context", [])
        jur_contexts = context_data.get("juridische_context", [])

        # Context logic validation
        if "KMAR" in org_contexts and "Strafrecht" not in jur_contexts:
            suggestions.append("💡 KMAR gebruikt meestal Strafrecht context")

        if "DJI" in org_contexts and not any("Straf" in j for j in jur_contexts):
            suggestions.append(
                "💡 DJI gebruikt meestal strafrecht gerelateerde context"
            )

        # Show validation results
        if issues:
            for issue in issues:
                st.error(issue)

        if suggestions:
            with st.expander("💡 Context Suggesties", expanded=False):
                for suggestion in suggestions:
                    st.info(suggestion)

        # Show context strength indicator
        if org_contexts and (jur_contexts or context_data.get("wettelijke_basis")):
            st.success("✅ Context configuratie is compleet")

    def _load_context_presets(self) -> list[ContextPreset]:
        """Laad voorgedefinieerde context presets."""
        return [
            ContextPreset(
                name="DJI Strafrecht",
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=[
                    "Wetboek van Strafvordering (huidig)",
                    "Wetboek van Strafrecht",
                ],
                description="Standaard context voor DJI strafrecht definities",
            ),
            ContextPreset(
                name="OM Vervolging",
                organisatorische_context=["OM"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafvordering (huidig)"],
                description="Context voor OM vervolgingsdefinities",
            ),
            ContextPreset(
                name="KMAR Identificatie",
                organisatorische_context=["KMAR"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=[
                    "Wet op de Identificatieplicht",
                    "Wet op de politiegegevens",
                ],
                description="Context voor KMAR identificatie procedures",
            ),
            ContextPreset(
                name="Ketenbreed Strafrecht",
                organisatorische_context=["OM", "DJI", "KMAR", "CJIB"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafvordering (huidig)"],
                description="Brede ketencontext voor strafrecht definities",
            ),
            ContextPreset(
                name="Privacy & Gegevensbescherming",
                organisatorische_context=["OM", "DJI", "KMAR"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=[
                    "Algemene verordening gegevensbescherming",
                    "Wet op de politiegegevens",
                ],
                description="Context voor privacy en gegevensbescherming",
            ),
        ]

    def _load_validation_rules(self) -> dict[str, Any]:
        """Laad context validatie regels."""
        return {
            "required_fields": ["organisatorische_context"],
            "suggested_combinations": {
                "KMAR": {"juridische_context": ["Strafrecht"]},
                "DJI": {"juridische_context": ["Strafrecht"]},
                "OM": {"juridische_context": ["Strafrecht"]},
            },
        }

    def _sanitize_custom_input(self, text: str) -> str | None:
        """
        Sanitize and validate custom input text.

        US-042: Prevent crashes from malicious or invalid input.

        Args:
            text: Raw input text from user

        Returns:
            Sanitized text or None if input is invalid
        """
        try:
            # Remove leading/trailing whitespace
            text = text.strip()

            # Check if empty after stripping
            if not text:
                return None

            # Check length
            if len(text) > self.max_custom_length:
                text = text[: self.max_custom_length]
                logger.warning(
                    f"Custom input truncated to {self.max_custom_length} chars"
                )

            # Remove control characters that could cause issues
            # Keep standard punctuation and Dutch characters
            import re

            # Remove control characters but keep regular spaces, tabs, newlines
            text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

            # Normalize excessive whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Use sanitizer for XSS prevention with STRICT level
            result = self.sanitizer.sanitize(
                text,
                ContentType.DUTCH_TEXT,
                SanitizationLevel.STRICT,  # US-042: Use STRICT for XSS prevention
            )

            sanitized_text = result.sanitized_value

            # Log any threats detected
            if result.warnings:
                logger.warning(
                    f"Sanitization warnings for custom input: {result.warnings}"
                )

            # Final validation - ensure we still have meaningful text
            if not sanitized_text or len(sanitized_text.strip()) < 2:
                return None

            return sanitized_text

        except Exception as e:
            # US-042: Never crash on input sanitization
            logger.error(f"Error sanitizing custom input: {e}")
            return None

    def _get_organisatorische_options(self) -> list[str]:
        """Get organisational context options."""
        return [
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
            "Anders...",
        ]

    def _get_juridische_options(self) -> list[str]:
        """Get juridical context options."""
        return [
            "Strafrecht",
            "Civiel recht",
            "Bestuursrecht",
            "Internationaal recht",
            "Europees recht",
            "Migratierecht",
            "Anders...",
        ]

    def _get_wettelijke_options(self) -> list[str]:
        """Get legal basis options."""
        return [
            "Wetboek van Strafvordering (huidig)",
            "Wetboek van Strafvordering (toekomstig)",
            "Wet op de Identificatieplicht",
            "Wet op de politiegegevens",
            "Wetboek van Strafrecht",
            "Algemene verordening gegevensbescherming",
            "Anders...",
        ]

    def save_as_preset(
        self,
        name: str,
        context_data: dict[str, Any],
        description: str = "",
    ):
        """Sla huidige context op als preset."""
        # TODO: Implement preset saving to database or config file
        st.success(f"Context preset '{name}' opgeslagen!")


def render_context_selector() -> dict[str, Any]:
    """Standalone context selector rendering."""
    selector = ContextSelector()
    return selector.render()
