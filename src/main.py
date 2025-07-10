"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.
"""

import streamlit as st
from dotenv import load_dotenv

# Configure Streamlit page
st.set_page_config(
    page_title="DefinitieAgent", 
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Import application modules
from log.log_definitie import get_logger
from ui.session_state import SessionStateManager
from ui.tabbed_interface import TabbedInterface
from database.definitie_repository import DefinitieRepository
from integration.definitie_checker import DefinitieChecker
from utils.exceptions import log_and_display_error

# Initialize logger
logger = get_logger(__name__)


def main():
    """Main application function."""
    try:
        # Initialize session state
        SessionStateManager.initialize_session_state()
        
        # Initialize database and services
        repository = DefinitieRepository()
        checker = DefinitieChecker(repository)
        
        # Create and render tabbed interface
        interface = TabbedInterface(checker, repository)
        interface.render()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(log_and_display_error(e, "application startup"))


if __name__ == "__main__":
    main()