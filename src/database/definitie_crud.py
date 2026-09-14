"""Core CRUD operaties voor definities."""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Final

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_duplicates import DefinitieDuplicateRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import DefinitieRecord, DefinitieStatus, VaststelconflictError

logger = logging.getLogger(__name__)

# De velden die samen de vaststel-identiteit vormen (B-03/B-10): begrip plus
# de drie contextlijsten. Categorie hoort daar bewust niet bij.
_IDENTITEITSVELDEN: tuple[str, ...] = (
    "begrip",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)


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

        # Alleen betekenisvolle tekst is een auditreden; een ander type
        # (bytes, getal, lijst) is een programmeerfout en wordt geweigerd vóór
        # het record wordt aangeraakt (reviewbevinding D4).
        if duplicate_reason is not None and not isinstance(duplicate_reason, str):
            msg = (
                "duplicate_reason moet tekst zijn (auditreden), niet "
                f"{type(duplicate_reason).__name__}"
            )
            raise ValueError(msg)
        reden = (duplicate_reason or "").strip()

        with operation_progress("saving_to_database"):
            now = datetime.now(UTC)
            record.created_at = now
            record.updated_at = now

            wb_value = (
                record.wettelijke_basis if record.wettelijke_basis is not None else "[]"
            )

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
                if record.status == DefinitieStatus.ESTABLISHED.value:
                    # B-03/B-10: ook een direct als vastgesteld aangemaakt
                    # record (import, tooling) mag geen tweede leidend record
                    # naast een bestaand vastgesteld record zetten.
                    self._eis_geen_vaststelconflict(
                        record.begrip,
                        record.organisatorische_context,
                        record.juridische_context,
                        record.wettelijke_basis,
                        eigen_id=None,
                    )
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

    def find_leidende_definitie(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any = "",
        wettelijke_basis: Any = None,
        *,
        eigen_id: int | None = None,
    ) -> DefinitieRecord | None:
        """Het vastgestelde, leidende record voor begrip + volledige context.

        Ongeacht categorie (B-03/B-10): categorie mag de exclusiviteit niet
        ongemerkt uitschakelen. `eigen_id` sluit het record zelf uit. Leest
        via een kale connectie en ziet dus ook de nog niet gecommitte staat
        binnen een lopende transactie — precies wat de hercontrole onder de
        schrijflock nodig heeft.
        """
        for rij in self._duplicates.zoek_gelijke_context(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            categorie=None,
            status=DefinitieStatus.ESTABLISHED,
        ):
            if rij.id is None or rij.id == eigen_id:
                continue
            if rij.via_synoniem:
                # De exclusiviteit geldt voor hetzelfde begrip (B-10). Een
                # ánder begrip dat dit begrip als synoniem voert, hoort bij
                # de generatielookup, niet bij de vaststelinvariant
                # (reviewbevinding E1).
                continue
            record = self.get_definitie(int(rij.id))
            if record is not None:
                return record
        return None

    def _eis_geen_vaststelconflict(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any,
        wettelijke_basis: Any,
        *,
        eigen_id: int | None,
    ) -> None:
        """De B-03/B-10-invariant op de persistentiegrens."""
        leidend = self.find_leidende_definitie(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            eigen_id=eigen_id,
        )
        if leidend is not None:
            msg = (
                f"Er is al een vastgestelde definitie (ID {leidend.id}) voor "
                f"'{begrip}' met dezelfde context; maximaal één leidend record "
                "per begrip en context (DEF-622). Vervang die bewust of archiveer "
                "haar eerst."
            )
            raise VaststelconflictError(msg, conflict_id=leidend.id)

    def set_context_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
    ) -> bool:
        """Leg de CON-01-expertbeoordeling vast op het record (DEF-622, B-07).

        Lees-wijzig-schrijf binnen één transactie op `validation_issues`;
        de overige issues blijven staan. Een gewone update: versie en audit
        volgen het bestaande pad.

        Herkomst (reviewbevinding V3): de beoordelaar in de beoordeling is de
        handelende gebruiker die haar opslaat (`updated_by`, de auditactor).
        Een payload met een andere beoordelaar wordt vóór mutatie geweigerd;
        ontbreekt de beoordelaar, dan wordt de handelende gebruiker gestempeld.
        Wie later vaststelt mag een ander zijn (bestaand contract).

        Versiebinding (reviewbevinding E2): de beoordeling krijgt het
        versienummer van het record ná deze opslag; elke latere wijziging
        (ook tekst terugzetten) geeft een nieuwere versie en laat haar
        vervallen.
        """
        if review is not None:
            if not isinstance(review, dict):
                msg = "context_review moet een dict zijn"
                raise ValueError(msg)
            actor = review.get("actor")
            handelend = updated_by if isinstance(updated_by, str) else None
            handelend = (handelend or "").strip() or None
            if handelend is None:
                msg = (
                    "set_context_review vereist een handelende gebruiker "
                    "(updated_by) als betrouwbare beoordelaarsbron"
                )
                raise ValueError(msg)
            if actor is not None and (
                not isinstance(actor, str) or actor.strip() != handelend
            ):
                msg = (
                    f"beoordelaar in de beoordeling ({actor!r}) wijkt af van de "
                    f"handelende gebruiker ({handelend!r}); geweigerd vóór opslag"
                )
                raise ValueError(msg)

        with self._db.transaction():
            current = self.get_definitie(definitie_id)
            if not current:
                return False
            if review is not None:
                review = {
                    **review,
                    "actor": handelend,
                    # De versie die het record ná deze opslag draagt.
                    "version_number": int(current.version_number or 0) + 1,
                }
            current.set_context_review(review)
            return self.update_definitie(
                definitie_id,
                {"validation_issues": current.validation_issues},
                updated_by,
            )

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
            # DEF-622: de CON-01-expertbeoordeling reist in dit veld mee;
            # zonder dit veld kon een beoordeling nooit worden bijgewerkt.
            "validation_issues",
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
            # DEF-622 (B-03/B-10): de invariant "maximaal één vastgesteld
            # record per begrip + volledige context" wordt hier, ónder de
            # schrijflock, hercontroleerd op de resulterende staat. Zo kan
            # geen enkele schrijfroute (statuswijziging, begrip-/context-
            # wijziging van een vastgesteld record, gelijktijdige poging) er
            # omheen. Categorie is bewust geen onderdeel van de identiteit.
            # Verse lezing ónder de lock: `current` van vóór de transactie kan
            # door een gelijktijdige vaststelling verouderd zijn.
            actueel = self.get_definitie(definitie_id) or current
            nieuwe_status = updates.get("status", actueel.status)
            raakt_identiteit = any(veld in updates for veld in _IDENTITEITSVELDEN)
            if nieuwe_status == DefinitieStatus.ESTABLISHED.value and (
                actueel.status != DefinitieStatus.ESTABLISHED.value or raakt_identiteit
            ):
                self._eis_geen_vaststelconflict(
                    updates.get("begrip", actueel.begrip),
                    updates.get(
                        "organisatorische_context", actueel.organisatorische_context
                    ),
                    updates.get("juridische_context", actueel.juridische_context),
                    updates.get("wettelijke_basis", actueel.wettelijke_basis),
                    eigen_id=definitie_id,
                )

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
                # DEF-622 (B-10): een notitie bij een statuswijziging — zoals
                # de verwijzing naar de opvolger bij archivering — hoort in
                # de reguliere statusaudit.
                reden = f"Status gewijzigd naar {new_status.value}"
                if notes and notes.strip():
                    reden += f": {notes.strip()}"
                self._audit.log_geschiedenis(
                    definitie_id, "status_changed", changed_by, reden
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
