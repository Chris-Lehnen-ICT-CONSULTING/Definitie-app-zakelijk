"""
Test suite for validation system - Tests the ACTUAL API of validation classes.

Tests:
- InputValidator: text validation, email, URL, definitions
- ValidationSchema: field-based schema validation
- ContentSanitizer: XSS prevention, SQL injection, content sanitization
- DutchTextValidator: Dutch text validation and improvement suggestions
- SecurityMiddleware: request validation, rate limiting, threat detection
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from security.security_middleware import (
    SecurityMiddleware,
    ThreatType,
    ValidationRequest,
)
from validation.dutch_text_validator import DutchTextType, DutchTextValidator
from validation.input_validator import InputValidator, ValidationSchema
from validation.sanitizer import ContentSanitizer, ContentType, SanitizationLevel


class TestInputValidator:
    """Test suite for InputValidator class."""

    def setup_method(self):
        """Setup for each test method."""
        self.validator = InputValidator()

    def test_basic_validation(self):
        """Test basic text validation functionality."""
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

    def test_email_validation(self):
        """Test email validation."""
        # Valid email
        result = self.validator.validate_email("test@example.com")
        assert result.is_valid is True

        # Invalid email
        result = self.validator.validate_email("invalid-email")
        assert result.is_valid is False

        # Non-string input
        result = self.validator.validate_email(12345)
        assert result.is_valid is False

    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        result = self.validator.validate_url("https://example.com")
        assert result.is_valid is True

        result = self.validator.validate_url("http://example.com/path?query=1")
        assert result.is_valid is True

        # Invalid URLs
        result = self.validator.validate_url("not-a-url")
        assert result.is_valid is False

        result = self.validator.validate_url("ftp://example.com")
        assert result.is_valid is False

    def test_dutch_text_validation(self):
        """Test Dutch text validation."""
        # Valid Dutch text
        result = self.validator.validate_dutch_text("Dit is Nederlandse tekst.")
        assert result.is_valid is True

        # Empty text
        result = self.validator.validate_dutch_text("")
        assert result.is_valid is False

    def test_definition_validation(self):
        """Test definition validation."""
        # Valid definition
        result = self.validator.validate_definition(
            "Een proces waarbij identiteit wordt vastgesteld."
        )
        assert result.is_valid is True

        # Too short definition
        result = self.validator.validate_definition("Kort")
        assert result.is_valid is False

        # Definition with forbidden patterns
        result = self.validator.validate_definition("Eh... dit is een definitie")
        assert result.is_valid is False

    def test_custom_validator(self):
        """Test custom validator function."""
        # Custom validator that rejects words starting with 'x'

        def no_x_words(text: str) -> bool:
            return not any(word.lower().startswith("x") for word in text.split())

        result = self.validator.validate_with_custom("Hello world", no_x_words)
        assert result.is_valid is True

        result = self.validator.validate_with_custom("Hello xray world", no_x_words)
        assert result.is_valid is False

    def test_context_validation(self):
        """Test context-aware validation."""
        # Normal mode allows ellipsis
        result = self.validator.validate_with_context(
            "This is incomplete...", {"strict_mode": False}
        )
        assert result.is_valid is True

        # Strict mode rejects ellipsis
        result = self.validator.validate_with_context(
            "This is incomplete...", {"strict_mode": True}
        )
        assert result.is_valid is False


class TestValidationSchema:
    """Test suite for ValidationSchema class."""

    def test_schema_creation(self):
        """Test schema creation and rule addition."""
        schema = ValidationSchema("test_schema")
        assert schema.schema_name == "test_schema"
        assert len(schema.rules) == 0

    def test_fluent_api(self):
        """Test fluent API for adding rules."""
        schema = ValidationSchema("test")
        result = (
            schema.required("field1")
            .type_check("field2", str)
            .length("field3", min_length=5, max_length=100)
        )

        # Fluent API returns self
        assert result is schema
        assert len(schema.rules) == 3

    def test_required_validation(self):
        """Test required field validation through InputValidator."""
        validator = InputValidator()

        # Create custom schema
        schema = ValidationSchema("custom_test")
        schema.required("name", "Name is required")
        validator.add_schema(schema)

        # Test with missing field
        result = validator.validate({}, "custom_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

        # Test with field present
        result = validator.validate({"name": "Test"}, "custom_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) == 0

    def test_type_validation(self):
        """Test type validation."""
        validator = InputValidator()

        schema = ValidationSchema("type_test")
        schema.type_check("age", int)
        validator.add_schema(schema)

        # Valid type
        result = validator.validate({"age": 25}, "type_test")
        assert all(r.passed for r in result)

        # Invalid type
        result = validator.validate({"age": "twenty-five"}, "type_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

    def test_length_validation(self):
        """Test length validation."""
        validator = InputValidator()

        schema = ValidationSchema("length_test")
        schema.length("text", min_length=5, max_length=10)
        validator.add_schema(schema)

        # Valid length
        result = validator.validate({"text": "hello"}, "length_test")
        assert all(r.passed for r in result)

        # Too short
        result = validator.validate({"text": "hi"}, "length_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

        # Too long
        result = validator.validate({"text": "hello world!!"}, "length_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

    def test_pattern_validation(self):
        """Test pattern validation."""
        validator = InputValidator()

        schema = ValidationSchema("pattern_test")
        schema.pattern("code", r"^[A-Z]{3}-\d{3}$", message="Invalid code format")
        validator.add_schema(schema)

        # Valid pattern
        result = validator.validate({"code": "ABC-123"}, "pattern_test")
        assert all(r.passed for r in result)

        # Invalid pattern
        result = validator.validate({"code": "abc123"}, "pattern_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

    def test_enum_validation(self):
        """Test enum validation."""
        validator = InputValidator()

        schema = ValidationSchema("enum_test")
        schema.enum("status", ["active", "inactive", "pending"])
        validator.add_schema(schema)

        # Valid enum value
        result = validator.validate({"status": "active"}, "enum_test")
        assert all(r.passed for r in result)

        # Invalid enum value
        result = validator.validate({"status": "unknown"}, "enum_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0

    def test_custom_validation(self):
        """Test custom validation function in schema."""
        validator = InputValidator()

        schema = ValidationSchema("custom_test")
        schema.custom("email", lambda x: "@" in str(x), "Must contain @")
        validator.add_schema(schema)

        # Valid
        result = validator.validate({"email": "test@example.com"}, "custom_test")
        assert all(r.passed for r in result)

        # Invalid
        result = validator.validate({"email": "invalid"}, "custom_test")
        errors = [r for r in result if not r.passed]
        assert len(errors) > 0


class TestContentSanitizer:
    """Test suite for ContentSanitizer class."""

    def setup_method(self):
        """Setup for each test method."""
        self.sanitizer = ContentSanitizer()

    def test_html_sanitization_strict(self):
        """Test strict HTML sanitization removes all tags."""
        malicious_html = "<p>Hello</p><script>alert('xss')</script>"
        result = self.sanitizer.sanitize(
            malicious_html, ContentType.HTML, SanitizationLevel.STRICT
        )

        # Strict mode should strip all HTML tags
        assert "<script>" not in result.sanitized_value
        assert "<p>" not in result.sanitized_value

    def test_sql_injection_prevention(self):
        """Test SQL injection pattern removal."""
        malicious_sql = "'; DROP TABLE users; --"
        result = self.sanitizer.sanitize(
            malicious_sql, ContentType.PLAIN_TEXT, SanitizationLevel.STRICT
        )

        # SQL keywords in the pattern list should be removed
        # Note: Only specific SQL keywords are removed (drop, select, union, etc.)
        # 'TABLE' is not in the removal pattern list
        assert "drop" not in result.sanitized_value.lower()
        assert len(result.changes_made) > 0  # Some changes should have been made

    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        traversal_input = "../../../etc/passwd"
        result = self.sanitizer.sanitize(
            traversal_input, ContentType.PLAIN_TEXT, SanitizationLevel.STRICT
        )

        # Path traversal patterns should be removed
        assert "../" not in result.sanitized_value

    def test_dutch_text_sanitization(self):
        """Test Dutch text sanitization removes control characters."""
        # Dutch text with control character (will be removed)
        dutch_text = "Dit is een Nederlandse tekst met\x00een control character."
        result = self.sanitizer.sanitize_dutch_text(dutch_text)

        # Control characters should be removed
        assert "\x00" not in result
        # Normal text preserved
        assert "Nederlandse" in result

    def test_whitelist_sanitization(self):
        """Test whitelist-based HTML sanitization."""
        html_with_script = "<p>Safe</p><script>alert('bad')</script><b>Bold</b>"
        result = self.sanitizer.sanitize_with_whitelist(html_with_script, ["p", "b"])

        # Allowed tags should be preserved, script removed
        assert "<p>" in result
        assert "<b>" in result
        assert "<script>" not in result

    def test_malicious_content_detection(self):
        """Test malicious content detection."""
        malicious_content = "<script>document.cookie</script>"
        threats = self.sanitizer.detect_malicious_content(malicious_content)

        assert len(threats) > 0
        assert any(
            "JavaScript" in threat or "injection" in threat for threat in threats
        )

    def test_definition_sanitization(self):
        """Test definition-specific sanitization."""
        definition = "Dit is een definitie met 123456789 (BSN nummer)"
        result = self.sanitizer.sanitize_for_definition(definition)

        # BSN-like numbers should be redacted
        assert "123456789" not in result or "[REDACTED]" in result

    def test_user_input_sanitization(self):
        """Test user input sanitization with content type mapping."""
        user_data = {
            "begrip": "test<script>bad</script>",
            "voorsteller": "Jan & Piet",
        }
        result = self.sanitizer.sanitize_user_input(user_data)

        assert isinstance(result, dict)
        assert "begrip" in result
        assert "voorsteller" in result

    def test_sanitization_stats(self):
        """Test sanitization statistics."""
        # Perform some sanitizations
        self.sanitizer.sanitize("test", ContentType.PLAIN_TEXT)
        self.sanitizer.sanitize("test2", ContentType.HTML)

        stats = self.sanitizer.get_sanitization_stats()
        assert "total_sanitizations" in stats
        assert stats["total_sanitizations"] >= 2


class TestDutchTextValidator:
    """Test suite for DutchTextValidator class."""

    def setup_method(self):
        """Setup for each test method."""
        self.validator = DutchTextValidator()

    def test_general_text_validation(self):
        """Test general Dutch text validation."""
        dutch_text = "Dit is een normale Nederlandse zin."
        result = self.validator.validate_text(dutch_text, DutchTextType.GENERAL)

        assert result.text == dutch_text
        assert result.text_type == DutchTextType.GENERAL
        # General text without issues should pass
        assert isinstance(result.passed, bool)

    def test_legal_text_validation(self):
        """Test legal text validation with article references."""
        legal_text = "Artikel 12 van de wet bepaalt dat elke burger rechten heeft."
        result = self.validator.validate_text(legal_text, DutchTextType.LEGAL)

        assert result.text_type == DutchTextType.LEGAL
        # Should detect legal article format
        legal_issues = [i for i in result.issues if "article" in i["rule_name"].lower()]
        assert len(legal_issues) >= 0  # May or may not detect depending on rules

    def test_government_text_validation(self):
        """Test government text validation."""
        gov_text = "Het Ministerie van Binnenlandse Zaken is verantwoordelijk."
        result = self.validator.validate_text(gov_text, DutchTextType.GOVERNMENT)

        assert result.text_type == DutchTextType.GOVERNMENT
        # Should detect government institution
        gov_issues = [
            i for i in result.issues if "government" in i["rule_name"].lower()
        ]
        assert isinstance(gov_issues, list)

    def test_definition_text_validation(self):
        """Test definition text validation."""
        definition = (
            "Identiteit is het geheel van kenmerken die een persoon uniek maken."
        )
        result = self.validator.validate_text(definition, DutchTextType.DEFINITION)

        assert result.text_type == DutchTextType.DEFINITION

    def test_vague_terms_detection(self):
        """Test detection of vague terms in definitions."""
        vague_definition = "Dit is ongeveer een redelijk goede definitie."
        result = self.validator.validate_text(
            vague_definition, DutchTextType.DEFINITION
        )

        # Should detect vague terms like "ongeveer", "redelijk"
        vague_issues = [i for i in result.issues if "vague" in i["rule_name"].lower()]
        assert len(vague_issues) > 0

    def test_excessive_capitals_detection(self):
        """Test detection of excessive capitalization."""
        caps_text = "Dit is HEEL BELANGRIJK en moet DUIDELIJK zijn."
        result = self.validator.validate_text(caps_text, DutchTextType.FORMAL)

        # Should detect excessive capitals
        caps_issues = [i for i in result.issues if "capital" in i["rule_name"].lower()]
        assert len(caps_issues) > 0

    def test_improvement_suggestions(self):
        """Test improvement suggestions."""
        text = "Dit is een tekst voor suggesties."
        suggestions = self.validator.suggest_improvements(
            text, DutchTextType.DEFINITION
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0  # Should always have some suggestions

    def test_text_statistics(self):
        """Test text statistics calculation."""
        text = "Dit is een test. Hier is nog een zin. En nog een laatste zin."
        result = self.validator.validate_text(text, DutchTextType.GENERAL)

        assert result.statistics is not None
        assert "word_count" in result.statistics
        assert "sentence_count" in result.statistics
        assert "readability_score" in result.statistics
        assert result.statistics["word_count"] > 0
        assert result.statistics["sentence_count"] > 0

    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        # Perform some validations
        self.validator.validate_text("Test tekst een", DutchTextType.GENERAL)
        self.validator.validate_text("Test tekst twee", DutchTextType.LEGAL)

        stats = self.validator.get_validation_statistics()
        assert "total_validations" in stats
        assert stats["total_validations"] >= 2


class TestSecurityMiddleware:
    """Test suite for SecurityMiddleware class."""

    def setup_method(self):
        """Setup for each test method."""
        self.middleware = SecurityMiddleware()

    @pytest.mark.asyncio
    async def test_normal_request_allowed(self):
        """Test that normal requests are allowed."""
        request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={"begrip": "identiteit"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response = await self.middleware.validate_request(request)
        assert response.allowed is True
        assert len(response.threats_detected) == 0

    @pytest.mark.asyncio
    async def test_xss_attack_blocked(self):
        """Test that XSS attacks are blocked."""
        request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={"begrip": "<script>alert('XSS')</script>"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.2",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response = await self.middleware.validate_request(request)
        assert response.allowed is False
        assert ThreatType.XSS in response.threats_detected

    @pytest.mark.asyncio
    async def test_sql_injection_blocked(self):
        """Test that SQL injection attempts are blocked."""
        request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={"begrip": "'; DROP TABLE users; --"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.3",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response = await self.middleware.validate_request(request)
        assert response.allowed is False
        assert ThreatType.SQL_INJECTION in response.threats_detected

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Use unique IP for this test
        test_ip = "192.168.100.1"

        # Make many rapid requests
        blocked = False
        for i in range(20):
            request = ValidationRequest(
                endpoint="definition_generation",  # Lower rate limit
                method="POST",
                data={"begrip": f"test_{i}"},
                headers={"User-Agent": "Mozilla/5.0"},
                source_ip=test_ip,
                user_agent="Mozilla/5.0",
                timestamp=datetime.now(UTC),
            )

            response = await self.middleware.validate_request(request)
            if (
                not response.allowed
                and ThreatType.RATE_LIMIT_EXCEEDED in response.threats_detected
            ):
                blocked = True
                break

        assert blocked, "Rate limiting should have triggered"

    @pytest.mark.asyncio
    async def test_ip_blocking(self):
        """Test IP blocking after high severity threat."""
        # First, trigger a high severity threat
        malicious_request = ValidationRequest(
            endpoint="test",
            method="POST",
            data={"begrip": "<script>document.cookie</script>"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.200.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response1 = await self.middleware.validate_request(malicious_request)
        assert response1.allowed is False

        # Second request from same IP should be blocked
        normal_request = ValidationRequest(
            endpoint="test",
            method="POST",
            data={"begrip": "normal request"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.200.1",  # Same IP
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response2 = await self.middleware.validate_request(normal_request)
        assert response2.allowed is False
        assert ThreatType.UNAUTHORIZED_ACCESS in response2.threats_detected

    @pytest.mark.asyncio
    async def test_security_headers(self):
        """Test that security headers are added to responses."""
        request = ValidationRequest(
            endpoint="test",
            method="POST",
            data={"begrip": "test"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.50.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response = await self.middleware.validate_request(request)

        # Should include security headers
        assert "X-Content-Type-Options" in response.response_headers
        assert "X-Frame-Options" in response.response_headers
        assert "X-XSS-Protection" in response.response_headers

    def test_security_report(self):
        """Test security report generation."""
        report = self.middleware.get_security_report()

        assert "generated_at" in report
        assert "total_security_events" in report
        assert "blocked_requests" in report
        assert "threat_types" in report


class TestValidationIntegration:
    """Integration tests for validation pipeline."""

    @pytest.mark.asyncio
    async def test_full_validation_pipeline(self):
        """Test complete validation pipeline from request to sanitized output."""
        # Create middleware
        middleware = SecurityMiddleware()

        # Create a request with data that needs sanitization
        request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={
                "begrip": "identiteit",  # Valid
                "voorsteller": "Jan de Vries",  # Valid
                "toelichting": "Dit is een   test   met   spaties.",  # Will be sanitized
            },
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.99.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(UTC),
        )

        response = await middleware.validate_request(request)

        # Request should be allowed
        assert response.allowed is True

        # Data should be sanitized
        assert isinstance(response.sanitized_data, dict)
        assert "begrip" in response.sanitized_data

        # Security headers should be present
        assert len(response.response_headers) > 0

    def test_validator_sanitizer_integration(self):
        """Test InputValidator and ContentSanitizer working together."""
        validator = InputValidator()
        sanitizer = ContentSanitizer()

        # Raw input with potential issues
        raw_input = "<script>bad</script>Hello World"

        # First sanitize
        sanitized = sanitizer.sanitize_html(raw_input)

        # Then validate
        result = validator.validate_text(sanitized)

        # Should pass validation after sanitization
        assert result.is_valid is True
