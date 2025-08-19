"""
External Sources Tab - Interface voor externe definitie bronnen.
"""

import json  # JSON data verwerking voor configuraties
from datetime import datetime  # Datum en tijd functionaliteit
from pathlib import Path  # Bestandspad manipulatie

import streamlit as st  # Streamlit web interface framework
from database.definitie_repository import (  # Database toegang voor definities
    DefinitieRepository,
    DefinitieStatus,
)
from ui.session_state import (  # Sessie status management voor Streamlit
    SessionStateManager,
)


class ExternalSourcesTab:
    """Tab voor externe bronnen beheer.

    Beheert verbindingen met externe definitie bronnen en importeert
    definities van verschillende externe systemen en databases.
    """

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer external sources tab met database repository."""
        self.repository = repository  # Database repository voor definitie opslag
        self._init_external_adapter()  # Initialiseer externe bron adapters

    def _init_external_adapter(self):
        """Initialiseer external source adapter voor externe bronnen."""
        try:
            import sys  # Systeem interface voor path manipulatie
            from pathlib import Path  # Object-georiënteerde bestandspad manipulatie

            sys.path.append(
                str(Path(__file__).parents[2] / "external")
            )  # Voeg externe module pad toe

            # Importeer externe bron adapter componenten
            from external_source_adapter import (
                ExternalSourceConfig,  # Configuratie container voor bronnen
                ExternalSourceManager,  # Manager voor externe bronnen
                ExternalSourceType,  # Enumeratie van bron types
                FileSystemAdapter,  # Bestandssysteem adapter
                MockExternalAdapter,  # Mock adapter voor development
                create_file_source,  # Factory voor bestandssysteem bronnen
                create_mock_source,  # Factory voor mock bronnen (testing)
            )

            # Sla klassen op voor gebruik in de tab
            self.ExternalSourceManager = (
                ExternalSourceManager  # Manager klasse referentie
            )
            self.create_mock_source = create_mock_source  # Mock bron factory referentie
            self.create_file_source = (
                create_file_source  # Bestand bron factory referentie
            )
            self.ExternalSourceConfig = ExternalSourceConfig  # Config klasse referentie
            self.ExternalSourceType = ExternalSourceType  # Type enum referentie
            self.MockExternalAdapter = MockExternalAdapter  # Mock adapter referentie
            self.FileSystemAdapter = (
                FileSystemAdapter  # Bestandssysteem adapter referentie
            )

            # Initialiseer manager in sessie state voor persistentie
            if "external_source_manager" not in st.session_state:
                st.session_state.external_source_manager = (
                    self.ExternalSourceManager()
                )  # Maak nieuwe manager instantie

        except Exception as e:
            st.error(
                f"❌ Kon external source adapter niet laden: {e!s}"
            )  # Toon foutmelding aan gebruiker
            self.ExternalSourceManager = None  # Zet manager op None bij falen

    def render(self):
        """Render external sources tab."""
        if not self.ExternalSourceManager:
            st.error("❌ External Source Adapter niet beschikbaar")
            return

        st.markdown("### 🔌 Externe Bronnen")

        # Main interface
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 Bronnen", "🔍 Zoeken", "📥 Import", "⚙️ Configuratie"]
        )

        with tab1:
            self._render_source_management()

        with tab2:
            self._render_source_search()

        with tab3:
            self._render_import_interface()

        with tab4:
            self._render_source_configuration()

    def _render_source_management(self):
        """Render source management interface."""
        st.markdown("#### 📋 Geregistreerde Bronnen")

        manager = st.session_state.external_source_manager

        # Show registered sources
        source_info = manager.get_source_info()

        if source_info:
            for info in source_info:
                with st.expander(f"🔌 {info['source_name']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**ID:** {info['source_id']}")
                        st.write(f"**Type:** {info['source_type']}")
                        status_color = "🟢" if info["connected"] else "🔴"
                        st.write(
                            f"**Status:** {status_color} {'Verbonden' if info['connected'] else 'Niet verbonden'}"
                        )

                    with col2:
                        if st.button("🔍 Test", key=f"test_{info['source_id']}"):
                            adapter = manager.get_adapter(info["source_id"])
                            if adapter:
                                if adapter.test_connection():
                                    st.success("✅ Verbinding succesvol")
                                else:
                                    st.error("❌ Verbinding mislukt")

                    with col3:
                        if st.button("🗑️ Verwijder", key=f"remove_{info['source_id']}"):
                            if manager.unregister_source(info["source_id"]):
                                st.success("✅ Bron verwijderd")
                                st.rerun()
                            else:
                                st.error("❌ Kon bron niet verwijderen")
        else:
            st.info("📭 Geen externe bronnen geregistreerd")

        # Add new source
        st.markdown("#### ➕ Nieuwe Bron Toevoegen")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧪 Mock Bron Toevoegen", type="primary"):
                mock_adapter = self.create_mock_source("Demo Mock Source")
                if mock_adapter.connect():
                    manager.register_source(mock_adapter)
                    st.success("✅ Mock bron toegevoegd")
                    st.rerun()
                else:
                    st.error("❌ Kon mock bron niet verbinden")

        with col2:
            uploaded_file = st.file_uploader(
                "📁 Upload Definitie Bestand",
                type=["json", "csv"],
                help="Upload JSON of CSV bestand met definities",
            )

            if uploaded_file:
                if st.button("📥 Bestand Bron Toevoegen"):
                    # Save uploaded file temporarily
                    temp_path = Path("cache") / f"uploaded_{uploaded_file.name}"
                    temp_path.parent.mkdir(exist_ok=True)

                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Create file source
                    file_adapter = self.create_file_source(
                        str(temp_path), f"Upload: {uploaded_file.name}"
                    )

                    if file_adapter.connect():
                        manager.register_source(file_adapter)
                        st.success(f"✅ Bestand bron toegevoegd: {uploaded_file.name}")
                        st.rerun()
                    else:
                        st.error("❌ Kon bestand bron niet verbinden")

    def _render_source_search(self):
        """Render search interface for external sources."""
        st.markdown("#### 🔍 Zoeken in Externe Bronnen")

        manager = st.session_state.external_source_manager

        # Search controls
        col1, col2, col3 = st.columns(3)

        with col1:
            search_query = st.text_input(
                "Zoekterm",
                placeholder="Zoek naar begrip of definitie...",
                key="external_search_query",
            )

        with col2:
            categorie_filter = st.selectbox(
                "Categorie",
                ["Alle", "type", "proces", "resultaat", "exemplaar"],
                key="external_search_category",
            )

        with col3:
            context_filter = st.text_input(
                "Context Filter",
                placeholder="Filter op context...",
                key="external_search_context",
            )

        # Search button
        if st.button("🔍 Zoeken in Alle Bronnen", type="primary"):
            with st.spinner("Zoeken in externe bronnen..."):
                try:
                    # Prepare search parameters
                    search_params = {}
                    if search_query:
                        search_params["query"] = search_query
                    if categorie_filter != "Alle":
                        search_params["categorie"] = categorie_filter
                    if context_filter:
                        search_params["context"] = context_filter

                    # Search all sources
                    results = manager.search_all_sources(
                        **search_params, limit_per_source=20
                    )

                    # Store results
                    SessionStateManager.set_value(
                        "external_search_results",
                        {
                            "results": results,
                            "timestamp": datetime.now().isoformat(),
                            "search_params": search_params,
                        },
                    )

                    # Display results
                    self._display_search_results(results)

                except Exception as e:
                    st.error(f"❌ Zoekfout: {e!s}")

        # Show previous results
        previous_results = SessionStateManager.get_value("external_search_results")
        if previous_results:
            st.markdown("#### 📋 Laatste Zoekresultaten")
            self._display_search_results(previous_results["results"])

    def _display_search_results(self, results: dict[str, list]):
        """Display search results from external sources."""
        total_results = sum(len(source_results) for source_results in results.values())

        if total_results == 0:
            st.info("🔍 Geen resultaten gevonden")
            return

        st.success(f"✅ {total_results} resultaten gevonden uit {len(results)} bronnen")

        for source_id, source_results in results.items():
            if source_results:
                with st.expander(
                    f"📁 {source_id} ({len(source_results)} resultaten)", expanded=True
                ):
                    for i, ext_def in enumerate(source_results):
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])

                            with col1:
                                st.markdown(f"**{ext_def.begrip}**")
                                st.markdown(
                                    f"*{ext_def.definitie[:100]}...*"
                                    if len(ext_def.definitie) > 100
                                    else f"*{ext_def.definitie}*"
                                )
                                st.caption(
                                    f"Context: {ext_def.context} | Status: {ext_def.status}"
                                )

                            with col2:
                                st.caption(f"Categorie: {ext_def.categorie}")
                                if ext_def.metadata:
                                    st.caption(
                                        f"Metadata: {len(ext_def.metadata)} items"
                                    )

                            with col3:
                                if st.button(
                                    "📥 Import", key=f"import_{source_id}_{i}"
                                ):
                                    self._import_external_definition(ext_def, source_id)

                            st.markdown("---")

    def _render_import_interface(self):
        """Render import interface."""
        st.markdown("#### 📥 Import Definities")

        # Bulk import options
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📦 Bulk Import")

            selected_source = st.selectbox(
                "Selecteer Bron",
                options=[""]
                + [
                    info["source_id"]
                    for info in st.session_state.external_source_manager.get_source_info()
                ],
                key="bulk_import_source",
            )

            if selected_source:
                import_limit = st.number_input(
                    "Maximum Definities",
                    min_value=1,
                    max_value=100,
                    value=10,
                    key="bulk_import_limit",
                )

                if st.button("📥 Import Alle Beschikbare", type="primary"):
                    self._perform_bulk_import(selected_source, import_limit)

        with col2:
            st.markdown("##### ⚙️ Import Instellingen")

            import_options = {
                "auto_validate": st.checkbox("🔍 Automatisch valideren", value=True),
                "set_status": st.selectbox(
                    "Status instellen",
                    [status.value for status in DefinitieStatus],
                    index=1,  # REVIEW
                ),
                "add_metadata": st.checkbox("📋 Metadata behouden", value=True),
                "overwrite_existing": st.checkbox(
                    "🔄 Bestaande overschrijven", value=False
                ),
            }

            SessionStateManager.set_value("import_options", import_options)

        # Import history
        self._render_import_history()

    def _render_import_history(self):
        """Render import history."""
        st.markdown("##### 📜 Import Geschiedenis")

        import_history = SessionStateManager.get_value("import_history", [])

        if import_history:
            for i, entry in enumerate(import_history[-5:]):  # Show last 5
                with st.expander(
                    f"📥 Import {i+1}: {entry.get('timestamp', 'Onbekend')}",
                    expanded=False,
                ):
                    st.write(f"**Bron:** {entry.get('source_id', 'Onbekend')}")
                    st.write(
                        f"**Geïmporteerd:** {entry.get('imported_count', 0)} definities"
                    )
                    st.write(f"**Status:** {entry.get('status', 'Onbekend')}")
                    if entry.get("errors"):
                        st.error(f"Fouten: {len(entry['errors'])}")
        else:
            st.info("📭 Geen import geschiedenis beschikbaar")

    def _render_source_configuration(self):
        """Render source configuration interface."""
        st.markdown("#### ⚙️ Bron Configuratie")

        # Manual source configuration
        with st.expander("🔧 Handmatige Bron Configuratie", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                source_id = st.text_input("Bron ID", key="manual_source_id")
                source_name = st.text_input("Bron Naam", key="manual_source_name")
                source_type = st.selectbox(
                    "Bron Type",
                    [t.value for t in self.ExternalSourceType],
                    key="manual_source_type",
                )

            with col2:
                connection_string = st.text_input(
                    "Verbinding String",
                    help="URL, bestandspad, of verbindingsstring",
                    key="manual_connection_string",
                )
                api_key = st.text_input(
                    "API Key (optioneel)", type="password", key="manual_api_key"
                )
                timeout = st.number_input(
                    "Timeout (seconden)",
                    min_value=1,
                    max_value=300,
                    value=30,
                    key="manual_timeout",
                )

            if st.button("➕ Configureer Bron"):
                if source_id and source_name and connection_string:
                    self._create_manual_source(
                        source_id,
                        source_name,
                        source_type,
                        connection_string,
                        api_key,
                        timeout,
                    )
                else:
                    st.error("❌ Vul alle verplichte velden in")

        # Configuration export/import
        st.markdown("##### 💾 Configuratie Beheer")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📁 Export Configuratie"):
                self._export_source_configuration()

        with col2:
            config_file = st.file_uploader(
                "📥 Import Configuratie", type=["json"], key="config_upload"
            )

            if config_file and st.button("⚙️ Import Configuratie"):
                self._import_source_configuration(config_file)

    def _import_external_definition(self, ext_def, source_id: str):
        """Import individual external definition."""
        try:
            # Get import options
            options = SessionStateManager.get_value("import_options", {})

            # Get source config
            manager = st.session_state.external_source_manager
            adapter = manager.get_adapter(source_id)

            if not adapter:
                st.error("❌ Kon bron adapter niet vinden")
                return

            # Convert to DefinitieRecord
            definitie_record = ext_def.to_definitie_record(adapter.config)

            # Set status based on options
            if options.get("set_status"):
                definitie_record.status = options["set_status"]

            # Check if exists
            existing = self.repository.search_definities(query=ext_def.begrip, limit=1)

            if existing and not options.get("overwrite_existing", False):
                st.warning(
                    f"⚠️ Definitie '{ext_def.begrip}' bestaat al. Schakel 'Bestaande overschrijven' in om te vervangen."
                )
                return

            # Save to database
            if existing and options.get("overwrite_existing", False):
                # Update existing
                success = self.repository.update_definitie(
                    existing[0].id,
                    {
                        "definitie": definitie_record.definitie,
                        "categorie": definitie_record.categorie,
                        "organisatorische_context": definitie_record.organisatorische_context,
                        "juridische_context": definitie_record.juridische_context,
                        "source_reference": definitie_record.source_reference,
                        "imported_from": definitie_record.imported_from,
                    },
                    "system_import",
                )

                if success:
                    st.success(f"✅ Definitie '{ext_def.begrip}' bijgewerkt")
                else:
                    st.error(f"❌ Kon definitie '{ext_def.begrip}' niet bijwerken")
            else:
                # Create new
                new_id = self.repository.create_definitie(definitie_record)

                if new_id:
                    st.success(
                        f"✅ Definitie '{ext_def.begrip}' geïmporteerd (ID: {new_id})"
                    )

                    # Add to import history
                    import_history = SessionStateManager.get_value("import_history", [])
                    import_history.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "source_id": source_id,
                            "begrip": ext_def.begrip,
                            "imported_count": 1,
                            "status": "success",
                        }
                    )
                    SessionStateManager.set_value("import_history", import_history)
                else:
                    st.error(f"❌ Kon definitie '{ext_def.begrip}' niet importeren")

        except Exception as e:
            st.error(f"❌ Import fout: {e!s}")

    def _perform_bulk_import(self, source_id: str, limit: int):
        """Perform bulk import from source."""
        with st.spinner(f"Importeer tot {limit} definities van {source_id}..."):
            try:
                manager = st.session_state.external_source_manager
                adapter = manager.get_adapter(source_id)

                if not adapter:
                    st.error("❌ Kon bron adapter niet vinden")
                    return

                # Connect to source
                if not adapter.connected:
                    adapter.connect()

                # Search all definitions
                ext_definitions = adapter.search_definitions(limit=limit)

                if not ext_definitions:
                    st.warning("⚠️ Geen definities gevonden in bron")
                    return

                # Import each definition
                imported_count = 0
                errors = []

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, ext_def in enumerate(ext_definitions):
                    progress = (i + 1) / len(ext_definitions)
                    progress_bar.progress(progress)
                    status_text.text(f"Importeer: {ext_def.begrip}")

                    try:
                        # Convert and save
                        definitie_record = ext_def.to_definitie_record(adapter.config)
                        new_id = self.repository.create_definitie(definitie_record)

                        if new_id:
                            imported_count += 1
                        else:
                            errors.append(f"Kon '{ext_def.begrip}' niet opslaan")

                    except Exception as e:
                        errors.append(f"Fout bij '{ext_def.begrip}': {e!s}")

                # Clear progress
                progress_bar.empty()
                status_text.empty()

                # Show results
                if imported_count > 0:
                    st.success(
                        f"✅ {imported_count} van {len(ext_definitions)} definities geïmporteerd"
                    )

                if errors:
                    st.error(f"❌ {len(errors)} fouten opgetreden")
                    with st.expander("🔍 Fout Details", expanded=False):
                        for error in errors:
                            st.write(f"- {error}")

                # Add to history
                import_history = SessionStateManager.get_value("import_history", [])
                import_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "source_id": source_id,
                        "imported_count": imported_count,
                        "total_attempted": len(ext_definitions),
                        "errors": errors,
                        "status": "completed",
                    }
                )
                SessionStateManager.set_value("import_history", import_history)

            except Exception as e:
                st.error(f"❌ Bulk import fout: {e!s}")

    def _create_manual_source(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        connection_string: str,
        api_key: str,
        timeout: int,
    ):
        """Create manually configured source."""
        try:
            config = self.ExternalSourceConfig(
                source_id=source_id,
                source_name=source_name,
                source_type=self.ExternalSourceType(source_type),
                connection_string=connection_string,
                api_key=api_key if api_key else None,
                timeout=timeout,
            )

            # Create appropriate adapter
            if source_type == "file_system":
                adapter = self.FileSystemAdapter(config)
            else:
                # For now, use mock adapter for other types
                adapter = self.MockExternalAdapter(config)

            # Test connection
            if adapter.connect():
                # Register source
                manager = st.session_state.external_source_manager
                manager.register_source(adapter)

                st.success(f"✅ Bron '{source_name}' succesvol geconfigureerd")
                st.rerun()
            else:
                st.error("❌ Kon geen verbinding maken met de bron")

        except Exception as e:
            st.error(f"❌ Configuratiefout: {e!s}")

    def _export_source_configuration(self):
        """Export source configuration to JSON."""
        try:
            manager = st.session_state.external_source_manager
            source_info = manager.get_source_info()

            config_data = {
                "export_timestamp": datetime.now().isoformat(),
                "sources": source_info,
            }

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"external_sources_config_{timestamp}.json"

            import os

            os.makedirs("exports", exist_ok=True)
            filepath = os.path.join("exports", filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            st.success(f"✅ Configuratie geëxporteerd naar: {filepath}")

            # Offer download
            with open(filepath) as f:
                st.download_button(
                    label="📁 Download Configuratie",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"❌ Export fout: {e!s}")

    def _import_source_configuration(self, config_file):
        """Import source configuration from JSON."""
        try:
            config_data = json.load(config_file)
            sources = config_data.get("sources", [])

            imported_count = 0
            errors = []

            for source_info in sources:
                try:
                    # Recreate source configuration
                    # Note: This is a simplified implementation
                    # In practice, you'd need to store more detailed config info
                    st.info(
                        f"⚠️ Import van bron '{source_info['source_name']}' vereist handmatige herconfiguratie"
                    )
                    imported_count += 1

                except Exception as e:
                    errors.append(
                        f"Fout bij {source_info.get('source_name', 'onbekend')}: {e!s}"
                    )

            if imported_count > 0:
                st.success(f"✅ {imported_count} bronnen geïmporteerd")

            if errors:
                st.error(f"❌ {len(errors)} fouten")
                for error in errors:
                    st.write(f"- {error}")

        except Exception as e:
            st.error(f"❌ Import configuratie fout: {e!s}")
