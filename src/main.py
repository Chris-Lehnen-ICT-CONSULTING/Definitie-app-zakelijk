"""
Main application file for DefinitieAgent - refactored version.
A Streamlit application for generating and validating legal definitions.
"""

import streamlit as st
from dotenv import load_dotenv

# Configure Streamlit page
st.set_page_config(page_title="DefinitieAgent", page_icon="🧠")

# Load environment variables
load_dotenv()

# Import application modules
from log.log_definitie import get_logger
from config.config_loader import laad_toetsregels
from ui.session_state import SessionStateManager
from ui.components import UIComponents
from services.definition_service import DefinitionService
from utils.exceptions import log_and_display_error

# Initialize logger
logger = get_logger(__name__)

# Initialize services
definition_service = DefinitionService()


def main():
    """Main application function."""
    try:
        # Initialize session state
        SessionStateManager.initialize_session_state()
        
        # Load quality rules
        toetsregels = laad_toetsregels()
        
        # Render input form
        form_data = UIComponents.render_input_form()
        
        # Generate definition button
        actie = st.button("Genereer definitie")
        
        # Process definition generation
        if actie and form_data["begrip"].strip():
            with st.spinner("Genereren van definitie..."):
                success = definition_service.process_complete_definition(form_data, toetsregels)
                
                if not success:
                    st.error("❌ Er is een fout opgetreden bij het genereren van de definitie.")
        
        # Create tabs for different views
        tab_ai, tab_aangepast, tab_expert = st.tabs([
            "🤖 AI-gegenereerde definitie",
            "✍️ Aangepaste definitie", 
            "📋 Expert-review & toelichting"
        ])
        
        # Render AI tab
        with tab_ai:
            UIComponents.render_ai_tab()
        
        # Render modified definition tab
        with tab_aangepast:
            hercontroleer = UIComponents.render_modified_tab()
            
            if hercontroleer:
                aangepaste_definitie = SessionStateManager.get_value("aangepaste_definitie")
                
                if aangepaste_definitie.strip():
                    with st.spinner("Hercontroleren van definitie..."):
                        success = definition_service.process_modified_definition(form_data, toetsregels)
                        
                        if success:
                            st.success("✅ Aangepaste definitie succesvol gecontroleerd.")
                        else:
                            st.error("❌ Er is een fout opgetreden bij het controleren van de aangepaste definitie.")
                else:
                    st.warning("⚠️ Voer eerst een aangepaste definitie in.")
            
            # Show testing results for modified definition
            UIComponents.render_modified_testing_results()
        
        # Render expert review tab
        with tab_expert:
            UIComponents.render_expert_tab()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(log_and_display_error(e, "application startup"))


if __name__ == "__main__":
    main()