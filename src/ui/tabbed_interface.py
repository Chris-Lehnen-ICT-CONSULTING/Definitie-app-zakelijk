"""
Tabbed Interface voor DefinitieAgent - Nieuwe UI architectuur.
Implementeert de requirements uit Project Requirements Document.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime

from ui.components.context_selector import ContextSelector
from ui.components.definition_generator_tab import DefinitionGeneratorTab
from ui.components.expert_review_tab import ExpertReviewTab
from ui.components.history_tab import HistoryTab
from ui.components.export_tab import ExportTab
from ui.session_state import SessionStateManager
from database.definitie_repository import get_definitie_repository, DefinitieRecord
from integration.definitie_checker import DefinitieChecker


class TabbedInterface:
    """Main tabbed interface controller voor DefinitieAgent."""
    
    def __init__(self):
        """Initialiseer tabbed interface met services."""
        self.repository = get_definitie_repository()
        self.checker = DefinitieChecker(self.repository)
        self.context_selector = ContextSelector()
        
        # Initialize tab components
        self.definition_tab = DefinitionGeneratorTab(self.checker)
        self.expert_tab = ExpertReviewTab(self.repository)
        self.history_tab = HistoryTab(self.repository)
        self.export_tab = ExportTab(self.repository)
        
        # Tab configuration
        self.tab_config = {
            "generator": {
                "title": "🚀 Definitie Generatie",
                "icon": "🚀",
                "description": "Genereer nieuwe definities met AI-ondersteuning"
            },
            "expert": {
                "title": "👨‍💼 Expert Review",  
                "icon": "👨‍💼",
                "description": "Review en goedkeuring van definities"
            },
            "history": {
                "title": "📜 Geschiedenis",
                "icon": "📜", 
                "description": "Bekijk historie van definities en wijzigingen"
            },
            "export": {
                "title": "📤 Export & Beheer",
                "icon": "📤",
                "description": "Exporteer en beheer definities"
            }
        }
    
    def render(self):
        """Render de volledige tabbed interface."""
        # App header
        self._render_header()
        
        # Global context selector (boven tabs)
        self._render_global_context()
        
        # Main tabs
        self._render_main_tabs()
        
        # Footer met systeem informatie
        self._render_footer()
    
    def _render_header(self):
        """Render applicatie header."""
        st.set_page_config(
            page_title="DefinitieAgent 2.0",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Header met logo en titel
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
                <div style="text-align: center;">
                    <h1>🧠 DefinitieAgent 2.0</h1>
                    <p style="font-size: 18px; color: #666;">
                        AI-ondersteunde definitie generatie en kwaliteitscontrole
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        # Status indicator
        with col3:
            self._render_status_indicator()
    
    def _render_status_indicator(self):
        """Render systeem status indicator."""
        # Simple health check
        try:
            stats = self.repository.get_statistics()
            total_definitions = stats.get('total_definities', 0)
            
            st.success(f"✅ Systeem Online\\n{total_definitions} definities beschikbaar")
        except Exception as e:
            st.error(f"❌ Systeem Issue\\n{str(e)[:50]}...")
    
    def _render_global_context(self):
        """Render globale context selector."""
        st.markdown("### 🎯 Context Configuratie")
        
        with st.expander("Selecteer context voor definitie generatie", expanded=False):
            context_data = self.context_selector.render()
            
            # Store in session state voor gebruik in tabs
            SessionStateManager.set_value("global_context", context_data)
            
            # Show selected context summary
            if any(context_data.values()):
                self._render_context_summary(context_data)
    
    def _render_context_summary(self, context_data: Dict[str, Any]):
        """Render samenvatting van geselecteerde context."""
        summary_parts = []
        
        if context_data.get("organisatorische_context"):
            summary_parts.append(f"📋 Org: {', '.join(context_data['organisatorische_context'])}")
        
        if context_data.get("juridische_context"):
            summary_parts.append(f"⚖️ Juridisch: {', '.join(context_data['juridische_context'])}")
        
        if context_data.get("wettelijke_basis"):
            summary_parts.append(f"📜 Wet: {', '.join(context_data['wettelijke_basis'])}")
        
        if summary_parts:
            st.info(" | ".join(summary_parts))
    
    def _render_main_tabs(self):
        """Render de hoofdtabbladen."""
        # Create tabs
        tab_keys = list(self.tab_config.keys())
        tab_titles = [self.tab_config[key]["title"] for key in tab_keys]
        
        tabs = st.tabs(tab_titles)
        
        # Render each tab
        for i, (tab_key, tab) in enumerate(zip(tab_keys, tabs)):
            with tab:
                self._render_tab_content(tab_key)
    
    def _render_tab_content(self, tab_key: str):
        """Render inhoud van specifiek tabblad."""
        config = self.tab_config[tab_key]
        
        # Tab header
        st.markdown(f"""
            <div style="margin-bottom: 20px; padding: 15px; 
                        background: linear-gradient(90deg, #f0f2f6, #ffffff); 
                        border-radius: 10px; border-left: 4px solid #ff6b6b;">
                <h3 style="margin: 0; color: #1f1f1f;">
                    {config['icon']} {config['title']}
                </h3>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                    {config['description']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tab-specific content
        if tab_key == "generator":
            self.definition_tab.render()
        elif tab_key == "expert":
            self.expert_tab.render()
        elif tab_key == "history":
            self.history_tab.render()
        elif tab_key == "export":
            self.export_tab.render()
    
    def _render_footer(self):
        """Render applicatie footer."""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        with col2:
            st.markdown("""
                <div style="text-align: center; color: #666; font-size: 12px;">
                    DefinitieAgent 2.0 | Laatste update: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Quick stats
            try:
                stats = self.repository.get_statistics()
                st.metric("📊 Definities", stats.get('total_definities', 0))
            except:
                pass


def render_tabbed_interface():
    """Main entry point voor tabbed interface."""
    # Initialize session state
    SessionStateManager.initialize_session_state()
    
    # Render interface
    interface = TabbedInterface()
    interface.render()


if __name__ == "__main__":
    render_tabbed_interface()