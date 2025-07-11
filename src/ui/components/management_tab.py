"""
Management Tab - Interface voor CLI management tools en database beheer.
Integreert definitie_manager.py en setup_database.py functionaliteit in de UI.
"""

import streamlit as st
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from database.definitie_repository import (
    DefinitieRepository, DefinitieStatus, SourceType, get_definitie_repository
)
from generation.definitie_generator import OntologischeCategorie
from integration.definitie_checker import DefinitieChecker, CheckAction
from ui.session_state import SessionStateManager

# Import CLI tools
import sys
sys.path.append(str(Path(__file__).parents[2] / "tools"))

try:
    from definitie_manager import DefinitieManagerCLI
    from setup_database import setup_database, create_test_data, create_sample_export
    CLI_TOOLS_AVAILABLE = True
except ImportError:
    CLI_TOOLS_AVAILABLE = False


class ManagementTab:
    """Tab voor database en system management."""
    
    def __init__(self, repository: DefinitieRepository):
        """Initialiseer management tab."""
        self.repository = repository
        self.checker = DefinitieChecker(repository)
        
        # Initialize CLI manager if available
        if CLI_TOOLS_AVAILABLE:
            self.cli_manager = DefinitieManagerCLI()
        else:
            self.cli_manager = None
    
    def render(self):
        """Render management tab."""
        if not CLI_TOOLS_AVAILABLE:
            st.error("❌ CLI Management tools niet beschikbaar")
            return
        
        st.markdown("### 🛠️ Database & System Management")
        
        # Main interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", "🔍 Database Browser", "⚙️ Database Setup", 
            "📥📤 Import/Export", "🧹 Maintenance"
        ])
        
        with tab1:
            self._render_management_dashboard()
        
        with tab2:
            self._render_database_browser()
        
        with tab3:
            self._render_database_setup()
        
        with tab4:
            self._render_import_export()
        
        with tab5:
            self._render_maintenance()
    
    def _render_management_dashboard(self):
        """Render management dashboard overzicht."""
        st.markdown("#### 📊 System Dashboard")
        
        # Haal statistieken op
        try:
            stats = self.repository.get_statistics()
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📚 Totaal Definities", stats.get('total_definities', 0))
            
            with col2:
                avg_score = stats.get('average_validation_score')
                if avg_score:
                    st.metric("🎯 Gem. Score", f"{avg_score:.2f}")
                else:
                    st.metric("🎯 Gem. Score", "N/A")
            
            with col3:
                pending_count = len(self.checker.get_pending_definitions())
                st.metric("⏳ Pending Reviews", pending_count)
            
            with col4:
                established_count = stats.get('by_status', {}).get('established', 0)
                st.metric("✅ Established", established_count)
            
            # Status distribution
            st.markdown("##### 📈 Status Verdeling")
            if stats.get('by_status'):
                status_data = pd.DataFrame(
                    list(stats['by_status'].items()),
                    columns=['Status', 'Aantal']
                )
                st.bar_chart(status_data.set_index('Status'))
            
            # Category distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📂 Per Categorie")
                if stats.get('by_category'):
                    for category, count in stats['by_category'].items():
                        st.write(f"**{category.title()}**: {count}")
            
            with col2:
                st.markdown("##### 🏢 Per Context")
                # Haal context statistieken op
                contexts = self._get_context_statistics()
                for context, count in contexts.items():
                    st.write(f"**{context}**: {count}")
            
            # Recent activity
            st.markdown("##### 🕒 Recente Activiteit")
            recent_definitions = self.repository.search_definities(limit=5)
            
            if recent_definitions:
                for definitie in recent_definitions:
                    with st.expander(f"📋 {definitie.begrip} - {definitie.status}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Context:** {definitie.organisatorische_context}")
                            st.write(f"**Categorie:** {definitie.categorie}")
                            st.write(f"**Score:** {definitie.validation_score:.2f}" if definitie.validation_score else "**Score:** N/A")
                        with col2:
                            st.write(f"**Aangemaakt:** {definitie.created_at}")
                            st.write(f"**Door:** {definitie.created_by}")
                        st.write(f"**Definitie:** {definitie.definitie[:100]}...")
            
        except Exception as e:
            st.error(f"❌ Fout bij ophalen dashboard data: {str(e)}")
    
    def _render_database_browser(self):
        """Render database browser interface."""
        st.markdown("#### 🔍 Database Browser")
        
        # Search and filter interface
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input(
                "🔍 Zoeken",
                placeholder="Zoek in begrip of definitie...",
                key="mgmt_search_query"
            )
        
        with col2:
            status_filter = st.selectbox(
                "📊 Status Filter",
                ["Alle"] + [s.value for s in DefinitieStatus],
                key="mgmt_status_filter"
            )
        
        with col3:
            category_filter = st.selectbox(
                "📂 Categorie Filter",
                ["Alle"] + [c.value for c in OntologischeCategorie],
                key="mgmt_category_filter"
            )
        
        # Additional filters
        with st.expander("🔧 Geavanceerde Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                context_filter = st.text_input(
                    "🏢 Organisatorische Context",
                    placeholder="bijv. DJI, OM...",
                    key="mgmt_context_filter"
                )
            
            with col2:
                min_score = st.slider(
                    "🎯 Min. Validation Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    key="mgmt_min_score"
                )
            
            with col3:
                max_results = st.number_input(
                    "📊 Max. Resultaten",
                    min_value=1,
                    max_value=100,
                    value=20,
                    key="mgmt_max_results"
                )
        
        # Search button
        if st.button("🔍 Zoeken", key="mgmt_search_btn"):
            self._perform_database_search(
                search_query, status_filter, category_filter,
                context_filter, min_score, max_results
            )
        
        # Display search results
        self._display_search_results()
    
    def _render_database_setup(self):
        """Render database setup interface."""
        st.markdown("#### ⚙️ Database Setup & Configuratie")
        
        # Database info
        st.markdown("##### 📁 Database Informatie")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Database Pad:** {self.repository.db_path}")
            
            # Check database size
            try:
                db_size = Path(self.repository.db_path).stat().st_size / 1024  # KB
                st.info(f"**Database Grootte:** {db_size:.1f} KB")
            except:
                st.warning("Kon database grootte niet bepalen")
        
        with col2:
            # Quick stats
            try:
                stats = self.repository.get_statistics()
                st.metric("📊 Totaal Records", stats.get('total_definities', 0))
            except:
                st.error("Kon statistieken niet ophalen")
        
        # Database operations
        st.markdown("##### 🔧 Database Operaties")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reset Database", key="reset_db_btn"):
                self._reset_database()
        
        with col2:
            if st.button("📥 Laad Test Data", key="load_test_data_btn"):
                self._load_test_data()
        
        with col3:
            if st.button("🧹 Cleanup Database", key="cleanup_db_btn"):
                self._cleanup_database()
        
        # Test data preview
        with st.expander("👀 Preview Test Data", expanded=False):
            test_records = create_test_data()
            
            # Create dataframe for display
            test_df = pd.DataFrame([
                {
                    "Begrip": rec.begrip,
                    "Categorie": rec.categorie,
                    "Context": rec.organisatorische_context,
                    "Status": rec.status,
                    "Score": rec.validation_score,
                    "Definitie": rec.definitie[:50] + "..."
                }
                for rec in test_records
            ])
            
            st.dataframe(test_df, use_container_width=True)
            st.info(f"📊 {len(test_records)} test records beschikbaar")
    
    def _render_import_export(self):
        """Render import/export interface."""
        st.markdown("#### 📥📤 Import & Export Management")
        
        # Export section
        st.markdown("##### 📤 Export Definities")
        
        with st.expander("⚙️ Export Configuratie", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                export_status = st.selectbox(
                    "📊 Status Filter",
                    ["Alle"] + [s.value for s in DefinitieStatus],
                    key="export_status_filter"
                )
                
                export_context = st.text_input(
                    "🏢 Context Filter",
                    placeholder="DJI, OM, etc.",
                    key="export_context_filter"
                )
            
            with col2:
                export_category = st.selectbox(
                    "📂 Categorie Filter",
                    ["Alle"] + [c.value for c in OntologischeCategorie],
                    key="export_category_filter"
                )
                
                export_filename = st.text_input(
                    "📁 Bestandsnaam",
                    value=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    key="export_filename"
                )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export naar File", key="export_to_file_btn"):
                self._export_definitions(export_status, export_context, export_category, export_filename)
        
        with col2:
            if st.button("📄 Preview Export", key="preview_export_btn"):
                self._preview_export(export_status, export_context, export_category)
        
        # Import section
        st.markdown("##### 📥 Import Definities")
        
        uploaded_file = st.file_uploader(
            "Selecteer JSON bestand voor import",
            type=['json'],
            help="Upload een JSON bestand met definities om te importeren",
            key="import_file_uploader"
        )
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                import_by = st.text_input(
                    "👤 Geïmporteerd door",
                    value="ui_user",
                    key="import_by_field"
                )
            
            with col2:
                if st.button("📥 Start Import", key="start_import_btn"):
                    self._import_definitions(uploaded_file, import_by)
        
        # Show recent exports/imports
        self._show_recent_operations()
    
    def _render_maintenance(self):
        """Render maintenance tools interface."""
        st.markdown("#### 🧹 Maintenance & Admin Tools")
        
        # Duplicate detection
        st.markdown("##### 🔍 Duplicate Detection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Scan voor Duplicaten", key="scan_duplicates_btn"):
                self._scan_for_duplicates()
        
        with col2:
            duplicate_threshold = st.slider(
                "🎯 Gelijkenis Drempel",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                key="duplicate_threshold"
            )
        
        # Validation issues
        st.markdown("##### ⚠️ Validation Issues")
        
        if st.button("🔍 Scan Validation Issues", key="scan_validation_btn"):
            self._scan_validation_issues()
        
        # Bulk operations
        st.markdown("##### 📦 Bulk Operaties")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Bulk Approve", key="bulk_approve_btn"):
                self._bulk_approve_interface()
        
        with col2:
            if st.button("📊 Bulk Status Update", key="bulk_status_btn"):
                self._bulk_status_update_interface()
        
        with col3:
            if st.button("🗑️ Bulk Delete", key="bulk_delete_btn"):
                self._bulk_delete_interface()
        
        # System health check
        st.markdown("##### 🏥 System Health Check")
        
        if st.button("🔍 Health Check", key="health_check_btn"):
            self._perform_health_check()
    
    def _get_context_statistics(self) -> Dict[str, int]:
        """Haal context statistieken op."""
        try:
            all_definitions = self.repository.search_definities(limit=1000)
            context_counts = {}
            
            for definitie in all_definitions:
                context = definitie.organisatorische_context or "Onbekend"
                context_counts[context] = context_counts.get(context, 0) + 1
            
            return context_counts
        except:
            return {}
    
    def _perform_database_search(self, query, status, category, context, min_score, max_results):
        """Voer database zoekopdracht uit."""
        try:
            # Convert filters
            status_enum = None if status == "Alle" else DefinitieStatus(status)
            category_enum = None if category == "Alle" else OntologischeCategorie(category)
            context_filter = context if context.strip() else None
            
            # Search definities
            results = self.repository.search_definities(
                query=query if query.strip() else None,
                categorie=category_enum,
                organisatorische_context=context_filter,
                status=status_enum,
                limit=max_results
            )
            
            # Filter on score if needed
            if min_score > 0.0:
                results = [r for r in results if r.validation_score and r.validation_score >= min_score]
            
            # Store results
            SessionStateManager.set_value("mgmt_search_results", results)
            SessionStateManager.set_value("mgmt_search_executed", True)
            
            st.success(f"✅ {len(results)} resultaten gevonden")
            
        except Exception as e:
            st.error(f"❌ Zoeken mislukt: {str(e)}")
    
    def _display_search_results(self):
        """Toon zoekresultaten."""
        if not SessionStateManager.get_value("mgmt_search_executed", False):
            return
        
        results = SessionStateManager.get_value("mgmt_search_results", [])
        
        if not results:
            st.info("📭 Geen resultaten gevonden")
            return
        
        st.markdown(f"##### 📋 Zoekresultaten ({len(results)} items)")
        
        for i, definitie in enumerate(results):
            with st.expander(
                f"📋 {definitie.begrip} (ID: {definitie.id}) - {definitie.status}",
                expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Context:** {definitie.organisatorische_context}")
                    st.write(f"**Categorie:** {definitie.categorie}")
                    st.write(f"**Status:** {definitie.status}")
                
                with col2:
                    st.write(f"**Score:** {definitie.validation_score:.2f}" if definitie.validation_score else "**Score:** N/A")
                    st.write(f"**Bron:** {definitie.source_type}")
                    st.write(f"**Versie:** {definitie.version_number}")
                
                with col3:
                    st.write(f"**Aangemaakt:** {definitie.created_at}")
                    st.write(f"**Door:** {definitie.created_by}")
                    if definitie.approved_by:
                        st.write(f"**Goedgekeurd door:** {definitie.approved_by}")
                
                st.write(f"**Definitie:** {definitie.definitie}")
                
                # Quick actions
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"✏️ Bewerk", key=f"edit_{definitie.id}"):
                        st.info("Bewerk functionaliteit nog niet geïmplementeerd")
                
                with action_col2:
                    if definitie.status != DefinitieStatus.ESTABLISHED.value:
                        if st.button(f"✅ Goedkeuren", key=f"approve_{definitie.id}"):
                            self._approve_definition(definitie.id)
                
                with action_col3:
                    if st.button(f"🗑️ Verwijder", key=f"delete_{definitie.id}"):
                        self._delete_definition(definitie.id)
    
    def _reset_database(self):
        """Reset database (met bevestiging)."""
        if st.session_state.get("confirm_reset_db", False):
            try:
                # Backup current data first
                backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.repository.export_to_json(backup_path, {})
                
                # Reset database
                setup_database(include_test_data=False)
                
                st.success(f"✅ Database gereset! Backup opgeslagen als {backup_path}")
                st.session_state["confirm_reset_db"] = False
                
            except Exception as e:
                st.error(f"❌ Reset mislukt: {str(e)}")
        else:
            st.warning("⚠️ Dit zal alle data wissen! Klik nogmaals om te bevestigen.")
            st.session_state["confirm_reset_db"] = True
    
    def _load_test_data(self):
        """Laad test data in database."""
        try:
            test_records = create_test_data()
            added_count = 0
            
            for record in test_records:
                # Check of al bestaat
                existing = self.repository.find_definitie(
                    record.begrip,
                    record.organisatorische_context,
                    record.juridische_context or ""
                )
                
                if not existing:
                    self.repository.create_definitie(record)
                    added_count += 1
            
            st.success(f"✅ {added_count} test records toegevoegd!")
            
        except Exception as e:
            st.error(f"❌ Test data laden mislukt: {str(e)}")
    
    def _cleanup_database(self):
        """Cleanup database (verwijder oude/ongeldige records)."""
        try:
            # Implementeer cleanup logica
            st.info("🧹 Database cleanup nog niet volledig geïmplementeerd")
            
            # Voorbeelden van cleanup:
            # - Verwijder definitie zonder tekst
            # - Merge duplicaten
            # - Update deprecated fields
            
        except Exception as e:
            st.error(f"❌ Cleanup mislukt: {str(e)}")
    
    def _export_definitions(self, status, context, category, filename):
        """Export definities naar bestand."""
        try:
            filters = {}
            
            if status != "Alle":
                filters['status'] = DefinitieStatus(status)
            if context.strip():
                filters['organisatorische_context'] = context.strip()
            if category != "Alle":
                filters['categorie'] = OntologischeCategorie(category)
            
            # Export path
            export_path = Path(__file__).parents[3] / "exports" / "definitions" / filename
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            count = self.repository.export_to_json(str(export_path), filters)
            
            st.success(f"✅ {count} definities geëxporteerd naar {filename}")
            
            # Download button
            with open(export_path, 'rb') as f:
                st.download_button(
                    label="📥 Download Export",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"❌ Export mislukt: {str(e)}")
    
    def _preview_export(self, status, context, category):
        """Preview export data."""
        try:
            # Same filtering logic as export
            status_enum = None if status == "Alle" else DefinitieStatus(status)
            category_enum = None if category == "Alle" else OntologischeCategorie(category)
            context_filter = context if context.strip() else None
            
            results = self.repository.search_definities(
                categorie=category_enum,
                organisatorische_context=context_filter,
                status=status_enum,
                limit=100  # Preview limit
            )
            
            st.info(f"📊 Preview: {len(results)} definities zouden worden geëxporteerd")
            
            if results:
                # Show first few as preview
                preview_df = pd.DataFrame([
                    {
                        "Begrip": r.begrip,
                        "Context": r.organisatorische_context,
                        "Categorie": r.categorie,
                        "Status": r.status,
                        "Score": r.validation_score
                    }
                    for r in results[:10]
                ])
                
                st.dataframe(preview_df, use_container_width=True)
                
                if len(results) > 10:
                    st.caption(f"... en {len(results) - 10} meer records")
            
        except Exception as e:
            st.error(f"❌ Preview mislukt: {str(e)}")
    
    def _import_definitions(self, uploaded_file, import_by):
        """Import definities uit bestand."""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Import using repository
            successful, failed, errors = self.repository.import_from_json(tmp_path, import_by)
            
            # Cleanup temp file
            Path(tmp_path).unlink()
            
            # Show results
            st.success(f"✅ Import voltooid: {successful} succesvol, {failed} mislukt")
            
            if errors:
                with st.expander("⚠️ Import Fouten", expanded=False):
                    for error in errors[:10]:
                        st.write(f"• {error}")
                    if len(errors) > 10:
                        st.write(f"... en {len(errors) - 10} meer fouten")
            
        except Exception as e:
            st.error(f"❌ Import mislukt: {str(e)}")
    
    def _show_recent_operations(self):
        """Toon recente import/export operaties."""
        st.markdown("##### 📜 Recente Operaties")
        
        # Dit zou ideaal uit een log tabel komen
        st.info("📋 Operatie geschiedenis nog niet geïmplementeerd")
    
    def _scan_for_duplicates(self):
        """Scan voor duplicate definities."""
        try:
            st.info("🔍 Scanning for duplicates...")
            
            # Implementeer duplicate scanning
            # Dit zou de web_lookup duplicate detection kunnen gebruiken
            
            st.info("🔧 Duplicate scanning nog niet volledig geïmplementeerd")
            
        except Exception as e:
            st.error(f"❌ Duplicate scan mislukt: {str(e)}")
    
    def _scan_validation_issues(self):
        """Scan voor validation issues."""
        try:
            # Haal alle definities op en valideer
            all_definitions = self.repository.search_definities(limit=1000)
            issues_found = []
            
            for definitie in all_definitions:
                if definitie.validation_score and definitie.validation_score < 0.7:
                    issues_found.append(definitie)
            
            st.info(f"⚠️ {len(issues_found)} definities met validation issues gevonden")
            
            if issues_found:
                for definitie in issues_found[:5]:
                    st.warning(f"• {definitie.begrip} (Score: {definitie.validation_score:.2f})")
            
        except Exception as e:
            st.error(f"❌ Validation scan mislukt: {str(e)}")
    
    def _bulk_approve_interface(self):
        """Interface voor bulk approve."""
        st.info("✅ Bulk approve interface nog niet geïmplementeerd")
    
    def _bulk_status_update_interface(self):
        """Interface voor bulk status update."""
        st.info("📊 Bulk status update interface nog niet geïmplementeerd")
    
    def _bulk_delete_interface(self):
        """Interface voor bulk delete."""
        st.info("🗑️ Bulk delete interface nog niet geïmplementeerd")
    
    def _perform_health_check(self):
        """Voer system health check uit."""
        try:
            st.info("🏥 Performing health check...")
            
            # Database connectivity
            stats = self.repository.get_statistics()
            st.success("✅ Database connectivity: OK")
            
            # Repository functionality
            test_definitions = self.repository.search_definities(limit=1)
            st.success("✅ Repository queries: OK")
            
            # CLI tools availability
            if CLI_TOOLS_AVAILABLE:
                st.success("✅ CLI tools: Available")
            else:
                st.warning("⚠️ CLI tools: Not available")
            
            # Validation system
            try:
                from validation.definitie_validator import DefinitieValidator
                validator = DefinitieValidator()
                st.success("✅ Validation system: OK")
            except Exception as e:
                st.error(f"❌ Validation system: {str(e)}")
            
            st.success("🎯 Health check completed!")
            
        except Exception as e:
            st.error(f"❌ Health check failed: {str(e)}")
    
    def _approve_definition(self, definitie_id: int):
        """Keur definitie goed."""
        try:
            success = self.checker.approve_definition(
                definitie_id=definitie_id,
                approved_by="ui_admin",
                notes="Goedgekeurd via management interface"
            )
            
            if success:
                st.success(f"✅ Definitie {definitie_id} goedgekeurd!")
                st.rerun()
            else:
                st.error(f"❌ Kon definitie {definitie_id} niet goedkeuren")
                
        except Exception as e:
            st.error(f"❌ Goedkeuring mislukt: {str(e)}")
    
    def _delete_definition(self, definitie_id: int):
        """Verwijder definitie (met bevestiging)."""
        confirm_key = f"confirm_delete_{definitie_id}"
        
        if st.session_state.get(confirm_key, False):
            try:
                # Implementeer delete functionaliteit
                st.warning("🗑️ Delete functionaliteit nog niet geïmplementeerd")
                st.session_state[confirm_key] = False
                
            except Exception as e:
                st.error(f"❌ Verwijderen mislukt: {str(e)}")
        else:
            st.warning("⚠️ Definitie verwijderen? Klik nogmaals om te bevestigen.")
            st.session_state[confirm_key] = True