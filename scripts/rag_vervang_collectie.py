"""Vervang een collectie in de bronbibliotheek door een al geïmporteerde nieuwe (DEF-620).

RAG fase 2: het nieuwe Wetboek van Strafvordering komt in plaats van het oude.
Dit script verwijdert de oude collectie pas als alle controles slagen:

1. identiteit: oude en nieuwe collectie bestaan met de opgegeven naam en id,
   en hebben precies het verwachte aantal chunks;
2. nieuwe collectie compleet: elk document heeft chunk_count = werkelijke
   chunks, elke chunk heeft een embedding met de dimensie uit de metadata;
3. zoek-smoketest: de embedding van een chunk uit de nieuwe collectie vindt
   die chunk zelf terug op plek 1 (geen API-aanroep nodig);
4. geen project verwijst naar de oude collectie;
5. elk uploadpad van de oude collectie ligt in ``<basis>/data/uploads``.

Zonder ``--bevestig`` is het een droge run: alleen controles, niets gewijzigd.
Met ``--bevestig``, in vaste fasen:

- ``backup``: geverifieerde SQLite-backup (DEF-663) naar de backupmap;
- ``uploadkopie``: kopie van de nog bestaande uploads, met hun relatieve pad
  en een manifest (sha256), elke kopie gecontroleerd;
- ``database``: in één transactie (``BEGIN IMMEDIATE``) de toestand opnieuw
  toetsen aan de controle vooraf en pas dan de collectie verwijderen
  (CASCADE: documenten en chunks); wijkt iets af, dan wordt er niets verwijderd.
  Bewust niet via ``RAGManagementService.delete_collection``: die leest de
  uploadpaden opnieuw uit de database en ruimt ze ongecontroleerd op;
- ``bestanden``: alleen de gecontroleerde én gekopieerde uploads verwijderen;
- ``nacontrole``: niets van de oude collectie over, integrity_check ok,
  nieuwe collectie ongewijzigd.

Bij een fout of onderbreking meldt het script de fase, de werkelijke
databasestatus (opnieuw vastgesteld), de achtergebleven bestanden en de
herstelpaden. De backup wordt na het maken vergeleken met de gecontroleerde
toestand (ook de inhoud van de oude chunks); een upload wordt alleen
verwijderd als pad en inhoud nog gelijk zijn aan de kopie.

Draai dit alleen terwijl de app gestopt is: het script gaat uit van
exclusieve toegang tot de database en de uploadmap.

Uploadpaden in ``rag_documents.file_path`` zijn relatief aan de projectmap
waarin de app draaide. Die map is hier vast: de map boven ``data/`` van de
database (``<basis>/data/definities.db`` → ``<basis>``), los van de werkmap.

Voorbeeld (eerst droog):
    python scripts/rag_vervang_collectie.py --db data/definities.db \\
        --oud-id 9 --oud-naam WvSv --oud-chunks 1423 \\
        --nieuw-naam "Sv (nieuw, i.w.t. 1-4-2029)" --nieuw-chunks 1273
"""

from __future__ import annotations

import argparse
import hashlib
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


class VervangError(RuntimeError):
    """Een controle of fase is niet geslaagd."""


@dataclass(frozen=True)
class Staat:
    """Wat er vlak voor het verwijderen exact zo moet zijn als bij de controle."""

    oud_id: int
    oud_chunks: int
    oud_documenten: tuple[tuple[int, str | None], ...]  # (id, file_path)
    oud_inhoud: str  # sha256 over id, document, tekst en embedding van elke chunk
    nieuw_id: int
    nieuw_chunks: int
    nieuw_dimensie: int
    nieuw_incompleet: int  # documenten met chunk_count != werkelijke chunks
    nieuw_ongeldig: int  # chunks zonder embedding van de juiste dimensie
    projectverwijzingen: int
    gedeelde_uploads: int  # uploads van oud waar ook een ander document naar wijst


@dataclass(frozen=True)
class Upload:
    opgeslagen: str  # file_path zoals in de database
    pad: Path  # opgelost, binnen <basis>/data/uploads
    relatief: Path  # t.o.v. de basis, voor de kopie


@dataclass(frozen=True)
class Plan:
    db: Path
    basis: Path
    oud_naam: str
    nieuw_naam: str
    staat: Staat
    uploads: tuple[Upload, ...]


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


def _inhoud_hash(conn: sqlite3.Connection, cid: int) -> str:
    h = hashlib.sha256()
    for cid_, doc, tekst, emb in conn.execute(
        "SELECT id, document_id, chunk_text, embedding FROM rag_chunks "
        "WHERE collection_id = ? ORDER BY id",
        (cid,),
    ):
        for deel in (cid_, doc, tekst):
            h.update(repr(deel).encode())
        h.update(emb or b"")
    return h.hexdigest()


def _zelfde_bestand(basis: Path, file_path: str) -> Path:
    pad = Path(file_path)
    return (pad if pad.is_absolute() else basis / pad).resolve()


def _lees_staat(
    conn: sqlite3.Connection, oud_naam: str, nieuw_naam: str, basis: Path
) -> Staat:
    """Lees alles wat tussen controle, backup en verwijderen gelijk moet blijven."""
    oud = _collectie(conn, oud_naam)
    nieuw = _collectie(conn, nieuw_naam)
    if oud is None:
        raise VervangError(f"oude collectie {oud_naam!r} niet gevonden")
    if nieuw is None:
        raise VervangError(f"nieuwe collectie {nieuw_naam!r} niet gevonden")
    oud_id, nieuw_id = oud[0], nieuw[0]
    dimensie = int(nieuw[1].get("dimensions") or 0)
    oud_documenten = tuple(
        (int(i), fp)
        for i, fp in conn.execute(
            "SELECT id, file_path FROM rag_documents WHERE collection_id = ? "
            "ORDER BY id",
            (oud_id,),
        ).fetchall()
    )
    oud_bestanden = {_zelfde_bestand(basis, fp) for _i, fp in oud_documenten if fp}
    andere = {
        _zelfde_bestand(basis, fp)
        for (fp,) in conn.execute(
            "SELECT file_path FROM rag_documents WHERE file_path IS NOT NULL "
            "AND collection_id IS NOT ?",
            (oud_id,),
        )
    }
    return Staat(
        oud_id=oud_id,
        oud_chunks=_aantal_chunks(conn, oud_id),
        oud_documenten=oud_documenten,
        oud_inhoud=_inhoud_hash(conn, oud_id),
        nieuw_id=nieuw_id,
        nieuw_chunks=_aantal_chunks(conn, nieuw_id),
        nieuw_dimensie=dimensie,
        nieuw_incompleet=int(
            conn.execute(
                "SELECT COUNT(*) FROM rag_documents d WHERE d.collection_id = ? "
                "AND COALESCE(d.chunk_count, 0) != (SELECT COUNT(*) FROM rag_chunks c "
                "WHERE c.document_id = d.id)",
                (nieuw_id,),
            ).fetchone()[0]
        ),
        nieuw_ongeldig=int(
            conn.execute(
                "SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ? "
                "AND (embedding IS NULL OR length(embedding) != ?)",
                (nieuw_id, dimensie * 4),
            ).fetchone()[0]
        ),
        projectverwijzingen=int(
            conn.execute(
                "SELECT COUNT(*) FROM projects WHERE rag_collection_id = ?", (oud_id,)
            ).fetchone()[0]
        ),
        gedeelde_uploads=len(oud_bestanden & andere),
    )


def los_upload_op(basis: Path, db: Path, file_path: str) -> Upload:
    """Los een opgeslagen uploadpad op; alleen bestanden in <basis>/data/uploads."""
    uploadmap = (basis / "data" / "uploads").resolve()
    pad = Path(file_path)
    opgelost = (pad if pad.is_absolute() else basis / pad).resolve()
    beschermd = {db, db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm")}
    if (
        opgelost == uploadmap
        or not opgelost.is_relative_to(uploadmap)
        or opgelost in beschermd
    ):
        raise VervangError(f"uploadpad buiten {uploadmap}: {file_path!r}")
    return Upload(file_path, opgelost, opgelost.relative_to(basis.resolve()))


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
        staat = _lees_staat(conn, oud_naam, nieuw_naam, basis)
        if staat.oud_id != oud_id:
            raise VervangError(
                f"oude collectie {oud_naam!r} heeft id {staat.oud_id}, verwacht {oud_id}"
            )
        if staat.nieuw_id == staat.oud_id:
            raise VervangError("oude en nieuwe collectie zijn dezelfde")
        if staat.oud_chunks != oud_chunks:
            raise VervangError(
                f"oude collectie heeft {staat.oud_chunks} chunks, verwacht {oud_chunks}"
            )
        if staat.nieuw_chunks != nieuw_chunks:
            raise VervangError(
                f"nieuwe collectie heeft {staat.nieuw_chunks} chunks, "
                f"verwacht {nieuw_chunks}"
            )
        if staat.projectverwijzingen:
            raise VervangError(
                f"{staat.projectverwijzingen} project(en) verwijzen naar de oude collectie"
            )

        if staat.nieuw_incompleet:
            raise VervangError(
                f"{staat.nieuw_incompleet} document(en) in de nieuwe collectie incompleet"
            )
        if staat.nieuw_dimensie <= 0:
            raise VervangError("nieuwe collectie heeft geen embeddingdimensie")
        if staat.nieuw_ongeldig:
            raise VervangError(
                f"{staat.nieuw_ongeldig} chunks in de nieuwe collectie zonder "
                "geldige embedding"
            )
        if staat.gedeelde_uploads:
            raise VervangError(
                f"{staat.gedeelde_uploads} uploadbestand(en) ook in gebruik buiten "
                "de oude collectie"
            )
        eerste = conn.execute(
            "SELECT id FROM rag_chunks WHERE collection_id = ? ORDER BY id LIMIT 1",
            (staat.nieuw_id,),
        ).fetchone()
    finally:
        conn.close()

    uploads = tuple(
        los_upload_op(basis, db, fp) for _id, fp in staat.oud_documenten if fp
    )
    if len({u.pad for u in uploads}) != len(uploads):
        raise VervangError("meerdere documenten delen hetzelfde uploadbestand")

    if eerste is None:
        raise VervangError("nieuwe collectie is leeg")
    store = EmbeddingStore(str(db))
    vector = store.get_embedding(int(eerste[0]))
    treffers = (
        store.search_similar(vector, staat.nieuw_id, top_k=1)
        if vector is not None
        else []
    )
    if not treffers or treffers[0]["chunk_id"] != int(eerste[0]):
        raise VervangError("zoek-smoketest op de nieuwe collectie mislukt")

    return Plan(db, basis, oud_naam, nieuw_naam, staat, uploads)


def _sha256(pad: Path) -> str:
    h = hashlib.sha256()
    with pad.open("rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _kopieer_uploads(plan: Plan, doelmap: Path) -> list[tuple[Upload, str]]:
    """Kopieer bestaande uploads met hun relatieve pad; controleer elke kopie.

    Geeft (upload, sha256) per gekopieerd bestand.
    """
    bestaand = [u for u in plan.uploads if u.pad.is_file()]
    if not bestaand:
        return []
    doelmap.mkdir()
    gekopieerd = []
    for u in bestaand:
        doel = doelmap / u.relatief
        doel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(u.pad, doel)
        som = _sha256(doel)
        if _sha256(u.pad) != som:
            raise VervangError(f"kopie wijkt af van het origineel: {u.pad}")
        gekopieerd.append((u, som))
    manifest = [
        {"origineel": str(u.pad), "file_path": u.opgeslagen,
         "kopie": str(doelmap / u.relatief), "sha256": som}
        for u, som in gekopieerd
    ]  # fmt: skip
    (doelmap / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return gekopieerd


def _controleer_backup(plan: Plan, backup: Path) -> None:
    """De backup moet precies de gecontroleerde toestand bevatten."""
    conn = _verbind(backup)
    try:
        in_backup = _lees_staat(conn, plan.oud_naam, plan.nieuw_naam, plan.basis)
    finally:
        conn.close()
    if in_backup != plan.staat:
        raise VervangError("database gewijzigd vóór de backup; niets verwijderd")


def _verwijder_collectie(plan: Plan) -> None:
    """Toets de toestand opnieuw en verwijder in één transactie."""
    conn = sqlite3.connect(plan.db, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE")
        try:
            nu = _lees_staat(conn, plan.oud_naam, plan.nieuw_naam, plan.basis)
            if nu != plan.staat:
                raise VervangError(
                    "database gewijzigd sinds de controle; niets verwijderd"
                )
            cur = conn.execute(
                "DELETE FROM rag_collections WHERE id = ?", (plan.staat.oud_id,)
            )
            if cur.rowcount != 1:
                raise VervangError("collectie niet verwijderd")
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def _oud_verwijderd(plan: Plan) -> bool | None:
    """Werkelijke databasestatus na een fout; None als dat niet vast te stellen is."""
    try:
        conn = _verbind(plan.db)
        try:
            rij = conn.execute(
                "SELECT COUNT(*) FROM rag_collections WHERE id = ?",
                (plan.staat.oud_id,),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    return rij[0] == 0


def _verwijder_bestanden(plan: Plan, gekopieerd: list[tuple[Upload, str]]) -> None:
    """Verwijder alleen uploads die nog exact de gekopieerde inhoud hebben."""
    uploadmap = (plan.basis / "data" / "uploads").resolve()
    overgeslagen = []
    for u, som in gekopieerd:
        echt = Path(os.path.realpath(u.pad))
        if (
            echt != u.pad
            or not echt.is_relative_to(uploadmap)
            or not u.pad.is_file()
            or _sha256(u.pad) != som
        ):
            overgeslagen.append(str(u.pad))
            continue
        u.pad.unlink()
    if overgeslagen:
        raise VervangError(
            f"niet verwijderd (pad of inhoud gewijzigd na de kopie): {overgeslagen}"
        )


def _nacontrole(plan: Plan) -> None:
    conn = _verbind(plan.db)
    try:
        oud = plan.staat.oud_id
        rest = conn.execute(
            "SELECT (SELECT COUNT(*) FROM rag_collections WHERE id = ?),"
            " (SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?),"
            " (SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ?)",
            (oud, oud, oud),
        ).fetchone()
        integriteit = conn.execute("PRAGMA integrity_check").fetchone()[0]
        nieuw = _aantal_chunks(conn, plan.staat.nieuw_id)
    finally:
        conn.close()
    if any(rest) or integriteit != "ok" or nieuw != plan.staat.nieuw_chunks:
        raise VervangError(
            f"nacontrole mislukt (rest={rest}, integriteit={integriteit}, nieuw={nieuw})"
        )


def voer_uit(plan: Plan, backupmap: Path, stempel: str | None = None) -> Path:
    """Backup, uploadkopie, verwijderen, nacontrole. Geeft het backuppad.

    Raist VervangError met fase, databasestatus en herstelpaden bij elke fout
    of onderbreking.
    """
    stempel = stempel or datetime.now().strftime("%Y%m%d_%H%M%S")
    backupmap = backupmap.resolve()
    if backupmap.is_relative_to((plan.basis / "data" / "uploads").resolve()):
        raise VervangError("backupmap mag niet in de uploadmap liggen")
    backup = backupmap / f"definities_backup_voor_vervang_{stempel}.db"
    kopiemap = backupmap / f"uploads_voor_vervang_{stempel}"
    fase = "backup"
    gekopieerd: list[tuple[Upload, str]] = []
    try:
        backupmap.mkdir(parents=True, exist_ok=True)
        try:
            create_verified_backup(plan.db, backup)
        except BackupError as exc:
            raise VervangError(f"backup mislukt: {exc.reason}") from exc
        _controleer_backup(plan, backup)

        fase = "uploadkopie"
        gekopieerd = _kopieer_uploads(plan, kopiemap)

        fase = "database"
        _verwijder_collectie(plan)

        fase = "bestanden"
        _verwijder_bestanden(plan, gekopieerd)

        fase = "nacontrole"
        _nacontrole(plan)
    except BaseException as exc:
        verwijderd = _oud_verwijderd(plan)
        status = {
            True: "AL gewijzigd (oude collectie verwijderd)",
            False: "niet gewijzigd",
            None: "ONBEKEND (controleer handmatig)",
        }[verwijderd]
        over = [str(u.pad) for u, _som in gekopieerd if u.pad.exists()]
        rest = f"; achtergebleven uploads: {over}" if verwijderd and over else ""
        herstel = f"; backup: {backup}" if backup.exists() else ""
        if kopiemap.exists():
            herstel += f"; uploadkopieën: {kopiemap}"
        raise VervangError(
            f"fase {fase} mislukt ({type(exc).__name__}: {exc}); "
            f"database {status}{rest}{herstel}"
        ) from exc
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
        f"controles geslaagd: oud id {plan.staat.oud_id} → nieuw id "
        f"{plan.staat.nieuw_id} ({plan.staat.nieuw_chunks} chunks); uploads oud: "
        f"{[str(u.pad) for u in plan.uploads] or 'geen'}"
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
    print(f"vervangen: collectie {plan.staat.oud_id} verwijderd; backup {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
