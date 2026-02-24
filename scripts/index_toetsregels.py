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
import os
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

    Raises:
        FileNotFoundError: als de directory niet bestaat.
    """
    if not regels_dir.exists():
        raise FileNotFoundError(
            f"Toetsregels directory niet gevonden: {regels_dir}. "
            "Controleer of het pad correct is en of de repository volledig is uitgecheckt."
        )
    regels = []
    for json_path in sorted(regels_dir.glob("*.json")):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Bestand '%s' overgeslagen: %s", json_path.name, exc)
            continue
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


def _maak_rag_service(db_path: str, api_key: str) -> RAGService:
    """Maak een geconfigureerde RAGService aan."""
    return RAGService(
        document_chunker=DocumentChunker(),
        embedding_service=EmbeddingService(api_key=api_key),
        embedding_store=EmbeddingStore(db_path),
        db_path=db_path,
    )


def _indexeer_regel(
    rag_service: RAGService,
    conn: sqlite3.Connection,
    regel: dict,
    collection_id: int,
    i: int,
    totaal: int,
) -> str:
    """Indexeer één toetsregel. Geeft 'geindexeerd', 'overgeslagen' of 'fout' terug."""
    bestandsnaam = regel.get("_bestandsnaam", f"toetsregel_{i}")
    filename = f"toetsregel_{bestandsnaam}"

    if is_already_indexed(conn, filename):
        logger.info("[%d/%d] Skip (al geïndexeerd): %s", i, totaal, bestandsnaam)
        return "overgeslagen"

    tekst = format_toetsregel_tekst(regel)
    try:
        rag_service.ingest_document(
            tekst=tekst,
            collection_id=collection_id,
            filename=filename,
            file_type="text/plain",
            bron_type=None,
        )
        logger.info(
            "[%d/%d] Geïndexeerd: %s — %s",
            i,
            totaal,
            bestandsnaam,
            regel.get("naam", ""),
        )
        return "geindexeerd"
    except Exception as exc:
        logger.error(
            "[%d/%d] Fout bij '%s': %s",
            i,
            totaal,
            bestandsnaam,
            exc,
            exc_info=True,
        )
        return "fout"


def index_toetsregels(db_path: str = DB_PATH, dry_run: bool = False) -> dict:
    """Indexeer toetsregels in de RAG kennisbank.

    Args:
        db_path: Pad naar SQLite database.
        dry_run: Als True worden geen wijzigingen opgeslagen.

    Returns:
        Dict met tellingen: geindexeerd, overgeslagen, fouten, totaal, succes.
    """
    regels = laad_toetsregels(REGELS_DIR)
    logger.info("Gevonden: %d toetsregels in %s", len(regels), REGELS_DIR)

    if dry_run:
        for regel in regels:
            logger.info(
                "  [DRY RUN] %s: %s", regel.get("_bestandsnaam"), regel.get("naam")
            )
        logger.info("[DRY RUN] Geen wijzigingen opgeslagen.")
        return {
            "geindexeerd": 0,
            "overgeslagen": 0,
            "fouten": 0,
            "totaal": len(regels),
            "succes": True,
        }

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_PROD")
    if not api_key:
        logger.error(
            "OPENAI_API_KEY niet ingesteld. Exporteer de key: export OPENAI_API_KEY=sk-..."
        )
        sys.exit(1)

    try:
        rag_service = _maak_rag_service(db_path, api_key)
        collection_id = rag_service._ensure_collection(COLLECTION_NAME)
    except Exception as exc:
        logger.error(
            "Kon RAG service of collection '%s' niet initialiseren: %s. "
            "Controleer of de database bestaat en het schema up-to-date is.",
            COLLECTION_NAME,
            exc,
        )
        sys.exit(1)

    logger.info("Collection '%s' (id=%d) gereed.", COLLECTION_NAME, collection_id)
    totaal = len(regels)
    geindexeerd = overgeslagen = fouten = 0

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        for i, regel in enumerate(regels, 1):
            status = _indexeer_regel(rag_service, conn, regel, collection_id, i, totaal)
            if status == "geindexeerd":
                geindexeerd += 1
            elif status == "overgeslagen":
                overgeslagen += 1
            else:
                fouten += 1
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
        "succes": fouten == 0,
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
    result = index_toetsregels(db_path=args.db_path, dry_run=args.dry_run)
    if result["fouten"] > 0:
        logger.error(
            "%d van %d toetsregels konden niet worden geïndexeerd.",
            result["fouten"],
            result["totaal"],
        )
        sys.exit(1)
