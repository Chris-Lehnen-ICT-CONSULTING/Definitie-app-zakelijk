"""Renderer voor RAG Management pagina (DEF-365).

Sidebar: collection beheer (list, create, delete).
Main panel: document beheer (list, upload, text input, delete).
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from services.rag.constants import (
    COLLECTION_TYPE_TO_BRON_TYPE,
    COLLECTION_TYPES,
    RECHTSGEBIEDEN,
)
from services.rag.rag_management_service import RAGManagementService
from services.rag.rag_service import RAGService
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class RAGManagementRenderer:
    """Renderer voor het RAG management scherm."""

    def __init__(
        self,
        management_service: RAGManagementService,
        rag_service: RAGService,
    ) -> None:
        self._mgmt = management_service
        self._rag = rag_service

    # ── Sidebar ─────────────────────────────────────────────

    def render_sidebar(self) -> int | None:
        """Render sidebar met collection beheer. Return geselecteerde collection_id."""
        with st.sidebar:
            st.markdown("## \U0001f4da Collections")

            collections = self._mgmt.list_collections()

            self._render_create_collection_form()

            if not collections:
                st.info("Nog geen collections. Maak er een aan.")
                return None

            st.markdown("---")
            selected = self._render_collection_list(collections)

            if selected is not None:
                self._render_delete_collection_button(selected, collections)

            return selected

    def _render_collection_list(self, collections: list[dict]) -> int | None:
        """Render lijst van collections. Return geselecteerde collection_id."""
        options = {
            c[
                "id"
            ]: f"{c['type_icon']} {c['name']} ({c['document_count']} docs, {c['chunk_count']} chunks)"
            for c in collections
        }

        prev_selected = SessionStateManager.get_value("rag_selected_collection", None)
        default_idx = 0
        if prev_selected is not None:
            ids = list(options.keys())
            if prev_selected in ids:
                default_idx = ids.index(prev_selected)

        selected_id = st.radio(
            "Selecteer collection",
            options=list(options.keys()),
            format_func=lambda x: options[x],
            index=default_idx,
            key="rag_collection_radio",
            label_visibility="collapsed",
        )

        SessionStateManager.set_value("rag_selected_collection", selected_id)
        return selected_id

    def _render_create_collection_form(self) -> None:
        """Render formulier voor nieuwe collection."""
        with st.expander("\u2795 Nieuwe collection", expanded=False):
            st.text_input(
                "Naam",
                key="rag_new_collection_name",
                placeholder="bijv. Wetboek van Strafrecht",
            )

            type_options = [ct.key for ct in COLLECTION_TYPES]
            type_labels = [f"{ct.icon} {ct.label}" for ct in COLLECTION_TYPES]
            st.selectbox(
                "Type",
                options=type_options,
                format_func=lambda x: type_labels[type_options.index(x)],
                key="rag_new_collection_type",
            )

            rg_keys = [""] + list(RECHTSGEBIEDEN.keys())
            st.selectbox(
                "Rechtsgebied (optioneel)",
                options=rg_keys,
                format_func=lambda x: (
                    RECHTSGEBIEDEN.get(x, "— geen —") if x else "— geen —"
                ),
                key="rag_new_collection_rg",
            )

            if st.button("Collection aanmaken", type="primary", key="rag_create_btn"):
                name = SessionStateManager.get_value("rag_new_collection_name", "")
                if not name or not name.strip():
                    st.error("Vul een naam in.")
                    return
                col_type = SessionStateManager.get_value(
                    "rag_new_collection_type", "vrij"
                )
                rg = SessionStateManager.get_value("rag_new_collection_rg", "") or None

                try:
                    cid = self._mgmt.create_collection(
                        name=name.strip(),
                        collection_type=col_type,
                        rechtsgebied=rg,
                    )
                    st.success(f"Collection aangemaakt (id={cid})")
                    SessionStateManager.set_value("rag_selected_collection", cid)
                    st.rerun()
                except Exception as e:
                    st.error(f"Aanmaken mislukt: {e}")

    def _render_delete_collection_button(
        self, selected_id: int, collections: list[dict]
    ) -> None:
        """Render verwijder-knop met dubbel-klik bevestiging."""
        st.markdown("---")
        confirm_key = f"rag_confirm_del_coll_{selected_id}"

        if st.button(
            "\U0001f5d1\ufe0f Verwijder collection",
            key=f"rag_del_coll_{selected_id}",
        ):
            if SessionStateManager.get_value(confirm_key, False):
                try:
                    self._mgmt.delete_collection(selected_id)
                    SessionStateManager.set_value(confirm_key, False)
                    SessionStateManager.set_value("rag_selected_collection", None)
                    st.success("Collection verwijderd")
                    st.rerun()
                except Exception as e:
                    st.error(f"Verwijderen mislukt: {e}")
            else:
                SessionStateManager.set_value(confirm_key, True)
                st.warning("Klik nogmaals om te bevestigen")

    # ── Main panel ──────────────────────────────────────────

    def render_document_panel(self, collection_id: int) -> None:
        """Render document management voor geselecteerde collection."""
        collections = self._mgmt.list_collections()
        collection = next((c for c in collections if c["id"] == collection_id), None)
        if collection is None:
            st.error("Collection niet gevonden")
            return

        st.markdown(f"### {collection['type_icon']} {collection['name']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documenten", collection["document_count"])
        with col2:
            st.metric("Chunks", collection["chunk_count"])
        with col3:
            rg = collection.get("rechtsgebied") or "—"
            st.metric("Rechtsgebied", rg)

        st.markdown("---")

        # Tabs voor upload vs tekst invoer
        tab_upload, tab_text = st.tabs(
            ["\U0001f4c2 Bestand uploaden", "\U0001f4dd Tekst invoeren"]
        )

        with tab_upload:
            self._render_document_upload(collection_id, collection)

        with tab_text:
            self._render_text_input(collection_id, collection)

        st.markdown("---")

        # Document tabel
        documents = self._mgmt.list_documents(collection_id)
        if documents:
            self._render_document_table(documents)
        else:
            st.info("Nog geen documenten in deze collection.")

    def _render_document_table(self, documents: list[dict]) -> None:
        """Render overzichtstabel van documenten."""
        st.markdown("#### \U0001f4c4 Documenten")

        for doc in documents:
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(
                    f"{doc.get('file_type', '?')} · "
                    f"{doc.get('chunk_count', 0)} chunks · "
                    f"{doc.get('rechtsgebied') or '—'}"
                )
            with col2:
                st.caption(doc.get("processed_at", ""))
            with col3:
                self._render_delete_document_button(doc)

    def _render_document_upload(self, collection_id: int, collection: dict) -> None:
        """Render file uploader + ingest."""
        uploaded = st.file_uploader(
            "Upload document",
            type=["txt", "pdf", "docx", "doc", "md", "csv", "json", "html", "rtf"],
            key=f"rag_upload_{collection_id}",
            help="Ondersteunde formaten: TXT, PDF, Word, Markdown, CSV, JSON, HTML, RTF",
        )

        if uploaded and st.button(
            "Indexeer document", type="primary", key=f"rag_ingest_{collection_id}"
        ):
            self._ingest_uploaded_file(collection_id, uploaded, collection)

    def _ingest_uploaded_file(
        self, collection_id: int, uploaded, collection: dict
    ) -> None:
        """Verwerk en ingest een geüpload bestand."""
        filename = uploaded.name

        if self._mgmt.check_duplicate_document(collection_id, filename):
            st.warning(f"Document '{filename}' bestaat al in deze collection.")
            return

        # DEF-379 Bevinding 1+2: extraheer rechtsgebied en bron_type uit collection
        rechtsgebied = collection.get("rechtsgebied") or None
        bron_type = COLLECTION_TYPE_TO_BRON_TYPE.get(collection.get("type_key", "vrij"))

        with st.spinner(f"Verwerken van {filename}..."):
            try:
                from document_processing.document_extractor import (
                    extract_text_from_file,
                )

                file_content = uploaded.read()
                tekst = extract_text_from_file(file_content, filename, uploaded.type)
                if not tekst or not tekst.strip():
                    st.error("Geen tekst geëxtraheerd uit het document.")
                    return

                # Sla bestand op in uploads dir
                saved_path = self._save_upload(file_content, filename)

                self._rag.ingest_document(
                    tekst=tekst,
                    collection_id=collection_id,
                    filename=filename,
                    file_type=uploaded.type or "application/octet-stream",
                    file_path=str(saved_path) if saved_path else None,
                    rechtsgebied=rechtsgebied,
                    bron_type=bron_type,
                )
                st.success(f"'{filename}' geïndexeerd")
                st.rerun()
            except Exception as e:
                st.error(f"Indexering mislukt: {e}")
                logger.error("Ingest mislukt voor %s: %s", filename, e, exc_info=True)

    def _render_text_input(self, collection_id: int, collection: dict) -> None:
        """Render tekstveld + ingest."""
        st.text_area(
            "Plak tekst",
            key=f"rag_text_input_{collection_id}",
            height=200,
            placeholder="Plak hier de tekst die je wilt indexeren...",
        )
        st.text_input(
            "Documentnaam",
            key=f"rag_text_name_{collection_id}",
            placeholder="bijv. notitie-strafrecht.txt",
        )

        if st.button(
            "Tekst indexeren",
            type="primary",
            key=f"rag_text_ingest_{collection_id}",
        ):
            tekst = SessionStateManager.get_value(f"rag_text_input_{collection_id}", "")
            name = SessionStateManager.get_value(f"rag_text_name_{collection_id}", "")
            if not tekst or not tekst.strip():
                st.error("Voer tekst in.")
                return
            if not name or not name.strip():
                st.error("Voer een documentnaam in.")
                return

            if self._mgmt.check_duplicate_document(collection_id, name.strip()):
                st.warning(f"Document '{name.strip()}' bestaat al in deze collection.")
                return

            # DEF-379 Bevinding 1+2: extraheer rechtsgebied en bron_type uit collection
            rechtsgebied = collection.get("rechtsgebied") or None
            bron_type = COLLECTION_TYPE_TO_BRON_TYPE.get(
                collection.get("type_key", "vrij")
            )

            with st.spinner("Tekst indexeren..."):
                try:
                    self._rag.ingest_document(
                        tekst=tekst,
                        collection_id=collection_id,
                        filename=name.strip(),
                        file_type="text/plain",
                        rechtsgebied=rechtsgebied,
                        bron_type=bron_type,
                    )
                    st.success(f"'{name.strip()}' geïndexeerd")
                    st.rerun()
                except Exception as e:
                    st.error(f"Indexering mislukt: {e}")

    def _render_delete_document_button(self, doc: dict) -> None:
        """Render verwijder-knop met dubbel-klik bevestiging."""
        doc_id = doc["id"]
        confirm_key = f"rag_confirm_del_doc_{doc_id}"

        if st.button(
            "\U0001f5d1\ufe0f",
            key=f"rag_del_doc_{doc_id}",
            help=f"Verwijder {doc['filename']}",
        ):
            if SessionStateManager.get_value(confirm_key, False):
                try:
                    self._mgmt.delete_document(doc_id)
                    SessionStateManager.set_value(confirm_key, False)
                    st.success("Document verwijderd")
                    st.rerun()
                except Exception as e:
                    st.error(f"Verwijderen mislukt: {e}")
            else:
                SessionStateManager.set_value(confirm_key, True)
                st.warning("Klik nogmaals")

    @staticmethod
    def _save_upload(file_content: bytes, filename: str) -> Path | None:
        """Sla upload op in data/uploads/ met timestamp prefix."""
        import re
        from datetime import datetime

        uploads_dir = Path("data/uploads")
        try:
            uploads_dir.mkdir(parents=True, exist_ok=True)
            clean = re.sub(r"[^\w.\-]", "_", Path(filename).name) or "unnamed"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = uploads_dir / f"{ts}_{clean}"
            dest.write_bytes(file_content)
            return dest
        except Exception as e:
            logger.warning("Upload opslaan mislukt: %s", e)
            return None
