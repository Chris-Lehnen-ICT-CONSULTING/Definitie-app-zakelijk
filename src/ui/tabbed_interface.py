"""Tabbed Interface voor DefinitieAgent - Nieuwe UI architectuur.
Implementeert de requirements uit Project Requirements Document.

Deze module bevat de hoofdcontroller voor de gebruikersinterface,
met ondersteuning voor meerdere tabs en complete workflow beheer.
"""

import asyncio  # Used by _render_category_preview delegate + test patching target
import logging  # Logging faciliteiten voor debug en monitoring
import sqlite3  # Voor specifieke exception handling in RAG selector
from datetime import (
    UTC,
    datetime,  # Datum en tijd functionaliteit
)
from typing import Any, cast  # Type hints voor betere code documentatie

import streamlit as st  # Streamlit web interface framework

from integration.definitie_checker import (  # Definitie integratie controle
    DefinitieChecker,
)

# Nieuwe services imports
from services import get_definition_service
from ui.components.definition_edit_tab import (
    DefinitionEditTab,  # Edit interface voor definities
)
from ui.components.definition_generator_tab import (
    DefinitionGeneratorTab,  # Hoofdtab voor definitie generatie
)

# Importeer alle UI tab componenten voor de verschillende functionaliteiten
from ui.components.enhanced_context_manager_selector import (
    EnhancedContextManagerSelector as ContextSelector,
)

# Context selectie component via ContextManager
from ui.components.expert_review_tab import (
    ExpertReviewTab,  # Expert review en validatie tab
)

# Geconsolideerde import/export/beheer tab (vervangt Export en Management tabs)
from ui.components.tabs.import_export_beheer import ImportExportBeheerTab

# DEF-141: Extracted handlers and renderers
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.renderers.document_upload_renderer import DocumentUploadRenderer
from ui.renderers.global_context_renderer import GlobalContextRenderer

# Importeer core services en utilities
from ui.session_state import (
    SessionStateManager,  # Sessie state management voor UI persistentie
)

# Module-level constants
UTC = UTC  # Voor Python 3.10 compatibility

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class TabbedInterface:
    """Main tabbed interface controller voor DefinitieAgent."""

    def __init__(self) -> None:
        """Initialiseer tabbed interface met alle benodigde services."""
        # US-202 FIX: Get container via session state singleton to prevent duplicate initialization
        from ui.cached_services import get_cached_service_container

        self.container = get_cached_service_container()

        # DEF-175: Lazy import to avoid database layer dependency at module level
        from database.definitie_repository import get_definitie_repository

        self.repository = (
            get_definitie_repository()
        )  # Haal database repository instantie op

        # Gebruik nieuwe service factory voor definitie service
        try:
            self.definition_service = get_definition_service()
        except Exception as e:
            # Tijdens tests of in omgevingen zonder API key mag initialisatie niet falen
            logger.warning(
                f"Definition service niet beschikbaar ({type(e).__name__}: {e!s}); val terug op dummy service"
            )

            class _DummyService:
                def get_service_info(self) -> dict:
                    return {
                        "service_mode": "dummy",
                        "architecture": "none",
                        "version": "test",
                    }

                async def generate_definition(
                    self, begrip: str, context_dict: dict[str, Any], **kwargs: Any
                ) -> dict[str, Any]:
                    # Uniform V2 response vorm; UI kan hiermee omgaan
                    return {
                        "success": False,
                        "definitie_origineel": "",
                        "definitie_gecorrigeerd": "",
                        "final_score": 0.0,
                        "validation_details": {
                            "overall_score": 0.0,
                            "is_acceptable": False,
                            "violations": [],
                            "passed_rules": [],
                        },
                        "voorbeelden": {},
                        "metadata": {"error": "Definition service unavailable"},
                        "sources": [],
                        "error_message": "Definition service unavailable",
                    }

            self.definition_service = _DummyService()

        # Maak DefinitieChecker met de service
        self.checker = DefinitieChecker(self.repository)
        # Update checker om nieuwe service te gebruiken indien beschikbaar
        if hasattr(self.definition_service, "get_service_info"):
            # V2 service heeft get_service_info methode
            self.checker._definition_service = self.definition_service

        self.context_selector = (
            ContextSelector()
        )  # Initialiseer context selector component

        # DEF-141: Extracted handlers and renderers
        self.document_upload_renderer = DocumentUploadRenderer()
        self.global_context_renderer = GlobalContextRenderer(self.context_selector)
        self.generation_handler = DefinitionGenerationHandler(
            checker=self.checker,
            definition_service=self.definition_service,
            repository=self.repository,
        )

        # Initialiseer alle tab componenten met repository referentie
        self.definition_tab = DefinitionGeneratorTab(self.checker)

        # Koppel validatie service aan Edit-tab (ModularValidation via Orchestrator V2)
        try:
            # Use cached container instead of creating new one
            validation_service = (
                self.container.orchestrator()
            )  # ValidationOrchestratorV2
        except Exception as e:
            logger.warning(
                f"Validatie service niet beschikbaar ({type(e).__name__}: {e!s}); Edit-tab zonder validator"
            )
            validation_service = None

        self.edit_tab = DefinitionEditTab(
            validation_service=validation_service
        )  # Edit tab with validator
        self.expert_tab = ExpertReviewTab(self.repository)
        # Nieuwe geconsolideerde tab vervangt Export en Management tabs
        self.import_export_beheer_tab = ImportExportBeheerTab(self.repository)

        # Tab configuration
        self.tab_config = {
            "generator": {
                "title": "🚀 Definitie Generatie",
                "icon": "🚀",
                "description": "Genereer nieuwe definities met AI-ondersteuning",
            },
            "edit": {
                "title": "✏️ Bewerk",
                "icon": "✏️",
                "description": "Bewerk definities met versiegeschiedenis en auto-save",
            },
            "expert": {
                "title": "👨‍💼 Expert Review",
                "icon": "👨‍💼",
                "description": "Review en goedkeuring van definities",
            },
            "import_export_beheer": {
                "title": "📦 Import, Export & Beheer",
                "icon": "📦",
                "description": "Geconsolideerde import, export en database beheer",
            },
        }

    def render(self) -> None:
        """Render de volledige tabbed interface."""
        # AI Provider sidebar (provider selection + API key)
        from ui.components.ai_provider_sidebar import render_ai_provider_sidebar

        render_ai_provider_sidebar()

        # App header
        self._render_header()

        # Global context selector (boven tabs)
        self._render_global_context()

        # Check of er een auto-generatie trigger is gezet
        if SessionStateManager.get_value("trigger_auto_generation", False):
            # Wis de trigger flag
            SessionStateManager.clear_value("trigger_auto_generation")
            # Haal begrip en context op
            begrip = SessionStateManager.get_value("begrip", "")
            context_data = SessionStateManager.get_value("global_context", {})
            if begrip.strip():
                # Trigger generatie
                self._handle_definition_generation(begrip, context_data)

        # Main tabs
        self._render_main_tabs()

        # Footer met systeem informatie
        self._render_footer()

    # ------- Delegates to DefinitionGenerationHandler (DEF-141) -------

    def _handle_definition_generation(
        self, begrip: str, context_data: dict[str, Any]
    ) -> None:
        """Delegate (backward compat). Passes module-level st/SM for test patching."""
        self.generation_handler.handle_definition_generation(
            begrip, context_data, _st=st, _sm=SessionStateManager
        )

    def _handle_duplicate_check(
        self, begrip: str, context_data: dict[str, Any]
    ) -> None:
        """Delegate (backward compat). Passes module-level st/SM for test patching."""
        self.generation_handler.handle_duplicate_check(
            begrip, context_data, _st=st, _sm=SessionStateManager
        )

    def _get_document_context(self) -> dict[str, Any] | None:
        """Delegate (backward compat)."""
        # DEF-439: generation_handler-import resolveert naar Any -> cast op de grens
        return cast(
            "dict[str, Any] | None",
            self.generation_handler._get_document_context(_sm=SessionStateManager),
        )

    def _build_document_context_summary(self, aggregated: dict[str, Any]) -> str:
        """Delegate (backward compat)."""
        # DEF-439: generation_handler-import resolveert naar Any -> cast op de grens
        return cast(
            str, self.generation_handler._build_document_context_summary(aggregated)
        )

    def _build_document_snippets(
        self,
        begrip: str,
        selected_doc_ids: list[str],
        max_snippets_total: int | None = None,
        per_doc_max: int = 4,
        snippet_window: int = 280,
    ) -> list[dict[str, Any]]:
        """Delegate (backward compat)."""
        # DEF-439: generation_handler-import resolveert naar Any -> cast op de grens
        return cast(
            "list[dict[str, Any]]",
            self.generation_handler._build_document_snippets(
                begrip=begrip,
                selected_doc_ids=selected_doc_ids,
                max_snippets_total=max_snippets_total,
                per_doc_max=per_doc_max,
                snippet_window=snippet_window,
            ),
        )

    # ------- Rendering methods -------

    # ------- Delegates to GlobalContextRenderer (DEF-141) -------

    async def _determine_ontological_category(
        self, begrip: str, org_context: Any, jur_context: Any
    ) -> tuple[Any, Any, Any]:
        """Delegate (backward compat)."""
        # DEF-439: renderer-import resolveert naar Any -> cast op de grens
        return cast(
            "tuple[Any, Any, Any]",
            await self.global_context_renderer.determine_ontological_category(
                begrip, org_context, jur_context
            ),
        )

    def _render_category_preview(self) -> None:
        """Delegate (backward compat). Passes module-level refs for test patching."""
        self.global_context_renderer.render_category_preview(
            _st=st,
            _sm=SessionStateManager,
            _asyncio_run=asyncio.run,
            _determine_fn=self._determine_ontological_category,
        )

    def _render_header(self) -> None:
        """Render applicatie header."""

        # Header met logo en titel
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(
                """
                <div style="text-align: center;">
                    <h1>🧠 DefinitieAgent 2.0</h1>
                    <p style="font-size: 18px; color: #666;">
                        AI-ondersteunde definitie generatie en kwaliteitscontrole
                    </p>
                </div>
            """,
                unsafe_allow_html=True,
            )

        # Status indicator
        with col3:
            self._render_status_indicator()

    def _render_status_indicator(self) -> None:
        """Render systeem status indicator."""
        # Simple health check
        try:
            stats = self.repository.get_statistics()
            total_definitions = stats.get("total_definities", 0)

            st.success(
                f"✅ Systeem Online\\n{total_definitions} definities beschikbaar"
            )
        except Exception as e:
            st.error(f"❌ Systeem Issue\\n{str(e)[:50]}...")

    def _render_global_context(self) -> None:
        """Render globale context selector (delegeert naar GlobalContextRenderer)."""
        gcr = self.global_context_renderer

        # Begrip invoer
        begrip = gcr.render_begrip_input()

        # Document upload sectie
        self._render_document_upload_section()

        # Context selector met fallback
        context_data = gcr.render_context_selector()

        # Metadata velden
        st.markdown("### 📝 Metadata")
        try:
            gcr.render_metadata_fields()
            st.success("✅ Metadata velden succesvol geladen")
        except Exception as e:
            logger.error(f"Metadata fields crashed: {e}", exc_info=True)
            st.error(f"❌ Metadata velden fout: {type(e).__name__}: {e!s}")

        # DEF-36: Toon category preview VOOR generatie button
        try:
            self._render_category_preview()
        except Exception as e:
            logger.error(f"Category preview crashed: {e}", exc_info=True)
            st.error(f"❌ Category preview fout: {type(e).__name__}: {e!s}")

        # Genereer definitie knop direct na context
        st.markdown("---")
        try:
            self._render_quick_generate_button(begrip, context_data)
            st.success("✅ Quick generate button succesvol geladen")
        except Exception as e:
            logger.error(f"Quick generate button crashed: {e}", exc_info=True)
            st.error(f"❌ Quick generate button fout: {type(e).__name__}: {e!s}")

    def _render_simplified_context_selector(self) -> dict[str, Any]:
        """Delegate (backward compat)."""
        # DEF-439: renderer-import resolveert naar Any -> cast op de grens
        return cast(
            "dict[str, Any]",
            self.global_context_renderer.render_simplified_context_selector(),
        )

    def _render_metadata_fields(self) -> None:
        """Delegate (backward compat)."""
        self.global_context_renderer.render_metadata_fields()

    def _render_context_summary(self, context_data: dict[str, Any]) -> None:
        """Delegate (backward compat)."""
        self.global_context_renderer.render_context_summary(context_data)

    @staticmethod
    @st.cache_data(ttl=30)
    def _load_rag_collections() -> list[dict[str, Any]]:
        """Laad RAG collections met 30s cache (review fix: voorkom N+1 bij elke rerun)."""
        from services.container import get_container

        container = get_container()
        # DEF-439: services-import resolveert naar Any -> cast op de grens
        return cast(
            "list[dict[str, Any]]",
            container.rag_management_service.list_collections(),
        )

    def _render_rag_collection_selector(self) -> None:
        """DEF-366: Render RAG collection selector voor definitie-generatie."""
        try:
            collections = self._load_rag_collections()

            if not collections:
                return

            with st.expander("🔎 RAG Collections", expanded=False):
                options = {
                    c["id"]: f"{c['type_icon']} {c['name']} ({c['chunk_count']} chunks)"
                    for c in collections
                }
                all_ids = list(options.keys())

                prev = SessionStateManager.get_value(
                    "rag_selected_collection_ids", None
                )

                selected = st.multiselect(
                    "Zoek in collections",
                    options=all_ids,
                    default=prev if prev else all_ids,
                    format_func=lambda x: options.get(x, str(x)),
                    key="rag_collection_multiselect",
                    help="Selecteer in welke RAG collections gezocht wordt bij generatie. Standaard: alle.",
                )

                SessionStateManager.set_value(
                    "rag_selected_collection_ids", selected or None
                )
        except (ImportError, sqlite3.Error) as e:
            logger.warning("RAG collection selector niet beschikbaar: %s", e)
        except Exception as e:
            logger.debug("RAG collection selector skipped: %s", e)

    def _render_quick_generate_button(
        self, begrip: str, context_data: dict[str, Any]
    ) -> None:
        """Render snelle genereer definitie knop."""
        # DEF-366: Collection selector boven de generate knop
        self._render_rag_collection_selector()

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.button(
                "🚀 Genereer Definitie",
                type="primary",
                help="Start definitie generatie",
                key="main_generate_btn",
            ):
                if begrip.strip():
                    self._handle_definition_generation(begrip, context_data)
                else:
                    st.error("❌ Voer eerst een begrip in")

        with col2:
            if st.button(
                "🔍 Check Duplicates",
                help="Controleer op bestaande definities",
                key="main_check_btn",
            ):
                if begrip.strip():
                    self._handle_duplicate_check(begrip, context_data)
                else:
                    st.error("❌ Voer eerst een begrip in")

        with col3:
            if st.button(
                "🗑️ Wis Velden", help="Maak alle velden leeg", key="main_clear_btn"
            ):
                self._clear_all_fields()
                st.rerun()

    def _clear_all_fields(self) -> None:
        """Wis alle velden inclusief classificatie state."""
        fields_to_clear = [
            "begrip",
            "org_context",
            "jur_context",
            "wet_basis",
            "last_generation_result",
            "last_check_result",
            "manual_ontological_category",
            "determined_category",
            "category_reasoning",
            "category_scores",
        ]

        for field in fields_to_clear:
            SessionStateManager.clear_value(field)

    def _render_document_upload_section(self) -> None:
        """Delegate to DocumentUploadRenderer (DEF-141)."""
        self.document_upload_renderer.render_document_upload_section()

    def _process_uploaded_files(self, uploaded_files: Any) -> None:
        """Delegate to DocumentUploadRenderer (DEF-141)."""
        self.document_upload_renderer._process_uploaded_files(uploaded_files)

    def _render_uploaded_documents_list(self) -> None:
        """Delegate to DocumentUploadRenderer (DEF-141)."""
        self.document_upload_renderer.render_uploaded_documents_list()

    def _render_main_tabs(self) -> None:
        """Render de hoofdtabbladen met radio-gestuurde navigatie."""
        # Stel beschikbare keys samen
        tab_keys = list(self.tab_config.keys())

        # Actieve tab uit session of default
        default_key = SessionStateManager.get_value("active_tab", "generator")
        if default_key not in tab_keys:
            default_key = tab_keys[0]

        # Radio-navigatie
        selected_key = st.radio(
            "Navigatie",
            options=tab_keys,
            format_func=lambda k: self.tab_config[k]["title"],
            horizontal=True,
            index=tab_keys.index(default_key),
            key="main_tabs_radio",
        )
        # Bewaar keuze
        SessionStateManager.set_value("active_tab", selected_key)

        # Render alleen de geselecteerde tab
        self._render_tab_content(selected_key)

    def _render_tab_content(self, tab_key: str) -> None:
        """Render inhoud van specifiek tabblad."""
        config = self.tab_config[tab_key]

        # Tab header
        st.markdown(
            f"""
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
        """,
            unsafe_allow_html=True,
        )

        # Tab-specific content met error handling
        try:
            if tab_key == "generator":
                self.definition_tab.render()
            elif tab_key == "edit":
                self.edit_tab.render()
            elif tab_key == "expert":
                self.expert_tab.render()
            elif tab_key == "import_export_beheer":
                self.import_export_beheer_tab.render()
        except Exception as e:
            # Log de echte error voor debugging
            logger.error(f"Error in tab {tab_key}: {e!s}", exc_info=True)
            # Toon gebruikersvriendelijke foutmelding met details
            st.error(f"❌ Er is een fout opgetreden in tab '{config['title']}'")

            # In debug mode, toon technische details
            if st.checkbox(
                f"🔍 Toon technische details voor {tab_key}", key=f"debug_{tab_key}"
            ):
                st.code(f"Error type: {type(e).__name__}\nError message: {e!s}")

                # Extra debug info voor missing methods
                if "has no attribute" in str(e):
                    st.warning(
                        "💡 Dit lijkt op een ontbrekende method. Controleer of alle tab methods geïmplementeerd zijn."
                    )

    def _render_footer(self) -> None:
        """Render applicatie footer."""
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()

        with col2:
            st.markdown(
                """
                <div style="text-align: center; color: #666; font-size: 12px;">
                    DefinitieAgent 2.0 | Laatste update: """
                + datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
                + """
                </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            # Quick stats
            try:
                stats = self.repository.get_statistics()
                st.metric("📊 Definities", stats.get("total_definities", 0))
            except (AttributeError, KeyError, RuntimeError) as e:
                # DEF-229: Log footer stats retrieval failures
                logger.debug(f"Could not retrieve footer stats: {e}")

    # ------- Lightweight helpers primarily for test harness patching -------
    def _handle_file_upload(self) -> bool:  # pragma: no cover
        """Stub: file upload handler (patched in tests)."""
        return False

    def _handle_export(self) -> None:  # pragma: no cover
        """Stub: export handler (patched in tests)."""
        return

    def _validate_inputs(self) -> bool:  # pragma: no cover
        """Stub: input validation (patched in tests)."""
        return True

    def _update_progress(self) -> dict:  # pragma: no cover
        """Stub: progress update (patched in tests)."""
        return {"progress": 0.0}

    def _handle_user_interaction(self) -> str:  # pragma: no cover
        """Stub: user interaction handler (patched in tests)."""
        return "ok"

    def _process_large_data(self) -> bool:  # pragma: no cover
        """Stub: large data processing (patched in tests)."""
        return True

    def _sync_backend_state(self) -> dict:  # pragma: no cover
        """Stub: sync backend state (patched in tests)."""
        return {}

    def _integrate_with_backend(self) -> bool:  # pragma: no cover
        """Stub: backend integration step (patched in tests)."""
        return True


def render_tabbed_interface() -> None:
    """Main entry point voor tabbed interface."""
    # Initialize session state
    SessionStateManager.initialize_session_state()

    # Render interface
    interface = TabbedInterface()
    interface.render()


def initialize_session_state() -> None:
    """Compat helper voor tests: initialiseer Streamlit sessiestatus.

    Sommige tests importeren deze functie direct uit ui.tabbed_interface.
    """
    SessionStateManager.initialize_session_state()


if __name__ == "__main__":
    render_tabbed_interface()


# Test helper hook: some tests patch this symbol directly
def generate_definition(
    *args: Any, **kwargs: Any
) -> None:  # pragma: no cover - patch target for tests
    msg = "UI-level generate_definition is a test patch target only"
    raise NotImplementedError(msg)


def process_uploaded_file(
    *args: Any, **kwargs: Any
) -> None:  # pragma: no cover - patch target for tests
    msg = "process_uploaded_file is a test patch target only"
    raise NotImplementedError(msg)


def export_to_txt(
    *args: Any, **kwargs: Any
) -> None:  # pragma: no cover - patch target for tests
    msg = "export_to_txt is a test patch target only"
    raise NotImplementedError(msg)
