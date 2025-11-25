"""
Bulk Operations component - Verplaatst van import_export_beheer_tab.py.

Bevat bulk status update functionaliteit, exact zoals het al werkte.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import logging
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRepository

# Status values as string literals (avoids runtime import of DefinitieStatus enum)
_DEFINITIE_STATUSES = ["draft", "review", "established", "archived", "imported"]

logger = logging.getLogger(__name__)


class BulkOperations:
    """Handles bulk operations zoals status updates."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository

    def render(self):
        """Render bulk operations sectie - verplaatst van _render_bulk_actions."""
        st.markdown("### Bulk Status Wijziging")

        col1, col2 = st.columns(2)

        with col1:
            from_status = st.selectbox(
                "Van status",
                _DEFINITIE_STATUSES,
                help="Selecteer huidige status",
            )

        with col2:
            to_status = st.selectbox(
                "Naar status",
                _DEFINITIE_STATUSES,
                help="Selecteer nieuwe status",
            )

        # Preview
        if from_status and to_status and from_status != to_status:
            count = len(self.repository.get_by_status(from_status))
            st.info(
                f"Dit zal {count} definities wijzigen van '{from_status}' naar '{to_status}'"
            )

            if st.button("⚡ Wijzig Status", type="primary"):
                self._execute_bulk_status_change(from_status, to_status)

    def _execute_bulk_status_change(self, from_status: str, to_status: str):
        """Voer bulk status wijziging uit - exact verplaatst van origineel."""
        with st.spinner("Status wijzigen..."):
            try:
                definitions = self.repository.get_by_status(from_status)
                updated = 0

                for definition in definitions:
                    definition.status = to_status
                    self.repository.update(definition)
                    updated += 1

                st.success(
                    f"✅ {updated} definities bijgewerkt naar status '{to_status}'"
                )
                st.rerun()

            except Exception as e:
                st.error(f"Fout bij bulk wijziging: {e!s}")
