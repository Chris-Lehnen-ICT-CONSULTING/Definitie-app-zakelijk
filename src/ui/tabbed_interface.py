"""
# ruff: noqa: PLR0912, PLR0915, N814, RUF005, SIM105
Tabbed Interface voor DefinitieAgent - Nieuwe UI architectuur.
Implementeert de requirements uit Project Requirements Document.

Deze module bevat de hoofdcontroller voor de gebruikersinterface,
met ondersteuning voor meerdere tabs en complete workflow beheer.
"""

import asyncio  # Asynchrone programmering voor ontologische analyse
import logging  # Logging faciliteiten voor debug en monitoring
import os
from datetime import datetime  # Datum en tijd functionaliteit
from datetime import UTC
from typing import Any  # Type hints voor betere code documentatie

import streamlit as st  # Streamlit web interface framework

from database.definitie_repository import (
    get_definitie_repository,  # Database toegang factory
)
from document_processing.document_extractor import (
    supported_file_types,  # Ondersteunde bestandstypen
)
from document_processing.document_processor import (
    get_document_processor,  # Document processor factory
)
from domain.ontological_categories import (
    OntologischeCategorie,  # Ontologische categorieën
)
from integration.definitie_checker import (  # Definitie integratie controle
    CheckAction,
    DefinitieChecker,
)

# Nieuwe services imports
from services import get_definition_service
from ui.components.context_state_cleaner import init_context_cleaner
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

# Quality Control tab verwijderd - functionaliteit gedocumenteerd in EPIC-023
# Orchestration tab verwijderd - functionaliteit gedocumenteerd in EPIC-028
# Web Lookup tab verwijderd - functionaliteit is automatic via ModernWebLookupService
# Importeer core services en utilities
from ui.session_state import (
    SessionStateManager,  # Sessie state management voor UI persistentie
)

# US-202: Removed direct import of get_cached_container - use session state instead
from utils.type_helpers import ensure_dict

# Hybrid context imports - optionele module voor hybride context verrijking
try:
    import importlib.util  # Voor module availability check

    HYBRID_CONTEXT_AVAILABLE = (
        importlib.util.find_spec("hybrid_context.hybrid_context_engine") is not None
    )
except ImportError:
    HYBRID_CONTEXT_AVAILABLE = False  # Hybride context niet beschikbaar

# Module-level constants
UTC = UTC  # Voor Python 3.10 compatibility  # noqa: PLW0127

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class TabbedInterface:
    """Main tabbed interface controller voor DefinitieAgent."""

    def __init__(self):
        """Initialiseer tabbed interface met alle benodigde services."""
        # US-202 FIX: Get container via session state singleton to prevent duplicate initialization
        # Previously: direct get_cached_container() call bypassed session state cache
        # Now: use session_state container (initialized in SessionStateManager.initialize_session_state)
        from ui.cached_services import get_cached_service_container

        self.container = get_cached_service_container()

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
                    self, begrip: str, context_dict: dict, **kwargs
                ):
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
        # Quality Control tab verwijderd - zie EPIC-023 voor toekomstige implementatie
        # External Sources tab verwijderd - 95% overlap met Export tab
        # Web Lookup tab verwijderd - zie EPIC-028, automatic via ModernWebLookupService

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
            # Quality Control tab verwijderd - zie EPIC-023
            # "quality": {
            #     "title": "🔧 Kwaliteitscontrole",
            #     "icon": "🔧",
            #     "description": "Toetsregels analyse en system health",
            # },
            # External Sources tab verwijderd - zie EPIC-022
            # "external": {
            #     "title": "🔌 Externe Bronnen",
            #     "icon": "🔌",
            #     "description": "Import van externe definitie bronnen",
            # },
            # Web Lookup tab verwijderd - zie EPIC-028
            # Orchestration tab verwijderd - zie EPIC-028
            # Management tab geconsolideerd in import_export_beheer
        }

    def render(self):
        """Render de volledige tabbed interface."""
        # Clean session state on initialization - FORCE CLEAN voor problematische waardes
        init_context_cleaner(force_clean=True)

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

    async def _determine_ontological_category(self, begrip, org_context, jur_context):
        """
        Bepaal automatisch de ontologische categorie.

        VERBETERD: Gebruikt ImprovedOntologyClassifier met 3-context support.
        """
        from ontologie.improved_classifier import ImprovedOntologyClassifier

        try:
            classifier = ImprovedOntologyClassifier()

            # Classificeer met alle 3 contexten (org, jur, wet)
            # Wet context kunnen we later toevoegen aan UI
            result = classifier.classify(
                begrip=begrip,
                org_context=org_context,
                jur_context=jur_context,
                wet_context="",  # Wettelijke context: optioneel via UI uitbreiding
            )

            logger.info(
                f"Ontologische classificatie voor '{begrip}': {result.categorie.value} "
                f"(scores: {result.test_scores})"
            )

            return result.categorie, result.reasoning, result.test_scores

        except Exception as e:
            logger.error(f"Ontologische classificatie mislukt voor '{begrip}': {e}")

            # Fallback: PROCES (meest voorkomend in tests: 43%)
            fallback_scores = {"type": 0, "proces": 1, "resultaat": 0, "exemplaar": 0}
            return (
                OntologischeCategorie.PROCES,
                f"Fallback naar PROCES (error: {str(e)[:50]})",
                fallback_scores,
            )

    def _legacy_pattern_matching(self, begrip: str) -> str:
        """Legacy pattern matching voor fallback situaties."""
        begrip_lower = begrip.lower()

        # Eenvoudige patronen
        if any(begrip_lower.endswith(p) for p in ["atie", "ing", "eren"]):
            return "Proces patroon gedetecteerd"
        if any(w in begrip_lower for w in ["document", "bewijs", "systeem"]):
            return "Type patroon gedetecteerd"
        if any(w in begrip_lower for w in ["resultaat", "uitkomst", "besluit"]):
            return "Resultaat patroon gedetecteerd"
        return "Geen duidelijke patronen gedetecteerd"

    def _generate_category_reasoning(
        self, begrip: str, category: str, scores: dict[str, int]
    ) -> str:
        """Genereer uitleg waarom deze categorie gekozen is."""
        begrip_lower = begrip.lower()

        # Patronen per categorie
        patterns = {
            "proces": [
                "atie",
                "eren",
                "ing",
                "verificatie",
                "authenticatie",
                "validatie",
                "controle",
                "check",
                "beoordeling",
                "analyse",
                "behandeling",
                "vaststelling",
                "bepaling",
                "registratie",
                "identificatie",
            ],
            "type": [
                "bewijs",
                "document",
                "middel",
                "systeem",
                "methode",
                "tool",
                "instrument",
                "gegeven",
                "kenmerk",
                "eigenschap",
            ],
            "resultaat": [
                "besluit",
                "uitslag",
                "rapport",
                "conclusie",
                "bevinding",
                "resultaat",
                "uitkomst",
                "advies",
                "oordeel",
            ],
            "exemplaar": [
                "specifiek",
                "individueel",
                "uniek",
                "persoon",
                "zaak",
                "instantie",
                "geval",
                "situatie",
            ],
        }

        # Zoek gedetecteerde patronen
        detected_patterns = []
        for pattern in patterns.get(category, []):
            if pattern in begrip_lower:
                detected_patterns.append(pattern)

        if detected_patterns:
            pattern_text = ", ".join(f"'{p}'" for p in detected_patterns)
            return f"Gedetecteerde patronen: {pattern_text} (score: {scores[category]})"
        if category == "proces" and scores[category] == 0:
            return "Standaard categorie (geen specifieke patronen gedetecteerd)"
        return f"Hoogste score voor {category} categorie (score: {scores[category]})"

    def _get_category_scores(self, begrip: str) -> dict[str, int]:
        """Herbereken de categorie scores voor display."""
        try:
            begrip_lower = begrip.lower()

            # Dezelfde patronen als in _determine_ontological_category
            proces_indicators = [
                "atie",
                "eren",
                "ing",
                "verificatie",
                "authenticatie",
                "validatie",
                "controle",
                "check",
                "beoordeling",
                "analyse",
                "behandeling",
                "vaststelling",
                "bepaling",
                "registratie",
                "identificatie",
            ]

            type_indicators = [
                "bewijs",
                "document",
                "middel",
                "systeem",
                "methode",
                "tool",
                "instrument",
                "gegeven",
                "kenmerk",
                "eigenschap",
            ]

            resultaat_indicators = [
                "besluit",
                "uitslag",
                "rapport",
                "conclusie",
                "bevinding",
                "resultaat",
                "uitkomst",
                "advies",
                "oordeel",
            ]

            exemplaar_indicators = [
                "specifiek",
                "individueel",
                "uniek",
                "persoon",
                "zaak",
                "instantie",
                "geval",
                "situatie",
            ]

            # Score per categorie
            return {
                "proces": sum(
                    1 for indicator in proces_indicators if indicator in begrip_lower
                ),
                "type": sum(
                    1 for indicator in type_indicators if indicator in begrip_lower
                ),
                "resultaat": sum(
                    1 for indicator in resultaat_indicators if indicator in begrip_lower
                ),
                "exemplaar": sum(
                    1 for indicator in exemplaar_indicators if indicator in begrip_lower
                ),
            }

        except Exception as e:
            logger.warning(f"Failed to calculate category scores: {e}")
            return {"proces": 0, "type": 0, "resultaat": 0, "exemplaar": 0}

    def _render_header(self):
        """Render applicatie header."""

        # Sidebar voor settings (reserved for future use)

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

    def _render_status_indicator(self):
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

    def _render_global_context(self):
        """Render globale context selector."""
        # Begrip invoer als eerste
        st.markdown("### 📝 Definitie Aanvraag")
        begrip = st.text_input(
            "Voer een term in waarvoor een definitie moet worden gegenereerd",
            value=SessionStateManager.get_value("begrip", ""),
            placeholder="bijv. authenticatie, verificatie, identiteitsvaststelling...",
            help="Het centrale begrip waarvoor een definitie gegenereerd wordt",
        )
        SessionStateManager.set_value("begrip", begrip)

        st.markdown("### 🎯 Context Configuratie")

        # Document upload sectie
        self._render_document_upload_section()

        # Context selector - gebruik de officiële ContextSelector component
        try:
            context_data = self.context_selector.render()
            st.success("✅ Context selector succesvol geladen")
        except Exception as e:
            logger.error(f"Context selector crashed: {e}", exc_info=True)
            st.error(f"❌ Context selector fout: {type(e).__name__}: {e!s}")
            # Fallback naar simplified versie
            try:
                context_data = self._render_simplified_context_selector()
            except Exception as e2:
                logger.error(f"Simplified selector also failed: {e2}", exc_info=True)
                context_data = {
                    "organisatorische_context": [],
                    "juridische_context": [],
                    "wettelijke_basis": [],
                }

        # Store in session state voor gebruik in tabs
        SessionStateManager.set_value("global_context", context_data)

        # Show selected context summary
        if any(context_data.values()):
            self._render_context_summary(context_data)

        # Metadata velden (legacy restoration)
        st.markdown("### 📝 Metadata")
        try:
            self._render_metadata_fields()
            st.success("✅ Metadata velden succesvol geladen")
        except Exception as e:
            logger.error(f"Metadata fields crashed: {e}", exc_info=True)
            st.error(f"❌ Metadata velden fout: {type(e).__name__}: {e!s}")

        # Genereer definitie knop direct na context
        st.markdown("---")
        try:
            self._render_quick_generate_button(begrip, context_data)
            st.success("✅ Quick generate button succesvol geladen")
        except Exception as e:
            logger.error(f"Quick generate button crashed: {e}", exc_info=True)
            st.error(f"❌ Quick generate button fout: {type(e).__name__}: {e!s}")

    def _render_simplified_context_selector(self) -> dict[str, Any]:
        """Render context selector using the ContextManager-only implementation.

        Verwijderd: fallback naar legacy session_state implementatie.
        """
        try:
            from ui.components.enhanced_context_manager_selector import (
                render_context_selector,
            )

            return render_context_selector()
        except Exception as e:
            logger.error(
                f"Enhanced context selector kon niet renderen: {e}", exc_info=True
            )
            # Nooit terugvallen op legacy sessiestate; lever veilige lege context
            return {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }

    def _render_metadata_fields(self):
        """Render metadata velden voor definitie voorstel."""
        from datetime import datetime

        col1, col2, col3 = st.columns(3)

        with col1:
            # Datum voorstel
            datum_voorstel = st.date_input(
                "📅 Datum voorstel",
                value=SessionStateManager.get_value(
                    "datum_voorstel", datetime.now(UTC).date()
                ),
                help="Datum waarop deze definitie wordt voorgesteld",
            )
            SessionStateManager.set_value("datum_voorstel", datum_voorstel)

        with col2:
            # Voorgesteld door
            voorgesteld_door = st.text_input(
                "👤 Voorgesteld door",
                value=SessionStateManager.get_value("voorgesteld_door", ""),
                placeholder="Naam van voorsteller",
                help="Persoon of organisatie die deze definitie voorstelt",
            )
            SessionStateManager.set_value("voorgesteld_door", voorgesteld_door)

        with col3:
            # Ketenpartners
            ketenpartner_opties = [
                "ZM",
                "DJI",
                "KMAR",
                "CJIB",
                "JUSTID",
                "OM",
                "Reclassering",
                "NP",
            ]
            ketenpartners = st.multiselect(
                "🤝 Ketenpartners die akkoord zijn",
                options=ketenpartner_opties,
                default=SessionStateManager.get_value("ketenpartners", []),
                help="Partners die akkoord zijn met deze definitie",
            )
            SessionStateManager.set_value("ketenpartners", ketenpartners)

        # UFO‑categorie (optioneel) — wordt automatisch meegestuurd bij generatie
        # en opgeslagen met de definitie
        st.markdown("#### 🧭 UFO‑categorie (optioneel)")
        ufo_opties = [
            "",  # leeg = geen voorkeur; service bepaalt of laat leeg
            "Kind",
            "Event",
            "Role",
            "Phase",
            "Relator",
            "Mode",
            "Quantity",
            "Quality",
            "Subkind",
            "Category",
            "Mixin",
            "RoleMixin",
            "PhaseMixin",
            "Abstract",
            "Relatie",
            "Event Composition",
        ]
        ufo_default = SessionStateManager.get_value("ufo_categorie", "")
        try:
            default_index = (
                ufo_opties.index(ufo_default) if ufo_default in ufo_opties else 0
            )
        except Exception:
            default_index = 0
        ufo_selected = st.selectbox(
            "UFO‑categorie",
            options=ufo_opties,
            index=default_index,
            key="meta_ufo_categorie",
            help="Kies desgewenst een UFO‑categorie; deze wordt automatisch opgeslagen bij generatie",
        )
        SessionStateManager.set_value("ufo_categorie", ufo_selected)

    def _render_quick_generate_button(self, begrip: str, context_data: dict[str, Any]):
        """Render snelle genereer definitie knop."""
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

    def _handle_definition_generation(self, begrip: str, context_data: dict[str, Any]):
        """Handle definitie generatie met voorafgaande duplicate-check en keuze.

        Simpel gehouden: als er een bestaande definitie wordt gevonden, onderbreken
        we de generatie en tonen we twee opties: (1) Toon bestaande definitie, (2) Genereer nieuw.
        Bij optie (2) forceren we generatie en markeren we dit zodat CON-01 als error verschijnt.
        """
        try:
            with st.spinner("🔄 Genereren van definitie met hybride context..."):
                # EPIC-010: Consistente context variabelen voor alle 3 types
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                wet_context = context_data.get("wettelijke_basis", [])

                # Extract primary context items (needed for both manual and auto paths)
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""

                # Check eerst of er een handmatige categorie override bestaat
                manual_category = SessionStateManager.get_value(
                    "manual_ontological_category"
                )

                if manual_category:
                    # Gebruik handmatige override
                    from domain.ontological_categories import OntologischeCategorie

                    # Converteer string naar OntologischeCategorie enum
                    category_map = {
                        "type": OntologischeCategorie.TYPE,
                        "proces": OntologischeCategorie.PROCES,
                        "resultaat": OntologischeCategorie.RESULTAAT,
                        "exemplaar": OntologischeCategorie.EXEMPLAAR,
                    }
                    auto_categorie = category_map.get(
                        manual_category.lower(), OntologischeCategorie.PROCES
                    )
                    category_reasoning = (
                        f"Handmatig gekozen door gebruiker: {manual_category}"
                    )
                    category_scores = {"manual_override": 1.0}
                    logger.info(
                        f"Gebruik handmatige categorie override: {manual_category}"
                    )
                else:
                    # Bepaal automatisch de ontologische categorie
                    auto_categorie, category_reasoning, category_scores = asyncio.run(
                        self._determine_ontological_category(
                            begrip, primary_org, primary_jur
                        )
                    )

                # Krijg document context en selected document IDs
                document_context = self._get_document_context()
                selected_doc_ids = SessionStateManager.get_value(
                    "selected_documents", []
                )

                # DUPLICATE GATE: Voer duplicate-check uit vóór generatie (tenzij geforceerd)
                options = ensure_dict(
                    SessionStateManager.get_value("generation_options", {})
                )
                is_forced = bool(options.get("force_generate"))

                # Gebruik de automatisch bepaalde categorie voor nauwkeuriger check
                if not is_forced:
                    # DB repository bewaart org/jur als JSON-string; vergelijk exact daarop
                    import json as _json

                    primary_org = _json.dumps(
                        sorted(org_context or []), ensure_ascii=False
                    )
                    primary_jur = _json.dumps(
                        sorted(jur_context or []), ensure_ascii=False
                    )
                    wet_norm = sorted({str(x).strip() for x in (wet_context or [])})
                    check_result = self.checker.check_before_generation(
                        begrip=begrip,
                        organisatorische_context=primary_org,
                        juridische_context=primary_jur,
                        categorie=auto_categorie,
                        wettelijke_basis=wet_norm,
                    )

                    # Als we NIET mogen doorgaan, toon keuzes en stop generatie
                    if check_result.action != CheckAction.PROCEED:
                        SessionStateManager.set_value("last_check_result", check_result)
                        st.warning("⚠️ Bestaande definitie gevonden. Kies een optie:")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(
                                "👁️ Toon bestaande definitie", key="btn_show_existing"
                            ):
                                if check_result.existing_definitie:
                                    SessionStateManager.set_value(
                                        "selected_definition",
                                        check_result.existing_definitie,
                                    )
                                # Wis eventuele vorige generatie-output
                                SessionStateManager.clear_value(
                                    "last_generation_result"
                                )
                                st.rerun()
                        with c2:
                            if st.button(
                                "🚀 Genereer nieuwe definitie", key="btn_force_generate"
                            ):
                                # Forceer generatie en duid duplicaat als geaccepteerd voor doorlopen
                                options["force_generate"] = True
                                options["force_duplicate"] = True
                                SessionStateManager.set_value(
                                    "generation_options", options
                                )
                                # Wis duplicate‑check resultaat zodat bestaande definitie niet meer wordt getoond
                                try:
                                    SessionStateManager.clear_value("last_check_result")
                                    SessionStateManager.clear_value(
                                        "selected_definition"
                                    )
                                except Exception:
                                    pass
                                # Ga door met geforceerde generatie (buiten gate)
                            else:
                                # Niet gekozen → stop huidige generatie
                                return

                # Check of hybrid context gebruikt moet worden
                use_hybrid = HYBRID_CONTEXT_AVAILABLE and (
                    len(selected_doc_ids) > 0
                    or (
                        document_context
                        and document_context.get("document_count", 0) > 0
                    )
                )

                if use_hybrid:
                    st.info(
                        "🔄 Hybrid context activief - combineer document en web context..."
                    )

                # Altijd V2-servicepad gebruiken (geen legacy fallback)
                from ui.helpers.async_bridge import run_async

                # Haal actuele generation options op (kan force flags bevatten)
                options = ensure_dict(
                    SessionStateManager.get_value("generation_options", {})
                )

                # EPIC-018: bouw een samenvatting van documentcontext voor de service
                doc_summary = None
                if document_context and document_context.get("document_count", 0) > 0:
                    doc_summary = self._build_document_context_summary(document_context)
                # EPIC-018/US-229: bouw snippets op basis van begrip in geselecteerde documenten
                doc_snippets = []
                if selected_doc_ids:
                    # Config via env
                    try:
                        per_doc = int(os.getenv("DOCUMENT_SNIPPETS_PER_DOC", "4"))
                    except Exception:
                        per_doc = 4
                    try:
                        window_chars = int(os.getenv("SNIPPET_WINDOW_CHARS", "280"))
                    except Exception:
                        window_chars = 280

                    doc_snippets = self._build_document_snippets(
                        begrip=begrip,
                        selected_doc_ids=selected_doc_ids,
                        max_snippets_total=len(selected_doc_ids) * max(1, per_doc),
                        per_doc_max=per_doc,
                        snippet_window=window_chars,
                    )

                service_result = run_async(
                    self.definition_service.generate_definition(
                        begrip=begrip,
                        context_dict={
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": wet_context,  # EPIC-010: Gebruik consistente variabele
                        },
                        organisatie=primary_org,
                        categorie=auto_categorie,
                        ufo_categorie=(
                            SessionStateManager.get_value("ufo_categorie") or None
                        ),
                        # Geef opties door zodat validator duplicate kan escaleren
                        options={
                            k: v
                            for k, v in options.items()
                            if k in ("force_generate", "force_duplicate")
                        },
                        # EPIC-018: doorgeven aan service
                        document_context=doc_summary,
                        document_snippets=doc_snippets,
                    ),
                    timeout=120,
                )

                # Converteer naar checker formaat voor UI compatibility variabelen
                check_result = None
                agent_result = service_result

                # Voor auto-load in de Bewerk-tab: gebruik ID uit service‑resultaat; geen extra DB‑save
                saved_record = None
                saved_definition_id = None
                if isinstance(service_result, dict) and service_result.get("success"):
                    # Orchestrator (V2) slaat zelf op en ServiceAdapter levert saved_definition_id terug
                    saved_definition_id = service_result.get("saved_definition_id")

                # Capture voorbeelden prompts voor debug
                voorbeelden_prompts = None
                if isinstance(agent_result, dict) and (
                    agent_result.get("definitie_gecorrigeerd")
                    or agent_result.get("definitie")
                ):
                    try:
                        from ui.components.prompt_debug_section import (
                            capture_voorbeelden_prompts,
                        )

                        # Create context_dict for prompt debug
                        context_dict = {
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": wet_context,  # EPIC-010: Gebruik consistente variabele
                        }

                        definitie_for_prompts = agent_result.get(
                            "definitie_gecorrigeerd"
                        ) or agent_result.get("definitie", "")
                        voorbeelden_prompts = capture_voorbeelden_prompts(
                            begrip=begrip,
                            definitie=definitie_for_prompts,
                            context_dict=context_dict,
                        )
                    except Exception as e:
                        logger.warning(f"Could not capture example prompts: {e}")

                # Debug logging point C - Pre-store
                if os.getenv("DEBUG_EXAMPLES"):
                    logger.info(
                        "[EXAMPLES-C] Pre-store | gen_id=%s | voorbeelden=%s | counts=%s",
                        (
                            agent_result.get("metadata", {}).get("generation_id")
                            if isinstance(agent_result, dict)
                            else "NO_ID"
                        ),
                        (
                            "present"
                            if isinstance(agent_result, dict)
                            and agent_result.get("voorbeelden")
                            else "missing"
                        ),
                        {
                            k: len(v) if isinstance(v, (list, str)) else "INVALID"
                            for k, v in (
                                agent_result.get("voorbeelden", {})
                                if isinstance(agent_result, dict)
                                else {}
                            ).items()
                        },
                    )

                # Store results voor display in tabs
                SessionStateManager.set_value(
                    "last_generation_result",
                    {
                        "begrip": begrip,
                        "check_result": check_result,
                        "agent_result": agent_result,
                        "saved_record": saved_record,
                        "saved_definition_id": saved_definition_id,
                        "determined_category": auto_categorie.value,
                        "category_reasoning": category_reasoning,
                        "category_scores": category_scores,
                        "document_context": document_context,
                        "voorbeelden_prompts": voorbeelden_prompts,
                        "timestamp": datetime.now(UTC),
                    },
                )

                # Koppel gegenereerde definitie aan edit tab voor auto-load
                # Dit zorgt ervoor dat de definitie klaarstaat als gebruiker naar Bewerk navigeert
                logger.info(
                    f"DEBUG: saved_record = {saved_record}, type = {type(saved_record)}"
                )
                if saved_record:
                    logger.info(
                        f"DEBUG: saved_record has id? {hasattr(saved_record, 'id')}"
                    )
                    if hasattr(saved_record, "id"):
                        logger.info(f"DEBUG: saved_record.id = {saved_record.id}")

                # Bepaal te openen definitie‑ID voor de Bewerk‑tab
                target_edit_id = None
                if saved_definition_id:
                    target_edit_id = int(saved_definition_id)
                elif saved_record and hasattr(saved_record, "id"):
                    target_edit_id = int(saved_record.id)

                if target_edit_id:
                    # Sla definitie ID op voor edit tab
                    SessionStateManager.set_value(
                        "editing_definition_id", target_edit_id
                    )

                    # Sla ook de contexten op voor de edit tab
                    # Gebruik de context uit de generation call, niet uit saved_record
                    SessionStateManager.set_value(
                        "edit_organisatorische_context", org_context
                    )
                    SessionStateManager.set_value(
                        "edit_juridische_context", jur_context
                    )
                    SessionStateManager.set_value("edit_wettelijke_basis", wet_context)

                    logger.info(
                        f"Definition {target_edit_id} prepared for edit tab with contexts: "
                        f"org={len(org_context)} items, jur={len(jur_context)} items, wet={len(wet_context)} items"
                    )

                # Debug logging point C2 - Post-store
                if os.getenv("DEBUG_EXAMPLES"):
                    stored = SessionStateManager.get_value("last_generation_result", {})
                    stored_agent_result = stored.get("agent_result", {})
                    logger.info(
                        "[EXAMPLES-C2] Post-store | gen_id=%s | stored.voorbeelden=%s",
                        (
                            stored_agent_result.get("metadata", {}).get("generation_id")
                            if isinstance(stored_agent_result, dict)
                            else "NO_ID"
                        ),
                        (
                            "present"
                            if isinstance(stored_agent_result, dict)
                            and stored_agent_result.get("voorbeelden")
                            else "missing"
                        ),
                    )

                # Reset force flag na generatie om onbedoelde effecten te vermijden
                try:
                    if options.get("force_generate"):
                        options.pop("force_generate", None)
                        SessionStateManager.set_value("generation_options", options)
                except Exception:
                    pass

                # V2 validation is already included in agent_result.validation_details
                # The beoordeling_gen will be generated from V2 ValidationDetailsDict in the UI
                if isinstance(agent_result, dict):
                    validation_details = agent_result.get("validation_details", {})
                    logger.info(
                        f"V2 validation available - overall_score: {validation_details.get('overall_score', 0.0)}, "
                        f"violations: {len(validation_details.get('violations', []))}, "
                        f"passed_rules: {len(validation_details.get('passed_rules', []))}"
                    )

                # Toon document context info als gebruikt
                if document_context and document_context.get("document_count", 0) > 0:
                    st.success(
                        f"✅ Definitie gegenereerd met context van {document_context['document_count']} document(en)! Bekijk resultaten in de 'Definitie Generatie' tab."
                    )
                else:
                    st.success(
                        "✅ Definitie succesvol gegenereerd! Bekijk resultaten in de 'Definitie Generatie' tab."
                    )

        except Exception as e:
            st.error(f"❌ Fout bij generatie: {e!s}")
            logger.error(f"Global generation failed: {e}", exc_info=True)

    def _get_document_context(self) -> dict[str, Any] | None:
        """Krijg document context voor definitie generatie."""
        try:
            selected_docs = SessionStateManager.get_value("selected_documents", [])
            if not selected_docs:
                return None

            processor = get_document_processor()
            aggregated_context = processor.get_aggregated_context(selected_docs)

            if aggregated_context["document_count"] == 0:
                return None

            return aggregated_context

        except Exception as e:
            logger.error(f"Fout bij ophalen document context: {e}")
            return None

    def _build_document_context_summary(self, aggregated: dict[str, Any]) -> str:
        """Bouw een compacte samenvatting uit geaggregeerde documentcontext.

        Opzet: korte lijstjes met top‑items; aantal items gelimiteerd zodat het
        samenvattend blijft. Dit wordt gebruikt als `document_context` in het
        GenerationRequest.
        """
        try:
            parts: list[str] = []
            doc_cnt = int(aggregated.get("document_count", 0) or 0)
            total_len = int(aggregated.get("total_text_length", 0) or 0)
            if doc_cnt > 0:
                parts.append(f"Docs: {doc_cnt} | Tekst: {total_len} chars")

            kws = list(aggregated.get("aggregated_keywords", []) or [])[:10]
            if kws:
                parts.append("Keywords: " + ", ".join(kws))

            concepts = list(aggregated.get("aggregated_concepts", []) or [])[:5]
            if concepts:
                parts.append("Concepten: " + ", ".join(concepts))

            legal = list(aggregated.get("aggregated_legal_refs", []) or [])[:5]
            if legal:
                parts.append("Juridisch: " + ", ".join(legal))

            hints = list(aggregated.get("aggregated_context_hints", []) or [])[:3]
            if hints:
                parts.append("Hints: " + "; ".join(hints))

            return " | ".join(parts)
        except Exception:
            return ""

    def _build_document_snippets(
        self,
        begrip: str,
        selected_doc_ids: list[str],
        max_snippets_total: int | None = None,
        per_doc_max: int = 4,
        snippet_window: int = 280,
    ) -> list[dict[str, Any]]:
        """Zoek op begrip in geselecteerde documenten en bouw korte snippets.

        - Maakt per document maximaal 1 snippet (eerste match)
        - Beperkt totaal aantal snippets (default 2)
        - Snippet wordt gesanitized in de prompt‑service; hier beperken we lengte
        """
        try:
            if not begrip or not selected_doc_ids:
                return []

            processor = get_document_processor()
            begrip_lower = str(begrip).strip().lower()

            # Stel totaal‑limiet af op aantal documenten × per‑doc‑limiet
            if max_snippets_total is None:
                max_snippets_total = max(
                    0, int(len(selected_doc_ids) * max(1, per_doc_max))
                )

            snippets: list[dict[str, Any]] = []
            for doc_id in selected_doc_ids:
                doc = processor.get_document_by_id(doc_id)
                if not doc or not getattr(doc, "extracted_text", None):
                    continue

                text = doc.extracted_text
                haystack = text.lower()
                # Zoek meerdere matches (max per_doc_max)
                try:
                    import re

                    count_for_doc = 0
                    for m in re.finditer(re.escape(begrip_lower), haystack):
                        if len(snippets) >= max_snippets_total:
                            break
                        if count_for_doc >= max(1, per_doc_max):
                            break

                        idx = m.start()
                        start = max(0, idx - snippet_window // 2)
                        end = min(len(text), idx + len(begrip) + snippet_window // 2)
                        raw = text[start:end].replace("\n", " ").strip()

                        # Bepaal bronvermelding binnen document (pagina of paragraaf)
                        citation_label = None
                        try:
                            mime = getattr(doc, "mime_type", "") or ""
                            if mime == "application/pdf":
                                page_num = text.count("\f", 0, idx) + 1
                                citation_label = f"p. {page_num}"
                            elif (
                                mime
                                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            ):
                                para_num = text.count("\n", 0, idx) + 1
                                citation_label = f"¶ {para_num}"
                        except Exception:
                            citation_label = None

                        snippet = {
                            "provider": "documents",
                            "title": getattr(doc, "filename", "document"),
                            "filename": getattr(doc, "filename", None),
                            "doc_id": getattr(doc, "id", None),
                            "snippet": raw,
                            "score": 1.0,
                            "used_in_prompt": True,
                            "citation_label": citation_label,
                        }
                        snippets.append(snippet)
                        count_for_doc += 1
                        if len(snippets) >= max_snippets_total:
                            break
                except Exception:
                    # Bij een fout in regex/matching: ga door met volgende document
                    continue

            return snippets[:max_snippets_total]
        except Exception:
            return []

    def _handle_duplicate_check(self, begrip: str, context_data: dict[str, Any]):
        """Handle duplicate check vanaf hoofdniveau."""
        try:
            with st.spinner("🔍 Controleren op duplicates..."):
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                wet_context = context_data.get("wettelijke_basis", [])

                import json as _json

                primary_org = _json.dumps(sorted(org_context or []), ensure_ascii=False)
                primary_jur = _json.dumps(sorted(jur_context or []), ensure_ascii=False)
                wet_norm = sorted({str(x).strip() for x in (wet_context or [])})

                check_result = self.checker.check_before_generation(
                    begrip=begrip,
                    organisatorische_context=primary_org,
                    juridische_context=primary_jur,
                    categorie=OntologischeCategorie.PROCES,  # Default
                    wettelijke_basis=wet_norm,
                )

                SessionStateManager.set_value("last_check_result", check_result)
                st.success(
                    "✅ Duplicate check voltooid! Bekijk resultaten in de 'Definitie Generatie' tab."
                )

        except Exception as e:
            st.error(f"❌ Fout bij duplicate check: {e!s}")
            logger.error(f"Global duplicate check failed: {e}")

    def _clear_all_fields(self):
        """Wis alle velden."""
        fields_to_clear = [
            "begrip",
            "org_context",
            "jur_context",
            "wet_basis",
            "last_generation_result",
            "last_check_result",
            "manual_ontological_category",  # Wis ook handmatige categorie override
        ]

        for field in fields_to_clear:
            SessionStateManager.clear_value(field)

    def _render_context_summary(self, context_data: dict[str, Any]):
        """Render samenvatting van geselecteerde context."""
        summary_parts = []

        if context_data.get("organisatorische_context"):
            summary_parts.append(
                f"📋 Org: {', '.join(context_data['organisatorische_context'])}"
            )

        if context_data.get("juridische_context"):
            summary_parts.append(
                f"⚖️ Juridisch: {', '.join(context_data['juridische_context'])}"
            )

        if context_data.get("wettelijke_basis"):
            summary_parts.append(
                f"📜 Wet: {', '.join(context_data['wettelijke_basis'])}"
            )

        if summary_parts:
            st.info(" | ".join(summary_parts))

    def _render_document_upload_section(self):
        """Render document upload sectie voor context enrichment."""
        with st.expander("📄 Document Upload voor Context Verrijking", expanded=False):
            st.markdown(
                "Upload documenten die relevante context bevatten voor de definitie generatie."
            )
            # Korte links naar documentatie
            st.markdown(
                "- ℹ️ Technisch: [Extractie & flow](docs/technisch/document_processing.md)"
            )
            st.markdown(
                "- 🧑‍💻 Dev how‑to: [document_context gebruiken](docs/handleidingen/ontwikkelaars/document-context-gebruik.md)"
            )

            # File uploader
            uploaded_files = st.file_uploader(
                "Selecteer documenten",
                type=["txt", "pdf", "docx", "doc", "md", "csv", "json", "html", "rtf"],
                accept_multiple_files=True,
                help="Ondersteunde formaten: TXT, PDF, Word, Markdown, CSV, JSON, HTML, RTF",
            )

            # Toon ondersteunde bestandstypen in sidebar of als tekst
            if st.checkbox("i️ Toon ondersteunde bestandstypen", value=False):
                supported_types = supported_file_types()
                st.markdown("**Ondersteunde bestandstypen:**")
                for _mime_type, description in supported_types.items():
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
                    file_content, uploaded_file.name, uploaded_file.type
                )

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
                        f"✅ {doc.filename}: {doc.text_length} karakters geëxtraheerd"
                    )
                else:
                    st.error(f"❌ {doc.filename}: {doc.error_message}")

            # Update session state
            SessionStateManager.set_value("documents_updated", True)

    def _render_uploaded_documents_list(self):  # noqa: PLR0915
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
                format_func=lambda x: next(
                    label
                    for doc_id, label in zip(doc_options, doc_labels, strict=False)
                    if doc_id == x
                ),
                default=SessionStateManager.get_value("selected_documents", []),
                help="Geselecteerde documenten worden gebruikt voor context en bronvermelding",
            )

            SessionStateManager.set_value("selected_documents", selected_docs)

            # Toon document details
            if selected_docs:
                st.markdown(
                    f"#### 📋 Details van {len(selected_docs)} geselecteerde document(en)"
                )
                aggregated = processor.get_aggregated_context(selected_docs)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Documenten", aggregated["document_count"])
                    st.metric(
                        "Totale tekst", f"{aggregated['total_text_length']:,} chars"
                    )

                with col2:
                    st.metric("Keywords", len(aggregated["aggregated_keywords"]))
                    st.metric("Concepten", len(aggregated["aggregated_concepts"]))

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
                            f"{doc.text_length:,} chars, {len(doc.keywords)} keywords"
                        )
                    else:
                        st.caption(f"Error: {doc.error_message}")

                with col2:
                    upload_date = doc.uploaded_at.strftime("%d-%m %H:%M")
                    st.caption(upload_date)

                with col3:
                    if st.button(
                        "🗑️", key=f"delete_{doc.id}", help=f"Verwijder {doc.filename}"
                    ):
                        processor.remove_document(doc.id)
                        st.rerun()

    def _render_main_tabs(self):
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

    def _render_tab_content(self, tab_key: str):
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
            # Quality Control tab verwijderd - zie EPIC-023
            # elif tab_key == "quality":
            #     self.quality_tab.render()
            # External Sources tab verwijderd
            # elif tab_key == "external":
            #     self.external_tab.render()
            # Web Lookup tab verwijderd - zie EPIC-028
            # Orchestration tab verwijderd - zie EPIC-028
            # Management tab geconsolideerd in import_export_beheer
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

    def _render_footer(self):
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
            except Exception:
                pass

    # ------- Lightweight helpers primarily for test harness patching -------
    def _handle_file_upload(self) -> bool:  # pragma: no cover
        """Stub: file upload handler (patched in tests)."""
        return False

    def _handle_export(self):  # pragma: no cover
        """Stub: export handler (patched in tests)."""
        return

    def _validate_inputs(self) -> bool:  # pragma: no cover
        """Stub: input validation (patched in tests)."""
        return True

    def _update_progress(self) -> dict:  # pragma: no cover
        """Stub: progress update (patched in tests)."""
        return {"progress": 0.0}

    def _handle_user_interaction(self):  # pragma: no cover
        """Stub: user interaction handler (patched in tests)."""
        return "ok"

    def _process_large_data(self) -> bool:  # pragma: no cover
        """Stub: large data processing (patched in tests)."""
        return True

    def _sync_backend_state(self) -> dict:  # pragma: no cover
        """Stub: sync backend state (patched in tests)."""
        return {}

    def _integrate_with_backend(self):  # pragma: no cover
        """Stub: backend integration step (patched in tests)."""
        return True


def render_tabbed_interface():
    """Main entry point voor tabbed interface."""
    # Initialize session state
    SessionStateManager.initialize_session_state()

    # Render interface
    interface = TabbedInterface()
    interface.render()


def initialize_session_state():
    """Compat helper voor tests: initialiseer Streamlit sessiestatus.

    Sommige tests importeren deze functie direct uit ui.tabbed_interface.
    """
    SessionStateManager.initialize_session_state()


if __name__ == "__main__":
    render_tabbed_interface()


# Test helper hook: some tests patch this symbol directly
def generate_definition(*args, **kwargs):  # pragma: no cover - patch target for tests
    msg = "UI-level generate_definition is a test patch target only"
    raise NotImplementedError(msg)


def process_uploaded_file(*args, **kwargs):  # pragma: no cover - patch target for tests
    msg = "process_uploaded_file is a test patch target only"
    raise NotImplementedError(msg)


def export_to_txt(*args, **kwargs):  # pragma: no cover - patch target for tests
    msg = "export_to_txt is a test patch target only"
    raise NotImplementedError(msg)
