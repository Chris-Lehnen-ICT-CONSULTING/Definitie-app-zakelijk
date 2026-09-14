"""Core CRUD operaties voor definities."""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Final

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_duplicates import DefinitieDuplicateRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import DefinitieRecord, DefinitieStatus

logger = logging.getLogger(__name__)


class Unset:
    """Type van de ``UNSET``-sentinel: parameter niet meegegeven (anders dan ``None``)."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final[Unset] = Unset()


class DefinitieCrudRepository:
    """Core CRUD repository voor definities."""

    def __init__(
        self,
        db: DatabaseConnection,
        audit: AuditHelpers,
        duplicates: DefinitieDuplicateRepository,
        search: DefinitieSearchRepository,
    ):
        self._db = db
        self._audit = audit
        self._duplicates = duplicates
        self._search = search

    def create_definitie(
        self,
        record: DefinitieRecord,
        allow_duplicate: bool = False,
        duplicate_reason: str | None = None,
    ) -> int:
        """Maak nieuwe definitie aan.

        DEF-622 (besluit 5): naast een bestaande definitie met gelijk begrip en
        gelijke context mag alleen bewust worden aangemaakt, mét reden. Die
        reden komt in de audit van het nieuwe record; het bestaande record
        wordt niet aangeraakt. `allow_duplicate=True` zonder reden wordt
        geweigerd zodra er werkelijk een duplicaat is — zonder duplicaat is
        er niets te verantwoorden.
        """
        # DEF-198: Clean architecture - import from utils/, callback registered by UI
        from utils.progress_callback import operation_progress

        with operation_progress("saving_to_database"):
            now = datetime.now(UTC)
            record.created_at = now
            record.updated_at = now

            wb_value = (
                record.wettelijke_basis if record.wettelijke_basis is not None else "[]"
            )
            reden = (duplicate_reason or "").strip()

            # DEF-391: INSERT + audit-log atomair (all-or-nothing).
            # DEF-482/DEF-483: de duplicaatcontrole draait binnen dezelfde
            # BEGIN IMMEDIATE, zodat gelijktijdige creates geserialiseerd worden
            # en de tweede de gecommitte rij van de eerste ziet.
            with self._db.transaction() as conn:
                bestaand = self._actief_duplicaat(record)
                if bestaand is not None and not allow_duplicate:
                    msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
                    raise ValueError(msg)
                if bestaand is not None and not reden:
                    msg = (
                        f"Definitie voor '{record.begrip}' bestaat al in deze "
                        "context; bewust een nieuw concept ernaast aanmaken "
                        "vereist een reden voor de audit"
                    )
                    raise ValueError(msg)
                include_legacy = AuditHelpers.has_legacy_columns_in_conn(conn)
                columns, values = AuditHelpers.build_insert_columns(
                    record, wb_value, include_legacy
                )
                column_sql = ", ".join(columns)
                placeholders = ", ".join("?" for _ in columns)

                cursor = conn.execute(
                    f"INSERT INTO definities ({column_sql}) VALUES ({placeholders})",
                    tuple(values),
                )

                record_id = cursor.lastrowid

                if record_id is None:
                    raise RuntimeError("Failed to get lastrowid after INSERT")

                audit = f"Nieuwe definitie aangemaakt voor '{record.begrip}'"
                if bestaand is not None:
                    audit += (
                        f" — bewust naast bestaande definitie {bestaand} "
                        f"(zelfde begrip en context); reden: {reden}"
                    )
                self._audit.log_geschiedenis(
                    record_id, "created", record.created_by, audit
                )

            logger.info(f"Created definitie {record_id}")
            return record_id

    def _actief_duplicaat(self, record: DefinitieRecord) -> int | None:
        """Het id van een actieve definitie met gelijk begrip en gelijke context.

        DEF-622: via `find_duplicates`, dat op de genormaliseerde volledige
        context vergelijkt. Bewust die naad en niet rechtstreeks de
        kandidaatselectie: de racetest (DEF-482/DEF-727) hangt zijn handshake
        aan `find_duplicates` binnen de schrijftransactie. Een gearchiveerd
        record is historie en telt niet als duplicaat.
        """
        duplicates = self._duplicates.find_duplicates(
            record.begrip,
            record.organisatorische_context,
            record.juridische_context or "",
            categorie=record.categorie,
            wettelijke_basis=(
                json.loads(record.wettelijke_basis) if record.wettelijke_basis else []
            ),
        )
        for match in duplicates:
            bestaand = match.definitie_record
            if bestaand.status != DefinitieStatus.ARCHIVED.value and bestaand.id:
                return int(bestaand.id)
        return None

    def _weiger_duplicaat(self, record: DefinitieRecord) -> None:
        """Gooi ``ValueError`` als er al een actieve definitie in deze context is."""
        if self._actief_duplicaat(record) is not None:
            msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
            raise ValueError(msg)

    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        """Haal definitie op op basis van ID.

        DEF-391: kale connectie (geen committende ``with conn:``) zodat een read
        binnen een lopende transaction() die transactie niet vroegtijdig sluit.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT * FROM definities WHERE id = ?", (definitie_id,))
        row = cursor.fetchone()

        if row:
            return self._audit.row_to_record(row)
        return None

    def find_definitie(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        status: DefinitieStatus | None = None,
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> DefinitieRecord | None:
        """Zoek de leidende definitie op begrip (of synoniem) en gelijke context.

        DEF-622 (B-03): de vergelijking loopt over de genormaliseerde
        volledige contextverzameling (`zoek_gelijke_context`), niet over de
        ruwe JSON-strings. Bij meerdere treffers wint het vastgestelde record;
        daarna in beoordeling, dan concept, telkens de hoogste versie.
        Gearchiveerde records tellen alleen bij een expliciete statusvraag.
        """
        kandidaten = self._duplicates.zoek_gelijke_context(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            categorie=categorie,
            status=status,
        )
        for rij in kandidaten:
            if rij.id is None:
                continue
            record = self.get_definitie(int(rij.id))
            if record is not None:
                return record
        return None

    def update_definitie(
        self,
        definitie_id: int,
        updates: dict[str, Any],
        updated_by: str | None = None,
        _skip_audit: bool = False,
    ) -> bool:
        """Update bestaande definitie."""
        current = self.get_definitie(definitie_id)
        if not current:
            return False

        allowed_fields = {
            "begrip",
            "definitie",
            "bron",
            "status",
            "categorie",
            "ufo_categorie",
            "ontologie",
            "validated",
            "validation_notes",
            # DEF-621: zonder dit veld werd een bijgewerkte score stil
            # genegeerd - de kolom bleef op de waarde van een eerdere,
            # inmiddels vervangen definitietekst staan. `None` hoort hier
            # net zo goed te landen als een float: het is de expliciete
            # vastlegging dat er geen oordeel is.
            "validation_score",
            "reviewed_by",
            "review_date",
            "improved_version",
            "context_info",
            "metadata",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "toelichting_proces",
            "ketenpartners",
            "approved_by",
            "approved_at",
            "approval_notes",
        }

        set_clauses = []
        params = []

        for field, value in updates.items():
            if hasattr(current, field) and field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = ?")
        params.append(datetime.now(UTC))

        if updated_by:
            set_clauses.append("updated_by = ?")
            params.append(updated_by)

        expected_version = updates.get("version_number")
        set_clauses.append("version_number = version_number + 1")

        where_clause = "id = ?"
        where_params: list[Any] = [definitie_id]
        if expected_version is not None:
            where_clause += " AND version_number = ?"
            where_params.append(expected_version)

        query = (
            "UPDATE definities SET " + ", ".join(set_clauses) + f" WHERE {where_clause}"
        )

        # DEF-391: UPDATE + audit-log atomair (all-or-nothing).
        with self._db.transaction() as conn:
            cursor = conn.execute(query, params + where_params)
            if cursor.rowcount == 0 and expected_version is not None:
                logger.warning(
                    f"Optimistic lock failed for definitie {definitie_id} (expected version {expected_version})"
                )
                return False

            if not _skip_audit:
                self._audit.log_geschiedenis(
                    definitie_id,
                    "updated",
                    updated_by,
                    f"Definitie geupdate: {list(updates.keys())}",
                )

        logger.info(f"Updated definitie {definitie_id}")
        return True

    def change_status(
        self,
        definitie_id: int,
        new_status: DefinitieStatus,
        changed_by: str | None = None,
        notes: str | None = None,
        *,
        ketenpartners: list[str] | None = None,
        ufo_categorie: str | Unset | None = UNSET,
        expected_version: int | None = None,
    ) -> bool:
        """Wijzig status van definitie in één UPDATE (één versiebump).

        DEF-482: ``ketenpartners`` en ``ufo_categorie`` liften mee in dezelfde
        UPDATE als de status; ``ufo_categorie=""`` maakt de kolom leeg, weglaten
        (``UNSET``) laat haar staan. ``expected_version`` is de optimistic lock:
        wijkt de opgeslagen versie af, dan wordt niets geschreven en is het
        resultaat ``False``.
        """
        updates: dict[str, Any] = {"status": new_status.value}

        if new_status == DefinitieStatus.ESTABLISHED and changed_by:
            updates.update(
                {
                    "approved_by": changed_by,
                    "approved_at": datetime.now(UTC),
                    "approval_notes": notes,
                }
            )
        if ketenpartners is not None:
            updates["ketenpartners"] = json.dumps(
                list(ketenpartners), ensure_ascii=False
            )
        if not isinstance(ufo_categorie, Unset):
            updates["ufo_categorie"] = ufo_categorie or None
        if expected_version is not None:
            updates["version_number"] = expected_version

        # DEF-391: status-UPDATE + audit-log atomair. update_definitie opent zelf
        # een transaction() die hier aansluit (nesting-guard) i.p.v. apart te
        # committen, zodat de statuswijziging en de audit-trail all-or-nothing zijn.
        with self._db.transaction():
            success = self.update_definitie(
                definitie_id, updates, changed_by, _skip_audit=True
            )

            if success:
                self._audit.log_geschiedenis(
                    definitie_id,
                    "status_changed",
                    changed_by,
                    f"Status gewijzigd naar {new_status.value}",
                )

        return success

    def get_all(self) -> list[DefinitieRecord]:
        """Haal alle definities op zonder limit."""
        return self._search.search_definities(limit=None)

    def get_by_status(self, status: str) -> list[DefinitieRecord]:
        """Haal definities op gefilterd op status."""
        try:
            status_enum = DefinitieStatus(status)
        except ValueError as e:
            valid_statuses = ", ".join([s.value for s in DefinitieStatus])
            raise ValueError(
                f"Ongeldige status '{status}'. Toegestane waarden: {valid_statuses}"
            ) from e

        return self._search.search_definities(status=status_enum, limit=None)
