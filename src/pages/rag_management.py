"""
RAG Management - Standalone Page (DEF-365)

Streamlit multipage app standalone page voor RAG collection en document beheer.

Features:
- Collection CRUD (aanmaken, selecteren, verwijderen)
- Document upload, tekst invoer, verwijderen
- Live statistieken (document/chunk counts)
- Dubbel-klik bevestiging voor destructieve acties
"""

import logging
import sys
from pathlib import Path

# Add src/ to path for imports (consistent met main.py)
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

from services.container import get_container

logger = logging.getLogger(__name__)

# ========================================
# PAGE CONFIG
# ========================================

st.set_page_config(
    page_title="RAG Management - DefinitieAgent",
    page_icon="\U0001f4da",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========================================
# HEADER
# ========================================

st.markdown("# \U0001f4da RAG Management")
st.caption(
    "Beheer RAG collections en documenten voor context-verrijkte definitie generatie."
)

# ========================================
# INITIALIZE SERVICES
# ========================================


@st.cache_resource
def get_services():
    """Initialize RAG management services (cached per session)."""
    container = get_container()
    return {
        "management": container.rag_management_service,
        "rag": container.rag_service,
    }


services = get_services()

# ========================================
# RENDER
# ========================================

from ui.renderers.rag_management_renderer import RAGManagementRenderer

renderer = RAGManagementRenderer(
    management_service=services["management"],
    rag_service=services["rag"],
)

selected_id = renderer.render_sidebar()

if selected_id is not None:
    renderer.render_document_panel(selected_id)
else:
    st.info("Selecteer een collection in de sidebar of maak een nieuwe aan.")

# ========================================
# FOOTER
# ========================================

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-size: 12px;">'
    "DefinitieAgent RAG Management (DEF-365) | "
    '<a href="/" target="_self">\u2190 Terug naar hoofdapplicatie</a>'
    "</div>",
    unsafe_allow_html=True,
)
