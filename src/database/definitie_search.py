"""Zoekfunctionaliteit voor definities."""

import logging
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import DefinitieRecord, DefinitieStatus
from domain.ontological_categories import OntologischeCategorie

logger = logging.getLogger(__name__)


class DefinitieSearchRepository:
    """Search repository voor definities."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def search_definities(
        self,
        query: str | None = None,
        categorie: OntologischeCategorie | None = None,
        organisatorische_context: str | None = None,
        status: DefinitieStatus | None = None,
        limit: int | None = 100,
    ) -> list[DefinitieRecord]:
        """Zoek definities met verschillende filters."""
        with self._db.get_connection() as conn:
            where_clauses: list[str] = []
            params: list[Any] = []

            if query:
                where_clauses.append("(begrip LIKE ? OR definitie LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term])

            if categorie:
                where_clauses.append("categorie = ?")
                params.append(categorie.value)

            if organisatorische_context:
                where_clauses.append("organisatorische_context = ?")
                params.append(organisatorische_context)

            if status:
                where_clauses.append("status = ?")
                params.append(status.value)

            base_query = "SELECT * FROM definities"
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)

            base_query += " ORDER BY begrip, created_at DESC"

            if limit:
                if isinstance(limit, int) and limit > 0:
                    base_query += " LIMIT ?"
                    params.append(limit)
                else:
                    logger.warning(f"Invalid limit value ignored: {limit}")

            cursor = conn.execute(base_query, params)
            return [self._audit.row_to_record(row) for row in cursor.fetchall()]
