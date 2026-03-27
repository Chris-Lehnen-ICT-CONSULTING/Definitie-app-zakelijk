"""Tests for security middleware wiring on FastAPI (DEF-388).

Verifies SecurityHeadersMiddleware is registered and functional.
"""

import pytest
from fastapi.testclient import TestClient

from api.feature_status_api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestSecurityMiddlewareRegistered:
    """Verify the security middleware is wired to the FastAPI app."""

    def test_security_headers_present(self, client):
        """All responses should include security headers."""
        response = client.get("/api/feature-status")
        # Even if the endpoint errors, security headers should be set
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header(self, client):
        response = client.get("/api/feature-status")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_xss_protection_header(self, client):
        response = client.get("/api/feature-status")
        assert "X-XSS-Protection" in response.headers

    def test_security_status_header(self, client):
        """Validated requests should have X-Security-Status: validated."""
        response = client.get("/api/feature-status")
        assert response.headers.get("X-Security-Status") == "validated"


class TestSecurityMiddlewareBlocking:
    """Verify the middleware blocks malicious requests."""

    def test_normal_get_request_passes(self, client):
        """Normal GET requests should pass through."""
        response = client.get("/api/feature-status/summary")
        # May be 200 or 500 (if JSON file missing), but NOT 403
        assert response.status_code != 403
