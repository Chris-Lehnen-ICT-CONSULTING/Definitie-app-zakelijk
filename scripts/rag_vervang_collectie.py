"""Vervang een collectie in de bronbibliotheek door een al geïmporteerde nieuwe (DEF-620).

RAG fase 2: het nieuwe Wetboek van Strafvordering komt in plaats van het oude.
Dit script verwijdert de oude collectie pas als alle controles slagen:

1. identiteit: oude en nieuwe collectie bestaan met de opgegeven naam en id,
   en hebben precies het verwachte aantal chunks;
2. nieuwe collectie compleet: elk document heeft chunk_count = werkelijke
   chunks, elke chunk heeft een embedding met de dimensie uit de metadata;
3. zoek-smoketest: de embedding van een chunk uit de nieuwe collectie vindt
   die chunk zelf terug op plek 1 (geen API-aanroep nodig);
4. geen project verwijst naar de oude collectie.

Zonder ``--bevestig`` is het een droge run: alleen controles, niets gewijzigd.
Met ``--bevestig``: eerst een geverifieerde SQLite-backup (DEF-663) en een
kopie van nog bestaande uploadbestanden naar de backupmap, dan
``RAGManagementService.delete_collection`` en een nacontrole.

Uploadpaden in ``rag_documents.file_path`` zijn relatief aan de projectmap
waarin de app draaide. Die map is hier vast: de map boven ``data/`` van de
database (``<basis>/data/definities.db`` → ``<basis>``), los van de werkmap.
Een pad dat buiten die basis uitkomt, wordt geweigerd.

Voorbeeld (eerst droog):
    python scripts/rag_vervang_collectie.py --db data/definities.db \\
        --oud-id 9 --oud-naam WvSv --oud-chunks 1423 \\
        --nieuw-naam "Sv (nieuw, i.w.t. 1-4-2029)" --nieuw-chunks 1273
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from database.sqlite_backup import BackupError, create_verified_backup
from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_management_service import RAGManagementService


class VervangError(RuntimeError):
    """Een controle is niet geslaagd; er is niets gewijzigd."""


@dataclass(frozen=True)
class Plan:
    db: Path
    basis: Path
    oud_id: int
    nieuw_id: int
    nieuw_chunks: int
    uploads: tuple[Path, ...]  # opgeloste paden van de oude collectie


def _verbind(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def _collectie(conn: sqlite3.Connection, naam: str) -> tuple[int, dict] | None:
    rij = conn.execute(
        "SELECT id, metadata_json FROM rag_collections WHERE collection_name = ?",
        (naam,),
    ).fetchone()
    if rij is None:
        return None
    try:
        meta = json.loads(rij[1] or "{}")
    except json.JSONDecodeError:
        meta = {}
    return int(rij[0]), meta if isinstance(meta, dict) else {}


def _aantal_chunks(conn: sqlite3.Connection, cid: int) -> int:
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ?", (cid,)
        ).fetchone()[0]
    )


def los_upload_op(basis: Path, file_path: str) -> Path:
    """Los een opgeslagen uploadpad op tegen de basis; weiger paden erbuiten."""
    pad = Path(file_path)
    opgelost = (pad if pad.is_absolute() else basis / pad).resolve()
    if not opgelost.is_relative_to(basis.resolve()):
        raise VervangError(f"uploadpad buiten de projectmap: {file_path!r}")
    return opgelost


def controleer(
    db: Path,
    oud_id: int,
    oud_naam: str,
    oud_chunks: int,
    nieuw_naam: str,
    nieuw_chunks: int,
) -> Plan:
    """Alle controles vóór het vervangen; raist VervangError bij een afwijking."""
    db = db.resolve()
    if not db.is_file():
        raise VervangError(f"database niet gevonden: {db}")
    basis = db.parent.parent
    conn = _verbind(db)
    try:
        oud = _collectie(conn, oud_naam)
        if oud is None or oud[0] != oud_id:
            raise VervangError(
                f"oude collectie {oud_naam!r} met id {oud_id} niet gevonden"
                f" (gevonden: {oud and oud[0]})"
            )
        nieuw = _collectie(conn, nieuw_naam)
        if nieuw is None:
            raise VervangError(f"nieuwe collectie {nieuw_naam!r} niet gevonden")
        nieuw_id, nieuw_meta = nieuw
        if nieuw_id == oud_id:
            raise VervangError("oude en nieuwe collectie zijn dezelfde")

        echt_oud = _aantal_chunks(conn, oud_id)
        if echt_oud != oud_chunks:
            raise VervangError(
                f"oude collectie heeft {echt_oud} chunks, verwacht {oud_chunks}"
            )
        echt_nieuw = _aantal_chunks(conn, nieuw_id)
        if echt_nieuw != nieuw_chunks:
            raise VervangError(
                f"nieuwe collectie heeft {echt_nieuw} chunks, verwacht {nieuw_chunks}"
            )

        for doc_id, naam, chunk_count in conn.execute(
            "SELECT id, filename, chunk_count FROM rag_documents "
            "WHERE collection_id = ?",
            (nieuw_id,),
        ).fetchall():
            werkelijk = int(
                conn.execute(
                    "SELECT COUNT(*) FROM rag_chunks WHERE document_id = ?", (doc_id,)
                ).fetchone()[0]
            )
            if int(chunk_count or 0) != werkelijk:
                raise VervangError(
                    f"nieuw document {naam!r} incompleet: chunk_count="
                    f"{chunk_count}, chunks={werkelijk}"
                )

        dimensie = int(nieuw_meta.get("dimensions") or 0)
        if dimensie <= 0:
            raise VervangError("nieuwe collectie heeft geen embeddingdimensie")
        afwijkend = conn.execute(
            "SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ? "
            "AND (embedding IS NULL OR length(embedding) != ?)",
            (nieuw_id, dimensie * 4),
        ).fetchone()[0]
        if afwijkend:
            raise VervangError(
                f"{afwijkend} chunks in de nieuwe collectie zonder geldige embedding"
            )

        verwijzing = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE rag_collection_id = ?", (oud_id,)
        ).fetchone()[0]
        if verwijzing:
            raise VervangError(
                f"{verwijzing} project(en) verwijzen naar de oude collectie"
            )

        uploads = tuple(
            los_upload_op(basis, fp)
            for (fp,) in conn.execute(
                "SELECT file_path FROM rag_documents "
                "WHERE collection_id = ? AND file_path IS NOT NULL",
                (oud_id,),
            ).fetchall()
        )
        eerste = conn.execute(
            "SELECT id FROM rag_chunks WHERE collection_id = ? ORDER BY id LIMIT 1",
            (nieuw_id,),
        ).fetchone()
    finally:
        conn.close()

    if eerste is None:
        raise VervangError("nieuwe collectie is leeg")
    store = EmbeddingStore(str(db))
    vector = store.get_embedding(int(eerste[0]))
    treffers = (
        store.search_similar(vector, nieuw_id, top_k=1) if vector is not None else []
    )
    if not treffers or treffers[0]["chunk_id"] != int(eerste[0]):
        raise VervangError("zoek-smoketest op de nieuwe collectie mislukt")

    return Plan(db, basis, oud_id, nieuw_id, nieuw_chunks, uploads)


@contextlib.contextmanager
def _werkmap(map_: Path):
    vorige = Path.cwd()
    os.chdir(map_)
    try:
        yield
    finally:
        os.chdir(vorige)


def voer_uit(plan: Plan, backupmap: Path, stempel: str | None = None) -> Path:
    """Backup, kopie van uploads, verwijderen, nacontrole. Geeft het backuppad."""
    stempel = stempel or datetime.now().strftime("%Y%m%d_%H%M%S")
    backupmap.mkdir(parents=True, exist_ok=True)
    backup = backupmap / f"definities_backup_voor_vervang_{stempel}.db"
    try:
        create_verified_backup(plan.db, backup)
    except BackupError as exc:
        raise VervangError(f"backup mislukt: {exc.reason}") from exc

    bestaand = [p for p in plan.uploads if p.is_file()]
    if bestaand:
        doel = backupmap / f"uploads_voor_vervang_{stempel}"
        doel.mkdir()
        for pad in bestaand:
            shutil.copy2(pad, doel / pad.name)

    beheer = RAGManagementService(str(plan.db), EmbeddingStore(str(plan.db)))
    with _werkmap(plan.basis):
        if not beheer.delete_collection(plan.oud_id):
            raise VervangError(f"collectie {plan.oud_id} niet verwijderd")

    conn = _verbind(plan.db)
    try:
        rest = conn.execute(
            "SELECT (SELECT COUNT(*) FROM rag_collections WHERE id = ?),"
            " (SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?),"
            " (SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ?)",
            (plan.oud_id, plan.oud_id, plan.oud_id),
        ).fetchone()
        integriteit = conn.execute("PRAGMA integrity_check").fetchone()[0]
        nieuw = _aantal_chunks(conn, plan.nieuw_id)
    finally:
        conn.close()
    if any(rest) or integriteit != "ok" or nieuw != plan.nieuw_chunks:
        raise VervangError(
            f"nacontrole mislukt (rest={rest}, integriteit={integriteit}, "
            f"nieuw={nieuw}); herstel uit {backup}"
        )
    return backup


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--oud-id", required=True, type=int)
    ap.add_argument("--oud-naam", required=True)
    ap.add_argument("--oud-chunks", required=True, type=int)
    ap.add_argument("--nieuw-naam", required=True)
    ap.add_argument("--nieuw-chunks", required=True, type=int)
    ap.add_argument(
        "--backupmap",
        type=Path,
        help="standaard <basis>/data/backups naast de database",
    )
    ap.add_argument("--bevestig", action="store_true", help="echt vervangen")
    args = ap.parse_args(argv)

    try:
        plan = controleer(
            args.db,
            args.oud_id,
            args.oud_naam,
            args.oud_chunks,
            args.nieuw_naam,
            args.nieuw_chunks,
        )
    except VervangError as exc:
        print(f"FOUT: {exc}. Niets gewijzigd.")
        return 2
    print(
        f"controles geslaagd: oud id {plan.oud_id} → nieuw id {plan.nieuw_id} "
        f"({plan.nieuw_chunks} chunks); uploads oud: "
        f"{[str(p) for p in plan.uploads] or 'geen'}"
    )
    if not args.bevestig:
        print("droge run: niets gewijzigd (gebruik --bevestig om te vervangen)")
        return 0

    backupmap = args.backupmap or plan.basis / "data" / "backups"
    try:
        backup = voer_uit(plan, backupmap)
    except VervangError as exc:
        print(f"FOUT: {exc}")
        return 3
    print(f"vervangen: collectie {plan.oud_id} verwijderd; backup {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
