"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.

This module serves as the entry point for the DefinitieAgent application,
handling initialization, configuration, and launching the main user interface.
"""

import logging
import os
import sys
import time
from pathlib import Path

# Add src directory to Python path for proper imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st  # Web applicatie framework voor de gebruikersinterface

from ui.session_state import SessionStateManager  # Sessie status beheer
from ui.tabbed_interface import TabbedInterface  # Hoofd gebruikersinterface
from utils.exceptions import log_and_display_error  # Foutafhandeling utilities
# Setup structured logging if enabled via environment variable
from utils.structured_logging import setup_structured_logging

if os.getenv("STRUCTURED_LOGGING", "false").lower() == "true":
    setup_structured_logging(enable_json=True, log_file="logs/app.json.log")

# Configureer basis logging (fallback als structured logging niet enabled is)
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
    # Track rerun performance - Meet Streamlit rerun tijd
    # BELANGRIJK: Timer moet binnen main() staan, niet op module niveau
    # Streamlit importeert de module EENMAAL en roept main() meerdere keren aan
    rerun_start = time.perf_counter()

    try:
        # Initialiseer sessie status - Stel Streamlit sessie status in
        SessionStateManager.initialize_session_state()  # Stel standaardwaarden in voor UI status

        # Maak en render tabbed interface - Maak en toon de hoofd gebruikersinterface
        interface = TabbedInterface()  # Instantieer de tabbed interface controller
        interface.render()  # Render de complete gebruikersinterface

        # Track rerun performance na render
        _track_rerun_performance(rerun_start)

    except Exception as e:
        # Log en toon startup fouten - Log en toon opstartfouten
        logger.error(f"Applicatie fout: {e!s}")  # Log fout voor debugging
        st.error(
            log_and_display_error(e, "applicatie opstarten")
        )  # Toon gebruikersvriendelijke fout


def _track_rerun_performance(start_time: float):
    """Track Streamlit rerun performance en check voor regressies.

    Deze functie meet de tijd voor een Streamlit rerun (UI framework overhead).
    Dit is NIET de tijd voor definitie generatie of andere business operaties.

    Args:
        start_time: perf_counter() value at start of main()

    Note:
        Metric naam is "streamlit_rerun_ms" omdat we reruns meten, niet cold startup.
        Typische waarden: 10-100ms voor normale reruns.
        Lange tijden (>1s) duiden op probleem in UI rendering, niet in business logica.
    """
    try:
        from monitoring.performance_tracker import get_tracker

        rerun_time_ms = (time.perf_counter() - start_time) * 1000

        # Track metric met session metadata
        tracker = get_tracker()
        tracker.track_metric(
            "streamlit_rerun_ms",
            rerun_time_ms,
            metadata={
                "session_id": id(st.session_state),
                "platform": sys.platform,
            },
        )

        # Check voor performance regressie
        alert = tracker.check_regression("streamlit_rerun_ms", rerun_time_ms)
        if alert == "CRITICAL":
            logger.warning(
                f"CRITICAL rerun regressie: {rerun_time_ms:.1f}ms "
                f"(>20% slechter dan baseline)"
            )
        elif alert == "WARNING":
            logger.warning(
                f"WARNING rerun regressie: {rerun_time_ms:.1f}ms "
                f"(>10% slechter dan baseline)"
            )
        else:
            logger.info(f"Rerun tijd: {rerun_time_ms:.1f}ms")

    except Exception as e:
        # Performance tracking mag nooit de applicatie breken
        logger.debug(f"Performance tracking fout (non-critical): {e}")


if __name__ == "__main__":
    # Start de applicatie alleen als dit bestand direct wordt uitgevoerd
    main()  # Roep de hoofd functie aan om de applicatie te starten
