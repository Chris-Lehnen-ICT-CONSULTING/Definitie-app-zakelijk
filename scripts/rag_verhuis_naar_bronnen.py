"""Verhuis de bronbibliotheek van data/definities.db naar data/bronnen.db (DEF-620).

RAG fase 3: de RAG-tabellen (collecties, documenten, fragmenten met embeddings)
krijgen een eigen bestand. Dit script kopieert ze met behoud van id's; de
definitiedatabase wordt alleen gelezen en blijft ongewijzigd.

Zonder ``--bevestig`` is het een droge run: alleen controles en aantallen.
Met ``--bevestig``:

1. geverifieerde backup van de bron (DEF-663) naar de backupmap;
2. kopie naar een tijdelijk bestand naast het doel, met het bronnenschema;
3. per collectie aantal documenten/fragmenten en een inhoudshash
   (id, document, tekst, embedding, metadata) vergelijken tussen bron en kopie,
   plus ``integrity_check`` en ``foreign_key_check``;
4. pas dan het tijdelijke bestand atomair op de plaats van het doel zetten.

Het doel mag niet bestaan, of moet een leeg bronnenbestand zijn (alleen de
RAG-tabellen, 0 rijen; de app maakt dat vanzelf aan). Elke andere database
(met gegevens, met andere tabellen, een definitiedatabase) wordt geweigerd.

Draai dit alleen terwijl de app gestopt is.

Voorbeeld:
    python scripts/rag_verhuis_naar_bronnen.py --van data/definities.db \\
        --naar data/bronnen.db            # droog
    python scripts/rag_verhuis_naar_bronnen.py --van data/definities.db \\
        --naar data/bronnen.db --bevestig
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from database.sqlite_backup import BackupError, create_verified_backup
from services.rag.bronnen_schema import RAG_TABELLEN, zorg_voor_bronnen_schema


class VerhuisError(RuntimeError):
    """Een controle is niet geslaagd."""


KOLOMMEN = {
    "rag_collections": ("id", "collection_name", "created_at", "metadata_json"),
    "rag_documents": (
        "id", "collection_id", "filename", "file_type", "chunk_count",
        "rechtsgebied", "processed_at", "file_path",
    ),
    "rag_chunks": (
        "id", "collection_id", "document_id", "chunk_text", "embedding",
        "chunk_index", "rechtsgebied", "wet_regeling", "artikel_lid",
        "created_at", "bron_type", "metadata",
    ),
}  # fmt: skip


def _alleen_lezen(pad: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{pad}?mode=ro", uri=True)


def _tabellen(conn: sqlite3.Connection) -> set[str]:
    return {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _overzicht(conn: sqlite3.Connection) -> dict[int, tuple[str, int, int, str]]:
    """Per collectie: (naam, documenten, fragmenten, inhoudshash)."""
    uit: dict[int, tuple[str, int, int, str]] = {}
    for cid, naam, aangemaakt, meta in conn.execute(
        "SELECT id, collection_name, created_at, metadata_json FROM rag_collections "
        "ORDER BY id"
    ):
        h = hashlib.sha256(repr((cid, naam, aangemaakt, meta)).encode())
        docs = conn.execute(
            "SELECT id, filename, file_type, chunk_count, rechtsgebied, processed_at, "
            "file_path FROM rag_documents WHERE collection_id = ? ORDER BY id",
            (cid,),
        ).fetchall()
        h.update(repr(docs).encode())
        n = 0
        for rij in conn.execute(
            "SELECT id, document_id, chunk_text, chunk_index, rechtsgebied, "
            "wet_regeling, artikel_lid, created_at, bron_type, metadata, embedding "
            "FROM rag_chunks WHERE collection_id = ? ORDER BY id",
            (cid,),
        ):
            h.update(repr(rij[:-1]).encode())
            h.update(rij[-1] or b"")
            n += 1
        uit[int(cid)] = (naam, len(docs), n, h.hexdigest())
    return uit


def _totalen(conn: sqlite3.Connection) -> tuple[tuple[str, int, int | None], ...]:
    """Per RAG-tabel (naam, aantal rijen, AUTOINCREMENT-teller)."""
    uit = []
    for tabel in RAG_TABELLEN:
        n = conn.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
        seq = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabel,)
        ).fetchone()
        uit.append((tabel, int(n), int(seq[0]) if seq else None))
    return tuple(uit)


def _wezen(conn: sqlite3.Connection) -> tuple[int, int]:
    """(documenten zonder collectie, fragmenten zonder collectie/document),
    inclusief ontbrekende (NULL) koppelingen."""
    docs = conn.execute(
        "SELECT COUNT(*) FROM rag_documents d WHERE d.collection_id IS NULL OR "
        "NOT EXISTS (SELECT 1 FROM rag_collections c WHERE c.id = d.collection_id)"
    ).fetchone()[0]
    chunks = conn.execute(
        "SELECT COUNT(*) FROM rag_chunks k WHERE k.collection_id IS NULL OR "
        "k.document_id IS NULL OR "
        "NOT EXISTS (SELECT 1 FROM rag_collections c WHERE c.id = k.collection_id) OR "
        "NOT EXISTS (SELECT 1 FROM rag_documents d WHERE d.id = k.document_id "
        "AND d.collection_id = k.collection_id)"
    ).fetchone()[0]
    return int(docs), int(chunks)


def controleer(van: Path, naar: Path) -> dict[int, tuple[str, int, int, str]]:
    """Controles vooraf; geeft het overzicht van de bron."""
    van, naar = van.resolve(), naar.resolve()
    if van == naar:
        raise VerhuisError("bron en doel zijn hetzelfde bestand")
    if not van.is_file():
        raise VerhuisError(f"bron niet gevonden: {van}")
    conn = _alleen_lezen(van)
    try:
        ontbreekt = set(RAG_TABELLEN) - _tabellen(conn)
        if ontbreekt:
            raise VerhuisError(f"bron mist tabellen: {sorted(ontbreekt)}")
        wezen = _wezen(conn)
        if any(wezen):
            raise VerhuisError(
                f"bron heeft verweesde rijen (documenten, fragmenten) = {wezen}"
            )
        overzicht = _overzicht(conn)
    finally:
        conn.close()
    _controleer_doel(naar)
    return overzicht


def _controleer_doel(naar: Path) -> None:
    """Het doel mag niet bestaan, leeg zijn (0 bytes) of alleen een leeg
    bronnenschema bevatten. Elke andere database wordt geweigerd."""
    if not naar.exists() or naar.stat().st_size == 0:
        return
    if not naar.is_file():
        raise VerhuisError(f"doel is geen bestand: {naar}")
    try:
        conn = _alleen_lezen(naar)
        try:
            tabellen = _tabellen(conn)
            versie = conn.execute("PRAGMA user_version").fetchone()[0]
            vreemd = tabellen - set(RAG_TABELLEN) - {"sqlite_sequence"}
            if "definities" in tabellen:
                raise VerhuisError(f"doel is een definitiedatabase: {naar}")
            if vreemd or versie not in (0, 1) or set(RAG_TABELLEN) - tabellen:
                raise VerhuisError(
                    f"doel is geen leeg bronnenbestand (tabellen {sorted(tabellen)}, "
                    f"user_version {versie}): {naar}"
                )
            gevuld = {
                t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in RAG_TABELLEN
            }
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        raise VerhuisError(f"doel is geen leesbare SQLite-database: {naar}") from exc
    if any(gevuld.values()):
        raise VerhuisError(f"doel bevat al gegevens: {gevuld}")


def _kopieer(van: Path, tijdelijk: Path) -> None:
    """Kopieer de RAG-tabellen rij voor rij (zonder ATTACH), met behoud van id's."""
    zorg_voor_bronnen_schema(tijdelijk)
    bron = _alleen_lezen(van)
    doel = sqlite3.connect(tijdelijk)
    try:
        with doel:
            for tabel in RAG_TABELLEN:
                kol = ", ".join(KOLOMMEN[tabel])
                plekken = ", ".join("?" for _ in KOLOMMEN[tabel])
                rijen = bron.execute(f"SELECT {kol} FROM {tabel} ORDER BY id")
                while blok := rijen.fetchmany(500):
                    doel.executemany(
                        f"INSERT INTO {tabel} ({kol}) VALUES ({plekken})", blok
                    )
                # AUTOINCREMENT-teller meenemen: id's van eerder verwijderde
                # rijen (bv. het oude Sv) worden in het nieuwe bestand niet
                # opnieuw uitgegeven.
                rij = bron.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabel,)
                ).fetchone()
                if rij is not None:
                    doel.execute(
                        "UPDATE sqlite_sequence SET seq = ? WHERE name = ? AND seq < ?",
                        (rij[0], tabel, rij[0]),
                    )
                    doel.execute(
                        "INSERT INTO sqlite_sequence (name, seq) SELECT ?, ? WHERE "
                        "NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = ?)",
                        (tabel, rij[0], tabel),
                    )
    finally:
        bron.close()
        doel.close()


def voer_uit(
    van: Path,
    naar: Path,
    overzicht: dict[int, tuple[str, int, int, str]],
    backupmap: Path,
    stempel: str | None = None,
) -> Path:
    """Backup, kopie, vergelijking, plaatsing. Geeft het backuppad."""
    van, naar = van.resolve(), naar.resolve()
    stempel = stempel or datetime.now().strftime("%Y%m%d_%H%M%S")
    backupmap.mkdir(parents=True, exist_ok=True)
    backup = backupmap / f"definities_backup_voor_verhuizing_bronnen_{stempel}.db"
    try:
        create_verified_backup(van, backup)
    except BackupError as exc:
        raise VerhuisError(f"backup mislukt: {exc.reason}") from exc

    tijdelijk = naar.with_name(f".{naar.name}.verhuizing-{stempel}")
    if tijdelijk.exists():
        raise VerhuisError(f"tijdelijk bestand bestaat al: {tijdelijk}")
    try:
        _kopieer(van, tijdelijk)
        conn = _alleen_lezen(van)
        try:
            totalen_bron = _totalen(conn)
        finally:
            conn.close()
        conn = _alleen_lezen(tijdelijk)
        try:
            kopie = _overzicht(conn)
            totalen_kopie = _totalen(conn)
            integriteit = conn.execute("PRAGMA integrity_check").fetchone()[0]
            sleutels = conn.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            conn.close()
        if (
            kopie != overzicht
            or totalen_kopie != totalen_bron
            or integriteit != "ok"
            or sleutels
        ):
            raise VerhuisError(
                "kopie wijkt af van de bron of is niet intact "
                f"(integriteit={integriteit}, foreign keys={len(sleutels)})"
            )
        _controleer_doel(naar)  # het doel mag intussen niet gevuld zijn
        os.replace(tijdelijk, naar)
    except BaseException:
        tijdelijk.unlink(missing_ok=True)
        raise
    return backup


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--van", required=True, type=Path, help="definitiedatabase")
    ap.add_argument("--naar", required=True, type=Path, help="nieuw bronnenbestand")
    ap.add_argument(
        "--backupmap", type=Path, help="standaard de map backups naast de bron"
    )
    ap.add_argument("--bevestig", action="store_true", help="echt verhuizen")
    args = ap.parse_args(argv)

    try:
        overzicht = controleer(args.van, args.naar)
    except VerhuisError as exc:
        print(f"FOUT: {exc}. Niets gewijzigd.")
        return 2
    for cid, (naam, docs, chunks, _h) in overzicht.items():
        print(f"collectie {cid} {naam!r}: {docs} documenten, {chunks} fragmenten")
    if not args.bevestig:
        print("droge run: niets gewijzigd (gebruik --bevestig om te verhuizen)")
        return 0
    backupmap = args.backupmap or args.van.resolve().parent / "backups"
    try:
        backup = voer_uit(args.van, args.naar, overzicht, backupmap)
    except VerhuisError as exc:
        print(f"FOUT: {exc}. Doel ongewijzigd; bron ongewijzigd.")
        return 3
    print(f"verhuisd naar {args.naar.resolve()}; bron ongewijzigd; backup {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
