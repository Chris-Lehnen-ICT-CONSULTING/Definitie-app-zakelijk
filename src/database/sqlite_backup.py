"""WAL-veilige SQLite-backup met verificatie vóór publicatie (DEF-663).

Een bestandskopie van alleen ``*.db`` verliest gecommitte rijen die nog in
``*.db-wal`` staan. Deze module gebruikt daarom uitsluitend de SQLite Online
Backup API (``sqlite3.Connection.backup``) op een read-only bron, en publiceert
het resultaat pas nadat ``PRAGMA integrity_check`` exact ``ok`` teruggeeft en
het schemamanifest van de backup gelijk is aan dat van de bron.

Werkwijze per aanroep:

1. paden valideren (geen glob/URI, geen symlink in enig padonderdeel van bron
   of doel, geen directory, doel bestaat niet, bron ≠ doel);
2. bron read-only openen (URI ``mode=ro``) en één leestransactie pinnen;
3. manifest lezen uit die snapshot en de kerntabellen controleren;
4. backup in begrensde stappen schrijven naar een eigen stagingbestand in de
   doelmap, met een totale deadline zodat contention nooit oneindig blokkeert;
5. staging verifiëren (integrity_check exact ``ok`` + kernschema + manifest);
6. atomisch publiceren zonder een bestaand doel te overschrijven.

De publicatie (stap 6) is het commitpunt: daarvóór laat een fout nooit een
doelbestand achter, hoogstens een herkenbaar stagingartefact
(``<doel>.staging-…``) bij een harde onderbreking. Een mislukte opruiming van
het eigen stagingbestand ná de publicatie is een waarschuwing, geen fout: de
backup bestaat en is geverifieerd. Alleen artefacten die tijdens dezelfde
aanroep zijn aangemaakt worden opgeruimd.

Herstellen naar een NIEUWE database is dezelfde route met de backup als bron:
``create_verified_backup(backup, nieuw_pad)``. In-place herstel valt buiten
deze module (DEF-666).

Logging bevat alleen een technische classificatie (``BackupError.reason``),
nooit paden of exceptietekst.

CLI: ``python -m database.sqlite_backup BRON DOEL`` (exit 0 = gepubliceerd).
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

BUSY_TIMEOUT_SECONDS = 5.0
"""Maximale wachttijd op een bronlock (rollback-journal-bron met open schrijver)."""

DEFAULT_DEADLINE_SECONDS = 60.0
"""Totale tijdsgrens per aanroep voor lezen en kopiëren; daarna wordt afgebroken."""

STAGING_BUSY_TIMEOUT_SECONDS = 0.1
"""Het stagingbestand is privé: een lock daarop is contention, geen wachtreden."""

BACKUP_PAGES_PER_STEP = 1024
"""Pagina's per backupstap; tussen de stappen wordt de deadline gecontroleerd."""

BACKUP_RETRY_SLEEP_SECONDS = 0.05
"""Pauze na een BUSY/LOCKED-stap vóór de volgende poging."""

PROGRESS_HANDLER_INSTRUCTIONS = 1000
"""Aantal VM-instructies tussen twee deadlinecontroles in een lopende query."""

STAGING_MARKER = ".staging-"

# Injecteerbare monotone klok: tests vervangen deze om deadlines deterministisch
# (zonder wallclock-wachttijd) te laten verlopen.
_monotonic = time.monotonic

# Kernmanifest: deze tabellen en kolommen moeten in elke bron aanwezig zijn.
# Rijaantallen zijn vrij (een lege database is geldig).
CORE_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "definities": ("id", "begrip", "definitie"),
    "definitie_geschiedenis": ("id", "definitie_id"),
    "definitie_tags": ("id", "definitie_id"),
    "definitie_voorbeelden": ("id", "definitie_id"),
    "synonym_groups": ("id", "canonical_term"),
    "synonym_group_members": ("id", "group_id", "term"),
    "import_export_logs": ("id",),
}

_GLOB_OR_CONTROL_CHARS = re.compile(r"[*?\[\]\x00\r\n]")
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


class BackupError(RuntimeError):
    """Backup geweigerd of mislukt; ``reason`` is een veilige classificatie."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SchemaManifest:
    """Schema en inhoudsomvang van een database, gelezen uit één snapshot."""

    objects: tuple[tuple[str, str, str, str | None], ...]
    """(type, naam, tabel, sql) van elk niet-intern object in sqlite_master."""

    columns: tuple[tuple[str, tuple[str, ...]], ...]
    """Kolomnamen per tabel."""

    row_counts: tuple[tuple[str, int], ...]
    """Rijaantal per tabel."""

    schema_version: int | None
    """Hoogste ``schema_version.version``; None als de tabel ontbreekt (pre-v5)."""

    def tables(self) -> dict[str, tuple[str, ...]]:
        return dict(self.columns)


# ---------------------------------------------------------------------------
# Lezen en verifiëren
# ---------------------------------------------------------------------------
def open_readonly_snapshot(
    path: Path, busy_timeout: float = BUSY_TIMEOUT_SECONDS
) -> sqlite3.Connection:
    """Open ``path`` read-only met een gepinde leestransactie.

    De eerste leesopdracht op de connection legt de snapshot vast; alles wat
    daarna binnen dezelfde transactie wordt gelezen of gebackupt komt uit
    diezelfde consistente toestand, ook als een schrijver intussen commit.
    ``busy_timeout`` begrenst het wachten op een bronlock.
    """
    conn = sqlite3.connect(
        path.resolve().as_uri() + "?mode=ro",
        uri=True,
        timeout=busy_timeout,
        isolation_level=None,
    )
    try:
        conn.execute("BEGIN")
    except sqlite3.Error:
        conn.close()
        raise
    return conn


def _quote_identifier(name: str) -> str:
    """Quote een SQLite-identifier; een dubbele quote in de naam wordt verdubbeld."""
    return '"' + name.replace('"', '""') + '"'


# Interne objecten beginnen (hoofdletterongevoelig) met het gereserveerde
# prefix 'sqlite_'. Een LIKE-patroon is hier fout: '_' is daarin een wildcard,
# waardoor een geldige gebruikerstabel zoals 'sqliteXextra' zou wegvallen.
_USER_OBJECTS_SQL = (
    "SELECT type, name, tbl_name, sql FROM sqlite_master "
    "WHERE lower(substr(name, 1, 7)) <> 'sqlite_' ORDER BY type, name"
)


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table)}").fetchone()
    return int(row[0])


def read_manifest(conn: sqlite3.Connection) -> SchemaManifest:
    """Lees het volledige schemamanifest en de rijaantallen uit ``conn``."""
    objects = tuple(conn.execute(_USER_OBJECTS_SQL).fetchall())
    tables = [name for kind, name, _tbl, _sql in objects if kind == "table"]
    columns = tuple(
        (
            table,
            tuple(
                row[1]
                for row in conn.execute(
                    f"PRAGMA table_info({_quote_identifier(table)})"
                )
            ),
        )
        for table in tables
    )
    row_counts = tuple((table, _count_rows(conn, table)) for table in tables)
    schema_version = None
    if "schema_version" in tables:
        schema_version = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()[0]
    return SchemaManifest(objects, columns, row_counts, schema_version)


def integrity_ok(conn: sqlite3.Connection) -> bool:
    """True alleen als ``PRAGMA integrity_check`` exact één rij ``ok`` geeft."""
    return conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]


def check_core_schema(manifest: SchemaManifest) -> None:
    """Raise ``BackupError("core_schema_incomplete")`` als een kerntabel/-kolom ontbreekt."""
    tables = manifest.tables()
    for table, required in CORE_TABLE_COLUMNS.items():
        present = tables.get(table)
        if present is None or any(column not in present for column in required):
            raise BackupError("core_schema_incomplete")


# ---------------------------------------------------------------------------
# Deadline
# ---------------------------------------------------------------------------
def _expired(deadline: float | None) -> bool:
    return deadline is not None and _monotonic() >= deadline


def monotonic_now() -> float:
    """Huidige waarde van de gedeelde (injecteerbare) monotone klok.

    Consumenten die een eigen deadline bijhouden (zoals de gzip-route in
    ``scripts/backup_restore.py``) gebruiken dezelfde klok als de helper, zodat
    één absolute deadline door alle stappen heen geldt.
    """
    return _monotonic()


def remaining_budget(deadline: float) -> float:
    """Resterend budget in seconden tot ``deadline``; nooit negatief."""
    return max(0.0, deadline - _monotonic())


def ensure_within_deadline(deadline: float | None) -> None:
    """Stapgrens-controle: raise ``backup_timeout`` zodra het budget op is."""
    if _expired(deadline):
        raise BackupError("backup_timeout")


def _classify_failure(deadline: float | None, reason: str) -> BackupError:
    """Fout in een except-blok: een verlopen budget wint van ``reason``.

    Altijd raisen met ``from None`` zodat de veilige reason geen
    exception-context (met paden in OSError-tekst) meeneemt.
    """
    return BackupError("backup_timeout" if _expired(deadline) else reason)


def _busy_timeout_within(deadline: float | None) -> float:
    """Busy-timeout voor een lockwacht, begrensd op het resterende budget.

    De SQLite busy-handler draait buiten de progress-handler om; zonder deze
    begrenzing zou een vergrendelde bron of backup de volledige
    ``BUSY_TIMEOUT_SECONDS`` kunnen kosten, ook als het budget al bijna op is.
    """
    if deadline is None:
        return BUSY_TIMEOUT_SECONDS
    return max(0.0, min(BUSY_TIMEOUT_SECONDS, deadline - _monotonic()))


def _arm_deadline(conn: sqlite3.Connection, deadline: float | None) -> None:
    """Laat SQLite een lopende query van ``conn`` afbreken na de deadline.

    De progress-handler wordt elke ``PROGRESS_HANDLER_INSTRUCTIONS`` VM-
    instructies aangeroepen; een niet-nul resultaat onderbreekt de query met
    ``OperationalError: interrupted``. Granulariteit: instructies binnen een
    statement; een enkele lange C-loop (zoals één ``OP_IntegrityCk``) eindigt
    eerst, waarna de stapgrens-controle het verlopen budget alsnog ziet.
    """
    if deadline is None:
        return

    def _abort_when_expired() -> int:
        return 1 if _monotonic() >= deadline else 0

    conn.set_progress_handler(_abort_when_expired, PROGRESS_HANDLER_INSTRUCTIONS)


def verify_backup_file(
    backup: Path,
    expected: SchemaManifest | None = None,
    *,
    deadline: float | None = None,
) -> SchemaManifest:
    """Gedeelde verifier: open ``backup`` read-only en controleer hem volledig.

    Controles: ``PRAGMA integrity_check`` exact ``ok``, het kernschema, en
    (indien opgegeven) gelijkheid met het manifest van de bron. Geeft het
    manifest van de backup terug; raist ``BackupError`` met een veilige
    ``reason`` (``backup_unreadable``, ``integrity_check_failed``,
    ``core_schema_incomplete``, ``manifest_mismatch``, ``backup_timeout``).
    ``deadline`` is een monotone tijdstempel (zie ``_monotonic``) waarna de
    verificatie wordt afgebroken.
    """
    backup = Path(backup)
    ensure_within_deadline(deadline)
    try:
        conn = open_readonly_snapshot(
            backup, busy_timeout=_busy_timeout_within(deadline)
        )
    except sqlite3.Error:
        raise _classify_failure(deadline, "backup_unreadable") from None
    try:
        _arm_deadline(conn, deadline)
        try:
            ok = integrity_ok(conn)
        except sqlite3.DatabaseError:
            if _expired(deadline):
                raise BackupError("backup_timeout") from None
            ok = False  # o.a. "file is not a database"
        if not ok:
            raise BackupError("integrity_check_failed")
        try:
            manifest = read_manifest(conn)
        except sqlite3.Error:
            raise _classify_failure(deadline, "backup_unreadable") from None
        ensure_within_deadline(deadline)
        check_core_schema(manifest)
        if expected is not None and manifest != expected:
            raise BackupError("manifest_mismatch")
        return manifest
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Padvalidatie
# ---------------------------------------------------------------------------
def _reject_symlink_components(path: Path, reason: str) -> None:
    """Weiger ``path`` als het bestand zelf óf een bovenliggende map een symlink is.

    ``is_dir()``/``resolve()`` volgen symlinks stilzwijgend; een aliasmap zou
    daardoor een bron of doel buiten de bedoelde map leggen. Elk onderdeel van
    het absolute pad wordt daarom afzonderlijk met ``is_symlink()`` getoetst.
    """
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise BackupError(reason)


def _reject_unsafe_text(path: Path) -> None:
    text = str(path)
    if not text or _GLOB_OR_CONTROL_CHARS.search(text) or _URI_SCHEME.match(text):
        raise BackupError("unsafe_path")


def validate_new_destination(destination: Path) -> None:
    """Weiger een doelpad dat niet veilig nieuw aangemaakt kan worden.

    Gedeeld door de helper en consumenten die zelf een eindbestand (zoals een
    ``.db.gz``) publiceren: geen glob/URI-tekst, geen symlink in enig
    padonderdeel, geen bestaand bestand/directory/symlink, en een bestaande
    echte doelmap.
    """
    destination = Path(destination)
    _reject_unsafe_text(destination)
    try:
        _reject_symlink_components(destination, "destination_symlink")
        if destination.exists():
            raise BackupError("destination_exists")
        if not destination.parent.is_dir():
            raise BackupError("destination_dir_missing")
    except OSError:
        # Bijv. PermissionError uit is_symlink()/exists(): veilige reason,
        # geen rauwe traceback met pad.
        raise BackupError("path_unreadable") from None


def _validate_paths(source: Path, destination: Path) -> None:
    _reject_unsafe_text(source)
    _reject_unsafe_text(destination)
    try:
        _reject_symlink_components(source, "source_symlink")
        if not source.exists():
            raise BackupError("source_missing")
        if not source.is_file():
            raise BackupError("source_not_a_file")
        _reject_symlink_components(destination, "destination_symlink")
        if os.path.realpath(source) == os.path.realpath(destination):
            raise BackupError("source_is_destination")
    except OSError:
        raise BackupError("path_unreadable") from None
    validate_new_destination(destination)


# ---------------------------------------------------------------------------
# Staging en publicatie
# ---------------------------------------------------------------------------
def make_staging(destination: Path) -> Path:
    """Maak een eigen, uniek en leeg stagingbestand naast ``destination``.

    De naam is herkenbaar (``<doelnaam>.staging-…``) zodat een artefact van
    een harde onderbreking nooit voor een geldige backup kan doorgaan.
    """
    destination = Path(destination)
    fd, name = tempfile.mkstemp(
        prefix=f"{destination.name}{STAGING_MARKER}", dir=destination.parent
    )
    os.close(fd)
    return Path(name)


def discard_staging(staging: Path) -> bool:
    """Verwijder alleen het eigen stagingbestand en zijn SQLite-bijbestanden.

    Geeft False terug als een artefact niet verwijderd kon worden. Dat wordt
    uitsluitend als waarschuwing gelogd (zonder pad) zodat een opruimfout
    nooit de oorspronkelijke foutclassificatie of een geslaagde publicatie
    maskeert. Uitsluitend bedoeld voor artefacten die de aanroeper zelf in
    dezelfde aanroep heeft aangemaakt.
    """
    staging = Path(staging)
    clean = True
    for suffix in ("", "-journal", "-wal", "-shm"):
        artefact = staging.with_name(staging.name + suffix)
        try:
            if artefact.is_file():
                artefact.unlink()
        except OSError:
            clean = False
    if not clean:
        logger.warning("sqlite_backup: staging_cleanup_failed")
    return clean


def _copy_snapshot(
    source_conn: sqlite3.Connection, staging: Path, deadline: float
) -> None:
    """Kopieer de gepinde snapshot in begrensde stappen naar ``staging``.

    ``Connection.backup`` herhaalt BUSY/LOCKED-stappen onbeperkt; de
    progress-callback controleert daarom na elke stap de deadline en breekt
    de backup gecontroleerd af met ``BackupError("backup_timeout")``.
    """

    def _guard_deadline(_status: int, _remaining: int, _total: int) -> None:
        ensure_within_deadline(deadline)

    target = sqlite3.connect(str(staging), timeout=STAGING_BUSY_TIMEOUT_SECONDS)
    try:
        source_conn.backup(
            target,
            pages=BACKUP_PAGES_PER_STEP,
            progress=_guard_deadline,
            sleep=BACKUP_RETRY_SLEEP_SECONDS,
        )
        # Eén zelfstandig bestand zonder -wal/-shm, ook als de bron WAL gebruikt.
        target.execute("PRAGMA journal_mode=DELETE")
    finally:
        target.close()


def publish_staged_file(staging: Path, destination: Path) -> None:
    """Publiceer een geverifieerd stagingbestand atomisch op ``destination``.

    Weigert een doel dat intussen is verschenen of een symlink is geworden
    (``destination_exists`` / ``destination_symlink``); de aanroeper ruimt
    daarna zelf de stagingnaam op met ``discard_staging``. Een geslaagde
    aanroep is het commitpunt van de backup.
    """
    _reject_symlink_components(destination, "destination_symlink")
    try:
        os.link(staging, destination)  # atomisch, weigert een bestaand doel
    except FileExistsError:
        raise BackupError("destination_exists") from None


# ---------------------------------------------------------------------------
# Publieke API
# ---------------------------------------------------------------------------
def create_verified_backup(
    source: Path, destination: Path, *, deadline_seconds: float | None = None
) -> SchemaManifest:
    """Maak een geverifieerde backup van ``source`` op ``destination``.

    Geeft het manifest van de gepubliceerde backup terug. Raist ``BackupError``
    met een veilige ``reason`` als de backup wordt geweigerd of mislukt; in dat
    geval bestaat ``destination`` niet. ``deadline_seconds`` (standaard
    ``DEFAULT_DEADLINE_SECONDS``) begrenst de totale duur van lezen en
    kopiëren, inclusief wachten op locks.
    """
    source = Path(source)
    destination = Path(destination)
    if deadline_seconds is None:
        deadline_seconds = DEFAULT_DEADLINE_SECONDS
    try:
        return _create_verified_backup(source, destination, deadline_seconds)
    except BackupError as exc:
        logger.error("sqlite_backup geweigerd of mislukt: %s", exc.reason)
        raise


def _create_verified_backup(
    source: Path, destination: Path, deadline_seconds: float
) -> SchemaManifest:
    # Het budget loopt vanaf binnenkomst; elke latere lockwacht krijgt alleen
    # wat er dan nog van over is (zie _busy_timeout_within).
    deadline = _monotonic() + deadline_seconds
    _validate_paths(source, destination)
    source_conn: sqlite3.Connection | None = None
    staging: Path | None = None
    published: Path | None = None
    phase = "source_unreadable"
    try:
        source_conn = open_readonly_snapshot(
            source, busy_timeout=_busy_timeout_within(deadline)
        )
        _arm_deadline(source_conn, deadline)
        manifest = read_manifest(source_conn)
        ensure_within_deadline(deadline)
        check_core_schema(manifest)
        phase = "copy_failed"
        staging = make_staging(destination)
        _copy_snapshot(source_conn, staging, deadline)
        source_conn.close()
        source_conn = None
        verify_backup_file(staging, manifest, deadline=deadline)
        # Geen late publicatie: ook na een geslaagde verificatie mag een
        # verlopen budget het doel niet meer laten verschijnen.
        ensure_within_deadline(deadline)
        phase = "publish_failed"
        publish_staged_file(staging, destination)
        # Commitpunt: het doel bestaat en is geverifieerd. Vanaf hier is de
        # stagingnaam alleen nog een op te ruimen tweede link naar hetzelfde
        # bestand; een opruimfout mag het succes niet meer omzetten in een fout.
        published, staging = staging, None
    except (sqlite3.Error, OSError):
        # Een door de progress-handler onderbroken query meldt zich als
        # OperationalError; classificeer dat als het verlopen budget. Altijd
        # ``from None``: de oorspronkelijke fouttekst kan paden bevatten.
        raise _classify_failure(deadline, phase) from None
    finally:
        if source_conn is not None:
            source_conn.close()
        if staging is not None:
            discard_staging(staging)
    discard_staging(published)
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sqlite_backup",
        description="WAL-veilige, geverifieerde SQLite-backup (DEF-663).",
    )
    parser.add_argument("source", type=Path, help="bestaande databasebron")
    parser.add_argument("destination", type=Path, help="nieuw backupbestand")
    args = parser.parse_args(argv)
    try:
        create_verified_backup(args.source, args.destination)
    except BackupError as exc:
        parser.exit(1, f"sqlite_backup: {exc.reason}\n")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
