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


def test_light_flow_upload_select_summarize_and_snippets():
    from document_processing.document_processor import get_document_processor
    from ui.tabbed_interface import TabbedInterface

    processor = get_document_processor()
    ui = TabbedInterface()

    begrip = "Authenticatie"

    content = make_docx_with_text(
        f"Intro. {begrip} is vereist in stap 1.\nParagraaf 2 bespreekt {begrip} opnieuw."
    )

    doc = processor.process_uploaded_file(
        content,
        filename="security.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert doc.processing_status == "success"

    # Aggregatie en samenvatting
    aggregated = processor.get_aggregated_context([doc.id])
    assert aggregated["document_count"] == 1

    summary = ui._build_document_context_summary(aggregated)
    assert isinstance(summary, str) and len(summary) > 0

    # Snippets (max 4 per doc)
    snippets = ui._build_document_snippets(
        begrip=begrip,
        selected_doc_ids=[doc.id],
        max_snippets_total=4,
        per_doc_max=4,
        snippet_window=200,
    )
    assert len(snippets) >= 2
    assert all(s.get("used_in_prompt") for s in snippets)

