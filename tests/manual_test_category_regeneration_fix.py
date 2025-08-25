#!/usr/bin/env python3
"""
Manual test voor category regeneration fix.

Dit test script verifieert dat na het wijzigen van een ontologische categorie
de regeneratie opties correct worden getoond.

Bug: Na categorie wijziging werd st.rerun() aangeroepen waardoor de 
regeneration preview direct verdween.

Fix: st.rerun() verwijderd zodat preview zichtbaar blijft.
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.session_state import SessionStateManager
from ui.components.definition_generator_tab import DefinitionGeneratorTab
from datetime import datetime, timezone

def test_category_change_flow():
    """Test de category change → regeneration preview flow."""
    
    st.title("🧪 Category Regeneration Fix Test")
    
    st.markdown("""
    ## Test Scenario
    
    1. Genereer een definitie
    2. Klik op "🔄 Wijzig Categorie"
    3. Selecteer een andere categorie
    4. Klik op "✅ Toepassen"
    5. **Verwacht**: Regeneration preview moet zichtbaar worden
    
    ## Bug die we fixen:
    - ❌ **Oud**: Preview verdween direct door st.rerun()
    - ✅ **Nieuw**: Preview blijft zichtbaar met 3 actie knoppen
    """)
    
    # Mock generation result
    if st.button("🎭 Mock een gegenereerde definitie"):
        mock_result = {
            "begrip": "vaststellen",
            "agent_result": {
                "definitie_gecorrigeerd": "Activiteit waarbij een officiële beslissing wordt genomen.",
                "definitie_origineel": "Vaststellen betreft een activiteit waarbij een officiële beslissing wordt genomen.",
                "validation_score": 0.85,
                "success": True
            },
            "saved_record": None,  # Test zonder database record
            "determined_category": "proces",
            "category_reasoning": "Het begrip beschrijft een activiteit",
            "category_scores": {
                "type": 0.2,
                "proces": 0.8,
                "resultaat": 0.1,
                "exemplaar": 0.1
            },
            "timestamp": datetime.now(timezone.utc)
        }
        
        SessionStateManager.set_value("last_generation_result", mock_result)
        st.success("✅ Mock definitie aangemaakt!")
        st.rerun()
    
    # Render the tab
    if SessionStateManager.get_value("last_generation_result"):
        tab = DefinitionGeneratorTab()
        
        st.markdown("---")
        st.markdown("### 🎯 Test de Fix:")
        
        # Show current state
        current_result = SessionStateManager.get_value("last_generation_result")
        st.info(f"**Huidige categorie**: {current_result.get('determined_category', 'onbekend')}")
        
        # Render the results (dit toont de categorie sectie)
        tab._render_generation_results(current_result)
        
        # Debug info
        with st.expander("🐛 Debug Info"):
            st.write("**Session State Keys:**")
            st.write(f"- show_category_selector: {SessionStateManager.get_value('show_category_selector', False)}")
            st.write(f"- last_generation_result keys: {list(current_result.keys())}")
            
            st.markdown("""
            **Verwacht gedrag na fix:**
            1. Klik "🔄 Wijzig Categorie"
            2. Selector verschijnt
            3. Kies nieuwe categorie
            4. Klik "✅ Toepassen"
            5. **Preview blijft zichtbaar** met:
               - Oude vs nieuwe categorie
               - Huidige definitie
               - 3 actie knoppen (Direct/Handmatig/Behoud)
            """)

if __name__ == "__main__":
    # Initialize session state
    SessionStateManager.get_value("initialized", True)
    
    # Run test
    test_category_change_flow()