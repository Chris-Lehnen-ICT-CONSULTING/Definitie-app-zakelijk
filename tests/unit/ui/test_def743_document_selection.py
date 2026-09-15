"""Selected short sources must survive without a literal search-term hit (DEF-743).

Exercises the real ``DefinitionGenerationHandler._build_document_snippets`` with
in-memory documents. The snippets are candidate sources for the prompt, not an
authority judgment: the assertions cover selection, locators and caps only.
"""

from types import SimpleNamespace

import pytest

from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]

# Awb 3:2, supplied research fixture (not an expert-adjudicated definition).
AWB32 = (
    "Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige "
    "kennis omtrent de relevante feiten en de af te wegen belangen."
)
PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
WHOLE = "selected_short_document"
MATCH = "term_match"


def document(doc_id, text, mime="text/plain"):
    return SimpleNamespace(
        id=doc_id, filename=f"{doc_id}.txt", extracted_text=text, mime_type=mime
    )


@pytest.fixture
def select(monkeypatch):
    """Run the real snippet builder against in-memory documents.

    ``docs`` overrides the single default document; ``selected`` overrides the
    selection (default: every document, in order). Remaining kwargs go to the
    production method (``max_snippets_total``, ``per_doc_max``, ``snippet_window``).
    """

    def run(
        text=AWB32,
        term="zorgvuldigheidsbeginsel",
        *,
        selected=None,
        docs=None,
        mime="text/plain",
        **kwargs,
    ):
        docs = [document("awb32", text, mime)] if docs is None else docs
        by_id = {doc.id: doc for doc in docs}
        monkeypatch.setattr(
            "ui.handlers.definition_generation_handler.get_document_processor",
            lambda: SimpleNamespace(get_document_by_id=by_id.get),
        )
        handler = DefinitionGenerationHandler(None, None, None)
        ids = list(by_id) if selected is None else selected
        return handler._build_document_snippets(term, ids, **kwargs)

    return run


def test_selected_short_source_retains_entire_passage_and_locator(select):
    snippets = select()
    assert len(snippets) == 1
    snippet = snippets[0]
    assert snippet["snippet"] == AWB32
    assert snippet["doc_id"] == "awb32"
    assert snippet["filename"] == "awb32.txt"
    assert snippet["title"] == "awb32.txt"
    assert snippet["citation_label"] == "volledig document"
    assert snippet["selection_basis"] == WHOLE
    assert snippet["score"] == 0.0  # No search match, not a source judgment.
    assert snippet["used_in_prompt"] is True


@pytest.mark.parametrize("term", ["", "   ", None])
def test_empty_term_does_not_select_sources(select, term):
    assert select(term=term) == []


@pytest.mark.parametrize("selected", [[], ["missing"]])
def test_only_explicitly_selected_available_sources(select, selected):
    assert select(selected=selected) == []


@pytest.mark.parametrize("text", [None, "", "   ", "x" * 281])
def test_no_arbitrary_excerpt_of_empty_or_long_unmatched_document(select, text):
    assert select(text=text) == []


def test_short_source_respects_window_total_and_per_document_limits(select):
    assert len(select(text="x" * 280)) == 1
    assert select(snippet_window=100) == []
    assert select(max_snippets_total=0) == []
    # A whole document is one source; the per-document cap does not multiply it.
    assert len(select(per_doc_max=3)) == 1


@pytest.mark.parametrize("mime", [PDF, DOCX])
def test_short_document_without_match_cites_whole_document_not_a_page(select, mime):
    snippets = select(mime=mime)
    assert len(snippets) == 1
    assert snippets[0]["citation_label"] == "volledig document"
    assert snippets[0]["selection_basis"] == WHOLE


def test_short_document_with_term_match_stays_a_term_match(select):
    snippets = select(term="Besluit")  # Case-insensitive, as before.
    assert len(snippets) == 1
    assert snippets[0]["selection_basis"] == MATCH
    assert snippets[0]["score"] == 1.0
    assert snippets[0]["citation_label"] is None
    assert "besluit" in snippets[0]["snippet"]


def test_existing_pdf_term_matches_keep_page_and_per_document_limit(select):
    snippets = select(
        text="voorblad\fbesluit in bron besluit",
        term="besluit",
        mime=PDF,
        per_doc_max=1,
    )
    assert len(snippets) == 1
    assert snippets[0]["citation_label"] == "p. 2"
    assert snippets[0]["selection_basis"] == MATCH
    assert snippets[0]["score"] == 1.0
    assert "besluit" in snippets[0]["snippet"]


def test_mixed_selection_keeps_order_and_per_document_basis(select):
    term = "archiefkaart"  # Absent from AWB32, present twice in the long text.
    long_hit = f"{term} " + "y" * 300 + f" {term}"  # Two matches, beyond window.
    docs = [
        document("kort", AWB32),  # Short, no match: whole document.
        document("lang", long_hit),  # Long, matches: term snippets only.
        document("blanco", "   "),  # Blank: never a source.
        document("lang-zonder", "z" * 300),  # Long, no match: no excerpt.
    ]
    snippets = select(term=term, docs=docs)
    assert [s["doc_id"] for s in snippets] == ["kort", "lang", "lang"]
    assert [s["selection_basis"] for s in snippets] == [WHOLE, MATCH, MATCH]
    assert snippets[0]["snippet"] == AWB32
    assert all(term in s["snippet"] for s in snippets[1:])
    assert len({s["snippet"] for s in snippets[1:]}) == 2  # Distinct excerpts.

    capped = select(term=term, docs=docs, max_snippets_total=2)
    assert [(s["doc_id"], s["selection_basis"]) for s in capped] == [
        ("kort", WHOLE),
        ("lang", MATCH),
    ]
