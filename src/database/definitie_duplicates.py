"""Duplicate detection voor definities."""

import logging
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import (
    DefinitieRecord,
    DuplicateMatch,
    normalize_wettelijke_basis,
)

logger = logging.getLogger(__name__)


# DEF-672: begrensde kandidaatquery voor de CON-01-duplicaatcontrole.
#
# Bewust géén `get_all()`: dat is de volledige tabelscan die DEF-176 juist heeft
# weggehaald. Deze query filtert op het begrip (index `idx_definities_begrip`),
# sluit gearchiveerde records uit en draagt een harde bovengrens, zodat het
# resultaat nooit met de tabel meegroeit.
#
# `COLLATE NOCASE` op het begrip vangt de gewone hoofdlettervarianten af; de
# gezaghebbende vergelijking gebeurt daarna in Python op de genormaliseerde
# context (`domain.context.normalisatie`), niet in SQL. Dat is precies waarom de
# oude vergelijking faalde: zij legde ruwe, ordegevoelige JSON-strings naast
# elkaar.
KANDIDATEN_LIMIET = 200
KANDIDATEN_QUERY = """
    SELECT * FROM definities
    WHERE begrip = ? COLLATE NOCASE
      AND status != 'archived'
    ORDER BY id
    LIMIT ?
"""


class DefinitieDuplicateRepository:
    """Duplicate detection repository."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def find_active_by_begrip(
        self, begrip: str, limiet: int = KANDIDATEN_LIMIET
    ) -> list[DefinitieRecord]:
        """Actieve records met dit begrip, begrensd (DEF-672).

        Levert de ruwe records; de aanroeper normaliseert de context. Een leeg
        of alleen-whitespace begrip levert niets op — dan is er geen identiteit
        om op te matchen en zou de query zinloos de hele tabel raken.
        """
        genormaliseerd = str(begrip or "").strip()
        if not genormaliseerd:
            return []
        with self._db.get_connection() as conn:
            cursor = conn.execute(KANDIDATEN_QUERY, (genormaliseerd, limiet))
            return [self._audit.row_to_record(rij) for rij in cursor.fetchall()]

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
                wb_json = normalize_wettelijke_basis(wettelijke_basis)
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
                wb_json = normalize_wettelijke_basis(wettelijke_basis)
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
                wb_json = normalize_wettelijke_basis(wettelijke_basis)
                query += " AND (wettelijke_basis = ? OR (wettelijke_basis IS NULL AND ? = '[]'))"
                params.extend([wb_json, wb_json])
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return int(row[0]) if row else 0
