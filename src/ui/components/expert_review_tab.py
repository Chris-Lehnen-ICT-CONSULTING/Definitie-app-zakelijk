"""
Expert Review Tab - Interface voor expert review en approval workflow.
"""

from datetime import datetime

import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from ui.session_state import SessionStateManager
from config.config_manager import get_config, ConfigSection


class ExpertReviewTab:
    """Tab voor expert review workflow."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer expert review tab."""
        self.repository = repository

    def render(self):
        """Render expert review tab."""
        # Prefill: toon laatst gegenereerde definitie met context (read-only) indien beschikbaar
        self._render_prefill_readonly_context()

        # Verboden woorden management sectie
        self._render_verboden_woorden_management()

        st.markdown("---")

        # Review queue sectie
        self._render_review_queue()

        # Selected definition review
        self._render_definition_review()

        # Review history
        self._render_review_history()

    def _render_review_queue(self):
        """Render lijst van definities awaiting review."""
        st.markdown("### 📋 Review Wachtrij")

        try:
            # Haal pending reviews op
            pending_reviews = self.repository.search_definities(
                status=DefinitieStatus.REVIEW, limit=50
            )

            if not pending_reviews:
                st.info("✅ Geen definities wachten op review")
                return

            # Verzamel unieke contextopties uit wachtrij (geparseerde lijsten)
            uniq_org: set[str] = set()
            uniq_jur: set[str] = set()
            uniq_wet: set[str] = set()
            for d in pending_reviews:
                org_list, jur_list, wet_list = self._parse_context_lists(d)
                uniq_org.update(org_list)
                uniq_jur.update(jur_list)
                uniq_wet.update(wet_list)

            # Filter en sort options
            st.markdown("#### Filters")
            col_search, col_sort = st.columns([2, 1])
            with col_search:
                search_filter = st.text_input(
                    "🔍 Zoek op begrip/definitie",
                    placeholder="Zoekterm...",
                    key="review_search",
                )
            with col_sort:
                sort_by = st.selectbox(
                    "Sorteer op",
                    ["Datum (nieuw eerst)", "Datum (oud eerst)", "Begrip A-Z", "Score"],
                    key="review_sort",
                )

            col_org, col_jur, col_wet = st.columns(3)
            with col_org:
                org_filter = st.multiselect(
                    "Organisatorisch",
                    options=sorted(uniq_org),
                    key="review_org_filter",
                    help="Filter op organisaties (één of meer)",
                )
                # Toon afkortingen-uitleg uit config (indien aanwezig)
                try:
                    ui_cfg = get_config(ConfigSection.UI)
                    abbrev = getattr(ui_cfg, 'afkortingen', {}) or {}
                    if abbrev:
                        with st.expander("ℹ️ Afkortingen (uitleg)", expanded=False):
                            for ak in sorted(abbrev.keys()):
                                st.markdown(f"- **{ak}** — {abbrev[ak]}")
                except Exception:
                    pass
            with col_jur:
                jur_filter = st.multiselect(
                    "Juridisch",
                    options=sorted(uniq_jur),
                    key="review_jur_filter",
                    help="Filter op rechtsgebieden (één of meer)",
                )
            with col_wet:
                wet_filter = st.multiselect(
                    "Wettelijk",
                    options=sorted(uniq_wet),
                    key="review_wet_filter",
                    help="Filter op wetten (één of meer)",
                )

            # Apply filters
            filtered_reviews = self._apply_filters(
                pending_reviews,
                search=search_filter,
                org_filter=org_filter,
                jur_filter=jur_filter,
                wet_filter=wet_filter,
                sort_by=sort_by,
            )

            # Display review queue
            st.markdown(f"**{len(filtered_reviews)} definities wachten op review:**")

            for definitie in filtered_reviews:
                self._render_review_queue_item(definitie)

        except Exception as e:
            st.error(f"❌ Kon review queue niet laden: {e!s}")

    def _render_review_queue_item(self, definitie: DefinitieRecord):
        """Render één item in review queue."""
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                # Begrip en definitie preview
                st.markdown(f"**{definitie.begrip}** ({definitie.categorie})")
                st.markdown(f"*{definitie.definitie[:100]}...*")
                # Geharmoniseerde contextweergave
                org, jur, wet = self._format_record_context(definitie)
                ctx_parts = []
                if org:
                    ctx_parts.append(f"Organisatorisch: {org}")
                if jur:
                    ctx_parts.append(f"Juridisch: {jur}")
                if wet:
                    ctx_parts.append(f"Wettelijk: {wet}")
                if ctx_parts:
                    st.caption(" | ".join(ctx_parts))

            with col2:
                # Metadata
                if definitie.validation_score:
                    score_color = (
                        "green"
                        if definitie.validation_score > 0.8
                        else "orange" if definitie.validation_score > 0.6 else "red"
                    )
                    st.markdown(
                        f"Score: <span style='color: {score_color}'>{definitie.validation_score:.2f}</span>",
                        unsafe_allow_html=True,
                    )

                if definitie.created_at:
                    st.caption(f"Gemaakt: {definitie.created_at.strftime('%Y-%m-%d')}")

                if definitie.created_by:
                    st.caption(f"Door: {definitie.created_by}")

            with col3:
                # Status info
                st.markdown("**Status**")
                st.markdown(f"🔄 {self._status_label(definitie.status)}")

                # Validation issues
                issues = definitie.get_validation_issues_list()
                if issues:
                    st.caption(f"⚠️ {len(issues)} issues")

            with col4:
                # Action buttons
                if st.button("📝 Review", key=f"review_{definitie.id}"):
                    SessionStateManager.set_value(
                        "selected_review_definition", definitie
                    )
                    st.rerun()

                if st.button("👁️ Preview", key=f"preview_{definitie.id}"):
                    self._show_definition_preview(definitie)

            st.markdown("---")

    def _render_definition_review(self):
        """Render detailed definition review interface."""
        selected_def = SessionStateManager.get_value("selected_review_definition")

        if not selected_def:
            st.info("👆 Selecteer een definitie uit de review wachtrij om te beginnen")
            return

        st.markdown(f"### 📝 Review: {selected_def.begrip}")

        # Definition details
        self._render_definition_details(selected_def)

        # Side-by-side comparison if edited
        self._render_comparison_view(selected_def)

        # Review acties (US-155): Vaststellen / Afwijzen / Maak bewerkbaar
        self._render_review_actions(selected_def)

    def _render_definition_details(self, definitie: DefinitieRecord):
        """Render uitgebreide definitie details."""
        with st.expander("📋 Definitie Details", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Definitie")
                st.info(definitie.definitie)

                st.markdown("#### Context")
                org_val, jur_val, wb_val = self._format_record_context(definitie)
                st.write(f"**Organisatorisch:** {org_val or '—'}")
                st.write(f"**Juridisch:** {jur_val or '—'}")
                st.write(f"**Wettelijke basis:** {wb_val or '—'}")
                st.write(f"**Categorie:** {definitie.categorie}")

                # Voorbeelden (hergebruik resolutie)
                try:
                    from ui.helpers.examples import resolve_examples

                    ex_key = f"review_examples_{definitie.id}"
                    examples = resolve_examples(ex_key, definitie)
                    if examples:
                        st.markdown("#### 📚 Gegenereerde Content")

                        def _render_list(title: str, key_name: str, empty_msg: str = "—"):
                            st.markdown(f"**{title}**")
                            items = []
                            try:
                                val = examples.get(key_name)
                                if isinstance(val, list):
                                    items = val
                                elif isinstance(val, str) and val.strip():
                                    items = [s.strip() for s in val.split(",") if s.strip()]
                            except Exception:
                                items = []
                            if items:
                                for it in items:
                                    st.markdown(f"- {str(it)}")
                            else:
                                st.caption(empty_msg)

                        _render_list("📄 Voorbeeldzinnen", "voorbeeldzinnen", "Geen voorbeeldzinnen")
                        _render_list("💼 Praktijkvoorbeelden", "praktijkvoorbeelden", "Geen praktijkvoorbeelden")
                        _render_list("❌ Tegenvoorbeelden", "tegenvoorbeelden", "Geen tegenvoorbeelden")
                        _render_list("🔄 Synoniemen", "synoniemen", "Geen synoniemen")
                        _render_list("↔️ Antoniemen", "antoniemen", "Geen antoniemen")

                        st.markdown("**📝 Toelichting**")
                        toel = ""
                        try:
                            val = examples.get("toelichting")
                            toel = val if isinstance(val, str) else ""
                        except Exception:
                            toel = ""
                        if toel:
                            st.info(toel)
                        else:
                            st.caption("Geen toelichting")

                    # Bewerken van voorbeelden (muteerbaar in review)
                    with st.expander("✏️ Bewerk Voorbeelden", expanded=False):
                        # Prefill: als resolver leeg is, haal DB-voorbeelden op per type
                        if not examples:
                            try:
                                db_examples = self.repository.get_voorbeelden_by_type(definitie.id)
                                if isinstance(db_examples, dict) and db_examples:
                                    examples = db_examples
                                    SessionStateManager.set_value(ex_key, examples)
                            except Exception:
                                pass

                        def _get_list(name: str) -> list[str]:
                            val = examples.get(name)
                            if isinstance(val, list):
                                return val
                            if isinstance(val, str) and val.strip():
                                return [s.strip() for s in val.split(",") if s.strip()]
                            return []

                        vz = st.text_area(
                            "📄 Voorbeeldzinnen (één per regel)",
                            value="\n".join(_get_list("voorbeeldzinnen")),
                            height=120,
                            key=f"vz_{definitie.id}",
                        )
                        pv = st.text_area(
                            "💼 Praktijkvoorbeelden (één per regel)",
                            value="\n".join(_get_list("praktijkvoorbeelden")),
                            height=120,
                            key=f"pv_{definitie.id}",
                        )
                        tv = st.text_area(
                            "❌ Tegenvoorbeelden (één per regel)",
                            value="\n".join(_get_list("tegenvoorbeelden")),
                            height=120,
                            key=f"tv_{definitie.id}",
                        )
                        syn = st.text_input(
                            "🔄 Synoniemen (komma-gescheiden)",
                            value=", ".join(_get_list("synoniemen")),
                            key=f"syn_{definitie.id}",
                        )
                        ant = st.text_input(
                            "↔️ Antoniemen (komma-gescheiden)",
                            value=", ".join(_get_list("antoniemen")),
                            key=f"ant_{definitie.id}",
                        )
                        tol = st.text_area(
                            "📝 Toelichting (korte tekst)",
                            value=str(examples.get("toelichting") or ""),
                            height=80,
                            key=f"tol_{definitie.id}",
                        )

                        col_s1, col_s2 = st.columns([1, 3])
                        with col_s1:
                            if st.button("💾 Voorbeelden opslaan", key=f"save_ex_{definitie.id}"):
                                try:
                                    def _split_lines(text: str) -> list[str]:
                                        return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

                                    def _split_csv(text: str) -> list[str]:
                                        return [p.strip() for p in (text or "").split(",") if p.strip()]

                                    new_examples: dict[str, list[str]] = {
                                        "voorbeeldzinnen": _split_lines(vz),
                                        "praktijkvoorbeelden": _split_lines(pv),
                                        "tegenvoorbeelden": _split_lines(tv),
                                        "synoniemen": _split_csv(syn),
                                        "antoniemen": _split_csv(ant),
                                    }
                                    if tol and tol.strip():
                                        new_examples["toelichting"] = [tol.strip()]

                                    # Persist to DB via repository helper
                                    reviewer = SessionStateManager.get_value("reviewer_name") or "expert"
                                    self.repository.save_voorbeelden(
                                        definitie_id=definitie.id,
                                        voorbeelden_dict=new_examples,
                                        gegenereerd_door=str(reviewer or "expert"),
                                        generation_model="manual",
                                        generation_params=None,
                                    )

                                    # Update in-session examples (flatten toelichting back to str)
                                    updated = {
                                        "voorbeeldzinnen": new_examples.get("voorbeeldzinnen", []),
                                        "praktijkvoorbeelden": new_examples.get("praktijkvoorbeelden", []),
                                        "tegenvoorbeelden": new_examples.get("tegenvoorbeelden", []),
                                        "synoniemen": new_examples.get("synoniemen", []),
                                        "antoniemen": new_examples.get("antoniemen", []),
                                        "toelichting": tol.strip() if tol and tol.strip() else "",
                                    }
                                    SessionStateManager.set_value(ex_key, updated)
                                    st.success("✅ Voorbeelden opgeslagen")
                                except Exception as e:
                                    st.error(f"❌ Opslaan mislukt: {e}")
                except Exception:
                    pass

            with col2:
                st.markdown("#### Metadata")
                st.write(f"**ID:** {definitie.id}")
                st.write(f"**Status:** {self._status_label(definitie.status)}")
                st.write(f"**Versie:** {definitie.version_number}")

                if definitie.validation_score:
                    st.write(f"**Score:** {definitie.validation_score:.2f}")

                if definitie.created_at:
                    st.write(
                        f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )

                if definitie.created_by:
                    st.write(f"**Door:** {definitie.created_by}")

                if definitie.source_type:
                    st.write(f"**Bron:** {definitie.source_type}")

        # Validation issues
        self._render_validation_issues(definitie)

    def _render_validation_issues(self, definitie: DefinitieRecord):
        """Render validation issues voor review."""
        issues = definitie.get_validation_issues_list()

        if not issues:
            st.success("✅ Geen validatie issues gevonden")
            return

        st.markdown("#### ⚠️ Validatie Issues")

        # Group by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        other_issues = [
            i for i in issues if i.get("severity") not in ["critical", "high"]
        ]

        if critical_issues:
            st.error("🚨 **Kritieke Issues** (moet opgelost worden)")
            for issue in critical_issues:
                st.write(
                    f"- {issue.get('rule_id', 'Unknown')}: {issue.get('description', 'No description')}"
                )

        if high_issues:
            st.warning("⚠️ **Hoge Prioriteit Issues**")
            for issue in high_issues:
                st.write(
                    f"- {issue.get('rule_id', 'Unknown')}: {issue.get('description', 'No description')}"
                )

        if other_issues:
            with st.expander(
                f"📋 Overige Issues ({len(other_issues)})", expanded=False
            ):
                for issue in other_issues:
                    st.write(
                        f"- {issue.get('rule_id', 'Unknown')}: {issue.get('description', 'No description')}"
                    )

    def _render_review_actions(self, definitie: DefinitieRecord):
        """Render US-155 acties: Vaststellen, Afwijzen, Maak bewerkbaar."""
        from services.container import get_container
        container = get_container()
        workflow = container.definition_workflow_service()

        status = definitie.status
        label = self._status_label(status)
        st.markdown(f"**Huidige status:** {label}")

        if status == 'review':
            # US-160: Gate preview tonen en knoppenstate bepalen
            try:
                gate = workflow.preview_gate(definitie.id)
            except Exception:
                gate = {"status": "blocked", "reasons": ["Technische fout bij gate‑preview"]}

            gate_status = gate.get("status", "blocked")
            gate_reasons = gate.get("reasons", []) or []

            # Indicator
            if gate_status == "pass":
                st.success("✅ Gate: toegestaan om vast te stellen")
            elif gate_status == "override_required":
                st.warning("⚠️ Gate: override vereist (reden verplicht)")
                with st.expander("Reden(en)", expanded=False):
                    for r in gate_reasons:
                        st.write(f"- {r}")
            else:  # blocked
                st.error("🚫 Gate: blokkade — voldoet niet aan criteria")
                with st.expander("Reden(en)", expanded=False):
                    for r in gate_reasons:
                        st.write(f"- {r}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ✅ Vaststellen")
                # Bij override_required moet een reden worden opgegeven
                notes_label = (
                    "Reden (verplicht bij override)" if gate_status == "override_required" else "Notities (optioneel)"
                )
                notes = st.text_area(notes_label, key=f"approve_notes_{definitie.id}", height=80)

                # Ketenpartners selectie
                from config.config_manager import get_config, ConfigSection
                ui_cfg = get_config(ConfigSection.UI)
                partner_opties = list(getattr(ui_cfg, "ketenpartners", []))
                geselecteerd = st.multiselect(
                    "🤝 Ketenpartners die akkoord zijn",
                    options=partner_opties,
                    default=definitie.get_ketenpartners_list() if hasattr(definitie, "get_ketenpartners_list") else [],
                    key=f"approve_ketenpartners_{definitie.id}",
                    help="Selecteer alle partners die expliciet akkoord zijn met deze definitie."
                )

                approve_label = (
                    "Vaststellen met override" if gate_status == "override_required" else "Vaststellen"
                )
                approve_disabled = gate_status == "blocked" or (
                    gate_status == "override_required" and not (notes and notes.strip())
                )
                approve_help = None
                if gate_status == "blocked":
                    approve_help = "Gate blokkeert vaststellen — los issues op of vul ontbrekende velden"
                elif gate_status == "override_required" and not (notes and notes.strip()):
                    approve_help = "Voer een reden in voor de override"

                if st.button(
                    approve_label,
                    key=f"approve_btn_{definitie.id}",
                    type="primary",
                    disabled=approve_disabled,
                    help=approve_help,
                ):
                    user = st.session_state.get('user', 'expert')
                    res = workflow.approve(
                        definition_id=definitie.id,
                        user=user,
                        notes=notes or "",
                        ketenpartners=geselecteerd,
                    )
                    if res.success:
                        st.success("✅ Definitie vastgesteld")
                        st.rerun()
                    else:
                        st.error(f"❌ Vaststellen mislukt: {res.error_message or 'Onbekende fout'}")
            with col2:
                st.markdown("#### ❌ Afwijzen")
                reason = st.text_area(
                    "Reden (verplicht)", key=f"reject_reason_{definitie.id}", height=80
                )
                disabled = not bool(reason and reason.strip())
                if st.button("Afwijzen", key=f"reject_btn_{definitie.id}", disabled=disabled):
                    user = st.session_state.get('user', 'expert')
                    res = workflow.reject(definition_id=definitie.id, user=user, reason=reason.strip())
                    if res.success:
                        st.success("✅ Definitie afgewezen (terug naar Concept)")
                        st.rerun()
                    else:
                        st.error(f"❌ Afwijzen mislukt: {res.error_message or 'Onbekende fout'}")

        elif status == 'established':
            st.markdown("#### 🔓 Maak bewerkbaar")
            reason = st.text_area(
                "Reden (verplicht)", key=f"unlock_reason_{definitie.id}", height=80
            )
            disabled = not bool(reason and reason.strip())
            if st.button("Maak bewerkbaar (naar Concept)", key=f"unlock_btn_{definitie.id}", disabled=disabled):
                user = st.session_state.get('user', 'expert')
                # Gebruik DefinitionWorkflowService voor consistente statuswijziging
                try:
                    from services.container import get_container
                    container = get_container()
                    workflow = container.definition_workflow_service()
                    ok = workflow.update_status(
                        definition_id=definitie.id,
                        new_status="draft",
                        user=user,
                        notes=reason.strip(),
                    )
                except Exception:
                    ok = False
                if ok:
                    st.success("✅ Status teruggezet naar Concept; bewerken weer mogelijk")
                    st.rerun()
                else:
                    st.error("❌ Terugzetten mislukt")

        elif status == 'archived':
            st.markdown("#### ♻️ Herstel uit archief")
            reason = st.text_area(
                "Reden (verplicht)", key=f"restore_reason_{definitie.id}", height=80
            )
            disabled = not bool(reason and reason.strip())
            if st.button("Herstel (naar Concept)", key=f"restore_btn_{definitie.id}", disabled=disabled):
                user = st.session_state.get('user', 'expert')
                try:
                    from services.container import get_container
                    container = get_container()
                    workflow = container.definition_workflow_service()
                    ok = workflow.update_status(
                        definition_id=definitie.id,
                        new_status="draft",
                        user=user,
                        notes=reason.strip(),
                    )
                except Exception:
                    ok = False
                if ok:
                    st.success("✅ Definitie hersteld uit archief (Concept)")
                    st.rerun()
                else:
                    st.error("❌ Herstellen mislukt")

    def _render_comparison_view(self, definitie: DefinitieRecord):
        """Render side-by-side comparison view voor edits."""
        st.markdown("#### ✏️ Definitie Bewerking")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Originele AI Definitie**")
            st.info(definitie.definitie)

        with col2:
            st.markdown("**Expert Aangepaste Versie**")

            # Editable text area
            edited_definitie = st.text_area(
                "Bewerk definitie",
                value=definitie.definitie,
                height=100,
                key=f"edit_def_{definitie.id}",
                help="Pas de definitie aan volgens expert kennnis",
            )

            # Show changes
            if edited_definitie != definitie.definitie:
                st.info("✏️ Definitie aangepast")
                SessionStateManager.set_value(
                    f"edited_definition_{definitie.id}", edited_definitie
                )
            else:
                SessionStateManager.clear_value(f"edited_definition_{definitie.id}")

    def _render_review_form(self, definitie: DefinitieRecord):
        """Render review form met approval options."""
        st.markdown("#### 🎯 Review Beslissing")

        # Review decision
        col1, col2 = st.columns([1, 2])

        with col1:
            review_decision = st.radio(
                "Review beslissing",
                ["👍 Goedkeuren", "📝 Wijzigingen Vereist", "❌ Afwijzen"],
                key=f"decision_{definitie.id}",
            )

        with col2:
            # Review comments
            review_comments = st.text_area(
                "Review opmerkingen",
                placeholder="Voeg opmerkingen toe over de definitie, wijzigingen, of redenen voor goedkeuring/afwijzing...",
                height=100,
                key=f"comments_{definitie.id}",
            )

        # Reviewer info
        reviewer_name = st.text_input(
            "Reviewer naam",
            value=SessionStateManager.get_value("reviewer_name", ""),
            key="reviewer_name_input",
        )
        SessionStateManager.set_value("reviewer_name", reviewer_name)

        # Review actions
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(
                "✅ Submit Review", type="primary", key=f"submit_{definitie.id}"
            ):
                self._submit_review(
                    definitie, review_decision, review_comments, reviewer_name
                )

        with col2:
            if st.button("💾 Save Draft", key=f"save_{definitie.id}"):
                self._save_review_draft(definitie, review_decision, review_comments)

        with col3:
            if st.button("🔄 Re-validate", key=f"revalidate_{definitie.id}"):
                self._revalidate_definition(definitie)

        with col4:
            if st.button("🚫 Cancel", key=f"cancel_{definitie.id}"):
                SessionStateManager.clear_value("selected_review_definition")
                st.rerun()

        # Full-width render area for (re-)validation details
        try:
            vkey = f"review_v2_validation_{definitie.id}"
            v2 = SessionStateManager.get_value(vkey)
            if v2:
                from ui.components.validation_view import render_validation_detailed_list
                st.markdown("#### ✅ Kwaliteitstoetsing")
                render_validation_detailed_list(v2, key_prefix=f"review_{definitie.id}", show_toggle=True, gate=None)
        except Exception:
            pass

    def _render_review_history(self):
        """Render review geschiedenis."""
        if st.checkbox("📜 Toon Review Geschiedenis", key="show_history"):
            st.markdown("### 📜 Recente Reviews")

            try:
                # Haal recent reviewed definities op
                recent_reviews = self.repository.search_definities(
                    status=DefinitieStatus.ESTABLISHED, limit=10
                )

                if recent_reviews:
                    for definitie in recent_reviews:
                        if definitie.approved_by and definitie.approved_at:
                            with st.expander(
                                f"{definitie.begrip} - Goedgekeurd door {definitie.approved_by}",
                                expanded=False,
                            ):
                                st.write(f"**Definitie:** {definitie.definitie}")
                                st.write(
                                    f"**Goedgekeurd op:** {definitie.approved_at.strftime('%Y-%m-%d %H:%M')}"
                                )
                                if definitie.approval_notes:
                                    st.write(
                                        f"**Notities:** {definitie.approval_notes}"
                                    )
                else:
                    st.info("Geen recente reviews gevonden")

            except Exception as e:
                st.error(f"❌ Kon review geschiedenis niet laden: {e!s}")

    def _submit_review(
        self, definitie: DefinitieRecord, decision: str, comments: str, reviewer: str
    ):
        """Submit review decision."""
        if not reviewer.strip():
            st.error("❌ Voer reviewer naam in")
            return

        try:
            # Check voor aangepaste definitie
            edited_def = SessionStateManager.get_value(
                f"edited_definition_{definitie.id}"
            )

            if edited_def and edited_def != definitie.definitie:
                # Update definitie met wijzigingen
                self.repository.update_definitie(
                    definitie.id, {"definitie": edited_def}, reviewer
                )

            # Process decision
            if "Goedkeuren" in decision:
                # Route via DefinitionWorkflowService om gate‑policy te handhaven (US‑160)
                try:
                    from services.container import get_container

                    container = get_container()
                    workflow_service = container.definition_workflow_service()

                    result = workflow_service.submit_for_review(
                        definition_id=definitie.id,
                        user=reviewer,
                        notes=comments or "",
                    )

                    if getattr(result, "success", False):
                        st.success("✅ Definitie goedgekeurd!")
                        # Toon gate‑status informatief
                        if getattr(result, "gate_status", None):
                            st.caption(
                                f"Gate: {result.gate_status}"
                                + (
                                    f" — redenen: {', '.join(result.gate_reasons or [])}"
                                    if getattr(result, "gate_reasons", None)
                                    else ""
                                )
                            )
                        self._clear_review_session(definitie.id)
                        st.rerun()
                    else:
                        # Toon duidelijke melding incl. gate redenen indien aanwezig
                        msg = getattr(result, "error_message", "Kon definitie niet goedkeuren") or "Kon definitie niet goedkeuren"
                        st.error(f"❌ {msg}")
                        if getattr(result, "gate_status", None):
                            st.info(
                                f"Gate: {result.gate_status}"
                                + (
                                    f" — redenen: {', '.join(result.gate_reasons or [])}"
                                    if getattr(result, "gate_reasons", None)
                                    else ""
                                )
                            )
                except Exception as se:
                    st.error(f"❌ Gate‑workflow fout: {se!s}")

            elif "Wijzigingen Vereist" in decision:
                # Keep in review status but add feedback
                self.repository.update_definitie(
                    definitie.id, {"approval_notes": comments}, reviewer
                )
                st.warning("⚠️ Wijzigingen gemarkeerd - definitie blijft in review")

            elif "Afwijzen" in decision:
                success = self.repository.change_status(
                    definitie.id,
                    DefinitieStatus.ARCHIVED,
                    reviewer,
                    f"Afgewezen: {comments}",
                )

                if success:
                    st.error("❌ Definitie afgewezen")
                    self._clear_review_session(definitie.id)
                    st.rerun()
                else:
                    st.error("❌ Kon definitie niet afwijzen")

        except Exception as e:
            st.error(f"❌ Fout bij review submission: {e!s}")

    def _save_review_draft(
        self, definitie: DefinitieRecord, decision: str, comments: str
    ):
        """Save review als draft."""
        st.info("💾 Draft opgeslagen (functionaliteit komt binnenkort)")

    def _revalidate_definition(self, definitie: DefinitieRecord):
        """Re-validate definitie met current rules en toon details (gedeeld)."""
        try:
            from services.container import get_container
            from services.interfaces import Definition
            from services.validation.interfaces import ValidationContext
            from ui.helpers.async_bridge import run_async

            container = get_container()
            orch = container.orchestrator()

            # Build Definition from record
            definition = Definition(
                begrip=definitie.begrip,
                definitie=definitie.definitie,
                organisatorische_context=definitie.get_org_list() if hasattr(definitie, 'get_org_list') else [],
                juridische_context=definitie.get_jur_list() if hasattr(definitie, 'get_jur_list') else [],
                wettelijke_basis=definitie.get_wettelijke_basis_list() if hasattr(definitie, 'get_wettelijke_basis_list') else [],
                categorie=definitie.categorie,
            )
            ctx = ValidationContext(
                correlation_id=None,
                metadata={
                    "organisatorische_context": definition.organisatorische_context or [],
                    "juridische_context": definition.juridische_context or [],
                    "wettelijke_basis": definition.wettelijke_basis or [],
                },
            )
            v2 = run_async(orch.validation_service.validate_definition(definition, ctx))
            # Sla resultaat op en render buiten de kolommen (full-width)
            vkey = f"review_v2_validation_{definitie.id}"
            if isinstance(v2, dict):
                SessionStateManager.set_value(vkey, v2)
            else:
                SessionStateManager.set_value(vkey, None)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Re-validatie mislukt: {e!s}")

    def _clear_review_session(self, definitie_id: int):
        """Clear review session data."""
        SessionStateManager.clear_value("selected_review_definition")
        SessionStateManager.clear_value(f"edited_definition_{definitie_id}")

    def _format_record_context(self, definitie: DefinitieRecord) -> tuple[str, str, str]:
        """Normaliseer en formatteer context (org/jur/wet) voor weergave."""
        import json as _json

        def _parse(val) -> list[str]:
            try:
                if not val:
                    return []
                if isinstance(val, str):
                    return list(_json.loads(val)) if val.strip().startswith("[") else [val]
                if isinstance(val, list):
                    return val
            except Exception:
                return []
            return []

        org_list = _parse(getattr(definitie, "organisatorische_context", None))
        jur_list = _parse(getattr(definitie, "juridische_context", None))
        wet_list = definitie.get_wettelijke_basis_list() if hasattr(definitie, 'get_wettelijke_basis_list') else []
        return ", ".join(org_list), ", ".join(jur_list), ", ".join(wet_list)

    def _show_definition_preview(self, definitie: DefinitieRecord):
        """Show quick definition preview."""
        with st.expander(f"👁️ Preview: {definitie.begrip}", expanded=True):
            st.info(definitie.definitie)
            org, jur, wet = self._format_record_context(definitie)
            parts = []
            if org:
                parts.append(f"Organisatorisch: {org}")
            if jur:
                parts.append(f"Juridisch: {jur}")
            if wet:
                parts.append(f"Wettelijk: {wet}")
            st.caption(
                f"Context: {' | '.join(parts) if parts else '—'} | Score: {definitie.validation_score:.2f if definitie.validation_score else 'N/A'}"
            )

    def _apply_filters(
        self,
        reviews: list[DefinitieRecord],
        search: str,
        org_filter: list[str],
        jur_filter: list[str],
        wet_filter: list[str],
        sort_by: str,
    ) -> list[DefinitieRecord]:
        """Apply filters en sorting to review list."""
        filtered = reviews

        # Search filter
        if search.strip():
            filtered = [
                r
                for r in filtered
                if search.lower() in r.begrip.lower()
                or search.lower() in r.definitie.lower()
            ]

        # Context filters (V2): overlappende selectie per categorie, AND tussen categorieën
        if org_filter:
            filtered = [
                r
                for r in filtered
                if set(org_filter) & set(self._parse_context_lists(r)[0])
            ]
        if jur_filter:
            filtered = [
                r
                for r in filtered
                if set(jur_filter) & set(self._parse_context_lists(r)[1])
            ]
        if wet_filter:
            filtered = [
                r
                for r in filtered
                if set(wet_filter) & set(self._parse_context_lists(r)[2])
            ]

        # Sorting
        if sort_by == "Datum (nieuw eerst)":
            filtered.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        elif sort_by == "Datum (oud eerst)":
            filtered.sort(key=lambda x: x.created_at or datetime.min, reverse=False)
        elif sort_by == "Begrip A-Z":
            filtered.sort(key=lambda x: x.begrip.lower())
        elif sort_by == "Score":
            filtered.sort(key=lambda x: x.validation_score or 0, reverse=True)

        return filtered

    def _parse_context_lists(self, definitie: DefinitieRecord) -> tuple[list[str], list[str], list[str]]:
        """Parseer org/jur (JSON/str) en wet (helper) naar lijsten."""
        import json as _json

        def _parse(val) -> list[str]:
            try:
                if not val:
                    return []
                if isinstance(val, str):
                    return list(_json.loads(val)) if val.strip().startswith("[") else [val]
                if isinstance(val, list):
                    return val
            except Exception:
                return []
            return []

        org_list = _parse(getattr(definitie, "organisatorische_context", None))
        jur_list = _parse(getattr(definitie, "juridische_context", None))
        wet_list = (
            definitie.get_wettelijke_basis_list()
            if hasattr(definitie, "get_wettelijke_basis_list")
            else []
        )
        return org_list, jur_list, wet_list

    def _render_verboden_woorden_management(self):
        """Render verboden woorden runtime management interface."""
        st.markdown("### 🚫 Verboden Woorden Management")

        with st.expander(
            "Configureer verboden woorden voor definitie opschoning", expanded=False
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Import verboden woorden functionaliteit
                try:
                    from config.verboden_woorden import (
                        laad_verboden_woorden,
                    )

                    # Huidige verboden woorden laden
                    huidige_woorden = laad_verboden_woorden()
                    woorden_str = ", ".join(huidige_woorden) if huidige_woorden else ""

                    # Text area voor editing
                    nieuwe_woorden = st.text_area(
                        "Verboden woorden (gescheiden door komma's)",
                        value=woorden_str,
                        height=100,
                        help="Deze woorden worden automatisch verwijderd uit het begin van definities",
                    )

                    # Override toggle
                    override_actief = st.checkbox(
                        "Activeer runtime override",
                        value=SessionStateManager.get_value("override_actief", False),
                        help="Overschrijft de standaard configuratie met deze woorden",
                    )

                    # Update session state
                    SessionStateManager.set_value("override_actief", override_actief)
                    SessionStateManager.set_value(
                        "override_verboden_woorden", nieuwe_woorden
                    )

                    # Test sectie
                    st.markdown("#### 🧪 Test Opschoning")
                    test_definitie = st.text_input(
                        "Test definitie",
                        placeholder="bijv. 'Is het proces waarbij een persoon wordt geïdentificeerd.'",
                        help="Test hoe de opschoning werkt met je verboden woorden",
                    )

                    test_begrip = st.text_input(
                        "Test begrip",
                        placeholder="bijv. 'identificatie'",
                        help="Het begrip dat gedefinieerd wordt",
                    )

                    if st.button("🔄 Test Opschoning"):
                        if test_definitie and test_begrip:
                            try:
                                from opschoning.opschoning import opschonen

                                opgeschoond = opschonen(test_definitie, test_begrip)

                                st.markdown("**Resultaat:**")
                                col_orig, col_clean = st.columns(2)

                                with col_orig:
                                    st.markdown("*Origineel:*")
                                    st.error(test_definitie)

                                with col_clean:
                                    st.markdown("*Opgeschoond:*")
                                    st.success(opgeschoond)

                                if test_definitie != opgeschoond:
                                    st.info(
                                        "✅ Opschoning heeft wijzigingen aangebracht"
                                    )
                                else:
                                    st.warning("i️ Geen wijzigingen nodig")

                            except ImportError:
                                st.error("❌ Opschoning module niet beschikbaar")
                            except Exception as e:
                                st.error(f"❌ Fout bij opschoning: {e}")
                        else:
                            st.warning("⚠️ Voer zowel een definitie als begrip in")

                except ImportError:
                    st.error("❌ Verboden woorden management niet beschikbaar")
                except Exception as e:
                    st.error(f"❌ Fout bij laden verboden woorden: {e}")

            with col2:
                st.markdown("#### 📋 Standaard Verboden Woorden")
                default_words = [
                    "is",
                    "zijn",
                    "wordt",
                    "betekent",
                    "omvat",
                    "behelst",
                    "houdt in",
                    "betreft",
                    "gaat over",
                    "heeft betrekking op",
                    "de",
                    "het",
                    "een",
                    "proces waarbij",
                    "handeling waarbij",
                    "activiteit waarbij",
                    "methode waarbij",
                ]

                for word in default_words[:8]:  # Toon eerste 8
                    st.code(word)

                if len(default_words) > 8:
                    st.caption(f"... en {len(default_words) - 8} meer")

                # Status indicator
                st.markdown("#### 🔧 Status")
                if SessionStateManager.get_value("override_actief", False):
                    st.success("✅ Runtime override actief")
                else:
                    st.info("i️ Standaard configuratie")

                # Quick actions
                if st.button("🔄 Reset naar standaard"):
                    SessionStateManager.set_value("override_actief", False)
                    SessionStateManager.set_value("override_verboden_woorden", "")
                    st.rerun()
    def _render_prefill_readonly_context(self):
        """Render read-only contextpaneel voor laatst gegenereerde definitie (prefill)."""
        try:
            sel_id = SessionStateManager.get_value("selected_review_definition_id")
            if not sel_id:
                return
            definitie = self.repository.get_definitie(sel_id)
            if not definitie:
                return

            st.markdown("### ⭐ Laatst Gegenereerde Definitie (alleen lezen)")
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Begrip:** {definitie.begrip}")
                    st.markdown("**Definitie:**")
                    st.info(definitie.definitie)

                with col2:
                    st.markdown("**Context**")
                    st.write(f"Organisatie: {definitie.organisatorische_context}")
                    if definitie.juridische_context:
                        st.write(f"Juridisch: {definitie.juridische_context}")
                    # Wettelijke basis (JSON TEXT → list via helper)
                    wb = definitie.get_wettelijke_basis_list()
                    if wb:
                        st.write(f"Wettelijke basis: {', '.join(wb)}")
                    # Status (code) tonen als label in Nederlands
                    label = self._status_label(definitie.status)
                    st.write(f"Status: {label}")

            st.markdown("---")
        except Exception as e:
            st.warning(f"Kon prefill niet tonen: {e!s}")

    def _status_label(self, code: str) -> str:
        """Geef Nederlands label voor statuscode."""
        mapping = {
            'draft': 'Concept',
            'review': 'In review',
            'established': 'Vastgesteld',
            'archived': 'Gearchiveerd',
        }
        return mapping.get(code, code)
