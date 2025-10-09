"""
Synonym Review & Approval - Admin Tool

Standalone page voor het reviewen en goedkeuren van AI-gegenereerde synoniemen.
Deze page is onderdeel van de Streamlit multipage app en verschijnt automatisch
in de sidebar als "Synonym Review".
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

# Import de synonym review tab component
from ui.tabs.synonym_review_tab import render_synonym_review_tab

# Page config
st.set_page_config(
    page_title="Synonym Review - DefinitieAgent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🔍 Synonym Review & Approval</h1>
        <p style="font-size: 16px; color: #666;">
            Admin tool voor het reviewen en goedkeuren van AI-gegenereerde synoniemen
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

# Info banner
st.info(
    """
    **💡 Workflow:**
    1. GPT-4 genereert synonym suggesties (via `SynonymWorkflow.suggest_synonyms()`)
    2. Review suggesties in deze interface
    3. Approve → toevoegen aan `juridische_synoniemen.yaml` + database update
    4. Reject → markeren als afgewezen in database

    **📊 Status:** Pending = wacht op review | Approved = toegevoegd aan YAML | Rejected = afgewezen
"""
)

st.markdown("---")

# Render de synonym review tab
render_synonym_review_tab()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
        DefinitieAgent Synonym Review |
        <a href="/" target="_self">← Terug naar hoofdapplicatie</a>
    </div>
""",
    unsafe_allow_html=True,
)
