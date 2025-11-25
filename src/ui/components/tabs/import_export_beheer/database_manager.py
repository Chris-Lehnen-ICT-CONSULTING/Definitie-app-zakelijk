"""
Database Manager component - Verplaatst van import_export_beheer_tab.py.

Bevat database beheer functionaliteit, exact zoals het al werkte.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRepository

# Status values as string literals (avoids runtime import of DefinitieStatus enum)
_STATUS_ESTABLISHED = "established"
_STATUS_DRAFT = "draft"

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database management en statistieken."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository

    def render(self):
        """Render database management sectie - verplaatst van _render_database_management."""
        st.markdown("### Database Beheer")

        # Database statistieken
        with st.expander("📊 Database Statistieken", expanded=True):
            stats = self._get_database_stats()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Totaal Definities", stats["total"])
            with col2:
                st.metric("Vastgesteld", stats["established"])
            with col3:
                st.metric("Draft", stats["draft"])
            with col4:
                st.metric("Database Size", stats["size"])

        # Reset functionaliteit
        st.markdown("### ⚠️ Database Reset")
        st.warning(
            "**LET OP**: Deze actie verwijdert ALLE data en kan niet ongedaan worden gemaakt!"
        )

        col1, col2 = st.columns(2)
        with col1:
            confirm_text = st.text_input(
                "Type 'RESET' om te bevestigen",
                help="Beveiliging tegen onbedoeld resetten",
            )

        with col2:
            if st.button(
                "🗑️ Reset Database", type="secondary", disabled=(confirm_text != "RESET")
            ):
                self._execute_database_reset()

    def _get_database_stats(self) -> dict[str, Any]:
        """Haal database statistieken op - exact verplaatst van origineel."""
        try:
            total = len(self.repository.get_all())
            established = len(self.repository.get_by_status(_STATUS_ESTABLISHED))
            draft = len(self.repository.get_by_status(_STATUS_DRAFT))

            # Database size
            db_path = Path("data/definities.db")
            if db_path.exists():
                size_bytes = db_path.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "N/A"

            return {
                "total": total,
                "established": established,
                "draft": draft,
                "size": size_str,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total": 0, "established": 0, "draft": 0, "size": "Error"}

    def _execute_database_reset(self):
        """Reset de database - exact verplaatst van origineel."""
        with st.spinner("Database resetten..."):
            try:
                # Implementatie afhankelijk van je database setup
                # Voor nu alleen een melding
                st.error("Database reset is uitgeschakeld in deze versie")
                # Database reset functionaliteit wordt in een aparte story geïmplementeerd
                # self.repository.reset_database()
                # st.success("✅ Database gereset")
                # st.rerun()

            except Exception as e:
                st.error(f"Fout bij database reset: {e!s}")
