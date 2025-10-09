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

import asyncio

import streamlit as st

# Import de synonym review tab component
from services.synonym_automation.workflow import SynonymWorkflow
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

# Generate section
with st.expander("🚀 Genereer Nieuwe Synoniemen", expanded=False):
    st.markdown("**Genereer AI-gestuurde synonym suggesties voor juridische termen**")

    col1, col2 = st.columns([3, 1])

    with col1:
        term = st.text_input(
            "Juridische term",
            placeholder="bijv. verdachte, getuige, rechter...",
            help="Voer een juridische term in waarvoor synoniemen gegenereerd moeten worden",
        )

    with col2:
        confidence = st.slider(
            "Min. Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Alleen suggesties met minimaal deze confidence score",
        )

    if st.button("🤖 Genereer Suggesties", type="primary", use_container_width=True):
        if not term or not term.strip():
            st.error("❌ Voer eerst een term in")
        else:
            with st.spinner(f"🔄 GPT-4 genereert synoniemen voor '{term}'..."):
                try:
                    workflow = SynonymWorkflow()

                    # Run async function
                    suggestions = asyncio.run(
                        workflow.suggest_synonyms(
                            hoofdterm=term.strip(), confidence_threshold=confidence
                        )
                    )

                    if suggestions:
                        st.success(
                            f"✅ {len(suggestions)} suggesties gegenereerd en opgeslagen!"
                        )

                        # Show preview
                        st.markdown("**Preview:**")
                        for sug in suggestions[:5]:  # Show max 5
                            st.write(
                                f"- **{sug.synoniem}** (confidence: {sug.confidence:.2f})"
                            )

                        if len(suggestions) > 5:
                            st.caption(f"... en {len(suggestions) - 5} meer")

                        st.info(
                            "💡 Scroll naar beneden om de suggesties te reviewen en goed te keuren"
                        )

                        # Rerun to refresh the review table with new suggestions
                        st.rerun()
                    else:
                        st.warning(
                            f"⚠️ Geen suggesties gevonden voor '{term}' met confidence ≥ {confidence}"
                        )

                except Exception as e:
                    st.error(f"❌ Fout bij genereren: {e}")
                    st.exception(e)

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
