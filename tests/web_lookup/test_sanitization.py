import pytest


def test_snippet_sanitization_strips_tags_and_blocks_protocols():
    try:
        from services.web_lookup.sanitization import sanitize_snippet
    except Exception as e:
        pytest.fail(f"sanitization module missing or import failed: {e}")

    raw = (
        "<script>alert(1)</script>"
        '<a href="javascript:evil()">bad</a>'
        "<div>Ok <b>content</b></div>"
    )
    result = sanitize_snippet(raw, max_length=500)
    assert "script" not in result.lower()
    assert "javascript:" not in result.lower()
    assert "Ok" in result
    assert "content" in result


def test_snippet_sanitization_truncates_to_limit():
    from services.web_lookup.sanitization import sanitize_snippet

    text = "A" * 1000
    result = sanitize_snippet(text, max_length=500)
    assert len(result) == 500
