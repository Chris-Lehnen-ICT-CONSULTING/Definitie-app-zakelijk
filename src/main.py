"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.

This module serves as the entry point for the DefinitieAgent application,
handling initialization, configuration, and launching the main user interface.
"""

import logging
import sys
from pathlib import Path

# Add src directory to Python path for proper imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st  # Web applicatie framework voor de gebruikersinterface

from ui.session_state import SessionStateManager  # Sessie status beheer
from ui.tabbed_interface import TabbedInterface  # Hoofd gebruikersinterface
from utils.exceptions import log_and_display_error  # Foutafhandeling utilities

# Configureer basis logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
try:
    # Voeg PII/redactie filter toe aan root logger
    from utils.logging_filters import PIIRedactingFilter

    _root = logging.getLogger()
    if not any(isinstance(f, PIIRedactingFilter) for f in _root.filters):
        _root.addFilter(PIIRedactingFilter())
except Exception:  # Fail-safe: logging mag nooit breken
    pass

# Initialiseer logger - Stel logging in voor deze module
logger = logging.getLogger(__name__)  # Verkrijg logger instantie voor dit bestand

# Configureer Streamlit pagina - Stel basis pagina instellingen in
st.set_page_config(
    page_title="DefinitieAgent",  # Browser tab titel
    page_icon="🧠",  # Browser tab icoon
    layout="wide",  # Gebruik volledige breedte van de pagina
    initial_sidebar_state="expanded",  # Start met uitgevouwen sidebar
)

# Let op: geen .env-bestand laden; vertrouw op systeem-omgeving


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
        logger.error(f"Applicatie fout: {e!s}")  # Log fout voor debugging
        st.error(
            log_and_display_error(e, "applicatie opstarten")
        )  # Toon gebruikersvriendelijke fout


if __name__ == "__main__":
    # Start de applicatie alleen als dit bestand direct wordt uitgevoerd
    main()  # Roep de hoofd functie aan om de applicatie te starten
