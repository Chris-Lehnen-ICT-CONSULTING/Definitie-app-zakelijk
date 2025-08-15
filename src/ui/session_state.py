"""
Sessie status beheer voor DefinitieAgent Streamlit applicatie.

Deze module beheert alle sessie variabelen die gebruikt worden
door de Streamlit interface om data tussen pagina refreshes te bewaren.
"""

import streamlit as st  # Streamlit framework voor web interface
from typing import Dict, Any, List  # Type hints voor betere code documentatie


class SessionStateManager:
    """Beheert Streamlit sessie status voor DefinitieAgent.

    Deze klasse biedt een gecentraliseerde manier om sessie variabelen
    te beheren, inclusief standaardwaarden en hulpmethoden.
    """

    # Standaardwaarden voor sessie status sleutels - Deze waarden worden gebruikt bij initialisatie
    DEFAULT_VALUES = {
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
        # Haal waarde op uit sessie status, gebruik default als niet gevonden
        return st.session_state.get(key, default)

    @staticmethod
    def set_value(key: str, value: Any):
        """
        Zet waarde in sessie status.

        Args:
            key: Sessie status sleutel
            value: Waarde om te zetten
        """
        # Zet de waarde direct in de sessie status
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
        beoordeling_gen: List[str] = None,
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
        voorbeeld_zinnen: List[str] = None,
        praktijkvoorbeelden: List[str] = None,
        tegenvoorbeelden: List[str] = None,
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
    def get_context_dict() -> Dict[str, List[str]]:
        """
        Haal context woordenboek op uit sessie status.

        Returns:
            Woordenboek met organisatorische, juridische en wettelijke contexten
        """
        # Bouw context woordenboek op basis van sessie status waarden
        return {
            "organisatorisch": st.session_state.get(
                "context", []
            ),  # Organisatorische context
            "juridisch": st.session_state.get(
                "juridische_context", []
            ),  # Juridische context
            "wettelijk": st.session_state.get("wet_basis", []),  # Wettelijke basis
        }

    @staticmethod
    def get_export_data() -> Dict[str, Any]:
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
