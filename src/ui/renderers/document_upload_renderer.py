"""Renderer voor document upload en beheer sectie.

Geextraheerd uit TabbedInterface (DEF-141). Bevat alle UI-logica
voor het uploaden, verwerken en beheren van documenten die als
context dienen voor definitie generatie.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from document_processing.document_extractor import supported_file_types
from document_processing.document_processor import get_document_processor
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


UPLOADS_DIR = Path("data/uploads")


def _sanitize_filename(name: str) -> str:
    """Verwijder path-traversal en onveilige karakters uit bestandsnaam."""
    # Strip directory componenten (path traversal)
    name = Path(name).name
    # Alleen alfanumeriek, punt, streepje, underscore
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "unnamed"


def _save_uploaded_file(uploaded_file) -> Path | None:
    """Sla geüpload bestand op in data/uploads/ met timestamp prefix."""
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = _sanitize_filename(uploaded_file.name)
        safe_name = f"{timestamp}_{clean_name}"
        dest = UPLOADS_DIR / safe_name
        dest.write_bytes(uploaded_file.getvalue())
        return dest
    except Exception as e:
        logger.warning("Bestand opslaan mislukt voor %s: %s", uploaded_file.name, e)
        return None


def _find_uploaded_file(filename: str) -> Path | None:
    """Zoek het meest recente upload-bestand met matchende naam."""
    if not UPLOADS_DIR.exists():
        return None
    # Bestanden zijn {timestamp}_{gesanitizede_naam} — zoek op suffix
    clean_name = _sanitize_filename(filename)
    matches = sorted(
        (p for p in UPLOADS_DIR.iterdir() if p.name.endswith(f"_{clean_name}")),
        reverse=True,  # Nieuwste eerst (timestamp prefix)
    )
    return matches[0] if matches else None


class DocumentUploadRenderer:
    """Render document upload, processing en beheer UI."""

    def render_document_upload_section(self):
        """Render document upload sectie voor context enrichment."""
        with st.expander("📄 Document Upload voor Context Verrijking", expanded=False):
            st.markdown(
                "Upload documenten die relevante context bevatten "
                "voor de definitie generatie."
            )
            st.markdown(
                "- i Technisch: [Extractie & flow]"
                "(docs/technisch/document_processing.md)"
            )
            st.markdown(
                "- 🧑\u200d💻 Dev how-to: [document_context gebruiken]"
                "(docs/handleidingen/ontwikkelaars/"
                "document-context-gebruik.md)"
            )

            # File uploader
            uploaded_files = st.file_uploader(
                "Selecteer documenten",
                type=[
                    "txt",
                    "pdf",
                    "docx",
                    "doc",
                    "md",
                    "csv",
                    "json",
                    "html",
                    "rtf",
                ],
                accept_multiple_files=True,
                help="Ondersteunde formaten: TXT, PDF, Word, "
                "Markdown, CSV, JSON, HTML, RTF",
            )

            # Toon ondersteunde bestandstypen
            if st.checkbox("i️ Toon ondersteunde bestandstypen", value=False):
                supported_types = supported_file_types()
                st.markdown("**Ondersteunde bestandstypen:**")
                for _mime_type, description in supported_types.items():
                    st.write(f"• {description}")

            # Process uploaded files
            if uploaded_files:
                self._process_uploaded_files(uploaded_files)

            # Toon bestaande documenten
            self.render_uploaded_documents_list()

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
                    file_content, uploaded_file.name, uploaded_file.type
                )

                # Sla origineel bestand op in data/uploads/
                _save_uploaded_file(uploaded_file)

                processed_docs.append(processed_doc)

            except Exception as e:
                st.error(f"Fout bij verwerken van {uploaded_file.name}: {e!s}")

        progress_bar.empty()
        status_text.empty()

        # Toon resultaten
        if processed_docs:
            st.success(f"✅ {len(processed_docs)} document(en) verwerkt!")

            for doc in processed_docs:
                if doc.processing_status == "success":
                    st.success(
                        f"✅ {doc.filename}: {doc.text_length} "
                        "karakters geëxtraheerd"
                    )
                else:
                    st.error(f"❌ {doc.filename}: {doc.error_message}")

            # Update session state
            SessionStateManager.set_value("documents_updated", True)

    def render_uploaded_documents_list(self):
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
                label = (
                    f"{doc.filename} ({doc.text_length:,} chars, "
                    f"{len(doc.keywords)} keywords)"
                )
                doc_options.append(doc.id)
                doc_labels.append(label)

        if doc_options:
            selected_docs = st.multiselect(
                "Selecteer documenten voor context verrijking",
                options=doc_options,
                format_func=lambda x: next(
                    label
                    for doc_id, label in zip(doc_options, doc_labels, strict=False)
                    if doc_id == x
                ),
                default=SessionStateManager.get_value("selected_documents", []),
                help="Geselecteerde documenten worden gebruikt "
                "voor context en bronvermelding",
            )

            SessionStateManager.set_value("selected_documents", selected_docs)

            # Toon document details
            if selected_docs:
                st.markdown(
                    f"#### 📋 Details van {len(selected_docs)} "
                    "geselecteerde document(en)"
                )
                aggregated = processor.get_aggregated_context(selected_docs)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Documenten", aggregated["document_count"])
                    st.metric(
                        "Totale tekst",
                        f"{aggregated['total_text_length']:,} chars",
                    )

                with col2:
                    st.metric(
                        "Keywords",
                        len(aggregated["aggregated_keywords"]),
                    )
                    st.metric(
                        "Concepten",
                        len(aggregated["aggregated_concepts"]),
                    )

                # Toon keywords en concepten
                if aggregated["aggregated_keywords"]:
                    st.markdown("**Top Keywords:**")
                    st.write(", ".join(aggregated["aggregated_keywords"][:10]))

                if aggregated["aggregated_concepts"]:
                    st.markdown("**Key Concepten:**")
                    st.write(", ".join(aggregated["aggregated_concepts"][:5]))

                if aggregated["aggregated_legal_refs"]:
                    st.markdown("**Juridische Verwijzingen:**")
                    st.write(", ".join(aggregated["aggregated_legal_refs"][:5]))

            # DEF-271: RAG ingest knop voor geselecteerde documenten
            if selected_docs:
                # DEF-361: Rechtsgebied selectie voor metadata enrichment
                st.selectbox(
                    "Rechtsgebied",
                    options=[
                        "",
                        "strafrecht",
                        "civiel recht",
                        "bestuursrecht",
                        "staatsrecht",
                        "belastingrecht",
                    ],
                    key="rag_rechtsgebied",
                    help="Selecteer het rechtsgebied voor betere RAG retrieval",
                )

                if st.button(
                    "Indexeer voor RAG",
                    key="rag_ingest_selected",
                    help="Indexeer geselecteerde documenten voor RAG context retrieval",
                ):
                    try:
                        from utils.container_manager import get_cached_container

                        container = get_cached_container()
                        rag_svc = container.rag_service
                        coll_id = rag_svc._ensure_collection("user_documents")

                        rechtsgebied = (
                            SessionStateManager.get_value("rag_rechtsgebied", "")
                            or None
                        )
                        ingested = 0
                        for doc_id in selected_docs:
                            doc = next(
                                (
                                    d
                                    for d in documents
                                    if d.id == doc_id
                                    and d.processing_status == "success"
                                ),
                                None,
                            )
                            if doc and doc.extracted_text:
                                # Zoek opgeslagen bestand in uploads dir
                                stored_path = _find_uploaded_file(doc.filename)
                                rag_svc.ingest_document(
                                    tekst=doc.extracted_text,
                                    collection_id=coll_id,
                                    filename=doc.filename,
                                    rechtsgebied=rechtsgebied,
                                    file_path=str(stored_path) if stored_path else None,
                                )
                                ingested += 1

                        if ingested > 0:
                            st.success(f"{ingested} document(en) geindexeerd voor RAG")
                        else:
                            st.warning(
                                "Geen documenten met tekst gevonden om te indexeren"
                            )
                    except Exception as e:
                        st.error(f"Indexering mislukt: {e}")

        # Document management - buiten expander om nesting te voorkomen
        if documents and st.checkbox("🗂️ Toon document beheer", value=False):
            st.markdown("#### 🗂️ Document Beheer")
            for doc in documents:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    status_emoji = "✅" if doc.processing_status == "success" else "❌"
                    st.write(f"{status_emoji} {doc.filename}")
                    if doc.processing_status == "success":
                        st.caption(
                            f"{doc.text_length:,} chars, "
                            f"{len(doc.keywords)} keywords"
                        )
                    else:
                        st.caption(f"Error: {doc.error_message}")

                with col2:
                    upload_date = doc.uploaded_at.strftime("%d-%m %H:%M")
                    st.caption(upload_date)

                with col3:
                    if st.button(
                        "🗑️",
                        key=f"delete_{doc.id}",
                        help=f"Verwijder {doc.filename}",
                    ):
                        processor.remove_document(doc.id)
                        st.rerun()
