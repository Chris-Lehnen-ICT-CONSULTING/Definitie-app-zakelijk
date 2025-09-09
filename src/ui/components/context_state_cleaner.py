"""
Context State Cleaner - Automatische opschoning van ongeldige session state waardes.
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


class ContextStateCleaner:
    """Clean en valideer context session state waardes."""

    @staticmethod
    def clean_session_state():
        """
        Verwijder ongeldige waardes uit session state bij app start.
        Dit voorkomt "default not in options" errors.
        """
        # Basis opties voor validatie
        base_org_options = [
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

        base_jur_options = [
            "Strafrecht",
            "Civiel recht",
            "Bestuursrecht",
            "Internationaal recht",
            "Europees recht",
            "Migratierecht",
        ]

        base_wet_options = [
            "Wetboek van Strafvordering (huidige versie)",
            "Wetboek van strafvordering (nieuwe versie)",
            "Wet op de Identificatieplicht",
            "Wet op de politiegegevens",
            "Wetboek van Strafrecht",
            "Algemene verordening gegevensbescherming",
        ]

        # Clean organisatorische context
        if "org_context_values" in st.session_state:
            original = st.session_state.org_context_values.copy()
            # Verwijder "Anders..." en behoud alleen geldige waardes
            cleaned = [v for v in original if v != "Anders..." and v != ""]
            if cleaned != original:
                logger.info(f"Cleaned org_context_values: {original} -> {cleaned}")
                st.session_state.org_context_values = cleaned

        # Clean juridische context
        if "jur_context_values" in st.session_state:
            original = st.session_state.jur_context_values.copy()
            # Verwijder "Anders..." en test waardes
            cleaned = [
                v for v in original if v != "Anders..." and v != "en nu" and v != ""
            ]
            if cleaned != original:
                logger.info(f"Cleaned jur_context_values: {original} -> {cleaned}")
                st.session_state.jur_context_values = cleaned

        # Clean wettelijke basis - AGRESSIEVE CLEANUP
        if "wet_basis_values" in st.session_state:
            original = st.session_state.wet_basis_values.copy()
            # Alleen behouden wat EXACT in de base options staat OF een echte custom waarde is
            # Verwijder ALLE test waardes en "Anders..."
            cleaned = []
            for v in original:
                # Skip lege strings, "Anders..." en bekende test waardes
                if (
                    v
                    and v != "Anders..."
                    and v not in ["toetsen", "testen", "rest", "test", "en nu"]
                    and len(v) > 2
                ):  # Skip te korte waardes
                    # Check of het een geldige optie is
                    if v in base_wet_options or (
                        # Of een echte custom waarde (niet een typfout)
                        not any(test in v.lower() for test in ["test", "rest", "toets"])
                    ):
                        cleaned.append(v)

            if cleaned != original:
                logger.warning(
                    f"AGGRESSIVE CLEANUP wet_basis_values: {original} -> {cleaned}"
                )
                st.session_state.wet_basis_values = cleaned

    @staticmethod
    def validate_and_fix_state(
        field_name: str, values: list, valid_options: list
    ) -> list:
        """
        Valideer en fix een specifiek context veld.

        Args:
            field_name: Naam van het veld (voor logging)
            values: Huidige waardes in session state
            valid_options: Lijst met geldige opties

        Returns:
            Gefilterde lijst met alleen geldige waardes
        """
        if not values:
            return []

        # Filter waardes die niet in options zitten
        # Custom waardes (niet in base options) zijn toegestaan
        # "Anders..." is NOOIT toegestaan als waarde
        filtered = [v for v in values if v != "Anders..."]

        if filtered != values:
            logger.warning(
                f"{field_name}: Removed invalid values. "
                f"Original: {values}, Filtered: {filtered}"
            )

        return filtered


def init_context_cleaner(force_clean=False):
    """Initialize context cleaner on app start.

    Args:
        force_clean: If True, force a cleanup even if already done
    """
    if force_clean or "context_cleaned" not in st.session_state:
        ContextStateCleaner.clean_session_state()
        st.session_state.context_cleaned = True
        logger.info("Context state cleaned on app initialization")


def reset_all_context():
    """Complete reset of all context fields."""
    logger.warning("FORCE RESET: Clearing all context fields")

    # Reset alle context velden
    if "org_context_values" in st.session_state:
        del st.session_state.org_context_values
    if "jur_context_values" in st.session_state:
        del st.session_state.jur_context_values
    if "wet_basis_values" in st.session_state:
        del st.session_state.wet_basis_values

    # Reset cleaned flag om force cleanup te triggeren
    if "context_cleaned" in st.session_state:
        del st.session_state.context_cleaned

    logger.info("All context fields reset")
