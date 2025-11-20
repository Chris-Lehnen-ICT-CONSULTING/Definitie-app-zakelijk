"""UI helper for feature toggles.

This module contains UI-specific feature toggle components.
Services should not depend on these UI elements.
"""

import streamlit as st


def render_feature_flag_toggle():
    """
    Render a toggle for new services in the Streamlit sidebar.

    This is a UI-only component that does not affect service layer.
    V2 services are always used per US-043.
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🚀 V2 Services")

        # Always show V2 is active
        st.success("✅ V2 services active (default)")

        # Show info about legacy removal
        with st.expander("i About V2 Services"):
            st.markdown(
                """
            **V2 Services are now the default and only path.**

            Changes per US-043:
            - Legacy routes removed
            - V1 orchestrator deprecated
            - Context fields are list-based
            - Full async support

            For more info, see EPIC-010 documentation.
            """
            )

        return True  # Always return True for V2


def render_legacy_warning(component_name: str) -> None:
    """Toon een waarschuwing voor legacy componenten in de UI."""
    st.warning(
        f"⚠️ **Legacy Component**: {component_name}\n\n"
        f"Deze component is verouderd en wordt in een toekomstige versie verwijderd. "
        f"Gebruik de V2-implementatie waar mogelijk."
    )
