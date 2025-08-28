"""Helper voor category-based regeneration."""

import streamlit as st

from ui.session_state import SessionStateManager


class CategoryRegenerationHelper:
    """Helper class voor category regeneration flow."""

    @staticmethod
    def check_for_regeneration_request() -> dict | None:
        """Check of er een regeneration request is vanuit category change.

        Returns:
            Dict met regeneration info of None
        """
        regen_data = SessionStateManager.get_value("regenerate_with_category")

        if regen_data:
            # Clear de flag na gebruik
            SessionStateManager.clear_value("regenerate_with_category")

            # Toon info aan gebruiker
            st.info(
                f"""
            🔄 **Category Regeneration Mode**
            - Begrip: {regen_data['begrip']}
            - Nieuwe categorie: {regen_data['category']}
            - {regen_data['feedback']}
            """
            )

            return regen_data

        return None

    @staticmethod
    def apply_regeneration_context(begrip_field, category_field=None):
        """Apply regeneration context to form fields.

        Args:
            begrip_field: Streamlit text input field
            category_field: Optional category selectbox
        """
        regen_data = SessionStateManager.get_value("regenerate_with_category")

        if regen_data:
            # Pre-fill het begrip
            if begrip_field:
                begrip_field.value = regen_data["begrip"]

            # Set category indien mogelijk
            if category_field and "category" in regen_data:
                category_field.value = regen_data["category"]

            return True

        return False
