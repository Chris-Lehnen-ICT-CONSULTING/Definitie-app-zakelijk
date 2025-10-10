"""
Synonym Review Component - UI for reviewing AI-pending synonyms.

Architecture v3.1 PHASE 3.2: Pending Review UI

This component provides a clean interface for reviewing AI-generated synonyms
that are pending approval. Displays metadata, rationale, and approve/reject actions.
"""

import json
import logging
from typing import Any

import streamlit as st

from src.repositories.synonym_registry import SynonymRegistry
from src.services.container import get_container
from src.utils.dict_helpers import safe_dict_get

logger = logging.getLogger(__name__)


class SynonymReviewComponent:
    """Component for reviewing AI-pending synonyms after definition generation."""

    def __init__(self):
        """Initialize synonym review component."""
        self.container = get_container()

    def render_synonym_metadata(self, generation_result: dict[str, Any]) -> None:
        """
        Render synonym enrichment metadata after definition generation.

        Shows:
        - Number of synonyms used
        - Number of AI-pending synonyms requiring review
        - Review button if pending synonyms exist

        Args:
            generation_result: Generation result dict from orchestrator
        """
        # Extract metadata from orchestrator response
        agent_result = safe_dict_get(generation_result, "agent_result", {})
        if not isinstance(agent_result, dict):
            return

        metadata = safe_dict_get(agent_result, "metadata", {})
        if not metadata:
            return

        # Get synonym enrichment data
        enriched_count = int(safe_dict_get(metadata, "enriched_synonyms_count", 0))
        ai_pending_count = int(safe_dict_get(metadata, "ai_pending_synonyms_count", 0))
        enrichment_status = safe_dict_get(
            metadata, "synonym_enrichment_status", "not_available"
        )

        # Only show if enrichment was attempted
        if enrichment_status == "not_available":
            return

        # Create metadata block
        st.markdown("#### 📚 Synoniemen Metadata")

        with st.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                if enrichment_status == "success":
                    st.success(
                        f"✅ **{enriched_count} synoniemen** gevonden en gebruikt"
                    )
                elif enrichment_status == "no_synonyms":
                    st.warning("⚠️ Geen synoniemen gevonden")
                elif enrichment_status == "error":
                    st.error("❌ Synoniemen enrichment gefaald")

                if ai_pending_count > 0:
                    st.warning(
                        f"⚠️ **{ai_pending_count} nieuwe AI-synoniemen** wachten op review"
                    )

            with col2:
                if ai_pending_count > 0:
                    if st.button("🔍 Review Synoniemen", key="review_synonyms_btn"):
                        self._open_review_dialog(generation_result)

                    if st.button("Later", key="review_later_btn"):
                        st.info("Review kan later via de Synoniemen tab")

    def _open_review_dialog(self, generation_result: dict[str, Any]) -> None:
        """
        Open review dialog for AI-pending synonyms.

        Args:
            generation_result: Generation result with synonym metadata
        """
        # Get the generated term
        term = safe_dict_get(generation_result, "begrip", "")
        if not term:
            st.error("Kan term niet bepalen voor synonym review")
            return

        # Get registry and fetch pending synonyms
        try:
            registry = self.container.synonym_registry()
            group = registry.find_group_by_term(term)

            if not group:
                st.warning(f"Geen synonym groep gevonden voor '{term}'")
                return

            # Get AI-pending members
            pending_members = registry.get_group_members(
                group_id=group.id, statuses=["ai_pending"], order_by=["weight DESC"]
            )

            if not pending_members:
                st.info("Geen AI-pending synoniemen gevonden")
                return

            # Render review interface
            self._render_review_interface(term, pending_members, registry)

        except Exception as e:
            logger.error(f"Failed to load pending synonyms: {e}", exc_info=True)
            st.error(f"Kon AI-pending synoniemen niet laden: {e}")

    def _render_review_interface(
        self, term: str, pending_members: list, registry: SynonymRegistry
    ) -> None:
        """
        Render the review interface for pending synonyms.

        Args:
            term: The term being reviewed
            pending_members: List of AI-pending synonym members
            registry: Synonym registry instance
        """
        st.markdown("---")
        st.markdown(f"### 🤖 AI-Gegenereerde Synoniemen Review voor '{term}'")
        st.caption(
            f"Review {len(pending_members)} AI-voorgestelde synoniemen. "
            "Goedgekeurde synoniemen worden gebruikt in toekomstige zoekacties."
        )

        # Bulk actions
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("✅ Alles Goedkeuren", key="approve_all"):
                self._approve_all_pending(pending_members, registry)
                st.success(f"Alle {len(pending_members)} synoniemen goedgekeurd!")
                st.rerun()

        with col3:
            if st.button("❌ Alles Afwijzen", key="reject_all"):
                self._reject_all_pending(pending_members, registry)
                st.warning(f"Alle {len(pending_members)} synoniemen afgewezen")
                st.rerun()

        st.markdown("---")

        # Individual synonym review cards
        for idx, member in enumerate(pending_members):
            self._render_synonym_card(member, registry, idx)

    def _render_synonym_card(
        self, member: Any, registry: SynonymRegistry, idx: int
    ) -> None:
        """
        Render individual synonym review card.

        Args:
            member: SynonymGroupMember instance
            registry: Synonym registry instance
            idx: Index for unique key generation
        """
        with st.container():
            # Header with term and weight
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                confidence_pct = member.weight * 100
                st.markdown(f"**{member.term}** (confidence: {confidence_pct:.0f}%)")

            with col2:
                if st.button("✓ Goedkeuren", key=f"approve_{idx}"):
                    self._approve_synonym(member, registry)
                    st.success(f"'{member.term}' goedgekeurd!")
                    st.rerun()

            with col3:
                if st.button("✗ Afwijzen", key=f"reject_{idx}"):
                    self._reject_synonym(member, registry)
                    st.warning(f"'{member.term}' afgewezen")
                    st.rerun()

            # Show rationale if available
            if member.context_json:
                try:
                    context = json.loads(member.context_json)
                    rationale = context.get("rationale", "")
                    if rationale:
                        st.caption(f"💡 Rationale: {rationale}")
                except Exception:
                    pass

            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Bron: {member.source}")
            with col2:
                if member.created_at:
                    st.caption(
                        f"Gemaakt: {member.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )

            st.markdown("---")

    def _approve_synonym(self, member: Any, registry: SynonymRegistry) -> None:
        """
        Approve a single synonym (change status from ai_pending to active).

        Args:
            member: SynonymGroupMember to approve
            registry: Synonym registry instance
        """
        try:
            registry.update_member_status(
                member_id=member.id,
                new_status="active",
                reviewed_by="user",
            )
            logger.info(f"Synonym '{member.term}' approved (member_id={member.id})")
        except Exception as e:
            logger.error(f"Failed to approve synonym: {e}", exc_info=True)
            st.error(f"Kon synoniem niet goedkeuren: {e}")

    def _reject_synonym(self, member: Any, registry: SynonymRegistry) -> None:
        """
        Reject a single synonym (change status from ai_pending to rejected_auto).

        Args:
            member: SynonymGroupMember to reject
            registry: Synonym registry instance
        """
        try:
            registry.update_member_status(
                member_id=member.id,
                new_status="rejected_auto",
                reviewed_by="user",
            )
            logger.info(f"Synonym '{member.term}' rejected (member_id={member.id})")
        except Exception as e:
            logger.error(f"Failed to reject synonym: {e}", exc_info=True)
            st.error(f"Kon synoniem niet afwijzen: {e}")

    def _approve_all_pending(self, members: list, registry: SynonymRegistry) -> None:
        """
        Approve all pending synonyms in bulk.

        Args:
            members: List of SynonymGroupMember instances to approve
            registry: Synonym registry instance
        """
        for member in members:
            try:
                registry.update_member_status(
                    member_id=member.id, new_status="active", reviewed_by="user"
                )
            except Exception as e:
                logger.error(f"Failed to approve synonym {member.term}: {e}")

    def _reject_all_pending(self, members: list, registry: SynonymRegistry) -> None:
        """
        Reject all pending synonyms in bulk.

        Args:
            members: List of SynonymGroupMember instances to reject
            registry: Synonym registry instance
        """
        for member in members:
            try:
                registry.update_member_status(
                    member_id=member.id, new_status="rejected_auto", reviewed_by="user"
                )
            except Exception as e:
                logger.error(f"Failed to reject synonym {member.term}: {e}")
