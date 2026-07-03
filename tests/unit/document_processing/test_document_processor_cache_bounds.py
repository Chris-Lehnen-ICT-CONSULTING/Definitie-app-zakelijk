"""Tests voor DEF-514: begrensde LRU-documentcache in DocumentProcessor.

De in-memory cache is de single source of truth voor het metadata-bestand;
eviction propageert daarom bewust naar disk bij de eerstvolgende save
(zie docstring van DocumentProcessor.__init__).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from document_processing.document_processor import DocumentProcessor

pytestmark = [pytest.mark.unit]

# Voldoende lange, niet-placeholder tekst zodat extractie als succesvol geldt
DOC_TEXT = (
    "Dit is een juridisch document over artikel 3 Awb met voldoende "
    "inhoud voor keyword-extractie en analyse van de wetgeving."
)


def _make_processor(tmp_path, max_documents: int) -> DocumentProcessor:
    storage = tmp_path / "docs"
    return DocumentProcessor(storage_dir=str(storage), max_documents=max_documents)


def _upload(processor: DocumentProcessor, name: str):
    """Upload een uniek document (content + naam bepalen de ID)."""
    with patch(
        "document_processing.document_processor.extract_text_from_file",
        return_value=DOC_TEXT,
    ):
        return processor.process_uploaded_file(
            file_content=f"inhoud van {name}".encode(),
            filename=f"{name}.txt",
            mime_type="text/plain",
        )


class TestDocumentCacheBounds:
    def test_cache_exceeds_max_evicts_oldest(self, tmp_path):
        """Cache boven max -> oudste (LRU) document wordt verwijderd."""
        processor = _make_processor(tmp_path, max_documents=3)

        docs = [_upload(processor, f"doc{i}") for i in range(4)]

        assert len(processor.get_processed_documents()) == 3
        assert processor.get_document_by_id(docs[0].id) is None  # oudste weg
        for doc in docs[1:]:
            assert processor.get_document_by_id(doc.id) is not None

    def test_access_refreshes_lru_recency(self, tmp_path):
        """Een gelezen document wordt recent en ontloopt daarmee eviction."""
        processor = _make_processor(tmp_path, max_documents=3)
        docs = [_upload(processor, f"doc{i}") for i in range(3)]

        # Touch doc0 zodat doc1 nu de LRU is
        assert processor.get_document_by_id(docs[0].id) is not None

        _upload(processor, "doc3")

        assert processor.get_document_by_id(docs[0].id) is not None
        assert processor.get_document_by_id(docs[1].id) is None  # LRU geëvict

    def test_duplicate_upload_refreshes_recency(self, tmp_path):
        """Herupload (cache-hit) telt als touch en veroorzaakt geen groei."""
        processor = _make_processor(tmp_path, max_documents=3)
        docs = [_upload(processor, f"doc{i}") for i in range(3)]

        _upload(processor, "doc0")  # zelfde content/naam -> cache-hit op doc0
        _upload(processor, "doc3")  # dwingt eviction af

        assert processor.get_document_by_id(docs[0].id) is not None
        assert processor.get_document_by_id(docs[1].id) is None

    def test_eviction_propagates_to_metadata_file(self, tmp_path):
        """Bewuste keuze DEF-514: cache is bron van waarheid voor metadata."""
        processor = _make_processor(tmp_path, max_documents=2)
        docs = [_upload(processor, f"doc{i}") for i in range(3)]

        data = json.loads(processor.metadata_file.read_text(encoding="utf-8"))
        persisted_ids = {d["id"] for d in data["documents"]}

        assert len(persisted_ids) == 2
        assert docs[0].id not in persisted_ids

    def test_load_metadata_enforces_bound(self, tmp_path):
        """Een nieuwe processor met lagere bound trimt bij het laden (LRU-orde)."""
        writer = _make_processor(tmp_path, max_documents=10)
        docs = [_upload(writer, f"doc{i}") for i in range(5)]

        reader = DocumentProcessor(storage_dir=str(tmp_path / "docs"), max_documents=3)

        assert len(reader.get_processed_documents()) == 3
        # De opgeslagen volgorde is LRU-orde: oudste twee zijn getrimd
        assert reader.get_document_by_id(docs[0].id) is None
        assert reader.get_document_by_id(docs[1].id) is None
        for doc in docs[2:]:
            assert reader.get_document_by_id(doc.id) is not None

    def test_default_bound_is_100(self, tmp_path):
        processor = _make_processor(
            tmp_path, max_documents=DocumentProcessor.MAX_CACHED_DOCUMENTS
        )
        assert processor.max_documents == 100
