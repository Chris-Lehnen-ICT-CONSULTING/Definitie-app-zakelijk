"""
Session state management for DefinitieAgent Streamlit application.
"""

import streamlit as st
from typing import Dict, Any, List


class SessionStateManager:
    """Manages Streamlit session state for DefinitieAgent."""
    
    # Default values for session state keys
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
        "override_verboden_woorden": []
    }
    
    @staticmethod
    def initialize_session_state():
        """Initialize all session state variables with default values."""
        for key, default_value in SessionStateManager.DEFAULT_VALUES.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """
        Get value from session state with fallback to default.
        
        Args:
            key: Session state key
            default: Default value if key not found
            
        Returns:
            Session state value or default
        """
        return st.session_state.get(key, default)
    
    @staticmethod
    def set_value(key: str, value: Any):
        """
        Set value in session state.
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
    
    @staticmethod
    def update_definition_results(
        definitie_origineel: str,
        definitie_gecorrigeerd: str,
        marker: str = "",
        beoordeling_gen: List[str] = None
    ):
        """
        Update session state with definition generation results.
        
        Args:
            definitie_origineel: Original generated definition
            definitie_gecorrigeerd: Cleaned definition
            marker: Ontological category marker
            beoordeling_gen: Quality test results
        """
        st.session_state["definitie_origineel"] = definitie_origineel
        st.session_state["definitie_gecorrigeerd"] = definitie_gecorrigeerd
        st.session_state["gegenereerd"] = definitie_origineel
        st.session_state["marker"] = marker
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
        bronnen_gebruikt: str = ""
    ):
        """
        Update session state with AI-generated content.
        
        Args:
            voorbeeld_zinnen: Example sentences
            praktijkvoorbeelden: Practice examples
            tegenvoorbeelden: Counter-examples
            toelichting: Explanation
            synoniemen: Synonyms
            antoniemen: Antonyms
            bronnen_gebruikt: Sources used
        """
        if voorbeeld_zinnen:
            st.session_state["voorbeeld_zinnen"] = voorbeeld_zinnen
        if praktijkvoorbeelden:
            st.session_state["praktijkvoorbeelden"] = praktijkvoorbeelden
        if tegenvoorbeelden:
            st.session_state["tegenvoorbeelden"] = tegenvoorbeelden
        if toelichting:
            st.session_state["toelichting"] = toelichting
        if synoniemen:
            st.session_state["synoniemen"] = synoniemen
        if antoniemen:
            st.session_state["antoniemen"] = antoniemen
        if bronnen_gebruikt:
            st.session_state["bronnen_gebruikt"] = bronnen_gebruikt
    
    @staticmethod
    def get_context_dict() -> Dict[str, List[str]]:
        """
        Get context dictionary from session state.
        
        Returns:
            Dictionary with organizational, juridical, and legal contexts
        """
        return {
            "organisatorisch": st.session_state.get("context", []),
            "juridisch": st.session_state.get("juridische_context", []),
            "wettelijk": st.session_state.get("wet_basis", [])
        }
    
    @staticmethod
    def get_export_data() -> Dict[str, Any]:
        """
        Get all data needed for export.
        
        Returns:
            Dictionary with export data
        """
        return {
            "begrip": st.session_state.get("begrip", ""),
            "definitie_gecorrigeerd": st.session_state.get("definitie_gecorrigeerd", ""),
            "definitie_origineel": st.session_state.get("definitie_origineel", ""),
            "metadata": {"marker": st.session_state.get("marker", "")},
            "context_dict": SessionStateManager.get_context_dict(),
            "toetsresultaten": st.session_state.get("beoordeling_gen", []),
            "bronnen": st.session_state.get("bronnen_gebruikt", "").splitlines(),
            "voorbeeld_zinnen": st.session_state.get("voorbeeld_zinnen", []),
            "praktijkvoorbeelden": st.session_state.get("praktijkvoorbeelden", []),
            "tegenvoorbeelden": st.session_state.get("tegenvoorbeelden", []),
            "toelichting": st.session_state.get("toelichting", ""),
            "synoniemen": st.session_state.get("synoniemen", ""),
            "antoniemen": st.session_state.get("antoniemen", ""),
            "voorkeursterm": st.session_state.get("voorkeursterm", "")
        }
    
    @staticmethod
    def clear_definition_results():
        """Clear all definition-related results from session state."""
        keys_to_clear = [
            "definitie_origineel", "definitie_gecorrigeerd", "gegenereerd",
            "marker", "beoordeling_gen", "beoordeling", "aangepaste_definitie",
            "voorbeeld_zinnen", "praktijkvoorbeelden", "tegenvoorbeelden",
            "toelichting", "synoniemen", "antoniemen", "bronnen_gebruikt"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = SessionStateManager.DEFAULT_VALUES.get(key, "")
    
    @staticmethod
    def has_generated_definition() -> bool:
        """
        Check if there's a generated definition available.
        
        Returns:
            True if definition exists and is not empty
        """
        definitie = st.session_state.get("definitie_gecorrigeerd", "")
        return isinstance(definitie, str) and len(definitie.strip()) > 3