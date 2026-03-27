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
    """Verify dangerous protocol removal in URL attributes."""

    def test_javascript_protocol_in_href(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="javascript:alert(1)">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "javascript:" not in result.sanitized_value.lower()

    def test_vbscript_protocol_in_href(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="vbscript:msgbox(1)">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "vbscript:" not in result.sanitized_value.lower()

    def test_data_protocol_in_href(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="data:text/html,<script>alert(1)</script>">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "data:" not in result.sanitized_value.lower()

    def test_javascript_protocol_in_src(self, sanitizer):
        result = sanitizer.sanitize(
            '<img src="javascript:alert(1)">',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "javascript:" not in result.sanitized_value.lower()

    def test_data_in_prose_not_stripped(self, sanitizer):
        """data: in normal text should not be removed."""
        result = sanitizer.sanitize(
            "De data: zie bijlage voor meer informatie.",
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "data:" in result.sanitized_value


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


class TestCaseInsensitive:
    """Verify case-insensitive matching (re.IGNORECASE in sanitize engine)."""

    def test_uppercase_onclick(self, sanitizer):
        result = sanitizer.sanitize(
            '<div ONCLICK="alert(1)">test</div>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onclick" not in result.sanitized_value.lower()

    def test_mixed_case_onerror(self, sanitizer):
        result = sanitizer.sanitize(
            '<img src=x OnError="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onerror" not in result.sanitized_value.lower()

    def test_mixed_case_javascript_protocol(self, sanitizer):
        result = sanitizer.sanitize(
            '<a href="JaVaScRiPt:alert(1)">click</a>',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "javascript:" not in result.sanitized_value.lower()


class TestFalsePositivePrevention:
    """Verify non-event attributes starting with 'on' are preserved."""

    def test_ongoing_attribute_preserved(self, sanitizer):
        """MODERATE level: attributes stay, only dangerous ones are removed."""
        result = sanitizer.sanitize(
            '<div ongoing="true">text</div>',
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "ongoing" in result.sanitized_value

    def test_one_attribute_preserved(self, sanitizer):
        """MODERATE level: attributes stay, only dangerous ones are removed."""
        result = sanitizer.sanitize(
            '<div one="1">text</div>',
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "one" in result.sanitized_value

    def test_ontvangen_in_text_preserved(self, sanitizer):
        """Dutch word 'ontvangen' should not be stripped."""
        result = sanitizer.sanitize(
            "Het document is ontvangen door de gemeente.",
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "ontvangen" in result.sanitized_value


class TestSVGVectors:
    """Verify SVG-based XSS vectors are caught."""

    def test_svg_onload(self, sanitizer):
        result = sanitizer.sanitize(
            '<svg onload="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.STRICT,
        )
        assert "onload" not in result.sanitized_value

    def test_svg_animate_onbegin_not_in_allowlist(self, sanitizer):
        """onbegin is not a standard DOM event handler, so it passes through."""
        result = sanitizer.sanitize(
            '<svg><animate onbegin="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "onbegin" in result.sanitized_value


class TestModerateLevel:
    """Verify XSS rules fire at MODERATE level too."""

    def test_onclick_at_moderate(self, sanitizer):
        result = sanitizer.sanitize(
            '<div onclick="alert(1)">test</div>',
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "onclick" not in result.sanitized_value

    def test_event_handler_at_moderate(self, sanitizer):
        """Event handler rules are MODERATE, so they should fire at MODERATE."""
        result = sanitizer.sanitize(
            '<img src=x onerror="alert(1)">',
            ContentType.HTML,
            SanitizationLevel.MODERATE,
        )
        assert "onerror" not in result.sanitized_value


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
