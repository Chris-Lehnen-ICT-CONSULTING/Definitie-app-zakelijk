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
from utils.exceptions import log_and_display_error

# Initialize logger
logger = get_logger(__name__)


def main():
    """Main application function."""
    try:
        # Initialize session state
        SessionStateManager.initialize_session_state()
        
        # Create and render tabbed interface
        interface = TabbedInterface()
        interface.render()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(log_and_display_error(e, "application startup"))


if __name__ == "__main__":
    main()