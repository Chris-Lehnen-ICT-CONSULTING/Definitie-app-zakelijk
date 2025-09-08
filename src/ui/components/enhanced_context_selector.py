"""
Enhanced Context Selector Component with Session State Management.

This component provides a stable, user-friendly interface for selecting
context with custom "Anders..." entries that don't crash the system.
"""

from dataclasses import dataclass

import streamlit as st

from config.context_options import (
    COMMON_LAWS,
    LEGAL_DOMAINS,
    ORGANIZATIONS as ASTRA_ORGANIZATIONS,
)
from services.context.context_adapter import get_context_adapter


@dataclass
class ValidationResult:
    """Validation result with warnings and suggestions."""

    is_valid: bool = True
    warnings: list[str] = None
    suggestions: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)

    def add_suggestion(self, suggestion: str):
        """Add a suggestion."""
        self.suggestions.append(suggestion)

    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    def has_suggestions(self) -> bool:
        """Check if there are suggestions."""
        return len(self.suggestions) > 0


class EnhancedContextSelector:
    """
    Context selector with stable session state management.

    Key features:
    - Preserves selection order
    - Handles "Anders..." custom entries without crashes
    - Intelligent deduplication
    - ASTRA validation with warnings (not errors)
    """

    # Options are sourced from centralized config (business knowledge)

    def __init__(self):
        """Initialize context selector with session state and adapter."""
        self.adapter = get_context_adapter()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state if not exists."""
        if "context_state" not in st.session_state:
            st.session_state.context_state = {
                "organisatorisch": [],
                "juridisch": [],
                "wettelijk": [],
                "custom_entries": {
                    "organisatorisch": [],
                    "juridisch": [],
                    "wettelijk": [],
                },
                "selection_order": {},
                "validation_results": {},
            }

    def render(self) -> dict[str, list[str]]:
        """
        Render complete context selector interface.

        Returns:
            Dictionary with selected context values for each type
        """
        st.markdown("### Context Selectie")
        st.info(
            "Selecteer de relevante context voor uw definitie. "
            "Gebruik 'Anders...' om eigen waarden toe te voegen."
        )

        # Render each context type
        org_context = self.render_multiselect_with_custom(
            field_name="organisatorisch",
            options=ASTRA_ORGANIZATIONS,
            label="Organisatorische Context",
            help_text="Selecteer betrokken organisaties",
        )

        jur_context = self.render_multiselect_with_custom(
            field_name="juridisch",
            options=LEGAL_DOMAINS,
            label="Juridische Context",
            help_text="Selecteer relevante rechtsgebieden",
        )

        wet_basis = self.render_multiselect_with_custom(
            field_name="wettelijk",
            options=COMMON_LAWS,
            label="Wettelijke Basis",
            help_text="Selecteer toepasselijke wetten",
        )

        # Store final selections
        result = {
            "organisatorische_context": org_context,
            "juridische_context": jur_context,
            "wettelijke_basis": wet_basis,
        }

        # Show validation feedback
        self._render_validation_feedback(result)

        return result

    def render_multiselect_with_custom(
        self, field_name: str, options: list[str], label: str, help_text: str = ""
    ) -> list[str]:
        """
        Render multiselect with "Anders..." option.

        This method handles the complex state management for custom entries,
        ensuring that the "Anders..." option works without crashes.

        Args:
            field_name: Internal field name for state management
            options: List of standard options
            label: Display label for the field
            help_text: Optional help text

        Returns:
            List of selected values including custom entries
        """
        # Get current state
        current_state = st.session_state.context_state.get(field_name, [])
        custom_entries = st.session_state.context_state.get("custom_entries", {}).get(
            field_name, []
        )

        # Combine standard options with custom entries
        all_options = options + custom_entries
        display_options = [*all_options, "Anders..."]

        # Filter current state to only include valid options
        valid_defaults = [x for x in current_state if x in all_options]

        # Render multiselect
        selected = st.multiselect(
            label,
            options=display_options,
            default=valid_defaults,
            help=help_text,
            key=f"{field_name}_multiselect",
        )

        # Handle "Anders..." selection
        if "Anders..." in selected:
            self._handle_custom_entry(field_name, label)
            # Remove "Anders..." from selection as it's not a real value
            selected = [x for x in selected if x != "Anders..."]

        # Update session state with current selection (UI local state)
        st.session_state.context_state[field_name] = selected

        # Also propagate to centralized ContextManager via adapter
        field_map = {
            "organisatorisch": "organisatorische_context",
            "juridisch": "juridische_context",
            "wettelijk": "wettelijke_basis",
        }
        canonical = field_map.get(field_name, field_name)
        from contextlib import suppress

        with suppress(Exception):
            self.adapter.update_field(canonical, selected, actor="ui")  # type: ignore[arg-type]

        # Apply deduplication while preserving order
        return self._deduplicate_preserving_order(selected)

    def _handle_custom_entry(self, field_name: str, label: str):
        """
        Handle custom "Anders..." entry with proper validation.

        This method ensures custom entries are properly added to session state
        without causing crashes or data loss.
        """
        custom_key = f"{field_name}_custom_input"

        col1, col2 = st.columns([3, 1])

        with col1:
            custom_value = st.text_input(
                "Voer aangepaste waarde in:",
                key=custom_key,
                placeholder=f"Typ hier uw eigen {label.lower()}...",
            )

        with col2:
            if st.button("Toevoegen", key=f"{custom_key}_btn", type="secondary"):
                if custom_value and custom_value.strip():
                    # Clean and validate input
                    cleaned_value = custom_value.strip()

                    # Add to custom entries if not already present
                    if "custom_entries" not in st.session_state.context_state:
                        st.session_state.context_state["custom_entries"] = {}

                    if (
                        field_name
                        not in st.session_state.context_state["custom_entries"]
                    ):
                        st.session_state.context_state["custom_entries"][
                            field_name
                        ] = []

                    if (
                        cleaned_value
                        not in st.session_state.context_state["custom_entries"][
                            field_name
                        ]
                    ):
                        st.session_state.context_state["custom_entries"][
                            field_name
                        ].append(cleaned_value)

                        # Also add to current selection
                        if field_name not in st.session_state.context_state:
                            st.session_state.context_state[field_name] = []

                        if (
                            cleaned_value
                            not in st.session_state.context_state[field_name]
                        ):
                            st.session_state.context_state[field_name].append(
                                cleaned_value
                            )

                        st.success(f"'{cleaned_value}' toegevoegd aan {label}")

                        # Propagate to adapter (central context)
                        try:
                            field_map = {
                                "organisatorisch": "organisatorische_context",
                                "juridisch": "juridische_context",
                                "wettelijk": "wettelijke_basis",
                            }
                            canonical = field_map.get(field_name, field_name)
                            current = st.session_state.context_state.get(field_name, [])
                            self.adapter.update_field(canonical, current, actor="ui")  # type: ignore[arg-type]
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.warning(f"'{cleaned_value}' bestaat al in {label}")
                else:
                    st.error("Voer een waarde in voordat u toevoegt")

    def _deduplicate_preserving_order(self, items: list[str]) -> list[str]:
        """
        Remove duplicates while preserving order.

        This method handles case-insensitive deduplication while
        preserving the original casing of the first occurrence.

        Args:
            items: List of items potentially containing duplicates

        Returns:
            Deduplicated list with order preserved
        """
        seen = {}
        result = []

        for item in items:
            # Normalize for comparison (lowercase, stripped)
            normalized = item.lower().strip()

            if normalized not in seen:
                seen[normalized] = item
                result.append(item)

        return result

    def _render_validation_feedback(self, context: dict[str, list[str]]):
        """
        Render validation feedback without blocking.

        This provides helpful warnings about ASTRA compliance
        without preventing the user from proceeding.
        """
        # Simple validation for demonstration
        has_org = bool(context.get("organisatorische_context"))
        has_jur = bool(context.get("juridische_context"))
        has_wet = bool(context.get("wettelijke_basis"))

        if not any([has_org, has_jur, has_wet]):
            st.warning(
                "Geen context geselecteerd. Definities zullen algemener zijn zonder specifieke context."
            )
        else:
            # Show what's selected
            with st.expander("Geselecteerde context", expanded=False):
                if has_org:
                    st.write(
                        f"**Organisatorisch:** {', '.join(context['organisatorische_context'])}"
                    )
                if has_jur:
                    st.write(
                        f"**Juridisch:** {', '.join(context['juridische_context'])}"
                    )
                if has_wet:
                    st.write(f"**Wettelijk:** {', '.join(context['wettelijke_basis'])}")

    def get_context_summary(self) -> str:
        """
        Get a text summary of the current context.

        Returns:
            Formatted string with context summary
        """
        # Prefer centralized context when available
        try:
            cm_state = self.adapter.to_generation_request()
            state = {
                "organisatorisch": cm_state.get("organisatorische_context", []),
                "juridisch": cm_state.get("juridische_context", []),
                "wettelijk": cm_state.get("wettelijke_basis", []),
            }
        except Exception:
            state = st.session_state.context_state
        summary_parts = []

        if state.get("organisatorisch"):
            summary_parts.append(f"Organisaties: {', '.join(state['organisatorisch'])}")

        if state.get("juridisch"):
            summary_parts.append(f"Rechtsgebieden: {', '.join(state['juridisch'])}")

        if state.get("wettelijk"):
            summary_parts.append(f"Wetten: {', '.join(state['wettelijk'])}")

        return (
            " | ".join(summary_parts) if summary_parts else "Geen context geselecteerd"
        )

    def clear_context(self):
        """Clear all context selections."""
        # Reset UI local state
        st.session_state.context_state = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
            "custom_entries": {"organisatorisch": [], "juridisch": [], "wettelijk": []},
            "selection_order": {},
            "validation_results": {},
        }
        # Clear centralized context as well
        from contextlib import suppress

        with suppress(Exception):
            self.adapter.clear(actor="ui")
        st.success("Context gewist")
