"""Duplicate detection voor definities."""

import json
import logging
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import DuplicateMatch

logger = logging.getLogger(__name__)


class DefinitieDuplicateRepository:
    """Duplicate detection repository."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def find_duplicates(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> list[DuplicateMatch]:
        """Zoek mogelijke duplicaten voor een begrip."""
        matches = []

        with self._db.get_connection() as conn:
            exact_query = """
                SELECT * FROM definities
                WHERE begrip = ?
                AND organisatorische_context = ?
                AND COALESCE(juridische_context, '') = COALESCE(?, '')
                AND status != 'archived'
            """
            exact_params: list[Any] = [
                begrip,
                organisatorische_context,
                juridische_context or "",
            ]

            if categorie is not None:
                exact_query += " AND categorie = ?"
                exact_params.append(categorie)

            if wettelijke_basis is not None:
                try:
                    norm = sorted({str(x).strip() for x in (wettelijke_basis or [])})
                    wb_json = json.dumps(norm, ensure_ascii=False)
                except Exception as e:
                    logger.debug(
                        f"Wettelijke basis normalisatie gefaald in find_duplicates: {e}"
                    )
                    wb_json = json.dumps(wettelijke_basis or [], ensure_ascii=False)
                exact_query += " AND (wettelijke_basis = ? OR (wettelijke_basis IS NULL AND ? = '[]'))"
                exact_params.extend([wb_json, wb_json])

            cursor = conn.execute(exact_query, exact_params)

            for row in cursor.fetchall():
                record = self._audit.row_to_record(row)
                matches.append(
                    DuplicateMatch(
                        definitie_record=record,
                        match_score=1.0,
                        match_reasons=["Exact match: begrip + context"],
                    )
                )

            # Exact synoniem-match
            syn_query = """
                SELECT d.*
                FROM definities d
                JOIN definitie_voorbeelden v ON v.definitie_id = d.id
                WHERE LOWER(v.voorbeeld_tekst) = LOWER(?)
                  AND v.voorbeeld_type = 'synonyms'
                  AND v.actief = TRUE
                  AND d.organisatorische_context = ?
                  AND COALESCE(d.juridische_context, '') = COALESCE(?, '')
                  AND d.status != 'archived'
            """
            syn_params: list[Any] = [
                begrip,
                organisatorische_context,
                juridische_context or "",
            ]

            if categorie is not None:
                syn_query += " AND d.categorie = ?"
                syn_params.append(categorie)

            if wettelijke_basis is not None:
                try:
                    norm = sorted({str(x).strip() for x in (wettelijke_basis or [])})
                    wb_json = json.dumps(norm, ensure_ascii=False)
                except Exception as e:
                    logger.debug(
                        f"Wettelijke basis normalisatie gefaald in duplicates synonym: {e}"
                    )
                    wb_json = json.dumps(wettelijke_basis or [], ensure_ascii=False)
                syn_query += " AND (d.wettelijke_basis = ? OR (d.wettelijke_basis IS NULL AND ? = '[]'))"
                syn_params.extend([wb_json, wb_json])

            cursor = conn.execute(syn_query, syn_params)
            for row in cursor.fetchall():
                record = self._audit.row_to_record(row)
                matches.append(
                    DuplicateMatch(
                        definitie_record=record,
                        match_score=1.0,
                        match_reasons=["Exact match: synoniem + context"],
                    )
                )

        return sorted(matches, key=lambda x: x.match_score, reverse=True)

    def count_exact_by_context(
        self,
        *,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        wettelijke_basis: list[str] | None = None,
    ) -> int:
        """Tel definities met exact zelfde begrip + context, status != archived."""
        with self._db.get_connection() as conn:
            query = (
                "SELECT COUNT(*) AS cnt FROM definities "
                "WHERE begrip = ? AND organisatorische_context = ? "
                "AND (juridische_context = ? OR (juridische_context IS NULL AND ? = '')) "
                "AND status != 'archived'"
            )
            params: list[Any] = [
                begrip,
                organisatorische_context,
                juridische_context,
                juridische_context,
            ]
            if wettelijke_basis is not None:
                try:
                    norm = sorted({str(x).strip() for x in (wettelijke_basis or [])})
                    wb_json = json.dumps(norm, ensure_ascii=False)
                except Exception as e:
                    logger.debug(
                        f"Wettelijke basis normalisatie gefaald in count_exact: {e}"
                    )
                    wb_json = json.dumps(wettelijke_basis or [], ensure_ascii=False)
                query += " AND (wettelijke_basis = ? OR (wettelijke_basis IS NULL AND ? = '[]'))"
                params.extend([wb_json, wb_json])
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return int(row[0]) if row else 0
