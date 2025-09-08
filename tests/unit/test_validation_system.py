"""
Comprehensive test suite for validation system.
Tests input validation, sanitization, Dutch text validation, and security middleware.
"""

from unittest.mock import MagicMock, patch

import pytest

# Fix import paths - these modules are in src/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from security.security_middleware import SecurityMiddleware
from validation.dutch_text_validator import DutchTextValidator
from validation.input_validator import InputValidator, ValidationSchema
from validation.sanitizer import ContentSanitizer


class TestInputValidator:
    """Test suite for InputValidator class."""

    def setup_method(self):
        """Setup for each test method."""
        self.validator = InputValidator()

    def test_basic_validation(self):
        """Test basic validation functionality."""
        # Test valid input
        result = self.validator.validate_text("Valid text input")
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Test empty input
        result = self.validator.validate_text("")
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_length_validation(self):
        """Test text length validation."""
        # Test minimum length
        result = self.validator.validate_text("Hi", min_length=5)
        assert result.is_valid is False
        assert any("too short" in error.lower() for error in result.errors)

        # Test maximum length
        long_text = "x" * 1000
        result = self.validator.validate_text(long_text, max_length=100)
        assert result.is_valid is False
        assert any("too long" in error.lower() for error in result.errors)

        # Test valid length
        result = self.validator.validate_text(
            "Valid length", min_length=5, max_length=20
        )
        assert result.is_valid is True

    def test_pattern_validation(self):
        """Test pattern-based validation."""
        # Test email pattern
        result = self.validator.validate_email("test@example.com")
        assert result.is_valid is True

        result = self.validator.validate_email("invalid-email")
        assert result.is_valid is False

        # Test URL pattern
        result = self.validator.validate_url("https://example.com")
        assert result.is_valid is True

        result = self.validator.validate_url("not-a-url")
        assert result.is_valid is False

    def test_dutch_text_validation(self):
        """Test Dutch text specific validation."""
        # Test Dutch text
        dutch_text = "Dit is een Nederlandse tekst met correcte grammatica."
        result = self.validator.validate_dutch_text(dutch_text)
        assert result.is_valid is True

        # Test non-Dutch text
        non_dutch_text = "This is English text."
        result = self.validator.validate_dutch_text(non_dutch_text)
        # Should still be valid but may have warnings
        assert result.is_valid is True

    def test_definition_validation(self):
        """Test definition-specific validation."""
        # Test valid definition
        valid_definition = (
            "Een definitie is een verklaring van de betekenis van een woord of begrip."
        )
        result = self.validator.validate_definition(valid_definition)
        assert result.is_valid is True

        # Test invalid definition (too short)
        invalid_definition = "Kort"
        result = self.validator.validate_definition(invalid_definition)
        assert result.is_valid is False

        # Test definition with forbidden patterns
        forbidden_definition = "Een definitie is... eh... een verklaring."
        result = self.validator.validate_definition(forbidden_definition)
        assert result.is_valid is False

    def test_validation_schema(self):
        """Test ValidationSchema functionality."""
        # Create schema
        schema = ValidationSchema().text().min_length(5).max_length(100).required()

        # Test valid input
        result = schema.validate("Valid text input")
        assert result.is_valid is True

        # Test invalid input
        result = schema.validate("Hi")
        assert result.is_valid is False

        # Test required field
        result = schema.validate("")
        assert result.is_valid is False
        assert any("required" in error.lower() for error in result.errors)

    def test_custom_validators(self):
        """Test custom validation functions."""

        # Create custom validator
        def custom_validator(value):
            if "forbidden" in value.lower():
                return False, "Contains forbidden word"
            return True, None

        # Test custom validator
        result = self.validator.validate_with_custom(
            "This is allowed text", custom_validator
        )
        assert result.is_valid is True

        result = self.validator.validate_with_custom(
            "This contains forbidden word", custom_validator
        )
        assert result.is_valid is False
        assert "forbidden word" in result.errors[0].lower()

    def test_validation_context(self):
        """Test validation with context."""
        context = {"organisation": "DJI", "domain": "Strafrecht", "strict_mode": True}

        # Test context-aware validation
        result = self.validator.validate_with_context(
            "Context-aware validation test", context
        )
        assert result.is_valid is True

        # Test strict mode
        result = self.validator.validate_with_context("Incomplete sentence...", context)
        assert result.is_valid is False


class TestContentSanitizer:
    """Test suite for ContentSanitizer class."""

    def setup_method(self):
        """Setup for each test method."""
        self.sanitizer = ContentSanitizer()

    def test_xss_prevention(self):
        """Test XSS prevention."""
        # Test script tag removal
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = self.sanitizer.sanitize_html(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized

        # Test event handler removal
        malicious_input = "<div onclick=\"alert('xss')\">Click me</div>"
        sanitized = self.sanitizer.sanitize_html(malicious_input)
        assert "onclick" not in sanitized
        assert "Click me" in sanitized

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        # Test SQL injection patterns
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
        ]

        for malicious_input in malicious_inputs:
            sanitized = self.sanitizer.sanitize_sql(malicious_input)
            assert "DROP" not in sanitized.upper()
            assert "UNION" not in sanitized.upper()
            assert "SELECT" not in sanitized.upper()

    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        # Test path traversal patterns
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
        ]

        for malicious_path in malicious_paths:
            sanitized = self.sanitizer.sanitize_path(malicious_path)
            assert "../" not in sanitized
            assert "..\\" not in sanitized
            assert "%2e" not in sanitized

    def test_content_type_sanitization(self):
        """Test content type specific sanitization."""
        # Test HTML content
        html_content = "<p>Valid paragraph</p><script>alert('xss')</script>"
        sanitized = self.sanitizer.sanitize_content(html_content, content_type="html")
        assert "<p>" in sanitized
        assert "<script>" not in sanitized

        # Test text content
        text_content = "Plain text with <tags>"
        sanitized = self.sanitizer.sanitize_content(text_content, content_type="text")
        assert "<tags>" not in sanitized or "&lt;tags&gt;" in sanitized

    def test_dutch_text_sanitization(self):
        """Test Dutch text specific sanitization."""
        # Test Dutch text with special characters
        dutch_text = "Café résumé naïve"
        sanitized = self.sanitizer.sanitize_dutch_text(dutch_text)
        assert "Café" in sanitized
        assert "résumé" in sanitized
        assert "naïve" in sanitized

        # Test Dutch text with forbidden patterns
        forbidden_text = "Dit is een tekst met verboden woorden."
        sanitized = self.sanitizer.sanitize_dutch_text(forbidden_text)
        # Should filter out forbidden words
        assert len(sanitized) <= len(forbidden_text)

    def test_sanitization_levels(self):
        """Test different sanitization levels."""
        test_input = "<p>Hello <b>world</b>!</p><script>alert('xss')</script>"

        # Test strict sanitization
        strict_sanitized = self.sanitizer.sanitize_content(test_input, level="strict")
        assert "<p>" not in strict_sanitized
        assert "<b>" not in strict_sanitized
        assert "<script>" not in strict_sanitized

        # Test moderate sanitization
        moderate_sanitized = self.sanitizer.sanitize_content(
            test_input, level="moderate"
        )
        assert "<p>" in moderate_sanitized
        assert "<b>" in moderate_sanitized
        assert "<script>" not in moderate_sanitized

    def test_whitelist_sanitization(self):
        """Test whitelist-based sanitization."""
        # Define allowed tags
        allowed_tags = ["p", "b", "i", "strong", "em"]

        test_input = (
            "<p>Hello <b>world</b>!</p><script>alert('xss')</script><div>Content</div>"
        )
        sanitized = self.sanitizer.sanitize_with_whitelist(test_input, allowed_tags)

        assert "<p>" in sanitized
        assert "<b>" in sanitized
        assert "<script>" not in sanitized
        assert "<div>" not in sanitized


class TestDutchTextValidator:
    """Test suite for DutchTextValidator class."""

    def setup_method(self):
        """Setup for each test method."""
        self.validator = DutchTextValidator()

    def test_language_detection(self):
        """Test Dutch language detection."""
        # Test Dutch text
        dutch_text = "Dit is een Nederlandse tekst."
        result = self.validator.detect_language(dutch_text)
        assert result.language == "nl"
        assert result.confidence > 0.8

        # Test English text
        english_text = "This is an English text."
        result = self.validator.detect_language(english_text)
        assert result.language == "en"

    def test_readability_scoring(self):
        """Test readability scoring."""
        # Test simple text
        simple_text = "Dit is een korte zin."
        score = self.validator.calculate_readability(simple_text)
        assert score > 0
        assert score <= 100

        # Test complex text
        complex_text = """
        De implementatie van geavanceerde algoritmen voor natuurlijke taalverwerking
        vereist uitgebreide kennis van computationele linguïstiek en machine learning
        methodologieën die geoptimaliseerd zijn voor Nederlandse taalstructuren.
        """
        complex_score = self.validator.calculate_readability(complex_text)
        assert complex_score < score  # Complex text should have lower score

    def test_grammar_validation(self):
        """Test grammar validation."""
        # Test correct grammar
        correct_text = "De kat zit op de mat."
        result = self.validator.validate_grammar(correct_text)
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Test incorrect grammar
        incorrect_text = "De kat zitten op de mat."
        result = self.validator.validate_grammar(incorrect_text)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_spelling_validation(self):
        """Test spelling validation."""
        # Test correct spelling
        correct_text = "Dit is correct gespeld."
        result = self.validator.validate_spelling(correct_text)
        assert result.is_valid is True

        # Test incorrect spelling
        incorrect_text = "Dit is verkeerd gespelt."
        result = self.validator.validate_spelling(incorrect_text)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_government_terminology_validation(self):
        """Test government terminology validation."""
        # Test valid government terminology
        valid_terms = [
            "authenticatie",
            "autorisatie",
            "identiteitsvaststelling",
            "verificatie",
        ]

        for term in valid_terms:
            result = self.validator.validate_government_terminology(term)
            assert result.is_valid is True

        # Test invalid terminology
        invalid_term = "ongeldig_overheids_begrip"
        result = self.validator.validate_government_terminology(invalid_term)
        assert result.is_valid is False

    def test_definition_quality_assessment(self):
        """Test definition quality assessment."""
        # Test high-quality definition
        good_definition = """
        Authenticatie is het proces waarbij de identiteit van een gebruiker,
        apparaat of systeem wordt geverifieerd door middel van het controleren
        van aangeleverde inloggegevens tegen een bekende en vertrouwde bron.
        """
        result = self.validator.assess_definition_quality(good_definition)
        assert result.score > 0.7  # High quality score

        # Test low-quality definition
        poor_definition = "Authenticatie is... eh... iets met inloggen."
        result = self.validator.assess_definition_quality(poor_definition)
        assert result.score < 0.5  # Low quality score

    def test_improvement_suggestions(self):
        """Test improvement suggestions."""
        # Test text that needs improvement
        text = "Dit is een tekst die verbeterd kan worden."
        suggestions = self.validator.get_improvement_suggestions(text)

        assert isinstance(suggestions, list)
        assert len(suggestions) >= 0

        # Each suggestion should have required fields
        for suggestion in suggestions:
            assert "type" in suggestion
            assert "description" in suggestion
            assert "suggestion" in suggestion

    def test_context_aware_validation(self):
        """Test context-aware validation."""
        context = {
            "domain": "strafrecht",
            "organization": "DJI",
            "target_audience": "professionals",
        }

        # Test context-specific validation
        legal_text = "De verdachte heeft het recht op juridische bijstand."
        result = self.validator.validate_with_context(legal_text, context)
        assert result.is_valid is True

        # Test inappropriate context
        informal_text = "Die gast heeft recht op een advocaat ofzo."
        result = self.validator.validate_with_context(informal_text, context)
        assert result.is_valid is False


class TestSecurityMiddleware:
    """Test suite for SecurityMiddleware class."""

    def setup_method(self):
        """Setup for each test method."""
        self.middleware = SecurityMiddleware()

    def test_request_validation(self):
        """Test request validation."""
        # Test valid request
        valid_request = {
            "content": "Valid content",
            "user_id": "user123",
            "ip_address": "192.168.1.1",
        }
        result = self.middleware.validate_request(valid_request)
        assert result.is_valid is True

        # Test invalid request
        invalid_request = {
            "content": '<script>alert("xss")</script>',
            "user_id": "user123",
            "ip_address": "192.168.1.1",
        }
        result = self.middleware.validate_request(invalid_request)
        assert result.is_valid is False

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Test normal request rate
        for i in range(10):
            result = self.middleware.check_rate_limit("192.168.1.1")
            assert result.allowed is True

        # Test excessive request rate
        for i in range(100):
            result = self.middleware.check_rate_limit("192.168.1.1")

        # Should eventually be rate limited
        assert result.allowed is False

    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        # Test normal IP
        result = self.middleware.check_ip_blocked("192.168.1.1")
        assert result.blocked is False

        # Block IP
        self.middleware.block_ip("192.168.1.1", duration=60)

        # Test blocked IP
        result = self.middleware.check_ip_blocked("192.168.1.1")
        assert result.blocked is True

    def test_threat_detection(self):
        """Test threat detection."""
        # Test XSS detection
        xss_content = '<script>alert("xss")</script>'
        result = self.middleware.detect_threats(xss_content)
        assert result.threat_detected is True
        assert "xss" in result.threat_types

        # Test SQL injection detection
        sql_content = "'; DROP TABLE users; --"
        result = self.middleware.detect_threats(sql_content)
        assert result.threat_detected is True
        assert "sql_injection" in result.threat_types

        # Test safe content
        safe_content = "This is safe content"
        result = self.middleware.detect_threats(safe_content)
        assert result.threat_detected is False

    def test_security_headers(self):
        """Test security headers."""
        headers = self.middleware.get_security_headers()

        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"

    def test_audit_logging(self):
        """Test security audit logging."""
        # Mock logger
        with patch("logging.getLogger") as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log

            # Test security event logging
            self.middleware.log_security_event(
                "threat_detected",
                {
                    "ip_address": "192.168.1.1",
                    "threat_type": "xss",
                    "content": '<script>alert("xss")</script>',
                },
            )

            # Verify logging was called
            mock_log.warning.assert_called_once()

    def test_csrf_protection(self):
        """Test CSRF protection."""
        # Generate CSRF token
        token = self.middleware.generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) > 0

        # Validate CSRF token
        result = self.middleware.validate_csrf_token(token)
        assert result.valid is True

        # Test invalid token
        result = self.middleware.validate_csrf_token("invalid_token")
        assert result.valid is False

    def test_content_security_policy(self):
        """Test Content Security Policy."""
        csp = self.middleware.get_csp_header()

        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "'self'" in csp
        assert "'unsafe-inline'" not in csp  # Should be secure


class TestValidationIntegration:
    """Integration tests for validation system."""

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        # Initialize all validators
        input_validator = InputValidator()
        sanitizer = ContentSanitizer()
        dutch_validator = DutchTextValidator()
        security_middleware = SecurityMiddleware()

        # Test input
        test_input = "Dit is een Nederlandse definitie van authenticatie."

        # Step 1: Input validation
        input_result = input_validator.validate_text(test_input)
        assert input_result.is_valid is True

        # Step 2: Content sanitization
        sanitized_input = sanitizer.sanitize_content(test_input, content_type="text")
        assert sanitized_input is not None

        # Step 3: Dutch text validation
        dutch_result = dutch_validator.validate_grammar(sanitized_input)
        assert dutch_result.is_valid is True

        # Step 4: Security validation
        security_result = security_middleware.detect_threats(sanitized_input)
        assert security_result.threat_detected is False

    def test_validation_with_configuration(self):
        """Test validation integration with configuration."""
        from config import get_validation_config

        # Get validation configuration
        validation_config = get_validation_config()

        # Test configuration-based validation
        validator = InputValidator(config=validation_config.config)

        # Test with configuration limits
        limits = validation_config.get_validation_limits()
        max_length = limits["max_text_length"]

        # Test text within limits
        valid_text = "x" * (max_length - 10)
        result = validator.validate_text(valid_text)
        assert result.is_valid is True

        # Test text exceeding limits
        invalid_text = "x" * (max_length + 10)
        result = validator.validate_text(invalid_text)
        assert result.is_valid is False

    def test_validation_error_handling(self):
        """Test validation error handling."""
        validator = InputValidator()

        # Test with None input
        result = validator.validate_text(None)
        assert result.is_valid is False
        assert len(result.errors) > 0

        # Test with empty input
        result = validator.validate_text("")
        assert result.is_valid is False

        # Test with invalid type
        result = validator.validate_text(123)
        assert result.is_valid is False

    def test_validation_performance(self):
        """Test validation performance."""
        import time

        validator = InputValidator()

        # Test performance with large input
        large_input = "Dit is een test. " * 1000

        start_time = time.time()
        result = validator.validate_text(large_input)
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # Less than 5 seconds
        assert (
            result.is_valid is True or result.is_valid is False
        )  # Should return result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
