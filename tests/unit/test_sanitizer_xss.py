"""Tests for XSS sanitization in src/validation/sanitizer.py.

Covers the regex bypass fix from DEF-395: event handlers without
leading whitespace must also be caught.
"""

import pytest

from validation.sanitizer import ContentSanitizer, ContentType, SanitizationLevel


@pytest.fixture
def sanitizer():
    return ContentSanitizer()


class TestXSSEventHandlerBypass:
    """DEF-395: Verify event handlers are removed regardless of leading whitespace."""

    def test_onclick_with_space(self, sanitizer):
        """Standard case: space before onclick."""
        result = sanitizer.sanitize(
            '<div onclick="alert(1)">test</div>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onclick" not in result.sanitized_value
        assert "alert" not in result.sanitized_value

    def test_onclick_without_space(self, sanitizer):
        """DEF-395 regression: no space before onclick."""
        result = sanitizer.sanitize(
            '<div/onclick="alert(1)">test</div>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onclick" not in result.sanitized_value
        assert "alert" not in result.sanitized_value

    def test_onerror_img_tag(self, sanitizer):
        """Common XSS vector: img onerror."""
        result = sanitizer.sanitize(
            '<img src=x onerror="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onerror" not in result.sanitized_value
        assert "alert" not in result.sanitized_value

    def test_onmouseover_no_quotes(self, sanitizer):
        """Event handler with unquoted value."""
        result = sanitizer.sanitize(
            "<div onmouseover=alert(1)>test</div>",
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onmouseover" not in result.sanitized_value

    def test_onload_body_tag(self, sanitizer):
        """Event handler on body tag."""
        result = sanitizer.sanitize(
            '<body onload="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onload" not in result.sanitized_value


class TestXSSScriptTags:
    """Verify script tag removal."""

    def test_script_tag_removed(self, sanitizer):
        result = sanitizer.sanitize(
            "<script>alert(1)</script>Normal text",
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "<script>" not in result.sanitized_value
        assert "alert" not in result.sanitized_value
        assert "Normal text" in result.sanitized_value

    def test_script_tag_with_attributes(self, sanitizer):
        result = sanitizer.sanitize(
            '<script type="text/javascript">alert(1)</script>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "script" not in result.sanitized_value.lower()


class TestXSSProtocols:
    """Verify dangerous protocol removal."""

    def test_javascript_protocol(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="javascript:alert(1)">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "javascript:" not in result.sanitized_value.lower()

    def test_vbscript_protocol(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="vbscript:msgbox(1)">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "vbscript:" not in result.sanitized_value.lower()

    def test_data_protocol(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="data:text/html,<script>alert(1)</script>">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "data:" not in result.sanitized_value.lower()


class TestXSSIframes:
    """Verify iframe removal."""

    def test_iframe_removed(self, sanitizer):
        result = sanitizer.sanitize(
            '<iframe src="evil.com"></iframe>Safe text',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "<iframe" not in result.sanitized_value.lower()
        assert "Safe text" in result.sanitized_value


class TestNormalContentPreserved:
    """Verify normal content passes through unchanged."""

    def test_plain_text_unchanged(self, sanitizer):
        text = "Dit is een normale Nederlandse tekst."
        result = sanitizer.sanitize(
            text, ContentType.PLAIN_TEXT, SanitizationLevel.MODERATE
        )
        assert result.sanitized_value == text

    def test_definition_text_preserved(self, sanitizer):
        text = "Een rechtspersoon is een entiteit die zelfstandig rechten en plichten kan hebben."
        result = sanitizer.sanitize(
            text, ContentType.DUTCH_TEXT, SanitizationLevel.MODERATE
        )
        assert "rechtspersoon" in result.sanitized_value
        assert "entiteit" in result.sanitized_value

    def test_html_sanitize_method(self, sanitizer):
        """Test the convenience sanitize_html method."""
        result = sanitizer.sanitize_html("<script>alert(1)</script>Veilige tekst")
        assert "script" not in result.lower()
        assert "Veilige tekst" in result
