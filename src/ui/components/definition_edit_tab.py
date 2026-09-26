"""
Definition Edit Tab - Rich text editor interface voor definities.

Deze tab biedt een gebruiksvriendelijke interface voor het bewerken
van definities met ondersteuning voor versiegeschiedenis en auto-save.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, cast

import streamlit as st

from config.config_manager import ConfigSection, get_config
from domain.categorie_herkomst import HERKOMST_EDITOR
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import AutoSaveResult, DefinitionEditService
from services.validation.modular_validation_service import ModularValidationService
from ui.helpers.categorie_weergave import (
    beschrijf_keuzestatus,
    bouw_categorie_opties,
    categorie_label,
)
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)

#: Compacte staat van het bronbewijs voor lijsten (DEF-743). Een opgeslagen
#: cijfer wordt niet meer als actuele kwaliteit getoond (besluit 3).
_BRONBASIS_LABEL = {
    "present": "bronbewijs",
    "reference_only": "alleen verwijzing",
    "absent": "geen bronnen",
    "invalid": "bewijs onleesbaar",
}

#: Toepassen van een voorstel vervangt de opgeslagen tekst; een niet-opgeslagen
#: bewerking in het widget zou daarbij zonder spoor verloren gaan.
_MELDING_ONOPGESLAGEN = (
    "Sla eerst je bewerking op: toepassen vervangt de opgeslagen tekst door het "
    "voorstel en zou je niet-opgeslagen bewerking verliezen."
)


def _als_dict(waarde: Any) -> dict[str, Any]:
    """Typegetrouwe vernauwing: een dict, anders een lege dict."""
    return waarde if isinstance(waarde, dict) else {}


def bronbasis_label(metadata: dict[str, Any] | None) -> str:
    """Leesbaar label voor `source_evidence_status` uit de recordmetadata."""
    status = (metadata or {}).get("source_evidence_status")
    if not isinstance(status, dict):
        return ""
    label = _BRONBASIS_LABEL.get(str(status.get("status") or ""), "")
    if label == "bronbewijs" and status.get("current") is False:
        label = "bronbewijs (verouderd)"
    return label


class DefinitionEditTab:
    """Tab voor het bewerken van definities met rich text editor."""

    def __init__(
        self,
        repository: DefinitionEditRepository | None = None,  # DEF-439
        validation_service: ModularValidationService | None = None,  # DEF-439
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

    def render(self) -> None:
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
                # DEF-236: Race condition fix - use version tracking to detect concurrent loads
                # Increment load version BEFORE starting the load operation
                current_load_version = SessionStateManager.get_value(
                    "edit_load_version", 0
                )
                new_load_version = current_load_version + 1
                SessionStateManager.set_value("edit_load_version", new_load_version)
                logger.debug(
                    f"Starting edit load v{new_load_version} for definition {target_id}"
                )

                # Probeer sessie te starten zodat geschiedenis/auto-save beschikbaar zijn
                session = self.edit_service.start_edit_session(
                    target_id, user=SessionStateManager.get_value("user") or "system"
                )
                if session and session.get("success"):
                    # DEF-236: Check if another load was triggered while we were loading
                    # If version changed, another load started - don't apply stale data
                    latest_version = SessionStateManager.get_value(
                        "edit_load_version", 0
                    )
                    if latest_version != new_load_version:
                        logger.warning(
                            f"Concurrent edit tab load detected - skipping stale data "
                            f"(started v{new_load_version}, current v{latest_version})",
                            extra={
                                "component": "definition_edit_tab",
                                "operation": "auto_load",
                                "target_id": target_id,
                                "started_version": new_load_version,
                                "current_version": latest_version,
                            },
                        )
                        # Don't return! Show info and let UI continue rendering
                        st.info(
                            "🔄 Gelijktijdige laadoperatie gedetecteerd. "
                            "De nieuwste versie wordt geladen."
                        )
                        # Skip applying stale session data, but continue UI rendering
                    else:
                        # Safe to apply session data - no concurrent load detected
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
                            SessionStateManager.clear_value(
                                "edit_organisatorische_context"
                            )
                            SessionStateManager.clear_value("edit_juridische_context")
                            SessionStateManager.clear_value("edit_wettelijke_basis")
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning(
                f"Error in edit tab auto-load: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "auto_load",
                    "target_id": target_id if "target_id" in dir() else None,
                    "error_type": type(e).__name__,
                },
            )
            # Don't show error to user - graceful degradation, user can manually select
        except Exception as e:
            logger.error(
                f"Unexpected error in edit tab auto-load: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "auto_load",
                    "error_type": type(e).__name__,
                },
            )
            st.warning("⚠️ Kon definitie niet automatisch laden. Selecteer handmatig.")

        # Main layout
        col1, col2 = st.columns([2, 1])

        with col1:
            # Definition selector and editor
            self._render_definition_selector()

            if SessionStateManager.get_value("editing_definition_id"):
                self._render_editor()
                self._render_action_buttons()
                self._render_examples_section()
                # DEF-151: Show generation prompt in main content area for visibility
                definition = SessionStateManager.get_value("editing_definition")
                if definition:
                    self._render_generation_prompt_section(definition)
                    # DEF-743: bronbasis (CON-02) van het opgeslagen record en
                    # het handmatige verbetervoorstel — uitsluitend op verzoek.
                    self._render_bronbasis_section(definition)
                    # DEF-766: telbaarheid (ESS-03) van het opgeslagen record,
                    # replay op de kandidaat zoals nu bewerkt.
                    self._render_ess03_section(definition)
                    # DEF-772: verwijzingen (INT-03) van het opgeslagen record,
                    # idem replay op de kandidaat zoals nu bewerkt.
                    self._render_int03_section(definition)
                    # DEF-808: opgegeven bronmetadata aanvullen op de
                    # documentbronnen van het opgeslagen record.
                    self._render_bronmetadata_section(definition)
                    self._render_voorstel_section(definition)

        with col2:
            # Sidebar with metadata and history
            if SessionStateManager.get_value("editing_definition_id"):
                self._render_metadata_panel()
                self._render_version_history()

        # Auto-save status
        self._render_auto_save_status()

    def _render_definition_selector(self) -> None:
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
            # Note: "Concept" is default (index=0), "Alle" toont ook archived
            status_options = {
                "Concept": "draft",
                "Alle": None,
                "Geïmporteerd": "imported",
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
        # Note: SessionStateManager.get_value() returns None for missing keys, no try-except needed
        current_results = SessionStateManager.get_value("edit_search_results")

        if (not current_results) and (not search_term) and status_label == "Alle":
            # Haal de laatste N definities op zonder filters (discovery)
            self._search_definitions("", "Alle", max_results)

        # Display search results
        if SessionStateManager.get_value("edit_search_results") is not None:
            self._render_search_results()

    def _render_search_results(self) -> None:
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

                def _join_list(v: Any) -> str:
                    try:
                        return ", ".join([str(x) for x in (v or [])])
                    except (TypeError, AttributeError):
                        # TypeError: v is not iterable, AttributeError: str() fails
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
                    rows.append(
                        {
                            "Selecteer": bool(prev_selected_id == d.id),
                            "ID": d.id,
                            "Begrip": d.begrip,
                            "Categorie": d.categorie or "",
                            "UFO-categorie": getattr(d, "ufo_categorie", None) or "",
                            "Status": status_disp,
                            "Herkomst": _source_label(source_type),
                            # DEF-743 (besluit 3): geen opgeslagen cijfer als
                            # actuele kwaliteit; wel de staat van het bronbewijs.
                            "Bronbasis": bronbasis_label(d.metadata),
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
                        "Bronbasis": st.column_config.TextColumn(disabled=True),
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
                except (ValueError, TypeError, KeyError, AttributeError):
                    # ValueError: int() fails, TypeError: iteration fails,
                    # KeyError: missing column, AttributeError: missing method
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
            except ImportError:
                # pandas not available - fallback to list view
                st.info("📋 Tabelweergave niet beschikbaar. Gebruik de lijstweergave.")
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.debug(
                    f"Table render issue: {e}",
                    extra={
                        "component": "definition_edit_tab",
                        "operation": "render_search_results",
                        "error_type": type(e).__name__,
                    },
                )
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
                        except (TypeError, AttributeError):
                            # TypeError: join fails on non-iterable, AttributeError: missing attr
                            pass
                    with c2:
                        if st.button("✏️ Bewerk", key=f"edit_btn_{d.id}"):
                            self._start_edit_session(int(d.id))
                st.markdown("---")

    @staticmethod
    def _plaats_klaargezette_tekst(def_id: Any) -> None:
        """F2 (DEF-743): een toegepast voorstel is in de vorige run klaargezet;
        plaats het hier — vóór de widgetconstructie — in het widget. Alleen
        als het klaargezette voorstel bij dít record hoort."""
        pending = SessionStateManager.get_value(f"edit_{def_id}_pending_definitie")
        if isinstance(pending, str):
            SessionStateManager.set_value(f"edit_{def_id}_definitie", pending)
            SessionStateManager.clear_value(f"edit_{def_id}_pending_definitie")

    def _render_editor(self) -> None:
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

        SessionStateManager.initialize_session_state({k("begrip"): definition.begrip})
        begrip = st.text_input(
            "Begrip",
            key=k("begrip"),
            disabled=disabled,
            help="Het juridische begrip dat gedefinieerd wordt",
        )

        # Rich text editor for definition
        st.markdown("**Definitie:**")

        # Use text area as fallback (st_quill requires additional setup)
        self._plaats_klaargezette_tekst(definition.id)
        SessionStateManager.initialize_session_state(
            {k("definitie"): definition.definitie}
        )
        definitie_text = st.text_area(
            "Definitie tekst",
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
                help="Selecteer één of meer organisaties; kies Anders... voor eigen waarden (komma-gescheiden)",
            )
            # Afkortingen-uitleg uit config (indien aanwezig)
            try:
                abbrev = getattr(ui_cfg, "afkortingen", {}) or {}
                if abbrev:
                    with st.expander("ℹ️ Afkortingen (uitleg)", expanded=False):
                        for ak in sorted(abbrev.keys()):
                            st.markdown(f"- **{ak}** — {abbrev[ak]}")
            except (TypeError, AttributeError, KeyError):
                # TypeError: sorted() fails, AttributeError: missing attr, KeyError: dict access
                pass
            org_custom_values = []
            if "Anders..." in org_selected:
                org_custom_raw = st.text_input(
                    "Andere organisatie(s) (komma-gescheiden)",
                    value=", ".join(org_other) if org_other else "",
                    key=k("org_custom"),
                    disabled=disabled,
                )
                org_custom_values = [
                    v.strip() for v in org_custom_raw.split(",") if v.strip()
                ]
            # Schrijf de samengevoegde lijst naar session state voor save-flow
            org_resolved = [
                v for v in org_selected if v != "Anders..."
            ] + org_custom_values
            SessionStateManager.set_value(k("organisatorische_context"), org_resolved)

            # Category — DEF-751: de geladen waarde komt exact terug (ook een
            # schemawaarde buiten de vier keuzes of een lege), zonder
            # ValueError en zonder stille omzetting naar proces; alleen-lezen
            # volgt hetzelfde beleid als de overige velden.
            categorie_opties, categorie_index = bouw_categorie_opties(
                definition.categorie
            )
            categorie = st.selectbox(
                "Categorie",
                options=categorie_opties,
                index=categorie_index,
                format_func=categorie_label,
                key=k("categorie"),
                disabled=disabled,
                help="Ontologische categorie van het begrip",
            )
            # DEF-751 B2: herkomst van de opgeslagen keuze — voorstel,
            # handmatig (opgegeven naam), import, default, onbekend of
            # verouderd — zichtbaar naast de keuze; geen oordeel.
            st.caption(
                beschrijf_keuzestatus(
                    (definition.metadata or {}).get("category_choice_status"),
                    (definition.metadata or {}).get("category_choice"),
                )
            )

            # UFO-categorie selectie (onder ontologische categorie)
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
            except (ValueError, TypeError, AttributeError):
                # ValueError: not in list, TypeError: unhashable, AttributeError: missing attr
                ufo_default_index = 0
            ufo_selected = st.selectbox(
                "UFO-categorie",
                options=ufo_opties,
                index=ufo_default_index,
                key=k("ufo_categorie"),
                disabled=disabled,
                help="Selecteer de UFO-categorie (OntoUML/UFO metamodel)",
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
                help="Selecteer rechtsgebieden; kies Anders... voor eigen waarden (komma-gescheiden)",
            )
            jur_custom_values = []
            if "Anders..." in jur_selected:
                jur_custom_raw = st.text_input(
                    "Andere rechtsgebieden (komma-gescheiden)",
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
                help="Selecteer wetten; kies Anders... voor eigen waarden (komma-gescheiden)",
            )
            wet_custom_values = []
            if "Anders..." in wet_selected:
                wet_custom_raw = st.text_input(
                    "Andere wetten (komma-gescheiden)",
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
        SessionStateManager.initialize_session_state(
            {k("toelichting"): definition.toelichting or ""}
        )
        toelichting = st.text_area(
            "Toelichting (optioneel)",
            height=100,
            key=k("toelichting"),
            disabled=disabled,
            help="Extra uitleg of context bij de definitie",
        )

        # DEF-766: het antwoord op de gerichte ESS-03-vraag hoort bij déze
        # kandidaat en gaat mee bij opnieuw toetsen; het herschrijft de
        # definitie niet en vervalst geen ESS-02-keuze. Hersteld uit de
        # opgeslagen beoordeling; leeg als er nog niets is verduidelijkt.
        SessionStateManager.initialize_session_state(
            {
                k("ess03_verduidelijking"): str(
                    (getattr(definition, "metadata", None) or {}).get(
                        "ess03_verduidelijking"
                    )
                    or ""
                )
            }
        )
        st.text_area(
            "ESS-03-verduidelijking bij deze kandidaat (optioneel)",
            height=80,
            key=k("ess03_verduidelijking"),
            disabled=disabled,
            help=(
                "Antwoord op de vraag van de ESS-03-beoordeling (telbaarheid): welke "
                "eenheid, conventie of scope is bedoeld. Wordt bij 'Valideren' "
                "meegegeven en bij opslaan met de beoordeling vastgelegd; de "
                "definitietekst zelf wordt niet automatisch aangepast. "
                # DEF-820 (K2): verwijzende formuleringen zonder aangeleverde
                # afspraak roepen vrijwel altijd de vraag naar die conventie op.
                "Verwijst de definitie naar een register, een code of een conventie "
                "die niet is aangeleverd, dan vraagt de beoordeling daar meestal "
                "naar: beschrijf die conventie hier of voeg de bronpassage toe. "
                "Herschrijf de definitie niet alleen om de vraag te ontlopen."
            ),
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

    def _render_action_buttons(self) -> None:
        """Render action buttons for saving and validation."""
        # Reden voor wijziging (persistente input boven de knoppen) - ID-gescope
        def_id = SessionStateManager.get_value("editing_definition_id")

        def k(name: str) -> str:
            return f"edit_{def_id}_{name}"

        st.text_input("Reden voor wijziging (optioneel)", key=k("save_reason"))

        # Check 'minstens 1 context' voor Save-actie
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
                    self._bewaar_sessieresultaat(
                        results, SessionStateManager.get_value("editing_definition_id")
                    )
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

    def _render_examples_section(self) -> None:
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
        # Zelfde database als de geïnjecteerde repository (DEF-743): geen
        # tweede, hardcoded productiepad naast de geïnjecteerde.
        repo = getattr(self.repository, "legacy_repo", None) or DefinitieRepository()

        # REMOVED: _reset_voorbeelden_context() call (caused data loss!)
        # De reset wiste voorbeelden uit session state bij elke render, terwijl ze
        # niet altijd in de database waren opgeslagen. Dit veroorzaakte permanent
        # data verlies wanneer voorbeelden alleen in session state zaten.
        # Reset gebeurt nu alleen bij definitie switches in _start_edit_session().

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
                        except (ImportError, AttributeError, TypeError):
                            # ImportError: module not found, AttributeError: missing attr, TypeError: comparison
                            st.info(
                                "ℹ️ Geen voorkeursterm geselecteerd. Gebruik de selector hierboven om er een te kiezen."
                            )
        except (KeyError, AttributeError, TypeError) as e:
            logger.debug(
                f"Could not show voorkeursterm status: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "render_examples_section",
                    "error_type": type(e).__name__,
                },
            )

    def _render_metadata_panel(self) -> None:
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

            # DEF-743 (besluit 3): geen opgeslagen validatiecijfer als actuele
            # kwaliteit; de regeloordelen staan in de Kwaliteitstoetsing.
            label = bronbasis_label(metadata)
            if label:
                st.caption(f"**Bronbasis:** {label}")

            # Source info
            if metadata.get("source_type"):
                st.caption(f"**Bron Type:** {metadata['source_type']}")
            if definition.bron:
                st.caption(f"**Bron Referentie:** {definition.bron}")

    def _render_generation_prompt_section(self, definition: Any) -> None:
        """
        Render generation prompt viewer (DEF-151).

        Displays the stored generation prompt data (if available) using the
        PromptDebugSection component. Includes prompt text, model info, and token usage.

        Args:
            definition: Definition object with generation_prompt_data attribute

        Note:
            Silently fails if prompt data is not available or cannot be parsed.
            This is non-critical functionality for viewing historical generation details.
            Uses same approach as generator tab for consistency.
        """
        try:
            from ui.components.prompt_debug_section import PromptDebugSection

            # Get prompt from definition.metadata (where it's actually stored!)
            prompt_template: str | None = None

            if definition.metadata and "generation_prompt_data" in definition.metadata:
                # metadata already contains parsed JSON dict
                prompt_data = definition.metadata["generation_prompt_data"]
                prompt_template = (
                    prompt_data.get("prompt") if isinstance(prompt_data, dict) else None
                )
                # DEF-622 (besluit tekstvergelijking): ook bij een opnieuw
                # geopend record, alleen met echt bewijs en zolang de zin nog
                # de generatie-eindtekst is (na handmatige wijziging: niets).
                # De actuele zin is wat in de editor staat (recordgebonden
                # widgetwaarde uit `_render_editor`), niet het geladen record:
                # anders blijft na herschrijven een melding met de oude
                # eindtekst staan (reviewbevinding op batch 2).
                from ui.components.tekstwijziging import (
                    render_tekstwijziging,
                    tekstwijziging_uit_bewijs,
                )

                actuele_tekst = SessionStateManager.get_value(
                    f"edit_{definition.id}_definitie",
                    getattr(definition, "definitie", None),
                )
                render_tekstwijziging(
                    tekstwijziging_uit_bewijs(
                        prompt_data if isinstance(prompt_data, dict) else None,
                        actuele_tekst=actuele_tekst,
                    )
                )

            if prompt_template:
                # Create container for PromptDebugSection (EXACT same pattern as generator tab)
                class _PromptContainer:
                    def __init__(self, text: str):
                        self.prompt_template = text

                container = _PromptContainer(prompt_template)
                # Render with PromptDebugSection (no voorbeelden_prompts in edit context)
                PromptDebugSection.render(container, voorbeelden_prompts=None)

        except (ImportError, KeyError, TypeError, AttributeError) as e:
            # ImportError: PromptDebugSection not found, KeyError: missing key
            # TypeError: wrong type, AttributeError: missing method
            logger.debug(
                f"Could not render generation prompt: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "render_generation_prompt_section",
                    "error_type": type(e).__name__,
                },
            )
            # Silently fail - not critical

    # ------------------------------------------------------------------
    # DEF-743: bronbasis (CON-02) en handmatig verbetervoorstel op verzoek
    # ------------------------------------------------------------------

    #: Bestaande identiteitsbronnen buiten het eigen naamveld van de
    #: bronmetadata-sectie: de ingelogde gebruiker en de reviewer naam uit de
    #: voorstel- en expertsectie.
    _BEKENDE_IDENTITEITSSLEUTELS: tuple[str, ...] = (
        "user",
        "edit_reviewer_name_input",
        "reviewer_name_input",
    )

    @classmethod
    def _bekende_gebruiker(cls) -> str | None:
        """Bestaande gebruikersidentiteit zónder het eigen naamveld van de
        bronmetadata-sectie; nooit verzonnen."""
        for sleutel in cls._BEKENDE_IDENTITEITSSLEUTELS:
            waarde = SessionStateManager.get_value(sleutel)
            if isinstance(waarde, str) and waarde.strip():
                return waarde.strip()
        return None

    @classmethod
    def _handelende_gebruiker(cls) -> str | None:
        """Bestaande gebruikersidentiteit (sessie-`user`, reviewer naam); nooit verzonnen."""
        bekend = cls._bekende_gebruiker()
        if bekend is not None:
            return bekend
        waarde = SessionStateManager.get_value("edit_bronmeta_reviewer_name_input")
        if isinstance(waarde, str) and waarde.strip():
            return waarde.strip()
        return None

    @staticmethod
    def _actorbron() -> str:
        """Waar de identiteit van `_handelende_gebruiker` vandaan komt (DEF-751):
        sessiegebruiker of getypte naam (voorstel-, expert- of bronmetadata-
        naamveld) — beide zonder authenticatie."""
        waarde = SessionStateManager.get_value("user")
        return (
            "session_user"
            if isinstance(waarde, str) and waarde.strip()
            else "typed_name"
        )

    @staticmethod
    def _sessiebeoordeling() -> dict[str, Any] | None:
        """De AI-bronbeoordeling uit de laatste toetsing in deze sessie, of None.

        DEF-809: `edit_last_validation` is het genormaliseerde resultaat van
        "Valideren" (`normaliseer_validatieresultaat`); de beoordeling staat
        daarin onder `source_assessment` (en ruw onder `raw_v2`). Alleen een
        object wordt doorgegeven; binding en status beoordeelt de servicelaag.
        """
        laatste = SessionStateManager.get_value("edit_last_validation")
        if not isinstance(laatste, dict):
            return None
        beoordeling = laatste.get("source_assessment")
        if beoordeling is None:
            beoordeling = _als_dict(laatste.get("raw_v2")).get("source_assessment")
        return beoordeling if isinstance(beoordeling, dict) else None

    @staticmethod
    def _sessiebeoordeling_ess03() -> dict[str, Any] | None:
        """De ESS-03-beoordeling uit de laatste toetsing in deze sessie, of None.

        DEF-766: zelfde route als de bronbeoordeling (`ess03_assessment` in
        het genormaliseerde resultaat, ruw onder `raw_v2`). Alleen een object
        wordt doorgegeven; binding en status beoordeelt de servicelaag.
        """
        laatste = SessionStateManager.get_value("edit_last_validation")
        if not isinstance(laatste, dict):
            return None
        beoordeling = laatste.get("ess03_assessment")
        if beoordeling is None:
            beoordeling = _als_dict(laatste.get("raw_v2")).get("ess03_assessment")
        return beoordeling if isinstance(beoordeling, dict) else None

    @staticmethod
    def _sessiebeoordeling_int03() -> dict[str, Any] | None:
        """De INT-03-beoordeling uit de laatste toetsing in deze sessie, of None.

        DEF-772: `int03_assessment` in het genormaliseerde resultaat, anders
        het document dat de evaluator in `raw_v2["rule_results"]["INT-03"]`
        zette. Alleen een object wordt doorgegeven; binding en status
        beoordeelt de servicelaag.
        """
        from services.definition_edit_service import int03_document_uit_resultaat

        laatste = SessionStateManager.get_value("edit_last_validation")
        if not isinstance(laatste, dict):
            return None
        beoordeling = laatste.get("int03_assessment")
        if beoordeling is None:
            beoordeling = int03_document_uit_resultaat(_als_dict(laatste.get("raw_v2")))
        return beoordeling if isinstance(beoordeling, dict) else None

    @staticmethod
    def _int03_binding() -> Any | None:
        """De actuele INT-03-beoordelingsbinding uit de gecachte dienst — zonder
        netwerk (promptversie/norm uit code en regelrecord, provider/model uit
        de ModelRouter). None wanneer de dienst niet beschikbaar is; de replay
        benoemt dat dan expliciet en past geen opgeslagen beoordeling toe."""
        try:
            from ui.cached_services import get_cached_service_container

            return get_cached_service_container().int03_assessment_service().binding()
        except Exception as e:
            logger.warning(
                "INT-03-beoordelingsbinding niet beschikbaar: %s: %s",
                type(e).__name__,
                e,
            )
            return None

    @staticmethod
    def _sessieverduidelijking(def_id: Any) -> str | None:
        """De ESS-03-verduidelijking zoals nu in de editor staat.

        `None` wanneer het veld in deze sessie niet bestaat (dan geldt de
        opgeslagen verduidelijking); een lege tekst wanneer de gebruiker het
        veld heeft gewist — dat is een bewuste keuze en geen ontbrekende waarde.
        """
        waarde = SessionStateManager.get_value(f"edit_{def_id}_ess03_verduidelijking")
        if waarde is None:
            return None
        return waarde.strip() if isinstance(waarde, str) else ""

    @staticmethod
    def _ess03_binding() -> Any | None:
        """De actuele ESS-03-beoordelingsbinding (R1) uit de gecachte dienst — zonder
        netwerk (promptversie/norm uit code en regelrecord, provider/model uit de
        ModelRouter). None wanneer de dienst niet beschikbaar is; de replay
        benoemt dat dan expliciet en past geen opgeslagen beoordeling toe."""
        try:
            from ui.cached_services import get_cached_service_container

            return get_cached_service_container().ess03_assessment_service().binding()
        except Exception as e:
            logger.warning(
                "ESS-03-beoordelingsbinding niet beschikbaar: %s: %s",
                type(e).__name__,
                e,
            )
            return None

    def _proposal_service(self) -> Any | None:
        """`SourceProposalService` uit de gecachte container (AI-service + router)."""
        if self.edit_service.proposal_service is not None:
            return self.edit_service.proposal_service
        try:
            from services.source_proposal_service import SourceProposalService
            from ui.cached_services import get_cached_service_container

            container = get_cached_service_container()
            dienst = SourceProposalService(
                container.ai_service(), model_router=container.model_router()
            )
        except Exception as e:
            logger.warning(
                "Voorsteldienst niet beschikbaar: %s: %s", type(e).__name__, e
            )
            return None
        self.edit_service.proposal_service = dienst
        return dienst

    def _bronbasis_van_geladen_record(self, definition: Any) -> dict[str, Any] | None:
        """CON-02-uitkomst (pure replay, geen AI) voor het opgeslagen record."""
        if getattr(definition, "id", None) is None:
            return None
        try:
            record = self.repository.get_definitie(int(definition.id))
            if record is None:
                return None
            laatste = SessionStateManager.get_value("edit_last_validation")
            huidig = laatste.get("raw_v2") if isinstance(laatste, dict) else None
            return self.edit_service.bronbasis_van_record(record, huidig)
        except ImportError as e:
            logger.warning("Bronbeoordelingskern niet beschikbaar: %s", e)
            return None
        except Exception as e:
            logger.error("Bronbasis niet te bepalen: %s", e, exc_info=True)
            return None

    def _render_bronbasis_section(self, definition: Any) -> None:
        """Bronbasis van het opgeslagen record: bronnen, kwitantie, AI-oordeel,
        citaten, uitzonderingen — uit het ID-only geladen record."""
        try:
            from ui.components.sources_renderer import SourcesRenderer

            meta = dict(getattr(definition, "metadata", None) or {})
            basis = self._bronbasis_van_geladen_record(definition)
            bronnen = meta.get("provenance_sources")
            if bronnen is None:
                bronnen = meta.get("sources")
            with st.expander(
                "📚 Bronbasis (CON-02) — opgeslagen record", expanded=False
            ):
                if basis is None:
                    st.caption(
                        "Bronbeoordelingskern niet beschikbaar of record niet opgeslagen: "
                        "alleen de bronnen worden getoond."
                    )
                SourcesRenderer().render_bronbasis_section(
                    sources=bronnen if isinstance(bronnen, list) else None,
                    assessment=(basis or {}).get("assessment")
                    or meta.get("source_assessment"),
                    receipt=meta.get("source_receipt"),
                    review=meta.get("source_review"),
                    con02=(basis or {}).get("con02"),
                    evidence_status=meta.get("source_evidence_status"),
                    review_status=meta.get("source_review_status"),
                    titel="",
                )
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning("Bronbasis-sectie kon niet worden getoond: %s", e)

    def _kandidaat_uit_formulier(self, definition: Any) -> Any:
        """De kandidaat zoals nu in de editor staat (R1/R5): widgetwaarden voor
        term, tekst, toelichting, drie contextlijsten, categorie en de
        ESS-03-verduidelijking (ook bewust leeg); ontbreekt een widgetwaarde,
        dan de geladen waarde. Bronset, generatieregistratie en opgeslagen
        beoordeling komen uit het geladen record. Hieraan binden zowel de
        replay van de opgeslagen beoordeling als het normale
        validatieresultaat van de laatste toetsing."""
        from services.interfaces import Definition

        def_id = getattr(definition, "id", None)

        def k(name: str) -> str:
            return f"edit_{def_id}_{name}"

        meta = dict(getattr(definition, "metadata", None) or {})
        kandidaat = Definition(
            id=def_id,
            begrip=SessionStateManager.get_value(k("begrip"), definition.begrip),
            definitie=SessionStateManager.get_value(
                k("definitie"), definition.definitie
            ),
            toelichting=SessionStateManager.get_value(
                k("toelichting"), definition.toelichting
            )
            or None,
            organisatorische_context=SessionStateManager.get_value(
                k("organisatorische_context"),
                list(definition.organisatorische_context or []),
            ),
            juridische_context=SessionStateManager.get_value(
                k("juridische_context"), list(definition.juridische_context or [])
            ),
            wettelijke_basis=SessionStateManager.get_value(
                k("wettelijke_basis"), list(definition.wettelijke_basis or [])
            ),
            categorie=SessionStateManager.get_value(
                k("categorie"), definition.categorie
            )
            or None,
            metadata={
                sleutel: meta.get(sleutel)
                for sleutel in (
                    "provenance_sources",
                    "sources",
                    "generation_prompt_data",
                    "ess03_assessment",
                    "ess03_verduidelijking",
                    "int03_assessment",
                )
                if meta.get(sleutel) is not None
            },
        )
        verduidelijking = self._sessieverduidelijking(def_id)
        if verduidelijking is not None:
            # metadata is hierboven altijd als dict geconstrueerd; de guard
            # maakt dat expliciet voor het `dict | None`-veldtype (mypy).
            if kandidaat.metadata is None:
                kandidaat.metadata = {}
            kandidaat.metadata["ess03_verduidelijking"] = verduidelijking
        return kandidaat

    def _render_ess03_section(self, definition: Any) -> None:
        """ESS-03 (telbaarheid) van het opgeslagen record: replay van de
        opgeslagen AI-beoordeling op de kandidaat zoals nu in de editor staat.

        Geen AI-aanroep. Zo ziet de gebruiker de laatste uitkomst (voldoet,
        voldoet niet, niet van toepassing, onvoldoende informatie met vraag, of
        technisch probleem) én of zij nog bij de huidige tekst, context,
        toelichting en verduidelijking hoort; een gewijzigde kandidaat maakt
        haar zichtbaar verouderd. Toetsen opnieuw ('Valideren') levert een
        verse beoordeling (DEF-766).
        """
        try:
            from services.definition_edit_service import ess03_uitkomst_van_definition
            from ui.components.validation_view import render_rule_results

            meta = dict(getattr(definition, "metadata", None) or {})
            opgeslagen = meta.get("ess03_assessment")
            kandidaat = self._kandidaat_uit_formulier(definition)
            with st.expander(
                "🔢 Telbaarheid (ESS-03) — opgeslagen AI-beoordeling", expanded=False
            ):
                if opgeslagen is None:
                    st.caption(
                        "Nog geen ESS-03-beoordeling opgeslagen bij dit record. "
                        "'Valideren' voert de AI-beoordeling uit; 'Opslaan' legt haar "
                        "vast zolang zij bij de opgeslagen kandidaat hoort."
                    )
                    return
                render_rule_results(
                    {
                        "ESS-03": ess03_uitkomst_van_definition(
                            kandidaat, binding=self._ess03_binding()
                        )
                    }
                )
                st.caption(
                    "Herkomst: AI-beoordeling (geen deskundigenoordeel, geen "
                    "vaststelling). Een negatieve uitkomst blokkeert vaststellen of "
                    "exporteren niet en wijzigt de tekst niet."
                )
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning("ESS-03-sectie kon niet worden getoond: %s", e)

    def _render_int03_section(self, definition: Any) -> None:
        """INT-03 (verwijzingen) van het opgeslagen record: replay van de
        opgeslagen AI-beoordeling op de kandidaat zoals nu in de editor staat.

        Geen AI-aanroep. Zo ziet de gebruiker de laatste uitkomst (voldoet,
        voldoet — niet van toepassing, voldoet niet met woord/passage/
        kandidaten, onvoldoende informatie met de ene vraag, of technisch
        probleem) én of zij nog bij de huidige tekst, term, context en
        toelichting en de actuele prompt/norm/model hoort; een gewijzigde
        kandidaat maakt haar zichtbaar historisch. 'Valideren' levert een
        verse beoordeling (DEF-772).
        """
        try:
            from services.definition_edit_service import int03_uitkomst_van_definition
            from ui.components.validation_view import render_rule_results

            meta = dict(getattr(definition, "metadata", None) or {})
            opgeslagen = meta.get("int03_assessment")
            kandidaat = self._kandidaat_uit_formulier(definition)
            with st.expander(
                "🔗 Verwijzingen (INT-03) — opgeslagen AI-beoordeling", expanded=False
            ):
                if opgeslagen is None:
                    st.caption(
                        "Nog geen INT-03-beoordeling opgeslagen bij dit record. "
                        "'Valideren' voert de AI-beoordeling uit; 'Opslaan' legt haar "
                        "vast zolang zij bij de opgeslagen kandidaat hoort."
                    )
                    return
                render_rule_results(
                    {
                        "INT-03": int03_uitkomst_van_definition(
                            kandidaat,
                            binding=self._int03_binding(),
                            assessment=opgeslagen,
                        )
                    }
                )
                st.caption(
                    "Herkomst: AI-beoordeling (geen deskundigenoordeel, geen "
                    "vaststelling). Een negatieve uitkomst blokkeert vaststellen of "
                    "exporteren niet en wijzigt de tekst niet; herstel volgt alleen "
                    "op verzoek."
                )
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning("INT-03-sectie kon niet worden getoond: %s", e)

    # ------------------------------------------------------------------
    # DEF-808: opgegeven bronmetadata aanvullen op het opgeslagen record
    # ------------------------------------------------------------------

    @staticmethod
    def _documentbronnen_per_id(bronnen: Any) -> dict[str, dict[str, Any]]:
        """De documentbronnen uit het bewijs, gegroepeerd per `doc_id`, met de
        huidige (eventueel eerder opgegeven) coördinaten van het document."""
        documenten: dict[str, dict[str, Any]] = {}
        for bron in bronnen if isinstance(bronnen, list) else []:
            if not isinstance(bron, dict):
                continue
            if str(bron.get("provider") or "").casefold() not in (
                "documents",
                "document",
            ):
                continue
            doc_id = str(bron.get("doc_id") or "").strip()
            if not doc_id:
                continue
            item = documenten.setdefault(
                doc_id,
                {
                    "filename": bron.get("filename") or bron.get("title") or doc_id,
                    "aantal": 0,
                    "url": bron.get("url"),
                    "source_version": bron.get("source_version"),
                    "locator": bron.get("locator"),
                    "declared": _als_dict(bron.get("declared_metadata")),
                },
            )
            item["aantal"] += 1
        return documenten

    @staticmethod
    def _toon_bronmetadata_resultaat(resultaat: dict[str, Any]) -> None:
        status = str(resultaat.get("status") or "")
        bericht = str(resultaat.get("message") or status)
        if status == "applied":
            st.success(f"✅ {bericht}")
        elif status == "invalid":
            st.error(f"❌ {bericht}")
        elif status in ("version_conflict", "not_editable", "not_found", "no_actor"):
            st.warning(f"🔄 {bericht}")
        else:
            st.error(f"❌ {bericht}")

    @classmethod
    def _bronmetadata_actor(cls) -> str | None:
        """De handelende gebruiker voor de bronmetadata-sectie.

        Het naamveld hangt af van de ándere identiteitsbronnen, nooit van zijn
        eigen waarde: een widget dat verdwijnt zodra zijn waarde is gevonden,
        wordt door Streamlit bij de eerstvolgende rerun opgeruimd (naam weg,
        knop weer uit — browserbevinding 18-09-2026). Zolang er geen bestaande
        identiteit is, blijft het veld dus staan.
        """
        actor = cls._bekende_gebruiker()
        if actor is not None:
            return actor
        ingevoerd = st.text_input(
            "Reviewer naam (vereist voor vastleggen)",
            key="edit_bronmeta_reviewer_name_input",
        )
        if isinstance(ingevoerd, str) and ingevoerd.strip():
            return ingevoerd.strip()
        return None

    @staticmethod
    def _toon_huidige_opgave(gekozen: dict[str, Any] | None) -> None:
        """De huidige (eerder opgegeven) coördinaten van het gekozen document."""
        if gekozen is None:
            return
        opgave = gekozen["declared"]
        herkomst = (
            f" (opgegeven door {opgave.get('declared_by') or 'onbekend'} op "
            f"{opgave.get('declared_at') or 'onbekend tijdstip'})"
            if opgave
            else " (nog niets opgegeven)"
        )
        st.caption(
            f"Huidige opgave bij {gekozen['filename']}: "
            f"url: {gekozen['url'] or 'geen'} · versie: "
            f"{gekozen['source_version'] or 'onbekend'} · vindplaats: "
            f"{gekozen['locator'] or 'onbekend'}{herkomst}"
        )

    @staticmethod
    def _bronmetadata_hulp(
        *, alleen_lezen: bool, actor: str | None, gekozen: Any, ingevuld: bool
    ) -> str | None:
        """Waarom de vastlegknop uit staat (help-tekst), of None als hij aan mag."""
        if alleen_lezen:
            return "Alleen-lezen status: geen aanvulling mogelijk"
        if not actor:
            return "Vul eerst een reviewer naam in"
        if gekozen is None:
            return "Kies een document"
        if not ingevuld:
            return "Geef minstens een hyperlink, bronversie of vindplaats op"
        return None

    def _render_bronmetadata_section(self, definition: Any) -> None:
        """Opgegeven hyperlink, bronversie en exacte vindplaats aanvullen op de
        documentbronnen van het OPGESLAGEN record (DEF-808), zodat een bestaand
        record kan worden hertoetst. De opgave blijft herkenbaar als opgegeven
        metadata; zij bewijst geen authenticiteit en keurt niets goed. Validatie
        en opslag lopen via de servicelaag (DEF-806-hyperlinkregel, versieguard)."""
        def_id = getattr(definition, "id", None)
        if def_id is None:
            return
        meta = dict(getattr(definition, "metadata", None) or {})
        bronnen = meta.get("provenance_sources")
        if bronnen is None:
            bronnen = meta.get("sources")
        documenten = self._documentbronnen_per_id(bronnen)
        k = f"edit_{def_id}_bronmeta"
        with st.expander(
            "🔗 Bronmetadata aanvullen (hyperlink, bronversie, vindplaats — opgegeven)",
            expanded=False,
        ):
            st.caption(
                "Opgegeven metadata is geen authenticiteitsbewijs en geen goedkeuring: "
                "brongezag, betekenissteun en verwijskwaliteit worden onverminderd "
                "beoordeeld. Een eerdere AI-bronbeoordeling geldt na aanvullen niet "
                "meer — valideer opnieuw en sla op. Er wordt geen netwerkcontrole "
                "uitgevoerd en de definitietekst wordt niet gewijzigd."
            )
            resultaat = SessionStateManager.get_value(f"{k}_resultaat")
            if isinstance(resultaat, dict):
                self._toon_bronmetadata_resultaat(resultaat)
            if not documenten:
                st.info(
                    "Geen documentbronnen in het opgeslagen bewijs: er is geen "
                    "geüpload document om metadata bij op te geven."
                )
                return
            actor = self._bronmetadata_actor()
            doc_ids = list(documenten)
            keuze = st.selectbox(
                "Document uit de opgeslagen bronset",
                options=doc_ids,
                format_func=lambda d: (
                    f"{documenten[d]['filename']} · {documenten[d]['aantal']} passage(s) "
                    f"· doc {d}"
                ),
                key=f"{k}_doc",
            )
            gekozen = documenten.get(str(keuze)) if keuze else None
            self._toon_huidige_opgave(gekozen)
            url = st.text_input(
                "Hyperlink (http(s); een interne link volstaat)", key=f"{k}_url"
            )
            versie = st.text_input(
                "Bronversie (bv. geldigheidsdatum 2026-08-15 of editie)",
                key=f"{k}_versie",
            )
            vindplaats = st.text_input(
                "Exacte vindplaats (bv. artikel 1:3 lid 1 Awb)", key=f"{k}_vindplaats"
            )
            hulp = self._bronmetadata_hulp(
                alleen_lezen=meta.get("status") in ("established", "archived"),
                actor=actor,
                gekozen=gekozen,
                ingevuld=any(str(v or "").strip() for v in (url, versie, vindplaats)),
            )
            if st.button(
                "🔗 Bronmetadata vastleggen (als opgegeven)",
                key=f"{k}_vastleggen",
                disabled=hulp is not None,
                help=hulp,
            ):
                if hulp is not None or not actor or keuze is None:
                    return
                self._leg_bronmetadata_vast(
                    int(def_id), str(keuze), url, versie, vindplaats, str(actor)
                )

    def _leg_bronmetadata_vast(
        self,
        def_id: int,
        doc_id: str,
        url: Any,
        versie: Any,
        vindplaats: Any,
        actor: str,
    ) -> None:
        """Eén expliciete vastlegging via de servicelaag; resultaat blijft zichtbaar."""
        try:
            resultaat = self.edit_service.vul_bronmetadata_aan(
                def_id,
                doc_id=doc_id,
                url=url,
                source_version=versie,
                locator=vindplaats,
                actor=actor,
                expected_version=self._getoonde_versie(def_id),
            )
        except Exception as e:
            logger.error("Bronmetadata vastleggen mislukt: %s", e, exc_info=True)
            resultaat = {"status": "error", "message": f"{type(e).__name__}: {e}"}
        SessionStateManager.set_value(f"edit_{def_id}_bronmeta_resultaat", resultaat)
        self._toon_bronmetadata_resultaat(resultaat)
        if resultaat.get("status") == "applied":
            self._refresh_current_definition()

    def _render_voorstel_section(self, definition: Any) -> None:
        """Handmatig verbetervoorstel (DEF-743, besluit 2): uitsluitend na een
        expliciete knop; nooit automatisch bij een CON-02-failure of rerun.
        De oorspronkelijke tekst blijft staan; toepassen is een aparte,
        bewuste keuze met hertoetsing."""
        def_id = getattr(definition, "id", None)
        if def_id is None:
            return
        meta = dict(getattr(definition, "metadata", None) or {})
        status_code = meta.get("status")
        with st.expander("🛠️ Verbetervoorstel op verzoek (CON-02)", expanded=False):
            st.caption(
                "Een CON-02-uitkomst 'voldoet niet' is niet vanzelf een fout in de "
                "definitiezin: ontbrekend bewijs, brontransport, een technische fout "
                "of AI-onzekerheid worden eerst onderscheiden. Maximaal één "
                "voorstelaanvraag per oorspronkelijke generatie (DEF-638)."
            )
            actor = self._handelende_gebruiker()
            if not actor:
                st.text_input(
                    "Reviewer naam (vereist voor aanvragen/toepassen)",
                    key="edit_reviewer_name_input",
                )
                actor = self._handelende_gebruiker()

            # Bestaande voorstellen (bewijs, ook geblokkeerd/fout/afgewezen).
            voorstellen = [
                v for v in (meta.get("source_proposals") or []) if isinstance(v, dict)
            ]
            ongewijzigd = not self._onopgeslagen_bewerking(int(def_id), definition)
            alleen_lezen = status_code in ("established", "archived")

            laatste = SessionStateManager.get_value(f"edit_{def_id}_voorstel_resultaat")
            if isinstance(laatste, dict):
                self._toon_voorstelresultaat(laatste)

            hulp = None
            if alleen_lezen:
                hulp = "Alleen-lezen status: geen voorstel mogelijk"
            elif not actor:
                hulp = "Vul eerst een reviewer naam in"
            elif not ongewijzigd:
                hulp = "Sla eerst je bewerking op: een voorstel geldt voor de opgeslagen tekst"
            if st.button(
                "🛠️ Vraag verbetervoorstel aan",
                key=f"edit_{def_id}_vraag_voorstel",
                disabled=hulp is not None,
                help=hulp,
            ):
                self._vraag_voorstel(int(def_id), str(actor))

            for voorstel in voorstellen:
                self._render_voorstel(
                    int(def_id), voorstel, actor, alleen_lezen, ongewijzigd
                )

    @staticmethod
    def _onopgeslagen_bewerking(def_id: int, definition: Any = None) -> bool:
        """Staat er in het tekstwidget een bewerking die nog niet is opgeslagen?

        Vergelijkt het widget (`edit_{id}_definitie`) met het geladen record.
        Zonder vergelijkbaar geladen record is het antwoord fail-closed 'ja':
        toepassen mag nooit iets overschrijven dat niet is nagekeken.
        """
        geladen = (
            definition
            if definition is not None
            else SessionStateManager.get_value("editing_definition")
        )
        if geladen is None or getattr(geladen, "id", None) != def_id:
            return True
        opgeslagen = (getattr(geladen, "definitie", "") or "").strip()
        bewerkt = SessionStateManager.get_value(f"edit_{def_id}_definitie", opgeslagen)
        return (bewerkt or "").strip() != opgeslagen

    def _toon_voorstelresultaat(self, resultaat: dict[str, Any]) -> None:
        status = str(resultaat.get("status") or "")
        bericht = str(resultaat.get("message") or status)
        diagnose = _als_dict(resultaat.get("diagnose"))
        oorzaak = diagnose.get("cause")
        if status in ("proposed", "applied"):
            st.success(f"✅ {bericht}")
        elif status in ("blocked", "attempt_consumed", "no_evidence", "unavailable"):
            st.warning(
                f"⛔ Geen voorstel: {bericht}"
                + (f" (oorzaak: {oorzaak})" if oorzaak else "")
            )
        elif status in ("version_conflict", "stale_original", "not_editable"):
            st.warning(f"🔄 {bericht}")
        elif status == "unsaved_changes":
            st.warning(f"💾 {bericht}")
        elif status == "rejected":
            st.info(f"ℹ️ {bericht}")
        else:
            st.error(f"❌ {bericht}" + (f" (oorzaak: {oorzaak})" if oorzaak else ""))
        for bevinding in diagnose.get("findings") or []:
            st.caption(f"Bevinding: {bevinding}")

    def _render_voorstel(
        self,
        def_id: int,
        voorstel: dict[str, Any],
        actor: str | None,
        alleen_lezen: bool,
        ongewijzigd: bool,
    ) -> None:
        pid = str(voorstel.get("proposal_id") or "")
        status = str(voorstel.get("status") or "")
        uitkomst = _als_dict(voorstel.get("outcome"))
        origineel = _als_dict(voorstel.get("original"))
        label = {
            "proposed": "voorstel beschikbaar",
            "applied": "toegepast",
            "rejected": "afgewezen",
            "superseded": "vervangen",
            "reserved": "aangevraagd (geen uitkomst vastgelegd)",
        }.get(status, status)
        st.markdown(
            f"**Voorstel {pid[:8]} — {label}** · door {voorstel.get('actor') or 'onbekend'}"
        )
        uitkomststatus = str(uitkomst.get("status") or "")
        if uitkomststatus in ("blocked", "error"):
            fout = (
                uitkomst.get("error")
                if isinstance(uitkomst.get("error"), dict)
                else None
            )
            st.warning(
                f"Geen bruikbaar voorstel ({uitkomststatus}): "
                f"{uitkomst.get('rationale') or (fout or {}).get('message') or 'geen details'}"
            )
        if uitkomst.get("candidate_text"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Oorspronkelijke tekst (bewaard)**")
                st.text(str(origineel.get("text") or ""))
            with col_b:
                st.markdown("**Voorgestelde tekst**")
                st.text(str(uitkomst.get("candidate_text")))
            if uitkomst.get("rationale"):
                st.caption(f"Reden: {uitkomst.get('rationale')}")
            st.caption(
                f"Model: {uitkomst.get('model') or 'onbekend'} · prompt {uitkomst.get('prompt_version') or '?'}"
                f" · bronbinding {str(uitkomst.get('assessment_fingerprint') or '?')[:12]}"
            )
        if status == "proposed" and uitkomststatus == "proposed" and not alleen_lezen:
            hulp = None if actor else "Vul eerst een reviewer naam in"
            # Toepassen vervangt de opgeslagen tekst; een niet-opgeslagen
            # bewerking in het widget zou daarbij verloren gaan (niet in het
            # bewaarde origineel, niet in de historie). Afwijzen raakt de tekst
            # niet en blijft beschikbaar.
            hulp_toepassen = hulp
            if hulp_toepassen is None and not ongewijzigd:
                hulp_toepassen = _MELDING_ONOPGESLAGEN
            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "✅ Pas voorstel toe (hertoetsing met dezelfde bronnen)",
                    key=f"edit_{def_id}_voorstel_{pid}_toepassen",
                    disabled=hulp_toepassen is not None,
                    help=hulp_toepassen,
                ):
                    self._pas_voorstel_toe(def_id, pid, str(actor))
            with c2:
                if st.button(
                    "❌ Wijs voorstel af",
                    key=f"edit_{def_id}_voorstel_{pid}_afwijzen",
                    disabled=not actor,
                    help=hulp,
                ):
                    self._wijs_voorstel_af(def_id, pid, str(actor))

    @staticmethod
    def _getoonde_versie(def_id: int) -> int | None:
        """F3: de recordversie die de editor vóór zich had (geen verse lezing)."""
        geladen = SessionStateManager.get_value("editing_definition")
        if geladen is None or getattr(geladen, "id", None) != def_id:
            return None
        versie = (getattr(geladen, "metadata", None) or {}).get("version_number")
        return (
            versie if isinstance(versie, int) and not isinstance(versie, bool) else None
        )

    def _vraag_voorstel(self, def_id: int, actor: str) -> None:
        """Eén expliciete aanvraag; reservering en uitkomst bij D, model via F."""
        from ui.helpers.async_bridge import run_async

        self._proposal_service()
        laatste = SessionStateManager.get_value("edit_last_validation")
        huidig = laatste.get("raw_v2") if isinstance(laatste, dict) else None
        try:
            resultaat = run_async(
                self.edit_service.vraag_verbetervoorstel(
                    def_id,
                    actor=actor,
                    huidig_resultaat=huidig,
                    expected_version=self._getoonde_versie(def_id),
                )
            )
        except Exception as e:
            logger.error("Voorstelaanvraag mislukt: %s", e, exc_info=True)
            resultaat = {"status": "error", "message": f"{type(e).__name__}: {e}"}
        SessionStateManager.set_value(f"edit_{def_id}_voorstel_resultaat", resultaat)
        self._refresh_current_definition()

    def _pas_voorstel_toe(self, def_id: int, proposal_id: str, actor: str) -> None:
        from ui.helpers.async_bridge import run_async

        if self._onopgeslagen_bewerking(def_id):
            # Zelfde controle als de knop, maar in de handler zelf: geen dienst-,
            # hertoetsings- of DB-aanroep, niets klaargezet, widget onaangeroerd.
            SessionStateManager.set_value(
                f"edit_{def_id}_voorstel_resultaat",
                {"status": "unsaved_changes", "message": _MELDING_ONOPGESLAGEN},
            )
            st.rerun()
            return
        try:
            resultaat = run_async(
                self.edit_service.pas_voorstel_toe(
                    def_id,
                    proposal_id,
                    actor=actor,
                    expected_version=self._getoonde_versie(def_id),
                )
            )
        except Exception as e:
            logger.error("Voorstel toepassen mislukt: %s", e, exc_info=True)
            resultaat = {"status": "error", "message": f"{type(e).__name__}: {e}"}
        SessionStateManager.set_value(f"edit_{def_id}_voorstel_resultaat", resultaat)
        if resultaat.get("status") == "applied":
            # F2: het tekstwidget van deze run bestaat al; zijn session-state-
            # sleutel mag nú niet meer worden gezet (StreamlitAPIException).
            # De toegepaste tekst wordt daarom klaargezet en pas in de
            # volgende run, vóór de widgetconstructie in `_render_editor`,
            # in het widget geplaatst. De hertoetsing is het actuele
            # resultaat (geen oude pass) — dat is geen widgetsleutel.
            SessionStateManager.set_value(
                f"edit_{def_id}_pending_definitie", resultaat.get("candidate_text")
            )
            validatie = resultaat.get("validation")
            if isinstance(validatie, dict):
                from services.definition_edit_service import (
                    normaliseer_validatieresultaat,
                )

                self._bewaar_sessieresultaat(
                    normaliseer_validatieresultaat(validatie), def_id
                )
        self._refresh_current_definition()

    def _wijs_voorstel_af(self, def_id: int, proposal_id: str, actor: str) -> None:
        resultaat = self.edit_service.wijs_voorstel_af(
            def_id,
            proposal_id,
            actor=actor,
            expected_version=self._getoonde_versie(def_id),
        )
        SessionStateManager.set_value(f"edit_{def_id}_voorstel_resultaat", resultaat)
        self._refresh_current_definition()

    def _render_version_history(self) -> None:
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
                            self._revert_to_version(
                                cast(int, entry.get("id"))
                            )  # DEF-439

                    # Change details (collapsed)
                    if entry.get("wijziging_reden"):
                        st.caption(f"Reden: {entry['wijziging_reden']}")

                    # Show preview of changes
                    if entry.get("definitie_nieuwe_waarde"):
                        preview = entry["definitie_nieuwe_waarde"][:100]
                        st.caption(f"_{preview}..._")

                    st.divider()

    def _render_auto_save_status(self) -> None:
        """Render auto-save status indicator."""
        if not SessionStateManager.get_value("editing_definition_id"):
            return

        # Auto-save status in sidebar
        with st.sidebar:
            st.markdown("---")

            SessionStateManager.initialize_session_state({"auto_save_enabled": True})
            auto_save_enabled = st.checkbox(
                "Auto-save inschakelen", key="auto_save_enabled"
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

    def _render_status_badge(self, status: str) -> None:
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
    ) -> None:
        """Search for definitions."""
        try:
            # Build filters
            filters: dict[str, Any] = {}  # DEF-439
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

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Search input error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "search_definitions",
                    "search_term": search_term,
                    "error_type": type(e).__name__,
                },
            )
            st.warning(f"⚠️ Ongeldige zoekopdracht: {e!s}")
        except Exception as e:
            logger.error(
                f"Search error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "search_definitions",
                    "search_term": search_term,
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"❌ Fout bij zoeken: {e!s}")

    def _start_edit_session(self, definition_id: int) -> None:
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
                # R1/R5: een nieuwe bewerksessie begint zonder toetsresultaat
                # van een vorige sessie; het record toont zijn opgeslagen
                # beoordeling via de replay-sectie.
                SessionStateManager.set_value("edit_last_validation", None)

                # DEF-156 Fix 2B: Eager voorbeelden loading to prevent data loss
                # Explicitly resolve and cache voorbeelden in session state
                try:
                    from database.definitie_repository import DefinitieRepository
                    from ui.helpers.examples import resolve_examples

                    # Zelfde database als de geïnjecteerde repository (DEF-743).
                    repo = (
                        getattr(self.repository, "legacy_repo", None)
                        or DefinitieRepository()
                    )
                    state_key = f"edit_{definition_id}_examples"
                    voorbeelden = resolve_examples(
                        state_key, session["definition"], repository=repo
                    )
                    if voorbeelden and any(voorbeelden.values()):
                        SessionStateManager.set_value(state_key, voorbeelden)
                        logger.debug(
                            f"Eager-loaded voorbeelden for edit session {definition_id}: "
                            f"{sum(len(v) if isinstance(v, list) else 0 for v in voorbeelden.values())} items"
                        )
                except (ImportError, KeyError, AttributeError, TypeError) as e:
                    # Don't fail session start if voorbeelden loading fails
                    # ImportError: module not found, KeyError: dict access, AttributeError: missing method
                    logger.warning(
                        f"Could not eager-load voorbeelden for edit session {definition_id}: {e}",
                        extra={
                            "component": "definition_edit_tab",
                            "operation": "start_edit_session",
                            "definition_id": definition_id,
                            "error_type": type(e).__name__,
                        },
                    )

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

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Invalid data when starting edit session: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "start_edit_session",
                    "definition_id": definition_id,
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"⚠️ Ongeldige gegevens bij starten sessie: {e!s}")
        except Exception as e:
            logger.error(
                f"Edit session error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "start_edit_session",
                    "definition_id": definition_id,
                    "error_type": type(e).__name__,
                },
            )
            st.error(
                f"❌ Fout bij starten edit sessie: {e!s}. "
                f"Probeer de pagina te verversen."
            )

    @staticmethod
    def _meld_bronbeoordeling_bij_opslaan(
        result: dict[str, Any], sessiebeoordeling: dict[str, Any] | None
    ) -> None:
        """DEF-809: wat er bij Opslaan met de sessiebeoordeling is gebeurd —
        opgeslagen als actueel bewijs, of benoemd waarom niet (nooit stil)."""
        if result.get("source_assessment_persisted"):
            st.success(
                "✅ Bronbeoordeling van de laatste toetsing opgeslagen bij de "
                "actuele tekst en context (herkenbaar als AI-beoordeling; "
                "geen vaststelling)."
            )
        elif sessiebeoordeling is not None and result.get("source_assessment_reason"):
            st.warning(
                "⚠️ Bronbeoordeling van de laatste toetsing niet opgeslagen: "
                f"{result['source_assessment_reason']}."
            )

    @staticmethod
    def _meld_ess03_beoordeling_bij_opslaan(
        result: dict[str, Any], sessiebeoordeling: dict[str, Any] | None
    ) -> None:
        """DEF-766: wat er bij Opslaan met de ESS-03-sessiebeoordeling is gebeurd —
        opgeslagen als actuele beoordeling, of benoemd waarom niet (nooit stil)."""
        if result.get("ess03_assessment_persisted"):
            st.success(
                "✅ ESS-03-beoordeling (telbaarheid) van de laatste toetsing opgeslagen "
                "bij de actuele kandidaat (herkenbaar als AI-beoordeling; geen "
                "vaststelling, geen blokkade)."
            )
        elif sessiebeoordeling is not None and result.get("ess03_assessment_reason"):
            st.warning(
                "⚠️ ESS-03-beoordeling van de laatste toetsing niet opgeslagen: "
                f"{result['ess03_assessment_reason']}."
            )

    @staticmethod
    def _meld_int03_beoordeling_bij_opslaan(
        result: dict[str, Any], sessiebeoordeling: dict[str, Any] | None
    ) -> None:
        """DEF-772: wat er bij Opslaan met de INT-03-sessiebeoordeling is gebeurd —
        opgeslagen als actuele beoordeling, of benoemd waarom niet (nooit stil)."""
        if result.get("int03_assessment_persisted"):
            st.success(
                "✅ INT-03-beoordeling (verwijzingen) van de laatste toetsing "
                "opgeslagen bij de actuele kandidaat (herkenbaar als AI-beoordeling; "
                "geen vaststelling, geen blokkade)."
            )
        elif sessiebeoordeling is not None and result.get("int03_assessment_reason"):
            st.warning(
                "⚠️ INT-03-beoordeling van de laatste toetsing niet opgeslagen: "
                f"{result['int03_assessment_reason']}."
            )

    def _save_definition(self) -> None:
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
                # DEF-751: een lege keuze (record zonder categorie) wordt geen
                # kolomwaarde; `_definition_to_updates` slaat None over, zodat
                # opslaan zonder categorieactie niets herclassificeert.
                "categorie": SessionStateManager.get_value(k("categorie")) or None,
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

            # DEF-809: de bronbeoordeling van de laatste "Valideren" reist mee;
            # de servicelaag legt haar alleen vast als zij exact aan de op te
            # slaan kandidaat bindt en benoemt anders waarom niet.
            sessiebeoordeling = self._sessiebeoordeling()
            # DEF-766: idem voor de ESS-03-beoordeling van de laatste toetsing.
            sessiebeoordeling_ess03 = self._sessiebeoordeling_ess03()
            # DEF-772: idem voor de INT-03-beoordeling van de laatste toetsing.
            sessiebeoordeling_int03 = self._sessiebeoordeling_int03()
            # R5: de actuele ESS-03-verduidelijking van de kandidaat reist
            # expliciet mee — ook bewust leeg — en wordt eigen recordwaarde;
            # zonder veld in deze sessie blijft de opgeslagen waarde staan.
            verduidelijking = self._sessieverduidelijking(definition_id)
            if verduidelijking is not None:
                updates["ess03_verduidelijking"] = verduidelijking

            # DEF-751 B2: alleen een werkelijk gewijzigde categorie is een
            # keuze van deze opslaan-actie; zij reist als `editor`-event mee
            # met de bestaande lokale identiteit (opgegeven naam of sessie-
            # gebruiker — geen authenticatie). Zonder identiteit blijft de
            # keuze ongeattribueerd; er wordt geen actor verzonnen.
            actor = self._handelende_gebruiker()
            geladen_categorie = getattr(editing_definition, "categorie", None)
            categoriekeuze = None
            if updates["categorie"] is not None and updates["categorie"] != (
                geladen_categorie or None
            ):
                # Expliciet commando (reviewbevinding 2): nooit via updates/
                # metadata; met de versie van de getoonde kandidaat (bevinding 3).
                categoriekeuze = {
                    "herkomst": HERKOMST_EDITOR,
                    "actor": actor,
                    "actor_source": self._actorbron() if actor else None,
                }

            # Save
            result = self.edit_service.save_definition(
                definition_id,
                updates,
                user=actor or SessionStateManager.get_value("user") or "system",
                reason=SessionStateManager.get_value(k("save_reason")),
                validate=True,
                source_assessment=sessiebeoordeling,
                ess03_assessment=sessiebeoordeling_ess03,
                ess03_binding=self._ess03_binding(),
                categoriekeuze=categoriekeuze,
                int03_assessment=sessiebeoordeling_int03,
                int03_binding=self._int03_binding(),
            )

            if result["success"]:
                st.success("✅ Definitie opgeslagen!")
                self._meld_bronbeoordeling_bij_opslaan(result, sessiebeoordeling)
                self._meld_ess03_beoordeling_bij_opslaan(
                    result, sessiebeoordeling_ess03
                )
                self._meld_int03_beoordeling_bij_opslaan(
                    result, sessiebeoordeling_int03
                )

                # Show validation results if available
                if result.get("validation"):
                    # Sla op in session en render buiten kolommen (full-width)
                    self._bewaar_sessieresultaat(result["validation"], definition_id)
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

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Invalid data in save request: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "save_definition",
                    "definition_id": definition_id,
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"⚠️ Ongeldige gegevens: {e!s}. Controleer de invoer.")
        except Exception as e:
            logger.error(
                f"Save error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "save_definition",
                    "definition_id": definition_id,
                    "error_type": type(e).__name__,
                },
            )
            st.error(
                f"❌ Fout bij opslaan: {e!s}. Je wijzigingen zijn NIET opgeslagen. "
                f"Kopieer je tekst naar een veilige plek en probeer opnieuw."
            )

    def _validate_definition(self) -> dict[str, Any] | None:
        """Validate the current definition and return results (do not render here)."""
        try:
            # Create definition object from current state
            from services.definition_edit_service import (
                bouw_validatiecontext,
                normaliseer_validatieresultaat,
            )
            from services.interfaces import Definition

            def_id = SessionStateManager.get_value("editing_definition_id")

            def k(name: str) -> str:
                return f"edit_{def_id}_{name}"

            # DEF-622/DEF-743: de kandidaat is de ACTUELE bewerkte tekst, term en
            # drie contextlijsten (ook leeg); id, recordversie, vastgelegde
            # beoordelingen én de bronset komen uit het ID-only geladen record.
            geladen = SessionStateManager.get_value("editing_definition")
            geladen_meta = dict(getattr(geladen, "metadata", None) or {})
            definition = Definition(
                id=def_id,
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
                # DEF-751: zonder widgetwaarde geldt de geladen categorie, geen
                # verzonnen proces.
                categorie=SessionStateManager.get_value(k("categorie"))
                or getattr(geladen, "categorie", None),
                toelichting=SessionStateManager.get_value(k("toelichting"), ""),
                metadata={
                    "status": SessionStateManager.get_value(k("status"), "draft"),
                    # DEF-766: de verduidelijking van déze sessie gaat mee in de
                    # ESS-03-binding (ook bewust leeg); zonder veld geldt die
                    # van het record. De tekst blijft ongewijzigd.
                    **(
                        {"ess03_verduidelijking": verduidelijking}
                        if (verduidelijking := self._sessieverduidelijking(def_id))
                        is not None
                        else {}
                    ),
                },
            )

            # Validate (DEF-439: edit_service resolveert naar Any -> expliciet getypeerd)
            results: dict[str, Any] | None = self.edit_service._validate_definition(
                definition, geladen_meta
            )

            # Als de service None teruggeeft (alleen async API beschikbaar), gebruik UI async-bridge
            if results is None:
                from ui.cached_services import get_cached_service_container
                from ui.helpers.async_bridge import run_async

                container = get_cached_service_container()
                orch = container.orchestrator()
                from services.validation.interfaces import ValidationContext

                # Dezelfde contextdict als het sync pad (pariteit): het
                # bewerkte record identificeert zichzelf (DUP_01), draagt de
                # CON-01-beoordeling mét geladen recordversie (K1) en de
                # bronset/CON-02-review van het geladen record mee; de
                # wrapper verkrijgt zelf de bronbeoordeling (C §8).
                vc = ValidationContext(
                    correlation_id=None,
                    metadata=bouw_validatiecontext(definition, geladen_meta),
                )
                v = run_async(
                    orch.validation_service.validate_text(
                        begrip=definition.begrip,
                        text=definition.definitie,
                        ontologische_categorie=definition.categorie,
                        context=vc,
                    )
                )
                # Normaliseer naar UI-structuur (status/onderdelen/dekking bewaard)
                if isinstance(v, dict):
                    results = normaliseer_validatieresultaat(v)

            if isinstance(results, dict):
                # R1/R5: het resultaat hoort bij dít record; een ander record
                # toont het niet (zie `_actueel_sessieresultaat`).
                results["editing_definition_id"] = def_id
            return results

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning(
                f"Validation input error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "validate_definition",
                    "error_type": type(e).__name__,
                },
            )
            st.warning(f"⚠️ Validatiefout: {e!s}")
            return None
        except Exception as e:
            logger.error(
                f"Validation error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "validate_definition",
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"❌ Fout bij validatie: {e!s}")
            return None

    def _render_fullwidth_validation_results(self) -> None:
        """Render opgeslagen validatieresultaten buiten de knoppenkolommen (volle breedte).

        R1/R5 (correctieronde 2): het resultaat van de laatste toetsing hoort
        bij één record (`editing_definition_id`) en wordt vóór weergave
        opnieuw aan de kandidaat gebonden zoals die nú in het formulier staat
        (`herbind_ess03_in_validatieresultaat`, pure replay — geen
        modelaanroep). Een eerder 'Voldoet' voor ESS-03 verschijnt dus nooit
        als actuele pass zodra tekst, term, context, bedoelde betekenis,
        verduidelijking, bronset of prompt/norm/model niet meer overeenkomen;
        het blijft zichtbaar als historisch.
        """
        try:
            results = self._actueel_sessieresultaat()
            if results:
                st.markdown("#### ✅ Kwaliteitstoetsing")
                self._show_validation_results(results)
            else:
                self._render_opgeslagen_int01()
        except (KeyError, TypeError, AttributeError):
            # KeyError: missing key, TypeError: wrong type, AttributeError: missing method
            pass

    @staticmethod
    def _bewaar_sessieresultaat(results: Any, def_id: Any) -> None:
        """Het enige schrijfpunt van `edit_last_validation` (DEF-770): bindt
        ieder vers resultaat (Valideren, voorsteltoepassing, opslaan) aan het
        record waarvoor het gemaakt is. De tekstbinding van INT-01 draagt het
        resultaat zelf (vingerafdruk van de getoetste tekst in
        `rule_results`), zodat geen producent haar kan vergeten."""
        if isinstance(results, dict) and def_id is not None:
            results = dict(results, editing_definition_id=def_id)
        SessionStateManager.set_value("edit_last_validation", results)

    def _actueel_sessieresultaat(self) -> dict[str, Any] | None:
        """`edit_last_validation` voor het record dat nu bewerkt wordt, met ESS-03
        herbonden aan het huidige formulier; None als er niets (meer) te tonen is.
        Een resultaat van een ander record wordt niet getoond en opgeruimd."""
        results = SessionStateManager.get_value("edit_last_validation")
        if not isinstance(results, dict):
            return None
        def_id = SessionStateManager.get_value("editing_definition_id")
        eigenaar = results.get("editing_definition_id")
        if eigenaar is not None and def_id is not None and eigenaar != def_id:
            SessionStateManager.set_value("edit_last_validation", None)
            return None
        definition = SessionStateManager.get_value("editing_definition")
        v2 = results.get("raw_v2")
        if definition is None or not isinstance(v2, dict):
            return results
        from services.definition_edit_service import (
            herbind_ess03_in_validatieresultaat,
            herbind_int01_in_validatieresultaat,
            herbind_int03_in_validatieresultaat,
        )

        kandidaat = self._kandidaat_uit_formulier(definition)
        herbonden = herbind_ess03_in_validatieresultaat(
            v2, kandidaat, binding=self._ess03_binding()
        )
        # DEF-770: INT-01 alleen voor exact de getoetste formuliertekst.
        herbonden = herbind_int01_in_validatieresultaat(
            herbonden, kandidaat.definitie or ""
        )
        # DEF-772: INT-03 alleen voor exact de getoetste term, tekst, context
        # en toelichting én de actuele prompt/norm/model; anders historisch.
        herbonden = herbind_int03_in_validatieresultaat(
            herbonden, kandidaat, binding=self._int03_binding()
        )
        if herbonden is v2:
            return results
        return {**results, "raw_v2": herbonden}

    def _render_opgeslagen_int01(self) -> None:
        """Zonder sessieresultaat: de opgeslagen INT-01-uitkomst (DEF-770),
        gebonden aan de tekst die nú in het formulier staat — anders zichtbaar
        niet toepasbaar of niet beoordeeld; nooit een oude pass."""
        definition = SessionStateManager.get_value("editing_definition")
        if definition is None:
            return
        from domain.int01.opslag import INT01_BEOORDELING_FIELD, weergavedetail
        from ui.components.validation_view import render_rule_results

        opgeslagen = (getattr(definition, "metadata", None) or {}).get(
            INT01_BEOORDELING_FIELD
        )
        kern = self._kandidaat_uit_formulier(definition).definitie or ""
        st.markdown("#### Opgeslagen INT-01-uitkomst (zinsgrenzen)")
        render_rule_results({"INT-01": weergavedetail(opgeslagen, kern)})

    def _show_validation_results(self, results: dict[str, Any]) -> None:
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
            return
        # Terugval zonder ruw V2-resultaat (sync pad / legacy): geen cijfer
        # (DEF-743, besluit 3), wel oordeel, dekking en regeluitkomsten.
        from ui.components.validation_view import (
            bereken_beoordelingsdekking,
            dekkingsregel,
            render_rule_results,
        )

        if results.get("valid"):
            st.success("✅ Validatie geslaagd (geen totaalcijfer; zie regeloordelen)")
        else:
            st.warning(
                "⚠️ Validatie problemen gevonden (geen totaalcijfer; zie regeloordelen)"
            )
        st.markdown(dekkingsregel(bereken_beoordelingsdekking(results)))
        rule_results = results.get("rule_results")
        if isinstance(rule_results, dict) and rule_results:
            render_rule_results(rule_results)
        for issue in results.get("issues") or []:
            if isinstance(issue, dict):
                st.markdown(
                    f"- {issue.get('rule') or '?'} ({issue.get('severity') or 'warning'}): "
                    f"{issue.get('message') or ''}"
                )

        # Let op: Geen extra 'Uitleg bij alle regels' sectie meer.
        # De gedeelde renderer toont inline uitleg per regel om duplicatie te voorkomen.

    def _undo_changes(self) -> None:
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

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(
                f"Undo error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "undo_changes",
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"Fout bij ongedaan maken: {e!s}")

    def _cancel_edit(self) -> None:
        """Cancel the edit session."""
        # Clear edit state using SessionStateManager. R1/R5: ook het resultaat
        # van de laatste toetsing — dat hoort bij de geannuleerde sessie en
        # mag bij heropenen niet als actueel oordeel terugkomen.
        for key in [
            "editing_definition_id",
            "editing_definition",
            "edit_session",
            "edit_last_validation",
        ]:
            SessionStateManager.set_value(key, None)

        st.info("Edit sessie geannuleerd")
        st.rerun()

    def _revert_to_version(self, version_id: int) -> None:
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

        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning(
                f"Revert error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "revert_to_version",
                    "version_id": version_id,
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"Fout bij herstellen: {e!s}")

    def _refresh_current_definition(self) -> None:
        """Refresh the current definition from database."""
        try:
            definition_id = SessionStateManager.get_value("editing_definition_id")
            if definition_id:
                definition = self.repository.get(definition_id)
                if definition:
                    SessionStateManager.set_value("editing_definition", definition)
                    st.rerun()

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(
                f"Refresh error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "refresh_current_definition",
                    "error_type": type(e).__name__,
                },
            )

    def _track_changes(self) -> None:
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
        def _norm_list(v: Any) -> list[str]:
            try:
                return sorted([str(x).strip() for x in (v or [])])
            except (TypeError, AttributeError):
                # TypeError: v not iterable or sorted() fails, AttributeError: strip() fails
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
                except (TypeError, AttributeError):
                    # TypeError: datetime subtraction fails, AttributeError: missing method
                    pass
            self._perform_auto_save()

    def _perform_auto_save(self) -> None:
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

            # Save (DEF-469: onderscheid SAVED / DISABLED / FAILED)
            result = self.edit_service.auto_save(definition_id, content)
            if result is AutoSaveResult.SAVED:
                SessionStateManager.set_value("last_auto_save", datetime.now())
            elif result is AutoSaveResult.FAILED:
                # Niet stil falen: waarschuw de gebruiker dat het concept niet is
                # opgeslagen (anders denkt die ten onrechte dat het bewaard is).
                st.warning(
                    "⚠️ Concept kon niet automatisch worden opgeslagen — "
                    "sla handmatig op om verlies te voorkomen."
                )

        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning(
                f"Auto-save error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "perform_auto_save",
                    "error_type": type(e).__name__,
                },
            )

    def _restore_auto_save(self, auto_save_content: dict[str, Any]) -> None:
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

        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.warning(
                f"Restore auto-save error: {e}",
                extra={
                    "component": "definition_edit_tab",
                    "operation": "restore_auto_save",
                    "error_type": type(e).__name__,
                },
            )
            st.error(f"Fout bij herstellen auto-save: {e!s}")

    def _format_datetime(self, dt: Any) -> str:
        """Format datetime for display."""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except (ValueError, TypeError):
                return cast(str, dt)

        if isinstance(dt, datetime):
            return dt.strftime("%d-%m-%Y %H:%M")

        return str(dt)

    # _hydrate_editor_fields verwijderd: niet nodig met ID-gescope widget keys

    def _ensure_edit_session_state(self) -> None:
        """Ensure edit session state variables exist via SessionStateManager."""
        # Gebruik SessionStateManager voor consistentie met de rest van de applicatie
        edit_defaults: dict[str, Any] = {
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
