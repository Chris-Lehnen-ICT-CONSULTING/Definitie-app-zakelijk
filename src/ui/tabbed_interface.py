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
from database.definitie_repository import get_definitie_repository, DefinitieRecord, DefinitieStatus
from integration.definitie_checker import DefinitieChecker
from generation.definitie_generator import OntologischeCategorie
import logging

logger = logging.getLogger(__name__)


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
        
        # Quick Start sectie (oorspronkelijke workflow)
        self._render_quick_start_section()
        
        st.markdown("---")
        
        # Advanced sectie met tabs
        st.markdown("### 🔧 Geavanceerde Functies")
        
        # Global context selector (boven tabs)
        self._render_global_context()
        
        # Main tabs
        self._render_main_tabs()
        
        # Footer met systeem informatie
        self._render_footer()
    
    def _handle_quick_generation(self, begrip, categorie, org_context, jur_context, wet_basis, voorsteller, include_examples):
        """Handle snelle definitie generatie."""
        try:
            with st.spinner("🔄 Genereren van definitie..."):
                # Gebruik de eerste organisatorische context voor generatie
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""
                
                # Bepaal automatisch de ontologische categorie via AI
                auto_categorie = self._determine_ontological_category(begrip, primary_org, primary_jur)
                
                # Voer complete workflow uit
                check_result, agent_result, saved_record = self.checker.generate_with_check(
                    begrip=begrip,
                    organisatorische_context=primary_org,
                    juridische_context=primary_jur,
                    categorie=auto_categorie,
                    force_generate=False,
                    created_by=voorsteller or "quick_user"
                )
                
                # Store results in session voor display
                SessionStateManager.set_value("quick_last_result", {
                    "check_result": check_result,
                    "agent_result": agent_result,
                    "saved_record": saved_record,
                    "include_examples": include_examples,
                    "determined_category": auto_categorie.value,
                    "timestamp": datetime.now()
                })
                
                st.success("✅ Definitie succesvol gegenereerd!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Fout bij generatie: {str(e)}")
            logger.error(f"Quick generation failed: {e}")
    
    def _handle_quick_duplicate_check(self, begrip, org_context, jur_context):
        """Handle snelle duplicate check."""
        try:
            with st.spinner("🔍 Controleren op duplicates..."):
                from generation.definitie_generator import OntologischeCategorie
                
                check_result = self.checker.check_before_generation(
                    begrip=begrip,
                    organisatorische_context=org_context,
                    juridische_context=jur_context,
                    categorie=OntologischeCategorie.PROCES  # Default
                )
                
                SessionStateManager.set_value("quick_duplicate_result", {
                    "check_result": check_result,
                    "timestamp": datetime.now()
                })
                
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Fout bij duplicate check: {str(e)}")
            logger.error(f"Quick duplicate check failed: {e}")
    
    def _clear_quick_form(self):
        """Wis alle quick form velden."""
        keys_to_clear = [
            "quick_begrip", "quick_categorie", "quick_org_context", 
            "quick_jur_context", "quick_wet_basis", "quick_voorsteller",
            "quick_ketenpartners", "quick_include_examples",
            "quick_last_result", "quick_duplicate_result"
        ]
        
        for key in keys_to_clear:
            SessionStateManager.clear_value(key)
    
    def _render_quick_results(self):
        """Render resultaten van quick generation."""
        # Check voor generatie resultaten
        last_result = SessionStateManager.get_value("quick_last_result")
        duplicate_result = SessionStateManager.get_value("quick_duplicate_result")
        
        if duplicate_result:
            self._render_quick_duplicate_results(duplicate_result["check_result"])
        
        if last_result:
            self._render_quick_generation_results(last_result)
    
    def _render_quick_duplicate_results(self, check_result):
        """Render duplicate check resultaten."""
        st.markdown("#### 🔍 Duplicate Check Resultaten")
        
        if check_result.action.value == "proceed":
            st.success(f"✅ {check_result.message}")
        elif check_result.action.value == "use_existing":
            st.warning(f"⚠️ {check_result.message}")
            
            if check_result.existing_definitie:
                with st.expander("📋 Bestaande definitie details", expanded=True):
                    st.info(check_result.existing_definitie.definitie)
                    st.caption(f"Context: {check_result.existing_definitie.organisatorische_context} | Status: {check_result.existing_definitie.status}")
        else:
            st.info(f"ℹ️ {check_result.message}")
    
    def _render_quick_generation_results(self, result_data):
        """Render generatie resultaten."""
        st.markdown("#### 🚀 Generatie Resultaten")
        
        agent_result = result_data.get("agent_result")
        saved_record = result_data.get("saved_record")
        
        if agent_result and agent_result.success:
            # Toon gegenereerde definitie
            st.markdown("##### 📝 Gegenereerde Definitie")
            st.info(agent_result.final_definitie)
            
            # Toon automatisch bepaalde categorie
            determined_category = result_data.get("determined_category", "proces")
            st.success(f"🤖 **Ontologische categorie (AI bepaald):** {determined_category.capitalize()}")
            
            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Kwaliteitsscore", f"{agent_result.final_score:.2f}")
            with col2:
                st.metric("Iteraties", agent_result.iteration_count)
            with col3:
                st.metric("Verwerkingstijd", f"{agent_result.total_processing_time:.1f}s")
            
            # Database info
            if saved_record:
                st.success(f"✅ Definitie opgeslagen in database (ID: {saved_record.id})")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📝 Submit voor Review"):
                        try:
                            success = self.repository.change_status(
                                saved_record.id, 
                                DefinitieStatus.REVIEW, 
                                "quick_user", 
                                "Submitted via quick interface"
                            )
                            if success:
                                st.success("✅ Ingediend voor expert review")
                            else:
                                st.error("❌ Kon status niet wijzigen")
                        except Exception as e:
                            st.error(f"❌ Fout: {str(e)}")
                
                with col2:
                    if st.button("📤 Exporteer TXT"):
                        # Quick TXT export
                        export_text = f"""BEGRIP: {saved_record.begrip}
DEFINITIE: {saved_record.definitie}
CATEGORIE: {saved_record.categorie}
CONTEXT: {saved_record.organisatorische_context}
STATUS: {saved_record.status}
SCORE: {agent_result.final_score:.2f}
GEGENEREERD: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                        st.download_button(
                            "💾 Download TXT",
                            export_text,
                            file_name=f"definitie_{saved_record.begrip}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
                
                with col3:
                    if st.button("🗑️ Wis Resultaten"):
                        SessionStateManager.clear_value("quick_last_result")
                        SessionStateManager.clear_value("quick_duplicate_result")
                        st.rerun()
        
        elif agent_result:
            st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {agent_result.reason}")
        else:
            st.error("❌ Generatie gefaald")
    
    def _determine_ontological_category(self, begrip, org_context, jur_context):
        """Bepaal automatisch de ontologische categorie via AI analyse."""
        try:
            # Eenvoudige heuristic gebaseerd op woord patronen
            # Later kan dit vervangen worden door GPT call
            
            begrip_lower = begrip.lower()
            
            # Proces patronen
            proces_indicators = [
                'atie', 'eren', 'ing', 'verificatie', 'authenticatie', 'validatie',
                'controle', 'check', 'beoordeling', 'analyse', 'behandeling',
                'vaststelling', 'bepaling', 'registratie', 'identificatie'
            ]
            
            # Type patronen  
            type_indicators = [
                'bewijs', 'document', 'middel', 'systeem', 'methode', 'tool',
                'instrument', 'gegeven', 'kenmerk', 'eigenschap'
            ]
            
            # Resultaat patronen
            resultaat_indicators = [
                'besluit', 'uitslag', 'rapport', 'conclusie', 'bevinding',
                'resultaat', 'uitkomst', 'advies', 'oordeel'
            ]
            
            # Exemplaar patronen
            exemplaar_indicators = [
                'specifiek', 'individueel', 'uniek', 'persoon', 'zaak',
                'instantie', 'geval', 'situatie'
            ]
            
            # Score per categorie
            scores = {
                'proces': 0,
                'type': 0, 
                'resultaat': 0,
                'exemplaar': 0
            }
            
            # Check proces indicators
            for indicator in proces_indicators:
                if indicator in begrip_lower:
                    scores['proces'] += 1
            
            # Check type indicators  
            for indicator in type_indicators:
                if indicator in begrip_lower:
                    scores['type'] += 1
                    
            # Check resultaat indicators
            for indicator in resultaat_indicators:
                if indicator in begrip_lower:
                    scores['resultaat'] += 1
                    
            # Check exemplaar indicators
            for indicator in exemplaar_indicators:
                if indicator in begrip_lower:
                    scores['exemplaar'] += 1
            
            # Bepaal hoogste score
            best_category = max(scores, key=scores.get)
            
            # Default naar proces als geen duidelijke match
            if scores[best_category] == 0:
                best_category = 'proces'
            
            logger.info(f"Auto-determined category voor '{begrip}': {best_category} (scores: {scores})")
            return OntologischeCategorie(best_category)
            
        except Exception as e:
            logger.warning(f"Failed to auto-determine category: {e}")
            # Default naar proces
            return OntologischeCategorie.PROCES
    
    def _render_quick_start_section(self):
        """Render quick start sectie met oorspronkelijke workflow."""
        st.markdown("### 🚀 Snelle Definitie Generatie")
        st.markdown("*Voor eenvoudige definities - gebruik direct onderstaande velden en klik op 'Genereer'*")
        
        # Main form in columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Term input (hoofdveld)
            begrip = st.text_input(
                "📝 Voer een term in waarvoor een definitie moet worden gegenereerd",
                value=SessionStateManager.get_value("quick_begrip", ""),
                placeholder="bijv. authenticatie, verificatie, identiteitsvaststelling...",
                help="Het centrale begrip waarvoor een definitie gegenereerd wordt"
            )
            SessionStateManager.set_value("quick_begrip", begrip)
            
        with col2:
            # AI informatie / status
            st.markdown("🤖 **AI Analyse**")
            st.info("De ontologische categorie wordt automatisch bepaald door de AI op basis van de term en context")
            
            # Optionele hint voor gebruiker
            st.markdown("💡 **Tips:**")
            st.caption("• Processen: authenticatie, verificatie")
            st.caption("• Types: identiteitsbewijs, document") 
            st.caption("• Resultaten: besluit, rapport")
            st.caption("• Exemplaren: specifiek document, persoon")
        
        # Context sectie (vereenvoudigd)
        st.markdown("#### 📋 Context Selectie")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Organisatorische context (direct multiselect)
            org_context = st.multiselect(
                "🏢 Organisatorische context",
                options=["OM", "ZM", "Reclassering", "DJI", "NP", "Justid", "KMAR", "FIOD", "CJIB", "Strafrechtketen", "Migratieketen"],
                default=SessionStateManager.get_value("quick_org_context", []),
                help="Selecteer één of meerdere organisaties"
            )
            SessionStateManager.set_value("quick_org_context", org_context)
            
        with col2:
            # Juridische context
            jur_context = st.multiselect(
                "⚖️ Juridische context",
                options=["Strafrecht", "Civiel recht", "Bestuursrecht", "Internationaal recht", "Europees recht"],
                default=SessionStateManager.get_value("quick_jur_context", []),
                help="Selecteer juridische gebieden"
            )
            SessionStateManager.set_value("quick_jur_context", jur_context)
            
        with col3:
            # Wettelijke basis
            wet_basis = st.multiselect(
                "📜 Wettelijke basis",
                options=[
                    "Wetboek van Strafvordering (huidige versie)",
                    "Wetboek van strafvordering (nieuwe versie)", 
                    "Wet op de Identificatieplicht",
                    "Wetboek van Strafrecht",
                    "Algemene verordening gegevensbescherming"
                ],
                default=SessionStateManager.get_value("quick_wet_basis", []),
                help="Selecteer relevante wetgeving"
            )
            SessionStateManager.set_value("quick_wet_basis", wet_basis)
        
        # Metadata sectie (inklapbaar)
        with st.expander("📊 Metadata (optioneel)", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                voorsteller = st.text_input(
                    "Voorgesteld door",
                    value=SessionStateManager.get_value("quick_voorsteller", ""),
                    placeholder="Naam van voorsteller"
                )
                SessionStateManager.set_value("quick_voorsteller", voorsteller)
                
            with col2:
                ketenpartners = st.multiselect(
                    "Akkoord ketenpartners",
                    options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"],
                    default=SessionStateManager.get_value("quick_ketenpartners", [])
                )
                SessionStateManager.set_value("quick_ketenpartners", ketenpartners)
                
            with col3:
                include_examples = st.checkbox(
                    "📝 Genereer voorbeelden",
                    value=SessionStateManager.get_value("quick_include_examples", True),
                    help="Voeg praktische voorbeelden toe aan de definitie"
                )
                SessionStateManager.set_value("quick_include_examples", include_examples)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Main generate button
            if st.button("🚀 Genereer Definitie", type="primary", help="Start definitie generatie met opgegeven parameters"):
                if begrip.strip() and org_context:
                    self._handle_quick_generation(begrip, None, org_context, jur_context, wet_basis, voorsteller, include_examples)
                else:
                    if not begrip.strip():
                        st.error("❌ Voer eerst een begrip in")
                    if not org_context:
                        st.error("❌ Selecteer minimaal één organisatorische context")
        
        with col2:
            if st.button("🔍 Check Duplicates", help="Controleer alleen op bestaande definities"):
                if begrip.strip() and org_context:
                    self._handle_quick_duplicate_check(begrip, org_context[0], jur_context[0] if jur_context else "")
                else:
                    st.error("❌ Voer begrip en context in voor duplicate check")
        
        with col3:
            if st.button("🗑️ Wis Velden", help="Maak alle velden leeg"):
                self._clear_quick_form()
                st.rerun()
                
        with col4:
            if st.button("🔧 Meer Opties", help="Ga naar geavanceerde interface"):
                st.info("👇 Scroll naar beneden voor geavanceerde functies")
        
        # Show results if available
        self._render_quick_results()
    
    def _render_header(self):
        """Render applicatie header."""
        
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