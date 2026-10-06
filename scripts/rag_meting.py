"""Meet de kwaliteit van de bronbibliotheek-zoekfunctie (DEF-620, RAG fase 1).

Alleen-lezen: werk op een KOPIE van de database. Doet echte embedding-aanroepen
(OpenAI, centen). Meet per begrip uit de meetset:
  - lexicale precisie: aandeel geleverde fragmenten dat het begrip noemt
    (orakel = regex uit de meetset, onafhankelijk van de zoekcode; zegt niets
    over betekenis);
  - homoniemen: geleverde fragmenten die het begrip in een andere betekenis
    noemen (optioneel patroon per begrip);
  - kerntreffer: staat er een kernartikel in de top-k;
  - negatieven: aantal geleverde fragmenten (hoort 0 te zijn).

Beide modi bootsen de orchestrator na: 'oud' = kaal begrip, cosine >= RAG_MIN_SCORE;
'nieuw' = relevantiepoort op het begrip (zoektermen) én dezelfde drempel.

Gebruik:
    python scripts/rag_meting.py --db <kopie.db> --modus oud --uit oud.json
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=False)

from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGService

FIXTURE = ROOT / "tests" / "fixtures" / "rag_meting" / "sv_begrippen.json"


def _collectie(db: str, naam: str) -> tuple[int, list[tuple]]:
    """Id en documenten (bestandsnaam, aantal chunks) van de meetcollectie."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rij = conn.execute(
            "SELECT id FROM rag_collections WHERE collection_name = ?", (naam,)
        ).fetchone()
        if rij is None:
            raise SystemExit(f"collectie {naam!r} niet gevonden in {db}")
        docs = conn.execute(
            "SELECT d.filename, COUNT(c.id) FROM rag_documents d "
            "LEFT JOIN rag_chunks c ON c.document_id = d.id "
            "WHERE d.collection_id = ? GROUP BY d.id",
            (rij[0],),
        ).fetchall()
        return int(rij[0]), docs
    finally:
        conn.close()


def _zoek(
    svc: RAGService, begrip: str, modus: str, top_k: int, rg: str, cid: int
) -> list[dict]:
    drempel = float(os.getenv("RAG_MIN_SCORE", "0.3"))
    if modus == "nieuw":
        params = inspect.signature(svc.retrieve_context_multi).parameters
        if "zoektermen" not in params:
            raise SystemExit("modus 'nieuw' vereist RAGService met zoektermen")
        ctx = svc.retrieve_context_multi(
            query=begrip,
            collection_ids=[cid],
            top_k=top_k,
            rechtsgebied=rg,
            zoektermen=[begrip],
        )
        return [c for c in ctx.chunks if c.get("score", 0) >= drempel]
    ctx = svc.retrieve_context_multi(
        query=begrip, collection_ids=[cid], top_k=top_k, rechtsgebied=rg
    )
    return [c for c in ctx.chunks if c.get("score", 0) >= drempel]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="pad naar een KOPIE van definities.db")
    ap.add_argument("--modus", choices=["oud", "nieuw"], required=True)
    ap.add_argument("--uit", required=True)
    ap.add_argument(
        "--meetset",
        default=str(FIXTURE),
        help="pad naar de meetset (standaard: de Sv-meetset van fase 1)",
    )
    args = ap.parse_args()

    meetset = json.loads(Path(args.meetset).read_text(encoding="utf-8"))
    sleutel = os.environ.get("OPENAI_API_KEY", "")
    svc = RAGService(
        DocumentChunker(), EmbeddingService(sleutel), EmbeddingStore(args.db), args.db
    )
    top_k, rg = meetset["top_k"], meetset["rechtsgebied"]
    cid, documenten = _collectie(args.db, meetset["collectie"])

    regels: list[dict] = []
    for soort in ("positief", "negatief"):
        for item in meetset[soort]:
            patroon = re.compile(item["patroon"], re.IGNORECASE)
            homoniem = (
                re.compile(item["homoniem"], re.IGNORECASE)
                if item.get("homoniem")
                else None
            )
            chunks = _zoek(svc, item["begrip"], args.modus, top_k, rg, cid)
            gevonden = [
                {
                    "artikel": c.get("artikel_lid"),
                    "score": round(float(c.get("score", 0)), 3),
                    "noemt": bool(patroon.search(c.get("chunk_text", ""))),
                    "homoniem": bool(
                        homoniem and homoniem.search(c.get("chunk_text", ""))
                    ),
                }
                for c in chunks
            ]
            noemt = sum(g["noemt"] for g in gevonden)
            kern = set(item.get("kernartikelen", []))
            regels.append(
                {
                    "soort": soort,
                    "begrip": item["begrip"],
                    "geleverd": len(gevonden),
                    "noemt_begrip": noemt,
                    "homoniemen": sum(g["homoniem"] for g in gevonden),
                    "kerntreffer": any(g["artikel"] in kern for g in gevonden),
                    "fragmenten": gevonden,
                }
            )

    pos = [r for r in regels if r["soort"] == "positief"]
    neg = [r for r in regels if r["soort"] == "negatief"]
    geleverd = sum(r["geleverd"] for r in pos)
    samenvatting = {
        "modus": args.modus,
        "collectie": {"id": cid, "documenten": documenten},
        "lexicale_precisie": (
            (sum(r["noemt_begrip"] for r in pos) / geleverd) if geleverd else None
        ),
        "homoniemen_geleverd": sum(r["homoniemen"] for r in pos),
        "kerntreffers": f"{sum(r['kerntreffer'] for r in pos)}/{len(pos)}",
        "negatieven_geleverd": sum(r["geleverd"] for r in neg),
    }
    Path(args.uit).write_text(
        json.dumps(
            {"samenvatting": samenvatting, "regels": regels},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(samenvatting, ensure_ascii=False))
    for r in regels:
        print(
            f"{r['soort']:8s} {r['begrip']:22s} geleverd={r['geleverd']} "
            f"noemt={r['noemt_begrip']} homoniem={r['homoniemen']} "
            f"kern={r['kerntreffer']} "
            f"{[(g['artikel'], g['score']) for g in r['fragmenten']]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
