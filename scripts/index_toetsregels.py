#!/usr/bin/env python3
"""Indexeer toetsregels in de RAG kennisbank (DEF-275).

Leest alle 53 toetsregel JSON-bestanden uit src/toetsregels/regels/ en
indexeert ze in de 'toetsregels' RAG collection. Hierdoor kan de
generatie-pipeline bij het opstellen van een definitie relevante
kwaliteitsregels als context ophalen.

Gebruik:
    .venv/bin/python scripts/index_toetsregels.py
    .venv/bin/python scripts/index_toetsregels.py --dry-run
    .venv/bin/python scripts/index_toetsregels.py --db-path pad/naar/db
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

# src/ op het pad zodat imports werken vanuit scripts/
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "data/definities.db"
COLLECTION_NAME = "toetsregels"
REGELS_DIR = SRC_DIR / "toetsregels" / "regels"


def laad_toetsregels(regels_dir: Path) -> list[dict]:
    """Laad alle toetsregel JSON-bestanden uit de regels directory.

    Args:
        regels_dir: Pad naar src/toetsregels/regels/

    Returns:
        Gesorteerde lijst van toetsregel dicts.
    """
    regels = []
    for json_path in sorted(regels_dir.glob("*.json")):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        data["_bestandsnaam"] = json_path.stem  # bijv. "STR-01"
        regels.append(data)
    return regels


def format_toetsregel_tekst(regel: dict) -> str:
    """Formatteer een toetsregel als doorzoekbare tekst voor RAG.

    Combineert alle inhoudelijke velden zodat zowel semantisch zoeken
    (op concept) als patroonzoeken (op voorbeeld) goed werken.
    """
    regel_id = regel.get("_bestandsnaam", regel.get("id", ""))
    naam = regel.get("naam", "")
    uitleg = regel.get("uitleg", "")
    toelichting = regel.get("toelichting", "")
    toetsvraag = regel.get("toetsvraag", "")
    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])
    prioriteit = regel.get("prioriteit", "")
    aanbeveling = regel.get("aanbeveling", "")

    delen = [f"Toetsregel {regel_id}: {naam}"]
    if uitleg:
        delen.append(uitleg)
    if toelichting:
        delen.append(toelichting)
    if toetsvraag:
        delen.append(f"Toetsvraag: {toetsvraag}")
    if goede_voorbeelden:
        delen.append("Goede voorbeelden:")
        delen.extend(f"  ✓ {v}" for v in goede_voorbeelden)
    if foute_voorbeelden:
        delen.append("Foute voorbeelden:")
        delen.extend(f"  ✗ {v}" for v in foute_voorbeelden)
    if prioriteit or aanbeveling:
        delen.append(f"Prioriteit: {prioriteit} | Aanbeveling: {aanbeveling}")

    return "\n".join(delen)


def is_already_indexed(conn: sqlite3.Connection, filename: str) -> bool:
    """Return True als dit bestand al in rag_documents staat (idempotentie)."""
    row = conn.execute(
        "SELECT id FROM rag_documents WHERE filename = ?", (filename,)
    ).fetchone()
    return row is not None


def index_toetsregels(db_path: str = DB_PATH, dry_run: bool = False) -> dict:
    """Indexeer toetsregels in de RAG kennisbank.

    Args:
        db_path: Pad naar SQLite database.
        dry_run: Als True worden geen wijzigingen opgeslagen.

    Returns:
        Dict met tellingen: geindexeerd, overgeslagen, fouten, totaal.
    """
    regels = laad_toetsregels(REGELS_DIR)
    logger.info("Gevonden: %d toetsregels in %s", len(regels), REGELS_DIR)

    if dry_run:
        for regel in regels:
            logger.info(
                "  [DRY RUN] %s: %s",
                regel.get("_bestandsnaam"),
                regel.get("naam"),
            )
        logger.info("[DRY RUN] Geen wijzigingen opgeslagen.")
        return {"geindexeerd": 0, "overgeslagen": 0, "fouten": 0, "totaal": len(regels)}

    rag_service = RAGService(
        document_chunker=DocumentChunker(),
        embedding_service=EmbeddingService(),
        embedding_store=EmbeddingStore(db_path),
        db_path=db_path,
    )

    collection_id = rag_service._ensure_collection(COLLECTION_NAME)
    logger.info("Collection '%s' (id=%d) gereed.", COLLECTION_NAME, collection_id)

    geindexeerd = 0
    overgeslagen = 0
    fouten = 0
    totaal = len(regels)

    conn = sqlite3.connect(db_path)
    try:
        for i, regel in enumerate(regels, 1):
            bestandsnaam = regel.get("_bestandsnaam", f"toetsregel_{i}")
            filename = f"toetsregel_{bestandsnaam}"

            if is_already_indexed(conn, filename):
                overgeslagen += 1
                logger.info(
                    "[%d/%d] Skip (al geïndexeerd): %s", i, totaal, bestandsnaam
                )
                continue

            tekst = format_toetsregel_tekst(regel)

            try:
                rag_service.ingest_document(
                    tekst=tekst,
                    collection_id=collection_id,
                    filename=filename,
                    file_type="text/plain",
                    bron_type=None,
                )
                geindexeerd += 1
                logger.info(
                    "[%d/%d] Geïndexeerd: %s — %s",
                    i,
                    totaal,
                    bestandsnaam,
                    regel.get("naam", ""),
                )
            except Exception as exc:
                fouten += 1
                logger.error("[%d/%d] Fout bij '%s': %s", i, totaal, bestandsnaam, exc)
    finally:
        conn.close()

    stats = rag_service.get_collection_stats(collection_id)
    logger.info(
        "\nResultaat: %d geïndexeerd, %d overgeslagen, %d fouten",
        geindexeerd,
        overgeslagen,
        fouten,
    )
    logger.info(
        "Collection '%s': %d documenten, %d chunks",
        COLLECTION_NAME,
        stats["document_count"],
        stats["chunk_count"],
    )

    return {
        "geindexeerd": geindexeerd,
        "overgeslagen": overgeslagen,
        "fouten": fouten,
        "totaal": totaal,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Indexeer toetsregels in de RAG kennisbank (DEF-275)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon wat er geïndexeerd zou worden zonder wijzigingen op te slaan",
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH,
        help=f"Pad naar SQLite database (standaard: {DB_PATH})",
    )
    args = parser.parse_args()
    index_toetsregels(db_path=args.db_path, dry_run=args.dry_run)
