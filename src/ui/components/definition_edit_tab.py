"""
Definition Edit Tab - Rich text editor interface voor definities.

Deze tab biedt een gebruiksvriendelijke interface voor het bewerken
van definities met ondersteuning voor versiegeschiedenis en auto-save.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from config.config_manager import ConfigSection, get_config
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.validation.modular_validation_service import ModularValidationService
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class DefinitionEditTab:
    """Tab voor het bewerken van definities met rich text editor."""

    def __init__(
        self,
        repository: DefinitionEditRepository = None,
        validation_service: ModularValidationService = None,
    ):
        """
        Initialiseer definition edit tab.

        Args:
            repository: Repository voor data toegang
            validation_service: Service voor validatie
        """
        self.repository = repository or DefinitionEditRepository()
        self.edit_service = DefinitionEditService(
            repository=self.repository, validation_service=validation_service
        )

        # Initialize session state via SessionStateManager
        self._ensure_edit_session_state()

        logger.info("DefinitionEditTab initialized")

    def render(self):
        """Render de edit tab interface."""
        st.markdown("## ✏️ Definitie Editor")
        st.markdown(
            "Bewerk definities met een rijke text editor, versiegeschiedenis en auto-save functionaliteit."
        )

        # Auto-start bewerksessie als er al een target ID is gezet (bijv. via generator-tab)
        try:
            target_id = SessionStateManager.get_value("editing_definition_id")
            current_definition = SessionStateManager.get_value("editing_definition")

            # Check of we een nieuwe definitie moeten laden
            # Dit gebeurt als:
            # 1. Er is een target_id EN geen huidige definitie, OF
            # 2. Er is een target_id EN het is een andere definitie dan de huidige
            should_load = False
            if target_id and not current_definition:
                should_load = True
                logger.info(f"Loading definition {target_id} - no current definition")
            elif target_id and current_definition and hasattr(current_definition, "id"):
                if current_definition.id != target_id:
                    should_load = True
                    logger.info(
                        f"Loading definition {target_id} - different from current {current_definition.id}"
                    )

            if should_load:
                # Probeer sessie te starten zodat geschiedenis/auto-save beschikbaar zijn
                session = self.edit_service.start_edit_session(
                    target_id, user=SessionStateManager.get_value("user") or "system"
                )
                if session and session.get("success"):
                    SessionStateManager.set_value(
                        "editing_definition", session.get("definition")
                    )
                    SessionStateManager.set_value("edit_session", session)

                    # Check of er contexten zijn meegegeven vanuit de generator tab
                    # Dit zorgt ervoor dat de contexten automatisch ingevuld worden
                    edit_org_context = SessionStateManager.get_value(
                        "edit_organisatorische_context"
                    )
                    edit_jur_context = SessionStateManager.get_value(
                        "edit_juridische_context"
                    )
                    edit_wet_context = SessionStateManager.get_value(
                        "edit_wettelijke_basis"
                    )

                    if edit_org_context or edit_jur_context or edit_wet_context:
                        # Log dat we contexten hebben gevonden
                        logger.info(
                            f"Loading contexts from generator tab for definition {target_id}"
                        )

                        # Toon melding aan gebruiker
                        st.info(
                            "📋 Contexten van gegenereerde definitie zijn automatisch ingevuld"
                        )

                        # Clear de tijdelijke context variabelen na gebruik
                        # Dit voorkomt dat oude contexten blijven hangen
                        SessionStateManager.clear_value("edit_organisatorische_context")
                        SessionStateManager.clear_value("edit_juridische_context")
                        SessionStateManager.clear_value("edit_wettelijke_basis")
        except Exception as e:
            logger.error(f"Error in edit tab auto-load: {e}")

        # Main layout
        col1, col2 = st.columns([2, 1])

        with col1:
            # Definition selector and editor
            self._render_definition_selector()

            if SessionStateManager.get_value("editing_definition_id"):
                self._render_editor()
                self._render_action_buttons()
                self._render_examples_section()

        with col2:
            # Sidebar with metadata and history
            if SessionStateManager.get_value("editing_definition_id"):
                self._render_metadata_panel()
                self._render_version_history()

        # Auto-save status
        self._render_auto_save_status()

    def _render_definition_selector(self):
        """Render definition selection interface."""
        st.markdown("### 📋 Selecteer Definitie")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            # Search box
            search_term = st.text_input(
                "Zoek definitie",
                placeholder="Typ begrip of deel van definitie...",
                key="edit_search_term",
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
                "Status", list(status_options.keys()), key="edit_status_filter"
            )

        with col3:
            max_results = st.selectbox(
                "Max resultaten",
                options=[10, 25, 50, 100, 200],
                index=2,
                key="edit_max_results",
                help="Aantal resultaten om op te halen en te tonen",
            )

        with col4:
            # Search button
            if st.button("🔍 Zoek", key="edit_search_btn"):
                # Gebruik het geselecteerde label als filter (mapping gebeurt in zoekfunctie)
                self._search_definitions(search_term, status_label, max_results)

        # Auto-load: toon standaard de meest recente definities wanneer er nog niet gezocht is
        try:
            current_results = SessionStateManager.get_value("edit_search_results")
        except Exception:
            current_results = None

        if (not current_results) and (not search_term) and status_label == "Alle":
            # Haal de laatste N definities op zonder filters (discovery)
            self._search_definitions("", "Alle", max_results)

        # Display search results
        if SessionStateManager.get_value("edit_search_results") is not None:
            self._render_search_results()

    def _render_search_results(self):
        """Render search results."""
        results = SessionStateManager.get_value("edit_search_results")

        if not results:
            st.info("Geen definities gevonden.")
            return

        st.markdown(f"**{len(results)} resultaten gevonden:**")

        # Kies weergave: interactieve lijst of tabel (selecteerbaar)
        show_table = st.checkbox(
            "Toon tabelweergave",
            value=True,
            key="edit_show_table",
            help="Schakel in voor compacte tabelweergave met selecteerbare rijen",
        )

        if show_table:
            # Tabelweergave (selecteerbaar via checkbox kolom, enkelvoudige selectie)
            try:
                import pandas as pd  # Lazy import voor UI

                def _join_list(v):
                    try:
                        return ", ".join([str(x) for x in (v or [])])
                    except Exception:
                        return ""

                rows = []

                def _status_label(code: str | None, source_type: str | None) -> str:
                    # Toon 'Geïmporteerd' als herkomst imported is, anders vertaal status
                    if (source_type or "").lower() == "imported":
                        return "Geïmporteerd"
                    mapping = {
                        "draft": "Concept",
                        "review": "In review",
                        "established": "Vastgesteld",
                        "archived": "Gearchiveerd",
                    }
                    return mapping.get((code or "").lower(), code or "")

                def _source_label(src: str | None) -> str:
                    m = {
                        "imported": "Geïmporteerd",
                        "generated": "Gegenereerd",
                        "manual": "Handmatig",
                    }
                    return m.get((src or "").lower(), src or "")

                prev_selected_id = SessionStateManager.get_value("edit_selected_id")
                for d in results:
                    status = (
                        d.metadata.get("status") if d.metadata else None
                    ) or "draft"
                    source_type = d.metadata.get("source_type") if d.metadata else None
                    status_disp = _status_label(status, source_type)
                    score = d.metadata.get("validation_score") if d.metadata else None
                    rows.append(
                        {
                            "Selecteer": bool(prev_selected_id == d.id),
                            "ID": d.id,
                            "Begrip": d.begrip,
                            "Categorie": d.categorie or "",
                            "UFO-categorie": getattr(d, "ufo_categorie", None) or "",
                            "Status": status_disp,
                            "Herkomst": _source_label(source_type),
                            "Score": score if score is not None else "",
                            "Organisatorische context": _join_list(
                                getattr(d, "organisatorische_context", [])
                            ),
                            "Juridische context": _join_list(
                                getattr(d, "juridische_context", [])
                            ),
                            "Wettelijke basis": _join_list(
                                getattr(d, "wettelijke_basis", [])
                            ),
                        }
                    )

                df = pd.DataFrame(rows)
                edited = st.data_editor(
                    df,
                    use_container_width=True,
                    height=420,
                    hide_index=True,
                    column_config={
                        "Selecteer": st.column_config.CheckboxColumn(
                            "Selecteer",
                            help="Kies één rij en klik op 'Bewerk geselecteerde'",
                            default=False,
                        ),
                        "ID": st.column_config.TextColumn(disabled=True),
                        "Begrip": st.column_config.TextColumn(disabled=True),
                        "Categorie": st.column_config.TextColumn(disabled=True),
                        "UFO-categorie": st.column_config.TextColumn(disabled=True),
                        "Status": st.column_config.TextColumn(disabled=True),
                        "Herkomst": st.column_config.TextColumn(disabled=True),
                        "Score": st.column_config.TextColumn(disabled=True),
                        "Organisatorische context": st.column_config.TextColumn(
                            disabled=True
                        ),
                        "Juridische context": st.column_config.TextColumn(
                            disabled=True
                        ),
                        "Wettelijke basis": st.column_config.TextColumn(disabled=True),
                    },
                )

                # Enforce enkelvoudige selectie: kies vorige selectie als aanwezig, anders de eerste True
                try:
                    true_ids = [
                        int(r["ID"])
                        for _, r in edited.iterrows()
                        if bool(r.get("Selecteer"))
                    ]
                except Exception:
                    true_ids = []

                selected_id = prev_selected_id
                if len(true_ids) == 1:
                    selected_id = true_ids[0]
                elif len(true_ids) >= 2:
                    # Behoud vorige selectie indien nog aanwezig, anders pak de eerste
                    if prev_selected_id in true_ids:
                        selected_id = prev_selected_id
                    else:
                        selected_id = true_ids[0]
                    st.caption(
                        "Er kan maar één rij geselecteerd zijn; selectie gecorrigeerd."
                    )
                # Update session state
                SessionStateManager.set_value("edit_selected_id", selected_id)

                col_sel, _ = st.columns([1, 3])
                with col_sel:
                    if st.button(
                        "✏️ Bewerk geselecteerde",
                        key="edit_btn_selected_table",
                        disabled=selected_id is None,
                    ):
                        self._start_edit_session(int(selected_id))
            except Exception as e:
                st.warning(f"Kon tabelweergave niet renderen: {e!s}")

        # Interactieve lijstweergave met direct selecteerbare items (alleen tonen als tabel uit staat)
        if not show_table:
            # Alternatieve lijstweergave met NL-statuslabels
            for d in results:
                with st.container():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        status = (
                            d.metadata.get("status") if d.metadata else None
                        ) or "draft"
                        source_type = (
                            d.metadata.get("source_type") if d.metadata else None
                        )
                        mapping = {
                            "draft": "Concept",
                            "review": "In review",
                            "established": "Vastgesteld",
                            "archived": "Gearchiveerd",
                        }
                        status_disp = (
                            "Geïmporteerd"
                            if (source_type or "").lower() == "imported"
                            else mapping.get((status or "").lower(), status or "")
                        )
                        st.markdown(
                            f"**[{d.id}] {d.begrip}** — {d.categorie or ''} · {status_disp}"
                        )
                        # Kleine contextregel
                        try:
                            org = ", ".join(
                                getattr(d, "organisatorische_context", []) or []
                            )
                            jur = ", ".join(getattr(d, "juridische_context", []) or [])
                            if org or jur:
                                st.caption(f"Org: {org or '—'} · Jur: {jur or '—'}")
                        except Exception:
                            pass
                    with c2:
                        if st.button("✏️ Bewerk", key=f"edit_btn_{d.id}"):
                            self._start_edit_session(int(d.id))
                st.markdown("---")

    def _render_editor(self):
        """Render the rich text editor."""
        st.markdown("### ✏️ Bewerk Definitie")

        # Get current definition
        definition = SessionStateManager.get_value("editing_definition")
        if not definition:
            st.error("Geen definitie geselecteerd voor bewerking.")
            return

        # ID-gescope widget keys helper
        def k(name: str) -> str:
            return f"edit_{definition.id}_{name}"

        # Begrip field
        status_code = definition.metadata.get("status") if definition.metadata else None
        disabled = status_code in ("established", "archived")

        begrip = st.text_input(
            "Begrip",
            value=definition.begrip,
            key=k("begrip"),
            disabled=disabled,
            help="Het juridische begrip dat gedefinieerd wordt",
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
            help="De volledige definitie van het begrip",
        )

        # Additional fields
        col1, col2 = st.columns(2)

        with col1:
            # Organisatorische context (multiselect met Anders...)
            ui_cfg = get_config(ConfigSection.UI)
            org_options = list(getattr(ui_cfg, "organizational_contexts", []) or [])
            # Bepaal bron (generator-tab of definitie) en splits in bekende/overige waarden
            edit_org_from_generator = SessionStateManager.get_value(
                "edit_organisatorische_context"
            )
            current_org = (
                edit_org_from_generator
                if (
                    edit_org_from_generator
                    and isinstance(edit_org_from_generator, list)
                )
                else (getattr(definition, "organisatorische_context", []) or [])
            )
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
                abbrev = getattr(ui_cfg, "afkortingen", {}) or {}
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
                org_custom_values = [
                    v.strip() for v in org_custom_raw.split(",") if v.strip()
                ]
            # Schrijf de samengevoegde lijst naar session state voor save‑flow
            org_resolved = [
                v for v in org_selected if v != "Anders..."
            ] + org_custom_values
            SessionStateManager.set_value(k("organisatorische_context"), org_resolved)

            # Category
            categorie = st.selectbox(
                "Categorie",
                ["type", "proces", "resultaat", "exemplaar"],
                index=["type", "proces", "resultaat", "exemplaar"].index(
                    definition.categorie or "proces"
                ),
                key=k("categorie"),
                help="Ontologische categorie van het begrip",
            )

            # UFO‑categorie selectie (onder ontologische categorie)
            ufo_opties = [
                "",
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
            try:
                current_ufo = getattr(definition, "ufo_categorie", None) or ""
                ufo_default_index = (
                    ufo_opties.index(current_ufo) if current_ufo in ufo_opties else 0
                )
            except Exception:
                ufo_default_index = 0
            ufo_selected = st.selectbox(
                "UFO‑categorie",
                options=ufo_opties,
                index=ufo_default_index,
                key=k("ufo_categorie"),
                disabled=disabled,
                help="Selecteer de UFO‑categorie (OntoUML/UFO metamodel)",
            )

        with col2:
            # Juridische context
            # Juridische context (multiselect met Anders...)
            jur_options = list(getattr(ui_cfg, "legal_contexts", []) or [])
            edit_jur_from_generator = SessionStateManager.get_value(
                "edit_juridische_context"
            )
            current_jur = (
                edit_jur_from_generator
                if (
                    edit_jur_from_generator
                    and isinstance(edit_jur_from_generator, list)
                )
                else (getattr(definition, "juridische_context", []) or [])
            )
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
                jur_custom_values = [
                    v.strip() for v in jur_custom_raw.split(",") if v.strip()
                ]
            jur_resolved = [
                v for v in jur_selected if v != "Anders..."
            ] + jur_custom_values
            SessionStateManager.set_value(k("juridische_context"), jur_resolved)

            # Wettelijke basis (multiselect met Anders...)
            wet_options = list(getattr(ui_cfg, "common_laws", []) or [])
            edit_wet_from_generator = SessionStateManager.get_value(
                "edit_wettelijke_basis"
            )
            current_wet = (
                edit_wet_from_generator
                if (
                    edit_wet_from_generator
                    and isinstance(edit_wet_from_generator, list)
                )
                else (getattr(definition, "wettelijke_basis", []) or [])
            )
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
                wet_custom_values = [
                    v.strip() for v in wet_custom_raw.split(",") if v.strip()
                ]
            wet_resolved = [
                v for v in wet_selected if v != "Anders..."
            ] + wet_custom_values
            SessionStateManager.set_value(k("wettelijke_basis"), wet_resolved)

            # Status (toon ook 'imported' indien van toepassing)
            current_status = (
                definition.metadata.get("status", "draft")
                if definition.metadata
                else "draft"
            )
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
                disabled=bool(disabled),
                help="De huidige status van de definitie",
            )

        # Toelichting
        toelichting = st.text_area(
            "Toelichting (optioneel)",
            value=definition.toelichting or "",
            height=100,
            key=k("toelichting"),
            disabled=disabled,
            help="Extra uitleg of context bij de definitie",
        )

        if disabled:
            if status_code == "established":
                st.info(
                    "🛡️ Deze definitie is Vastgesteld en daarom alleen-lezen. Zet de status via de Expert-tab terug om te bewerken."
                )
            elif status_code == "archived":
                st.info(
                    "📦 Deze definitie is Gearchiveerd en daarom alleen-lezen. Herstel via de Expert-tab om te bewerken."
                )

        # Persist context lijsten (gebruik resolved waarden zonder 'Anders...')
        if "org_resolved" in locals():
            SessionStateManager.set_value(k("organisatorische_context"), org_resolved)
        if "jur_resolved" in locals():
            SessionStateManager.set_value(k("juridische_context"), jur_resolved)
        if "wet_resolved" in locals():
            SessionStateManager.set_value(k("wettelijke_basis"), wet_resolved)

        # Track changes for auto-save
        self._track_changes()

    def _render_action_buttons(self):
        """Render action buttons for saving and validation."""
        # Reden voor wijziging (persistente input boven de knoppen) - ID-gescope
        def_id = SessionStateManager.get_value("editing_definition_id")

        def k(name: str) -> str:
            return f"edit_{def_id}_{name}"

        st.text_input("Reden voor wijziging (optioneel)", key=k("save_reason"))

        # Check ‘minstens 1 context’ voor Save‑actie
        org_list = SessionStateManager.get_value(k("organisatorische_context")) or []
        jur_list = SessionStateManager.get_value(k("juridische_context")) or []
        wet_list = SessionStateManager.get_value(k("wettelijke_basis")) or []
        can_save = bool(org_list or jur_list or wet_list)
        if not can_save:
            st.warning(
                "Minstens één context is vereist (organisatorisch of juridisch of wettelijk) om op te slaan."
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(
                "💾 Opslaan", type="primary", key="save_btn", disabled=not can_save
            ):
                self._save_definition()

        with col2:
            if st.button("✅ Valideren", key="validate_btn"):
                results = self._validate_definition()
                if results:
                    # Sla op in session en render buiten kolommen (full-width)
                    SessionStateManager.set_value("edit_last_validation", results)
                    st.rerun()
                else:
                    st.info("Validatie service niet beschikbaar")

        with col3:
            if st.button("↩️ Ongedaan maken", key="undo_btn"):
                self._undo_changes()

        with col4:
            if st.button("❌ Annuleren", key="cancel_btn"):
                self._cancel_edit()

        # Full-width panel (onder de knoppen) voor validatieresultaten
        self._render_fullwidth_validation_results()

    def _render_examples_section(self):
        """Render sectie voor AI-gegenereerde voorbeelden (edit-tab)."""
        def_id = SessionStateManager.get_value("editing_definition_id")
        if not def_id:
            return
        definition = SessionStateManager.get_value("editing_definition")
        if not definition:
            return

        # Toon voorbeelden sectie met mooie layout zoals in Generator tab
        st.markdown("### 📚 Voorbeelden & Synoniemen")

        # Gebruik het gedeelde voorbeelden-blok
        from database.definitie_repository import DefinitieRepository
        from ui.components.examples_block import render_examples_block

        # Get repository voor edit functionaliteit
        repo = DefinitieRepository()

        # Render voorbeelden met edit mogelijkheid
        with st.expander("📋 Voorbeelden Details", expanded=True):
            render_examples_block(
                definition,
                state_prefix=f"edit_{def_id}",
                allow_generate=True,
                allow_edit=True,  # Enable editing including voorkeursterm selector
                repository=repo,  # Pass repository for saving
            )

        # Extra prominente voorkeursterm weergave als er synoniemen zijn
        try:
            if repo and definition.id:
                voorbeelden_dict = repo.get_voorbeelden_by_type(definition.id)
                synoniemen = voorbeelden_dict.get("synonyms", [])

                if synoniemen:
                    st.markdown("### 🔁 Voorkeursterm Status")
                    voorkeursterm = repo.get_voorkeursterm(definition.id)
                    if voorkeursterm:
                        st.success(f"✅ Huidige voorkeursterm: **{voorkeursterm}**")
                    else:
                        # Consistent met generator-tab: als gebruiker 'begrip' selecteert is er geen DB-flag.
                        try:
                            from ui.session_state import SessionStateManager as _SSM

                            sess_vt = _SSM.get_value("voorkeursterm", "")
                            if sess_vt and str(sess_vt).strip() == str(
                                getattr(definition, "begrip", "") or ""
                            ):
                                st.success(
                                    f"✅ Huidige voorkeursterm: **{getattr(definition, 'begrip', '')}**"
                                )
                            else:
                                st.info(
                                    "ℹ️ Geen voorkeursterm geselecteerd. Gebruik de selector hierboven om er een te kiezen."
                                )
                        except Exception:
                            st.info(
                                "ℹ️ Geen voorkeursterm geselecteerd. Gebruik de selector hierboven om er een te kiezen."
                            )
        except Exception as e:
            logger.debug(f"Could not show voorkeursterm status: {e}")

    def _render_metadata_panel(self):
        """Render compact metadata panel."""
        definition = SessionStateManager.get_value("editing_definition")
        if not definition:
            return

        metadata = definition.metadata or {}
        version = metadata.get("version_number", 1)

        # Compact summary line
        updated = (
            self._format_datetime(definition.updated_at)
            if definition.updated_at
            else "Nooit"
        )
        st.caption(f"**Versie v{version}** • Laatst bewerkt: {updated}")

        # Full metadata in collapsed expander
        with st.expander("📊 Volledige metadata", expanded=False):
            # Timestamps
            if definition.created_at:
                st.caption(
                    f"**Aangemaakt:** {self._format_datetime(definition.created_at)}"
                )
            if definition.updated_at:
                st.caption(
                    f"**Laatst bewerkt:** {self._format_datetime(definition.updated_at)}"
                )

            # Created/Updated by
            if metadata.get("created_by"):
                st.caption(f"**Aangemaakt door:** {metadata['created_by']}")
            if metadata.get("updated_by"):
                st.caption(f"**Bewerkt door:** {metadata['updated_by']}")

            # Validation score
            if metadata.get("validation_score"):
                score = metadata["validation_score"]
                color = "green" if score > 0.8 else "orange" if score > 0.6 else "red"
                st.markdown(f"**Validatie Score:** :{color}[{score:.2f}]")

            # Source info
            if metadata.get("source_type"):
                st.caption(f"**Bron Type:** {metadata['source_type']}")
            if definition.bron:
                st.caption(f"**Bron Referentie:** {definition.bron}")

    def _render_version_history(self):
        """Render compact version history panel."""
        definition_id = SessionStateManager.get_value("editing_definition_id")
        if not definition_id:
            return

        # Get history (excluding auto-saves)
        history = self.edit_service.get_version_history(definition_id, limit=10)

        if not history:
            st.caption("📜 Geen versiegeschiedenis beschikbaar")
            return

        # Show count summary
        st.caption(f"📜 **{len(history)} versie(s)** beschikbaar")

        # History in collapsed expander
        with st.expander("Bekijk versiegeschiedenis", expanded=False):
            for entry in history:
                with st.container():
                    # Compact header
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(
                            f"**{entry.get('wijziging_type', 'Wijziging')}** - {entry.get('gewijzigd_op_readable', '')}"
                        )
                    with col2:
                        if st.button(
                            "↩️ Herstel",
                            key=f"revert_{entry.get('id')}",
                            use_container_width=True,
                        ):
                            self._revert_to_version(entry.get("id"))

                    # Change details (collapsed)
                    if entry.get("wijziging_reden"):
                        st.caption(f"Reden: {entry['wijziging_reden']}")

                    # Show preview of changes
                    if entry.get("definitie_nieuwe_waarde"):
                        preview = entry["definitie_nieuwe_waarde"][:100]
                        st.caption(f"_{preview}..._")

                    st.divider()

    def _render_auto_save_status(self):
        """Render auto-save status indicator."""
        if not SessionStateManager.get_value("editing_definition_id"):
            return

        # Auto-save status in sidebar
        with st.sidebar:
            st.markdown("---")

            auto_save_enabled = st.checkbox(
                "Auto-save inschakelen", value=True, key="auto_save_enabled"
            )

            if auto_save_enabled:
                last_save = SessionStateManager.get_value("last_auto_save")
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
            "imported": "🔵",
            "draft": "🟡",
            "review": "🟠",
            "established": "🟢",
            "archived": "⚫",
        }
        labels_nl = {
            "imported": "Geïmporteerd",
            "draft": "Concept",
            "review": "In review",
            "established": "Vastgesteld",
            "archived": "Gearchiveerd",
        }
        st.markdown(f"{colors.get(status, '⚪')} {labels_nl.get(status, status)}")

    # Action methods

    def _search_definitions(
        self, search_term: str, status_filter: str, limit: int = 50
    ):
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
            # Speciale case: 'Geïmporteerd' is herkomst (source_type), geen status in schema
            if status_code == "imported":
                filters["source_type"] = "imported"
            elif status_code and status_code != "Alle":
                filters["status"] = status_code

            # Search
            results = self.repository.search_with_filters(
                search_term=search_term, **filters, limit=int(limit or 50)
            )

            SessionStateManager.set_value("edit_search_results", results)

            if results:
                st.success(f"✅ {len(results)} definities gevonden")
            else:
                st.info("Geen definities gevonden met deze criteria")

        except Exception as e:
            st.error(f"Fout bij zoeken: {e!s}")
            logger.error(f"Search error: {e}")

    def _start_edit_session(self, definition_id: int):
        """Start edit session for a definition."""
        try:
            # Start session
            session = self.edit_service.start_edit_session(
                definition_id, user=SessionStateManager.get_value("user") or "system"
            )

            if session["success"]:
                SessionStateManager.set_value("editing_definition_id", definition_id)
                SessionStateManager.set_value(
                    "editing_definition", session["definition"]
                )
                SessionStateManager.set_value("edit_session", session)

                # Check for auto-save draft en bied herstelknop
                if session.get("auto_save"):
                    timestamp = session["auto_save"].get(
                        "auto_save_timestamp", "onbekend"
                    )
                    st.warning(f"💾 Niet-opgeslagen concept gevonden ({timestamp})")

                    # Show buttons without columns (already in column context from selector)
                    if st.button("↩️ Herstel concept", key="restore_auto_save_btn"):
                        self._restore_auto_save(session["auto_save"])
                        st.rerun()
                    if st.button("🗑️ Negeer concept", key="ignore_auto_save_btn"):
                        # Just continue with current definition state
                        pass

                # ID-gescope widget-keys zorgen dat de juiste waarden direct getoond worden

                st.success("✅ Edit sessie gestart")
                st.rerun()
            else:
                st.error(f"Fout: {session.get('error', 'Onbekende fout')}")

        except Exception as e:
            st.error(f"Fout bij starten edit sessie: {e!s}")
            logger.error(f"Edit session error: {e}")

    def _save_definition(self):
        """Save the edited definition."""
        try:
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if not definition_id:
                st.error("Geen definitie geselecteerd")
                return

            def k(name: str) -> str:
                return f"edit_{definition_id}_{name}"

            # Collect updates - gebruik SessionStateManager.get_value voor context lijsten
            # Minimaal één context vereist
            org_list = (
                SessionStateManager.get_value(k("organisatorische_context")) or []
            )
            jur_list = SessionStateManager.get_value(k("juridische_context")) or []
            wet_list = SessionStateManager.get_value(k("wettelijke_basis")) or []
            if not (org_list or jur_list or wet_list):
                st.error(
                    "Minimaal één context is vereist (organisatorisch, juridisch of wettelijk)"
                )
                return

            # Voor de overige velden gebruiken we SessionStateManager voor consistentie
            updates = {
                "begrip": SessionStateManager.get_value(k("begrip")),
                "definitie": SessionStateManager.get_value(k("definitie")),
                "organisatorische_context": org_list,
                "juridische_context": jur_list,
                "wettelijke_basis": wet_list,
                "categorie": SessionStateManager.get_value(k("categorie")),
                "ufo_categorie": (
                    SessionStateManager.get_value(k("ufo_categorie")) or None
                ),
                "toelichting": SessionStateManager.get_value(k("toelichting")),
                "status": SessionStateManager.get_value(k("status")),
            }

            # Add version number for optimistic locking
            editing_definition = SessionStateManager.get_value("editing_definition")
            if editing_definition and editing_definition.metadata:
                updates["version_number"] = editing_definition.metadata.get(
                    "version_number", 1
                )

            # Save
            result = self.edit_service.save_definition(
                definition_id,
                updates,
                user=SessionStateManager.get_value("user") or "system",
                reason=SessionStateManager.get_value(k("save_reason")),
                validate=True,
            )

            if result["success"]:
                st.success("✅ Definitie opgeslagen!")

                # Show validation results if available
                if result.get("validation"):
                    # Sla op in session en render buiten kolommen (full-width)
                    SessionStateManager.set_value(
                        "edit_last_validation", result["validation"]
                    )
                    st.rerun()

                # Refresh definition
                self._refresh_current_definition()
            elif result.get("conflict"):
                st.error(
                    "⚠️ Versie conflict - de definitie is gewijzigd door een andere gebruiker"
                )
                if st.button("🔄 Ververs en probeer opnieuw"):
                    self._refresh_current_definition()
            else:
                st.error(f"Fout bij opslaan: {result.get('error', 'Onbekende fout')}")

        except Exception as e:
            st.error(f"Fout bij opslaan: {e!s}")
            logger.error(f"Save error: {e}")

    def _validate_definition(self):
        """Validate the current definition and return results (do not render here)."""
        try:
            # Create definition object from current state
            from services.interfaces import Definition

            def_id = SessionStateManager.get_value("editing_definition_id")

            def k(name: str) -> str:
                return f"edit_{def_id}_{name}"

            definition = Definition(
                begrip=SessionStateManager.get_value(k("begrip"), ""),
                definitie=SessionStateManager.get_value(k("definitie"), ""),
                organisatorische_context=SessionStateManager.get_value(
                    k("organisatorische_context")
                )
                or [],
                juridische_context=SessionStateManager.get_value(
                    k("juridische_context")
                )
                or [],
                wettelijke_basis=SessionStateManager.get_value(k("wettelijke_basis"))
                or [],
                categorie=SessionStateManager.get_value(k("categorie"), "proces"),
                toelichting=SessionStateManager.get_value(k("toelichting"), ""),
                metadata={
                    "status": SessionStateManager.get_value(k("status"), "draft")
                },
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
                        "organisatorische_context": definition.organisatorische_context
                        or [],
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
                                "message": item.get("description")
                                or item.get("message", ""),
                                "severity": item.get("severity", "warning"),
                            }
                        )
                    results = {
                        "valid": bool(v.get("is_acceptable", False)),
                        "score": float(v.get("overall_score", 0.0) or 0.0),
                        "issues": normalized_issues,
                        "raw_v2": v,
                    }

            return results

        except Exception as e:
            st.error(f"Fout bij validatie: {e!s}")
            logger.error(f"Validation error: {e}")
            return None

    def _render_fullwidth_validation_results(self) -> None:
        """Render opgeslagen validatieresultaten buiten de knoppenkolommen (volle breedte)."""
        try:
            results = SessionStateManager.get_value("edit_last_validation")
            if results:
                st.markdown("#### ✅ Kwaliteitstoetsing")
                self._show_validation_results(results)
        except Exception:
            pass

    def _show_validation_results(self, results: dict[str, Any]):
        """Show validation results."""
        # Als V2 ruwe data aanwezig is: render gedetailleerde output gelijk aan generatie-tab
        v2 = results.get("raw_v2") if isinstance(results, dict) else None
        if isinstance(v2, dict):
            st.markdown("#### ✅ Kwaliteitstoetsing")
            from ui.components.validation_view import render_validation_detailed_list

            # Gebruik ID-gescope key_prefix voor stabiele togglestate per definitie
            def_id = SessionStateManager.get_value("editing_definition_id")
            kp = f"edit_{def_id}" if def_id else "edit"
            render_validation_detailed_list(
                v2, key_prefix=kp, show_toggle=True, gate=None
            )
        elif results["valid"]:
            st.success(f"✅ Validatie geslaagd! Score: {results['score']:.2f}")
        else:
            st.warning(f"⚠️ Validatie problemen gevonden. Score: {results['score']:.2f}")

        # Let op: Geen extra 'Uitleg bij alle regels' sectie meer.
        # De gedeelde renderer toont inline uitleg per regel om duplicatie te voorkomen.

    def _build_rule_hint_markdown(self, rule_id: str) -> str:
        """Bouw korte hint-uitleg voor een toetsregel uit JSON en standaardtekst.

        Toont:
        - Wat toetst de regel (uitleg/toetsvraag)
        - Optioneel voorbeelden (goed/fout) als bullets
        - Link naar uitgebreide handleiding
        """
        try:
            import json as _json
            from pathlib import Path

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
                explanation = str(
                    data.get("uitleg") or data.get("toetsvraag") or ""
                ).strip()
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
                "Meer uitleg: [Validatieregels (CON‑01 e.a.)]"
                "(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )

    def _render_v2_validation_details(self, validation_result: dict) -> None:
        """Render V2 validatie details: score, samenvatting, violations en geslaagde regels."""
        try:
            overall_score = float(validation_result.get("overall_score", 0.0))
            violations = list(validation_result.get("violations") or [])
            passed_rules = list(validation_result.get("passed_rules") or [])

            score_color = (
                "green"
                if overall_score > 0.8
                else ("orange" if overall_score > 0.6 else "red")
            )
            st.markdown(
                f"**Overall Score:** <span style='color: {score_color}'>{overall_score:.2f}</span>",
                unsafe_allow_html=True,
            )

            # Samenvatting
            failed_ids = sorted(
                {
                    str(v.get("rule_id") or v.get("code") or "")
                    for v in violations
                    if isinstance(v, dict)
                }
            )
            passed_ids = sorted({str(r) for r in passed_rules})
            total = len(set(failed_ids).union(passed_ids))
            passed_count = len(passed_ids)
            failed_count = len(failed_ids)
            pct = (passed_count / total * 100.0) if total > 0 else 0.0
            st.markdown(
                f"📊 **Toetsing Samenvatting**: {passed_count}/{total} regels geslaagd ({pct:.1f}%)"
                + (f" | ❌ {failed_count} gefaald" if failed_count else "")
            )

            # Violations
            if violations:
                st.markdown("#### ❌ Gevallen regels")

                def _v_key(v):
                    rid = str(v.get("rule_id") or v.get("code") or "")
                    return self._rule_sort_key(rid)

                for v in sorted(violations, key=_v_key):
                    rid = str(v.get("rule_id") or v.get("code") or "")
                    sev = str(v.get("severity", "warning")).lower()
                    desc = v.get("description") or v.get("message") or ""
                    suggestion = v.get("suggestion")
                    if suggestion:
                        desc = f"{desc} · Wat verbeteren: {suggestion}"
                    emoji = "❌" if sev in {"critical", "error", "high"} else "⚠️"
                    name, explanation = self._get_rule_info(rid)
                    name_part = f" — {name}" if name else ""
                    expl_labeled = (
                        f" · Wat toetst: {explanation}"
                        if explanation
                        else " · Wat toetst: —"
                    )
                    st.markdown(
                        f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}"
                    )

            # Geslaagde regels
            if passed_ids:
                with st.expander("✅ Geslaagde regels", expanded=False):
                    for rid in sorted(passed_ids, key=self._rule_sort_key):
                        name, explanation = self._get_rule_info(rid)
                        name_part = f" — {name}" if name else ""
                        wat_toetst = (
                            f"Wat toetst: {explanation}"
                            if explanation
                            else "Wat toetst: —"
                        )
                        st.markdown(f"✅ {rid}{name_part}: OK · {wat_toetst}")
        except Exception as e:
            st.warning(f"Kon gedetailleerde validatie niet tonen: {e!s}")

    def _get_rule_info(self, rule_id: str) -> tuple[str, str]:
        """Haal (naam, uitleg) op voor een regel uit JSON, indien beschikbaar."""
        try:
            import json as _json
            from pathlib import Path

            rid = (rule_id or "").replace("_", "-")
            json_path = Path("src/toetsregels/regels") / f"{rid}.json"
            if not json_path.exists():
                return "", ""
            data = _json.loads(json_path.read_text(encoding="utf-8"))
            name = str(data.get("naam") or "").strip()
            explanation = str(
                data.get("uitleg") or data.get("toetsvraag") or ""
            ).strip()
            return name, explanation
        except Exception:
            return "", ""

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
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if definition_id:
                definition = self.repository.get(definition_id)
                if definition:
                    SessionStateManager.set_value("editing_definition", definition)
                    st.success("✅ Wijzigingen ongedaan gemaakt")
                    st.rerun()

        except Exception as e:
            st.error(f"Fout bij ongedaan maken: {e!s}")
            logger.error(f"Undo error: {e}")

    def _cancel_edit(self):
        """Cancel the edit session."""
        # Clear edit state using SessionStateManager
        for key in ["editing_definition_id", "editing_definition", "edit_session"]:
            SessionStateManager.set_value(key, None)

        st.info("Edit sessie geannuleerd")
        st.rerun()

    def _revert_to_version(self, version_id: int):
        """Revert to a specific version."""
        try:
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if not definition_id:
                return

            result = self.edit_service.revert_to_version(
                definition_id,
                version_id,
                user=SessionStateManager.get_value("user") or "system",
            )

            if result["success"]:
                st.success("✅ Definitie hersteld naar eerdere versie")
                self._refresh_current_definition()
            else:
                st.error(
                    f"Fout bij herstellen: {result.get('error', 'Onbekende fout')}"
                )

        except Exception as e:
            st.error(f"Fout bij herstellen: {e!s}")
            logger.error(f"Revert error: {e}")

    def _refresh_current_definition(self):
        """Refresh the current definition from database."""
        try:
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if definition_id:
                definition = self.repository.get(definition_id)
                if definition:
                    SessionStateManager.set_value("editing_definition", definition)
                    st.rerun()

        except Exception as e:
            logger.error(f"Refresh error: {e}")

    def _track_changes(self):
        """Track changes for auto-save."""
        auto_save_enabled = SessionStateManager.get_value("auto_save_enabled")
        if not auto_save_enabled:
            return

        # Check if content changed
        definition = SessionStateManager.get_value("editing_definition")
        if not definition:
            return

        def k(name: str) -> str:
            return f"edit_{definition.id}_{name}"

        changed = False

        # Check each field for changes (widget keys nog steeds in st.session_state)
        fields_to_check = [
            (k("begrip"), "begrip"),
            (k("definitie"), "definitie"),
            (k("categorie"), "categorie"),
            (k("toelichting"), "toelichting"),
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
            if (
                _norm_list(SessionStateManager.get_value(k("organisatorische_context")))
                != _norm_list(getattr(definition, "organisatorische_context", []))
                or _norm_list(SessionStateManager.get_value(k("juridische_context")))
                != _norm_list(getattr(definition, "juridische_context", []))
                or _norm_list(SessionStateManager.get_value(k("wettelijke_basis")))
                != _norm_list(getattr(definition, "wettelijke_basis", []))
            ):
                changed = True

        # Auto-save if changed and interval verstreken
        if changed:
            last = SessionStateManager.get_value("last_auto_save")
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
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if not definition_id:
                return

            def k(name: str) -> str:
                return f"edit_{definition_id}_{name}"

            # Collect current state - gebruik SessionStateManager
            content = {
                "begrip": SessionStateManager.get_value(k("begrip")),
                "definitie": SessionStateManager.get_value(k("definitie")),
                "organisatorische_context": SessionStateManager.get_value(
                    k("organisatorische_context")
                ),
                "juridische_context": SessionStateManager.get_value(
                    k("juridische_context")
                ),
                "wettelijke_basis": SessionStateManager.get_value(
                    k("wettelijke_basis")
                ),
                "categorie": SessionStateManager.get_value(k("categorie")),
                "toelichting": SessionStateManager.get_value(k("toelichting")),
                "status": SessionStateManager.get_value(k("status")),
            }

            # Save
            if self.edit_service.auto_save(definition_id, content):
                SessionStateManager.set_value("last_auto_save", datetime.now())

        except Exception as e:
            logger.error(f"Auto-save error: {e}")

    def _restore_auto_save(self, auto_save_content: dict[str, Any]):
        """Restore from auto-save."""
        try:
            def_id = SessionStateManager.get_value("editing_definition_id")

            def k(name: str) -> str:
                return f"edit_{def_id}_{name}"

            # Update session state with auto-save content - hybride aanpak
            field_mapping = {
                "begrip": k("begrip"),
                "definitie": k("definitie"),
                "categorie": k("categorie"),
                "toelichting": k("toelichting"),
                "status": k("status"),
            }
            # Context lijsten via SessionStateManager
            context_mapping = {
                "organisatorische_context": k("organisatorische_context"),
                "juridische_context": k("juridische_context"),
                "wettelijke_basis": k("wettelijke_basis"),
            }

            # Backward compat: map legacy 'context' naar organisatorische_context indien aanwezig
            if (
                "context" in auto_save_content
                and "organisatorische_context" not in auto_save_content
            ):
                auto_save_content["organisatorische_context"] = auto_save_content.get(
                    "context"
                )

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
            st.error(f"Fout bij herstellen auto-save: {e!s}")
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
            "editing_definition_id": None,
            "editing_definition": None,
            "edit_session": None,
            "edit_search_results": [],
            "last_auto_save": None,
            "auto_save_enabled": True,
        }

        # Gebruik SessionStateManager voor alle edit-specifieke defaults
        for key, default_value in edit_defaults.items():
            if SessionStateManager.get_value(key) is None:
                SessionStateManager.set_value(key, default_value)
