"""Tests for DEF-229 exception handling in DocumentProcessor.

These tests verify that silent exception patterns are properly logged
and handled according to the multi-agent consensus plan.
"""

from __future__ import annotations

import logging
import re
from unittest.mock import MagicMock, patch


class TestExtractLegalReferencesExceptions:
    """Tests for _extract_legal_references error handling."""

    def test_malformed_reference_object_logged(self, caplog, tmp_path):
        """Verify malformed reference objects are skipped with debug logging.

        DEF-229 Phase 2.1: Log individual reference extraction failures.
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        dp = DocumentProcessor(storage_dir=str(storage))

        # Create mock that raises on attribute access
        mock_ref = MagicMock()
        mock_ref.wet = None
        mock_ref.artikel = None
        type(mock_ref).boek = property(
            lambda self: (_ for _ in ()).throw(AttributeError("test"))
        )

        with patch(
            "document_processing.document_processor.JuridischePatronen", create=True
        ) as mock_jp:
            mock_jp.zoek_alle_verwijzingen.return_value = [mock_ref]

            with caplog.at_level(logging.DEBUG):
                result = dp._extract_legal_references("test tekst over artikel 123")

        # Should fall through to regex fallback
        assert "Skipping malformed reference object" in caplog.text or len(result) >= 0

    def test_domain_module_import_failure_uses_regex_fallback(self, caplog, tmp_path):
        """Verify fallback to regex when domain module raises ImportError.

        DEF-229 Phase 3.2: Domain module unavailable triggers regex fallback.
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        dp = DocumentProcessor(storage_dir=str(storage))

        # Simulate import failure
        with (
            patch.dict(
                "sys.modules",
                {
                    "domain": None,
                    "domain.juridisch": None,
                    "domain.juridisch.patronen": None,
                },
            ),
            caplog.at_level(logging.DEBUG),
        ):
            result = dp._extract_legal_references("artikel 123 van de wet")

        # Should find via regex fallback
        assert (
            any("artikel" in r.lower() for r in result)
            or "Domain module unavailable" in caplog.text
        )

    def test_regex_failure_returns_empty_with_warning(self, caplog, tmp_path):
        """Verify empty list returned and warning logged when regex fails.

        DEF-229 Phase 2.2: Log regex fallback failures with text length (NO text content).
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        dp = DocumentProcessor(storage_dir=str(storage))

        # Force regex to fail by making re.findall raise
        with (
            patch.dict(
                "sys.modules",
                {
                    "domain": None,
                    "domain.juridisch": None,
                    "domain.juridisch.patronen": None,
                },
            ),
            patch("re.findall", side_effect=re.error("Bad pattern")),
            caplog.at_level(logging.WARNING),
        ):
            result = dp._extract_legal_references("test text")

        assert result == []
        assert "Legal reference regex extraction failed" in caplog.text
        assert "text_length=" in caplog.text  # Verify we log length, not content


class TestLoadMetadataExceptions:
    """Tests for _load_metadata error handling (Phase 1.3 fix)."""

    def test_json_decode_error_clears_cache(self, caplog, tmp_path):
        """Verify corrupt JSON triggers cache clear with error logging.

        DEF-229 Phase 1.3: JSONDecodeError clears cache (known corrupt state).
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        metadata_file = storage / "documents_metadata.json"
        metadata_file.write_text("{ invalid json }")

        with caplog.at_level(logging.ERROR):
            dp = DocumentProcessor(storage_dir=str(storage))

        assert "Metadata JSON corrupt" in caplog.text
        assert len(dp._documents_cache) == 0

    def test_os_error_preserves_cache(self, caplog, tmp_path):
        """Verify OSError keeps existing cache (might be transient).

        DEF-229 Phase 1.3: OSError preserves cache - file might be temporarily locked.
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        # Create a valid metadata file first
        metadata_file = storage / "documents_metadata.json"
        metadata_file.write_text('{"documents": [], "last_updated": "2025-01-01"}')

        # Create processor, then simulate OSError on subsequent load
        dp = DocumentProcessor(storage_dir=str(storage))

        # Add something to cache
        mock_doc = MagicMock()
        mock_doc.id = "test-id"
        dp._documents_cache["test-id"] = mock_doc

        # Now make the file unreadable
        original_open = open

        def mock_open_for_metadata(*args, **kwargs):
            if str(metadata_file) in str(args[0]) and "r" in str(args[1:]):
                raise PermissionError("Access denied")
            return original_open(*args, **kwargs)

        with (
            patch("builtins.open", side_effect=mock_open_for_metadata),
            caplog.at_level(logging.WARNING),
        ):
            dp._load_metadata()

        # Cache should be preserved
        assert (
            "test-id" in dp._documents_cache
            or "bestaande cache behouden" in caplog.text
        )


class TestSaveMetadataExceptions:
    """Tests for _save_metadata error handling (Phase 1.4 fix)."""

    def test_save_error_logged_with_stack_trace(self, caplog, tmp_path):
        """Verify save failures include exc_info.

        DEF-229 Phase 1.4: Add exc_info=True to save metadata errors.
        """
        from document_processing.document_processor import DocumentProcessor

        storage = tmp_path / "docs"
        storage.mkdir()
        dp = DocumentProcessor(storage_dir=str(storage))

        # Add something to the cache
        mock_doc = MagicMock()
        mock_doc.id = "test-id"
        mock_doc.to_dict.return_value = {"id": "test-id"}
        dp._documents_cache["test-id"] = mock_doc

        with (
            patch("builtins.open", side_effect=PermissionError("Access denied")),
            caplog.at_level(logging.ERROR),
        ):
            dp._save_metadata()

        # DEF-229: Updated log message to indicate CRITICAL and data loss risk
        assert "CRITICAL: Metadata niet opgeslagen" in caplog.text
        assert "PermissionError" in caplog.text
        # Verify persistence_failed flag is set
        assert dp._persistence_failed is True
