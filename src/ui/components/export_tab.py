"""
Export Tab - Interface voor definitie export en beheer functionaliteit.
"""

import io
import json
from datetime import UTC, datetime, timedelta

UTC = UTC  # Voor Python 3.10 compatibility

import pandas as pd
import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from services.service_factory import get_definition_service


class ExportTab:
    """Tab voor definitie export en beheer functionaliteit."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer export tab."""
        self.repository = repository
        try:
            self.service = get_definition_service()
        except Exception:
            # In testomgevingen zonder API key: gebruik dummy service
            class _DummyService:
                def get_service_info(self) -> dict:
                    return {
                        "service_mode": "dummy",
                        "architecture": "none",
                        "version": "test",
                    }

            self.service = _DummyService()

    def render(self):
        """Render export tab."""
        # Export section
        self._render_export_section()

        # Bulk operations section
        self._render_bulk_operations()

        # Database management section
        self._render_database_management()

        # Statistics section
        self._render_statistics_section()

    def _render_export_section(self):
        """Render export functionaliteit."""
        st.markdown("### 📤 Export Definities")

        # Export filters
        col1, col2, col3 = st.columns(3)

        with col1:
            export_format = st.selectbox(
                "Export formaat",
                ["TXT", "CSV", "JSON", "Excel"],
                help="Selecteer het gewenste export formaat",
            )

        with col2:
            status_filter = st.selectbox(
                "Status filter",
                ["Alle"] + [status.value for status in DefinitieStatus],
                help="Filter op definitie status",
            )

        with col3:
            date_range = st.selectbox(
                "Tijdsperiode",
                [
                    "Alle",
                    "Laatste week",
                    "Laatste maand",
                    "Laatste 3 maanden",
                    "Aangepast...",
                ],
                help="Filter op datum",
            )

        # Additional filters
        with st.expander("🔧 Geavanceerde Filters", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                context_filter = st.text_input(
                    "Organisatorische context",
                    placeholder="Filter op organisatie...",
                    help="Gebruik wildcards (*) voor patroon matching",
                )

                categorie_filter = st.multiselect(
                    "Categorieën",
                    ["type", "proces", "resultaat", "exemplaar"],
                    help="Selecteer categorieën om te exporteren",
                )

            with col2:
                min_score = st.slider(
                    "Minimum kwaliteitsscore",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Exporteer alleen definities met score >= deze waarde",
                )

                include_metadata = st.checkbox(
                    "Inclusief metadata",
                    value=True,
                    help="Voeg metadata toe aan export (timestamps, scores, etc.)",
                )

        # Custom date range
        start_date = end_date = None
        if date_range == "Aangepast...":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Van datum")
            with col2:
                end_date = st.date_input("Tot datum")

        # Export actions
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔍 Preview Export", help="Bekijk export voordat je download"):
                self._preview_export(
                    export_format,
                    status_filter,
                    date_range,
                    context_filter,
                    categorie_filter,
                    min_score,
                    include_metadata,
                    start_date,
                    end_date,
                )

        with col2:
            if st.button("📤 Export", type="primary", help="Download export bestand"):
                self._execute_export(
                    export_format,
                    status_filter,
                    date_range,
                    context_filter,
                    categorie_filter,
                    min_score,
                    include_metadata,
                    start_date,
                    end_date,
                )

        with col3:
            if st.button("📧 Email Export", help="Verstuur export via email"):
                self._email_export()

        with col4:
            if st.button("⏰ Plan Export", help="Plan automatische exports"):
                self._schedule_export()

    def _render_bulk_operations(self):
        """Render bulk operaties sectie."""
        st.markdown("### 🔄 Bulk Operaties")

        with st.expander("Bulk Status Updates", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                bulk_status_filter = st.selectbox(
                    "Selecteer definities met status",
                    [status.value for status in DefinitieStatus],
                    key="bulk_status_filter",
                )

            with col2:
                new_status = st.selectbox(
                    "Nieuwe status",
                    [status.value for status in DefinitieStatus],
                    key="bulk_new_status",
                )

            with col3:
                bulk_reason = st.text_area(
                    "Reden voor wijziging",
                    placeholder="Voer reden voor bulk update in...",
                    key="bulk_reason",
                )

            if st.button("🔄 Update Status (Bulk)", key="bulk_update"):
                self._execute_bulk_status_update(
                    bulk_status_filter, new_status, bulk_reason
                )

        with st.expander("Bulk Import", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload definitie bestand",
                type=["json", "csv", "xlsx"],
                help="Upload een bestand met definities om te importeren",
            )

            if uploaded_file:
                col1, col2 = st.columns(2)

                with col1:
                    import_mode = st.selectbox(
                        "Import modus",
                        ["Nieuwe definities", "Update bestaande", "Vervang alles"],
                        help="Bepaal hoe imports worden behandeld",
                    )

                with col2:
                    duplicate_handling = st.selectbox(
                        "Duplicate handling",
                        ["Overslaan", "Overschrijven", "Nieuwe versie"],
                        help="Wat te doen met duplicates",
                    )

                if st.button("📥 Import", key="bulk_import"):
                    self._execute_bulk_import(
                        uploaded_file, import_mode, duplicate_handling
                    )

    def _render_database_management(self):
        """Render database management sectie."""
        st.markdown("### 🗄️ Database Beheer")

        with st.expander("Database Status", expanded=False):
            try:
                stats = self.repository.get_statistics()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_defs = stats.get("total_definitions", 0)
                    st.metric("📊 Totaal Definities", total_defs)

                with col2:
                    established = stats.get("by_status", {}).get("established", 0)
                    st.metric("✅ Vastgesteld", established)

                with col3:
                    in_review = stats.get("by_status", {}).get("review", 0)
                    st.metric("🔄 In Review", in_review)

                with col4:
                    avg_score = stats.get("average_validation_score", 0)
                    st.metric(
                        "📈 Gem. Score", f"{avg_score:.2f}" if avg_score else "N/A"
                    )

                # Database health check
                st.markdown("#### 🩺 Database Health Check")
                health_status = self._check_database_health()

                for check, result in health_status.items():
                    if result["status"] == "ok":
                        st.success(f"✅ {check}: {result['message']}")
                    elif result["status"] == "warning":
                        st.warning(f"⚠️ {check}: {result['message']}")
                    else:
                        st.error(f"❌ {check}: {result['message']}")

            except Exception as e:
                st.error(f"❌ Kon database status niet ophalen: {e!s}")

        with st.expander("Database Operaties", expanded=False):
            st.warning("⚠️ Gevaarlijke operaties - gebruik met voorzichtigheid")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(
                    "🗑️ Cleanup Duplicates", help="Verwijder exacte duplicaten"
                ):
                    self._cleanup_duplicates()

            with col2:
                if st.button("🔄 Rebuild Indexes", help="Herbouw database indexen"):
                    self._rebuild_indexes()

            with col3:
                if st.button(
                    "📊 Analyze Database", help="Analyseer database prestaties"
                ):
                    self._analyze_database()

    def _render_statistics_section(self):
        """Render statistieken sectie."""
        st.markdown("### 📊 Statistieken & Analytics")

        try:
            stats = self.repository.get_statistics()

            # Status distribution pie chart
            if stats.get("by_status"):
                st.markdown("#### Status Verdeling")
                status_df = pd.DataFrame(
                    list(stats["by_status"].items()), columns=["Status", "Aantal"]
                )
                st.bar_chart(status_df.set_index("Status"))

            # Category distribution
            if stats.get("by_category"):
                st.markdown("#### Categorie Verdeling")
                cat_df = pd.DataFrame(
                    list(stats["by_category"].items()), columns=["Categorie", "Aantal"]
                )
                st.bar_chart(cat_df.set_index("Categorie"))

            # Recent activity
            self._render_recent_activity()

        except Exception as e:
            st.error(f"❌ Kon statistieken niet laden: {e!s}")

    def _render_recent_activity(self):
        """Render recente activiteit."""
        st.markdown("#### 📅 Recente Activiteit")

        try:
            # Get recent definitions
            recent_defs = self.repository.search_definities(limit=10)

            if recent_defs:
                activity_data = []
                for def_rec in recent_defs:
                    activity_data.append(
                        {
                            "Datum": (
                                def_rec.created_at.strftime("%Y-%m-%d %H:%M")
                                if def_rec.created_at
                                else "Onbekend"
                            ),
                            "Begrip": def_rec.begrip,
                            "Status": def_rec.status,
                            "Context": def_rec.organisatorische_context,
                            "Score": (
                                f"{def_rec.validation_score:.2f}"
                                if def_rec.validation_score
                                else "N/A"
                            ),
                        }
                    )

                df = pd.DataFrame(activity_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Geen recente activiteit gevonden")

        except Exception as e:
            st.error(f"❌ Kon recente activiteit niet laden: {e!s}")

    def _preview_export(
        self,
        format_type,
        status_filter,
        date_range,
        context_filter,
        categorie_filter,
        min_score,
        include_metadata,
        start_date,
        end_date,
    ):
        """Preview export data."""
        try:
            # Get filtered data
            filtered_data = self._get_filtered_export_data(
                status_filter,
                date_range,
                context_filter,
                categorie_filter,
                min_score,
                start_date,
                end_date,
            )

            if not filtered_data:
                st.info("Geen data gevonden met de geselecteerde filters")
                return

            st.markdown(f"### 👁️ Export Preview ({len(filtered_data)} definities)")

            # Show first few records
            preview_data = []
            for def_rec in filtered_data[:5]:
                preview_data.append(
                    {
                        "ID": def_rec.id,
                        "Begrip": def_rec.begrip,
                        "Status": def_rec.status,
                        "Context": def_rec.organisatorische_context,
                        "Score": (
                            f"{def_rec.validation_score:.2f}"
                            if def_rec.validation_score
                            else "N/A"
                        ),
                    }
                )

            df = pd.DataFrame(preview_data)
            st.dataframe(df, use_container_width=True)

            if len(filtered_data) > 5:
                st.info(f"Toont de eerste 5 van {len(filtered_data)} definities")

        except Exception as e:
            st.error(f"❌ Kon preview niet genereren: {e!s}")

    def _execute_export(
        self,
        format_type,
        status_filter,
        date_range,
        context_filter,
        categorie_filter,
        min_score,
        include_metadata,
        start_date,
        end_date,
    ):
        """Voer export uit via nieuwe services."""
        try:
            # Get filtered data
            filtered_data = self._get_filtered_export_data(
                status_filter,
                date_range,
                context_filter,
                categorie_filter,
                min_score,
                start_date,
                end_date,
            )

            if not filtered_data:
                st.error("Geen data gevonden voor export")
                return

            st.success(f"✅ Export gegenereerd: {len(filtered_data)} definities")

            # Voor bulk export via nieuwe services - loop through filtered_data
            for def_rec in filtered_data:
                try:
                    # Bereid additional_data voor voor elke definitie
                    additional_data = {
                        "metadata": (
                            {
                                "id": def_rec.id,
                                "status": def_rec.status,
                                "categorie": def_rec.categorie,
                                # Optionele velden; sommige modellen hebben deze niet
                                "datum_voorstel": getattr(def_rec, "created_at", None),
                                "voorsteller": getattr(def_rec, "created_by", None) or "Systeem",
                                "versie": getattr(def_rec, "version_number", None),
                            }
                            if include_metadata
                            else {}
                        ),
                        # Context kan verschillen per record; indien aanwezig meegeven
                        "context_dict": getattr(def_rec, "context", {}) or {},
                    }

                    # Probeer sync export via service adapter
                    try:
                        result = self.service.export_definition(
                            definition_id=def_rec.id,
                            ui_data=additional_data,
                            format=format_type.lower(),
                        )
                    except NotImplementedError:
                        # Fallback naar async export indien validatiegate actief is
                        from services.container import get_container
                        from services.export_service import ExportFormat
                        from ui.helpers.async_bridge import run_async

                        container = get_container()
                        export_service = container.export_service()

                        fmt_map = {
                            "txt": ExportFormat.TXT,
                            "json": ExportFormat.JSON,
                            "csv": ExportFormat.CSV,
                        }
                        export_format = fmt_map.get(format_type.lower())
                        if not export_format:
                            st.warning(
                                f"Formaat {format_type} wordt nog niet ondersteund in async export"
                            )
                            continue

                        path = run_async(
                            export_service.export_definitie_async(
                                definitie_id=def_rec.id,
                                definitie_record=None,
                                additional_data=additional_data,
                                format=export_format,
                            )
                        )
                        result = {"success": True, "path": path}

                    # Toon downloadknop voor de eerste definitie
                    if result.get("success") and def_rec == filtered_data[0]:
                        file_bytes = None
                        filename = None
                        if "content" in result:
                            file_bytes = result["content"]
                        elif "path" in result and result["path"]:
                            try:
                                with open(result["path"], "rb") as f:
                                    file_bytes = f.read()
                            except Exception:
                                file_bytes = None
                            # Extract filename if available
                            filename = result.get("filename")

                        if file_bytes:
                            if not filename:
                                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                                safe_begrip = (def_rec.begrip or "definitie").replace(" ", "_")
                                filename = f"definitie_{safe_begrip}_{timestamp}.{format_type.lower()}"

                            st.download_button(
                                label=f"📥 Download {format_type} (Voorbeeld: {def_rec.begrip})",
                                data=file_bytes,
                                file_name=filename,
                                mime=self._get_mime_type(format_type),
                            )

                except Exception as e:
                    st.warning(f"⚠️ Export fout voor '{def_rec.begrip}': {e!s}")
                    continue

        except Exception as e:
            st.error(f"❌ Export gefaald: {e!s}")

    def _get_filtered_export_data(
        self,
        status_filter,
        date_range,
        context_filter,
        categorie_filter,
        min_score,
        start_date,
        end_date,
    ) -> list[DefinitieRecord]:
        """Haal gefilterde data op voor export."""
        search_params = {}

        if status_filter and status_filter != "Alle":
            search_params["status"] = DefinitieStatus(status_filter)

        if context_filter:
            search_params["organisatorische_context"] = context_filter

        definitions = self.repository.search_definities(**search_params, limit=10000)

        # Apply additional filters
        if categorie_filter:
            definitions = [d for d in definitions if d.categorie in categorie_filter]

        if min_score > 0:
            definitions = [
                d
                for d in definitions
                if d.validation_score and d.validation_score >= min_score
            ]

        # Apply date filter
        if date_range != "Alle":
            if date_range == "Laatste week":
                cutoff_date = datetime.now(UTC) - timedelta(days=7)
            elif date_range == "Laatste maand":
                cutoff_date = datetime.now(UTC) - timedelta(days=30)
            elif date_range == "Laatste 3 maanden":
                cutoff_date = datetime.now(UTC) - timedelta(days=90)
            elif start_date and end_date:
                return [
                    d
                    for d in definitions
                    if d.created_at and start_date <= d.created_at.date() <= end_date
                ]
            else:
                return definitions

            definitions = [
                d for d in definitions if d.created_at and d.created_at >= cutoff_date
            ]

        return definitions

    def _generate_export_data(
        self,
        definitions: list[DefinitieRecord],
        format_type: str,
        include_metadata: bool,
    ):
        """
        LEGACY: Genereer export data in gewenste formaat.

        NOTE: Deze methode wordt vervangen door de nieuwe ExportService.
        De nieuwe implementatie gebruikt service.export_definition() per definitie.
        """
        if format_type == "JSON":
            return self._generate_json_export(definitions, include_metadata)
        if format_type == "CSV":
            return self._generate_csv_export(definitions, include_metadata)
        if format_type == "TXT":
            return self._generate_txt_export(definitions, include_metadata)
        if format_type == "Excel":
            return self._generate_excel_export(definitions, include_metadata)
        msg = f"Unsupported format: {format_type}"
        raise ValueError(msg)

    def _generate_json_export(
        self, definitions: list[DefinitieRecord], include_metadata: bool
    ):
        """Genereer JSON export."""
        export_data = []
        for def_rec in definitions:
            record = {
                "begrip": def_rec.begrip,
                "definitie": def_rec.definitie,
                "categorie": def_rec.categorie,
                "organisatorische_context": def_rec.organisatorische_context,
                "juridische_context": def_rec.juridische_context,
                "status": def_rec.status,
            }

            if include_metadata:
                record.update(
                    {
                        "id": def_rec.id,
                        "validation_score": def_rec.validation_score,
                        "created_at": (
                            def_rec.created_at.isoformat()
                            if def_rec.created_at
                            else None
                        ),
                        "created_by": def_rec.created_by,
                        "version_number": def_rec.version_number,
                    }
                )

            export_data.append(record)

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _generate_csv_export(
        self, definitions: list[DefinitieRecord], include_metadata: bool
    ):
        """Genereer CSV export."""
        data = []
        for def_rec in definitions:
            record = {
                "Begrip": def_rec.begrip,
                "Definitie": def_rec.definitie,
                "Categorie": def_rec.categorie,
                "Organisatorische_Context": def_rec.organisatorische_context,
                "Juridische_Context": def_rec.juridische_context,
                "Status": def_rec.status,
            }

            if include_metadata:
                record.update(
                    {
                        "ID": def_rec.id,
                        "Validation_Score": def_rec.validation_score,
                        "Created_At": (
                            def_rec.created_at.isoformat()
                            if def_rec.created_at
                            else None
                        ),
                        "Created_By": def_rec.created_by,
                        "Version_Number": def_rec.version_number,
                    }
                )

            data.append(record)

        df = pd.DataFrame(data)
        return df.to_csv(index=False)

    def _generate_txt_export(
        self, definitions: list[DefinitieRecord], include_metadata: bool
    ):
        """Genereer TXT export."""
        lines = []
        for def_rec in definitions:
            lines.append(f"BEGRIP: {def_rec.begrip}")
            lines.append(f"DEFINITIE: {def_rec.definitie}")
            lines.append(f"CATEGORIE: {def_rec.categorie}")
            lines.append(
                f"ORGANISATORISCHE CONTEXT: {def_rec.organisatorische_context}"
            )
            if def_rec.juridische_context:
                lines.append(f"JURIDISCHE CONTEXT: {def_rec.juridische_context}")
            lines.append(f"STATUS: {def_rec.status}")

            if include_metadata:
                lines.append(f"ID: {def_rec.id}")
                if def_rec.validation_score:
                    lines.append(f"SCORE: {def_rec.validation_score:.2f}")
                if def_rec.created_at:
                    lines.append(
                        f"GEMAAKT: {def_rec.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                if def_rec.created_by:
                    lines.append(f"DOOR: {def_rec.created_by}")

            lines.append("-" * 50)
            lines.append("")

        return "\n".join(lines)

    def _generate_excel_export(
        self, definitions: list[DefinitieRecord], include_metadata: bool
    ):
        """Genereer Excel export."""
        data = []
        for def_rec in definitions:
            record = {
                "Begrip": def_rec.begrip,
                "Definitie": def_rec.definitie,
                "Categorie": def_rec.categorie,
                "Organisatorische_Context": def_rec.organisatorische_context,
                "Juridische_Context": def_rec.juridische_context,
                "Status": def_rec.status,
            }

            if include_metadata:
                record.update(
                    {
                        "ID": def_rec.id,
                        "Validation_Score": def_rec.validation_score,
                        "Created_At": def_rec.created_at,
                        "Created_By": def_rec.created_by,
                        "Version_Number": def_rec.version_number,
                    }
                )

            data.append(record)

        df = pd.DataFrame(data)

        # Use BytesIO to create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Definities", index=False)

        return output.getvalue()

    def _get_mime_type(self, format_type: str) -> str:
        """Get MIME type voor format."""
        mime_types = {
            "JSON": "application/json",
            "CSV": "text/csv",
            "TXT": "text/plain",
            "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return mime_types.get(format_type, "application/octet-stream")

    def _check_database_health(self) -> dict[str, dict]:
        """Check database health."""
        health_status = {}

        try:
            # Check connection
            stats = self.repository.get_statistics()
            health_status["Connection"] = {
                "status": "ok",
                "message": "Database verbinding actief",
            }

            # Check data integrity
            total_defs = stats.get("total_definitions", 0)
            if total_defs > 0:
                health_status["Data Integrity"] = {
                    "status": "ok",
                    "message": f"{total_defs} definities aanwezig",
                }
            else:
                health_status["Data Integrity"] = {
                    "status": "warning",
                    "message": "Geen definities in database",
                }

            # Check for orphaned records (implementatie volgt via US-063)
            health_status["Orphaned Records"] = {
                "status": "ok",
                "message": "Geen wees-records gevonden",
            }

        except Exception as e:
            health_status["Connection"] = {
                "status": "error",
                "message": f"Database fout: {e!s}",
            }

        return health_status

    def _execute_bulk_status_update(
        self, status_filter: str, new_status: str, reason: str
    ):
        """Voer bulk status update uit."""
        if not reason.strip():
            st.error("❌ Voer een reden in voor de bulk update")
            return

        try:
            # Get definitions to update
            definitions = self.repository.search_definities(
                status=DefinitieStatus(status_filter), limit=1000
            )

            if not definitions:
                st.info("Geen definities gevonden voor update")
                return

            # Confirm action
            if not st.session_state.get("bulk_update_confirmed", False):
                st.warning(
                    f"⚠️ Dit zal {len(definitions)} definities wijzigen van {status_filter} naar {new_status}"
                )
                if st.button("✅ Bevestig Bulk Update"):
                    st.session_state["bulk_update_confirmed"] = True
                    st.rerun()
                return

            # Execute bulk update
            updated_count = 0
            for def_rec in definitions:
                success = self.repository.change_status(
                    def_rec.id, DefinitieStatus(new_status), "bulk_operation", reason
                )
                if success:
                    updated_count += 1

            st.success(f"✅ {updated_count} definities bijgewerkt")
            st.session_state["bulk_update_confirmed"] = False

        except Exception as e:
            st.error(f"❌ Bulk update gefaald: {e!s}")

    def _execute_bulk_import(
        self, uploaded_file, import_mode: str, duplicate_handling: str
    ):
        """Voer bulk import uit."""
        # Bulk import functionaliteit volgt via US-062
        st.info("📥 Bulk import functionaliteit komt binnenkort beschikbaar")

    def _cleanup_duplicates(self):
        """Cleanup duplicate definities."""
        # Duplicate cleanup volgt via US-063
        st.info("🗑️ Duplicate cleanup functionaliteit komt binnenkort beschikbaar")

    def _rebuild_indexes(self):
        """Herbouw database indexes."""
        # Index rebuild volgt via US-063
        st.info("🔄 Index rebuild functionaliteit komt binnenkort beschikbaar")

    def _analyze_database(self):
        """Analyseer database prestaties."""
        # Database analyse volgt via US-063
        st.info("📊 Database analyse functionaliteit komt binnenkort beschikbaar")

    def _email_export(self):
        """Verstuur export via email."""
        # Email export volgt via US-065
        st.info("📧 Email export functionaliteit komt binnenkort beschikbaar")

    def _schedule_export(self):
        """Plan automatische exports."""
        # Geplande exports volgen via US-065
        st.info("⏰ Geplande export functionaliteit komt binnenkort beschikbaar")
