"""Duplicate detection voor definities.

DEF-622 (B-03): de lookup vóór generatie (`find_duplicates`, en via de CRUD
`find_definitie`) vergelijkt niet langer ruwe JSON-strings, maar de
genormaliseerde *volledige* contextverzameling — dezelfde `contextsleutel`
die DUP_01 en de opslag gebruiken. Overlap op één waarde is geen gelijke
context; een verschil in schrijfwijze, volgorde, whitespace of herhaling is
dat evenmin. De kandidaten blijven begrensd op begrip (plus actieve
synoniemen), nooit een tabelscan.
"""

import logging
from dataclasses import dataclass
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import DefinitieStatus, DuplicateMatch, normalize_wettelijke_basis
from domain.context.normalisatie import contextsleutel, lees_contextwaarden

logger = logging.getLogger(__name__)

# Voorrang bij meerdere records met gelijk begrip en gelijke context (B-03/B-10):
# het vastgestelde record is leidend, daarna wat in beoordeling is, dan een
# concept. Gearchiveerd is historie en komt alleen mee bij een expliciete
# statusvraag.
_STATUSVOORRANG: dict[str, int] = {
    DefinitieStatus.ESTABLISHED.value: 0,
    DefinitieStatus.REVIEW.value: 1,
    DefinitieStatus.DRAFT.value: 2,
    DefinitieStatus.IMPORTED.value: 3,
    DefinitieStatus.ARCHIVED.value: 4,
}


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

_KANDIDAAT_KOLOMMEN = (
    "id, status, categorie, organisatorische_context, juridische_context, "
    "wettelijke_basis, begrip, version_number"
)

KANDIDATEN_QUERY = f"""
    SELECT {_KANDIDAAT_KOLOMMEN}
    FROM definities
    WHERE begrip = ? COLLATE NOCASE
      AND status != 'archived'
      AND id > ?
    ORDER BY id
    LIMIT ?
"""

# Zonder statusfilter: alleen voor een expliciete statusvraag (bv. gearchiveerd
# terugvinden). Kan de partiële NOCASE-index niet gebruiken; dat is hier
# aanvaardbaar omdat dit pad niet in de generatieflow zit.
KANDIDATEN_QUERY_ALLE = f"""
    SELECT {_KANDIDAAT_KOLOMMEN}
    FROM definities
    WHERE begrip = ? COLLATE NOCASE
      AND id > ?
    ORDER BY id
    LIMIT ?
"""

# Kandidaten via een actief synoniem (DEF-622 behoudt het synoniempad van de
# oude `find_definitie`/`find_duplicates`). Begrensd op het synoniem, en
# gepagineerd op id net als de begripsquery.
KANDIDATEN_SYNONIEM_QUERY = f"""
    SELECT DISTINCT {', '.join('d.' + k.strip() for k in _KANDIDAAT_KOLOMMEN.split(','))}
    FROM definities d
    JOIN definitie_voorbeelden v ON v.definitie_id = d.id
    WHERE LOWER(v.voorbeeld_tekst) = LOWER(?)
      AND v.voorbeeld_type = 'synonyms'
      AND v.actief = TRUE
      AND d.status != 'archived'
      AND d.id > ?
    ORDER BY d.id
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
    begrip: str | None = None
    version_number: int | None = None
    via_synoniem: bool = False

    @property
    def contextsleutels(self) -> tuple[tuple[str, ...], ...]:
        """De genormaliseerde vergelijkingssleutel van de drie lijsten."""
        return (
            contextsleutel(lees_contextwaarden(self.organisatorische_context)),
            contextsleutel(lees_contextwaarden(self.juridische_context)),
            contextsleutel(lees_contextwaarden(self.wettelijke_basis)),
        )


def _rij(ruw: Any, *, via_synoniem: bool = False) -> DuplicaatKandidaatRij:
    return DuplicaatKandidaatRij(
        id=ruw[0],
        status=ruw[1],
        categorie=ruw[2],
        organisatorische_context=ruw[3],
        juridische_context=ruw[4],
        wettelijke_basis=ruw[5],
        begrip=ruw[6],
        version_number=ruw[7],
        via_synoniem=via_synoniem,
    )


def _voorrang(rij: DuplicaatKandidaatRij) -> tuple[int, int, int]:
    """Sorteersleutel: leidende status eerst, dan hoogste versie, dan laagste id."""
    return (
        _STATUSVOORRANG.get(str(rij.status or ""), len(_STATUSVOORRANG)),
        -int(rij.version_number or 0),
        int(rij.id or 0),
    )


class DefinitieDuplicateRepository:
    """Duplicate detection repository."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def _pagineer(
        self, query: str, sleutel: str, *, via_synoniem: bool = False
    ) -> list[DuplicaatKandidaatRij]:
        """Keyset-paginatie op id tot de kandidaten op zijn.

        Pagineert tot de kandidaten op zijn, zodat er geen duplicaat buiten
        een willekeurige grens kan vallen. Het plafond is een vangnet tegen
        een oneindige lus en eindigt fail-closed met een uitzondering, nooit
        met een ingekorte lijst die als "geen duplicaat" leest.

        Kale connectie, géén committend ``with conn:`` (DEF-482): deze lezer
        draait ook binnen de schrijftransactie van `create_definitie`, en een
        commit halverwege zou die transactie sluiten.
        """
        kandidaten: list[DuplicaatKandidaatRij] = []
        laatste_id = 0
        conn = self._db.get_connection()
        while True:
            rijen = conn.execute(
                query, (sleutel, laatste_id, KANDIDATEN_PAGINA)
            ).fetchall()
            if not rijen:
                break
            kandidaten.extend(_rij(rij, via_synoniem=via_synoniem) for rij in rijen)
            laatste_id = int(rijen[-1][0])
            if len(kandidaten) > KANDIDATEN_PLAFOND:
                msg = (
                    f"meer dan {KANDIDATEN_PLAFOND} actieve kandidaten voor "
                    f"{sleutel!r}; de duplicaatcontrole is onvolledig en mag "
                    f"niet als 'geen duplicaat' eindigen"
                )
                raise DuplicaatKandidatenOverschredenError(msg)
            if len(rijen) < KANDIDATEN_PAGINA:
                break
        return kandidaten

    def find_active_by_begrip(self, begrip: str) -> list[DuplicaatKandidaatRij]:
        """Álle actieve kandidaten met dit begrip (DEF-672).

        Een leeg of alleen-whitespace begrip levert niets op — dan is er geen
        identiteit om op te matchen.
        """
        genormaliseerd = str(begrip or "").strip()
        if not genormaliseerd:
            return []
        return self._pagineer(KANDIDATEN_QUERY, genormaliseerd)

    def find_active_by_synoniem(self, begrip: str) -> list[DuplicaatKandidaatRij]:
        """Actieve kandidaten waarvan een actief synoniem gelijk is aan `begrip`."""
        genormaliseerd = str(begrip or "").strip()
        if not genormaliseerd:
            return []
        return self._pagineer(
            KANDIDATEN_SYNONIEM_QUERY, genormaliseerd, via_synoniem=True
        )

    def zoek_gelijke_context(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any = "",
        wettelijke_basis: Any = None,
        *,
        categorie: str | None = None,
        status: DefinitieStatus | None = None,
    ) -> list[DuplicaatKandidaatRij]:
        """Kandidaten met gelijk begrip (of synoniem) én gelijke volledige context.

        Vergelijkt de drie genormaliseerde lijsten integraal (B-03): een
        gedeelde waarde of een ontbrekende lijst is géén gelijke context. Een
        opgegeven categorie moet mee-matchen (bestaand lookup-onderscheid);
        `None` laat de categorie buiten beschouwing. `wettelijke_basis=None`
        betekent 'geen wettelijke basis', niet 'negeer'. Gesorteerd op
        voorrang: vastgesteld, in beoordeling, concept; daarbinnen hoogste
        versie eerst.
        """
        gezocht = (
            contextsleutel(lees_contextwaarden(organisatorische_context)),
            contextsleutel(lees_contextwaarden(juridische_context)),
            contextsleutel(lees_contextwaarden(wettelijke_basis)),
        )
        genormaliseerd = str(begrip or "").strip()
        if not genormaliseerd:
            return []

        if status is DefinitieStatus.ARCHIVED:
            kandidaten = self._pagineer(KANDIDATEN_QUERY_ALLE, genormaliseerd)
        else:
            kandidaten = self.find_active_by_begrip(genormaliseerd)
        gezien = {rij.id for rij in kandidaten}
        kandidaten.extend(
            rij
            for rij in self.find_active_by_synoniem(genormaliseerd)
            if rij.id not in gezien
        )

        gelijk = [
            rij
            for rij in kandidaten
            if rij.contextsleutels == gezocht
            and (
                categorie is None
                or str(rij.categorie or "").casefold() == str(categorie).casefold()
            )
            and (status is None or rij.status == status.value)
        ]
        return sorted(gelijk, key=_voorrang)

    def _volledig_record(self, definitie_id: int) -> Any:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT * FROM definities WHERE id = ?", (definitie_id,)
        ).fetchone()
        return self._audit.row_to_record(row) if row else None

    def find_duplicates(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> list[DuplicateMatch]:
        """Zoek bestaande definities met gelijk begrip (of synoniem) en gelijke context.

        DEF-622: vergelijkt op de genormaliseerde volledige context, via
        `zoek_gelijke_context`. Een `wettelijke_basis` van `None` telt als
        'geen wettelijke basis' — een record mét wettelijke basis is dan geen
        duplicaat, want de contextverzameling verschilt (B-03).

        DEF-482: kale connectie — een committend ``with conn:`` zou de
        transactie van create_definitie halverwege sluiten.
        """
        matches: list[DuplicateMatch] = []
        for rij in self.zoek_gelijke_context(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            categorie=categorie,
        ):
            if rij.id is None:
                continue
            record = self._volledig_record(int(rij.id))
            if record is None:
                continue
            matches.append(
                DuplicateMatch(
                    definitie_record=record,
                    match_score=1.0,
                    match_reasons=[
                        (
                            "Exact match: synoniem + context"
                            if rij.via_synoniem
                            else "Exact match: begrip + context"
                        )
                    ],
                )
            )
        return matches

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
