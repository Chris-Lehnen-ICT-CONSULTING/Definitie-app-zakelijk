"""
Synonym Review Tab - UI voor het reviewen en goedkeuren van AI-gegenereerde synoniemen.

Deze tab biedt:
- Overzicht van pending/approved/rejected suggestions
- Filter- en zoekfunctionaliteit
- Approve/Reject acties met rationale
- Bulk operaties met confirmatie
- Real-time statistieken
"""

import logging
from datetime import datetime

import streamlit as st

from repositories.synonym_repository import (
    SuggestionStatus,
    SynonymRepository,
    SynonymSuggestionRecord,
)
from services.synonym_automation.workflow import SynonymWorkflow

logger = logging.getLogger(__name__)


class SynonymReviewTab:
    """Tab voor synonym suggestion review workflow."""

    def __init__(self):
        """Initialiseer synonym review tab met repository en workflow."""
        self.repository = SynonymRepository()
        self.workflow = SynonymWorkflow(repository=self.repository)

    def render(self):
        """Render synonym review tab."""
        st.markdown("## 🔍 Synoniem Review & Goedkeuring")
        st.markdown(
            "Review en keur AI-gegenereerde synoniemen goed voor gebruik in de definitie generator."
        )

        # Statistics panel bovenaan
        self._render_statistics_panel()

        st.markdown("---")

        # Filters section
        filters = self._render_filters_section()

        st.markdown("---")

        # Suggestions table
        self._render_suggestions_table(filters)

    def _render_statistics_panel(self):
        """Render statistieken panel met totalen en scores."""
        try:
            stats = self.repository.get_statistics()

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                total = stats.get("total", 0)
                st.metric("📊 Totaal Suggesties", total)

            with col2:
                pending = stats.get("by_status", {}).get(
                    SuggestionStatus.PENDING.value, 0
                )
                st.metric("⏳ Pending", pending, delta=None)

            with col3:
                approved = stats.get("by_status", {}).get(
                    SuggestionStatus.APPROVED.value, 0
                )
                st.metric("✅ Approved", approved, delta=None)

            with col4:
                rejected = stats.get("by_status", {}).get(
                    SuggestionStatus.REJECTED.value, 0
                )
                st.metric("❌ Rejected", rejected, delta=None)

            with col5:
                # Average confidence voor pending
                avg_conf = stats.get("avg_confidence_by_status", {}).get(
                    SuggestionStatus.PENDING.value, 0.0
                )
                st.metric("🎯 Avg Confidence", f"{avg_conf:.2f}")

            # Approval rate (indien relevant)
            if stats.get("approval_rate") is not None:
                approval_rate = stats["approval_rate"]
                st.caption(f"📈 Approval Rate: {approval_rate:.1%}")

        except Exception as e:
            st.error(f"❌ Kon statistieken niet laden: {e}")
            logger.error(f"Statistics panel error: {e}", exc_info=True)

    def _render_filters_section(self) -> dict:
        """Render filters sectie en return filter criteria."""
        st.markdown("### 🔎 Filters")

        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            # Status filter
            status_options = ["Alle", "Pending", "Approved", "Rejected"]
            status_filter = st.radio(
                "Status",
                status_options,
                horizontal=True,
                key="synonym_status_filter",
                help="Filter op suggestion status",
            )

        with col2:
            # Hoofdterm zoeken
            search_term = st.text_input(
                "🔍 Zoek Hoofdterm",
                placeholder="bijv. authenticatie...",
                key="synonym_search",
                help="Zoek op hoofdterm (exact match)",
            )

        with col3:
            # Confidence threshold slider
            min_confidence = st.slider(
                "Min. Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.1,
                key="synonym_confidence",
                help="Minimum confidence score (0.0-1.0)",
            )

        with col4:
            # Refresh button
            if st.button("🔄 Refresh", key="synonym_refresh", help="Herlaad data"):
                st.rerun()

        return {
            "status": status_filter,
            "hoofdterm": search_term.strip() if search_term else None,
            "min_confidence": min_confidence,
        }

    def _render_suggestions_table(self, filters: dict):
        """Render suggestions tabel met acties."""
        try:
            # Haal suggestions op basis van filters
            suggestions = self._get_filtered_suggestions(filters)

            if not suggestions:
                st.info(
                    "📭 Geen suggesties gevonden met de huidige filters. "
                    "Probeer de filters aan te passen."
                )
                return

            st.markdown(f"### 📋 Suggesties ({len(suggestions)})")

            # Pagination state
            items_per_page = 20
            total_pages = (len(suggestions) - 1) // items_per_page + 1

            # Get current page from session state
            current_page = st.session_state.get("synonym_page", 1)
            if current_page > total_pages:
                current_page = 1

            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input(
                    "Pagina",
                    min_value=1,
                    max_value=total_pages,
                    value=current_page,
                    key="synonym_page_input",
                )
                st.session_state["synonym_page"] = page

            # Paginate suggestions
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_suggestions = suggestions[start_idx:end_idx]

            # Bulk actions (only for pending)
            pending_on_page = [
                s
                for s in page_suggestions
                if s.status == SuggestionStatus.PENDING.value
            ]
            if pending_on_page:
                self._render_bulk_actions(pending_on_page)

            # Render suggestions as expandable cards
            for suggestion in page_suggestions:
                self._render_suggestion_card(suggestion)

        except Exception as e:
            st.error(f"❌ Fout bij laden suggesties: {e}")
            logger.error(f"Suggestions table error: {e}", exc_info=True)

    def _get_filtered_suggestions(self, filters: dict) -> list[SynonymSuggestionRecord]:
        """Haal gefilterde suggestions op uit repository."""
        status_filter = filters["status"]
        hoofdterm_filter = filters["hoofdterm"]
        min_confidence = filters["min_confidence"]

        # Map UI status naar enum
        if status_filter == "Alle":
            # Haal alle suggestions op en filter lokaal
            all_suggestions = []
            for status in SuggestionStatus:
                all_suggestions.extend(
                    self.repository.get_suggestions_by_status(status)
                )
            suggestions = all_suggestions
        elif status_filter == "Pending":
            suggestions = self.repository.get_pending_suggestions(
                hoofdterm_filter=hoofdterm_filter, min_confidence=min_confidence
            )
        elif status_filter == "Approved":
            suggestions = self.repository.get_suggestions_by_status(
                SuggestionStatus.APPROVED
            )
        elif status_filter == "Rejected":
            suggestions = self.repository.get_suggestions_by_status(
                SuggestionStatus.REJECTED
            )
        else:
            suggestions = []

        # Extra filtering voor non-pending statuses
        if status_filter != "Pending":
            if hoofdterm_filter:
                suggestions = [
                    s for s in suggestions if s.hoofdterm == hoofdterm_filter
                ]
            if min_confidence > 0.0:
                suggestions = [s for s in suggestions if s.confidence >= min_confidence]

        # Sort by confidence descending
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return suggestions

    def _render_suggestion_card(self, suggestion: SynonymSuggestionRecord):
        """Render één suggestion als expandable card."""
        # Color coding based on status
        if suggestion.status == SuggestionStatus.PENDING.value:
            status_color = "🟡"
            status_label = "Pending"
        elif suggestion.status == SuggestionStatus.APPROVED.value:
            status_color = "🟢"
            status_label = "Approved"
        else:
            status_color = "🔴"
            status_label = "Rejected"

        # Card header
        with st.expander(
            f"{status_color} **{suggestion.hoofdterm}** → **{suggestion.synoniem}** "
            f"(Confidence: {suggestion.confidence:.2f})",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown("**Rationale:**")
                st.info(suggestion.rationale)

                # Context data (if available) - displayed directly to avoid nested expanders
                context = suggestion.get_context_dict()
                if context:
                    st.markdown("**📋 Context Data:**")
                    with st.container():
                        st.json(context)

            with col2:
                st.markdown("**Details:**")
                st.write(f"Status: {status_label}")
                st.write(f"ID: {suggestion.id}")
                st.write(f"Created: {self._format_datetime(suggestion.created_at)}")

                if suggestion.reviewed_by:
                    st.write(f"Reviewed by: {suggestion.reviewed_by}")
                    st.write(
                        f"Reviewed at: {self._format_datetime(suggestion.reviewed_at)}"
                    )

                if suggestion.rejection_reason:
                    st.markdown("**Rejection Reason:**")
                    st.error(suggestion.rejection_reason)

            # Actions (only for pending)
            if suggestion.status == SuggestionStatus.PENDING.value:
                st.markdown("---")
                self._render_suggestion_actions(suggestion)

    def _render_suggestion_actions(self, suggestion: SynonymSuggestionRecord):
        """Render approve/reject acties voor pending suggestion."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✅ Approve",
                key=f"approve_{suggestion.id}",
                type="primary",
                help="Approve suggestion en voeg toe aan synoniemen",
            ):
                self._approve_suggestion(suggestion)

        with col2:
            if st.button(
                "❌ Reject",
                key=f"reject_{suggestion.id}",
                help="Reject suggestion",
            ):
                # Toon rejection reason input
                st.session_state[f"show_reject_reason_{suggestion.id}"] = True
                st.rerun()

        # Rejection reason input (if triggered)
        if st.session_state.get(f"show_reject_reason_{suggestion.id}", False):
            reason = st.text_area(
                "Rejection Reason (verplicht)",
                key=f"reject_reason_{suggestion.id}",
                placeholder="Waarom wordt deze suggestie afgewezen?",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Confirm Reject",
                    key=f"confirm_reject_{suggestion.id}",
                    disabled=not reason.strip(),
                ):
                    self._reject_suggestion(suggestion, reason)
            with col2:
                if st.button("Cancel", key=f"cancel_reject_{suggestion.id}"):
                    st.session_state[f"show_reject_reason_{suggestion.id}"] = False
                    st.rerun()

    def _render_bulk_actions(self, pending_suggestions: list[SynonymSuggestionRecord]):
        """Render bulk acties voor alle visible pending suggestions."""
        st.markdown("#### ⚡ Bulk Acties")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                f"✅ Approve All Visible ({len(pending_suggestions)})",
                key="bulk_approve",
                help="Approve alle zichtbare pending suggestions op deze pagina",
            ):
                # Confirmation dialog
                st.session_state["confirm_bulk_approve"] = True

        with col2:
            if st.button(
                f"❌ Reject All Visible ({len(pending_suggestions)})",
                key="bulk_reject",
                help="Reject alle zichtbare pending suggestions op deze pagina",
            ):
                # Confirmation dialog
                st.session_state["confirm_bulk_reject"] = True

        # Confirmation dialogs
        if st.session_state.get("confirm_bulk_approve", False):
            st.warning(
                f"⚠️ Weet je zeker dat je {len(pending_suggestions)} suggesties wilt approven?"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ja, Approve All", key="confirm_bulk_approve_yes"):
                    self._bulk_approve(pending_suggestions)
            with col2:
                if st.button("Annuleer", key="confirm_bulk_approve_no"):
                    st.session_state["confirm_bulk_approve"] = False
                    st.rerun()

        if st.session_state.get("confirm_bulk_reject", False):
            reason = st.text_area(
                "Bulk Rejection Reason (verplicht)",
                key="bulk_reject_reason",
                placeholder="Waarom worden deze suggesties afgewezen?",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Ja, Reject All",
                    key="confirm_bulk_reject_yes",
                    disabled=not reason.strip(),
                ):
                    self._bulk_reject(pending_suggestions, reason)
            with col2:
                if st.button("Annuleer", key="confirm_bulk_reject_no"):
                    st.session_state["confirm_bulk_reject"] = False
                    st.rerun()

    def _approve_suggestion(self, suggestion: SynonymSuggestionRecord):
        """Approve een suggestion via workflow (updates DB + YAML)."""
        try:
            user = st.session_state.get("user", "reviewer")

            # Use workflow for approve (updates DB + YAML with rollback)
            success = self.workflow.approve_suggestion(suggestion.id, user)

            if success:
                st.success(
                    f"✅ Suggestion approved & toegevoegd aan YAML: '{suggestion.hoofdterm}' → '{suggestion.synoniem}'"
                )
                st.toast(f"✅ Approved: {suggestion.synoniem}", icon="✅")

                # Clear any open dialogs
                if f"show_reject_reason_{suggestion.id}" in st.session_state:
                    del st.session_state[f"show_reject_reason_{suggestion.id}"]

                st.rerun()
            else:
                st.error("❌ Kon suggestion niet approven")

        except Exception as e:
            st.error(f"❌ Fout bij approven: {e}")
            logger.error(f"Approve suggestion error: {e}", exc_info=True)

    def _reject_suggestion(self, suggestion: SynonymSuggestionRecord, reason: str):
        """Reject een suggestion via workflow."""
        try:
            user = st.session_state.get("user", "reviewer")

            # Use workflow for reject
            success = self.workflow.reject_suggestion(
                suggestion.id, user, reason.strip()
            )

            if success:
                st.warning(
                    f"❌ Suggestion rejected: '{suggestion.hoofdterm}' → '{suggestion.synoniem}'"
                )
                st.toast(f"❌ Rejected: {suggestion.synoniem}", icon="❌")

                # Clear rejection dialog
                if f"show_reject_reason_{suggestion.id}" in st.session_state:
                    del st.session_state[f"show_reject_reason_{suggestion.id}"]

                st.rerun()
            else:
                st.error("❌ Kon suggestion niet rejecten")

        except Exception as e:
            st.error(f"❌ Fout bij rejecten: {e}")
            logger.error(f"Reject suggestion error: {e}", exc_info=True)

    def _bulk_approve(self, suggestions: list[SynonymSuggestionRecord]):
        """Bulk approve multiple suggestions via workflow."""
        try:
            user = st.session_state.get("user", "reviewer")
            suggestion_ids = [s.id for s in suggestions]

            with st.spinner(f"Approving {len(suggestions)} suggestions..."):
                # Use workflow batch approve
                result = self.workflow.batch_approve(suggestion_ids, user)

            success_count = result["approved"]
            fail_count = result["failed"]

            if success_count > 0:
                st.success(
                    f"✅ {success_count} suggesties approved & toegevoegd aan YAML"
                )
            if fail_count > 0:
                st.warning(f"⚠️ {fail_count} suggesties konden niet approved worden")
                # Show errors in expander
                if result["errors"]:
                    with st.expander("Bekijk errors"):
                        for error in result["errors"]:
                            st.error(error)

            # Clear confirmation state
            st.session_state["confirm_bulk_approve"] = False
            st.rerun()

        except Exception as e:
            st.error(f"❌ Bulk approve fout: {e}")
            logger.error(f"Bulk approve error: {e}", exc_info=True)

    def _bulk_reject(self, suggestions: list[SynonymSuggestionRecord], reason: str):
        """Bulk reject multiple suggestions via workflow."""
        try:
            user = st.session_state.get("user", "reviewer")
            success_count = 0
            fail_count = 0
            errors = []

            with st.spinner(f"Rejecting {len(suggestions)} suggestions..."):
                for suggestion in suggestions:
                    try:
                        if self.workflow.reject_suggestion(
                            suggestion.id, user, reason.strip()
                        ):
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        logger.error(f"Failed to reject {suggestion.id}: {e}")
                        errors.append(f"ID {suggestion.id}: {e}")
                        fail_count += 1

            if success_count > 0:
                st.warning(f"❌ {success_count} suggesties rejected")
            if fail_count > 0:
                st.warning(f"⚠️ {fail_count} suggesties konden niet rejected worden")
                if errors:
                    with st.expander("Bekijk errors"):
                        for error in errors:
                            st.error(error)

            # Clear confirmation state
            st.session_state["confirm_bulk_reject"] = False
            st.rerun()

        except Exception as e:
            st.error(f"❌ Bulk reject fout: {e}")
            logger.error(f"Bulk reject error: {e}", exc_info=True)

    @staticmethod
    def _format_datetime(dt: datetime | None) -> str:
        """Format datetime voor weergave."""
        if not dt:
            return "—"
        return dt.strftime("%Y-%m-%d %H:%M")


# Factory function voor gebruik in tabbed interface
def render_synonym_review_tab():
    """Render synonym review tab (entry point)."""
    tab = SynonymReviewTab()
    tab.render()
