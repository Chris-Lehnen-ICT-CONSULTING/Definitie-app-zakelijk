"""Importeer wetten (XML/XHTML) in de bronbibliotheek (DEF-620).

Eén chunk per artikel (plus één per definitie). Formaten (``--formaat``):
``op`` officiële publicatie (Staatsblad, ``officiele_publicatie_parser``),
``bwb`` geldende toestand uit het BWB (``bwb_parser``) en ``eu``
EU-verordening uit Cellar (``eu_parser``). Opslag via
``RAGService.ingest_chunks`` (zelfde embedding, opslag en rollback als de
gewone upload). Voor de hele bronnenlijst: ``scripts/rag_importeer_bronnenlijst.py``.

Voorbeeld (eerst droog, dan echt; werk bij voorkeur eerst op een kopie):
    python scripts/rag_importeer_officiele_publicatie.py --db data/bronnen.db \\
        --collectie "Sv (nieuw, i.w.t. 1-4-2029)" \\
        --wet-regeling "Wetboek van Strafvordering (nieuw, i.w.t. 1-4-2029)" \\
        --bestanden stb-2026-56.xml stb-2026-57.xml --droog

Bestaat de collectie al, dan wordt die gebruikt. Een document met dezelfde
bestandsnaam wordt alleen overgeslagen als het compleet is (opgeslagen aantal
chunks = verwacht aantal); een incompleet document geeft een fout (exitcode 2)
zodat het eerst onderzocht wordt. Verwijdert nooit iets.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=False)

from services.rag.bronnen_schema import zorg_voor_bronnen_schema
from services.rag.bwb_parser import parse_bwb_toestand
from services.rag.constants import normaliseer_rechtsgebied
from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.eu_parser import parse_eu_xhtml
from services.rag.models import ChunkingResult
from services.rag.officiele_publicatie_parser import parse_officiele_publicatie
from services.rag.rag_service import RAGService


def _opgeslagen(db: str, cid: int, naam: str) -> tuple[int, int] | None:
    """(chunk_count in rag_documents, werkelijk aantal chunks) of None."""
    conn = sqlite3.connect(db)
    try:
        rij = conn.execute(
            "SELECT id, chunk_count FROM rag_documents "
            "WHERE collection_id = ? AND filename = ?",
            (cid, naam),
        ).fetchone()
        if rij is None:
            return None
        echt = conn.execute(
            "SELECT COUNT(*) FROM rag_chunks WHERE document_id = ?", (rij[0],)
        ).fetchone()[0]
        return int(rij[1] or 0), int(echt)
    finally:
        conn.close()


def _collectie_meta(db: str, cid: int) -> dict:
    conn = sqlite3.connect(db)
    try:
        rij = conn.execute(
            "SELECT metadata_json FROM rag_collections WHERE id = ?", (cid,)
        ).fetchone()
    finally:
        conn.close()
    try:
        meta = json.loads(rij[0] or "{}") if rij else {}
    except json.JSONDecodeError:
        meta = {}
    return meta if isinstance(meta, dict) else {}


def _collectie_id(db: str, naam: str) -> int | None:
    conn = sqlite3.connect(db)
    try:
        rij = conn.execute(
            "SELECT id FROM rag_collections WHERE collection_name = ?", (naam,)
        ).fetchone()
        return int(rij[0]) if rij else None
    finally:
        conn.close()


#: Parser per bronformaat (DEF-620 fase 3).
PARSERS: dict[str, Callable[..., ChunkingResult]] = {
    "op": parse_officiele_publicatie,
    "bwb": parse_bwb_toestand,
    "eu": parse_eu_xhtml,
}


def importeer(
    db: str,
    collectie: str,
    wet_regeling: str,
    rechtsgebied_ruw: str,
    bestanden: list[str],
    formaat: str = "op",
    droog: bool = False,
    bron: dict | None = None,
) -> int:
    """Parse en importeer bestanden in één collectie; geeft de exitcode.

    0 = gelukt (of compleet aanwezig), 1 = invoer- of parsefout,
    2 = incompleet document aanwezig (niets verwijderd).
    """
    rechtsgebied = normaliseer_rechtsgebied(rechtsgebied_ruw)
    if rechtsgebied is None:
        print(f"FOUT: onbekend rechtsgebied {rechtsgebied_ruw!r}")
        return 1
    parser = PARSERS.get(formaat)
    if parser is None:
        print(f"FOUT: onbekend formaat {formaat!r}")
        return 1

    resultaten = []
    for pad in bestanden:
        res = parser(pad, wet_regeling, rechtsgebied)
        if res.fout_melding or not res.chunks:
            print(f"FOUT {pad}: {res.fout_melding or 'geen chunks'}")
            return 1
        soorten = Counter(c.metadata.structuur_type for c in res.chunks)
        print(
            f"{Path(pad).name}: {len(res.chunks)} chunks {dict(soorten)}, "
            f"{res.totaal_tokens} tokens, max {max(c.token_count for c in res.chunks)}"
        )
        resultaten.append((pad, res))
    if droog:
        print("droog: niets geschreven")
        return 0

    zorg_voor_bronnen_schema(db)  # DEF-620: bronnenbestand met schema
    store = EmbeddingStore(db)
    cid = _collectie_id(db, collectie)
    if cid is None:
        extra: dict = {"type": "wetgeving", "rechtsgebied": rechtsgebied}
        if bron:
            extra["bron"] = bron
        cid = store.create_collection(
            collection_name=collectie,
            dimensions=EmbeddingService.DIMENSIONS,
            model=EmbeddingService.MODEL,
            extra_metadata=extra,
        )
        print(f"collectie aangemaakt: {collectie!r} (id {cid})")
    else:
        print(f"collectie bestaat al: {collectie!r} (id {cid})")
        if bron:
            # Zelfde collectienaam = zelfde versie: een gewijzigde bron mag niet
            # stil als "compleet" worden overgeslagen (DEF-620 fase 3).
            oud = (_collectie_meta(db, cid).get("bron") or {}).get("sha256") or {}
            nieuw = bron.get("sha256") or {}
            if not oud:
                print("  (bestaande collectie zonder bronhash; inhoud niet vergeleken)")
            verschil = sorted(
                n for n, h in nieuw.items() if oud.get(n) not in (None, h)
            )
            if verschil:
                print(
                    f"FOUT: bron gewijzigd t.o.v. de bestaande collectie {collectie!r} "
                    f"({verschil}); niets geïmporteerd. Een nieuwe versie hoort in een "
                    "nieuwe collectie (andere versie in de naam)."
                )
                return 2

    svc = RAGService(
        DocumentChunker(),
        EmbeddingService(os.environ.get("OPENAI_API_KEY", "")),
        store,
        db,
    )
    for pad, res in resultaten:
        naam = Path(pad).name
        bestaand = _opgeslagen(db, cid, naam)
        if bestaand is not None:
            verwacht = len(res.chunks)
            if bestaand == (verwacht, verwacht):
                print(f"overgeslagen (compleet aanwezig, {verwacht} chunks): {naam}")
                continue
            print(
                f"FOUT: {naam} staat al in de collectie maar is incompleet "
                f"(chunk_count={bestaand[0]}, chunks={bestaand[1]}, verwacht={verwacht}). "
                "Niets verwijderd; onderzoek dit document eerst."
            )
            return 2
        doc_id = svc.ingest_chunks(
            res,
            collection_id=cid,
            filename=naam,
            file_type=res.bestandstype,
            rechtsgebied=rechtsgebied,
            bron_type="wetgeving",
        )
        print(f"geïmporteerd: {naam} → document {doc_id}, {len(res.chunks)} chunks")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--collectie", required=True)
    ap.add_argument("--wet-regeling", required=True)
    ap.add_argument("--rechtsgebied", default="strafrecht")
    ap.add_argument("--formaat", choices=sorted(PARSERS), default="op")
    ap.add_argument("--bestanden", nargs="+", required=True)
    ap.add_argument("--droog", action="store_true", help="alleen parsen en tellen")
    args = ap.parse_args(argv)
    return importeer(
        args.db,
        args.collectie,
        args.wet_regeling,
        args.rechtsgebied,
        args.bestanden,
        formaat=args.formaat,
        droog=args.droog,
    )


if __name__ == "__main__":
    raise SystemExit(main())
