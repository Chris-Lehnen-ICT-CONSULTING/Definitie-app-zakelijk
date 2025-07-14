"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.

This module serves as the entry point for the DefinitieAgent application,
handling initialization, configuration, and launching the main user interface.
"""

import streamlit as st  # Web applicatie framework voor de gebruikersinterface
from dotenv import load_dotenv  # Laadt omgevingsvariabelen uit .env bestand

# Configureer Streamlit pagina - Stel basis pagina instellingen in
st.set_page_config(
    page_title="DefinitieAgent",  # Browser tab titel
    page_icon="🧠",  # Browser tab icoon
    layout="wide",  # Gebruik volledige breedte van de pagina
    initial_sidebar_state="expanded"  # Start met uitgevouwen sidebar
)

# Laad omgevingsvariabelen - Laad configuratie uit .env bestand
load_dotenv()  # Laadt API keys, database configuratie, etc.

# Importeer applicatie modules - Importeer kern applicatie componenten
import sys
import os
# Voeg root directory toe aan Python path voor logs module toegang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logs.application.log_definitie import get_logger  # Logging systeem uit root logs directory
from ui.session_state import SessionStateManager  # Sessie status beheer
from ui.tabbed_interface import TabbedInterface  # Hoofd gebruikersinterface
from utils.exceptions import log_and_display_error  # Foutafhandeling utilities

# Initialiseer logger - Stel logging in voor deze module
logger = get_logger(__name__)  # Verkrijg logger instantie voor dit bestand


def main():
    """Hoofd applicatie functie.
    
    Deze functie is het startpunt voor de DefinitieAgent applicatie.
    Het initialiseert alle benodigde componenten en start de gebruikersinterface.
    
    Raises:
        Exception: Alle onverwachte fouten worden gelogd en getoond aan gebruiker
    """
    try:
        # Initialiseer sessie status - Stel Streamlit sessie status in
        SessionStateManager.initialize_session_state()  # Stel standaardwaarden in voor UI status
        
        # Maak en render tabbed interface - Maak en toon de hoofd gebruikersinterface
        interface = TabbedInterface()  # Instantieer de tabbed interface controller
        interface.render()  # Render de complete gebruikersinterface
            
    except Exception as e:
        # Log en toon startup fouten - Log en toon opstartfouten
        logger.error(f"Applicatie fout: {str(e)}")  # Log fout voor debugging
        st.error(log_and_display_error(e, "applicatie opstarten"))  # Toon gebruikersvriendelijke fout


if __name__ == "__main__":
    # Start de applicatie alleen als dit bestand direct wordt uitgevoerd
    main()  # Roep de hoofd functie aan om de applicatie te starten