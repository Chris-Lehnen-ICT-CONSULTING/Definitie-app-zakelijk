"""
Tabbed Interface voor DefinitieAgent - Nieuwe UI architectuur.
Implementeert de requirements uit Project Requirements Document.

Deze module bevat de hoofdcontroller voor de gebruikersinterface,
met ondersteuning voor meerdere tabs en complete workflow beheer.
"""

import asyncio  # Asynchrone programmering voor ontologische analyse
from datetime import datetime, timezone  # Datum en tijd functionaliteit, timezone
from typing import Any  # Type hints voor betere code documentatie

import streamlit as st  # Streamlit web interface framework
from database.definitie_repository import (  # Database toegang factory
    get_definitie_repository,
)
from document_processing.document_extractor import (  # Ondersteunde bestandstypen
    supported_file_types,
)
from document_processing.document_processor import (  # Document processor factory
    get_document_processor,
)
from domain.ontological_categories import (
    OntologischeCategorie,  # Ontologische categorieën
)
from integration.definitie_checker import (  # Definitie integratie controle
    DefinitieChecker,
)

# Nieuwe services imports
from services import get_definition_service, render_feature_flag_toggle
from services.regeneration_service import RegenerationService

# Importeer alle UI tab componenten voor de verschillende functionaliteiten
from ui.components.context_selector import ContextSelector  # Context selectie component
from ui.components.definition_generator_tab import (  # Hoofdtab voor definitie generatie
    DefinitionGeneratorTab,
)
from ui.components.expert_review_tab import (  # Expert review en validatie tab
    ExpertReviewTab,
)
from ui.components.export_tab import ExportTab  # Export functionaliteit tab
from ui.components.external_sources_tab import (  # Externe bronnen beheer
    ExternalSourcesTab,
)
from ui.components.history_tab import HistoryTab  # Historie overzicht tab
from ui.components.management_tab import ManagementTab  # Systeem management tools
from ui.components.monitoring_tab import MonitoringTab  # Monitoring en statistieken

# TIJDELIJK UITGESCHAKELD - OrchestrationTab heeft compatibility issues
# from ui.components.orchestration_tab import (  # Orchestratie en automatisering
#     OrchestrationTab,
# )
from ui.components.quality_control_tab import (  # Kwaliteitscontrole dashboard
    QualityControlTab,
)
from ui.components.web_lookup_tab import WebLookupTab  # Web lookup interface

# Importeer core services en utilities
from ui.session_state import (  # Sessie state management voor UI persistentie
    SessionStateManager,
)

# Hybrid context imports - optionele module voor hybride context verrijking
try:
    import importlib.util  # Voor module availability check

    HYBRID_CONTEXT_AVAILABLE = (
        importlib.util.find_spec("hybrid_context.hybrid_context_engine") is not None
    )
except ImportError:
    HYBRID_CONTEXT_AVAILABLE = False  # Hybride context niet beschikbaar
import logging  # Logging faciliteiten voor debug en monitoring

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class TabbedInterface:
    """Main tabbed interface controller voor DefinitieAgent."""

    def __init__(self):
        """Initialiseer tabbed interface met alle benodigde services."""
        self.repository = (
            get_definitie_repository()
        )  # Haal database repository instantie op

        # Gebruik nieuwe service factory voor definitie service
        self.definition_service = get_definition_service()

        # Maak DefinitieChecker met de service
        self.checker = DefinitieChecker(self.repository)
        # Update checker om nieuwe service te gebruiken indien beschikbaar
        if hasattr(self.definition_service, "get_service_info"):
            # V2 service heeft get_service_info methode
            self.checker._definition_service = self.definition_service

        # Initialiseer RegenerationService voor category regeneration (GVI Rode Kabel)
        from services.definition_generator_config import UnifiedGeneratorConfig
        from services.definition_generator_prompts import UnifiedPromptBuilder

        # Basic config voor regeneration service
        config = UnifiedGeneratorConfig()
        prompt_builder = UnifiedPromptBuilder(config)
        self.regeneration_service = RegenerationService(prompt_builder)

        self.context_selector = (
            ContextSelector()
        )  # Initialiseer context selector component

        # Initialiseer alle tab componenten met repository referentie
        self.definition_tab = DefinitionGeneratorTab(self.checker)
        self.expert_tab = ExpertReviewTab(self.repository)
        self.history_tab = HistoryTab(self.repository)
        self.export_tab = ExportTab(self.repository)
        self.quality_tab = QualityControlTab(self.repository)
        self.external_tab = ExternalSourcesTab(self.repository)
        self.monitoring_tab = MonitoringTab(self.repository)
        self.web_lookup_tab = WebLookupTab(self.repository)
        # TIJDELIJK UITGESCHAKELD - OrchestrationTab heeft compatibility issues
        # self.orchestration_tab = OrchestrationTab(self.repository)
        self.management_tab = ManagementTab(self.repository)

        # Tab configuration
        self.tab_config = {
            "generator": {
                "title": "🚀 Definitie Generatie",
                "icon": "🚀",
                "description": "Genereer nieuwe definities met AI-ondersteuning",
            },
            "expert": {
                "title": "👨‍💼 Expert Review",
                "icon": "👨‍💼",
                "description": "Review en goedkeuring van definities",
            },
            "history": {
                "title": "📜 Geschiedenis",
                "icon": "📜",
                "description": "Bekijk historie van definities en wijzigingen",
            },
            "export": {
                "title": "📤 Export & Beheer",
                "icon": "📤",
                "description": "Exporteer en beheer definities",
            },
            "quality": {
                "title": "🔧 Kwaliteitscontrole",
                "icon": "🔧",
                "description": "Toetsregels analyse en system health",
            },
            "external": {
                "title": "🔌 Externe Bronnen",
                "icon": "🔌",
                "description": "Import van externe definitie bronnen",
            },
            "monitoring": {
                "title": "📈 Monitoring",
                "icon": "📈",
                "description": "Performance monitoring en API cost tracking",
            },
            "web_lookup": {
                "title": "🔍 Web Lookup",
                "icon": "🔍",
                "description": "Zoek definities en bronnen, valideer duplicaten",
            },
            # TIJDELIJK UITGESCHAKELD - OrchestrationTab heeft compatibility issues
            # "orchestration": {
            #     "title": "🤖 Orchestratie",
            #     "icon": "🤖",
            #     "description": "Intelligente definitie orchestratie en iteratieve verbetering",
            # },
            "management": {
                "title": "🛠️ Management",
                "icon": "🛠️",
                "description": "Database beheer, import/export en system administratie",
            },
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

    async def _determine_ontological_category(self, begrip, org_context, jur_context):
        """Bepaal automatisch de ontologische categorie via 6-stappen protocol."""
        try:
            # Importeer de nieuwe ontologische analyzer
            from ontologie.ontological_analyzer import (
                OntologischeAnalyzer,
                QuickOntologischeAnalyzer,
            )

            # Probeer eerst de volledige 6-stappen analyse
            try:
                analyzer = OntologischeAnalyzer()
                (
                    categorie,
                    analyse_resultaat,
                ) = await analyzer.bepaal_ontologische_categorie(
                    begrip, org_context, jur_context
                )

                # Haal de redenering en scores uit het analyse resultaat
                reasoning = analyse_resultaat.get(
                    "reasoning", "Ontologische analyse voltooid"
                )
                test_scores = analyse_resultaat.get("categorie_resultaat", {}).get(
                    "test_scores", {}
                )

                logger.info(
                    f"6-stappen ontologische analyse voor '{begrip}': {categorie.value}"
                )
                return categorie, reasoning, test_scores

            except Exception as e:
                logger.warning(f"6-stappen analyse mislukt voor '{begrip}': {e}")

                # Fallback naar quick analyzer
                quick_analyzer = QuickOntologischeAnalyzer()
                categorie, reasoning = quick_analyzer.quick_categoriseer(begrip)

                logger.info(
                    f"Quick ontologische analyse voor '{begrip}': {categorie.value}"
                )
                # Genereer dummy scores voor quick analyzer
                quick_scores = {
                    cat: 0.5 if cat == categorie.value else 0.0
                    for cat in ["type", "proces", "resultaat", "exemplaar"]
                }
                return categorie, f"Quick analyse - {reasoning}", quick_scores

        except Exception as e:
            logger.error(f"Ontologische analyse volledig mislukt voor '{begrip}': {e}")

            # Ultieme fallback naar oude pattern matching
            reasoning = self._legacy_pattern_matching(begrip)
            # Genereer dummy scores voor legacy fallback
            legacy_scores = {"type": 0, "proces": 1, "resultaat": 0, "exemplaar": 0}
            return (
                OntologischeCategorie.PROCES,
                f"Legacy fallback - {reasoning}",
                legacy_scores,
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

        # Sidebar voor settings
        with st.sidebar:
            st.markdown("### ⚙️ Instellingen")

            # Feature flag toggle voor nieuwe services
            render_feature_flag_toggle()

            st.markdown("---")

            # Service info
            if hasattr(self.definition_service, "get_service_info"):
                info = self.definition_service.get_service_info()
                st.info(
                    f"**Service Mode:** {info['service_mode']}\n**Architecture:** {info['architecture']}"
                )

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

        # Context selector zonder presets - direct handmatige selectie
        context_data = self._render_simplified_context_selector()

        # Store in session state voor gebruik in tabs
        SessionStateManager.set_value("global_context", context_data)

        # Show selected context summary
        if any(context_data.values()):
            self._render_context_summary(context_data)

        # Metadata velden (legacy restoration)
        st.markdown("### 📝 Metadata")
        self._render_metadata_fields()

        # Genereer definitie knop direct na context
        st.markdown("---")
        self._render_quick_generate_button(begrip, context_data)

    def _render_simplified_context_selector(self) -> dict[str, Any]:
        """Render vereenvoudigde context selector zonder presets."""
        col1, col2, col3 = st.columns(3)

        with col1:
            # Organisatorische context
            org_options = [
                "OM",
                "ZM",
                "Reclassering",
                "DJI",
                "NP",
                "Justid",
                "KMAR",
                "FIOD",
                "CJIB",
                "Strafrechtketen",
                "Migratieketen",
                "Justitie en Veiligheid",
                "Anders...",
            ]

            selected_org = st.multiselect(
                "📋 Organisatorische context",
                options=org_options,
                default=SessionStateManager.get_value("org_context", []),
                help="Selecteer één of meerdere organisaties",
            )

            # Custom org context
            custom_org = ""
            if "Anders..." in selected_org:
                custom_org = st.text_input(
                    "Aangepaste organisatorische context",
                    placeholder="Voer andere organisatie in...",
                    key="custom_org_global",
                )

            # Combineer contexts
            final_org = [opt for opt in selected_org if opt != "Anders..."]
            if custom_org.strip():
                final_org.append(custom_org.strip())

            SessionStateManager.set_value("org_context", final_org)

        with col2:
            # Juridische context
            jur_options = [
                "Strafrecht",
                "Civiel recht",
                "Bestuursrecht",
                "Internationaal recht",
                "Europees recht",
                "Migratierecht",
                "Anders...",
            ]

            selected_jur = st.multiselect(
                "⚖️ Juridische context",
                options=jur_options,
                default=SessionStateManager.get_value("jur_context", []),
                help="Selecteer juridische gebieden",
            )

            # Custom juridical context
            custom_jur = ""
            if "Anders..." in selected_jur:
                custom_jur = st.text_input(
                    "Aangepaste juridische context",
                    placeholder="Voer ander rechtsgebied in...",
                    key="custom_jur_global",
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
                "Anders...",
            ]

            selected_wet = st.multiselect(
                "📜 Wettelijke basis",
                options=wet_options,
                default=SessionStateManager.get_value("wet_basis", []),
                help="Selecteer relevante wetgeving",
            )

            # Custom legal basis
            custom_wet = ""
            if "Anders..." in selected_wet:
                custom_wet = st.text_input(
                    "Aangepaste wettelijke basis",
                    placeholder="Voer andere wetgeving in...",
                    key="custom_wet_global",
                )

            # Combineer wettelijke basis
            final_wet = [opt for opt in selected_wet if opt != "Anders..."]
            if custom_wet.strip():
                final_wet.append(custom_wet.strip())

            SessionStateManager.set_value("wet_basis", final_wet)

        return {
            "organisatorische_context": final_org,
            "juridische_context": final_jur,
            "wettelijke_basis": final_wet,
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
                    "datum_voorstel", datetime.now(timezone.utc).date()
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
        """Handle definitie generatie vanaf hoofdniveau met hybrid context ondersteuning."""
        try:
            with st.spinner("🔄 Genereren van definitie met hybride context..."):
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])

                # Bepaal automatisch de ontologische categorie
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""
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

                # Check voor actieve regeneration context (GVI Rode Kabel)
                regeneration_context = self.regeneration_service.get_active_context()
                if regeneration_context:
                    # Override categorie met nieuwe categorie uit regeneration context
                    auto_categorie_original = auto_categorie
                    try:
                        # Convert string to OntologischeCategorie if needed
                        if isinstance(regeneration_context.new_category, str):
                            auto_categorie = OntologischeCategorie(
                                regeneration_context.new_category.lower()
                            )
                        else:
                            auto_categorie = regeneration_context.new_category

                        logger.info(
                            f"Regeneration actief: categorie override {auto_categorie_original.value} -> {auto_categorie.value}"
                        )

                        # Update category reasoning voor UI feedback
                        category_reasoning = f"Regeneratie: aangepast van {auto_categorie_original.value} naar {auto_categorie.value}"

                    except Exception as e:
                        logger.warning(
                            f"Could not apply regeneration category override: {e}"
                        )
                        auto_categorie = auto_categorie_original

                # Gebruik de nieuwe service factory indien beschikbaar
                if hasattr(self, "definition_service") and hasattr(
                    self.definition_service, "get_service_info"
                ):
                    # Gebruik de V2 service voor generatie - nu sync interface
                    service_result = self.definition_service.generate_definition(
                        begrip=begrip,
                        context_dict={
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": context_data.get("wettelijke_basis", []),
                        },
                        organisatie=primary_org,
                        categorie=auto_categorie,
                        # Pass regeneration context for GVI feedback loop
                        regeneration_context=regeneration_context,
                    )

                    # Converteer naar checker formaat voor UI compatibility
                    check_result = None
                    agent_result = service_result
                    saved_record = None
                else:
                    # Legacy path
                    check_result, agent_result, saved_record = (
                        self.checker.generate_with_check(
                            begrip=begrip,
                            organisatorische_context=primary_org,
                            juridische_context=primary_jur,
                            categorie=auto_categorie,
                            force_generate=False,
                            created_by="global_user",
                            # Hybride context parameters
                            selected_document_ids=(
                                selected_doc_ids if use_hybrid else None
                            ),
                            enable_hybrid=use_hybrid,
                        )
                    )

                # Capture voorbeelden prompts voor debug
                voorbeelden_prompts = None
                if agent_result and agent_result.final_definitie:
                    try:
                        from ui.components.prompt_debug_section import (
                            capture_voorbeelden_prompts,
                        )

                        # Create context_dict for prompt debug
                        context_dict = {
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": context_data.get("wettelijke_basis", []),
                        }

                        voorbeelden_prompts = capture_voorbeelden_prompts(
                            begrip=begrip,
                            definitie=agent_result.final_definitie,
                            context_dict=context_dict,
                        )
                    except Exception as e:
                        logger.warning(f"Could not capture example prompts: {e}")

                # Store results voor display in tabs
                SessionStateManager.set_value(
                    "last_generation_result",
                    {
                        "begrip": begrip,
                        "check_result": check_result,
                        "agent_result": agent_result,
                        "saved_record": saved_record,
                        "determined_category": auto_categorie.value,
                        "category_reasoning": category_reasoning,
                        "category_scores": category_scores,
                        "document_context": document_context,
                        "voorbeelden_prompts": voorbeelden_prompts,
                        "timestamp": datetime.now(timezone.utc),
                        "regeneration_used": regeneration_context is not None,
                    },
                )

                # Clear regeneration context after successful generation (GVI cleanup)
                if regeneration_context:
                    self.regeneration_service.clear_context()
                    logger.info(
                        f"Regeneration context cleared after successful generation for '{begrip}'"
                    )

                    # Also clear UI session state markers
                    SessionStateManager.clear_value("regeneration_active")
                    SessionStateManager.clear_value("regeneration_begrip")
                    SessionStateManager.clear_value("regeneration_category")

                # Store detailed validation results for display
                # Check for both legacy (best_iteration) and new service (dict) formats
                if agent_result and (
                    hasattr(agent_result, "best_iteration")
                    or isinstance(agent_result, dict)
                ):
                    logger.info(
                        f"Attempting to run toets_definitie. agent_result type: {type(agent_result)}"
                    )
                    from ai_toetser.modular_toetser import toets_definitie
                    from toetsregels.modular_loader import load_all_toetsregels

                    # Get detailed validation results with proper context using modular loader
                    # Dit laadt zowel JSON configs als Python validators
                    alle_regel_data = load_all_toetsregels()

                    # Converteer naar formaat dat toets_definitie verwacht
                    toetsregels = {}
                    for regel_id, regel_data in alle_regel_data.items():
                        toetsregels[regel_id] = regel_data["config"]

                    logger.info(
                        f"Loaded {len(toetsregels)} toetsregels via modular loader (JSON + Python modules)"
                    )

                    # Create contexten dictionary for validation
                    contexten = {
                        "organisatorisch": org_context,
                        "juridisch": jur_context,
                        "wettelijk": context_data.get("wettelijke_basis", []),
                    }

                    # Get definition from either legacy or new service format
                    if isinstance(agent_result, dict):
                        # New service format
                        definitie_text = agent_result.get("definitie_gecorrigeerd", "")
                        logger.info(
                            f"Using new service format. Keys in agent_result: {list(agent_result.keys())}"
                        )
                        logger.info(
                            f"definitie_text from dict: '{definitie_text[:50]}...'"
                        )
                    else:
                        # Legacy format with best_iteration
                        definitie_text = (
                            agent_result.final_definitie
                            if hasattr(agent_result, "final_definitie")
                            else ""
                        )
                        logger.info(
                            f"Using legacy format. definitie_text: '{definitie_text[:50]}...'"
                        )

                    detailed_results = toets_definitie(
                        definitie=definitie_text,
                        toetsregels=toetsregels,
                        begrip=begrip,
                        marker=auto_categorie.value,
                        contexten=contexten,
                        gebruik_logging=True,
                    )

                    SessionStateManager.set_value("beoordeling_gen", detailed_results)
                    logger.info(
                        f"Stored {len(detailed_results)} detailed validation results in session state"
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

    def _handle_duplicate_check(self, begrip: str, context_data: dict[str, Any]):
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
                    categorie=OntologischeCategorie.PROCES,  # Default
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
        """Render de hoofdtabbladen."""
        # Create tabs
        tab_keys = list(self.tab_config.keys())
        tab_titles = [self.tab_config[key]["title"] for key in tab_keys]

        tabs = st.tabs(tab_titles)

        # Render each tab
        for _i, (tab_key, tab) in enumerate(zip(tab_keys, tabs, strict=False)):
            with tab:
                self._render_tab_content(tab_key)

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
            # TIJDELIJK UITGESCHAKELD - OrchestrationTab heeft compatibility issues
            # elif tab_key == "orchestration":
            #     self.orchestration_tab.render()
            elif tab_key == "management":
                self.management_tab.render()
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
                + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
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


def render_tabbed_interface():
    """Main entry point voor tabbed interface."""
    # Initialize session state
    SessionStateManager.initialize_session_state()

    # Render interface
    interface = TabbedInterface()
    interface.render()


if __name__ == "__main__":
    render_tabbed_interface()
