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


class ExpertReviewTab:
    """Tab voor expert review workflow."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer expert review tab."""
        self.repository = repository

    def render(self):
        """Render expert review tab."""
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

            # Filter en sort options
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                search_filter = st.text_input(
                    "🔍 Filter definities",
                    placeholder="Zoek op begrip...",
                    key="review_search",
                )

            with col2:
                sort_by = st.selectbox(
                    "Sorteer op",
                    ["Datum (nieuw eerst)", "Datum (oud eerst)", "Begrip A-Z", "Score"],
                    key="review_sort",
                )

            with col3:
                context_filter = st.selectbox(
                    "Filter context",
                    [
                        "Alle",
                        *list({d.organisatorische_context for d in pending_reviews}),
                    ],
                    key="review_context_filter",
                )

            # Apply filters
            filtered_reviews = self._apply_filters(
                pending_reviews, search_filter, context_filter, sort_by
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
                st.caption(f"Context: {definitie.organisatorische_context}")

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
                st.markdown(f"🔄 {definitie.status}")

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

        # Review form
        self._render_review_form(selected_def)

    def _render_definition_details(self, definitie: DefinitieRecord):
        """Render uitgebreide definitie details."""
        with st.expander("📋 Definitie Details", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Definitie")
                st.info(definitie.definitie)

                st.markdown("#### Context")
                st.write(f"**Organisatorisch:** {definitie.organisatorische_context}")
                if definitie.juridische_context:
                    st.write(f"**Juridisch:** {definitie.juridische_context}")
                st.write(f"**Categorie:** {definitie.categorie}")

            with col2:
                st.markdown("#### Metadata")
                st.write(f"**ID:** {definitie.id}")
                st.write(f"**Status:** {definitie.status}")
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
                success = self.repository.change_status(
                    definitie.id, DefinitieStatus.ESTABLISHED, reviewer, comments
                )

                if success:
                    st.success("✅ Definitie goedgekeurd!")
                    self._clear_review_session(definitie.id)
                    st.rerun()
                else:
                    st.error("❌ Kon definitie niet goedkeuren")

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
        # TODO: Implement draft saving
        st.info("💾 Draft opgeslagen (functionaliteit komt binnenkort)")

    def _revalidate_definition(self, definitie: DefinitieRecord):
        """Re-validate definitie met current rules."""
        # TODO: Implement revalidation
        st.info("🔄 Re-validatie gestart (functionaliteit komt binnenkort)")

    def _clear_review_session(self, definitie_id: int):
        """Clear review session data."""
        SessionStateManager.clear_value("selected_review_definition")
        SessionStateManager.clear_value(f"edited_definition_{definitie_id}")

    def _show_definition_preview(self, definitie: DefinitieRecord):
        """Show quick definition preview."""
        with st.expander(f"👁️ Preview: {definitie.begrip}", expanded=True):
            st.info(definitie.definitie)
            st.caption(
                f"Context: {definitie.organisatorische_context} | Score: {definitie.validation_score:.2f if definitie.validation_score else 'N/A'}"
            )

    def _apply_filters(
        self, reviews: list[DefinitieRecord], search: str, context: str, sort_by: str
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

        # Context filter
        if context != "Alle":
            filtered = [r for r in filtered if r.organisatorische_context == context]

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
                                    st.warning("ℹ️ Geen wijzigingen nodig")

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
                    st.info("ℹ️ Standaard configuratie")

                # Quick actions
                if st.button("🔄 Reset naar standaard"):
                    SessionStateManager.set_value("override_actief", False)
                    SessionStateManager.set_value("override_verboden_woorden", "")
                    st.rerun()
