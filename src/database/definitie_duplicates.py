"""Duplicate detection voor definities."""

import logging
from dataclasses import dataclass
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import DuplicateMatch, normalize_wettelijke_basis

logger = logging.getLogger(__name__)


# DEF-672: begrensde kandidaatquery voor de CON-01-duplicaatcontrole.
#
# Bewust géén `get_all()`: dat is de volledige tabelscan die DEF-176 juist heeft
# weggehaald. De query filtert op het begrip, sluit gearchiveerde records uit en
# haalt alléén de kolommen op die de duplicaatcontrole nodig heeft — geen
# `SELECT *`, dus niet de definitietekst en niet de overige metadata.
#
# `COLLATE NOCASE` op het begrip vangt de gewone hoofdlettervarianten af. Dat
# kan de BINARY-index `idx_definities_begrip` niet gebruiken; `EXPLAIN QUERY
# PLAN` gaf daarop `SCAN definities`. Vandaar de partiële NOCASE-index
# hieronder, die precies deze query bedient.
#
# De gezaghebbende vergelijking gebeurt daarna in Python op de genormaliseerde
# context (`domain.context.normalisatie`), niet in SQL. Dat is precies waarom de
# oude vergelijking faalde: zij legde ruwe, ordegevoelige JSON-strings naast
# elkaar.
KANDIDATEN_INDEX = "idx_definities_begrip_nocase_actief"
KANDIDATEN_INDEX_DDL = (
    f"CREATE INDEX IF NOT EXISTS {KANDIDATEN_INDEX} "
    "ON definities(begrip COLLATE NOCASE) WHERE status != 'archived'"
)

# Keyset-paginatie op `id`. Er is géén willekeurige resultaatgrens meer: een
# duplicaat op positie 201 viel daar stil buiten en de uitkomst werd "geen
# duplicaat" — een fail-open op precies de as die DEF-624 sluit. De paginering
# loopt door tot de kandidaten voor dit begrip op zijn.
KANDIDATEN_PAGINA = 500

# Absoluut plafond tegen een oneindige lus. Wordt dit geraakt, dan is de
# uitkomst ónbekend, niet negatief: `DuplicaatKandidatenOverschredenError` loopt door
# naar de ERROR-grens in de validatieservice en blokkeert de acceptatie. Nooit
# stil afkappen.
KANDIDATEN_PLAFOND = 50_000

KANDIDATEN_QUERY = """
    SELECT id, status, categorie,
           organisatorische_context, juridische_context, wettelijke_basis
    FROM definities
    WHERE begrip = ? COLLATE NOCASE
      AND status != 'archived'
      AND id > ?
    ORDER BY id
    LIMIT ?
"""


class DuplicaatKandidatenOverschredenError(RuntimeError):
    """Het kandidatenplafond is geraakt; de duplicaatcontrole is onvolledig."""


@dataclass(frozen=True)
class DuplicaatKandidaatRij:
    """Eén ruwe kandidaatrij: identiteit plus de drie opgeslagen contextvelden.

    Bewust géén `DefinitieRecord`: dat vraagt alle kolommen, inclusief de
    definitietekst die de duplicaatcontrole niet nodig heeft. De normalisatie
    van de contextwaarden gebeurt een laag hoger, bij de repository die de
    vergelijkingssleutels opbouwt.
    """

    id: int | None
    status: str | None
    categorie: str | None
    organisatorische_context: str | None
    juridische_context: str | None
    wettelijke_basis: str | None


class DefinitieDuplicateRepository:
    """Duplicate detection repository."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def find_active_by_begrip(self, begrip: str) -> list[DuplicaatKandidaatRij]:
        """Álle actieve kandidaten met dit begrip (DEF-672).

        Pagineert op `id` tot de kandidaten op zijn, zodat er geen duplicaat
        buiten een willekeurige grens kan vallen. Het plafond is een vangnet
        tegen een oneindige lus en eindigt fail-closed met een uitzondering,
        nooit met een ingekorte lijst die als "geen duplicaat" leest.

        Een leeg of alleen-whitespace begrip levert niets op — dan is er geen
        identiteit om op te matchen.
        """
        genormaliseerd = str(begrip or "").strip()
        if not genormaliseerd:
            return []

        kandidaten: list[DuplicaatKandidaatRij] = []
        laatste_id = 0
        with self._db.get_connection() as conn:
            while True:
                rijen = conn.execute(
                    KANDIDATEN_QUERY,
                    (genormaliseerd, laatste_id, KANDIDATEN_PAGINA),
                ).fetchall()
                if not rijen:
                    break
                for rij in rijen:
                    kandidaten.append(
                        DuplicaatKandidaatRij(
                            id=rij[0],
                            status=rij[1],
                            categorie=rij[2],
                            organisatorische_context=rij[3],
                            juridische_context=rij[4],
                            wettelijke_basis=rij[5],
                        )
                    )
                laatste_id = int(rijen[-1][0])
                if len(kandidaten) > KANDIDATEN_PLAFOND:
                    msg = (
                        f"meer dan {KANDIDATEN_PLAFOND} actieve kandidaten voor "
                        f"begrip {genormaliseerd!r}; de duplicaatcontrole is "
                        f"onvolledig en mag niet als 'geen duplicaat' eindigen"
                    )
                    raise DuplicaatKandidatenOverschredenError(msg)
                if len(rijen) < KANDIDATEN_PAGINA:
                    break
        return kandidaten

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

        # DEF-482: kale connectie — een committend ``with conn:`` zou de
        # transactie van create_definitie halverwege sluiten.
        conn = self._db.get_connection()
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
            exact_query += (
                " AND (wettelijke_basis = ? OR (wettelijke_basis IS NULL AND ? = '[]'))"
            )
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
