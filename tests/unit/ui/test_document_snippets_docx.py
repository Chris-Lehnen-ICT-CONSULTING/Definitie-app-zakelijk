import io

import pytest

docx = pytest.importorskip("docx")


def make_docx_with_text(text: str) -> bytes:
    from docx import Document

    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def test_build_document_snippets_multiple_matches_with_citation():
    from document_processing.document_processor import get_document_processor
    from ui.tabbed_interface import TabbedInterface

    processor = get_document_processor()

    # Maak DOCX met meerdere matches
    begrip = "BegripX"
    content = make_docx_with_text(
        f"Dit is een test. {begrip} komt hier voor.\nNog een paragraaf met {begrip} en extra tekst."
    )

    # Verwerk document
    doc = processor.process_uploaded_file(
        content,
        filename="test.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert doc.processing_status == "success"
    assert begrip in doc.extracted_text

    # Instantieer UI controller en bouw snippets (per document max 4)
    ui = TabbedInterface()
    snippets = ui._build_document_snippets(
        begrip=begrip,
        selected_doc_ids=[doc.id],
        max_snippets_total=4,
        per_doc_max=4,
        snippet_window=120,
    )

    assert len(snippets) >= 2  # beide matches moeten gevonden worden
    # Controleer bronvermelding (DOCX → paragraaf label)
    assert all(s.get("citation_label", "").startswith("¶ ") for s in snippets)
