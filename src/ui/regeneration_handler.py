"""Handler voor regeneration flow in UI."""

import streamlit as st

from ui.session_state import SessionStateManager


class RegenerationHandler:
    """Handle regeneration flow tussen tabs."""

    @staticmethod
    def check_and_apply_regeneration() -> tuple[str, str]:
        """Check voor regeneration request en apply.

        Returns:
            Tuple van (begrip, category) of ("", "")
        """
        if SessionStateManager.get_value("regeneration_active", False):
            begrip = SessionStateManager.get_value("regeneration_begrip", "")
            category = SessionStateManager.get_value("regeneration_category", "")

            # Clear flags
            SessionStateManager.clear_value("regeneration_active")

            # Show info
            if begrip and category:
                st.info(
                    f"""
                🔄 **Regeneratie Mode Actief**
                - Begrip: {begrip}
                - Nieuwe categorie: {category}
                - De definitie wordt gegenereerd voor de nieuwe ontologische categorie
                """
                )

                return begrip, category

        return "", ""

    @staticmethod
    def inject_into_context(context_data: dict, category: str) -> dict:
        """Inject category into context data.

        Args:
            context_data: Existing context
            category: Category to inject

        Returns:
            Updated context data
        """
        if category:
            # Voeg category toe aan context voor generator
            context_data["ontological_category"] = category
            context_data["regeneration_mode"] = True

        return context_data
