"""
Comprehensive tests for the validation and sanitization system.
Tests input validation, sanitization, Dutch text validation, and security middleware.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any

from validation.input_validator import (
    get_validator, ValidationSeverity, ValidationType, ValidationSchema
)
from validation.sanitizer import (
    get_sanitizer, SanitizationLevel, ContentType
)
from validation.dutch_text_validator import (
    get_dutch_validator, DutchTextType
)
from security.security_middleware import (
    get_security_middleware, ValidationRequest, ThreatType
)


class TestInputValidator:
    """Test suite for input validation system."""
    
    def test_definition_generation_validation(self):
        """Test validation of definition generation input."""
        validator = get_validator()
        
        # Valid data
        valid_data = {
            "begrip": "identiteitsbehandeling",
            "context_dict": {
                "organisatorisch": ["Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        }
        
        results = validator.validate(valid_data, "definition_generation")
        assert all(r.passed for r in results)
        
        # Invalid data - empty term
        invalid_data = {
            "begrip": "",
            "context_dict": {
                "organisatorisch": ["Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        }
        
        results = validator.validate(invalid_data, "definition_generation")
        errors = [r for r in results if not r.passed and r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0
    
    def test_user_input_validation(self):
        """Test validation of user input."""
        validator = get_validator()
        
        # Valid user input
        valid_input = {
            "voorsteller": "Jan de Vries",
            "datum": "2025-07-09",
            "ketenpartners": ["Openbaar Ministerie", "Politie"]
        }
        
        results = validator.validate(valid_input, "user_input")
        assert all(r.passed for r in results)
        
        # Invalid user input - invalid date format
        invalid_input = {
            "voorsteller": "Jan de Vries",
            "datum": "09-07-2025",  # Wrong format
            "ketenpartners": ["Openbaar Ministerie", "Politie"]
        }
        
        results = validator.validate(invalid_input, "user_input")
        errors = [r for r in results if not r.passed and r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0
    
    def test_custom_validation_schema(self):
        """Test custom validation schema creation."""
        validator = get_validator()
        
        # Create custom schema
        custom_schema = ValidationSchema("custom_test")
        custom_schema.required("test_field", "Test field is required") \
                     .type_check("test_field", str) \
                     .length("test_field", min_length=5, max_length=50)
        
        validator.add_schema(custom_schema)
        
        # Test with valid data
        valid_data = {"test_field": "Valid test string"}
        results = validator.validate(valid_data, "custom_test")
        assert all(r.passed for r in results)
        
        # Test with invalid data
        invalid_data = {"test_field": "bad"}  # Too short
        results = validator.validate(invalid_data, "custom_test")
        errors = [r for r in results if not r.passed and r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0
    
    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        validator = get_validator()
        
        # Perform several validations
        test_data = {"begrip": "test"}
        for _ in range(5):
            validator.validate(test_data, "definition_generation")
        
        stats = validator.get_validation_stats()
        assert stats['total_validations'] >= 5
        assert 'success_rate' in stats
        assert 'schema_usage' in stats


class TestContentSanitizer:
    """Test suite for content sanitization system."""
    
    def test_xss_sanitization(self):
        """Test XSS attack sanitization."""
        sanitizer = get_sanitizer()
        
        malicious_text = "<script>alert('XSS')</script>Hello World"
        result = sanitizer.sanitize(malicious_text, ContentType.HTML, SanitizationLevel.STRICT)
        
        assert "<script>" not in result.sanitized_value
        assert "alert" not in result.sanitized_value
        assert len(result.changes_made) > 0
    
    def test_sql_injection_sanitization(self):
        """Test SQL injection sanitization."""
        sanitizer = get_sanitizer()
        
        malicious_text = "'; DROP TABLE users; --"
        result = sanitizer.sanitize(malicious_text, ContentType.PLAIN_TEXT, SanitizationLevel.STRICT)
        
        assert "DROP TABLE" not in result.sanitized_value
        assert "--" not in result.sanitized_value
        assert len(result.changes_made) > 0
    
    def test_dutch_text_sanitization(self):
        """Test Dutch text specific sanitization."""
        sanitizer = get_sanitizer()
        
        dutch_text = "Dit is een Nederlandse tekst met kut woorden"
        result = sanitizer.sanitize(dutch_text, ContentType.DUTCH_TEXT, SanitizationLevel.STRICT)
        
        assert "[FILTERED]" in result.sanitized_value
        assert len(result.changes_made) > 0
    
    def test_user_input_sanitization(self):
        """Test comprehensive user input sanitization."""
        sanitizer = get_sanitizer()
        
        user_data = {
            'begrip': 'test<script>alert(1)</script>',
            'voorsteller': 'Jan & Piet',
            'definitie_origineel': 'Een proces waarbij <iframe>bad</iframe> wordt gebruikt'
        }
        
        sanitized_data = sanitizer.sanitize_user_input(user_data)
        
        assert "<script>" not in sanitized_data['begrip']
        assert "<iframe>" not in sanitized_data['definitie_origineel']
        assert "&" in sanitized_data['voorsteller']  # Should be preserved in names
    
    def test_threat_detection(self):
        """Test malicious content detection."""
        sanitizer = get_sanitizer()
        
        malicious_content = "<script>document.cookie</script>"
        threats = sanitizer.detect_malicious_content(malicious_content)
        
        assert len(threats) > 0
        assert any("JavaScript" in threat for threat in threats)
    
    def test_sanitization_statistics(self):
        """Test sanitization statistics tracking."""
        sanitizer = get_sanitizer()
        
        # Perform several sanitizations
        test_texts = [
            "<script>alert('test')</script>",
            "Normal text",
            "'; DROP TABLE users; --",
            "Another normal text"
        ]
        
        for text in test_texts:
            sanitizer.sanitize(text, ContentType.PLAIN_TEXT, SanitizationLevel.STRICT)
        
        stats = sanitizer.get_sanitization_stats()
        assert stats['total_sanitizations'] >= 4
        assert 'total_changes' in stats
        assert 'content_type_usage' in stats


class TestDutchTextValidator:
    """Test suite for Dutch text validation system."""
    
    def test_general_dutch_validation(self):
        """Test general Dutch text validation."""
        validator = get_dutch_validator()
        
        # Valid Dutch text
        valid_text = "Dit is een Nederlandse tekst voor identiteitsbehandeling."
        result = validator.validate_text(valid_text, DutchTextType.GENERAL)
        
        assert result.passed
        assert result.text_type == DutchTextType.GENERAL
        assert result.statistics is not None
    
    def test_legal_text_validation(self):
        """Test legal text validation."""
        validator = get_dutch_validator()
        
        # Legal text with proper structure
        legal_text = "Artikel 12 van de Wet op de identificatieplicht bepaalt dat elke burger een geldig identiteitsbewijs moet kunnen tonen."
        result = validator.validate_text(legal_text, DutchTextType.LEGAL)
        
        # Should pass but may have informational issues
        assert result.passed or all(issue['severity'] in ['info', 'warning'] for issue in result.issues)
    
    def test_definition_validation(self):
        """Test definition text validation."""
        validator = get_dutch_validator()
        
        # Well-formed definition
        definition_text = "Identiteitsbehandeling is het proces waarbij de identiteit van een persoon wordt vastgesteld."
        result = validator.validate_text(definition_text, DutchTextType.DEFINITION)
        
        assert result.passed or all(issue['severity'] in ['info', 'warning'] for issue in result.issues)
    
    def test_problematic_text_detection(self):
        """Test detection of problematic Dutch text."""
        validator = get_dutch_validator()
        
        # Text with multiple issues
        problematic_text = "DIT IS EEN ZEER SLECHTE TEKST DIE VEEL TE LANG IS EN EIGENLIJK OPGEDEELD ZOU MOETEN WORDEN!!!"
        result = validator.validate_text(problematic_text, DutchTextType.FORMAL)
        
        # Should detect excessive capitals and multiple punctuation
        assert len(result.issues) > 0
        assert any("capital" in issue['description'].lower() for issue in result.issues)
    
    def test_readability_calculation(self):
        """Test readability score calculation."""
        validator = get_dutch_validator()
        
        # Simple text should have higher readability
        simple_text = "Dit is een korte en duidelijke zin."
        result = validator.validate_text(simple_text, DutchTextType.GENERAL)
        
        # Complex text should have lower readability
        complex_text = "De implementatie van een geïntegreerd identiteitsmanagementsysteem vereist een uitgebreide evaluatie van de bestaande infrastructuur en de ontwikkeling van nieuwe beveiligingsprotocollen."
        complex_result = validator.validate_text(complex_text, DutchTextType.TECHNICAL)
        
        assert result.statistics['readability_score'] > complex_result.statistics['readability_score']
    
    def test_improvement_suggestions(self):
        """Test improvement suggestions generation."""
        validator = get_dutch_validator()
        
        # Text that needs improvement
        text = "Dit is een tekst die verbeterd kan worden voor definities."
        suggestions = validator.suggest_improvements(text, DutchTextType.DEFINITION)
        
        assert len(suggestions) > 0
        assert any("definition" in suggestion.lower() for suggestion in suggestions)


class TestSecurityMiddleware:
    """Test suite for security middleware system."""
    
    async def test_normal_request_validation(self):
        """Test validation of normal requests."""
        middleware = get_security_middleware()
        
        normal_request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={
                "begrip": "identiteitsbehandeling",
                "context_dict": {
                    "organisatorisch": ["Strafrechtketen"],
                    "juridisch": ["Strafrecht"],
                    "wettelijk": ["Wetboek van Strafrecht"]
                }
            },
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        response = await middleware.validate_request(normal_request)
        assert response.allowed
        assert len(response.threats_detected) == 0
    
    async def test_malicious_request_detection(self):
        """Test detection of malicious requests."""
        middleware = get_security_middleware()
        
        malicious_request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data={
                "begrip": "<script>alert('XSS')</script>",
                "context_dict": {
                    "organisatorisch": ["'; DROP TABLE users; --"],
                    "juridisch": ["Strafrecht"],
                    "wettelijk": ["Wetboek van Strafrecht"]
                }
            },
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.2",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        response = await middleware.validate_request(malicious_request)
        assert not response.allowed
        assert len(response.threats_detected) > 0
        assert ThreatType.XSS in response.threats_detected or ThreatType.SQL_INJECTION in response.threats_detected
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        middleware = get_security_middleware()
        
        # Send multiple requests rapidly
        for i in range(15):
            test_request = ValidationRequest(
                endpoint="definition_generation",
                method="POST",
                data={"begrip": f"test_{i}"},
                headers={"User-Agent": "Mozilla/5.0"},
                source_ip="192.168.1.3",
                user_agent="Mozilla/5.0",
                timestamp=datetime.now()
            )
            
            response = await middleware.validate_request(test_request)
            if not response.allowed and ThreatType.RATE_LIMIT_EXCEEDED in response.threats_detected:
                assert i > 0  # Should trigger after some requests
                break
    
    async def test_security_reporting(self):
        """Test security reporting functionality."""
        middleware = get_security_middleware()
        
        # Generate some security events
        malicious_request = ValidationRequest(
            endpoint="test",
            method="POST",
            data={"test": "<script>alert('test')</script>"},
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.4",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        await middleware.validate_request(malicious_request)
        
        # Get security report
        report = middleware.get_security_report()
        
        assert 'total_security_events' in report
        assert 'blocked_requests' in report
        assert 'threat_types' in report
        assert report['total_security_events'] > 0


class TestIntegratedValidation:
    """Test suite for integrated validation system."""
    
    async def test_full_validation_pipeline(self):
        """Test complete validation pipeline integration."""
        validator = get_validator()
        sanitizer = get_sanitizer()
        dutch_validator = get_dutch_validator()
        security_middleware = get_security_middleware()
        
        # Test data that goes through entire pipeline
        test_data = {
            "begrip": "identiteitsbehandeling",
            "definitie_origineel": "Identiteitsbehandeling is het proces waarbij de identiteit van een persoon wordt vastgesteld, geverifieerd en gevalideerd door middel van verschillende technieken en procedures.",
            "context_dict": {
                "organisatorisch": ["Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        }
        
        # Step 1: Security validation
        security_request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data=test_data,
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.5",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        security_response = await security_middleware.validate_request(security_request)
        assert security_response.allowed
        
        # Step 2: Input validation
        validation_results = validator.validate(security_response.sanitized_data, "definition_generation")
        assert all(r.passed or r.severity in [ValidationSeverity.INFO, ValidationSeverity.WARNING] for r in validation_results)
        
        # Step 3: Dutch text validation
        dutch_result = dutch_validator.validate_text(
            test_data["definitie_origineel"], 
            DutchTextType.DEFINITION
        )
        assert dutch_result.passed or all(issue['severity'] in ['info', 'warning'] for issue in dutch_result.issues)
        
        # Step 4: Additional sanitization
        final_sanitized = sanitizer.sanitize_user_input(test_data)
        assert final_sanitized["begrip"] == test_data["begrip"]  # Should be unchanged for clean data
    
    async def test_malicious_input_handling(self):
        """Test handling of malicious input through entire pipeline."""
        security_middleware = get_security_middleware()
        
        # Malicious test data
        malicious_data = {
            "begrip": "<script>alert('XSS')</script>identiteit",
            "definitie_origineel": "'; DROP TABLE definitions; -- Een definitie",
            "context_dict": {
                "organisatorisch": ["<iframe src='evil.com'></iframe>Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"]
            }
        }
        
        # Security validation should block this
        security_request = ValidationRequest(
            endpoint="definition_generation",
            method="POST",
            data=malicious_data,
            headers={"User-Agent": "Mozilla/5.0"},
            source_ip="192.168.1.6",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now()
        )
        
        security_response = await security_middleware.validate_request(security_request)
        assert not security_response.allowed
        assert len(security_response.threats_detected) > 0
        assert len(security_response.security_events) > 0


# Test runner
async def run_validation_tests():
    """Run all validation system tests."""
    print("🧪 Testing Validation System")
    print("=" * 30)
    
    test_classes = [
        TestInputValidator,
        TestContentSanitizer,
        TestDutchTextValidator,
        TestSecurityMiddleware,
        TestIntegratedValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")
        
        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                # Create test instance
                test_instance = test_class()
                
                # Run test method
                test_method = getattr(test_instance, method_name)
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {str(e)}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All validation tests passed!")
    else:
        print("⚠️ Some tests failed - check implementation")


if __name__ == "__main__":
    asyncio.run(run_validation_tests())
