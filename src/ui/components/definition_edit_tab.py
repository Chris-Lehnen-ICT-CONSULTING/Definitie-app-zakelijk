"""
Definition Edit Tab - Rich text editor interface voor definities.

Deze tab biedt een gebruiksvriendelijke interface voor het bewerken
van definities met ondersteuning voor versiegeschiedenis en auto-save.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import streamlit as st
from config.config_manager import get_config, ConfigSection

from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.validation.modular_validation_service import ModularValidationService
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class DefinitionEditTab:
    """Tab voor het bewerken van definities met rich text editor."""

    def __init__(self,
                 repository: DefinitionEditRepository = None,
                 validation_service: ModularValidationService = None):
        """
        Initialiseer definition edit tab.

        Args:
            repository: Repository voor data toegang
            validation_service: Service voor validatie
        """
        self.repository = repository or DefinitionEditRepository()
        self.edit_service = DefinitionEditService(
            repository=self.repository,
            validation_service=validation_service
        )

        # Initialize session state via SessionStateManager
        self._ensure_edit_session_state()

        logger.info("DefinitionEditTab initialized")

    def render(self):
        """Render de edit tab interface."""
        st.markdown("## ✏️ Definitie Editor")
        st.markdown("Bewerk definities met een rijke text editor, versiegeschiedenis en auto-save functionaliteit.")

        # Auto-start bewerksessie als er al een target ID is gezet (bijv. via generator-tab)
        try:
            target_id = SessionStateManager.get_value('editing_definition_id')
            current_definition = SessionStateManager.get_value('editing_definition')

            # Check of we een nieuwe definitie moeten laden
            # Dit gebeurt als:
            # 1. Er is een target_id EN geen huidige definitie, OF
            # 2. Er is een target_id EN het is een andere definitie dan de huidige
            should_load = False
            if target_id and not current_definition:
                should_load = True
                logger.info(f"Loading definition {target_id} - no current definition")
            elif target_id and current_definition and hasattr(current_definition, 'id'):
                if current_definition.id != target_id:
                    should_load = True
                    logger.info(f"Loading definition {target_id} - different from current {current_definition.id}")

            if should_load:
                # Probeer sessie te starten zodat geschiedenis/auto-save beschikbaar zijn
                session = self.edit_service.start_edit_session(
                    target_id,
                    user=SessionStateManager.get_value('user') or 'system'
                )
                if session and session.get('success'):
                    SessionStateManager.set_value('editing_definition', session.get('definition'))
                    SessionStateManager.set_value('edit_session', session)

                    # Check of er contexten zijn meegegeven vanuit de generator tab
                    # Dit zorgt ervoor dat de contexten automatisch ingevuld worden
                    edit_org_context = SessionStateManager.get_value('edit_organisatorische_context')
                    edit_jur_context = SessionStateManager.get_value('edit_juridische_context')
                    edit_wet_context = SessionStateManager.get_value('edit_wettelijke_basis')

                    if edit_org_context or edit_jur_context or edit_wet_context:
                        # Log dat we contexten hebben gevonden
                        logger.info(f"Loading contexts from generator tab for definition {target_id}")

                        # Toon melding aan gebruiker
                        st.info("📋 Contexten van gegenereerde definitie zijn automatisch ingevuld")

                        # Clear de tijdelijke context variabelen na gebruik
                        # Dit voorkomt dat oude contexten blijven hangen
                        SessionStateManager.clear_value('edit_organisatorische_context')
                        SessionStateManager.clear_value('edit_juridische_context')
                        SessionStateManager.clear_value('edit_wettelijke_basis')
        except Exception as e:
            logger.error(f"Error in edit tab auto-load: {e}")
            pass

        # Main layout
        col1, col2 = st.columns([2, 1])

        with col1:
            # Definition selector and editor
            self._render_definition_selector()

            if SessionStateManager.get_value('editing_definition_id'):
                self._render_editor()
                self._render_action_buttons()

        with col2:
            # Sidebar with metadata and history
            if SessionStateManager.get_value('editing_definition_id'):
                self._render_metadata_panel()
                self._render_version_history()

        # Auto-save status
        self._render_auto_save_status()

    def _render_definition_selector(self):
        """Render definition selection interface."""
        st.markdown("### 📋 Selecteer Definitie")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Search box
            search_term = st.text_input(
                "Zoek definitie",
                placeholder="Typ begrip of deel van definitie...",
                key="edit_search_term"
            )

        with col2:
            # Status filter (NL labels → codes)
            status_options = {
                "Alle": None,
                "Geïmporteerd": "imported",
                "Concept": "draft",
                "In review": "review",
                "Vastgesteld": "established",
                "Gearchiveerd": "archived",
            }
            status_label = st.selectbox(
                "Status",
                list(status_options.keys()),
                key="edit_status_filter"
            )

        with col3:
            # Search button
            if st.button("🔍 Zoek", key="edit_search_btn"):
                # Gebruik het geselecteerde label als filter (mapping gebeurt in zoekfunctie)
                self._search_definitions(search_term, status_label)

        # Display search results
        if SessionStateManager.get_value('edit_search_results') is not None:
            self._render_search_results()

    def _render_search_results(self):
        """Render search results."""
        results = SessionStateManager.get_value('edit_search_results')

        if not results:
            st.info("Geen definities gevonden.")
            return

        st.markdown(f"**{len(results)} resultaten gevonden:**")

        for idx, definition in enumerate(results[:10]):  # Limit to 10 results
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{definition.begrip}**")
                st.caption(f"{definition.definitie[:100]}...")

            with col2:
                status = definition.metadata.get('status', 'draft') if definition.metadata else 'draft'
                self._render_status_badge(status)

            with col3:
                if st.button("✏️ Bewerk", key=f"edit_btn_{definition.id}"):
                    self._start_edit_session(definition.id)

    def _render_editor(self):
        """Render the rich text editor."""
        st.markdown("### ✏️ Bewerk Definitie")

        # Get current definition
        definition = SessionStateManager.get_value('editing_definition')
        if not definition:
            st.error("Geen definitie geselecteerd voor bewerking.")
            return

        # ID-gescope widget keys helper
        def k(name: str) -> str:
            return f"edit_{definition.id}_{name}"

        # Begrip field
        status_code = definition.metadata.get('status') if definition.metadata else None
        disabled = True if status_code in ('established', 'archived') else False

        begrip = st.text_input(
            "Begrip",
            value=definition.begrip,
            key=k("begrip"),
            disabled=disabled,
            help="Het juridische begrip dat gedefinieerd wordt"
        )

        # Rich text editor for definition
        st.markdown("**Definitie:**")

        # Use text area as fallback (st_quill requires additional setup)
        definitie_text = st.text_area(
            "Definitie tekst",
            value=definition.definitie,
            height=200,
            key=k("definitie"),
            disabled=disabled,
            help="De volledige definitie van het begrip"
        )

        # Additional fields
        col1, col2 = st.columns(2)

        with col1:
            # Organisatorische context (multiselect met Anders...)
            ui_cfg = get_config(ConfigSection.UI)
            org_options = list(getattr(ui_cfg, 'organizational_contexts', []) or [])
            # Bepaal bron (generator-tab of definitie) en splits in bekende/overige waarden
            edit_org_from_generator = SessionStateManager.get_value('edit_organisatorische_context')
            current_org = edit_org_from_generator if (edit_org_from_generator and isinstance(edit_org_from_generator, list)) else (getattr(definition, 'organisatorische_context', []) or [])
            org_known = [v for v in current_org if v in org_options]
            org_other = [v for v in current_org if v not in org_options]
            org_default = org_known + (["Anders..."] if org_other else [])
            org_selected = st.multiselect(
                "Organisatorische Context",
                options=[*org_options, "Anders..."],
                default=org_default,
                key=k("org_multiselect"),
                disabled=disabled,
                help="Selecteer één of meer organisaties; kies Anders... voor eigen waarden (komma‑gescheiden)",
            )
            # Afkortingen-uitleg uit config (indien aanwezig)
            try:
                abbrev = getattr(ui_cfg, 'afkortingen', {}) or {}
                if abbrev:
                    with st.expander("ℹ️ Afkortingen (uitleg)", expanded=False):
                        for ak in sorted(abbrev.keys()):
                            st.markdown(f"- **{ak}** — {abbrev[ak]}")
            except Exception:
                pass
            org_custom_values = []
            if "Anders..." in org_selected:
                org_custom_raw = st.text_input(
                    "Andere organisatie(s) (komma‑gescheiden)",
                    value=", ".join(org_other) if org_other else "",
                    key=k("org_custom"),
                    disabled=disabled,
                )
                org_custom_values = [v.strip() for v in org_custom_raw.split(",") if v.strip()]
            # Schrijf de samengevoegde lijst naar session state voor save‑flow
            org_resolved = [v for v in org_selected if v != "Anders..."] + org_custom_values
            SessionStateManager.set_value(k('organisatorische_context'), org_resolved)

            # Category
            categorie = st.selectbox(
                "Categorie",
                ["type", "proces", "resultaat", "exemplaar"],
                index=["type", "proces", "resultaat", "exemplaar"].index(
                    definition.categorie or "proces"
                ),
                key=k("categorie"),
                help="Ontologische categorie van het begrip"
            )

        with col2:
            # Juridische context
            # Juridische context (multiselect met Anders...)
            jur_options = list(getattr(ui_cfg, 'legal_contexts', []) or [])
            edit_jur_from_generator = SessionStateManager.get_value('edit_juridische_context')
            current_jur = edit_jur_from_generator if (edit_jur_from_generator and isinstance(edit_jur_from_generator, list)) else (getattr(definition, 'juridische_context', []) or [])
            jur_known = [v for v in current_jur if v in jur_options]
            jur_other = [v for v in current_jur if v not in jur_options]
            jur_default = jur_known + (["Anders..."] if jur_other else [])
            jur_selected = st.multiselect(
                "Juridische Context",
                options=[*jur_options, "Anders..."],
                default=jur_default,
                key=k("jur_multiselect"),
                disabled=disabled,
                help="Selecteer rechtsgebieden; kies Anders... voor eigen waarden (komma‑gescheiden)",
            )
            jur_custom_values = []
            if "Anders..." in jur_selected:
                jur_custom_raw = st.text_input(
                    "Andere rechtsgebieden (komma‑gescheiden)",
                    value=", ".join(jur_other) if jur_other else "",
                    key=k("jur_custom"),
                    disabled=disabled,
                )
                jur_custom_values = [v.strip() for v in jur_custom_raw.split(",") if v.strip()]
            jur_resolved = [v for v in jur_selected if v != "Anders..."] + jur_custom_values
            SessionStateManager.set_value(k('juridische_context'), jur_resolved)

            # Wettelijke basis (multiselect met Anders...)
            wet_options = list(getattr(ui_cfg, 'common_laws', []) or [])
            edit_wet_from_generator = SessionStateManager.get_value('edit_wettelijke_basis')
            current_wet = edit_wet_from_generator if (edit_wet_from_generator and isinstance(edit_wet_from_generator, list)) else (getattr(definition, 'wettelijke_basis', []) or [])
            wet_known = [v for v in current_wet if v in wet_options]
            wet_other = [v for v in current_wet if v not in wet_options]
            wet_default = wet_known + (["Anders..."] if wet_other else [])
            wet_selected = st.multiselect(
                "Wettelijke Basis",
                options=[*wet_options, "Anders..."],
                default=wet_default,
                key=k("wet_multiselect"),
                disabled=disabled,
                help="Selecteer wetten; kies Anders... voor eigen waarden (komma‑gescheiden)",
            )
            wet_custom_values = []
            if "Anders..." in wet_selected:
                wet_custom_raw = st.text_input(
                    "Andere wetten (komma‑gescheiden)",
                    value=", ".join(wet_other) if wet_other else "",
                    key=k("wet_custom"),
                    disabled=disabled,
                )
                wet_custom_values = [v.strip() for v in wet_custom_raw.split(",") if v.strip()]
            wet_resolved = [v for v in wet_selected if v != "Anders..."] + wet_custom_values
            SessionStateManager.set_value(k('wettelijke_basis'), wet_resolved)

            # Status (toon ook 'imported' indien van toepassing)
            current_status = definition.metadata.get('status', 'draft') if definition.metadata else 'draft'
            status_options = ["imported", "draft", "review", "established", "archived"]
            try:
                status_index = status_options.index(current_status)
            except ValueError:
                status_index = status_options.index("draft")
            status = st.selectbox(
                "Status",
                status_options,
                index=status_index,
                key=k("status"),
                disabled=True if disabled else False,
                help="De huidige status van de definitie"
            )

        # Toelichting
        toelichting = st.text_area(
            "Toelichting (optioneel)",
            value=definition.toelichting or "",
            height=100,
            key=k("toelichting"),
            disabled=disabled,
            help="Extra uitleg of context bij de definitie"
        )

        if disabled:
            if status_code == 'established':
                st.info("🛡️ Deze definitie is Vastgesteld en daarom alleen-lezen. Zet de status via de Expert-tab terug om te bewerken.")
            elif status_code == 'archived':
                st.info("📦 Deze definitie is Gearchiveerd en daarom alleen-lezen. Herstel via de Expert-tab om te bewerken.")

        # Persist context lijsten (gebruik resolved waarden zonder 'Anders...')
        if 'org_resolved' in locals():
            SessionStateManager.set_value(k("organisatorische_context"), org_resolved)
        if 'jur_resolved' in locals():
            SessionStateManager.set_value(k("juridische_context"), jur_resolved)
        if 'wet_resolved' in locals():
            SessionStateManager.set_value(k("wettelijke_basis"), wet_resolved)

        # Track changes for auto-save
        self._track_changes()

    def _render_action_buttons(self):
        """Render action buttons for saving and validation."""
        # Reden voor wijziging (persistente input boven de knoppen) - ID-gescope
        def_id = SessionStateManager.get_value('editing_definition_id')
        def k(name: str) -> str:
            return f"edit_{def_id}_{name}"
        st.text_input("Reden voor wijziging (optioneel)", key=k("save_reason"))

        # Check ‘minstens 1 context’ voor Save‑actie
        org_list = SessionStateManager.get_value(k('organisatorische_context')) or []
        jur_list = SessionStateManager.get_value(k('juridische_context')) or []
        wet_list = SessionStateManager.get_value(k('wettelijke_basis')) or []
        can_save = bool(org_list or jur_list or wet_list)
        if not can_save:
            st.warning("Minstens één context is vereist (organisatorisch of juridisch of wettelijk) om op te slaan.")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💾 Opslaan", type="primary", key="save_btn", disabled=not can_save):
                self._save_definition()

        with col2:
            if st.button("✅ Valideren", key="validate_btn"):
                self._validate_definition()

        with col3:
            if st.button("↩️ Ongedaan maken", key="undo_btn"):
                self._undo_changes()

        with col4:
            if st.button("❌ Annuleren", key="cancel_btn"):
                self._cancel_edit()

    def _render_metadata_panel(self):
        """Render metadata panel."""
        st.markdown("### 📊 Metadata")

        definition = SessionStateManager.get_value('editing_definition')
        if not definition:
            return

        # Display metadata
        metadata = definition.metadata or {}

        # Version info
        version = metadata.get('version_number', 1)
        st.metric("Versie", f"v{version}")

        # Timestamps
        if definition.created_at:
            st.caption(f"**Aangemaakt:** {self._format_datetime(definition.created_at)}")
        if definition.updated_at:
            st.caption(f"**Laatst bewerkt:** {self._format_datetime(definition.updated_at)}")

        # Created/Updated by
        if metadata.get('created_by'):
            st.caption(f"**Aangemaakt door:** {metadata['created_by']}")
        if metadata.get('updated_by'):
            st.caption(f"**Bewerkt door:** {metadata['updated_by']}")

        # Validation score
        if metadata.get('validation_score'):
            score = metadata['validation_score']
            color = "green" if score > 0.8 else "orange" if score > 0.6 else "red"
            st.markdown(f"**Validatie Score:** :{color}[{score:.2f}]")

        # Source info
        if metadata.get('source_type'):
            st.caption(f"**Bron Type:** {metadata['source_type']}")
        if definition.bron:
            st.caption(f"**Bron Referentie:** {definition.bron}")

    def _render_version_history(self):
        """Render version history panel."""
        st.markdown("### 📜 Versiegeschiedenis")

        definition_id = SessionStateManager.get_value('editing_definition_id')
        if not definition_id:
            return

        # Get history
        history = self.edit_service.get_version_history(definition_id, limit=10)

        if not history:
            st.info("Geen geschiedenis beschikbaar.")
            return

        # Display history entries
        for entry in history:
            with st.expander(
                f"{entry.get('summary', 'Wijziging')} - {entry.get('gewijzigd_op_readable', '')}",
                expanded=False
            ):
                # Change details
                if entry.get('wijziging_reden'):
                    st.caption(f"**Reden:** {entry['wijziging_reden']}")

                # Show old vs new if available
                if entry.get('definitie_oude_waarde'):
                    st.caption("**Oude waarde:**")
                    st.text(entry['definitie_oude_waarde'][:200] + "...")

                if entry.get('definitie_nieuwe_waarde'):
                    st.caption("**Nieuwe waarde:**")
                    st.text(entry['definitie_nieuwe_waarde'][:200] + "...")

                # Revert button
                if st.button(f"↩️ Herstel", key=f"revert_{entry.get('id')}"):
                    self._revert_to_version(entry.get('id'))

    def _render_auto_save_status(self):
        """Render auto-save status indicator."""
        if not SessionStateManager.get_value('editing_definition_id'):
            return

        # Auto-save status in sidebar
        with st.sidebar:
            st.markdown("---")

            auto_save_enabled = st.checkbox(
                "Auto-save inschakelen",
                value=True,
                key="auto_save_enabled"
            )

            if auto_save_enabled:
                last_save = SessionStateManager.get_value('last_auto_save')
                if last_save:
                    time_diff = datetime.now() - last_save
                    if time_diff < timedelta(seconds=60):
                        st.success(f"✅ Auto-save: {time_diff.seconds}s geleden")
                    else:
                        minutes = time_diff.seconds // 60
                        st.info(f"💾 Auto-save: {minutes}m geleden")
                else:
                    st.info("💾 Auto-save actief")

    def _render_status_badge(self, status: str):
        """Render a status badge."""
        colors = {
            'imported': '🔵',
            'draft': '🟡',
            'review': '🟠',
            'established': '🟢',
            'archived': '⚫'
        }
        labels_nl = {
            'imported': 'Geïmporteerd',
            'draft': 'Concept',
            'review': 'In review',
            'established': 'Vastgesteld',
            'archived': 'Gearchiveerd',
        }
        st.markdown(f"{colors.get(status, '⚪')} {labels_nl.get(status, status)}")

    # Action methods

    def _search_definitions(self, search_term: str, status_filter: str):
        """Search for definitions."""
        try:
            # Build filters
            filters = {}
            # Map label → code (als we labels doorgeven)
            status_label_to_code = {
                "Alle": None,
                "Geïmporteerd": "imported",
                "Concept": "draft",
                "In review": "review",
                "Vastgesteld": "established",
                "Gearchiveerd": "archived",
            }
            status_code = status_label_to_code.get(status_filter, status_filter)
            if status_code and status_code != "Alle":
                filters['status'] = status_code

            # Search
            results = self.repository.search_with_filters(
                search_term=search_term,
                **filters,
                limit=20
            )

            SessionStateManager.set_value('edit_search_results', results)

            if results:
                st.success(f"✅ {len(results)} definities gevonden")
            else:
                st.info("Geen definities gevonden met deze criteria")

        except Exception as e:
            st.error(f"Fout bij zoeken: {str(e)}")
            logger.error(f"Search error: {e}")

    def _start_edit_session(self, definition_id: int):
        """Start edit session for a definition."""
        try:
            # Start session
            session = self.edit_service.start_edit_session(
                definition_id,
                user=SessionStateManager.get_value('user') or 'system'
            )

            if session['success']:
                SessionStateManager.set_value('editing_definition_id', definition_id)
                SessionStateManager.set_value('editing_definition', session['definition'])
                SessionStateManager.set_value('edit_session', session)

                # Check for auto-save en bied herstelknop
                if session.get('auto_save'):
                    st.info("💾 Auto-save gevonden voor deze definitie.")
                    if st.button("Herstel auto-save", key="restore_auto_save_btn"):
                        self._restore_auto_save(session['auto_save'])

                # ID-gescope widget-keys zorgen dat de juiste waarden direct getoond worden

                st.success("✅ Edit sessie gestart")
                st.rerun()
            else:
                st.error(f"Fout: {session.get('error', 'Onbekende fout')}")

        except Exception as e:
            st.error(f"Fout bij starten edit sessie: {str(e)}")
            logger.error(f"Edit session error: {e}")

    def _save_definition(self):
        """Save the edited definition."""
        try:
            definition_id = SessionStateManager.get_value('editing_definition_id')
            if not definition_id:
                st.error("Geen definitie geselecteerd")
                return
            def k(name: str) -> str:
                return f"edit_{definition_id}_{name}"

            # Collect updates - gebruik SessionStateManager.get_value voor context lijsten
            # Minimaal één context vereist
            org_list = SessionStateManager.get_value(k('organisatorische_context')) or []
            jur_list = SessionStateManager.get_value(k('juridische_context')) or []
            wet_list = SessionStateManager.get_value(k('wettelijke_basis')) or []
            if not (org_list or jur_list or wet_list):
                st.error("Minimaal één context is vereist (organisatorisch, juridisch of wettelijk)")
                return

            # Voor de overige velden gebruiken we SessionStateManager voor consistentie
            updates = {
                'begrip': SessionStateManager.get_value(k('begrip')),
                'definitie': SessionStateManager.get_value(k('definitie')),
                'organisatorische_context': org_list,
                'juridische_context': jur_list,
                'wettelijke_basis': wet_list,
                'categorie': SessionStateManager.get_value(k('categorie')),
                'toelichting': SessionStateManager.get_value(k('toelichting')),
                'status': SessionStateManager.get_value(k('status')),
            }

            # Add version number for optimistic locking
            editing_definition = SessionStateManager.get_value('editing_definition')
            if editing_definition and editing_definition.metadata:
                updates['version_number'] = editing_definition.metadata.get('version_number', 1)

            # Save
            result = self.edit_service.save_definition(
                definition_id,
                updates,
                user=SessionStateManager.get_value('user') or 'system',
                reason=SessionStateManager.get_value(k('save_reason')),
                validate=True
            )

            if result['success']:
                st.success("✅ Definitie opgeslagen!")

                # Show validation results if available
                if result.get('validation'):
                    self._show_validation_results(result['validation'])

                # Refresh definition
                self._refresh_current_definition()
            else:
                if result.get('conflict'):
                    st.error("⚠️ Versie conflict - de definitie is gewijzigd door een andere gebruiker")
                    if st.button("🔄 Ververs en probeer opnieuw"):
                        self._refresh_current_definition()
                else:
                    st.error(f"Fout bij opslaan: {result.get('error', 'Onbekende fout')}")

        except Exception as e:
            st.error(f"Fout bij opslaan: {str(e)}")
            logger.error(f"Save error: {e}")

    def _validate_definition(self):
        """Validate the current definition."""
        try:
            # Create definition object from current state
            from services.interfaces import Definition
            def_id = SessionStateManager.get_value('editing_definition_id')
            def k(name: str) -> str:
                return f"edit_{def_id}_{name}"

            definition = Definition(
                begrip=SessionStateManager.get_value(k('begrip'), ''),
                definitie=SessionStateManager.get_value(k('definitie'), ''),
                organisatorische_context=SessionStateManager.get_value(k('organisatorische_context')) or [],
                juridische_context=SessionStateManager.get_value(k('juridische_context')) or [],
                wettelijke_basis=SessionStateManager.get_value(k('wettelijke_basis')) or [],
                categorie=SessionStateManager.get_value(k('categorie'), 'proces'),
                toelichting=SessionStateManager.get_value(k('toelichting'), ''),
                metadata={
                    'status': SessionStateManager.get_value(k('status'), 'draft')
                }
            )

            # Validate
            results = self.edit_service._validate_definition(definition)

            # Als de service None teruggeeft (alleen async API beschikbaar), gebruik UI async-bridge
            if results is None:
                from services.container import get_container
                from ui.helpers.async_bridge import run_async

                container = get_container()
                orch = container.orchestrator()
                from services.validation.interfaces import ValidationContext
                vc = ValidationContext(
                    correlation_id=None,
                    metadata={
                        "organisatorische_context": definition.organisatorische_context or [],
                        "juridische_context": definition.juridische_context or [],
                        "wettelijke_basis": definition.wettelijke_basis or [],
                    },
                )
                v = run_async(
                    orch.validation_service.validate_text(
                        begrip=definition.begrip,
                        text=definition.definitie,
                        ontologische_categorie=definition.categorie,
                        context=vc,
                    )
                )
                # Normaliseer naar UI‑structuur
                if isinstance(v, dict):
                    violations = v.get("violations", []) or []
                    normalized_issues = []
                    for item in violations:
                        normalized_issues.append(
                            {
                                "rule": item.get("rule_id") or item.get("code"),
                                "message": item.get("description") or item.get("message", ""),
                                "severity": item.get("severity", "warning"),
                            }
                        )
                    results = {
                        "valid": bool(v.get("is_acceptable", False)),
                        "score": float(v.get("overall_score", 0.0) or 0.0),
                        "issues": normalized_issues,
                        "raw_v2": v,
                    }

            if results:
                self._show_validation_results(results)
            else:
                st.info("Validatie service niet beschikbaar")

        except Exception as e:
            st.error(f"Fout bij validatie: {str(e)}")
            logger.error(f"Validation error: {e}")

    def _show_validation_results(self, results: Dict[str, Any]):
        """Show validation results."""
        if results['valid']:
            st.success(f"✅ Validatie geslaagd! Score: {results['score']:.2f}")
        else:
            st.warning(f"⚠️ Validatie problemen gevonden. Score: {results['score']:.2f}")

            if results.get('issues'):
                with st.expander("Bekijk validatie problemen"):
                    issues_sorted = sorted(
                        list(results['issues']),
                        key=lambda it: self._rule_sort_key(str(it.get('rule') or '')),
                    )
                    for idx, issue in enumerate(issues_sorted):
                        severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
                        rule_id = str(issue.get('rule') or '')
                        st.markdown(f"{severity_icon} **{rule_id}:** {issue['message']}")

                        # Hint/uitleg per regel (best-effort uit JSON + link naar handleiding)
                        with st.expander(f"ℹ️ Toon uitleg voor {rule_id}", expanded=False):
                            st.markdown(self._build_rule_hint_markdown(rule_id))

        # Uitleg bij alle geëvalueerde regels (indien raw V2 resultaat aanwezig), ook bij geslaagde validatie
        try:
            v2 = results.get('raw_v2') if isinstance(results, dict) else None
            if isinstance(v2, dict):
                violations = list(v2.get('violations') or [])
                passed = list(v2.get('passed_rules') or [])
                all_rids: set[str] = set()
                for v in violations:
                    rid = str(v.get('rule_id') or v.get('code') or '').strip()
                    if rid:
                        all_rids.add(rid)
                for rid in passed:
                    r = str(rid or '').strip()
                    if r:
                        all_rids.add(r)
                if all_rids:
                    st.markdown("### ℹ️ Uitleg bij alle geëvalueerde regels")
                    for rid in sorted(all_rids, key=self._rule_sort_key):
                        with st.expander(f"ℹ️ Toon uitleg voor {rid}", expanded=False):
                            st.markdown(self._build_rule_hint_markdown(rid))
        except Exception:
            pass

    def _build_rule_hint_markdown(self, rule_id: str) -> str:
        """Bouw korte hint-uitleg voor een toetsregel uit JSON en standaardtekst.

        Toont:
        - Wat toetst de regel (uitleg/toetsvraag)
        - Optioneel voorbeelden (goed/fout) als bullets
        - Link naar uitgebreide handleiding
        """
        try:
            from pathlib import Path
            import json as _json

            rules_dir = Path("src/toetsregels/regels")
            json_path = rules_dir / f"{rule_id}.json"
            if not json_path.exists():
                alt = rule_id.replace("_", "-")
                json_path = rules_dir / f"{alt}.json"

            name = explanation = ""
            good = bad = []
            if json_path.exists():
                data = _json.loads(json_path.read_text(encoding="utf-8"))
                name = str(data.get("naam") or "").strip()
                explanation = str(data.get("uitleg") or data.get("toetsvraag") or "").strip()
                good = list(data.get("goede_voorbeelden") or [])
                bad = list(data.get("foute_voorbeelden") or [])

            lines = []
            title = f"**{rule_id}** — {name}" if name else f"**{rule_id}**"
            lines.append(title)
            if explanation:
                lines.append(f"Wat toetst: {explanation}")
            if good:
                lines.append("\nGoed voorbeeld:")
                lines.extend([f"- {g}" for g in good[:2]])
            if bad:
                lines.append("\nFout voorbeeld:")
                lines.extend([f"- {b}" for b in bad[:2]])
            lines.append(
                "\nMeer uitleg: [Validatieregels (CON‑01 e.a.)](docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )
            return "\n".join(lines)
        except Exception:
            return (
                f"Meer uitleg: [Validatieregels (CON‑01 e.a.)]"
                f"(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )

    def _rule_sort_key(self, rule_id: str):
        """Zelfde groeperings- en sorteersleutel als generator-tab."""
        rid = (rule_id or "").upper().replace("_", "-")
        prefix = rid.split("-", 1)[0] if "-" in rid else rid[:4]
        order = {
            "CON": 0,
            "ESS": 1,
            "STR": 2,
            "INT": 3,
            "SAM": 4,
            "ARAI": 5,
            "VER": 6,
            "VAL": 7,
        }
        grp = order.get(prefix, 99)
        num = 9999
        try:
            tail = rid.split("-", 1)[1] if "-" in rid else ""
            import re as _re
            m = _re.search(r"(\d+)", tail)
            if m:
                num = int(m.group(1))
        except Exception:
            num = 9999
        return (grp, num, rid)

    def _undo_changes(self):
        """Undo recent changes."""
        try:
            # Reload original definition
            definition_id = SessionStateManager.get_value('editing_definition_id')
            if definition_id:
                definition = self.repository.get(definition_id)
                if definition:
                    SessionStateManager.set_value('editing_definition', definition)
                    st.success("✅ Wijzigingen ongedaan gemaakt")
                    st.rerun()

        except Exception as e:
            st.error(f"Fout bij ongedaan maken: {str(e)}")
            logger.error(f"Undo error: {e}")

    def _cancel_edit(self):
        """Cancel the edit session."""
        # Clear edit state using SessionStateManager
        for key in ['editing_definition_id', 'editing_definition', 'edit_session']:
            SessionStateManager.set_value(key, None)

        st.info("Edit sessie geannuleerd")
        st.rerun()

    def _revert_to_version(self, version_id: int):
        """Revert to a specific version."""
        try:
            definition_id = SessionStateManager.get_value('editing_definition_id')
            if not definition_id:
                return

            result = self.edit_service.revert_to_version(
                definition_id,
                version_id,
                user=SessionStateManager.get_value('user') or 'system'
            )

            if result['success']:
                st.success("✅ Definitie hersteld naar eerdere versie")
                self._refresh_current_definition()
            else:
                st.error(f"Fout bij herstellen: {result.get('error', 'Onbekende fout')}")

        except Exception as e:
            st.error(f"Fout bij herstellen: {str(e)}")
            logger.error(f"Revert error: {e}")

    def _refresh_current_definition(self):
        """Refresh the current definition from database."""
        try:
            definition_id = SessionStateManager.get_value('editing_definition_id')
            if definition_id:
                definition = self.repository.get(definition_id)
                if definition:
                    SessionStateManager.set_value('editing_definition', definition)
                    st.rerun()

        except Exception as e:
            logger.error(f"Refresh error: {e}")

    def _track_changes(self):
        """Track changes for auto-save."""
        auto_save_enabled = SessionStateManager.get_value('auto_save_enabled')
        if not auto_save_enabled:
            return

        # Check if content changed
        definition = SessionStateManager.get_value('editing_definition')
        if not definition:
            return

        def k(name: str) -> str:
            return f"edit_{definition.id}_{name}"
        changed = False

        # Check each field for changes (widget keys nog steeds in st.session_state)
        fields_to_check = [
            (k('begrip'), 'begrip'),
            (k('definitie'), 'definitie'),
            (k('categorie'), 'categorie'),
            (k('toelichting'), 'toelichting'),
        ]
        # Vergelijk ook V2 contextlijsten (genormaliseerd)
        def _norm_list(v):
            try:
                return sorted([str(x).strip() for x in (v or [])])
            except Exception:
                return []

        for session_key, def_attr in fields_to_check:
            session_value = SessionStateManager.get_value(session_key)
            def_value = getattr(definition, def_attr, None)
            if session_value != def_value:
                changed = True
                break

        if not changed:
            # Check contextlijsten via SessionStateManager
            if _norm_list(SessionStateManager.get_value(k('organisatorische_context'))) != _norm_list(getattr(definition, 'organisatorische_context', [])):
                changed = True
            elif _norm_list(SessionStateManager.get_value(k('juridische_context'))) != _norm_list(getattr(definition, 'juridische_context', [])):
                changed = True
            elif _norm_list(SessionStateManager.get_value(k('wettelijke_basis'))) != _norm_list(getattr(definition, 'wettelijke_basis', [])):
                changed = True

        # Auto-save if changed and interval verstreken
        if changed:
            last = SessionStateManager.get_value('last_auto_save')
            if last:
                try:
                    elapsed = datetime.now() - last
                    if elapsed.total_seconds() < 30:
                        return  # throttle
                except Exception:
                    pass
            self._perform_auto_save()

    def _perform_auto_save(self):
        """Perform auto-save."""
        try:
            definition_id = SessionStateManager.get_value('editing_definition_id')
            if not definition_id:
                return
            def k(name: str) -> str:
                return f"edit_{definition_id}_{name}"

            # Collect current state - gebruik SessionStateManager
            content = {
                'begrip': SessionStateManager.get_value(k('begrip')),
                'definitie': SessionStateManager.get_value(k('definitie')),
                'organisatorische_context': SessionStateManager.get_value(k('organisatorische_context')),
                'juridische_context': SessionStateManager.get_value(k('juridische_context')),
                'wettelijke_basis': SessionStateManager.get_value(k('wettelijke_basis')),
                'categorie': SessionStateManager.get_value(k('categorie')),
                'toelichting': SessionStateManager.get_value(k('toelichting')),
                'status': SessionStateManager.get_value(k('status')),
            }

            # Save
            if self.edit_service.auto_save(definition_id, content):
                SessionStateManager.set_value('last_auto_save', datetime.now())

        except Exception as e:
            logger.error(f"Auto-save error: {e}")

    def _restore_auto_save(self, auto_save_content: Dict[str, Any]):
        """Restore from auto-save."""
        try:
            def_id = SessionStateManager.get_value('editing_definition_id')
            def k(name: str) -> str:
                return f"edit_{def_id}_{name}"
            # Update session state with auto-save content - hybride aanpak
            field_mapping = {
                'begrip': k('begrip'),
                'definitie': k('definitie'),
                'categorie': k('categorie'),
                'toelichting': k('toelichting'),
                'status': k('status'),
            }
            # Context lijsten via SessionStateManager
            context_mapping = {
                'organisatorische_context': k('organisatorische_context'),
                'juridische_context': k('juridische_context'),
                'wettelijke_basis': k('wettelijke_basis'),
            }

            # Backward compat: map legacy 'context' naar organisatorische_context indien aanwezig
            if 'context' in auto_save_content and 'organisatorische_context' not in auto_save_content:
                auto_save_content['organisatorische_context'] = auto_save_content.get('context')

            # Widget fields naar SessionStateManager
            for field, session_key in field_mapping.items():
                if field in auto_save_content:
                    SessionStateManager.set_value(session_key, auto_save_content[field])

            # Context lijsten naar SessionStateManager
            for field, session_key in context_mapping.items():
                if field in auto_save_content:
                    SessionStateManager.set_value(session_key, auto_save_content[field])

            st.success("✅ Auto-save hersteld")

        except Exception as e:
            st.error(f"Fout bij herstellen auto-save: {str(e)}")
            logger.error(f"Restore auto-save error: {e}")

    def _format_datetime(self, dt) -> str:
        """Format datetime for display."""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except (ValueError, TypeError):
                return dt

        if isinstance(dt, datetime):
            return dt.strftime("%d-%m-%Y %H:%M")

        return str(dt)

    # _hydrate_editor_fields verwijderd: niet nodig met ID-gescope widget keys

    def _ensure_edit_session_state(self):
        """Ensure edit session state variables exist via SessionStateManager."""
        # Gebruik SessionStateManager voor consistentie met de rest van de applicatie
        edit_defaults = {
            'editing_definition_id': None,
            'editing_definition': None,
            'edit_session': None,
            'edit_search_results': [],
            'last_auto_save': None,
            'auto_save_enabled': True,
        }

        # Gebruik SessionStateManager voor alle edit-specifieke defaults
        for key, default_value in edit_defaults.items():
            if SessionStateManager.get_value(key) is None:
                SessionStateManager.set_value(key, default_value)
