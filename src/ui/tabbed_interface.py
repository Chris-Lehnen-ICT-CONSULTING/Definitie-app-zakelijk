"""
Tabbed Interface voor DefinitieAgent - Nieuwe UI architectuur.
Implementeert de requirements uit Project Requirements Document.

Deze module bevat de hoofdcontroller voor de gebruikersinterface,
met ondersteuning voor meerdere tabs en complete workflow beheer.
"""

import streamlit as st  # Streamlit web interface framework
from typing import Dict, Any, Optional, List  # Type hints voor betere code documentatie
from datetime import datetime  # Datum en tijd functionaliteit

# Importeer alle UI tab componenten voor de verschillende functionaliteiten
from ui.components.context_selector import ContextSelector  # Context selectie component
from ui.components.definition_generator_tab import DefinitionGeneratorTab  # Hoofdtab voor definitie generatie
from ui.components.expert_review_tab import ExpertReviewTab  # Expert review en validatie tab
from ui.components.history_tab import HistoryTab  # Historie overzicht tab
from ui.components.export_tab import ExportTab  # Export functionaliteit tab
from ui.components.quality_control_tab import QualityControlTab  # Kwaliteitscontrole dashboard
from ui.components.external_sources_tab import ExternalSourcesTab  # Externe bronnen beheer
from ui.components.monitoring_tab import MonitoringTab  # Monitoring en statistieken
from ui.components.web_lookup_tab import WebLookupTab  # Web lookup interface
from ui.components.orchestration_tab import OrchestrationTab  # Orchestratie en automatisering
from ui.components.management_tab import ManagementTab  # Systeem management tools
# Importeer core services en utilities
from ui.session_state import SessionStateManager  # Sessie state management voor UI persistentie
from database.definitie_repository import get_definitie_repository  # Database toegang factory
from integration.definitie_checker import DefinitieChecker  # Definitie integratie controle
from generation.definitie_generator import OntologischeCategorie  # Ontologische categorieën
from document_processing.document_processor import get_document_processor  # Document processor factory
from document_processing.document_extractor import supported_file_types  # Ondersteunde bestandstypen
# Hybrid context imports - optionele module voor hybride context verrijking
try:
    from hybrid_context.hybrid_context_engine import get_hybrid_context_engine  # Hybride context engine factory
    HYBRID_CONTEXT_AVAILABLE = True  # Hybride context succesvol geladen
except ImportError:
    HYBRID_CONTEXT_AVAILABLE = False  # Hybride context niet beschikbaar
import logging  # Logging faciliteiten voor debug en monitoring

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class TabbedInterface:
    """Main tabbed interface controller voor DefinitieAgent."""
    
    def __init__(self):
        """Initialiseer tabbed interface met alle benodigde services."""
        self.repository = get_definitie_repository()  # Haal database repository instantie op
        self.checker = DefinitieChecker(self.repository)  # Maak definitie checker instantie
        self.context_selector = ContextSelector()  # Initialiseer context selector component
        
        # Initialiseer alle tab componenten met repository referentie
        self.definition_tab = DefinitionGeneratorTab(self.checker)
        self.expert_tab = ExpertReviewTab(self.repository)
        self.history_tab = HistoryTab(self.repository)
        self.export_tab = ExportTab(self.repository)
        self.quality_tab = QualityControlTab(self.repository)
        self.external_tab = ExternalSourcesTab(self.repository)
        self.monitoring_tab = MonitoringTab(self.repository)
        self.web_lookup_tab = WebLookupTab(self.repository)
        self.orchestration_tab = OrchestrationTab(self.repository)
        self.management_tab = ManagementTab(self.repository)
        
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
            },
            "quality": {
                "title": "🔧 Kwaliteitscontrole",
                "icon": "🔧",
                "description": "Toetsregels analyse en system health"
            },
            "external": {
                "title": "🔌 Externe Bronnen",
                "icon": "🔌",
                "description": "Import van externe definitie bronnen"
            },
            "monitoring": {
                "title": "📈 Monitoring",
                "icon": "📈",
                "description": "Performance monitoring en API cost tracking"
            },
            "web_lookup": {
                "title": "🔍 Web Lookup",
                "icon": "🔍",
                "description": "Zoek definities en bronnen, valideer duplicaten"
            },
            "orchestration": {
                "title": "🤖 Orchestratie",
                "icon": "🤖",
                "description": "Intelligente definitie orchestratie en iteratieve verbetering"
            },
            "management": {
                "title": "🛠️ Management",
                "icon": "🛠️",
                "description": "Database beheer, import/export en system administratie"
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
        # Begrip invoer als eerste
        st.markdown("### 📝 Definitie Aanvraag")
        begrip = st.text_input(
            "Voer een term in waarvoor een definitie moet worden gegenereerd",
            value=SessionStateManager.get_value("begrip", ""),
            placeholder="bijv. authenticatie, verificatie, identiteitsvaststelling...",
            help="Het centrale begrip waarvoor een definitie gegenereerd wordt"
        )
        SessionStateManager.set_value("begrip", begrip)
        
        st.markdown("### 🎯 Context Configuratie")
        
        # Document upload sectie
        self._render_document_upload_section()
        
        # Context selector zonder presets - direct handmatige selectie
        context_data = self._render_simplified_context_selector()
        
        # Store in session state voor gebruik in tabs
        SessionStateManager.set_value("global_context", context_data)
        
        # Show selected context summary
        if any(context_data.values()):
            self._render_context_summary(context_data)
        
        # Genereer definitie knop direct na context
        st.markdown("---")
        self._render_quick_generate_button(begrip, context_data)
    
    def _render_simplified_context_selector(self) -> Dict[str, Any]:
        """Render vereenvoudigde context selector zonder presets."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Organisatorische context
            org_options = [
                "OM", "ZM", "Reclassering", "DJI", "NP", "Justid",
                "KMAR", "FIOD", "CJIB", "Strafrechtketen", "Migratieketen",
                "Justitie en Veiligheid", "Anders..."
            ]
            
            selected_org = st.multiselect(
                "📋 Organisatorische context",
                options=org_options,
                default=SessionStateManager.get_value("org_context", []),
                help="Selecteer één of meerdere organisaties"
            )
            
            # Custom org context
            custom_org = ""
            if "Anders..." in selected_org:
                custom_org = st.text_input(
                    "Aangepaste organisatorische context",
                    placeholder="Voer andere organisatie in...",
                    key="custom_org_global"
                )
            
            # Combineer contexts
            final_org = [opt for opt in selected_org if opt != "Anders..."]
            if custom_org.strip():
                final_org.append(custom_org.strip())
            
            SessionStateManager.set_value("org_context", final_org)
            
        with col2:
            # Juridische context
            jur_options = [
                "Strafrecht", "Civiel recht", "Bestuursrecht", 
                "Internationaal recht", "Europees recht", "Migratierecht",
                "Anders..."
            ]
            
            selected_jur = st.multiselect(
                "⚖️ Juridische context",
                options=jur_options,
                default=SessionStateManager.get_value("jur_context", []),
                help="Selecteer juridische gebieden"
            )
            
            # Custom juridical context
            custom_jur = ""
            if "Anders..." in selected_jur:
                custom_jur = st.text_input(
                    "Aangepaste juridische context",
                    placeholder="Voer ander rechtsgebied in...",
                    key="custom_jur_global"
                )
            
            # Combineer juridische context
            final_jur = [opt for opt in selected_jur if opt != "Anders..."]
            if custom_jur.strip():
                final_jur.append(custom_jur.strip())
            
            SessionStateManager.set_value("jur_context", final_jur)
            
        with col3:
            # Wettelijke basis
            wet_options = [
                "Wetboek van Strafvordering (huidige versie)",
                "Wetboek van strafvordering (nieuwe versie)",
                "Wet op de Identificatieplicht",
                "Wet op de politiegegevens",
                "Wetboek van Strafrecht",
                "Algemene verordening gegevensbescherming",
                "Anders..."
            ]
            
            selected_wet = st.multiselect(
                "📜 Wettelijke basis",
                options=wet_options,
                default=SessionStateManager.get_value("wet_basis", []),
                help="Selecteer relevante wetgeving"
            )
            
            # Custom legal basis
            custom_wet = ""
            if "Anders..." in selected_wet:
                custom_wet = st.text_input(
                    "Aangepaste wettelijke basis",
                    placeholder="Voer andere wetgeving in...",
                    key="custom_wet_global"
                )
            
            # Combineer wettelijke basis
            final_wet = [opt for opt in selected_wet if opt != "Anders..."]
            if custom_wet.strip():
                final_wet.append(custom_wet.strip())
            
            SessionStateManager.set_value("wet_basis", final_wet)
        
        return {
            "organisatorische_context": final_org,
            "juridische_context": final_jur,
            "wettelijke_basis": final_wet
        }
    
    def _render_quick_generate_button(self, begrip: str, context_data: Dict[str, Any]):
        """Render snelle genereer definitie knop."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🚀 Genereer Definitie", type="primary", help="Start definitie generatie", key="main_generate_btn"):
                if begrip.strip():
                    self._handle_definition_generation(begrip, context_data)
                else:
                    st.error("❌ Voer eerst een begrip in")
        
        with col2:
            if st.button("🔍 Check Duplicates", help="Controleer op bestaande definities", key="main_check_btn"):
                if begrip.strip():
                    self._handle_duplicate_check(begrip, context_data)
                else:
                    st.error("❌ Voer eerst een begrip in")
        
        with col3:
            if st.button("🗑️ Wis Velden", help="Maak alle velden leeg", key="main_clear_btn"):
                self._clear_all_fields()
                st.rerun()
    
    def _handle_definition_generation(self, begrip: str, context_data: Dict[str, Any]):
        """Handle definitie generatie vanaf hoofdniveau met hybrid context ondersteuning."""
        try:
            with st.spinner("🔄 Genereren van definitie met hybride context..."):
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                
                # Bepaal automatisch de ontologische categorie
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""
                auto_categorie = self._determine_ontological_category(begrip, primary_org, primary_jur)
                
                # Krijg document context en selected document IDs
                document_context = self._get_document_context()
                selected_doc_ids = SessionStateManager.get_value("selected_documents", [])
                
                # Check of hybrid context gebruikt moet worden
                use_hybrid = (HYBRID_CONTEXT_AVAILABLE and 
                             (len(selected_doc_ids) > 0 or (document_context and document_context.get('document_count', 0) > 0)))
                
                if use_hybrid:
                    st.info("🔄 Hybrid context activief - combineer document en web context...")
                
                # Voer complete workflow uit met mogelijke hybrid enhancement
                check_result, agent_result, saved_record = self.checker.generate_with_check(
                    begrip=begrip,
                    organisatorische_context=primary_org,
                    juridische_context=primary_jur,
                    categorie=auto_categorie,
                    force_generate=False,
                    created_by="global_user",
                    # Hybride context parameters
                    selected_document_ids=selected_doc_ids if use_hybrid else None,
                    enable_hybrid=use_hybrid
                )
                
                # Store results voor display in tabs
                SessionStateManager.set_value("last_generation_result", {
                    "check_result": check_result,
                    "agent_result": agent_result,
                    "saved_record": saved_record,
                    "determined_category": auto_categorie.value,
                    "document_context": document_context,
                    "timestamp": datetime.now()
                })
                
                # Store detailed validation results for display
                if agent_result and agent_result.best_iteration:
                    from ai_toetser.modular_toetser import toets_definitie
                    from config.toetsregel_manager import get_toetsregel_manager
                    
                    # Get detailed validation results
                    toetsregel_manager = get_toetsregel_manager()
                    toetsregels = toetsregel_manager.get_all_rules()
                    
                    detailed_results = toets_definitie(
                        definitie=agent_result.final_definitie,
                        toetsregels=toetsregels,
                        begrip=begrip,
                        gebruik_logging=True
                    )
                    
                    SessionStateManager.set_value("beoordeling_gen", detailed_results)
                
                # Toon document context info als gebruikt
                if document_context and document_context.get('document_count', 0) > 0:
                    st.success(f"✅ Definitie gegenereerd met context van {document_context['document_count']} document(en)! Bekijk resultaten in de 'Definitie Generatie' tab.")
                else:
                    st.success("✅ Definitie succesvol gegenereerd! Bekijk resultaten in de 'Definitie Generatie' tab.")
                
        except Exception as e:
            st.error(f"❌ Fout bij generatie: {str(e)}")
            logger.error(f"Global generation failed: {e}")
    
    def _get_document_context(self) -> Optional[Dict[str, Any]]:
        """Krijg document context voor definitie generatie."""
        try:
            selected_docs = SessionStateManager.get_value("selected_documents", [])
            if not selected_docs:
                return None
            
            processor = get_document_processor()
            aggregated_context = processor.get_aggregated_context(selected_docs)
            
            if aggregated_context['document_count'] == 0:
                return None
            
            return aggregated_context
            
        except Exception as e:
            logger.error(f"Fout bij ophalen document context: {e}")
            return None
    
    def _handle_duplicate_check(self, begrip: str, context_data: Dict[str, Any]):
        """Handle duplicate check vanaf hoofdniveau."""
        try:
            with st.spinner("🔍 Controleren op duplicates..."):
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""
                
                check_result = self.checker.check_before_generation(
                    begrip=begrip,
                    organisatorische_context=primary_org,
                    juridische_context=primary_jur,
                    categorie=OntologischeCategorie.PROCES  # Default
                )
                
                SessionStateManager.set_value("last_check_result", check_result)
                st.success("✅ Duplicate check voltooid! Bekijk resultaten in de 'Definitie Generatie' tab.")
                
        except Exception as e:
            st.error(f"❌ Fout bij duplicate check: {str(e)}")
            logger.error(f"Global duplicate check failed: {e}")
    
    def _clear_all_fields(self):
        """Wis alle velden."""
        fields_to_clear = [
            "begrip", "org_context", "jur_context", "wet_basis",
            "last_generation_result", "last_check_result"
        ]
        
        for field in fields_to_clear:
            SessionStateManager.clear_value(field)
    
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
    
    def _render_document_upload_section(self):
        """Render document upload sectie voor context enrichment."""
        with st.expander("📄 Document Upload voor Context Verrijking", expanded=False):
            st.markdown("Upload documenten die relevante context bevatten voor de definitie generatie.")
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Selecteer documenten",
                type=['txt', 'pdf', 'docx', 'doc', 'md', 'csv', 'json', 'html', 'rtf'],
                accept_multiple_files=True,
                help="Ondersteunde formaten: TXT, PDF, Word, Markdown, CSV, JSON, HTML, RTF"
            )
            
            # Toon ondersteunde bestandstypen in sidebar of als tekst
            if st.checkbox("ℹ️ Toon ondersteunde bestandstypen", value=False):
                supported_types = supported_file_types()
                st.markdown("**Ondersteunde bestandstypen:**")
                for mime_type, description in supported_types.items():
                    st.write(f"• {description}")
            
            # Process uploaded files
            if uploaded_files:
                self._process_uploaded_files(uploaded_files)
            
            # Toon bestaande documenten
            self._render_uploaded_documents_list()
    
    def _process_uploaded_files(self, uploaded_files):
        """Verwerk geüploade bestanden."""
        processor = get_document_processor()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_docs = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Verwerken van {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Lees bestandsinhoud
                file_content = uploaded_file.read()
                
                # Verwerk document
                processed_doc = processor.process_uploaded_file(
                    file_content, 
                    uploaded_file.name, 
                    uploaded_file.type
                )
                
                processed_docs.append(processed_doc)
                
            except Exception as e:
                st.error(f"Fout bij verwerken van {uploaded_file.name}: {str(e)}")
        
        progress_bar.empty()
        status_text.empty()
        
        # Toon resultaten
        if processed_docs:
            st.success(f"✅ {len(processed_docs)} document(en) verwerkt!")
            
            for doc in processed_docs:
                if doc.processing_status == "success":
                    st.success(f"✅ {doc.filename}: {doc.text_length} karakters geëxtraheerd")
                else:
                    st.error(f"❌ {doc.filename}: {doc.error_message}")
            
            # Update session state
            SessionStateManager.set_value("documents_updated", True)
    
    def _render_uploaded_documents_list(self):
        """Render lijst van geüploade documenten."""
        processor = get_document_processor()
        documents = processor.get_processed_documents()
        
        if not documents:
            st.info("Geen documenten geüpload")
            return
        
        st.markdown("#### 📚 Geüploade Documenten")
        
        # Document selectie voor context enrichment
        doc_options = []
        doc_labels = []
        
        for doc in documents:
            if doc.processing_status == "success":
                label = f"{doc.filename} ({doc.text_length:,} chars, {len(doc.keywords)} keywords)"
                doc_options.append(doc.id)
                doc_labels.append(label)
        
        if doc_options:
            selected_docs = st.multiselect(
                "Selecteer documenten voor context verrijking",
                options=doc_options,
                format_func=lambda x: next(label for doc_id, label in zip(doc_options, doc_labels) if doc_id == x),
                default=SessionStateManager.get_value("selected_documents", []),
                help="Geselecteerde documenten worden gebruikt voor context en bronvermelding"
            )
            
            SessionStateManager.set_value("selected_documents", selected_docs)
            
            # Toon document details
            if selected_docs:
                st.markdown(f"#### 📋 Details van {len(selected_docs)} geselecteerde document(en)")
                aggregated = processor.get_aggregated_context(selected_docs)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Documenten", aggregated['document_count'])
                    st.metric("Totale tekst", f"{aggregated['total_text_length']:,} chars")
                    
                with col2:
                    st.metric("Keywords", len(aggregated['aggregated_keywords']))
                    st.metric("Concepten", len(aggregated['aggregated_concepts']))
                
                # Toon keywords en concepten
                if aggregated['aggregated_keywords']:
                    st.markdown("**Top Keywords:**")
                    st.write(", ".join(aggregated['aggregated_keywords'][:10]))
                
                if aggregated['aggregated_concepts']:
                    st.markdown("**Key Concepten:**")
                    st.write(", ".join(aggregated['aggregated_concepts'][:5]))
                
                if aggregated['aggregated_legal_refs']:
                    st.markdown("**Juridische Verwijzingen:**")
                    st.write(", ".join(aggregated['aggregated_legal_refs'][:5]))
        
        # Document management - buiten expander om nesting te voorkomen
        if documents and st.checkbox("🗂️ Toon document beheer", value=False):
            st.markdown("#### 🗂️ Document Beheer")
            for doc in documents:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    status_emoji = "✅" if doc.processing_status == "success" else "❌"
                    st.write(f"{status_emoji} {doc.filename}")
                    if doc.processing_status == "success":
                        st.caption(f"{doc.text_length:,} chars, {len(doc.keywords)} keywords")
                    else:
                        st.caption(f"Error: {doc.error_message}")
                
                with col2:
                    upload_date = doc.uploaded_at.strftime("%d-%m %H:%M")
                    st.caption(upload_date)
                
                with col3:
                    if st.button("🗑️", key=f"delete_{doc.id}", help=f"Verwijder {doc.filename}"):
                        processor.remove_document(doc.id)
                        st.rerun()
    
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
        elif tab_key == "quality":
            self.quality_tab.render()
        elif tab_key == "external":
            self.external_tab.render()
        elif tab_key == "monitoring":
            self.monitoring_tab.render()
        elif tab_key == "web_lookup":
            self.web_lookup_tab.render()
        elif tab_key == "orchestration":
            self.orchestration_tab.render()
        elif tab_key == "management":
            self.management_tab.render()
    
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