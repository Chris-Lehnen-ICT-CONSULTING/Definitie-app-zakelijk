"""
Sessie status beheer voor DefinitieAgent Streamlit applicatie.

Deze module beheert alle sessie variabelen die gebruikt worden
door de Streamlit interface om data tussen pagina refreshes te bewaren.
"""

import logging
from typing import Any, ClassVar  # Type hints voor betere code documentatie

import streamlit as st  # Streamlit framework voor web interface

logger = logging.getLogger(__name__)

# NOTE: get_context_adapter import moved to get_context_dict() to break circular dependency
# See DEF-86: Circular import deadlock fix


class SessionStateManager:
    """Beheert Streamlit sessie status voor DefinitieAgent.

    Deze klasse biedt een gecentraliseerde manier om sessie variabelen
    te beheren, inclusief standaardwaarden en hulpmethoden.
    """

    # Standaardwaarden voor sessie status sleutels - Deze waarden worden gebruikt bij initialisatie
    DEFAULT_VALUES: ClassVar[dict[str, Any]] = {
        "gegenereerd": "",
        "beoordeling_gen": [],
        "aangepaste_definitie": "",
        "beoordeling": [],
        "voorbeeld_zinnen": [],
        "praktijkvoorbeelden": [],
        "tegenvoorbeelden": [],
        "toelichting": "",
        "synoniemen": "",
        "antoniemen": "",
        "voorkeursterm": "",
        "expert_review": "",
        "definitie_origineel": "",
        "definitie_gecorrigeerd": "",
        "marker": "",
        "bronnen_gebruikt": "",
        "prompt_text": "",
        "vrije_input": "",
        "toon_ai_toetsing": False,
        "toon_toetsing_hercontrole": True,
        "override_actief": False,
        "override_verboden_woorden": [],
        # Metadata velden (legacy restoration)
        "datum_voorstel": None,
        "voorgesteld_door": "",
        "ketenpartners": [],
        # External sources manager
        "external_source_manager": None,
        # Edit tab state variables voor auto-load functionaliteit
        "editing_definition_id": None,  # ID van definitie om te bewerken
        "editing_definition": None,  # Definitie object
        "edit_session": None,  # Edit sessie metadata
        "edit_search_results": None,  # Zoekresultaten in edit tab
        "last_auto_save": None,  # Auto-save timestamp
        # Edit tab context behoud
        "edit_organisatorische_context": None,  # Org context voor edit
        "edit_juridische_context": None,  # Jur context voor edit
        "edit_wettelijke_basis": None,  # Wet context voor edit
        # DEF-236: Race condition tracking for edit tab auto-load
        "edit_load_version": 0,
    }

    @staticmethod
    def initialize_session_state():
        """Initialiseer alle sessie status variabelen met standaardwaarden.

        Doorloopt alle standaardwaarden en zet ze in de sessie status
        als ze nog niet bestaan.
        """
        # Doorloop alle standaardwaarden en initialiseer ze
        for key, default_value in SessionStateManager.DEFAULT_VALUES.items():
            if key not in st.session_state:  # Controleer of sleutel al bestaat
                st.session_state[key] = default_value  # Zet standaardwaarde

        # US-202: Initialize services met caching om herinitialisatie te voorkomen
        # Import hier om circulaire import te voorkomen
        from ui.cached_services import initialize_services_once

        initialize_services_once()

    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """
        Haal waarde op uit sessie status met fallback naar standaardwaarde.

        Args:
            key: Sessie status sleutel
            default: Standaardwaarde als sleutel niet gevonden

        Returns:
            Sessie status waarde of standaardwaarde
        """
        # Direct access to avoid circular dependency
        return st.session_state.get(key, default)

    @staticmethod
    def set_value(key: str, value: Any):
        """
        Zet waarde in sessie status.

        Args:
            key: Sessie status sleutel
            value: Waarde om te zetten
        """
        # Direct access to avoid circular dependency
        st.session_state[key] = value

    @staticmethod
    def clear_value(key: str):
        """
        Verwijder een specifieke waarde uit sessie status.

        Args:
            key: Sessie status sleutel om te verwijderen
        """
        # Verwijder sleutel uit sessie status als deze bestaat
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def update_definition_results(
        definitie_origineel: str,
        definitie_gecorrigeerd: str,
        marker: str = "",
        beoordeling_gen: list[str] | None = None,
    ):
        """
        Update sessie status met definitie generatie resultaten.

        Args:
            definitie_origineel: Originele gegenereerde definitie
            definitie_gecorrigeerd: Opgeschoonde definitie
            marker: Ontologische categorie marker
            beoordeling_gen: Kwaliteitstoets resultaten
        """
        # Sla originele AI-gegenereerde definitie op
        st.session_state["definitie_origineel"] = definitie_origineel
        # Sla opgeschoonde definitie op
        st.session_state["definitie_gecorrigeerd"] = definitie_gecorrigeerd
        # Sla ook op onder 'gegenereerd' voor backwards compatibility
        st.session_state["gegenereerd"] = definitie_origineel
        # Sla ontologische categorie marker op
        st.session_state["marker"] = marker
        # Sla kwaliteitsbeoordeling op als deze bestaat
        if beoordeling_gen:
            st.session_state["beoordeling_gen"] = beoordeling_gen

    @staticmethod
    def update_ai_content(
        voorbeeld_zinnen: list[str] | None = None,
        praktijkvoorbeelden: list[str] | None = None,
        tegenvoorbeelden: list[str] | None = None,
        toelichting: str = "",
        synoniemen: str = "",
        antoniemen: str = "",
        bronnen_gebruikt: str = "",
    ):
        """
        Update sessie status met AI-gegenereerde content.

        Args:
            voorbeeld_zinnen: Voorbeeldzinnen
            praktijkvoorbeelden: Praktische voorbeelden
            tegenvoorbeelden: Tegenvoorbeelden
            toelichting: Uitleg
            synoniemen: Synoniemen
            antoniemen: Antoniemen
            bronnen_gebruikt: Gebruikte bronnen
        """
        # Update voorbeeldzinnen als deze zijn gegeven
        if voorbeeld_zinnen:
            st.session_state["voorbeeld_zinnen"] = voorbeeld_zinnen
        # Update praktijkvoorbeelden als deze zijn gegeven
        if praktijkvoorbeelden:
            st.session_state["praktijkvoorbeelden"] = praktijkvoorbeelden
        # Update tegenvoorbeelden als deze zijn gegeven
        if tegenvoorbeelden:
            st.session_state["tegenvoorbeelden"] = tegenvoorbeelden
        # Update toelichting als deze is gegeven
        if toelichting:
            st.session_state["toelichting"] = toelichting
        # Update synoniemen als deze zijn gegeven
        if synoniemen:
            st.session_state["synoniemen"] = synoniemen
        # Update antoniemen als deze zijn gegeven
        if antoniemen:
            st.session_state["antoniemen"] = antoniemen
        # Update bronnen als deze zijn gegeven
        if bronnen_gebruikt:
            st.session_state["bronnen_gebruikt"] = bronnen_gebruikt

    @staticmethod
    def get_context_dict() -> dict[str, list[str]]:
        """
        Haal context woordenboek op uit sessie status.

        Returns:
            Woordenboek met organisatorische, juridische en wettelijke contexten
        """
        # Probeer eerst de gecentraliseerde ContextManager via adapter
        try:
            # Late import to break circular dependency (DEF-86)
            from ui.helpers.context_adapter import get_context_adapter

            adapter = get_context_adapter()
            # Fixed: was calling non-existent to_generation_request(), now using get_merged_context()
            context = adapter.get_merged_context()
            return {
                "organisatorisch": context.get("organisatorische_context", []),
                "juridisch": context.get("juridische_context", []),
                "wettelijk": context.get("wettelijke_basis", []),
            }
        except (AttributeError, KeyError, TypeError, ValueError, ImportError) as e:
            # DEF-234/DEF-252: Log error and warn user about fallback to legacy session state
            logger.error(
                f"ContextManager failed, falling back to legacy session state: {type(e).__name__}: {e}",
                exc_info=True,
                extra={
                    "component": "session_state",
                    "operation": "get_context_dict",
                    "event": "context_fallback",
                },
            )
            # Show warning in UI so user knows context may be incorrect
            st.warning(
                "Context manager fout - fallback naar legacy context. "
                "Controleer context velden voor generatie."
            )
            # DEF-252: Fixed fallback keys to match ContextManager keys
            return {
                "organisatorisch": st.session_state.get("organisatorische_context", []),
                "juridisch": st.session_state.get("juridische_context", []),
                "wettelijk": st.session_state.get("wettelijke_basis", []),
            }

    @staticmethod
    def get_export_data() -> dict[str, Any]:
        """
        Haal alle data op die nodig is voor export.

        Returns:
            Woordenboek met export data
        """
        # Bouw complete export data structuur op
        return {
            "begrip": st.session_state.get("begrip", ""),  # Het begrip zelf
            "definitie_gecorrigeerd": st.session_state.get(
                "definitie_gecorrigeerd", ""
            ),  # Gecorrigeerde definitie
            "definitie_origineel": st.session_state.get(
                "definitie_origineel", ""
            ),  # Originele definitie
            "metadata": {
                "marker": st.session_state.get(
                    "marker", ""
                ),  # Marker voor identificatie
                "datum_voorstel": st.session_state.get(
                    "datum_voorstel"
                ),  # Datum van voorstel
                "voorgesteld_door": st.session_state.get(
                    "voorgesteld_door", ""
                ),  # Voorsteller
                "ketenpartners": st.session_state.get(
                    "ketenpartners", []
                ),  # Ketenpartners
            },
            "context_dict": SessionStateManager.get_context_dict(),  # Context informatie
            "toetsresultaten": st.session_state.get(
                "beoordeling_gen", []
            ),  # Kwaliteitstoets resultaten
            "bronnen": st.session_state.get(
                "bronnen_gebruikt", ""
            ).splitlines(),  # Gebruikte bronnen (gesplitst op regels)
            "voorbeeld_zinnen": st.session_state.get(
                "voorbeeld_zinnen", []
            ),  # Voorbeeldzinnen
            "praktijkvoorbeelden": st.session_state.get(
                "praktijkvoorbeelden", []
            ),  # Praktijkvoorbeelden
            "tegenvoorbeelden": st.session_state.get(
                "tegenvoorbeelden", []
            ),  # Tegenvoorbeelden
            "toelichting": st.session_state.get(
                "toelichting", ""
            ),  # Uitgebreide toelichting
            "synoniemen": st.session_state.get("synoniemen", ""),  # Synoniemen
            "antoniemen": st.session_state.get("antoniemen", ""),  # Antoniemen
            "voorkeursterm": st.session_state.get("voorkeursterm", ""),  # Voorkeursterm
        }

    @staticmethod
    def clear_definition_results():
        """Wis alle definitie-gerelateerde resultaten uit sessie status."""
        # Lijst van sleutels die gewist moeten worden
        keys_to_clear = [
            "definitie_origineel",
            "definitie_gecorrigeerd",
            "gegenereerd",
            "marker",
            "beoordeling_gen",
            "beoordeling",
            "aangepaste_definitie",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "toelichting",
            "synoniemen",
            "antoniemen",
            "bronnen_gebruikt",
        ]
        # Doorloop alle sleutels en reset naar standaardwaarden
        for key in keys_to_clear:
            if key in st.session_state:  # Controleer of sleutel bestaat
                # Reset naar standaardwaarde of lege string
                st.session_state[key] = SessionStateManager.DEFAULT_VALUES.get(key, "")

    @staticmethod
    def has_generated_definition() -> bool:
        """
        Controleer of er een gegenereerde definitie beschikbaar is.

        Returns:
            True als definitie bestaat en niet leeg is
        """
        # Haal gecorrigeerde definitie op uit sessie status
        definitie = st.session_state.get("definitie_gecorrigeerd", "")
        # Controleer of het een string is en minimaal 3 karakters bevat
        return isinstance(definitie, str) and len(definitie.strip()) > 3


def force_cleanup_voorbeelden(prefix: str) -> None:
    """Clear all voorbeelden widget state for a given prefix.

    Used when crossing definition boundaries to prevent stale data.

    Args:
        prefix: Session key prefix (e.g., 'edit_106')

    Business Logic:
        - Nuclear option: deletes ALL voorbeelden-related keys
        - Safety: only deletes keys containing voorbeelden indicators
        - Called by _reset_voorbeelden_context() when definition changes

    Example:
        force_cleanup_voorbeelden("edit_106")
        # Deletes: edit_106_vz_edit, edit_106_syn_edit, edit_106_examples, etc.

    DEF-110: Moved to session_state.py where direct st.session_state access is allowed.
    """
    # Find all keys for this prefix that contain voorbeelden data
    keys_to_clear = [
        k
        for k in st.session_state
        if k.startswith(f"{prefix}_")
        and any(
            indicator in k
            for indicator in ["vz_", "pv_", "tv_", "syn_", "ant_", "tol_", "examples"]
        )
    ]

    # DEF-235: Nuclear cleanup with explicit logging
    # Note: keys_to_clear comes from iterating st.session_state, so keys always exist
    # (removed unreachable else branch that was dead code)
    if keys_to_clear:
        logger.debug(
            f"Cleaning {len(keys_to_clear)} voorbeelden keys for prefix={prefix}",
            extra={
                "component": "session_state",
                "operation": "force_cleanup_voorbeelden",
                "prefix": prefix,
                "key_count": len(keys_to_clear),
            },
        )
    for key in keys_to_clear:
        del st.session_state[key]
