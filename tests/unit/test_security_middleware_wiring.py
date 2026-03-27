"""Tests for security middleware wiring on FastAPI (DEF-388).

Verifies SecurityHeadersMiddleware is registered and functional.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.feature_status_api import app
from security.security_middleware import ValidationResponse


@pytest.fixture
def client():
    return TestClient(app)


class TestSecurityMiddlewareRegistered:
    """Verify the security middleware is wired to the FastAPI app."""

    def test_security_headers_present(self, client):
        """All responses should include security headers."""
        response = client.get("/api/feature-status")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header(self, client):
        response = client.get("/api/feature-status")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_xss_protection_header(self, client):
        response = client.get("/api/feature-status")
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_security_status_header(self, client):
        """Validated requests should have X-Security-Status: validated."""
        response = client.get("/api/feature-status")
        assert response.headers.get("X-Security-Status") == "validated"

    def test_csp_header(self, client):
        response = client.get("/api/feature-status")
        assert "Content-Security-Policy" in response.headers

    def test_hsts_header(self, client):
        response = client.get("/api/feature-status")
        assert "Strict-Transport-Security" in response.headers


class TestSecurityMiddlewareBlocking:
    """Verify the middleware blocks malicious requests."""

    def test_normal_get_request_passes(self, client):
        """Normal GET requests should pass through."""
        response = client.get("/api/feature-status/summary")
        # May be 200 or 500 (if JSON file missing), but NOT 403
        assert response.status_code != 403

    def test_blocked_request_returns_403(self, client):
        """When SecurityMiddleware rejects a request, middleware returns 403."""
        blocked_response = ValidationResponse(
            allowed=False,
            sanitized_data={},
            threats_detected=[],
            security_events=[],
            sanitization_changes=[],
            validation_errors=["Test block"],
            response_headers={"X-Security-Status": "blocked"},
        )
        with patch("api.feature_status_api.get_security_middleware") as mock_factory:
            mock_mw = mock_factory.return_value
            mock_mw.validate_request = AsyncMock(return_value=blocked_response)
            response = client.get("/api/feature-status")

        assert response.status_code == 403
        assert response.json()["detail"] == "Request blocked by security policy"
        assert response.headers.get("X-Security-Status") == "blocked"
