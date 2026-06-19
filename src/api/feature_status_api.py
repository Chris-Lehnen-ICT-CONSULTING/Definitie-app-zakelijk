"""
Feature Status API voor real-time dashboard updates
"""

import json
import logging
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from security.security_middleware import (
    ValidationRequest,
    get_security_middleware,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Feature Status API")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that wires SecurityMiddleware into the request pipeline.

    Validates requests via SecurityMiddleware.validate_request() and
    adds security headers to all responses.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        security = get_security_middleware()

        # Build ValidationRequest from FastAPI request
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        body_data: dict[str, Any] = {}
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                body_data = json.loads(body_bytes) if body_bytes else {}
            except (json.JSONDecodeError, ValueError):
                body_data = {}

        validation_request = ValidationRequest(
            endpoint=request.url.path,
            method=request.method,
            data=body_data,
            headers=dict(request.headers),
            source_ip=client_ip,
            user_agent=user_agent,
            timestamp=datetime.now(UTC),
        )

        validation_response = await security.validate_request(validation_request)

        if not validation_response.allowed:
            logger.warning(
                "Security middleware blocked request: %s %s from %s — %s",
                request.method,
                request.url.path,
                client_ip,
                "; ".join(validation_response.validation_errors),
            )
            return Response(
                content=json.dumps({"detail": "Request blocked by security policy"}),
                status_code=403,
                media_type="application/json",
                headers=validation_response.response_headers,
            )

        response = await call_next(request)

        # Add security headers to all responses
        for header, value in validation_response.response_headers.items():
            response.headers[header] = value

        return response


# Security middleware (must be added before CORS so it runs after CORS)
app.add_middleware(SecurityHeadersMiddleware)

# CORS voor browser toegang
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Cache voor performance
_feature_cache = None
_cache_timestamp = None
CACHE_DURATION = 300  # 5 minuten


@app.get("/api/feature-status")
async def get_feature_status() -> dict[str, Any]:
    """Get current feature status from GitHub or cache"""
    global _feature_cache, _cache_timestamp

    # Check cache
    if _feature_cache and _cache_timestamp:
        cache_age = (datetime.now(UTC) - _cache_timestamp).seconds
        if cache_age < CACHE_DURATION:
            return cast(dict[str, Any], _feature_cache)

    # Load from JSON file (or fetch from GitHub)
    try:
        json_path = (
            Path(__file__).parent.parent.parent
            / "docs"
            / "architectuur"
            / "feature-status.json"
        )
        with open(json_path) as f:
            data: dict[str, Any] = json.load(f)

        # Update cache
        _feature_cache = data
        _cache_timestamp = datetime.now(UTC)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/feature-status/summary")
async def get_feature_summary() -> dict[str, Any]:
    """Get summary statistics only"""
    data = await get_feature_status()
    return {
        "lastUpdated": data.get("lastUpdated"),
        "statistics": data.get("statistics"),
        "epicCount": len(data.get("epics", [])),
    }


@app.get("/api/feature-status/epic/{epic_id}")
async def get_epic_status(epic_id: str) -> dict[str, Any]:
    """Get status for specific epic"""
    data = await get_feature_status()

    for epic in data.get("epics", []):
        if epic["id"] == epic_id:
            return cast(dict[str, Any], epic)

    raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")


@app.get("/api/feature-status/by-status/{status}")
async def get_features_by_status(status: str) -> dict[str, Any]:
    """Get all features with specific status"""
    valid_statuses = ["complete", "in-progress", "not-started"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    data = await get_feature_status()
    features = []

    for epic in data.get("epics", []):
        for feature in epic.get("features", []):
            if feature["status"] == status:
                features.append(
                    {**feature, "epicId": epic["id"], "epicName": epic["name"]}
                )

    return {"status": status, "count": len(features), "features": features}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
