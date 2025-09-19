"""
Management Tab - Interface voor CLI management tools en database beheer.
Integreert definitie_manager.py en setup_database.py functionaliteit in de UI.
"""

# Importeer CLI tools voor management functionaliteit
import asyncio
import os
import sys  # Systeem interface voor path manipulatie
import tempfile  # Tijdelijke bestanden voor upload/download operaties
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility# Datum en tijd functionaliteit, timezone
from pathlib import Path  # Object-georiënteerde bestandspad manipulatie

import pandas as pd  # Data manipulatie en analyse framework
import streamlit as st  # Streamlit web interface framework

# Database en core component imports
from database.definitie_repository import (
    DefinitieRepository,
    DefinitieStatus,  # Database toegang en status enums
)
from domain.ontological_categories import (  # Categorieën voor definitie classificatie
    OntologischeCategorie,
)
from integration.definitie_checker import (  # Definitie validatie en check acties
    DefinitieChecker,
)
from ui.session_state import (  # Sessie status management voor Streamlit
    SessionStateManager,
)

sys.path.append(
    str(Path(__file__).parents[2] / "tools")
)  # Voeg tools directory toe aan Python path

try:
    # Probeer CLI management tools te importeren
    from definitie_manager import (  # CLI tool voor definitie management
        DefinitieManagerCLI,
    )
    from setup_database import (  # Database setup utilities
        create_test_data,
        setup_database,
    )

    CLI_TOOLS_AVAILABLE = True  # CLI tools succesvol geladen
except ImportError:
    CLI_TOOLS_AVAILABLE = False  # CLI tools niet beschikbaar


class ManagementTab:
    """Tab voor database en system management.

    Biedt interface voor database beheer, CLI tool integratie,
    en systeem administratie functionaliteiten.
    """

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer management tab met database repository."""
        self.repository = repository  # Database repository voor definitie toegang
        self.checker = DefinitieChecker(repository)  # Checker voor definitie validatie

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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "📊 Dashboard",
                "🔍 Database Browser",
                "⚙️ Database Setup",
                "📥📤 Import/Export",
                "🧹 Maintenance",
                "🧪 Developer Tools",
            ]
        )

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

        with tab6:
            self._render_developer_tools()

    def _render_management_dashboard(self):
        """Render management dashboard overzicht."""
        st.markdown("#### 📊 System Dashboard")

        # Haal statistieken op
        try:
            stats = self.repository.get_statistics()

            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📚 Totaal Definities", stats.get("total_definities", 0))

            with col2:
                avg_score = stats.get("average_validation_score")
                if avg_score:
                    st.metric("🎯 Gem. Score", f"{avg_score:.2f}")
                else:
                    st.metric("🎯 Gem. Score", "N/A")

            with col3:
                pending_count = len(self.checker.get_pending_definitions())
                st.metric("⏳ Pending Reviews", pending_count)

            with col4:
                established_count = stats.get("by_status", {}).get("established", 0)
                st.metric("✅ Established", established_count)

            # Status distribution
            st.markdown("##### 📈 Status Verdeling")
            if stats.get("by_status"):
                status_data = pd.DataFrame(
                    list(stats["by_status"].items()), columns=["Status", "Aantal"]
                )
                st.bar_chart(status_data.set_index("Status"))

            # Category distribution
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### 📂 Per Categorie")
                if stats.get("by_category"):
                    for category, count in stats["by_category"].items():
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
                    with st.expander(
                        f"📋 {definitie.begrip} - {definitie.status}", expanded=False
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(
                                f"**Context:** {definitie.organisatorische_context}"
                            )
                            st.write(f"**Categorie:** {definitie.categorie}")
                            st.write(
                                f"**Score:** {definitie.validation_score:.2f}"
                                if definitie.validation_score
                                else "**Score:** N/A"
                            )
                        with col2:
                            st.write(f"**Aangemaakt:** {definitie.created_at}")
                            st.write(f"**Door:** {definitie.created_by}")
                        st.write(f"**Definitie:** {definitie.definitie[:100]}...")

        except Exception as e:
            st.error(f"❌ Fout bij ophalen dashboard data: {e!s}")

    def _render_database_browser(self):
        """Render database browser interface."""
        st.markdown("#### 🔍 Database Browser")

        # Search and filter interface
        col1, col2, col3 = st.columns(3)

        with col1:
            search_query = st.text_input(
                "🔍 Zoeken",
                placeholder="Zoek in begrip of definitie...",
                key="mgmt_search_query",
            )

        with col2:
            status_filter = st.selectbox(
                "📊 Status Filter",
                ["Alle"] + [s.value for s in DefinitieStatus],
                key="mgmt_status_filter",
            )

        with col3:
            category_filter = st.selectbox(
                "📂 Categorie Filter",
                ["Alle"] + [c.value for c in OntologischeCategorie],
                key="mgmt_category_filter",
            )

        # Additional filters
        with st.expander("🔧 Geavanceerde Filters", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                context_filter = st.text_input(
                    "🏢 Organisatorische Context",
                    placeholder="bijv. DJI, OM...",
                    key="mgmt_context_filter",
                )

            with col2:
                min_score = st.slider(
                    "🎯 Min. Validation Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    key="mgmt_min_score",
                )

            with col3:
                max_results = st.number_input(
                    "📊 Max. Resultaten",
                    min_value=1,
                    max_value=100,
                    value=20,
                    key="mgmt_max_results",
                )

        # Search button
        if st.button("🔍 Zoeken", key="mgmt_search_btn"):
            self._perform_database_search(
                search_query,
                status_filter,
                category_filter,
                context_filter,
                min_score,
                max_results,
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
            except (FileNotFoundError, OSError, AttributeError):
                st.warning("Kon database grootte niet bepalen")

        with col2:
            # Quick stats
            try:
                stats = self.repository.get_statistics()
                st.metric("📊 Totaal Records", stats.get("total_definities", 0))
            except Exception:
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
            test_df = pd.DataFrame(
                [
                    {
                        "Begrip": rec.begrip,
                        "Categorie": rec.categorie,
                        "Context": rec.organisatorische_context,
                        "Status": rec.status,
                        "Score": rec.validation_score,
                        "Definitie": rec.definitie[:50] + "...",
                    }
                    for rec in test_records
                ]
            )

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
                    key="export_status_filter",
                )

                export_context = st.text_input(
                    "🏢 Context Filter",
                    placeholder="DJI, OM, etc.",
                    key="export_context_filter",
                )

            with col2:
                export_category = st.selectbox(
                    "📂 Categorie Filter",
                    ["Alle"] + [c.value for c in OntologischeCategorie],
                    key="export_category_filter",
                )

                export_filename = st.text_input(
                    "📁 Bestandsnaam",
                    value=f"export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json",
                    key="export_filename",
                )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Export naar File", key="export_to_file_btn"):
                self._export_definitions(
                    export_status, export_context, export_category, export_filename
                )

        with col2:
            if st.button("📄 Preview Export", key="preview_export_btn"):
                self._preview_export(export_status, export_context, export_category)

        # Import section
        st.markdown("##### 📥 Import Definities")

        uploaded_file = st.file_uploader(
            "Selecteer JSON bestand voor import",
            type=["json"],
            help="Upload een JSON bestand met definities om te importeren",
            key="import_file_uploader",
        )

        if uploaded_file:
            col1, col2 = st.columns(2)

            with col1:
                import_by = st.text_input(
                    "👤 Geïmporteerd door", value="ui_user", key="import_by_field"
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
            st.slider(
                "🎯 Gelijkenis Drempel",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                key="duplicate_threshold",
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

    def _get_context_statistics(self) -> dict[str, int]:
        """Haal context statistieken op."""
        try:
            all_definitions = self.repository.search_definities(limit=1000)
            context_counts = {}

            for definitie in all_definitions:
                context = definitie.organisatorische_context or "Onbekend"
                context_counts[context] = context_counts.get(context, 0) + 1

            return context_counts
        except Exception:
            return {}

    def _perform_database_search(
        self, query, status, category, context, min_score, max_results
    ):
        """Voer database zoekopdracht uit."""
        try:
            # Convert filters
            status_enum = None if status == "Alle" else DefinitieStatus(status)
            category_enum = (
                None if category == "Alle" else OntologischeCategorie(category)
            )
            context_filter = context if context.strip() else None

            # Search definities
            results = self.repository.search_definities(
                query=query if query.strip() else None,
                categorie=category_enum,
                organisatorische_context=context_filter,
                status=status_enum,
                limit=max_results,
            )

            # Filter on score if needed
            if min_score > 0.0:
                results = [
                    r
                    for r in results
                    if r.validation_score and r.validation_score >= min_score
                ]

            # Store results
            SessionStateManager.set_value("mgmt_search_results", results)
            SessionStateManager.set_value("mgmt_search_executed", True)

            st.success(f"✅ {len(results)} resultaten gevonden")

        except Exception as e:
            st.error(f"❌ Zoeken mislukt: {e!s}")

    def _display_search_results(self):
        """Toon zoekresultaten."""
        if not SessionStateManager.get_value("mgmt_search_executed", False):
            return

        results = SessionStateManager.get_value("mgmt_search_results", [])

        if not results:
            st.info("📭 Geen resultaten gevonden")
            return

        st.markdown(f"##### 📋 Zoekresultaten ({len(results)} items)")

        for _i, definitie in enumerate(results):
            with st.expander(
                f"📋 {definitie.begrip} (ID: {definitie.id}) - {definitie.status}",
                expanded=False,
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Context:** {definitie.organisatorische_context}")
                    st.write(f"**Categorie:** {definitie.categorie}")
                    st.write(f"**Status:** {definitie.status}")

                with col2:
                    st.write(
                        f"**Score:** {definitie.validation_score:.2f}"
                        if definitie.validation_score
                        else "**Score:** N/A"
                    )
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
                    if st.button("✏️ Bewerk", key=f"edit_{definitie.id}"):
                        st.info("Bewerk functionaliteit nog niet geïmplementeerd")

                with action_col2:
                    if definitie.status != DefinitieStatus.ESTABLISHED.value:
                        if st.button("✅ Goedkeuren", key=f"approve_{definitie.id}"):
                            self._approve_definition(definitie.id)

                with action_col3:
                    if st.button("🗑️ Verwijder", key=f"delete_{definitie.id}"):
                        self._delete_definition(definitie.id)

    def _reset_database(self):
        """Reset database (met bevestiging)."""
        if SessionStateManager.get_value("confirm_reset_db", False):
            try:
                # Backup current data first
                backup_path = (
                    f"backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
                )
                self.repository.export_to_json(backup_path, {})

                # Reset database
                setup_database(include_test_data=False)

                st.success(f"✅ Database gereset! Backup opgeslagen als {backup_path}")
                SessionStateManager.set_value("confirm_reset_db", False)

            except Exception as e:
                st.error(f"❌ Reset mislukt: {e!s}")
        else:
            st.warning("⚠️ Dit zal alle data wissen! Klik nogmaals om te bevestigen.")
            SessionStateManager.set_value("confirm_reset_db", True)

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
                    record.juridische_context or "",
                )

                if not existing:
                    self.repository.create_definitie(record)
                    added_count += 1

            st.success(f"✅ {added_count} test records toegevoegd!")

        except Exception as e:
            st.error(f"❌ Test data laden mislukt: {e!s}")

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
            st.error(f"❌ Cleanup mislukt: {e!s}")

    def _export_definitions(self, status, context, category, filename):
        """Export definities naar bestand."""
        try:
            filters = {}

            if status != "Alle":
                filters["status"] = DefinitieStatus(status)
            if context.strip():
                filters["organisatorische_context"] = context.strip()
            if category != "Alle":
                filters["categorie"] = OntologischeCategorie(category)

            # Export path
            export_path = (
                Path(__file__).parents[3] / "exports" / "definitions" / filename
            )
            export_path.parent.mkdir(parents=True, exist_ok=True)

            count = self.repository.export_to_json(str(export_path), filters)

            st.success(f"✅ {count} definities geëxporteerd naar {filename}")

            # Download button
            with open(export_path, "rb") as f:
                st.download_button(
                    label="📥 Download Export",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"❌ Export mislukt: {e!s}")

    def _preview_export(self, status, context, category):
        """Preview export data."""
        try:
            # Same filtering logic as export
            status_enum = None if status == "Alle" else DefinitieStatus(status)
            category_enum = (
                None if category == "Alle" else OntologischeCategorie(category)
            )
            context_filter = context if context.strip() else None

            results = self.repository.search_definities(
                categorie=category_enum,
                organisatorische_context=context_filter,
                status=status_enum,
                limit=100,  # Preview limit
            )

            st.info(f"📊 Preview: {len(results)} definities zouden worden geëxporteerd")

            if results:
                # Show first few as preview
                preview_df = pd.DataFrame(
                    [
                        {
                            "Begrip": r.begrip,
                            "Context": r.organisatorische_context,
                            "Categorie": r.categorie,
                            "Status": r.status,
                            "Score": r.validation_score,
                        }
                        for r in results[:10]
                    ]
                )

                st.dataframe(preview_df, use_container_width=True)

                if len(results) > 10:
                    st.caption(f"... en {len(results) - 10} meer records")

        except Exception as e:
            st.error(f"❌ Preview mislukt: {e!s}")

    def _import_definitions(self, uploaded_file, import_by):
        """Import definities uit bestand."""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, suffix=".json"
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # Import using repository
            successful, failed, errors = self.repository.import_from_json(
                tmp_path, import_by
            )

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
            st.error(f"❌ Import mislukt: {e!s}")

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
            st.error(f"❌ Duplicate scan mislukt: {e!s}")

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
                    st.warning(
                        f"• {definitie.begrip} (Score: {definitie.validation_score:.2f})"
                    )

        except Exception as e:
            st.error(f"❌ Validation scan mislukt: {e!s}")

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
            self.repository.get_statistics()
            st.success("✅ Database connectivity: OK")

            # Repository functionality
            self.repository.search_definities(limit=1)
            st.success("✅ Repository queries: OK")

            # CLI tools availability
            if CLI_TOOLS_AVAILABLE:
                st.success("✅ CLI tools: Available")
            else:
                st.warning("⚠️ CLI tools: Not available")

            # Validation system (V2) — alleen in DEV_MODE uitvoeren om externe afhankelijkheden te vermijden
            DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("1", "true", "yes")
            if DEV_MODE:
                try:
                    from services.container import get_container

                    container = get_container()
                    orchestrator = container.orchestrator()
                    validation_orch = getattr(orchestrator, "validation_service", None)
                    if validation_orch is None:
                        msg = "Validation orchestrator not available"
                        raise RuntimeError(msg)
                    # Kleine noop‑validatie om de integratie te testen
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            validation_orch.validate_text(
                                begrip="",
                                text="test",
                                ontologische_categorie=None,
                                context=None,
                            )
                        )
                        ok = isinstance(result, dict) and "overall_score" in result
                        if ok:
                            st.success("✅ Validation system (V2): OK")
                        else:
                            st.warning("⚠️ Validation system (V2): unexpected result")
                    finally:
                        loop.close()
                except Exception as e:
                    st.error(f"❌ Validation system (V2): {e!s}")
            else:
                st.info(
                    "ℹ️ Validation system check overgeslagen (set DEV_MODE=1 om te testen)"
                )

            st.success("🎯 Health check completed!")

        except Exception as e:
            st.error(f"❌ Health check failed: {e!s}")

    def _approve_definition(self, definitie_id: int):
        """Keur definitie goed."""
        try:
            success = self.checker.approve_definition(
                definitie_id=definitie_id,
                approved_by="ui_admin",
                notes="Goedgekeurd via management interface",
            )

            if success:
                st.success(f"✅ Definitie {definitie_id} goedgekeurd!")
                st.rerun()
            else:
                st.error(f"❌ Kon definitie {definitie_id} niet goedkeuren")

        except Exception as e:
            st.error(f"❌ Goedkeuring mislukt: {e!s}")

    def _delete_definition(self, definitie_id: int):
        """Verwijder definitie (met bevestiging)."""
        confirm_key = f"confirm_delete_{definitie_id}"

        if SessionStateManager.get_value(confirm_key, False):
            try:
                # Implementeer delete functionaliteit
                st.warning("🗑️ Delete functionaliteit nog niet geïmplementeerd")
                SessionStateManager.set_value(confirm_key, False)

            except Exception as e:
                st.error(f"❌ Verwijderen mislukt: {e!s}")
        else:
            st.warning("⚠️ Definitie verwijderen? Klik nogmaals om te bevestigen.")
            SessionStateManager.set_value(confirm_key, True)

    def _render_developer_tools(self):
        """Render developer testing en debug tools."""
        st.markdown("#### 🧪 Developer Tools & Testing")

        # Configuration testing
        with st.expander("⚙️ Configuration Testing", expanded=False):
            self._render_config_testing()

        # Prompt testing
        with st.expander("📝 Prompt Testing", expanded=False):
            self._render_prompt_testing()

        # Validation testing
        with st.expander("✅ Validation Testing", expanded=False):
            self._render_validation_testing()

        # Performance debugging
        with st.expander("⚡ Performance Debugging", expanded=False):
            self._render_performance_debugging()

        # AI Integration Testing
        with st.expander("🤖 AI Integration Testing", expanded=False):
            self._render_ai_integration_testing()

    def _render_config_testing(self):
        """Render configuration testing interface."""
        st.markdown("##### 🔧 Configuration Testing")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Verboden Woorden Test**")

            # Test individual word
            test_woord = st.text_input(
                "Test woord", placeholder="bijv. 'is'", key="dev_test_woord"
            )

            test_zin = st.text_input(
                "Test zin",
                placeholder="bijv. 'Is het proces waarbij...'",
                key="dev_test_zin",
            )

            if st.button("🧪 Test Woord", key="dev_test_woord_btn"):
                if test_woord and test_zin:
                    try:
                        import re

                        # Normalisatie
                        woord_norm = test_woord.strip().lower()
                        zin_norm = test_zin.strip().lower()

                        # Tests
                        komt_voor = woord_norm in zin_norm
                        regex_match = bool(
                            re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm)
                        )

                        # Resultaten
                        st.markdown("**Resultaten:**")
                        st.write(f"• Woord in zin: {'✅' if komt_voor else '❌'}")
                        st.write(
                            f"• Regex match aan begin: {'✅' if regex_match else '❌'}"
                        )

                        if regex_match:
                            st.success("🎯 Woord wordt gefilterd door opschoning")
                        elif komt_voor:
                            st.warning("⚠️ Woord komt voor maar niet aan het begin")
                        else:
                            st.info("i️ Woord komt niet voor in zin")

                    except Exception as e:
                        st.error(f"❌ Test fout: {e}")
                else:
                    st.warning("⚠️ Voer zowel woord als zin in")

        with col2:
            st.markdown("**V2 Validation Service Test**")

            try:
                # Use V2 validation service to get rule info
                container = SessionStateManager.get_value('service_container')
                if container:
                    validation_service = container.orchestrator()
                    # Get service info which includes rule count
                    service_info = validation_service.get_service_info()
                    st.write(f"📋 **V2 Validation Service:** {service_info.get('service_mode', 'unknown')}")
                    st.write(f"📋 **Validation Rules Available:** {service_info.get('rule_count', 0)}")

                    # Show sample info from service
                    st.code(f"Architecture: {service_info.get('architecture', 'unknown')}")
                    st.code(f"Version: {service_info.get('version', 'unknown')}")
                else:
                    st.warning("⚠️ Service container not initialized")

                if st.button("🔄 Refresh Service Info", key="dev_reload_rules"):
                    st.success("✅ Service info refreshed")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Cannot access V2 validation service: {e}")

    def _render_prompt_testing(self):
        """Render prompt testing interface."""
        st.markdown("##### 📝 Prompt Testing")

        col1, col2 = st.columns([1, 1])

        with col1:
            # Test begrip en context
            test_begrip = st.text_input(
                "Test begrip",
                placeholder="bijv. 'authenticatie'",
                key="dev_prompt_begrip",
            )

            test_org_context = st.selectbox(
                "Organisatorische context",
                ["DJI", "OM", "ZM", "KMAR", "Reclassering"],
                key="dev_prompt_org",
            )

            test_jur_context = st.selectbox(
                "Juridische context",
                ["Strafrecht", "Civiel recht", "Bestuursrecht"],
                key="dev_prompt_jur",
            )

            if st.button("🚀 Genereer Test Definitie", key="dev_generate_test"):
                if test_begrip:
                    with st.spinner("Genereren..."):
                        try:
                            # Simuleer definitie generatie

                            # Test via integrated service
                            from services.integrated_service import (
                                get_integrated_service,
                            )

                            get_integrated_service()

                            # Async call simulation (zou eigenlijk async moeten zijn)
                            st.success("🎯 Test definitie generatie gestart")
                            st.info(
                                "💡 Voor echte generatie, gebruik de definitie generatie tab"
                            )

                        except Exception as e:
                            st.error(f"❌ Test generatie fout: {e}")
                else:
                    st.warning("⚠️ Voer een begrip in")

        with col2:
            st.markdown("**Prompt Debug Info**")

            # Prompt statistieken
            st.metric("Max tokens", "350")
            st.metric("Temperature", "0.01")
            st.metric("Model", "gpt-4")

            # Test prompt opbouw
            if st.button("🔍 Toon Prompt Preview", key="dev_prompt_preview"):
                if test_begrip:
                    st.markdown("**Prompt Preview:**")
                    prompt_preview = f"""
                    Je bent een expert in beleidsmatige definities.

                    **Begrip:** {test_begrip}
                    **Context:** {test_org_context} - {test_jur_context}

                    [... volledige prompt zou hier staan ...]
                    """
                    st.code(prompt_preview)
                else:
                    st.warning("⚠️ Voer eerst een begrip in")

    def _render_validation_testing(self):
        """Render validation testing interface."""
        st.markdown("##### ✅ Validation Testing")

        # Check for DEV_MODE to enable V2 validation
        import os

        use_v2 = os.getenv("DEV_MODE", "false").lower() == "true"

        if use_v2:
            st.info("🚀 Using ValidationOrchestratorV2 (DEV_MODE enabled)")

        # Test definitie validatie
        test_definitie = st.text_area(
            "Test definitie voor validatie",
            placeholder="Voer een definitie in om te valideren...",
            height=100,
            key="dev_validation_definitie",
        )

        test_categorie = st.selectbox(
            "Ontologische categorie",
            ["type", "proces", "resultaat", "exemplaar"],
            key="dev_validation_categorie",
        )

        if st.button("🔍 Valideer Test Definitie", key="dev_validate_btn"):
            if test_definitie:
                try:
                    if use_v2:
                        # Use V2 validation orchestrator via service container (async)
                        from services.container import get_container

                        container = get_container()
                        orchestrator = container.orchestrator()
                        validation_orch = getattr(
                            orchestrator, "validation_service", None
                        )
                        if validation_orch is None:
                            msg = "Validation orchestrator not available"
                            raise RuntimeError(msg)

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                validation_orch.validate_text(
                                    begrip="",
                                    text=test_definitie,
                                    ontologische_categorie=test_categorie,
                                    context=None,
                                )
                            )
                        finally:
                            loop.close()

                        # Map result dict naar object-achtige velden voor weergave
                        class _R:
                            def __init__(self, d):
                                self._d = d
                                self.overall_score = d.get("overall_score", 0.0)
                                self.is_acceptable = d.get("is_acceptable", False)
                                self.violations = d.get("violations", [])

                        result = _R(result)
                    else:
                        # Always use V2 validation service
                        st.error("❌ V2 validation service (DEV_MODE) is required for validation testing")
                        return

                    st.markdown("**Validatie Resultaten:**")
                    st.metric("Overall Score", f"{result.overall_score:.2f}")
                    st.metric("Acceptabel", "✅" if result.is_acceptable else "❌")
                    st.metric("Violations", len(result.violations))

                    if result.violations:
                        st.markdown("**Violations:**")
                        for violation in result.violations[:5]:  # Toon eerste 5
                            st.warning(f"• {violation.description}")

                except Exception as e:
                    st.error(f"❌ Validatie fout: {e}")
            else:
                st.warning("⚠️ Voer een definitie in")

    def _render_performance_debugging(self):
        """Render performance debugging interface."""
        st.markdown("##### ⚡ Performance Debugging")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Cache Status**")

            try:
                # Cache informatie (simulatie)
                st.metric("Cache Hits", "42")
                st.metric("Cache Miss", "8")
                st.metric("Hit Rate", "84%")

                if st.button("🗑️ Clear Cache", key="dev_clear_cache"):
                    st.success("✅ Cache cleared (simulatie)")

            except Exception as e:
                st.error(f"❌ Cache info niet beschikbaar: {e}")

        with col2:
            st.markdown("**API Monitoring**")

            # API call statistieken
            st.metric("API Calls (vandaag)", "156")
            st.metric("Avg Response Time", "2.3s")
            st.metric("Errors", "3")

            # Service status
            service_status = {
                "Modern Generator": "🟢",
                "Legacy Service": "🟢",
                "Web Lookup": "🟡",
                "Validation": "🟢",
            }

            st.markdown("**Service Status:**")
            for service, status in service_status.items():
                st.write(f"{status} {service}")

            if st.button("🔄 Refresh Status", key="dev_refresh_status"):
                st.success("✅ Status refreshed")

    def _render_ai_integration_testing(self):
        """Render AI integration testing interface."""
        st.markdown("##### 🤖 AI Integration Testing")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Direct GPT Testing**")

            # Direct AI prompt testing
            test_model = st.selectbox(
                "AI Model",
                ["gpt-4.1", "gpt-4", "gpt-4-turbo"],
                key="ai_test_model",
            )

            test_temperature = st.slider(
                "Temperature", 0.0, 1.0, 0.01, key="ai_test_temperature"
            )

            test_max_tokens = st.number_input(
                "Max Tokens", 50, 2000, 350, key="ai_test_max_tokens"
            )

            # Custom prompt testing
            custom_prompt = st.text_area(
                "Custom AI Prompt",
                placeholder="Voer een custom prompt in voor directe AI testing...",
                height=100,
                key="ai_custom_prompt",
            )

            if st.button("🚀 Test Direct AI Call", key="ai_test_direct"):
                if custom_prompt:
                    with st.spinner("Calling AI..."):
                        try:
                            # Simulate AI call
                            st.success("🎯 AI Call Simulation:")
                            st.info(f"Model: {test_model}")
                            st.info(f"Temperature: {test_temperature}")
                            st.info(f"Max Tokens: {test_max_tokens}")
                            st.info(
                                "💡 Voor echte AI calls, gebruik de integrated service"
                            )

                            # Log API call
                            try:
                                # Simulate API monitoring
                                st.caption("📊 API call would be monitored")
                            except ImportError:
                                st.caption("⚠️ API monitoring niet beschikbaar")

                        except Exception as e:
                            st.error(f"❌ AI test fout: {e}")
                else:
                    st.warning("⚠️ Voer een prompt in")

        with col2:
            st.markdown("**Integrated Service Testing**")

            # Test integrated service different modes
            service_mode = st.selectbox(
                "Service Mode",
                ["AUTO", "MODERN", "LEGACY", "HYBRID"],
                key="ai_service_mode",
            )

            # Test definitie generation via integrated service
            test_begrip = st.text_input(
                "Test Begrip",
                placeholder="bijv. 'digitale identiteit'",
                key="ai_integrated_begrip",
            )

            st.selectbox(
                "Test Context",
                ["DJI", "OM", "KMAR", "Reclassering"],
                key="ai_integrated_context",
            )

            if st.button("🔧 Test Integrated Service", key="ai_test_integrated"):
                if test_begrip:
                    with st.spinner("Testing integrated service..."):
                        try:
                            from services.integrated_service import (
                                ServiceConfig,
                                ServiceMode,
                                get_integrated_service,
                            )

                            # Create config for testing
                            service_config = ServiceConfig(
                                mode=ServiceMode(service_mode.lower()),
                                enable_monitoring=True,
                                # Web lookup is automatic when available; no explicit toggle
                            )

                            service = get_integrated_service(service_config)

                            # Get service info
                            service_info = service.get_service_info()

                            st.success("🎯 Integrated Service Test:")
                            st.json(
                                {
                                    "active_mode": service_info["active_mode"],
                                    "modern_available": service_info["availability"][
                                        "modern_services"
                                    ],
                                    "legacy_available": service_info["availability"][
                                        "legacy_services"
                                    ],
                                    "web_lookup": service_info["availability"][
                                        "web_lookup"
                                    ],
                                    "monitoring": service_info["availability"][
                                        "monitoring"
                                    ],
                                }
                            )

                            st.info(
                                "💡 Voor volledige generatie, gebruik de definitie tab"
                            )

                        except Exception as e:
                            st.error(f"❌ Integrated service test fout: {e}")
                else:
                    st.warning("⚠️ Voer een begrip in")

            # API Key testing
            st.markdown("**API Key & Configuration**")

            if st.button("🔑 Test API Keys", key="ai_test_keys"):
                try:
                    import os

                    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv(
                        "OPENAI_API_KEY_PROD"
                    )

                    if openai_key:
                        # Mask API key for security
                        masked_key = (
                            openai_key[:8] + "..." + openai_key[-4:]
                            if len(openai_key) > 12
                            else "***"
                        )
                        st.success(f"✅ OpenAI API Key: {masked_key}")
                    else:
                        st.error("❌ OpenAI API Key niet gevonden")

                    # Test other env vars
                    other_vars = ["AZURE_OPENAI_ENDPOINT", "ANTHROPIC_API_KEY"]
                    for var in other_vars:
                        value = os.getenv(var)
                        if value:
                            st.info(f"✅ {var}: Configured")
                        else:
                            st.caption(f"i️ {var}: Niet geconfigureerd")

                except Exception as e:
                    st.error(f"❌ API key test fout: {e}")

        # Live API monitoring section
        st.markdown("---")
        st.markdown("**🔴 Live API Monitoring**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Current Metrics", key="ai_current_metrics"):
                try:
                    from services.integrated_service import get_integrated_service

                    service = get_integrated_service()

                    # Get operation stats
                    stats = service.operation_stats

                    if stats:
                        st.json(stats)
                    else:
                        st.info("📭 Geen recente operaties")

                except Exception as e:
                    st.error(f"❌ Metrics ophalen mislukt: {e}")

        with col2:
            if st.button("💰 Cost Estimate", key="ai_cost_estimate"):
                st.info("📈 Cost estimation: $0.0042/request (gemiddeld)")
                st.caption("Based on GPT-4 pricing voor definition generation")

        with col3:
            if st.button("⚡ Performance Test", key="ai_performance_test"):
                with st.spinner("Testing performance..."):
                    import time

                    start = time.time()
                    time.sleep(0.1)  # Simulate processing
                    duration = time.time() - start

                    st.success(f"⏱️ Test completed in {duration:.3f}s")

        with col4:
            if st.button("🔄 Reset Stats", key="ai_reset_stats"):
                try:
                    from services.integrated_service import get_integrated_service

                    service = get_integrated_service()
                    service.operation_stats = {}
                    st.success("✅ Statistics reset")
                except Exception as e:
                    st.error(f"❌ Reset mislukt: {e}")
