"""Importeer wetten uit officiële publicaties (XML) in de bronbibliotheek (DEF-620).

RAG fase 2: één chunk per artikel (plus één per definitie) via
``services.rag.officiele_publicatie_parser``; opslag via
``RAGService.ingest_chunks`` (zelfde embedding, opslag en rollback als de
gewone upload).

Voorbeeld (eerst droog, dan echt; werk bij voorkeur eerst op een kopie):
    python scripts/rag_importeer_officiele_publicatie.py --db data/definities.db \\
        --collectie "Sv (nieuw, i.w.t. 1-4-2029)" \\
        --wet-regeling "Wetboek van Strafvordering (nieuw, i.w.t. 1-4-2029)" \\
        --bestanden stb-2026-56.xml stb-2026-57.xml --droog

Bestaat de collectie al, dan wordt die gebruikt; een document met dezelfde
bestandsnaam wordt niet opnieuw geïmporteerd. Verwijdert nooit iets.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=False)

from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.officiele_publicatie_parser import parse_officiele_publicatie
from services.rag.rag_management_service import RAGManagementService
from services.rag.rag_service import RAGService


def _collectie_id(db: str, naam: str) -> int | None:
    conn = sqlite3.connect(db)
    try:
        rij = conn.execute(
            "SELECT id FROM rag_collections WHERE collection_name = ?", (naam,)
        ).fetchone()
        return int(rij[0]) if rij else None
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--collectie", required=True)
    ap.add_argument("--wet-regeling", required=True)
    ap.add_argument("--rechtsgebied", default="strafrecht")
    ap.add_argument("--bestanden", nargs="+", required=True)
    ap.add_argument("--droog", action="store_true", help="alleen parsen en tellen")
    args = ap.parse_args()

    resultaten = []
    for pad in args.bestanden:
        res = parse_officiele_publicatie(pad, args.wet_regeling, args.rechtsgebied)
        if res.fout_melding or not res.chunks:
            print(f"FOUT {pad}: {res.fout_melding or 'geen chunks'}")
            return 1
        soorten = Counter(c.metadata.structuur_type for c in res.chunks)
        print(
            f"{Path(pad).name}: {len(res.chunks)} chunks {dict(soorten)}, "
            f"{res.totaal_tokens} tokens, max {max(c.token_count for c in res.chunks)}"
        )
        resultaten.append((pad, res))
    if args.droog:
        print("droog: niets geschreven")
        return 0

    store = EmbeddingStore(args.db)
    beheer = RAGManagementService(args.db, store)
    cid = _collectie_id(args.db, args.collectie)
    if cid is None:
        cid = beheer.create_collection(
            args.collectie, collection_type="wetgeving", rechtsgebied=args.rechtsgebied
        )
        print(f"collectie aangemaakt: {args.collectie!r} (id {cid})")
    else:
        print(f"collectie bestaat al: {args.collectie!r} (id {cid})")

    svc = RAGService(
        DocumentChunker(),
        EmbeddingService(os.environ.get("OPENAI_API_KEY", "")),
        store,
        args.db,
    )
    for pad, res in resultaten:
        naam = Path(pad).name
        if beheer.check_duplicate_document(cid, naam):
            print(f"overgeslagen (bestaat al): {naam}")
            continue
        doc_id = svc.ingest_chunks(
            res,
            collection_id=cid,
            filename=naam,
            rechtsgebied=args.rechtsgebied,
            bron_type="wetgeving",
        )
        print(f"geïmporteerd: {naam} → document {doc_id}, {len(res.chunks)} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
