"""
Synonym Metrics Dashboard - PHASE 4.2 Implementation.

Standalone page voor real-time monitoring van Synonym Orchestrator v3.1.
Deze page is onderdeel van de Streamlit multipage app en verschijnt automatisch
in de sidebar als "Synonym Metrics".

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 1082-1104: Metrics Dashboard specification
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

# Import de metrics tab component
from ui.tabs.synonym_metrics_tab import SynonymMetricsTab

# Page config
st.set_page_config(
    page_title="Synonym Metrics - DefinitieAgent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>📊 Synonym System Metrics</h1>
        <p style="font-size: 16px; color: #666;">
            Real-time monitoring van Synonym Orchestrator v3.1 (Architecture PHASE 3)
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

# Info banner
st.info(
    """
    **💡 Dashboard Overzicht:**
    - **🚀 Cache Performance:** Hit rate, size, TTL metrics
    - **🤖 GPT-4 Enrichment:** Success rate, avg duration, timeouts
    - **✅ Approval Workflow:** Pending review count, approval rate
    - **📈 Top Synonyms:** Most used synonyms by usage count

    **Architecture:** Synonym Orchestrator v3.1 (Graph-Based Registry)
"""
)

st.markdown("---")

# Render de metrics dashboard
metrics_tab = SynonymMetricsTab()
metrics_tab.render()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
        DefinitieAgent Synonym Metrics |
        <a href="/" target="_self">← Terug naar hoofdapplicatie</a> |
        <a href="/synonym_review" target="_self">Synonym Review →</a>
    </div>
""",
    unsafe_allow_html=True,
)
