"""Tests voor scripts/index_toetsregels.py (DEF-275)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# scripts/ op het pad
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from index_toetsregels import (
    format_toetsregel_tekst,
    index_toetsregels,
    is_already_indexed,
    laad_toetsregels,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REGEL_FIXTURE = {
    "_bestandsnaam": "INT-02",
    "id": "INT_02",
    "naam": "Geen beslisregel",
    "uitleg": "Een definitie bevat geen beslisregels of voorwaarden.",
    "toelichting": "Beschrijft wat iets ís, niet wat ermee moet gebeuren.",
    "toetsvraag": "Bevat de definitie geen voorwaardelijke formuleringen?",
    "goede_voorbeelden": ["transitie-eis: eis die een organisatie ondersteunt..."],
    "foute_voorbeelden": [
        "transitie-eis: eis die een organisatie moet ondersteunen..."
    ],
    "prioriteit": "midden",
    "aanbeveling": "aanbevolen",
}


@pytest.fixture
def regels_dir(tmp_path: Path) -> Path:
    """Tijdelijke directory met twee voorbeeld toetsregel JSON-bestanden."""
    (tmp_path / "INT-02.json").write_text(
        json.dumps(REGEL_FIXTURE, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "STR-01.json").write_text(
        json.dumps(
            {
                "_bestandsnaam": "STR-01",
                "id": "STR_01",
                "naam": "definitie start met zelfstandig naamwoord",
                "uitleg": "Definitie moet starten met zelfstandig naamwoord.",
                "toelichting": "",
                "toetsvraag": "Begint de definitie met een zelfstandig naamwoord?",
                "goede_voorbeelden": ["proces dat beslissers identificeert"],
                "foute_voorbeelden": ["is een maatregel die recidive voorkomt"],
                "prioriteit": "hoog",
                "aanbeveling": "verplicht",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def leeg_db(tmp_path: Path) -> str:
    """SQLite database met alleen de rag_documents tabel."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE rag_documents (id INTEGER PRIMARY KEY, filename TEXT)")
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# laad_toetsregels
# ---------------------------------------------------------------------------


def test_laad_toetsregels_laadt_alle_json(regels_dir: Path) -> None:
    regels = laad_toetsregels(regels_dir)
    assert len(regels) == 2


def test_laad_toetsregels_voegt_bestandsnaam_toe(regels_dir: Path) -> None:
    regels = laad_toetsregels(regels_dir)
    bestandsnamen = {r["_bestandsnaam"] for r in regels}
    assert "INT-02" in bestandsnamen
    assert "STR-01" in bestandsnamen


def test_laad_toetsregels_sorteert_alfabetisch(regels_dir: Path) -> None:
    regels = laad_toetsregels(regels_dir)
    assert regels[0]["_bestandsnaam"] == "INT-02"
    assert regels[1]["_bestandsnaam"] == "STR-01"


def test_laad_toetsregels_leeg_dir_geeft_lege_lijst(tmp_path: Path) -> None:
    assert laad_toetsregels(tmp_path) == []


# ---------------------------------------------------------------------------
# format_toetsregel_tekst
# ---------------------------------------------------------------------------


def test_format_bevat_id_en_naam() -> None:
    tekst = format_toetsregel_tekst(REGEL_FIXTURE)
    assert "INT-02" in tekst
    assert "Geen beslisregel" in tekst


def test_format_bevat_uitleg_en_toelichting() -> None:
    tekst = format_toetsregel_tekst(REGEL_FIXTURE)
    assert "bevat geen beslisregels" in tekst
    assert "wat iets ís" in tekst


def test_format_bevat_goede_en_foute_voorbeelden() -> None:
    tekst = format_toetsregel_tekst(REGEL_FIXTURE)
    assert "✓" in tekst
    assert "✗" in tekst
    assert "transitie-eis" in tekst


def test_format_bevat_prioriteit_en_aanbeveling() -> None:
    tekst = format_toetsregel_tekst(REGEL_FIXTURE)
    assert "midden" in tekst
    assert "aanbevolen" in tekst


def test_format_zonder_optionele_velden() -> None:
    minimaal = {"_bestandsnaam": "X-01", "naam": "Test"}
    tekst = format_toetsregel_tekst(minimaal)
    assert "X-01" in tekst
    assert "Test" in tekst


# ---------------------------------------------------------------------------
# is_already_indexed
# ---------------------------------------------------------------------------


def test_is_already_indexed_false_voor_nieuw(leeg_db: str) -> None:
    conn = sqlite3.connect(leeg_db)
    assert not is_already_indexed(conn, "toetsregel_INT-02")
    conn.close()


def test_is_already_indexed_true_na_insert(leeg_db: str) -> None:
    conn = sqlite3.connect(leeg_db)
    conn.execute(
        "INSERT INTO rag_documents (filename) VALUES (?)", ("toetsregel_INT-02",)
    )
    conn.commit()
    assert is_already_indexed(conn, "toetsregel_INT-02")
    conn.close()


# ---------------------------------------------------------------------------
# index_toetsregels — integratie (mocked RAGService)
# ---------------------------------------------------------------------------


def test_dry_run_voert_geen_ingest_uit(regels_dir: Path) -> None:
    with (
        patch("index_toetsregels.REGELS_DIR", regels_dir),
        patch("index_toetsregels.RAGService") as mock_rag_cls,
    ):
        resultaat = index_toetsregels(dry_run=True)

    mock_rag_cls.assert_not_called()
    assert resultaat["geindexeerd"] == 0
    assert resultaat["totaal"] == 2


def test_indexeert_alle_nieuwe_regels(regels_dir: Path, tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")

    mock_rag = MagicMock()
    mock_rag._ensure_collection.return_value = 1
    mock_rag.get_collection_stats.return_value = {
        "document_count": 2,
        "chunk_count": 2,
    }

    with (
        patch("index_toetsregels.REGELS_DIR", regels_dir),
        patch("index_toetsregels.RAGService", return_value=mock_rag),
        patch("index_toetsregels.DocumentChunker"),
        patch("index_toetsregels.EmbeddingService"),
        patch("index_toetsregels.EmbeddingStore"),
        patch("index_toetsregels.sqlite3.connect") as mock_connect,
    ):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None  # niet geïndexeerd
        mock_connect.return_value = mock_conn

        resultaat = index_toetsregels(db_path=db_path)

    assert resultaat["geindexeerd"] == 2
    assert resultaat["overgeslagen"] == 0
    assert resultaat["fouten"] == 0
    assert mock_rag.ingest_document.call_count == 2


def test_slaat_al_geindexeerde_over(regels_dir: Path, tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")

    mock_rag = MagicMock()
    mock_rag._ensure_collection.return_value = 1
    mock_rag.get_collection_stats.return_value = {"document_count": 1, "chunk_count": 1}

    with (
        patch("index_toetsregels.REGELS_DIR", regels_dir),
        patch("index_toetsregels.RAGService", return_value=mock_rag),
        patch("index_toetsregels.DocumentChunker"),
        patch("index_toetsregels.EmbeddingService"),
        patch("index_toetsregels.EmbeddingStore"),
        patch("index_toetsregels.sqlite3.connect") as mock_connect,
    ):
        # Eerste regel al geïndexeerd, tweede niet
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.side_effect = [
            (1,),  # INT-02: al aanwezig
            None,  # STR-01: nieuw
        ]
        mock_connect.return_value = mock_conn

        resultaat = index_toetsregels(db_path=db_path)

    assert resultaat["geindexeerd"] == 1
    assert resultaat["overgeslagen"] == 1
    assert mock_rag.ingest_document.call_count == 1


def test_telt_fouten_bij_ingest_fout(regels_dir: Path, tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")

    mock_rag = MagicMock()
    mock_rag._ensure_collection.return_value = 1
    mock_rag.ingest_document.side_effect = RuntimeError("embedding mislukt")
    mock_rag.get_collection_stats.return_value = {"document_count": 0, "chunk_count": 0}

    with (
        patch("index_toetsregels.REGELS_DIR", regels_dir),
        patch("index_toetsregels.RAGService", return_value=mock_rag),
        patch("index_toetsregels.DocumentChunker"),
        patch("index_toetsregels.EmbeddingService"),
        patch("index_toetsregels.EmbeddingStore"),
        patch("index_toetsregels.sqlite3.connect") as mock_connect,
    ):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        resultaat = index_toetsregels(db_path=db_path)

    assert resultaat["fouten"] == 2
    assert resultaat["geindexeerd"] == 0
