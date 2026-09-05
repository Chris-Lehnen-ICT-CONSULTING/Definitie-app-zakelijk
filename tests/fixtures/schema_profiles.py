"""Versieprofielen en sentineldata voor schema- en migratietests (DEF-664).

Elke test die een database "op versie N" nodig heeft bouwt die hier, altijd
uitsluitend op een tijdelijk pad. Het canonieke profiel (versie 3) is het
volledige ``src/database/schema.sql``; lagere profielen worden daaruit
afgeleid door precies de wijzigingen van v7, v6 en v5 terug te draaien:

- versie 2: rag_collections heeft de tellers nog, schema_version mist 3;
- versie 1: rag_chunks mist bron_type/metadata en de filterindexen, mist 2;
- pre-v5 (``None``): de acht v5-tabellen bestaan niet, geen schema_version.

De sentineldata is bewust divers: JSON-lijsten, NULL-velden, een
geschiedenisrij, voorbeelden, tags en synoniemen. ``lees_sentinels`` leest
alleen kolommen die in álle profielen bestaan, zodat de uitkomst vóór en ná
een migratie en na een restore één-op-één vergeleken kan worden.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL_PATH = REPO_ROOT / "src" / "database" / "schema.sql"

V5_TABELLEN: tuple[str, ...] = (
    "projects",
    "ontology_relationships",
    "ontology_terms",
    "ontological_models",
    "rag_chunks",
    "rag_documents",
    "rag_collections",
    "schema_version",
)

SENTINEL_PROMPT = '{"prompt": "sentinel-DEF-664", "model": "test", "tokens_used": 7}'
SENTINEL_CONTEXT = '["DJI", "OM"]'
SENTINEL_WETTELIJK = '["Awb", "Sv"]'

_NAAR_VERSIE_2 = """
ALTER TABLE rag_collections ADD COLUMN document_count INTEGER DEFAULT 0;
ALTER TABLE rag_collections ADD COLUMN chunk_count INTEGER DEFAULT 0;
DELETE FROM schema_version WHERE version = 3;
"""

_NAAR_VERSIE_1 = """
DROP INDEX idx_chunks_rechtsgebied;
DROP INDEX idx_chunks_wet_regeling;
DROP INDEX idx_chunks_bron_type;
ALTER TABLE rag_chunks DROP COLUMN bron_type;
ALTER TABLE rag_chunks DROP COLUMN metadata;
DELETE FROM schema_version WHERE version = 2;
"""

_SENTINELS_KERN = """
INSERT INTO definities (
    begrip, definitie, categorie, organisatorische_context, juridische_context,
    wettelijke_basis, status, validation_score, generation_prompt_data,
    datum_voorstel, ketenpartners, voorkeursterm
) VALUES (
    'sentinelbegrip', 'sentinelbegrip: een bewaakte definitie', 'type',
    '["DJI", "OM"]', '["strafrecht"]', '["Awb", "Sv"]', 'review', NULL,
    '{"prompt": "sentinel-DEF-664", "model": "test", "tokens_used": 7}',
    NULL, '["RvdK"]', 'sentinelterm'
);
INSERT INTO definitie_geschiedenis (definitie_id, begrip, wijziging_type, wijziging_reden)
    SELECT id, begrip, 'created', 'sentinel-reden' FROM definities WHERE begrip = 'sentinelbegrip';
INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde)
    SELECT id, 'synonyms', 'sentinelsynoniem', 1 FROM definities WHERE begrip = 'sentinelbegrip';
INSERT INTO definitie_tags (definitie_id, tag_naam, tag_waarde)
    SELECT id, 'sentinel', 'ja' FROM definities WHERE begrip = 'sentinelbegrip';
INSERT INTO synonym_groups (canonical_term, domain) VALUES ('sentinelbegrip', 'strafrecht');
INSERT INTO synonym_group_members (group_id, term, source, status)
    SELECT id, 'sentinelsynoniem', 'manual', 'active' FROM synonym_groups
    WHERE canonical_term = 'sentinelbegrip';
"""

_SENTINELS_RAG = """
INSERT INTO rag_collections (collection_name, metadata_json)
    VALUES ('sentinelcollectie', '{"dimensions": 8}');
INSERT INTO rag_documents (collection_id, filename, file_type, chunk_count, rechtsgebied,
                           file_path)
    SELECT id, 'sentinel.pdf', 'pdf', 1, 'bestuursrecht', 'uploads/sentinel-file-path.pdf'
    FROM rag_collections WHERE collection_name = 'sentinelcollectie';
INSERT INTO rag_chunks (collection_id, document_id, chunk_text, embedding, chunk_index,
                        rechtsgebied, wet_regeling, artikel_lid)
    SELECT c.id, d.id, 'Artikel 1 lid 2 sentinel', X'00FF10', 0, 'bestuursrecht', 'Awb',
           'art. 1:2'
    FROM rag_collections c JOIN rag_documents d ON d.collection_id = c.id
    WHERE c.collection_name = 'sentinelcollectie';
"""

# Extra sentinelvelden op definities die de oude selectieve herlezing miste.
_SENTINELS_DEFINITIES_EXTRA = """
UPDATE definities SET
    toelichting_proces = 'sentinel-toelichting',
    validation_issues = '[{"code": "sentinel"}]',
    source_reference = 'sentinel-bron',
    imported_from = 'sentinel-import',
    updated_by = 'sentinel-user',
    approval_notes = 'sentinel-notitie',
    export_destinations = '["sentinel-export"]'
WHERE begrip = 'sentinelbegrip';
"""


def lees_alles(pad: Path) -> dict[str, tuple[tuple[str, ...], list[tuple]]]:
    """Volledige inhoud van élke gebruikerstabel: (kolommen, rijen op rowid).

    Alle kolommen, ook extra gebruikerskolommen; niets geselecteerd. Dit is
    de basis van het restorebewijs: na herstel moet dit exact gelijk zijn.
    """
    conn = sqlite3.connect(str(pad))
    try:
        tabellen = [
            rij[0]
            for rij in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND lower(substr(name, 1, 7)) <> 'sqlite_' ORDER BY name"
            )
        ]
        uit: dict[str, tuple[tuple[str, ...], list[tuple]]] = {}
        for tabel in tabellen:
            kolomnamen = tuple(
                rij[1] for rij in conn.execute(f'PRAGMA table_info("{tabel}")')
            )
            rijen = conn.execute(f'SELECT * FROM "{tabel}" ORDER BY rowid').fetchall()
            uit[tabel] = (kolomnamen, rijen)
        return uit
    finally:
        conn.close()


def projecteer(
    inhoud: dict[str, tuple[tuple[str, ...], list[tuple]]],
    kolommen_per_tabel: dict[str, tuple[str, ...]],
) -> dict[str, list[tuple]]:
    """Rijen beperkt tot de opgegeven kolommen (in die volgorde), per tabel."""
    uit: dict[str, list[tuple]] = {}
    for tabel, keuze in kolommen_per_tabel.items():
        kolomnamen, rijen = inhoud[tabel]
        posities = [kolomnamen.index(k) for k in keuze]
        uit[tabel] = [tuple(rij[p] for p in posities) for rij in rijen]
    return uit


HERLEES_QUERIES: dict[str, str] = {
    "definities": (
        "SELECT id, begrip, definitie, categorie, organisatorische_context, "
        "juridische_context, wettelijke_basis, status, validation_score, "
        "generation_prompt_data, datum_voorstel, ketenpartners, voorkeursterm "
        "FROM definities ORDER BY id"
    ),
    "definitie_geschiedenis": (
        "SELECT id, definitie_id, begrip, wijziging_type, wijziging_reden "
        "FROM definitie_geschiedenis ORDER BY id"
    ),
    "definitie_voorbeelden": (
        "SELECT id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde "
        "FROM definitie_voorbeelden ORDER BY id"
    ),
    "definitie_tags": (
        "SELECT id, definitie_id, tag_naam, tag_waarde FROM definitie_tags ORDER BY id"
    ),
    "synonym_groups": "SELECT id, canonical_term, domain FROM synonym_groups ORDER BY id",
    "synonym_group_members": (
        "SELECT id, group_id, term, source, status FROM synonym_group_members ORDER BY id"
    ),
    "rag_collections": (
        "SELECT id, collection_name, metadata_json FROM rag_collections ORDER BY id"
    ),
    "rag_documents": (
        "SELECT id, collection_id, filename, rechtsgebied FROM rag_documents ORDER BY id"
    ),
    "rag_chunks": (
        "SELECT id, collection_id, document_id, chunk_text, chunk_index, rechtsgebied, "
        "wet_regeling, artikel_lid FROM rag_chunks ORDER BY id"
    ),
}


def bouw_profiel(pad: Path, versie: int | None) -> Path:
    """Bouw op ``pad`` een database in de vorm van schemaversie ``versie``."""
    if versie is not None and versie not in (1, 2, 3):
        raise ValueError(f"onbekend profiel: {versie!r}")
    conn = sqlite3.connect(str(pad))
    try:
        conn.executescript(SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
        if versie is None or versie < 3:
            conn.executescript(_NAAR_VERSIE_2)
        if versie is None or versie < 2:
            conn.executescript(_NAAR_VERSIE_1)
        if versie is None:
            for tabel in V5_TABELLEN:
                conn.execute(f"DROP TABLE {tabel}")
        conn.commit()
    finally:
        conn.close()
    return pad


def zaai_sentinels(pad: Path) -> None:
    """Vul de kerntabellen (en de RAG-tabellen als die bestaan) met sentinels."""
    conn = sqlite3.connect(str(pad))
    try:
        conn.executescript(_SENTINELS_KERN)
        conn.executescript(_SENTINELS_DEFINITIES_EXTRA)
        if _tabel_bestaat(conn, "rag_chunks"):
            conn.executescript(_SENTINELS_RAG)
        conn.commit()
    finally:
        conn.close()


def lees_sentinels(
    pad: Path, tabellen: Iterable[str] | None = None
) -> dict[str, list[tuple]]:
    """Lees de sentinelrijen terug van ``tabellen`` (standaard: alle bestaande).

    Geef de sleutels van een eerdere uitkomst mee om na een migratie die
    tabellen toevoegt (v5) precies dezelfde tabellen te vergelijken.
    """
    conn = sqlite3.connect(str(pad))
    try:
        keuze = (
            HERLEES_QUERIES
            if tabellen is None
            else {tabel: HERLEES_QUERIES[tabel] for tabel in tabellen}
        )
        return {
            tabel: conn.execute(query).fetchall()
            for tabel, query in keuze.items()
            if _tabel_bestaat(conn, tabel)
        }
    finally:
        conn.close()


def schema_versies(pad: Path) -> list[int]:
    conn = sqlite3.connect(str(pad))
    try:
        if not _tabel_bestaat(conn, "schema_version"):
            return []
        return [
            int(rij[0])
            for rij in conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            )
        ]
    finally:
        conn.close()


def kolommen(pad: Path, tabel: str) -> list[str]:
    conn = sqlite3.connect(str(pad))
    try:
        return [rij[1] for rij in conn.execute(f"PRAGMA table_info({tabel})")]
    finally:
        conn.close()


def _tabel_bestaat(conn: sqlite3.Connection, tabel: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabel,)
        ).fetchone()
        is not None
    )
