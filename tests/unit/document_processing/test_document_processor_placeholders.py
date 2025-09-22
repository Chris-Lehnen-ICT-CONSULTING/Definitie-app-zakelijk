import io
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(
    "placeholder",
    [
        "⚠️ PDF extractie vereist PyPDF2 library (pip install PyPDF2)",
        "⚠️ Word extractie vereist python-docx library (pip install python-docx)",
    ],
)
def test_placeholder_warnings_are_not_marked_success(placeholder):
    from document_processing.document_processor import DocumentProcessor

    dp = DocumentProcessor(storage_dir="data/test_uploaded_documents_placeholders")
    fake_bytes = b"%PDF-1.4 fake content"

    with patch(
        "document_processing.document_processor.extract_text_from_file",
        return_value=placeholder,
    ):
        doc = dp.process_uploaded_file(fake_bytes, filename="fake.pdf", mime_type="application/pdf")

    assert doc.processing_status == "error"
    assert doc.text_length == 0
    assert doc.error_message.startswith("⚠️")

